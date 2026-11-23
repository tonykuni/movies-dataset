#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only SDD, regex and synonym gate for the isolated handoff.

VDF, VQG and VAP keep their own words. A shared spelling is listed twice,
not merged into one number. The workflow lamp stays yellow because this
file does not judge runtime evidence.

  py -3 VDF_MDL033_TermGate_v0100.py resolve 買進
  py -3 VDF_MDL033_TermGate_v0100.py sdd
  py -3 VDF_MDL033_TermGate_v0100.py selftest
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SSOT = HERE / "SSOT"
VQG = HERE.parent / "VQG"
PIN = HERE / "intake" / "vap_core_ssot"
FLOW = ("VDF", "PARQUET", "VQG", "VAP")


def _latest(pattern: str) -> Path:
    hits = sorted(SSOT.glob(pattern))
    if not hits:
        raise RuntimeError("missing " + pattern)
    return hits[-1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _add(index: dict, term: str, system: str, canonical: str) -> None:
    key = str(term).strip()
    if not key:
        return
    index.setdefault(key.casefold(), []).append({"term": key, "system": system, "id": canonical})


def build() -> dict:
    errors = []
    regex_book = _load(_latest("VDF_Regex_SSOT_v*.json"))
    synonym_book = _load(_latest("VDF_Synonym_SSOT_v*.json"))
    workflow_book = _load(_latest("VDF_Workflow_SSOT_v*.json"))
    patterns = (regex_book.get("body") or {}).get("regex") or (synonym_book.get("body") or {}).get("regex") or {}
    compiled, broken = {}, []
    for name, spec in patterns.items():
        pattern = spec.get("pattern") if isinstance(spec, dict) else None
        if not pattern:
            broken.append(name)
            continue
        try:
            compiled[name] = {"re": re.compile(pattern), "locked": bool(spec.get("locked")), "owner": spec.get("owner") or "VDF"}
        except re.error:
            broken.append(name)
            if spec.get("locked"):
                errors.append("locked regex does not compile " + name)
    groups = (synonym_book.get("body") or {}).get("synonyms") or {}
    index = {}
    for canonical, names in groups.items():
        if isinstance(names, list):
            for name in names:
                _add(index, name, "VDF", canonical)
            _add(index, canonical, "VDF", canonical)
    register = _load(sorted(VQG.glob("VQG_IndicatorRegister_SSOT_v*.json"))[-1])
    for row in register.get("entries") or []:
        sid = row.get("stable_id")
        if not sid:
            continue
        for field in ("stable_id", "code_key", "name_zh", "name_en"):
            if row.get(field):
                _add(index, row[field], "VQG", sid)
    library = _load(PIN / "vap_chartlib.json")
    for group in library.get("groups") or []:
        for chart in group.get("charts") or []:
            code = chart.get("code")
            if not code:
                continue
            for field in ("code", "id", "zh", "en"):
                if chart.get(field):
                    _add(index, chart[field], "VAP", code)
    collisions = []
    for key, rows in index.items():
        by_system = {}
        for row in rows:
            by_system.setdefault(row["system"], set()).add(row["id"])
        for system, ids in by_system.items():
            if len(ids) > 1:
                collisions.append({"term": key, "system": system, "ids": sorted(ids)})
    workflows = (workflow_book.get("body") or {}).get("workflows") or []
    codes = [row.get("code") for row in workflows if isinstance(row, dict)]
    if "VDF-WKF001" not in codes:
        errors.append("VDF-WKF001 absent")
    return {
        "patterns": len(compiled),
        "broken": broken,
        "groups": len(groups),
        "terms": len(index),
        "index": index,
        "compiled": compiled,
        "collisions": collisions,
        "workflows": codes,
        "sdd_lamp": "YELLOW",
        "evidence": "未判",
        "errors": errors,
        "state": "ERROR" if errors else "REGISTERED",
    }


def resolve(text: str, book=None) -> int:
    book = book or build()
    rows = book["index"].get(str(text).strip().casefold(), [])
    if not rows:
        print("NONE", text)
        return 1
    seen = []
    for row in rows:
        item = (row["system"], row["id"])
        if item not in seen:
            seen.append(item)
            print("%s %s" % item)
    systems = {item[0] for item in seen}
    same = {}
    for system, canonical in seen:
        same.setdefault(system, set()).add(canonical)
    if any(len(ids) > 1 for ids in same.values()):
        print("lamp=RED")
        return 2
    print("lamp=%s" % ("GREEN" if len(systems) == 1 else "YELLOW"))
    return 0


def match_code(text: str, book=None) -> int:
    book = book or build()
    hits = [name for name, spec in book["compiled"].items() if spec["locked"] and spec["re"].fullmatch(str(text).strip())]
    if not hits:
        print("NONE", text)
        return 1
    for name in hits:
        print("VDF", name)
    print("lamp=%s" % ("GREEN" if len(hits) == 1 else "YELLOW"))
    return 0 if len(hits) == 1 else 2


def sdd(book=None) -> int:
    book = book or build()
    print("sdd_lamp=%s evidence=%s flow=%s workflows=%d" % (
        book["sdd_lamp"], book["evidence"], ">".join(FLOW), len(book["workflows"])))
    return 0 if book["state"] == "REGISTERED" else 1


def selftest() -> int:
    book = build()
    if book["state"] != "REGISTERED":
        print("[FAIL]", book["errors"][:8])
        return 1
    if book["sdd_lamp"] != "YELLOW" or book["evidence"] != "未判":
        print("[FAIL] sdd lamp must stay yellow")
        return 1
    if not book["compiled"]["TW_TICKER_LOCKED"]["re"].fullmatch("2330"):
        print("[FAIL] ticker")
        return 1
    if match_code("2330", book) not in (0, 2):
        print("[FAIL] ticker match")
        return 1
    if resolve("買進", book) != 0 or resolve("rsi", book) != 0 or resolve("VAP-CH-01", book) != 0:
        print("[FAIL] resolve")
        return 1
    if resolve("沒有這個詞", book) != 1 or resolve("強烈買進", book) != 2:
        print("[FAIL] none or collision")
        return 1
    print("[OK] regex=%d synonyms=%d terms=%d collisions=%d sdd=%s" % (
        book["patterns"], book["groups"], book["terms"], len(book["collisions"]), book["sdd_lamp"]))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "sdd"
    if cmd == "selftest":
        return selftest()
    if cmd == "sdd":
        return sdd()
    if cmd == "resolve" and len(argv) > 1:
        return resolve(" ".join(argv[1:]))
    print("verbs: resolve <term> | sdd | selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
