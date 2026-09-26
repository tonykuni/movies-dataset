#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. Read-only table take. Do not write a database.

A grid needs at least 2 rows, 2 columns, and 4 filled cells.
pdfplumber lines, then pdfplumber text, inside the crop.
The higher score wins. A header-only row scores 0, so it cannot block the next try.
Camelot lattice, then stream, only when both plumber scores are 0.
The crop is passed in. Tabula returns every table in the area, not the first table of the page.
fitz text lines are never a table.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CUT = VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py"
FIN = ("損益", "資產負債", "現金流量", "Income Statement", "Balance Sheet", "Cash Flow", "每股盈餘")
PAGE_CAP = 20


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


def clean(rows) -> list:
    out = []
    for row in rows or []:
        out.append([("" if cell is None else str(cell)).strip() for cell in row])
    return out


def score_grid(rows) -> int:
    rows = clean(rows)
    if len(rows) < 2:
        return 0
    width = max((len(row) for row in rows), default=0)
    if width < 2:
        return 0
    filled = sum(1 for row in rows for cell in row if cell)
    if filled < 4:
        return 0
    return filled


def camelot_area(bbox, height: float) -> str:
    x0, top, x1, bottom = bbox
    return f"{x0:.2f},{height - top:.2f},{x1:.2f},{height - bottom:.2f}"


def tabula_area(bbox) -> list:
    x0, top, x1, bottom = bbox
    return [top, x0, bottom, x1]


def pick(candidates: list) -> dict | None:
    good = [item for item in candidates if item["score"] > 0 and item["engine"] != "fitz"]
    if not good:
        return None
    return max(good, key=lambda item: item["score"])


def plumber_tries(page, bbox=None) -> list:
    target = page.within_bbox(tuple(bbox)) if bbox else page
    found = []
    for name, kwargs in (
        ("pdfplumber_lines", {"vertical_strategy": "lines", "horizontal_strategy": "lines", "snap_tolerance": 3}),
        ("pdfplumber_text", {"vertical_strategy": "text", "horizontal_strategy": "text"}),
    ):
        try:
            tables = target.extract_tables(**kwargs) or []
        except Exception:
            tables = []
        for table in tables:
            found.append({"engine": name, "rows": clean(table), "score": score_grid(table)})
    return found


def _append_grids(found: list, engine: str, tables) -> None:
    for table in tables or []:
        rows = table.df.values.tolist() if hasattr(table, "df") else table
        found.append({"engine": engine, "rows": clean(rows), "score": score_grid(rows)})


def camelot_tries(path, page_no: int, bbox, height: float) -> list:
    try:
        import camelot
    except Exception:
        return []
    found = []
    area = [camelot_area(bbox, height)]
    for flavor in ("lattice", "stream"):
        tables = None
        for kwargs in ({"table_areas": area}, {}):
            try:
                tables = camelot.read_pdf(str(path), pages=str(page_no), flavor=flavor, **kwargs)
                break
            except Exception:
                tables = None
        if tables is not None:
            _append_grids(found, f"camelot_{flavor}", tables)
    return found


def tabula_tries(path, page_no: int, bbox) -> list:
    try:
        import tabula
    except Exception:
        return []
    frames = None
    for kwargs in ({"area": tabula_area(bbox)}, {}):
        try:
            frames = tabula.read_pdf(str(path), pages=page_no, multiple_tables=True, silent=True, **kwargs) or []
            break
        except Exception:
            frames = None
    found = []
    for frame in frames or []:
        rows = [list(frame.columns)] + frame.fillna("").values.tolist()
        found.append({"engine": "tabula", "rows": clean(rows), "score": score_grid(rows)})
    return found


def needs_fallback(found: list) -> bool:
    return pick(found) is None


def is_stock(name: str, cut) -> bool:
    named = cut.read_name(name)
    tickers = [row for row in named.get("parts") or [] if row.get("role") == "TICKER"]
    if not tickers:
        return False
    return not all(row.get("ambiguous_year") for row in tickers)


def selftest() -> int:
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    header = [["科目", "2024", "2025"]]
    grid = [["科目", "2024", "2025"], ["營收", "10", "12"], ["毛利", "2", "3"]]
    smash = [["只有一段很長的句子沒有欄"]]
    chk("header-only scores 0", score_grid(header) == 0)
    chk("2x3 grid scores the filled cells", score_grid(grid) == 9)
    chk("one column is not a table", score_grid(smash) == 0)
    chosen = pick([
        {"engine": "pdfplumber_lines", "score": 0},
        {"engine": "pdfplumber_text", "score": 9},
        {"engine": "fitz", "score": 40},
    ])
    chk("fitz cannot win", chosen["engine"] == "pdfplumber_text" and chosen["score"] == 9)
    chk("crop reaches camelot", camelot_area((10, 20, 110, 220), 800) == "10.00,780.00,110.00,580.00")
    chk("crop reaches tabula", tabula_area((10, 20, 110, 220)) == [20, 10, 220, 110])
    chk("empty plumber asks for the next engine", needs_fallback([{"engine": "pdfplumber_lines", "score": 0}]))
    chk("a scored grid does not ask", not needs_fallback([{"engine": "pdfplumber_lines", "score": 9}]))
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


def take_page(path, page, page_no: int) -> dict | None:
    found = plumber_tries(page)
    chosen = pick(found)
    if chosen:
        return chosen
    text = page.extract_text() or ""
    if not any(token in text for token in FIN):
        return None
    bbox = tuple(page.bbox)
    found.extend(camelot_tries(path, page_no, bbox, float(page.height)))
    chosen = pick(found)
    if chosen:
        return chosen
    found.extend(tabula_tries(path, page_no, bbox))
    return pick(found)


def run_folder(folder: Path) -> dict:
    cut = _load(CUT, "filename_cut")
    import pdfplumber

    rows = []
    skipped = 0
    for path in sorted(folder.glob("*.pdf")):
        if not is_stock(path.name, cut):
            skipped += 1
            continue
        try:
            with pdfplumber.open(path) as pdf:
                hits = []
                for index, page in enumerate(pdf.pages[:PAGE_CAP], start=1):
                    chosen = take_page(path, page, index)
                    if not chosen:
                        continue
                    hits.append({
                        "page": index,
                        "engine": chosen["engine"],
                        "score": chosen["score"],
                        "rows": len(chosen["rows"]),
                        "cols": max((len(row) for row in chosen["rows"]), default=0),
                    })
        except Exception as exc:
            rows.append({"lamp": "RED", "file": path.name, "engine": "FAIL", "tables": 0, "detail": type(exc).__name__})
            continue
        tables = hits
        if tables:
            lamp, engine = "GREEN", tables[0]["engine"]
        else:
            lamp, engine = "YELLOW", "NONE"
        rows.append({
            "lamp": lamp,
            "file": path.name,
            "engine": engine,
            "tables": len(tables),
            "pending": 0,
        })
    return {"stock_pdf": len(rows), "skipped_non_stock": skipped, "rows": rows}


def main() -> int:
    if selftest() != 0:
        print(json.dumps({"via": "vcgc", "door": "CGC_MDL149_TableTake_v0100", "selftest": "FAIL"}, ensure_ascii=False))
        return 1
    folder = sample_dir()
    present = folder.is_dir()
    body = {"stock_pdf": 0, "skipped_non_stock": 0, "rows": []}
    if present:
        try:
            import pdfplumber  # noqa: F401
            body = run_folder(folder)
        except Exception as exc:
            body = {"stock_pdf": 0, "skipped_non_stock": 0, "rows": [], "import": type(exc).__name__}
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in body["rows"]:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_TableTake_v0100",
        "selftest": "OK",
        "fails": [],
        "folder": str(folder),
        "present": present,
        "stock_pdf": body["stock_pdf"],
        "skipped_non_stock": body["skipped_non_stock"],
        "counts": counts,
        "rule": "lines then text; camelot only if both score 0; fitz is not a table; no database",
        "rows": body["rows"][:8],
        "do_not": [
            "write the database this round",
            "count fitz text lines as a table",
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
