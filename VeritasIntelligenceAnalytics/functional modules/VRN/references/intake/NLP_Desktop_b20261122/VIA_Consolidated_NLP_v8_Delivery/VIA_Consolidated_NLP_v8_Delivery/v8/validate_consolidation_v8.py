from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "VIA_SSOT_Engine_Registry_v8.json"
DEFAULT_CORE = ROOT / "v8" / "via_consolidated_nlp_v8.py"


def validate(registry_path: Path, core_path: Path) -> dict[str, object]:
    errors: list[str] = []
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    engines = registry.get("engines", [])
    modules = [item for item in engines if item.get("kind") == "consolidated_module"]
    orchestrators = [item for item in engines if item.get("kind") == "canonical_orchestrator"]
    if registry.get("schema") != "VIA_SSOT_CONSOLIDATED_MODULE_REGISTRY/8.0":
        errors.append("registry schema is not v8 consolidated")
    if len(modules) != 7:
        errors.append(f"expected 7 consolidated modules, got {len(modules)}")
    if len(orchestrators) != 1 or orchestrators[0].get("engine_id") != "VIA-ENG-022":
        errors.append("missing VIA-ENG-022 canonical orchestrator")
    ids = [str(item.get("engine_id")) for item in engines]
    if len(ids) != len(set(ids)):
        errors.append("duplicate canonical IDs")
    aliases = registry.get("legacy_aliases", {})
    if len(aliases) < 18:
        errors.append("legacy alias map is incomplete")
    if registry.get("source_policy", {}).get("automatic_code_execution") is not False:
        errors.append("automatic code execution must remain false")
    if registry.get("system", {}).get("canonical_module_count") != 7:
        errors.append("system canonical_module_count must be 7")
    text = core_path.read_text(encoding="utf-8")
    for required in ("ast.parse", "source_is_immutable", "execution_authorized", "artifact_payloads_v8", "CONSOLIDATED_MODULES"):
        if required not in text:
            errors.append(f"core missing required marker: {required}")
    return {
        "schema": "VIA_CONSOLIDATED_NLP_VALIDATION/8.0",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "canonical_modules": len(modules),
        "legacy_aliases": len(aliases),
        "contracts": len(registry.get("contracts", [])),
        "gates": len(registry.get("gates", [])),
        "core_bytes": core_path.stat().st_size if core_path.is_file() else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--core", type=Path, default=DEFAULT_CORE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.registry, args.core)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
