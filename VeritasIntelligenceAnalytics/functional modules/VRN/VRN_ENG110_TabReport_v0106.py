#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page 1 uses the registered non-OCR pair from VRN_ENG072. OCR stays off."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("tab_report_v0103", HERE / "VRN_ENG110_TabReport_v0103.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_page1(path: Path) -> tuple[str, str, list[str]]:
    errors = []
    try:
        import fitz
        with fitz.open(str(path)) as doc:
            if doc.page_count:
                text = (doc[0].get_text("text", sort=True) or "").strip()
                if text:
                    return text, "ENG072_FITZ_LAYOUT", errors
        errors.append("ENG072_FITZ_LAYOUT:empty")
    except Exception as exc:
        errors.append("ENG072_FITZ_LAYOUT:" + type(exc).__name__)
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        if reader.pages:
            text = (reader.pages[0].extract_text() or "").strip()
            if text:
                return text, "ENG072_PYPDF", errors
        errors.append("ENG072_PYPDF:empty")
    except Exception as exc:
        errors.append("ENG072_PYPDF:" + type(exc).__name__)
    errors.append("OCR_NOT_CALLED")
    return "", "", errors


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _prior()
    prior.read_page1 = read_page1
    card = prior.run(folder, data_root, open_page)
    card["door"] = "VRN_ENG110_TabReport_v0106"
    card["python"] = sys.executable
    card["reader_order"] = ["ENG072_FITZ_LAYOUT", "ENG072_PYPDF"]
    card["ocr"] = "not called"
    card["registered"] = "VRN_ENG072_FirstPageText_v0139.extract_pdf_page1"
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
    folder = Path("/tmp/vrn_v0106")
    folder.mkdir(parents=True, exist_ok=True)
    good = folder / "JP-2330 20250718.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Layout order text from the registered non-OCR pair.")
    doc.save(good)
    doc.close()
    card = run(folder, Path("/tmp/vrn_v0106_out"), False)
    ok = card["text"] == 1 and card["readers"].get("ENG072_FITZ_LAYOUT") == 1 and card["ocr"] == "not called" and card["written"] == 0
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({k: card[k] for k in ("text", "readers", "reader_error", "ocr")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
