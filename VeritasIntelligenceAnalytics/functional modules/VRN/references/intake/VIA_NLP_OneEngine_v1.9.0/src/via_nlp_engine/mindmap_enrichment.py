"""Typed Mind Map enrichment for context, templates, layout and functions."""

from __future__ import annotations

from typing import Any


def enrich_mind_map_v15(
    mind_map: dict[str, Any],
    context_reconstruction: dict[str, Any],
    function_classification: dict[str, Any],
    template_reconstruction: dict[str, Any],
    layout_analysis: dict[str, Any],
    max_edges: int,
) -> dict[str, Any]:
    """Append source-grounded typed nodes without mutating existing identities."""
    ai_view = mind_map["ai_view"]
    nodes = ai_view.setdefault("nodes", [])
    edges = ai_view.setdefault("edges", [])
    known_nodes = {str(item.get("node_id")) for item in nodes}
    known_edges = {
        (str(item.get("from")), str(item.get("to")), str(item.get("relation")))
        for item in edges
    }

    def add_node(node: dict[str, Any]) -> None:
        node_id = str(node["node_id"])
        if node_id not in known_nodes:
            label = node.get("label", node_id)
            if isinstance(label, dict):
                bilingual = {"zh": str(label.get("zh", node_id)), "en": str(label.get("en", label.get("zh", node_id)))}
                node["label"] = bilingual["zh"]
            else:
                bilingual = {"zh": str(label), "en": str(label)}
            node.setdefault("bilingual_label", bilingual)
            nodes.append(node)
            known_nodes.add(node_id)

    def add_edge(left: str, right: str, relation: str, confidence: float = 1.0) -> None:
        key = (left, right, relation)
        if len(edges) < max_edges and key not in known_edges and left in known_nodes and right in known_nodes:
            edges.append({"from": left, "to": right, "relation": relation, "confidence": confidence})
            known_edges.add(key)

    for thread in context_reconstruction.get("topic_threads", []):
        thread_id = str(thread["thread_id"])
        add_node(
            {
                "node_id": thread_id,
                "node_type": "context_thread",
                "label": {"zh": str(thread.get("title") or thread["topic_id"]), "en": str(thread.get("title") or thread["topic_id"])},
                "topic_id": thread["topic_id"],
                "source_segments": thread.get("source_segments", []),
                "return_count": thread.get("return_count", 0),
                "functional_labels": thread.get("functional_labels", []),
            }
        )
        add_edge(str(thread["topic_id"]), thread_id, "has_context_thread")

    for record in function_classification.get("records", []):
        function_id = str(record["function_id"])
        add_node(
            {
                "node_id": function_id,
                "node_type": "function",
                "label": {"zh": record["symbol_name"], "en": record["symbol_name"]},
                "language": record.get("language"),
                "primary_category": record.get("primary_category"),
                "source_segments": record.get("source_segments", []),
                "confidence": record.get("confidence"),
                "review_required": record.get("review_required"),
            }
        )
        parent = str(record.get("family_id") or record.get("code_id"))
        add_edge(parent, function_id, "defines_function", float(record.get("confidence", 0.5)))

    template_root = "TEMPLATE-ROOT"
    selected = template_reconstruction.get("selected_template", {})
    add_node(
        {
            "node_id": template_root,
            "node_type": "standard_template",
            "label": {"zh": "標準模板還原", "en": "Standard Template Reconstruction"},
            "template_schema": selected.get("template_schema"),
            "mode": selected.get("mode"),
            "missing_required_slots": template_reconstruction.get("missing_required_slots", []),
        }
    )
    add_edge("ROOT", template_root, "has_standard_template")
    for skeleton in template_reconstruction.get("template_skeleton", []):
        slot_type = str(skeleton["slot_type"])
        slot_node = f"TEMPLATE-SLOT-TYPE-{slot_type.upper()}"
        add_node(
            {
                "node_id": slot_node,
                "node_type": "template_slot_type",
                "label": {"zh": slot_type, "en": slot_type},
                "status": skeleton.get("status"),
                "slot_refs": skeleton.get("slot_refs", []),
            }
        )
        add_edge(template_root, slot_node, "contains_slot_type")

    layout_root = "LAYOUT-ROOT"
    add_node(
        {
            "node_id": layout_root,
            "node_type": "layout_analysis",
            "label": {"zh": "Markdown 版面分析", "en": "Markdown Layout Analysis"},
            "exact_reconstruction": layout_analysis.get("completeness", {}).get("exact_reconstruction", False),
        }
    )
    add_edge("ROOT", layout_root, "has_layout_analysis")
    for block_type, count in layout_analysis.get("statistics", {}).get("block_type_counts", {}).items():
        layout_type_id = f"LAYOUT-TYPE-{str(block_type).upper()}"
        add_node(
            {
                "node_id": layout_type_id,
                "node_type": "layout_block_type",
                "label": {"zh": str(block_type), "en": str(block_type)},
                "count": count,
            }
        )
        add_edge(layout_root, layout_type_id, "contains_layout_type")

    ai_view["enrichment_schema"] = "VIA_MIND_MAP_ENRICHMENT/1.0"
    ai_view["node_count"] = len(nodes)
    ai_view["edge_count"] = len(edges)
    ai_view["edge_capacity_reached"] = len(edges) >= max_edges
    return mind_map
