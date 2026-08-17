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
