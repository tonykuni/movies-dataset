# -*- coding: utf-8 -*-
"""
🚀 PDF 智能區塊切割與表格識別 - 終極加速版
特色：
1. 所有模組整合終極加速器
2. 每個流程記錄加速效果
3. 完整效能指標追蹤
4. Parquet 格式輸出（深度學習）
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
import pdfplumber
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import cv2
import time
import psutil
import warnings
warnings.filterwarnings('ignore')

# Rich 視覺化
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False

# ============================================================
# 🚀 載入終極加速器
# ============================================================

def load_ultimate_accelerator():
    """載入終極加速器"""
    import sys
    sys.path.insert(0, r'C:\VeritasReportNova')
    
    try:
        exec(open(r'C:\VeritasReportNova\1760065687980_ultimate_accelerator.py', encoding='utf-8').read())
        
        ACCEL = UltimateAccelerator(
            max_workers=psutil.cpu_count(logical=True) * 3,
            aggressive_mode=True,
            enable_cache=True
        )
        
        if RICH_AVAILABLE:
            console.print("[bold green]✅ 終極加速器已載入[/bold green]")
            console.print(f"[cyan]   • 工作執行緒: {ACCEL.max_workers}[/cyan]")
            console.print(f"[cyan]   • 激進模式: 已啟用[/cyan]")
            console.print(f"[cyan]   • 智能快取: 已啟用[/cyan]")
        
        return ACCEL, True
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[yellow]⚠️ 加速器載入失敗: {e}[/yellow]")
        return None, False

ACCEL, ACCEL_LOADED = load_ultimate_accelerator()

# ============================================================
# 📊 效能監控系統（完整版）
# ============================================================

class AcceleratedPerformanceMonitor:
    """加速效能監控器"""
    
    def __init__(self):
        self.metrics = []
        self.start_time = None
        self.module_name = None
        
    def start(self, module_name: str):
        """開始監控模組"""
        self.module_name = module_name
        self.start_time = time.time()
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]⚡ {module_name} 開始...[/bold cyan]")
    
    def end(self, success: bool, **extra_data):
        """結束監控並記錄"""
        if self.start_time is None:
            return None
        
        elapsed = time.time() - self.start_time
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        metric = {
            'module': self.module_name,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(elapsed, 3),
            'success': success,
            'cpu_percent': round(cpu, 2),
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'accelerator_used': ACCEL_LOADED,
            **extra_data
        }
        
        self.metrics.append(metric)
        
        # 顯示結果
        if RICH_AVAILABLE:
            status = "[green]✓[/green]" if success else "[red]✗[/red]"
            console.print(f"{status} {self.module_name} 完成: [yellow]{elapsed:.2f}秒[/yellow]")
            if extra_data:
                for key, value in extra_data.items():
                    console.print(f"   • {key}: {value}")
        
        return metric
    
    def save_metrics(self, output_dir: Path):
        """儲存效能指標"""
        if not self.metrics:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # DataFrame
        df = pd.DataFrame(self.metrics)
        
        # Parquet（深度學習格式）
        parquet_path = output_dir / f"performance_metrics_{timestamp}.parquet"
        df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
        
        # CSV（可讀格式）
        csv_path = output_dir / f"performance_metrics_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # JSON（詳細格式）
        json_path = output_dir / f"performance_metrics_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        
        if RICH_AVAILABLE:
            console.print(f"\n[green]💾 效能指標已儲存:[/green]")
            console.print(f"   • Parquet: {parquet_path.name}")
            console.print(f"   • CSV: {csv_path.name}")
            console.print(f"   • JSON: {json_path.name}")
        
        return str(parquet_path)
    
    def print_summary(self):
        """顯示效能摘要"""
        if not self.metrics:
            return
        
        df = pd.DataFrame(self.metrics)
        
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]📊 效能摘要[/bold cyan]\n")
            
            table = Table(box=box.ROUNDED)
            table.add_column("模組", style="cyan")
            table.add_column("時間(秒)", justify="right", style="yellow")
            table.add_column("CPU%", justify="right", style="green")
            table.add_column("加速器", justify="center", style="magenta")
            
            for _, row in df.iterrows():
                accel_icon = "⚡" if row['accelerator_used'] else "○"
                table.add_row(
                    row['module'],
                    f"{row['duration_seconds']:.2f}",
                    f"{row['cpu_percent']:.1f}",
                    accel_icon
                )
            
            console.print(table)
            
            # 統計
            total_time = df['duration_seconds'].sum()
            avg_cpu = df['cpu_percent'].mean()
            accel_count = df['accelerator_used'].sum()
            
            console.print(f"\n[bold green]總執行時間:[/bold green] {total_time:.2f} 秒")
            console.print(f"[bold green]平均 CPU:[/bold green] {avg_cpu:.1f}%")
            console.print(f"[bold green]加速模組數:[/bold green] {accel_count}/{len(df)}")

# 創建全局監控器
monitor = AcceleratedPerformanceMonitor()

# ============================================================
# 📊 資料結構
# ============================================================

@dataclass
class BlockRegion:
    """區塊區域"""
    block_id: int
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    height: float
    area: float
    
    def to_bbox(self) -> Tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

@dataclass
class TableStructure:
    """表格結構"""
    structure_id: str
    column_count: int
    row_count: int
    column_names: List[str]
    column_types: List[str]
    null_rate: float
    
    def get_signature(self) -> str:
        cols_str = "_".join(sorted(self.column_names))
        return f"{self.column_count}C_{self.row_count}R_{hash(cols_str) % 10000}"

@dataclass
class ExtractedTable:
    """抽取的表格"""
    table_id: str
    page_number: int
    block_id: int
    block_region: BlockRegion
    dataframe: pd.DataFrame
    structure: TableStructure
    extraction_method: str
    confidence: float

# ============================================================
# 🔍 區塊偵測引擎（加速版）
# ============================================================

class AcceleratedBlockDetector:
    """加速版區塊偵測器"""
    
    def __init__(self):
        self.MIN_BLOCK_WIDTH = 100
        self.MIN_BLOCK_HEIGHT = 50
        self.MIN_BLOCK_AREA = 5000
    
    def detect_blocks_batch(self, pages: List[fitz.Page]) -> List[List[BlockRegion]]:
        """批次偵測區塊（使用加速器）"""
        monitor.start("區塊偵測（批次）")
        
        def detect_single_page(page_tuple):
            page_num, page = page_tuple
            return self._detect_blocks_single(page, page_num)
        
        # 使用加速器批次處理
        if ACCEL_LOADED:
            page_tuples = list(enumerate(pages))
            all_blocks = ACCEL.batch_cross_process(
                page_tuples,
                detect_single_page,
                batch_size=max(len(pages) // ACCEL.max_workers, 1),
                use_cache=False
            )
        else:
            all_blocks = [detect_single_page((i, p)) for i, p in enumerate(pages)]
        
        total_blocks = sum(len(blocks) for blocks in all_blocks)
        monitor.end(True, total_blocks=total_blocks, pages=len(pages))
        
        return all_blocks
    
    def _detect_blocks_single(self, page: fitz.Page, page_num: int) -> List[BlockRegion]:
        """偵測單頁區塊"""
        # 方法1: 圖片分析
        blocks_image = self._detect_from_image(page, page_num)
        
        # 方法2: 版面結構
        blocks_layout = self._detect_from_layout(page, page_num)
        
        # 合併去重
        all_blocks = blocks_image + blocks_layout
        unique_blocks = self._merge_overlapping_blocks(all_blocks)
        
        return unique_blocks
    
    def _detect_from_image(self, page: fitz.Page, page_num: int) -> List[BlockRegion]:
        """從圖片偵測區塊"""
        try:
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.samples
            
            img = np.frombuffer(img_data, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            
            # 找輪廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            blocks = []
            page_rect = page.rect
            scale_x = page_rect.width / pix.width
            scale_y = page_rect.height / pix.height
            
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                
                x0 = x * scale_x
                y0 = y * scale_y
                x1 = (x + w) * scale_x
                y1 = (y + h) * scale_y
                
                width = x1 - x0
                height = y1 - y0
                area = width * height
                
                if (width >= self.MIN_BLOCK_WIDTH and 
                    height >= self.MIN_BLOCK_HEIGHT and 
                    area >= self.MIN_BLOCK_AREA):
                    
                    blocks.append(BlockRegion(
                        block_id=i,
                        page_number=page_num,
                        x0=x0, y0=y0, x1=x1, y1=y1,
                        width=width, height=height, area=area
                    ))
            
            return blocks
        except:
            return []
    
    def _detect_from_layout(self, page: fitz.Page, page_num: int) -> List[BlockRegion]:
        """從版面偵測區塊"""
        try:
            blocks = []
            text_blocks = page.get_text("dict")["blocks"]
            
            for i, block in enumerate(text_blocks):
                if "bbox" in block:
                    x0, y0, x1, y1 = block["bbox"]
                    width = x1 - x0
                    height = y1 - y0
                    area = width * height
                    
                    if (width >= self.MIN_BLOCK_WIDTH and 
                        height >= self.MIN_BLOCK_HEIGHT and 
                        area >= self.MIN_BLOCK_AREA):
                        
                        blocks.append(BlockRegion(
                            block_id=i,
                            page_number=page_num,
                            x0=x0, y0=y0, x1=x1, y1=y1,
                            width=width, height=height, area=area
                        ))
            
            return blocks
        except:
            return []
    
    def _merge_overlapping_blocks(self, blocks: List[BlockRegion]) -> List[BlockRegion]:
        """合併重疊區塊"""
        if not blocks:
            return []
        
        blocks = sorted(blocks, key=lambda b: b.area, reverse=True)
        merged = []
        used = set()
        
        for i, block1 in enumerate(blocks):
            if i in used:
                continue
            
            overlapping = [block1]
            for j, block2 in enumerate(blocks[i+1:], start=i+1):
                if j in used:
                    continue
                
                iou = self._calculate_iou(block1, block2)
                if iou > 0.5:
                    overlapping.append(block2)
                    used.add(j)
            
            if len(overlapping) == 1:
                merged.append(block1)
            else:
                merged_block = self._merge_blocks(overlapping)
                merged.append(merged_block)
        
        for idx, block in enumerate(merged):
            block.block_id = idx
        
        return merged
    
    def _calculate_iou(self, b1: BlockRegion, b2: BlockRegion) -> float:
        """計算 IoU"""
        x_overlap = max(0, min(b1.x1, b2.x1) - max(b1.x0, b2.x0))
        y_overlap = max(0, min(b1.y1, b2.y1) - max(b1.y0, b2.y0))
        
        intersection = x_overlap * y_overlap
        union = b1.area + b2.area - intersection
        
        return intersection / union if union > 0 else 0
    
    def _merge_blocks(self, blocks: List[BlockRegion]) -> BlockRegion:
        """合併多個區塊"""
        x0 = min(b.x0 for b in blocks)
        y0 = min(b.y0 for b in blocks)
        x1 = max(b.x1 for b in blocks)
        y1 = max(b.y1 for b in blocks)
        
        return BlockRegion(
            block_id=blocks[0].block_id,
            page_number=blocks[0].page_number,
            x0=x0, y0=y0, x1=x1, y1=y1,
            width=x1 - x0,
            height=y1 - y0,
            area=(x1 - x0) * (y1 - y0)
        )

# ============================================================
# 📊 表格抽取引擎（加速版）
# ============================================================

class AcceleratedTableExtractor:
    """加速版表格抽取器"""
    
    def extract_tables_batch(self, pdf_path: str, blocks_by_page: List[List[BlockRegion]]) -> List[ExtractedTable]:
        """批次抽取表格（使用加速器）"""
        monitor.start("表格抽取（批次）")
        
        # 準備任務列表
        tasks = []
        for page_num, blocks in enumerate(blocks_by_page):
            for block in blocks:
                tasks.append((pdf_path, page_num, block))
        
        def extract_single(task):
            pdf_path, page_num, block = task
            return self._extract_single_table(pdf_path, page_num, block)
        
        # 使用加速器批次處理
        if ACCEL_LOADED:
            results = ACCEL.batch_cross_process(
                tasks,
                extract_single,
                batch_size=max(len(tasks) // (ACCEL.max_workers * 2), 1),
                use_cache=False
            )
        else:
            results = [extract_single(task) for task in tasks]
        
        # 過濾有效結果
        valid_tables = [r for r in results if r is not None]
        
        monitor.end(True, total_tasks=len(tasks), valid_tables=len(valid_tables))
        
        return valid_tables
    
    def _extract_single_table(self, pdf_path: str, page_num: int, block: BlockRegion) -> Optional[ExtractedTable]:
        """抽取單一表格"""
        # 嘗試 pdfplumber
        df = self._extract_with_pdfplumber(pdf_path, page_num, block)
        method = 'pdfplumber'
        
        # 如果失敗，嘗試其他方法
        if df is None or df.empty:
            df = self._extract_with_pymupdf(pdf_path, page_num, block)
            method = 'pymupdf'
        
        if df is None or df.empty:
            return None
        
        # 計算信心度
        confidence = self._calculate_confidence(df)
        
        # 分析結構
        structure = self._analyze_structure(df)
        
        table = ExtractedTable(
            table_id=f"P{page_num+1}_B{block.block_id}",
            page_number=page_num + 1,
            block_id=block.block_id,
            block_region=block,
            dataframe=df,
            structure=structure,
            extraction_method=method,
            confidence=confidence
        )
        
        return table
    
    def _extract_with_pdfplumber(self, pdf_path: str, page_num: int, block: BlockRegion) -> Optional[pd.DataFrame]:
        """使用 pdfplumber 抽取"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num]
                bbox = block.to_bbox()
                cropped = page.crop(bbox)
                tables = cropped.extract_tables()
                
                if tables and len(tables[0]) > 1:
                    df = pd.DataFrame(tables[0][1:], columns=tables[0][0])
                    return df
        except:
            pass
        return None
    
    def _extract_with_pymupdf(self, pdf_path: str, page_num: int, block: BlockRegion) -> Optional[pd.DataFrame]:
        """使用 PyMuPDF 抽取"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            clip = fitz.Rect(block.to_bbox())
            text = page.get_text("text", clip=clip)
            doc.close()
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None
            
            # 嘗試分隔
            for sep in ['\t', '  ', '|']:
                if sep in lines[0]:
                    data = [line.split(sep) for line in lines]
                    df = pd.DataFrame(data[1:], columns=data[0])
                    return df
        except:
            pass
        return None
    
    def _calculate_confidence(self, df: pd.DataFrame) -> float:
        """計算信心度"""
        if df.empty:
            return 0.0
        
        col_score = min(len(df.columns) / 10, 1.0) * 0.3
        row_score = min(len(df) / 20, 1.0) * 0.3
        
        null_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
        non_null_score = (1 - null_rate) * 0.4
        
        return col_score + row_score + non_null_score
    
    def _analyze_structure(self, df: pd.DataFrame) -> TableStructure:
        """分析表格結構"""
        if df.empty:
            return TableStructure(
                structure_id="EMPTY",
                column_count=0,
                row_count=0,
                column_names=[],
                column_types=[],
                null_rate=1.0
            )
        
        column_types = [str(dtype) for dtype in df.dtypes]
        null_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
        
        structure = TableStructure(
            structure_id="",
            column_count=len(df.columns),
            row_count=len(df),
            column_names=df.columns.tolist(),
            column_types=column_types,
            null_rate=float(null_rate)
        )
        
        structure.structure_id = structure.get_signature()
        return structure

# ============================================================
# 🛠️ 表格修復引擎（加速版）
# ============================================================

class AcceleratedTableRepairer:
    """加速版表格修復器"""
    
    def repair_tables_batch(self, tables: List[ExtractedTable]) -> List[ExtractedTable]:
        """批次修復表格（使用加速器）"""
        monitor.start("表格修復（批次）")
        
        def repair_single(table):
            df_repaired = self._repair_dataframe(table.dataframe)
            table.dataframe = df_repaired
            table.structure = self._reanalyze_structure(df_repaired, table.structure.structure_id)
            return table
        
        # 使用加速器批次處理
        if ACCEL_LOADED:
            repaired_tables = ACCEL.batch_cross_process(
                tables,
                repair_single,
                batch_size=max(len(tables) // ACCEL.max_workers, 1),
                use_cache=False
            )
        else:
            repaired_tables = [repair_single(t) for t in tables]
        
        monitor.end(True, repaired_count=len(repaired_tables))
        
        return repaired_tables
    
    def _repair_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """修復 DataFrame"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 1. 清理欄位名
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # 2. 移除全空行列
        df = df.dropna(how='all', axis=0)
        df = df.dropna(how='all', axis=1)
        
        # 3. 填補空值
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna(method='ffill')
        df = df.fillna('N/A')
        
        # 4. 標準化類型
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        
        return df
    
    def _clean_column_name(self, col: str) -> str:
        """清理欄位名"""
        col = str(col).strip()
        col = col.replace('\n', ' ').replace('\r', ' ')
        col = ' '.join(col.split())
        return col if col else 'Unnamed'
    
    def _reanalyze_structure(self, df: pd.DataFrame, old_id: str) -> TableStructure:
        """重新分析結構"""
        if df.empty:
            return TableStructure(
                structure_id=old_id,
                column_count=0,
                row_count=0,
                column_names=[],
                column_types=[],
                null_rate=1.0
            )
        
        column_types = [str(dtype) for dtype in df.dtypes]
        null_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
        
        structure = TableStructure(
            structure_id=old_id,
            column_count=len(df.columns),
            row_count=len(df),
            column_names=df.columns.tolist(),
            column_types=column_types,
            null_rate=float(null_rate)
        )
        
        return structure

# ============================================================
# 🗂️ 表格分群引擎（加速版）
# ============================================================

class AcceleratedTableClusterer:
    """加速版表格分群器"""
    
    def cluster_tables(self, tables: List[ExtractedTable]) -> Dict[str, List[ExtractedTable]]:
        """分群表格"""
        monitor.start("表格分群")
        
        clusters = {}
        
        for table in tables:
            sig = table.structure.get_signature()
            
            if sig not in clusters:
                clusters[sig] = []
            
            clusters[sig].append(table)
        
        monitor.end(True, total_tables=len(tables), clusters=len(clusters))
        
        return clusters

# ============================================================
# 🎯 主處理器（完整加速版）
# ============================================================

class UltimateAcceleratedPDFProcessor:
    """終極加速 PDF 處理器"""
    
    def __init__(self):
        self.detector = AcceleratedBlockDetector()
        self.extractor = AcceleratedTableExtractor()
        self.repairer = AcceleratedTableRepairer()
        self.clusterer = AcceleratedTableClusterer()
        
        self.output_dir = Path("output_accelerated")
        self.output_dir.mkdir(exist_ok=True)
        
        (self.output_dir / "blocks").mkdir(exist_ok=True)
        (self.output_dir / "tables").mkdir(exist_ok=True)
        (self.output_dir / "clusters").mkdir(exist_ok=True)
        (self.output_dir / "metrics").mkdir(exist_ok=True)
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """處理 PDF（完整加速流程）"""
        if RICH_AVAILABLE:
            console.rule(f"[bold cyan]📄 {Path(pdf_path).name}[/bold cyan]")
        
        overall_start = time.time()
        
        # ============================================================
        # 步驟1: 載入 PDF
        # ============================================================
        monitor.start("PDF 載入")
        doc = fitz.open(pdf_path)
        pages = [doc[i] for i in range(len(doc))]
        monitor.end(True, total_pages=len(pages))
        
        # ============================================================
        # 步驟2: 批次偵測區塊（加速）
        # ============================================================
        all_blocks = self.detector.detect_blocks_batch(pages)
        
        # ============================================================
        # 步驟3: 批次抽取表格（加速）
        # ============================================================
        all_tables = self.extractor.extract_tables_batch(pdf_path, all_blocks)
        
        doc.close()
        
        # ============================================================
        # 步驟4: 批次修復表格（加速）
        # ============================================================
        if all_tables:
            all_tables = self.repairer.repair_tables_batch(all_tables)
        
        # ============================================================
        # 步驟5: 分群表格（加速）
        # ============================================================
        clusters = self.clusterer.cluster_tables(all_tables)
        
        # ============================================================
        # 步驟6: 儲存結果
        # ============================================================
        monitor.start("結果輸出")
        self._save_results(pdf_path, all_blocks, all_tables, clusters)
        monitor.end(True)
        
        # ============================================================
        # 步驟7: 儲存效能指標
        # ============================================================
        metrics_path = monitor.save_metrics(self.output_dir / "metrics")
        
        # 生成報告
        overall_time = time.time() - overall_start
        report = self._generate_report(pdf_path, all_blocks, all_tables, clusters, overall_time)
        
        # 顯示摘要
        monitor.print_summary()
        
        return report
    
    def _save_results(self, pdf_path: str, blocks: List[List[BlockRegion]], 
                     tables: List[ExtractedTable], clusters: Dict):
        """儲存結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = Path(pdf_path).stem
        
        # 1. 儲存所有表格（CSV）
        for table in tables:
            filename = f"{pdf_name}_{table.table_id}_{timestamp}.csv"
            filepath = self.output_dir / "tables" / filename
            table.dataframe.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        # 2. 按群組儲存
        for cluster_id, cluster_tables in clusters.items():
            cluster_dir = self.output_dir / "clusters" / cluster_id
            cluster_dir.mkdir(parents=True, exist_ok=True)
            
            for table in cluster_tables:
                filename = f"{pdf_name}_{table.table_id}.csv"
                filepath = cluster_dir / filename
                table.dataframe.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        # 3. 儲存元數據（Parquet + JSON）
        flat_blocks = [block for page_blocks in blocks for block in page_blocks]
        
        metadata = {
            'pdf_name': pdf_name,
            'timestamp': timestamp,
            'accelerator_used': ACCEL_LOADED,
            'summary': {
                'total_blocks': len(flat_blocks),
                'total_tables': len(tables),
                'total_clusters': len(clusters)
            },
            'clusters': {
                cid: {
                    'count': len(ctables),
                    'avg_confidence': float(np.mean([t.confidence for t in ctables]))
                }
                for cid, ctables in clusters.items()
            }
        }
        
        # JSON
        json_path = self.output_dir / f"{pdf_name}_metadata_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Parquet
        if tables:
            table_data = []
            for table in tables:
                table_data.append({
                    'table_id': table.table_id,
                    'page': table.page_number,
                    'block_id': table.block_id,
                    'columns': table.structure.column_count,
                    'rows': table.structure.row_count,
                    'confidence': table.confidence,
                    'method': table.extraction_method,
                    'cluster': table.structure.structure_id
                })
            
            df_meta = pd.DataFrame(table_data)
            parquet_path = self.output_dir / f"{pdf_name}_tables_{timestamp}.parquet"
            df_meta.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    
    def _generate_report(self, pdf_path: str, blocks: List[List[BlockRegion]],
                        tables: List[ExtractedTable], clusters: Dict, total_time: float) -> Dict:
        """生成報告"""
        flat_blocks = [block for page_blocks in blocks for block in page_blocks]
        
        report = {
            'pdf_file': Path(pdf_path).name,
            'processing_time': datetime.now().isoformat(),
            'total_duration_seconds': round(total_time, 2),
            'accelerator_enabled': ACCEL_LOADED,
            'summary': {
                'total_blocks': len(flat_blocks),
                'total_tables': len(tables),
                'total_clusters': len(clusters),
                'avg_confidence': float(np.mean([t.confidence for t in tables])) if tables else 0
            }
        }
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold green]✅ 處理完成！[/bold green]")
            console.print(f"[cyan]總時間: {total_time:.2f} 秒[/cyan]")
            console.print(f"[cyan]偵測區塊: {len(flat_blocks)}[/cyan]")
            console.print(f"[cyan]抽取表格: {len(tables)}[/cyan]")
            console.print(f"[cyan]表格分群: {len(clusters)}[/cyan]")
        
        return report

# ============================================================
# 🚀 主程式
# ============================================================

def main():
    """主程式"""
    if RICH_AVAILABLE:
        console.rule("[bold magenta]🚀 終極加速 PDF 處理系統[/bold magenta]")
    else:
        print("="*70)
        print("🚀 終極加速 PDF 處理系統")
        print("="*70)
    
    # 測試檔案
    pdf_path = "C:/VeritasReportNova/input/test.pdf"
    
    if not Path(pdf_path).exists():
        if RICH_AVAILABLE:
            console.print(f"\n[red]❌ 找不到檔案: {pdf_path}[/red]")
        return
    
    # 創建處理器
    processor = UltimateAcceleratedPDFProcessor()
    
    # 處理 PDF
    report = processor.process_pdf(pdf_path)
    
    if RICH_AVAILABLE:
        console.print(f"\n[bold green]📁 輸出目錄:[/bold green] {processor.output_dir}")

if __name__ == "__main__":
    main()
