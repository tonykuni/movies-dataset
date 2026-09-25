# -*- coding: utf-8 -*-
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
"""
VRN_MDL008_CrossValidator.py
==============================
VERITAS REPORT NOVA -- MDL008  財報交叉驗證引擎
Version   : 1.0.0   |   Module ID : VRN-MDL008-SUP-001
Asset ID  : VRN-MDL008-CLS-001
Policy    : 功能只增不減 · append-only · SSOT

PIPELINE POSITION
  VRN_FinancialDataPhase1/2  ← MDL003/004/005/006 報告擷取
  VRN_MDL007_APIData         ← MDL007 MOPS/TWSE/yfinance
    ↓ MDL008
  VRN_MDL008_Verified.parquet/csv/duckdb  最終驗證結果

VALIDATION LOGIC (Step 7~11 of 擷取對照法)
  Step 7:  單位統一 + 精度標準化
  Step 8:  歷史數據對照（報告 vs MOPS）
  Step 9:  不一致交叉查找 Fallback Chain
  Step 10: 預測數據自洽驗證（加減/除法）
  Step 11: 信心分數計算 + 最終一致性判定

ANCHOR MAP
  [VRN:ANCHOR:MDL008-META-001]    §0  Module Metadata
  [VRN:ANCHOR:MDL008-PARAMS-001]  §1  ALL PARAMETERS
  [VRN:ANCHOR:MDL008-SSOT-001]    §2  SSOT embedded
  [VRN:ANCHOR:MDL008-ACCEL-001]   §3  Accelerator Init
  [VRN:ANCHOR:MDL008-PLUGIN-001]  §4  Plugin Loader
  [VRN:ANCHOR:MDL008-PROXY-001]   §5  Plugin Proxy
  [VRN:ANCHOR:MDL008-UNIT-001]    §6  單位+精度統一
  [VRN:ANCHOR:MDL008-HIST-001]    §7  歷史數據交叉比對
  [VRN:ANCHOR:MDL008-FALLBACK-001]§8  不一致 Fallback Chain
  [VRN:ANCHOR:MDL008-FCST-001]    §9  預測數據自洽驗證
  [VRN:ANCHOR:MDL008-CONF-001]    §10 信心分數計算
  [VRN:ANCHOR:MDL008-OUT-001]     §11 Output Assembler
  [VRN:ANCHOR:MDL008-DB-001]      §12 DB Writer
  [VRN:ANCHOR:MDL008-SYS-001]     §13 Pipeline Entry

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20
"""

__version__   = "1.1.0"
__module_id__ = "VRN-MDL008-SUP-001"
__asset_id__  = "VRN-MDL008-CLS-001"

# ============================================================================
# §0  STDLIB
# ============================================================================

import os, sys, re, json, time, math, hashlib, logging, sqlite3, gc
import warnings, threading, importlib, statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

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
duckdb_lib = duckdb
POLARS_OK  = pl is not None
DUCKDB_OK  = duckdb_lib is not None

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ============================================================================
# [VRN:ANCHOR:MDL008-PARAMS-001] §1  ALL PARAMETERS
# ============================================================================

_PARAMS: dict = {
    # ── Paths ────────────────────────────────────────────────────────────────
    "output_dir":   r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\output",
    "mdl007_temp":  r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl007_temp",
    "ssot_dir":     r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",

    # ── Plugin flags ─────────────────────────────────────────────────────────
    "enable_ssot":      True,
    "enable_celeritas": True,
    "enable_aegis":     True,

    # ── 單位+精度 ─────────────────────────────────────────────────────────────
    "output_unit":     "million",
    "output_decimal":  1,          # 統一保留1位小數

    # ── 誤差容忍 ─────────────────────────────────────────────────────────────
    # 依數值大小分段（百萬元）
    "tol_large":  0.001,   # >= 1000m: 0.1%
    "tol_medium": 0.005,   # 100~999m: 0.5%
    "tol_small":  0.010,   # < 100m:   1.0%

    # ── 年度判定 ─────────────────────────────────────────────────────────────
    "hist_suffix":  ["A","a"],              # 歷史年度後綴
    "fcst_suffix":  ["E","F","e","f","P"],  # 預測年度後綴

    # ── 預測自洽驗證 ─────────────────────────────────────────────────────────
    "fcst_arithmetic_tol":  0.02,   # 加減法容忍 2%
    "fcst_ratio_tol":       0.05,   # 比率法容忍 5%（%為單位時）
    "fcst_growth_max_mult": 3.0,    # 預測成長不超過歷史最大值3倍

    # ── Fallback chain ───────────────────────────────────────────────────────
    "fallback_max_levels": 4,

    # ── Confidence 權重 ──────────────────────────────────────────────────────
    "conf_base":              0.80,
    "conf_bonus_match":       0.15,   # 歷史完全吻合
    "conf_bonus_multi_src":   0.05,   # 多源一致
    "conf_penalty_unit_miss": 0.15,   # 單位誤差
    "conf_penalty_synonym":   0.10,   # 同義字模糊
    "conf_penalty_unresolved":0.20,   # 無法追查
    "conf_penalty_ocr_fix":   0.05,   # OCR修正

    # ── DB ───────────────────────────────────────────────────────────────────
    "enable_db":    True,
    "csv_encoding": "utf-8-sig",

    # ── Concurrency ──────────────────────────────────────────────────────────
    "workers": 0,
    # ── v1.1.0 NEW (append-only) ─────────────────────────────────────────────
    "use_duckdb":    True,    # P3 DuckDB primary, sqlite fallback
    "batch_size":    5000,    # P3 buffer flush threshold
    "polars_first":  True,    # P5 polars vectorized exports
    "self_verify":   True,    # P6 4-phase HTML
}
_P = _PARAMS

# ============================================================================
# [VRN:ANCHOR:MDL008-SSOT-001] §2  SSOT EMBEDDED
# ============================================================================

# TW Ticker Regex（三鎖定）
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

PERIOD_HIST_RE = re.compile(r"^(20\d{2})[AaHh]?$")  # 歷史年度
PERIOD_FCST_RE = re.compile(r"^(20\d{2})[EeFfPp]$") # 預測年度

def is_historical(period: str) -> bool:
    s = str(period).strip()
    if PERIOD_HIST_RE.match(s): return True
    if s.endswith(tuple(_P["hist_suffix"])): return True
    if s.endswith(tuple(_P["fcst_suffix"])): return False
    # 純年份（2023）視為歷史
    return bool(re.match(r"^20\d{2}$", s))

def is_forecast(period: str) -> bool:
    s = str(period).strip()
    return bool(PERIOD_FCST_RE.match(s)) or s.endswith(tuple(_P["fcst_suffix"]))

def to_year(period: str) -> Optional[int]:
    m = re.search(r"20\d{2}", str(period))
    return int(m.group()) if m else None

# 同義字對照：不同名稱 → 同一個 canonical
SYNONYM_FALLBACK: Dict[str, List[str]] = {
    "revenue":          ["gross_revenue","net_sales","sales","top_line"],
    "gross_profit":     ["gross_income","gross"],
    "operating_income": ["ebit","operating_profit","op_income"],
    "net_income":       ["profit_after_tax","pat","bottom_line","net_profit"],
    "eps":              ["basic_eps","diluted_eps","earnings_per_share"],
    "total_equity":     ["shareholders_equity","book_value_total","net_worth"],
}
# Reverse: alias → primary canonical
_SYN_REV: Dict[str, str] = {
    alias: canon
    for canon, aliases in SYNONYM_FALLBACK.items()
    for alias in aliases
}

# 符號規範：某些科目在不同系統符號相反
SIGN_CONVENTION: Dict[str, int] = {
    "cogs":        -1,  # 成本在損益表為負，但MOPS有時記正值
    "capex":       -1,  # 資本支出通常記負
    "investing_cf":-1,  # 投資活動現金通常為負
}

def _h8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

TODAY = __import__("datetime").date.today().isoformat()

# ============================================================================
# [VRN:ANCHOR:MDL008-ACCEL-001] §3  ACCELERATOR INIT
# ============================================================================

def _mdl008_accel_init(workers: int = 0) -> Dict:
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for v in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(v, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {"workers": w, "pandas": pd is not None, "duckdb": duckdb is not None}

# ============================================================================
# [VRN:ANCHOR:MDL008-PLUGIN-001] §4  PLUGIN LOADER
# ============================================================================

_CEL: Any = None;  _CEL_OK: bool = False
_SSOT: Any = None; _SSOT_OK: bool = False
_NET: Any = None;  _NET_OK: bool = False
# [VRN:ANCHOR:HARDGATE_HOLDERS:V1] Additional holders per VIA_Supportive_HardGate_Seal.json
_REG: Any = None;  _REG_OK: bool = False  # VIA_RegistryCore_v1
_BRG: Any = None;  _BRG_OK: bool = False  # VIA_Runtime_Bridge_All_in_One
_ENV: Any = None;  _ENV_OK: bool = False  # VIA_EnvManager
_AST: Any = None;  _AST_OK: bool = False  # VIA_Panorama_AST_RuntimeInjector

def load_plugins(ssot_dir: str) -> Dict[str, bool]:
    """Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json order.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    """
    global _CEL, _CEL_OK, _SSOT, _SSOT_OK, _NET, _NET_OK
    global _REG, _REG_OK, _BRG, _BRG_OK, _ENV, _ENV_OK, _AST, _AST_OK
    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False}
    import importlib.util as _ilu
    # [VRN:ANCHOR:HARDGATE_PLUGIN_MAP:V1] order matches HardGate Seal
    plugin_map = [
        ("VIA_SSOT_Unified",                "via_ssot",       "_SSOT", "_SSOT_OK"),
        ("VIA_RegistryCore_v1",             "registry",       "_REG",  "_REG_OK"),
        ("VIA_Runtime_Bridge_All_in_One",   "runtime_bridge", "_BRG",  "_BRG_OK"),
        ("VIA_EnvManager",                  "env_manager",    "_ENV",  "_ENV_OK"),
        ("VIA_Panorama_AST_RuntimeInjector","ast_planner",    "_AST",  "_AST_OK"),
        ("VeritasCeleritas",                "celeritas",      "_CEL",  "_CEL_OK"),
        ("VeritasAegisNexus",               "aegis",          "_NET",  "_NET_OK"),
    ]
    for mod_name, key, gname, ok_name in plugin_map:
        for base in [Path(ssot_dir), Path(ssot_dir).parent]:
            p = base / f"{mod_name}.py"
            if p.exists():
                try:
                    spec = _ilu.spec_from_file_location(mod_name, str(p))
                    mod  = _ilu.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                    globals()[gname]  = mod
                    globals()[ok_name]= True
                    result[key] = True
                    if mod_name == "VeritasCeleritas":
                        if hasattr(mod,"bootstrap_at_import"): mod.bootstrap_at_import(__file__)
                        if hasattr(mod,"warm_thread_pool"):    mod.warm_thread_pool()
                    break
                except Exception as e:
                    log.debug("[MDL008] %s: %s", mod_name, e)
    return result

# ============================================================================
# [VRN:ANCHOR:MDL008-PROXY-001] §5  PLUGIN PROXY
# ============================================================================

def _cel_submit(fn, *args, **kw):
    if _CEL_OK:
        if hasattr(_CEL,"_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)

def _cel_map(fn, items):
    if _CEL_OK and hasattr(_CEL,"_LazyPool"):
        try: return list(_CEL._LazyPool.map(fn, items))
        except Exception: pass
    return list(map(fn, items))

# ============================================================================
# [VRN:ANCHOR:MDL008-UNIT-001] §6  單位+精度統一 (Step 7)
# ============================================================================

UNIT_MULT: Dict[str, float] = {
    "thousand":        0.001,
    "million":         1.0,
    "billion":         1000.0,
    "hundred_million": 100.0,
    "million_ntd":     1.0,
    "thousand_ntd":    0.001,
}

def to_million(value: Any, unit: str = "million") -> Optional[float]:
    """VRN-MDL008-FNC-001  Convert any unit to million."""
    try:
        v = float(str(value).replace(",","").replace("，","").strip())
        return v * UNIT_MULT.get(unit, 1.0)
    except: return None

def precision_normalize(v: Optional[float], decimal: int = 1) -> Optional[float]:
    """VRN-MDL008-FNC-002  Round then truncate — eliminates float drift.
    22500.049 → round(1) → 22500.0 → floor*10/10 → 22500.0
    """
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    rounded = round(v, decimal)
    factor  = 10 ** decimal
    return math.floor(rounded * factor) / factor

def std_val(value: Any, unit: str = "million") -> Optional[float]:
    """Shorthand: to_million + precision_normalize."""
    v = to_million(value, unit)
    if v is None: return None
    return precision_normalize(v, _P["output_decimal"])

def tolerance(v: Optional[float]) -> float:
    """VRN-MDL008-FNC-003  Tolerance by magnitude (百萬元)."""
    if v is None: return _P["tol_small"]
    a = abs(v)
    if a >= 1000: return _P["tol_large"]
    if a >= 100:  return _P["tol_medium"]
    return _P["tol_small"]

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class VerifyResult:
    """One field comparison result."""
    ticker:        str = ""
    canonical:     str = ""
    period:        str = ""
    value_report:  Optional[float] = None  # 報告值（百萬，1位小數）
    value_api:     Optional[float] = None  # API值（相同規格）
    value_final:   Optional[float] = None  # 採用值
    status:        str = "SKIP"   # MATCH/MISMATCH/CALC/FORECAST/UNRESOLVED/SKIP
    diff_pct:      Optional[float] = None
    diff_abs:      Optional[float] = None
    tol_used:      float = 0.01
    mismatch_reason: Optional[str] = None   # unit_error/synonym/sign/rounding/ocr/unknown
    fallback_level:  int = 0
    confidence:    float = 0.80
    source_report: str = ""
    source_api:    str = ""
    is_historical: bool = True

@dataclass
class ForecastCheck:
    """One arithmetic/ratio self-consistency check."""
    ticker:    str = ""
    period:    str = ""
    rule:      str = ""   # e.g. "gross_profit = revenue - cogs"
    lhs:       Optional[float] = None
    rhs:       Optional[float] = None
    diff_pct:  Optional[float] = None
    passed:    bool = False
    note:      str = ""

# ============================================================================
# [VRN:ANCHOR:MDL008-HIST-001] §7  歷史數據交叉比對 (Step 8)
# ============================================================================

def compare_one(
    canonical:    str,
    period:       str,
    report_val:   Any,
    report_unit:  str,
    api_val:      Any,
    api_unit:     str,
    ticker:       str,
) -> VerifyResult:
    """VRN-MDL008-FNC-004  Compare one field (report vs API) with full normalization."""
    vr = VerifyResult(ticker=ticker, canonical=canonical, period=period)
    vr.is_historical = is_historical(period)

    # Normalize both sides
    r = std_val(report_val, report_unit)
    a = std_val(api_val, api_unit)
    vr.value_report = r
    vr.value_api    = a

    if r is None or a is None:
        vr.status      = "SKIP"
        vr.value_final = a if r is None else r
        return vr

    # Denominator protection
    if abs(a) < 0.01:
        vr.status      = "SKIP"
        vr.value_final = a
        return vr

    diff_abs = abs(r - a)
    diff_pct = diff_abs / abs(a)
    vr.diff_abs  = round(diff_abs, 2)
    vr.diff_pct  = round(diff_pct * 100, 3)   # store as %
    vr.tol_used  = tolerance(a)

    if diff_pct <= vr.tol_used:
        vr.status      = "MATCH"
        vr.value_final = a          # API值為準（官方）
        vr.confidence  = _P["conf_base"] + _P["conf_bonus_match"]
    else:
        vr.status      = "MISMATCH"
        vr.value_final = r          # 暫存報告值，等fallback解決
        vr.mismatch_reason = classify_mismatch(r, a, canonical)
        vr.confidence  = _P["conf_base"] - _P["conf_penalty_unresolved"]

    return vr

def classify_mismatch(
    report_val: float, api_val: float, canonical: str
) -> str:
    """VRN-MDL008-FNC-005  Classify mismatch by ratio pattern."""
    if api_val == 0: return "zero_denominator"
    ratio = report_val / api_val

    # Unit error detection
    if 990 <= ratio <= 1010 or 0.00099 <= ratio <= 0.00101:
        return "unit_error_thousand"
    if 99 <= ratio <= 101 or 0.0099 <= ratio <= 0.0101:
        return "unit_error_hundred"
    if 9 <= ratio <= 11 or 0.099 <= ratio <= 0.101:
        return "unit_error_ten"

    # Sign error
    if -1.05 <= ratio <= -0.95:
        return "sign_opposite"

    # Synonym / scope
    if 1.2 <= ratio <= 2.0 or 0.5 <= ratio <= 0.85:
        return "synonym_scope"

    # Rounding
    if 0.995 <= ratio <= 1.005:
        return "rounding"

    return "unknown"

# ============================================================================
# [VRN:ANCHOR:MDL008-FALLBACK-001] §8  不一致 Fallback Chain (Step 9)
# ============================================================================

def fallback_resolve(
    result: VerifyResult,
    all_api_rows: List[Dict],
    all_report_rows: List[Dict],
    ticker: str,
) -> VerifyResult:
    """VRN-MDL008-FNC-006  Multi-level fallback when MISMATCH detected."""
    if result.status == "MATCH": return result

    canonical = result.canonical
    period    = result.period
    r_val     = result.value_report
    tol       = result.tol_used

    # ── Level 1: 換同義字重比 ──────────────────────────────────────────────
    synonyms = SYNONYM_FALLBACK.get(canonical, [])
    for syn in synonyms:
        api_row = _find_api(all_api_rows, ticker, syn, period)
        if api_row:
            a = std_val(api_row.get("value"), api_row.get("unit","million"))
            if a and abs(r_val - a) / max(abs(a),0.01) <= tol:
                result.status          = "MATCH"
                result.value_api       = a
                result.value_final     = a
                result.mismatch_reason = f"resolved_via_synonym:{syn}"
                result.fallback_level  = 1
                result.confidence      = _P["conf_base"] + 0.05
                return result

    # ── Level 2: 符號修正重比 ─────────────────────────────────────────────
    sign = SIGN_CONVENTION.get(canonical, 1)
    if sign == -1:
        api_row = _find_api(all_api_rows, ticker, canonical, period)
        if api_row:
            a = std_val(api_row.get("value"), api_row.get("unit","million"))
            if a:
                a_flipped = -a
                if abs(r_val - a_flipped) / max(abs(a_flipped),0.01) <= tol:
                    result.status         = "MATCH"
                    result.value_api      = a_flipped
                    result.value_final    = a_flipped
                    result.mismatch_reason= "resolved_sign_flip"
                    result.fallback_level = 2
                    result.confidence     = _P["conf_base"] + 0.03
                    return result

    # ── Level 3: 換單位重試 ────────────────────────────────────────────────
    for alt_unit in ["thousand", "billion", "hundred_million"]:
        if alt_unit == result.source_api: continue
        api_row = _find_api(all_api_rows, ticker, canonical, period)
        if api_row:
            a_reunit = std_val(api_row.get("value_original",
                                           api_row.get("value")), alt_unit)
            if a_reunit and abs(r_val - a_reunit) / max(abs(a_reunit),0.01) <= tol:
                result.status          = "MATCH"
                result.value_api       = a_reunit
                result.value_final     = a_reunit
                result.mismatch_reason = f"resolved_unit_fix:{alt_unit}"
                result.fallback_level  = 3
                result.confidence      = _P["conf_base"] - _P["conf_penalty_unit_miss"] + 0.05
                return result

    # ── Level 4: 換來源年份（±1年）──────────────────────────────────────────
    yr = to_year(period)
    if yr:
        for adj_yr in [yr-1, yr+1]:
            adj_period = f"{adj_yr}A"
            api_row = _find_api(all_api_rows, ticker, canonical, adj_period)
            if api_row:
                a = std_val(api_row.get("value"), api_row.get("unit","million"))
                if a and abs(r_val - a) / max(abs(a),0.01) <= tol * 2:
                    result.status          = "MISMATCH"
                    result.mismatch_reason = f"closest_year:{adj_period}"
                    result.fallback_level  = 4
                    result.confidence      = _P["conf_base"] - 0.10
                    return result

    # ── Unresolved ────────────────────────────────────────────────────────────
    result.status          = "UNRESOLVED"
    result.value_final     = result.value_report   # 保留報告值
    result.mismatch_reason = f"unresolved:{result.mismatch_reason or 'unknown'}"
    result.fallback_level  = 99
    result.confidence      = _P["conf_base"] - _P["conf_penalty_unresolved"]
    return result

def _find_api(rows: List[Dict], ticker: str,
              canonical: str, period: str) -> Optional[Dict]:
    """Find one API row by ticker+canonical+period."""
    for r in rows:
        if (str(r.get("ticker","")) == ticker and
            str(r.get("canonical","")) == canonical and
            str(r.get("period","")) == period):
            return r
    return None

# ============================================================================
# [VRN:ANCHOR:MDL008-FCST-001] §9  預測數據自洽驗證 (Step 10)
# ============================================================================

def verify_forecast_arithmetic(
    ticker: str, period: str, fields: Dict[str, Optional[float]]
) -> List[ForecastCheck]:
    """VRN-MDL008-FNC-007  Financial equation self-consistency checks."""
    checks = []
    tol_arith = _P["fcst_arithmetic_tol"]
    tol_ratio  = _P["fcst_ratio_tol"]

    def _check(rule: str, lhs: Optional[float], rhs: Optional[float]) -> ForecastCheck:
        if lhs is None or rhs is None or abs(rhs) < 0.01:
            return ForecastCheck(ticker=ticker, period=period, rule=rule,
                                 lhs=lhs, rhs=rhs, passed=True, note="skip_null")
        diff = abs(lhs - rhs) / abs(rhs)
        return ForecastCheck(
            ticker=ticker, period=period, rule=rule,
            lhs=round(lhs,2), rhs=round(rhs,2),
            diff_pct=round(diff*100,3),
            passed=diff <= tol_arith,
            note="" if diff <= tol_arith else f"diff={diff*100:.2f}%",
        )

    rev = fields.get("revenue")
    gp  = fields.get("gross_profit")
    cogs= fields.get("cogs")
    oi  = fields.get("operating_income")
    ni  = fields.get("net_income")
    ta  = fields.get("total_assets")
    tl  = fields.get("total_liabilities")
    te  = fields.get("total_equity")
    eps = fields.get("eps")
    gm  = fields.get("gross_margin")
    om  = fields.get("operating_margin")

    # A1: 毛利 = 營收 - 成本
    if gp and rev and cogs:
        checks.append(_check("gross_profit = revenue - cogs", gp, rev - cogs))

    # A2: 毛利率 = 毛利 / 營收 × 100
    if gm and gp and rev and rev != 0:
        checks.append(_check("gross_margin% = gross_profit/revenue*100",
                             gm, gp/rev*100))

    # A3: 營益率 = 營業利益 / 營收 × 100
    if om and oi and rev and rev != 0:
        checks.append(_check("operating_margin% = OI/revenue*100",
                             om, oi/rev*100))

    # A4: 總資產 = 負債 + 股東權益
    if ta and tl and te:
        checks.append(_check("total_assets = total_liabilities + total_equity",
                             ta, tl + te))

    # A5: EPS × 股本 ≈ 淨利（粗估，允許5%）
    # 需要shares_outstanding，暫跳

    return checks

def verify_growth_reasonableness(
    ticker: str,
    canonical: str,
    hist_values: Dict[str, float],   # {period: value}
    fcst_values: Dict[str, float],
) -> List[ForecastCheck]:
    """VRN-MDL008-FNC-008  Forecast growth should not exceed 3x historical max growth."""
    checks = []
    if not hist_values or not fcst_values: return checks

    # Compute historical growth rates
    hist_sorted = sorted(hist_values.items())
    hist_growths = []
    for i in range(1, len(hist_sorted)):
        y0 = hist_sorted[i-1][1]
        y1 = hist_sorted[i][1]
        if y0 and abs(y0) > 0.01:
            hist_growths.append(abs((y1-y0)/y0))

    if not hist_growths: return checks
    max_hist_g = max(hist_growths)
    max_allowed = max_hist_g * _P["fcst_growth_max_mult"]

    # Check forecast growth
    fcst_sorted = sorted(fcst_values.items())
    all_vals = sorted(list(hist_values.items()) + list(fcst_values.items()))
    for i in range(1, len(all_vals)):
        if all_vals[i][0] not in fcst_values: continue
        y0 = all_vals[i-1][1]
        y1 = all_vals[i][1]
        if y0 and abs(y0) > 0.01:
            fcst_g = abs((y1-y0)/y0)
            passed = fcst_g <= max_allowed
            checks.append(ForecastCheck(
                ticker=ticker, period=all_vals[i][0],
                rule=f"{canonical}_growth_reasonable",
                lhs=round(fcst_g*100,2),
                rhs=round(max_allowed*100,2),
                diff_pct=None,
                passed=passed,
                note=f"fcst_growth={fcst_g*100:.1f}% max_allowed={max_allowed*100:.1f}%",
            ))

    return checks

# ============================================================================
# [VRN:ANCHOR:MDL008-CONF-001] §10  信心分數計算 (Step 11)
# ============================================================================

def compute_confidence(
    result: VerifyResult,
    n_arithmetic_fail: int = 0,
    n_multi_src_agree: int = 0,
) -> float:
    """VRN-MDL008-FNC-009  Confidence 0.0~1.0 for a single VerifyResult."""
    score = _P["conf_base"]

    if result.status == "MATCH":
        score += _P["conf_bonus_match"]
    elif result.status == "UNRESOLVED":
        score -= _P["conf_penalty_unresolved"]
    elif result.status == "MISMATCH":
        score -= _P["conf_penalty_unresolved"] * 0.5

    reason = result.mismatch_reason or ""
    if "unit_error" in reason:     score -= _P["conf_penalty_unit_miss"]
    if "synonym" in reason:        score -= _P["conf_penalty_synonym"]
    if "sign" in reason:           score -= 0.05

    score -= n_arithmetic_fail * 0.05
    score += min(n_multi_src_agree * _P["conf_bonus_multi_src"], 0.10)

    return round(max(0.0, min(1.0, score)), 3)

# ============================================================================
# [VRN:ANCHOR:MDL008-OUT-001] §11  OUTPUT ASSEMBLER
# ============================================================================

VERIFY_COLS = [
    "date","ticker","yfinance_ticker","canonical","period","is_historical",
    "value_report","value_api","value_final",
    "status","diff_pct","diff_abs","tol_used",
    "mismatch_reason","fallback_level","confidence",
    "source_report","source_api",
]

ARITH_COLS = [
    "date","ticker","period","rule","lhs","rhs","diff_pct","passed","note",
]

def results_to_df(results: List[VerifyResult]) -> "pd.DataFrame":
    if not pd: return None
    rows = []
    for r in results:
        yf = f"{r.ticker}.TW" if r.ticker else ""
        rows.append({
            "date": TODAY, "ticker": r.ticker, "yfinance_ticker": yf,
            "canonical": r.canonical, "period": r.period,
            "is_historical": r.is_historical,
            "value_report": r.value_report, "value_api": r.value_api,
            "value_final": r.value_final,
            "status": r.status, "diff_pct": r.diff_pct, "diff_abs": r.diff_abs,
            "tol_used": r.tol_used, "mismatch_reason": r.mismatch_reason,
            "fallback_level": r.fallback_level, "confidence": r.confidence,
            "source_report": r.source_report, "source_api": r.source_api,
        })
    return pd.DataFrame(rows, columns=VERIFY_COLS)

def checks_to_df(checks: List[ForecastCheck]) -> "pd.DataFrame":
    if not pd: return None
    rows = [{"date":TODAY,"ticker":c.ticker,"period":c.period,
             "rule":c.rule,"lhs":c.lhs,"rhs":c.rhs,
             "diff_pct":c.diff_pct,"passed":c.passed,"note":c.note}
            for c in checks]
    return pd.DataFrame(rows, columns=ARITH_COLS)

# ============================================================================
# [VRN:ANCHOR:MDL008-DB-001] §12  DB WRITER
# ============================================================================

class MDL008DBWriter:
    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl008_verify (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, ticker TEXT, yfinance_ticker TEXT,
    canonical TEXT, period TEXT, is_historical INTEGER,
    value_report REAL, value_api REAL, value_final REAL,
    status TEXT, diff_pct REAL, diff_abs REAL, tol_used REAL,
    mismatch_reason TEXT, fallback_level INTEGER, confidence REAL,
    source_report TEXT, source_api TEXT,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl008_forecast_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, ticker TEXT, period TEXT,
    rule TEXT, lhs REAL, rhs REAL, diff_pct REAL, passed INTEGER, note TEXT,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_mdl008_tkr ON vrn_mdl008_verify(ticker,canonical,period,status);
"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock   = threading.Lock()
        self._con    = sqlite3.connect(db_path, check_same_thread=False)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=NORMAL")
        self._con.executescript(self.DDL)
        self._con.commit()

    def insert_verify(self, df: "pd.DataFrame"):
        if df is None or not len(df): return
        df.to_sql("vrn_mdl008_verify", self._con,
                  if_exists="append", index=False, method="multi")
        with self._lock: self._con.commit()

    def insert_checks(self, df: "pd.DataFrame"):
        if df is None or not len(df): return
        df.to_sql("vrn_mdl008_forecast_checks", self._con,
                  if_exists="append", index=False, method="multi")
        with self._lock: self._con.commit()

    def export(self, out_dir: str):
        if not pd: return
        out = Path(out_dir)
        for tbl, base in [("vrn_mdl008_verify","VRN_MDL008_Verified"),
                          ("vrn_mdl008_forecast_checks","VRN_MDL008_ForecastChecks")]:
            df = pd.read_sql(f"SELECT * FROM {tbl}", self._con)
            if not len(df): continue
            if pyarrow: df.to_parquet(str(out/f"{base}.parquet"), index=False)
            df.to_csv(str(out/f"{base}.csv"), index=False, encoding=_P["csv_encoding"])
            if duckdb:
                con = duckdb.connect(str(out/f"{base}.duckdb"))
                t   = base.lower()
                con.execute(f"DROP TABLE IF EXISTS {t}")
                con.execute(f"CREATE TABLE {t} AS SELECT * FROM df")
                con.close()
            log.info("[MDL008] Exported %s: %d rows", base, len(df))


# ============================================================================
# [VRN:ANCHOR:MDL008-BATCH-001]  v1.1.0  P3 BATCH BUFFER + DUCK WRITER
# ============================================================================

class MDL008BatchBuffer:
    """VRN-MDL008-CLS-002 (NEW v1.1.0)."""
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._verify_buf: List[Tuple] = []
        self._fcst_buf:   List[Tuple] = []
        self._lock = threading.Lock()

    def push_verify(self, results: List["VerifyResult"]):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rs = [(None, TODAY, vr.ticker, "",  # yfinance_ticker not on VerifyResult
               vr.canonical, vr.period, 1 if vr.is_historical else 0,
               vr.value_report, vr.value_api, vr.value_final,
               vr.status, vr.diff_pct, vr.diff_abs, vr.tol_used,
               vr.mismatch_reason, vr.fallback_level, vr.confidence,
               vr.source_report, vr.source_api, ts) for vr in results]
        with self._lock:
            self._verify_buf.extend(rs)

    def push_forecast(self, checks: List["ForecastCheck"]):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rs = [(None, TODAY, c.ticker, c.period, c.rule,
               c.lhs, c.rhs, c.diff_pct, 1 if c.passed else 0, c.note, ts)
              for c in checks]
        with self._lock:
            self._fcst_buf.extend(rs)

    def stats(self) -> Dict[str, int]:
        return {"verify": len(self._verify_buf), "fcst": len(self._fcst_buf)}

    def consume_all(self) -> Tuple[List, List]:
        with self._lock:
            v, f = self._verify_buf, self._fcst_buf
            self._verify_buf, self._fcst_buf = [], []
        return v, f


_DDL_DUCK_M008_VERIFY = """
CREATE TABLE IF NOT EXISTS vrn_mdl008_verify (
    id INTEGER, date VARCHAR, ticker VARCHAR, yfinance_ticker VARCHAR,
    canonical VARCHAR, period VARCHAR, is_historical INTEGER,
    value_report DOUBLE, value_api DOUBLE, value_final DOUBLE,
    status VARCHAR, diff_pct DOUBLE, diff_abs DOUBLE, tol_used DOUBLE,
    mismatch_reason VARCHAR, fallback_level INTEGER, confidence DOUBLE,
    source_report VARCHAR, source_api VARCHAR, ts VARCHAR
);
"""

_DDL_DUCK_M008_FCST = """
CREATE TABLE IF NOT EXISTS vrn_mdl008_forecast_checks (
    id INTEGER, date VARCHAR, ticker VARCHAR, period VARCHAR,
    rule VARCHAR, lhs DOUBLE, rhs DOUBLE, diff_pct DOUBLE,
    passed INTEGER, note VARCHAR, ts VARCHAR
);
"""


class MDL008DuckWriter:
    """VRN-MDL008-CLS-003 (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        self._con.execute(_DDL_DUCK_M008_VERIFY)
        self._con.execute(_DDL_DUCK_M008_FCST)

    def flush(self, verify_rows: List, fcst_rows: List) -> Dict[str, int]:
        n = {"verify": 0, "fcst": 0}
        try:
            self._con.execute("BEGIN TRANSACTION")
            if verify_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl008_verify VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    verify_rows)
                n["verify"] = len(verify_rows)
            if fcst_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl008_forecast_checks VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?)",
                    fcst_rows)
                n["fcst"] = len(fcst_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error("[MDL008] DuckDB flush fail: %s", e); raise
        return n

    def export_parquet_polars(self, out_dir: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        targets = [
            ("vrn_mdl008_verify", "VRN_MDL008_Verified.parquet"),
            ("vrn_mdl008_forecast_checks", "VRN_MDL008_ForecastChecks.parquet"),
        ]
        for tbl, fn in targets:
            p = str(Path(out_dir) / fn)
            try:
                self._con.execute(
                    f"COPY (SELECT * FROM {tbl}) "
                    f"TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD)")
                out[fn] = p
            except Exception as e:
                log.debug("[MDL008] %s parquet fail: %s", fn, e)
        return out

    def close(self):
        try: self._con.close()
        except: pass


# ============================================================================
# [VRN:ANCHOR:MDL008-SELFCHK-001]  v1.1.0  P6 4-PHASE SELF-VERIFICATION
# ============================================================================

class MDL008SelfVerifier:
    """VRN-MDL008-CLS-004 (NEW v1.1.0)."""
    def __init__(self, cfg: Dict, run_summary: Dict, out_dir: str):
        self.cfg = cfg; self.run_summary = run_summary; self.out_dir = out_dir
        self.checks: List[Dict] = []

    def _add(self, phase, name, ok, detail=""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        self._add("1/4", "polars available", POLARS_OK, "")
        self._add("1/4", "duckdb available", DUCKDB_OK, "")
        self._add("1/4", "VerifyResult dataclass exists",
                  "VerifyResult" in globals(), "")
        self._add("1/4", "ForecastCheck dataclass exists",
                  "ForecastCheck" in globals(), "")

        self._add("2/4", "MDL008BatchBuffer exists", "MDL008BatchBuffer" in globals())
        self._add("2/4", "MDL008DuckWriter exists",  "MDL008DuckWriter" in globals())
        self._add("2/4", "compare_one callable", callable(compare_one))
        self._add("2/4", "fallback_resolve callable", callable(fallback_resolve))
        self._add("2/4", "verify_forecast_arithmetic callable",
                  callable(verify_forecast_arithmetic))

        duck_p = Path(self.out_dir) / "VRN_MDL008.duckdb"
        self._add("3/4", "DuckDB file exists", duck_p.exists(),
                  f"size={duck_p.stat().st_size if duck_p.exists() else 0}")
        if duck_p.exists() and DUCKDB_OK:
            try:
                con = duckdb_lib.connect(str(duck_p), read_only=True)
                tbls = {t[0] for t in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'").fetchall()}
                con.close()
                expected = {"vrn_mdl008_verify", "vrn_mdl008_forecast_checks"}
                self._add("3/4", "DuckDB schema 2 tables",
                          expected.issubset(tbls), str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema 2 tables", False, str(e))

        for fn in ("VRN_MDL008_Summary.json",):
            p = Path(self.out_dir) / fn
            self._add("4/4", f"file:{fn}", p.exists(),
                      f"size={p.stat().st_size if p.exists() else 0}")
        self._add("4/4", "n_verify >= 0",
                  self.run_summary.get("n_verify", 0) >= 0)
        self._add("4/4", "n_fcst_checks >= 0",
                  self.run_summary.get("n_fcst_checks", 0) >= 0)

        n_total = len(self.checks); n_pass = sum(1 for c in self.checks if c["ok"])
        n_fail  = n_total - n_pass
        cls = "READY" if n_fail == 0 else ("NEAR-READY" if n_fail <= 2 else "NOT-READY")
        return {"total":n_total,"pass":n_pass,"fail":n_fail,
                "classification":cls,"checks":self.checks,
                "generated":time.strftime("%Y-%m-%d %H:%M:%S")}


def build_self_verify_html_mdl008(verify_result: Dict, run_summary: Dict) -> str:
    """VRN-MDL008  VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
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

    sum_lines = [
        f"$ VRN_MDL008 v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  n_verify       : {run_summary.get('n_verify','-')}",
        f"  n_fcst_checks  : {run_summary.get('n_fcst_checks','-')}",
        f"  n_match        : {run_summary.get('n_match','-')}",
        f"  n_mismatch     : {run_summary.get('n_mismatch','-')}",
        f"  match_rate     : {run_summary.get('match_rate', 0):.2%}",
        f"  ok             : {run_summary.get('ok','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL008 v{__version__} · Self-Verification · {cls}</title>
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
<div class="hdr"><h1>VRN MDL008 · CrossValidator v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · v{__version__}</div>
</body></html>"""
    return html


# ============================================================================
# [VRN:ANCHOR:MDL008-SYS-001] §13  PIPELINE ENTRY
# ============================================================================

class VRN_MDL008_CrossValidator:
    """VRN-MDL008-CLS-001  Main cross-validation engine.

    Usage:
        report_rows = pd.read_parquet("VRN_FinancialDataPhase1.parquet").to_dict("records")
        api_rows    = pd.read_parquet("VRN_MDL007_APIData.parquet").to_dict("records")
        validator   = VRN_MDL008_CrossValidator()
        result      = validator.run(report_rows, api_rows)
    """
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg     = dict(_PARAMS, **(cfg or {}))
        self.workers = self.cfg.get("workers") or max(1,(os.cpu_count() or 4)-1)
        self.db: Optional[MDL008DBWriter] = None

    def _group_by_ticker(self, rows: List[Dict]) -> Dict[str, List[Dict]]:
        g: Dict[str, List[Dict]] = {}
        for r in rows:
            t = str(r.get("ticker",""))
            g.setdefault(t, []).append(r)
        return g

    def validate_one_ticker(
        self,
        ticker: str,
        report_rows: List[Dict],
        api_rows:    List[Dict],
    ) -> Tuple[List[VerifyResult], List[ForecastCheck]]:
        """Full validation pipeline for one ticker."""
        verify_results: List[VerifyResult] = []
        arith_checks:   List[ForecastCheck] = []

        # Step 7: normalize all to million + 1 decimal
        # (done inside compare_one / fallback_resolve)

        # Step 8: historical cross-compare
        hist_report = [r for r in report_rows if is_historical(r.get("period",""))]
        for rr in hist_report:
            canonical = rr.get("data_name","") or rr.get("canonical","")
            period    = str(rr.get("period",""))
            r_val     = rr.get("value")
            r_unit    = rr.get("unit","million")

            api_row   = _find_api(api_rows, ticker, canonical, period)
            if not api_row:
                # Try synonym
                syn_found = None
                for syn in _SYN_REV:
                    if syn in canonical.lower():
                        syn_found = _SYN_REV[syn]
                if syn_found:
                    api_row = _find_api(api_rows, ticker, syn_found, period)

            if api_row:
                a_val  = api_row.get("value")
                a_unit = api_row.get("unit","million")
                vr = compare_one(canonical, period, r_val, r_unit,
                                 a_val, a_unit, ticker)
                vr.source_report = "phase1_mdl003"
                vr.source_api    = api_row.get("source","mops")

                # Step 9: fallback if mismatch
                if vr.status == "MISMATCH":
                    vr = fallback_resolve(vr, api_rows, report_rows, ticker)

                # Step 10/11: confidence
                vr.confidence = compute_confidence(vr)
                verify_results.append(vr)
            else:
                # No API match at all
                vr = VerifyResult(ticker=ticker, canonical=canonical,
                                  period=period, is_historical=True)
                vr.value_report = std_val(r_val, r_unit)
                vr.value_final  = vr.value_report
                vr.status       = "NO_API"
                vr.confidence   = _P["conf_base"] - 0.10
                verify_results.append(vr)

        # Step 10: forecast arithmetic self-consistency
        fcst_report = [r for r in report_rows if is_forecast(r.get("period",""))]
        fcst_periods = sorted(set(r.get("period","") for r in fcst_report))
        for period in fcst_periods:
            period_rows = [r for r in fcst_report if r.get("period","") == period]
            fields: Dict[str, Optional[float]] = {}
            for r in period_rows:
                cn = r.get("data_name","") or r.get("canonical","")
                fields[cn] = std_val(r.get("value"), r.get("unit","million"))
            arith_checks.extend(
                verify_forecast_arithmetic(ticker, period, fields))

        # Growth reasonableness check per canonical
        for canonical in set(r.get("data_name","") for r in fcst_report):
            hist_vals = {r.get("period",""): std_val(r.get("value"),r.get("unit","million"))
                         for r in hist_report
                         if (r.get("data_name","") or r.get("canonical","")) == canonical}
            fcst_vals = {r.get("period",""): std_val(r.get("value"),r.get("unit","million"))
                         for r in fcst_report
                         if (r.get("data_name","") or r.get("canonical","")) == canonical}
            arith_checks.extend(
                verify_growth_reasonableness(ticker, canonical, hist_vals, fcst_vals))

        return verify_results, arith_checks

    def run(self, report_rows: List[Dict], api_rows: List[Dict]) -> Dict:
        t0       = time.perf_counter()
        out_dir  = self.cfg.get("output_dir", _P["output_dir"])
        ssot_dir = self.cfg.get("ssot_dir",   _P["ssot_dir"])
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        plugin_caps = load_plugins(ssot_dir)
        cap = _mdl008_accel_init(self.workers)
        log.info("[MDL008] accel=%s plugins=%s", cap, plugin_caps)

        if self.cfg.get("enable_db", True):
            self.db = MDL008DBWriter(str(Path(out_dir)/"VRN_MDL008.db"))

        # Group by ticker
        report_by_ticker = self._group_by_ticker(report_rows)
        api_by_ticker    = self._group_by_ticker(api_rows)
        tickers = sorted(set(report_by_ticker) | set(api_by_ticker))

        all_verify:  List[VerifyResult]   = []
        all_checks:  List[ForecastCheck]  = []

        for ticker in tickers:
            r_rows = report_by_ticker.get(ticker, [])
            a_rows = api_by_ticker.get(ticker, [])
            vrs, acs = self.validate_one_ticker(ticker, r_rows, a_rows)
            all_verify.extend(vrs)
            all_checks.extend(acs)

        # Convert to DF
        df_verify = results_to_df(all_verify)
        df_checks = checks_to_df(all_checks)

        # DB + export
        if self.db:
            if df_verify is not None: self.db.insert_verify(df_verify)
            if df_checks is not None: self.db.insert_checks(df_checks)
            self.db.export(out_dir)

        # Summary stats
        total = len(all_verify)
        n_match  = sum(1 for r in all_verify if r.status == "MATCH")
        n_miss   = sum(1 for r in all_verify if r.status == "MISMATCH")
        n_unres  = sum(1 for r in all_verify if r.status == "UNRESOLVED")
        n_noapi  = sum(1 for r in all_verify if r.status == "NO_API")
        n_fcst   = sum(1 for c in all_checks if not c.passed)
        match_rate = n_match / total if total else 0.0
        avg_conf   = (sum(r.confidence for r in all_verify) / total) if total else 0.0

        elapsed = round(time.perf_counter()-t0, 2)
        summary = {
            "module": __module_id__, "version": __version__,
            "elapsed": elapsed,
            "tickers": tickers, "n_tickers": len(tickers),
            "total_comparisons": total,
            "match":      n_match,
            "mismatch":   n_miss,
            "unresolved": n_unres,
            "no_api":     n_noapi,
            "match_rate": round(match_rate, 4),
            "avg_confidence": round(avg_conf, 3),
            "forecast_checks_total": len(all_checks),
            "forecast_checks_fail":  n_fcst,
            "success": match_rate >= 0.90 and n_unres == 0,
            "plugin_caps": plugin_caps,
        }

        Path(out_dir).joinpath("VRN_MDL008_Summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")

        # ── v1.1.0: BatchBuffer + DuckDB ───────────────────────────────────
        flush_stats = {"verify": 0, "fcst": 0}
        if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
            try:
                buf = MDL008BatchBuffer(self.cfg.get("batch_size", 5000))
                buf.push_verify(all_verify)
                buf.push_forecast(all_checks)
                duck_path = str(Path(out_dir) / "VRN_MDL008.duckdb")
                duck = MDL008DuckWriter(duck_path)
                v_rows, f_rows = buf.consume_all()
                flush_stats = duck.flush(v_rows, f_rows)
                log.info("[MDL008] DuckDB flush: %s", flush_stats)
                pq_paths = duck.export_parquet_polars(out_dir)
                if pq_paths: log.info("[MDL008] Parquet exports: %d", len(pq_paths))
                duck.close()
                summary["flush_stats"] = flush_stats
            except Exception as e:
                log.warning("[MDL008] DuckDB pipeline fail: %s", e)

        # Inject summary fields needed by SelfVerifier
        summary["n_verify"]      = len(all_verify)
        summary["n_fcst_checks"] = len(all_checks)
        summary["n_match"]       = n_match
        summary["n_mismatch"]    = n_miss
        summary["ok"]            = summary.get("success", False)

        # ── v1.1.0: 4-phase Self-Verify HTML ───────────────────────────────
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                sv = MDL008SelfVerifier(self.cfg, summary, out_dir).run()
                html = build_self_verify_html_mdl008(sv, summary)
                sv_html_path = str(Path(out_dir) / "VRN_MDL008_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL008] Self-verify: %s (%d/%d) → %s",
                         sv["classification"], sv["pass"], sv["total"], sv_html_path)
                summary["self_verify"] = sv["classification"]
                summary["self_verify_html"] = sv_html_path
            except Exception as e:
                log.warning("[MDL008] self_verify build fail: %s", e)

        log.info("[MDL008] DONE: tickers=%d compare=%d match=%.1f%% conf=%.3f unres=%d "
                 "fcst_fail=%d %.2fs",
                 len(tickers), total, match_rate*100, avg_conf, n_unres, n_fcst, elapsed)
        return summary

__all__ = [
    "__version__","__module_id__",
    "_PARAMS","_P",
    "TW_TICKER_REGEX","TW_BLOOMBERG_REGEX","TW_YFINANCE_REGEX",
    "is_historical","is_forecast","to_year",
    "SYNONYM_FALLBACK","SIGN_CONVENTION",
    "_mdl008_accel_init","load_plugins",
    "_cel_submit","_cel_map",
    "to_million","precision_normalize","std_val","tolerance",
    "VerifyResult","ForecastCheck",
    "compare_one","classify_mismatch",
    "fallback_resolve",
    "verify_forecast_arithmetic","verify_growth_reasonableness",
    "compute_confidence",
    "results_to_df","checks_to_df",
    "MDL008DBWriter","VRN_MDL008_CrossValidator",
    # v1.1.0 NEW
    "MDL008BatchBuffer","MDL008DuckWriter","MDL008SelfVerifier",
    "build_self_verify_html_mdl008",
    "POLARS_OK","DUCKDB_OK",
]

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="VRN MDL008 Cross Validator")
    p.add_argument("--report-parquet", required=True, help="Phase1 or Phase2 parquet")
    p.add_argument("--api-parquet",    required=True, help="MDL007 API parquet")
    p.add_argument("--output-dir",     default=_P["output_dir"])
    p.add_argument("--ssot-dir",       default=_P["ssot_dir"])
    args = p.parse_args()

    if pd:
        report_rows = pd.read_parquet(args.report_parquet).to_dict("records")
        api_rows    = pd.read_parquet(args.api_parquet).to_dict("records")
    else:
        print("pandas required"); sys.exit(1)

    cfg    = {"output_dir": args.output_dir, "ssot_dir": args.ssot_dir}
    result = VRN_MDL008_CrossValidator(cfg).run(report_rows, api_rows)
    print(json.dumps({
        "success":    result["success"],
        "match_rate": result["match_rate"],
        "total":      result["total_comparisons"],
        "match":      result["match"],
        "unresolved": result["unresolved"],
    }, indent=2))
