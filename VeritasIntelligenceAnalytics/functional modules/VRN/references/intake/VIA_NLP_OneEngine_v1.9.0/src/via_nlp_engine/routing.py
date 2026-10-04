"""Task-to-tier routing with deterministic pressure fallback."""

from __future__ import annotations

from typing import Any

from .schemas import ProcessRequest, ResourceSnapshot, RouteDecision


TASK_TIERS = {
    "normalize": 1,
    "repair": 1,
    "keywords": 1,
    "classify": 1,
    "reorganize": 2,
    "knowledge": 2,
    "govern": 2,
    "translate": 3,
    "analyze": 2,
    "entities": 2,
    "structure": 2,
    "restore_transcript": 2,
    "summarize": 1,
    "embed": 3,
    "chat": 4,
}

PIPELINES = {
    "normalize": ["sanitize", "normalize"],
    "repair": ["sanitize", "language", "lexicon", "punctuation", "diff"],
    "keywords": ["sanitize", "tokenize", "frequency"],
    "classify": ["sanitize", "online_ml_or_rules"],
    "reorganize": ["lossless_segment", "cpu_hierarchical_topics", "topic_return_links", "refinement_ledger", "source_ledger"],
    "knowledge": ["reorganize", "human_mind_map", "ai_typed_graph", "ssot_candidates", "via_keywords", "code_blueprint", "optional_deep_semantics"],
    "govern": ["knowledge", "three_round_panorama", "six_pipeline_matrix", "hydra_gate", "evolution_quality_gates"],
    "translate": ["lossless_chunk", "translation_memory", "explicit_backend", "bilingual_ledger"],
    "analyze": ["repair", "document_type", "structure", "extractive_summary", "entities", "classification"],
    "entities": ["sanitize", "regex_ner", "optional_spacy_ner"],
    "structure": ["repair", "document_type", "schema_projection"],
    "restore_transcript": ["repair", "transcript_projection", "diff"],
    "summarize": ["sanitize", "extractive_summary", "optional_llm"],
    "embed": ["sanitize", "chunk", "embedding"],
    "chat": ["sanitize", "optional_retrieval", "ollama"],
}


class TaskRouter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def decide(self, request: ProcessRequest, resources: ResourceSnapshot) -> RouteDecision:
        task = "analyze" if request.task == "auto" else request.task
        if task not in TASK_TIERS:
            raise ValueError(f"Unsupported task: {task}")
        requested = request.tier or TASK_TIERS[task]
        if request.quality == "deep" and task in {"knowledge", "reorganize", "govern"}:
            requested = 3
        elif request.quality == "deep" and task in {"summarize", "analyze", "structure"}:
            requested = 4
        allowed = sorted(int(item) for item in self.config["allow_tiers"])
        if requested not in allowed:
            requested = max(tier for tier in allowed if tier <= requested) if any(tier <= requested for tier in allowed) else min(allowed)

        selected = requested
        reason = ""
        if selected >= 4 and not self.config["allow_llm"]:
            selected = min(2, max(allowed))
            reason = "LLM is opt-in and currently disabled"
        if selected == 3 and not self.config["allow_deep_models"]:
            raise RuntimeError("Embedding task requires routing.allow_deep_models=true")
        if resources.pressure == "critical":
            raise RuntimeError("Critical resource pressure")
        if selected >= 4 and resources.available_ram_mb > 0 and resources.available_ram_mb < float(self.config["llm_min_available_ram_mb"]):
            raise RuntimeError("Available RAM is below the configured LLM minimum")
        if selected == 3 and resources.available_ram_mb > 0 and resources.available_ram_mb < float(self.config["deep_min_available_ram_mb"]):
            raise RuntimeError("Available RAM is below the configured deep-model minimum")
        if resources.pressure == "shed" and self.config["fallback_on_pressure"]:
            selected = 1
            reason = "Resource pressure fallback"
        elif resources.pressure == "warning" and selected >= 3 and self.config["fallback_on_pressure"]:
            selected = 2
            reason = "Heavy tier deferred under warning pressure"
        if task in {"embed", "chat", "translate"} and selected < TASK_TIERS[task]:
            raise RuntimeError(f"{task} cannot produce a safe lower-tier substitute")
        return RouteDecision(
            task=task,
            requested_tier=requested,
            selected_tier=selected,
            pipeline=list(PIPELINES[task]),
            degraded=selected != requested,
            reason=reason,
        )
