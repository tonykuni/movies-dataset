#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. Grade the text layer. Do not OCR.

Three grades, from the best body page (pages 2-12; a one-page file uses that page):
TEXT  >= 400 characters, no OCR
THIN  40-399, text exists but thin
SCAN  < 40, OCR would be required later
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from io import StringIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CUT = VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py"
LABEL = {"TEXT": "免OCR", "THIN": "文字薄", "SCAN": "要OCR", "FAIL": "打不開"}
LAMP = {"TEXT": "GREEN", "THIN": "YELLOW", "SCAN": "RED", "FAIL": "RED"}


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


def grade_chars(chars: int) -> str:
    if chars >= 400:
        return "TEXT"
    if chars >= 40:
        return "THIN"
    return "SCAN"


def body_chars(pages: list[int]) -> int:
    """pages[0] is the cover. Grade the rest. A single page is graded as itself."""
    if not pages:
        return 0
    body = pages[1:12]
    return max(body) if body else pages[0]


def _fit(rows: list[dict], columns: list[str]) -> str:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(pad_edge=False, padding=(0, 1), show_lines=False, expand=False)
        for name in columns:
            table.add_column(name, no_wrap=True, overflow="ignore")
        for row in rows:
            table.add_row(*[str(row.get(name, "")) for name in columns])
        buf = StringIO()
        Console(file=buf, width=220, force_terminal=False, color_system=None).print(table)
        return buf.getvalue().rstrip()
    except Exception:
        widths = {name: len(name) for name in columns}
        for row in rows:
            for name in columns:
                widths[name] = max(widths[name], len(str(row.get(name, ""))))
        lines = [" ".join(name.ljust(widths[name]) for name in columns)]
        for row in rows:
            lines.append(" ".join(str(row.get(name, "")).ljust(widths[name]) for name in columns))
        return "\n".join(lines)


def _pages(path: Path) -> tuple[str, list[int]]:
    try:
        import fitz
    except Exception:
        return "ABSENT", []
    try:
        with fitz.open(str(path)) as doc:
            counts = []
            for index, page in enumerate(doc):
                if index >= 12:
                    break
                counts.append(len(page.get_text("text") or ""))
            return "OK", counts
    except Exception:
        return "FAIL", []


def measure() -> dict:
    folder = sample_dir()
    if not folder.is_dir():
        return {"folder": str(folder), "present": False, "rows": [], "skipped": 0}
    cut = _load(CUT, "cut104")
    rows = []
    skipped = 0
    for item in sorted(folder.iterdir()):
        if not item.is_file() or item.suffix.lower() != ".pdf":
            continue
        if not cut.read_name(item.name).get("ticker"):
            skipped += 1
            continue
        state, counts = _pages(item)
        if state == "ABSENT":
            grade = "FAIL"
            best = 0
            where = ""
        elif state == "FAIL" or not counts:
            grade = "FAIL"
            best = 0
            where = ""
        else:
            best = body_chars(counts)
            grade = grade_chars(best)
            body = counts[1:12] or counts[:1]
            where = str((counts[1:12] or counts).index(best) + (2 if len(counts) > 1 else 1))
            if best not in body:
                where = "1"
        rows.append({
            "lamp": LAMP[grade],
            "file": item.name,
            "grade": LABEL[grade],
            "code": grade,
            "chars": best,
            "page": where,
        })
    return {"folder": str(folder), "present": True, "rows": rows, "skipped": skipped}


def selftest() -> list[str]:
    fails = []
    if grade_chars(400) != "TEXT" or grade_chars(399) != "THIN" or grade_chars(39) != "SCAN":
        fails.append("cut")
    if body_chars([10, 900, 20]) != 900 or body_chars([12]) != 12 or body_chars([]) != 0:
        fails.append("body")
    if LAMP["TEXT"] != "GREEN" or LAMP["SCAN"] != "RED":
        fails.append("lamp")
    return fails


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    fails = selftest()
    book = measure()
    counts = {"TEXT": 0, "THIN": 0, "SCAN": 0, "FAIL": 0}
    for row in book["rows"]:
        counts[row["code"]] = counts.get(row["code"], 0) + 1
    errors = [
        {"lamp": "GREEN", "check": "text", "detail": f"{counts['TEXT']} 免OCR"},
        {"lamp": "YELLOW", "check": "thin", "detail": f"{counts['THIN']} 文字薄"},
        {"lamp": "RED" if counts["SCAN"] else "GREEN", "check": "scan", "detail": f"{counts['SCAN']} 要OCR，這輪沒叫"},
        {"lamp": "YELLOW", "check": "paddle", "detail": "ABSENT not called"},
        {"lamp": "GREEN", "check": "quote", "detail": "not refetched"},
    ]
    if not book["present"]:
        errors.append({"lamp": "YELLOW", "check": "folder", "detail": book["folder"]})
    cols = ["lamp", "file", "grade", "chars", "page"]
    shown = [{k: row[k] for k in cols} for row in book["rows"]]
    print("GRADE")
    print(_fit(shown, cols) if shown else "(no stock pdf)")
    print("ERROR")
    print(_fit(errors, ["lamp", "check", "detail"]))
    focus = [row for row in book["rows"] if "2330" in row["file"]]
    hold = [row for row in book["rows"] if row["code"] != "TEXT"]
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_TextGrade_v0100",
        "selftest": "FAIL" if fails else "OK",
        "fails": fails,
        "folder": book["folder"],
        "present": book["present"],
        "stock_pdf": len(book["rows"]),
        "skipped_non_stock": book["skipped"],
        "counts": counts,
        "cut": {"TEXT": ">=400", "THIN": "40-399", "SCAN": "<40"},
        "focus": [{k: row[k] for k in ("lamp", "file", "grade", "code", "chars", "page")} for row in focus[:8]],
        "hold": [{k: row[k] for k in ("lamp", "file", "grade", "code", "chars", "page")} for row in hold[:24]],
        "errors": errors,
        "do_not": ["run ocr this round", "call paddle", "refetch the locked close", "parse non-stock reports"],
        "next": "none",
    }
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
