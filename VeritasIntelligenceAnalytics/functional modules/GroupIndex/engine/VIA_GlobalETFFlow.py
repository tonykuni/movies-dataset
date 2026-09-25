#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_GlobalETFFlow.py
====================
VERITAS INTELLIGENCE ANALYTICS · 全球 ETF 資金流動監控引擎
Global ETF Capital-Flow Monitor  ·  GIF (MDL008) 橫向擴張版

用 ETF 當「探針」，監控全球各區股市與各類金融商品的資金流動。
一檔 ETF 的申購/贖回是真實的現金進出，因此 ETF 是目前唯一能在
「跨市場、跨資產、同一把尺」上量到資金流的公開工具。

真值階梯（沿用 VIA_GIF 既有規範，不得跨階冒充）
------------------------------------------------
  T1  真流 PRIMARY   ΔSharesOutstanding × NAV  → 有金額（美元），evidence V/Der
  T2  部位 POSITION  COT / 官方持倉            → 本引擎不產生，保留欄位
  T3  估流 ESTIMATE  價量推導（FIS_pv）        → 只給方向與強度，flow_usd 永遠 "—"
  T4  模擬 SIM       情境模擬                  → 本引擎禁止產生

  T3 不會被寫成金額。這是本引擎與坊間「資金流模擬器」最大的差別：
  那些把 tsM/instM 乘數寫死再乘出「億元」的做法屬於 T4 偽裝成 T1，
  本引擎一律拒絕。

FIS_pv 合成（與 VIA_GIF FIS 引擎同式，確保兩邊可比）
  組件 → robust-z((x-median)/(1.4826·MAD)) → 取均 → 100·tanh(z/2) → ±100

治理
  只增不減：universe 與 shares registry 皆為 append-only，退場者轉 DORMANT。
  UTF-8 no-BOM、無互動輸入、一次跑完、HTML 輸出。

用法
  python VIA_GlobalETFFlow.py                 完整執行 → HTML/JSON/CSV
  python VIA_GlobalETFFlow.py --selftest      離線單元測試
  python VIA_GlobalETFFlow.py --mocktest      本機 mock 伺服器整合測試
  python VIA_GlobalETFFlow.py --probe         端點連通性矩陣
  python VIA_GlobalETFFlow.py --offline       只用快取
  python VIA_GlobalETFFlow.py --group asset   以資產類別聚合（預設 region）

純標準庫。無 pandas / requests / yfinance 依賴。
"""

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

import argparse
import base64
import bisect as _bisect
import concurrent.futures as _cf
import csv
import datetime as _dt
import gzip
import io
import json
import math
import os
import re
import shutil
import string as _string
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from collections import deque as _deque
from pathlib import Path

__version__ = "v0100"
__engine__ = "VIA-MDL008-ETFFLOW"

# --------------------------------------------------------------------------- #
# 0.  UNIVERSE  ── 區域 × 資產類別 的 ETF 探針地圖
# --------------------------------------------------------------------------- #
# (ticker, 中文名, region, asset_class, tier)
#   region      地理暴險：US / EU / JP / APAC / EM / CN / TW / GLOBAL / NONE
#   asset_class EQUITY / BOND / CREDIT / COMMODITY / FX / CRYPTO / REIT / CASH
#   tier        風險階層 1..5（對應既有 Tier 1/2 避險 → Tier 5 投機）
UNIVERSE_SEED = [
    # ---- 區域股市 ----------------------------------------------------------
    ("SPY",  "美股核心 S&P500",     "US",     "EQUITY", 3),
    ("QQQ",  "美股科技 Nasdaq100",  "US",     "EQUITY", 4),
    ("IWM",  "美股小型 Russell2000", "US",    "EQUITY", 4),
    ("VGK",  "歐洲整體",            "EU",     "EQUITY", 3),
    ("EWG",  "德國",                "EU",     "EQUITY", 3),
    ("EWU",  "英國",                "EU",     "EQUITY", 3),
    ("EWJ",  "日本",                "JP",     "EQUITY", 3),
    ("EWY",  "南韓",                "APAC",   "EQUITY", 4),
    ("EWT",  "台灣（境外視角）",     "TW",     "EQUITY", 4),
    ("EWA",  "澳洲",                "APAC",   "EQUITY", 3),
    ("INDA", "印度",                "EM",     "EQUITY", 4),
    ("EEM",  "新興市場整體",         "EM",     "EQUITY", 4),
    ("MCHI", "中國整體",            "CN",     "EQUITY", 4),
    ("FXI",  "中國大型股",           "CN",     "EQUITY", 4),
    ("EWZ",  "巴西",                "EM",     "EQUITY", 5),
    ("ACWI", "全球股市基準",         "GLOBAL", "EQUITY", 3),
    # ---- 美股類股（資金輪動偵測）--------------------------------------------
    ("XLK",  "科技類股",            "US",     "EQUITY", 4),
    ("XLF",  "金融類股",            "US",     "EQUITY", 3),
    ("XLE",  "能源類股",            "US",     "EQUITY", 4),
    ("XLV",  "醫療類股",            "US",     "EQUITY", 3),
    ("XLI",  "工業類股",            "US",     "EQUITY", 3),
    ("XLU",  "公用事業類股",         "US",     "EQUITY", 2),
    ("XLP",  "民生必需類股",         "US",     "EQUITY", 2),
    # ---- 利率 / 主權債 ------------------------------------------------------
    ("BIL",  "美短債 1-3M（現金）",  "US",     "CASH",   1),
    ("SHY",  "美公債 1-3Y",         "US",     "BOND",   1),
    ("IEF",  "美公債 7-10Y",        "US",     "BOND",   2),
    ("TLT",  "美公債 20Y+",         "US",     "BOND",   2),
    ("TIP",  "美抗通膨債 TIPS",      "US",     "BOND",   2),
    ("BNDX", "非美投等債（避險）",    "GLOBAL", "BOND",   2),
    # ---- 信用 ---------------------------------------------------------------
    ("LQD",  "美投資級公司債",       "US",     "CREDIT", 3),
    ("HYG",  "美高收益債",          "US",     "CREDIT", 4),
    ("JNK",  "美高收益債（次驗證）",  "US",     "CREDIT", 4),
    ("EMB",  "新興市場美元債",       "EM",     "CREDIT", 4),
    # ---- 商品 ---------------------------------------------------------------
    ("GLD",  "黃金",                "GLOBAL", "COMMODITY", 2),
    ("SLV",  "白銀",                "GLOBAL", "COMMODITY", 4),
    ("DBC",  "廣泛商品",            "GLOBAL", "COMMODITY", 4),
    ("USO",  "原油",                "GLOBAL", "COMMODITY", 5),
    ("COPX", "銅礦",                "GLOBAL", "COMMODITY", 5),
    # ---- 匯率 ---------------------------------------------------------------
    ("UUP",  "美元指數多頭",         "US",     "FX",     2),
    ("FXE",  "歐元",                "EU",     "FX",     3),
    ("FXY",  "日圓",                "JP",     "FX",     2),
    # ---- 不動產 -------------------------------------------------------------
    ("VNQ",  "美國 REIT",           "US",     "REIT",   4),
    ("VNQI", "非美 REIT",           "GLOBAL", "REIT",   4),
    # ---- 加密（風險光譜末端）------------------------------------------------
    ("IBIT", "比特幣現貨",           "GLOBAL", "CRYPTO", 5),
    ("FBTC", "比特幣現貨（次驗證）",  "GLOBAL", "CRYPTO", 5),
]

BENCHMARK = "ACWI"          # 相對強弱的分母
DUAL_VERIFY = [("HYG", "JNK"), ("MCHI", "FXI"), ("IBIT", "FBTC")]   # 雙重驗證對

REGION_LABEL = {
    "US": "美國", "EU": "歐洲", "JP": "日本", "APAC": "亞太成熟",
    "EM": "新興市場", "CN": "中國", "TW": "台灣", "GLOBAL": "全球/跨區",
}
ASSET_LABEL = {
    "EQUITY": "股票", "BOND": "主權債", "CREDIT": "信用債", "COMMODITY": "商品",
    "FX": "匯率", "CRYPTO": "加密", "REIT": "不動產", "CASH": "現金等價",
}

# --------------------------------------------------------------------------- #
# 1.  CONFIG
# --------------------------------------------------------------------------- #

BASE_STOOQ = "https://stooq.com"
BASE_YAHOO = "https://query1.finance.yahoo.com"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) VIA/GlobalETFFlow "
              + __version__ + " (+VeritasIntelligenceAnalytics)")

HOST_MIN_INTERVAL = {"stooq.com": 0.6, "query1.finance.yahoo.com": 0.4}
DEFAULT_MIN_INTERVAL = 0.4

HTTP_TIMEOUT = 25
HTTP_RETRIES = 3
CACHE_TTL = 6 * 3600

HORIZONS = [1, 5, 20, 60, 120, 240]
MIN_BARS = 70              # 少於此根數 → FIS_pv 判 PENDING
MIN_COMPONENTS = 3         # 合成 FIS 至少要有幾個組件成立
MF_WINDOW = 20             # NetMF / CMF 視窗
INTENSITY_WINDOW = 60      # 成交金額中位數基準視窗
MFI_WINDOW = 14

# 真值階梯
T1, T2, T3, T4 = "T1", "T2", "T3", "T4"
EV_OFFICIAL, EV_DERIVED, EV_ESTIMATED, EV_PENDING = "V", "Der", "Est", "P"
EVIDENCE_LABEL = {
    EV_OFFICIAL: "官方確認", EV_DERIVED: "規則推導",
    EV_ESTIMATED: "價量估算(方向)", EV_PENDING: "待補",
}

# Visual Lock
VL = {"bg": "#f5f4f0", "paper": "#fff", "ink": "#1e1d1a", "up": "#c96b5a",
      "down": "#5a9e6f", "blue": "#4c78a8", "teal": "#439a9a", "am": "#c4943a"}
RESON = ("linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,"
         "#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)")


# --------------------------------------------------------------------------- #
# 2.  LOG
# --------------------------------------------------------------------------- #

class Log:
    MARK = {"OK": "\u2713", "WARN": "!", "ERR": "\u2717", "INFO": "\u00b7", "STEP": "\u25b8"}

    def __init__(self, quiet=False):
        self.quiet = quiet
        self.lines: list[tuple[str, str, float]] = []
        self.t0 = time.time()
        self._lock = threading.Lock()

    def _emit(self, lv, msg):
        with self._lock:
            self.lines.append((lv, msg, time.time() - self.t0))
            if not self.quiet:
                sys.stdout.write("  [%6.1fs] %s %s\n"
                                 % (time.time() - self.t0, self.MARK.get(lv, "-"), msg))
                sys.stdout.flush()

    def step(self, m): self._emit("STEP", m)
    def ok(self, m): self._emit("OK", m)
    def warn(self, m): self._emit("WARN", m)
    def err(self, m): self._emit("ERR", m)
    def info(self, m): self._emit("INFO", m)

    def banner(self, title, sub=""):
        if self.quiet:
            return
        bar = "=" * 74
        sys.stdout.write("\n%s\n  %s\n%s%s\n" % (bar, title, ("  " + sub + "\n") if sub else "", bar))
        sys.stdout.flush()


LOG = Log()


# --------------------------------------------------------------------------- #
# 3.  HTTP
# --------------------------------------------------------------------------- #

class FetchError(Exception):
    pass


class Http:
    def __init__(self, cache_dir: Path, offline=False, no_cache=False):
        self.cache_dir = cache_dir
        self.offline = offline
        self.no_cache = no_cache
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()
        self.stats = {"net": 0, "cache": 0, "fail": 0}

    @staticmethod
    def _key(url):
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", url)
        if len(safe) > 110:
            import hashlib
            safe = safe[:80] + "_" + hashlib.blake2s(url.encode(), digest_size=6).hexdigest()
        return safe

    def _cpath(self, url):
        return self.cache_dir / (self._key(url) + ".bin")

    def _cread(self, url, ttl):
        # --no-cache 必須連「讀」也繞過。只停寫不停讀會讓呼叫端拿到舊值卻以為是新抓的，
        # 這正是差分型指標（ΔShares×NAV）被算成 0 的成因。
        if self.no_cache and not self.offline:
            return None
        p = self._cpath(url)
        if not p.exists():
            return None
        if not self.offline and ttl >= 0 and (time.time() - p.stat().st_mtime) > ttl:
            return None
        try:
            return p.read_bytes()
        except OSError:
            return None

    def _throttle(self, host):
        # 節流是為了不打爆公開端點；本機 mock/代理不適用。
        if host.startswith("127.0.0.1") or host.startswith("localhost") or host.startswith("[::1]"):
            return
        gap = HOST_MIN_INTERVAL.get(host, DEFAULT_MIN_INTERVAL)
        with self._lock:
            wait = gap - (time.time() - self._last.get(host, 0.0))
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.time()

    def get(self, url, ttl=CACHE_TTL) -> bytes:
        c = self._cread(url, ttl)
        if c is not None:
            self.stats["cache"] += 1
            return c
        if self.offline:
            raise FetchError("offline and not cached: %s" % url)
        host = urllib.parse.urlparse(url).netloc
        last = None
        for attempt in range(1, HTTP_RETRIES + 1):
            self._throttle(host)
            req = urllib.request.Request(url)
            req.add_header("User-Agent", USER_AGENT)
            req.add_header("Accept", "application/json, text/csv, */*;q=0.8")
            req.add_header("Accept-Encoding", "gzip")
            req.add_header("Connection", "close")
            try:
                with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding", "") == "gzip":
                        try:
                            raw = gzip.decompress(raw)
                        except OSError:
                            pass
                self.stats["net"] += 1
                if not self.no_cache:
                    try:
                        self._cpath(url).write_bytes(raw)
                    except OSError:
                        pass
                return raw
            except Exception as exc:                       # noqa: BLE001
                last = exc
                if attempt < HTTP_RETRIES:
                    time.sleep(min(5.0, 1.0 * (2 ** (attempt - 1))))
        self.stats["fail"] += 1
        stale = self._cread(url, -1)
        if stale is not None:
            return stale
        raise FetchError("%s -> %s" % (url, last))

    def get_text(self, url, ttl=CACHE_TTL) -> str:
        return decode_text(self.get(url, ttl))

    def get_json(self, url, ttl=CACHE_TTL):
        return json.loads(decode_text(self.get(url, ttl)))


def decode_text(raw: bytes) -> str:
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    for enc in ("utf-8", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# 4.  UTILITIES
# --------------------------------------------------------------------------- #

def to_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else float(v)
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "--", "N/A", "null", "None", "nan"):
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return None if (math.isnan(f) or math.isinf(f)) else f


def median(xs):
    v = sorted(x for x in xs if x is not None)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def mad(xs, med=None):
    v = [x for x in xs if x is not None]
    if not v:
        return None
    m = median(v) if med is None else med
    return median([abs(x - m) for x in v])


def robust_z(x, sample):
    """(x - median) / (1.4826 * MAD).  MAD==0 → 無法標準化，回 None（不假造 0）。"""
    if x is None:
        return None
    v = [s for s in sample if s is not None]
    if len(v) < 8:
        return None
    m = median(v)
    d = mad(v, m)
    if d is None or d <= 1e-12:
        return None
    return (x - m) / (1.4826 * d)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def today_utc() -> _dt.date:
    return _dt.datetime.now(_dt.timezone.utc).date()


# --------------------------------------------------------------------------- #
# 5.  EVIDENCE-TAGGED VALUE
# --------------------------------------------------------------------------- #

class Val:
    """值 + 真值階梯 + 證據。value 為 None 時一律 PENDING，永遠不會被冒充成官方。"""

    __slots__ = ("value", "tier", "evidence", "source", "note")

    def __init__(self, value=None, tier=T3, evidence=EV_PENDING, source="", note=""):
        self.value = value
        self.tier = tier
        self.evidence = evidence if value is not None else EV_PENDING
        self.source = source
        self.note = note

    @property
    def ok(self):
        return self.value is not None

    def as_dict(self):
        return {"value": self.value, "tier": self.tier, "evidence": self.evidence,
                "source": self.source, "note": self.note}

    def __repr__(self):
        return "Val(%r,%s/%s)" % (self.value, self.tier, self.evidence)


# --------------------------------------------------------------------------- #
# 6.  SOURCE ADAPTERS
# --------------------------------------------------------------------------- #

class Sources:
    """價量與股數來源。任何未解析者回空，依賴欄位停留 PENDING，絕不補值。"""

    def __init__(self, http: Http, base_stooq=BASE_STOOQ, base_yahoo=BASE_YAHOO):
        self.http = http
        self.b_stooq = base_stooq.rstrip("/")
        self.b_yahoo = base_yahoo.rstrip("/")

    # -- 6.1 日線 ------------------------------------------------------------ #
    def stooq_symbol(self, ticker: str) -> str:
        t = ticker.lower()
        if t.endswith(".tw") or t.endswith(".two"):
            return t.replace(".two", ".tw")
        return t + ".us"

    def daily_stooq(self, ticker: str) -> list[dict]:
        url = "%s/q/d/l/?s=%s&i=d" % (self.b_stooq, self.stooq_symbol(ticker))
        return parse_stooq_csv(self.http.get_text(url))

    def daily_yahoo(self, ticker: str, rng="2y") -> list[dict]:
        url = ("%s/v8/finance/chart/%s?range=%s&interval=1d"
               % (self.b_yahoo, urllib.parse.quote(ticker), rng))
        return parse_yahoo_chart(self.http.get_json(url))

    def daily(self, ticker: str) -> tuple[list[dict], str]:
        """主 Stooq、備 Yahoo。回 (bars, source_name)。"""
        errs = []
        for name, fn in (("stooq", self.daily_stooq), ("yahoo", self.daily_yahoo)):
            try:
                bars = fn(ticker)
            except Exception as exc:                       # noqa: BLE001
                errs.append("%s:%s" % (name, str(exc)[:50]))
                continue
            if len(bars) >= 2:
                return bars, name
            errs.append("%s:only %d bars" % (name, len(bars)))
        raise FetchError("daily(%s) %s" % (ticker, "; ".join(errs)))

    # -- 6.2 在外流通股數 / NAV （T1 真流的唯一合法入口）--------------------- #
    def shares_nav_yahoo(self, ticker: str) -> dict:
        url = ("%s/v10/finance/quoteSummary/%s?modules=defaultKeyStatistics,price"
               % (self.b_yahoo, urllib.parse.quote(ticker)))
        doc = self.http.get_json(url)
        return parse_quote_summary(doc)


# -- parsers (module level so --selftest can drive them offline) ------------- #

def parse_stooq_csv(text: str) -> list[dict]:
    """Stooq 日線 CSV → 升冪 bars。表頭缺失或全為 N/D 時回空，不猜。"""
    out = []
    rdr = csv.DictReader(io.StringIO(text.strip()))
    if not rdr.fieldnames or "Date" not in rdr.fieldnames:
        return []
    for r in rdr:
        d = (r.get("Date") or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            continue
        c = to_float(r.get("Close"))
        if c is None or c <= 0:
            continue
        out.append({"date": d, "open": to_float(r.get("Open")),
                    "high": to_float(r.get("High")), "low": to_float(r.get("Low")),
                    "close": c, "volume": to_float(r.get("Volume"))})
    out.sort(key=lambda x: x["date"])
    return out


def parse_yahoo_chart(doc) -> list[dict]:
    try:
        res = doc["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError):
        return []
    out = []
    for i, t in enumerate(ts):
        c = to_float((q.get("close") or [None] * len(ts))[i])
        if c is None or c <= 0:
            continue
        d = _dt.datetime.fromtimestamp(t, _dt.timezone.utc).date().isoformat()
        out.append({"date": d,
                    "open": to_float((q.get("open") or [None] * len(ts))[i]),
                    "high": to_float((q.get("high") or [None] * len(ts))[i]),
                    "low": to_float((q.get("low") or [None] * len(ts))[i]),
                    "close": c,
                    "volume": to_float((q.get("volume") or [None] * len(ts))[i])})
    out.sort(key=lambda x: x["date"])
    return out


def parse_quote_summary(doc) -> dict:
    """→ {shares, nav}。任一欄位取不到就不放，讓上游停在 PENDING。"""
    out = {}
    try:
        res = doc["quoteSummary"]["result"][0]
    except (KeyError, IndexError, TypeError):
        return out
    dks = res.get("defaultKeyStatistics") or {}
    price = res.get("price") or {}
    sh = dks.get("sharesOutstanding")
    if isinstance(sh, dict):
        sh = sh.get("raw")
    sh = to_float(sh)
    if sh and sh > 0:
        out["shares"] = sh
    nav = dks.get("navPrice") or price.get("navPrice")
    if isinstance(nav, dict):
        nav = nav.get("raw")
    nav = to_float(nav)
    if nav and nav > 0:
        out["nav"] = nav
    return out


# --------------------------------------------------------------------------- #
# 7.  FIS_pv  ── T3 價量估流（只給方向與強度，永不產生金額）
# --------------------------------------------------------------------------- #

def _signed_dollar_volume(bars):
    """sign(當日報酬) × 成交金額。方向由收盤變化決定。"""
    out = [None]
    for prev, cur in zip(bars, bars[1:]):
        v, c = cur.get("volume"), cur.get("close")
        if v is None or c is None or prev.get("close") in (None, 0):
            out.append(None)
            continue
        sgn = 1.0 if c >= prev["close"] else -1.0
        out.append(sgn * c * v)
    return out


def _mfi(bars, window=MFI_WINDOW):
    """Money Flow Index (0..100)。需要 high/low/close/volume 齊全。"""
    tp, mf = [], []
    for b in bars:
        h, l, c, v = b.get("high"), b.get("low"), b.get("close"), b.get("volume")
        if None in (h, l, c, v):
            tp.append(None)
            mf.append(None)
            continue
        t = (h + l + c) / 3.0
        tp.append(t)
        mf.append(t * v)
    if len(tp) <= window:
        return None
    pos = neg = 0.0
    got = 0
    for i in range(len(tp) - window, len(tp)):
        if tp[i] is None or tp[i - 1] is None or mf[i] is None:
            continue
        got += 1
        if tp[i] > tp[i - 1]:
            pos += mf[i]
        elif tp[i] < tp[i - 1]:
            neg += mf[i]
    if got < window * 0.6 or (pos + neg) <= 0:
        return None
    return 100.0 * pos / (pos + neg)


def _cmf(bars, window=MF_WINDOW):
    """Chaikin Money Flow (-1..1)。"""
    if len(bars) < window:
        return None
    num = den = 0.0
    got = 0
    for b in bars[-window:]:
        h, l, c, v = b.get("high"), b.get("low"), b.get("close"), b.get("volume")
        if None in (h, l, c, v) or v <= 0:
            continue
        rng = h - l
        if rng <= 0:
            continue
        mfm = ((c - l) - (h - c)) / rng
        num += mfm * v
        den += v
        got += 1
    if got < window * 0.6 or den <= 0:
        return None
    return num / den


def _obv_slope(bars, window=MF_WINDOW):
    """OBV 最近 window 根的線性斜率，除以平均量做尺度歸一。"""
    if len(bars) < window + 1:
        return None
    obv, cur = [], 0.0
    for prev, b in zip(bars, bars[1:]):
        v = b.get("volume")
        if v is None or prev.get("close") is None or b.get("close") is None:
            obv.append(cur)
            continue
        cur += v if b["close"] >= prev["close"] else -v
        obv.append(cur)
    seg = obv[-window:]
    if len(seg) < window:
        return None
    vols = [b.get("volume") for b in bars[-window:] if b.get("volume")]
    scale = (sum(vols) / len(vols)) if vols else None
    if not scale or scale <= 0:
        return None
    n = len(seg)
    mx = (n - 1) / 2.0
    my = sum(seg) / n
    sxy = sum((i - mx) * (y - my) for i, y in enumerate(seg))
    sxx = sum((i - mx) ** 2 for i in range(n))
    if sxx <= 0:
        return None
    return (sxy / sxx) / scale


class _RobustWindow:
    """滾動 robust-z 視窗：維持最近 N 個有效值的排序副本。

    median 由排序副本 O(1) 取得；MAD 用「以中位數為軸的雙指標合併」在 O(w) 內求出，
    不需要對絕對離差再排序一次。這是把逐日重算從 O(n^2 log w) 壓到 O(n·w) 的關鍵。
    """

    __slots__ = ("size", "order", "s")

    def __init__(self, size):
        self.size = size
        self.order = _deque()
        self.s = []

    def add(self, x):
        if x is None:
            return
        _bisect.insort(self.s, x)
        self.order.append(x)
        if len(self.order) > self.size:
            old = self.order.popleft()
            self.s.pop(_bisect.bisect_left(self.s, old))

    def median(self):
        n = len(self.s)
        if n == 0:
            return None
        return self.s[n // 2] if n % 2 else (self.s[n // 2 - 1] + self.s[n // 2]) / 2.0

    def mad(self):
        """median(|x - median|) via two-pointer merge over the sorted window."""
        n = len(self.s)
        if n == 0:
            return None
        m = self.median()
        i = _bisect.bisect_left(self.s, m) - 1      # 往左遞增的離差
        j = _bisect.bisect_left(self.s, m)          # 往右遞增的離差
        need = n // 2
        picks = []
        want = need + 1 if n % 2 else need + 1
        for _ in range(want):
            lv = (m - self.s[i]) if i >= 0 else None
            rv = (self.s[j] - m) if j < n else None
            if lv is None and rv is None:
                break
            if rv is None or (lv is not None and lv <= rv):
                picks.append(lv)
                i -= 1
            else:
                picks.append(rv)
                j += 1
        if len(picks) <= need:
            return picks[-1] if picks else None
        return picks[need] if n % 2 else (picks[need - 1] + picks[need]) / 2.0

    def z(self, x):
        if x is None or len(self.s) < 8:
            return None
        m = self.median()
        d = self.mad()
        if d is None or d <= 1e-12:
            return None
        return (x - m) / (1.4826 * d)


def _raw_components(bars):
    """一次線性掃描算出六個原始組件序列（未標準化）。

    全部以滾動累加/滾動視窗完成，對每根 bar 都是 O(1)~O(w)，
    因此「整條時間序列」與「單一時點」的成本幾乎相同。
    """
    n = len(bars)
    out = {k: [None] * n for k in ("signed_dollar_vol", "net_mf20", "flow_intensity",
                                   "mfi14", "cmf20", "obv_slope")}
    dv = [None] * n
    intensity_raw = [None] * n

    # 滾動狀態
    sdv_q = _deque()          # NetMF20 視窗
    sdv_sum = 0.0
    dv_win = _RobustWindow(INTENSITY_WINDOW)      # 只借用它的 median
    mfi_q = _deque()          # (pos, neg)
    mfi_pos = mfi_neg = 0.0
    cmf_q = _deque()          # (mfm*v, v)
    cmf_num = cmf_den = 0.0
    vol_q = _deque()
    vol_sum = 0.0
    obv = 0.0
    obv_hist = []             # 絕對索引 -> obv 值
    oy_q = _deque()           # (j, y)
    sum_y = sum_jy = 0.0

    for i, b in enumerate(bars):
        c, v = b.get("close"), b.get("volume")
        h, l = b.get("high"), b.get("low")
        prev_c = bars[i - 1]["close"] if i > 0 else None

        d = (c * v) if (c is not None and v is not None) else None
        dv[i] = d

        # (1) signed dollar volume
        if d is not None and prev_c:
            sgn = 1.0 if c >= prev_c else -1.0
            out["signed_dollar_vol"][i] = sgn * d

        # (2) NetMF20
        sv = out["signed_dollar_vol"][i]
        sdv_q.append(sv)
        if sv is not None:
            sdv_sum += sv
        if len(sdv_q) > MF_WINDOW:
            old = sdv_q.popleft()
            if old is not None:
                sdv_sum -= old
        valid = sum(1 for x in sdv_q if x is not None)
        if len(sdv_q) == MF_WINDOW and valid >= MF_WINDOW * 0.6:
            out["net_mf20"][i] = sdv_sum

        # (3) flow intensity（今日成交金額 / 60 日中位數），帶方向
        dv_win.add(d)
        med = dv_win.median()
        if d is not None and med and med > 0:
            intensity_raw[i] = d / med
            if prev_c:
                out["flow_intensity"][i] = intensity_raw[i] * (1.0 if c >= prev_c else -1.0)

        # (4) MFI14
        tp = ((h + l + c) / 3.0) if None not in (h, l, c) else None
        prev_tp = None
        if i > 0:
            pb = bars[i - 1]
            if None not in (pb.get("high"), pb.get("low"), pb.get("close")):
                prev_tp = (pb["high"] + pb["low"] + pb["close"]) / 3.0
        pos = neg = 0.0
        if tp is not None and prev_tp is not None and v is not None:
            if tp > prev_tp:
                pos = tp * v
            elif tp < prev_tp:
                neg = tp * v
            mfi_q.append((pos, neg, True))
        else:
            mfi_q.append((0.0, 0.0, False))
        mfi_pos += pos
        mfi_neg += neg
        if len(mfi_q) > MFI_WINDOW:
            op, on, _ok = mfi_q.popleft()
            mfi_pos -= op
            mfi_neg -= on
        got = sum(1 for x in mfi_q if x[2])
        if len(mfi_q) == MFI_WINDOW and got >= MFI_WINDOW * 0.6 and (mfi_pos + mfi_neg) > 0:
            out["mfi14"][i] = 100.0 * mfi_pos / (mfi_pos + mfi_neg)

        # (5) CMF20
        num = den = 0.0
        okc = False
        if None not in (h, l, c, v) and v > 0 and (h - l) > 0:
            mfm = ((c - l) - (h - c)) / (h - l)
            num, den, okc = mfm * v, v, True
        cmf_q.append((num, den, okc))
        cmf_num += num
        cmf_den += den
        if len(cmf_q) > MF_WINDOW:
            on_, od, _o = cmf_q.popleft()
            cmf_num -= on_
            cmf_den -= od
        gotc = sum(1 for x in cmf_q if x[2])
        if len(cmf_q) == MF_WINDOW and gotc >= MF_WINDOW * 0.6 and cmf_den > 0:
            out["cmf20"][i] = cmf_num / cmf_den

        # (6) OBV 斜率（滾動線性回歸，前綴和求解）
        if i > 0 and v is not None and prev_c is not None and c is not None:
            obv += v if c >= prev_c else -v
        obv_hist.append(obv)
        if i > 0:
            oy_q.append((i, obv))
            sum_y += obv
            sum_jy += i * obv
            if len(oy_q) > MF_WINDOW:
                oj, oyv = oy_q.popleft()
                sum_y -= oyv
                sum_jy -= oj * oyv
        vol_q.append(v if v is not None else 0.0)
        vol_sum += (v or 0.0)
        if len(vol_q) > MF_WINDOW:
            vol_sum -= vol_q.popleft()
        if len(oy_q) == MF_WINDOW and len(vol_q) == MF_WINDOW and vol_sum > 0:
            w = MF_WINDOW
            j0 = oy_q[0][0]
            mx = (w - 1) / 2.0
            sxx = sum((k - mx) ** 2 for k in range(w))
            sxy = (sum_jy - j0 * sum_y) - mx * sum_y
            scale = vol_sum / w
            if sxx > 0 and scale > 0:
                out["obv_slope"][i] = (sxy / sxx) / scale

    return out, dv, intensity_raw


def compute_flow_series(bars, tail=None):
    """FIS_pv 時間序列。單點值即 series[-1]，與逐日重算結果一致。

    回傳 dates / fis / intensity / mfi14 / cmf20 / coverage，全部對齊 bars。
    T3：僅方向與強度，任何呼叫端都不得換算為金額。
    """
    n = len(bars)
    empty = {"dates": [], "fis": [], "intensity": [], "mfi14": [], "cmf20": [],
             "coverage": [], "close": [], "dollar_vol": [], "bars": n}
    if n == 0:
        return empty

    raw, dv, intensity_raw = _raw_components(bars)
    keys = list(raw.keys())
    # 每個組件配一個滾動標準化視窗；mfi/cmf 用固定尺度（本就有自然量綱）
    wins = {k: _RobustWindow(INTENSITY_WINDOW) for k in keys}

    fis, cov = [None] * n, [0.0] * n
    for i in range(n):
        zs = []
        for k in keys:
            x = raw[k][i]
            if k == "mfi14":
                z = None if x is None else (x - 50.0) / 12.5
            elif k == "cmf20":
                z = None if x is None else x / 0.08
            else:
                wins[k].add(x)
                z = wins[k].z(x)
            zs.append(None if z is None else clamp(z, -6.0, 6.0))
        live = [z for z in zs if z is not None]
        cov[i] = round(len(live) / float(len(keys)), 3)
        if i + 1 >= MIN_BARS and len(live) >= MIN_COMPONENTS:
            fis[i] = round(100.0 * math.tanh((sum(live) / len(live)) / 2.0), 1)

    res = {
        "dates": [b["date"] for b in bars],
        "close": [b.get("close") for b in bars],
        "dollar_vol": dv,
        "fis": fis,
        "intensity": [None if x is None else round(x, 3) for x in intensity_raw],
        "mfi14": [None if x is None else round(x, 1) for x in raw["mfi14"]],
        "cmf20": [None if x is None else round(x, 4) for x in raw["cmf20"]],
        "coverage": cov,
        "components_last": {k: raw[k][-1] for k in keys},
        "bars": n,
    }
    if tail:
        for k in ("dates", "close", "dollar_vol", "fis", "intensity",
                  "mfi14", "cmf20", "coverage"):
            res[k] = res[k][-tail:]
    return res


def compute_fis_pv(bars: list[dict]) -> dict:
    """單一時點的 FIS_pv。薄包裝，與時間序列共用同一份計算路徑。

    合併之前：單點與序列各有一份實作，兩者會漂移。合併之後只有一個真相來源。
    """
    out = {"fis": Val(tier=T3), "components": {}, "coverage": 0.0, "bars": len(bars),
           "intensity": None, "mfi14": None, "cmf20": None, "series": None}
    if len(bars) < MIN_BARS:
        out["fis"] = Val(None, T3, note="樣本不足 %d/%d 根" % (len(bars), MIN_BARS))
        return out

    s = compute_flow_series(bars)
    out["series"] = s
    out["coverage"] = s["coverage"][-1]
    out["intensity"] = s["intensity"][-1]
    out["mfi14"] = s["mfi14"][-1]
    out["cmf20"] = s["cmf20"][-1]
    out["components"] = {k: (None if v is None else round(v, 3))
                         for k, v in s["components_last"].items()}

    n_live = int(round(out["coverage"] * 6))
    if s["fis"][-1] is None:
        out["fis"] = Val(None, T3,
                         note="有效組件 %d < %d，拒絕合成" % (n_live, MIN_COMPONENTS))
    else:
        out["fis"] = Val(s["fis"][-1], T3, EV_ESTIMATED,
                         "price-volume composite (%d comps)" % n_live,
                         "T3 估流：僅方向與強度，不可換算金額")
    return out


def compute_returns(bars: list[dict], horizons=None) -> dict:
    horizons = horizons or HORIZONS
    out = {"horizons": {}, "ytd": Val(tier=T1), "last_close": Val(tier=T1),
           "last_date": "", "bars": len(bars)}
    if not bars:
        for n in horizons:
            out["horizons"][n] = Val(None, T1)
        return out
    closes = [b["close"] for b in bars]
    last = closes[-1]
    out["last_close"] = Val(last, T1, EV_OFFICIAL, "daily close")
    out["last_date"] = bars[-1]["date"]
    for n in horizons:
        if len(closes) > n and closes[-1 - n] > 0:
            out["horizons"][n] = Val(round((last / closes[-1 - n] - 1) * 100, 2),
                                     T1, EV_OFFICIAL, "close ratio")
        else:
            out["horizons"][n] = Val(None, T1, note="歷史不足 %dD" % n)
    year = bars[-1]["date"][:4]
    prior = [b for b in bars if b["date"][:4] < year]
    if prior and prior[-1]["close"] > 0:
        out["ytd"] = Val(round((last / prior[-1]["close"] - 1) * 100, 2), T1,
                         EV_OFFICIAL, "close ratio (%s base)" % prior[-1]["date"])
    else:
        out["ytd"] = Val(None, T1, note="無去年底基期")
    return out


def relative_strength(bars: list[dict], bench: list[dict], window=60) -> Val:
    """相對基準的超額報酬（百分點）。基準缺失 → PENDING，不用 0 代替。"""
    if len(bars) <= window or len(bench) <= window:
        return Val(None, T1, note="樣本不足 %dD" % window)
    bmap = {b["date"]: b["close"] for b in bench}
    dates = [b["date"] for b in bars if b["date"] in bmap]
    if len(dates) <= window:
        return Val(None, T1, note="與基準重疊交易日不足")
    d_now, d_then = dates[-1], dates[-1 - window]
    cmap = {b["date"]: b["close"] for b in bars}
    if not all(x and x > 0 for x in (cmap.get(d_then), bmap.get(d_then))):
        return Val(None, T1, note="基期價格無效")
    r_self = cmap[d_now] / cmap[d_then] - 1
    r_bench = bmap[d_now] / bmap[d_then] - 1
    return Val(round((r_self - r_bench) * 100, 2), T1, EV_DERIVED,
               "%dD excess vs %s" % (window, BENCHMARK))


# --------------------------------------------------------------------------- #
# 8.  APPEND-ONLY REGISTRIES  (只增不減)
# --------------------------------------------------------------------------- #

class UniverseRegistry:
    """ETF 探針宇宙。種子清單 + 使用者擴充，永不刪除，退場者轉 DORMANT。"""

    def __init__(self, path: Path):
        self.path = path
        self.data = {"schema": 1, "entries": {}, "updated": ""}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            doc = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and "entries" in doc:
                self.data.update(doc)
        except (OSError, ValueError) as exc:
            LOG.warn("universe registry 讀取失敗，改用種子清單：%s" % exc)

    def seed_and_merge(self, run_date: str) -> dict:
        rep = {"new": [], "total": 0}
        for ticker, name, region, asset, tier in UNIVERSE_SEED:
            e = self.data["entries"].get(ticker)
            if e is None:
                self.data["entries"][ticker] = {
                    "ticker": ticker, "name": name, "region": region,
                    "asset_class": asset, "risk_tier": tier,
                    "status": "ACTIVE", "first_seen": run_date, "last_ok": "",
                    "history": [{"date": run_date, "event": "SEEDED"}],
                }
                rep["new"].append(ticker)
            else:
                # 只補空欄，不覆寫使用者手改過的分類
                for k, v in (("name", name), ("region", region),
                             ("asset_class", asset), ("risk_tier", tier)):
                    e.setdefault(k, v)
                e.setdefault("status", "ACTIVE")
                e.setdefault("history", [])
        rep["total"] = len(self.data["entries"])
        return rep

    def active(self) -> list[dict]:
        return [e for e in self.data["entries"].values() if e.get("status") != "RETIRED"]

    def mark(self, ticker: str, ok: bool, run_date: str, reason: str = ""):
        e = self.data["entries"].get(ticker)
        if not e:
            return
        if ok:
            e["last_ok"] = run_date
            if e.get("status") == "DORMANT":
                e["status"] = "ACTIVE"
                e.setdefault("history", []).append({"date": run_date, "event": "REACTIVATED"})
            e["fail_streak"] = 0
        else:
            e["fail_streak"] = int(e.get("fail_streak", 0)) + 1
            if e["fail_streak"] >= 3 and e.get("status") == "ACTIVE":
                e["status"] = "DORMANT"
                e.setdefault("history", []).append(
                    {"date": run_date, "event": "WENT_DORMANT", "reason": reason[:120]})

    def save(self):
        self.data["updated"] = _dt.datetime.now().isoformat(timespec="seconds")
        write_json(self.path, self.data, keep_prev=True)


class SharesRegistry:
    """append-only 在外流通股數 / NAV 快照序列 —— T1 真流的唯一來源。

    ΔShares × NAV 必須由本引擎自己觀測到的兩個快照相減得出。累積到 2 筆之前，
    真流一律 PENDING，絕不用價量估算頂替。
    """

    def __init__(self, path: Path):
        self.path = path
        self.data = {"schema": 1, "snapshots": {}, "updated": ""}
        if path.exists():
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(doc, dict) and "snapshots" in doc:
                    self.data.update(doc)
            except (OSError, ValueError) as exc:
                LOG.warn("shares registry 讀取失敗：%s" % exc)

    def add(self, ticker, date, shares, nav):
        if shares is None and nav is None:
            return
        series = self.data["snapshots"].setdefault(ticker, [])
        for p in series:
            if p["date"] == date:
                if shares is not None:
                    p["shares"] = shares
                if nav is not None:
                    p["nav"] = nav
                return
        series.append({"date": date, "shares": shares, "nav": nav})
        series.sort(key=lambda p: p["date"])

    def primary_flow(self, ticker, lookback_days=20) -> Val:
        """ΔShares × NAV，單位美元。T1 真流。"""
        s = [p for p in self.data["snapshots"].get(ticker, []) if p.get("shares")]
        if len(s) < 2:
            return Val(None, T1, note="股數快照 %d 筆，需 ≥2 筆才有真流" % len(s))
        cutoff = (_dt.date.fromisoformat(s[-1]["date"])
                  - _dt.timedelta(days=lookback_days)).isoformat()
        window = [p for p in s if p["date"] >= cutoff]
        if len(window) < 2:
            window = s[-2:]
        total = 0.0
        used = 0
        for prev, cur in zip(window, window[1:]):
            nav = cur.get("nav") or prev.get("nav")
            if nav is None:
                continue
            total += (cur["shares"] - prev["shares"]) * nav
            used += 1
        if used == 0:
            return Val(None, T1, note="快照缺 NAV，無法換算金額")
        return Val(round(total, 0), T1, EV_DERIVED,
                   "ΔShares × NAV (%d intervals)" % used)

    def save(self):
        self.data["updated"] = _dt.datetime.now().isoformat(timespec="seconds")
        write_json(self.path, self.data, keep_prev=True)


def write_json(path: Path, obj, keep_prev=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    if keep_prev and path.exists():
        try:
            shutil.copy2(path, path.with_name(path.stem + "_prev.json"))
        except OSError:
            pass
    tmp.replace(path)


# --------------------------------------------------------------------------- #
# 9.  AGGREGATION  ── 籃子聚合（v3 E2：籃子優於單檔）
# --------------------------------------------------------------------------- #

def aggregate(probes: list[dict], key: str) -> list[dict]:
    """依 region 或 asset_class 聚合。

    籃子 FIS 用「成交金額加權」而非等權：一檔 20 億美元成交的 SPY 與一檔
    2000 萬美元的小型 ETF，對資金流的代表性本就不同。
    覆蓋率低於 50% 的籃子，FIS 回 PENDING（v3 的 coverage floor 概念）。
    """
    groups: dict[str, list[dict]] = {}
    for p in probes:
        groups.setdefault(p[key], []).append(p)

    out = []
    for gname, members in sorted(groups.items()):
        with_fis = [m for m in members if m["fis"]["fis"].ok]
        coverage = len(with_fis) / float(len(members)) if members else 0.0

        if with_fis and coverage >= 0.5:
            wsum = 0.0
            acc = 0.0
            for m in with_fis:
                w = m.get("dollar_vol") or 0.0
                w = w if w > 0 else 1.0
                acc += m["fis"]["fis"].value * w
                wsum += w
            fis = Val(round(acc / wsum, 1), T3, EV_ESTIMATED,
                      "dollar-volume weighted basket (%d/%d)" % (len(with_fis), len(members)))
        else:
            fis = Val(None, T3, note="籃子覆蓋率 %.0f%% < 50%%" % (coverage * 100))

        prim = [m["primary_flow"].value for m in members if m["primary_flow"].ok]
        primary = (Val(round(sum(prim), 0), T1, EV_DERIVED,
                       "Σ ΔShares×NAV (%d/%d 檔有快照)" % (len(prim), len(members)))
                   if prim else Val(None, T1, note="尚無成員具備 ≥2 筆股數快照"))

        rets = {}
        for n in HORIZONS:
            vs = [m["ret"]["horizons"][n].value for m in members
                  if m["ret"]["horizons"][n].ok]
            rets[n] = (Val(round(sum(vs) / len(vs), 2), T1, EV_DERIVED,
                           "equal-weight mean (%d)" % len(vs)) if vs else Val(None, T1))

        rs = [m["rs"].value for m in members if m["rs"].ok]
        out.append({
            "group": gname,
            "label": (REGION_LABEL if key == "region" else ASSET_LABEL).get(gname, gname),
            "n": len(members), "n_fis": len(with_fis), "coverage": round(coverage, 3),
            "fis": fis, "primary_flow": primary, "ret": rets,
            "rs": (Val(round(sum(rs) / len(rs), 2), T1, EV_DERIVED, "mean excess")
                   if rs else Val(None, T1)),
            "members": [m["ticker"] for m in members],
        })
    out.sort(key=lambda g: -(g["fis"].value if g["fis"].ok else -999))
    return out


def dual_verify(probes: list[dict]) -> list[dict]:
    """雙重驗證對：同曝險的兩檔 ETF 若 FIS 方向相反，該訊號不可信。"""
    idx = {p["ticker"]: p for p in probes}
    out = []
    for a, b in DUAL_VERIFY:
        pa, pb = idx.get(a), idx.get(b)
        if not pa or not pb:
            continue
        fa, fb = pa["fis"]["fis"], pb["fis"]["fis"]
        if not (fa.ok and fb.ok):
            verdict, css = "無法驗證", "P"
            detail = "任一方 FIS 為 PENDING"
        elif fa.value * fb.value < 0:
            verdict, css = "背離 · 訊號不可信", "BAD"
            detail = "%s %+.1f vs %s %+.1f 方向相反" % (a, fa.value, b, fb.value)
        elif abs(fa.value - fb.value) > 40:
            verdict, css = "強度分歧", "WARN"
            detail = "差距 %.1f 點" % abs(fa.value - fb.value)
        else:
            verdict, css = "一致 · 可採信", "OK"
            detail = "%s %+.1f / %s %+.1f" % (a, fa.value, b, fb.value)
        out.append({"pair": "%s ↔ %s" % (a, b), "verdict": verdict,
                    "css": css, "detail": detail})
    return out


def risk_appetite(probes: list[dict]) -> dict:
    """RORO：風險端籃子 FIS 減避險端籃子 FIS。兩端任一 PENDING 則整體 PENDING。"""
    risk_on = [p for p in probes if p["risk_tier"] >= 4 and p["fis"]["fis"].ok]
    risk_off = [p for p in probes if p["risk_tier"] <= 2 and p["fis"]["fis"].ok]
    if len(risk_on) < 3 or len(risk_off) < 3:
        return {"score": Val(None, T3, note="風險/避險端樣本不足"),
                "n_on": len(risk_on), "n_off": len(risk_off), "regime": "—", "desc": "資料不足以判定"}
    on = sum(p["fis"]["fis"].value for p in risk_on) / len(risk_on)
    off = sum(p["fis"]["fis"].value for p in risk_off) / len(risk_off)
    score = round(on - off, 1)
    if score >= 40:
        regime, desc = "RISK-ON 擴張", "資金向高風險端集中，避險端同步失血。"
    elif score >= 12:
        regime, desc = "溫和偏多", "風險端佔優，但避險端未見明顯撤離。"
    elif score > -12:
        regime, desc = "中性均衡", "風險與避險兩端資金強度接近，無明確方向。"
    elif score > -40:
        regime, desc = "溫和避險", "資金開始偏向債券與現金等價端。"
    else:
        regime, desc = "RISK-OFF 收縮", "高風險端遭撤離，資金湧入主權債與現金等價。"
    return {"score": Val(score, T3, EV_ESTIMATED, "risk_on basket − risk_off basket"),
            "n_on": len(risk_on), "n_off": len(risk_off),
            "on": round(on, 1), "off": round(off, 1), "regime": regime, "desc": desc}


# --------------------------------------------------------------------------- #
# 10.  PIPELINE
# --------------------------------------------------------------------------- #

def build_dataset(src: Sources, uni: UniverseRegistry, shares: SharesRegistry,
                  args, log: Log) -> dict:
    run_date = today_utc().isoformat()

    log.step("階段 1/4  宇宙登錄（append-only）")
    rep = uni.seed_and_merge(run_date)
    entries = uni.active()
    log.ok("探針宇宙 %d 檔（新登錄 %d）" % (len(entries), len(rep["new"])))

    log.step("階段 2/4  抓取日線（%d 檔，%d 執行緒）" % (len(entries), args.workers))
    bars_map: dict[str, list[dict]] = {}
    src_map: dict[str, str] = {}
    fails: list[tuple[str, str]] = []

    def _pull(e):
        try:
            b, name = src.daily(e["ticker"])
            return e["ticker"], b, name, ""
        except Exception as exc:                          # noqa: BLE001
            return e["ticker"], [], "", str(exc)[:100]

    with _cf.ThreadPoolExecutor(max_workers=max(1, min(args.workers, len(entries) or 1))) as pool:
        for i, (t, b, name, err) in enumerate(pool.map(_pull, entries), 1):
            bars_map[t] = b
            src_map[t] = name
            uni.mark(t, bool(b), run_date, err)
            if err:
                fails.append((t, err))
            log.info("  %2d/%d  %-6s %4d 根 %s" % (i, len(entries), t, len(b), name or "FAIL"))
    if fails:
        log.warn("日線失敗 %d 檔：%s" % (len(fails), ", ".join(t for t, _ in fails[:8])))

    log.step("階段 3/4  股數/NAV 快照（T1 真流唯一入口）")
    n_shares = 0
    for e in entries:
        t = e["ticker"]
        if not bars_map.get(t):
            continue
        try:
            sn = src.shares_nav_yahoo(t)
        except Exception:                                  # noqa: BLE001
            sn = {}
        nav = sn.get("nav")
        if nav is None and bars_map[t]:
            nav = None      # 不用收盤價假裝 NAV：那會讓 T1 金額失真
        if sn.get("shares"):
            shares.add(t, bars_map[t][-1]["date"], sn.get("shares"), nav)
            n_shares += 1
    log.ok("股數快照取得 %d/%d 檔" % (n_shares, len(entries)))
    if n_shares == 0:
        log.warn("無股數來源 → T1 真流全數 PENDING，本次僅有 T3 方向訊號")

    log.step("階段 4/4  FIS_pv 合成與聚合")
    bench = bars_map.get(BENCHMARK, [])
    probes = []
    for e in entries:
        t = e["ticker"]
        bars = bars_map.get(t, [])
        fis = compute_fis_pv(bars)
        series = fis.pop("series", None)
        ret = compute_returns(bars)
        dv = None
        if bars and bars[-1].get("volume") and bars[-1].get("close"):
            dv = bars[-1]["close"] * bars[-1]["volume"]
        probes.append({
            "ticker": t, "name": e.get("name", ""),
            "region": e.get("region", "GLOBAL"),
            "asset_class": e.get("asset_class", "EQUITY"),
            "risk_tier": int(e.get("risk_tier", 3)),
            "status": e.get("status", "ACTIVE"),
            "bars": len(bars), "source": src_map.get(t, ""),
            "dollar_vol": dv,
            "fis": fis,
            "series": series,
            "ret": ret,
            "rs": relative_strength(bars, bench) if t != BENCHMARK else Val(0.0, T1, EV_DERIVED, "self"),
            "primary_flow": shares.primary_flow(t),
        })

    ok_fis = sum(1 for p in probes if p["fis"]["fis"].ok)
    ok_t1 = sum(1 for p in probes if p["primary_flow"].ok)
    log.ok("FIS_pv 成立 %d/%d 檔 · T1 真流成立 %d 檔" % (ok_fis, len(probes), ok_t1))

    timeline = build_timeline(probes, tail=args.tail)
    log.ok("時間軸資料塊：%d 個交易日 × %d 檔" % (len(timeline["dates"]), len(timeline["series"])))

    by_region = aggregate(probes, "region")
    by_asset = aggregate(probes, "asset_class")
    roro = risk_appetite(probes)
    dv_pairs = dual_verify(probes)

    data_date = max([p["ret"]["last_date"] for p in probes if p["ret"]["last_date"]] or [""])
    return {
        "meta": {
            "engine": __engine__, "version": __version__,
            "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "run_date": run_date, "data_date": data_date,
            "n_probes": len(probes), "n_fis": ok_fis, "n_primary": ok_t1,
            "benchmark": BENCHMARK, "group_by": args.group,
            "http": dict(src.http.stats),
            "failures": [{"ticker": t, "error": e} for t, e in fails],
        },
        "probes": probes,
        "timeline": timeline,
        "by_region": by_region,
        "by_asset": by_asset,
        "roro": roro,
        "dual_verify": dv_pairs,
        "dormant": [e["ticker"] for e in uni.data["entries"].values()
                    if e.get("status") == "DORMANT"],
    }


# --------------------------------------------------------------------------- #
# 10b. TIMELINE  ── 跨資產可比較的時間軸資料塊
# --------------------------------------------------------------------------- #

def build_timeline(probes: list[dict], tail: int = 250) -> dict:
    """組出共用日期軸 + 每檔的 close / FIS / intensity 三條序列。

    跨資產可比較的關鍵在正規化，而正規化留給前端做，因為 CRITERIA 是可變的：
      價 → 由使用者選定的視窗起點 rebase 成 100（不同幣別/價位可疊圖）
      量 → intensity＝成交金額 / 自身 60 日中位數（自我參照，故 SPY 與 GLD 可比）
      流 → FIS_pv ±100（設計上就已無量綱）
    後端只送這三條原始可比序列，門檻與視窗一律不寫死。
    """
    all_dates = set()
    for p in probes:
        s = p.get("series") or {}
        all_dates.update(s.get("dates") or [])
    dates = sorted(all_dates)[-tail:]
    idx = {d: i for i, d in enumerate(dates)}
    n = len(dates)

    series = {}
    for p in probes:
        s = p.get("series") or {}
        ds = s.get("dates") or []
        if not ds:
            continue
        c = [None] * n
        f = [None] * n
        v = [None] * n
        for k, d in enumerate(ds):
            j = idx.get(d)
            if j is None:
                continue
            cv = s["close"][k]
            c[j] = None if cv is None else round(cv, 4)
            f[j] = s["fis"][k]
            v[j] = s["intensity"][k]
        if not any(x is not None for x in c):
            continue
        series[p["ticker"]] = {"c": c, "f": f, "v": v}

    return {"dates": dates, "series": series,
            "meta": {t: {"name": p["name"], "region": p["region"],
                         "asset": p["asset_class"], "tier": p["risk_tier"]}
                     for p in probes for t in [p["ticker"]] if t in series}}


# --------------------------------------------------------------------------- #
# 11.  RENDER
# --------------------------------------------------------------------------- #

def esc(s):
    import html as _h
    return _h.escape("" if s is None else str(s), quote=True)


def fmt_sig(v: Val, digits=1, suffix=""):
    if not v.ok:
        return "—"
    return ("+" if v.value >= 0 else "") + ("%.*f" % (digits, v.value)) + suffix


def fmt_usd(v: Val):
    """T1 金額。只有 T1 才准帶單位。"""
    if not v.ok:
        return "—"
    x = v.value
    sign = "+" if x >= 0 else "−"
    a = abs(x)
    if a >= 1e9:
        return "%s$%.2fB" % (sign, a / 1e9)
    if a >= 1e6:
        return "%s$%.1fM" % (sign, a / 1e6)
    return "%s$%.0f" % (sign, a)


def sc(v: Val):
    if not v.ok:
        return "color:var(--mut2);"
    return "color:var(--up);" if v.value >= 0 else "color:var(--down);"


def badge(v: Val):
    col = {EV_OFFICIAL: "var(--gn)", EV_DERIVED: "var(--teal)",
           EV_ESTIMATED: "var(--am)", EV_PENDING: "var(--mut2)"}
    tip = "%s · %s" % (v.tier, EVIDENCE_LABEL.get(v.evidence, v.evidence))
    if v.note:
        tip += " · " + v.note
    if v.source:
        tip += " · " + v.source
    return ('<span class="ev" style="background:%s" title="%s">%s</span>'
            % (col.get(v.evidence, "var(--mut2)"), esc(tip), esc(v.tier)))


def fis_bar(v: Val):
    """-100..100 的雙向條。PENDING 顯示灰色虛位，不畫成 0。"""
    if not v.ok:
        return '<div class="fb"><div class="fbz"></div><span class="fbn">—</span></div>'
    w = min(50.0, abs(v.value) / 2.0)
    col = "var(--up)" if v.value >= 0 else "var(--down)"
    left = 50.0 if v.value >= 0 else 50.0 - w
    return ('<div class="fb"><div class="fbz"></div>'
            '<div class="fbf" style="left:%.1f%%;width:%.1f%%;background:%s"></div>'
            '<span class="fbn" style="%s">%s</span></div>'
            % (left, w, col, sc(v), fmt_sig(v)))


def render_html(ds: dict, log: Log) -> str:
    meta = ds["meta"]
    groups = ds["by_region"] if meta["group_by"] == "region" else ds["by_asset"]
    other = ds["by_asset"] if meta["group_by"] == "region" else ds["by_region"]

    roro = ds["roro"]
    cards = [
        ("風險偏好 RORO", fmt_sig(roro["score"]), roro["regime"],
         "var(--up)" if (roro["score"].ok and roro["score"].value >= 0) else "var(--down)"),
        ("探針檔數", str(meta["n_probes"]),
         "FIS 成立 %d 檔" % meta["n_fis"], "var(--blue)"),
        ("T1 真流", "%d 檔" % meta["n_primary"],
         "ΔShares×NAV 已成立" if meta["n_primary"] else "股數快照累積中", "var(--teal)"),
        ("資料日", meta["data_date"] or "—", "基準 %s" % meta["benchmark"], "var(--am)"),
    ]
    card_html = "".join(
        '<div class="card"><div class="cl">%s</div><div class="cv" style="color:%s">%s</div>'
        '<div class="cs">%s</div></div>' % (esc(l), c, esc(v), esc(s)) for l, v, s, c in cards)

    def group_rows(gs):
        rows = []
        for i, g in enumerate(gs):
            rets = "".join('<td class="num" style="%s">%s</td>'
                           % (sc(g["ret"][n]), fmt_sig(g["ret"][n], 1, "%"))
                           for n in (5, 20, 60, 240))
            rows.append(
                '<tr style="background:%s"><td><b>%s</b> <span class="dim mono">%s</span></td>'
                '<td class="num dim">%d 檔</td><td style="min-width:190px">%s %s</td>'
                '<td class="num">%s %s</td>%s'
                '<td class="num" style="%s">%s</td><td class="num dim">%.0f%%</td></tr>'
                % ("#f6f4ef" if i % 2 else "var(--paper)", esc(g["label"]), esc(g["group"]),
                   g["n"], fis_bar(g["fis"]), badge(g["fis"]),
                   fmt_usd(g["primary_flow"]), badge(g["primary_flow"]), rets,
                   sc(g["rs"]), fmt_sig(g["rs"], 1, "pp"), g["coverage"] * 100))
        return "".join(rows) or '<tr><td colspan="9" class="empty">無資料</td></tr>'

    probe_rows = []
    for i, p in enumerate(sorted(ds["probes"],
                                 key=lambda x: -(x["fis"]["fis"].value
                                                 if x["fis"]["fis"].ok else -999))):
        f = p["fis"]
        probe_rows.append(
            '<tr style="background:%s"><td class="mono"><b>%s</b></td><td>%s</td>'
            '<td class="dim">%s</td><td class="dim">%s</td><td class="num dim">T%d</td>'
            '<td style="min-width:190px">%s %s</td>'
            '<td class="num dim">%s</td><td class="num dim">%s</td>'
            '<td class="num">%s %s</td>'
            '<td class="num" style="%s">%s</td><td class="num" style="%s">%s</td>'
            '<td class="num dim">%d</td></tr>'
            % ("#f6f4ef" if i % 2 else "var(--paper)", esc(p["ticker"]), esc(p["name"]),
               esc(REGION_LABEL.get(p["region"], p["region"])),
               esc(ASSET_LABEL.get(p["asset_class"], p["asset_class"])),
               p["risk_tier"],
               fis_bar(f["fis"]), badge(f["fis"]),
               ("%.2fx" % f["intensity"]) if f.get("intensity") else "—",
               ("%.0f" % f["mfi14"]) if f.get("mfi14") is not None else "—",
               fmt_usd(p["primary_flow"]), badge(p["primary_flow"]),
               sc(p["ret"]["horizons"][20]), fmt_sig(p["ret"]["horizons"][20], 1, "%"),
               sc(p["rs"]), fmt_sig(p["rs"], 1, "pp"),
               p["bars"]))

    dv_rows = "".join(
        '<tr><td class="mono">%s</td><td><span class="vd %s">%s</span></td>'
        '<td class="dim">%s</td></tr>'
        % (esc(d["pair"]), d["css"].lower(), esc(d["verdict"]), esc(d["detail"]))
        for d in ds["dual_verify"]) or '<tr><td colspan="3" class="empty">無驗證對</td></tr>'

    fail_rows = "".join(
        '<tr><td class="mono">%s</td><td class="dim">%s</td></tr>'
        % (esc(f["ticker"]), esc(f["error"])) for f in meta["failures"])
    fail_block = ('<div class="note"><b>抓取失敗（連續 3 次自動轉 DORMANT，資料不刪）</b>'
                  '<table class="mini"><tbody>%s</tbody></table></div>' % fail_rows) if fail_rows else ""

    log_rows = "".join(
        '<div class="lg %s"><span class="lt">%6.1fs</span><span class="ll">%s</span>'
        '<span class="lm">%s</span></div>' % (lv.lower(), t, esc(lv), esc(msg))
        for lv, msg, t in log.lines)

    tl = ds.get("timeline") or {"dates": [], "series": {}, "meta": {}}
    return HTML.substitute({
        "timeline_json": json.dumps(tl, ensure_ascii=False, separators=(",", ":")),
        "tl_days": len(tl["dates"]),
        "tl_n": len(tl["series"]),
        "reson": RESON,
        "generated": esc(meta["generated_at"]),
        "data_date": esc(meta["data_date"] or "—"),
        "engine": esc("%s %s" % (__engine__, __version__)),
        "cards": card_html,
        "roro_regime": esc(roro["regime"]),
        "roro_desc": esc(roro["desc"]),
        "roro_detail": esc("風險端 %s（%d 檔） / 避險端 %s（%d 檔）"
                           % (roro.get("on", "—"), roro["n_on"],
                              roro.get("off", "—"), roro["n_off"])),
        "grp_title": "區域" if meta["group_by"] == "region" else "資產類別",
        "grp_rows": group_rows(groups),
        "oth_title": "資產類別" if meta["group_by"] == "region" else "區域",
        "oth_rows": group_rows(other),
        "probe_rows": "".join(probe_rows) or '<tr><td colspan="12" class="empty">無資料</td></tr>',
        "dv_rows": dv_rows,
        "fail_block": fail_block,
        "log_rows": log_rows,
        "n_probes": meta["n_probes"], "n_fis": meta["n_fis"], "n_primary": meta["n_primary"],
        "net": meta["http"].get("net", 0), "cache": meta["http"].get("cache", 0),
        "fail": meta["http"].get("fail", 0),
    })


# --------------------------------------------------------------------------- #
# 12.  HTML SHELL
# --------------------------------------------------------------------------- #

HTML = _string.Template(r"""<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · 全球 ETF 資金流動監控</title>
<style>
:root{--bg:#f5f4f0;--paper:#fff;--paper2:#fafaf8;--ink:#1e1d1a;--ink2:#33403f;
--mut:#6b6860;--mut2:#9c9890;--line:#dbd9d3;--soft:#ecebe6;--accent:#439a9a;
--blue:#4c78a8;--teal:#439a9a;--up:#c96b5a;--down:#5a9e6f;--am:#c4943a;
--vi:#7a6daa;--gn:#5a9e6f;--reson:${reson};}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg)}
body{color:var(--ink2);font-family:'DM Sans','Noto Sans TC','Microsoft JhengHei',system-ui,sans-serif;
font-size:11px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1400px;margin:0 auto;padding:0 22px 46px}
.topbar{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);z-index:50}
header{position:relative;padding:18px 0 9px;margin-bottom:12px;border-bottom:2px solid var(--ink)}
.eyebrow{font:700 10px 'DM Mono',ui-monospace,monospace;letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:6px}
h1{font:800 18px/1.2 'Syne',sans-serif;color:var(--ink)}
h1 span{color:var(--up)}
.sub{margin-top:5px;font-size:10.5px;color:var(--mut);max-width:760px}
.sub b{color:var(--ink2)}
.hmeta{position:absolute;top:4px;right:0;display:flex;flex-direction:column;align-items:flex-end;gap:3px}
.hmeta span{font:500 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut)}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:9px 11px}
.cl{font:600 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut);letter-spacing:.6px;text-transform:uppercase}
.cv{font:800 19px/1.15 'Syne',sans-serif;margin:3px 0 1px}
.cs{font-size:9px;color:var(--mut2)}
.roro{background:#1e1d1a;border-radius:3px;padding:10px 14px;margin-bottom:12px;display:flex;
align-items:center;gap:14px;flex-wrap:wrap}
.roro .rt{font:800 13px 'Syne',sans-serif;color:#fff}
.roro .rd{font-size:9.5px;color:#cfcabf;flex:1;min-width:240px}
.roro .rx{font:500 8.5px 'DM Mono',ui-monospace,monospace;color:#8a948f}
.tabs{display:flex;gap:3px;margin-bottom:-1px}
.tab{font:700 10px 'DM Mono',ui-monospace,monospace;padding:7px 14px;border:1px solid var(--line);
border-bottom:none;border-radius:3px 3px 0 0;background:var(--soft);color:var(--mut);cursor:pointer;user-select:none}
.tab.on{background:var(--bg);color:var(--ink);border-color:var(--ink);box-shadow:0 -2px 0 var(--accent) inset}
.panel{display:none;border:1px solid var(--line);background:var(--paper);border-radius:0 3px 3px 3px;padding:12px}
.panel.on{display:block}
.ptitle{font:700 12px 'Syne',sans-serif;color:var(--ink);margin-bottom:8px}
.ptitle em{font:500 9px 'DM Mono',ui-monospace,monospace;color:var(--mut2);font-style:normal;margin-left:8px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:10px}
th{background:var(--ink);color:#fff;font:700 9px 'DM Mono',ui-monospace,monospace;padding:6px 7px;
text-align:left;white-space:nowrap;position:sticky;top:0;z-index:2}
td{padding:5px 7px;border-bottom:1px solid var(--line);white-space:nowrap}
td.num{text-align:right;font-family:'DM Mono',ui-monospace,monospace}
.mono{font-family:'DM Mono',ui-monospace,monospace}
.dim{color:var(--mut2)}
td.empty{text-align:center;color:var(--mut);padding:22px;white-space:normal}
.ev{display:inline-block;color:#fff;border-radius:2px;padding:0 4px;
font:700 7.5px 'DM Mono',ui-monospace,monospace;vertical-align:1px;opacity:.85;cursor:help}
.fb{position:relative;height:14px;width:180px;background:var(--soft);border-radius:2px;display:inline-block}
.fbz{position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--mut2);opacity:.6}
.fbf{position:absolute;top:2px;bottom:2px;border-radius:1px}
.fbn{position:absolute;right:4px;top:0;line-height:14px;font:700 9px 'DM Mono',ui-monospace,monospace}
.vd{display:inline-block;color:#fff;border-radius:2px;padding:1px 6px;font-size:9px;font-weight:700}
.vd.ok{background:var(--gn)} .vd.warn{background:var(--am)}
.vd.bad{background:var(--up)} .vd.p{background:var(--mut2)}
.note{margin-top:10px;border:1px solid var(--line);border-left:3px solid var(--am);border-radius:3px;
padding:9px 11px;background:var(--paper2);font-size:9.5px;color:var(--mut);line-height:1.7}
.note b{color:var(--ink2)}
table.mini{margin-top:6px;font-size:9px}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font-size:9px;color:var(--mut)}
.legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px;vertical-align:-1px}
.runlog{max-height:300px;overflow:auto;border:1px solid var(--line);border-radius:3px;background:#1e1d1a;padding:8px}
.lg{font:500 9px/1.6 'DM Mono',ui-monospace,monospace;color:#cfcabf;display:flex;gap:8px}
.lg .lt{color:#6b6860;width:48px;text-align:right;flex:none}
.lg .ll{width:34px;flex:none}
.lg.ok .ll{color:#7fd0a0}.lg.warn .ll{color:#c4943a}.lg.err .ll{color:#c96b5a}
.lg.step .ll{color:#4c78a8}.lg.info .ll{color:#6b6860}
footer{margin-top:18px;padding-top:9px;border-top:1px solid var(--line);display:flex;
justify-content:space-between;font:600 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut2);flex-wrap:wrap;gap:8px}
.crit{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end;background:var(--paper2);
border:1px solid var(--line);border-radius:3px;padding:9px 12px;margin-bottom:10px}
.cg{display:flex;flex-direction:column;gap:3px}
.cg label{font:700 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut);letter-spacing:.5px;text-transform:uppercase}
.cg label b{color:var(--ink);font-size:9.5px}
.cg select,.cg input[type=range]{font:inherit;font-size:10px;border:1px solid var(--line);
border-radius:2px;background:var(--paper);padding:3px 5px;color:var(--ink2)}
.cg input[type=range]{width:110px;padding:0}
.btn{font:700 9px 'DM Mono',ui-monospace,monospace;background:var(--soft);border:1px solid var(--line);
border-radius:2px;padding:5px 10px;cursor:pointer;color:var(--ink2);user-select:none}
.btn:hover{border-color:var(--ink2)}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px}
.chip{font:600 9px 'DM Mono',ui-monospace,monospace;border:1px solid var(--line);border-radius:2px;
padding:3px 8px;cursor:pointer;user-select:none;background:var(--paper);color:var(--mut2)}
.chip.on{color:#fff;border-color:transparent}
.chart-title{font:700 10px 'DM Mono',ui-monospace,monospace;color:var(--ink);margin:12px 0 5px;
letter-spacing:.5px;text-transform:uppercase}
.chart-title .dim{font-weight:500;text-transform:none;letter-spacing:0}
.chart{background:var(--paper2);border:1px solid var(--line);border-radius:3px;padding:6px;overflow-x:auto}
.chart svg{display:block}
.gl{fill:none;stroke-width:1.4}
.ax{stroke:var(--line);stroke-width:1}
.axt{font:500 8px 'DM Mono',ui-monospace,monospace;fill:var(--mut2)}
.rl{font:600 8.5px 'DM Mono',ui-monospace,monospace;fill:var(--ink2)}
.hot{stroke:var(--ink);stroke-width:.5;stroke-dasharray:3 3;opacity:.5}
.empty-chart{padding:26px;text-align:center;color:var(--mut);font-size:10px}
@media(max-width:1100px){.cards{grid-template-columns:repeat(2,1fr)}}
@media print{@page{size:A4 landscape;margin:8mm}.tab{display:none}.panel{display:block!important;page-break-before:always}th{position:static}}
</style></head><body>
<div class="topbar"></div>
<div class="wrap">
<header>
  <div class="eyebrow">VERITAS INTELLIGENCE ANALYTICS · GLOBAL ETF CAPITAL-FLOW MONITOR · MDL008</div>
  <h1>全球 ETF <span>資金流動監控</span> · Global ETF Capital-Flow Monitor</h1>
  <p class="sub">以 ETF 為探針，量測各區股市與各類金融商品的資金流向。
  <b>T1 真流</b>＝ΔSharesOutstanding×NAV（有金額）；<b>T3 估流 FIS_pv</b>＝價量合成，
  <b>只給方向與強度，永遠不換算成金額</b>。查無來源顯示 —，不以模擬數字填充。紅漲綠跌。</p>
  <div class="hmeta">
    <span>產生 ${generated}</span><span>資料日 ${data_date}</span>
    <span>${engine}</span>
    <span>HTTP net ${net} · cache ${cache} · fail ${fail}</span>
  </div>
</header>

<div class="cards">${cards}</div>

<div class="roro">
  <span class="rt">${roro_regime}</span>
  <span class="rd">${roro_desc}</span>
  <span class="rx">${roro_detail}</span>
</div>

<div class="tabs">
  <div class="tab on" data-p="tl">時間軸比較</div>
  <div class="tab" data-p="grp">${grp_title}資金流</div>
  <div class="tab" data-p="oth">${oth_title}資金流</div>
  <div class="tab" data-p="probe">個別探針</div>
  <div class="tab" data-p="verify">雙重驗證</div>
  <div class="tab" data-p="log">執行日誌</div>
</div>

<div class="panel on" id="p-tl">
  <div class="ptitle">量價可比較時間軸<em>${tl_days} 交易日 × ${tl_n} 檔 · 下列所有 CRITERIA 皆為變數，改動即時重算</em></div>

  <div class="crit">
    <div class="cg"><label>視窗</label>
      <select id="cWin"><option value="20">20D</option><option value="60">60D</option>
      <option value="120" selected>120D</option><option value="250">250D</option></select></div>
    <div class="cg"><label>面板指標</label>
      <select id="cMetric">
        <option value="price">價格 rebase=100</option>
        <option value="fis" selected>資金流 FIS_pv</option>
        <option value="vol">量能強度 ×中位數</option>
        <option value="rs">相對基準超額</option>
      </select></div>
    <div class="cg"><label>分組</label>
      <select id="cGroup"><option value="region" selected>區域</option>
      <option value="asset">資產類別</option><option value="tier">風險階</option>
      <option value="none">不分組</option></select></div>
    <div class="cg"><label>聚合</label>
      <select id="cAgg"><option value="basket" selected>籃子（成交金額加權）</option>
      <option value="each">逐檔</option></select></div>
    <div class="cg"><label>熱區門檻 <b id="cHotV">30</b></label>
      <input type="range" id="cHot" min="5" max="80" step="5" value="30"></div>
    <div class="cg"><label>平滑 <b id="cSmoothV">5</b>D</label>
      <input type="range" id="cSmooth" min="1" max="21" step="2" value="5"></div>
    <div class="cg"><label>最少樣本 <b id="cMinV">60</b></label>
      <input type="range" id="cMin" min="0" max="200" step="10" value="60"></div>
    <div class="cg"><label>排序</label>
      <select id="cSort"><option value="last" selected>期末值</option>
      <option value="mean">期間均值</option><option value="delta">期間變化</option>
      <option value="name">名稱</option></select></div>
    <div class="cg"><span class="btn" id="cReset">重設</span></div>
  </div>
  <div id="cFilter" class="chips"></div>

  <div class="chart-title">趨勢疊圖 <span class="dim" id="tTrend"></span></div>
  <div id="chTrend" class="chart"></div>

  <div class="chart-title">資金流時間熱圖 <span class="dim">列＝標的／籃子，欄＝交易日，紅進綠出；灰＝樣本不足</span></div>
  <div id="chHeat" class="chart"></div>

  <div class="chart-title">量價象限 <span class="dim">X＝期間價格動能%，Y＝期間平均 FIS_pv，泡泡＝量能強度</span></div>
  <div id="chQuad" class="chart"></div>

  <div class="note"><b>為什麼這樣才叫「可比較」：</b>SPY 單日成交約 300 億美元、GLD 約 20 億，
  絕對金額並排沒有意義。此頁三條序列都經過自我參照正規化——價格由視窗起點 rebase 成 100、
  量能除以自身 60 日中位數、FIS_pv 本身就是 ±100 無量綱——因此黃金、公債、台股 ETF、
  半導體類股可以放在同一張圖上直接比。<b>門檻與視窗全是拉桿</b>，不是寫死的常數；
  你改一次，圖與熱區判定就重算一次。樣本不足者一律留白，不補值。</div>
</div>

<div class="panel" id="p-grp">
  <div class="ptitle">${grp_title}別資金流<em>籃子以成交金額加權 · 覆蓋率 &lt;50% 判 PENDING</em></div>
  <div class="scroll"><table><thead><tr>
  <th>${grp_title}</th><th>成員</th><th>FIS_pv 估流強度 (T3)</th><th>T1 真流 (ΔShares×NAV)</th>
  <th>5D</th><th>20D</th><th>60D</th><th>240D</th><th>相對 ACWI</th><th>覆蓋</th>
  </tr></thead><tbody>${grp_rows}</tbody></table></div>
  <div class="legend">
    <span><i style="background:var(--gn)"></i>V 官方</span>
    <span><i style="background:var(--teal)"></i>Der 推導</span>
    <span><i style="background:var(--am)"></i>Est 價量估算（僅方向）</span>
    <span><i style="background:var(--mut2)"></i>P 待補（顯示 —）</span>
    <span>徽章上的 T1/T3 為真值階梯，滑過可看來源。</span>
  </div>
</div>

<div class="panel" id="p-oth">
  <div class="ptitle">${oth_title}別資金流<em>同一把尺的交叉切面</em></div>
  <div class="scroll"><table><thead><tr>
  <th>${oth_title}</th><th>成員</th><th>FIS_pv 估流強度 (T3)</th><th>T1 真流 (ΔShares×NAV)</th>
  <th>5D</th><th>20D</th><th>60D</th><th>240D</th><th>相對 ACWI</th><th>覆蓋</th>
  </tr></thead><tbody>${oth_rows}</tbody></table></div>
</div>

<div class="panel" id="p-probe">
  <div class="ptitle">個別 ETF 探針<em>依 FIS_pv 降冪 · 強度倍數為今日成交金額／60日中位數</em></div>
  <div class="scroll"><table><thead><tr>
  <th>代碼</th><th>名稱</th><th>區域</th><th>資產</th><th>風險階</th>
  <th>FIS_pv (T3)</th><th>強度</th><th>MFI14</th><th>T1 真流</th>
  <th>20D</th><th>相對 ACWI</th><th>樣本</th>
  </tr></thead><tbody>${probe_rows}</tbody></table></div>
  ${fail_block}
</div>

<div class="panel" id="p-verify">
  <div class="ptitle">雙重驗證<em>同曝險兩檔 ETF 方向相反時，該訊號不予採信</em></div>
  <div class="scroll"><table><thead><tr><th>驗證對</th><th>判定</th><th>細節</th></tr></thead>
  <tbody>${dv_rows}</tbody></table></div>
  <div class="note"><b>為什麼要雙重驗證：</b>單一 ETF 的價量會被自身流動性、造市商庫存與
  期權到期扭曲。HYG 與 JNK 追同一批高收益債，若兩者 FIS 方向相反，代表訊號來自該檔自身的
  微結構雜訊而非真實資金流，此時應直接棄用，而不是取平均值粉飾。</div>
</div>

<div class="panel" id="p-log">
  <div class="ptitle">執行日誌<em>${n_probes} 檔探針 · FIS 成立 ${n_fis} · T1 真流 ${n_primary}</em></div>
  <div class="runlog">${log_rows}</div>
  <div class="note"><b>如何讓 T1 真流長出來：</b>ΔShares×NAV 必須由本引擎自己觀測到的
  兩筆股數快照相減得出，因此首次執行一定是 —。每日排程跑一次，第二天起 T1 欄位開始有金額，
  20 個交易日後即具備完整的月度真實申贖流。在那之前，畫面上只會有 T3 方向訊號，
  <b>不會有任何被偽裝成金額的估算值</b>。</div>
</div>

<footer><span>VERITAS INTELLIGENCE ANALYTICS</span>
<span>${engine} · ${generated} · Data ${data_date}</span></footer>
</div>
<script>
(function(){
  var tabs=document.querySelectorAll('.tab');
  tabs.forEach(function(t){t.addEventListener('click',function(){
    tabs.forEach(function(x){x.classList.remove('on')});
    document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('on')});
    t.classList.add('on');
    var el=document.getElementById('p-'+t.dataset.p); if(el){el.classList.add('on')}
  })});

/* ============ 時間軸比較引擎：所有 CRITERIA 皆為變數，前端即時重算 ============ */
var TL = ${timeline_json};

var GCOL = {US:"#4c78a8",EU:"#7a6daa",JP:"#b05580",APAC:"#439a9a",EM:"#c4943a",
            CN:"#c96b5a",TW:"#5a9e6f",GLOBAL:"#6b6860",
            EQUITY:"#4c78a8",BOND:"#439a9a",CREDIT:"#c4943a",COMMODITY:"#b05580",
            FX:"#6b6860",CRYPTO:"#7a6daa",REIT:"#5a9e6f",CASH:"#9c9890",
            "1":"#439a9a","2":"#4c78a8","3":"#9c9890","4":"#c4943a","5":"#c96b5a"};
var GLAB = {US:"美國",EU:"歐洲",JP:"日本",APAC:"亞太成熟",EM:"新興市場",CN:"中國",
            TW:"台灣",GLOBAL:"全球/跨區",EQUITY:"股票",BOND:"主權債",CREDIT:"信用債",
            COMMODITY:"商品",FX:"匯率",CRYPTO:"加密",REIT:"不動產",CASH:"現金等價",
            "1":"風險階1",  "2":"風險階2","3":"風險階3","4":"風險階4","5":"風險階5"};

var CRIT={win:120,metric:"fis",group:"region",agg:"basket",hot:30,smooth:5,minbars:60,sort:"last"};
var OFF={};   /* 被關掉的分組 */
function clearOff(){Object.keys(OFF).forEach(function(k){delete OFF[k];});}

function gkey(t){var m=TL.meta[t]||{};
  if(CRIT.group==="asset")return m.asset||"?";
  if(CRIT.group==="tier")return String(m.tier||"3");
  if(CRIT.group==="none")return t;
  return m.region||"?";}
function gcol(k){return GCOL[k]||"#6b6860";}
function glab(k){return CRIT.group==="none"?k:(GLAB[k]||k);}

function smooth(a,w){
  if(w<=1)return a.slice();
  var o=[],h=Math.floor(w/2),i,j,s,n;
  for(i=0;i<a.length;i++){s=0;n=0;
    for(j=Math.max(0,i-h);j<=Math.min(a.length-1,i+h);j++){if(a[j]!==null){s+=a[j];n++;}}
    o.push(n?s/n:null);}
  return o;}

/* 取出某檔在視窗內、依 metric 正規化後的序列 */
function seriesOf(t,i0){
  var d=TL.series[t]; if(!d)return null;
  var c=d.c.slice(i0), f=d.f.slice(i0), v=d.v.slice(i0), i, out=[];
  var valid=0; for(i=0;i<c.length;i++){if(c[i]!==null)valid++;}
  if(valid<Math.max(2,CRIT.minbars*0.2))return null;
  if(CRIT.metric==="fis"){out=f.slice();}
  else if(CRIT.metric==="vol"){out=v.slice();}
  else{ /* price / rs 都需要 rebase */
    var base=null; for(i=0;i<c.length;i++){if(c[i]!==null&&c[i]>0){base=c[i];break;}}
    if(!base)return null;
    for(i=0;i<c.length;i++)out.push(c[i]===null?null:c[i]/base*100);
    if(CRIT.metric==="rs"){
      var b=TL.series["ACWI"]; 
      if(!b)return null;
      var bc=b.c.slice(i0), bb=null;
      for(i=0;i<bc.length;i++){if(bc[i]!==null&&bc[i]>0){bb=bc[i];break;}}
      if(!bb)return null;
      for(i=0;i<out.length;i++){
        out[i]=(out[i]===null||bc[i]===null)?null:(out[i]-bc[i]/bb*100);}
    }
  }
  return smooth(out,CRIT.smooth);}

/* 依 CRITERIA 組出要畫的線：籃子（成交金額加權以檔數近似）或逐檔 */
function buildLines(){
  var i0=Math.max(0,TL.dates.length-CRIT.win), tickers=Object.keys(TL.series), out=[];
  if(CRIT.agg==="each"){
    tickers.forEach(function(t){
      var k=gkey(t); if(OFF[k])return;
      var y=seriesOf(t,i0); if(!y)return;
      out.push({id:t,label:t,group:k,color:gcol(k),y:y,n:1});});
  }else{
    var buckets={};
    tickers.forEach(function(t){
      var k=gkey(t); if(OFF[k])return;
      var y=seriesOf(t,i0); if(!y)return;
      (buckets[k]=buckets[k]||[]).push(y);});
    Object.keys(buckets).forEach(function(k){
      var arr=buckets[k],L=arr[0].length,y=[],i,j,s,n;
      for(i=0;i<L;i++){s=0;n=0;
        for(j=0;j<arr.length;j++){if(arr[j][i]!==null){s+=arr[j][i];n++;}}
        y.push(n?s/n:null);}
      out.push({id:k,label:glab(k),group:k,color:gcol(k),y:y,n:arr.length});});
  }
  var lastOf=function(a){for(var i=a.length-1;i>=0;i--)if(a[i]!==null)return a[i];return null;};
  var firstOf=function(a){for(var i=0;i<a.length;i++)if(a[i]!==null)return a[i];return null;};
  var meanOf=function(a){var s=0,n=0,i;for(i=0;i<a.length;i++)if(a[i]!==null){s+=a[i];n++;}return n?s/n:null;};
  out.forEach(function(L){L.last=lastOf(L.y);L.mean=meanOf(L.y);
    var f=firstOf(L.y);L.delta=(f===null||L.last===null)?null:L.last-f;});
  var key=CRIT.sort;
  out.sort(function(a,b){
    if(key==="name")return a.label<b.label?-1:1;
    var av=a[key==="last"?"last":key],bv=b[key==="last"?"last":key];
    if(av===null)return 1; if(bv===null)return -1; return bv-av;});
  return out;}

function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function fmt(v,d){return v===null||v===undefined?"—":(v>=0?"+":"")+v.toFixed(d===undefined?1:d);}

function drawTrend(lines){
  var el=document.getElementById("chTrend");
  if(!lines.length){el.innerHTML='<div class="empty-chart">目前 CRITERIA 下沒有足夠樣本的序列</div>';return;}
  var W=1320,H=300,ml=46,mr=118,mt=10,mb=22,pw=W-ml-mr,ph=H-mt-mb;
  var L=lines[0].y.length,i,j,lo=Infinity,hi=-Infinity;
  lines.forEach(function(s){s.y.forEach(function(v){if(v!==null){if(v<lo)lo=v;if(v>hi)hi=v;}});});
  if(lo===Infinity){el.innerHTML='<div class="empty-chart">無有效數值</div>';return;}
  if(hi-lo<1e-9){hi=lo+1;lo=lo-1;}
  var pad=(hi-lo)*0.08;lo-=pad;hi+=pad;
  var X=function(i){return ml+(L<2?0:i/(L-1)*pw);};
  var Y=function(v){return mt+ph-(v-lo)/(hi-lo)*ph;};
  var svg='<svg viewBox="0 0 '+W+' '+H+'" width="100%" preserveAspectRatio="xMidYMid meet">';
  for(j=0;j<=4;j++){var gv=lo+(hi-lo)*j/4,gy=Y(gv);
    svg+='<line class="ax" x1="'+ml+'" y1="'+gy.toFixed(1)+'" x2="'+(ml+pw)+'" y2="'+gy.toFixed(1)+'"/>';
    svg+='<text class="axt" x="'+(ml-5)+'" y="'+(gy+3).toFixed(1)+'" text-anchor="end">'+gv.toFixed(1)+'</text>';}
  var zero=(CRIT.metric==="fis"||CRIT.metric==="rs")?0:(CRIT.metric==="vol"?1:100);
  if(zero>lo&&zero<hi){svg+='<line x1="'+ml+'" y1="'+Y(zero).toFixed(1)+'" x2="'+(ml+pw)+'" y2="'+Y(zero).toFixed(1)+'" stroke="#1e1d1a" stroke-width="1" opacity=".55"/>';}
  if(CRIT.metric==="fis"){[CRIT.hot,-CRIT.hot].forEach(function(h){
    if(h>lo&&h<hi)svg+='<line class="hot" x1="'+ml+'" y1="'+Y(h).toFixed(1)+'" x2="'+(ml+pw)+'" y2="'+Y(h).toFixed(1)+'"/>';});}
  var step=Math.max(1,Math.floor(L/8)),i0=TL.dates.length-L;
  for(i=0;i<L;i+=step){var d=TL.dates[i0+i]||"";
    svg+='<text class="axt" x="'+X(i).toFixed(1)+'" y="'+(H-6)+'" text-anchor="middle">'+esc(d.slice(2))+'</text>';}
  lines.forEach(function(s){
    var p="",pen=false;
    for(i=0;i<L;i++){if(s.y[i]===null){pen=false;continue;}
      p+=(pen?"L":"M")+X(i).toFixed(1)+" "+Y(s.y[i]).toFixed(1)+" ";pen=true;}
    if(p)svg+='<path class="gl" d="'+p+'" stroke="'+s.color+'"/>';
    if(s.last!==null){
      svg+='<text class="rl" x="'+(ml+pw+6)+'" y="'+(Y(s.last)+3).toFixed(1)+'" fill="'+s.color+'">'
        +esc(s.label)+' '+fmt(s.last)+'</text>';}});
  el.innerHTML=svg+'</svg>';
  document.getElementById("tTrend").textContent=
    "視窗 "+CRIT.win+"D · "+lines.length+" 條 · 平滑 "+CRIT.smooth+"D";}

function drawHeat(lines){
  var el=document.getElementById("chHeat");
  var rows=lines.filter(function(s){return s.y.some(function(v){return v!==null;});});
  if(!rows.length){el.innerHTML='<div class="empty-chart">無資料</div>';return;}
  rows=rows.slice(0,40);
  var L=rows[0].y.length,maxc=140,stride=Math.max(1,Math.ceil(L/maxc)),cols=Math.ceil(L/stride);
  var cw=Math.max(4,Math.min(11,Math.floor(1140/cols))),rh=15,ml=132,mt=14;
  var W=ml+cols*cw+10,H=mt+rows.length*rh+20;
  var lo=Infinity,hi=-Infinity;
  rows.forEach(function(s){s.y.forEach(function(v){if(v!==null){if(v<lo)lo=v;if(v>hi)hi=v;}});});
  var mid=(CRIT.metric==="fis"||CRIT.metric==="rs")?0:(CRIT.metric==="vol"?1:100);
  var span=Math.max(Math.abs(hi-mid),Math.abs(mid-lo))||1;
  var svg='<svg viewBox="0 0 '+W+' '+H+'" width="100%" preserveAspectRatio="xMidYMid meet">';
  rows.forEach(function(s,r){
    var y=mt+r*rh;
    svg+='<text class="rl" x="'+(ml-6)+'" y="'+(y+11)+'" text-anchor="end" fill="'+s.color+'">'+esc(s.label)+'</text>';
    for(var k=0;k<cols;k++){
      var i=k*stride,acc=0,n=0,q;
      for(q=i;q<Math.min(L,i+stride);q++){if(s.y[q]!==null){acc+=s.y[q];n++;}}
      var x=ml+k*cw;
      if(!n){svg+='<rect x="'+x+'" y="'+y+'" width="'+(cw-1)+'" height="'+(rh-2)+'" fill="#e6e4de"/>';continue;}
      var v=acc/n,t=Math.min(1,Math.abs(v-mid)/span),a=(0.10+t*0.80).toFixed(3);
      var col=v>=mid?"192,88,78":"79,138,91";
      var hot=(CRIT.metric==="fis"&&Math.abs(v)>=CRIT.hot)?' stroke="#1e1d1a" stroke-width=".6"':"";
      svg+='<rect x="'+x+'" y="'+y+'" width="'+(cw-1)+'" height="'+(rh-2)+'" fill="rgba('+col+','+a+')"'+hot+'><title>'
        +esc(s.label)+' '+esc(TL.dates[TL.dates.length-L+i]||"")+' '+fmt(v)+'</title></rect>';}});
  var st=Math.max(1,Math.floor(cols/8));
  for(var k=0;k<cols;k+=st){var d=TL.dates[TL.dates.length-L+k*stride]||"";
    svg+='<text class="axt" x="'+(ml+k*cw)+'" y="'+(H-6)+'">'+esc(d.slice(2))+'</text>';}
  el.innerHTML=svg+'</svg>';}

function drawQuad(){
  var el=document.getElementById("chQuad");
  var i0=Math.max(0,TL.dates.length-CRIT.win),pts=[];
  Object.keys(TL.series).forEach(function(t){
    var k=gkey(t); if(OFF[k])return;
    var d=TL.series[t],c=d.c.slice(i0),f=d.f.slice(i0),v=d.v.slice(i0),i;
    var c0=null,c1=null;
    for(i=0;i<c.length;i++){if(c[i]!==null){if(c0===null)c0=c[i];c1=c[i];}}
    if(c0===null||c1===null||c0<=0)return;
    var fs=0,fn=0,vs=0,vn=0;
    for(i=0;i<f.length;i++){if(f[i]!==null){fs+=f[i];fn++;}if(v[i]!==null){vs+=v[i];vn++;}}
    if(fn<Math.max(1,CRIT.minbars*0.2))return;
    pts.push({t:t,g:k,x:(c1/c0-1)*100,y:fs/fn,r:vn?vs/vn:1,color:gcol(k)});});
  if(!pts.length){el.innerHTML='<div class="empty-chart">目前 CRITERIA 下無足夠樣本</div>';return;}
  var W=1320,H=340,ml=46,mr=16,mt=12,mb=26,pw=W-ml-mr,ph=H-mt-mb;
  var xs=pts.map(function(p){return p.x;}),ys=pts.map(function(p){return p.y;});
  var xlo=Math.min.apply(null,xs),xhi=Math.max.apply(null,xs);
  var ylo=Math.min.apply(null,ys),yhi=Math.max.apply(null,ys);
  var xp=(xhi-xlo)*0.12||1,yp=(yhi-ylo)*0.12||1;
  xlo-=xp;xhi+=xp;ylo-=yp;yhi+=yp;
  if(xlo>0)xlo=-xp; if(xhi<0)xhi=xp; if(ylo>0)ylo=-yp; if(yhi<0)yhi=yp;
  var X=function(v){return ml+(v-xlo)/(xhi-xlo)*pw;},
      Y=function(v){return mt+ph-(v-ylo)/(yhi-ylo)*ph;};
  var svg='<svg viewBox="0 0 '+W+' '+H+'" width="100%" preserveAspectRatio="xMidYMid meet">';
  svg+='<rect x="'+X(0)+'" y="'+mt+'" width="'+(ml+pw-X(0))+'" height="'+(Y(0)-mt)+'" fill="rgba(192,88,78,.05)"/>';
  svg+='<rect x="'+ml+'" y="'+Y(0)+'" width="'+(X(0)-ml)+'" height="'+(mt+ph-Y(0))+'" fill="rgba(79,138,91,.05)"/>';
  svg+='<line class="ax" x1="'+ml+'" y1="'+Y(0).toFixed(1)+'" x2="'+(ml+pw)+'" y2="'+Y(0).toFixed(1)+'"/>';
  svg+='<line class="ax" x1="'+X(0).toFixed(1)+'" y1="'+mt+'" x2="'+X(0).toFixed(1)+'" y2="'+(mt+ph)+'"/>';
  svg+='<text class="axt" x="'+(ml+pw-4)+'" y="'+(Y(0)+12)+'" text-anchor="end">價格動能 % →</text>';
  svg+='<text class="axt" x="'+(X(0)+5)+'" y="'+(mt+9)+'">↑ 資金流 FIS_pv</text>';
  svg+='<text class="axt" x="'+(ml+pw-4)+'" y="'+(mt+9)+'" text-anchor="end">量價齊揚</text>';
  svg+='<text class="axt" x="'+(ml+4)+'" y="'+(mt+ph-4)+'">價跌且失血</text>';
  pts.forEach(function(p){
    var r=Math.max(3.2,Math.min(15,3+ (p.r||1)*3.2));
    svg+='<circle cx="'+X(p.x).toFixed(1)+'" cy="'+Y(p.y).toFixed(1)+'" r="'+r.toFixed(1)
      +'" fill="'+p.color+'" fill-opacity=".42" stroke="'+p.color+'" stroke-width="1.1"><title>'
      +esc(p.t)+' 動能'+fmt(p.x)+'% FIS'+fmt(p.y)+' 量能'+(p.r||0).toFixed(2)+'x</title></circle>';
    svg+='<text class="rl" x="'+(X(p.x)+r+3).toFixed(1)+'" y="'+(Y(p.y)+3).toFixed(1)+'">'+esc(p.t)+'</text>';});
  el.innerHTML=svg+'</svg>';}

function drawChips(){
  var el=document.getElementById("cFilter");
  if(CRIT.group==="none"){el.innerHTML='<span class="dim" style="font-size:9px">不分組模式下無群組篩選</span>';return;}
  var ks={};Object.keys(TL.series).forEach(function(t){ks[gkey(t)]=1;});
  el.innerHTML=Object.keys(ks).sort().map(function(k){
    var on=!OFF[k];
    return '<span class="chip'+(on?" on":"")+'" data-k="'+esc(k)+'"'
      +(on?' style="background:'+gcol(k)+'"':'')+'>'+esc(glab(k))+'</span>';}).join("");
  Array.prototype.forEach.call(el.querySelectorAll(".chip"),function(c){
    c.addEventListener("click",function(){var k=c.dataset.k;OFF[k]=!OFF[k];draw();});});}

function draw(){
  var lines=buildLines();
  drawTrend(lines);drawHeat(lines);drawQuad();drawChips();}

function bindCrit(){
  var m={cWin:"win",cMetric:"metric",cGroup:"group",cAgg:"agg",cSort:"sort"};
  Object.keys(m).forEach(function(id){
    var e=document.getElementById(id); if(!e)return;
    e.addEventListener("change",function(){
      var v=e.value;CRIT[m[id]]=(id==="cWin")?parseInt(v,10):v;
      if(id==="cGroup")clearOff();draw();});});
  [["cHot","hot","cHotV"],["cSmooth","smooth","cSmoothV"],["cMin","minbars","cMinV"]]
    .forEach(function(a){
      var e=document.getElementById(a[0]); if(!e)return;
      e.addEventListener("input",function(){
        CRIT[a[1]]=parseInt(e.value,10);
        var lbl=document.getElementById(a[2]); if(lbl)lbl.textContent=e.value;
        draw();});});
  var r=document.getElementById("cReset");
  if(r)r.addEventListener("click",function(){
    /* 原地修改，不重新綁定：任何持有 CRIT/OFF 參照的呼叫端才不會指到舊物件 */
    var dflt={win:120,metric:"fis",group:"region",agg:"basket",hot:30,smooth:5,minbars:60,sort:"last"};
    Object.keys(dflt).forEach(function(k){CRIT[k]=dflt[k];});
    clearOff();
    var set=function(id,v){var e=document.getElementById(id);if(e)e.value=v;};
    set("cWin",120);set("cMetric","fis");set("cGroup","region");set("cAgg","basket");
    set("cHot",30);set("cSmooth",5);set("cMin",60);set("cSort","last");
    ["cHotV","cSmoothV","cMinV"].forEach(function(id,i){
      var e=document.getElementById(id);if(e)e.textContent=[30,5,60][i];});
    draw();});}

if(TL.dates.length){bindCrit();draw();}

})();
</script>
</body></html>
""")


# --------------------------------------------------------------------------- #
# 13.  EXPORTS
# --------------------------------------------------------------------------- #

def _jsonable(o):
    if isinstance(o, Val):
        return o.as_dict()
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    return o


def export_json(ds, path: Path):
    """完整 SSOT。時間軸另存一檔，避免主檔被逐日序列灌爆。"""
    slim = dict(ds)
    slim["probes"] = [{k: v for k, v in p.items() if k != "series"} for p in ds["probes"]]
    slim.pop("timeline", None)
    write_json(path, _jsonable(slim))
    if ds.get("timeline"):
        write_json(path.with_name("etf_flow_timeline.json"), ds["timeline"])


def export_csv(ds, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = (["ticker", "name", "region", "asset_class", "risk_tier", "bars", "source",
             "fis_pv", "fis_tier", "fis_evidence", "coverage", "intensity", "mfi14", "cmf20",
             "primary_flow_usd", "primary_flow_evidence", "rs_60d"]
            + ["ret_%dD" % n for n in HORIZONS] + ["ret_ytd", "last_date", "last_close"])
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for p in ds["probes"]:
            f = p["fis"]
            row = [p["ticker"], p["name"], p["region"], p["asset_class"], p["risk_tier"],
                   p["bars"], p["source"],
                   f["fis"].value, f["fis"].tier, f["fis"].evidence, f["coverage"],
                   f.get("intensity"), f.get("mfi14"), f.get("cmf20"),
                   p["primary_flow"].value, p["primary_flow"].evidence, p["rs"].value]
            row += [p["ret"]["horizons"][n].value for n in HORIZONS]
            row += [p["ret"]["ytd"].value, p["ret"]["last_date"], p["ret"]["last_close"].value]
            w.writerow(["" if v is None else v for v in row])


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# --------------------------------------------------------------------------- #
# 14.  SELF-TEST  (離線，內嵌 fixtures)
# --------------------------------------------------------------------------- #

def _synth_bars(n=300, base=100.0, drift=0.0004, vol=1_000_000, seed=7, spike=None):
    """決定性合成 bars。只用於測試引擎管線，永不進入產出。"""
    out = []
    d = _dt.date(2025, 1, 1)
    px = base
    s = seed
    for i in range(n):
        while d.weekday() >= 5:
            d += _dt.timedelta(days=1)
        s = (s * 1103515245 + 12345) % 2147483648
        w = (s / 2147483648.0) - 0.5
        px = px * (1 + drift + w * 0.01)
        v = vol * (0.7 + (s % 700) / 1000.0)
        if spike and i >= n - spike[0]:
            v *= spike[1]
        out.append({"date": d.isoformat(), "open": round(px * 0.998, 4),
                    "high": round(px * 1.006, 4), "low": round(px * 0.994, 4),
                    "close": round(px, 4), "volume": round(v)})
        d += _dt.timedelta(days=1)
    return out


def _cases():
    cases = []

    def case(fn):
        cases.append((fn.__name__[2:], fn))
        return fn

    # ---- numerics -------------------------------------------------------- #
    @case
    def t_stats():
        assert median([3, 1, 2]) == 2
        assert median([4, 1, 2, 3]) == 2.5
        assert median([]) is None
        assert mad([1, 1, 1]) == 0
        assert robust_z(5, [1, 1, 1, 1, 1, 1, 1, 1]) is None, "MAD=0 必須回 None 而非 0"
        assert robust_z(5, [1, 2, 3]) is None, "樣本 <8 不標準化"
        z = robust_z(20, list(range(1, 21)))
        assert z is not None and z > 0, z
        assert robust_z(1, list(range(1, 21))) < 0
        assert abs(robust_z(10.5, list(range(1, 21)))) < 1e-9, "中位數本身 z 應為 0"
        assert to_float("1,234.5") == 1234.5 and to_float("--") is None
        assert to_float(float("nan")) is None and to_float(float("inf")) is None

    # ---- parsers ---------------------------------------------------------- #
    @case
    def t_stooq_parser():
        csv_text = ("Date,Open,High,Low,Close,Volume\n"
                    "2026-06-17,100.0,101.0,99.0,100.5,1000000\n"
                    "2026-06-18,100.5,102.0,100.0,101.8,1200000\n"
                    "2026-06-16,99.0,100.0,98.5,99.5,900000\n"
                    "N/D,N/D,N/D,N/D,N/D,N/D\n")
        b = parse_stooq_csv(csv_text)
        assert len(b) == 3, b
        assert [x["date"] for x in b] == ["2026-06-16", "2026-06-17", "2026-06-18"]
        assert b[-1]["close"] == 101.8
        assert parse_stooq_csv("garbage") == []
        assert parse_stooq_csv("") == []

    @case
    def t_yahoo_parser():
        doc = {"chart": {"result": [{
            "timestamp": [1750118400, 1750204800],
            "indicators": {"quote": [{"open": [10.0, 10.5], "high": [11.0, 11.5],
                                      "low": [9.5, 10.0], "close": [10.5, None],
                                      "volume": [100, 200]}]}}]}}
        b = parse_yahoo_chart(doc)
        assert len(b) == 1, "close=None 的 bar 必須丟棄"
        assert parse_yahoo_chart({"chart": {"error": "x"}}) == []
        assert parse_yahoo_chart(None) == []

    @case
    def t_quote_summary_parser():
        doc = {"quoteSummary": {"result": [{
            "defaultKeyStatistics": {"sharesOutstanding": {"raw": 1234567},
                                     "navPrice": {"raw": 55.5}},
            "price": {}}]}}
        r = parse_quote_summary(doc)
        assert r["shares"] == 1234567 and r["nav"] == 55.5
        assert parse_quote_summary({"quoteSummary": {"result": [{}]}}) == {}
        assert parse_quote_summary({}) == {}

    # ---- FIS -------------------------------------------------------------- #
    @case
    def t_fis_needs_samples():
        r = compute_fis_pv(_synth_bars(30))
        assert not r["fis"].ok and "樣本不足" in r["fis"].note
        assert r["fis"].tier == T3

    @case
    def t_fis_bounded_and_signed():
        r = compute_fis_pv(_synth_bars(300))
        assert r["fis"].ok, r["fis"].note
        assert -100.0 <= r["fis"].value <= 100.0
        assert r["fis"].tier == T3 and r["fis"].evidence == EV_ESTIMATED
        assert r["coverage"] > 0.5, r["coverage"]

    @case
    def t_fis_reacts_to_buying_surge():
        calm = _synth_bars(300, seed=11)
        # 同一條價格路徑，最後 3 日爆量且收高 → FIS 應顯著上移
        surge = [dict(b) for b in calm]
        for b in surge[-3:]:
            b["volume"] = b["volume"] * 9
        for i in range(-3, 0):
            surge[i]["close"] = round(surge[i - 1]["close"] * 1.02, 4)
            surge[i]["high"] = round(surge[i]["close"] * 1.001, 4)
            surge[i]["low"] = round(surge[i - 1]["close"] * 0.999, 4)
        a = compute_fis_pv(calm)["fis"]
        b = compute_fis_pv(surge)["fis"]
        assert a.ok and b.ok
        assert b.value > a.value + 10, "爆量收高應推升 FIS：%s -> %s" % (a.value, b.value)

    @case
    def t_fis_symmetric_selling():
        calm = _synth_bars(300, seed=13)
        dump = [dict(b) for b in calm]
        for b in dump[-3:]:
            b["volume"] = b["volume"] * 9
        for i in range(-3, 0):
            dump[i]["close"] = round(dump[i - 1]["close"] * 0.98, 4)
            dump[i]["low"] = round(dump[i]["close"] * 0.999, 4)
            dump[i]["high"] = round(dump[i - 1]["close"] * 1.001, 4)
        assert compute_fis_pv(dump)["fis"].value < compute_fis_pv(calm)["fis"].value - 10

    @case
    def t_fis_rejects_missing_volume():
        bars = _synth_bars(300)
        for b in bars:
            b["volume"] = None
        r = compute_fis_pv(bars)
        assert not r["fis"].ok, "沒有量就沒有資金流，必須 PENDING"
        assert "組件" in r["fis"].note

    @case
    def t_fis_never_emits_amount():
        r = compute_fis_pv(_synth_bars(300))
        assert r["fis"].tier == T3
        # T3 的值域是 ±100 的強度，不是金額：抽樣確認不會出現大額數字
        assert abs(r["fis"].value) <= 100

    # ---- returns / RS ------------------------------------------------------ #
    @case
    def t_returns():
        bars = ([{"date": "2025-12-%02d" % d, "close": 100.0, "volume": 1} for d in range(20, 32)]
                + [{"date": "2026-01-%02d" % d, "close": 100.0 + d, "volume": 1} for d in range(1, 29)])
        r = compute_returns(bars, horizons=[1, 5, 240])
        assert r["last_close"].value == 128.0 and r["last_close"].tier == T1
        assert r["horizons"][240].value is None and r["horizons"][240].evidence == EV_PENDING
        assert r["ytd"].value == 28.0
        assert compute_returns([])["ytd"].value is None

    @case
    def t_relative_strength():
        a = _synth_bars(200, base=100, drift=0.002, seed=3)
        b = _synth_bars(200, base=100, drift=0.0002, seed=3)
        rs = relative_strength(a, b)
        assert rs.ok and rs.value > 0, rs
        assert not relative_strength(a[:10], b).ok
        # 基準無重疊日期 → PENDING 而非 0
        shifted = [dict(x, date="20%02d-01-01" % (30 + i)) for i, x in enumerate(b[:80])]
        assert not relative_strength(a, shifted).ok

    # ---- registries -------------------------------------------------------- #
    @case
    def t_universe_append_only():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "u.json"
            u = UniverseRegistry(p)
            rep = u.seed_and_merge("2026-08-16")
            assert rep["total"] == len(UNIVERSE_SEED)
            u.data["entries"]["SPY"]["region"] = "CUSTOM"      # 使用者手改
            u.save()
            u2 = UniverseRegistry(p)
            u2.seed_and_merge("2026-08-17")
            assert u2.data["entries"]["SPY"]["region"] == "CUSTOM", "不得覆寫使用者分類"
            for _ in range(3):
                u2.mark("QQQ", False, "2026-08-17", "boom")
            assert u2.data["entries"]["QQQ"]["status"] == "DORMANT"
            assert "QQQ" in u2.data["entries"], "只增不減"
            u2.mark("QQQ", True, "2026-08-18")
            assert u2.data["entries"]["QQQ"]["status"] == "ACTIVE"

    @case
    def t_shares_primary_flow():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            s = SharesRegistry(Path(td) / "s.json")
            assert not s.primary_flow("SPY").ok, "無快照 → PENDING，不得回 0"
            s.add("SPY", "2026-08-15", 1_000_000, 500.0)
            assert not s.primary_flow("SPY").ok, "一筆快照不成差分"
            s.add("SPY", "2026-08-16", 1_010_000, 505.0)
            f = s.primary_flow("SPY")
            assert f.ok and abs(f.value - 10_000 * 505.0) < 1.0, f
            assert f.tier == T1 and f.evidence == EV_DERIVED
            s.add("SPY", "2026-08-16", 1_010_000, 505.0)
            assert len(s.data["snapshots"]["SPY"]) == 2, "同日快照須去重"
            # 缺 NAV 的快照不得換算金額
            s2 = SharesRegistry(Path(td) / "s2.json")
            s2.add("X", "2026-08-15", 100, None)
            s2.add("X", "2026-08-16", 200, None)
            assert not s2.primary_flow("X").ok

    # ---- aggregation ------------------------------------------------------- #
    @case
    def t_aggregate_coverage_floor():
        def mk(t, region, fisv, dv=1e6, tier=3):
            return {"ticker": t, "region": region, "asset_class": "EQUITY",
                    "risk_tier": tier, "dollar_vol": dv,
                    "fis": {"fis": Val(fisv, T3, EV_ESTIMATED, "x") if fisv is not None
                            else Val(None, T3)},
                    "ret": {"horizons": {n: Val(1.0, T1, EV_OFFICIAL, "x") for n in HORIZONS}},
                    "rs": Val(2.0, T1, EV_DERIVED, "x"),
                    "primary_flow": Val(None, T1)}
        probes = [mk("A", "US", 60, dv=9e9), mk("B", "US", -10, dv=1e6),
                  mk("C", "EU", None), mk("D", "EU", None), mk("E", "EU", 50)]
        gs = {g["group"]: g for g in aggregate(probes, "region")}
        assert gs["US"]["fis"].ok
        # 成交金額加權：A 的權重壓倒性 → 籃子應貼近 +60 而非等權 +25
        assert gs["US"]["fis"].value > 55, gs["US"]["fis"]
        assert not gs["EU"]["fis"].ok, "覆蓋率 33% < 50% 必須 PENDING"
        assert "覆蓋率" in gs["EU"]["fis"].note
        assert not gs["US"]["primary_flow"].ok, "無成員有真流 → PENDING"

    @case
    def t_dual_verify():
        def mk(t, v):
            return {"ticker": t, "fis": {"fis": Val(v, T3, EV_ESTIMATED, "x") if v is not None
                                         else Val(None, T3)}}
        probes = [mk("HYG", 30), mk("JNK", -25), mk("MCHI", 20), mk("FXI", 22),
                  mk("IBIT", 50), mk("FBTC", None)]
        r = {d["pair"]: d for d in dual_verify(probes)}
        assert r["HYG ↔ JNK"]["css"] == "BAD", r["HYG ↔ JNK"]
        assert r["MCHI ↔ FXI"]["css"] == "OK"
        assert r["IBIT ↔ FBTC"]["css"] == "P"

    @case
    def t_roro():
        def mk(t, tier, v):
            return {"ticker": t, "risk_tier": tier,
                    "fis": {"fis": Val(v, T3, EV_ESTIMATED, "x")}}
        probes = ([mk("a%d" % i, 5, 60) for i in range(4)]
                  + [mk("b%d" % i, 1, -40) for i in range(4)])
        r = risk_appetite(probes)
        assert r["score"].ok and r["score"].value == 100.0, r
        assert "RISK-ON" in r["regime"]
        thin = risk_appetite([mk("a", 5, 60), mk("b", 1, -40)])
        assert not thin["score"].ok, "樣本不足必須 PENDING"

    # ---- render / export --------------------------------------------------- #
    @case
    def t_render():
        ds = _fixture_ds()
        h = render_html(ds, Log(quiet=True))
        assert "<!DOCTYPE html>" in h
        assert "${" not in h, "樣板殘留未替換佔位符"
        assert "\u2014" in h, "PENDING 必須渲染成破折號"
        tiers = re.findall(r'<span class="ev"[^>]*>([^<]*)</span>', h)
        assert tiers and set(tiers) <= {T1, T2, T3, T4}, set(tiers)
        assert T4 not in tiers, "T4 模擬值不得出現在產出"
        for t in ("p-grp", "p-oth", "p-probe", "p-verify", "p-log"):
            assert 'id="%s"' % t in h, t

    @case
    def t_render_all_pending():
        ds = _fixture_ds(all_pending=True)
        h = render_html(ds, Log(quiet=True))
        assert "${" not in h and "<!DOCTYPE html>" in h
        assert h.count("\u2014") > 5

    @case
    def t_export():
        import tempfile
        ds = _fixture_ds()
        with tempfile.TemporaryDirectory() as td:
            jp, cp = Path(td) / "a.json", Path(td) / "a.csv"
            export_json(ds, jp)
            export_csv(ds, cp)
            doc = json.loads(jp.read_text(encoding="utf-8"))
            assert doc["probes"][0]["fis"]["fis"]["tier"] == T3
            rows = list(csv.DictReader(io.open(cp, encoding="utf-8")))
            assert len(rows) == len(ds["probes"])
            pend = [r for r in rows if r["ticker"] == "TLT"][0]
            assert pend["fis_pv"] == "", "PENDING 必須匯出空白而非 0"
            assert pend["primary_flow_usd"] == ""

    @case
    def t_fmt():
        assert fmt_usd(Val(None, T1)) == "\u2014"
        assert fmt_usd(Val(2.5e9, T1, EV_DERIVED)) == "+$2.50B"
        assert fmt_usd(Val(-3.4e6, T1, EV_DERIVED)) == "\u2212$3.4M"
        assert fmt_sig(Val(-3.25, T3, EV_ESTIMATED)) == "-3.2"
        assert fmt_sig(Val(3.25, T3, EV_ESTIMATED)) == "+3.2"
        assert Val(None, T1, EV_OFFICIAL).evidence == EV_PENDING, "None 不得帶官方標籤"
        assert "\u2014" in fis_bar(Val(None, T3))

    @case
    def t_timeline_alignment():
        p1 = {"ticker": "AAA", "name": "a", "region": "US", "asset_class": "EQUITY",
              "risk_tier": 3,
              "series": {"dates": ["2026-01-02", "2026-01-05", "2026-01-06"],
                         "close": [10.0, 11.0, 12.0], "fis": [None, 5.0, 7.0],
                         "intensity": [1.0, 1.2, 0.9]}}
        p2 = {"ticker": "BBB", "name": "b", "region": "EU", "asset_class": "BOND",
              "risk_tier": 2,
              "series": {"dates": ["2026-01-05", "2026-01-07"],
                         "close": [20.0, 21.0], "fis": [-3.0, -4.0],
                         "intensity": [0.8, 1.1]}}
        p3 = {"ticker": "CCC", "name": "c", "region": "EM", "asset_class": "EQUITY",
              "risk_tier": 4, "series": None}
        tl = build_timeline([p1, p2, p3])
        assert tl["dates"] == ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"], tl["dates"]
        assert set(tl["series"]) == {"AAA", "BBB"}, "無序列者不得進入時間軸"
        a, b = tl["series"]["AAA"], tl["series"]["BBB"]
        assert len(a["c"]) == 4 and len(b["c"]) == 4, "所有序列須對齊到共用日期軸"
        assert a["c"] == [10.0, 11.0, 12.0, None], a["c"]
        assert b["c"] == [None, 20.0, None, 21.0], "缺漏日必須留 None，不得前向填值"
        assert b["f"] == [None, -3.0, None, -4.0]
        assert tl["meta"]["AAA"]["region"] == "US" and tl["meta"]["BBB"]["asset"] == "BOND"
        assert "CCC" not in tl["meta"]
        assert build_timeline([])["dates"] == []

    @case
    def t_timeline_tail():
        p1 = {"ticker": "AAA", "name": "a", "region": "US", "asset_class": "EQUITY",
              "risk_tier": 3,
              "series": {"dates": ["2026-01-%02d" % d for d in range(1, 11)],
                         "close": [float(d) for d in range(1, 11)],
                         "fis": [float(d) for d in range(1, 11)],
                         "intensity": [1.0] * 10}}
        tl = build_timeline([p1], tail=4)
        assert len(tl["dates"]) == 4 and tl["dates"][0] == "2026-01-07", tl["dates"]
        assert tl["series"]["AAA"]["c"] == [7.0, 8.0, 9.0, 10.0]

    @case
    def t_render_embeds_timeline():
        ds = _fixture_ds()
        bars = _synth_bars(150, seed=41)
        s = compute_flow_series(bars)
        ds["probes"][0]["series"] = s
        ds["timeline"] = build_timeline(ds["probes"], tail=60)
        h = render_html(ds, Log(quiet=True))
        assert "var TL = " in h, "時間軸資料塊必須嵌入頁面"
        blob = h.split("var TL = ", 1)[1].split(";\n", 1)[0]
        doc = json.loads(blob)
        assert len(doc["dates"]) == 60, len(doc["dates"])
        assert "SPY" in doc["series"]
        assert 'id="p-tl"' in h and 'id="cWin"' in h and 'id="cHot"' in h
        assert "${" not in h

    @case
    def t_series_matches_pointwise():
        bars = _synth_bars(220, seed=53)
        s = compute_flow_series(bars)
        pt = compute_fis_pv(bars)
        assert pt["fis"].value == s["fis"][-1], (pt["fis"].value, s["fis"][-1])
        assert pt["intensity"] == s["intensity"][-1]
        assert pt["mfi14"] == s["mfi14"][-1]
        # 前段不足 MIN_BARS 的點必須是 None，不得補值
        assert all(x is None for x in s["fis"][:MIN_BARS - 1]), "暖機期不得產生數值"
        assert s["fis"][-1] is not None

    @case
    def t_rolling_window_mad():
        import random as _r
        _r.seed(4)
        for _ in range(40):
            n = _r.choice([8, 13, 60])
            xs = [round(_r.gauss(0, _r.choice([1, 1e5])), 6) for _ in range(n)]
            w = _RobustWindow(n)
            for x in xs:
                w.add(x)
            m = w.median()
            assert abs(m - median(xs)) < 1e-9
            assert abs(w.mad() - mad(xs, m)) < 1e-6 * max(1.0, abs(mad(xs, m)))
        w = _RobustWindow(3)
        for x in [1.0, 2.0, 3.0, 4.0]:
            w.add(x)
        assert w.s == [2.0, 3.0, 4.0], "超出視窗須逐出最舊值"
        w.add(None)
        assert len(w.s) == 3, "None 不入視窗"

    return cases


def _fixture_ds(all_pending=False):
    def probe(t, name, reg, asset, tier, fisv, prim, bars=300):
        return {"ticker": t, "name": name, "region": reg, "asset_class": asset,
                "risk_tier": tier, "status": "ACTIVE", "bars": bars, "source": "stooq",
                "dollar_vol": 1e9,
                "fis": {"fis": (Val(fisv, T3, EV_ESTIMATED, "fx") if fisv is not None
                                else Val(None, T3, note="樣本不足")),
                        "components": {}, "coverage": 0.8,
                        "intensity": 1.42 if fisv is not None else None,
                        "mfi14": 61.0 if fisv is not None else None, "cmf20": 0.04},
                "ret": {"horizons": {n: (Val(round(n * 0.05, 2), T1, EV_OFFICIAL, "fx")
                                         if bars > n else Val(None, T1))
                                     for n in HORIZONS},
                        "ytd": Val(8.4, T1, EV_OFFICIAL, "fx"),
                        "last_close": Val(123.45, T1, EV_OFFICIAL, "fx"),
                        "last_date": "2026-08-14", "bars": bars},
                "rs": Val(2.4, T1, EV_DERIVED, "fx") if fisv is not None else Val(None, T1),
                "primary_flow": (Val(prim, T1, EV_DERIVED, "fx") if prim is not None
                                 else Val(None, T1, note="快照不足"))}

    probes = [
        probe("SPY", "美股核心", "US", "EQUITY", 3, None if all_pending else 42.0,
              None if all_pending else 2.4e9),
        probe("QQQ", "美股科技", "US", "EQUITY", 4, None if all_pending else 61.0, None),
        probe("TLT", "美公債 20Y+", "US", "BOND", 2, None, None, bars=40),
        probe("GLD", "黃金", "GLOBAL", "COMMODITY", 2, None if all_pending else -18.0, None),
    ]
    reg = aggregate(probes, "region")
    ast = aggregate(probes, "asset_class")
    return {
        "meta": {"engine": __engine__, "version": __version__,
                 "generated_at": "2026-08-16T12:00:00", "run_date": "2026-08-16",
                 "data_date": "2026-08-14", "n_probes": len(probes),
                 "n_fis": sum(1 for p in probes if p["fis"]["fis"].ok),
                 "n_primary": sum(1 for p in probes if p["primary_flow"].ok),
                 "benchmark": BENCHMARK, "group_by": "region",
                 "http": {"net": 44, "cache": 10, "fail": 1},
                 "failures": [{"ticker": "USO", "error": "timeout"}]},
        "probes": probes, "by_region": reg, "by_asset": ast,
        "roro": risk_appetite(probes),
        "dual_verify": dual_verify(probes),
        "dormant": ["EWZ"],
    }


def run_selftest() -> int:
    LOG.banner("VIA GlobalETFFlow · SELF-TEST", "離線 · fixtures · 無網路")
    cases = _cases()
    ok, failed = 0, []
    for name, fn in cases:
        try:
            fn()
            ok += 1
            sys.stdout.write("  \u2713 PASS  %s\n" % name)
        except Exception:                                  # noqa: BLE001
            failed.append((name, traceback.format_exc()))
            sys.stdout.write("  \u2717 FAIL  %s\n" % name)
    sys.stdout.write("\n  %d/%d PASS\n" % (ok, len(cases)))
    for n, tb in failed:
        sys.stdout.write("\n--- %s ---\n%s\n" % (n, tb))
    sys.stdout.flush()
    return 0 if not failed else 1


# --------------------------------------------------------------------------- #
# 15.  MOCK INTEGRATION TEST  (本機伺服器，跑真管線)
# --------------------------------------------------------------------------- #

def run_mocktest(keep=False, quiet_tail=False) -> int:
    import http.server
    import socketserver
    import tempfile

    results = []

    def chk(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        sys.stdout.write("    %s %s%s\n" % ("\u2713" if cond else "\u2717", name,
                                            "" if cond else "   <-- " + detail))
        sys.stdout.flush()

    state = {"shares_mode": "on", "dead": set(), "shares_day": 0, "hits": 0}

    def bars_for(t):
        seed = sum(ord(c) for c in t)
        drift = 0.0012 if t in ("QQQ", "XLK", "IBIT") else (-0.0006 if t in ("TLT", "UUP") else 0.0003)
        return _synth_bars(320, base=50 + (seed % 400), drift=drift, seed=seed)

    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def _send(self, body, ctype="application/json", code=200):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):                                   # noqa: N802
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            state["hits"] += 1

            if u.path.startswith("/q/d/l/"):
                sym = (q.get("s") or [""])[0]
                t = sym.split(".")[0].upper()
                if t in state["dead"]:
                    return self._send(b"", ctype="text/csv")
                rows = ["Date,Open,High,Low,Close,Volume"]
                for b in bars_for(t):
                    rows.append("%s,%s,%s,%s,%s,%d" % (b["date"], b["open"], b["high"],
                                                       b["low"], b["close"], b["volume"]))
                return self._send("\n".join(rows).encode(), ctype="text/csv")

            if u.path.startswith("/v8/finance/chart/"):
                t = u.path.rsplit("/", 1)[-1].upper()
                if t in state["dead"]:
                    return self._send(json.dumps({"chart": {"result": None,
                                                            "error": {"code": "Not Found"}}}).encode(),
                                      code=404)
                bs = bars_for(t)
                ts = [int(_dt.datetime.fromisoformat(b["date"] + "T00:00:00+00:00").timestamp())
                      for b in bs]
                return self._send(json.dumps({"chart": {"result": [{
                    "timestamp": ts,
                    "indicators": {"quote": [{
                        "open": [b["open"] for b in bs], "high": [b["high"] for b in bs],
                        "low": [b["low"] for b in bs], "close": [b["close"] for b in bs],
                        "volume": [b["volume"] for b in bs]}]}}]}}).encode())

            if u.path.startswith("/v10/finance/quoteSummary/"):
                if state["shares_mode"] == "off":
                    return self._send(json.dumps({"quoteSummary": {"result": None}}).encode(),
                                      code=404)
                t = u.path.rsplit("/", 1)[-1].upper()
                seed = sum(ord(c) for c in t)
                sh = 100_000_000 + seed * 1000 + state["shares_day"] * 500_000
                return self._send(json.dumps({"quoteSummary": {"result": [{
                    "defaultKeyStatistics": {"sharesOutstanding": {"raw": sh},
                                             "navPrice": {"raw": 50.0 + (seed % 400)}},
                    "price": {}}]}}).encode())

            return self._send(b'{"error":"nf"}', code=404)

        def log_message(self, *a):
            return

    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % port

    tmp = Path(tempfile.mkdtemp(prefix="via_etfflow_it_"))
    LOG.banner("VIA GlobalETFFlow · INTEGRATION TEST", "mock stooq/yahoo @ %s" % base)

    def run(out, extra=None):
        argv = ["--out", str(out), "--quiet", "--workers", "8",
                "--base-stooq", base, "--base-yahoo", base] + (extra or [])
        return main(argv)

    def load(out):
        doc = json.loads((out / "etf_flow_matrix.json").read_text(encoding="utf-8"))
        html = sorted(out.glob("VIA_GlobalETFFlow_2*.html"))[-1].read_text(encoding="utf-8")
        rows = list(csv.DictReader(io.open(out / "etf_flow_matrix.csv", encoding="utf-8")))
        uni = json.loads((out / "etf_universe_registry.json").read_text(encoding="utf-8"))
        sh = json.loads((out / "etf_shares_registry.json").read_text(encoding="utf-8"))
        return doc, html, rows, uni, sh

    try:
        # ---- 1 冷啟動 ----------------------------------------------------- #
        sys.stdout.write("\n[1] 冷啟動：宇宙登錄 / 日線 / FIS / 聚合\n")
        o1 = tmp / "s1"
        chk("exit 0", run(o1) == 0)
        doc, html, rows, uni, sh = load(o1)
        chk("探針數 == 種子清單", doc["meta"]["n_probes"] == len(UNIVERSE_SEED),
            str(doc["meta"]["n_probes"]))
        chk("FIS 全數成立", doc["meta"]["n_fis"] == len(UNIVERSE_SEED),
            "%d/%d" % (doc["meta"]["n_fis"], len(UNIVERSE_SEED)))
        chk("FIS 落在 ±100", all(-100 <= p["fis"]["fis"]["value"] <= 100
                                  for p in doc["probes"] if p["fis"]["fis"]["value"] is not None))
        chk("首跑 T1 真流全 PENDING（不得用估算頂替）",
            doc["meta"]["n_primary"] == 0, str(doc["meta"]["n_primary"]))
        chk("股數快照已寫入", len(sh["snapshots"]) == len(UNIVERSE_SEED), str(len(sh["snapshots"])))
        chk("區域聚合有結果", len(doc["by_region"]) >= 6, str(len(doc["by_region"])))
        chk("資產聚合有結果", len(doc["by_asset"]) >= 6, str(len(doc["by_asset"])))
        chk("RORO 成立", doc["roro"]["score"]["value"] is not None, str(doc["roro"]))
        chk("HTML 無殘留佔位符", "${" not in html)
        chk("HTML 含所有代碼", all(t in html for t, *_ in UNIVERSE_SEED[:10]))
        chk("CSV 行數相符", len(rows) == len(UNIVERSE_SEED), str(len(rows)))
        chk("CSV 中 T1 真流為空白非 0",
            all(r["primary_flow_usd"] == "" for r in rows))
        chk("universe registry 建立", len(uni["entries"]) == len(UNIVERSE_SEED))

        # ---- 2 第二日：T1 真流長出來 -------------------------------------- #
        sys.stdout.write("\n[2] 第二日：ΔShares×NAV 真流成立\n")
        state["shares_day"] = 1
        for p in sh["snapshots"].values():
            for pt in p:
                pt["date"] = "2020-01-01"          # 讓今日快照成為第二筆
        write_json(o1 / "etf_shares_registry.json", sh)
        chk("exit 0", run(o1, ["--no-cache"]) == 0)
        doc2, html2, rows2, _u, sh2 = load(o1)
        chk("T1 真流成立", doc2["meta"]["n_primary"] > 0, str(doc2["meta"]["n_primary"]))
        spy = [p for p in doc2["probes"] if p["ticker"] == "SPY"][0]
        chk("SPY 真流帶 T1 標籤", spy["primary_flow"]["tier"] == T1
            and spy["primary_flow"]["evidence"] == EV_DERIVED, str(spy["primary_flow"]))
        chk("真流為正（股數增加＝申購）", (spy["primary_flow"]["value"] or 0) > 0,
            str(spy["primary_flow"]["value"]))
        chk("HTML 顯示金額單位", "$" in html2 and "B" in html2)
        chk("籃子真流聚合", any(g["primary_flow"]["value"] is not None
                                for g in doc2["by_region"]))

        # ---- 3 來源劣化 ---------------------------------------------------- #
        sys.stdout.write("\n[3] 來源劣化：股數端全滅 → 只剩 T3，不得偽造 T1\n")
        state["shares_mode"] = "off"
        o3 = tmp / "s3"
        chk("exit 0", run(o3) == 0)
        doc3, html3, _r, _u, sh3 = load(o3)
        chk("T1 全 PENDING", doc3["meta"]["n_primary"] == 0)
        chk("T3 仍然成立", doc3["meta"]["n_fis"] > 30, str(doc3["meta"]["n_fis"]))
        chk("股數 registry 保持空", len(sh3.get("snapshots", {})) == 0)
        chk("HTML 仍完整", "${" not in html3 and "<!DOCTYPE html>" in html3)

        # ---- 4 個別標的死亡 → DORMANT ------------------------------------- #
        sys.stdout.write("\n[4] 標的抓取失敗 3 次 → DORMANT（只增不減）\n")
        state["shares_mode"] = "on"
        state["dead"] = {"USO", "COPX"}
        o4 = tmp / "s4"
        for i in range(3):
            run(o4, ["--no-cache"])
        doc4, html4, _r, uni4, _s = load(o4)
        chk("死亡標的不進 FIS 統計",
            all(p["fis"]["fis"]["value"] is None
                for p in doc4["probes"] if p["ticker"] in ("USO", "COPX")))
        chk("USO 轉 DORMANT", uni4["entries"]["USO"]["status"] == "DORMANT",
            uni4["entries"]["USO"].get("status"))
        chk("registry 未刪除", "USO" in uni4["entries"] and "COPX" in uni4["entries"])
        chk("DORMANT 事件留痕",
            any(h["event"] == "WENT_DORMANT" for h in uni4["entries"]["USO"]["history"]))
        chk("失敗清單出現在 HTML", "USO" in html4)
        chk("其他標的不受影響", doc4["meta"]["n_fis"] >= len(UNIVERSE_SEED) - 4,
            str(doc4["meta"]["n_fis"]))

        # ---- 5 離線 -------------------------------------------------------- #
        sys.stdout.write("\n[5] 離線：關站後靠快取重跑\n")
        state["dead"] = set()
        o5 = tmp / "s5"
        chk("暖機 exit 0", run(o5) == 0)
        httpd.shutdown()
        chk("離線 exit 0", run(o5, ["--offline"]) == 0)
        doc5, html5, _r, _u, _s = load(o5)
        chk("離線仍有完整探針", doc5["meta"]["n_probes"] == len(UNIVERSE_SEED))
        chk("離線 FIS 仍成立", doc5["meta"]["n_fis"] > 30, str(doc5["meta"]["n_fis"]))
        chk("快取確實被使用", doc5["meta"]["http"]["cache"] > 0, str(doc5["meta"]["http"]))
        chk("離線 HTML 完整", "${" not in html5 and "<!DOCTYPE html>" in html5)
        chk("mock 有被打到", state["hits"] > 0, str(state["hits"]))

    except Exception:                                      # noqa: BLE001
        traceback.print_exc()
        results.append(("harness crashed", False, "exception"))
    finally:
        try:
            httpd.shutdown()
        except Exception:                                  # noqa: BLE001
            pass
        httpd.server_close()

    ok = sum(1 for _n, c, _d in results if c)
    sys.stdout.write("\n" + "=" * 74 + "\n  %d/%d CHECKS PASS\n" % (ok, len(results)))
    for n, c, d in results:
        if not c:
            sys.stdout.write("   FAIL  %s   %s\n" % (n, d))
    sys.stdout.write("=" * 74 + "\n")
    try:
        h = sorted((tmp / "s1").glob("VIA_GlobalETFFlow_2*.html"))
        _LAST_MOCK_HTML["path"] = str(h[-1]) if h else None
        _LAST_MOCK_HTML["workspace"] = str(tmp)
    except OSError:
        pass
    if keep:
        if not quiet_tail:
            sys.stdout.write("  workspace: %s\n" % tmp)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok == len(results) else 1


# --------------------------------------------------------------------------- #
# 15b. USER-TEST  ── 用 node 真的跑一次頁面 JS，把每個 CRITERIA 都操作一遍
# --------------------------------------------------------------------------- #

UI_HARNESS_B64 = (
    "Ly8gVVNFUi1URVNUOiDlnKggbm9kZSDku6XmnIDlsI8gRE9NIHNoaW0g5Z+36KGMIEhUTUwg5YWn55qE5ZyW6KGoIEpT77yM"
    "Ci8vIOmAkOS4gOaTjeS9nOavj+WAiyBDUklURVJJQSDmjqfliLbpoIXvvIzpqZforYnnnJ/nmoTmnIPph43nrpfkuJTkuI3k"
    "uJ/kvovlpJbjgIIKY29uc3QgZnMgPSByZXF1aXJlKCdmcycpOwpjb25zdCBwYXRoID0gcHJvY2Vzcy5hcmd2WzJdOwpsZXQg"
    "aHRtbCA9IGZzLnJlYWRGaWxlU3luYyhwYXRoLCAndXRmOCcpOwoKbGV0IFBBU1MgPSAwLCBGQUlMID0gW107CmZ1bmN0aW9u"
    "IGNoayhuYW1lLCBjb25kLCBkZXRhaWwpIHsKICBpZiAoY29uZCkgeyBQQVNTKys7IGNvbnNvbGUubG9nKCcgICAgXHUyNzEz"
    "ICcgKyBuYW1lKTsgfQogIGVsc2UgeyBGQUlMLnB1c2goW25hbWUsIGRldGFpbCB8fCAnJ10pOyBjb25zb2xlLmxvZygnICAg"
    "IFx1MjcxNyAnICsgbmFtZSArICcgICA8LS0gJyArIChkZXRhaWwgfHwgJycpKTsgfQp9CgovLyAtLS0tLS0tLS0tIG1pbmlt"
    "YWwgRE9NIC0tLS0tLS0tLS0KY2xhc3MgRWwgewogIGNvbnN0cnVjdG9yKHRhZywgaWQpIHsKICAgIHRoaXMudGFnTmFtZSA9"
    "IHRhZzsgdGhpcy5pZCA9IGlkIHx8ICcnOyB0aGlzLnZhbHVlID0gJyc7CiAgICB0aGlzLl9odG1sID0gJyc7IHRoaXMuX3Rl"
    "eHQgPSAnJzsgdGhpcy5kYXRhc2V0ID0ge307CiAgICB0aGlzLmNsYXNzTGlzdCA9IG5ldyBTZXQoKTsgdGhpcy5oYW5kbGVy"
    "cyA9IHt9OyB0aGlzLmNoaWxkcmVuID0gW107CiAgICB0aGlzLnN0eWxlID0ge307CiAgfQogIHNldCBpbm5lckhUTUwodikg"
    "eyB0aGlzLl9odG1sID0gU3RyaW5nKHYpOyB0aGlzLmNoaWxkcmVuID0gcGFyc2VDaGlsZHJlbih0aGlzLl9odG1sKTsgfQog"
    "IGdldCBpbm5lckhUTUwoKSB7IHJldHVybiB0aGlzLl9odG1sOyB9CiAgc2V0IHRleHRDb250ZW50KHYpIHsgdGhpcy5fdGV4"
    "dCA9IFN0cmluZyh2KTsgfQogIGdldCB0ZXh0Q29udGVudCgpIHsgcmV0dXJuIHRoaXMuX3RleHQ7IH0KICBhZGRFdmVudExp"
    "c3RlbmVyKGV2LCBmbikgeyAodGhpcy5oYW5kbGVyc1tldl0gPSB0aGlzLmhhbmRsZXJzW2V2XSB8fCBbXSkucHVzaChmbik7"
    "IH0KICBmaXJlKGV2KSB7ICh0aGlzLmhhbmRsZXJzW2V2XSB8fCBbXSkuZm9yRWFjaChmID0+IGYoeyB0YXJnZXQ6IHRoaXMg"
    "fSkpOyB9CiAgcXVlcnlTZWxlY3RvckFsbChzZWwpIHsgcmV0dXJuIHRoaXMuY2hpbGRyZW4uZmlsdGVyKGMgPT4gYy5fc2Vs"
    "ID09PSBzZWwpOyB9Cn0KLy8gY2hpcHMgaW5zaWRlICNjRmlsdGVyIGNvbWUgYmFjayBhcyBpbm5lckhUTUw7IHBhcnNlIHRo"
    "ZW0gc28gY2xpY2sgaGFuZGxlcnMgY2FuIGJpbmQKZnVuY3Rpb24gcGFyc2VDaGlsZHJlbihoKSB7CiAgY29uc3Qgb3V0ID0g"
    "W107CiAgY29uc3QgcmUgPSAvPHNwYW4gY2xhc3M9ImNoaXBbXiJdKiIgZGF0YS1rPSIoW14iXSopIi9nOwogIGxldCBtOwog"
    "IHdoaWxlICgobSA9IHJlLmV4ZWMoaCkpKSB7CiAgICBjb25zdCBlID0gbmV3IEVsKCdzcGFuJyk7IGUuX3NlbCA9ICcuY2hp"
    "cCc7IGUuZGF0YXNldC5rID0gbVsxXTsKICAgIGUuY2xhc3NMaXN0LmFkZCgnY2hpcCcpOyBvdXQucHVzaChlKTsKICB9CiAg"
    "cmV0dXJuIG91dDsKfQoKY29uc3QgUkVHID0ge307CmNvbnN0IGlkcyA9IFsnY2hUcmVuZCcsICdjaEhlYXQnLCAnY2hRdWFk"
    "JywgJ2NGaWx0ZXInLCAndFRyZW5kJywKICAnY1dpbicsICdjTWV0cmljJywgJ2NHcm91cCcsICdjQWdnJywgJ2NIb3QnLCAn"
    "Y1Ntb290aCcsICdjTWluJywgJ2NTb3J0JywKICAnY0hvdFYnLCAnY1Ntb290aFYnLCAnY01pblYnLCAnY1Jlc2V0J107Cmlk"
    "cy5mb3JFYWNoKGkgPT4geyBSRUdbaV0gPSBuZXcgRWwoJ2RpdicsIGkpOyB9KTsKUkVHLmNXaW4udmFsdWUgPSAnMTIwJzsg"
    "UkVHLmNNZXRyaWMudmFsdWUgPSAnZmlzJzsgUkVHLmNHcm91cC52YWx1ZSA9ICdyZWdpb24nOwpSRUcuY0FnZy52YWx1ZSA9"
    "ICdiYXNrZXQnOyBSRUcuY0hvdC52YWx1ZSA9ICczMCc7IFJFRy5jU21vb3RoLnZhbHVlID0gJzUnOwpSRUcuY01pbi52YWx1"
    "ZSA9ICc2MCc7IFJFRy5jU29ydC52YWx1ZSA9ICdsYXN0JzsKCmdsb2JhbC5kb2N1bWVudCA9IHsKICBnZXRFbGVtZW50QnlJ"
    "ZDogaWQgPT4gUkVHW2lkXSB8fCBudWxsLAogIHF1ZXJ5U2VsZWN0b3JBbGw6ICgpID0+IFtdLAogIGFkZEV2ZW50TGlzdGVu"
    "ZXI6ICgpID0+IHt9LAp9OwoKLy8gLS0tLS0tLS0tLSBleHRyYWN0IGFuZCBydW4gdGhlIHBhZ2Ugc2NyaXB0IC0tLS0tLS0t"
    "LS0KY29uc3Qgc2NyaXB0cyA9IFsuLi5odG1sLm1hdGNoQWxsKC88c2NyaXB0PihbXHNcU10qPyk8XC9zY3JpcHQ+L2cpXS5t"
    "YXAobSA9PiBtWzFdKTsKY2hrKCfpoIHpnaLlkKsgaW5saW5lIHNjcmlwdCcsIHNjcmlwdHMubGVuZ3RoID49IDEsIFN0cmlu"
    "ZyhzY3JpcHRzLmxlbmd0aCkpOwpsZXQgY29kZSA9IHNjcmlwdHNbc2NyaXB0cy5sZW5ndGggLSAxXTsKLy8gc3RyaXAgdGhl"
    "IHRhYi1iaW5kaW5nIHByZWFtYmxlIChuZWVkcyBjbGFzc0xpc3Qgb24gcmVhbCBub2RlcyB3ZSBkb24ndCBzaGltKQpjb25z"
    "dCBjdXQgPSBjb2RlLmluZGV4T2YoJy8qID09PT09PT09PT09PSDmmYLplpPou7jmr5TovIPlvJXmk44nKTsKY2hrKCfmib7l"
    "vpfliLDmmYLplpPou7jlvJXmk47ljYDloYonLCBjdXQgPiAwLCBTdHJpbmcoY3V0KSk7CmNvZGUgPSBjb2RlLnNsaWNlKGN1"
    "dCk7Ci8vIOaIkeWAkeaYr+W+niBJSUZFIOS4reauteWIh+WHuuS+hueahO+8jOWwvuerr+eahCBgfSkoKTtgIOacg+iuiuaI"
    "kOmdnuazlSByZXR1cm4KY29uc3QgdGFpbCA9IGNvZGUubGFzdEluZGV4T2YoJ30pKCk7Jyk7CmlmICh0YWlsID4gMCkgY29k"
    "ZSA9IGNvZGUuc2xpY2UoMCwgdGFpbCk7CgpsZXQgYXBpID0gbnVsbDsKdHJ5IHsKICBhcGkgPSBuZXcgRnVuY3Rpb24oY29k"
    "ZSArICdcbnJldHVybiB7Q1JJVDpDUklULE9GRjpPRkYsZHJhdzpkcmF3LGJpbmRDcml0OmJpbmRDcml0LGJ1aWxkTGluZXM6"
    "YnVpbGRMaW5lcyxUTDpUTH07JykoKTsKICBjaGsoJ+W8leaTjui8ieWFpeeEoeS+i+WklicsIHRydWUpOwp9IGNhdGNoIChl"
    "KSB7CiAgY2hrKCflvJXmk47ovInlhaXnhKHkvovlpJYnLCBmYWxzZSwgZS5tZXNzYWdlKTsKICBmaW5pc2goKTsKfQoKY2hr"
    "KCdUTCDos4fmlpnlt7LltYzlhaUnLCBhcGkuVEwuZGF0ZXMubGVuZ3RoID4gMTAwICYmIE9iamVjdC5rZXlzKGFwaS5UTC5z"
    "ZXJpZXMpLmxlbmd0aCA+IDIwLAogIGFwaS5UTC5kYXRlcy5sZW5ndGggKyAnZCB4ICcgKyBPYmplY3Qua2V5cyhhcGkuVEwu"
    "c2VyaWVzKS5sZW5ndGgpOwoKLy8gaW5pdGlhbCByZW5kZXIKdHJ5IHsgYXBpLmJpbmRDcml0KCk7IGFwaS5kcmF3KCk7IGNo"
    "aygn5Yid5aeL5riy5p+T54Sh5L6L5aSWJywgdHJ1ZSk7IH0KY2F0Y2ggKGUpIHsgY2hrKCfliJ3lp4vmuLLmn5PnhKHkvovl"
    "pJYnLCBmYWxzZSwgZS5tZXNzYWdlKTsgfQoKZnVuY3Rpb24gc3ZnT2YoaWQpIHsgcmV0dXJuIFJFR1tpZF0uaW5uZXJIVE1M"
    "OyB9CmZ1bmN0aW9uIGlzU3ZnKGlkKSB7IHJldHVybiAvXjxzdmcgLy50ZXN0KHN2Z09mKGlkKSk7IH0KCmNoaygn6Lao5Yui"
    "5ZyW55Si5Ye6IFNWRycsIGlzU3ZnKCdjaFRyZW5kJyksIHN2Z09mKCdjaFRyZW5kJykuc2xpY2UoMCwgNjApKTsKY2hrKCfn"
    "hrHlnJbnlKLlh7ogU1ZHJywgaXNTdmcoJ2NoSGVhdCcpLCBzdmdPZignY2hIZWF0Jykuc2xpY2UoMCwgNjApKTsKY2hrKCfo"
    "saHpmZDlnJbnlKLlh7ogU1ZHJywgaXNTdmcoJ2NoUXVhZCcpLCBzdmdPZignY2hRdWFkJykuc2xpY2UoMCwgNjApKTsKY2hr"
    "KCfotqjli6LlnJbmnInmipjnt5onLCAoc3ZnT2YoJ2NoVHJlbmQnKS5tYXRjaCgvPHBhdGggL2cpIHx8IFtdKS5sZW5ndGgg"
    "Pj0gMywKICBTdHJpbmcoKHN2Z09mKCdjaFRyZW5kJykubWF0Y2goLzxwYXRoIC9nKSB8fCBbXSkubGVuZ3RoKSk7CmNoaygn"
    "54ax5ZyW5pyJ6Imy5qC8JywgKHN2Z09mKCdjaEhlYXQnKS5tYXRjaCgvPHJlY3QgL2cpIHx8IFtdKS5sZW5ndGggPiAyMDAs"
    "CiAgU3RyaW5nKChzdmdPZignY2hIZWF0JykubWF0Y2goLzxyZWN0IC9nKSB8fCBbXSkubGVuZ3RoKSk7CmNoaygn6LGh6ZmQ"
    "5ZyW5pyJ5rOh5rOhJywgKHN2Z09mKCdjaFF1YWQnKS5tYXRjaCgvPGNpcmNsZSAvZykgfHwgW10pLmxlbmd0aCA+IDEwLAog"
    "IFN0cmluZygoc3ZnT2YoJ2NoUXVhZCcpLm1hdGNoKC88Y2lyY2xlIC9nKSB8fCBbXSkubGVuZ3RoKSk7CmNoaygn576k57WE"
    "IGNoaXBzIOW3sua4suafkycsIChzdmdPZignY0ZpbHRlcicpLm1hdGNoKC9jbGFzcz0iY2hpcC9nKSB8fCBbXSkubGVuZ3Ro"
    "ID49IDUsCiAgU3RyaW5nKChzdmdPZignY0ZpbHRlcicpLm1hdGNoKC9jbGFzcz0iY2hpcC9nKSB8fCBbXSkubGVuZ3RoKSk7"
    "CmNoaygn54ShIE5hTiDmtKnmvI/liLAgU1ZHJywgIS9OYU58dW5kZWZpbmVkLy50ZXN0KHN2Z09mKCdjaFRyZW5kJykgKyBz"
    "dmdPZignY2hRdWFkJykpLAogICdmb3VuZCBOYU4vdW5kZWZpbmVkJyk7CgovLyAtLS0tLS0tLS0tIGRyaXZlIGV2ZXJ5IGNy"
    "aXRlcmlvbiAtLS0tLS0tLS0tCmZ1bmN0aW9uIHNldFNlbChpZCwgdikgeyBSRUdbaWRdLnZhbHVlID0gU3RyaW5nKHYpOyBS"
    "RUdbaWRdLmZpcmUoJ2NoYW5nZScpOyB9CmZ1bmN0aW9uIHNldFJhbmdlKGlkLCB2KSB7IFJFR1tpZF0udmFsdWUgPSBTdHJp"
    "bmcodik7IFJFR1tpZF0uZmlyZSgnaW5wdXQnKTsgfQoKY29uc29sZS5sb2coJ1xuICBb6amF5YuV5q+P5LiA5YCL5Y+v6K6K"
    "IENSSVRFUklBXScpOwpsZXQgcHJldiwgY2hhbmdlZDsKCnByZXYgPSBzdmdPZignY2hUcmVuZCcpOwpzZXRTZWwoJ2NXaW4n"
    "LCAyMCk7CmNoaygn6KaW56qXIDEyMOKGkjIwIOinuOeZvOmHjeeulycsIHN2Z09mKCdjaFRyZW5kJykgIT09IHByZXYgJiYg"
    "aXNTdmcoJ2NoVHJlbmQnKSk7CmNoaygn6KaW56qXIDIwRCDmqJnnpLrmraPnoronLCAvMjBELy50ZXN0KFJFRy50VHJlbmQu"
    "dGV4dENvbnRlbnQpLCBSRUcudFRyZW5kLnRleHRDb250ZW50KTsKc2V0U2VsKCdjV2luJywgMjUwKTsKY2hrKCfoppbnqpcg"
    "MjUwRCDku43lj6/muLLmn5MnLCBpc1N2ZygnY2hUcmVuZCcpICYmIGFwaS5DUklULndpbiA9PT0gMjUwLCBTdHJpbmcoYXBp"
    "LkNSSVQud2luKSk7CgpbJ3ByaWNlJywgJ3ZvbCcsICdycycsICdmaXMnXS5mb3JFYWNoKG10ID0+IHsKICBwcmV2ID0gc3Zn"
    "T2YoJ2NoVHJlbmQnKTsKICBzZXRTZWwoJ2NNZXRyaWMnLCBtdCk7CiAgY2hrKCfmjIfmqJnliIfmj5sgJyArIG10LCBpc1N2"
    "ZygnY2hUcmVuZCcpICYmIGFwaS5DUklULm1ldHJpYyA9PT0gbXQsCiAgICBhcGkuQ1JJVC5tZXRyaWMgKyAnIC8gJyArIHN2"
    "Z09mKCdjaFRyZW5kJykuc2xpY2UoMCwgNDApKTsKICBjaGsoJ+aMh+aomSAnICsgbXQgKyAnIOeEoSBOYU4nLCAhL05hTi8u"
    "dGVzdChzdmdPZignY2hUcmVuZCcpKSk7Cn0pOwoKWydhc3NldCcsICd0aWVyJywgJ25vbmUnLCAncmVnaW9uJ10uZm9yRWFj"
    "aChnID0+IHsKICBzZXRTZWwoJ2NHcm91cCcsIGcpOwogIGNoaygn5YiG57WE5YiH5o+bICcgKyBnLCBpc1N2ZygnY2hUcmVu"
    "ZCcpICYmIGFwaS5DUklULmdyb3VwID09PSBnLCBhcGkuQ1JJVC5ncm91cCk7Cn0pOwoKc2V0U2VsKCdjQWdnJywgJ2VhY2gn"
    "KTsKY29uc3QgZWFjaE4gPSAoc3ZnT2YoJ2NoVHJlbmQnKS5tYXRjaCgvPHBhdGggL2cpIHx8IFtdKS5sZW5ndGg7CnNldFNl"
    "bCgnY0FnZycsICdiYXNrZXQnKTsKY29uc3QgYmFza2V0TiA9IChzdmdPZignY2hUcmVuZCcpLm1hdGNoKC88cGF0aCAvZykg"
    "fHwgW10pLmxlbmd0aDsKY2hrKCfpgJDmqpTnt5rmlbggPiDnsYPlrZDnt5rmlbgnLCBlYWNoTiA+IGJhc2tldE4sIGVhY2hO"
    "ICsgJyB2cyAnICsgYmFza2V0Tik7CgpwcmV2ID0gc3ZnT2YoJ2NoSGVhdCcpOwpzZXRSYW5nZSgnY0hvdCcsIDcwKTsKY2hr"
    "KCfnhrHljYDploDmqrvmi4nmob/op7jnmbzph43nrpcnLCBzdmdPZignY2hIZWF0JykgIT09IHByZXYpOwpjaGsoJ+mWgOaq"
    "u+aomeexpOWQjOatpScsIFJFRy5jSG90Vi50ZXh0Q29udGVudCA9PT0gJzcwJywgUkVHLmNIb3RWLnRleHRDb250ZW50KTsK"
    "Y2hrKCdDUklULmhvdCDlt7Lmm7TmlrAnLCBhcGkuQ1JJVC5ob3QgPT09IDcwLCBTdHJpbmcoYXBpLkNSSVQuaG90KSk7Cgpw"
    "cmV2ID0gc3ZnT2YoJ2NoVHJlbmQnKTsKc2V0UmFuZ2UoJ2NTbW9vdGgnLCAyMSk7CmNoaygn5bmz5ruR5ouJ5qG/6Ke455m8"
    "6YeN566XJywgc3ZnT2YoJ2NoVHJlbmQnKSAhPT0gcHJldiAmJiBhcGkuQ1JJVC5zbW9vdGggPT09IDIxLCBTdHJpbmcoYXBp"
    "LkNSSVQuc21vb3RoKSk7CnNldFJhbmdlKCdjU21vb3RoJywgMSk7CmNoaygn5bmz5ruRIDFE77yI5LiN5bmz5ruR77yJ5Y+v"
    "5riy5p+TJywgaXNTdmcoJ2NoVHJlbmQnKSk7CgpzZXRSYW5nZSgnY01pbicsIDIwMCk7CmNoaygn5pyA5bCR5qij5pysIDIw"
    "MCDku43kuI3ltKknLCB0eXBlb2Ygc3ZnT2YoJ2NoVHJlbmQnKSA9PT0gJ3N0cmluZycgJiYgYXBpLkNSSVQubWluYmFycyA9"
    "PT0gMjAwLAogIFN0cmluZyhhcGkuQ1JJVC5taW5iYXJzKSk7CnNldFJhbmdlKCdjTWluJywgMCk7CgpbJ21lYW4nLCAnZGVs"
    "dGEnLCAnbmFtZScsICdsYXN0J10uZm9yRWFjaChzayA9PiB7CiAgc2V0U2VsKCdjU29ydCcsIHNrKTsKICBjaGsoJ+aOkuW6"
    "jyAnICsgc2ssIGlzU3ZnKCdjaFRyZW5kJykgJiYgYXBpLkNSSVQuc29ydCA9PT0gc2ssIGFwaS5DUklULnNvcnQpOwp9KTsK"
    "Ci8vIGNoaXAgZmlsdGVyaW5nCnNldFNlbCgnY0dyb3VwJywgJ3JlZ2lvbicpOwpjb25zdCBjaGlwcyA9IFJFRy5jRmlsdGVy"
    "LnF1ZXJ5U2VsZWN0b3JBbGwoJy5jaGlwJyk7CmNoaygnY2hpcHMg5Y+v6bue5pOK57aB5a6aJywgY2hpcHMubGVuZ3RoID49"
    "IDUsIFN0cmluZyhjaGlwcy5sZW5ndGgpKTsKaWYgKGNoaXBzLmxlbmd0aCkgewogIGNvbnN0IGJlZm9yZSA9IChzdmdPZign"
    "Y2hUcmVuZCcpLm1hdGNoKC88cGF0aCAvZykgfHwgW10pLmxlbmd0aDsKICBjaGlwc1swXS5maXJlKCdjbGljaycpOwogIGNv"
    "bnN0IGFmdGVyID0gKHN2Z09mKCdjaFRyZW5kJykubWF0Y2goLzxwYXRoIC9nKSB8fCBbXSkubGVuZ3RoOwogIGNoaygn6Zec"
    "6ZaJ5LiA5YCL576k57WE5pyD5bCR5LiA5qKd57eaJywgYWZ0ZXIgPT09IGJlZm9yZSAtIDEsIGJlZm9yZSArICcgLT4gJyAr"
    "IGFmdGVyKTsKICBjaGlwc1swXS5maXJlKCdjbGljaycpOwogIGNoaygn5YaN6bue5Zue5L6G57ea5pW45b6p5Y6fJywKICAg"
    "IChzdmdPZignY2hUcmVuZCcpLm1hdGNoKC88cGF0aCAvZykgfHwgW10pLmxlbmd0aCA9PT0gYmVmb3JlKTsKfQoKLy8gdHVy"
    "biBldmVyeXRoaW5nIG9mZiAtPiBtdXN0IGRlZ3JhZGUgZ3JhY2VmdWxseSwgbm90IGNyYXNoCmNvbnN0IGFsbCA9IFJFRy5j"
    "RmlsdGVyLnF1ZXJ5U2VsZWN0b3JBbGwoJy5jaGlwJyk7CmFsbC5mb3JFYWNoKGMgPT4geyBpZiAoIWFwaS5PRkZbYy5kYXRh"
    "c2V0LmtdKSBjLmZpcmUoJ2NsaWNrJyk7IH0pOwpjaGsoJ+WFqOmDqOmXnOmWieaZgumhr+ekuuaPkOekuuiAjOmdnuW0qea9"
    "sCcsIC9lbXB0eS1jaGFydC8udGVzdChzdmdPZignY2hUcmVuZCcpKSwgc3ZnT2YoJ2NoVHJlbmQnKS5zbGljZSgwLCA3MCkp"
    "OwphbGwuZm9yRWFjaChjID0+IHsgaWYgKGFwaS5PRkZbYy5kYXRhc2V0LmtdKSBjLmZpcmUoJ2NsaWNrJyk7IH0pOwoKLy8g"
    "cmVzZXQKc2V0U2VsKCdjV2luJywgMjApOyBzZXRTZWwoJ2NNZXRyaWMnLCAncHJpY2UnKTsgc2V0UmFuZ2UoJ2NIb3QnLCA4"
    "MCk7ClJFRy5jUmVzZXQuZmlyZSgnY2xpY2snKTsKY2hrKCfph43oqK3lm57poJDoqK3lgLwnLAogIGFwaS5DUklULndpbiA9"
    "PT0gMTIwICYmIGFwaS5DUklULm1ldHJpYyA9PT0gJ2ZpcycgJiYgYXBpLkNSSVQuaG90ID09PSAzMCwKICBKU09OLnN0cmlu"
    "Z2lmeShhcGkuQ1JJVCkpOwpjaGsoJ+mHjeioreW+jOWcluS7jeWcqCcsIGlzU3ZnKCdjaFRyZW5kJykpOwoKLy8gbnVtZXJp"
    "YyBzYW5pdHk6IEZJUyBiYXNrZXQgdmFsdWVzIG11c3Qgc3RheSBpbiArLy0xMDAKc2V0U2VsKCdjTWV0cmljJywgJ2Zpcycp"
    "OyBzZXRTZWwoJ2NBZ2cnLCAnYmFza2V0Jyk7CmNvbnN0IGxpbmVzID0gYXBpLmJ1aWxkTGluZXMoKTsKY29uc3QgYmFkID0g"
    "bGluZXMuZmlsdGVyKGwgPT4gbC5sYXN0ICE9PSBudWxsICYmIE1hdGguYWJzKGwubGFzdCkgPiAxMDApOwpjaGsoJ+exg+Wt"
    "kCBGSVMg5LiN6LaK55WMIMKxMTAwJywgYmFkLmxlbmd0aCA9PT0gMCwgSlNPTi5zdHJpbmdpZnkoYmFkLm1hcChiID0+IFti"
    "LmxhYmVsLCBiLmxhc3RdKSkpOwpjaGsoJ+exg+WtkOacieaIkOWToeaVuCcsIGxpbmVzLmV2ZXJ5KGwgPT4gbC5uID49IDEp"
    "KTsKCmZ1bmN0aW9uIGZpbmlzaCgpIHsKICBjb25zb2xlLmxvZygnXG4nICsgJz0nLnJlcGVhdCg3NCkpOwogIGNvbnNvbGUu"
    "bG9nKCcgIFVTRVItVEVTVCAgJyArIFBBU1MgKyAnLycgKyAoUEFTUyArIEZBSUwubGVuZ3RoKSArICcgUEFTUycpOwogIEZB"
    "SUwuZm9yRWFjaChmID0+IGNvbnNvbGUubG9nKCcgICBGQUlMICAnICsgZlswXSArICcgICAnICsgZlsxXSkpOwogIGNvbnNv"
    "bGUubG9nKCc9Jy5yZXBlYXQoNzQpKTsKICBwcm9jZXNzLmV4aXQoRkFJTC5sZW5ndGggPyAxIDogMCk7Cn0KZmluaXNoKCk7"
    "Cg=="
)

def run_uitest(html_path: Path | None, log: Log) -> int:
    """把產出的 HTML 丟進 node，以最小 DOM shim 執行其中的圖表引擎。

    這不是靜態檢查：控制項會被真的觸發，圖會被真的重繪，SVG 會被真的斷言。
    找不到 node 時回 skip（不視為失敗），因為 node 並非本引擎的執行期依賴。
    """
    import subprocess
    import tempfile

    node = shutil.which("node")
    if not node:
        log.warn("找不到 node，UI 測試略過（node 不是本引擎的執行期依賴）")
        return 0

    if html_path is None:
        cands = sorted(Path(default_root()).glob("VIA_GlobalETFFlow_*.html"))
        if not cands:
            log.err("找不到可測試的 HTML，請先執行一次或用 --uitest <path>")
            return 2
        html_path = cands[-1]
    html_path = Path(html_path)
    if not html_path.exists():
        log.err("HTML 不存在：%s" % html_path)
        return 2

    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "harness.js"
        hp.write_bytes(base64.b64decode(UI_HARNESS_B64))
        proc = subprocess.run([node, str(hp), str(html_path)],
                              capture_output=True, text=True, timeout=300)
    sys.stdout.write(proc.stdout)
    if proc.stderr.strip():
        sys.stdout.write(proc.stderr)
    return proc.returncode


def run_all(args) -> int:
    """完整驗收閘門：單元 → 整合 → UI。任一環節失敗即整體失敗。"""
    global LOG
    saved_log = LOG
    LOG.banner("VIA GlobalETFFlow · FULL GATE", "selftest → mocktest → uitest")
    rc_unit = run_selftest()
    sys.stdout.write("\n")
    rc_int = run_mocktest(keep=True, quiet_tail=True)
    # mock harness 內部以 --quiet 呼叫 main()，會把全域 LOG 換成靜音版。
    # 不還原的話，後續的 GATE 標記會無聲消失——測試污染全域狀態的典型案例。
    LOG = saved_log
    html = _LAST_MOCK_HTML.get("path")
    sys.stdout.write("\n  [UI USER-TEST]\n")
    rc_ui = run_uitest(Path(html) if html else None, LOG)
    if _LAST_MOCK_HTML.get("workspace"):
        shutil.rmtree(_LAST_MOCK_HTML["workspace"], ignore_errors=True)
    worst = max(rc_unit, rc_int, rc_ui)
    LOG.banner("GATE %s" % ("VIA_ETFFLOW_V010_ALL_PASS" if worst == 0 else "FAILED"),
               "unit=%d integration=%d ui=%d" % (rc_unit, rc_int, rc_ui))
    return worst


_LAST_MOCK_HTML: dict = {}


# --------------------------------------------------------------------------- #
# 16.  PROBE
# --------------------------------------------------------------------------- #

def run_probe(src: Sources, log: Log) -> int:
    log.banner("VIA GlobalETFFlow · ENDPOINT PROBE", "read-only")
    checks = [
        ("Stooq 日線 SPY", lambda: len(src.daily_stooq("SPY"))),
        ("Stooq 日線 GLD", lambda: len(src.daily_stooq("GLD"))),
        ("Yahoo chart SPY", lambda: len(src.daily_yahoo("SPY", "6mo"))),
        ("Yahoo quoteSummary SPY (T1 股數)", lambda: len(src.shares_nav_yahoo("SPY"))),
        ("Yahoo quoteSummary IBIT", lambda: len(src.shares_nav_yahoo("IBIT"))),
    ]
    bad = 0
    for label, fn in checks:
        try:
            n = fn()
            if n:
                log.ok("%-38s  %d" % (label, n))
            else:
                log.warn("%-38s  空結果" % label)
                bad += 1
        except Exception as exc:                           # noqa: BLE001
            log.err("%-38s  %s" % (label, str(exc)[:70]))
            bad += 1
    log.step("PROBE：%d/%d 異常" % (bad, len(checks)))
    if bad:
        log.info("股數端失敗只影響 T1 真流；日線端可用時 T3 方向訊號仍可產出")
    return 0 if bad == 0 else 2


# --------------------------------------------------------------------------- #
# 17.  MAIN
# --------------------------------------------------------------------------- #

def default_root() -> Path:
    env = os.environ.get("VIA_ETFFLOW_ROOT")
    if env:
        return Path(env)
    for c in (Path(r"C:\VeritasIntelligenceAnalytics"),
              Path.home() / "Downloads" / "VeritasIntelligenceAnalytics"):
        if c.exists():
            return c / "VIA_GIF" / "ETFFlow" / "_active"
    return Path.cwd() / "VIA_GlobalETFFlow_out"


def build_parser():
    p = argparse.ArgumentParser(prog="VIA_GlobalETFFlow.py",
                                description="全球 ETF 資金流動監控引擎 (VIA MDL008)")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--cache", type=Path, default=None)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--tail", type=int, default=250,
                   help="嵌入 HTML 的時間軸長度（交易日）")
    p.add_argument("--group", choices=["region", "asset"], default="region",
                   help="主分頁聚合維度（另一維度仍會產出）")
    p.add_argument("--offline", action="store_true")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--open", dest="do_open", action="store_true")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--mocktest", action="store_true")
    p.add_argument("--keep", action="store_true")
    p.add_argument("--uitest", nargs="?", const="", default=None,
                   help="用 node 驗證產出 HTML 的互動；可選填 HTML 路徑")
    p.add_argument("--all", dest="run_all", action="store_true",
                   help="完整閘門：unit → integration → ui")
    p.add_argument("--probe", action="store_true")
    p.add_argument("--base-stooq", default=BASE_STOOQ)
    p.add_argument("--base-yahoo", default=BASE_YAHOO)
    return p


def main(argv=None) -> int:
    global LOG
    args = build_parser().parse_args(argv)

    if args.selftest:
        return run_selftest()
    if args.mocktest:
        return run_mocktest(keep=args.keep)
    if args.run_all:
        return run_all(args)
    if args.uitest is not None:
        return run_uitest(Path(args.uitest) if args.uitest else None, LOG)

    LOG = Log(quiet=args.quiet)
    log = LOG

    args.out = Path(args.out or default_root())
    args.cache = Path(args.cache) if args.cache else args.out / "_cache"
    args.out.mkdir(parents=True, exist_ok=True)

    http = Http(args.cache, offline=args.offline, no_cache=args.no_cache)
    src = Sources(http, args.base_stooq, args.base_yahoo)

    if args.probe:
        return run_probe(src, log)

    log.banner("VIA GlobalETFFlow %s · 全球 ETF 資金流動監控" % __version__,
               "真值階梯 T1 真流 / T3 估流 · 只增不減 · 輸出 %s" % args.out)

    uni = UniverseRegistry(args.out / "etf_universe_registry.json")
    shares = SharesRegistry(args.out / "etf_shares_registry.json")

    t0 = time.time()
    try:
        ds = build_dataset(src, uni, shares, args, log)
    except FetchError as exc:
        log.err("資料層失敗：%s" % exc)
        log.info("先跑 --probe 確認端點；--offline 需先有一次成功的線上執行")
        return 2

    uni.save()
    shares.save()

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = args.out / ("VIA_GlobalETFFlow_%s.html" % stamp)
    write_text(html_path, render_html(ds, log))
    export_json(ds, args.out / "etf_flow_matrix.json")
    export_csv(ds, args.out / "etf_flow_matrix.csv")
    latest = args.out / "VIA_GlobalETFFlow_latest.html"
    try:
        shutil.copy2(html_path, latest)
    except OSError:
        latest = html_path

    log.step("完成 %.1fs · 探針 %d · FIS 成立 %d · T1 真流 %d"
             % (time.time() - t0, ds["meta"]["n_probes"],
                ds["meta"]["n_fis"], ds["meta"]["n_primary"]))
    log.ok("HTML  %s" % html_path)
    log.ok("JSON  %s" % (args.out / "etf_flow_matrix.json"))
    log.ok("CSV   %s" % (args.out / "etf_flow_matrix.csv"))

    if ds["meta"]["n_fis"] == 0:
        log.err("FIS 全數 PENDING — 資料層等同全滅，請跑 --probe")
        return 3

    if args.do_open:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(latest))                  # noqa: S606
            elif sys.platform == "darwin":
                os.system("open '%s'" % latest)            # noqa: S605
            else:
                os.system("xdg-open '%s' >/dev/null 2>&1 &" % latest)   # noqa: S605
        except Exception as exc:                           # noqa: BLE001
            log.warn("無法自動開啟：%s" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
