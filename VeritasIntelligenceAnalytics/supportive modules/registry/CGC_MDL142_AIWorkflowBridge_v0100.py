#!/usr/bin/env python3
"""CGC_MDL142_AIWorkflowBridge_v0100 — AI 模組指令、AST 與多代理接棒橋接治理模組。"""

from __future__ import annotations

# ============================================================================
# 01. PARAMETERS
# ============================================================================

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence


MODULE_ID = "CGC_MDL142"
MODULE_VERSION = "0100"
MODULE_STATUS = "REGISTRATION_PROPOSAL"
SUPPORTIVE_ROOT = Path(__file__).resolve().parents[1]
AI_WORKFLOW_ROOT = SUPPORTIVE_ROOT / "20_Registry_SSOT" / "VIA_AI_Workflow_v0100"
AI_WORKFLOW_ENTRY = AI_WORKFLOW_ROOT / "src" / "via_ai_workflow.py"
AI_REGISTRY = AI_WORKFLOW_ROOT / "registry" / "ai_module_registry.v0100.json"
AI_BRIDGE_CONFIG = AI_WORKFLOW_ROOT / "config" / "VIA_MotherSystem_Database_Bridge.v0100.json"


# ============================================================================
# 02. BRIDGE CONTRACT
# ============================================================================


def module_contract() -> dict[str, object]:
    """Return the stable contract consumed by registry and mother-system scans."""
    return {
        "module_id": MODULE_ID,
        "version": MODULE_VERSION,
        "status": MODULE_STATUS,
        "role": "AI_WORKFLOW_BRIDGE",
        "canonical_parent": "VIA_RegistryCore_v1.py",
        "workflow_entry": str(AI_WORKFLOW_ENTRY),
        "registry": str(AI_REGISTRY),
        "database_bridge": str(AI_BRIDGE_CONFIG),
        "capabilities": [
            "instruction_contract_validation",
            "instruction_ast",
            "python_ast_index",
            "append_only_ai_module_id",
            "multi_ai_id_lease",
            "task_context_pack",
            "handoff_validation",
        ],
        "promotion": {
            "automatic": False,
            "requires_human_approval": True,
        },
    }


def load_workflow() -> ModuleType:
    """Load the versioned workflow without changing global import paths."""
    if not AI_WORKFLOW_ENTRY.is_file():
        raise FileNotFoundError(f"AI workflow entry not found: {AI_WORKFLOW_ENTRY}")
    specification = importlib.util.spec_from_file_location(
        "via_ai_workflow_v0100",
        AI_WORKFLOW_ENTRY,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Unable to create import specification: {AI_WORKFLOW_ENTRY}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def selftest() -> dict[str, object]:
    """Validate bridge paths and delegate the package contract test."""
    checks = {
        "workflow_entry_exists": AI_WORKFLOW_ENTRY.is_file(),
        "ai_registry_exists": AI_REGISTRY.is_file(),
        "database_bridge_exists": AI_BRIDGE_CONFIG.is_file(),
    }
    workflow_result: dict[str, object] = {"status": "FAIL", "errors": ["not run"]}
    if all(checks.values()):
        workflow_result = load_workflow().validate_all()
    passed = all(checks.values()) and workflow_result.get("status") == "PASS"
    return {
        "status": "PASS" if passed else "FAIL",
        "module": module_contract(),
        "checks": checks,
        "workflow": workflow_result,
    }


# ============================================================================
# 03. ENTRY POINT
# ============================================================================


def main(argv: Sequence[str] | None = None) -> int:
    """Expose bridge metadata, self-test, or the complete workflow CLI."""
    arguments = list(argv if argv is not None else sys.argv[1:])
    if not arguments or arguments[0] == "contract":
        print(json.dumps(module_contract(), ensure_ascii=False, indent=2))
        return 0
    if arguments[0] == "selftest":
        result = selftest()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 2
    return int(load_workflow().main(arguments))


if __name__ == "__main__":
    raise SystemExit(main())

