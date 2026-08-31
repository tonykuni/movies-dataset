#!/usr/bin/env python3
"""
GenericLayoutEngine
===================

Generic, local-first PDF/image layout analysis with deterministic geometry,
font/style classification, OCR fallback, table/figure grouping, stable IDs,
reading order, audit outputs, and optional heavyweight backends.

The core remains usable with PyMuPDF alone. Every optional backend is probed
and reported; unavailable engines never silently change the result.
"""

from __future__ import annotations

# =============================================================================
# 01. PARAMETERS — keep user-adjustable settings at the top of the file
# =============================================================================

ENGINE_NAME = "GenericLayoutEngine"
ENGINE_VERSION = "1.0.0"
SCHEMA_VERSION = "GLE-LAYOUT/1.0"

SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}

DEFAULT_DPI = 180
DEFAULT_OCR_MODE = "auto"  # auto | always | never
DEFAULT_OCR_LANGUAGES = "chi_tra+chi_sim+eng"
DEFAULT_MIN_NATIVE_CHARACTERS = 40
DEFAULT_NORMALIZED_BBOX_SCALE = 10_000
DEFAULT_HEADER_ZONE_RATIO = 0.10
DEFAULT_FOOTER_ZONE_RATIO = 0.88
DEFAULT_REPEAT_PAGE_RATIO = 0.60
DEFAULT_END_MATTER_PAGE_COUNT = 3
DEFAULT_BODY_FONT_BIN = 0.25
DEFAULT_MIN_HEADING_CHARACTERS = 2
DEFAULT_MAX_HEADING_CHARACTERS = 120
DEFAULT_TABLE_CAPTION_GAP_RATIO = 0.07
DEFAULT_SOURCE_GAP_RATIO = 0.09
DEFAULT_COLUMN_GAP_RATIO = 0.035
DEFAULT_MAX_COLUMNS = 4
DEFAULT_SAVE_PAGE_IMAGES = True
DEFAULT_SAVE_ANNOTATED_IMAGES = True
DEFAULT_ENABLE_TABLES = True
DEFAULT_ENABLE_BORDERLESS_TABLES = False
DEFAULT_ENABLE_OPTIONAL_BACKENDS = True
DEFAULT_FAIL_CLOSED = False

TYPE_CODES = {
    "TEXT": "TXT",
    "TABLE": "TBL",
    "FIGURE": "FIG",
    "META": "MET",
    "NOISE": "NOI",
}

SUBTYPE_CODES = {
    "H1": "H1",
    "H2": "H2",
    "H3": "H3",
    "BODY": "BDY",
    "BULLET": "BLT",
    "NOTE": "NOT",
    "CAPTION": "CAP",
    "HEADER": "HDR",
    "STUB": "STB",
    "DATA": "DAT",
    "CONTENT": "CNT",
    "SOURCE": "SRC",
    "LEGEND": "LEG",
    "AXIS": "AXS",
    "LABEL": "LBL",
    "PAGE_NUMBER": "PGN",
    "RUNNING_HEADER": "RHD",
    "PAGE_FOOTER": "PFT",
    "END_DISCLAIMER": "END",
    "WATERMARK": "WMK",
    "OCR_ARTIFACT": "OCR",
    "UNKNOWN": "UNK",
}

ZONE_CODES = ("TL", "TC", "TR", "ML", "MC", "MR", "BL", "BC", "BR", "FULL")

HEADING_NUMBER_PATTERN = r"^(?:第[一二三四五六七八九十百\d]+[章节篇部]|[壹貳參肆伍陸柒捌玖拾]+[、.]|(?:\d+\.){1,4}\d*\s*|[A-Z]\.|[IVX]+\.)"
TABLE_CAPTION_PATTERN = r"^\s*(?:表|表格|Table|TABLE|Exhibit|EXHIBIT)\s*[A-Za-z0-9一二三四五六七八九十\.\-]*\s*[:：.、\-]?\s*\S+"
FIGURE_CAPTION_PATTERN = r"^\s*(?:圖|图|Figure|FIGURE|Fig\.?|FIG\.?|Exhibit|EXHIBIT)\s*[A-Za-z0-9一二三四五六七八九十\.\-]*\s*[:：.、\-]?\s*\S+"
SOURCE_PATTERN = r"^\s*(?:資料來源|数据来源|來源|来源|Source|Sources)\s*[:：]"
NOTE_PATTERN = r"^\s*(?:註|注|備註|备注|Note|Notes)\s*[:：]"
PAGE_NUMBER_PATTERN = r"^\s*(?:第\s*)?(?:Page\s*)?[-–—]?\s*\d{1,4}\s*(?:頁|页)?\s*[-–—]?\s*$"
BULLET_PATTERN = r"^\s*(?:[•●▪◦‧·]|[-–—]|\(?[a-zA-Z0-9一二三四五六七八九十]+[.)、])\s+"
DISCLAIMER_KEYWORDS = (
    "免責", "免责声明", "利益衝突", "利益冲突", "分析師聲明", "分析师声明",
    "重要聲明", "重要声明", "法律責任", "投資人應", "投資者應",
    "disclaimer", "important disclosures", "analyst certification", "conflict of interest",
    "not constitute", "investment advice", "legal notice",
)

ANNOTATION_COLORS = {
    "TEXT": "#2f80ed",
    "TABLE": "#27ae60",
    "FIGURE": "#9b51e0",
    "META": "#f2994a",
    "NOISE": "#eb5757",
}

OPTIONAL_BACKEND_SPECS = {
    "docling": {"module": "docling", "binary": None, "role": "document parser"},
    "pymupdf": {"module": "fitz", "binary": None, "role": "native geometry/font core"},
    "pymupdf4llm": {"module": "pymupdf4llm", "binary": None, "role": "reading-order/markdown"},
    "pdfplumber": {"module": "pdfplumber", "binary": None, "role": "geometry/table core"},
    "pdfminer_six": {"module": "pdfminer", "binary": None, "role": "layout consensus"},
    "layoutparser": {"module": "layoutparser", "binary": None, "role": "vision layout"},
    "deepdoctection": {"module": "deepdoctection", "binary": None, "role": "vision/table orchestration"},
    "paddleocr_ppstructure": {"module": "paddleocr", "binary": None, "role": "CJK OCR/layout"},
    "marker": {"module": "marker", "binary": "marker_single", "role": "document reconstruction"},
    "unstructured": {"module": "unstructured", "binary": None, "role": "semantic elements"},
    "huridocs": {"module": "pdf_document_layout_analysis", "binary": None, "role": "VGT layout"},
    "table_transformer": {"module": "transformers", "binary": None, "role": "table structure recognition"},
    "camelot": {"module": "camelot", "binary": None, "role": "geometric tables"},
    "tabula_py": {"module": "tabula", "binary": None, "role": "Java tables"},
    "tesseract": {"module": "pytesseract", "binary": "tesseract", "role": "OCR/TSV/hOCR"},
    "ocrmypdf": {"module": "ocrmypdf", "binary": "ocrmypdf", "role": "searchable PDF OCR"},
    "apache_pdfbox": {"module": None, "binary": "java", "role": "Java PDF structure"},
    "poppler": {"module": None, "binary": "pdftotext", "role": "layout-preserving fallback"},
    "transkribus_core": {"module": "transkribus", "binary": None, "role": "historical document adapter"},
}


# =============================================================================
# 02. IMPORTS
# =============================================================================

import argparse
import csv
import hashlib
import html
import importlib.util
import io
import json
import math
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence


# =============================================================================
# 03. DATA CONTRACTS
# =============================================================================

@dataclass
class EngineConfig:
    dpi: int = DEFAULT_DPI
    ocr_mode: str = DEFAULT_OCR_MODE
    ocr_languages: str = DEFAULT_OCR_LANGUAGES
    min_native_characters: int = DEFAULT_MIN_NATIVE_CHARACTERS
    normalized_bbox_scale: int = DEFAULT_NORMALIZED_BBOX_SCALE
    header_zone_ratio: float = DEFAULT_HEADER_ZONE_RATIO
    footer_zone_ratio: float = DEFAULT_FOOTER_ZONE_RATIO
    repeat_page_ratio: float = DEFAULT_REPEAT_PAGE_RATIO
    end_matter_page_count: int = DEFAULT_END_MATTER_PAGE_COUNT
    body_font_bin: float = DEFAULT_BODY_FONT_BIN
    min_heading_characters: int = DEFAULT_MIN_HEADING_CHARACTERS
    max_heading_characters: int = DEFAULT_MAX_HEADING_CHARACTERS
    table_caption_gap_ratio: float = DEFAULT_TABLE_CAPTION_GAP_RATIO
    source_gap_ratio: float = DEFAULT_SOURCE_GAP_RATIO
    column_gap_ratio: float = DEFAULT_COLUMN_GAP_RATIO
    max_columns: int = DEFAULT_MAX_COLUMNS
    save_page_images: bool = DEFAULT_SAVE_PAGE_IMAGES
    save_annotated_images: bool = DEFAULT_SAVE_ANNOTATED_IMAGES
    enable_tables: bool = DEFAULT_ENABLE_TABLES
    enable_borderless_tables: bool = DEFAULT_ENABLE_BORDERLESS_TABLES
    enable_optional_backends: bool = DEFAULT_ENABLE_OPTIONAL_BACKENDS
    fail_closed: bool = DEFAULT_FAIL_CLOSED

    def validate(self) -> None:
        if self.ocr_mode not in {"auto", "always", "never"}:
            raise ValueError("ocr_mode must be auto, always, or never")
        if self.dpi < 72 or self.dpi > 600:
            raise ValueError("dpi must be between 72 and 600")
        if not 0.0 < self.header_zone_ratio < self.footer_zone_ratio < 1.0:
            raise ValueError("header/footer ratios are invalid")
        if self.max_columns < 1 or self.max_columns > 8:
            raise ValueError("max_columns must be between 1 and 8")


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    def as_list(self) -> list[float]:
        return [round(self.x0, 3), round(self.y0, 3), round(self.x1, 3), round(self.y1, 3)]

    def normalized(self, page_width: float, page_height: float, scale: int) -> list[int]:
        width = max(page_width, 1.0)
        height = max(page_height, 1.0)
        return [
            int(round(max(0.0, min(1.0, self.x0 / width)) * scale)),
            int(round(max(0.0, min(1.0, self.y0 / height)) * scale)),
            int(round(max(0.0, min(1.0, self.x1 / width)) * scale)),
            int(round(max(0.0, min(1.0, self.y1 / height)) * scale)),
        ]

    def contains_center(self, other: "BBox", margin: float = 0.0) -> bool:
        return (
            self.x0 - margin <= other.cx <= self.x1 + margin
            and self.y0 - margin <= other.cy <= self.y1 + margin
        )

    def intersection_ratio(self, other: "BBox") -> float:
        ix0 = max(self.x0, other.x0)
        iy0 = max(self.y0, other.y0)
        ix1 = min(self.x1, other.x1)
        iy1 = min(self.y1, other.y1)
        intersection = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
        return intersection / max(min(self.area, other.area), 1e-9)


@dataclass
class FontProfile:
    size: Optional[float] = None
    name: Optional[str] = None
    weight: Optional[int] = None
    is_bold: Optional[bool] = None
    is_italic: Optional[bool] = None
    color: Optional[str] = None
    source: str = "unknown"


@dataclass
class Relation:
    relation: str
    target_id: str
    confidence: float = 1.0


@dataclass
class LayoutElement:
    page: int
    bbox: BBox
    raw_text: str = ""
    repaired_text: str = ""
    element_type: str = "TEXT"
    subtype: str = "BODY"
    zone: str = "MC"
    source_method: str = "unknown"
    confidence: float = 1.0
    font: FontProfile = field(default_factory=FontProfile)
    metadata: dict[str, Any] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    element_id: str = ""
    source_fingerprint: str = ""
    parent_id: Optional[str] = None
    reading_order: Optional[int] = None
    column_index: Optional[int] = None
    include_in_main_text: bool = True
    include_in_summary: bool = True
    retained_for_audit: bool = True

    def text(self) -> str:
        return self.repaired_text or self.raw_text

    def to_dict(self, page_width: float, page_height: float, config: EngineConfig) -> dict[str, Any]:
        payload = asdict(self)
        payload["bbox_pt"] = self.bbox.as_list()
        payload["bbox_norm"] = self.bbox.normalized(
            page_width, page_height, config.normalized_bbox_scale
        )
        payload.pop("bbox", None)
        return payload


@dataclass
class PageLayout:
    physical_page: int
    width: float
    height: float
    printed_page: Optional[str] = None
    page_id: str = ""
    image_path: Optional[str] = None
    annotated_image_path: Optional[str] = None
    native_character_count: int = 0
    used_ocr: bool = False
    elements: list[LayoutElement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class BackendStatus:
    name: str
    role: str
    python_available: bool
    binary_available: bool
    available: bool
    activated: bool = False
    message: str = ""


@dataclass
class DocumentLayout:
    document_id: str
    filename: str
    file_sha256: str
    schema_version: str
    engine_version: str
    created_utc: str
    body_font_size: Optional[float]
    pages: list[PageLayout]
    backends: list[BackendStatus]
    warnings: list[str] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 04. GENERAL UTILITIES
# =============================================================================

def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash8(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:8].upper()


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\u00ad", "").replace("\u200b", "")
    text = re.sub(r"[ \t\u3000]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return text.strip()


def text_signature(value: str) -> str:
    text = normalize_text(value).casefold()
    text = re.sub(r"\d+", "#", text)
    text = re.sub(r"[^\w\u3400-\u9fff#]+", "", text)
    return text[:240]


def weighted_median(values: Sequence[tuple[float, int]]) -> Optional[float]:
    cleaned = sorted((float(v), max(1, int(w))) for v, w in values if v and v > 0)
    if not cleaned:
        return None
    total = sum(weight for _, weight in cleaned)
    midpoint = total / 2.0
    running = 0
    for value, weight in cleaned:
        running += weight
        if running >= midpoint:
            return value
    return cleaned[-1][0]


def union_bbox(boxes: Iterable[BBox]) -> BBox:
    items = list(boxes)
    if not items:
        return BBox(0.0, 0.0, 0.0, 0.0)
    return BBox(
        min(item.x0 for item in items),
        min(item.y0 for item in items),
        max(item.x1 for item in items),
        max(item.y1 for item in items),
    )


def zone_for_bbox(box: BBox, width: float, height: float) -> str:
    if box.width >= width * 0.78:
        return "FULL"
    x_band = min(2, max(0, int((box.cx / max(width, 1.0)) * 3)))
    y_band = min(2, max(0, int((box.cy / max(height, 1.0)) * 3)))
    return (("T", "M", "B")[y_band] + ("L", "C", "R")[x_band])


def font_weight_from_name(font_name: str, flags: int = 0) -> tuple[int, bool, bool]:
    lowered = (font_name or "").casefold()
    bold = bool(flags & 16) or any(token in lowered for token in ("bold", "black", "heavy", "demi"))
    italic = bool(flags & 2) or any(token in lowered for token in ("italic", "oblique"))
    if "black" in lowered or "heavy" in lowered:
        weight = 900
    elif bold:
        weight = 700
    elif "semibold" in lowered or "demi" in lowered:
        weight = 600
    elif "light" in lowered:
        weight = 300
    else:
        weight = 400
    return weight, bold, italic


def safe_relative_path(path: Optional[Path], base: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def is_supported_input(path: Path) -> bool:
    suffix = path.suffix.casefold()
    return suffix in SUPPORTED_PDF_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS


# =============================================================================
# 05. BACKEND DISCOVERY AND OPTIONAL ADAPTER REGISTRY
# =============================================================================

def probe_backends() -> list[BackendStatus]:
    statuses: list[BackendStatus] = []
    for name, spec in OPTIONAL_BACKEND_SPECS.items():
        module = spec.get("module")
        binary = spec.get("binary")
        python_available = bool(module and importlib.util.find_spec(str(module)))
        binary_available = bool(binary and shutil.which(str(binary)))
        if module and binary:
            available = python_available or binary_available
        elif module:
            available = python_available
        else:
            available = binary_available
        statuses.append(
            BackendStatus(
                name=name,
                role=str(spec["role"]),
                python_available=python_available,
                binary_available=binary_available,
                available=available,
                message="available" if available else "not installed; adapter remains registered",
            )
        )
    return statuses


def backend_map(statuses: Sequence[BackendStatus]) -> dict[str, BackendStatus]:
    return {status.name: status for status in statuses}


# =============================================================================
# 06. NATIVE PDF AND IMAGE EXTRACTION
# =============================================================================

def extract_with_pymupdf(
    input_path: Path,
    output_dir: Path,
    config: EngineConfig,
    statuses: dict[str, BackendStatus],
) -> list[PageLayout]:
    import fitz  # type: ignore

    status = statuses.get("pymupdf")
    if status:
        status.activated = True

    pages: list[PageLayout] = []
    document = fitz.open(str(input_path))
    page_image_dir = output_dir / "pages"
    if config.save_page_images or config.save_annotated_images or config.ocr_mode != "never":
        page_image_dir.mkdir(parents=True, exist_ok=True)

    for page_index, page in enumerate(document, start=1):
        rect = page.rect
        page_layout = PageLayout(physical_page=page_index, width=float(rect.width), height=float(rect.height))
        text_dict = page.get_text("dict", sort=False)
        for block_index, block in enumerate(text_dict.get("blocks", [])):
            block_type = int(block.get("type", 0))
            if block_type == 1:
                raw_bbox = block.get("bbox", (0, 0, 0, 0))
                element = LayoutElement(
                    page=page_index,
                    bbox=BBox(*map(float, raw_bbox)),
                    element_type="FIGURE",
                    subtype="CONTENT",
                    source_method="pymupdf.image_block",
                    confidence=0.98,
                    metadata={"block_index": block_index, "image_ext": block.get("ext")},
                )
                page_layout.elements.append(element)
                continue
            if block_type != 0:
                continue
            for line_index, line in enumerate(block.get("lines", [])):
                spans = [span for span in line.get("spans", []) if normalize_text(str(span.get("text", "")))]
                if not spans:
                    continue
                raw_text = "".join(str(span.get("text", "")) for span in spans)
                repaired_text = normalize_text(raw_text)
                span_boxes = [BBox(*map(float, span.get("bbox", (0, 0, 0, 0)))) for span in spans]
                bbox = union_bbox(span_boxes)
                sized = [(float(span.get("size", 0.0)), len(str(span.get("text", "")))) for span in spans]
                font_size = weighted_median(sized)
                dominant = max(spans, key=lambda item: len(str(item.get("text", ""))))
                font_name = str(dominant.get("font", ""))
                flags = int(dominant.get("flags", 0))
                weight, bold, italic = font_weight_from_name(font_name, flags)
                element = LayoutElement(
                    page=page_index,
                    bbox=bbox,
                    raw_text=raw_text,
                    repaired_text=repaired_text,
                    source_method="pymupdf.native_line",
                    confidence=0.99,
                    font=FontProfile(
                        size=font_size,
                        name=font_name,
                        weight=weight,
                        is_bold=bold,
                        is_italic=italic,
                        color=str(dominant.get("color", "")),
                        source="pdf_font_metrics",
                    ),
                    metadata={
                        "block_index": block_index,
                        "line_index": line_index,
                        "span_count": len(spans),
                    },
                )
                page_layout.elements.append(element)
                page_layout.native_character_count += len(repaired_text)

        if config.save_page_images or config.save_annotated_images or should_ocr(page_layout, config):
            matrix = fitz.Matrix(config.dpi / 72.0, config.dpi / 72.0)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = page_image_dir / f"page_{page_index:04d}.png"
            pixmap.save(str(image_path))
            page_layout.image_path = str(image_path)
        pages.append(page_layout)
    document.close()
    return pages


def extract_image_page(input_path: Path, output_dir: Path, config: EngineConfig) -> list[PageLayout]:
    from PIL import Image, ImageSequence

    pages: list[PageLayout] = []
    page_image_dir = output_dir / "pages"
    page_image_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        for page_index, frame in enumerate(ImageSequence.Iterator(image), start=1):
            rgb = frame.convert("RGB")
            page_path = page_image_dir / f"page_{page_index:04d}.png"
            rgb.save(page_path)
            width_px, height_px = rgb.size
            width_pt = width_px * 72.0 / config.dpi
            height_pt = height_px * 72.0 / config.dpi
            pages.append(
                PageLayout(
                    physical_page=page_index,
                    width=width_pt,
                    height=height_pt,
                    image_path=str(page_path),
                )
            )
    return pages


def should_ocr(page: PageLayout, config: EngineConfig) -> bool:
    if config.ocr_mode == "always":
        return True
    if config.ocr_mode == "never":
        return False
    return page.native_character_count < config.min_native_characters


# =============================================================================
# 07. OCR FALLBACK
# =============================================================================

def run_tesseract_tsv(
    image_path: Path,
    page: PageLayout,
    config: EngineConfig,
    statuses: dict[str, BackendStatus],
) -> list[LayoutElement]:
    executable = shutil.which("tesseract")
    if not executable:
        page.warnings.append("OCR requested but tesseract executable is unavailable")
        return []
    status = statuses.get("tesseract")
    if status:
        status.activated = True
    command = [executable, str(image_path), "stdout", "-l", config.ocr_languages, "tsv"]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
    except subprocess.CalledProcessError as exc:
        fallback_command = [executable, str(image_path), "stdout", "-l", "eng", "tsv"]
        page.warnings.append(f"configured OCR languages failed; falling back to eng: {exc.stderr.strip()[:200]}")
        try:
            completed = subprocess.run(fallback_command, check=True, capture_output=True, text=True, timeout=300)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as fallback_exc:
            page.warnings.append(f"tesseract failed: {fallback_exc}")
            return []
    except subprocess.TimeoutExpired:
        page.warnings.append("tesseract timed out")
        return []

    from PIL import Image

    with Image.open(image_path) as image:
        image_width, image_height = image.size
    x_scale = page.width / max(image_width, 1)
    y_scale = page.height / max(image_height, 1)

    reader = csv.DictReader(io.StringIO(completed.stdout), delimiter="\t")
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in reader:
        text = normalize_text(row.get("text", ""))
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            confidence = -1.0
        if not text or confidence < 0:
            continue
        key = (row.get("block_num", "0"), row.get("par_num", "0"), row.get("line_num", "0"))
        grouped[key].append(row)

    elements: list[LayoutElement] = []
    for key, words in grouped.items():
        words.sort(key=lambda item: int(item.get("left", "0")))
        raw_text = " ".join(item.get("text", "") for item in words)
        x0 = min(int(item.get("left", "0")) for item in words) * x_scale
        y0 = min(int(item.get("top", "0")) for item in words) * y_scale
        x1 = max(int(item.get("left", "0")) + int(item.get("width", "0")) for item in words) * x_scale
        y1 = max(int(item.get("top", "0")) + int(item.get("height", "0")) for item in words) * y_scale
        confidences = [max(0.0, float(item.get("conf", "0"))) for item in words]
        font_size = max(1.0, (y1 - y0) * 0.78)
        elements.append(
            LayoutElement(
                page=page.physical_page,
                bbox=BBox(x0, y0, x1, y1),
                raw_text=raw_text,
                repaired_text=normalize_text(raw_text),
                source_method="tesseract.tsv_line",
                confidence=min(1.0, statistics.fmean(confidences) / 100.0),
                font=FontProfile(size=font_size, weight=400, source="ocr_bbox_estimate"),
                metadata={"ocr_line_key": list(key), "font_size_is_estimated": True},
            )
        )
    page.used_ocr = bool(elements)
    return elements


def merge_native_and_ocr(page: PageLayout, ocr_elements: Sequence[LayoutElement]) -> None:
    if not page.elements:
        page.elements.extend(ocr_elements)
        return
    for candidate in ocr_elements:
        duplicate = False
        candidate_signature = text_signature(candidate.text())
        for existing in page.elements:
            if existing.bbox.intersection_ratio(candidate.bbox) >= 0.70:
                if candidate_signature and candidate_signature == text_signature(existing.text()):
                    duplicate = True
                    existing.metadata.setdefault("consensus_sources", []).append("tesseract")
                    existing.confidence = max(existing.confidence, candidate.confidence)
                    break
        if not duplicate:
            page.elements.append(candidate)


# =============================================================================
# 08. TABLE GEOMETRY
# =============================================================================

def enrich_tables_with_pdfplumber(
    input_path: Path,
    pages: list[PageLayout],
    config: EngineConfig,
    statuses: dict[str, BackendStatus],
) -> None:
    if not config.enable_tables or input_path.suffix.casefold() != ".pdf":
        return
    if not importlib.util.find_spec("pdfplumber"):
        for page in pages:
            page.warnings.append("pdfplumber unavailable; geometric table detection skipped")
        return
    import pdfplumber  # type: ignore

    status = statuses.get("pdfplumber")
    if status:
        status.activated = True
    settings_variants = [
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
    ]
    if config.enable_borderless_tables:
        settings_variants.append(
            {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "min_words_vertical": 3,
                "min_words_horizontal": 2,
            }
        )
    try:
        with pdfplumber.open(str(input_path)) as pdf:
            for page_index, pdf_page in enumerate(pdf.pages):
                if page_index >= len(pages):
                    break
                page_layout = pages[page_index]
                detected: list[Any] = []
                for strategy_index, settings in enumerate(settings_variants):
                    if strategy_index > 0 and detected:
                        break
                    try:
                        candidates = pdf_page.find_tables(table_settings=settings)
                    except Exception as exc:  # backend variations must not abort core
                        page_layout.warnings.append(f"pdfplumber table strategy failed: {exc}")
                        continue
                    for candidate in candidates:
                        bbox = BBox(*map(float, candidate.bbox))
                        if bbox.area <= 0:
                            continue
                        if strategy_index > 0 and (
                            bbox.height > page_layout.height * 0.58
                            or bbox.width > page_layout.width * 0.96
                        ):
                            continue
                        if any(bbox.intersection_ratio(BBox(*map(float, item.bbox))) > 0.88 for item in detected):
                            continue
                        detected.append(candidate)

                for table_index, table in enumerate(detected, start=1):
                    table_bbox = BBox(*map(float, table.bbox))
                    parent = LayoutElement(
                        page=page_layout.physical_page,
                        bbox=table_bbox,
                        element_type="TABLE",
                        subtype="CONTENT",
                        source_method="pdfplumber.find_tables",
                        confidence=0.90,
                        metadata={"table_index": table_index},
                    )
                    page_layout.elements.append(parent)
                    try:
                        rows = getattr(table, "rows", [])
                        for row_index, row in enumerate(rows, start=1):
                            cells = getattr(row, "cells", [])
                            for column_index, cell in enumerate(cells, start=1):
                                if not cell:
                                    continue
                                cell_bbox = BBox(*map(float, cell))
                                try:
                                    cell_text = normalize_text(pdf_page.crop(cell).extract_text() or "")
                                except Exception:
                                    cell_text = ""
                                subtype = "HEADER" if row_index == 1 else ("STUB" if column_index == 1 else "DATA")
                                page_layout.elements.append(
                                    LayoutElement(
                                        page=page_layout.physical_page,
                                        bbox=cell_bbox,
                                        raw_text=cell_text,
                                        repaired_text=cell_text,
                                        element_type="TABLE",
                                        subtype=subtype,
                                        source_method="pdfplumber.table_cell",
                                        confidence=0.88,
                                        metadata={
                                            "table_index": table_index,
                                            "row": row_index,
                                            "column": column_index,
                                            "temporary_parent_bbox": table_bbox.as_list(),
                                        },
                                    )
                                )
                    except Exception as exc:
                        page_layout.warnings.append(f"table cell extraction failed: {exc}")
    except Exception as exc:
        for page in pages:
            page.warnings.append(f"pdfplumber document enrichment failed: {exc}")


# =============================================================================
# 09. FONT, REPETITION, AND SEMANTIC CLASSIFICATION
# =============================================================================

def estimate_body_font_size(pages: Sequence[PageLayout], config: EngineConfig) -> Optional[float]:
    histogram: Counter[float] = Counter()
    for page in pages:
        for element in page.elements:
            if element.element_type != "TEXT" or not element.text() or not element.font.size:
                continue
            y_ratio = element.bbox.cy / max(page.height, 1.0)
            if y_ratio < config.header_zone_ratio or y_ratio > config.footer_zone_ratio:
                continue
            binned = round(element.font.size / config.body_font_bin) * config.body_font_bin
            histogram[binned] += max(1, len(element.text()))
    if not histogram:
        values = [
            (element.font.size, len(element.text()))
            for page in pages
            for element in page.elements
            if element.font.size and element.text() and element.element_type == "TEXT"
        ]
        return weighted_median(values)
    return float(histogram.most_common(1)[0][0])


def repeated_margin_signatures(
    pages: Sequence[PageLayout], config: EngineConfig
) -> tuple[set[str], set[str]]:
    header_pages: dict[str, set[int]] = defaultdict(set)
    footer_pages: dict[str, set[int]] = defaultdict(set)
    for page in pages:
        for element in page.elements:
            if not element.text() or element.element_type != "TEXT":
                continue
            signature = text_signature(element.text())
            if len(signature) < 3:
                continue
            ratio = element.bbox.cy / max(page.height, 1.0)
            if ratio <= config.header_zone_ratio:
                header_pages[signature].add(page.physical_page)
            elif ratio >= config.footer_zone_ratio:
                footer_pages[signature].add(page.physical_page)
    threshold = max(2, math.ceil(len(pages) * config.repeat_page_ratio))
    return (
        {key for key, page_numbers in header_pages.items() if len(page_numbers) >= threshold},
        {key for key, page_numbers in footer_pages.items() if len(page_numbers) >= threshold},
    )


def heading_score(element: LayoutElement, page: PageLayout, body_font_size: Optional[float]) -> float:
    text = element.text()
    if not text or not body_font_size or not element.font.size:
        return 0.0
    ratio = element.font.size / max(body_font_size, 0.1)
    size_score = min(1.0, max(0.0, (ratio - 1.0) / 0.65))
    weight_score = 1.0 if element.font.is_bold else (0.45 if (element.font.weight or 400) >= 600 else 0.0)
    short_score = 1.0 if len(text) <= 45 else max(0.0, 1.0 - (len(text) - 45) / 100.0)
    semantic_score = 1.0 if re.match(HEADING_NUMBER_PATTERN, text, re.IGNORECASE) else 0.0
    punctuation_score = 1.0 if not re.search(r"[。！？.!?]\s*$", text) else 0.0
    top_score = 1.0 if element.bbox.y0 <= page.height * 0.22 else 0.4
    return (
        0.30 * size_score
        + 0.20 * weight_score
        + 0.15 * short_score
        + 0.15 * semantic_score
        + 0.10 * punctuation_score
        + 0.10 * top_score
    )


def estimate_heading_levels(
    pages: Sequence[PageLayout], body_font_size: Optional[float], config: EngineConfig
) -> list[float]:
    if not body_font_size:
        return []
    candidates: Counter[float] = Counter()
    for page in pages:
        for element in page.elements:
            text = element.text()
            if (
                element.element_type != "TEXT"
                or not element.font.size
                or not config.min_heading_characters <= len(text) <= config.max_heading_characters
                or element.font.size < body_font_size * 1.04
            ):
                continue
            if not element.font.is_bold and not re.match(HEADING_NUMBER_PATTERN, text, re.IGNORECASE):
                continue
            binned = round(element.font.size / config.body_font_bin) * config.body_font_bin
            candidates[binned] += 1
    return sorted(candidates, reverse=True)[:3]


def classify_elements(
    pages: list[PageLayout], body_font_size: Optional[float], config: EngineConfig
) -> None:
    repeated_headers, repeated_footers = repeated_margin_signatures(pages, config)
    heading_levels = estimate_heading_levels(pages, body_font_size, config)
    page_count = len(pages)
    end_start = max(1, page_count - config.end_matter_page_count + 1)

    for page in pages:
        for element in page.elements:
            element.zone = zone_for_bbox(element.bbox, page.width, page.height)
            if element.element_type != "TEXT":
                continue
            text = element.text()
            signature = text_signature(text)
            y_ratio = element.bbox.cy / max(page.height, 1.0)
            font_ratio = (element.font.size / body_font_size) if body_font_size and element.font.size else 1.0
            lowered = text.casefold()

            if re.match(PAGE_NUMBER_PATTERN, text, re.IGNORECASE) and (
                y_ratio >= config.footer_zone_ratio or y_ratio <= config.header_zone_ratio
            ):
                element.element_type = "META"
                element.subtype = "PAGE_NUMBER"
                element.include_in_main_text = False
                element.include_in_summary = False
                page.printed_page = re.sub(r"\D", "", text) or text
                continue
            if signature in repeated_headers:
                element.element_type = "META"
                element.subtype = "RUNNING_HEADER"
                element.include_in_main_text = False
                element.include_in_summary = False
                continue
            if signature in repeated_footers or (
                y_ratio >= config.footer_zone_ratio and font_ratio <= 0.88 and len(text) <= 260
            ):
                element.element_type = "NOISE"
                element.subtype = "PAGE_FOOTER"
                element.include_in_main_text = False
                element.include_in_summary = False
                continue
            disclaimer_hits = sum(1 for keyword in DISCLAIMER_KEYWORDS if keyword in lowered)
            if page.physical_page >= end_start and disclaimer_hits and font_ratio <= 1.0:
                element.element_type = "NOISE"
                element.subtype = "END_DISCLAIMER"
                element.include_in_main_text = False
                element.include_in_summary = False
                continue
            if re.match(SOURCE_PATTERN, text, re.IGNORECASE):
                element.subtype = "SOURCE"
                element.include_in_main_text = False
                continue
            if re.match(TABLE_CAPTION_PATTERN, text, re.IGNORECASE):
                element.element_type = "TABLE"
                element.subtype = "CAPTION"
                continue
            if re.match(FIGURE_CAPTION_PATTERN, text, re.IGNORECASE):
                element.element_type = "FIGURE"
                element.subtype = "CAPTION"
                continue
            if re.match(NOTE_PATTERN, text, re.IGNORECASE):
                element.subtype = "NOTE"
                continue
            score = heading_score(element, page, body_font_size)
            if config.min_heading_characters <= len(text) <= config.max_heading_characters:
                matched_level: Optional[int] = None
                if element.font.size and heading_levels:
                    distances = [abs(element.font.size - level) for level in heading_levels]
                    nearest = min(range(len(distances)), key=distances.__getitem__)
                    if distances[nearest] <= max(config.body_font_bin, heading_levels[nearest] * 0.06):
                        matched_level = nearest + 1
                if matched_level and score >= 0.43:
                    element.subtype = f"H{min(3, matched_level)}"
                elif font_ratio >= 1.50 and score >= 0.58:
                    element.subtype = "H1"
                elif font_ratio >= 1.25 and score >= 0.50:
                    element.subtype = "H2"
                elif font_ratio >= 1.05 and score >= 0.43 and (
                    bool(element.font.is_bold) or bool(re.match(HEADING_NUMBER_PATTERN, text, re.IGNORECASE))
                ):
                    element.subtype = "H3"
                elif re.match(BULLET_PATTERN, text):
                    element.subtype = "BULLET"
                else:
                    element.subtype = "BODY"
            else:
                element.subtype = "BODY"


# =============================================================================
# 10. CONTAINMENT, CAPTION/SOURCE BINDING, AND READING ORDER
# =============================================================================

def attach_contained_elements(page: PageLayout) -> None:
    parents = [
        element for element in page.elements
        if (element.element_type, element.subtype) in {("TABLE", "CONTENT"), ("FIGURE", "CONTENT")}
    ]
    children = [element for element in page.elements if element not in parents]
    for child in children:
        candidates = [
            parent for parent in parents
            if parent.bbox.contains_center(child.bbox, margin=1.5)
            and parent.bbox.intersection_ratio(child.bbox) >= 0.35
        ]
        if not candidates:
            continue
        parent = min(candidates, key=lambda item: item.bbox.area)
        child.metadata["temporary_parent_ref"] = id(parent)
        if parent.element_type == "TABLE" and child.element_type == "TEXT":
            child.element_type = "TABLE"
            child.subtype = "HEADER" if child.bbox.cy <= parent.bbox.y0 + parent.bbox.height * 0.18 else "DATA"
        elif parent.element_type == "FIGURE" and child.element_type == "TEXT":
            child.element_type = "FIGURE"
            child.subtype = "LABEL"


def bind_captions_and_sources(page: PageLayout, config: EngineConfig) -> None:
    parents = [
        element for element in page.elements
        if (element.element_type, element.subtype) in {("TABLE", "CONTENT"), ("FIGURE", "CONTENT")}
    ]
    candidates = [
        element for element in page.elements
        if element.subtype in {"CAPTION", "SOURCE", "NOTE"}
    ]
    for candidate in candidates:
        best_parent: Optional[LayoutElement] = None
        best_distance = float("inf")
        for parent in parents:
            horizontal_overlap = max(
                0.0,
                min(candidate.bbox.x1, parent.bbox.x1) - max(candidate.bbox.x0, parent.bbox.x0),
            )
            overlap_ratio = horizontal_overlap / max(min(candidate.bbox.width, parent.bbox.width), 1.0)
            if overlap_ratio < 0.20:
                continue
            if candidate.subtype == "CAPTION":
                distance = parent.bbox.y0 - candidate.bbox.y1
                allowed = page.height * config.table_caption_gap_ratio
                if not (-2.0 <= distance <= allowed):
                    continue
            else:
                distance = candidate.bbox.y0 - parent.bbox.y1
                allowed = page.height * config.source_gap_ratio
                if not (-2.0 <= distance <= allowed):
                    continue
            if abs(distance) < best_distance:
                best_distance = abs(distance)
                best_parent = parent
        if best_parent:
            candidate.metadata["temporary_parent_ref"] = id(best_parent)
            if candidate.subtype == "SOURCE":
                candidate.element_type = best_parent.element_type


def deduplicate_table_text(page: PageLayout) -> None:
    cells = [element for element in page.elements if element.source_method == "pdfplumber.table_cell"]
    if not cells:
        return
    retained: list[LayoutElement] = []
    for element in page.elements:
        if element.source_method not in {"pymupdf.native_line", "tesseract.tsv_line"}:
            retained.append(element)
            continue
        signature = text_signature(element.text())
        duplicate = any(
            cell.bbox.intersection_ratio(element.bbox) >= 0.65
            and signature
            and signature == text_signature(cell.text())
            for cell in cells
        )
        if not duplicate:
            retained.append(element)
    page.elements = retained


def detect_column_boundaries(elements: Sequence[LayoutElement], page: PageLayout, config: EngineConfig) -> list[float]:
    candidates = [
        element for element in elements
        if element.include_in_main_text
        and element.bbox.width < page.width * 0.72
        and element.element_type in {"TEXT", "TABLE", "FIGURE"}
    ]
    if len(candidates) < 6:
        return []
    bins = 120
    occupancy = [0] * bins
    for element in candidates:
        start = max(0, min(bins - 1, int(element.bbox.x0 / max(page.width, 1.0) * bins)))
        end = max(0, min(bins - 1, int(element.bbox.x1 / max(page.width, 1.0) * bins)))
        for index in range(start, end + 1):
            occupancy[index] += 1
    zero_runs: list[tuple[int, int]] = []
    run_start: Optional[int] = None
    for index, count in enumerate(occupancy + [1]):
        if count == 0 and run_start is None:
            run_start = index
        elif count != 0 and run_start is not None:
            if index - run_start >= max(2, int(config.column_gap_ratio * bins)):
                zero_runs.append((run_start, index - 1))
            run_start = None
    boundaries = [((start + end) / 2.0) / bins * page.width for start, end in zero_runs]
    boundaries = [value for value in boundaries if page.width * 0.12 < value < page.width * 0.88]
    if len(boundaries) >= config.max_columns:
        boundaries = sorted(boundaries, key=lambda value: abs(value - page.width / 2.0))[: config.max_columns - 1]
    return sorted(boundaries)


def assign_reading_order(page: PageLayout, config: EngineConfig) -> None:
    boundaries = detect_column_boundaries(page.elements, page, config)
    for element in page.elements:
        if element.bbox.width >= page.width * 0.72:
            element.column_index = -1
        else:
            element.column_index = sum(1 for boundary in boundaries if element.bbox.cx > boundary)

    anchors = sorted(
        [element for element in page.elements if element.column_index == -1],
        key=lambda item: (item.bbox.y0, item.bbox.x0),
    )
    ordered: list[LayoutElement] = []
    lower_y = -1.0
    for anchor in anchors + [None]:
        upper_y = anchor.bbox.y0 if anchor is not None else page.height + 1.0
        band = [
            element for element in page.elements
            if element.column_index != -1
            and lower_y <= element.bbox.cy < upper_y
            and element not in ordered
        ]
        band.sort(key=lambda item: (item.column_index or 0, item.bbox.y0, item.bbox.x0))
        ordered.extend(band)
        if anchor is not None:
            ordered.append(anchor)
            lower_y = anchor.bbox.y1
    leftovers = [element for element in page.elements if element not in ordered]
    leftovers.sort(key=lambda item: (item.bbox.y0, item.bbox.x0))
    ordered.extend(leftovers)
    for order, element in enumerate(ordered, start=1):
        element.reading_order = order


def assign_ids(document_id: str, pages: list[PageLayout], config: EngineConfig) -> None:
    temporary_to_element: dict[int, LayoutElement] = {}
    for page in pages:
        page.page_id = f"{document_id}-P{page.physical_page:04d}"
        counters: Counter[tuple[str, str, str]] = Counter()
        for element in sorted(page.elements, key=lambda item: item.reading_order or 10**9):
            element.zone = zone_for_bbox(element.bbox, page.width, page.height)
            type_code = TYPE_CODES.get(element.element_type, "UNK")
            subtype_code = SUBTYPE_CODES.get(element.subtype, "UNK")
            key = (element.zone, type_code, subtype_code)
            counters[key] += 1
            element.element_id = (
                f"{page.page_id}-{element.zone}-{type_code}-{subtype_code}-{counters[key]:03d}"
            )
            bbox_norm = element.bbox.normalized(page.width, page.height, config.normalized_bbox_scale)
            fingerprint_seed = json.dumps(
                [document_id, page.physical_page, bbox_norm, element.raw_text, element.source_method],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            element.source_fingerprint = hash8(fingerprint_seed)
            temporary_to_element[id(element)] = element

    for page in pages:
        for element in page.elements:
            temp_ref = element.metadata.pop("temporary_parent_ref", None)
            if temp_ref and temp_ref in temporary_to_element:
                parent = temporary_to_element[temp_ref]
                element.parent_id = parent.element_id
                relation_name = {
                    "CAPTION": "CAPTION_OF",
                    "SOURCE": "SOURCE_OF",
                    "HEADER": "HEADER_OF",
                }.get(element.subtype, "PART_OF")
                element.relations.append(Relation(relation_name, parent.element_id, 0.95))


# =============================================================================
# 11. ANNOTATED PAGE RENDERING
# =============================================================================

def render_annotations(pages: list[PageLayout], output_dir: Path, config: EngineConfig) -> None:
    if not config.save_annotated_images:
        return
    from PIL import Image, ImageColor, ImageDraw, ImageFont

    annotation_dir = output_dir / "annotated"
    annotation_dir.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for page in pages:
        if not page.image_path or not Path(page.image_path).exists():
            continue
        with Image.open(page.image_path) as source:
            image = source.convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        x_scale = image.width / max(page.width, 1.0)
        y_scale = image.height / max(page.height, 1.0)
        for element in page.elements:
            color_hex = ANNOTATION_COLORS.get(element.element_type, "#828282")
            red, green, blue = ImageColor.getrgb(color_hex)
            coords = (
                int(element.bbox.x0 * x_scale),
                int(element.bbox.y0 * y_scale),
                int(element.bbox.x1 * x_scale),
                int(element.bbox.y1 * y_scale),
            )
            draw.rectangle(coords, outline=(red, green, blue, 230), width=2)
            label = f"{element.element_type}.{element.subtype} #{element.reading_order or 0}"
            label_x = max(0, coords[0])
            label_y = max(0, coords[1] - 12)
            text_box = draw.textbbox((label_x, label_y), label, font=font)
            draw.rectangle(text_box, fill=(red, green, blue, 205))
            draw.text((label_x, label_y), label, fill=(255, 255, 255, 255), font=font)
        destination = annotation_dir / f"page_{page.physical_page:04d}_annotated.png"
        image.save(destination)
        page.annotated_image_path = str(destination)


# =============================================================================
# 12. OUTPUTS
# =============================================================================

def collect_statistics(document: DocumentLayout) -> dict[str, Any]:
    elements = [element for page in document.pages for element in page.elements]
    type_counts = Counter(element.element_type for element in elements)
    subtype_counts = Counter(f"{element.element_type}.{element.subtype}" for element in elements)
    return {
        "page_count": len(document.pages),
        "element_count": len(elements),
        "type_counts": dict(sorted(type_counts.items())),
        "subtype_counts": dict(sorted(subtype_counts.items())),
        "ocr_page_count": sum(1 for page in document.pages if page.used_ocr),
        "warning_count": len(document.warnings) + sum(len(page.warnings) for page in document.pages),
    }


def document_to_dict(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "file_sha256": document.file_sha256,
        "schema_version": document.schema_version,
        "engine_version": document.engine_version,
        "created_utc": document.created_utc,
        "body_font_size": document.body_font_size,
        "backends": [asdict(status) for status in document.backends],
        "warnings": document.warnings,
        "statistics": document.statistics,
        "pages": [
            {
                "physical_page": page.physical_page,
                "printed_page": page.printed_page,
                "page_id": page.page_id,
                "width": page.width,
                "height": page.height,
                "image_path": safe_relative_path(Path(page.image_path), output_dir) if page.image_path else None,
                "annotated_image_path": safe_relative_path(Path(page.annotated_image_path), output_dir)
                if page.annotated_image_path else None,
                "native_character_count": page.native_character_count,
                "used_ocr": page.used_ocr,
                "warnings": page.warnings,
                "elements": [element.to_dict(page.width, page.height, config) for element in page.elements],
            }
            for page in document.pages
        ],
    }


def flatten_elements(document: DocumentLayout, config: EngineConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in document.pages:
        for element in page.elements:
            row = element.to_dict(page.width, page.height, config)
            row["document_id"] = document.document_id
            row["page_id"] = page.page_id
            row["physical_page"] = page.physical_page
            row["printed_page"] = page.printed_page
            row["font_size"] = element.font.size
            row["font_name"] = element.font.name
            row["font_weight"] = element.font.weight
            row["is_bold"] = element.font.is_bold
            row["is_italic"] = element.font.is_italic
            row["bbox_pt"] = json.dumps(row["bbox_pt"], ensure_ascii=False)
            row["bbox_norm"] = json.dumps(row["bbox_norm"], ensure_ascii=False)
            row["metadata"] = json.dumps(element.metadata, ensure_ascii=False, sort_keys=True)
            row["relations"] = json.dumps([asdict(relation) for relation in element.relations], ensure_ascii=False)
            row.pop("font", None)
            rows.append(row)
    return rows


def export_json(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> Path:
    destination = output_dir / "layout_document.json"
    destination.write_text(
        json.dumps(document_to_dict(document, output_dir, config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def export_jsonl(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> Path:
    destination = output_dir / "layout_elements.jsonl"
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for row in flatten_elements(document, config):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return destination


def export_csv(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> Path:
    destination = output_dir / "layout_elements.csv"
    rows = flatten_elements(document, config)
    if not rows:
        destination.write_text("", encoding="utf-8-sig")
        return destination
    fieldnames = list(rows[0].keys())
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return destination


def export_sqlite(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> Path:
    destination = output_dir / "layout.sqlite"
    if destination.exists():
        destination.unlink()
    connection = sqlite3.connect(destination)
    try:
        connection.execute(
            """
            CREATE TABLE documents (
                document_id TEXT PRIMARY KEY, filename TEXT, file_sha256 TEXT,
                schema_version TEXT, engine_version TEXT, created_utc TEXT,
                body_font_size REAL, statistics_json TEXT, warnings_json TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE pages (
                page_id TEXT PRIMARY KEY, document_id TEXT, physical_page INTEGER,
                printed_page TEXT, width REAL, height REAL, native_character_count INTEGER,
                used_ocr INTEGER, image_path TEXT, annotated_image_path TEXT, warnings_json TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE elements (
                element_id TEXT PRIMARY KEY, source_fingerprint TEXT, page_id TEXT,
                document_id TEXT, physical_page INTEGER, printed_page TEXT,
                reading_order INTEGER, column_index INTEGER, zone TEXT,
                element_type TEXT, subtype TEXT, parent_id TEXT,
                raw_text TEXT, repaired_text TEXT, bbox_pt_json TEXT, bbox_norm_json TEXT,
                font_size REAL, font_name TEXT, font_weight INTEGER,
                is_bold INTEGER, is_italic INTEGER, source_method TEXT,
                confidence REAL, include_in_main_text INTEGER, include_in_summary INTEGER,
                retained_for_audit INTEGER, metadata_json TEXT, relations_json TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                document.document_id, document.filename, document.file_sha256,
                document.schema_version, document.engine_version, document.created_utc,
                document.body_font_size, json.dumps(document.statistics, ensure_ascii=False),
                json.dumps(document.warnings, ensure_ascii=False),
            ),
        )
        for page in document.pages:
            connection.execute(
                "INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    page.page_id, document.document_id, page.physical_page, page.printed_page,
                    page.width, page.height, page.native_character_count, int(page.used_ocr),
                    page.image_path, page.annotated_image_path,
                    json.dumps(page.warnings, ensure_ascii=False),
                ),
            )
            for element in page.elements:
                connection.execute(
                    "INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        element.element_id, element.source_fingerprint, page.page_id,
                        document.document_id, page.physical_page, page.printed_page,
                        element.reading_order, element.column_index, element.zone,
                        element.element_type, element.subtype, element.parent_id,
                        element.raw_text, element.repaired_text,
                        json.dumps(element.bbox.as_list()),
                        json.dumps(element.bbox.normalized(page.width, page.height, config.normalized_bbox_scale)),
                        element.font.size, element.font.name, element.font.weight,
                        None if element.font.is_bold is None else int(element.font.is_bold),
                        None if element.font.is_italic is None else int(element.font.is_italic),
                        element.source_method, element.confidence,
                        int(element.include_in_main_text), int(element.include_in_summary),
                        int(element.retained_for_audit),
                        json.dumps(element.metadata, ensure_ascii=False, sort_keys=True),
                        json.dumps([asdict(relation) for relation in element.relations], ensure_ascii=False),
                    ),
                )
        connection.execute("CREATE INDEX idx_elements_page_order ON elements(page_id, reading_order)")
        connection.execute("CREATE INDEX idx_elements_type ON elements(element_type, subtype)")
        connection.execute("CREATE INDEX idx_elements_parent ON elements(parent_id)")
        connection.commit()
    finally:
        connection.close()
    return destination


def export_parquet_if_available(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> Optional[Path]:
    if not importlib.util.find_spec("pandas") or not importlib.util.find_spec("pyarrow"):
        return None
    import pandas as pd  # type: ignore

    destination = output_dir / "layout_elements.parquet"
    pd.DataFrame(flatten_elements(document, config)).to_parquet(destination, index=False)
    return destination


def export_html(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> Path:
    destination = output_dir / "layout_report.html"
    stats = document.statistics
    type_cards = "".join(
        f'<div class="card"><b>{html.escape(key)}</b><span>{value}</span></div>'
        for key, value in stats.get("type_counts", {}).items()
    )
    backend_rows = "".join(
        "<tr>"
        f"<td>{html.escape(status.name)}</td><td>{html.escape(status.role)}</td>"
        f"<td>{'Yes' if status.available else 'No'}</td><td>{'Yes' if status.activated else 'No'}</td>"
        f"<td>{html.escape(status.message)}</td></tr>"
        for status in document.backends
    )
    page_sections: list[str] = []
    for page in document.pages:
        image_path = page.annotated_image_path or page.image_path
        image_html = ""
        if image_path:
            relative = safe_relative_path(Path(image_path), output_dir)
            image_html = f'<img loading="lazy" src="{html.escape(relative or "")}" alt="Page {page.physical_page}">'
        rows = "".join(
            "<tr>"
            f"<td>{element.reading_order}</td><td>{html.escape(element.zone)}</td>"
            f"<td>{html.escape(element.element_type)}</td><td>{html.escape(element.subtype)}</td>"
            f"<td>{html.escape(element.text()[:220])}</td><td>{element.confidence:.2f}</td>"
            f"<td><code>{html.escape(element.element_id)}</code></td></tr>"
            for element in sorted(page.elements, key=lambda item: item.reading_order or 10**9)
        )
        page_sections.append(
            f"<section><h2>Page {page.physical_page}</h2>{image_html}"
            f"<table><thead><tr><th>Order</th><th>Zone</th><th>Type</th><th>Subtype</th>"
            f"<th>Text</th><th>Confidence</th><th>ID</th></tr></thead><tbody>{rows}</tbody></table></section>"
        )
    html_text = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ENGINE_NAME} Report</title>
<style>
body{{font-family:Inter,"Noto Sans TC",Arial,sans-serif;margin:0;background:#f4f7fb;color:#1f2937}}
header{{padding:24px 4vw;background:#fff;border-bottom:1px solid #dbe3ef}}
main{{max-width:1500px;margin:auto;padding:20px 3vw}} .cards{{display:flex;gap:10px;flex-wrap:wrap}}
.card{{background:#fff;border:1px solid #dbe3ef;border-radius:10px;padding:10px 14px;min-width:120px;display:flex;justify-content:space-between;gap:20px}}
section{{background:#fff;border:1px solid #dbe3ef;border-radius:12px;padding:16px;margin:18px 0;overflow:auto}}
img{{display:block;max-width:100%;height:auto;border:1px solid #cbd5e1;margin-bottom:14px}}
table{{border-collapse:collapse;width:100%;font-size:12px}} th,td{{border-bottom:1px solid #e5e7eb;text-align:left;padding:7px;vertical-align:top}}
th{{background:#eef3f9;position:sticky;top:0}} code{{font-size:10px;word-break:break-all}}
.backend{{max-height:360px;overflow:auto}}
</style></head><body><header><h1>{ENGINE_NAME} · Layout Analysis</h1>
<p>{html.escape(document.filename)} · {html.escape(document.document_id)} · Schema {SCHEMA_VERSION}</p></header>
<main><div class="cards">{type_cards}</div>
<section class="backend"><h2>Backend Capability Audit</h2><table><thead><tr><th>Backend</th><th>Role</th><th>Available</th><th>Activated</th><th>Status</th></tr></thead><tbody>{backend_rows}</tbody></table></section>
{''.join(page_sections)}</main></body></html>"""
    destination.write_text(html_text, encoding="utf-8")
    return destination


def export_all(document: DocumentLayout, output_dir: Path, config: EngineConfig) -> dict[str, Optional[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Optional[Path]] = {
        "json": export_json(document, output_dir, config),
        "jsonl": export_jsonl(document, output_dir, config),
        "csv": export_csv(document, output_dir, config),
        "sqlite": export_sqlite(document, output_dir, config),
        "parquet": export_parquet_if_available(document, output_dir, config),
        "html": export_html(document, output_dir, config),
    }
    manifest_path = output_dir / "manifest.json"
    serializable = {key: safe_relative_path(value, output_dir) if value else None for key, value in paths.items()}
    serializable["document_id"] = document.document_id
    serializable["created_utc"] = utc_timestamp()
    manifest_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    serializable["manifest"] = manifest_path.name
    return serializable


# =============================================================================
# 13. ORCHESTRATOR
# =============================================================================

def analyze_document(input_path: Path, output_dir: Path, config: EngineConfig) -> tuple[DocumentLayout, dict[str, Optional[str]]]:
    config.validate()
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not is_supported_input(input_path):
        raise ValueError(f"unsupported input type: {input_path.suffix}")
    output_dir.mkdir(parents=True, exist_ok=True)

    digest = sha256_file(input_path)
    document_id = f"GLE-{digest[:8].upper()}"
    backend_statuses = probe_backends()
    statuses = backend_map(backend_statuses)

    if input_path.suffix.casefold() == ".pdf":
        if not statuses.get("pymupdf") or not statuses["pymupdf"].available:
            raise RuntimeError("PyMuPDF is required by the current core PDF adapter")
        pages = extract_with_pymupdf(input_path, output_dir, config, statuses)
    else:
        pages = extract_image_page(input_path, output_dir, config)

    for page in pages:
        if should_ocr(page, config):
            if page.image_path:
                ocr_elements = run_tesseract_tsv(Path(page.image_path), page, config, statuses)
                merge_native_and_ocr(page, ocr_elements)
            else:
                page.warnings.append("OCR required but no rendered page image is available")

    enrich_tables_with_pdfplumber(input_path, pages, config, statuses)
    body_font_size = estimate_body_font_size(pages, config)
    classify_elements(pages, body_font_size, config)
    for page in pages:
        attach_contained_elements(page)
        bind_captions_and_sources(page, config)
        deduplicate_table_text(page)
        assign_reading_order(page, config)
    assign_ids(document_id, pages, config)
    render_annotations(pages, output_dir, config)

    document = DocumentLayout(
        document_id=document_id,
        filename=input_path.name,
        file_sha256=digest,
        schema_version=SCHEMA_VERSION,
        engine_version=ENGINE_VERSION,
        created_utc=utc_timestamp(),
        body_font_size=body_font_size,
        pages=pages,
        backends=backend_statuses,
    )
    document.statistics = collect_statistics(document)
    outputs = export_all(document, output_dir, config)
    return document, outputs


# =============================================================================
# 14. CONFIGURATION AND CLI
# =============================================================================

def load_config(path: Optional[Path]) -> EngineConfig:
    config = EngineConfig()
    if path is None:
        return config
    payload = json.loads(path.read_text(encoding="utf-8"))
    allowed = set(EngineConfig.__dataclass_fields__)
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown config keys: {', '.join(unknown)}")
    for key, value in payload.items():
        setattr(config, key, value)
    config.validate()
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic local PDF/image layout analysis engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="analyze one PDF or image")
    analyze_parser.add_argument("input", type=Path)
    analyze_parser.add_argument("--output", type=Path, required=True)
    analyze_parser.add_argument("--config", type=Path)
    analyze_parser.add_argument("--ocr", choices=["auto", "always", "never"])
    analyze_parser.add_argument("--languages")
    analyze_parser.add_argument("--dpi", type=int)
    analyze_parser.add_argument("--no-tables", action="store_true")
    analyze_parser.add_argument("--no-annotations", action="store_true")

    subparsers.add_parser("probe", help="show optional backend availability")
    return parser


def command_probe() -> int:
    payload = {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "schema": SCHEMA_VERSION,
        "backends": [asdict(status) for status in probe_backends()],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.ocr:
        config.ocr_mode = args.ocr
    if args.languages:
        config.ocr_languages = args.languages
    if args.dpi:
        config.dpi = args.dpi
    if args.no_tables:
        config.enable_tables = False
    if args.no_annotations:
        config.save_annotated_images = False
    document, outputs = analyze_document(args.input, args.output, config)
    print(json.dumps({"status": "PASS", "statistics": document.statistics, "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "probe":
            return command_probe()
        if args.command == "analyze":
            return command_analyze(args)
        parser.error(f"unknown command: {args.command}")
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
