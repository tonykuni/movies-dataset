#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_ActiveStockETF.py
=====================
VERITAS INTELLIGENCE ANALYTICS - Active Taiwan Stock ETF Console (data engine)

Fetches live data for the "主動式台股 ETF 戰情台" console template and renders a
standalone HTML console.  The ETF universe is DISCOVERED, never hardcoded: any
new 主動式 ETF (code suffix "A") approved and listed shows up automatically on
the next run and is flagged NEW.

Governance (VIA locked rules honoured here)
-------------------------------------------
  * 只增不減 / append-only  : the ETF registry never deletes a code.  A code that
                              disappears from the exchange feed transitions to
                              DORMANT and keeps its history.
  * Evidence honesty        : every field carries an evidence tag
                              V   = Confirmed Official (exchange / regulator feed)
                              M   = Media-verified
                              Der = Derived by rule from a V field
                              Est = Estimated (proxy used, stated)
                              P   = Pending (no source resolved -> renders "—")
                              Syn = Synthetic. NEVER emitted by this script.
                              No number is ever invented.  Missing stays missing.
  * UTF-8 no-BOM writes, no interactive input, one-shot run, HTML progress out.

Usage
-----
  python VIA_ActiveStockETF.py                  full run: discover -> fetch -> render
  python VIA_ActiveStockETF.py --selftest       offline unit tests (no network)
  python VIA_ActiveStockETF.py --probe          endpoint reachability matrix only
  python VIA_ActiveStockETF.py --offline        render from cache + registry only
  python VIA_ActiveStockETF.py --open           open the HTML when done
  python VIA_ActiveStockETF.py --months 14      months of daily history to pull
  python VIA_ActiveStockETF.py --suffix A,D     also include 主動式債券 ETF (D)

Stdlib only.  No pandas, no requests.  Runs in any VIA venv or bare python 3.9+.
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

import argparse
import concurrent.futures as _cf
import csv
import datetime as _dt
import gzip
import io
import json
import os
import re
import shutil
import sys
import threading
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

__version__ = "v0100"
__engine__ = "VIA-SPJ-ETF-ACTIVE"

# --------------------------------------------------------------------------- #
# 0.  CONFIG
# --------------------------------------------------------------------------- #

DEFAULT_ROOT = Path(os.environ.get("VIA_ETF_ROOT", "")) if os.environ.get("VIA_ETF_ROOT") else None

# Endpoint bases are overridable so the whole pipeline can be pointed at a local
# mock server for testing without touching a line of pipeline code.
BASE_OPENAPI = "https://openapi.twse.com.tw/v1"
BASE_TWSE = "https://www.twse.com.tw"
BASE_ISIN = "https://isin.twse.com.tw"
BASE_TPEX = "https://www.tpex.org.tw"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) VIA/ActiveStockETF "
              + __version__ + " (+VeritasIntelligenceAnalytics)")

# TWSE throttles aggressive callers.  Keep a polite floor between requests to the
# same host; the exchange's documented soft limit is ~3 requests / 5 seconds.
HOST_MIN_INTERVAL = {
    "www.twse.com.tw": 1.9,
    "openapi.twse.com.tw": 0.35,
    "isin.twse.com.tw": 1.0,
    "www.tpex.org.tw": 1.2,
}
DEFAULT_MIN_INTERVAL = 0.5

HTTP_TIMEOUT = 25
HTTP_RETRIES = 3
CACHE_TTL_SECONDS = 6 * 3600          # intraday reuse; history months cached longer
CACHE_TTL_HISTORY = 20 * 24 * 3600    # closed months never change

# Return horizons rendered in the performance matrix (trading days).
HORIZONS = [1, 5, 10, 20, 60, 120, 240]

# A code is flagged NEW for this many days after its listing date.
NEW_WINDOW_DAYS = 90

# Evidence tags
EV_OFFICIAL = "V"
EV_MEDIA = "M"
EV_DERIVED = "Der"
EV_ESTIMATED = "Est"
EV_PENDING = "P"

EVIDENCE_LABEL = {
    EV_OFFICIAL: "官方確認",
    EV_MEDIA: "媒體驗證",
    EV_DERIVED: "規則推導",
    EV_ESTIMATED: "估算",
    EV_PENDING: "待補",
}

# Visual Lock design tokens (locked - do not drift)
VL = {
    "bg": "#f5f4f0", "paper": "#fff", "paper2": "#fafaf8",
    "ink": "#1e1d1a", "ink2": "#33403f", "mut": "#6b6860", "mut2": "#9c9890",
    "line": "#dbd9d3", "soft": "#ecebe6",
    "accent": "#439a9a", "blue": "#4c78a8", "teal": "#439a9a",
    "up": "#c96b5a", "down": "#5a9e6f", "am": "#c4943a", "co": "#c96b5a",
    "vi": "#7a6daa", "gn": "#5a9e6f", "ro": "#b05580",
}
RESON = ("linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,"
         "#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)")

# 投信 (asset manager) names used to derive the manager from the fund name.
TRUST_NAMES = [
    "元大", "國泰", "富邦", "群益", "統一", "野村", "安聯", "中信", "凱基", "第一金",
    "兆豐", "台新", "永豐", "日盛", "華南永昌", "華南", "復華", "街口", "新光", "保德信",
    "柏瑞", "施羅德", "景順", "宏利", "瀚亞", "路博邁", "聯博", "富蘭克林", "貝萊德",
    "摩根", "安本", "匯豐", "王道", "合庫", "玉山", "土銀", "遠東", "紐約梅隆", "PGIM",
]

# Style classification rules: (keyword, style label).  First match wins.
# Derived by rule from the official fund name -> evidence tag "Der", never Syn.
STYLE_RULES = [
    ("高息", "高息"), ("收益", "高息"), ("配息", "高息"),
    ("科技", "科技"), ("AI", "科技"), ("半導體", "科技"), ("創新", "科技"),
    ("價值", "價值"),
    ("增長", "成長"), ("成長", "成長"), ("動能", "成長"), ("強棒", "成長"),
    ("領航", "成長"), ("未來", "成長"), ("新經濟", "成長"),
    ("優選", "優選"), ("精選", "優選"), ("優勢", "優選"), ("優質", "優選"),
    ("50", "優選"), ("台股", "優選"),
]
STYLE_CSS = {"成長": "var(--co)", "高息": "var(--am)", "優選": "var(--blue)",
             "價值": "var(--teal)", "科技": "var(--vi)"}


# --------------------------------------------------------------------------- #
# 1.  LOGGING
# --------------------------------------------------------------------------- #

class Log:
    """Console logger with phase tracking; also accumulates lines for the HTML run log."""

    LEVELS = {"OK": "\u2713", "WARN": "!", "ERR": "\u2717", "INFO": "\u00b7", "STEP": "\u25b8"}

    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.lines: list[tuple[str, str, float]] = []
        self.t0 = time.time()
        self._lock = threading.Lock()
        self.counts = {"OK": 0, "WARN": 0, "ERR": 0, "INFO": 0, "STEP": 0}

    def _emit(self, level: str, msg: str) -> None:
        with self._lock:
            self.counts[level] = self.counts.get(level, 0) + 1
            self.lines.append((level, msg, time.time() - self.t0))
            if not self.quiet:
                mark = self.LEVELS.get(level, "-")
                sys.stdout.write("  [%6.1fs] %s %s\n" % (time.time() - self.t0, mark, msg))
                sys.stdout.flush()

    def step(self, msg): self._emit("STEP", msg)
    def ok(self, msg): self._emit("OK", msg)
    def warn(self, msg): self._emit("WARN", msg)
    def err(self, msg): self._emit("ERR", msg)
    def info(self, msg): self._emit("INFO", msg)

    def banner(self, title: str, sub: str = "") -> None:
        if self.quiet:
            return
        bar = "=" * 74
        sys.stdout.write("\n%s\n  %s\n" % (bar, title))
        if sub:
            sys.stdout.write("  %s\n" % sub)
        sys.stdout.write("%s\n" % bar)
        sys.stdout.flush()


LOG = Log()


# --------------------------------------------------------------------------- #
# 2.  HTTP LAYER  (stdlib, cached, rate-limited, retrying)
# --------------------------------------------------------------------------- #

class FetchError(Exception):
    pass


class Http:
    """Polite HTTP client with on-disk cache, per-host rate limiting and retries."""

    def __init__(self, cache_dir: Path, offline: bool = False, no_cache: bool = False):
        self.cache_dir = cache_dir
        self.offline = offline
        self.no_cache = no_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_hit: dict[str, float] = {}
        self._lock = threading.Lock()
        self.stats = {"net": 0, "cache": 0, "fail": 0}

    # -- cache ------------------------------------------------------------- #
    @staticmethod
    def _key(url: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", url)
        if len(safe) > 120:
            import hashlib
            safe = safe[:90] + "_" + hashlib.blake2s(url.encode("utf-8"), digest_size=6).hexdigest()
        return safe

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / (self._key(url) + ".bin")

    def _cache_read(self, url: str, ttl: int):
        p = self._cache_path(url)
        if not p.exists():
            return None
        if not self.offline and ttl >= 0 and (time.time() - p.stat().st_mtime) > ttl:
            return None
        try:
            return p.read_bytes()
        except OSError:
            return None

    def _cache_write(self, url: str, data: bytes) -> None:
        if self.no_cache:
            return
        try:
            self._cache_path(url).write_bytes(data)
        except OSError:
            pass

    # -- throttle ---------------------------------------------------------- #
    def _throttle(self, host: str) -> None:
        gap = HOST_MIN_INTERVAL.get(host, DEFAULT_MIN_INTERVAL)
        with self._lock:
            last = self._last_hit.get(host, 0.0)
            wait = gap - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
            self._last_hit[host] = time.time()

    # -- fetch ------------------------------------------------------------- #
    def get(self, url: str, ttl: int = CACHE_TTL_SECONDS, referer: str = "") -> bytes:
        cached = self._cache_read(url, ttl)
        if cached is not None:
            self.stats["cache"] += 1
            return cached
        if self.offline:
            raise FetchError("offline and not cached: %s" % url)

        host = urllib.parse.urlparse(url).netloc
        last_exc = None
        for attempt in range(1, HTTP_RETRIES + 1):
            self._throttle(host)
            req = urllib.request.Request(url)
            req.add_header("User-Agent", USER_AGENT)
            req.add_header("Accept", "application/json, text/csv, text/html;q=0.9, */*;q=0.8")
            req.add_header("Accept-Encoding", "gzip")
            req.add_header("Connection", "close")
            if referer:
                req.add_header("Referer", referer)
            try:
                with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding", "") == "gzip":
                        try:
                            raw = gzip.decompress(raw)
                        except OSError:
                            pass
                self.stats["net"] += 1
                self._cache_write(url, raw)
                return raw
            except Exception as exc:                     # noqa: BLE001 - want every failure mode
                last_exc = exc
                if attempt < HTTP_RETRIES:
                    time.sleep(min(6.0, 1.2 * (2 ** (attempt - 1))))
        self.stats["fail"] += 1
        stale = self._cache_read(url, -1)
        if stale is not None:
            LOG.warn("網路失敗，改用過期快取 %s" % url.split("/")[-1][:60])
            return stale
        raise FetchError("%s -> %s" % (url, last_exc))

    def get_json(self, url: str, ttl: int = CACHE_TTL_SECONDS, referer: str = ""):
        raw = self.get(url, ttl=ttl, referer=referer)
        return json.loads(decode_text(raw))

    def get_text(self, url: str, ttl: int = CACHE_TTL_SECONDS, referer: str = "") -> str:
        return decode_text(self.get(url, ttl=ttl, referer=referer))


def decode_text(raw: bytes) -> str:
    """Decode TWSE payloads: UTF-8 (with/without BOM) first, then Big5/cp950."""
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    for enc in ("utf-8", "utf-8-sig", "cp950", "big5hkscs", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# 3.  SMALL UTILITIES
# --------------------------------------------------------------------------- #

def roc_to_iso(s: str) -> str | None:
    """'1150731' or '115/07/31' or '115年07月31日' -> '2026-07-31'."""
    if not s:
        return None
    digits = re.sub(r"\D", "", str(s))
    if len(digits) == 7:
        y, m, d = int(digits[:3]) + 1911, digits[3:5], digits[5:7]
    elif len(digits) == 6:
        y, m, d = int(digits[:2]) + 1911, digits[2:4], digits[4:6]
    elif len(digits) == 8 and digits[0] in "12":
        return "%s-%s-%s" % (digits[:4], digits[4:6], digits[6:8])
    else:
        return None
    try:
        _dt.date(y, int(m), int(d))
    except ValueError:
        return None
    return "%04d-%s-%s" % (y, m, d)


def to_float(v) -> float | None:
    """Parse TWSE numeric strings: '1,234.5', '--', '', 'X0.00', None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("+", "")
    if s in ("", "--", "-", "---", "N/A", "NA", "null", "None"):
        return None
    s = re.sub(r"[^\d.\-eE]", "", s)
    if s in ("", "-", ".", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int(v) -> int | None:
    f = to_float(v)
    return None if f is None else int(round(f))


def norm_text(s) -> str:
    if s is None:
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip()


def today_tw() -> _dt.date:
    """Taipei calendar date (UTC+8) regardless of host timezone."""
    return (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=8)).date()


def month_starts(months: int, end: _dt.date | None = None) -> list[str]:
    """Return ['20250801', ...] first-of-month stamps, oldest first."""
    end = end or today_tw()
    out, y, m = [], end.year, end.month
    for _ in range(months):
        out.append("%04d%02d01" % (y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


# --------------------------------------------------------------------------- #
# 4.  EVIDENCE-TAGGED VALUE
# --------------------------------------------------------------------------- #

class Val:
    """A value plus where it came from.  A Val with value None renders as '—'."""

    __slots__ = ("value", "evidence", "source", "note")

    def __init__(self, value=None, evidence: str = EV_PENDING, source: str = "", note: str = ""):
        self.value = value
        self.evidence = evidence if value is not None else EV_PENDING
        self.source = source
        self.note = note

    @property
    def ok(self) -> bool:
        return self.value is not None

    def as_dict(self) -> dict:
        return {"value": self.value, "evidence": self.evidence,
                "source": self.source, "note": self.note}

    def __repr__(self):
        return "Val(%r,%s)" % (self.value, self.evidence)


PENDING = Val()


# --------------------------------------------------------------------------- #
# 5.  SOURCE ADAPTERS
# --------------------------------------------------------------------------- #

class Sources:
    """Every exchange/regulator endpoint this engine speaks to.

    Each adapter returns parsed rows or raises FetchError.  Nothing here
    fabricates a value: a source that cannot be resolved yields no rows and the
    dependent field stays PENDING.
    """

    def __init__(self, http: Http, base_openapi=BASE_OPENAPI, base_twse=BASE_TWSE,
                 base_isin=BASE_ISIN, base_tpex=BASE_TPEX):
        self.http = http
        self.b_open = base_openapi.rstrip("/")
        self.b_twse = base_twse.rstrip("/")
        self.b_isin = base_isin.rstrip("/")
        self.b_tpex = base_tpex.rstrip("/")

    # -- 5.1 fund master ---------------------------------------------------- #
    def fund_master(self) -> list[dict]:
        """TWSE OpenAPI 基金基本資料彙總表 (t187ap47_L).

        The authoritative record for: fund code, Chinese name, fund type,
        listing date, 基金經理人 (portfolio manager) and 發行單位數.
        """
        url = self.b_open + "/opendata/t187ap47_L"
        rows = self.http.get_json(url, ttl=CACHE_TTL_SECONDS)
        if not isinstance(rows, list):
            raise FetchError("fund_master: unexpected payload type")
        return rows

    # -- 5.2 whole-market daily quote --------------------------------------- #
    def stock_day_all(self) -> list[dict]:
        """TWSE OpenAPI 上市個股日成交資訊 - whole listed market, latest session."""
        url = self.b_open + "/exchangeReport/STOCK_DAY_ALL"
        rows = self.http.get_json(url, ttl=CACHE_TTL_SECONDS)
        if not isinstance(rows, list):
            raise FetchError("stock_day_all: unexpected payload type")
        return rows

    # -- 5.3 per-code monthly history --------------------------------------- #
    def stock_day(self, code: str, yyyymmdd: str) -> list[list]:
        """TWSE 個股日成交資訊 for one code, one month.

        Returns raw rows: [日期, 成交股數, 成交金額, 開盤, 最高, 最低, 收盤, 漲跌, 筆數]
        """
        url = ("%s/rwd/zh/afterTrading/STOCK_DAY?date=%s&stockNo=%s&response=json"
               % (self.b_twse, yyyymmdd, code))
        # A month that has fully closed can be cached hard; the current month cannot.
        cur = today_tw().strftime("%Y%m")
        ttl = CACHE_TTL_SECONDS if yyyymmdd[:6] >= cur else CACHE_TTL_HISTORY
        try:
            doc = self.http.get_json(url, ttl=ttl, referer=self.b_twse + "/zh/trading/historical/stock-day.html")
        except FetchError:
            # legacy path still served by TWSE for older tooling
            url2 = ("%s/exchangeReport/STOCK_DAY?date=%s&stockNo=%s&response=json"
                    % (self.b_twse, yyyymmdd, code))
            doc = self.http.get_json(url2, ttl=ttl)
        if not isinstance(doc, dict):
            raise FetchError("stock_day: unexpected payload")
        if str(doc.get("stat", "")).upper() not in ("OK", ""):
            return []
        return doc.get("data") or []

    # -- 5.4 ISIN security master ------------------------------------------- #
    def isin_list(self, mode: int) -> list[dict]:
        """isin.twse.com.tw C_public.jsp - Big5 HTML table of every listed security.

        mode 2 = 上市 (TWSE), mode 4 = 上櫃 (TPEx).  Used as a cross-check on the
        universe so a new listing is caught even if the fund master lags.
        """
        url = "%s/isin/C_public.jsp?strMode=%d" % (self.b_isin, mode)
        html_text = self.http.get_text(url, ttl=CACHE_TTL_SECONDS)
        return parse_isin_table(html_text)

    # -- 5.5 ETF net asset value -------------------------------------------- #
    def etf_nav(self) -> list[dict]:
        """ETF 每受益權單位淨值.

        TWSE has moved this dataset between paths over the years, so a candidate
        chain is tried in order.  If none resolves, callers fall back to the
        closing price as an explicitly-Estimated NAV proxy.
        """
        candidates = [
            self.b_twse + "/rwd/zh/ETF/etfNav?response=json",
            self.b_twse + "/rwd/zh/ETF/etfNav?response=json&date=" + today_tw().strftime("%Y%m%d"),
            self.b_open + "/fund/etfNav",
        ]
        errors = []
        for url in candidates:
            try:
                doc = self.http.get_json(url, ttl=CACHE_TTL_SECONDS)
            except Exception as exc:                      # noqa: BLE001
                errors.append("%s: %s" % (url.rsplit("/", 1)[-1][:40], exc))
                continue
            rows = doc if isinstance(doc, list) else (doc.get("data") or doc.get("aaData") or [])
            parsed = parse_nav_rows(rows)
            if parsed:
                return parsed
        raise FetchError("etf_nav: no candidate resolved (%s)" % "; ".join(errors[:3]))

    # -- 5.6 TPEx daily quotes ---------------------------------------------- #
    def tpex_daily(self) -> list[dict]:
        """TPEx 上櫃每日收盤行情 - a handful of ETFs list on TPEx rather than TWSE."""
        url = self.b_tpex + "/openapi/v1/tpex_mainboard_daily_close_quotes"
        rows = self.http.get_json(url, ttl=CACHE_TTL_SECONDS)
        if not isinstance(rows, list):
            raise FetchError("tpex_daily: unexpected payload type")
        return rows


# -- parsers kept module-level so --selftest can exercise them offline ------- #

def parse_isin_table(html_text: str) -> list[dict]:
    """Parse the ISIN C_public table into {code, name, isin, listed, market, industry}."""
    out = []
    # Rows are plain <tr><td>...  The first cell is "CODE\u3000NAME" (ideographic space).
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html_text, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", m.group(1), re.S | re.I)
        if len(cells) < 4:
            continue
        clean = [re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ").strip() for c in cells]
        head = clean[0].replace("\u3000", " ").replace("\xa0", " ")
        parts = [p for p in head.split(" ") if p]
        if len(parts) < 2:
            continue
        code, name = parts[0].strip(), " ".join(parts[1:]).strip()
        if not re.match(r"^[0-9]{4,6}[A-Z]?$", code):
            continue
        out.append({
            "code": code, "name": name,
            "isin": clean[1] if len(clean) > 1 else "",
            "listed": roc_to_iso(clean[2]) or (clean[2] if len(clean) > 2 else ""),
            "market": clean[3] if len(clean) > 3 else "",
            "industry": clean[4] if len(clean) > 4 else "",
        })
    return out


def parse_nav_rows(rows) -> list[dict]:
    """Normalise a NAV payload (dict rows or positional list rows) to {code, nav, date}."""
    out = []
    for r in rows or []:
        code = nav = date = None
        if isinstance(r, dict):
            for k, v in r.items():
                kn = norm_text(k)
                if code is None and ("代號" in kn or "代碼" in kn or kn.lower() in ("code", "stockcode", "fundcode")):
                    code = norm_text(v)
                elif nav is None and ("淨值" in kn and "前一" not in kn and "折溢" not in kn):
                    nav = to_float(v)
                elif nav is None and kn.lower() in ("nav", "navpershare"):
                    nav = to_float(v)
                elif date is None and ("日期" in kn or kn.lower() == "date"):
                    date = roc_to_iso(v) or norm_text(v)
        elif isinstance(r, (list, tuple)) and len(r) >= 3:
            code, nav = norm_text(r[0]), to_float(r[2])
        if code and nav is not None and nav > 0:
            out.append({"code": code.upper(), "nav": nav, "date": date or ""})
    return out


def parse_stock_day_rows(rows: list[list]) -> list[dict]:
    """TWSE STOCK_DAY rows -> [{date, open, high, low, close, volume}] ascending."""
    out = []
    for r in rows or []:
        if not isinstance(r, (list, tuple)) or len(r) < 7:
            continue
        iso = roc_to_iso(r[0])
        close = to_float(r[6])
        if not iso or close is None or close <= 0:
            continue
        out.append({
            "date": iso,
            "volume": to_int(r[1]),
            "open": to_float(r[3]),
            "high": to_float(r[4]),
            "low": to_float(r[5]),
            "close": close,
        })
    out.sort(key=lambda x: x["date"])
    return out


# --------------------------------------------------------------------------- #
# 6.  UNIVERSE DISCOVERY  (the "automatically update the list" part)
# --------------------------------------------------------------------------- #

def is_active_etf_code(code: str, suffixes: str = "A") -> bool:
    """Taiwan active-ETF code shape: 5 digits + a letter suffix.

    A = 主動式股票型 (00981A, 00403A ...), D = 主動式債券型 (00982D ...).
    Passive suffixes B/K/L/R/U and plain 4-digit equities are excluded.
    """
    if not code:
        return False
    c = code.strip().upper()
    return bool(re.match(r"^\d{5}[%s]$" % re.escape(suffixes), c))


def derive_trust(name: str) -> Val:
    """Derive 投信 (asset manager) from the official fund name."""
    n = norm_text(name)
    for t in sorted(TRUST_NAMES, key=len, reverse=True):
        if t in n:
            return Val(t + "投信" if not t.endswith("投信") else t, EV_DERIVED, "fund name")
    return Val(None)


def derive_style(name: str) -> Val:
    """Derive the strategy style bucket from the official fund name."""
    n = norm_text(name)
    for kw, style in STYLE_RULES:
        if kw in n:
            return Val(style, EV_DERIVED, "fund name")
    return Val(None)


def discover_universe(src: Sources, suffixes: str, log: Log) -> tuple[dict[str, dict], dict]:
    """Union every independent listing feed, keyed by code.

    No code list is hardcoded anywhere: whatever the exchange publishes with an
    active-ETF code shape becomes the universe for this run.  Newly approved
    funds therefore appear without any edit to this file.
    """
    found: dict[str, dict] = {}
    diag = {"fund_master": "", "stock_day_all": "", "isin_twse": "", "isin_tpex": "", "tpex": ""}

    # (a) fund master - richest record: PM, listing date, units outstanding
    try:
        for r in src.fund_master():
            code = norm_text(r.get("基金代號") or r.get("基金代碼") or r.get("Code"))
            if not is_active_etf_code(code, suffixes):
                continue
            name = norm_text(r.get("基金中文名稱") or r.get("基金簡稱") or "")
            rec = found.setdefault(code.upper(), {"code": code.upper()})
            rec.update({
                "name": name or rec.get("name", ""),
                "short_name": norm_text(r.get("基金簡稱") or ""),
                "fund_type": norm_text(r.get("基金類型") or ""),
                "pm": norm_text(r.get("基金經理人") or ""),
                "listed": roc_to_iso(r.get("上市日期")) or roc_to_iso(r.get("成立日期")) or "",
                "units": to_float(r.get("發行單位數/轉換數") or r.get("發行單位數")),
                "market": "TWSE",
                "src": ["fund_master"],
            })
        diag["fund_master"] = "OK %d 檔" % sum(1 for v in found.values() if "fund_master" in v.get("src", []))
        log.ok("基金基本資料彙總表：命中 %s" % diag["fund_master"])
    except Exception as exc:                              # noqa: BLE001
        diag["fund_master"] = "FAIL %s" % exc
        log.warn("基金基本資料彙總表失敗：%s" % exc)

    # (b) whole-market daily quotes - catches anything trading today
    try:
        n_new = 0
        for r in src.stock_day_all():
            code = norm_text(r.get("Code"))
            if not is_active_etf_code(code, suffixes):
                continue
            rec = found.setdefault(code.upper(), {"code": code.upper(), "src": []})
            if not rec.get("name"):
                rec["name"] = norm_text(r.get("Name"))
                n_new += 1
            rec.setdefault("market", "TWSE")
            rec.setdefault("src", []).append("stock_day_all")
        diag["stock_day_all"] = "OK"
        log.ok("全市場日成交：交叉比對完成（新增 %d 檔僅見於行情表）" % n_new)
    except Exception as exc:                              # noqa: BLE001
        diag["stock_day_all"] = "FAIL %s" % exc
        log.warn("全市場日成交失敗：%s" % exc)

    # (c) ISIN masters - the registrar's own list, catches pre-trading listings
    for mode, key, market in ((2, "isin_twse", "TWSE"), (4, "isin_tpex", "TPEx")):
        try:
            for r in src.isin_list(mode):
                code = r["code"]
                if not is_active_etf_code(code, suffixes):
                    continue
                rec = found.setdefault(code.upper(), {"code": code.upper(), "src": []})
                if not rec.get("name"):
                    rec["name"] = r["name"]
                if not rec.get("listed"):
                    rec["listed"] = r.get("listed", "")
                rec.setdefault("market", market)
                rec.setdefault("src", []).append(key)
            diag[key] = "OK"
        except Exception as exc:                          # noqa: BLE001
            diag[key] = "FAIL %s" % exc
            log.warn("ISIN(%s) 失敗：%s" % (market, exc))

    # (d) TPEx quotes
    try:
        for r in src.tpex_daily():
            code = norm_text(r.get("SecuritiesCompanyCode") or r.get("Code") or r.get("股票代號"))
            if not is_active_etf_code(code, suffixes):
                continue
            rec = found.setdefault(code.upper(), {"code": code.upper(), "src": []})
            if not rec.get("name"):
                rec["name"] = norm_text(r.get("CompanyName") or r.get("Name") or r.get("名稱"))
            rec["market"] = "TPEx"
            rec.setdefault("src", []).append("tpex")
        diag["tpex"] = "OK"
    except Exception as exc:                              # noqa: BLE001
        diag["tpex"] = "FAIL %s" % exc

    # Fill derived attributes
    for rec in found.values():
        rec.setdefault("name", "")
        rec.setdefault("listed", "")
        rec.setdefault("pm", "")
        rec.setdefault("units", None)
        rec.setdefault("market", "TWSE")
        rec["trust"] = derive_trust(rec["name"])
        rec["style"] = derive_style(rec["name"])

    log.ok("宇宙探索完成：%d 檔主動式 ETF（後綴 %s）" % (len(found), suffixes))
    return found, diag


# --------------------------------------------------------------------------- #
# 7.  APPEND-ONLY REGISTRY  (只增不減)
# --------------------------------------------------------------------------- #

class Registry:
    """Append-only ETF registry + rolling units/NAV snapshot history.

    A code is never removed.  When the exchange stops publishing it, the entry
    transitions ACTIVE -> DORMANT and keeps every field it ever had.  The
    snapshot history is what makes YTD fund-flow computable over time: flow is
    derived from the change in units outstanding this engine has itself observed,
    so it starts PENDING and becomes real as history accumulates.
    """

    SCHEMA = 2

    def __init__(self, path: Path):
        self.path = path
        self.data = {"schema": self.SCHEMA, "created": "", "updated": "",
                     "entries": {}, "snapshots": {}}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.data["created"] = _dt.datetime.now().isoformat(timespec="seconds")
            return
        try:
            doc = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and "entries" in doc:
                self.data.update(doc)
                self.data.setdefault("snapshots", {})
        except (OSError, ValueError) as exc:
            LOG.warn("registry 讀取失敗，改用空白 registry：%s" % exc)

    def merge(self, found: dict[str, dict], run_date: str) -> dict:
        """Merge a discovery result.  Returns {new: [...], returned: [...], dormant: [...]}."""
        entries = self.data["entries"]
        report = {"new": [], "returned": [], "dormant": [], "total": 0}

        for code, rec in found.items():
            e = entries.get(code)
            if e is None:
                entries[code] = {
                    "code": code,
                    "first_seen": run_date,
                    "last_seen": run_date,
                    "status": "ACTIVE",
                    "name": rec.get("name", ""),
                    "listed": rec.get("listed", ""),
                    "market": rec.get("market", ""),
                    "history": [{"date": run_date, "event": "DISCOVERED"}],
                }
                report["new"].append(code)
            else:
                if e.get("status") == "DORMANT":
                    e.setdefault("history", []).append({"date": run_date, "event": "REACTIVATED"})
                    report["returned"].append(code)
                e["status"] = "ACTIVE"
                e["last_seen"] = run_date
                # append-only field fill: never blank out a value we once had
                for k in ("name", "listed", "market"):
                    if rec.get(k) and not e.get(k):
                        e[k] = rec[k]
                    elif rec.get(k) and e.get(k) and rec[k] != e[k]:
                        e.setdefault("history", []).append(
                            {"date": run_date, "event": "FIELD_CHANGED",
                             "field": k, "from": e[k], "to": rec[k]})
                        e[k] = rec[k]

        for code, e in entries.items():
            if code not in found and e.get("status") == "ACTIVE":
                e["status"] = "DORMANT"
                e.setdefault("history", []).append({"date": run_date, "event": "WENT_DORMANT"})
                report["dormant"].append(code)

        report["total"] = len(entries)
        return report

    def add_snapshot(self, code: str, run_date: str, nav, units) -> None:
        """Record one (date, nav, units) point.  Append-only, de-duplicated by date."""
        if nav is None and units is None:
            return
        series = self.data["snapshots"].setdefault(code, [])
        for pt in series:
            if pt.get("date") == run_date:
                if nav is not None:
                    pt["nav"] = nav
                if units is not None:
                    pt["units"] = units
                return
        series.append({"date": run_date, "nav": nav, "units": units})
        series.sort(key=lambda p: p["date"])

    def flow_ytd(self, code: str, year: int) -> Val:
        """Net creation flow (億元) this year, from observed units deltas."""
        series = [p for p in self.data["snapshots"].get(code, [])
                  if p.get("date", "")[:4] == str(year) and p.get("units") is not None]
        if len(series) < 2:
            return Val(None, note="快照歷史不足，需累積至少 2 個交易日")
        total = 0.0
        for prev, cur in zip(series, series[1:]):
            d_units = (cur["units"] or 0) - (prev["units"] or 0)
            nav = cur.get("nav") or prev.get("nav")
            if nav is None:
                continue
            total += d_units * nav
        return Val(round(total / 1e8, 1), EV_DERIVED,
                   "registry snapshots (%d pts)" % len(series))

    def save(self, run_date: str) -> None:
        self.data["updated"] = _dt.datetime.now().isoformat(timespec="seconds")
        self.data["schema"] = self.SCHEMA
        if not self.data.get("created"):
            self.data["created"] = self.data["updated"]
        tmp = self.path.with_suffix(".tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=1)
        # Keep the previous generation rather than overwriting it outright.
        if self.path.exists():
            bak = self.path.with_name(self.path.stem + "_prev.json")
            try:
                shutil.copy2(self.path, bak)
            except OSError:
                pass
        tmp.replace(self.path)


# --------------------------------------------------------------------------- #
# 8.  METRICS
# --------------------------------------------------------------------------- #

def build_price_series(src: Sources, code: str, months: int, log: Log) -> list[dict]:
    """Concatenate monthly STOCK_DAY pulls into one ascending daily series."""
    seen, series = set(), []
    for stamp in month_starts(months):
        try:
            rows = parse_stock_day_rows(src.stock_day(code, stamp))
        except Exception as exc:                          # noqa: BLE001
            log.warn("%s %s 月成交取得失敗：%s" % (code, stamp[:6], str(exc)[:70]))
            continue
        for r in rows:
            if r["date"] not in seen:
                seen.add(r["date"])
                series.append(r)
    series.sort(key=lambda x: x["date"])
    return series


def compute_returns(series: list[dict], horizons=None) -> dict:
    """Price returns over N trading days, plus YTD / since-listing.

    TWSE STOCK_DAY closes are unadjusted, so these are PRICE returns.  For a
    distributing ETF the total return is higher by the distributions paid; the
    console labels this explicitly rather than silently presenting it as total
    return.
    """
    horizons = horizons or HORIZONS
    out = {"horizons": {}, "ytd": Val(), "since": Val(), "last_close": Val(),
           "last_date": "", "day_pct": Val(), "volume": Val(), "points": len(series)}
    if not series:
        return out

    closes = [r["close"] for r in series]
    last = closes[-1]
    out["last_close"] = Val(last, EV_OFFICIAL, "TWSE STOCK_DAY")
    out["last_date"] = series[-1]["date"]
    if series[-1].get("volume") is not None:
        out["volume"] = Val(int(series[-1]["volume"] / 1000), EV_OFFICIAL, "TWSE STOCK_DAY")

    for n in horizons:
        if len(closes) > n and closes[-1 - n] > 0:
            out["horizons"][n] = Val(round((last / closes[-1 - n] - 1) * 100, 1),
                                     EV_OFFICIAL, "TWSE close ratio")
        else:
            out["horizons"][n] = Val(None, note="歷史不足 %dD（現有 %d 日）" % (n, len(closes)))

    if len(closes) >= 2 and closes[-2] > 0:
        out["day_pct"] = Val(round((last / closes[-2] - 1) * 100, 2), EV_OFFICIAL, "TWSE close ratio")

    year = series[-1]["date"][:4]
    prior = [r for r in series if r["date"][:4] < year]
    if prior and prior[-1]["close"] > 0:
        out["ytd"] = Val(round((last / prior[-1]["close"] - 1) * 100, 1),
                         EV_OFFICIAL, "TWSE close ratio (%s base)" % prior[-1]["date"])
    else:
        out["ytd"] = Val(None, note="本年度前無交易資料（今年掛牌），改看上市來")

    if closes[0] > 0:
        out["since"] = Val(round((last / closes[0] - 1) * 100, 1), EV_OFFICIAL,
                           "TWSE close ratio (%s base)" % series[0]["date"])
    return out


# --------------------------------------------------------------------------- #
# 9.  HOLDINGS
# --------------------------------------------------------------------------- #

HOLDINGS_HEADER_MAP = {
    "code": ("代號", "代碼", "股票代號", "證券代號", "ticker", "code", "symbol"),
    "name": ("名稱", "股票名稱", "證券名稱", "個股", "name"),
    "weight": ("權重", "比例", "比重", "淨值比", "占比", "佔比", "weight", "pct"),
    "shares": ("股數", "持股數", "shares"),
    "group": ("族群", "產業", "類別", "industry", "sector", "group"),
}


def load_holdings_overrides(folder: Path, log: Log) -> dict[str, list[dict]]:
    """Load operator-supplied holdings files: <folder>/holdings_<CODE>.csv|json.

    主動式 ETF must publish full daily holdings, but each 投信 publishes on its
    own site in its own shape.  Rather than guess at twenty scrapers that cannot
    be verified, this engine reads whatever the operator has landed (via VDF or
    by hand) and leaves the field PENDING when nothing is there.
    """
    out: dict[str, list[dict]] = {}
    if not folder or not folder.exists():
        return out
    for path in sorted(folder.iterdir()):
        m = re.match(r"^holdings_([0-9A-Za-z]+)\.(csv|json)$", path.name, re.I)
        if not m:
            continue
        code = m.group(1).upper()
        try:
            rows = (_read_holdings_json(path) if path.suffix.lower() == ".json"
                    else _read_holdings_csv(path))
        except Exception as exc:                          # noqa: BLE001
            log.warn("持股檔解析失敗 %s：%s" % (path.name, exc))
            continue
        if rows:
            out[code] = rows
            log.ok("持股覆蓋載入 %s：%d 檔成分股" % (code, len(rows)))
    return out


def _map_header(field: str) -> str | None:
    f = norm_text(field).lower()
    for canon, keys in HOLDINGS_HEADER_MAP.items():
        for k in keys:
            if k.lower() in f:
                return canon
    return None


def _normalise_holding_rows(raw_rows: list[dict]) -> list[dict]:
    out = []
    for r in raw_rows:
        rec = {}
        for k, v in r.items():
            canon = _map_header(k)
            if canon and canon not in rec:
                rec[canon] = v
        code = norm_text(rec.get("code", ""))
        code = re.sub(r"\.(TW|TWO)$", "", code, flags=re.I)
        weight = to_float(rec.get("weight"))
        if not code or weight is None:
            continue
        out.append({
            "code": code,
            "name": norm_text(rec.get("name", "")) or code,
            "weight": weight,
            "group": norm_text(rec.get("group", "")) or "",
        })
    out.sort(key=lambda x: -x["weight"])
    return out


def _read_holdings_csv(path: Path) -> list[dict]:
    text = decode_text(path.read_bytes())
    reader = csv.DictReader(io.StringIO(text))
    return _normalise_holding_rows([dict(r) for r in reader])


def _read_holdings_json(path: Path) -> list[dict]:
    doc = json.loads(decode_text(path.read_bytes()))
    rows = doc if isinstance(doc, list) else (doc.get("holdings") or doc.get("data") or [])
    return _normalise_holding_rows([r for r in rows if isinstance(r, dict)])


def aggregate_holdings(codes: list[str], holdings: dict[str, list[dict]],
                       quotes: dict[str, dict]) -> list[dict]:
    """Average constituent weight across the selected ETFs, joined to live quotes."""
    agg: dict[str, dict] = {}
    n = len([c for c in codes if holdings.get(c)])
    if not n:
        return []
    for code in codes:
        for h in holdings.get(code, []):
            a = agg.setdefault(h["code"], {"code": h["code"], "name": h["name"],
                                           "group": h["group"], "wsum": 0.0, "funds": 0})
            a["wsum"] += h["weight"]
            a["funds"] += 1
            if not a["group"] and h["group"]:
                a["group"] = h["group"]
    rows = []
    for a in agg.values():
        q = quotes.get(a["code"], {})
        rows.append({
            "code": a["code"], "name": a["name"], "group": a["group"] or "—",
            "weight": round(a["wsum"] / n, 2),
            "funds": a["funds"],
            "close": q.get("close"),
            "day_pct": q.get("day_pct"),
            "volume": q.get("volume"),
        })
    rows.sort(key=lambda r: -r["weight"])
    return rows


# --------------------------------------------------------------------------- #
# 10.  PIPELINE
# --------------------------------------------------------------------------- #

def quote_index(src: Sources, log: Log) -> dict[str, dict]:
    """Whole-market close/day%/volume keyed by code, for the holdings join."""
    idx = {}
    try:
        for r in src.stock_day_all():
            code = norm_text(r.get("Code"))
            close = to_float(r.get("ClosingPrice"))
            if not code or close is None:
                continue
            change = to_float(r.get("Change"))
            prev = close - change if change is not None else None
            idx[code] = {
                "close": close,
                "day_pct": (round(change / prev * 100, 2)
                            if (change is not None and prev not in (None, 0)) else None),
                "volume": (to_int(r.get("TradeVolume")) or 0) // 1000,
                "name": norm_text(r.get("Name")),
            }
        log.ok("全市場報價索引：%d 檔" % len(idx))
    except Exception as exc:                              # noqa: BLE001
        log.warn("全市場報價索引失敗：%s" % exc)
    return idx


def build_dataset(src: Sources, reg: Registry, args, log: Log) -> dict:
    """Discover -> fetch -> compute.  Returns the full SSOT payload."""
    run_date = today_tw().isoformat()
    year = today_tw().year

    log.step("階段 1/5  探索主動式 ETF 宇宙")
    found, diag = discover_universe(src, args.suffix, log)

    log.step("階段 2/5  合併 append-only registry")
    reg_report = reg.merge(found, run_date)
    if reg_report["new"]:
        log.ok("新增 %d 檔：%s" % (len(reg_report["new"]), ", ".join(sorted(reg_report["new"]))))
    if reg_report["dormant"]:
        log.warn("轉入 DORMANT %d 檔（資料保留不刪）：%s"
                 % (len(reg_report["dormant"]), ", ".join(sorted(reg_report["dormant"]))))

    log.step("階段 3/5  淨值 / 報價")
    navs = {}
    try:
        for r in src.etf_nav():
            navs[r["code"]] = r
        log.ok("ETF 淨值：%d 檔" % len(navs))
    except Exception as exc:                              # noqa: BLE001
        diag["etf_nav"] = "FAIL %s" % exc
        log.warn("ETF 淨值來源未解析，改以收盤價為估算代理（標記 Est）：%s" % str(exc)[:80])
    quotes = quote_index(src, log)

    log.step("階段 4/5  逐檔日線與報酬矩陣（%d 檔 × %d 個月）"
             % (len(found), args.months))
    codes = sorted(found.keys())
    series_map: dict[str, list[dict]] = {}

    def _pull(code):
        return code, build_price_series(src, code, args.months, log)

    if codes:
        workers = max(1, min(args.workers, len(codes)))
        with _cf.ThreadPoolExecutor(max_workers=workers) as pool:
            for i, (code, series) in enumerate(pool.map(_pull, codes), 1):
                series_map[code] = series
                log.info("  %2d/%d  %s  %d 個交易日" % (i, len(codes), code, len(series)))

    log.step("階段 5/5  組裝 ETF 明細")
    etfs = []
    for code in codes:
        rec = found[code]
        series = series_map.get(code, [])
        met = compute_returns(series)

        nav_row = navs.get(code)
        if nav_row:
            nav = Val(round(nav_row["nav"], 2), EV_OFFICIAL, "TWSE ETF NAV")
        elif met["last_close"].ok:
            nav = Val(round(met["last_close"].value, 2), EV_ESTIMATED,
                      "收盤價代理", "淨值來源未解析，以收盤價估算")
        else:
            nav = Val(None)

        units = rec.get("units")
        if units and nav.ok:
            aum = Val(round(units * nav.value / 1e8, 1),
                      EV_DERIVED if nav.evidence == EV_OFFICIAL else EV_ESTIMATED,
                      "發行單位數 × 淨值")
        else:
            aum = Val(None, note="缺發行單位數或淨值")

        reg.add_snapshot(code, run_date, nav.value if nav.ok else None, units)

        listed = rec.get("listed", "")
        is_new = False
        if listed:
            try:
                is_new = (today_tw() - _dt.date.fromisoformat(listed)).days <= NEW_WINDOW_DAYS
            except ValueError:
                is_new = False
        if not is_new:
            entry = reg.data["entries"].get(code, {})
            is_new = entry.get("first_seen") == run_date

        etfs.append({
            "code": code,
            "name": rec.get("name", ""),
            "trust": rec["trust"],
            "pm": Val(rec.get("pm") or None, EV_OFFICIAL, "TWSE 基金基本資料") if rec.get("pm") else Val(None),
            "style": rec["style"],
            "market": rec.get("market", ""),
            "listed": listed,
            "is_new": is_new,
            "nav": nav,
            "aum": aum,
            "units": Val(units, EV_OFFICIAL, "TWSE 基金基本資料") if units else Val(None),
            "flow_ytd": reg.flow_ytd(code, year),
            "fee": Val(None, note="費用率需 SITCA 月報或公開說明書落地"),
            "dist": Val(None, note="配息頻率需 SITCA / 投信公告落地"),
            "ret": met,
            "points": len(series),
            "sources": sorted(set(rec.get("src", []))),
        })

    holdings_raw = load_holdings_overrides(args.overrides, log)
    holdings = {c: holdings_raw[c] for c in codes if c in holdings_raw}
    if not holdings:
        log.warn("尚無持股明細檔（overrides/holdings_<代碼>.csv）→ 總持股頁標記 PENDING")

    dataset = {
        "meta": {
            "engine": __engine__,
            "version": __version__,
            "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "run_date": run_date,
            "data_date": max([e["ret"]["last_date"] for e in etfs if e["ret"]["last_date"]] or [""]),
            "suffix": args.suffix,
            "months": args.months,
            "count": len(etfs),
            "count_new": sum(1 for e in etfs if e["is_new"]),
            "registry_total": reg_report["total"],
            "registry_new": reg_report["new"],
            "registry_dormant": reg_report["dormant"],
            "http": dict(src.http.stats),
        },
        "diagnostics": diag,
        "etfs": etfs,
        "holdings": holdings,
        "quotes": quotes,
        "dormant": [
            {"code": c, "name": e.get("name", ""), "first_seen": e.get("first_seen", ""),
             "last_seen": e.get("last_seen", "")}
            for c, e in sorted(reg.data["entries"].items())
            if e.get("status") == "DORMANT"
        ],
    }
    return dataset


# --------------------------------------------------------------------------- #
# 11.  HTML RENDER  (Visual Lock, self-contained, no external assets)
# --------------------------------------------------------------------------- #

ACTION_STAGES = [
    ("一", "破冰進場", "從無到有", "var(--blue)", [
        ("首度佈局", "第一次買進這家公司（建立樁腳）。"),
        ("分批建倉", "因為資金龐大，拆成好幾天慢慢買，避免把股價買飛。")]),
    ("二", "乘勝追擊", "由小變大", "var(--co)", [
        ("順勢加碼", "股價上漲證明看對了，繼續加買。"),
        ("強勢重壓", "財報超乎預期，不計成本掠奪式買進。"),
        ("逢低承接", "看好中長線，趁股價稍微回檔時多撿一點。")]),
    ("三", "動態平衡", "持股比重", "var(--teal)", [
        ("超額配置", "買得比大盤指數規定的比例還多（投下強烈信任票）。"),
        ("基準配置", "跟大盤規定的比例一模一樣（不求打敗大盤，只求不落後）。"),
        ("欠額配置", "買得比大盤規定的比例還少（相對看壞）。")]),
    ("四", "高檔防禦", "由大變小", "var(--am)", [
        ("逢高減碼", "股價短線衝太快了，先賣掉一部分。"),
        ("獲利調節", "賺夠了，把本金抽回一部分，留利潤在裡面滾。"),
        ("降險減持", "該個股漲太多導致佔基金總權重過高，觸發法規上限，被迫賣出。")]),
    ("五", "決絕離場", "從有到無", "var(--down)", [
        ("獲利清倉", "題材走完了，一股不留，全數賣光。"),
        ("停損砍倉", "基本面看錯了，跌破經理人防線，不計代價認賠殺出。")]),
]

FIELD_MAP = [
    ("ETF 代碼 / 名稱", "TWSE 基金基本資料 + ISIN + 全市場行情", "後綴 A 自動篩選", "V"),
    ("經理人", "TWSE 基金基本資料彙總表", "官方欄位 基金經理人", "V"),
    ("風格 / 投信", "由官方基金名稱規則推導", "關鍵字對照表", "Der"),
    ("上市日期 / NEW", "TWSE 基金基本資料 + ISIN", "%d 日內掛牌標 NEW" % NEW_WINDOW_DAYS, "V"),
    ("報酬 1D~240D / YTD", "TWSE 個股日成交（逐月串接）", "close[t]/close[t-n]-1（價格報酬）", "V"),
    ("淨值 NAV", "TWSE ETF 淨值；未解析時以收盤價估算", "缺值標 Est 不假造", "V/Est"),
    ("規模 AUM", "發行單位數 × 淨值", "官方單位數 × NAV", "Der"),
    ("YTD 資金流", "本引擎自建單位數快照序列", "Σ Δ單位數 × NAV", "Der"),
    ("費用率 / 配息", "SITCA 月報 / 公開說明書", "尚未落地 → 標 P", "P"),
    ("持股 / 權重", "各投信每日完整持股揭露", "overrides/holdings_<代碼>.csv", "P"),
]


def esc(s) -> str:
    import html as _h
    return _h.escape("" if s is None else str(s), quote=True)


def fmt_pct(val: Val, digits: int = 1) -> str:
    if not val.ok:
        return "—"
    v = val.value
    return ("+" if v >= 0 else "") + ("%%.%df%%%%" % digits) % v


def fmt_num(val: Val, digits: int = 1) -> str:
    if not val.ok:
        return "—"
    if digits == 0:
        return "{:,}".format(int(round(val.value)))
    return "{:,.{d}f}".format(val.value, d=digits)


def sign_css(val: Val) -> str:
    if not val.ok:
        return "color:var(--mut2);"
    return "color:var(--up);" if val.value >= 0 else "color:var(--down);"


def ev_badge(val: Val) -> str:
    """Small evidence chip so a reader can always see where a number came from."""
    colors = {EV_OFFICIAL: "var(--gn)", EV_MEDIA: "var(--blue)", EV_DERIVED: "var(--teal)",
              EV_ESTIMATED: "var(--am)", EV_PENDING: "var(--mut2)"}
    tip = EVIDENCE_LABEL.get(val.evidence, val.evidence)
    if val.note:
        tip += " · " + val.note
    return ('<span class="ev" style="background:%s" title="%s">%s</span>'
            % (colors.get(val.evidence, "var(--mut2)"), esc(tip), esc(val.evidence)))


def heat_css(v, col_max) -> str:
    if v is None or not col_max:
        return ""
    t = min(1.0, abs(v) / col_max)
    a = 0.06 + t * 0.30
    rgb = "192,88,78" if v >= 0 else "79,138,91"
    return "background:rgba(%s,%.3f);" % (rgb, a)


def render_html(ds: dict, log: Log) -> str:
    meta, etfs = ds["meta"], ds["etfs"]

    # ---- KPI cards ------------------------------------------------------- #
    aums = [e["aum"].value for e in etfs if e["aum"].ok]
    sinces = [e["ret"]["since"].value for e in etfs if e["ret"]["since"].ok]
    best = max((e for e in etfs if e["ret"]["since"].ok),
               key=lambda e: e["ret"]["since"].value, default=None)
    cards = [
        ("主動式 ETF 數", str(meta["count"]),
         "後綴 %s · 含 %d 檔 NEW" % (meta["suffix"], meta["count_new"]), "var(--co)"),
        ("總規模", ("$%s億" % "{:,.0f}".format(sum(aums))) if aums else "—",
         "AUM · %d/%d 檔有值" % (len(aums), meta["count"]), "var(--blue)"),
        ("平均上市來", ("%+.1f%%" % (sum(sinces) / len(sinces))) if sinces else "—",
         "since listing · 價格報酬", "var(--up)"),
        ("最佳", ("%+.1f%%" % best["ret"]["since"].value) if best else "—",
         ("%s %s" % (best["code"], best["style"].value or "")) if best else "資料不足", "var(--gn)"),
        ("資料交易日", meta["data_date"] or "—",
         "來源 TWSE 官方", "var(--am)"),
    ]
    card_html = "".join(
        '<div class="card"><div class="cl">%s</div><div class="cv" style="color:%s">%s</div>'
        '<div class="cs">%s</div></div>' % (esc(l), c, esc(v), esc(s))
        for l, v, s, c in cards)

    # ---- performance matrix ---------------------------------------------- #
    col_max = []
    for n in HORIZONS:
        vals = [abs(e["ret"]["horizons"][n].value) for e in etfs if e["ret"]["horizons"][n].ok]
        col_max.append(max(vals) if vals else 0)
    ytd_vals = [abs(e["ret"]["ytd"].value) for e in etfs if e["ret"]["ytd"].ok]
    col_max.append(max(ytd_vals) if ytd_vals else 0)

    def _sort_key(e):
        r = e["ret"]["ytd"]
        s = e["ret"]["since"]
        return -(r.value if r.ok else (s.value if s.ok else -9e9))

    perf_rows = []
    for i, e in enumerate(sorted(etfs, key=_sort_key), 1):
        cells = ""
        for j, n in enumerate(HORIZONS):
            v = e["ret"]["horizons"][n]
            cells += ('<td class="num" style="%s%s">%s</td>'
                      % (sign_css(v), heat_css(v.value, col_max[j]), fmt_pct(v)))
        ytd = e["ret"]["ytd"]
        cells += ('<td class="num" style="%s%sfont-weight:700;">%s</td>'
                  % (sign_css(ytd), heat_css(ytd.value, col_max[-1]), fmt_pct(ytd)))
        perf_rows.append(
            '<tr style="background:%s">'
            '<td class="num" style="%s">%d</td>'
            '<td class="mono">%s%s</td><td>%s</td>'
            '<td><span class="pill" style="background:%s">%s</span></td>'
            '<td>%s</td>%s'
            '<td class="num">%s</td><td class="num" style="%s">%s %s</td></tr>'
            % ("#f6f4ef" if i % 2 else "var(--paper)",
               "color:var(--co);font-weight:800;" if i <= 3 else "color:var(--mut2);", i,
               '<span class="new">NEW</span>' if e["is_new"] else "", esc(e["code"]),
               esc(e["name"]),
               STYLE_CSS.get(e["style"].value, "var(--mut2)"), esc(e["style"].value or "—"),
               esc(e["pm"].value or "—"), cells,
               fmt_num(e["aum"], 0),
               sign_css(e["flow_ytd"]), fmt_num(e["flow_ytd"], 1),
               ev_badge(e["flow_ytd"])))

    perf_head = "".join("<th>%dD</th>" % n for n in HORIZONS)

    # ---- fund list -------------------------------------------------------- #
    list_rows = []
    for i, e in enumerate(sorted(etfs, key=lambda x: -(x["aum"].value or -1)), 1):
        list_rows.append(
            '<tr data-code="%s" style="background:%s">'
            '<td class="pick"><span class="mark">\u2610</span></td>'
            '<td class="mono">%s%s</td><td>%s</td><td>%s</td><td>%s %s</td>'
            '<td><span class="pill" style="background:%s">%s</span></td>'
            '<td class="num">%s %s</td><td class="num">%s %s</td>'
            '<td class="num" style="%s">%s</td><td class="num">%s %s</td>'
            '<td class="num" style="%s">%s</td><td>%s %s</td></tr>'
            % (esc(e["code"]), "#f6f4ef" if i % 2 else "var(--paper)",
               '<span class="new">NEW</span>' if e["is_new"] else "", esc(e["code"]),
               esc(e["name"]),
               esc(e["trust"].value or "—"),
               esc(e["pm"].value or "—"), ev_badge(e["pm"]),
               STYLE_CSS.get(e["style"].value, "var(--mut2)"), esc(e["style"].value or "—"),
               fmt_num(e["aum"], 0), ev_badge(e["aum"]),
               fmt_num(e["nav"], 2), ev_badge(e["nav"]),
               sign_css(e["flow_ytd"]), fmt_num(e["flow_ytd"], 1),
               "—", ev_badge(e["fee"]),
               sign_css(e["ret"]["since"]), fmt_pct(e["ret"]["since"]),
               "—", ev_badge(e["dist"])))

    # ---- holdings --------------------------------------------------------- #
    have_holdings = sorted(ds["holdings"].keys())
    agg = aggregate_holdings(have_holdings, ds["holdings"], ds["quotes"])
    max_w = agg[0]["weight"] if agg else 1
    hold_rows = []
    for i, h in enumerate(agg[:80], 1):
        day = Val(h["day_pct"], EV_OFFICIAL) if h["day_pct"] is not None else Val(None)
        close = Val(h["close"], EV_OFFICIAL) if h["close"] is not None else Val(None)
        vol = Val(h["volume"], EV_OFFICIAL) if h["volume"] is not None else Val(None)
        hold_rows.append(
            '<tr style="background:%s"><td class="num">%d</td>'
            '<td>%s <span class="mono dim">%s.TW</span></td><td>%s</td>'
            '<td class="num">%.2f%%</td>'
            '<td><div class="bar"><div style="width:%.1f%%"></div></div></td>'
            '<td class="num">%d</td><td class="num">%s</td><td class="num">%s</td>'
            '<td class="num" style="%s">%s</td></tr>'
            % ("#f6f4ef" if i % 2 else "var(--paper)", i,
               esc(h["name"]), esc(h["code"]), esc(h["group"]),
               h["weight"], min(100.0, h["weight"] / max_w * 100) if max_w else 0,
               h["funds"], fmt_num(close, 2), fmt_num(vol, 0),
               sign_css(day), fmt_pct(day, 2)))
    if not hold_rows:
        hold_rows = ['<tr><td colspan="9" class="empty">尚無持股明細。主動式 ETF 依法每日'
                     '公布完整持股，請將各投信揭露檔落地為 '
                     '<span class="mono">overrides/holdings_&lt;代碼&gt;.csv</span>'
                     '（欄位：代號,名稱,權重[,族群]），本引擎會自動聚合。'
                     '在此之前本頁不會顯示任何假造權重。</td></tr>']

    # ---- data request tab ------------------------------------------------- #
    diag = ds["diagnostics"]
    src_cards = []
    for label, key, scope in [
        ("TWSE 基金基本資料", "fund_master", "代碼 / 名稱 / 經理人 / 上市日 / 發行單位數"),
        ("TWSE 全市場日成交", "stock_day_all", "當日 OHLCV · 全市場報價索引"),
        ("TWSE ISIN 上市", "isin_twse", "證券主檔 · 掛牌前即可見"),
        ("TWSE ISIN 上櫃", "isin_tpex", "上櫃證券主檔"),
        ("TPEx 上櫃行情", "tpex", "上櫃 ETF 收盤"),
        ("TWSE ETF 淨值", "etf_nav", "每受益權單位淨值"),
    ]:
        st = diag.get(key, "") or "OK"
        good = st.startswith("OK")
        src_cards.append(
            '<div class="src"><div class="sh"><span>%s</span><span class="dot" '
            'style="background:%s"></span></div><div class="ss">%s</div>'
            '<div class="st" style="color:%s">%s</div></div>'
            % (esc(label), "var(--gn)" if good else "var(--co)", esc(scope),
               "var(--gn)" if good else "var(--co)", esc(st[:90] if st else "OK")))

    fieldmap_rows = "".join(
        '<tr style="background:%s"><td>%s</td><td>%s</td><td class="dim">%s</td>'
        '<td class="mono">%s</td></tr>'
        % ("#f6f4ef" if i % 2 else "var(--paper)", esc(f), esc(s), esc(a), esc(ev))
        for i, (f, s, a, ev) in enumerate(FIELD_MAP))

    req_json = json.dumps({
        "request": "tw_active_etf_matrix",
        "engine": __engine__, "version": __version__,
        "asof": meta["data_date"], "generated": meta["generated_at"],
        "universe": {"type": "active_etf", "suffix": meta["suffix"],
                     "discovery": ["twse_fund_master", "twse_stock_day_all",
                                   "twse_isin_2", "twse_isin_4", "tpex_daily"],
                     "hardcoded": False},
        "tickers": [e["code"] for e in etfs],
        "fields": ["name", "pm", "trust", "style", "listed", "nav", "aum", "units",
                   "flow_ytd", "ret:1D,5D,10D,20D,60D,120D,240D,YTD,SINCE",
                   "holdings:weight", "price_adj", "volume"],
        "pending": ["expense_ratio", "distribution", "holdings", "target_price"],
        "evidence_policy": {"V": "官方", "Der": "規則推導", "Est": "估算(已標示)",
                            "P": "待補(顯示 —)", "Syn": "禁止產生"},
        "governance": "append-only registry; no code ever deleted",
    }, ensure_ascii=False, indent=2)

    # ---- action lifecycle tab -------------------------------------------- #
    act_html = ""
    for num, stage, sub, color, actions in ACTION_STAGES:
        items = "".join('<div class="act"><div class="an">%s</div><div class="am">%s</div></div>'
                        % (esc(a), esc(m)) for a, m in actions)
        act_html += ('<div class="stage"><div class="sthead" style="background:%s">'
                     '<div class="stn">%s</div><div class="stt">%s</div>'
                     '<div class="sts">%s</div></div><div class="stbody">%s</div></div>'
                     % (color, esc(num), esc(stage), esc(sub), items))

    # ---- registry / dormant ---------------------------------------------- #
    dormant_html = ""
    if ds["dormant"]:
        rows = "".join('<tr><td class="mono">%s</td><td>%s</td><td class="dim">%s</td>'
                       '<td class="dim">%s</td></tr>'
                       % (esc(d["code"]), esc(d["name"]), esc(d["first_seen"]), esc(d["last_seen"]))
                       for d in ds["dormant"])
        dormant_html = ('<div class="note"><b>DORMANT（只增不減，資料保留）</b>'
                        '<table class="mini"><thead><tr><th>代碼</th><th>名稱</th>'
                        '<th>首見</th><th>末見</th></tr></thead><tbody>%s</tbody></table></div>' % rows)

    # ---- run log ---------------------------------------------------------- #
    log_rows = "".join(
        '<div class="lg %s"><span class="lt">%6.1fs</span><span class="ll">%s</span>'
        '<span class="lm">%s</span></div>' % (lv.lower(), t, esc(lv), esc(msg))
        for lv, msg, t in log.lines)

    pending_n = sum(1 for e in etfs for f in ("nav", "aum", "flow_ytd", "fee", "dist")
                    if not e[f].ok)
    verify_tag = ("\u2713 官方直取 · 資料交易日 %s · %d 檔 · %d 個待補欄位"
                  % (meta["data_date"] or "—", meta["count"], pending_n))

    return HTML_SHELL.substitute({
        "title": "主動式台股 ETF 戰情台 · Active Taiwan Stock ETF Console",
        "reson": RESON,
        "generated": esc(meta["generated_at"]),
        "data_date": esc(meta["data_date"] or "—"),
        "verify_tag": esc(verify_tag),
        "engine": esc("%s %s" % (__engine__, __version__)),
        "cards": card_html,
        "perf_head": perf_head,
        "perf_rows": "".join(perf_rows) or '<tr><td colspan="16" class="empty">無資料</td></tr>',
        "list_rows": "".join(list_rows) or '<tr><td colspan="12" class="empty">無資料</td></tr>',
        "hold_rows": "".join(hold_rows),
        "hold_note": ("聚合 %d 檔基金持股" % len(have_holdings)) if have_holdings else "尚無持股來源",
        "src_cards": "".join(src_cards),
        "fieldmap_rows": fieldmap_rows,
        "req_json": esc(req_json),
        "act_html": act_html,
        "dormant": dormant_html,
        "log_rows": log_rows,
        "net": meta["http"].get("net", 0),
        "cache": meta["http"].get("cache", 0),
        "fail": meta["http"].get("fail", 0),
        "count": meta["count"],
        "count_new": meta["count_new"],
        "reg_total": meta["registry_total"],
        "months": meta["months"],
    })


# --------------------------------------------------------------------------- #
# 12.  HTML SHELL
# --------------------------------------------------------------------------- #

import string as _string  # noqa: E402  (kept next to the template it serves)

HTML_SHELL = _string.Template(r"""<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<style>
:root{--bg:#f5f4f0;--paper:#fff;--paper2:#fafaf8;--ink:#1e1d1a;--ink2:#33403f;
--mut:#6b6860;--mut2:#9c9890;--line:#dbd9d3;--soft:#ecebe6;--accent:#439a9a;
--blue:#4c78a8;--teal:#439a9a;--up:#c96b5a;--down:#5a9e6f;--am:#c4943a;
--co:#c96b5a;--vi:#7a6daa;--gn:#5a9e6f;--ro:#b05580;--reson:${reson};}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);}
body{color:var(--ink2);font-family:'DM Sans','Noto Sans TC','Microsoft JhengHei',system-ui,sans-serif;
font-size:11px;line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1340px;margin:0 auto;padding:0 22px 46px;}
.topbar{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);opacity:.92;z-index:50;}
header{position:relative;padding:18px 0 9px;margin-bottom:12px;border-bottom:2px solid var(--ink);}
.eyebrow{font:700 10px 'DM Mono',ui-monospace,monospace;letter-spacing:2.2px;color:var(--mut);
text-transform:uppercase;margin-bottom:6px;}
h1{font:800 18px/1.2 'Syne',sans-serif;color:var(--ink);}
h1 span{color:var(--up);}
.sub{margin-top:5px;font:400 10.5px/1.5 inherit;color:var(--mut);max-width:720px;}
.sub b{color:var(--ink2);}
.hmeta{position:absolute;top:4px;right:0;display:flex;flex-direction:column;align-items:flex-end;
gap:3px;text-align:right;max-width:340px;}
.hmeta span{font:500 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut);}
.hmeta .live{display:inline-flex;align-items:center;gap:5px;font-weight:600;font-size:9px;color:var(--ink2);}
.hmeta .live i{width:7px;height:7px;border-radius:50%;background:var(--gn);display:inline-block;}
.hmeta .tag{font-weight:700;font-size:8px;color:#fff;background:var(--gn);border-radius:3px;padding:2px 8px;}
.lockbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:#1e1d1a;border-radius:3px;
padding:6px 13px;margin-bottom:12px;}
.lockbar .t{font:700 8.5px 'DM Mono',ui-monospace,monospace;letter-spacing:.8px;color:#7fd0a0;text-transform:uppercase;}
.lockbar .sw{display:inline-flex;align-items:center;gap:4px;font:500 8px 'DM Mono',ui-monospace,monospace;color:#cfcabf;}
.lockbar .sw i{width:11px;height:11px;border-radius:2px;display:inline-block;}
.lockbar .m{font:500 8px 'DM Mono',ui-monospace,monospace;color:#8a948f;}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px;}
.card{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:9px 11px;}
.cl{font:600 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut);letter-spacing:.6px;text-transform:uppercase;}
.cv{font:800 19px/1.15 'Syne',sans-serif;margin:3px 0 1px;}
.cs{font-size:9px;color:var(--mut2);}
.tabs{display:flex;gap:3px;margin-bottom:-1px;}
.tab{font:700 10px 'DM Mono',ui-monospace,monospace;padding:7px 14px;border:1px solid var(--line);
border-bottom:none;border-radius:3px 3px 0 0;background:var(--soft);color:var(--mut);cursor:pointer;
user-select:none;letter-spacing:.5px;}
.tab.on{background:var(--bg);color:var(--ink);border-color:var(--ink);box-shadow:0 -2px 0 var(--accent) inset;}
.panel{display:none;border:1px solid var(--line);background:var(--paper);border-radius:0 3px 3px 3px;padding:12px;}
.panel.on{display:block;}
.ptitle{font:700 12px 'Syne',sans-serif;color:var(--ink);margin-bottom:8px;display:flex;
align-items:center;gap:8px;flex-wrap:wrap;}
.ptitle em{font:500 9px 'DM Mono',ui-monospace,monospace;color:var(--mut2);font-style:normal;}
.scroll{overflow-x:auto;}
table{border-collapse:collapse;width:100%;font-size:10px;}
th{background:var(--ink);color:#fff;font:700 9px 'DM Mono',ui-monospace,monospace;padding:6px 7px;
text-align:left;white-space:nowrap;position:sticky;top:0;z-index:2;letter-spacing:.4px;}
td{padding:5px 7px;border-bottom:1px solid var(--line);white-space:nowrap;}
td.num{text-align:right;font-family:'DM Mono',ui-monospace,monospace;}
td.mono,.mono{font-family:'DM Mono',ui-monospace,monospace;}
td.empty{text-align:center;color:var(--mut);padding:22px 12px;white-space:normal;line-height:1.7;}
.dim{color:var(--mut2);}
.pill{display:inline-block;color:#fff;border-radius:2px;padding:1px 6px;font-size:9px;font-weight:600;}
.new{display:inline-block;background:var(--co);color:#fff;font:700 7.5px 'DM Mono',ui-monospace,monospace;
border-radius:2px;padding:1px 4px;margin-right:4px;vertical-align:1px;}
.ev{display:inline-block;color:#fff;border-radius:2px;padding:0 4px;font:700 7.5px 'DM Mono',ui-monospace,monospace;
vertical-align:1px;opacity:.85;cursor:help;}
.bar{width:78px;height:7px;background:var(--soft);border-radius:2px;overflow:hidden;}
.bar div{height:100%;background:var(--teal);}
tr.sel{box-shadow:inset 3px 0 0 var(--co);background:rgba(201,107,90,0.10) !important;}
.pick{cursor:pointer;user-select:none;text-align:center;}
.tools{display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap;}
.btn{font:700 9px 'DM Mono',ui-monospace,monospace;background:var(--soft);border:1px solid var(--line);
border-radius:2px;padding:4px 10px;cursor:pointer;color:var(--ink2);}
.btn:hover{background:var(--paper2);border-color:var(--ink2);}
.srcs{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px;}
.src{border:1px solid var(--line);border-radius:3px;padding:8px 10px;background:var(--paper2);}
.sh{display:flex;justify-content:space-between;align-items:center;font:700 10px 'DM Mono',ui-monospace,monospace;color:var(--ink);}
.sh .dot{width:8px;height:8px;border-radius:50%;display:inline-block;}
.ss{font-size:9px;color:var(--mut);margin:3px 0;}
.st{font:600 8.5px 'DM Mono',ui-monospace,monospace;word-break:break-all;}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
pre{background:#1e1d1a;color:#cfcabf;border-radius:3px;padding:10px;font:500 9px/1.55 'DM Mono',ui-monospace,monospace;
overflow:auto;max-height:420px;}
.stage{border:1px solid var(--line);border-radius:3px;overflow:hidden;margin-bottom:6px;}
.sthead{display:flex;align-items:center;gap:10px;padding:7px 11px;color:#fff;cursor:pointer;}
.stn{font:800 13px 'Syne',sans-serif;width:18px;}
.stt{font:700 12px 'Syne',sans-serif;}
.sts{font:500 9px 'DM Mono',ui-monospace,monospace;opacity:.85;margin-left:auto;}
.stbody{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:9px 11px;background:var(--paper2);}
.act{border-left:2px solid var(--line);padding-left:8px;}
.an{font-weight:700;color:var(--ink);font-size:10.5px;}
.am{font-size:9px;color:var(--mut);line-height:1.55;}
.note{margin-top:10px;border:1px solid var(--line);border-left:3px solid var(--am);border-radius:3px;
padding:9px 11px;background:var(--paper2);font-size:9.5px;color:var(--mut);line-height:1.7;}
.note b{color:var(--ink2);}
table.mini{margin-top:6px;font-size:9px;}
table.mini th{background:var(--soft);color:var(--ink2);position:static;}
.legend{display:flex;gap:12px;flex-wrap:wrap;margin:9px 0 0;font-size:9px;color:var(--mut);}
.legend span i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px;vertical-align:-1px;}
.runlog{max-height:280px;overflow:auto;border:1px solid var(--line);border-radius:3px;background:#1e1d1a;padding:8px;}
.lg{font:500 9px/1.6 'DM Mono',ui-monospace,monospace;color:#cfcabf;display:flex;gap:8px;}
.lg .lt{color:#6b6860;width:48px;text-align:right;flex:none;}
.lg .ll{width:34px;flex:none;}
.lg.ok .ll{color:#7fd0a0;} .lg.warn .ll{color:#c4943a;} .lg.err .ll{color:#c96b5a;}
.lg.step .ll{color:#4c78a8;} .lg.info .ll{color:#6b6860;}
footer{margin-top:18px;padding-top:9px;border-top:1px solid var(--line);display:flex;
justify-content:space-between;font:600 8.5px 'DM Mono',ui-monospace,monospace;color:var(--mut2);flex-wrap:wrap;gap:8px;}
@media print{@page{size:A4 landscape;margin:8mm}body{background:#fff}
.tab,.btn{display:none}.panel{display:block !important;page-break-before:always}
th{position:static}}
@media(max-width:1100px){.cards{grid-template-columns:repeat(2,1fr)}.srcs,.two,.stbody{grid-template-columns:1fr}}
</style></head>
<body>
<div class="topbar"></div>
<div class="wrap">
<header>
  <div class="eyebrow">VERITAS INTELLIGENCE ANALYTICS · ACTIVE TAIWAN STOCK ETF CONSOLE</div>
  <h1>主動式台股 <span>ETF 戰情台</span> · Active Taiwan Stock ETF Console</h1>
  <p class="sub">代碼後綴 <b>A</b> 的主動式 ETF，清單由 TWSE 基金基本資料 / ISIN 主檔 / 全市場行情
  <b>自動探索</b>，無任何硬編碼名單；新核准掛牌者下次執行自動出現並標 <b>NEW</b>。
  數值一律附證據標籤，查無來源顯示 <b>—</b>，不以合成數字填充。紅漲綠跌。</p>
  <div class="hmeta">
    <span class="live"><i></i>OFFICIAL FEED</span>
    <span>產生 ${generated}</span>
    <span>資料交易日 ${data_date}</span>
    <span>來源 TWSE OpenAPI / ISIN / TPEx</span>
    <span class="tag">${verify_tag}</span>
  </div>
</header>

<div class="lockbar">
  <span class="t">&#128274; VISUAL LOCK · 全格式鎖定</span>
  <span class="sw">色票
    <i style="background:#4c78a8"></i><i style="background:#439a9a"></i><i style="background:#9c9890"></i>
    <i style="background:#c96b5a"></i><i style="background:#5a9e6f"></i>
    <i style="background:#f5f4f0;border:1px solid #555"></i></span>
  <span class="m">字體 Syne / DM Sans / DM Mono</span>
  <span class="m">引擎 ${engine}</span>
  <span class="m">HTTP net ${net} · cache ${cache} · fail ${fail}</span>
</div>

<div class="cards">${cards}</div>

<div class="tabs">
  <div class="tab on" data-p="perf">績效矩陣</div>
  <div class="tab" data-p="list">基金清單</div>
  <div class="tab" data-p="hold">總持股</div>
  <div class="tab" data-p="req">資料請求</div>
  <div class="tab" data-p="act">動作分類</div>
  <div class="tab" data-p="log">執行日誌</div>
</div>

<div class="panel on" id="p-perf">
  <div class="ptitle">績效矩陣 <em>多期間價格報酬 · 熱力色階 · 依 YTD 排序</em></div>
  <div class="scroll"><table>
    <thead><tr><th>#</th><th>代碼</th><th>ETF 名稱</th><th>風格</th><th>經理人</th>
    ${perf_head}<th>YTD</th><th>規模(億)</th><th>YTD流(億)</th></tr></thead>
    <tbody>${perf_rows}</tbody>
  </table></div>
  <div class="legend">
    <span><i style="background:var(--gn)"></i>V 官方確認</span>
    <span><i style="background:var(--teal)"></i>Der 規則推導</span>
    <span><i style="background:var(--am)"></i>Est 估算(已標示)</span>
    <span><i style="background:var(--mut2)"></i>P 待補(顯示 —)</span>
    <span>報酬為 <b>價格報酬</b>（TWSE 收盤價未還原配息），配息型 ETF 之含息總報酬更高。</span>
  </div>
</div>

<div class="panel" id="p-list">
  <div class="tools">
    <span class="btn" id="selAll">全選</span>
    <span class="btn" id="selNone">全不選</span>
    <span class="dim">已選 <b id="nSel">0</b> 檔 → 供總持股頁聚合</span>
  </div>
  <div class="scroll"><table>
    <thead><tr><th>勾</th><th>代碼</th><th>ETF 名稱</th><th>投信</th><th>經理人</th><th>風格</th>
    <th>規模(億)</th><th>淨值</th><th>資金流(億)</th><th>費用率</th><th>上市來%</th><th>配息</th></tr></thead>
    <tbody id="listBody">${list_rows}</tbody>
  </table></div>
  ${dormant}
</div>

<div class="panel" id="p-hold">
  <div class="ptitle">總持股聚合矩陣 <em>${hold_note} · 跨基金按 ticker 平均權重</em></div>
  <div class="scroll"><table>
    <thead><tr><th>#</th><th>個股</th><th>族群</th><th>平均權重</th><th>權重佔比</th>
    <th>命中基金</th><th>現價</th><th>成交量(張)</th><th>日%</th></tr></thead>
    <tbody>${hold_rows}</tbody>
  </table></div>
</div>

<div class="panel" id="p-req">
  <div class="ptitle">資料請求 <em>Data Request · 來源健康度與欄位對應</em></div>
  <div class="srcs">${src_cards}</div>
  <div class="two">
    <div>
      <div class="ptitle">欄位 → 來源對應 Field Map</div>
      <div class="scroll"><table>
        <thead><tr><th>欄位</th><th>來源 / API</th><th>彙整規則</th><th>證據</th></tr></thead>
        <tbody>${fieldmap_rows}</tbody>
      </table></div>
    </div>
    <div>
      <div class="ptitle">請求規格 request.json <span class="btn" id="copyReq">&#10697; 複製</span></div>
      <pre id="reqJson">${req_json}</pre>
    </div>
  </div>
  <div class="note"><b>待補欄位怎麼補：</b>費用率 / 配息頻率來自 SITCA 月報與公開說明書；
  持股明細各投信依法每日完整揭露，格式各異。把落地檔放成
  <span class="mono">overrides/holdings_&lt;代碼&gt;.csv</span>（欄位 <span class="mono">代號,名稱,權重[,族群]</span>），
  本引擎下次執行會自動讀入並聚合。在來源接上之前，這些欄位一律顯示 <b>—</b> 而非估值。</div>
</div>

<div class="panel" id="p-act">
  <div class="ptitle">經理人動作分類 <em>Manager Action Lifecycle · 五階段</em></div>
  ${act_html}
  <div class="note">五個階段依資金生命週期排序：<b>破冰進場</b>（建倉）→<b>乘勝追擊</b>（加碼）→
  <b>動態平衡</b>（配置）→<b>高檔防禦</b>（減碼）→<b>決絕離場</b>（出清）。
  接上每日持股揭露後，本引擎可由權重變化自動判定各檔當前所處階段。</div>
</div>

<div class="panel" id="p-log">
  <div class="ptitle">執行日誌 <em>${count} 檔 · 新增 ${count_new} · registry 累計 ${reg_total} · 回溯 ${months} 個月</em></div>
  <div class="runlog">${log_rows}</div>
</div>

<footer>
  <span>VERITAS INTELLIGENCE ANALYTICS</span>
  <span>${engine} · Generated ${generated} · Data ${data_date}</span>
</footer>
</div>
<script>
(function(){
  var tabs=document.querySelectorAll('.tab');
  tabs.forEach(function(t){t.addEventListener('click',function(){
    tabs.forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('on');});
    t.classList.add('on');
    var el=document.getElementById('p-'+t.dataset.p); if(el){el.classList.add('on');}
  });});

  var body=document.getElementById('listBody');
  function count(){
    var n=body?body.querySelectorAll('tr.sel').length:0;
    var el=document.getElementById('nSel'); if(el){el.textContent=n;}
  }
  if(body){
    body.querySelectorAll('tr').forEach(function(tr){
      tr.addEventListener('click',function(){
        tr.classList.toggle('sel');
        var m=tr.querySelector('.mark');
        if(m){m.textContent=tr.classList.contains('sel')?'\u2611':'\u2610';}
        count();
      });
    });
  }
  var a=document.getElementById('selAll'), b=document.getElementById('selNone');
  function setAll(on){
    if(!body){return;}
    body.querySelectorAll('tr').forEach(function(tr){
      tr.classList.toggle('sel',on);
      var m=tr.querySelector('.mark'); if(m){m.textContent=on?'\u2611':'\u2610';}
    });
    count();
  }
  if(a){a.addEventListener('click',function(e){e.stopPropagation();setAll(true);});}
  if(b){b.addEventListener('click',function(e){e.stopPropagation();setAll(false);});}

  var c=document.getElementById('copyReq');
  if(c){c.addEventListener('click',function(){
    var t=document.getElementById('reqJson');
    if(!t){return;}
    try{navigator.clipboard.writeText(t.textContent);c.textContent='\u2713 已複製';
      setTimeout(function(){c.innerHTML='&#10697; 複製';},1500);}catch(e){}
  });}

  document.querySelectorAll('.sthead').forEach(function(h){
    h.addEventListener('click',function(){
      var bd=h.nextElementSibling;
      if(bd){bd.style.display=(bd.style.display==='none')?'grid':'none';}
    });
  });
  count();
})();
</script>
</body></html>
""")


# --------------------------------------------------------------------------- #
# 13.  EXPORTS
# --------------------------------------------------------------------------- #

def _jsonable(obj):
    if isinstance(obj, Val):
        return obj.as_dict()
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def export_json(ds: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(_jsonable(ds), fh, ensure_ascii=False, indent=1)


def export_csv(ds: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = (["code", "name", "trust", "pm", "style", "market", "listed", "is_new",
             "nav", "nav_ev", "aum", "aum_ev", "units", "flow_ytd", "flow_ytd_ev",
             "last_date", "last_close"]
            + ["ret_%dD" % n for n in HORIZONS] + ["ret_ytd", "ret_since", "points"])
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for e in ds["etfs"]:
            row = [e["code"], e["name"], e["trust"].value, e["pm"].value, e["style"].value,
                   e["market"], e["listed"], int(e["is_new"]),
                   e["nav"].value, e["nav"].evidence, e["aum"].value, e["aum"].evidence,
                   e["units"].value, e["flow_ytd"].value, e["flow_ytd"].evidence,
                   e["ret"]["last_date"], e["ret"]["last_close"].value]
            row += [e["ret"]["horizons"][n].value for n in HORIZONS]
            row += [e["ret"]["ytd"].value, e["ret"]["since"].value, e["points"]]
            w.writerow(["" if v is None else v for v in row])


def write_text(path: Path, text: str) -> None:
    """UTF-8, no BOM, LF - VIA locked convention."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# --------------------------------------------------------------------------- #
# 14.  PROBE
# --------------------------------------------------------------------------- #

def run_probe(src: Sources, log: Log) -> int:
    """Reachability + shape matrix for every endpoint.  Read-only, no side effects."""
    log.banner("VIA ActiveStockETF · ENDPOINT PROBE", "read-only reachability matrix")
    checks = [
        ("TWSE 基金基本資料 t187ap47_L", lambda: len(src.fund_master())),
        ("TWSE 全市場日成交 STOCK_DAY_ALL", lambda: len(src.stock_day_all())),
        ("TWSE ISIN 上市 (strMode=2)", lambda: len(src.isin_list(2))),
        ("TWSE ISIN 上櫃 (strMode=4)", lambda: len(src.isin_list(4))),
        ("TWSE ETF 淨值", lambda: len(src.etf_nav())),
        ("TPEx 上櫃收盤", lambda: len(src.tpex_daily())),
        ("TWSE 個股日成交 STOCK_DAY(0050)", lambda: len(src.stock_day("0050", today_tw().strftime("%Y%m01")))),
    ]
    bad = 0
    for label, fn in checks:
        try:
            n = fn()
            if n:
                log.ok("%-42s  %d rows" % (label, n))
            else:
                log.warn("%-42s  0 rows" % label)
                bad += 1
        except Exception as exc:                          # noqa: BLE001
            log.err("%-42s  %s" % (label, str(exc)[:80]))
            bad += 1
    log.step("PROBE 結束：%d/%d 個端點異常" % (bad, len(checks)))
    return 0 if bad == 0 else 2


# --------------------------------------------------------------------------- #
# 15.  SELF-TEST  (offline; fixtures embedded)
# --------------------------------------------------------------------------- #

FIXTURE_ISIN = """<html><body><table>
<tr><td colspan="7">\u4e0a\u5e02\u6307\u6578\u80a1\u7968\u578b\u57fa\u91d1(ETF)</td></tr>
<tr><td>00981A\u3000\u4e3b\u52d5\u7d71\u4e00\u53f0\u80a1\u589e\u9577</td><td>TW00000981A9</td>
<td>114/05/05</td><td>\u4e0a\u5e02</td><td>ETF</td><td>CEOGEU</td><td></td></tr>
<tr><td>00403A\u3000\u4e3b\u52d5\u65b0\u6a02\u53f0\u80a1</td><td>TW00000403A1</td>
<td>115/05/12</td><td>\u4e0a\u5e02</td><td>ETF</td><td>CEOGEU</td><td></td></tr>
<tr><td>2330\u3000\u53f0\u7a4d\u96fb</td><td>TW0002330008</td><td>83/09/05</td>
<td>\u4e0a\u5e02</td><td>\u534a\u5c0e\u9ad4\u696d</td><td>ESVUFR</td><td></td></tr>
<tr><td>00679B\u3000\u5143\u5927\u7f8e\u50b520\u5e74</td><td>TW00000679B5</td><td>106/01/17</td>
<td>\u4e0a\u5e02</td><td>ETF</td><td>CEOGEU</td><td></td></tr>
</table></body></html>"""


def _selftest_cases():
    """(name, callable) pairs.  Each returns None on pass or raises AssertionError."""
    cases = []

    def case(fn):
        cases.append((fn.__name__.replace("t_", ""), fn))
        return fn

    # -- date + number parsing --------------------------------------------- #
    @case
    def t_roc_dates():
        assert roc_to_iso("1150731") == "2026-07-31", roc_to_iso("1150731")
        assert roc_to_iso("115/07/31") == "2026-07-31"
        assert roc_to_iso("114\u5e7405\u670805\u65e5") == "2025-05-05"
        assert roc_to_iso("2026-07-31") == "2026-07-31"
        assert roc_to_iso("") is None
        assert roc_to_iso("115/13/45") is None, "invalid month/day must reject"

    @case
    def t_numbers():
        assert to_float("1,234.5") == 1234.5
        assert to_float("--") is None
        assert to_float("") is None
        assert to_float("X0.00") == 0.0
        assert to_float(None) is None
        assert to_float("+3.2") == 3.2
        assert to_int("1,234") == 1234

    # -- universe filter ---------------------------------------------------- #
    @case
    def t_code_filter():
        for good in ("00981A", "00403A", "00999A", "00400A"):
            assert is_active_etf_code(good), good
        for bad in ("2330", "0050", "00679B", "00670L", "00632R", "00981", "009A01", "A0098"):
            assert not is_active_etf_code(bad), bad
        assert is_active_etf_code("00982D", "AD")
        assert not is_active_etf_code("00982D", "A")

    @case
    def t_derivations():
        assert derive_trust("\u4e3b\u52d5\u7d71\u4e00\u53f0\u80a1\u589e\u9577").value == "\u7d71\u4e00\u6295\u4fe1"
        assert derive_trust("\u672a\u77e5\u57fa\u91d1").value is None
        assert derive_style("\u4e3b\u52d5\u7d71\u4e00\u53f0\u80a1\u589e\u9577").value == "\u6210\u9577"
        assert derive_style("\u4e3b\u52d5\u5b89\u806f\u53f0\u7063\u9ad8\u606f").value == "\u9ad8\u606f"
        assert derive_style("\u4e3b\u52d5\u7fa4\u76ca\u79d1\u6280\u5275\u65b0").value == "\u79d1\u6280"
        assert derive_style("zzz").value is None
        # a derived value must never be tagged as official
        assert derive_style("\u4e3b\u52d5\u7fa4\u76ca\u79d1\u6280\u5275\u65b0").evidence == EV_DERIVED

    # -- parsers ------------------------------------------------------------ #
    @case
    def t_isin_parser():
        rows = parse_isin_table(FIXTURE_ISIN)
        codes = [r["code"] for r in rows]
        assert "00981A" in codes and "2330" in codes, codes
        act = [r for r in rows if is_active_etf_code(r["code"])]
        assert len(act) == 2, act
        r = [x for x in rows if x["code"] == "00981A"][0]
        assert r["listed"] == "2025-05-05", r
        assert "\u4e3b\u52d5" in r["name"], r

    @case
    def t_stock_day_parser():
        raw = [["115/06/17", "12,345,678", "1,000", "31.00", "31.50", "30.80", "31.20", "+0.20", "5,000"],
               ["115/06/18", "9,000,000", "900", "31.20", "31.90", "31.10", "31.80", "+0.60", "4,000"],
               ["115/06/16", "8,000,000", "800", "30.50", "31.00", "30.40", "30.90", "-0.10", "3,000"],
               ["\u5408\u8a08", "-", "-", "-", "-", "-", "--", "-", "-"]]
        rows = parse_stock_day_rows(raw)
        assert len(rows) == 3, rows
        assert [r["date"] for r in rows] == ["2026-06-16", "2026-06-17", "2026-06-18"]
        assert rows[-1]["close"] == 31.8

    @case
    def t_nav_parser():
        rows = parse_nav_rows([
            {"\u57fa\u91d1\u4ee3\u865f": "00981A", "\u6bcf\u53d7\u76ca\u6b0a\u55ae\u4f4d\u6de8\u503c": "32.45",
             "\u65e5\u671f": "1150619"},
            {"\u57fa\u91d1\u4ee3\u865f": "00982A", "\u6bcf\u53d7\u76ca\u6b0a\u55ae\u4f4d\u6de8\u503c": "--"},
        ])
        assert len(rows) == 1 and rows[0]["nav"] == 32.45 and rows[0]["date"] == "2026-06-19", rows

    # -- metrics ------------------------------------------------------------ #
    @case
    def t_returns_math():
        series = ([{"date": "2025-12-%02d" % d, "close": 100.0, "volume": 1000} for d in range(20, 32)]
                  + [{"date": "2026-01-%02d" % d, "close": 100.0 + d, "volume": 2000} for d in range(1, 29)])
        met = compute_returns(series, horizons=[1, 5, 240])
        assert met["last_close"].value == 128.0
        assert met["horizons"][1].value == round((128 / 127 - 1) * 100, 1)
        assert met["horizons"][240].value is None, "must not invent a 240D return"
        assert met["horizons"][240].evidence == EV_PENDING
        assert met["ytd"].value == 28.0, met["ytd"]
        assert met["since"].value == 28.0
        assert met["volume"].value == 2

    @case
    def t_returns_empty():
        met = compute_returns([])
        assert not met["last_close"].ok and not met["ytd"].ok
        assert met["points"] == 0

    @case
    def t_ytd_for_new_listing():
        series = [{"date": "2026-05-%02d" % d, "close": 20.0 + d, "volume": 1} for d in range(12, 29)]
        met = compute_returns(series, horizons=[1])
        assert met["ytd"].value is None, "listed this year -> no YTD base, must stay PENDING"
        assert met["since"].ok

    # -- evidence discipline ------------------------------------------------ #
    @case
    def t_val_pending_discipline():
        v = Val(None, EV_OFFICIAL, "x")
        assert v.evidence == EV_PENDING, "a None value can never carry an official tag"
        assert fmt_pct(v) == "\u2014" and fmt_num(v) == "\u2014"
        assert fmt_pct(Val(-3.25, EV_OFFICIAL), 1) == "-3.2"[:0] + "-3.2%"
        assert fmt_pct(Val(3.25, EV_OFFICIAL), 1) == "+3.2%"

    # -- registry append-only ----------------------------------------------- #
    @case
    def t_registry_append_only():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "reg.json"
            reg = Registry(p)
            r1 = reg.merge({"00981A": {"name": "A", "listed": "2025-05-05", "market": "TWSE"},
                            "00982A": {"name": "B", "listed": "", "market": "TWSE"}}, "2026-08-01")
            assert sorted(r1["new"]) == ["00981A", "00982A"]
            reg.save("2026-08-01")

            reg2 = Registry(p)
            r2 = reg2.merge({"00981A": {"name": "A", "listed": "2025-05-05", "market": "TWSE"},
                             "00983A": {"name": "C", "listed": "", "market": "TWSE"}}, "2026-08-02")
            assert r2["new"] == ["00983A"], r2
            assert r2["dormant"] == ["00982A"], r2
            assert "00982A" in reg2.data["entries"], "\u53ea\u589e\u4e0d\u6e1b: entry must survive"
            assert reg2.data["entries"]["00982A"]["status"] == "DORMANT"
            assert reg2.data["entries"]["00982A"]["name"] == "B", "history preserved"
            assert r2["total"] == 3

            r3 = reg2.merge({"00981A": {"name": "A", "listed": "2025-05-05", "market": "TWSE"},
                             "00982A": {"name": "B", "listed": "", "market": "TWSE"},
                             "00983A": {"name": "C", "listed": "", "market": "TWSE"}}, "2026-08-03")
            assert r3["returned"] == ["00982A"], r3

    @case
    def t_registry_flow():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            reg = Registry(Path(td) / "r.json")
            assert not reg.flow_ytd("00981A", 2026).ok, "no history -> PENDING, never 0"
            reg.add_snapshot("00981A", "2026-01-05", 30.0, 1_000_000_000)
            assert not reg.flow_ytd("00981A", 2026).ok, "one point is not a delta"
            reg.add_snapshot("00981A", "2026-01-06", 31.0, 1_100_000_000)
            f = reg.flow_ytd("00981A", 2026)
            assert f.ok and abs(f.value - 31.0) < 0.01, f          # 1e8 units * 31 / 1e8 = 31 億
            assert f.evidence == EV_DERIVED
            reg.add_snapshot("00981A", "2026-01-06", 31.0, 1_100_000_000)
            assert len(reg.data["snapshots"]["00981A"]) == 2, "same-day snapshot must dedupe"

    # -- holdings ----------------------------------------------------------- #
    @case
    def t_holdings_parse_and_aggregate():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "holdings_00981A.csv").write_text(
                "\u4ee3\u865f,\u540d\u7a31,\u6b0a\u91cd,\u65cf\u7fa4\n"
                "2330,\u53f0\u7a4d\u96fb,28.5,\u534a\u5c0e\u9ad4\n"
                "2317.TW,\u9d3b\u6d77,7.4,AI\u4f3a\u670d\u5668\n"
                "BAD,,,\n", encoding="utf-8")
            (d / "holdings_00982A.json").write_text(json.dumps(
                [{"code": "2330", "name": "\u53f0\u7a4d\u96fb", "weight": 20.5},
                 {"code": "2454", "name": "\u806f\u767c\u79d1", "weight": 9.2}]), encoding="utf-8")
            (d / "notes.txt").write_text("ignore me", encoding="utf-8")
            h = load_holdings_overrides(d, Log(quiet=True))
            assert set(h) == {"00981A", "00982A"}, h
            assert len(h["00981A"]) == 2, h["00981A"]
            assert h["00981A"][0]["code"] == "2330"
            assert h["00981A"][1]["code"] == "2317", "suffix .TW must be stripped"

            agg = aggregate_holdings(["00981A", "00982A"], h,
                                     {"2330": {"close": 1200.0, "day_pct": 1.2, "volume": 30000}})
            top = agg[0]
            assert top["code"] == "2330" and abs(top["weight"] - 24.5) < 1e-6, top
            assert top["funds"] == 2 and top["close"] == 1200.0
            assert [r["code"] for r in agg] == ["2330", "2454", "2317"], agg
            assert aggregate_holdings(["00999A"], h, {}) == [], "no source -> empty, not fabricated"

    # -- rendering ---------------------------------------------------------- #
    @case
    def t_render_full():
        ds = _fixture_dataset()
        html_out = render_html(ds, Log(quiet=True))
        assert "<!DOCTYPE html>" in html_out
        assert "00981A" in html_out and "00403A" in html_out
        assert html_out.count("</table>") >= 4
        assert "NEW" in html_out
        assert "\u2014" in html_out, "pending fields must render as em dash"
        assert "${" not in html_out, "unsubstituted placeholder left in output"
        assert "$title" not in html_out and "$cards" not in html_out
        badges = re.findall(r'<span class="ev"[^>]*>([^<]*)</span>', html_out)
        assert badges, "evidence badges must render"
        assert all(b in EVIDENCE_LABEL for b in badges), set(badges)
        assert "Syn" not in badges, "a synthetic evidence tag must never be emitted"
        for tab in ("p-perf", "p-list", "p-hold", "p-req", "p-act", "p-log"):
            assert 'id="%s"' % tab in html_out, tab

    @case
    def t_render_empty_universe():
        ds = _fixture_dataset(empty=True)
        html_out = render_html(ds, Log(quiet=True))
        assert "<!DOCTYPE html>" in html_out and "\u7121\u8cc7\u6599" in html_out
        assert "${" not in html_out

    @case
    def t_exports():
        import tempfile
        ds = _fixture_dataset()
        with tempfile.TemporaryDirectory() as td:
            jp, cp = Path(td) / "m.json", Path(td) / "m.csv"
            export_json(ds, jp)
            export_csv(ds, cp)
            doc = json.loads(jp.read_text(encoding="utf-8"))
            assert doc["etfs"][0]["nav"]["evidence"] in (EV_OFFICIAL, EV_ESTIMATED, EV_PENDING)
            rows = list(csv.DictReader(io.open(cp, encoding="utf-8")))
            assert len(rows) == len(ds["etfs"])
            assert rows[0]["code"] == "00981A"
            assert rows[1]["ret_240D"] == "", "missing horizon must export blank, not 0"

    @case
    def t_escaping():
        assert "&lt;script&gt;" in esc("<script>")
        assert esc(None) == ""

    @case
    def t_month_walk():
        ms = month_starts(3, _dt.date(2026, 1, 15))
        assert ms == ["20251101", "20251201", "20260101"], ms

    return cases


def _fixture_dataset(empty: bool = False) -> dict:
    """A dataset shaped exactly like build_dataset output, for offline render tests."""
    def mk(code, name, trust, pm, style, nav, nav_ev, aum, ytd, since, new, points):
        ret = {"horizons": {}, "last_date": "2026-06-19", "points": points,
               "last_close": Val(nav, EV_OFFICIAL, "fx") if nav else Val(None),
               "day_pct": Val(0.8, EV_OFFICIAL, "fx"),
               "volume": Val(12345, EV_OFFICIAL, "fx"),
               "ytd": Val(ytd, EV_OFFICIAL, "fx") if ytd is not None else Val(None),
               "since": Val(since, EV_OFFICIAL, "fx") if since is not None else Val(None)}
        for i, n in enumerate(HORIZONS):
            ret["horizons"][n] = (Val(round(1.5 * (i + 1) - 3, 1), EV_OFFICIAL, "fx")
                                  if points > n else Val(None, note="hist short"))
        return {"code": code, "name": name, "trust": Val(trust, EV_DERIVED, "fx"),
                "pm": Val(pm, EV_OFFICIAL, "fx") if pm else Val(None),
                "style": Val(style, EV_DERIVED, "fx"), "market": "TWSE",
                "listed": "2025-05-05", "is_new": new,
                "nav": Val(nav, nav_ev, "fx") if nav else Val(None),
                "aum": Val(aum, EV_DERIVED, "fx") if aum else Val(None),
                "units": Val(1e9, EV_OFFICIAL, "fx"),
                "flow_ytd": Val(12.5, EV_DERIVED, "fx") if not new else Val(None),
                "fee": Val(None), "dist": Val(None), "ret": ret, "points": points,
                "sources": ["fund_master"]}

    etfs = [] if empty else [
        mk("00981A", "\u4e3b\u52d5\u7d71\u4e00\u53f0\u80a1\u589e\u9577", "\u7d71\u4e00\u6295\u4fe1",
           "\u6797\u54f2\u7def", "\u6210\u9577", 32.45, EV_OFFICIAL, 285.0, 18.4, 42.1, False, 300),
        mk("00403A", "\u4e3b\u52d5\u65b0\u6a02\u53f0\u80a1", "\u65b0\u5149\u6295\u4fe1",
           None, "\u512a\u9078", 10.9, EV_ESTIMATED, None, None, 3.2, True, 12),
    ]
    return {
        "meta": {"engine": __engine__, "version": __version__,
                 "generated_at": "2026-08-16T12:00:00", "run_date": "2026-08-16",
                 "data_date": "2026-06-19", "suffix": "A", "months": 14,
                 "count": len(etfs), "count_new": sum(1 for e in etfs if e["is_new"]),
                 "registry_total": len(etfs) + 1, "registry_new": [], "registry_dormant": ["00900A"],
                 "http": {"net": 12, "cache": 30, "fail": 1}},
        "diagnostics": {"fund_master": "OK 2 \u6a94", "stock_day_all": "OK",
                        "isin_twse": "OK", "isin_tpex": "FAIL timeout", "tpex": "OK"},
        "etfs": etfs,
        "holdings": ({} if empty else {"00981A": [
            {"code": "2330", "name": "\u53f0\u7a4d\u96fb", "weight": 28.5, "group": "\u534a\u5c0e\u9ad4"},
            {"code": "2317", "name": "\u9d3b\u6d77", "weight": 7.4, "group": "AI"}]}),
        "quotes": {"2330": {"close": 1200.0, "day_pct": 1.2, "volume": 30000}},
        "dormant": [{"code": "00900A", "name": "\u820a\u6a94", "first_seen": "2026-01-01",
                     "last_seen": "2026-05-01"}],
    }


def run_selftest(verbose: bool = True) -> int:
    LOG.banner("VIA ActiveStockETF · SELF-TEST", "offline · fixtures only · no network")
    cases = _selftest_cases()
    passed, failed = 0, []
    for name, fn in cases:
        try:
            fn()
            passed += 1
            if verbose:
                sys.stdout.write("  \u2713 PASS  %s\n" % name)
        except Exception:                                  # noqa: BLE001
            failed.append((name, traceback.format_exc()))
            sys.stdout.write("  \u2717 FAIL  %s\n" % name)
    sys.stdout.write("\n  %d/%d PASS\n" % (passed, len(cases)))
    for name, tb in failed:
        sys.stdout.write("\n--- %s ---\n%s\n" % (name, tb))
    sys.stdout.flush()
    return 0 if not failed else 1


# --------------------------------------------------------------------------- #
# 16.  MAIN
# --------------------------------------------------------------------------- #

def default_root() -> Path:
    if DEFAULT_ROOT:
        return DEFAULT_ROOT
    for cand in (Path(r"C:\VeritasIntelligenceAnalytics"),
                 Path.home() / "Downloads" / "VeritasIntelligenceAnalytics"):
        if cand.exists():
            return cand / "dict" / "ETF" / "_active"
    return Path.cwd() / "VIA_ActiveStockETF_out"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="VIA_ActiveStockETF.py",
        description="VIA Active Taiwan Stock ETF Console - fetch, verify, render.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=None, help="output folder")
    p.add_argument("--cache", type=Path, default=None, help="HTTP cache folder")
    p.add_argument("--overrides", type=Path, default=None,
                   help="folder holding holdings_<CODE>.csv|json override files")
    p.add_argument("--months", type=int, default=14,
                   help="months of daily history per ETF (default 14 => covers 240D)")
    p.add_argument("--suffix", default="A",
                   help="active-ETF code suffixes to include (A=equity, D=bond; e.g. AD)")
    p.add_argument("--workers", type=int, default=4, help="parallel history fetchers")
    p.add_argument("--offline", action="store_true", help="use cache only, never touch the network")
    p.add_argument("--no-cache", action="store_true", help="do not write the HTTP cache")
    p.add_argument("--open", dest="do_open", action="store_true", help="open the HTML when finished")
    p.add_argument("--quiet", action="store_true", help="suppress console progress")
    p.add_argument("--selftest", action="store_true", help="run offline unit tests and exit")
    p.add_argument("--probe", action="store_true", help="endpoint reachability matrix and exit")
    # Base-URL overrides let the whole pipeline run against a local mock server.
    p.add_argument("--base-openapi", default=BASE_OPENAPI)
    p.add_argument("--base-twse", default=BASE_TWSE)
    p.add_argument("--base-isin", default=BASE_ISIN)
    p.add_argument("--base-tpex", default=BASE_TPEX)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.selftest:
        return run_selftest()

    global LOG
    LOG = Log(quiet=args.quiet)
    log = LOG

    out = args.out or default_root()
    args.out = Path(out)
    args.cache = Path(args.cache) if args.cache else args.out / "_cache"
    args.overrides = Path(args.overrides) if args.overrides else args.out / "overrides"
    args.suffix = re.sub(r"[^A-Za-z]", "", args.suffix).upper() or "A"
    args.months = max(2, min(60, args.months))
    args.out.mkdir(parents=True, exist_ok=True)
    args.overrides.mkdir(parents=True, exist_ok=True)

    http = Http(args.cache, offline=args.offline, no_cache=args.no_cache)
    src = Sources(http, args.base_openapi, args.base_twse, args.base_isin, args.base_tpex)

    if args.probe:
        return run_probe(src, log)

    log.banner("VIA ActiveStockETF %s · \u4e3b\u52d5\u5f0f\u53f0\u80a1 ETF \u6230\u60c5\u53f0" % __version__,
               "\u81ea\u52d5\u63a2\u7d22\u6e05\u55ae \u00b7 \u53ea\u589e\u4e0d\u6e1b registry \u00b7 \u8b49\u64da\u8aa0\u5be6 \u00b7 \u8f38\u51fa %s" % args.out)

    reg = Registry(args.out / "active_etf_registry.json")
    t0 = time.time()
    try:
        ds = build_dataset(src, reg, args, log)
    except FetchError as exc:
        log.err("\u8cc7\u6599\u64f7\u53d6\u5931\u6557\uff1a%s" % exc)
        log.info("\u8a66\u8a66 --probe \u78ba\u8a8d\u7aef\u9ede\uff0c\u6216 --offline \u4f7f\u7528\u5feb\u53d6")
        return 2

    reg.save(ds["meta"]["run_date"])
    log.ok("registry \u5beb\u56de\uff1a%d \u7b46\uff08\u53ea\u589e\u4e0d\u6e1b\uff09" % ds["meta"]["registry_total"])

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = args.out / ("VIA_ActiveStockETF_%s.html" % stamp)
    json_path = args.out / "etf_matrix.json"
    csv_path = args.out / "etf_matrix.csv"

    write_text(html_path, render_html(ds, log))
    export_json(ds, json_path)
    export_csv(ds, csv_path)
    latest = args.out / "VIA_ActiveStockETF_latest.html"
    try:
        shutil.copy2(html_path, latest)
    except OSError:
        latest = html_path

    pend = sum(1 for e in ds["etfs"] for f in ("nav", "aum", "flow_ytd", "fee", "dist")
               if not e[f].ok)
    log.step("\u5b8c\u6210 %.1fs \u00b7 %d \u6a94\u4e3b\u52d5\u5f0f ETF \u00b7 %d \u500b\u5f85\u88dc\u6b04\u4f4d\u4fdd\u6301 PENDING"
             % (time.time() - t0, ds["meta"]["count"], pend))
    log.ok("HTML  %s" % html_path)
    log.ok("JSON  %s" % json_path)
    log.ok("CSV   %s" % csv_path)

    # An empty universe is never a success.  Outputs are still written so the
    # operator can read the diagnostics, but the exit code says so out loud.
    if not ds["etfs"]:
        log.err("\u63a2\u7d22\u7d50\u679c\u70ba 0 \u6a94 \u2014 \u4f86\u6e90\u5168\u6578\u672a\u89e3\u6790\u6216\u5feb\u53d6\u70ba\u7a7a")
        for k, v in ds["diagnostics"].items():
            log.info("  %-14s %s" % (k, v or "OK"))
        log.info("\u5148\u8dd1 --probe \u78ba\u8a8d\u7aef\u9ede\uff1b--offline \u9700\u5148\u6709\u4e00\u6b21\u6210\u529f\u7684\u7dda\u4e0a\u57f7\u884c\u5efa\u7acb\u5feb\u53d6")
        return 3

    if args.do_open:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(latest))                  # noqa: S606
            elif sys.platform == "darwin":
                os.system("open '%s'" % latest)            # noqa: S605
            else:
                os.system("xdg-open '%s' >/dev/null 2>&1 &" % latest)  # noqa: S605
        except Exception as exc:                           # noqa: BLE001
            log.warn("\u7121\u6cd5\u81ea\u52d5\u958b\u555f\uff1a%s" % exc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
