#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0100 — VDF 獨立擷取系統:MDL001–007 核心擷取引擎(舊模組原件)經 VDF 管理員一條路跑

操作員 2026-10-03:「VDF 只有生成資料庫功能,沒有分析功能」「只留擷取」「根據舊的檔案每個引擎擷取功能」
「先拿舊模組用 vdf manager 建立獨立擷取系統」「MDL 核心擷取引擎:依 VDF_MDL000_README.md(2026-06-04 編號表),001–099 才是
資料引擎」「整合測試輸出成功」。

本支 = 子系統大引擎(MDL;小功能指令才用 ENG),只做「系統」那一層,七支舊模組一個位元組都不改(凍結原件;同 ENG230 先例:只載入、在記憶體裡補丁):
  ① 冊:VDF_FetchSystem_SSOT_v0100.json(MDL001–007 正本檔 · 擷取函式 AST 定位 · 啟動參數 · 相依 · 輸出契約)。
  ② 路徑:原件寫死工作站舊佈局 C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\…\\dict(實測在 Linux 變成倉內怪名資料夾,
     MDL007 又因「資料夾在就當正式路徑」跟著寫進去)→ 執行前在 AST 裡把這些常數改指本系統輸出根(VIA_VDF_FETCH_HOME;
     沒設 = VIA_Reports/vdf_fetch/dict,整夾不入 git)。
  ③ 兩段執行:先跑模組本體(不含 __main__ 段)→ 換網路入口 → 再跑 __main__ 段(原件的旗標 · 自測動詞 · governed 入口照舊)。
  ④ 網路三態:
       live    真網路;**系統層同意閘**:VIA_NET_CONSENT 必須是 YES(操作員的手;本支只讀不寫,AI 永不代設)→ 否則 rc4 GATED、零子行程。
               (原件 MDL001 / 005 / 007 自己沒有閘,實測 007 的 --selftest 會直接上 Yahoo 抓 —— 系統層把它們一起擋住。)
       fixture 離線整合測試網:requests 的 Session.request · yfinance · 統包網路工具全換成固定樣本(TWSE / TPEX OpenAPI 欄位照官方形狀,
               中英文鍵都給);閘回「FIXTURE 模擬」(各引擎自測用的同一個模擬縫,不讀不寫環境變數);socket · urllib · curl_cffi 全封。
       block   全封(實測 socket 封不住 yfinance —— 它走 curl_cffi 的 C 層;所以在模組層封)。
  ⑤ 輸出契約:每支該產哪些檔(相對輸出根),verify 逐檔查在 · 非空 · 列數。
動詞:list | plan [MDL…] | run [MDL…] [--apply] [--mode live|fixture|block] [--home 夾] | verify [MDL…] [--home 夾] | test | --selftest
只收 VCGC 呼叫(VIA_FROM_VCGC=YES);不碰 TA-Lib;不代設同意閘;不代裝套件(缺件 = 原件自己誠實回 NODATA / rc3)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import types
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # functional modules/VDF(MDL 大引擎放子系統根)
VDF_DIR = HERE
VIA = HERE.parents[1]                                  # VeritasIntelligenceAnalytics
REPO = VIA.parent
TAG = "VDF_MDL008_FetchSystem v" + Path(__file__).stem.rsplit("_v", 1)[-1]
BOOK = VDF_DIR / "VDF_FetchSystem_SSOT_v0100.json"
DEFAULT_HOME = VIA / "VIA_Reports" / "vdf_fetch" / "dict"
LEGACY_PREFIXES = (r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict",
                   r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\dict")
MODES = ("live", "fixture", "block")
CHILD_TIMEOUT_S = 1800


# ---------------------------------------------------------------- 冊
def load_book(path: Path = BOOK) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def entries(book: dict, wanted=None) -> list:
    rows = list(book.get("engines") or [])
    if not wanted:
        return rows
    keys = {str(w).upper().replace("VDF_", "") for w in wanted}
    return [r for r in rows if r["id"].upper() in keys or r["mdl"].upper() in keys]


def unknown_ids(book: dict, wanted) -> list:
    have = {r["id"].upper() for r in book.get("engines") or []} | {r["mdl"].upper() for r in book.get("engines") or []}
    return [w for w in (wanted or []) if str(w).upper().replace("VDF_", "") not in have]


def ordered(rows: list) -> list:
    """依 needs 拓撲排序(同層照冊序);有環 = ValueError(冊錯,不猜)。"""
    by = {r["id"]: r for r in rows}
    done, out = set(), []
    pending = list(rows)
    while pending:
        progressed = False
        for r in list(pending):
            if all(n in done or n not in by for n in r.get("needs") or []):
                out.append(r)
                done.add(r["id"])
                pending.remove(r)
                progressed = True
        if not progressed:
            raise ValueError("FETCH_BOOK_CYCLE: " + ",".join(r["id"] for r in pending))
    return out


def home_dir(arg: str | None = None) -> Path:
    return Path(arg or os.environ.get("VIA_VDF_FETCH_HOME") or DEFAULT_HOME)


# ---------------------------------------------------------------- 路徑改寫 + 兩段編譯
def _is_main_guard(node) -> bool:
    t = getattr(node, "test", None)
    return (isinstance(node, ast.If) and isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
            and t.left.id == "__name__" and any(isinstance(c, ast.Constant) and c.value == "__main__" for c in t.comparators))


def compile_engine(path: Path, home: Path):
    """回 (本體碼, __main__ 段碼, 改寫筆數)。只動記憶體裡的 AST:舊佈局絕對路徑常數 → 輸出根下同一相對位置。"""
    src = Path(path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src, filename=str(path))
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for pre in LEGACY_PREFIXES:
                if node.value.startswith(pre):
                    rest = [p for p in node.value[len(pre):].replace("\\", "/").split("/") if p]
                    node.value = str(Path(home, *rest))
                    n += 1
                    break
    body = [s for s in tree.body if not _is_main_guard(s)]
    mains = [s for s in tree.body if _is_main_guard(s)]
    mk = lambda stmts: compile(ast.Module(body=stmts, type_ignores=[]), str(path), "exec")  # noqa: E731
    return mk(body), mk(mains), n


# ---------------------------------------------------------------- 離線整合測試網(fixture)
FIX_TWSE = [("2330", "台積電", 1000.0), ("2317", "鴻海", 200.0), ("2454", "聯發科", 1300.0), ("1301", "台塑", 45.0),
            ("2881", "富邦金", 90.0), ("0050", "元大台灣50", 190.0)]
FIX_TPEX = [("6488", "環球晶", 400.0), ("3324", "雙鴻", 700.0), ("8069", "元太", 250.0), ("00679B", "元大美債20年", 28.0)]
FIX_STATS = {"requests": 0, "yf": 0, "net": 0, "blocked": 0}


def _roc(d: date) -> str:
    return f"{d.year - 1911}{d.month:02d}{d.day:02d}"


def _num(code: str, lo: float, hi: float) -> float:
    h = int(hashlib.sha256(code.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return round(lo + (hi - lo) * h, 2)


def _fix_route(url: str):
    """URL → 官方 OpenAPI 形狀的固定樣本(中英文鍵都給:各引擎讀的鍵不同)。找不到路由回 None(= 404)。"""
    u = url.lower()
    today = date.today()
    if "openapi.twse.com.tw" in u and ("stock_day_all" in u or "stock_day_avg_all" in u):
        return [{"Date": _roc(today), "Code": c, "Name": n, "TradeVolume": str(int(_num(c, 1e6, 5e7))),
                 "TradeValue": str(int(p * _num(c, 1e6, 5e7))), "OpeningPrice": f"{p:.2f}", "HighestPrice": f"{p * 1.01:.2f}",
                 "LowestPrice": f"{p * 0.99:.2f}", "ClosingPrice": f"{p:.2f}", "Change": "1.50", "Transaction": "12345",
                 "MonthlyAveragePrice": f"{p * 0.98:.2f}",
                 "證券代號": c, "證券名稱": n, "成交股數": str(int(_num(c, 1e6, 5e7))), "成交金額": str(int(p * 1e7)),
                 "開盤價": f"{p:.2f}", "最高價": f"{p * 1.01:.2f}", "最低價": f"{p * 0.99:.2f}", "收盤價": f"{p:.2f}",
                 "漲跌價差": "1.50", "成交筆數": "12345"} for c, n, p in FIX_TWSE]
    if "openapi.twse.com.tw" in u and "bwibbu" in u:
        return [{"Date": _roc(today), "Code": c, "Name": n, "PEratio": f"{_num(c, 8, 30):.2f}", "DividendYield": f"{_num(c, 1, 6):.2f}",
                 "PBratio": f"{_num(c, 1, 6):.2f}", "本益比": f"{_num(c, 8, 30):.2f}", "殖利率(%)": f"{_num(c, 1, 6):.2f}",
                 "股價淨值比": f"{_num(c, 1, 6):.2f}", "證券代號": c, "證券名稱": n} for c, n, _ in FIX_TWSE]
    if "t187ap03_l" in u:
        return [{"出表日期": _roc(today), "公司代號": c, "公司名稱": n + "股份有限公司", "公司簡稱": n, "英文簡稱": "FIX" + c,
                 "產業別": "24", "董事長": "樣本", "住址": "台北市", "實收資本額": str(int(_num(c, 1e9, 3e11))),
                 "已發行普通股數或TDR原股發行股數": str(int(_num(c, 1e8, 3e10))), "已發行普通股數": str(int(_num(c, 1e8, 3e10))),
                 "上市日期": "19940905"} for c, n, _ in FIX_TWSE if len(c) == 4]
    if "tpex.org.tw" in u and ("daily_close_quotes" in u or "peratio" in u):
        return [{"Date": _roc(today), "SecuritiesCompanyCode": c, "CompanyCode": c, "CompanyName": n, "Close": f"{p:.2f}",
                 "Change": "2.00", "Open": f"{p:.2f}", "High": f"{p * 1.02:.2f}", "Low": f"{p * 0.98:.2f}",
                 "TradingShares": str(int(_num(c, 1e5, 9e6))), "TransactionAmount": str(int(p * 1e6)), "TransactionNumber": "2345",
                 "PriceEarningRatio": f"{_num(c, 8, 30):.2f}", "DividendPerShare": "5.0", "YieldRatio": f"{_num(c, 1, 6):.2f}",
                 "PriceBookRatio": f"{_num(c, 1, 6):.2f}"} for c, n, p in FIX_TPEX]
    if "mopsfin_t187ap03_o" in u:
        return [{"SecuritiesCompanyCode": c, "CompanyCode": c, "CompanyName": n + "股份有限公司", "CompanyAbbreviation": n,
                 "公司代號": c, "公司名稱": n + "股份有限公司", "公司簡稱": n, "產業別": "24", "上櫃日期": "20010101",
                 "實收資本額": str(int(_num(c, 1e9, 3e10)))} for c, n, _ in FIX_TPEX if len(c) == 4]
    if "fearandgreed" in u:
        base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        hist = [{"x": int((base - timedelta(days=i)).timestamp() * 1000), "y": 40 + i % 30, "rating": "neutral"} for i in range(60)][::-1]
        return {"fear_and_greed": {"score": 55.0, "rating": "neutral", "timestamp": base.isoformat(), "previous_close": 54.0,
                                   "previous_1_week": 50.0, "previous_1_month": 48.0, "previous_1_year": 60.0},
                "fear_and_greed_historical": {"timestamp": int(base.timestamp() * 1000), "score": 55.0, "rating": "neutral", "data": hist}}
    if "stlouisfed.org" in u:
        return {"observations": [{"date": (today - timedelta(days=30 * i)).isoformat(), "value": f"{4 + i * 0.01:.2f}"} for i in range(24)][::-1]}
    return None


def _install_requests_fixture():
    import requests
    from requests.models import Response

    def fake_request(self, method, url, *a, **k):
        FIX_STATS["requests"] += 1
        data = _fix_route(str(url))
        r = Response()
        r.url, r.encoding = str(url), "utf-8"
        r.status_code = 200 if data is not None else 404
        r.reason = "OK" if data is not None else "FIXTURE_NO_ROUTE"
        r._content = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else b""
        r.headers["Content-Type"] = "application/json"
        return r
    requests.sessions.Session.request = fake_request


def _fix_index(n: int = 40):
    import pandas as pd
    return pd.bdate_range(end=pd.Timestamp(date.today()) - pd.Timedelta(days=1), periods=n)


def _fix_ohlc(sym: str, n: int = 40):
    import numpy as np
    import pandas as pd
    idx = _fix_index(n)
    base = _num(sym, 20, 900)
    close = base * (1 + 0.002 * np.arange(n))
    return pd.DataFrame({"Open": close * 0.995, "High": close * 1.01, "Low": close * 0.99, "Close": close, "Adj Close": close,
                         "Volume": (np.arange(n) + 1) * 1000 + int(_num(sym, 1e5, 1e6)), "Dividends": 0.0, "Stock Splits": 0.0},
                        index=idx.rename("Date"))


def _fake_yfinance():
    import pandas as pd
    yf = types.ModuleType("yfinance")
    yf.__version__ = "0.2.fixture"

    def download(tickers, *a, **k):
        FIX_STATS["yf"] += 1
        syms = tickers.split() if isinstance(tickers, str) else list(tickers)
        frames = {s: _fix_ohlc(s).drop(columns=["Dividends", "Stock Splits"]) for s in syms}
        if len(syms) == 1 and k.get("group_by") != "ticker" and not k.get("multi_level_index", False):
            return frames[syms[0]]
        if k.get("group_by") == "ticker":
            return pd.concat(frames, axis=1)
        return pd.concat(frames, axis=1).swaplevel(0, 1, axis=1).sort_index(axis=1)

    class Ticker:
        def __init__(self, sym, *a, **k):
            FIX_STATS["yf"] += 1
            self.ticker = str(sym)
            p = _num(self.ticker, 20, 900)
            self.info = {"symbol": self.ticker, "shortName": "FIX " + self.ticker, "longName": "Fixture " + self.ticker,
                         "currency": "TWD", "financialCurrency": "TWD", "quoteType": "EQUITY", "sector": "Technology",
                         "industry": "Semiconductors", "currentPrice": p, "regularMarketPrice": p, "previousClose": p * 0.99,
                         "marketCap": int(p * 1e9), "sharesOutstanding": int(1e9), "trailingPE": 18.5, "forwardPE": 16.2,
                         "trailingEps": round(p / 18.5, 2), "forwardEps": round(p / 16.2, 2), "priceToBook": 4.1, "bookValue": round(p / 4.1, 2),
                         "targetMeanPrice": p * 1.15, "targetMedianPrice": p * 1.12, "targetHighPrice": p * 1.4, "targetLowPrice": p * 0.9,
                         "numberOfAnalystOpinions": 21, "recommendationKey": "buy", "recommendationMean": 1.9,
                         "dividendRate": round(p * 0.02, 2), "dividendYield": 2.0, "beta": 1.1,
                         "fiftyTwoWeekHigh": p * 1.2, "fiftyTwoWeekLow": p * 0.8, "averageVolume": 1_000_000, "volume": 900_000}
            self.fast_info = {"last_price": p, "market_cap": int(p * 1e9), "shares": int(1e9), "currency": "TWD"}
            ends = [pd.Timestamp(f"{date.today().year - i}-12-31") for i in range(1, 5)]
            qends = [pd.Timestamp(date.today()) - pd.offsets.QuarterEnd(i) for i in range(1, 5)]

            def stmt(rows, cols, scale):
                return pd.DataFrame({c: [scale * (1 + 0.1 * j) * (k + 1) for k in range(len(rows))] for j, c in enumerate(cols)}, index=rows)
            inc = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "EBITDA", "Diluted EPS", "Basic EPS",
                   "Net Income Common Stockholders"]
            bs = ["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity", "Total Debt", "Current Assets",
                  "Current Liabilities", "Cash And Cash Equivalents", "Ordinary Shares Number", "Common Stock Equity"]
            cf = ["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow", "Cash Dividends Paid"]
            self.income_stmt = self.financials = stmt(inc, ends, 1e9)
            self.balance_sheet = stmt(bs, ends, 2e9)
            self.cashflow = stmt(cf, ends, 5e8)
            self.quarterly_income_stmt = self.quarterly_financials = stmt(inc, qends, 3e8)
            self.quarterly_balance_sheet = stmt(bs, qends, 2e9)
            self.quarterly_cashflow = stmt(cf, qends, 1e8)
            self.earnings_estimate = pd.DataFrame({"avg": [p / 70, p / 68, p / 18, p / 16], "low": [p / 80, p / 75, p / 20, p / 18],
                                                   "high": [p / 60, p / 60, p / 16, p / 14], "yearAgoEps": [p / 75, p / 72, p / 20, p / 18],
                                                   "numberOfAnalysts": [12, 12, 20, 18], "growth": [0.1, 0.1, 0.12, 0.11]},
                                                  index=pd.Index(["0q", "+1q", "0y", "+1y"], name="period"))
            self.dividends = pd.Series([p * 0.01, p * 0.01], index=_fix_index(2), name="Dividends")
            self.recommendations = pd.DataFrame()

        def history(self, *a, **k):
            return _fix_ohlc(self.ticker)

        def get_info(self):
            return self.info

    class Tickers:
        def __init__(self, syms, *a, **k):
            self.tickers = {s: Ticker(s) for s in (syms.split() if isinstance(syms, str) else syms)}

    yf.download, yf.Ticker, yf.Tickers = download, Ticker, Tickers
    yf.set_tz_cache_location = lambda *a, **k: None
    yf.enable_debug_mode = lambda *a, **k: None
    return yf


class _FakeNet(types.ModuleType):
    """統包網路工具的 fixture 替身:閘回 FIXTURE 模擬(不讀不寫環境變數),資料走同一套路由。"""

    def __init__(self, open_: bool):
        super().__init__("VIA_NET_UNIFIED_FIXTURE")
        self._open = open_

    def gate_state(self):
        return {"open": self._open, "gate1_net_consent": self._open, "gate2_scrape_consent": self._open,
                "gate1_raw": "FIXTURE(模擬;未讀未寫環境變數)" if self._open else "BLOCK"}

    def http_json(self, url, *a, **k):
        FIX_STATS["net"] += 1
        if not self._open:
            FIX_STATS["blocked"] += 1
            return {"state": "DENY", "note": "BLOCK"}
        data = _fix_route(str(url))
        return {"state": "OK", "data": data} if data is not None else {"state": "FAIL", "note": "FIXTURE_NO_ROUTE"}

    def yahoo_quote_summary_raw(self, syms, modules="financialData", *a, **k):
        FIX_STATS["net"] += 1
        if not self._open:
            FIX_STATS["blocked"] += 1
            return {"state": "DENY"}
        res = {}
        for s in (syms if isinstance(syms, (list, tuple)) else [syms]):
            info = _fake_yfinance().Ticker(s).info
            res[s] = {"financialData": {k: {"raw": info[k]} for k in ("targetMeanPrice", "targetMedianPrice", "targetHighPrice",
                                                                       "targetLowPrice", "numberOfAnalystOpinions", "currentPrice")}
                      | {"recommendationKey": info["recommendationKey"]}}
        return {"state": "OK", "results": res}

    def __getattr__(self, name):
        def nope(*a, **k):
            FIX_STATS["blocked"] += 1
            raise RuntimeError("FIXTURE_NET_NO_ROUTE:" + name)
        return nope


def _install_block_sockets():
    import socket
    import urllib.request

    def deny(*a, **k):
        FIX_STATS["blocked"] += 1
        raise OSError("VDF_FETCH_NET_BLOCKED")
    socket.socket.connect = deny
    socket.create_connection = deny
    urllib.request.urlopen = deny
    cc = types.ModuleType("curl_cffi")
    cc.__getattr__ = lambda name: deny                                   # yfinance 的 C 層出口:模組層封
    sys.modules["curl_cffi"] = cc
    sys.modules["curl_cffi.requests"] = cc


def _install_live_routes(nt) -> None:
    """live:原件直呼的 requests / yfinance / akshare 全收進鎖版網路工具(L20 唯一出口)。
    requests → nt.http_bytes(GET)/ nt.post_json(POST);yfinance / akshare → 先問 nt 雙閘才放行(同工具 ④ 道語意)。"""
    import requests
    from requests.models import Response

    def via_tool(self, method, url, *a, **k):
        from urllib.parse import urlencode
        params = k.get("params")
        full = str(url) + (("&" if "?" in str(url) else "?") + urlencode(params, doseq=True) if params else "")
        if str(method).upper() == "POST":
            r0 = nt.post_json(full, payload=k.get("json", k.get("data")), headers=k.get("headers"), timeout=int(k.get("timeout") or 30))
        else:
            r0 = nt.http_bytes(full, timeout=int(k.get("timeout") or 30), headers=k.get("headers"))
        st = str((r0 or {}).get("state") or "")
        if st == "DENY":
            raise requests.exceptions.ConnectionError("GATED:鎖版網路工具雙閘未開(不是壞掉)")
        r = Response()
        r.url, r.encoding = full, None
        data = (r0 or {}).get("data")
        r._content = data if isinstance(data, (bytes, bytearray)) else (json.dumps(data, ensure_ascii=False).encode("utf-8")
                                                                       if isinstance(data, (dict, list)) else str(data or "").encode("utf-8"))
        r.status_code = 200 if st == "OK" else (404 if st == "EMPTY" else 502)
        r.reason = st or "FAIL"
        return r
    requests.sessions.Session.request = via_tool

    def gated(real, name):
        def call(*a, **k):
            if not (nt.gate_state() or {}).get("open"):
                raise RuntimeError(f"GATED:{name} 要鎖版網路工具雙閘(不是壞掉)")
            return real(*a, **k)
        return call
    for mod_name, attrs in (("yfinance", ("download", "Ticker", "Tickers")), ("akshare", ())):
        try:
            real_mod = __import__(mod_name)
        except ImportError:
            continue
        proxy = types.ModuleType(mod_name)
        proxy.__dict__.update({k: v for k, v in vars(real_mod).items() if not k.startswith("__")})
        for a in attrs or [k for k, v in vars(real_mod).items() if callable(v) and not k.startswith("_")]:
            if hasattr(real_mod, a):
                setattr(proxy, a, gated(getattr(real_mod, a), f"{mod_name}.{a}"))
        sys.modules[mod_name] = proxy


def install_mode(mode: str) -> object | None:
    """回替身網路工具(None = 不換;live 用鎖版真工具)。"""
    if mode == "live":
        nt = _via_net()
        if nt is None:
            raise RuntimeError("ABSENT:鎖版網路工具載不到(supportive modules/network → SUP_MDL740 → 鎖冊 network)")
        _install_live_routes(nt)
        return None
    _install_block_sockets()
    if mode == "fixture":
        _install_requests_fixture()
        sys.modules["yfinance"] = _fake_yfinance()
        return _FakeNet(True)
    import requests

    def deny_req(self, *a, **k):
        FIX_STATS["blocked"] += 1
        raise requests.exceptions.ConnectionError("VDF_FETCH_NET_BLOCKED")
    requests.sessions.Session.request = deny_req
    yf = types.ModuleType("yfinance")

    def yf_deny(*a, **k):
        FIX_STATS["blocked"] += 1
        raise RuntimeError("VDF_FETCH_NET_BLOCKED")
    yf.download, yf.Ticker, yf.Tickers = yf_deny, yf_deny, yf_deny
    sys.modules["yfinance"] = yf
    return _FakeNet(False)


# ---------------------------------------------------------------- 子行程:跑一支
def child(eid: str, home: str, mode: str, argv: list) -> int:
    row = next(r for r in load_book()["engines"] if r["id"] == eid)
    path = VDF_DIR / row["file"]
    home_p = Path(home)
    home_p.mkdir(parents=True, exist_ok=True)
    os.chdir(home_p)
    body, mains, n = compile_engine(path, home_p)
    if mode == "live" and not gate_open():
        print(f"[MDL008] {row['mdl']} GATED:鎖版網路工具雙閘未開 —— 零出網、零寫檔(不是壞掉)", flush=True)
        return 4
    fake = install_mode(mode)
    sys.argv = [str(path), *argv]
    sys.path.insert(0, str(path.parent))
    g = {"__name__": "__vdf_fetch_body__", "__file__": str(path), "__builtins__": __builtins__}
    print(f"[MDL008] {row['mdl']} {row['file']} · 舊路徑改寫 {n} 處 → {home_p} · 網路 {mode}", flush=True)
    rc = 0
    try:
        exec(body, g)
        if fake is not None:
            g["_via_net"] = lambda: fake                                   # 統包工具入口換成替身
        g["__name__"] = "__main__"
        exec(mains, g)
        if row.get("call_after_body") and callable(g.get(row["call_after_body"])):
            rc = g[row["call_after_body"]]() or 0
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code in (None, "") else 1)
    except Exception as e:                                                # 原件例外照實回 1(不吞)
        print(f"[MDL008] 例外 {type(e).__name__}: {e}", flush=True)
        rc = 1
    print(f"[MDL008] {row['mdl']} rc={rc} · 網路計數 {json.dumps(FIX_STATS, ensure_ascii=False)}", flush=True)
    return rc


# ---------------------------------------------------------------- 父行程:計畫 · 執行 · 驗收
def plan(rows: list, mode: str, home: Path) -> list:
    return [{"id": r["id"], "mdl": r["mdl"], "file": r["file"], "args": r["run_args"], "needs": r.get("needs") or [],
             "outputs": [o["path"] for o in r.get("outputs") or []],
             "cmd": f"via-vdfsys fetch run {r['id']} --apply --mode {mode}"} for r in ordered(rows)]


def gate_open() -> bool:
    """live 閘 = 鎖版網路工具的雙閘(gate_state()["open"]:VIA_NET_CONSENT=YES 且 VIA_SCRAPE_CONSENT 有效)。
    只讀;AI 永不代設。工具缺席 = 關(誠實,不退回自己讀環境變數)。"""
    nt = _via_net()
    try:
        return bool(nt is not None and (nt.gate_state() or {}).get("open"))
    except Exception:
        return False


def run(rows: list, mode: str, home: Path, logs: Path | None = None, timeout: int = CHILD_TIMEOUT_S, args_key: str = "run_args") -> list:
    logs = logs or (home.parent / "_logs")
    logs.mkdir(parents=True, exist_ok=True)
    out = []
    for r in ordered(rows):
        log = logs / f"{r['id']}_{mode}.log"
        t0 = time.time()
        env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONIOENCODING="utf-8")
        try:
            p = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__)), "_child", r["id"], str(home), mode, "--",
                                *r.get(args_key, [])], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env, cwd=str(home.parent))
            rc, txt = p.returncode, p.stdout
        except subprocess.TimeoutExpired as e:
            rc, txt = 124, (e.stdout or "") if isinstance(e.stdout, str) else ""
        log.write_text(txt, encoding="utf-8")
        tail = [ln for ln in txt.splitlines() if ln.strip()][-3:]
        out.append({"id": r["id"], "mdl": r["mdl"], "rc": rc, "sec": round(time.time() - t0, 1), "log": str(log), "tail": tail})
    return out


def verify(rows: list, home: Path) -> list:
    res = []
    for r in rows:
        for o in r.get("outputs") or []:
            p = home / o["path"]
            row = {"id": r["id"], "path": o["path"], "exists": p.is_file(), "bytes": p.stat().st_size if p.is_file() else 0, "rows": None}
            if p.is_file() and p.suffix in (".parquet", ".csv"):
                try:
                    import pandas as pd
                    df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
                    row["rows"] = len(df)
                    row["cols"] = len(df.columns)
                except Exception as e:
                    row["err"] = type(e).__name__
            elif p.is_file() and p.suffix == ".json":
                try:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    row["rows"] = len(d) if isinstance(d, (list, dict)) else 1
                except Exception as e:
                    row["err"] = type(e).__name__
            row["ok"] = row["exists"] and row["bytes"] > 0 and (row["rows"] is None or row["rows"] >= o.get("min_rows", 1)) and "err" not in row
            res.append(row)
    return res


def _git_dirty() -> set:
    p = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True)
    return set(p.stdout.splitlines()) if p.returncode == 0 else set()


def integration_test(rows: list | None = None, rounds: int = 1) -> dict:
    """離線整合測試:fixture 網跑 MDL001–007 全鏈 → 輸出契約逐檔驗 → 倉內零寫入;block 網再驗 007 零出網。"""
    book = load_book()
    rows = rows or book["engines"]
    before = _git_dirty()
    report = {"rounds": []}
    for k in range(rounds):
        with tempfile.TemporaryDirectory(prefix="vdf_fetch_it_") as tmp:
            home = Path(tmp) / "dict"
            runs = run(rows, "fixture", home, logs=Path(tmp) / "_logs", timeout=900)
            ver = verify(rows, home)
            blk = run([r for r in book["engines"] if r["id"] == "007"], "block", Path(tmp) / "block_dict", logs=Path(tmp) / "_logs", timeout=300)
            blk_log = Path(blk[0]["log"]).read_text(encoding="utf-8") if blk else ""
            m = re.search(r'"blocked": (\d+)', blk_log)
            report["rounds"].append({"runs": runs, "verify": ver, "block": {"rc": blk[0]["rc"] if blk else None,
                                                                            "blocked": int(m.group(1)) if m else 0,
                                                                            "yf_ok_line": "YF: " in blk_log and " ok /" in blk_log and not re.search(r"YF: 0 ok", blk_log)}})
    # 只算擷取引擎可能寫到的地方:VDF 子系統夾 · 舊佈局路徑在 Linux 變出的怪名夾(C:\…)。其他行程同時寫的冊(VCGC 紀錄冊等)不算。
    leaked = sorted(x for x in _git_dirty() - before if "functional modules/VDF/" in x or "C:\\" in x or "C:\\\\" in x)
    report["repo_writes"] = leaked
    rr = report["rounds"]
    report["pass"] = all(all(x["rc"] in r_.get("ok_rcs", (0,)) for x, r_ in zip(rd["runs"], ordered(rows))) and all(v["ok"] for v in rd["verify"])
                         and rd["block"]["blocked"] > 0 for rd in rr) and not leaked
    return report


# ---------------------------------------------------------------- CLI
def _print_runs(runs: list) -> None:
    for x in runs:
        print(f"  [{'OK' if x['rc'] == 0 else 'rc' + str(x['rc'])}] {x['mdl']:7} {x['sec']:6.1f}s · {(x['tail'] or [''])[-1][:110]}")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["_child"]:
        i = args.index("--") if "--" in args else len(args)
        eid, home, mode = args[1], args[2], args[3]
        return child(eid, home, mode, args[i + 1:])
    if args == ["--selftest"]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF_MDL008] 拒絕。只能經 via-vcgc(via-vdfsys fetch …)。")
        return 2
    verb = args[0] if args else "list"
    rest = args[1:]
    as_json = "--json" in rest
    home = home_dir(rest[rest.index("--home") + 1] if "--home" in rest and rest.index("--home") + 1 < len(rest) else None)
    mode = rest[rest.index("--mode") + 1] if "--mode" in rest and rest.index("--mode") + 1 < len(rest) else "live"
    ids = [a for i, a in enumerate(rest) if not a.startswith("--") and (i == 0 or rest[i - 1] not in ("--home", "--mode"))]
    book = load_book()
    bad = unknown_ids(book, ids)
    if verb not in ("list", "plan", "run", "verify", "test"):
        print(f"[拒跑] {TAG}:未知動詞 '{verb}'(已知:list · plan · run · verify · test · --selftest)")
        return 2
    if bad:
        print(f"[拒跑] {TAG}:冊上沒有 {' '.join(bad)}(MDL001–007:{' · '.join(r['id'] for r in book['engines'])})")
        return 2
    if mode not in MODES:
        print(f"[拒跑] {TAG}:--mode 只收 {' · '.join(MODES)}")
        return 2
    rows = entries(book, ids)
    if verb == "list":
        out = [{"id": r["id"], "mdl": r["mdl"], "role": r["role"], "file": r["file"], "exists": (VDF_DIR / r["file"]).is_file(),
                "fetch_functions": len(r.get("fetch_functions") or []), "outputs": len(r.get("outputs") or [])} for r in rows]
        if as_json:
            print(json.dumps({"vdf_fetch_system": out, "home": str(home)}, ensure_ascii=False))
        else:
            print(f"[VDF 擷取系統] 冊 {BOOK.name} · 輸出根 {home} · MDL001–007 共 {len(out)} 支")
            for o in out:
                print(f"  {'✓' if o['exists'] else '✗'} {o['mdl']:7} {o['role'][:34]:34} 擷取函式 {o['fetch_functions']:2} · 輸出 {o['outputs']} 檔 · {o['file']}")
        return 0 if all(o["exists"] for o in out) else 1
    if verb == "plan" or (verb == "run" and "--apply" not in rest):
        pl = plan(rows, mode, home)
        print(json.dumps({"plan": pl, "mode": mode, "home": str(home)}, ensure_ascii=False, indent=1) if as_json else
              "\n".join([f"[VDF 擷取系統 · 計畫(不執行;加 --apply 才跑)] 模式 {mode} · 輸出根 {home}"]
                        + [f"  {i + 1}. {p['mdl']:7} {p['file']}  參數 {' '.join(p['args']) or '—'}  ← 需 {','.join(p['needs']) or '—'}"
                           for i, p in enumerate(pl)]))
        return 0
    if verb == "run":
        if mode == "live" and not gate_open():
            print(f"[GATED] {TAG}:同意閘未開 —— 這不是壞掉。live 擷取要觸網;零子行程、零出網、零寫檔。"
                  "開閘是操作員的手(本視窗):$env:VIA_NET_CONSENT='YES' 與 $env:VIA_SCRAPE_CONSENT(雙閘;AI 永不代設)")
            return 4
        runs = run(rows, mode, home)
        ver = verify(rows, home)
        if as_json:
            print(json.dumps({"runs": runs, "verify": ver}, ensure_ascii=False))
        else:
            print(f"[VDF 擷取系統 · 執行] 模式 {mode} · 輸出根 {home}")
            _print_runs(runs)
            bad_v = [v for v in ver if not v["ok"]]
            print(f"  [驗收] 輸出 {len(ver) - len(bad_v)}/{len(ver)} 檔合格" + ("" if not bad_v else " · 缺/空:" + " · ".join(v["path"] for v in bad_v[:6])))
        return 0 if all(x["rc"] == 0 for x in runs) and all(v["ok"] for v in ver) else 1
    if verb == "verify":
        ver = verify(rows, home)
        if as_json:
            print(json.dumps({"verify": ver, "home": str(home)}, ensure_ascii=False))
        else:
            print(f"[VDF 擷取系統 · 驗收] 輸出根 {home}")
            for v in ver:
                print(f"  {'✓' if v['ok'] else '✗'} {v['id']:4} {v['path']:58} {v['bytes']:>9} B · 列 {v['rows']}")
        return 0 if all(v["ok"] for v in ver) else 1
    rep = integration_test(rows)
    rd = rep["rounds"][0]
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, default=str))
    else:
        print(f"[VDF 擷取系統 · 整合測試(fixture 離線網)] {'PASS' if rep['pass'] else 'FAIL'}")
        _print_runs(rd["runs"])
        ok_v = sum(v["ok"] for v in rd["verify"])
        print(f"  [輸出] {ok_v}/{len(rd['verify'])} 檔合格(在 · 非空 · 列數)")
        for v in rd["verify"]:
            if not v["ok"]:
                print(f"     ✗ {v['id']} {v['path']} · {v.get('err') or ('不在' if not v['exists'] else '空')}")
        print(f"  [封網] MDL007 block 模式 rc {rd['block']['rc']} · 擋下 {rd['block']['blocked']} 次出網")
        print(f"  [倉內寫入] {len(rep['repo_writes'])} 檔" + ("" if not rep["repo_writes"] else " · " + " · ".join(rep["repo_writes"][:4])))
    return 0 if rep["pass"] else 1


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 自測(獨立擷取系統:冊 · 改寫 · 閘 · 路由;整合全鏈另跑 test)===")
    book = load_book()
    rows = book["engines"]
    chk("① 冊:MDL001–007 每號至少一支 · 檔都在 · 每支有擷取函式定位與輸出契約",
        {r["mdl"] for r in rows} >= {f"MDL00{i}" for i in range(1, 8)} and all((VDF_DIR / r["file"]).is_file() for r in rows)
        and all(r.get("fetch_functions") and r.get("outputs") for r in rows), len(rows))
    miss = []
    for r in rows:
        src = (VDF_DIR / r["file"]).read_text(encoding="utf-8", errors="replace")
        defs = {(n.name, n.lineno) for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        miss += [f"{r['id']}:{f['name']}" for f in r["fetch_functions"] if (f["name"], f["line"]) not in defs]
    chk("② 擷取函式 AST 定位與原件一致(名稱 + 行號;原件改了就紅)", not miss, miss[:4])
    with tempfile.TemporaryDirectory() as tmp:
        counts = {r["id"]: compile_engine(VDF_DIR / r["file"], Path(tmp))[2] for r in rows}
        _, mains, _ = compile_engine(VDF_DIR / rows[0]["file"], Path(tmp))
    chk("③ 舊佈局絕對路徑全改寫到輸出根(每支 ≥ 1 處)· __main__ 段分出", all(v >= 1 for v in counts.values()) and mains is not None, counts)
    chk("④ 依 needs 排序:MDL001 宇宙先於 004 / 005 / 006 / 007", [r["id"] for r in ordered(rows)].index("001u") <
        min([r["id"] for r in ordered(rows)].index(x) for x in ("004", "005", "006", "007")))
    real_gate, keep_vcgc = globals()["gate_open"], os.environ.get("VIA_FROM_VCGC")
    try:
        globals()["gate_open"] = lambda: False                           # 模擬閘關:不讀不寫 VIA_NET_CONSENT
        os.environ["VIA_FROM_VCGC"] = "YES"
        buf = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(buf):
            rc_g = main(["run", "--apply"])
            rc_u = main(["runn"])
            rc_x = main(["run", "MDL099"])
            rc_p = main(["run"])
        chk("⑤ live 閘沒開 → rc4 GATED 零子行程;未知動詞 / 冊外代號 rc2;不加 --apply 只列計畫", rc_g == 4 and rc_u == 2 and rc_x == 2
            and rc_p == 0 and "[GATED]" in buf.getvalue() and "計畫" in buf.getvalue(), (rc_g, rc_u, rc_x, rc_p))
    finally:
        globals()["gate_open"] = real_gate
        if keep_vcgc is None:
            os.environ.pop("VIA_FROM_VCGC", None)
    routes = {u: _fix_route(u) for u in ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
                                         "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
                                         "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
                                         "https://production.dataviz.cnn.io/index/fearandgreed/graphdata")}
    chk("⑥ fixture 路由:兩所日行情 · 上市基本資料 · CNN 都有樣本;未知網址回 404(不編)", all(routes.values())
        and _fix_route("https://example.com/x") is None)
    import requests as _rq
    real_req = _rq.sessions.Session.request
    calls = []

    class _T:
        def __init__(self, open_):
            self.open_ = open_

        def gate_state(self):
            return {"open": self.open_}

        def http_bytes(self, url, timeout=30, headers=None):
            calls.append(url)
            return {"state": "OK", "data": b'[{"Code": "2330"}]'} if self.open_ else {"state": "DENY"}

        def post_json(self, url, payload=None, headers=None, timeout=30):
            calls.append("POST " + url)
            return {"state": "OK", "data": {"ok": 1}}
    try:
        _install_live_routes(_T(True))
        r1 = _rq.get("https://openapi.twse.com.tw/v1/x", params={"a": 1}, timeout=5).json()
        r2 = _rq.post("https://example.org/p", json={"b": 2}).json()
        _install_live_routes(_T(False))
        try:
            _rq.get("https://openapi.twse.com.tw/v1/x")
            denied = False
        except _rq.exceptions.ConnectionError as e:
            denied = "GATED" in str(e)
    finally:
        _rq.sessions.Session.request = real_req
        for m in ("yfinance", "akshare"):
            sys.modules.pop(m, None)
    chk("⑧ live 路由:requests GET/POST 全走鎖版網路工具(http_bytes / post_json · 帶 params)· 閘關 = GATED 例外不出網",
        r1 == [{"Code": "2330"}] and r2 == {"ok": 1} and calls[0].endswith("/x?a=1") and calls[1].startswith("POST ") and denied, calls[:3])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;本支不寫 VIA_NET_CONSENT", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_NET_CONSENT[\"']\]\s*=", text))
    print(f"  [計] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
