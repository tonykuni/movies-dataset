#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. A dotted register still counts as defining its commands.

v0114 still owns the handover patch. This file does not fetch and does not write a chain report.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PRIOR = HERE / "VDF_SystemManager_v0114.py"
PAGE = VIA / "VIA_Reports" / "vdf_system" / "VDF_Manager_Matrix_v0115.html"
DOT = re.compile(r'Join-Path \$PSScriptRoot "(Register-VIA-Commands-v\d+\.ps1)"')


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _joined(path: Path, seen: set[Path] | None = None) -> str:
    seen = seen or set()
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    found = DOT.search(text)
    older = _joined(path.parent / found.group(1), seen) if found else ""
    return older + "\n" + text


def _body():
    body = _load(PRIOR, "vdf_v0114_for_v0115")._body()
    orig = body._src

    def _src(p):
        path = Path(p) if p else None
        if path and path.name.startswith("Register-VIA-Commands-"):
            return _joined(path)
        return orig(p)

    body._src = _src
    return body


def measure() -> dict:
    body = _body()
    raw = body.collect()
    rows = []
    for name, lamp in (raw.get("lamps") or {}).items():
        domain = raw.get(name) or {}
        why = str(domain.get("why") or (domain.get("chain") or {}).get("why") or domain.get("state") or "")
        rows.append({"lamp": lamp, "lamp_name": name, "why": why[:240]})
    open_rows = [row["lamp_name"] for row in rows if row["lamp"] != "GREEN"]
    launch = raw.get("launch") or {}
    missing = list((launch.get("launchers") or {}).get("cmds_missing") or [])
    out = {
        "via": "vcgc",
        "door": "VDF_SystemManager_v0115",
        "enter": "vcgc",
        "exit": "vcgc",
        "page": str(PAGE),
        "rc_name": raw.get("rc_name"),
        "launch": launch.get("state"),
        "cmds_missing": missing,
        "rows": rows,
        "open": open_rows,
        "fetched": False,
        "chain_written": False,
        "intake_edited": False,
        "next": "none" if "via-vdffetch" not in missing else "the register chain still hides via-vdffetch",
    }
    text = ["<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VDF Manager Matrix</title>",
            "<style>body{margin:0;background:#101412;color:#d7ddd8;font:11px/1.4 ui-sans-serif,sans-serif}",
            "main{max-width:980px;margin:auto;padding:16px}table{border-collapse:collapse;width:100%}",
            "th,td{border-bottom:1px solid #2a332e;padding:4px 6px;text-align:left;vertical-align:top;word-break:break-word}",
            ".green{color:#7dcea0;font-weight:700}.red{color:#e07a7a;font-weight:700}.stale,.nodata,.gated{color:#e0c36a;font-weight:700}</style>",
            "<main><h1>VDF SYSTEM MANAGER MATRIX</h1><table><tr><th>lamp</th><th>domain</th><th>why</th></tr>"]
    for row in rows:
        text.append("<tr><td class='%s'>%s</td><td>%s</td><td>%s</td></tr>" % (row["lamp"].lower(), row["lamp"], row["lamp_name"], row["why"]))
    text.append("</table></main></html>")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text("".join(text), encoding="utf-8")
    return out


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    if "measure" in sys.argv[1:]:
        card = measure()
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return 0 if "via-vdffetch" not in card["cmds_missing"] else 2
    return _load(PRIOR, "vdf_v0114_passthrough").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = measure()
    ok = denied and "via-vdffetch" not in card["cmds_missing"] and card["launch"] != "RED"
    print("  [OK]" if ok else "  [FAIL] " + card["launch"] + " " + ",".join(card["cmds_missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
