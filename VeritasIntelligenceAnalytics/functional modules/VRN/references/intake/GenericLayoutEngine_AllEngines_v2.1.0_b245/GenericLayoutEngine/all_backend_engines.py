#!/usr/bin/env python3
"""Concrete adapters for the full local PDF/image extraction matrix."""

from __future__ import annotations

# =============================================================================
# 01. PARAMETERS — ordered from lightest to heaviest
# =============================================================================

PDFPLUMBER_PRIORITY = 10
PYPDF_PRIORITY = 20
POPPLER_PRIORITY = 30
PDF_PARSE_PRIORITY = 40
PYMUPDF_PRIORITY = 50
PDFMINER_PRIORITY = 60
PDFBOX_PRIORITY = 70
PDFJS_PRIORITY = 80
MUPDF_PRIORITY = 90
PYMUPDF4LLM_PRIORITY = 95
CAMEL0T_PRIORITY = 96
TABULA_PRIORITY = 97
DOCLING_PRIORITY = 110
UNSTRUCTURED_PRIORITY = 120
TIKA_PRIORITY = 130
PDFSHARP_PRIORITY = 140
MARKER_PRIORITY = 210
MINERU_PRIORITY = 220
LAYOUTPARSER_PRIORITY = 230
DEEPDOCTECTION_PRIORITY = 240
HURIDOCS_PRIORITY = 250
TABLE_TRANSFORMER_PRIORITY = 260
TESSERACT_PRIORITY = 310
PADDLE_OCR_PRIORITY = 320
PADDLE_PPSTRUCTURE_PRIORITY = 330
PADDLE_LAYOUT_PRIORITY = 340
PADDLE_PDF_PRIORITY = 345
PADDLE_DETECTION_PRIORITY = 350
EASYOCR_PRIORITY = 360
OCRMYPDF_PRIORITY = 370
TRANSKRIBUS_PRIORITY = 380
ADOBE_EXTRACT_PRIORITY = 900


# =============================================================================
# 02. IMPORTS
# =============================================================================

import json
import os
import re
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from adapter_sdk import (
    AdapterContext,
    AdapterElement,
    AdapterProbe,
    AdapterResult,
    BaseAdapter,
    ExternalCommandAdapter,
    STATUS_PASS,
    STATUS_SKIPPED_POLICY,
    module_exists,
    normalize_text,
    package_version,
    run_command,
    utc_timestamp,
)


# =============================================================================
# 03. SHARED ADAPTER HELPERS
# =============================================================================

def result_shell(adapter: BaseAdapter, probe: AdapterProbe) -> AdapterResult:
    return AdapterResult(
        adapter_name=adapter.name,
        resource_level=adapter.resource_level,
        priority=adapter.priority,
        status=STATUS_PASS,
        started_utc=utc_timestamp(),
        duration_ms=0,
        capabilities=list(adapter.capabilities),
        probe=probe,
    )


def bbox_from_any(value: Any) -> Optional[list[float]]:
    if value is None:
        return None
    if hasattr(value, "as_tuple"):
        value = value.as_tuple()
    if hasattr(value, "l") and hasattr(value, "t") and hasattr(value, "r") and hasattr(value, "b"):
        value = [value.l, value.t, value.r, value.b]
    if isinstance(value, dict):
        candidates = [
            value.get("bbox"),
            [value.get("x0"), value.get("y0"), value.get("x1"), value.get("y1")],
            [value.get("left"), value.get("top"), value.get("right"), value.get("bottom")],
        ]
        for candidate in candidates:
            parsed = bbox_from_any(candidate)
            if parsed:
                return parsed
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 4:
        try:
            return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
        except (TypeError, ValueError):
            return None
    return None


def render_pdf_pages(context: AdapterContext) -> list[Path]:
    if context.page_images and all(path.exists() for path in context.page_images):
        return context.page_images
    if context.input_path.suffix.casefold() != ".pdf":
        return [context.input_path]
    if not module_exists("fitz"):
        return []
    import fitz  # type: ignore

    destination = context.work_dir / "rendered_pages"
    destination.mkdir(parents=True, exist_ok=True)
    document = fitz.open(str(context.input_path))
    paths: list[Path] = []
    try:
        matrix = fitz.Matrix(context.config.dpi / 72.0, context.config.dpi / 72.0)
        for index, page in enumerate(document, start=1):
            path = destination / f"page_{index:04d}.png"
            if not path.exists():
                page.get_pixmap(matrix=matrix, alpha=False).save(str(path))
            paths.append(path)
    finally:
        document.close()
    context.page_images = paths
    return paths


def image_dimensions(path: Path) -> tuple[Optional[float], Optional[float]]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            width, height = image.size
        return float(width), float(height)
    except Exception:
        return None, None


def resolved_tesseract_languages(context: AdapterContext) -> tuple[str, list[str]]:
    requested = [item.strip() for item in context.config.ocr_languages.split("+") if item.strip()]
    executable = shutil.which("tesseract")
    if not executable:
        return context.config.ocr_languages, []
    try:
        completed = run_command([executable, "--list-langs"], context.config, timeout_seconds=15)
        available = {
            line.strip() for line in completed.stdout.splitlines()
            if line.strip() and not line.casefold().startswith("list of available")
        }
    except Exception:
        return context.config.ocr_languages, []
    selected = [language for language in requested if language in available]
    missing = [language for language in requested if language not in available]
    if not selected and "eng" in available:
        selected = ["eng"]
    return "+".join(selected), missing


def command_from_template(template: str, input_path: Path, output_dir: Path) -> list[str]:
    formatted = template.format(input=str(input_path), output=str(output_dir))
    return shlex.split(formatted, posix=os.name != "nt")


def markdown_to_elements(markdown: str) -> list[AdapterElement]:
    elements: list[AdapterElement] = []
    page = 1
    order = 0
    for line in markdown.splitlines():
        text = normalize_text(line)
        if not text:
            continue
        order += 1
        hashes = len(line) - len(line.lstrip("#"))
        if hashes:
            subtype = f"H{min(3, hashes)}"
            element_type = "TEXT"
            text = normalize_text(line.lstrip("#"))
        elif line.lstrip().startswith(("|", "+---")):
            element_type = "TABLE"
            subtype = "DATA"
        elif re.match(r"^[-*+]\s+", line):
            element_type = "TEXT"
            subtype = "BULLET"
        else:
            element_type = "TEXT"
            subtype = "BODY"
        elements.append(
            AdapterElement(
                page=page,
                text=text,
                element_type=element_type,
                subtype=subtype,
                confidence=0.75,
                reading_order=order,
            )
        )
    return elements


def find_first_text_file(directory: Path, suffixes: Sequence[str]) -> Optional[Path]:
    for suffix in suffixes:
        matches = sorted(directory.rglob(f"*{suffix}"))
        if matches:
            return matches[0]
    return None


def package_major_version(distribution_name: str) -> int:
    value = package_version(distribution_name) or "0"
    match = re.match(r"^(\d+)", value)
    return int(match.group(1)) if match else 0


def paddle_result_payload(value: Any) -> dict[str, Any]:
    payload = value.json if hasattr(value, "json") else value
    if callable(payload):
        payload = payload()
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        return {}
    root = payload.get("res", payload)
    return root if isinstance(root, dict) else {}


def paddle_label_contract(label: str) -> tuple[str, str]:
    lowered = label.casefold().replace("-", "_").replace(" ", "_")
    if "table" in lowered:
        return "TABLE", "CONTENT"
    if any(token in lowered for token in ("figure", "image", "chart")):
        return "FIGURE", "CONTENT"
    if "document_title" in lowered:
        return "TEXT", "H1"
    if any(token in lowered for token in ("paragraph_title", "section_title", "title")):
        return "TEXT", "H2"
    if "header" in lowered:
        return "PAGE_META", "HEADER"
    if "footer" in lowered or "page_number" in lowered:
        return "PAGE_META", "FOOTER"
    if "formula" in lowered:
        return "FORMULA", "CONTENT"
    return "TEXT", "BODY"


def paddle_v3_elements(page_result: Any, fallback_page: int) -> list[AdapterElement]:
    root = paddle_result_payload(page_result)
    page_value = root.get("page_index")
    page_number = int(page_value) + 1 if page_value is not None else fallback_page
    items = root.get("parsing_res_list")
    if not isinstance(items, list):
        items = root.get("boxes", [])
    elements: list[AdapterElement] = []
    for order, item in enumerate(items if isinstance(items, list) else [], start=1):
        if not isinstance(item, dict):
            continue
        label = str(item.get("block_label", item.get("label", item.get("type", "text"))))
        element_type, subtype = paddle_label_contract(label)
        text = normalize_text(str(item.get("block_content", item.get("text", item.get("content", "")))))
        bbox = bbox_from_any(
            item.get("block_bbox", item.get("coordinate", item.get("bbox")))
        )
        elements.append(
            AdapterElement(
                page=page_number,
                text=text,
                bbox=bbox,
                element_type=element_type,
                subtype=subtype,
                confidence=float(item.get("score", item.get("confidence", 0.80))),
                reading_order=int(item.get("block_order", item.get("order", order))),
                metadata={
                    "paddle_label": label,
                    "coordinate_space": "paddle_pixels",
                    "paddle_api": 3,
                },
            )
        )
    return elements


# =============================================================================
# 04. LEVEL 1 — LIGHTWEIGHT STRUCTURE ENGINES
# =============================================================================

class PdfPlumberEngine(BaseAdapter):
    name = "pdfplumber"
    resource_level = 1
    priority = PDFPLUMBER_PRIORITY
    capabilities = ("text", "bbox", "font", "table", "layout")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("pdfplumber") and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name,
            available=available,
            module_available=module_exists("pdfplumber"),
            version=package_version("pdfplumber"),
            reason="available" if available else "requires pdfplumber and PDF input",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import pdfplumber  # type: ignore

        probe = self.probe(context)
        result = result_shell(self, probe)
        texts: list[str] = []
        with pdfplumber.open(str(context.input_path)) as document:
            for page_number, page in enumerate(document.pages, start=1):
                page_text = page.extract_text(layout=True) or page.extract_text() or ""
                texts.append(page_text)
                words = page.extract_words(
                    use_text_flow=True,
                    keep_blank_chars=False,
                    extra_attrs=["fontname", "size"],
                )
                for order, word in enumerate(words, start=1):
                    text = normalize_text(str(word.get("text", "")))
                    if not text:
                        continue
                    result.elements.append(
                        AdapterElement(
                            page=page_number,
                            text=text,
                            bbox=[
                                float(word.get("x0", 0)), float(word.get("top", 0)),
                                float(word.get("x1", 0)), float(word.get("bottom", 0)),
                            ],
                            confidence=0.98,
                            reading_order=order,
                            metadata={
                                "fontname": word.get("fontname"),
                                "font_size": word.get("size"),
                                "page_width": float(page.width),
                                "page_height": float(page.height),
                            },
                        )
                    )
                try:
                    tables = page.find_tables(
                        table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"}
                    )
                except Exception as exc:
                    result.warnings.append(f"page {page_number} table detection failed: {exc}")
                    tables = []
                for table_number, table in enumerate(tables, start=1):
                    table_bbox = bbox_from_any(table.bbox)
                    result.elements.append(
                        AdapterElement(
                            page=page_number,
                            bbox=table_bbox,
                            element_type="TABLE",
                            subtype="CONTENT",
                            confidence=0.92,
                            metadata={
                                "table_number": table_number,
                                "page_width": float(page.width),
                                "page_height": float(page.height),
                            },
                        )
                    )
                    for row_index, row in enumerate(getattr(table, "rows", []), start=1):
                        for column_index, cell in enumerate(getattr(row, "cells", []), start=1):
                            cell_bbox = bbox_from_any(cell)
                            if not cell_bbox:
                                continue
                            try:
                                cell_text = normalize_text(page.crop(tuple(cell_bbox)).extract_text() or "")
                            except Exception:
                                cell_text = ""
                            result.elements.append(
                                AdapterElement(
                                    page=page_number,
                                    text=cell_text,
                                    bbox=cell_bbox,
                                    element_type="TABLE",
                                    subtype="HEADER" if row_index == 1 else ("STUB" if column_index == 1 else "DATA"),
                                    confidence=0.90,
                                    row=row_index,
                                    column=column_index,
                                    metadata={
                                        "table_number": table_number,
                                        "page_width": float(page.width),
                                        "page_height": float(page.height),
                                    },
                                )
                            )
        result.document_text = "\n\f\n".join(texts)
        return result


class PyPdfEngine(BaseAdapter):
    name = "pypdf"
    resource_level = 1
    priority = PYPDF_PRIORITY
    capabilities = ("text", "metadata")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("pypdf") and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name,
            available=available,
            module_available=module_exists("pypdf"),
            version=package_version("pypdf"),
            reason="available" if available else "requires pypdf and PDF input",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        from pypdf import PdfReader  # type: ignore

        result = result_shell(self, self.probe(context))
        reader = PdfReader(str(context.input_path))
        texts: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
            texts.append(text)
            result.elements.append(
                AdapterElement(page=page_number, text=text, element_type="TEXT", subtype="BODY", confidence=0.82)
            )
        result.document_text = "\n\f\n".join(texts)
        return result


class PopplerEngine(ExternalCommandAdapter):
    name = "poppler_pdftotext"
    resource_level = 1
    priority = POPPLER_PRIORITY
    capabilities = ("text", "layout")
    binary_name = "pdftotext"

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        completed = run_command(
            [shutil.which("pdftotext") or "pdftotext", "-layout", "-enc", "UTF-8", str(context.input_path), "-"],
            context.config,
        )
        result.document_text = completed.stdout
        for page_number, text in enumerate(completed.stdout.split("\f"), start=1):
            if normalize_text(text):
                result.elements.append(AdapterElement(page=page_number, text=text, confidence=0.75))
        return result


class PdfParseNodeEngine(ExternalCommandAdapter):
    name = "pdf_parse_node"
    resource_level = 1
    priority = PDF_PARSE_PRIORITY
    capabilities = ("text", "metadata")
    binary_name = "node"
    environment_command_key = "GLE_PDF_PARSE_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        base = super().probe(context)
        if self.configured_command(context):
            return base
        if not shutil.which("node"):
            base.available = False
            base.reason = "node executable unavailable"
            return base
        try:
            run_command(
                ["node", "-e", "try{require.resolve('pdf-parse');process.exit(0)}catch(e){process.exit(1)}"],
                context.config,
                timeout_seconds=15,
            )
            base.available = True
            base.reason = "available"
        except Exception:
            base.available = False
            base.reason = "pdf-parse node package unavailable"
        return base

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        configured = self.configured_command(context)
        if configured:
            command = command_from_template(configured, context.input_path, context.work_dir / self.name)
        else:
            script = (
                "const fs=require('fs');const pdf=require('pdf-parse');"
                "pdf(fs.readFileSync(process.argv[1])).then(x=>process.stdout.write(JSON.stringify({text:x.text,numpages:x.numpages,info:x.info||{}})))"
            )
            command = ["node", "-e", script, str(context.input_path)]
        completed = run_command(command, context.config)
        payload = json.loads(completed.stdout)
        result.document_text = str(payload.get("text", ""))
        result.elements.append(AdapterElement(page=1, text=result.document_text, confidence=0.72, metadata=payload.get("info", {})))
        return result


# =============================================================================
# 05. LEVEL 2 — GEOMETRY, FONT, MULTI-COLUMN, TABLE ENGINES
# =============================================================================

class PyMuPdfEngine(BaseAdapter):
    name = "pymupdf"
    resource_level = 2
    priority = PYMUPDF_PRIORITY
    capabilities = ("text", "bbox", "font", "image", "layout")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("fitz") and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name, available=available, module_available=module_exists("fitz"),
            version=package_version("PyMuPDF"), reason="available" if available else "requires PyMuPDF and PDF input"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import fitz  # type: ignore

        result = result_shell(self, self.probe(context))
        document = fitz.open(str(context.input_path))
        texts: list[str] = []
        try:
            for page_number, page in enumerate(document, start=1):
                texts.append(page.get_text("text", sort=True))
                order = 0
                for block in page.get_text("dict", sort=True).get("blocks", []):
                    if block.get("type") == 1:
                        result.elements.append(
                            AdapterElement(
                                page=page_number,
                                bbox=bbox_from_any(block.get("bbox")),
                                element_type="FIGURE",
                                subtype="CONTENT",
                                confidence=0.98,
                                metadata={
                                    "page_width": float(page.rect.width),
                                    "page_height": float(page.rect.height),
                                },
                            )
                        )
                    if block.get("type") != 0:
                        continue
                    for line in block.get("lines", []):
                        spans = line.get("spans", [])
                        text = normalize_text("".join(str(span.get("text", "")) for span in spans))
                        if not text:
                            continue
                        order += 1
                        dominant = max(spans, key=lambda item: len(str(item.get("text", ""))))
                        result.elements.append(
                            AdapterElement(
                                page=page_number,
                                text=text,
                                bbox=bbox_from_any(line.get("bbox")),
                                confidence=0.99,
                                reading_order=order,
                                metadata={
                                    "font": dominant.get("font"),
                                    "font_size": dominant.get("size"),
                                    "flags": dominant.get("flags"),
                                    "page_width": float(page.rect.width),
                                    "page_height": float(page.rect.height),
                                },
                            )
                        )
        finally:
            document.close()
        result.document_text = "\n\f\n".join(texts)
        return result


class PdfMinerEngine(BaseAdapter):
    name = "pdfminer_six"
    resource_level = 2
    priority = PDFMINER_PRIORITY
    capabilities = ("text", "bbox", "font", "layout")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("pdfminer") and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name, available=available, module_available=module_exists("pdfminer"),
            version=package_version("pdfminer.six"), reason="available" if available else "requires pdfminer.six and PDF input"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        from pdfminer.high_level import extract_pages  # type: ignore
        from pdfminer.layout import LTChar, LTTextContainer  # type: ignore

        result = result_shell(self, self.probe(context))
        texts: list[str] = []
        for page_number, layout in enumerate(extract_pages(str(context.input_path)), start=1):
            page_height = float(getattr(layout, "height", 0.0))
            page_width = float(getattr(layout, "width", 0.0))
            order = 0
            for item in layout:
                if not isinstance(item, LTTextContainer):
                    continue
                text = normalize_text(item.get_text())
                if not text:
                    continue
                order += 1
                x0, y0, x1, y1 = map(float, item.bbox)
                top_bbox = [x0, page_height - y1, x1, page_height - y0]
                fonts: list[str] = []
                sizes: list[float] = []
                for line in item:
                    for character in line:
                        if isinstance(character, LTChar):
                            fonts.append(str(character.fontname))
                            sizes.append(float(character.size))
                result.elements.append(
                    AdapterElement(
                        page=page_number,
                        text=text,
                        bbox=top_bbox,
                        confidence=0.96,
                        reading_order=order,
                        metadata={
                            "font": max(set(fonts), key=fonts.count) if fonts else None,
                            "font_size": sum(sizes) / len(sizes) if sizes else None,
                            "page_width": page_width,
                            "page_height": page_height,
                        },
                    )
                )
                texts.append(text)
        result.document_text = "\n".join(texts)
        return result


class PdfBoxEngine(ExternalCommandAdapter):
    name = "apache_pdfbox"
    resource_level = 2
    priority = PDFBOX_PRIORITY
    capabilities = ("text", "metadata", "java")
    binary_name = "java"
    environment_command_key = "GLE_PDFBOX_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        base = super().probe(context)
        jar = context.config.environment.get("PDFBOX_JAR") or os.environ.get("PDFBOX_JAR")
        base.configured = bool(self.configured_command(context) or jar)
        base.available = bool(shutil.which("java") and base.configured)
        base.reason = "available" if base.available else "set PDFBOX_JAR or GLE_PDFBOX_COMMAND"
        return base

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        configured = self.configured_command(context)
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "pdfbox.txt"
        if configured:
            command = command_from_template(configured, context.input_path, output_dir)
        else:
            jar = context.config.environment.get("PDFBOX_JAR") or os.environ["PDFBOX_JAR"]
            command = ["java", "-jar", jar, "export:text", "-i", str(context.input_path), "-o", str(output_path)]
        completed = run_command(command, context.config)
        text = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else completed.stdout
        result.document_text = text
        result.elements.append(AdapterElement(page=1, text=text, confidence=0.78))
        if output_path.exists():
            result.artifacts["text"] = str(output_path)
        return result


class PdfJsEngine(ExternalCommandAdapter):
    name = "pdfjs_node"
    resource_level = 2
    priority = PDFJS_PRIORITY
    capabilities = ("text", "bbox", "javascript")
    binary_name = "node"
    environment_command_key = "GLE_PDFJS_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        base = super().probe(context)
        if self.configured_command(context):
            return base
        if not shutil.which("node"):
            base.available = False
            base.reason = "node executable unavailable"
            return base
        try:
            run_command(
                ["node", "-e", "import('pdfjs-dist/legacy/build/pdf.mjs').then(()=>process.exit(0)).catch(()=>process.exit(1))"],
                context.config,
                timeout_seconds=20,
            )
            base.available = True
            base.reason = "available"
        except Exception:
            base.available = False
            base.reason = "pdfjs-dist node package unavailable"
        return base

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        configured = self.configured_command(context)
        if configured:
            command = command_from_template(configured, context.input_path, context.work_dir / self.name)
        else:
            script = """
import fs from 'fs';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.mjs';
const data=new Uint8Array(fs.readFileSync(process.argv[1]));
const doc=await pdfjsLib.getDocument({data}).promise; const out=[];
for(let p=1;p<=doc.numPages;p++){const page=await doc.getPage(p);const c=await page.getTextContent();
 for(const i of c.items){out.push({page:p,text:i.str,bbox:[i.transform[4],i.transform[5],i.transform[4]+i.width,i.transform[5]+i.height]});}}
process.stdout.write(JSON.stringify(out));
"""
            command = ["node", "--input-type=module", "-e", script, str(context.input_path)]
        completed = run_command(command, context.config)
        payload = json.loads(completed.stdout)
        for order, item in enumerate(payload, start=1):
            result.elements.append(
                AdapterElement(
                    page=int(item.get("page", 1)), text=normalize_text(item.get("text", "")),
                    bbox=bbox_from_any(item.get("bbox")), confidence=0.86, reading_order=order,
                )
            )
        result.document_text = "\n".join(element.text for element in result.elements)
        return result


class MuPdfCliEngine(ExternalCommandAdapter):
    name = "mupdf_cli"
    resource_level = 2
    priority = MUPDF_PRIORITY
    capabilities = ("text", "layout", "c_cpp")
    binary_name = "mutool"
    environment_command_key = "GLE_MUPDF_COMMAND"

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        configured = self.configured_command(context)
        command = command_from_template(configured, context.input_path, context.work_dir / self.name) if configured else ["mutool", "draw", "-F", "txt", str(context.input_path)]
        completed = run_command(command, context.config)
        result.document_text = completed.stdout
        result.elements.append(AdapterElement(page=1, text=completed.stdout, confidence=0.80))
        return result


class PyMuPdf4LlmEngine(BaseAdapter):
    name = "pymupdf4llm"
    resource_level = 2
    priority = PYMUPDF4LLM_PRIORITY
    capabilities = ("text", "markdown", "layout", "rag")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("pymupdf4llm") and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name, available=available, module_available=module_exists("pymupdf4llm"),
            version=package_version("pymupdf4llm"), reason="available" if available else "requires pymupdf4llm and PDF input"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import pymupdf4llm  # type: ignore

        result = result_shell(self, self.probe(context))
        markdown = pymupdf4llm.to_markdown(str(context.input_path))
        result.markdown = str(markdown)
        result.document_text = re.sub(r"[#*_`|]", "", result.markdown)
        result.elements = markdown_to_elements(result.markdown)
        return result


class CamelotEngine(BaseAdapter):
    name = "camelot"
    resource_level = 2
    priority = CAMEL0T_PRIORITY
    capabilities = ("table", "csv", "bbox")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("camelot") and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name, available=available, module_available=module_exists("camelot"),
            version=package_version("camelot-py"), reason="available" if available else "requires camelot and PDF input"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import camelot  # type: ignore

        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        tables = camelot.read_pdf(str(context.input_path), pages="all", flavor="lattice")
        text_parts: list[str] = []
        for table_number, table in enumerate(tables, start=1):
            page_number = int(getattr(table, "page", 1))
            bbox = bbox_from_any(getattr(table, "_bbox", None))
            result.elements.append(
                AdapterElement(page=page_number, bbox=bbox, element_type="TABLE", subtype="CONTENT", confidence=0.90, metadata={"table_number": table_number, "accuracy": getattr(table, "accuracy", None)})
            )
            frame = table.df
            csv_path = output_dir / f"table_{table_number:04d}.csv"
            frame.to_csv(csv_path, index=False, header=False, encoding="utf-8-sig")
            result.artifacts[f"table_{table_number}"] = str(csv_path)
            for row_index, row in frame.iterrows():
                for column_index, value in enumerate(row.tolist()):
                    text = normalize_text(str(value))
                    result.elements.append(
                        AdapterElement(
                            page=page_number, text=text, element_type="TABLE",
                            subtype="HEADER" if row_index == 0 else ("STUB" if column_index == 0 else "DATA"),
                            confidence=0.86, row=int(row_index) + 1, column=column_index + 1,
                            metadata={"table_number": table_number},
                        )
                    )
            text_parts.append(frame.to_csv(index=False, header=False))
        result.document_text = "\n".join(text_parts)
        return result


class TabulaEngine(BaseAdapter):
    name = "tabula_py"
    resource_level = 2
    priority = TABULA_PRIORITY
    capabilities = ("table", "csv", "java")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("tabula") and bool(shutil.which("java")) and context.input_path.suffix.casefold() == ".pdf"
        return AdapterProbe(
            name=self.name, available=available, module_available=module_exists("tabula"),
            binary_available=bool(shutil.which("java")), version=package_version("tabula-py"),
            reason="available" if available else "requires tabula-py, Java, and PDF input",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import tabula  # type: ignore

        result = result_shell(self, self.probe(context))
        frames = tabula.read_pdf(str(context.input_path), pages="all", multiple_tables=True, lattice=True)
        text_parts: list[str] = []
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        for table_number, frame in enumerate(frames, start=1):
            path = output_dir / f"table_{table_number:04d}.csv"
            frame.to_csv(path, index=False, encoding="utf-8-sig")
            result.artifacts[f"table_{table_number}"] = str(path)
            result.elements.append(AdapterElement(page=1, element_type="TABLE", subtype="CONTENT", confidence=0.75, metadata={"table_number": table_number}))
            text_parts.append(frame.to_csv(index=False))
        result.document_text = "\n".join(text_parts)
        return result


# =============================================================================
# 06. LEVEL 3 — LAYOUT-AWARE DOCUMENT RECONSTRUCTION
# =============================================================================

class DoclingEngine(BaseAdapter):
    name = "docling"
    resource_level = 3
    priority = DOCLING_PRIORITY
    capabilities = ("text", "markdown", "layout", "table", "figure", "rag")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("docling")
        return AdapterProbe(
            name=self.name, available=available, module_available=available,
            version=package_version("docling"), reason="available" if available else "requires docling"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        from docling.document_converter import DocumentConverter  # type: ignore

        result = result_shell(self, self.probe(context))
        conversion = DocumentConverter().convert(str(context.input_path))
        document = conversion.document
        result.markdown = document.export_to_markdown()
        result.document_text = re.sub(r"[#*_`|]", "", result.markdown)
        result.elements = markdown_to_elements(result.markdown)
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / "document.md"
        markdown_path.write_text(result.markdown, encoding="utf-8")
        result.artifacts["markdown"] = str(markdown_path)
        try:
            json_path = output_dir / "document.json"
            json_path.write_text(json.dumps(document.export_to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            result.artifacts["json"] = str(json_path)
        except Exception as exc:
            result.warnings.append(f"Docling JSON export skipped: {exc}")
        return result


class UnstructuredEngine(BaseAdapter):
    name = "unstructured"
    resource_level = 3
    priority = UNSTRUCTURED_PRIORITY
    capabilities = ("text", "layout", "table", "semantic", "rag")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("unstructured")
        return AdapterProbe(
            name=self.name, available=available, module_available=available,
            version=package_version("unstructured"), reason="available" if available else "requires unstructured"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        from unstructured.partition.auto import partition  # type: ignore

        result = result_shell(self, self.probe(context))
        parts = partition(filename=str(context.input_path), strategy="auto")
        text_parts: list[str] = []
        for order, part in enumerate(parts, start=1):
            text = normalize_text(str(part))
            if not text:
                continue
            metadata = part.metadata.to_dict() if hasattr(part, "metadata") else {}
            page = int(metadata.get("page_number") or 1)
            category = str(getattr(part, "category", type(part).__name__))
            category_lower = category.casefold()
            if "title" in category_lower:
                element_type, subtype = "TEXT", "H2"
            elif "table" in category_lower:
                element_type, subtype = "TABLE", "CONTENT"
            elif "list" in category_lower:
                element_type, subtype = "TEXT", "BULLET"
            elif "image" in category_lower or "figure" in category_lower:
                element_type, subtype = "FIGURE", "CONTENT"
            else:
                element_type, subtype = "TEXT", "BODY"
            coordinates = metadata.get("coordinates") or {}
            bbox = None
            points = coordinates.get("points") if isinstance(coordinates, dict) else None
            if points and len(points) >= 3:
                xs = [float(point[0]) for point in points]
                ys = [float(point[1]) for point in points]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            result.elements.append(
                AdapterElement(
                    page=page, text=text, bbox=bbox, element_type=element_type, subtype=subtype,
                    confidence=0.84, reading_order=order, metadata={"category": category, **metadata},
                )
            )
            text_parts.append(text)
        result.document_text = "\n".join(text_parts)
        return result


class ApacheTikaEngine(ExternalCommandAdapter):
    name = "apache_tika"
    resource_level = 3
    priority = TIKA_PRIORITY
    capabilities = ("text", "metadata", "java", "multi_format")
    binary_name = "java"
    environment_command_key = "GLE_TIKA_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        base = super().probe(context)
        jar = context.config.environment.get("TIKA_JAR") or os.environ.get("TIKA_JAR")
        base.configured = bool(self.configured_command(context) or jar)
        base.available = bool(shutil.which("java") and base.configured)
        base.reason = "available" if base.available else "set TIKA_JAR or GLE_TIKA_COMMAND"
        return base

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        configured = self.configured_command(context)
        if configured:
            command = command_from_template(configured, context.input_path, context.work_dir / self.name)
        else:
            jar = context.config.environment.get("TIKA_JAR") or os.environ["TIKA_JAR"]
            command = ["java", "-jar", jar, "--text", str(context.input_path)]
        completed = run_command(command, context.config)
        result.document_text = completed.stdout
        result.elements.append(AdapterElement(page=1, text=completed.stdout, confidence=0.76))
        return result


class PdfSharpEngine(ExternalCommandAdapter):
    name = "pdfsharp_dotnet"
    resource_level = 3
    priority = PDFSHARP_PRIORITY
    capabilities = ("text", "layout", "dotnet")
    binary_name = "dotnet"
    environment_command_key = "GLE_PDFSHARP_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        base = super().probe(context)
        base.available = bool(shutil.which("dotnet") and self.configured_command(context))
        base.configured = bool(self.configured_command(context))
        base.reason = "available" if base.available else "set GLE_PDFSHARP_COMMAND to a PdfSharp helper template"
        return base

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        command = command_from_template(self.configured_command(context) or "", context.input_path, output_dir)
        completed = run_command(command, context.config)
        text_path = find_first_text_file(output_dir, [".txt", ".json"])
        result.document_text = text_path.read_text(encoding="utf-8", errors="replace") if text_path else completed.stdout
        result.elements.append(AdapterElement(page=1, text=result.document_text, confidence=0.72))
        if text_path:
            result.artifacts["output"] = str(text_path)
        return result


# =============================================================================
# 07. LEVEL 4 — DEEP LAYOUT, FORMULA, AND VISION ENGINES
# =============================================================================

class MarkerEngine(ExternalCommandAdapter):
    name = "marker"
    resource_level = 4
    priority = MARKER_PRIORITY
    capabilities = ("text", "markdown", "layout", "formula", "table", "figure")
    heavy = True
    binary_name = "marker_single"
    module_name = "marker"
    distribution_name = "marker-pdf"
    environment_command_key = "GLE_MARKER_COMMAND"

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        configured = self.configured_command(context)
        command = command_from_template(configured, context.input_path, output_dir) if configured else [
            shutil.which("marker_single") or "marker_single", str(context.input_path), "--output_dir", str(output_dir)
        ]
        completed = run_command(command, context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        markdown_path = find_first_text_file(output_dir, [".md", ".markdown"])
        result.markdown = markdown_path.read_text(encoding="utf-8", errors="replace") if markdown_path else completed.stdout
        result.document_text = re.sub(r"[#*_`|]", "", result.markdown)
        result.elements = markdown_to_elements(result.markdown)
        if markdown_path:
            result.artifacts["markdown"] = str(markdown_path)
        return result


class MinerUEngine(ExternalCommandAdapter):
    name = "mineru"
    resource_level = 4
    priority = MINERU_PRIORITY
    capabilities = ("text", "markdown", "layout", "formula", "table", "figure")
    heavy = True
    module_name = "magic_pdf"
    binary_name = "magic-pdf"
    distribution_name = "magic-pdf"
    environment_command_key = "GLE_MINERU_COMMAND"

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        configured = self.configured_command(context)
        command = command_from_template(configured, context.input_path, output_dir) if configured else [
            shutil.which("magic-pdf") or "magic-pdf", "-p", str(context.input_path), "-o", str(output_dir), "-m", "auto"
        ]
        completed = run_command(command, context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        markdown_path = find_first_text_file(output_dir, [".md", ".markdown"])
        result.markdown = markdown_path.read_text(encoding="utf-8", errors="replace") if markdown_path else completed.stdout
        result.document_text = re.sub(r"[#*_`|]", "", result.markdown)
        result.elements = markdown_to_elements(result.markdown)
        if markdown_path:
            result.artifacts["markdown"] = str(markdown_path)
        return result


class LayoutParserEngine(BaseAdapter):
    name = "layoutparser"
    resource_level = 4
    priority = LAYOUTPARSER_PRIORITY
    capabilities = ("layout", "bbox", "vision", "table", "figure")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        configured = bool(context.config.environment.get("LAYOUTPARSER_MODEL_URI") or os.environ.get("LAYOUTPARSER_MODEL_URI"))
        available = module_exists("layoutparser") and configured
        return AdapterProbe(
            name=self.name, available=available, module_available=module_exists("layoutparser"), configured=configured,
            version=package_version("layoutparser"), reason="available" if available else "requires layoutparser and LAYOUTPARSER_MODEL_URI"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import layoutparser as lp  # type: ignore
        from PIL import Image

        result = result_shell(self, self.probe(context))
        model_uri = context.config.environment.get("LAYOUTPARSER_MODEL_URI") or os.environ["LAYOUTPARSER_MODEL_URI"]
        label_map_raw = context.config.environment.get("LAYOUTPARSER_LABEL_MAP") or os.environ.get("LAYOUTPARSER_LABEL_MAP", "{}")
        label_map = {int(key): value for key, value in json.loads(label_map_raw).items()}
        model = lp.Detectron2LayoutModel(model_uri, label_map=label_map or None, extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5])
        for page_number, path in enumerate(render_pdf_pages(context), start=1):
            image = Image.open(path).convert("RGB")
            layout = model.detect(image)
            for order, block in enumerate(layout, start=1):
                label = str(getattr(block, "type", "Text"))
                lowered = label.casefold()
                if "table" in lowered:
                    element_type, subtype = "TABLE", "CONTENT"
                elif "figure" in lowered or "image" in lowered:
                    element_type, subtype = "FIGURE", "CONTENT"
                elif "title" in lowered:
                    element_type, subtype = "TEXT", "H2"
                else:
                    element_type, subtype = "TEXT", "BODY"
                result.elements.append(
                    AdapterElement(
                        page=page_number, bbox=bbox_from_any(block.coordinates), element_type=element_type,
                        subtype=subtype, confidence=float(getattr(block, "score", 0.75)), reading_order=order,
                        metadata={"model_label": label},
                    )
                )
        result.document_text = ""
        return result


class DeepDoctectionEngine(BaseAdapter):
    name = "deepdoctection"
    resource_level = 4
    priority = DEEPDOCTECTION_PRIORITY
    capabilities = ("layout", "bbox", "vision", "table", "ocr")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("deepdoctection")
        return AdapterProbe(
            name=self.name, available=available, module_available=available,
            version=package_version("deepdoctection"), reason="available" if available else "requires deepdoctection and local model weights"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import deepdoctection as dd  # type: ignore

        result = result_shell(self, self.probe(context))
        analyzer = dd.get_dd_analyzer()
        dataflow = analyzer.analyze(path=str(context.input_path))
        dataflow.reset_state()
        for page_number, page in enumerate(dataflow, start=1):
            if hasattr(page, "as_dict"):
                page_dict = page.as_dict()
            else:
                page_dict = json.loads(page.as_json())
            for order, annotation in enumerate(page_dict.get("layouts", page_dict.get("annotations", [])), start=1):
                category = str(annotation.get("category_name", annotation.get("category", "text")))
                lowered = category.casefold()
                element_type = "TABLE" if "table" in lowered else ("FIGURE" if "figure" in lowered else "TEXT")
                subtype = "CONTENT" if element_type != "TEXT" else ("H2" if "title" in lowered else "BODY")
                result.elements.append(
                    AdapterElement(
                        page=page_number, text=normalize_text(annotation.get("text", "")),
                        bbox=bbox_from_any(annotation.get("bounding_box", annotation.get("bbox"))),
                        element_type=element_type, subtype=subtype,
                        confidence=float(annotation.get("score", 0.75)), reading_order=order,
                        metadata={"model_label": category},
                    )
                )
        result.document_text = "\n".join(element.text for element in result.elements if element.text)
        return result


class HuriDocsEngine(ExternalCommandAdapter):
    name = "huridocs_vgt"
    resource_level = 4
    priority = HURIDOCS_PRIORITY
    capabilities = ("layout", "bbox", "vision", "reading_order")
    heavy = True
    module_name = "pdf_document_layout_analysis"
    environment_command_key = "GLE_HURIDOCS_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        base = super().probe(context)
        base.configured = bool(self.configured_command(context))
        base.available = base.configured
        base.reason = "available" if base.available else "set GLE_HURIDOCS_COMMAND for the installed HURIDOCS runner"
        return base

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        configured = self.configured_command(context)
        if not configured:
            raise RuntimeError("HURIDOCS Python distributions vary; configure GLE_HURIDOCS_COMMAND")
        completed = run_command(command_from_template(configured, context.input_path, output_dir), context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        json_path = find_first_text_file(output_dir, [".json", ".jsonl"])
        payload = json.loads(json_path.read_text(encoding="utf-8")) if json_path else json.loads(completed.stdout)
        items = payload.get("elements", payload if isinstance(payload, list) else [])
        for order, item in enumerate(items, start=1):
            result.elements.append(
                AdapterElement(
                    page=int(item.get("page", item.get("page_number", 1))), text=normalize_text(item.get("text", "")),
                    bbox=bbox_from_any(item.get("bbox")), element_type=str(item.get("type", "TEXT")).upper(),
                    subtype=str(item.get("subtype", "BODY")).upper(), confidence=float(item.get("confidence", 0.75)),
                    reading_order=order, metadata={"raw_label": item.get("label")},
                )
            )
        result.document_text = "\n".join(element.text for element in result.elements if element.text)
        if json_path:
            result.artifacts["json"] = str(json_path)
        return result


class TableTransformerEngine(BaseAdapter):
    name = "table_transformer"
    resource_level = 4
    priority = TABLE_TRANSFORMER_PRIORITY
    capabilities = ("table", "bbox", "vision", "table_structure")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("transformers") and module_exists("torch") and module_exists("PIL")
        return AdapterProbe(
            name=self.name, available=available, module_available=available,
            version=package_version("transformers"), reason="available" if available else "requires transformers, torch, Pillow, and cached TATR weights"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import torch  # type: ignore
        from PIL import Image
        from transformers import AutoImageProcessor, TableTransformerForObjectDetection  # type: ignore

        result = result_shell(self, self.probe(context))
        model_name = context.config.environment.get("TATR_MODEL", "microsoft/table-transformer-detection")
        local_only = not context.config.allow_model_downloads
        processor = AutoImageProcessor.from_pretrained(model_name, local_files_only=local_only)
        model = TableTransformerForObjectDetection.from_pretrained(model_name, local_files_only=local_only)
        model.eval()
        for page_number, path in enumerate(render_pdf_pages(context), start=1):
            image = Image.open(path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs)
            target_sizes = torch.tensor([image.size[::-1]])
            processed = processor.post_process_object_detection(outputs, threshold=0.70, target_sizes=target_sizes)[0]
            for score, label, box in zip(processed["scores"], processed["labels"], processed["boxes"]):
                result.elements.append(
                    AdapterElement(
                        page=page_number, bbox=[float(value) for value in box.tolist()],
                        element_type="TABLE", subtype="CONTENT", confidence=float(score),
                        metadata={"label_id": int(label)},
                    )
                )
        return result


# =============================================================================
# 08. LEVEL 5 — OCR AND SCANNED DOCUMENT ENGINES
# =============================================================================

class TesseractEngine(ExternalCommandAdapter):
    name = "tesseract"
    resource_level = 5
    priority = TESSERACT_PRIORITY
    capabilities = ("ocr", "text", "bbox", "layout", "multilingual")
    binary_name = "tesseract"

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        executable = shutil.which("tesseract") or "tesseract"
        languages, missing_languages = resolved_tesseract_languages(context)
        if not languages:
            raise RuntimeError("none of the requested Tesseract languages are installed")
        if missing_languages:
            result.warnings.append(
                "missing Tesseract languages: " + ", ".join(missing_languages)
                + f"; using {languages}"
            )
        for page_number, image_path in enumerate(render_pdf_pages(context), start=1):
            page_width, page_height = image_dimensions(image_path)
            completed = run_command(
                [executable, str(image_path), "stdout", "-l", languages, "tsv"],
                context.config,
                timeout_seconds=context.config.heavy_timeout_seconds,
            )
            rows = completed.stdout.splitlines()
            if not rows:
                continue
            headers = rows[0].split("\t")
            groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
            for row_text in rows[1:]:
                values = row_text.split("\t", len(headers) - 1)
                if len(values) != len(headers):
                    continue
                row = dict(zip(headers, values))
                text = normalize_text(row.get("text", ""))
                try:
                    confidence = float(row.get("conf", "-1"))
                except ValueError:
                    confidence = -1.0
                if not text or confidence < 0:
                    continue
                key = (row.get("block_num", "0"), row.get("par_num", "0"), row.get("line_num", "0"))
                groups.setdefault(key, []).append(row)
            for order, words in enumerate(groups.values(), start=1):
                words.sort(key=lambda item: int(item.get("left", "0")))
                text = " ".join(item.get("text", "") for item in words)
                x0 = min(int(item.get("left", "0")) for item in words)
                y0 = min(int(item.get("top", "0")) for item in words)
                x1 = max(int(item.get("left", "0")) + int(item.get("width", "0")) for item in words)
                y1 = max(int(item.get("top", "0")) + int(item.get("height", "0")) for item in words)
                confidence = sum(float(item.get("conf", "0")) for item in words) / max(1, len(words)) / 100.0
                result.elements.append(
                    AdapterElement(
                        page=page_number, text=normalize_text(text), bbox=[x0, y0, x1, y1],
                        confidence=max(0.0, min(1.0, confidence)), reading_order=order,
                        metadata={
                            "coordinate_space": "rendered_pixels",
                            "page_width": page_width,
                            "page_height": page_height,
                        },
                    )
                )
        result.document_text = "\n".join(element.text for element in result.elements)
        return result


class PaddleOcrEngine(BaseAdapter):
    name = "paddleocr"
    resource_level = 5
    priority = PADDLE_OCR_PRIORITY
    capabilities = ("ocr", "text", "bbox", "layout", "cjk", "multilingual")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("paddleocr") and module_exists("paddle")
        return AdapterProbe(
            name=self.name, available=available, module_available=available,
            version=package_version("paddleocr"), reason="available" if available else "requires paddleocr, paddlepaddle, and cached models"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        from paddleocr import PaddleOCR  # type: ignore

        result = result_shell(self, self.probe(context))
        language = context.config.environment.get("PADDLE_OCR_LANG", "chinese_cht")
        try:
            engine = PaddleOCR(
                lang=language,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                device=context.config.device,
            )
            api_version = 3
        except TypeError:
            engine = PaddleOCR(lang="ch", use_angle_cls=True, use_gpu=context.config.device != "cpu", show_log=False)
            api_version = 2
        for page_number, image_path in enumerate(render_pdf_pages(context), start=1):
            page_width, page_height = image_dimensions(image_path)
            raw = engine.predict(str(image_path)) if api_version == 3 and hasattr(engine, "predict") else engine.ocr(str(image_path), cls=True)
            if api_version == 3:
                items: list[dict[str, Any]] = []
                for page_result in raw:
                    payload = page_result.json if hasattr(page_result, "json") else page_result
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    root = payload.get("res", payload) if isinstance(payload, dict) else {}
                    texts = root.get("rec_texts", [])
                    scores = root.get("rec_scores", [])
                    boxes = root.get("rec_boxes", root.get("dt_polys", []))
                    for text, score, box in zip(texts, scores, boxes):
                        items.append({"text": text, "score": score, "box": box})
            else:
                items = []
                lines = raw[0] if raw and isinstance(raw, list) else []
                for line in lines or []:
                    if not line or len(line) < 2:
                        continue
                    box, text_score = line[0], line[1]
                    items.append({"text": text_score[0], "score": text_score[1], "box": box})
            for order, item in enumerate(items, start=1):
                box = item.get("box")
                bbox = None
                if box and isinstance(box, (list, tuple)):
                    if len(box) == 4 and all(isinstance(value, (int, float)) for value in box):
                        bbox = [float(value) for value in box]
                    elif len(box) >= 3:
                        xs = [float(point[0]) for point in box]
                        ys = [float(point[1]) for point in box]
                        bbox = [min(xs), min(ys), max(xs), max(ys)]
                result.elements.append(
                    AdapterElement(
                        page=page_number, text=normalize_text(str(item.get("text", ""))), bbox=bbox,
                        confidence=float(item.get("score", 0.75)), reading_order=order,
                        metadata={
                            "coordinate_space": "rendered_pixels",
                            "paddle_api": api_version,
                            "page_width": page_width,
                            "page_height": page_height,
                        },
                    )
                )
        result.document_text = "\n".join(element.text for element in result.elements)
        return result


class PaddlePPStructureEngine(BaseAdapter):
    name = "paddle_ppstructure"
    resource_level = 5
    priority = PADDLE_PPSTRUCTURE_PRIORITY
    capabilities = ("ocr", "layout", "table", "figure", "bbox", "cjk")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("paddleocr") and module_exists("paddle")
        reason = "available" if available else "requires paddleocr, paddlepaddle, and PP-Structure models"
        return AdapterProbe(name=self.name, available=available, module_available=available, version=package_version("paddleocr"), reason=reason)

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        if package_major_version("paddleocr") >= 3:
            try:
                from paddleocr import PPStructureV3  # type: ignore

                pipeline = PPStructureV3(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    device=context.config.device,
                )
                predictions = pipeline.predict(input=str(context.input_path))
                markdown_pages: list[dict[str, Any]] = []
                for page_number, page_result in enumerate(predictions, start=1):
                    result.elements.extend(paddle_v3_elements(page_result, page_number))
                    markdown = getattr(page_result, "markdown", None)
                    if isinstance(markdown, dict):
                        markdown_pages.append(markdown)
                if markdown_pages and hasattr(pipeline, "concatenate_markdown_pages"):
                    result.markdown = str(pipeline.concatenate_markdown_pages(markdown_pages))
                result.document_text = "\n".join(
                    element.text for element in result.elements if element.text
                ) or normalize_text(result.markdown)
                return result
            except ImportError:
                pass

        from PIL import Image
        import numpy as np  # type: ignore
        try:
            from paddleocr import PPStructure  # type: ignore
        except ImportError as exc:
            raise RuntimeError("installed PaddleOCR version does not expose PPStructure") from exc
        engine = PPStructure(show_log=False, image_orientation=True, lang="ch")
        for page_number, image_path in enumerate(render_pdf_pages(context), start=1):
            image = np.array(Image.open(image_path).convert("RGB"))
            predictions = engine(image)
            for order, item in enumerate(predictions, start=1):
                label = str(item.get("type", "text"))
                lowered = label.casefold()
                element_type = "TABLE" if "table" in lowered else ("FIGURE" if "figure" in lowered else "TEXT")
                subtype = "CONTENT" if element_type != "TEXT" else ("H2" if "title" in lowered else "BODY")
                res = item.get("res")
                if isinstance(res, dict):
                    text = normalize_text(str(res.get("html", res.get("text", ""))))
                else:
                    text = normalize_text(str(res or ""))
                result.elements.append(
                    AdapterElement(
                        page=page_number, text=text, bbox=bbox_from_any(item.get("bbox")),
                        element_type=element_type, subtype=subtype, confidence=float(item.get("score", 0.78)),
                        reading_order=order, metadata={"paddle_label": label, "paddle_api": 2},
                    )
                )
        result.document_text = "\n".join(element.text for element in result.elements if element.text)
        return result


class PaddleLayoutEngine(ExternalCommandAdapter):
    name = "paddle_layout"
    resource_level = 5
    priority = PADDLE_LAYOUT_PRIORITY
    capabilities = ("layout", "bbox", "vision", "paddle")
    heavy = True
    module_name = "paddleocr"
    environment_command_key = "GLE_PADDLE_LAYOUT_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        configured = bool(self.configured_command(context))
        installed = module_exists("paddleocr")
        direct_api = installed and package_major_version("paddleocr") >= 3
        available = direct_api or (configured and installed)
        return AdapterProbe(
            name=self.name, available=available, module_available=installed, configured=configured,
            version=package_version("paddleocr"),
            reason="available" if available else "requires PaddleOCR 3.x LayoutDetection or GLE_PADDLE_LAYOUT_COMMAND",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        if package_major_version("paddleocr") >= 3:
            try:
                from paddleocr import LayoutDetection  # type: ignore

                model_name = context.config.environment.get(
                    "PADDLE_LAYOUT_MODEL", "PP-DocLayout-S"
                )
                model = LayoutDetection(model_name=model_name, device=context.config.device)
                for page_number, image_path in enumerate(render_pdf_pages(context), start=1):
                    page_width, page_height = image_dimensions(image_path)
                    predictions = model.predict(str(image_path), batch_size=1, layout_nms=True)
                    for page_result in predictions:
                        root = paddle_result_payload(page_result)
                        for order, item in enumerate(root.get("boxes", []), start=1):
                            if not isinstance(item, dict):
                                continue
                            label = str(item.get("label", "text"))
                            element_type, subtype = paddle_label_contract(label)
                            result.elements.append(
                                AdapterElement(
                                    page=page_number,
                                    bbox=bbox_from_any(item.get("coordinate", item.get("bbox"))),
                                    element_type=element_type,
                                    subtype=subtype,
                                    confidence=float(item.get("score", 0.75)),
                                    reading_order=order,
                                    metadata={
                                        "paddle_label": label,
                                        "coordinate_space": "rendered_pixels",
                                        "paddle_api": 3,
                                        "model": model_name,
                                        "page_width": page_width,
                                        "page_height": page_height,
                                    },
                                )
                            )
                return result
            except ImportError:
                pass

        configured = self.configured_command(context)
        if not configured:
            raise RuntimeError("PaddleOCR 3.x LayoutDetection unavailable; set GLE_PADDLE_LAYOUT_COMMAND")
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        completed = run_command(command_from_template(configured, context.input_path, output_dir), context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        json_path = find_first_text_file(output_dir, [".json", ".jsonl"])
        payload = json.loads(json_path.read_text(encoding="utf-8")) if json_path else json.loads(completed.stdout)
        items = payload.get("elements", payload if isinstance(payload, list) else [])
        for order, item in enumerate(items, start=1):
            label = str(item.get("label", item.get("type", "text")))
            lowered = label.casefold()
            element_type = "TABLE" if "table" in lowered else ("FIGURE" if "figure" in lowered else "TEXT")
            result.elements.append(
                AdapterElement(
                    page=int(item.get("page", 1)), text=normalize_text(item.get("text", "")),
                    bbox=bbox_from_any(item.get("bbox")), element_type=element_type,
                    subtype="CONTENT" if element_type != "TEXT" else "BODY",
                    confidence=float(item.get("confidence", item.get("score", 0.75))), reading_order=order,
                    metadata={"paddle_label": label},
                )
            )
        result.document_text = "\n".join(element.text for element in result.elements if element.text)
        return result


class PaddlePdfEngine(BaseAdapter):
    name = "paddle_pdf_pipeline"
    resource_level = 5
    priority = PADDLE_PDF_PRIORITY
    capabilities = ("pdf", "ocr", "text", "layout", "table", "figure", "paddle")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        installed = module_exists("paddleocr") and module_exists("paddle")
        pdf_input = context.input_path.suffix.casefold() == ".pdf"
        v3_api = package_major_version("paddleocr") >= 3
        available = installed and pdf_input and v3_api
        return AdapterProbe(
            name=self.name, available=available, module_available=installed,
            version=package_version("paddleocr"),
            reason="available" if available else "requires PaddleOCR/PaddlePaddle 3.x PPStructureV3 and PDF input",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        from paddleocr import PPStructureV3  # type: ignore

        result = result_shell(self, self.probe(context))
        pipeline = PPStructureV3(
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
            device=context.config.device,
        )
        predictions = pipeline.predict(input=str(context.input_path))
        markdown_pages: list[dict[str, Any]] = []
        for page_number, page_result in enumerate(predictions, start=1):
            result.elements.extend(paddle_v3_elements(page_result, page_number))
            markdown = getattr(page_result, "markdown", None)
            if isinstance(markdown, dict):
                markdown_pages.append(markdown)
        if markdown_pages:
            result.markdown = str(pipeline.concatenate_markdown_pages(markdown_pages))
            output_dir = context.work_dir / self.name
            output_dir.mkdir(parents=True, exist_ok=True)
            markdown_path = output_dir / f"{context.input_path.stem}.md"
            markdown_path.write_text(result.markdown, encoding="utf-8")
            result.artifacts["markdown"] = str(markdown_path)
        result.document_text = "\n".join(
            element.text for element in result.elements if element.text
        ) or normalize_text(result.markdown)
        return result


class PaddleDetectionEngine(ExternalCommandAdapter):
    name = "paddle_detection"
    resource_level = 5
    priority = PADDLE_DETECTION_PRIORITY
    capabilities = ("layout", "bbox", "vision", "object_detection", "paddle")
    heavy = True
    module_name = "paddledet"
    environment_command_key = "GLE_PADDLE_DETECTION_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        configured = bool(self.configured_command(context))
        installed = module_exists("ppdet") or module_exists("paddledet")
        available = configured and installed
        return AdapterProbe(
            name=self.name, available=available, module_available=installed, configured=configured,
            version=package_version("paddledet"), reason="available" if available else "requires PaddleDetection and GLE_PADDLE_DETECTION_COMMAND"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        completed = run_command(command_from_template(self.configured_command(context) or "", context.input_path, output_dir), context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        json_path = find_first_text_file(output_dir, [".json", ".jsonl"])
        payload = json.loads(json_path.read_text(encoding="utf-8")) if json_path else json.loads(completed.stdout)
        items = payload.get("elements", payload.get("detections", payload if isinstance(payload, list) else []))
        for order, item in enumerate(items, start=1):
            result.elements.append(
                AdapterElement(
                    page=int(item.get("page", 1)), bbox=bbox_from_any(item.get("bbox")),
                    element_type=str(item.get("type", "FIGURE")).upper(), subtype="CONTENT",
                    confidence=float(item.get("score", 0.75)), reading_order=order,
                    metadata={"label": item.get("label")},
                )
            )
        return result


class EasyOcrEngine(BaseAdapter):
    name = "easyocr"
    resource_level = 5
    priority = EASYOCR_PRIORITY
    capabilities = ("ocr", "text", "bbox", "layout", "multilingual")
    heavy = True

    def probe(self, context: AdapterContext) -> AdapterProbe:
        available = module_exists("easyocr") and module_exists("torch")
        return AdapterProbe(
            name=self.name, available=available, module_available=available,
            version=package_version("easyocr"), reason="available" if available else "requires easyocr, torch, and cached models"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        import easyocr  # type: ignore

        result = result_shell(self, self.probe(context))
        languages = context.config.environment.get("EASYOCR_LANGUAGES", "ch_tra,en").split(",")
        reader = easyocr.Reader(languages, gpu=context.config.device != "cpu", download_enabled=context.config.allow_model_downloads)
        for page_number, image_path in enumerate(render_pdf_pages(context), start=1):
            page_width, page_height = image_dimensions(image_path)
            predictions = reader.readtext(str(image_path), detail=1, paragraph=False)
            for order, prediction in enumerate(predictions, start=1):
                polygon, text, confidence = prediction
                xs = [float(point[0]) for point in polygon]
                ys = [float(point[1]) for point in polygon]
                result.elements.append(
                    AdapterElement(
                        page=page_number, text=normalize_text(text), bbox=[min(xs), min(ys), max(xs), max(ys)],
                        confidence=float(confidence), reading_order=order,
                        metadata={
                            "coordinate_space": "rendered_pixels",
                            "page_width": page_width,
                            "page_height": page_height,
                        },
                    )
                )
        result.document_text = "\n".join(element.text for element in result.elements)
        return result


class OcrMyPdfEngine(ExternalCommandAdapter):
    name = "ocrmypdf"
    resource_level = 5
    priority = OCRMYPDF_PRIORITY
    capabilities = ("ocr", "searchable_pdf", "preprocess")
    heavy = True
    binary_name = "ocrmypdf"
    module_name = "ocrmypdf"

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        if context.input_path.suffix.casefold() != ".pdf":
            return self.skip_result(context, STATUS_SKIPPED_POLICY, "OCRmyPDF requires PDF input")
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "searchable.pdf"
        executable = shutil.which("ocrmypdf") or "ocrmypdf"
        languages, missing_languages = resolved_tesseract_languages(context)
        if not languages:
            raise RuntimeError("none of the requested OCRmyPDF/Tesseract languages are installed")
        if missing_languages:
            result.warnings.append(
                "missing OCRmyPDF/Tesseract languages: " + ", ".join(missing_languages)
                + f"; using {languages}"
            )
        command = [
            executable, "--skip-text", "--deskew", "--optimize", "1",
            "--language", languages, str(context.input_path), str(output_path),
        ]
        run_command(command, context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        result.artifacts["searchable_pdf"] = str(output_path)
        if module_exists("fitz"):
            import fitz  # type: ignore

            document = fitz.open(str(output_path))
            try:
                result.document_text = "\n\f\n".join(page.get_text("text") for page in document)
            finally:
                document.close()
        result.elements.append(AdapterElement(page=1, text=result.document_text, confidence=0.82))
        return result


class TranskribusEngine(ExternalCommandAdapter):
    name = "transkribus_core"
    resource_level = 5
    priority = TRANSKRIBUS_PRIORITY
    capabilities = ("ocr", "handwriting", "historical_document", "layout")
    heavy = True
    environment_command_key = "GLE_TRANSKRIBUS_COMMAND"

    def probe(self, context: AdapterContext) -> AdapterProbe:
        configured = bool(self.configured_command(context))
        return AdapterProbe(
            name=self.name, available=configured, configured=configured,
            reason="available" if configured else "set GLE_TRANSKRIBUS_COMMAND for the local Transkribus Core runner"
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = result_shell(self, self.probe(context))
        output_dir = context.work_dir / self.name
        output_dir.mkdir(parents=True, exist_ok=True)
        completed = run_command(command_from_template(self.configured_command(context) or "", context.input_path, output_dir), context.config, timeout_seconds=context.config.heavy_timeout_seconds)
        xml_path = find_first_text_file(output_dir, [".xml", ".json", ".txt"])
        text = xml_path.read_text(encoding="utf-8", errors="replace") if xml_path else completed.stdout
        result.document_text = re.sub(r"<[^>]+>", " ", text)
        result.elements.append(AdapterElement(page=1, text=normalize_text(result.document_text), confidence=0.70))
        if xml_path:
            result.artifacts["output"] = str(xml_path)
        return result


# =============================================================================
# 09. EXTERNAL-CREDENTIAL BACKEND — REGISTERED BUT DISABLED BY DEFAULT
# =============================================================================

class AdobeExtractEngine(BaseAdapter):
    name = "adobe_extract_api"
    resource_level = 9
    priority = ADOBE_EXTRACT_PRIORITY
    capabilities = ("cloud", "text", "table", "figure", "structured_json")

    def probe(self, context: AdapterContext) -> AdapterProbe:
        configured = bool(
            context.config.allow_cloud_backends
            and (context.config.environment.get("ADOBE_PDF_SERVICES_CLIENT_ID") or os.environ.get("ADOBE_PDF_SERVICES_CLIENT_ID"))
            and (context.config.environment.get("ADOBE_PDF_SERVICES_CLIENT_SECRET") or os.environ.get("ADOBE_PDF_SERVICES_CLIENT_SECRET"))
        )
        return AdapterProbe(
            name=self.name, available=False, configured=configured,
            reason="cloud backend is intentionally not executed by the local-only engine; use a separate credentialed plugin",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        raise RuntimeError("Adobe Extract API is outside the local-only execution boundary")


# =============================================================================
# 10. REGISTRY FACTORY
# =============================================================================

def build_all_adapters() -> list[BaseAdapter]:
    adapters: list[BaseAdapter] = [
        PdfPlumberEngine(),
        PyPdfEngine(),
        PopplerEngine(),
        PdfParseNodeEngine(),
        PyMuPdfEngine(),
        PdfMinerEngine(),
        PdfBoxEngine(),
        PdfJsEngine(),
        MuPdfCliEngine(),
        PyMuPdf4LlmEngine(),
        CamelotEngine(),
        TabulaEngine(),
        DoclingEngine(),
        UnstructuredEngine(),
        ApacheTikaEngine(),
        PdfSharpEngine(),
        MarkerEngine(),
        MinerUEngine(),
        LayoutParserEngine(),
        DeepDoctectionEngine(),
        HuriDocsEngine(),
        TableTransformerEngine(),
        TesseractEngine(),
        PaddleOcrEngine(),
        PaddlePPStructureEngine(),
        PaddleLayoutEngine(),
        PaddlePdfEngine(),
        PaddleDetectionEngine(),
        EasyOcrEngine(),
        OcrMyPdfEngine(),
        TranskribusEngine(),
        AdobeExtractEngine(),
    ]
    return sorted(adapters, key=lambda adapter: (adapter.resource_level, adapter.priority, adapter.name))


def adapter_registry() -> dict[str, BaseAdapter]:
    return {adapter.name: adapter for adapter in build_all_adapters()}
