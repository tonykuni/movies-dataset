"""額外資訊注入 adapter（把信件以外的補充資訊加進 SSOT）。

用途：自動讀取信件之後，你常還想補進「信裡沒有、但你知道」的資訊：
  - 某討論串其實對應 PO-20260629-088
  - 某案負責人應改為某人（人工覆寫）
  - 某事項的線下決策/電話結論
  - 從別系統來的補充事實

作法：你維護一個簡單的 CSV/JSON（可用滑鼠在 Excel 點一點），本 adapter 讀進來：
  (A) 當成獨立的補充事件 Record（source_type='supplement'，清楚可辨）
  (B) 或依 relate_to 鍵，把欄位「附加」到既有 Record（enrich，不覆寫原文）

治理：append-only，補充一律加註來源=人工，不竄改原始郵件內容；可追溯。
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

import csv
import json
import os

SUPPLEMENT_FIELDS = ("relate_to", "title", "body", "actor", "product", "topic", "status", "note")


def _rows_from_file(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    # CSV
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


class SupplementAdapter:
    """讀使用者維護的補充資訊表，產生補充 Record 或 enrich 既有 Record。"""

    def __init__(self, path: str, mode: str = "record"):
        self.path = path
        self.mode = mode            # 'record'=獨立補充事件；'enrich'=附加到既有
        self.source_type = "supplement"

    def available(self) -> bool:
        return os.path.exists(self.path)

    def fetch(self):
        """mode='record'：把每列補充當成一筆 source_type='supplement' 的 Record。"""
        from ..schema import Record
        for r in _rows_from_file(self.path):
            note = (r.get("note") or "").strip()
            body = (r.get("body") or "").strip()
            full_body = (body + ("　〔補充：" + note + "〕" if note else "")).strip()
            yield Record(
                title=(r.get("title") or "（補充資訊）").strip(),
                body=full_body,
                actor=(r.get("actor") or "人工補充").strip(),
                event_time=(r.get("event_time") or "").strip(),
                source_type=self.source_type,
                source_ref=f"supplement:{os.path.basename(self.path)}",
                raw_keys=(r.get("title") or "") + " " + note,
                product=(r.get("product") or "").strip(),
                topic=(r.get("topic") or "").strip(),
                status=(r.get("status") or "").strip(),
                thread_id=(r.get("relate_to") or "").strip(),
            )


def enrich_records(records, supplement_path: str) -> int:
    """mode='enrich'：依 relate_to 鍵，把補充欄位附加到既有 Record（不覆寫原 body）。

    relate_to 可比對 thread_id / product / uid / source_ref。回傳成功附加的筆數。
    """
    rows = _rows_from_file(supplement_path)
    if not rows:
        return 0
    n = 0
    for r in rows:
        key = (r.get("relate_to") or "").strip()
        if not key:
            continue
        note = (r.get("note") or r.get("body") or "").strip()
        for rec in records:
            if key in (rec.thread_id, rec.product, rec.uid, rec.source_ref, rec.title):
                # append-only：補充附加在 body 尾端並標記，不動原文
                if note and note not in rec.body:
                    rec.body = (rec.body + f"\n〔人工補充：{note}〕").strip()
                # 欄位補空（只補不覆寫）
                for fld in ("product", "topic", "status", "actor"):
                    v = (r.get(fld) or "").strip()
                    if v and not getattr(rec, fld, ""):
                        setattr(rec, fld, v)
                n += 1
    return n


# adapter 協定別名
SupplementAdapter.read = SupplementAdapter.fetch
