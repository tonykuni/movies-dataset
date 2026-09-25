"""
Mail Tracker V2 – email intelligence pipeline.

Same module layout as the original project, packaged for install with
modern pyproject.toml (PEP 621 + PEP 735 dependency groups).
"""

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
