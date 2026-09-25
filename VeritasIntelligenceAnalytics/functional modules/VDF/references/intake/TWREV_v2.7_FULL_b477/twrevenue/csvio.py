"""csvio.py -- CSV 讀寫的單一入口 (編碼治理).

── 問題 ────────────────────────────────────────────────────
pandas 的 to_csv 預設寫「**無 BOM 的 UTF-8**」。
繁體中文 Windows 的 Excel 在開 .csv 時, 若檔案沒有 BOM, 會改用系統 ANSI
codepage (CP950 / Big5) 去解讀, 於是中文全變亂碼:

    正確      2330,台積電,半導體,L,上市
    Excel     2330,??????,?????,L,????

── 解法 ────────────────────────────────────────────────────
寫檔一律用 **utf-8-sig** (UTF-8 + BOM)。Excel 看到 BOM 就會正確以 UTF-8 開啟,
Google Sheets、Numbers 也都認得。

讀檔同樣用 utf-8-sig: 有 BOM 時自動吃掉, 沒 BOM 時行為與 utf-8 相同 —
這一點很重要, 否則用純 utf-8 讀含 BOM 的檔, 第一個欄名會變成
'\\ufeffstock_id', 後續所有欄位存取都會失敗。

若要餵給不吃 BOM 的下游工具, 於 config 設 output.csv_encoding: utf-8 即可。
"""
from __future__ import annotations

import pandas as pd

# UTF-8 + BOM: Excel(繁中 Windows) 開啟不亂碼
DEFAULT_WRITE_ENCODING = "utf-8-sig"
# 讀取用 utf-8-sig 可同時相容「有 BOM」與「無 BOM」
READ_ENCODING = "utf-8-sig"


def write_encoding(cfg: dict | None = None) -> str:
    if cfg:
        return ((cfg.get("output") or {}).get("csv_encoding")
                or DEFAULT_WRITE_ENCODING)
    return DEFAULT_WRITE_ENCODING


def write(df: pd.DataFrame, path: str, cfg: dict | None = None, **kw) -> None:
    """輸出 CSV (預設 utf-8-sig, Excel 直接開不亂碼)."""
    kw.setdefault("index", False)
    df.to_csv(path, encoding=write_encoding(cfg), **kw)


def read(path: str, **kw) -> pd.DataFrame:
    """讀取 CSV (utf-8-sig: 有無 BOM 皆可)."""
    kw.setdefault("encoding", READ_ENCODING)
    return pd.read_csv(path, **kw)


def has_bom(path: str) -> bool:
    """檔案是否帶 UTF-8 BOM (供稽核/測試用)."""
    try:
        with open(path, "rb") as f:
            return f.read(3) == b"\xef\xbb\xbf"
    except OSError:
        return False
