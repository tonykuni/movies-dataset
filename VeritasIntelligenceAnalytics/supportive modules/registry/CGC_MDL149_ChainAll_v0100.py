#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One VCGC pass. Read-only. Numbering is planned, not written."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "vcgc" / "CHAIN_ALL_latest.json"
ORDER = ["policy", "env_names", "tools", "numbering", "params", "vdf", "vrn"]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _quiet(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        value = fn()
    return value, buf.getvalue()


def run() -> dict:
    os.environ["VIA_FROM_VCGC"] = "YES"
    door = _load(HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py")
    steps = []

    lock = _load(HERE / "CGC_MDL149_EntryLock_v0100.py").matrix()
    steps.append({"n": 1, "id": "policy", "locked": lock["policy"]["locked"], "sha16": lock["policy"]["sha16"], "write": False})

    rc, text = _quiet(door.env_step)
    steps.append({"n": 2, "id": "env_names", "rc": rc, "note": next((line.strip() for line in text.splitlines() if "要改名" in line), "NODATA"), "write": False})

    gov = _load(sorted(HERE.glob("CGC_MDL135_EnvGovernance_v*.py"))[-1])
    _quiet(lambda: gov.do_tools([]))
    plan_path = VIA / "VIA_Reports" / "env_governance" / "TOOLS_PLAN_latest.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.is_file() else {}
    steps.append({"n": 3, "id": "tools", "state": plan.get("state") or "PLAN", "counts": plan.get("counts") or {}, "stages": len(plan.get("stages") or []), "applied": False})

    reg = door.registry_sync(False)
    steps.append({"n": 4, "id": "numbering", "state": reg.get("state"), "live": reg.get("expected"), "new": reg.get("new"), "changed": reg.get("changed"), "retired": reg.get("stale"), "ast_err": len(reg.get("parse_errors") or []), "applied": False})

    params = _load(HERE / "CGC_MDL149_PasteBlock_v0101.py").param_ids()
    steps.append({"n": 5, "id": "params", "state": params.get("state"), "books": params.get("books"), "missing": params.get("missing"), "write": False})

    vdf = _load(VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0105.py")
    vrn = _load(VIA / "functional modules" / "VRN" / "VRN_SystemManager_v0105.py")
    a, b = vdf.collect(), vrn.collect()
    steps.append({"n": 6, "id": "vdf", "rc": a.get("rc"), "rc_name": a.get("rc_name"), "lamps": a.get("lamps"), "write": False})
    steps.append({"n": 7, "id": "vrn", "rc": b.get("rc"), "rc_name": b.get("rc_name"), "lamps": b.get("lamps"), "write": False})

    missing = [name for name in ORDER if name not in {step["id"] for step in steps}]
    return {
        "via": "vcgc",
        "order": steps,
        "missing": missing,
        "applied": False,
        "do_not": ["registry-sync --apply", "TOOLS_PLAN_latest.ps1", "page --publish"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[全鏈] 拒絕。只能經 via-vcgc。")
        return 2
    try:
        body = run()
    except Exception as exc:
        body = {"via": "vcgc", "order": [], "missing": ORDER, "error": f"{type(exc).__name__}: {exc}"[:180], "applied": False, "next": "none"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if not body.get("missing") and not body.get("error") else 2


def selftest() -> int:
    ok = ORDER == ["policy", "env_names", "tools", "numbering", "params", "vdf", "vrn"]
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    print("  [OK]" if ok and denied else "  [FAIL]")
    return 0 if ok and denied else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
