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
# ===== [VIA:ANCHOR:PD_PL:START] =====
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import polars as pl
except Exception:
    pl = None
# ===== [VIA:ANCHOR:PD_PL:END] =====

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
import sys
from pathlib import Path

def _via_bootstrap_support_paths() -> None:
    """找 supportive_module, 最多往上 4 層。"""
    try:
        _self = Path(__file__).resolve()
        _candidates = [_self.parent]
        p = _self.parent
        for _ in range(4):
            p = p.parent
            _candidates.append(p)
        for root in _candidates:
            sup = root / "supportive_module"
            if sup.is_dir():
                _s = str(sup)
                if _s not in sys.path:
                    sys.path.insert(0, _s)
                break
        if str(_self.parent) not in sys.path:
            sys.path.insert(0, str(_self.parent))
    except Exception:
        pass

_via_bootstrap_support_paths()

# VRN_SupportBridge: 統一橋接 SSOT/Aegis/Celeritas/super_engine
try:
    from VRN_SupportBridge import BRIDGE as _BRIDGE
    _HAS_BRIDGE = True
except Exception:
    _BRIDGE = None
    _HAS_BRIDGE = False

# 保留原變數名供向後相容 (MDL 內部若有直接引用)
try:
    import VIA_SSOT_Unified as VIA_SSOT_Unified
except Exception:
    VIA_SSOT_Unified = None

try:
    import VeritasAegisNexus as VeritasAegisNexus
except Exception:
    VeritasAegisNexus = None

try:
    import VeritasCeleritas as VeritasCeleritas
except Exception:
    VeritasCeleritas = None
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

"""
VRN_MDL010_CodeRegistry.py
===========================
VERITAS REPORT NOVA — MDL010 Code Registry & Full-Name Resolver
Version   : 1.0.0   |   Module ID : VRN-MDL010-SUP-001
Asset ID  : VRN-MDL010-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

PIPELINE POSITION
=================
  [FETCH SUBSYSTEM]
    MDL010 (THIS)  → 代號/全名中樞 (universe)
    MDL011         → 每日 MOPS/TWSE/TPEX/YF 抓取
    MDL012         → 單季/累計/年度交互驗證
    MDL013         → AKShare
    MDL014         → FRED/宏觀
    VRN_Pipeline_Runner_Fetch → 總編排 + iteration

PUBLIC API (class VRN_MDL010_CodeRegistry)
==========================================
  __init__(cfg: Dict)
  run()                          → {ok, total, by_class, log_json}
  resolve(query_code: str)       → {ok, code, canonical, name, asset_class, meta, source}
  list_universe(asset_class=None)→ list[dict]
  suggest(query, top=5)          → list[dict]
  add_default(cls, code, meta)   → bool
  dump_universe(out_json=None)   → dict
"""

import os
import json
import re
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("VRN_MDL010")
if not log.handlers:
    logging.basicConfig(level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT UNIVERSE (可由 cfg 覆蓋/擴充)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_TW_STOCKS = {
    "2330": {"name": "台積電",   "yf": "2330.TW",  "market": "TWSE", "sector": "半導體"},
    "2317": {"name": "鴻海",     "yf": "2317.TW",  "market": "TWSE", "sector": "電子代工"},
    "2454": {"name": "聯發科",   "yf": "2454.TW",  "market": "TWSE", "sector": "IC設計"},
    "2308": {"name": "台達電",   "yf": "2308.TW",  "market": "TWSE", "sector": "電源"},
    "2603": {"name": "長榮",     "yf": "2603.TW",  "market": "TWSE", "sector": "航運"},
    "2609": {"name": "陽明",     "yf": "2609.TW",  "market": "TWSE", "sector": "航運"},
    "2615": {"name": "萬海",     "yf": "2615.TW",  "market": "TWSE", "sector": "航運"},
    "3006": {"name": "晶豪科",   "yf": "3006.TW",  "market": "TWSE", "sector": "記憶體"},
    "3014": {"name": "聯陽",     "yf": "3014.TW",  "market": "TWSE", "sector": "IC設計"},
    "3017": {"name": "奇鋐",     "yf": "3017.TW",  "market": "TWSE", "sector": "散熱"},
    "3324": {"name": "雙鴻",     "yf": "3324.TWO", "market": "TPEX", "sector": "散熱"},
    "6505": {"name": "台塑化",   "yf": "6505.TW",  "market": "TWSE", "sector": "石化"},
    "2002": {"name": "中鋼",     "yf": "2002.TW",  "market": "TWSE", "sector": "鋼鐵"},
    "1301": {"name": "台塑",     "yf": "1301.TW",  "market": "TWSE", "sector": "石化"},
    "1303": {"name": "南亞",     "yf": "1303.TW",  "market": "TWSE", "sector": "石化"},
}

_DEFAULT_TW_INDEX = {
    "TWII":   {"name": "加權指數", "yf": "^TWII",  "market": "TWSE", "src": "TWSE_API"},
    "OTCI":   {"name": "櫃買指數", "yf": "^TWOII", "market": "TPEX", "src": "TPEX_API"},
}

_DEFAULT_GLOBAL_INDEX = {
    "^GSPC":    {"name": "S&P 500",      "region": "US", "currency": "USD"},
    "^NDX":     {"name": "Nasdaq 100",   "region": "US", "currency": "USD"},
    "^DJI":     {"name": "Dow Jones",    "region": "US", "currency": "USD"},
    "^RUT":     {"name": "Russell 2000", "region": "US", "currency": "USD"},
    "^VIX":     {"name": "VIX",          "region": "US", "currency": "USD"},
    "^N225":    {"name": "Nikkei 225",   "region": "JP", "currency": "JPY"},
    "^HSI":     {"name": "Hang Seng",    "region": "HK", "currency": "HKD"},
    "^KS11":    {"name": "KOSPI",        "region": "KR", "currency": "KRW"},
    "^GDAXI":   {"name": "DAX 30",       "region": "DE", "currency": "EUR"},
    "^FTSE":    {"name": "FTSE 100",     "region": "GB", "currency": "GBP"},
}

_DEFAULT_FX = {
    "TWD=X":    {"name": "USD/TWD", "pair": "USDTWD"},
    "EURUSD=X": {"name": "EUR/USD", "pair": "EURUSD"},
    "JPY=X":    {"name": "USD/JPY", "pair": "USDJPY"},
    "GBPUSD=X": {"name": "GBP/USD", "pair": "GBPUSD"},
    "CNY=X":    {"name": "USD/CNY", "pair": "USDCNY"},
    "DX-Y.NYB": {"name": "DXY",     "pair": "DXY"},
}

_DEFAULT_COMMODITIES = {
    "CL=F": {"name": "WTI 原油",         "cat": "energy"},
    "BZ=F": {"name": "Brent 原油",       "cat": "energy"},
    "NG=F": {"name": "天然氣",           "cat": "energy"},
    "GC=F": {"name": "黃金",             "cat": "precious"},
    "SI=F": {"name": "白銀",             "cat": "precious"},
    "HG=F": {"name": "銅 Dr.Copper",     "cat": "base_metal"},
    "ZS=F": {"name": "大豆",             "cat": "agri"},
    "ZC=F": {"name": "玉米",             "cat": "agri"},
    "^BDI": {"name": "BDI 波羅的海綜合", "cat": "shipping"},
}

_DEFAULT_CRYPTO = {
    "BTC-USD": {"name": "Bitcoin",  "exch": "Coinbase"},
    "ETH-USD": {"name": "Ethereum", "exch": "Coinbase"},
    "SOL-USD": {"name": "Solana",   "exch": "Coinbase"},
}

_DEFAULT_ETF = {
    "SPY":      {"name": "S&P 500 ETF",         "cat": "A"},
    "QQQ":      {"name": "Nasdaq 100 ETF",      "cat": "A"},
    "TLT":      {"name": "20Y+ Treasury ETF",   "cat": "C"},
    "SMH":      {"name": "VanEck Semicon ETF",  "cat": "B"},
    "SOXX":     {"name": "iShares Semicon ETF", "cat": "B"},
    "EWT":      {"name": "iShares Taiwan ETF",  "cat": "A"},
    "0050.TW":  {"name": "元大台灣50",          "cat": "F"},
    "0056.TW":  {"name": "元大高股息",          "cat": "F"},
    "00878.TW": {"name": "國泰永續高股息",      "cat": "F"},
}

_DEFAULT_FRED = {
    "US.Prices.CPI.Headline":       {"name": "CPI Headline",     "fred_id": "CPIAUCSL"},
    "US.Prices.CPI.Core":           {"name": "Core CPI",         "fred_id": "CPILFESL"},
    "US.Prices.PCE.Core":           {"name": "Core PCE",         "fred_id": "PCEPILFE"},
    "US.Rates.Treasury.10Y":        {"name": "10Y Treasury",     "fred_id": "DGS10"},
    "US.Rates.Treasury.2Y":         {"name": "2Y Treasury",      "fred_id": "DGS2"},
    "US.Rates.Spread.2s10s":        {"name": "10Y-2Y Spread",    "fred_id": "T10Y2Y"},
    "US.Rates.HY.Spread":           {"name": "HY OAS Spread",    "fred_id": "BAMLH0A0HYM2"},
    "US.FinCond.ChicagoFCI":        {"name": "Chicago Fed NFCI", "fred_id": "NFCI"},
    "US.Trade.DXY":                 {"name": "USD Broad Index",  "fred_id": "DTWEXBGS"},
    "CN.Business.PMI.Manufacturing":{"name": "China NBS Mfg PMI","fred_id": "CHNMFGPMI"},
}

_DEFAULT_AKSHARE = {
    "cn_copper_continuous":   {"name": "滬銅連續",     "func": "futures_main_sina", "sym": "CU0"},
    "cn_rebar_continuous":    {"name": "螺紋鋼連續",   "func": "futures_main_sina", "sym": "RB0"},
    "cn_iron_ore_continuous": {"name": "鐵礦石連續",   "func": "futures_main_sina", "sym": "I0"},
    "cn_gold_continuous":     {"name": "滬金連續",     "func": "futures_main_sina", "sym": "AU0"},
    "cn_crude_oil":           {"name": "上期所原油",   "func": "futures_main_sina", "sym": "SC0"},
    "cn_bdi":                 {"name": "BDI(AK)",      "func": "shipping_bdi",       "sym": None},
    "cn_pmi_mfg":             {"name": "中國製造業PMI","func": "macro_china_pmi",    "sym": None},
    "cn_pmi_svc":             {"name": "中國非製PMI",  "func": "macro_china_non_man_pmi","sym": None},
    "cn_m2":                  {"name": "中國M2",       "func": "macro_china_m2_yearly","sym": None},
}

_DEFAULTS = {
    "mdl010_temp": "./mdl010_temp",
    "enable_db":   True,
    "workers":     2,
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _jwrite(p: str, data: Any) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _ssot_normalize(v: str) -> str:
    """SSOT bridge: 台積電 → 2330.TW ; 營收 → Revenue (經 BRIDGE 統一)"""
    if _HAS_BRIDGE:
        out = _BRIDGE.ssot_normalize(_s(v))
        return _s(out) if out else _s(v)
    # Fallback: 直接呼叫
    if VIA_SSOT_Unified is None:
        return _s(v)
    try:
        s = VIA_SSOT_Unified.get_ssot()
        out = s.normalize(_s(v))
        return _s(out) if out else _s(v)
    except Exception:
        return _s(v)


# ─────────────────────────────────────────────────────────────────────────────
# CORE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class VRN_MDL010_CodeRegistry:
    """VRN-MDL010-CLS-001  Code/full-name resolution hub.

    run():
      1. Build asset buckets (9 classes) from defaults + cfg overrides
      2. Build reverse index (code / name / yf / fred_id → record)
      3. Write VRN_MDL010_Registry.json + csv + db (optional)
      4. Return {ok, total, by_class, log_json}
    """

    VERSION = "1.0.0"
    ASSET_ID = "VRN-MDL010-CLS-001"

    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg = dict(_DEFAULTS)
        if cfg:
            self.cfg.update(cfg)

        # Asset buckets (9 classes, extensible)
        self._buckets: Dict[str, Dict[str, Dict]] = {
            "TW_STOCK":     dict(_DEFAULT_TW_STOCKS),
            "TW_INDEX":     dict(_DEFAULT_TW_INDEX),
            "GLOBAL_INDEX": dict(_DEFAULT_GLOBAL_INDEX),
            "FX":           dict(_DEFAULT_FX),
            "COMMODITY":    dict(_DEFAULT_COMMODITIES),
            "CRYPTO":       dict(_DEFAULT_CRYPTO),
            "ETF":          dict(_DEFAULT_ETF),
            "FRED":         dict(_DEFAULT_FRED),
            "AKSHARE":      dict(_DEFAULT_AKSHARE),
        }

        # cfg override: cfg["universe_extend"] = {"TW_STOCK": {"6488": {...}}}
        ext = self.cfg.get("universe_extend") or {}
        for cls, items in ext.items():
            self._buckets.setdefault(cls, {}).update(items)

        self._rebuild_index()

    # ── internals ────────────────────────────────────────────────────────
    def _rebuild_index(self) -> None:
        idx: Dict[str, Dict[str, Any]] = {}
        for cls, bucket in self._buckets.items():
            for code, meta in bucket.items():
                rec = {
                    "code": code,
                    "asset_class": cls,
                    "name": meta.get("name", ""),
                    "meta": dict(meta),
                }
                idx[code.lower()] = rec
                if meta.get("name"):
                    idx[meta["name"].lower()] = rec
                if meta.get("yf"):
                    idx[meta["yf"].lower()] = rec
                if meta.get("fred_id"):
                    idx[meta["fred_id"].lower()] = rec
        self._idx = idx

    # ── public ───────────────────────────────────────────────────────────
    def resolve(self, query_code: str) -> Dict:
        """查詢任意代號 → 標準化紀錄"""
        if not query_code:
            return {"ok": False, "error": "empty_query"}

        q = _s(query_code)
        key = q.lower()

        if key in self._idx:
            rec = self._idx[key]
            return {
                "ok": True, "query": q,
                "code": rec["code"], "canonical": rec["code"],
                "name": rec["name"], "asset_class": rec["asset_class"],
                "meta": rec["meta"], "source": "default_universe",
            }

        # 4 碼台股 → .TW 自動補
        if re.fullmatch(r"[1-9]\d{3}", q):
            return {
                "ok": True, "query": q,
                "code": q, "canonical": q,
                "name": f"TW:{q}", "asset_class": "TW_STOCK_DYNAMIC",
                "meta": {"yf": q + ".TW", "market": "TWSE",
                         "note": "auto_suffix_TW"},
                "source": "regex_autofill",
            }

        # SSOT 兜底
        norm = _ssot_normalize(q)
        if norm and norm.lower() != q.lower():
            if norm.lower() in self._idx:
                rec = self._idx[norm.lower()]
                return {
                    "ok": True, "query": q,
                    "code": rec["code"], "canonical": rec["code"],
                    "name": rec["name"], "asset_class": rec["asset_class"],
                    "meta": rec["meta"], "source": "ssot_normalize",
                }
            return {
                "ok": True, "query": q,
                "code": norm, "canonical": norm,
                "name": norm, "asset_class": "SSOT_NORMALIZED",
                "meta": {}, "source": "ssot_normalize",
            }

        return {
            "ok": False, "query": q, "error": "code_not_found",
            "suggestions": self.suggest(q, top=5),
        }

    def resolve_batch(self, codes: List[str]) -> List[Dict]:
        return [self.resolve(c) for c in codes]

    def suggest(self, query_code: str, top: int = 5) -> List[Dict]:
        q = _s(query_code).lower()
        if not q:
            return []
        hits = []
        for key, rec in self._idx.items():
            if q in key:
                hits.append({"code": rec["code"], "name": rec["name"],
                             "asset_class": rec["asset_class"]})
                if len(hits) >= top:
                    break
        return hits

    def list_universe(self, asset_class: Optional[str] = None) -> List[Dict]:
        out = []
        buckets = (self._buckets if asset_class is None
                   else {asset_class: self._buckets.get(asset_class, {})})
        for cls, bucket in buckets.items():
            for code, meta in bucket.items():
                out.append({
                    "asset_class": cls, "code": code,
                    "name": meta.get("name", ""), "meta": meta,
                })
        return out

    def add_default(self, asset_class: str, code: str, meta: Dict) -> bool:
        if asset_class not in self._buckets:
            self._buckets[asset_class] = {}
        self._buckets[asset_class][code] = dict(meta)
        self._rebuild_index()
        return True

    def dump_universe(self, out_json: Optional[str] = None) -> Dict:
        payload = {
            "version": self.VERSION,
            "asset_classes": list(self._buckets.keys()),
            "counts": {k: len(v) for k, v in self._buckets.items()},
            "total": sum(len(v) for v in self._buckets.values()),
            "universe": {k: v for k, v in self._buckets.items()},
        }
        if out_json:
            _jwrite(out_json, payload)
        return payload

    # ── run (pipeline entry) ─────────────────────────────────────────────
    def run(self) -> Dict:
        t0 = time.perf_counter()
        out_dir = self.cfg.get("mdl010_temp", _DEFAULTS["mdl010_temp"])
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        log.info("[MDL010] building universe (%d classes)", len(self._buckets))
        payload = self.dump_universe()

        # Write JSON registry
        reg_json = str(Path(out_dir) / "VRN_MDL010_Registry.json")
        _jwrite(reg_json, payload)

        # Write flat CSV for downstream
        flat_rows = []
        for cls, bucket in self._buckets.items():
            for code, meta in bucket.items():
                flat_rows.append({
                    "asset_class": cls,
                    "code": code,
                    "name": meta.get("name", ""),
                    "yf": meta.get("yf") or meta.get("fred_id") or code,
                    "region": meta.get("region") or meta.get("market", "") or "",
                    "sector": meta.get("sector") or meta.get("cat", "") or "",
                })
        flat_csv = str(Path(out_dir) / "VRN_MDL010_Registry_flat.csv")
        if pd is not None and flat_rows:
            pd.DataFrame(flat_rows).to_csv(flat_csv, index=False,
                encoding=self.cfg.get("csv_encoding", "utf-8-sig"))
        else:
            # Manual CSV fallback
            lines = ["asset_class,code,name,yf,region,sector"]
            for r in flat_rows:
                lines.append(",".join(str(r.get(k, "")).replace(",", " ")
                             for k in ["asset_class", "code", "name",
                                       "yf", "region", "sector"]))
            Path(flat_csv).write_text("\n".join(lines), encoding="utf-8")

        # Write log
        result = {
            "ok": True,
            "module": "VRN_MDL010_CodeRegistry",
            "version": self.VERSION,
            "engine": {
                "aegis":     bool(_HAS_BRIDGE and _BRIDGE.has_aegis),
                "celeritas": bool(_HAS_BRIDGE and _BRIDGE.has_celeritas),
                "ssot":      bool(_HAS_BRIDGE and _BRIDGE.has_ssot),
                "super":     bool(_HAS_BRIDGE and _BRIDGE.has_super),
            },
            "total": payload["total"],
            "by_class": payload["counts"],
            "log_json": reg_json,
            "flat_csv": flat_csv,
            "elapsed": round(time.perf_counter() - t0, 3),
        }

        log_json = str(Path(out_dir) / "VRN_MDL010_Log.json")
        _jwrite(log_json, result)
        log.info("[MDL010] done total=%d elapsed=%.3fs",
                 payload["total"], result["elapsed"])
        return result


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli_main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="VRN_MDL010_CodeRegistry")
    p.add_argument("--query", default="", help="代號查詢")
    p.add_argument("--out",   default="./mdl010_temp")
    args = p.parse_args()

    reg = VRN_MDL010_CodeRegistry({"mdl010_temp": args.out})
    if args.query:
        print(json.dumps(reg.resolve(args.query), ensure_ascii=False, indent=2))
        return 0
    r = reg.run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(_cli_main())
