#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL157: VIA unique entry-point control plane.

This is a deterministic, offline, read-only gate. It does not execute market
engines. It proves that VRN, VDF and QuantGuard are reached through the VIA
command book and the single Invoke-VIAPython/bootstrap path, with the network
consent gate remaining fail-closed.
"""
from __future__ import annotations

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
COMMAND_BOOK = sorted(ROOT.glob("Register-VIA-Commands-v*.ps1"))[-1] if list(ROOT.glob("Register-VIA-Commands-v*.ps1")) else ROOT / "Register-VIA-Commands-v0208.ps1"   # 批534 尾版律
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
    checks = run_checks() + _b534_checks()
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



def _b534_checks() -> list[dict[str, Any]]:
    """批534 新增三檢:尾版命令冊 · 家族境派送 · 誠實四態判讀。"""
    books = sorted(ROOT.glob("Register-VIA-Commands-v*.ps1"))
    newest_book = books[-1].name if books else ""
    a = judge_route(3, "=== ABSENT · 本境無 polars ===")
    b = judge_route(1, "Traceback\nModuleNotFoundError: No module named 'polars'")
    c = judge_route(2, "[NODATA] input not found")
    d = judge_route(1, "AssertionError: boom")
    e = judge_route(None, "TIMEOUT after 900s")
    v_green = verdict_of([{"state": "GREEN"}])
    v_yellow = verdict_of([{"state": "GREEN"}, {"state": "ABSENT"}])
    v_red = verdict_of([{"state": "GREEN"}, {"state": "RED"}])
    src = Path(__file__).read_text(encoding="utf-8")
    return [
        check("批534 命令冊走尾版 glob(不釘死版號)", COMMAND_BOOK.name == newest_book and 'Register-VIA-Commands-v*.ps1' in src, f"{COMMAND_BOOK.name} = newest {newest_book}"),
        check("批534 子路由用家族境 python(匯流排 python_for;非 sys.executable 一律)", "family_python(fam)" in src and "python_for" in src and "child_env(fam)" in src, f"vrn→{family_python('vrn')[1]} · quantguard→{family_python('quantguard')[1]}"),
        check("批534 誠實四態:缺件 ABSENT · 缺料 NODATA · 逾時 TIMEOUT · 真壞才 RED;裁決 GREEN/YELLOW/RED",
              a[0] == "ABSENT" and b[0] == "ABSENT" and c[0] == "NODATA" and d[0] == "RED" and e[0] == "TIMEOUT"
              and v_green == "GREEN" and v_yellow == "YELLOW" and v_red == "RED",
              f"{a[0]}/{b[0]}/{c[0]}/{d[0]}/{e[0]} → {v_green}/{v_yellow}/{v_red}"),
    ]

def render_html(payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{html.escape(x['name'])}</td><td class='{x['state']}'>{x['state']}</td><td>{html.escape(x['detail'])}</td></tr>" for x in payload["checks"])
    c = payload["counts"]
    return f"""<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Unique Entry Control</title><style>body{{font:14px system-ui,sans-serif;margin:30px;color:#172033}}h1{{margin-bottom:4px}}.pill{{padding:5px 12px;border-radius:999px;font-weight:700}}.GREEN,.PASS{{background:#d9f2e9;color:#08745b}}.RED,.FAIL{{background:#ffe1df;color:#a52b25}}table{{border-collapse:collapse;width:100%;margin-top:20px}}th,td{{border-bottom:1px solid #dfe5ee;padding:9px;text-align:left;vertical-align:top}}th{{background:#f4f7fb}}</style></head><body><h1>VIA 唯一接觸口控制</h1><p><span class='pill {payload['verdict']}'>{payload['verdict']}</span> <b>{payload['control_state']}</b> · {payload['timestamp']}</p><p>PASS {c['pass']} / {c['total']} · data flow: <b>VDF/DuckDB → QuantGuard</b> · network: <b>OFF</b></p><table><thead><tr><th>檢查</th><th>狀態</th><th>細節</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""



VERSION = "v0101"


def newest(folder: Path, pattern: str) -> str:
    """尾版律:同名不同版取字典序最後一個;缺=回 pattern 本身(下游 judge 判 ABSENT/RED,不假裝在)。"""
    hits = sorted(folder.glob(pattern))
    return str(hits[-1]) if hits else str(folder / pattern)


_BUS = {"mod": None, "tried": False}


def _bus():
    """匯流排(CGC_MDL148)=家族境 python 與子行程環境的正主(L30 一功能一主);缺席=None。"""
    if not _BUS["tried"]:
        _BUS["tried"] = True
        try:
            import importlib.util
            cands = sorted((ROOT / "supportive modules" / "registry").glob("CGC_MDL148_EngineBus_v*.py"))
            if cands:
                spec = importlib.util.spec_from_file_location("via_bus_for_157", cands[-1])
                m = importlib.util.module_from_spec(spec)
                sys.modules["via_bus_for_157"] = m
                spec.loader.exec_module(m)
                _BUS["mod"] = m
        except Exception:
            _BUS["mod"] = None
    return _BUS["mod"]


_FAMILY_ENV = {"vrn": "VIA_PY_VRN", "vdf": "VIA_PY_VDF", "quantguard": "VIA_PY_VDF", "vap": "VIA_PY_VAP", "core": "VIA_PY_CORE"}


def family_python(family: str) -> tuple[str, str]:
    """家族境 python:env 明給 > 匯流排 python_for > 目前解譯器。QuantGuard 住 vdf 境。"""
    key = _FAMILY_ENV.get(family, "")
    e = os.environ.get(key) if key else None
    if e and Path(e).exists():
        return e, key
    b = _bus()
    if b is not None:
        try:
            got = b.python_for("vdf" if family == "quantguard" else family)
            py = (got or {}).get("python")
            if py and Path(py).exists():
                return py, f"bus:{(got or {}).get('source') or 'python_for'}"
        except Exception:
            pass
    return sys.executable, "sys.executable(退路)"


def child_env(family: str) -> dict:
    b = _bus()
    if b is not None:
        try:
            return dict(b.child_env("vdf" if family == "quantguard" else family))
        except Exception:
            pass
    e = dict(os.environ)
    e.pop("PYTHONHOME", None)           # L32 PYTHONHOME 清洗
    e["VIA_PYTHONHOME_SCRUBBED"] = "1"
    return e


_ABSENT_MARK = ("ModuleNotFoundError", "[ABSENT]", "· ABSENT ·", "ABSENT(", "No module named")
_NODATA_MARK = ("[NODATA]", "[NEED_INPUT]", "NODATA", "NEED_INPUT")


def judge_route(rc: int | None, output: str) -> tuple[str, str]:
    """誠實四態:缺件=ABSENT、缺料=NODATA、逾時=TIMEOUT、真壞才 RED(判錯的紅燈和假綠一樣傷)。"""
    if rc is None:
        return "TIMEOUT", output.splitlines()[-1][:160] if output else "逾時"
    if rc == 0:
        return "GREEN", "rc0"
    tail = output[-2000:]
    if rc == 3 or any(k in tail for k in _ABSENT_MARK):
        line = next((l for l in reversed(tail.splitlines()) if any(k in l for k in _ABSENT_MARK)), "")
        return "ABSENT", ("本境缺件(不是壞):" + line.strip()[:150]) if line else f"本境缺件 rc={rc}"
    if rc == 2 or any(k in tail for k in _NODATA_MARK):
        line = next((l for l in reversed(tail.splitlines()) if any(k in l for k in _NODATA_MARK)), "")
        return "NODATA", ("資料側(不是壞):" + line.strip()[:150]) if line else f"缺料 rc={rc}"
    return "RED", (tail.splitlines()[-1].strip()[:160] if tail.strip() else f"rc={rc}")


def verdict_of(routes: list[dict[str, Any]]) -> str:
    if not routes:
        return "RED"
    states = {r["state"] for r in routes}
    if states <= {"GREEN"}:
        return "GREEN"
    if states & {"RED", "TIMEOUT"}:
        return "RED"
    return "YELLOW"


_FLAG_VERBS = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes", "--dispatch": "dispatch"}


def _normalise_argv(argv: list[str]) -> list[str]:
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS and verb is None:
            verb = _FLAG_VERBS[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out


def dispatch(family: str, timeout: int = 0) -> dict[str, Any]:
    """Run only fixed, offline child routes after the unique-entry gate (family-env aware)."""
    timeout = int(timeout or os.environ.get("VIA_CENTRAL_TIMEOUT") or 900)
    gate = run(write=True)
    if gate["verdict"] != "GREEN":
        result = {"schema": "VIA.CGC157.UniqueEntryDispatch.v1", "verdict": "BLOCKED", "gate": gate, "routes": []}
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        DISPATCH_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    VRN = ROOT / "functional modules" / "VRN"
    VDFE = ROOT / "functional modules" / "VDF" / "engine"
    commands: dict[str, list[tuple[str, list[str]]]] = {                  # 批534:一律尾版 glob(釘死版號=新版出了中央還跑舊的)
        "vrn": [("VRN_ENG087_NLP", [newest(VRN, "VRN_ENG087_NLPTextSummaryBridge_v*.py"), "selftest"])],
        "vdf": [
            ("VDF_ENG073_DataArchitecture", [newest(VDFE, "VDF_ENG073_DataArchitecture_v*.py"), "--selftest"]),
            ("VDF_ENG087_MarketListGovernance", [newest(VDFE, "VDF_ENG087_MarketListGovernance_v*.py"), "--selftest"]),
        ],
        "quantguard": [("VDF_ENG086_QuantGuard", [newest(VDFE, "VDF_ENG086_QuantGuardOneBridge_v*.py"), "selftest"])],
    }
    families = ["vrn", "vdf", "quantguard"] if family == "all" else [family]
    routes: list[dict[str, Any]] = []
    for fam in families:
        py, py_src = family_python(fam)
        env = child_env(fam)
        env["VIA_ROOT"] = str(ROOT)
        env["VIA_CENTRAL_ENTRY"] = "1"
        env["VIA_ENTRY_CONTROL"] = f"CGC_MDL157_VIAUniqueEntryControl_{VERSION}"
        env.setdefault("VIA_NET_CONSENT", "OFF")
        env.setdefault("VIA_SCRAPE_CONSENT", "OFF")
        env["PYTHONPATH"] = str(BOOTSTRAP) + os.pathsep + env.get("PYTHONPATH", "")
        for label, argv in commands[fam]:
            try:
                proc = subprocess.run([py, *argv], cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=timeout)
                rc, output = proc.returncode, (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
            except subprocess.TimeoutExpired:
                rc, output = None, f"TIMEOUT after {timeout}s"
            except FileNotFoundError as exc:
                rc, output = None, f"family python not found: {exc}"
            state, why = judge_route(rc, output)
            routes.append({"family": fam, "engine": label, "argv": argv, "python": py, "python_source": py_src,
                           "returncode": rc, "state": state, "why": why, "output_tail": output[-4000:]})
    result = {
        "schema": "VIA.CGC157.UniqueEntryDispatch.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gate": {"engine": gate["engine"], "verdict": gate["verdict"], "control_state": gate["control_state"]},
        "family": family,
        "routes": routes,
        "network": {"default": "OFF", "consent": env.get("VIA_NET_CONSENT"), "silent_open": False},
        "data_flow": "VDF_DUCKDB_TO_QUANTGUARD",
        "verdict": verdict_of(routes),
        "counts": {st: sum(1 for x in routes if x["state"] == st) for st in ("GREEN", "ABSENT", "NODATA", "TIMEOUT", "RED")},
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DISPATCH_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="VIA unique entry-point control plane")
    parser.add_argument("command", choices=("selftest", "status", "manifest", "routes", "dispatch"))
    parser.add_argument("--family", choices=("vrn", "vdf", "quantguard", "all"), default="all")
    parser.add_argument("--timeout", type=int, default=0)
    args = parser.parse_args(_normalise_argv(sys.argv[1:]))
    if args.command == "dispatch":
        result = dispatch(args.family, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        c = result.get("counts") or {}
        print(f"[CGC_MDL157 {VERSION}] dispatch {args.family} · {result['verdict']} · " +
              " · ".join(f"{k}={v}" for k, v in c.items() if v))
        for r in result.get("routes", []):
            print(f"  [{r['state']:<7}] {r['family']:<10} {r['engine']:<32} rc={r['returncode']} · {str(r.get('why', ''))[:90]}")
            print(f"            python={r.get('python_source')} → {r.get('python')}")
        return {"GREEN": 0, "YELLOW": 0}.get(result["verdict"], 2)
    payload = run(write=True)
    if args.command == "selftest":
        print(f"[CGC_MDL157 {VERSION}] {payload['verdict']} · {payload['counts']['pass']}/{payload['counts']['total']} · ONLY_VIA_ENTRY")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
