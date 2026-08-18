# -*- coding: utf-8 -*-
"""VDF · 價格資料層(ADJ 優先 → 一般價格)。

設計準則(對接 VRN_TAEngine_v01.py):
  1. 先取 Adj Close(還原價,含除權息/分割調整)→ 作為報酬率/技術指標主序列。
  2. 再取 Close(原始收盤價)→ 保留供顯示與量價對照。
  3. graceful degrade:Adj Close 缺 → 退回 Close;兩者皆缺 → 該檔略過。
  4. 只增不減:本檔僅新增資料層函式,不修改既有引擎內部。

所有參數置頂。離線 --selftest 不需網路。
"""

from __future__ import annotations

import sys
import json

# =============================================================================
# PARAMETERS (all on top)
# =============================================================================

# 價格優先序:ADJ 優先,其次一般收盤。引擎以 PRICE 欄算報酬,RAW_CLOSE 供顯示。
PRICE_PRIORITY = ["Adj Close", "Close"]

# yfinance 取數一律 auto_adjust=False,確保同時拿到 Adj Close 與 Close。
YF_AUTO_ADJUST = False

# 欄位標準化別名(與引擎 normalize_columns 一致的子集)。
COLUMN_ALIASES = {
    "Date": ["Date", "date", "datetime", "日期"],
    "Open": ["Open", "open", "開盤價", "o"],
    "High": ["High", "high", "最高價", "h"],
    "Low": ["Low", "low", "最低價", "l"],
    "Close": ["Close", "close", "收盤價", "收盤", "c"],
    "Adj Close": ["Adj Close", "adj_close", "還原收盤價", "復權收盤", "adjclose"],
    "Volume": ["Volume", "volume", "成交量", "成交股數", "vol"],
}

# 多來源備援順序(yfinance 為主,stooq 為備)。
SOURCE_ORDER = ["yfinance", "stooq"]


# =============================================================================
# COLUMN NORMALIZATION
# =============================================================================

def normalize_columns(df):
    """把任意中英欄名映射成標準鍵。回傳新 DataFrame(不改原物件)。"""
    rename = {}
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for std, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = alias.strip().lower()
            if key in lower_map:
                rename[lower_map[key]] = std
                break
    return df.rename(columns=rename)


def select_price_series(df):
    """依 PRICE_PRIORITY 選主價格序列。

    回傳 (price_source, df_with_PRICE)。
      price_source: 實際採用的欄名('Adj Close' 或 'Close')。
    若兩者皆缺,price_source 為 None,PRICE 欄不建立。
    """
    chosen = None
    for col in PRICE_PRIORITY:
        if col in df.columns and df[col].notna().any():
            chosen = col
            break

    out = df.copy()
    if chosen is not None:
        out["PRICE"] = out[chosen]
        out["PRICE_SOURCE"] = chosen
        if "Close" in out.columns:
            out["RAW_CLOSE"] = out["Close"]
        else:
            out["RAW_CLOSE"] = out[chosen]
    return chosen, out


# =============================================================================
# FETCH (network) — keep separate from parse for offline testing
# =============================================================================

def _fetch_yfinance(ticker, start, end):
    import yfinance as yf  # noqa: lazy import

    raw = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=YF_AUTO_ADJUST,
        progress=False,
    )
    if raw is None or len(raw) == 0:
        return None
    raw = raw.reset_index()
    # yfinance 多層欄位攤平
    if hasattr(raw.columns, "nlevels") and raw.columns.nlevels > 1:
        raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
    return raw


def _fetch_stooq(ticker, start, end):
    import pandas as pd  # noqa
    from urllib.request import urlopen

    sym = ticker.lower()
    url = "https://stooq.com/q/d/l/?s={0}&i=d".format(sym)
    with urlopen(url, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    from io import StringIO
    df = pd.read_csv(StringIO(text))
    return df if len(df) > 0 else None


def fetch_prices(ticker, start=None, end=None, sources=None):
    """ADJ 優先取價。回傳標準化後含 PRICE/RAW_CLOSE/PRICE_SOURCE 的 DataFrame。

    來源依 SOURCE_ORDER 逐一嘗試,成功即停;全失敗回傳 None。
    """
    use = sources if sources else SOURCE_ORDER
    last_err = None
    for src in use:
        try:
            if src == "yfinance":
                raw = _fetch_yfinance(ticker, start, end)
            elif src == "stooq":
                raw = _fetch_stooq(ticker, start, end)
            else:
                continue
            if raw is None:
                continue
            norm = normalize_columns(raw)
            price_source, out = select_price_series(norm)
            if price_source is None:
                continue
            out.attrs["ticker"] = ticker
            out.attrs["fetch_source"] = src
            out.attrs["price_source"] = price_source
            return out
        except Exception as exc:  # noqa: broad — 來源容錯
            last_err = "{0}: {1}".format(src, exc)
            continue
    if last_err is not None:
        sys.stderr.write("fetch_prices all sources failed: {0}\n".format(last_err))
    return None


def to_parquet(df, path):
    df.to_parquet(path, index=False)
    return path


# =============================================================================
# SELFTEST (offline, no network)
# =============================================================================

def _selftest():
    import pandas as pd

    passed = 0
    total = 0

    def check(name, cond):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print("  PASS  {0}".format(name))
        else:
            print("  FAIL  {0}".format(name))

    # case 1: 同時有 Adj Close 與 Close → 採 Adj Close(ADJ 優先)
    df1 = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low": [99.0, 100.0],
        "close": [101.0, 102.0],
        "adj_close": [90.0, 91.0],
        "volume": [1000, 1200],
    })
    n1 = normalize_columns(df1)
    src1, out1 = select_price_series(n1)
    check("ADJ-first selects Adj Close", src1 == "Adj Close")
    check("PRICE equals Adj Close", list(out1["PRICE"]) == [90.0, 91.0])
    check("RAW_CLOSE keeps Close", list(out1["RAW_CLOSE"]) == [101.0, 102.0])

    # case 2: 只有 Close → 退回 Close
    df2 = pd.DataFrame({
        "Date": ["2026-01-01"],
        "Close": [55.0],
        "Volume": [10],
    })
    n2 = normalize_columns(df2)
    src2, out2 = select_price_series(n2)
    check("fallback to Close when no Adj Close", src2 == "Close")
    check("PRICE equals Close on fallback", list(out2["PRICE"]) == [55.0])

    # case 3: 中文欄名標準化
    df3 = pd.DataFrame({"日期": ["2026-01-01"], "收盤價": [70.0], "還原收盤價": [65.0]})
    n3 = normalize_columns(df3)
    check("Chinese columns normalized", "Adj Close" in n3.columns and "Close" in n3.columns)
    src3, _ = select_price_series(n3)
    check("Chinese ADJ-first", src3 == "Adj Close")

    # case 4: 兩者皆缺 → price_source None
    df4 = pd.DataFrame({"Date": ["2026-01-01"], "Volume": [1]})
    n4 = normalize_columns(df4)
    src4, _ = select_price_series(n4)
    check("no price series -> None", src4 is None)

    print("SELFTEST {0}/{1} PASS".format(passed, total))
    summary = {"passed": passed, "total": total, "ok": passed == total}
    print("SELFTEST_JSON " + json.dumps(summary))
    return 0 if passed == total else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print("vdf_price_fetch ready. PRICE_PRIORITY={0}".format(PRICE_PRIORITY))
