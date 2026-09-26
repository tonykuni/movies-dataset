#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. Column reading order. Read-only.

pdfminer uses one boxes_flow for the whole page:
  -1  only x. Left before right, but the y order inside a column is lost.
  +1  only y. Top before bottom, so the right rail is mixed into the body.
  0.5 the default. y still weighs more than x, so a high right card
      is read before a lower left block.
Columns need two values. Across columns, boxes_flow is -1 via the 52% cut.
Inside a column, boxes_flow is +1. The sort key is pdfminer's, y up.
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
SPLIT = 0.52


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


def flow_key(box: dict, boxes_flow: float) -> float:
    if not -1 <= boxes_flow <= 1:
        raise ValueError("boxes_flow must be from -1 to 1")
    return (1 - boxes_flow) * box["x0"] - (1 + boxes_flow) * (box["y0"] + box["y1"])


def order_flow(boxes: list, boxes_flow: float) -> list:
    return sorted(boxes, key=lambda box: flow_key(box, boxes_flow))


def order_columns(boxes: list, width: float) -> list:
    left, right = [], []
    for box in boxes:
        if box["x0"] >= SPLIT * width:
            right.append(box)
        else:
            left.append(box)
    return order_flow(left, 1) + order_flow(right, 1)


def is_stock(name: str, cut) -> bool:
    named = cut.read_name(name)
    tickers = [row for row in named.get("parts") or [] if row.get("role") == "TICKER"]
    if not tickers:
        return False
    return not all(row.get("ambiguous_year") for row in tickers)


def read_page1(path: Path) -> dict:
    import fitz

    with fitz.open(path) as doc:
        if not doc.page_count:
            return {"boxes": [], "width": 0, "changed": False}
        page = doc[0]
        width, height = float(page.rect.width), float(page.rect.height)
        boxes = []
        for index, block in enumerate(page.get_text("dict")["blocks"]):
            if block.get("type") != 0:
                continue
            x0, y0, x1, y1 = block["bbox"]
            text = "".join(
                span.get("text") or ""
                for line in block.get("lines") or []
                for span in line.get("spans") or []
            ).strip()
            if not text:
                continue
            boxes.append({
                "id": index,
                "x0": x0,
                "x1": x1,
                "y0": height - y1,
                "y1": height - y0,
                "text": text[:24],
            })
    plain = [box["id"] for box in order_flow(boxes, 0.5)]
    columns = [box["id"] for box in order_columns(boxes, width)]
    return {"boxes": len(boxes), "width": width, "changed": plain != columns}


def selftest() -> int:
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    boxes = [
        {"id": "left-top", "x0": 40, "y0": 700, "y1": 720},
        {"id": "left-low", "x0": 40, "y0": 100, "y1": 120},
        {"id": "right-top", "x0": 520, "y0": 700, "y1": 720},
    ]
    plain = [box["id"] for box in order_flow(boxes, 0.5)]
    adjusted = [box["id"] for box in order_columns(boxes, 1000)]
    chk("default 0.5 reads the right card before the lower left block",
        plain.index("right-top") < plain.index("left-low"))
    chk("columns finish the left side first",
        adjusted == ["left-top", "left-low", "right-top"])
    chk("minus one keeps left before right but drops the y order",
        [box["id"] for box in order_flow(list(reversed(boxes[:2])), -1)] == ["left-low", "left-top"])
    try:
        flow_key(boxes[0], 2)
        chk("a flow outside -1 to 1 is refused", False)
    except ValueError:
        chk("a flow outside -1 to 1 is refused", True)
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if selftest() != 0:
        print(json.dumps({"via": "vcgc", "door": "CGC_MDL149_BoxesFlow_v0100", "selftest": "FAIL"}, ensure_ascii=False))
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
            if got["boxes"] == 0:
                lamp = "RED"
            elif got["changed"]:
                lamp = "GREEN"
            else:
                lamp = "YELLOW"
            rows.append({"lamp": lamp, "file": path.name, "boxes": got["boxes"], "changed": got["changed"]})
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in rows:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_BoxesFlow_v0100",
        "selftest": "OK",
        "fails": [],
        "folder": str(folder),
        "present": present,
        "stock_pdf": len(rows),
        "skipped_non_stock": skipped,
        "counts": counts,
        "rows": rows[:8],
        "rule": "across columns the 52% cut stands in for boxes_flow -1; inside a column boxes_flow is +1; the page default 0.5 is not used",
        "do_not": [
            "set one boxes_flow for a two-column page",
            "call paddle",
            "run ocr",
            "write the database",
            "parse non-stock reports",
        ],
        "next": "none",
    }
    print(f"FLOW  stock {len(rows)}  skip {skipped}  {counts}")
    for row in rows:
        print(f"{row['lamp']:6}  changed {str(row.get('changed')):5}  boxes {row.get('boxes', 0):3}  {row['file']}")
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("END_PASTE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
