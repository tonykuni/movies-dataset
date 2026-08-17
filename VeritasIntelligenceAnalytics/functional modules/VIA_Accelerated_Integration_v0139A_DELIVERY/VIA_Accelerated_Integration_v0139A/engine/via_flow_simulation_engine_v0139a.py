from typing import Any

from .via_domain_engine_v0139a import def_compute_flow_simulation


COMPONENT_ID = "VIA_Flow_Simulation_Engine_v0139A"


def def_run(
    flows: Any,
    prices: Any,
    classification: Any,
    short_window: int = 3,
    long_window: int = 5,
) -> tuple[Any, Any]:
    return def_compute_flow_simulation(
        flows,
        prices,
        classification,
        short_window=short_window,
        long_window=long_window,
    )
