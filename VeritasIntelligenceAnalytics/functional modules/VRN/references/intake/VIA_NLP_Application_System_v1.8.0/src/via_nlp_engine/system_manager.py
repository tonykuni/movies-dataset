"""Explicit macro-module registry and fail-closed system manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


SYSTEM_MANAGER_SCHEMA = "VIA_SYSTEM_MANAGER/1.0"
MACRO_MODULE_SCHEMA = "VIA_MACRO_MODULE/1.0"
Handler = Callable[..., Any]

MACRO_MODULE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "module_id": "NLP-CORE",
        "name": {"zh": "NLP 核心模組", "en": "NLP Core Module"},
        "independent": True,
        "categories": ["normalization", "analytics_nlp"],
        "capabilities": [
            "normalize", "repair", "segment", "keywords", "entities", "summarize",
            "topic_recurrence", "context_reconstruction", "bilingual_projection",
            "cpu_ml_challenger", "knowledge", "reorganize", "complete_summarizer",
            "evidence_summarizer", "content_role_analysis",
        ],
        "dependencies": [],
    },
    {
        "module_id": "FORMAT-LAYOUT-IO",
        "name": {"zh": "格式、版面與資料匯入模組", "en": "Format, Layout and Intake Module"},
        "independent": True,
        "categories": ["ingestion", "parsing"],
        "capabilities": [
            "local_document_intake", "markitdown_projection", "markdown_layout_analysis",
            "table_structure", "source_record_ledger", "layout_quality_gate",
        ],
        "dependencies": [],
    },
    {
        "module_id": "CODE-INTELLIGENCE",
        "name": {"zh": "程式理解與模組重建模組", "en": "Code Intelligence and Reconstruction Module"},
        "independent": True,
        "categories": ["transformation", "testing_debug"],
        "capabilities": [
            "language_detection", "ast_cst_inspection", "class_function_parameter_library_registry",
            "revision_families", "call_graph", "dependency_topology", "module_blueprints",
        ],
        "dependencies": ["FORMAT-LAYOUT-IO"],
    },
    {
        "module_id": "KNOWLEDGE-GRAPH",
        "name": {"zh": "知識體與動態 Mind Map 模組", "en": "Knowledge Body and Dynamic Mind Map Module"},
        "independent": True,
        "categories": ["knowledge_graph"],
        "capabilities": [
            "knowledge_units", "conflict_register", "ssot_candidates", "typed_graph",
            "mind_map_evolution", "source_attribution", "retrieval_projection",
        ],
        "dependencies": ["NLP-CORE"],
    },
    {
        "module_id": "GOVERNANCE-QUALITY",
        "name": {"zh": "治理、安全與品質模組", "en": "Governance, Security and Quality Module"},
        "independent": True,
        "categories": ["validation", "configuration", "security_governance"],
        "capabilities": [
            "quality_gates", "hydra_risk", "decision_cards", "audit_hash_chain",
            "human_approval", "champion_challenger_gate", "fail_closed_policy", "govern",
        ],
        "dependencies": [],
    },
    {
        "module_id": "RUNTIME-ACCELERATION",
        "name": {"zh": "CPU 執行期與加速模組", "en": "CPU Runtime and Acceleration Module"},
        "independent": True,
        "categories": ["concurrency_performance"],
        "capabilities": [
            "resource_monitor", "lazy_loading", "bounded_concurrency", "cache",
            "batch_processing", "optional_cpu_providers", "oom_protection",
        ],
        "dependencies": [],
    },
    {
        "module_id": "EXPORT-REPORTING",
        "name": {"zh": "輸出、儲存與報告模組", "en": "Export, Persistence and Reporting Module"},
        "independent": True,
        "categories": ["persistence_io", "ui_reporting"],
        "capabilities": [
            "deterministic_package", "json_artifacts", "html_dashboard", "csv_projection",
            "handoff_report", "sha256_manifest",
        ],
        "dependencies": [],
    },
)


@dataclass(slots=True)
class SystemModuleRegistration:
    """A macro-module contract plus explicitly bound internal operations."""

    module_id: str
    name: dict[str, str]
    independent: bool
    categories: list[str]
    capabilities: list[str]
    dependencies: list[str]
    handlers: dict[str, Handler]

    def status(self) -> dict[str, Any]:
        return {
            "schema": MACRO_MODULE_SCHEMA,
            "module_id": self.module_id,
            "name": self.name,
            "independent": self.independent,
            "categories": list(self.categories),
            "capabilities": list(self.capabilities),
            "dependencies": list(self.dependencies),
            "bound_operations": sorted(self.handlers),
            "available": True,
            "dynamic_import_allowed": False,
        }

    def invoke(self, operation: str, **payload: Any) -> Any:
        handler = self.handlers.get(operation)
        if handler is None:
            raise KeyError(f"Operation {operation!r} is not registered for module {self.module_id!r}")
        return handler(**payload)


class VIASystemManager:
    """Integrate independent macro modules through an explicit allow-list."""

    def __init__(self) -> None:
        self._modules: dict[str, SystemModuleRegistration] = {}
        self._started = False

    def register(
        self,
        definition: dict[str, Any],
        handlers: dict[str, Handler] | None = None,
    ) -> None:
        module_id = str(definition["module_id"])
        if module_id in self._modules:
            raise ValueError(f"Duplicate macro module registration: {module_id}")
        allowed = set(str(item) for item in definition.get("capabilities", []))
        selected_handlers = dict(handlers or {})
        unknown = sorted(set(selected_handlers) - allowed)
        if unknown:
            raise ValueError(f"Handlers are not declared capabilities for {module_id}: {unknown}")
        self._modules[module_id] = SystemModuleRegistration(
            module_id=module_id,
            name={str(key): str(value) for key, value in definition.get("name", {}).items()},
            independent=bool(definition.get("independent", True)),
            categories=[str(item) for item in definition.get("categories", [])],
            capabilities=[str(item) for item in definition.get("capabilities", [])],
            dependencies=[str(item) for item in definition.get("dependencies", [])],
            handlers=selected_handlers,
        )

    def start(self) -> None:
        validation = self.validate_topology()
        if validation["status"] != "pass":
            raise RuntimeError(f"System Manager topology is invalid: {validation}")
        self._started = True

    def stop(self) -> None:
        self._started = False

    def dispatch(self, module_id: str, operation: str, **payload: Any) -> Any:
        if not self._started:
            raise RuntimeError("System Manager is not started")
        selected = self._modules.get(module_id)
        if selected is None:
            raise KeyError(f"Unknown macro module: {module_id}")
        missing_dependencies = [item for item in selected.dependencies if item not in self._modules]
        if missing_dependencies:
            raise RuntimeError(f"Module {module_id} has missing dependencies: {missing_dependencies}")
        return selected.invoke(operation, **payload)

    def validate_topology(self) -> dict[str, Any]:
        dependency_map = {
            module_id: set(module.dependencies)
            for module_id, module in self._modules.items()
        }
        missing = sorted({
            dependency
            for dependencies in dependency_map.values()
            for dependency in dependencies
            if dependency not in dependency_map
        })
        remaining = {key: set(value) for key, value in dependency_map.items()}
        layers: list[list[str]] = []
        while remaining and not missing:
            ready = sorted(key for key, dependencies in remaining.items() if not dependencies)
            if not ready:
                break
            layers.append(ready)
            for key in ready:
                remaining.pop(key)
            for dependencies in remaining.values():
                dependencies.difference_update(ready)
        cycles = sorted(remaining)
        return {
            "status": "pass" if not missing and not cycles else "fail",
            "missing_dependencies": missing,
            "cycles": cycles,
            "topological_layers": layers,
            "topological_order": [item for layer in layers for item in layer],
        }

    def health(self) -> dict[str, Any]:
        topology = self.validate_topology()
        return {
            "schema": SYSTEM_MANAGER_SCHEMA,
            "status": "ready" if self._started and topology["status"] == "pass" else "stopped" if not self._started else "degraded",
            "manager_role": {
                "zh": "註冊、路由、依賴、生命週期與健康整合",
                "en": "Registry, routing, dependency, lifecycle and health integration",
            },
            "modules": [self._modules[key].status() for key in sorted(self._modules)],
            "module_count": len(self._modules),
            "topology": topology,
            "quality_gates": {
                "nlp_core_is_independent": bool(
                    self._modules.get("NLP-CORE")
                    and self._modules["NLP-CORE"].independent
                    and not self._modules["NLP-CORE"].dependencies
                ),
                "dynamic_module_import": False,
                "extracted_code_registration": False,
                "unknown_operation_fails_closed": True,
                "system_manager_contains_domain_logic": False,
            },
        }


def build_default_system_manager(processor: Any, knowledge_builder: Any) -> VIASystemManager:
    """Bind existing trusted engine services to the seven macro modules."""
    manager = VIASystemManager()
    handlers: dict[str, dict[str, Handler]] = {
        "NLP-CORE": {
            "normalize": processor.normalize,
            "repair": processor.repair,
            "segment": knowledge_builder.segmenter.segment,
            "keywords": processor.keywords,
            "entities": processor.entities,
            "summarize": processor.summarize,
            "knowledge": knowledge_builder.knowledge,
            "reorganize": knowledge_builder.reorganize,
            "complete_summarizer": processor.summarize_complete,
            "evidence_summarizer": processor.summarize_complete,
            "content_role_analysis": lambda text: knowledge_builder.knowledge(text)["content_role_analysis"],
        },
        "FORMAT-LAYOUT-IO": {
            "markdown_layout_analysis": lambda text: knowledge_builder.layout_analyzer.build(
                text,
                knowledge_builder.segmenter.segment(text)["segments"],
                [],
            ),
        },
        "CODE-INTELLIGENCE": {
            "class_function_parameter_library_registry": lambda text: knowledge_builder.knowledge(text)[
                "module_composition_registry"
            ],
        },
        "KNOWLEDGE-GRAPH": {
            "typed_graph": lambda text: knowledge_builder.knowledge(text)["mind_map"],
        },
        "GOVERNANCE-QUALITY": {
            "quality_gates": lambda text: knowledge_builder.govern(text),
            "govern": knowledge_builder.govern,
        },
        "RUNTIME-ACCELERATION": {},
        "EXPORT-REPORTING": {},
    }
    for definition in MACRO_MODULE_DEFINITIONS:
        manager.register(definition, handlers.get(str(definition["module_id"]), {}))
    return manager


def macro_module_catalog() -> list[dict[str, Any]]:
    """Return a detached bilingual catalog for reports and composition plans."""
    return [
        {
            "schema": MACRO_MODULE_SCHEMA,
            "module_id": str(item["module_id"]),
            "name": dict(item["name"]),
            "independent": bool(item["independent"]),
            "categories": list(item["categories"]),
            "capabilities": list(item["capabilities"]),
            "dependencies": list(item["dependencies"]),
        }
        for item in MACRO_MODULE_DEFINITIONS
    ]
