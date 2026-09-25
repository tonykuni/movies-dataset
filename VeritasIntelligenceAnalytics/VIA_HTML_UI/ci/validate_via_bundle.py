#!/usr/bin/env python3
"""Validate a VIA v2 state or industry template JSON bundle."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_MODULE_TYPES = {"dashboard", "data", "automation", "governance", "integration"}
ALLOWED_CHART_TYPES = {"line", "bar", "area", "kpi"}
ALLOWED_AGG = {"sum", "average", "min", "max"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_via_bundle.py <json-file>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        fail(f"file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"invalid JSON: {exc}")
    if not isinstance(data, dict):
        fail("root must be an object")

    modules = data.get("modules", [])
    analytics = data.get("analytics", data)
    charts = analytics.get("charts", []) if isinstance(analytics, dict) else []
    history = analytics.get("history", []) if isinstance(analytics, dict) else []
    if not isinstance(modules, list) or not isinstance(charts, list) or not isinstance(history, list):
        fail("modules, charts, and history must be arrays")

    module_ids = set()
    for index, module in enumerate(modules):
        if not isinstance(module, dict):
            fail(f"module[{index}] must be an object")
        for key in ("id", "name", "type"):
            if not str(module.get(key, "")).strip():
                fail(f"module[{index}] missing {key}")
        if module["id"] in module_ids:
            fail(f"duplicate module id: {module['id']}")
        module_ids.add(module["id"])
        if module["type"] not in ALLOWED_MODULE_TYPES:
            fail(f"unsupported module type: {module['type']}")

    chart_ids = set()
    for index, chart in enumerate(charts):
        if not isinstance(chart, dict):
            fail(f"chart[{index}] must be an object")
        for key in ("id", "name", "metric"):
            if not str(chart.get(key, "")).strip():
                fail(f"chart[{index}] missing {key}")
        if chart["id"] in chart_ids:
            fail(f"duplicate chart id: {chart['id']}")
        chart_ids.add(chart["id"])
        if chart.get("type", "line") not in ALLOWED_CHART_TYPES:
            fail(f"unsupported chart type: {chart.get('type')}")

    for index, row in enumerate(history):
        if not isinstance(row, dict):
            fail(f"history[{index}] must be an object")
        for key in ("date", "metric"):
            if not str(row.get(key, "")).strip():
                fail(f"history[{index}] missing {key}")
        try:
            float(row.get("value", 0))
        except (TypeError, ValueError):
            fail(f"history[{index}] value must be numeric")

    pivot = analytics.get("pivot", {}) if isinstance(analytics, dict) else {}
    if pivot and pivot.get("aggregation", "sum") not in ALLOWED_AGG:
        fail(f"unsupported pivot aggregation: {pivot.get('aggregation')}")

    print(f"OK: modules={len(modules)} charts={len(charts)} history={len(history)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
