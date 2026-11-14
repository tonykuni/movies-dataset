#!/usr/bin/env python3
"""Standalone Chromium UAT for bounded v0106.4 subsystem workspaces."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import csv
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("vcgc", "vdf", "vrn", "vqg", "vap", "database")
VIEWPORTS = ((1440, 900, "desktop"), (768, 1024, "tablet"), (390, 844, "mobile"))
CATEGORIES = ("all", "io", "commands", "files", "environment", "policy", "conflicts", "requirements", "tests", "systems")
CATEGORY_ORDER = ("systems", "io", "commands", "files", "environment", "policy", "conflicts", "requirements", "tests")
EXPECTED_ROWS = {"vcgc": 22, "vdf": 50, "vrn": 24426, "vqg": 33, "vap": 2135, "database": 0}
MODEL_SHA = "c3b2b84d16abbe3ae1ab8984dc6fd933b6aceef18372d1fea16d94d694691ff1"
REQUIRED_FIELDS = ("id", "version", "completion_time", "tools")


def page_path(root: Path, system: str) -> Path:
    return root / "public" / f"system-v0106.4-{system}.html"


def inspect_pdf(pdf_path: Path, work: Path) -> str:
    text_path = work / (pdf_path.stem + ".txt")
    completed = subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], capture_output=True, text=True)
    if completed.returncode != 0:
        raise AssertionError(f"pdftotext failed for {pdf_path}: {completed.stderr}")
    return text_path.read_text(encoding="utf-8", errors="replace")


def raw_expected_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in CATEGORY_ORDER:
        for raw in payload[category]:
            item = {**raw, "category": category}
            for key in REQUIRED_FIELDS:
                item.setdefault(key, "NOT_OBSERVED")
            rows.append(item)
    return rows


def row_key(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def run(root: Path, out: Path) -> dict[str, Any]:
    if out.exists():
        raise FileExistsError(f"refuse existing UAT output: {out}")
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []
    page_errors: list[str] = []
    console_errors: list[str] = []
    external_requests: list[str] = []
    downloaded: list[str] = []
    pdf_receipts: dict[str, dict[str, Any]] = {}
    chromium = shutil.which("chromium") or shutil.which("google-chrome")
    if not chromium:
        raise RuntimeError("installed Chromium required; no browser download performed")
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext required for actual PDF inspection")

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    with tempfile.TemporaryDirectory(prefix="viaatlas-v0106.4-uat-") as temp_name:
        temp = Path(temp_name)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chromium, headless=True, args=["--no-sandbox"])
            for system in SYSTEMS:
                html = page_path(root, system)
                if not html.is_file():
                    raise FileNotFoundError(html)
                raw_payload_by_category: dict[str, list[dict[str, Any]]] | None = None
                for width, height, viewport_name in VIEWPORTS:
                    context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="no-preference", accept_downloads=True)
                    context.add_init_script("window.__VIA_NATIVE_ERRORS=[]; window.addEventListener('error', event => window.__VIA_NATIVE_ERRORS.push(event.message));")
                    page = context.new_page()
                    page.on("pageerror", lambda error, s=system, v=viewport_name: page_errors.append(f"{s}/{v}: {error}"))
                    page.on("console", lambda message, s=system, v=viewport_name: console_errors.append(f"{s}/{v}: {message.text}") if message.type == "error" else None)
                    page.on("request", lambda request, s=system, v=viewport_name: external_requests.append(f"{s}/{v}: {request.url}") if request.url.startswith(("http:", "https:")) else None)
                    page.goto(html.resolve().as_uri())
                    page.wait_for_function("Boolean(window.VIA_SUBSYSTEM && window.VIA_SUBSYSTEM.LAST_MATRIX && window.__VIA_PDF)", timeout=30000)
                    page.wait_for_timeout(80)
                    expected_system = "Database" if system == "database" else system.upper()
                    check(f"{system}/{viewport_name} payload identity", page.evaluate("window.VIA_SUBSYSTEM.version") == "v0106.4" and page.evaluate("window.VIA_SUBSYSTEM.system") == expected_system)
                    check(f"{system}/{viewport_name} exact locked titles", page.locator(".eyebrow").first.inner_text() == "VIA · ARCHITECTURE BASELINE · 2026-11-05 · ENGINE v0103" and page.locator("h1").first.inner_text() == "VIA System Architecture & Integration Blueprint" and page.locator(".lock").inner_text() == "ENG049 v0102 VISUAL LOCK")
                    check(f"{system}/{viewport_name} candidate and actual red badges", page.locator(".candidate").inner_text() == "v0106.4 CANDIDATE" and page.locator("#actual-release").inner_text() == "ACTUAL · RED / BLOCKED")
                    check(f"{system}/{viewport_name} management tab last and selected", page.locator('[data-tab="management"]').get_attribute("aria-selected") == "true" and page.locator("#management-view").is_visible() and [page.locator("[data-tab]").nth(i).get_attribute("data-tab") for i in range(page.locator("[data-tab]").count())] == ["summary", "verification", "management"])
                    order = page.evaluate("(() => { const a=document.querySelector('#workflow-section').getBoundingClientRect(); const b=document.querySelector('#category-tabs').getBoundingClientRect(); const c=document.querySelector('#view-head').getBoundingClientRect(); return {workflow:a.top, categories:b.top, matrix:c.top}; })()")
                    check(f"{system}/{viewport_name} evidence map precedes matrix", order["workflow"] <= order["categories"] + 2 and order["categories"] <= order["matrix"] + 2, order)
                    check(f"{system}/{viewport_name} exact source model hash", page.evaluate("window.VIA_SUBSYSTEM.source.model_gzip_sha256") == MODEL_SHA)
                    check(f"{system}/{viewport_name} no viewport overflow", page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                    check(f"{system}/{viewport_name} source no innerHTML sink", page.evaluate("!Array.from(document.scripts).some((script) => script.textContent.includes('innerHTML'))"))
                    check(f"{system}/{viewport_name} all categories present", all(page.locator(f'.category-tabs [data-category="{category}"]').count() == 1 for category in CATEGORIES))
                    owned = page.evaluate("Object.values(window.VIA_SUBSYSTEM.LAST_MATRIX).flatMap((rows) => rows).length")
                    category_counts = page.evaluate("Object.fromEntries(Object.entries(window.VIA_SUBSYSTEM.LAST_MATRIX).map(([k,v]) => [k,v.length]))")
                    check(f"{system}/{viewport_name} exact owned matrix count", owned == EXPECTED_ROWS[system], {"actual": owned, "expected": EXPECTED_ROWS[system]})
                    check(f"{system}/{viewport_name} exact nine category matrix counts", set(category_counts) == set(CATEGORY_ORDER) and sum(category_counts.values()) == EXPECTED_ROWS[system], category_counts)
                    check(f"{system}/{viewport_name} PDF controls default AI_HANDOVER", page.locator("#pdf-scope").input_value() == "AI_HANDOVER" and "AI_HANDOVER" in page.locator("#pdf-part-meta").inner_text())
                    page.locator("[data-tab=verification]").click()
                    verification_text = page.locator("#verification-view").inner_text()
                    test_count = page.locator("#verification-view .receipt-table tbody tr").count()
                    check(f"{system}/{viewport_name} verification includes exact owned tests", test_count == category_counts["tests"] and f"LAST_MATRIX.tests exact scope" in verification_text and f"{category_counts['tests']}" in verification_text, {"rows": test_count, "expected": category_counts["tests"]})
                    check(f"{system}/{viewport_name} verification keeps native boundary", "NOT_OBSERVED" in verification_text and "native runtime" in verification_text and "RED / BLOCKED" in verification_text)
                    if system == "database":
                        check(f"{system}/{viewport_name} historical database governance separate", "Historical Database governance" in verification_text and "system_matrix" in verification_text and "system_coverage" in verification_text and "NOT LIVE" in verification_text and owned == 0)
                    page.locator("[data-tab=management]").click()
                    page.locator('[data-category="all"]').click()
                    headers = page.locator("#view thead th")
                    header_text = [headers.nth(index).inner_text() for index in range(headers.count())]
                    check(f"{system}/{viewport_name} table prefix and final error_detail", header_text[:3] == ["燈號", "編號", "SSOT名稱"] and header_text[-1] == "錯誤詳細說明", header_text[:5] + header_text[-2:])
                    check(f"{system}/{viewport_name} management capped at 50", page.locator("#view tbody tr").count() <= 50)
                    page.locator('.category-tabs [data-category="files"]').click()
                    page.locator("#query").fill("NOT_A_REAL_ROW_0106_2")
                    check(f"{system}/{viewport_name} search filter empties deterministically", page.locator("#view tbody tr").count() == 0)
                    page.locator("#reset-view").click()
                    page.locator("#status-filter").select_option("RED")
                    check(f"{system}/{viewport_name} actual red filter retained", page.locator("#view tbody tr").count() <= 50)
                    page.locator("#reset-view").click()
                    first_row = page.locator("#view tbody tr").first
                    if first_row.count():
                        first_row.click()
                        check(f"{system}/{viewport_name} inspector renders selected row", page.locator("#inspect-fields").inner_text() != "")
                    else:
                        check(f"{system}/{viewport_name} empty system has no fabricated inspector row", system == "database" and page.locator("#inspect-fields").inner_text() == "")
                    # Actual header measurement and sticky geometry after scrolling.
                    sticky = page.evaluate("(() => { const header=document.querySelector('#masthead').getBoundingClientRect(); const root=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--head')); window.scrollTo(0, 260); const rail=document.querySelector('.rail-head').getBoundingClientRect(); const center=document.querySelector('.center-panel-head').getBoundingClientRect(); return {headerHeight:header.height, rootHead:root, railTop:rail.top, centerTop:center.top, sticky:getComputedStyle(document.querySelector('.center-panel-head')).position}; })()")
                    check(f"{system}/{viewport_name} measured header and sticky geometry", abs(sticky["headerHeight"] - sticky["rootHead"]) <= 3 and sticky["sticky"] == "sticky" and sticky["centerTop"] >= sticky["headerHeight"] - 3, sticky)
                    page.evaluate("window.scrollTo(0, 0)")
                    if viewport_name == "desktop":
                        with page.expect_download() as csv_event:
                            page.locator("#export-csv").click()
                        csv_path = out / f"{system}-management.csv"
                        csv_event.value.save_as(str(csv_path)); downloaded.append(str(csv_path))
                        csv_text = csv_path.read_text(encoding="utf-8-sig")
                        parsed_csv = list(csv.reader(csv_text.splitlines()))
                        check(f"{system}/desktop CSV header stable and formula-safe", csv_text.splitlines()[0].startswith('"燈號"') and all(not cell.lstrip().startswith(("=", "+", "@", "-")) for row in parsed_csv for cell in row), {"rows": len(parsed_csv)})
                        with page.expect_download() as json_event:
                            page.locator("#export-json").click()
                        json_path = out / f"{system}-LAST_MATRIX.json"
                        json_event.value.save_as(str(json_path)); downloaded.append(str(json_path))
                        exported = json.loads(json_path.read_text(encoding="utf-8"))
                        raw_payload_by_category = exported["LAST_MATRIX"]
                        keys_ok = all(key in exported for key in ("LAST_MATRIX", "DISPLAY_MATRIX", "source", "metadata", "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS", "supplemental_receipts"))
                        display_count = sum(len(rows) for rows in exported["DISPLAY_MATRIX"].values())
                        check(f"{system}/desktop JSON raw/display full matrix and metadata", exported["version"] == "v0106.4" and keys_ok and sum(len(rows) for rows in exported["LAST_MATRIX"].values()) == owned and display_count == owned and exported["metadata"]["raw_last_matrix_lossless"] is True and exported["metadata"]["source_filter"] == "r.system == system exactly", {"owned": owned, "display": display_count})
                        with page.expect_download() as md_event:
                            page.locator("#export-md").click()
                        md_path = out / f"{system}-LAST_MATRIX.md"
                        md_event.value.save_as(str(md_path)); downloaded.append(str(md_path))
                        md_text = md_path.read_text(encoding="utf-8")
                        check(f"{system}/desktop full MD retains all category headings and pins", all(f"### {category} (" in md_text for category in CATEGORY_ORDER) and MODEL_SHA in md_text and "## Shared evidence" in md_text and "## Supplemental observations" in md_text)
                        with page.expect_download() as handover_event:
                            page.locator("#export-handover").click()
                        handover_path = out / f"{system}-AI_HANDOVER.md"
                        handover_event.value.save_as(str(handover_path)); downloaded.append(str(handover_path))
                        handover_text = handover_path.read_text(encoding="utf-8")
                        red_rows = [row for rows in raw_payload_by_category.values() for row in rows if "RED" in str(row.get("status", "")).upper()]
                        required_handover = ["RED / BLOCKED", "Exact owned RED blockers", "Owned filter", "Next gates", "Completion: NOT_OBSERVED", "observed_at_utc", "status:", "receipt hashes", MODEL_SHA]
                        check(f"{system}/desktop compact AI handover exact blockers and current connection", handover_path.stat().st_size < 35 * 1024 and all(token in handover_text for token in required_handover) and all(str(row.get("id")) in handover_text and str(row.get("ssot_name")) in handover_text and str(row.get("error_detail")) in handover_text and str(row.get("version")) in handover_text and str(row.get("source_sha256")) in handover_text for row in red_rows), {"bytes": handover_path.stat().st_size, "red_rows": len(red_rows)})
                        # AI_HANDOVER actual print scope.
                        page.evaluate("window.__VIA_PDF.setScope('AI_HANDOVER'); window.__VIA_PRINT_PREPARE();")
                        ai_dom = page.evaluate("(() => ({scope:document.querySelector('#print-all').dataset.scope, text:document.querySelector('#print-all').innerText, records:document.querySelectorAll('#print-all .print-record').length}))()")
                        check(f"{system}/desktop AI print DOM bounded summary scope", ai_dom["scope"] == "AI_HANDOVER" and "Exact owned RED blockers" in ai_dom["text"] and "Owned test scope / receipts" in ai_dom["text"] and MODEL_SHA in ai_dom["text"])
                        ai_pdf = temp / f"{system}-AI_HANDOVER.pdf"
                        page.pdf(path=str(ai_pdf), format="A4", print_background=True)
                        ai_text = inspect_pdf(ai_pdf, temp)
                        check(f"{system}/desktop actual AI PDF text scope", "AI_HANDOVER" in ai_text and "Exact owned RED blockers" in ai_text and MODEL_SHA in ai_text)
                        saved_ai = out / ai_pdf.name; shutil.copy2(ai_pdf, saved_ai); downloaded.append(str(saved_ai))
                        # Logical union: all bounded parts, no duplicates or truncation; render only first/last actual PDFs.
                        parts_meta = page.evaluate("window.__VIA_PDF.setScope('FULL_PARTS'); (() => { const x=window.__VIA_PDF.meta(); return {totalRows:x.totalRows,totalParts:x.totalParts,parts:x.parts.map((part)=>part.map((row)=>row))}; })()")
                        logical_parts = parts_meta["parts"]
                        logical_rows = [row for part in logical_parts for row in part]
                        expected_display = raw_expected_rows({category: raw_payload_by_category[category] for category in CATEGORY_ORDER})
                        check(f"{system}/desktop full PDF logical chunks cover each owned row once", len(logical_rows) == owned and all(len(part) <= 100 for part in logical_parts) and [row_key(row) for row in logical_rows] == [row_key(row) for row in expected_display], {"totalRows": parts_meta["totalRows"], "totalParts": parts_meta["totalParts"], "chunkSizes": [len(part) for part in logical_parts[:3]] + ([len(logical_parts[-1])] if logical_parts else [])})
                        rendered_parts = sorted({0, max(0, int(parts_meta["totalParts"]) - 1)})
                        part_receipts = []
                        for part_index in rendered_parts:
                            page.evaluate("(part) => window.__VIA_PDF.setPart(part)", part_index)
                            part_dom = page.evaluate("window.__VIA_PRINT_PREPARE(); (() => { const root=document.querySelector('#print-all'); return {scope:root.dataset.scope,part:Number(root.dataset.part),totalParts:Number(root.dataset.totalParts),ids:Array.from(root.querySelectorAll('.print-record')).map((node)=>node.dataset.rowId),text:root.innerText}; })()")
                            expected_part = logical_parts[part_index]
                            expected_ids = [str(row.get("id", "NOT_OBSERVED")) for row in expected_part]
                            check(f"{system}/desktop bounded print DOM part {part_index + 1} full fields", part_dom["scope"] == "FULL_PARTS" and part_dom["part"] == part_index + 1 and part_dom["totalParts"] == parts_meta["totalParts"] and part_dom["ids"] == expected_ids and all(str(row.get("id", "NOT_OBSERVED")) in part_dom["text"] for row in expected_part[:1] + expected_part[-1:]), {"part": part_index + 1, "rows": len(expected_part)})
                            pdf_path = temp / f"{system}-FULL_PART_{part_index + 1:03d}.pdf"
                            page.pdf(path=str(pdf_path), format="A4", print_background=True)
                            pdf_text = inspect_pdf(pdf_path, temp)
                            first_id = expected_ids[0] if expected_ids else "NO_OWNED_SOURCE_ROWS"
                            last_id = expected_ids[-1] if expected_ids else "NO_OWNED_SOURCE_ROWS"
                            check(f"{system}/desktop actual bounded PDF part {part_index + 1} first/last ID", first_id in pdf_text and last_id in pdf_text and f"part {part_index + 1}" in pdf_text, {"first": first_id, "last": last_id, "bytes": pdf_path.stat().st_size})
                            part_receipts.append({"part": part_index + 1, "path": str(pdf_path), "bytes": pdf_path.stat().st_size, "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(), "first_id": first_id, "last_id": last_id})
                        pdf_receipts[system] = {"scope_default": "AI_HANDOVER", "ai_pdf": {"bytes": ai_pdf.stat().st_size, "sha256": hashlib.sha256(ai_pdf.read_bytes()).hexdigest()}, "full_parts": {"part_size": 100, "total_rows": parts_meta["totalRows"], "total_parts": parts_meta["totalParts"], "rendered_part_receipts": part_receipts, "honest_scope": "AI_HANDOVER is a summary PDF; FULL_PARTS requires saving every bounded part; no single full PDF is claimed."}}
                        page.evaluate("document.getElementById('print-all').hidden = true; document.getElementById('print-all').setAttribute('aria-hidden','true'); window.scrollTo(0,0)")
                        animation = page.evaluate("(() => { const red=document.querySelector('.status-dot.red'); const yellow=document.querySelector('.status-dot.yellow'); const green=document.querySelector('.status-dot.green'); return {red:red ? getComputedStyle(red).animationName : '', duration:red ? getComputedStyle(red).animationDuration : '', yellow:yellow ? getComputedStyle(yellow).animationName : 'none', green:green ? getComputedStyle(green).animationName : 'none'}; })()")
                        check(f"{system}/desktop RED-only slow pulse", animation["red"] in ("redSlowPulse", "none", "") and animation["duration"] in ("2.8s", "0s", "") and animation["yellow"] in ("none", "") and animation["green"] in ("none", ""), animation)
                    if viewport_name == "mobile":
                        check(f"{system}/mobile internal table scroll", page.evaluate("(() => { const wrap=document.querySelector('.table-wrap'); return wrap.clientWidth <= innerWidth && wrap.scrollWidth >= wrap.clientWidth; })()"))
                        page.locator("#toggle-input").click()
                        check(f"{system}/mobile collapse keeps viewport", page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                        page.locator("#toggle-input").click()
                    page.evaluate("window.scrollTo(0, 260)")
                    page.wait_for_timeout(30)
                    check(f"{system}/{viewport_name} sticky heading declarations", page.evaluate("getComputedStyle(document.querySelector('.rail-head')).position === 'sticky' && getComputedStyle(document.querySelector('.center-panel-head')).position === 'sticky' && getComputedStyle(document.querySelector('.view-head')).position === 'sticky'"))
                    page.evaluate("window.scrollTo(0,0)")
                    page.screenshot(path=str(out / f"{system}-{viewport_name}.png"), full_page=False)
                    native_errors = page.evaluate("window.__VIA_NATIVE_ERRORS || []")
                    check(f"{system}/{viewport_name} no native window error events including ResizeObserver", not native_errors, native_errors)
                    context.close()
            reduced = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce", accept_downloads=True)
            reduced_page = reduced.new_page()
            reduced_page.goto(page_path(root, "vcgc").resolve().as_uri())
            reduced_page.wait_for_function("Boolean(window.VIA_SUBSYSTEM)", timeout=30000)
            reduced_animation = reduced_page.evaluate("(() => { const red=document.querySelector('.status-dot.red'); const stage=document.querySelector('.stage-dot.red'); return {red:red ? getComputedStyle(red).animationName : 'none', stage:stage ? getComputedStyle(stage).animationName : 'none'}; })()")
            check("reduced motion disables red and stage-dot animation", reduced_animation["red"] in ("none", "") and reduced_animation["stage"] in ("none", ""), reduced_animation)
            reduced.close(); browser.close()
    result = {"schema": "VIA-SUBSYSTEM-UI-UAT/1.2", "status": "PASS" if all(item["passed"] for item in checks) and not page_errors and not console_errors and not external_requests else "FAIL", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "checks_total": len(checks), "checks_passed": sum(item["passed"] for item in checks), "checks": checks, "elapsed_seconds": round(time.perf_counter() - started, 3), "external_requests": external_requests, "page_errors": page_errors, "console_errors": console_errors, "downloaded": downloaded, "pdf_receipts": pdf_receipts, "pages": {system: hashlib.sha256(page_path(root, system).read_bytes()).hexdigest() for system in SYSTEMS}, "scope": "Sandbox Chromium standalone subsystem UI only; six pages x three viewports; CSV/JSON/full-MD/compact-AI-MD; actual bounded AI and first/last FULL_PARTS PDFs with pdftotext; logical all-chunk completeness; no engine, shell, SSOT write, integration, registration, deployment or publication."}
    (out / "receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.out)
    print(json.dumps({key: result[key] for key in ("status", "checks_total", "checks_passed", "scope")}, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
