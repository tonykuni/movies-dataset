# -*- coding: utf-8 -*-
# =====================================================================================
# VIA_PDFPlumberPlusEngine.py
# Veritas Intelligence Analytics — PDFPlumber-Plus Multi-Engine Extraction Engine
# ASSET: CLS_VIA_PDFPLUMBERPLUS_V1
# -------------------------------------------------------------------------------------
# 設計原則（遵循 VIA / VRN 既有慣例）:
#   1. _PARAMS 為唯一設定真值來源 (SSOT)，程式碼內零魔術數字。
#   2. 確定性優先 (deterministic-first cascade)：PyMuPDF 快篩 -> pdfplumber 結構化
#      -> camelot(lattice) -> tabula -> 最後才喚醒 OCR (PaddleOCR / PP-Structure)。
#   3. 純 CPU 優化：強制 use_gpu=False、MKLDNN、ir_optim、cpu_threads 吃滿核心；
#      OCR 模型「延遲載入」(lazy)，未遇掃描頁完全不佔用記憶體。
#   4. 表格去重採「重疊率 (overlap-ratio)」而非 bbox 分桶；fill factor 平方化以懲罰
#      碎片化策略；lines-detected 表格給 1.25x 權重加成。
#   5. Markdown 是衍生輸出 (RAG/全文檢索用)，不是結構化數值的真值來源；
#      表格真值走 JSON / CSV 結構化通道，並保留 page_no / bbox / engine 溯源。
#   6. 只增不減：JSONL ledger 一律 append-only，never overwrite。
#   7. 進度以 @@PROGRESS|pct|label 打到 stderr，供 PowerShell launcher 進度條解析。
#   8. 編碼：Markdown / JSON / JSONL 一律 UTF-8 no-BOM；CSV 一律 utf-8-sig (Excel 相容)。
#   9. 所有第三方引擎皆為「可選」：缺件不炸，降級並在 capability 報告中誠實標記。
#  10. CLS(CFG).run() 回傳含 "ok" 鍵的 dict（runner 相容介面）。
# =====================================================================================

from __future__ import annotations

# [VIA:ANCHOR:IMPORT_STDLIB] ---------------------------------------------------------
import os
import sys
import gc
import io
import csv
import json
import time
import html
import math
import argparse
import hashlib
import platform
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# [VIA:ANCHOR:PARAMS] ----------------------------------------------------------------
# 單一真值來源。任何行為調整只改這裡，不改函式內部。
_PARAMS: Dict[str, Any] = {
    "ENGINE_NAME": "VIA_PDFPlumberPlusEngine",
    "ENGINE_VERSION": "v1.0.0",
    "ASSET_ID": "CLS_VIA_PDFPLUMBERPLUS_V1",

    # ---- 路徑 (SSOT) ----
    "VIA_ROOT": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics",
    "OUT_SUBDIR": r"outputs\PDFPlumberPlus",
    "LEDGER_NAME": "VIA_PDFPlumberPlus_Ledger.jsonl",

    # ---- 分流門檻 ----
    "TRIAGE_MIN_CHARS": 10,             # 原生文字字元數低於此值 -> 判定掃描頁
    "TRIAGE_MIN_CHAR_DENSITY": 0.0002,  # 每平方點字元密度下限，防「浮水印假文字」
    "RENDER_ZOOM": 2.0,                 # PyMuPDF 渲染倍率 (OCR 前放大)
    "RENDER_MAX_PIXELS": 40_000_000,    # 單頁渲染像素上限，超過自動降 zoom

    # ---- pdfplumber 多策略表格抽取 ----
    "TABLE_STRATEGIES": [
        {"id": "S1_lines",      "vertical_strategy": "lines", "horizontal_strategy": "lines", "lines_based": True},
        {"id": "S2_lines_text", "vertical_strategy": "lines", "horizontal_strategy": "text",  "lines_based": True},
        {"id": "S3_text_lines", "vertical_strategy": "text",  "horizontal_strategy": "lines", "lines_based": True},
        {"id": "S4_text",       "vertical_strategy": "text",  "horizontal_strategy": "text",  "lines_based": False},
    ],
    "TABLE_SNAP_TOLERANCE": 3,
    "TABLE_JOIN_TOLERANCE": 3,
    "TABLE_INTERSECTION_TOLERANCE": 3,
    "TABLE_TEXT_TOLERANCE": 2,
    "TABLE_MIN_ROWS": 2,
    "TABLE_MIN_COLS": 2,
    "TABLE_MIN_CELLS": 4,
    "LINES_BASED_BONUS": 1.25,       # 有線框表格的可信度加成
    "FILL_FACTOR_POWER": 2.0,        # 填充率平方化 -> 懲罰碎片化策略
    "DEDUP_OVERLAP_RATIO": 0.50,     # 重疊率去重門檻 (非 bbox 分桶)

    # ---- 表頭回溯 (向上比對 N 行鎖定欄位名稱) ----
    "HEADER_LOOKBACK_LINES": 3,
    "HEADER_LOOKBACK_PT": 36.0,      # 表格上緣往上取 N points 的文字作為標題候選

    # ---- 儲存格清洗 ----
    "CELL_STRIP_CHARS": " \t\r\n\u3000\xa0",
    "CELL_COLLAPSE_NEWLINE": True,   # 儲存格內換行 -> 單一空白
    "CELL_NULL_TOKENS": ["", "-", "—", "－", "N/A", "n/a", "null", "NULL"],

    # ---- OCR (純 CPU) ----
    "OCR_ENABLE": True,
    "OCR_LANG": "ch",                # ch = 中英混合 (含繁中)
    "OCR_USE_ANGLE_CLS": True,
    "OCR_MIN_CONFIDENCE": 0.50,
    "OCR_USE_STRUCTURE": True,       # 掃描頁優先用 PP-Structure 還原表格
    "OCR_CPU_THREADS": 0,            # 0 = 自動吃滿核心
    "OCR_ENABLE_MKLDNN": True,
    "OCR_IR_OPTIM": True,
    "OCR_FORCE_CPU": True,           # 硬性禁用 GPU (Gate G12)

    # ---- 確定性 fallback 引擎 (可選) ----
    "USE_CAMELOT": False,            # 需 Ghostscript；預設關閉，缺件不炸
    "USE_TABULA": False,             # 需 Java；預設關閉
    "CAMELOT_FLAVOR": "lattice",

    # ---- 輸出 ----
    "EMIT_JSON": True,
    "EMIT_CSV": True,
    "EMIT_MARKDOWN": True,           # 衍生輸出，供 RAG/全文檢索，非真值
    "EMIT_HTML_REPORT": True,
    "CSV_ENCODING": "utf-8-sig",     # Excel 相容
    "TEXT_ENCODING": "utf-8",        # Markdown / JSON / JSONL 一律 no-BOM
    "RUN_ID_BYTES": 6,               # blake2s digest 長度 -> 12 hex chars

    # ---- 進度 ----
    "PROGRESS_ENABLED": True,
    "PROGRESS_PREFIX": "@@PROGRESS",

    # ---- 驗證閘門 ----
    "GATES": ["G00", "G01", "G02", "G03", "G04", "G05",
              "G06", "G07", "G08", "G09", "G10", "G11", "G12"],
    "GATE_FAIL_IS_ERROR": False,     # WARN 不中斷；僅在 ERR 時 ok=False

    # ---- Visual Lock 配色 (HTML 報告) ----
    "VL_BG": "#f5f4f0",
    "VL_PAPER": "#ffffff",
    "VL_INK": "#1e1d1a",
    "VL_LINE": "#dbd9d3",
    "VL_BLUE": "#4c78a8",
    "VL_TEAL": "#439a9a",
    "VL_RED": "#c96b5a",
    "VL_GREEN": "#5a9e6f",
    "VL_SEAL": "牘",
}


# [VIA:ANCHOR:CPU_ENV] ---------------------------------------------------------------
def _apply_cpu_env(threads: int) -> int:
    """FNC_APPLY_CPU_ENV — 在任何深度學習框架 import 之前鎖定 CPU 執行緒數。"""
    n = threads if threads and threads > 0 else (os.cpu_count() or 4)
    n = max(1, int(n))
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                "FLAGS_use_mkldnn", "PADDLE_NUM_THREADS"):
        if key.startswith("FLAGS_"):
            os.environ.setdefault(key, "1")
        else:
            os.environ.setdefault(key, str(n))
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")  # 硬性斷 GPU
    os.environ.setdefault("FLAGS_allocator_strategy", "auto_growth")
    return n


# [VIA:ANCHOR:UTILS] -----------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _progress(pct: float, label: str) -> None:
    """FNC_PROGRESS — @@PROGRESS|pct|label 打到 stderr 供 launcher 解析。"""
    if not _PARAMS["PROGRESS_ENABLED"]:
        return
    pct = max(0.0, min(100.0, float(pct)))
    sys.stderr.write(f'{_PARAMS["PROGRESS_PREFIX"]}|{pct:.1f}|{label}\n')
    sys.stderr.flush()


def _log(msg: str) -> None:
    sys.stderr.write(f"[{_PARAMS['ENGINE_NAME']}] {msg}\n")
    sys.stderr.flush()


def _run_id(pdf_path: Path, params: Dict[str, Any]) -> str:
    """FNC_RUN_ID — blake2s(檔案指紋 + 關鍵參數) -> 穩定可重現的 run id (Gate G11)。"""
    h = hashlib.blake2s(digest_size=params["RUN_ID_BYTES"])
    try:
        st = pdf_path.stat()
        h.update(pdf_path.name.encode("utf-8"))
        h.update(str(st.st_size).encode("utf-8"))
        with pdf_path.open("rb") as fh:
            h.update(fh.read(1024 * 512))
    except Exception:
        h.update(str(pdf_path).encode("utf-8"))
    sig = {k: params[k] for k in (
        "ENGINE_VERSION", "TRIAGE_MIN_CHARS", "DEDUP_OVERLAP_RATIO",
        "FILL_FACTOR_POWER", "LINES_BASED_BONUS", "OCR_LANG", "RENDER_ZOOM")}
    h.update(json.dumps(sig, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()


def _write_text(path: Path, content: str, encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding=encoding, newline="\n") as fh:
        fh.write(content)


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    """FNC_APPEND_LEDGER — append-only，只增不減。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "a", encoding=_PARAMS["TEXT_ENCODING"], newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _clean_cell(value: Any, params: Dict[str, Any]) -> str:
    """FNC_CLEAN_CELL — 邊框多餘空白 / 換行 / 全形空白自動過濾。"""
    if value is None:
        return ""
    s = str(value)
    if params["CELL_COLLAPSE_NEWLINE"]:
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = " ".join(part.strip() for part in s.split("\n") if part.strip())
    s = s.strip(params["CELL_STRIP_CHARS"])
    s = " ".join(s.split())
    return "" if s in params["CELL_NULL_TOKENS"] else s


def _bbox_overlap_ratio(a: Tuple[float, float, float, float],
                        b: Tuple[float, float, float, float]) -> float:
    """FNC_OVERLAP_RATIO — 交集面積 / 較小者面積。取代脆弱的 bbox 分桶去重。"""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = max(1e-9, (ax1 - ax0) * (ay1 - ay0))
    area_b = max(1e-9, (bx1 - bx0) * (by1 - by0))
    return inter / min(area_a, area_b)


def _score_table(matrix: List[List[str]], lines_based: bool, params: Dict[str, Any]) -> float:
    """FNC_SCORE_TABLE — (填充率^p) x 已填儲存格數 x 線框加成 x 欄數一致性。"""
    if not matrix:
        return 0.0
    rows = len(matrix)
    cols = max(len(r) for r in matrix)
    total = max(1, rows * cols)
    filled = sum(1 for r in matrix for c in r if c)
    fill = filled / total
    score = (fill ** params["FILL_FACTOR_POWER"]) * float(filled)
    if lines_based:
        score *= params["LINES_BASED_BONUS"]
    widths = [len(r) for r in matrix]
    consistency = widths.count(max(set(widths), key=widths.count)) / rows
    return score * (0.5 + 0.5 * consistency)


# [VIA:ANCHOR:CAPABILITY] ------------------------------------------------------------
def _probe_capabilities(params: Dict[str, Any]) -> Dict[str, Any]:
    """FNC_PROBE — 誠實回報哪些引擎真的在場，缺件降級不炸。"""
    caps: Dict[str, Any] = {}

    try:
        import pdfplumber  # noqa: F401
        caps["pdfplumber"] = getattr(pdfplumber, "__version__", "unknown")
    except Exception as exc:
        caps["pdfplumber"] = f"MISSING ({exc.__class__.__name__})"

    caps["pymupdf"] = "MISSING"
    try:
        import pymupdf as _fz  # type: ignore
        caps["pymupdf"] = getattr(_fz, "__version__", "unknown")
    except Exception:
        try:
            import fitz as _fz  # type: ignore
            caps["pymupdf"] = str(getattr(_fz, "__doc__", "unknown")).split("\n")[0]
        except Exception:
            pass

    for name in ("paddleocr", "cv2", "numpy", "camelot", "tabula", "pandas", "openpyxl"):
        try:
            mod = __import__(name)
            caps[name] = getattr(mod, "__version__", "present")
        except Exception:
            caps[name] = "MISSING"

    caps["_gpu_forced_off"] = bool(params["OCR_FORCE_CPU"])
    caps["_cpu_count"] = os.cpu_count() or 0
    caps["_python"] = platform.python_version()
    caps["_platform"] = platform.platform()
    return caps


# [VIA:ANCHOR:TRIAGE] ----------------------------------------------------------------
class _Triage:
    """CLS_TRIAGE — 引擎 1：PyMuPDF 快篩（缺件時自動降級為 pdfplumber 快篩）。"""

    def __init__(self, pdf_path: Path, params: Dict[str, Any]) -> None:
        self.params = params
        self.path = pdf_path
        self.doc = None
        self.backend = "none"
        try:
            try:
                import pymupdf as fz  # type: ignore
            except Exception:
                import fitz as fz  # type: ignore
            self.fz = fz
            self.doc = fz.open(str(pdf_path))
            self.backend = "pymupdf"
        except Exception as exc:
            self.fz = None
            _log(f"PyMuPDF 不可用，降級為 pdfplumber 快篩：{exc.__class__.__name__}")

    @property
    def available(self) -> bool:
        return self.doc is not None

    def page_count(self) -> int:
        return len(self.doc) if self.doc is not None else 0

    def native_text(self, idx: int) -> str:
        if self.doc is None:
            return ""
        try:
            return (self.doc[idx].get_text() or "").strip()
        except Exception:
            return ""

    def page_area(self, idx: int) -> float:
        if self.doc is None:
            return 1.0
        try:
            r = self.doc[idx].rect
            return max(1.0, float(r.width) * float(r.height))
        except Exception:
            return 1.0

    def render_rgb(self, idx: int) -> Optional[Any]:
        """記憶體內渲染 -> NumPy RGB，不落地暫存檔（保護隱私 + 免 I/O 等待）。"""
        if self.doc is None:
            return None
        try:
            import numpy as np
        except Exception:
            return None
        zoom = float(self.params["RENDER_ZOOM"])
        page = self.doc[idx]
        rect = page.rect
        est = (rect.width * zoom) * (rect.height * zoom)
        if est > self.params["RENDER_MAX_PIXELS"]:
            zoom = max(1.0, math.sqrt(self.params["RENDER_MAX_PIXELS"] /
                                      max(1.0, rect.width * rect.height)))
        pix = page.get_pixmap(matrix=self.fz.Matrix(zoom, zoom), alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 1:
            img = np.repeat(img, 3, axis=2)
        elif pix.n == 4:
            img = img[:, :, :3]
        return img.copy()

    def close(self) -> None:
        try:
            if self.doc is not None:
                self.doc.close()
        except Exception:
            pass


# [VIA:ANCHOR:DIGITAL] ---------------------------------------------------------------
class _DigitalExtractor:
    """CLS_DIGITAL — 引擎 2：pdfplumber 多策略表格抽取 + 重疊率去重 + 表頭回溯。"""

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def _settings(self, strat: Dict[str, Any]) -> Dict[str, Any]:
        p = self.params
        return {
            "vertical_strategy": strat["vertical_strategy"],
            "horizontal_strategy": strat["horizontal_strategy"],
            "snap_tolerance": p["TABLE_SNAP_TOLERANCE"],
            "join_tolerance": p["TABLE_JOIN_TOLERANCE"],
            "intersection_tolerance": p["TABLE_INTERSECTION_TOLERANCE"],
            "text_tolerance": p["TABLE_TEXT_TOLERANCE"],
        }

    def _header_lookback(self, page: Any, bbox: Tuple[float, float, float, float]) -> List[str]:
        """向上比對 N 行，鎖定表格真正的標題/欄位名稱。"""
        p = self.params
        x0, top, x1, _bottom = bbox
        y_from = max(0.0, top - p["HEADER_LOOKBACK_PT"])
        try:
            crop = page.crop((max(0.0, x0 - 2.0), y_from,
                              min(float(page.width), x1 + 2.0), max(y_from, top)))
            txt = crop.extract_text() or ""
        except Exception:
            return []
        lines = [ln.strip() for ln in txt.split("\n") if ln.strip()]
        return lines[-p["HEADER_LOOKBACK_LINES"]:]

    def extract(self, page: Any, page_no: int) -> Dict[str, Any]:
        p = self.params
        text = ""
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            _log(f"p{page_no} extract_text 失敗：{exc}")

        candidates: List[Dict[str, Any]] = []
        for strat in p["TABLE_STRATEGIES"]:
            try:
                found = page.find_tables(table_settings=self._settings(strat))
            except Exception:
                continue
            for tb in found:
                try:
                    raw = tb.extract()
                except Exception:
                    continue
                matrix = [[_clean_cell(c, p) for c in row] for row in (raw or [])]
                matrix = [r for r in matrix if any(c for c in r)]
                if len(matrix) < p["TABLE_MIN_ROWS"]:
                    continue
                if max((len(r) for r in matrix), default=0) < p["TABLE_MIN_COLS"]:
                    continue
                if sum(1 for r in matrix for c in r if c) < p["TABLE_MIN_CELLS"]:
                    continue
                bbox = tuple(float(v) for v in tb.bbox)
                candidates.append({
                    "strategy": strat["id"],
                    "lines_based": strat["lines_based"],
                    "bbox": bbox,
                    "matrix": matrix,
                    "score": _score_table(matrix, strat["lines_based"], p),
                })

        kept = self._dedup(candidates)
        tables: List[Dict[str, Any]] = []
        for i, cand in enumerate(kept, start=1):
            tables.append({
                "region_id": f"p{page_no:04d}_t{i:02d}",
                "page_no": page_no,
                "bbox": [round(v, 2) for v in cand["bbox"]],
                "engine": "pdfplumber",
                "strategy": cand["strategy"],
                "score": round(cand["score"], 4),
                "n_rows": len(cand["matrix"]),
                "n_cols": max(len(r) for r in cand["matrix"]),
                "header_context": self._header_lookback(page, cand["bbox"]),
                "matrix": cand["matrix"],
            })
        return {"text": text, "tables": tables}

    def _dedup(self, cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重疊率去重（Gate G05）：同一區域只留分數最高者。"""
        thr = self.params["DEDUP_OVERLAP_RATIO"]
        ordered = sorted(cands, key=lambda c: c["score"], reverse=True)
        kept: List[Dict[str, Any]] = []
        for c in ordered:
            if all(_bbox_overlap_ratio(c["bbox"], k["bbox"]) < thr for k in kept):
                kept.append(c)
        kept.sort(key=lambda c: (c["bbox"][1], c["bbox"][0]))
        return kept


# [VIA:ANCHOR:SCANNED] ---------------------------------------------------------------
class _ScannedExtractor:
    """CLS_SCANNED — 引擎 3：PaddleOCR / PP-Structure 純 CPU 輕量視覺流（延遲載入）。"""

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self._ocr = None
        self._structure = None
        self._failed = False
        self.backend = "none"

    def _cpu_kwargs(self) -> Dict[str, Any]:
        p = self.params
        threads = p["OCR_CPU_THREADS"] or (os.cpu_count() or 4)
        return {
            "use_gpu": False,
            "ir_optim": bool(p["OCR_IR_OPTIM"]),
            "enable_mkldnn": bool(p["OCR_ENABLE_MKLDNN"]),
            "cpu_threads": int(threads),
        }

    def _build(self, cls: Any, base: Dict[str, Any]) -> Optional[Any]:
        """不同 paddleocr 版本參數差異大 -> 逐步剝除不支援的 kwargs 再重試。"""
        kwargs = dict(base)
        kwargs.update(self._cpu_kwargs())
        droppable = ["enable_mkldnn", "ir_optim", "cpu_threads", "use_gpu",
                     "show_log", "structure_version", "image_orientation",
                     "use_angle_cls", "layout", "table"]
        for _ in range(len(droppable) + 1):
            try:
                return cls(**kwargs)
            except TypeError as exc:
                removed = False
                for key in droppable:
                    if key in kwargs and key in str(exc):
                        kwargs.pop(key, None)
                        removed = True
                        break
                if not removed:
                    for key in droppable:
                        if key in kwargs:
                            kwargs.pop(key, None)
                            removed = True
                            break
                if not removed:
                    raise
            except Exception:
                raise
        return None

    def _ensure(self) -> bool:
        if self._failed or not self.params["OCR_ENABLE"]:
            return False
        if self._ocr is not None or self._structure is not None:
            return True
        _apply_cpu_env(self.params["OCR_CPU_THREADS"])
        p = self.params
        try:
            if p["OCR_USE_STRUCTURE"]:
                try:
                    from paddleocr import PPStructure  # type: ignore
                    self._structure = self._build(PPStructure, {
                        "show_log": False,
                        "image_orientation": True,
                        "structure_version": "PP-StructureV2",
                        "table": True,
                        "layout": True,
                    })
                    self.backend = "PP-Structure(CPU)"
                except Exception as exc:
                    _log(f"PP-Structure 不可用，改用 PaddleOCR：{exc.__class__.__name__}")
            if self._structure is None:
                from paddleocr import PaddleOCR  # type: ignore
                self._ocr = self._build(PaddleOCR, {
                    "lang": p["OCR_LANG"],
                    "use_angle_cls": bool(p["OCR_USE_ANGLE_CLS"]),
                    "show_log": False,
                })
                self.backend = "PaddleOCR(CPU)"
            return True
        except Exception as exc:
            self._failed = True
            _log(f"OCR 引擎載入失敗，掃描頁將標記為 NO_OCR：{exc.__class__.__name__}: {exc}")
            return False

    def extract(self, img_rgb: Any, page_no: int) -> Dict[str, Any]:
        if img_rgb is None:
            return {"text": "", "tables": [], "engine": "none", "note": "RENDER_UNAVAILABLE"}
        if not self._ensure():
            return {"text": "", "tables": [], "engine": "none", "note": "OCR_UNAVAILABLE"}
        try:
            if self._structure is not None:
                return self._run_structure(img_rgb, page_no)
            return self._run_ocr(img_rgb, page_no)
        except Exception as exc:
            _log(f"p{page_no} OCR 失敗：{exc.__class__.__name__}: {exc}")
            return {"text": "", "tables": [], "engine": self.backend, "note": "OCR_ERROR"}

    def _run_structure(self, img_rgb: Any, page_no: int) -> Dict[str, Any]:
        result = self._structure(img_rgb)
        texts: List[str] = []
        tables: List[Dict[str, Any]] = []
        for region in (result or []):
            rtype = region.get("type", "")
            res = region.get("res", None)
            if rtype == "table":
                html_data = ""
                if isinstance(res, dict):
                    html_data = res.get("html", "") or ""
                tables.append({
                    "region_id": f"p{page_no:04d}_s{len(tables) + 1:02d}",
                    "page_no": page_no,
                    "bbox": [round(float(v), 2) for v in region.get("bbox", [0, 0, 0, 0])],
                    "engine": "PP-Structure",
                    "strategy": "visual_table",
                    "score": None,
                    "header_context": [],
                    "html_data": html_data,
                    "matrix": self._html_to_matrix(html_data),
                })
            elif isinstance(res, list):
                for line in res:
                    if isinstance(line, dict) and line.get("text"):
                        if float(line.get("confidence", 1.0)) >= self.params["OCR_MIN_CONFIDENCE"]:
                            texts.append(str(line["text"]))
        for t in tables:
            t["n_rows"] = len(t["matrix"])
            t["n_cols"] = max((len(r) for r in t["matrix"]), default=0)
        return {"text": "\n".join(texts), "tables": tables,
                "engine": "PP-Structure(CPU)", "note": ""}

    def _run_ocr(self, img_rgb: Any, page_no: int) -> Dict[str, Any]:
        try:
            res = self._ocr.ocr(img_rgb, cls=bool(self.params["OCR_USE_ANGLE_CLS"]))
        except TypeError:
            res = self._ocr.ocr(img_rgb)
        texts: List[str] = []
        block = res[0] if (res and isinstance(res, list) and isinstance(res[0], list)) else res
        for line in (block or []):
            try:
                payload = line[1]
                text_str, conf = payload[0], float(payload[1])
                if conf >= self.params["OCR_MIN_CONFIDENCE"]:
                    texts.append(str(text_str))
            except Exception:
                continue
        return {"text": "\n".join(texts), "tables": [], "engine": "PaddleOCR(CPU)", "note": ""}

    @staticmethod
    def _html_to_matrix(html_str: str) -> List[List[str]]:
        if not html_str:
            return []
        try:
            import pandas as pd
            dfs = pd.read_html(io.StringIO(html_str))
            if not dfs:
                return []
            df = dfs[0].fillna("")
            return [[str(c) for c in row] for row in df.astype(str).values.tolist()]
        except Exception:
            return []


# [VIA:ANCHOR:EMIT] ------------------------------------------------------------------
class _Emitter:
    """CLS_EMIT — JSON / CSV / Markdown / HTML 輸出。Markdown 為衍生物，非真值。"""

    def __init__(self, out_dir: Path, params: Dict[str, Any]) -> None:
        self.out = out_dir
        self.params = params
        self.files: List[str] = []

    def _reg(self, path: Path) -> None:
        self.files.append(str(path))

    def emit_json(self, payload: Dict[str, Any]) -> Path:
        path = self.out / "extraction.json"
        _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2),
                    self.params["TEXT_ENCODING"])
        self._reg(path)
        return path

    def emit_csv(self, pages: List[Dict[str, Any]]) -> int:
        n = 0
        tdir = self.out / "tables"
        for pg in pages:
            for tb in pg["tables"]:
                matrix = tb.get("matrix") or []
                if not matrix:
                    continue
                path = tdir / f"{tb['region_id']}.csv"
                path.parent.mkdir(parents=True, exist_ok=True)
                width = max(len(r) for r in matrix)
                with io.open(path, "w", encoding=self.params["CSV_ENCODING"], newline="") as fh:
                    w = csv.writer(fh)
                    for row in matrix:
                        w.writerow(list(row) + [""] * (width - len(row)))
                self._reg(path)
                n += 1
        return n

    def emit_markdown(self, meta: Dict[str, Any], pages: List[Dict[str, Any]]) -> Path:
        lines: List[str] = [
            f"# {meta['source_name']}",
            "",
            "> 衍生輸出 (derivative)，供全文檢索 / RAG 使用；"
            "結構化數值真值請取 tables/*.csv 與 extraction.json。",
            f"> run_id: `{meta['run_id']}` | 產出時間: {meta['finished_at']}",
            "",
        ]
        for pg in pages:
            lines.append(f"## Page {pg['page_no']}  \n`type={pg['type']}` `engine={pg['engine']}`")
            lines.append("")
            if pg.get("text"):
                lines.append(pg["text"])
                lines.append("")
            for tb in pg["tables"]:
                lines.append(f"### Table {tb['region_id']}  ")
                if tb.get("header_context"):
                    lines.append("> 表頭回溯: " + " / ".join(tb["header_context"]))
                lines.append("")
                lines.extend(self._md_table(tb.get("matrix") or []))
                lines.append("")
        path = self.out / "content.md"
        _write_text(path, "\n".join(lines), self.params["TEXT_ENCODING"])
        self._reg(path)
        return path

    @staticmethod
    def _md_table(matrix: List[List[str]]) -> List[str]:
        if not matrix:
            return ["_(empty table)_"]
        width = max(len(r) for r in matrix)
        norm = [list(r) + [""] * (width - len(r)) for r in matrix]
        head = norm[0]
        out = ["| " + " | ".join(c.replace("|", "\\|") for c in head) + " |",
               "| " + " | ".join(["---"] * width) + " |"]
        for row in norm[1:]:
            out.append("| " + " | ".join(c.replace("|", "\\|") for c in row) + " |")
        return out

    def emit_html(self, meta: Dict[str, Any], pages: List[Dict[str, Any]],
                  gates: List[Dict[str, Any]], caps: Dict[str, Any]) -> Path:
        p = self.params
        esc = html.escape

        def gate_color(status: str) -> str:
            return {"PASS": p["VL_GREEN"], "WARN": p["VL_BLUE"],
                    "ERR": p["VL_RED"]}.get(status, p["VL_INK"])

        n_digital = sum(1 for pg in pages if pg["type"] == "digital")
        n_scanned = len(pages) - n_digital
        n_tables = sum(len(pg["tables"]) for pg in pages)
        n_chars = sum(len(pg.get("text") or "") for pg in pages)

        cards = [
            ("頁數", len(pages), p["VL_INK"]),
            ("原生電子頁", n_digital, p["VL_BLUE"]),
            ("掃描/影像頁", n_scanned, p["VL_TEAL"]),
            ("表格區域", n_tables, p["VL_RED"]),
            ("文字量 (字元)", f"{n_chars:,}", p["VL_INK"]),
            ("耗時 (秒)", meta["elapsed_sec"], p["VL_GREEN"]),
        ]
        card_html = "".join(
            f'<div class="card"><div class="k">{esc(str(k))}</div>'
            f'<div class="v" style="color:{c}">{esc(str(v))}</div></div>'
            for k, v, c in cards)

        gate_rows = "".join(
            f'<tr><td class="mono">{esc(g["id"])}</td><td>{esc(g["name"])}</td>'
            f'<td class="mono" style="color:{gate_color(g["status"])};font-weight:600">{esc(g["status"])}</td>'
            f'<td>{esc(g["detail"])}</td></tr>' for g in gates)

        page_rows = "".join(
            f'<tr><td class="mono">{pg["page_no"]}</td>'
            f'<td class="mono">{esc(pg["type"])}</td>'
            f'<td class="mono">{esc(pg["engine"])}</td>'
            f'<td class="mono">{len(pg.get("text") or ""):,}</td>'
            f'<td class="mono">{len(pg["tables"])}</td>'
            f'<td class="mono">{esc(", ".join(sorted({str(t.get("strategy")) for t in pg["tables"]})) or "-")}</td>'
            f'<td class="mono">{pg["elapsed_ms"]}</td></tr>' for pg in pages)

        cap_rows = "".join(
            f'<tr><td class="mono">{esc(k)}</td>'
            f'<td class="mono" style="color:{p["VL_RED"] if str(v).startswith("MISSING") else p["VL_GREEN"]}">'
            f'{esc(str(v))}</td></tr>' for k, v in caps.items())

        table_cards = []
        for pg in pages:
            for tb in pg["tables"]:
                matrix = (tb.get("matrix") or [])[:12]
                if not matrix:
                    continue
                width = max(len(r) for r in matrix)
                body = "".join(
                    "<tr>" + "".join(f"<td>{esc(str(c))}</td>"
                                     for c in (list(r) + [""] * (width - len(r)))) + "</tr>"
                    for r in matrix)
                hdr = " / ".join(tb.get("header_context") or []) or "—"
                table_cards.append(
                    f'<div class="tblock"><div class="thead"><span class="mono">{esc(tb["region_id"])}</span>'
                    f'<span class="tag">{esc(str(tb.get("engine")))}</span>'
                    f'<span class="tag">{esc(str(tb.get("strategy")))}</span>'
                    f'<span class="tag">score {esc(str(tb.get("score")))}</span>'
                    f'<span class="tag">{tb.get("n_rows", 0)}x{tb.get("n_cols", 0)}</span></div>'
                    f'<div class="hctx">表頭回溯：{esc(hdr)}</div>'
                    f'<div class="tscroll"><table class="grid">{body}</table></div></div>')
        tables_html = "".join(table_cards) or '<div class="hctx">本次未抽出表格區域。</div>'

        doc = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(p["ENGINE_NAME"])} — {esc(meta["source_name"])}</title>
<style>
:root{{--bg:{p["VL_BG"]};--paper:{p["VL_PAPER"]};--ink:{p["VL_INK"]};--line:{p["VL_LINE"]};}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:"DM Sans","Noto Sans TC","Segoe UI",sans-serif;font-size:14px;line-height:1.6}}
.mono{{font-family:"DM Mono","Consolas",monospace;font-size:12.5px}}
.wrap{{max-width:1180px;margin:0 auto;padding:32px 20px 64px}}
.bar{{height:5px;border-radius:2px;margin-bottom:22px;
background:linear-gradient(90deg,{p["VL_BLUE"]},{p["VL_TEAL"]},{p["VL_GREEN"]},#b8ae7d,{p["VL_RED"]},#8d6f9e,{p["VL_BLUE"]})}}
h1{{font-family:"Syne","Noto Sans TC",sans-serif;font-size:25px;margin:0 0 4px;letter-spacing:.2px}}
h2{{font-family:"Syne","Noto Sans TC",sans-serif;font-size:16px;margin:30px 0 10px;
padding-bottom:6px;border-bottom:1px solid var(--line)}}
.sub{{color:#6a675f;font-size:12.5px;margin-bottom:6px}}
.seal{{float:right;width:44px;height:44px;border:2px solid {p["VL_RED"]};border-radius:3px;
color:{p["VL_RED"]};display:flex;align-items:center;justify-content:center;
font-size:22px;font-weight:700;margin-left:14px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:18px}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:12px 14px}}
.card .k{{font-family:"DM Mono",monospace;font-size:11px;color:#6a675f;text-transform:uppercase}}
.card .v{{font-size:23px;font-weight:600;margin-top:2px}}
table{{width:100%;border-collapse:collapse;background:var(--paper)}}
th,td{{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}}
th{{background:#efeee9;font-family:"DM Mono",monospace;font-size:11.5px;
text-transform:uppercase;letter-spacing:.4px}}
.tblock{{background:var(--paper);border:1px solid var(--line);border-radius:3px;
padding:12px 14px;margin-bottom:12px}}
.thead{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:6px}}
.tag{{font-family:"DM Mono",monospace;font-size:11px;background:#efeee9;
border:1px solid var(--line);border-radius:2px;padding:1px 7px;color:#55524b}}
.hctx{{font-size:12px;color:#6a675f;margin-bottom:8px}}
.tscroll{{overflow-x:auto}}
.grid td{{font-size:12.5px;white-space:nowrap}}
.grid tr:first-child td{{background:#f7f6f2;font-weight:600}}
.foot{{margin-top:34px;padding-top:12px;border-top:1px solid var(--line);
color:#8a867d;font-size:11.5px}}
</style></head><body><div class="wrap">
<div class="bar"></div>
<div class="seal">{esc(p["VL_SEAL"])}</div>
<h1>{esc(p["ENGINE_NAME"])} <span class="mono">{esc(p["ENGINE_VERSION"])}</span></h1>
<div class="sub">來源：{esc(meta["source_path"])}</div>
<div class="sub mono">run_id {esc(meta["run_id"])} · {esc(meta["finished_at"])} ·
CPU {esc(str(meta["cpu_threads"]))} threads · GPU OFF</div>
<div class="cards">{card_html}</div>

<h2>驗證閘門 Gates</h2>
<table><tr><th>ID</th><th>Gate</th><th>Status</th><th>Detail</th></tr>{gate_rows}</table>

<h2>逐頁分流 Page Triage</h2>
<table><tr><th>Page</th><th>Type</th><th>Engine</th><th>Chars</th><th>Tables</th>
<th>Strategy</th><th>ms</th></tr>{page_rows}</table>

<h2>表格區域 Tables (前 12 列預覽)</h2>
{tables_html}

<h2>引擎能力探測 Capabilities</h2>
<table><tr><th>Component</th><th>Version</th></tr>{cap_rows}</table>

<div class="foot">Veritas Intelligence Analytics · {esc(p["ASSET_ID"])} · 只增不減 append-only ledger ·
Markdown 為衍生輸出，結構化真值以 extraction.json / tables/*.csv 為準。</div>
</div></body></html>"""
        path = self.out / "report.html"
        _write_text(path, doc, self.params["TEXT_ENCODING"])
        self._reg(path)
        return path


# [VIA:ANCHOR:GATES] -----------------------------------------------------------------
def _run_gates(meta: Dict[str, Any], pages: List[Dict[str, Any]],
               caps: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """FNC_GATES — G00–G12 驗證閘門，PASS / WARN / ERR 三態標記。"""
    g: List[Dict[str, Any]] = []

    def add(gid: str, name: str, ok: bool, detail: str, warn_only: bool = True) -> None:
        status = "PASS" if ok else ("WARN" if warn_only else "ERR")
        g.append({"id": gid, "name": name, "status": status, "detail": detail})

    add("G00", "輸入檔存在且可讀", meta["source_exists"], meta["source_path"], warn_only=False)
    add("G01", "pdfplumber 可用", not str(caps.get("pdfplumber", "")).startswith("MISSING"),
        str(caps.get("pdfplumber")), warn_only=False)
    add("G02", "頁數 > 0", len(pages) > 0, f"{len(pages)} pages", warn_only=False)

    typed = all(pg.get("type") in ("digital", "scanned") for pg in pages)
    add("G03", "每頁皆完成分流", typed, "所有頁面皆標記 digital / scanned")

    empty_digital = [pg["page_no"] for pg in pages
                     if pg["type"] == "digital" and not (pg.get("text") or "").strip()]
    add("G04", "原生頁文字非空", not empty_digital, f"空文字頁: {empty_digital or '無'}")

    dup = []
    for pg in pages:
        boxes = [(t["region_id"], tuple(t["bbox"])) for t in pg["tables"] if t.get("bbox")]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if _bbox_overlap_ratio(boxes[i][1], boxes[j][1]) >= params["DEDUP_OVERLAP_RATIO"]:
                    dup.append(f"{boxes[i][0]}~{boxes[j][0]}")
    add("G05", "無重複表格區域 (overlap-ratio)", not dup, f"重複: {dup or '無'}")

    ragged = [t["region_id"] for pg in pages for t in pg["tables"]
              if (t.get("matrix") and len({len(r) for r in t["matrix"]}) > 1)]
    add("G06", "表格欄數一致性", not ragged, f"欄數不齊: {ragged[:8] or '無'}")

    thin = [t["region_id"] for pg in pages for t in pg["tables"]
            if t.get("n_rows", 0) < params["TABLE_MIN_ROWS"]
            or t.get("n_cols", 0) < params["TABLE_MIN_COLS"]]
    add("G07", "表格最小規模", not thin, f"過小表格: {thin[:8] or '無'}")

    scanned = [pg for pg in pages if pg["type"] == "scanned"]
    no_ocr = [pg["page_no"] for pg in scanned
              if not (pg.get("text") or "").strip() and not pg["tables"]]
    add("G08", "掃描頁 OCR 產出", not no_ocr,
        f"無 OCR 產出頁: {no_ocr or '無'}（掃描頁共 {len(scanned)}）")

    add("G09", "輸出檔已寫入", meta["n_output_files"] > 0, f"{meta['n_output_files']} files")
    add("G10", "Ledger append-only 已追加", meta["ledger_appended"], meta["ledger_path"])
    add("G11", "run_id 可重現 (blake2s)", bool(meta["run_id"]), meta["run_id"])
    add("G12", "GPU 強制關閉",
        os.environ.get("CUDA_VISIBLE_DEVICES", "") == "" and params["OCR_FORCE_CPU"],
        "CUDA_VISIBLE_DEVICES='' / use_gpu=False")
    return g


# [VIA:ANCHOR:CLASS] -----------------------------------------------------------------
class PDFPlumberPlusEngine:
    """
    CLS_VIA_PDFPLUMBERPLUS_V1 — runner 相容介面。

        CFG = {"pdf_path": r"...\\x.pdf", "out_dir": r"...", "params": {...覆寫...}}
        result = PDFPlumberPlusEngine(CFG).run()   # -> dict, 含 "ok"
    """

    def __init__(self, CFG: Optional[Dict[str, Any]] = None) -> None:
        CFG = CFG or {}
        self.params: Dict[str, Any] = dict(_PARAMS)
        self.params.update(CFG.get("params") or {})
        self.pdf_path = Path(str(CFG.get("pdf_path", ""))).expanduser()
        out = CFG.get("out_dir") or str(Path(self.params["VIA_ROOT"]) / self.params["OUT_SUBDIR"])
        self.out_root = Path(out).expanduser()
        self.cpu_threads = _apply_cpu_env(self.params["OCR_CPU_THREADS"])

    # ---- 主流程 ----
    def run(self) -> Dict[str, Any]:
        t0 = time.time()
        p = self.params
        started = _now_iso()
        _progress(0.0, "初始化 · 探測引擎能力")

        caps = _probe_capabilities(p)
        source_exists = self.pdf_path.is_file()
        run_id = _run_id(self.pdf_path, p) if source_exists else "0" * (p["RUN_ID_BYTES"] * 2)
        out_dir = self.out_root / f"{self.pdf_path.stem or 'NO_INPUT'}_{run_id}"
        emitter = _Emitter(out_dir, p)
        ledger_path = self.out_root / p["LEDGER_NAME"]

        pages: List[Dict[str, Any]] = []
        errors: List[str] = []

        if not source_exists:
            errors.append(f"INPUT_NOT_FOUND: {self.pdf_path}")
        elif str(caps.get("pdfplumber", "")).startswith("MISSING"):
            errors.append("PDFPLUMBER_MISSING")
        else:
            try:
                pages = self._extract_all(caps)
            except Exception as exc:
                errors.append(f"EXTRACT_FAILED: {exc.__class__.__name__}: {exc}")
                _log(traceback.format_exc())

        _progress(88.0, "輸出 JSON / CSV / Markdown / HTML")
        meta: Dict[str, Any] = {
            "engine": p["ENGINE_NAME"],
            "engine_version": p["ENGINE_VERSION"],
            "asset_id": p["ASSET_ID"],
            "run_id": run_id,
            "source_path": str(self.pdf_path),
            "source_name": self.pdf_path.name or "(no input)",
            "source_exists": source_exists,
            "out_dir": str(out_dir),
            "started_at": started,
            "finished_at": _now_iso(),
            "elapsed_sec": round(time.time() - t0, 3),
            "cpu_threads": self.cpu_threads,
            "n_pages": len(pages),
            "n_tables": sum(len(pg["tables"]) for pg in pages),
            "n_digital": sum(1 for pg in pages if pg["type"] == "digital"),
            "n_scanned": sum(1 for pg in pages if pg["type"] == "scanned"),
            "n_chars": sum(len(pg.get("text") or "") for pg in pages),
            "errors": errors,
            "n_output_files": 0,
            "ledger_appended": False,
            "ledger_path": str(ledger_path),
        }

        n_csv = 0
        try:
            if p["EMIT_CSV"]:
                n_csv = emitter.emit_csv(pages)
            if p["EMIT_MARKDOWN"]:
                emitter.emit_markdown(meta, pages)
            if p["EMIT_JSON"]:
                emitter.emit_json({"meta": meta, "capabilities": caps, "pages": pages})
        except Exception as exc:
            errors.append(f"EMIT_FAILED: {exc.__class__.__name__}: {exc}")
        meta["n_output_files"] = len(emitter.files)
        meta["n_csv"] = n_csv

        try:
            _append_jsonl(ledger_path, {
                "ts": _now_iso(), "run_id": run_id, "engine": p["ENGINE_NAME"],
                "version": p["ENGINE_VERSION"], "source": str(self.pdf_path),
                "out_dir": str(out_dir), "n_pages": meta["n_pages"],
                "n_tables": meta["n_tables"], "n_digital": meta["n_digital"],
                "n_scanned": meta["n_scanned"], "elapsed_sec": meta["elapsed_sec"],
                "errors": errors,
            })
            meta["ledger_appended"] = True
        except Exception as exc:
            errors.append(f"LEDGER_FAILED: {exc.__class__.__name__}: {exc}")

        gates = _run_gates(meta, pages, caps, p)
        if p["EMIT_HTML_REPORT"]:
            try:
                emitter.emit_html(meta, pages, gates, caps)
                meta["n_output_files"] = len(emitter.files)
            except Exception as exc:
                errors.append(f"HTML_FAILED: {exc.__class__.__name__}: {exc}")

        hard_err = [g for g in gates if g["status"] == "ERR"]
        ok = (not errors) and (not hard_err)
        _progress(100.0, "完成" if ok else "完成（含警告）")

        return {
            "ok": ok,
            "run_id": run_id,
            "meta": meta,
            "gates": gates,
            "capabilities": caps,
            "out_dir": str(out_dir),
            "report_html": str(out_dir / "report.html") if p["EMIT_HTML_REPORT"] else "",
            "files": emitter.files,
            "errors": errors,
            "pages": pages,
        }

    # ---- 逐頁抽取 ----
    def _extract_all(self, caps: Dict[str, Any]) -> List[Dict[str, Any]]:
        import pdfplumber
        p = self.params
        triage = _Triage(self.pdf_path, p)
        digital = _DigitalExtractor(p)
        scanned = _ScannedExtractor(p)
        pages: List[Dict[str, Any]] = []

        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                total = len(pdf.pages)
                _log(f"共 {total} 頁；快篩後端 = {triage.backend}；CPU threads = {self.cpu_threads}")
                for idx in range(total):
                    tp = time.time()
                    page_no = idx + 1
                    _progress(2.0 + 85.0 * idx / max(1, total), f"第 {page_no}/{total} 頁 · 分流中")
                    plb_page = pdf.pages[idx]

                    if triage.available:
                        native = triage.native_text(idx)
                        area = triage.page_area(idx)
                    else:
                        native = (plb_page.extract_text() or "").strip()
                        area = max(1.0, float(plb_page.width) * float(plb_page.height))

                    density = len(native) / area
                    is_digital = (len(native) >= p["TRIAGE_MIN_CHARS"]
                                  and density >= p["TRIAGE_MIN_CHAR_DENSITY"])

                    if is_digital:
                        res = digital.extract(plb_page, page_no)
                        rec = {"page_no": page_no, "type": "digital", "engine": "pdfplumber",
                               "note": "", "text": res["text"], "tables": res["tables"]}
                    else:
                        img = triage.render_rgb(idx) if triage.available else None
                        res = scanned.extract(img, page_no)
                        rec = {"page_no": page_no, "type": "scanned", "engine": res["engine"],
                               "note": res.get("note", ""), "text": res["text"],
                               "tables": res["tables"]}
                        del img

                    rec["n_chars"] = len(rec["text"] or "")
                    rec["elapsed_ms"] = int((time.time() - tp) * 1000)
                    pages.append(rec)

                    try:
                        plb_page.flush_cache()
                    except Exception:
                        pass
                    gc.collect()
        finally:
            triage.close()
            gc.collect()
        return pages


# 別名：與 VIA runner 慣例對齊
CLS = PDFPlumberPlusEngine


# [VIA:ANCHOR:CLI] -------------------------------------------------------------------
def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog=_PARAMS["ENGINE_NAME"],
        description="VIA PDFPlumber-Plus 多引擎 PDF 抽取（純 CPU 優化，原生文字優先 -> OCR 後備）")
    ap.add_argument("pdf", nargs="?", default="", help="PDF 檔案路徑，或使用 --scan-dir 批次")
    ap.add_argument("--out", default="", help="輸出根目錄（預設 VIA_ROOT\\outputs\\PDFPlumberPlus）")
    ap.add_argument("--scan-dir", default="", help="批次處理整個資料夾內的 *.pdf")
    ap.add_argument("--threads", type=int, default=0, help="CPU 執行緒數（0=全核心）")
    ap.add_argument("--no-ocr", action="store_true", help="完全停用 OCR（只處理原生電子文字）")
    ap.add_argument("--no-structure", action="store_true", help="掃描頁改用 PaddleOCR 而非 PP-Structure")
    ap.add_argument("--no-html", action="store_true", help="不產生 HTML 報告")
    ap.add_argument("--json-only", action="store_true", help="只輸出 extraction.json")
    ap.add_argument("--selftest", action="store_true", help="自我測試：產生樣本 PDF 並跑完整流程")
    return ap.parse_args(argv)


def _cfg_from_args(ns: argparse.Namespace, pdf: str) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {"OCR_CPU_THREADS": ns.threads}
    if ns.no_ocr:
        overrides["OCR_ENABLE"] = False
    if ns.no_structure:
        overrides["OCR_USE_STRUCTURE"] = False
    if ns.no_html:
        overrides["EMIT_HTML_REPORT"] = False
    if ns.json_only:
        overrides.update({"EMIT_CSV": False, "EMIT_MARKDOWN": False, "EMIT_HTML_REPORT": False})
    cfg: Dict[str, Any] = {"pdf_path": pdf, "params": overrides}
    if ns.out:
        cfg["out_dir"] = ns.out
    return cfg


def _make_sample_pdf(path: Path) -> bool:
    """FNC_SELFTEST_FIXTURE — 用 reportlab 產生含線框表格的測試 PDF（無則跳過）。"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, h - 70, "VIA SelfTest Report")
    c.setFont("Helvetica", 10)
    c.drawString(60, h - 90, "Quarterly Revenue Summary (unit: NTD thousand)")
    cols = [60, 200, 320, 440, 540]
    rows = [h - 110, h - 132, h - 154, h - 176, h - 198]
    data = [["Segment", "Q1", "Q2", "Q3"],
            ["Foundry", "1,204", "1,388", "1,455"],
            ["Packaging", "622", "701", "690"],
            ["Testing", "318", "344", "402"]]
    for y in rows:
        c.line(cols[0], y, cols[-1], y)
    for x in cols:
        c.line(x, rows[0], x, rows[-1])
    for r, row in enumerate(data):
        for ci, cell in enumerate(row):
            c.drawString(cols[ci] + 5, rows[r] - 15, cell)
    c.drawString(60, h - 230, "Note: figures are synthetic fixtures for engine validation only.")
    c.showPage()
    c.save()
    return True


def main(argv: Optional[List[str]] = None) -> int:
    ns = _parse_args(argv)

    if ns.selftest:
        base = Path(ns.out) if ns.out else Path.cwd() / "VIA_PDFPlumberPlus_SelfTest"
        sample = base / "selftest_sample.pdf"
        # 只增不減：樣本已存在就沿用，重跑時 run_id 完全一致 (Gate G11 可觀察)
        if not sample.is_file() and not _make_sample_pdf(sample):
            _log("selftest 需要 reportlab 產生樣本 PDF；"
                 "請改用 `python VIA_PDFPlumberPlusEngine.py <你的.pdf>`")
            return 2
        cfg = _cfg_from_args(ns, str(sample))
        cfg["out_dir"] = str(base)
        res = PDFPlumberPlusEngine(cfg).run()
        print(json.dumps({"ok": res["ok"], "run_id": res["run_id"],
                          "n_pages": res["meta"]["n_pages"],
                          "n_tables": res["meta"]["n_tables"],
                          "report_html": res["report_html"],
                          "gates": {g["id"]: g["status"] for g in res["gates"]}},
                         ensure_ascii=False, indent=2))
        return 0 if res["ok"] else 1

    targets: List[Path] = []
    if ns.scan_dir:
        targets = sorted(Path(ns.scan_dir).expanduser().glob("*.pdf"))
    elif ns.pdf:
        targets = [Path(ns.pdf).expanduser()]

    if not targets:
        _log("未指定輸入。用法： python VIA_PDFPlumberPlusEngine.py <file.pdf> [--out DIR]"
             " | --scan-dir DIR | --selftest")
        return 2

    summaries: List[Dict[str, Any]] = []
    worst = 0
    for i, tgt in enumerate(targets, start=1):
        _log(f"=== ({i}/{len(targets)}) {tgt.name} ===")
        res = PDFPlumberPlusEngine(_cfg_from_args(ns, str(tgt))).run()
        summaries.append({
            "file": tgt.name, "ok": res["ok"], "run_id": res["run_id"],
            "n_pages": res["meta"]["n_pages"], "n_tables": res["meta"]["n_tables"],
            "n_digital": res["meta"]["n_digital"], "n_scanned": res["meta"]["n_scanned"],
            "elapsed_sec": res["meta"]["elapsed_sec"],
            "gates_warn": [g["id"] for g in res["gates"] if g["status"] == "WARN"],
            "gates_err": [g["id"] for g in res["gates"] if g["status"] == "ERR"],
            "report_html": res["report_html"], "errors": res["errors"],
        })
        if not res["ok"]:
            worst = 1
    print(json.dumps({"ok": worst == 0, "count": len(summaries), "results": summaries},
                     ensure_ascii=False, indent=2))
    return worst


if __name__ == "__main__":
    sys.exit(main())
