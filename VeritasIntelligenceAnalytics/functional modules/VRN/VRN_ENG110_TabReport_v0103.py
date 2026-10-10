#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three page-1 readers, the locked columns, and the store gate. Nothing is invented."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGIC = HERE / "references" / "intake" / "VIA_VRNLogic_AllInOne_v0201_b504" / "VIA_VRNLogic_AllInOne_v0201.py"
DEFAULT_DIR = Path(r"C:\測試樣本報告")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_fitz(path: Path) -> tuple[str, str]:
    try:
        try:
            import fitz
        except ImportError:
            import pymupdf as fitz
        with fitz.open(str(path)) as doc:
            if not doc.page_count:
                return "", "empty"
            return (doc[0].get_text("text") or "").strip(), ""
    except Exception as exc:
        return "", type(exc).__name__


def _read_pypdf(path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if not reader.pages:
            return "", "empty"
        return (reader.pages[0].extract_text() or "").strip(), ""
    except Exception as exc:
        return "", type(exc).__name__


def _read_plumber(path: Path) -> tuple[str, str]:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as doc:
            if not doc.pages:
                return "", "empty"
            return (doc.pages[0].extract_text() or "").strip(), ""
    except Exception as exc:
        return "", type(exc).__name__


def read_page1(path: Path) -> tuple[str, str, list[str]]:
    errors = []
    for name, reader in (("fitz", _read_fitz), ("pypdf", _read_pypdf), ("pdfplumber", _read_plumber)):
        text, err = reader(path)
        if text:
            return text, name, errors
        if err:
            errors.append(f"{name}:{err}")
    return "", "", errors


def _logic():
    return _load(LOGIC, "vrn_logic_gate")


def _facts_engine():
    files = sorted(HERE.glob("VIA_VRN_FirstPageEngine_v*.py"))
    if not files:
        return None
    try:
        return _load(files[-1], "vrn_facts_gate").FirstPageEngine()
    except Exception:
        return None


def _one(path: Path, logic, gate, facts_engine) -> dict:
    text, reader, errors = read_page1(path)
    file_id = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:16]
    basic = {}
    if logic is not None:
        try:
            basic, _validation = logic.build_basic_info(
                file_id=file_id,
                filename=path.name,
                file_size=path.stat().st_size,
                first_page_text=text,
                pages=1,
            )
        except Exception:
            basic = {}
    facts = {}
    if facts_engine is not None:
        try:
            facts = facts_engine.filename_facts(path.name)
        except Exception:
            facts = {}
    page = {"fileId": file_id, "fileName": path.name, "page": 1 if text else "", "fixed_page1": text, "summary_page1": ""}
    mapped = gate.map_report(basic, page, [])
    return {
        "file": path.name,
        "reader": reader,
        "errors": errors,
        "chars": len(text),
        "basic": basic,
        "page": page,
        "facts_ticker": str(facts.get("ticker") or ""),
        "why": mapped["why"],
    }


def _table(rows: list[dict], fields: list[str], pick) -> str:
    head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
    body = []
    for row in rows:
        values = pick(row)
        body.append("<tr>" + "".join(f"<td>{html.escape(str(values.get(field, '')))}</td>" for field in fields) + "</tr>")
    return f"<table><tr>{head}</tr>{''.join(body) or '<tr><td>NODATA</td></tr>'}</table>"


def _html(folder: Path, rows: list[dict], fields: dict) -> str:
    basic = _table(rows, fields["basic"], lambda row: row["basic"])
    page = _table(rows, fields["page"], lambda row: row["page"])
    financial = "<p>沒有驗證過的財報列。空白不補數字。</p><table><tr>" + "".join(f"<th>{html.escape(field)}</th>" for field in fields["financial"]) + "</tr></table>"
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>VRN 三頁</title>
<style>
body {{ margin:0; background:#121418; color:#d7dde6; font:12px/1.4 "Segoe UI",sans-serif; }}
header,nav {{ padding:8px 12px; border-bottom:1px solid #2a3140; }}
input {{ display:none; }}
#t1:checked ~ main .p1, #t2:checked ~ main .p2, #t3:checked ~ main .p3 {{ display:block; }}
main section {{ display:none; padding:10px 12px; overflow:auto; }}
table {{ border-collapse:collapse; width:max-content; max-width:100%; }}
th,td {{ border-bottom:1px solid #2a3140; padding:3px 6px; text-align:left; vertical-align:top; max-width:420px; }}
td {{ white-space:pre-wrap; }}
</style></head><body>
<input id="t1" type="radio" name="tab" checked><input id="t2" type="radio" name="tab"><input id="t3" type="radio" name="tab">
<header>VRN 三頁 · {html.escape(str(folder))} · 未入庫</header>
<nav><label for="t1">BASIC INFO</label><label for="t2">PAGE 1</label><label for="t3">FINANCIAL DATA</label></nav>
<main><section class="p1">{basic}</section><section class="p2">{page}</section><section class="p3">{financial}</section></main>
</body></html>"""


def _open(page: Path) -> tuple[bool, str]:
    if not sys.platform.startswith("win"):
        return False, "not-windows"
    done = subprocess.call(["cmd", "/c", "start", "", str(page)])
    return done == 0, "cmd"


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    store = _load(HERE / "VRN_ENG109_TabStore_v0100.py", "tab_store_report")
    gate = _load(HERE / "VRN_ENG109_GateMap_v0100.py", "gate_map_report")
    logic = None
    logic_error = ""
    try:
        logic = _logic()
    except Exception as exc:
        logic_error = type(exc).__name__
    facts_engine = _facts_engine()
    rows = [_one(path, logic, gate, facts_engine) for path in sorted(folder.glob("*.pdf"))] if folder.is_dir() else []
    data_root.mkdir(parents=True, exist_ok=True)
    page = data_root / "VRN_TabReport.html"
    fields = {"basic": list(store.BASIC), "page": ["fileId", "fileName", "page", "fixed_page1", "summary_page1"], "financial": list(store.FINANCIAL)}
    page.write_text(_html(folder, rows, fields), encoding="utf-8")
    opened, how = _open(page) if open_page else (False, "")
    why = Counter(item for row in rows for item in row["why"])
    readers = Counter(row["reader"] or "none" for row in rows)
    first_error = next((item for row in rows for item in row["errors"]), "")
    mismatch = sum(1 for row in rows if row["facts_ticker"] and row["basic"].get("ticker") not in {"", "—", row["facts_ticker"]})
    return {
        "via": "vcgc",
        "door": "VRN_ENG110_TabReport_v0103",
        "enter": "vcgc",
        "exit": "vcgc",
        "folder": str(folder),
        "present": folder.is_dir(),
        "pdf": len(rows),
        "text": sum(1 for row in rows if row["chars"]),
        "readers": dict(readers),
        "reader_error": first_error,
        "logic_error": logic_error,
        "ticker_mismatch": mismatch,
        "why": dict(why),
        "page": str(page),
        "opened": opened,
        "open_how": how,
        "columns": {name: len(values) for name, values in fields.items()},
        "written": 0,
        "verified": 0,
        "hub_edited": False,
        "intake_edited": False,
        "do_not": ["invent a financial value", "use a later page as page 1", "copy the page into the summary", "edit intake macro_ssot"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["present"] else 2


def selftest() -> int:
    import fitz
    folder = Path("/tmp/vrn_v0103")
    folder.mkdir(parents=True, exist_ok=True)
    good = folder / "JP-2330 20250718.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Target price discussed after the company visit.")
    doc.save(good)
    doc.close()
    (folder / "broken.pdf").write_bytes(b"not a pdf")
    card = run(folder, Path("/tmp/vrn_v0103_out"), False)
    text = Path(card["page"]).read_text(encoding="utf-8")
    ok = (
        card["text"] == 1
        and card["written"] == 0
        and card["readers"].get("fitz") == 1
        and "financial_empty" in card["why"]
        and card["columns"] == {"basic": 22, "page": 5, "financial": 14}
        and "summary_page1" in text
        and "validationStatus" in text
        and card["reader_error"] != ""
    )
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
