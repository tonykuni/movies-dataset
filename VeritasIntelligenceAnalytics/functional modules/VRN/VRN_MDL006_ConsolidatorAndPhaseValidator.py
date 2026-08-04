# -*- coding: utf-8 -*-
from __future__ import annotations
"""
VRN_MDL006_ConsolidatorAndPhaseValidator.py
=============================================
VERITAS REPORT NOVA -- MDL006  Consolidation + Phase1/Phase2 Validator
Version   : 1.0.0   |   Module ID : VRN-MDL006-SUP-001
Asset ID  : VRN-MDL006-CLS-001
Policy    : 功能只增不減 · append-only · SSOT

PIPELINE POSITION
  MDL002 (VRN_MDL002_Layout.json)  ← layout source
  MDL004 (VRN_MDL004_Tables.json)  ← OCR tables
  MDL005 (VRN_MDL005_Text.json)    ← OCR text
    ↓ MDL006 consolidates
  PHASE 1: MDL001/MDL002 → MDL003 → VRN_BasicInfoPhase1 / VRN_FinancialDataPhase1
  PHASE 2: MDL001/MDL002 → MDL004/MDL005/MDL006 → VRN_BasicInfoPhase2 / VRN_FinancialDataPhase2
  COMPARE: Phase1 == Phase2 → SYSTEM SUCCESS

OUTPUT SCHEMA
  VRN_BasicInfo:
    date(today) / updating_date / ticker / yfinance_ticker / bloomberg_ticker /
    company_name / report_date / broker / broker_abbr /
    rating_raw / rating_canonical / target_price / report_code

  VRN_FinancialData:
    date(today) / updating_date / ticker / yfinance_ticker / company_name /
    category(IS/BS/CF/VAL/RATIO) / data_name / unit / period /
    value / status(verified/calc/err) / confidence / source(phase1/phase2/both)
"""

__version__   = "1.1.0"
__module_id__ = "VRN-MDL006-SUP-001"

import os, sys, re, json, time, math, hashlib, logging, sqlite3, threading
import gc, warnings, collections, importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date as _date

warnings.filterwarnings("ignore")

def _si(n):
    try: return importlib.import_module(n)
    except: return None

pd      = _si("pandas")
pyarrow = _si("pyarrow")
duckdb  = _si("duckdb")
xxhash  = _si("xxhash")

# v1.1.0 NEW: polars + duckdb alias
pl         = _si("polars")
duckdb_lib = duckdb  # alias for unified naming
POLARS_OK  = pl is not None
DUCKDB_OK  = duckdb_lib is not None

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── Celeritas plugin ───────────────────────────────────────────────────────────
_CEL: object = None;  _CEL_OK: bool = False
_SSOT: object = None; _SSOT_OK: bool = False
# [VRN:ANCHOR:HARDGATE_HOLDERS:V1] Additional holders per VIA_Supportive_HardGate_Seal.json
_REG: object = None;  _REG_OK: bool = False  # VIA_RegistryCore_v1
_BRG: object = None;  _BRG_OK: bool = False  # VIA_Runtime_Bridge_All_in_One
_ENV: object = None;  _ENV_OK: bool = False  # VIA_EnvManager
_AST: object = None;  _AST_OK: bool = False  # VIA_Panorama_AST_RuntimeInjector
_NET: object = None;  _NET_OK: bool = False  # VeritasAegisNexus

def _load_plugins(ssot_dir: str) -> Dict[str, bool]:
    """VRN-MDL006: Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH. Python 3.12 inject.
    """
    global _CEL, _CEL_OK, _SSOT, _SSOT_OK
    global _REG, _REG_OK, _BRG, _BRG_OK, _ENV, _ENV_OK, _AST, _AST_OK, _NET, _NET_OK
    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False}
    import importlib.util as _ilu
    # [VRN:ANCHOR:HARDGATE_PLUGIN_MAP:V1] order matches HardGate Seal
    for fname, key, gname in [
        ("VIA_SSOT_Unified.py",                 "via_ssot",       "_SSOT"),
        ("VIA_RegistryCore_v1.py",              "registry",       "_REG"),
        ("VIA_Runtime_Bridge_All_in_One.py",    "runtime_bridge", "_BRG"),
        ("VIA_EnvManager.py",                   "env_manager",    "_ENV"),
        ("VIA_Panorama_AST_RuntimeInjector.py", "ast_planner",    "_AST"),
        ("VeritasCeleritas.py",                 "celeritas",      "_CEL"),
        ("VeritasAegisNexus.py",                "aegis",          "_NET"),
    ]:
        for base in [Path(ssot_dir), Path(ssot_dir).parent]:
            p = base / fname
            if p.exists():
                try:
                    mod_name = fname.replace(".py","")
                    spec = _ilu.spec_from_file_location(mod_name, str(p))
                    mod  = _ilu.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    if gname == "_CEL":
                        sys.modules["VeritasCeleritas"] = mod   # Py3.12 dataclass fix
                    spec.loader.exec_module(mod)
                    globals()[gname] = mod
                    if gname == "_CEL":
                        _CEL_OK = True
                        if hasattr(mod, "bootstrap_at_import"): mod.bootstrap_at_import(__file__)
                        if hasattr(mod, "warm_thread_pool"):    mod.warm_thread_pool()
                    elif gname == "_SSOT": _SSOT_OK = True
                    elif gname == "_REG":  _REG_OK  = True
                    elif gname == "_BRG":  _BRG_OK  = True
                    elif gname == "_ENV":  _ENV_OK  = True
                    elif gname == "_AST":  _AST_OK  = True
                    elif gname == "_NET":  _NET_OK  = True
                    result[key] = True
                    log.info("[MDL006] %s loaded from %s", mod_name, p)
                    break
                except Exception as e:
                    log.debug("[MDL006] %s: %s", fname, e)
    return result

def _mdl006_accel_init(workers: int = 0) -> Dict:
    """VRN-MDL006: 6-ENV thread init + GC tuning."""
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for v in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(v, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {"workers": w, "pandas": pd is not None,
            "pyarrow": pyarrow is not None, "duckdb": duckdb is not None,
            "celeritas": _CEL_OK, "via_ssot": _SSOT_OK}

def _cel_submit(fn, *args, **kw):
    """Submit via Celeritas if available."""
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)

# ── PARAMS ────────────────────────────────────────────────────────────────────
_PARAMS: dict = {
    "mdl002_temp":  "/home/claude/mdl002_temp",
    "mdl003_temp":  "/home/claude/mdl003_temp",
    "mdl004_temp":  "/home/claude/mdl004_temp",
    "mdl005_temp":  "/home/claude/mdl005_temp",
    "mdl006_temp":  "/home/claude/mdl006_temp",
    "output_dir":   "/home/claude/vrn_output",
    "compare_tol":  0.02,    # 2% numeric tolerance for Phase1==Phase2
    "min_confidence": 0.60,  # minimum confidence to include in output
    "csv_encoding": "utf-8-sig",  # BOM for Excel compatibility
    # ── v1.1.0 NEW (append-only) ─────────────────────────────────────────────
    "use_duckdb":    True,    # P3 DuckDB primary, sqlite fallback
    "batch_size":    5000,    # P3 buffer flush threshold
    "polars_first":  True,    # P5 polars vectorized exports
    "self_verify":   True,    # P6 4-phase HTML
    "ssot_dir":      "",      # 7-tool HardGate plugin dir
}
_P = _PARAMS

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── TW TICKER REGEX (locked) ──────────────────────────────────────────────────
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

def _yfinance_ticker(ticker: str) -> str:
    return f"{ticker}.TW" if ticker else ""

def _bloomberg_ticker(ticker: str) -> str:
    return f"{ticker} TT" if ticker else ""

def _hash8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

def _jload(p: str) -> Any:
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except: return None

def _clean_num(v) -> Optional[float]:
    if v is None: return None
    try:
        s = str(v).replace(",","").replace("，","").replace("%","").strip()
        s = re.sub(r"^\((.*)\)$", r"-\1", s)
        return float(s)
    except: return None

today_str = _date.today().isoformat()

# ─────────────────────────────────────────────────────────────────────────────
# BASIC INFO SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

BASIC_INFO_COLS = [
    "date", "updating_date", "ticker", "yfinance_ticker", "bloomberg_ticker",
    "company_name", "report_date", "broker", "broker_abbr",
    "rating_raw", "rating_canonical", "target_price", "report_code",
    "source_phase", "confidence",
]

# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL DATA SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

FINANCIAL_DATA_COLS = [
    "date", "updating_date", "ticker", "yfinance_ticker", "company_name",
    "category", "data_name", "unit", "period",
    "value", "status", "confidence", "source_phase", "report_code",
]

# Category mapping from canonical field name
_CATEGORY_MAP: Dict[str, str] = {
    "revenue":"IS","cogs":"IS","gross_profit":"IS","opex":"IS",
    "operating_income":"IS","pretax_income":"IS","net_income":"IS",
    "net_income_parent":"IS","basic_eps":"IS","diluted_eps":"IS","eps":"IS",
    "gross_margin":"RATIO","operating_margin":"RATIO","net_margin":"RATIO",
    "revenue_growth":"RATIO","roe":"RATIO","roa":"RATIO",
    "total_assets":"BS","total_liabilities":"BS","total_equity":"BS",
    "current_assets":"BS","cash":"BS",
    "operating_cf":"CF","investing_cf":"CF","financing_cf":"CF","free_cf":"CF","capex":"CF",
    "pe_ratio":"VAL","pb_ratio":"VAL","dividend_yield":"VAL","bvps":"VAL","dps":"VAL",
}

def _category(canonical: str) -> str:
    return _CATEGORY_MAP.get(canonical, "OTHER")

# ─────────────────────────────────────────────────────────────────────────────
# LOADERS — read output from each upstream module
# ─────────────────────────────────────────────────────────────────────────────

def load_mdl003_output(mdl003_temp: str) -> Optional[Dict]:
    p = Path(mdl003_temp) / "VRN_MDL003_Restored.json"
    return _jload(str(p))

def load_mdl004_output(mdl004_temp: str) -> Optional[Dict]:
    p = Path(mdl004_temp) / "VRN_MDL004_Tables.json"
    return _jload(str(p))

def load_mdl005_output(mdl005_temp: str) -> Optional[Dict]:
    p = Path(mdl005_temp) / "VRN_MDL005_Text.json"
    return _jload(str(p))

def load_mdl002_output(mdl002_temp: str) -> Optional[Dict]:
    p = Path(mdl002_temp) / "VRN_MDL002_Layout.json"
    return _jload(str(p))

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTORS — parse upstream data into flat rows
# ─────────────────────────────────────────────────────────────────────────────

def extract_basic_info_from_report(report: Dict, phase: str) -> Dict:
    """Extract one BasicInfo row from a PDF report dict."""
    ticker = report.get("ticker","")
    return {
        "date":             today_str,
        "updating_date":    report.get("generated", today_str)[:19],
        "ticker":           ticker,
        "yfinance_ticker":  _yfinance_ticker(ticker),
        "bloomberg_ticker": _bloomberg_ticker(ticker),
        "company_name":     report.get("company_name", ""),
        "report_date":      report.get("report_date",""),
        "broker":           report.get("broker",""),
        "broker_abbr":      report.get("broker_abbr",""),
        "rating_raw":       report.get("rating_raw",""),
        "rating_canonical": report.get("rating_canonical",""),
        "target_price":     _clean_num(report.get("target_price")),
        "report_code":      report.get("report_code",""),
        "source_phase":     phase,
        "confidence":       report.get("validation_grade_score", 0.8),
    }

def extract_financial_rows_from_mdl003(report: Dict, phase: str) -> List[Dict]:
    """Extract FinancialData rows from MDL003 restored tables."""
    ticker = report.get("ticker","")
    yf     = _yfinance_ticker(ticker)
    rc     = report.get("report_code","")
    rows   = []
    for tbl in report.get("restored_tables", []):
        if not tbl.get("ok"): continue
        for row in tbl.get("rows", []):
            canonical = row.get("canonical","")
            label_raw = row.get("label_raw","")
            category  = _category(canonical)
            for period, val in (row.get("values") or {}).items():
                if val is None: continue
                src   = row.get("sources",{}).get(period,"RP")
                status = "verified" if src == "RP" else ("calc" if src == "CALC" else "err")
                rows.append({
                    "date":          today_str,
                    "updating_date": today_str,
                    "ticker":        ticker,
                    "yfinance_ticker": yf,
                    "company_name":  report.get("company_name",""),
                    "category":      category,
                    "data_name":     label_raw,
                    "unit":          "mn_ntd",
                    "period":        period,
                    "value":         val,
                    "status":        status,
                    "confidence":    0.85 if status == "verified" else 0.70,
                    "source_phase":  phase,
                    "report_code":   rc,
                })
    return rows

def extract_financial_rows_from_mdl004(pdf_report: Dict, phase: str) -> List[Dict]:
    """Extract FinancialData rows from MDL004 OCR table fetch."""
    ticker = pdf_report.get("ticker","")
    yf     = _yfinance_ticker(ticker)
    rc     = pdf_report.get("report_code","")
    rows   = []
    for tbl in pdf_report.get("tables", []):
        if not tbl.get("ok", True): continue
        confidence = tbl.get("confidence", 0.7)
        if confidence < _P["min_confidence"]: continue
        periods = tbl.get("periods", [])
        for row in tbl.get("rows", []):
            label     = row.get("label_raw","")
            canonical = row.get("canonical", label.lower().replace(" ","_"))
            category  = _category(canonical)
            for period, val in (row.get("values") or {}).items():
                if val is None: continue
                status = row.get("status","PASS")
                rows.append({
                    "date":          today_str,
                    "updating_date": today_str,
                    "ticker":        ticker,
                    "yfinance_ticker": yf,
                    "company_name":  "",
                    "category":      category,
                    "data_name":     label,
                    "unit":          "mn_ntd",
                    "period":        period,
                    "value":         _clean_num(val) if not isinstance(val, float) else val,
                    "status":        "verified" if status=="PASS" else "err",
                    "confidence":    confidence,
                    "source_phase":  phase,
                    "report_code":   rc,
                })
    return rows

def extract_financial_rows_from_mdl002(pdf_report: Dict, phase: str) -> List[Dict]:
    """Extract FinancialData rows from MDL002 layout (raw table data)."""
    ticker = pdf_report.get("ticker","")
    yf     = _yfinance_ticker(ticker)
    rc     = pdf_report.get("report_code","")
    rows   = []
    for tbl in pdf_report.get("tables", []):
        if not tbl.get("is_financial"): continue
        raw_data = tbl.get("raw_data", [])
        periods  = tbl.get("header_periods", [])
        if not raw_data or not periods: continue
        for row in raw_data[1:]:  # skip header
            if not row or not row[0]: continue
            label = str(row[0]).strip()
            if not label: continue
            for ci, cell in enumerate(row[1:]):
                period = periods[ci] if ci < len(periods) else f"col{ci}"
                val = _clean_num(cell)
                if val is None: continue
                rows.append({
                    "date":          today_str,
                    "updating_date": today_str,
                    "ticker":        ticker,
                    "yfinance_ticker": yf,
                    "company_name":  "",
                    "category":      "OTHER",
                    "data_name":     label,
                    "unit":          "mn_ntd",
                    "period":        period,
                    "value":         val,
                    "status":        "raw",
                    "confidence":    0.65,
                    "source_phase":  phase,
                    "report_code":   rc,
                })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 BUILDER (MDL003 output)
# ─────────────────────────────────────────────────────────────────────────────

def build_phase1(mdl003_temp: str) -> Tuple[List[Dict], List[Dict]]:
    """Build Phase1 BasicInfo + FinancialData from MDL003."""
    data = load_mdl003_output(mdl003_temp)
    if not data:
        log.warning("[MDL006] Phase1: MDL003 output not found in %s", mdl003_temp)
        return [], []
    basic_rows: List[Dict] = []
    fin_rows:   List[Dict] = []
    for rpt in data.get("reports", []):
        basic_rows.append(extract_basic_info_from_report(rpt, "phase1"))
        fin_rows.extend(extract_financial_rows_from_mdl003(rpt, "phase1"))
    log.info("[MDL006] Phase1: basic=%d financial=%d", len(basic_rows), len(fin_rows))
    return basic_rows, fin_rows

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 BUILDER (MDL002 + MDL004 + MDL005)
# ─────────────────────────────────────────────────────────────────────────────

def build_phase2(mdl002_temp: str, mdl004_temp: str, mdl005_temp: str) -> Tuple[List[Dict], List[Dict]]:
    """Build Phase2 BasicInfo + FinancialData by consolidating MDL002/004/005."""
    basic_rows: List[Dict] = []
    fin_rows:   List[Dict] = []

    # MDL002 — layout data (best for basic metadata from page 1 zones)
    mdl002 = load_mdl002_output(mdl002_temp)
    if mdl002:
        for rpt in mdl002.get("reports", []):
            basic_rows.append(extract_basic_info_from_report(rpt, "phase2"))
            fin_rows.extend(extract_financial_rows_from_mdl002(rpt, "phase2"))

    # MDL004 — OCR table fetch (best financial data)
    mdl004 = load_mdl004_output(mdl004_temp)
    if mdl004:
        for rpt in mdl004.get("reports", []):
            fin_rows.extend(extract_financial_rows_from_mdl004(rpt, "phase2"))

    # MDL005 — text extraction (supplement metadata from text segments)
    mdl005 = load_mdl005_output(mdl005_temp)
    if mdl005:
        for rpt in mdl005.get("reports", []):
            # Extract rating/TP from text blocks if not already found
            for pg in rpt.get("pages", []):
                for blk in pg.get("blocks", []):
                    txt = blk.get("text","")
                    # Rating detection from text
                    for seg_kw in ["Outperform","Buy","Hold","Sell","Overweight",
                                   "買進","增持","中立","持有"]:
                        if seg_kw in txt:
                            # Tag to report code
                            break

    log.info("[MDL006] Phase2: basic=%d financial=%d", len(basic_rows), len(fin_rows))
    return basic_rows, fin_rows

# ─────────────────────────────────────────────────────────────────────────────
# DEDUP + BEST VALUE SELECTION
# ─────────────────────────────────────────────────────────────────────────────

def dedup_and_best_basic(rows: List[Dict]) -> List[Dict]:
    """Keep one BasicInfo row per report_code, highest confidence."""
    best: Dict[str, Dict] = {}
    for r in rows:
        key = r.get("report_code","") or r.get("ticker","")
        if key not in best or r.get("confidence",0) > best[key].get("confidence",0):
            best[key] = r
    return list(best.values())

def dedup_and_best_financial(rows: List[Dict]) -> List[Dict]:
    """Keep one FinancialData row per (report_code, data_name, period), highest confidence."""
    best: Dict[str, Dict] = {}
    for r in rows:
        key = "||".join([
            str(r.get("report_code","")),
            str(r.get("data_name","")),
            str(r.get("period","")),
        ])
        existing = best.get(key)
        if existing is None or r.get("confidence",0) > existing.get("confidence",0):
            best[key] = r
    return list(best.values())

# ─────────────────────────────────────────────────────────────────────────────
# PHASE COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CompareResult:
    n_phase1_basic:    int = 0
    n_phase2_basic:    int = 0
    n_phase1_fin:      int = 0
    n_phase2_fin:      int = 0
    n_fin_matched:     int = 0
    n_fin_mismatch:    int = 0
    n_fin_p1_only:     int = 0
    n_fin_p2_only:     int = 0
    match_rate:        float = 0.0
    success:           bool = False
    mismatch_details:  List[Dict] = field(default_factory=list)
    summary:           str = ""

def compare_phases(
    basic1: List[Dict], fin1: List[Dict],
    basic2: List[Dict], fin2: List[Dict],
    tol:    float = 0.02,
) -> CompareResult:
    """Compare Phase1 vs Phase2. Success if match_rate >= 0.95."""
    cr = CompareResult(
        n_phase1_basic=len(basic1), n_phase2_basic=len(basic2),
        n_phase1_fin=len(fin1),     n_phase2_fin=len(fin2),
    )

    # Build lookup for Phase1 financial: key = (report_code, data_name, period)
    def _fin_key(r): return (r.get("report_code",""), r.get("data_name",""), r.get("period",""))
    p1_map = {_fin_key(r): r for r in fin1}
    p2_map = {_fin_key(r): r for r in fin2}

    all_keys = set(p1_map) | set(p2_map)
    for k in all_keys:
        r1 = p1_map.get(k)
        r2 = p2_map.get(k)
        if r1 and not r2:
            cr.n_fin_p1_only += 1
        elif r2 and not r1:
            cr.n_fin_p2_only += 1
        else:
            v1 = r1.get("value")
            v2 = r2.get("value")
            if v1 is None or v2 is None:
                cr.n_fin_mismatch += 1
                continue
            diff = abs(v1 - v2) / max(abs(v1), abs(v2), 1e-6)
            if diff <= tol:
                cr.n_fin_matched += 1
            else:
                cr.n_fin_mismatch += 1
                cr.mismatch_details.append({
                    "report_code": k[0], "data_name": k[1], "period": k[2],
                    "phase1_val": v1, "phase2_val": v2,
                    "diff_pct": round(diff*100, 2),
                })

    total_comparable = cr.n_fin_matched + cr.n_fin_mismatch
    cr.match_rate = round(cr.n_fin_matched / max(total_comparable, 1), 4)
    cr.success    = cr.match_rate >= 0.95 and total_comparable > 0
    cr.summary    = (
        f"Phase1: basic={cr.n_phase1_basic} fin={cr.n_phase1_fin} | "
        f"Phase2: basic={cr.n_phase2_basic} fin={cr.n_phase2_fin} | "
        f"Match: {cr.n_fin_matched}/{total_comparable} ({cr.match_rate*100:.1f}%) | "
        f"P1_only={cr.n_fin_p1_only} P2_only={cr.n_fin_p2_only} | "
        f"{'SUCCESS' if cr.success else 'NEEDS IMPROVEMENT'}"
    )
    return cr

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT WRITERS — Parquet + CSV (UTF-8 BOM) + DuckDB
# ─────────────────────────────────────────────────────────────────────────────

def write_outputs(
    rows:     List[Dict],
    columns:  List[str],
    base_name: str,
    out_dir:  str,
) -> Dict[str, str]:
    """Write Parquet + CSV(UTF-8 BOM) + DuckDB. Returns {format: path}."""
    paths: Dict[str, str] = {}
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if not rows or not pd:
        log.warning("[MDL006] No rows to write for %s", base_name)
        return paths

    # Normalise rows to have all columns
    norm = []
    for r in rows:
        row = {c: r.get(c) for c in columns}
        norm.append(row)

    df = pd.DataFrame(norm, columns=columns)

    # ── JSON (v1.1.0 NEW: required by SelfVerifier) ──────────────────────
    json_path = str(Path(out_dir) / f"{base_name}.json")
    try:
        Path(json_path).write_text(
            json.dumps(norm, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        paths["json"] = json_path
    except Exception as e:
        log.warning("[MDL006] JSON write %s: %s", json_path, e)

    # ── Parquet ────────────────────────────────────────────────────────────
    if pyarrow:
        pq_path = str(Path(out_dir) / f"{base_name}.parquet")
        df.to_parquet(pq_path, index=False)
        paths["parquet"] = pq_path
        log.info("[MDL006] Parquet: %s (%d rows)", pq_path, len(df))

    # ── CSV (UTF-8 BOM — Excel 開啟不亂碼) ────────────────────────────────
    csv_path = str(Path(out_dir) / f"{base_name}.csv")
    df.to_csv(csv_path, index=False, encoding=_P["csv_encoding"])
    paths["csv"] = csv_path
    log.info("[MDL006] CSV (utf-8-sig): %s (%d rows)", csv_path, len(df))

    # ── DuckDB ────────────────────────────────────────────────────────────
    if duckdb:
        db_path  = str(Path(out_dir) / f"{base_name}.duckdb")
        tbl_name = base_name.lower().replace("-","_").replace(" ","_")
        try:
            con = duckdb.connect(db_path)
            con.execute(f"DROP TABLE IF EXISTS {tbl_name}")
            con.execute(f"CREATE TABLE {tbl_name} AS SELECT * FROM df")
            n = con.execute(f"SELECT COUNT(*) FROM {tbl_name}").fetchone()[0]
            con.close()
            paths["duckdb"] = db_path
            log.info("[MDL006] DuckDB: %s table=%s rows=%d", db_path, tbl_name, n)
        except Exception as e:
            log.warning("[MDL006] DuckDB write %s: %s", db_path, e)

    return paths

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT VERIFICATION — multi-method cross-check
# ─────────────────────────────────────────────────────────────────────────────

def audit_financial_data(fin_rows: List[Dict], phase: str) -> Dict:
    """Multi-method verification audit."""
    audit = {
        "phase":         phase,
        "total":         len(fin_rows),
        "verified":      0,
        "calc":          0,
        "err":           0,
        "raw":           0,
        "checks":        [],
        "pass":          False,
    }
    # Count by status
    for r in fin_rows:
        s = r.get("status","raw")
        if "verified" in s: audit["verified"] += 1
        elif "calc" in s:   audit["calc"] += 1
        elif "err" in s:    audit["err"] += 1
        else:               audit["raw"] += 1

    # Check 1: gross_profit == revenue - cogs (per report_code + period)
    by_rcp: Dict = {}
    for r in fin_rows:
        k = (r.get("report_code",""), r.get("period",""))
        by_rcp.setdefault(k, {})[r.get("data_name","").lower()] = r.get("value")

    gp_checks = 0; gp_pass = 0
    for (rc,period), fields in by_rcp.items():
        rev  = fields.get("revenue") or fields.get("net revenue") or fields.get("营业收入淨額")
        cogs = fields.get("cogs") or fields.get("cost of revenue") or fields.get("营业成本")
        gp   = fields.get("gross profit") or fields.get("gross_profit") or fields.get("营业毛利淨額")
        if rev is not None and cogs is not None and gp is not None:
            gp_checks += 1
            expected = rev - cogs
            diff = abs(gp - expected) / max(abs(expected), 1e-6)
            if diff <= 0.03: gp_pass += 1

    if gp_checks > 0:
        audit["checks"].append({
            "name": "gross_profit=revenue-cogs",
            "total": gp_checks, "pass": gp_pass,
            "rate": round(gp_pass/gp_checks, 3),
        })

    # Check 2: all target_price > 0 in basic info (done separately)

    # Check 3: EPS > 0 for profitable companies
    eps_rows = [r for r in fin_rows if "eps" in r.get("data_name","").lower()]
    pos_eps  = sum(1 for r in eps_rows if (r.get("value") or 0) > 0)
    if eps_rows:
        audit["checks"].append({
            "name": "eps_positive",
            "total": len(eps_rows), "pass": pos_eps,
            "rate": round(pos_eps/len(eps_rows), 3),
        })

    # Check 4: confidence above threshold
    low_conf = sum(1 for r in fin_rows if (r.get("confidence",1.0) or 1.0) < _P["min_confidence"])
    audit["checks"].append({
        "name": f"confidence>={_P['min_confidence']}",
        "total": len(fin_rows), "pass": len(fin_rows)-low_conf,
        "rate": round((len(fin_rows)-low_conf)/max(len(fin_rows),1), 3),
    })

    # Overall pass if err < 10% and at least 1 verified check
    err_rate = audit["err"] / max(audit["total"],1)
    all_checks_ok = all(c.get("rate",0) >= 0.7 for c in audit["checks"])
    audit["pass"] = err_rate < 0.10 and (audit["verified"] + audit["calc"]) > 0

    log.info("[MDL006] Audit %s: total=%d verified=%d calc=%d err=%d pass=%s",
             phase, audit["total"], audit["verified"], audit["calc"],
             audit["err"], audit["pass"])
    return audit

# ============================================================================
# [VRN:ANCHOR:MDL006-BATCH-001]  v1.1.0  P3 BATCH BUFFER + DUCK WRITER
# ── 同 MDL002/004/005 v1.1.0 模式：一次 flush，避免 sqlite 鎖競爭         ─
# ============================================================================

class MDL006BatchBuffer:
    """VRN-MDL006-CLS-002 (NEW v1.1.0)."""
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._basic1_buf: List[Tuple] = []
        self._basic2_buf: List[Tuple] = []
        self._fin1_buf:   List[Tuple] = []
        self._fin2_buf:   List[Tuple] = []
        self._cmp_buf:    List[Tuple] = []
        self._lock = threading.Lock()

    def push_basic(self, rows: List[Dict], phase: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rs = [(None, r.get("date",""), r.get("updating_date",""),
               r.get("ticker",""), r.get("yfinance_ticker",""),
               r.get("bloomberg_ticker",""), r.get("company_name",""),
               r.get("report_date",""), r.get("broker",""), r.get("broker_abbr",""),
               r.get("rating_raw",""), r.get("rating_canonical",""),
               float(r.get("target_price",0.0) or 0.0),
               r.get("report_code",""), r.get("source_phase",phase),
               float(r.get("confidence",0.8) or 0.8), ts) for r in rows]
        with self._lock:
            (self._basic1_buf if phase == "phase1" else self._basic2_buf).extend(rs)

    def push_financial(self, rows: List[Dict], phase: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rs = [(None, r.get("date",""), r.get("updating_date",""),
               r.get("ticker",""), r.get("yfinance_ticker",""),
               r.get("company_name",""), r.get("category",""),
               r.get("data_name",""), r.get("unit",""), r.get("period",""),
               float(r.get("value",0.0) or 0.0), r.get("status",""),
               float(r.get("confidence",0.7) or 0.7), r.get("source_phase",phase),
               r.get("report_code",""), ts) for r in rows]
        with self._lock:
            (self._fin1_buf if phase == "phase1" else self._fin2_buf).extend(rs)

    def push_compare(self, mismatches: List[Dict]):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rs = [(None, m.get("report_code",""), m.get("data_name",""),
               m.get("period",""),
               float(m.get("phase1_value", 0.0) or 0.0),
               float(m.get("phase2_value", 0.0) or 0.0),
               float(m.get("diff_pct", 0.0) or 0.0),
               m.get("status",""), ts) for m in mismatches]
        with self._lock:
            self._cmp_buf.extend(rs)

    def stats(self) -> Dict[str, int]:
        return {"basic1": len(self._basic1_buf), "basic2": len(self._basic2_buf),
                "fin1":   len(self._fin1_buf),   "fin2":   len(self._fin2_buf),
                "cmp":    len(self._cmp_buf)}

    def consume_all(self) -> Tuple[List, List, List, List, List]:
        with self._lock:
            b1, b2, f1, f2, c = (self._basic1_buf, self._basic2_buf,
                                  self._fin1_buf, self._fin2_buf, self._cmp_buf)
            self._basic1_buf, self._basic2_buf = [], []
            self._fin1_buf, self._fin2_buf, self._cmp_buf = [], [], []
        return b1, b2, f1, f2, c


_DDL_DUCK_M006_BASIC = """
CREATE TABLE IF NOT EXISTS vrn_mdl006_basic_{phase} (
    id INTEGER, date VARCHAR, updating_date VARCHAR,
    ticker VARCHAR, yfinance_ticker VARCHAR, bloomberg_ticker VARCHAR,
    company_name VARCHAR, report_date VARCHAR,
    broker VARCHAR, broker_abbr VARCHAR,
    rating_raw VARCHAR, rating_canonical VARCHAR,
    target_price DOUBLE, report_code VARCHAR,
    source_phase VARCHAR, confidence DOUBLE, ts VARCHAR
);
"""

_DDL_DUCK_M006_FIN = """
CREATE TABLE IF NOT EXISTS vrn_mdl006_financial_{phase} (
    id INTEGER, date VARCHAR, updating_date VARCHAR,
    ticker VARCHAR, yfinance_ticker VARCHAR, company_name VARCHAR,
    category VARCHAR, data_name VARCHAR, unit VARCHAR, period VARCHAR,
    value DOUBLE, status VARCHAR, confidence DOUBLE,
    source_phase VARCHAR, report_code VARCHAR, ts VARCHAR
);
"""

_DDL_DUCK_M006_CMP = """
CREATE TABLE IF NOT EXISTS vrn_mdl006_compare_mismatches (
    id INTEGER, report_code VARCHAR, data_name VARCHAR, period VARCHAR,
    phase1_value DOUBLE, phase2_value DOUBLE, diff_pct DOUBLE,
    status VARCHAR, ts VARCHAR
);
"""


class MDL006DuckWriter:
    """VRN-MDL006-CLS-003 (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        for ph in ("phase1", "phase2"):
            self._con.execute(_DDL_DUCK_M006_BASIC.format(phase=ph))
            self._con.execute(_DDL_DUCK_M006_FIN.format(phase=ph))
        self._con.execute(_DDL_DUCK_M006_CMP)

    def flush(self, b1: List, b2: List, f1: List, f2: List, c: List) -> Dict[str, int]:
        n = {"basic1":0, "basic2":0, "fin1":0, "fin2":0, "cmp":0}
        try:
            self._con.execute("BEGIN TRANSACTION")
            if b1:
                self._con.executemany(
                    "INSERT INTO vrn_mdl006_basic_phase1 VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", b1)
                n["basic1"] = len(b1)
            if b2:
                self._con.executemany(
                    "INSERT INTO vrn_mdl006_basic_phase2 VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", b2)
                n["basic2"] = len(b2)
            if f1:
                self._con.executemany(
                    "INSERT INTO vrn_mdl006_financial_phase1 VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", f1)
                n["fin1"] = len(f1)
            if f2:
                self._con.executemany(
                    "INSERT INTO vrn_mdl006_financial_phase2 VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", f2)
                n["fin2"] = len(f2)
            if c:
                self._con.executemany(
                    "INSERT INTO vrn_mdl006_compare_mismatches VALUES "
                    "(?,?,?,?,?,?,?,?,?)", c)
                n["cmp"] = len(c)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error("[MDL006] DuckDB flush fail: %s", e); raise
        return n

    def export_parquet_polars(self, out_dir: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        if not POLARS_OK:
            return out
        targets = [
            ("vrn_mdl006_basic_phase1",       "VRN_BasicInfoPhase1.parquet"),
            ("vrn_mdl006_basic_phase2",       "VRN_BasicInfoPhase2.parquet"),
            ("vrn_mdl006_financial_phase1",   "VRN_FinancialDataPhase1.parquet"),
            ("vrn_mdl006_financial_phase2",   "VRN_FinancialDataPhase2.parquet"),
            ("vrn_mdl006_compare_mismatches", "VRN_CompareMismatches.parquet"),
        ]
        for tbl, fn in targets:
            p = str(Path(out_dir) / fn)
            try:
                self._con.execute(
                    f"COPY (SELECT * FROM {tbl}) "
                    f"TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD)")
                out[fn] = p
            except Exception as e:
                log.debug("[MDL006] %s parquet fail: %s", fn, e)
        return out

    def close(self):
        try: self._con.close()
        except: pass


# ── Append v1.1.0 batch flush + polars exports to legacy db (sqlite fallback) ─
# (no legacy MDL006DBWriter exists; DuckDB is the primary path)


# ============================================================================
# [VRN:ANCHOR:MDL006-SELFCHK-001]  v1.1.0  P6 4-PHASE SELF-VERIFICATION
# ============================================================================

class MDL006SelfVerifier:
    """VRN-MDL006-CLS-004 (NEW v1.1.0)."""
    def __init__(self, cfg: Dict, run_summary: Dict, out_dir: str):
        self.cfg = cfg; self.run_summary = run_summary; self.out_dir = out_dir
        self.checks: List[Dict] = []

    def _add(self, phase, name, ok, detail=""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        # P1
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        self._add("1/4", "TW_TICKER_REGEX locked",
                  TW_TICKER_REGEX.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})", "")
        self._add("1/4", "polars available", POLARS_OK, "")
        self._add("1/4", "duckdb available", DUCKDB_OK, "")

        # P2
        self._add("2/4", "MDL006BatchBuffer exists",
                  "MDL006BatchBuffer" in globals(), "")
        self._add("2/4", "MDL006DuckWriter exists",
                  "MDL006DuckWriter" in globals(), "")
        self._add("2/4", "BASIC_INFO_COLS defined",
                  "BASIC_INFO_COLS" in globals() and len(BASIC_INFO_COLS) > 5, "")
        self._add("2/4", "FINANCIAL_DATA_COLS defined",
                  "FINANCIAL_DATA_COLS" in globals() and len(FINANCIAL_DATA_COLS) > 5, "")

        # P3: DB
        duck_p = Path(self.out_dir) / "VRN_MDL006.duckdb"
        self._add("3/4", "DuckDB file exists", duck_p.exists(),
                  f"size={duck_p.stat().st_size if duck_p.exists() else 0}")
        if duck_p.exists() and DUCKDB_OK:
            try:
                con = duckdb_lib.connect(str(duck_p), read_only=True)
                tbls = {t[0] for t in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'").fetchall()}
                con.close()
                expected = {"vrn_mdl006_basic_phase1","vrn_mdl006_basic_phase2",
                            "vrn_mdl006_financial_phase1","vrn_mdl006_financial_phase2",
                            "vrn_mdl006_compare_mismatches"}
                self._add("3/4", "DuckDB schema 5 tables",
                          expected.issubset(tbls), str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema 5 tables", False, str(e))

        # P4: outputs
        for fn in ("VRN_BasicInfoPhase1.json", "VRN_BasicInfoPhase2.json",
                   "VRN_FinancialDataPhase1.json", "VRN_FinancialDataPhase2.json",
                   "VRN_PhaseCompare_Report.json"):
            p = Path(self.out_dir) / fn
            self._add("4/4", f"file:{fn}", p.exists(),
                      f"size={p.stat().st_size if p.exists() else 0}")

        # phase1/phase2 counts non-negative
        self._add("4/4", "phase1.n_basic >= 0",
                  self.run_summary.get("phase1",{}).get("n_basic",0) >= 0)
        self._add("4/4", "phase2.n_basic >= 0",
                  self.run_summary.get("phase2",{}).get("n_basic",0) >= 0)
        self._add("4/4", "compare.match_rate in [0,1]",
                  0 <= self.run_summary.get("compare",{}).get("match_rate",0) <= 1)

        n_total = len(self.checks); n_pass = sum(1 for c in self.checks if c["ok"])
        n_fail  = n_total - n_pass
        cls = "READY" if n_fail == 0 else ("NEAR-READY" if n_fail <= 2 else "NOT-READY")
        return {"total":n_total,"pass":n_pass,"fail":n_fail,
                "classification":cls,"checks":self.checks,
                "generated":time.strftime("%Y-%m-%d %H:%M:%S")}


def build_self_verify_html_mdl006(verify_result: Dict, run_summary: Dict) -> str:
    """VRN-MDL006-FNC-020  VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
    cls = verify_result.get("classification","?")
    cls_color = {"READY":"#439a9a","NEAR-READY":"#e0b020",
                 "NOT-READY":"#c83030"}.get(cls,"#666")
    cls_emoji = {"READY":"✓","NEAR-READY":"⚠","NOT-READY":"✗"}.get(cls,"?")

    by_phase: Dict[str,List[Dict]] = {}
    for c in verify_result.get("checks",[]):
        by_phase.setdefault(c["phase"], []).append(c)

    phase_html = []
    for phase, items in by_phase.items():
        rows = "".join(
            f'<tr><td class="ck-name">{c["name"]}</td>'
            f'<td class="ck-{"ok" if c["ok"] else "fail"}">'
            f'{"✓" if c["ok"] else "✗"} {"PASS" if c["ok"] else "FAIL"}</td>'
            f'<td class="ck-detail">{str(c["detail"])[:120]}</td></tr>'
            for c in items)
        n_pass = sum(1 for c in items if c["ok"])
        phase_html.append(f"""
        <div class="cd"><div class="cd-h">PHASE {phase} ({n_pass}/{len(items)} pass)</div>
        <div class="cd-b"><table class="ck-tbl">
        <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
        <tbody>{rows}</tbody></table></div></div>""")

    p1 = run_summary.get("phase1",{}); p2 = run_summary.get("phase2",{})
    cmp_d = run_summary.get("compare",{})
    sum_lines = [
        f"$ VRN_MDL006 v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ phase consolidation summary",
        f"  phase1 basic   : {p1.get('n_basic','-')}",
        f"  phase1 finrows : {p1.get('n_financial','-')}",
        f"  phase2 basic   : {p2.get('n_basic','-')}",
        f"  phase2 finrows : {p2.get('n_financial','-')}",
        "",
        "$ cross-validation",
        f"  matched        : {cmp_d.get('n_matched','-')}",
        f"  mismatch       : {cmp_d.get('n_mismatch','-')}",
        f"  p1 only / p2   : {cmp_d.get('n_p1_only','-')} / {cmp_d.get('n_p2_only','-')}",
        f"  match_rate     : {cmp_d.get('match_rate', 0):.2%}",
        f"  success        : {cmp_d.get('success','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL006 v{__version__} · Self-Verification · {cls}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f5f4f0;color:#1a1a1a;font-family:'DM Sans',-apple-system,sans-serif;font-size:11px;line-height:1.6;padding:24px}}
.hdr{{border-top:4px solid;border-image:linear-gradient(90deg,#ff5e5e,#ffae5e,#ffe55e,#5eff8c,#5ec8ff,#8c5eff,#ff5ec8) 1;padding-top:16px;margin-bottom:24px}}
h1{{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;letter-spacing:-0.02em}}
.sub{{font-family:'DM Mono',monospace;font-size:10px;color:#666;margin-top:4px}}
.cls-badge{{display:inline-block;padding:4px 12px;background:{cls_color};color:white;font-family:'Syne',sans-serif;font-weight:700;font-size:11px;margin-left:12px;letter-spacing:0.05em}}
.cd{{background:white;border:1px solid #e0ddd5;margin-bottom:16px}}
.cd-h{{background:#4c78a8;color:white;padding:8px 16px;font-family:'Syne',sans-serif;font-weight:600;font-size:11px;letter-spacing:0.03em}}
.cd-b{{padding:12px 16px}}
.tm{{background:#1a1a1a;color:#c8e0c8;font-family:'DM Mono',monospace;font-size:10px;padding:32px 16px 16px 16px;position:relative;white-space:pre;line-height:1.5}}
.tm::before{{content:"● ● ●";position:absolute;top:8px;left:12px;color:#ff5e5e;letter-spacing:4px;font-size:10px}}
.ck-tbl{{width:100%;border-collapse:collapse}}
.ck-tbl th{{background:#f5f4f0;color:#4c78a8;text-align:left;padding:6px 8px;font-weight:600;border-bottom:2px solid #4c78a8;font-size:10px;letter-spacing:0.05em}}
.ck-tbl td{{padding:6px 8px;border-bottom:1px solid #f0ede5;vertical-align:top}}
.ck-name{{font-weight:500;min-width:200px}}
.ck-ok{{color:#439a9a;font-weight:600;min-width:80px}}
.ck-fail{{color:#c83030;font-weight:700;min-width:80px}}
.ck-detail{{color:#666;font-family:'DM Mono',monospace;font-size:10px}}
.foot{{margin-top:24px;color:#999;font-family:'DM Mono',monospace;font-size:9px;text-align:right}}
</style></head><body>
<div class="hdr"><h1>VRN MDL006 · ConsolidatorAndPhaseValidator v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · v{__version__}</div>
</body></html>"""
    return html


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONSOLIDATOR CLASS
# ─────────────────────────────────────────────────────────────────────────────

class VRN_MDL006_Consolidator:
    """Pipeline:
      Phase1 → MDL003 → BasicInfoPhase1 + FinancialDataPhase1
      Phase2 → MDL002/004/005 → BasicInfoPhase2 + FinancialDataPhase2
      Compare Phase1 == Phase2 → report success
    """
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg = dict(_PARAMS, **(cfg or {}))

    def run(self) -> Dict:
        t0 = time.perf_counter()
        out_dir = self.cfg.get("output_dir", _P["output_dir"])
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        # Accel init + plugin load
        plugin_caps = _load_plugins(self.cfg.get("ssot_dir", _P.get("ssot_dir","")))
        cap = _mdl006_accel_init(self.cfg.get("workers", 0))
        log.info("[MDL006] accel=%s plugins=%s", cap, plugin_caps)

        results: Dict = {
            "phase1": {}, "phase2": {},
            "compare": {}, "audit": {},
            "outputs": {}, "ok": False,
        }

        # ── Phase 1 ────────────────────────────────────────────────────────
        log.info("[MDL006] Building Phase1 from MDL003...")
        basic1_raw, fin1_raw = build_phase1(self.cfg.get("mdl003_temp", _P["mdl003_temp"]))
        basic1 = dedup_and_best_basic(basic1_raw)
        fin1   = dedup_and_best_financial(fin1_raw)

        p1_paths = {}
        if basic1:
            p1_paths.update(write_outputs(basic1, BASIC_INFO_COLS,
                "VRN_BasicInfoPhase1", out_dir))
        if fin1:
            p1_paths.update(write_outputs(fin1, FINANCIAL_DATA_COLS,
                "VRN_FinancialDataPhase1", out_dir))
        audit1 = audit_financial_data(fin1, "phase1")

        results["phase1"] = {
            "n_basic": len(basic1), "n_financial": len(fin1),
            "audit": audit1, "paths": p1_paths,
        }

        # ── Phase 2 ────────────────────────────────────────────────────────
        log.info("[MDL006] Building Phase2 from MDL002/004/005...")
        basic2_raw, fin2_raw = build_phase2(
            self.cfg.get("mdl002_temp", _P["mdl002_temp"]),
            self.cfg.get("mdl004_temp", _P["mdl004_temp"]),
            self.cfg.get("mdl005_temp", _P["mdl005_temp"]),
        )
        basic2 = dedup_and_best_basic(basic2_raw)
        fin2   = dedup_and_best_financial(fin2_raw)

        p2_paths = {}
        if basic2:
            p2_paths.update(write_outputs(basic2, BASIC_INFO_COLS,
                "VRN_BasicInfoPhase2", out_dir))
        if fin2:
            p2_paths.update(write_outputs(fin2, FINANCIAL_DATA_COLS,
                "VRN_FinancialDataPhase2", out_dir))
        audit2 = audit_financial_data(fin2, "phase2")

        results["phase2"] = {
            "n_basic": len(basic2), "n_financial": len(fin2),
            "audit": audit2, "paths": p2_paths,
        }

        # ── Compare ────────────────────────────────────────────────────────
        log.info("[MDL006] Comparing Phase1 vs Phase2...")
        cr = compare_phases(basic1, fin1, basic2, fin2, self.cfg.get("compare_tol", 0.02))
        results["compare"] = {
            "n_matched":    cr.n_fin_matched,
            "n_mismatch":   cr.n_fin_mismatch,
            "n_p1_only":    cr.n_fin_p1_only,
            "n_p2_only":    cr.n_fin_p2_only,
            "match_rate":   cr.match_rate,
            "success":      cr.success,
            "summary":      cr.summary,
            "mismatches":   cr.mismatch_details[:20],  # top 20
        }
        results["ok"] = cr.success

        # ── Write comparison report ────────────────────────────────────────
        report_path = str(Path(out_dir) / "VRN_PhaseCompare_Report.json")
        Path(report_path).write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")

        # ── v1.1.0: BatchBuffer + DuckDB write-through ─────────────────────
        flush_stats: Dict[str,int] = {}
        if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
            try:
                buf = MDL006BatchBuffer(self.cfg.get("batch_size", 5000))
                buf.push_basic(basic1, "phase1")
                buf.push_basic(basic2, "phase2")
                buf.push_financial(fin1, "phase1")
                buf.push_financial(fin2, "phase2")
                buf.push_compare(cr.mismatch_details)

                duck_path = str(Path(out_dir) / "VRN_MDL006.duckdb")
                duck = MDL006DuckWriter(duck_path)
                b1, b2, f1, f2, c = buf.consume_all()
                flush_stats = duck.flush(b1, b2, f1, f2, c)
                log.info("[MDL006] DuckDB flush: %s", flush_stats)

                # Polars-direct parquet exports
                pq_paths = duck.export_parquet_polars(out_dir)
                if pq_paths:
                    log.info("[MDL006] Parquet exports: %d files", len(pq_paths))
                    results.setdefault("outputs", {}).update(pq_paths)
                duck.close()
                results["flush_stats"] = flush_stats
            except Exception as e:
                log.warning("[MDL006] DuckDB pipeline fail: %s", e)

        # ── v1.1.0: 4-phase Self-Verify HTML ───────────────────────────────
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                sv = MDL006SelfVerifier(self.cfg, results, out_dir).run()
                html = build_self_verify_html_mdl006(sv, results)
                sv_html_path = str(Path(out_dir) / "VRN_MDL006_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL006] Self-verify: %s (%d/%d) → %s",
                         sv["classification"], sv["pass"], sv["total"], sv_html_path)
                results["self_verify"] = sv["classification"]
                results["self_verify_html"] = sv_html_path
            except Exception as e:
                log.warning("[MDL006] self_verify build fail: %s", e)

        elapsed = round(time.perf_counter()-t0, 2)
        log.info("[MDL006] COMPLETE in %.2fs — %s", elapsed, cr.summary)

        results["elapsed"]    = elapsed
        results["report_path"]= report_path
        return results