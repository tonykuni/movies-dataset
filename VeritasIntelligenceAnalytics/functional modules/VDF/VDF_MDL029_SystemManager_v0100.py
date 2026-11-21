#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated VDF system manager.

Reads other managers, does not load them.
  VRN synchronizer: run / check / manifest. check does not write.
  VCGC catalog: a missing binding fails the book. REGISTERED only with zero errors.

This file registers the latest VDF engine tail, its commands, and the shared
SSOT parameters. It does not set VIA_NET_CONSENT and it does not launch fetches.

  py -3 VDF_MDL029_SystemManager_v0100.py catalog
  py -3 VDF_MDL029_SystemManager_v0100.py params US_UNRATE
  py -3 VDF_MDL029_SystemManager_v0100.py selftest
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VER = "v0100"
FAMILY = re.compile(r"(VDF_(?:ENG|MDL)\d+)")
TAIL = re.compile(r"_v(\d+)")
ELEC = {f"{i:02d}" for i in range(24, 32)}


def _latest(paths):
    best = {}
    for path in paths:
        fam = FAMILY.search(path.name)
        ver = TAIL.search(path.name)
        if not fam or not ver:
            continue
        key, num = fam.group(1), int(ver.group(1))
        if key not in best or num > best[key][0]:
            best[key] = (num, path)
    return best


def _literal(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise RuntimeError("%s has no %s" % (path.name, name))


def _verbs(path: Path) -> list:
    text = path.read_text(encoding="utf-8", errors="replace")
    found = []
    for verb in ("main", "selftest", "catalog", "fetch", "start"):
        if re.search(r"^def %s\(" % verb, text, re.M):
            found.append(verb)
    return found


def _book(pattern: str) -> Path:
    hits = sorted(HERE.glob(pattern))
    if not hits:
        raise RuntimeError("missing " + pattern)
    return hits[-1]


def build() -> dict:
    errors = []
    engines = []
    commands = []
    seen = set()
    roots = [HERE, HERE / "engine"]
    paths = []
    for root in roots:
        if root.is_dir():
            paths.extend(root.glob("VDF_*.py"))
    for fam, (num, path) in sorted(_latest(paths).items()):
        verbs = _verbs(path)
        engines.append({
            "id": fam,
            "version": "v%04d" % num,
            "file": path.name,
            "commands": verbs,
        })
        for verb in verbs:
            cid = "%s.%s" % (fam, verb)
            if cid in seen:
                errors.append("duplicate command " + cid)
            seen.add(cid)
            commands.append({"id": cid, "engine": fam, "verb": verb, "file": path.name, "writes": verb not in ("selftest", "catalog")})

    groups = json.loads(_book("VDF_FetchGroups_SSOT_v*.json").read_text(encoding="utf-8"))
    universe = json.loads(_book("VDF_InputUniverse_SSOT_v*.json").read_text(encoding="utf-8"))
    pairs = json.loads(_book("VDF_MacroCrossCheck_Pairs_SSOT_v*.json").read_text(encoding="utf-8"))
    industry_hits = sorted((HERE / "engine").glob("VDF_ENG055_*.py"), key=lambda p: int(TAIL.search(p.name).group(1)))
    industry, industry_file = None, None
    for path in reversed(industry_hits):
        try:
            industry = _literal(path, "INDUSTRY_MAP")
            industry_file = path
            break
        except RuntimeError:
            continue
    if industry is None:
        raise RuntimeError("INDUSTRY_MAP absent")

    parameters = []
    for cat in groups.get("categories") or []:
        parameters.append({
            "id": "group." + cat["id"],
            "kind": "fetch_window",
            "value": cat.get("default_start"),
            "source": "VDF_FetchGroups_SSOT",
        })
    for row in universe.get("inputs") or []:
        parameters.append({
            "id": row["id"],
            "kind": "input",
            "value": row.get("code_regex") or row.get("truth"),
            "source": "VDF_InputUniverse_SSOT",
        })
    for pair in pairs.get("pairs") or []:
        parameters.append({
            "id": pair["id"],
            "kind": "crosscheck",
            "akshare": (pair.get("akshare") or {}).get("fn"),
            "official": ((pair.get("official") or {}).get("provider"), (pair.get("official") or {}).get("series")),
            "latest_n": (pairs.get("policy") or {}).get("n_latest"),
            "source": "VDF_MacroCrossCheck_Pairs_SSOT",
        })
    for code in sorted(industry):
        layer = "ELEC" if code in ELEC else "FIN" if code == "17" else "TRAD"
        parameters.append({
            "id": "TW.IND." + code,
            "kind": "industry",
            "layer1": layer,
            "layer2": industry[code],
            "source": industry_file.name,
        })
    for ticker, name in (
        ("^GSPC", "S&P 500"), ("^DJI", "Dow Jones"),
        ("XLK", "Information Technology"), ("XLF", "Financials"),
        ("XLV", "Health Care"), ("XLE", "Energy"), ("XLI", "Industrials"),
        ("XLY", "Consumer Discretionary"), ("XLP", "Consumer Staples"),
        ("XLU", "Utilities"), ("XLRE", "Real Estate"), ("XLB", "Materials"),
        ("XLC", "Communication Services"),
    ):
        parameters.append({
            "id": "US.MKT." + ticker.replace("^", ""),
            "kind": "market_proxy",
            "value": ticker,
            "name": name,
            "source": "VDF_MDL002_ETF_SECTOR_US",
            "note": "Yahoo proxy, not the official sector index",
        })

    ids = [p["id"] for p in parameters]
    if len(ids) != len(set(ids)):
        errors.append("duplicate parameter id")
    if "24" not in industry or industry["24"] != "半導體業":
        errors.append("industry 24 is not semiconductors")
    if not any(p["id"] == "US_UNRATE" for p in parameters):
        errors.append("missing US_UNRATE")
    if "07" in industry or "13" in industry:
        errors.append("retired industry code came back")

    book = {
        "schema": "VDF-SYSTEM-REGISTRY/1.0",
        "manager": "VDF_MDL029_SystemManager_%s" % VER,
        "peers_readonly": {
            "VRN": ["synchronizer run", "synchronizer check", "synchronizer manifest"],
            "VCGC": ["catalog fails when a binding is missing"],
        },
        "engines": len(engines),
        "commands": commands,
        "parameters": parameters,
        "errors": errors,
        "state": "ERROR" if errors else "REGISTERED",
    }
    return book


def catalog(book=None) -> int:
    book = book or build()
    print("state=%s engines=%d commands=%d parameters=%d" % (
        book["state"], book["engines"], len(book["commands"]), len(book["parameters"])))
    if book["errors"]:
        for err in book["errors"]:
            print("ERROR", err)
    return 0 if book["state"] == "REGISTERED" else 1


def params(key: str, book=None) -> int:
    book = book or build()
    hits = [p for p in book["parameters"] if key in p["id"]]
    if not hits:
        print("NONE", key)
        return 1
    for row in hits:
        print(json.dumps(row, ensure_ascii=False))
    return 0


def selftest() -> int:
    book = build()
    if book["state"] != "REGISTERED":
        print("[FAIL]", book["errors"])
        return 1
    out = HERE / "output_hub" / "mega" / "system_registry"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "VDF_SYSTEM_REGISTRY_latest.json"
    path.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    again = json.loads(path.read_text(encoding="utf-8"))
    if again["state"] != "REGISTERED":
        print("[FAIL] reread")
        return 1
    if not any(c["id"] == "VDF_MDL029.selftest" for c in book["commands"]):
        print("[FAIL] own command missing")
        return 1
    print("[OK] REGISTERED engines=%d commands=%d parameters=%d" % (
        book["engines"], len(book["commands"]), len(book["parameters"])))
    print("book=%s" % path)
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "catalog"
    if cmd == "selftest":
        return selftest()
    if cmd == "catalog":
        return catalog()
    if cmd == "params" and len(argv) > 1:
        return params(argv[1])
    print("verbs: catalog | params <id> | selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
