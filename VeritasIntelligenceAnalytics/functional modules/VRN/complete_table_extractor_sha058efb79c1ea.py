"""
完整表格識別+寫入系統
確保每個引擎都有完整的數據提取和保存功能
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
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import subprocess

# Rich支援
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

class CompleteTableExtractor:
    """完整的表格識別和寫入系統"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path("./complete_extraction_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # 為每個引擎創建專門目錄
        self.engine_dirs = {}
        for engine in ['pdfplumber', 'camelot', 'pymupdf', 'tabula', 'javascript']:
            engine_dir = self.output_dir / engine
            engine_dir.mkdir(exist_ok=True)
            self.engine_dirs[engine] = engine_dir
        
        self.available_engines = self._check_engines()
        self.extraction_log = []
        
        self._print("🔧 完整表格識別+寫入系統", "info")
        self._print(f"📁 主輸出目錄: {self.output_dir}", "info")
        
    def _check_engines(self) -> Dict[str, bool]:
        """檢查可用引擎"""
        engines = {
            'pdfplumber': False,
            'camelot': False,
            'pymupdf': False,
            'tabula': False,
            'nodejs': False
        }
        
        # 檢查Python引擎
        for engine in ['pdfplumber', 'camelot', 'pymupdf', 'tabula']:
            try:
                if engine == 'pdfplumber':
                    import pdfplumber
                    engines[engine] = True
                elif engine == 'camelot':
                    import camelot
                    engines[engine] = True
                elif engine == 'pymupdf':
                    import fitz
                    engines[engine] = True
                elif engine == 'tabula':
                    import tabula
                    engines[engine] = True
            except ImportError:
                pass
        
        # 檢查Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            engines['nodejs'] = result.returncode == 0
        except:
            pass
        
        return engines
    
    def _print(self, message: str, level: str = "info"):
        """統一打印方法"""
        if RICH_AVAILABLE:
            styles = {"error": "red", "warning": "yellow", "success": "green", "info": "cyan"}
            console.print(f"[{styles.get(level, 'white')}]{message}[/{styles.get(level, 'white')}]")
        else:
            prefixes = {"error": "❌", "warning": "⚠️ ", "success": "✅", "info": "ℹ️ "}
            print(f"{prefixes.get(level, '')} {message}")
    
    def _log_extraction(self, engine: str, pdf_name: str, page_num: int, 
                       table_idx: int, success: bool, output_file: str = "", error: str = ""):
        """記錄提取操作"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'engine': engine,
            'pdf_name': pdf_name,
            'page_num': page_num + 1,
            'table_idx': table_idx + 1,
            'success': success,
            'output_file': output_file,
            'error': error
        }
        self.extraction_log.append(log_entry)
    
    # ========================================
    # PDFPlumber 完整提取+寫入
    # ========================================
    def extract_and_save_pdfplumber(self, pdf_path: str) -> Dict:
        """PDFPlumber完整提取和保存"""
        if not self.available_engines['pdfplumber']:
            return {'engine': 'pdfplumber', 'status': 'unavailable', 'tables_saved': 0}
        
        import pdfplumber
        pdf_name = Path(pdf_path).stem
        engine_output_dir = self.engine_dirs['pdfplumber'] / pdf_name
        engine_output_dir.mkdir(exist_ok=True)
        
        self._print(f"🔍 PDFPlumber 提取: {pdf_name}", "info")
        
        tables_saved = 0
        results = {
            'engine': 'pdfplumber',
            'status': 'success',
            'tables_saved': 0,
            'pages_processed': 0,
            'output_files': [],
            'processing_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    self._print(f"  📄 處理第 {page_num + 1} 頁...", "info")
                    
                    try:
                        tables = page.extract_tables()
                        
                        if tables:
                            for table_idx, table in enumerate(tables):
                                if table and len(table) > 1:  # 確保有標題行和數據行
                                    try:
                                        # 轉換為DataFrame
                                        headers = table[0] if table[0] else [f"Column_{j+1}" for j in range(len(table[1]))]
                                        data_rows = table[1:]
                                        
                                        df = pd.DataFrame(data_rows, columns=headers)
                                        
                                        # 保存CSV
                                        csv_filename = f"page_{page_num+1:03d}_table_{table_idx+1:02d}.csv"
                                        csv_path = engine_output_dir / csv_filename
                                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                                        
                                        # 保存Excel (可選)
                                        xlsx_filename = f"page_{page_num+1:03d}_table_{table_idx+1:02d}.xlsx"
                                        xlsx_path = engine_output_dir / xlsx_filename
                                        df.to_excel(xlsx_path, index=False, engine='openpyxl')
                                        
                                        # 保存JSON (結構化數據)
                                        json_filename = f"page_{page_num+1:03d}_table_{table_idx+1:02d}.json"
                                        json_path = engine_output_dir / json_filename
                                        table_data = {
                                            'metadata': {
                                                'page': page_num + 1,
                                                'table_index': table_idx + 1,
                                                'rows': len(df),
                                                'columns': len(df.columns),
                                                'extraction_engine': 'pdfplumber'
                                            },
                                            'data': df.to_dict('records')
                                        }
                                        
                                        with open(json_path, 'w', encoding='utf-8') as f:
                                            json.dump(table_data, f, indent=2, ensure_ascii=False)
                                        
                                        results['output_files'].extend([str(csv_path), str(xlsx_path), str(json_path)])
                                        tables_saved += 1
                                        
                                        self._log_extraction('pdfplumber', pdf_name, page_num, table_idx, True, str(csv_path))
                                        self._print(f"    ✅ 表格 {table_idx+1}: {len(df)}行×{len(df.columns)}列 → {csv_filename}", "success")
                                        
                                    except Exception as e:
                                        error_msg = f"保存表格失敗: {str(e)}"
                                        results['errors'].append(error_msg)
                                        self._log_extraction('pdfplumber', pdf_name, page_num, table_idx, False, "", error_msg)
                                        self._print(f"    ❌ 表格 {table_idx+1}: {error_msg}", "error")
                        
                        results['pages_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"處理第{page_num+1}頁失敗: {str(e)}"
                        results['errors'].append(error_msg)
                        self._print(f"  ❌ 第{page_num+1}頁: {error_msg}", "error")
        
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"PDF開啟失敗: {str(e)}")
            self._print(f"❌ PDFPlumber處理失敗: {str(e)}", "error")
        
        results['tables_saved'] = tables_saved
        results['processing_time'] = time.time() - start_time
        
        return results
    
    # ========================================
    # Camelot 完整提取+寫入
    # ========================================
    def extract_and_save_camelot(self, pdf_path: str) -> Dict:
        """Camelot完整提取和保存"""
        if not self.available_engines['camelot']:
            return {'engine': 'camelot', 'status': 'unavailable', 'tables_saved': 0}
        
        import camelot
        pdf_name = Path(pdf_path).stem
        engine_output_dir = self.engine_dirs['camelot'] / pdf_name
        engine_output_dir.mkdir(exist_ok=True)
        
        self._print(f"🎯 Camelot 提取: {pdf_name}", "info")
        
        results = {
            'engine': 'camelot',
            'status': 'success',
            'tables_saved': 0,
            'pages_processed': 0,
            'output_files': [],
            'processing_time': 0,
            'errors': [],
            'accuracy_scores': []
        }
        
        start_time = time.time()
        
        try:
            # 嘗試lattice模式
            tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')
            
            if len(tables) == 0:
                # 如果lattice沒找到，嘗試stream模式
                self._print("  🔄 Lattice模式無結果，嘗試Stream模式...", "warning")
                tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
            
            tables_saved = 0
            
            for table_idx, table in enumerate(tables):
                try:
                    page_num = table.page - 1  # Camelot頁數從1開始
                    accuracy = table.accuracy
                    
                    self._print(f"  📄 第{table.page}頁 表格{table_idx+1} (準確度: {accuracy:.1f}%)", "info")
                    
                    # 獲取DataFrame
                    df = table.df
                    
                    if not df.empty:
                        # 文件名包含準確度信息
                        base_filename = f"page_{table.page:03d}_table_{table_idx+1:02d}_acc_{accuracy:.0f}"
                        
                        # 保存CSV
                        csv_filename = f"{base_filename}.csv"
                        csv_path = engine_output_dir / csv_filename
                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        
                        # 保存Excel
                        xlsx_filename = f"{base_filename}.xlsx"
                        xlsx_path = engine_output_dir / xlsx_filename
                        df.to_excel(xlsx_path, index=False, engine='openpyxl')
                        
                        # 保存JSON (包含Camelot特有的元數據)
                        json_filename = f"{base_filename}.json"
                        json_path = engine_output_dir / json_filename
                        table_data = {
                            'metadata': {
                                'page': table.page,
                                'table_index': table_idx + 1,
                                'rows': len(df),
                                'columns': len(df.columns),
                                'extraction_engine': 'camelot',
                                'accuracy': accuracy,
                                'flavor': 'lattice',  # 或從tables對象獲取
                                'bbox': table._bbox
                            },
                            'data': df.to_dict('records')
                        }
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(table_data, f, indent=2, ensure_ascii=False)
                        
                        # 額外保存Camelot原生格式
                        camelot_csv = engine_output_dir / f"{base_filename}_camelot.csv"
                        table.to_csv(str(camelot_csv))
                        
                        results['output_files'].extend([str(csv_path), str(xlsx_path), str(json_path), str(camelot_csv)])
                        results['accuracy_scores'].append(accuracy)
                        tables_saved += 1
                        
                        self._log_extraction('camelot', pdf_name, page_num, table_idx, True, str(csv_path))
                        self._print(f"    ✅ 表格保存: {len(df)}行×{len(df.columns)}列 → {csv_filename}", "success")
                        
                except Exception as e:
                    error_msg = f"Camelot表格{table_idx+1}保存失敗: {str(e)}"
                    results['errors'].append(error_msg)
                    self._log_extraction('camelot', pdf_name, page_num if 'page_num' in locals() else 0, table_idx, False, "", error_msg)
                    self._print(f"    ❌ 表格{table_idx+1}: {error_msg}", "error")
            
            results['tables_saved'] = tables_saved
            
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"Camelot處理失敗: {str(e)}")
            self._print(f"❌ Camelot處理失敗: {str(e)}", "error")
        
        results['processing_time'] = time.time() - start_time
        return results
    
    # ========================================
    # PyMuPDF 完整提取+寫入
    # ========================================
    def extract_and_save_pymupdf(self, pdf_path: str) -> Dict:
        """PyMuPDF完整提取和保存"""
        if not self.available_engines['pymupdf']:
            return {'engine': 'pymupdf', 'status': 'unavailable', 'tables_saved': 0}
        
        import fitz
        pdf_name = Path(pdf_path).stem
        engine_output_dir = self.engine_dirs['pymupdf'] / pdf_name
        engine_output_dir.mkdir(exist_ok=True)
        
        self._print(f"🚀 PyMuPDF 提取: {pdf_name}", "info")
        
        results = {
            'engine': 'pymupdf',
            'status': 'success',
            'tables_saved': 0,
            'pages_processed': 0,
            'output_files': [],
            'processing_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        tables_saved = 0
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                self._print(f"  📄 處理第 {page_num + 1} 頁...", "info")
                page = doc.load_page(page_num)
                
                try:
                    # 使用find_tables方法
                    tables = page.find_tables()
                    
                    for table_idx, table in enumerate(tables):
                        try:
                            # 提取表格數據
                            table_data = table.extract()
                            
                            if table_data and len(table_data) > 1:
                                # 轉換為DataFrame
                                headers = table_data[0] if table_data[0] else [f"Column_{j+1}" for j in range(len(table_data[1]))]
                                data_rows = table_data[1:]
                                
                                df = pd.DataFrame(data_rows, columns=headers)
                                
                                # 清理空值和格式
                                df = df.fillna('')
                                
                                base_filename = f"page_{page_num+1:03d}_table_{table_idx+1:02d}"
                                
                                # 保存CSV
                                csv_filename = f"{base_filename}.csv"
                                csv_path = engine_output_dir / csv_filename
                                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                                
                                # 保存Excel
                                xlsx_filename = f"{base_filename}.xlsx"
                                xlsx_path = engine_output_dir / xlsx_filename
                                df.to_excel(xlsx_path, index=False, engine='openpyxl')
                                
                                # 保存JSON (包含PyMuPDF特有的元數據)
                                json_filename = f"{base_filename}.json"
                                json_path = engine_output_dir / json_filename
                                metadata = {
                                    'metadata': {
                                        'page': page_num + 1,
                                        'table_index': table_idx + 1,
                                        'rows': len(df),
                                        'columns': len(df.columns),
                                        'extraction_engine': 'pymupdf',
                                        'bbox': table.bbox,
                                        'page_width': page.rect.width,
                                        'page_height': page.rect.height
                                    },
                                    'data': df.to_dict('records')
                                }
                                
                                with open(json_path, 'w', encoding='utf-8') as f:
                                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                                
                                results['output_files'].extend([str(csv_path), str(xlsx_path), str(json_path)])
                                tables_saved += 1
                                
                                self._log_extraction('pymupdf', pdf_name, page_num, table_idx, True, str(csv_path))
                                self._print(f"    ✅ 表格 {table_idx+1}: {len(df)}行×{len(df.columns)}列 → {csv_filename}", "success")
                                
                        except Exception as e:
                            error_msg = f"PyMuPDF表格{table_idx+1}提取失敗: {str(e)}"
                            results['errors'].append(error_msg)
                            self._log_extraction('pymupdf', pdf_name, page_num, table_idx, False, "", error_msg)
                            self._print(f"    ❌ 表格{table_idx+1}: {error_msg}", "error")
                
                except Exception as e:
                    # 降級處理：如果find_tables失敗，嘗試文本分析
                    self._print(f"  ⚠️  第{page_num+1}頁find_tables失敗，使用文本分析", "warning")
                    try:
                        self._extract_pymupdf_text_analysis(page, page_num, pdf_name, engine_output_dir, results)
                    except Exception as text_error:
                        error_msg = f"第{page_num+1}頁處理完全失敗: {str(text_error)}"
                        results['errors'].append(error_msg)
                        self._print(f"  ❌ 第{page_num+1}頁: {error_msg}", "error")
                
                results['pages_processed'] += 1
            
            doc.close()
            results['tables_saved'] = tables_saved
            
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"PyMuPDF處理失敗: {str(e)}")
            self._print(f"❌ PyMuPDF處理失敗: {str(e)}", "error")
        
        results['processing_time'] = time.time() - start_time
        return results
    
    def _extract_pymupdf_text_analysis(self, page, page_num: int, pdf_name: str, 
                                     output_dir: Path, results: Dict):
        """PyMuPDF文本分析降級方法"""
        try:
            # 獲取文本塊
            blocks = page.get_text("dict")["blocks"]
            
            # 尋找可能的表格結構
            for block_idx, block in enumerate(blocks):
                if "lines" in block:
                    lines = block["lines"]
                    
                    # 簡單的表格檢測：多行且每行有多個spans
                    table_lines = []
                    for line in lines:
                        spans = line.get("spans", [])
                        if len(spans) >= 2:  # 至少2個字段
                            row_data = [span.get("text", "").strip() for span in spans]
                            if any(text for text in row_data):  # 至少有一個非空字段
                                table_lines.append(row_data)
                    
                    # 如果找到至少3行數據，視為表格
                    if len(table_lines) >= 3:
                        # 標準化列數（取最常見的列數）
                        col_counts = [len(line) for line in table_lines]
                        most_common_cols = max(set(col_counts), key=col_counts.count)
                        
                        # 過濾並補齊列
                        standardized_lines = []
                        for line in table_lines:
                            if len(line) == most_common_cols:
                                standardized_lines.append(line)
                            elif len(line) < most_common_cols:
                                # 補齊空列
                                line.extend([''] * (most_common_cols - len(line)))
                                standardized_lines.append(line)
                        
                        if len(standardized_lines) >= 2:  # 至少標題+1行數據
                            # 創建DataFrame
                            headers = standardized_lines[0]
                            data_rows = standardized_lines[1:]
                            df = pd.DataFrame(data_rows, columns=headers)
                            
                            base_filename = f"page_{page_num+1:03d}_textblock_{block_idx+1:02d}"
                            
                            # 保存文件
                            csv_filename = f"{base_filename}.csv"
                            csv_path = output_dir / csv_filename
                            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                            
                            results['output_files'].append(str(csv_path))
                            results['tables_saved'] = results.get('tables_saved', 0) + 1
                            
                            self._print(f"    ✅ 文本表格 {block_idx+1}: {len(df)}行×{len(df.columns)}列 → {csv_filename}", "success")
                            
        except Exception as e:
            self._print(f"    ⚠️  文本分析也失敗: {str(e)}", "warning")
    
    # ========================================
    # Tabula 完整提取+寫入
    # ========================================
    def extract_and_save_tabula(self, pdf_path: str) -> Dict:
        """Tabula完整提取和保存"""
        if not self.available_engines['tabula']:
            return {'engine': 'tabula', 'status': 'unavailable', 'tables_saved': 0}
        
        import tabula
        pdf_name = Path(pdf_path).stem
        engine_output_dir = self.engine_dirs['tabula'] / pdf_name
        engine_output_dir.mkdir(exist_ok=True)
        
        self._print(f"☕ Tabula 提取: {pdf_name}", "info")
        
        results = {
            'engine': 'tabula',
            'status': 'success',
            'tables_saved': 0,
            'pages_processed': 0,
            'output_files': [],
            'processing_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        tables_saved = 0
        
        try:
            # 獲取總頁數
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
            
            # 逐頁處理
            for page_num in range(total_pages):
                self._print(f"  📄 處理第 {page_num + 1} 頁...", "info")
                
                try:
                    # Tabula提取該頁的所有表格
                    dfs = tabula.read_pdf(pdf_path, pages=[page_num + 1], multiple_tables=True)
                    
                    valid_tables = [df for df in dfs if not df.empty]
                    
                    for table_idx, df in enumerate(valid_tables):
                        try:
                            # 清理DataFrame
                            df = df.fillna('')
                            
                            # 如果第一行看起來是標題，使用它作為列名
                            if len(df) > 1:
                                first_row = df.iloc[0]
                                if first_row.astype(str).str.len().mean() > 3:  # 平均字符長度大於3可能是標題
                                    df.columns = first_row
                                    df = df.iloc[1:].reset_index(drop=True)
                            
                            base_filename = f"page_{page_num+1:03d}_table_{table_idx+1:02d}"
                            
                            # 保存CSV
                            csv_filename = f"{base_filename}.csv"
                            csv_path = engine_output_dir / csv_filename
                            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                            
                            # 保存Excel
                            xlsx_filename = f"{base_filename}.xlsx"
                            xlsx_path = engine_output_dir / xlsx_filename
                            df.to_excel(xlsx_path, index=False, engine='openpyxl')
                            
                            # 保存JSON
                            json_filename = f"{base_filename}.json"
                            json_path = engine_output_dir / json_filename
                            table_data = {
                                'metadata': {
                                    'page': page_num + 1,
                                    'table_index': table_idx + 1,
                                    'rows': len(df),
                                    'columns': len(df.columns),
                                    'extraction_engine': 'tabula'
                                },
                                'data': df.to_dict('records')
                            }
                            
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(table_data, f, indent=2, ensure_ascii=False)
                            
                            results['output_files'].extend([str(csv_path), str(xlsx_path), str(json_path)])
                            tables_saved += 1
                            
                            self._log_extraction('tabula', pdf_name, page_num, table_idx, True, str(csv_path))
                            self._print(f"    ✅ 表格 {table_idx+1}: {len(df)}行×{len(df.columns)}列 → {csv_filename}", "success")
                            
                        except Exception as e:
                            error_msg = f"Tabula表格{table_idx+1}保存失敗: {str(e)}"
                            results['errors'].append(error_msg)
                            self._log_extraction('tabula', pdf_name, page_num, table_idx, False, "", error_msg)
                            self._print(f"    ❌ 表格{table_idx+1}: {error_msg}", "error")
                
                except Exception as e:
                    error_msg = f"Tabula第{page_num+1}頁處理失敗: {str(e)}"
                    results['errors'].append(error_msg)
                    self._print(f"  ❌ 第{page_num+1}頁: {error_msg}", "error")
                
                results['pages_processed'] += 1
        
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"Tabula處理失敗: {str(e)}")
            self._print(f"❌ Tabula處理失敗: {str(e)}", "error")
        
        results['tables_saved'] = tables_saved
        results['processing_time'] = time.time() - start_time
        return results
    
    # ========================================
    # JavaScript引擎 (結構化提取+保存)
    # ========================================
    def extract_and_save_javascript(self, pdf_path: str) -> Dict:
        """JavaScript引擎提取和保存"""
        if not self.available_engines['nodejs']:
            return {'engine': 'javascript', 'status': 'unavailable', 'tables_saved': 0}
        
        pdf_name = Path(pdf_path).stem
        engine_output_dir = self.engine_dirs['javascript'] / pdf_name
        engine_output_dir.mkdir(exist_ok=True)
        
        self._print(f"⚡ JavaScript 引擎提取: {pdf_name}", "info")
        
        results = {
            'engine': 'javascript',
            'status': 'success',
            'tables_saved': 0,
            'pages_processed': 0,
            'output_files': [],
            'processing_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        # 創建JavaScript提取腳本
        js_script = f'''
const fs = require('fs');

async function extractTablesFromPDF() {{
    console.log("開始JavaScript表格提取...");
    
    try {{
        // 嘗試使用pdf2json
        const pdf2json = require('pdf2json');
        const pdfParser = new pdf2json();
        
        const results = [];
        let tablesFound = 0;
        
        pdfParser.on('pdfParser_dataReady', pdfData => {{
            console.log("PDF解析完成，分析表格結構...");
            
            pdfData.Pages.forEach((page, pageIndex) => {{
                const pageNum = pageIndex + 1;
                const textItems = page.Texts || [];
                
                // 按Y座標分組文本項目
                const yGroups = {{}};
                textItems.forEach(item => {{
                    const y = Math.round(item.y * 10) / 10; // 四捨五入到1位小數
                    if (!yGroups[y]) yGroups[y] = [];
                    
                    // 解析文本內容
                    const text = item.R.map(r => decodeURIComponent(r.T || "")).join("");
                    if (text.trim()) {{
                        yGroups[y].push({{
                            x: item.x,
                            text: text.trim()
                        }});
                    }}
                }});
                
                // 檢測表格行
                const sortedY = Object.keys(yGroups).map(y => parseFloat(y)).sort((a, b) => b - a);
                const potentialTableRows = [];
                
                sortedY.forEach(y => {{
                    const items = yGroups[y];
                    if (items.length >= 2) {{ // 至少2個項目在同一行
                        // 按X座標排序
                        items.sort((a, b) => a.x - b.x);
                        potentialTableRows.push({{
                            y: y,
                            items: items,
                            rowData: items.map(item => item.text)
                        }});
                    }}
                }});
                
                // 如果有連續的多項目行，識別為表格
                if (potentialTableRows.length >= 3) {{
                    console.log(`第${{pageNum}}頁發現潛在表格，共${{potentialTableRows.length}}行`);
                    
                    // 標準化列數（使用最常見的列數）
                    const colCounts = potentialTableRows.map(row => row.items.length);
                    const mostCommonCols = colCounts.sort((a,b) =>
                        colCounts.filter(v => v===a).length - colCounts.filter(v => v===b).length
                    ).pop();
                    
                    // 過濾出列數一致的行
                    const standardizedRows = potentialTableRows
                        .filter(row => row.items.length === mostCommonCols)
                        .slice(0, 50); // 最多取50行避免過大
                    
                    if (standardizedRows.length >= 2) {{
                        const tableData = {{
                            metadata: {{
                                page: pageNum,
                                table_index: 1,
                                rows: standardizedRows.length,
                                columns: mostCommonCols,
                                extraction_engine: 'javascript_pdf2json',
                                y_positions: standardizedRows.map(row => row.y)
                            }},
                            headers: standardizedRows[0].rowData,
                            data: standardizedRows.slice(1).map(row => {{
                                const rowObj = {{}};
                                standardizedRows[0].rowData.forEach((header, idx) => {{
                                    rowObj[header || `Column_${{idx+1}}`] = row.rowData[idx] || "";
                                }});
                                return rowObj;
                            }})
                        }};
                        
                        // 保存JSON文件
                        const jsonFilename = `page_${{pageNum.toString().padStart(3, '0')}}_table_001.json`;
                        const jsonPath = `{str(engine_output_dir).replace(os.sep, '/')}/${{jsonFilename}}`;
                        fs.writeFileSync(jsonPath, JSON.stringify(tableData, null, 2), 'utf8');
                        
                        // 保存CSV文件
                        const csvFilename = `page_${{pageNum.toString().padStart(3, '0')}}_table_001.csv`;
                        const csvPath = `{str(engine_output_dir).replace(os.sep, '/')}/${{csvFilename}}`;
                        
                        let csvContent = standardizedRows[0].rowData.map(h => `"${{h || ''}}"`).join(',') + '\\n';
                        standardizedRows.slice(1).forEach(row => {{
                            csvContent += row.rowData.map(cell => `"${{cell || ''}}"`).join(',') + '\\n';
                        }});
                        
                        fs.writeFileSync(csvPath, csvContent, 'utf8');
                        
                        console.log(`✅ 第${{pageNum}}頁表格已保存: ${{csvFilename}} (${{standardizedRows.length}}行×${{mostCommonCols}}列)`);
                        
                        results.push({{
                            page: pageNum,
                            tables_saved: 1,
                            files: [jsonPath, csvPath]
                        }});
                        
                        tablesFound++;
                    }}
                }}
            }});
            
            // 輸出最終結果
            console.log(JSON.stringify({{
                status: 'success',
                total_tables: tablesFound,
                pages: results
            }}));
        }});
        
        pdfParser.on('pdfParser_dataError', err => {{
            console.log(JSON.stringify({{
                status: 'error',
                error: err.message || err.toString()
            }}));
        }});
        
        pdfParser.loadPDF('{str(pdf_path).replace(os.sep, '/')}');
        
    }} catch (error) {{
        console.log(JSON.stringify({{
            status: 'error',
            error: error.message || error.toString()
        }}));
    }}
}}

extractTablesFromPDF();
'''
        
        try:
            # 執行JavaScript腳本
            result = subprocess.run([
                'node', '-e', js_script
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                try:
                    # 解析最後一行JSON結果
                    output_lines = result.stdout.strip().split('\n')
                    result_json = None
                    
                    for line in reversed(output_lines):
                        try:
                            result_json = json.loads(line)
                            break
                        except:
                            continue
                    
                    if result_json and result_json.get('status') == 'success':
                        results['tables_saved'] = result_json.get('total_tables', 0)
                        
                        # 收集生成的文件
                        for page_result in result_json.get('pages', []):
                            results['output_files'].extend(page_result.get('files', []))
                        
                        results['pages_processed'] = len(result_json.get('pages', []))
                        
                        self._print(f"  ✅ JavaScript提取完成: {results['tables_saved']}個表格", "success")
                    else:
                        error_msg = result_json.get('error', '未知錯誤') if result_json else '輸出格式錯誤'
                        results['status'] = 'failed'
                        results['errors'].append(f"JavaScript執行失敗: {error_msg}")
                        
                except Exception as parse_error:
                    results['status'] = 'failed'
                    results['errors'].append(f"JavaScript結果解析失敗: {str(parse_error)}")
                    self._print(f"  ❌ JavaScript結果解析失敗: {str(parse_error)}", "error")
            else:
                error_output = result.stderr or "無錯誤輸出"
                results['status'] = 'failed'
                results['errors'].append(f"JavaScript腳本執行失敗: {error_output}")
                self._print(f"  ❌ JavaScript執行失敗: {error_output}", "error")
                
        except subprocess.TimeoutExpired:
            results['status'] = 'failed'
            results['errors'].append("JavaScript執行超時")
            self._print("  ⏱️  JavaScript執行超時", "error")
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"JavaScript引擎錯誤: {str(e)}")
            self._print(f"  ❌ JavaScript引擎錯誤: {str(e)}", "error")
        
        results['processing_time'] = time.time() - start_time
        return results
    
    # ========================================
    # 主要處理方法
    # ========================================
    def process_pdf_complete_extraction(self, pdf_path: str, engines: List[str] = None) -> Dict:
        """完整的PDF表格提取處理"""
        if engines is None:
            engines = [e for e, available in self.available_engines.items() if available and e != 'nodejs']
            if self.available_engines['nodejs']:
                engines.append('javascript')
        
        pdf_name = Path(pdf_path).stem
        self._print(f"\n🚀 開始完整提取: {pdf_name}", "info")
        self._print(f"🔧 使用引擎: {', '.join(engines)}", "info")
        self._print("=" * 60, "info")
        
        all_results = {}
        
        # 執行各個引擎的提取
        for engine in engines:
            self._print(f"\n📊 {engine.upper()} 引擎處理中...", "info")
            
            if engine == 'pdfplumber' and self.available_engines['pdfplumber']:
                all_results[engine] = self.extract_and_save_pdfplumber(pdf_path)
            elif engine == 'camelot' and self.available_engines['camelot']:
                all_results[engine] = self.extract_and_save_camelot(pdf_path)
            elif engine == 'pymupdf' and self.available_engines['pymupdf']:
                all_results[engine] = self.extract_and_save_pymupdf(pdf_path)
            elif engine == 'tabula' and self.available_engines['tabula']:
                all_results[engine] = self.extract_and_save_tabula(pdf_path)
            elif engine == 'javascript' and self.available_engines['nodejs']:
                all_results[engine] = self.extract_and_save_javascript(pdf_path)
            else:
                self._print(f"  ⚠️  {engine} 引擎不可用，跳過", "warning")
        
        # 生成匯總報告
        summary = self._generate_extraction_summary(all_results, pdf_name)
        
        # 保存提取日誌
        self._save_extraction_log(pdf_name)
        
        return summary
    
    def _generate_extraction_summary(self, all_results: Dict, pdf_name: str) -> Dict:
        """生成提取摘要"""
        total_tables = sum(result.get('tables_saved', 0) for result in all_results.values())
        total_files = sum(len(result.get('output_files', [])) for result in all_results.values())
        successful_engines = sum(1 for result in all_results.values() if result.get('status') == 'success')
        
        summary = {
            'pdf_name': pdf_name,
            'timestamp': datetime.now().isoformat(),
            'total_engines': len(all_results),
            'successful_engines': successful_engines,
            'total_tables_extracted': total_tables,
            'total_output_files': total_files,
            'engine_results': all_results,
            'output_directory': str(self.output_dir)
        }
        
        # 保存摘要報告
        summary_path = self.output_dir / f"{pdf_name}_extraction_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary
    
    def _save_extraction_log(self, pdf_name: str):
        """保存提取日誌"""
        log_path = self.output_dir / f"{pdf_name}_extraction_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_log, f, indent=2, ensure_ascii=False)
    
    def batch_process_complete_extraction(self, folder_path: str, engines: List[str] = None):
        """批量完整提取處理"""
        folder = Path(folder_path)
        pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        
        if not pdf_files:
            self._print(f"❌ 在 {folder_path} 中沒有找到PDF文件", "error")
            return
        
        self._print(f"📁 找到 {len(pdf_files)} 個PDF文件", "success")
        self._print(f"📊 將使用完整提取模式，每個表格都會保存為多種格式", "info")
        
        batch_summary = {
            'batch_start': datetime.now().isoformat(),
            'total_files': len(pdf_files),
            'processed_files': 0,
            'total_tables_extracted': 0,
            'total_output_files': 0,
            'file_results': {}
        }
        
        for i, pdf_file in enumerate(pdf_files, 1):
            self._print(f"\n{'='*80}", "info")
            self._print(f"📄 [{i}/{len(pdf_files)}] 完整提取: {pdf_file.name}", "info")
            self._print(f"{'='*80}", "info")
            
            try:
                file_summary = self.process_pdf_complete_extraction(str(pdf_file), engines)
                
                batch_summary['processed_files'] += 1
                batch_summary['total_tables_extracted'] += file_summary['total_tables_extracted']
                batch_summary['total_output_files'] += file_summary['total_output_files']
                batch_summary['file_results'][pdf_file.name] = file_summary
                
                self._print(f"✅ {pdf_file.name}: {file_summary['total_tables_extracted']}個表格已完整提取", "success")
                
            except Exception as e:
                self._print(f"❌ 處理 {pdf_file.name} 時出錯: {e}", "error")
                batch_summary['file_results'][pdf_file.name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                continue
            
            time.sleep(0.5)
        
        # 保存批量處理摘要
        batch_summary['batch_end'] = datetime.now().isoformat()
        batch_summary_path = self.output_dir / f"BATCH_EXTRACTION_SUMMARY_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(batch_summary_path, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, indent=2, ensure_ascii=False)
        
        # 顯示最終摘要
        self._print(f"\n🎉 批量完整提取完成！", "success")
        self._print(f"📊 處理文件: {batch_summary['processed_files']}/{batch_summary['total_files']}", "info")
        self._print(f"📊 總提取表格: {batch_summary['total_tables_extracted']}", "info")
        self._print(f"📊 總輸出文件: {batch_summary['total_output_files']}", "info")
        self._print(f"📁 結果目錄: {self.output_dir}", "info")
        self._print(f"📄 批量摘要: {batch_summary_path}", "info")


def main():
    """主函數"""
    # === 配置區域 ===
    PDF_FOLDER = r"C:\Users\tonyk\OneDrive\App\VeritasIntelligenceSystem\VeritasReportNova™\input"
    OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\App\VeritasIntelligenceSystem\VeritasReportNova™\complete_extraction"
    
    # 選擇引擎 (留空會自動使用所有可用引擎)
    ENGINES = None  # 或指定如: ['pdfplumber', 'camelot', 'pymupdf']
    
    # 檢查路徑
    if not os.path.exists(PDF_FOLDER):
        if RICH_AVAILABLE:
            console.print(f"[red]❌ 找不到資料夾: {PDF_FOLDER}[/red]")
            PDF_FOLDER = console.input("請輸入正確的PDF資料夾路徑: ").strip().strip('"')
        else:
            print(f"❌ 找不到資料夾: {PDF_FOLDER}")
            PDF_FOLDER = input("請輸入正確的PDF資料夾路徑: ").strip().strip('"')
        
        if not os.path.exists(PDF_FOLDER):
            print("❌ 無效路徑，程序結束")
            return
    
    # 創建完整提取器
    extractor = CompleteTableExtractor(OUTPUT_DIR)
    
    # 檢查可用引擎
    available_count = sum(1 for available in extractor.available_engines.values() if available)
    if available_count == 0:
        extractor._print("❌ 沒有可用的引擎，請安裝相關套件", "error")
        extractor._print("安裝建議:", "info")
        extractor._print("  pip install pdfplumber camelot-py[cv] PyMuPDF tabula-py openpyxl", "info")
        extractor._print("  Node.js: https://nodejs.org/ + npm install pdf2json", "info")
        return
    
    # 顯示引擎狀態
    if RICH_AVAILABLE:
        engine_table = Table(title="🔧 可用引擎狀態", box=box.ROUNDED)
        engine_table.add_column("引擎", style="cyan")
        engine_table.add_column("狀態", justify="center")
        engine_table.add_column("功能", style="dim")
        
        engine_info = {
            'pdfplumber': '完整表格提取+多格式保存',
            'camelot': '高精度提取+準確度評分',
            'pymupdf': '高效提取+結構分析',
            'tabula': 'Java核心+大表格支援',
            'nodejs': 'JavaScript引擎+結構化分析'
        }
        
        for engine, desc in engine_info.items():
            available = extractor.available_engines.get(engine, False)
            status = "✅ 可用" if available else "❌ 未安裝"
            style = "green" if available else "red"
            engine_table.add_row(engine, f"[{style}]{status}[/{style}]", desc)
        
        console.print(engine_table)
    
    extractor._print(f"✅ 系統就緒，將執行完整表格提取", "success")
    
    # 開始批量完整提取
    try:
        extractor.batch_process_complete_extraction(PDF_FOLDER, ENGINES)
        extractor._print("\n🎉 所有PDF的表格都已完整提取並保存！", "success")
        
    except KeyboardInterrupt:
        extractor._print("\n⚠️  用戶中斷處理", "warning")
    except Exception as e:
        extractor._print(f"\n❌ 處理失敗: {str(e)}", "error")


if __name__ == "__main__":
    main()


# ==========================================
# 💡 完整功能說明
# ==========================================
"""
🎯 每個引擎的完整寫入功能:

📊 PDFPlumber:
• CSV格式 (UTF-8編碼)
• Excel格式 (.xlsx)
• JSON格式 (含元數據)

🎯 Camelot:
• CSV格式 + Camelot原生CSV
• Excel格式
• JSON格式 (含準確度評分)

🚀 PyMuPDF:
• CSV格式
• Excel格式  
• JSON格式 (含座標信息)
• 文本分析降級處理

☕ Tabula:
• CSV格式 (智能標題識別)
• Excel格式
• JSON格式

⚡ JavaScript:
• JSON格式 (結構化數據)
• CSV格式 (從結構分析生成)

📁 輸出目錄結構:
complete_extraction/
├── pdfplumber/
│   └── [PDF名稱]/
│       ├── page_001_table_01.csv
│       ├── page_001_table_01.xlsx
│       └── page_001_table_01.json
├── camelot/
├── pymupdf/
├── tabula/
└── javascript/

📊 批量處理特色:
• 每個PDF生成詳細的提取日誌
• 批量處理摘要報告
• 錯誤處理和恢復機制
• 進度顯示和狀態監控

🔧 使用方式:
1. 修改 PDF_FOLDER 路徑
2. 運行: python complete_table_extractor.py
3. 查看結果目錄中的完整提取文件
"""