"""Excel / CSV adapter（第一個示範來源）。

很多人拿 Excel 當分析底稿，所以這個 adapter 不只讀值，還盡量讀懂結構：
  - 多工作表（每張表都讀）
  - 自動治亂碼（CSV 偵測編碼；字串做 mojibake 修復）
  - 欄位語意對應：用模糊比對把「主旨/負責人/日期…」對到 SSOT 欄位

把每一列當成一個「事件」，轉成統一 Record。
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
from typing import Iterable

import pandas as pd

from ..schema import Record
from ..encoding import detect_file_encoding, repair_mojibake


# 來源欄名 → SSOT 欄位 的模糊對應（小寫比對；可自由擴充）
_FIELD_HINTS = {
    "title": ["主旨", "標題", "項目", "工作項目", "事項", "subject", "title", "item", "task"],
    "body": ["內容", "說明", "描述", "備註", "進度說明", "body", "description", "note", "detail"],
    "actor": ["負責人", "負責", "owner", "assignee", "寄件人", "from", "承辦"],
    "counterparts": ["相關方", "對口", "收件人", "cc", "to", "單位", "stakeholder"],
    "event_time": ["日期", "時間", "date", "time", "更新日", "deadline", "due", "截止"],
    "product": ["產品", "產品線", "product", "line", "機種"],
    "topic": ["主題", "類別", "topic", "category", "階段", "phase"],
    "status": ["狀態", "進度", "status", "state", "progress"],
}


def _match_column(colname: str) -> str | None:
    low = str(colname).strip().lower()
    for ssot_field, hints in _FIELD_HINTS.items():
        for h in hints:
            if h in low:
                return ssot_field
    return None


def _clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return repair_mojibake(str(val).strip())


class ExcelCsvAdapter:
    source_type = "excel_csv"

    def __init__(self, path: str, audit=None):
        self.path = path
        self.audit = audit

    def _iter_files(self):
        if os.path.isdir(self.path):
            for name in sorted(os.listdir(self.path)):
                if name.lower().endswith((".xlsx", ".xls", ".csv", ".tsv")):
                    yield os.path.join(self.path, name)
        else:
            yield self.path

    def _read_frame(self, fpath: str):
        """回傳 {sheet_name: DataFrame}。CSV 視為單一 sheet。"""
        low = fpath.lower()
        if low.endswith((".csv", ".tsv")):
            enc = detect_file_encoding(fpath)
            sep = "\t" if low.endswith(".tsv") else ","
            df = pd.read_csv(fpath, encoding=enc, sep=sep, dtype=str, keep_default_na=False)
            return {os.path.basename(fpath): df}
        # Excel：讀全部工作表
        sheets = pd.read_excel(fpath, sheet_name=None, dtype=str)
        return {k: v.fillna("") for k, v in sheets.items()}

    def read(self) -> Iterable[Record]:
        a = self.audit.audit("excel_csv") if self.audit else None
        for fpath in self._iter_files():
            try:
                frames = self._read_frame(fpath)
            except Exception as e:
                print(f"  [warn] 略過無法讀取的檔案 {fpath}: {e}")
                if a:

                    a.failures.append((os.path.basename(fpath), f"read_error:{e.__class__.__name__}"))
                continue

            for sheet_name, df in frames.items():
                if df.empty:
                    continue
                colmap = {c: _match_column(c) for c in df.columns}

                for idx, row in df.iterrows():
                    if a:
                        a.seen += 1
                    rec = Record(source_type=self.source_type)
                    rec.source_ref = f"{os.path.basename(fpath)}::{sheet_name}::row{idx + 2}"
                    raw_bits = []

                    for col, ssot_field in colmap.items():
                        val = _clean(row[col])
                        if not val:
                            continue
                        raw_bits.append(f"{col}={val}")
                        if ssot_field and not getattr(rec, ssot_field):
                            setattr(rec, ssot_field, val)

                    # 沒對到標題時，用整列當標題，確保不遺漏
                    if not rec.title and raw_bits:
                        rec.title = raw_bits[0].split("=", 1)[-1]
                    rec.raw_keys = " | ".join(raw_bits)

                    if not (rec.title or rec.body):
                        if a:

                            a.failures.append((rec.source_ref, "empty_row"))
                        continue
                    if a:
                        a.extracted += 1
                    yield rec
