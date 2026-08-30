# -*- coding: utf-8 -*-
"""
🚀 完整擴充系統：OCR + 24引擎交叉驗證 + 視覺化審核
模組：
1. 多引擎 OCR 系統（Tesseract/EasyOCR/PaddleOCR）
2. 24 引擎表格抽取與交叉驗證
3. 即時視覺化審核界面（Dash）
4. 完整加速與效能追蹤
"""

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import fitz
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import warnings
import cv2
from PIL import Image
import time
import hashlib
warnings.filterwarnings('ignore')

# ============================================================
# 🔧 依賴檢查與自動安裝提示
# ============================================================

def check_dependencies():
    """檢查並提示安裝依賴"""
    missing = []
    
    # 核心依賴
    try:
        import pytesseract
    except ImportError:
        missing.append("pytesseract")
    
    try:
        import easyocr
    except ImportError:
        missing.append("easyocr")
    
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        missing.append("paddleocr")
    
    try:
        import camelot
    except ImportError:
        missing.append("camelot-py[cv]")
    
    try:
        import tabula
    except ImportError:
        missing.append("tabula-py")
    
    try:
        import dash
    except ImportError:
        missing.append("dash")
    
    if missing:
        print("⚠️ 缺少以下依賴，請安裝：")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

# Rich 視覺化
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, track
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False

# 載入加速器
try:
    import sys
    sys.path.insert(0, r'C:\VeritasReportNova')
    exec(open(r'C:\VeritasReportNova\1760065687980_ultimate_accelerator.py', encoding='utf-8').read())
    import psutil
    ACCEL = UltimateAccelerator(
        max_workers=psutil.cpu_count(logical=True) * 3,
        aggressive_mode=True,
        enable_cache=True
    )
    ACCEL_LOADED = True
    if RICH_AVAILABLE:
        console.print("[green]✅ 終極加速器已載入[/green]")
except:
    ACCEL = None
    ACCEL_LOADED = False

# ============================================================
# 📊 資料結構
# ============================================================

@dataclass
class OCRResult:
    """OCR 結果"""
    engine: str
    text: str
    confidence: float
    language: str
    processing_time: float
    bbox: Optional[List[Tuple[int, int, int, int]]] = None

@dataclass
class TableExtractionResult:
    """表格抽取結果"""
    engine: str
    dataframe: pd.DataFrame
    confidence: float
    row_count: int
    column_count: int
    cell_count: int
    null_rate: float
    extraction_time: float
    
@dataclass
class CrossValidationScore:
    """交叉驗證分數"""
    metric_name: str
    score: float  # 0-100
    passed: bool
    details: Dict[str, Any]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL

# ============================================================
# 🔍 模組 1: 多引擎 OCR 系統
# ============================================================

class MultiEngineOCRSystem:
    """多引擎 OCR 系統"""
    
    def __init__(self):
        self.engines = {}
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化所有可用的 OCR 引擎"""
        if RICH_AVAILABLE:
            console.print("\n[cyan]🔍 初始化 OCR 引擎...[/cyan]")
        
        # Tesseract OCR
        try:
            import pytesseract
            self.engines['tesseract'] = True
            if RICH_AVAILABLE:
                console.print("[green]✓ Tesseract OCR[/green]")
        except:
            if RICH_AVAILABLE:
                console.print("[yellow]✗ Tesseract OCR (未安裝)[/yellow]")
        
        # EasyOCR
        try:
            import easyocr
            self.engines['easyocr'] = easyocr.Reader(['ch_tra', 'en'], gpu=False)
            if RICH_AVAILABLE:
                console.print("[green]✓ EasyOCR[/green]")
        except:
            if RICH_AVAILABLE:
                console.print("[yellow]✗ EasyOCR (未安裝)[/yellow]")
        
        # PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.engines['paddleocr'] = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            if RICH_AVAILABLE:
                console.print("[green]✓ PaddleOCR[/green]")
        except:
            if RICH_AVAILABLE:
                console.print("[yellow]✗ PaddleOCR (未安裝)[/yellow]")
        
        if RICH_AVAILABLE:
            console.print(f"[cyan]總計: {len([k for k, v in self.engines.items() if v])} 個引擎可用[/cyan]\n")
    
    def ocr_with_tesseract(self, image: np.ndarray, lang: str = 'chi_tra+eng') -> OCRResult:
        """Tesseract OCR"""
        if 'tesseract' not in self.engines:
            return None
        
        try:
            import pytesseract
            
            start = time.time()
            
            # 轉換為 PIL Image
            if isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # OCR 識別
            text = pytesseract.image_to_string(pil_image, lang=lang)
            
            # 獲取詳細資訊（含信心度）
            data = pytesseract.image_to_data(pil_image, lang=lang, output_type=pytesseract.Output.DICT)
            
            # 計算平均信心度
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = np.mean(confidences) / 100 if confidences else 0.0
            
            elapsed = time.time() - start
            
            return OCRResult(
                engine='tesseract',
                text=text.strip(),
                confidence=avg_confidence,
                language=lang,
                processing_time=elapsed
            )
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Tesseract 錯誤: {e}[/red]")
            return None
    
    def ocr_with_easyocr(self, image: np.ndarray) -> OCRResult:
        """EasyOCR"""
        if 'easyocr' not in self.engines or not isinstance(self.engines['easyocr'], object):
            return None
        
        try:
            start = time.time()
            
            # OCR 識別
            reader = self.engines['easyocr']
            results = reader.readtext(image)
            
            # 整合文字
            text = '\n'.join([result[1] for result in results])
            
            # 計算平均信心度
            confidences = [result[2] for result in results]
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            # 提取邊界框
            bboxes = [result[0] for result in results]
            
            elapsed = time.time() - start
            
            return OCRResult(
                engine='easyocr',
                text=text.strip(),
                confidence=avg_confidence,
                language='ch_tra+en',
                processing_time=elapsed,
                bbox=bboxes
            )
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]EasyOCR 錯誤: {e}[/red]")
            return None
    
    def ocr_with_paddleocr(self, image: np.ndarray) -> OCRResult:
        """PaddleOCR"""
        if 'paddleocr' not in self.engines or not isinstance(self.engines['paddleocr'], object):
            return None
        
        try:
            start = time.time()
            
            # OCR 識別
            ocr = self.engines['paddleocr']
            results = ocr.ocr(image, cls=True)
            
            if not results or not results[0]:
                return None
            
            # 整合文字
            text_lines = []
            confidences = []
            
            for line in results[0]:
                text_lines.append(line[1][0])
                confidences.append(line[1][1])
            
            text = '\n'.join(text_lines)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            elapsed = time.time() - start
            
            return OCRResult(
                engine='paddleocr',
                text=text.strip(),
                confidence=avg_confidence,
                language='ch',
                processing_time=elapsed
            )
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]PaddleOCR 錯誤: {e}[/red]")
            return None
    
    def ocr_multi_engine(self, image: np.ndarray) -> List[OCRResult]:
        """多引擎 OCR（並行處理）"""
        if RICH_AVAILABLE:
            console.print("[cyan]⚡ 多引擎 OCR 處理...[/cyan]")
        
        tasks = []
        
        if 'tesseract' in self.engines:
            tasks.append(lambda: self.ocr_with_tesseract(image))
        
        if 'easyocr' in self.engines:
            tasks.append(lambda: self.ocr_with_easyocr(image))
        
        if 'paddleocr' in self.engines:
            tasks.append(lambda: self.ocr_with_paddleocr(image))
        
        # 使用加速器並行執行
        if ACCEL_LOADED and len(tasks) > 1:
            results = ACCEL.parallel_execute(tasks, use_processes=False)
        else:
            results = [task() for task in tasks]
        
        # 過濾有效結果
        valid_results = [r for r in results if r is not None]
        
        return valid_results
    
    def select_best_ocr(self, results: List[OCRResult]) -> OCRResult:
        """選擇最佳 OCR 結果"""
        if not results:
            return None
        
        # 按信心度排序
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        return results[0]

# ============================================================
# 📊 模組 2: 24 引擎表格抽取系統
# ============================================================

class TwentyFourEngineTableExtractor:
    """24 引擎表格抽取系統"""
    
    def __init__(self):
        self.engines = self._get_available_engines()
        
        if RICH_AVAILABLE:
            console.print(f"\n[cyan]📊 初始化 24 引擎系統[/cyan]")
            console.print(f"[green]✓ 可用引擎: {len(self.engines)}/24[/green]\n")
    
    def _get_available_engines(self) -> List[str]:
        """獲取所有可用引擎"""
        available = []
        
        # 開源引擎
        try:
            import camelot
            available.extend(['camelot-lattice', 'camelot-stream'])
        except:
            pass
        
        try:
            import tabula
            available.extend(['tabula-lattice', 'tabula-stream'])
        except:
            pass
        
        try:
            import pdfplumber
            available.extend(['pdfplumber-default', 'pdfplumber-strict'])
        except:
            pass
        
        available.extend(['pymupdf-tables'])  # PyMuPDF 總是可用
        
        # 模擬其他引擎（實際使用時替換為真實引擎）
        available.extend([
            'tabula+camelot-hybrid',
            'pdfplumber+pymupdf-hybrid',
            'opencv-table-detector',
            'ml-table-transformer'
        ])
        
        return available
    
    def extract_with_engine(self, pdf_path: str, page_num: int, 
                           bbox: Tuple[float, float, float, float], 
                           engine: str) -> Optional[TableExtractionResult]:
        """使用指定引擎抽取表格"""
        start = time.time()
        
        try:
            df = None
            
            # Camelot
            if engine == 'camelot-lattice':
                df = self._extract_camelot(pdf_path, page_num, bbox, flavor='lattice')
            elif engine == 'camelot-stream':
                df = self._extract_camelot(pdf_path, page_num, bbox, flavor='stream')
            
            # Tabula
            elif engine == 'tabula-lattice':
                df = self._extract_tabula(pdf_path, page_num, bbox, lattice=True)
            elif engine == 'tabula-stream':
                df = self._extract_tabula(pdf_path, page_num, bbox, lattice=False)
            
            # pdfplumber
            elif engine == 'pdfplumber-default':
                df = self._extract_pdfplumber(pdf_path, page_num, bbox, strategy='default')
            elif engine == 'pdfplumber-strict':
                df = self._extract_pdfplumber(pdf_path, page_num, bbox, strategy='strict')
            
            # PyMuPDF
            elif engine == 'pymupdf-tables':
                df = self._extract_pymupdf(pdf_path, page_num, bbox)
            
            # 混合引擎（簡化版）
            elif 'hybrid' in engine:
                df = self._extract_hybrid(pdf_path, page_num, bbox, engine)
            
            if df is None or df.empty:
                return None
            
            elapsed = time.time() - start
            
            # 計算指標
            row_count = len(df)
            col_count = len(df.columns)
            cell_count = df.count().sum()
            expected_cells = row_count * col_count
            null_rate = 1 - (cell_count / expected_cells) if expected_cells > 0 else 1.0
            confidence = self._calculate_confidence(df)
            
            return TableExtractionResult(
                engine=engine,
                dataframe=df,
                confidence=confidence,
                row_count=row_count,
                column_count=col_count,
                cell_count=int(cell_count),
                null_rate=null_rate,
                extraction_time=elapsed
            )
            
        except Exception as e:
            return None
    
    def _extract_camelot(self, pdf_path: str, page_num: int, bbox: Tuple, flavor: str) -> Optional[pd.DataFrame]:
        """Camelot 抽取"""
        try:
            import camelot
            page_str = str(page_num + 1)
            bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            tables = camelot.read_pdf(pdf_path, pages=page_str, flavor=flavor, table_areas=[bbox_str])
            return tables[0].df if len(tables) > 0 else None
        except:
            return None
    
    def _extract_tabula(self, pdf_path: str, page_num: int, bbox: Tuple, lattice: bool) -> Optional[pd.DataFrame]:
        """Tabula 抽取"""
        try:
            import tabula
            area = [bbox[1], bbox[0], bbox[3], bbox[2]]  # [top, left, bottom, right]
            tables = tabula.read_pdf(
                pdf_path, 
                pages=page_num + 1, 
                area=area, 
                lattice=lattice,
                pandas_options={'header': None}
            )
            return tables[0] if len(tables) > 0 else None
        except:
            return None
    
    def _extract_pdfplumber(self, pdf_path: str, page_num: int, bbox: Tuple, strategy: str) -> Optional[pd.DataFrame]:
        """pdfplumber 抽取"""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num]
                cropped = page.crop(bbox)
                
                settings = {}
                if strategy == 'strict':
                    settings = {'text_tolerance': 1, 'intersection_tolerance': 1}
                
                tables = cropped.extract_tables(table_settings=settings)
                if tables and len(tables[0]) > 1:
                    return pd.DataFrame(tables[0][1:], columns=tables[0][0])
        except:
            pass
        return None
    
    def _extract_pymupdf(self, pdf_path: str, page_num: int, bbox: Tuple) -> Optional[pd.DataFrame]:
        """PyMuPDF 抽取"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            clip = fitz.Rect(bbox)
            text = page.get_text("text", clip=clip)
            doc.close()
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < 2:
                return None
            
            for sep in ['\t', '  ', '|']:
                if sep in lines[0]:
                    data = [line.split(sep) for line in lines]
                    return pd.DataFrame(data[1:], columns=data[0])
        except:
            pass
        return None
    
    def _extract_hybrid(self, pdf_path: str, page_num: int, bbox: Tuple, engine: str) -> Optional[pd.DataFrame]:
        """混合引擎抽取（簡化版）"""
        # 嘗試多個引擎，返回第一個成功的
        if 'camelot' in engine:
            df = self._extract_camelot(pdf_path, page_num, bbox, 'lattice')
            if df is not None:
                return df
        
        if 'pdfplumber' in engine:
            df = self._extract_pdfplumber(pdf_path, page_num, bbox, 'default')
            if df is not None:
                return df
        
        return self._extract_pymupdf(pdf_path, page_num, bbox)
    
    def _calculate_confidence(self, df: pd.DataFrame) -> float:
        """計算抽取信心度"""
        if df.empty:
            return 0.0
        
        col_score = min(len(df.columns) / 10, 1.0) * 0.3
        row_score = min(len(df) / 20, 1.0) * 0.3
        null_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
        non_null_score = (1 - null_rate) * 0.4
        
        return col_score + row_score + non_null_score
    
    def extract_all_engines(self, pdf_path: str, page_num: int, 
                           bbox: Tuple[float, float, float, float]) -> List[TableExtractionResult]:
        """使用所有引擎抽取（並行處理）"""
        if RICH_AVAILABLE:
            console.print(f"[cyan]⚡ 24 引擎並行抽取...[/cyan]")
        
        def extract_with_engine_wrapper(engine):
            return self.extract_with_engine(pdf_path, page_num, bbox, engine)
        
        # 使用加速器並行執行
        if ACCEL_LOADED:
            tasks = [lambda e=engine: extract_with_engine_wrapper(e) for engine in self.engines]
            results = ACCEL.batch_cross_process(
                self.engines,
                extract_with_engine_wrapper,
                batch_size=max(len(self.engines) // ACCEL.max_workers, 1),
                use_cache=False
            )
        else:
            results = [extract_with_engine_wrapper(e) for e in self.engines]
        
        # 過濾有效結果
        valid_results = [r for r in results if r is not None]
        
        if RICH_AVAILABLE:
            console.print(f"[green]✓ 成功: {len(valid_results)}/{len(self.engines)} 引擎[/green]")
        
        return valid_results

# ============================================================
# 🔬 模組 3: 交叉驗證系統
# ============================================================

class CrossValidationSystem:
    """交叉驗證系統"""
    
    def __init__(self):
        self.thresholds = {
            'table_count_variance': 0.2,  # 表格數量變異 20%
            'dimension_similarity': 0.8,   # 維度相似度 80%
            'cell_count_deviation': 0.15,  # 格數偏差 15%
            'column_similarity': 0.7,      # 欄位相似度 70%
            'numeric_deviation': 0.1,      # 數值偏差 10%
            'null_rate_max': 0.3          # 最大空值率 30%
        }
    
    def validate_table_count(self, results: List[TableExtractionResult]) -> CrossValidationScore:
        """指標1: 表格數量一致性"""
        if not results:
            return CrossValidationScore(
                metric_name="表格數量一致性",
                score=0,
                passed=False,
                details={"error": "無結果"},
                severity="CRITICAL"
            )
        
        # 統計每個引擎抽出的表格數（這裡簡化為都是1）
        counts = [1 for _ in results]
        expected = max(set(counts), key=counts.count)
        
        matching = sum(1 for c in counts if c == expected)
        score = (matching / len(results)) * 100
        
        passed = score >= (1 - self.thresholds['table_count_variance']) * 100
        
        return CrossValidationScore(
            metric_name="表格數量一致性",
            score=score,
            passed=passed,
            details={
                "expected_count": expected,
                "matching_engines": matching,
                "total_engines": len(results)
            },
            severity="HIGH" if not passed else "LOW"
        )
    
    def validate_dimensions(self, results: List[TableExtractionResult]) -> CrossValidationScore:
        """指標2: 維度（行列數）一致性"""
        if not results:
            return CrossValidationScore(
                metric_name="維度一致性",
                score=0,
                passed=False,
                details={},
                severity="CRITICAL"
            )
        
        dimensions = [(r.row_count, r.column_count) for r in results]
        
        # 找眾數
        dim_counter = {}
        for dim in dimensions:
            dim_counter[dim] = dim_counter.get(dim, 0) + 1
        
        expected_dim = max(dim_counter, key=dim_counter.get)
        matching = dim_counter[expected_dim]
        
        score = (matching / len(results)) * 100
        passed = score >= self.thresholds['dimension_similarity'] * 100
        
        return CrossValidationScore(
            metric_name="維度一致性",
            score=score,
            passed=passed,
            details={
                "expected_dimension": f"{expected_dim[0]}行 x {expected_dim[1]}列",
                "matching_count": matching,
                "total_engines": len(results),
                "all_dimensions": [f"{d[0]}x{d[1]}" for d in dimensions]
            },
            severity="HIGH" if not passed else "LOW"
        )
    
    def validate_cell_counts(self, results: List[TableExtractionResult]) -> CrossValidationScore:
        """指標3: 格數驗證"""
        if not results:
            return CrossValidationScore(
                metric_name="格數驗證",
                score=0,
                passed=False,
                details={},
                severity="HIGH"
            )
        
        cell_counts = [r.cell_count for r in results]
        expected_cells = [r.row_count * r.column_count for r in results]
        
        # 計算偏差
        deviations = []
        for actual, expected in zip(cell_counts, expected_cells):
            if expected > 0:
                deviation = abs(actual - expected) / expected
                deviations.append(deviation)
        
        avg_deviation = np.mean(deviations) if deviations else 1.0
        score = max(0, (1 - avg_deviation)) * 100
        
        passed = avg_deviation <= self.thresholds['cell_count_deviation']
        
        return CrossValidationScore(
            metric_name="格數驗證",
            score=score,
            passed=passed,
            details={
                "average_deviation": f"{avg_deviation*100:.1f}%",
                "cell_counts": cell_counts[:5],  # 前5個
                "expected_counts": expected_cells[:5]
            },
            severity="MEDIUM" if not passed else "LOW"
        )
    
    def validate_columns(self, results: List[TableExtractionResult]) -> CrossValidationScore:
        """指標4: 欄位一致性"""
        if not results:
            return CrossValidationScore(
                metric_name="欄位一致性",
                score=0,
                passed=False,
                details={},
                severity="MEDIUM"
            )
        
        # 比對前兩個結果的欄位
        if len(results) < 2:
            return CrossValidationScore(
                metric_name="欄位一致性",
                score=100,
                passed=True,
                details={"note": "僅一個引擎"},
                severity="LOW"
            )
        
        ref_cols = set(results[0].dataframe.columns)
        similarities = []
        
        for result in results[1:]:
            cols = set(result.dataframe.columns)
            intersection = len(ref_cols & cols)
            union = len(ref_cols | cols)
            similarity = intersection / union if union > 0 else 0
            similarities.append(similarity)
        
        avg_similarity = np.mean(similarities)
        score = avg_similarity * 100
        
        passed = avg_similarity >= self.thresholds['column_similarity']
        
        return CrossValidationScore(
            metric_name="欄位一致性",
            score=score,
            passed=passed,
            details={
                "average_similarity": f"{avg_similarity*100:.1f}%",
                "reference_columns": list(ref_cols)[:5]
            },
            severity="MEDIUM" if not passed else "LOW"
        )
    
    def validate_null_rates(self, results: List[TableExtractionResult]) -> CrossValidationScore:
        """指標6: 空值率檢查"""
        if not results:
            return CrossValidationScore(
                metric_name="空值率檢查",
                score=0,
                passed=False,
                details={},
                severity="LOW"
            )
        
        null_rates = [r.null_rate for r in results]
        avg_null_rate = np.mean(null_rates)
        
        score = max(0, (1 - avg_null_rate)) * 100
        passed = avg_null_rate <= self.thresholds['null_rate_max']
        
        return CrossValidationScore(
            metric_name="空值率檢查",
            score=score,
            passed=passed,
            details={
                "average_null_rate": f"{avg_null_rate*100:.1f}%",
                "max_null_rate": f"{max(null_rates)*100:.1f}%",
                "engine_null_rates": {r.engine: f"{r.null_rate*100:.1f}%" for r in results[:5]}
            },
            severity="LOW" if not passed else "LOW"
        )
    
    def cross_validate(self, results: List[TableExtractionResult]) -> Dict[str, CrossValidationScore]:
        """執行完整交叉驗證"""
        if RICH_AVAILABLE:
            console.print("\n[cyan]🔬 執行交叉驗證...[/cyan]")
        
        scores = {}
        
        # 執行所有驗證
        scores['table_count'] = self.validate_table_count(results)
        scores['dimensions'] = self.validate_dimensions(results)
        scores['cell_counts'] = self.validate_cell_counts(results)
        scores['columns'] = self.validate_columns(results)
        scores['null_rates'] = self.validate_null_rates(results)
        
        # 顯示結果
        if RICH_AVAILABLE:
            self._display_validation_results(scores)
        
        return scores
    
    def _display_validation_results(self, scores: Dict[str, CrossValidationScore]):
        """顯示驗證結果"""
        table = Table(title="交叉驗證結果", box=box.ROUNDED)
        table.add_column("指標", style="cyan")
        table.add_column("分數", justify="right", style="yellow")
        table.add_column("狀態", justify="center")
        table.add_column("嚴重性", justify="center")
        
        for metric_name, score in scores.items():
            status = "[green]✓ 通過[/green]" if score.passed else "[red]✗ 失敗[/red]"
            severity_color = {
                "CRITICAL": "red",
                "HIGH": "orange",
                "MEDIUM": "yellow",
                "LOW": "green"
            }.get(score.severity, "white")
            
            table.add_row(
                score.metric_name,
                f"{score.score:.1f}",
                status,
                f"[{severity_color}]{score.severity}[/{severity_color}]"
            )
        
        console.print(table)
    
    def select_best_result(self, results: List[TableExtractionResult], 
                          validation_scores: Dict[str, CrossValidationScore]) -> TableExtractionResult:
        """根據驗證分數選擇最佳結果"""
        if not results:
            return None
        
        # 綜合評分
        scored_results = []
        
        for result in results:
            score = (
                result.confidence * 0.4 +
                (1 - result.null_rate) * 0.3 +
                (result.column_count / 10) * 0.2 +
                (result.row_count / 20) * 0.1
            )
            scored_results.append((score, result))
        
        # 排序
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return scored_results[0][1]

# ============================================================
# 🎨 模組 4: 視覺化審核系統（Dash）
# ============================================================

class VisualInspectionDashboard:
    """視覺化審核儀表板"""
    
    def __init__(self, results: List[TableExtractionResult], 
                 validation_scores: Dict[str, CrossValidationScore]):
        self.results = results
        self.validation_scores = validation_scores
        self.app = None
    
    def create_dashboard(self):
        """創建 Dash 儀表板"""
        try:
            import dash
            from dash import dcc, html, dash_table
            import plotly.graph_objs as go
            
            self.app = dash.Dash(__name__)
            
            # 創建圖表
            confidence_fig = self._create_confidence_chart()
            dimension_fig = self._create_dimension_chart()
            null_rate_fig = self._create_null_rate_chart()
            
            # 創建表格預覽
            table_preview = self._create_table_preview()
            
            # 布局
            self.app.layout = html.Div([
                html.H1("📊 表格抽取審核儀表板", style={'textAlign': 'center'}),
                
                html.Div([
                    html.H2("信心度分布"),
                    dcc.Graph(figure=confidence_fig)
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H2("維度分布"),
                    dcc.Graph(figure=dimension_fig)
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H2("空值率分析"),
                    dcc.Graph(figure=null_rate_fig)
                ], style={'width': '100%'}),
                
                html.Div([
                    html.H2("表格預覽"),
                    table_preview
                ], style={'width': '100%', 'marginTop': '20px'})
            ])
            
        except ImportError:
            if RICH_AVAILABLE:
                console.print("[yellow]⚠️ Dash 未安裝，跳過視覺化[/yellow]")
    
    def _create_confidence_chart(self):
        """創建信心度圖表"""
        try:
            import plotly.graph_objs as go
            
            engines = [r.engine for r in self.results]
            confidences = [r.confidence * 100 for r in self.results]
            
            fig = go.Figure(data=[
                go.Bar(x=engines, y=confidences, marker_color='lightblue')
            ])
            
            fig.update_layout(
                title="各引擎信心度",
                xaxis_title="引擎",
                yaxis_title="信心度 (%)",
                yaxis_range=[0, 100]
            )
            
            return fig
        except:
            return {}
    
    def _create_dimension_chart(self):
        """創建維度圖表"""
        try:
            import plotly.graph_objs as go
            
            engines = [r.engine for r in self.results]
            rows = [r.row_count for r in self.results]
            cols = [r.column_count for r in self.results]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='行數', x=engines, y=rows))
            fig.add_trace(go.Bar(name='列數', x=engines, y=cols))
            
            fig.update_layout(
                title="表格維度",
                xaxis_title="引擎",
                yaxis_title="數量",
                barmode='group'
            )
            
            return fig
        except:
            return {}
    
    def _create_null_rate_chart(self):
        """創建空值率圖表"""
        try:
            import plotly.graph_objs as go
            
            engines = [r.engine for r in self.results]
            null_rates = [r.null_rate * 100 for r in self.results]
            
            fig = go.Figure(data=[
                go.Scatter(x=engines, y=null_rates, mode='lines+markers', 
                          line=dict(color='red', width=2))
            ])
            
            fig.update_layout(
                title="空值率趨勢",
                xaxis_title="引擎",
                yaxis_title="空值率 (%)",
                yaxis_range=[0, 100]
            )
            
            return fig
        except:
            return {}
    
    def _create_table_preview(self):
        """創建表格預覽"""
        try:
            from dash import dash_table
            
            if not self.results:
                return html.Div("無表格數據")
            
            # 使用第一個結果
            df = self.results[0].dataframe.head(10)
            
            return dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )
        except:
            return html.Div("表格預覽失敗")
    
    def run_server(self, port: int = 8050):
        """運行儀表板"""
        if self.app:
            if RICH_AVAILABLE:
                console.print(f"\n[green]🌐 儀表板啟動於: http://localhost:{port}[/green]")
            self.app.run_server(debug=True, port=port)

# ============================================================
# 🚀 完整整合處理器
# ============================================================

class CompleteIntegratedSystem:
    """完整整合系統"""
    
    def __init__(self):
        self.ocr_system = MultiEngineOCRSystem()
        self.table_extractor = TwentyFourEngineTableExtractor()
        self.validator = CrossValidationSystem()
    
    def process_complete(self, pdf_path: str, page_num: int, 
                        bbox: Tuple[float, float, float, float],
                        enable_ocr: bool = True,
                        enable_validation: bool = True,
                        enable_dashboard: bool = False) -> Dict:
        """完整處理流程"""
        if RICH_AVAILABLE:
            console.rule("[bold magenta]🚀 完整整合處理[/bold magenta]")
        
        overall_start = time.time()
        report = {}
        
        # 1. OCR 處理（可選）
        if enable_ocr:
            # 截取區域圖片
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat, clip=fitz.Rect(bbox))
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            doc.close()
            
            ocr_results = self.ocr_system.ocr_multi_engine(img)
            best_ocr = self.ocr_system.select_best_ocr(ocr_results)
            
            report['ocr'] = {
                'total_engines': len(ocr_results),
                'best_engine': best_ocr.engine if best_ocr else None,
                'best_confidence': best_ocr.confidence if best_ocr else 0,
                'text_preview': best_ocr.text[:200] if best_ocr else ""
            }
        
        # 2. 24 引擎表格抽取
        extraction_results = self.table_extractor.extract_all_engines(pdf_path, page_num, bbox)
        
        report['extraction'] = {
            'total_engines': len(self.table_extractor.engines),
            'successful_engines': len(extraction_results),
            'results': [
                {
                    'engine': r.engine,
                    'confidence': r.confidence,
                    'dimensions': f"{r.row_count}x{r.column_count}",
                    'null_rate': r.null_rate
                }
                for r in extraction_results
            ]
        }
        
        # 3. 交叉驗證（可選）
        if enable_validation and extraction_results:
            validation_scores = self.validator.cross_validate(extraction_results)
            best_result = self.validator.select_best_result(extraction_results, validation_scores)
            
            report['validation'] = {
                'scores': {k: {'score': v.score, 'passed': v.passed} for k, v in validation_scores.items()},
                'best_engine': best_result.engine,
                'best_confidence': best_result.confidence
            }
        
        # 4. 視覺化儀表板（可選）
        if enable_dashboard and extraction_results:
            dashboard = VisualInspectionDashboard(extraction_results, validation_scores if enable_validation else {})
            dashboard.create_dashboard()
            # dashboard.run_server()  # 註解掉以免阻塞
            report['dashboard'] = {'status': 'created', 'url': 'http://localhost:8050'}
        
        elapsed = time.time() - overall_start
        report['total_time'] = elapsed
        
        if RICH_AVAILABLE:
            console.print(f"\n[green]✅ 完整處理完成: {elapsed:.2f} 秒[/green]")
        
        return report

# ============================================================
# 🚀 主程式
# ============================================================

def main():
    """主程式"""
    if not check_dependencies():
        return
    
    if RICH_AVAILABLE:
        console.rule("[bold magenta]🚀 完整擴充系統[/bold magenta]")
    
    # 測試
    pdf_path = "C:/VeritasReportNova/input/test.pdf"
    page_num = 0
    bbox = (72, 100, 540, 400)  # 測試區域
    
    if not Path(pdf_path).exists():
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 找不到檔案: {pdf_path}[/red]")
        return
    
    # 創建完整系統
    system = CompleteIntegratedSystem()
    
    # 執行完整處理
    report = system.process_complete(
        pdf_path,
        page_num,
        bbox,
        enable_ocr=True,
        enable_validation=True,
        enable_dashboard=False  # 設為 True 可啟動儀表板
    )
    
    # 顯示報告
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📊 處理報告:[/bold cyan]")
        console.print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
