#!/usr/bin/env python3
"""One Python governance controller for VIA Python + JavaScript scraping engines."""
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

# =============================================================================
# def 00 PARAMETERS / SSOT
# =============================================================================
import argparse
import ast
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

CONTROLLER_NAME = "VIA Dual WebScraping Governance Controller"
CONTROLLER_VERSION = "1.0.0"
BASE_DIR = Path(__file__).resolve().parent
PYTHON_ENGINE = BASE_DIR / "VIA_Unified_WebScraping_Playwright_Engine.py"
JAVASCRIPT_ENGINE = BASE_DIR / "VIA_WebScraping_Playwright_Engine.js"
REPORT_TYPE_SSOT = BASE_DIR / "VIA_Investment_Report_Type_SSOT.json"
PYTHON_CLASSIFIER = BASE_DIR / "VIA_Investment_Report_Classifier.py"
JAVASCRIPT_CLASSIFIER = BASE_DIR / "VIA_Investment_Report_Classifier.js"
COMPLIANCE_SSOT = BASE_DIR / "VIA_WebScraping_Compliance_SSOT.json"
PYTHON_COMPLIANCE = BASE_DIR / "VIA_WebScraping_Compliance.py"
JAVASCRIPT_COMPLIANCE = BASE_DIR / "VIA_WebScraping_Compliance.js"
DEFAULT_OUTPUT_DIR = Path("via_dual_webscraping_output")
DEFAULT_TIMEOUT_SECONDS = 1800
VALID_MODES = {"auto", "python", "javascript", "dual", "diagnose"}
BLOCK_RE = re.compile(r"captcha|verify you are human|access denied|unusual traffic", re.I)

ACCELERATORS = {
    "A01": "AST Precision Parser", "A02": "Cross-Language Contract Alignment",
    "A03": "Hydra Risk Detection", "A04": "Dependency Topology",
    "A05": "Sandbox Process Isolation", "A06": "Safe Repair Proposal",
    "A07": "Three-Round Panorama", "A08": "SSOT Regex Alignment",
    "A09": "Matrix Report", "A10": "Finding Classification",
    "A11": "Performance Budget", "A12": "Dual-Engine Synchronization",
    "A13": "Version And Hash Snapshot", "A14": "Regression Gate",
    "A15": "Execution Order Optimizer", "A16": "Progress Events",
    "A17": "Status Narration", "A18": "Non-Blocking Subprocess",
    "A19": "Python Node Integration", "A20": "Environment Preflight",
}

PY_REQUIRED_DYNAMIC = ["playwright"]
PY_RECOMMENDED = ["httpx", "bs4", "lxml", "trafilatura", "readability", "extruct", "html2text", "pyarrow", "duckdb"]
JS_REQUIRED = ["playwright", "jsdom", "@mozilla/readability", "robots-parser"]
JS_RECOMMENDED = ["cheerio", "undici", "ajv", "bottleneck", "p-retry", "better-sqlite3"]


# =============================================================================
# def 01 CONTRACTS
# =============================================================================
@dataclass
class Capability:
    name: str
    available: bool
    required: bool
    lane: str
    detail: str = ""


@dataclass
class EngineHealth:
    lane: str
    file: str
    exists: bool
    syntax_pass: bool
    runtime_available: bool
    capabilities: list[Capability] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    sha256: str = ""
    gate: str = "FAIL_CLOSED"


@dataclass
class RunResult:
    lane: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    output_dir: str
    gate: str


# =============================================================================
# def 02 UTILITIES / ACCELERATORS
# =============================================================================
def def_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def def_atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def def_python_module_available(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


def def_node_module_available(name: str) -> bool:
    node = shutil.which("node")
    if not node:
        return False
    result = subprocess.run([node, "-e", f"require.resolve({json.dumps(name)})"], cwd=BASE_DIR,
                            capture_output=True, text=True, timeout=15, check=False)
    return result.returncode == 0


def def_emit(percent: int, status: str, message: str) -> None:
    print(f"def [{percent:3d}%] [{status}] {message}", flush=True)


# =============================================================================
# def 03 THREE-ROUND PANORAMA / PREFLIGHT
# =============================================================================
def def_check_python_engine(dynamic_required: bool) -> EngineHealth:
    health = EngineHealth("python", str(PYTHON_ENGINE), PYTHON_ENGINE.exists(), False, bool(sys.executable))
    if health.exists:
        try:
            ast.parse(PYTHON_ENGINE.read_text(encoding="utf-8")); health.syntax_pass = True
        except SyntaxError as exc:
            health.findings.append(f"PY_AST_ERROR:{exc}")
        health.sha256 = def_hash_file(PYTHON_ENGINE)
    required = set(PY_REQUIRED_DYNAMIC if dynamic_required else [])
    for name in PY_REQUIRED_DYNAMIC + PY_RECOMMENDED:
        available = def_python_module_available(name)
        health.capabilities.append(Capability(name, available, name in required, "python"))
        if name in required and not available: health.findings.append(f"REQUIRED_MODULE_MISSING:{name}")
    health.gate = "PASS" if health.exists and health.syntax_pass and not any(x.startswith("REQUIRED_") for x in health.findings) else "FAIL_CLOSED"
    return health


def def_check_javascript_engine() -> EngineHealth:
    node = shutil.which("node")
    health = EngineHealth("javascript", str(JAVASCRIPT_ENGINE), JAVASCRIPT_ENGINE.exists(), False, bool(node))
    if health.exists and node:
        check = subprocess.run([node, "--check", str(JAVASCRIPT_ENGINE)], capture_output=True, text=True, timeout=30, check=False)
        health.syntax_pass = check.returncode == 0
        if check.returncode: health.findings.append(f"JS_SYNTAX_ERROR:{check.stderr.strip()}")
        health.sha256 = def_hash_file(JAVASCRIPT_ENGINE)
    elif not node:
        health.findings.append("NODE_RUNTIME_MISSING")
    for name in JS_REQUIRED + JS_RECOMMENDED:
        available = def_node_module_available(name)
        health.capabilities.append(Capability(name, available, name in JS_REQUIRED, "javascript"))
        if name in JS_REQUIRED and not available: health.findings.append(f"REQUIRED_MODULE_MISSING:{name}")
    health.gate = "PASS" if health.exists and health.syntax_pass and health.runtime_available and not any(x.startswith("REQUIRED_") for x in health.findings) else "FAIL_CLOSED"
    return health


def def_panorama(mode: str) -> dict[str, Any]:
    def_emit(8, "INFO", "Round 1 · AST and runtime inventory")
    python = def_check_python_engine(dynamic_required=mode in {"python", "dual"})
    javascript = def_check_javascript_engine()
    def_emit(20, "INFO", "Round 2 · SSOT, dependency, and Hydra alignment")
    conflicts = []
    for required_file in (REPORT_TYPE_SSOT, PYTHON_CLASSIFIER, JAVASCRIPT_CLASSIFIER,
                          COMPLIANCE_SSOT, PYTHON_COMPLIANCE, JAVASCRIPT_COMPLIANCE):
        if not required_file.exists(): conflicts.append(f"REQUIRED_SUPPORT_FILE_MISSING:{required_file.name}")
    if REPORT_TYPE_SSOT.exists():
        try:
            report_ssot = json.loads(REPORT_TYPE_SSOT.read_text(encoding="utf-8-sig"))
            if len(report_ssot.get("types", {})) < 30: conflicts.append("REPORT_TYPE_SSOT_INCOMPLETE")
        except Exception as exc: conflicts.append(f"REPORT_TYPE_SSOT_INVALID:{exc}")
    if PYTHON_ENGINE.resolve() == JAVASCRIPT_ENGINE.resolve(): conflicts.append("ENGINE_PATH_COLLISION")
    if not BLOCK_RE.search(PYTHON_ENGINE.read_text(encoding="utf-8", errors="ignore")) if PYTHON_ENGINE.exists() else True:
        conflicts.append("PY_BLOCK_PAGE_POLICY_MISSING")
    if not BLOCK_RE.search(JAVASCRIPT_ENGINE.read_text(encoding="utf-8", errors="ignore")) if JAVASCRIPT_ENGINE.exists() else True:
        conflicts.append("JS_BLOCK_PAGE_POLICY_MISSING")
    def_emit(32, "INFO", "Round 3 · regression readiness and execution order")
    return {"controller": CONTROLLER_NAME, "version": CONTROLLER_VERSION, "generated_at": def_now(),
            "accelerators": ACCELERATORS, "python": asdict(python), "javascript": asdict(javascript),
            "hydra_findings": conflicts, "gate": "PASS" if not conflicts else "FAIL_CLOSED"}


# =============================================================================
# def 04 ROUTING / NON-BLOCKING EXECUTION
# =============================================================================
def def_choose_lanes(mode: str, panorama: dict[str, Any]) -> list[str]:
    if mode == "diagnose": return []
    if mode == "python": return ["python"]
    if mode == "javascript": return ["javascript"]
    if mode == "dual": return ["python", "javascript"]
    if panorama["javascript"]["gate"] == "PASS": return ["javascript"]
    return ["python"]


def def_build_command(lane: str, urls: list[str], output_dir: Path, args: argparse.Namespace) -> list[str]:
    common = urls + ["--output-dir", str(output_dir), "--max-pages", str(args.max_pages),
                     "--max-depth", str(args.max_depth), "--delay", str(args.delay)]
    if args.wait_selector: common += ["--wait-selector", args.wait_selector]
    for selector in args.click: common += ["--click", selector]
    if args.headed: common += ["--headed"]
    common += ["--consent-token", args.consent_token, "--purpose", args.purpose,
               "--authorization-basis", args.authorization_basis, "--pii-mode", args.pii_mode]
    if lane == "python": return [sys.executable, str(PYTHON_ENGINE), "--backend", args.python_backend] + common
    return [shutil.which("node") or "node", str(JAVASCRIPT_ENGINE), "--browser", args.browser] + common


async def def_run_lane(lane: str, command: list[str], output_dir: Path, timeout: int) -> RunResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    process = await asyncio.create_subprocess_exec(*command, cwd=BASE_DIR,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "PYTHONUNBUFFERED": "1"})
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.terminate(); await process.wait()
        return RunResult(lane, command, 124, "", "ENGINE_TIMEOUT", str(output_dir), "FAIL_CLOSED")
    code = process.returncode or 0
    return RunResult(lane, command, code, stdout.decode(errors="replace"), stderr.decode(errors="replace"),
                     str(output_dir), "PASS" if code == 0 else "COMPLETED_WITH_FINDINGS" if code == 3 else "FAIL_CLOSED")


def def_read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists(): return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
    return rows


def def_cross_validate(root: Path) -> dict[str, Any]:
    py_rows = {x.get("canonical_url") or x.get("url"): x for x in def_read_jsonl(root / "python" / "pages.jsonl")}
    js_rows = {x.get("canonical_url") or x.get("url"): x for x in def_read_jsonl(root / "javascript" / "pages.jsonl")}
    comparisons = []
    for url in sorted(set(py_rows) | set(js_rows)):
        left, right = py_rows.get(url, {}), js_rows.get(url, {})
        comparisons.append({"url": url, "python_present": bool(left), "javascript_present": bool(right),
            "title_match": bool(left and right and left.get("title") == right.get("title")),
            "published_at_match": bool(left and right and left.get("published_at") == right.get("published_at")),
            "content_hash_match": bool(left and right and left.get("content_sha256") == right.get("content_sha256")),
            "report_type_match": bool(left and right and left.get("report_classification", {}).get("report_type_code") == right.get("report_classification", {}).get("report_type_code")),
            "python_gate": left.get("quality_gate", "MISSING"), "javascript_gate": right.get("quality_gate", "MISSING")})
    return {"compared_urls": len(comparisons), "comparisons": comparisons,
            "gate": "PASS" if comparisons and all(x["python_present"] and x["javascript_present"] for x in comparisons) else "REVIEW_REQUIRED"}


async def def_execute(args: argparse.Namespace, panorama: dict[str, Any]) -> dict[str, Any]:
    lanes = def_choose_lanes(args.mode, panorama)
    for lane in lanes:
        if panorama[lane]["gate"] != "PASS":
            raise RuntimeError(f"{lane.upper()}_PREFLIGHT_FAIL_CLOSED:{panorama[lane]['findings']}")
    root = args.output_dir.resolve(); root.mkdir(parents=True, exist_ok=True)
    tasks = []
    for lane in lanes:
        lane_dir = root / lane
        command = def_build_command(lane, args.urls, lane_dir, args)
        tasks.append(def_run_lane(lane, command, lane_dir, args.timeout_seconds))
    def_emit(50, "INFO", f"Launching governed lanes: {', '.join(lanes) or 'diagnose-only'}")
    results = await asyncio.gather(*tasks) if tasks else []
    validation = def_cross_validate(root) if set(lanes) == {"python", "javascript"} else {"gate": "NOT_APPLICABLE"}
    gate = "PASS" if all(x.gate == "PASS" for x in results) and validation["gate"] in {"PASS", "NOT_APPLICABLE"} else "COMPLETED_WITH_FINDINGS"
    return {"controller": CONTROLLER_NAME, "version": CONTROLLER_VERSION, "mode": args.mode,
            "generated_at": def_now(), "panorama": panorama, "runs": [asdict(x) for x in results],
            "cross_validation": validation, "gate": gate}


# =============================================================================
# def 05 REPORT / SELF-TEST / CLI
# =============================================================================
def def_html_report(report: dict[str, Any], path: Path) -> None:
    rows = []
    for lane in ("python", "javascript"):
        health = report["panorama"][lane]
        rows.append(f"<tr><td>{lane}</td><td>{health['gate']}</td><td>{health['syntax_pass']}</td><td>{len(health['findings'])}</td><td>{'<br>'.join(health['findings']) or 'None'}</td></tr>")
    html = f"""<!doctype html><meta charset='utf-8'><title>VIA Dual Engine Matrix</title>
    <style>body{{font:12px Inter,Arial;background:#f7fafc;color:#223;padding:18px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #dce4ec;padding:7px;vertical-align:top;overflow-wrap:anywhere}}th{{background:#eaf2f8}}.pass{{color:#16784b}}</style>
    <h1>VIA Dual WebScraping Governance Matrix</h1><p>Gate: <b class='pass'>{report['gate']}</b> · {report['generated_at']}</p>
    <table><tr><th>ENGINE</th><th>GATE</th><th>SYNTAX</th><th>FINDINGS</th><th>DETAIL</th></tr>{''.join(rows)}</table>
    <h2>Cross Validation</h2><pre>{json.dumps(report['cross_validation'], ensure_ascii=False, indent=2)}</pre>"""
    path.write_text(html, encoding="utf-8")


def def_self_test() -> None:
    assert len(ACCELERATORS) == 20
    ast.parse(PYTHON_ENGINE.read_text(encoding="utf-8"))
    assert JAVASCRIPT_ENGINE.exists()
    assert REPORT_TYPE_SSOT.exists() and PYTHON_CLASSIFIER.exists() and JAVASCRIPT_CLASSIFIER.exists()
    assert COMPLIANCE_SSOT.exists() and PYTHON_COMPLIANCE.exists() and JAVASCRIPT_COMPLIANCE.exists()
    health = def_panorama("diagnose")
    assert health["python"]["syntax_pass"]


def def_parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=CONTROLLER_NAME)
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="auto")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--python-backend", choices=["auto", "playwright", "httpx", "urllib"], default="auto")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium")
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--wait-selector", default="")
    parser.add_argument("--click", action="append", default=[])
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--consent-token", default="")
    parser.add_argument("--purpose", default="")
    parser.add_argument("--authorization-basis", default="")
    parser.add_argument("--pii-mode", choices=["partial", "full", "off"], default="partial")
    return parser.parse_args(argv)


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    args = def_parse_args(argv)
    if args.self_test:
        def_self_test(); print("def CONTROLLER_SELF_TEST: PASS")
        if not args.urls: return 0
    if args.mode != "diagnose" and not args.urls:
        print("def ERROR: 請提供至少一個 URL，或使用 --mode diagnose", file=sys.stderr); return 2
    if args.mode != "diagnose":
        from VIA_WebScraping_Compliance import def_load_compliance_ssot, def_validate_consent
        compliance_ssot = def_load_compliance_ssot()
        consent_findings = def_validate_consent(args.consent_token, args.purpose, args.authorization_basis, compliance_ssot)
        if consent_findings:
            print("def RISK_NOTICE:", file=sys.stderr)
            for item in compliance_ssot["risk_notice"]: print(f"def - {item}", file=sys.stderr)
            print("def CONSENT_REQUIRED: --consent-token I_ACCEPT_RESPONSIBLE_SCRAPING --purpose <用途> --authorization-basis <授權依據>", file=sys.stderr)
            return 4
    panorama = def_panorama(args.mode)
    try:
        report = asyncio.run(def_execute(args, panorama))
    except Exception as exc:
        print(f"def FAIL_CLOSED: {exc}", file=sys.stderr); return 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    def_atomic_json(args.output_dir / "governance_report.json", report)
    def_html_report(report, args.output_dir / "governance_matrix.html")
    def_emit(100, report["gate"], "Governed execution completed")
    print(json.dumps({"gate": report["gate"], "output_dir": str(args.output_dir.resolve())}, ensure_ascii=False, indent=2))
    return 0 if report["gate"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(def_main())
