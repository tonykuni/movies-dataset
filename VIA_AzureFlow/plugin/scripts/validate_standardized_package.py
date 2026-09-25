#!/usr/bin/env python3
"""Validate a canonical VIA standardized template directory."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from validate_via_zip import html_contract, inline_scripts, run_node_checks

REQUIRED_FILES = [
    "README.md",
    "STANDARD.md",
    "CHANGELOG.md",
    "manifest.json",
    "ui/VIA-UI-Standalone-NoServer.html",
    "ui/VIA-SYNCHRONIZER-Standalone.html",
    "profiles/industry-profile.json",
    "engines/via_spec_extractor.py",
    "engines/via_triengine_hub.py",
    "ci/run_via_ci.py",
    "ci/validate_via_bundle.py",
    "e2e/run_via_investment_e2e.py",
    "e2e/analyze_report.py",
    "e2e/results-final/report.json",
    "e2e/results-final/report.md",
    "e2e/results-final/junit.xml",
    "skills/via-ucc-triengine-workbench/SKILL.md",
    "skills/via-e2e-zip-verifier/SKILL.md",
]
INDUSTRIES = {"smart-manufacturing", "finance-cyber", "smart-healthcare", "investment-research"}


def add(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    checks.append({"name": name, "passed": ok, "detail": detail})


def sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(root: Path, run_e2e: bool, out_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    missing = [rel for rel in REQUIRED_FILES if not (root / rel).is_file() or (root / rel).stat().st_size == 0]
    add(checks, "required_files", not missing, missing or REQUIRED_FILES)

    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_entrypoints = manifest.get("canonicalEntrypoints", {})
        manifest_ok = (
            manifest.get("schema") == "VIA.STANDARD.TEMPLATE"
            and expected_entrypoints.get("centralUI") == "ui/VIA-UI-Standalone-NoServer.html"
            and expected_entrypoints.get("synchronizer") == "ui/VIA-SYNCHRONIZER-Standalone.html"
            and set(manifest.get("canonicalDirectories", [])) >= {"ui", "profiles", "engines", "ci", "e2e", "skills", "docs", "qa", "assets"}
            and manifest.get("legacyBoundary") == "legacy/reference-templates"
        )
        add(checks, "manifest_contract", manifest_ok, {"schema": manifest.get("schema"), "release": manifest.get("release"), "entrypoints": expected_entrypoints})
        manifest_files = {item["path"]: item for item in manifest.get("files", [])}
        mismatches = []
        for rel, item in manifest_files.items():
            path = root / rel
            if not path.is_file() or path.stat().st_size != item.get("bytes") or sha256(path) != item.get("sha256"):
                mismatches.append(rel)
        add(checks, "manifest_file_hashes", not mismatches and bool(manifest_files), {"files": len(manifest_files), "mismatches": mismatches})
    except Exception as exc:
        add(checks, "manifest_contract", False, str(exc))

    profile = json.loads((root / "profiles/industry-profile.json").read_text(encoding="utf-8"))
    counts = {key: len(value.get("modules", [])) for key, value in sorted(profile.items())}
    profile_ok = INDUSTRIES <= set(profile) and all(counts.get(key, 0) >= 5 for key in INDUSTRIES)
    add(checks, "industry_registry", profile_ok, {"industries": sorted(profile), "module_counts": counts})

    for rel in ("ui/VIA-UI-Standalone-NoServer.html", "ui/VIA-SYNCHRONIZER-Standalone.html"):
        contract = html_contract(root / rel)
        ok = contract["has_body"] and contract["external_resource_tags"] == 0 and contract["local_script_or_link_tags"] == 0 and contract["has_ui_markers"] and contract["has_light_theme_marker"]
        add(checks, f"standalone_contract:{rel}", ok, contract)
        run_node_checks(root, rel, checks)

    report = json.loads((root / "e2e/results-final/report.json").read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    add(checks, "e2e_report", summary.get("total") == 54 and summary.get("passed") == 54 and summary.get("failed") == 0, summary)
    for device, data in report.get("by_device", {}).items():
        add(checks, f"e2e_device:{device}", data.get("failed") == 0 and data.get("browser_errors") == 0, data)

    junit = ET.parse(root / "e2e/results-final/junit.xml").getroot()
    suites = [junit] if junit.tag == "testsuite" else list(junit.findall("testsuite"))
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    add(checks, "junit", tests == 54 and failures == 0 and errors == 0, {"tests": tests, "failures": failures, "errors": errors})

    legacy = root / "legacy/reference-templates"
    add(checks, "legacy_boundary", legacy.is_dir(), str(legacy))

    if run_e2e:
        target = out_dir / "e2e"
        target.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([sys.executable, str(root / "e2e/run_via_investment_e2e.py"), "--html", str(root / "ui/VIA-UI-Standalone-NoServer.html"), "--out-dir", str(target)], capture_output=True, text=True, timeout=180)
        report_path = target / "report.json"
        if result.returncode == 0 and report_path.exists():
            rerun = json.loads(report_path.read_text(encoding="utf-8"))
            rerun_summary = rerun.get("summary", {})
            add(checks, "packaged_e2e", rerun_summary.get("total") == 54 and rerun_summary.get("passed") == 54 and rerun_summary.get("failed") == 0, rerun_summary)
        else:
            add(checks, "packaged_e2e", False, {"returncode": result.returncode, "stderr": result.stderr[-2000:]})

    summary = {"total": len(checks), "passed": sum(1 for item in checks if item["passed"]), "failed": sum(1 for item in checks if not item["passed"])}
    return {"root": str(root), "summary": summary, "passed": summary["failed"] == 0, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--run-e2e", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/via-standardized-verify"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = validate(args.root.resolve(), args.run_e2e, args.out_dir.resolve())
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
