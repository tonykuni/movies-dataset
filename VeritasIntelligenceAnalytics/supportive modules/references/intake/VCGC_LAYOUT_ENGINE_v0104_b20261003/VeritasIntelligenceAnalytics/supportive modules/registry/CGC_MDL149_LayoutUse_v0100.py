#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. Use the existing four-zone cut. Read-only.

Same ruler as VRN_ENG072, page 1 only:
  footer  bottom edge below 92% and size < 9
  header  wider than 66% and starts in the top 18%
  right   left edge at or past 52%
  body    the rest
A gap wider than 15% of the page splits a line before the zone test,
so one block that covers both columns does not all fall into the body.
No OCR, no paddle, no database.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CUT = VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sample_dir() -> Path:
    spec = HERE / "VIA_InputConsole_Spec_v0100.json"
    chosen = ""
    if spec.is_file():
        data = json.loads(spec.read_text(encoding="utf-8"))
        chosen = str(((data.get("user") or {}).get("vrn_dir") or "")).strip()
    return Path(chosen or r"C:\測試樣本報告")


def zone_of(x0, y0, x1, y1, size, width, height) -> str:
    wide = (x1 - x0) > 0.66 * width
    if y1 > 0.92 * height and size < 9:
        return "footer"
    if wide and y0 < 0.18 * height:
        return "header"
    if x0 >= 0.52 * width:
        return "right"
    return "body"


def split_spans(spans, width) -> list:
    ordered = sorted(spans, key=lambda span: span["x0"])
    if not ordered:
        return []
    parts = [[ordered[0]]]
    for span in ordered[1:]:
        if span["x0"] - parts[-1][-1]["x1"] > 0.15 * width:
            parts.append([span])
        else:
            parts[-1].append(span)
    return parts


def is_stock(name: str, cut) -> bool:
    named = cut.read_name(name)
    tickers = [row for row in named.get("parts") or [] if row.get("role") == "TICKER"]
    if not tickers:
        return False
    return not all(row.get("ambiguous_year") for row in tickers)


def read_page1(path: Path) -> dict:
    import fitz

    counts = {"header": 0, "right": 0, "body": 0, "footer": 0}
    splits = 0
    with fitz.open(path) as doc:
        if not doc.page_count:
            return {"chars": counts, "splits": 0, "pages": 0}
        page = doc[0]
        width, height = float(page.rect.width), float(page.rect.height)
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines") or []:
                spans = []
                for span in line.get("spans") or []:
                    text = span.get("text") or ""
                    if not text.strip():
                        continue
                    x0, y0, x1, y1 = span["bbox"]
                    spans.append({
                        "text": text, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "size": float(span.get("size") or 0),
                    })
                parts = split_spans(spans, width)
                if len(parts) > 1:
                    splits += 1
                for part in parts:
                    x0 = min(span["x0"] for span in part)
                    y0 = min(span["y0"] for span in part)
                    x1 = max(span["x1"] for span in part)
                    y1 = max(span["y1"] for span in part)
                    size = max(span["size"] for span in part)
                    zone = zone_of(x0, y0, x1, y1, size, width, height)
                    counts[zone] += sum(len(span["text"].strip()) for span in part)
        return {"chars": counts, "splits": splits, "pages": doc.page_count}


def lamp_for(chars: dict) -> str:
    body, right = chars["body"], chars["right"]
    if body == 0 and right == 0:
        return "RED"
    if body > 0 and right > 0:
        return "GREEN"
    return "YELLOW"


def selftest() -> int:
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    chk("right rail starts at 52%", zone_of(520, 100, 700, 140, 11, 1000, 800) == "right")
    chk("the left side stays body", zone_of(40, 100, 480, 200, 11, 1000, 800) == "body")
    chk("a wide top band is the header", zone_of(20, 10, 900, 80, 16, 1000, 800) == "header")
    chk("small type at the bottom is the footer", zone_of(40, 760, 200, 790, 8, 1000, 800) == "footer")
    spans = [
        {"x0": 40, "x1": 80, "text": "本文"},
        {"x0": 700, "x1": 760, "text": "目標價"},
    ]
    chk("a 15% gap splits one line", len(split_spans(spans, 1000)) == 2)
    close = [
        {"x0": 40, "x1": 80, "text": "營"},
        {"x0": 90, "x1": 130, "text": "收"},
    ]
    chk("a small gap stays one segment", len(split_spans(close, 1000)) == 1)
    chk("both columns present is green", lamp_for({"body": 20, "right": 8, "header": 0, "footer": 0}) == "GREEN")
    chk("body only is yellow", lamp_for({"body": 20, "right": 0, "header": 0, "footer": 0}) == "YELLOW")
    chk("no text is red", lamp_for({"body": 0, "right": 0, "header": 0, "footer": 0}) == "RED")
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if selftest() != 0:
        print(json.dumps({"via": "vcgc", "door": "CGC_MDL149_LayoutUse_v0100", "selftest": "FAIL"}, ensure_ascii=False))
        return 1
    folder = sample_dir()
    present = folder.is_dir()
    rows = []
    skipped = 0
    if present:
        cut = _load(CUT, "filename_cut")
        for path in sorted(folder.glob("*.pdf")):
            if not is_stock(path.name, cut):
                skipped += 1
                continue
            try:
                got = read_page1(path)
            except Exception as exc:
                rows.append({"lamp": "RED", "file": path.name, "detail": type(exc).__name__})
                continue
            chars = got["chars"]
            rows.append({
                "lamp": lamp_for(chars),
                "file": path.name,
                "body": chars["body"],
                "right": chars["right"],
                "header": chars["header"],
                "footer": chars["footer"],
                "splits": got["splits"],
            })
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in rows:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    focus = next((row for row in rows if "2330" in row["file"]), None)
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_LayoutUse_v0100",
        "selftest": "OK",
        "fails": [],
        "folder": str(folder),
        "present": present,
        "stock_pdf": len(rows),
        "skipped_non_stock": skipped,
        "page": 1,
        "counts": counts,
        "focus": focus,
        "rows": rows[:8],
        "rule": "ENG072 zones; gap over 15% of width splits a line first; page 1 only",
        "do_not": [
            "call paddle",
            "run ocr",
            "write the database",
            "refetch the locked close",
            "parse non-stock reports",
        ],
        "next": "none",
    }
    print(f"LAYOUT  stock {len(rows)}  skip {skipped}  {counts}")
    for row in rows:
        print(
            f"{row['lamp']:6}  body {row.get('body', 0):5}  right {row.get('right', 0):5}  "
            f"split {row.get('splits', 0):3}  {row['file']}"
        )
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("END_PASTE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
