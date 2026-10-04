"""Evidence-first knowledge object reconstruction for noisy discussion records."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from typing import Any

from .discourse import infer_content_roles


DEFAULT_MAX_KNOWLEDGE_UNITS = 2000
DEFAULT_MAX_CONFLICTS = 500
MAX_UNIT_TEXT_CHARS = 8000
ROLE_ORDER = ("decision", "requirement", "question", "issue", "action", "parameter", "context")
PARAMETER_ASSIGNMENT_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?P<name>\$?[A-Za-z_][A-Za-z0-9_.-]{1,63})\s*(?:=|:)\s*(?P<value>[^\r\n,;|]{1,160})"
)
EXPLICIT_SUPERSESSION_RE = re.compile(
    r"(?:改為|更新為|取代|覆蓋|以.+為準|最新版|supersed(?:e|ed|es)|replace(?:d)?\s+with|use\s+.+instead)",
    re.I,
)
COMPLETED_RE = re.compile(r"(?:已完成|完成了|已通過|結案|done|completed?|passed?)", re.I)
BLOCKED_RE = re.compile(r"(?:阻塞|卡住|等待|失敗|無法|blocked?|waiting|failed?)", re.I)
APPROVED_RE = re.compile(r"(?:已核准|核准|已確認|確認採用|approved?|confirmed?)", re.I)
PROPOSED_RE = re.compile(r"(?:建議|提議|候選|待確認|propos(?:e|ed|al)|candidate|review)", re.I)
IGNORED_PARAMETER_NAMES = {
    "assistant",
    "author",
    "http",
    "https",
    "role",
    "speaker",
    "system",
    "user",
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_unit(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _normalize_parameter_value(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip(" `\"'。；，,.;")


def _unit_status(roles: list[str], text: str) -> str:
    if COMPLETED_RE.search(text):
        return "completed_claim_requires_evidence"
    if BLOCKED_RE.search(text):
        return "blocked_or_failed_claim"
    if APPROVED_RE.search(text):
        return "recorded_as_confirmed"
    if EXPLICIT_SUPERSESSION_RE.search(text):
        return "supersession_claim_requires_review"
    if "question" in roles:
        return "open_question"
    if PROPOSED_RE.search(text):
        return "proposal"
    if "decision" in roles:
        return "recorded_decision"
    return "recorded_unverified"


def _is_parameter_name(name: str, roles: list[str]) -> bool:
    plain = name.lstrip("$")
    if plain.casefold() in IGNORED_PARAMETER_NAMES:
        return False
    return (
        "parameter" in roles
        or name.startswith("$")
        or "_" in plain
        or plain.upper() == plain
        or plain.casefold().endswith(("config", "threshold", "limit", "path", "url", "date"))
    )


class DiscussionKnowledgeReconstructor:
    """Collapse repeated semantic units while retaining every source occurrence."""

    def __init__(
        self,
        max_units: int = DEFAULT_MAX_KNOWLEDGE_UNITS,
        max_conflicts: int = DEFAULT_MAX_CONFLICTS,
    ) -> None:
        self.max_units = max(1, int(max_units))
        self.max_conflicts = max(1, int(max_conflicts))

    def build(
        self,
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
        topics: list[dict[str, Any]],
    ) -> dict[str, Any]:
        segment_map = {item["segment_id"]: item for item in segments}
        segment_order = {item["segment_id"]: index for index, item in enumerate(segments, start=1)}
        topic_for_segment = {
            segment_id: topic["topic_id"]
            for topic in topics
            for segment_id in topic["segment_ids"]
        }
        units_by_key: dict[str, dict[str, Any]] = {}
        overflow_occurrences = 0

        for refined in refinement_ledger:
            segment_id = refined["segment_id"]
            segment = segment_map[segment_id]
            candidates = refined.get("semantic_units") or [refined.get("optimized_text", "")]
            for unit_index, raw_text in enumerate(candidates, start=1):
                text = str(raw_text).strip()
                if not text:
                    continue
                normalized = _normalize_unit(text)
                if not normalized:
                    continue
                key = _sha256_text(normalized)
                roles = infer_content_roles(text, str(segment.get("kind", "article")))
                occurrence = {
                    "source_segment": segment_id,
                    "source_order": segment_order[segment_id],
                    "semantic_unit_index": unit_index,
                    "topic_id": topic_for_segment.get(segment_id),
                    "speaker": segment.get("speaker"),
                    "timestamp": segment.get("timestamp"),
                    "source_span": segment.get("source_span"),
                    "source_sha256": segment.get("sha256"),
                    "derivative_sha256": _sha256_text(text),
                }
                if key not in units_by_key:
                    if len(units_by_key) >= self.max_units:
                        overflow_occurrences += 1
                        continue
                    units_by_key[key] = {
                        "knowledge_id": f"KU-{key[:16].upper()}",
                        "text": text[:MAX_UNIT_TEXT_CHARS],
                        "text_truncated": len(text) > MAX_UNIT_TEXT_CHARS,
                        "normalized_sha256": key,
                        "roles": list(roles),
                        "status": _unit_status(roles, text),
                        "occurrences": [occurrence],
                        "source_segments": [segment_id],
                        "topic_ids": [topic_for_segment[segment_id]] if segment_id in topic_for_segment else [],
                        "is_derivative": True,
                        "source_of_truth": "source_ledger",
                    }
                else:
                    unit = units_by_key[key]
                    unit["occurrences"].append(occurrence)
                    unit["roles"] = sorted(set(unit["roles"]) | set(roles), key=self._role_sort_key)
                    if segment_id not in unit["source_segments"]:
                        unit["source_segments"].append(segment_id)
                    topic_id = topic_for_segment.get(segment_id)
                    if topic_id and topic_id not in unit["topic_ids"]:
                        unit["topic_ids"].append(topic_id)

        units = sorted(
            units_by_key.values(),
            key=lambda item: (item["occurrences"][0]["source_order"], item["knowledge_id"]),
        )
        registers: dict[str, list[dict[str, Any]]] = {role: [] for role in ROLE_ORDER}
        for unit in units:
            for role in unit["roles"]:
                registers.setdefault(role, []).append(unit)

        parameter_candidates = self._parameter_candidates(units)
        conflicts, supersession_links = self._parameter_conflicts(parameter_candidates)
        duplicate_groups = [
            {
                "knowledge_id": unit["knowledge_id"],
                "occurrence_count": len(unit["occurrences"]),
                "source_segments": unit["source_segments"],
                "deduplication": "normalized_exact_match_only",
            }
            for unit in units
            if len(unit["occurrences"]) > 1
        ]
        evidence_matrix = [
            {
                "knowledge_id": unit["knowledge_id"],
                "source_segments": unit["source_segments"],
                "source_hashes": sorted({item["source_sha256"] for item in unit["occurrences"]}),
                "topic_ids": unit["topic_ids"],
            }
            for unit in units
        ]
        return {
            "schema": "VIA_KNOWLEDGE_OBJECT_REGISTRY/1.0",
            "knowledge_units": units,
            "registers": registers,
            "parameter_register": parameter_candidates,
            "conflict_register": conflicts,
            "supersession_links": supersession_links,
            "duplicate_groups": duplicate_groups,
            "evidence_matrix": evidence_matrix,
            "statistics": {
                "unique_units": len(units),
                "total_occurrences": sum(len(item["occurrences"]) for item in units) + overflow_occurrences,
                "collapsed_duplicate_occurrences": sum(len(item["occurrences"]) - 1 for item in units),
                "parameter_names": len(parameter_candidates),
                "unresolved_conflicts": sum(item["status"] == "unresolved_conflict" for item in conflicts),
                "explicit_supersession_reviews": sum(
                    item["status"] == "explicit_supersession_review" for item in conflicts
                ),
            },
            "quality_gates": {
                "source_traceability": "pass" if all(item["source_segments"] for item in units) else "fail",
                "silent_conflict_resolution": False,
                "automatic_supersession": False,
                "truncated": overflow_occurrences > 0,
                "overflow_occurrences": overflow_occurrences,
            },
        }

    @staticmethod
    def _role_sort_key(role: str) -> tuple[int, str]:
        try:
            return ROLE_ORDER.index(role), role
        except ValueError:
            return len(ROLE_ORDER), role

    @staticmethod
    def _parameter_candidates(units: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        output: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for unit in units:
            if "code" in unit["roles"]:
                continue
            scan_text = re.sub(
                r"^\s*(?:User|Assistant|Human|AI|使用者|助理|系統)\s*[:：]\s*",
                "",
                unit["text"],
                flags=re.I,
            )
            for match in PARAMETER_ASSIGNMENT_RE.finditer(scan_text):
                name = match.group("name")
                if not _is_parameter_name(name, unit["roles"]):
                    continue
                value = _normalize_parameter_value(match.group("value"))
                candidate = {
                    "value": value,
                    "knowledge_id": unit["knowledge_id"],
                    "source_segments": unit["source_segments"],
                    "first_source_order": unit["occurrences"][0]["source_order"],
                    "explicit_supersession_language": bool(EXPLICIT_SUPERSESSION_RE.search(unit["text"])),
                }
                canonical_name = name.lstrip("$").upper()
                if candidate not in output[canonical_name]:
                    output[canonical_name].append(candidate)
        return dict(sorted(output.items()))

    def _parameter_conflicts(
        self,
        parameters: dict[str, list[dict[str, Any]]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        conflicts: list[dict[str, Any]] = []
        supersession_links: list[dict[str, Any]] = []
        for name, candidates in parameters.items():
            values = {_normalize_unit(item["value"]) for item in candidates}
            if len(values) <= 1:
                continue
            explicit = [item for item in candidates if item["explicit_supersession_language"]]
            status = "explicit_supersession_review" if explicit else "unresolved_conflict"
            conflict_id = f"KCONFLICT-{_sha256_text(name + '|' + '|'.join(sorted(values)))[:12].upper()}"
            conflicts.append(
                {
                    "conflict_id": conflict_id,
                    "kind": "parameter_value_conflict",
                    "parameter": name,
                    "candidates": candidates,
                    "status": status,
                    "resolution": "human_required",
                }
            )
            for latest in explicit:
                earlier = [
                    item
                    for item in candidates
                    if item["first_source_order"] < latest["first_source_order"]
                    and _normalize_unit(item["value"]) != _normalize_unit(latest["value"])
                ]
                for prior in earlier:
                    supersession_links.append(
                        {
                            "from_knowledge_id": prior["knowledge_id"],
                            "to_knowledge_id": latest["knowledge_id"],
                            "relation": "explicitly_claims_to_supersede",
                            "parameter": name,
                            "applied": False,
                            "review_required": True,
                        }
                    )
            if len(conflicts) >= self.max_conflicts:
                break
        return conflicts, supersession_links
