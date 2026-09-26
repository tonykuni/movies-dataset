#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page 1: triple probe, then the registered text layer. Visual engines stay lazy."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
_MARKDOWN = None
_RAPID = None


def _prior():
    spec = importlib.util.spec_from_file_location("tab_report_v0103", HERE / "VRN_ENG110_TabReport_v0103.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _markdown():
    global _MARKDOWN
    if _MARKDOWN is None:
        try:
            import pymupdf4llm
            _MARKDOWN = pymupdf4llm
        except Exception:
            _MARKDOWN = False
    return _MARKDOWN


def _rapid():
    global _RAPID
    if _RAPID is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _RAPID = RapidOCR()
        except Exception:
            _RAPID = False
    return _RAPID


def _probe(page) -> tuple[bool, str, int, float, float]:
    import fitz
    raw = page.get_text("text") or ""
    chars = [ch for ch in raw if not ch.isspace()]
    count = len(chars)
    garbled = sum(1 for ch in chars if ch == "\ufffd" or unicodedata.category(ch) in {"Cc", "Co", "Cs"})
    ratio = (garbled / count) if count else 0.0
    rect = page.rect
    area = rect.width * rect.height
    covered = 0.0
    if area:
        for info in page.get_image_info(xrefs=False):
            box = fitz.Rect(info["bbox"]) & rect
            if not box.is_empty:
                covered += box.width * box.height
    coverage = min(1.0, covered / area) if area else 0.0
    if count < 50:
        return False, "few_chars", count, coverage, ratio
    if ratio > 0.08:
        return False, "garbled", count, coverage, ratio
    if coverage > 0.65 and count < 300:
        return False, "image_watermark", count, coverage, ratio
    return True, "native", count, coverage, ratio


def _native(doc, page) -> tuple[str, str]:
    markdown = _markdown()
    if markdown:
        try:
            text = (markdown.to_markdown(doc, pages=[page.number], write_images=False, show_progress=False) or "").strip()
            if text:
                return text, "PYMUPDF4LLM"
        except Exception:
            pass
    return (page.get_text("text", sort=True) or "").strip(), "ENG072_FITZ_LAYOUT"


def _visual(page) -> tuple[str, str]:
    engine = _rapid()
    if not engine:
        return "", "RAPIDOCR_ABSENT"
    import numpy as np
    pix = page.get_pixmap(dpi=200, alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    result, _ = engine(image)
    if not result:
        return "", "RAPIDOCR_EMPTY"
    lines = [item[1] for item in result if len(item) > 1 and item[1]]
    return "\n".join(lines).strip(), "RAPIDOCR"


def read_page1(path: Path) -> tuple[str, str, list[str]]:
    errors = []
    try:
        import fitz
        with fitz.open(str(path)) as doc:
            if not doc.page_count:
                return "", "", ["empty"]
            page = doc[0]
            native, why, _count, _coverage, _ratio = _probe(page)
            if native:
                text, reader = _native(doc, page)
                if text:
                    return text, reader, errors
                errors.append(reader + ":empty")
            else:
                text, reader = _visual(page)
                errors.append("NEEDS_VISUAL:" + why)
                if text:
                    return text, reader, errors
                errors.append(reader)
    except Exception as exc:
        errors.append("ENG072_FITZ_LAYOUT:" + type(exc).__name__)
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        if reader.pages:
            text = (reader.pages[0].extract_text() or "").strip()
            if len("".join(text.split())) >= 50:
                return text, "ENG072_PYPDF", errors
        errors.append("ENG072_PYPDF:empty")
    except Exception as exc:
        errors.append("ENG072_PYPDF:" + type(exc).__name__)
    return "", "", errors


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _prior()
    prior.read_page1 = read_page1
    card = prior.run(folder, data_root, open_page)
    card["door"] = "VRN_ENG110_TabReport_v0107"
    card["python"] = sys.executable
    card["reader_order"] = ["PYMUPDF4LLM", "ENG072_FITZ_LAYOUT", "RAPIDOCR", "ENG072_PYPDF"]
    card["pymupdf4llm"] = "ready" if _markdown() else "ABSENT"
    card["rapidocr"] = "ready" if _rapid() else "ABSENT"
    card["docling"] = "ABSENT"
    card["ocr_budget"] = "not called"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _prior()
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["present"] else 2


def selftest() -> int:
    import fitz
    folder = Path("/tmp/vrn_v0107")
    folder.mkdir(parents=True, exist_ok=True)
    good = folder / "JP-2330 20250718.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Revenue grew after the company visit and the target was raised again today.")
    doc.save(good)
    doc.close()
    blank = folder / "A-scan.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(blank)
    doc.close()
    card = run(folder, Path("/tmp/vrn_v0107_out"), False)
    ok = card["text"] == 1 and card["ocr_budget"] == "not called" and card["written"] == 0 and "NEEDS_VISUAL" in card["reader_error"]
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({k: card[k] for k in ("text", "readers", "reader_error", "pymupdf4llm", "rapidocr")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
