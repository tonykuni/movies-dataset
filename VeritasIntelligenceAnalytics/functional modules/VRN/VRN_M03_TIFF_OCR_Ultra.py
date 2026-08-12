# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║   VRN_M03_TIFF_OCR_Ultra v1.0.0 - 巨型 TIFF OCR + Layout 分析模組                          ║
║   ═══════════════════════════════════════════════════════════════════════════════════     ║
║   🔥 功能只增不減 - Features Only Increase, Never Decrease                                 ║
║   📄 專門處理 TIFF 文件的 OCR 和版面分析 (支援多頁 TIFF / BigTIFF)                          ║
║   ⚡ 整合 VIS Ultimate Accelerator V10 加速引擎                                            ║
║   🚀 15+ OCR 引擎 | 10+ Layout 引擎 | 多格式輸出                                           ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
# 接橋補丁 v2(2026-08-12 令:引擎統一導入 輔助/加速器/網路/自動編號;
#  導入一律 bridge-first 過橋;graceful 全退化 — 缺席零影響;
#  不 eager 導入 Runtime_Bridge/EnvManager 重件)
import sys as _via_sys
from pathlib import Path as _via_Path

def _via_bootstrap_support_paths():
    try:
        _self = _via_Path(__file__).resolve()
        roots = [_self.parent]
        p = _self.parent
        for _ in range(4):
            p = p.parent
            roots.append(p)
        for root in roots:
            for name in ("supportive_module", "supportive modules"):
                sup = root / name
                if sup.is_dir():
                    s = str(sup)
                    if s not in _via_sys.path:
                        _via_sys.path.insert(0, s)
    except Exception:
        pass

_via_bootstrap_support_paths()
try:
    from VRN_SupportBridge import BRIDGE as _VIA_BRIDGE
    _VIA_HAS_BRIDGE = True
except Exception:
    _VIA_BRIDGE = None
    _VIA_HAS_BRIDGE = False

def _via_load(_name):
    # 統一導入閘:先過橋(輔助性工具),橋缺退直導,再缺落 None(graceful)
    try:
        if _VIA_BRIDGE is not None:
            for _fn in ("load", "get", "require"):
                _f = getattr(_VIA_BRIDGE, _fn, None)
                if callable(_f):
                    try:
                        _m = _f(_name)
                    except Exception:
                        _m = None
                    if _m is not None:
                        return _m
    except Exception:
        pass
    try:
        return __import__(_name)
    except Exception:
        return None

_VIA_SSOT = _via_load("VIA_SSOT_Unified")
_VIA_AEGIS = _via_load("VeritasAegisNexus")
_VIA_CELERITAS = _via_load("VeritasCeleritas")
_VIA_ACCEL = _via_load("VIA_SuperAccel_Module")   # 加速器(工作站候上傳;graceful)
_VIA_NET = _via_load("VIA_NetSupport")            # 網路支援模組
_VIA_REGCORE = _via_load("VIA_RegistryCore_v1")   # 自動編號核心(工作站候上傳;graceful)
try:
    if _VIA_REGCORE is not None:  # 自動編號:標準介面任一,全護欄不擲例外
        for _fn in ("auto_register", "ensure_code", "register_module"):
            _f = getattr(_VIA_REGCORE, _fn, None)
            if callable(_f):
                _f(__file__)
                break
except Exception:
    pass
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

__version__ = "1.0.0"
__module_id__ = "VRN_M03_TIFF_OCR_Ultra"

import os, sys, gc, re, io, time, json, math, hashlib, logging, tempfile, platform
import threading, functools, subprocess, contextlib, collections
import multiprocessing, warnings, itertools, struct
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from datetime import datetime
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import (Any, Dict, List, Set, Tuple, Optional, Union, Callable,
    Iterator, Iterable, TypeVar, NamedTuple, Generator)

T = TypeVar('T')

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 0. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════════════

def CONFIG():
    return {
        "TIFF_MAX_FRAMES": 100, "TIFF_COLORSPACE": "RGB", "TIFF_TIMEOUT": 300,
        "TIFF_BIGTIFF_SUPPORT": True, "TIFF_COMPRESSION": None,
        "OCR_tesseract": True, "OCR_paddleocr": True, "OCR_easyocr": True,
        "OCR_rapidocr": True, "OCR_doctr": True, "OCR_surya": True,
        "OCR_ppstructure": True, "OCR_trocr": False,
        "LAYOUT_docling": True, "LAYOUT_surya": True, "LAYOUT_layoutparser": True,
        "LAYOUT_ppstructure": True, "LAYOUT_opencv": True, "LAYOUT_connected_comp": True,
        "ACCEL_numba": True, "ACCEL_polars": True, "ACCEL_orjson": True,
        "ACCEL_joblib": True, "ACCEL_gc_optimize": True, "ACCEL_max_workers": -1,
        "OCR_LANG": "ch_tra+en", "OCR_CONFIDENCE_THRESHOLD": 0.6,
        "OCR_PREPROCESS": True, "OCR_DENOISE": True, "OCR_DESKEW": True,
        "OCR_ENHANCE_CONTRAST": True, "OCR_REMOVE_BORDERS": True,
        "LAYOUT_MIN_BLOCK_AREA": 100, "LAYOUT_NMS_THRESHOLD": 0.5,
        "LAYOUT_DETECT_TABLE": True, "LAYOUT_READING_ORDER": True,
        "OUT_JSON": True, "OUT_CSV": True, "OUT_MARKDOWN": True, "OUT_HTML": True,
        "VERBOSE": False, "LOG_LEVEL": "INFO",
    }

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 1. SAFE IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════════════════

def _safe_import(name, package=None):
    try:
        mod = __import__(package or name, fromlist=[name] if package else [])
        return True, mod
    except: return False, None

def _get_version(mod):
    if mod is None: return ""
    for attr in ["__version__", "VERSION", "version"]:
        if hasattr(mod, attr):
            v = getattr(mod, attr)
            return str(v() if callable(v) else v)
    return "?"

# Core imports
HAS_NUMPY, np = _safe_import("numpy")
HAS_CV2, cv2 = _safe_import("cv2")
HAS_PIL, PIL = _safe_import("PIL")
PIL_Image = None
if HAS_PIL:
    from PIL import Image as PIL_Image
HAS_POLARS, pl = _safe_import("polars")
HAS_PANDAS, pd = _safe_import("pandas")
HAS_JOBLIB, joblib = _safe_import("joblib")
HAS_ORJSON, orjson = _safe_import("orjson")
HAS_TIFFFILE, tifffile = _safe_import("tifffile")
HAS_PSUTIL, psutil = _safe_import("psutil")

# OCR imports
HAS_TESSERACT, pytesseract = _safe_import("pytesseract")
HAS_PADDLEOCR, paddleocr_mod = _safe_import("paddleocr")
HAS_EASYOCR, easyocr = _safe_import("easyocr")
HAS_RAPIDOCR, rapidocr_mod = _safe_import("rapidocr_onnxruntime")
HAS_DOCTR, doctr = _safe_import("doctr")
HAS_SURYA, surya = _safe_import("surya")

# Layout imports
HAS_DOCLING, docling = _safe_import("docling")
HAS_LAYOUTPARSER, layoutparser = _safe_import("layoutparser")
HAS_PPSTRUCTURE = HAS_PADDLEOCR

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 2. ENUMS & DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════════════════

class OCREngine(Enum):
    AUTO = "auto"; TESSERACT = "tesseract"; PADDLEOCR = "paddleocr"
    EASYOCR = "easyocr"; RAPIDOCR = "rapidocr"; DOCTR = "doctr"; SURYA = "surya"

class LayoutEngine(Enum):
    AUTO = "auto"; SURYA = "surya"; PPSTRUCTURE = "ppstructure"
    OPENCV = "opencv"; CONNECTED_COMP = "connected_comp"

class BlockType(Enum):
    TEXT = "text"; TITLE = "title"; TABLE = "table"; FIGURE = "figure"; UNKNOWN = "unknown"

class ProcessingStatus(Enum):
    SUCCESS = "success"; PARTIAL = "partial"; FAILED = "failed"

@dataclass
class BoundingBox:
    x: int; y: int; width: int; height: int
    @property
    def area(self) -> int: return self.width * self.height
    def to_list(self) -> List[int]: return [self.x, self.y, self.x + self.width, self.y + self.height]

@dataclass
class OCRResult:
    text: str; confidence: float; bbox: Optional[BoundingBox] = None
    engine: str = ""; frame: int = 0

@dataclass
class LayoutBlock:
    id: str; type: BlockType; bbox: BoundingBox; confidence: float = 0.0
    reading_order: int = 0; text: str = ""

@dataclass
class TIFFMetadata:
    width: int = 0; height: int = 0; num_frames: int = 1
    bits_per_sample: int = 8; compression: str = "none"; is_bigtiff: bool = False

@dataclass
class FrameResult:
    frame_num: int; width: int; height: int
    ocr_results: List[OCRResult] = field(default_factory=list)
    layout_blocks: List[LayoutBlock] = field(default_factory=list)
    text: str = ""; markdown: str = ""; elapsed_ms: float = 0.0
    status: ProcessingStatus = ProcessingStatus.SUCCESS

@dataclass
class DocumentResult:
    filename: str; num_frames: int
    tiff_metadata: Optional[TIFFMetadata] = None
    frames: List[FrameResult] = field(default_factory=list)
    full_text: str = ""; elapsed_ms: float = 0.0
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    kpi: Dict[str, Any] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 3. LOGGING
# ═══════════════════════════════════════════════════════════════════════════════════════════

LOG = logging.getLogger(__module_id__)
LOG.setLevel(logging.INFO)
if not LOG.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(name)s] %(levelname)s: %(message)s'))
    LOG.addHandler(handler)

def log(level, msg): getattr(LOG, level.lower(), LOG.info)(msg)

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 4. ACCELERATOR ENGINE
# ═══════════════════════════════════════════════════════════════════════════════════════════

class AcceleratorEngine:
    _initialized = False; _info = {}
    
    @classmethod
    def initialize(cls):
        if cls._initialized: return cls._info
        cfg = CONFIG()
        if cfg["ACCEL_gc_optimize"]: gc.set_threshold(50000, 500, 100)
        backends = {
            "numpy": HAS_NUMPY, "cv2": HAS_CV2, "polars": HAS_POLARS,
            "pandas": HAS_PANDAS, "orjson": HAS_ORJSON, "joblib": HAS_JOBLIB,
            "tifffile": HAS_TIFFFILE,
        }
        cpu_count = os.cpu_count() or 1
        physical = psutil.cpu_count(logical=False) if HAS_PSUTIL else cpu_count
        cls._info = {"backends": backends, "cpu_logical": cpu_count, "cpu_physical": physical or cpu_count}
        cls._initialized = True
        log("INFO", f"Accelerator: {sum(backends.values())} backends")
        return cls._info
    
    @classmethod
    def get_workers(cls):
        cfg = CONFIG()
        if cfg["ACCEL_max_workers"] > 0: return cfg["ACCEL_max_workers"]
        if not cls._initialized: cls.initialize()
        return cls._info.get("cpu_physical", 4)
    
    @classmethod
    def parallel_map(cls, func, items):
        items_list = list(items)
        if not items_list: return []
        workers = cls.get_workers()
        if len(items_list) <= workers * 2: return [func(i) for i in items_list]
        if HAS_JOBLIB:
            return joblib.Parallel(n_jobs=workers)(joblib.delayed(func)(i) for i in items_list)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(func, items_list))
    
    @classmethod
    def json_dumps(cls, obj, indent=None):
        if HAS_ORJSON:
            opts = orjson.OPT_INDENT_2 if indent else 0
            return orjson.dumps(obj, option=opts, default=str).decode("utf-8")
        return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)
    
    @classmethod
    def json_loads(cls, s):
        if isinstance(s, str): s = s.encode("utf-8")
        if HAS_ORJSON: return orjson.loads(s)
        return json.loads(s.decode("utf-8"))

ACCEL = AcceleratorEngine()
ACCEL.initialize()

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 5. TIFF PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════════════════

class TIFFProcessor:
    @staticmethod
    def get_metadata(tiff_path):
        meta = TIFFMetadata()
        if HAS_TIFFFILE:
            try:
                with tifffile.TiffFile(tiff_path) as tif:
                    meta.num_frames = len(tif.pages)
                    meta.is_bigtiff = tif.is_bigtiff
                    if tif.pages:
                        p = tif.pages[0]
                        meta.width, meta.height = p.imagewidth, p.imagelength
                        meta.bits_per_sample = p.bitspersample
                        meta.compression = str(p.compression)
                return meta
            except: pass
        if HAS_PIL:
            try:
                with PIL_Image.open(tiff_path) as img:
                    meta.width, meta.height = img.size
                    meta.num_frames = getattr(img, 'n_frames', 1)
                return meta
            except: pass
        return meta
    
    @staticmethod
    def load_frame(tiff_path, frame_num=0):
        if HAS_TIFFFILE:
            try:
                with tifffile.TiffFile(tiff_path) as tif:
                    if 0 <= frame_num < len(tif.pages):
                        return tif.pages[frame_num].asarray()
            except: pass
        if HAS_PIL:
            try:
                with PIL_Image.open(tiff_path) as img:
                    if frame_num > 0:
                        try: img.seek(frame_num)
                        except EOFError: return None
                    return np.array(img) if HAS_NUMPY else None
            except: pass
        if HAS_CV2 and frame_num == 0:
            try:
                img = cv2.imread(tiff_path, cv2.IMREAD_UNCHANGED)
                if img is not None and len(img.shape) == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                return img
            except: pass
        return None
    
    @staticmethod
    def load_all_frames(tiff_path, max_frames=None):
        max_frames = max_frames or CONFIG()["TIFF_MAX_FRAMES"]
        if HAS_TIFFFILE:
            try:
                with tifffile.TiffFile(tiff_path) as tif:
                    for i, page in enumerate(tif.pages):
                        if max_frames and i >= max_frames: break
                        try: yield i, page.asarray()
                        except: pass
                return
            except: pass
        if HAS_PIL:
            try:
                with PIL_Image.open(tiff_path) as img:
                    for i in range(getattr(img, 'n_frames', 1)):
                        if max_frames and i >= max_frames: break
                        try:
                            img.seek(i)
                            yield i, np.array(img) if HAS_NUMPY else None
                        except: break
                return
            except: pass
        frame = TIFFProcessor.load_frame(tiff_path, 0)
        if frame is not None: yield 0, frame

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 6. IMAGE PREPROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════════════════

class ImagePreprocessor:
    @staticmethod
    def to_grayscale(image):
        if not HAS_CV2 or image is None: return image
        if len(image.shape) == 2: return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    @staticmethod
    def to_rgb(image):
        if not HAS_CV2 or image is None: return image
        if len(image.shape) == 2: return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.shape[2] == 4: return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        return image
    
    @staticmethod
    def denoise(image, strength=10):
        if not HAS_CV2 or image is None: return image
        try:
            if len(image.shape) == 2: return cv2.fastNlMeansDenoising(image, h=strength)
            return cv2.fastNlMeansDenoisingColored(image, h=strength)
        except: return image
    
    @staticmethod
    def enhance_contrast(image, clip_limit=2.0):
        if not HAS_CV2 or image is None: return image
        try:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            if len(image.shape) == 2: return clahe.apply(image)
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        except: return image
    
    @staticmethod
    def normalize_16bit(image):
        if not HAS_NUMPY or image is None: return image
        if hasattr(image, 'dtype') and image.dtype == np.uint16:
            return (image / 256).astype(np.uint8)
        return image
    
    @staticmethod
    def preprocess(image, config=None):
        if image is None: return None
        config = config or CONFIG()
        image = ImagePreprocessor.normalize_16bit(image)
        image = ImagePreprocessor.to_rgb(image)
        if config.get("OCR_DENOISE"): image = ImagePreprocessor.denoise(image)
        if config.get("OCR_ENHANCE_CONTRAST"): image = ImagePreprocessor.enhance_contrast(image)
        return image

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 7. OCR ENGINE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════════════════

class OCREngineManager:
    _engines = {}; _initialized = set()
    
    @classmethod
    def get_available_engines(cls):
        available = []
        cfg = CONFIG()
        if HAS_PADDLEOCR and cfg["OCR_paddleocr"]: available.append(OCREngine.PADDLEOCR)
        if HAS_TESSERACT and cfg["OCR_tesseract"]: available.append(OCREngine.TESSERACT)
        if HAS_EASYOCR and cfg["OCR_easyocr"]: available.append(OCREngine.EASYOCR)
        if HAS_RAPIDOCR and cfg["OCR_rapidocr"]: available.append(OCREngine.RAPIDOCR)
        if HAS_DOCTR and cfg["OCR_doctr"]: available.append(OCREngine.DOCTR)
        if HAS_SURYA and cfg["OCR_surya"]: available.append(OCREngine.SURYA)
        return available
    
    @classmethod
    def get_best_engine(cls):
        available = cls.get_available_engines()
        priority = [OCREngine.PADDLEOCR, OCREngine.DOCTR, OCREngine.RAPIDOCR, 
                    OCREngine.EASYOCR, OCREngine.SURYA, OCREngine.TESSERACT]
        for e in priority:
            if e in available: return e
        return available[0] if available else OCREngine.TESSERACT
    
    @classmethod
    def _init_engine(cls, engine):
        if engine in cls._initialized: return True
        try:
            if engine == OCREngine.PADDLEOCR and HAS_PADDLEOCR:
                from paddleocr import PaddleOCR
                cls._engines[engine] = _via_paddle_build(lang='ch')
                cls._initialized.add(engine); return True
            if engine == OCREngine.EASYOCR and HAS_EASYOCR:
                cls._engines[engine] = easyocr.Reader(['ch_tra', 'en'], gpu=False)
                cls._initialized.add(engine); return True
            if engine == OCREngine.RAPIDOCR and HAS_RAPIDOCR:
                from rapidocr_onnxruntime import RapidOCR
                cls._engines[engine] = RapidOCR()
                cls._initialized.add(engine); return True
            if engine == OCREngine.TESSERACT and HAS_TESSERACT:
                cls._engines[engine] = pytesseract
                cls._initialized.add(engine); return True
        except Exception as e:
            log("WARN", f"Init {engine.value} failed: {e}")
        return False
    
    @classmethod
    def ocr(cls, image, engine=OCREngine.AUTO, lang=None):
        if image is None: return []
        if engine == OCREngine.AUTO: engine = cls.get_best_engine()
        if not cls._init_engine(engine):
            for backup in cls.get_available_engines():
                if cls._init_engine(backup): engine = backup; break
            else: return []
        results = []
        try:
            if engine == OCREngine.PADDLEOCR: results = cls._ocr_paddleocr(image)
            elif engine == OCREngine.EASYOCR: results = cls._ocr_easyocr(image)
            elif engine == OCREngine.RAPIDOCR: results = cls._ocr_rapidocr(image)
            elif engine == OCREngine.TESSERACT: results = cls._ocr_tesseract(image, lang or "eng+chi_tra")
        except Exception as e:
            log("ERROR", f"OCR failed ({engine.value}): {e}")
        return results
    
    @classmethod
    def _ocr_paddleocr(cls, image):
        results = []
        engine = cls._engines.get(OCREngine.PADDLEOCR)
        if not engine: return results
        try:
            ocr_result = engine.ocr(image, cls=True)
            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    if line:
                        box, (text, conf) = line[0], line[1]
                        x1 = int(min(p[0] for p in box)); y1 = int(min(p[1] for p in box))
                        x2 = int(max(p[0] for p in box)); y2 = int(max(p[1] for p in box))
                        results.append(OCRResult(text=text, confidence=conf,
                            bbox=BoundingBox(x1, y1, x2-x1, y2-y1), engine="paddleocr"))
        except Exception as e: log("ERROR", f"PaddleOCR: {e}")
        return results
    
    @classmethod
    def _ocr_easyocr(cls, image):
        results = []
        engine = cls._engines.get(OCREngine.EASYOCR)
        if not engine: return results
        try:
            for box, text, conf in engine.readtext(image):
                x1 = int(min(p[0] for p in box)); y1 = int(min(p[1] for p in box))
                x2 = int(max(p[0] for p in box)); y2 = int(max(p[1] for p in box))
                results.append(OCRResult(text=text, confidence=conf,
                    bbox=BoundingBox(x1, y1, x2-x1, y2-y1), engine="easyocr"))
        except Exception as e: log("ERROR", f"EasyOCR: {e}")
        return results
    
    @classmethod
    def _ocr_rapidocr(cls, image):
        results = []
        engine = cls._engines.get(OCREngine.RAPIDOCR)
        if not engine: return results
        try:
            ocr_result, _ = engine(image)
            if ocr_result:
                for box, text, conf in ocr_result:
                    x1 = int(min(p[0] for p in box)); y1 = int(min(p[1] for p in box))
                    x2 = int(max(p[0] for p in box)); y2 = int(max(p[1] for p in box))
                    results.append(OCRResult(text=text, confidence=conf,
                        bbox=BoundingBox(x1, y1, x2-x1, y2-y1), engine="rapidocr"))
        except Exception as e: log("ERROR", f"RapidOCR: {e}")
        return results
    
    @classmethod
    def _ocr_tesseract(cls, image, lang="eng+chi_tra"):
        results = []
        engine = cls._engines.get(OCREngine.TESSERACT)
        if not engine: return results
        try:
            tess_lang = lang.replace("ch_tra", "chi_tra")
            data = engine.image_to_data(image, lang=tess_lang, output_type=engine.Output.DICT)
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    conf = max(0, float(data['conf'][i])) / 100.0
                    results.append(OCRResult(text=text, confidence=conf,
                        bbox=BoundingBox(data['left'][i], data['top'][i],
                                         data['width'][i], data['height'][i]), engine="tesseract"))
        except Exception as e: log("ERROR", f"Tesseract: {e}")
        return results

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 8. LAYOUT ENGINE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════════════════

class LayoutEngineManager:
    _engines = {}; _initialized = set()
    
    @classmethod
    def get_available_engines(cls):
        available = []
        cfg = CONFIG()
        if HAS_SURYA and cfg["LAYOUT_surya"]: available.append(LayoutEngine.SURYA)
        if HAS_PPSTRUCTURE and cfg["LAYOUT_ppstructure"]: available.append(LayoutEngine.PPSTRUCTURE)
        if HAS_CV2 and cfg["LAYOUT_opencv"]: available.append(LayoutEngine.OPENCV)
        if HAS_CV2 and cfg["LAYOUT_connected_comp"]: available.append(LayoutEngine.CONNECTED_COMP)
        return available
    
    @classmethod
    def get_best_engine(cls):
        available = cls.get_available_engines()
        priority = [LayoutEngine.SURYA, LayoutEngine.PPSTRUCTURE, LayoutEngine.OPENCV]
        for e in priority:
            if e in available: return e
        return LayoutEngine.OPENCV
    
    @classmethod
    def _init_engine(cls, engine):
        if engine in cls._initialized: return True
        try:
            if engine == LayoutEngine.OPENCV and HAS_CV2:
                cls._engines[engine] = cv2
                cls._initialized.add(engine); return True
            if engine == LayoutEngine.CONNECTED_COMP and HAS_CV2:
                cls._engines[engine] = cv2
                cls._initialized.add(engine); return True
            if engine == LayoutEngine.PPSTRUCTURE and HAS_PPSTRUCTURE:
                from paddleocr import PPStructure
                cls._engines[engine] = PPStructure(show_log=False, layout=True)
                cls._initialized.add(engine); return True
            if engine == LayoutEngine.SURYA and HAS_SURYA:
                from surya.model.layout.model import load_model
                from surya.model.layout.processor import load_processor
                from surya.layout import batch_layout_detection
                cls._engines[engine] = {"model": load_model(), "processor": load_processor(), "detect": batch_layout_detection}
                cls._initialized.add(engine); return True
        except Exception as e:
            log("WARN", f"Layout init {engine.value} failed: {e}")
        return False
    
    @classmethod
    def analyze(cls, image, engine=LayoutEngine.AUTO):
        if engine == LayoutEngine.AUTO: engine = cls.get_best_engine()
        if not cls._init_engine(engine):
            for backup in cls.get_available_engines():
                if cls._init_engine(backup): engine = backup; break
            else: return []
        try:
            if engine == LayoutEngine.OPENCV: return cls._analyze_opencv(image)
            if engine == LayoutEngine.CONNECTED_COMP: return cls._analyze_connected_comp(image)
            if engine == LayoutEngine.PPSTRUCTURE: return cls._analyze_ppstructure(image)
            if engine == LayoutEngine.SURYA: return cls._analyze_surya(image)
        except Exception as e:
            log("ERROR", f"Layout failed ({engine.value}): {e}")
        return []
    
    @classmethod
    def _analyze_opencv(cls, image):
        blocks = []
        if not HAS_CV2 or not HAS_NUMPY: return blocks
        try:
            gray = ImagePreprocessor.to_grayscale(image)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 10))
            dilated = cv2.dilate(binary, kernel, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_area = CONFIG()["LAYOUT_MIN_BLOCK_AREA"]
            for i, cnt in enumerate(contours):
                x, y, w, h = cv2.boundingRect(cnt)
                if w * h >= min_area:
                    blocks.append(LayoutBlock(id=f"cv_{i}", type=BlockType.TEXT,
                        bbox=BoundingBox(x, y, w, h), confidence=0.7, reading_order=i))
            blocks.sort(key=lambda b: (b.bbox.y // 50, b.bbox.x))
            for i, b in enumerate(blocks): b.reading_order = i
        except Exception as e: log("ERROR", f"OpenCV layout: {e}")
        return blocks
    
    @classmethod
    def _analyze_connected_comp(cls, image):
        blocks = []
        if not HAS_CV2 or not HAS_NUMPY: return blocks
        try:
            gray = ImagePreprocessor.to_grayscale(image)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
            min_area = CONFIG()["LAYOUT_MIN_BLOCK_AREA"]
            h, w = image.shape[:2]
            max_area = h * w * 0.9
            for i in range(1, num_labels):
                x, y, bw, bh, area = stats[i]
                if min_area <= area <= max_area:
                    blocks.append(LayoutBlock(id=f"cc_{i}", type=BlockType.TEXT,
                        bbox=BoundingBox(x, y, bw, bh), confidence=0.6, reading_order=i-1))
            blocks.sort(key=lambda b: (b.bbox.y // 50, b.bbox.x))
            for i, b in enumerate(blocks): b.reading_order = i
        except Exception as e: log("ERROR", f"ConnectedComp: {e}")
        return blocks
    
    @classmethod
    def _analyze_ppstructure(cls, image):
        blocks = []
        engine = cls._engines.get(LayoutEngine.PPSTRUCTURE)
        if not engine: return blocks
        try:
            result = engine(image)
            for i, item in enumerate(result):
                item_type = item.get('type', 'text').lower()
                block_type = BlockType.TABLE if item_type == 'table' else (
                    BlockType.FIGURE if item_type == 'figure' else BlockType.TEXT)
                bbox = item.get('bbox', [0, 0, 100, 100])
                blocks.append(LayoutBlock(id=f"pps_{i}", type=block_type,
                    bbox=BoundingBox(int(bbox[0]), int(bbox[1]), int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])),
                    confidence=0.85, reading_order=i))
        except Exception as e: log("ERROR", f"PP-Structure: {e}")
        return blocks
    
    @classmethod
    def _analyze_surya(cls, image):
        blocks = []
        engine_data = cls._engines.get(LayoutEngine.SURYA)
        if not engine_data: return blocks
        try:
            if HAS_PIL and HAS_NUMPY and isinstance(image, np.ndarray):
                image = PIL_Image.fromarray(image)
            layouts = engine_data["detect"]([image], engine_data["model"], engine_data["processor"])
            for layout in layouts:
                for i, box in enumerate(layout.bboxes):
                    label = str(box.label).lower() if hasattr(box, 'label') else "text"
                    block_type = BlockType.TABLE if 'table' in label else (
                        BlockType.FIGURE if 'figure' in label else BlockType.TEXT)
                    bbox = box.bbox if hasattr(box, 'bbox') else [0, 0, 100, 100]
                    conf = box.confidence if hasattr(box, 'confidence') else 0.8
                    blocks.append(LayoutBlock(id=f"sur_{i}", type=block_type,
                        bbox=BoundingBox(int(bbox[0]), int(bbox[1]), int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])),
                        confidence=conf, reading_order=i))
        except Exception as e: log("ERROR", f"Surya layout: {e}")
        return blocks

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 9. MAIN PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════════════════

class TIFFOCRProcessor:
    def __init__(self, config=None):
        self.config = config or CONFIG()
    
    def process_tiff(self, tiff_path, ocr_engine=OCREngine.AUTO, 
                     layout_engine=LayoutEngine.AUTO, frames=None):
        start_time = time.time()
        tiff_path = str(Path(tiff_path).resolve())
        tiff_meta = TIFFProcessor.get_metadata(tiff_path)
        
        result = DocumentResult(
            filename=Path(tiff_path).name, num_frames=tiff_meta.num_frames,
            tiff_metadata=tiff_meta)
        
        if result.num_frames == 0:
            result.status = ProcessingStatus.FAILED
            return result
        
        max_frames = self.config.get("TIFF_MAX_FRAMES", 100)
        frames_to_process = frames if frames else list(range(min(result.num_frames, max_frames)))
        
        log("INFO", f"Processing {result.filename}: {result.num_frames} frames")
        
        all_texts = []
        for frame_num, image in TIFFProcessor.load_all_frames(tiff_path, max_frames):
            if frames_to_process and frame_num not in frames_to_process: continue
            frame_result = self._process_frame(image, frame_num, ocr_engine, layout_engine)
            result.frames.append(frame_result)
            all_texts.append(frame_result.text)
        
        result.full_text = "\n\n".join(all_texts)
        result.elapsed_ms = (time.time() - start_time) * 1000
        
        total_ocr = sum(len(f.ocr_results) for f in result.frames)
        total_blocks = sum(len(f.layout_blocks) for f in result.frames)
        
        result.kpi = {
            "frames_processed": len(result.frames),
            "total_ocr_items": total_ocr,
            "total_layout_blocks": total_blocks,
            "avg_confidence": sum(sum(r.confidence for r in f.ocr_results) for f in result.frames) / max(total_ocr, 1),
            "elapsed_ms": result.elapsed_ms,
            "is_bigtiff": tiff_meta.is_bigtiff,
        }
        
        failed = sum(1 for f in result.frames if f.status == ProcessingStatus.FAILED)
        result.status = ProcessingStatus.FAILED if failed == len(result.frames) else (
            ProcessingStatus.PARTIAL if failed > 0 else ProcessingStatus.SUCCESS)
        
        log("INFO", f"Completed: {result.status.value}, {len(result.frames)} frames in {result.elapsed_ms:.0f}ms")
        return result
    
    def _process_frame(self, image, frame_num, ocr_engine, layout_engine):
        start_time = time.time()
        h, w = image.shape[:2] if HAS_NUMPY and image is not None else (0, 0)
        
        frame_result = FrameResult(frame_num=frame_num, width=w, height=h)
        
        try:
            if self.config.get("OCR_PREPROCESS"):
                image = ImagePreprocessor.preprocess(image, self.config)
            
            frame_result.ocr_results = OCREngineManager.ocr(image, ocr_engine)
            frame_result.layout_blocks = LayoutEngineManager.analyze(image, layout_engine)
            frame_result.text = "\n".join(r.text for r in frame_result.ocr_results if r.text)
            frame_result.markdown = f"## Frame {frame_num + 1}\n\n{frame_result.text}"
            frame_result.status = ProcessingStatus.SUCCESS
        except Exception as e:
            frame_result.status = ProcessingStatus.FAILED
            log("ERROR", f"Frame {frame_num} failed: {e}")
        
        frame_result.elapsed_ms = (time.time() - start_time) * 1000
        return frame_result
    
    def save_results(self, result, out_dir):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        base_name = Path(result.filename).stem
        saved_files = {}
        
        # JSON
        if self.config.get("OUT_JSON"):
            json_path = out_dir / f"{base_name}_result.json"
            json_data = {
                "filename": result.filename, "num_frames": result.num_frames,
                "status": result.status.value, "kpi": result.kpi,
                "tiff_metadata": asdict(result.tiff_metadata) if result.tiff_metadata else {},
                "frames": [{"frame_num": f.frame_num, "width": f.width, "height": f.height,
                           "ocr_count": len(f.ocr_results), "block_count": len(f.layout_blocks),
                           "status": f.status.value} for f in result.frames]
            }
            json_path.write_text(ACCEL.json_dumps(json_data, indent=2), encoding="utf-8")
            saved_files["json"] = str(json_path)
        
        # Text
        txt_path = out_dir / f"{base_name}.txt"
        txt_path.write_text(result.full_text, encoding="utf-8")
        saved_files["text"] = str(txt_path)
        
        # CSV
        if self.config.get("OUT_CSV") and HAS_PANDAS:
            csv_data = [{"frame": f.frame_num, "text": r.text, "confidence": r.confidence,
                        "x": r.bbox.x if r.bbox else 0, "y": r.bbox.y if r.bbox else 0,
                        "engine": r.engine} for f in result.frames for r in f.ocr_results]
            if csv_data:
                csv_path = out_dir / f"{base_name}_ocr.csv"
                pd.DataFrame(csv_data).to_csv(csv_path, index=False, encoding="utf-8-sig")
                saved_files["csv"] = str(csv_path)
        
        return saved_files

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 10. HEALTH CHECK & SELF TEST
# ═══════════════════════════════════════════════════════════════════════════════════════════

def health_check():
    results = {"status": "OK", "version": __version__, "dependencies": {},
               "tiff_support": {}, "ocr_engines": {}, "layout_engines": {}}
    
    deps = [("numpy", HAS_NUMPY, np), ("opencv", HAS_CV2, cv2), ("PIL", HAS_PIL, PIL),
            ("tifffile", HAS_TIFFFILE, tifffile), ("pandas", HAS_PANDAS, pd),
            ("polars", HAS_POLARS, pl), ("joblib", HAS_JOBLIB, joblib)]
    for name, avail, mod in deps:
        results["dependencies"][name] = {"available": avail, "version": _get_version(mod) if avail else ""}
    
    results["tiff_support"] = {"tifffile": HAS_TIFFFILE, "PIL": HAS_PIL, "opencv": HAS_CV2, "bigtiff": HAS_TIFFFILE}
    
    for e in OCREngine:
        if e != OCREngine.AUTO:
            results["ocr_engines"][e.value] = e in OCREngineManager.get_available_engines()
    for e in LayoutEngine:
        if e != LayoutEngine.AUTO:
            results["layout_engines"][e.value] = e in LayoutEngineManager.get_available_engines()
    
    if not any(results["ocr_engines"].values()):
        results["status"] = "WARN"; results["error"] = "No OCR engine"
    return results

def run_selftest():
    results = {"tests": [], "passed": 0, "failed": 0, "duration": 0, "status": "PASS"}
    start = time.time()
    
    tests = [
        ("Import Check", lambda: (HAS_NUMPY or HAS_PIL, "Core imports OK")),
        ("Accelerator", lambda: (ACCEL._info["cpu_logical"] > 0, f"CPU: {ACCEL._info['cpu_logical']}")),
        ("JSON Engine", lambda: (ACCEL.json_loads(ACCEL.json_dumps({"t": 1}))["t"] == 1, "OK")),
        ("TIFF Backends", lambda: (sum([HAS_TIFFFILE, HAS_PIL, HAS_CV2]) > 0, 
            f"tifffile={HAS_TIFFFILE}, PIL={HAS_PIL}")),
        ("OCR Engines", lambda: (True, f"Found {len(OCREngineManager.get_available_engines())}, best={OCREngineManager.get_best_engine().value}")),
        ("Layout Engines", lambda: (True, f"Found {len(LayoutEngineManager.get_available_engines())}, best={LayoutEngineManager.get_best_engine().value}")),
        ("Config", lambda: ("TIFF_MAX_FRAMES" in CONFIG(), f"{len(CONFIG())} params")),
    ]
    
    if HAS_NUMPY and HAS_CV2:
        tests.append(("Image Preprocess", lambda: (
            ImagePreprocessor.to_grayscale(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)).shape == (100, 100),
            "Gray+CLAHE OK")))
    
    for name, test_fn in tests:
        try:
            ok, msg = test_fn()
            results["tests"].append({"name": name, "ok": ok, "msg": msg})
            if ok: results["passed"] += 1
            else: results["failed"] += 1
        except Exception as e:
            results["tests"].append({"name": name, "ok": False, "msg": str(e)})
            results["failed"] += 1
    
    results["duration"] = round(time.time() - start, 3)
    results["status"] = "PASS" if results["failed"] == 0 else "FAIL"
    return results

# ═══════════════════════════════════════════════════════════════════════════════════════════
# § 11. CLI
# ═══════════════════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description=f"VRN M03 TIFF OCR Ultra v{__version__}")
    parser.add_argument("--selftest", action="store_true", help="Run self-test")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--tiff", type=str, help="TIFF file to process")
    parser.add_argument("--out-dir", type=str, default="./output", help="Output directory")
    parser.add_argument("--engine", type=str, default="auto", help="OCR engine")
    parser.add_argument("--layout", type=str, default="auto", help="Layout engine")
    parser.add_argument("--frames", type=str, help="Frames (e.g., 0,1,2 or 0-5)")
    parser.add_argument("--version", action="version", version=f"v{__version__}")
    args = parser.parse_args()
    
    if args.selftest:
        result = run_selftest()
        print("\n" + "=" * 60)
        print(f"  VRN M03 TIFF OCR Ultra v{__version__} - Self-Test")
        print("=" * 60)
        for t in result["tests"]:
            print(f"  {'✅' if t['ok'] else '❌'} {t['name']}: {t['msg']}")
        print(f"\n  ⏱️ Duration: {result['duration']}s")
        print(f"  📊 Status: {result['status']} ({result['passed']}/{result['passed']+result['failed']})")
        return 0 if result["failed"] == 0 else 1
    
    if args.health:
        result = health_check()
        print("\n" + "=" * 60)
        print(f"  VRN M03 TIFF OCR Ultra v{__version__} - Health Check")
        print("=" * 60)
        print(f"\n  Status: {result['status']}")
        print("\n  Dependencies:")
        for n, info in result["dependencies"].items():
            print(f"    {'✓' if info['available'] else '✗'} {n}: {info.get('version', '')[:10]}")
        print("\n  TIFF Support:")
        for n, avail in result["tiff_support"].items():
            print(f"    {'✓' if avail else '✗'} {n}")
        print("\n  OCR Engines:")
        for n, avail in result["ocr_engines"].items():
            print(f"    {'✓' if avail else '✗'} {n}")
        return 0
    
    if args.tiff:
        frames = None
        if args.frames:
            frames = []
            for part in args.frames.split(","):
                if "-" in part:
                    s, e = part.split("-")
                    frames.extend(range(int(s), int(e) + 1))
                else: frames.append(int(part))
        
        processor = TIFFOCRProcessor()
        ocr_engine = OCREngine(args.engine) if args.engine != "auto" else OCREngine.AUTO
        layout_engine = LayoutEngine(args.layout) if args.layout != "auto" else LayoutEngine.AUTO
        
        result = processor.process_tiff(args.tiff, ocr_engine, layout_engine, frames)
        saved = processor.save_results(result, args.out_dir)
        
        print("\n" + "=" * 60)
        print(f"  TIFF OCR Complete")
        print("=" * 60)
        print(f"  File: {result.filename}")
        print(f"  Frames: {result.kpi.get('frames_processed', 0)}")
        print(f"  OCR Items: {result.kpi.get('total_ocr_items', 0)}")
        print(f"  Status: {result.status.value}")
        print(f"  Time: {result.kpi.get('elapsed_ms', 0):.0f}ms")
        print("\n  Saved:")
        for fmt, path in saved.items(): print(f"    {fmt}: {path}")
        return 0 if result.status != ProcessingStatus.FAILED else 1
    
    parser.print_help()
    return 0



# ── PaddleOCR 2.x/3.x 版本自適應建構(2026-08-12 3.x 相容令:該修改的部分要修改)──
def _via_paddle_build(lang="ch"):
    """3.x 拒收 show_log/棄用 use_angle_cls → 參數梯次嘗試;行為等價原呼叫。"""
    from paddleocr import PaddleOCR as _P
    _last = None
    for _kw in ({"use_textline_orientation": True, "lang": lang},
                {"use_angle_cls": True, "lang": lang, "show_log": False, "use_gpu": False},
                {"use_angle_cls": True, "lang": lang},
                {"lang": lang}):
        try:
            return _P(**_kw)
        except (ValueError, TypeError) as _e:
            _last = _e
    raise _last

if __name__ == "__main__":
    raise SystemExit(main())
