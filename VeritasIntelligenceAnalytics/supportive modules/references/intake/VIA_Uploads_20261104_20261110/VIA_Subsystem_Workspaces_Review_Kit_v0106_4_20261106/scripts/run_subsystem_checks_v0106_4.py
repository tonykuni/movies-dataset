#!/usr/bin/env python3
"""Finite fixed checks for the v0106.4 review kit; writes only to a new external output."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(root: Path, out: Path, ui: bool = True) -> dict:
    root = root.resolve(strict=True)
    out = out.absolute()
    if out.exists() or out.is_relative_to(root):
        raise ValueError('STOP output must be a new directory outside package root')
    if not out.parent.is_dir() or any(p.is_symlink() for p in (out.parent, *out.parents)):
        raise ValueError('STOP physical existing output parent required')
    manifest_path = root / 'manifest.json'
    if manifest_path.exists():
        spec = importlib.util.spec_from_file_location('fixed_verifier', root / 'scripts/stage_subsystem_workspaces_v0106_4.py')
        if spec is None or spec.loader is None:
            raise RuntimeError('STOP fixed verifier unavailable')
        verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
        manifest = verifier.strict(manifest_path.read_bytes())
        if manifest.get('version') != 'v0106.4':
            raise ValueError('STOP package version mismatch')
        for flag in ('release_ready', 'production_deployment', 'formal_registration', 'existing_engine_modified', 'contracts_activated'):
            if manifest.get(flag) is not False:
                raise ValueError('STOP package safety flag missing/unsafe')
        for name, info in manifest['files'].items():
            verifier.safe_name(name)
            p = verifier.chain(root / name)
            raw = p.read_bytes()
            if len(raw) != info['bytes'] or hashlib.sha256(raw).hexdigest() != info['sha256']:
                raise ValueError(f'STOP payload source drift: {name}')
    out.mkdir(exist_ok=False)
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    commands = [
        ('ui_whitebox', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_subsystem_workspaces_v0106_4.py']),
        ('stage_whitebox', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_stage_subsystem_workspaces_v0106_4.py']),
        ('mcp_whitebox', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_governance_mcp_v0105.py']),
        ('token_cli', [sys.executable, '-B', 'scripts/test_token_tools_v0104.py', '--package-root', str(root), '--out', str(out / 'token.json')]),
        ('mcp_stdio', [sys.executable, '-B', 'scripts/mcp_stdio_smoke_v0105_2.py', '--package-root', str(root), '--out', str(out / 'mcp_stdio.json')]),
    ]
    if ui:
        commands.append(('resize_observer', [sys.executable, '-B', 'tests/resize_observer_uat_v0106_4.py', '--root', str(root), '--out', str(out / 'resize')]))
        commands.append(('ui_e2e', [sys.executable, '-B', 'tests/subsystem_ui_uat_v0106_4.py', '--root', str(root), '--out', str(out / 'ui')]))
    records = []
    status = 'PASS'
    for name, argv in commands:
        print('RUN', name, flush=True)
        try:
            completed = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=900)
            output = completed.stdout + '\n' + completed.stderr
            log = out / (name + '.log'); log.write_text(output, encoding='utf-8')
            count = re.search(r'Ran (\d+) tests?', output)
            records.append({'name': name, 'exit_code': completed.returncode, 'unit_count': int(count.group(1)) if count else None, 'log': log.name, 'sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
            if completed.returncode:
                status = 'FAIL'; break
        except subprocess.TimeoutExpired:
            records.append({'name': name, 'status': 'TIMEOUT'}); status = 'FAIL_TIMEOUT'; break
    receipt = {'version': 'v0106.4', 'status': status, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
               'root': str(root), 'commands': records, 'ui_requested': ui,
               'formal_registration': False, 'production_deployment': False,
               'PC': 'NOT_RUN', 'existing_engine_modified': False,
               'scope': 'fixed finite local candidate checks only; no install, shell, registry, provider or live PC/VCGC mutation'}
    for name, path in [('token', out / 'token.json'), ('mcp_stdio', out / 'mcp_stdio.json'), ('ui', out / 'ui/receipt.json')]:
        if path.exists():
            raw = path.read_bytes(); item = json.loads(raw)
            receipt[name] = {'status': item.get('status'), 'count': item.get('count'), 'checks_total': item.get('checks_total'), 'checks_passed': item.get('checks_passed'), 'sha256': hashlib.sha256(raw).hexdigest()}
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--skip-ui', action='store_true', help='Explicit skip; receipt records UI was not run')
    a = parser.parse_args()
    result = run(a.package_root, a.out, not a.skip_ui)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
