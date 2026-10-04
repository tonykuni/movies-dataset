"""Static, non-executing reconstruction of code pasted across discussions."""

from __future__ import annotations

import copy
import hashlib
import re
from collections import defaultdict
from typing import Any


DEFAULT_MAX_CODE_FAMILIES = 500
KNOWN_CALLS = {
    "bool",
    "dict",
    "enumerate",
    "float",
    "int",
    "len",
    "list",
    "max",
    "min",
    "open",
    "print",
    "range",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _family_signature(block: dict[str, Any]) -> str:
    spec = block["engine_spec"]
    symbols = list(spec.get("functions", [])) + list(spec.get("classes", []))
    if symbols:
        return f"{block['language']}|symbols|{'|'.join(sorted(set(symbols)))}"
    structural = re.sub(r"(?:\s+|#[^\n]*|//[^\n]*)", " ", block["code"]).strip()
    structural = re.sub(r"(?:\d+(?:\.\d+)?|'[^']*'|\"[^\"]*\")", "<VALUE>", structural)
    return f"{block['language']}|structure|{structural[:500]}"


def _syntax_rank(status: str) -> int:
    return {
        "valid": 4,
        "valid_lexical_only": 3,
        "unchecked": 2,
        "parser_failed": 1,
        "invalid": 0,
    }.get(status, 1)


class CodeDiscussionReconstructor:
    """Create revision families, symbol registry and interface review gates."""

    def __init__(self, max_families: int = DEFAULT_MAX_CODE_FAMILIES) -> None:
        self.max_families = max(1, int(max_families))

    def build(self, code_blocks: list[dict[str, Any]]) -> dict[str, Any]:
        enriched = copy.deepcopy(code_blocks)
        family_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        overflow_blocks: list[str] = []
        for block in enriched:
            signature = _family_signature(block)
            if signature not in family_groups and len(family_groups) >= self.max_families:
                overflow_blocks.append(block["code_id"])
                continue
            family_groups[signature].append(block)

        families: list[dict[str, Any]] = []
        exact_duplicate_count = 0
        for signature, members in sorted(
            family_groups.items(),
            key=lambda item: min(int(block["source_span"]["start"]) for block in item[1]),
        ):
            family_id = f"CODEFAM-{_sha256_text(signature)[:12].upper()}"
            ordered = sorted(members, key=lambda item: (int(item["source_span"]["start"]), item["code_id"]))
            first_by_hash: dict[str, str] = {}
            nonduplicates: list[dict[str, Any]] = []
            for revision, block in enumerate(ordered, start=1):
                duplicate_of = first_by_hash.get(block["sha256"])
                block["family_id"] = family_id
                block["revision"] = revision
                block["duplicate_of"] = duplicate_of
                block["revision_status"] = "exact_duplicate" if duplicate_of else "distinct_revision"
                block["canonical_promotion"] = "not_applied"
                if duplicate_of:
                    exact_duplicate_count += 1
                else:
                    first_by_hash[block["sha256"]] = block["code_id"]
                    nonduplicates.append(block)
            ranked_candidates = sorted(
                nonduplicates,
                key=lambda item: (
                    _syntax_rank(str(item["syntax"].get("status", "unchecked"))),
                    int(item["source_span"]["start"]),
                ),
                reverse=True,
            )
            candidate = ranked_candidates[0] if ranked_candidates else ordered[0]
            candidate["canonical_promotion"] = "candidate_requires_review"
            revisions = [
                {
                    "code_id": block["code_id"],
                    "revision": block["revision"],
                    "sha256": block["sha256"],
                    "duplicate_of": block["duplicate_of"],
                    "syntax_status": block["syntax"].get("status"),
                    "source_segments": block["source_segments"],
                    "canonical_promotion": block["canonical_promotion"],
                }
                for block in ordered
            ]
            families.append(
                {
                    "family_id": family_id,
                    "signature": signature,
                    "language": ordered[0]["language"],
                    "code_ids": [item["code_id"] for item in ordered],
                    "revision_count": len(ordered),
                    "distinct_revision_count": len(nonduplicates),
                    "exact_duplicate_count": len(ordered) - len(nonduplicates),
                    "candidate_code_id": candidate["code_id"],
                    "candidate_basis": "latest_highest_static_syntax_rank",
                    "candidate_applied": False,
                    "review_required": len(nonduplicates) > 1 or candidate["syntax"].get("status") != "valid",
                    "revisions": revisions,
                }
            )

        symbol_registry, symbol_conflicts = self._symbol_registry(enriched)
        interface_graph = self._interface_graph(enriched, symbol_registry)
        invalid_blocks = [
            item["code_id"] for item in enriched if item["syntax"].get("status") == "invalid"
        ]
        review_reasons = []
        family_reviews = [item["family_id"] for item in families if item["review_required"]]
        if family_reviews:
            review_reasons.append("revision_or_lexical_family_review")
        if invalid_blocks:
            review_reasons.append("invalid_code_fragments")
        if symbol_conflicts:
            review_reasons.append("symbol_revision_or_owner_conflicts")
        if interface_graph["ambiguous_calls"]:
            review_reasons.append("ambiguous_interfaces")
        if interface_graph["unresolved_calls"]:
            review_reasons.append("unresolved_interfaces")
        low_confidence_languages = [
            item["code_id"]
            for item in enriched
            if item.get("language_detection", {}).get("review_required", False)
        ]
        if low_confidence_languages:
            review_reasons.append("low_confidence_language_detection")
        if overflow_blocks:
            review_reasons.append("family_capacity_overflow")
        return {
            "schema": "VIA_CODE_RECONSTRUCTION/3.0",
            "code_blocks": enriched,
            "families": families,
            "symbol_registry": symbol_registry,
            "symbol_conflicts": symbol_conflicts,
            "interface_graph": interface_graph,
            "language_summary": self._language_summary(enriched),
            "build_readiness": {
                "status": "review_required" if review_reasons else "static_blueprint_ready",
                "review_reasons": review_reasons,
                "invalid_code_ids": invalid_blocks,
                "review_family_ids": family_reviews,
                "overflow_code_ids": overflow_blocks,
                "low_confidence_language_code_ids": low_confidence_languages,
                "exact_duplicate_blocks": exact_duplicate_count,
                "automatic_code_merge": False,
                "automatic_file_write": False,
                "execution_authorized": False,
            },
            "reconstruction_stages": [
                {"stage": 1, "name": "language_and_source_detection", "automatic": True},
                {"stage": 2, "name": "exact_duplicate_collapse", "automatic": True},
                {"stage": 3, "name": "revision_family_reconstruction", "automatic": True},
                {"stage": 4, "name": "symbol_and_interface_review", "automatic": False},
                {"stage": 5, "name": "human_canonical_selection", "automatic": False},
                {"stage": 6, "name": "sandbox_test_and_activation", "automatic": False},
            ],
        }

    @staticmethod
    def _symbol_registry(
        blocks: list[dict[str, Any]],
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
        registry: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for block in blocks:
            spec = block["engine_spec"]
            contracts = {item["name"]: item for item in spec.get("function_contracts", [])}
            for name in spec.get("functions", []):
                contract = contracts.get(name, {"name": name, "arguments": [], "returns": None})
                registry[f"function:{name}"].append(
                    {
                        "code_id": block["code_id"],
                        "family_id": block.get("family_id"),
                        "language": block["language"],
                        "contract": contract,
                        "contract_sha256": _sha256_text(repr(contract)),
                        "code_sha256": block["sha256"],
                    }
                )
            for name in spec.get("classes", []):
                registry[f"class:{name}"].append(
                    {
                        "code_id": block["code_id"],
                        "family_id": block.get("family_id"),
                        "language": block["language"],
                        "code_sha256": block["sha256"],
                    }
                )
        conflicts = []
        for symbol, owners in sorted(registry.items()):
            distinct_code = {item["code_sha256"] for item in owners}
            distinct_families = {item["family_id"] for item in owners}
            if len(distinct_code) > 1 or len(distinct_families) > 1:
                conflicts.append(
                    {
                        "symbol": symbol,
                        "owners": owners,
                        "status": "revision_or_owner_conflict",
                        "resolution": "human_required",
                    }
                )
        return dict(sorted(registry.items())), conflicts

    @staticmethod
    def _interface_graph(
        blocks: list[dict[str, Any]],
        symbol_registry: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        owners_by_name = {
            symbol.split(":", 1)[1]: owners
            for symbol, owners in symbol_registry.items()
            if symbol.startswith("function:")
        }
        edges: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        ambiguous: list[dict[str, Any]] = []
        seen_edges: set[tuple[str, str, str]] = set()
        for block in blocks:
            own_functions = set(block["engine_spec"].get("functions", []))
            for raw_call in block["engine_spec"].get("calls", []):
                call = str(raw_call)
                short = call.split(".")[-1]
                if short in own_functions or short in KNOWN_CALLS:
                    continue
                owners = [item for item in owners_by_name.get(short, []) if item["code_id"] != block["code_id"]]
                owner_families = sorted({item["family_id"] for item in owners if item.get("family_id")})
                if len(owner_families) == 1:
                    key = (owner_families[0], block.get("family_id", block["code_id"]), short)
                    if key not in seen_edges:
                        edges.append(
                            {
                                "from_family": owner_families[0],
                                "to_family": block.get("family_id"),
                                "relation": "provides_symbol_to",
                                "symbol": short,
                                "source_code_id": block["code_id"],
                            }
                        )
                        seen_edges.add(key)
                elif len(owner_families) > 1:
                    ambiguous.append(
                        {
                            "source_code_id": block["code_id"],
                            "call": call,
                            "candidate_families": owner_families,
                            "resolution": "human_required",
                        }
                    )
                elif "." not in call:
                    unresolved.append(
                        {
                            "source_code_id": block["code_id"],
                            "call": call,
                            "resolution": "dependency_or_missing_symbol_review",
                        }
                    )
        return {
            "edges": edges,
            "ambiguous_calls": ambiguous,
            "unresolved_calls": unresolved,
            "automatic_binding": False,
        }

    @staticmethod
    def _language_summary(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for block in blocks:
            grouped[block["language"]].append(block)
        return [
            {
                "language": language,
                "blocks": len(items),
                "valid": sum(item["syntax"].get("status") in {"valid", "valid_lexical_only"} for item in items),
                "invalid": sum(item["syntax"].get("status") == "invalid" for item in items),
                "unchecked": sum(item["syntax"].get("status") == "unchecked" for item in items),
                "declared": sum(item.get("language_detection", {}).get("source") == "declared" for item in items),
                "heuristic": sum(item.get("language_detection", {}).get("source") == "heuristic" for item in items),
                "review_required": sum(item.get("language_detection", {}).get("review_required", False) for item in items),
            }
            for language, items in sorted(grouped.items())
        ]
