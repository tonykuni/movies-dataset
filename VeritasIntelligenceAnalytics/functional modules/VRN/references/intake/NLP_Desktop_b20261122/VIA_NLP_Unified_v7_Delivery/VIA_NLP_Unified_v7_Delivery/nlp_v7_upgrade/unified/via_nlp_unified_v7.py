from __future__ import annotations

import atexit
import hashlib
import json
import re
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "nlp_v7_upgrade"
VENDOR_PROJECT = WORKSPACE / "vendor" / "VIA_NLP_Application_System_v1.8.0"
VENDOR_SRC = VENDOR_PROJECT / "src"
VENDOR_CONFIG = VENDOR_PROJECT / "config" / "default.json"
RUNTIME_DIR = ROOT / "app" / "v7_runtime"

if str(VENDOR_SRC) not in sys.path:
    sys.path.insert(0, str(VENDOR_SRC))

from via_nlp_engine import VIAEngine  # type: ignore  # vendored, pinned source

ENGINE_ID = "VIA-ENG-021"
ENGINE_VERSION = "7.0.0"
ADAPTER_SCHEMA = "VIA_UNIFIED_NLP_ADAPTER/7.0"

_ENGINE: VIAEngine | None = None
_ENGINE_LOCK = threading.RLock()
_PROCESS_LOCK = threading.RLock()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_engine() -> VIAEngine:
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is None:
            _ENGINE = VIAEngine(
                config_path=VENDOR_CONFIG,
                overrides={
                    "engine": {
                        "data_dir": str(RUNTIME_DIR),
                        "name": "VIA Unified NLP Evidence Reconstruction Engine",
                        "max_text_chars": 2_000_000,
                        "max_concurrency": 1,
                    },
                    "routing": {
                        "allow_tiers": [1, 2],
                        "default_tier": 1,
                        "allow_deep_models": False,
                        "allow_llm": False,
                    },
                    "knowledge": {
                        "cpu_tools": {"use_available_providers": False},
                    },
                    "security": {
                        "offline": True,
                        "allow_remote_bind": False,
                        "require_api_key": False,
                    },
                },
                auto_start=False,
            )
            _ENGINE.start()
        return _ENGINE


def close_engine() -> None:
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is not None:
            _ENGINE.close()
            _ENGINE = None


atexit.register(close_engine)


def _label(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("zh") or value.get("en") or next(iter(value.values()), "node"))
    return str(value or "node")


def mind_map_mermaid(mind_map: dict[str, Any], max_nodes: int = 80, max_edges: int = 140) -> str:
    """Render a bounded evidence graph without executing or modifying it."""
    ai_view = mind_map.get("ai_view", {}) if isinstance(mind_map, dict) else {}
    nodes = list(ai_view.get("nodes", []))[:max_nodes]
    node_ids = {str(item.get("node_id")): f"N{index:03d}" for index, item in enumerate(nodes, 1)}
    lines = ["flowchart LR"]
    for original, alias in node_ids.items():
        item = next(item for item in nodes if str(item.get("node_id")) == original)
        label = re.sub(r'["\\\n\r]', " ", _label(item.get("label"))[:100])
        node_type = re.sub(r'["\\\n\r]', " ", str(item.get("node_type", "node"))[:40])
        lines.append(f'    {alias}["{node_type}: {label}"]')
    seen: set[tuple[str, str, str]] = set()
    for edge in list(ai_view.get("edges", []))[:max_edges]:
        left = node_ids.get(str(edge.get("from")))
        right = node_ids.get(str(edge.get("to")))
        if not left or not right:
            continue
        relation = re.sub(r'["\\\n\r|]', " ", str(edge.get("relation", "related"))[:50])
        key = (left, right, relation)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'    {left} -->|"{relation}"| {right}')
    return "\n".join(lines) + "\n"


def _quality_summary(output: dict[str, Any]) -> dict[str, Any]:
    gates = output.get("quality_gates", {})
    content = output.get("content_role_analysis", {})
    summarizer = content.get("summarizer", {})
    body = summarizer.get("body_summary", {})
    full = summarizer.get("full_input_summary", {})
    context = output.get("context_reconstruction", {}).get("statistics", {})
    instructions = output.get("instruction_reconstruction", {}).get("statistics", {})
    composition = output.get("module_composition_registry", {}).get("statistics", {})
    return {
        "source_reconstruction": gates.get("source_reconstruction"),
        "source_text_mutated": gates.get("source_writeback_applied", False),
        "fact_integrity": gates.get("fact_integrity"),
        "knowledge_units": gates.get("knowledge_units"),
        "knowledge_conflicts": gates.get("knowledge_conflicts"),
        "topics": len(output.get("body_of_knowledge", {}).get("topics", [])),
        "context_threads": context.get("topic_threads", 0),
        "reply_links": context.get("reply_links", 0),
        "unanswered_questions": context.get("unanswered_questions", 0),
        "instructions": instructions.get("instruction_count", 0),
        "commands": instructions.get("command_count", 0),
        "composition_modules": composition.get("modules", 0),
        "composition_components": composition.get("components", 0),
        "body_summary_evidence_integrity": body.get("quality", {}).get("evidence_hashes_valid", False),
        "full_summary_evidence_integrity": full.get("quality", {}).get("evidence_hashes_valid", False),
        "body_chunk_representation_rate": body.get("quality", {}).get("chunk_representation_rate", 0),
        "full_chunk_representation_rate": full.get("quality", {}).get("chunk_representation_rate", 0),
        "mind_map_graph_endpoints_valid": gates.get("cpu_graph_endpoints_valid"),
        "automatic_code_merge": gates.get("automatic_code_merge", False),
        "command_execution_authorized": gates.get("command_execution_authorized", False),
    }


def process_text(source_name: str, text: str, quality: str = "balanced") -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if len(text) > 2_000_000:
        raise ValueError("v7 unified engine maximum is 2,000,000 characters; split into reviewed bundles")
    with _PROCESS_LOCK:
        result = _get_engine().process({
            "text": text,
            "task": "knowledge",
            "quality": quality if quality in {"fast", "balanced", "deep"} else "balanced",
            "options": {"bundle_mode": False},
        }).to_dict()
    output = result["output"]
    source_sha = _sha256(text)
    projection = {
        "schema": ADAPTER_SCHEMA,
        "engine": {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION, "base_engine_version": result.get("engine_version")},
        "source": {"source_name": source_name, "source_sha256": source_sha, "source_characters": len(text)},
        "compatibility": {
            "v5_projection_preserved": True,
            "v18_output_additive": True,
            "source_is_immutable": True,
            "all_derivatives_are_reviewable": True,
        },
        "capabilities": [
            "complete_evidence_summary", "content_role_and_layout_analysis", "context_thread_reconstruction",
            "instruction_and_command_reconstruction", "bilingual_knowledge_body", "typed_mind_map",
            "mind_map_evolution", "module_composition", "function_classification", "cpu_provider_governance",
        ],
        "quality": _quality_summary(output),
        "output_contracts": sorted(output),
    }
    return {
        "schema": "VIA_UNIFIED_NLP_RESULT/7.0",
        "projection": projection,
        "full_output": output,
        "mind_map_mermaid": mind_map_mermaid(output.get("mind_map", {})),
        "engine_result": {
            "task": result.get("task"),
            "language": result.get("language"),
            "route": result.get("route"),
            "elapsed_ms": result.get("elapsed_ms"),
            "cache_hit": result.get("cache_hit"),
            "warnings": result.get("warnings", []),
        },
    }


def artifact_payloads(result: dict[str, Any]) -> dict[str, Any]:
    output = result["full_output"]
    return {
        "v7_unified.json": result,
        "v7_summary.json": output.get("content_role_analysis", {}).get("summarizer", {}),
        "v7_knowledge_body.json": output.get("body_of_knowledge", {}),
        "v7_context_reconstruction.json": output.get("context_reconstruction", {}),
        "v7_instruction_reconstruction.json": output.get("instruction_reconstruction", {}),
        "v7_module_composition.json": output.get("module_composition_registry", {}),
        "v7_content_roles.json": output.get("content_role_analysis", {}),
        "v7_function_classification.json": output.get("function_classification", {}),
        "v7_source_ledger.json": {
            "source_ledger": output.get("source_ledger", []),
            "completeness": output.get("completeness", {}),
        },
        "v7_mind_map.json": output.get("mind_map", {}),
        "v7_mind_map_evolution.json": output.get("mind_map_evolution", {}),
        "v7_mind_map.mmd": result["mind_map_mermaid"],
        "v7_quality_gates.json": output.get("quality_gates", {}),
    }
