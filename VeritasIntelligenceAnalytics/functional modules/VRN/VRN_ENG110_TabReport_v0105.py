#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page 1 through the pdfplumber pair. PyMuPDF is not required."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
HUB = VIA / "supportive modules" / "70_VRN_Rules" / "SUP_MDL746_PDFPlumberPlusHub_v0101.py"


def _prior():
    spec = importlib.util.spec_from_file_location("tab_report_v0103", HERE / "VRN_ENG110_TabReport_v0103.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hub():
    spec = importlib.util.spec_from_file_location("ppp_hub", HUB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_page1(path: Path) -> tuple[str, str, list[str]]:
    errors = []
    try:
        text, mark = _hub().page_text(path, 1)
        if text:
            return text, "pdfplumber_plus", errors
        if mark:
            errors.append(mark)
    except Exception as exc:
        errors.append("pdfplumber_plus:" + type(exc).__name__)
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as doc:
            if doc.pages:
                text = (doc.pages[0].extract_text() or "").strip()
                if text:
                    return text, "pdfplumber", errors
        errors.append("pdfplumber:empty")
    except Exception as exc:
        errors.append("pdfplumber:" + type(exc).__name__)
    try:
        from pdfminer.high_level import extract_text
        text = (extract_text(str(path), page_numbers={0}) or "").strip()
        if text:
            return text, "pdfminer", errors
        errors.append("pdfminer:empty")
    except Exception as exc:
        errors.append("pdfminer:" + type(exc).__name__)
    return "", "", errors


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _prior()
    prior.read_page1 = read_page1
    card = prior.run(folder, data_root, open_page)
    card["door"] = "VRN_ENG110_TabReport_v0105"
    card["python"] = sys.executable
    card["reader_order"] = ["pdfplumber_plus", "pdfplumber", "pdfminer"]
    try:
        import pdfplumber
        card["pdfplumber"] = pdfplumber.__version__
    except Exception as exc:
        card["pdfplumber"] = type(exc).__name__
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
    folder = Path("/tmp/vrn_v0105")
    folder.mkdir(parents=True, exist_ok=True)
    good = folder / "JP-2330 20250718.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Revenue grew after the company visit.")
    doc.save(good)
    doc.close()
    card = run(folder, Path("/tmp/vrn_v0105_out"), False)
    ok = card["text"] == 1 and "fitz" not in card["readers"] and card["written"] == 0 and card["pdfplumber"] != "ModuleNotFoundError"
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({k: card[k] for k in ("text", "readers", "reader_error", "pdfplumber")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
