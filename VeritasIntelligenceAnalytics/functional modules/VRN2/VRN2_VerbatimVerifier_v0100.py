#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only second-reader check of the four source excerpts and their PDF hash."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unicodedata


def comparable(text):
    # PDFium maps the discretionary-hyphen glyph in some embedded fonts to
    # U+0002. Normalize that reader artifact only; stored excerpts stay exact.
    text = unicodedata.normalize("NFKC", str(text)).replace("\u00ad", "").replace("\x02", "")
    text = re.sub(r"-\s*\n\s*(?=[a-z])", "", text)
    return re.sub(r"\s+", "", text).translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})).casefold()


def verify(output, source):
    import pypdfium2 as pdfium
    output, source = Path(output), Path(source)
    document = json.loads((output / "VRN2_SummarySource_latest.json").read_text(encoding="utf-8-sig"))
    public_rows = json.loads((output / "VRN2_Summary_latest.json").read_text(encoding="utf-8-sig"))
    summaries = {row["FILENAME"]: row for row in public_rows}
    rows = []
    names = [item["file"] for item in document["documents"]]
    if len(public_rows) != len(summaries) or len(names) != len(set(names)) or set(names) != set(summaries):
        rows.append({"state": "FAIL", "reason": "source proof/public output file set differs or contains duplicate files"})
    for item in document["documents"]:
        if sorted(proof.get("point", 0) for proof in item["points"]) != [1, 2, 3, 4]:
            rows.append({"file": item["file"], "state": "FAIL", "reason": "four distinct source points required"})
            continue
        path = source / item["file"]
        if not path.is_file():
            rows.append({"file": item["file"], "state": "FAIL", "reason": "source PDF missing"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with pdfium.PdfDocument(str(path)) as pdf:
            for proof in item["points"]:
                point = int(proof["point"])
                row = {"file": item["file"], "point": point, "page": proof.get("page"), "state": "FAIL"}
                rows.append(row)
                quote = str(proof.get("quote") or "")
                actual = (summaries.get(item["file"]) or {}).get(f"POINT_{point}")
                if not quote or actual != quote or not proof.get("verbatim") or hashlib.sha256(quote.encode("utf-8")).hexdigest() != proof.get("quote_sha256"):
                    row["reason"] = "output text/quote/hash mismatch"
                    continue
                if digest != item.get("pdf_sha256"):
                    row["reason"] = "input PDF hash changed"
                    continue
                number = int(proof.get("page") or 0)
                if not 1 <= number <= len(pdf):
                    row["reason"] = "invalid source page"
                    continue
                page = pdf[number - 1]
                text_page = page.get_textpage()
                whole = text_page.get_text_range()
                if not whole.strip():
                    row.update(state="OCR_PENDING", reason="image page; OCR excerpt needs image verification")
                    continue
                box = proof.get("bbox")
                bounded = ""
                if box and len(box) == 4:
                    height = page.get_height()
                    bounded = text_page.get_text_bounded(left=max(0, box[0] - 2), bottom=max(0, height - box[3] - 2), right=box[2] + 2, top=height - box[1] + 2)
                needle = comparable(quote)
                if needle and needle in comparable(bounded):
                    row.update(state="PASS", reader="pypdfium2", match="source bounding box")
                elif needle and needle in comparable(whole):
                    row.update(state="PASS", reader="pypdfium2", match="same source page")
                elif proof.get("reader") == "OCR":
                    row.update(state="OCR_PENDING", reason="OCR excerpt needs image verification; PDF text layer is insufficient")
                else:
                    row["reason"] = "second reader did not reproduce the complete source excerpt"
    counts = dict(Counter(row["state"] for row in rows))
    if len(document["documents"]) != len(summaries) or not rows:
        counts["FAIL"] = counts.get("FAIL", 0) + 1
    code = 1 if counts.get("FAIL") else (2 if counts.get("OCR_PENDING") else 0)
    return {"schema": "VRN2_VERBATIM_VERIFY/1", "verdict": {0: "PASS", 1: "FAIL", 2: "REVIEW_OCR"}[code], "rc": code, "counts": counts, "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    options = parser.parse_args(argv)
    # [VIA:ACCEL-BRIDGE:v0100] The second reader has the same active accelerator.
    path = Path(__file__).with_name("VIA_ExecutionBridge_v0100.py")
    spec = importlib.util.spec_from_file_location("verbatim_verify_acceleration", path)
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    bridge.activate(options.root)
    report = verify(options.output, options.source)
    options.report.parent.mkdir(parents=True, exist_ok=True)
    options.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[原文獨立核對]", report["verdict"], report["counts"], options.report, flush=True)
    return report["rc"]


if __name__ == "__main__":
    raise SystemExit(main())
