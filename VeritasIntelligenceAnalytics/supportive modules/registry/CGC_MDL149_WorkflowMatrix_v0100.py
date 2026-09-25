#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seven gates, one matrix. A failed gate stays on the matrix. Nothing is applied."""
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
OUT = VIA / "VIA_Reports" / "vcgc" / "MATRIX_latest.json"
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


def _lamp_rc(rc: int) -> str:
    return {0: "GREEN", 1: "RED", 2: "YELLOW"}.get(int(rc), "RED")


def execute(calls: dict) -> dict:
    steps = []
    for n, name in enumerate(ORDER, 1):
        try:
            row = calls[name]()
            row["n"] = n
            row["id"] = name
            row.setdefault("lamp", "GREEN")
            row.setdefault("ast", "not_used")
            row.setdefault("write", False)
        except Exception as exc:
            row = {"n": n, "id": name, "lamp": "RED", "error": f"{type(exc).__name__}: {exc}"[:180], "ast": "not_used", "write": False}
        steps.append(row)
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in steps:
        counts[row["lamp"]] = counts.get(row["lamp"], 0) + 1
    return {
        "via": "vcgc",
        "metrics": {"gates": len(ORDER), "ran": len(steps), **counts},
        "order": steps,
        "missing": [name for name in ORDER if name not in {row["id"] for row in steps}],
        "applied": False,
        "ssot": ["VIA_Policy_Laws_SSOT_v0100.json", "VIA_Component_Inventory_SSOT_v0100.json", "VIA_Central_Params_SSOT_v0100.json"],
        "do_not": ["registry-sync --apply", "TOOLS_PLAN_latest.ps1", "page --publish"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def real_calls() -> dict:
    os.environ["VIA_FROM_VCGC"] = "YES"
    door = _load(HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py")

    def policy():
        lock = _load(HERE / "CGC_MDL149_EntryLock_v0100.py").matrix()
        same = bool(lock["policy"]["locked"])
        return {"lamp": "GREEN" if same else "RED", "locked": same, "sha16": lock["policy"]["sha16"]}

    def env_names():
        rc, text = _quiet(door.env_step)
        note = next((line.strip() for line in text.splitlines() if "要改名" in line or "境根" in line), "")
        return {"lamp": "GREEN" if rc == 0 else "RED", "rc": rc, "note": note[:160]}

    def tools():
        gov = _load(sorted(HERE.glob("CGC_MDL135_EnvGovernance_v*.py"))[-1])
        _quiet(lambda: gov.do_tools([]))
        path = VIA / "VIA_Reports" / "env_governance" / "TOOLS_PLAN_latest.json"
        plan = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        counts = plan.get("counts") or {}
        lamp = "YELLOW" if counts.get("ENV_ABSENT") or counts.get("UNROUTED") else "GREEN"
        return {"lamp": lamp, "counts": counts, "stages": len(plan.get("stages") or []), "applied": False}

    def numbering():
        reg = door.registry_sync(False)
        errors = len(reg.get("parse_errors") or [])
        changed = int(reg.get("new") or 0) + int(reg.get("changed") or 0) + int(reg.get("stale") or 0)
        lamp = "RED" if errors else ("YELLOW" if changed else "GREEN")
        return {"lamp": lamp, "state": reg.get("state"), "live": reg.get("expected"), "new": reg.get("new"), "changed": reg.get("changed"), "retired": reg.get("stale"), "ast_err": errors, "applied": False, "ssot": "VIA_Component_Inventory_SSOT_v0100.json"}

    def params():
        path = sorted(HERE.glob("VIA_Central_Params_SSOT_v*.json"))[-1]
        books = [x for x in json.loads(path.read_text(encoding="utf-8")).get("books") or [] if isinstance(x, dict)]
        missing = [str(x.get("path") or "") for x in books if not str(x.get("id") or "").strip()]
        return {"lamp": "GREEN" if not missing else "RED", "books": len(books), "missing": len(missing), "ssot": path.name}

    def subsystem(folder: str, file_name: str):
        mod = _load(VIA / "functional modules" / folder / file_name)
        got = mod.collect()
        return {"lamp": _lamp_rc(got.get("rc") or 0), "rc": got.get("rc"), "rc_name": got.get("rc_name"), "lamps": got.get("lamps")}

    return {
        "policy": policy,
        "env_names": env_names,
        "tools": tools,
        "numbering": numbering,
        "params": params,
        "vdf": lambda: subsystem("VDF", "VDF_SystemManager_v0105.py"),
        "vrn": lambda: subsystem("VRN", "VRN_SystemManager_v0105.py"),
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[矩陣] 拒絕。只能經 via-vcgc。")
        return 2
    body = execute(real_calls())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    for row in body["order"]:
        if row["lamp"] == "GREEN":
            print("GREEN " + json.dumps(row, ensure_ascii=False))
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if body["metrics"]["RED"] == 0 and not body["missing"] else 2


def selftest() -> int:
    def boom():
        raise AttributeError("param_ids")

    body = execute({
        "policy": lambda: {"lamp": "GREEN"},
        "env_names": lambda: {"lamp": "GREEN"},
        "tools": lambda: {"lamp": "YELLOW", "applied": False},
        "numbering": lambda: {"lamp": "YELLOW", "new": 1, "applied": False},
        "params": boom,
        "vdf": lambda: {"lamp": "YELLOW"},
        "vrn": lambda: {"lamp": "RED"},
    })
    ids = [row["id"] for row in body["order"]]
    ok = ids == ORDER and body["missing"] == [] and body["order"][4]["lamp"] == "RED" and "param_ids" in body["order"][4]["error"]
    ok = ok and body["metrics"]["ran"] == 7
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(body, ensure_ascii=False)[:400])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
