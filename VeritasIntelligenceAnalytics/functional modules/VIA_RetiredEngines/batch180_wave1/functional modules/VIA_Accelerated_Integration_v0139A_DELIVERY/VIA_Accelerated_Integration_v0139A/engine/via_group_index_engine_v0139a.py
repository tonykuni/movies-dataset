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
from typing import Any

from .via_domain_engine_v0139a import def_compute_group_index


COMPONENT_ID = "VIA_TW_Group_Index_Engine_v0139A"


def def_run(
    prices: Any,
    classification: Any,
    group_column: str = "Sector",
    weighting: str = "equal",
    base_value: float = 100.0,
) -> Any:
    return def_compute_group_index(
        prices,
        classification,
        group_column=group_column,
        weighting=weighting,
        base_value=base_value,
    )
