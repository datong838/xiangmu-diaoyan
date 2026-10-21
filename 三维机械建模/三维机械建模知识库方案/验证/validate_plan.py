"""Only validates the synthetic plate-hole DESIGN contract; never executes geometry."""
import json
from decimal import Decimal, localcontext
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / '契约/model-plan.schema.json').read_text())
Draft202012Validator.check_schema(SCHEMA)


class PlanError(ValueError):
    def __init__(self, code, path, reason):
        self.code, self.path, self.reason = code, path, reason
        super().__init__(f'{code} {path}: {reason}')


def reject(code, path, reason):
    raise PlanError(code, path, reason)


def unique(items, key, path):
    result = {}
    for i, item in enumerate(items):
        ident = item[key]
        if ident in result:
            reject('DUPLICATE_ID', f'{path}/{i}/{key}', ident)
        result[ident] = item
    return result


def validate_plan(plan):
    """Read-only validation. Success means design coherence, not executable/engineering approval."""
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(plan),
                    key=lambda e: '/'.join(str(x) for x in e.absolute_path))
    if errors:
        e = errors[0]
        reject('SCHEMA', '/' + '/'.join(str(x) for x in e.absolute_path), e.message)
    if len(plan['steps']) > 64:
        reject('BUDGET', '/steps', 'design limit 64')
    parameters = plan['parameters']
    with localcontext() as ctx:
        ctx.prec = 200
        values = {k: Decimal(v['value']) for k, v in parameters.items()}
        if any(v <= 0 for v in values.values()):
            reject('PARAMETER_RANGE', '/parameters', 'all six parameters must be positive')
        radius = values['hole_diameter'] / 2
        if not (radius < values['hole_x'] < values['length'] - radius and
                radius < values['hole_y'] < values['width'] - radius):
            reject('PARAMETER_RANGE', '/parameters', 'this task requires a fully internal hole')
    requirements = unique(plan['requirements'], 'id', '/requirements')
    steps = unique(plan['steps'], 'step_id', '/steps')
    checks = unique(plan['validations'], 'id', '/validations')
    unique(plan['expected_failures'], 'id', '/expected_failures')
    required_kinds = {'closed_solid', 'single_through_hole', 'plate_bounds'}
    if len(requirements) != 3 or {r['kind'] for r in requirements.values()} != required_kinds:
        reject('REQUIREMENT_SET', '/requirements', 'exactly one requirement of each plate-hole kind')
    for ident, req in requirements.items():
        kind = req['kind']
        expected = {'id', 'kind'}
        if kind == 'single_through_hole':
            expected |= {'diameter_ref', 'center_refs', 'axis'}
            if (req.get('diameter_ref') != 'hole_diameter' or
                    req.get('center_refs') != ['hole_x', 'hole_y'] or req.get('axis') != 'Z'):
                reject('REFERENCE', '/requirements/' + ident, 'hole bindings must match task parameters')
        if kind == 'plate_bounds':
            expected |= {'parameter_refs'}
            if req.get('parameter_refs') != ['length', 'width', 'thickness']:
                reject('REFERENCE', '/requirements/' + ident, 'plate bounds bindings differ')
        if set(req) != expected:
            reject('ROLE_FIELDS', '/requirements/' + ident, 'missing or irrelevant fields')
    visiting, visited = set(), set()
    def visit(ident):
        if ident not in steps:
            reject('REFERENCE', '/steps', 'unknown dependency ' + ident)
        if ident in visiting:
            reject('CYCLIC_PLAN', '/steps', ident)
        if ident in visited:
            return
        visiting.add(ident)
        for dep in steps[ident]['depends_on']:
            visit(dep)
        visiting.remove(ident)
        visited.add(ident)
    for ident in steps:
        visit(ident)
    ops = [s['registered_operation'] for s in steps.values()]
    if sorted(ops) != sorted(['create_plate', 'create_through_hole_tool', 'subtract']):
        reject('OPERATION_SET', '/steps', 'one plate, one cutter, one subtraction required')
    for ident, step in steps.items():
        op = step['registered_operation']
        base = {'step_id', 'registered_operation', 'depends_on'}
        if op in ('create_plate', 'create_through_hole_tool'):
            expected_params = (['length', 'width', 'thickness'] if op == 'create_plate' else
                               ['hole_diameter', 'hole_x', 'hole_y', 'thickness'])
            expected_fields = base | {'parameter_refs'}
            if op == 'create_through_hole_tool':
                expected_fields.add('execution_settings')
            if (set(step) != expected_fields or step['depends_on'] or
                    step.get('parameter_refs') != expected_params):
                reject('OPERATION_FIELDS', '/steps/' + ident, 'producer contract mismatch')
        else:
            if set(step) != base | {'workpiece_step', 'tool_step'}:
                reject('OPERATION_FIELDS', '/steps/' + ident, 'subtract contract mismatch')
            a, b = step['workpiece_step'], step['tool_step']
            if a == b or set(step['depends_on']) != {a, b}:
                reject('REFERENCE', '/steps/' + ident, 'ordered operands must be distinct dependencies')
            if steps[a]['registered_operation'] != 'create_plate' or steps[b]['registered_operation'] != 'create_through_hole_tool':
                reject('OPERAND_ROLE', '/steps/' + ident, 'workpiece and cutter swapped')
    expected_checks = {
        'solid_validity': {'closed_solid'},
        'hole_geometry_and_throughness': {'single_through_hole'},
        'plate_bounds': {'plate_bounds'},
        'plate_single_through_hole_volume': required_kinds,
    }
    if len(checks) != 4 or {c['method'] for c in checks.values()} != set(expected_checks):
        reject('VALIDATION_SET', '/validations', 'four independent task methods required')
    for ident, check in checks.items():
        refs = check['requirement_refs']
        if not set(refs) <= set(requirements):
            reject('REFERENCE', '/validations/' + ident, 'unknown requirement')
        if {requirements[r]['kind'] for r in refs} != expected_checks[check['method']]:
            reject('VALIDATION_ROLE', '/validations/' + ident, 'method covers wrong requirement')
        extras = {'formula_note', 'tolerance_policy'} if check['method'] == 'plate_single_through_hole_volume' else set()
        if set(check) != {'id', 'requirement_refs', 'method'} | extras:
            reject('VALIDATION_FIELDS', '/validations/' + ident, 'method fields mismatch')
    return {'state': 'DESIGN_COHERENT', 'executable': False,
            'engineering_approved': False, 'checks': len(checks),
            'unresolved': ['adapter axial margin', 'kernel tolerance', 'measurement uncertainty',
                           'real source bindings', 'actual geometry and engineering verification']}
