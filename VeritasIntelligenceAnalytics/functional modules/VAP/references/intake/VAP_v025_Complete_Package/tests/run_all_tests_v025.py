import json
import os
import hashlib
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MANIFEST = ROOT / "spec" / "vap_package_manifest_v025.json"


def def_find_browser():
    explicit = os.environ.get("VAP_BROWSER_EXECUTABLE")
    if explicit and Path(explicit).is_file():
        return explicit
    names = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "msedge"]
    discovered = next((shutil.which(name) for name in names if shutil.which(name)), None)
    if discovered:
        return discovered
    roots = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")]
    relatives = ["Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"]
    return next((str(Path(root) / relative) for root in roots if root for relative in relatives if (Path(root) / relative).is_file()), None)


def def_write_package_manifest():
    excluded_directories = {"__pycache__", "logs", "state", "saved_images", "node_modules"}
    records = {}
    for file_path in sorted(ROOT.rglob("*")):
        relative = file_path.relative_to(ROOT)
        if not file_path.is_file() or file_path == PACKAGE_MANIFEST or "output" in relative.parts or any(part in excluded_directories for part in relative.parts) or file_path.suffix == ".pyc":
            continue
        records[relative.as_posix()] = hashlib.sha256(file_path.read_bytes()).hexdigest()
    manifest = {
        "schema": "VIA-VAP-PACKAGE-MANIFEST/1.1",
        "version": "v025",
        "policy": "SHA256_EXCLUDES_THIS_MANIFEST_OUTPUT_RUNTIME_STATE_NODE_MODULES",
        "fileCount": len(records),
        "files": records,
    }
    PACKAGE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def def_run_python_suite():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return {"name": "Python Unit / Integration / Static", "passed": result.testsRun - len(result.failures) - len(result.errors), "failed": len(result.failures) + len(result.errors), "skipped": len(result.skipped)}


def def_run_node_suite():
    node = shutil.which("node")
    if not node:
        return {"name": "JavaScript Module", "passed": 0, "failed": 0, "skipped": 1, "detail": "Node not installed"}
    process = subprocess.run([node, str(ROOT / "tests" / "test_vap_core_v025.js")], cwd=ROOT, capture_output=True, text=True, timeout=60)
    return {"name": "JavaScript Module", "passed": 1 if process.returncode == 0 else 0, "failed": 0 if process.returncode == 0 else 1, "skipped": 0, "detail": (process.stdout + process.stderr).strip()}


def def_browser_capability():
    executable = def_find_browser()
    if not executable:
        return {"name": "Browser User Test", "passed": 0, "failed": 0, "skipped": 1, "detail": "No Chrome/Chromium executable installed; Workbench UAT remains Fail-Closed"}
    node = shutil.which("node")
    if not node:
        return {"name": "Browser User Test", "passed": 0, "failed": 1, "skipped": 0, "detail": "Browser exists but Node is unavailable"}
    environment = dict(os.environ)
    environment["VAP_BROWSER_EXECUTABLE"] = executable
    process = subprocess.run([node, str(ROOT / "tests" / "test_browser_uat_v025.js")], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=360)
    return {"name": "Browser User Test", "passed": 1 if process.returncode == 0 else 0, "failed": 0 if process.returncode == 0 else 1, "skipped": 0, "detail": (process.stdout + process.stderr).strip()}


def def_main():
    started = time.time()
    results = [def_run_python_suite(), def_run_node_suite(), def_browser_capability()]
    summary = {
        "schema": "VIA-VAP-PACKAGE-QA/1.0", "version": "v025",
        "status": "PASS" if sum(item["failed"] for item in results) == 0 else "FAIL",
        "passed": sum(item["passed"] for item in results), "failed": sum(item["failed"] for item in results),
        "skipped": sum(item["skipped"] for item in results), "durationSeconds": round(time.time() - started, 3),
        "results": results,
        "workbenchDefinitions": {"fullDiagnostics": 136, "userAcceptance": 72, "execution": "BROWSER_REQUIRED"},
        "verifiedContracts": ["VDF_AUTHORIZATION", "ADJUSTED_PRICE_ONLY", "TALIB_EVIDENCE", "PRICE_FORWARD_FILL", "VOLUME_ZERO_NO_CARRY", "SQLITE_READ_ONLY", "INCREMENTAL_REFRESH", "FILESYSTEM_IMAGE_SHA256", "HTTP_BRIDGE", "WORKBENCH_STRUCTURE", "OBSERVATION_RANGE_FREQUENCY_VALUE_MODE", "LATEST_VALUE_EVIDENCE_STRIP", "OBSERVATION_BOOKMARK_IDEMPOTENCY"],
        "browserTruth": "NOT_EXECUTED" if results[-1]["skipped"] else ("EXECUTED_PASS" if results[-1]["failed"] == 0 else "EXECUTED_FAIL"),
    }
    report = ROOT / "output" / "VIA_VAP_v025_Package_QA_Report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def_write_package_manifest()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(def_main())
