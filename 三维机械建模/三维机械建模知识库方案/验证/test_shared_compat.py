"""Read-only compatibility probe against the current common seven-object prototype."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from validate_plan import validate_plan

ROOT = Path(__file__).resolve().parents[1]
COMMON = Path('/Users/ddt/work/projects/ai_agent/cad/engineering-kb')
SPEC = importlib.util.spec_from_file_location('common_kb_contracts_readonly', COMMON / 'src/kb_contracts.py')
common = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(common)


class SharedCompatibilityTests(unittest.TestCase):
    def test_current_legacy_synthetic_bundle_still_valid(self):
        bundle = json.loads((COMMON/'fixtures/contract_examples.json').read_text())
        raw = copy.deepcopy(bundle)
        common.validate_bundle(bundle)
        self.assertEqual(raw, bundle)

    def test_current_real_a_preserves_identity_and_raw(self):
        path = COMMON/'fixtures/real_a.json'
        before = path.read_bytes()
        bundle = json.loads(before)
        raw = copy.deepcopy(bundle)
        common.validate_bundle(bundle)
        self.assertEqual(raw, bundle)
        self.assertEqual(before, path.read_bytes())
        for a in bundle['assets']:
            self.assertEqual(a['id'], common.stable_id('av', a['asset_id'], a['content_sha256']))

    def test_separate_design_entry_old_consumer_rejects_new_type(self):
        plan = json.loads((ROOT/'设计样例/板孔计划.json').read_text())
        self.assertFalse(validate_plan(plan)['executable'])
        with self.assertRaises(common.ContractError) as caught:
            common.validate_bundle(plan)
        self.assertEqual(caught.exception.code, 'SCHEMA')

    def test_no_silent_new_fields_in_old_bundle(self):
        bundle = json.loads((COMMON/'fixtures/contract_examples.json').read_text())
        bundle['model_plan'] = {'execute': True}
        with self.assertRaises(common.ContractError) as caught:
            common.validate_bundle(bundle)
        self.assertEqual(caught.exception.code, 'SCHEMA')

    def test_old_scope_guards_survive_three_dimensional_extension(self):
        bundle = json.loads((COMMON/'fixtures/real_a.json').read_text())
        bundle['observations'][0]['scope']['project'] = 'unrelated-project'
        with self.assertRaises(common.ContractError) as caught:
            common.validate_bundle(bundle)
        self.assertEqual(caught.exception.code, 'SCOPE')


if __name__ == '__main__':
    unittest.main()
