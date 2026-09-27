#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the VCGC selftests in one pass. Nothing is fetched and nothing is pushed.

Each row is the newest tail of that door. A timeout is a failure, not a skip.
"""
from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PAGE = VIA / "VIA_Reports" / "vcgc" / "VIA_Test_Matrix_v0100.html"
SUITES = (
    ("policy", "CGC_MDL207_PolicyRun_v*.py"),
    ("talib", "CGC_MDL205_TalibBan_v*.py"),
    ("ledger", "CGC_MDL220_SuccessLedger_v*.py"),
    ("matrix", "CGC_MDL217_ManagerMatrix_v*.py"),
    ("backup", "CGC_MDL221_SystemBackup_v*.py"),
    ("probe", "CGC_MDL222_SubsystemProbe_v*.py"),
    ("flow", "CGC_MDL223_FlowConsistency_v*.py"),
    ("manager", "CGC_SystemManager_v*.py"),
    ("console", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"),
)


def _newest(pattern: str) -> Path | None:
    hits = [p for p in sorted(HERE.glob(pattern)) if p.name != Path(__file__).name]
    return hits[-1] if hits else None


def _one(name: str, path: Path | None) -> dict:
    if path is None:
        return {"lamp": "RED", "suite": name, "tail": "", "rc": 2, "secs": 0, "last": "ABSENT"}
    env = os.environ.copy()
    env["VIA_FROM_VCGC"] = "YES"
    env["VIA_VCGC_PUSH"] = "NO"
    t0 = time.time()
    try:
        done = subprocess.run(
            [sys.executable, str(path), "--selftest"],
            cwd=str(VIA.parent), env=env, capture_output=True, text=True, timeout=90,
        )
        lines = [ln.strip() for ln in (done.stdout or "").splitlines() if ln.strip()]
        last = lines[-1] if lines else ""
        rc = done.returncode
    except subprocess.TimeoutExpired:
        rc, last = 3, "TIMEOUT"
    return {
        "lamp": "GREEN" if rc == 0 else "RED",
        "suite": name,
        "tail": path.name,
        "rc": rc,
        "secs": round(time.time() - t0, 1),
        "last": last[:80],
    }


def run() -> dict:
    rows = [_one(name, _newest(pattern)) for name, pattern in SUITES]
    red = [row["suite"] for row in rows if row["lamp"] != "GREEN"]
    return {
        "via": "vcgc",
        "door": "CGC_MDL224_TestAuto_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not red,
        "page": str(PAGE),
        "rows": rows,
        "green": sum(1 for row in rows if row["lamp"] == "GREEN"),
        "red": red,
        "fetched": False,
        "pushed": False,
        "book_edited": False,
        "intake_edited": False,
        "do_not": [
            "push from a selftest",
            "fetch from this door",
            "rewrite the locked policy book",
            "edit intake macro_ssot",
        ],
        "next": "none" if not red else "do not unlock; name the red suite",
    }


def write_page(card: dict) -> None:
    body = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (html.escape(row["lamp"]), html.escape(row["suite"]), html.escape(row["tail"]),
           str(row["rc"]), str(row["secs"]), html.escape(row["last"]))
        for row in card["rows"]
    )
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VCGC test matrix</title>
<style>
body{margin:0;background:#121614;color:#d5ddd6;font:11px/1.35 ui-sans-serif,sans-serif}
main{max-width:1100px;margin:auto;padding:14px}
h1{font-size:14px;font-weight:650;margin:0 0 8px}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #2c3832;padding:4px 6px;text-align:left;vertical-align:top;white-space:normal;word-break:break-word}
th{color:#8e9b93}td:first-child{font-weight:700}
</style><main><h1>VCGC TEST MATRIX</h1>
<table><tr><th>lamp</th><th>suite</th><th>tail</th><th>rc</th><th>secs</th><th>last</th></tr>__ROWS__</table>
</main></html>"""
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(text.replace("__ROWS__", body), encoding="utf-8")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = run()
    write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    missing = [name for name, pattern in SUITES if _newest(pattern) is None]
    ok = denied and not missing and PAGE.parent.parent.is_dir()
    print("  [OK]" if ok else "  [FAIL] " + ",".join(missing))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
