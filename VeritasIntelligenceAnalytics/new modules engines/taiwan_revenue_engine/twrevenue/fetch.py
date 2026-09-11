"""fetch.py -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收.

資料來源 (官方): 公開資訊觀測站 MOPS
    URL: https://mops.twse.com.tw/nas/t21/{market}/t21sc03_{roc}_{month}_{i}.html
        market : sii=上市(TWSE), otc=上櫃(TPEX)
        roc    : 民國年 = 西元 - 1911
        month  : 1..12  (不補零)
        i      : 0=國內公司, 1=國外KY公司
        舊格式 (roc <= 98): t21sc03_{roc}_{month}.html  (無 _i)
    編碼: Big5

每個月抓 markets x registrations 個頁面 (預設 sii/otc x 0/1 = 4 個)。
已抓過的月份會快取到 config.fetch.cache_dir, 重跑時不會重抓歷史月份。

MOPS 頁面欄位 (中文) -> 標準英文欄位:
    公司代號            -> stock_id
    公司名稱            -> name
    當月營收            -> revenue            (單月營收, 千元)
    上月營收            -> revenue_prev_month
    去年當月營收        -> revenue_prev_year
    上月比較增減(%)     -> mom                (MoM 月增率 %)
    去年同月增減(%)     -> yoy                (YoY 年增率 %)
    當月累計營收        -> cum_revenue        (累計營收, 千元)
    去年累計營收        -> cum_revenue_prev_year
    前期比較增減(%)     -> cum_yoy            (累計 YoY %)
產業別 (由頁面群組標題擷取) -> industry
"""
from __future__ import annotations

import io
import os
import time
import datetime as dt
from typing import Iterable

import pandas as pd
import requests

# MOPS 中文欄位 -> 標準欄位 (用「包含」比對, 容忍全形括號/空白差異)
_COLUMN_PATTERNS = {
    "stock_id":               ["公司代號", "公司 代號"],
    "name":                   ["公司名稱", "公司 名稱"],
    "revenue":                ["當月營收"],
    "revenue_prev_month":     ["上月營收"],
    "revenue_prev_year":      ["去年當月營收", "去年 當月營收"],
    "mom":                    ["上月比較增減", "上月比較 增減"],
    "yoy":                    ["去年同月增減", "去年同月 增減"],
    "cum_revenue":            ["當月累計營收", "本月累計營收"],
    "cum_revenue_prev_year":  ["去年累計營收"],
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
    """產生 (year, month), 由最新往回推 months_back 個月.

    月營收在次月 10 號前後才公布, 所以「最新可抓月份」= 上個月。
    """
    ref = ref or dt.date.today()
    # 最新完整月份 = 上個月
    y, m = ref.year, ref.month
    m -= 1
    if m == 0:
        y -= 1
        m = 12
    for _ in range(months_back):
        yield y, m
        m -= 1
        if m == 0:
            y -= 1
            m = 12


def _build_url(host: str, market: str, year: int, month: int, reg: int) -> str:
    roc = _roc_year(year)
    if roc <= 98:  # 舊格式無註冊別後綴
        path = f"/nas/t21/{market}/t21sc03_{roc}_{month}.html"
    else:
        path = f"/nas/t21/{market}/t21sc03_{roc}_{month}_{reg}.html"
    return host.rstrip("/") + path


def _cell_to_std(text: str) -> str | None:
    """把單一表頭文字對應到標準欄位名 (無對映回 None).

    採「最長匹配」: 例如「去年當月營收」同時包含「當月營收」(revenue) 與
    「去年當月營收」(revenue_prev_year), 取最長者 -> revenue_prev_year,
    避免當月營收被去年同月營收覆蓋 (會毀掉所有 YoY 計算)。
    """
    t = str(text).replace(" ", "").replace("　", "").replace("\n", "")
    best_std, best_len = None, 0
    for std, pats in _COLUMN_PATTERNS.items():
        for p in pats:
            pc = p.replace(" ", "")
            if pc in t and len(pc) > best_len:
                best_std, best_len = std, len(pc)
    return best_std


def _rows_from_table(tbl: pd.DataFrame) -> list[dict]:
    """逐列掃描一張表, 自行辨識表頭列與產業別標題列.

    MOPS 頁面把「產業別：xxx」標題、表頭、資料列混在同一張表:
      - 「產業別：xxx」列 -> 更新目前產業別, 附掛到其後每筆資料 (industry 欄)
      - 含「公司代號」且含「當月營收」的列 -> 表頭, 建立欄位映射
      - 其後資料列依映射取值
    如此全市場每家公司都自動帶產業別 (供週期分流使用)。
    """
    # 把欄位名也視為資料的第一列 (若 pandas 誤把資料當表頭)
    matrix = []
    header_from_cols = [
        "".join(str(x) for x in c) if isinstance(c, tuple) else str(c)
        for c in tbl.columns
    ]
    matrix.append(header_from_cols)
    for _, r in tbl.iterrows():
        matrix.append([str(x) for x in r.tolist()])

    rows: list[dict] = []
    colmap: dict[int, str] = {}
    current_ind = None
    for line in matrix:
        # 產業別標題列? (colspan 會讓同文字重複在多欄, 取第一個)
        cap = next((c for c in line if "產業別" in str(c)), None)
        if cap is not None:
            t = str(cap).replace("：", ":")
            if ":" in t:
                current_ind = t.split(":", 1)[1].strip() or None
            continue
        std_in_line = {i: s for i, s in
                       ((i, _cell_to_std(v)) for i, v in enumerate(line)) if s}
        # 是表頭列嗎? (同時含 stock_id 與 revenue)
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
    """把單一 MOPS 頁面解析成標準長格式 DataFrame (可能為空)."""
    try:
        tables = pd.read_html(io.StringIO(html))
    except ValueError:
        return pd.DataFrame()  # 頁面無表格 (該月尚未公布)

    all_rows: list[dict] = []
    for tbl in tables:
        all_rows.extend(_rows_from_table(tbl))

    if not all_rows:
        return pd.DataFrame()

    out = pd.DataFrame(all_rows)
    if "stock_id" not in out.columns or "revenue" not in out.columns:
        return pd.DataFrame()
    # 清掉小計/合計/表頭殘留: stock_id 必須是純數字代號
    out["stock_id"] = out["stock_id"].astype(str).str.strip()
    out = out[out["stock_id"].str.match(STOCK_ID_REGEX, na=False)].copy()
    # 數值欄位轉型 (移除逗號)
    for col in _NUMERIC_COLS:
        if col in out.columns:
            out[col] = (
                out[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("--", "", regex=False)
                .str.strip()
            )
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def fetch_page(session, hosts, market, year, month, reg,
               user_agent, timeout, retries) -> pd.DataFrame:
    """抓單一 (market, year, month, reg) 頁面, 回傳標準 DataFrame."""
    last_err = None
    for host in hosts:
        url = _build_url(host, market, year, month, reg)
        for attempt in range(retries):
            try:
                r = session.get(url, headers={"User-Agent": user_agent},
                                timeout=timeout, verify=True)
                if r.status_code == 404:
                    return pd.DataFrame()  # 該月/市場無此頁, 換下一個
                r.raise_for_status()
                r.encoding = "big5"
                df = _parse_html(r.text)
                if not df.empty:
                    df["year"] = year
                    df["month"] = month
                    df["market"] = market
                return df
            except requests.RequestException as e:
                last_err = e
                time.sleep(2 * (attempt + 1))
    if last_err:
        print(f"    [warn] {market} {year}-{month:02d} reg{reg}: {last_err}")
    return pd.DataFrame()


def fetch_all(cfg: dict, ref: dt.date | None = None) -> pd.DataFrame:
    """依 config 抓取近 months_back 個月的全上市/上櫃月營收.

    回傳長格式 DataFrame (一列 = 一家公司一個月)。
    """
    fc = cfg["fetch"]
    global STOCK_ID_REGEX
    STOCK_ID_REGEX = fc.get("stock_id_regex", STOCK_ID_REGEX)
    os.makedirs(fc["cache_dir"], exist_ok=True)
    session = requests.Session()
    all_frames = []

    for year, month in month_iter(fc["months_back"], ref):
        cache_fp = os.path.join(fc["cache_dir"], f"{year}_{month:02d}.csv")
        if os.path.exists(cache_fp):
            all_frames.append(pd.read_csv(cache_fp, dtype={"stock_id": str}))
            print(f"  [cache] {year}-{month:02d}")
            continue

        month_frames = []
        for market in fc["markets"]:
            for reg in fc["registrations"]:
                df = fetch_page(
                    session, fc["base_hosts"], market, year, month, reg,
                    fc["user_agent"], fc["timeout_sec"], fc["retries"],
                )
                if not df.empty:
                    month_frames.append(df)
                time.sleep(fc["request_delay_sec"])

        if month_frames:
            m = pd.concat(month_frames, ignore_index=True)
            m.to_csv(cache_fp, index=False)
            all_frames.append(m)
            print(f"  [ok]    {year}-{month:02d}  ({len(m)} 家)")
        else:
            print(f"  [empty] {year}-{month:02d}  (可能尚未公布)")

    if not all_frames:
        raise RuntimeError(
            "未抓到任何資料。可能原因: (1) 此環境無法連到 MOPS; "
            "(2) 網域已變更 -> 請調整 config.fetch.base_hosts。"
        )

    data = pd.concat(all_frames, ignore_index=True)
    data = data.drop_duplicates(subset=["stock_id", "year", "month"], keep="last")
    data["date"] = pd.to_datetime(
        dict(year=data.year, month=data.month, day=1)
    )
    data = data.sort_values(["stock_id", "date"]).reset_index(drop=True)
    data.to_csv(fc["raw_out"], index=False)
    print(f"\n已存檔: {fc['raw_out']}  (共 {len(data)} 列, "
          f"{data.stock_id.nunique()} 家公司)")
    return data
