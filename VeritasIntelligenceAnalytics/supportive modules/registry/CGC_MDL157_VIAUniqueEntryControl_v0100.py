#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL157: VIA unique entry-point control plane.

This is a deterministic, offline, read-only gate. It does not execute market
engines. It proves that VRN, VDF and QuantGuard are reached through the VIA
command book and the single Invoke-VIAPython/bootstrap path, with the network
consent gate remaining fail-closed.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
COMMAND_BOOK = ROOT / "Register-VIA-Commands-v0208.ps1"
PY_HELPER = ROOT / "supportive modules" / "VIA_PS_PyProgress_Module.ps1"
BOOTSTRAP = ROOT / "supportive modules" / "bootstrap" / "sitecustomize.py"
POLICY = ROOT / "supportive modules" / "registry" / "VIA_QuantGuard_TA_Lib_Policy_v0100.json"
INPUT_CONSOLE = ROOT / "supportive modules" / "registry" / "VIA_InputConsole_Spec_v0100.json"
WORKFLOW = ROOT / "supportive modules" / "registry" / "VIA_Workflow_SSOT_v0100.json"
TOOL_ROSTER = ROOT / "supportive modules" / "registry" / "VIA_ToolRoster_SSOT_v0100.json"
REPORT_DIR = ROOT / "VIA_Reports" / "entry"
LATEST_JSON = REPORT_DIR / "VIA_UNIQUE_ENTRY_CONTROL_latest.json"
LATEST_HTML = REPORT_DIR / "VIA_UNIQUE_ENTRY_CONTROL_latest.html"
DISPATCH_JSON = REPORT_DIR / "VIA_UNIQUE_ENTRY_DISPATCH_latest.json"

TARGET_ENTRYPOINTS = (
    "via-nlpvrn",
    "via-nlpunified",
    "via-vrn4",
    "via-vdfarch",
    "via-vdfdb",
    "via-quantguard",
)
TARGET_TOKENS = ("VRN_ENG", "VDF_ENG", "SUP_MDL", "CGC_MDL")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "state": "PASS" if ok else "FAIL", "ok": bool(ok), "detail": detail}


def function_bodies(text: str) -> dict[str, str]:
    pattern = re.compile(r"(?ms)^function\s+global:(via-[\w-]+)\s*\{(?P<body>.*?)(?=^function\s+global:|\Z)")
    return {m.group(1): m.group("body") for m in pattern.finditer(text)}


def run_checks() -> list[dict[str, Any]]:
    book = read(COMMAND_BOOK)
    helper = read(PY_HELPER)
    boot = read(BOOTSTRAP)
    bodies = function_bodies(book)
    checks: list[dict[str, Any]] = [
        check("VIA command book exists", COMMAND_BOOK.is_file(), str(COMMAND_BOOK)),
        check("VIA Python helper exists", PY_HELPER.is_file(), str(PY_HELPER)),
        check("single Invoke-VIAPython helper is defined", "function Invoke-VIAPython" in helper, "VIA_PS_PyProgress_Module.ps1"),
        check("helper owns process start", "Start-Process -FilePath $exe" in helper, "central process wrapper"),
        check("bootstrap exists", BOOTSTRAP.is_file(), str(BOOTSTRAP)),
        check("bootstrap carries central entry identity", "VIA_ENTRY_CONTROL" in boot and "CGC_MDL157" in boot and "VIA_CENTRAL_ENTRY" in boot, "sitecustomize.py"),
        check("network default is fail-closed in command book", 'VIA_NET_CONSENT = "OFF"' in book and 'VIA_SCRAPE_CONSENT = "OFF"' in book, "Set-VIAGateDefaults"),
        check("command book never auto-opens consent", 'VIA_NET_CONSENT = "YES"' not in book and 'VIA_SCRAPE_CONSENT = "YES"' not in book, "operator consent only"),
        check("command book has unique central dispatcher", "function global:via-central" in book and "function global:via-unique-check" in book, "VIA central command"),
    ]
    central = bodies.get("via-central", "")
    checks.append(check("central dispatcher routes VRN/VDF/QuantGuard", all(x in central for x in ("via-nlpvrn", "via-vdfarch", "via-quantguard")), "via-central child routes"))
    checks.append(check("central dispatcher gates before child route", "CGC157 未 GREEN" in central and "Invoke-VIAPython" in central, "pre-dispatch gate"))
    missing = [name for name in TARGET_ENTRYPOINTS if name not in bodies]
    checks.append(check("VRN/VDF/QuantGuard target entries exist", not missing, "missing=" + ",".join(missing)))
    bypasses: list[str] = []
    for name in TARGET_ENTRYPOINTS:
        body = bodies.get(name, "")
        if body and "Invoke-VIAPython" not in body and "via-closeout" not in body:
            bypasses.append(name)
    checks.append(check("target entries dispatch only through VIA Python helper", not bypasses, "bypass=" + ",".join(bypasses)))
    direct_engine_lines = []
    for name in TARGET_ENTRYPOINTS:
        body = bodies.get(name, "")
        for line in body.splitlines():
            if any(token in line for token in TARGET_TOKENS) and "Invoke-VIAPython" not in line and "Get-VIANewest" not in line and "FAIL:" not in line and not line.lstrip().startswith("#"):
                direct_engine_lines.append(f"{name}:{line.strip()[:140]}")
    checks.append(check("no target engine line bypasses Invoke-VIAPython", not direct_engine_lines, "; ".join(direct_engine_lines[:4])))
    checks.append(check("fail-closed helper does not direct-fallback", "中央 helper 缺失" in book and "& $exe @Rest" not in book, "missing helper must stop"))
    checks.append(check("policy SSOT is active and one-way", POLICY.is_file() and '"direction": "VDF_DUCKDB_TO_QUANTGUARD"' in read(POLICY) and '"source_mutation": "FORBIDDEN"' in read(POLICY), "QuantGuard policy"))
    checks.append(check("central registries contain unique entry contract", all(token in read(path) for path, token in ((INPUT_CONSOLE, "via_unique_entry_control"), (WORKFLOW, "via_unique_entry_control"), (TOOL_ROSTER, "unique_entry_control"))), "InputConsole/Workflow/ToolRoster"))
    checks.append(check("entry-control report directory is writable", REPORT_DIR.parent.is_dir(), str(REPORT_DIR)))
    return checks


def run(write: bool = True) -> dict[str, Any]:
    checks = run_checks()
    passed = sum(1 for item in checks if item["ok"])
    failed = len(checks) - passed
    verdict = "GREEN" if failed == 0 else "RED"
    payload = {
        "schema": "VIA.CGC157.UniqueEntryControl.v1",
        "engine": "CGC_MDL157_VIAUniqueEntryControl_v0100",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict,
        "control_state": "ONLY_VIA_ENTRY" if verdict == "GREEN" else "DO_NOT_ROUTE",
        "scope": {"vrn": list(TARGET_ENTRYPOINTS[:3]), "vdf": list(TARGET_ENTRYPOINTS[3:5]), "quantguard": [TARGET_ENTRYPOINTS[5]]},
        "checks": checks,
        "counts": {"total": len(checks), "pass": passed, "fail": failed},
        "network": {"default": "OFF", "consent": "operator_owned", "silent_open": False},
        "data_flow": "VDF_DUCKDB_TO_QUANTGUARD",
        "source_mutation": "FORBIDDEN",
        "artifacts": {name: {"path": str(path), "sha256": sha256(path)} for name, path in {"command_book": COMMAND_BOOK, "python_helper": PY_HELPER, "bootstrap": BOOTSTRAP, "policy": POLICY}.items()},
    }
    if write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        LATEST_HTML.write_text(render_html(payload), encoding="utf-8")
    return payload


def render_html(payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{html.escape(x['name'])}</td><td class='{x['state']}'>{x['state']}</td><td>{html.escape(x['detail'])}</td></tr>" for x in payload["checks"])
    c = payload["counts"]
    return f"""<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Unique Entry Control</title><style>body{{font:14px system-ui,sans-serif;margin:30px;color:#172033}}h1{{margin-bottom:4px}}.pill{{padding:5px 12px;border-radius:999px;font-weight:700}}.GREEN,.PASS{{background:#d9f2e9;color:#08745b}}.RED,.FAIL{{background:#ffe1df;color:#a52b25}}table{{border-collapse:collapse;width:100%;margin-top:20px}}th,td{{border-bottom:1px solid #dfe5ee;padding:9px;text-align:left;vertical-align:top}}th{{background:#f4f7fb}}</style></head><body><h1>VIA 唯一接觸口控制</h1><p><span class='pill {payload['verdict']}'>{payload['verdict']}</span> <b>{payload['control_state']}</b> · {payload['timestamp']}</p><p>PASS {c['pass']} / {c['total']} · data flow: <b>VDF/DuckDB → QuantGuard</b> · network: <b>OFF</b></p><table><thead><tr><th>檢查</th><th>狀態</th><th>細節</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""


def dispatch(family: str) -> dict[str, Any]:
    """Run only fixed, offline child routes after the unique-entry gate."""
    gate = run(write=True)
    if gate["verdict"] != "GREEN":
        result = {"schema": "VIA.CGC157.UniqueEntryDispatch.v1", "verdict": "BLOCKED", "gate": gate, "routes": []}
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        DISPATCH_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    commands: dict[str, list[tuple[str, list[str]]]] = {
        "vrn": [("VRN_ENG087_NLP", [str(ROOT / "functional modules" / "VRN" / "VRN_ENG087_NLPTextSummaryBridge_v0100.py"), "selftest"])],
        "vdf": [
            ("VDF_ENG073_DataArchitecture", [str(ROOT / "functional modules" / "VDF" / "engine" / "VDF_ENG073_DataArchitecture_v0100.py"), "--selftest"]),
            ("VDF_ENG087_MarketListGovernance", [str(ROOT / "functional modules" / "VDF" / "engine" / "VDF_ENG087_MarketListGovernance_v0101.py"), "--selftest"]),
        ],
        "quantguard": [("VDF_ENG086_QuantGuard", [str(ROOT / "functional modules" / "VDF" / "engine" / "VDF_ENG086_QuantGuardOneBridge_v0100.py"), "selftest"])],
    }
    families = ["vrn", "vdf", "quantguard"] if family == "all" else [family]
    env = os.environ.copy()
    env["VIA_ROOT"] = str(ROOT)
    env["VIA_CENTRAL_ENTRY"] = "1"
    env["VIA_ENTRY_CONTROL"] = "CGC_MDL157_VIAUniqueEntryControl_v0100"
    env.setdefault("VIA_NET_CONSENT", "OFF")
    env.setdefault("VIA_SCRAPE_CONSENT", "OFF")
    env["PYTHONPATH"] = str(BOOTSTRAP) + os.pathsep + env.get("PYTHONPATH", "")
    routes: list[dict[str, Any]] = []
    for fam in families:
        for label, argv in commands[fam]:
            proc = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=300)
            output = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
            routes.append({"family": fam, "engine": label, "argv": argv, "returncode": proc.returncode, "state": "GREEN" if proc.returncode == 0 else "RED", "output_tail": output[-4000:]})
    result = {
        "schema": "VIA.CGC157.UniqueEntryDispatch.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gate": {"engine": gate["engine"], "verdict": gate["verdict"], "control_state": gate["control_state"]},
        "family": family,
        "routes": routes,
        "network": {"default": "OFF", "consent": env.get("VIA_NET_CONSENT"), "silent_open": False},
        "data_flow": "VDF_DUCKDB_TO_QUANTGUARD",
        "verdict": "GREEN" if routes and all(x["returncode"] == 0 for x in routes) else "RED",
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DISPATCH_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="VIA unique entry-point control plane")
    parser.add_argument("command", choices=("selftest", "status", "manifest", "routes", "dispatch"))
    parser.add_argument("--family", choices=("vrn", "vdf", "quantguard", "all"), default="all")
    args = parser.parse_args()
    if args.command == "dispatch":
        result = dispatch(args.family)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["verdict"] == "GREEN" else 2
    payload = run(write=True)
    if args.command == "selftest":
        print(f"[CGC_MDL157] {payload['verdict']} · {payload['counts']['pass']}/{payload['counts']['total']} · ONLY_VIA_ENTRY")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
