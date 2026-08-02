"""自動編號層（WBS 式穩定 ID）。

格式： {prefix}-{domain}-{hash}
  - prefix / domain 來自 config（換職位/換領域只改這兩段）
  - hash 由「內容」算出 → 同一件事永遠得到同一個 ID（穩定、可重跑、不需人工編號）

這正是回應「功能群組抗拒額外工作」的設計：沒有人需要手動編號，
編號是系統內建、自動、從內容長出來的。
"""
from __future__ import annotations

import hashlib


def content_hash(*parts: str) -> str:
    """以內容算 SHA-1，取前段當穩定指紋。"""
    joined = "\u0001".join((p or "").strip().lower() for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def make_uid(prefix: str, domain: str, chash: str, hash_len: int = 6) -> str:
    return f"{prefix}-{domain}-{chash[:hash_len].upper()}"
