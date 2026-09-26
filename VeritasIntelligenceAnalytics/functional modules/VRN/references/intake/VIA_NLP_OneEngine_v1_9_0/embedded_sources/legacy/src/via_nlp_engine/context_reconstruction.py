"""Source-grounded reconstruction for disordered articles and conversations."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any


CONTEXT_SCHEMA = "VIA_CONTEXT_RECONSTRUCTION/1.0"
MAX_UNIT_LABELS = 6
MAX_REPLY_GAP = 3

FUNCTION_LABELS = {
    "heading": {"zh": "標題", "en": "Heading"},
    "context": {"zh": "背景", "en": "Context"},
    "requirement": {"zh": "需求", "en": "Requirement"},
    "decision": {"zh": "決策", "en": "Decision"},
    "instruction": {"zh": "指令", "en": "Instruction"},
    "question": {"zh": "問題", "en": "Question"},
    "answer": {"zh": "回答", "en": "Answer"},
    "constraint": {"zh": "限制", "en": "Constraint"},
    "parameter": {"zh": "參數", "en": "Parameter"},
    "verification": {"zh": "驗證", "en": "Verification"},
    "result": {"zh": "結果", "en": "Result"},
    "warning": {"zh": "警告／風險", "en": "Warning / Risk"},
    "example": {"zh": "範例", "en": "Example"},
    "code": {"zh": "程式", "en": "Code"},
    "template": {"zh": "模板", "en": "Template"},
    "data": {"zh": "資料", "en": "Data"},
    "citation": {"zh": "引用／來源", "en": "Citation / Source"},
}

FUNCTION_PATTERNS = {
    "requirement": r"(?:必須|需要|應該|請|must|shall|should|need to|require)",
    "decision": r"(?:決定|採用|確定|結論|批准|decid|adopt|approved?)",
    "instruction": r"(?:執行|建立|新增|修改|安裝|啟動|步驟|run|create|add|update|install|step)",
    "question": r"(?:[?？]|如何|為何|是否|什麼|how|why|whether|what|which)",
    "constraint": r"(?:不得|禁止|不可|限制|避免|must not|do not|never|limit)",
    "parameter": r"(?:參數|門檻|設定|config|parameter|threshold|[A-Z][A-Z0-9_]{2,}\s*=)",
    "verification": r"(?:驗證|確認|檢查|測試|預期|verify|validate|check|test|expect)",
    "result": r"(?:完成|成功|結果|通過|輸出|completed|success|result|passed|output)",
    "warning": r"(?:警告|風險|錯誤|失敗|衝突|warning|risk|error|failed?|conflict)",
    "example": r"(?:例如|範例|示例|e\.g\.|for example|example)",
    "template": r"(?:模板|範本|schema|template|blueprint)",
    "data": r"(?:資料|數據|欄位|表格|JSON|CSV|database|data|field|table)",
    "citation": r"(?:https?://|來源|參考|source|reference|citation)",
}


def _stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()[:16].upper()
    return f"{prefix}-{digest}"


class ContextReconstructor:
    """Build chronological and topical views while preserving immutable source."""

    def build(
        self,
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
        topics: list[dict[str, Any]],
        dialogue_flow: dict[str, Any],
        code_blocks: list[dict[str, Any]],
        instruction_registry: dict[str, Any],
        conflict_register: list[dict[str, Any]],
    ) -> dict[str, Any]:
        refined = {item["segment_id"]: item for item in refinement_ledger}
        topic_for_segment = {
            segment_id: topic["topic_id"]
            for topic in topics
            for segment_id in topic.get("segment_ids", [])
        }
        code_segments = {
            segment_id
            for block in code_blocks
            for segment_id in block.get("source_segments", [])
        }
        classified: list[dict[str, Any]] = []
        for source_order, segment in enumerate(segments, start=1):
            item = refined.get(segment["segment_id"], {})
            labels = self._labels(segment, item, segment["segment_id"] in code_segments)
            classified.append(
                {
                    "context_unit_id": _stable_id("CTXU", segment["segment_id"], segment["sha256"]),
                    "source_order": source_order,
                    "source_segment": segment["segment_id"],
                    "source_sha256": segment["sha256"],
                    "topic_id": topic_for_segment.get(segment["segment_id"]),
                    "speaker": segment.get("speaker"),
                    "timestamp": segment.get("timestamp"),
                    "kind": segment.get("kind"),
                    "functional_labels": [
                        {"label": label, "bilingual": FUNCTION_LABELS[label]}
                        for label in labels
                    ],
                    "source_text": segment["text"],
                    "derivative_text": item.get("optimized_text", segment["text"]),
                    "derivative_only": True,
                }
            )
        document_mode = self._document_mode(segments, code_segments)
        reply_links, unanswered = self._reply_links(classified)
        threads = self._threads(topics, classified, dialogue_flow)
        issues = self._issues(classified, threads, unanswered, code_blocks, instruction_registry, conflict_register)
        counts = Counter(
            label["label"]
            for item in classified
            for label in item["functional_labels"]
        )
        return {
            "schema": CONTEXT_SCHEMA,
            "languages": ["zh", "en"],
            "document_mode": document_mode,
            "functional_labels": FUNCTION_LABELS,
            "chronological_view": classified,
            "topic_threads": threads,
            "reply_links": reply_links,
            "review_queue": {
                "unanswered_question_units": unanswered,
                "context_issues": issues,
                "topic_return_links": dialogue_flow.get("return_links", []),
            },
            "statistics": {
                "context_units": len(classified),
                "topic_threads": len(threads),
                "reply_links": len(reply_links),
                "unanswered_questions": len(unanswered),
                "functional_label_counts": dict(sorted(counts.items())),
                "jumpiness_ratio": dialogue_flow.get("metrics", {}).get("jumpiness_ratio", 0.0),
            },
            "quality_gates": {
                "source_traceability": "pass" if all(item["source_segment"] and item["source_sha256"] for item in classified) else "fail",
                "automatic_source_reorder": False,
                "invented_bridge_text": False,
                "silent_topic_merge": False,
                "reply_inference_is_candidate": True,
                "derivative_mutates_source": False,
            },
        }

    @staticmethod
    def _document_mode(segments: list[dict[str, Any]], code_segments: set[str]) -> dict[str, Any]:
        messages = sum(bool(item.get("kind") == "message" or item.get("speaker")) for item in segments)
        articles = sum(item.get("kind") in {"article", "heading_section"} for item in segments)
        code_ratio = len(code_segments) / max(1, len(segments))
        if code_ratio >= 0.5:
            selected = "code_heavy"
        elif messages and articles:
            selected = "mixed"
        elif messages:
            selected = "dialogue"
        else:
            selected = "article"
        return {
            "value": selected,
            "bilingual": {
                "zh": {"article": "文章", "dialogue": "對話", "mixed": "混合內容", "code_heavy": "程式為主"}[selected],
                "en": {"article": "Article", "dialogue": "Dialogue", "mixed": "Mixed", "code_heavy": "Code-heavy"}[selected],
            },
            "evidence": {"message_segments": messages, "article_segments": articles, "code_segment_ratio": round(code_ratio, 6)},
        }

    @staticmethod
    def _labels(segment: dict[str, Any], refinement: dict[str, Any], contains_code: bool) -> list[str]:
        text = str(refinement.get("optimized_text", segment.get("text", "")))
        labels: list[str] = []
        if segment.get("kind") == "heading_section":
            labels.append("heading")
        if contains_code or "code" in str(segment.get("kind", "")):
            labels.append("code")
        for label, pattern in FUNCTION_PATTERNS.items():
            if re.search(pattern, text, flags=re.I):
                labels.append(label)
        existing_roles = [str(item) for item in refinement.get("roles", [])]
        for role in existing_roles:
            if role in FUNCTION_LABELS and role not in labels:
                labels.append(role)
        if not labels:
            labels = ["context"]
        return list(dict.fromkeys(labels))[:MAX_UNIT_LABELS]

    @staticmethod
    def _threads(
        topics: list[dict[str, Any]],
        classified: list[dict[str, Any]],
        dialogue_flow: dict[str, Any],
    ) -> list[dict[str, Any]]:
        by_segment = {item["source_segment"]: item for item in classified}
        returns = Counter(item["topic_id"] for item in dialogue_flow.get("return_links", []))
        threads: list[dict[str, Any]] = []
        for topic in topics:
            members = [by_segment[item] for item in topic.get("segment_ids", []) if item in by_segment]
            threads.append(
                {
                    "thread_id": _stable_id("THREAD", topic["topic_id"], *(item["source_sha256"] for item in members)),
                    "topic_id": topic["topic_id"],
                    "title": topic.get("title"),
                    "keywords": topic.get("keywords", []),
                    "anchors": topic.get("anchors", []),
                    "source_segments": [item["source_segment"] for item in members],
                    "source_orders": [item["source_order"] for item in members],
                    "episodes": topic.get("episodes", []),
                    "return_count": returns[topic["topic_id"]],
                    "functional_labels": sorted({label["label"] for item in members for label in item["functional_labels"]}),
                    "status": topic.get("semantic_status", "unknown"),
                }
            )
        return threads

    @staticmethod
    def _reply_links(classified: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
        links: list[dict[str, Any]] = []
        answered: set[str] = set()
        for index, item in enumerate(classified):
            labels = {entry["label"] for entry in item["functional_labels"]}
            if "question" not in labels:
                continue
            for candidate in classified[index + 1 : index + 1 + MAX_REPLY_GAP]:
                candidate_labels = {entry["label"] for entry in candidate["functional_labels"]}
                speaker_changed = bool(item.get("speaker") and candidate.get("speaker") and item["speaker"] != candidate["speaker"])
                same_topic = bool(item.get("topic_id") and item.get("topic_id") == candidate.get("topic_id"))
                if "question" in candidate_labels and not speaker_changed:
                    break
                if speaker_changed or same_topic:
                    confidence = 0.58 + (0.20 if speaker_changed else 0.0) + (0.14 if same_topic else 0.0)
                    links.append(
                        {
                            "reply_link_id": _stable_id("REPLY", item["context_unit_id"], candidate["context_unit_id"]),
                            "question_unit": item["context_unit_id"],
                            "answer_unit": candidate["context_unit_id"],
                            "confidence": round(min(confidence, 0.92), 4),
                            "review_required": confidence < 0.85,
                            "evidence": {"speaker_changed": speaker_changed, "same_topic": same_topic},
                        }
                    )
                    answered.add(item["context_unit_id"])
                    break
        questions = [
            item["context_unit_id"]
            for item in classified
            if any(label["label"] == "question" for label in item["functional_labels"])
        ]
        return links, [item for item in questions if item not in answered]

    @staticmethod
    def _issues(
        classified: list[dict[str, Any]],
        threads: list[dict[str, Any]],
        unanswered: list[str],
        code_blocks: list[dict[str, Any]],
        instruction_registry: dict[str, Any],
        conflict_register: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for unit_id in unanswered:
            issues.append({"type": "unanswered_question", "target_id": unit_id, "resolution": "human_or_later_source_required"})
        for block in code_blocks:
            if not block.get("source_segments"):
                issues.append({"type": "orphan_code", "target_id": block["code_id"], "resolution": "source_link_required"})
        for thread in threads:
            if thread["status"] != "resolved":
                issues.append({"type": "unresolved_topic", "target_id": thread["thread_id"], "resolution": "manual_topic_review"})
        for conflict in conflict_register:
            issues.append({"type": "knowledge_conflict", "target_id": conflict.get("conflict_id"), "resolution": "human_required"})
        review = instruction_registry.get("review_queue", {})
        for command_id in review.get("incomplete_command_ids", []):
            issues.append({"type": "incomplete_command", "target_id": command_id, "resolution": "complete_from_source_or_reject"})
        return issues
