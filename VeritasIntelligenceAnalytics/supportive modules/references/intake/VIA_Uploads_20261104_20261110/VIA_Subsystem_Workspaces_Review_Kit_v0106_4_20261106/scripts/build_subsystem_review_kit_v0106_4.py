#!/usr/bin/env python3
"""Create-once candidate kit; no install, registry write, network or engine activation."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'v0106.4'
DEFAULT_OUT = ROOT.parent / 'VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip'
FILES = [
    'public/governance-preview-v0105.3.html',
    'scripts/governance_v0105_3.js',
    'scripts/build_preview_transport_v0105_3.py',
    'data/private_transport_v0105_3.json',
    'public/governance_v0105_3.html.v0105.3.gz',
    'tests/resize_observer_uat_v0106_4.py',
    'artifacts/resize_observer_uat_v0106_4/receipt.json',
    'public/subsystems-v0106.4.html',
    *[f'public/system-v0106.4-{s}.html' for s in ('vcgc', 'vdf', 'vrn', 'vqg', 'vap', 'database')],
    'public/veritas_logo_header_v0105.png',
    'data/brand_asset_v0105.json',
    'data/subsystem_manifest_v0106_4.json',
    'data/subsystem_live_observations_v0106.json',
    'data/subsystem_review_v0106.json',
    'data/system_matrix.json', 'data/system_coverage.json',
    'data/governance_inventory_v0105.json',
    'data/token_engine_candidate_v0100.json', 'data/mcp_candidate_v0105.json',
    'scripts/build_subsystem_workspaces_v0106_4.py',
    'scripts/subsystem_v0106_4.html', 'scripts/subsystem_v0106_4.css', 'scripts/subsystem_v0106_4.js',
    'scripts/stage_subsystem_workspaces_v0106_4.py',
    'scripts/build_subsystem_review_kit_v0106_4.py',
    'scripts/run_subsystem_checks_v0106_4.py',
    'scripts/Start-VIA-MatrixGovernance-Candidate-v0106_1.ps1',
    'scripts/via_governance_mcp_v0105.py', 'scripts/mcp_stdio_smoke_v0105_2.py',
    'scripts/test_token_tools_v0104.py',
    'engines/tooling/via_agent_os_unified_readonly_hardened.py',
    'tests/test_subsystem_workspaces_v0106_4.py', 'tests/subsystem_ui_uat_v0106_4.py',
    'tests/test_stage_subsystem_workspaces_v0106_4.py', 'tests/test_governance_mcp_v0105.py',
    'docs/SUBSYSTEM_WORKSPACES_HANDOVER_v0106_4.md',
    'docs/MCP_WINDOWS_COMPLETE_GUIDE_v0105_2.md',
    'docs/FIVE_SYSTEM_RED_REPAIR_PLAN_v0105_2.md',
    'docs/MATRIX_REFERENCE_BRIDGE_v0106.md',
    'artifacts/subsystem_token_context_v0106.json',
    'artifacts/token_tools_v0106_20261106.json',
    'artifacts/mcp_stdio_smoke_v0106_20261106_verified.json',
    'artifacts/reference_ui_startup_v0106_20261106.json',
    'artifacts/matrix_reference_v0106_20261106/receipt.json',
    'artifacts/github_read_health_v0106_20261106_verified.json',
    'artifacts/subsystem_ui_uat_v0106_4_verified/receipt.json',
]
MODEL_FILE = 'VIA_Matrix_Governance_Full_Model_v0105_1_20261106.json.gz'
MODEL_SHA = 'c3b2b84d16abbe3ae1ab8984dc6fd933b6aceef18372d1fea16d94d694691ff1'


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def physical_file(path: Path) -> bytes:
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f'STOP missing/non-physical source: {path}')
    return path.read_bytes()


def create(root: Path, out: Path) -> dict:
    spec = importlib.util.spec_from_file_location('fixed_stage', root / 'scripts/stage_subsystem_workspaces_v0106_4.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('STOP fixed verifier missing')
    stage = importlib.util.module_from_spec(spec); spec.loader.exec_module(stage)
    stage.chain(out.parent)
    if not out.parent.is_dir() or out.exists() or out.with_suffix(out.suffix + '.sha256').exists():
        raise FileExistsError('STOP output directory must exist and ZIP/sidecar must be new')
    model_path = root / 'data/source_model_v0105.json.gz'
    if not model_path.exists():
        model_path = root.parent / MODEL_FILE
    model = physical_file(model_path)
    if sha(model) != MODEL_SHA:
        raise ValueError('STOP fixed model source drift')
    ro_receipt = json.loads(physical_file(root / 'artifacts/resize_observer_uat_v0106_4/receipt.json'))
    if ro_receipt.get('status') != 'PASS' or ro_receipt.get('checks_passed') != ro_receipt.get('checks_total'):
        raise ValueError('STOP ResizeObserver stress not passing')
    ui_receipt = json.loads(physical_file(root / 'artifacts/subsystem_ui_uat_v0106_4_verified/receipt.json'))
    if ui_receipt.get('status') != 'PASS' or ui_receipt.get('checks_passed') != ui_receipt.get('checks_total'):
        raise ValueError('STOP newest full UI UAT not passing')
    if any(ui_receipt.get(k) for k in ('external_requests', 'page_errors', 'console_errors')):
        raise ValueError('STOP UI errors/external calls')
    bodies = {name: physical_file(root / name) for name in FILES}
    bodies['data/source_model_v0105.json.gz'] = model
    bodies['public/index.html'] = bodies['public/subsystems-v0106.4.html']
    routes = [{'path': '/', 'title': 'VIA Independent Subsystems v0106.4'}, {'path': '/subsystems-v0106.4.html', 'title': 'VIA Hub'}]
    routes.append({'path': '/governance-preview-v0105.3.html', 'title': 'Global Governance Snapshot'})
    routes += [{'path': f'/system-v0106.4-{s}.html', 'title': s.upper()} for s in ('vcgc', 'vdf', 'vrn', 'vqg', 'vap', 'database')]
    bodies['public/manus-routes.json'] = (json.dumps({'routes': routes}, ensure_ascii=False, indent=2) + '\n').encode()
    readme = ('# VIA 六系統獨立工作台候選包 v0106.4\n\n開啟 public/index.html；詳讀 docs/SUBSYSTEM_WORKSPACES_HANDOVER_v0106_4.md。\n\n這是候選 UI / MCP stdio / Token工具審查包，不是production/native六系統部署。\n\nPDF有AI摘要與全量分卷，JSON/MD包含完整矩陣；Windows/正式VCGC/SSOT/Database未啟動。\n')
    bodies['README.md'] = readme.encode()
    for name in bodies:
        stage.safe_name(name)
    records = {name: {'bytes': len(body), 'sha256': sha(body)} for name, body in sorted(bodies.items())}
    manifest = {'schema': 'VIA-SUBSYSTEM-REVIEW-KIT/1.0', 'version': VERSION,
                'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'policy': 'EXISTING_PLUS_NEW_ATLAS_AND_LOCAL_TOOLS',
                'release_ready': False, 'production_deployment': False, 'formal_registration': False,
                'existing_engine_modified': False, 'contracts_activated': False,
                'native_runtime': 'NOT_RUN', 'scope': 'candidate UI plus pinned local MCP/Token tools only',
                'file_count': len(records), 'files': records, 'model_sha256': MODEL_SHA,
                'PDF_scope': 'AI summary or bounded all-record parts; user saves each part through print dialog',
                'source_UI_receipt_sha256': sha(physical_file(root / 'artifacts/subsystem_ui_uat_v0106_4_verified/receipt.json'))}
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(bodies.items()):
            z.writestr(name, body)
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        z.writestr('SHA256SUMS', ''.join(f'{records[name]["sha256"]}  {name}\n' for name in records))
    digest = sha(out.read_bytes())
    stage.verify(out, digest)
    sidecar = out.with_suffix(out.suffix + '.sha256')
    with sidecar.open('x', encoding='utf-8') as f:
        f.write(f'{digest}  {out.name}\n')
    return {'status': 'PASS_BUILT_NOT_DEPLOYED', 'version': VERSION, 'zip': str(out), 'sha256': digest,
            'file_count': len(records), 'zip_members': len(records) + 2,
            'uncompressed_bytes': sum(len(v) for v in bodies.values()), 'formal_registration': False}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    print(json.dumps(create(a.root.resolve(), a.out.absolute()), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
