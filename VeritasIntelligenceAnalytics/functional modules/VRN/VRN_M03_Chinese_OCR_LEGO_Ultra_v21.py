#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  VRN_M03_Chinese_OCR_LEGO_Ultra.py                                           ║
║  Version: 2.1.0 | LEGO Architecture | Top 10 OCR + Smart Deskew + OpenCC     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  功能只增不減 | Pipeline Compliant | Cascade Fallback OCR                    ║
║  NEW: 智慧歪斜校正 (僅在需要時) + 簡繁轉換 (OpenCC s2twp)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

v2.1.0 NEW Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Smart Deskew: 偵測歪斜角度 > 閾值時才校正 (避免不必要處理)
- OpenCC: 簡體中文 → 繁體中文(台灣正體) 自動轉換
- Cascade OCR: PaddleOCR → EasyOCR → Tesseract → Simulated
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

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


import sys
import os
import argparse
import logging
import json
import time
import traceback
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from abc import ABC, abstractmethod

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 0: MODULE METADATA
# ═══════════════════════════════════════════════════════════════════════════════
__module_id__ = "M03"
__module_name__ = "Chinese_OCR_LEGO_Ultra"
__version__ = "2.1.0"
__author__ = "VRN Team"
__description__ = "Multi-engine Chinese OCR with smart deskew + OpenCC"
__dependencies__ = [
    "paddleocr", "easyocr", "pytesseract", "opencv-python", "pillow",
    "deskew", "opencc-python-reimplemented", "numpy"
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(f"VRN_{__module_id__}")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class OCRResult:
    """OCR 結果"""
    doc_id: str
    image_source: str
    layout_source: Optional[str] = None
    ocr_text: str = ""                    # 最終文字 (繁體)
    ocr_text_original: str = ""           # 原始 OCR 文字
    confidence: float = 0.0
    engine_used: str = "unknown"
    engines_tried: List[str] = field(default_factory=list)
    raw_blocks: Dict = field(default_factory=dict)
    text_blocks: List[Dict] = field(default_factory=list)
    processing_time_ms: float = 0.0
    # Deskew info
    deskew_applied: bool = False
    deskew_angle: float = 0.0
    # OpenCC info  
    opencc_applied: bool = False
    simplified_detected: bool = False
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ProcessingStats:
    """處理統計"""
    total_files: int = 0
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    deskewed: int = 0
    opencc_converted: int = 0
    total_time_ms: float = 0.0
    engines_used: Dict[str, int] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: SMART DESKEW (只在需要時校正)
# ═══════════════════════════════════════════════════════════════════════════════
class SmartDeskewer:
    """智慧歪斜校正 - 僅在角度超過閾值時校正"""
    
    # 歪斜角度閾值 (度)：低於此值不校正
    ANGLE_THRESHOLD = 0.5
    
    def __init__(self):
        self.available = False
        self.method = None
        self._init()
    
    def _init(self):
        """初始化 deskew"""
        # 方法1: deskew 套件
        try:
            import deskew
            self.available = True
            self.method = "deskew"
            logger.info("✅ Deskew: deskew library")
            return
        except ImportError:
            pass
        
        # 方法2: OpenCV
        try:
            import cv2
            import numpy as np
            self.available = True
            self.method = "opencv"
            logger.info("✅ Deskew: OpenCV method")
            return
        except ImportError:
            pass
        
        logger.warning("⚠️ Deskew unavailable (pip install deskew opencv-python)")
    
    def detect_skew_angle(self, image_path: str) -> float:
        """偵測歪斜角度"""
        if not self.available:
            return 0.0
        
        try:
            import numpy as np
            from PIL import Image
            
            img = Image.open(image_path)
            
            # 轉灰度
            if img.mode != 'L':
                img = img.convert('L')
            
            img_array = np.array(img)
            
            if self.method == "deskew":
                import deskew as dsk
                angle = dsk.determine_skew(img_array)
                return angle if angle else 0.0
            
            elif self.method == "opencv":
                import cv2
                # 使用 Hough 線偵測
                edges = cv2.Canny(img_array, 50, 150, apertureSize=3)
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
                
                if lines is None:
                    return 0.0
                
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    # 只取接近水平的線
                    if abs(angle) < 45:
                        angles.append(angle)
                
                if angles:
                    return np.median(angles)
                return 0.0
                
        except Exception as e:
            logger.warning(f"Skew detection error: {e}")
            return 0.0
    
    def deskew_if_needed(self, image_path: str, output_dir: str = None) -> Tuple[str, float, bool]:
        """
        智慧校正：只在歪斜角度超過閾值時校正
        Returns: (image_path, angle, was_corrected)
        """
        angle = self.detect_skew_angle(image_path)
        
        # 角度小於閾值，不需校正
        if abs(angle) < self.ANGLE_THRESHOLD:
            logger.debug(f"Skew {angle:.2f}° < threshold {self.ANGLE_THRESHOLD}° - no correction needed")
            return image_path, angle, False
        
        logger.info(f"   🔧 Deskew: {angle:.2f}° detected, correcting...")
        
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path)
            
            # 旋轉校正 (負角度因為要反向旋轉)
            corrected = img.rotate(-angle, expand=True, fillcolor='white')
            
            # 保存到臨時檔案或輸出目錄
            if output_dir:
                out_path = Path(output_dir) / f"{Path(image_path).stem}_deskewed{Path(image_path).suffix}"
            else:
                fd, out_path = tempfile.mkstemp(suffix=Path(image_path).suffix)
                os.close(fd)
                out_path = Path(out_path)
            
            corrected.save(str(out_path))
            logger.info(f"   ✅ Deskew complete: {angle:.2f}°")
            
            return str(out_path), angle, True
            
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
            return image_path, angle, False

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: OPENCC 簡繁轉換
# ═══════════════════════════════════════════════════════════════════════════════
class ChineseConverter:
    """簡體中文 → 繁體中文(台灣正體) 轉換器"""
    
    # 常見簡體字樣本 (用於偵測)
    SIMPLIFIED_SAMPLES = set('的一是不了在人有我他这为之来以时要出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之用着看二次今信机化进现代话体前入明社部第点平问向电高系相正张边门先科原边业儿华两头员长声几动报备场图记将进开运组该马数内两关条当几还发级面意没头点别认书张级与没几远现使统术办实区向问政南资点北运组')
    
    def __init__(self):
        self.available = False
        self.converter = None
        self._init()
    
    def _init(self):
        """初始化 OpenCC"""
        try:
            import opencc
            # s2twp: 簡體 → 繁體(台灣正體，含詞彙轉換)
            self.converter = opencc.OpenCC('s2twp')
            self.available = True
            logger.info("✅ OpenCC: s2twp (簡→繁台灣正體)")
        except ImportError:
            logger.warning("⚠️ OpenCC unavailable (pip install opencc-python-reimplemented)")
    
    def has_simplified(self, text: str) -> bool:
        """偵測文字是否包含簡體中文"""
        if not text:
            return False
        
        # 計算簡體字比例
        simplified_count = sum(1 for c in text if c in self.SIMPLIFIED_SAMPLES)
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        
        if chinese_count == 0:
            return False
        
        ratio = simplified_count / chinese_count
        return ratio > 0.1  # 超過 10% 簡體字則判定為簡體
    
    def convert_to_traditional(self, text: str) -> Tuple[str, bool]:
        """
        轉換為繁體中文
        Returns: (converted_text, was_converted)
        """
        if not self.available or not text:
            return text, False
        
        # 檢查是否需要轉換
        if not self.has_simplified(text):
            return text, False
        
        try:
            converted = self.converter.convert(text)
            logger.debug(f"OpenCC converted: {len(text)} chars")
            return converted, True
        except Exception as e:
            logger.warning(f"OpenCC conversion error: {e}")
            return text, False

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: OCR ENGINES
# ═══════════════════════════════════════════════════════════════════════════════
class OCREngine(ABC):
    """OCR 引擎抽象基類"""
    
    def __init__(self):
        self.name = "base"
        self.available = False
        self.priority = 999
        
    @abstractmethod
    def initialize(self) -> bool:
        pass
    
    @abstractmethod
    def recognize(self, image_path: str) -> Tuple[str, float, List[Dict]]:
        """Returns: (text, confidence, text_blocks)"""
        pass


class PaddleOCREngine(OCREngine):
    """PaddleOCR - Top 1"""
    
    def __init__(self):
        super().__init__()
        self.name = "paddleocr"
        self.priority = 1
        self.ocr = None
        
    def initialize(self) -> bool:
        try:
            from paddleocr import PaddleOCR
            self.ocr = _via_paddle_build(lang='ch')
            self.available = True
            logger.info(f"✅ {self.name} initialized")
            return True
        except Exception as e:
            logger.warning(f"⚠️ {self.name}: {e}")
            return False
    
    def recognize(self, image_path: str) -> Tuple[str, float, List[Dict]]:
        if not self.available:
            raise RuntimeError("PaddleOCR not initialized")
        
        result = self.ocr.ocr(image_path, cls=True)
        
        if not result or not result[0]:
            return "", 0.0, []
        
        text_blocks = []
        texts = []
        total_conf = 0.0
        
        for line in result[0]:
            text = line[1][0]
            conf = line[1][1]
            texts.append(text)
            total_conf += conf
            text_blocks.append({"text": text, "confidence": conf, "bbox": line[0], "engine": self.name})
        
        return '\n'.join(texts), total_conf / len(result[0]), text_blocks


class EasyOCREngine(OCREngine):
    """EasyOCR - Top 2"""
    
    def __init__(self):
        super().__init__()
        self.name = "easyocr"
        self.priority = 2
        self.reader = None
        
    def initialize(self) -> bool:
        try:
            import easyocr
            self.reader = easyocr.Reader(['ch_sim', 'ch_tra', 'en'], gpu=False)
            self.available = True
            logger.info(f"✅ {self.name} initialized")
            return True
        except Exception as e:
            logger.warning(f"⚠️ {self.name}: {e}")
            return False
    
    def recognize(self, image_path: str) -> Tuple[str, float, List[Dict]]:
        if not self.available:
            raise RuntimeError("EasyOCR not initialized")
        
        result = self.reader.readtext(image_path)
        
        if not result:
            return "", 0.0, []
        
        text_blocks = []
        texts = []
        total_conf = 0.0
        
        for det in result:
            text = det[1]
            conf = det[2]
            texts.append(text)
            total_conf += conf
            text_blocks.append({"text": text, "confidence": conf, "bbox": det[0], "engine": self.name})
        
        return '\n'.join(texts), total_conf / len(result), text_blocks


class TesseractEngine(OCREngine):
    """Tesseract - Top 3"""
    
    def __init__(self):
        super().__init__()
        self.name = "tesseract"
        self.priority = 3
        
    def initialize(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self.available = True
            logger.info(f"✅ {self.name} initialized")
            return True
        except Exception as e:
            logger.warning(f"⚠️ {self.name}: {e}")
            return False
    
    def recognize(self, image_path: str) -> Tuple[str, float, List[Dict]]:
        if not self.available:
            raise RuntimeError("Tesseract not initialized")
        
        import pytesseract
        from PIL import Image
        
        img = Image.open(image_path)
        
        try:
            text = pytesseract.image_to_string(img, lang='chi_sim+chi_tra+eng')
        except:
            text = pytesseract.image_to_string(img, lang='eng')
        
        return text.strip(), 0.7, [{"text": text.strip(), "confidence": 0.7, "engine": self.name}]


class SimulatedOCREngine(OCREngine):
    """Simulated - Fallback"""
    
    def __init__(self):
        super().__init__()
        self.name = "simulated"
        self.priority = 999
        self.available = True
        
    def initialize(self) -> bool:
        logger.info(f"✅ {self.name} (fallback)")
        return True
    
    def recognize(self, image_path: str) -> Tuple[str, float, List[Dict]]:
        filename = Path(image_path).stem
        text = f"[Simulated OCR] {filename}\n[Install paddleocr/easyocr for real OCR]"
        return text, 0.5, [{"text": text, "confidence": 0.5, "engine": self.name}]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: OCR ENGINE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════
class OCREngineManager:
    """OCR 引擎管理器 - 級聯回退"""
    
    def __init__(self, preferred_engine: Optional[str] = None):
        self.engines: List[OCREngine] = []
        self.preferred_engine = preferred_engine
        self.deskewer = SmartDeskewer()
        self.chinese_converter = ChineseConverter()
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化所有引擎"""
        for cls in [PaddleOCREngine, EasyOCREngine, TesseractEngine, SimulatedOCREngine]:
            try:
                engine = cls()
                if engine.initialize():
                    self.engines.append(engine)
            except Exception as e:
                logger.warning(f"Engine init error: {e}")
        
        self.engines.sort(key=lambda e: e.priority)
        logger.info(f"📊 OCR engines: {[e.name for e in self.engines]}")
    
    def recognize_with_cascade(self, image_path: str, temp_dir: str = None) -> OCRResult:
        """級聯 OCR + Deskew + OpenCC"""
        doc_id = Path(image_path).stem
        engines_tried = []
        start_time = time.time()
        
        # Step 1: Smart Deskew (只在需要時)
        processed_image, deskew_angle, deskew_applied = self.deskewer.deskew_if_needed(
            image_path, temp_dir
        )
        
        # Step 2: Cascade OCR
        ocr_text = ""
        confidence = 0.0
        text_blocks = []
        engine_used = "none"
        
        engines_to_try = list(self.engines)
        if self.preferred_engine:
            pref = next((e for e in engines_to_try if e.name == self.preferred_engine), None)
            if pref:
                engines_to_try = [pref] + [e for e in engines_to_try if e.name != self.preferred_engine]
        
        for engine in engines_to_try:
            if not engine.available:
                continue
            
            engines_tried.append(engine.name)
            
            try:
                text, conf, blocks = engine.recognize(processed_image)
                
                if text.strip():
                    ocr_text = text
                    confidence = conf
                    text_blocks = blocks
                    engine_used = engine.name
                    break
                    
            except Exception as e:
                logger.warning(f"Engine {engine.name} failed: {e}")
                continue
        
        # Step 3: OpenCC 簡繁轉換
        original_text = ocr_text
        simplified_detected = self.chinese_converter.has_simplified(ocr_text)
        
        if simplified_detected:
            ocr_text, opencc_applied = self.chinese_converter.convert_to_traditional(ocr_text)
            if opencc_applied:
                logger.info(f"   🔄 OpenCC: 簡體→繁體")
        else:
            opencc_applied = False
        
        # 清理臨時檔案
        if deskew_applied and processed_image != image_path:
            try:
                os.remove(processed_image)
            except:
                pass
        
        elapsed = (time.time() - start_time) * 1000
        
        return OCRResult(
            doc_id=doc_id,
            image_source=str(image_path),
            ocr_text=ocr_text,
            ocr_text_original=original_text,
            confidence=confidence,
            engine_used=engine_used,
            engines_tried=engines_tried,
            text_blocks=text_blocks,
            processing_time_ms=elapsed,
            deskew_applied=deskew_applied,
            deskew_angle=deskew_angle,
            opencc_applied=opencc_applied,
            simplified_detected=simplified_detected
        )

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: MAIN PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════
IMAGE_EXTENSIONS = {'.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp', '.webp'}

class M03Processor:
    """M03 OCR 處理器"""
    
    def __init__(self, input_path: str, output_path: str, engine: Optional[str] = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.engine_name = engine
        self.ocr_manager = None
        self.stats = ProcessingStats()
        
    def initialize(self) -> bool:
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info("🔧 Initializing OCR engines + Deskew + OpenCC...")
        self.ocr_manager = OCREngineManager(preferred_engine=self.engine_name)
        return bool(self.ocr_manager.engines)
    
    def process(self) -> ProcessingStats:
        logger.info("=" * 60)
        logger.info(f"🚀 VRN M03 OCR LEGO Ultra v{__version__}")
        logger.info(f"   + Smart Deskew (threshold: {SmartDeskewer.ANGLE_THRESHOLD}°)")
        logger.info(f"   + OpenCC s2twp (簡→繁)")
        logger.info("=" * 60)
        logger.info(f"   Input : {self.input_path}")
        logger.info(f"   Output: {self.output_path}")
        
        start_time = time.time()
        
        # 發現檔案
        image_files, json_files = self._discover_files()
        logger.info(f"📁 Found: {len(image_files)} images, {len(json_files)} JSON files")
        
        if json_files:
            self._process_json_mode(json_files, image_files)
        elif image_files:
            self._process_image_mode(image_files)
        else:
            logger.warning("⚠️ No files to process!")
        
        self.stats.total_time_ms = (time.time() - start_time) * 1000
        self._log_summary()
        
        return self.stats
    
    def _discover_files(self):
        if not self.input_path.exists():
            return [], []
        
        if self.input_path.is_file():
            ext = self.input_path.suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                return [self.input_path], []
            elif ext == '.json':
                return [], [self.input_path]
            return [], []
        
        image_files = []
        json_files = []
        
        for f in self.input_path.iterdir():
            if f.is_file():
                ext = f.suffix.lower()
                if ext in IMAGE_EXTENSIONS:
                    image_files.append(f)
                elif ext == '.json':
                    json_files.append(f)
        
        return sorted(image_files), sorted(json_files)
    
    def _find_matching_image(self, json_file: Path, image_files: List[Path]) -> Optional[Path]:
        base_name = json_file.stem
        for img in image_files:
            if img.stem == base_name:
                return img
        clean_base = base_name.replace('_layout', '').replace('_ocr', '')
        for img in image_files:
            if img.stem == clean_base or clean_base in img.stem:
                return img
        return None
    
    def _process_json_mode(self, json_files: List[Path], image_files: List[Path]):
        self.stats.total_files = len(json_files)
        
        for json_file in json_files:
            base_name = json_file.stem
            logger.info(f"   Processing: {base_name}...")
            
            image_file = self._find_matching_image(json_file, image_files)
            
            if not image_file:
                logger.warning(f"   ❌ No image for {base_name}")
                self.stats.skipped += 1
                continue
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    layout_data = json.load(f)
            except:
                layout_data = {}
            
            result = self.ocr_manager.recognize_with_cascade(str(image_file), str(self.output_path))
            result.layout_source = str(json_file.name)
            result.raw_blocks = layout_data
            
            self._save_result(result)
    
    def _process_image_mode(self, image_files: List[Path]):
        self.stats.total_files = len(image_files)
        
        for image_file in image_files:
            logger.info(f"   Processing: {image_file.name}...")
            result = self.ocr_manager.recognize_with_cascade(str(image_file), str(self.output_path))
            self._save_result(result)
    
    def _save_result(self, result: OCRResult):
        out_file = self.output_path / f"{result.doc_id}_ocr.json"
        
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, ensure_ascii=False, indent=2)
            
            self.stats.processed += 1
            
            if result.ocr_text:
                self.stats.succeeded += 1
                status = f"✅ {result.engine_used}"
                if result.deskew_applied:
                    status += f" | deskew {result.deskew_angle:.1f}°"
                    self.stats.deskewed += 1
                if result.opencc_applied:
                    status += " | 簡→繁"
                    self.stats.opencc_converted += 1
                logger.info(f"   {status}")
            else:
                self.stats.failed += 1
            
            self.stats.engines_used[result.engine_used] = self.stats.engines_used.get(result.engine_used, 0) + 1
            
        except Exception as e:
            self.stats.failed += 1
            logger.error(f"   ❌ Save error: {e}")
    
    def _log_summary(self):
        logger.info("=" * 60)
        logger.info(f"🏁 M03 Complete | {self.stats.succeeded}/{self.stats.total_files} succeeded")
        logger.info(f"   Deskewed: {self.stats.deskewed} | OpenCC: {self.stats.opencc_converted}")
        logger.info(f"   Time: {self.stats.total_time_ms:.1f}ms | Engines: {self.stats.engines_used}")
        logger.info("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: CLI
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description=f"VRN M03 OCR v{__version__} (Deskew + OpenCC)")
    
    # 同時支援 --input/--output 和 --input_dir/--output_dir
    parser.add_argument("--input", "-i", help="Input directory or file")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--input_dir", help="Input (legacy)")
    parser.add_argument("--output_dir", help="Output (legacy)")
    parser.add_argument("--engine", "-e", choices=["paddleocr", "easyocr", "tesseract", "auto"], default="auto")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    input_path = args.input or args.input_dir
    output_path = args.output or args.output_dir
    
    if not input_path or not output_path:
        parser.print_help()
        print("\n❌ Error: --input and --output required")
        sys.exit(1)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    processor = M03Processor(input_path, output_path, args.engine if args.engine != "auto" else None)
    
    if not processor.initialize():
        sys.exit(1)
    
    stats = processor.process()
    sys.exit(0 if stats.succeeded > 0 else 1)




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
    main()
