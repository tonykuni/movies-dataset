from typing import Any

from .via_domain_engine_v0139a import def_build_stock_group_classification


COMPONENT_ID = "VIA_TW_Stock_Group_Classification_Engine_v0139A"


def def_run(classification: Any) -> Any:
    return def_build_stock_group_classification(classification)
