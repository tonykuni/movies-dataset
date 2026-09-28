#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add the all-in-one VRN logic file. Nothing already on the book is removed.

Token tools run first: pack, slice, digest, source etag, text etag, and the
token-save seat. Their bodies are not printed. Install apply is not called,
so this file does not replace vrn_logic.py.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PANORAMA = HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0115.py"
TOKEN = VIA / "supportive modules" / "VIA_TokenSave_v0100.py"
BOOK = HERE / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"
ENGINE = VIA / "functional modules" / "VRN" / "VIA_VRNLogic_AllInOne_v0201.py"
FAMILY = "VIA_VRNLogic_AllInOne"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _tools() -> dict:
    panorama = _load(PANORAMA, "vcgc_panorama_for_logic_add")
    token = _load(TOKEN, "vcgc_token_for_logic_add")
    sliced = panorama.slice_def(str(ENGINE), "process_report")
    hit = (sliced.get("hits") or [{}])[0]
    packed = panorama.pack_payload(ENGINE.parent, limit=1)
    digested = panorama.digest_log("vrn logic add\n")
    return {
        "pack": {"files": packed.get("files") or packed.get("n") or packed.get("count"), "etag": packed.get("etag")},
        "slice": {"name": "process_report", "line": hit.get("line"), "slice_tokens": sliced.get("slice_tokens"), "body": False},
        "digest": {"kept": list(digested)[:6]},
        "source_etag": panorama.source_etag([ENGINE]),
        "text_etag": panorama.text_etag(FAMILY),
        "token_save": token.check()["door"],
    }


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    nodes = []
    for body in (book.get("layers") or {}).values():
        nodes.extend(body.get("nodes") or [])
    families = [row.get("family") for row in nodes]
    added = FAMILY in families
    tools = _tools()
    run = subprocess.run(
        [sys.executable, str(ENGINE), "--selftest"],
        cwd=str(VIA),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    tail = "\n".join((run.stdout or "").splitlines()[-3:])
    passed = run.returncode == 0 and "FAIL 0" in run.stdout
    return {
        "via": "vcgc",
        "door": "CGC_MDL244_VrnLogicAdd_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "book_version": book.get("version"),
        "nodes": len(nodes),
        "added": FAMILY,
        "added_present": added,
        "removed": [],
        "engine": ENGINE.name,
        "selftest": "PASS" if passed else "FAIL",
        "selftest_tail": tail,
        "install_apply": False,
        "tools": tools,
        "talib": False,
        "lock_success": added and passed and book.get("version") == "v0112" and len(nodes) >= 49,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "run --install apply",
            "replace an older VRN engine with this file",
            "delete a logic node",
            "print a sliced body",
            "import talib",
            "edit intake macro_ssot",
        ],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    if not card["lock_success"]:
        card["next"] = "name the failed check; do not install over the old logic"
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    text = json.dumps(card)
    ok = denied and card["lock_success"] and card["install_apply"] is False and "def process_report" not in text
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
