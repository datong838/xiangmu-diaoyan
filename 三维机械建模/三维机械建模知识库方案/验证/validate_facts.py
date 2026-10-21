"""Offline DESIGN interchange checks. Not geometry execution, authentication or engineering approval."""
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT/'契约/engineering-facts.schema.json').read_text())
Draft202012Validator.check_schema(SCHEMA)


class FactError(ValueError):
    def __init__(self, code, path, reason):
        self.code, self.path = code, path
        super().__init__(f'{code} {path}: {reason}')


def fail(code, path, reason):
    raise FactError(code, path, reason)


def index(items, path):
    result = {}
    for item in items:
        if item['id'] in result: fail('IDENTITY', path, 'duplicate id')
        result[item['id']] = item
    return result


def dag(mapping, dependencies, path):
    visiting, seen = set(), set()
    def visit(k):
        if k not in mapping: fail('REFERENCE', path, k)
        if k in visiting: fail('CYCLE', path, k)
        if k in seen: return
        visiting.add(k)
        for dep in dependencies(mapping[k]): visit(dep)
        visiting.remove(k); seen.add(k)
    for k in mapping: visit(k)


def validate_facts(bundle, trusted_assets):
    errors = list(Draft202012Validator(SCHEMA).iter_errors(bundle))
    if errors:
        e = errors[0]
        fail('SCHEMA', '/'+'/'.join(str(x) for x in e.absolute_path), e.message)
    groups = ['representations','objects','contexts','facts','bindings','intents','instances']
    maps = {g:index(bundle[g], '/'+g) for g in groups}
    all_ids = [x['id'] for g in groups for x in bundle[g]]
    if len(all_ids) != len(set(all_ids)): fail('IDENTITY','/', 'cross-type id collision')
    def get(group, ident, path):
        if ident not in maps[group]: fail('REFERENCE', path, ident)
        return maps[group][ident]
    for rep in bundle['representations']:
        source = trusted_assets.get(rep['source_ref'])
        if source is None: fail('REFERENCE', '/representations', 'unknown external asset')
        if source['scope'] != bundle['scope']: fail('SCOPE', '/representations', 'source scope differs')
    for o in bundle['objects']:
        for r in o['representation_refs']: get('representations', r, '/objects')
    for f in bundle['facts']:
        subject = get('objects', f['subject_ref'], '/facts')
        if subject['revision'] != f['subject_revision']: fail('STALE_BINDING','/facts','subject revision')
        get('contexts', f['context_ref'], '/facts')
        if f['object_ref'] is not None: get('objects', f['object_ref'], '/facts')
        value, unit = f['quantity']['value'], f['quantity']['unit']
        if value is not None and unit is None: fail('FACT_VALUE','/facts','quantity unit unknown')
        if f['state'] == 'UNKNOWN' and (value is not None or f['object_ref'] is not None):
            fail('FACT_VALUE','/facts','unknown has an asserted value')
        if f['state'] == 'KNOWN' and value is None and f['object_ref'] is None:
            fail('FACT_VALUE','/facts','known has no value or relation target')
        if f['state'] == 'CONFLICTED' and not f['conflict_refs']: fail('CONFLICT','/facts','missing conflict')
        if f['state'] != 'CONFLICTED' and f['conflict_refs']: fail('CONFLICT','/facts','unmarked conflict')
        for ref in f['conflict_refs']:
            other = get('facts', ref, '/facts/conflict_refs')
            if ref == f['id'] or any(other[k] != f[k] for k in ['subject_ref','subject_revision','predicate','context_ref']):
                fail('CONFLICT','/facts','conflict must describe same subject/predicate/context')
    for b in bundle['bindings']:
        o = get('objects', b['object_ref'], '/bindings')
        r = get('representations', b['representation_ref'], '/bindings')
        if b['representation_ref'] not in o['representation_refs']: fail('BINDING','/bindings','object not represented here')
        for candidate in b['candidate_sets']:
            if not set(candidate) <= set(r['entities']): fail('BINDING','/bindings','unknown entity')
        candidates = {tuple(sorted(x)) for x in b['candidate_sets']}
        if len(candidates) != len(b['candidate_sets']): fail('BINDING','/bindings','duplicate candidates')
        if b['state'] == 'RESOLVED':
            if len(candidates)!=1: fail('BINDING','/bindings','resolved requires one candidate set')
            if o['revision']!=b['object_revision'] or r['revision']!=b['representation_revision']:
                fail('STALE_BINDING','/bindings','resolved binding targets old version')
        if b['state']=='AMBIGUOUS' and len(candidates)<2: fail('BINDING','/bindings','ambiguous requires alternatives')
        if b['state']=='UNRESOLVED' and candidates: fail('BINDING','/bindings','unresolved cannot select entities')
    for intent in bundle['intents']:
        get('objects',intent['object_ref'],'/intents')
        params = index(intent['parameters'],'/intents/parameters')
        if not set(intent['frozen']+intent['variable']) <= set(params): fail('REFERENCE','/intents','unknown parameter')
        if set(intent['frozen']) & set(intent['variable']): fail('INTENT','/intents','frozen and variable overlap')
        dag(params,lambda p:p['depends_on'],'/intents/parameters')
        for param in params.values():
            kind = param['kind']; value=param['quantity']['value']; unit=param['quantity']['unit']
            if kind=='INPUT' and (value is None or unit is None or param['depends_on'] or param['method']!='INPUT'):
                fail('INTENT','/intents','input needs known quantity with no expression')
            if kind=='UNKNOWN' and (value is not None or unit is not None or param['depends_on'] or param['method']!='UNKNOWN'):
                fail('INTENT','/intents','unknown parameter has determined quantity/expression')
            if kind=='DERIVED' and (len(param['depends_on'])!=2 or param['method'] not in ['add','subtract','multiply','divide'] or value is not None or unit is not None):
                fail('INTENT','/intents','draft derived expression has two ordered operands, not evaluated')
        index(intent['constraints'],'/intents/constraints')
        for c in intent['constraints']:
            for o in c['object_refs']: get('objects',o,'/intents/constraints')
            if not c['object_refs'] or not c['parameter_refs'] or not set(c['parameter_refs']) <= set(params):
                fail('REFERENCE','/intents/constraints','constraint needs known object and parameter')
    occurrences=maps['instances']
    dag(occurrences,lambda x:[] if x['parent_ref'] is None else [x['parent_ref']],'/instances')
    tolerance=1e-9 # Matrix arithmetic tolerance for this contract check, not an engineering tolerance.
    for ins in occurrences.values():
        definition=get('objects',ins['definition_ref'],'/instances')
        if definition['kind'] not in ['PART','ASSEMBLY']: fail('REFERENCE','/instances','definition is not a part/assembly')
        get('contexts',ins['context_ref'],'/instances')
        if ins['parent_ref'] is not None:
            parent=get('instances',ins['parent_ref'],'/instances')
            if parent['context_ref']!=ins['context_ref']: fail('REFERENCE','/instances','parent belongs to another configuration/state')
        m=ins['transform']
        if any(not math.isfinite(x) for row in m for x in row): fail('TRANSFORM','/instances','nonfinite transform')
        if any(abs(m[3][i]-[0,0,0,1][i])>tolerance for i in range(4)): fail('TRANSFORM','/instances','invalid homogeneous row')
        if any(abs(sum(m[k][i]*m[k][j] for k in range(3))-(1 if i==j else 0))>tolerance for i in range(3) for j in range(3)):
            fail('TRANSFORM','/instances','rotation not orthogonal')
        det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
        if abs(det-1)>tolerance: fail('TRANSFORM','/instances','mirror or invalid rotation')
    return {'contract_valid':True,'sample_class':bundle['sample_class'], 'geometry_verified':False,
            'engineering_approved':False,'expression_evaluation':'NOT_IMPLEMENTED',
            'unresolved_bindings':[b['id'] for b in bundle['bindings'] if b['state']!='RESOLVED']}
