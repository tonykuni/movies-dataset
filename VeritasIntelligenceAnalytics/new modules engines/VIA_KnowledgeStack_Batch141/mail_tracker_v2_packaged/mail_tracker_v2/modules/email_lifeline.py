"""Build a Lifeline record – the persistent tracking object for an email."""

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
