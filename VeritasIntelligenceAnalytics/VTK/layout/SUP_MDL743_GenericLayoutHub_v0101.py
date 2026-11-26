#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reuse the locked GLE package for complete, source-backed layout review.

The existing extraction, financial values, dictionaries and database are not
modified. Regions come from complete page elements; position labels never crop
the input. This is review evidence, not a financial verification verdict.
"""
from __future__ import annotations

import base64
import hashlib
import html
import importlib.metadata
import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path

# def 01_PARAMETERS: one versioned policy owns route and output settings.
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
POLICY_PATH = VIA / "supportive modules/registry/VIA_Layout_Reuse_SSOT_v0100.json"
VERSION = "v0101"
SCHEMA = "VIA.LayoutReview.v1"
PREVIOUS = HERE / "SUP_MDL743_GenericLayoutHub_v0100.py"
SUMMARY_NAME = "LAYOUT_REVIEW.json"
HTML_NAME = "LAYOUT_REVIEW.html"

# ===== [VIA:ACCEL-BRIDGE:v0100] existing canonical compatibility bridge =====
try:
    sys.path.insert(0, str(VIA / "supportive modules"))
    import VIA_SuperAccel_Module as VIA_ACCEL
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====


def def_load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_previous = def_load(PREVIOUS, "via_layout_hub_locked_v0100")


def __getattr__(name: str):
    return getattr(_previous, name)


def def_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8-sig"))


def def_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def def_locked_sources(policy: dict) -> dict:
    result = {}
    for relative, expected in policy["locked_sources"].items():
        path = VIA / relative
        actual = def_sha(path) if path.is_file() else "ABSENT"
        result[relative] = {"expected": expected, "actual": actual,
                            "state": "UNCHANGED" if actual == expected else "MISMATCH"}
    return result


def def_signature(path: Path, policy: dict) -> str:
    mounted = _previous.mount()
    if mounted.get("state") != "VERIFIED":
        raise RuntimeError("ABSENT: registered GenericLayoutEngine package")
    root = Path(mounted["dir"])
    engines = {name: def_sha(root / (name + ".py")) for name in _previous.GLE_MODULES}
    packages = {}
    for name in policy["cache_packages"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "ABSENT"
    data = {"input_sha256": def_sha(path), "filename": path.name,
            "engines": engines, "packages": packages, "policy": policy,
            "bridge_sha256": def_sha(Path(__file__))}
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def def_analyze(path: Path, output_root: Path) -> dict:
    """Run existing route/core once; retain every page, cell and source bbox."""
    path = path.resolve()
    policy = def_policy()
    signature = def_signature(path, policy)
    folder = output_root.resolve() / "documents" / signature
    manifest = folder / "layout_review.json"
    if manifest.is_file():
        try:
            cached = json.loads(manifest.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            cached = {}
        pages = cached.get("layout", {}).get("pages", [])
        images_ready = bool(pages) and all(
            p.get("image_path") and Path(p["image_path"]).is_file() for p in pages)
        if cached.get("signature") == signature and cached.get("cacheable") and images_ready:
            cached["cache_hit"] = True
            return cached
    folder.mkdir(parents=True, exist_ok=True)
    orchestrator = _previous.orchestrator()
    core = _previous.gle()
    if orchestrator is None or core is None:
        raise RuntimeError("ABSENT: registered layout modules")
    route_config = orchestrator.OrchestratorConfig(**policy["route"])
    for key, value in policy["adapter"].items():
        setattr(route_config.adapter, key, value)
    run = orchestrator.run_orchestrator(path, folder / "consensus", route_config)
    native = next((r for r in run.adapter_results if r.adapter_name == "pdfplumber" and r.accepted), None)
    if native is None:
        native = next((r for r in run.adapter_results if r.accepted and any(e.bbox for e in r.elements)), None)
    native_elements = [asdict(e) for e in native.elements if e.bbox and e.element_type == "TEXT"] if native else []
    financial_engine = def_load(VIA / policy["financial_table_engine"], "layout_locked_financial_tables")
    financial_tables = financial_engine.extract_document_tables(path)
    config = core.EngineConfig(**policy["core"])
    document, outputs = core.analyze_document(path, folder / "core", config)
    data = core.document_to_dict(document, folder / "core", config)
    # No role or position filter: even elements marked noise remain in evidence.
    for page in data["pages"]:
        for key in ("image_path", "annotated_image_path"):
            if page.get(key):
                page[key] = str((folder / "core" / page[key]).resolve())
    statuses = [{"name": item.adapter_name, "status": item.status,
                 "warnings": item.warnings, "error": item.error}
                for item in run.adapter_results]
    has_text = any(page["native_character_count"] or page["used_ocr"] for page in data["pages"])
    accepted = any(item.accepted for item in run.adapter_results)
    result = {"schema": SCHEMA, "via": "vcgc", "filename": path.name,
              "signature": signature, "input_sha256": data["file_sha256"],
              "state": "REVIEW" if has_text and accepted else "NODATA",
              "cache_hit": False,
              "cacheable": has_text and accepted and all(
                  page["native_character_count"] >= config.min_native_characters
                  and not page["used_ocr"] for page in data["pages"]),
              "extraction_policy": "locked; no basic/financial database writes",
              "engine_package": _previous.mount()["dir_name"],
              "route": run.route, "backends": statuses,
              "native_geometry": native_elements,
              "native_geometry_source": native.adapter_name if native else "ABSENT",
              "financial_tables": financial_tables,
              "consensus_elements": len(run.canonical_elements),
              "core_outputs": outputs, "layout": data}
    temporary = manifest.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(manifest)
    return result


def def_native_svg(page: dict, elements: list[dict]) -> str:
    """Preserve the existing adapter's word positions, including unruled tables."""
    words = [e for e in elements if e.get("page") == page["physical_page"] and e.get("bbox") and e.get("text")]
    if not words:
        return '<p>本頁無可用文字座標，請查看原頁；不以空白表示擷取成功。</p>'
    parts = []
    for word in words:
        x0, y0, x1, y1 = word["bbox"]
        if x1 <= x0 or y1 <= y0:
            continue
        metadata = word.get("metadata") or {}
        size = float(metadata.get("font_size") or min(y1-y0, 10))
        weight = "700" if "bold" in str(metadata.get("fontname", "")).casefold() else "400"
        parts.append(f'<text x="{x0}" y="{y0}" font-size="{size}" font-weight="{weight}" '
                     f'dominant-baseline="text-before-edge" textLength="{x1-x0}" lengthAdjust="spacingAndGlyphs">'
                     f'{html.escape(word["text"])}</text>')
    return (f'<svg class="page-reconstruction" role="img" aria-label="依原座標還原整頁文字" '
            f'viewBox="0 0 {page["width"]} {page["height"]}" style="width:100%;max-width:760px;background:white">'
            + ''.join(parts) + '</svg>')


def def_financial_matrix(table: dict) -> str:
    """Display the locked reader's matrix separately from source geometry."""
    rows = table.get("Rows") or []
    body = ''.join('<tr>' + ''.join('<td>' + html.escape("" if cell is None else str(cell)) + '</td>' for cell in row) + '</tr>' for row in rows)
    note = "僅有表頭，結構化資料未完整；請核對上方整頁還原。" if len(rows) < 2 else "沿用既有財務表格讀取結果；未改寫原始值。"
    return f'<p>{note}</p><div class="matrix"><table>{body}</table></div>'


def def_tables(page: dict) -> list[dict]:
    """Group the engine's cells without changing values or deriving periods."""
    tables = {}
    for element in page.get("elements", []):
        if element.get("element_type") != "TABLE":
            continue
        metadata = element.get("metadata") or {}
        index = metadata.get("table_index")
        if index is None:
            continue
        group = tables.setdefault(index, {"index": index, "cells": [], "bbox_pt": None})
        if metadata.get("row") is not None and metadata.get("column") is not None:
            group["cells"].append(element)
        elif element.get("subtype") == "CONTENT":
            group["bbox_pt"] = element.get("bbox_pt")
    return [tables[k] for k in sorted(tables) if tables[k]["cells"]]


def def_table_svg(table: dict) -> str:
    """Render source rectangles directly; merged-cell geometry is retained."""
    cells = table["cells"]
    boxes = [c["bbox_pt"] for c in cells]
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    if x1 <= x0 or y1 <= y0:
        return "<p>表格座標不足，請查看原頁。</p>"
    parts = []
    for cell in cells:
        a, b, c, d = cell["bbox_pt"]
        raw = cell.get("raw_text", "")
        text = cell.get("repaired_text") or raw
        meta = cell["metadata"]
        label = f'row {meta["row"]}, column {meta["column"]}: {raw}'
        parts.append(f'<g data-row="{meta["row"]}" data-column="{meta["column"]}">'
                     f'<title>{html.escape(label)}</title>'
                     f'<rect x="{a}" y="{b}" width="{c-a}" height="{d-b}" fill="white" stroke="#c8c3ba" stroke-width="0.3"/>'
                     f'<foreignObject x="{a+0.6}" y="{b+0.3}" width="{max(c-a-1.2,0.1)}" height="{max(d-b-0.6,0.1)}">'
                     f'<div xmlns="http://www.w3.org/1999/xhtml" class="cell">{html.escape(text)}</div>'
                     '</foreignObject></g>')
    return (f'<svg role="img" aria-label="表格重建" viewBox="{x0} {y0} {x1-x0} {y1-y0}" '
            f'style="width:100%;max-width:{(x1-x0)*1.8}px">' + ''.join(parts) + '</svg>')


def def_render(report: dict, destination: Path) -> None:
    sections = []
    for item in report["documents"]:
        name = html.escape(item["filename"])
        pages = item["layout"]["pages"]
        content = []
        for page in sorted(pages, key=lambda p: p["physical_page"]):
            tables = def_tables(page)
            financial = [t for t in item.get("financial_tables", []) if t.get("PageNumber") == page["physical_page"]]
            original = ""
            picture = Path(page["image_path"]) if page.get("image_path") else None
            if picture and picture.is_file():
                encoded = base64.b64encode(picture.read_bytes()).decode("ascii")
                original = f'<details><summary>原頁對照</summary><img loading="lazy" src="data:image/png;base64,{encoded}" alt="{name} 第 {page["physical_page"]} 頁原頁"></details>'
            raw_blocks = ""
            if page["physical_page"] == 1:
                blocks = sorted(page["elements"], key=lambda e: (e.get("reading_order") or 10**9))
                raw_blocks = '<details><summary>首頁完整區塊與內文</summary>' + ''.join(
                    f'<article data-element="{html.escape(e["element_id"])}"><small>{html.escape(e["zone"])} · {html.escape(e["element_type"])}.{html.escape(e["subtype"])}</small><pre>{html.escape(e.get("repaired_text") or e.get("raw_text") or "")}</pre></article>'
                    for e in blocks if e.get("raw_text") or e.get("repaired_text")) + '</details>'
            grids = ''.join(f'<h4>表格 {t["index"]}</h4>{def_table_svg(t)}' for t in tables)
            matrices = ''.join('<h4>' + html.escape(t.get("TableID", "")) + '</h4>' + def_financial_matrix(t) for t in financial)
            geometry = def_native_svg(page, item.get("native_geometry", []))
            opened = " open" if page["physical_page"] == 1 else ""
            content.append(f'<section data-page="{page["physical_page"]}"><h3>第 {page["physical_page"]} 頁</h3>{original}'
                           f'<details{opened}><summary>版面還原（保留整頁文字座標）</summary>{geometry}</details>{raw_blocks}'
                           f'<details><summary>FINANCIAL DATA／結構化表格候選（仍須核對列欄）</summary>{grids}{matrices}</details></section>')
        sections.append(f'<div class="report" data-filename="{name}"><h2>{name}</h2><p>{item["state"]} · {len(pages)} 頁 · 表格與數值待原頁核對</p>{"".join(content)}</div>')
    failures = ''.join(f'<li>{html.escape(e["filename"])}：{html.escape(e["error"])}</li>' for e in report["errors"])
    text = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VRN Layout Review</title><style>
body{margin:0;background:#faf8f3;color:#302f2b;font:12px/1.5 Arial,"Noto Sans TC",sans-serif}header,main{max-width:1120px;margin:auto;padding:18px}header{border-bottom:1px solid #ded8ca}header strong{display:block}header p{margin:4px 0}h2{font-size:16px;overflow-wrap:anywhere}h3{font-size:13px}h4{margin:8px 0;font-size:12px}.report{padding:14px;background:white;border:1px solid #e5dfd2;margin:14px 0}section{padding:8px 0;border-top:1px solid #e9e3d8}details{margin:7px 0}summary{cursor:pointer}img{max-width:760px;width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}.cell{font:6.5px/1.15 Arial,"Noto Sans TC",sans-serif;white-space:pre-wrap;overflow-wrap:anywhere;color:#242424}svg{display:block;margin:6px 0}article{border-bottom:1px solid #eee}small{color:#756c5f}@media(max-width:650px){header,main{padding:8px}.report{padding:8px}}
</style><header><strong>VERITAS INTELLIGENCE ANALYTICS</strong><p>DISCIPLINA • PRUDENTIA • INTEGRITAS</p><strong>AI-Powered Research &amp; Decision Intelligence Platform</strong><p>VeritasReportNova · 版面與表格還原 · 依輸入檔名排序</p></header><main>'''
    text += '<style>.matrix{overflow:auto}.matrix table{border-collapse:collapse;font-size:11px}.matrix td{border:1px solid #ddd;padding:3px 5px;white-space:pre-wrap}.page-reconstruction text{font-family:Arial,"Noto Sans TC",sans-serif;fill:#242424}</style>'
    text += '<p>沿用既有 GLE 引擎。原頁、整頁文字座標、表格候選並存；表格辨識不完整時仍保留整頁內容。此頁為核對證據。</p>'
    text += '<ul>' + failures + '</ul>' + ''.join(sections) + '</main></html>'
    destination.write_text(text, encoding="utf-8")


def def_run_batch(source: Path, output_root: Path) -> dict:
    policy = def_policy()
    before = def_locked_sources(policy)
    if any(v["state"] != "UNCHANGED" for v in before.values()):
        raise RuntimeError("LOCK_MISMATCH: extraction baseline changed; review before layout run")
    files = [source] if source.is_file() else list(source.rglob("*")) if source.is_dir() else []
    files = sorted((p for p in files if p.is_file() and p.suffix.lower() == ".pdf"), key=lambda p: (p.name.casefold(), p.name, str(p)))
    documents, errors = [], []
    for i, path in enumerate(files, 1):
        print(f'[Layout {i}/{len(files)}] {path.name}', flush=True)
        try:
            documents.append(def_analyze(path, output_root))
        except Exception as exc:
            errors.append({"filename": path.name, "error": f"{type(exc).__name__}: {exc}"})
    after = def_locked_sources(policy)
    if before != after:
        raise RuntimeError("LOCK_MISMATCH: protected sources changed during review")
    report = {"schema": SCHEMA, "via": "vcgc", "engine": "SUP_MDL743/" + VERSION,
              "state": "ERROR" if errors else "REVIEW" if any(d["state"] == "REVIEW" for d in documents) else "NODATA",
              "documents": documents, "errors": errors, "locked_sources": after,
              "order": "input filename, physical page, original table geometry",
              "financial_database_written": False,
              "cache_hits": sum(bool(d["cache_hit"]) for d in documents)}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / SUMMARY_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    def_render(report, output_root / HTML_NAME)
    return report


def selftest() -> int:
    import unittest
    if _previous.selftest():
        return 1
    tests = def_load(HERE / "tests/test_layout_reuse_v0100.py", "via_layout_reuse_tests")
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return _previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
