#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. Read statement pages already on disk. No quote refetch. No Paddle.

Basic EPS and diluted EPS stay apart. A bare EPS fills neither. Report age is not read.
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
CHECK = VIA / "functional modules" / "VRN" / "VRN_ENG108_StatementCheck_v0100.py"
CUT = VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py"
SCALE = HERE / "CGC_MDL149_UnitScale_v0101.py"


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


def row_lamp(card: dict) -> str:
    state = str(card.get("state") or "")
    if state.startswith("FAIL"):
        return "RED"
    if card.get("add") == "FAIL" or card.get("div") == "FAIL":
        return "RED"
    if state != "SEEN":
        return "YELLOW"
    if card.get("basic_eps") is None and card.get("diluted_eps") is None:
        return "YELLOW"
    return "GREEN"


def _eps(scale, value) -> str:
    if value is None:
        return ""
    shown = scale.convert_unit(str(value), "basic_eps", "元")
    return shown["display"] if shown.get("ok") else ""


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
        Console(file=buf, width=240, force_terminal=False, color_system=None).print(table)
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


def measure() -> dict:
    folder = sample_dir()
    if not folder.is_dir():
        return {"folder": str(folder), "present": False, "rows": [], "skipped": 0}
    cut = _load(CUT, "cut104")
    check = _load(CHECK, "stmt108")
    scale = _load(SCALE, "scale0101")
    rows = []
    skipped = 0
    for item in sorted(folder.iterdir()):
        if not item.is_file() or item.suffix.lower() != ".pdf":
            continue
        named = cut.read_name(item.name)
        if not named.get("ticker"):
            skipped += 1
            continue
        card = check.inspect(item)
        rows.append({
            "lamp": row_lamp(card),
            "file": item.name,
            "page": "" if card.get("page") is None else str(card.get("page")),
            "basic": _eps(scale, card.get("basic_eps")),
            "diluted": _eps(scale, card.get("diluted_eps")),
            "bare": _eps(scale, card.get("unlabeled_eps")),
            "add": card.get("add") or "",
            "div": card.get("div") or "",
            "annual": card.get("state") or "",
        })
    return {"folder": str(folder), "present": True, "rows": rows, "skipped": skipped}


def selftest() -> list[str]:
    fails = []
    check = _load(CHECK, "stmt108")
    good = check.from_text("\n".join([
        "Revenue 80 100",
        "Cost of revenue 30 40",
        "Gross profit 50 60",
        "Gross margin 62.5% 60%",
        "Basic EPS 8 10",
        "Diluted EPS 7 9",
    ]))
    bare = check.from_text("EPS 5.2")
    if good["basic_eps"] != 10 or good["diluted_eps"] != 9 or good["unlabeled_eps"] is not None:
        fails.append("split")
    if bare["unlabeled_eps"] != 5.2 or bare["basic_eps"] is not None or bare["diluted_eps"] is not None:
        fails.append("bare")
    seen = {"state": "SEEN", "basic_eps": 10, "diluted_eps": 9, "add": "OK", "div": "OK"}
    if row_lamp(seen) != "GREEN" or row_lamp({"state": "NODATA"}) != "YELLOW":
        fails.append("lamp")
    if row_lamp({"state": "SEEN", "basic_eps": None, "diluted_eps": None, "unlabeled_eps": 5}) != "YELLOW":
        fails.append("unsplit")
    if row_lamp({"state": "SEEN", "basic_eps": 10, "diluted_eps": 9, "add": "FAIL", "div": "OK"}) != "RED":
        fails.append("add")
    return fails


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    fails = selftest()
    book = measure()
    cols = ["lamp", "file", "page", "basic", "diluted", "bare", "add", "div", "annual"]
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in book["rows"]:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    annual = "NODATA" if not book["present"] else ("SEEN" if any(row["annual"] == "SEEN" for row in book["rows"]) else "NODATA")
    errors = [
        {"lamp": "GREEN" if not fails else "RED", "check": "split", "detail": "basic and diluted stay apart"},
        {"lamp": "YELLOW" if annual != "SEEN" else "GREEN", "check": "annual", "detail": annual},
        {"lamp": "YELLOW", "check": "paddle", "detail": "ABSENT not called"},
        {"lamp": "GREEN", "check": "quote", "detail": "not refetched"},
    ]
    if not book["present"]:
        errors.append({"lamp": "YELLOW", "check": "folder", "detail": book["folder"]})
    print("STATEMENT")
    print(_fit(book["rows"], cols) if book["rows"] else "(no stock pdf)")
    print("ERROR")
    print(_fit(errors, ["lamp", "check", "detail"]))
    open_rows = [row for row in book["rows"] if row["lamp"] != "GREEN"]
    focus = [row for row in book["rows"] if "2330" in row["file"]]
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_StatementCheck_v0100",
        "selftest": "FAIL" if fails else "OK",
        "fails": fails,
        "folder": book["folder"],
        "present": book["present"],
        "stock_pdf": len(book["rows"]),
        "skipped_non_stock": book["skipped"],
        "counts": counts,
        "focus": focus[:8],
        "open": open_rows[:24],
        "errors": errors,
        "do_not": [
            "refetch the locked close",
            "fill basic and diluted with the same EPS",
            "parse non-stock reports",
            "call paddle",
        ],
        "next": "none",
    }
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
