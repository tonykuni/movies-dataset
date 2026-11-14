#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0115: four deterministic, verbatim source excerpts; no generated prose.

Financial metric extraction remains v0114. Every displayed point carries its
original block, page, raw character span and quote hash, including OCR labels.
"""
from __future__ import annotations

# ===== 1. Parameters =====
VERSION = "v0115"
PRIOR_NAME = "VRN_ENG062_SummarizerV1_v0114.py"
MAX_POINT_CHARS = 850
FRONT_PAGES = 3
MIN_CJK_CHARS = 24
MIN_ENGLISH_WORDS = 9

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

# [VIA:ACCEL-BRIDGE:v0111] The prior's executable bridge loads Celeritas.
_spec = importlib.util.spec_from_file_location("vrn_summary_prior_for_v0115", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_ORIGINAL_SUMMARIZE = PRIOR.summarize_document


def __getattr__(name):
    return getattr(PRIOR, name)


def _net():
    return PRIOR._net()


NOISE = re.compile(
    r"(?i)disclaimer|important disclosures|analyst certification|FINRA|conflict of interest|"
    r"not an offer to|for further information|research analysts responsible|"
    r"本公司不負|法律責任|純屬研究性質|審慎考量投資風險|本刊所刊載|僅做為參考|"
    r"投資人應自行|投資人需自行|著作權|免責聲明|資料來源\s*[:：]|@|\bLHS\b|\bRHS\b|[（(][左右]軸[)）]"
)
TOPICS = dict(PRIOR.TOPIC_WORDS, valuation=["valuation", "target price", "price target", "P/E", "EPS", "目標價", "評價", "本益比", "每股盈餘"])


# ===== 2. Preserve exact character spans =====
def compact(text):
    return re.sub(r"\s+", "", str(text)).casefold()


def source_spans(text):
    """Sentence boundaries keep punctuation, spelling and internal line breaks."""
    start = 0
    boundaries = list(re.finditer(r"(?<=[。！？!?])|(?<=\.)\s+(?=[A-Z\u3400-\u9fff])", text))
    for end in [match.end() for match in boundaries] + [len(text)]:
        left, right = start, end
        while left < right and text[left].isspace():
            left += 1
        heading = re.match(r"(?:標題|投資建議|投資重點|Investment summary|Investment thesis|CITI[’']S TAKE)[ \t]*\n", text[left:right], re.I)
        if heading:
            left += heading.end()
        while right > left and text[right - 1].isspace():
            right -= 1
        if right > left:
            yield left, right, text[left:right]
        start = end


def eligible(text):
    if not text or len(text) > MAX_POINT_CHARS or NOISE.search(text):
        return False
    chinese = len(re.findall(r"[\u3400-\u9fff]", text))
    words = re.findall(r"[A-Za-z][A-Za-z’'-]+", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    short_lines = sum(len(line.split()) <= 4 and len(line) < 45 for line in lines)
    if len(lines) >= 6 and short_lines / len(lines) >= 0.75:
        return False
    if re.match(r"(?i)^Category\s*:", text) or re.match(r"^(?:月稅前|從明年起|其中|以及|並且|的成長)", text):
        return False
    if re.match(r"^.{0,65}\(\d{4}\.(?:TW|TWO)\)", text):
        return False
    financial_labels = re.findall(r"(?im)^\s*(?:Year to|Net Profit|Diluted EPS|EPS growth|P/E|P/B|ROE|Yield|Target price|Expected (?:share price|dividend|total return))\b", text)
    if len(financial_labels) >= 3:
        return False
    minimum_chinese = 16 if re.search(r"風險|risks?", text, re.I) else MIN_CJK_CHARS
    if chinese < minimum_chinese and len(words) < MIN_ENGLISH_WORDS:
        return False
    if chinese < 6 and not re.search(r"\b(?:is|are|was|were|will|would|should|could|have|has|expect\w*|forecast\w*|believe\w*|reflect\w*|support\w*|driv\w*|risk\w*|lift\w*|rais\w*|cut\w*|benefit\w*|grow\w*|improv\w*|remain\w*|command\w*|see|sees|reiterate\w*)\b", text, re.I):
        return False
    tokens = text.split()
    numeric = sum(bool(re.fullmatch(r"[-+()\d,.%xX]+|ppts?", token)) for token in tokens)
    if len(tokens) >= 6 and numeric / len(tokens) >= 0.42:
        return False
    # Avoid selecting an isolated line of estimates or a truncated chart label.
    if len(re.findall(r"\d", text)) / max(1, len(text)) > 0.28:
        return False
    return True


def candidates(blocks, catalog=None):
    rows = []
    seen = set()
    words_by_topic = {name: list(words) for name, words in TOPICS.items()}
    if catalog:
        for topic, fields in {"growth": ("revenue", "net_profit"), "margin": ("gross_margin", "operating_margin", "net_margin")}.items():
            for entry in catalog.get("financial_lexicon", []):
                if entry.get("std") in fields:
                    words_by_topic[topic].extend(entry.get("zh", []) + entry.get("en", []))
            for field in fields:
                words_by_topic[topic].extend(catalog.get("central_synonyms", {}).get("FINANCIAL_FIELD_" + field.upper(), []))
    # Narrative terms supplement the existing financial-field aliases, without changing them.
    words_by_topic["growth"].extend(("sales", "earnings", "ramp", "shipment"))
    words_by_topic["moat"].extend(("customer", "qualified", "capacity"))
    for block in blocks:
        if int(block.get("page") or 1) > FRONT_PAGES or block.get("role") in ("disclosure", "header", "contact"):
            continue
        raw = str(block.get("text") or "")
        for left, right, quote in source_spans(raw):
            if not eligible(quote):
                continue
            key = compact(quote)
            if key in seen:
                continue
            seen.add(key)
            tags = {topic: sum(bool(re.search(PRIOR.alias_pattern([word]), quote, re.I)) for word in aliases) for topic, aliases in words_by_topic.items()}
            if not any(tags.values()):
                continue
            complete = bool(re.search(r"[。！？.!?][\"”’')）]*$", quote))
            score = 2 * sum(tags.values()) + (10 if block.get("page") == 1 else 0) + (3 if complete else 0) + bool(re.search(r"\d", quote)) + min(3, len(quote) / 80)
            proof = {"block_id": block["id"], "page": block.get("page", 1), "source": block.get("source", ""),
                     "quote": quote, "raw_span": [left, right], "bbox": block.get("bbox"),
                     "source_block_ids": block.get("source_block_ids", [block["id"]]),
                     "reader": block.get("reader", "PDF_TEXT"),
                     "quote_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest()}
            rows.append({"text": quote, "tags": tags, "score": score, "evidence": proof})
    return sorted(rows, key=lambda row: (-row["score"], row["evidence"]["page"], row["evidence"]["block_id"], row["evidence"]["raw_span"][0], row["text"]))


def shingles(text):
    text = compact(text)
    return {text[index:index + 5] for index in range(max(1, len(text) - 4))}


def similarity(left, right):
    a, b = shingles(left), shingles(right)
    return len(a & b) / max(1, min(len(a), len(b)))


def pick_four(rows):
    chosen = []
    # Soft semantic variety; a missing valuation/risk paragraph never creates an empty point.
    for preferred in ("valuation", "growth", "moat", "risk"):
        pool = [row for row in rows if row not in chosen and max([similarity(row["text"], old["text"]) for old in chosen] or [0]) < 0.78]
        if not pool:
            break
        pool.sort(key=lambda row: (-(row["score"] + (5 if row["tags"].get(preferred) else 0)), row["evidence"]["page"], row["evidence"]["block_id"], row["evidence"]["raw_span"][0], row["text"]))
        chosen.append(pool[0])
    return chosen


def original_title(document):
    existing = document.get("title_original")
    if existing:
        return existing
    possible = []
    for block in document.get("blocks", []):
        if block.get("page") != 1 or block.get("role") in ("table", "prose", "layout_fragment"):
            continue
        box = block.get("bbox") or [0, 9999, 0, 0]
        if box[1] > 360:
            continue
        for line in str(block.get("text") or "").splitlines():
            text = line.strip()
            if not 10 <= len(text) <= 180 or NOISE.search(text):
                continue
            if re.search(r"(?i)research|macquarie|goldman sachs|\b(?:Taiwan|Asia Pacific|Rating|Price|Target)\b|\d{4}\s*(?:TT|TW)|\d{4}[-/]\d{1,2}", text):
                continue
            if len(re.findall(r"[\u3400-\u9fff]", text)) < 6 and len(re.findall(r"[A-Za-z]+", text)) < 3:
                continue
            possible.append((float(block.get("max_font_size") or 0), -float(box[1]), text))
    return max(possible)[2] if possible else None


# ===== 3. Original API, original finance extraction, new quote-only points =====
def summarize_document(document, catalog=None):
    catalog = catalog or PRIOR.load_catalog()
    result = _ORIGINAL_SUMMARIZE(document, catalog)
    blocks = document.get("blocks") or ([{"id": "text-1", "page": 1, "text": document["text"], "source": "text"}] if document.get("text") else [])
    # Existing geometry-aware reconstruction is retained and its source IDs remain visible.
    expanded = list(blocks)
    ids = {block["id"] for block in expanded}
    for block in PRIOR._merge_lines(blocks):
        if block["id"] not in ids:
            expanded.append(block)
            ids.add(block["id"])
    rows = candidates(expanded, catalog)
    if document.get("title_original"):
        rows = [row for row in rows if compact(row["text"]) != compact(document["title_original"])]
    selected = pick_four(rows)
    points = []
    for index in range(4):
        row = selected[index] if index < len(selected) else None
        points.append({"index": index + 1, "topic": max(row["tags"], key=row["tags"].get) if row else "unavailable",
                       "text": row["text"] if row else None, "status": "EXTRACTIVE" if row else "MISSING", "verbatim": bool(row),
                       "source_language": ("en" if len(re.findall(r"[A-Za-z]", row["text"])) > len(re.findall(r"[\u3400-\u9fff]", row["text"])) else "zh-TW") if row else None,
                       "evidence": [row["evidence"]] if row else []})
    result.update(version=VERSION, points=points, summary_mode="SOURCE_VERBATIM", title=original_title(document), title_original=original_title(document))
    result["missing"] = [name for name in result.get("missing", []) if not name.startswith("point_") and name != "title_original"]
    result["missing"] += [f"point_{point['index']}" for point in points if not point["text"]]
    if not result["title_original"]:
        result["missing"].append("title_original")
    result["nlp"].update(method="deterministic_source_spans_mmr", candidate_sentences=len(rows), translation_status="ORIGINAL_LANGUAGE", llm_calls=0, micro_payload=[], payload_chars=0)
    result["status"] = "REVIEW" if result.get("issues") or result["missing"] else "EXTRACTED"
    validate_summary(result, expanded)
    return result


def validate_summary(result, blocks):
    by_id = {block["id"]: block for block in blocks}
    if len(result["points"]) != 4:
        raise ValueError("Four-point contract violated")
    for point in result["points"]:
        if not point.get("text"):
            continue
        proof = point["evidence"][0]
        raw = by_id[proof["block_id"]]["text"]
        left, right = proof["raw_span"]
        if raw[left:right] != point["text"] or proof["quote"] != point["text"]:
            raise ValueError("Point is not an exact source excerpt")
        if hashlib.sha256(point["text"].encode("utf-8")).hexdigest() != proof["quote_sha256"]:
            raise ValueError("Quote hash mismatch")
    return True


def summarize_pdf(path, catalog=None, company_name_zh=None):
    document = PRIOR.pdf_document(path)
    document["company_name_zh"] = company_name_zh
    result = summarize_document(document, catalog)
    result["reader_crosscheck"] = document["reader_crosscheck"]
    result["reader_warnings"] = document["reader_warnings"]
    result["source_pdf_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return result


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        raw = "Our valuation reflects stronger demand and improving product mix, with the target price based on forward earnings. Revenue growth is supported by new customer orders and rising shipments. Gross margin improves with a richer product mix and better utilization. Key risks include weaker demand, pricing pressure and slower customer investment."
        document = {"filename": "test.pdf", "title_original": "Original title", "blocks": [{"id": "p1-b1", "text": raw, "page": 1, "source": "test.pdf"}]}
        first = summarize_document(document)
        second = summarize_document(document)
        assert first == second
        assert all(point["text"] and point["text"] in raw for point in first["points"])
        first["points"][0]["text"] += " invented"
        try:
            validate_summary(first, document["blocks"])
        except ValueError:
            pass
        else:
            raise AssertionError("Fabricated text was accepted")
        print("[PASS] four original-language source excerpts, stable selection, fabricated point rejected")
        return 0
    # Existing CLI looks up its functions in its own namespace.
    PRIOR.summarize_document = summarize_document
    PRIOR.summarize_pdf = summarize_pdf
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
