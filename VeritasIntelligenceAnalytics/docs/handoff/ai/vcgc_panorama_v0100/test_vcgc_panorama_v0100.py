#!/usr/bin/env python3
"""Isolated regression tests for the delivered runner, not VIA production tests."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('vcgc_panorama', ROOT / 'VCGC_Panorama_v0100.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
RESULTS = []


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def test_nonexecution_and_compile(folder):
    sentinel = folder / 'DO_NOT_CREATE'
    path = put(folder / 'sample.py', f'from pathlib import Path\nPath({str(sentinel)!r}).touch()\ndef good():\n    return 4\n')
    row = M.inspect_source(path)
    assert row['state'] == 'PARSED' and not sentinel.exists()
    bad = put(folder / 'bad.py', 'def broken(\n')
    assert M.inspect_source(bad)['state'] == 'ERROR'


def test_all_versions_overlap_and_dependencies(folder):
    put(folder / 'a_v0100.py', 'x=1\n')
    put(folder / 'a_v0101.py', 'x=2\n')
    put(folder / 'child' / 'b.PS1', 'Write-Output hi\n')
    put(folder / 'via_core' / 'pyvenv.cfg', 'home=test')
    put(folder / 'via_core' / 'd.py', 'x=3\n')
    files, omitted = M.enumerate_sources([folder, folder / 'child'])
    assert len(files) == 3 and any(x['reason'] == 'DEPENDENCY_OR_GIT' for x in omitted)
    all_files, _ = M.enumerate_sources([folder], True)
    assert len(all_files) == 4


def test_links_and_missing_root(folder):
    target = put(folder / 'normal.py', 'x=1\n')
    if os.name != 'nt':
        (folder / 'loop').symlink_to(folder, target_is_directory=True)
        (folder / 'alias.py').symlink_to(target)
    files, omitted = M.enumerate_sources([folder, folder / 'absent'])
    assert len(files) == 1 and any(x.get('blocking') for x in omitted)


def test_locked_hash_and_transport(folder):
    path = put(folder / 'tool.py', 'x=1\n')
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    lock = {'token': {'path': 'VeritasIntelligenceAnalytics/tool.py', 'sha256': expected, 'version': 'v0001'}}
    assert M.inspect_pins(folder, lock)[0]['state'] == 'MATCH'
    path.write_bytes(b'x=1\r\n')
    assert M.inspect_pins(folder, lock)[0]['state'] == 'LINE_ENDINGS_ONLY'
    path.write_bytes(b'x=2\n')
    assert M.inspect_pins(folder, lock)[0]['state'] == 'MISMATCH'
    try:
        M.pinned_path(folder, '../escape.py')
    except ValueError:
        return
    raise AssertionError('Path escape accepted')


def test_findings_do_not_count_strings_as_calls(folder):
    path = put(folder / 'review.py', '# VIA_ACCEL.accel_map(fake)\nx="requests.get(url)"\ndef f(items=[]):\n    try:\n        return 1\n    except:\n        pass\ndef f():\n    return 2\n')
    row = M.inspect_source(path)
    assert not row['accel_calls'] and not row['network_calls']
    assert {'MUTABLE_DEFAULT', 'BARE_EXCEPT', 'SAME_SCOPE_REDEFINITION_REVIEW'} <= {f['rule'] for f in row['findings']}


def test_ps_unverified_never_green(folder):
    path = put(folder / 'test.ps1', 'function F { 1 }\n')
    rows = [M.inspect_source(path)]
    M.merge_ps_results(rows, folder / 'missing.jsonl')
    assert rows[0]['state'] == 'POWERSHELL_AST_UNVERIFIED'
    parsed = {'path': str(path), 'errors': [{'message': 'fixture parse error'}], 'functions': [], 'commands': []}
    put(folder / 'result.jsonl', json.dumps(parsed) + '\n')
    M.merge_ps_results(rows, folder / 'result.jsonl')
    assert rows[0]['state'] == 'ERROR'


def test_source_change_detection(folder):
    a = put(folder / 'a.py', 'x=1\n')
    b = put(folder / 'b.py', 'x=2\n')
    rows = [M.inspect_source(a), M.inspect_source(b)]
    a.write_text('x=3\n'); b.unlink(); put(folder / 'c.py', 'x=4\n')
    changes, _ = M.compare_snapshot(rows, [folder], False)
    assert {r['kind'] for r in changes} == {'ADDED', 'REMOVED', 'CHANGED'}


def test_command_exit_timeout_and_argument_integrity(folder):
    receipts = []
    literal = 'space ; $(no-shell) ` no-exec 中文'
    script = put(folder / 'echo.py', 'import sys\nprint(sys.argv[1])\nraise SystemExit(7)\n')
    row = M.run_command('exit7', [sys.executable, str(script), literal], folder, folder, 5, receipts, os.environ.copy())
    assert row['rc'] == 7 and literal in Path(row['log']).read_text()
    row = M.run_command('timeout', [sys.executable, '-c', 'import time; time.sleep(10)'], folder, folder, 1, receipts, os.environ.copy())
    assert row['rc'] == 124 and row['state'] == 'TIMEOUT'


def test_token_failure_blocks_registered_execution(folder):
    via = folder / 'VIA'
    reg = via / 'supportive modules' / 'registry'
    log = folder / 'verbs.log'
    console = put(reg / 'CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py', f'import sys\nfrom pathlib import Path\nwith Path({str(log)!r}).open("a") as f: f.write(" ".join(sys.argv[1:])+"\\n")\nraise SystemExit(2)\n')
    out = folder / 'reports'
    rc = M.main(['--via-root', str(via), '--root', str(via), '--out', str(out)])
    assert rc == 1 and log.read_text().splitlines() == ['token']
    assert M.read_json(out / 'SUMMARY.json')['state'] == 'RED'
    assert (out / 'VCGC_PANORAMA.html').is_file()
    assert not list(via.rglob('*.pyc'))


def test_missing_root_reports_blocker(folder):
    rc = M.main(['--via-root', str(folder / 'missing'), '--root', str(folder / 'missing'), '--out', str(folder / 'out')])
    report = M.read_json(folder / 'out' / 'SUMMARY.json')
    assert rc == 1 and report['counts']['source_files'] == 0 and report['state'] == 'RED'


def test_html_escapes_source_content(folder):
    report = {'at': 'fixture', 'state': 'RED', 'counts': {}, 'tools': [], 'commands': []}
    rows = [{'path': '<script>alert(1)</script>.py', 'state': 'ERROR', 'findings': []}]
    M.save_reports(folder, report, rows, [])
    text = (folder / 'VCGC_PANORAMA.html').read_text()
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in text and '<script>alert(1)</script>' not in text


def test_station_reference_integrity(folder):
    inv = M.read_json(ROOT / 'reference' / 'VIA_VCGC_FunctionInventory_SSOT_v0191.json')
    assert len(inv['stations']) == 328
    assert len({s['id'] for s in inv['stations']}) == len(inv['stations'])
    assert any(s.get('argv') == ['mcp', 'selftest'] for s in inv['stations'])


def test_successful_orchestration_uses_registered_full_test(folder):
    via = folder / 'VeritasIntelligenceAnalytics'
    reg = via / 'supportive modules' / 'registry'
    console_source = '''# [VIA:ACCEL-BRIDGE]
import json, sys
from pathlib import Path
via = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
if args == ['test', '--full']:
    report = via / 'VIA_Reports' / 'vcgc' / 'TEST_latest.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'lamp':'GREEN','counts':{'GREEN':2},'rows':[{'id':'fixture1'},{'id':'fixture2'}]}))
print('FIXTURE ONLY', args)
'''
    put(reg / 'CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py', console_source)
    token = put(reg / 'fixture_token.py', '# [VIA:ACCEL-BRIDGE]\nimport sys\nprint("304_NOT_MODIFIED" if "--if-etag" in sys.argv else "etag=0123456789abcdef")\n')
    support = put(via / 'supportive modules' / 'fixture_support.py', '# [VIA:ACCEL-BRIDGE]\n')
    put(via / 'supportive modules' / 'VIA_SuperAccel_Module.py', '# [VIA:ACCEL-BRIDGE]\ndef activate(apply_limits=True):\n    return {"celeritas": True, "thread_budget":1, "applied":{"OMP_NUM_THREADS":"1"}}\n')
    lock = {}
    for family in M.PIN_FAMILIES:
        file = token if family == 'token' else support
        lock[family] = {'path': str(file.relative_to(via)), 'version':'fixture', 'sha256':M.sha_file(file)}
    M.write_json(reg / 'VIA_ToolVersion_Lock_v0100.json', lock)
    M.write_json(reg / 'VIA_VCGC_FunctionInventory_SSOT_v0001.json', {'version':'fixture','stations':[{'id':'fixture1'},{'id':'fixture2'}]})
    out = folder / 'out'
    rc = M.main(['--via-root', str(via), '--root', str(via), '--out', str(out)])
    report = M.read_json(out / 'SUMMARY.json')
    assert rc == 2  # no real PS acceleration receipt: cannot become GREEN
    assert report['registered_tests']['stations_returned'] == 2
    assert report['etag_check']['state'] == 'VERIFIED_304'
    commands = [r['command'][2:] for r in report['commands']]
    assert ['test', '--full'] in commands and ['go'] not in commands
    assert report['counts']['source_changes'] == 0 and not list(via.rglob('*.pyc'))


def main():
    tests = [(name, fn) for name, fn in globals().copy().items() if name.startswith('test_') and callable(fn)]
    for name, test in tests:
        with tempfile.TemporaryDirectory(prefix='vcgc_fixture_') as temporary:
            try:
                test(Path(temporary))
                RESULTS.append({'test': name, 'passed': True})
            except Exception as exc:
                RESULTS.append({'test': name, 'passed': False, 'error': f'{type(exc).__name__}: {exc}'})
                print(f'[FAIL] {name}: {exc}')
    result = {'scope': 'Delivered runner isolated Linux regression tests; not Windows/VIA production acceptance', 'at': M.utc_now(), 'passed': sum(x['passed'] for x in RESULTS), 'total': len(RESULTS), 'tests': RESULTS, 'windows_ps7': 'NOT_RUN'}
    M.write_json(ROOT / 'DELIVERY_QA.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(x['passed'] for x in RESULTS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
