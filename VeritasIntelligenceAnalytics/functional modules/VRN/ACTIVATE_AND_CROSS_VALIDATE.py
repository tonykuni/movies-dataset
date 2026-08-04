# -*- coding: utf-8 -*-
r"""
ACTIVATE_AND_CROSS_VALIDATE.py
==============================
ACTIVATE the system + run TWO independent sets with DIFFERENT inputs +
cross-validate (1) invariants stable across sets, (2) expected differences
correctly detected.

SET A — Clean baseline:
  No OCR noise. All values match ground truth.

SET B — Realistic noisy:
  1 OCR typo (220 → 221, 0.45% drift, within 2% tolerance)
  1 missing field (net_income absent from MDL004 phase2 OCR output)

CROSS-VALIDATION asserts:
  ─── INVARIANTS (Set A == Set B) ───
    HardGate seal stable across runs
    MDL003 phase1 source stable (ground truth)
    MDL007 official API rows stable (MOPS+TWSE+yfinance)
    MDL008 triangle validation stable (both reports use ground truth)

  ─── EXPECTED DIFFERENCES (Set A != Set B) ───
    Set B phase2 row count < Set A phase2 row count (missing field detected)
    Set B p1_only count > Set A p1_only count (orphan phase1 rows surface)
    Set A is fully deterministic on first run

Pipeline per set:
  HardGate 7-tool BOOT_PRECHECK
    → MDL001 → MDL002 → mock(M3/4/5) → MDL006 → MDL007 → MDL008

USAGE:
  py -3.12 ACTIVATE_AND_CROSS_VALIDATE.py
  py -3.12 ACTIVATE_AND_CROSS_VALIDATE.py --output-dir D:\my_runs
"""
from __future__ import annotations
import os, sys, json, time, shutil, tempfile, argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Resolve script dir + sys.path ───────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Suppress library noise
import warnings, logging
warnings.filterwarnings("ignore")
for n in ("pdfminer", "pdfplumber", "fontTools", "fitz", "yfinance"):
    logging.getLogger(n).setLevel(logging.ERROR)


def _resolve_ssot_dir() -> str:
    """Find supportive_module folder. Falls back to script dir."""
    candidates = [
        os.path.normpath(os.path.join(SCRIPT_DIR, "..", "supportive_module")),
        os.path.join(SCRIPT_DIR, "supportive_module"),
        SCRIPT_DIR,
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return SCRIPT_DIR

SSOT_DIR = _resolve_ssot_dir()


# ── BOOT: HardGate ──────────────────────────────────────────────────────────
print("=" * 76)
print(" VRN ACTIVATE + DUAL-SET CROSS VALIDATE")
print("=" * 76)
print()

from VIA_HardGate_BootPrecheck import HARDGATE_BOOT, hardgate_caps_summary
HG_CAPS = HARDGATE_BOOT(ssot_dir=SSOT_DIR, quiet=True)
print(f"  HardGate seal:    {HG_CAPS['seal']}")
print(f"  HardGate capable: {HG_CAPS['n_capable']}/7  ({HG_CAPS['elapsed_ms']}ms)")
print(f"  policy:           {HG_CAPS['policy']}")
print(f"  ssot_dir:         {SSOT_DIR}")
print(f"  caps:             {hardgate_caps_summary(HG_CAPS)}")
print()


# ── Load modules ────────────────────────────────────────────────────────────
import VRN_MDL001_Converter                     as MDL001
import VRN_MDL002_LayoutExtractor               as MDL002
import VRN_MDL006_ConsolidatorAndPhaseValidator as MDL006
import VRN_MDL007_APIDataFetcher                as MDL007
import VRN_MDL008_CrossValidator                as MDL008

print(f"  Modules online:")
for n, m in [("MDL001",MDL001),("MDL002",MDL002),
              ("MDL006",MDL006),("MDL007",MDL007),("MDL008",MDL008)]:
    print(f"    {n} v{m.__version__}")
print()


# ── Ground truth (TSMC, used as Phase1 source by MDL003) ────────────────────
TICKER       = "2330"
COMPANY      = "TSMC"
REPORT_CODE  = "2330_2024_JPM"
REPORT_DATE  = "2024-12-31"

GROUND_TRUTH = {
    ("revenue",          "2023A"): 1000.0,
    ("revenue",          "2024A"): 1100.0,
    ("revenue",          "2025E"): 1300.0,
    ("gross_profit",     "2023A"):  300.0,
    ("gross_profit",     "2024A"):  330.0,
    ("operating_income", "2023A"):  200.0,
    ("operating_income", "2024A"):  220.0,
    ("net_income",       "2023A"):  180.0,
    ("net_income",       "2024A"):  200.0,
}


def _ensure_test_pdfs(target_dir: str) -> int:
    """Create or copy test PDFs into target_dir."""
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    candidates = [
        os.path.join(SCRIPT_DIR, "test_pdfs"),
        "/home/claude/work/test_pdfs",
    ]
    src = next((c for c in candidates if os.path.isdir(c)), None)
    if src:
        for f in os.listdir(src):
            if f.endswith(".pdf"):
                shutil.copy(os.path.join(src, f), target_dir)
        return len([f for f in os.listdir(target_dir) if f.endswith(".pdf")])
    # Fallback: minimal valid PDF bytes
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
        b"0000000058 00000 n\n0000000115 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n175\n%%EOF\n"
    )
    for i in range(3):
        Path(target_dir, f"synthetic_report_{i:02d}.pdf").write_bytes(minimal_pdf)
    return 3


def run_set(set_name: str,
            ocr_overrides: Dict[Tuple[str,str], float],
            ocr_missing: List[str]) -> Dict:
    """Run one full pipeline. Returns flattened result summary."""
    print()
    print("█" * 76)
    print(f"  SET {set_name}  (OCR overrides={len(ocr_overrides)}, missing={ocr_missing})")
    print("█" * 76)

    t_start = time.perf_counter()
    root = tempfile.mkdtemp(prefix=f"set_{set_name}_")
    INPUT      = os.path.join(root, "input")
    PDF_TEMP   = os.path.join(root, "pdf_temp")
    M01_TEMP   = os.path.join(root, "mdl001_temp")
    M02_TEMP   = os.path.join(root, "mdl002_temp")
    M03_TEMP   = os.path.join(root, "mdl003_temp")
    M04_TEMP   = os.path.join(root, "mdl004_temp")
    M05_TEMP   = os.path.join(root, "mdl005_temp")
    M06_OUT    = os.path.join(root, "mdl006_out")
    M07_OUT    = os.path.join(root, "mdl007_out")
    M08_OUT    = os.path.join(root, "mdl008_out")
    for d in [INPUT, PDF_TEMP, M01_TEMP, M02_TEMP, M03_TEMP,
              M04_TEMP, M05_TEMP, M06_OUT, M07_OUT, M08_OUT]:
        Path(d).mkdir(parents=True, exist_ok=True)
    n_pdfs = _ensure_test_pdfs(INPUT)

    # PHASE A: MDL001
    ta = time.perf_counter()
    res_m1 = MDL001.VRN_MDL001_Converter({
        "input_dir": INPUT, "pdf_temp": PDF_TEMP,
        "mdl001_temp": M01_TEMP, "ssot_dir": SSOT_DIR,
        "workers": 2, "use_duckdb": True, "self_verify": True,
        "max_pages": 8, "dpi": 150,
    }).run()
    ta = time.perf_counter() - ta
    print(f"  [A] MDL001  conv={res_m1['converted']}/{res_m1['total']}  {ta:.2f}s")

    # PHASE B: MDL002
    tb = time.perf_counter()
    res_m2 = MDL002.VRN_MDL002_LayoutExtractor({
        "pdf_temp": PDF_TEMP, "mdl002_temp": M02_TEMP,
        "ssot_dir": SSOT_DIR, "workers": 2,
        "use_doc_cache": True, "page_parallel": True,
        "use_duckdb": True, "self_verify": True, "max_pages": 8,
    }).run()
    tb = time.perf_counter() - tb
    print(f"  [B] MDL002  reports={res_m2['success']}/{res_m2['total']}  "
          f"tables={res_m2['total_tables']}  {tb:.2f}s")

    # PHASE C: Mock fixtures
    # MDL003 Phase1 — clean ground truth (INVARIANT across both sets)
    m003_data = {"reports": [{
        "ticker": TICKER, "company_name": COMPANY,
        "report_date": REPORT_DATE, "broker": "JPM", "broker_abbr": "JPM",
        "rating_raw": "Overweight", "rating_canonical": "BUY",
        "target_price": 1200, "report_code": REPORT_CODE,
        "validation_grade_score": 0.95,
        "restored_tables": [{"ok": True, "rows": [
            {"label_raw": canonical.replace("_", " ").title(),
             "canonical": canonical,
             "values": {p: GROUND_TRUTH[(canonical, p)]
                          for p in ["2023A","2024A","2025E"]
                          if (canonical, p) in GROUND_TRUTH},
             "sources": {p: "RP" for p in ["2023A","2024A","2025E"]
                          if (canonical, p) in GROUND_TRUTH}}
            for canonical in ["revenue","gross_profit","operating_income","net_income"]
        ]}]}]}
    Path(M03_TEMP, "VRN_MDL003_Restored.json").write_text(
        json.dumps(m003_data, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    # MDL004 Phase2 — varies by set (DIFFERENCE source)
    m004_rows = []
    for canonical in ["revenue","gross_profit","operating_income","net_income"]:
        if canonical in ocr_missing:
            continue  # simulate missing OCR
        vals = {}
        for p in ["2023A","2024A"]:
            if (canonical, p) not in GROUND_TRUTH:
                continue
            v = ocr_overrides.get((canonical, p), GROUND_TRUTH[(canonical, p)])
            vals[p] = v
        m004_rows.append({"label_raw": canonical.replace("_", " ").title(),
                           "values": vals, "status": "PASS"})
    m004_data = {"reports": [{"ticker": TICKER, "report_code": REPORT_CODE,
        "tables": [{"ok": True, "confidence": 0.85,
                     "periods": ["2023A","2024A"], "rows": m004_rows}]}]}
    Path(M04_TEMP, "VRN_MDL004_Tables.json").write_text(
        json.dumps(m004_data, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    m005_data = {"reports": [{"ticker": TICKER, "report_code": REPORT_CODE,
        "pages": [{"blocks": [{"text": f"{COMPANY} BUY rating, target NT$1200"}]}]}]}
    Path(M05_TEMP, "VRN_MDL005_Text.json").write_text(
        json.dumps(m005_data, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    m002_sim = {"reports": [{"ticker": TICKER, "company_name": COMPANY,
        "report_date": REPORT_DATE, "broker": "JPM", "broker_abbr": "JPM",
        "report_code": REPORT_CODE, "tables": []}]}
    Path(M02_TEMP, "VRN_MDL002_Layout.json").write_text(
        json.dumps(m002_sim, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    # PHASE D: MDL006
    td = time.perf_counter()
    res_m6 = MDL006.VRN_MDL006_Consolidator({
        "mdl002_temp": M02_TEMP, "mdl003_temp": M03_TEMP,
        "mdl004_temp": M04_TEMP, "mdl005_temp": M05_TEMP,
        "output_dir":  M06_OUT,  "ssot_dir": SSOT_DIR,
        "use_duckdb": True, "self_verify": True, "compare_tol": 0.02,
    }).run()
    td = time.perf_counter() - td
    cmp6 = res_m6["compare"]
    print(f"  [D] MDL006  phase1.fin={res_m6['phase1']['n_financial']}  "
          f"phase2.fin={res_m6['phase2']['n_financial']}  "
          f"match={cmp6['n_matched']}/{cmp6['n_matched']+cmp6['n_mismatch']}  "
          f"({cmp6['match_rate']:.1%})  p1_only={cmp6['n_p1_only']}  {td:.2f}s")

    # PHASE E: MDL007 mock fetch (INVARIANT — official MOPS doesn't change)
    te = time.perf_counter()

    def _mock_fetch(self, ticker: str, report_year: Optional[int] = None) -> Dict:
        rows = []
        for canonical in ["revenue","gross_profit","operating_income","net_income"]:
            for period in ["2023A","2024A"]:
                if (canonical, period) in GROUND_TRUTH:
                    rows.append({"ticker": ticker, "source": "mops",
                        "category": "IS", "data_name": canonical.replace("_"," ").title(),
                        "canonical": canonical, "period": period,
                        "value": GROUND_TRUTH[(canonical, period)],
                        "unit": "million", "confidence": 0.98, "status": "ok"})
        rows.append({"ticker": ticker, "source": "twse", "category": "MARKET",
            "data_name": "Adj Close", "canonical": "adj_close",
            "period": "2024-12-31", "value": 1050.0,
            "unit": "ntd", "confidence": 0.95, "status": "ok"})
        rows.append({"ticker": ticker, "source": "yfinance", "category": "CONSENSUS",
            "data_name": "Target Mean", "canonical": "consensus_target_mean",
            "period": "current", "value": 1180.0,
            "unit": "ntd", "confidence": 0.90, "status": "ok"})
        return {"ticker": ticker, "ok": True, "rows": len(rows),
                "elapsed": 0.05, "data": rows}

    MDL007.VRN_MDL007_APIDataFetcher.fetch_one_ticker = _mock_fetch

    res_m7 = MDL007.VRN_MDL007_APIDataFetcher({
        "mdl007_temp": M07_OUT, "ssot_dir": SSOT_DIR,
        "use_duckdb": True, "self_verify": True, "enable_db": False,
    }).run([TICKER])
    te = time.perf_counter() - te
    api_rows = []
    for r in res_m7["results"]:
        api_rows.extend(r.get("data", []))
    print(f"  [E] MDL007  api_rows={len(api_rows)}  {te:.2f}s")

    # PHASE F: MDL008 (INVARIANT — both reports use ground truth)
    tf = time.perf_counter()
    report_rows = []
    for canonical in ["revenue","gross_profit","operating_income","net_income"]:
        for p in ["2023A","2024A","2025E"]:
            if (canonical, p) in GROUND_TRUTH:
                report_rows.append({"ticker": TICKER, "canonical": canonical,
                    "period": p, "value": GROUND_TRUTH[(canonical, p)],
                    "unit": "million", "source": "phase1"})

    res_m8 = MDL008.VRN_MDL008_CrossValidator({
        "output_dir": M08_OUT, "ssot_dir": SSOT_DIR,
        "use_duckdb": True, "self_verify": True, "enable_db": False,
    }).run(report_rows, api_rows)
    tf = time.perf_counter() - tf
    print(f"  [F] MDL008  match={res_m8.get('match',0)}/{res_m8.get('total_comparisons',0)}  "
          f"({res_m8.get('match_rate',0):.1%})  conf={res_m8.get('avg_confidence',0):.3f}  {tf:.2f}s")

    # Cleanup
    shutil.rmtree(root, ignore_errors=True)

    elapsed = round(time.perf_counter() - t_start, 2)
    print(f"  → SET {set_name} elapsed: {elapsed}s")

    return {
        "set":             set_name,
        "elapsed":         elapsed,
        "hardgate_seal":   HG_CAPS["seal"],
        "hardgate_caps":   HG_CAPS["n_capable"],
        "mdl001_conv":     res_m1["converted"],
        "mdl002_tables":   res_m2["total_tables"],
        "phase1_fin":      res_m6["phase1"]["n_financial"],
        "phase2_fin":      res_m6["phase2"]["n_financial"],
        "phase_match":     cmp6["n_matched"],
        "phase_mismatch":  cmp6["n_mismatch"],
        "phase_p1_only":   cmp6["n_p1_only"],
        "phase_p2_only":   cmp6["n_p2_only"],
        "phase_match_rate":cmp6["match_rate"],
        "phase_success":   cmp6["success"],
        "api_rows":        len(api_rows),
        "triangle_match":  res_m8.get("match", 0),
        "triangle_total":  res_m8.get("total_comparisons", 0),
        "triangle_match_rate": res_m8.get("match_rate", 0),
        "triangle_avg_conf":   res_m8.get("avg_confidence", 0),
        "triangle_ok":         res_m8.get("ok", False),
        "self_verify": {
            "mdl001": "READY" if res_m1.get("self_verify_html") else "?",
            "mdl002": "READY" if res_m2.get("self_verify_html") else "?",
            "mdl006": res_m6.get("self_verify", "?"),
            "mdl007": res_m7.get("self_verify", "?"),
            "mdl008": res_m8.get("self_verify", "?"),
        },
    }


# ── ARGS ────────────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("--output-dir", default=os.path.join(SCRIPT_DIR, "_runs"))
args = ap.parse_args()
Path(args.output_dir).mkdir(parents=True, exist_ok=True)


# ── RUN BOTH SETS ───────────────────────────────────────────────────────────
result_A = run_set(
    "A",
    ocr_overrides={},     # clean — no OCR overrides
    ocr_missing=[],       # no missing fields
)
result_B = run_set(
    "B",
    ocr_overrides={("operating_income","2024A"): 221.0},  # 0.45% drift, in 2% tol
    ocr_missing=["net_income"],                            # entirely missing
)


# ── CROSS VALIDATION ────────────────────────────────────────────────────────
print()
print("=" * 76)
print(" CROSS VALIDATION — Set A vs Set B")
print("=" * 76)

CV_PASS = 0; CV_FAIL = 0
CV_DETAILS: List[Tuple[str, str, bool, Any, Any]] = []

def cv(category: str, name: str, ok: bool, va: Any = "", vb: Any = ""):
    global CV_PASS, CV_FAIL
    if ok: CV_PASS += 1
    else:  CV_FAIL += 1
    CV_DETAILS.append((category, name, ok, va, vb))


# ─── INVARIANTS (Set A == Set B) ───
cv("INVARIANT", "HardGate seal stable",
    result_A["hardgate_seal"] == result_B["hardgate_seal"],
    result_A["hardgate_seal"], result_B["hardgate_seal"])

cv("INVARIANT", "HardGate capable count stable",
    result_A["hardgate_caps"] == result_B["hardgate_caps"],
    result_A["hardgate_caps"], result_B["hardgate_caps"])

cv("INVARIANT", "MDL001 conversion deterministic",
    result_A["mdl001_conv"] == result_B["mdl001_conv"],
    result_A["mdl001_conv"], result_B["mdl001_conv"])

cv("INVARIANT", "MDL002 layout extraction stable",
    result_A["mdl002_tables"] == result_B["mdl002_tables"],
    result_A["mdl002_tables"], result_B["mdl002_tables"])

cv("INVARIANT", "MDL003 phase1 source identical",
    result_A["phase1_fin"] == result_B["phase1_fin"],
    result_A["phase1_fin"], result_B["phase1_fin"])

cv("INVARIANT", "MDL007 official API rows identical",
    result_A["api_rows"] == result_B["api_rows"],
    result_A["api_rows"], result_B["api_rows"])

cv("INVARIANT", "MDL008 triangle match identical",
    result_A["triangle_match"] == result_B["triangle_match"],
    result_A["triangle_match"], result_B["triangle_match"])

cv("INVARIANT", "MDL008 triangle match_rate identical",
    abs(result_A["triangle_match_rate"] - result_B["triangle_match_rate"]) < 0.001,
    f"{result_A['triangle_match_rate']:.2%}",
    f"{result_B['triangle_match_rate']:.2%}")

cv("INVARIANT", "MDL008 avg_confidence stable",
    abs(result_A["triangle_avg_conf"] - result_B["triangle_avg_conf"]) < 0.001,
    f"{result_A['triangle_avg_conf']:.3f}",
    f"{result_B['triangle_avg_conf']:.3f}")

cv("INVARIANT", "MDL001 self_verify=READY in both",
    result_A["self_verify"]["mdl001"] == "READY"
    and result_B["self_verify"]["mdl001"] == "READY",
    result_A["self_verify"]["mdl001"], result_B["self_verify"]["mdl001"])

cv("INVARIANT", "MDL002 self_verify=READY in both",
    result_A["self_verify"]["mdl002"] == "READY"
    and result_B["self_verify"]["mdl002"] == "READY",
    result_A["self_verify"]["mdl002"], result_B["self_verify"]["mdl002"])

cv("INVARIANT", "MDL006 self_verify=READY in both",
    result_A["self_verify"]["mdl006"] == "READY"
    and result_B["self_verify"]["mdl006"] == "READY",
    result_A["self_verify"]["mdl006"], result_B["self_verify"]["mdl006"])

cv("INVARIANT", "MDL007 self_verify=READY in both",
    result_A["self_verify"]["mdl007"] == "READY"
    and result_B["self_verify"]["mdl007"] == "READY",
    result_A["self_verify"]["mdl007"], result_B["self_verify"]["mdl007"])

cv("INVARIANT", "MDL008 self_verify=READY in both",
    result_A["self_verify"]["mdl008"] == "READY"
    and result_B["self_verify"]["mdl008"] == "READY",
    result_A["self_verify"]["mdl008"], result_B["self_verify"]["mdl008"])

cv("INVARIANT", "Both triangle_ok=True",
    result_A["triangle_ok"] and result_B["triangle_ok"],
    result_A["triangle_ok"], result_B["triangle_ok"])


# ─── EXPECTED DIFFERENCES (Set A != Set B) ───
cv("EXPECTED-DIFF", "Set A clean: phase_match_rate == 100%",
    result_A["phase_match_rate"] == 1.0,
    f"{result_A['phase_match_rate']:.2%}",
    f"{result_B['phase_match_rate']:.2%}")

cv("EXPECTED-DIFF", "Set B phase2.fin < Set A phase2.fin (missing field detected)",
    result_B["phase2_fin"] < result_A["phase2_fin"],
    f"{result_A['phase2_fin']} fin rows",
    f"{result_B['phase2_fin']} fin rows")

cv("EXPECTED-DIFF", "Set B has fewer matched pairs (coverage drop)",
    result_B["phase_match"] < result_A["phase_match"],
    f"{result_A['phase_match']} matched",
    f"{result_B['phase_match']} matched")

cv("EXPECTED-DIFF", "Set B p1_only > Set A p1_only (orphan rows surface)",
    result_B["phase_p1_only"] > result_A["phase_p1_only"],
    result_A["phase_p1_only"], result_B["phase_p1_only"])

cv("EXPECTED-DIFF", "Set B has expected p1_only count (≥2 from net_income)",
    result_B["phase_p1_only"] >= 2,
    result_A["phase_p1_only"], result_B["phase_p1_only"])


# ─── SANITY ───
cv("SANITY", "Set A elapsed < 30s",
    result_A["elapsed"] < 30, f"{result_A['elapsed']}s", "")
cv("SANITY", "Set B elapsed < 30s",
    result_B["elapsed"] < 30, "", f"{result_B['elapsed']}s")


# ── PRINT TABLE ─────────────────────────────────────────────────────────────
print()
print(f"  {'Category':<14s} {'Check':<54s}  {'Set A':>14s}  {'Set B':>14s}  Match")
print(f"  {'-'*14} {'-'*54}  {'-'*14}  {'-'*14}  -----")
for cat, name, ok, va, vb in CV_DETAILS:
    badge = "✓" if ok else "✗"
    va_str = str(va)[:14]; vb_str = str(vb)[:14]
    print(f"  {cat:<14s} {name[:54]:<54s}  {va_str:>14s}  {vb_str:>14s}  {badge}")

print()
print("=" * 76)
total = CV_PASS + CV_FAIL
classification = ("READY" if CV_FAIL == 0 else
                   "NEAR-READY" if CV_FAIL <= 2 else "NOT-READY")
print(f"  CROSS VALIDATION: {CV_PASS}/{total} pass · {CV_FAIL} fail · {classification}")
n_inv = sum(1 for c in CV_DETAILS if c[0] == "INVARIANT")
n_inv_ok = sum(1 for c in CV_DETAILS if c[0] == "INVARIANT" and c[2])
n_diff = sum(1 for c in CV_DETAILS if c[0] == "EXPECTED-DIFF")
n_diff_ok = sum(1 for c in CV_DETAILS if c[0] == "EXPECTED-DIFF" and c[2])
print(f"    INVARIANTS    : {n_inv_ok}/{n_inv} stable across runs")
print(f"    EXPECTED-DIFF : {n_diff_ok}/{n_diff} differences correctly detected")
print("=" * 76)


# ── HTML REPORT ─────────────────────────────────────────────────────────────
def _badge(s, color="#666"):
    return f'<span style="display:inline-block;padding:2px 8px;background:{color};color:white;font-weight:700;font-size:9px;letter-spacing:0.05em">{s}</span>'

cls_color = "#439a9a" if classification == "READY" else "#e0b020" if classification == "NEAR-READY" else "#c83030"
cls_emoji = "✓" if classification == "READY" else "⚠" if classification == "NEAR-READY" else "✗"

cv_rows_html = []
for cat, name, ok, va, vb in CV_DETAILS:
    cat_color = {"INVARIANT": "#4c78a8", "EXPECTED-DIFF": "#439a9a", "SANITY": "#666"}.get(cat, "#666")
    cv_rows_html.append(
        f'<tr><td>{_badge(cat, cat_color)}</td>'
        f'<td class="ck-name">{name}</td>'
        f'<td class="kv-v" style="text-align:right">{str(va)[:30]}</td>'
        f'<td class="kv-v" style="text-align:right">{str(vb)[:30]}</td>'
        f'<td class="ck-{"ok" if ok else "fail"}" style="text-align:center">'
        f'{"✓ PASS" if ok else "✗ FAIL"}</td></tr>')

set_table_a = f"""<table class="kv">
<tr><td class="kv-k">elapsed</td><td class="kv-v">{result_A['elapsed']}s</td></tr>
<tr><td class="kv-k">MDL001 converted</td><td class="kv-v">{result_A['mdl001_conv']}</td></tr>
<tr><td class="kv-k">MDL002 tables</td><td class="kv-v">{result_A['mdl002_tables']}</td></tr>
<tr><td class="kv-k">phase1 fin rows</td><td class="kv-v">{result_A['phase1_fin']}</td></tr>
<tr><td class="kv-k">phase2 fin rows</td><td class="kv-v">{result_A['phase2_fin']}</td></tr>
<tr><td class="kv-k">phase match</td><td class="kv-v">{result_A['phase_match']}/{result_A['phase_match']+result_A['phase_mismatch']} ({result_A['phase_match_rate']:.0%})</td></tr>
<tr><td class="kv-k">phase p1_only</td><td class="kv-v">{result_A['phase_p1_only']}</td></tr>
<tr><td class="kv-k">api rows</td><td class="kv-v">{result_A['api_rows']}</td></tr>
<tr><td class="kv-k">triangle match</td><td class="kv-v">{result_A['triangle_match']}/{result_A['triangle_total']} ({result_A['triangle_match_rate']:.0%})</td></tr>
<tr><td class="kv-k">avg confidence</td><td class="kv-v">{result_A['triangle_avg_conf']:.3f}</td></tr>
</table>"""

set_table_b = f"""<table class="kv">
<tr><td class="kv-k">elapsed</td><td class="kv-v">{result_B['elapsed']}s</td></tr>
<tr><td class="kv-k">MDL001 converted</td><td class="kv-v">{result_B['mdl001_conv']}</td></tr>
<tr><td class="kv-k">MDL002 tables</td><td class="kv-v">{result_B['mdl002_tables']}</td></tr>
<tr><td class="kv-k">phase1 fin rows</td><td class="kv-v">{result_B['phase1_fin']}</td></tr>
<tr><td class="kv-k">phase2 fin rows</td><td class="kv-v">{result_B['phase2_fin']}</td></tr>
<tr><td class="kv-k">phase match</td><td class="kv-v">{result_B['phase_match']}/{result_B['phase_match']+result_B['phase_mismatch']} ({result_B['phase_match_rate']:.0%})</td></tr>
<tr><td class="kv-k">phase p1_only</td><td class="kv-v">{result_B['phase_p1_only']}</td></tr>
<tr><td class="kv-k">api rows</td><td class="kv-v">{result_B['api_rows']}</td></tr>
<tr><td class="kv-k">triangle match</td><td class="kv-v">{result_B['triangle_match']}/{result_B['triangle_total']} ({result_B['triangle_match_rate']:.0%})</td></tr>
<tr><td class="kv-k">avg confidence</td><td class="kv-v">{result_B['triangle_avg_conf']:.3f}</td></tr>
</table>"""

html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN Activate · Dual-Set Cross Validate</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f5f4f0;color:#1a1a1a;font-family:'DM Sans',-apple-system,sans-serif;font-size:11px;line-height:1.6;padding:24px;max-width:1280px;margin:0 auto}}
.hdr{{border-top:4px solid;border-image:linear-gradient(90deg,#ff5e5e,#ffae5e,#ffe55e,#5eff8c,#5ec8ff,#8c5eff,#ff5ec8) 1;padding-top:16px;margin-bottom:24px}}
h1{{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;letter-spacing:-0.02em}}
h2{{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;margin-top:24px;margin-bottom:12px;color:#4c78a8}}
.sub{{font-family:'DM Mono',monospace;font-size:10px;color:#666;margin-top:4px}}
.cls-badge{{display:inline-block;padding:4px 12px;background:{cls_color};color:white;font-family:'Syne',sans-serif;font-weight:700;font-size:11px;margin-left:12px;letter-spacing:0.05em}}
.cd{{background:white;border:1px solid #e0ddd5;margin-bottom:16px}}
.cd-h{{background:#4c78a8;color:white;padding:8px 16px;font-family:'Syne',sans-serif;font-weight:600;font-size:12px;letter-spacing:0.03em}}
.cd-b{{padding:12px 16px}}
.tm{{background:#1a1a1a;color:#c8e0c8;font-family:'DM Mono',monospace;font-size:10px;padding:32px 16px 16px 16px;position:relative;white-space:pre;line-height:1.5}}
.tm::before{{content:"● ● ●";position:absolute;top:8px;left:12px;color:#ff5e5e;letter-spacing:4px;font-size:10px}}
.kv{{width:100%;border-collapse:collapse}}
.kv td{{padding:4px 8px;border-bottom:1px solid #f0ede5}}
.kv .kv-k{{font-weight:600;color:#4c78a8;width:50%}}
.kv .kv-v{{font-family:'DM Mono',monospace;font-size:10px}}
.ck-tbl{{width:100%;border-collapse:collapse;font-size:10px}}
.ck-tbl th{{background:#f5f4f0;color:#4c78a8;text-align:left;padding:6px 8px;font-weight:600;border-bottom:2px solid #4c78a8;font-size:10px}}
.ck-tbl td{{padding:5px 8px;border-bottom:1px solid #f0ede5;font-family:'DM Mono',monospace;font-size:10px;vertical-align:middle}}
.ck-name{{font-weight:500;min-width:280px;font-family:'DM Sans',sans-serif}}
.ck-ok{{color:#439a9a;font-weight:600;min-width:80px}}
.ck-fail{{color:#c83030;font-weight:700;min-width:80px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.foot{{margin-top:24px;color:#999;font-family:'DM Mono',monospace;font-size:9px;text-align:right}}
</style></head><body>

<div class="hdr">
<h1>VRN ACTIVATE · DUAL-SET CROSS VALIDATE<span class="cls-badge">{cls_emoji} {classification}</span></h1>
<div class="sub">Set A clean vs Set B noisy · Invariants stable + Expected differences detected · {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
</div>

<div class="cd"><div class="cd-h">⚓ HardGate 7-Tool BOOT_PRECHECK (shared)</div>
<div class="cd-b"><div class="tm">$ HardGate
  policy:    {HG_CAPS['policy']}
  py_inject: {HG_CAPS['py_inject']}
  capable:   {HG_CAPS['n_capable']}/7
  elapsed:   {HG_CAPS['elapsed_ms']}ms
  seal:      {HG_CAPS['seal']}
  ssot_dir:  {SSOT_DIR}</div></div></div>

<h2>Per-Set Results</h2>
<div class="grid2">
<div class="cd"><div class="cd-h">SET A — Clean (no OCR noise)</div><div class="cd-b">{set_table_a}</div></div>
<div class="cd"><div class="cd-h">SET B — Noisy (1 typo + 1 missing)</div><div class="cd-b">{set_table_b}</div></div>
</div>

<h2>Cross-Validation Checks ({CV_PASS}/{total} pass)</h2>
<div class="cd"><div class="cd-h">🔬 Invariants ({n_inv_ok}/{n_inv}) + Expected Differences ({n_diff_ok}/{n_diff})</div>
<div class="cd-b">
<table class="ck-tbl">
<thead><tr><th>Category</th><th>Check</th>
<th style="text-align:right">Set A</th><th style="text-align:right">Set B</th>
<th style="text-align:center">Match</th></tr></thead>
<tbody>{"".join(cv_rows_html)}</tbody>
</table>
</div></div>

<h2>Final Verdict</h2>
<div class="cd"><div class="cd-h">🎯 System Status</div>
<div class="cd-b"><div class="tm">$ activation summary
  hardgate seal       : {HG_CAPS['seal']} ({HG_CAPS['n_capable']}/7)

  SET A — Clean
    phase compare     : {result_A['phase_match_rate']:.2%} ({result_A['phase_match']}/{result_A['phase_match']+result_A['phase_mismatch']})
    triangle validate : {result_A['triangle_match_rate']:.2%} ({result_A['triangle_match']}/{result_A['triangle_total']})
    elapsed           : {result_A['elapsed']}s

  SET B — Noisy
    phase compare     : {result_B['phase_match_rate']:.2%} ({result_B['phase_match']}/{result_B['phase_match']+result_B['phase_mismatch']})
    phase p1_only     : {result_B['phase_p1_only']}  ← detected missing OCR
    triangle validate : {result_B['triangle_match_rate']:.2%} ({result_B['triangle_match']}/{result_B['triangle_total']})
    elapsed           : {result_B['elapsed']}s

  CROSS VALIDATION
    invariants stable : {n_inv_ok}/{n_inv}
    expected diffs    : {n_diff_ok}/{n_diff}
    overall           : {classification}</div></div></div>

<div class="foot">VRN Activate Dual-Set Cross-Validate · v1.1.0 · {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
</body></html>"""


# ── SAVE ────────────────────────────────────────────────────────────────────
out_html = os.path.join(args.output_dir, "VRN_DualSet_Report.html")
out_json = os.path.join(args.output_dir, "VRN_DualSet_Summary.json")

Path(out_html).write_text(html, encoding="utf-8")
Path(out_json).write_text(json.dumps({
    "generated":      time.strftime("%Y-%m-%d %H:%M:%S"),
    "classification": classification,
    "cv_pass":        CV_PASS,
    "cv_fail":        CV_FAIL,
    "cv_total":       total,
    "invariants":     {"pass": n_inv_ok, "total": n_inv},
    "expected_diffs": {"pass": n_diff_ok, "total": n_diff},
    "hardgate":       HG_CAPS,
    "set_A":          result_A,
    "set_B":          result_B,
    "checks":         [{"category": cat, "name": n, "ok": ok,
                         "set_A": va, "set_B": vb}
                        for cat, n, ok, va, vb in CV_DETAILS],
}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print()
print(f"  → {out_html}")
print(f"  → {out_json}")
print()
print(f"  ACTIVATION: {'✓ COMPLETE' if classification == 'READY' else '✗ ISSUES'}")

sys.exit(0 if classification == "READY" else 1)
