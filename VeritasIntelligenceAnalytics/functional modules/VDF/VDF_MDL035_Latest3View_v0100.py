#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast local view: latest three values per source, names through the synonym gate.

A term that already points at two ids is not compared and is not written
back into the locked synonym book.

  py -3 VDF_MDL035_Latest3View_v0100.py selftest
"""
from __future__ import annotations

import html
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output_hub" / "mega" / "name_check"
TOL = {"abs": 0.05, "pct": 1.0}


def _mod(file: str, name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def within(a: float, b: float) -> bool:
    gap = abs(a - b)
    return gap <= TOL["abs"] or (b != 0 and gap / abs(b) * 100.0 <= TOL["pct"])


def _canon(term: str, gate: dict):
    rows = gate["index"].get(str(term).strip().casefold(), [])
    seen = []
    for row in rows:
        item = (row["system"], row["id"])
        if item not in seen:
            seen.append(item)
    by = {}
    for system, canonical in seen:
        by.setdefault(system, set()).add(canonical)
    if any(len(ids) > 1 for ids in by.values()):
        return None, "RED"
    if len(seen) > 1:
        return None, "YELLOW"
    if len(seen) == 1:
        return seen[0][1], "GREEN"
    return str(term).strip(), "UNLISTED"


def check(rows: list, gate=None) -> dict:
    gate = gate or _mod("VDF_MDL033_TermGate_v0100.py", "vdf_terms").build()
    skipped, buckets = [], {}
    for row in rows:
        canonical, lamp = _canon(row["name"], gate)
        if lamp in ("RED", "YELLOW"):
            skipped.append({"name": row["name"], "lamp": lamp})
            continue
        buckets.setdefault(canonical, {}).setdefault(row["source"], {})[row["period"]] = float(row["value"])
    series = []
    for canonical, sources in buckets.items():
        latest = {src: dict(sorted(vals.items())[-3:]) for src, vals in sources.items()}
        periods = sorted({p for vals in latest.values() for p in vals})[-3:]
        diffs = []
        for period in periods:
            vals = {src: latest[src][period] for src in latest if period in latest[src]}
            if len(vals) < 2:
                continue
            base = next(iter(vals.values()))
            if any(not within(v, base) for v in vals.values()):
                diffs.append(period)
        verdict = "SINGLE" if len(latest) < 2 else ("DIFF" if diffs else "AGREE")
        series.append({"id": canonical, "verdict": verdict, "latest": latest, "periods": periods})
    collisions = len(gate["collisions"])
    lamp = "RED" if any(row["verdict"] == "DIFF" for row in series) or skipped else (
        "YELLOW" if any(row["verdict"] != "AGREE" for row in series) or collisions else "GREEN")
    return {"series": series, "skipped": skipped, "collisions": collisions, "lamp": lamp}


def render(book: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ["<h1>最新三值</h1>", "<p>燈 %s · 同義字衝突 %d 組不參與比對</p>" % (book["lamp"], book["collisions"])]
    body.append("<table><tr><th>名稱</th><th>判決</th><th>來源</th><th>近三期</th></tr>")
    for row in book["series"]:
        for source, vals in row["latest"].items():
            shown = " · ".join("%s=%s" % (k, vals[k]) for k in row["periods"] if k in vals)
            body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(row["id"]), row["verdict"], html.escape(source), html.escape(shown)))
    for row in book["skipped"]:
        body.append("<tr><td>%s</td><td>%s</td><td></td><td>名稱衝突，不核對</td></tr>" % (
            html.escape(row["name"]), row["lamp"]))
    body.append("</table>")
    path.write_text("<!DOCTYPE html><meta charset='utf-8'><title>最新三值</title>" + "".join(body), encoding="utf-8")
    return path


def admit(term: str, canonical: str, system: str, gate=None) -> int:
    gate = gate or _mod("VDF_MDL033_TermGate_v0100.py", "vdf_terms").build()
    rows = gate["index"].get(str(term).strip().casefold(), [])
    ids = {row["id"] for row in rows if row["system"] == system}
    if ids and ids != {canonical}:
        print("REFUSE", term, sorted(ids))
        return 2
    print("KEEP", system, canonical, term)
    return 0


def selftest() -> int:
    import tempfile
    gate = _mod("VDF_MDL033_TermGate_v0100.py", "vdf_terms").build()
    before = (HERE / "SSOT" / "VDF_Synonym_SSOT_v0100.json").read_bytes()
    rows = []
    for period, left, right in (("2026-08", 1.0, 1.0), ("2026-09", 1.1, 1.1), ("2026-10", 1.2, 9.9)):
        rows.append({"name": "DGS10", "source": "FRED", "period": period, "value": left})
        rows.append({"name": "DGS10", "source": "AKSHARE", "period": period, "value": right})
    for period, value in (("2026-08", 5), ("2026-09", 5), ("2026-10", 5)):
        rows.append({"name": "買進", "source": "A", "period": period, "value": value})
        rows.append({"name": "Buy", "source": "B", "period": period, "value": value})
    rows.append({"name": "強烈買進", "source": "A", "period": "2026-10", "value": 1})
    book = check(rows, gate)
    by = {row["id"]: row["verdict"] for row in book["series"]}
    if by.get("DGS10") != "DIFF" or by.get("RATING_BUY") != "AGREE":
        print("[FAIL]", by)
        return 1
    if not any(row["name"] == "強烈買進" and row["lamp"] == "RED" for row in book["skipped"]):
        print("[FAIL] conflict not skipped")
        return 1
    if admit("強烈買進", "RATING_BUY", "VDF", gate) != 2 or admit("全新詞不衝突", "RATING_BUY", "VDF", gate) != 0:
        print("[FAIL] admit")
        return 1
    if (HERE / "SSOT" / "VDF_Synonym_SSOT_v0100.json").read_bytes() != before:
        print("[FAIL] synonym book changed")
        return 1
    with tempfile.TemporaryDirectory() as td:
        page = render(book, Path(td) / "latest3.html")
        text = page.read_text(encoding="utf-8")
        if "DIFF" not in text or "RATING_BUY" not in text:
            print("[FAIL] view")
            return 1
    print("[OK] latest3 lamp=%s skipped=%d" % (book["lamp"], len(book["skipped"])))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "selftest"
    if cmd == "selftest":
        return selftest()
    if cmd == "view" and len(argv) > 1:
        book = check(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        print(render(book, OUT / "latest3.html"))
        print("lamp=%s" % book["lamp"])
        return 0
    print("verbs: selftest | view <rows.json>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
