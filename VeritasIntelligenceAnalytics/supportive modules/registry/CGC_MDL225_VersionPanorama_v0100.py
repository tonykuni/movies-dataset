#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panorama of the four live engines. Each one must be a versioned file.

The component inventory is only read. Missing tails are registered in
VIA_EngineVersion_Register_v0100.json. Nothing is fetched.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
BOOK = HERE / "VIA_EngineVersion_Register_v0100.json"
INVENTORY = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
PAGE = VIA / "VIA_Reports" / "vcgc" / "VIA_Version_Matrix_v0100.html"
VERSION = re.compile(r"_v\d+")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _resolved() -> dict[str, str]:
    accel = _load(VIA / "supportive modules" / "SUP_MDL737_SuperAccelModule_v0108.py", "accel_v0108_panorama")
    net = _load(VIA / "supportive modules" / "network" / "SUP_MDL740_NetUnified_v0115.py", "net_v0115_panorama")
    aegis = Path(net._resolve_aegis_path() or "").name
    pinned = accel.CEL_CANDIDATES[-1] if getattr(accel, "CEL_CANDIDATES", ()) else ""
    return {"accelerator": pinned, "network": aegis}


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    inventory = INVENTORY.read_text(encoding="utf-8") if INVENTORY.is_file() else ""
    resolved = _resolved()
    rows = []
    for row in book["rows"]:
        path = VIA / row["path"]
        versioned = bool(VERSION.search(row["file"]))
        exists = path.is_file()
        live = resolved.get(row["family"])
        agrees = live is None or live == row["file"] or row["role"] != "engine"
        if row["family"] == "network" and row["role"] == "engine":
            agrees = live == row["file"]
        if row["family"] == "accelerator" and row["role"] == "engine":
            agrees = live == row["file"]
        lamp = "GREEN" if exists and versioned and agrees else "RED"
        rows.append({
            "lamp": lamp,
            "family": row["family"],
            "role": row["role"],
            "file": row["file"],
            "code": row["code"],
            "versioned": versioned,
            "exists": exists,
            "in_inventory": row["file"] in inventory,
        })
    red = [row["file"] for row in rows if row["lamp"] != "GREEN"]
    return {
        "via": "vcgc",
        "door": "CGC_MDL225_VersionPanorama_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not red and book.get("inventory_edited") is False,
        "page": str(PAGE),
        "rows": rows,
        "resolved": resolved,
        "inventory_edited": False,
        "fetched": False,
        "missing": red,
        "do_not": [
            "overwrite VIA_Component_Inventory_SSOT",
            "registry-sync --apply",
            "retire an old inventory code",
            "import talib",
            "edit intake macro_ssot",
        ],
        "next": "none" if not red else "do not unlock; name the red file",
    }


def write_page(card: dict) -> None:
    body = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (html.escape(row["lamp"]), html.escape(row["family"]), html.escape(row["role"]),
           html.escape(row["file"]), html.escape(row["code"]), "yes" if row["in_inventory"] else "register")
        for row in card["rows"]
    )
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>engine versions</title>
<style>
body{margin:0;background:#121614;color:#d5ddd6;font:11px/1.35 ui-sans-serif,sans-serif}
main{max-width:980px;margin:auto;padding:14px}h1{font-size:14px;margin:0 0 8px}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #2c3832;padding:4px 6px;text-align:left;vertical-align:top;word-break:break-word}
td:first-child{font-weight:700}
</style><main><h1>ENGINE VERSION MATRIX</h1>
<table><tr><th>lamp</th><th>family</th><th>role</th><th>file</th><th>code</th><th>book</th></tr>__ROWS__</table>
</main></html>"""
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(text.replace("__ROWS__", body), encoding="utf-8")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    before = INVENTORY.read_bytes()
    card = check()
    ok = denied and card["lock_success"] and INVENTORY.read_bytes() == before
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
