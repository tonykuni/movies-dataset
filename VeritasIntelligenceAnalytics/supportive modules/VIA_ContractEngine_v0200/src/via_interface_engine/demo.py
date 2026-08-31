"""Build and execute the complete local reference engine."""

from __future__ import annotations
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

import json
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_SSOT_DATABASE,
    HTML_CONSOLE_FILENAME,
    SCHEMA_CATALOG_FILENAME,
    SSOT_SNAPSHOT_FILENAME,
    TWIN_REPORT_HTML_FILENAME,
    TWIN_REPORT_JSON_FILENAME,
)
from .contracts import ModuleContext
from .examples import CoreLogger, DBConnection, OrderProcessorModule
from .executor import VIASmartExecutor
from .providers import ProviderRegistry
from .registry import VIACommandRegistry
from .ssot import VIASSOTRegistry
from .twin import VIADigitalTwinTester
from .ui import SchemaToHTMLRenderer


# def 01 DEMO PARAMETERS
DEMO_RUN_ID = "RUN_VIA_CONTRACT_ENGINE_DEMO"
DEMO_SUBSYSTEM = "VIA_DEMO"
DEMO_VALID_PAYLOAD = {"order_id": "ORD-20260817-001", "amount": "500", "currency": "TWD"}
DEMO_INVALID_PAYLOAD = {"order_id": "ORD-20260817-002", "amount": "五百", "currency": "TWD"}


def def_build_reference_engine(
    ssot_database_path: Path = DEFAULT_SSOT_DATABASE,
) -> tuple[
    ProviderRegistry,
    VIACommandRegistry,
    VIASmartExecutor,
]:
    providers = ProviderRegistry()
    providers.register(DBConnection, DBConnection, name="db")
    providers.register(CoreLogger, CoreLogger, name="logger")

    ssot_registry = VIASSOTRegistry(ssot_database_path)
    registry = VIACommandRegistry(providers, ssot_registry)
    context = ModuleContext(
        run_id=DEMO_RUN_ID,
        subsystem=DEMO_SUBSYSTEM,
        config={"mode": "sandbox", "canonical_mutation": False},
    )
    registry.register(OrderProcessorModule(), context)
    return providers, registry, VIASmartExecutor(registry)


def def_run_demo(output_directory: Path) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=True)
    ssot_database_path = output_directory / "via_ssot_registry.sqlite3"
    _, registry, executor = def_build_reference_engine(ssot_database_path)

    valid_result = executor.execute_safe("OrderProcessor", DEMO_VALID_PAYLOAD)
    invalid_result = executor.execute_safe("OrderProcessor", DEMO_INVALID_PAYLOAD)
    renderer = SchemaToHTMLRenderer()
    twin = VIADigitalTwinTester(renderer)
    twin_report = twin.run_registry(registry)

    schema_path = output_directory / SCHEMA_CATALOG_FILENAME
    html_path = output_directory / HTML_CONSOLE_FILENAME
    twin_json_path = output_directory / TWIN_REPORT_JSON_FILENAME
    twin_html_path = output_directory / TWIN_REPORT_HTML_FILENAME
    ssot_snapshot_path = output_directory / SSOT_SNAPSHOT_FILENAME

    schema_path.write_text(
        json.dumps(registry.schema_catalog(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    html_path.write_text(renderer.render_catalog_document(registry), encoding="utf-8")
    twin_json_path.write_text(twin.report_json(twin_report), encoding="utf-8")
    twin_html_path.write_text(twin.render_report_html(twin_report), encoding="utf-8")
    health_results = registry.health_check_all()
    ssot_snapshot_path.write_text(
        json.dumps(
            registry.ssot.snapshot_catalog(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    summary = {
        "gate": twin_report.gate,
        "valid_execution": valid_result.model_dump(mode="json"),
        "invalid_execution": invalid_result.model_dump(mode="json"),
        "health_results": health_results,
        "outputs": {
            "schema": str(schema_path.resolve()),
            "html_console": str(html_path.resolve()),
            "twin_json": str(twin_json_path.resolve()),
            "twin_html": str(twin_html_path.resolve()),
            "ssot_snapshot": str(ssot_snapshot_path.resolve()),
            "ssot_database": str(ssot_database_path.resolve()),
        },
    }
    registry.shutdown()
    return summary
