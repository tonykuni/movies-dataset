"""Map an email to a known project code."""

from __future__ import annotations

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
