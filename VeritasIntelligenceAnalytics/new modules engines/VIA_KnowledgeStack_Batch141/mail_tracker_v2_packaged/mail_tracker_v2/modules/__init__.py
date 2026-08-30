"""Mail Tracker V2 – modular email intelligence pipeline."""

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
