"""SLA policy lookup by semantic category."""

from __future__ import annotations

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
