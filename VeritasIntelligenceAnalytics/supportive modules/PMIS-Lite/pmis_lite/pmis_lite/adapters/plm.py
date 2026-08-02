"""PLM adapter（通用匯出版）。

PLM 系統(Windchill / Teamcenter / Agile / SAP PLM…)各家 API 不同，
最務實、最合規的通用作法：用『你在 PLM 內有權限匯出的 CSV/Excel』+ 欄位對應。

設定檔給一份 field_map：把該 PLM 匯出的欄名對到 SSOT 欄位。
這樣同一支 adapter 套不同 PLM 只要換 field_map，符合『萬用』精神。
"""
from __future__ import annotations

import os
from typing import Iterable

import pandas as pd

from ..schema import Record
from ..encoding import detect_file_encoding, repair_mojibake


class PLMExportAdapter:
    source_type = "plm"

    def __init__(self, path: str, field_map: dict | None = None, audit=None):
        self.path = path
        # PLM 匯出欄名 → SSOT 欄位
        self.field_map = field_map or {
            "Object": "title", "Name": "title", "物件名稱": "title",
            "Description": "body", "說明": "body",
            "Owner": "actor", "負責人": "actor", "Responsible": "actor",
            "State": "status", "狀態": "status", "Lifecycle State": "status",
            "Modified": "event_time", "更新日期": "event_time",
            "Product": "product", "產品": "product",
        }
        self.audit = audit

    def _iter_files(self):
        if os.path.isdir(self.path):
            for n in sorted(os.listdir(self.path)):
                if n.lower().endswith((".csv", ".xlsx", ".xls")):
                    yield os.path.join(self.path, n)
        else:
            yield self.path

    def _load(self, fpath: str) -> pd.DataFrame:
        if fpath.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(fpath, dtype=str).fillna("")
        enc = detect_file_encoding(fpath)
        return pd.read_csv(fpath, encoding=enc, dtype=str, keep_default_na=False)

    def read(self) -> Iterable[Record]:
        a = self.audit.audit("plm") if self.audit else None
        for fpath in self._iter_files():
            try:
                df = self._load(fpath)
            except Exception as e:
                if a:

                    a.failures.append((os.path.basename(fpath), f"load:{e.__class__.__name__}"))
                continue
            for idx, row in df.iterrows():
                if a:
                    a.seen += 1
                rec = Record(source_type=self.source_type)
                rec.source_ref = f"plm::{os.path.basename(fpath)}::row{idx + 2}"
                bits = []
                for col in df.columns:
                    val = repair_mojibake(str(row[col]).strip())
                    if not val:
                        continue
                    bits.append(f"{col}={val}")
                    ssot_field = self.field_map.get(col)
                    if ssot_field and not getattr(rec, ssot_field):
                        setattr(rec, ssot_field, val)
                rec.raw_keys = " | ".join(bits)
                if not (rec.title or rec.body):
                    if a:

                        a.failures.append((rec.source_ref, "no_title_or_body"))
                    continue
                if a:
                    a.extracted += 1
                yield rec
