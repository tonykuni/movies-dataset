from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics')
PY = '/home/ubuntu/work/quantguard_venv/bin/python'
OUT = Path('/home/ubuntu/work/vrn_b526_automated_integration_latest')
EVID = ROOT / 'VIA_Reports/handover/evidence_b526_vrn_integration'
OUT.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], name: str, cwd: Path = ROOT) -> dict:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    text = p.stdout + ('\n' + p.stderr if p.stderr else '')
    out = OUT / name
    out.write_text(text, encoding='utf-8')
    return {
        'command': cmd,
        'returncode': p.returncode,
        'output_file': str(out),
        'tail': text[-5000:],
    }


def load(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


started = datetime.now(timezone.utc)
selftests = run(['bash', '/home/ubuntu/work/run_vrn_selftests_b524.sh'], 'vrn_selftests.txt', cwd=ROOT)
pdf = run([PY, '/home/ubuntu/work/run_vrn_pdf_validation_b524.py'], 'vrn_pdf_validation.txt', cwd=ROOT)
# The full VIA/VDF integration runner re-checks real DuckDB integrity and central state.
full = run([PY, '/home/ubuntu/work/run_via_vrn_full_integration_b526.py'], 'via_vrn_vdf_full_integration.txt', cwd=ROOT)

selftest_text = Path(selftests['output_file']).read_text(encoding='utf-8', errors='replace')
module_results = {}
for name in ['vrn_072', 'vrn_073', 'vrn_074', 'vrn_080', 'vrn_082', 'vrn_086', 'nlp_744']:
    p = OUT / f'{name}.txt'
    if p.exists():
        text = p.read_text(encoding='utf-8', errors='replace')
    else:
        text = ''
    rcs = re.findall(r'RC=(\d+)', text)
    module_results[name] = {
        'output_file': str(p),
        'rc': int(rcs[-1]) if rcs else None,
        'passed': bool(rcs) and int(rcs[-1]) == 0,
        'summary_tail': text[-1200:],
    }
# run_vrn_selftests writes per-module files under its fixed output directory.
fixed = Path('/home/ubuntu/work/vrn_pdf_acceptance_b524')
for name in module_results:
    src = fixed / f'{name}.txt'
    dst = OUT / f'{name}.txt'
    if src.exists():
        shutil.copy2(src, dst)
        text = dst.read_text(encoding='utf-8', errors='replace')
        rcs = re.findall(r'RC=(\d+)', text)
        module_results[name].update({'output_file': str(dst), 'rc': int(rcs[-1]) if rcs else None, 'passed': bool(rcs) and int(rcs[-1]) == 0, 'summary_tail': text[-1200:]})

vrn_pdf = load(Path('/home/ubuntu/work/vrn_pdf_validation_b524.json'), {})
full_json = load(Path('/home/ubuntu/work/full_integration_b526/VIA_VRN_VDF_FULL_INTEGRATION_B526.json'), {})

vrn = vrn_pdf.get('vrn', {})
pdf_result = vrn_pdf.get('pdf', {})
module_selftests_pass = all(x['passed'] for x in module_results.values())
software_green = (
    selftests['returncode'] == 0
    and pdf['returncode'] == 0
    and full['returncode'] == 0
    and module_selftests_pass
    and vrn.get('state') == 'GREEN'
    and vrn.get('compile_ok') == vrn.get('active_python_files')
    and vrn.get('import_ok') == vrn.get('active_python_files')
    and pdf_result.get('state') == 'GREEN'
)
full_chain = full_json.get('verdict')

payload = {
    'schema': 'VIA.VRN.B526.AutomatedIntegrationTest.v1',
    'started_at': started.isoformat(),
    'finished_at': datetime.now(timezone.utc).isoformat(),
    'software_verdict': 'GREEN' if software_green else 'RED',
    'full_chain_verdict': full_chain,
    'module_selftests': module_results,
    'vrn_panorama': vrn,
    'pdf_dual_engine': pdf_result,
    'via_vrn_vdf_full_integration': full_json,
    'runner_commands': {'selftests': selftests, 'pdf': pdf, 'full_integration': full},
    'limitations': [
        'The VRN active-tree gate excludes references/intake by policy.',
        'The 64 original Windows PDF/DOCX files are not mounted; no original-file content-level pass is claimed.',
        'PDF dual-engine result uses the retained synthetic regression fixture.',
    ],
}
json_out = OUT / 'VRN_B526_AUTOMATED_INTEGRATION_RESULT.json'
json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')

# Copy evidence into the VIA mother-system handover folder.
for src in [json_out, Path(selftests['output_file']), Path(pdf['output_file']), Path(full['output_file'])]:
    shutil.copy2(src, EVID / src.name)
for name in module_results:
    src = OUT / f'{name}.txt'
    if src.exists():
        shutil.copy2(src, EVID / src.name)

md_out = EVID / 'VIA_VRN_B526_AUTOMATED_INTEGRATION_TEST.md'
rows = []
for name, item in module_results.items():
    rows.append(f"| {name} | RC={item['rc']} | {'PASS' if item['passed'] else 'FAIL'} |")
md_out.write_text(f'''# VRN B526 自動化整合測試報告

**完成時間：** {payload['finished_at']}
**VRN 軟體整合判定：** **{payload['software_verdict']}**
**VIA/VDF 完整串接判定：** **{full_chain}**

## 測試矩陣

| 模組 | 退出碼 | 結果 |
|---|---:|---|
{chr(10).join(rows)}

| 項目 | 實測結果 |
|---|---|
| VRN active compile | {vrn.get('compile_ok')}/{vrn.get('active_python_files')} |
| VRN active import | {vrn.get('import_ok')}/{vrn.get('active_python_files')} |
| VRN panorama state | {vrn.get('state')} |
| PDF fitz／pdfplumber | {pdf_result.get('state')} |
| PDF pages | fitz={pdf_result.get('fitz', {}).get('pages')}; pdfplumber={pdf_result.get('pdfplumber', {}).get('pages')} |
| PDF tables | {pdf_result.get('pdfplumber', {}).get('tables')} tables; {pdf_result.get('pdfplumber', {}).get('nonempty_cells')} non-empty cells |
| VIA/VDF full integration | {full_chain} |

## 結論

VRN B526 的 active module compile/import、正主 selftest、NLP 掛載、PDF 雙引擎 regression 與 VIA/VDF 串接均已由實際命令執行並保存輸出。軟體整合 gate 判定為 **{payload['software_verdict']}**。完整鏈路仍受 64 份未掛載 Windows 原始 PDF/DOCX 限制，因此整體內容級驗收維持 **{full_chain}**，不將 synthetic fixture 結果冒稱為原始報告通過。

機器結果：`VRN_B526_AUTOMATED_INTEGRATION_RESULT.json`
各模組輸出與命令輸出均收容在同一 evidence 目錄。
''', encoding='utf-8')

# Exclude pycache generated by any compile/import probing from evidence.
for p in EVID.rglob('__pycache__'):
    shutil.rmtree(p, ignore_errors=True)

# Hash all evidence except the checksum file itself.
checksum = EVID / 'SHA256SUMS.txt'
files = sorted(p for p in EVID.iterdir() if p.is_file() and p.name != checksum.name)
import hashlib
lines = []
for p in files:
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    lines.append(f'{h}  {p}')
checksum.write_text('\n'.join(lines) + '\n', encoding='utf-8')

print(json.dumps({
    'software_verdict': payload['software_verdict'],
    'full_chain_verdict': full_chain,
    'module_selftests_pass': module_selftests_pass,
    'active_compile': f"{vrn.get('compile_ok')}/{vrn.get('active_python_files')}",
    'active_import': f"{vrn.get('import_ok')}/{vrn.get('active_python_files')}",
    'report_json': str(json_out),
    'report_md': str(md_out),
    'evidence_dir': str(EVID),
}, ensure_ascii=False, indent=2))
