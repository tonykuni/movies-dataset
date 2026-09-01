"""Reviewable module templates reconstructed from static code evidence."""

from __future__ import annotations

import hashlib
from typing import Any


CODE_RESTORATION_SCHEMA = "VIA_CODE_RESTORATION/1.0"


def _stable_id(*values: str) -> str:
    return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()[:16].upper()


class CodeRestorer:
    """Assemble non-executing module blueprints; never generate canonical files."""

    def build(
        self,
        code_reconstruction: dict[str, Any],
        function_classification: dict[str, Any],
    ) -> dict[str, Any]:
        blocks = {item["code_id"]: item for item in code_reconstruction.get("code_blocks", [])}
        classified: dict[str, list[dict[str, Any]]] = {}
        for item in function_classification.get("records", []):
            classified.setdefault(str(item["code_id"]), []).append(item)
        modules: list[dict[str, Any]] = []
        for family in code_reconstruction.get("families", []):
            code_ids = [str(item) for item in family.get("code_ids", [])]
            selected_id = str(family.get("candidate_code_id"))
            selected = blocks.get(selected_id, {})
            spec = selected.get("engine_spec", {})
            modules.append(
                {
                    "module_template_id": f"MODULE-{_stable_id(family['family_id'], selected_id)}",
                    "family_id": family["family_id"],
                    "language": family.get("language"),
                    "candidate_code_id": selected_id,
                    "candidate_applied": False,
                    "source_revision_code_ids": code_ids,
                    "source_segments": selected.get("source_segments", []),
                    "source_code_sha256": selected.get("sha256"),
                    "structure": {
                        "imports": spec.get("imports", []),
                        "dependencies": spec.get("dependencies", []),
                        "parameters": spec.get("parameters", {}),
                        "classes": spec.get("classes", []),
                        "functions": spec.get("functions", []),
                        "function_contracts": spec.get("function_contracts", []),
                        "reads": spec.get("reads", []),
                        "writes": spec.get("writes", []),
                    },
                    "functional_classification": classified.get(selected_id, []),
                    "syntax_status": selected.get("syntax", {}).get("status", "missing"),
                    "hydra_risks": selected.get("hydra_risks", []),
                    "review_required": bool(family.get("review_required")) or selected.get("syntax", {}).get("status") != "valid",
                    "source_code_available_verbatim": bool(selected.get("code")),
                }
            )
        interface_graph = code_reconstruction.get("interface_graph", {})
        unresolved = interface_graph.get("unresolved_calls", [])
        ambiguous = interface_graph.get("ambiguous_calls", [])
        review_queue = {
            "module_template_ids": [item["module_template_id"] for item in modules if item["review_required"]],
            "unresolved_calls": unresolved,
            "ambiguous_calls": ambiguous,
            "symbol_conflicts": code_reconstruction.get("symbol_conflicts", []),
            "invalid_code_ids": code_reconstruction.get("build_readiness", {}).get("invalid_code_ids", []),
        }
        return {
            "schema": CODE_RESTORATION_SCHEMA,
            "modules": modules,
            "dependency_graph": interface_graph,
            "review_queue": review_queue,
            "statistics": {
                "module_templates": len(modules),
                "review_required": len(review_queue["module_template_ids"]),
                "unresolved_calls": len(unresolved),
                "ambiguous_calls": len(ambiguous),
            },
            "restoration_stages": [
                {"stage": 1, "zh": "逐字程式區塊擷取", "en": "Exact Code Block Capture", "automatic": True},
                {"stage": 2, "zh": "版本家族分組", "en": "Revision Family Grouping", "automatic": True},
                {"stage": 3, "zh": "函式用途分類", "en": "Function Classification", "automatic": True},
                {"stage": 4, "zh": "依賴與介面拓撲", "en": "Dependency and Interface Topology", "automatic": True},
                {"stage": 5, "zh": "候選模組模板", "en": "Candidate Module Template", "automatic": True},
                {"stage": 6, "zh": "人工選定版本", "en": "Human Canonical Selection", "automatic": False},
                {"stage": 7, "zh": "沙箱測試與啟用", "en": "Sandbox Test and Activation", "automatic": False},
            ],
            "quality_gates": {
                "verbatim_source_code_preserved": all(item["source_code_available_verbatim"] for item in modules) if modules else True,
                "automatic_revision_merge": False,
                "automatic_file_write": False,
                "automatic_dependency_install": False,
                "code_execution_authorized": False,
                "missing_symbol_fail_closed": True,
            },
        }
