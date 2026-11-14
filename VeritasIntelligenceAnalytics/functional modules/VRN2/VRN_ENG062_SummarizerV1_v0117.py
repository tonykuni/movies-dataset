#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 v0117: the four verbatim excerpts no longer start with a running header, a title line or a section heading.

Workstation output 2026-10-28 (52 reports): a point could begin with the page banner
("Alchip Technologies Ltd | Asia Pacific"), with the report title repeated, or with a section
heading ("Dual growth engines moving into focus") glued to the first sentence of the block.
The excerpt was still an exact span of the source, so every verbatim gate passed, but the
reader saw layout text in front of the sentence.

v0117 keeps v0116's selection (strict pass + ladder) and only moves the left edge of a chosen
span past such leading lines; the remaining text must still be eligible, and the evidence
(raw_span · quote · quote_sha256) is rewritten for the shorter span so validate_summary and the
independent verifier check the new span exactly as before. Financial metric extraction stays
v0114; v0115 and v0116 are not modified.
"""
from __future__ import annotations

VERSION = "v0117"
PRIOR_NAME = "VRN_ENG062_SummarizerV1_v0116.py"

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("vrn_eng062_prior_for_v0117", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


compact = PRIOR.compact
eligible = PRIOR.eligible
validate_summary = PRIOR.validate_summary

# ===== leading-line rules =====
_PIPE_HEADER = re.compile(r"^[^\n|]{1,80}\|\s*[^\n|]{1,60}$")                       # "Company | Asia Pacific" page banner
_BANNER = re.compile(r"(?i)^(?:equity research|company report|research report|morning note|company update|sector update|flash note|"
                     r"initiation of coverage|rating change|earnings review|quick take|first take|第一時間|個股報告|訪談速報|晨會報告)\b[^\n]{0,80}$")
_SECTION_WORDS = re.compile(r"(?i)^(?:key takeaways?|investment (?:summary|thesis|highlights?)|what'?s new|our view|our take|bottom line|"
                            r"valuation(?: and risks?)?|risks?(?: to our (?:view|rating))?|catalysts?|outlook|summary|highlights?|conclusion|"
                            r"投資建議|投資重點|投資評等|結論|重點摘要|營運概況|評價與目標價|風險(?:因素)?)\s*[:：]?$")
_CONTINUE_END = {"a", "an", "the", "of", "to", "and", "or", "in", "on", "for", "with", "by", "at", "from", "as", "is", "are", "was", "were",
                 "be", "our", "its", "their", "his", "her", "this", "that", "these", "those", "which", "but", "than", "into", "over", "under",
                 "per", "vs", "vs.", "we", "it", "has", "have", "had", "will", "would", "should", "could", "may", "might", "not", "also", "more"}
_NO_HEADING_START = re.compile(r"(?i)^(?:from|in|on|with|as|after|before|since|while|although|because|during|despite|following|given|"
                               r"if|when|where|whereas|though|unless|until|per|among|between|through|under|over|at|by|for|to|of)\b")
MAX_LEADING_LINES = 3


def _heading_like(line, nxt, title_keys):
    """A short line without terminal punctuation that a new sentence follows, or a banner / title / section-name line."""
    stripped = line.strip()
    if not stripped:
        return False
    key = compact(stripped)
    if key in title_keys or any(len(key) >= 12 and key in t for t in title_keys):          # the line is (part of) the title
        return True
    if _PIPE_HEADER.match(stripped) or _BANNER.match(stripped) or _SECTION_WORDS.match(stripped):
        return True
    if re.search(r"[。！？.!?,，、;；:：]$", stripped):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z’'’-]*", stripped)
    cjk = len(re.findall(r"[㐀-鿿]", stripped))
    if cjk:
        # 中文標題:短(≤ 10 字)、沒有逗頓號(有 = 換行折句)、沒有數字、下一行不是以標點接續
        return cjk <= 10 and len(stripped) <= 16 and bool(nxt) and not re.search(r"[\d，、,：:]", stripped) and not re.match(r"[、，。,]", nxt.lstrip()[:1] or "x")
    if not words or len(words) > 8 or len(stripped) > 60 or re.search(r"\d", stripped):
        return False
    if _NO_HEADING_START.match(stripped) or words[-1].lower() in _CONTINUE_END:
        return False
    if not nxt or not re.match(r"[A-Z㐀-鿿“\"(]", nxt.lstrip()[:1] or "x"):
        return False
    return True


def _title_prefix_end(line, title_lines):
    """When a line starts with a whole title line and the sentence continues on the same line, return the raw index just past the title text; else -1."""
    for title in title_lines:
        target = compact(title)
        if len(target) < 12:
            continue
        got, index = "", 0
        while index < len(line) and len(got) < len(target):
            if not line[index].isspace():
                got += line[index].casefold()
            index += 1
        if got == target and index < len(line) and (line[index].isspace() or re.match(r"[A-Z\u3400-\u9fff“\"(]", line[index])):
            return index
    return -1


def trim_leading(raw, left, right, title_keys, title_lines=()):
    """Move `left` past up to MAX_LEADING_LINES heading-like lines (or a title glued to the first line); the result is still raw[left:right]."""
    for _ in range(MAX_LEADING_LINES):
        segment = raw[left:right]
        cut = segment.find("\n")
        line = segment if cut < 0 else segment[:cut]
        rest = "" if cut < 0 else segment[cut + 1:]
        nxt = rest.split("\n", 1)[0]
        prefix = _title_prefix_end(line, title_lines)
        if prefix > 0:
            candidate = left + prefix
        elif cut > 0 and _heading_like(line, nxt, title_keys):
            candidate = left + cut + 1
        else:
            return left
        while candidate < right and raw[candidate].isspace():
            candidate += 1
        if candidate >= right or not eligible(raw[candidate:right]):
            return left
        left = candidate
    return left


def _title_keys(document):
    keys, lines = set(), []
    for text in (document.get("title_original") or "", document.get("title") or ""):
        if text:
            keys.add(compact(text))
            lines.append(str(text).strip())
            for line in str(text).splitlines():
                if len(line.strip()) >= 6:
                    keys.add(compact(line))
                    lines.append(line.strip())
    return {k for k in keys if k}, lines


def polish_points(result, document):
    blocks = {b["id"]: b for b in (document.get("blocks") or [])}
    merged = {b["id"]: b for b in PRIOR.PRIOR._merge_lines(document.get("blocks") or [])}
    title_keys, title_lines = _title_keys(document)
    changed = 0
    for point in result.get("points") or []:
        text = point.get("text")
        evidence = (point.get("evidence") or [None])[0]
        if not text or not isinstance(evidence, dict) or not evidence.get("raw_span"):
            continue
        block = blocks.get(evidence.get("block_id")) or merged.get(evidence.get("block_id"))
        if block is None:
            continue
        raw = str(block.get("text") or "")
        left, right = evidence["raw_span"]
        if raw[left:right] != text:
            continue
        new_left = trim_leading(raw, left, right, title_keys, title_lines)
        if new_left == left:
            continue
        quote = raw[new_left:right]
        point["text"] = quote
        evidence["raw_span"] = [new_left, right]
        evidence["quote"] = quote
        evidence["quote_sha256"] = hashlib.sha256(quote.encode("utf-8")).hexdigest()
        evidence["leading_trimmed"] = raw[left:new_left].strip()
        changed += 1
    result["version"] = VERSION
    result.setdefault("nlp", {})["leading_trimmed"] = changed
    return result


def summarize_document(document, catalog=None):
    result = PRIOR.summarize_document(document, catalog)
    polish_points(result, document)
    blocks = list(document.get("blocks") or [])
    ids = {b["id"] for b in blocks}
    for block in PRIOR.PRIOR._merge_lines(document.get("blocks") or []):
        if block["id"] not in ids:
            blocks.append(block)
    validate_summary(result, blocks)
    return result


def summarize_pdf(path, catalog=None, company_name_zh=None):
    document = PRIOR.PRIOR.pdf_document(path)
    document["company_name_zh"] = company_name_zh
    result = summarize_document(document, catalog)
    result["reader_crosscheck"] = document["reader_crosscheck"]
    result["reader_warnings"] = document["reader_warnings"]
    result["source_pdf_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return result


def selftest():
    PRIOR.main(["--selftest"])
    title = "Read-across from AWS re:Invent"
    b1 = "Alchip Technologies Ltd | Asia Pacific\nTrainium3's revenue contribution to the company should stay intact, while it should be able to support both UALink and NVLink for the next generation as customers ramp."
    b2 = "Dual growth engines moving into focus  \nWe are turning more constructive on the company and expect revenue growth to accelerate through 2026 as new customers ramp."
    b3 = "Read-across from AWS re:Invent Key risks include slower demand, pricing pressure and customer concentration in the second half of the year."
    b4 = "From our Summit \nFeedback, the company seeks a win-win situation with the major customer at 2nm, meaning revenue and profits can grow with demand."
    blocks = [{"id": "p1-b%d" % i, "text": t, "page": 1, "source": "t.pdf", "bbox": [0, 10 * i, 10, 10 * i + 5]} for i, t in enumerate((b1, b2, b3, b4), 1)]
    document = {"filename": "t.pdf", "title_original": title, "blocks": blocks}
    result = summarize_document(document)
    texts = [p["text"] for p in result["points"]]
    assert all(texts), texts
    raw = {b["id"]: b["text"] for b in blocks}
    assert any(t.startswith("Trainium3's revenue contribution") for t in texts), texts              # page banner removed
    assert any(t.startswith("We are turning more constructive") for t in texts), texts              # section heading removed
    assert any(t.startswith("Key risks include") for t in texts), texts                             # title line removed
    assert any(t.startswith("From our Summit") for t in texts), texts                               # preposition start kept
    assert not any("| Asia Pacific" in t or t.startswith("Dual growth") or t.startswith("Read-across") for t in texts), texts
    for p in result["points"]:
        ev = p["evidence"][0]
        assert raw[ev["block_id"]][ev["raw_span"][0]:ev["raw_span"][1]] == p["text"] == ev["quote"]
        assert ev["quote_sha256"] == hashlib.sha256(p["text"].encode("utf-8")).hexdigest()
    assert result["version"] == VERSION and result["nlp"]["leading_trimmed"] == 3, result["nlp"]
    assert summarize_document(document) == result                                                   # deterministic
    validate_summary(result, blocks)
    tampered = json.loads(json.dumps(result)); tampered["points"][0]["text"] += "x"
    try:
        validate_summary(tampered, blocks)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered text accepted")
    # A wrapped first word ("Management \nalso …") is not a heading and stays.
    b5 = "Management \nalso highlighted data center and automotive segments as the main growth drivers, with new product dollar content ramping faster than expected."
    doc5 = {"filename": "m.pdf", "title_original": "Monthly update", "blocks": [{"id": "p1-b1", "text": b5, "page": 1, "source": "m.pdf", "bbox": [0, 0, 10, 5]}] + blocks[1:3]}
    t5 = [p["text"] for p in summarize_document(doc5)["points"] if p["text"]]
    assert any(t.startswith("Management \nalso highlighted") for t in t5), t5
    # Chinese: a short heading line before the sentence is removed; a wrapped clause is not.
    zh = ("營運概況\n前三季累計營收10.2 億元，成長主要來自於授權金，前三季累計每股盈餘為負七點六八元，公司表示下半年需求回溫。\n"
          "對於中長期發展，公司仍維\n持每年營收成長30%的目標，看好RISC-V 架構在未來的發展，我們認為未來客戶與案件規模將持續逐步成長。")
    doc2 = {"filename": "z.pdf", "title_original": "晶心科更新", "blocks": [{"id": "p1-b1", "text": zh, "page": 1, "source": "z.pdf", "bbox": [0, 0, 10, 10]}]}
    t2 = [p["text"] for p in summarize_document(doc2)["points"] if p["text"]]
    assert t2 and not any(t.startswith("營運概況") for t in t2) and any(t.startswith("前三季累計營收") for t in t2), t2
    assert any(t.startswith("對於中長期發展，公司仍維\n持") for t in t2), t2
    empty = summarize_document({"filename": "e.pdf", "title_original": None, "blocks": [{"id": "p1-b1", "text": "12 34 56", "page": 1, "source": "e.pdf"}]})
    assert all(p["status"] == "MISSING" for p in empty["points"])
    print("[PASS] v0117: banner / title / section-heading lines trimmed from the span start; wrapped words and preposition starts kept; spans stay exact; tamper rejected")
    return 0


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    PRIOR.PRIOR.summarize_document = summarize_document
    PRIOR.PRIOR.summarize_pdf = summarize_pdf
    PRIOR.summarize_document = summarize_document
    PRIOR.summarize_pdf = summarize_pdf
    return PRIOR.PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
