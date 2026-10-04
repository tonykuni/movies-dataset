"""Layered bilingual knowledge-body projection over immutable evidence registers."""

from __future__ import annotations

from typing import Any

from .bilingual_ops import bilingual_label, build_glossary


LAYER_DEFINITIONS = (
    ("requirements", "需求", "Requirements", ("requirement",)),
    ("decisions", "決策", "Decisions", ("decision",)),
    ("questions_issues", "問題與議題", "Questions and Issues", ("question", "issue")),
    ("procedures", "指令與程序", "Instructions and Procedures", ("action", "prerequisite", "verification", "prohibition")),
    ("parameters", "參數", "Parameters", ("parameter",)),
    ("context", "背景知識", "Context", ("context",)),
)


def build_bilingual_knowledge_body(
    source_text: str,
    topics: list[dict[str, Any]],
    knowledge_registry: dict[str, Any],
    instruction_registry: dict[str, Any],
    code_reconstruction: dict[str, Any],
) -> dict[str, Any]:
    glossary = build_glossary(source_text)
    units = knowledge_registry["knowledge_units"]
    topic_views = []
    for topic in topics:
        topic_units = [item for item in units if topic["topic_id"] in item.get("topic_ids", [])]
        topic_views.append(
            {
                "topic_id": topic["topic_id"],
                "title": bilingual_label(topic["title"], glossary),
                "keywords": [bilingual_label(item, glossary) for item in topic.get("keywords", [])],
                "knowledge_ids": [item["knowledge_id"] for item in topic_units],
                "source_segments": topic["segment_ids"],
                "episode_ids": [item["episode_id"] for item in topic.get("episodes", [])],
                "recurrence_count": topic.get("recurrence_count", 0),
            }
        )
    layers = []
    covered: set[str] = set()
    for layer_id, zh, en, roles in LAYER_DEFINITIONS:
        matching = [item for item in units if set(item.get("roles", [])) & set(roles)]
        covered.update(item["knowledge_id"] for item in matching)
        layers.append(
            {
                "layer_id": layer_id,
                "label": {"zh": zh, "en": en},
                "knowledge_ids": [item["knowledge_id"] for item in matching],
                "count": len(matching),
            }
        )
    return {
        "schema": "VIA_BILINGUAL_KNOWLEDGE_BODY/1.0",
        "languages": ["zh", "en"],
        "topics": topic_views,
        "layers": layers,
        "instruction_ids": [item["instruction_id"] for item in instruction_registry["instructions"]],
        "command_ids": [item["command_id"] for item in instruction_registry["command_units"]],
        "procedure_ids": [item["procedure_id"] for item in instruction_registry["procedures"]],
        "code_family_ids": [item["family_id"] for item in code_reconstruction["families"]],
        "conflict_ids": [item["conflict_id"] for item in knowledge_registry["conflict_register"]],
        "unclassified_knowledge_ids": [item["knowledge_id"] for item in units if item["knowledge_id"] not in covered],
        "evidence_contract": {
            "source_of_truth": "source_ledger",
            "knowledge_registry_join_key": "knowledge_id",
            "instruction_registry_join_key": "instruction_id_or_command_id",
            "code_join_key": "family_id",
            "all_labels_are_derivative": True,
            "unknown_translation_policy": "preserve_source_and_mark_needs_translation",
        },
    }
