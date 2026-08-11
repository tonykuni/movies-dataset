# -*- coding: utf-8 -*-
from __future__ import annotations
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
VRN_MDL011_DailyFetcher.py
===========================
VERITAS REPORT NOVA — MDL011  Daily Info Fetcher
Version   : 1.0.0   |   Module ID : VRN-MDL011-SUP-001
Asset ID  : VRN-MDL011-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

ROLE
====
每日一體抓取 (MOPS/TWSE/TPEX 籌碼 + YFinance 價格 + 兩大指數量價)
- 依 MDL010 做代號解析
- 依 Aegis 做 http 抓取 (若可用)
- 依 Celeritas 做平行化 (若可用)

PUBLIC API (class VRN_MDL011_DailyFetcher)
==========================================
  __init__(cfg)
  run() -> Dict
  fetch_daily_all(codes, date) -> Dict
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

log = logging.getLogger("VRN_MDL011")
if not log.handlers:
    logging.basicConfig(level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")

try:
    import yfinance as yf
except Exception:
    yf = None

# 引用 MDL010 + DataEngines (TWSE/TPEX/MOPS)
try:
    import VRN_MDL010_CodeRegistry as _mdl010_mod
    _HAS_MDL010 = True
except Exception:
    _HAS_MDL010 = False

try:
    from VDF_D2_DataEngines_v1 import (
        fetch_three_investors as _fetch_3inv,
        fetch_margin as _fetch_margin,
        fetch_day_trade as _fetch_daytrade,
    )
    _HAS_E1_DATA = True
except Exception:
    _HAS_E1_DATA = False

# SupportBridge (Aegis / Celeritas / SSOT / super) — 正式接入
try:
    from VRN_SupportBridge import BRIDGE as _BRIDGE
    _HAS_BRIDGE = True
except Exception:
    _BRIDGE = None
    _HAS_BRIDGE = False


_DEFAULTS = {
    "mdl011_temp":    "./mdl011_temp",
    "yf_retry":       2,
    "yf_delay":       1.5,
    "chunk":          50,
    "safe_skip":      True,
    "enable_db":      True,
    "include_chips":  True,
    "include_prices": True,
    "csv_encoding":   "utf-8-sig",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _jwrite(p: str, data: Any) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")


def _validate_date(date_yyyymmdd: str) -> Dict:
    try:
        dt = datetime.strptime(date_yyyymmdd, "%Y%m%d")
        today = datetime.now()
        if dt > today:
            return {"ok": False, "reason": "date_in_future"}
        if (today - dt).days > 365 * 5:
            return {"ok": False, "reason": "date_too_old"}
        return {"ok": True, "reason": "OK", "dt": dt}
    except Exception as exc:
        return {"ok": False, "reason": f"invalid_date:{exc}"}


def _shape_of(obj) -> Optional[Dict]:
    if pd is not None and hasattr(obj, "shape"):
        return {"type": "DataFrame", "shape": list(obj.shape),
                "columns": list(getattr(obj, "columns", []))[:20]}
    if isinstance(obj, list):
        return {"type": "list", "len": len(obj)}
    return {"type": type(obj).__name__} if obj is not None else None


# ─────────────────────────────────────────────────────────────────────────────
# CORE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class VRN_MDL011_DailyFetcher:
    """VRN-MDL011-CLS-001  daily price + chip fetcher.

    run():
      1. Build/inherit registry from MDL010
      2. Resolve codes → yf tickers
      3. YF download (window ±5 day)
      4. TWSE/TPEX chips (3inv / margin / day_trade)
      5. Index (^TWII)
      6. Write VRN_MDL011_DailyLog.json + csv + db
    """

    VERSION = "1.0.0"
    ASSET_ID = "VRN-MDL011-CLS-001"

    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg = dict(_DEFAULTS)
        if cfg:
            self.cfg.update(cfg)

        # Registry (shared with MDL010)
        self._registry = None
        if _HAS_MDL010:
            try:
                self._registry = _mdl010_mod.VRN_MDL010_CodeRegistry(cfg or {})
            except Exception as exc:
                log.warning("[MDL011] MDL010 init fail: %s", exc)

    # ── internals ────────────────────────────────────────────────────────
    def _to_yf_ticker(self, code: str) -> str:
        if self._registry is not None:
            r = self._registry.resolve(code)
            if r.get("ok"):
                m = r.get("meta") or {}
                return m.get("yf") or r.get("code") or code
        # Fallback: 4-digit TW
        if str(code).isdigit() and len(str(code)) == 4:
            return str(code) + ".TW"
        return str(code)

    def _resolve_batch(self, codes: List[str]) -> List[Dict]:
        if self._registry is not None:
            return self._registry.resolve_batch(codes)
        return [{"ok": True, "query": c, "code": c, "canonical": c,
                 "name": "", "asset_class": "UNKNOWN",
                 "meta": {"yf": self._to_yf_ticker(c)}} for c in codes]

    def _fetch_yf_prices(self, codes: List[str], date: str,
                         interval: str = "1d") -> Any:
        """
        價格抓取路徑:
          Path A  BRIDGE.aegis + BRIDGE.celeritas_parallel_map  (正式管道)
          Path B  yfinance.download                              (fallback)
        """
        if pd is None:
            return None
        dv = _validate_date(date)
        if not dv["ok"]:
            return None
        dt = dv["dt"]
        start = (dt - timedelta(days=7)).strftime("%Y-%m-%d")
        end   = (dt + timedelta(days=2)).strftime("%Y-%m-%d")
        tickers = [self._to_yf_ticker(c) for c in codes]
        tickers = [t for t in tickers if t]
        if not tickers:
            return None

        # Path A: BRIDGE Aegis + Celeritas
        if _HAS_BRIDGE and _BRIDGE.has_aegis:
            def _fetch_one(t):
                try:
                    return _BRIDGE.aegis_fetch_yf_history_single(
                        t, start=start, end=end, auto_adjust=False)
                except Exception:
                    return None

            # Celeritas.parallel_map; 無則自動 sequential
            results = _BRIDGE.celeritas_parallel_map(_fetch_one, tickers)

            frames = []
            for t, r in zip(tickers, results):
                if r is not None and pd is not None and hasattr(r, "copy"):
                    if hasattr(r, "empty") and not r.empty:
                        r2 = r.copy()
                        r2["yf_ticker"] = t
                        frames.append(r2)
            if frames:
                merged = _BRIDGE.celeritas_concat(frames)
                return merged if merged is not None and not (
                    hasattr(merged, "empty") and merged.empty) else None

        # Path B: yfinance fallback
        if yf is None:
            return None
        try:
            df = yf.download(
                tickers, start=start, end=end,
                interval=interval, auto_adjust=False,
                group_by="ticker", threads=True, progress=False,
            )
            return df if df is not None and not df.empty else None
        except Exception as exc:
            log.warning("[MDL011] yf.download fail: %s", exc)
            return None

    def _fetch_tw_chips(self, date: str, market: str = "ALL") -> Dict:
        """
        籌碼抓取路徑:
          Path A  BRIDGE.aegis (原生 TWSE/TPEX API + shield)
          Path B  VDF_D2_DataEngines (第三方 API fallback)
        """
        out = {"three_inv": None, "margin": None,
               "day_trade": None, "errors": [], "source": None}

        # Path A: BRIDGE Aegis (優先, 官方 API + compliance)
        if _HAS_BRIDGE and _BRIDGE.has_aegis:
            try:
                if market in ("TWSE", "ALL"):
                    twse_inst = _BRIDGE.aegis_fetch_twse_institutional(date)
                    twse_mar  = _BRIDGE.aegis_fetch_twse_margin(date)
                    twse_day  = _BRIDGE.aegis_fetch_twse_day_trading(date)
                else:
                    twse_inst = twse_mar = twse_day = None

                if market in ("TPEX", "ALL"):
                    tpex_inst = _BRIDGE.aegis_fetch_tpex_institutional(date)
                    tpex_mar  = _BRIDGE.aegis_fetch_tpex_margin(date)
                    tpex_day  = _BRIDGE.aegis_fetch_tpex_day_trading(date)
                else:
                    tpex_inst = tpex_mar = tpex_day = None

                # 合併 TWSE + TPEX
                def _merge(tw, tp):
                    if tw and tp:
                        if pd is not None and isinstance(tw, (list, dict)) \
                                          and isinstance(tp, (list, dict)):
                            try:
                                dtw = pd.DataFrame(tw) if isinstance(tw, list) else pd.DataFrame([tw])
                                dtp = pd.DataFrame(tp) if isinstance(tp, list) else pd.DataFrame([tp])
                                return _BRIDGE.celeritas_concat([dtw, dtp])
                            except Exception:
                                pass
                        return tw or tp
                    return tw or tp

                out["three_inv"] = _merge(twse_inst, tpex_inst)
                out["margin"]    = _merge(twse_mar, tpex_mar)
                out["day_trade"] = _merge(twse_day, tpex_day)
                out["source"]    = "aegis"
                return out
            except Exception as exc:
                out["errors"].append(f"aegis_chips:{exc}")
                # 繼續嘗試 Path B

        # Path B: VDF_D2_DataEngines fallback
        if _HAS_E1_DATA:
            for key, fn in [("three_inv", _fetch_3inv),
                            ("margin", _fetch_margin),
                            ("day_trade", _fetch_daytrade)]:
                try:
                    out[key] = fn(date, market)
                except Exception as exc:
                    out["errors"].append(f"{key}:{exc}")
            out["source"] = "vdf_dataengines"
        else:
            out["errors"].append("no_aegis_and_no_dataengines")
        return out

    # ── public API ───────────────────────────────────────────────────────
    def fetch_daily_all(self, codes: List[str], date: str) -> Dict:
        errors = []
        meta = {
            "date": date, "codes_in": len(codes),
            "include_chips": self.cfg.get("include_chips"),
            "include_prices": self.cfg.get("include_prices"),
            "ts": datetime.now().isoformat(timespec="seconds"),
        }

        dv = _validate_date(date)
        if not dv["ok"]:
            return {"ok": False, "error": dv["reason"], "meta": meta}

        resolved = self._resolve_batch(codes)
        meta["codes_resolved_ok"] = sum(1 for r in resolved if r.get("ok"))

        prices = None
        if self.cfg.get("include_prices"):
            try:
                prices = self._fetch_yf_prices(codes, date)
            except Exception as exc:
                errors.append(f"prices:{exc}")

        chips = {"three_inv": None, "margin": None, "day_trade": None}
        if self.cfg.get("include_chips"):
            try:
                chips = self._fetch_tw_chips(date, market="ALL")
                errors.extend(chips.pop("errors", []) or [])
            except Exception as exc:
                errors.append(f"chips:{exc}")

        # Index
        index_df = None
        try:
            if yf is not None:
                idx_s = (dv["dt"] - timedelta(days=7)).strftime("%Y-%m-%d")
                idx_e = (dv["dt"] + timedelta(days=2)).strftime("%Y-%m-%d")
                index_df = yf.download(
                    ["^TWII"], start=idx_s, end=idx_e,
                    auto_adjust=False, threads=True, progress=False)
        except Exception as exc:
            errors.append(f"index:{exc}")

        return {
            "ok": True, "meta": meta,
            "resolved": resolved,
            "prices": prices, "chips": chips, "index": index_df,
            "errors": errors,
        }

    # ── run (pipeline entry) ─────────────────────────────────────────────
    def run(self) -> Dict:
        t0 = time.perf_counter()
        out_dir = self.cfg.get("mdl011_temp", _DEFAULTS["mdl011_temp"])
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        codes = self.cfg.get("codes") or ["2330", "3017", "3324"]
        date  = self.cfg.get("date") or datetime.now().strftime("%Y%m%d")

        log.info("[MDL011] fetch_daily_all codes=%d date=%s", len(codes), date)
        result_raw = self.fetch_daily_all(codes, date)

        # Persist DataFrames to CSV
        csv_paths = {}
        if pd is not None:
            prices = result_raw.get("prices")
            if hasattr(prices, "to_csv"):
                p = str(Path(out_dir) / "VRN_MDL011_prices.csv")
                try:
                    prices.to_csv(p, encoding=self.cfg.get("csv_encoding"))
                    csv_paths["prices"] = p
                except Exception:
                    pass
            for k in ("three_inv", "margin", "day_trade"):
                v = (result_raw.get("chips") or {}).get(k)
                if hasattr(v, "to_csv"):
                    p = str(Path(out_dir) / f"VRN_MDL011_chips_{k}.csv")
                    try:
                        v.to_csv(p, index=False,
                            encoding=self.cfg.get("csv_encoding"))
                        csv_paths[k] = p
                    except Exception:
                        pass
            idx = result_raw.get("index")
            if hasattr(idx, "to_csv"):
                p = str(Path(out_dir) / "VRN_MDL011_index.csv")
                try:
                    idx.to_csv(p, encoding=self.cfg.get("csv_encoding"))
                    csv_paths["index"] = p
                except Exception:
                    pass

        # Summary (JSON-safe: strip DataFrames)
        summary = {
            "ok": bool(result_raw.get("ok")),
            "module": "VRN_MDL011_DailyFetcher",
            "version": self.VERSION,
            "engine": {
                "aegis":     bool(_HAS_BRIDGE and _BRIDGE.has_aegis),
                "celeritas": bool(_HAS_BRIDGE and _BRIDGE.has_celeritas),
                "ssot":      bool(_HAS_BRIDGE and _BRIDGE.has_ssot),
                "super":     bool(_HAS_BRIDGE and _BRIDGE.has_super),
            },
            "meta": result_raw.get("meta", {}),
            "prices": _shape_of(result_raw.get("prices")),
            "chips": {k: _shape_of(v)
                      for k, v in (result_raw.get("chips") or {}).items()},
            "index": _shape_of(result_raw.get("index")),
            "resolved_count": len(result_raw.get("resolved") or []),
            "resolved_ok_count": sum(
                1 for r in (result_raw.get("resolved") or []) if r.get("ok")),
            "errors": result_raw.get("errors", []),
            "csv_paths": csv_paths,
            "elapsed": round(time.perf_counter() - t0, 3),
        }

        log_json = str(Path(out_dir) / "VRN_MDL011_Log.json")
        _jwrite(log_json, summary)
        summary["log_json"] = log_json

        log.info("[MDL011] done ok=%s errs=%d elapsed=%.3fs",
                 summary["ok"], len(summary["errors"]), summary["elapsed"])
        return summary


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli_main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="VRN_MDL011_DailyFetcher")
    p.add_argument("--codes", default="2330,3017,3324")
    p.add_argument("--date",  default=datetime.now().strftime("%Y%m%d"))
    p.add_argument("--out",   default="./mdl011_temp")
    args = p.parse_args()

    cfg = {
        "codes": [c.strip() for c in args.codes.split(",") if c.strip()],
        "date":  args.date,
        "mdl011_temp": args.out,
    }
    fetcher = VRN_MDL011_DailyFetcher(cfg)
    r = fetcher.run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(_cli_main())
