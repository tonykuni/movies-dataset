"""統一 SSOT 資料格式 (schema)。

所有 adapter（Excel/CSV、Outlook、Gmail…）都把各自來源轉成這個統一格式，
核心引擎只認得這個格式 —— 這就是「萬用 / adapter 模式」的關鍵。

一筆 SSOT Record = 一個「事件」：誰、何時、做了什麼、屬哪個案子。
有了事件序列，才能做關聯分析、process mining、進度比對。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


# SSOT 欄位（統一格式）。adapter 負責把來源欄位對應到這些欄位。
SSOT_COLUMNS = [
    "uid",            # 自動編號（WBS 式穩定 ID）
    "source_type",    # 來源：excel_csv / outlook / gmail ...
    "source_ref",     # 來源定位（檔名+列號 / 郵件 message-id）
    "event_time",     # 事件時間（ISO 字串）
    "actor",          # 行為人/負責人/寄件人
    "counterparts",   # 相關方（收件人/CC/對口單位），以 ; 分隔
    "title",          # 主旨/項目名稱
    "body",           # 內文/說明（已治亂碼、已清理）
    "raw_keys",       # 原始來源用到的關鍵詞（供探勘層挖同義字）
    "product",        # 分類：產品線
    "topic",          # 分類：主題類別
    "status",         # 分類：狀態
    "thread_id",      # 討論串/案件聚合鍵
    "content_hash",   # 內容雜湊（去重 + 編號用）
    "ingested_at",    # 寫入時間
]


@dataclass
class Record:
    title: str = ""
    body: str = ""
    actor: str = ""
    counterparts: str = ""
    event_time: str = ""
    source_type: str = ""
    source_ref: str = ""
    raw_keys: str = ""
    product: str = ""
    topic: str = ""
    status: str = ""
    thread_id: str = ""
    uid: str = ""
    content_hash: str = ""
    ingested_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {c: d.get(c, "") for c in SSOT_COLUMNS}
