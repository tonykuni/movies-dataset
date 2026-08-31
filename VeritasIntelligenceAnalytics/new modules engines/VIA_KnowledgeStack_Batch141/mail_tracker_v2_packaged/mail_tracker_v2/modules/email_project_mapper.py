"""Map an email to a known project code."""

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
from typing import Any, Dict, List, Optional


# Common project-code patterns (Pxxxx, PROJ-xxx, etc.)
_PROJECT_PATTERN = re.compile(
    r"\b(P\d{3,5}|PROJ[-_]?\d{2,5}|PRJ[-_]?\d{2,5})\b",
    re.IGNORECASE,
)


def map_project(
    email: Dict[str, Any],
    known_projects: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Resolve project from subject/body against a known list,
    with regex fallback for common project-code formats.
    """
    subject = email.get("subject") or ""
    body = email.get("body") or ""
    blob = f"{subject}\n{body}"

    known = known_projects or []

    # 1. Exact / substring match against known list (case-insensitive)
    blob_lower = blob.lower()
    for p in known:
        if p.lower() in blob_lower:
            return {
                "project": p,
                "method": "known_list",
                "confidence": 0.95,
            }

    # 2. Regex discovery
    m = _PROJECT_PATTERN.search(blob)
    if m:
        code = m.group(1).upper().replace("_", "-")
        return {
            "project": code,
            "method": "regex",
            "confidence": 0.7,
        }

    return {
        "project": "UnknownProject",
        "method": "none",
        "confidence": 0.0,
    }
