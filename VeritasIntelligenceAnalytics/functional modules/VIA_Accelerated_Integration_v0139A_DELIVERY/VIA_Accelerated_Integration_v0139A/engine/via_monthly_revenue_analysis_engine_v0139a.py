from typing import Any

from .via_domain_engine_v0139a import def_compute_monthly_revenue_analysis


COMPONENT_ID = "VIA_TW_Monthly_Revenue_Analysis_Engine_v0139A"


def def_run(revenue: Any, classification: Any) -> tuple[Any, Any]:
    return def_compute_monthly_revenue_analysis(revenue, classification)
