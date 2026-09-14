"""fetch.py -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收.

資料來源 (官方): 公開資訊觀測站 MOPS
    URL: https://mops.twse.com.tw/nas/t21/{market}/t21sc03_{roc}_{month}_{i}.html
        market : sii=上市(TWSE), otc=上櫃(TPEX)
        roc    : 民國年 = 西元 - 1911
        month  : 1..12  (不補零)
        i      : 0=國內公司, 1=國外KY公司
        舊格式 (roc <= 98): t21sc03_{roc}_{month}.html  (無 _i)
    編碼: Big5

MOPS 欄位 -> 標準欄位:
    公司代號 -> stock_id      公司名稱 -> name
    當月營收 -> revenue       上月營收 -> revenue_prev_month
    去年當月營收 -> revenue_prev_year
    上月比較增減(%) -> mom    去年同月增減(%) -> yoy
    當月累計營收 -> cum_revenue   去年累計營收 -> cum_revenue_prev_year
    前期比較增減(%) -> cum_yoy
    產業別(群組標題) -> industry
"""
from __future__ import annotations

import io
import os
import time
import datetime as dt

import pandas as pd
import requests

from . import csvio

_COLUMN_PATTERNS = {
    "stock_id":              ["公司代號"],
    "name":                  ["公司名稱"],
    "revenue":               ["當月營收"],
    "revenue_prev_month":    ["上月營收"],
    "revenue_prev_year":     ["去年當月營收"],
    "mom":                   ["上月比較增減"],
    "yoy":                   ["去年同月增減"],
    "cum_revenue":           ["當月累計營收", "本月累計營收"],
    "cum_revenue_prev_year": ["去年累計營收"],
    "cum_yoy":               ["前期比較增減"],
}
_NUMERIC_COLS = [
    "revenue", "revenue_prev_month", "revenue_prev_year", "mom", "yoy",
    "cum_revenue", "cum_revenue_prev_year", "cum_yoy",
]

# 股票代號規則: 四碼數字, 第一碼不可為零 (可由 config.fetch.stock_id_regex 覆寫)
STOCK_ID_REGEX = r"^[1-9]\d{3}$"


def _roc_year(year: int) -> int:
    return year - 1911


def month_iter(months_back: int, ref: dt.date | None = None):
    """由最新往回推 months_back 個月. 月營收次月10號前後公布 -> 最新可抓=上個月."""
    ref = ref or dt.date.today()
    y, m = ref.year, ref.month - 1
    if m == 0:
        y, m = y - 1, 12
    for _ in range(months_back):
        yield y, m
        m -= 1
        if m == 0:
            y, m = y - 1, 12


def _build_url(host: str, market: str, year: int, month: int, reg: int) -> str:
    roc = _roc_year(year)
    if roc <= 98:
        path = f"/nas/t21/{market}/t21sc03_{roc}_{month}.html"
    else:
        path = f"/nas/t21/{market}/t21sc03_{roc}_{month}_{reg}.html"
    return host.rstrip("/") + path


def _cell_to_std(text: str) -> str | None:
    """表頭文字 -> 標準欄位名, 採「最長匹配」.

    「去年當月營收」同時包含「當月營收」(revenue) 與「去年當月營收」
    (revenue_prev_year); 取最長者, 避免當月營收被去年同月覆蓋
    (那會毀掉所有 YoY 計算)。
    """
    t = str(text).replace(" ", "").replace("　", "").replace("\n", "")
    best, best_len = None, 0
    for std, pats in _COLUMN_PATTERNS.items():
        for p in pats:
            pc = p.replace(" ", "")
            if pc in t and len(pc) > best_len:
                best, best_len = std, len(pc)
    return best


def _rows_from_table(tbl: pd.DataFrame) -> list[dict]:
    """逐列掃描, 自行辨識表頭列與產業別標題列.

    MOPS 把「產業別：xxx」標題、表頭、資料列混在同一張表:
      - 「產業別：xxx」-> 更新目前產業別, 附掛到其後每筆資料
      - 含「公司代號」且含「當月營收」-> 表頭, 建立欄位映射
    如此全市場每家公司都自動帶產業別 (供週期分流使用)。
    """
    matrix = [[
        "".join(str(x) for x in c) if isinstance(c, tuple) else str(c)
        for c in tbl.columns
    ]]
    for _, r in tbl.iterrows():
        matrix.append([str(x) for x in r.tolist()])

    rows: list[dict] = []
    colmap: dict[int, str] = {}
    current_ind = None
    for line in matrix:
        cap = next((c for c in line if "產業別" in str(c)), None)
        if cap is not None:
            t = str(cap).replace("：", ":")
            if ":" in t:
                current_ind = t.split(":", 1)[1].strip() or None
            continue
        std_in_line = {i: s for i, s in
                       ((i, _cell_to_std(v)) for i, v in enumerate(line)) if s}
        if "stock_id" in std_in_line.values() and "revenue" in std_in_line.values():
            colmap = std_in_line
            continue
        if not colmap:
            continue
        rec = {std: line[i] for i, std in colmap.items() if i < len(line)}
        rec["industry"] = current_ind
        rows.append(rec)
    return rows


def _parse_html(html: str) -> pd.DataFrame:
    """單一 MOPS 頁面 -> 標準長格式 DataFrame (可能為空)."""
    try:
        tables = pd.read_html(io.StringIO(html))
    except ValueError:
        return pd.DataFrame()

    all_rows: list[dict] = []
    for tbl in tables:
        all_rows.extend(_rows_from_table(tbl))
    if not all_rows:
        return pd.DataFrame()

    out = pd.DataFrame(all_rows)
    if "stock_id" not in out.columns or "revenue" not in out.columns:
        return pd.DataFrame()

    out["stock_id"] = out["stock_id"].astype(str).str.strip()
    out = out[out["stock_id"].str.match(STOCK_ID_REGEX, na=False)].copy()
    for col in _NUMERIC_COLS:
        if col in out.columns:
            out[col] = (out[col].astype(str)
                        .str.replace(",", "", regex=False)
                        .str.replace("--", "", regex=False).str.strip())
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def fetch_page(session, hosts, market, year, month, reg,
               user_agent, timeout, retries) -> pd.DataFrame:
    last_err = None
    for host in hosts:
        url = _build_url(host, market, year, month, reg)
        for attempt in range(retries):
            try:
                r = session.get(url, headers={"User-Agent": user_agent},
                                timeout=timeout)
                if r.status_code == 404:
                    return pd.DataFrame()
                r.raise_for_status()
                r.encoding = "big5"
                df = _parse_html(r.text)
                if not df.empty:
                    df["year"], df["month"], df["market"] = year, month, market
                return df
            except requests.RequestException as e:
                last_err = e
                time.sleep(2 * (attempt + 1))
    if last_err:
        print(f"    [warn] {market} {year}-{month:02d} reg{reg}: {last_err}")
    return pd.DataFrame()


def fetch_all(cfg: dict, ref: dt.date | None = None) -> pd.DataFrame:
    """依 config 抓取近 months_back 個月的全上市/上櫃月營收."""
    global STOCK_ID_REGEX
    fc = cfg["fetch"]
    STOCK_ID_REGEX = fc.get("stock_id_regex", STOCK_ID_REGEX)
    os.makedirs(fc["cache_dir"], exist_ok=True)
    session = requests.Session()
    frames = []

    for year, month in month_iter(fc["months_back"], ref):
        cache_fp = os.path.join(fc["cache_dir"], f"{year}_{month:02d}.csv")
        if os.path.exists(cache_fp):
            frames.append(csvio.read(cache_fp, dtype={"stock_id": str}))
            print(f"  [cache] {year}-{month:02d}")
            continue
        month_frames = []
        for market in fc["markets"]:
            for reg in fc["registrations"]:
                df = fetch_page(session, fc["base_hosts"], market, year, month,
                                reg, fc["user_agent"], fc["timeout_sec"],
                                fc["retries"])
                if not df.empty:
                    month_frames.append(df)
                time.sleep(fc["request_delay_sec"])
        if month_frames:
            m = pd.concat(month_frames, ignore_index=True)
            csvio.write(m, cache_fp, cfg)
            frames.append(m)
            print(f"  [ok]    {year}-{month:02d}  ({len(m)} 家)")
        else:
            print(f"  [empty] {year}-{month:02d}  (可能尚未公布)")

    if not frames:
        raise RuntimeError(
            "未抓到任何資料。可能原因: (1) 此環境無法連到 MOPS; "
            "(2) 網域已變更 -> 請調整 config.fetch.base_hosts。")

    data = pd.concat(frames, ignore_index=True)
    data = data.drop_duplicates(subset=["stock_id", "year", "month"], keep="last")
    data["date"] = pd.to_datetime(dict(year=data.year, month=data.month, day=1))
    data = data.sort_values(["stock_id", "date"]).reset_index(drop=True)
    csvio.write(data, fc["raw_out"], cfg)
    print(f"\n已存檔: {fc['raw_out']}  ({len(data)} 列, "
          f"{data.stock_id.nunique()} 家公司)")
    return data
