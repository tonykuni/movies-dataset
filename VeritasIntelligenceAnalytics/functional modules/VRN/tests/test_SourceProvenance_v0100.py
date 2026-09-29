"""Fault-injection regression, v0100, 2026-09-29. No production data writes."""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import copy
import json
import unittest

M=None
N=None


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.catalog={key:'VIA-VRN-SRC'+str(i).zfill(3) for i,key in enumerate(['filename','first_page_info','first_page_body','annual_financial'],1)}
        self.doc='a'*64

    def obs(self,lane='filename',value=123,locator=None,context=None,glyphs=None):
        return M.observation(N,self.catalog,self.doc,lane,'target_price',value,locator or {'page':1},context=context,glyphs=glyphs)

    def test_same_value_different_source_distinct(self):
        self.assertNotEqual(self.obs()['id'],self.obs('first_page_info')['id'])

    def test_same_source_retry_same_identity(self):
        self.assertEqual(self.obs()['id'],self.obs()['id'])

    def test_repair_is_revision_not_new_independent_source(self):
        a,b=self.obs(value=123),self.obs(value=124)
        self.assertEqual(a['id'],b['id']);self.assertNotEqual(a['revision_sha256'],b['revision_sha256'])

    def test_null_preserved(self):
        self.assertIsNone(self.obs(value=None)['value']);self.assertEqual(self.obs(value=None)['state'],'NULL_ALLOWED')

    def test_zero_not_null(self):
        self.assertEqual(self.obs(value=0)['value'],0);self.assertEqual(self.obs(value=0)['state'],'EXTRACTED')

    def test_page_context_distinct(self):
        self.assertNotEqual(self.obs(locator={'page':1})['id'],self.obs(locator={'page':2})['id'])

    def test_unicode_identity_stable(self):
        a=self.obs(locator={'table':'資產負債表','row':3});b=self.obs(locator={'row':3,'table':'資產負債表'})
        self.assertEqual(a['id'],b['id'])

    def test_same_glyph_two_engines_not_independent(self):
        r=M.reconcile([self.obs(glyphs=['glyph1']),self.obs('first_page_body',glyphs=['glyph1'])])[0]
        self.assertEqual(r['independent_count'],1);self.assertEqual(r['state'],'SINGLE_SOURCE')

    def test_two_sources_agree_not_complete(self):
        r=M.reconcile([self.obs(),self.obs('first_page_info')])[0]
        self.assertEqual(r['state'],'AGREE');self.assertFalse(r['proves_complete'])

    def test_conflict_retained(self):
        r=M.reconcile([self.obs(),self.obs('first_page_info',value=456)])[0]
        self.assertEqual(r['state'],'CONFLICT');self.assertEqual(len(r['observations']),2)

    def test_years_must_not_compare(self):
        r=M.reconcile([self.obs(context={'year':2024}),self.obs('first_page_info',value=456,context={'year':2025})])
        self.assertEqual(len(r),2);self.assertTrue(all(x['state']=='SINGLE_SOURCE' for x in r))

    def test_units_must_not_compare(self):
        r=M.reconcile([self.obs(context={'unit':'million'}),self.obs('first_page_info',context={'unit':'billion'})])
        self.assertEqual(len(r),2)

    def test_raw_null_no_consensus(self):
        r=M.reconcile([self.obs(value=None),self.obs('first_page_info',value=None)])[0]
        self.assertEqual(r['state'],'NULL_ALLOWED')

    def test_completed_region_no_heavy_plan(self):
        self.assertEqual(M.plan_escalation({}, {}, json.loads(M.CONTRACT.read_text())),[])

    def test_failed_region_only(self):
        r=M.plan_escalation({'p1-right':'missing'}, {}, json.loads(M.CONTRACT.read_text()))
        self.assertEqual(len(r),1);self.assertEqual(r[0]['next']['engine'],'second_native');self.assertFalse(r[0]['automatic_execution'])

    def test_dpi_raised_only_after_failed_earlier_stages(self):
        r=M.plan_escalation({'p1':'missing'}, {'p1':[{'seconds':1}]*2}, json.loads(M.CONTRACT.read_text()))
        self.assertEqual(r[0]['next']['dpi'],300)

    def test_time_budget_stops_escalation(self):
        r=M.plan_escalation({'p1':'missing'}, {'p1':[{'seconds':61}]}, json.loads(M.CONTRACT.read_text()))
        self.assertIsNone(r[0]['next']);self.assertEqual(r[0]['state'],'REVIEW_BUDGET')

    def test_attempt_budget_stops_escalation(self):
        r=M.plan_escalation({'p1':'missing'}, {'p1':[{'seconds':1}]*5}, json.loads(M.CONTRACT.read_text()))
        self.assertEqual(r[0]['state'],'REVIEW_BUDGET')

    def test_unregistered_source_rejected(self):
        with self.assertRaises(ValueError):N.observation_id('my_local_id',self.doc,{},'price')

    def test_missing_document_identity_rejected(self):
        with self.assertRaises(ValueError):N.observation_id('VIA-VRN-SRC001','',{},'price')

    def test_existing_filename_parser_ctbc(self):
        core=M.load(M.HERE/'engine/VRN_Evidence_Core.py','_filename_core_ctbc')
        fields=M.filename_fields('晶心科(6533,N,中立)-CTBC251208.pdf',core)
        self.assertEqual(fields['ticker'],'6533');self.assertEqual(fields['report_date'],'2025-12-08')

    def test_existing_filename_parser_roc(self):
        core=M.load(M.HERE/'engine/VRN_Evidence_Core.py','_filename_core_roc')
        fields=M.filename_fields('華南投顧-2606-裕民-1141202.pdf',core)
        self.assertEqual(fields['ticker'],'2606');self.assertEqual(fields['report_date'],'2025-12-02')

    def test_page_date_uses_owner_iso_key(self):
        core=M.load(M.HERE/'engine/VRN_Evidence_Core.py','_date_core')
        fields=M.page_fields(core,['晶心科 (6533 TT)','2025/12/06'])
        self.assertEqual(fields['report_date'],'2025-12-06')


def run(module):
    global M,N
    M=module
    N=M.load(max(M.REG.glob('CGC_MDL237_NumberingSystem_v*.py')),'_provenance_test_numbering')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProvenanceTests))
    failure=len(result.errors)+len(result.failures)
    print('[來源回歸] fail='+str(failure)+'; tests='+str(result.testsRun))
    return int(not result.wasSuccessful())
