"""SLA policy lookup by semantic category."""

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

from typing import Dict


# category → response-time SLA
SLA_POLICY: Dict[str, str] = {
    "Risk": "4h",
    "Escalation": "2h",
    "Issue": "8h",
    "Delay": "12h",
    "Decision": "16h",
    "Action": "24h",
}

DEFAULT_SLA = "24h"


def compute_sla(semantic: str) -> str:
    """Return SLA string for the given semantic category."""
    return SLA_POLICY.get(semantic, DEFAULT_SLA)
