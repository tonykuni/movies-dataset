#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Contract and regression tests. [VIA:ACCEL-BRIDGE] No target imports."""
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

FIXTURE_MODULE = 'def describe():\n    return {}\ndef execute(request):\n    return request\ndef main():\n    return 0\n'

import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from vcgc_tools import actions, cli, core, inventory, report


class ToolModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'input'
        self.root.mkdir()
        self.out = self.base / 'output'

    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def snap(self, previous=None):
        return inventory.scan([('fixture', self.root)], previous=previous)

    def test_no_target_execution(self):
        marker = self.base / 'must-not-exist'
        self.put('a.py', f'open({str(marker)!r}, "w").write("EXECUTED")\ndef main():\n    return 0\n')
        self.assertEqual(self.snap()['quantity']['parsed'], 1)
        self.assertFalse(marker.exists())

    def test_valid_bom_and_chinese(self):
        self.put('中文.py', '\ufeffdef 計算(數值):\n    return 數值\n')
        self.assertEqual(self.snap()['nodes'][0]['parameters'], ['數值'])

    def test_compile_error_is_error(self):
        self.put('bad.py', 'return 1\n')
        self.assertEqual(self.snap()['quantity']['errors'], 1)

    def test_syntax_error_is_not_green(self):
        self.put('bad.py', 'def bad(:\n pass')
        self.assertEqual(self.snap()['status'], 'RED')

    def test_duplicate_defs_have_distinct_ids(self):
        self.put('a.py', 'def x():\n pass\ndef x():\n pass\n')
        result = self.snap()
        self.assertEqual(len({n['node_id'] for n in result['nodes']}), 2)
        self.assertEqual(result['files'][0]['issues'][0]['kind'], 'DUPLICATE_DEFINITION')

    def test_ids_stable_after_line_insertion(self):
        p = self.put('a.py', FIXTURE_MODULE)
        first = self.snap()
        p.write_text('\n\n' + FIXTURE_MODULE)
        second = self.snap()
        self.assertEqual([n['node_id'] for n in first['nodes']], [n['node_id'] for n in second['nodes']])
        self.assertNotEqual(first['input_fingerprint'], second['input_fingerprint'])

    def test_same_content_different_source_not_deduped(self):
        self.put('a.py', FIXTURE_MODULE)
        self.put('b.py', FIXTURE_MODULE)
        self.assertEqual(len({n['node_id'] for n in self.snap()['nodes']}), 6)

    def test_changed_file_invalidates_cache(self):
        p = self.put('a.py', FIXTURE_MODULE)
        first = self.snap()
        self.assertEqual(self.snap(first)['quantity']['cache_hits'], 1)
        p.write_text(FIXTURE_MODULE + '\nX=2\n')
        self.assertEqual(self.snap(first)['quantity']['cache_hits'], 0)

    def test_scope_definitions_not_collapsed(self):
        self.put('a.py', 'class A:\n def run(self):\n  return 1\nclass B:\n def run(self):\n  return 2\n')
        self.assertEqual(self.snap()['quantity']['nodes'], 4)
        self.assertEqual(self.snap()['duplicate_node_ids'], [])

    def test_nested_defs_under_duplicate_parents_have_distinct_ids(self):
        self.put('a.py', 'def f():\n def inner():\n  return 1\n return inner\ndef f():\n def inner():\n  return 2\n return inner\n')
        result = self.snap()
        self.assertEqual(len({n['node_id'] for n in result['nodes']}), 4)
        self.assertEqual(result['duplicate_node_ids'], [])
        self.assertNotEqual(result['status'], 'RED')

    def test_conditional_definitions(self):
        self.put('a.py', 'if True:\n def f():\n  return 1\nelse:\n def f():\n  return 2\n')
        self.assertEqual(len({n['node_id'] for n in self.snap()['nodes']}), 2)

    def test_missing_root_preserves_error(self):
        result = inventory.scan([('missing', self.base / 'missing')])
        self.assertEqual(result['status'], 'RED')
        self.assertEqual(result['quantity']['errors'], 1)

    def test_output_inside_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'OUTPUT_MUST'):
            core.new_run(self.root / 'out', [self.root])

    def test_write_state_machine(self):
        path = self.out / 'a.json'
        self.assertEqual(core.write_new(path, {'x':1}), 'APPLIED_NEW')
        self.assertEqual(core.write_new(path, {'x':1}), 'SKIPPED_IDENTICAL')
        with self.assertRaisesRegex(ValueError, 'HASH_STATE'):
            core.write_new(path, {'x':2})
        self.assertEqual(core.load_json(path), {'x':1})

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON'):
            core.strict_json('{"x":1,"x":2}')

    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, 'NONFINITE'):
            core.strict_json('{"x":NaN}')

    def test_context_has_no_literal_password(self):
        self.put('a.py', 'def login(password="DO-NOT-EMIT"):\n return password\n')
        text = core.encode(actions.compact_context(self.snap())).decode()
        self.assertNotIn('DO-NOT-EMIT', text)
        self.assertIn('password', text)

    def test_context_budget(self):
        self.put('a.py', '\n'.join(f'def f{i}(x):\n return x\n' for i in range(100)))
        result = actions.compact_context(self.snap(), budget=1000)
        self.assertLessEqual(len(core.encode(result).decode()), 1000)
        self.assertTrue(result['truncated'])

    def test_compare_added_removed_changed(self):
        a = self.put('a.py', FIXTURE_MODULE)
        self.put('b.py', FIXTURE_MODULE)
        first = self.snap()
        a.unlink()
        self.put('b.py', FIXTURE_MODULE + '\nX=1')
        self.put('c.py', FIXTURE_MODULE)
        self.assertEqual({r['status'] for r in actions.compare(first, self.snap())['changes']}, {'ADDED','REMOVED','CHANGED'})

    def manifest(self):
        p = self.put('module.py', FIXTURE_MODULE)
        m = dict(schema='via.toolmodule/1',module_id='VTM-CUSTOM-001',verb='custom',description='Test module',entry='module.py',sha256=core.digest(p.read_bytes()),input_schema={'type':'object'},output_schema={'type':'object'},capabilities=['local-read'])
        return self.put('module.json', json.dumps(m))

    def test_module_contract(self):
        r = actions.module_check(self.manifest())
        self.assertEqual(r['status'], 'STATIC_CONTRACT_PASS')
        self.assertFalse(r['activated'])
        self.assertIsNone(r['ssot_id'])

    def test_module_hash_mismatch(self):
        manifest = self.manifest()
        self.put('module.py', FIXTURE_MODULE + '\nX=2')
        with self.assertRaisesRegex(ValueError, 'HASH_MISMATCH'):
            actions.module_check(manifest)

    def test_module_id_collision_rejected(self):
        p = self.manifest()
        m = core.load_json(p)
        m['module_id'] = 'VTM-TOOL-001'
        p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, 'COLLISION'):
            actions.module_check(p)

    def test_builtin_verb_collision_rejected(self):
        p = self.manifest()
        m = core.load_json(p)
        m['verb'] = 'context'
        p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, 'COLLISION'):
            actions.module_check(p)

    def test_module_path_escape(self):
        p = self.manifest()
        m = core.load_json(p)
        m['entry'] = '../outside.py'
        p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, 'ENTRY_ESCAPE'):
            actions.module_check(p)

    def test_metrics_empty_is_empty(self):
        p = self.put('usage.json', '[]')
        self.assertEqual(actions.token_metrics(p)['status'], 'EMPTY')

    def test_metrics_dedup_and_totals(self):
        rows = [{'event_id':'e1','action':'read','input_tokens':12,'output_tokens':3}]*2
        p = self.put('usage.json',json.dumps(rows))
        r = actions.token_metrics(p)
        self.assertEqual((r['accepted'],r['duplicates'],r['rows'][0]['input_tokens']),(1,1,12))

    def test_metrics_conflict_is_invalid(self):
        p = self.put('usage.json',json.dumps([{'event_id':'e','action':'read','input_tokens':1,'output_tokens':2},{'event_id':'e','action':'read','input_tokens':2,'output_tokens':2}]))
        self.assertEqual(actions.token_metrics(p)['status'], 'INVALID')

    def test_invalid_counts_rejected(self):
        for n in (-1, True, 2.5, '3.0'):
            p = self.put('usage.json',json.dumps([{'event_id':'e','action':'read','input_tokens':n,'output_tokens':2}]))
            self.assertEqual(actions.token_metrics(p)['status'], 'INVALID')

    def test_symlink_skipped(self):
        p = self.put('real.py', FIXTURE_MODULE)
        link = self.root / 'link.py'
        try:
            link.symlink_to(p)
        except OSError:
            self.skipTest('symlink creation unavailable')
        # One real source, symlink cannot become a second executed/imported input.
        self.assertEqual(self.snap()['quantity']['parsed'], 1)

    def test_powershell_not_python_pass(self):
        self.put('test.ps1', 'this is not valid powershell }')
        self.assertEqual(self.snap()['files'][0]['status'], 'POWERSHELL_AST_NOT_RUN')

    def test_report_escapes_script_content(self):
        self.put('a.py', FIXTURE_MODULE)
        tools = [{'id':'VTM-X','name':'</script><script>alert(1)</script>','status':'WAIT','verb':'x','purpose':'x','next':'x','evidence':'x'}]
        html = report.render(self.snap(), tools, 1)
        self.assertNotIn('</script><script>alert(1)', html)
        self.assertIn('\\u003c/script>', html)

    def test_catalog_ids_unique(self):
        rows = actions.catalog(Path(__file__).resolve().parents[1])
        self.assertEqual(len(rows), len({r['id'] for r in rows}))
        self.assertTrue(all(r['ssot_id'] is None for r in rows))

    def test_cli_three_rounds_preserve_source(self):
        p = self.put('a.py', FIXTURE_MODULE)
        before = p.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(['panorama','--root','fixture='+str(self.root),'--out',str(self.out)])
        self.assertEqual(rc, 0)
        self.assertEqual(p.read_bytes(), before)
        runs = list(self.out.iterdir())
        self.assertEqual(len(runs), 1)
        result = core.load_json(runs[0]/'result.json')
        self.assertEqual(len(result['rounds']), 3)
        self.assertTrue((runs[0]/'round_3/Matrix.html').exists())
        self.assertFalse(result['external_activation'])

    def test_registration_is_proposal_only(self):
        r = actions.registration_plan(actions.catalog(Path(__file__).resolve().parents[1]), self.root)
        self.assertEqual(r['status'], 'NOT_APPLIED')
        self.assertFalse(r['mcp']['new_tools_exposed'])

    def test_audit_chain_links(self):
        run = core.new_run(self.out, [self.root])
        a = core.event(run,'a',{})
        b = core.event(run,'b',{},a)
        row = core.load_json(run/'events'/(b+'.json'))
        self.assertEqual(row.pop('sha256'), core.digest(row))
        self.assertEqual(row['previous_sha256'], a)


if __name__ == '__main__':
    unittest.main(verbosity=2)
