#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ToolHub v0100 — NON-OCR + OCR 工具總站(模組化 · 單一介面 · 可插拔 · 本機免費)。
操作員 2026-10-10:「先將 NON-OCR 工具補齊 AST 注入 分類 模塊化整合 再將 OCR 工具補齊 將已經有的工具抓下來整合補不足模塊化補功能工具
OCR 可擷取 PDF PNG IMAGE」;工具清單 = 操作員兩份 TOP 20(原生 PDF NON-OCR · PNG 表格 OCR)合併去重 + VRN 現用。
  目錄 CATALOG · 探測 probe()(只查套件 / 執行檔在不在,不 import 重套件)
  NON-OCR:nonocr_words(pdf, page, backend) · nonocr_tables(pdf, page, bbox, backend)· nonocr_markdown(pdf, backend)
  OCR:load_images(PDF / PNG / JPG / TIFF / BMP / WEBP → 影像)· ocr_image(img, backend)· ocr_any(path, backends)
  AST:ast_scan(root)= VRN 既有引擎各用了哪些工具 · ast_self()= 本檔函式分類區隔
每個轉接器回同一形狀 {"status": ok/missing/error, ...};工具沒裝 = missing(不崩)。座標一律 PDF points 左上原點(OCR 回影像 px + dpi)。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import importlib.metadata as _md
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0100"
G_TXT, G_TBL, G_LAY = "NON-OCR · 文字 / 字詞", "NON-OCR · 表格", "NON-OCR · 版面 / Markdown"
G_OCR, G_OTB, G_IMG, G_EXT = "OCR · 引擎", "OCR · 表格結構 / 版面模型", "影像前處理", "外部 / GUI / 非 Python(登記 · 不接管線)"


def _t(i, name, group, src, imp="", pip="", binary="", heavy=False, lic="", role="", adapter=False, note=""):
    return {"id": i, "name": name, "group": group, "src": src, "import": imp, "pip": pip, "bin": binary, "heavy": heavy, "license": lic, "role": role, "adapter": adapter, "note": note}


CATALOG = [
    _t("pymupdf", "PyMuPDF (fitz)", G_TXT, "N01 · O13", "fitz", "pymupdf", lic="AGPL / 商業", role="字詞 · find_tables · 渲染 PNG(切塊 / OCR 前處理)", adapter=True),
    _t("pypdfium2", "pypdfium2", G_TXT, "N02", "pypdfium2", "pypdfium2", lic="Apache-2.0 / BSD", role="純文字串流 · 渲染", adapter=True),
    _t("pypdf", "pypdf", G_TXT, "N03", "pypdf", "pypdf", lic="BSD", role="基礎文字 · metadata", adapter=True),
    _t("pdfminer", "pdfminer.six", G_TXT, "N04", "pdfminer", "pdfminer.six", lic="MIT", role="字元座標 · 多欄版面", adapter=True),
    _t("pdfquery", "PDFQuery", G_TXT, "N05", "pdfquery", "pdfquery", lic="MIT", role="座標選擇器(範本式)"),
    _t("slate", "Slate (slate3k)", G_TXT, "N06", "slate3k", "slate3k", lic="GPL", role="pdfminer 簡化封裝", note="久未維護 · 功能被 pdfminer 涵蓋"),
    _t("pikepdf", "pikepdf (QPDF)", G_TXT, "N07", "pikepdf", "pikepdf", lic="MPL-2.0", role="物件樹 · 修復 / 解密(VRN 取頁已用)"),
    _t("poppler", "Poppler pdftotext -layout", G_TXT, "N18", binary="pdftotext", lic="GPL", role="物理網格純文字(外部呼叫)", adapter=True),
    _t("pdfbox", "Apache PDFBox (+ Tesseract CLI)", G_EXT, "N17 · O20", binary="java", lic="Apache-2.0", role="Java 工業級文字 / 字型", note="Java 橋接 · 不接管線"),
    _t("pdfplumber", "pdfplumber", G_TBL, "N08", "pdfplumber", "pdfplumber", lic="MIT", role="字詞 · 表格(lines / text)· VRN 第二步主力", adapter=True),
    _t("camelot", "Camelot", G_TBL, "N09", "camelot", "camelot-py", lic="MIT", role="表格 lattice / stream", adapter=True),
    _t("tabula", "tabula-py", G_TBL, "N10", "tabula", "tabula-py", binary="java", lic="MIT", role="無邊框表格(Java)", adapter=True),
    _t("img2table", "img2table", G_TBL, "N11 · O01", "img2table", "img2table", lic="MIT", role="幾何表格(PDF 原生 / 影像 + OCR)", adapter=True),
    _t("pymupdf4llm", "PyMuPDF4LLM", G_LAY, "N12", "pymupdf4llm", "pymupdf4llm", lic="AGPL / 商業", role="PDF → Markdown(標題位階 · 表格)", adapter=True),
    _t("unstructured", "Unstructured (local)", G_LAY, "N13", "unstructured", "unstructured[pdf]", heavy=True, lic="Apache-2.0", role="語意區塊 Title / NarrativeText / Table"),
    _t("textract", "textract", G_LAY, "N14", "textract", "textract", heavy=True, lic="MIT", role="多格式文字", note="Windows 相依多 · 選配"),
    _t("pdf_extract_kit", "PDF-Extract-Kit 1.0 (ONNX)", G_OTB, "N15 · O06", "pdf_extract_kit", "", heavy=True, lic="AGPL-3.0", role="版面模型(表 / 圖 / 公式)", note="模型權重另下載 · 選配"),
    _t("marker", "Marker", G_OTB, "N16 · O08", "marker", "marker-pdf", heavy=True, lic="GPL-3.0 + 模型另授權", role="多欄 → Markdown", note="權重授權另計 · 選配"),
    _t("plainbytes", "PlainBytes DocumentExtractor", G_EXT, "N19", lic="免費(閉源)", role="Windows 視覺範本擷取"),
    _t("pad", "Power Automate Desktop", G_EXT, "N20 · O17", lic="Windows 內建", role="免代碼 PDF / 影像擷取"),
    _t("markitdown", "MarkItDown", G_LAY, "VRN 現用", "markitdown", "markitdown", lic="MIT", role="多格式 → Markdown(VRN TextOmni 用)", adapter=True),
    _t("docling", "Docling", G_LAY, "VRN 現用", "docling", "docling", heavy=True, lic="MIT", role="版面 + 表格(VRN TableOmni 用)"),
    _t("opencv", "OpenCV (cv2)", G_IMG, "O02", "cv2", "opencv-python-headless", lic="Apache-2.0", role="格線 / 輪廓 / 前處理"),
    _t("skimage", "scikit-image", G_IMG, "O03", "skimage", "scikit-image", lic="BSD", role="傾斜校正 · 線條強化"),
    _t("table_transformer", "Table Transformer (ONNX)", G_OTB, "O04", "", "", heavy=True, lic="MIT", role="表格結構偵測", note="需 ONNX 權重 · 選配"),
    _t("paddleocr", "PaddleOCR (core + PP-Structure)", G_OCR, "O05 · O10", "paddleocr", "paddleocr paddlepaddle", heavy=True, lic="Apache-2.0", role="中文 OCR 最強 · 表格結構", adapter=True, note="首次用會下載模型;建議獨立 OCR 環境"),
    _t("surya", "Surya", G_OTB, "O07", "surya", "surya-ocr", heavy=True, lic="GPL-3.0 + 模型另授權", role="版面 / 表格偵測", note="API 常變 · 先登記"),
    _t("layoutparser", "LayoutParser", G_OTB, "O09", "layoutparser", "layoutparser", heavy=True, lic="Apache-2.0", role="版面區塊框選", note="需 detectron2 · 選配"),
    _t("tesseract", "Tesseract (pytesseract)", G_OCR, "O11", "pytesseract", "pytesseract", binary="tesseract", lic="Apache-2.0", role="單行 / 區塊 OCR(繁中需 chi_tra)", adapter=True),
    _t("easyocr", "EasyOCR", G_OCR, "O12", "easyocr", "easyocr", heavy=True, lic="Apache-2.0", role="80+ 語言(PyTorch)", adapter=True, note="首次用會下載模型"),
    _t("rapidocr", "RapidOCR (ONNX)", G_OCR, "VRN 現用", "rapidocr_onnxruntime", "rapidocr_onnxruntime", lic="Apache-2.0", role="中英 CPU 輕量 OCR(VRN 第三步引擎一)", adapter=True),
    _t("textshot", "TextShot", G_EXT, "O14", lic="MIT", role="截圖 OCR 測試"),
    _t("labelimg_cvat", "LabelImg / CVAT", G_EXT, "O15", lic="MIT", role="手動範本框"),
    _t("snipping", "Windows 剪取工具(文字動作)", G_EXT, "O16", lic="Windows 內建", role="快速複製影像文字"),
    _t("tesseract_net", "Tesseract.NET", G_EXT, "O18", lic="Apache-2.0", role="C# 封裝"),
    _t("sharpcv", "SharpCV", G_EXT, "O19", lic="Apache-2.0", role="C# OpenCV"),
]
_IMPORT_ALIAS = {"fitz": "pymupdf", "pymupdf": "pymupdf", "pypdfium2": "pypdfium2", "pypdf": "pypdf", "PyPDF2": "pypdf", "pdfminer": "pdfminer", "pdfquery": "pdfquery", "slate3k": "slate", "slate": "slate",
                 "pikepdf": "pikepdf", "pdfplumber": "pdfplumber", "camelot": "camelot", "tabula": "tabula", "img2table": "img2table", "pymupdf4llm": "pymupdf4llm", "unstructured": "unstructured",
                 "textract": "textract", "marker": "marker", "markitdown": "markitdown", "docling": "docling", "cv2": "opencv", "skimage": "skimage", "paddleocr": "paddleocr", "paddle": "paddleocr",
                 "surya": "surya", "layoutparser": "layoutparser", "pytesseract": "tesseract", "easyocr": "easyocr", "rapidocr_onnxruntime": "rapidocr", "rapidocr": "rapidocr", "pdf2image": "poppler"}


def _ver(t: dict) -> str:
    for dist in [x for x in (t["pip"].split(" ")[0] if t["pip"] else "", t["import"]) if x]:
        try:
            return _md.version(re.sub(r"\[.*\]$", "", dist))
        except Exception:  # noqa: BLE001
            continue
    return ""


def _tess_cmd() -> str:
    for c in (shutil.which("tesseract"), r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        if c and Path(c).exists():
            return str(c)
    return ""


def probe_tools(catalog: list = None) -> list:
    """只查在不在(find_spec / which / 版本),不 import 重套件 —— 不會像子程序探測那樣卡 90 秒。"""
    out = []
    for t in catalog or CATALOG:
        imp_ok = bool(t["import"]) and importlib.util.find_spec(t["import"]) is not None
        bin_path = (_tess_cmd() if t["bin"] == "tesseract" else shutil.which(t["bin"])) if t["bin"] else ""
        if t["group"] == G_EXT:
            st = "外部"
        elif t["import"] and t["bin"]:
            st = "ok" if (imp_ok and bin_path) else ("缺執行檔" if imp_ok else "missing")
        elif t["import"]:
            st = "ok" if imp_ok else "missing"
        elif t["bin"]:
            st = "ok" if bin_path else "missing"
        else:
            st = "登記"
        extra = ""
        if t["id"] == "tesseract" and bin_path:
            try:
                langs = subprocess.run([bin_path, "--list-langs"], capture_output=True, text=True, timeout=15).stdout.split()
                extra = "語言 " + ",".join(l for l in langs if l in ("eng", "chi_tra", "chi_sim")) + ("" if "chi_tra" in langs else " · 缺繁中 chi_tra")
            except Exception:  # noqa: BLE001
                extra = "語言 ?"
        out.append(dict(t, status=st, version=_ver(t) if imp_ok else "", bin_path=bin_path or "", extra=extra))
    return out


# ───────── NON-OCR 轉接器 ─────────
def _res(status, **kw):
    return dict({"status": status}, **kw)


def nonocr_words(pdf: str, page: int, backend: str = "pymupdf") -> dict:
    t0 = time.time()
    try:
        if backend == "pymupdf":
            import fitz  # noqa: WPS433
            with fitz.open(pdf) as d:
                ws = [{"text": w[4], "bbox": [round(w[0], 2), round(w[1], 2), round(w[2], 2), round(w[3], 2)]} for w in d[page - 1].get_text("words")]
        elif backend == "pdfplumber":
            import pdfplumber  # noqa: WPS433
            with pdfplumber.open(pdf) as d:
                ws = [{"text": w["text"], "bbox": [round(w["x0"], 2), round(w["top"], 2), round(w["x1"], 2), round(w["bottom"], 2)]} for w in d.pages[page - 1].extract_words()]
        elif backend == "pdfminer":
            from pdfminer.high_level import extract_pages  # noqa: WPS433
            from pdfminer.layout import LTTextLine  # noqa: WPS433
            ws = []
            for lt in extract_pages(pdf, page_numbers=[page - 1]):
                H = lt.height

                def walk(o):
                    if isinstance(o, LTTextLine):
                        ws.append({"text": o.get_text().strip(), "bbox": [round(o.x0, 2), round(H - o.y1, 2), round(o.x1, 2), round(H - o.y0, 2)]})
                    elif hasattr(o, "__iter__"):
                        for c in o:
                            walk(c)
                walk(lt)
        elif backend in ("pypdfium2", "pypdf", "poppler"):
            if backend == "pypdfium2":
                import pypdfium2 as pdfium  # noqa: WPS433
                d = pdfium.PdfDocument(pdf)
                txt = d[page - 1].get_textpage().get_text_range()
                d.close()
            elif backend == "pypdf":
                from pypdf import PdfReader  # noqa: WPS433
                txt = PdfReader(pdf).pages[page - 1].extract_text() or ""
            else:
                exe = shutil.which("pdftotext")
                if not exe:
                    return _res("missing", backend=backend, why="pdftotext 不在")
                txt = subprocess.run([exe, "-layout", "-f", str(page), "-l", str(page), pdf, "-"], capture_output=True, text=True, timeout=60).stdout
            ws = [{"text": l, "bbox": None} for l in txt.splitlines() if l.strip()]
        else:
            return _res("missing", backend=backend, why="沒有這個轉接器")
        return _res("ok", backend=backend, words=ws, n=len(ws), ms=int((time.time() - t0) * 1000))
    except ImportError as exc:
        return _res("missing", backend=backend, why=str(exc)[:80])
    except Exception as exc:  # noqa: BLE001
        return _res("error", backend=backend, why="%s: %s" % (type(exc).__name__, str(exc)[:100]), ms=int((time.time() - t0) * 1000))


TABLE_BACKENDS = ["pymupdf_lines", "pymupdf_text", "pdfplumber_lines", "pdfplumber_text", "camelot_lattice", "camelot_stream", "tabula_lattice", "tabula_stream", "img2table"]


def _clean(rows) -> list:
    out = []
    for r in rows or []:
        rr = [("" if c is None else str(c)).replace("\n", " ").strip() for c in r]
        if any(rr):
            out.append(rr)
    w = max((len(r) for r in out), default=0)
    return [r + [""] * (w - len(r)) for r in out]


def _df_rows(df) -> list:
    try:
        return _clean(df.fillna("").astype(str).values.tolist())
    except Exception:  # noqa: BLE001
        return []


def nonocr_tables(pdf: str, page: int, bbox: list = None, backend: str = "pymupdf_lines") -> dict:
    """bbox = [x0, top, x1, bottom](PDF points · 左上原點);回 tables:[{bbox, rows}]。"""
    t0 = time.time()
    tabs = []
    try:
        if backend.startswith("pymupdf"):
            import fitz  # noqa: WPS433
            with fitz.open(pdf) as d:
                pg = d[page - 1]
                kw = {"strategy": "lines" if backend.endswith("lines") else "text"}
                if bbox:
                    kw["clip"] = fitz.Rect(*bbox)
                for t in pg.find_tables(**kw).tables:
                    tabs.append({"bbox": [round(x, 2) for x in t.bbox], "rows": _clean(t.extract())})
        elif backend.startswith("pdfplumber"):
            import pdfplumber  # noqa: WPS433
            s = "lines" if backend.endswith("lines") else "text"
            with pdfplumber.open(pdf) as d:
                pg = d.pages[page - 1]
                if bbox:
                    pg = pg.crop(bbox)
                for t in pg.find_tables(table_settings={"vertical_strategy": s, "horizontal_strategy": s}):
                    tabs.append({"bbox": [round(x, 2) for x in t.bbox], "rows": _clean(t.extract())})
        elif backend.startswith("camelot"):
            import camelot  # noqa: WPS433
            import fitz  # noqa: WPS433
            with fitz.open(pdf) as d:
                H = d[page - 1].rect.height
            kw = {"pages": str(page), "flavor": "lattice" if backend.endswith("lattice") else "stream"}
            if bbox:
                area = "%.2f,%.2f,%.2f,%.2f" % (bbox[0], H - bbox[1], bbox[2], H - bbox[3])
                kw["table_areas" if kw["flavor"] == "stream" else "table_regions"] = [area]
            for t in camelot.read_pdf(pdf, **kw):
                x0, y0, x1, y1 = getattr(t, "_bbox", (0, 0, 0, 0))
                tabs.append({"bbox": [round(x0, 2), round(H - y1, 2), round(x1, 2), round(H - y0, 2)], "rows": _df_rows(t.df)})
        elif backend.startswith("tabula"):
            import tabula  # noqa: WPS433
            if not shutil.which("java"):
                return _res("missing", backend=backend, why="Java 不在(tabula 需要)")
            kw = {"pages": page, "multiple_tables": True, "pandas_options": {"header": None}, "silent": True}
            kw["lattice" if backend.endswith("lattice") else "stream"] = True
            if bbox:
                kw["area"] = [bbox[1], bbox[0], bbox[3], bbox[2]]
            for df in tabula.read_pdf(pdf, **kw) or []:
                tabs.append({"bbox": list(bbox) if bbox else None, "rows": _df_rows(df)})
        elif backend == "img2table":
            from img2table.document import PDF  # noqa: WPS433
            doc = PDF(src=pdf, pages=[page - 1])
            res = doc.extract_tables(ocr=None, implicit_rows=True, borderless_tables=True)
            for t in res.get(page - 1, []):
                b = t.bbox
                bb = [b.x1 * 72 / 200, b.y1 * 72 / 200, b.x2 * 72 / 200, b.y2 * 72 / 200]
                tabs.append({"bbox": [round(x, 2) for x in bb], "rows": _df_rows(t.df)})
        else:
            return _res("missing", backend=backend, why="沒有這個轉接器")
        return _res("ok", backend=backend, tables=[t for t in tabs if t["rows"]], ms=int((time.time() - t0) * 1000))
    except ImportError as exc:
        return _res("missing", backend=backend, why=str(exc)[:80])
    except Exception as exc:  # noqa: BLE001
        return _res("error", backend=backend, why="%s: %s" % (type(exc).__name__, str(exc)[:100]), ms=int((time.time() - t0) * 1000))


def nonocr_markdown(pdf: str, backend: str = "pymupdf4llm", pages: list = None) -> dict:
    t0 = time.time()
    try:
        if backend == "pymupdf4llm":
            import pymupdf4llm  # noqa: WPS433
            md = pymupdf4llm.to_markdown(pdf, pages=[p - 1 for p in pages] if pages else None)
        elif backend == "markitdown":
            from markitdown import MarkItDown  # noqa: WPS433
            md = MarkItDown().convert(pdf).text_content
        else:
            return _res("missing", backend=backend, why="沒有這個轉接器")
        return _res("ok", backend=backend, markdown=md, chars=len(md), ms=int((time.time() - t0) * 1000))
    except ImportError as exc:
        return _res("missing", backend=backend, why=str(exc)[:80])
    except Exception as exc:  # noqa: BLE001
        return _res("error", backend=backend, why="%s: %s" % (type(exc).__name__, str(exc)[:100]))


# ───────── OCR 轉接器(PDF / PNG / IMAGE 一律先成影像)─────────
IMG_EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif")


def load_images(path: str, pages: list = None, dpi: int = 300) -> list:
    """PDF → 每頁渲染(dpi);影像檔 → 原圖(多頁 TIFF 每頁一張)。回 [(標籤, PIL.Image RGB, dpi)]。"""
    from PIL import Image, ImageSequence  # noqa: WPS433
    p = Path(path)
    out = []
    if p.suffix.lower() == ".pdf":
        import fitz  # noqa: WPS433
        with fitz.open(str(p)) as d:
            for i in (pages or range(1, len(d) + 1)):
                if 1 <= i <= len(d):
                    pix = d[i - 1].get_pixmap(dpi=dpi, alpha=False)
                    out.append(("P%02d" % i, Image.frombytes("RGB", (pix.width, pix.height), pix.samples), dpi))
    elif p.suffix.lower() in IMG_EXT:
        im = Image.open(str(p))
        d0 = int((im.info.get("dpi") or (dpi, dpi))[0] or dpi)
        for k, fr in enumerate(ImageSequence.Iterator(im), 1):
            out.append(("F%02d" % k if k > 1 or getattr(im, "n_frames", 1) > 1 else "IMG", fr.convert("RGB"), d0))
    return out


_ENG = {}


def _engine(backend: str):
    if backend in _ENG:
        return _ENG[backend]
    e = None
    if backend == "rapidocr":
        from rapidocr_onnxruntime import RapidOCR  # noqa: WPS433
        e = RapidOCR()
    elif backend == "paddleocr":
        from paddleocr import PaddleOCR  # noqa: WPS433
        try:
            e = PaddleOCR(use_angle_cls=True, lang="chinese_cht", show_log=False)
        except TypeError:
            e = PaddleOCR(lang="chinese_cht")
    elif backend == "easyocr":
        import easyocr  # noqa: WPS433
        e = easyocr.Reader(["ch_tra", "en"], gpu=False)
    elif backend == "tesseract":
        import pytesseract  # noqa: WPS433
        cmd = _tess_cmd()
        if not cmd:
            raise ImportError("tesseract 執行檔不在")
        pytesseract.pytesseract.tesseract_cmd = cmd
        langs = subprocess.run([cmd, "--list-langs"], capture_output=True, text=True, timeout=15).stdout.split()
        e = (pytesseract, "+".join(l for l in ("chi_tra", "eng") if l in langs) or "eng")
    _ENG[backend] = e
    return e


def ocr_image(img, backend: str = "rapidocr") -> dict:
    """img = PIL.Image;回 lines:[{text, bbox:[x0,y0,x1,y1](px), conf}]。"""
    import numpy as np  # noqa: WPS433
    t0 = time.time()
    try:
        e = _engine(backend)
        arr = np.array(img)
        lines = []
        if backend == "rapidocr":
            res, _ = e(arr)
            for box, text, conf in res or []:
                xs, ys = [p[0] for p in box], [p[1] for p in box]
                lines.append({"text": text, "bbox": [min(xs), min(ys), max(xs), max(ys)], "conf": round(float(conf), 3)})
        elif backend == "tesseract":
            pt, lang = e
            d = pt.image_to_data(img, lang=lang, config="--psm 6", output_type=pt.Output.DICT)
            rows = {}
            for i, w in enumerate(d["text"]):
                if str(w).strip() and float(d["conf"][i]) >= 0:
                    k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
                    rows.setdefault(k, []).append(i)
            for k, ids in rows.items():
                x0 = min(d["left"][i] for i in ids)
                y0 = min(d["top"][i] for i in ids)
                x1 = max(d["left"][i] + d["width"][i] for i in ids)
                y1 = max(d["top"][i] + d["height"][i] for i in ids)
                lines.append({"text": " ".join(d["text"][i] for i in ids), "bbox": [x0, y0, x1, y1], "conf": round(sum(float(d["conf"][i]) for i in ids) / len(ids) / 100, 3)})
        elif backend == "paddleocr":
            res = e.ocr(arr) if hasattr(e, "ocr") else e.predict(arr)
            for page in res or []:
                for it in page or []:
                    try:
                        box, (text, conf) = it[0], it[1]
                        xs, ys = [p[0] for p in box], [p[1] for p in box]
                        lines.append({"text": text, "bbox": [min(xs), min(ys), max(xs), max(ys)], "conf": round(float(conf), 3)})
                    except Exception:  # noqa: BLE001
                        continue
        elif backend == "easyocr":
            for box, text, conf in e.readtext(arr):
                xs, ys = [p[0] for p in box], [p[1] for p in box]
                lines.append({"text": text, "bbox": [min(xs), min(ys), max(xs), max(ys)], "conf": round(float(conf), 3)})
        else:
            return _res("missing", backend=backend, why="沒有這個轉接器")
        lines.sort(key=lambda l: (round(l["bbox"][1] / 12), l["bbox"][0]))
        return _res("ok", backend=backend, lines=lines, n=len(lines), conf=round(sum(l["conf"] for l in lines) / len(lines), 3) if lines else 0.0, ms=int((time.time() - t0) * 1000))
    except ImportError as exc:
        return _res("missing", backend=backend, why=str(exc)[:80])
    except Exception as exc:  # noqa: BLE001
        return _res("error", backend=backend, why="%s: %s" % (type(exc).__name__, str(exc)[:100]), ms=int((time.time() - t0) * 1000))


def ocr_any(path: str, backends: list = None, pages: list = None, dpi: int = 300) -> dict:
    """PDF / PNG / JPG / TIFF … → 每頁 / 每張 × 每個引擎;兩個引擎時算文字一致度(候選,不當已驗證)。"""
    import difflib  # noqa: WPS433
    backends = backends or ["rapidocr"]
    out = []
    for label, img, d in load_images(path, pages, dpi):
        rs = {b: ocr_image(img, b) for b in backends}
        ok = [r for r in rs.values() if r["status"] == "ok"]
        agree = None
        if len(ok) >= 2:
            a = re.sub(r"\s+", "", " ".join(l["text"] for l in ok[0]["lines"]))
            b = re.sub(r"\s+", "", " ".join(l["text"] for l in ok[1]["lines"]))
            agree = round(difflib.SequenceMatcher(None, a, b).ratio(), 3)
        out.append({"src": str(path), "unit": label, "size": list(img.size), "dpi": d, "engines": rs, "agree": agree})
    return {"path": str(path), "units": out}


# ───────── AST:既有引擎用了哪些工具 · 本檔分類區隔 ─────────
def ast_scan(root: Path, skip: str = r"(_quarantine|_retired|_archive|__pycache__|[\\/]tests?[\\/]|site-packages|\.venv|envs)") -> dict:
    use, eng = {}, {}
    for p in sorted(Path(root).rglob("*.py")):
        if re.search(skip, str(p)) or p.stat().st_size > 3_000_000:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError):
            continue
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                mods.add(n.module.split(".")[0])
        tools = sorted({_IMPORT_ALIAS[m] for m in mods if m in _IMPORT_ALIAS})
        if tools:
            fam = re.sub(r"_v\d{4}$", "", p.stem)
            rel = str(p.relative_to(root))
            eng.setdefault(fam, {"files": [], "tools": set(), "funcs": 0})
            eng[fam]["files"].append(rel)
            eng[fam]["tools"].update(tools)
            eng[fam]["funcs"] = max(eng[fam]["funcs"], sum(1 for n in tree.body if isinstance(n, ast.FunctionDef)))
            for t in tools:
                use.setdefault(t, set()).add(fam)
    return {"by_tool": {k: sorted(v) for k, v in use.items()}, "by_engine": {k: {"files": v["files"][-1:], "n_files": len(v["files"]), "tools": sorted(v["tools"]), "funcs": v["funcs"]} for k, v in eng.items()}}


_CATS = [("探測", "probe_"), ("NON-OCR 轉接", "nonocr_"), ("OCR 轉接", "ocr_"), ("影像載入", "load_"), ("AST 整合", "ast_"), ("內部", "_")]


def ast_self() -> dict:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    cat = lambda n: next((c for c, pre in _CATS if n.startswith(pre)), "其他")  # noqa: E731
    return {"functions": [{"name": f.name, "cat": cat(f.name), "args": [a.arg for a in f.args.args], "lines": [f.lineno, getattr(f, "end_lineno", f.lineno)]} for f in fns],
            "categories": {c: sum(1 for f in fns if cat(f.name) == c) for c in [c for c, _ in _CATS] + ["其他"]}}


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    ids = [t["id"] for t in CATALOG]
    chk("① 目錄 %d 項(兩份 TOP 20 合併去重 + VRN 現用)· id 不重複 · 每項有分組 / 來源" % len(ids), len(ids) == len(set(ids)) and len(ids) >= 33 and all(t["group"] and t["src"] for t in CATALOG))
    pr = probe_tools()
    chk("② 探測不 import 重套件(find_spec / which)· 每項有狀態", all(r["status"] in ("ok", "missing", "缺執行檔", "外部", "登記") for r in pr))
    td = Path(tempfile.mkdtemp(prefix="toolhub-"))
    try:
        from reportlab.pdfgen import canvas
        pdf = td / "t.pdf"
        c = canvas.Canvas(str(pdf), pagesize=(595, 842))
        Y = lambda y: 842 - y - 9  # noqa: E731
        c.setFont("Helvetica", 10)
        for t, x in (("Item", 60), ("2024", 220), ("2025", 320)):
            c.drawString(x, Y(100), t)
        for y, lab, v in ((120, "Revenue", ("1,234", "1,456")), (140, "EPS", ("2.31", "3.10"))):
            c.drawString(60, Y(y), lab)
            c.drawString(220, Y(y), v[0])
            c.drawString(320, Y(y), v[1])
        for y in (95, 112, 132, 152):
            c.line(55, 842 - y, 400, 842 - y)
        for x in (55, 200, 300, 400):
            c.line(x, 842 - 95, x, 842 - 152)
        c.save()
        w = nonocr_words(str(pdf), 1, "pymupdf")
        chk("③ NON-OCR 字詞(PyMuPDF)· 讀到 Revenue / 1,456", w["status"] == "ok" and {"Revenue", "1,456"} <= {x["text"] for x in w["words"]})
        t = nonocr_tables(str(pdf), 1, [50, 90, 405, 157], "pymupdf_lines")
        chk("④ NON-OCR 表格(PyMuPDF lines · 依 bbox)· 3×3 · Revenue 列 = 1,234 / 1,456", t["status"] == "ok" and t["tables"] and t["tables"][0]["rows"][1] == ["Revenue", "1,234", "1,456"])
        bad = nonocr_tables(str(pdf), 1, None, "no_such")
        chk("⑤ 沒有的轉接器 / 沒裝的工具 → missing(不崩)", bad["status"] == "missing")
        ims = load_images(str(pdf), [1], 150)
        from PIL import Image
        png = td / "x.png"
        ims[0][1].save(str(png))
        im2 = load_images(str(png))
        sz = ims[0][1].size if ims else (0, 0)
        chk("⑥ PDF / PNG 都能載成影像(PDF 150 DPI ≈ 595×842 pt × 150/72 = %d×%d · PNG 原圖同尺寸)" % sz, abs(sz[0] - 1240) <= 1 and abs(sz[1] - 1754) <= 1 and im2 and im2[0][1].size == sz)
        if importlib.util.find_spec("rapidocr_onnxruntime"):
            o = ocr_any(str(png), ["rapidocr"])
            txt = " ".join(l["text"] for l in o["units"][0]["engines"]["rapidocr"]["lines"])
            chk("⑦ OCR(rapidocr)讀 PNG → 讀到 Revenue", "Revenue" in txt)
        else:
            chk("⑦ OCR:rapidocr 沒裝 → missing(不崩)", ocr_image(ims[0][1], "rapidocr")["status"] == "missing")
    finally:
        import shutil as _sh
        _sh.rmtree(td, ignore_errors=True)
    a = ast_self()
    chk("⑧ AST 分類區隔(探測 / NON-OCR / OCR / 影像載入 / AST 整合)", all(a["categories"].get(c, 0) > 0 for c in ("探測", "NON-OCR 轉接", "OCR 轉接", "影像載入", "AST 整合")))
    print("[計] VRN_ToolHub_v%s 自測 %d/%d · %s" % (VERSION, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    if "--probe" in sys.argv:
        for r in probe_tools():
            print("%-18s %-8s %-10s %s" % (r["id"], r["status"], r["version"], r["extra"]))
        raise SystemExit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--ocr":
        print(json.dumps(ocr_any(sys.argv[2], (sys.argv[3].split(",") if len(sys.argv) > 3 else None)), ensure_ascii=False)[:4000])
