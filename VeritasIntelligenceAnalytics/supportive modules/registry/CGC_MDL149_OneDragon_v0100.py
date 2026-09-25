#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One read-only pass: policy sections, environment inspection, AST scan, then the two managers."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "vcgc" / "DRAGON_latest.json"
ORDER = ["policy", "env_names", "env_inspect", "tools", "numbering", "params", "ast", "vdf", "vrn"]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("via_" + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _quiet(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        value = fn()
    return value, buf.getvalue()


def policy_lamp(raw16: str, norm16: str, expected: str, step_rc: int) -> str:
    same = bool(expected) and (norm16 == expected or raw16 == expected)
    return "GREEN" if same and step_rc == 0 else "RED"


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
            row.setdefault("write", False)
        except Exception as exc:
            row = {"n": n, "id": name, "lamp": "RED", "error": f"{type(exc).__name__}: {exc}"[:180], "write": False}
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
        "do_not": ["registry-sync --apply", "TOOLS_PLAN_latest.ps1", "page --publish", "eight-hub --execute", "panorama fix"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def real_calls() -> dict:
    os.environ["VIA_FROM_VCGC"] = "YES"
    door = _load(HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py")
    gov = _load(sorted(HERE.glob("CGC_MDL135_EnvGovernance_v*.py"))[-1])

    def policy():
        laws = sorted(HERE.glob("VIA_Policy_Laws_SSOT_v*.json"))[-1]
        raw = laws.read_bytes()
        norm = raw.replace(b"\r\n", b"\n")
        raw16 = hashlib.sha256(raw).hexdigest()[:16]
        norm16 = hashlib.sha256(norm).hexdigest()[:16]
        expected = json.loads((HERE / "VIA_EntryLock_v0100.json").read_text(encoding="utf-8")).get("policy_sha16", "")
        rc, text = _quiet(door.policy_step)
        kept = [line.strip() for line in text.splitlines() if line.strip().startswith("[") or "通過" in line or "RED" in line]
        return {"lamp": policy_lamp(raw16, norm16, expected, rc), "rc": rc, "raw16": raw16, "norm16": norm16, "locked": norm16 == expected or raw16 == expected, "lines": kept[:12], "write": False}

    def env_names():
        rc, text = _quiet(door.env_step)
        note = next((line.strip() for line in text.splitlines() if "要改名" in line or "境根" in line), "")
        return {"lamp": "GREEN" if rc == 0 else "RED", "rc": rc, "note": note[:180], "write": False}

    def env_inspect():
        hubs = sorted(HERE.glob("CGC_MDL186_EnvGovernance_8Hub_v*.py"))
        if not hubs:
            return {"lamp": "RED", "error": "eight-hub absent", "write": False}
        hub = _load(hubs[-1])
        rc, text = _quiet(lambda: hub.run(gov, []))
        state = ""
        for line in reversed(text.splitlines()):
            if "八路衝突" in line:
                state = line.strip()[:180]
                break
        report = {}
        if gov.RUN_LATEST.is_file():
            run = json.loads(gov.RUN_LATEST.read_text(encoding="utf-8"))
            report = {"verdict": run.get("verdict"), "conflicts": len(run.get("conflicts") or []), "ts": str(run.get("ts") or "")[:19]}
        lamp = "RED" if rc not in (0, 1) and not state else ("YELLOW" if report.get("verdict") == "RED" or "BLOCKED" in state else "GREEN")
        return {"lamp": lamp, "rc": rc, "eight_hub": state, "last_run": report, "executed": False, "write": False}

    def tools():
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
        return {"lamp": lamp, "state": reg.get("state"), "live": reg.get("expected"), "new": reg.get("new"), "changed": reg.get("changed"), "retired": reg.get("stale"), "ast_err": errors, "applied": False}

    def params():
        path = sorted(HERE.glob("VIA_Central_Params_SSOT_v*.json"))[-1]
        books = [x for x in json.loads(path.read_text(encoding="utf-8")).get("books") or [] if isinstance(x, dict)]
        missing = [str(x.get("path") or "") for x in books if not str(x.get("id") or "").strip()]
        return {"lamp": "GREEN" if not missing else "RED", "books": len(books), "missing": len(missing), "ssot": path.name}

    def ast_scan():
        mod = _load(sorted(HERE.glob("CGC_MDL158_VIAPanoramaAuditRepair_v*.py"))[-1])
        scanned = mod.scan(progress=False)
        tri = mod.issue_triage(scanned)
        by = scanned.get("by_class") or {}
        lamp = "RED" if tri.get("red") else ("YELLOW" if tri.get("total") else "GREEN")
        return {"lamp": lamp, "ast": "mdl158-scan", "files": scanned.get("files_scanned"), "syntax": by.get("SYNTAX", 0), "triage": tri, "fixed": False}

    def subsystem(folder: str, file_name: str):
        got = _load(VIA / "functional modules" / folder / file_name).collect()
        return {"lamp": _lamp_rc(got.get("rc") or 0), "rc": got.get("rc"), "rc_name": got.get("rc_name"), "lamps": got.get("lamps"), "ast": "manager", "write": False}

    return {
        "policy": policy,
        "env_names": env_names,
        "env_inspect": env_inspect,
        "tools": tools,
        "numbering": numbering,
        "params": params,
        "ast": ast_scan,
        "vdf": lambda: subsystem("VDF", "VDF_SystemManager_v0105.py"),
        "vrn": lambda: subsystem("VRN", "VRN_SystemManager_v0105.py"),
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[一條龍] 拒絕。只能經 via-vcgc。")
        return 2
    body = execute(real_calls())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    for row in body["order"]:
        if row["lamp"] == "GREEN":
            print("GREEN " + json.dumps({k: row[k] for k in row if k in ("n", "id", "lamp", "rc")}, ensure_ascii=False))
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if body["metrics"]["RED"] == 0 and not body["missing"] else 2


def selftest() -> int:
    same = policy_lamp("43b2de1213c987e7", "c7aab42f7ebfd283", "c7aab42f7ebfd283", 0) == "GREEN"
    differ = policy_lamp("aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb", "c7aab42f7ebfd283", 0) == "RED"
    body = execute({name: (lambda: {"lamp": "GREEN"}) for name in ORDER})
    ok = same and differ and [row["id"] for row in body["order"]] == ORDER and body["missing"] == [] and body["metrics"]["ran"] == 9
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
