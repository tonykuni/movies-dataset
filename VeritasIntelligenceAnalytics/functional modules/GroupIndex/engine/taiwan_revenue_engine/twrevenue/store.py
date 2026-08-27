"""store.py -- 月營收累計增量資料庫 (parquet SSOT + duckdb 查詢層).

設計:
    - parquet (data/revenue.parquet) 是唯一真實來源 (SSOT), 累計保存
      「歷來抓過的所有月份、所有個股」— 不只最近 36 個月, 資料只增不減。
    - 每次 fetch 後 upsert: 以 (stock_id, year, month) 為主鍵去重,
      新資料覆蓋舊資料 (公司更正重編月營收時以最新公告為準)。
    - duckdb (data/revenue.duckdb) 為查詢層, 每次 upsert 後由 parquet 重建
      monthly_revenue 表, 供 SQL 分析 (體量小, 全量重建 < 1 秒)。
    - 分析時 load() 預設只取最近 months_back 個月的視窗, 歷史仍完整保存。
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

import os

import pandas as pd

KEY = ["stock_id", "year", "month"]


def _paths(cfg: dict) -> tuple[str, str | None]:
    sc = cfg.get("storage", {}) or {}
    pq = sc.get("parquet_path", "data/revenue.parquet")
    db = sc.get("duckdb_path") or None
    return pq, db


def upsert(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """把新抓的資料合併進累計 parquet, 並同步 duckdb. 回傳合併後全量."""
    pq, db = _paths(cfg)
    os.makedirs(os.path.dirname(pq) or ".", exist_ok=True)

    df = df.copy()
    df["stock_id"] = df["stock_id"].astype(str)
    n_before = 0
    frames = [df]
    if os.path.exists(pq):
        old = pd.read_parquet(pq)
        old["stock_id"] = old["stock_id"].astype(str)
        n_before = len(old)
        frames.insert(0, old)

    allq = pd.concat(frames, ignore_index=True)
    # 主鍵去重: 保留最後 (= 本次新抓) -> 公司更正月營收時以新公告為準
    allq = allq.drop_duplicates(subset=KEY, keep="last")
    allq["date"] = pd.to_datetime(dict(year=allq["year"], month=allq["month"], day=1))
    allq = allq.sort_values(["stock_id", "date"]).reset_index(drop=True)
    allq.to_parquet(pq, index=False)

    added = len(allq) - n_before
    print(f"[store] parquet 累計 {len(allq):,} 列 "
          f"({allq['stock_id'].nunique():,} 檔 × "
          f"{allq['date'].nunique()} 個月; 本次淨增 {added:+,}) -> {pq}")

    if db:
        try:
            import duckdb
            con = duckdb.connect(db)
            con.execute(
                "CREATE OR REPLACE TABLE monthly_revenue AS "
                "SELECT * FROM read_parquet(?)", [pq])
            n = con.execute("SELECT COUNT(*) FROM monthly_revenue").fetchone()[0]
            con.close()
            print(f"[store] duckdb monthly_revenue {n:,} 列 -> {db}")
        except ImportError:
            print("[store] 未安裝 duckdb, 略過查詢層 (pip install duckdb)")
    return allq


def load(cfg: dict, months_back: int | None = None) -> pd.DataFrame | None:
    """讀取累計 parquet; months_back 給定時只取最近 N 個月視窗. 無檔回 None."""
    pq, _ = _paths(cfg)
    if not os.path.exists(pq):
        return None
    df = pd.read_parquet(pq)
    df["stock_id"] = df["stock_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"])
    if months_back:
        keep = sorted(df["date"].unique())[-months_back:]
        df = df[df["date"].isin(keep)]
    return df.sort_values(["stock_id", "date"]).reset_index(drop=True)
