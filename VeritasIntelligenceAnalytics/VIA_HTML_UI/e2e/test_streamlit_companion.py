#!/usr/bin/env python3
"""Headless smoke test for the optional local Streamlit companion."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


def check(results: list[dict[str, Any]], name: str, fn) -> None:
    started = time.perf_counter()
    try:
        detail = fn() or {}
        results.append({"name": name, "passed": True, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "detail": detail})
    except Exception as exc:  # noqa: BLE001
        results.append({"name": name, "passed": False, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "detail": {}, "error": f"{type(exc).__name__}: {exc}"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--executable-path", default="/usr/bin/chromium")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    args.out.parent.mkdir(parents=True, exist_ok=True)
    screenshots = args.out.parent / "screens"
    screenshots.mkdir(parents=True, exist_ok=True)
    csv_path = args.csv or Path("/tmp/via-companion-smoke.csv")
    if not csv_path.exists():
        csv_path.write_text("date,oee,latency_ms,category\n2026-09-18,0.91,42,alpha\n2026-09-19,0.94,37,beta\n2026-09-20,0.93,39,gamma\n", encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=args.executable_path, args=["--no-sandbox", "--disable-gpu"])
        desktop = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        desktop.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        desktop.on("pageerror", lambda error: page_errors.append(str(error)))
        desktop.goto(args.url, wait_until="domcontentloaded")
        desktop.get_by_text("VIA Local Workflow Companion", exact=True).wait_for(state="visible", timeout=20000)
        desktop.wait_for_timeout(1200)

        check(results, "desktop_render_and_tabs", lambda: {
            "title_visible": desktop.get_by_text("VIA Local Workflow Companion", exact=True).is_visible(),
            "tabs": desktop.get_by_role("tab").all_text_contents(),
            "tab_count": desktop.get_by_role("tab").count(),
        })
        check(results, "graphviz_static_png", lambda: _graphviz(desktop, screenshots))
        check(results, "csv_upload_and_export", lambda: _csv(desktop, csv_path, screenshots))
        desktop.close()

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        mobile.on("pageerror", lambda error: page_errors.append(str(error)))
        mobile.goto(args.url, wait_until="domcontentloaded")
        mobile.get_by_text("VIA Local Workflow Companion", exact=True).wait_for(state="visible", timeout=20000)
        mobile.wait_for_timeout(700)
        check(results, "mobile_responsive_layout", lambda: _mobile(mobile, screenshots))
        mobile.close()
        browser.close()

    check(results, "browser_console_clean", lambda: {"console_errors": console_errors, "page_errors": page_errors})
    summary = {"total": len(results), "passed": sum(item["passed"] for item in results), "failed": sum(not item["passed"] for item in results)}
    report = {"url": args.url, "summary": summary, "results": results, "browser_errors": console_errors, "page_errors": page_errors}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["failed"] == 0 else 1


def _select_backend(page, label: str) -> None:
    combo = page.locator('input[aria-label="工作流後端"]')
    combo.click()
    page.get_by_role("option", name=label, exact=True).wait_for(state="visible", timeout=5000)
    page.get_by_role("option", name=label, exact=True).click()
    page.wait_for_timeout(900)
    if combo.input_value() != label:
        raise AssertionError(f"backend did not switch to {label}")


def _graphviz(page, screenshots: Path) -> dict[str, Any]:
    _select_backend(page, "Graphviz")
    page.get_by_role("tab", name="工作流圖表", exact=True).click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(screenshots / "streamlit-graphviz.png"), full_page=True)
    heading = page.get_by_text("Graphviz 工作流", exact=True).is_visible()
    image_count = page.locator("img").count()
    fallback = page.get_by_text("digraph VIA", exact=False).count() > 0
    if not heading or not (image_count > 0 or fallback):
        raise AssertionError(f"Graphviz render missing: heading={heading}, images={image_count}, fallback={fallback}")
    return {"heading_visible": heading, "static_image_count": image_count, "dot_fallback": fallback}


def _csv(page, csv_path: Path, screenshots: Path) -> dict[str, Any]:
    page.locator('input[type="file"]').first.set_input_files(str(csv_path))
    page.wait_for_timeout(1400)
    page.get_by_role("tab", name="CSV 分析", exact=True).click()
    page.wait_for_timeout(500)
    row_summary = page.get_by_text("資料列：3，欄位：4", exact=True).count() > 0
    download = page.get_by_text("下載目前 CSV", exact=True).count() > 0
    loaded = page.get_by_text("已載入", exact=True).count() > 0
    page.screenshot(path=str(screenshots / "streamlit-csv.png"), full_page=True)
    if not (row_summary and download and loaded):
        raise AssertionError(f"CSV flow incomplete: {row_summary}/{download}/{loaded}")
    return {"loaded": loaded, "row_summary": row_summary, "download_button": download}


def _mobile(page, screenshots: Path) -> dict[str, Any]:
    values = page.evaluate("({innerWidth, docWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth})")
    tabs = page.get_by_role("tab").count()
    page.screenshot(path=str(screenshots / "streamlit-mobile.png"), full_page=True)
    if values["docWidth"] > values["innerWidth"] + 1 or values["bodyWidth"] > values["innerWidth"] + 1:
        raise AssertionError(f"horizontal overflow: {values}")
    if tabs < 3:
        raise AssertionError(f"mobile tabs missing: {tabs}")
    return {**values, "tabs": tabs}


if __name__ == "__main__":
    raise SystemExit(main())
