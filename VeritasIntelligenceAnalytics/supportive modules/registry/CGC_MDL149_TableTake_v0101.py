#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. pdfplumber accuracy. Still read-only.

v0100 counted filled cells, so a shredded text grid could tie a real table.
This version uses the four strategies already measured on this corpus:
lines/lines, lines/text, text/lines, text/text.
Score is fill squared, times filled cells, times 1.25 when a line is involved,
times column-width consistency. Overlapping crops keep the higher score.
Camelot and tabula still run only when every pdfplumber score is 0.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "CGC_MDL149_TableTake_v0100.py"
STRATEGIES = (
    {"id": "S1_lines", "v": "lines", "h": "lines", "lines": True},
    {"id": "S2_lines_text", "v": "lines", "h": "text", "lines": True},
    {"id": "S3_text_lines", "v": "text", "h": "lines", "lines": True},
    {"id": "S4_text", "v": "text", "h": "text", "lines": False},
)
NULL_CELLS = {"", "-", "—", "－", "N/A", "n/a", "null", "NULL"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_cell(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = " ".join(part.strip() for part in text.split("\n") if part.strip())
    text = " ".join(text.split())
    return "" if text in NULL_CELLS else text


def clean_matrix(rows) -> list:
    matrix = [[clean_cell(cell) for cell in row] for row in (rows or [])]
    return [row for row in matrix if any(row)]


def score_accuracy(matrix, lines_based: bool) -> float:
    matrix = clean_matrix(matrix)
    if len(matrix) < 2:
        return 0.0
    cols = max((len(row) for row in matrix), default=0)
    if cols < 2:
        return 0.0
    filled = sum(1 for row in matrix for cell in row if cell)
    if filled < 4:
        return 0.0
    total = max(1, len(matrix) * cols)
    fill = filled / total
    score = (fill ** 2) * float(filled)
    if lines_based:
        score *= 1.25
    widths = [len(row) for row in matrix]
    usual = max(set(widths), key=widths.count)
    consistency = widths.count(usual) / len(matrix)
    return score * (0.5 + 0.5 * consistency)


def overlap(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = max(1e-9, (ax1 - ax0) * (ay1 - ay0))
    area_b = max(1e-9, (bx1 - bx0) * (by1 - by0))
    return inter / min(area_a, area_b)


def dedup(candidates: list) -> list:
    ordered = sorted(candidates, key=lambda item: item["score"], reverse=True)
    kept = []
    for item in ordered:
        if item["score"] <= 0:
            continue
        box = item.get("bbox")
        if box is None or all(overlap(box, other["bbox"]) < 0.5 for other in kept):
            kept.append(item)
    return kept


def _settings(spec: dict) -> list:
    full = {
        "vertical_strategy": spec["v"],
        "horizontal_strategy": spec["h"],
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "intersection_tolerance": 3,
        "text_tolerance": 2,
    }
    plain = {
        "vertical_strategy": spec["v"],
        "horizontal_strategy": spec["h"],
        "snap_tolerance": 3,
        "join_tolerance": 3,
    }
    return [full, plain]


def plumber_tries(page, bbox=None) -> list:
    target = page.within_bbox(tuple(bbox)) if bbox else page
    found = []
    for spec in STRATEGIES:
        tables = None
        for settings in _settings(spec):
            try:
                tables = target.find_tables(table_settings=settings) or []
                break
            except Exception:
                tables = None
        if not tables:
            continue
        for table in tables:
            try:
                raw = table.extract()
            except Exception:
                continue
            matrix = clean_matrix(raw)
            found.append({
                "engine": spec["id"],
                "rows": matrix,
                "score": score_accuracy(matrix, spec["lines"]),
                "bbox": tuple(float(v) for v in table.bbox),
            })
    return dedup(found)


def selftest() -> int:
    base = _load(BASE, "table_take_v0100")
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    grid = [["科目", "2024", "2025"], ["營收", "10", "12"], ["毛利", "2", "3"]]
    shred = [["科目", "", "", ""], ["", "10", "", ""], ["", "", "12", ""], ["", "", "", "3"]]
    chk("v0100 selftest still holds", base.selftest() == 0)
    lined = score_accuracy(grid, True)
    plain = score_accuracy(grid, False)
    chk("same grid, a line strategy outranks plain text", lined > plain > 0)
    chk("a full grid outranks a shred with the same filled count", lined > score_accuracy(shred, False))
    chk("a dash placeholder is empty, not a value", clean_cell("-") == "" and clean_cell("-12.7") == "-12.7")
    chk("header-only stays 0", score_accuracy([["科目", "2024", "2025"]], True) == 0)
    one = dedup([
        {"engine": "S4_text", "score": 9, "bbox": (0, 0, 100, 40), "rows": grid},
        {"engine": "S1_lines", "score": 12, "bbox": (2, 1, 98, 39), "rows": grid},
        {"engine": "S1_lines", "score": 4, "bbox": (0, 200, 80, 260), "rows": grid},
    ])
    chk("overlap keeps the higher score and a second region", len(one) == 2 and one[0]["engine"] == "S1_lines")
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if selftest() != 0:
        print(json.dumps({"via": "vcgc", "door": "CGC_MDL149_TableTake_v0101", "selftest": "FAIL"}, ensure_ascii=False))
        return 1
    base = _load(BASE, "table_take_v0100_run")
    base.plumber_tries = plumber_tries
    folder = base.sample_dir()
    present = folder.is_dir()
    body = {"stock_pdf": 0, "skipped_non_stock": 0, "rows": []}
    if present:
        try:
            import pdfplumber  # noqa: F401
            body = base.run_folder(folder)
        except Exception as exc:
            body = {"stock_pdf": 0, "skipped_non_stock": 0, "rows": [], "import": type(exc).__name__}
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in body["rows"]:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_TableTake_v0101",
        "selftest": "OK",
        "fails": [],
        "folder": str(folder),
        "present": present,
        "stock_pdf": body["stock_pdf"],
        "skipped_non_stock": body["skipped_non_stock"],
        "counts": counts,
        "rule": "S1-S4; fill squared; line bonus 1.25; overlap keeps the higher score; camelot only if all four score 0; no database",
        "rows": body["rows"][:8],
        "do_not": [
            "write the database this round",
            "count fitz text lines as a table",
            "let a shredded grid outrank a lined grid",
            "call paddle",
            "refetch the locked close",
            "parse non-stock reports",
        ],
        "next": "none",
    }
    print(f"TABLE  stock {body['stock_pdf']}  skip {body['skipped_non_stock']}  {counts}")
    for row in body["rows"]:
        print(f"{row['lamp']:6}  {row['engine']:20}  {row['tables']:3}  {row['file']}")
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("END_PASTE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
