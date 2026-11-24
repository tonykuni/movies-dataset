#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NON_STOCK_CORE v0400 — compatible core plus integrated report engine

Profiles:
- INDUSTRY_OUTLOOK
- MESSENGER_INTELLIGENCE
- EVERNOTE_INTELLIGENCE
- OTHER_INVESTMENT_INTELLIGENCE

Local-only, evidence-grounded, source-preserving.
"""
from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS — ALL EDITABLE PARAMETERS LIVE HERE
# =============================================================================
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable, Optional
from collections import Counter, defaultdict
from html.parser import HTMLParser
import argparse, csv, hashlib, html, json, os, re, sys, unicodedata
import xml.etree.ElementTree as ET


# [VIA:ACCEL-BRIDGE] Local bounded token cache + fingerprinted incremental analysis.
# External Celeritas integration is NOT_VERIFIED; no fictitious coverage claim.
from functools import lru_cache
MAX_INPUT_BYTES = 64 * 1024 * 1024
TOKEN_CACHE_SIZE = 32768
INPUT_SUFFIXES = (".pdf", ".txt", ".md", ".log", ".html", ".htm", ".docx", ".enex", ".json")
SOURCE_PROVENANCE = {'VIA_NonStock_Intelligence_Engine_v0100.py': 'fa3966543ed828e5bc826965f37186350bb506257cf985ae47dd803845cc3415', 'VIA_NON_STOCK_SUMMARIZER_ENGINE_v0200.py': '92f53d82c2facb41e599bf730b8be524901ed5d355aaed22a73444e85dccfa27', 'VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py': '86903811ad13b33ec4687105cc8143c0ea88997590807e235fcdf3224dcee5ef', 'VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300.py': 'c9cd3003160fa07c7fb0d5033eebe3ccbaa2d1e53e783cd59ef094b850961055'}
EMBEDDED_SHA256 = {'layout': '482e93ce2b53bd72bb85a9f74ad28a4a9315376cc4f07f2acf3fbe24d90bf620', 'repair': 'e58646f6e84739a6ccd3f61f8d70b458c16e764a0202c5f874f4a839d4150810', 'nlp': '8c0c649377bf38651913b0fb8282db8ddbde3739532e8f2f1f6c783bd7b6a768', 'integrated': '88393fed5598d31ff2a214dac490a1fcc0cafe9e37631c304e1d8fabe4afdac3'}
# Auditable bundled source; use --export-components to inspect individual modules.
EMBEDDED_SOURCES = {'layout': '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nVRN M03 PDF Layout → Full JSON  [SUPREME v3]\n=============================================\n整合全部已知 lib / class / function（5 classes + 22 functions）：\n\nClasses  : BlockItem, LineBox, PageLayoutResult, TableRegion, TextSpan\nFunctions: analyze_financial_page, analyze_pdf_layout,\n           apply_text_fixes, apply_text_fixes_to_spans,\n           build_page_candidates, classify_roles_by_size_and_bold,\n           detect_two_column_tables,\n           enrich_tables_with_captions_and_sources,\n           extract_blocks_pymupdf, extract_line_items_pdfplumber,\n           extract_lines_pdfplumber, extract_spans_with_font,\n           find_vertical_split, flag_bold_by_fontname, get_lines,\n           group_tables_in_column, ocr_page_image_to_spans,\n           split_lines_by_side,\n           _classify_roles_by_size_and_bold, _flag_bold_by_fontname,\n           _overlap_x, _pick_nearest\n\n加速: ThreadPoolExecutor(min(16, CPU×2)) + 動態進度條(\\\\r)\n輸入: pdf_temp（所有 PDF）\n輸出: m03_temp / VRN_Layout_Full.json + VRN_Verification_Layout.json\nPipeline: pdf_temp → M03 → m03_temp（供 M04/M05 讀取）\n\n# [ANC-A] MODULE_HEADER\n"""\n\nfrom __future__ import annotations\n\nimport os\nimport re\nimport sys\nimport json\nimport time\nimport hashlib\nimport statistics\nimport threading\nfrom dataclasses import dataclass, asdict\nfrom typing import Any, Callable, Dict, List, Optional, Tuple\nfrom concurrent.futures import ThreadPoolExecutor, as_completed\n\n# ── VRN 路徑注入 ─────────────────────────────────────────────────────────────\n# [ANC-B] PATH_BOOTSTRAP\ntry:\n    import VRN_Core_Loader\n    VRN_Core_Loader.ensure_paths()\nexcept Exception:\n    pass\n\n# [ANC-C] ACCEL_BOOTSTRAP\ntry:\n    from VRN_Accel_Unified import bootstrap as _vrn_accel_bootstrap\n    _vrn_accel_bootstrap()\nexcept Exception:\n    pass\n\n# ── 環境變數路徑 ─────────────────────────────────────────────────────────────\n# [ANC-D] ENV_PATHS\nP_PDF_TEMP = os.environ.get(\n    "VRN_PDF_TEMP",\n    r"C:\\VeritasIntelligenceAnalytics\\VeritasReportNova\\temp\\pdf_temp",\n)\nP_M03_TEMP = os.environ.get(\n    "VRN_M03_TEMP",\n    r"C:\\VeritasIntelligenceAnalytics\\VeritasReportNova\\temp\\m03_temp",\n)\n\n_MAX_WORKERS: int = min(16, (os.cpu_count() or 4) * 2)\n\n# Caption / Source 正則\nTABLE_NO_PATTERNS = [re.compile(r"^(表|Table)\\s*\\d+[-\\u2013]?\\d*", re.IGNORECASE)]\nSOURCE_PATTERNS   = [re.compile(r"^(資料來源|Source)\\s*[:：]", re.IGNORECASE)]\n\n\n# =============================================================================\n# [ANC-E] DATA_STRUCTURES  (5 classes)\n# =============================================================================\n\n@dataclass\nclass TextSpan:\n    """單 span：文字 + bbox + font + 語義角色。"""\n    page:      int\n    text:      str\n    bbox:      Tuple[float, float, float, float]\n    fontname:  str\n    size:      float\n    is_bold:   bool\n    role:      str   # TITLE / SUBTITLE / SECTION_HEADING / BODY / SMALL_NOISE / UNKNOWN\n    is_fixed:  bool\n\n\n@dataclass\nclass LineBox:\n    """行/詞級 bbox（pdfplumber extract_words 單位）。"""\n    page: int\n    x0:   float\n    y0:   float\n    x1:   float\n    y1:   float\n    text: str\n\n\n@dataclass\nclass PageLayoutResult:\n    """單頁 PyMuPDF span 版面分析結果。"""\n    page:        int\n    spans:       List[TextSpan]\n    page_width:  float\n    page_height: float\n\n\n@dataclass\nclass TableRegion:\n    """偵測到的表格區域（含左右欄、caption、source）。"""\n    page:        int\n    side:        str\n    table_id:    str\n    bbox:        Tuple[float, float, float, float]\n    lines:       List[LineBox]\n    caption:     Optional[str]       = None\n    table_no:    Optional[str]       = None\n    table_title: Optional[str]       = None\n    source:      Optional[str]       = None\n    notes:       Optional[List[str]] = None\n\n\n@dataclass\nclass BlockItem:\n    """粗/細粒度 block（段落/行/詞）。"""\n    page:     int\n    block_id: str\n    bbox:     Tuple[float, float, float, float]\n    text:     str\n\n\n# =============================================================================\n# [ANC-F] PROGRESS_ENGINE\n# =============================================================================\n\n_progress_lock  = threading.Lock()\n_progress_state: Dict[str, Any] = {\n    "done": 0, "total": 0, "errors": 0, "t0": 0.0, "label": "",\n}\n\n\ndef _progress_init(total: int, label: str = "M03-Layout") -> None:\n    with _progress_lock:\n        _progress_state.update(\n            {"done": 0, "total": total, "errors": 0, "t0": time.time(), "label": label}\n        )\n\n\ndef _progress_tick(error: bool = False) -> None:\n    with _progress_lock:\n        _progress_state["done"] += 1\n        if error:\n            _progress_state["errors"] += 1\n        done  = _progress_state["done"]\n        total = _progress_state["total"]\n        errs  = _progress_state["errors"]\n        label = _progress_state["label"]\n        pct   = done / total * 100 if total else 0\n        bar_w = 40\n        filled = int(bar_w * done / total) if total else 0\n        bar = "\\u2588" * filled + "\\u2591" * (bar_w - filled)\n        elapsed = time.time() - _progress_state["t0"]\n        eta = (elapsed / done * (total - done)) if done else 0\n        sys.stdout.write(\n            f"\\r[{label}] [{bar}] {done}/{total} ({pct:.1f}%)"\n            f"  ERR:{errs}  ETA:{eta:.1f}s  "\n        )\n        sys.stdout.flush()\n        if done == total:\n            sys.stdout.write("\\n")\n            sys.stdout.flush()\n\n\n# =============================================================================\n# [ANC-G] SHA256_UTIL\n# =============================================================================\n\ndef _file_sha256(path: str, max_mb: int = 50) -> Optional[str]:\n    if not os.path.isfile(path):\n        return None\n    try:\n        h = hashlib.sha256()\n        with open(path, "rb") as fh:\n            for chunk in iter(lambda: fh.read(1 << 20), b""):\n                h.update(chunk)\n                if max_mb and fh.tell() > max_mb * (1 << 20):\n                    break\n        return h.hexdigest()\n    except Exception:\n        return None\n\n\n# =============================================================================\n# [ANC-H] PDF_LIST\n# =============================================================================\n\ndef _list_pdfs(pdf_dir: str) -> List[str]:\n    if not os.path.isdir(pdf_dir):\n        return []\n    return sorted(\n        os.path.join(pdf_dir, f)\n        for f in os.listdir(pdf_dir)\n        if f.lower().endswith(".pdf") and "__COVER_FIN" not in f\n    )\n\n\n# =============================================================================\n# [ANC-I] FONT_ANALYSIS\n# Functions: flag_bold_by_fontname, _flag_bold_by_fontname,\n#            classify_roles_by_size_and_bold, _classify_roles_by_size_and_bold\n# =============================================================================\n\ndef flag_bold_by_fontname(spans: List[TextSpan]) -> None:\n    """利用 fontname 含 Bold/Demi/Black 判斷粗體。"""\n    for s in spans:\n        name = s.fontname.lower()\n        s.is_bold = any(tok in name for tok in ["bold", "demi", "black"])\n\n\n_flag_bold_by_fontname = flag_bold_by_fontname  # 內部別名\n\n\ndef classify_roles_by_size_and_bold(spans: List[TextSpan]) -> None:\n    """依字級分佈 + 粗體決定語義角色。"""\n    if not spans:\n        return\n    sizes        = [s.size for s in spans]\n    median_size  = statistics.median(sizes)\n    max_size     = max(sizes)\n    t_thresh     = max_size      * 0.9\n    sub_thresh   = median_size   * 1.3\n    small_thresh = median_size   * 0.75\n\n    for s in spans:\n        if   s.size >= t_thresh   and s.is_bold: s.role = "TITLE"\n        elif s.size >= sub_thresh and s.is_bold: s.role = "SUBTITLE"\n        elif s.size >  median_size and s.is_bold: s.role = "SECTION_HEADING"\n        elif s.size <= small_thresh:              s.role = "SMALL_NOISE"\n        else:                                     s.role = "BODY"\n\n\n_classify_roles_by_size_and_bold = classify_roles_by_size_and_bold  # 內部別名\n\n\n# =============================================================================\n# [ANC-J] SPAN_EXTRACTOR\n# Function: extract_spans_with_font\n# =============================================================================\n\ndef extract_spans_with_font(pdf_path: str) -> List[Dict[str, Any]]:\n    """PyMuPDF span dict → 全頁 TextSpan 清單（已含 bold+role）。"""\n    try:\n        import fitz\n    except ImportError:\n        return []\n    doc   = fitz.open(pdf_path)\n    pages: List[Dict[str, Any]] = []\n    for page_index, page in enumerate(doc):\n        raw   = page.get_text("dict")\n        spans: List[TextSpan] = []\n        for block in raw.get("blocks", []):\n            if block.get("type", 0) != 0:\n                continue\n            for line in block.get("lines", []):\n                for span in line.get("spans", []):\n                    text = span.get("text", "").strip()\n                    if not text:\n                        continue\n                    spans.append(TextSpan(\n                        page=page_index, text=text,\n                        bbox=tuple(span.get("bbox", (0, 0, 0, 0))),\n                        fontname=span.get("font", ""),\n                        size=float(span.get("size", 0)),\n                        is_bold=False, role="UNKNOWN", is_fixed=False,\n                    ))\n        flag_bold_by_fontname(spans)\n        classify_roles_by_size_and_bold(spans)\n        pages.append({\n            "page":   page_index,\n            "width":  page.rect.width,\n            "height": page.rect.height,\n            "spans":  [asdict(s) for s in spans],\n        })\n    doc.close()\n    return pages\n\n\n# =============================================================================\n# [ANC-K] OCR_HOOKS\n# Function: ocr_page_image_to_spans\n# =============================================================================\n\ndef ocr_page_image_to_spans(\n    image_path: str,\n    ocr_engine: str = "paddle",\n    lang: str = "ch",\n    page_index: int = 0,\n) -> List[TextSpan]:\n    """\n    掃描 PDF 備援 OCR：\n    paddle → PaddleOCR（bbox 高度作為視覺字級）\n    surya  → 預留（NotImplemented）\n    """\n    spans: List[TextSpan] = []\n    if ocr_engine == "paddle":\n        try:\n            from paddleocr import PaddleOCR  # type: ignore\n        except ImportError as e:\n            raise RuntimeError("請先 pip install paddleocr") from e\n        ocr    = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=False)\n        result = ocr.ocr(image_path, cls=True)\n        for line in (result[0] or []):\n            pts = line[0]\n            xs  = [p[0] for p in pts]; ys = [p[1] for p in pts]\n            txt = line[1][0].strip()\n            if not txt:\n                continue\n            height = max(ys) - min(ys)\n            spans.append(TextSpan(\n                page=page_index, text=txt,\n                bbox=(min(xs), min(ys), max(xs), max(ys)),\n                fontname="ocr_visual", size=float(height),\n                is_bold=False, role="UNKNOWN", is_fixed=False,\n            ))\n    elif ocr_engine == "surya":\n        raise NotImplementedError("surya OCR 接口尚未實作示例")\n    else:\n        raise ValueError(f"未知 OCR 引擎: {ocr_engine}")\n    flag_bold_by_fontname(spans)\n    classify_roles_by_size_and_bold(spans)\n    return spans\n\n\n# =============================================================================\n# [ANC-L] ANALYZE_PDF_LAYOUT（含 OCR 分支預留）\n# Function: analyze_pdf_layout\n# =============================================================================\n\ndef _extract_layout_results(pdf_path: str) -> List[PageLayoutResult]:\n    try:\n        import fitz\n    except ImportError:\n        return []\n    doc     = fitz.open(pdf_path)\n    results: List[PageLayoutResult] = []\n    for page_index, page in enumerate(doc):\n        raw   = page.get_text("dict")\n        spans: List[TextSpan] = []\n        for block in raw.get("blocks", []):\n            if block.get("type", 0) != 0:\n                continue\n            for line in block.get("lines", []):\n                for span in line.get("spans", []):\n                    text = span.get("text", "").strip()\n                    if not text:\n                        continue\n                    spans.append(TextSpan(\n                        page=page_index, text=text,\n                        bbox=tuple(span.get("bbox", (0, 0, 0, 0))),\n                        fontname=span.get("font", ""),\n                        size=float(span.get("size", 0)),\n                        is_bold=False, role="UNKNOWN", is_fixed=False,\n                    ))\n        results.append(PageLayoutResult(\n            page=page_index, spans=spans,\n            page_width=page.rect.width, page_height=page.rect.height,\n        ))\n    doc.close()\n    return results\n\n\ndef analyze_pdf_layout(\n    pdf_path: str,\n    use_ocr_for_image_only: bool = True,\n    ocr_engine: str = "paddle",\n    ocr_lang: str = "ch",\n) -> List[Dict[str, Any]]:\n    """高階：原生 PDF 用 PyMuPDF；純影像頁可接 ocr_page_image_to_spans。"""\n    layout_results = _extract_layout_results(pdf_path)\n    for pr in layout_results:\n        flag_bold_by_fontname(pr.spans)\n        classify_roles_by_size_and_bold(pr.spans)\n        # if use_ocr_for_image_only and not pr.spans:\n        #     image_path = render_page_to_image(pdf_path, pr.page)\n        #     pr.spans = ocr_page_image_to_spans(image_path, ocr_engine, ocr_lang, pr.page)\n    return [\n        {"page": pr.page, "width": pr.page_width, "height": pr.page_height,\n         "spans": [asdict(s) for s in pr.spans]}\n        for pr in layout_results\n    ]\n\n\n# =============================================================================\n# [ANC-M] TEXT_FIXES\n# Functions: apply_text_fixes, apply_text_fixes_to_spans\n# =============================================================================\n\ndef apply_text_fixes(\n    layout_data: List[Dict[str, Any]],\n    fixer_fn: Callable[[str], Any],\n) -> List[Dict[str, Any]]:\n    """對 layout_data 中所有 span 套用文字修復函式並標記 is_fixed。"""\n    for page in layout_data:\n        for span in page.get("spans", []):\n            old = span["text"]\n            new = fixer_fn(old)\n            if isinstance(new, tuple):\n                new_text, fixed_flag = new\n            else:\n                new_text, fixed_flag = new, (new != old)\n            span["text"]     = new_text\n            span["is_fixed"] = bool(fixed_flag)\n    return layout_data\n\n\ndef apply_text_fixes_to_spans(\n    pages_spans: List[Dict[str, Any]],\n    fixer_fn: Callable[[str], str],\n) -> List[Dict[str, Any]]:\n    """apply_text_fixes 的別名（financial_layout_ocr 用名）。"""\n    return apply_text_fixes(pages_spans, fixer_fn)\n\n\n# =============================================================================\n# [ANC-N] LINE_EXTRACTION\n# Functions: extract_lines_pdfplumber, get_lines\n# =============================================================================\n\ndef extract_lines_pdfplumber(pdf_path: str, page_index: int) -> List[LineBox]:\n    """pdfplumber extract_words → LineBox 列表（供雙欄偵測 & 表格分組）。"""\n    lines: List[LineBox] = []\n    try:\n        import pdfplumber\n        with pdfplumber.open(pdf_path) as pdf:\n            if page_index >= len(pdf.pages):\n                return lines\n            page = pdf.pages[page_index]\n            for w in page.extract_words(x_tolerance=1, y_tolerance=3):\n                txt = w["text"].strip()\n                if not txt:\n                    continue\n                lines.append(LineBox(\n                    page=page_index,\n                    x0=float(w["x0"]),   y0=float(w["top"]),\n                    x1=float(w["x1"]),   y1=float(w["bottom"]),\n                    text=txt,\n                ))\n    except Exception:\n        pass\n    return lines\n\n\ndef get_lines(pdf_path: str, page_index: int) -> List[LineBox]:\n    """extract_lines_pdfplumber 的別名（two_column_detector 用名）。"""\n    return extract_lines_pdfplumber(pdf_path, page_index)\n\n\n# =============================================================================\n# [ANC-O] TWO_COLUMN_DETECTION\n# Functions: find_vertical_split, split_lines_by_side,\n#            group_tables_in_column, detect_two_column_tables\n# =============================================================================\n\ndef find_vertical_split(lines: List[LineBox]) -> Optional[float]:\n    if not lines:\n        return None\n    centers       = [0.5 * (ln.x0 + ln.x1) for ln in lines]\n    median_x      = statistics.median(centers)\n    left_centers  = [c for c in centers if c < median_x]\n    right_centers = [c for c in centers if c > median_x]\n    if not left_centers or not right_centers:\n        return None\n    return 0.5 * (max(left_centers) + min(right_centers))\n\n\ndef split_lines_by_side(\n    lines: List[LineBox],\n    split_x: float,\n) -> Tuple[List[LineBox], List[LineBox]]:\n    left  = [ln for ln in lines if ln.x1 <= split_x]\n    right = [ln for ln in lines if ln.x0 >= split_x]\n    for ln in lines:\n        if ln.x0 < split_x < ln.x1:\n            if 0.5 * (ln.x0 + ln.x1) <= split_x:\n                left.append(ln)\n            else:\n                right.append(ln)\n    return left, right\n\n\ndef group_tables_in_column(\n    lines: List[LineBox],\n    page_index: int,\n    side: str,\n) -> List[TableRegion]:\n    if not lines:\n        return []\n    lines_sorted = sorted(lines, key=lambda l: (l.y0, l.x0))\n    gaps = [lines_sorted[i].y0 - lines_sorted[i - 1].y1\n            for i in range(1, len(lines_sorted))]\n    gap_median    = statistics.median(gaps) if gaps else 0\n    gap_threshold = gap_median * 2.5 if gap_median > 0 else 10\n\n    tables: List[TableRegion] = []\n    current: List[LineBox]    = [lines_sorted[0]]\n    counter = 1\n\n    def _flush(cur: List[LineBox]) -> TableRegion:\n        nonlocal counter\n        x0 = min(l.x0 for l in cur); y0 = min(l.y0 for l in cur)\n        x1 = max(l.x1 for l in cur); y1 = max(l.y1 for l in cur)\n        t  = TableRegion(\n            page=page_index, side=side,\n            table_id=f"P{page_index:03d}-{side.upper()[0]}T{counter:02d}",\n            bbox=(x0, y0, x1, y1), lines=cur[:],\n        )\n        counter += 1\n        return t\n\n    for i in range(1, len(lines_sorted)):\n        if lines_sorted[i].y0 - lines_sorted[i - 1].y1 > gap_threshold:\n            tables.append(_flush(current))\n            current = [lines_sorted[i]]\n        else:\n            current.append(lines_sorted[i])\n    if current:\n        tables.append(_flush(current))\n    return tables\n\n\ndef detect_two_column_tables(pdf_path: str, page_index: int) -> Dict[str, Any]:\n    lines = get_lines(pdf_path, page_index)\n    if not lines:\n        return {"page": page_index, "split_x": None,\n                "left_tables": [], "right_tables": []}\n    split_x = find_vertical_split(lines)\n    if split_x is None:\n        left_lines, right_lines = lines, []\n    else:\n        left_lines, right_lines = split_lines_by_side(lines, split_x)\n    left_tables  = group_tables_in_column(left_lines,  page_index, "left")\n    right_tables = group_tables_in_column(right_lines, page_index, "right")\n    return {\n        "page":        page_index,\n        "split_x":     split_x,\n        "left_tables": [asdict(t) for t in left_tables],\n        "right_tables":[asdict(t) for t in right_tables],\n    }\n\n\n# =============================================================================\n# [ANC-P] CAPTION_SOURCE_DETECTION\n# Functions: _overlap_x, _pick_nearest, enrich_tables_with_captions_and_sources\n# =============================================================================\n\ndef _overlap_x(line: LineBox, bbox: Tuple[float, float, float, float]) -> bool:\n    bx0, _, bx1, _ = bbox\n    return not (line.x1 < bx0 or line.x0 > bx1)\n\n\ndef _pick_nearest(\n    lines: List[LineBox],\n    ref_y: float,\n    above: bool = True,\n) -> Optional[LineBox]:\n    if not lines:\n        return None\n    if above:\n        cands = [ln for ln in lines if ln.y1 <= ref_y]\n        return min(cands, key=lambda ln: ref_y - ln.y1) if cands else None\n    cands = [ln for ln in lines if ln.y0 >= ref_y]\n    return min(cands, key=lambda ln: ln.y0 - ref_y) if cands else None\n\n\ndef enrich_tables_with_captions_and_sources(\n    tables: List[TableRegion],\n    all_lines: List[LineBox],\n    above_window: float = 80.0,\n    below_window: float = 120.0,\n) -> None:\n    for t in tables:\n        tx0, ty0, tx1, ty1 = t.bbox\n        above_lines = [\n            ln for ln in all_lines\n            if ln.y1 <= ty0 and (ty0 - ln.y1) <= above_window\n            and _overlap_x(ln, t.bbox)\n        ]\n        below_lines = [\n            ln for ln in all_lines\n            if ln.y0 >= ty1 and (ln.y0 - ty1) <= below_window\n            and _overlap_x(ln, t.bbox)\n        ]\n        caption_line = _pick_nearest(above_lines, ref_y=ty0, above=True)\n        if caption_line:\n            txt = caption_line.text.strip()\n            t.caption  = txt\n            table_no   = title = None\n            for pat in TABLE_NO_PATTERNS:\n                m = pat.match(txt)\n                if m:\n                    table_no = m.group(0)\n                    title    = txt[m.end():].strip("：: -")\n                    break\n            t.table_no    = table_no\n            t.table_title = title if title else txt\n        notes: List[str] = []\n        for ln in below_lines:\n            txt = ln.text.strip()\n            if any(p.match(txt) for p in SOURCE_PATTERNS):\n                t.source = txt\n            else:\n                notes.append(txt)\n        t.notes = notes if notes else None\n\n\n# =============================================================================\n# [ANC-Q] FINANCIAL_PAGE_ANALYZER\n# Function: analyze_financial_page\n# =============================================================================\n\ndef _extract_spans_single_page(pdf_path: str, page_index: int) -> List[Dict[str, Any]]:\n    try:\n        import fitz\n        doc  = fitz.open(pdf_path)\n        if page_index >= len(doc):\n            doc.close()\n            return []\n        page = doc[page_index]\n        raw  = page.get_text("dict")\n        spans: List[TextSpan] = []\n        for block in raw.get("blocks", []):\n            if block.get("type", 0) != 0:\n                continue\n            for line in block.get("lines", []):\n                for span in line.get("spans", []):\n                    text = span.get("text", "").strip()\n                    if not text:\n                        continue\n                    spans.append(TextSpan(\n                        page=page_index, text=text,\n                        bbox=tuple(span.get("bbox", (0, 0, 0, 0))),\n                        fontname=span.get("font", ""),\n                        size=float(span.get("size", 0)),\n                        is_bold=False, role="UNKNOWN", is_fixed=False,\n                    ))\n        flag_bold_by_fontname(spans)\n        classify_roles_by_size_and_bold(spans)\n        doc.close()\n        return [asdict(s) for s in spans]\n    except Exception:\n        return []\n\n\ndef analyze_financial_page(pdf_path: str, page_index: int) -> Dict[str, Any]:\n    """\n    單頁財報完整分析：\n    1. pdfplumber 取行 boxes\n    2. 偵測雙欄分界\n    3. 左右欄分組成表格區域\n    4. caption / source / notes 附加\n    5. PyMuPDF span + font + role\n    """\n    lines     = extract_lines_pdfplumber(pdf_path, page_index)\n    spans_out = _extract_spans_single_page(pdf_path, page_index)\n\n    if not lines:\n        return {\n            "page":        page_index,\n            "split_x":     None,\n            "left_tables": [],\n            "right_tables":[],\n            "spans":       spans_out,\n        }\n\n    split_x = find_vertical_split(lines)\n    if split_x is None:\n        left_lines, right_lines = lines, []\n    else:\n        left_lines, right_lines = split_lines_by_side(lines, split_x)\n\n    left_tables  = group_tables_in_column(left_lines,  page_index, "left")\n    right_tables = group_tables_in_column(right_lines, page_index, "right")\n    enrich_tables_with_captions_and_sources(left_tables,  lines)\n    enrich_tables_with_captions_and_sources(right_tables, lines)\n\n    return {\n        "page":        page_index,\n        "split_x":     split_x,\n        "left_tables": [asdict(t) for t in left_tables],\n        "right_tables":[asdict(t) for t in right_tables],\n        "spans":       spans_out,\n    }\n\n\n# =============================================================================\n# [ANC-R] BLOCK_SEGMENTER\n# Functions: extract_blocks_pymupdf, extract_line_items_pdfplumber,\n#            build_page_candidates\n# =============================================================================\n\ndef extract_blocks_pymupdf(pdf_path: str, page_index: int) -> List[BlockItem]:\n    """PyMuPDF block 層（段落/表格/圖附近的粗粒度區塊）。"""\n    blocks: List[BlockItem] = []\n    try:\n        import fitz\n        doc  = fitz.open(pdf_path)\n        if page_index >= len(doc):\n            doc.close()\n            return blocks\n        page = doc[page_index]\n        raw  = page.get_text("dict")\n        for b_idx, block in enumerate(raw.get("blocks", [])):\n            if block.get("type", 0) != 0:\n                continue\n            texts: List[str] = []\n            x0 = y0 = 1e9; x1 = y1 = -1e9\n            for line in block.get("lines", []):\n                for span in line.get("spans", []):\n                    t = span.get("text", "")\n                    if t.strip():\n                        texts.append(t)\n                    sx0, sy0, sx1, sy1 = span.get("bbox", (0, 0, 0, 0))\n                    x0 = min(x0, sx0); y0 = min(y0, sy0)\n                    x1 = max(x1, sx1); y1 = max(y1, sy1)\n            if not texts:\n                continue\n            blocks.append(BlockItem(\n                page=page_index,\n                block_id=f"P{page_index:03d}-B{b_idx:03d}",\n                bbox=(x0, y0, x1, y1),\n                text=" ".join(texts).strip(),\n            ))\n        doc.close()\n    except Exception:\n        pass\n    return blocks\n\n\ndef extract_line_items_pdfplumber(pdf_path: str, page_index: int) -> List[BlockItem]:\n    """pdfplumber 行/詞級 BlockItem（細粒度，適合句子分析）。"""\n    blocks: List[BlockItem] = []\n    try:\n        import pdfplumber\n        with pdfplumber.open(pdf_path) as pdf:\n            if page_index >= len(pdf.pages):\n                return blocks\n            page = pdf.pages[page_index]\n            for i, w in enumerate(page.extract_words(x_tolerance=1, y_tolerance=3)):\n                txt = w["text"].strip()\n                if not txt:\n                    continue\n                blocks.append(BlockItem(\n                    page=page_index,\n                    block_id=f"P{page_index:03d}-L{i:04d}",\n                    bbox=(float(w["x0"]), float(w["top"]),\n                          float(w["x1"]), float(w["bottom"])),\n                    text=txt,\n                ))\n    except Exception:\n        pass\n    return blocks\n\n\ndef build_page_candidates(pdf_path: str, page_index: int) -> Dict[str, Any]:\n    """\n    雙層 block 候選結構：\n    page_blocks → 粗粒度（段落/表格/圖），適合表格候選判斷\n    line_items  → 細粒度（行/詞），適合句子級分析\n    """\n    coarse = extract_blocks_pymupdf(pdf_path, page_index)\n    fine   = extract_line_items_pdfplumber(pdf_path, page_index)\n    return {\n        "page":        page_index,\n        "page_blocks": [asdict(b) for b in coarse],\n        "line_items":  [asdict(l) for l in fine],\n    }\n\n\n# =============================================================================\n# [ANC-S] PDF_EXTRACTOR（單 PDF 完整結構，4 層優先鏈）\n# =============================================================================\n\ndef _extract_pdf_structure(pdf_path: str) -> Dict[str, Any]:\n    """\n    優先鏈：\n    1. VRN_Extraction_Orchestrator.run_layout_once（最快）\n    2. analyze_financial_page × 全頁（雙欄+span+block，最完整）\n    3. pdfplumber 純文字\n    4. fitz 純文字\n    """\n    # 優先 1：Orchestrator\n    try:\n        from VRN_Extraction_Orchestrator import run_layout_once\n        rec = run_layout_once(pdf_path)\n        if rec and not rec.get("error"):\n            rec.setdefault("layout_source", "VRN_Extraction_Orchestrator")\n            rec["sha256"] = _file_sha256(pdf_path)\n            return rec\n    except ImportError:\n        pass\n    except Exception:\n        pass\n\n    result: Dict[str, Any] = {\n        "file":          os.path.basename(pdf_path),\n        "path":          pdf_path,\n        "sha256":        _file_sha256(pdf_path),\n        "n_pages":       0,\n        "pages":         [],\n        "tables_total":  0,\n        "layout_source": None,\n        "error":         None,\n    }\n\n    # 優先 2：analyze_financial_page（完整）\n    try:\n        import fitz\n        import pdfplumber\n        doc     = fitz.open(pdf_path)\n        n_pages = len(doc)\n        doc.close()\n        result["n_pages"]       = n_pages\n        result["layout_source"] = "financial_page_analyzer"\n        total_tables = 0\n        pages_out: List[Dict[str, Any]] = []\n        for pg_idx in range(n_pages):\n            pg_rec = analyze_financial_page(pdf_path, pg_idx)\n            cands  = build_page_candidates(pdf_path, pg_idx)\n            pg_rec["page_blocks"] = cands["page_blocks"]\n            pg_rec["line_items"]  = cands["line_items"]\n            total_tables += (\n                len(pg_rec.get("left_tables", []))\n                + len(pg_rec.get("right_tables", []))\n            )\n            pages_out.append(pg_rec)\n        result["pages"]        = pages_out\n        result["tables_total"] = total_tables\n        return result\n    except Exception as e:\n        result["error"] = f"financial_analyzer:{e}"\n\n    # 優先 3：pdfplumber 純文字\n    try:\n        import pdfplumber\n        with pdfplumber.open(pdf_path) as pdf:\n            result["n_pages"]       = len(pdf.pages)\n            result["layout_source"] = "pdfplumber_text"\n            result["error"]         = None\n            pages_out = []\n            total_tbl = 0\n            for i, page in enumerate(pdf.pages):\n                raw_text = page.extract_text() or ""\n                words    = page.extract_words() or []\n                tables   = page.extract_tables() or []\n                total_tbl += len(tables)\n                tbl_list: List[Dict[str, Any]] = []\n                for t_idx, tbl in enumerate(tables):\n                    tbl_list.append({\n                        "table_index": t_idx,\n                        "rows":  len(tbl),\n                        "cols":  max((len(r) for r in tbl if r), default=0),\n                        "data":  tbl,\n                    })\n                pages_out.append({\n                    "page":       i + 1,\n                    "width":      float(page.width)  if page.width  else None,\n                    "height":     float(page.height) if page.height else None,\n                    "text":       raw_text,\n                    "char_count": len(raw_text),\n                    "word_count": len(words),\n                    "tables":     tbl_list,\n                })\n            result["pages"]        = pages_out\n            result["tables_total"] = total_tbl\n        return result\n    except Exception as e:\n        if not result["error"]:\n            result["error"] = f"pdfplumber:{e}"\n\n    # 優先 4：fitz 純文字\n    try:\n        import fitz\n        doc = fitz.open(pdf_path)\n        result["n_pages"]       = len(doc)\n        result["layout_source"] = "pymupdf_text"\n        result["error"]         = None\n        pages_out = []\n        for i in range(len(doc)):\n            pg   = doc[i]\n            text = pg.get_text()\n            pages_out.append({\n                "page":        i + 1,\n                "width":       float(pg.rect.width),\n                "height":      float(pg.rect.height),\n                "text":        text,\n                "char_count":  len(text),\n                "block_count": len(pg.get_text("blocks") or []),\n                "tables":      [],\n            })\n        doc.close()\n        result["pages"] = pages_out\n        return result\n    except Exception as e2:\n        if not result["error"]:\n            result["error"] = f"fitz:{e2}"\n        return result\n\n\n# =============================================================================\n# [ANC-T] PARALLEL_CORE\n# =============================================================================\n\ndef _parallel_extract(pdf_list: List[str]) -> List[Tuple[str, Dict[str, Any]]]:\n    try:\n        from VRN_Extraction_Orchestrator import parallel_map_pdfs\n        results = parallel_map_pdfs(_extract_pdf_structure, pdf_list)\n        _progress_init(len(pdf_list))\n        out = []\n        for path, rec in zip(pdf_list, results):\n            err = rec is None or bool(rec.get("error") if rec else True)\n            _progress_tick(error=err)\n            out.append((path, rec or {\n                "file": os.path.basename(path), "path": path,\n                "n_pages": 0, "pages": [], "tables_total": 0,\n                "layout_source": None, "error": "parallel_failed",\n            }))\n        return out\n    except Exception:\n        pass\n\n    _progress_init(len(pdf_list))\n    results_map: Dict[str, Dict[str, Any]] = {}\n    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:\n        future_to_path = {pool.submit(_extract_pdf_structure, p): p for p in pdf_list}\n        for fut in as_completed(future_to_path):\n            path = future_to_path[fut]\n            try:\n                rec = fut.result(timeout=180)\n            except Exception as exc:\n                rec = {\n                    "file": os.path.basename(path), "path": path,\n                    "n_pages": 0, "pages": [], "tables_total": 0,\n                    "layout_source": None, "error": str(exc),\n                }\n            results_map[path] = rec\n            _progress_tick(error=bool(rec.get("error")))\n    return [(p, results_map[p]) for p in pdf_list]\n\n\n# =============================================================================\n# [ANC-U] MAIN_FLOW\n# =============================================================================\n\ndef run_layout_to_json(pdf_dir: str, output_dir: str) -> Dict[str, Any]:\n    os.makedirs(output_dir, exist_ok=True)\n    pdf_list = _list_pdfs(pdf_dir)\n\n    full: Dict[str, Any] = {\n        "module":           "VRN_M03_PDF_Layout_JSON",\n        "schema_version":   "3.0",\n        "source_dir":       pdf_dir,\n        "generated_at":     time.strftime("%Y-%m-%d %H:%M:%S"),\n        "file_count":       len(pdf_list),\n        "workers":          _MAX_WORKERS,\n        "registered_classes": [\n            "BlockItem", "LineBox", "PageLayoutResult", "TableRegion", "TextSpan",\n        ],\n        "registered_functions": [\n            "analyze_financial_page", "analyze_pdf_layout",\n            "apply_text_fixes", "apply_text_fixes_to_spans",\n            "build_page_candidates", "classify_roles_by_size_and_bold",\n            "detect_two_column_tables",\n            "enrich_tables_with_captions_and_sources",\n            "extract_blocks_pymupdf", "extract_line_items_pdfplumber",\n            "extract_lines_pdfplumber", "extract_spans_with_font",\n            "find_vertical_split", "flag_bold_by_fontname",\n            "get_lines", "group_tables_in_column",\n            "ocr_page_image_to_spans", "split_lines_by_side",\n            "_classify_roles_by_size_and_bold", "_flag_bold_by_fontname",\n            "_overlap_x", "_pick_nearest",\n        ],\n        "files": {},\n    }\n    stats: Dict[str, Any] = {\n        "processed": 0, "errors": [], "skipped": 0,\n        "total_pages": 0, "total_tables": 0, "file_checksums": {},\n    }\n\n    if not pdf_list:\n        print("[M03-Layout] No PDF found — writing empty structure.")\n        out_json = os.path.join(output_dir, "VRN_Layout_Full.json")\n        try:\n            with open(out_json, "w", encoding="utf-8") as fh:\n                json.dump(full, fh, ensure_ascii=False, indent=2)\n        except Exception as e:\n            stats["errors"].append(f"Write VRN_Layout_Full.json (empty): {e}")\n        return stats\n\n    print(f"[M03-Layout] {len(pdf_list)} PDFs  workers={_MAX_WORKERS}")\n    pairs = _parallel_extract(pdf_list)\n\n    for path, rec in pairs:\n        fn = os.path.basename(path)\n        full["files"][fn] = rec\n        if rec.get("error"):\n            stats["errors"].append(f"{fn}: {rec[\'error\']}")\n        else:\n            stats["processed"]    += 1\n            stats["total_pages"]  += rec.get("n_pages", 0)\n            stats["total_tables"] += rec.get("tables_total", 0)\n\n    out_json = os.path.join(output_dir, "VRN_Layout_Full.json")\n    try:\n        with open(out_json, "w", encoding="utf-8") as fh:\n            json.dump(full, fh, ensure_ascii=False, indent=2)\n        c = _file_sha256(out_json)\n        if c:\n            stats["file_checksums"]["VRN_Layout_Full.json"] = c\n    except Exception as e:\n        stats["errors"].append(f"Write VRN_Layout_Full.json: {e}")\n\n    return stats\n\n\n# =============================================================================\n# [ANC-V] ENTRY_POINT\n# =============================================================================\n\ndef main() -> int:\n    t0      = time.time()\n    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else P_PDF_TEMP\n    out_dir = sys.argv[2] if len(sys.argv) > 2 else P_M03_TEMP\n\n    print("=" * 65)\n    print("  VRN M03  PDF Layout → Full JSON  [SUPREME v3]")\n    print("  Registered: 5 classes  22 functions")\n    print("=" * 65)\n    print(f"  Input  (pdf_temp) : {pdf_dir}")\n    print(f"  Output (m03_temp) : {out_dir}")\n    print(f"  Workers           : {_MAX_WORKERS}")\n    print()\n\n    stats   = run_layout_to_json(pdf_dir, out_dir)\n    elapsed = round(time.time() - t0, 2)\n\n    verification = {\n        "module":         "VRN_M03_PDF_Layout_JSON",\n        "schema_version": "3.0",\n        "output_dir":     out_dir,\n        "input_pdf_temp": pdf_dir,\n        "verification": {\n            "quantity": {\n                "file_count":   stats.get("processed", 0),\n                "total_listed": len(_list_pdfs(pdf_dir)),\n                "total_pages":  stats.get("total_pages", 0),\n                "total_tables": stats.get("total_tables", 0),\n            },\n            "quality": {\n                "errors_count": len(stats.get("errors", [])),\n                "errors":       stats.get("errors", []),\n            },\n            "speed": {"elapsed_sec": elapsed, "workers": _MAX_WORKERS},\n            "registry": {"classes": 5, "functions": 22},\n            "file_checksums": stats.get("file_checksums", {}),\n        },\n        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),\n    }\n\n    vpath = os.path.join(out_dir, "VRN_Verification_Layout.json")\n    try:\n        with open(vpath, "w", encoding="utf-8") as fh:\n            json.dump(verification, fh, ensure_ascii=False, indent=2)\n    except Exception:\n        pass\n\n    print(f"\\n[M03-Layout] Done in {elapsed}s")\n    print(f"  Processed : {stats.get(\'processed\', 0)}")\n    print(f"  Pages     : {stats.get(\'total_pages\', 0)}")\n    print(f"  Tables    : {stats.get(\'total_tables\', 0)}")\n    print(f"  Errors    : {len(stats.get(\'errors\', []))}")\n    print(f"  Verify    : {vpath}")\n    return 0\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n', 'repair': '# -*- coding: utf-8 -*-\nfrom __future__ import annotations\n"""\nVRN_MDL003_TableRestorer.py\n============================\nVERITAS REPORT NOVA -- MDL003  Table Restoration + Validation + SSOT Integration\nVersion   : 1.0.0   |   Module ID : VRN-MDL003-SUP-001\nAsset ID  : VRN-MDL003-CLS-001\nPolicy    : 功能只增不減 · append-only · SSOT · 獨立模組\n\nPIPELINE POSITION\n  mdl002_temp/           ← VRN_MDL002_Layout.json (from MDL002)\n    ↓\n  VRN_MDL003_TableRestorer  (此模組)\n    ↓\n  mdl003_temp/           ← 還原後表格 + 驗證結果 + 標準化財務數據 → MDL004+\n\nWHAT THIS MODULE DOES\n  1. Load VRN_MDL002_Layout.json from mdl002_temp\n  2. For each table record:\n     a. TEXT REPAIR (9-step R1–R9): noise → dedup → merge → OCR-fix → canonicalize\n     b. TABLE RESTORATION:\n        - Split raw_data into header_row + data_rows\n        - Align time-axis (periods) with value columns using zip()\n        - Canonicalize row labels via _CANONICAL_MAP (SynonymEngine embedded)\n        - CALC repair: fill missing values using accounting identities\n        - OCR numeric fix: l→1, O→0, bracket negatives, dash→null\n     c. FINANCIAL VALIDATION:\n        - verify_financial_arithmetic(): gross_profit = revenue - cogs\n        - Cross-check periods alignment\n        - Tag each field: RP (OCR) | CALC (derived) | API (external) | ERR (failed)\n     d. SSOT Integration:\n        - VIA_SSOT_Unified.py (if available): load and use for synonym lookup\n        - VeritasAegisNexus.py (if available): security/governance check\n        - VeritasCeleritas.py (if available): accelerator\n  3. Text block restoration:\n     - Remove OCR noise (axis numbers, watermarks)\n     - Smart sentence merge (向右向下整合直到句點)\n     - Title detection + preservation\n  4. Output restored + validated JSON/DB/Parquet\n\nANCHOR MAP\n  [VRN:ANCHOR:MDL003-META-001]   §0  Module Metadata\n  [VRN:ANCHOR:MDL003-SSOT-001]   §1  Embedded SSOT + Synonym Engine\n  [VRN:ANCHOR:MDL003-ACCEL-001]  §2  Accelerator Init\n  [VRN:ANCHOR:MDL003-DAT-001]    §3  Config / _DEFAULTS\n  [VRN:ANCHOR:MDL003-LOAD-001]   §4  MDL002 Output Loader\n  [VRN:ANCHOR:MDL003-REPAIR-001] §5  Text Repair Engine (R1–R9)\n  [VRN:ANCHOR:MDL003-RESTORE-001] §6 Table Restoration Engine\n  [VRN:ANCHOR:MDL003-CALC-001]   §7  CALC Rule Engine (accounting identities)\n  [VRN:ANCHOR:MDL003-VERIFY-001] §8  Financial Verification + Tagging (RP/CALC/API/ERR)\n  [VRN:ANCHOR:MDL003-TEXTFLOW-001] §9 Text Flow Restoration (sentence merge)\n  [VRN:ANCHOR:MDL003-EXTERNAL-001] §10 External SSOT Integration (optional)\n  [VRN:ANCHOR:MDL003-DB-001]     §11 DB Writer\n  [VRN:ANCHOR:MDL003-OUT-001]    §12 Output Assembler\n  [VRN:ANCHOR:MDL003-SYS-001]    §13 Pipeline Entry\n\nSMART ASSET REGISTRY\n  VRN-MDL003-CLS-001  VRN_MDL003_TableRestorer\n  VRN-MDL003-CLS-002  MDL003DBWriter\n  VRN-MDL003-CLS-003  TextRepairEngine\n  VRN-MDL003-CLS-004  TableRestoreEngine\n  VRN-MDL003-CLS-005  FinancialVerifier\n  VRN-MDL003-CLS-006  RestoredTable\n  VRN-MDL003-CLS-007  RestoredTextBlock\n  VRN-MDL003-FNC-001  load_mdl002_output\n  VRN-MDL003-FNC-002  canonicalize_label\n  VRN-MDL003-FNC-003  classify_fin_type\n  VRN-MDL003-FNC-004  clean_ocr_number\n  VRN-MDL003-FNC-005  is_axis_noise\n  VRN-MDL003-FNC-006  restore_one_table\n  VRN-MDL003-FNC-007  verify_financial_arithmetic\n  VRN-MDL003-FNC-008  reflow_text_blocks\n  VRN-MDL003-FNC-009  load_external_ssot\n  VRN-MDL003-FNC-010  process_one_pdf\n  VRN-MDL003-FNC-011  assemble_output\n  VRN-MDL003-FNC-012  _mdl003_accel_init\n\nOUTPUTS (mdl003_temp)\n  VRN_MDL003_Restored.json       ← 主輸出：還原表格 + 驗證結果 → MDL004+\n  VRN_MDL003_VerifySummary.json  ← 驗證摘要 (RP/CALC/API/ERR counts)\n  VRN_MDL003.db                  ← SQLite WAL\n  VRN_MDL003_Restored.parquet    ← Parquet flat (FinancialRow per record)\n  VRN_MDL003_Restored.csv        ← CSV (UTF-8 BOM)\n  VRN_MDL003_TextFlow.json       ← 還原文字段落 (for RAG/LLM)\n\nSSOT INTEGRATION PATHS\n  supportive_module/VIA_SSOT_Unified.py      ← optional synonym extension\n  supportive_module/VeritasAegisNexus.py     ← optional governance check\n  supportive_module/VeritasCeleritas.py      ← optional acceleration\n\nLL RULES: #10 #12 #13 #15 #17 #18 #19 #20\n"""\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-META-001] §0\n# ============================================================================\n\n__version__   = "1.0.0"\n__module_id__ = "VRN-MDL003-SUP-001"\n__asset_id__  = "VRN-MDL003-CLS-001"\n__author__    = "VRN Team"\n__domain__    = "RESTORE_VALIDATE"\n\n# ============================================================================\n# STDLIB\n# ============================================================================\n\nimport os, sys, re, json, time, math, hashlib, logging, sqlite3, csv, io\nimport gc, argparse, threading, warnings, collections, copy\nfrom pathlib import Path\nfrom typing import Any, Dict, List, Optional, Tuple\nfrom dataclasses import dataclass, field\nfrom concurrent.futures import ThreadPoolExecutor, as_completed\n\nwarnings.filterwarnings("ignore")\n\ndef _si(n):\n    try: import importlib; return importlib.import_module(n)\n    except: return None\n\npd       = _si("pandas")\npyarrow  = _si("pyarrow")\norjson   = _si("orjson")\nxxhash   = _si("xxhash")\nfitz     = _si("fitz")\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-SSOT-001] §1  EMBEDDED SSOT + SYNONYM ENGINE\n# ============================================================================\n\n# THREE LOCKED TW TICKER REGEX — IMMUTABLE\nTW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})")\nTW_BLOOMBERG_REGEX = re.compile(r"\\b(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})\\s+TT\\b")\nTW_YFINANCE_REGEX  = re.compile(r"\\b(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})\\.(TW|TWO)\\b")\n\n# ── Canonical Map (append-only — never remove existing entries) ───────────────\n_CANONICAL_MAP: Dict[str, str] = {\n    # ── Revenue ──────────────────────────────────────────────────────────────\n    "營業收入淨額":"revenue", "營業收入":"revenue", "收入":"revenue",\n    "Revenue":"revenue", "Net Revenue":"revenue", "Net Sales":"revenue",\n    "营收":"revenue", "Sales":"revenue", "Total Revenue":"revenue",\n    # ── COGS ─────────────────────────────────────────────────────────────────\n    "營業成本":"cogs", "Cost of Revenue":"cogs", "COGS":"cogs",\n    "Cost of Sales":"cogs", "销售成本":"cogs", "营业成本":"cogs",\n    # ── Gross Profit ─────────────────────────────────────────────────────────\n    "營業毛利淨額":"gross_profit", "毛利":"gross_profit", "Gross Profit":"gross_profit",\n    "营业毛利淨額":"gross_profit",\n    # ── OpEx ─────────────────────────────────────────────────────────────────\n    "營業費用":"opex", "Operating Expense":"opex", "OpEx":"opex",\n    "SG&A":"opex", "营业費用":"opex",\n    # ── Operating Income ─────────────────────────────────────────────────────\n    "營業淨利/損":"operating_income", "營業利益":"operating_income",\n    "Operating Income":"operating_income", "EBIT":"operating_income",\n    "营业淨利/損":"operating_income",\n    # ── Pre-tax ──────────────────────────────────────────────────────────────\n    "稅前淨利":"pretax_income", "Pretax Income":"pretax_income",\n    "Pre-tax Income":"pretax_income", "税前淨利":"pretax_income",\n    # ── Net Income ───────────────────────────────────────────────────────────\n    "稅後淨利":"net_income", "Net Income":"net_income",\n    "Net Profit":"net_income", "税後淨利":"net_income",\n    "歸屬母公司淨利":"net_income_parent", "Attributable Net":"net_income_parent",\n    # ── EPS ──────────────────────────────────────────────────────────────────\n    "每股盈餘(元)":"eps", "每股盈餘":"eps", "EPS":"eps",\n    "EPS (NT$)":"eps", "Basic EPS":"basic_eps", "Diluted EPS":"diluted_eps",\n    "每股净利":"eps",\n    # ── Margins ──────────────────────────────────────────────────────────────\n    "毛利率":"gross_margin", "Gross Margin":"gross_margin",\n    "營業利益率":"operating_margin", "Operating Margin":"operating_margin",\n    "淨利率":"net_margin", "Net Margin":"net_margin",\n    # ── Growth ───────────────────────────────────────────────────────────────\n    "營收成長率":"revenue_growth", "Revenue Growth":"revenue_growth",\n    "YoY":"yoy_growth", "QoQ":"qoq_growth",\n    # ── Per-share ────────────────────────────────────────────────────────────\n    "每股淨值":"bvps", "BVPS":"bvps", "Book Value Per Share":"bvps",\n    "每股現金股利":"dps", "DPS":"dps", "Dividend Per Share":"dps",\n    # ── Valuation ────────────────────────────────────────────────────────────\n    "本益比(P/E)":"pe_ratio", "P/E":"pe_ratio", "本益比":"pe_ratio",\n    "股價淨值比":"pb_ratio", "P/B":"pb_ratio", "PBR":"pb_ratio",\n    "殖利率":"dividend_yield", "Dividend Yield":"dividend_yield",\n    # ── Balance Sheet ────────────────────────────────────────────────────────\n    "總資產":"total_assets", "Total Assets":"total_assets",\n    "總負債":"total_liabilities", "Total Liabilities":"total_liabilities",\n    "股東權益":"total_equity", "Total Equity":"total_equity",\n    "流動資產":"current_assets", "Current Assets":"current_assets",\n    "現金及約當現金":"cash", "Cash":"cash",\n    # ── Cash Flow ────────────────────────────────────────────────────────────\n    "來自營業活動現金":"operating_cf", "Operating CF":"operating_cf",\n    "投資活動現金":"investing_cf", "Investing CF":"investing_cf",\n    "自由現金流量":"free_cf", "Free Cash Flow":"free_cf", "FCF":"free_cf",\n    "資本支出":"capex", "CapEx":"capex",\n    # ── ROE/ROA ──────────────────────────────────────────────────────────────\n    "股東權益報酬率":"roe", "ROE":"roe",\n    "資產報酬率":"roa", "ROA":"roa",\n}\n\n# ── Fin type classifier ───────────────────────────────────────────────────────\n_IS_FIELDS = {"revenue","cogs","gross_profit","opex","operating_income",\n              "pretax_income","net_income","net_income_parent","eps","basic_eps",\n              "diluted_eps","gross_margin","operating_margin","net_margin",\n              "revenue_growth","yoy_growth","qoq_growth"}\n_BS_FIELDS = {"total_assets","total_liabilities","total_equity","current_assets",\n              "cash","inventory","accounts_receivable","property_plant"}\n_CF_FIELDS = {"operating_cf","investing_cf","financing_cf","free_cf","capex"}\n_VL_FIELDS = {"pe_ratio","pb_ratio","dividend_yield","bvps","dps","roe","roa",\n              "peg_ratio","ev_ebitda"}\n\n# ── CALC identity rules ───────────────────────────────────────────────────────\n# Format: target_field: (operand_a, operand_b, operator)\nCALC_RULES: Dict[str, Tuple[str, str, str]] = {\n    "gross_profit":      ("revenue",       "cogs",               "sub"),\n    "operating_income":  ("gross_profit",  "opex",               "sub"),\n    "net_income":        ("pretax_income", None,                 "approx"),  # approx only\n    "gross_margin":      ("gross_profit",  "revenue",            "div"),\n    "operating_margin":  ("operating_income","revenue",          "div"),\n    "net_margin":        ("net_income",    "revenue",            "div"),\n}\n\n# Noise patterns for text (chart axis, watermarks, etc.)\n_NOISE_RE = re.compile(\n    r"\\{.*?\\}|[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]"\n    r"|(?<!\\w)[lO\\|](?=[\\d,])|(?<=[\\d,])[lO\\|](?!\\w)"\n    r"|(?:^|\\n)[-+]?\\s*\\d+\\s*-\\s*(?=\\n|$)"   # page number dash: - 1 -\n)\n_AXIS_RE1 = re.compile(r"^[-+]?[\\d\\s,\\.]+%?$")\n_AXIS_RE2 = re.compile(r"^(?:[-+]?\\d{1,3}(?:\\.\\d+)?[%O]?\\s*){4,}$")\n_AXIS_RE3 = re.compile(r"^\\s*(\\d+[OBoS]+|[sS]o+|JO+|I+)\\s*$")\n\n# Time-period detection\n_PERIOD_RE = re.compile(\n    r"(20\\d{2}[AEFaefCTct]?|\\d{1,2}Q\\d{2}|[Ff][Yy]\\d{2}[AEae]?|"\n    r"\\d{4}[Qq]\\d|2[0-9][A-Z]{1,2})"\n)\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-ACCEL-001] §2\n# ============================================================================\n\ndef _mdl003_accel_init(workers: int = 0) -> Dict:\n    """VRN-MDL003-FNC-012"""\n    w = workers or max(1, (os.cpu_count() or 4) - 1)\n    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",\n                "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):\n        os.environ.setdefault(var, str(w))\n    gc.set_threshold(50_000, 500, 50)\n    return {"workers": w, "pyarrow": pyarrow is not None, "fitz": fitz is not None}\n\nlogging.basicConfig(\n    level=logging.INFO,\n    format="[%(asctime)s][%(levelname)s] %(message)s",\n    datefmt="%H:%M:%S"\n)\nlog = logging.getLogger(__name__)\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-DAT-001] §3\n# ============================================================================\n\n_DEFAULTS = dict(\n    mdl002_temp  = r"C:\\VeritasIntelligenceAnalytics\\VeritasReportNova\\temp\\mdl002_temp",\n    mdl003_temp  = r"C:\\VeritasIntelligenceAnalytics\\VeritasReportNova\\temp\\mdl003_temp",\n    ssot_dir     = r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module",\n    workers      = 0,\n    enable_db    = True,\n    zero_error   = True,\n    enable_calc  = True,     # apply CALC identity repair\n    min_rows     = 2,        # minimum rows to keep a restored table\n    min_cols     = 2,        # minimum cols to keep a restored table\n    text_reflow  = True,     # enable sentence merge\n)\n\n# ============================================================================\n# UTILITIES\n# ============================================================================\n\ndef _hash8(s: str) -> str:\n    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()\n    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()\n\ndef _jwrite(p: str, data: Any):\n    def _def(o): return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)\n    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_def), encoding="utf-8")\n\ndef _jload(p: str) -> Any:\n    try:\n        txt = Path(p).read_text(encoding="utf-8")\n        if orjson: return orjson.loads(txt)\n        return json.loads(txt)\n    except Exception as e: log.warning("[MDL003] jload %s: %s", p, e); return None\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-LOAD-001] §4  MDL002 LOADER\n# ============================================================================\n\ndef load_mdl002_output(mdl002_temp: str) -> Optional[Dict]:\n    """VRN-MDL003-FNC-001  Load VRN_MDL002_Layout.json."""\n    path = Path(mdl002_temp) / "VRN_MDL002_Layout.json"\n    if not path.exists():\n        log.error("[MDL003] VRN_MDL002_Layout.json not found in: %s", mdl002_temp)\n        return None\n    data = _jload(str(path))\n    if not data or not data.get("reports"):\n        log.error("[MDL003] VRN_MDL002_Layout.json is empty or invalid")\n        return None\n    log.info("[MDL003] Loaded MDL002: %d PDF reports", len(data["reports"]))\n    return data\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-REPAIR-001] §5  TEXT REPAIR ENGINE\n# ============================================================================\n\nclass TextRepairEngine:\n    """VRN-MDL003-CLS-003\n    9-step repair pipeline:\n    R1 — encoding noise removal (watermarks, control chars)\n    R2 — duplicate line dedup\n    R3 — right-broken line merge (continuation to sentence end)\n    R4 — normalize CJK spaces, trim\n    R5 — header de-duplication (repeated column headers removed)\n    R6 — empty/stub line removal (len<2)\n    R7 — OCR numeric fix (l→1, O→0 in numeric context)\n    R8 — axis noise filter (chart coordinate numbers)\n    R9 — label canonicalization hint\n    """\n\n    _OCR_NUM_RE = re.compile(r"(?<!\\w)([lO\\|])(?=[\\d,])|(?<=[\\d,])([lO\\|])(?!\\w)")\n    # Chinese char space removal\n    _ZH_SPACE_RE = re.compile(r"(?<=[\\u4e00-\\u9fa5])\\s+(?=[\\u4e00-\\u9fa5])")\n\n    def repair_text_blocks(self, blocks: List[Dict], reflow: bool = True) -> List[Dict]:\n        """Apply R1–R8 to text blocks, optionally merge sentences."""\n        seen   = set()\n        result = []\n        for blk in blocks:\n            text = blk.get("text", "")\n            # R1: remove noise\n            text = _NOISE_RE.sub(" ", text).strip()\n            # R4: normalize spaces\n            text = text.replace("\\u3000", " ").replace("\\u00a0", " ")\n            text = self._ZH_SPACE_RE.sub("", text)\n            text = re.sub(r" {2,}", " ", text)\n            # R6: empty\n            if not text or len(text) < 2: continue\n            # R8: axis noise\n            if is_axis_noise(text): continue\n            # R2: dedup\n            key = _hash8(text[:80])\n            if key in seen: continue\n            seen.add(key)\n            blk = dict(blk); blk["text"] = text\n            result.append(blk)\n\n        if not reflow: return result\n\n        # R3: sentence merge (向右向下整合直到句點)\n        merged = []\n        buf_text = ""\n        buf_blk  = None\n        for blk in result:\n            text    = blk.get("text", "")\n            is_tbl  = blk.get("block_type","") == "table"\n            is_title= blk.get("is_title", False) or len(text) < 20\n\n            if is_tbl or is_title:\n                if buf_text and buf_blk:\n                    merged.append(dict(buf_blk, text=buf_text.strip()))\n                    buf_text = ""; buf_blk = None\n                merged.append(blk)\n                continue\n\n            buf_text += text\n            buf_blk   = blk\n            # Sentence end?\n            if re.search(r"[。！？.!?]$", buf_text.strip()):\n                merged.append(dict(buf_blk, text=buf_text.strip()))\n                buf_text = ""; buf_blk = None\n\n        if buf_text and buf_blk:\n            merged.append(dict(buf_blk, text=buf_text.strip()))\n        return merged\n\n    def repair_table_label(self, label: str) -> str:\n        """R7: OCR numeric fix on label."""\n        label = self._OCR_NUM_RE.sub(\n            lambda m: "1" if (m.group(1) or m.group(2)) in "lL|" else "0", label\n        )\n        return label.strip()\n\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-RESTORE-001] §6  TABLE RESTORATION ENGINE\n# ============================================================================\n\ndef canonicalize_label(label: str) -> str:\n    """VRN-MDL003-FNC-002  Map raw label → canonical field name."""\n    if label in _CANONICAL_MAP: return _CANONICAL_MAP[label]\n    norm = re.sub(r"[\\s/（）()（）%,，]", "", label)\n    for k, v in _CANONICAL_MAP.items():\n        if re.sub(r"[\\s/（）()（）%,，]", "", k) == norm: return v\n    for k, v in _CANONICAL_MAP.items():\n        if k.lower() in label.lower() or label.lower() in k.lower(): return v\n    return label.lower().replace(" ", "_")[:40]\n\ndef classify_fin_type(canonical: str) -> str:\n    """VRN-MDL003-FNC-003"""\n    if canonical in _IS_FIELDS: return "income_statement"\n    if canonical in _BS_FIELDS: return "balance_sheet"\n    if canonical in _CF_FIELDS: return "cash_flow"\n    if canonical in _VL_FIELDS: return "valuation"\n    return "other"\n\ndef clean_ocr_number(val: str) -> Optional[float]:\n    """VRN-MDL003-FNC-004  Convert raw cell string to float or None."""\n    if not val: return None\n    val = str(val).strip()\n    # Special strings → null\n    if val in ("--", "---", "n.a.", "N/A", "NA", "nm", "NM",\n               "盈轉虧", "虧轉盈", "-", "—", ""):\n        return None\n    # Remove thousands separators and spaces\n    val = val.replace(",", "").replace("，", "").replace(" ", "").replace("\\u00a0","")\n    # Bracket negative: (268) → -268\n    val = re.sub(r"^\\((.*?)\\)$", r"-\\1", val)\n    # Percentage: 48.5% → 48.5\n    val = val.replace("%", "")\n    # OCR: O→0, l→1 in pure numeric context\n    val = re.sub(r"(?<!\\w)O(?=\\d)|(?<=\\d)O(?!\\w)", "0", val)\n    try:\n        return float(val)\n    except ValueError:\n        return None\n\ndef is_axis_noise(text: str) -> bool:\n    """VRN-MDL003-FNC-005  Detect chart axis coordinate noise."""\n    t = text.strip()\n    if _AXIS_RE1.match(t): return True\n    if _AXIS_RE2.match(t): return True\n    if _AXIS_RE3.match(t): return True\n    return False\n\n@dataclass\nclass RestoredTable:\n    """VRN-MDL003-CLS-006  One restored financial table."""\n    region_id:        str = ""\n    pdf_name:         str = ""\n    report_code:      str = ""\n    page_no:          int = 0\n    region_type:      str = ""\n    quadrant:         str = ""\n    is_financial:     bool = False\n    periods:          List[str] = field(default_factory=list)\n    rows: List[Dict] = field(default_factory=list)\n    # Format per row: {label_raw, canonical, fin_type, values: {period: float|None}, sources: {period: "RP"|"CALC"|"ERR"}}\n    calc_applied:     int = 0\n    err_count:        int = 0\n    ok:               bool = False\n    error:            Optional[str] = None\n\ndef restore_one_table(\n    tbl_dict: Dict,\n    repair: TextRepairEngine,\n    cfg:    Dict,\n) -> RestoredTable:\n    """VRN-MDL003-FNC-006  Core table restoration logic."""\n    rt = RestoredTable(\n        region_id    = tbl_dict.get("region_id", ""),\n        pdf_name     = tbl_dict.get("pdf_name", ""),\n        report_code  = tbl_dict.get("report_code", ""),\n        page_no      = tbl_dict.get("page_no", 0),\n        region_type  = tbl_dict.get("region_type", ""),\n        quadrant     = tbl_dict.get("quadrant", "full"),\n        is_financial = tbl_dict.get("is_financial", False),\n    )\n\n    raw_data: List[List[str]] = tbl_dict.get("raw_data", [])\n    if not raw_data or len(raw_data) < 2:\n        rt.error = "insufficient_rows"; return rt\n\n    # ── Step 1: Extract periods from header row(s) ───────────────────────────\n    periods: List[str] = []\n    data_start_row = 0\n    for row_idx in range(min(3, len(raw_data))):\n        row = raw_data[row_idx] or []\n        row_periods = []\n        for cell in row:\n            cell_s = str(cell or "").strip()\n            m = _PERIOD_RE.findall(cell_s)\n            if m: row_periods.extend(m)\n        if len(row_periods) >= 2:\n            periods = list(dict.fromkeys(row_periods))  # dedup preserve order\n            data_start_row = row_idx + 1\n            break\n\n    # Use MDL002\'s detected periods as fallback\n    if not periods:\n        periods = tbl_dict.get("header_periods", [])\n\n    rt.periods = periods\n\n    # ── Step 2: Parse data rows ──────────────────────────────────────────────\n    rows_out: List[Dict] = []\n    for row in raw_data[data_start_row:]:\n        if not row: continue\n        label_raw = repair.repair_table_label(str(row[0] or "").strip())\n        if not label_raw or len(label_raw) < 1: continue\n        # Skip header repeat rows (all periods/years in label)\n        if re.fullmatch(r"[\\s\\d年QEFefCTctat\\-/]+", label_raw): continue\n\n        canonical = canonicalize_label(label_raw)\n        fin_type  = classify_fin_type(canonical)\n\n        # Parse numeric values\n        values_raw: List[str] = [str(c or "").strip() for c in row[1:]]\n        values_map: Dict[str, Optional[float]] = {}\n        sources_map: Dict[str, str] = {}\n\n        for ci, v_raw in enumerate(values_raw):\n            period = periods[ci] if ci < len(periods) else f"col{ci}"\n            v_num  = clean_ocr_number(v_raw)\n            values_map[period]  = v_num\n            sources_map[period] = "RP" if v_num is not None else "ERR"\n            if v_num is None and v_raw not in ("", "--", "---", "n.a.", "N/A"):\n                rt.err_count += 1\n\n        rows_out.append({\n            "label_raw":    label_raw,\n            "canonical":    canonical,\n            "fin_type":     fin_type,\n            "values":       values_map,\n            "sources":      sources_map,\n        })\n\n    rt.rows = rows_out\n\n    if len(rt.rows) >= cfg.get("min_rows", 2):\n        rt.ok = True\n    else:\n        rt.error = f"too_few_rows: {len(rt.rows)}"\n\n    return rt\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-CALC-001] §7  CALC RULE ENGINE\n# ============================================================================\n\ndef apply_calc_rules(rt: RestoredTable) -> RestoredTable:\n    """VRN-MDL003-FNC: Apply accounting identities to fill ERR cells.\n    For each period, if target field is None (ERR) but operands are available → CALC.\n    """\n    # Build lookup: canonical → row dict\n    row_by_canonical: Dict[str, Dict] = {}\n    for row in rt.rows:\n        row_by_canonical[row["canonical"]] = row\n\n    for target, (a_field, b_field, op) in CALC_RULES.items():\n        if target not in row_by_canonical: continue\n        tgt_row = row_by_canonical[target]\n\n        for period in rt.periods:\n            if tgt_row["sources"].get(period) in ("RP", "CALC"): continue  # already valid\n            # Look up operands\n            a_val = None\n            b_val = None\n            if a_field in row_by_canonical:\n                a_val = row_by_canonical[a_field]["values"].get(period)\n            if b_field and b_field in row_by_canonical:\n                b_val = row_by_canonical[b_field]["values"].get(period)\n\n            calc_val: Optional[float] = None\n            if op == "sub" and a_val is not None and b_val is not None:\n                calc_val = round(a_val - b_val, 4)\n            elif op == "div" and a_val is not None and b_val and abs(b_val) > 0:\n                calc_val = round(a_val / b_val, 6)\n            elif op == "approx" and a_val is not None:\n                # Just propagate operand a as approximation (pretax ≈ net)\n                calc_val = a_val\n\n            if calc_val is not None:\n                tgt_row["values"][period]  = calc_val\n                tgt_row["sources"][period] = "CALC"\n                rt.calc_applied += 1\n\n    return rt\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-VERIFY-001] §8  FINANCIAL VERIFICATION\n# ============================================================================\n\ndef verify_financial_arithmetic(rt: RestoredTable) -> Dict:\n    """VRN-MDL003-FNC-007  Cross-check key accounting identities."""\n    results = []\n    # Build lookup\n    by_canon: Dict[str, Dict] = {r["canonical"]: r for r in rt.rows}\n\n    checks = [\n        ("gross_profit", "revenue", "cogs", "sub"),\n        ("operating_income", "gross_profit", "opex", "sub"),\n        ("gross_margin", "gross_profit", "revenue", "div"),\n        ("operating_margin", "operating_income", "revenue", "div"),\n    ]\n    for target, a_f, b_f, op in checks:\n        if target not in by_canon or a_f not in by_canon: continue\n        tgt = by_canon[target]\n        a_r = by_canon[a_f]\n        b_r = by_canon.get(b_f, {})\n\n        for period in rt.periods:\n            t_v = tgt["values"].get(period)\n            a_v = a_r["values"].get(period)\n            b_v = b_r.get("values", {}).get(period) if b_r else None\n\n            if t_v is None or a_v is None: continue\n            if op == "sub" and b_v is not None:\n                expected = a_v - b_v\n                pct_diff = abs(t_v - expected) / (abs(expected) + 1e-6)\n                ok = pct_diff < 0.02  # 2% tolerance\n                results.append({\n                    "check":    f"{target}={a_f}-{b_f}",\n                    "period":   period,\n                    "ok":       ok,\n                    "expected": round(expected, 2),\n                    "actual":   round(t_v, 2),\n                    "diff_pct": round(pct_diff * 100, 2),\n                })\n            elif op == "div" and b_v and abs(b_v) > 0:\n                expected = a_v / b_v\n                pct_diff = abs(t_v - expected) / (abs(expected) + 1e-6)\n                ok = pct_diff < 0.05  # 5% for ratios\n                results.append({\n                    "check":  f"{target}={a_f}/{b_f}",\n                    "period": period,\n                    "ok":     ok,\n                    "diff_pct": round(pct_diff * 100, 2),\n                })\n\n    pass_count = sum(1 for r in results if r["ok"])\n    return {\n        "checks":     len(results),\n        "pass":       pass_count,\n        "fail":       len(results) - pass_count,\n        "details":    results,\n    }\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-TEXTFLOW-001] §9  TEXT FLOW RESTORATION\n# ============================================================================\n\ndef reflow_text_blocks(blocks: List[Dict], repair: TextRepairEngine) -> List[Dict]:\n    """VRN-MDL003-FNC-008  Apply full text repair + sentence merge."""\n    return repair.repair_text_blocks(blocks, reflow=True)\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-EXTERNAL-001] §10  EXTERNAL SSOT INTEGRATION\n# ============================================================================\n\n\ndef _cel_submit(fn, *args, **kw):\n    """Submit via Celeritas _LazyPool if available, else direct call."""\n    if _CEL_OK:\n        if hasattr(_CEL, "_LazyPool"):\n            try: return _CEL._LazyPool.submit(fn, *args, **kw)\n            except Exception: pass\n        if hasattr(_CEL, "submit"):\n            try: return _CEL.submit(fn, *args, **kw)\n            except Exception: pass\n    return fn(*args, **kw)\n\ndef load_external_ssot(ssot_dir: str) -> Dict:\n    """VRN-MDL003-FNC-009  Try to load supportive modules and extend _CANONICAL_MAP."""\n    result = {"via_ssot": False, "aegis": False, "celeritas": False, "super_engine": False}\n    ssot_path = Path(ssot_dir)\n    if not ssot_path.is_dir(): return result\n\n    # Add ssot_dir to sys.path temporarily\n    ssot_str = str(ssot_path)\n    if ssot_str not in sys.path:\n        sys.path.insert(0, ssot_str)\n\n    # VIA_SSOT_Unified\n    try:\n        import importlib\n        via_ssot = importlib.import_module("VIA_SSOT_Unified")\n        # Attempt to merge synonym maps if available\n        if hasattr(via_ssot, "CANONICAL_MAP"):\n            ext_map: Dict = getattr(via_ssot, "CANONICAL_MAP", {})\n            for k, v in ext_map.items():\n                if k not in _CANONICAL_MAP:  # append-only\n                    _CANONICAL_MAP[k] = v\n            log.info("[MDL003] VIA_SSOT_Unified: merged %d new entries", len(ext_map))\n        result["via_ssot"] = True\n    except Exception as e:\n        log.debug("[MDL003] VIA_SSOT_Unified not loaded: %s", e)\n\n    # VeritasAegisNexus\n    try:\n        aegis = importlib.import_module("VeritasAegisNexus")\n        result["aegis"] = True\n        log.info("[MDL003] VeritasAegisNexus loaded")\n    except Exception as e:\n        log.debug("[MDL003] VeritasAegisNexus not loaded: %s", e)\n\n    # VeritasCeleritas — spec/exec with sys.modules inject (Python 3.12 @dataclass fix)\n    try:\n        import importlib.util as _ilu3\n        _cel_paths = [Path(ssot_dir)/"VeritasCeleritas.py",\n                      Path(ssot_dir).parent/"VeritasCeleritas.py"]\n        for _cp in _cel_paths:\n            if _cp.exists():\n                _spec3 = _ilu3.spec_from_file_location("VeritasCeleritas", str(_cp))\n                _mod3  = _ilu3.module_from_spec(_spec3)\n                sys.modules["VeritasCeleritas"] = _mod3   # inject before exec (Py3.12)\n                _spec3.loader.exec_module(_mod3)\n                result["celeritas"] = True\n                if hasattr(_mod3, "bootstrap_at_import"): _mod3.bootstrap_at_import(__file__)\n                if hasattr(_mod3, "warm_thread_pool"):    _mod3.warm_thread_pool()\n                log.info("[MDL003] VeritasCeleritas loaded from %s", _cp)\n                break\n    except Exception as e:\n        log.debug("[MDL003] VeritasCeleritas not loaded: %s", e)\n\n    # super_engine — spec/exec with sys.modules inject (Py3.12)\n    try:\n        import importlib.util as _ilu3s\n        _se_paths = [Path(ssot_dir)/"super_engine.py",\n                     Path(ssot_dir).parent/"super_engine.py"]\n        for _sp in _se_paths:\n            if _sp.exists():\n                _spec3s = _ilu3s.spec_from_file_location("super_engine", str(_sp))\n                _mod3s  = _ilu3s.module_from_spec(_spec3s)\n                sys.modules["super_engine"] = _mod3s\n                _spec3s.loader.exec_module(_mod3s)\n                result["super_engine"] = True\n                log.info("[MDL003] super_engine loaded from %s", _sp)\n                break\n    except Exception as e:\n        log.debug("[MDL003] super_engine not loaded: %s", e)\n\n    return result\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-DB-001] §11  DB WRITER\n# ============================================================================\n\nclass MDL003DBWriter:\n    """VRN-MDL003-CLS-002"""\n\n    DDL = """\nCREATE TABLE IF NOT EXISTS vrn_mdl003_financial_rows (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    region_id TEXT, pdf_name TEXT, report_code TEXT,\n    page_no INTEGER, region_type TEXT, quadrant TEXT,\n    label_raw TEXT, canonical TEXT, fin_type TEXT,\n    period TEXT, value REAL, source TEXT,\n    calc_applied INTEGER DEFAULT 0,\n    ts TEXT DEFAULT (datetime(\'now\',\'localtime\'))\n);\nCREATE TABLE IF NOT EXISTS vrn_mdl003_verify_results (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    region_id TEXT, pdf_name TEXT, report_code TEXT,\n    check_name TEXT, period TEXT, ok INTEGER,\n    expected REAL, actual REAL, diff_pct REAL,\n    ts TEXT DEFAULT (datetime(\'now\',\'localtime\'))\n);\nCREATE TABLE IF NOT EXISTS vrn_mdl003_text_flow (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    block_id TEXT, pdf_name TEXT, report_code TEXT,\n    page_no INTEGER, block_type TEXT, text TEXT,\n    is_title INTEGER, is_bold INTEGER, font_size REAL,\n    ts TEXT DEFAULT (datetime(\'now\',\'localtime\'))\n);\n"""\n    def __init__(self, db_path: str):\n        self.db_path = db_path\n        self._con    = sqlite3.connect(db_path, check_same_thread=False)\n        self._lock   = threading.Lock()\n        self._con.execute("PRAGMA journal_mode=WAL")\n        self._con.execute("PRAGMA synchronous=NORMAL")\n        self._con.executescript(self.DDL)\n        self._con.commit()\n\n    def insert_financial_rows(self, rt: RestoredTable):\n        sql = """INSERT INTO vrn_mdl003_financial_rows\n                 (region_id,pdf_name,report_code,page_no,region_type,quadrant,\n                  label_raw,canonical,fin_type,period,value,source,calc_applied)\n                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""\n        rows_flat = []\n        for row in rt.rows:\n            for period, val in row["values"].items():\n                src = row["sources"].get(period, "ERR")\n                rows_flat.append((\n                    rt.region_id, rt.pdf_name, rt.report_code,\n                    rt.page_no, rt.region_type, rt.quadrant,\n                    row["label_raw"], row["canonical"], row["fin_type"],\n                    period, val, src, rt.calc_applied,\n                ))\n        with self._lock:\n            self._con.executemany(sql, rows_flat)\n            self._con.commit()\n\n    def insert_verify(self, rt: RestoredTable, verify: Dict):\n        sql = """INSERT INTO vrn_mdl003_verify_results\n                 (region_id,pdf_name,report_code,check_name,period,ok,expected,actual,diff_pct)\n                 VALUES (?,?,?,?,?,?,?,?,?)"""\n        with self._lock:\n            for det in verify.get("details", []):\n                self._con.execute(sql, (\n                    rt.region_id, rt.pdf_name, rt.report_code,\n                    det.get("check",""), det.get("period",""),\n                    1 if det.get("ok") else 0,\n                    det.get("expected"), det.get("actual"), det.get("diff_pct"),\n                ))\n            self._con.commit()\n\n    def insert_text_flow(self, blocks: List[Dict]):\n        sql = """INSERT INTO vrn_mdl003_text_flow\n                 (block_id,pdf_name,report_code,page_no,block_type,text,is_title,is_bold,font_size)\n                 VALUES (?,?,?,?,?,?,?,?,?)"""\n        with self._lock:\n            for b in blocks:\n                self._con.execute(sql, (\n                    b.get("block_id",""), b.get("pdf_name",""),\n                    b.get("report_code",""), b.get("page_no",0),\n                    b.get("block_type",""), b.get("text",""),\n                    1 if b.get("is_title") else 0,\n                    1 if b.get("is_bold") else 0,\n                    b.get("font_size",0.0),\n                ))\n            self._con.commit()\n\n    def export_parquet(self, out_dir: str):\n        if not pd or not pyarrow: return\n        try:\n            df = pd.read_sql("SELECT * FROM vrn_mdl003_financial_rows", self._con)\n            df.to_parquet(str(Path(out_dir) / "VRN_MDL003_Restored.parquet"), index=False)\n        except Exception as e: log.warning("[MDL003] parquet: %s", e)\n\n    def export_csv(self, out_dir: str):\n        if not pd: return\n        try:\n            df = pd.read_sql("SELECT * FROM vrn_mdl003_financial_rows", self._con)\n            df.to_csv(str(Path(out_dir) / "VRN_MDL003_Restored.csv"),\n                      index=False, encoding="utf-8-sig")\n        except Exception as e: log.warning("[MDL003] csv: %s", e)\n\n# ============================================================================\n# CORE PROCESSOR\n# ============================================================================\n\ndef process_one_pdf(\n    pdf_report: Dict,\n    cfg:        Dict,\n    repair:     TextRepairEngine,\n    db:         Optional[MDL003DBWriter],\n) -> Dict:\n    """VRN-MDL003-FNC-010  Restore all tables + text for one PDF report."""\n    t0          = time.perf_counter()\n    pdf_name    = pdf_report.get("pdf_name", "")\n    report_code = pdf_report.get("report_code", "")\n\n    out = {\n        "pdf_name":          pdf_name,\n        "report_code":       report_code,\n        "ticker":            pdf_report.get("ticker", ""),\n        "report_date":       pdf_report.get("report_date", ""),\n        "broker_abbr":       pdf_report.get("broker_abbr", ""),\n        "n_tables_in":       len(pdf_report.get("tables", [])),\n        "n_tables_restored": 0,\n        "n_tables_ok":       0,\n        "n_financial_tables":0,\n        "n_calc_applied":    0,\n        "n_err":             0,\n        "n_verify_pass":     0,\n        "n_verify_fail":     0,\n        "n_text_blocks_in":  len(pdf_report.get("text_blocks", [])),\n        "n_text_blocks_out": 0,\n        "restored_tables":   [],\n        "text_flow":         [],\n        "ok":                False,\n        "error":             None,\n        "elapsed":           0.0,\n    }\n\n    try:\n        # ── Restore tables ─────────────────────────────────────────────────\n        for tbl_dict in pdf_report.get("tables", []):\n            rt = restore_one_table(tbl_dict, repair, cfg)\n\n            # Apply CALC rules\n            if cfg.get("enable_calc", True) and rt.ok:\n                rt = apply_calc_rules(rt)\n                out["n_calc_applied"] += rt.calc_applied\n\n            out["n_err"] += rt.err_count\n\n            # Verify arithmetic\n            verify_result = {}\n            if rt.ok and rt.is_financial:\n                verify_result = verify_financial_arithmetic(rt)\n                out["n_verify_pass"] += verify_result.get("pass", 0)\n                out["n_verify_fail"] += verify_result.get("fail", 0)\n\n            out["n_tables_restored"] += 1\n            if rt.ok:\n                out["n_tables_ok"] += 1\n            if rt.is_financial:\n                out["n_financial_tables"] += 1\n\n            # Serialize restored table\n            rt_dict = {\n                "region_id":    rt.region_id,\n                "pdf_name":     rt.pdf_name,\n                "report_code":  rt.report_code,\n                "page_no":      rt.page_no,\n                "region_type":  rt.region_type,\n                "quadrant":     rt.quadrant,\n                "is_financial": rt.is_financial,\n                "periods":      rt.periods,\n                "rows":         rt.rows,\n                "calc_applied": rt.calc_applied,\n                "err_count":    rt.err_count,\n                "ok":           rt.ok,\n                "error":        rt.error,\n                "verify":       verify_result,\n            }\n            out["restored_tables"].append(rt_dict)\n\n            if db:\n                try:\n                    if rt.ok: db.insert_financial_rows(rt)\n                    if verify_result: db.insert_verify(rt, verify_result)\n                except Exception as e:\n                    log.warning("[MDL003] DB rows %s: %s", rt.region_id, e)\n\n        # ── Restore text ───────────────────────────────────────────────────\n        if cfg.get("text_reflow", True):\n            raw_blocks = pdf_report.get("text_blocks", [])\n            flowed = reflow_text_blocks(raw_blocks, repair)\n            out["n_text_blocks_out"] = len(flowed)\n            out["text_flow"] = flowed\n\n            if db and flowed:\n                try: db.insert_text_flow(flowed)\n                except Exception as e:\n                    log.warning("[MDL003] DB text %s: %s", pdf_name, e)\n\n        out["ok"] = True\n\n    except Exception as e:\n        out["error"] = str(e)\n        log.error("[MDL003] process_one_pdf %s: %s", pdf_name, e)\n\n    out["elapsed"] = round(time.perf_counter() - t0, 2)\n    log.info("[MDL003] %s: tables=%d/%d  fin=%d  calc=%d  err=%d  txt=%d  %.2fs",\n             pdf_name, out["n_tables_ok"], out["n_tables_restored"],\n             out["n_financial_tables"], out["n_calc_applied"],\n             out["n_err"], out["n_text_blocks_out"], out["elapsed"])\n    return out\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-OUT-001] §12\n# ============================================================================\n\ndef assemble_output(results: List[Dict]) -> Dict:\n    """VRN-MDL003-FNC-011"""\n    ok_count = sum(1 for r in results if r.get("ok"))\n    return {\n        "module":              __module_id__,\n        "version":             __version__,\n        "generated":           time.strftime("%Y-%m-%d %H:%M:%S"),\n        "total":               len(results),\n        "ok_count":            ok_count,\n        "fail_count":          len(results) - ok_count,\n        "total_tables_in":     sum(r.get("n_tables_in",0) for r in results),\n        "total_tables_ok":     sum(r.get("n_tables_ok",0) for r in results),\n        "total_fin_tables":    sum(r.get("n_financial_tables",0) for r in results),\n        "total_calc_applied":  sum(r.get("n_calc_applied",0) for r in results),\n        "total_err":           sum(r.get("n_err",0) for r in results),\n        "total_verify_pass":   sum(r.get("n_verify_pass",0) for r in results),\n        "total_verify_fail":   sum(r.get("n_verify_fail",0) for r in results),\n        "total_text_blocks":   sum(r.get("n_text_blocks_out",0) for r in results),\n        "reports":             results,\n    }\n\n# ============================================================================\n# [VRN:ANCHOR:MDL003-SYS-001] §13  PIPELINE ENTRY\n# ============================================================================\n\nclass VRN_MDL003_TableRestorer:\n    """VRN-MDL003-CLS-001\n    run():\n      1. Load external SSOT (optional)\n      2. Accel init\n      3. Load VRN_MDL002_Layout.json\n      4. Parallel process_one_pdf() — restore tables + text\n      5. DB export\n      6. VRN_MDL003_Restored.json + TextFlow.json + VerifySummary.json\n    """\n    def __init__(self, cfg: Dict):\n        self.cfg     = cfg\n        workers      = cfg.get("workers", 0) or max(1, (os.cpu_count() or 4) - 1)\n        self.workers = workers\n        self.db: Optional[MDL003DBWriter] = None\n        self.repair  = TextRepairEngine()\n\n    def run(self) -> Dict:\n        mdl002_temp = self.cfg.get("mdl002_temp", _DEFAULTS["mdl002_temp"])\n        mdl003_temp = self.cfg.get("mdl003_temp", _DEFAULTS["mdl003_temp"])\n        ssot_dir    = self.cfg.get("ssot_dir",    _DEFAULTS["ssot_dir"])\n        Path(mdl003_temp).mkdir(parents=True, exist_ok=True)\n\n        # Load external SSOT\n        ssot_caps = load_external_ssot(ssot_dir)\n        log.info("[MDL003] SSOT caps: %s", ssot_caps)\n\n        cap = _mdl003_accel_init(self.workers)\n        log.info("[MDL003] accel caps: %s", cap)\n\n        if self.cfg.get("enable_db", True):\n            self.db = MDL003DBWriter(str(Path(mdl003_temp) / "VRN_MDL003.db"))\n\n        # Load MDL002 output\n        mdl002_data = load_mdl002_output(mdl002_temp)\n        if not mdl002_data:\n            return {"ok": False, "total": 0, "success": 0,\n                    "errors": ["MDL002 output not found"], "out_dir": mdl003_temp}\n\n        pdf_reports = mdl002_data.get("reports", [])\n        log.info("[MDL003] Restoring %d PDF reports, workers=%d",\n                 len(pdf_reports), self.workers)\n\n        all_results: List[Dict] = []\n        fail_count = 0\n\n        with ThreadPoolExecutor(max_workers=self.workers) as ex:\n            futs = {\n                ex.submit(process_one_pdf, rpt, self.cfg, self.repair, self.db): rpt\n                for rpt in pdf_reports\n            }\n            for fut in as_completed(futs):\n                res = fut.result()\n                all_results.append(res)\n                if not res.get("ok"): fail_count += 1\n\n        if self.db:\n            self.db.export_parquet(mdl003_temp)\n            self.db.export_csv(mdl003_temp)\n\n        out = assemble_output(all_results)\n        _jwrite(str(Path(mdl003_temp) / "VRN_MDL003_Restored.json"), out)\n\n        # Separate text flow output\n        text_flow_out = {\n            "module": __module_id__, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),\n            "reports": [\n                {"pdf_name": r["pdf_name"], "report_code": r["report_code"],\n                 "text_flow": r.get("text_flow", [])}\n                for r in all_results\n            ]\n        }\n        _jwrite(str(Path(mdl003_temp) / "VRN_MDL003_TextFlow.json"), text_flow_out)\n\n        verify_summary = {\n            "module":             __module_id__,\n            "version":            __version__,\n            "generated":          time.strftime("%Y-%m-%d %H:%M:%S"),\n            "total":              len(pdf_reports),\n            "ok":                 fail_count == 0,\n            "ok_count":           len(pdf_reports) - fail_count,\n            "fail_count":         fail_count,\n            "total_tables_ok":    out["total_tables_ok"],\n            "total_fin_tables":   out["total_fin_tables"],\n            "total_calc_applied": out["total_calc_applied"],\n            "total_err":          out["total_err"],\n            "total_verify_pass":  out["total_verify_pass"],\n            "total_verify_fail":  out["total_verify_fail"],\n            "ssot_caps":          ssot_caps,\n            "accel_caps":         cap,\n            "fail_details": [\n                {"pdf_name": r["pdf_name"], "error": r.get("error")}\n                for r in all_results if not r.get("ok")\n            ],\n        }\n        _jwrite(str(Path(mdl003_temp) / "VRN_MDL003_VerifySummary.json"), verify_summary)\n\n        log.info(\n            "[MDL003] Complete: %d/%d OK  tables=%d/%d  fin=%d  calc=%d  err=%d  "\n            "verify=%d/%d  text=%d",\n            len(pdf_reports) - fail_count, len(pdf_reports),\n            out["total_tables_ok"], out["total_tables_in"],\n            out["total_fin_tables"], out["total_calc_applied"],\n            out["total_err"], out["total_verify_pass"],\n            out["total_verify_pass"] + out["total_verify_fail"],\n            out["total_text_blocks"],\n        )\n        return {\n            "ok":               fail_count == 0,\n            "total":            len(pdf_reports),\n            "success":          len(pdf_reports) - fail_count,\n            "total_tables_ok":  out["total_tables_ok"],\n            "total_fin_tables": out["total_fin_tables"],\n            "total_calc":       out["total_calc_applied"],\n            "total_err":        out["total_err"],\n            "errors":           [r.get("error","") for r in all_results if not r.get("ok")],\n            "out_dir":          mdl003_temp,\n        }\n\n# ============================================================================\n# __all__\n# ============================================================================\n\n__all__ = [\n    "__version__", "__module_id__",\n    "TW_TICKER_REGEX", "TW_BLOOMBERG_REGEX", "TW_YFINANCE_REGEX",\n    "_CANONICAL_MAP", "CALC_RULES",\n    "_mdl003_accel_init",\n    "load_mdl002_output", "load_external_ssot",\n    "canonicalize_label", "classify_fin_type",\n    "clean_ocr_number", "is_axis_noise",\n    "TextRepairEngine", "TableRestoreEngine",\n    "RestoredTable",\n    "restore_one_table", "apply_calc_rules", "verify_financial_arithmetic",\n    "reflow_text_blocks",\n    "process_one_pdf", "assemble_output",\n    "MDL003DBWriter", "VRN_MDL003_TableRestorer",\n]\n\n# ============================================================================\n# __main__\n# ============================================================================\n\nif __name__ == "__main__":\n    p = argparse.ArgumentParser(description="VRN MDL003 TableRestorer -- Restore+Validate")\n    for k, v in _DEFAULTS.items():\n        tp = bool if isinstance(v, bool) else (int if isinstance(v, int) else str)\n        if tp == bool: p.add_argument("--" + k.replace("_", "-"), action="store_true", default=v)\n        else:          p.add_argument("--" + k.replace("_", "-"), type=tp, default=v)\n    args   = p.parse_args()\n    cfg    = {k.replace("-", "_"): v for k, v in vars(args).items()}\n    result = VRN_MDL003_TableRestorer(cfg).run()\n    print(json.dumps(result, ensure_ascii=False, indent=2))\n    sys.exit(0 if result["ok"] else 1)', 'nlp': '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nVRN_M07_Summarizer — Veritas NLP Bullet Summarizer Kernel\n==========================================================\n• Best local free NLP summarizer stack: Chinese + English.\n• Input: M01~M06 outputs (財報/OCR/表格/PDF/API/Log/HTML) or raw text.\n• Pipeline: Sentence Split → Semantic Embedding → Ranking → Transformer/Extractive Summary → Bullet Generator.\n• Output: Bullet-point summary (zh + en), JSON report, compatible with Report Page-1.\n• Libraries: transformers (BART/T5), sentence-transformers, summa/gensim, yake, jieba — all local & free.\n• TOP 10 free LLM/summarizer libs: 5 English + 5 Chinese, used together in pipeline with fallback.\n"""\n\nfrom __future__ import annotations\n\nimport os\nimport re\nimport json\nimport argparse\nfrom pathlib import Path\nfrom typing import List, Dict, Any, Optional, Tuple\nfrom datetime import datetime, timezone\n\n# ═══════════════════════════════════════════════════════════════════════════\n# PARAMETERS (same style as all previous VRN modules)\n# ═══════════════════════════════════════════════════════════════════════════\n\n# Tier 1 — Transformer summarization\nMODEL_EN = "facebook/bart-large-cnn"\nMODEL_CN = "uer/bart-base-chinese-cluecorpussmall"\n# Fallback smaller (faster)\nMODEL_EN_SMALL = "sshleifer/distilbart-cnn-6-6"\nMODEL_CN_ALT = "IDEA-CCNL/Randeng-BART-139M-Summary-Chinese"\n\n# Embedding for sentence ranking (multilingual)\nEMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"\n# Fallback\nEMBED_MODEL_SMALL = "sentence-transformers/all-MiniLM-L6-v2"\n\n# Length & bullets\nMAX_SUMMARY_LEN = 200\nMIN_SUMMARY_LEN = 50\nNUM_BULLETS = 8\nMAX_INPUT_CHARS = 8000  # truncate long input for transformer\n\n# M01~M06 output directory (text/JSON from extractors)\nM01_M06_OUTPUT_DIR: str = os.environ.get("VRN_OUTPUT_SAVE_DIR") or os.path.join(os.path.dirname(__file__) or ".", "VRN_Output")\nOUTPUT_REPORT_PATH: str = ""  # empty = auto under M01_M06_OUTPUT_DIR\n\n# Language\nLANG_MODE = "auto"  # "auto" | "zh" | "en"\nOUTPUT_BOTH_LANGS = True  # produce bullets in both Chinese and English when possible\n\n# ═══════════════════════════════════════════════════════════════════════════\n# TOP 10 FREE LLM / SUMMARIZER LIBS — 中英文各五個，一起完成 pipeline\n# EN: transformers, sumy, bert-extractive-summarizer, gensim, summa\n# ZH: transformers(中文BART), ckip-transformers, jieba, text2vec, snownlp\n# ═══════════════════════════════════════════════════════════════════════════\n\n# English (5): local free, offline-capable\nTOP_5_LLM_LIBS_EN = [\n    {"name": "transformers", "pip": "transformers", "model": "facebook/bart-large-cnn", "type": "summarization"},\n    {"name": "sumy", "pip": "sumy", "model": "lex-rank", "type": "extractive"},\n    {"name": "bert_extractive", "pip": "bert-extractive-summarizer", "model": "bert-base-uncased", "type": "extractive"},\n    {"name": "gensim", "pip": "gensim", "model": "summarization", "type": "textrank"},\n    {"name": "summa", "pip": "summa", "model": "textrank", "type": "extractive"},\n]\n\n# Chinese (5): 本地免費、可離線\nTOP_5_LLM_LIBS_ZH = [\n    {"name": "transformers_zh", "pip": "transformers", "model": "uer/bart-base-chinese-cluecorpussmall", "type": "summarization"},\n    {"name": "ckip_transformers", "pip": "ckip-transformers", "model": "bert-base", "type": "nlp"},\n    {"name": "jieba", "pip": "jieba", "model": "default", "type": "segment"},\n    {"name": "text2vec", "pip": "text2vec", "model": "shibing624/text2vec-base-chinese", "type": "embedding"},\n    {"name": "snownlp", "pip": "snownlp", "model": "summary", "type": "extractive"},\n]\n\n# Combined: try in order for summarization (EN then ZH or by lang)\nTOP_10_LLM_LIBS = TOP_5_LLM_LIBS_EN + TOP_5_LLM_LIBS_ZH\n\n# ═══════════════════════════════════════════════════════════════════════════\n# SAFE IMPORTS (local free libs — optional with fallbacks)\n# ═══════════════════════════════════════════════════════════════════════════\n\ndef _safe_import(name: str, package: Optional[str] = None) -> Any:\n    try:\n        if package:\n            return __import__(package, fromlist=[name])\n        return __import__(name)\n    except Exception:\n        return None\n\n\ndef load_libraries() -> Dict[str, Any]:\n    """Load NLP/summarizer libs; fallbacks if not installed."""\n    libs: Dict[str, Any] = {"re": re}\n    # numpy\n    np = _safe_import("numpy")\n    libs["np"] = np\n    # transformers\n    trf = _safe_import("transformers")\n    libs["transformers"] = trf\n    if trf:\n        try:\n            libs["pipeline"] = trf.pipeline\n        except Exception:\n            libs["pipeline"] = None\n    else:\n        libs["pipeline"] = None\n    # sentence-transformers\n    st = _safe_import("sentence_transformers")\n    libs["SentenceTransformer"] = st.SentenceTransformer if st else None\n    # sklearn cosine\n    try:\n        from sklearn.metrics.pairwise import cosine_similarity\n        libs["cosine_similarity"] = cosine_similarity\n    except Exception:\n        libs["cosine_similarity"] = None\n    # yake\n    libs["yake"] = _safe_import("yake")\n    # summa (TextRank)\n    libs["summa"] = _safe_import("summa")\n    # gensim (TextRank fallback)\n    libs["gensim"] = _safe_import("gensim")\n    # jieba (Chinese)\n    libs["jieba"] = _safe_import("jieba")\n    # keybert (optional)\n    libs["keybert"] = _safe_import("keybert")\n    # TOP 10 free LLM libs: which are available (5 EN + 5 ZH)\n    def _has(pkg: str) -> bool:\n        try:\n            __import__(pkg.replace("-", "_"))\n            return True\n        except Exception:\n            return False\n    libs["top10_en"] = [e for e in TOP_5_LLM_LIBS_EN if _has(e["pip"].split("-")[0]) or (e["pip"] == "transformers" and libs.get("transformers")) or (e["pip"] == "gensim" and libs.get("gensim")) or (e["pip"] == "summa" and libs.get("summa"))]\n    libs["top10_zh"] = [e for e in TOP_5_LLM_LIBS_ZH if _has(e["pip"].split("-")[0]) or (e["pip"] == "transformers" and libs.get("transformers")) or (e["pip"] == "jieba" and libs.get("jieba"))]\n    if not libs["top10_en"]:\n        libs["top10_en"] = TOP_5_LLM_LIBS_EN  # names for reference\n    if not libs["top10_zh"]:\n        libs["top10_zh"] = TOP_5_LLM_LIBS_ZH\n    try:\n        libs["sumy"] = __import__("sumy")\n    except Exception:\n        libs["sumy"] = None\n    try:\n        libs["snownlp"] = __import__("snownlp")\n    except Exception:\n        libs["snownlp"] = None\n    return libs\n\n\ndef detect_language(text: str) -> str:\n    """Detect zh vs en from raw text."""\n    if not text or not text.strip():\n        return "en"\n    chinese_chars = re.findall(r"[\\u4e00-\\u9fff]", text)\n    if len(chinese_chars) > 10 or (len(chinese_chars) / max(len(text), 1)) > 0.05:\n        return "zh"\n    return "en"\n\n\ndef split_sentences(text: str, lang: str) -> List[str]:\n    """Split into sentences (regex)."""\n    if lang == "zh":\n        parts = re.split(r"[。！？\\n]+", text)\n    else:\n        parts = re.split(r"[.!?\\n]+", text)\n    sentences = [s.strip() for s in parts if s and len(s.strip()) > 8]\n    return sentences\n\n\ndef rank_sentences_textrank(sentences: List[str], libs: Dict[str, Any], top_k: int = 15) -> List[str]:\n    """Rank sentences with TextRank (summa or gensim)."""\n    if not sentences:\n        return []\n    combined = " ".join(sentences) if len(sentences) > 1 else sentences[0]\n    summa_mod = libs.get("summa")\n    if summa_mod and hasattr(summa_mod, "keywords"):\n        try:\n            from summa import summarizer as sm\n            ranked_text = sm.summarize(combined, ratio=0.5)\n            if ranked_text:\n                return [s.strip() for s in ranked_text.split(". ") if s.strip()][:top_k]\n        except Exception:\n            pass\n    if libs.get("gensim"):\n        try:\n            from gensim.summarization import summarize\n            out = summarize(combined, ratio=0.5)\n            if out:\n                return [s.strip() for s in out.split(". ") if s.strip()][:top_k]\n        except Exception:\n            pass\n    return sentences[:top_k]\n\n\ndef rank_sentences_embedding(sentences: List[str], libs: Dict[str, Any], top_k: int = 15) -> List[str]:\n    """Rank by semantic embedding + cosine centrality."""\n    if not sentences or not libs.get("SentenceTransformer") or not libs.get("cosine_similarity"):\n        return rank_sentences_textrank(sentences, libs, top_k)\n    try:\n        for model_name in (EMBED_MODEL, EMBED_MODEL_SMALL):\n            try:\n                model = libs["SentenceTransformer"](model_name)\n                emb = model.encode(sentences)\n                sim = libs["cosine_similarity"](emb, emb)\n                scores = sim.sum(axis=1)\n                ranked = sorted(zip(sentences, scores), key=lambda x: x[1], reverse=True)\n                return [r[0] for r in ranked[:top_k]]\n            except Exception:\n                continue\n    except Exception:\n        pass\n    return rank_sentences_textrank(sentences, libs, top_k)\n\n\ndef _sumy_summarize(text: str, libs: Dict[str, Any], max_sents: int = 5) -> Optional[str]:\n    """Summarize with sumy (EN): LexRank, LSA, etc. — TOP 10 EN lib #2."""\n    if not libs.get("sumy"):\n        return None\n    try:\n        from sumy.parsers.plaintext import PlaintextParser\n        from sumy.nlp.tokenizers import Tokenizer\n        from sumy.summarizers.lex_rank import LexRankSummarizer\n        parser = PlaintextParser.from_string(text, Tokenizer("english"))\n        summarizer = LexRankSummarizer()\n        sents = summarizer(parser.document, max_sents)\n        return " ".join(str(s) for s in sents) if sents else None\n    except Exception:\n        try:\n            from sumy.summarizers.lsa import LsaSummarizer\n            from sumy.parsers.plaintext import PlaintextParser\n            from sumy.nlp.tokenizers import Tokenizer\n            parser = PlaintextParser.from_string(text, Tokenizer("english"))\n            summarizer = LsaSummarizer()\n            sents = summarizer(parser.document, max_sents)\n            return " ".join(str(s) for s in sents) if sents else None\n        except Exception:\n            pass\n    return None\n\n\ndef _snownlp_summarize(text: str, libs: Dict[str, Any]) -> Optional[str]:\n    """Summarize with snownlp (ZH). — TOP 10 ZH lib #5. Uses TextRank sentences."""\n    if not libs.get("snownlp"):\n        return None\n    try:\n        from snownlp import SnowNLP\n        s = SnowNLP(text)\n        # s.summary(n) returns list of top n sentences\n        n = min(max(3, len(text) // 200), 10)\n        sentences = s.summary(n)\n        if sentences:\n            return "".join(sentences) if isinstance(sentences[0], str) else " ".join(str(x) for x in sentences)\n    except Exception:\n        pass\n    return None\n\n\ndef summarize_with_top10_llms(text: str, lang: str, libs: Dict[str, Any]) -> Tuple[str, str]:\n    """Use TOP 10 free LLM libs (5 EN + 5 ZH) in order; return (summary, used_lib_name)."""\n    if len(text) > MAX_INPUT_CHARS:\n        text = text[:MAX_INPUT_CHARS]\n    # 1) Transformers (EN: BART/T5 — ZH: BART-chinese)\n    pipe = libs.get("pipeline")\n    if pipe:\n        for model in ([MODEL_CN, MODEL_CN_ALT] if lang == "zh" else [MODEL_EN, MODEL_EN_SMALL]):\n            try:\n                summarizer = pipe("summarization", model=model)\n                out = summarizer(text, max_length=MAX_SUMMARY_LEN, min_length=min(20, MAX_SUMMARY_LEN // 2), do_sample=False)\n                if out and isinstance(out, list) and len(out) > 0:\n                    s = out[0].get("summary_text", str(out[0]))\n                    if s and len(s) > 10:\n                        return s, "transformers"\n            except Exception:\n                continue\n    # 2) sumy (EN) — TOP 5 EN #2\n    if lang == "en":\n        s = _sumy_summarize(text, libs)\n        if s:\n            return s, "sumy"\n    # 3) snownlp (ZH) — TOP 5 ZH #5\n    if lang == "zh":\n        s = _snownlp_summarize(text, libs)\n        if s:\n            return s, "snownlp"\n    # 4) summa / gensim (both)\n    s = extractive_summary_fallback(text, libs)\n    return s, "summa/gensim"\n\n\ndef transformer_summary(text: str, lang: str, libs: Dict[str, Any]) -> Tuple[str, str]:\n    """Summarize with BART/T5 + TOP 10 free LLM libs (5 EN + 5 ZH) together. Returns (summary, used_lib)."""\n    return summarize_with_top10_llms(text, lang, libs)\n\n\ndef extractive_summary_fallback(text: str, libs: Dict[str, Any]) -> str:\n    """Use TextRank-style extractive summary when transformer unavailable."""\n    try:\n        from summa import summarizer as sm\n        return sm.summarize(text, ratio=0.3) or text[:MAX_SUMMARY_LEN]\n    except Exception:\n        pass\n    if libs.get("gensim"):\n        try:\n            from gensim.summarization import summarize\n            return summarize(text, ratio=0.3) or text[:MAX_SUMMARY_LEN]\n        except Exception:\n            pass\n    sentences = re.split(r"[。.!?\\n]+", text)\n    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]\n    return " ".join(sentences[:5]) if sentences else text[:MAX_SUMMARY_LEN]\n\n\ndef generate_bullets(summary: str, lang: str, libs: Dict[str, Any]) -> List[str]:\n    """Generate bullet points (YAKE / KeyBERT or sentence split)."""\n    bullets: List[str] = []\n    # YAKE\n    yake_mod = libs.get("yake")\n    if yake_mod and hasattr(yake_mod, "KeywordExtractor"):\n        try:\n            kw = yake_mod.KeywordExtractor(lan=lang if lang == "en" else "zh", n=2, top=NUM_BULLETS)\n            kws = kw.extract_keywords(summary)\n            for kw_phrase, _ in (kws or [])[:NUM_BULLETS]:\n                if kw_phrase and len(kw_phrase) > 2:\n                    bullets.append("• " + kw_phrase.strip())\n        except Exception:\n            pass\n    if bullets:\n        return bullets\n    # KeyBERT\n    kb = libs.get("keybert")\n    if kb and hasattr(kb, "KeyBERT"):\n        try:\n            model = kb.KeyBERT()\n            kws = model.extract_keywords(summary, keyphrase_ngram_range=(1, 2), top_n=NUM_BULLETS)\n            for kw, _ in (kws or [])[:NUM_BULLETS]:\n                if kw:\n                    bullets.append("• " + kw.strip())\n        except Exception:\n            pass\n    if bullets:\n        return bullets\n    # Fallback: split by sentence\n    for sep in ("。", ". ", "! ", "? "):\n        parts = [p.strip() for p in summary.split(sep) if len(p.strip()) > 10]\n        if len(parts) >= 2:\n            for p in parts[:NUM_BULLETS]:\n                bullets.append("• " + p)\n            break\n    if not bullets and summary:\n        bullets.append("• " + summary[:150].strip())\n    return bullets[:NUM_BULLETS]\n\n\ndef load_text_from_m01_m06_output(output_dir: str) -> str:\n    """Aggregate text from M01~M06 outputs (JSON/txt in folder)."""\n    if not output_dir or not os.path.isdir(output_dir):\n        return ""\n    chunks: List[str] = []\n    for root, _, files in os.walk(output_dir):\n        for f in files:\n            if not (f.endswith(".json") or f.endswith(".txt") or f.endswith(".md")):\n                continue\n            path = os.path.join(root, f)\n            try:\n                with open(path, "r", encoding="utf-8", errors="ignore") as fp:\n                    raw = fp.read()\n                if f.endswith(".json"):\n                    try:\n                        data = json.loads(raw)\n                        if isinstance(data, dict):\n                            for v in data.values():\n                                if isinstance(v, str) and len(v) > 20:\n                                    chunks.append(v)\n                                elif isinstance(v, list):\n                                    for item in v:\n                                        if isinstance(item, str) and len(item) > 20:\n                                            chunks.append(item)\n                        elif isinstance(data, list):\n                            for item in data:\n                                if isinstance(item, str) and len(item) > 20:\n                                    chunks.append(item)\n                    except json.JSONDecodeError:\n                        chunks.append(raw[:5000])\n                else:\n                    if len(raw) > 50:\n                        chunks.append(raw[:8000])\n            except Exception:\n                continue\n    return "\\n\\n".join(chunks) if chunks else ""\n\n\ndef summarize_text(\n    text: str,\n    lang_override: Optional[str] = None,\n    libs: Optional[Dict[str, Any]] = None,\n) -> Dict[str, Any]:\n    """Full pipeline: sentence split → rank → summarize → bullets. Returns dict with summary + bullets (zh/en when OUTPUT_BOTH_LANGS)."""\n    if not text or not text.strip():\n        return {"language": "en", "summary": "", "bullets": [], "summary_en": "", "summary_zh": "", "bullets_en": [], "bullets_zh": [], "top10_llm_used": "", "top10_libs_en": [], "top10_libs_zh": []}\n    libs = libs or load_libraries()\n    lang = lang_override or (LANG_MODE if LANG_MODE != "auto" else detect_language(text))\n    sentences = split_sentences(text, lang)\n    if not sentences:\n        sentences = [text[:MAX_INPUT_CHARS]]\n    ranked = rank_sentences_embedding(sentences, libs, top_k=15)\n    if not ranked:\n        ranked = sentences[:10]\n    top_text = " ".join(ranked) if isinstance(ranked[0], str) else " ".join(str(s) for s in ranked)\n    summary_primary, llm_used = transformer_summary(top_text, lang, libs)\n    bullets_primary = generate_bullets(summary_primary, lang, libs)\n    result: Dict[str, Any] = {\n        "language": lang,\n        "summary": summary_primary,\n        "bullets": bullets_primary,\n        "summary_en": "",\n        "summary_zh": "",\n        "bullets_en": [],\n        "bullets_zh": [],\n        "top10_llm_used": llm_used,\n        "top10_libs_en": [e["name"] for e in libs.get("top10_en", TOP_5_LLM_LIBS_EN)],\n        "top10_libs_zh": [e["name"] for e in libs.get("top10_zh", TOP_5_LLM_LIBS_ZH)],\n    }\n    if lang == "zh":\n        result["summary_zh"] = summary_primary\n        result["bullets_zh"] = bullets_primary\n        if OUTPUT_BOTH_LANGS and libs.get("pipeline"):\n            try:\n                s_en, _ = transformer_summary(top_text[:4000], "en", libs)\n                result["summary_en"] = s_en\n                result["bullets_en"] = generate_bullets(s_en, "en", libs)\n            except Exception:\n                result["bullets_en"] = bullets_primary  # same bullets\n    else:\n        result["summary_en"] = summary_primary\n        result["bullets_en"] = bullets_primary\n        if OUTPUT_BOTH_LANGS and libs.get("pipeline"):\n            try:\n                s_zh, _ = transformer_summary(top_text[:4000], "zh", libs)\n                result["summary_zh"] = s_zh\n                result["bullets_zh"] = generate_bullets(s_zh, "zh", libs)\n            except Exception:\n                result["bullets_zh"] = bullets_primary\n    return result\n\n\ndef run_from_m01_m06_output(output_dir: Optional[str] = None) -> Dict[str, Any]:\n    """Load text from M01~M06 output directory and run summarizer. Data source = M01~M06 outputs."""\n    out_dir = output_dir or M01_M06_OUTPUT_DIR\n    text = load_text_from_m01_m06_output(out_dir)\n    if not text.strip():\n        text = "No extracted text found in M01–M06 output directory. Add JSON or TXT files with content."\n    return summarize_text(text, libs=load_libraries())\n\n\ndef save_report(report: Dict[str, Any], out_path: Optional[str] = None) -> str:\n    """Save summarizer report JSON (and optional TXT) to path."""\n    out_path = out_path or OUTPUT_REPORT_PATH\n    if not out_path:\n        os.makedirs(M01_M06_OUTPUT_DIR, exist_ok=True)\n        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")\n        out_path = os.path.join(M01_M06_OUTPUT_DIR, f"VRN_M07_Summarizer_Report_{ts}.json")\n    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)\n    with open(out_path, "w", encoding="utf-8") as f:\n        json.dump(report, f, ensure_ascii=False, indent=2)\n    txt_path = out_path.replace(".json", ".txt")\n    lines = [\n        "VRN_M07_Summarizer Report",\n        "Summary (primary): " + report.get("summary", ""),\n        "",\n        "Bullets (primary):",\n    ]\n    for b in report.get("bullets", []):\n        lines.append("  " + b)\n    if report.get("bullets_zh"):\n        lines.append("")\n        lines.append("Bullets (中文):")\n        for b in report["bullets_zh"]:\n            lines.append("  " + b)\n    if report.get("bullets_en"):\n        lines.append("")\n        lines.append("Bullets (English):")\n        for b in report["bullets_en"]:\n            lines.append("  " + b)\n    with open(txt_path, "w", encoding="utf-8") as f:\n        f.write("\\n".join(lines))\n    return out_path\n\n\ndef main() -> int:\n    parser = argparse.ArgumentParser(description="VRN_M07_Summarizer — NLP bullet summarizer (zh/en), data from M01~M06")\n    parser.add_argument("--input-dir", type=str, default="", help="M01~M06 output directory (default: VRN_OUTPUT_SAVE_DIR)")\n    parser.add_argument("--text", type=str, default="", help="Raw text to summarize (overrides input-dir)")\n    parser.add_argument("--output", type=str, default="", help="Output JSON report path")\n    parser.add_argument("--lang", type=str, choices=["auto", "zh", "en"], default="auto")\n    parser.add_argument("--auto", action="store_true")\n    parser.add_argument("--max-confidence", action="store_true")\n    args = parser.parse_args()\n\n    global LANG_MODE\n    if args.lang != "auto":\n        LANG_MODE = args.lang\n\n    if args.text.strip():\n        report = summarize_text(args.text.strip(), lang_override=LANG_MODE if LANG_MODE != "auto" else None)\n    else:\n        report = run_from_m01_m06_output(args.input_dir or None)\n\n    path = save_report(report, args.output or None)\n    print("VRN_M07_Summarizer OK")\n    print("  Report:", path)\n    print("  Summary:", (report.get("summary") or "")[:200])\n    print("  Bullets:", len(report.get("bullets", [])))\n    return 0\n\n\nif __name__ == "__main__":\n    import sys\n    sys.exit(main())\n', 'integrated': '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nfrom __future__ import annotations\n"""\nVIA NON-STOCK SUMMARIZER ENGINE v0310\n=====================================\nSingle-entry integration engine.\n\nReuses, rather than rewrites:\n- VRN_M03_PDF_Layout_JSON v3       -> PDF layout / roles / blocks\n- VRN_MDL003_TableRestorer         -> TextRepairEngine / axis-noise / dedup\n- VRN_M07_Summarizer               -> local extractive NLP helper\n- NON_STOCK_CORE v0200             -> Story/claim/evidence/guards/events\n\nOutput philosophy:\n    ONE REPORT = ONE MAIN ROW\n    Details live in TOPIC / COMPANY / EVIDENCE child tables.\n\nMain summary contract:\n    TITLE\n    POINT_1 = core thesis / what happened\n    POINT_2 = driver / why\n    POINT_3 = impact / who benefits or is affected\n    POINT_4 = outlook / risk / what next\n\nLocal-only. No model download. No source mutation.\n"""\n\n# =============================================================================\n# def 00 PARAMETERS — all editable parameters are kept at the top\n# =============================================================================\nfrom dataclasses import asdict\nfrom pathlib import Path\nfrom collections import Counter, defaultdict\nfrom typing import Any, Optional\nimport argparse, csv, hashlib, html, importlib.util, json, os, re, sys\n\nENGINE_ID = "VIA-NON-STOCK-SUMMARIZER-INTEGRATED-002"\nENGINE_VERSION = "v0400"\nENGINE_NAME = "VIA NON-STOCK SUMMARIZER ENGINE"\nNETWORK_ALLOWED = False\n\nMAX_REPORT_POINT_CHARS = 220\nMAX_TOPIC_POINT_CHARS = 220\nMAX_TOPICS_PER_REPORT_HTML = 40\nMAX_COMPANIES_PER_REPORT_HTML = 40\nTOPIC_MIN_CHARS = 1\nMIN_REPORT_EVIDENCE = 1\n\nBROKER_PATTERNS = {\n    "UBS": ("UBS",), "MS": ("MS-", "Morgan Stanley"), "GS": ("GS-", "Goldman"),\n    "CITI": ("Citi-",), "DAIWA": ("Daiwa-",), "JPM": ("JP-", "JPM"),\n    "MEGA": ("兆豐",), "TAISHIN": ("台新",), "CTBC": ("中信", "CTBC"),\n    "CATHAY": ("國泰",), "YUANTA": ("元大",), "CLSA": ("CLST-", "CLSA"),\n}\n\nINDUSTRY_MAP = {\n    "AI_INFRASTRUCTURE":"AI Infrastructure",\n    "ASIC_CUSTOM_SILICON":"Semiconductor / ASIC",\n    "AI_THERMAL":"Thermal / Cooling",\n    "MEMORY":"Memory",\n    "PCB_MATERIALS":"PCB / Materials",\n    "CPO_OPTICAL":"Optical / CPO",\n    "FOUNDRY_ADVANCED":"Foundry",\n    "ADVANCED_PACKAGING":"Advanced Packaging",\n    "SEMICONDUCTOR_MATERIALS":"Semiconductor Materials",\n    "SEMICONDUCTOR_EQUIPMENT":"Semiconductor Equipment",\n    "AEROSPACE":"Aerospace",\n    "DEFENSE_DRONE":"Defense / Drone",\n    "ROBOTICS_PHYSICAL_AI":"Robotics / Physical AI",\n    "EV_AUTOMOTIVE":"Automotive / EV",\n    "SHIPPING":"Shipping",\n    "RATES_BONDS":"Macro / Rates / Bonds",\n    "ENERGY_GEOPOLITICS":"Energy / Geopolitics",\n    "DISPLAY_ESL":"Display / E-paper / ESL",\n    "CDMO_PHARMA":"Pharma / CDMO",\n    "POWER_GRID":"Power Grid",\n}\n\nREPORT_COLUMNS = [\n    "REPORT_ID","REPORT_DATE","FILE_NAME","REPORT_TYPE","SOURCE","ANALYST_AUTHOR",\n    "MAIN_STORY","MAIN_INDUSTRY","TITLE",\n    "POINT_1","POINT_2","POINT_3","POINT_4",\n    "DIRECTION","HORIZON","COMPANY_COUNT","TOPIC_COUNT","EVIDENCE_COUNT",\n    "LAYOUT_ENGINE","TEXT_REPAIR_ENGINE","NLP_ENGINE","STATUS","DETAIL_REF"\n]\nTOPIC_COLUMNS = [\n    "REPORT_ID","TOPIC_ID","SOURCE_UNIT","TOPIC_TITLE","STORY_L1","INDUSTRY",\n    "TITLE","POINT_1","POINT_2","POINT_3","POINT_4","DIRECTION","HORIZON",\n    "TICKERS","GLOBAL_ANCHORS","EVIDENCE_SIDS","NLP_HINT","STATUS"\n]\nCOMPANY_COLUMNS = [\n    "REPORT_ID","TICKER","COMPANY_NAME","STORIES","INDUSTRY","RATING","TARGET_PRICE",\n    "TITLE","POINT_1","POINT_2","POINT_3","POINT_4","EVIDENCE_SIDS","STATUS"\n]\nEVIDENCE_COLUMNS = [\n    "REPORT_ID","CLAIM_ID","EVIDENCE_SID","PAGE","ATTRIBUTION","IMPORTANCE","DIRECTION",\n    "STORIES","TICKERS","DRIVERS","RELATIONS","PERIODS","TEXT"\n]\n\n# =============================================================================\n# def 01 MODULE LOADER\n# =============================================================================\ndef def_load_module(name: str, path: Path):\n    spec=importlib.util.spec_from_file_location(name,path)\n    if not spec or not spec.loader: raise ImportError(f"Cannot load {name}: {path}")\n    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod\n\n# Components supplied by the verified single-file loader.\n\n# =============================================================================\n# def 02 GENERIC HELPERS\n# =============================================================================\ndef def_hash8(text:str)->str: return hashlib.sha256(text.encode("utf-8",errors="ignore")).hexdigest()[:8].upper()\ndef def_clean(text:str)->str: return CORE.def_normalize_text(text or "")\ndef def_clip(text:str,n:int=MAX_REPORT_POINT_CHARS)->str:\n    t=def_clean(text); return t if len(t)<=n else t[:n-1].rstrip()+"…"\ndef def_join_unique(items:list[str],sep:str=";")->str:\n    out=[]\n    for x in items:\n        if x and x not in out: out.append(x)\n    return sep.join(out)\ndef def_file_sha(path:Path)->str:\n    h=hashlib.sha256()\n    with path.open(\'rb\') as f:\n        for b in iter(lambda:f.read(1024*1024),b\'\'): h.update(b)\n    return h.hexdigest()\n\ndef def_source_name(path:Path, blocks:list[Any])->str:\n    hay=path.name+"\\n"+"\\n".join(b.text for b in blocks[:20])\n    for source,pats in BROKER_PATTERNS.items():\n        if any(p.lower() in hay.lower() for p in pats): return source\n    return "UNKNOWN"\n\ndef def_report_date(path: Path, blocks: list[Any]) -> str:\n    from datetime import date\n    hay = path.name + "\\n" + "\\n".join(b.text for b in blocks[:25])\n    patterns = [r"(?<!\\d)(20\\d{2})(\\d{2})(\\d{2})(?!\\d)",\n                r"(?<!\\d)(20\\d{2})[年/.-](\\d{1,2})[月/.-](\\d{1,2})日?"]\n    for pattern in patterns:\n        for match in re.finditer(pattern, hay):\n            try:\n                return date(*(int(value) for value in match.groups())).isoformat()\n            except ValueError:\n                continue\n    return ""\n\ndef def_author(blocks:list[Any])->str:\n    hay="\\n".join(b.text for b in blocks[:25])\n    for p in [r"(?:研究員|分析師|報告人)[：:]?\\s*([\\u4e00-\\u9fff]{2,4})",r"([\\u4e00-\\u9fff]{2,4})\\s*(?:證券研究員|合格證券投資分析人員)"]:\n        m=re.search(p,hay)\n        if m:return m.group(1)\n    return ""\n\n# =============================================================================\n# def 03 VRN-2 PDF LAYOUT + TEXT REPAIR ADAPTER\n# =============================================================================\ndef def_page_title_from_layout(layout_page:dict[str,Any])->str:\n    spans=layout_page.get("spans",[])\n    cand=[s for s in spans if s.get("role") in {"TITLE","SUBTITLE","SECTION_HEADING"} and len(def_clean(s.get("text","")))>1]\n    if not cand:return ""\n    # Preserve reading order; prefer larger font / upper page. Merge nearby title fragments.\n    cand=sorted(cand,key=lambda s:(round(s.get("bbox",(0,0,0,0))[1],1),s.get("bbox",(0,0,0,0))[0]))\n    top_y=min(s.get("bbox",(0,0,0,0))[1] for s in cand)\n    near=[s for s in cand if s.get("bbox",(0,0,0,0))[1] <= top_y+65]\n    text=" ".join(def_clean(s.get("text","")) for s in near[:4])\n    return re.sub(r"\\s+"," ",text).strip()\n\ndef def_extract_pdf_vrn2(path:Path)->tuple[list[Any],dict[str,Any],dict[int,str]]:\n    layout=VRN_LAYOUT.analyze_pdf_layout(str(path),use_ocr_for_image_only=False)\n    title_map={int(p["page"])+1:def_page_title_from_layout(p) for p in layout}\n    raw_blocks=[]\n    pages=len(layout)\n    for pi in range(pages):\n        try: items=VRN_LAYOUT.extract_blocks_pymupdf(str(path),pi)\n        except Exception: items=[]\n        for j,it in enumerate(items):\n            text=def_clean(getattr(it,"text","") if not isinstance(it,dict) else it.get("text",""))\n            # PyMuPDF blocks often preserve visual line wraps; prose should be semantic sentences, not layout fragments.\n            if len(CORE.NUMBER_RE.findall(text)) < 5:\n                text=re.sub(r"\\s*\\n\\s*"," ",text).strip()\n            if not text or (text.isdigit() and len(text)<=3): continue\n            if re.search(r"本刊所刊載之內容僅做為參考|僅供內部參考|請勿外傳",text):\n                btype="DISCLAIMER"\n            elif text.startswith("資料來源") or text.startswith("Source"):\n                btype="SOURCE"\n            elif CORE.URL_RE.fullmatch(text): btype="URL"\n            else: btype=CORE.def_guess_block_type(text)\n            raw_blocks.append({"page":pi+1,"block_index":j,"text":text,"block_type":btype,"is_title": text==title_map.get(pi+1,"")})\n    # VRN MDL003 nine-step repair. Reflow within each page only: fixes wrapped prose\n    # while preventing cross-page merges and preserving page-level topic boundaries.\n    repaired=[]\n    by_page=defaultdict(list)\n    for b in raw_blocks: by_page[int(b.get("page",1))].append(b)\n    for pg in sorted(by_page): repaired.extend(REPAIR.repair_text_blocks(by_page[pg],reflow=True))\n    blocks=[]\n    for j,b in enumerate(repaired):\n        text=def_clean(b.get("text","")); page=int(b.get("page",1)); btype=b.get("block_type") or CORE.def_guess_block_type(text)\n        sid=f"VRN-P{page:03d}-B{j:04d}-{def_hash8(text)}"\n        blocks.append(CORE.SourceBlock(sid,path.name,page,j,btype,text))\n    meta={\n      "backend":"VRN2_M03_LAYOUT+MDL003_REPAIR",\n      "pages":pages,\n      "layout_module":"VRN_M03_PDF_Layout_JSON_v3",\n      "repair_module":"VRN_MDL003_TableRestorer.TextRepairEngine",\n    }\n    return blocks,meta,title_map\n\n# =============================================================================\n# def 04 SOURCE EXTRACTION / ROUTER\n# =============================================================================\ndef def_extract_source(path: Path) -> tuple[list[Any], dict[str, Any], dict[int, str]]:\n    if path.stat().st_size > CORE.MAX_INPUT_BYTES:\n        raise ValueError("INPUT_BYTES_LIMIT")\n    if path.suffix.lower() == ".pdf":\n        blocks, meta, titles = def_extract_pdf_vrn2(path)\n        if sum(len(b.text) for b in blocks) > CORE.MAX_INPUT_CHARS:\n            raise ValueError("INPUT_CHARACTER_LIMIT")\n        if not blocks:\n            raise ValueError("NO_EXTRACTABLE_TEXT: scanned PDFs require an explicitly configured OCR lane")\n        return blocks, meta, titles\n    blocks, meta = CORE.def_extract_input(path)\n    return blocks, meta, {}\n\n# =============================================================================\n# def 05 TOPIC UNIT SPLITTER — physical boundary first, semantic second\n# =============================================================================\ndef def_message_subunits(block:Any)->list[dict[str,Any]]:\n    text=block.text\n    # Keep strong structural headings; don\'t split on every bullet.\n    pieces=re.split(r"\\n(?=(?:\\d+\\.\\s*(?:結論|重點|內容|評論|拜訪|財報|未來)|\\(\\d+\\)\\s*(?:現況|未來|產能|產品|產業)|\\[[^\\]]{2,20}\\]|《[^》]{2,20}》))",text)\n    out=[]\n    for i,p in enumerate(pieces):\n        p=def_clean(p)\n        if len(p)<TOPIC_MIN_CHARS: continue\n        first=p.splitlines()[0][:80]\n        out.append({"unit_key":f"{block.sid}-T{i+1:02d}","source_unit":block.sid,"title":first,"text":p,"page":block.page})\n    if not out and len(text)>=TOPIC_MIN_CHARS:\n        out=[{"unit_key":f"{block.sid}-T01","source_unit":block.sid,"title":text.splitlines()[0][:80],"text":text,"page":block.page}]\n    return out\n\ndef def_pdf_units(blocks:list[Any],title_map:dict[int,str])->list[dict[str,Any]]:\n    by_page=defaultdict(list)\n    for b in blocks:\n        if b.block_type in {"DISCLAIMER","SOURCE","URL"}: continue\n        by_page[b.page].append(b)\n    units=[]\n    for p in sorted(by_page):\n        txt="\\n".join(b.text for b in by_page[p] if len(b.text)>1)\n        if len(txt)<TOPIC_MIN_CHARS: continue\n        title=title_map.get(p) or next((b.text for b in by_page[p] if b.block_type=="HEADING"),f"Page {p}")\n        # Skip cover-only pages unless they contain meaningful body text.\n        units.append({"unit_key":f"P{p:03d}","source_unit":f"PAGE-{p}","title":def_clip(title,100),"text":txt,"page":p})\n    return units\n\ndef def_build_topic_units(profile:str, blocks:list[Any], title_map:dict[int,str])->list[dict[str,Any]]:\n    if profile==CORE.PROFILE_MESSENGER:\n        # One physical Messenger/LINE message is one detail row. Long Call Memos stay intact;\n        # their internal sections are summarized into the four fixed points instead of exploding rows.\n        return [\n            {"unit_key":f"{b.sid}-T01","source_unit":b.sid,"title":def_clip(b.text.splitlines()[0],100),"text":b.text,"page":b.page}\n            for b in blocks if len(b.text)>=TOPIC_MIN_CHARS\n        ]\n    return def_pdf_units(blocks,title_map) if title_map else [\n        {"unit_key":b.sid,"source_unit":b.sid,"title":def_clip(b.text.splitlines()[0],100),"text":b.text,"page":b.page}\n        for b in blocks if b.block_type not in {"DISCLAIMER","SOURCE","URL"} and len(b.text)>=TOPIC_MIN_CHARS\n    ]\n\n# =============================================================================\n# def 05B REPORT-TYPE ROUTER OVERRIDE — filename/layout wins over semantic noise\n# =============================================================================\ndef def_route_profile(path:Path, blocks:list[Any])->tuple[str,str]:\n    name=path.name.lower()\n    if "test message" in name or "messenger" in name or re.search(r"(?<![a-z])line(?![a-z])", name):\n        return CORE.PROFILE_MESSENGER,"DAILY_MESSAGE_STREAM"\n    if "晨會" in name or "morning meeting" in name:\n        return CORE.PROFILE_OTHER,"MORNING_MEETING"\n    if any(k in name for k in ("盤勢","盤後分析","投資早報","market strategy")):\n        return CORE.PROFILE_OTHER,"MARKET_STRATEGY"\n    if any(k in name for k in ("債券etf周報","債券週報","macro","總經")):\n        return CORE.PROFILE_OTHER,"MACRO_OUTLOOK"\n    if any(k in name for k in ("產業專題","industry","outlook","pcb","thermal solutions","memory","automation","ai power")):\n        return CORE.PROFILE_INDUSTRY,"INDUSTRY_REPORT"\n    return CORE.def_profile_router(path,blocks)\n\n# =============================================================================\n# def 06 CLAIM EXTRACTION PER UNIT + VRN NLP HINT\n# =============================================================================\ndef def_claims_for_unit(path:Path, unit:dict[str,Any], profile:str)->list[Any]:\n    text=unit["text"]\n    if profile==CORE.PROFILE_MESSENGER:\n        # Preserve URL as message metadata upstream, but do not let query strings become investment claims.\n        text=CORE.URL_RE.sub(" ",text)\n    b=CORE.SourceBlock(\n      sid=unit["unit_key"],source_id=path.name,page=unit["page"],block_index=0,\n      block_type="MESSAGE" if profile==CORE.PROFILE_MESSENGER else "TOPIC_UNIT",text=text,note_layer=unit.get("note_layer","SOURCE_CONTENT")\n    )\n    return CORE.def_extract_claims([b])\n\ndef def_vrn_nlp_hint(text:str)->str:\n    # Reuse VRN_M07 only in its extractive/local path; never call transformers/models here.\n    try:\n        hint=VRN_NLP.extractive_summary_fallback(text,NLP_LIBS)\n        return def_clip(hint,500)\n    except Exception:\n        return ""\n\n# =============================================================================\n# def 07 FOUR-POINT SUMMARY CONTRACT\n# =============================================================================\ndef def_claim_score(c:Any)->float:\n    imp={"MUST_KEEP":12,"IMPORTANT":6,"SUPPORTING":1}.get(c.importance,1)\n    score=imp + 2*len(c.metrics) + 1.2*len(c.stories) + .8*min(len(c.tickers),2) + .5*len(c.relations) + .4*len(c.drivers)\n    low=c.text.lower()\n    if len(c.tickers)>=6 or low.startswith(("多單","空單","推薦相關個股")): score-=4\n    if c.text.rstrip().endswith((",","，",":","：")): score-=3\n    if "http://" in low or "https://" in low or "證券研究員" in c.text: score-=5\n    return score\n\ndef def_pick(claims:list[Any], used:set[str], pred, fallback:bool=True)->Optional[Any]:\n    pool=[c for c in claims if c.claim_id not in used and pred(c)]\n    if not pool and fallback: pool=[c for c in claims if c.claim_id not in used]\n    if not pool:return None\n    c=max(pool,key=def_claim_score); used.add(c.claim_id); return c\n\ndef def_four_points(claims: list[Any], title_hint: str = "") -> dict[str, Any]:\n    ranked = sorted(claims, key=def_claim_score, reverse=True)\n    substantive = [claim for claim in ranked if len(claim.text) > 18]\n    thesis = [claim for claim in substantive if not claim.text.startswith(("推薦相關個股", "多單", "空單"))]\n    pools = [thesis,\n             [claim for claim in substantive if claim.drivers or claim.relations],\n             [claim for claim in substantive if claim.tickers or claim.anchors],\n             [claim for claim in substantive if claim.periods or claim.uncertain or claim.conditional\n              or claim.direction == "NEGATIVE" or claim.attribution in {"MANAGEMENT_GUIDANCE", "ANALYST_VIEW"}]]\n    owners = {}\n    selected = [None] * 4\n\n    def assign_slot(slot, visited):\n        for claim in pools[slot]:\n            if claim.claim_id in visited:\n                continue\n            visited.add(claim.claim_id)\n            previous = owners.get(claim.claim_id)\n            if previous is None or assign_slot(previous, visited):\n                owners[claim.claim_id] = slot\n                selected[slot] = claim\n                return True\n        return False\n\n    for slot in sorted(range(4), key=lambda index: (len(pools[index]), index)):\n        assign_slot(slot, set())\n    p1 = selected[0]\n    return {"TITLE": def_clip(title_hint or (p1.text if p1 else "投資情報摘要"), 100),\n            **{f"POINT_{i}": claim.text if claim else "" for i, claim in enumerate(selected, 1)},\n            "DIRECTION": Counter(claim.direction for claim in selected if claim).most_common(1)[0][0] if any(selected) else "NEUTRAL_OR_MIXED",\n            "HORIZON": def_join_unique([period for claim in selected if claim for period in claim.periods]),\n            "EVIDENCE_SIDS": def_join_unique([claim.evidence_sid for claim in selected if claim])}\n\n# =============================================================================\n# def 08 COMPANY RESOLUTION / FINANCIAL QUICK FIELDS\n# =============================================================================\ndef def_company_map(text:str)->dict[str,str]:\n    out={}\n    patterns=[\n      r"([A-Za-z\\u4e00-\\u9fff][A-Za-z0-9\\u4e00-\\u9fff\\-]{1,24})\\s*[（(]([1-9]\\d{3})[）)]",\n      r"(?:即時訊息_|Call Memo_|個股報告_)([1-9]\\d{3})\\s*([^\\n\\r]{1,30})",\n    ]\n    for m in re.finditer(patterns[0],text):\n        ticker,name=m.group(2),m.group(1).strip()\n        if len(name)>len(out.get(ticker,"")): out[ticker]=name\n    for m in re.finditer(patterns[1],text,re.I):\n        ticker=m.group(1); name=re.split(r"\\s|法說會|TT",m.group(2).strip())[0]; out.setdefault(ticker,name)\n    return out\n\ndef def_rating(text:str)->str:\n    m=re.search(r"(?:投資評等|評等)[：:]?\\s*(強力買進|買進|逢低買進|區間操作|中立|持有|賣出|未評等)",text)\n    return m.group(1) if m else ""\n\ndef def_target_price(text:str)->str:\n    m=re.search(r"(?:目標價|6M\\s*目標價)[：:]?\\s*([0-9][0-9,.]*)\\s*元?",text,re.I)\n    return m.group(1).replace(",","") if m else ""\n\ndef def_point_from_claim(c:Optional[Any])->str:\n    return def_clean(c.text) if c else ""\n\ndef def_best_distinct_story_claims(claims:list[Any], n:int=3)->list[Any]:\n    grouped=defaultdict(list)\n    for c in claims:\n        for st in c.stories: grouped[st].append(c)\n    scored=[]\n    for st,cs in grouped.items():\n        best=max(cs,key=def_claim_score)\n        weight=sum({"MUST_KEEP":3,"IMPORTANT":2,"SUPPORTING":1}.get(x.importance,1) for x in cs)\n        scored.append((weight,st,best))\n    out=[]; seen=set()\n    for _,_,best in sorted(scored,key=lambda z:(-z[0],z[1])):\n        if best.claim_id in seen: continue\n        out.append(best); seen.add(best.claim_id)\n        if len(out)>=n: break\n    return out\n\ndef def_special_four(profile:str, subtype:str, claims:list[Any])->Optional[dict[str,Any]]:\n    if not claims:return None\n    used=set(); pts=[]\n    if profile==CORE.PROFILE_MESSENGER:\n        pts=def_best_distinct_story_claims(claims,3)\n        macro=def_pick(claims,{c.claim_id for c in pts},lambda c:bool(c.macro_terms) and len(c.text)>20,False)\n        if macro: pts.append(macro)\n    elif subtype=="MARKET_STRATEGY":\n        p1=def_pick(claims,used,lambda c:any(k in c.text for k in ("操作策略","台股","加權指數","重回","偏多","偏空")) and len(c.text)>20,False)\n        p2=def_pick(claims,used,lambda c:bool(c.stories) and bool(c.drivers or c.relations) and len(c.text)>20)\n        p3=def_pick(claims,used,lambda c:bool(c.tickers) and len(c.tickers)<=5 and len(c.text)>20)\n        p4=def_pick(claims,used,lambda c:c.direction=="NEGATIVE" or c.uncertain or bool(c.periods))\n        pts=[p1,p2,p3,p4]\n    elif subtype=="MORNING_MEETING":\n        seen=set()\n        preferred=sorted(claims,key=lambda c:(c.attribution not in {"ANALYST_VIEW","MANAGEMENT_GUIDANCE"}, -def_claim_score(c)))\n        for c in preferred:\n            if len(c.text)<25 or len(c.text)>260: continue\n            ts=[t for t in c.tickers if t not in seen]\n            if not ts: continue\n            pts.append(c); seen.update(ts)\n            if len(pts)>=4: break\n    elif subtype=="MACRO_OUTLOOK":\n        p1=def_pick(claims,used,lambda c:bool(c.macro_terms) and bool(c.relations or c.drivers) and len(c.text)>25)\n        p2=def_pick(claims,used,lambda c:"RATES_BONDS" in c.stories and len(c.text)>20)\n        p3=def_pick(claims,used,lambda c:bool(c.periods) or c.attribution in {"MANAGEMENT_GUIDANCE","ANALYST_VIEW"})\n        p4=def_pick(claims,used,lambda c:c.direction=="NEGATIVE" or c.uncertain or "風險" in c.text)\n        pts=[p1,p2,p3,p4]\n    else:\n        return None\n    pts=[p for p in pts if p]\n    if not pts:return None\n    while len(pts)<4:\n        nxt=def_pick(claims,{c.claim_id for c in pts},lambda c:len(c.text)>18,False)\n        if not nxt:break\n        pts.append(nxt)\n    direction=Counter(c.direction for c in pts).most_common(1)[0][0]\n    return {"TITLE":"","POINT_1":def_point_from_claim(pts[0] if len(pts)>0 else None),"POINT_2":def_point_from_claim(pts[1] if len(pts)>1 else None),"POINT_3":def_point_from_claim(pts[2] if len(pts)>2 else None),"POINT_4":def_point_from_claim(pts[3] if len(pts)>3 else None),"DIRECTION":direction,"HORIZON":def_join_unique([p for c in pts for p in c.periods]),"EVIDENCE_SIDS":def_join_unique([c.evidence_sid for c in pts])}\n\n# =============================================================================\n# def 09 REPORT-LEVEL SUMMARY — one report, one row\n# =============================================================================\ndef def_report_title(path:Path, profile:str, title_map:dict[int,str], topic_rows:list[dict[str,Any]], report_date:str)->str:\n    if profile==CORE.PROFILE_MESSENGER:\n        return f"{report_date or \'Daily\'} Messenger / 即時投資情報摘要"\n    if "晨會" in path.name:\n        return path.stem\n    if title_map:\n        top=[]\n        for p in sorted(title_map):\n            t=def_clean(title_map[p])\n            if t and t not in top: top.append(t)\n            if len(top)>=2: break\n        if top:return "｜".join(top)\n    return path.stem\n\ndef def_report_summary(path:Path, profile:str, subtype:str, blocks:list[Any], title_map:dict[int,str], all_claims:list[Any], topic_rows:list[dict[str,Any]])->dict[str,Any]:\n    rid=f"RPT-{def_hash8(path.name+def_file_sha(path)[:16])}"\n    # Industry reports: conclusion/outline pages have editorial priority.\n    preferred=[]\n    if title_map:\n        priority_pages={p for p,t in title_map.items() if any(k in t for k in ("結論","簡報大綱","市場焦點","重點"))}\n        preferred=[]; _seen_pref=[]\n        for c in [c for c in all_claims if c.page in priority_pages]:\n            if any(CORE.def_similarity(c.text,x.text)>=0.88 for x in _seen_pref): continue\n            preferred.append(c); _seen_pref.append(c)\n    ordered=(preferred + [c for c in all_claims if c not in preferred]) if preferred else all_claims\n    if profile==CORE.PROFILE_INDUSTRY and preferred:\n        four=def_four_points(preferred,"")\n        # Fill missing slots from the rest without allowing detailed company tables to dominate the main thesis.\n        used_text={four[k] for k in ("POINT_1","POINT_2","POINT_3","POINT_4") if four[k]}\n        for key,pred in [\n            ("POINT_1",lambda c:len(c.text)>20),\n            ("POINT_2",lambda c:bool(c.drivers or c.relations)),\n            ("POINT_3",lambda c:bool(c.tickers or c.anchors)),\n            ("POINT_4",lambda c:bool(c.periods) or c.uncertain or c.direction=="NEGATIVE"),\n        ]:\n            if four[key]: continue\n            cand=next((c for c in sorted(all_claims,key=def_claim_score,reverse=True) if pred(c) and c.text not in used_text),None)\n            if cand: four[key]=def_clean(cand.text); used_text.add(cand.text)\n    else:\n        four=def_special_four(profile,subtype,ordered) or def_four_points(ordered,"")\n    story_scores=Counter()\n    for c in all_claims:\n        for st in c.stories: story_scores[st]+={"MUST_KEEP":3,"IMPORTANT":2,"SUPPORTING":1}.get(c.importance,1)\n    main_story=story_scores.most_common(1)[0][0] if story_scores else ""\n    company_map=def_company_map("\\n".join(b.text for b in blocks))\n    all_company_tickers=set(company_map) | {t for c in all_claims for t in c.tickers}\n    rdate=def_report_date(path,blocks)\n    four["TITLE"]=def_report_title(path,profile,title_map,topic_rows,rdate)\n    if not four["POINT_3"] and company_map:\n        four["POINT_3"]="涉及公司："+"、".join(f"{n}({t})" for t,n in list(company_map.items())[:8])\n    status="PASS" if sum(bool(four[k]) for k in ("POINT_1","POINT_2","POINT_3","POINT_4"))>=3 else "REVIEW"\n    return {\n      "REPORT_ID":rid,"REPORT_DATE":rdate,"FILE_NAME":path.name,\n      "REPORT_TYPE":profile if profile!=CORE.PROFILE_OTHER else subtype,\n      "SOURCE":"MULTI_SOURCE" if profile==CORE.PROFILE_MESSENGER else def_source_name(path,blocks),"ANALYST_AUTHOR":"" if profile==CORE.PROFILE_MESSENGER else def_author(blocks),\n      "MAIN_STORY":main_story,"MAIN_INDUSTRY":INDUSTRY_MAP.get(main_story,main_story),\n      "TITLE":four["TITLE"],"POINT_1":four["POINT_1"],"POINT_2":four["POINT_2"],"POINT_3":four["POINT_3"],"POINT_4":four["POINT_4"],\n      "DIRECTION":four["DIRECTION"],"HORIZON":four["HORIZON"],\n      "COMPANY_COUNT":len(all_company_tickers),"TOPIC_COUNT":len(topic_rows),"EVIDENCE_COUNT":len(all_claims),\n      "LAYOUT_ENGINE":"VRN_M03_PDF_Layout_JSON_v3" if path.suffix.lower()==".pdf" else "CORE_INPUT_PARSER",\n      "TEXT_REPAIR_ENGINE":"VRN_MDL003_TextRepairEngine" if path.suffix.lower()==".pdf" else "CORE_NORMALIZER",\n      "NLP_ENGINE":"VRN_M07_EXTRACTIVE+NONSTOCK_CORE_v0200",\n      "STATUS":status,"DETAIL_REF":rid,\n    }\n\n# =============================================================================\n# def 10 TOPIC / COMPANY / EVIDENCE TABLE BUILDERS\n# =============================================================================\ndef def_topic_rows(path:Path, report_id:str, profile:str, units:list[dict[str,Any]])->tuple[list[dict[str,Any]],list[Any]]:\n    rows=[]; all_claims=[]\n    for i,u in enumerate(units,1):\n        claims=def_claims_for_unit(path,u,profile); all_claims.extend(claims)\n        if not claims: continue\n        four=def_four_points(claims,u.get("title",f"Topic {i}"))\n        sc=Counter(s for c in claims for s in c.stories); story=sc.most_common(1)[0][0] if sc else ""\n        tickers=sorted({t for c in claims for t in c.tickers}); anchors=sorted({a for c in claims for a in c.anchors})\n        rows.append({\n          "REPORT_ID":report_id,"TOPIC_ID":f"{report_id}-T{i:03d}","SOURCE_UNIT":u["source_unit"],"TOPIC_TITLE":u.get("title","")[:120],\n          "STORY_L1":story,"INDUSTRY":INDUSTRY_MAP.get(story,story),\n          "TITLE":four["TITLE"],"POINT_1":four["POINT_1"],"POINT_2":four["POINT_2"],"POINT_3":four["POINT_3"],"POINT_4":four["POINT_4"],\n          "DIRECTION":four["DIRECTION"],"HORIZON":four["HORIZON"],"TICKERS":def_join_unique(tickers),"GLOBAL_ANCHORS":def_join_unique(anchors),\n          "EVIDENCE_SIDS":four["EVIDENCE_SIDS"],"NLP_HINT":def_vrn_nlp_hint(u["text"]),"STATUS":"PASS"\n        })\n    return rows,all_claims\n\ndef def_company_rows(report_id: str, blocks: list[Any], claims: list[Any]) -> list[dict[str, Any]]:\n    names = def_company_map("\\n".join(b.text for b in blocks))\n    rows = []\n    for ticker in sorted({ticker for claim in claims for ticker in claim.tickers} | set(names)):\n        company_claims = [claim for claim in claims if ticker in claim.tickers]\n        if not company_claims:\n            continue\n        four = def_four_points(company_claims, f"{names.get(ticker, ticker)} ({ticker})")\n        unambiguous = [claim for claim in company_claims if claim.tickers == [ticker]]\n        ratings = sorted({def_rating(claim.text) for claim in unambiguous} - {""})\n        targets = sorted({def_target_price(claim.text) for claim in unambiguous} - {""})\n        issues = []\n        if len(ratings) > 1 or len(targets) > 1:\n            issues.append("FINANCIAL_FIELD_CONFLICT")\n        if any(len(claim.tickers) > 1 and (def_rating(claim.text) or def_target_price(claim.text)) for claim in company_claims):\n            issues.append("MULTI_COMPANY_FINANCIAL_AMBIGUITY")\n        stories = sorted({story for claim in company_claims for story in claim.stories})\n        row = {"REPORT_ID": report_id, "TICKER": ticker, "COMPANY_NAME": names.get(ticker, ""),\n               "STORIES": def_join_unique(stories), "INDUSTRY": INDUSTRY_MAP.get(stories[0], stories[0]) if stories else "",\n               "RATING": ratings[0] if len(ratings) == 1 else "",\n               "TARGET_PRICE": targets[0] if len(targets) == 1 else "", **four,\n               "STATUS": "REVIEW" if issues else "PASS", "VALIDATION_ISSUES": ";".join(issues)}\n        rows.append(row)\n    return rows\n\ndef def_evidence_rows(report_id:str,claims:list[Any])->list[dict[str,Any]]:\n    return [{\n      "REPORT_ID":report_id,"CLAIM_ID":c.claim_id,"EVIDENCE_SID":c.evidence_sid,"PAGE":c.page,"ATTRIBUTION":c.attribution,\n      "IMPORTANCE":c.importance,"DIRECTION":c.direction,"STORIES":def_join_unique(c.stories),"TICKERS":def_join_unique(c.tickers),\n      "DRIVERS":def_join_unique(c.drivers),"RELATIONS":def_join_unique(c.relations),"PERIODS":def_join_unique(c.periods),"TEXT":c.text\n    } for c in claims]\n\n# =============================================================================\n# def 11 SINGLE FILE ANALYSIS\n# =============================================================================\ndef def_analyze_one(path: Path, prior_path: Optional[Path] = None) -> dict[str, Any]:\n    path = Path(path)\n    before = def_file_sha(path)\n    blocks, meta, title_map = def_extract_source(path)\n    profile, subtype = def_route_profile(path, blocks)\n    if profile == CORE.PROFILE_MESSENGER:\n        blocks = CORE.def_parse_messenger_blocks(path, blocks)\n    if profile == CORE.PROFILE_EVERNOTE:\n        blocks = CORE.def_apply_note_layers(blocks)\n    units = def_build_topic_units(profile, blocks, title_map)\n    by_sid = {block.sid: block for block in blocks}\n    unit_blocks = []\n    for unit in units:\n        source = by_sid.get(unit["source_unit"])\n        unit["note_layer"] = source.note_layer if source else "SOURCE_CONTENT"\n        block = CORE.SourceBlock(unit["unit_key"], path.name, unit["page"], len(unit_blocks),\n                                 "MESSAGE" if profile == CORE.PROFILE_MESSENGER else "TOPIC_UNIT", unit["text"],\n                                 note_layer=unit["note_layer"])\n        unit_blocks.append(block)\n    core = CORE.def_analyze_blocks(path, unit_blocks or blocks, meta, profile, subtype, prior_path)\n    claims = [CORE.Claim(**record) for record in core["claims"]]\n    report_id = "RPT-" + hashlib.sha256((str(path.resolve()) + "\\0" + before).encode("utf-8")).hexdigest()[:24].upper()\n    topics, _ = def_topic_rows(path, report_id, profile, units)\n    report = def_report_summary(path, profile, subtype, blocks, title_map, claims, topics)\n    report["LEGACY_REPORT_ID"] = report["REPORT_ID"]\n    report["REPORT_ID"] = report["DETAIL_REF"] = report_id\n    report["NLP_ENGINE"] = "VRN_M07_LOCAL_EXTRACTIVE+NON_STOCK_CORE_v0400"\n    companies = def_company_rows(report_id, blocks, claims)\n    report["COMPANY_COUNT"] = len(companies)\n    report["EVIDENCE_COUNT"] = len(claims)\n    checks = {"report": def_validate_points(report, claims), "topics": {}, "companies": {}}\n    for row in topics:\n        row["REPORT_ID"] = report_id\n        checks["topics"][row["TOPIC_ID"]] = def_validate_points(row, claims)\n    for row in companies:\n        checks["companies"][row["TICKER"]] = def_validate_points(row, [claim for claim in claims if row["TICKER"] in claim.tickers])\n    if core["quality"]["gate"] != "PASS" or any(row["STATUS"] != "PASS" for row in topics + companies):\n        report["STATUS"] = "REVIEW"\n    evidence = def_evidence_rows(report_id, claims)\n    valid_ids = {claim.claim_id for claim in claims}\n    for scope in [checks["report"], *checks["topics"].values(), *checks["companies"].values()]:\n        if any(not set(check["claim_ids"]).issubset(valid_ids) for check in scope):\n            raise RuntimeError("EVIDENCE_REFERENTIAL_INTEGRITY")\n    if len(valid_ids) != len(claims) or len(evidence) != report["EVIDENCE_COUNT"]:\n        raise RuntimeError("CLAIM_ID_OR_COUNT_MISMATCH")\n    if def_file_sha(path) != before:\n        raise RuntimeError("SOURCE_CHANGED_DURING_ANALYSIS")\n    return {"report": report, "topics": topics, "companies": companies, "evidence": evidence,\n            "meta": {**meta, "source_sha256": before, "source_path": str(path.resolve())},\n            "title_map": title_map, "core": core, "point_validation": checks}\n\n# =============================================================================\n# def 12 BATCH / OUTPUT\n# =============================================================================\ndef def_collect_inputs(inputs:list[str])->list[Path]:\n    out=[]; allowed={".pdf",".txt",".md",".html",".htm",".docx",".enex",".json"}\n    for raw in inputs:\n        p=Path(raw)\n        if p.is_dir(): out.extend(sorted(x for x in p.iterdir() if x.is_file() and x.suffix.lower() in allowed))\n        elif p.is_file() and p.suffix.lower() in allowed: out.append(p)\n    return out\n\ndef def_write_csv(path:Path,cols:list[str],rows:list[dict[str,Any]])->None:\n    with path.open(\'w\',newline=\'\',encoding=\'utf-8-sig\') as f:\n        w=csv.DictWriter(f,fieldnames=cols,extrasaction=\'ignore\'); w.writeheader(); w.writerows(rows)\n\ndef def_write_parquet_if_available(path:Path,rows:list[dict[str,Any]])->str:\n    if not rows:return ""\n    try:\n        import pandas as pd\n        pd.DataFrame(rows).to_parquet(path,index=False); return str(path)\n    except Exception:return ""\n\ndef def_render_html(reports:list[dict[str,Any]],topics:list[dict[str,Any]],companies:list[dict[str,Any]])->str:\n    trs="".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,\'\')))}</td>" for c in ["REPORT_DATE","REPORT_TYPE","SOURCE","MAIN_STORY","TITLE","POINT_1","POINT_2","POINT_3","POINT_4","STATUS"])+"</tr>" for r in reports)\n    trows="".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,\'\')))}</td>" for c in ["REPORT_ID","TOPIC_TITLE","STORY_L1","TITLE","POINT_1","POINT_2","POINT_3","POINT_4"])+"</tr>" for r in topics[:MAX_TOPICS_PER_REPORT_HTML*max(1,len(reports))])\n    crows="".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,\'\')))}</td>" for c in ["REPORT_ID","TICKER","COMPANY_NAME","STORIES","RATING","TARGET_PRICE","POINT_1","POINT_4"])+"</tr>" for r in companies[:MAX_COMPANIES_PER_REPORT_HTML*max(1,len(reports))])\n    return f"""<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>NON-STOCK SUMMARIZER v0400</title>\n<style>body{{font:11px/1.45 Segoe UI,Noto Sans TC,sans-serif;background:#f4f5f7;margin:0;color:#222}}main{{padding:14px;max-width:1800px;margin:auto}}h1{{font-size:18px}}h2{{font-size:14px;margin-top:18px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{border-bottom:1px solid #ddd;padding:5px;vertical-align:top;text-align:left}}th{{position:sticky;top:0;background:#eee}}.note{{background:#fff;border:1px solid #ddd;padding:8px;border-radius:7px}}</style><main>\n<h1>VIA NON-STOCK SUMMARIZER ENGINE v0400</h1><div class="note">One Report = One Main Row · VRN-2 Layout + Text Repair + NLP reused · Detail on demand</div>\n<h2>REPORT_SUMMARY</h2><table><thead><tr>{\'\'.join(f\'<th>{c}</th>\' for c in [\'DATE\',\'TYPE\',\'SOURCE\',\'STORY\',\'TITLE\',\'P1\',\'P2\',\'P3\',\'P4\',\'STATUS\'])}</tr></thead><tbody>{trs}</tbody></table>\n<h2>TOPIC_DETAIL</h2><table><thead><tr>{\'\'.join(f\'<th>{c}</th>\' for c in [\'REPORT\',\'TOPIC\',\'STORY\',\'TITLE\',\'P1\',\'P2\',\'P3\',\'P4\'])}</tr></thead><tbody>{trows}</tbody></table>\n<h2>COMPANY_DETAIL</h2><table><thead><tr>{\'\'.join(f\'<th>{c}</th>\' for c in [\'REPORT\',\'TICKER\',\'COMPANY\',\'STORIES\',\'RATING\',\'TP\',\'P1\',\'P4\'])}</tr></thead><tbody>{crows}</tbody></table></main></html>"""\n\ndef def_legacy_integrated_run(inputs:list[str],outdir:Path)->dict[str,Any]:\n    paths=def_collect_inputs(inputs); outdir.mkdir(parents=True,exist_ok=True)\n    reports=[];topics=[];companies=[];evidence=[];runs=[]\n    for p in paths:\n        try:\n            x=def_analyze_one(p); reports.append(x["report"]); topics+=x["topics"]; companies+=x["companies"]; evidence+=x["evidence"]\n            runs.append({"file":p.name,"status":"PASS","report_id":x["report"]["REPORT_ID"],"topics":len(x["topics"]),"companies":len(x["companies"]),"evidence":len(x["evidence"]),"backend":x["meta"].get("backend")})\n        except Exception as e:\n            runs.append({"file":p.name,"status":"ERROR","error":f"{type(e).__name__}: {e}"})\n    def_write_csv(outdir/\'REPORT_SUMMARY.csv\',REPORT_COLUMNS,reports)\n    def_write_csv(outdir/\'TOPIC_DETAIL.csv\',TOPIC_COLUMNS,topics)\n    def_write_csv(outdir/\'COMPANY_DETAIL.csv\',COMPANY_COLUMNS,companies)\n    def_write_csv(outdir/\'EVIDENCE_DETAIL.csv\',EVIDENCE_COLUMNS,evidence)\n    pq={\n      "report":def_write_parquet_if_available(outdir/\'REPORT_SUMMARY.parquet\',reports),\n      "topic":def_write_parquet_if_available(outdir/\'TOPIC_DETAIL.parquet\',topics),\n      "company":def_write_parquet_if_available(outdir/\'COMPANY_DETAIL.parquet\',companies),\n      "evidence":def_write_parquet_if_available(outdir/\'EVIDENCE_DETAIL.parquet\',evidence),\n    }\n    (outdir/\'REPORT_SUMMARY.html\').write_text(def_render_html(reports,topics,companies),encoding=\'utf-8\')\n    payload={\n      "engine_id":ENGINE_ID,"version":ENGINE_VERSION,"network_allowed":False,\n      "reuse_hard_gate":"PASS","reuse_status":REUSE_STATUS,\n      "reused_modules":["VRN_M03_PDF_Layout_JSON_v3","VRN_MDL003_TableRestorer.TextRepairEngine","VRN_M07_Summarizer.extractive_summary_fallback","NON_STOCK_CORE_v0200"],\n      "runs":runs,"report_summary":reports,"topic_detail":topics,"company_detail":companies,\n      "parquet":pq,\n    }\n    (outdir/\'RESULTS.json\').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding=\'utf-8\')\n    return payload\n\n# =============================================================================\n# def 13 DOCTOR / SELFTEST / CLI\n# =============================================================================\ndef def_doctor()->dict[str,Any]:\n    return {\n      "engine":ENGINE_NAME,"version":ENGINE_VERSION,"network_allowed":False,\n      "reuse_hard_gate":"PASS",\n      "reuse_status":REUSE_STATUS,\n      "modules":{\n        "layout":"VRN_M03_PDF_Layout_JSON_v3 (BUNDLED)",\n        "text_repair":"VRN_MDL003_TableRestorer.TextRepairEngine (BUNDLED)",\n        "nlp":"VRN_M07_Summarizer.extractive_summary_fallback (BUNDLED)",\n        "core":"NON_STOCK_CORE_v0200 (BUNDLED)",\n      },\n      "output_tables":["REPORT_SUMMARY","TOPIC_DETAIL","COMPANY_DETAIL","EVIDENCE_DETAIL"],\n      "contract":"ONE_REPORT_ONE_ROW + ONE_TITLE_FOUR_POINTS + DETAILS_ON_DEMAND",\n    }\n\ndef def_selftest()->int:\n    checks=[]\n    checks.append(("layout_loaded",hasattr(VRN_LAYOUT,"analyze_pdf_layout")))\n    checks.append(("repair_loaded",hasattr(REPAIR,"repair_text_blocks")))\n    checks.append(("nlp_loaded",hasattr(VRN_NLP,"extractive_summary_fallback")))\n    c=CORE.Claim("c","s","e","CSP CAPEX上調帶動ASIC需求成長",1,"x","SOURCE_FACT_OR_REPORTED_DATA","POSITIVE",False,False,"IMPORTANT",stories=["ASIC_CUSTOM_SILICON"],drivers=["CAPEX","DEMAND"])\n    four=def_four_points([c],"ASIC")\n    checks.append(("four_point_contract",bool(four["POINT_1"])))\n    checks.append(("network_off",NETWORK_ALLOWED is False))\n    ok=sum(bool(v) for _,v in checks)\n    print(json.dumps({"passed":ok,"total":len(checks),"checks":checks},ensure_ascii=False,indent=2))\n    return 0 if ok==len(checks) else 1\n\ndef def_main(argv:Optional[list[str]]=None)->int:\n    p=argparse.ArgumentParser(description=ENGINE_NAME)\n    p.add_argument("inputs",nargs="*")\n    p.add_argument("--outdir",default="output")\n    p.add_argument("--doctor",action="store_true")\n    p.add_argument("--selftest",action="store_true")\n    args=p.parse_args(argv)\n    if args.doctor: print(json.dumps(def_doctor(),ensure_ascii=False,indent=2)); return 0\n    if args.selftest: return def_selftest()\n    if not args.inputs: p.error("Provide one or more files/folders")\n    result=def_run(args.inputs,Path(args.outdir))\n    errors=sum(r.get("status")!="PASS" for r in result["runs"])\n    print(json.dumps({"runs":result["runs"],"outdir":str(Path(args.outdir).resolve())},ensure_ascii=False,indent=2))\n    return 0 if errors==0 else 2\n\n\n\ndef def_validate_points(row: dict[str, Any], claims: list[Any]) -> list[dict[str, Any]]:\n    """An exact source sentence is evidence fidelity, not independent factual verification."""\n    checks = []\n    refs = []\n    for key in ("POINT_1", "POINT_2", "POINT_3", "POINT_4"):\n        text = row.get(key, "")\n        matches = [claim for claim in claims if claim.text == text] if text else []\n        checks.append({"field": key, "present": bool(text), "source_exact_match": bool(matches),\n                       "claim_ids": [claim.claim_id for claim in matches],\n                       "evidence_sids": sorted({claim.evidence_sid for claim in matches})})\n        refs.extend(claim.evidence_sid for claim in matches)\n    row["EVIDENCE_SIDS"] = def_join_unique(refs)\n    if not all(check["source_exact_match"] for check in checks):\n        row["STATUS"] = "REVIEW"\n    return checks\n'}

ENGINE_ID = "VIA-NON-STOCK-CORE-UNIFIED"
ENGINE_VERSION = "v0400"
ENGINE_NAME = "VIA NON-STOCK SUMMARIZER ENGINE"
NETWORK_ALLOWED = False
MAX_INPUT_CHARS = 3_000_000
FLASH_BULLETS = 5
INVESTMENT_BULLETS = 10
EVIDENCE_VIEW_BULLETS = 40
SECTION_BULLETS = 5
MIN_SENTENCE_CHARS = 9
MAX_CLAIMS_PER_SOURCE = 5000
EVENT_SIMILARITY_THRESHOLD = 0.46
NEAR_DUP_THRESHOLD = 0.86
NOVELTY_THRESHOLD = 0.70
CONTRADICTION_NUM_TOL = 0.03
SUMMARY_MUST_KEEP_TARGET = 0.90
SUMMARY_IMPORTANT_TARGET = 0.75

PROFILE_INDUSTRY = "INDUSTRY_OUTLOOK"
PROFILE_MESSENGER = "MESSENGER_INTELLIGENCE"
PROFILE_EVERNOTE = "EVERNOTE_INTELLIGENCE"
PROFILE_OTHER = "OTHER_INVESTMENT_INTELLIGENCE"

VIA_SEARCH_ROOTS = [
    Path(os.environ["VIA_ROOT"]) if os.environ.get("VIA_ROOT") else None,
    Path.home()/"OneDrive"/"Documents"/"movies-dataset"/"VeritasIntelligenceAnalytics",
    Path.home()/"Github"/"VIA-VDF-VRN",
]

PROFILE_TERMS = {
    PROFILE_INDUSTRY: ("產業專題","產業展望","供應鏈","industry outlook","industry report","產業報告","產業看法"),
    PROFILE_MESSENGER: ("即時訊息_","call memo_","早安","line today","☎","盤後","精華版","僅供內部參考"),
    PROFILE_EVERNOTE: ("evernote","en-media","en-note","source-url","note-attributes"),
}
OTHER_SUBTYPE_TERMS = {
    "MARKET_STRATEGY": ("盤勢","盤後分析","市場策略","投資早報","market strategy"),
    "MACRO_OUTLOOK": ("總經","債券","利率","殖利率","fed","央行","macro","bond"),
    "MORNING_MEETING": ("晨會","morning meeting"),
    "NEWS_EVENT": ("新聞","news","快訊","headline"),
    "MULTI_COMPANY_NOTE": ("公司訪談摘要","summit","conference","多公司"),
}

STORY_TAXONOMY = {
    "AI_INFRASTRUCTURE": ("ai infrastructure","ai基礎建設","ai基建","ai伺服器","ai server","gpu server","csp","hyperscaler","neocloud","ai factory"),
    "ASIC_CUSTOM_SILICON": ("asic","custom silicon","自研晶片","ai晶片","設計服務","cot模式","trainium","trn3","trn4"),
    "AI_THERMAL": ("散熱","水冷","液冷","冷板","cold plate","cdu","mcl","micro channel lid","cooling"),
    "MEMORY": ("記憶體","dram","nand","hbm","flash","快閃記憶體","memory"),
    "PCB_MATERIALS": ("pcb","abf","載板","ccl","銅箔基板","玻纖布","fpc","hdi","軟板","硬板","substrate"),
    "CPO_OPTICAL": ("cpo","光通訊","光收發","光模組","矽光子","silicon photonics","1.6t","800g","optical"),
    "FOUNDRY_ADVANCED": ("晶圓代工","foundry","2nm","n2","a16","gaa","先進製程","finfet","wafer"),
    "ADVANCED_PACKAGING": ("cowos","先進封裝","chiplet","2.5d","3d封裝","hybrid bonding"),
    "SEMICONDUCTOR_MATERIALS": ("半導體材料","矽晶圓","特用化學","特殊氣體","光阻","photoresist","precursor","slurry"),
    "SEMICONDUCTOR_EQUIPMENT": ("半導體設備","曝光","蝕刻","沉積","檢測","量測","euv","lithography","etch","deposition","inspection","metrology","cmp"),
    "AEROSPACE": ("航太","航空","客機","mro","boeing","airbus","商用航空"),
    "DEFENSE_DRONE": ("國防","軍工","無人機","飛彈","雷達","防衛","gcs"),
    "ROBOTICS_PHYSICAL_AI": ("機器人","robot","amr","協作機器人","physical ai","實體ai","飛控","減速機","伺服馬達","servo motor"),
    "EV_AUTOMOTIVE": ("電動車","ev","bms","e-axle","逆變器","車載","automotive"),
    "SHIPPING": ("航運","貨櫃","散裝","貨櫃運價","海運運價","scfi","ccfi","container shipping","bulk shipping","塞港"),
    "RATES_BONDS": ("fed","聯準會","利率","殖利率","公債","債券","升息","降息","treasury","yield"),
    "ENERGY_GEOPOLITICS": ("原油","布蘭特","中東","伊朗","胡塞","地緣政治","oil","荷姆茲","hormuz"),
    "DISPLAY_ESL": ("電子紙","esl","signage","數位看板","ereader","enote"),
    "CDMO_PHARMA": ("cdmo","學名藥","藥證","fda","無菌針劑","罕病","製藥"),
    "POWER_GRID": ("重電","電網","變壓器","輸配電","grid","power"),
}
GLOBAL_ANCHORS = {
    "NVIDIA": ("nvidia","輝達"), "AMD": ("amd",), "BROADCOM": ("broadcom","博通"),
    "MARVELL": ("marvell","mrvl"), "TSMC": ("台積電","tsmc"), "BOEING": ("boeing","波音"),
    "AIRBUS": ("airbus","空中巴士"), "MICRON": ("micron","美光"), "SAMSUNG": ("samsung","三星"),
    "SANDISK": ("sandisk",), "WESTERN_DIGITAL": ("western digital","wdc"), "ASML": ("asml",),
    "APPLIED_MATERIALS": ("applied materials","amat","應用材料"), "LAM_RESEARCH": ("lam research",),
    "KLA": ("kla",), "AMAZON_AWS": ("amazon","aws"), "MICROSOFT": ("microsoft","msft"),
    "META": ("meta",), "GOOGLE": ("google","alphabet"),
}
MACRO_TERMS = ("fed","聯準會","cpi","pce","ppi","pmi","gdp","非農","殖利率","升息","降息","通膨","美元","匯率","央行","原油","黃金","dxy","失業","零售銷售","消費者信心")
FACT_CUES = ("公告","公布","營收","eps","毛利率","營業利益","淨利","出貨","產能","capex","市占率","訂單","持股","收盤","殖利率")
OPINION_CUES = ("我們認為","本中心認為","看好","看法","預估","預期","預計","有望","可望","建議","維持正向","偏多","偏空","目標價")
MANAGEMENT_CUES = ("公司表示","管理層表示","公司預期","公司預估","公司目標","管理層認為","公司認為","指引","guidance")
RUMOR_CUES = ("市場傳出","傳聞","據傳","市場消息","未證實","rumor")
USER_NOTE_CUES = ("我認為","我覺得","我的看法","note:","備註:","註記:")
POSITIVE_CUES = ("成長","上調","上修","受惠","增加","改善","復甦","擴張","強勁","正向","領漲","突破","創新高","優於預期","滿載","放量")
NEGATIVE_CUES = ("下調","下修","衰退","惡化","下降","承壓","風險","延遲","需求疲弱","虧損","下滑","拋售","壓抑","低於預期","缺貨")
UNCERTAINTY_CUES = ("可能","或許","有機會","尚未","仍待","不確定","觀察","若","如果","視","取決於")
DRIVER_TERMS = {
    "DEMAND": ("需求","訂單","客戶","出貨","銷售","滲透率"), "SUPPLY": ("供給","供應","缺貨","產能","稼動率","庫存"),
    "PRICE": ("價格","售價","asp","報價","漲價","降價"), "MARGIN": ("毛利率","營業利益率","margin","opm"),
    "COST": ("成本","原物料","費用","燃油","記憶體價格"), "CAPEX": ("capex","資本支出","擴產","建廠","新廠"),
    "PRODUCT_MIX": ("產品組合","比重","mix"), "CUSTOMER": ("客戶","csp","hyperscaler","品牌"),
    "INVENTORY": ("庫存","備貨","stocking"), "REGULATION": ("法案","政策","監管","法規","關稅","補貼"),
    "FX": ("匯率","美元","日圓","新台幣","匯兌"), "INTEREST_RATE": ("利率","殖利率","升息","降息","fed"),
    "TECHNOLOGY": ("製程","技術","平台","架構","產品世代","roadmap"),
}
RELATION_CUES = {
    "DRIVES": ("帶動","推動","驅動","拉動"), "BENEFITS_FROM": ("受惠","受益"), "CAUSED_BY": ("主因","由於","因為","反映"),
    "SUPPLIES": ("供應","供貨","出貨給"), "CUSTOMER_OF": ("客戶","供應鏈"), "UPSTREAM_DOWNSTREAM": ("上游","下游","供應鏈"),
    "SUBSTITUTES": ("替代","取代"), "COMPETES_WITH": ("競爭","同業"),
}
CATALYST_CUES = ("催化","法說","量產","放量","上市","擴產","capex","新品","決策","導入")
RISK_CUES = ("風險","不確定","壓力","下行","downside","延遲","缺貨","供過於求","成本上升")

TW_TICKER_RE = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
TW_TICKER_PAREN_RE = re.compile(r"\(([1-9]\d{3})(?:\s*TT)?\)", re.I)
TW_TICKER_HEADER_RE = re.compile(r"(?:即時訊息_|Call Memo_|個股報告_|_)([1-9]\d{3})(?!\d)", re.I)
TW_TICKER_TT_RE = re.compile(r"(?<!\d)([1-9]\d{3})\s*TT\b", re.I)
TW_TICKER_LABEL_RE = re.compile(r"(?:代號|股號|ticker)\s*[:：]?\s*([1-9]\d{3})(?!\d)", re.I)
US_TICKER_US_RE = re.compile(r"(?:\(|\b)([A-Z]{1,5})\s+US(?:\)|\b)", re.I)
US_TICKER_LABEL_RE = re.compile(r"(?:代號|ticker)\s*[:：]\s*([A-Z]{1,5})\b", re.I)
NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?(?:\s*(?:%|億元|百萬元|兆元|兆|億|萬|美元|元|倍|x|bps|ppts|ppt|架|人次|萬櫃|萬台))?", re.I)
PERIOD_RE = re.compile(r"(?<![A-Za-z0-9])(?:20\d{2}[.]?Q[1-4]|20\d{2}年?|FY\s*[- ]?\d{2,4}|[1-4]Q\d{2,4}|[12]H\d{2,4}|\d{1,2}M\d{2}|\d{1,2}月)(?![A-Za-z0-9])", re.I)
MESSAGE_HEADER_RE = re.compile(r"^\s*(\d{1,2}:\d{2})\s+(.+?)\s*$")
DATE_LINE_RE = re.compile(r"^\s*(?:(20\d{2})[/-](\d{1,2})[/-](\d{1,2})|(20\d{2})年(\d{1,2})月(\d{1,2})日)\s*$")
URL_RE = re.compile(r"https?://\S+")
METRIC_PATTERNS = {
    "EPS": re.compile(r"\bEPS\s*[:：]?\s*([+-]?[0-9]+(?:\.[0-9]+)?)", re.I),
    "REVENUE_YOY": re.compile(r"(?:營收[^。\n]{0,80}?|revenue[^。\n]{0,80}?)(YoY|年增|年減)\s*([+-]?\d+(?:\.\d+)?)\s*%", re.I),
    "REVENUE_QOQ": re.compile(r"(?:營收[^。\n]{0,80}?|revenue[^。\n]{0,80}?)(QoQ|季增|季減)\s*([+-]?\d+(?:\.\d+)?)\s*%", re.I),
    "GM": re.compile(r"(?:毛利率|gross margin)\s*([0-9]+(?:\.[0-9]+)?)\s*%", re.I),
    "TP": re.compile(r"(?:目標價|target price)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
    "CAPEX": re.compile(r"(?:CAPEX|資本支出)[^。\n]{0,30}?([0-9]+(?:\.[0-9]+)?)\s*(億元|億|百萬美元|美元)?", re.I),
}

# =============================================================================
# def 01 DATA STRUCTURES
# =============================================================================

# Canonical taxonomy merge from v0100; matching uses token boundaries.
LEGACY_TAXONOMY_ALIASES = {'AI_INFRASTRUCTURE': ['AI', '人工智慧', 'AI伺服器', 'AI server', 'GPU', 'TPU', 'CSP', '資料中心', 'data center', 'AI agent', 'ASIC'], 'ASIC_CUSTOM_SILICON': ['ASIC', 'custom silicon', '自研晶片', 'AI晶片', '設計服務', '矽智財'], 'AI_THERMAL': ['散熱', '水冷', '液冷', 'MCL', 'Micro Channel Lid', 'cold plate', 'CDU'], 'MEMORY': ['記憶體', 'DRAM', 'NAND', 'HBM', 'flash', '快閃記憶體'], 'PCB_MATERIALS': ['PCB', 'ABF', '載板', 'CCL', '銅箔基板', '玻纖布', 'FPC', 'HDI', '軟板', '硬板'], 'CPO_OPTICAL': ['CPO', '光通訊', '光收發', '光模組', '矽光子', 'silicon photonics', '1.6T', '800G'], 'FOUNDRY_ADVANCED': ['晶圓代工', 'foundry', '2nm', 'N2', 'A16', 'GAA', '先進製程'], 'SEMICONDUCTOR_MATERIALS': ['半導體材料', '矽晶圓', '特用化學', '特殊氣體', '光阻', 'wafer', 'photoresist'], 'SEMICONDUCTOR_EQUIPMENT': ['半導體設備', '半導體檢測', '半導體量測', '曝光機', '蝕刻機', '沉積設備', 'EUV', 'lithography', 'etch', 'deposition', 'inspection', 'metrology'], 'AEROSPACE': ['航太', '航空', '客機', 'MRO', 'Boeing', 'Airbus', '商用航空'], 'DEFENSE_DRONE': ['國防', '軍工', '無人機', '飛彈', '雷達', '防衛'], 'ROBOTICS_PHYSICAL_AI': ['機器人', 'robot', 'AMR', '協作機器人', '伺服', '減速機'], 'EV_AUTOMOTIVE': ['電動車', 'EV', '電池', 'BMS', 'e-Axle', '逆變器'], 'SHIPPING': ['航運', '貨櫃', '散裝', '運價', 'container', 'bulk shipping'], 'RATES_BONDS': ['Fed', '聯準會', '利率', '殖利率', '公債', '債券', '升息', '降息', 'Treasury'], 'ENERGY_GEOPOLITICS': ['原油', '布蘭特', '中東', '伊朗', '胡塞', '地緣政治', 'oil']}
for _story, _aliases in LEGACY_TAXONOMY_ALIASES.items():
    STORY_TAXONOMY[_story] = tuple(dict.fromkeys((*STORY_TAXONOMY.get(_story, ()), *_aliases)))

@dataclass
class SourceBlock:
    sid: str; source_id: str; page: int; block_index: int; block_type: str; text: str
    author: str = ""; timestamp: str = ""; source_label: str = ""; url: str = ""; note_layer: str = "SOURCE_CONTENT"

@dataclass
class Claim:
    claim_id: str; source_id: str; evidence_sid: str; text: str; page: int; block_type: str
    attribution: str; direction: str; conditional: bool; uncertain: bool; importance: str
    stories: list[str] = field(default_factory=list); tickers: list[str] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list); macro_terms: list[str] = field(default_factory=list)
    drivers: list[str] = field(default_factory=list); relations: list[str] = field(default_factory=list)
    periods: list[str] = field(default_factory=list); numbers: list[str] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list); novelty_state: str = "UNKNOWN"
    change_state: str = "UNKNOWN"; event_id: str = ""; why_selected: list[str] = field(default_factory=list)

@dataclass
class EventCluster:
    event_id: str; title: str; claim_ids: list[str]; stories: list[str]; tickers: list[str]; anchors: list[str]
    directions: dict[str, int]; consensus_state: str; disagreement_notes: list[str]; source_count: int

# =============================================================================
# def 02 HELPERS
# =============================================================================
def def_sha8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()

def def_normalize_text(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "").replace("\u00a0"," ").replace("\u200b","")
    s = re.sub(r"[ \t]+"," ",s); s = re.sub(r"\r\n?","\n",s); s = re.sub(r"\n{3,}","\n\n",s)
    return s.strip()

def def_file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

@lru_cache(maxsize=TOKEN_CACHE_SIZE)
def def_tokenize(text: str) -> frozenset[str]:
    toks = re.findall(r"[A-Za-z][A-Za-z0-9_.+-]*|[\u4e00-\u9fff]{1,4}|\d+(?:\.\d+)?", text.lower())
    stop={"的","了","與","和","及","在","為","是","有","將","之","to","and","the","of","a","an"}
    return frozenset(t for t in toks if len(t)>1 and t not in stop)

def def_jaccard(a: str,b: str) -> float:
    sa,sb=def_tokenize(a),def_tokenize(b)
    return 0.0 if not sa or not sb else len(sa&sb)/max(1,len(sa|sb))

def def_similarity(a: str,b: str) -> float:
    j=def_jaccard(a,b)
    try:
        from rapidfuzz.fuzz import token_set_ratio
        r=token_set_ratio(a,b)/100.0
        return max(j,0.65*r+0.35*j)
    except Exception:
        return j

def def_json_write(obj: Any,path: Path) -> None:
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding="utf-8")

# =============================================================================
# def 03 EXISTING VIA DISCOVERY
# =============================================================================
def def_discover_existing_via_engines() -> dict[str,str|None]:
    found={"layout":None,"text_repair":None,"markdown":None,"nlp":None,"summarizer_v0100":None}
    patterns={
        "layout":("*Layout*.py","*LAYOUT*.py"), "text_repair":("*Text*Repair*.py","*Repair*Engine*.py"),
        "markdown":("*Markdown*.py","*MARKDOWN*.py"), "nlp":("*NLP*.py","*NaturalLanguage*.py"),
        "summarizer_v0100":("VIA_NonStock_Intelligence_Engine_v0100.py",),
    }
    for root in VIA_SEARCH_ROOTS:
        if root is None or not root.exists(): continue
        for key,pats in patterns.items():
            if found[key]: continue
            cand=[]
            for pat in pats:
                try: cand.extend(root.rglob(pat))
                except Exception: pass
            if cand: found[key]=str(sorted(cand,key=lambda p:str(p))[-1])
    return found

# =============================================================================
# def 04 INPUT / LAYOUT
# =============================================================================
def def_guess_block_type(text: str) -> str:
    s=text.strip()
    if not s: return "EMPTY"
    if URL_RE.fullmatch(s): return "URL"
    if len(s)<=80 and any(k in s.lower() for k in ("結論","大綱","展望","摘要","重點","市場焦點","產業看法","現況分析","拜訪內容","產品發展","產能規劃","焦點族群")): return "HEADING"
    if s.startswith(("●","•","➢","▪","🔹","🔘","🟢","🔴","-","–")): return "BULLET"
    if len(NUMBER_RE.findall(s))>=4 and any(k in s.lower() for k in ("yoy","qoq","eps","營收","毛利率","殖利率","收盤")): return "TABLE_OR_METRIC"
    return "PARAGRAPH"

def def_extract_pdf(path: Path) -> tuple[list[SourceBlock],dict[str,Any]]:
    blocks=[]
    try:
        import fitz
        doc=fitz.open(path)
        for pno,page in enumerate(doc,start=1):
            for bi,raw in enumerate(page.get_text("blocks")):
                text=def_normalize_text(raw[4] if len(raw)>4 else "")
                if text:
                    blocks.append(SourceBlock(f"P{pno:03d}-B{bi:03d}-{def_sha8(text)}",path.name,pno,bi,def_guess_block_type(text),text))
        pages=len(doc); doc.close(); return blocks,{"backend":"pymupdf","pages":pages}
    except Exception as e1:
        from pypdf import PdfReader
        reader=PdfReader(str(path))
        for pno,page in enumerate(reader.pages,start=1):
            text=def_normalize_text(page.extract_text() or "")
            if text: blocks.append(SourceBlock(f"P{pno:03d}-B000-{def_sha8(text)}",path.name,pno,0,"PAGE_TEXT",text))
        return blocks,{"backend":"pypdf","pages":len(reader.pages),"fallback_reason":type(e1).__name__}

def def_decode_bytes(raw: bytes) -> tuple[str,str]:
    for enc in ("utf-8-sig","utf-8","cp950","big5","cp1252"):
        try: return raw.decode(enc),enc
        except Exception: pass
    return raw.decode("utf-8",errors="replace"),"utf-8-replace"

class _HTMLTextExtractor(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in {"script","style"}: self.skip+=1
        if tag in {"p","div","br","li","h1","h2","h3","tr"}: self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in {"script","style"} and self.skip: self.skip-=1
        if tag in {"p","div","li","h1","h2","h3","tr"}: self.parts.append("\n")
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def def_html_to_text(raw_html: str) -> str:
    p=_HTMLTextExtractor(); p.feed(raw_html); return def_normalize_text("".join(p.parts))

def def_extract_text_like(path: Path) -> tuple[list[SourceBlock],dict[str,Any]]:
    text,enc=def_decode_bytes(path.read_bytes())
    if path.suffix.lower() in {".html",".htm"}: text=def_html_to_text(text)
    blocks=[]
    for i,para in enumerate([def_normalize_text(x) for x in re.split(r"\n\s*\n",text) if def_normalize_text(x)]):
        blocks.append(SourceBlock(f"P001-B{i:04d}-{def_sha8(para)}",path.name,1,i,def_guess_block_type(para),para))
    return blocks,{"backend":"text","pages":1,"encoding":enc}

def def_extract_docx(path: Path) -> tuple[list[SourceBlock],dict[str,Any]]:
    from docx import Document
    doc=Document(str(path)); blocks=[]; i=0
    for p in doc.paragraphs:
        text=def_normalize_text(p.text)
        if text: blocks.append(SourceBlock(f"P001-B{i:04d}-{def_sha8(text)}",path.name,1,i,def_guess_block_type(text),text)); i+=1
    for table in doc.tables:
        for row in table.rows:
            text=" | ".join(def_normalize_text(c.text) for c in row.cells)
            if text.strip(" |"):
                blocks.append(SourceBlock(f"P001-B{i:04d}-{def_sha8(text)}",path.name,1,i,"TABLE_OR_METRIC",text)); i+=1
    return blocks,{"backend":"python-docx","pages":None}

def def_extract_enex(path: Path) -> tuple[list[SourceBlock],dict[str,Any]]:
    root=ET.parse(path).getroot(); blocks=[]; i=0; notes=root.findall(".//note")
    for note_idx,note in enumerate(notes,start=1):
        title=def_normalize_text(note.findtext("title") or f"Evernote Note {note_idx}")
        text=def_html_to_text(note.findtext("content") or "")
        created=def_normalize_text(note.findtext("created") or ""); src_url=""
        a=note.find("note-attributes")
        if a is not None: src_url=def_normalize_text(a.findtext("source-url") or "")
        for para in [def_normalize_text(x) for x in (title+"\n"+text).split("\n") if def_normalize_text(x)]:
            blocks.append(SourceBlock(f"N{note_idx:03d}-B{i:04d}-{def_sha8(para)}",path.name,note_idx,i,def_guess_block_type(para),para,timestamp=created,url=src_url)); i+=1
    return blocks,{"backend":"evernote-enex","pages":len(notes)}

def def_extract_input(path: Path) -> tuple[list[SourceBlock], dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"INPUT_NOT_FOUND: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"INPUT_BYTES_LIMIT: {path.stat().st_size} > {MAX_INPUT_BYTES}")
    ext = path.suffix.lower()
    if ext == ".pdf":
        blocks, meta = def_extract_pdf(path)
    elif ext in {".txt", ".md", ".log", ".html", ".htm"}:
        blocks, meta = def_extract_text_like(path)
    elif ext == ".docx":
        blocks, meta = def_extract_docx(path)
    elif ext == ".enex":
        blocks, meta = def_extract_enex(path)
    elif ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("evidence_index"), list):
            records = data["evidence_index"]
        elif isinstance(data, dict) and isinstance(data.get("blocks"), list):
            records = data["blocks"]
        elif isinstance(data, dict) and isinstance(data.get("text"), str):
            records = [data]
        elif isinstance(data, list):
            records = data
        else:
            raise ValueError("JSON_SCHEMA_UNSUPPORTED: expected text, blocks, evidence_index or a block list")
        blocks = []
        seen = set()
        for i, record in enumerate(records):
            if not isinstance(record, dict) or not isinstance(record.get("text"), str):
                raise ValueError(f"JSON_BLOCK_INVALID: index={i}")
            text = def_normalize_text(record["text"])
            if not text:
                continue
            page = record.get("page", 1)
            if type(page) is not int or page < 1:
                raise ValueError(f"JSON_PAGE_INVALID: index={i}")
            sid = record.get("sid") or f"P{page:03d}-B{i:05d}-{def_sha8(text)}"
            if not isinstance(sid, str) or sid in seen:
                raise ValueError(f"JSON_DUPLICATE_OR_INVALID_SID: {sid}")
            seen.add(sid)
            block = SourceBlock(sid, path.name, page, i, str(record.get("block_type") or def_guess_block_type(text)), text)
            for key in ("author", "timestamp", "source_label", "url", "note_layer"):
                if key in record:
                    if not isinstance(record[key], str):
                        raise ValueError(f"JSON_FIELD_INVALID: {key}")
                    setattr(block, key, record[key])
            blocks.append(block)
        meta = {"backend": "structured-json", "pages": len({b.page for b in blocks}), "records": len(blocks)}
    else:
        raise ValueError(f"Unsupported input type: {ext}")
    if sum(len(b.text) for b in blocks) > MAX_INPUT_CHARS:
        raise ValueError("INPUT_CHARACTER_LIMIT: no silent truncation")
    return blocks, meta

# =============================================================================
# def 05 ROUTER / MESSAGE / EVERNOTE
# =============================================================================
def def_profile_router(path: Path, blocks: list[SourceBlock]) -> tuple[str, str]:
    name = path.name.casefold()
    text = "\n".join(b.text for b in blocks[:100]).casefold()
    if path.suffix.lower() == ".enex" or any(t in name or t in text[:5000] for t in PROFILE_TERMS[PROFILE_EVERNOTE]):
        return PROFILE_EVERNOTE, "EVERNOTE_NOTE"
    is_message_name = re.search(r"(?<![a-z])(?:messenger|line)(?![a-z])|test[ _-]message", name)
    score = sum(term in text for term in PROFILE_TERMS[PROFILE_MESSENGER])
    if score >= 2 or is_message_name:
        return PROFILE_MESSENGER, "DAILY_MESSAGE_STREAM"
    if any(term in name or term in text[:12000] for term in PROFILE_TERMS[PROFILE_INDUSTRY]):
        return PROFILE_INDUSTRY, "INDUSTRY_REPORT"
    for subtype, terms in OTHER_SUBTYPE_TERMS.items():
        if any(def_alias_hit(name + "\n" + text[:10000], term) for term in terms):
            return PROFILE_OTHER, subtype
    return PROFILE_OTHER, "GENERAL_NON_STOCK"

def def_parse_messenger_blocks(path: Path,blocks: list[SourceBlock]) -> list[SourceBlock]:
    raw="\n".join(b.text for b in blocks); lines=raw.splitlines(); out=[]; buf=[]
    author=time=date=source=url=""; idx=0
    def flush():
        nonlocal idx,buf,url
        text=def_normalize_text("\n".join(buf))
        if text:
            idx+=1; out.append(SourceBlock(f"M{idx:05d}-{def_sha8(text)}",path.name,1,idx,"MESSAGE",text,author=author,timestamp=" ".join(x for x in (date,time) if x),source_label=source,url=url))
        buf=[]; url=""
    for line in lines:
        s=line.strip()
        if not s: continue
        hm=MESSAGE_HEADER_RE.match(s); dm=DATE_LINE_RE.match(s)
        if hm:
            flush(); time=hm.group(1); author=hm.group(2); source=""
            for marker in ("元大投顧","兆豐","台新","中信","國泰","富邦","凱基","群益"):
                if marker in author: source=marker; break
            continue
        if dm: date=s; continue
        um=URL_RE.search(s)
        if um: url=um.group(0)
        buf.append(s)
    flush(); return out or blocks

def def_detect_note_layer(text: str) -> str:
    low=text.lower()
    if any(c in low for c in USER_NOTE_CUES): return "USER_NOTE"
    if text.startswith((">","引用","轉貼")): return "QUOTED_CONTENT"
    if "http://" in low or "https://" in low: return "WEB_CLIP_OR_LINK"
    return "SOURCE_CONTENT"

def def_apply_note_layers(blocks: list[SourceBlock]) -> list[SourceBlock]:
    for b in blocks: b.note_layer=def_detect_note_layer(b.text)
    return blocks

# =============================================================================
# def 06 CLAIM EXTRACTION
# =============================================================================
def def_split_sentences(text: str) -> list[str]:
    parts=re.split(r"(?<=[。！？!?；;])\s*|\n+|(?=●)|(?=🔹)|(?=➢)",def_normalize_text(text))
    return [p.strip(" •➢－-–▪🔹🔘🟢🔴\t") for p in parts if len(p.strip())>=MIN_SENTENCE_CHARS]

def def_detect_stories(text: str) -> list[str]:
    macro_safe = text.replace("毛利率", " ").replace("營業利益率", " ").replace("營益率", " ").replace("淨利率", " ")
    return [name for name, aliases in STORY_TAXONOMY.items()
            if any(def_alias_hit(macro_safe if name == "RATES_BONDS" else text, alias) for alias in aliases)]

def def_detect_anchors(text: str) -> list[str]:
    return [name for name, aliases in GLOBAL_ANCHORS.items() if any(def_alias_hit(text, alias) for alias in aliases)]

def def_detect_tickers(text: str) -> list[str]:
    # Four digits alone are NOT sufficient: revenue/price/index values often have four digits.
    out=set(TW_TICKER_PAREN_RE.findall(text))
    out.update(TW_TICKER_HEADER_RE.findall(text))
    out.update(TW_TICKER_TT_RE.findall(text))
    out.update(TW_TICKER_LABEL_RE.findall(text))
    out.update(x.upper() for x in US_TICKER_US_RE.findall(text))
    out.update(x.upper() for x in US_TICKER_LABEL_RE.findall(text))
    return sorted(out)

def def_detect_macro(text: str) -> list[str]:
    clean = text.replace("毛利率", " ").replace("營業利益率", " ").replace("營益率", " ").replace("淨利率", " ")
    return [term for term in MACRO_TERMS if def_alias_hit(clean, term)]

def def_detect_drivers(text: str) -> list[str]:
    low=text.lower(); return [k for k,v in DRIVER_TERMS.items() if any(x.lower() in low for x in v)]

def def_detect_relations(text: str) -> list[str]:
    low=text.lower(); return [k for k,v in RELATION_CUES.items() if any(x.lower() in low for x in v)]

def def_attribution(text: str,note_layer: str) -> str:
    low=text.lower()
    if note_layer=="USER_NOTE" or any(x.lower() in low for x in USER_NOTE_CUES): return "USER_NOTE"
    if any(x.lower() in low for x in RUMOR_CUES): return "MARKET_RUMOR"
    if any(x.lower() in low for x in MANAGEMENT_CUES): return "MANAGEMENT_GUIDANCE"
    if any(x.lower() in low for x in OPINION_CUES): return "ANALYST_VIEW"
    if any(x.lower() in low for x in FACT_CUES) or NUMBER_RE.search(text): return "SOURCE_FACT_OR_REPORTED_DATA"
    return "SOURCE_STATEMENT"

def def_direction(text: str) -> str:
    low=text.lower(); p=sum(x.lower() in low for x in POSITIVE_CUES); n=sum(x.lower() in low for x in NEGATIVE_CUES)
    return "POSITIVE" if p>n else "NEGATIVE" if n>p else "NEUTRAL_OR_MIXED"

def def_metrics(text: str) -> list[dict[str,Any]]:
    rows=[]
    for metric,pat in METRIC_PATTERNS.items():
        for m in pat.finditer(text): rows.append({"metric":metric,"raw":m.group(0),"groups":list(m.groups())})
    return rows

def def_importance(text: str,stories: list[str],tickers: list[str],metrics: list[dict[str,Any]],attr: str) -> str:
    score=min(3,len(metrics))*2+min(2,len(stories))+min(2,len(tickers))
    if any(x.lower() in text.lower() for x in ("上修","下修","優於預期","低於預期","新高","量產","放量","風險","目標","指引")): score+=2
    if attr in {"MANAGEMENT_GUIDANCE","SOURCE_FACT_OR_REPORTED_DATA"}: score+=1
    return "MUST_KEEP" if score>=6 else "IMPORTANT" if score>=3 else "SUPPORTING"

def def_extract_claims(blocks: list[SourceBlock]) -> list[Claim]:
    claims = []
    for block in blocks:
        if block.block_type in {"DISCLAIMER", "SOURCE", "URL"}:
            continue
        block_tickers = def_detect_tickers(block.text + " " + block.author)
        inherited = block_tickers if len(block_tickers) == 1 else []
        for index, sentence in enumerate(def_split_sentences(block.text)):
            sentence = URL_RE.sub("", sentence).strip()
            explicit = def_detect_tickers(sentence)
            tickers = explicit or inherited
            stories = def_detect_stories(sentence)
            anchors = def_detect_anchors(sentence)
            macro = def_detect_macro(sentence)
            metrics = def_metrics(sentence)
            attribution = def_attribution(sentence, block.note_layer)
            informative = bool(stories or tickers or anchors or macro or metrics or
                               any(def_alias_hit(sentence, cue) for cue in OPINION_CUES + MANAGEMENT_CUES + RISK_CUES + CATALYST_CUES))
            if not informative:
                continue
            if len(claims) >= MAX_CLAIMS_PER_SOURCE:
                raise ValueError(f"CLAIM_LIMIT: more than {MAX_CLAIMS_PER_SOURCE}; no silent truncation")
            claims.append(Claim(
                f"C-{block.sid}-{index:03d}-{def_sha8(sentence)}", block.source_id, block.sid,
                sentence, block.page, block.block_type, attribution, def_direction(sentence),
                bool(re.search(r"(若|如果|倘若|assuming|\bif\s)", sentence, re.I)),
                any(def_alias_hit(sentence, cue) for cue in UNCERTAINTY_CUES),
                def_importance(sentence, stories, tickers, metrics, attribution),
                stories, tickers, anchors, macro, def_detect_drivers(sentence), def_detect_relations(sentence),
                [match.group(0) for match in PERIOD_RE.finditer(sentence)], NUMBER_RE.findall(sentence), metrics))
    return claims

# =============================================================================
# def 07 EVIDENCE GUARDS
# =============================================================================
def def_normalize_number_token(token: str) -> str:
    return re.sub(r"[\s,]","",token).lower()

def def_numeric_guard(summary_text: str,evidence_text: str) -> dict[str,Any]:
    sn=[def_normalize_number_token(x) for x in NUMBER_RE.findall(summary_text)]; en={def_normalize_number_token(x) for x in NUMBER_RE.findall(evidence_text)}
    bad=[x for x in sn if x not in en]; return {"unsupported_numbers":bad,"pass":not bad}

def def_entity_guard(summary_text: str,evidence_text: str) -> dict[str,Any]:
    st=set(def_detect_tickers(summary_text)+def_detect_anchors(summary_text)); ev=set(def_detect_tickers(evidence_text)+def_detect_anchors(evidence_text)); bad=sorted(st-ev)
    return {"unsupported_entities":bad,"pass":not bad}

def def_temporal_guard(summary_text: str,evidence_text: str) -> dict[str,Any]:
    st={m.group(0).lower() for m in PERIOD_RE.finditer(summary_text)}; ev={m.group(0).lower() for m in PERIOD_RE.finditer(evidence_text)}; bad=sorted(st-ev)
    return {"unsupported_periods":bad,"pass":not bad}

# =============================================================================
# def 08 DEDUP / NOVELTY / CHANGE
# =============================================================================
def def_mark_near_duplicates(claims: list[Claim]) -> dict[str,str]:
    dup={}; canonical=[]
    for c in claims:
        best=None; best_s=0.0
        for old in canonical[-300:]:
            if c.stories and old.stories and not(set(c.stories)&set(old.stories)): continue
            s=def_similarity(c.text,old.text)
            if s>best_s: best_s,best=s,old
        if best and best_s>=NEAR_DUP_THRESHOLD: dup[c.claim_id]=best.claim_id
        else: canonical.append(c)
    return dup

def def_load_prior_claims(prior_path: Optional[Path]) -> list[dict[str,Any]]:
    if not prior_path: return []
    return json.loads(prior_path.read_text(encoding="utf-8")).get("claims",[])

def def_mark_novelty_and_change(claims: list[Claim],prior: list[dict[str,Any]]) -> None:
    if not prior:
        for c in claims: c.novelty_state="NEW_WITHIN_INPUT"; c.change_state="UNKNOWN_NO_PRIOR"
        return
    for c in claims:
        cand=[p for p in prior if (not c.stories or set(c.stories)&set(p.get("stories",[]))) and (not c.tickers or set(c.tickers)&set(p.get("tickers",[])))]
        best=None; best_s=0.0
        for p in cand[:1000]:
            s=def_similarity(c.text,p.get("text",""))
            if s>best_s: best_s,best=s,p
        if best is None or best_s<NOVELTY_THRESHOLD: c.novelty_state="NEW"; c.change_state="NEW"
        else:
            c.novelty_state="KNOWN_OR_UPDATED"; old=best.get("direction")
            c.change_state="REVERSE" if old and old!=c.direction and "NEUTRAL" not in old+c.direction else "UPDATED" if c.metrics and best.get("metrics") and c.text!=best.get("text","") else "CONFIRMED_OR_REPEATED"

# =============================================================================
# def 09 EVENT / CONSENSUS
# =============================================================================
def def_cluster_events(claims: list[Claim],duplicate_of: dict[str,str]) -> list[EventCluster]:
    # Stage 1: all claims from the same source block/message are one physical event unit.
    by_evidence=defaultdict(list)
    for c in claims:
        if c.claim_id not in duplicate_of:
            by_evidence[c.evidence_sid].append(c)
    base_clusters=list(by_evidence.values())

    # Stage 2: merge different source blocks/messages only when entity/story overlap and semantic similarity support it.
    merged=[]
    for cluster in base_clusters:
        rep=max(cluster,key=lambda c:def_claim_score(c,PROFILE_OTHER)) if cluster else None
        target=None; best_s=0.0
        if rep is not None:
            for old_cluster in merged[-300:]:
                old=max(old_cluster,key=lambda c:def_claim_score(c,PROFILE_OTHER))
                overlap=bool(set(rep.stories)&set(old.stories) or set(rep.tickers)&set(old.tickers) or set(rep.anchors)&set(old.anchors))
                if not overlap: continue
                s=def_similarity(rep.text,old.text)
                if s>best_s: best_s,target=s,old_cluster
        if target is not None and best_s>=EVENT_SIMILARITY_THRESHOLD:
            target.extend(cluster)
        else:
            merged.append(list(cluster))

    out=[]
    for i,cluster in enumerate(merged,start=1):
        dirs=Counter(c.direction for c in cluster)
        non=[d for d in dirs if d!='NEUTRAL_OR_MIXED' and dirs[d]>0]
        state='DIVERGENT' if len(non)>1 else 'CONSENSUS_OR_NO_CONFLICT'
        notes=[f'{d}:{dirs[d]}' for d in sorted(non)] if len(non)>1 else []
        stories=sorted({s for c in cluster for s in c.stories})
        tickers=sorted({t for c in cluster for t in c.tickers})
        anchors=sorted({a for c in cluster for a in c.anchors})
        rep=max(cluster,key=lambda c:def_claim_score(c,PROFILE_OTHER))
        title=' / '.join((stories+tickers+anchors)[:4]) or rep.text[:80]
        eid=f'EVT-{i:05d}-{def_sha8(title)}'
        event=EventCluster(eid,title,[c.claim_id for c in cluster],stories,tickers,anchors,dict(dirs),state,notes,len({c.evidence_sid for c in cluster}))
        out.append(event)
        for c in cluster: c.event_id=eid
    return out

# =============================================================================
# def 10 CONTRADICTION
# =============================================================================
def def_metric_value(metric: dict[str, Any]) -> Optional[float]:
    for group in reversed(metric.get("groups", [])):
        try:
            value = float(str(group).replace(",", ""))
        except (TypeError, ValueError):
            continue
        raw = metric.get("raw", "")
        if metric.get("metric") in {"REVENUE_YOY", "REVENUE_QOQ"} and re.search(r"年減|季減", raw):
            value = -abs(value)
        return value
    return None

def def_detect_contradictions(claims: list[Claim]) -> list[dict[str, Any]]:
    """Conservative candidates: differing numbers alone never establish a contradiction."""
    buckets = defaultdict(list)
    reviews = []
    for claim in claims:
        entity = ("TICKER", claim.tickers[0]) if len(claim.tickers) == 1 else ("ANCHOR", claim.anchors[0]) if not claim.tickers and len(claim.anchors) == 1 else None
        grouped = defaultdict(list)
        for metric in claim.metrics:
            grouped[metric["metric"]].append(metric)
        for name, metrics in grouped.items():
            values = [def_metric_value(metric) for metric in metrics]
            if len(metrics) > 1 and len({value for value in values if value is not None}) > 1:
                reviews.append({"status": "METRIC_CONTEXT_REVIEW", "metric": name, "claim_id": claim.claim_id,
                                "reason": "Multiple values inside one claim may describe different months, segments or scenarios; not a confirmed contradiction.",
                                "values": [{"value": value, "raw": metric["raw"]} for metric, value in zip(metrics, values)]})
                continue
            if entity is None or len(set(claim.periods)) != 1 or len(metrics) != 1 or values[0] is None:
                continue
            metric = metrics[0]
            unit = str(metric.get("groups", [None])[-1]) if name == "CAPEX" else "%" if name in {"GM", "REVENUE_YOY", "REVENUE_QOQ"} else "UNSPECIFIED_CURRENCY"
            key = (name, entity, claim.periods[0], claim.attribution, unit)
            buckets[key].append((claim, values[0], metric))
    for key, items in buckets.items():
        if len({claim.claim_id for claim, _, _ in items}) < 2:
            continue
        values = [value for _, value, _ in items]
        if (max(values) - min(values)) / max(abs(min(values)), abs(max(values)), 1e-9) > CONTRADICTION_NUM_TOL:
            reviews.append({"key": list(key), "status": "POTENTIAL_CONFLICT_REVIEW",
                            "reason": "Entity and period match; scope/currency/scenario still require source verification.",
                            "values": [{"claim_id": claim.claim_id, "value": value, "raw": metric["raw"]} for claim, value, metric in items]})
    return reviews

# =============================================================================
# def 11 SUMMARY / EXPLAINABILITY
# =============================================================================
def def_claim_score(c: Claim,profile: str) -> float:
    score={"MUST_KEEP":10.0,"IMPORTANT":5.0,"SUPPORTING":1.0}[c.importance]+min(len(c.metrics),3)*1.2+min(len(c.stories),2)*0.9+min(len(c.tickers),2)*0.8+min(len(c.anchors),2)*0.6+min(len(c.relations),2)*0.5
    if c.novelty_state in {"NEW","NEW_WITHIN_INPUT"}: score+=1.2
    if c.change_state in {"UPDATED","REVERSE"}: score+=1.5
    if c.attribution=="MANAGEMENT_GUIDANCE": score+=1.0
    if c.attribution=="MARKET_RUMOR": score-=1.0
    if c.attribution=="USER_NOTE": score-=1.5
    if c.conditional or c.uncertain: score-=0.2
    return score

def def_select_claims(claims: list[Claim],n: int,profile: str,require: Optional[Callable[[Claim],bool]]=None) -> list[Claim]:
    pool=[c for c in claims if require(c)] if require else list(claims)
    ranked=sorted(pool,key=lambda c:(-def_claim_score(c,profile),c.page,c.claim_id))
    selected=[]; used_events=set(); story_counts=Counter(); story_cap=1 if n<=FLASH_BULLETS else 2
    for c in ranked:
        # A compact summary should not repeat multiple sentences from the same Call Memo/event.
        if c.event_id and c.event_id in used_events: continue
        # Keep Story diversity. A Story can appear twice, but should not monopolize the Flash/Investment view.
        if c.stories and any(story_counts[s]>=story_cap for s in c.stories): continue
        if any(def_similarity(c.text,o.text)>=0.80 for o in selected): continue
        reasons=[]
        if c.importance=='MUST_KEEP': reasons.append('MUST_KEEP')
        if c.metrics: reasons.append('NUMERIC_EVIDENCE')
        if c.novelty_state in {'NEW','NEW_WITHIN_INPUT'}: reasons.append('NOVELTY')
        if c.change_state in {'UPDATED','REVERSE'}: reasons.append(c.change_state)
        if c.stories: reasons.append('STORY_RELEVANCE')
        if c.tickers or c.anchors: reasons.append('ENTITY_RELEVANCE')
        if c.attribution=='MANAGEMENT_GUIDANCE': reasons.append('MANAGEMENT_GUIDANCE')
        c.why_selected=reasons or ['IMPORTANCE_RANK']; selected.append(c)
        if c.event_id: used_events.add(c.event_id)
        for s in c.stories: story_counts[s]+=1
        if len(selected)>=n: break
    return selected

def def_profile_sections(profile: str,claims: list[Claim]) -> dict[str,list[Claim]]:
    if profile==PROFILE_INDUSTRY:
        specs=[("核心投資結論",lambda c:c.importance in {"MUST_KEEP","IMPORTANT"}),("需求/供給/價格",lambda c:bool(set(c.drivers)&{"DEMAND","SUPPLY","PRICE","INVENTORY"})),("技術/產品/產能",lambda c:bool(set(c.drivers)&{"TECHNOLOGY","PRODUCT_MIX","CAPEX"})),("供應鏈/公司影響",lambda c:bool(c.tickers or c.anchors or c.relations)),("催化劑",lambda c:any(x.lower() in c.text.lower() for x in CATALYST_CUES)),("風險與待觀察",lambda c:any(x.lower() in c.text.lower() for x in RISK_CUES))]
    elif profile==PROFILE_MESSENGER:
        specs=[("今日核心事件",lambda c:c.importance in {"MUST_KEEP","IMPORTANT"}),("Story/產業",lambda c:bool(c.stories)),("公司/個股",lambda c:bool(c.tickers or c.anchors)),("總經/市場",lambda c:bool(c.macro_terms)),("新增/變更資訊",lambda c:c.novelty_state in {"NEW","NEW_WITHIN_INPUT"} or c.change_state in {"UPDATED","REVERSE"}),("風險/分歧",lambda c:c.direction=="NEGATIVE" or c.uncertain or c.conditional)]
    elif profile==PROFILE_EVERNOTE:
        specs=[("核心論點",lambda c:c.importance in {"MUST_KEEP","IMPORTANT"}),("重要事實/數字",lambda c:bool(c.metrics)),("Story/公司/產品",lambda c:bool(c.stories or c.tickers or c.anchors)),("使用者註記",lambda c:c.attribution=="USER_NOTE"),("催化/風險",lambda c:any(x.lower() in c.text.lower() for x in CATALYST_CUES+RISK_CUES))]
    else:
        specs=[("核心重點",lambda c:c.importance in {"MUST_KEEP","IMPORTANT"}),("市場/總經",lambda c:bool(c.macro_terms)),("Story/產業",lambda c:bool(c.stories)),("公司",lambda c:bool(c.tickers or c.anchors)),("展望/風險",lambda c:c.direction!="NEUTRAL_OR_MIXED" or c.uncertain)]
    return {name:def_select_claims(claims,SECTION_BULLETS,profile,fn) for name,fn in specs}

# =============================================================================
# def 12 LOSS AUDIT / MATRICES
# =============================================================================
def def_evidence_map(blocks: list[SourceBlock]) -> dict[str,SourceBlock]: return {b.sid:b for b in blocks}

def def_guard_claim(c: Claim,evidence: dict[str,SourceBlock]) -> dict[str,Any]:
    ev=evidence.get(c.evidence_sid); text=ev.text if ev else ""; ng=def_numeric_guard(c.text,text); eg=def_entity_guard(c.text,text); tg=def_temporal_guard(c.text,text)
    return {"claim_id":c.claim_id,"evidence_sid":c.evidence_sid,"numeric_guard":ng,"entity_guard":eg,"temporal_guard":tg,"pass":bool(ev) and ng["pass"] and eg["pass"] and tg["pass"]}

def def_summary_loss_audit(claims: list[Claim],selected: list[Claim]) -> dict[str,Any]:
    # Audit by event/evidence unit, not raw sentence count. Long Call Memos can contain dozens of claims.
    unit=lambda c: c.event_id or c.evidence_sid
    selected_units={unit(c) for c in selected}
    must_units={unit(c) for c in claims if c.importance=='MUST_KEEP'}
    important_units={unit(c) for c in claims if c.importance in {'MUST_KEEP','IMPORTANT'}}
    ratio=lambda xs:1.0 if not xs else len(xs & selected_units)/len(xs)
    mr,ir=ratio(must_units),ratio(important_units)
    gate='PASS' if mr>=SUMMARY_MUST_KEEP_TARGET and ir>=SUMMARY_IMPORTANT_TARGET else 'REVIEW'
    return {'must_keep_recall':round(mr,4),'important_recall':round(ir,4),'must_keep_units':len(must_units),'important_units':len(important_units),'selected_units':len(selected_units),'gate':gate}

def def_story_matrix(claims: list[Claim]) -> list[dict[str,Any]]:
    bucket=defaultdict(list)
    for c in claims:
        for s in c.stories: bucket[s].append(c)
    rows=[]
    for s,cs in bucket.items():
        d=Counter(c.direction for c in cs); dr=Counter(x for c in cs for x in c.drivers)
        rows.append({"story":s,"claim_count":len(cs),"positive":d.get("POSITIVE",0),"negative":d.get("NEGATIVE",0),"mixed":d.get("NEUTRAL_OR_MIXED",0),"must_keep":sum(c.importance=="MUST_KEEP" for c in cs),"tickers":sorted({t for c in cs for t in c.tickers}),"global_anchors":sorted({a for c in cs for a in c.anchors}),"drivers":dict(dr),"evidence_sids":sorted({c.evidence_sid for c in cs})})
    return sorted(rows,key=lambda r:(-r["must_keep"],-r["claim_count"],r["story"]))

def def_to_canonical_markdown(blocks: list[SourceBlock]) -> str:
    out=[]
    for b in blocks:
        meta=" | ".join(x for x in (b.timestamp,b.author,b.sid) if x); out.append(f"<!-- {meta} -->")
        prefix="## " if b.block_type=="HEADING" else "- " if b.block_type in {"BULLET","MESSAGE"} else ""; out.append(prefix+b.text); out.append("")
    return "\n".join(out).strip()

# =============================================================================
# def 13 ANALYZE
# =============================================================================
def def_claim_dict(c: Claim) -> dict[str,Any]: return asdict(c)
def def_event_dict(e: EventCluster) -> dict[str,Any]: return asdict(e)

def def_analyze(path: Path, outdir: Optional[Path] = None, prior_path: Optional[Path] = None) -> dict[str, Any]:
    """Compatible v0200 API; structured evidence quality is not a truth guarantee."""
    path = Path(path)
    initial_sha = def_file_sha256(path)
    blocks, extraction = def_extract_input(path)
    profile, subtype = def_profile_router(path, blocks)
    if profile == PROFILE_MESSENGER:
        blocks = def_parse_messenger_blocks(path, blocks)
    if profile == PROFILE_EVERNOTE:
        blocks = def_apply_note_layers(blocks)
    result = def_analyze_blocks(path, blocks, extraction, profile, subtype, prior_path)
    if def_file_sha256(path) != initial_sha:
        raise RuntimeError("SOURCE_CHANGED_DURING_ANALYSIS")
    if outdir is not None:
        result["outputs"] = def_write_outputs(result, Path(outdir))
    return result

# =============================================================================
# def 14 OUTPUTS
# =============================================================================
def def_render_markdown(result: dict[str,Any]) -> str:
    m,q=result["meta"],result["quality"]; lines=[f"# {m['filename']}","",f"- Profile: `{m['profile']}` / `{m['subtype']}`",f"- Engine: `{m['engine_name']} {m['version']}`",f"- Gate: `{q['gate']}`",f"- Claims: {q['claim_count']} · Events: {q['event_count']} · Stories: {q['story_count']}","","## Flash"]
    lines += [f"- {c['text']} `[{c['evidence_sid']}]`" for c in result["summary_views"]["flash"]]; lines += ["","## Investment Summary"]
    lines += [f"- {c['text']} `[{c['evidence_sid']}]` _{','.join(c.get('why_selected',[]))}_" for c in result["summary_views"]["investment"]]
    lines += ["","## Consensus / Disagreement"] + [f"- **{e['title']}** · {e['consensus_state']} · {e['directions']}" for e in result["events"][:20]]
    lines += ["","## Summary Loss Audit","```json",json.dumps(result["summary_loss_audit"],ensure_ascii=False,indent=2),"```"]; return "\n".join(lines)

def def_render_html(result: dict[str,Any]) -> str:
    m,q=result["meta"],result["quality"]
    def cards(rows): return "".join("<li><div>"+html.escape(c["text"])+"</div><small>"+html.escape(c["evidence_sid"])+" · "+html.escape(c["attribution"])+" · "+html.escape(c["importance"])+"</small></li>" for c in rows)
    story="".join(f"<tr><td>{html.escape(r['story'])}</td><td>{r['claim_count']}</td><td>{r['positive']}</td><td>{r['negative']}</td><td>{html.escape(', '.join(r['tickers']) or '—')}</td></tr>" for r in result["story_matrix"][:30])
    return f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>{html.escape(m['filename'])}</title><style>body{{margin:0;background:#f4f5f7;color:#222;font:12px/1.5 "Segoe UI","Noto Sans TC",sans-serif}}main{{max-width:1180px;margin:auto;padding:15px}}header,section{{background:white;border:1px solid #ddd;border-radius:8px;padding:11px}}header{{margin-bottom:8px}}h1{{font-size:18px;margin:0 0 5px}}h2{{font-size:13px;margin:0 0 6px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:8px}}ul{{margin:0;padding-left:18px}}li{{margin:5px 0}}small{{display:block;color:#777;font:9px Consolas,monospace}}.badge{{display:inline-block;border:1px solid #bbb;border-radius:99px;padding:2px 7px;margin-right:4px}}table{{width:100%;border-collapse:collapse;background:white;margin-top:8px}}th,td{{padding:6px;border-bottom:1px solid #e5e5e5;text-align:left}}</style><main><header><h1>{html.escape(m['filename'])}</h1><span class="badge">{html.escape(m['profile'])}</span><span class="badge">{html.escape(m['subtype'])}</span><span class="badge">{html.escape(q['gate'])}</span><div>Claims {q['claim_count']} · Events {q['event_count']} · Stories {q['story_count']} · Guard {q['investment_guard_pass_pct']}%</div></header><div class="grid"><section><h2>Flash</h2><ul>{cards(result['summary_views']['flash'])}</ul></section><section><h2>Investment Summary</h2><ul>{cards(result['summary_views']['investment'])}</ul></section><section><h2>Summary Loss Audit</h2><pre>{html.escape(json.dumps(result['summary_loss_audit'],ensure_ascii=False,indent=2))}</pre></section><section><h2>Contradictions</h2><pre>{html.escape(json.dumps(result['contradictions'][:10],ensure_ascii=False,indent=2))}</pre></section></div><table><thead><tr><th>Story</th><th>Claims</th><th>+</th><th>-</th><th>Tickers</th></tr></thead><tbody>{story}</tbody></table></main></html>'''

def def_write_outputs(result: dict[str,Any],outdir: Path) -> dict[str,str]:
    outdir.mkdir(parents=True,exist_ok=True); stem=Path(result["meta"]["filename"]).stem
    paths={"json":outdir/f"{stem}.nonstock.json","md":outdir/f"{stem}.summary.md","html":outdir/f"{stem}.summary.html","claims_csv":outdir/f"{stem}.claims.csv","events_csv":outdir/f"{stem}.events.csv","story_csv":outdir/f"{stem}.story_matrix.csv"}
    def_json_write(result,paths["json"]); paths["md"].write_text(def_render_markdown(result),encoding="utf-8"); paths["html"].write_text(def_render_html(result),encoding="utf-8")
    cf=["claim_id","source_id","evidence_sid","page","attribution","direction","conditional","uncertain","importance","novelty_state","change_state","event_id","stories","tickers","anchors","macro_terms","drivers","relations","periods","numbers","text"]
    with paths["claims_csv"].open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=cf); w.writeheader()
        for c in result["claims"]:
            row={k:c.get(k) for k in cf}
            for k in ("stories","tickers","anchors","macro_terms","drivers","relations","periods","numbers"): row[k]=";".join(row[k] or [])
            w.writerow(row)
    ef=["event_id","title","stories","tickers","anchors","directions","consensus_state","disagreement_notes","source_count","claim_ids"]
    with paths["events_csv"].open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=ef); w.writeheader()
        for e in result["events"]:
            row=dict(e)
            for k in ("stories","tickers","anchors","disagreement_notes","claim_ids"): row[k]=";".join(str(x) for x in row[k])
            row["directions"]=json.dumps(row["directions"],ensure_ascii=False); w.writerow(row)
    sf=["story","claim_count","positive","negative","mixed","must_keep","tickers","global_anchors","drivers","evidence_sids"]
    with paths["story_csv"].open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=sf); w.writeheader()
        for r in result["story_matrix"]:
            row=dict(r); row["tickers"]=";".join(row["tickers"]); row["global_anchors"]=";".join(row["global_anchors"]); row["evidence_sids"]=";".join(row["evidence_sids"]); row["drivers"]=json.dumps(row["drivers"],ensure_ascii=False); w.writerow(row)
    return {k:str(v) for k,v in paths.items()}

# =============================================================================
# def 15 HEALTH / DOCTOR / SELFTEST
# =============================================================================
def def_health() -> dict[str, Any]:
    """Probe without importing every heavy NLP library or scanning user folders."""
    import importlib.util
    names = ("fitz", "pypdf", "docx", "rapidfuzz", "spacy", "sklearn", "sentence_transformers", "duckdb", "polars", "pyarrow")
    return {"engine_id": ENGINE_ID, "version": ENGINE_VERSION, "network_allowed": False,
            "optional_libraries": {name: importlib.util.find_spec(name) is not None for name in names},
            "existing_via_engines": {key: None for key in ("layout", "text_repair", "markdown", "nlp", "summarizer_v0100")},
            "discovery_status": "NOT_SCANNED; explicit discovery API remains available"}

def def_core_doctor() -> dict[str,Any]:
    h=def_health(); h.update({"profiles":[PROFILE_INDUSTRY,PROFILE_MESSENGER,PROFILE_EVERNOTE,PROFILE_OTHER],"guards":["NUMERIC","ENTITY","TEMPORAL","FACT_OPINION","DUPLICATE","NOVELTY","CONSENSUS","CONTRADICTION","SUMMARY_LOSS"],"notes":["No network calls.","SentenceTransformer is optional and never auto-downloaded.","RapidFuzz is optional; Jaccard fallback is built-in."]}); return h

def def_selftest() -> int:
    checks=[]; s="管理層表示2027年AI Server營收占比將達30-40%，並受惠CSP CAPEX擴張。"
    checks += [("story","AI_INFRASTRUCTURE" in def_detect_stories(s)),("ticker_context",def_detect_tickers("運量(RPK)年增16%，ASP提升") == []),("period","2027" in [m.group(0) for m in PERIOD_RE.finditer(s)]),("number_guard",def_numeric_guard("2027年占比30-40%",s)["pass"]),("entity_guard",def_entity_guard("NVIDIA需求強","NVIDIA需求強")["pass"]),("attribution",def_attribution(s,"SOURCE_CONTENT")=="MANAGEMENT_GUIDANCE"),("driver","CAPEX" in def_detect_drivers(s)),("network",NETWORK_ALLOWED is False)]
    fake=[Claim("c1","x","e1","AI Server需求成長",1,"x","SOURCE_FACT_OR_REPORTED_DATA","POSITIVE",False,False,"IMPORTANT",stories=["AI_INFRASTRUCTURE"]),Claim("c2","x","e2","AI Server需求下滑",1,"x","SOURCE_FACT_OR_REPORTED_DATA","NEGATIVE",False,False,"IMPORTANT",stories=["AI_INFRASTRUCTURE"])]
    checks.append(("consensus_divergence",any(e.consensus_state=="DIVERGENT" for e in def_cluster_events(fake,{}))))
    passed=sum(bool(v) for _,v in checks); print(json.dumps({"passed":passed,"total":len(checks),"checks":checks},ensure_ascii=False,indent=2)); return 0 if passed==len(checks) else 1

# =============================================================================
# def 16 CLI
# =============================================================================
def def_legacy_main(argv: Optional[list[str]]=None) -> int:
    p=argparse.ArgumentParser(description=ENGINE_NAME); p.add_argument("input",nargs="?"); p.add_argument("--outdir",default="output"); p.add_argument("--prior-intelligence",default=""); p.add_argument("--health",action="store_true"); p.add_argument("--doctor",action="store_true"); p.add_argument("--selftest",action="store_true"); args=p.parse_args(argv)
    if args.health: print(json.dumps(def_health(),ensure_ascii=False,indent=2)); return 0
    if args.doctor: print(json.dumps(def_doctor(),ensure_ascii=False,indent=2)); return 0
    if args.selftest: return def_selftest()
    if not args.input: p.error("input is required unless --health/--doctor/--selftest")
    r=def_analyze(Path(args.input),Path(args.outdir),Path(args.prior_intelligence) if args.prior_intelligence else None); print(json.dumps({"file":r["meta"]["filename"],"profile":r["meta"]["profile"],"subtype":r["meta"]["subtype"],"quality":r["quality"],"outputs":r.get("outputs",{})},ensure_ascii=False,indent=2)); return 0 if r["quality"]["gate"]=="PASS" else 2



def def_alias_hit(text: str, alias: str) -> bool:
    """Latin aliases require word boundaries; Chinese aliases use substring matching."""
    low = text.casefold()
    alias = alias.casefold()
    if re.fullmatch(r"[a-z0-9 ._+/-]+", alias):
        return re.search(r"(?<![a-z0-9_])" + re.escape(alias) + r"(?![a-z0-9_])", low) is not None
    return alias in low

def def_analyze_blocks(path: Path, blocks: list[SourceBlock], extraction: dict[str, Any], profile: str, subtype: str, prior_path: Optional[Path] = None) -> dict[str, Any]:
    raw_chars=sum(len(b.text) for b in blocks)
    if raw_chars>MAX_INPUT_CHARS: raise ValueError(f"Input exceeds MAX_INPUT_CHARS={MAX_INPUT_CHARS}; no silent truncation.")
    claims=def_extract_claims(blocks); def_mark_novelty_and_change(claims,def_load_prior_claims(prior_path)); dup=def_mark_near_duplicates(claims); events=def_cluster_events(claims,dup); contradictions=def_detect_contradictions(claims)
    flash=def_select_claims(claims,FLASH_BULLETS,profile); invest=def_select_claims(claims,INVESTMENT_BULLETS,profile)
    # Evidence view keeps one representative per event plus all MUST_KEEP claims.
    by_event=defaultdict(list)
    for c in claims: by_event[c.event_id or c.evidence_sid].append(c)
    evidence=[max(cs,key=lambda c:def_claim_score(c,profile)) for cs in by_event.values() if cs]
    evidence=sorted(evidence,key=lambda c:(-def_claim_score(c,profile),c.page,c.claim_id))
    existing={c.claim_id for c in evidence}; evidence.extend(c for c in claims if c.importance=="MUST_KEEP" and c.claim_id not in existing)
    sections=def_profile_sections(profile,claims); evmap=def_evidence_map(blocks); guards=[def_guard_claim(c,evmap) for c in invest]; loss=def_summary_loss_audit(claims,evidence)
    q={"claim_count":len(claims),"event_count":len(events),"story_count":len({s for c in claims for s in c.stories}),"ticker_count":len({t for c in claims for t in c.tickers}),"must_keep_count":sum(c.importance=="MUST_KEEP" for c in claims),"duplicate_count":len(dup),"contradiction_count":len(contradictions),"investment_guard_pass_pct":round((sum(g["pass"] for g in guards)/len(guards)*100) if guards else 0.0,2),"summary_loss_gate":loss["gate"]}
    q["gate"]="PASS" if claims and guards and q["investment_guard_pass_pct"]==100.0 and loss["gate"]=="PASS" and not contradictions else "REVIEW"
    result={"meta":{"engine_id":ENGINE_ID,"engine_name":ENGINE_NAME,"version":ENGINE_VERSION,"filename":path.name,"sha256":def_file_sha256(path),"profile":profile,"subtype":subtype,"extraction":extraction,"network_allowed":NETWORK_ALLOWED,"raw_chars":raw_chars,"existing_via_engines":{key:None for key in ("layout","text_repair","markdown","nlp","summarizer_v0100")},"discovery_status":"NOT_SCANNED"},"summary_views":{"flash":[def_claim_dict(c) for c in flash],"investment":[def_claim_dict(c) for c in invest],"evidence_matrix":[def_claim_dict(c) for c in evidence],"sections":{k:[def_claim_dict(c) for c in v] for k,v in sections.items()}},"events":[def_event_dict(e) for e in events],"story_matrix":def_story_matrix(claims),"claims":[def_claim_dict(c) for c in claims],"duplicate_of":dup,"contradictions":contradictions,"summary_guards":guards,"summary_loss_audit":loss,"canonical_markdown":def_to_canonical_markdown(blocks),"evidence_index":[asdict(b) for b in blocks],"quality":q}
    return result


# =============================================================================
# def 17 UNIFIED RUNTIME / VERIFIED BATCH PUBLICATION
# =============================================================================
def def_atomic_json(path: Path, value: Any) -> None:
    """Publish one JSON file by same-filesystem replacement; never claim multi-file atomicity."""
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def def_embedded_module(key: str, bindings: Optional[dict[str, Any]] = None):
    """Only load bundled, SHA-checked source; never load a path supplied by input documents."""
    import types
    source = EMBEDDED_SOURCES[key]
    actual = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if actual != EMBEDDED_SHA256[key]:
        raise RuntimeError(f"EMBEDDED_HASH_MISMATCH: {key}")
    name = "_nonstock_" + key + "_" + actual[:16]
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__file__ = str(Path(__file__).resolve()) + "::" + key + ".py"
    module.__dict__.update(bindings or {})
    sys.modules[name] = module
    try:
        exec(compile(source, module.__file__, "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def def_integrated_module():
    import types
    # Functions retain this file's own globals. A proxy also supports runpy callers.
    core = types.SimpleNamespace(**globals())
    repair = def_embedded_module("repair")
    return def_embedded_module("integrated", {
        "CORE": core, "VRN_LAYOUT": def_embedded_module("layout"),
        "VRN_REPAIR": repair, "REPAIR": repair.TextRepairEngine(),
        "VRN_NLP": def_embedded_module("nlp"), "NLP_LIBS": {"gensim": None},
        "REUSE_STATUS": {key: {"embedded": True, "sha256": value} for key, value in EMBEDDED_SHA256.items()}})


def def_analyze_one(path: Path, prior_path: Optional[Path] = None) -> dict[str, Any]:
    return def_integrated_module().def_analyze_one(Path(path), prior_path)


def def_collect_inputs(inputs: list[str], recursive: bool = False, excluded: Optional[Path] = None) -> list[Path]:
    paths = []
    seen = set()
    for raw in inputs:
        root = Path(raw).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"INPUT_NOT_FOUND: {root}")
        if root.is_file() and root.suffix.lower() not in INPUT_SUFFIXES:
            raise ValueError(f"UNSUPPORTED_INPUT: {root}")
        items = root.rglob("*") if root.is_dir() and recursive else root.iterdir() if root.is_dir() else [root]
        for path in sorted(items):
            resolved = path.resolve()
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in INPUT_SUFFIXES:
                continue
            if excluded is not None and (resolved == excluded or excluded in resolved.parents):
                continue
            if resolved not in seen:
                seen.add(resolved)
                paths.append(resolved)
    if not paths:
        raise ValueError("NO_SUPPORTED_INPUT_FILES")
    return paths


def def_output_schema(module) -> dict[str, list[str]]:
    return {"REPORT_SUMMARY": list(dict.fromkeys(module.REPORT_COLUMNS + ["EVIDENCE_SIDS", "LEGACY_REPORT_ID"])),
            "TOPIC_DETAIL": module.TOPIC_COLUMNS,
            "COMPANY_DETAIL": list(dict.fromkeys(module.COMPANY_COLUMNS + ["VALIDATION_ISSUES"])),
            "EVIDENCE_DETAIL": module.EVIDENCE_COLUMNS}


def def_write_table(directory: Path, name: str, columns: list[str], rows: list[dict[str, Any]], parquet: bool) -> dict[str, Any]:
    csv_path = directory / (name + ".csv")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    with csv_path.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != columns or len(list(reader)) != len(rows):
            raise RuntimeError("CSV_ROUNDTRIP_FAILED: " + name)
    receipt = {"rows": len(rows), "csv": csv_path.name, "parquet_status": "DISABLED_BY_USER"}
    if parquet:
        import pyarrow as pa
        import pyarrow.parquet as pq
        integers = {"COMPANY_COUNT", "TOPIC_COUNT", "EVIDENCE_COUNT", "PAGE"}
        schema = pa.schema([(column, pa.int64() if column in integers else pa.string()) for column in columns])
        normalized = [{column: (int(row[column]) if column in integers and row.get(column) is not None
                                else None if column in integers else str(row.get(column, ""))) for column in columns} for row in rows]
        table = pa.Table.from_pylist(normalized, schema=schema)
        target = directory / (name + ".parquet")
        pq.write_table(table, target)
        reread = pq.read_table(target)
        if not reread.equals(table):
            raise RuntimeError("PARQUET_ROUNDTRIP_FAILED: " + name)
        receipt.update(parquet_status="VERIFIED", parquet=target.name)
    return receipt


def def_run(inputs: list[str], outdir: Path, recursive: bool = False, use_cache: bool = True,
            parquet: bool = True, prior_path: Optional[Path] = None) -> dict[str, Any]:
    import importlib.util
    import importlib.metadata
    import platform
    import time
    import uuid
    from datetime import datetime, timezone
    outdir = Path(outdir).resolve()
    paths = def_collect_inputs(inputs, recursive, outdir)
    if parquet and importlib.util.find_spec("pyarrow") is None:
        raise RuntimeError("PARQUET_DEPENDENCY_MISSING: install pyarrow in the selected environment or explicitly use --csv-only")
    outdir.mkdir(parents=True, exist_ok=True)
    lock = outdir / ".nonstock-writer.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat()}, stream)
    try:
        module = def_integrated_module()
        code_sha = def_file_sha256(Path(__file__))
        prior_sha = def_file_sha256(Path(prior_path)) if prior_path else ""
        dependency_versions = {}
        for package in ("PyMuPDF", "pypdf", "python-docx", "rapidfuzz", "summa"):
            try:
                dependency_versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                dependency_versions[package] = "ABSENT"
        config = {"version": ENGINE_VERSION, "python": platform.python_version(), "dependencies": dependency_versions,
                  "core_parameters": {key: value for key, value in globals().items()
                                      if key.isupper() and isinstance(value, (str, int, float, bool, list, tuple, dict))
                                      and key not in {"EMBEDDED_SOURCES", "EMBEDDED_SHA256", "SOURCE_PROVENANCE"}},
                  "prior_sha": prior_sha, "code_sha": code_sha}
        config_sha = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:12]
        directory = outdir / "batches" / batch_id
        directory.mkdir(parents=True)
        tables = {name: [] for name in def_output_schema(module)}
        runs = []
        detail_dir = directory / "details"
        detail_dir.mkdir()
        for path in paths:
            started = time.perf_counter()
            source_sha = def_file_sha256(path)
            key = hashlib.sha256((str(path) + "\0" + source_sha + "\0" + config_sha).encode()).hexdigest()
            cache_path = outdir / "cache" / (key + ".json")
            hit = False
            try:
                result = None
                if use_cache and cache_path.exists():
                    try:
                        cached = json.loads(cache_path.read_text(encoding="utf-8"))
                        body = json.dumps(cached["result"], sort_keys=True, ensure_ascii=False, allow_nan=False)
                        if cached["key"] == key and hashlib.sha256(body.encode()).hexdigest() == cached["payload_sha256"]:
                            result = cached["result"]
                            hit = True
                    except (KeyError, ValueError, TypeError):
                        pass
                if result is None:
                    result = module.def_analyze_one(path, prior_path)
                if def_file_sha256(path) != source_sha:
                    raise RuntimeError("SOURCE_CHANGED_DURING_ANALYSIS")
                if prior_path and def_file_sha256(Path(prior_path)) != prior_sha:
                    raise RuntimeError("PRIOR_CHANGED_DURING_ANALYSIS")
                if not hit and use_cache:
                    # JSON object keys are strings: canonicalize before hashing, including PDF page keys.
                    canonical = json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))
                    body = json.dumps(canonical, sort_keys=True, ensure_ascii=False, allow_nan=False)
                    def_atomic_json(cache_path, {"key": key, "payload_sha256": hashlib.sha256(body.encode()).hexdigest(), "result": result})
                report = result["report"]
                tables["REPORT_SUMMARY"].append(report)
                for name, field in (("TOPIC_DETAIL", "topics"), ("COMPANY_DETAIL", "companies"), ("EVIDENCE_DETAIL", "evidence")):
                    tables[name].extend(result[field])
                filename = report["REPORT_ID"] + ".json"
                def_atomic_json(detail_dir / filename, result)
                runs.append({"file": str(path), "source_sha256": source_sha, "status": report["STATUS"],
                             "report_id": report["REPORT_ID"], "cache_hit": hit, "detail": "details/" + filename,
                             "elapsed_seconds": round(time.perf_counter() - started, 6)})
            except Exception as exc:
                runs.append({"file": str(path), "source_sha256": source_sha, "status": "ERROR",
                             "error": f"{type(exc).__name__}: {exc}", "cache_hit": False})
        receipts = {name: def_write_table(directory, name, columns, tables[name], parquet)
                    for name, columns in def_output_schema(module).items()}
        reports = tables["REPORT_SUMMARY"]
        if len({row["REPORT_ID"] for row in reports}) != len(reports):
            raise RuntimeError("REPORT_ID_COLLISION")
        document = module.def_render_html(reports, tables["TOPIC_DETAIL"], tables["COMPANY_DETAIL"])
        banner = ('<section class="note"><b>批次 ' + html.escape(batch_id) + '</b> · 結果為來源忠實度檢查，非外部事實查核。'
                  + '<br>完整來源、事件、矛盾、逐點證據與錯誤請查看 RESULTS.json 及 details/。</section>')
        document = document.replace("<main>", "<main>" + banner)
        document = document.replace("</main>", '<p>HTML 明細有顯示筆數限制；完整資料請使用 CSV／Parquet。</p></main>')
        (directory / "REPORT_SUMMARY.html").write_text(document, encoding="utf-8")
        status = "PASS" if runs and all(run["status"] == "PASS" for run in runs) else "REVIEW"
        result = {"engine_id": ENGINE_ID, "version": ENGINE_VERSION, "status": status, "batch_id": batch_id,
                  "generated_at": datetime.now(timezone.utc).isoformat(), "network_allowed": False,
                  "code_sha256": code_sha, "config_sha256": config_sha, "runs": runs, "tables": receipts,
                  "report_summary": reports, "topic_detail": tables["TOPIC_DETAIL"], "company_detail": tables["COMPANY_DETAIL"],
                  "evidence_detail": tables["EVIDENCE_DETAIL"], "output_directory": str(directory),
                  "parquet_enabled": parquet, "source_provenance": SOURCE_PROVENANCE}
        def_atomic_json(directory / "RESULTS.json", result)
        artifacts = {str(path.relative_to(directory)): def_file_sha256(path)
                     for path in sorted(directory.rglob("*")) if path.is_file()}
        def_atomic_json(directory / "MANIFEST.json", {"batch_id": batch_id, "sha256": artifacts})
        # All artifacts have been closed and verified before updating this one commit pointer.
        def_atomic_json(outdir / "LATEST.json", {"batch_id": batch_id, "directory": str(directory.relative_to(outdir)),
                                                "status": status, "manifest_sha256": def_file_sha256(directory / "MANIFEST.json")})
        return result
    finally:
        lock.unlink(missing_ok=True)


def def_doctor() -> dict[str, Any]:
    import ast
    diagnostics = def_core_doctor()
    checks = {}
    for key, source in EMBEDDED_SOURCES.items():
        actual = hashlib.sha256(source.encode("utf-8")).hexdigest()
        ast.parse(source, filename=key + ".py")
        checks[key] = {"sha256": actual, "expected_sha256": EMBEDDED_SHA256[key],
                       "hash_match": actual == EMBEDDED_SHA256[key], "ast_parse": True}
    diagnostics.update({"embedded_components": checks, "source_provenance": SOURCE_PROVENANCE,
                        "core_api": "v0200 def_analyze / SourceBlock / Claim retained",
                        "network_enforcement": "No network path is invoked by this engine; not an OS firewall",
                        "acceleration": {"workers": 1, "incremental_cache": True, "token_cache": True,
                                         "external_celeritas": "NOT_VERIFIED"}})
    return diagnostics


def def_main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="NON_STOCK_CORE v0400 — integrated local engine")
    parser.add_argument("inputs", nargs="*")
    parser.add_argument("--outdir", default="nonstock_output_v0400")
    parser.add_argument("--prior-intelligence", default="")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--csv-only", action="store_true", help="Explicitly disable Parquet output")
    parser.add_argument("--legacy-core", action="store_true", help="Use compatible v0200 core result contract for one file")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--export-components", metavar="DIRECTORY")
    args = parser.parse_args(argv)
    try:
        if args.health or args.doctor:
            print(json.dumps(def_doctor() if args.doctor else def_health(), ensure_ascii=False, indent=2))
            return 0
        if args.selftest:
            return def_selftest()
        if args.export_components:
            directory = Path(args.export_components)
            directory.mkdir(parents=True, exist_ok=True)
            for key, source in EMBEDDED_SOURCES.items():
                target = directory / (key + ".py")
                with target.open("x", encoding="utf-8") as stream:
                    stream.write(source)
            print(json.dumps({"exported": list(EMBEDDED_SOURCES), "directory": str(directory)}, ensure_ascii=False))
            return 0
        if not args.inputs:
            parser.error("Provide at least one file or folder")
        prior = Path(args.prior_intelligence) if args.prior_intelligence else None
        if args.legacy_core:
            if len(args.inputs) != 1:
                parser.error("--legacy-core requires exactly one file")
            result = def_analyze(Path(args.inputs[0]), Path(args.outdir), prior)
            print(json.dumps({"quality": result["quality"], "outputs": result.get("outputs", {})}, ensure_ascii=False, indent=2))
            return 0 if result["quality"]["gate"] == "PASS" else 2
        result = def_run(args.inputs, Path(args.outdir), args.recursive, not args.no_cache, not args.csv_only, prior)
        print(json.dumps({key: result[key] for key in ("version", "status", "batch_id", "runs", "tables", "output_directory")}, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(def_main())
