#!/usr/bin/env python3
"""Manifest-driven VIA AzureFlow QA system orchestrator.

This layer composes the existing three-action QA CLI without replacing it. It
adds a deterministic preflight, manifest inventory, scheduling readiness
assessment, human-review activation gate, and one human-readable system report.
It never registers a Windows task itself and never writes to selected sources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SYSTEM_SCHEMA = "VIA_AZUREFLOW_QA_SYSTEM/1.0"
PLUGIN_ID = "via-azureflow-qa-plugin"
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
QA_CLI = SCRIPT_DIR / "via_azureflow_qa.py"
MANIFEST_PATH = PLUGIN_ROOT / "plugin_manifest.json"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def state(raw: str | None, kind: str, required: bool = False) -> dict[str, Any]:
    if not raw:
        return {"provided": False, "raw": None, "resolved": None, "exists": False, "status": "REQUIRED" if required else "NOT_PROVIDED", "kind": kind}
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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def load_manifest() -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    if not MANIFEST_PATH.is_file():
        return None, [check("manifest_exists", False, str(MANIFEST_PATH))]
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [check("manifest_parse", False, str(exc))]
    checks.append(check("manifest_schema", manifest.get("schema") == "VIA_PLUGIN_MANIFEST/1.0", manifest.get("schema")))
    checks.append(check("manifest_plugin_id", manifest.get("plugin_id") == PLUGIN_ID, manifest.get("plugin_id")))
    checks.append(check("manifest_system_version", str(manifest.get("version", "")) >= "1.2.0", manifest.get("version")))
    actions = manifest.get("actions") if isinstance(manifest.get("actions"), list) else []
    checks.append(check("manifest_three_actions", [item.get("id") for item in actions if isinstance(item, dict)] == ["inspect", "verify", "all"], actions))
    entrypoints = manifest.get("entrypoints") if isinstance(manifest.get("entrypoints"), dict) else {}
    required_entrypoints = [
        "python_cli", "windows_launcher", "scheduled_runner", "task_registration", "task_test",
        "unified_system_python", "unified_system_windows", "standalone_ui", "interactive_architecture",
    ]
    missing_entrypoints = [key for key in required_entrypoints if not entrypoints.get(key)]
    checks.append(check("manifest_system_entrypoints", not missing_entrypoints, missing_entrypoints or required_entrypoints))
    file_paths = {
        "manifest": "plugin_manifest.json",
        "python_cli": entrypoints.get("python_cli"),
        "windows_launcher": entrypoints.get("windows_launcher"),
        "scheduled_runner": entrypoints.get("scheduled_runner"),
        "task_registration": entrypoints.get("task_registration"),
        "task_test": entrypoints.get("task_test"),
        "unified_system_python": entrypoints.get("unified_system_python"),
        "unified_system_windows": entrypoints.get("unified_system_windows"),
        "standalone_ui": entrypoints.get("standalone_ui"),
        "interactive_architecture": entrypoints.get("interactive_architecture"),
        "architecture_source": entrypoints.get("architecture_source"),
    }
    missing_files = []
    file_inventory = []
    for label, rel in file_paths.items():
        if not isinstance(rel, str) or not rel or " " in rel:
            missing_files.append({"label": label, "path": rel})
            continue
        path = PLUGIN_ROOT / rel
        item = {"label": label, "path": rel, "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0}
        if path.is_file():
            item["sha256"] = sha256(path)
        else:
            missing_files.append(item)
        file_inventory.append(item)
    checks.append(check("manifest_entrypoint_files", not missing_files, missing_files or file_inventory))
    pycache = [str(path.relative_to(PLUGIN_ROOT)) for path in PLUGIN_ROOT.rglob("__pycache__")]
    checks.append(check("runtime_cache_observation", True, {"ignored_for_runtime": pycache, "package_builder_must_exclude": True}))
    return manifest, checks


def run_qa(args: argparse.Namespace, out_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    qa_dir = out_dir / "qa"
    command = [
        sys.executable, str(QA_CLI), "all",
        "--base-url", args.base_url,
        "--root", args.root or "",
        "--zip", args.zip or "",
        "--out-dir", str(qa_dir),
        "--package-kind", args.package_kind,
    ]
    if args.runs_dir:
        command += ["--runs-dir", args.runs_dir]
    if args.checksum_file:
        command += ["--checksum-file", args.checksum_file]
    if args.run_extracted_e2e:
        command.append("--run-extracted-e2e")
    if args.no_artifact_probe:
        command.append("--no-artifact-probe")
    qa_stdout = out_dir / "qa_stdout.txt"
    qa_stderr = out_dir / "qa_stderr.txt"
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=1200)
        qa_stdout.write_text(result.stdout or "", encoding="utf-8")
        qa_stderr.write_text(result.stderr or "", encoding="utf-8")
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        qa_stdout.write_text(exc.stdout or "", encoding="utf-8")
        qa_stderr.write_text((exc.stderr or "") + "\nTimed out after 1200 seconds\n", encoding="utf-8")
        exit_code = 124
    summary_path = qa_dir / "VIA_AzureFlow_QA_Run_Summary.json"
    summary: dict[str, Any] = {}
    if summary_path.is_file():
        try:
            loaded = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                summary = loaded
        except (OSError, UnicodeError, json.JSONDecodeError):
            summary = {}
    return {
        "status": summary.get("status", "FAIL" if exit_code else "REVIEW_REQUIRED"),
        "exit_code": exit_code,
        "command": command,
        "summary": str(summary_path) if summary_path.is_file() else None,
        "summary_exists": summary_path.is_file(),
        "stdout": str(qa_stdout),
        "stderr": str(qa_stderr),
        "actions": summary.get("actions", {}),
    }, summary


def render_markdown(report: dict[str, Any]) -> str:
    qa = report["qa"]
    scheduling = report["scheduling"]
    activation = report["activation"]
    lines = [
        "# VIA 天青智流 AzureFlow QA Plug-in 完整系統報告",
        "",
        f"**檢查時間：** {report['finished_at']}  ",
        f"**Plug-in：** `{report['plugin']}`  ",
        f"**版本：** `{report['version']}`  ",
        f"**系統狀態：** `{report['status']}`  ",
        "",
        "## 1. 執行摘要",
        "",
        "此報告以 `plugin_manifest.json` 為單一契約入口，依序完成 manifest preflight、AzureFlow inspect、ZIP verify、combined handoff 與 Windows Task Scheduler readiness 評估。排程註冊不會在本 Python system layer 自動發生，必須由 Windows PowerShell 的明確 `-ActivateSchedule` 開關與人工審核觸發。",
        "",
        f"- Manifest checks：`{report['manifest_summary']['passed']}/{report['manifest_summary']['total']}` PASS。",
        f"- QA combined status：`{qa.get('status')}`；exit code=`{qa.get('exit_code')}`。",
        f"- Task Scheduler readiness：`{scheduling.get('status')}`。",
        f"- Activation gate：`{activation.get('status')}`；registered=`{activation.get('registered')}`。",
        "",
        "## 2. Manifest 與核心檔案矩陣",
        "",
        "| 名稱 | 路徑 | 存在 | bytes | SHA-256 |\n|---|---|---:|---:|---|",
    ]
    for item in report["manifest_inventory"]:
        lines.append(f"| `{item['label']}` | `{item['path']}` | {item['exists']} | {item['bytes']} | `{item.get('sha256', 'n/a')}` |")
    lines += [
        "",
        "## 3. QA 三動作與輸出",
        "",
        "| Action | Status | Exit code | Summary |\n|---|---|---:|---|",
    ]
    for name, value in (qa.get("actions") or {}).items():
        lines.append(f"| `{name}` | `{value.get('status', 'n/a')}` | `{value.get('exit_code', 'n/a')}` | `{value.get('report') or value.get('summary') or 'n/a'}` |")
    lines += [
        "",
        f"- Combined summary：`{qa.get('summary')}`。",
        f"- stdout：`{qa.get('stdout')}`。",
        f"- stderr：`{qa.get('stderr')}`。",
        "",
        "## 4. Task Scheduler readiness",
        "",
        f"- 狀態：`{scheduling.get('status')}`。",
        f"- Windows registration script：`{scheduling.get('registration_script')}`。",
        f"- Scheduled runner：`{scheduling.get('scheduled_runner')}`。",
        f"- CMD wrapper：`{scheduling.get('cmd_wrapper')}`。",
        f"- Current host supports Windows Task Scheduler：`{scheduling.get('windows_runtime_available')}`。",
        "- 每次排程必須使用 timestamped directory，保留 `task_scheduler.log`、`task_result.json` 與 combined summary。",
        "",
        "## 5. Activation gate",
        "",
        f"- 狀態：`{activation.get('status')}`。",
        f"- registered：`{activation.get('registered')}`。",
        f"- automatic registration：`{activation.get('automatic_registration')}`。",
        f"- human review required：`{activation.get('human_review_required')}`。",
        f"- activation command：`{activation.get('command')}`。",
        "",
        "## 6. 安全邊界",
        "",
        "- `source_write=false`、`source_delete=false`、`code_execution=false`（除非明確 opt-in packaged E2E）、`network=false`（inspect 僅允許指定 localhost GET）。",
        "- 不會因 API 安靜或不可用而重啟服務。",
        "- 不會自動 promotion SSOT、不會自動批准或執行 command、不會改寫使用者來源檔案。",
        "",
        "## 7. 可重跑輸出位置",
        "",
        f"- System JSON：`{report['json_path']}`。",
        f"- System Markdown：`{report['markdown_path']}`。",
        f"- Plugin root：`{report['plugin_root']}`。",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA AzureFlow QA manifest-driven complete system")
    parser.add_argument("--root", required=True)
    parser.add_argument("--zip", required=True)
    parser.add_argument("--checksum-file")
    parser.add_argument("--runs-dir")
    parser.add_argument("--base-url", default="http://127.0.0.1:8766")
    parser.add_argument("--package-kind", choices=("auto", "via", "standardized"), default="auto")
    parser.add_argument("--out-dir", default="VIA_AzureFlow_QA_System_Output")
    parser.add_argument("--run-extracted-e2e", action="store_true")
    parser.add_argument("--no-artifact-probe", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = now()
    manifest, manifest_checks = load_manifest()
    manifest = manifest or {}
    inventory = []
    entrypoint_check = next((item for item in manifest_checks if item.get("name") == "manifest_entrypoint_files"), None)
    for item in (entrypoint_check.get("detail", []) if entrypoint_check else []):
        if isinstance(item, dict) and "label" in item:
            inventory.append(item)
    if not inventory:
        entrypoints = manifest.get("entrypoints") if isinstance(manifest.get("entrypoints"), dict) else {}
        for label, rel in entrypoints.items():
            if isinstance(rel, str) and " " not in rel:
                path = PLUGIN_ROOT / rel
                inventory.append({"label": label, "path": rel, "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0, "sha256": sha256(path) if path.is_file() else None})
    root_state = state(args.root, "workspace_root", required=True)
    zip_state = state(args.zip, "zip", required=True)
    checksum_state = state(args.checksum_file, "checksum") if args.checksum_file else None
    qa, qa_summary = run_qa(args, out_dir)
    manifest_summary = {"total": len(manifest_checks), "passed": sum(1 for item in manifest_checks if item["passed"]), "failed": sum(1 for item in manifest_checks if not item["passed"])}
    scheduler_files = {
        "scheduled_runner": str(PLUGIN_ROOT / "scripts" / "Invoke-VIA-AzureFlowQA-Scheduled.ps1"),
        "registration_script": str(PLUGIN_ROOT / "scripts" / "Register-VIAAzureFlowQATask.ps1"),
        "task_test": str(PLUGIN_ROOT / "scripts" / "Test-VIAAzureFlowQATask.ps1"),
        "cmd_wrapper": str(PLUGIN_ROOT / "Run-VIAAzureFlowQAScheduled.cmd"),
    }
    missing_scheduler = [path for path in scheduler_files.values() if not Path(path).is_file()]
    windows_runtime = os.name == "nt"
    scheduling_status = "READY" if not missing_scheduler else "BLOCKED"
    activation_status = "READY_FOR_WINDOWS_ACTIVATION" if manifest_summary["failed"] == 0 and qa.get("status") == "PASS" and scheduling_status == "READY" and root_state["exists"] and zip_state["exists"] else "BLOCKED"
    report: dict[str, Any] = {
        "schema": SYSTEM_SCHEMA,
        "plugin": PLUGIN_ID,
        "version": manifest.get("version", "unknown"),
        "mode": "complete_system",
        "started_at": started,
        "finished_at": now(),
        "status": "PASS" if manifest_summary["failed"] == 0 and qa.get("status") == "PASS" else ("REVIEW_REQUIRED" if qa.get("status") == "REVIEW_REQUIRED" else "FAIL"),
        "plugin_root": str(PLUGIN_ROOT),
        "manifest_path": str(MANIFEST_PATH),
        "manifest_checks": manifest_checks,
        "manifest_summary": manifest_summary,
        "manifest_inventory": inventory,
        "inputs": {"root": root_state, "zip": zip_state, "checksum_file": checksum_state, "base_url": args.base_url, "run_extracted_e2e": bool(args.run_extracted_e2e)},
        "qa": qa,
        "qa_summary": qa_summary,
        "scheduling": {"status": scheduling_status, "missing": missing_scheduler, "windows_runtime_available": windows_runtime, **scheduler_files},
        "activation": {"status": activation_status, "registered": False, "automatic_registration": False, "human_review_required": True, "command": "Invoke-VIAAzureFlowQASystem.ps1 -ActivateSchedule (Windows only)"},
        "safety": {"source_write": False, "source_delete": False, "code_execution": bool(args.run_extracted_e2e), "network": False, "localhost_get_only_for_inspect": True, "automatic_command_activation": False, "ssot_promotion": False, "human_review_required": True},
    }
    json_path = out_dir / "VIA_AzureFlow_QA_System_Report.json"
    markdown_path = out_dir / "VIA_AzureFlow_QA_System_Report.md"
    activation_path = out_dir / "activation_result.json"
    report["json_path"] = str(json_path)
    report["markdown_path"] = str(markdown_path)
    report["activation_result_path"] = str(activation_path)
    dump_json(activation_path, {
        "schema": "VIA_AZUREFLOW_QA_SYSTEM_ACTIVATION/1.0",
        "plugin": PLUGIN_ID,
        "requested": False,
        "status": activation_status,
        "registered": False,
        "task_name": None,
        "system_report": str(json_path),
        "qa_exit_code": qa.get("exit_code"),
        "safety": report["safety"],
    })
    dump_json(json_path, report)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "activation": activation_status, "system_json": str(json_path), "system_markdown": str(markdown_path), "qa_status": qa.get("status")}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
