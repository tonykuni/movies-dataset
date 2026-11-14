#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only second-reader check of the four source excerpts and their PDF hash.

v0104: a point with no source excerpt is MISSING (原文不足 · 待核對 · rc 2), not FAIL;
FAIL stays for a quote the second reader cannot reproduce, a changed PDF or a bad hash.
"""
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
    text = unicodedata.normalize("NFKC", str(text)).replace("\u00ad", "")
    # v0104: PDFium and PyMuPDF map missing bullet / control glyphs differently (\x00, \x02, •, ■ …).
    # Those are layout decorations, never the quoted words; drop them on both sides of the comparison.
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f•·‧●○■□▪▫◆◇◼◻▲△►▶➢➤➔→✓✔✗※◎★☆‣⁃⦁]", "", text)
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
        try:
            opened = pdfium.PdfDocument(str(path))
        except Exception as error:
            rows.append({"file": item["file"], "state": "FAIL", "reason": "source PDF unreadable: " + type(error).__name__})
            continue
        with opened as pdf:
            for proof in item["points"]:
                point = int(proof["point"])
                row = {"file": item["file"], "point": point, "page": proof.get("page"), "state": "FAIL"}
                rows.append(row)
                quote = str(proof.get("quote") or "")
                actual = (summaries.get(item["file"]) or {}).get(f"POINT_{point}")
                if not quote and not (actual or "").strip():
                    row.update(state="MISSING", reason="no source excerpt; original text insufficient (待核對)")
                    continue
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
    code = 1 if counts.get("FAIL") else (2 if counts.get("OCR_PENDING") or counts.get("MISSING") else 0)
    verdict = {0: "PASS", 1: "FAIL", 2: "REVIEW_OCR" if counts.get("OCR_PENDING") and not counts.get("MISSING") else "REVIEW_MISSING"}[code]
    return {"schema": "VRN2_VERBATIM_VERIFY/1", "verdict": verdict, "rc": code, "counts": counts, "rows": rows}


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        out, src = Path(temporary) / "out", Path(temporary) / "src"
        out.mkdir(); src.mkdir()
        import pypdfium2 as pdfium
        blank = pdfium.PdfDocument.new()
        blank.new_page(200, 200)
        blank.save(src / "a.pdf")
        rows = [{"FILENAME": "a.pdf", "TITLE": "t", "POINT_1": "", "POINT_2": "", "POINT_3": "", "POINT_4": "", "POINTS_OK": 0}]
        (out / "VRN2_Summary_latest.json").write_text(json.dumps(rows), encoding="utf-8")
        points = [{"point": i, "verbatim": False, "text": "", "quote": "", "page": None} for i in range(1, 5)]
        (out / "VRN2_SummarySource_latest.json").write_text(json.dumps({"documents": [{"file": "a.pdf", "pdf_sha256": hashlib.sha256((src / "a.pdf").read_bytes()).hexdigest(), "points": points}]}), encoding="utf-8")
        report = verify(out, src)
        assert report["rc"] == 2 and report["counts"] == {"MISSING": 4} and report["verdict"] == "REVIEW_MISSING", report
        assert comparable("\x00 先進封裝 • 測試\n產能") == comparable("先進封裝測試產能")
        rows[0]["POINT_1"] = "text that is not in the proof"
        (out / "VRN2_Summary_latest.json").write_text(json.dumps(rows), encoding="utf-8")
        report = verify(out, src)
        assert report["rc"] == 1 and report["counts"].get("FAIL") == 1 and report["counts"].get("MISSING") == 3, report
    print("[PASS] v0104: missing excerpt is MISSING (rc 2); text without proof stays FAIL (rc 1)")
    return 0


def main(argv=None):
    if (sys.argv[1:] if argv is None else argv) == ["--selftest"]:
        return selftest()
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    options = parser.parse_args(argv)
    # [VIA:ACCEL-BRIDGE:v0111] The second reader has the same active accelerator.
    path = Path(__file__).with_name("VIA_ExecutionBridge_v0103.py")
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
