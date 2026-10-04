"""Standard template reconstruction around immutable source references."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


TEMPLATE_SCHEMA = "VIA_TEMPLATE_RECONSTRUCTION/1.0"
TEMPLATE_DEFINITIONS = {
    "article": {
        "schema": "VIA_ARTICLE_TEMPLATE/1.0",
        "required": ["heading", "context", "result"],
    },
    "dialogue": {
        "schema": "VIA_DIALOGUE_TEMPLATE/1.0",
        "required": ["context", "question", "answer", "decision"],
    },
    "mixed": {
        "schema": "VIA_TECHNICAL_SPEC_TEMPLATE/1.0",
        "required": ["context", "requirement", "decision", "verification"],
    },
    "code_heavy": {
        "schema": "VIA_CODE_TEMPLATE/1.0",
        "required": ["requirement", "code", "verification"],
    },
}


def _stable_id(*values: str) -> str:
    return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()[:16].upper()


class StandardTemplateReconstructor:
    """Create a source-filled template and an explicit missing-slot queue."""

    def build(self, source_text: str, context_reconstruction: dict[str, Any]) -> dict[str, Any]:
        mode = str(context_reconstruction["document_mode"]["value"])
        definition = TEMPLATE_DEFINITIONS[mode]
        slots: list[dict[str, Any]] = []
        counts: Counter[str] = Counter()
        for unit in context_reconstruction.get("chronological_view", []):
            labels = [str(item["label"]) for item in unit.get("functional_labels", [])]
            for label in labels:
                counts[label] += 1
                slots.append(
                    {
                        "slot_id": f"SLOT-{_stable_id(unit['context_unit_id'], label)}",
                        "slot_type": label,
                        "slot_label": next(
                            item["bilingual"] for item in unit["functional_labels"] if item["label"] == label
                        ),
                        "source_order": unit["source_order"],
                        "source_segment": unit["source_segment"],
                        "source_sha256": unit["source_sha256"],
                        "source_text": unit["source_text"],
                        "filled_from_source": True,
                        "generated_content": False,
                    }
                )
        missing = [item for item in definition["required"] if not counts[item]]
        source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        return {
            "schema": TEMPLATE_SCHEMA,
            "selected_template": {
                "template_schema": definition["schema"],
                "mode": mode,
                "languages": ["zh", "en"],
                "selection_basis": context_reconstruction["document_mode"]["evidence"],
            },
            "required_slots": definition["required"],
            "missing_required_slots": missing,
            "slots": slots,
            "template_skeleton": [
                {
                    "slot_type": slot_type,
                    "slot_refs": [item["slot_id"] for item in slots if item["slot_type"] == slot_type],
                    "status": "source_filled" if counts[slot_type] else "missing_requires_review",
                }
                for slot_type in list(dict.fromkeys(definition["required"] + [item["slot_type"] for item in slots]))
            ],
            "repair_proposals": [
                {
                    "proposal_id": f"TPLFIX-{_stable_id(definition['schema'], item)}",
                    "slot_type": item,
                    "action": "locate_additional_source_or_mark_not_applicable",
                    "automatic_fill": False,
                    "status": "candidate_only",
                }
                for item in missing
            ],
            "source_integrity": {
                "source_characters": len(source_text),
                "source_sha256": source_sha256,
                "canonical_reconstruction_path": "source_ledger_in_source_order",
                "template_slots_replace_source_ledger": False,
            },
            "quality_gates": {
                "source_ledger_is_canonical": True,
                "automatic_slot_fill": False,
                "automatic_source_reorder": False,
                "invented_facts": False,
                "template_is_derivative": True,
                "ready": not missing,
            },
        }
