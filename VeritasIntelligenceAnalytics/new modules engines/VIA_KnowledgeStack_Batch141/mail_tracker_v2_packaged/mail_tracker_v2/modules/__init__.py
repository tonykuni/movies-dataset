"""Mail Tracker V2 – modular email intelligence pipeline."""

from .email_identity import generate_uid_v2
from .email_parser import parse_email
from .email_semantic import semantic_classify
from .email_project_mapper import map_project
from .email_dept_mapper import map_dept
from .email_lifeline import build_lifeline
from .email_sla import compute_sla, SLA_POLICY
from .email_workflow import workflow_task

__all__ = [
    "generate_uid_v2",
    "parse_email",
    "semantic_classify",
    "map_project",
    "map_dept",
    "build_lifeline",
    "compute_sla",
    "SLA_POLICY",
    "workflow_task",
]
