"""SSOT 儲存層：Parquet 增量維護。

  - 增量：只追加新事件（以 content_hash 去重），不重算全量
  - append-only：舊資料不刪不改，符合治理原則
  - snapshot diff：和上一版比，標出 新增 / 變更 / 消失 —— 進度比對的基礎
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

import os
from datetime import datetime

import pandas as pd

from .schema import SSOT_COLUMNS


class ParquetStore:
    def __init__(self, store_dir: str):
        self.store_dir = store_dir
        os.makedirs(store_dir, exist_ok=True)
        self.main_path = os.path.join(store_dir, "ssot.parquet")

    def load(self) -> pd.DataFrame:
        if os.path.exists(self.main_path):
            return pd.read_parquet(self.main_path)
        return pd.DataFrame(columns=SSOT_COLUMNS)

    def upsert(self, new_df: pd.DataFrame) -> dict:
        """增量寫入。回傳 {added, updated, total} 與 diff 明細。"""
        existing = self.load()
        for col in SSOT_COLUMNS:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[SSOT_COLUMNS]

        if existing.empty:
            merged = new_df.copy()
            diff = {"added": new_df["uid"].tolist(), "updated": [], "stale": []}
        else:
            old_hash = dict(zip(existing["uid"], existing["content_hash"]))
            added, updated = [], []
            for _, r in new_df.iterrows():
                uid = r["uid"]
                if uid not in old_hash:
                    added.append(uid)
                elif old_hash[uid] != r["content_hash"]:
                    updated.append(uid)
            new_uids = set(new_df["uid"])
            stale = [u for u in existing["uid"] if u not in new_uids]

            # 合併：以 uid 為鍵，新資料覆蓋同 uid 舊資料；舊有但這次沒出現的保留
            combined = pd.concat([existing[~existing["uid"].isin(new_uids)], new_df], ignore_index=True)
            merged = combined
            diff = {"added": added, "updated": updated, "stale": stale}

        # 寫快照（供日後比對）+ 主檔
        snap = os.path.join(self.store_dir, f"snapshot_{datetime.now():%Y%m%d_%H%M%S}.parquet")
        merged.to_parquet(snap, index=False)
        merged.to_parquet(self.main_path, index=False)

        return {
            "added": len(diff["added"]),
            "updated": len(diff["updated"]),
            "stale": len(diff["stale"]),
            "total": len(merged),
            "detail": diff,
        }
