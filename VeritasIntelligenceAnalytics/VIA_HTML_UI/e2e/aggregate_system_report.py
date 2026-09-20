#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    base = out.parent
    sources = {
        "canonical": load(base / "canonical.json"),
        "cross_page": load(base / "cross-page/report.json"),
        "launcher": load(base / "launcher/report.json"),
        "streamlit": load(base / "streamlit/report.json"),
        "zip": load(base / "zip.json"),
    }
    checks: list[dict[str, Any]] = []
    for name, report in sources.items():
        if report is None:
            if name == "streamlit":
                checks.append({"name": name, "status": "SKIP", "passed": True, "detail": "optional runtime not enabled"})
            elif name == "zip":
                checks.append({"name": name, "status": "SKIP", "passed": True, "detail": "ZIP was not supplied"})
            else:
                checks.append({"name": name, "status": "FAIL", "passed": False, "detail": "missing report"})
            continue
        summary = report.get("summary", {})
        ok = summary.get("failed", 1) == 0 and summary.get("passed", 0) == summary.get("total", -1)
        if name == "canonical":
            ok = report.get("passed", False)
        if name == "streamlit":
            ok = summary.get("failed", 1) == 0 and summary.get("passed", 0) == summary.get("total", -1) and not report.get("browser_errors") and not report.get("page_errors")
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "passed": ok, "detail": summary or report.get("passed")})
    summary = {
        "total": len(checks),
        "passed": sum(item["passed"] for item in checks),
        "failed": sum(not item["passed"] for item in checks),
        "skipped": sum(item["status"] == "SKIP" for item in checks),
    }
    result = {"system": "VIA Complete System", "root": str(root), "summary": summary, "checks": checks, "passed": summary["failed"] == 0}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
