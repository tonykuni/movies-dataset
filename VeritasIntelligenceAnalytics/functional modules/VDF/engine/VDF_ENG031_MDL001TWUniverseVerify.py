#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL001_TWUniverse_Verify.py
================================================================================
  VERITAS DATA FRAMEWORK · MDL001 補助
  Version    : 1.0.0   |   Module ID : VDF-MDL001-VRF-001

  目的:
    擷取台灣個股 (TWSE 上市 + TPEX 上櫃) 全清單,
    套用 SSOT 鎖定的 TW_TICKER_REGEX,
    驗證 TWSE / TPEX 個別數量, 並輸出可給 MDL001 主引擎使用的 universe 檔.

  SSOT 鎖定 regex (USER LOCKED · 不可修改):
    TW_TICKER_REGEX     = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
    TW_BLOOMBERG_REGEX  = XXXX TT format
    TW_YFINANCE_REGEX   = XXXX.TW / XXXX.TWO format

  策略:
    1. TWSE OpenAPI  : openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
    2. TPEX OpenAPI  : tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
    3. 套 SSOT regex 篩選 (擷取 4 位數字 ticker, 排除首位 0, 排除 2021-2030)
    4. 額外標註: 被排除的 codes (ETF/年份/格式不符), 給使用者參考
    5. 輸出:
        - twse_universe.parquet / .csv (utf-8-sig)
        - tpex_universe.parquet / .csv
        - tw_universe_combined.parquet / .csv
        - tw_universe_rejected.parquet / .csv (排除清單)
        - verify_report.json (詳細統計)
    6. Rich Summary Matrix: TWSE/TPEX 數量驗證表

USAGE
================================================================================
  python VDF_MDL001_TWUniverse_Verify.py            # 完整抓 + 驗證
  python VDF_MDL001_TWUniverse_Verify.py --dryrun   # 不抓網,只跑 regex 自我驗證
  python VDF_MDL001_TWUniverse_Verify.py --no-pause # CI/批次模式
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

# =====================================================================================
# 📋 ALL PARAMETERS ON TOP
# =====================================================================================

PROJECT_NAME       = "MDL001-TWUniverseVerify"
BASE_DIR           = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
OUTPUT_DIR         = "1-0-TWUniverse"

# SSOT 鎖定 regex (USER LOCKED · 唯讀)
TW_TICKER_REGEX    = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
TW_BLOOMBERG_REGEX = r"^([1-9]\d{3})\s+TT$"
TW_YFINANCE_REGEX  = r"^([1-9]\d{3})\.(TW|TWO)$"

# 官方 OpenAPI endpoints
TWSE_LISTING_URL   = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX_LISTING_URL   = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"

# 備援 endpoints (主要失敗時)
TWSE_LISTING_FB    = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL"
TPEX_LISTING_FB    = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"

# Network
HTTP_TIMEOUT       = 30
MAX_RETRIES        = 3
RETRY_DELAY        = 2
HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json, */*",
}

# Output formats
OUTPUT_PARQUET     = True
OUTPUT_CSV         = True
OUTPUT_JSON        = True
CSV_ENCODING       = "utf-8-sig"


# =====================================================================================
# 📦 Imports
# =====================================================================================

import os, sys, re, json, time, warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None


# =====================================================================================
# 🔧 Utilities
# =====================================================================================

def _http_get(url: str, timeout: int = HTTP_TIMEOUT,
              retries: int = MAX_RETRIES) -> Optional[Any]:
    if not REQUESTS_AVAILABLE:
        return None
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
            if r.ok:
                return r
            last_exc = f"HTTP {r.status_code}"
        except Exception as e:
            last_exc = str(e)[:120]
        if attempt < retries - 1:
            time.sleep(RETRY_DELAY)
    return None


def apply_ssot_regex(code: str) -> Tuple[bool, str]:
    """
    套用 SSOT 鎖定的 TW_TICKER_REGEX 判定.

    回傳:
      (pass_flag, reject_reason)
        - pass_flag=True  → 符合, reject_reason=""
        - pass_flag=False → 不符, reject_reason=原因標籤
    """
    code = str(code).strip()
    if not code:
        return False, "EMPTY"
    if not code.isdigit():
        return False, "NON_DIGIT"
    if len(code) != 4:
        return False, "NON_4DIGIT"
    # SSOT 鎖定條件
    if code.startswith('0'):
        return False, "LEADING_ZERO_ETF"     # ETF 起始為 0 (0050, 00878 等)
    if re.match(r'^202[1-9]$', code):
        return False, "YEAR_LIKE_2021_2029"  # 年份排除
    if code == '2030':
        return False, "YEAR_LIKE_2030"
    # 核心 regex 驗證 (應通過)
    if not re.match(r'^[1-9]\d{3}$', code):
        return False, "REGEX_FAIL"
    return True, ""


# =====================================================================================
# 🌐 TWSE / TPEX Fetcher
# =====================================================================================

class TWUniverseFetcher:
    """抓 TWSE + TPEX OpenAPI."""

    def __init__(self):
        self.stats = {"twse_raw": 0, "tpex_raw": 0, "errors": []}

    def _fetch_url(self, url: str, label: str, fb_url: str = None) -> List[Dict]:
        r = _http_get(url)
        if r is None and fb_url:
            print(f"   ⚠ {label} 主 URL 失敗, 嘗試備援 ...")
            r = _http_get(fb_url)
        if r is None:
            self.stats["errors"].append(f"{label}: HTTP all retries failed")
            return []
        try:
            data = r.json()
            if isinstance(data, dict):
                # 有些 API 包在 'data' 鍵裡
                data = data.get('data', [])
            return data if isinstance(data, list) else []
        except Exception as e:
            self.stats["errors"].append(f"{label}: JSON parse fail {str(e)[:80]}")
            return []

    def fetch_twse(self) -> "pd.DataFrame":
        """TWSE 全清單. 欄位: Code, Name."""
        rows = self._fetch_url(TWSE_LISTING_URL, "TWSE", TWSE_LISTING_FB)
        self.stats["twse_raw"] = len(rows)
        if not rows or pd is None:
            return pd.DataFrame(columns=["code", "name", "market"]) if pd is not None else None
        out = []
        for r_ in rows:
            code = str(r_.get("Code", "")).strip()
            name = str(r_.get("Name", "")).strip()
            if code:
                out.append({"code": code, "name": name, "market": "TWSE"})
        return pd.DataFrame(out)

    def fetch_tpex(self) -> "pd.DataFrame":
        """TPEX 全清單. 欄位: SecuritiesCompanyCode, CompanyName."""
        rows = self._fetch_url(TPEX_LISTING_URL, "TPEX", TPEX_LISTING_FB)
        self.stats["tpex_raw"] = len(rows)
        if not rows or pd is None:
            return pd.DataFrame(columns=["code", "name", "market"]) if pd is not None else None
        out = []
        for r_ in rows:
            # TPEX 不同 endpoint 欄位不同
            code = (str(r_.get("SecuritiesCompanyCode", "")).strip()
                    or str(r_.get("CompanyCode", "")).strip()
                    or str(r_.get("Code", "")).strip())
            name = (str(r_.get("CompanyName", "")).strip()
                    or str(r_.get("Name", "")).strip())
            if code:
                out.append({"code": code, "name": name, "market": "TPEX"})
        return pd.DataFrame(out)


# =====================================================================================
# 🔍 Verifier (SSOT regex application + count verification)
# =====================================================================================

class TWUniverseVerifier:
    """套 SSOT regex, 拆 pass/reject, 統計."""

    def __init__(self):
        self.stats = {"start": time.time()}

    def verify(self, df: "pd.DataFrame") -> Dict[str, "pd.DataFrame"]:
        """
        對 raw DataFrame (含 code 欄) 套 SSOT regex.
        回傳:
          - passed:    通過 regex 的 stocks (給 MDL001 用)
          - rejected:  排除清單 + reject_reason
        """
        if pd is None or df is None or df.empty:
            return {"passed": pd.DataFrame() if pd is not None else None,
                    "rejected": pd.DataFrame() if pd is not None else None}
        df = df.copy()
        regex_results = df["code"].apply(lambda c: apply_ssot_regex(c))
        df["passed"] = regex_results.apply(lambda x: x[0])
        df["reject_reason"] = regex_results.apply(lambda x: x[1])
        passed = df[df["passed"]].drop(columns=["passed", "reject_reason"]).reset_index(drop=True)
        rejected = df[~df["passed"]].drop(columns=["passed"]).reset_index(drop=True)
        return {"passed": passed, "rejected": rejected}


# =====================================================================================
# 💾 OutputManager
# =====================================================================================

class OutputManager:
    """Parquet + CSV (utf-8-sig) + JSON 多格式輸出."""

    def __init__(self):
        self.output_dir = Path(BASE_DIR) / OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}

    def save(self, name: str, df: "pd.DataFrame") -> Dict:
        if pd is None or df is None or df.empty:
            self.results[name] = {"rows": 0, "outputs": []}
            return self.results[name]
        outputs = []
        if OUTPUT_PARQUET and PYARROW_AVAILABLE:
            p = self.output_dir / f"{name}.parquet"
            try:
                df.to_parquet(p, index=False)
                outputs.append({"format": "parquet", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "parquet", "error": str(e)[:80]})
        if OUTPUT_CSV:
            p = self.output_dir / f"{name}.csv"
            try:
                df.to_csv(p, index=False, encoding=CSV_ENCODING)
                outputs.append({"format": "csv", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "csv", "error": str(e)[:80]})
        if OUTPUT_JSON:
            p = self.output_dir / f"{name}.json"
            try:
                df.to_json(p, orient="records", indent=2, force_ascii=False)
                outputs.append({"format": "json", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "json", "error": str(e)[:80]})
        self.results[name] = {"rows": len(df), "outputs": outputs}
        return self.results[name]


# =====================================================================================
# 🎯 Main pipeline
# =====================================================================================

def run_verify(dryrun: bool = False) -> int:
    """主入口."""
    t0 = time.time()

    if RICH_AVAILABLE:
        console.print(Panel(
            f"[bold]MDL001 TW Universe Verifier · v1.0.0[/bold]\n\n"
            f"SSOT regex: [cyan]{TW_TICKER_REGEX}[/cyan]\n"
            f"TWSE API  : {TWSE_LISTING_URL}\n"
            f"TPEX API  : {TPEX_LISTING_URL}\n"
            f"輸出      : {Path(BASE_DIR) / OUTPUT_DIR}\n"
            f"模式      : {'DRY-RUN (regex 自測, 不抓網)' if dryrun else 'LIVE FETCH'}",
            title="[bold blue]🇹🇼 TW Stock Universe Verification[/bold blue]",
            border_style="blue"))
    else:
        print(f"== TW Universe Verifier == mode={'dryrun' if dryrun else 'live'}")

    # ── 1. Fetch (or generate mock) ──
    if dryrun:
        print("\n🧪 步驟 1/3: DRY-RUN · 用合成樣本測 SSOT regex")
        # 合成 sample: 5 TWSE 個股 + 3 TWSE ETF + 3 年份 + 5 TPEX 個股 + 2 邊界
        df_twse_raw = pd.DataFrame([
            {"code": "2330", "name": "台積電",      "market": "TWSE"},
            {"code": "2317", "name": "鴻海",        "market": "TWSE"},
            {"code": "2454", "name": "聯發科",      "market": "TWSE"},
            {"code": "1301", "name": "台塑",        "market": "TWSE"},
            {"code": "6505", "name": "台塑化",      "market": "TWSE"},
            {"code": "0050", "name": "元大台灣50",   "market": "TWSE"},  # ETF · reject
            {"code": "0056", "name": "元大高股息",   "market": "TWSE"},  # ETF · reject
            {"code": "00878","name": "國泰永續高股息","market": "TWSE"}, # ETF 5碼 · reject
            {"code": "2025", "name": "千興",        "market": "TWSE"},  # 年份-like · reject (SSOT 鎖)
            {"code": "2027", "name": "大成鋼",      "market": "TWSE"},  # 年份-like · reject (SSOT 鎖)
            {"code": "2030", "name": "彰源",        "market": "TWSE"},  # 年份-like · reject (SSOT 鎖)
            {"code": "ABCD", "name": "亂碼",        "market": "TWSE"},  # 非數字 · reject
        ])
        df_tpex_raw = pd.DataFrame([
            {"code": "6415", "name": "矽力-KY",     "market": "TPEX"},
            {"code": "3324", "name": "雙鴻",        "market": "TPEX"},
            {"code": "5483", "name": "中美晶",      "market": "TPEX"},
            {"code": "6488", "name": "環球晶",      "market": "TPEX"},
            {"code": "8069", "name": "元太",        "market": "TPEX"},
            {"code": "00679B","name":"元大美債20年", "market": "TPEX"}, # ETF · reject
        ])
        twse_raw_n, tpex_raw_n = len(df_twse_raw), len(df_tpex_raw)
        print(f"   ✓ TWSE 合成: {twse_raw_n} 筆")
        print(f"   ✓ TPEX 合成: {tpex_raw_n} 筆")
        fetch_errors = []
    else:
        print("\n🌐 步驟 1/3: 從官方 OpenAPI 抓 TWSE + TPEX 全清單")
        fetcher = TWUniverseFetcher()
        df_twse_raw = fetcher.fetch_twse()
        df_tpex_raw = fetcher.fetch_tpex()
        twse_raw_n = len(df_twse_raw) if df_twse_raw is not None else 0
        tpex_raw_n = len(df_tpex_raw) if df_tpex_raw is not None else 0
        fetch_errors = fetcher.stats.get("errors", [])
        print(f"   ✓ TWSE 抓回: {twse_raw_n:,} 筆")
        print(f"   ✓ TPEX 抓回: {tpex_raw_n:,} 筆")
        for e in fetch_errors: print(f"   ⚠ {e}")

    # ── 2. Apply SSOT regex ──
    print("\n🔍 步驟 2/3: 套 SSOT regex 過濾 + 拆 pass/reject")
    verifier = TWUniverseVerifier()
    twse_res = verifier.verify(df_twse_raw)
    tpex_res = verifier.verify(df_tpex_raw)

    twse_pass = twse_res["passed"];     twse_rej = twse_res["rejected"]
    tpex_pass = tpex_res["passed"];     tpex_rej = tpex_res["rejected"]

    print(f"   ✓ TWSE PASS: {len(twse_pass):,}  ·  REJECT: {len(twse_rej):,}")
    print(f"   ✓ TPEX PASS: {len(tpex_pass):,}  ·  REJECT: {len(tpex_rej):,}")

    # 合併 universe
    combined_pass = pd.concat([twse_pass, tpex_pass], ignore_index=True) if pd is not None else None
    combined_rej  = pd.concat([twse_rej,  tpex_rej],  ignore_index=True) if pd is not None else None

    # ── 3. Save ──
    print("\n💾 步驟 3/3: 多格式輸出 (Parquet + CSV utf-8-sig + JSON)")
    mgr = OutputManager()
    save_results = {}
    if pd is not None:
        save_results["twse_universe"]         = mgr.save("twse_universe", twse_pass)
        save_results["tpex_universe"]         = mgr.save("tpex_universe", tpex_pass)
        save_results["tw_universe_combined"]  = mgr.save("tw_universe_combined", combined_pass)
        save_results["tw_universe_rejected"]  = mgr.save("tw_universe_rejected", combined_rej)
    for tbl, info in save_results.items():
        fmts = [o.get("format") for o in info.get("outputs", []) if "error" not in o]
        print(f"   ✓ {tbl:<26} → {info['rows']:>6,} 列  [{' · '.join(fmts)}]")

    # JSON verify report
    report = {
        "version": "1.0.0",
        "ts": datetime.now().isoformat(timespec='seconds'),
        "ssot_regex": TW_TICKER_REGEX,
        "mode": "dryrun" if dryrun else "live",
        "twse": {
            "raw": twse_raw_n,
            "passed": len(twse_pass),
            "rejected": len(twse_rej),
            "reject_breakdown": twse_rej["reject_reason"].value_counts().to_dict() if not twse_rej.empty else {},
        },
        "tpex": {
            "raw": tpex_raw_n,
            "passed": len(tpex_pass),
            "rejected": len(tpex_rej),
            "reject_breakdown": tpex_rej["reject_reason"].value_counts().to_dict() if not tpex_rej.empty else {},
        },
        "combined": {
            "passed": len(combined_pass) if combined_pass is not None else 0,
            "rejected": len(combined_rej) if combined_rej is not None else 0,
        },
        "fetch_errors": fetch_errors if not dryrun else [],
        "elapsed_sec": round(time.time() - t0, 3),
    }
    rep_path = mgr.output_dir / "verify_report.json"
    rep_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str),
                        encoding='utf-8')

    # ── Rich Summary Matrix ──
    print_summary_matrix(report, twse_pass, tpex_pass, combined_rej, mgr, save_results)
    print(f"\n🎉 完成! 報告: {rep_path}")
    return 0


# =====================================================================================
# 🎨 Rich Summary Matrix
# =====================================================================================

def print_summary_matrix(report, twse_pass, tpex_pass, combined_rej, mgr, save_results):
    if not RICH_AVAILABLE:
        return _print_plain(report)

    console.rule("[bold cyan]🇹🇼 TW Universe Verification · Summary Matrix[/bold cyan]")

    # ─ Table 1: 抓取結果驗證 ─
    t = Table(title="📊 [bold]TWSE / TPEX 數量驗證矩陣[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("市場",     style="cyan",  width=10)
    t.add_column("Raw 抓回", style="yellow", width=12, justify="right")
    t.add_column("PASS",    style="green",  width=10, justify="right")
    t.add_column("REJECT",  style="red",    width=10, justify="right")
    t.add_column("通過率",   style="yellow", width=10, justify="right")
    t.add_column("狀態",     style="green",  width=20)

    twse = report["twse"]; tpex = report["tpex"]
    twse_pct = (twse["passed"]/twse["raw"]*100) if twse["raw"] else 0
    tpex_pct = (tpex["passed"]/tpex["raw"]*100) if tpex["raw"] else 0
    t.add_row("TWSE",  f"{twse['raw']:,}",  f"{twse['passed']:,}",
              f"{twse['rejected']:,}",  f"{twse_pct:.1f}%",
              ("✅ 抓取成功" if twse['raw'] > 100 else
               "⚠️ 抓取少量" if twse['raw'] > 0 else "❌ 抓取失敗"))
    t.add_row("TPEX",  f"{tpex['raw']:,}",  f"{tpex['passed']:,}",
              f"{tpex['rejected']:,}",  f"{tpex_pct:.1f}%",
              ("✅ 抓取成功" if tpex['raw'] > 100 else
               "⚠️ 抓取少量" if tpex['raw'] > 0 else "❌ 抓取失敗"))
    t.add_row("合計",  f"{twse['raw']+tpex['raw']:,}",
              f"{report['combined']['passed']:,}",
              f"{report['combined']['rejected']:,}",
              f"{(report['combined']['passed']/(twse['raw']+tpex['raw'])*100) if (twse['raw']+tpex['raw']) else 0:.1f}%",
              "—")
    console.print(t)

    # ─ Table 2: Reject reason breakdown ─
    if combined_rej is not None and not combined_rej.empty:
        t = Table(title="🚫 [bold]Reject Reason 分類 (SSOT regex 拆解)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Reject 原因",   style="cyan",   width=22)
        t.add_column("數量",          style="red",    width=8, justify="right")
        t.add_column("說明",          style="yellow", width=40)
        t.add_column("範例 codes",    style="green",  width=24)
        reasons_help = {
            "LEADING_ZERO_ETF":      "ETF 首位為 0 (0050, 00878)",
            "YEAR_LIKE_2021_2029":   "年份 2021-2029 (SSOT 鎖排除)",
            "YEAR_LIKE_2030":        "年份 2030 (SSOT 鎖排除)",
            "NON_DIGIT":             "非純數字 (包含字母/特殊字元)",
            "NON_4DIGIT":            "非 4 位數",
            "EMPTY":                 "空字串",
            "REGEX_FAIL":            "其他正則表達式失敗",
        }
        for reason, cnt in combined_rej["reject_reason"].value_counts().items():
            sample_codes = combined_rej[combined_rej["reject_reason"]==reason]["code"].head(3).tolist()
            t.add_row(reason, str(cnt), reasons_help.get(reason, "—"),
                      ", ".join(sample_codes))
        console.print(t)

    # ─ Table 3: 通過樣本 (TWSE) ─
    if pd is not None and twse_pass is not None and not twse_pass.empty:
        t = Table(title=f"📈 [bold]TWSE 通過樣本 (顯示前 8 筆)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Code",   style="cyan",   width=10)
        t.add_column("Name",   style="yellow", width=30)
        t.add_column("Market", style="green",  width=10)
        for _, r_ in twse_pass.head(8).iterrows():
            t.add_row(str(r_['code']), str(r_.get('name','')), str(r_.get('market','')))
        console.print(t)

    # ─ Table 4: 通過樣本 (TPEX) ─
    if pd is not None and tpex_pass is not None and not tpex_pass.empty:
        t = Table(title=f"📊 [bold]TPEX 通過樣本 (顯示前 8 筆)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Code",   style="cyan",   width=10)
        t.add_column("Name",   style="yellow", width=30)
        t.add_column("Market", style="green",  width=10)
        for _, r_ in tpex_pass.head(8).iterrows():
            t.add_row(str(r_['code']), str(r_.get('name','')), str(r_.get('market','')))
        console.print(t)

    # ─ Table 5: 輸出 ─
    t = Table(title="💾 [bold]輸出檔案明細[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("檔名",     style="cyan",   width=26)
    t.add_column("列數",     style="green",  width=10, justify="right")
    t.add_column("Parquet",  style="yellow", width=10, justify="center")
    t.add_column("CSV",      style="yellow", width=10, justify="center")
    t.add_column("JSON",     style="yellow", width=10, justify="center")
    for tbl, info in save_results.items():
        fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                for o in info.get("outputs", [])}
        t.add_row(tbl, f"{info['rows']:,}",
                  fmts.get("parquet", "—"), fmts.get("csv", "—"),
                  fmts.get("json", "—"))
    console.print(t)

    # ─ Final panel ─
    twse_pct = (report['twse']['passed']/report['twse']['raw']*100) if report['twse']['raw'] else 0
    tpex_pct = (report['tpex']['passed']/report['tpex']['raw']*100) if report['tpex']['raw'] else 0
    summary = (
        f"[bold]SSOT regex[/bold]      : [cyan]{TW_TICKER_REGEX}[/cyan]\n"
        f"[bold]TWSE 上市公司[/bold]    : [green]{report['twse']['passed']:,}[/green] 檔 / "
        f"{report['twse']['raw']:,} raw ({twse_pct:.1f}%)\n"
        f"[bold]TPEX 上櫃公司[/bold]    : [green]{report['tpex']['passed']:,}[/green] 檔 / "
        f"{report['tpex']['raw']:,} raw ({tpex_pct:.1f}%)\n"
        f"[bold]合計 TW Universe[/bold] : [bold green]{report['combined']['passed']:,}[/bold green] 檔可餵 MDL001 引擎\n"
        f"[bold]排除[/bold]            : [red]{report['combined']['rejected']:,}[/red] 檔 "
        f"(ETF/年份/非格式)\n"
        f"[bold]耗時[/bold]            : {report['elapsed_sec']} 秒"
    )
    console.print(Panel.fit(summary, title="[bold cyan]🎯 整體驗證結果[/bold cyan]",
                            border_style="cyan"))


def _print_plain(report):
    print("\n" + "=" * 70)
    print("TW Universe Verification Summary")
    print("=" * 70)
    print(f"  SSOT regex : {TW_TICKER_REGEX}")
    print(f"  TWSE       : {report['twse']['passed']:,} / {report['twse']['raw']:,} raw")
    print(f"  TPEX       : {report['tpex']['passed']:,} / {report['tpex']['raw']:,} raw")
    print(f"  Combined   : {report['combined']['passed']:,} pass · {report['combined']['rejected']:,} reject")
    print(f"  Time       : {report['elapsed_sec']}s")


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7+"); return 1
    print("🚀 VDF MDL001 TW Universe Verifier 啟動...")
    dryrun = "--dryrun" in sys.argv
    return run_verify(dryrun=dryrun)


if __name__ == "__main__":
    try:
        ec = main()
        if "--no-pause" not in sys.argv:
            try: input("\n按 Enter 鍵退出 ...")
            except (EOFError, KeyboardInterrupt): pass
        sys.exit(ec)
    except KeyboardInterrupt:
        print("\n⚠️ 中斷"); sys.exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
