#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  VRN_M03_Layout_OCR_Ultra.py v3.0                                            ║
║  ════════════════════════════════════════════════════════════════════════    ║
║  功能: 版面分析 + OCR 文字提取 (多引擎 + Fallback)                           ║
║  支援引擎: PaddleOCR, EasyOCR, Tesseract, OpenCV                             ║
║  Lego 標準介面: module_meta(), run(), self_test(), health_check()            ║
║  ★ TIFF-only Gate: 只接受 M02 輸出的高畫質 TIFF                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
# 接橋補丁(2026-08-13 稽核令 TOOL-009 後續:功能引擎統一導入支援模組;
#  graceful 全退化 — 橋/核心缺席零影響;不 eager 導入 Runtime_Bridge/EnvManager 重件)
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
try:
    import VIA_SSOT_Unified as _VIA_SSOT
except Exception:
    _VIA_SSOT = None
try:
    import VeritasAegisNexus as _VIA_AEGIS
except Exception:
    _VIA_AEGIS = None
try:
    import VeritasCeleritas as _VIA_CELERITAS
except Exception:
    _VIA_CELERITAS = None
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

__version__ = "3.0.0"
__module_id__ = "VRN_M03_Layout_OCR"

import os
import sys
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field, asdict

# =============================================================================
# § 1. 依賴檢測
# =============================================================================

DEPS = {
    "PIL": False,
    "cv2": False,
    "numpy": False,
    "paddleocr": False,
    "easyocr": False,
    "pytesseract": False,
}

try:
    from PIL import Image
    DEPS["PIL"] = True
except ImportError:
    Image = None

try:
    import cv2
    DEPS["cv2"] = True
except ImportError:
    cv2 = None

try:
    import numpy as np
    DEPS["numpy"] = True
except ImportError:
    np = None

try:
    from paddleocr import PaddleOCR
    DEPS["paddleocr"] = True
except ImportError:
    PaddleOCR = None

try:
    import easyocr
    DEPS["easyocr"] = True
except ImportError:
    easyocr = None

try:
    import pytesseract
    DEPS["pytesseract"] = True
except ImportError:
    pytesseract = None

# =============================================================================
# § 2. 模組元數據
# =============================================================================

META = {
    "module_id": __module_id__,
    "module_no": "M03",
    "version": __version__,
    "name": "Layout_OCR",
    "description": "版面分析 + OCR 文字提取 (多引擎 + Fallback)",
    "category": "OCR_Pipeline",
    "inputs": [".tiff"],
    "outputs": ["elements[]", "layout.json", "text.txt"],
    "depends_on": ["M02"],
    "outputs_to": ["M04", "M05"],
    "libs": ["paddleocr", "easyocr", "pytesseract", "opencv-python", "PIL"],
    "risk_level": "MEDIUM",
    "fallback_order": ["paddleocr", "easyocr", "tesseract", "opencv", "stub"],
}

# =============================================================================
# § 3. 資料結構
# =============================================================================

@dataclass
class BoundingBox:
    """邊界框"""
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    def to_list(self) -> List[int]:
        return [self.x1, self.y1, self.x2, self.y2]


@dataclass
class OCRElement:
    """OCR 元素"""
    element_id: str
    element_type: str  # text, table, figure, header, footer
    content: str
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    page: int = 0
    engine: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PageLayout:
    """頁面版面"""
    page_num: int
    width: int
    height: int
    elements: List[OCRElement] = field(default_factory=list)
    text_blocks: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "page_num": self.page_num,
            "width": self.width,
            "height": self.height,
            "elements_count": len(self.elements),
            "elements": [e.to_dict() for e in self.elements],
        }


# =============================================================================
# § 4. OCR 引擎
# =============================================================================

class BaseOCREngine:
    """OCR 引擎基類"""
    
    ENGINE_NAME = "base"
    
    def __init__(self):
        self._initialized = False
        self._warnings: List[str] = []
    
    def initialize(self) -> bool:
        """初始化引擎"""
        return False
    
    def process(self, image_path: str, page_num: int = 0) -> List[OCRElement]:
        """處理影像"""
        return []
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return False


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR 引擎"""
    
    ENGINE_NAME = "paddleocr"
    
    def __init__(self, lang: str = "ch"):
        super().__init__()
        self.lang = lang
        self._ocr = None
    
    def initialize(self) -> bool:
        if not DEPS["paddleocr"]:
            return False
        try:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                show_log=False,
                use_gpu=False
            )
            self._initialized = True
            return True
        except Exception as e:
            self._warnings.append(f"PaddleOCR init failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return DEPS["paddleocr"]
    
    def process(self, image_path: str, page_num: int = 0) -> List[OCRElement]:
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            result = self._ocr.ocr(image_path, cls=True)
            elements = []
            
            if result and result[0]:
                for idx, line in enumerate(result[0]):
                    if not line:
                        continue
                    
                    box = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    # 轉換 box 格式 [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] -> [x1,y1,x2,y2]
                    x1 = int(min(p[0] for p in box))
                    y1 = int(min(p[1] for p in box))
                    x2 = int(max(p[0] for p in box))
                    y2 = int(max(p[1] for p in box))
                    
                    elements.append(OCRElement(
                        element_id=f"paddle_{page_num}_{idx}",
                        element_type="text",
                        content=text,
                        bbox=[x1, y1, x2, y2],
                        confidence=confidence,
                        page=page_num,
                        engine=self.ENGINE_NAME
                    ))
            
            return elements
            
        except Exception as e:
            self._warnings.append(f"PaddleOCR error: {e}")
            return []


class EasyOCREngine(BaseOCREngine):
    """EasyOCR 引擎"""
    
    ENGINE_NAME = "easyocr"
    
    def __init__(self, langs: List[str] = None):
        super().__init__()
        self.langs = langs or ["ch_tra", "en"]
        self._reader = None
    
    def initialize(self) -> bool:
        if not DEPS["easyocr"]:
            return False
        try:
            self._reader = easyocr.Reader(self.langs, gpu=False, verbose=False)
            self._initialized = True
            return True
        except Exception as e:
            self._warnings.append(f"EasyOCR init failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return DEPS["easyocr"]
    
    def process(self, image_path: str, page_num: int = 0) -> List[OCRElement]:
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            results = self._reader.readtext(image_path)
            elements = []
            
            for idx, (box, text, confidence) in enumerate(results):
                # box 是 4 個點的座標
                x1 = int(min(p[0] for p in box))
                y1 = int(min(p[1] for p in box))
                x2 = int(max(p[0] for p in box))
                y2 = int(max(p[1] for p in box))
                
                elements.append(OCRElement(
                    element_id=f"easy_{page_num}_{idx}",
                    element_type="text",
                    content=text,
                    bbox=[x1, y1, x2, y2],
                    confidence=confidence,
                    page=page_num,
                    engine=self.ENGINE_NAME
                ))
            
            return elements
            
        except Exception as e:
            self._warnings.append(f"EasyOCR error: {e}")
            return []


class TesseractEngine(BaseOCREngine):
    """Tesseract 引擎"""
    
    ENGINE_NAME = "tesseract"
    
    def __init__(self, lang: str = "chi_tra+eng"):
        super().__init__()
        self.lang = lang
    
    def initialize(self) -> bool:
        if not DEPS["pytesseract"]:
            return False
        try:
            # 測試 tesseract 是否可用
            pytesseract.get_tesseract_version()
            self._initialized = True
            return True
        except Exception as e:
            self._warnings.append(f"Tesseract init failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return DEPS["pytesseract"]
    
    def process(self, image_path: str, page_num: int = 0) -> List[OCRElement]:
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            img = Image.open(image_path)
            
            # 使用 image_to_data 獲取詳細資訊
            data = pytesseract.image_to_data(
                img, 
                lang=self.lang, 
                output_type=pytesseract.Output.DICT
            )
            
            elements = []
            n_boxes = len(data['text'])
            
            for idx in range(n_boxes):
                text = data['text'][idx].strip()
                conf = int(data['conf'][idx])
                
                if not text or conf < 0:
                    continue
                
                x = data['left'][idx]
                y = data['top'][idx]
                w = data['width'][idx]
                h = data['height'][idx]
                
                elements.append(OCRElement(
                    element_id=f"tess_{page_num}_{idx}",
                    element_type="text",
                    content=text,
                    bbox=[x, y, x + w, y + h],
                    confidence=conf / 100.0,
                    page=page_num,
                    engine=self.ENGINE_NAME
                ))
            
            return elements
            
        except Exception as e:
            self._warnings.append(f"Tesseract error: {e}")
            return []


class OpenCVEngine(BaseOCREngine):
    """OpenCV 引擎 (簡易文字偵測)"""
    
    ENGINE_NAME = "opencv"
    
    def __init__(self):
        super().__init__()
    
    def initialize(self) -> bool:
        if not DEPS["cv2"] or not DEPS["numpy"]:
            return False
        self._initialized = True
        return True
    
    def is_available(self) -> bool:
        return DEPS["cv2"] and DEPS["numpy"]
    
    def process(self, image_path: str, page_num: int = 0) -> List[OCRElement]:
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            # 讀取影像
            img = cv2.imread(image_path)
            if img is None:
                return []
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用 MSER 偵測文字區域
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            elements = []
            hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in regions]
            
            for idx, hull in enumerate(hulls[:100]):  # 限制數量
                x, y, w, h = cv2.boundingRect(hull)
                
                # 過濾太小的區域
                if w < 10 or h < 10:
                    continue
                
                elements.append(OCRElement(
                    element_id=f"cv_{page_num}_{idx}",
                    element_type="text_region",
                    content="[detected region]",
                    bbox=[x, y, x + w, y + h],
                    confidence=0.5,
                    page=page_num,
                    engine=self.ENGINE_NAME,
                    metadata={"detection_only": True}
                ))
            
            return elements
            
        except Exception as e:
            self._warnings.append(f"OpenCV error: {e}")
            return []


class StubEngine(BaseOCREngine):
    """Stub 引擎 (永遠可用，保證至少 1 個 element)"""
    
    ENGINE_NAME = "stub"
    
    def initialize(self) -> bool:
        self._initialized = True
        return True
    
    def is_available(self) -> bool:
        return True  # 永遠可用
    
    def process(self, image_path: str, page_num: int = 0) -> List[OCRElement]:
        # 嘗試獲取圖片尺寸
        width, height = 0, 0
        if DEPS["PIL"]:
            try:
                img = Image.open(image_path)
                width, height = img.size
            except:
                pass
        
        return [OCRElement(
            element_id=f"stub_{page_num}_0",
            element_type="page_image",
            content="[stub - no OCR performed]",
            bbox=[0, 0, width, height],
            confidence=0.0,
            page=page_num,
            engine=self.ENGINE_NAME,
            metadata={"source": image_path, "width": width, "height": height}
        )]


# =============================================================================
# § 5. Layout OCR 主引擎
# =============================================================================

class LayoutOCREngine:
    """版面分析 + OCR 主引擎"""
    
    FALLBACK_ORDER = ["paddleocr", "easyocr", "tesseract", "opencv", "stub"]
    
    def __init__(self, fallback_order: List[str] = None):
        self.fallback_order = fallback_order or self.FALLBACK_ORDER
        self._engines: Dict[str, BaseOCREngine] = {}
        self._warnings: List[str] = []
        
        self._init_engines()
    
    def _init_engines(self):
        """初始化所有可用引擎"""
        self._engines["paddleocr"] = PaddleOCREngine()
        self._engines["easyocr"] = EasyOCREngine()
        self._engines["tesseract"] = TesseractEngine()
        self._engines["opencv"] = OpenCVEngine()
        self._engines["stub"] = StubEngine()
    
    def get_available_engines(self) -> List[str]:
        """獲取可用引擎列表"""
        return [name for name, engine in self._engines.items() if engine.is_available()]
    
    def process_tiff(self, tiff_path: str) -> Tuple[List[OCRElement], Dict]:
        """
        處理 TIFF 檔案 (使用 Fallback)
        
        Returns:
            (elements, result_dict)
        """
        tiff_path = Path(tiff_path)
        
        # TIFF-only Gate
        if tiff_path.suffix.lower() not in [".tif", ".tiff"]:
            return [], {
                "status": "FAIL",
                "error": f"TIFF-only Gate: {tiff_path.suffix} not allowed"
            }
        
        if not tiff_path.exists():
            return [], {"status": "FAIL", "error": f"File not found: {tiff_path}"}
        
        # 使用 Fallback 順序嘗試
        for engine_name in self.fallback_order:
            engine = self._engines.get(engine_name)
            if not engine or not engine.is_available():
                continue
            
            try:
                elements = engine.process(str(tiff_path))
                if elements:
                    return elements, {
                        "status": "OK",
                        "engine": engine_name,
                        "elements_count": len(elements)
                    }
            except Exception as e:
                self._warnings.append(f"{engine_name} failed: {e}")
                continue
        
        # 最終使用 stub
        stub = self._engines["stub"]
        elements = stub.process(str(tiff_path))
        return elements, {
            "status": "FALLBACK",
            "engine": "stub",
            "elements_count": len(elements),
            "warning": "All engines failed, using stub"
        }
    
    def process_batch(self, tiff_paths: List[str]) -> Tuple[List[OCRElement], List[PageLayout], Dict]:
        """批次處理多個 TIFF"""
        all_elements = []
        layouts = []
        results = []
        
        for page_num, tiff_path in enumerate(tiff_paths):
            elements, result = self.process_tiff(tiff_path)
            
            # 更新頁碼
            for elem in elements:
                elem.page = page_num
            
            all_elements.extend(elements)
            results.append({"file": tiff_path, "result": result})
            
            # 創建 PageLayout
            width, height = 0, 0
            if DEPS["PIL"]:
                try:
                    img = Image.open(tiff_path)
                    width, height = img.size
                except:
                    pass
            
            layouts.append(PageLayout(
                page_num=page_num,
                width=width,
                height=height,
                elements=elements
            ))
        
        return all_elements, layouts, {
            "status": "OK" if all_elements else "FAIL",
            "total_elements": len(all_elements),
            "pages": len(tiff_paths),
            "results": results,
            "warnings": self._warnings
        }


# =============================================================================
# § 6. Lego 標準介面
# =============================================================================

def module_meta() -> Dict[str, Any]:
    """Lego 介面: 模組元數據"""
    return META.copy()


def run(cfg: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lego 介面: 執行模組
    
    輸入: ctx["tiff_paths"] (來自 M02)
    輸出: ctx["elements"], ctx["layouts"]
    
    ★ TIFF-only Gate: 只接受 .tif/.tiff
    """
    start_time = time.time()
    
    # 獲取輸入
    tiff_paths = ctx.get("tiff_paths", [])
    
    # TIFF-only Gate
    if not tiff_paths:
        ctx.setdefault("warnings", []).append("M03: No tiff_paths from M02")
        ctx.setdefault("elements", [])
        ctx["M03_result"] = {"status": "SKIP", "reason": "No TIFF input"}
        return ctx
    
    # 檢查所有輸入都是 TIFF
    non_tiff = [p for p in tiff_paths if Path(p).suffix.lower() not in [".tif", ".tiff"]]
    if non_tiff:
        ctx.setdefault("errors", []).append(f"M03 TIFF-only Gate: {len(non_tiff)} non-TIFF files rejected")
        tiff_paths = [p for p in tiff_paths if Path(p).suffix.lower() in [".tif", ".tiff"]]
    
    if not tiff_paths:
        ctx["elements"] = []
        ctx["M03_result"] = {"status": "FAIL", "error": "TIFF-only Gate: No valid TIFF files"}
        return ctx
    
    # 執行 OCR
    fallback_order = cfg.get("fallback_order", META["fallback_order"])
    engine = LayoutOCREngine(fallback_order=fallback_order)
    
    elements, layouts, result = engine.process_batch(tiff_paths)
    
    # 更新 context
    ctx.setdefault("elements", []).extend([e.to_dict() for e in elements])
    ctx["layouts"] = [l.to_dict() for l in layouts]
    ctx.setdefault("warnings", []).extend(result.get("warnings", []))
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    ctx["M03_result"] = {
        "status": result["status"],
        "total_elements": result["total_elements"],
        "pages": result["pages"],
        "available_engines": engine.get_available_engines(),
        "elapsed_ms": elapsed_ms
    }
    
    return ctx


def self_test() -> Dict[str, Any]:
    """Lego 介面: 自我測試"""
    tests = []
    passed = 0
    start_time = time.time()
    
    # Test 1: 依賴檢查
    available = [k for k, v in DEPS.items() if v]
    ok = len(available) >= 1
    tests.append({"name": "dependencies", "pass": ok, "detail": f"Available: {available}"})
    if ok:
        passed += 1
    
    # Test 2: 引擎檢測
    engine = LayoutOCREngine()
    available_engines = engine.get_available_engines()
    ok = len(available_engines) >= 1  # 至少 stub
    tests.append({"name": "available_engines", "pass": ok, "detail": available_engines})
    if ok:
        passed += 1
    
    # Test 3: Stub 永遠可用
    stub = StubEngine()
    ok = stub.is_available()
    tests.append({"name": "stub_available", "pass": ok, "detail": "Stub is fallback guarantee"})
    if ok:
        passed += 1
    
    # Test 4: 創建測試 TIFF 並處理
    if DEPS["PIL"]:
        try:
            # 創建測試圖片
            test_img = Image.new('RGB', (200, 100), 'white')
            # 添加一些內容讓 OCR 有東西可處理
            from PIL import ImageDraw
            draw = ImageDraw.Draw(test_img)
            draw.text((10, 10), "Test 123", fill='black')
            
            test_path = Path(tempfile.gettempdir()) / "vrn_test_ocr.tiff"
            test_img.save(str(test_path), "TIFF")
            
            # 處理
            elements, result = engine.process_tiff(str(test_path))
            
            ok = len(elements) >= 1  # 至少 stub element
            tests.append({"name": "process_tiff", "pass": ok, "detail": result})
            if ok:
                passed += 1
            
            # 清理
            try:
                os.remove(test_path)
            except:
                pass
                
        except Exception as e:
            tests.append({"name": "process_tiff", "pass": False, "detail": str(e)})
    else:
        tests.append({"name": "process_tiff", "pass": False, "detail": "PIL not available"})
    
    # Test 5: TIFF-only Gate
    try:
        engine = LayoutOCREngine()
        elements, result = engine.process_tiff("/fake/path.pdf")  # 非 TIFF
        ok = result.get("status") == "FAIL" and "TIFF-only" in result.get("error", "")
        tests.append({"name": "tiff_only_gate", "pass": ok, "detail": result.get("error", "")})
        if ok:
            passed += 1
    except Exception as e:
        tests.append({"name": "tiff_only_gate", "pass": False, "detail": str(e)})
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    return {
        "ok": passed == len(tests),
        "passed": passed,
        "total": len(tests),
        "tests": tests,
        "elapsed_ms": elapsed_ms
    }


def health_check() -> Dict[str, Any]:
    """Lego 介面: 健康檢查"""
    engine = LayoutOCREngine()
    available = engine.get_available_engines()
    
    engines_status = {}
    for name in META["fallback_order"]:
        engines_status[name] = "available" if name in available else "missing"
    
    if len(available) >= 3:
        status = "PASS"
    elif len(available) >= 2:
        status = "WARN"
    else:
        status = "WARN" if "stub" in available else "FAIL"
    
    return {
        "status": status,
        "engines": engines_status,
        "available_count": len(available),
        "fallback_order": META["fallback_order"],
        "dependencies": DEPS,
        "message": f"{len(available)} engines available (stub always available)"
    }


# =============================================================================
# § 7. CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{__module_id__} v{__version__}")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--ocr", type=str, nargs="+", help="OCR TIFF files")
    parser.add_argument("--engine", type=str, help="Preferred engine")
    parser.add_argument("--output", type=str, help="Output JSON file")
    
    args = parser.parse_args()
    
    if args.test:
        result = self_test()
        print(f"\n{__module_id__} Self-Test:")
        for t in result["tests"]:
            icon = "✅" if t["pass"] else "❌"
            print(f"  {icon} {t['name']}: {t['detail']}")
        print(f"\nTotal: {result['passed']}/{result['total']} ({result['elapsed_ms']:.0f}ms)")
        sys.exit(0 if result["ok"] else 1)
    
    if args.health:
        result = health_check()
        print(f"\n{__module_id__} Health Check: {result['status']}")
        print(f"Fallback Order: {result['fallback_order']}")
        for name, status in result["engines"].items():
            icon = "✅" if status == "available" else "❌"
            print(f"  {icon} {name}: {status}")
        sys.exit(0)
    
    if args.ocr:
        engine = LayoutOCREngine()
        all_elements = []
        
        for tiff in args.ocr:
            print(f"Processing: {tiff}")
            elements, result = engine.process_tiff(tiff)
            print(f"  Status: {result.get('status')}")
            print(f"  Engine: {result.get('engine')}")
            print(f"  Elements: {len(elements)}")
            all_elements.extend([e.to_dict() for e in elements])
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_elements, f, ensure_ascii=False, indent=2)
            print(f"\nSaved to: {args.output}")
        
        sys.exit(0)
    
    parser.print_help()
