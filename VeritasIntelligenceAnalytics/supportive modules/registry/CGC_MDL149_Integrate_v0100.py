#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. One read-only pass over the pieces already measured.

Page 1 of a stock PDF:
  four zones, then a 15% gap split
  left column finished before the right rail
  body only goes through ENG085 repair and sentence split
  tables are scored inside the body crop when a right rail exists
  NLP target is the newest hub package; it is not asked to rewrite text
No LayoutParser, no paddle, no database, no quote refetch.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENG085 = VIA / "functional modules" / "VRN" / "VRN_ENG085_MarkdownRestore_v0104.py"
HUB = VIA / "supportive modules" / "70_VRN_Rules" / "SUP_MDL744_NLPApplicationHub_v0101.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def table_crop(width: float, height: float, segments: list) -> tuple:
    has_right = any(seg["zone"] == "right" for seg in segments)
    has_body = any(seg["zone"] == "body" for seg in segments)
    if has_right and has_body:
        return (0.0, 0.0, 0.52 * width, height)
    return (0.0, 0.0, width, height)


def body_source(segments: list) -> str:
    body = [seg for seg in segments if seg["zone"] == "body"]
    body.sort(key=lambda seg: (round(seg["y0"], 1), seg["x0"]))
    return "\n".join(seg["text"] for seg in body)


def widest_white(spans: list, key0: str, key1: str, start: float, end: float, floor: float) -> float:
    merged = []
    for span in sorted(spans, key=lambda item: item[key0]):
        a, b = span[key0], span[key1]
        if b <= a:
            continue
        if not merged or a > merged[-1][1]:
            merged.append([a, b])
        else:
            merged[-1][1] = max(merged[-1][1], b)
    cursor = start
    best = 0.0
    for a, b in merged:
        if a - cursor >= floor:
            best = max(best, a - cursor)
        cursor = max(cursor, b)
    if end - cursor >= floor:
        best = max(best, end - cursor)
    return best


def nlp_target() -> dict:
    hub = _load(HUB, "nlp_hub")
    newest = hub.newest()
    if newest is None:
        return {"state": "ABSENT", "version": None, "writeback": False}
    return {
        "state": "SEEN",
        "version": ".".join(str(part) for part in hub._ver(newest)),
        "name": newest.name,
        "writeback": False,
    }


def selftest() -> int:
    layout = _load(HERE / "CGC_MDL149_LayoutUse_v0100.py", "layout_use")
    flow = _load(HERE / "CGC_MDL149_BoxesFlow_v0100.py", "boxes_flow")
    score = _load(HERE / "CGC_MDL149_TableTake_v0101.py", "table_score")
    text = _load(ENG085, "eng085")
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    chk("zones still come from the layout door", layout.selftest() == 0)
    chk("column order still comes from the flow door", flow.selftest() == 0)
    long_left = "先進製程需求強勁且資本支出繼續增加"
    joined, counts = text.repair_text(long_left + "\n中的資本支出")
    chk("a long CJK wrap joins", counts["joins"] == 1 and "\n" not in joined)
    kept, counts = text.repair_text("Q2\n2025")
    chk("latin wrap stays broken", counts["joins"] == 0 and kept == "Q2\n2025")
    sentences = text.split_sentences("營收成長。毛利持平")
    chk("sentences break on the period only", sentences == ["營收成長。", "毛利持平"])
    segments = [
        {"zone": "body", "x0": 40, "y0": 100, "text": long_left},
        {"zone": "right", "x0": 600, "y0": 100, "text": "目標價 1,275"},
        {"zone": "body", "x0": 40, "y0": 130, "text": "中的資本支出。"},
    ]
    source = body_source(segments)
    chk("the right rail stays out of the body", "目標價" not in source and "先進製程" in source)
    crop = table_crop(1000, 800, segments)
    chk("a two-column page scores tables only on the left", crop[2] == 520)
    chk("a single column keeps the whole page", table_crop(1000, 800, segments[:1]) == (0.0, 0.0, 1000, 800))
    grid = [["科目", "2024", "2025"], ["營收", "10", "12"], ["毛利", "2", "3"]]
    shred = [["科目", "", "", ""], ["", "10", "", ""], ["", "", "12", ""], ["", "", "", "3"]]
    chk("a lined grid still beats a shred", score.score_accuracy(grid, True) > score.score_accuracy(shred, False))
    chk("a dash is empty and a negative number is not", score.clean_cell("-") == "" and score.clean_cell("-12.7") == "-12.7")
    spans = [{"x0": 0, "x1": 10}, {"x0": 40, "x1": 80}]
    chk("a 30pt gap is a valley and a word gap is not", widest_white(spans, "x0", "x1", 0, 100, 20) == 30)
    chk("the floor can reject that valley", widest_white(spans, "x0", "x1", 0, 100, 50) == 0)
    target = nlp_target()
    chk("nlp is seen and not written back", target["state"] == "SEEN" and target["writeback"] is False)
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


def segments_of(page, width: float) -> list:
    layout = _load(HERE / "CGC_MDL149_LayoutUse_v0100.py", "layout_use_run")
    found = []
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
                spans.append({"text": text, "x0": x0, "y0": y0, "x1": x1, "y1": y1, "size": float(span.get("size") or 0)})
            for part in layout.split_spans(spans, width):
                found.append({
                    "text": "".join(span["text"] for span in part),
                    "x0": min(span["x0"] for span in part),
                    "y0": min(span["y0"] for span in part),
                    "x1": max(span["x1"] for span in part),
                    "y1": max(span["y1"] for span in part),
                    "size": max(span["size"] for span in part),
                    "zone": layout.zone_of(
                        min(span["x0"] for span in part),
                        min(span["y0"] for span in part),
                        max(span["x1"] for span in part),
                        max(span["y1"] for span in part),
                        max(span["size"] for span in part),
                        width,
                        float(page.rect.height),
                    ),
                })
    return found


def run_folder(folder: Path) -> dict:
    layout = _load(HERE / "CGC_MDL149_LayoutUse_v0100.py", "layout_stock")
    score = _load(HERE / "CGC_MDL149_TableTake_v0101.py", "table_run")
    text = _load(ENG085, "eng085_run")
    cut = layout._load(layout.CUT, "filename_cut")
    import fitz
    try:
        import pdfplumber
    except Exception:
        pdfplumber = None
    rows = []
    skipped = 0
    for path in sorted(folder.glob("*.pdf")):
        if not layout.is_stock(path.name, cut):
            skipped += 1
            continue
        try:
            with fitz.open(path) as doc:
                if not doc.page_count:
                    rows.append({"lamp": "RED", "file": path.name, "detail": "empty"})
                    continue
                page = doc[0]
                width, height = float(page.rect.width), float(page.rect.height)
                segments = segments_of(page, width)
            source = body_source(segments)
            repaired, counts = text.repair_text(source)
            sentences = [sent for sent in text.split_sentences(repaired) if sent.strip()]
            chars = {zone: sum(len(seg["text"]) for seg in segments if seg["zone"] == zone)
                     for zone in ("header", "right", "body", "footer")}
            tables = []
            if pdfplumber is not None:
                crop = table_crop(width, height, segments)
                with pdfplumber.open(path) as pdf:
                    if pdf.pages:
                        tables = score.plumber_tries(pdf.pages[0], crop)
            best = tables[0]["engine"] if tables else "NONE"
            if chars["body"] == 0 and chars["right"] == 0:
                lamp = "RED"
            elif sentences and chars["right"]:
                lamp = "GREEN"
            else:
                lamp = "YELLOW"
            rows.append({
                "lamp": lamp,
                "file": path.name,
                "body": chars["body"],
                "right": chars["right"],
                "sentences": len(sentences),
                "joins": counts["joins"],
                "tables": len(tables),
                "engine": best,
            })
        except Exception as exc:
            rows.append({"lamp": "RED", "file": path.name, "detail": type(exc).__name__})
    return {"stock_pdf": len(rows), "skipped_non_stock": skipped, "rows": rows}


def main() -> int:
    if selftest() != 0:
        print(json.dumps({"via": "vcgc", "door": "CGC_MDL149_Integrate_v0100", "selftest": "FAIL"}, ensure_ascii=False))
        return 1
    layout = _load(HERE / "CGC_MDL149_LayoutUse_v0100.py", "layout_main")
    folder = layout.sample_dir()
    present = folder.is_dir()
    body = {"stock_pdf": 0, "skipped_non_stock": 0, "rows": []}
    if present:
        body = run_folder(folder)
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in body["rows"]:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    target = nlp_target()
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_Integrate_v0100",
        "selftest": "OK",
        "fails": [],
        "folder": str(folder),
        "present": present,
        "stock_pdf": body["stock_pdf"],
        "skipped_non_stock": body["skipped_non_stock"],
        "counts": counts,
        "nlp": target,
        "rows": body["rows"][:8],
        "rule": "zones then body repair; tables cropped off the right rail; nlp is not written back",
        "do_not": [
            "send the right rail into sentences",
            "call layoutparser",
            "call paddle",
            "write the database",
            "write nlp text back onto the page",
            "refetch the locked close",
            "parse non-stock reports",
        ],
        "next": "none",
    }
    print(f"ALL  stock {body['stock_pdf']}  skip {body['skipped_non_stock']}  nlp {target.get('name')}  {counts}")
    for row in body["rows"]:
        print(
            f"{row['lamp']:6}  sent {row.get('sentences', 0):3}  join {row.get('joins', 0):2}  "
            f"tbl {row.get('tables', 0):2}  {row.get('engine', ''):12}  {row['file']}"
        )
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("END_PASTE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
