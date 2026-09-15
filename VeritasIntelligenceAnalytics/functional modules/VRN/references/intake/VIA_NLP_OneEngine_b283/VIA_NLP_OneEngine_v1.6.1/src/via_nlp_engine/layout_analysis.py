"""Lossless Markdown-oriented layout analysis and NLP repair projection."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any


LAYOUT_SCHEMA = "VIA_MARKDOWN_LAYOUT_ANALYSIS/1.0"
MAX_INLINE_MARKS_PER_BLOCK = 200

BLOCK_LABELS = {
    "front_matter": {"zh": "前置中繼資料", "en": "Front Matter"},
    "heading": {"zh": "標題", "en": "Heading"},
    "paragraph": {"zh": "段落", "en": "Paragraph"},
    "blank": {"zh": "空白", "en": "Blank"},
    "unordered_list": {"zh": "項目清單", "en": "Unordered List"},
    "ordered_list": {"zh": "編號清單", "en": "Ordered List"},
    "task_list": {"zh": "工作清單", "en": "Task List"},
    "blockquote": {"zh": "引用", "en": "Block Quote"},
    "table": {"zh": "表格", "en": "Table"},
    "fenced_code": {"zh": "圍欄程式碼", "en": "Fenced Code"},
    "indented_code": {"zh": "縮排程式碼", "en": "Indented Code"},
    "html_block": {"zh": "HTML 區塊", "en": "HTML Block"},
    "math_block": {"zh": "數學區塊", "en": "Math Block"},
    "thematic_break": {"zh": "分隔線", "en": "Thematic Break"},
    "source_record_marker": {"zh": "來源記錄標記", "en": "Source Record Marker"},
}

INLINE_PATTERNS = {
    "image": re.compile(r"!\[[^\]]*\]\([^\n)]+\)"),
    "link": re.compile(r"(?<!!)\[[^\]]+\]\([^\n)]+\)"),
    "inline_code": re.compile(r"(?<!`)`[^`\n]+`(?!`)"),
    "strong": re.compile(r"(?:\*\*|__)(?=\S).+?(?<=\S)(?:\*\*|__)", re.S),
    "emphasis": re.compile(r"(?<!\*)\*(?!\*)(?=\S).+?(?<=\S)\*(?!\*)", re.S),
    "strikethrough": re.compile(r"~~(?=\S).+?(?<=\S)~~", re.S),
    "autolink": re.compile(r"https?://[^\s>)]+", re.I),
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class MarkdownLayoutAnalyzer:
    """Classify every source character into a Markdown layout block."""

    def build(
        self,
        text: str,
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raw_blocks = self._blocks(text)
        refined = {item["segment_id"]: item for item in refinement_ledger}
        blocks: list[dict[str, Any]] = []
        for index, item in enumerate(raw_blocks, start=1):
            source_segments = [
                segment["segment_id"]
                for segment in segments
                if item["start"] < int(segment["source_span"]["end"])
                and item["end"] > int(segment["source_span"]["start"])
            ]
            repair_changes = [
                change
                for segment_id in source_segments
                for change in refined.get(segment_id, {}).get("changes", [])
            ]
            blocks.append(
                {
                    "layout_id": f"LAYOUT-{index:06d}",
                    "block_type": item["type"],
                    "block_label": BLOCK_LABELS[item["type"]],
                    "source_span": {"start": item["start"], "end": item["end"]},
                    "source_text": item["text"],
                    "source_sha256": _sha256(item["text"]),
                    "source_segments": source_segments,
                    "attributes": self._attributes(item["type"], item["text"]),
                    "inline_marks": self._inline_marks(item["text"], item["start"]),
                    "nlp_repair_projection": {
                        "candidate_changes": repair_changes,
                        "automatic_layout_writeback": False,
                        "source_text_preserved": True,
                    },
                }
            )
        reconstructed = "".join(item["source_text"] for item in blocks)
        counts = Counter(item["block_type"] for item in blocks)
        return {
            "schema": LAYOUT_SCHEMA,
            "languages": ["zh", "en"],
            "input_projection": "markdown_or_plain_text",
            "blocks": blocks,
            "statistics": {
                "blocks": len(blocks),
                "block_type_counts": dict(sorted(counts.items())),
                "inline_marks": sum(len(item["inline_marks"]) for item in blocks),
                "source_characters": len(text),
            },
            "completeness": {
                "exact_reconstruction": reconstructed == text,
                "coverage_ratio": 1.0 if reconstructed == text else len(reconstructed) / max(1, len(text)),
                "source_sha256": _sha256(text),
                "reconstructed_sha256": _sha256(reconstructed),
            },
            "quality_gates": {
                "all_characters_classified": reconstructed == text,
                "nlp_repair_is_derivative": True,
                "automatic_layout_reorder": False,
                "automatic_source_mutation": False,
                "unsupported_construct_policy": "preserve_as_paragraph",
            },
        }

    def _blocks(self, text: str) -> list[dict[str, Any]]:
        lines: list[tuple[int, int, str]] = []
        position = 0
        for line in text.splitlines(keepends=True):
            lines.append((position, position + len(line), line))
            position += len(line)
        if position < len(text):
            lines.append((position, len(text), text[position:]))
        if not lines and text == "":
            return []

        blocks: list[dict[str, Any]] = []
        index = 0
        front_matter_allowed = True
        while index < len(lines):
            start, end, line = lines[index]
            stripped = line.strip("\r\n")
            if front_matter_allowed and index == 0 and stripped == "---":
                index, end = self._consume_until(lines, index, lambda value: value.strip("\r\n") in {"---", "..."})
                block_type = "front_matter"
            elif re.match(r"^\s*(?:```|~~~)", line):
                fence = re.match(r"^\s*(```+|~~~+)", line)
                marker = fence.group(1)[0] if fence else "`"
                index, end = self._consume_until(
                    lines, index, lambda value: bool(re.match(rf"^\s*{re.escape(marker)}{{3,}}\s*$", value.strip("\r\n")))
                )
                block_type = "fenced_code"
            elif stripped == "$$":
                index, end = self._consume_until(lines, index, lambda value: value.strip("\r\n") == "$$")
                block_type = "math_block"
            else:
                block_type = self._line_type(line, lines, index)
                index += 1
                while index < len(lines) and self._line_type(lines[index][2], lines, index) == block_type and block_type in {
                    "paragraph", "blank", "unordered_list", "ordered_list", "task_list", "blockquote",
                    "table", "indented_code", "html_block", "source_record_marker",
                }:
                    end = lines[index][1]
                    index += 1
            front_matter_allowed = False
            blocks.append({"start": start, "end": end, "text": text[start:end], "type": block_type})
        return blocks

    @staticmethod
    def _consume_until(
        lines: list[tuple[int, int, str]],
        start_index: int,
        closes: Any,
    ) -> tuple[int, int]:
        index = start_index + 1
        end = lines[start_index][1]
        while index < len(lines):
            end = lines[index][1]
            if closes(lines[index][2]):
                return index + 1, end
            index += 1
        return index, end

    @staticmethod
    def _line_type(line: str, lines: list[tuple[int, int, str]], index: int) -> str:
        stripped = line.strip("\r\n")
        if not stripped.strip():
            return "blank"
        if re.match(r"^===== (?:BEGIN|END) VIA SOURCE RECORD", stripped) or re.match(r"^===== (?:BEGIN|END) EXTRACTED CONTENT", stripped):
            return "source_record_marker"
        if re.match(r"^ {0,3}#{1,6}(?:\s+|$)", line) or (
            index + 1 < len(lines) and re.match(r"^ {0,3}(?:=+|-+)\s*$", lines[index + 1][2].strip("\r\n"))
        ):
            return "heading"
        if re.match(r"^\s*[-+*]\s+\[[ xX]\]\s+", line):
            return "task_list"
        if re.match(r"^\s*[-+*]\s+", line):
            return "unordered_list"
        if re.match(r"^\s*\d+[.)]\s+", line):
            return "ordered_list"
        if re.match(r"^\s*>\s?", line):
            return "blockquote"
        if re.match(r"^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$", stripped):
            return "thematic_break"
        if line.startswith(("    ", "\t")):
            return "indented_code"
        if re.match(r"^\s*</?[A-Za-z][^>]*>", line):
            return "html_block"
        if "|" in line:
            previous_table = index > 0 and "|" in lines[index - 1][2]
            next_separator = index + 1 < len(lines) and bool(
                re.match(r"^\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)+\s*\|?\s*$", lines[index + 1][2].strip("\r\n"))
            )
            separator = bool(re.match(r"^\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)+\s*\|?\s*$", stripped))
            if previous_table or next_separator or separator:
                return "table"
        return "paragraph"

    @staticmethod
    def _attributes(block_type: str, text: str) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        if block_type == "heading":
            match = re.match(r"^\s*(#{1,6})\s+", text)
            attributes["level"] = len(match.group(1)) if match else 1
        elif block_type == "fenced_code":
            match = re.match(r"^\s*(?:```|~~~)\s*([^\s`]*)", text)
            attributes["language"] = match.group(1) if match and match.group(1) else "unknown"
        elif block_type == "table":
            attributes["row_count"] = sum(bool(line.strip()) for line in text.splitlines())
            attributes["estimated_columns"] = max((line.count("|") - 1 for line in text.splitlines()), default=0)
        elif block_type == "task_list":
            attributes["checked_items"] = len(re.findall(r"^\s*[-+*]\s+\[[xX]\]", text, flags=re.M))
            attributes["unchecked_items"] = len(re.findall(r"^\s*[-+*]\s+\[ \]", text, flags=re.M))
        return attributes

    @staticmethod
    def _inline_marks(text: str, absolute_start: int) -> list[dict[str, Any]]:
        marks: list[dict[str, Any]] = []
        for mark_type, pattern in INLINE_PATTERNS.items():
            for match in pattern.finditer(text):
                marks.append(
                    {
                        "mark_type": mark_type,
                        "source_span": {"start": absolute_start + match.start(), "end": absolute_start + match.end()},
                        "source_text": match.group(0),
                    }
                )
                if len(marks) >= MAX_INLINE_MARKS_PER_BLOCK:
                    return sorted(marks, key=lambda item: (item["source_span"]["start"], item["mark_type"]))
        return sorted(marks, key=lambda item: (item["source_span"]["start"], item["mark_type"]))
