#!/usr/bin/env python3
"""Evidence-preserving Markdown segmentation and table reconstruction analysis."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


# =============================================================================
# 參數區：所有判斷門檻集中於此，避免散落在函式內。
# =============================================================================

RECONSTRUCTION_SCHEMA_VERSION = "1.2"
DEFAULT_ENCODING = "utf-8"
MAX_TITLE_LENGTH = 100
LONG_SENTENCE_LENGTH = 180
SHORT_TITLE_LENGTH = 60
MIN_TOPIC_SENTENCE_LENGTH = 20
TOPIC_DISCONTINUITY_THRESHOLD = 0.02
REPEATED_BLOCK_THRESHOLD = 3
HEADING_PATTERN = re.compile(r"^(#{1,6})(?:[ \t]+|(?=[^#\s]))(.+?)\s*#*\s*$")
SETEXT_PATTERN = re.compile(r"^\s*(=+|-+)\s*$")
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
LIST_PATTERN = re.compile(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$")
ORDERED_LIST_PATTERN = re.compile(r"^\s*(\d+)[.)]\s+")
BLOCKQUOTE_PATTERN = re.compile(r"^\s*>\s?(.*)$")
HTML_TAG_PATTERN = re.compile(r"^\s*</?[A-Za-z][^>]*>\s*$")
KEY_VALUE_PATTERN = re.compile(r"^([^\n:：]{1,50})\s*[:：]\s*(.+)$")
METRIC_PATTERN = re.compile(
    r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?\s*(?:%|％|元|萬元|億元|千|萬|億|kg|g|km|m|ms|s|秒|分鐘|小時|日|天|年|bps|x)?",
    flags=re.IGNORECASE,
)
CJK_LATIN_FUSION_PATTERN = re.compile(r"(?:[\u3400-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u3400-\u9fff])")
ABBREVIATIONS = {
    "e.g.",
    "i.e.",
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "vs.",
    "etc.",
    "fig.",
    "no.",
    "inc.",
    "ltd.",
}
SENTENCE_TERMINATORS = {"。", "！", "？", "!", "?"}
SENTENCE_CLOSERS = {'"', "'", "”", "’", "」", "』", ")", "]", "】", "〉", "》"}
NO_TOUCH_BLOCK_TYPES = {"frontmatter", "code", "html"}
INFORMATION_ACTION_TERMS = {
    "必須",
    "需要",
    "應該",
    "請",
    "待辦",
    "執行",
    "修正",
    "驗證",
    "must",
    "should",
    "todo",
    "action",
}
INFORMATION_DEFINITION_TERMS = {"定義", "指的是", "稱為", "代表", "意指", " is ", " means ", " refers to "}
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "以及",
    "一個",
    "這個",
    "可以",
    "使用",
    "進行",
}


def def_sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode(DEFAULT_ENCODING)).hexdigest()


def def_normalize_semantic_text(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def def_finding(
    code: str,
    severity: str,
    message: str,
    start_line: int,
    end_line: int | None = None,
    confidence: float = 0.8,
    evidence: str = "",
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "start_line": start_line,
        "end_line": end_line or start_line,
        "confidence": round(max(0.0, min(confidence, 1.0)), 3),
        "evidence": evidence[:240],
    }


def def_count_unescaped_pipes(line: str) -> int:
    count = 0
    escaped = False
    code_ticks = 0
    index = 0
    while index < len(line):
        character = line[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if character == "\\":
            escaped = True
            index += 1
            continue
        if character == "`":
            run = 1
            while index + run < len(line) and line[index + run] == "`":
                run += 1
            code_ticks = 0 if code_ticks == run else run
            index += run
            continue
        if character == "|" and code_ticks == 0:
            count += 1
        index += 1
    return count


def def_split_pipe_row(line: str) -> list[str]:
    stripped = line.strip()
    leading_boundary = stripped.startswith("|")
    trailing_boundary = stripped.endswith("|") and not stripped.endswith("\\|")
    if leading_boundary:
        stripped = stripped[1:]
    if trailing_boundary:
        stripped = stripped[:-1]
    cells: list[str] = []
    buffer: list[str] = []
    escaped = False
    code_ticks = 0
    index = 0
    while index < len(stripped):
        character = stripped[index]
        if escaped:
            buffer.append(character)
            escaped = False
            index += 1
            continue
        if character == "\\":
            buffer.append(character)
            escaped = True
            index += 1
            continue
        if character == "`":
            run = 1
            while index + run < len(stripped) and stripped[index + run] == "`":
                run += 1
            buffer.extend("`" * run)
            code_ticks = 0 if code_ticks == run else run
            index += run
            continue
        if character == "|" and code_ticks == 0:
            cells.append("".join(buffer).strip())
            buffer = []
        else:
            buffer.append(character)
        index += 1
    cells.append("".join(buffer).strip())
    return cells


def def_is_delimiter_cells(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def def_is_delimiter_like_cells(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in cells)


def def_find_frontmatter_range(lines: list[str]) -> tuple[int, int, bool] | None:
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            return 0, index, True
    return 0, len(lines) - 1, False


def def_find_fence_ranges(lines: list[str]) -> list[tuple[int, int, bool]]:
    ranges: list[tuple[int, int, bool]] = []
    index = 0
    while index < len(lines):
        match = FENCE_PATTERN.match(lines[index])
        if not match:
            index += 1
            continue
        marker = match.group(1)
        marker_character = marker[0]
        marker_length = len(marker)
        end_index = index + 1
        closed = False
        while end_index < len(lines):
            candidate = lines[end_index].lstrip()
            if candidate.startswith(marker_character * marker_length):
                closed = True
                break
            end_index += 1
        ranges.append((index, min(end_index, len(lines) - 1), closed))
        index = end_index + 1 if closed else len(lines)
    return ranges


def def_index_ranges(ranges: list[tuple[int, int, Any]]) -> dict[int, tuple[int, int, Any]]:
    result: dict[int, tuple[int, int, Any]] = {}
    for item in ranges:
        for line_index in range(item[0], item[1] + 1):
            result[line_index] = item
    return result


def def_find_table_ranges(
    lines: list[str],
    protected_indices: set[int],
) -> list[tuple[int, int, dict[str, Any]]]:
    ranges: list[tuple[int, int, dict[str, Any]]] = []
    index = 0
    while index < len(lines):
        if index in protected_indices or def_count_unescaped_pipes(lines[index]) < 1:
            index += 1
            continue
        start = index
        candidate_lines = []
        while (
            index < len(lines)
            and index not in protected_indices
            and lines[index].strip()
            and def_count_unescaped_pipes(lines[index]) >= 1
        ):
            candidate_lines.append(lines[index])
            index += 1
        rows = [def_split_pipe_row(line) for line in candidate_lines]
        widths = [len(row) for row in rows]
        delimiter_indices = [row_index for row_index, row in enumerate(rows) if def_is_delimiter_cells(row)]
        delimiter_like_indices = [row_index for row_index, row in enumerate(rows) if def_is_delimiter_like_cells(row)]
        consistent = bool(widths) and len(set(widths)) == 1 and widths[0] >= 2
        if len(rows) >= 2 and (delimiter_indices or consistent):
            ranges.append(
                (
                    start,
                    index - 1,
                    {
                        "rows": rows,
                        "widths": widths,
                        "delimiter_indices": delimiter_indices,
                        "delimiter_like_indices": delimiter_like_indices,
                        "consistent": consistent,
                        "raw_lines": candidate_lines,
                    },
                )
            )
        if index == start:
            index += 1
    return ranges


def def_is_structural_start(line: str, next_line: str | None = None) -> bool:
    if not line.strip():
        return True
    if HEADING_PATTERN.match(line) or FENCE_PATTERN.match(line) or LIST_PATTERN.match(line):
        return True
    if BLOCKQUOTE_PATTERN.match(line) or HTML_TAG_PATTERN.match(line):
        return True
    return bool(next_line is not None and SETEXT_PATTERN.match(next_line) and line.strip())


def def_classify_blocks(lines: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    frontmatter = def_find_frontmatter_range(lines)
    fence_ranges = def_find_fence_ranges(lines)
    protected_indices: set[int] = set()
    if frontmatter:
        protected_indices.update(range(frontmatter[0], frontmatter[1] + 1))
    for start, end, _closed in fence_ranges:
        protected_indices.update(range(start, end + 1))
    table_ranges = def_find_table_ranges(lines, protected_indices)
    table_index = def_index_ranges(table_ranges)
    fence_index = def_index_ranges(fence_ranges)
    block_id = 0
    index = 0
    while index < len(lines):
        if frontmatter and index == frontmatter[0]:
            start, end, closed = frontmatter
            blocks.append(def_make_block(block_id, "frontmatter", start, end, lines[start : end + 1], 1.0))
            if not closed:
                findings.append(def_finding("T011", "error", "Front matter 未閉合", 1, len(lines), 1.0))
            block_id += 1
            index = end + 1
            continue
        if index in fence_index and index == fence_index[index][0]:
            start, end, closed = fence_index[index]
            blocks.append(def_make_block(block_id, "code", start, end, lines[start : end + 1], 1.0 if closed else 0.2))
            if not closed:
                findings.append(def_finding("T010", "error", "程式碼 fence 未閉合", start + 1, end + 1, 1.0))
            block_id += 1
            index = end + 1
            continue
        if index in table_index and index == table_index[index][0]:
            start, end, metadata = table_index[index]
            blocks.append(def_make_block(block_id, "table", start, end, lines[start : end + 1], 0.95, metadata))
            block_id += 1
            index = end + 1
            continue
        line = lines[index]
        if not line.strip():
            start = index
            while index + 1 < len(lines) and not lines[index + 1].strip():
                index += 1
            blocks.append(def_make_block(block_id, "blank", start, index, lines[start : index + 1], 1.0))
            block_id += 1
            index += 1
            continue
        heading = HEADING_PATTERN.match(line)
        if heading:
            metadata = {"depth": len(heading.group(1)), "text": heading.group(2).strip()}
            blocks.append(def_make_block(block_id, "heading", index, index, [line], 1.0, metadata))
            block_id += 1
            index += 1
            continue
        if index + 1 < len(lines) and SETEXT_PATTERN.match(lines[index + 1]) and line.strip():
            depth = 1 if lines[index + 1].lstrip().startswith("=") else 2
            metadata = {"depth": depth, "text": line.strip(), "style": "setext"}
            blocks.append(def_make_block(block_id, "heading", index, index + 1, lines[index : index + 2], 0.98, metadata))
            block_id += 1
            index += 2
            continue
        list_match = LIST_PATTERN.match(line)
        if list_match:
            metadata = {"indent": len(list_match.group(1).replace("\t", "    ")), "marker": list_match.group(2)}
            blocks.append(def_make_block(block_id, "list_item", index, index, [line], 0.98, metadata))
            block_id += 1
            index += 1
            continue
        if BLOCKQUOTE_PATTERN.match(line):
            start = index
            while index + 1 < len(lines) and BLOCKQUOTE_PATTERN.match(lines[index + 1]):
                index += 1
            blocks.append(def_make_block(block_id, "blockquote", start, index, lines[start : index + 1], 0.98))
            block_id += 1
            index += 1
            continue
        if HTML_TAG_PATTERN.match(line):
            blocks.append(def_make_block(block_id, "html", index, index, [line], 0.9))
            block_id += 1
            index += 1
            continue
        start = index
        while index + 1 < len(lines):
            candidate = lines[index + 1]
            after_candidate = lines[index + 2] if index + 2 < len(lines) else None
            if index + 1 in table_index or index + 1 in fence_index:
                break
            if def_is_structural_start(candidate, after_candidate):
                break
            index += 1
        blocks.append(def_make_block(block_id, "paragraph", start, index, lines[start : index + 1], 0.95))
        block_id += 1
        index += 1
    tables, table_findings = def_analyze_tables(blocks)
    findings.extend(table_findings)
    findings.extend(def_detect_text_failures(lines, blocks))
    return blocks, tables, findings


def def_make_block(
    block_id: int,
    block_type: str,
    start_index: int,
    end_index: int,
    raw_lines: list[str],
    confidence: float,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = "\n".join(raw_lines)
    return {
        "block_id": f"B{block_id + 1:05d}",
        "type": block_type,
        "start_line": start_index + 1,
        "end_line": end_index + 1,
        "text": text,
        "text_sha256": def_sha256_text(text),
        "confidence": confidence,
        "metadata": metadata or {},
    }


def def_sentence_source(block: dict[str, Any]) -> str:
    text = block["text"]
    if block["type"] == "list_item":
        match = LIST_PATTERN.match(text)
        return match.group(3) if match else text
    if block["type"] == "blockquote":
        values = [
            BLOCKQUOTE_PATTERN.match(line).group(1)
            for line in text.splitlines()
            if BLOCKQUOTE_PATTERN.match(line)
        ]
        if values and re.fullmatch(r"\[![A-Za-z]+\]", values[0].strip()):
            values = values[1:]
        return " ".join(values)
    return " ".join(line.strip() for line in text.splitlines())


def def_period_is_boundary(text: str, index: int) -> bool:
    previous_character = text[index - 1] if index > 0 else ""
    next_character = text[index + 1] if index + 1 < len(text) else ""
    if previous_character.isdigit() and next_character.isdigit():
        return False
    prefix = text[: index + 1].casefold()
    token_match = re.search(r"([a-z]+\.)$", prefix)
    if token_match and token_match.group(1) in ABBREVIATIONS:
        return False
    if re.search(r"(?:https?://|www\.)\S*$", text[: index + 1], flags=re.IGNORECASE):
        return False
    return not next_character or next_character.isspace() or next_character in SENTENCE_CLOSERS


def def_split_sentences(text: str) -> list[dict[str, Any]]:
    compact = re.sub(r"[ \t\r\n]+", " ", text).strip()
    if not compact:
        return []
    sentences: list[dict[str, Any]] = []
    start = 0
    index = 0
    while index < len(compact):
        character = compact[index]
        boundary = character in SENTENCE_TERMINATORS or (character == "." and def_period_is_boundary(compact, index))
        if boundary:
            end = index + 1
            while end < len(compact) and compact[end] in SENTENCE_CLOSERS:
                end += 1
            sentence = compact[start:end].strip()
            if sentence:
                sentences.append({"text": sentence, "boundary": "explicit", "confidence": 0.99})
            start = end
            index = end
            continue
        index += 1
    remainder = compact[start:].strip()
    if remainder:
        confidence = 0.84 if len(remainder) <= LONG_SENTENCE_LENGTH else 0.58
        sentences.append({"text": remainder, "boundary": "block-end", "confidence": confidence})
    return sentences


def def_terms(text: str) -> set[str]:
    latin = {word.casefold() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)}
    cjk_runs = re.findall(r"[\u3400-\u9fff]{2,}", text)
    cjk = {run[index : index + 2] for run in cjk_runs for index in range(len(run) - 1)}
    return {term for term in latin | cjk if term not in STOPWORDS}


def def_jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def def_build_sentences(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sentences: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    sentence_id = 0
    for block in blocks:
        if block["type"] not in {"paragraph", "list_item", "blockquote"}:
            continue
        split_items = def_split_sentences(def_sentence_source(block))
        for split_index, split_item in enumerate(split_items):
            sentence_id += 1
            sentence_text = split_item["text"]
            sentences.append(
                {
                    "sentence_id": f"S{sentence_id:06d}",
                    "block_id": block["block_id"],
                    "start_line": block["start_line"],
                    "end_line": block["end_line"],
                    "sequence_in_block": split_index + 1,
                    "text": sentence_text,
                    "semantic_sha256": def_sha256_text(def_normalize_semantic_text(sentence_text)),
                    "boundary": split_item["boundary"],
                    "confidence": split_item["confidence"],
                    "terms": sorted(def_terms(sentence_text))[:24],
                }
            )
        if len(split_items) >= 3:
            for left, right in zip(split_items, split_items[1:]):
                if min(len(left["text"]), len(right["text"])) < MIN_TOPIC_SENTENCE_LENGTH:
                    continue
                similarity = def_jaccard(def_terms(left["text"]), def_terms(right["text"]))
                if similarity < TOPIC_DISCONTINUITY_THRESHOLD:
                    findings.append(
                        def_finding(
                            "T019",
                            "warning",
                            "同一段落內相鄰句主題詞完全斷裂，可能誤接",
                            block["start_line"],
                            block["end_line"],
                            0.72,
                            f"{left['text'][:80]} || {right['text'][:80]}",
                        )
                    )
    return sentences, findings


def def_detect_text_failures(lines: list[str], blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    previous_heading_depth = 0
    heading_counts: dict[str, int] = {}
    short_block_counts: dict[str, list[int]] = {}
    for block_index, block in enumerate(blocks):
        block_type = block["type"]
        text = block["text"]
        if block_type == "heading":
            depth = int(block["metadata"].get("depth", 1))
            heading_text = str(block["metadata"].get("text", "")).strip()
            normalized_heading = def_normalize_semantic_text(heading_text)
            heading_counts[normalized_heading] = heading_counts.get(normalized_heading, 0) + 1
            if previous_heading_depth and depth > previous_heading_depth + 1:
                findings.append(def_finding("T004", "warning", "標題層級跳階", block["start_line"], confidence=0.98, evidence=text))
            previous_heading_depth = depth
            terminal_match = re.search(r"[。！？!?]", heading_text)
            if len(heading_text) > MAX_TITLE_LENGTH or (terminal_match and len(heading_text[terminal_match.end() :].strip()) >= 6):
                findings.append(def_finding("T002", "warning", "標題行疑似黏入正文", block["start_line"], confidence=0.86, evidence=text))
            if not heading_text:
                findings.append(def_finding("T020", "error", "空白標題", block["start_line"], confidence=1.0, evidence=text))
            following = next((item for item in blocks[block_index + 1 :] if item["type"] != "blank"), None)
            following_depth = int(following["metadata"].get("depth", 1)) if following and following["type"] == "heading" else None
            if following is None or (following_depth is not None and following_depth <= depth):
                findings.append(def_finding("T006", "warning", "標題下沒有內容", block["start_line"], confidence=0.92, evidence=text))
        if block_type == "paragraph":
            compact = re.sub(r"\s+", " ", text).strip()
            if len(compact) > LONG_SENTENCE_LENGTH and not re.search(r"[。！？!?]", compact):
                findings.append(def_finding("T001", "warning", "過長段落缺少可確認句界", block["start_line"], block["end_line"], 0.9, compact))
            if block["start_line"] == block["end_line"] and len(compact) <= SHORT_TITLE_LENGTH and not re.search(r"[。！？!?.]$", compact):
                previous_blank = block_index == 0 or blocks[block_index - 1]["type"] == "blank"
                next_blank = block_index + 1 < len(blocks) and blocks[block_index + 1]["type"] == "blank"
                if previous_blank and next_blank:
                    findings.append(def_finding("T003", "info", "短獨立行可能是遺失標記的標題，禁止自動升級", block["start_line"], confidence=0.55, evidence=text))
        if block_type == "list_item":
            indent = int(block["metadata"].get("indent", 0))
            if indent % 2:
                findings.append(def_finding("T007", "warning", "清單縮排不是 2 的倍數", block["start_line"], confidence=0.82, evidence=text))
            match = LIST_PATTERN.match(text)
            if match and not match.group(3).strip():
                findings.append(def_finding("T020", "error", "空白清單項目", block["start_line"], confidence=1.0, evidence=text))
        normalized_short = def_normalize_semantic_text(text)
        if block_type in {"paragraph", "heading"} and 0 < len(normalized_short) <= 80:
            short_block_counts.setdefault(normalized_short, []).append(block["start_line"])
    for heading, count in heading_counts.items():
        if heading and count > 1:
            matching = [block for block in blocks if block["type"] == "heading" and def_normalize_semantic_text(block["metadata"].get("text", "")) == heading]
            findings.append(def_finding("T005", "info", "重複標題可能造成歸屬歧義", matching[0]["start_line"], matching[-1]["end_line"], 0.75, heading))
    for normalized, line_numbers in short_block_counts.items():
        if len(line_numbers) >= REPEATED_BLOCK_THRESHOLD:
            findings.append(def_finding("T018", "warning", "短區塊重複出現，可能是頁首頁尾污染", line_numbers[0], line_numbers[-1], 0.82, normalized))
    for line_index, line in enumerate(lines):
        if re.search(r"[A-Za-z]-\s*$", line) and line_index + 1 < len(lines) and re.match(r"^\s*[a-z]", lines[line_index + 1]):
            findings.append(def_finding("T013", "warning", "疑似跨行斷字，禁止直接拼接", line_index + 1, line_index + 2, 0.85, f"{line} | {lines[line_index + 1]}"))
        if re.search(r"\d+\.\d+(?:\.\d+)+", line):
            findings.append(def_finding("T014", "info", "版本號含句點，已套用防誤斷規則", line_index + 1, confidence=0.99, evidence=line))
        if any(abbreviation in line.casefold() for abbreviation in ABBREVIATIONS):
            findings.append(def_finding("T015", "info", "縮寫含句點，已套用防誤斷規則", line_index + 1, confidence=0.99, evidence=line))
        if CJK_LATIN_FUSION_PATTERN.search(line):
            findings.append(def_finding("T016", "info", "中英數相鄰，交由中文排版器處理，不作句界", line_index + 1, confidence=0.95, evidence=line))
        if re.search(r"([。！？!?])\1{2,}", line):
            findings.append(def_finding("T017", "warning", "重複標點可能來自 OCR 或轉換錯誤", line_index + 1, confidence=0.92, evidence=line))
    for left, right in zip(blocks, blocks[1:]):
        if left["type"] == "blockquote" and right["type"] == "paragraph" and left["end_line"] + 1 == right["start_line"]:
            findings.append(def_finding("T009", "warning", "引用區塊後一行未留邊界，可能遺失 > 前綴", right["start_line"], confidence=0.7, evidence=right["text"]))
    ordered_groups: list[list[tuple[int, int]]] = []
    current_group: list[tuple[int, int]] = []
    for block in blocks:
        match = ORDERED_LIST_PATTERN.match(block["text"]) if block["type"] == "list_item" else None
        if match:
            current_group.append((int(match.group(1)), block["start_line"]))
        elif block["type"] != "blank" and current_group:
            ordered_groups.append(current_group)
            current_group = []
    if current_group:
        ordered_groups.append(current_group)
    for group in ordered_groups:
        for (left_number, _), (right_number, right_line) in zip(group, group[1:]):
            if right_number not in {1, left_number + 1}:
                findings.append(def_finding("T008", "warning", "有序清單編號不連續", right_line, confidence=0.9, evidence=str(right_number)))
    return findings


def def_analyze_tables(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tables: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    table_number = 0
    for block in blocks:
        if block["type"] != "table":
            continue
        table_number += 1
        metadata = block["metadata"]
        rows = metadata["rows"]
        widths = metadata["widths"]
        delimiter_indices = metadata["delimiter_indices"]
        delimiter_like_indices = metadata.get("delimiter_like_indices", [])
        expected_columns = max(set(widths), key=widths.count) if widths else 0
        header_index = 0
        delimiter_index = delimiter_indices[0] if delimiter_indices else (delimiter_like_indices[0] if delimiter_like_indices else None)
        data_rows = [row for row_index, row in enumerate(rows) if row_index != delimiter_index]
        table = {
            "table_id": f"T{table_number:05d}",
            "block_id": block["block_id"],
            "start_line": block["start_line"],
            "end_line": block["end_line"],
            "expected_columns": expected_columns,
            "row_count": max(0, len(data_rows) - 1),
            "delimiter_index": delimiter_index,
            "headers": rows[header_index] if rows else [],
            "rows": data_rows[1:] if data_rows else [],
            "matrix_sha256": def_sha256_text(
                json.dumps(
                    [[def_normalize_semantic_text(cell) for cell in row] for row in data_rows],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            ),
            "confidence": 1.0,
        }
        if not delimiter_indices:
            findings.append(def_finding("B001", "warning", "表格缺少有效標頭分隔列，禁止補造資料格", block["start_line"], block["end_line"], 0.95))
            table["confidence"] -= 0.25
        elif len(rows[delimiter_index]) != len(rows[header_index]):
            findings.append(def_finding("B002", "error", "表格分隔列欄數與標頭不一致", block["start_line"] + delimiter_index, confidence=1.0))
            table["confidence"] -= 0.45
        if len(set(widths)) > 1:
            findings.append(def_finding("B003", "error", "表格各列欄數不一致", block["start_line"], block["end_line"], 1.0, str(widths)))
            findings.append(def_finding("B004", "warning", "可能有未跳脫的 | 或遺失分隔符", block["start_line"], block["end_line"], 0.8))
            table["confidence"] -= 0.45
        for row_index, (row, width) in enumerate(zip(rows, widths)):
            line_number = block["start_line"] + row_index
            if row_index == delimiter_index:
                continue
            if width < expected_columns:
                findings.append(def_finding("B007", "warning", "疑似合併欄或缺失空白欄", line_number, confidence=0.86, evidence=str(row)))
            if width > expected_columns:
                findings.append(def_finding("B008", "warning", "疑似欄位被錯誤切開", line_number, confidence=0.86, evidence=str(row)))
            if any("<br" in cell.lower() or "  \n" in cell for cell in row):
                findings.append(def_finding("B006", "info", "儲存格包含多行內容，需保留原順序", line_number, confidence=0.95))
            if any(re.fullmatch(r"[-+$€£¥NT$元]+", cell.strip(), flags=re.IGNORECASE) for cell in row if cell.strip()):
                findings.append(def_finding("B010", "warning", "貨幣或正負號可能與數值分離", line_number, confidence=0.78, evidence=str(row)))
            if any(re.search(r"\d{1,3}(?:[,.]\d{3})+[,.]\d+", cell) for cell in row):
                findings.append(def_finding("B011", "warning", "小數點與千分位格式混雜", line_number, confidence=0.75, evidence=str(row)))
            if any(re.fullmatch(r"\[\^?\d+\]|\[\^\d+\]|<sup>\d+</sup>", cell.strip(), flags=re.IGNORECASE) for cell in row if cell.strip()):
                findings.append(def_finding("B017", "info", "腳註標記可能被吸收入儲存格", line_number, confidence=0.7, evidence=str(row)))
        raw_lines = metadata["raw_lines"]
        if any(not line.strip().startswith("|") or not line.rstrip().endswith("|") for line in raw_lines):
            findings.append(def_finding("B009", "info", "表格缺少外側 pipe，但不影響欄位語意", block["start_line"], block["end_line"], 0.99))
        if any("`" in line and "|" in line for line in raw_lines):
            findings.append(def_finding("B005", "info", "inline code 內 pipe 已由狀態機保護", block["start_line"], block["end_line"], 0.99))
        if any("rowspan=" in line.lower() for line in raw_lines):
            findings.append(def_finding("B014", "warning", "HTML rowspan 無法直接映射為標準 Markdown", block["start_line"], block["end_line"], 0.98))
        if delimiter_index is not None and any(row == rows[0] for row in rows[delimiter_index + 1 :]):
            findings.append(def_finding("B015", "warning", "頁面串接後出現重複表頭", block["start_line"], block["end_line"], 0.9))
        if rows and sum(not cell.strip() for row in data_rows for cell in row) and len(set(widths)) > 1:
            findings.append(def_finding("B019", "warning", "無法區分空白儲存格與遺失欄位", block["start_line"], block["end_line"], 0.9))
        if delimiter_index is not None and all(not cell.startswith(":") and not cell.endswith(":") for cell in rows[delimiter_index]):
            findings.append(def_finding("B020", "info", "未宣告欄位對齊，保留為預設對齊", block["start_line"] + delimiter_index, confidence=0.99))
        table["confidence"] = round(max(0.0, table["confidence"]), 3)
        tables.append(table)
    return tables, findings


def def_heading_context(blocks: list[dict[str, Any]]) -> dict[str, list[str]]:
    context: dict[str, list[str]] = {}
    stack: list[tuple[int, str]] = []
    for block in blocks:
        if block["type"] == "heading":
            depth = int(block["metadata"].get("depth", 1))
            title = str(block["metadata"].get("text", "")).strip()
            stack = [(level, text) for level, text in stack if level < depth]
            stack.append((depth, title))
        context[block["block_id"]] = [text for _level, text in stack]
    return context


def def_information_kind(text: str) -> str:
    folded = f" {text.casefold()} "
    if KEY_VALUE_PATTERN.match(text.strip()):
        return "key_value"
    if any(term.casefold() in folded for term in INFORMATION_ACTION_TERMS):
        return "action"
    if any(term.casefold() in folded for term in INFORMATION_DEFINITION_TERMS):
        return "definition"
    if METRIC_PATTERN.search(text):
        return "metric"
    return "narrative"


def def_build_information_units(
    blocks: list[dict[str, Any]],
    sentences: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    source_sha256: str,
) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    contexts = def_heading_context(blocks)
    for sentence in sentences:
        unit_id = f"I{len(units) + 1:06d}"
        text = sentence["text"]
        key_value = KEY_VALUE_PATTERN.match(text.strip())
        units.append(
            {
                "information_id": unit_id,
                "kind": def_information_kind(text),
                "heading_path": contexts.get(sentence["block_id"], []),
                "subject": key_value.group(1).strip() if key_value else "",
                "value": key_value.group(2).strip() if key_value else text,
                "metrics": METRIC_PATTERN.findall(text),
                "source_block_id": sentence["block_id"],
                "source_sentence_id": sentence["sentence_id"],
                "source_lines": [sentence["start_line"], sentence["end_line"]],
                "source_sha256": source_sha256,
                "confidence": sentence["confidence"],
            }
        )
    for table in tables:
        headers = table["headers"]
        for row_number, row in enumerate(table["rows"], start=1):
            unit_id = f"I{len(units) + 1:06d}"
            record = {
                headers[index] if index < len(headers) and headers[index] else f"column_{index + 1}": value
                for index, value in enumerate(row)
            }
            units.append(
                {
                    "information_id": unit_id,
                    "kind": "table_record",
                    "heading_path": contexts.get(table["block_id"], []),
                    "subject": headers[0] if headers else "",
                    "value": record,
                    "metrics": [metric for value in row for metric in METRIC_PATTERN.findall(value)],
                    "source_block_id": table["block_id"],
                    "source_table_id": table["table_id"],
                    "source_row": row_number,
                    "source_lines": [table["start_line"], table["end_line"]],
                    "source_sha256": source_sha256,
                    "confidence": table["confidence"],
                }
            )
    return units


def def_reconstruction_signature(
    blocks: list[dict[str, Any]],
    sentences: list[dict[str, Any]],
    tables: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "headings": [
            [block["metadata"].get("depth"), def_normalize_semantic_text(block["metadata"].get("text", ""))]
            for block in blocks
            if block["type"] == "heading"
        ],
        "block_sequence": [block["type"] for block in blocks if block["type"] != "blank"],
        "sentences": [sentence["semantic_sha256"] for sentence in sentences],
        "tables": [
            [table["expected_columns"], table["row_count"], table["matrix_sha256"]]
            for table in tables
        ],
        "code": [
            def_sha256_text(def_normalize_semantic_text(block["text"]))
            for block in blocks
            if block["type"] == "code"
        ],
    }


def def_analysis_gate(findings: list[dict[str, Any]]) -> tuple[str, float]:
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    gate = "FAIL" if errors else ("REVIEW" if warnings else "PASS")
    confidence = max(0.0, 1.0 - errors * 0.25 - warnings * 0.04)
    return gate, round(confidence, 3)


def def_analyze_markdown_text(text: str, source_path: str = "") -> dict[str, Any]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    source_sha256 = def_sha256_text(normalized)
    blocks, tables, findings = def_classify_blocks(lines)
    sentences, sentence_findings = def_build_sentences(blocks)
    findings.extend(sentence_findings)
    findings.sort(key=lambda item: (item["start_line"], item["code"], item["severity"]))
    information_units = def_build_information_units(blocks, sentences, tables, source_sha256)
    gate, confidence = def_analysis_gate(findings)
    return {
        "schema_version": RECONSTRUCTION_SCHEMA_VERSION,
        "source_path": source_path,
        "source_sha256": source_sha256,
        "gate": gate,
        "confidence": confidence,
        "summary": {
            "lines": len(lines),
            "blocks": len(blocks),
            "headings": sum(block["type"] == "heading" for block in blocks),
            "sentences": len(sentences),
            "tables": len(tables),
            "information_units": len(information_units),
            "errors": sum(item["severity"] == "error" for item in findings),
            "warnings": sum(item["severity"] == "warning" for item in findings),
            "info": sum(item["severity"] == "info" for item in findings),
        },
        "blocks": blocks,
        "sentences": sentences,
        "tables": tables,
        "information_units": information_units,
        "findings": findings,
        "signature": def_reconstruction_signature(blocks, sentences, tables),
    }


def def_analyze_markdown_file(path: Path) -> dict[str, Any]:
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    return def_analyze_markdown_text(text, str(path))


def def_compare_reconstruction(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_signature = before["signature"]
    after_signature = after["signature"]
    keys = ["headings", "block_sequence", "sentences", "tables", "code"]
    differences = [key for key in keys if before_signature.get(key) != after_signature.get(key)]
    return {
        "passed": not differences,
        "differences": differences,
        "before_gate": before["gate"],
        "after_gate": after["gate"],
        "before_confidence": before["confidence"],
        "after_confidence": after["confidence"],
    }


def def_safe_repair_markdown_text(text: str) -> tuple[str, dict[str, Any]]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    frontmatter = def_find_frontmatter_range(lines)
    fences = def_find_fence_ranges(lines)
    protected: set[int] = set()
    if frontmatter:
        protected.update(range(frontmatter[0], frontmatter[1] + 1))
    for start, end, _closed in fences:
        protected.update(range(start, end + 1))
    output: list[str] = []
    inserted_boundaries = 0
    expanded_delimiters = 0
    for index, line in enumerate(lines):
        if index not in protected and def_count_unescaped_pipes(line) >= 1:
            cells = def_split_pipe_row(line)
            if def_is_delimiter_like_cells(cells) and not def_is_delimiter_cells(cells):
                normalized_cells = []
                for cell in cells:
                    compact = cell.replace(" ", "")
                    left = compact.startswith(":")
                    right = compact.endswith(":")
                    normalized_cells.append(f"{':' if left else ''}---{':' if right else ''}")
                leading = line.strip().startswith("|")
                trailing = line.rstrip().endswith("|")
                line = f"{'| ' if leading else ''}{' | '.join(normalized_cells)}{' |' if trailing else ''}"
                expanded_delimiters += 1
        is_heading = index not in protected and bool(HEADING_PATTERN.match(line))
        if is_heading and output and output[-1].strip():
            output.append("")
            inserted_boundaries += 1
        output.append(line)
        if is_heading and index + 1 < len(lines) and lines[index + 1].strip():
            output.append("")
            inserted_boundaries += 1
    repaired = "\n".join(output).rstrip("\n") + "\n"
    return repaired, {
        "inserted_boundaries": inserted_boundaries,
        "expanded_delimiters": expanded_delimiters,
        "merge_operations": 0,
        "fabricated_cells": 0,
        "changed": repaired != normalized,
        "policy": "split-first-merge-never",
    }


def def_write_structure_sidecar(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding=DEFAULT_ENCODING)
    temporary.replace(path)


def def_write_reconstruction_indexes(root: Path) -> dict[str, str]:
    sidecars = sorted(root.rglob("*.structure.json"), key=lambda path: str(path).casefold())
    if not sidecars:
        return {}
    sentence_path = root / "Sentence_SSOT.csv"
    information_path = root / "Information_SSOT.csv"
    table_path = root / "Table_SSOT.csv"
    with sentence_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_path", "sentence_id", "block_id", "start_line", "end_line", "text", "confidence", "semantic_sha256"],
        )
        writer.writeheader()
        for sidecar in sidecars:
            payload = json.loads(sidecar.read_text(encoding=DEFAULT_ENCODING))
            analysis = payload["analysis"]
            for sentence in analysis["sentences"]:
                writer.writerow({"source_path": payload["source_path"], **{key: sentence.get(key, "") for key in writer.fieldnames if key != "source_path"}})
    with information_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_path", "information_id", "kind", "heading_path", "subject", "value", "metrics", "source_block_id", "source_lines", "confidence", "source_sha256"],
        )
        writer.writeheader()
        for sidecar in sidecars:
            payload = json.loads(sidecar.read_text(encoding=DEFAULT_ENCODING))
            for unit in payload["analysis"]["information_units"]:
                row = {"source_path": payload["source_path"]}
                for key in writer.fieldnames:
                    if key == "source_path":
                        continue
                    value = unit.get(key, "")
                    row[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                writer.writerow(row)
    with table_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_path", "table_id", "start_line", "end_line", "expected_columns", "row_count", "headers", "confidence", "matrix_sha256"],
        )
        writer.writeheader()
        for sidecar in sidecars:
            payload = json.loads(sidecar.read_text(encoding=DEFAULT_ENCODING))
            for table in payload["analysis"]["tables"]:
                row = {"source_path": payload["source_path"]}
                for key in writer.fieldnames:
                    if key == "source_path":
                        continue
                    value = table.get(key, "")
                    row[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                writer.writerow(row)
    return {
        "sentence_ssot": str(sentence_path),
        "information_ssot": str(information_path),
        "table_ssot": str(table_path),
    }
