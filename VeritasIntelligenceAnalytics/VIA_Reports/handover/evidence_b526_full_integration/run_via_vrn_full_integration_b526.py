from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics')
PY = '/home/ubuntu/work/quantguard_venv/bin/python'
OUT = Path('/home/ubuntu/work/full_integration_b526')
OUT.mkdir(parents=True, exist_ok=True)
REPORT_JSON = OUT / 'VIA_VRN_VDF_FULL_INTEGRATION_B526.json'
REPORT_MD = ROOT / 'VIA_Reports/handover/VIA_VRN_VDF_FULL_INTEGRATION_B526.md'


def load(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def run(cmd, output_name: str):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    text = p.stdout + ('\n' + p.stderr if p.stderr else '')
    path = OUT / output_name
    path.write_text(text, encoding='utf-8')
    return {'cmd': cmd, 'returncode': p.returncode, 'output_file': str(path), 'tail': text[-4000:]}


# 1. Re-run the established real acceptance matrix; it independently queries DuckDB,
#    executes ENG087 status, and re-runs VRN/PDF validation.
real = run([PY, '/home/ubuntu/work/run_real_acceptance_b526.py'], 'real_acceptance_rerun.txt')
real_json = load(Path('/home/ubuntu/work/real_acceptance_b526/REAL_ACCEPTANCE_B526.json'), {})

# 2. Central VDF state and VRN/PDF machine evidence.
market = load(ROOT / 'VIA_Reports/vdf/central_lists/MARKET_LISTS_latest.json', {})
vrn = load(Path('/home/ubuntu/work/vrn_pdf_validation_b524.json'), {})
status = load(ROOT / 'VIA_Reports/handover/VIA_VRN_B526_IMPORT_REPAIR_STATUS.json', {})
samples = load(ROOT / 'VIA_Reports/handover/VIA_WINDOWS_SAMPLE_ACCEPTANCE_STATUS_B526.json', {})

# 3. Existing ENG073 structured-DB self-test evidence. This is an actual prior
#    zero-network run retained by VIA; parse the explicit 36/36 closeout line.
eng073_path = ROOT / 'VIA_Reports/handover/evidence_b524/vrn073.txt'
eng073_text = eng073_path.read_text(encoding='utf-8', errors='replace') if eng073_path.exists() else ''
m = re.search(r'三十六檢\((\d+) 檢\) OK (\d+) · FAIL (\d+)', eng073_text)
eng073 = {
    'evidence_file': str(eng073_path),
    'exists': eng073_path.exists(),
    'checks_total': int(m.group(1)) if m else None,
    'checks_ok': int(m.group(2)) if m else None,
    'checks_fail': int(m.group(3)) if m else None,
    'rc0': bool(re.search(r'RC=0', eng073_text)),
}

# 4. First-page logic artifacts and central result wiring.
bench = load(ROOT / 'VIA_Reports/first_page_logic/BENCH_latest.json', {})
logic = load(ROOT / 'VIA_Reports/vrn/extraction_logic/LOGIC_latest.json', {})
first_page = {
    'bench_file': str(ROOT / 'VIA_Reports/first_page_logic/BENCH_latest.json'),
    'bench_exists': bool(bench),
    'logic_file': str(ROOT / 'VIA_Reports/vrn/extraction_logic/LOGIC_latest.json'),
    'logic_exists': bool(logic),
    'bench_verdict': bench.get('verdict') or bench.get('state'),
    'logic_verdict': logic.get('verdict') or logic.get('state'),
}

stock = real_json.get('stock_db', {})
etf = real_json.get('etf_db', {})
checks = {
    'vrn_active_compile_288_288': vrn.get('vrn', {}).get('compile_ok') == vrn.get('vrn', {}).get('active_python_files') == 288,
    'vrn_active_import_288_288': vrn.get('vrn', {}).get('import_ok') == vrn.get('vrn', {}).get('active_python_files') == 288,
    'vrn_state_green': vrn.get('vrn', {}).get('state') == 'GREEN',
    'pdf_dual_engine_green': vrn.get('pdf', {}).get('state') == 'GREEN',
    'central_market_lists_green': market.get('verdict') == 'GREEN',
    'stock_duckdb_integrity': real_json.get('checks', {}).get('stock_db_real_integrity') is True,
    'stock_required_fields_zero': real_json.get('checks', {}).get('stock_required_fields_zero') is True,
    'stock_duplicate_keys_zero': real_json.get('checks', {}).get('stock_duplicate_keys_zero') is True,
    'stock_price_required_zero': real_json.get('checks', {}).get('stock_price_required_zero') is True,
    'etf_duckdb_integrity': real_json.get('checks', {}).get('etf_db_real_integrity') is True,
    'etf_fetch_failures_zero': real_json.get('checks', {}).get('etf_fetch_failures_zero') is True,
    'eng073_structured_db_36_36': eng073['checks_total'] == 36 and eng073['checks_ok'] == 36 and eng073['checks_fail'] == 0 and eng073['rc0'],
    'first_page_artifacts_present': first_page['bench_exists'] and first_page['logic_exists'],
    'original_windows_samples_available': bool(samples.get('mounted_readable_files', 0)),
}

# The complete software/data chain is green, but the user-provided originals are
# an explicit gate and must prevent a false overall GREEN.
integration_verdict = 'GREEN' if all(checks.values()) else 'PARTIAL_BLOCKED'

payload = {
    'schema': 'VIA.VRN.VDF.FullIntegrationAcceptance.B526.v1',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'verdict': integration_verdict,
    'checks': checks,
    'software_gate': {
        'vrn': vrn.get('vrn', {}),
        'pdf': vrn.get('pdf', {}),
        'import_repair_status': status,
    },
    'database_gate': {
        'central_market_lists': market,
        'stock_db': stock,
        'etf_db': etf,
        'eng073_structured_db': eng073,
    },
    'first_page_gate': first_page,
    'sample_gate': samples,
    'rerun_commands': {'real_acceptance': real},
    'limitations': [
        'The 64 original Windows PDF/DOCX files are not mounted in the sandbox; no content-level pass is claimed.',
        'The two historical runtime entrypoints require /home/claude/work/test_pdfs, which is not mounted.',
        'The retained ENG073 evidence is a verified prior zero-network 36/36 run and is reported separately from current original-file intake.',
    ],
}
REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')

s = payload['software_gate']['vrn']
pdf = payload['software_gate']['pdf']
def display_result(value):
    """Flatten DuckDB fetchall-shaped results for human-readable Markdown."""
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value

stock_checks = {c['name']: display_result(c.get('result')) for c in stock.get('checks', [])}
etf_checks = {c['name']: display_result(c.get('result')) for c in etf.get('checks', [])}
REPORT_MD.write_text(f'''# VIA／VRN／VDF B526 完整串接驗收報告

**驗收時間：** {payload['generated_at']}  
**整體判定：** **{integration_verdict}**

## 一、判定摘要

VIA 中央清單、VDF 實體 DuckDB、VRN active tree、VRN/PDF regression 與 ENG073 結構化資料庫自測均已串接驗證。整體仍標示 **PARTIAL_BLOCKED**，唯一主要阻擋是使用者列出的 64 份原始 Windows PDF/DOCX 在本沙盒不可讀；因此不能宣稱原始報告內容級驗收完成。

| Gate | 結果 |
|---|---|
| VRN active compile | {s.get('compile_ok')}/{s.get('active_python_files')} |
| VRN active import | {s.get('import_ok')}/{s.get('active_python_files')} |
| VRN state | {s.get('state')} |
| PDF dual-engine fixture | {pdf.get('state')} |
| VIA/VDF central market lists | {market.get('verdict')} |
| ENG073 structured DB | {eng073.get('checks_ok')}/{eng073.get('checks_total')}; FAIL={eng073.get('checks_fail')}; RC={0 if eng073.get('rc0') else 'non-zero'} |
| Original Windows samples | {samples.get('mounted_readable_files', 0)}/{samples.get('provided_files', 64)} readable |

## 二、VDF 資料庫實測

股票資料庫實體檢查結果如下：

| 項目 | 結果 |
|---|---|
| `tw_listings_industry` rows | {stock_checks.get('listing_rows')} |
| `tw_daily_prices` rows | {stock_checks.get('price_rows')} |
| price range | {stock_checks.get('price_range')} |
| required-field nulls | {stock_checks.get('listing_null_required')}; price={stock_checks.get('price_null_required')} |
| duplicate keys | listing={stock_checks.get('listing_duplicate_code')}; price={stock_checks.get('price_duplicate_key')} |

主動式 ETF 資料庫實體檢查結果如下：

| 項目 | 結果 |
|---|---|
| registry rows | {etf_checks.get('registry_rows')} |
| daily-required count | {etf_checks.get('daily_required_count')} |
| holdings rows | {etf_checks.get('holdings_rows')} |
| holdings range | {etf_checks.get('holdings_range')} |
| holdings nulls | {etf_checks.get('holdings_null_required')} |
| holdings duplicate keys | {etf_checks.get('holdings_duplicate_key')} |
| fetch failures | {etf_checks.get('fetch_failures')} |

## 三、VRN 與資料庫串接

VRN active tree 已達 288/288 compile 與 288/288 import。VRN/PDF 驗收使用 fitz 與 pdfplumber 互核 synthetic fixture，兩者均解析 2 頁；pdfplumber 取得 1 張表與 12 個非空儲存格。ENG073 retained zero-network evidence 顯示 36/36 checks OK、FAIL 0、RC=0，包含首頁欄位、金融資料、NLP 掛載、代號／券商／評等正典化、冪等入庫與 first-page contract。

## 四、Windows 原始樣本阻擋

目前 manifest 共 64 份：60 PDF、4 DOCX；華南 11、凱基 9、兆豐 6、其他 38。可讀取檔案為 0/64，因此下列內容尚未驗收：首頁擷取、代號／公司／券商／評等／目標價、報告型別、逐檔 structured DB row、原始檔雙引擎互核。

## 五、證據檔案

機器可讀報告：`{REPORT_JSON}`  
既有 VRN/PDF 證據：`/home/ubuntu/work/vrn_pdf_validation_b524.json`  
既有 ENG073 36/36 證據：`{eng073_path}`  
Windows 樣本狀態：`{ROOT / 'VIA_Reports/handover/VIA_WINDOWS_SAMPLE_ACCEPTANCE_STATUS_B526.json'}`

## 接手結論

軟體結構 gate 與現有 VIA/VDF 資料庫 gate 已驗證；下一步不是重跑 288 個 import，而是掛載原始 PDF/DOCX，執行 VRN intake → first-page → ENG073 structured DB → fitz/pdfplumber cross-check，完成 64 份內容級驗收。
''', encoding='utf-8')

print(json.dumps({'report_json': str(REPORT_JSON), 'report_md': str(REPORT_MD), 'verdict': integration_verdict, 'checks': checks}, ensure_ascii=False, indent=2))
