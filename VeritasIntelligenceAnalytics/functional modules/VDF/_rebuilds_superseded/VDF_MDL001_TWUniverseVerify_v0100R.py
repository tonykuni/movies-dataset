#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL001_TWUniverseVerify.py
================================================================================
  VERITAS DATA FRAMEWORK · TW Universe Verifier
  Version    : 1.0.0R  |  Module ID : VDF-MDL001-VRF

  重建R(2026-08-12「完成全部」令;工作站正本候上傳,到件即讓位)。
  TWSE/TPEX OpenAPI 全市場 universe + SSOT regex 驗證:
    TW_TICKER_REGEX = (?!0)(?!202[1-9])(?!2030)([1-9]\d{3})  ← SSOT 鎖定
  離線/API 失敗=誠實 FAIL 列錯,不產假 universe。輸出 4 表 → 1-0-TWUniverse。
================================================================================
"""
import re
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
TW_TICKER_REGEX = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
TWSE_API = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_API = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"


class TWUniverseFetcher:
    """TWSE/TPEX OpenAPI → universe 驗證。stats 誠實記錄各源成敗。"""

    def __init__(self):
        self.stats = {"twse": 0, "tpex": 0, "rejected": 0, "errors": []}

    def _get(self, url):
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    def fetch(self):
        rows_ok, rows_rej = [], []
        pat = re.compile(r"^%s$" % TW_TICKER_REGEX)
        for market, url, code_k, name_k in (
                ("TWSE", TWSE_API, "公司代號", "公司簡稱"),
                ("TPEX", TPEX_API, "SecuritiesCompanyCode", "CompanyName")):
            try:
                for it in self._get(url):
                    code = str(it.get(code_k, "")).strip()
                    name = str(it.get(name_k, "")).strip()
                    row = {"code": code, "name": name, "market": market}
                    if pat.match(code):
                        rows_ok.append(row)
                        self.stats[market.lower()] += 1
                    else:
                        rows_rej.append({**row, "reason": "SSOT regex 不符"})
                        self.stats["rejected"] += 1
            except Exception as e:
                self.stats["errors"].append("%s:%s" % (market, str(e)[:80]))
        return rows_ok, rows_rej


class TWUniverseVerifyEngine:
    def __init__(self):
        self.save_results = {}

    def run(self):
        if not PANDAS_AVAILABLE:
            print("❌ pandas 未裝,中止")
            return 2
        f = TWUniverseFetcher()
        ok, rej = (f.fetch() if REQUESTS_AVAILABLE else ([], []))
        if not REQUESTS_AVAILABLE:
            f.stats["errors"].append("requests 未裝 — 離線誠實空")
        mgr = OutputManager(base_dir=BASE_DIR, output_dir="1-0-TWUniverse",
                            duckdb_filename="VDF_MDL001_TWUniverse.duckdb")
        df_ok = pd.DataFrame(ok)
        for name, df in (("twse_universe", df_ok[df_ok["market"] == "TWSE"] if len(df_ok) else df_ok),
                         ("tpex_universe", df_ok[df_ok["market"] == "TPEX"] if len(df_ok) else df_ok),
                         ("tw_universe_combined", df_ok),
                         ("tw_universe_rejected", pd.DataFrame(rej))):
            self.save_results[name] = mgr.save(name, df)
        n = sum(r["rows"] for r in self.save_results.values())
        print("MDL001-VRF:%d 列(twse %d/tpex %d/rej %d)· errors=%s"
              % (n, f.stats["twse"], f.stats["tpex"], f.stats["rejected"],
                 f.stats["errors"] or "無"))
        # 誠實:全空且有錯 → 非零(沒抓到=沒抓到)
        return 0 if n > 0 else (1 if f.stats["errors"] else 0)


if __name__ == "__main__":
    ec = TWUniverseVerifyEngine().run()
    if "--no-pause" not in sys.argv:
        try:
            input("\n按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
