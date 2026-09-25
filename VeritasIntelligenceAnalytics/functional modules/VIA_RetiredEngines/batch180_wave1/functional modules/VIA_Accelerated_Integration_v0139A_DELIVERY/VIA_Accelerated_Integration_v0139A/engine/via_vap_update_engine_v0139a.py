# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
from pathlib import Path
from typing import Any, Mapping

from .via_domain_engine_v0139a import def_render_vap_html, def_validate_vap_visual_lock


COMPONENT_ID = "VIA_VAP_Integration_Update_Engine_v0139A"


def def_render(
    output_path: Path,
    group_index: Any,
    flow_daily: Any,
    flow_summary: Any,
    revenue_group: Any,
    evidence: Mapping[str, Any],
) -> list[str]:
    def_render_vap_html(
        output_path,
        group_index,
        flow_daily,
        flow_summary,
        revenue_group,
        evidence,
    )
    return def_validate_vap_visual_lock(output_path)
