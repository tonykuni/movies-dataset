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
