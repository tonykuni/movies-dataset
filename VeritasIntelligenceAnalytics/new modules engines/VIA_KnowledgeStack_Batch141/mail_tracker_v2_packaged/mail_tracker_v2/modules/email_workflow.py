"""Create a workflow task from classified email context."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .email_sla import compute_sla


# category → (task_type, default_team)
_ROUTING = {
    "Risk": ("RiskTask", "RiskTeam"),
    "Issue": ("IssueTask", "PM"),
    "Escalation": ("EscalationTask", "Manager"),
    "Delay": ("DelayTask", "PM"),
    "Decision": ("DecisionTask", "Manager"),
}


def workflow_task(
    uid: str,
    semantic: str,
    project: str,
    dept: str,
    risk_level: int,
    *,
    sla: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Produce a task ticket ready for a workflow / ticketing system.
    """
    sla = sla or compute_sla(semantic)
    task_type, team = _ROUTING.get(semantic, ("ActionTask", None))

    if team is None:
        team = f"{dept}_Owner" if dept and dept != "UnknownDept" else "General"

    return {
        "task_id": f"TASK_{uid}",
        "uid": uid,
        "type": task_type,
        "project": project,
        "dept": dept,
        "team": team,
        "risk_level": int(risk_level),
        "sla": sla,
        "status": "Pending",
        "priority": _priority_from_risk(risk_level),
    }


def _priority_from_risk(risk_level: int) -> str:
    if risk_level >= 7:
        return "P0"
    if risk_level >= 5:
        return "P1"
    if risk_level >= 3:
        return "P2"
    return "P3"
