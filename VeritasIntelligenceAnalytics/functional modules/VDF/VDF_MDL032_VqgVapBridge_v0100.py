#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only bridge from the isolated VDF system to VQG and VAP.

Reads the indicator register, the formula table still stored in VQG code,
the latest VAP engine tail of each family, and the sealed chart library.
VDF fetches into Parquet. VQG reads that store, then defines, calculates,
backtests and verifies. VAP only presents templates and the chart library.

  py -3 VDF_MDL032_VqgVapBridge_v0100.py catalog
  py -3 VDF_MDL032_VqgVapBridge_v0100.py spec VQG.IND.RSI
  py -3 VDF_MDL032_VqgVapBridge_v0100.py selftest
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = HERE / "intake" / "vap_core_ssot"
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


def _official() -> dict:
    boundary = json.loads((PIN / "boundary.json").read_text(encoding="utf-8"))
    library = json.loads((PIN / "vap_chartlib.json").read_text(encoding="utf-8"))
    spec = json.loads((PIN / "vap_spec.json").read_text(encoding="utf-8"))
    request = json.loads((PIN / "first_chart_request.json").read_text(encoding="utf-8"))
    charts = [chart for group in library.get("groups") or [] for chart in group.get("charts") or []]
    codes = [chart.get("code") for chart in charts]
    problems = []
    expected = {"VAP-CH-%02d" % i for i in range(1, 29)}
    if set(codes) != expected or len(codes) != 28:
        problems.append("official chart library is not the sealed 28")
    first = next((chart for chart in charts if chart.get("code") == "VAP-CH-01"), None)
    if not first or first.get("fields") != ["date", "value"] or first.get("axes") != 1 or first.get("dataShape") != "series[]":
        problems.append("VAP-CH-01 is not date,value series")
    if spec.get("$schema") != "VIA-VAP-SPEC/1.0" or library.get("$schema") != "VIA-VAP-CHARTLIB/1.0":
        problems.append("spec schema drifted")
    if request.get("parameters", {}).get("date_field") != "date" or request.get("parameters", {}).get("value_field") != "value":
        problems.append("first chart request does not bind date and value")
    if boundary.get("flow") != ["VDF", "PARQUET", "VQG", "VAP"] or boundary.get("store", {}).get("format") != "parquet":
        problems.append("role boundary drifted")
    if "real_quantguard" not in boundary.get("not_verified", []) or boundary.get("test_only_provider_is_deliverable") is not False:
        problems.append("verification overclaims QuantGuard")
    sibling = VAP / "intake" / "VAP_Core_SSOT_Bootstrap_v1" / "ssot" / "vap_chartlib.json"
    if sibling.is_file():
        other = json.loads(sibling.read_text(encoding="utf-8"))
        if other != library:
            problems.append("VAP intake chart library differs from the pin")
    return {
        "charts": charts,
        "boundary": boundary,
        "hashes": {
            "chartlib": hashlib.sha256((PIN / "vap_chartlib.json").read_bytes()).hexdigest(),
            "spec": hashlib.sha256((PIN / "vap_spec.json").read_bytes()).hexdigest(),
        },
        "problems": problems,
    }


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
    official = _official()
    errors.extend(official["problems"])
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
        "official_charts": official["charts"],
        "boundary": official["boundary"],
        "hashes": official["hashes"],
        "errors": errors,
        "state": "ERROR" if errors else "REGISTERED",
    }


def catalog(book=None) -> int:
    book = book or build()
    print("state=%s flow=%s indicators=%d official_charts=%d gallery=%d vap_engines=%d gaps=%d" % (
        book["state"], ">".join(book["boundary"]["flow"]), len(book["indicators"]),
        len(book["official_charts"]), len(book["charts"]), len(book["engines"]), len(book["gaps"])))
    print("not_verified", " ".join(book["boundary"]["not_verified"]))
    for err in book["errors"]:
        print("ERROR", err)
    return 0 if book["state"] == "REGISTERED" else 1


def spec(key: str, book=None) -> int:
    book = book or build()
    hits = [row for row in book["indicators"] if key in row["stable_id"] or key == row.get("code_key")]
    hits += [row for row in book["official_charts"] if key in (row.get("code"), row.get("id"))]
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
    if len(book["official_charts"]) != 28 or book["boundary"]["flow"] != ["VDF", "PARQUET", "VQG", "VAP"]:
        print("[FAIL] roles", book["boundary"]["flow"])
        return 1
    if "read_parquet" not in book["boundary"]["roles"]["VAP"]["does_not"]:
        print("[FAIL] VAP must not read the parquet store")
        return 1
    if book["boundary"]["roles"]["VQG"]["does"][0] != "read_parquet":
        print("[FAIL] VQG must read parquet")
        return 1
    if len(book["engines"]) + len(book["gaps"]) != 16:
        print("[FAIL] roster", len(book["engines"]), book["gaps"])
        return 1
    print("[OK] VDF > PARQUET > VQG > VAP · charts=%d gallery=%d" % (
        len(book["official_charts"]), len(book["charts"])))
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
