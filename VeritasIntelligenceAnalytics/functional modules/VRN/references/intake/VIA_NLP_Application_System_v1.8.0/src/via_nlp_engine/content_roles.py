"""Conservative body/non-body classification and complete-input summarization."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from typing import Any


CONTENT_ROLE_SCHEMA = "VIA_CONTENT_ROLE_ANALYSIS/1.0"
HIGH_CONFIDENCE_EXCLUSION = 0.90
MAX_REVIEW_ITEMS = 1000

ROLE_LABELS = {
    "primary_body": {"zh": "本文", "en": "Primary Body"},
    "supporting_evidence": {"zh": "支援證據", "en": "Supporting Evidence"},
    "code_evidence": {"zh": "程式證據", "en": "Code Evidence"},
    "metadata": {"zh": "中繼資料", "en": "Metadata"},
    "navigation": {"zh": "導覽", "en": "Navigation"},
    "advertisement": {"zh": "廣告／推廣", "en": "Advertisement / Promotion"},
    "header_footer": {"zh": "頁首／頁尾", "en": "Header / Footer"},
    "source_wrapper": {"zh": "來源封裝標記", "en": "Source Wrapper"},
    "blank": {"zh": "空白", "en": "Blank"},
    "uncertain": {"zh": "待判讀內容", "en": "Uncertain Content"},
}

SOURCE_METADATA_RE = re.compile(
    r"(?mi)^\s*(?:SourceName|SourceExtension|ExtractedTextSHA256)\s*:"
)
NAVIGATION_RE = re.compile(
    r"(?ix)(?:"
    r"^\s*(?:home|menu|back\s+to\s+top|previous|next|sign\s*in|log\s*in|register)\s*$|"
    r"^\s*(?:首頁|主選單|返回頂端|上一頁|下一頁|登入|註冊|麵包屑|目錄)\s*$|"
    r"(?:相關新聞|延伸閱讀|熱門新聞|推薦閱讀|related\s+(?:news|articles)|read\s+more)\s*[:：]?\s*$"
    r")"
)
ADVERTISEMENT_RE = re.compile(
    r"(?ix)(?:"
    r"^\s*(?:advertisement|sponsored\s+content|廣告|贊助內容|合作推廣)\s*(?::|：|$)|"
    r"(?:download\s+our\s+app|下載\s*APP|立即訂閱|立即購買|開戶優惠)|"
    r"(?:research\s+survey.{0,80}ballot)"
    r")"
)
HEADER_FOOTER_RE = re.compile(
    r"(?ix)(?:"
    r"(?:copyright|all\s+rights\s+reserved|privacy\s+policy|terms\s+of\s+use)|"
    r"(?:版權所有|隱私權政策|使用條款|服務條款)|©\s*\d{4}"
    r")"
)
CONTENT_SIGNAL_RE = re.compile(
    r"(?ix)(?:"
    r"\d+(?:\.\d+)?\s*(?:%|億|萬|元|美元|bps)|"
    r"(?:結果|結論|方法|需求|決定|風險|營收|獲利|利率|匯率|函式|類別|參數|資料)|"
    r"\b(?:result|conclusion|method|requirement|decision|risk|revenue|function|class|parameter|data)\b"
    r")"
)
LAYOUT_ARTIFACT_RE = re.compile(
    r"(?ix)^\s*(?:"
    r"HTML(?:\s*[+＋-]\s*\d+)?|MD(?:\s*[+＋-]\s*\d+)?|"
    r"本文區(?:\s*\([^)]*\))?|右資訊區|左資訊區|"
    r"main\s+content|right\s+(?:rail|sidebar)|left\s+(?:rail|sidebar)"
    r")\s*$"
)
PAGE_NUMBER_RE = re.compile(
    r"(?ix)^\s*(?:"
    r"page\s*\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?|"
    r"第?\s*\d{1,4}\s*頁(?:\s*/\s*\d{1,4}\s*頁)?|"
    r"[-–—]\s*\d{1,4}\s*[-–—]"
    r")\s*$"
)
DOCUMENT_BOUNDARY_RE = re.compile(
    r"(?ix)\.(?:pdf|docx|txt|md|html?)"
    r"(?:\s*)?(?:DUAL_ZONES|DOCX_HEAD|TEXT_HEAD|MARKDOWN_HEAD)\b"
)
CONTACT_METADATA_RE = re.compile(
    r"(?ix)(?:"
    r"^[^\s@]+@[^\s@]+\.[^\s@]+\s*$|"
    r"^\s*(?:tel|telephone|電話|手機|fax|傳真)\s*[:：]?\s*[+()\d\s.-]{7,}\s*$|"
    r"^\s*(?:\+?886|\(886\))\s*[()\d\s.-]{7,}\s*$|"
    r"^\s*(?:equity\s+analyst|research\s+associate|研究員|分析師)\s*[:：]?\s*[^\n]{0,100}$"
    r")"
)
FACT_TOKEN_RE = re.compile(
    r"(?ix)(?:"
    r"(?:NT\$|US\$|HK\$|CNY|USD|EUR|JPY|GBP|TWD)?\s*[-+]?"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
    r"\s*(?:%|％|bps?|億|萬|千|百萬|元|美元|日圓|歐元|倍|股|張|年|月|日)?"
    r")"
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalized_fingerprint(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip().casefold()
    return _sha256(normalized) if normalized else ""


class ContentRoleAnalyzer:
    """Classify every layout block while failing closed against content loss."""

    def __init__(self, processor: Any) -> None:
        self.processor = processor

    def build(self, text: str, layout_analysis: dict[str, Any]) -> dict[str, Any]:
        blocks = [
            part
            for block in layout_analysis.get("blocks", [])
            for part in self._atomic_items(block)
        ]
        fingerprints = Counter(
            _normalized_fingerprint(str(item.get("source_text", "")))
            for item in blocks
            if str(item.get("source_text", "")).strip()
        )
        layout_dump_mode = sum(
            1
            for item in blocks
            if LAYOUT_ARTIFACT_RE.match(str(item.get("source_text", "")).strip())
        ) >= 3
        records: list[dict[str, Any]] = []
        section_transitions: list[dict[str, Any]] = []
        content_region = "unscoped"
        for item in blocks:
            stripped = str(item.get("source_text", "")).strip()
            previous_region = content_region
            transition_reason: str | None = None
            if (
                str(item.get("block_type")) == "source_record_marker"
                or DOCUMENT_BOUNDARY_RE.search(stripped)
            ):
                content_region = "unscoped"
                transition_reason = "document_boundary"
            if re.match(r"(?i)^\s*(?:本文區|main\s+content)(?:\s*\([^)]*\))?\s*$", stripped):
                content_region = "main"
                transition_reason = "explicit_main_region"
            elif re.match(r"(?i)^\s*(?:右資訊區|左資訊區|(?:right|left)\s+(?:rail|sidebar))\s*$", stripped):
                content_region = "sidebar"
                transition_reason = "explicit_sidebar_region"
            if transition_reason is not None:
                section_transitions.append(
                    {
                        "transition_id": f"REGION-{len(section_transitions) + 1:05d}",
                        "from": previous_region,
                        "to": content_region,
                        "reason": transition_reason,
                        "layout_id": item.get("layout_id"),
                        "layout_part_id": item.get("layout_part_id", item.get("layout_id")),
                        "source_span": item.get("source_span"),
                    }
                )
            role = self._classify(item, fingerprints, layout_dump_mode, content_region)
            records.append(
                {
                    "content_role_id": f"CONTENT-{len(records) + 1:06d}",
                    "layout_id": item.get("layout_id"),
                    "layout_part_id": item.get("layout_part_id", item.get("layout_id")),
                    "role": role["role"],
                    "role_label": ROLE_LABELS[role["role"]],
                    "summary_relevance": role["summary_relevance"],
                    "include_in_body_summary": role["include_in_body_summary"],
                    "confidence": role["confidence"],
                    "reason_codes": role["reason_codes"],
                    "review_required": role["review_required"],
                    "content_region": content_region,
                    "source_span": item.get("source_span"),
                    "source_sha256": item.get("source_sha256"),
                    "source_segments": item.get("source_segments", []),
                    "source_text": item.get("source_text", ""),
                    "source_preserved": True,
                }
            )
        body_records = [item for item in records if item["include_in_body_summary"]]
        fallback_applied = False
        if text.strip() and not any(str(item["source_text"]).strip() for item in body_records):
            body_records = [
                item
                for item in records
                if item["role"] not in {"blank", "source_wrapper"}
            ]
            fallback_applied = True
        body_projection = "".join(str(item["source_text"]) for item in body_records)
        full_summary = self.processor.summarize_complete(text, max_points=12)
        repair_result = self.processor.repair(body_projection)
        repaired_body = str(repair_result.get("repaired_text", body_projection))
        source_fact_tokens = self._fact_tokens(body_projection)
        candidate_fact_tokens = self._fact_tokens(repaired_body)
        fact_tokens_preserved = Counter(source_fact_tokens) == Counter(candidate_fact_tokens)
        repair_selected = bool(fact_tokens_preserved)
        summary_input = repaired_body if repair_selected else body_projection
        body_summary = self.processor.summarize_complete(summary_input, max_points=12)
        excluded = [item for item in records if not item["include_in_body_summary"]]
        review = [item for item in records if item["review_required"]]
        high_confidence_excluded = [
            item for item in excluded
            if float(item["confidence"]) >= HIGH_CONFIDENCE_EXCLUSION
        ]
        role_counts = Counter(str(item["role"]) for item in records)
        full_reconstruction = "".join(str(item["source_text"]) for item in records)
        source_characters = len(text)
        body_characters = len(body_projection)
        non_body_characters = sum(len(str(item["source_text"])) for item in excluded)
        summary_evidence_valid = all(
            bool(summary["quality"][gate])
            for summary in (body_summary, full_summary)
            for gate in ("key_points_bounded", "evidence_spans_valid", "evidence_hashes_valid")
        )
        return {
            "schema": CONTENT_ROLE_SCHEMA,
            "languages": ["zh", "en"],
            "classification_policy": {
                "name": "conservative_fail_closed_non_body_filter",
                "high_confidence_exclusion_threshold": HIGH_CONFIDENCE_EXCLUSION,
                "uncertain_content_default": "include_and_review",
                "code_default": "preserve_in_specialized_pipeline_exclude_from_prose_summary",
                "source_deletion_allowed": False,
            },
            "section_transitions": section_transitions,
            "records": records,
            "body_projection": {
                "text": body_projection,
                "sha256": _sha256(body_projection),
                "source_layout_ids": [item["layout_id"] for item in body_records],
                "is_derivative": True,
                "fallback_included_uncertain_content": fallback_applied,
            },
            "repair_projection": {
                "source_sha256": _sha256(body_projection),
                "candidate_sha256": _sha256(repaired_body),
                "candidate_text": repaired_body,
                "selected_for_body_summary": repair_selected,
                "fact_tokens_preserved": fact_tokens_preserved,
                "semantic_rewrite_applied": False,
                "source_writeback_applied": False,
                "changes": list(repair_result.get("changes", []))[:1000],
                "suggestions": list(repair_result.get("review_suggestions", []))[:1000],
            },
            "non_body_register": [
                {
                    key: item[key]
                    for key in (
                        "content_role_id", "layout_id", "role", "role_label", "summary_relevance",
                        "confidence", "reason_codes", "review_required", "source_span",
                        "source_sha256", "source_segments", "source_text",
                    )
                }
                for item in excluded
            ],
            "summarizer": {
                "body_summary": body_summary,
                "full_input_summary": full_summary,
                "default_projection": "body_summary",
                "full_input_was_also_processed": True,
                "high_confidence_non_body_excluded_from_default": True,
                "uncertain_content_included_by_default": True,
            },
            "review_queue": {
                "items": [
                    {
                        "content_role_id": item["content_role_id"],
                        "role": item["role"],
                        "confidence": item["confidence"],
                        "reason_codes": item["reason_codes"],
                        "source_span": item["source_span"],
                    }
                    for item in review[:MAX_REVIEW_ITEMS]
                ],
                "truncated": len(review) > MAX_REVIEW_ITEMS,
            },
            "statistics": {
                "source_characters": source_characters,
                "body_projection_characters": body_characters,
                "non_body_characters": non_body_characters,
                "body_retention_ratio": round(body_characters / max(1, source_characters), 6),
                "non_body_ratio": round(non_body_characters / max(1, source_characters), 6),
                "blocks": len(records),
                "included_blocks": len(body_records),
                "excluded_blocks": len(excluded),
                "high_confidence_excluded_blocks": len(high_confidence_excluded),
                "review_blocks": len(review),
                "section_transitions": len(section_transitions),
                "role_counts": dict(sorted(role_counts.items())),
            },
            "quality_gates": {
                "all_source_characters_classified": full_reconstruction == text,
                "source_reconstruction_sha256_match": _sha256(full_reconstruction) == _sha256(text),
                "complete_input_processed_by_summarizer": full_summary["coverage"]["all_input_consumed"],
                "body_projection_processed_by_summarizer": body_summary["coverage"]["all_input_consumed"],
                "summary_evidence_integrity": summary_evidence_valid,
                "summary_points_bounded": all(
                    summary["quality"]["key_points_bounded"]
                    for summary in (body_summary, full_summary)
                ),
                "summary_chunk_representation_policy_passed": all(
                    summary["quality"]["all_eligible_chunks_represented_when_budget_allows"]
                    for summary in (body_summary, full_summary)
                ),
                "repair_projection_fact_tokens_preserved": fact_tokens_preserved,
                "repair_projection_fact_integrity": "pass" if fact_tokens_preserved else "pass_with_source_fallback",
                "repair_projection_selected": repair_selected,
                "repair_projection_source_writeback": False,
                "low_confidence_content_silently_excluded": False,
                "source_text_mutated": False,
                "automatic_source_deletion": False,
            },
        }

    @staticmethod
    def _atomic_items(item: dict[str, Any]) -> list[dict[str, Any]]:
        """Split mixed prose blocks by source line without changing any character."""
        block_type = str(item.get("block_type", "paragraph"))
        source_text = str(item.get("source_text", ""))
        if block_type not in {"paragraph", "unordered_list", "ordered_list", "task_list", "blockquote"}:
            return [dict(item)]
        lines = source_text.splitlines(keepends=True)
        if len(lines) <= 1:
            return [dict(item)]
        base_start = int(item.get("source_span", {}).get("start", 0))
        parts: list[dict[str, Any]] = []
        position = base_start
        for index, line in enumerate(lines, start=1):
            part = dict(item)
            part["layout_part_id"] = f"{item.get('layout_id')}-P{index:04d}"
            part["source_text"] = line
            part["source_span"] = {"start": position, "end": position + len(line)}
            part["source_sha256"] = _sha256(line)
            parts.append(part)
            position += len(line)
        if position < int(item.get("source_span", {}).get("end", position)):
            remainder = source_text[position - base_start:]
            part = dict(item)
            part["layout_part_id"] = f"{item.get('layout_id')}-P{len(parts) + 1:04d}"
            part["source_text"] = remainder
            part["source_span"] = {"start": position, "end": position + len(remainder)}
            part["source_sha256"] = _sha256(remainder)
            parts.append(part)
        return parts

    @staticmethod
    def _classify(
        item: dict[str, Any],
        fingerprints: Counter[str],
        layout_dump_mode: bool,
        content_region: str,
    ) -> dict[str, Any]:
        block_type = str(item.get("block_type", "paragraph"))
        source_text = str(item.get("source_text", ""))
        stripped = source_text.strip()
        fingerprint = _normalized_fingerprint(source_text)
        repeated_short = bool(
            stripped
            and len(stripped) <= 180
            and fingerprint
            and fingerprints[fingerprint] >= 3
        )
        if block_type == "source_record_marker" or SOURCE_METADATA_RE.match(stripped):
            return ContentRoleAnalyzer._role("source_wrapper", False, 1.0, ["explicit_source_wrapper"])
        if block_type == "blank":
            return ContentRoleAnalyzer._role("blank", False, 1.0, ["blank_layout_block"])
        if block_type == "front_matter":
            return ContentRoleAnalyzer._role("metadata", False, 0.98, ["front_matter"])
        if layout_dump_mode and LAYOUT_ARTIFACT_RE.match(stripped):
            return ContentRoleAnalyzer._role("metadata", False, 0.99, ["layout_dump_artifact"])
        if PAGE_NUMBER_RE.match(stripped):
            return ContentRoleAnalyzer._role("header_footer", False, 0.98, ["page_number_marker"])
        if CONTACT_METADATA_RE.search(stripped):
            return ContentRoleAnalyzer._role("metadata", False, 0.97, ["contact_or_author_metadata"])
        if block_type in {"fenced_code", "indented_code"}:
            return ContentRoleAnalyzer._role(
                "code_evidence", False, 0.99, ["specialized_code_pipeline"], relevance="excluded_specialized"
            )
        if NAVIGATION_RE.search(stripped):
            return ContentRoleAnalyzer._role("navigation", False, 0.96, ["navigation_marker"])
        if ADVERTISEMENT_RE.search(stripped) and not CONTENT_SIGNAL_RE.search(stripped):
            return ContentRoleAnalyzer._role("advertisement", False, 0.97, ["advertisement_marker"])
        if HEADER_FOOTER_RE.search(stripped):
            return ContentRoleAnalyzer._role("header_footer", False, 0.98, ["copyright_or_policy_marker"])
        if content_region == "sidebar" and stripped:
            return ContentRoleAnalyzer._role(
                "supporting_evidence",
                False,
                0.94,
                ["explicit_sidebar_region"],
                relevance="excluded_secondary_from_default",
            )
        if block_type == "table":
            return ContentRoleAnalyzer._role("supporting_evidence", True, 0.98, ["structured_table"])
        if repeated_short and not CONTENT_SIGNAL_RE.search(stripped):
            return ContentRoleAnalyzer._role(
                "primary_body",
                True,
                0.70,
                ["repeated_short_content_retained"],
                review=False,
                relevance="include_conservative",
            )
        if block_type in {"heading", "paragraph", "unordered_list", "ordered_list", "task_list", "blockquote", "math_block"}:
            return ContentRoleAnalyzer._role("primary_body", True, 0.92, [f"content_layout:{block_type}"])
        if block_type == "thematic_break":
            return ContentRoleAnalyzer._role("metadata", False, 0.93, ["thematic_separator"])
        if block_type == "html_block":
            confidence = 0.65 if stripped else 0.95
            return ContentRoleAnalyzer._role(
                "uncertain",
                True,
                confidence,
                ["html_requires_render_or_parser"],
                review=True,
                relevance="include_until_review",
            )
        return ContentRoleAnalyzer._role(
            "uncertain", True, 0.50, ["unknown_layout_role"], review=True, relevance="include_until_review"
        )

    @staticmethod
    def _fact_tokens(value: str) -> list[str]:
        """Return numeric and unit-bearing tokens for a conservative repair gate."""
        normalized_value = unicodedata.normalize("NFKC", value)
        return [
            re.sub(r"\s+", "", match.group(0)).casefold()
            for match in FACT_TOKEN_RE.finditer(normalized_value)
        ]

    @staticmethod
    def _role(
        role: str,
        include: bool,
        confidence: float,
        reasons: list[str],
        review: bool = False,
        relevance: str | None = None,
    ) -> dict[str, Any]:
        if relevance is None:
            relevance = "include_primary" if include else "excluded_non_body"
        if not include and confidence < HIGH_CONFIDENCE_EXCLUSION:
            include = True
            review = True
            relevance = "include_until_review"
        return {
            "role": role,
            "include_in_body_summary": include,
            "summary_relevance": relevance,
            "confidence": round(float(confidence), 4),
            "reason_codes": reasons,
            "review_required": review,
        }
