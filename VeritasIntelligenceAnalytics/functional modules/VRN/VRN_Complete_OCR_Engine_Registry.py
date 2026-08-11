#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                      ║
║   VRN_Complete_OCR_Engine_Registry.py v3.0                                                           ║
║   ══════════════════════════════════════════════════════════════════════════════════════════         ║
║                                                                                                      ║
║   🔧 完整 OCR 引擎註冊系統 - ALL TOOLS + LIMITS + BACKUP + AUTO TEST DEBUG VERIFY AUDIT              ║
║                                                                                                      ║
║   📦 FREE UNLIMITED (主要引擎 - 無限制):                                                             ║
║      1. Tesseract (pytesseract) - 95-98% 準確率                                                      ║
║      2. PaddleOCR - 95-98% 準確率, 多語言                                                            ║
║      3. EasyOCR - 95-97% 準確率, 輕量                                                                ║
║      4. DeepSeek-OCR - 97% 準確率, LLM-based (需 GPU)                                                ║
║      5. RapidOCR - 95-97% 準確率, ONNX                                                               ║
║      6. docTR - 96-98% 準確率, 端到端                                                                ║
║                                                                                                      ║
║   📦 LIMITED/PAID (備援引擎 - 記錄限制):                                                             ║
║      7. AWS Textract - 99.3% 準確率, 1000頁免費試用, $25-30/1000頁                                   ║
║      8. Google Cloud Vision - 98-99% 準確率, 1000頁/月免費, $1.50/1000單位                           ║
║      9. Azure AI Vision - 95-98% 準確率, 限額免費, $10/計算時                                        ║
║     10. ABBYY FineReader - 99.3% 準確率, 無免費版, $99-165/年                                        ║
║                                                                                                      ║
║   🎯 功能:                                                                                           ║
║      - 全部引擎註冊與狀態追蹤                                                                        ║
║      - 限制記錄與用量監控                                                                            ║
║      - 自動 Fallback 鏈 (免費優先)                                                                   ║
║      - 自動測試、除錯、驗證、稽核                                                                    ║
║      - 效能優化與準確率追蹤                                                                          ║
║      - TIFF 專用處理                                                                                 ║
║                                                                                                      ║
║   功能只增不減 - Features Only Increase, Never Decrease                                              ║
║                                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
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

import os
import sys
import re
import json
import time
import traceback
import unicodedata
import importlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import threading
import hashlib

# =============================================================================
# § 0. 基礎導入與檢查
# =============================================================================

# 核心庫 (必需)
try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

# =============================================================================
# § 1. 引擎狀態與限制定義
# =============================================================================

class EngineType(Enum):
    FREE_UNLIMITED = "FREE_UNLIMITED"      # 免費無限制
    FREE_LIMITED = "FREE_LIMITED"          # 免費有限制
    PAID_TRIAL = "PAID_TRIAL"              # 付費有試用
    PAID_ONLY = "PAID_ONLY"                # 純付費

class EngineStatus(Enum):
    AVAILABLE = "AVAILABLE"                # 可用
    UNAVAILABLE = "UNAVAILABLE"            # 不可用 (未安裝)
    LIMIT_REACHED = "LIMIT_REACHED"        # 達到限制
    ERROR = "ERROR"                        # 錯誤狀態
    DISABLED = "DISABLED"                  # 手動停用

@dataclass
class UsageLimit:
    """使用限制"""
    limit_type: str                        # "daily", "monthly", "total", "none"
    limit_value: int                       # 限制數量 (0 = 無限制)
    current_usage: int = 0                 # 當前用量
    reset_time: Optional[datetime] = None  # 重置時間
    cost_per_unit: float = 0.0             # 每單位成本 (USD)
    unit_name: str = "pages"               # 單位名稱
    
    def is_within_limit(self) -> bool:
        if self.limit_value == 0:  # 無限制
            return True
        return self.current_usage < self.limit_value
    
    def remaining(self) -> int:
        if self.limit_value == 0:
            return float('inf')
        return max(0, self.limit_value - self.current_usage)
    
    def increment(self, count: int = 1):
        self.current_usage += count
    
    def reset_if_needed(self):
        if self.reset_time and datetime.now() > self.reset_time:
            self.current_usage = 0
            if self.limit_type == "daily":
                self.reset_time = datetime.now() + timedelta(days=1)
            elif self.limit_type == "monthly":
                self.reset_time = datetime.now() + timedelta(days=30)

@dataclass
class EngineInfo:
    """引擎資訊"""
    engine_id: str
    name: str
    engine_type: EngineType
    import_name: str
    accuracy_range: Tuple[float, float]    # (min%, max%)
    supported_langs: List[str]
    tiff_support: bool
    gpu_required: bool
    description: str
    install_cmd: str
    usage_limit: UsageLimit
    status: EngineStatus = EngineStatus.UNAVAILABLE
    last_test_time: Optional[datetime] = None
    last_test_result: bool = False
    error_message: str = ""
    avg_speed_ms: float = 0.0              # 平均處理速度
    total_processed: int = 0               # 總處理數
    total_errors: int = 0                  # 總錯誤數

# =============================================================================
# § 2. 完整引擎註冊表
# =============================================================================

ENGINE_REGISTRY: Dict[str, EngineInfo] = {
    # ─────────────────────────────────────────────────────────────────────────
    # FREE UNLIMITED - 免費無限制引擎 (主要)
    # ─────────────────────────────────────────────────────────────────────────
    
    "tesseract": EngineInfo(
        engine_id="tesseract",
        name="Tesseract OCR",
        engine_type=EngineType.FREE_UNLIMITED,
        import_name="pytesseract",
        accuracy_range=(95.0, 98.0),
        supported_langs=["eng", "chi_tra", "chi_sim", "jpn", "kor"],
        tiff_support=True,
        gpu_required=False,
        description="Google 支持的開源 OCR，穩定可靠，支援 100+ 語言",
        install_cmd="pip install pytesseract && apt-get install tesseract-ocr",
        usage_limit=UsageLimit(limit_type="none", limit_value=0),
    ),
    
    "paddleocr": EngineInfo(
        engine_id="paddleocr",
        name="PaddleOCR",
        engine_type=EngineType.FREE_UNLIMITED,
        import_name="paddleocr",
        accuracy_range=(95.0, 98.0),
        supported_langs=["en", "ch", "chinese_cht", "japan", "korean"],
        tiff_support=True,
        gpu_required=False,
        description="百度開源 OCR，亞洲語言優秀，支援 190+ 語言",
        install_cmd="pip install paddleocr paddlepaddle",
        usage_limit=UsageLimit(limit_type="none", limit_value=0),
    ),
    
    "easyocr": EngineInfo(
        engine_id="easyocr",
        name="EasyOCR",
        engine_type=EngineType.FREE_UNLIMITED,
        import_name="easyocr",
        accuracy_range=(95.0, 97.0),
        supported_langs=["en", "ch_tra", "ch_sim", "ja", "ko"],
        tiff_support=True,
        gpu_required=False,
        description="輕量級開源 OCR，邊緣部署友好，支援 80+ 語言",
        install_cmd="pip install easyocr",
        usage_limit=UsageLimit(limit_type="none", limit_value=0),
    ),
    
    "rapidocr": EngineInfo(
        engine_id="rapidocr",
        name="RapidOCR",
        engine_type=EngineType.FREE_UNLIMITED,
        import_name="rapidocr_onnxruntime",
        accuracy_range=(95.0, 97.0),
        supported_langs=["en", "ch"],
        tiff_support=True,
        gpu_required=False,
        description="基於 ONNX 的快速 OCR，純 CPU 運行",
        install_cmd="pip install rapidocr-onnxruntime",
        usage_limit=UsageLimit(limit_type="none", limit_value=0),
    ),
    
    "doctr": EngineInfo(
        engine_id="doctr",
        name="docTR",
        engine_type=EngineType.FREE_UNLIMITED,
        import_name="doctr",
        accuracy_range=(96.0, 98.0),
        supported_langs=["en", "fr", "de"],
        tiff_support=True,
        gpu_required=False,
        description="Mindee 開源端到端 OCR，文件分析優秀",
        install_cmd="pip install python-doctr[torch]",
        usage_limit=UsageLimit(limit_type="none", limit_value=0),
    ),
    
    "surya": EngineInfo(
        engine_id="surya",
        name="Surya OCR",
        engine_type=EngineType.FREE_UNLIMITED,
        import_name="surya",
        accuracy_range=(95.0, 98.0),
        supported_langs=["en", "zh", "ja", "ko"],
        tiff_support=True,
        gpu_required=True,
        description="多語言 OCR，版面分析強，需 GPU",
        install_cmd="pip install surya-ocr",
        usage_limit=UsageLimit(limit_type="none", limit_value=0),
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # PAID WITH TRIAL - 付費有試用引擎 (備援)
    # ─────────────────────────────────────────────────────────────────────────
    
    "aws_textract": EngineInfo(
        engine_id="aws_textract",
        name="AWS Textract",
        engine_type=EngineType.PAID_TRIAL,
        import_name="boto3",
        accuracy_range=(98.0, 99.3),
        supported_langs=["en", "es", "de", "fr", "it", "pt"],
        tiff_support=True,
        gpu_required=False,
        description="AWS 企業級 OCR，表格/表單識別最強",
        install_cmd="pip install boto3",
        usage_limit=UsageLimit(
            limit_type="monthly",
            limit_value=1000,           # 3個月試用 1000頁
            cost_per_unit=0.025,        # $25/1000頁 = $0.025/頁
            unit_name="pages"
        ),
    ),
    
    "google_vision": EngineInfo(
        engine_id="google_vision",
        name="Google Cloud Vision",
        engine_type=EngineType.PAID_TRIAL,
        import_name="google.cloud.vision",
        accuracy_range=(98.0, 99.0),
        supported_langs=["en", "zh", "ja", "ko", "es", "fr", "de"],
        tiff_support=True,
        gpu_required=False,
        description="Google Cloud OCR，190+ 語言，多欄位佳",
        install_cmd="pip install google-cloud-vision",
        usage_limit=UsageLimit(
            limit_type="monthly",
            limit_value=1000,           # 每月 1000 單位免費
            cost_per_unit=0.0015,       # $1.50/1000 = $0.0015/單位
            unit_name="units"
        ),
    ),
    
    "azure_vision": EngineInfo(
        engine_id="azure_vision",
        name="Azure AI Vision",
        engine_type=EngineType.PAID_TRIAL,
        import_name="azure.cognitiveservices.vision.computervision",
        accuracy_range=(95.0, 98.0),
        supported_langs=["en", "zh", "ja", "ko"],
        tiff_support=True,
        gpu_required=False,
        description="Microsoft Azure OCR，整合 Microsoft 生態",
        install_cmd="pip install azure-cognitiveservices-vision-computervision",
        usage_limit=UsageLimit(
            limit_type="monthly",
            limit_value=5000,           # 免費額度
            cost_per_unit=0.01,         # $10/計算時
            unit_name="transactions"
        ),
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # PAID ONLY - 純付費引擎 (最後備援)
    # ─────────────────────────────────────────────────────────────────────────
    
    "abbyy": EngineInfo(
        engine_id="abbyy",
        name="ABBYY FineReader",
        engine_type=EngineType.PAID_ONLY,
        import_name="abbyy",
        accuracy_range=(99.0, 99.3),
        supported_langs=["en", "zh", "ja", "ko", "de", "fr"],
        tiff_support=True,
        gpu_required=False,
        description="企業級 OCR，201 語言，on-premises",
        install_cmd="需購買授權",
        usage_limit=UsageLimit(
            limit_type="total",
            limit_value=0,              # 無免費額度
            cost_per_unit=99.0,         # $99/年 Standard
            unit_name="license"
        ),
    ),
}

# =============================================================================
# § 3. Fallback 鏈定義 (免費優先)
# =============================================================================

FALLBACK_CHAIN = [
    # 第一優先: 免費無限制
    "tesseract",
    "easyocr",
    "rapidocr",
    "paddleocr",
    "doctr",
    "surya",
    # 第二優先: 付費有試用 (在限制內)
    "google_vision",
    "azure_vision",
    "aws_textract",
    # 最後: 純付費
    "abbyy",
]

# =============================================================================
# § 4. 抽象引擎介面
# =============================================================================

class OCREngineBase(ABC):
    """OCR 引擎抽象基類"""
    
    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.info = ENGINE_REGISTRY.get(engine_id)
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化引擎"""
        pass
    
    @abstractmethod
    def ocr(self, image: Image.Image, lang: str = "eng") -> Tuple[str, float]:
        """
        執行 OCR
        Returns: (text, confidence)
        """
        pass
    
    def ocr_tiff(self, tiff_path: str, page: int = 0, lang: str = "eng") -> Tuple[str, float]:
        """處理 TIFF 檔案"""
        if not PIL_OK:
            raise RuntimeError("Pillow not available")
        
        img = Image.open(tiff_path)
        if hasattr(img, 'n_frames') and img.n_frames > 1:
            img.seek(page)
        
        img = img.convert('RGB')
        return self.ocr(img, lang)
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        if not self.info:
            return False
        return self.info.status == EngineStatus.AVAILABLE
    
    def is_within_limit(self) -> bool:
        """檢查是否在限制內"""
        if not self.info:
            return False
        self.info.usage_limit.reset_if_needed()
        return self.info.usage_limit.is_within_limit()
    
    def record_usage(self, count: int = 1):
        """記錄使用量"""
        if self.info:
            self.info.usage_limit.increment(count)
            self.info.total_processed += count

# =============================================================================
# § 5. 具體引擎實作
# =============================================================================

class TesseractEngine(OCREngineBase):
    """Tesseract OCR 引擎"""
    
    def __init__(self):
        super().__init__("tesseract")
        self._pytesseract = None
    
    def initialize(self) -> bool:
        try:
            import pytesseract
            self._pytesseract = pytesseract
            # 測試可用性
            pytesseract.get_tesseract_version()
            self.info.status = EngineStatus.AVAILABLE
            self._initialized = True
            return True
        except Exception as e:
            self.info.status = EngineStatus.UNAVAILABLE
            self.info.error_message = str(e)
            return False
    
    def ocr(self, image: Image.Image, lang: str = "eng") -> Tuple[str, float]:
        if not self._initialized:
            self.initialize()
        
        if not self._pytesseract:
            raise RuntimeError("Tesseract not initialized")
        
        # 執行 OCR
        text = self._pytesseract.image_to_string(image, lang=lang)
        
        # 計算信心分數
        data = self._pytesseract.image_to_data(image, lang=lang, output_type=self._pytesseract.Output.DICT)
        confs = [float(c) for c in data['conf'] if c != '-1' and float(c) > 0]
        avg_conf = sum(confs) / len(confs) if confs else 0
        
        self.record_usage(1)
        return text, avg_conf


class EasyOCREngine(OCREngineBase):
    """EasyOCR 引擎"""
    
    def __init__(self):
        super().__init__("easyocr")
        self._reader = None
        self._current_langs = []
    
    def initialize(self) -> bool:
        try:
            import easyocr
            self._easyocr = easyocr
            self.info.status = EngineStatus.AVAILABLE
            self._initialized = True
            return True
        except Exception as e:
            self.info.status = EngineStatus.UNAVAILABLE
            self.info.error_message = str(e)
            return False
    
    def _get_reader(self, lang: str):
        # 映射語言代碼
        lang_map = {
            "eng": "en",
            "chi_tra": "ch_tra",
            "chi_sim": "ch_sim",
            "jpn": "ja",
            "kor": "ko",
        }
        mapped_lang = lang_map.get(lang, lang)
        
        if self._reader is None or mapped_lang not in self._current_langs:
            self._reader = self._easyocr.Reader([mapped_lang], gpu=False)
            self._current_langs = [mapped_lang]
        
        return self._reader
    
    def ocr(self, image: Image.Image, lang: str = "eng") -> Tuple[str, float]:
        if not self._initialized:
            self.initialize()
        
        reader = self._get_reader(lang)
        
        # 轉換為 numpy array
        import numpy as np
        img_array = np.array(image)
        
        results = reader.readtext(img_array)
        
        text = ' '.join([det[1] for det in results])
        avg_conf = sum(det[2] for det in results) / len(results) * 100 if results else 0
        
        self.record_usage(1)
        return text, avg_conf


class RapidOCREngine(OCREngineBase):
    """RapidOCR 引擎"""
    
    def __init__(self):
        super().__init__("rapidocr")
        self._ocr = None
    
    def initialize(self) -> bool:
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._ocr = RapidOCR()
            self.info.status = EngineStatus.AVAILABLE
            self._initialized = True
            return True
        except Exception as e:
            self.info.status = EngineStatus.UNAVAILABLE
            self.info.error_message = str(e)
            return False
    
    def ocr(self, image: Image.Image, lang: str = "eng") -> Tuple[str, float]:
        if not self._initialized:
            self.initialize()
        
        if not self._ocr:
            raise RuntimeError("RapidOCR not initialized")
        
        import numpy as np
        img_array = np.array(image)
        
        result, elapse = self._ocr(img_array)
        
        if result:
            text = '\n'.join([line[1] for line in result])
            avg_conf = sum(line[2] for line in result) / len(result) * 100 if result else 0
        else:
            text = ""
            avg_conf = 0
        
        self.record_usage(1)
        return text, avg_conf


class PaddleOCREngine(OCREngineBase):
    """PaddleOCR 引擎"""
    
    def __init__(self):
        super().__init__("paddleocr")
        self._ocr = None
        self._current_lang = None
    
    def initialize(self) -> bool:
        try:
            from paddleocr import PaddleOCR
            self._PaddleOCR = PaddleOCR
            self.info.status = EngineStatus.AVAILABLE
            self._initialized = True
            return True
        except Exception as e:
            self.info.status = EngineStatus.UNAVAILABLE
            self.info.error_message = str(e)
            return False
    
    def _get_ocr(self, lang: str):
        lang_map = {
            "eng": "en",
            "chi_tra": "chinese_cht",
            "chi_sim": "ch",
            "jpn": "japan",
            "kor": "korean",
        }
        mapped_lang = lang_map.get(lang, lang)
        
        if self._ocr is None or self._current_lang != mapped_lang:
            self._ocr = self.__via_paddle_build(lang=mapped_lang)
            self._current_lang = mapped_lang
        
        return self._ocr
    
    def ocr(self, image: Image.Image, lang: str = "eng") -> Tuple[str, float]:
        if not self._initialized:
            self.initialize()
        
        ocr = self._get_ocr(lang)
        
        import numpy as np
        img_array = np.array(image)
        
        result = ocr.ocr(img_array, cls=True)
        
        if result and result[0]:
            text = '\n'.join([line[1][0] for line in result[0]])
            avg_conf = sum(line[1][1] for line in result[0]) / len(result[0]) * 100
        else:
            text = ""
            avg_conf = 0
        
        self.record_usage(1)
        return text, avg_conf


class StubEngine(OCREngineBase):
    """Stub 引擎 (永不失敗的備援)"""
    
    def __init__(self):
        super().__init__("stub")
        self.info = EngineInfo(
            engine_id="stub",
            name="Stub OCR",
            engine_type=EngineType.FREE_UNLIMITED,
            import_name="",
            accuracy_range=(0.0, 0.0),
            supported_langs=["all"],
            tiff_support=True,
            gpu_required=False,
            description="Stub 引擎，永不失敗，返回空結果",
            install_cmd="",
            usage_limit=UsageLimit(limit_type="none", limit_value=0),
            status=EngineStatus.AVAILABLE,
        )
        self._initialized = True
    
    def initialize(self) -> bool:
        return True
    
    def ocr(self, image: Image.Image, lang: str = "eng") -> Tuple[str, float]:
        return "[STUB: No OCR result - all engines failed]", 0.0

# =============================================================================
# § 6. 引擎工廠
# =============================================================================

ENGINE_CLASSES = {
    "tesseract": TesseractEngine,
    "easyocr": EasyOCREngine,
    "rapidocr": RapidOCREngine,
    "paddleocr": PaddleOCREngine,
    "stub": StubEngine,
}

def create_engine(engine_id: str) -> Optional[OCREngineBase]:
    """創建引擎實例"""
    if engine_id in ENGINE_CLASSES:
        return ENGINE_CLASSES[engine_id]()
    return None

# =============================================================================
# § 7. 完整 OCR 管理器
# =============================================================================

class OCRManager:
    """OCR 引擎管理器"""
    
    def __init__(self):
        self.engines: Dict[str, OCREngineBase] = {}
        self.fallback_chain = FALLBACK_CHAIN.copy()
        self.usage_log: List[Dict] = []
        self.test_results: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def initialize_all(self) -> Dict[str, bool]:
        """初始化所有引擎"""
        results = {}
        
        for engine_id in ENGINE_REGISTRY.keys():
            engine = create_engine(engine_id)
            if engine:
                try:
                    success = engine.initialize()
                    results[engine_id] = success
                    self.engines[engine_id] = engine
                except Exception as e:
                    results[engine_id] = False
                    if engine.info:
                        engine.info.error_message = str(e)
        
        # 加入 Stub 引擎
        stub = StubEngine()
        self.engines["stub"] = stub
        results["stub"] = True
        
        return results
    
    def get_available_engines(self) -> List[str]:
        """獲取可用引擎列表"""
        available = []
        for engine_id, engine in self.engines.items():
            if engine.is_available() and engine.is_within_limit():
                available.append(engine_id)
        return available
    
    def ocr_with_fallback(self, tiff_path: str, page: int = 0, lang: str = "eng",
                          min_confidence: float = 80.0) -> Dict:
        """使用 Fallback 鏈執行 OCR"""
        result = {
            "file": tiff_path,
            "page": page,
            "lang": lang,
            "text": "",
            "confidence": 0.0,
            "engine_used": None,
            "engines_tried": [],
            "success": False,
            "elapsed_ms": 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        start_time = time.time()
        
        for engine_id in self.fallback_chain:
            engine = self.engines.get(engine_id)
            if not engine:
                continue
            
            if not engine.is_available():
                result["engines_tried"].append({
                    "engine": engine_id,
                    "status": "unavailable",
                    "reason": engine.info.error_message if engine.info else "Not initialized"
                })
                continue
            
            if not engine.is_within_limit():
                result["engines_tried"].append({
                    "engine": engine_id,
                    "status": "limit_reached",
                    "reason": f"Limit: {engine.info.usage_limit.current_usage}/{engine.info.usage_limit.limit_value}"
                })
                continue
            
            try:
                text, conf = engine.ocr_tiff(tiff_path, page, lang)
                
                result["engines_tried"].append({
                    "engine": engine_id,
                    "status": "success" if conf >= min_confidence else "low_confidence",
                    "confidence": conf,
                })
                
                if conf >= min_confidence:
                    result["text"] = text
                    result["confidence"] = conf
                    result["engine_used"] = engine_id
                    result["success"] = True
                    break
                elif conf > result["confidence"]:
                    # 保留最高信心結果
                    result["text"] = text
                    result["confidence"] = conf
                    result["engine_used"] = engine_id
                    
            except Exception as e:
                result["engines_tried"].append({
                    "engine": engine_id,
                    "status": "error",
                    "error": str(e),
                })
                if engine.info:
                    engine.info.total_errors += 1
        
        # 如果所有引擎都失敗，使用 Stub
        if not result["success"] and not result["text"]:
            stub = self.engines.get("stub")
            if stub:
                text, conf = stub.ocr_tiff(tiff_path, page, lang)
                result["text"] = text
                result["confidence"] = conf
                result["engine_used"] = "stub"
        
        result["elapsed_ms"] = (time.time() - start_time) * 1000
        
        # 記錄使用
        with self._lock:
            self.usage_log.append(result)
        
        return result
    
    # ─────────────────────────────────────────────────────────────────────────
    # 自動測試與驗證
    # ─────────────────────────────────────────────────────────────────────────
    
    def auto_test_all(self, test_image_path: Optional[str] = None) -> Dict:
        """自動測試所有引擎"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "engines": {},
            "summary": {
                "total": 0,
                "available": 0,
                "unavailable": 0,
                "passed": 0,
                "failed": 0,
            }
        }
        
        # 創建測試圖片
        if not test_image_path:
            test_image_path = self._create_test_image()
        
        for engine_id, engine in self.engines.items():
            results["summary"]["total"] += 1
            
            test_result = {
                "engine_id": engine_id,
                "name": engine.info.name if engine.info else engine_id,
                "type": engine.info.engine_type.value if engine.info else "UNKNOWN",
                "available": False,
                "within_limit": False,
                "test_passed": False,
                "confidence": 0.0,
                "speed_ms": 0.0,
                "error": "",
            }
            
            # 檢查可用性
            if engine.is_available():
                test_result["available"] = True
                results["summary"]["available"] += 1
            else:
                results["summary"]["unavailable"] += 1
                test_result["error"] = engine.info.error_message if engine.info else "Not initialized"
                results["engines"][engine_id] = test_result
                continue
            
            # 檢查限制
            test_result["within_limit"] = engine.is_within_limit()
            
            # 執行測試
            try:
                start = time.time()
                text, conf = engine.ocr_tiff(test_image_path)
                test_result["speed_ms"] = (time.time() - start) * 1000
                test_result["confidence"] = conf
                
                # 驗證結果
                if "2330" in text or "TSMC" in text or conf > 50:
                    test_result["test_passed"] = True
                    results["summary"]["passed"] += 1
                else:
                    test_result["test_passed"] = False
                    results["summary"]["failed"] += 1
                    test_result["error"] = f"Expected text not found (conf: {conf:.1f}%)"
                    
            except Exception as e:
                test_result["error"] = str(e)
                results["summary"]["failed"] += 1
            
            results["engines"][engine_id] = test_result
            
            # 更新引擎資訊
            if engine.info:
                engine.info.last_test_time = datetime.now()
                engine.info.last_test_result = test_result["test_passed"]
                engine.info.avg_speed_ms = test_result["speed_ms"]
        
        self.test_results = results
        return results
    
    def _create_test_image(self) -> str:
        """創建測試圖片"""
        if not PIL_OK:
            raise RuntimeError("Pillow not available")
        
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (800, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), "TSMC 2330", fill='black', font=font)
        draw.text((50, 100), "2025-01-15", fill='black', font=font)
        draw.text((50, 150), "Revenue: 625,000,000,000", fill='black', font=font)
        
        test_path = "/tmp/vrn_ocr_test.tiff"
        img.save(test_path, "TIFF", dpi=(300, 300))
        
        return test_path
    
    # ─────────────────────────────────────────────────────────────────────────
    # 稽核與報告
    # ─────────────────────────────────────────────────────────────────────────
    
    def audit_usage(self) -> Dict:
        """稽核使用量"""
        audit = {
            "timestamp": datetime.now().isoformat(),
            "engines": {},
            "total_processed": 0,
            "total_errors": 0,
            "cost_estimate": 0.0,
            "warnings": [],
        }
        
        for engine_id, engine in self.engines.items():
            if not engine.info:
                continue
            
            limit = engine.info.usage_limit
            limit.reset_if_needed()
            
            engine_audit = {
                "name": engine.info.name,
                "type": engine.info.engine_type.value,
                "limit_type": limit.limit_type,
                "limit_value": limit.limit_value,
                "current_usage": limit.current_usage,
                "remaining": limit.remaining(),
                "usage_percent": (limit.current_usage / limit.limit_value * 100) if limit.limit_value > 0 else 0,
                "cost": limit.current_usage * limit.cost_per_unit,
                "total_processed": engine.info.total_processed,
                "total_errors": engine.info.total_errors,
                "error_rate": (engine.info.total_errors / engine.info.total_processed * 100) if engine.info.total_processed > 0 else 0,
            }
            
            audit["engines"][engine_id] = engine_audit
            audit["total_processed"] += engine.info.total_processed
            audit["total_errors"] += engine.info.total_errors
            audit["cost_estimate"] += engine_audit["cost"]
            
            # 警告
            if limit.limit_value > 0:
                if engine_audit["usage_percent"] >= 90:
                    audit["warnings"].append(f"{engine.info.name}: 使用量達 {engine_audit['usage_percent']:.0f}%")
                elif engine_audit["usage_percent"] >= 75:
                    audit["warnings"].append(f"{engine.info.name}: 使用量達 {engine_audit['usage_percent']:.0f}%，接近限制")
        
        return audit
    
    def generate_status_report(self) -> str:
        """生成狀態報告"""
        lines = []
        
        lines.append("=" * 100)
        lines.append("  📊 VRN OCR 引擎狀態報告")
        lines.append("=" * 100)
        lines.append(f"  時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 引擎狀態表
        lines.append("┌─ 引擎狀態")
        lines.append(f"│  {'ID':<15} {'名稱':<20} {'類型':<15} {'狀態':<12} {'準確率':<12} {'限制':<20}")
        lines.append("│" + "-" * 95)
        
        for engine_id, engine in self.engines.items():
            if not engine.info:
                continue
            
            info = engine.info
            status_icon = {
                EngineStatus.AVAILABLE: "✅",
                EngineStatus.UNAVAILABLE: "❌",
                EngineStatus.LIMIT_REACHED: "⚠️",
                EngineStatus.ERROR: "💥",
                EngineStatus.DISABLED: "🚫",
            }.get(info.status, "?")
            
            acc = f"{info.accuracy_range[0]:.0f}-{info.accuracy_range[1]:.0f}%"
            
            if info.usage_limit.limit_value > 0:
                limit_str = f"{info.usage_limit.current_usage}/{info.usage_limit.limit_value}"
            else:
                limit_str = "無限制"
            
            lines.append(f"│  {engine_id:<15} {info.name:<20} {info.engine_type.value:<15} {status_icon:<12} {acc:<12} {limit_str:<20}")
        
        lines.append("")
        
        # 測試結果
        if self.test_results:
            summary = self.test_results.get("summary", {})
            lines.append("┌─ 測試結果")
            lines.append(f"│  總計: {summary.get('total', 0)} | ✅ 通過: {summary.get('passed', 0)} | ❌ 失敗: {summary.get('failed', 0)}")
            lines.append("")
        
        # 使用量稽核
        audit = self.audit_usage()
        lines.append("┌─ 使用量稽核")
        lines.append(f"│  總處理: {audit['total_processed']} | 總錯誤: {audit['total_errors']} | 預估成本: ${audit['cost_estimate']:.2f}")
        
        if audit["warnings"]:
            lines.append("│  ⚠️ 警告:")
            for w in audit["warnings"]:
                lines.append(f"│    - {w}")
        
        lines.append("")
        lines.append("=" * 100)
        
        return "\n".join(lines)

# =============================================================================
# § 8. 驗證規則
# =============================================================================

class OCRValidator:
    """OCR 結果驗證器"""
    
    # 正則規則
    PATTERNS = {
        "ticker_tw": r'(?<![0-9])(?!20[2-3][0-9])(?!2030)[1-9][0-9]{3}(?![0-9])',
        "date_iso": r'\d{4}-\d{2}-\d{2}',
        "date_slash": r'\d{4}/\d{1,2}/\d{1,2}',
        "date_roc": r'\d{2,3}/\d{1,2}/\d{1,2}',
        "quarter": r'(?:20\d{2}Q[1-4]|Q[1-4]\s*20\d{2}|[1-4]Q\d{2,4}|FY\d{2,4}[eE]?)',
        "percentage": r'-?\d+(?:\.\d+)?%',
        "number": r'-?\d{1,3}(?:,\d{3})*(?:\.\d+)?',
        "currency": r'(?:NT\$|US\$|\$|TWD|USD)\s*[\d,]+(?:\.\d+)?',
    }
    
    @classmethod
    def validate_text(cls, text: str) -> Dict:
        """驗證 OCR 文字"""
        result = {
            "valid": True,
            "findings": [],
            "extracted": {},
            "warnings": [],
        }
        
        # 正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 提取各類型
        for pattern_name, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result["extracted"][pattern_name] = matches
        
        # 驗證股票代號
        tickers = result["extracted"].get("ticker_tw", [])
        for ticker in tickers:
            # 排除年份
            if re.match(r'^20[2-3][0-9]$', ticker) or ticker == "2030":
                result["warnings"].append(f"股票代號 '{ticker}' 可能是年份誤判")
        
        # 驗證日期
        dates = result["extracted"].get("date_iso", []) + result["extracted"].get("date_slash", [])
        for date in dates:
            try:
                # 簡單格式檢查
                parts = re.split(r'[-/]', date)
                year = int(parts[0])
                if year < 1900 or year > 2100:
                    result["warnings"].append(f"日期 '{date}' 年份異常")
            except:
                pass
        
        return result
    
    @classmethod
    def compare_results(cls, text1: str, text2: str) -> Dict:
        """比較兩個 OCR 結果"""
        from difflib import SequenceMatcher
        
        # 正規化
        text1 = unicodedata.normalize('NFKC', text1).strip()
        text2 = unicodedata.normalize('NFKC', text2).strip()
        
        # 相似度
        similarity = SequenceMatcher(None, text1, text2).ratio() * 100
        
        # 提取比較
        v1 = cls.validate_text(text1)
        v2 = cls.validate_text(text2)
        
        return {
            "similarity": similarity,
            "consistent": similarity >= 95,
            "extracted_1": v1["extracted"],
            "extracted_2": v2["extracted"],
            "key_match": {
                "tickers": set(v1["extracted"].get("ticker_tw", [])) == set(v2["extracted"].get("ticker_tw", [])),
                "dates": set(v1["extracted"].get("date_iso", [])) == set(v2["extracted"].get("date_iso", [])),
            }
        }

# =============================================================================
# § 9. 主程式
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="VRN Complete OCR Engine Registry v3.0")
    parser.add_argument("--init", action="store_true", help="Initialize all engines")
    parser.add_argument("--test", action="store_true", help="Run auto tests")
    parser.add_argument("--audit", action="store_true", help="Audit usage")
    parser.add_argument("--status", action="store_true", help="Show status report")
    parser.add_argument("--ocr", type=str, help="Run OCR on TIFF file")
    parser.add_argument("--lang", type=str, default="eng", help="Language code")
    parser.add_argument("--json", type=str, help="Output JSON path")
    
    args = parser.parse_args()
    
    manager = OCRManager()
    
    # 初始化
    print("\n🔧 初始化 OCR 引擎...")
    init_results = manager.initialize_all()
    
    available = sum(1 for v in init_results.values() if v)
    print(f"   ✅ {available}/{len(init_results)} 引擎可用")
    
    if args.init:
        for engine_id, success in init_results.items():
            icon = "✅" if success else "❌"
            print(f"   {icon} {engine_id}")
    
    # 測試
    if args.test:
        print("\n🧪 執行自動測試...")
        test_results = manager.auto_test_all()
        
        summary = test_results["summary"]
        print(f"   總計: {summary['total']} | ✅ 通過: {summary['passed']} | ❌ 失敗: {summary['failed']}")
        
        for engine_id, result in test_results["engines"].items():
            icon = "✅" if result["test_passed"] else "❌"
            speed = f"{result['speed_ms']:.0f}ms" if result["speed_ms"] > 0 else "N/A"
            conf = f"{result['confidence']:.0f}%" if result["confidence"] > 0 else "N/A"
            print(f"   {icon} {engine_id:<15} [{speed:>6}] conf: {conf}")
    
    # 稽核
    if args.audit:
        print("\n📋 使用量稽核...")
        audit = manager.audit_usage()
        
        print(f"   總處理: {audit['total_processed']}")
        print(f"   預估成本: ${audit['cost_estimate']:.2f}")
        
        if audit["warnings"]:
            print("   ⚠️ 警告:")
            for w in audit["warnings"]:
                print(f"      - {w}")
    
    # 狀態報告
    if args.status:
        report = manager.generate_status_report()
        print(report)
    
    # OCR
    if args.ocr:
        print(f"\n🔍 OCR: {args.ocr}")
        result = manager.ocr_with_fallback(args.ocr, lang=args.lang)
        
        print(f"   引擎: {result['engine_used']}")
        print(f"   信心: {result['confidence']:.1f}%")
        print(f"   耗時: {result['elapsed_ms']:.0f}ms")
        print(f"   嘗試: {len(result['engines_tried'])} 引擎")
        print(f"\n   文字預覽:\n   {result['text'][:500]}...")
        
        if args.json:
            with open(args.json, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n   📄 JSON: {args.json}")
    
    # 預設: 初始化 + 測試 + 狀態
    if not any([args.init, args.test, args.audit, args.status, args.ocr]):
        print("\n🧪 執行完整測試...")
        test_results = manager.auto_test_all()
        print(manager.generate_status_report())




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
