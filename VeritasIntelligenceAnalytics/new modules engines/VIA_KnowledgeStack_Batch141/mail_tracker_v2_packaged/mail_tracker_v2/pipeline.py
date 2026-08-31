"""
Mail Tracker V2 – main orchestration pipeline.

Flow:
  raw email
    → parse
    → project / dept mapping
    → UID
    → semantic classification (+ risk)
    → lifeline
    → workflow task
    → unified result
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

import json
from typing import Any, Dict, List, Optional

from mail_tracker_v2.modules.email_identity import generate_uid_v2
from mail_tracker_v2.modules.email_parser import parse_email
from mail_tracker_v2.modules.email_semantic import semantic_classify
from mail_tracker_v2.modules.email_project_mapper import map_project
from mail_tracker_v2.modules.email_dept_mapper import map_dept
from mail_tracker_v2.modules.email_lifeline import build_lifeline
from mail_tracker_v2.modules.email_sla import compute_sla
from mail_tracker_v2.modules.email_workflow import workflow_task


KNOWN_PROJECTS: List[str] = ["P2382", "P3101", "P9999"]


def mail_tracker_v2(
    raw_email: Dict[str, Any],
    *,
    known_projects: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    End-to-end processing of a single email.
    Returns a structured tracking payload.
    """
    projects = known_projects if known_projects is not None else KNOWN_PROJECTS

    email = parse_email(raw_email)
    project_info = map_project(email, projects)
    dept_info = map_dept(email)
    project = project_info["project"]
    dept = dept_info["dept"]

    uid = generate_uid_v2({**email, "project": project, "dept": dept})

    sem = semantic_classify(email)
    category = sem["category"]
    risk_level = sem["risk_level"]

    sla = compute_sla(category)

    lifeline = build_lifeline(
        uid=uid,
        semantic=category,
        project=project,
        dept=dept,
        risk_level=risk_level,
        sla=sla,
        extra={
            "MatchedKeywords": sem.get("matched_keywords", []),
            "SemanticConfidence": sem.get("confidence"),
            "ProjectMethod": project_info.get("method"),
            "DeptSource": dept_info.get("source"),
        },
    )

    task = workflow_task(
        uid=uid,
        semantic=category,
        project=project,
        dept=dept,
        risk_level=risk_level,
        sla=sla,
    )

    return {
        "UID": uid,
        "Email": email,
        "Semantic": {
            "category": category,
            "risk_level": risk_level,
            "matched_keywords": sem.get("matched_keywords", []),
            "confidence": sem.get("confidence"),
        },
        "Project": project_info,
        "Dept": dept_info,
        "SLA": sla,
        "Lifeline": lifeline,
        "Task": task,
    }


def main() -> None:
    sample = {
        "sender": "rd_lead@example.com",
        "receiver": "pm@example.com",
        "subject": "P2382 risk on validation schedule",
        "body": "We see potential risk and delay on validation phase.",
        "timestamp": "2026-08-25 16:50",
    }
    result = mail_tracker_v2(sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
