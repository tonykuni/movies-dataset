"""利害關係人登錄層（合規版）。

只記錄『工作事實』：此人以什麼角色出現(寄件/收件/CC)、出現頻率、所屬單位(由 email domain/前綴推斷)、
首末出現時間、關聯到哪些案子。

明確不做：不建立私人檔案、不推測個性/動機、不做爽點死穴那類東西。
參與度評估(engagement)只給客觀類別佔位：active(常寄)/responsive(常被回)/cc_only/unknown，
真正的 unaware/resistant/neutral/supportive 由你人工標註，系統不臆測。
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
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Stakeholder:
    handle: str                       # 顯示名/email
    unit: str = ""                    # 推斷單位
    as_sender: int = 0
    as_recipient: int = 0
    as_cc: int = 0
    first_seen: str = ""
    last_seen: str = ""
    projects: set = field(default_factory=set)
    engagement: str = "unknown"       # 客觀類別；非心理側寫

    def total(self) -> int:
        return self.as_sender + self.as_recipient + self.as_cc


def _unit_of(handle: str) -> str:
    """由 email domain 或前綴粗略推斷單位，純輔助。"""
    h = handle.strip()
    if "@" in h:
        return h.split("@", 1)[1]
    m = re.match(r"^([A-Za-z]+)[_\-]", h)   # RD_Lin → RD
    return m.group(1).upper() if m else ""


def build_registry(records) -> dict[str, Stakeholder]:
    reg: dict[str, Stakeholder] = {}

    def touch(handle: str) -> Stakeholder:
        handle = handle.strip()
        if handle not in reg:
            reg[handle] = Stakeholder(handle=handle, unit=_unit_of(handle))
        return reg[handle]

    for rec in records:
        t = getattr(rec, "event_time", "") or ""
        proj = getattr(rec, "product", "") or getattr(rec, "thread_id", "")

        if rec.actor:
            s = touch(rec.actor)
            s.as_sender += 1
            s.projects.add(proj)
            s.first_seen = min(s.first_seen or t, t) if t else s.first_seen
            s.last_seen = max(s.last_seen, t)

        for cp in (rec.counterparts or "").split(";"):
            cp = cp.strip()
            if not cp or cp.upper() == "ALL":
                continue
            s = touch(cp)
            s.as_recipient += 1
            s.projects.add(proj)
            s.last_seen = max(s.last_seen, t)

    # 客觀參與度分類
    for s in reg.values():
        if s.as_sender >= 2:
            s.engagement = "active"
        elif s.as_sender == 1:
            s.engagement = "responsive"
        elif s.as_recipient or s.as_cc:
            s.engagement = "cc_only"
    return reg
