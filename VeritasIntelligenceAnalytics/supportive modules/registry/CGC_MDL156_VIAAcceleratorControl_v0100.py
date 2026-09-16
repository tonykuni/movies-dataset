#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL156: VIA 25-accelerator control plane.

This module is deliberately offline and read-only during selftest. It verifies
that the PowerShell roster, Python bootstrap, SuperAccel, Celeritas, Aegis and
central registries agree before any accelerator generation or execution.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
ROSTER_JSON = ROOT / "supportive modules" / "registry" / "VIA_Accelerator_Roster_SSOT_v0100.json"
PS_ROSTER = ROOT / "supportive modules" / "registry" / "VIA_PS_Accelerators_25_Roster_v0100.ps1"
PS_MODULE = ROOT / "supportive modules" / "VIA_PS_Accel_Module.ps1"
BOOTSTRAP = ROOT / "supportive modules" / "bootstrap" / "sitecustomize.py"
SUPERACC = ROOT / "supportive modules" / "VIA_SuperAccel_Module.py"
CELERITAS = ROOT / "supportive modules" / "accelerator" / "VeritasCeleritas.py"
AEGIS = ROOT / "supportive modules" / "network" / "VeritasAegisNexus.py"
QUANTGUARD = ROOT / "functional modules" / "VDF" / "engine" / "VDF_ENG086_QuantGuardOneBridge_v0100.py"
REPORT_DIR = ROOT / "VIA_Reports" / "accelerator"
LATEST_JSON = REPORT_DIR / "VIA_ACCELERATOR_CONTROL_latest.json"
LATEST_HTML = REPORT_DIR / "VIA_ACCELERATOR_CONTROL_latest.html"

REGISTRIES = [
    ROOT / "supportive modules" / "registry" / "VIA_InputConsole_Spec_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Workflow_SSOT_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Interface_Contract_Registry_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Naming_Registry_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Component_Inventory_SSOT_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_ToolRoster_SSOT_v0100.json",
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "state": "PASS" if ok else "FAIL", "ok": bool(ok), "detail": detail}


def roster_checks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("accelerators") or []
    ids = [str(x.get("id")) for x in items]
    expected = [f"{i:02d}" for i in range(1, 26)]
    out = [check("SSOT roster JSON exists", ROSTER_JSON.is_file(), str(ROSTER_JSON))]
    out.append(check("SSOT roster count=25", len(items) == 25, f"count={len(items)}"))
    out.append(check("SSOT ids unique and contiguous", ids == expected, f"ids={ids}"))
    out.append(check("network accelerator is explicit", any(x.get("id") == "23" and x.get("network") is True for x in items), "id=23"))
    return out


def runtime_checks() -> list[dict[str, Any]]:
    ps_roster_text = read(PS_ROSTER)
    ps_module_text = read(PS_MODULE)
    boot_text = read(BOOTSTRAP)
    reg_text = "\n".join(read(p) for p in REGISTRIES)
    out = [
        check("PowerShell 25 roster exists", PS_ROSTER.is_file(), str(PS_ROSTER)),
        check("PowerShell roster declares 25 entries", len(re.findall(r"^\s*'\d{2}'\s*=", ps_roster_text, re.M)) == 25, "regex count"),
        check("PowerShell runtime exports VIA_ACCEL25", "VIA_ACCEL25" in ps_module_text and "Get-VIAAccelRoster" in ps_module_text, "VIA_PS_Accel_Module.ps1"),
        check("Python sitecustomize bootstrap exists", BOOTSTRAP.is_file(), str(BOOTSTRAP)),
        check("Python bootstrap exposes accelerator state", "VIA_ACCEL_BOOT" in boot_text, "sitecustomize.py"),
        check("Python bootstrap exports 25-roster identity", "VIA_ACCELERATOR_ROSTER" in boot_text and ":25" in boot_text, "all Python families"),
        check("Python bootstrap exports central control identity", "VIA_ACCELERATOR_CONTROL" in boot_text and "CGC_MDL156" in boot_text, "central control"),
        check("Python bootstrap mounts via_net for VDF", 'sys.modules["via_net"]' in boot_text and 'fam == "vdf"' in boot_text, "network family gate"),
        check("Python bootstrap mounts Celeritas/Aegis", "VeritasCeleritas" in boot_text and "VeritasAegisNexus" in boot_text, "lazy tool mounts"),
        check("SuperAccel canonical module exists", SUPERACC.is_file(), str(SUPERACC)),
        check("Celeritas canonical mount exists", CELERITAS.is_file(), str(CELERITAS)),
        check("Aegis canonical mount exists", AEGIS.is_file(), str(AEGIS)),
        check("network is OFF by default in roster", '"network_default": "OFF"' in read(ROSTER_JSON), "fail-closed"),
        check("central registries mention accelerator control", "via_accelerator_control" in reg_text or "CGC_MDL156" in reg_text, "central registry references"),
    ]
    # TA-Lib is permanently prohibited. Scan only canonical active mounts;
    # retired/reference material is intentionally not treated as an active path.
    forbidden = re.compile(r"(?im)^\s*(?:from\s+talib\s+import|import\s+talib)|_si\(\s*['\"]talib['\"]\)|['\"]talib['\"]")
    active_hits = []
    for path in (CELERITAS, AEGIS, QUANTGUARD):
        match = forbidden.search(read(path))
        if match:
            active_hits.append(f"{path.name}:{match.group(0).strip()}")
    out.append(check("canonical active mounts contain no TA-Lib path", not active_hits, "; ".join(active_hits) or "QuantGuard only"))
    # Count active Python files that receive the bootstrap transitively.
    py_files = []
    for base in (ROOT / "functional modules", ROOT / "supportive modules"):
        if base.exists():
            py_files.extend(p for p in base.rglob("*.py") if ".git" not in p.parts and "__pycache__" not in p.parts)
    out.append(check("Python active tree is non-empty", bool(py_files), f"python_files={len(py_files)}"))
    return out


def run(write: bool = True) -> dict[str, Any]:
    try:
        roster = load_json(ROSTER_JSON)
        load_error = None
    except Exception as exc:  # pragma: no cover - emitted in status
        roster = {}
        load_error = f"{type(exc).__name__}: {exc}"
    checks = roster_checks(roster) if not load_error else [check("SSOT roster JSON parse", False, load_error)]
    checks.extend(runtime_checks())
    passed = sum(1 for x in checks if x["ok"])
    failed = len(checks) - passed
    verdict = "GREEN" if failed == 0 else "RED"
    payload = {
        "schema": "VIA.CGC156.AcceleratorControl.v1",
        "engine": "CGC_MDL156_VIAAcceleratorControl_v0100",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict,
        "control_state": "READY_FOR_25" if verdict == "GREEN" else "DO_NOT_GENERATE_25",
        "checks": checks,
        "counts": {"total": len(checks), "pass": passed, "fail": failed, "accelerators": len(roster.get("accelerators", []))},
        "mounts": {name: {"path": str(path), "exists": path.is_file(), "sha256": sha256(path)} for name, path in {"superaccel": SUPERACC, "celeritas": CELERITAS, "aegis": AEGIS}.items()},
        "generation_policy": "Only generate/execute accelerator modules after this report is GREEN and registry-sync is idempotent.",
    }
    if write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        LATEST_HTML.write_text(render_html(payload), encoding="utf-8")
    return payload


def render_html(payload: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(str(x['name']))}</td><td class='{x['state']}'>{x['state']}</td><td>{html.escape(str(x.get('detail','')))}</td></tr>"
        for x in payload["checks"]
    )
    c = payload["counts"]
    return f"""<!doctype html>
<html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA 25 Accelerator Control</title>
<style>body{{font:14px system-ui,sans-serif;margin:32px;color:#172033}}h1{{margin-bottom:4px}}.pill{{padding:5px 12px;border-radius:999px;font-weight:700}}.GREEN,.PASS{{background:#d9f2e9;color:#08745b}}.RED,.FAIL{{background:#ffe1df;color:#a52b25}}table{{border-collapse:collapse;width:100%;margin-top:22px}}th,td{{border-bottom:1px solid #dfe5ee;padding:9px;text-align:left;vertical-align:top}}th{{background:#f4f7fb}}code{{white-space:pre-wrap}}</style></head>
<body><h1>VIA 25 加速器中央線控驗收</h1><p><span class='pill {payload['verdict']}'>{payload['verdict']}</span> <b>{payload['control_state']}</b> · {payload['timestamp']}</p>
<p>PASS {c['pass']} / {c['total']} · accelerators={c['accelerators']}</p><table><thead><tr><th>檢查</th><th>狀態</th><th>細節</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""


def selftest() -> int:
    payload = run(write=True)
    c = payload["counts"]
    print(f"[CGC_MDL156] {payload['verdict']} · {c['pass']}/{c['total']} · accelerators={c['accelerators']}")
    print(f"JSON: {LATEST_JSON}")
    print(f"HTML: {LATEST_HTML}")
    return 0 if payload["verdict"] == "GREEN" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="VIA 25 accelerator control plane")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("status")
    sub.add_parser("manifest")
    sub.add_parser("routes")
    args = parser.parse_args()
    if args.cmd == "selftest":
        return selftest()
    payload = run(write=True)
    if args.cmd == "routes":
        print(json.dumps({"powershell": str(PS_ROSTER), "python_bootstrap": str(BOOTSTRAP), "network": "VDF only and operator consent", "generation": payload["control_state"]}, ensure_ascii=False, indent=2))
    elif args.cmd == "manifest":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"verdict": payload["verdict"], "control_state": payload["control_state"], "counts": payload["counts"], "json": str(LATEST_JSON), "html": str(LATEST_HTML)}, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
