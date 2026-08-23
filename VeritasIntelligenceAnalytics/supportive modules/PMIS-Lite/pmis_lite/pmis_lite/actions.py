"""追蹤事項擷取層。

從事件文字中找出『需要有人做的事』：請求動詞 + (負責人) + (期限)。
保守抽取：抓得到就標，抓不到的欄位留空，不臆造。
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

import re
from dataclasses import dataclass

# 請求/待辦的觸發詞（中英）
_TRIGGERS = [
    "請", "麻煩", "需要", "需", "務必", "盡快", "待", "追蹤", "確認", "回覆", "提供", "排",
    "todo", "to-do", "action", "follow up", "follow-up", "need to", "please", "by ",
    "pending", "asap",
]
_TRIGGER_RE = re.compile("|".join(re.escape(t) for t in _TRIGGERS), re.IGNORECASE)

# 期限：2026-06-30 / 6/30 / 下週 / next week / by Friday
_DUE_RE = re.compile(
    r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})"
    r"|(\d{1,2}[-/.]\d{1,2})(?!\d)"
    r"|(下週|下周|本週|本周|這週|月底|月初|週[一二三四五]|next week|this week|by \w+)",
    re.IGNORECASE,
)


@dataclass
class ActionItem:
    uid: str
    text: str
    owner: str = ""
    due: str = ""
    source_ref: str = ""


def extract_actions(records) -> list[ActionItem]:
    items: list[ActionItem] = []
    for rec in records:
        body = " ".join([getattr(rec, "title", ""), getattr(rec, "body", "")]).strip()
        if not body or not _TRIGGER_RE.search(body):
            continue
        # 以句子為單位找觸發句
        for sent in re.split(r"[。\.\n；;]", body):
            if _TRIGGER_RE.search(sent):
                due_m = _DUE_RE.search(sent)
                items.append(ActionItem(
                    uid=getattr(rec, "uid", ""),
                    text=sent.strip()[:120],
                    owner=getattr(rec, "actor", ""),
                    due=(due_m.group(0) if due_m else ""),
                    source_ref=getattr(rec, "source_ref", ""),
                ))
    return items
