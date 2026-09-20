#!/usr/bin/env python3
"""User-flow smoke test for the single VIA Complete System launcher."""
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
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--executable-path", default="/usr/bin/chromium")
    args = parser.parse_args()
    launcher = args.launcher.resolve()
    results: list[dict[str, Any]] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    screenshots = args.out.parent / "screens"
    screenshots.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=args.executable_path, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(locale="zh-TW", reduced_motion="reduce")
        page = context.new_page()
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(launcher.as_uri(), wait_until="load")
        page.set_default_timeout(8000)

        check(results, "launcher_render", lambda: {
            "title": page.title(),
            "headline": page.get_by_text("中央管理、同步、產業模組與品質驗證", exact=True).is_visible(),
            "ready": page.locator("#statusLocal").inner_text() == "READY",
            "origin": page.locator("#statusOrigin").inner_text(),
        })
        check(results, "launcher_standalone_contract", lambda: _contract(launcher))
        check(results, "central_ui_link_flow", lambda: _open_and_assert(page, "#openUi", "#investmentDesk", "Central UI"))
        check(results, "synchronizer_link_flow", lambda: _open_and_assert(page, "#openSync", "#templateSelect", "SYNCHRONIZER"))
        check(results, "offline_guide_link_flow", lambda: _file_link(page, launcher, "#openOffline", "Offline guide"))
        check(results, "mobile_launcher_geometry", lambda: _mobile_geometry(context, launcher))
        page.screenshot(path=str(screenshots / "complete-system-launcher.png"), full_page=True)
        check(results, "launcher_browser_console_clean", lambda: {"console_errors": console_errors, "page_errors": page_errors})
        context.close()
        browser.close()

    summary = {"total": len(results), "passed": sum(item["passed"] for item in results), "failed": sum(not item["passed"] for item in results)}
    report = {"launcher": str(launcher), "summary": summary, "results": results, "console_errors": console_errors, "page_errors": page_errors}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["failed"] == 0 else 1


def _contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    forbidden = [token for token in ("fetch(", "WebSocket", "EventSource", "<script src=", "<link rel=") if token in text]
    required = ["VIA Complete System", "VIA-UI-Standalone-NoServer.html", "VIA-SYNCHRONIZER-Standalone.html", "run_offline_smoke.sh"]
    if forbidden:
        raise AssertionError(f"launcher has external dependency markers: {forbidden}")
    missing = [token for token in required if token not in text]
    if missing:
        raise AssertionError(f"launcher missing markers: {missing}")
    return {"bytes": path.stat().st_size, "forbidden": forbidden, "missing": missing}


def _open_and_assert(page, selector: str, target_selector_or_text: str, label: str) -> dict[str, Any]:
    with page.expect_popup() as popup_info:
        page.locator(selector).click()
    popup = popup_info.value
    popup.wait_for_load_state("load")
    popup.set_default_timeout(8000)
    url = popup.url
    if target_selector_or_text.startswith("#"):
        popup.locator(target_selector_or_text).wait_for(state="visible")
        visible = popup.locator(target_selector_or_text).is_visible()
    else:
        popup.get_by_text(target_selector_or_text, exact=False).first.wait_for(state="visible")
        visible = popup.get_by_text(target_selector_or_text, exact=False).first.is_visible()
    popup.close()
    if not visible:
        raise AssertionError(f"{label} target was not visible: {url}")
    return {"label": label, "url": url, "target_visible": visible, "protocol": url.split(":", 1)[0] + ":"}


def _file_link(page, launcher: Path, selector: str, label: str) -> dict[str, Any]:
    href = page.locator(selector).get_attribute("href") or ""
    target = (launcher.parent / href).resolve()
    if not href or not target.is_file():
        raise AssertionError(f"{label} target file missing: href={href}, path={target}")
    return {"label": label, "href": href, "path": str(target), "bytes": target.stat().st_size}


def _mobile_geometry(context, launcher: Path) -> dict[str, Any]:
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(launcher.as_uri(), wait_until="load")
    page.locator("#statusLocal").wait_for(state="visible")
    values = page.evaluate("({innerWidth, docWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth})")
    page.screenshot(path=str(launcher.parent.parent / "e2e" / "results-system" / "screens" / "launcher-mobile-390.png"), full_page=True)
    page.close()
    if values["docWidth"] > values["innerWidth"] + 1 or values["bodyWidth"] > values["innerWidth"] + 1:
        raise AssertionError(f"launcher horizontal overflow: {values}")
    return values


if __name__ == "__main__":
    raise SystemExit(main())
