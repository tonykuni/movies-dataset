"""Bounded, evidence-linked and complete-input extractive summarization."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any


SUMMARY_SCHEMA = "VIA_EVIDENCE_SUMMARIZER/1.0"
DEFAULT_MAX_UNIT_CHARS = 900
MIN_UNIT_CHARS = 8
MAX_CANDIDATES_PER_CHUNK = 4
UNIT_BOUNDARY_RE = re.compile(
    r"(?:\n+|(?<=[。！？!?；;])\s*|(?<=\.)\s+(?=[A-Z0-9\u3400-\u9fff]))"
)
NOISE_ONLY_RE = re.compile(
    r"(?ix)^\s*(?:"
    r"=====\s*(?:BEGIN|END)\s+VIA\s+SOURCE|"
    r"(?:SourceName|SourceExtension|ExtractedTextSHA256)\s*:|"
    r"HTML(?:\s*[+＋-]\s*\d+)?|MD(?:\s*[+＋-]\s*\d+)?|"
    r"本文區(?:\s*\([^)]*\))?|右資訊區|左資訊區|"
    r"(?:page\s*)?\d{1,4}\s*/\s*\d{1,4}"
    r")\s*$"
)
FACT_SIGNAL_RE = re.compile(
    r"(?ix)(?:"
    r"[-+]?\d[\d,]*(?:\.\d+)?\s*(?:%|％|bps?|億|萬|元|美元|倍)|"
    r"(?:結論|重點|結果|原因|風險|展望|建議|營收|獲利|需求|決策)|"
    r"\b(?:conclusion|result|reason|risk|outlook|recommendation|revenue|profit|decision)\b"
    r")"
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fingerprint(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


class CompleteEvidenceSummarizer:
    """Summarize all chunks while bounding points and retaining source proof."""

    def __init__(self, processor: Any) -> None:
        self.processor = processor

    def summarize(
        self,
        text: str,
        max_points: int = 10,
        max_chunk_chars: int = 20_000,
        max_unit_chars: int = DEFAULT_MAX_UNIT_CHARS,
    ) -> dict[str, Any]:
        if max_chunk_chars < 1000:
            raise ValueError("max_chunk_chars must be at least 1000")
        if max_unit_chars < 120:
            raise ValueError("max_unit_chars must be at least 120")
        point_limit = max(1, min(int(max_points), 100))
        chunks = self._build_chunks(text, max_chunk_chars, max_unit_chars)
        candidates = [candidate for chunk in chunks for candidate in chunk.pop("_candidates")]
        selected = self._select(candidates, chunks, point_limit)
        evidence_points = [
            {
                "summary_point_id": f"SUMMARY-POINT-{index:04d}",
                "text": item["text"],
                "source_text": item["source_text"],
                "source_span": item["source_span"],
                "source_sha256": item["source_sha256"],
                "chunk_id": item["chunk_id"],
                "language": item["language"],
                "score": item["score"],
                "selection_reasons": item["selection_reasons"],
            }
            for index, item in enumerate(selected, start=1)
        ]
        key_points = [item["text"] for item in evidence_points]
        reconstructed = "".join(
            text[item["source_span"]["start"]:item["source_span"]["end"]]
            for item in chunks
        )
        eligible_chunk_ids = {
            item["chunk_id"]
            for item in candidates
        }
        represented_chunk_ids = {
            item["chunk_id"]
            for item in evidence_points
        }
        evidence_spans_valid = all(
            text[item["source_span"]["start"]:item["source_span"]["end"]] == item["source_text"]
            for item in evidence_points
        )
        evidence_hashes_valid = all(
            _sha256(item["source_text"]) == item["source_sha256"]
            for item in evidence_points
        )
        normalized_points = [_fingerprint(item) for item in key_points]
        duplicate_points = len(normalized_points) - len(set(normalized_points))
        maximum_observed = max((len(item) for item in key_points), default=0)
        language_counts = Counter(str(item["language"]) for item in evidence_points)
        return {
            "schema": SUMMARY_SCHEMA,
            "summary": "\n".join(key_points),
            "key_points": key_points,
            "evidence_points": evidence_points,
            "backend": "hierarchical_evidence_extractive_complete_input",
            "languages": {
                "labels": {"zh": "摘要證據", "en": "Summary Evidence"},
                "point_language_counts": dict(sorted(language_counts.items())),
                "translation_applied": False,
            },
            "chunks": chunks,
            "coverage": {
                "source_characters": len(text),
                "consumed_characters": sum(item["source_characters"] for item in chunks),
                "chunk_count": len(chunks),
                "all_input_consumed": reconstructed == text,
                "source_sha256": _sha256(text),
                "reconstructed_sha256": _sha256(reconstructed),
                "silent_truncation": False,
            },
            "quality": {
                "selection_strategy": "chunk_representative_then_global_score_source_order",
                "max_point_characters": max_unit_chars,
                "max_observed_point_characters": maximum_observed,
                "key_points_bounded": maximum_observed <= max_unit_chars,
                "evidence_spans_valid": evidence_spans_valid,
                "evidence_hashes_valid": evidence_hashes_valid,
                "duplicate_points": duplicate_points,
                "eligible_chunks": len(eligible_chunk_ids),
                "represented_chunks": len(represented_chunk_ids),
                "chunk_representation_rate": round(
                    len(represented_chunk_ids) / max(1, len(eligible_chunk_ids)),
                    6,
                ),
                "all_eligible_chunks_represented_when_budget_allows": (
                    len(eligible_chunk_ids) > point_limit
                    or represented_chunk_ids == eligible_chunk_ids
                ),
                "source_text_mutated": False,
                "generative_facts_added": False,
            },
        }

    def _build_chunks(
        self,
        text: str,
        max_chunk_chars: int,
        max_unit_chars: int,
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        position = 0
        while position < len(text):
            end = min(len(text), position + max_chunk_chars)
            if end < len(text):
                boundary = max(
                    text.rfind("\n\n", position, end),
                    text.rfind("\n", position, end),
                    text.rfind("。", position, end),
                    text.rfind(". ", position, end),
                )
                if boundary > position + max_chunk_chars // 2:
                    end = boundary + (2 if text[boundary:boundary + 2] == "\n\n" else 1)
            source_text = text[position:end]
            chunk_id = f"SUMMARY-CHUNK-{len(chunks) + 1:05d}"
            candidates = self._score_units(
                source_text,
                source_start=position,
                chunk_id=chunk_id,
                max_unit_chars=max_unit_chars,
            )
            previews = candidates[:MAX_CANDIDATES_PER_CHUNK]
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source_span": {"start": position, "end": end},
                    "source_characters": len(source_text),
                    "source_sha256": _sha256(source_text),
                    "summary": "\n".join(item["text"] for item in previews),
                    "key_points": [item["text"] for item in previews],
                    "candidate_count": len(candidates),
                    "_candidates": candidates,
                }
            )
            position = end
        return chunks

    def _score_units(
        self,
        chunk_text: str,
        source_start: int,
        chunk_id: str,
        max_unit_chars: int,
    ) -> list[dict[str, Any]]:
        units = self._bounded_units(chunk_text, source_start, max_unit_chars)
        frequencies = Counter(self.processor.tokenize(chunk_text))
        candidates: list[dict[str, Any]] = []
        for index, unit in enumerate(units):
            display_text = unit["source_text"].strip()
            if len(display_text) < MIN_UNIT_CHARS or NOISE_ONLY_RE.match(display_text):
                continue
            tokens = self.processor.tokenize(display_text)
            if not tokens:
                continue
            score = sum(math.log1p(frequencies[token]) for token in tokens) / max(1.0, math.sqrt(len(tokens)))
            reasons = ["lexical_salience"]
            if index < max(1, len(units) // 8):
                score *= 1.08
                reasons.append("early_chunk_context")
            if FACT_SIGNAL_RE.search(display_text):
                score *= 1.12
                reasons.append("fact_or_decision_signal")
            if len(display_text) < 24:
                score *= 0.55
                reasons.append("short_unit_penalty")
            candidates.append(
                {
                    "text": display_text,
                    "source_text": unit["source_text"],
                    "source_span": unit["source_span"],
                    "source_sha256": _sha256(unit["source_text"]),
                    "chunk_id": chunk_id,
                    "language": self.processor.detect_language(display_text),
                    "score": round(float(score), 8),
                    "selection_reasons": reasons,
                }
            )
        return sorted(candidates, key=lambda item: (-item["score"], item["source_span"]["start"]))

    @staticmethod
    def _bounded_units(text: str, source_start: int, max_unit_chars: int) -> list[dict[str, Any]]:
        rough_spans: list[tuple[int, int]] = []
        cursor = 0
        for match in UNIT_BOUNDARY_RE.finditer(text):
            end = match.end()
            if end > cursor:
                rough_spans.append((cursor, end))
            cursor = end
        if cursor < len(text):
            rough_spans.append((cursor, len(text)))
        units: list[dict[str, Any]] = []
        for start, end in rough_spans:
            piece_start = start
            while end - piece_start > max_unit_chars:
                proposed = piece_start + max_unit_chars
                search_start = piece_start + max_unit_chars // 2
                boundary = max(
                    text.rfind("\n", search_start, proposed),
                    text.rfind("。", search_start, proposed),
                    text.rfind("；", search_start, proposed),
                    text.rfind(" ", search_start, proposed),
                )
                piece_end = boundary + 1 if boundary >= search_start else proposed
                units.append(
                    {
                        "source_text": text[piece_start:piece_end],
                        "source_span": {
                            "start": source_start + piece_start,
                            "end": source_start + piece_end,
                        },
                    }
                )
                piece_start = piece_end
            if piece_start < end:
                units.append(
                    {
                        "source_text": text[piece_start:end],
                        "source_span": {
                            "start": source_start + piece_start,
                            "end": source_start + end,
                        },
                    }
                )
        return units

    @staticmethod
    def _select(
        candidates: list[dict[str, Any]],
        chunks: list[dict[str, Any]],
        max_points: int,
    ) -> list[dict[str, Any]]:
        by_chunk: dict[str, list[dict[str, Any]]] = {}
        for candidate in candidates:
            by_chunk.setdefault(str(candidate["chunk_id"]), []).append(candidate)
        eligible_chunk_ids = [
            str(chunk["chunk_id"])
            for chunk in chunks
            if by_chunk.get(str(chunk["chunk_id"]))
        ]
        if len(eligible_chunk_ids) <= max_points:
            representative_ids = eligible_chunk_ids
        elif max_points == 1:
            representative_ids = [eligible_chunk_ids[0]]
        else:
            representative_indexes = {
                round(index * (len(eligible_chunk_ids) - 1) / (max_points - 1))
                for index in range(max_points)
            }
            representative_ids = [eligible_chunk_ids[index] for index in sorted(representative_indexes)]
        selected: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add(candidate: dict[str, Any]) -> None:
            fingerprint = _fingerprint(str(candidate["text"]))
            if not fingerprint or fingerprint in seen or len(selected) >= max_points:
                return
            seen.add(fingerprint)
            selected.append(candidate)

        for chunk_id in representative_ids:
            for candidate in by_chunk[chunk_id]:
                before = len(selected)
                add(candidate)
                if len(selected) > before:
                    break
        for candidate in sorted(
            candidates,
            key=lambda item: (-item["score"], item["source_span"]["start"]),
        ):
            add(candidate)
        return sorted(selected, key=lambda item: item["source_span"]["start"])
