"""
🧠 PDF 表格並行提取與修復系統 - 完整版
適合初學者使用，功能強大且模組化

安裝需求:
pip install pdfplumber camelot-py tabula-py pandas openpyxl pytesseract Pillow scikit-learn fuzzywuzzy python-Levenshtein ocrmypdf layoutparser torch torchvision pdf2image

使用方法:
python pdf_extractor.py --input "your_file.pdf" --output "results"
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

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import warnings

warnings.filterwarnings('ignore')

# ==================== 導入所有需要的工具 ====================
import pdfplumber
import pandas as pd
import numpy as np
from PIL import Image
from fuzzywuzzy import fuzz
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import pytesseract

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 數據結構定義 ====================
@dataclass
class TableBlock:
    """表格區塊信息"""
    page_num: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    block_type: str
    confidence: float = 0.0


@dataclass
class ExtractedTable:
    """提取的表格數據"""
    data: pd.DataFrame
    source: TableBlock
    features: Dict
    repair_log: List[str]


@dataclass
class ProcessConfig:
    """處理配置"""
    max_workers: int = 6
    enable_ocr: bool = True
    fill_blanks: bool = True
    merge_headers: bool = True
    cluster_method: str = "kmeans"
    output_format: str = "csv"


# ==================== 模組 1: PDF 區塊分割 ====================
class BlockSplitter:
    """PDF 區塊分割器 - 5 種方法"""
    
    def __init__(self):
        self.methods = []
    
    def method1_pdfplumber_tables(self, pdf_path: str) -> List[TableBlock]:
        """方法1: PDFPlumber 內建表格檢測"""
        blocks = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.find_tables()
                    for table in tables:
                        bbox = table.bbox
                        blocks.append(TableBlock(
                            page_num=page_num,
                            bbox=bbox,
                            block_type="pdfplumber_table",
                            confidence=0.9
                        ))
            logger.info(f"方法1找到 {len(blocks)} 個表格區塊")
        except Exception as e:
            logger.error(f"方法1失敗: {e}")
        return blocks
    
    def method2_text_density_analysis(self, pdf_path: str) -> List[TableBlock]:
        """方法2: 文字密度分析"""
        blocks = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    words = page.extract_words()
                    if not words:
                        continue
                    
                    # 計算文字密度網格
                    width, height = page.width, page.height
                    grid_size = 50
                    density_map = np.zeros((int(height/grid_size)+1, int(width/grid_size)+1))
                    
                    for word in words:
                        x = int(word['x0'] / grid_size)
                        y = int(word['top'] / grid_size)
                        density_map[y, x] += 1
                    
                    # 找到高密度區域
                    threshold = np.percentile(density_map[density_map > 0], 75)
                    high_density = np.argwhere(density_map > threshold)
                    
                    if len(high_density) > 0:
                        y_min = high_density[:, 0].min() * grid_size
                        y_max = high_density[:, 0].max() * grid_size + grid_size
                        x_min = high_density[:, 1].min() * grid_size
                        x_max = high_density[:, 1].max() * grid_size + grid_size
                        
                        blocks.append(TableBlock(
                            page_num=page_num,
                            bbox=(x_min, y_min, x_max, y_max),
                            block_type="density_analysis",
                            confidence=0.7
                        ))
            logger.info(f"方法2找到 {len(blocks)} 個表格區塊")
        except Exception as e:
            logger.error(f"方法2失敗: {e}")
        return blocks
    
    def method3_line_detection(self, pdf_path: str) -> List[TableBlock]:
        """方法3: 線條檢測（表格框線）"""
        blocks = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # 獲取所有線條
                    lines = page.lines + page.rects
                    if not lines:
                        continue
                    
                    # 分組相近的線條
                    horizontal = [l for l in lines if abs(l['height']) < 2]
                    vertical = [l for l in lines if abs(l['width']) < 2]
                    
                    if len(horizontal) > 2 and len(vertical) > 2:
                        x_coords = [l['x0'] for l in vertical] + [l['x1'] for l in vertical]
                        y_coords = [l['top'] for l in horizontal] + [l['bottom'] for l in horizontal]
                        
                        if x_coords and y_coords:
                            blocks.append(TableBlock(
                                page_num=page_num,
                                bbox=(min(x_coords), min(y_coords), max(x_coords), max(y_coords)),
                                block_type="line_detection",
                                confidence=0.85
                            ))
            logger.info(f"方法3找到 {len(blocks)} 個表格區塊")
        except Exception as e:
            logger.error(f"方法3失敗: {e}")
        return blocks
    
    def method4_whitespace_analysis(self, pdf_path: str) -> List[TableBlock]:
        """方法4: 空白區域分析"""
        blocks = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    chars = page.chars
                    if not chars:
                        continue
                    
                    # 按 Y 座標分組（找到行）
                    y_positions = sorted(set(c['top'] for c in chars))
                    rows = []
                    current_row = []
                    last_y = None
                    
                    for y in y_positions:
                        if last_y is None or abs(y - last_y) < 5:
                            current_row.append(y)
                        else:
                            if current_row:
                                rows.append(sum(current_row) / len(current_row))
                            current_row = [y]
                        last_y = y
                    
                    if len(rows) > 3:  # 至少3行才算表格
                        y_min = min(rows) - 10
                        y_max = max(rows) + 10
                        x_coords = [c['x0'] for c in chars] + [c['x1'] for c in chars]
                        
                        blocks.append(TableBlock(
                            page_num=page_num,
                            bbox=(min(x_coords), y_min, max(x_coords), y_max),
                            block_type="whitespace_analysis",
                            confidence=0.65
                        ))
            logger.info(f"方法4找到 {len(blocks)} 個表格區塊")
        except Exception as e:
            logger.error(f"方法4失敗: {e}")
        return blocks
    
    def method5_hybrid_voting(self, pdf_path: str) -> List[TableBlock]:
        """方法5: 混合投票法（整合前4種方法）"""
        all_blocks = []
        all_blocks.extend(self.method1_pdfplumber_tables(pdf_path))
        all_blocks.extend(self.method2_text_density_analysis(pdf_path))
        all_blocks.extend(self.method3_line_detection(pdf_path))
        all_blocks.extend(self.method4_whitespace_analysis(pdf_path))
        
        # 合併重疊區塊
        merged_blocks = self._merge_overlapping_blocks(all_blocks)
        logger.info(f"方法5整合後找到 {len(merged_blocks)} 個表格區塊")
        return merged_blocks
    
    def _merge_overlapping_blocks(self, blocks: List[TableBlock], iou_threshold: float = 0.3) -> List[TableBlock]:
        """合併重疊的區塊"""
        if not blocks:
            return []
        
        merged = []
        blocks_by_page = {}
        
        # 按頁面分組
        for block in blocks:
            if block.page_num not in blocks_by_page:
                blocks_by_page[block.page_num] = []
            blocks_by_page[block.page_num].append(block)
        
        # 每頁單獨處理
        for page_num, page_blocks in blocks_by_page.items():
            sorted_blocks = sorted(page_blocks, key=lambda b: b.confidence, reverse=True)
            used = [False] * len(sorted_blocks)
            
            for i, block1 in enumerate(sorted_blocks):
                if used[i]:
                    continue
                
                # 找到所有重疊的區塊
                overlapping = [block1]
                for j, block2 in enumerate(sorted_blocks[i+1:], i+1):
                    if used[j]:
                        continue
                    if self._calculate_iou(block1.bbox, block2.bbox) > iou_threshold:
                        overlapping.append(block2)
                        used[j] = True
                
                # 合併區塊
                x0 = min(b.bbox[0] for b in overlapping)
                y0 = min(b.bbox[1] for b in overlapping)
                x1 = max(b.bbox[2] for b in overlapping)
                y1 = max(b.bbox[3] for b in overlapping)
                avg_confidence = sum(b.confidence for b in overlapping) / len(overlapping)
                
                merged.append(TableBlock(
                    page_num=page_num,
                    bbox=(x0, y0, x1, y1),
                    block_type="merged",
                    confidence=avg_confidence
                ))
                used[i] = True
        
        return merged
    
    def _calculate_iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """計算兩個邊界框的 IoU"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0


# ==================== 模組 2: 表格提取 ====================
class TableExtractor:
    """表格提取器 - 5 種方法"""
    
    def extract_with_fallback(self, pdf_path: str, block: TableBlock) -> Optional[pd.DataFrame]:
        """使用 5 種方法提取，自動 fallback"""
        methods = [
            self.method1_camelot_stream,
            self.method2_camelot_lattice,
            self.method3_pdfplumber,
            self.method4_tabula,
            self.method5_ocr_based
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                df = method(pdf_path, block)
                if df is not None and not df.empty:
                    logger.info(f"方法{i}成功提取表格")
                    return df
            except Exception as e:
                logger.warning(f"方法{i}失敗: {e}")
                continue
        
        logger.error("所有提取方法都失敗")
        return None
    
    def method1_camelot_stream(self, pdf_path: str, block: TableBlock) -> Optional[pd.DataFrame]:
        """方法1: Camelot Stream 模式"""
        try:
            import camelot
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(block.page_num),
                flavor='stream',
                table_areas=[f"{block.bbox[0]},{block.bbox[3]},{block.bbox[2]},{block.bbox[1]}"]
            )
            if tables:
                return tables[0].df
        except:
            pass
        return None
    
    def method2_camelot_lattice(self, pdf_path: str, block: TableBlock) -> Optional[pd.DataFrame]:
        """方法2: Camelot Lattice 模式"""
        try:
            import camelot
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(block.page_num),
                flavor='lattice',
                table_areas=[f"{block.bbox[0]},{block.bbox[3]},{block.bbox[2]},{block.bbox[1]}"]
            )
            if tables:
                return tables[0].df
        except:
            pass
        return None
    
    def method3_pdfplumber(self, pdf_path: str, block: TableBlock) -> Optional[pd.DataFrame]:
        """方法3: PDFPlumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[block.page_num - 1]
                cropped = page.crop(block.bbox)
                table = cropped.extract_table()
                if table:
                    return pd.DataFrame(table[1:], columns=table[0])
        except:
            pass
        return None
    
    def method4_tabula(self, pdf_path: str, block: TableBlock) -> Optional[pd.DataFrame]:
        """方法4: Tabula-py"""
        try:
            import tabula
            area = [block.bbox[1], block.bbox[0], block.bbox[3], block.bbox[2]]
            dfs = tabula.read_pdf(
                pdf_path,
                pages=block.page_num,
                area=area,
                pandas_options={'header': None}
            )
            if dfs:
                return dfs[0]
        except:
            pass
        return None
    
    def method5_ocr_based(self, pdf_path: str, block: TableBlock) -> Optional[pd.DataFrame]:
        """方法5: OCR 基礎提取"""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, first_page=block.page_num, last_page=block.page_num)
            if not images:
                return None
            
            img = images[0]
            # 裁切到表格區域
            cropped = img.crop((
                int(block.bbox[0]),
                int(block.bbox[1]),
                int(block.bbox[2]),
                int(block.bbox[3])
            ))
            
            # OCR 識別
            text = pytesseract.image_to_string(cropped, lang='chi_tra+eng')
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) > 1:
                # 簡單的表格解析
                data = [line.split() for line in lines]
                return pd.DataFrame(data[1:], columns=data[0] if data else None)
        except:
            pass
        return None


# ==================== 模組 3: 表格修復 ====================
class TableRepairer:
    """表格修復器"""
    
    def __init__(self):
        self.repair_log = []
    
    def repair_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """執行完整修復流程"""
        self.repair_log = []
        
        df = self._remove_empty_rows_cols(df)
        df = self._merge_split_headers(df)
        df = self._fill_blank_cells(df)
        df = self._standardize_columns(df)
        df = self._fix_data_types(df)
        
        return df
    
    def _remove_empty_rows_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除完全空白的行和列"""
        before_rows = len(df)
        before_cols = len(df.columns)
        
        df = df.dropna(how='all')
        df = df.loc[:, df.notna().any(axis=0)]
        
        removed_rows = before_rows - len(df)
        removed_cols = before_cols - len(df.columns)
        
        if removed_rows > 0 or removed_cols > 0:
            self.repair_log.append(f"移除 {removed_rows} 空行, {removed_cols} 空列")
        
        return df
    
    def _merge_split_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """合併分割的表頭"""
        if len(df) < 2:
            return df
        
        # 檢查第一行是否為跨列表頭
        first_row = df.iloc[0]
        if first_row.notna().sum() < len(df.columns) * 0.5:
            # 可能是跨列表頭，嘗試合併
            second_row = df.iloc[1]
            new_columns = []
            
            for col in df.columns:
                val1 = str(first_row[col]) if pd.notna(first_row[col]) else ""
                val2 = str(second_row[col]) if pd.notna(second_row[col]) else ""
                new_columns.append(f"{val1} {val2}".strip())
            
            df.columns = new_columns
            df = df.iloc[2:].reset_index(drop=True)
            self.repair_log.append("合併跨列表頭")
        
        return df
    
    def _fill_blank_cells(self, df: pd.DataFrame) -> pd.DataFrame:
        """填補空白儲存格"""
        filled_count = 0
        
        for col in df.columns:
            # 向下填充
            before_na = df[col].isna().sum()
            df[col] = df[col].fillna(method='ffill')
            after_na = df[col].isna().sum()
            filled_count += before_na - after_na
        
        if filled_count > 0:
            self.repair_log.append(f"填補 {filled_count} 個空白儲存格")
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """標準化欄位名稱"""
        new_columns = []
        for col in df.columns:
            # 移除多餘空白
            col_str = str(col).strip()
            # 替換特殊字元
            col_str = col_str.replace('\n', ' ').replace('\r', '')
            new_columns.append(col_str)
        
        df.columns = new_columns
        self.repair_log.append("標準化欄位名稱")
        return df
    
    def _fix_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """修正數據類型"""
        for col in df.columns:
            # 嘗試轉換為數字
            try:
                if df[col].dtype == 'object':
                    # 移除逗號和其他非數字字元
                    cleaned = df[col].astype(str).str.replace(',', '').str.replace('$', '')
                    numeric = pd.to_numeric(cleaned, errors='ignore')
                    if not numeric.equals(df[col]):
                        df[col] = numeric
                        self.repair_log.append(f"欄位 '{col}' 轉換為數字")
            except:
                continue
        
        return df


# ==================== 模組 4: 表格分群 ====================
class TableClusterer:
    """表格分群器"""
    
    def extract_features(self, df: pd.DataFrame) -> Dict:
        """提取表格特徵"""
        features = {
            'num_columns': len(df.columns),
            'num_rows': len(df),
            'column_names': list(df.columns),
            'column_types': [str(dtype) for dtype in df.dtypes],
            'has_numeric': any(df.dtypes.apply(lambda x: np.issubdtype(x, np.number))),
            'density': df.notna().sum().sum() / (len(df) * len(df.columns)) if len(df) > 0 else 0
        }
        return features
    
    def cluster_tables(self, tables: List[ExtractedTable], method: str = "kmeans") -> Dict[int, List[ExtractedTable]]:
        """對表格進行分群"""
        if len(tables) < 2:
            return {0: tables}
        
        # 提取數值特徵
        feature_vectors = []
        for table in tables:
            feat = table.features
            vec = [
                feat['num_columns'],
                feat['num_rows'],
                1 if feat['has_numeric'] else 0,
                feat['density']
            ]
            feature_vectors.append(vec)
        
        X = StandardScaler().fit_transform(feature_vectors)
        
        # 執行分群
        if method == "kmeans":
            n_clusters = min(5, len(tables))
            labels = KMeans(n_clusters=n_clusters, random_state=42).fit_predict(X)
        elif method == "dbscan":
            labels = DBSCAN(eps=0.5, min_samples=2).fit_predict(X)
        else:
            labels = np.zeros(len(tables), dtype=int)
        
        # 組織結果
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(tables[i])
        
        logger.info(f"分群完成: {len(clusters)} 個群組")
        return clusters


# ==================== 模組 5: 主處理流程 ====================
class PDFTableProcessor:
    """PDF 表格處理主程序"""
    
    def __init__(self, config: ProcessConfig):
        self.config = config
        self.splitter = BlockSplitter()
        self.extractor = TableExtractor()
        self.repairer = TableRepairer()
        self.clusterer = TableClusterer()
    
    def process_pdf(self, pdf_path: str, output_dir: str) -> Dict:
        """處理 PDF 文件"""
        logger.info(f"開始處理: {pdf_path}")
        
        # 1. 分割區塊
        blocks = self.splitter.method5_hybrid_voting(pdf_path)
        logger.info(f"找到 {len(blocks)} 個表格區塊")
        
        # 2. 並行提取表格
        extracted_tables = []
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._process_block, pdf_path, block): block 
                for block in blocks
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    extracted_tables.append(result)
        
        logger.info(f"成功提取 {len(extracted_tables)} 個表格")
        
        # 3. 分群
        clusters = self.clusterer.cluster_tables(extracted_tables, self.config.cluster_method)
        
        # 4. 輸出結果
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = self._export_results(clusters, output_path)
        
        logger.info("處理完成!")
        return results
    
    def _process_block(self, pdf_path: str, block: TableBlock) -> Optional[ExtractedTable]:
        """處理單個區塊"""
        try:
            # 提取表格
            df = self.extractor.extract_with_fallback(pdf_path, block)
            if df is None or df.empty:
                return None
            
            # 修復表格
            repaired_df = self.repairer.repair_table(df)
            
            # 提取特徵
            features = self.clusterer.extract_features(repaired_df)
            
            return ExtractedTable(
                data=repaired_df,
                source=block,
                features=features,
                repair_log=self.repairer.repair_log.copy()
            )
        except Exception as e:
            logger.error(f"處理區塊失敗: {e}")
            return None
    
    def _export_results(self, clusters: Dict[int, List[ExtractedTable]], output_dir: Path) -> Dict:
        """輸出結果"""
        summary = {
            'total_tables': sum(len(tables) for tables in clusters.values()),
            'num_clusters': len(clusters),
            'clusters': {}
        }
        
        for cluster_id, tables in clusters.items():
            cluster_dir = output_dir / f"cluster_{cluster_id}"
            cluster_dir.mkdir(exist_ok=True)
            
            cluster_info = {
                'num_tables': len(tables),
                'files': []
            }
            
            for i, table in enumerate(tables):
                filename = f"table_{i}_page{table.source.page_num}.csv"
                filepath = cluster_dir / filename
                table.data.to_csv(filepath, index=False, encoding='utf-8-sig')
                
                cluster_info['files'].append({
                    'filename': filename,
                    'page': table.source.page_num,
                    'features': table.features,
                    'repair_log': table.repair_log
                })
            
            summary['clusters'][cluster_id] = cluster_info
        
        # 保存摘要
        summary_file = output_dir / 'summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"結果已保存到: {output_dir}")
        return summary


# ==================== 主程序入口 ====================
def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF 表格提取系統')
    parser.add_argument('--input', '-i', required=True, help='輸入 PDF 文件路徑')
    parser.add_argument('--output', '-o', default='output', help='輸出目錄')
    parser.add_argument('--workers', '-w', type=int, default=6, help='並行處理數量')
    parser.add_argument('--cluster', '-c', choices=['kmeans', 'dbscan'], default='kmeans', help='分群方法')
    
    args = parser.parse_args()
    
    # 配置
    config = ProcessConfig(
        max_workers=args.workers,
        cluster_method=args.cluster
    )
    
    # 處理
    processor = PDFTableProcessor(config)
    results = processor.process_pdf(args.input, args.output)
    
    print("\n" + "="*50)
    print("處理完成!")
    print(f"總共提取: {results['total_tables']} 個表格")
    print(f"分成: {results['num_clusters']} 個群組")
    print(f"結果保存在: {args.output}")
    print("="*50)


if __name__ == "__main__":
    main()
