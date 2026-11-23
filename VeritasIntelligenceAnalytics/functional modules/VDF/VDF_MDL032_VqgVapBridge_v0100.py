#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only bridge from the isolated VDF system to VQG and VAP.

Reads the indicator register, the formula table still stored in VQG code,
the latest VAP engine tail of each family, and the chart spec. It does not
import those engines and it does not write their books.

  py -3 VDF_MDL032_VqgVapBridge_v0100.py catalog
  py -3 VDF_MDL032_VqgVapBridge_v0100.py spec VQG.IND.RSI
  py -3 VDF_MDL032_VqgVapBridge_v0100.py selftest
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODS = HERE.parent
VQG = MODS / "VQG"
VAP = MODS / "VAP"
TAIL = re.compile(r"_v(\d+)")
ENG = re.compile(r"(VAP_ENG\d+)")
NEED = ("stable_id", "no", "category", "name_zh", "formula", "time_params", "kind")
VAP_ROSTER = ["VAP_ENG%03d" % i for i in range(1, 17)]


def _latest(paths, family):
    best = {}
    for path in paths:
        fam = family.search(path.name)
        ver = TAIL.search(path.name)
        if not fam or not ver:
            continue
        key, num = fam.group(1), int(ver.group(1))
        if key not in best or num > best[key][0]:
            best[key] = (num, path)
    return best


def _book(pattern: str, root: Path) -> Path:
    hits = sorted(root.glob(pattern))
    if not hits:
        raise RuntimeError("missing " + pattern)
    return hits[-1]


def _core() -> tuple:
    merged, sources = {}, []
    for path in sorted(VQG.glob("VQG_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            if not isinstance(value, dict) or not value:
                continue
            if not all(isinstance(item, dict) and "stable_id" in item and "formula" in item for item in value.values()):
                continue
            merged.update(value)
            sources.append(path.name)
    if not merged:
        raise RuntimeError("VQG formulas absent")
    return sources, merged


def build() -> dict:
    errors = []
    register_path = _book("VQG_IndicatorRegister_SSOT_v*.json", VQG)
    register = json.loads(register_path.read_text(encoding="utf-8"))
    entries = register.get("entries") or []
    ids, nos = {}, {}
    for row in entries:
        for field in NEED:
            if not str(row.get(field) or "").strip():
                errors.append("empty %s %s" % (row.get("stable_id"), field))
        if row.get("kind") == "indicator" and not isinstance(row.get("params"), list):
            errors.append("params not a list " + str(row.get("stable_id")))
        ids[row.get("stable_id")] = ids.get(row.get("stable_id"), 0) + 1
        nos[row.get("no")] = nos.get(row.get("no"), 0) + 1
    errors += ["duplicate id " + key for key, n in ids.items() if n > 1]
    errors += ["duplicate no " + key for key, n in nos.items() if n > 1]
    known = set(ids)
    for row in entries:
        for alt in row.get("alternatives") or []:
            if str(alt).startswith("VQG.") and alt not in known:
                errors.append("missing alternative %s" % alt)
    declared = register.get("counts") or {}
    by_kind = {}
    for row in entries:
        by_kind[row.get("kind")] = by_kind.get(row.get("kind"), 0) + 1
    if declared.get("total") != len(entries):
        errors.append("count total %s != %d" % (declared.get("total"), len(entries)))
    for kind, n in by_kind.items():
        if declared.get(kind) != n:
            errors.append("count %s %s != %d" % (kind, declared.get(kind), n))

    core_sources, core = _core()
    live = {row.get("code_key"): row for row in entries if row.get("kind") == "indicator" and row.get("implemented", True)}
    for key, spec in core.items():
        row = live.get(key)
        if row is None:
            errors.append("code without a register row " + key)
            continue
        if row.get("stable_id") != spec.get("stable_id") or row.get("formula") != spec.get("formula"):
            errors.append("formula drifted " + key)
    for key in live:
        if key not in core:
            errors.append("register without code " + key)

    engines = []
    for fam, (num, path) in sorted(_latest((VAP / "engine").glob("VAP_ENG*.py"), ENG).items()):
        engines.append({"id": fam, "version": "v%04d" % num, "file": path.name})
    present = {row["id"]: row for row in engines}
    gaps = [{"id": fam, "reason": "no file in VAP/engine"} for fam in VAP_ROSTER if fam not in present]

    spec_path = _book("vap_spec.json", VAP / "spec" / "ssot")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    sections = [key for key in spec if key not in ("$schema", "meta", "changelog")]
    if "price" not in sections or "line" not in sections:
        errors.append("vap spec missing price or line")

    chart_path = _book("VIA_VAP_All_Chart_Specs_v*.json", VAP / "spec")
    charts_doc = json.loads(chart_path.read_text(encoding="utf-8"))
    charts = []
    for row in charts_doc.get("charts") or []:
        if not row.get("id") or not row.get("code"):
            errors.append("chart missing id")
            continue
        charts.append({"id": row["id"], "code": row["code"], "zh": row.get("zh") or ""})
    if len(charts) < 40:
        errors.append("charts %d" % len(charts))

    indicators = [row for row in entries if row.get("kind") == "indicator"]
    return {
        "register": register_path.name,
        "indicators": indicators,
        "entries": len(entries),
        "by_kind": by_kind,
        "core": core_sources,
        "engines": engines,
        "gaps": gaps,
        "spec_sections": sections,
        "charts": charts,
        "errors": errors,
        "state": "ERROR" if errors else "REGISTERED",
    }


def catalog(book=None) -> int:
    book = book or build()
    print("state=%s indicators=%d entries=%d vap_engines=%d gaps=%d charts=%d sections=%d" % (
        book["state"], len(book["indicators"]), book["entries"], len(book["engines"]),
        len(book["gaps"]), len(book["charts"]), len(book["spec_sections"])))
    for err in book["errors"]:
        print("ERROR", err)
    return 0 if book["state"] == "REGISTERED" else 1


def spec(key: str, book=None) -> int:
    book = book or build()
    hits = [row for row in book["indicators"] if key in row["stable_id"] or key == row.get("code_key")]
    hits += [row for row in book["charts"] if key in row["id"] or key == row["code"]]
    if not hits:
        print("NONE", key)
        return 1
    for row in hits:
        print(json.dumps(row if "formula" not in row else {
            "stable_id": row["stable_id"], "name_zh": row["name_zh"],
            "formula": row["formula"], "time_params": row["time_params"],
        }, ensure_ascii=False))
    return 0


def selftest() -> int:
    book = build()
    if book["state"] != "REGISTERED":
        print("[FAIL]", book["errors"])
        return 1
    if book["by_kind"].get("indicator") != 19 or book["entries"] != 66:
        print("[FAIL] counts", book["by_kind"], book["entries"])
        return 1
    if not any(row["stable_id"] == "VQG.IND.RSI" for row in book["indicators"]):
        print("[FAIL] RSI")
        return 1
    if not any(row["id"] == "VAP_ENG010" for row in book["engines"]):
        print("[FAIL] chart library engine")
        return 1
    if len(book["engines"]) + len(book["gaps"]) != 16:
        print("[FAIL] roster", len(book["engines"]), book["gaps"])
        return 1
    print("[OK] VQG indicators=%d VAP engines=%d gaps=%d charts=%d" % (
        len(book["indicators"]), len(book["engines"]), len(book["gaps"]), len(book["charts"])))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "catalog"
    if cmd == "selftest":
        return selftest()
    if cmd == "catalog":
        return catalog()
    if cmd == "spec" and len(argv) > 1:
        return spec(argv[1])
    print("verbs: catalog | spec <id> | selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
