#!/usr/bin/env python3
"""One-click orchestrator for the VIA AzureFlow QA plug-in.

The orchestrator only coordinates the two existing deterministic validators. It
never writes to a selected source, never restarts a service, and never executes
user source. Extracted package E2E is opt-in.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent
INSPECTOR = PLUGIN_DIR / "inspect_azureflow.py"
ZIP_VALIDATOR = PLUGIN_DIR / "validate_via_zip.py"
STANDARDIZED_ZIP_VALIDATOR = PLUGIN_DIR / "validate_standardized_zip.py"
SCHEMA = "VIA_AZUREFLOW_QA_PLUGIN_RUN/1.0"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def run_child(command: list[str], stdout_path: Path, stderr_path: Path, timeout: int = 300) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        stdout_path.write_text(result.stdout or "", encoding="utf-8")
        stderr_path.write_text(result.stderr or "", encoding="utf-8")
        return {
            "exit_code": result.returncode,
            "command": display_command(command),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text((exc.stderr or "") + f"\nTimed out after {timeout}s\n", encoding="utf-8")
        return {
            "exit_code": 124,
            "command": display_command(command),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "timed_out": True,
        }


def path_state(raw: str | None, kind: str) -> dict[str, Any]:
    if not raw:
        return {"provided": False, "raw": None, "exists": False, "status": "NOT_PROVIDED", "kind": kind}
    path = Path(raw).expanduser()
    exists = path.exists()
    return {
        "provided": True,
        "raw": raw,
        "resolved": str(path.resolve()) if exists else None,
        "exists": exists,
        "status": "READY" if exists else "NOT_MOUNTED_IN_SANDBOX",
        "kind": kind,
    }


def preflight_input(raw: str | None, kind: str, required: bool) -> dict[str, Any]:
    state = path_state(raw, kind)
    if not state["provided"] and required:
        state["status"] = "REQUIRED"
    return state


def detect_package_kind(zip_path: Path) -> str:
    """Select the matching verifier without extracting an untrusted archive."""
    try:
        with zipfile.ZipFile(zip_path) as archive:
            names = [info.filename.replace("\\", "/") for info in archive.infolist()]
    except (OSError, zipfile.BadZipFile):
        return "via"
    root_manifests = [
        name for name in names
        if name.count("/") == 1 and name.endswith("/manifest.json")
    ]
    if len(root_manifests) == 1:
        return "standardized"
    if any(name.endswith("/ui/VIA-UI-Standalone-NoServer.html") for name in names):
        return "via"
    return "via"


def inspect_action(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    action_dir = out_dir / "inspect"
    report = action_dir / "VIA_AzureFlow_Engine_Job_Inspection.md"
    root_raw = args.root or "."
    root_state = preflight_input(root_raw, "workspace_root", required=True)
    command = [sys.executable, str(INSPECTOR), "--base-url", args.base_url, "--root", root_raw, "--out", str(report)]
    if args.runs_dir:
        command += ["--runs-dir", args.runs_dir]
    if args.no_artifact_probe:
        command.append("--no-artifact-probe")
    child = run_child(command, action_dir / "stdout.txt", action_dir / "stderr.txt")
    report_exists = report.is_file() and report.stat().st_size > 0
    if child["timed_out"] or child["exit_code"] != 0:
        status = "FAIL"
    elif root_state["status"] != "READY":
        status = "REVIEW_REQUIRED"
    elif report_exists:
        status = "PASS"
    else:
        status = "FAIL"
    result = {
        "action": "inspect",
        "status": status,
        "exit_code": child["exit_code"],
        "report": str(report) if report_exists else None,
        "root": root_state,
        "api": args.base_url,
        "command": child["command"],
        "stdout": child["stdout"],
        "stderr": child["stderr"],
        "report_exists": report_exists,
        "safety": {"source_write": False, "source_delete": False, "code_execution": False, "network": False, "localhost_get_only": True},
    }
    json_dump(action_dir / "inspect_summary.json", result)
    return result


def verify_action(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    action_dir = out_dir / "verify"
    result_json = action_dir / "verification.json"
    zip_state = preflight_input(args.zip, "zip", required=True)
    package_kind = args.package_kind
    if package_kind == "auto" and zip_state["exists"]:
        package_kind = detect_package_kind(Path(args.zip).expanduser())
    validator_script = STANDARDIZED_ZIP_VALIDATOR if package_kind == "standardized" else ZIP_VALIDATOR
    command: list[str] = [sys.executable, str(validator_script), args.zip or "", "--out-dir", str(action_dir / "validator"), "--json", str(result_json)]
    if args.checksum_file:
        command += ["--checksum-file", args.checksum_file]
    if args.run_extracted_e2e:
        command.append("--run-extracted-e2e")
    if not zip_state["exists"]:
        result = {
            "action": "verify",
            "status": "FAIL",
            "exit_code": 2,
            "report": None,
            "zip": zip_state,
            "package_kind": package_kind,
            "validator": str(validator_script),
            "command": display_command(command),
            "error": "ZIP path is missing or not mounted in the current environment; validator was not started.",
            "safety": {"source_write": False, "source_delete": False, "code_execution": bool(args.run_extracted_e2e), "network": False},
        }
        json_dump(action_dir / "verify_summary.json", result)
        return result
    child = run_child(command, action_dir / "stdout.txt", action_dir / "stderr.txt", timeout=900 if args.run_extracted_e2e else 300)
    validator = None
    if result_json.is_file():
        try:
            validator = json.loads(result_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            validator = None
    passed = bool(isinstance(validator, dict) and validator.get("passed") is True and child["exit_code"] == 0)
    result = {
        "action": "verify",
        "status": "PASS" if passed else "FAIL",
        "exit_code": child["exit_code"],
        "report": str(result_json) if result_json.is_file() else None,
        "zip": zip_state,
        "package_kind": package_kind,
        "validator": str(validator_script),
        "checksum_file": path_state(args.checksum_file, "checksum") if args.checksum_file else None,
        "run_extracted_e2e": bool(args.run_extracted_e2e),
        "command": child["command"],
        "stdout": child["stdout"],
        "stderr": child["stderr"],
        "validator_summary": validator.get("summary") if isinstance(validator, dict) else None,
        "validator_passed": validator.get("passed") if isinstance(validator, dict) else False,
        "safety": {"source_write": False, "source_delete": False, "code_execution": bool(args.run_extracted_e2e), "network": False},
    }
    json_dump(action_dir / "verify_summary.json", result)
    return result


def combined_status(actions: dict[str, dict[str, Any]]) -> str:
    statuses = [item.get("status") for item in actions.values()]
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status in {"REVIEW_REQUIRED", "SKIPPED"} for status in statuses):
        return "REVIEW_REQUIRED"
    return "PASS"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA AzureFlow QA plug-in: inspect, verify, or run all")
    parser.add_argument("action", choices=("inspect", "verify", "all"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8766")
    parser.add_argument("--root", default=".")
    parser.add_argument("--runs-dir")
    parser.add_argument("--zip")
    parser.add_argument("--checksum-file")
    parser.add_argument("--out-dir", default="VIA_AzureFlow_QA_Output")
    parser.add_argument("--run-extracted-e2e", action="store_true")
    parser.add_argument("--package-kind", choices=("auto", "via", "standardized"), default="auto")
    parser.add_argument("--no-artifact-probe", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = now()
    actions: dict[str, dict[str, Any]] = {}
    if args.action in {"inspect", "all"}:
        actions["inspect"] = inspect_action(args, out_dir)
    if args.action in {"verify", "all"}:
        actions["verify"] = verify_action(args, out_dir)
    finished = now()
    status = combined_status(actions)
    summary = {
        "schema": SCHEMA,
        "plugin": "via-azureflow-qa-plugin",
        "action": args.action,
        "started_at": started,
        "finished_at": finished,
        "inputs": {
            "base_url": args.base_url,
            "root": args.root,
            "runs_dir": args.runs_dir,
            "zip": args.zip,
            "checksum_file": args.checksum_file,
            "run_extracted_e2e": bool(args.run_extracted_e2e),
            "out_dir": str(out_dir),
        },
        "actions": actions,
        "safety": {
            "source_write": False,
            "source_delete": False,
            "code_execution": False,
            "network": False,
            "human_review_required": True,
            "extracted_e2e_opt_in": bool(args.run_extracted_e2e),
        },
        "status": status,
    }
    summary_path = out_dir / "VIA_AzureFlow_QA_Run_Summary.json"
    json_dump(summary_path, summary)
    print(json.dumps({"status": status, "summary": str(summary_path), "actions": {k: v.get("status") for k, v in actions.items()}}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
