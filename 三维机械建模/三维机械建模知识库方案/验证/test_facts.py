import copy
import json
from pathlib import Path
import unittest
from validate_facts import validate_facts, FactError

ROOT=Path(__file__).resolve().parents[1]
COMMON=Path('/Users/ddt/work/projects/ai_agent/cad/engineering-kb')


class FactTests(unittest.TestCase):
    def setUp(self):
        self.raw=(ROOT/'设计样例/工程事实包.json').read_bytes()
        self.bundle=json.loads(self.raw)
        assets=json.loads((COMMON/'fixtures/contract_examples.json').read_text())['assets']
        self.registry={a['id']:a for a in assets}

    def reject(self, edit, code):
        b=copy.deepcopy(self.bundle);edit(b)
        with self.assertRaises(FactError) as caught:validate_facts(b,self.registry)
        self.assertEqual(caught.exception.code,code)

    def test_all_four_fact_domains_and_input_preservation(self):
        b=copy.deepcopy(self.bundle)
        r=validate_facts(b,self.registry)
        self.assertTrue(r['contract_valid']);self.assertFalse(r['geometry_verified']);self.assertFalse(r['engineering_approved'])
        self.assertEqual({x['domain'] for x in b['facts']},{'GEOMETRY','TOPOLOGY','PARAMETER','ASSEMBLY'})
        self.assertEqual(b,self.bundle);self.assertEqual((ROOT/'设计样例/工程事实包.json').read_bytes(),self.raw)

    def test_identity_scope_and_references(self):
        cases=[('scope',lambda b:b['scope'].update(project='elsewhere'),'SCOPE'),
               ('source',lambda b:b['representations'][0].update(source_ref='absent'),'REFERENCE'),
               ('duplicate',lambda b:b['objects'].append(copy.deepcopy(b['objects'][0])),'IDENTITY'),
               ('fact_subject',lambda b:b['facts'][0].update(subject_ref='absent'),'REFERENCE'),
               ('context',lambda b:b['facts'][0].update(context_ref='absent'),'REFERENCE'),
               ('revision',lambda b:b['facts'][0].update(subject_revision=2),'STALE_BINDING'),
               ('path',lambda b:b.update(source_path='/tmp/fake'),'SCHEMA')]
        for name,edit,code in cases:
            with self.subTest(name=name):self.reject(edit,code)

    def test_fact_value_unknown_and_conflict(self):
        cases=[('unit',lambda b:b['facts'][0]['quantity'].update(unit=None),'FACT_VALUE'),
               ('unknown_asserted',lambda b:b['facts'][0].update(state='UNKNOWN'),'FACT_VALUE'),
               ('empty_known',lambda b:b['facts'][2].update(state='KNOWN'),'FACT_VALUE'),
               ('missing_conflict',lambda b:b['facts'][0].update(state='CONFLICTED'),'CONFLICT'),
               ('unmarked_conflict',lambda b:b['facts'][0].update(conflict_refs=['f2']),'CONFLICT')]
        for name,edit,code in cases:
            with self.subTest(name=name):self.reject(edit,code)
        b=copy.deepcopy(self.bundle)
        f=copy.deepcopy(b['facts'][0]);f.update(id='conflicting_f1',state='CONFLICTED',conflict_refs=['f1']);f['quantity']['value']='20'
        b['facts'][0].update(state='CONFLICTED',conflict_refs=['conflicting_f1']);b['facts'].append(f)
        self.assertTrue(validate_facts(b,self.registry)['contract_valid']) # recording a conflict is valid, not resolving it

    def test_binding_alternatives_staleness_and_split_entities(self):
        cases=[('old',lambda b:b['bindings'][0].update(representation_revision=2),'STALE_BINDING'),
               ('entity',lambda b:b['bindings'][0].update(candidate_sets=[['not_in_model']]),'BINDING'),
               ('ambiguous_single',lambda b:b['bindings'][0].update(state='AMBIGUOUS'),'BINDING'),
               ('resolved_multiple',lambda b:b['bindings'][0].update(candidate_sets=[['cylinder1'],['cylinder2']]),'BINDING'),
               ('unresolved_selected',lambda b:b['bindings'][0].update(state='UNRESOLVED'),'BINDING')]
        for name,edit,code in cases:
            with self.subTest(name=name):self.reject(edit,code)
        for state,sets in [('RESOLVED',[['cylinder1','cylinder2']]),('AMBIGUOUS',[['cylinder1'],['cylinder2']]),('INVALIDATED',[['cylinder1']])]:
            b=copy.deepcopy(self.bundle);b['bindings'][0].update(state=state,candidate_sets=sets)
            r=validate_facts(b,self.registry)
            self.assertEqual(bool(r['unresolved_bindings']),state!='RESOLVED')

    def test_parameter_dependency_and_frozen_scope(self):
        cases=[('cycle',lambda b:b['intents'][0]['parameters'][2].update(depends_on=['double_diameter','diameter']),'CYCLE'),
               ('unknown_dep',lambda b:b['intents'][0]['parameters'][2].update(depends_on=['missing','diameter']),'REFERENCE'),
               ('freeze',lambda b:b['intents'][0]['variable'].append('diameter'),'INTENT'),
               ('unknown_value',lambda b:b['intents'][0]['parameters'][1]['quantity'].update(value='10',unit='mm'),'INTENT'),
               ('constraint',lambda b:b['intents'][0]['constraints'][0].update(parameter_refs=['absent']),'REFERENCE'),
               ('fake_solver',lambda b:b['intents'][0]['parameters'][2].update(method='eval'),'SCHEMA')]
        for name,edit,code in cases:
            with self.subTest(name=name):self.reject(edit,code)

    def test_assembly_instance_transform_and_cycle(self):
        cases=[('self_parent',lambda b:b['instances'][0].update(parent_ref='occ1'),'CYCLE'),
               ('missing_definition',lambda b:b['instances'][0].update(definition_ref='missing'),'REFERENCE'),
               ('feature_not_part',lambda b:b['instances'][0].update(definition_ref='hole1'),'REFERENCE'),
               ('scale',lambda b:b['instances'][0]['transform'][0].__setitem__(0,2),'TRANSFORM'),
               ('mirror',lambda b:b['instances'][0]['transform'][0].__setitem__(0,-1),'TRANSFORM'),
               ('row',lambda b:b['instances'][0]['transform'][3].__setitem__(0,1),'TRANSFORM')]
        for name,edit,code in cases:
            with self.subTest(name=name):self.reject(edit,code)
        b=copy.deepcopy(self.bundle);second=copy.deepcopy(b['instances'][0]);second.update(id='occ2',parent_ref='occ1');second['transform'][0][3]=25;b['instances'].append(second)
        self.assertTrue(validate_facts(b,self.registry)['contract_valid']) # shared definition, distinct occurrence


if __name__=='__main__':unittest.main()
