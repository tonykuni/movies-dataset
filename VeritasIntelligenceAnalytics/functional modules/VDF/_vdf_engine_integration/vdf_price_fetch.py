# -*- coding: utf-8 -*-
"""VDF price layer (ADJ-first then regular). See VDF_Engine_Config.json."""
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
import sys, json

PRICE_PRIORITY = ["Adj Close", "Close"]
YF_AUTO_ADJUST = False
COLUMN_ALIASES = {
    "Date": ["Date", "date", "datetime", "日期"],
    "Open": ["Open", "open", "開盤價", "o"],
    "High": ["High", "high", "最高價", "h"],
    "Low": ["Low", "low", "最低價", "l"],
    "Close": ["Close", "close", "收盤價", "收盤", "c"],
    "Adj Close": ["Adj Close", "adj_close", "還原收盤價", "復權收盤", "adjclose"],
    "Volume": ["Volume", "volume", "成交量", "成交股數", "vol"],
}
SOURCE_ORDER = ["yfinance", "stooq"]


def normalize_columns(df):
    rename = {}
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for std, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            k = alias.strip().lower()
            if k in lower_map:
                rename[lower_map[k]] = std
                break
    return df.rename(columns=rename)


def select_price_series(df):
    chosen = None
    for col in PRICE_PRIORITY:
        if col in df.columns and df[col].notna().any():
            chosen = col
            break
    out = df.copy()
    if chosen is not None:
        out["PRICE"] = out[chosen]
        out["PRICE_SOURCE"] = chosen
        out["RAW_CLOSE"] = out["Close"] if "Close" in out.columns else out[chosen]
    return chosen, out


def _fetch_yfinance(ticker, start, end):
    import yfinance as yf
    raw = yf.download(ticker, start=start, end=end, auto_adjust=YF_AUTO_ADJUST, progress=False)
    if raw is None or len(raw) == 0:
        return None
    raw = raw.reset_index()
    if hasattr(raw.columns, "nlevels") and raw.columns.nlevels > 1:
        raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
    return raw


def _fetch_stooq(ticker, start, end):
    import pandas as pd
    from urllib.request import urlopen
    from io import StringIO
    url = "https://stooq.com/q/d/l/?s={0}&i=d".format(ticker.lower())
    with urlopen(url, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    df = pd.read_csv(StringIO(text))
    return df if len(df) > 0 else None


def fetch_prices(ticker, start=None, end=None, sources=None):
    use = sources if sources else SOURCE_ORDER
    last_err = None
    for src in use:
        try:
            raw = _fetch_yfinance(ticker, start, end) if src == "yfinance" else (
                _fetch_stooq(ticker, start, end) if src == "stooq" else None)
            if raw is None:
                continue
            ps, out = select_price_series(normalize_columns(raw))
            if ps is None:
                continue
            out.attrs["ticker"] = ticker
            out.attrs["fetch_source"] = src
            out.attrs["price_source"] = ps
            return out
        except Exception as exc:
            last_err = "{0}: {1}".format(src, exc)
            continue
    if last_err is not None:
        sys.stderr.write("fetch_prices failed: {0}\n".format(last_err))
    return None


def to_parquet(df, path):
    df.to_parquet(path, index=False)
    return path


def _selftest():
    import pandas as pd
    passed = 0
    total = 0

    def check(name, cond):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print("  PASS  " + name)
        else:
            print("  FAIL  " + name)

    n1 = normalize_columns(pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"], "open": [100.0, 101.0],
        "high": [102.0, 103.0], "low": [99.0, 100.0], "close": [101.0, 102.0],
        "adj_close": [90.0, 91.0], "volume": [1000, 1200]}))
    s1, o1 = select_price_series(n1)
    check("ADJ-first selects Adj Close", s1 == "Adj Close")
    check("PRICE equals Adj Close", list(o1["PRICE"]) == [90.0, 91.0])
    check("RAW_CLOSE keeps Close", list(o1["RAW_CLOSE"]) == [101.0, 102.0])
    n2 = normalize_columns(pd.DataFrame({"Date": ["2026-01-01"], "Close": [55.0], "Volume": [10]}))
    s2, o2 = select_price_series(n2)
    check("fallback to Close", s2 == "Close")
    check("PRICE equals Close", list(o2["PRICE"]) == [55.0])
    n4 = normalize_columns(pd.DataFrame({"Date": ["2026-01-01"], "Volume": [1]}))
    s4, _ = select_price_series(n4)
    check("no price -> None", s4 is None)
    print("SELFTEST {0}/{1} PASS".format(passed, total))
    print("SELFTEST_JSON " + json.dumps({"passed": passed, "total": total, "ok": passed == total}))
    return 0 if passed == total else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print("vdf_price_fetch ready. PRICE_PRIORITY={0}".format(PRICE_PRIORITY))
