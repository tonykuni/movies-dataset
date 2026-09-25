#!/usr/bin/env python3
"""Cross-device end-to-end tests for the standalone VIA investment UI.

The runner targets the local-only file:// build and uses the system Chromium
through Playwright. It produces JSON, Markdown, JUnit XML, screenshots, and
failure artifacts without requiring a server or external chart runtime.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


DEVICES: dict[str, dict[str, int]] = {
    "desktop-1440": {"width": 1440, "height": 1000},
    "tablet-768": {"width": 768, "height": 1024},
    "mobile-390": {"width": 390, "height": 844},
}

DEFAULT_HTML = Path(__file__).resolve().parents[1] / "VIA-UI-Standalone-NoServer.html"


@dataclass
class CheckResult:
    device: str
    name: str
    passed: bool
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class DeviceSuite:
    def __init__(self, page: Page, device: str, out_dir: Path):
        self.page = page
        self.device = device
        self.out_dir = out_dir
        self.results: list[CheckResult] = []
        self.console_errors: list[str] = []
        self.page_errors: list[str] = []
        self.page.on("console", self._on_console)
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))

    def _on_console(self, message: Any) -> None:
        if getattr(message, "type", "") == "error":
            self.console_errors.append(getattr(message, "text", str(message)))

    def check(self, name: str, fn: Callable[[], dict[str, Any] | None]) -> None:
        started = time.perf_counter()
        try:
            details = fn() or {}
            self.results.append(CheckResult(self.device, name, True, round((time.perf_counter() - started) * 1000, 2), details))
        except Exception as exc:  # noqa: BLE001 - keep all checks running for a useful report
            self.results.append(CheckResult(self.device, name, False, round((time.perf_counter() - started) * 1000, 2), {}, f"{type(exc).__name__}: {exc}"))

    def expect(self, condition: Any, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    def visible_count(self, selector: str) -> int:
        return self.page.locator(selector).evaluate_all("els => els.filter(el => getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden').length")

    def geometry(self, selector: str) -> dict[str, float]:
        box = self.page.locator(selector).bounding_box()
        self.expect(box is not None, f"missing geometry for {selector}")
        return {key: round(float(value), 2) for key, value in box.items()}  # type: ignore[union-attr]

    def ensure_sidebar_open(self) -> None:
        viewport = self.page.viewport_size or {"width": 0}
        if viewport["width"] <= 820:
            sidebar = self.page.locator("#sidebar")
            if not sidebar.evaluate("el => el.classList.contains('mobile-open')"):
                self.page.locator("#mobileMenu").click()
            self.expect(sidebar.evaluate("el => el.classList.contains('mobile-open')"), "mobile sidebar did not open")

    def run(self, uri: str) -> None:
        page = self.page
        page.set_default_timeout(8000)
        page.set_default_navigation_timeout(8000)
        page.goto(uri, wait_until="load")
        page.locator("#investmentDesk").wait_for(state="visible")
        page.wait_for_timeout(100)

        self.check("initial_render", lambda: {
            "title": page.title(),
            "investment_desk": page.locator("#investmentDesk").is_visible(),
            "market_chart": page.locator("#marketChart").is_visible(),
            "watchlist_rows": page.locator("#investmentWatchlist tr").count(),
            "engine_version": page.evaluate("window.VIA_ENGINE_HUB?.version"),
        })
        self.check("static_standalone_contract", self.static_contract)
        self.check("responsive_no_horizontal_overflow", self.responsive_overflow)
        self.check("responsive_investment_geometry", self.responsive_investment_geometry)
        self.check("chart_modes", self.chart_modes)
        self.check("chart_ranges", self.chart_ranges)
        self.check("chart_tooltip_crosshair", self.chart_tooltip_crosshair)
        self.check("market_scope_filter", self.market_scope_filter)
        self.check("global_search_filter", self.global_search_filter)
        self.check("settings_drawer", self.settings_drawer)
        self.check("connection_modal", self.connection_modal)
        self.check("ui_lab_toggle", self.ui_lab_toggle)
        self.check("navigation_and_flow_controls", self.navigation_and_flow_controls)
        self.check("addon_registration", self.addon_registration)
        self.check("state_engine_snapshot", self.state_engine_snapshot)
        self.check("mobile_menu_behavior", self.mobile_menu_behavior)
        self.check("accessibility_landmarks", self.accessibility_landmarks)

        # Capture the stable final state after all checks restored their controls.
        screenshot = self.out_dir / "screens" / f"{self.device}.png"
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot), full_page=True)

        self.check("browser_console_clean", lambda: {
            "console_errors": self.console_errors.copy(),
            "page_errors": self.page_errors.copy(),
        })

    def static_contract(self) -> dict[str, Any]:
        html_path = Path(self.page.url.removeprefix("file://"))
        source = html_path.read_text(encoding="utf-8")
        external_patterns = [r'<script[^>]+src=', r'<link[^>]+href=', r'\bfetch\s*\(', r'\bWebSocket\b', r'\bEventSource\b']
        matches = [pattern for pattern in external_patterns if re.search(pattern, source, re.I)]
        self.expect(not matches, f"external/server dependency detected: {matches}")
        self.expect("VIA_ENGINE_HUB" in source, "Engine Hub missing from standalone HTML")
        self.expect("data-chart-mode=\"line\"" in source and "data-chart-mode=\"area\"" in source and "data-chart-mode=\"bars\"" in source, "chart modes missing")
        return {"external_dependency_patterns": matches, "source_bytes": len(source.encode("utf-8"))}

    def responsive_overflow(self) -> dict[str, Any]:
        values = self.page.evaluate("({innerWidth, docWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth, viewport: document.documentElement.dataset.viaViewport})")
        self.expect(values["docWidth"] <= values["innerWidth"] + 1, f"document horizontal overflow: {values}")
        self.expect(values["bodyWidth"] <= values["innerWidth"] + 1, f"body horizontal overflow: {values}")
        return values

    def responsive_investment_geometry(self) -> dict[str, Any]:
        cards = self.page.locator("#investmentDesk .market-card")
        boxes = [cards.nth(i).bounding_box() for i in range(cards.count())]
        self.expect(all(boxes), "one or more investment cards has no layout box")
        tops = [round(box["y"], 1) for box in boxes if box]
        widths = [round(box["width"], 1) for box in boxes if box]
        viewport = self.page.viewport_size or {}
        if viewport.get("width", 0) <= 820:
            self.expect(tops[0] < tops[1] < tops[2], f"mobile cards are not stacked: {tops}")
        else:
            self.expect(max(tops) - min(tops) < 5, f"desktop cards are not aligned: {tops}")
        return {"viewport": viewport, "tops": tops, "widths": widths}

    def chart_modes(self) -> dict[str, Any]:
        chart = self.page.locator("#marketChart")
        results = []
        for mode in ("bars", "area", "line"):
            self.page.locator(f'[data-chart-mode="{mode}"]').click()
            self.page.wait_for_timeout(20)
            has_class = chart.evaluate("(el, mode) => el.classList.contains('mode-' + mode)", mode)
            bar_count = self.page.locator("#marketBars rect").count()
            point_count = self.page.locator("#marketPoints circle").count()
            self.expect(has_class, f"chart mode did not apply: {mode}")
            self.expect(bar_count > 0 and point_count > 0, f"chart decorations missing in {mode}")
            results.append({"mode": mode, "class_applied": has_class, "bar_count": bar_count, "point_count": point_count})
        return {"results": results, "final_mode": chart.get_attribute("class")}

    def chart_ranges(self) -> dict[str, Any]:
        results = []
        expected = {"1D": "+0.38%", "1W": "+4.82%", "1M": "+8.64%", "3M": "+12.38%"}
        for range_name, value in expected.items():
            self.page.locator(f'[data-market-time="{range_name}"]').click()
            self.page.wait_for_timeout(20)
            actual_range = self.page.locator("#marketRangeLabel").inner_text()
            actual_value = self.page.locator("#marketChartValue").inner_text()
            self.expect(actual_range == range_name and actual_value == value, f"range {range_name}: got {actual_range}/{actual_value}")
            results.append({"range": range_name, "value": actual_value})
        self.page.locator('[data-market-time="1W"]').click()
        self.page.locator('[data-chart-mode="line"]').click()
        return {"ranges": results, "restored_range": self.page.locator("#marketRangeLabel").inner_text()}

    def chart_tooltip_crosshair(self) -> dict[str, Any]:
        chart = self.page.locator("#marketChart")
        chart.scroll_into_view_if_needed()
        box = chart.bounding_box()
        self.expect(box is not None, "chart geometry missing")
        self.page.mouse.move(box["x"] + box["width"] * 0.6, box["y"] + box["height"] * 0.4)  # type: ignore[index]
        self.page.wait_for_timeout(30)
        result = self.page.evaluate("({tooltipHidden: document.querySelector('#marketTooltip').hidden, tooltipText: document.querySelector('#marketTooltip').textContent, crosshairHidden: document.querySelector('#marketCrosshair').hidden})")
        self.expect(not result["tooltipHidden"] and not result["crosshairHidden"], f"tooltip/crosshair did not appear: {result}")
        self.expect("1W" in result["tooltipText"], f"tooltip lacks active range: {result}")
        self.page.mouse.move(2, 2)
        return result

    def market_scope_filter(self) -> dict[str, Any]:
        select = self.page.locator("#marketScope")
        select.select_option("tw")
        count = self.visible_count("#investmentWatchlist tr")
        label = self.page.locator("#watchlistCount").inner_text()
        self.expect(count == 2 and label == "2 symbols", f"TW filter mismatch: {count}/{label}")
        select.select_option("all")
        restored = self.visible_count("#investmentWatchlist tr")
        self.expect(restored == 6, f"watchlist restore mismatch: {restored}")
        return {"tw_visible": count, "tw_label": label, "restored": restored}

    def global_search_filter(self) -> dict[str, Any]:
        search = self.page.locator("#globalSearch")
        if (self.page.viewport_size or {"width": 0})["width"] <= 820:
            self.page.locator(".search").click()
            self.expect(self.page.locator(".search").evaluate("el => el.classList.contains('expanded')"), "mobile search did not expand")
        search.fill("VDF")
        endpoint_count = self.visible_count("#endpointTable tr")
        investment_count = self.visible_count("#investmentWatchlist tr")
        self.expect(endpoint_count == 1, f"VDF endpoint search mismatch: {endpoint_count}")
        search.fill("")
        self.expect(self.visible_count("#endpointTable tr") == 4 and self.visible_count("#investmentWatchlist tr") == 6, "search clear did not restore tables")
        return {"query": "VDF", "endpoint_visible": endpoint_count, "investment_visible": investment_count}

    def settings_drawer(self) -> dict[str, Any]:
        self.ensure_sidebar_open()
        self.page.locator("[data-open-settings]").first.click()
        backdrop = self.page.locator("#settingsBackdrop")
        self.expect("open" in (backdrop.get_attribute("class") or ""), "settings drawer did not open")
        self.page.locator('[data-density="compact"]').click()
        density_active = self.page.locator('[data-density="compact"]').evaluate("el => el.classList.contains('active')")
        self.expect(density_active, "compact density did not activate")
        self.page.locator("#settingsBackdrop [data-close-settings]").first.click(force=True)
        self.expect("open" not in (backdrop.get_attribute("class") or ""), "settings drawer did not close")
        if (self.page.viewport_size or {"width": 0})["width"] <= 820:
            sidebar = self.page.locator("#sidebar")
            if sidebar.evaluate("el => el.classList.contains('mobile-open')"):
                self.page.locator("#mobileMenu").click()
        return {"compact_active": density_active, "closed": True}

    def connection_modal(self) -> dict[str, Any]:
        self.page.locator("#newConnectionBtn").click()
        modal = self.page.locator("#connectionBackdrop")
        self.expect("open" in (modal.get_attribute("class") or ""), "connection modal did not open")
        self.page.locator("#connectionName").fill("E2E Investment Stream")
        self.page.locator("#createConnectionBtn").click()
        self.expect("open" not in (modal.get_attribute("class") or ""), "connection modal did not close after create")
        toast = self.page.locator("#toastText").inner_text()
        self.expect("E2E Investment Stream" in toast, f"connection toast mismatch: {toast}")
        return {"created_name": "E2E Investment Stream", "toast": toast}

    def ui_lab_toggle(self) -> dict[str, Any]:
        lab = self.page.locator("#uiLab")
        self.expect(lab.is_hidden(), "UI Lab should start hidden")
        self.page.locator("#uiLabBtn").click()
        self.expect(lab.is_visible(), "UI Lab did not open")
        self.page.locator("#uiLabBtn").click()
        self.expect(lab.is_hidden(), "UI Lab did not close")
        return {"opened_and_closed": True}

    def navigation_and_flow_controls(self) -> dict[str, Any]:
        self.ensure_sidebar_open()
        nav = self.page.locator('.nav-item[data-nav="銜接拓撲"]')
        nav.click()
        self.expect(nav.evaluate("el => el.classList.contains('active')"), "navigation active state missing")
        pause = self.page.locator("#pauseFlowBtn")
        pause.click()
        paused = pause.get_attribute("data-paused")
        pause.click()
        restored = pause.get_attribute("data-paused")
        self.expect(paused == "true" and restored == "false", f"flow pause state mismatch: {paused}/{restored}")
        return {"nav_active": True, "paused_state": paused, "restored_state": restored}

    def addon_registration(self) -> dict[str, Any]:
        result = self.page.evaluate("""() => {
          const mounted = window.VIA_REGISTER_ADDON({
            id: 'e2e-investment-addon', name: 'E2E Investment Add-on', version: '1.0.0',
            mount: (host, api) => { host.dataset.apiVersion = api.version; host.textContent = 'E2E mounted'; }
          });
          return {mounted, list: window.VIA_ADDON_API.list(), text: document.querySelector('#addonSlotBody').textContent, apiVersion: document.querySelector('#addonSlotBody [data-addon-id]')?.dataset.apiVersion || null};
        }""")
        self.expect(result["mounted"] is True, f"add-on did not mount: {result}")
        self.expect(any(item["id"] == "e2e-investment-addon" for item in result["list"]), f"add-on missing from registry: {result}")
        self.expect("E2E mounted" in result["text"], f"add-on host not mounted: {result}")
        self.page.evaluate("""() => { window.VIA_ADDONS = []; const slot = document.querySelector('#addonSlotBody'); slot.classList.remove('is-mounted'); slot.replaceChildren(Object.assign(document.createElement('span'), {textContent: '此區保留給未來產業卡片、研究插件、資料匯入器或自訂圖表；未註冊時保持最小視覺佔用。'})); }""")
        return result

    def state_engine_snapshot(self) -> dict[str, Any]:
        result = self.page.evaluate("""() => ({
          version: window.VIA_ENGINE_HUB?.state?.version,
          storageKey: window.VIA_ENGINE_HUB?.state?.storageKey,
          channel: window.VIA_ENGINE_HUB?.state?.channel,
          snapshotVersion: window.VIA_ENGINE_HUB?.state?.snapshot()?.version,
          mode: window.VIA_ENGINE_HUB?.visualization?.getState()?.mode,
          range: window.VIA_ENGINE_HUB?.visualization?.getState()?.range
        })""")
        self.expect(result["version"] == "2" and result["snapshotVersion"] == 2, f"state schema mismatch: {result}")
        self.expect(result["mode"] == "line" and result["range"] == "1W", f"visualization state not restored: {result}")
        return result

    def mobile_menu_behavior(self) -> dict[str, Any]:
        viewport = self.page.viewport_size or {"width": 0}
        if viewport["width"] > 820:
            return {"skipped": True, "reason": "desktop viewport"}
        menu = self.page.locator("#mobileMenu")
        self.expect(menu.is_visible(), "mobile menu is not visible on narrow viewport")
        menu.click()
        opened = self.page.locator("#sidebar").evaluate("el => el.classList.contains('mobile-open')")
        menu.click()
        closed = self.page.locator("#sidebar").evaluate("el => !el.classList.contains('mobile-open')")
        self.expect(opened and closed, f"mobile menu state mismatch: {opened}/{closed}")
        return {"opened": opened, "closed": closed}

    def accessibility_landmarks(self) -> dict[str, Any]:
        result = self.page.evaluate("""() => ({
          main: document.querySelectorAll('main').length,
          nav: document.querySelectorAll('nav').length,
          investmentLabel: document.querySelector('#investmentDesk')?.getAttribute('aria-label'),
          chartRole: document.querySelector('#marketChart')?.getAttribute('role'),
          chartLabel: document.querySelector('#marketChart')?.getAttribute('aria-label'),
          modalRole: document.querySelector('#connectionBackdrop')?.getAttribute('role')
        })""")
        self.expect(result["main"] == 1 and result["nav"] >= 1, f"landmark count mismatch: {result}")
        self.expect(result["investmentLabel"] == "投資研究工作台" and result["chartRole"] == "img" and result["modalRole"] == "dialog", f"accessible labels missing: {result}")
        return result


def flatten_results(results: list[CheckResult]) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]


def write_junit(path: Path, results: list[CheckResult]) -> None:
    suite = ET.Element("testsuites")
    by_device: dict[str, list[CheckResult]] = {}
    for result in results:
        by_device.setdefault(result.device, []).append(result)
    for device, device_results in by_device.items():
        testsuite = ET.SubElement(suite, "testsuite", name=f"VIA investment UI · {device}", tests=str(len(device_results)), failures=str(sum(not r.passed for r in device_results)), time=f"{sum(r.duration_ms for r in device_results) / 1000:.3f}")
        for result in device_results:
            case = ET.SubElement(testsuite, "testcase", name=result.name, time=f"{result.duration_ms / 1000:.3f}")
            if not result.passed:
                failure = ET.SubElement(case, "failure", message=result.error or "failed")
                failure.text = result.error or "failed"
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# VIA Investment UI Cross-Device E2E Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- HTML: `{report['html']}`",
        f"- Overall: **{'PASS' if report['summary']['failed'] == 0 else 'FAIL'}**",
        f"- Devices: `{', '.join(report['devices'])}`",
        "",
        "## Summary",
        "",
        "| Device | Checks | Passed | Failed | Console/page errors | Screenshot |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for device in report["devices"]:
        summary = report["by_device"][device]
        lines.append(f"| {device} | {summary['total']} | {summary['passed']} | {summary['failed']} | {summary['browser_errors']} | `{summary['screenshot']}` |")
    lines.extend(["", "## Covered journeys", "", "The suite covers initial render, standalone/no-server dependency checks, responsive overflow and investment-card geometry, chart modes, 1D/1W/1M/3M ranges, tooltip/crosshair, market scope filtering, global search, settings drawer, connection modal, UI Lab, navigation, flow pause/resume, add-on registration, state engine snapshot, mobile menu behavior, accessibility landmarks, and browser console/page errors.", "", "## Result details", ""])
    for result in report["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        suffix = f" — {result['error']}" if result["error"] else ""
        lines.append(f"- **{status}** `{result['device']}` · `{result['name']}` ({result['duration_ms']} ms){suffix}")
    lines.extend(["", "## Execution", "", "Run locally with:", "", "```bash", f"python3 {Path(__file__).name} --html /path/to/VIA-UI-Standalone-NoServer.html --out-dir e2e-results", "```", "", "The runner uses the installed Chromium executable through Playwright and does not start an HTTP server.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML, help="Standalone VIA UI HTML path")
    parser.add_argument("--out-dir", type=Path, default=Path("via-e2e-results"), help="Output directory for reports and screenshots")
    parser.add_argument("--devices", default=",".join(DEVICES), help="Comma-separated device names")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser")
    parser.add_argument("--executable-path", default="/usr/bin/chromium", help="Chromium executable path")
    args = parser.parse_args()

    html_path = args.html.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = [name.strip() for name in args.devices.split(",") if name.strip()]
    unknown = sorted(set(selected) - set(DEVICES))
    if unknown:
        parser.error(f"unknown device(s): {', '.join(unknown)}")
    if not html_path.is_file():
        parser.error(f"HTML file not found: {html_path}")

    uri = html_path.as_uri()
    all_results: list[CheckResult] = []
    device_errors: dict[str, list[str]] = {}
    screenshots: dict[str, str] = {}
    started_at = datetime.now(timezone.utc)

    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(headless=not args.headed, executable_path=args.executable_path, args=["--no-sandbox", "--disable-gpu"])
        try:
            for device in selected:
                spec = DEVICES[device]
                context: BrowserContext = browser.new_context(viewport={"width": spec["width"], "height": spec["height"]}, locale="zh-TW", reduced_motion="reduce")
                page = context.new_page()
                suite = DeviceSuite(page, device, out_dir)
                try:
                    suite.run(uri)
                except (PlaywrightTimeoutError, Exception):  # keep artifacts if a catastrophic page failure occurs
                    if not suite.results or not suite.results[-1].passed:
                        error = traceback.format_exc()
                        suite.results.append(CheckResult(device, "suite_fatal_error", False, 0, {}, error))
                    device_errors[device] = [traceback.format_exc()]
                finally:
                    screenshots[device] = str(out_dir / "screens" / f"{device}.png")
                    all_results.extend(suite.results)
                    context.close()
        finally:
            browser.close()

    by_device: dict[str, dict[str, Any]] = {}
    for device in selected:
        device_results = [result for result in all_results if result.device == device]
        by_device[device] = {
            "total": len(device_results),
            "passed": sum(result.passed for result in device_results),
            "failed": sum(not result.passed for result in device_results),
            "browser_errors": sum(1 for result in device_results if result.name == "browser_console_clean" and (result.details.get("console_errors") or result.details.get("page_errors"))),
            "screenshot": str(Path(screenshots.get(device, "")).relative_to(out_dir)) if screenshots.get(device) else "",
        }
    report = {
        "generated_at": started_at.isoformat(),
        "html": str(html_path),
        "devices": selected,
        "summary": {"total": len(all_results), "passed": sum(result.passed for result in all_results), "failed": sum(not result.passed for result in all_results)},
        "by_device": by_device,
        "results": flatten_results(all_results),
        "device_errors": device_errors,
    }
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(out_dir / "report.md", report)
    write_junit(out_dir / "junit.xml", all_results)
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
