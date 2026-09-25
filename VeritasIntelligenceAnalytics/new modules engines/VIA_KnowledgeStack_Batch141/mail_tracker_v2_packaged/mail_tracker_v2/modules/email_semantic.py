"""Rule-based semantic classification of email intent."""

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


# (category, keywords, base_risk) – first match wins (order = priority)
_RULES: List[Tuple[str, List[str], int]] = [
    ("Risk", ["risk", "hazard", "critical", "blocker", "showstopper", "風險", "危機"], 7),
    ("Escalation", ["escalate", "escalation", "approve", "approval", "sign-off", "簽核", "升級"], 5),
    ("Issue", ["issue", "bug", "defect", "problem", "incident", "問題", "異常"], 4),
    ("Delay", ["delay", "slip", "postpone", "behind schedule", "延遲", "時程"], 3),
    ("Decision", ["decision", "decide", "resolved", "結論", "決議"], 2),
    ("Action", ["action", "todo", "follow up", "please", "kindly", "請", "協助"], 1),
]


def semantic_classify(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return category + risk_level + matched signals.

    Backwards-compatible: callers that expect a plain string can use
    result["category"].
    """
    subject = (email.get("subject") or "").lower()
    body = (email.get("body") or "").lower()
    blob = f"{subject}\n{body}"

    for category, keywords, risk in _RULES:
        hits = [kw for kw in keywords if kw in blob]
        if hits:
            return {
                "category": category,
                "risk_level": risk,
                "matched_keywords": hits,
                "confidence": min(0.95, 0.55 + 0.1 * len(hits)),
            }

    return {
        "category": "Action",
        "risk_level": 0,
        "matched_keywords": [],
        "confidence": 0.4,
    }


def semantic_category_only(email: Dict[str, Any]) -> str:
    """Convenience wrapper that returns only the category string."""
    return semantic_classify(email)["category"]
