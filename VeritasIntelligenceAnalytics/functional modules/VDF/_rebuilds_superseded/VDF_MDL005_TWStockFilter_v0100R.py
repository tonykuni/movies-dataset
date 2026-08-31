#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL005_TWStockFilter.py
================================================================================
  VERITAS DATA FRAMEWORK · TW Stock Filter + Consensus
  Version    : 1.0.0R  |  Module ID : VDF-MDL005

  重建R(2026-08-12「完成全部」令;工作站正本候上傳,到件即讓位)。
  讀 MDL001 universe(+--tickers EXTRA)→ YF Consensus(target/upside/PER/DPS)+
  FactSet stub(需 entitlement,誠實 stub 不偽造)。輸出 1 表 → 1-5-TWStockFilter。
================================================================================
"""
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from VDF_MDL101_OutputManager import OutputManager

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False

BASE_DIR = str(Path(__file__).parent / "db")
UNIVERSE_SOURCE = str(Path(__file__).parent / "db" / "1-0-TWUniverse")
FACTSET_STATUS = "FACTSET_BRIDGE_STUB_AWAITING_ENTITLEMENT_IMPL"


def _cli_tickers():
    if "--tickers" in sys.argv:
        i = sys.argv.index("--tickers")
        if i + 1 < len(sys.argv):
            return [t.strip() for t in sys.argv[i + 1].split(",") if t.strip()]
    return []


def _universe_markets():
    """code → market(TWSE/TPEX);universe 缺席=空表誠實。"""
    p = Path(UNIVERSE_SOURCE)
    fp = p / "tw_universe_combined.parquet" if p.is_dir() else p
    if not fp.exists():
        return {}
    try:
        df = pd.read_parquet(fp)
        return dict(zip(df["code"].astype(str), df["market"]))
    except Exception:
        return {}


def _symbol(code, markets):
    if not code.isdigit():
        return code
    return code + (".TWO" if markets.get(code) == "TPEX" else ".TW")


class StockFilterEngine:
    def __init__(self):
        self.save_results = {}

    def run(self):
        if not PANDAS_AVAILABLE:
            print("❌ pandas 未裝,中止")
            return 2
        if not YFINANCE_AVAILABLE or yf is None:
            print("❌ yfinance 不可用 — 誠實中止(pip install yfinance)")
            return 1
        markets = _universe_markets()
        codes = _cli_tickers() or sorted(markets)
        rows = []
        errs = []
        for code in codes:
            sym = _symbol(code, markets)
            try:
                t = yf.Ticker(sym)
                info = t.info or {}
                hist = t.history(period="5d")
                price = float(hist["Close"].iloc[-1]) if len(hist) else None
                tm = info.get("targetMeanPrice")
                rows.append({
                    "ticker": code, "symbol": sym,
                    "name": info.get("shortName"), "currency": info.get("currency"),
                    "price": price,
                    "target_mean": tm, "target_median": info.get("targetMedianPrice"),
                    "target_high": info.get("targetHighPrice"),
                    "target_low": info.get("targetLowPrice"),
                    "upside_pct": (round((tm / price - 1) * 100, 2)
                                   if tm and price else None),
                    "recommendation": info.get("recommendationKey"),
                    "analysts": info.get("numberOfAnalystOpinions"),
                    "eps_trailing": info.get("trailingEps"),
                    "eps_forward": info.get("forwardEps"),
                    "per_trailing": info.get("trailingPE"),
                    "per_forward": info.get("forwardPE"),
                    "book_value": info.get("bookValue"),
                    "pb": info.get("priceToBook"),
                    "dps": info.get("dividendRate"),
                    "dividend_yield": info.get("dividendYield"),
                    "factset_consensus": FACTSET_STATUS,
                })
            except Exception as e:
                errs.append("%s:%s" % (sym, str(e)[:60]))
        mgr = OutputManager(base_dir=BASE_DIR, output_dir="1-5-TWStockFilter",
                            duckdb_filename="VDF_MDL005_TWStockFilter.duckdb")
        self.save_results["stock_filter_consensus"] = mgr.save(
            "stock_filter_consensus", pd.DataFrame(rows))
        print("MDL005:%d 檔 consensus · errors=%d" % (len(rows), len(errs)))
        for e in errs[:5]:
            print("   ⚠ %s" % e)
        return 0 if rows else 1


if __name__ == "__main__":
    ec = StockFilterEngine().run()
    if "--no-pause" not in sys.argv:
        try:
            input("\n按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
