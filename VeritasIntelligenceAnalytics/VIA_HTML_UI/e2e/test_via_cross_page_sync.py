#!/usr/bin/env python3
"""Headless cross-page synchronization test for the standalone VIA UI pair."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

KEY = "via.sync.state.v2"
CHANNEL = "via.sync.v2"


def expect(condition: Any, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ui", type=Path, required=True)
    parser.add_argument("--synchronizer", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--executable-path", default="/usr/bin/chromium")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    ui_uri = args.ui.resolve().as_uri()
    sync_uri = args.synchronizer.resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=args.executable_path, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(locale="zh-TW", reduced_motion="reduce")
        ui = context.new_page()
        sync = context.new_page()
        ui.goto(ui_uri, wait_until="load")
        sync.goto(sync_uri, wait_until="load")
        ui.locator("#investmentDesk").wait_for(state="visible")
        sync.locator("#templateSelect").wait_for(state="visible")
        time.sleep(0.15)

        def check(name: str, fn) -> None:
            started = time.perf_counter()
            detail: dict[str, Any] = {}
            try:
                value = fn()
                if isinstance(value, dict):
                    detail.update(value)
                results.append({"name": name, "passed": True, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "detail": detail})
            except Exception as exc:  # noqa: BLE001
                results.append({"name": name, "passed": False, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "detail": detail, "error": f"{type(exc).__name__}: {exc}"})

        check("same_file_origin", lambda: {
            "ui_origin": ui.evaluate("location.origin"),
            "sync_origin": sync.evaluate("location.origin"),
            "same_origin": ui.evaluate("location.origin") == sync.evaluate("location.origin"),
        })
        expect(ui.evaluate("location.origin") == sync.evaluate("location.origin"), "the two file pages do not share an origin")

        check("channel_and_storage_capability", lambda: {
            "ui_channel": ui.evaluate("window.VIA_ENGINE_HUB?.state?.channel"),
            "ui_storage_key": ui.evaluate("window.VIA_ENGINE_HUB?.state?.storageKey"),
            "sync_channel_visible": sync.locator("#channelCheck").is_checked(),
            "sync_storage_visible": sync.locator("#storageCheck").is_checked(),
        })
        expect(ui.evaluate("window.VIA_ENGINE_HUB?.state?.channel") == CHANNEL, "UI channel name mismatch")
        expect(ui.evaluate("window.VIA_ENGINE_HUB?.state?.storageKey") == KEY, "UI storage key mismatch")

        ui.evaluate(f"localStorage.removeItem('{KEY}'); localStorage.removeItem('via.sync.state.v1')")
        sync.reload(wait_until="load")
        ui.reload(wait_until="load")
        ui.locator("#investmentDesk").wait_for(state="visible")
        sync.locator("#templateSelect").wait_for(state="visible")

        check("synchronizer_to_ui_template_broadcast", lambda: _sync_template(sync, ui))
        check("ui_received_template_and_modules", lambda: _wait_ui_template(ui))
        expect(_wait_ui_template(ui)["template_id"] == "investment-research", "UI did not receive investment template")

        check("ui_to_synchronizer_view_broadcast", lambda: _sync_view(ui, sync))
        check("synchronizer_received_view_state", lambda: _wait_sync_view(sync))
        expect(_wait_sync_view(sync)["density"] == "compact", "SYNCHRONIZER did not receive compact density")

        check("local_storage_state_envelope", lambda: _storage_envelope(ui, sync))
        check("local_storage_event_to_synchronizer", lambda: _storage_event(ui, sync))
        check("sync_scope_view_only", lambda: _scope_view_only(sync, ui))
        check("sync_scope_modules_only", lambda: _scope_modules_only(sync, ui))
        check("manual_scope_blocks_broadcast", lambda: _manual_scope_blocks(sync, ui))

        context.close()
        browser.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary = {"total": len(results), "passed": sum(1 for item in results if item["passed"]), "failed": sum(1 for item in results if not item["passed"])}
    report = {"ui": str(args.ui.resolve()), "synchronizer": str(args.synchronizer.resolve()), "key": KEY, "channel": CHANNEL, "summary": summary, "results": results}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["failed"] == 0 else 1


def _sync_template(sync, ui) -> dict[str, Any]:
    sync.locator("#templateSelect").select_option("investment-research")
    sync.locator("#templateMode").select_option("replace")
    sync.locator("#applyTemplate").click()
    deadline = time.time() + 3
    while time.time() < deadline:
        snapshot = ui.evaluate("window.VIA_ENGINE_HUB?.state?.snapshot?.()")
        if snapshot and snapshot.get("analytics", {}).get("templateId") == "investment-research":
            return {"template_id": snapshot["analytics"]["templateId"], "module_ids": [m["id"] for m in snapshot.get("modules", [])]}
        time.sleep(0.05)
    raise AssertionError("template broadcast did not arrive at UI")


def _wait_ui_template(ui) -> dict[str, Any]:
    snapshot = ui.evaluate("window.VIA_ENGINE_HUB?.state?.snapshot?.()")
    return {"template_id": snapshot.get("analytics", {}).get("templateId"), "history": len(snapshot.get("analytics", {}).get("history", [])), "module_ids": [m["id"] for m in snapshot.get("modules", [])]}


def _sync_view(ui, sync) -> dict[str, Any]:
    ui.locator("[data-open-settings]").first.click()
    ui.locator("#settingsBackdrop").wait_for(state="visible")
    ui.locator('#settingsBackdrop [data-density="compact"]').click()
    ui.locator("#settingsBackdrop [data-close-settings]").first.click(force=True)
    deadline = time.time() + 3
    while time.time() < deadline:
        if sync.locator("#density").input_value() == "compact":
            return {"density": "compact", "stored": bool(sync.evaluate(f"localStorage.getItem('{KEY}')"))}
        time.sleep(0.05)
    raise AssertionError("view broadcast did not arrive at SYNCHRONIZER")


def _wait_sync_view(sync) -> dict[str, Any]:
    return {"density": sync.locator("#density").input_value(), "theme": sync.locator("#theme").input_value()}


def _storage_envelope(ui, sync) -> dict[str, Any]:
    ui_state = ui.evaluate(f"JSON.parse(localStorage.getItem('{KEY}'))")
    sync_state = sync.evaluate(f"JSON.parse(localStorage.getItem('{KEY}'))")
    expect(ui_state["version"] == 2 and sync_state["version"] == 2, "state version is not v2")
    expect(ui_state["analytics"]["templateId"] == "investment-research", "analytics template missing from storage")
    expect(ui_state["sync"]["revision"] == sync_state["sync"]["revision"], "revision differs across pages")
    return {"version": ui_state["version"], "revision": ui_state["sync"]["revision"], "template_id": ui_state["analytics"]["templateId"], "same_revision": True}


def _storage_event(ui, sync) -> dict[str, Any]:
    ui.evaluate(f"""() => {{
      const state = JSON.parse(localStorage.getItem('{KEY}'));
      state.view.theme = 'highContrast';
      state.updatedAt = new Date(Date.now() + 1000).toISOString();
      localStorage.setItem('{KEY}', JSON.stringify(state));
    }}""")
    deadline = time.time() + 3
    while time.time() < deadline:
        if sync.locator("#theme").input_value() == "highContrast":
            return {"theme": "highContrast", "sync_source": sync.evaluate("JSON.parse(localStorage.getItem('via.sync.state.v2')).source")}
        time.sleep(0.05)
    raise AssertionError("localStorage storage event did not arrive at SYNCHRONIZER")


def _scope_view_only(sync, ui) -> dict[str, Any]:
    sync.locator("#syncScope").select_option("view-only")
    sync.locator("#applyRules").click()
    time.sleep(0.4)
    before = ui.evaluate("window.VIA_ENGINE_HUB.state.snapshot().modules.map(module => module.id)")
    sync.locator("#moduleName").fill("View Only Module")
    sync.locator("#addModule").click()
    deadline = time.time() + 3
    while time.time() < deadline:
        after = ui.evaluate("window.VIA_ENGINE_HUB.state.snapshot().modules.map(module => module.id)")
        if after == before:
            return {"scope": sync.locator("#syncScope").input_value(), "ui_modules_unchanged": True, "ui_module_count": len(after)}
        time.sleep(0.05)
    raise AssertionError("view-only scope changed UI modules")


def _scope_modules_only(sync, ui) -> dict[str, Any]:
    sync.locator("#syncScope").select_option("modules-only")
    sync.locator("#applyRules").click()
    deadline = time.time() + 3
    while time.time() < deadline:
        scope = ui.evaluate("window.VIA_ENGINE_HUB.state.snapshot().sync.scope")
        if scope == "modules-only":
            break
        time.sleep(0.05)
    expect(ui.evaluate("window.VIA_ENGINE_HUB.state.snapshot().sync.scope") == "modules-only", "UI did not receive modules-only scope")
    before_theme = sync.locator("#theme").input_value()
    ui.locator("[data-open-settings]").first.click()
    ui.locator("#settingsBackdrop").wait_for(state="visible")
    ui.locator('#settingsBackdrop [data-theme="light"]').click()
    ui.locator("#settingsBackdrop [data-close-settings]").first.click(force=True)
    time.sleep(0.6)
    expect(sync.locator("#theme").input_value() == before_theme, "modules-only scope overwrote SYNCHRONIZER view")
    return {"scope": sync.locator("#syncScope").input_value(), "theme_preserved": True, "theme": before_theme}


def _manual_scope_blocks(sync, ui) -> dict[str, Any]:
    sync.locator("#syncScope").select_option("manual")
    sync.locator("#applyRules").click()
    time.sleep(0.4)
    before = ui.evaluate("window.VIA_ENGINE_HUB.state.snapshot().view.density")
    ui.locator("[data-open-settings]").first.click()
    ui.locator("#settingsBackdrop").wait_for(state="visible")
    ui.locator('#settingsBackdrop [data-density="comfortable"]').click()
    ui.locator("#settingsBackdrop [data-close-settings]").first.click(force=True)
    time.sleep(0.5)
    after = ui.evaluate("window.VIA_ENGINE_HUB.state.snapshot().view.density")
    css_density = ui.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--density').trim()")
    expect(css_density == "1.15", "UI visual density did not change under manual scope")
    expect(after == before, "manual scope unexpectedly published the UI state snapshot")
    expect(sync.locator("#density").input_value() == "compact", "manual scope incorrectly broadcast view")
    return {"scope": sync.locator("#syncScope").input_value(), "before_ui_density": before, "snapshot_after": after, "css_density": css_density, "sync_density": sync.locator("#density").input_value()}


if __name__ == "__main__":
    raise SystemExit(main())
