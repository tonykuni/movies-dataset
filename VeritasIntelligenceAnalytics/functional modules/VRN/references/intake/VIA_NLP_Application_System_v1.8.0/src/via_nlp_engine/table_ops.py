"""Deterministic, provenance-first table recognition for noisy extracted text."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


MARKDOWN_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")
KEY_VALUE_RE = re.compile(r"^\s*(?P<key>[^:：|]{1,40}?)\s*[:：]\s*(?P<value>\S.{0,160})\s*$")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pipe_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


@dataclass(slots=True)
class StructuredTable:
    table_id: str
    kind: str
    source_segment: str
    first_line: int
    last_line: int
    headers: list[str]
    rows: list[list[str]]
    original_text: str
    confidence: float
    review_required: bool
    merged_cell_proposals: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "schema": "VIA_STRUCTURED_TABLE/1.0",
            "kind": self.kind,
            "source_segment": self.source_segment,
            "source_lines": {"first": self.first_line, "last": self.last_line},
            "headers": self.headers,
            "rows": self.rows,
            "original_text": self.original_text,
            "source_sha256": _sha256(self.original_text),
            "confidence": round(self.confidence, 6),
            "review_required": self.review_required,
            "merged_cell_proposals": self.merged_cell_proposals,
            "cell_policy": "verbatim_only_no_silent_fill",
        }


class TextTableExtractor:
    """Recognize explicit tables without inventing missing labels or values."""

    def __init__(self, enabled: bool = True, max_columns: int = 24, max_tables: int = 500) -> None:
        self.enabled = enabled
        self.max_columns = max(2, int(max_columns))
        self.max_tables = max(1, int(max_tables))

    def extract(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        output: list[StructuredTable] = []
        seen_hashes: set[str] = set()
        for segment in segments:
            lines = segment["text"].splitlines()
            candidates = self._markdown_candidates(lines) + self._key_value_candidates(lines)
            for kind, first, last, block in sorted(candidates, key=lambda item: (item[1], item[2], item[0])):
                table = self._parse_candidate(
                    table_id=f"TABLE-{len(output) + 1:05d}",
                    kind=kind,
                    source_segment=segment["segment_id"],
                    first_line=first,
                    last_line=last,
                    lines=block,
                )
                if table is None:
                    continue
                digest = _sha256(table.original_text)
                if digest in seen_hashes:
                    continue
                seen_hashes.add(digest)
                output.append(table)
                if len(output) >= self.max_tables:
                    return [item.to_dict() for item in output]
        return [item.to_dict() for item in output]

    @staticmethod
    def _markdown_candidates(lines: list[str]) -> list[tuple[str, int, int, list[str]]]:
        output: list[tuple[str, int, int, list[str]]] = []
        start: int | None = None
        for index, line in enumerate(lines + [""]):
            is_row = line.count("|") >= 2
            if is_row and start is None:
                start = index
            if not is_row and start is not None:
                block = lines[start:index]
                if len(block) >= 2:
                    output.append(("markdown_pipe", start + 1, index, block))
                start = None
        return output

    @staticmethod
    def _key_value_candidates(lines: list[str]) -> list[tuple[str, int, int, list[str]]]:
        output: list[tuple[str, int, int, list[str]]] = []
        start: int | None = None
        for index, line in enumerate(lines + [""]):
            is_row = bool(KEY_VALUE_RE.match(line))
            if is_row and start is None:
                start = index
            if not is_row and start is not None:
                block = lines[start:index]
                if len(block) >= 2:
                    output.append(("key_value", start + 1, index, block))
                start = None
        return output

    def _parse_candidate(
        self,
        table_id: str,
        kind: str,
        source_segment: str,
        first_line: int,
        last_line: int,
        lines: list[str],
    ) -> StructuredTable | None:
        original = "\n".join(lines)
        if kind == "key_value":
            pairs = [KEY_VALUE_RE.match(line) for line in lines]
            if any(match is None for match in pairs):
                return None
            rows = [[match.group("key").strip(), match.group("value").strip()] for match in pairs if match]
            return StructuredTable(
                table_id=table_id,
                kind=kind,
                source_segment=source_segment,
                first_line=first_line,
                last_line=last_line,
                headers=["field", "value"],
                rows=rows,
                original_text=original,
                confidence=0.88,
                review_required=False,
            )

        parsed = [_pipe_cells(line) for line in lines]
        widths = [len(row) for row in parsed]
        width = max(widths, default=0)
        if width < 2 or width > self.max_columns or min(widths, default=0) < width - 1:
            return None
        separator_indexes = [index for index, line in enumerate(lines) if MARKDOWN_SEPARATOR_RE.match(line)]
        separator_index = separator_indexes[0] if separator_indexes else None
        header_index = max(0, (separator_index or 1) - 1)
        headers = parsed[header_index] + [""] * (width - len(parsed[header_index]))
        body_indexes = [index for index in range(len(parsed)) if index != header_index and index != separator_index]
        rows = [parsed[index] + [""] * (width - len(parsed[index])) for index in body_indexes]
        if not rows:
            return None
        proposals: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows):
            for column_index, cell in enumerate(row):
                if not cell and row_index > 0 and rows[row_index - 1][column_index]:
                    proposals.append(
                        {
                            "row": row_index,
                            "column": column_index,
                            "candidate": rows[row_index - 1][column_index],
                            "action": "review_only_not_applied",
                        }
                    )
        return StructuredTable(
            table_id=table_id,
            kind=kind,
            source_segment=source_segment,
            first_line=first_line,
            last_line=last_line,
            headers=headers,
            rows=rows,
            original_text=original,
            confidence=0.96 if separator_index is not None else 0.80,
            review_required=bool(proposals) or separator_index is None,
            merged_cell_proposals=proposals,
        )
