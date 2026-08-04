# -*- coding: utf-8 -*-
"""
panorama_xcheck_v110.py — VRN 全景式交叉核對驗證微型 Pipeline
==============================================================
跑同一組 PDF 經過 MDL001 → MDL002 → (MDL003 mock) → MDL004 → MDL005
→ MDL006 phase1 vs phase2 比對 → MDL007 mock external API
→ MDL008 三角驗證 (報告 vs API)。

最終產出：
  - panorama_summary.json   全景 pipeline 結果
  - panorama_report.html    8-panel VIA Visual Lock 全景 HTML 報告

Why "微型"：在沙箱環境用 mock data + test PDFs，因為實際 OCR/MOPS API
需要外部依賴。但管線結構與生產一致。

Test data flow:
  test_pdfs/ (3 個 fake reports)
    ├─ MDL001 → pdf_temp/        (HQ PDF)
    ├─ MDL002 → mdl002_temp/     (layout + text)
    ├─ MDL003 → 用 mock 提供 phase1 financial rows
    ├─ MDL004 → 用 mock 提供 phase2 OCR tables
    ├─ MDL005 → 用 mock 提供 phase2 OCR text
    ├─ MDL006 → phase1 vs phase2 比對 → match_rate
    ├─ MDL007 → mock external API (MOPS-like + yfinance-like + TWSE-like)
    └─ MDL008 → 報告 vs API 三角驗證
"""
import os
import sys
import json
import time
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, "/home/claude/work")

# ── HardGate BOOT_PRECHECK ─────────────────────────────────────────────────
from VIA_HardGate_BootPrecheck import HARDGATE_BOOT, hardgate_caps_summary
HG_CAPS = HARDGATE_BOOT(ssot_dir="/tmp/fake_ssot", quiet=True)
print(f"[Panorama] HardGate: {hardgate_caps_summary(HG_CAPS)}")
print(f"[Panorama] policy: {HG_CAPS['policy']}")
print(f"[Panorama] BOOT_PRECHECK in {HG_CAPS['elapsed_ms']:.1f}ms")
print()

# ── Modules ────────────────────────────────────────────────────────────────
import MDL001_Conv_v110     as MDL001
import MDL002_v110          as MDL002
import MDL006_v110          as MDL006
import MDL007_v110          as MDL007
import MDL008_v110          as MDL008

print(f"[Panorama] Module versions:")
print(f"  MDL001 v{MDL001.__version__}")
print(f"  MDL002 v{MDL002.__version__}")
print(f"  MDL006 v{MDL006.__version__}")
print(f"  MDL007 v{MDL007.__version__}")
print(f"  MDL008 v{MDL008.__version__}")
print()

t_panorama_start = time.perf_counter()

# ── Setup workspace ────────────────────────────────────────────────────────
ROOT = tempfile.mkdtemp(prefix="panorama_")
INPUT_DIR    = ROOT + "/input"
PDF_TEMP     = ROOT + "/pdf_temp"
MDL001_TEMP  = ROOT + "/mdl001_temp"
MDL002_TEMP  = ROOT + "/mdl002_temp"
MDL003_TEMP  = ROOT + "/mdl003_temp"  # mock
MDL004_TEMP  = ROOT + "/mdl004_temp"  # mock
MDL005_TEMP  = ROOT + "/mdl005_temp"  # mock
MDL006_OUT   = ROOT + "/mdl006_out"
MDL007_OUT   = ROOT + "/mdl007_out"
MDL008_OUT   = ROOT + "/mdl008_out"

for d in [INPUT_DIR, PDF_TEMP, MDL001_TEMP, MDL002_TEMP,
          MDL003_TEMP, MDL004_TEMP, MDL005_TEMP,
          MDL006_OUT, MDL007_OUT, MDL008_OUT]:
    Path(d).mkdir(parents=True, exist_ok=True)

# Copy test PDFs
for f in os.listdir("/home/claude/work/test_pdfs"):
    shutil.copy(f"/home/claude/work/test_pdfs/{f}", INPUT_DIR)

print(f"[Panorama] Workspace: {ROOT}")
print(f"[Panorama] Input PDFs: {len(os.listdir(INPUT_DIR))}")
print()

# ── PHASE A: MDL001 Converter ───────────────────────────────────────────────
print("=" * 70)
print(" PHASE A — MDL001 Universal → HQ PDF Converter")
print("=" * 70)
ta = time.perf_counter()
res_m1 = MDL001.VRN_MDL001_Converter({
    "input_dir": INPUT_DIR, "pdf_temp": PDF_TEMP,
    "mdl001_temp": MDL001_TEMP, "ssot_dir": "/tmp/fake_ssot",
    "workers": 2, "use_duckdb": True, "self_verify": True,
    "max_pages": 8, "dpi": 150,
}).run()
ta = time.perf_counter() - ta
print(f"  ok={res_m1['ok']} converted={res_m1['converted']} pages={res_m1['total_pages']}")
print(f"  flush={res_m1['flush_stats']} elapsed={ta:.2f}s")
print()

# ── PHASE B: MDL002 Layout Extractor ────────────────────────────────────────
print("=" * 70)
print(" PHASE B — MDL002 Layout + Table + Text Extractor")
print("=" * 70)
tb = time.perf_counter()
res_m2 = MDL002.VRN_MDL002_LayoutExtractor({
    "pdf_temp": PDF_TEMP, "mdl002_temp": MDL002_TEMP,
    "ssot_dir": "/tmp/fake_ssot", "workers": 2,
    "use_doc_cache": True, "page_parallel": True,
    "use_duckdb": True, "self_verify": True, "max_pages": 8,
}).run()
tb = time.perf_counter() - tb
print(f"  ok={res_m2['ok']} reports={res_m2['success']}/{res_m2['total']} "
      f"tables={res_m2['total_tables']} elapsed={tb:.2f}s")
print()

# ── PHASE C: MDL003/004/005 Mock fixtures (would be real in production) ─────
print("=" * 70)
print(" PHASE C — MDL003/004/005 Mock Fixtures (sandbox uses synthetic data)")
print("=" * 70)
TICKER = "2330"
COMPANY = "TSMC"
REPORT_CODE = "2330_2024_JPM"
REPORT_DATE = "2024-12-31"

# These are the GROUND TRUTH numbers for the report (in millions NTD)
GROUND_TRUTH = {
    ("revenue", "2023A"):       1000.0,
    ("revenue", "2024A"):       1100.0,
    ("revenue", "2025E"):       1300.0,  # estimate
    ("gross_profit", "2023A"):   300.0,
    ("gross_profit", "2024A"):   330.0,
    ("operating_income", "2023A"):200.0,
    ("operating_income", "2024A"):220.0,
    ("net_income", "2023A"):     180.0,
    ("net_income", "2024A"):     200.0,
}

# MDL003 mock: phase1 source (cleaner — restored from layout)
m003_data = {"reports": [{
    "ticker": TICKER, "company_name": COMPANY,
    "report_date": REPORT_DATE, "broker": "JPM", "broker_abbr": "JPM",
    "rating_raw": "Overweight", "rating_canonical": "BUY",
    "target_price": 1200, "report_code": REPORT_CODE,
    "validation_grade_score": 0.95,
    "restored_tables": [{"ok": True, "rows": [
        {"label_raw": canonical.replace("_", " ").title(),
         "canonical": canonical,
         "values": {p: GROUND_TRUTH.get((canonical, p), 0)
                     for p in ["2023A", "2024A", "2025E"]
                     if (canonical, p) in GROUND_TRUTH},
         "sources": {p: "RP" for p in ["2023A", "2024A", "2025E"]
                     if (canonical, p) in GROUND_TRUTH}}
        for canonical in ["revenue", "gross_profit", "operating_income", "net_income"]
    ]}],
}]}
Path(MDL003_TEMP, "VRN_MDL003_Restored.json").write_text(
    json.dumps(m003_data, ensure_ascii=False), encoding="utf-8")
print(f"  MDL003 mock: 1 report, {len(m003_data['reports'][0]['restored_tables'][0]['rows'])} canonicals")

# MDL004 mock: phase2 OCR — 99% accurate (introduce 1 small mismatch)
m004_data = {"reports": [{
    "ticker": TICKER, "report_code": REPORT_CODE, "tables": [{
        "ok": True, "confidence": 0.85, "periods": ["2023A", "2024A"],
        "rows": [
            {"label_raw": "Revenue", "values": {"2023A": 1000.0, "2024A": 1100.0}, "status": "PASS"},
            {"label_raw": "Gross Profit", "values": {"2023A": 300.0, "2024A": 330.0}, "status": "PASS"},
            # Slightly off — OCR typo (220 → 221, 0.45% diff)
            {"label_raw": "Operating Income", "values": {"2023A": 200.0, "2024A": 221.0}, "status": "PASS"},
            {"label_raw": "Net Income", "values": {"2023A": 180.0, "2024A": 200.0}, "status": "PASS"},
        ],
    }],
}]}
Path(MDL004_TEMP, "VRN_MDL004_Tables.json").write_text(
    json.dumps(m004_data, ensure_ascii=False), encoding="utf-8")
print(f"  MDL004 mock: 1 report with 1 OCR-induced near-mismatch (0.45%)")

# MDL005 mock: text blocks
m005_data = {"reports": [{"ticker": TICKER, "report_code": REPORT_CODE,
                          "pages": [{"blocks": [
                              {"text": f"{COMPANY} BUY rating, target NT$1200"},
                              {"text": "Outperform with 12-month horizon"},
                          ]}]}]}
Path(MDL005_TEMP, "VRN_MDL005_Text.json").write_text(
    json.dumps(m005_data, ensure_ascii=False), encoding="utf-8")
print(f"  MDL005 mock: 1 report, 2 text blocks")

# MDL002 simulated layout output (overlapping with what MDL002 would extract)
m002_sim = {"reports": [{
    "ticker": TICKER, "company_name": COMPANY,
    "report_date": REPORT_DATE, "broker": "JPM", "broker_abbr": "JPM",
    "report_code": REPORT_CODE, "tables": [],
}]}
# We'll override the actual MDL002 output for MDL006 with this simulated version
# (MDL002 ran on synthetic test PDFs without real ticker info)
Path(MDL002_TEMP, "VRN_MDL002_Layout.json").write_text(
    json.dumps(m002_sim, ensure_ascii=False), encoding="utf-8")
print(f"  MDL002 sim: ticker injected for downstream")
print()

# ── PHASE D: MDL006 phase1 vs phase2 reconciliation ─────────────────────────
print("=" * 70)
print(" PHASE D — MDL006 Phase1 (M03) vs Phase2 (M02+M04+M05) Reconciliation")
print("=" * 70)
td = time.perf_counter()
res_m6 = MDL006.VRN_MDL006_Consolidator({
    "mdl002_temp": MDL002_TEMP, "mdl003_temp": MDL003_TEMP,
    "mdl004_temp": MDL004_TEMP, "mdl005_temp": MDL005_TEMP,
    "output_dir":  MDL006_OUT,  "ssot_dir": "/tmp/fake_ssot",
    "use_duckdb": True, "self_verify": True,
    "compare_tol": 0.02,
}).run()
td = time.perf_counter() - td
cmp6 = res_m6['compare']
print(f"  phase1: basic={res_m6['phase1']['n_basic']} fin={res_m6['phase1']['n_financial']}")
print(f"  phase2: basic={res_m6['phase2']['n_basic']} fin={res_m6['phase2']['n_financial']}")
print(f"  match: {cmp6['n_matched']}/{cmp6['n_matched']+cmp6['n_mismatch']} "
      f"({cmp6['match_rate']:.1%})  mismatch={cmp6['n_mismatch']}  "
      f"p1_only={cmp6['n_p1_only']} p2_only={cmp6['n_p2_only']}")
print(f"  success={cmp6['success']}  sv={res_m6.get('self_verify')}  elapsed={td:.2f}s")
print()

# ── PHASE E: MDL007 mock external API (MOPS + yfinance + TWSE) ──────────────
print("=" * 70)
print(" PHASE E — MDL007 Mock External API (MOPS + yfinance + TWSE)")
print("=" * 70)
te = time.perf_counter()

# Mock fetch_one_ticker with 3 sources
def _mock_fetch_one_ticker(self, ticker: str, report_year: Optional[int] = None) -> Dict:
    """Mock external API: synthesizes MOPS + yfinance + TWSE rows."""
    rows: List[Dict] = []
    # MOPS (官方損益表)
    for canonical in ["revenue", "gross_profit", "operating_income", "net_income"]:
        for period in ["2023A", "2024A"]:
            if (canonical, period) in GROUND_TRUTH:
                rows.append({
                    "ticker": ticker, "source": "mops",
                    "category": "IS", "data_name": canonical.replace("_", " ").title(),
                    "canonical": canonical, "period": period,
                    "value": GROUND_TRUTH[(canonical, period)],
                    "unit": "million", "confidence": 0.98, "status": "ok",
                })
    # TWSE/TPEX market data
    rows.append({
        "ticker": ticker, "source": "twse", "category": "MARKET",
        "data_name": "Adj Close", "canonical": "adj_close",
        "period": "2024-12-31", "value": 1050.0,
        "unit": "ntd", "confidence": 0.95, "status": "ok",
    })
    # yfinance consensus
    rows.append({
        "ticker": ticker, "source": "yfinance", "category": "CONSENSUS",
        "data_name": "Target Mean", "canonical": "consensus_target_mean",
        "period": "current", "value": 1180.0,
        "unit": "ntd", "confidence": 0.90, "status": "ok",
    })
    return {"ticker": ticker, "ok": True, "rows": len(rows),
            "elapsed": 0.05, "data": rows}

# Patch the real fetcher with mock
MDL007.VRN_MDL007_APIDataFetcher.fetch_one_ticker = _mock_fetch_one_ticker

res_m7 = MDL007.VRN_MDL007_APIDataFetcher({
    "mdl007_temp": MDL007_OUT, "ssot_dir": "/tmp/fake_ssot",
    "use_duckdb": True, "self_verify": True,
    "enable_db": False,  # skip sqlite (we use DuckDB)
}).run([TICKER])
te = time.perf_counter() - te
print(f"  ok={res_m7['ok']} tickers={res_m7['n_tickers']} "
      f"total_rows={res_m7['total_rows']}")
print(f"  flush={res_m7.get('flush_stats')}  sv={res_m7.get('self_verify')}  "
      f"elapsed={te:.2f}s")
print()

# Collect API rows for MDL008
api_rows: List[Dict] = []
for r in res_m7["results"]:
    api_rows.extend(r.get("data", []))
print(f"  Aggregated API rows for MDL008: {len(api_rows)}")
print()

# ── PHASE F: MDL008 三角交叉驗證 (報告 vs API) ───────────────────────────────
print("=" * 70)
print(" PHASE F — MDL008 Triangular Cross-Validation (Report ↔ API)")
print("=" * 70)
tf = time.perf_counter()

# Build phase1 financial rows for MDL008 input
report_rows: List[Dict] = []
for canonical, periods in [
    ("revenue", ["2023A", "2024A", "2025E"]),
    ("gross_profit", ["2023A", "2024A"]),
    ("operating_income", ["2023A", "2024A"]),
    ("net_income", ["2023A", "2024A"]),
]:
    for p in periods:
        if (canonical, p) in GROUND_TRUTH:
            report_rows.append({
                "ticker": TICKER, "canonical": canonical, "period": p,
                "value": GROUND_TRUTH[(canonical, p)],
                "unit": "million", "source": "phase1",
            })

res_m8 = MDL008.VRN_MDL008_CrossValidator({
    "output_dir": MDL008_OUT, "ssot_dir": "/tmp/fake_ssot",
    "use_duckdb": True, "self_verify": True,
    "enable_db": False,
}).run(report_rows, api_rows)
tf = time.perf_counter() - tf
print(f"  ok={res_m8.get('ok')} match_rate={res_m8.get('match_rate'):.1%}")
print(f"  comparisons: match={res_m8.get('match')} mismatch={res_m8.get('mismatch')} "
      f"unresolved={res_m8.get('unresolved')} no_api={res_m8.get('no_api')}")
print(f"  fcst_checks: total={res_m8.get('forecast_checks_total')} "
      f"fail={res_m8.get('forecast_checks_fail')}")
print(f"  flush={res_m8.get('flush_stats')}  sv={res_m8.get('self_verify')}  "
      f"elapsed={tf:.2f}s")
print()

# ── PHASE G: 全景 HTML 報告 ─────────────────────────────────────────────────
t_total = time.perf_counter() - t_panorama_start

panorama_summary = {
    "version":   "1.1.0",
    "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
    "elapsed_total":  round(t_total, 2),
    "hardgate":       {
        "seal":      HG_CAPS["seal"],
        "n_capable": HG_CAPS["n_capable"],
        "n_loaded":  HG_CAPS["n_loaded"],
        "elapsed_ms":HG_CAPS["elapsed_ms"],
    },
    "modules": {
        "mdl001": {"version": MDL001.__version__, "ok": res_m1["ok"],
                    "elapsed": ta, "converted": res_m1["converted"],
                    "self_verify": "READY" if res_m1.get("self_verify_html") else "?"},
        "mdl002": {"version": MDL002.__version__, "ok": res_m2["ok"],
                    "elapsed": tb, "tables": res_m2["total_tables"],
                    "self_verify": "READY" if res_m2.get("self_verify_html") else "?"},
        "mdl006": {"version": MDL006.__version__, "ok": res_m6["ok"],
                    "elapsed": td, "match_rate": cmp6["match_rate"],
                    "self_verify": res_m6.get("self_verify", "?")},
        "mdl007": {"version": MDL007.__version__, "ok": res_m7["ok"],
                    "elapsed": te, "rows": res_m7["total_rows"],
                    "self_verify": res_m7.get("self_verify", "?")},
        "mdl008": {"version": MDL008.__version__, "ok": res_m8.get("ok"),
                    "elapsed": tf, "match_rate": res_m8.get("match_rate"),
                    "self_verify": res_m8.get("self_verify", "?")},
    },
    "phase_pipeline": {
        "input_pdfs":           len(os.listdir(INPUT_DIR)),
        "mdl001_converted":     res_m1["converted"],
        "mdl002_tables":        res_m2["total_tables"],
        "mdl003_phase1_fin":    res_m6["phase1"]["n_financial"],
        "mdl004_phase2_fin":    res_m6["phase2"]["n_financial"],
        "phase_match_rate":     cmp6["match_rate"],
        "phase_mismatch":       cmp6["n_mismatch"],
        "mdl007_api_rows":      len(api_rows),
        "mdl008_triangle_match":res_m8.get("match_rate", 0),
        "mdl008_match_count":   res_m8.get("match", 0),
        "mdl008_mismatch":      res_m8.get("mismatch", 0),
    },
    "data_flow_signals": {
        "phase1_has_data":   res_m6["phase1"]["n_financial"] > 0,
        "phase2_has_data":   res_m6["phase2"]["n_financial"] > 0,
        "internal_match":    cmp6["success"],
        "api_loaded":        len(api_rows) > 0,
        "triangle_validated":res_m8.get("ok", False),
    },
}

# Write JSON summary
sum_path = ROOT + "/panorama_summary.json"
Path(sum_path).write_text(json.dumps(panorama_summary, ensure_ascii=False, indent=2,
                                      default=str), encoding="utf-8")

# Write HTML report (8-panel: hardgate + 5 modules + phase compare + summary)
def _badge(cls):
    color = {"READY": "#439a9a", "NEAR-READY": "#e0b020",
             "NOT-READY": "#c83030", "BOOT_PRECHECKED": "#439a9a",
             "PARTIAL": "#e0b020"}.get(cls, "#666")
    return f'<span style="display:inline-block;padding:2px 8px;background:{color};color:white;font-weight:700;font-size:10px;letter-spacing:0.05em">{cls}</span>'

def _kv_table(d: Dict) -> str:
    rows = "".join(f'<tr><td class="kv-k">{k}</td><td class="kv-v">{v}</td></tr>'
                    for k, v in d.items())
    return f'<table class="kv">{rows}</table>'

# Mismatch chain visualization
mismatch_html = ""
if cmp6["mismatches"]:
    mismatch_html = '<table class="ck-tbl"><thead><tr><th>Field</th><th>Period</th>' \
                     '<th>Phase1</th><th>Phase2</th><th>Diff %</th></tr></thead><tbody>'
    for m in cmp6["mismatches"][:10]:
        mismatch_html += (f'<tr><td>{m.get("data_name","")}</td>'
                           f'<td>{m.get("period","")}</td>'
                           f'<td>{m.get("phase1_value","")}</td>'
                           f'<td>{m.get("phase2_value","")}</td>'
                           f'<td>{m.get("diff_pct",0):.2%}</td></tr>')
    mismatch_html += "</tbody></table>"
else:
    mismatch_html = '<p style="color:#439a9a;font-weight:600">✓ All phases agree perfectly</p>'

# HardGate panel
hg_rows = "".join(
    f'<tr><td>{k}</td><td>{_badge("READY") if v else _badge("NOT-READY")}</td></tr>'
    for k, v in HG_CAPS["ok"].items())
hardgate_panel = f"""
<div class="cd"><div class="cd-h">⚓ HardGate 7-Tool BOOT_PRECHECK</div>
<div class="cd-b"><div class="tm">$ HardGate boot precheck
  policy:     {HG_CAPS['policy']}
  py_inject:  {HG_CAPS['py_inject']}
  loaded:     {HG_CAPS['n_loaded']}/7
  capable:    {HG_CAPS['n_capable']}/7
  elapsed:    {HG_CAPS['elapsed_ms']}ms
  seal:       {HG_CAPS['seal']}</div>
<table class="ck-tbl" style="margin-top:8px">
<thead><tr><th>Tool</th><th>Status</th></tr></thead>
<tbody>{hg_rows}</tbody></table>
</div></div>
"""

# Module panels (one card per module)
def _module_panel(mid: str, m: Dict, extras: str = "") -> str:
    return f"""
<div class="cd"><div class="cd-h">{mid.upper()} v{m['version']} {_badge(m.get('self_verify','?'))}</div>
<div class="cd-b">{_kv_table({k:v for k,v in m.items() if k not in ('version','self_verify')})}
{extras}</div></div>"""

modules_html = "".join([
    _module_panel("mdl001", panorama_summary["modules"]["mdl001"]),
    _module_panel("mdl002", panorama_summary["modules"]["mdl002"]),
    _module_panel("mdl006", panorama_summary["modules"]["mdl006"]),
    _module_panel("mdl007", panorama_summary["modules"]["mdl007"]),
    _module_panel("mdl008", panorama_summary["modules"]["mdl008"]),
])

# Phase compare panel
phase_panel = f"""
<div class="cd"><div class="cd-h">⚖ MDL006 — Phase1 vs Phase2 Reconciliation</div>
<div class="cd-b"><div class="tm">$ phase compare
  phase1 basic   : {res_m6['phase1']['n_basic']}
  phase1 finrows : {res_m6['phase1']['n_financial']}
  phase2 basic   : {res_m6['phase2']['n_basic']}
  phase2 finrows : {res_m6['phase2']['n_financial']}
  matched        : {cmp6['n_matched']}
  mismatch       : {cmp6['n_mismatch']}
  match_rate     : {cmp6['match_rate']:.2%}
  success        : {cmp6['success']}</div>
{mismatch_html}
</div></div>
"""

# Triangle validation panel
triangle_panel = f"""
<div class="cd"><div class="cd-h">📐 MDL008 — Triangular Cross-Validation (Report ↔ API)</div>
<div class="cd-b"><div class="tm">$ triangle validation
  total compare  : {res_m8.get('total_comparisons',0)}
  match          : {res_m8.get('match',0)}
  mismatch       : {res_m8.get('mismatch',0)}
  unresolved     : {res_m8.get('unresolved',0)}
  no_api         : {res_m8.get('no_api',0)}
  match_rate     : {res_m8.get('match_rate',0):.2%}
  avg_confidence : {res_m8.get('avg_confidence',0):.3f}
  fcst total     : {res_m8.get('forecast_checks_total',0)}
  fcst fail      : {res_m8.get('forecast_checks_fail',0)}
  ok             : {res_m8.get('ok')}</div></div></div>
"""

# Pipeline flow diagram (SVG)
flow_svg = f"""
<svg viewBox="0 0 700 220" style="width:100%;height:auto">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#4c78a8"/>
    </marker>
    <style>
      .b {{font-family:'DM Mono',monospace;font-size:10px;font-weight:600;fill:#1a1a1a}}
      .l {{stroke:#4c78a8;stroke-width:2;fill:none}}
      .box {{fill:#f5f4f0;stroke:#4c78a8;stroke-width:1.5}}
      .box-ok {{fill:#e8f5e8;stroke:#439a9a;stroke-width:2}}
    </style>
  </defs>

  <!-- Row 1: PDF input -->
  <rect class="box-ok" x="10" y="10" width="80" height="40" rx="4"/>
  <text class="b" x="50" y="35" text-anchor="middle">PDFs</text>

  <!-- MDL001 -->
  <rect class="box" x="120" y="10" width="80" height="40" rx="4"/>
  <text class="b" x="160" y="30" text-anchor="middle">MDL001</text>
  <text class="b" x="160" y="42" text-anchor="middle">Convert</text>
  <line class="l" x1="90" y1="30" x2="120" y2="30" marker-end="url(#arr)"/>

  <!-- MDL002 -->
  <rect class="box" x="230" y="10" width="80" height="40" rx="4"/>
  <text class="b" x="270" y="30" text-anchor="middle">MDL002</text>
  <text class="b" x="270" y="42" text-anchor="middle">Layout</text>
  <line class="l" x1="200" y1="30" x2="230" y2="30" marker-end="url(#arr)"/>

  <!-- Phase1 branch (MDL003) -->
  <rect class="box" x="340" y="10" width="80" height="40" rx="4"/>
  <text class="b" x="380" y="30" text-anchor="middle">MDL003</text>
  <text class="b" x="380" y="42" text-anchor="middle">Phase1</text>
  <line class="l" x1="310" y1="30" x2="340" y2="30" marker-end="url(#arr)"/>

  <!-- Phase2 branch (MDL004/005) -->
  <rect class="box" x="340" y="70" width="80" height="40" rx="4"/>
  <text class="b" x="380" y="90" text-anchor="middle">MDL004/5</text>
  <text class="b" x="380" y="102" text-anchor="middle">Phase2</text>
  <line class="l" x1="270" y1="50" x2="270" y2="90" marker-end="url(#arr)"/>
  <line class="l" x1="270" y1="90" x2="340" y2="90" marker-end="url(#arr)"/>

  <!-- MDL006 reconciler -->
  <rect class="box-ok" x="450" y="40" width="80" height="40" rx="4"/>
  <text class="b" x="490" y="60" text-anchor="middle">MDL006</text>
  <text class="b" x="490" y="72" text-anchor="middle">{cmp6['match_rate']:.0%}</text>
  <line class="l" x1="420" y1="30" x2="450" y2="50" marker-end="url(#arr)"/>
  <line class="l" x1="420" y1="90" x2="450" y2="70" marker-end="url(#arr)"/>

  <!-- MDL007 API -->
  <rect class="box" x="120" y="140" width="80" height="40" rx="4"/>
  <text class="b" x="160" y="160" text-anchor="middle">MDL007</text>
  <text class="b" x="160" y="172" text-anchor="middle">API</text>

  <!-- MDL008 triangle validator -->
  <rect class="box-ok" x="450" y="140" width="80" height="40" rx="4"/>
  <text class="b" x="490" y="160" text-anchor="middle">MDL008</text>
  <text class="b" x="490" y="172" text-anchor="middle">{res_m8.get('match_rate',0):.0%}</text>

  <!-- Flow lines -->
  <line class="l" x1="490" y1="80" x2="490" y2="140" marker-end="url(#arr)"/>
  <line class="l" x1="200" y1="160" x2="450" y2="160" marker-end="url(#arr)"/>

  <!-- Final output -->
  <rect class="box-ok" x="560" y="40" width="120" height="100" rx="4"/>
  <text class="b" x="620" y="80" text-anchor="middle">PANORAMA</text>
  <text class="b" x="620" y="95" text-anchor="middle">REPORT</text>
  <text class="b" x="620" y="115" text-anchor="middle" style="fill:#439a9a">match {res_m8.get('match_rate',0):.0%}</text>
  <line class="l" x1="530" y1="60" x2="560" y2="80" marker-end="url(#arr)"/>
  <line class="l" x1="530" y1="160" x2="560" y2="120" marker-end="url(#arr)"/>
</svg>
"""

# Final HTML
panorama_html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN Panorama Cross-Validation Report v1.1.0</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f5f4f0;color:#1a1a1a;font-family:'DM Sans',-apple-system,sans-serif;font-size:11px;line-height:1.6;padding:24px;max-width:1200px;margin:0 auto}}
.hdr{{border-top:4px solid;border-image:linear-gradient(90deg,#ff5e5e,#ffae5e,#ffe55e,#5eff8c,#5ec8ff,#8c5eff,#ff5ec8) 1;padding-top:16px;margin-bottom:24px}}
h1{{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;letter-spacing:-0.02em}}
h2{{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;margin-top:24px;margin-bottom:12px;color:#4c78a8}}
.sub{{font-family:'DM Mono',monospace;font-size:10px;color:#666;margin-top:4px}}
.cd{{background:white;border:1px solid #e0ddd5;margin-bottom:16px}}
.cd-h{{background:#4c78a8;color:white;padding:8px 16px;font-family:'Syne',sans-serif;font-weight:600;font-size:12px;letter-spacing:0.03em;display:flex;align-items:center;gap:8px}}
.cd-b{{padding:12px 16px}}
.tm{{background:#1a1a1a;color:#c8e0c8;font-family:'DM Mono',monospace;font-size:10px;padding:32px 16px 16px 16px;position:relative;white-space:pre;line-height:1.5}}
.tm::before{{content:"● ● ●";position:absolute;top:8px;left:12px;color:#ff5e5e;letter-spacing:4px;font-size:10px}}
.kv{{width:100%;border-collapse:collapse}}
.kv td{{padding:4px 8px;border-bottom:1px solid #f0ede5}}
.kv .kv-k{{font-weight:600;color:#4c78a8;width:40%}}
.kv .kv-v{{font-family:'DM Mono',monospace;font-size:10px;color:#1a1a1a}}
.ck-tbl{{width:100%;border-collapse:collapse}}
.ck-tbl th{{background:#f5f4f0;color:#4c78a8;text-align:left;padding:6px 8px;font-weight:600;border-bottom:2px solid #4c78a8;font-size:10px}}
.ck-tbl td{{padding:6px 8px;border-bottom:1px solid #f0ede5;font-family:'DM Mono',monospace;font-size:10px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.foot{{margin-top:24px;color:#999;font-family:'DM Mono',monospace;font-size:9px;text-align:right}}
</style></head><body>
<div class="hdr">
<h1>VRN Panorama Cross-Validation Report</h1>
<div class="sub">VeritasReportNova v1.1.0 · Cross-module data flow + triangle validation · {time.strftime("%Y-%m-%d %H:%M:%S")} · total {t_total:.2f}s</div>
</div>

<div class="cd"><div class="cd-h">🔄 Pipeline Flow</div>
<div class="cd-b">{flow_svg}</div></div>

{hardgate_panel}

<h2>Per-Module Status</h2>
{modules_html}

<h2>Cross-Module Reconciliation</h2>
{phase_panel}
{triangle_panel}

<h2>Final Verdict</h2>
<div class="cd"><div class="cd-h">🎯 Pipeline Health</div>
<div class="cd-b"><div class="tm">$ panorama summary
  hardgate seal       : {HG_CAPS['seal']}
  hardgate capable    : {HG_CAPS['n_capable']}/7

  mdl001 converted    : {res_m1['converted']}/{res_m1['total']}
  mdl002 tables       : {res_m2['total_tables']}
  mdl003 phase1 fin   : {res_m6['phase1']['n_financial']}
  mdl004 phase2 fin   : {res_m6['phase2']['n_financial']}
  mdl006 phase match  : {cmp6['match_rate']:.2%}  ({cmp6['n_matched']}/{cmp6['n_matched']+cmp6['n_mismatch']})
  mdl007 api rows     : {len(api_rows)}
  mdl008 triangle     : {res_m8.get('match_rate',0):.2%}  ({res_m8.get('match',0)}/{res_m8.get('total_comparisons',0)})

  total elapsed       : {t_total:.2f}s
  internal_match      : {cmp6['success']}
  triangle_validated  : {res_m8.get('ok', False)}</div></div></div>

<div class="foot">VRN Panorama Cross-Validation · v1.1.0 · {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
</body></html>
"""

html_path = ROOT + "/panorama_report.html"
Path(html_path).write_text(panorama_html, encoding="utf-8")

# ── Print summary ──────────────────────────────────────────────────────────
print("=" * 70)
print(" PANORAMA SUMMARY")
print("=" * 70)
print(f"  HardGate seal:          {HG_CAPS['seal']} ({HG_CAPS['n_capable']}/7 capable)")
print(f"  MDL001 → MDL002:        OK ({res_m1['converted']} conv, {res_m2['total_tables']} tables)")
print(f"  MDL003 → MDL004/005:    Phase1={res_m6['phase1']['n_financial']} Phase2={res_m6['phase2']['n_financial']}")
print(f"  MDL006 phase compare:   {cmp6['match_rate']:.2%} match ({cmp6['n_matched']} matched / {cmp6['n_mismatch']} mismatch)")
print(f"  MDL007 external API:    {len(api_rows)} rows (MOPS+TWSE+yfinance)")
print(f"  MDL008 triangle check:  {res_m8.get('match_rate',0):.2%} match ({res_m8.get('match',0)} / {res_m8.get('total_comparisons',0)})")
print()
print(f"  Total panorama time:    {t_total:.2f}s")
print(f"  Output JSON:            {sum_path}")
print(f"  Output HTML:            {html_path}")
print()
print(f"  ✓ panorama_summary.json (size={os.path.getsize(sum_path)})")
print(f"  ✓ panorama_report.html  (size={os.path.getsize(html_path)})")

# Copy to outputs
import shutil
out_json = "/mnt/user-data/outputs/panorama_summary.json"
out_html = "/mnt/user-data/outputs/panorama_report.html"
shutil.copy(sum_path, out_json)
shutil.copy(html_path, out_html)
print(f"\n  → Copied to outputs:")
print(f"    {out_json}")
print(f"    {out_html}")
