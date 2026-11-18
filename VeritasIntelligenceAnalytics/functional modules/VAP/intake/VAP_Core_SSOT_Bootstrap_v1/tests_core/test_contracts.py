from pathlib import Path
import copy
import json
import tempfile
import unittest
from vap_core import VAPContracts, ContractError
from extract_vap_ssot import extract

ROOT = Path(__file__).resolve().parents[1]


class ContractsTest(unittest.TestCase):
    def setUp(self):
        self.core = VAPContracts(ROOT)

    def test_28_original_codes(self):
        self.assertEqual({c['code'] for c in self.core.catalog()}, {'VAP-CH-' + str(n).zfill(2) for n in range(1,29)})

    def test_eight_groups(self):
        self.assertEqual(self.core.report()['groups'], {'single':5,'stack':3,'indiv':2,'dual':2,'adv':4,'rolling':8,'ta':3,'fund':1})

    def test_no_declared_chart_is_claimed_executable(self):
        self.assertTrue(all(c['execution_status']=='declared_only' and c['renderer_status']=='not_verified' for c in self.core.catalog()))
        self.assertEqual(self.core.report()['verified_chart_engine_count'],0)

    def test_authoritative_line_and_area_defaults(self):
        r=self.core.resolve('VAP-CH-02')
        self.assertEqual(r['resolved_spec']['line']['width'],1)
        self.assertEqual(r['resolved_spec']['line']['opacity'],.9)
        self.assertEqual(r['resolved_spec']['fill']['areaUnderLine'],.75)

    def test_full_price_policy_preserved(self):
        p=self.core.resolve('VAP-CH-27')['resolved_spec']['price']
        self.assertEqual(p['sourcePriority'],['adjClose','close'])
        self.assertEqual(p['missingVolume'],'doNotFill')
        self.assertTrue(p['splitAdjustVolume'])

    def test_named_gap_preset_does_not_destroy_map(self):
        r=self.core.resolve('VAP-CH-07')
        self.assertEqual(r['chart_extensions']['bar_gap_factor'],.86)
        self.assertIsInstance(r['resolved_spec']['bar']['gapFactor'],dict)
        self.assertEqual(r['resolved_spec']['bar']['gapFactor']['grouped'],.44)

    def test_grid_extension_preserved(self):
        self.assertEqual(self.core.resolve('VAP-CH-09')['chart_extensions']['grid'],'2x2')

    def test_safe_scalar_override(self):
        r=self.core.resolve('VAP-CH-02',{'fill.areaUnderLine':.5})
        self.assertEqual(r['resolved_spec']['fill']['areaUnderLine'],.5)
        self.assertEqual(self.core.spec['fill']['areaUnderLine'],.75)

    def test_invalid_opacity_rejected(self):
        for v in [-.1,1.1,float('nan'),float('inf'),True,'0.5']:
            with self.subTest(v=v),self.assertRaises(ContractError):
                self.core.resolve('VAP-CH-01',{'line.opacity':v})

    def test_fixed_line_width_ambiguity_fail_closed(self):
        with self.assertRaisesRegex(ContractError,'policy unresolved'):
            self.core.resolve('VAP-CH-01',{'line.width':1.5})

    def test_unknown_parameter_rejected(self):
        with self.assertRaises(ContractError):
            self.core.resolve('VAP-CH-01',{'palette.default':'unregistered'})

    def test_unknown_chart_rejected(self):
        with self.assertRaises(ContractError):self.core.resolve('VAP-CH-99')

    def test_mutation_does_not_change_authority(self):
        s=self.core.spec;s['line']['width']=99
        lib=self.core.library;lib['groups'].clear()
        c=self.core.chart('VAP-CH-01');c['fields'].clear()
        self.assertEqual(self.core.spec['line']['width'],1)
        self.assertEqual(len(self.core.catalog()),28)
        self.assertEqual(self.core.chart('VAP-CH-01')['fields'],['date','value'])

    def temporary_core(self, modifier):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'ssot').mkdir()
            spec=self.core.spec;lib=self.core.library
            modifier(spec,lib)
            for name,obj in [('vap_spec.json',spec),('vap_chartlib.json',lib)]:
                (root/'ssot'/name).write_text(json.dumps(obj))
            return VAPContracts(root)

    def test_original_code_cannot_be_removed(self):
        with self.assertRaises(ContractError):
            self.temporary_core(lambda s,l:l['groups'][0]['charts'].pop())

    def test_duplicate_code_rejected(self):
        with self.assertRaises(ContractError):
            self.temporary_core(lambda s,l:l['groups'][0]['charts'].append(copy.deepcopy(l['groups'][0]['charts'][0])))

    def test_unknown_spec_ref_rejected(self):
        with self.assertRaises(ContractError):
            self.temporary_core(lambda s,l:l['meta'].update(specRef='different.json'))

    def test_unknown_library_gap_preset_rejected(self):
        with self.assertRaises(ContractError):
            self.temporary_core(lambda s,l:l['groups'][1]['charts'][1]['override'].update({'bar.gapFactor':'unknown'}))

    def test_spec_opacity_rejected(self):
        with self.assertRaises(ContractError):
            self.temporary_core(lambda s,l:s['line'].update(opacity=2))

    def test_missing_version_changelog_rejected(self):
        with self.assertRaises(ContractError):
            self.temporary_core(lambda s,l:s.update(changelog=[]))

    def test_additional_code_keeps_originals(self):
        def mod(s,l):
            c=copy.deepcopy(l['groups'][0]['charts'][0]);c.update(code='VAP-CH-29',id='extension-test')
            l['groups'][0]['charts'].append(c)
            l['meta']['version']='1.1.0';l['changelog'].append({'version':'1.1.0','note':'Unit fixture only'})
        self.assertEqual(len(self.temporary_core(mod).catalog()),29)

    def test_all_chart_defaults_resolve_without_mutating_source(self):
        s=copy.deepcopy(self.core.spec)
        for c in self.core.catalog():
            with self.subTest(code=c['code']):
                r=self.core.resolve(c['code']);self.assertFalse(r['rendering_verified']);self.assertIn('source_hashes',r)
        self.assertEqual(self.core.spec,s)

    def test_extractor_refuses_different_existing_target(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'vap_spec.json').write_text('{}\n')
            with self.assertRaises(FileExistsError):extract(ROOT/'inputs/pasted_content_3.txt',root)
            self.assertEqual((root/'vap_spec.json').read_text(),'{}\n')
            self.assertFalse((root/'vap_chartlib.json').exists())

    def test_extractor_idempotent(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);m=extract(ROOT/'inputs/pasted_content_3.txt',root)
            self.assertEqual(extract(ROOT/'inputs/pasted_content_3.txt',root),m)


if __name__=='__main__':unittest.main()
