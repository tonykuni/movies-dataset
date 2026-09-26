#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read a report folder and open a three-tab HTML result. Unverified rows stay out of Parquet."""
from __future__ import annotations

import html
import json
import os
import re
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DIR = Path(r"C:\測試樣本報告")


def _engine():
    files = sorted(HERE.glob("VIA_VRN_FirstPageEngine_v*.py"))
    if not files:
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("vrn_first", files[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FirstPageEngine()


def _facts(name: str, engine) -> dict:
    if engine is not None:
        try:
            got = engine.filename_facts(name)
            return {"ticker": got.get("ticker") or "", "broker": got.get("broker") or "", "date": got.get("date") or "", "kind": got.get("kind") or "", "by": "filename_facts"}
        except Exception:
            pass
    code = re.search(r"(?<!\d)(\d{4})(?!\d)", name)
    day = re.search(r"(20\d{6})", name)
    broker = name.split("-", 1)[0].split(" ", 1)[0]
    return {"ticker": code.group(1) if code else "", "broker": broker, "date": day.group(1) if day else "", "kind": "", "by": "filename"}


def _page1(path: Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if not reader.pages:
            return ""
        return (reader.pages[0].extract_text() or "")[:4000]
    except Exception:
        return ""


def _rows(folder: Path, engine) -> list[dict]:
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.pdf")):
        facts = _facts(path.name, engine)
        text = _page1(path)
        summary = " ".join(text.split())[:280]
        out.append({
            "file": path.name,
            "ticker": facts["ticker"],
            "broker": facts["broker"],
            "date": facts["date"],
            "kind": facts["kind"],
            "by": facts["by"],
            "fixed_page1": text,
            "summary_page1": summary,
            "financial": "",
            "lamp": "YELLOW" if text else "RED",
            "verified": False,
        })
    return out


def _html(folder: Path, rows: list[dict], data: str) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr><td>{lamp}</td><td>{file}</td><td>{ticker}</td><td>{broker}</td><td>{date}</td><td>{kind}</td></tr>".format(
                lamp=html.escape(row["lamp"]),
                file=html.escape(row["file"]),
                ticker=html.escape(row["ticker"]),
                broker=html.escape(row["broker"]),
                date=html.escape(row["date"]),
                kind=html.escape(row["kind"]),
            )
        )
    pages = []
    for row in rows[:12]:
        pages.append(
            "<article><h3>{file}</h3><div class='pair'><pre>{fixed}</pre><pre>{summary}</pre></div></article>".format(
                file=html.escape(row["file"]),
                fixed=html.escape(row["fixed_page1"] or "NODATA"),
                summary=html.escape(row["summary_page1"] or "NODATA"),
            )
        )
    table = "\n".join(body) or "<tr><td colspan='6'>資料夾沒有 PDF</td></tr>"
    page = "\n".join(pages) or "<p>NODATA</p>"
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>VRN 三頁實測</title>
<style>
body {{ margin:0; background:#121418; color:#d7dde6; font:13px/1.45 "Segoe UI",sans-serif; }}
header {{ padding:10px 14px; border-bottom:1px solid #2a3140; }}
nav label {{ display:inline-block; padding:8px 12px; }}
input {{ display:none; }}
#t1:checked ~ main .p1, #t2:checked ~ main .p2, #t3:checked ~ main .p3 {{ display:block; }}
main section {{ display:none; padding:12px 14px; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ border-bottom:1px solid #2a3140; padding:4px 6px; text-align:left; vertical-align:top; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
pre {{ white-space:pre-wrap; background:#0e1116; padding:8px; max-height:280px; overflow:auto; }}
small {{ color:#8b97a8; }}
</style></head><body>
<input id="t1" type="radio" name="tab" checked>
<input id="t2" type="radio" name="tab">
<input id="t3" type="radio" name="tab">
<header>VRN 三頁實測 <small>{html.escape(str(folder))} · 未驗證 · 不入庫 · {html.escape(data)}</small></header>
<nav><label for="t1">BASIC INFO</label><label for="t2">PAGE 1</label><label for="t3">FINANCIAL DATA</label></nav>
<main>
<section class="p1"><table><tr><th>燈</th><th>檔</th><th>代碼</th><th>券商</th><th>日期</th><th>型別</th></tr>
{table}</table></section>
<section class="p2">{page}</section>
<section class="p3"><p>FINANCIAL DATA 尚未逐科目驗證。這頁不把空白填成數字，也不寫入 Parquet。</p></section>
</main></body></html>
"""


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    engine = None
    why = ""
    try:
        engine = _engine()
    except Exception as exc:
        why = type(exc).__name__
    rows = _rows(folder, engine)
    data_root.mkdir(parents=True, exist_ok=True)
    page = data_root / "VRN_TabReport.html"
    page.write_text(_html(folder, rows, str(data_root)), encoding="utf-8")
    if open_page and page.is_file():
        webbrowser.open(page.as_uri())
    return {
        "via": "vcgc",
        "door": "VRN_ENG110_TabReport_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "folder": str(folder),
        "present": folder.is_dir(),
        "pdf": len(rows),
        "text": sum(1 for row in rows if row["fixed_page1"]),
        "facts": rows[0]["by"] if rows else "",
        "engine_error": why,
        "page": str(page),
        "opened": open_page,
        "written": 0,
        "verified": 0,
        "hub_edited": False,
        "intake_edited": False,
        "do_not": ["write an unverified tab", "invent a financial value", "edit intake macro_ssot"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path(os.environ.get("VIA_VRN_SAMPLES", str(DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, os.environ.get("VIA_NO_OPEN") != "1")
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["present"] else 2


def selftest() -> int:
    folder = Path("/tmp/vrn_sample_reports")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "JP-2330 20250718.pdf").write_bytes(b"%PDF-1.1\n")
    os.environ["VIA_NO_OPEN"] = "1"
    card = run(folder, Path("/tmp/vrn_sample_out"), False)
    text = Path(card["page"]).read_text(encoding="utf-8")
    ok = card["written"] == 0 and card["pdf"] == 1 and "2330" in text and "FINANCIAL DATA" in text and "BASIC INFO" in text
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
