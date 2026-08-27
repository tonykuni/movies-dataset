"""
Mail Tracker V2 – email intelligence pipeline.

Same module layout as the original project, packaged for install with
modern pyproject.toml (PEP 621 + PEP 735 dependency groups).
"""

from .modules import (
    generate_uid_v2,
    parse_email,
    semantic_classify,
    map_project,
    map_dept,
    build_lifeline,
    compute_sla,
    SLA_POLICY,
    workflow_task,
)
from .pipeline import mail_tracker_v2, KNOWN_PROJECTS

__all__ = [
    "mail_tracker_v2",
    "KNOWN_PROJECTS",
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

__version__ = "2.1.0"
