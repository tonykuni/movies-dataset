#!/usr/bin/env python3
"""Summarize VIA cross-device E2E compatibility and performance data."""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def pct(value: float) -> str:
    return f"{value:.2f}%"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: analyze_report.py REPORT.json OUT.json", file=sys.stderr)
        return 2
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    results = report["results"]
    by_device: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        by_device[item["device"]].append(item)

    device_summary = {}
    for device, items in by_device.items():
        durations = [float(item["duration_ms"]) for item in items]
        passed = sum(1 for item in items if item.get("passed"))
        errors = sum(len(item.get("details", {}).get("console_errors", [])) + len(item.get("details", {}).get("page_errors", [])) for item in items)
        responsive = next(item for item in items if item["name"] == "responsive_no_horizontal_overflow")
        geometry = next(item for item in items if item["name"] == "responsive_investment_geometry")
        static = next(item for item in items if item["name"] == "static_standalone_contract")
        device_summary[device] = {
            "checks": len(items),
            "passed": passed,
            "failed": len(items) - passed,
            "pass_rate_pct": round(passed / len(items) * 100, 2),
            "duration_total_ms": round(sum(durations), 2),
            "duration_mean_ms": round(statistics.mean(durations), 2),
            "duration_median_ms": round(statistics.median(durations), 2),
            "duration_p95_ms": round(sorted(durations)[max(0, int(len(durations) * 0.95) - 1)], 2),
            "slowest_checks": [
                {"name": item["name"], "duration_ms": item["duration_ms"]}
                for item in sorted(items, key=lambda item: item["duration_ms"], reverse=True)[:5]
            ],
            "browser_error_count": errors,
            "no_horizontal_overflow": responsive["details"]["docWidth"] <= responsive["details"]["innerWidth"] and responsive["details"]["bodyWidth"] <= responsive["details"]["innerWidth"],
            "investment_card_widths": geometry["details"]["widths"],
            "standalone_external_dependency_patterns": static["details"]["external_dependency_patterns"],
            "source_bytes": static["details"]["source_bytes"],
        }

    all_durations = [float(item["duration_ms"]) for item in results]
    checks = {
        "all_passed": all(item.get("passed") for item in results),
        "total_checks": len(results),
        "total_passed": sum(1 for item in results if item.get("passed")),
        "total_failed": sum(1 for item in results if not item.get("passed")),
        "total_duration_ms": round(sum(all_durations), 2),
        "mean_duration_ms": round(statistics.mean(all_durations), 2),
        "median_duration_ms": round(statistics.median(all_durations), 2),
        "slowest_check": max(results, key=lambda item: item["duration_ms"])["name"],
        "slowest_duration_ms": max(all_durations),
    }
    output = {
        "report": {"generated_at": report.get("generated_at"), "html": report.get("html"), "devices": report.get("devices")},
        "checks": checks,
        "devices": device_summary,
        "coverage": {
            "functional": ["initial_render", "chart_modes", "chart_ranges", "chart_tooltip_crosshair", "market_scope_filter", "global_search_filter", "settings_drawer", "connection_modal", "ui_lab_toggle", "navigation_and_flow_controls", "addon_registration", "state_engine_snapshot"],
            "compatibility": ["static_standalone_contract", "responsive_no_horizontal_overflow", "responsive_investment_geometry", "mobile_menu_behavior"],
            "quality": ["accessibility_landmarks", "browser_console_clean"],
        },
    }
    Path(sys.argv[2]).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
