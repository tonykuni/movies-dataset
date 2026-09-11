"""Source-grounded CLASS/FUNCTION/PARAMETER/LIB module composition registry.

This module only builds reviewable metadata.  It never imports a discovered
library, executes extracted code, writes reconstructed source, or resolves a
conflict silently.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

from .system_manager import macro_module_catalog


MODULE_COMPOSITION_SCHEMA = "VIA_MODULE_COMPOSITION_REGISTRY/1.0"
DEFAULT_MAX_COMPONENTS = 20_000
PYTHON_STANDARD_LIBRARIES = {
    "abc", "argparse", "ast", "asyncio", "base64", "bisect", "calendar",
    "collections", "concurrent", "contextlib", "copy", "csv", "dataclasses",
    "datetime", "decimal", "enum", "functools", "glob", "hashlib", "heapq",
    "html", "http", "importlib", "inspect", "io", "itertools", "json",
    "logging", "math", "multiprocessing", "operator", "os", "pathlib",
    "pickle", "platform", "queue", "random", "re", "shlex", "shutil",
    "signal", "sqlite3", "statistics", "string", "subprocess", "sys",
    "tempfile", "threading", "time", "tomllib", "traceback", "types",
    "typing", "unittest", "urllib", "uuid", "warnings", "weakref", "xml",
    "zipfile",
}


def _stable_id(prefix: str, *values: str) -> str:
    payload = "\0".join(values)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()
    return f"{prefix}-{digest}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _library_kind(language: str, name: str) -> str:
    normalized = name.strip().split("/", 1)[0].split(".", 1)[0]
    if name.startswith((".", "/")):
        return "local_or_relative"
    if language == "python" and normalized in PYTHON_STANDARD_LIBRARIES:
        return "standard_library"
    if language in {"javascript", "typescript"} and name.startswith(("node:", "@types/")):
        return "runtime_or_type_library"
    return "third_party_or_external"


class ModuleCompositionRegistry:
    """Combine static evidence into scoped, non-executing module blueprints."""

    def __init__(self, max_components: int = DEFAULT_MAX_COMPONENTS) -> None:
        self.max_components = max(1, int(max_components))

    def build(
        self,
        code_reconstruction: dict[str, Any],
        function_classification: dict[str, Any],
        code_restoration: dict[str, Any],
    ) -> dict[str, Any]:
        blocks = {
            str(item["code_id"]): item
            for item in code_reconstruction.get("code_blocks", [])
        }
        classifications = self._classification_index(function_classification)
        composition_modules: list[dict[str, Any]] = []
        component_index: dict[str, dict[str, Any]] = {}
        library_owners: dict[tuple[str, str], set[str]] = defaultdict(set)
        module_by_family: dict[str, str] = {}
        module_by_code: dict[str, str] = {}
        overflow_components = 0

        def register_component(component: dict[str, Any]) -> str | None:
            nonlocal overflow_components
            component_id = str(component["component_id"])
            current = component_index.get(component_id)
            if current is not None:
                for field in ("module_ids", "source_code_ids", "source_segments"):
                    current[field] = sorted(set(current.get(field, [])) | set(component.get(field, [])))
                return component_id
            if len(component_index) >= self.max_components:
                overflow_components += 1
                return None
            component_index[component_id] = component
            return component_id

        for restored in code_restoration.get("modules", []):
            code_id = str(restored.get("candidate_code_id", ""))
            block = blocks.get(code_id, {})
            spec = block.get("engine_spec", restored.get("structure", {}))
            family_id = str(restored.get("family_id") or block.get("family_id") or code_id)
            module_id = _stable_id("COMPMOD", family_id, code_id)
            module_by_family[family_id] = module_id
            module_by_code[code_id] = module_id
            source_segments = sorted(set(block.get("source_segments", restored.get("source_segments", []))))
            component_ids: list[str] = []

            fragment_id = register_component(
                {
                    "component_id": _stable_id("CMP", module_id, "code_fragment", code_id),
                    "component_kind": "code_fragment",
                    "name": code_id,
                    "scope": module_id,
                    "language": block.get("language", restored.get("language", "unknown")),
                    "contract": {
                        "syntax_status": block.get("syntax", {}).get("status", restored.get("syntax_status", "missing")),
                        "fragment_status": block.get("fragment_classification", {}).get("status", "unknown"),
                        "source_sha256": block.get("sha256", restored.get("source_code_sha256")),
                    },
                    "module_ids": [module_id],
                    "source_code_ids": [code_id],
                    "source_segments": source_segments,
                    "review_required": bool(block.get("fragment_classification", {}).get("review_required", False)),
                }
            )
            if fragment_id:
                component_ids.append(fragment_id)

            for name, value in sorted(spec.get("parameters", {}).items()):
                component_id = register_component(
                    self._parameter_component(
                        module_id, code_id, source_segments, str(name), value,
                        parameter_role="module_parameter", scope=module_id,
                    )
                )
                if component_id:
                    component_ids.append(component_id)

            contracts = {
                str(item.get("name")): item
                for item in spec.get("function_contracts", [])
            }
            for name in sorted({str(item) for item in spec.get("functions", [])}):
                contract = contracts.get(name, {"name": name, "arguments": [], "returns": None, "calls": []})
                classification = classifications.get((code_id, name))
                function_id = register_component(
                    {
                        "component_id": _stable_id("CMP", module_id, "function", name),
                        "component_kind": "function",
                        "name": name,
                        "scope": module_id,
                        "language": block.get("language", restored.get("language", "unknown")),
                        "contract": contract,
                        "functional_classification": classification,
                        "module_ids": [module_id],
                        "source_code_ids": [code_id],
                        "source_segments": source_segments,
                        "review_required": bool(classification and classification.get("review_required")),
                    }
                )
                if function_id:
                    component_ids.append(function_id)
                for argument in contract.get("arguments", []):
                    argument_name = str(argument.get("name", "")).strip()
                    if not argument_name:
                        continue
                    parameter_id = register_component(
                        self._parameter_component(
                            module_id,
                            code_id,
                            source_segments,
                            argument_name,
                            argument.get("default"),
                            parameter_role="function_argument",
                            scope=f"{module_id}:function:{name}",
                            annotation=argument.get("annotation"),
                            argument_kind=argument.get("kind"),
                        )
                    )
                    if parameter_id:
                        component_ids.append(parameter_id)

            class_contracts = {
                str(item.get("name")): item
                for item in spec.get("class_contracts", [])
            }
            for name in sorted({str(item) for item in spec.get("classes", [])}):
                contract = class_contracts.get(name, {"name": name, "bases": [], "methods": []})
                class_id = register_component(
                    {
                        "component_id": _stable_id("CMP", module_id, "class", name),
                        "component_kind": "class",
                        "name": name,
                        "scope": module_id,
                        "language": block.get("language", restored.get("language", "unknown")),
                        "contract": contract,
                        "module_ids": [module_id],
                        "source_code_ids": [code_id],
                        "source_segments": source_segments,
                        "review_required": not bool(class_contracts.get(name)),
                    }
                )
                if class_id:
                    component_ids.append(class_id)
                for method in contract.get("methods", []):
                    method_name = str(method.get("name", "")).strip()
                    if not method_name:
                        continue
                    method_id = register_component(
                        {
                            "component_id": _stable_id("CMP", module_id, "class_method", name, method_name),
                            "component_kind": "function",
                            "function_role": "class_method",
                            "name": method_name,
                            "scope": f"{module_id}:class:{name}",
                            "language": block.get("language", restored.get("language", "unknown")),
                            "contract": method,
                            "functional_classification": None,
                            "module_ids": [module_id],
                            "source_code_ids": [code_id],
                            "source_segments": source_segments,
                            "review_required": False,
                        }
                    )
                    if method_id:
                        component_ids.append(method_id)

            for dependency in sorted({str(item) for item in spec.get("dependencies", []) if str(item).strip()}):
                language = str(block.get("language", restored.get("language", "unknown")))
                library_id = _stable_id("LIB", language, dependency)
                registered = register_component(
                    {
                        "component_id": library_id,
                        "component_kind": "library",
                        "name": dependency,
                        "scope": "shared_dependency_registry",
                        "language": language,
                        "contract": {
                            "library_kind": _library_kind(language, dependency),
                            "import_evidence": [
                                str(item) for item in spec.get("imports", [])
                                if dependency.split(".", 1)[0] in str(item)
                            ],
                        },
                        "module_ids": [module_id],
                        "source_code_ids": [code_id],
                        "source_segments": source_segments,
                        "review_required": _library_kind(language, dependency) == "third_party_or_external",
                    }
                )
                if registered:
                    component_ids.append(registered)
                    library_owners[(language, dependency)].add(module_id)

            block_issues = self._block_interface_issues(code_id, code_reconstruction, module_id)
            review_reasons: list[str] = []
            syntax_status = str(block.get("syntax", {}).get("status", restored.get("syntax_status", "missing")))
            fragment_review = bool(block.get("fragment_classification", {}).get("review_required", False))
            if syntax_status not in {"valid", "valid_lexical_only"}:
                review_reasons.append("invalid_or_unchecked_syntax")
            if fragment_review:
                review_reasons.append("incomplete_or_uncertain_fragment")
            if restored.get("review_required"):
                review_reasons.append("revision_family_review")
            if block.get("hydra_risks"):
                review_reasons.append("hydra_risk_review")
            if block_issues["unresolved_calls"]:
                review_reasons.append("unresolved_interfaces")
            if block_issues["ambiguous_calls"]:
                review_reasons.append("ambiguous_interfaces")
            blocking = syntax_status == "invalid" or "destructive_operation" in block.get("hydra_risks", [])
            status = "blocked" if blocking else "review_required" if review_reasons else "static_ready"
            category_records = classifications.get((code_id, "*"), [])
            categories = sorted({
                str(item.get("primary_category"))
                for item in category_records
                if item.get("primary_category")
            })
            composition_modules.append(
                {
                    "module_id": module_id,
                    "module_template_id": restored.get("module_template_id"),
                    "family_id": family_id,
                    "candidate_code_id": code_id,
                    "language": block.get("language", restored.get("language", "unknown")),
                    "labels": {
                        "zh": f"候選模組 {code_id}",
                        "en": f"Candidate Module {code_id}",
                    },
                    "namespace_proposal": f"via_module_{module_id.split('-', 1)[-1].lower()}",
                    "component_ids": sorted(set(component_ids)),
                    "functional_categories": categories,
                    "source_segments": source_segments,
                    "source_code_sha256": block.get("sha256", restored.get("source_code_sha256")),
                    "syntax_status": syntax_status,
                    "status": status,
                    "review_reasons": sorted(set(review_reasons)),
                    "unresolved_calls": block_issues["unresolved_calls"],
                    "ambiguous_calls": block_issues["ambiguous_calls"],
                    "automatic_merge_applied": False,
                    "source_code_emitted": False,
                }
            )

        parameter_registry = self._parameter_registry(code_reconstruction, module_by_family, module_by_code)
        dependency_graph = self._dependency_graph(
            composition_modules,
            code_reconstruction.get("interface_graph", {}),
            module_by_family,
        )
        self._apply_dependency_state(composition_modules, dependency_graph, parameter_registry)
        groups = self._functional_groups(composition_modules)
        components = sorted(component_index.values(), key=lambda item: str(item["component_id"]))
        for component in components:
            component["evidence_grade"] = {
                "structure": "V",
                "functional_classification": "M" if component.get("functional_classification") else None,
                "macro_assignment": "P",
            }
        libraries = [
            {
                "library_id": _stable_id("LIB", language, name),
                "name": name,
                "language": language,
                "library_kind": _library_kind(language, name),
                "consumer_module_ids": sorted(owners),
                "automatic_install": False,
                "availability_verified": False,
            }
            for (language, name), owners in sorted(library_owners.items())
        ]
        review_modules = [item["module_id"] for item in composition_modules if item["status"] != "static_ready"]
        macro_architecture = self._macro_architecture(composition_modules)
        decision_cards = self._decision_cards(
            composition_modules,
            parameter_registry,
            dependency_graph,
        )
        return {
            "schema": MODULE_COMPOSITION_SCHEMA,
            "languages": ["zh", "en"],
            "modules": composition_modules,
            "component_registry": components,
            "parameter_registry": parameter_registry,
            "library_registry": libraries,
            "functional_groups": groups,
            "macro_architecture": macro_architecture,
            "dependency_graph": dependency_graph,
            "composition_plan": {
                "topological_layers": dependency_graph["topological_layers"],
                "ordered_module_ids": dependency_graph["topological_order"],
                "review_module_ids": review_modules,
                "activation_status": "human_review_required_before_generation_or_execution",
                "stages": [
                    {"stage": 1, "zh": "來源與語法驗證", "en": "Source and Syntax Validation", "automatic": True},
                    {"stage": 2, "zh": "參數作用域與衝突檢查", "en": "Parameter Scope and Conflict Check", "automatic": True},
                    {"stage": 3, "zh": "類別／函式／函式庫組合", "en": "Class / Function / Library Composition", "automatic": True},
                    {"stage": 4, "zh": "依賴拓撲與介面審查", "en": "Dependency Topology and Interface Review", "automatic": True},
                    {"stage": 5, "zh": "人工核准產生模組", "en": "Human-approved Module Generation", "automatic": False},
                    {"stage": 6, "zh": "沙箱測試與啟用", "en": "Sandbox Test and Activation", "automatic": False},
                ],
            },
            "compatibility_contract": {
                "same_language_composition": "metadata_ready_runtime_test_required",
                "cross_language_composition": "adapter_or_process_boundary_required",
                "mixed_runtime_auto_bridge": False,
                "missing_interface_policy": "fail_closed_review_required",
            },
            "review_queue": {
                "module_ids": review_modules,
                "parameter_conflicts": parameter_registry["conflicts"],
                "cross_scope_name_collisions": parameter_registry["cross_scope_name_collisions"],
                "unresolved_calls": dependency_graph["unresolved_calls"],
                "ambiguous_calls": dependency_graph["ambiguous_calls"],
                "cycles": dependency_graph["cycles"],
                "component_capacity_overflow": overflow_components,
            },
            "decision_cards": decision_cards,
            "statistics": {
                "modules": len(composition_modules),
                "static_ready_modules": sum(item["status"] == "static_ready" for item in composition_modules),
                "review_required_modules": sum(item["status"] == "review_required" for item in composition_modules),
                "blocked_modules": sum(item["status"] == "blocked" for item in composition_modules),
                "components": len(components),
                "classes": sum(item["component_kind"] == "class" for item in components),
                "functions": sum(item["component_kind"] == "function" for item in components),
                "parameters": sum(item["component_kind"] == "parameter" for item in components),
                "libraries": len(libraries),
                "functional_groups": len(groups),
                "macro_modules": len(macro_architecture["macro_modules"]),
                "decision_cards": len(decision_cards),
            },
            "quality_gates": {
                "component_source_traceability": "pass" if all(item.get("source_code_ids") for item in components) or not components else "fail",
                "parameter_scope_preserved": True,
                "conflicting_values_silently_resolved": False,
                "incomplete_fragments_auto_stitched": False,
                "automatic_module_merge": False,
                "automatic_source_generation": False,
                "automatic_file_write": False,
                "automatic_library_import": False,
                "automatic_dependency_install": False,
                "code_execution_authorized": False,
                "backward_compatible_additive_contract": True,
                "nlp_core_is_independent": macro_architecture["quality_gates"]["nlp_core_is_independent"],
                "system_manager_only_integrates": True,
            },
        }

    @staticmethod
    def _classification_index(function_classification: dict[str, Any]) -> dict[Any, Any]:
        index: dict[Any, Any] = {}
        by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in function_classification.get("records", []):
            code_id = str(record.get("code_id", ""))
            name = str(record.get("symbol_name", ""))
            index[(code_id, name)] = record
            by_code[code_id].append(record)
        for code_id, records in by_code.items():
            index[(code_id, "*")] = records
        return index

    @staticmethod
    def _parameter_component(
        module_id: str,
        code_id: str,
        source_segments: list[str],
        name: str,
        value: Any,
        parameter_role: str,
        scope: str,
        annotation: Any = None,
        argument_kind: Any = None,
    ) -> dict[str, Any]:
        return {
            "component_id": _stable_id("CMP", module_id, "parameter", scope, name, _canonical_json(value)),
            "component_kind": "parameter",
            "parameter_role": parameter_role,
            "name": name,
            "scope": scope,
            "language": None,
            "contract": {
                "value_or_default": value,
                "annotation": annotation,
                "argument_kind": argument_kind,
            },
            "module_ids": [module_id],
            "source_code_ids": [code_id],
            "source_segments": source_segments,
            "review_required": False,
        }

    @staticmethod
    def _block_interface_issues(
        code_id: str,
        code_reconstruction: dict[str, Any],
        module_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        graph = code_reconstruction.get("interface_graph", {})
        return {
            key: [
                {**item, "consumer_module_id": module_id}
                for item in graph.get(key, [])
                if str(item.get("source_code_id")) == code_id
            ]
            for key in ("unresolved_calls", "ambiguous_calls")
        }

    @staticmethod
    def _parameter_registry(
        code_reconstruction: dict[str, Any],
        module_by_family: dict[str, str],
        module_by_code: dict[str, str],
    ) -> dict[str, Any]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for block in code_reconstruction.get("code_blocks", []):
            code_id = str(block["code_id"])
            family_id = str(block.get("family_id") or code_id)
            base_scope = f"family:{family_id}"
            selected_module_id = module_by_family.get(family_id) or module_by_code.get(code_id)
            spec = block.get("engine_spec", {})
            for name, value in spec.get("parameters", {}).items():
                grouped[(base_scope, str(name))].append(
                    {
                        "candidate_id": _stable_id("PARAMCAND", base_scope, str(name), code_id, _canonical_json(value)),
                        "name": str(name),
                        "scope": base_scope,
                        "parameter_role": "module_parameter",
                        "value_or_default": value,
                        "source_code_id": code_id,
                        "source_segments": block.get("source_segments", []),
                        "selected_module_id": selected_module_id,
                        "selected_revision": bool(selected_module_id and module_by_code.get(code_id) == selected_module_id),
                    }
                )
            for contract in spec.get("function_contracts", []):
                function_name = str(contract.get("name", ""))
                for argument in contract.get("arguments", []):
                    name = str(argument.get("name", "")).strip()
                    if not name:
                        continue
                    scope = f"{base_scope}:function:{function_name}"
                    value = argument.get("default")
                    grouped[(scope, name)].append(
                        {
                            "candidate_id": _stable_id("PARAMCAND", scope, name, code_id, _canonical_json(value)),
                            "name": name,
                            "scope": scope,
                            "parameter_role": "function_argument",
                            "value_or_default": value,
                            "annotation": argument.get("annotation"),
                            "argument_kind": argument.get("kind"),
                            "source_code_id": code_id,
                            "source_segments": block.get("source_segments", []),
                            "selected_module_id": selected_module_id,
                            "selected_revision": bool(selected_module_id and module_by_code.get(code_id) == selected_module_id),
                        }
                    )
        entries: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        name_scopes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for (scope, name), candidates in sorted(grouped.items()):
            distinct_values = sorted({_canonical_json(item.get("value_or_default")) for item in candidates})
            status = "conflict_review_required" if len(distinct_values) > 1 else "scoped_consistent"
            entry = {
                "parameter_id": _stable_id("PARAM", scope, name),
                "name": name,
                "scope": scope,
                "status": status,
                "candidates": candidates,
                "distinct_value_count": len(distinct_values),
                "automatic_resolution": False,
            }
            entries.append(entry)
            name_scopes[name].append(entry)
            if status == "conflict_review_required":
                conflicts.append(
                    {
                        "conflict_id": _stable_id("PARAMCONFLICT", scope, name),
                        "parameter_id": entry["parameter_id"],
                        "name": name,
                        "scope": scope,
                        "candidate_ids": [item["candidate_id"] for item in candidates],
                        "resolution": "human_required",
                    }
                )
        collisions = []
        for name, scoped_entries in sorted(name_scopes.items()):
            if len(scoped_entries) <= 1:
                continue
            values = {
                _canonical_json(candidate.get("value_or_default"))
                for entry in scoped_entries
                for candidate in entry["candidates"]
            }
            if len(values) > 1:
                collisions.append(
                    {
                        "name": name,
                        "scopes": [item["scope"] for item in scoped_entries],
                        "status": "informational_scopes_remain_isolated",
                        "automatic_global_binding": False,
                    }
                )
        return {
            "entries": entries,
            "conflicts": conflicts,
            "cross_scope_name_collisions": collisions,
            "scope_policy": "family_and_function_scoped_never_global_by_name",
        }

    @staticmethod
    def _dependency_graph(
        modules: list[dict[str, Any]],
        interface_graph: dict[str, Any],
        module_by_family: dict[str, str],
    ) -> dict[str, Any]:
        dependencies: dict[str, set[str]] = {str(item["module_id"]): set() for item in modules}
        edges: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for edge in interface_graph.get("edges", []):
            provider = module_by_family.get(str(edge.get("from_family")))
            consumer = module_by_family.get(str(edge.get("to_family")))
            symbol = str(edge.get("symbol", ""))
            if not provider or not consumer or provider == consumer:
                continue
            key = (provider, consumer, symbol)
            if key in seen:
                continue
            seen.add(key)
            dependencies[consumer].add(provider)
            edges.append(
                {
                    "from": provider,
                    "to": consumer,
                    "relation": "provides_symbol_to",
                    "symbol": symbol,
                    "source_code_id": edge.get("source_code_id"),
                }
            )
        remaining = {name: set(values) for name, values in dependencies.items()}
        layers: list[list[str]] = []
        while remaining:
            ready = sorted(name for name, required in remaining.items() if not required)
            if not ready:
                break
            layers.append(ready)
            for name in ready:
                remaining.pop(name)
            for required in remaining.values():
                required.difference_update(ready)
        cycles = sorted(remaining)
        unresolved = [dict(item) for item in interface_graph.get("unresolved_calls", [])]
        ambiguous = [dict(item) for item in interface_graph.get("ambiguous_calls", [])]
        return {
            "edges": edges,
            "module_dependencies": {name: sorted(values) for name, values in sorted(dependencies.items())},
            "topological_layers": layers,
            "topological_order": [name for layer in layers for name in layer],
            "cycles": cycles,
            "topology_complete": not cycles and sum(len(layer) for layer in layers) == len(modules),
            "unresolved_calls": unresolved,
            "ambiguous_calls": ambiguous,
            "automatic_binding": False,
        }

    @staticmethod
    def _apply_dependency_state(
        modules: list[dict[str, Any]],
        dependency_graph: dict[str, Any],
        parameter_registry: dict[str, Any],
    ) -> None:
        conflicts_by_family = {
            str(item["scope"]).split(":", 1)[-1].split(":function:", 1)[0]
            for item in parameter_registry["conflicts"]
        }
        cycles = set(dependency_graph["cycles"])
        dependencies = dependency_graph["module_dependencies"]
        for module in modules:
            module_id = str(module["module_id"])
            module["depends_on_module_ids"] = dependencies.get(module_id, [])
            if str(module["family_id"]) in conflicts_by_family:
                module["review_reasons"] = sorted(set(module["review_reasons"]) | {"parameter_conflict"})
            if module_id in cycles:
                module["review_reasons"] = sorted(set(module["review_reasons"]) | {"dependency_cycle"})
            if module["review_reasons"] and module["status"] == "static_ready":
                module["status"] = "review_required"

    @staticmethod
    def _functional_groups(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for module in modules:
            categories = module.get("functional_categories") or ["unclassified"]
            for category in categories:
                grouped[str(category)].append(str(module["module_id"]))
        return [
            {
                "group_id": _stable_id("FUNCGRP", category),
                "category": category,
                "module_ids": sorted(set(module_ids)),
                "automatic_runtime_binding": False,
            }
            for category, module_ids in sorted(grouped.items())
        ]

    @staticmethod
    def _macro_architecture(modules: list[dict[str, Any]]) -> dict[str, Any]:
        category_owners = {
            "ingestion": "FORMAT-LAYOUT-IO",
            "parsing": "FORMAT-LAYOUT-IO",
            "normalization": "NLP-CORE",
            "analytics_nlp": "NLP-CORE",
            "transformation": "CODE-INTELLIGENCE",
            "testing_debug": "GOVERNANCE-QUALITY",
            "validation": "GOVERNANCE-QUALITY",
            "configuration": "GOVERNANCE-QUALITY",
            "security_governance": "GOVERNANCE-QUALITY",
            "concurrency_performance": "RUNTIME-ACCELERATION",
            "persistence_io": "EXPORT-REPORTING",
            "ui_reporting": "EXPORT-REPORTING",
            "orchestration": "GOVERNANCE-QUALITY",
            "utility": "GOVERNANCE-QUALITY",
            "unclassified": "GOVERNANCE-QUALITY",
        }
        assignments: dict[str, set[str]] = defaultdict(set)
        assignment_evidence: list[dict[str, Any]] = []
        for module in modules:
            categories = module.get("functional_categories") or ["unclassified"]
            for category in categories:
                owner = category_owners.get(str(category), "GOVERNANCE-QUALITY")
                assignments[owner].add(str(module["module_id"]))
                assignment_evidence.append(
                    {
                        "candidate_module_id": module["module_id"],
                        "macro_module_id": owner,
                        "category": category,
                        "evidence_grade": "P",
                        "automatic_runtime_binding": False,
                    }
                )
        catalog = macro_module_catalog()
        for item in catalog:
            item["candidate_module_ids"] = sorted(assignments.get(str(item["module_id"]), set()))
            item["candidate_assignment_is_proposal"] = True
        topology_edges = [
            {
                "from": dependency,
                "to": item["module_id"],
                "relation": "macro_dependency",
            }
            for item in catalog
            for dependency in item.get("dependencies", [])
        ]
        return {
            "schema": "VIA_MACRO_ARCHITECTURE/1.0",
            "system_manager": {
                "manager_id": "SYSTEM-MANAGER",
                "name": {"zh": "系統整合管理器", "en": "System Integration Manager"},
                "responsibilities": [
                    "registry", "routing", "dependency_injection", "lifecycle", "health", "audit",
                ],
                "contains_domain_logic": False,
                "loads_extracted_code": False,
            },
            "macro_modules": catalog,
            "candidate_assignments": assignment_evidence,
            "topology_edges": topology_edges,
            "quality_gates": {
                "nlp_core_is_independent": any(
                    item["module_id"] == "NLP-CORE" and item["independent"] and not item["dependencies"]
                    for item in catalog
                ),
                "macro_modules_can_exist_independently": all(item["independent"] for item in catalog),
                "candidate_assignment_auto_activated": False,
                "system_manager_contains_domain_logic": False,
            },
        }

    @staticmethod
    def _decision_cards(
        modules: list[dict[str, Any]],
        parameter_registry: dict[str, Any],
        dependency_graph: dict[str, Any],
    ) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for module in modules:
            if module["status"] == "static_ready":
                continue
            cards.append(
                {
                    "card_id": _stable_id("CARD", "module", str(module["module_id"])),
                    "kind": "MODULE_REVIEW",
                    "impact": len(module.get("component_ids", [])),
                    "minimal_context": {
                        "module_id": module["module_id"],
                        "candidate_code_id": module["candidate_code_id"],
                        "language": module["language"],
                        "status": module["status"],
                        "review_reasons": module["review_reasons"],
                        "source_segments": module["source_segments"][:12],
                    },
                    "options": ["KEEP_ISOLATED", "REQUEST_SOURCE_CONTEXT", "APPROVE_STATIC_BLUEPRINT"],
                    "default": "DEFER",
                    "evidence_grade": "V",
                }
            )
        for conflict in parameter_registry.get("conflicts", []):
            cards.append(
                {
                    "card_id": _stable_id("CARD", "parameter", str(conflict["conflict_id"])),
                    "kind": "PARAMETER_CONFLICT",
                    "impact": len(conflict.get("candidate_ids", [])),
                    "minimal_context": conflict,
                    "options": ["KEEP_SCOPED", "SELECT_CANDIDATE", "REQUEST_SOURCE_CONTEXT"],
                    "default": "DEFER",
                    "evidence_grade": "V",
                }
            )
        for kind, key in (("UNRESOLVED_CALL", "unresolved_calls"), ("AMBIGUOUS_CALL", "ambiguous_calls")):
            for issue in dependency_graph.get(key, []):
                cards.append(
                    {
                        "card_id": _stable_id("CARD", kind, _canonical_json(issue)),
                        "kind": kind,
                        "impact": 1,
                        "minimal_context": issue,
                        "options": ["DECLARE_EXTERNAL", "BIND_EXISTING", "REQUEST_SOURCE_CONTEXT"],
                        "default": "DEFER",
                        "evidence_grade": "V",
                    }
                )
        return sorted(cards, key=lambda item: (-int(item["impact"]), str(item["card_id"])))

    @staticmethod
    def enrich_mind_map(
        mind_map: dict[str, Any],
        registry: dict[str, Any],
        max_edges: int,
    ) -> dict[str, Any]:
        """Append bilingual module/component nodes without changing old nodes."""
        ai_view = mind_map["ai_view"]
        nodes = ai_view.setdefault("nodes", [])
        edges = ai_view.setdefault("edges", [])
        known_nodes = {str(item.get("node_id")) for item in nodes}
        known_edges = {
            (str(item.get("from")), str(item.get("to")), str(item.get("relation")))
            for item in edges
        }

        def add_node(node: dict[str, Any]) -> bool:
            node_id = str(node["node_id"])
            if node_id in known_nodes or len(edges) >= max_edges:
                return node_id in known_nodes
            label = node.pop("labels", {"zh": str(node.get("label", node_id)), "en": str(node.get("label", node_id))})
            node["label"] = str(label.get("zh", node_id))
            node["bilingual_label"] = {
                "source": node["label"],
                "source_language": "mixed",
                "zh": str(label.get("zh", node["label"])),
                "en": str(label.get("en", node["label"])),
                "translation_status": "verified_structural_label",
            }
            node["type_label"] = {
                "zh": str(node.get("node_type", "module_component")),
                "en": str(node.get("node_type", "module_component")),
            }
            nodes.append(node)
            known_nodes.add(node_id)
            return True

        def add_edge(left: str, right: str, relation: str) -> None:
            key = (left, right, relation)
            if len(edges) >= max_edges or key in known_edges or left not in known_nodes or right not in known_nodes:
                return
            edges.append(
                {
                    "from": left,
                    "to": right,
                    "relation": relation,
                    "relation_label": {"zh": relation, "en": relation},
                    "confidence": 1.0,
                }
            )
            known_edges.add(key)

        root_id = "MODULE-COMPOSITION-ROOT"
        if add_node(
            {
                "node_id": root_id,
                "node_type": "module_composition_registry",
                "labels": {"zh": "模組組合註冊表", "en": "Module Composition Registry"},
                "source_segments": [],
                "schema": registry.get("schema"),
            }
        ):
            add_edge("ROOT", root_id, "has_module_composition")
        manager_definition = registry.get("macro_architecture", {}).get("system_manager", {})
        manager_id = str(manager_definition.get("manager_id", "SYSTEM-MANAGER"))
        if add_node(
            {
                "node_id": manager_id,
                "node_type": "system_manager",
                "labels": manager_definition.get(
                    "name", {"zh": "系統整合管理器", "en": "System Integration Manager"}
                ),
                "source_segments": [],
                "responsibilities": manager_definition.get("responsibilities", []),
                "contains_domain_logic": False,
            }
        ):
            add_edge("ROOT", manager_id, "has_system_manager")
            add_edge(manager_id, root_id, "governs_module_composition")
        for macro in registry.get("macro_architecture", {}).get("macro_modules", []):
            macro_id = str(macro["module_id"])
            if not add_node(
                {
                    "node_id": macro_id,
                    "node_type": "macro_module",
                    "labels": macro.get("name", {"zh": macro_id, "en": macro_id}),
                    "source_segments": [],
                    "independent": macro.get("independent", True),
                    "capabilities": macro.get("capabilities", []),
                }
            ):
                continue
            add_edge(manager_id, macro_id, "integrates_macro_module")
        for macro_edge in registry.get("macro_architecture", {}).get("topology_edges", []):
            add_edge(str(macro_edge["from"]), str(macro_edge["to"]), "macro_module_dependency")
        for module in registry.get("modules", []):
            module_id = str(module["module_id"])
            if not add_node(
                {
                    "node_id": module_id,
                    "node_type": "composition_module",
                    "labels": module.get("labels", {"zh": module_id, "en": module_id}),
                    "source_segments": module.get("source_segments", []),
                    "language": module.get("language"),
                    "status": module.get("status"),
                    "functional_categories": module.get("functional_categories", []),
                }
            ):
                continue
            add_edge(root_id, module_id, "contains_composition_module")
        for assignment in registry.get("macro_architecture", {}).get("candidate_assignments", []):
            add_edge(
                str(assignment["macro_module_id"]),
                str(assignment["candidate_module_id"]),
                "classifies_candidate_module",
            )
        for component in registry.get("component_registry", []):
            component_id = str(component["component_id"])
            name = str(component.get("name", component_id))
            if not add_node(
                {
                    "node_id": component_id,
                    "node_type": f"module_{component.get('component_kind', 'component')}",
                    "labels": {"zh": name, "en": name},
                    "source_segments": component.get("source_segments", []),
                    "scope": component.get("scope"),
                    "review_required": component.get("review_required", False),
                }
            ):
                continue
            for module_id in component.get("module_ids", []):
                add_edge(str(module_id), component_id, "contains_component")
        for edge in registry.get("dependency_graph", {}).get("edges", []):
            add_edge(str(edge["from"]), str(edge["to"]), "module_dependency")
        ai_view["module_composition_schema"] = registry.get("schema")
        ai_view["node_count"] = len(nodes)
        ai_view["edge_count"] = len(edges)
        ai_view["edge_capacity_reached"] = len(edges) >= max_edges
        contract = mind_map.get("bilingual_contract")
        if isinstance(contract, dict):
            statuses = [
                item.get("bilingual_label", {}).get("translation_status")
                for item in nodes
            ]
            contract["semantic_labels_total"] = len(statuses)
            contract["semantic_labels_needing_translation"] = sum(item == "needs_translation" for item in statuses)
        return mind_map
