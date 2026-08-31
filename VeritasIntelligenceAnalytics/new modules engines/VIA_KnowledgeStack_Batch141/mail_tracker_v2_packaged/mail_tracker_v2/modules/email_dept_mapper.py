"""Infer owning department from sender / receiver addresses."""

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
from typing import Any, Dict, List, Tuple


# (dept_code, patterns) – checked in order
_DEPT_RULES: List[Tuple[str, List[str]]] = [
    ("RD", ["rd", "r&d", "research", "dev", "developer", "engineering"]),
    ("ME", ["me", "mechanical", "mech"]),
    ("QA", ["qa", "quality", "qc", "test"]),
    ("PM", ["pm", "project.manager", "program.manager", "pmo"]),
    ("Finance", ["fin", "finance", "accounting", "cfo", "controller"]),
    ("Sales", ["sales", "account", "bd", "business.development"]),
    ("Ops", ["ops", "operation", "supply", "logistics"]),
    ("HR", ["hr", "human.resources", "people"]),
]


def _match_dept(address: str) -> str | None:
    addr = (address or "").lower()
    local = addr.split("@")[0] if "@" in addr else addr
    for dept, patterns in _DEPT_RULES:
        for p in patterns:
            # word-ish boundary to avoid "me" matching inside "team"
            if re.search(rf"(?:^|[._\-+]){re.escape(p)}(?:[._\-+]|$)", local):
                return dept
            if p in local and len(p) >= 3:
                return dept
    return None


def map_dept(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Infer department primarily from sender, falling back to receiver.
    """
    sender = email.get("sender") or ""
    receiver = email.get("receiver") or ""

    dept = _match_dept(sender)
    source = "sender"
    if not dept:
        dept = _match_dept(receiver)
        source = "receiver"

    if not dept:
        return {
            "dept": "UnknownDept",
            "source": None,
            "confidence": 0.0,
        }

    return {
        "dept": dept,
        "source": source,
        "confidence": 0.85 if source == "sender" else 0.6,
    }
