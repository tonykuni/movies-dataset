"""Build a Lifeline record – the persistent tracking object for an email."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def build_lifeline(
    uid: str,
    semantic: str,
    project: str,
    dept: str,
    risk_level: int = 0,
    *,
    status: str = "Pending",
    sla: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Lifeline = the single source of truth for this email's lifecycle.
    """
    record = {
        "UID": uid,
        "Project": project,
        "Dept": dept,
        "Category": semantic,
        "RiskLevel": int(risk_level),
        "Status": status,
        "SLA": sla,
        "CreatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "UpdatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if extra:
        record.update(extra)
    return record
