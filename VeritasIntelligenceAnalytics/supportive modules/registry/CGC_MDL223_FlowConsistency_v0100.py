#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the VCGC policy, sync the subsystem managers, then allow the verb.

The locked policy book stays untouched. GitHub receives the seat only.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
REPO = VIA.parent
NOTE = HERE / "VIA_Policy_FlowGate_v0100.json"
POLICY = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0152.py"
PROBE = HERE / "CGC_MDL222_SubsystemProbe_v0100.py"
SEAT = HERE / "VIA_VCGC_SubsystemSeat_v0100.json"
PAGE = VIA / "VIA_Reports" / "vcgc" / "VIA_Flow_Matrix_v0100.html"
NEEDLES = ("VIA_FROM_VCGC", "def main", "def selftest")
FAMILIES = (
    ("VCGC", HERE, "CGC_SystemManager_v*.py"),
    ("VDF", VIA / "functional modules" / "VDF", "VDF_SystemManager_v*.py"),
    ("VRN", VIA / "functional modules" / "VRN", "VRN_SystemManager_v*.py"),
    ("NLP", VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py"),
    ("LAYOUT", VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL743_GenericLayoutHub_v*.py"),
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def functions() -> list[dict]:
    rows = []
    for system, folder, pattern in FAMILIES:
        path = _newest(folder, pattern)
        text = path.read_text(encoding="utf-8", errors="ignore") if path else ""
        have = [needle for needle in NEEDLES if needle in text]
        rows.append({
            "lamp": "GREEN" if path and len(have) == len(NEEDLES) else "RED",
            "system": system,
            "tail": path.name if path else "",
            "have": have,
            "role": "parent" if system == "VCGC" else "child",
        })
    return rows


def gate() -> dict:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    policy = _load(POLICY, "policy_for_flow")
    rc = policy.policy_step()
    probe = _load(PROBE, "probe_for_flow")
    seat_card = probe.check()
    if seat_card["drift"]:
        probe.write_seat(seat_card["rows"])
        seat_card = probe.check()
        seat_card["synced"] = True
    rows = functions()
    weak = [row["system"] for row in rows if row["lamp"] != "GREEN"]
    missing = []
    if rc != 0:
        missing.append("policy_step")
    if note.get("book_edited") is not False:
        missing.append("book")
    missing.extend(seat_card["missing"])
    missing.extend(weak)
    return {
        "via": "vcgc",
        "door": "CGC_MDL223_FlowConsistency_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "policy_rc": rc,
        "book_edited": False,
        "synced": bool(seat_card.get("synced")),
        "rows": rows,
        "drift": seat_card["drift"],
        "weak": weak,
        "missing": missing,
        "pushed": False,
        "intake_edited": False,
        "do_not": note["do_not"],
        "next": "none" if not missing else "do not run the verb",
    }


def write_page(card: dict) -> None:
    body = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (html.escape(row["lamp"]), html.escape(row["role"]), html.escape(row["system"]),
           html.escape(row["tail"]), html.escape(", ".join(row["have"])))
        for row in card["rows"]
    )
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VCGC flow matrix</title>
<style>
body{margin:0;background:#121614;color:#d5ddd6;font:11px/1.35 ui-sans-serif,sans-serif}
main{max-width:1100px;margin:auto;padding:14px}
h1{font-size:14px;font-weight:650;margin:0 0 8px}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #2c3832;padding:4px 6px;text-align:left;vertical-align:top;white-space:normal;word-break:break-word}
th{color:#8e9b93}
td:first-child{font-weight:700}
</style><main><h1>VCGC FLOW · PARENT AND CHILDREN</h1>
<table><tr><th>lamp</th><th>role</th><th>system</th><th>tail</th><th>functions</th></tr>__ROWS__</table>
</main></html>"""
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(text.replace("__ROWS__", body), encoding="utf-8")


def publish() -> dict:
    if os.environ.get("VIA_VCGC_PUSH") == "NO":
        return {"pushed": False, "why": "held"}
    rel = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json"
    status = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=REPO, capture_output=True, text=True)
    if status.returncode != 0:
        return {"pushed": False, "why": "git"}
    if not status.stdout.strip():
        return {"pushed": False, "why": "clean"}
    subprocess.run(["git", "add", "--", rel], cwd=REPO, check=False)
    commit = subprocess.run(
        ["git", "-c", "user.name=Tony Huang", "-c", "user.email=138236302+tonykuni@users.noreply.github.com",
         "commit", "-m", "vcgc: sync the subsystem seat"],
        cwd=REPO, capture_output=True, text=True,
    )
    if commit.returncode != 0:
        return {"pushed": False, "why": "commit"}
    push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return {"pushed": push.returncode == 0, "why": "pushed" if push.returncode == 0 else "push"}


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = gate()
    write_page(card)
    if card["lock_success"]:
        card.update(publish())
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ["VIA_VCGC_PUSH"] = "NO"
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = gate()
    write_page(card)
    parent = next(row for row in card["rows"] if row["role"] == "parent")
    children = [row for row in card["rows"] if row["role"] == "child"]
    ok = denied and card["lock_success"] and parent["have"] == list(NEEDLES)
    ok = ok and children and all(row["have"] == list(NEEDLES) for row in children)
    ok = ok and PAGE.is_file() and SEAT.is_file()
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
