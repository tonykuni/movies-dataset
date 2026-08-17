"""VIA Contract Interface Engine central parameters."""

from __future__ import annotations

from pathlib import Path


# def 01 ENGINE PARAMETERS
ENGINE_NAME = "VIA Contract Interface Engine"
ENGINE_VERSION = "0.2.0"
ENGINE_COMPATIBILITY = ">=0.2,<1.0"

# def 02 CONTRACT PARAMETERS
MODULE_NAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]{2,63}$"
SEMANTIC_VERSION_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$"
PRIMARY_URN_PATTERN = r"^VIA-MOD-(PY|PS|JS|JSON|HTML)-[A-Z0-9-]{2,32}-\d{8}-\d{4,}$"
DEPENDENCY_URN_PATTERN = r"^(?:VIA-MOD-(?:PY|PS|JS|JSON|HTML)-[A-Z0-9-]{2,32}-\d{8}-\d{4,}|urn:via:[A-Za-z0-9:._-]+)$"
DEFAULT_SUBSYSTEM = "VIA"
DEFAULT_AUTHOR = "VIA"
DEFAULT_LANGUAGE = "PY"
DEFAULT_CAPABILITY_MAX_LENGTH = 24

# def 03 EXECUTION PARAMETERS
DEFAULT_ASYNC_TIMEOUT_SECONDS = 30.0
ALLOW_PROVIDER_NAME_FALLBACK = False
ALLOW_UNTYPED_PARAMETERS = False

# def 04 SSOT REGISTRY PARAMETERS
DEFAULT_SSOT_DIRECTORY = Path(".via_ssot_registry")
DEFAULT_SSOT_DATABASE = DEFAULT_SSOT_DIRECTORY / "via_ssot_registry.sqlite3"
DEFAULT_WATCHDOG_INTERVAL_SECONDS = 1.0
DEFAULT_WATCHDOG_EXTENSIONS = frozenset({".py", ".json"})
DEFAULT_HEALTH_WORKERS = 4
URN_SEQUENCE_WIDTH = 4

# def 05 UI PARAMETERS
DEFAULT_UI_TITLE = "VIA Contract-Driven Command Console"
DEFAULT_UI_LANGUAGE = "zh-Hant"
DEFAULT_ENDPOINT_PREFIX = "/via/commands"
DEFAULT_SUBMIT_LABEL = "執行指令"
ALLOWED_UI_WIDGETS = frozenset(
    {
        "auto",
        "hidden",
        "text",
        "textarea",
        "number",
        "select",
        "checkbox",
        "color",
        "date",
        "datetime-local",
        "email",
        "password",
    }
)

# def 06 OUTPUT PARAMETERS
DEFAULT_OUTPUT_DIRECTORY = Path("via_contract_engine_output")
SCHEMA_CATALOG_FILENAME = "via_command_schema_catalog.json"
HTML_CONSOLE_FILENAME = "via_contract_command_console.html"
TWIN_REPORT_JSON_FILENAME = "via_contract_twin_report.json"
TWIN_REPORT_HTML_FILENAME = "via_contract_twin_report.html"
SSOT_SNAPSHOT_FILENAME = "via_ssot_registry_snapshot.json"
