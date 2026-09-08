"""Append-only Mind Map snapshot comparison and reviewable correction proposals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


MAX_PREVIOUS_PACKAGE_BYTES = 128 * 1024 * 1024


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _node_identity(node: dict[str, Any], source_hashes: dict[str, str]) -> str:
    node_type = str(node.get("node_type", "unknown"))
    if node_type == "knowledge_root":
        return "knowledge_root|ROOT"
    if node_type == "source_segment" and node.get("source_sha256"):
        return f"source_segment|{node['source_sha256']}"
    if node_type in {"knowledge_unit", "code_family", "instruction", "command"}:
        return f"{node_type}|{node.get('node_id')}"
    if node_type in {"topic", "topic_episode"}:
        grounded_hashes = [
            source_hashes[segment_id]
            for segment_id in node.get("source_segments", [])
            if segment_id in source_hashes
        ]
        if grounded_hashes:
            return f"{node_type}|first_source|{grounded_hashes[0]}"
    if node_type == "topic":
        keywords = sorted(str(item).casefold() for item in node.get("keywords", []))
        return f"topic|{_sha256_json(keywords)[:20]}"
    return f"{node_type}|{node.get('node_id')}|{_sha256_json(node.get('label', ''))[:12]}"


def _node_payload_hash(node: dict[str, Any]) -> str:
    selected = {
        key: value
        for key, value in node.items()
        if key not in {"node_id", "stable_identity", "lifecycle"}
    }
    return _sha256_json(selected)


def load_previous_reconstruction(path: str | Path) -> dict[str, Any]:
    selected = Path(path).expanduser().resolve(strict=True)
    if not selected.is_file():
        raise ValueError("Previous reconstruction must be a JSON file")
    if selected.stat().st_size > MAX_PREVIOUS_PACKAGE_BYTES:
        raise ValueError("Previous reconstruction exceeds the 128 MiB safety limit")
    value = json.loads(selected.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Previous reconstruction root must be a JSON object")
    if "process_result" in value:
        output = value.get("process_result", {}).get("output", {})
        mind_map = output.get("mind_map")
        evolution = output.get("mind_map_evolution")
    elif "ai_view" in value:
        mind_map = value
        evolution = None
    elif "mind_map" in value:
        mind_map = value.get("mind_map")
        evolution = value.get("mind_map_evolution")
    else:
        raise ValueError("Previous JSON does not contain a recognized Mind Map")
    if not isinstance(mind_map, dict) or not isinstance(mind_map.get("ai_view"), dict):
        raise ValueError("Previous Mind Map is missing ai_view")
    return {"mind_map": mind_map, "mind_map_evolution": evolution, "path": str(selected)}


def build_mind_map_evolution(
    current_mind_map: dict[str, Any],
    previous: dict[str, Any] | None = None,
    conflict_register: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    current_nodes = current_mind_map["ai_view"].get("nodes", [])
    current_edges = current_mind_map["ai_view"].get("edges", [])
    previous_map = previous.get("mind_map") if previous else None
    previous_nodes = previous_map.get("ai_view", {}).get("nodes", []) if previous_map else []
    previous_edges = previous_map.get("ai_view", {}).get("edges", []) if previous_map else []

    current_source_hashes = {
        str(item.get("node_id")): str(item.get("source_sha256"))
        for item in current_nodes
        if item.get("node_type") == "source_segment" and item.get("source_sha256")
    }
    previous_source_hashes = {
        str(item.get("node_id")): str(item.get("source_sha256"))
        for item in previous_nodes
        if item.get("node_type") == "source_segment" and item.get("source_sha256")
    }
    current_by_identity = {_node_identity(item, current_source_hashes): item for item in current_nodes}
    previous_by_identity = {_node_identity(item, previous_source_hashes): item for item in previous_nodes}
    added = sorted(set(current_by_identity) - set(previous_by_identity))
    retired = sorted(set(previous_by_identity) - set(current_by_identity))
    shared = sorted(set(current_by_identity) & set(previous_by_identity))
    retained = [
        identity
        for identity in shared
        if _node_payload_hash(current_by_identity[identity]) == _node_payload_hash(previous_by_identity[identity])
    ]
    updated = [identity for identity in shared if identity not in retained]

    current_id_to_identity = {str(item.get("node_id")): identity for identity, item in current_by_identity.items()}
    previous_id_to_identity = {str(item.get("node_id")): identity for identity, item in previous_by_identity.items()}

    def edge_key(edge: dict[str, Any], lookup: dict[str, str]) -> str:
        left = lookup.get(str(edge.get("from")), str(edge.get("from")))
        right = lookup.get(str(edge.get("to")), str(edge.get("to")))
        return f"{left}|{edge.get('relation')}|{right}"

    current_edge_keys = {edge_key(item, current_id_to_identity) for item in current_edges}
    previous_edge_keys = {edge_key(item, previous_id_to_identity) for item in previous_edges}
    edge_added = sorted(current_edge_keys - previous_edge_keys)
    edge_retired = sorted(previous_edge_keys - current_edge_keys)
    previous_evolution = previous.get("mind_map_evolution") if previous else None
    previous_sequence = (
        int(previous_evolution.get("version", {}).get("sequence", 1))
        if isinstance(previous_evolution, dict)
        else 1 if previous_map is not None else 0
    )
    current_hash = _sha256_json(current_mind_map)
    previous_hash = _sha256_json(previous_map) if previous_map else None

    proposals: list[dict[str, Any]] = []
    for action, identities, review in (
        ("add_node", added, False),
        ("update_node", updated, True),
        ("deprecate_node_candidate", retired, True),
        ("add_edge", edge_added, False),
        ("retire_edge_candidate", edge_retired, True),
    ):
        proposals.extend(
            {
                "proposal_id": f"MMFIX-{hashlib.sha256(f'{action}|{identity}'.encode()).hexdigest()[:16].upper()}",
                "action": action,
                "target_identity": identity,
                "review_required": review,
                "applied_to_previous_snapshot": False,
                "status": "candidate_only",
            }
            for identity in identities
        )
    for conflict in conflict_register or []:
        proposals.append(
            {
                "proposal_id": f"MMFIX-CONFLICT-{str(conflict.get('conflict_id', 'UNKNOWN')).split('-')[-1]}",
                "action": "resolve_knowledge_conflict",
                "target_identity": conflict.get("conflict_id"),
                "review_required": True,
                "applied_to_previous_snapshot": False,
                "status": "human_resolution_required",
            }
        )
    delta_core = {
        "nodes": {"added": added, "retained": retained, "updated": updated, "deprecation_candidates": retired},
        "edges": {"added": edge_added, "retained_count": len(current_edge_keys & previous_edge_keys), "retirement_candidates": edge_retired},
    }
    return {
        "schema": "VIA_MIND_MAP_EVOLUTION/1.0",
        "version": {
            "sequence": previous_sequence + 1,
            "snapshot_sha256": current_hash,
            "previous_snapshot_sha256": previous_hash,
            "delta_sha256": _sha256_json(delta_core),
            "chain_status": "genesis" if previous_map is None else "linked_to_previous_snapshot",
        },
        "delta": delta_core,
        "correction_proposals": proposals,
        "progressive_stages": [
            {"stage": 1, "zh": "不可變來源擷取", "en": "Immutable Source Intake", "automatic": True},
            {"stage": 2, "zh": "指令、知識與程式抽取", "en": "Instruction, Knowledge and Code Extraction", "automatic": True},
            {"stage": 3, "zh": "暫定 Mind Map", "en": "Provisional Mind Map", "automatic": True},
            {"stage": 4, "zh": "衝突與版本差異閘門", "en": "Conflict and Version Delta Gate", "automatic": True},
            {"stage": 5, "zh": "中英文結構投影", "en": "Chinese/English Structural Projection", "automatic": True},
            {"stage": 6, "zh": "人工核准動態修正", "en": "Human Approval of Dynamic Corrections", "automatic": False},
        ],
        "quality_gates": {
            "silent_node_deletion": False,
            "silent_edge_deletion": False,
            "automatic_conflict_resolution": False,
            "automatic_canonical_mutation": False,
            "rollback_reference_available": previous_hash is not None,
            "stable_identity_count": len(current_by_identity),
        },
    }
