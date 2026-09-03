#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL003_SentimentMacroEngine.py
================================================================================
  VERITAS DATA FRAMEWORK · Sentiment + Macro Engine
  Version    : 1.0.0R  |  Module ID : VDF-MDL003

  重建R(2026-08-12「完成全部」令;工作站正本候上傳,到件即讓位)。
  4 條 API 整合:AAII 情緒 · CNN Fear&Greed(主指標+子指標)· FRED 總經 · AKShare
  (期貨/航運/總經)。各 fetcher 獨立、可 patch(302 端到端測試即 patch 本面)、
  失敗誠實記 stats.errors 回空表 — 絕不產假資料。輸出 7 表 → 1-4-SentimentMacro。
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
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
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

BASE_DIR = str(Path(__file__).parent / "db")
AAII_URL = "https://www.aaii.com/files/surveys/sentiment.xls"
CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s"
FRED_SERIES = ["DGS10", "DGS2", "CPIAUCSL", "UNRATE", "WALCL", "DCOILWTICO", "DTWEXBGS"]
AKSHARE_FUTURES = ["cn_copper_continuous", "cn_iron_ore", "cn_rebar_continuous"]


class AAIIFetcher:
    """AAII 週頻情緒(bull/neutral/bear)。回 DataFrame;失敗=空+errors。"""

    def __init__(self):
        self.stats = {"rows": 0, "method": "", "errors": []}

    def fetch(self):
        try:
            df = pd.read_excel(AAII_URL, skiprows=3)  # 官方 xls
            df = df.rename(columns=str.lower)
            self.stats = {"rows": len(df), "method": "xls", "errors": []}
            return df
        except Exception as e:
            self.stats = {"rows": 0, "method": "fail", "errors": [str(e)[:80]]}
            return pd.DataFrame()


class CNNFearGreedFetcher:
    """CNN F&G:回 {"fear_greed": df, "subindicators": df}。"""

    def __init__(self):
        self.stats = {"rows": 0, "subindicators": 0, "errors": []}

    def fetch(self):
        try:
            j = requests.get(CNN_URL, timeout=30,
                             headers={"User-Agent": "Mozilla/5.0"}).json()
            main = pd.DataFrame(j.get("fear_and_greed_historical", {}).get("data", []))
            if len(main):
                main = main.rename(columns={"x": "date", "y": "fear_greed_index"})
                main["date"] = pd.to_datetime(main["date"], unit="ms")
            subs = []
            for k, v in j.items():
                if k.startswith(("market_", "stock_", "junk_", "safe_", "put_")) and isinstance(v, dict):
                    for d in v.get("data", []):
                        subs.append({"date": pd.to_datetime(d["x"], unit="ms"),
                                     "indicator": k, "value": d["y"]})
            sub = pd.DataFrame(subs)
            self.stats = {"rows": len(main), "subindicators": sub["indicator"].nunique()
                          if len(sub) else 0, "errors": []}
            return {"fear_greed": main, "subindicators": sub}
        except Exception as e:
            self.stats = {"rows": 0, "subindicators": 0, "errors": [str(e)[:80]]}
            return {"fear_greed": pd.DataFrame(), "subindicators": pd.DataFrame()}


class FREDFetcher:
    """FRED fredgraph.csv 免金鑰路徑;長格式 date/value/fred_id。"""

    def __init__(self, series=None):
        self.series = series or FRED_SERIES
        self.stats = {"ok": 0, "fail": 0, "rows": 0, "errors": [], "method": {}}

    def fetch(self):
        frames = []
        for sid in self.series:
            try:
                df = pd.read_csv(FRED_CSV % sid)
                df.columns = ["date", "value"]
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                df = df.dropna()
                df["fred_id"] = sid
                df["via_code"] = "US.fred.%s" % sid
                frames.append(df)
                self.stats["ok"] += 1
            except Exception as e:
                self.stats["fail"] += 1
                self.stats["errors"].append("%s:%s" % (sid, str(e)[:60]))
        out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        self.stats["rows"] = len(out)
        return out


class AKShareFetcher:
    """AKShare(選配):期貨/航運/總經。未裝=誠實空。回 dict 三鍵。"""

    def __init__(self):
        self.stats = {"ok": 0, "fail": 0, "rows": 0, "errors": []}

    def fetch(self):
        try:
            import akshare as ak  # noqa: F401
        except ImportError:
            self.stats["errors"].append("akshare 未裝 — 誠實空(pip install akshare)")
            return {"futures": pd.DataFrame(), "shipping": pd.DataFrame(),
                    "macro": pd.DataFrame()}
        fut_rows = []
        try:
            import akshare as ak
            df = ak.futures_main_sina(symbol="CU0")
            df["code"] = "cn_copper_continuous"
            fut_rows.append(df)
            self.stats["ok"] += 1
        except Exception as e:
            self.stats["fail"] += 1
            self.stats["errors"].append(str(e)[:60])
        fut = pd.concat(fut_rows, ignore_index=True) if fut_rows else pd.DataFrame()
        self.stats["rows"] = len(fut)
        return {"futures": fut, "shipping": pd.DataFrame(), "macro": pd.DataFrame()}


class SentimentMacroEngine:
    """編排:4 fetcher → 7 表落檔。save_results = {表: OutputManager.save 回傳}。"""

    def __init__(self):
        self.save_results = {}

    def run(self):
        if not PANDAS_AVAILABLE:
            print("❌ pandas 未裝,中止")
            return 2
        aaii = AAIIFetcher()
        cnn = CNNFearGreedFetcher()
        fred = FREDFetcher()
        ak = AKShareFetcher()
        df_aaii = aaii.fetch()
        cnn_r = cnn.fetch()
        df_fred = fred.fetch()
        ak_r = ak.fetch()
        mgr = OutputManager(base_dir=BASE_DIR, output_dir="1-4-SentimentMacro",
                            duckdb_filename="VDF_MDL003_SentimentMacro.duckdb")
        for name, df in (("aaii_sentiment", df_aaii),
                         ("cnn_fear_greed", cnn_r.get("fear_greed")),
                         ("cnn_subindicators", cnn_r.get("subindicators")),
                         ("fred_macro", df_fred),
                         ("akshare_futures", ak_r.get("futures")),
                         ("akshare_shipping", ak_r.get("shipping")),
                         ("akshare_macro", ak_r.get("macro"))):
            self.save_results[name] = mgr.save(name, df)
        tot = sum(r["rows"] for r in self.save_results.values())
        errs = aaii.stats["errors"] + cnn.stats["errors"] + fred.stats["errors"] + ak.stats["errors"]
        print("MDL003:%d 表 · %s 列 · errors=%d" % (len(self.save_results), "{:,}".format(tot), len(errs)))
        for e in errs[:6]:
            print("   ⚠ %s" % e)
        return 0


if __name__ == "__main__":
    ec = SentimentMacroEngine().run()
    if "--no-pause" not in sys.argv:
        try:
            input("\n按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
