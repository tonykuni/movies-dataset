#!/usr/bin/env python3
"""Validate a VIA all-in-one ZIP package without trusting the source workspace."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


REQUIRED_RELATIVE = [
    "ui/VIA-UI-Standalone-NoServer.html",
    "ui/VIA-SYNCHRONIZER-Standalone.html",
    "e2e/run_via_investment_e2e.py",
    "e2e/results-final/report.json",
    "e2e/results-final/report.md",
    "e2e/results-final/junit.xml",
    "skill/via-ucc-triengine-workbench/SKILL.md",
    "complete-package/README.md",
]
REQUIRED_INDUSTRIES = {"smart-manufacturing", "finance-cyber", "smart-healthcare", "investment-research"}
HTML_NAMES = ("ui/VIA-UI-Standalone-NoServer.html", "ui/VIA-SYNCHRONIZER-Standalone.html")


def fail(checks: list[dict[str, Any]], name: str, detail: Any) -> None:
    checks.append({"name": name, "passed": False, "detail": detail})


def passed(checks: list[dict[str, Any]], name: str, detail: Any) -> None:
    checks.append({"name": name, "passed": True, "detail": detail})


def safe_members(zf: zipfile.ZipFile) -> tuple[bool, list[str]]:
    bad = []
    names = []
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        names.append(name)
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            bad.append(name)
    return not bad, bad


def find_root(extracted: Path) -> Path:
    candidates = sorted(extracted.glob("*/ui/VIA-UI-Standalone-NoServer.html"))
    if not candidates:
        raise FileNotFoundError("cannot locate package root containing ui/VIA-UI-Standalone-NoServer.html")
    return candidates[0].parent.parent


def inline_scripts(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [body for attrs, body in re.findall(r"<script([^>]*)>(.*?)</script>", text, flags=re.I | re.S) if not re.search(r"\bsrc\s*=", attrs, flags=re.I)]


def html_contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    external_tags = re.findall(r"<(?:script|link|img|iframe|audio|video)[^>]+(?:src|href)\s*=\s*[\"'](?:https?:|//|//)[^\"']+[\"']", text, flags=re.I)
    local_src_tags = re.findall(r"<(?:script|link)[^>]+(?:src|href)\s*=", text, flags=re.I)
    is_synchronizer = path.name == "VIA-SYNCHRONIZER-Standalone.html"
    markers = ("VIA_SYNCHRONIZER_ADDON_API", "via.sync.state.v2", "BroadcastChannel", "exportExcel") if is_synchronizer else ("investment", "market-chart", "watchlist")
    return {
        "bytes": path.stat().st_size,
        "inline_scripts": len(inline_scripts(path)),
        "external_resource_tags": len(external_tags),
        "local_script_or_link_tags": len(local_src_tags),
        "has_body": bool(re.search(r"<body\b", text, flags=re.I)),
        "has_ui_markers": all(marker in text for marker in markers),
        "required_markers": list(markers),
        "has_light_theme_marker": "via-reference-light-compact" in text or "via-reference-light-compact-sync" in text,
    }


def run_node_checks(root: Path, html_rel: str, checks: list[dict[str, Any]]) -> None:
    node = shutil.which("node")
    if not node:
        fail(checks, f"node_syntax:{html_rel}", "node executable not found")
        return
    html = root / html_rel
    for index, script in enumerate(inline_scripts(html)):
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
            handle.write(script)
            temp = Path(handle.name)
        result = subprocess.run([node, "--check", str(temp)], capture_output=True, text=True)
        temp.unlink(missing_ok=True)
        if result.returncode:
            fail(checks, f"node_syntax:{html_rel}#{index}", result.stderr.strip())
        else:
            passed(checks, f"node_syntax:{html_rel}#{index}", "PASS")


def load_industry_profiles(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    candidates = [
        root / "skill/via-ucc-triengine-workbench/templates/industry-profile.json",
        root / "complete-package/skill/templates/industry-profile.json",
    ]
    profiles = []
    for candidate in candidates:
        if candidate.exists():
            profiles.append((candidate, json.loads(candidate.read_text(encoding="utf-8"))))
    return profiles


def run_e2e(root: Path, out_dir: Path, checks: list[dict[str, Any]]) -> None:
    runner = root / "e2e/run_via_investment_e2e.py"
    html = root / "ui/VIA-UI-Standalone-NoServer.html"
    if not runner.exists() or not html.exists():
        fail(checks, "extracted_e2e", "runner or UI is missing")
        return
    command = [sys.executable, str(runner), "--html", str(html), "--out-dir", str(out_dir)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        fail(checks, "extracted_e2e", "timed out after 180 seconds")
        return
    if result.returncode:
        fail(checks, "extracted_e2e", {"returncode": result.returncode, "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]})
        return
    report_path = out_dir / "report.json"
    if not report_path.exists():
        fail(checks, "extracted_e2e", "runner completed without report.json")
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    detail = {"total": summary.get("total"), "passed": summary.get("passed"), "failed": summary.get("failed"), "devices": report.get("devices")}
    if summary.get("failed") == 0 and summary.get("passed") == summary.get("total") and summary.get("total", 0) > 0:
        passed(checks, "extracted_e2e", detail)
    else:
        fail(checks, "extracted_e2e", detail)


def failed_result(zip_path: Path, actual_sha: str, checks: list[dict[str, Any]], root: Path | None = None) -> dict[str, Any]:
    return {
        "zip": str(zip_path),
        "sha256": actual_sha,
        "root": str(root) if root else None,
        "checks": checks,
        "summary": {"total": len(checks), "passed": sum(1 for item in checks if item["passed"]), "failed": sum(1 for item in checks if not item["passed"])},
        "passed": False,
    }


def validate(zip_path: Path, out_dir: Path, run_extracted_e2e: bool, checksum_file: Path | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    if checksum_file and checksum_file.exists():
        expected = checksum_file.read_text(encoding="utf-8").split()[0]
        (passed if expected == actual_sha else fail)(checks, "sha256", {"expected": expected, "actual": actual_sha})
    else:
        passed(checks, "sha256", {"actual": actual_sha, "expected": None})

    extract_dir = out_dir / "extracted"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        good, bad = safe_members(zf)
        if not good:
            fail(checks, "zip_path_safety", bad)
            return failed_result(zip_path, actual_sha, checks)
        passed(checks, "zip_path_safety", {"members": len(zf.infolist())})
        corrupt = zf.testzip()
        if corrupt:
            fail(checks, "zip_integrity", corrupt)
            return failed_result(zip_path, actual_sha, checks)
        passed(checks, "zip_integrity", {"members": len(zf.infolist())})
        zf.extractall(extract_dir)

    try:
        root = find_root(extract_dir)
    except FileNotFoundError as exc:
        fail(checks, "package_root", str(exc))
        return failed_result(zip_path, actual_sha, checks)
    passed(checks, "package_root", str(root))

    missing = [rel for rel in REQUIRED_RELATIVE if not (root / rel).is_file() or (root / rel).stat().st_size == 0]
    if missing:
        fail(checks, "required_files", missing)
        return failed_result(zip_path, actual_sha, checks, root)
    passed(checks, "required_files", REQUIRED_RELATIVE)

    for html_rel in HTML_NAMES:
        path = root / html_rel
        if not path.exists():
            continue
        contract = html_contract(path)
        if contract["external_resource_tags"] == 0 and contract["local_script_or_link_tags"] == 0 and contract["has_body"] and contract["has_ui_markers"]:
            passed(checks, f"standalone_contract:{html_rel}", contract)
        else:
            fail(checks, f"standalone_contract:{html_rel}", contract)
        if contract["has_light_theme_marker"]:
            passed(checks, f"light_theme:{html_rel}", "reference-light theme marker present")
        else:
            fail(checks, f"light_theme:{html_rel}", "reference-light theme marker missing")
        run_node_checks(root, html_rel, checks)

    report_path = root / "e2e/results-final/report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    if summary.get("failed") == 0 and summary.get("passed") == summary.get("total") and summary.get("total", 0) > 0:
        passed(checks, "bundled_e2e_report", summary)
    else:
        fail(checks, "bundled_e2e_report", summary)
    for device, data in report.get("by_device", {}).items():
        if data.get("failed") == 0 and data.get("browser_errors") == 0:
            passed(checks, f"bundled_e2e_device:{device}", data)
        else:
            fail(checks, f"bundled_e2e_device:{device}", data)

    import xml.etree.ElementTree as ET
    junit = ET.parse(root / "e2e/results-final/junit.xml").getroot()
    suites = [junit] if junit.tag == "testsuite" else list(junit.findall("testsuite"))
    junit_failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    junit_errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    junit_tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    if junit_failures == 0 and junit_errors == 0 and junit_tests > 0:
        passed(checks, "bundled_junit", {"tests": junit_tests, "failures": junit_failures, "errors": junit_errors})
    else:
        fail(checks, "bundled_junit", {"tests": junit_tests, "failures": junit_failures, "errors": junit_errors})

    profiles = load_industry_profiles(root)
    if not profiles:
        fail(checks, "industry_profile", "industry-profile.json missing")
    else:
        profile_sets = [set(profile) for _, profile in profiles]
        profile_consistent = all(profile == profiles[0][1] for _, profile in profiles[1:])
        profile = profiles[0][1]
        industries = set(profile)
        missing_industries = sorted(REQUIRED_INDUSTRIES - industries)
        module_counts = {name: len(profile[name].get("modules", [])) for name in sorted(REQUIRED_INDUSTRIES & industries)}
        detail = {"paths": [str(path) for path, _ in profiles], "industries": sorted(industries), "module_counts": module_counts, "copies_consistent": profile_consistent}
        if not missing_industries and profile_consistent and all(count > 0 for count in module_counts.values()):
            passed(checks, "industry_profile", detail)
        else:
            fail(checks, "industry_profile", {**detail, "missing": missing_industries})

    top_ui = root / "ui/VIA-UI-Standalone-NoServer.html"
    package_ui = root / "complete-package/ui/VIA-UI-Standalone-NoServer.html"
    if package_ui.exists() and top_ui.read_bytes() == package_ui.read_bytes():
        passed(checks, "complete_package_ui_sync", "top-level ui equals complete-package/ui")
    else:
        fail(checks, "complete_package_ui_sync", "central UI copies differ or package copy missing")

    screenshots = [root / "e2e/results-final/screens" / f"{device}.png" for device in ("desktop-1440", "tablet-768", "mobile-390")]
    missing_screens = [str(path.relative_to(root)) for path in screenshots if not path.is_file() or path.stat().st_size == 0]
    if not missing_screens:
        passed(checks, "e2e_screenshots", [str(path.relative_to(root)) for path in screenshots])
    else:
        fail(checks, "e2e_screenshots", missing_screens)

    if run_extracted_e2e:
        run_e2e(root, out_dir / "extracted-e2e", checks)

    return {
        "zip": str(zip_path),
        "sha256": actual_sha,
        "root": str(root),
        "checks": checks,
        "summary": {"total": len(checks), "passed": sum(1 for item in checks if item["passed"]), "failed": sum(1 for item in checks if not item["passed"])},
        "passed": all(item["passed"] for item in checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("via-zip-verification"))
    parser.add_argument("--checksum-file", type=Path)
    parser.add_argument("--run-extracted-e2e", action="store_true")
    parser.add_argument("--json", type=Path, help="write verification JSON to this path")
    args = parser.parse_args()
    result = validate(args.zip.resolve(), args.out_dir.resolve(), args.run_extracted_e2e, args.checksum_file.resolve() if args.checksum_file else None)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
