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
from pathlib import Path
import tempfile
import unittest

M = None


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.via = Path(self.tmp.name)
        self.policy = {"watch": ["engine.py", "req_v*.json"], "requirements": "req_v*.json",
                       "checkpoint": "checkpoint.json", "tool_lock": "tools.json", "source_contract": "sources.json",
                       "component_inventory": "components.json", "managed_modules": ["engine.py"],
                       "required_source_lanes": ["filename", "first_page_info", "first_page_body", "annual_financial"],
                       "work_items": [{"id": "work", "requirement": "VCGC-REQ001", "state": "VERIFIED", "case": "fixture", "receipt": "receipt.json"}]}
        self.put('engine.py', '# [VIA:ACCEL-BRIDGE:v0100]\nVERSION="v0100"\n')
        self.put('frozen.py', 'successful extraction\n')
        self.put('tool.py', 'locked token tool\n')
        self.policy['frozen_sources'] = {'frozen.py': M.sha(self.via/'frozen.py')}
        self.put('req_v0100.json', {'requirements': [{'code': 'VCGC-REQ001', 'status': 'COVERED', 'requirement': 'keep evidence', 'homes': ['VCGC-WKF001']}]})
        self.put('tools.json', {'token': {'path': 'tool.py', 'sha256': M.sha(self.via/'tool.py')}})
        self.put('sources.json', {'sources': [{'key': x} for x in self.policy['required_source_lanes']]})
        self.put('components.json', {'records': [{'source': 'engine.py'}]})
        self.put('test.log', '[fixture target] PASS\n')
        self.receipt = {'schema': 'VIA.Handoff.TestReceipt.v1', 'rc': 0, 'target_marker_seen': True,
                        'case': 'fixture', 'command': ['VCGC', 'run', 'engine', '--selftest'], 'completed_at': '2026-09-29T00:00:00Z',
                        'dependencies': {'engine.py': M.sha(self.via/'engine.py')}, 'log': 'test.log', 'log_sha256': M.sha(self.via/'test.log')}
        self.put('receipt.json', self.receipt)
        self.baseline = self.audit(baseline={})

    def put(self, name, obj):
        p=self.via/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(obj if isinstance(obj,str) else json.dumps(obj), encoding='utf-8', newline='')

    def audit(self, **kw):
        return M.audit(self.via,self.policy,kw.get('baseline',getattr(self,'baseline',{})), require_baseline=False)

    def rule(self, name):
        self.assertIn(name,[x['rule'] for x in self.audit()['rows']])

    def test_unchanged_proof_reused(self):
        r=self.audit();self.assertEqual(r['lamp'],'GREEN');self.assertEqual(r['reusable_successes'],['work'])

    def test_deleted_requirement_red(self):
        self.put('req_v0101.json',{'requirements':[]});self.rule('REQ_REMOVED')

    def test_new_requirement_requires_ack(self):
        d=M.read(self.via/'req_v0100.json');d['requirements'].append({'code':'VCGC-REQ002','status':'RECORDED'})
        self.put('req_v0101.json',d);self.rule('REQ_CHANGED')

    def test_changed_definition_not_hidden(self):
        d=M.read(self.via/'req_v0100.json');d['requirements'][0]['requirement']='new rule';self.put('req_v0100.json',d)
        self.rule('REQ_CHANGED')

    def test_pending_item_cannot_disappear(self):
        self.policy['work_items']=[];self.rule('WORK_ITEM_REMOVED')

    def test_missing_receipt(self):
        (self.via/'receipt.json').unlink();self.rule('EVIDENCE_INVALID')

    def test_wrong_receipt_target(self):
        self.receipt['case']='another target';self.put('receipt.json',self.receipt);self.rule('EVIDENCE_INVALID')

    def test_failed_receipt(self):
        self.receipt['rc']=1;self.put('receipt.json',self.receipt);self.rule('EVIDENCE_INVALID')

    def test_zero_exit_without_marker_is_invalid(self):
        self.receipt['target_marker_seen']=False;self.put('receipt.json',self.receipt);self.rule('EVIDENCE_INVALID')

    def test_empty_dependency_not_proof(self):
        self.receipt['dependencies']={};self.put('receipt.json',self.receipt);self.rule('EVIDENCE_INVALID')

    def test_changed_code_invalidates_receipt(self):
        self.put('engine.py','# [VIA:ACCEL-BRIDGE:v0100]\nVERSION="v0101"\n');self.rule('EVIDENCE_INVALID')

    def test_changed_log_invalidates_receipt(self):
        self.put('test.log','forged pass');self.rule('EVIDENCE_INVALID')

    def test_missing_log_invalidates_receipt(self):
        (self.via/'test.log').unlink();self.rule('EVIDENCE_INVALID')

    def test_changed_frozen_source_red(self):
        self.put('frozen.py','changed');self.rule('SUCCESS_LOCK_CHANGED')

    def test_frozen_definition_cannot_be_removed_to_pass(self):
        self.policy['frozen_sources']={};self.rule('LOCK_DEFINITION_REMOVED_OR_CHANGED')

    def test_frozen_definition_cannot_be_rewritten_to_pass(self):
        self.put('frozen.py','changed');self.policy['frozen_sources']['frozen.py']=M.sha(self.via/'frozen.py')
        self.rule('LOCK_DEFINITION_REMOVED_OR_CHANGED')

    def test_source_scope_cannot_shrink(self):
        self.policy['required_source_lanes']=['filename'];self.rule('POLICY_SCOPE_REMOVED')

    def test_missing_frozen_source_red(self):
        (self.via/'frozen.py').unlink();self.rule('SUCCESS_LOCK_CHANGED')

    def test_changed_tool_red(self):
        self.put('tool.py','changed');self.rule('TOOL_LOCK_CHANGED')

    def test_unregistered_module_red(self):
        self.put('components.json',{'records':[]});self.rule('MODULE_UNREGISTERED')

    def test_acceleration_bridge_required(self):
        self.put('engine.py','no bridge');self.rule('ACCEL_BRIDGE_MISSING')

    def test_deleted_module_red(self):
        (self.via/'engine.py').unlink();self.rule('FILE_REMOVED');self.rule('MODULE_MISSING')

    def test_missing_source_lane_red(self):
        self.put('sources.json',{'sources':[{'key':'filename'}]});self.rule('SOURCE_LANE_MISSING')

    def test_duplicate_source_lane_red(self):
        self.put('sources.json',{'sources':[{'key':x} for x in self.policy['required_source_lanes']+['filename']]});self.rule('SOURCE_LANE_MISSING')

    def test_duplicate_requirement_rejected(self):
        self.put('req_v0100.json',{'requirements':[{'code':'A'},{'code':'A'}]})
        with self.assertRaises(ValueError):self.audit()

    def test_pending_without_next_red(self):
        self.policy['work_items'][0]={'id':'work','requirement':'VCGC-REQ001','state':'PENDING','owner':'AI'}
        self.rule('PENDING_WITHOUT_NEXT')

    def test_handoff_green_is_not_closeout_green(self):
        self.policy['work_items'].append({'id':'host','requirement':'VCGC-REQ001','state':'BLOCKED','owner':'AI','reason':'missing host','next':'run authorized host test'})
        r=self.audit();self.assertEqual(r['lamp'],'GREEN');self.assertEqual(r['closeout_lamp'],'YELLOW')

    def test_unknown_requirement_red(self):
        self.policy['work_items'][0]['requirement']='unknown';self.rule('UNREGISTERED_REQUIREMENT')

    def test_null_source_contract_not_green(self):
        self.put('sources.json',{'sources':[]});self.rule('SOURCE_LANE_MISSING')

    def test_partial_old_requirement_preserved(self):
        self.put('req_v0100.json',{'requirements':[{'code':'VCGC-REQ001','status':'PARTIAL','next':'finish test','hand':'AI'}]})
        self.assertTrue(any(x['id']=='VCGC-REQ001' for x in self.audit()['pending']))

    def test_crlf_does_not_invalidate_git_text(self):
        original=M.sha(self.via/'engine.py');(self.via/'engine.py').write_bytes(b'# [VIA:ACCEL-BRIDGE:v0100]\r\nVERSION="v0100"\r\n')
        self.assertEqual(original,M.sha(self.via/'engine.py'));self.assertEqual(self.audit()['lamp'],'GREEN')

    def test_no_path_escape(self):
        with self.assertRaises(ValueError):M.local(self.via,'../outside')

    def test_missing_checkpoint_is_yellow(self):
        r=M.audit(self.via,self.policy,require_baseline=True);self.assertEqual(r['lamp'],'YELLOW')


def run(module):
    global M
    M=module
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContinuityTests))
    failure=len(result.failures)+len(result.errors)
    print('[交接回歸] fail='+str(failure)+'; tests='+str(result.testsRun))
    return int(not result.wasSuccessful())
