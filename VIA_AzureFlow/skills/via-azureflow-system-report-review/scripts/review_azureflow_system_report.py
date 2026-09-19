#!/usr/bin/env python3
"""Read-only reviewer for VIA AzureFlow complete-system reports."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REVIEW_SCHEMA = "VIA_AZUREFLOW_QA_SYSTEM_REVIEW/1.0"
BLOCKING_SAFETY_KEYS = {
    "source_write",
    "source_delete",
    "automatic_command_activation",
    "ssot_promotion",
    "network",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def resolve_json_path(markdown_path: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    candidate = markdown_path.with_suffix(".json")
    return candidate.resolve()


def load_cases(path: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": str(path) if path else None,
        "total": 0,
        "zero_exit": 0,
        "nonzero_exit": 0,
        "items": [],
        "missing_evidence": [],
    }
    if path is None:
        return result
    if not path.is_file():
        result["missing_evidence"].append(str(path))
        return result
    for line_number, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not raw.strip():
            continue
        fields = raw.split("\t")
        if len(fields) < 3:
            result["items"].append({"line": line_number, "raw": raw, "parse_error": "expected tab-separated case, exit_code, evidence"})
            continue
        case, code_text, evidence = fields[0], fields[1], "\t".join(fields[2:])
        try:
            exit_code = int(code_text)
        except ValueError:
            result["items"].append({"line": line_number, "case": case, "raw_exit_code": code_text, "evidence": evidence, "parse_error": "exit_code is not an integer"})
            continue
        evidence_path = Path(evidence)
        exists = evidence_path.exists()
        item = {
            "line": line_number,
            "case": case,
            "exit_code": exit_code,
            "evidence": evidence,
            "evidence_exists": exists,
        }
        result["items"].append(item)
        result["total"] += 1
        if exit_code == 0:
            result["zero_exit"] += 1
        else:
            result["nonzero_exit"] += 1
        if not exists:
            result["missing_evidence"].append(evidence)
    return result


def markdown_facts(text: str) -> dict[str, Any]:
    """Extract only stable human-facing facts for drift checks."""
    facts: dict[str, Any] = {}
    patterns = {
        "version": r"\*\*版本：\*\*\s*`?([^`\s]+)",
        "status": r"\*\*系統狀態：\*\*\s*`?([^`\s]+)",
        "manifest_checks": r"Manifest checks：`?(\d+/\d+)`?",
        "qa_status": r"QA combined status：`?([^`；\s]+)",
        "qa_exit_code": r"exit code=`?(-?\d+)`?",
        "scheduler_status": r"Task Scheduler readiness：`?([^`；\s]+)",
        "activation_status": r"Activation gate：`?([^`；\s]+)",
        "windows_runtime": r"Current host supports Windows Task Scheduler：`?([^`。\s]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            facts[key] = match.group(1)
    return facts


def compare_markdown_json(markdown_path: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    if not markdown_path.is_file():
        return [{"kind": "markdown_missing", "path": str(markdown_path)}]
    facts = markdown_facts(markdown_path.read_text(encoding="utf-8", errors="replace"))
    expected = {
        "version": str(report.get("version", "")),
        "status": str(report.get("status", "")),
        "manifest_checks": f"{report.get('manifest_summary', {}).get('passed', 0)}/{report.get('manifest_summary', {}).get('total', 0)}",
        "qa_status": str(report.get("qa", {}).get("status", "")),
        "qa_exit_code": str(report.get("qa", {}).get("exit_code", "")),
        "scheduler_status": str(report.get("scheduling", {}).get("status", "")),
        "activation_status": str(report.get("activation", {}).get("status", "")),
        "windows_runtime": str(report.get("scheduling", {}).get("windows_runtime_available", "")),
    }
    comparisons = []
    for key, expected_value in expected.items():
        if key not in facts:
            comparisons.append({"kind": "markdown_fact_missing", "field": key, "expected": expected_value})
        elif facts[key] != expected_value:
            comparisons.append({"kind": "markdown_json_mismatch", "field": key, "markdown": facts[key], "json": expected_value})
    return comparisons


def inspect_plugin_root(report: dict[str, Any], plugin_root: Path | None) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if plugin_root is None:
        return checks
    if not plugin_root.exists():
        return [{"path": str(plugin_root), "status": "MISSING", "reason": "plugin root does not exist"}]
    for item in report.get("manifest_inventory", []):
        relative = item.get("path")
        if not relative:
            continue
        path = plugin_root / relative
        actual = {
            "path": relative,
            "exists": path.is_file(),
            "status": "EXISTS_FILE" if path.is_file() else "MISSING",
        }
        if path.is_file():
            actual["bytes"] = path.stat().st_size
            actual["sha256"] = sha256(path)
            actual["bytes_match"] = actual["bytes"] == item.get("bytes")
            actual["sha256_match"] = actual["sha256"] == item.get("sha256")
        checks.append(actual)
    return checks


def inspect_zip(zip_path: Path | None) -> dict[str, Any] | None:
    if zip_path is None:
        return None
    if not zip_path.is_file():
        return {"path": str(zip_path), "status": "MISSING"}
    return {"path": str(zip_path), "status": "EXISTS_FILE", "bytes": zip_path.stat().st_size, "sha256": sha256(zip_path)}


def validation_facts(path: Path | None) -> dict[str, Any]:
    result = {"path": str(path) if path else None, "exists": bool(path and path.is_file()), "version": None, "zip_sha256": None}
    if not path or not path.is_file():
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    version_match = re.search(r"\*\*Plug-in 版本：\*\*\s*([^\s]+)", text)
    zip_match = re.search(r"\*\*ZIP SHA-256：\*\*\s*`?([0-9a-f]{64})", text, re.IGNORECASE)
    result["version"] = version_match.group(1) if version_match else None
    result["zip_sha256"] = zip_match.group(1).lower() if zip_match else None
    return result


def build_review(args: argparse.Namespace) -> dict[str, Any]:
    markdown_path = Path(args.markdown).expanduser().resolve()
    json_path = resolve_json_path(markdown_path, args.json)
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if not markdown_path.is_file():
        issues.append({"kind": "markdown_missing", "path": str(markdown_path)})
    if not json_path.is_file():
        issues.append({"kind": "json_missing", "path": str(json_path)})
        report: dict[str, Any] = {}
    else:
        try:
            report = load_json(json_path)
        except Exception as exc:  # noqa: BLE001 - report input must become a structured issue
            report = {}
            issues.append({"kind": "json_invalid", "path": str(json_path), "error": str(exc)})

    manifest_summary = report.get("manifest_summary", {})
    qa = report.get("qa", {})
    actions = qa.get("actions", {}) if isinstance(qa, dict) else {}
    scheduling = report.get("scheduling", {})
    activation = report.get("activation", {})
    safety = report.get("safety", {})
    cases = load_cases(Path(args.cases).expanduser().resolve() if args.cases else None)

    if report:
        if report.get("status") not in {"PASS", "REVIEW_REQUIRED"}:
            issues.append({"kind": "report_status", "value": report.get("status")})
        if qa.get("status") != "PASS":
            issues.append({"kind": "qa_status", "value": qa.get("status")})
        if qa.get("exit_code") not in (0, None):
            issues.append({"kind": "qa_exit_code", "value": qa.get("exit_code")})
        if manifest_summary.get("failed", 0) != 0:
            issues.append({"kind": "manifest_failed", "value": manifest_summary})
        for action_name in ("inspect", "verify"):
            action = actions.get(action_name)
            if not isinstance(action, dict):
                issues.append({"kind": "action_missing", "action": action_name})
            elif action.get("status") != "PASS" or action.get("exit_code") not in (0, None):
                issues.append({"kind": "action_failed", "action": action_name, "value": action})
        verify = actions.get("verify", {}) if isinstance(actions, dict) else {}
        validator_summary = verify.get("validator_summary", {}) if isinstance(verify, dict) else {}
        if validator_summary and validator_summary.get("failed", 0) != 0:
            issues.append({"kind": "validator_failed", "value": validator_summary})
        for key in BLOCKING_SAFETY_KEYS:
            if safety.get(key) is True:
                issues.append({"kind": "unsafe_flag", "flag": key, "value": True})
        if safety.get("code_execution") is True:
            warnings.append({"kind": "code_execution_enabled", "reason": "review whether this was explicit opt-in packaged E2E"})

    if cases["nonzero_exit"]:
        warnings.append({"kind": "boundary_cases_present", "count": cases["nonzero_exit"], "reason": "nonzero cases are preserved as negative or boundary evidence"})
    if cases["missing_evidence"]:
        warnings.append({"kind": "case_evidence_missing", "paths": cases["missing_evidence"]})

    if scheduling.get("windows_runtime_available") is False:
        warnings.append({"kind": "windows_runtime_unavailable", "reason": "Task Scheduler registration was not executed in this environment"})
    if activation.get("status") == "READY_FOR_WINDOWS_ACTIVATION":
        warnings.append({"kind": "activation_pending", "reason": "READY_FOR_WINDOWS_ACTIVATION is not ACTIVATED"})
    if activation.get("registered") is False:
        warnings.append({"kind": "not_registered", "reason": "registered=false; human review and explicit Windows activation remain required"})
    if activation.get("human_review_required") is True or report.get("safety", {}).get("human_review_required") is True:
        warnings.append({"kind": "human_review_required", "reason": "safety gate remains enabled"})

    path_checks = inspect_plugin_root(report, Path(args.plugin_root).expanduser().resolve() if args.plugin_root else None)
    if any(item.get("status") == "MISSING" for item in path_checks):
        warnings.append({"kind": "plugin_entrypoint_missing", "paths": [item["path"] for item in path_checks if item.get("status") == "MISSING"]})
    if any(item.get("bytes_match") is False or item.get("sha256_match") is False for item in path_checks):
        warnings.append({"kind": "plugin_entrypoint_hash_drift", "paths": [item["path"] for item in path_checks if item.get("bytes_match") is False or item.get("sha256_match") is False]})

    zip_check = inspect_zip(Path(args.zip).expanduser().resolve() if args.zip else None)
    validation = validation_facts(Path(args.validation_report).expanduser().resolve() if args.validation_report else None)
    comparisons = compare_markdown_json(markdown_path, report) if report else []
    if comparisons:
        warnings.append({"kind": "markdown_json_drift", "count": len(comparisons)})
    if validation.get("exists"):
        if validation.get("version") and str(validation["version"]) != str(report.get("version")):
            warnings.append({"kind": "validation_version_drift", "validation": validation["version"], "report": report.get("version")})
        if zip_check and validation.get("zip_sha256") and zip_check.get("sha256") != validation.get("zip_sha256"):
            warnings.append({"kind": "validation_zip_hash_drift", "validation": validation["zip_sha256"], "current": zip_check.get("sha256")})

    if issues:
        verdict = "FAIL"
    elif warnings:
        verdict = "PASS_WITH_REVIEW"
    else:
        verdict = "PASS"

    return {
        "schema": REVIEW_SCHEMA,
        "source": {"markdown": str(markdown_path), "json": str(json_path)},
        "summary": {
            "report_status": report.get("status"),
            "qa_status": qa.get("status"),
            "qa_exit_code": qa.get("exit_code"),
            "version": report.get("version"),
            "mode": report.get("mode"),
            "manifest": {
                "total": manifest_summary.get("total", 0),
                "passed": manifest_summary.get("passed", 0),
                "failed": manifest_summary.get("failed", 0),
            },
        },
        "metrics": {
            "actions": {name: {"status": value.get("status"), "exit_code": value.get("exit_code")} for name, value in actions.items() if isinstance(value, dict)},
            "validator": actions.get("verify", {}).get("validator_summary", {}) if isinstance(actions.get("verify"), dict) else {},
            "scheduling": {"status": scheduling.get("status"), "windows_runtime_available": scheduling.get("windows_runtime_available")},
            "activation": {"status": activation.get("status"), "registered": activation.get("registered"), "human_review_required": activation.get("human_review_required")},
            "safety": safety,
        },
        "cases": cases,
        "path_checks": path_checks,
        "zip_check": zip_check,
        "validation_report": validation,
        "comparisons": comparisons,
        "warnings": warnings,
        "issues": issues,
        "verdict": verdict,
    }


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["summary"]
    metrics = review["metrics"]
    cases = review["cases"]
    lines = [
        "# VIA 天青智流 AzureFlow QA System Report Review",
        "",
        f"**判定：** `{review['verdict']}`  ",
        f"**來源 Markdown：** `{review['source']['markdown']}`  ",
        f"**來源 JSON：** `{review['source']['json']}`",
        "",
        "## 1. 核心結論",
        "",
        f"報告版本為 `{summary.get('version')}`，原始 system status 為 `{summary.get('report_status')}`。QA combined status 為 `{summary.get('qa_status')}`，exit code 為 `{summary.get('qa_exit_code')}`。Manifest checks 為 `{summary['manifest']['passed']}/{summary['manifest']['total']}`，失敗數為 `{summary['manifest']['failed']}`。",
        "",
        "此 review 只讀取既有報告與證據，不會註冊 Task Scheduler、執行使用者來源程式、修改 SSOT 或改寫來源文件。",
        "",
        "## 2. 指標摘要",
        "",
        "| 指標 | 結果 |",
        "|---|---|",
        f"| `inspect` | `{metrics['actions'].get('inspect', {}).get('status', 'MISSING')}` / exit `{metrics['actions'].get('inspect', {}).get('exit_code', '')}` |",
        f"| `verify` | `{metrics['actions'].get('verify', {}).get('status', 'MISSING')}` / exit `{metrics['actions'].get('verify', {}).get('exit_code', '')}` |",
        f"| Validator | `{metrics['validator'].get('passed', 0)}/{metrics['validator'].get('total', 0)}` passed；failed `{metrics['validator'].get('failed', 0)}` |",
        f"| Scheduler readiness | `{metrics['scheduling'].get('status')}`；Windows runtime `{metrics['scheduling'].get('windows_runtime_available')}` |",
        f"| Activation | `{metrics['activation'].get('status')}`；registered `{metrics['activation'].get('registered')}` |",
        f"| Human review | `{metrics['activation'].get('human_review_required')}` |",
        "",
        "## 3. Full-validation cases",
        "",
        f"Cases total `{cases['total']}`；exit code 0 `{cases['zero_exit']}`；nonzero `{cases['nonzero_exit']}`。Nonzero cases are preserved as negative or boundary evidence and are not automatically treated as defects.",
        "",
        "| Case | Exit code | Evidence exists | Evidence |",
        "|---|---:|---:|---|",
    ]
    for item in cases.get("items", []):
        lines.append(f"| `{md_cell(item.get('case', item.get('raw', '')) )}` | `{md_cell(item.get('exit_code', item.get('raw_exit_code', '')) )}` | `{md_cell(item.get('evidence_exists', ''))}` | `{md_cell(item.get('evidence', ''))}` |")
    lines += [
        "",
        "## 4. Safety and activation",
        "",
        "| Flag | Value | Interpretation |",
        "|---|---:|---|",
    ]
    for key, value in metrics.get("safety", {}).items():
        lines.append(f"| `{md_cell(key)}` | `{md_cell(value)}` | {'review gate' if key in {'human_review_required', 'localhost_get_only_for_inspect'} else 'safety state'} |")
    lines += [
        "",
        "`READY_FOR_WINDOWS_ACTIVATION` is not `ACTIVATED`. When Windows runtime is unavailable or `registered=false`, the review remains `PASS_WITH_REVIEW` even if technical QA is PASS.",
        "",
        "## 5. Warnings and issues",
        "",
    ]
    if review["issues"]:
        lines.append("### Blocking issues")
        lines.append("")
        for item in review["issues"]:
            lines.append(f"- `{md_cell(item.get('kind'))}`: `{md_cell(item)}`")
        lines.append("")
    if review["warnings"]:
        lines.append("### Human-review warnings")
        lines.append("")
        for item in review["warnings"]:
            lines.append(f"- `{md_cell(item.get('kind'))}`: `{md_cell(item)}`")
        lines.append("")
    if not review["issues"] and not review["warnings"]:
        lines.append("No warnings or blocking issues were detected.")
        lines.append("")
    lines += [
        "## 6. Evidence paths",
        "",
        f"- Plugin root checks: `{len(review['path_checks'])}` entries checked.",
        f"- ZIP check: `{review.get('zip_check')}`.",
        f"- Validation report comparison: `{review.get('validation_report')}`.",
        f"- Markdown／JSON comparisons: `{len(review['comparisons'])}` findings.",
        "",
        "## References",
        "",
        f"[1]: file://{review['source']['markdown']} \"VIA AzureFlow QA system report\"",
        f"[2]: file://{review['source']['json']} \"VIA AzureFlow QA system report JSON\"",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review VIA AzureFlow complete-system Markdown/JSON reports without changing source evidence.")
    parser.add_argument("markdown", help="Path to VIA_AzureFlow_QA_System_Report.md")
    parser.add_argument("--json", help="Explicit companion JSON path")
    parser.add_argument("--cases", help="Optional full-validation cases.tsv")
    parser.add_argument("--validation-report", help="Optional full-validation Markdown report")
    parser.add_argument("--plugin-root", help="Optional plugin root for entrypoint hash checks")
    parser.add_argument("--zip", help="Optional current ZIP for size/hash checks")
    parser.add_argument("--out-dir", default=".", help="Output directory for review JSON and Markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    review = build_review(args)
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "VIA_AzureFlow_QA_System_Report_Review.json"
    markdown_path = out_dir / "VIA_AzureFlow_QA_System_Report_Review.md"
    json_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps({"verdict": review["verdict"], "json": str(json_path), "markdown": str(markdown_path), "issues": len(review["issues"]), "warnings": len(review["warnings"])}, ensure_ascii=False, indent=2))
    return 0 if review["verdict"] in {"PASS", "PASS_WITH_REVIEW"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
