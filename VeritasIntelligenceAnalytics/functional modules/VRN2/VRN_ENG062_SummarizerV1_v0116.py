#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0116: four verbatim source excerpts for every report with a text layer.

v0115 selected only strict narrative sentences (page ≤ 3 · ≥ 24 CJK / ≥ 9 English words ·
topic words · numeric ratio). Short notes, bullet-style updates and English reports with
unusual spacing therefore produced fewer than four points, and the closeout counted every
missing point as a FAIL (操作員 2026-10-22:GFHK Apple update POINT_1~4 · 欣銓 POINT_3~4 ·
3014TT · 華南 2606).

v0116 keeps v0115's strict pass first and then fills the remaining slots with a graded
ladder — every candidate is still an exact character span of one source block with page,
raw span, bbox and quote hash, so the verbatim gate and the independent verifier check it
the same way. The ladder level is recorded in the evidence ("selection"). Image-only pages
remain MISSING (OCR pending). Financial metric extraction stays v0114; nothing in v0115 is
modified.
"""
from __future__ import annotations

# ===== 1. Parameters =====
VERSION = "v0116"
PRIOR_NAME = "VRN_ENG062_SummarizerV1_v0115.py"
LADDER = (
    # name · pages · minimum CJK chars · minimum English words · minimum total chars · topic required · similarity ceiling
    ("strict", 3, 24, 9, 0, True, 0.78),
    ("relaxed", 6, 12, 5, 14, False, 0.85),
    ("line", 6, 8, 4, 12, False, 0.9),
    ("page", 8, 8, 4, 12, False, 0.9),
)
MIN_SQUASHED = 8          # the independent verifier marks shorter points 太短

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

# [VIA:ACCEL-BRIDGE:v0111] The prior's executable bridge loads Celeritas.
_spec = importlib.util.spec_from_file_location("vrn_summary_prior_for_v0116", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _net():
    return PRIOR._net()


NOISE = PRIOR.NOISE
compact = PRIOR.compact
source_spans = PRIOR.source_spans
similarity = PRIOR.similarity
original_title = PRIOR.original_title
validate_summary = PRIOR.validate_summary
_LINE_NOISE = re.compile(r"(?i)^\s*(?:page\s*\d+|\d+\s*/\s*\d+|第\s*\d+\s*頁|source\s*:|資料來源|figure\s*\d|table\s*\d|圖\s*\d|表\s*\d|exhibit\s*\d)")
_URL_MAIL = re.compile(r"(?i)https?://|www\.|@")
_DECOR = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f•·‧●○■□▪▫◆◇◼◻▲△►▶➢➤➔→✓✔✗※◎★☆-–—‑·•*·‣⁃⦁ \t\u3000\xa0"   # bullets / controls / dashes at a span edge are layout, not text


# ===== 2. Graded eligibility (strict level = v0115 unchanged) =====
def eligible_at(text, level):
    name, _pages, min_cjk, min_words, min_chars, _topic, _sim = level
    if name == "strict":
        return PRIOR.eligible(text)
    if not text or len(text) > PRIOR.MAX_POINT_CHARS or NOISE.search(text) or _URL_MAIL.search(text) or _LINE_NOISE.match(text):
        return False
    squashed = re.sub(r"\s+", "", text)
    if len(squashed) < max(min_chars, MIN_SQUASHED):
        return False
    chinese = len(re.findall(r"[㐀-鿿]", text))
    words = re.findall(r"[A-Za-z][A-Za-z’'-]+", text)
    letters = len(re.findall(r"[A-Za-z]", text))
    if chinese < min_cjk and len(words) < min_words and not (chinese < 6 and letters >= 24):
        return False
    digits = len(re.findall(r"\d", text))
    if digits / max(1, len(squashed)) > 0.4:
        return False
    tokens = text.split()
    numeric = sum(bool(re.fullmatch(r"[-+()\d,.%xX]+|ppts?", token)) for token in tokens)
    if len(tokens) >= 6 and numeric / len(tokens) >= 0.6:
        return False
    if re.fullmatch(r"[\W\d_]+", text):
        return False
    return True


def _topic_tags(quote, words_by_topic):
    return {topic: sum(bool(re.search(PRIOR.alias_pattern([word]), quote, re.I)) for word in aliases) for topic, aliases in words_by_topic.items()}


def _topic_words(catalog):
    words_by_topic = {name: list(words) for name, words in PRIOR.TOPICS.items()}
    if catalog:
        for topic, fields in {"growth": ("revenue", "net_profit"), "margin": ("gross_margin", "operating_margin", "net_margin")}.items():
            for entry in catalog.get("financial_lexicon", []):
                if entry.get("std") in fields:
                    words_by_topic[topic].extend(entry.get("zh", []) + entry.get("en", []))
            for field in fields:
                words_by_topic[topic].extend(catalog.get("central_synonyms", {}).get("FINANCIAL_FIELD_" + field.upper(), []))
    words_by_topic["growth"].extend(("sales", "earnings", "ramp", "shipment"))
    words_by_topic["moat"].extend(("customer", "qualified", "capacity"))
    return words_by_topic


def _trim_edges(raw, left, right):
    """Move the span edges past bullets, control glyphs and whitespace; the span stays an exact substring."""
    while left < right and raw[left] in _DECOR:
        left += 1
    while right > left and (raw[right - 1].isspace() or raw[right - 1] in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x7f"):
        right -= 1
    return left, right


def _spans_for(level, raw):
    """strict / relaxed: sentence spans · line: one source line each · page: lines of the page text."""
    if level[0] in ("strict", "relaxed"):
        for left, right, _quote in source_spans(raw):
            left, right = _trim_edges(raw, left, right)
            if right > left:
                yield left, right, raw[left:right]
        return
    position = 0
    for line in raw.split("\n"):
        left, right = position, position + len(line)
        position = right + 1
        left, right = _trim_edges(raw, left, right)
        if right > left:
            yield left, right, raw[left:right]


def ladder_candidates(blocks, catalog, level, seen):
    """Exact source spans eligible at one ladder level, excluding spans already seen (compact key)."""
    name, pages, _c, _w, _m, topic_required, _s = level
    words_by_topic = _topic_words(catalog)
    rows = []
    for block in blocks:
        role = block.get("role")
        page = int(block.get("page") or 1)
        is_page_text = str(block.get("id", "")).startswith("page-") or role == "table_context"   # whole-page text (v0114 pdf_document)
        if page > pages or role in ("disclosure", "contact"):
            continue
        if name == "page":
            if not is_page_text:
                continue
        elif is_page_text or role in ("table", "header"):
            continue
        raw = str(block.get("text") or "")
        for left, right, quote in _spans_for(level, raw):
            if not eligible_at(quote, level):
                continue
            key = compact(quote)
            if key in seen or len(key) < MIN_SQUASHED:
                continue
            tags = _topic_tags(quote, words_by_topic)
            if topic_required and not any(tags.values()):
                continue
            seen.add(key)
            complete = bool(re.search(r"[。！？.!?][\"”’')）]*$", quote))
            score = 2 * sum(tags.values()) + (10 if page == 1 else 0) + (3 if complete else 0) + bool(re.search(r"\d", quote)) + min(3, len(quote) / 80)
            proof = {"block_id": block["id"], "page": page, "source": block.get("source", ""), "quote": quote, "raw_span": [left, right],
                     "bbox": block.get("bbox"), "source_block_ids": block.get("source_block_ids", [block["id"]]), "reader": block.get("reader", "PDF_TEXT"),
                     "quote_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(), "selection": name}
            rows.append({"text": quote, "tags": tags, "score": score, "evidence": proof})
    return sorted(rows, key=lambda row: (-row["score"], row["evidence"]["page"], row["evidence"]["block_id"], row["evidence"]["raw_span"][0], row["text"]))


def fill_four(rows, chosen, ceiling):
    """Deterministic MMR fill of the remaining slots (same preference order as v0115)."""
    for preferred in ("valuation", "growth", "moat", "risk"):
        if len(chosen) >= 4:
            break
        pool = [row for row in rows if row not in chosen and max([similarity(row["text"], old["text"]) for old in chosen] or [0]) < ceiling]
        if not pool:
            continue
        pool.sort(key=lambda row: (-(row["score"] + (5 if row["tags"].get(preferred) else 0)), row["evidence"]["page"], row["evidence"]["block_id"], row["evidence"]["raw_span"][0], row["text"]))
        chosen.append(pool[0])
    return chosen


# ===== 3. Original API; strict pass first, ladder only for the empty slots =====
def summarize_document(document, catalog=None):
    catalog = catalog or PRIOR.load_catalog()
    result = PRIOR.summarize_document(document, catalog)          # v0115 strict selection (unchanged)
    points = result["points"]
    if all(point.get("text") for point in points):
        result["version"] = VERSION
        for point in points:
            point["evidence"][0].setdefault("selection", "strict")
        return result
    blocks = document.get("blocks") or ([{"id": "text-1", "page": 1, "text": document["text"], "source": "text"}] if document.get("text") else [])
    expanded = list(blocks)
    ids = {block["id"] for block in expanded}
    for block in PRIOR._merge_lines(blocks):
        if block["id"] not in ids:
            expanded.append(block)
            ids.add(block["id"])
    title_key = compact(document.get("title_original") or "")
    chosen = [{"text": point["text"], "tags": {point["topic"]: 1}, "score": 0, "evidence": point["evidence"][0]} for point in points if point.get("text")]
    for row in chosen:
        row["evidence"].setdefault("selection", "strict")
    seen = {compact(row["text"]) for row in chosen}
    if title_key:
        seen.add(title_key)
    levels_used = []
    for level in LADDER[1:]:
        if len(chosen) >= 4:
            break
        rows = ladder_candidates(expanded, catalog, level, seen)
        before = len(chosen)
        chosen = fill_four(rows, chosen, level[6])
        if len(chosen) > before:
            levels_used.append("%s+%d" % (level[0], len(chosen) - before))
    new_points = []
    for index in range(4):
        row = chosen[index] if index < len(chosen) else None
        if row is None:
            new_points.append({"index": index + 1, "topic": "unavailable", "text": None, "status": "MISSING", "verbatim": False, "source_language": None, "evidence": []})
            continue
        text = row["text"]
        new_points.append({"index": index + 1, "topic": max(row["tags"], key=row["tags"].get) if row["tags"] else "narrative", "text": text,
                           "status": "EXTRACTIVE", "verbatim": True,
                           "source_language": "en" if len(re.findall(r"[A-Za-z]", text)) > len(re.findall(r"[㐀-鿿]", text)) else "zh-TW",
                           "evidence": [row["evidence"]]})
    result["points"] = new_points
    result["version"] = VERSION
    result["missing"] = [name for name in result.get("missing", []) if not name.startswith("point_")]
    result["missing"] += [f"point_{point['index']}" for point in new_points if not point["text"]]
    result["nlp"].update(method="deterministic_source_spans_mmr+ladder", ladder=levels_used)
    result["status"] = "REVIEW" if result.get("issues") or result["missing"] else "EXTRACTED"
    validate_summary(result, expanded)
    return result


def summarize_pdf(path, catalog=None, company_name_zh=None):
    document = PRIOR.pdf_document(path)
    document["company_name_zh"] = company_name_zh
    result = summarize_document(document, catalog)
    result["reader_crosscheck"] = document["reader_crosscheck"]
    result["reader_warnings"] = document["reader_warnings"]
    result["source_pdf_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return result


def selftest():
    PRIOR.main(["--selftest"])
    strict = ("Our valuation reflects stronger demand and improving product mix, with the target price based on forward earnings. "
              "Revenue growth is supported by new customer orders and rising shipments through 2026. "
              "The company holds a qualified position with major customers and is expanding capacity. "
              "Key risks include slower demand and pricing pressure in the second half.")
    document = {"filename": "t.pdf", "title_original": "Original title", "blocks": [{"id": "p1-b1", "text": strict, "page": 1, "source": "t.pdf"}]}
    full = summarize_document(document)
    assert all(point["text"] for point in full["points"]) and full["version"] == VERSION
    assert all(point["evidence"][0]["selection"] == "strict" for point in full["points"])
    # Short note: one strict sentence only; the ladder must fill the rest with exact spans.
    note = ("公司公告第三季營收創新高。\n\x00 新產品線出貨量持續成長帶動毛利率改善\n• 法人預估全年獲利優於去年\n資料來源:公司\n"
            "Management guided a mid-teens increase in shipments for next year.")
    doc2 = {"filename": "n.pdf", "title_original": "欣銓更新", "blocks": [{"id": "p1-b1", "text": note, "page": 1, "source": "n.pdf", "bbox": [0, 0, 10, 10]}]}
    filled = summarize_document(doc2)
    texts = [point["text"] for point in filled["points"]]
    assert all(texts), texts
    assert all(text in note for text in texts) and "資料來源" not in "".join(texts)
    assert not any(text[0] in _DECOR for text in texts), texts
    assert len(set(map(compact, texts))) == 4
    assert {point["evidence"][0]["selection"] for point in filled["points"]} - {"strict"}, "ladder level not recorded"
    assert summarize_document(doc2) == filled
    validate_summary(filled, doc2["blocks"])
    # Page-text last resort: narrative lines inside a whole-page block.
    page = "Apple update\n" + "\n".join("Line %d: iPhone demand remains resilient while services keep compounding in region %d." % (i, i) for i in range(1, 6))
    doc3 = {"filename": "g.pdf", "title_original": "Apple update", "blocks": [{"id": "page-1", "text": page, "page": 1, "source": "g.pdf", "role": "header", "bbox": [0, 0, 1, 1]}]}
    paged = summarize_document(doc3)
    assert all(point["text"] and point["text"] in page for point in paged["points"]) and all(point["evidence"][0]["selection"] == "page" for point in paged["points"])
    # No text at all stays MISSING.
    empty = summarize_document({"filename": "e.pdf", "title_original": None, "blocks": [{"id": "p1-b1", "text": "12 34 56", "page": 1, "source": "e.pdf"}]})
    assert all(point["status"] == "MISSING" for point in empty["points"])
    tampered = json.loads(json.dumps(filled))
    tampered["points"][1]["text"] += "x"
    try:
        validate_summary(tampered, doc2["blocks"])
    except ValueError:
        pass
    else:
        raise AssertionError("tampered text accepted")
    print("[PASS] v0116: strict pass unchanged; ladder fills four exact spans for short notes and page text; no-text stays MISSING; tamper rejected")
    return 0


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    PRIOR.summarize_document = summarize_document
    PRIOR.summarize_pdf = summarize_pdf
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
