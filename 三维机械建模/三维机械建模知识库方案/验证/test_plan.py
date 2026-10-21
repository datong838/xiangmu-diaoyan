"""Independent negative cases for a DESIGN fixture; no kernel or external effects."""
import copy
import json
import unittest
from pathlib import Path
from validate_plan import validate_plan, PlanError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / '设计样例/板孔计划.json'


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.raw = FIXTURE.read_bytes()
        self.plan = json.loads(self.raw)

    def rejected(self, edit, code):
        p = copy.deepcopy(self.plan)
        edit(p)
        with self.assertRaises(PlanError) as caught:
            validate_plan(p)
        self.assertEqual(caught.exception.code, code)

    def test_valid_design_is_not_execution_or_engineering_approval(self):
        result = validate_plan(self.plan)
        self.assertEqual(result['state'], 'DESIGN_COHERENT')
        self.assertFalse(result['executable'])
        self.assertFalse(result['engineering_approved'])
        self.assertTrue(result['unresolved'])
        self.assertEqual(FIXTURE.read_bytes(), self.raw)

    def test_identity_units_and_source_scope(self):
        cases = [
            ('missing_thickness', lambda p: p['parameters'].pop('thickness')),
            ('missing_unit', lambda p: p['parameters']['hole_diameter'].update(unit=None)),
            ('centimeter_not_silently_scaled', lambda p: p['parameters']['length'].update(unit='cm')),
            ('exponent', lambda p: p['parameters']['length'].update(value='1e2')),
            ('not_a_number', lambda p: p['parameters']['length'].update(value='NaN')),
            ('unknown_version', lambda p: p.update(schema_version='model3d-plan/999')),
            ('fabricated_real_source', lambda p: p.update(sample_class='REAL')),
            ('fabricated_success', lambda p: p.update(execution_status='PASS')),
            ('cross_project', lambda p: p['scope'].update(project='other-project')),
            ('extra_confirmation', lambda p: p.update(engineering_approved=True)),
            ('wrong_frame', lambda p: p['frame'].update(handedness='LEFT')),
        ]
        for name, edit in cases:
            with self.subTest(name=name): self.rejected(edit, 'SCHEMA')

    def test_geometry_constraints_before_kernel(self):
        for name, param, value in [('zero','thickness','0'), ('outside','hole_diameter','80'), ('edge_tangent','hole_x','5')]:
            with self.subTest(name=name):
                self.rejected(lambda p: p['parameters'][param].update(value=value), 'PARAMETER_RANGE')

    def test_operation_dependencies_and_roles(self):
        cases = [
            ('dangling',lambda p:p['steps'][2]['depends_on'].append('absent'),'REFERENCE'),
            ('cycle',lambda p:p['steps'][0]['depends_on'].append('S3'),'CYCLIC_PLAN'),
            ('duplicate',lambda p:p['steps'].append(copy.deepcopy(p['steps'][0])),'DUPLICATE_ID'),
            ('arbitrary_code',lambda p:p['steps'][0].update(registered_operation='eval'),'SCHEMA'),
            ('swapped_cut',lambda p:p['steps'][2].update(workpiece_step='S2',tool_step='S1'),'OPERAND_ROLE'),
            ('wrong_diameter_source',lambda p:p['steps'][1]['parameter_refs'].__setitem__(0,'length'),'OPERATION_FIELDS'),
            ('missing_margin',lambda p:p['steps'][1].pop('execution_settings'),'OPERATION_FIELDS'),
        ]
        for name, edit, code in cases:
            with self.subTest(name=name): self.rejected(edit,code)

    def test_no_single_metric_or_misbound_requirement(self):
        cases = [
            ('volume_only',lambda p:p.update(validations=[p['validations'][3]]),'VALIDATION_SET'),
            ('dangling_requirement',lambda p:p['validations'][0].update(requirement_refs=['absent']),'REFERENCE'),
            ('volume_instead_of_hole_position',lambda p:p['validations'][1].update(requirement_refs=['R1']),'VALIDATION_ROLE'),
            ('swapped_diameter_and_x',lambda p:p['requirements'][1].update(diameter_ref='hole_x'),'REFERENCE'),
            ('missing_tolerance_policy',lambda p:p['validations'][3].pop('tolerance_policy'),'VALIDATION_FIELDS'),
        ]
        for name, edit, code in cases:
            with self.subTest(name=name): self.rejected(edit,code)


if __name__ == '__main__':
    unittest.main()
