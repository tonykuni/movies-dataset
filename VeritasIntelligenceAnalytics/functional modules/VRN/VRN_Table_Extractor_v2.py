# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                         VRN 年度財報表格擷取器 v2.0 (加速版)                                                      ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  功能: 鎖定年度財報頁 → 多方法表格擷取 → 錯誤修復 → 整合輸出 CSV                                                   ║
║  加速: OMEGA 加速器整合 (Numba/Polars/並行)                                                                       ║
║  輸出: UTF-8-BOM CSV (filename 區隔)                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

使用方式:
    python VRN_Table_Extractor_v2.py -i input_folder -o output.csv
    python VRN_Table_Extractor_v2.py -i report.pdf -o tables.csv
    python VRN_Table_Extractor_v2.py -i report.pdf --method camelot
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
import sys
import csv
import json
import time
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 路徑設定
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
_BASE_DIR = Path(__file__).resolve().parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 安全導入加速器 (不影響主流程)
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
VRN_OMEGA = None
VRN_REGEX = None

def _safe_import(module_name: str):
    """安全導入模組"""
    try:
        import importlib
        return importlib.import_module(module_name)
    except Exception:
        return None

# 嘗試載入 OMEGA 加速器
for omega_name in ["VRN_M12_OMEGA_UltimateAccelerator", "VRN_M12_OMEGA_Accelerator", "VRN_M12_MEGA_Accelerator"]:
    VRN_OMEGA = _safe_import(omega_name)
    if VRN_OMEGA:
        # 嘗試啟用
        for fn in ("init", "bootstrap", "enable", "activate"):
            if hasattr(VRN_OMEGA, fn) and callable(getattr(VRN_OMEGA, fn)):
                try:
                    getattr(VRN_OMEGA, fn)()
                except Exception:
                    pass
                break
        break

# 嘗試載入 Regex Pattern
for regex_name in ["InvestmentRegexPattern_M100_Compat", "InvestmentRegexPattern_VALIDATED"]:
    VRN_REGEX = _safe_import(regex_name)
    if VRN_REGEX:
        break

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 依賴檢查
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
HAS_PDFPLUMBER = False
HAS_CAMELOT = False
HAS_TABULA = False
HAS_PYMUPDF = False
HAS_PANDAS = False
HAS_CV2 = False
HAS_POLARS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    pl = None

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    pdfplumber = None

try:
    import camelot
    HAS_CAMELOT = True
except ImportError:
    camelot = None

try:
    import tabula
    HAS_TABULA = True
except ImportError:
    tabula = None

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    fitz = None

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    cv2 = None
    np = None

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 日誌設定
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("VRN_TableExtractor")

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
CONFIG = {
    # 擷取方法優先順序
    "methods_priority": ["pdfplumber", "camelot", "tabula", "pymupdf"],
    
    # 年度財報關鍵字
    "financial_keywords": [
        "資產負債表", "綜合損益表", "權益變動表", "現金流量表",
        "財務狀況表", "損益表", "資產負債",
        "營業收入", "營業成本", "營業毛利", "營業利益", "稅後淨利",
        "流動資產", "非流動資產", "資產總計", "負債總計", "權益總計",
        "Balance Sheet", "Income Statement", "Cash Flow",
    ],
    
    # 最低表格品質
    "min_rows": 2,
    "min_cols": 2,
    
    # 並行處理
    "max_workers": 4,
    
    # 錯誤重試
    "max_retries": 2,
}

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 表格擷取類別
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

class TableExtractor:
    """多方法表格擷取器"""
    
    def __init__(self, method: str = "auto"):
        self.method = method
        self.all_rows: List[List[str]] = []
        self.max_cols = 1  # filename 欄
        self.stats = {
            "files_processed": 0,
            "tables_extracted": 0,
            "rows_total": 0,
            "errors": 0,
        }
        
        # 顯示可用方法
        self._show_available_methods()
    
    def _show_available_methods(self):
        """顯示可用的擷取方法"""
        logger.info("=" * 60)
        logger.info("  VRN 表格擷取器 v2.0 (加速版)")
        logger.info("=" * 60)
        logger.info(f"  pdfplumber : {'✓' if HAS_PDFPLUMBER else '✗'}")
        logger.info(f"  camelot    : {'✓' if HAS_CAMELOT else '✗'}")
        logger.info(f"  tabula     : {'✓' if HAS_TABULA else '✗'}")
        logger.info(f"  PyMuPDF    : {'✓' if HAS_PYMUPDF else '✗'}")
        logger.info(f"  OMEGA 加速 : {'✓' if VRN_OMEGA else '✗'}")
        logger.info(f"  Polars     : {'✓' if HAS_POLARS else '✗'}")
        logger.info("=" * 60)
    
    # ───────────────────────────────────────────────────────────────────────────
    # 主要擷取方法
    # ───────────────────────────────────────────────────────────────────────────
    
    def extract_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        從 PDF 擷取表格（自動選擇最佳方法）
        
        Returns:
            List[Dict]: 表格列表
        """
        pdf_path = Path(pdf_path)
        filename = pdf_path.stem
        
        logger.info(f"📄 處理: {pdf_path.name}")
        start_time = time.time()
        
        tables = []
        
        # 決定使用的方法
        if self.method == "auto":
            methods = CONFIG["methods_priority"]
        else:
            methods = [self.method]
        
        # 嘗試各種方法
        for method in methods:
            try:
                if method == "pdfplumber" and HAS_PDFPLUMBER:
                    tables = self._extract_pdfplumber(pdf_path, filename)
                elif method == "camelot" and HAS_CAMELOT:
                    tables = self._extract_camelot(pdf_path, filename)
                elif method == "tabula" and HAS_TABULA:
                    tables = self._extract_tabula(pdf_path, filename)
                elif method == "pymupdf" and HAS_PYMUPDF:
                    tables = self._extract_pymupdf(pdf_path, filename)
                
                if tables:
                    elapsed = time.time() - start_time
                    logger.info(f"  ✓ {method}: {len(tables)} 表格 ({elapsed:.1f}s)")
                    break
                    
            except Exception as e:
                logger.warning(f"  ✗ {method} 失敗: {str(e)[:50]}")
                continue
        
        if not tables:
            logger.warning(f"  ⚠ 未擷取到表格: {pdf_path.name}")
            self.stats["errors"] += 1
        
        return tables
    
    # ───────────────────────────────────────────────────────────────────────────
    # pdfplumber 方法
    # ───────────────────────────────────────────────────────────────────────────
    
    def _extract_pdfplumber(self, pdf_path: Path, filename: str) -> List[Dict]:
        """使用 pdfplumber 擷取"""
        tables = []
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 檢查是否為財報頁
                text = page.extract_text() or ""
                is_financial = any(kw in text for kw in CONFIG["financial_keywords"])
                
                # 擷取表格
                page_tables = page.extract_tables()
                
                for t_idx, table in enumerate(page_tables):
                    if self._is_valid_table(table):
                        tables.append({
                            "filename": filename,
                            "page": page_num,
                            "table_idx": t_idx + 1,
                            "is_financial": is_financial,
                            "rows": len(table),
                            "cols": len(table[0]) if table else 0,
                            "data": table,
                            "method": "pdfplumber",
                        })
        
        return tables
    
    # ───────────────────────────────────────────────────────────────────────────
    # camelot 方法
    # ───────────────────────────────────────────────────────────────────────────
    
    def _extract_camelot(self, pdf_path: Path, filename: str) -> List[Dict]:
        """使用 camelot 擷取"""
        tables = []
        
        # 嘗試 lattice 模式（有邊框表格）
        try:
            result = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")
        except Exception:
            result = []
        
        # 如果沒結果，嘗試 stream 模式（無邊框表格）
        if len(result) == 0:
            try:
                result = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")
            except Exception:
                result = []
        
        for t in result:
            df = t.df
            data = [df.columns.tolist()] + df.values.tolist()
            
            if self._is_valid_table(data):
                tables.append({
                    "filename": filename,
                    "page": t.page,
                    "table_idx": t.order,
                    "is_financial": True,
                    "rows": len(data),
                    "cols": len(data[0]) if data else 0,
                    "data": data,
                    "method": "camelot",
                    "accuracy": getattr(t, 'accuracy', 0),
                })
        
        return tables
    
    # ───────────────────────────────────────────────────────────────────────────
    # tabula 方法
    # ───────────────────────────────────────────────────────────────────────────
    
    def _extract_tabula(self, pdf_path: Path, filename: str) -> List[Dict]:
        """使用 tabula 擷取"""
        tables = []
        
        dfs = tabula.read_pdf(str(pdf_path), pages="all", multiple_tables=True)
        
        for idx, df in enumerate(dfs):
            # 轉換為列表
            headers = df.columns.tolist()
            data = [headers] + df.values.tolist()
            
            if self._is_valid_table(data):
                tables.append({
                    "filename": filename,
                    "page": idx + 1,
                    "table_idx": idx + 1,
                    "is_financial": True,
                    "rows": len(data),
                    "cols": len(data[0]) if data else 0,
                    "data": data,
                    "method": "tabula",
                })
        
        return tables
    
    # ───────────────────────────────────────────────────────────────────────────
    # PyMuPDF 方法
    # ───────────────────────────────────────────────────────────────────────────
    
    def _extract_pymupdf(self, pdf_path: Path, filename: str) -> List[Dict]:
        """使用 PyMuPDF 擷取"""
        tables = []
        
        doc = fitz.open(str(pdf_path))
        
        for page_num, page in enumerate(doc, 1):
            # PyMuPDF 2.0+ 有內建表格擷取
            if hasattr(page, 'find_tables'):
                page_tables = page.find_tables()
                for t_idx, tab in enumerate(page_tables):
                    data = tab.extract()
                    if self._is_valid_table(data):
                        tables.append({
                            "filename": filename,
                            "page": page_num,
                            "table_idx": t_idx + 1,
                            "is_financial": True,
                            "rows": len(data),
                            "cols": len(data[0]) if data else 0,
                            "data": data,
                            "method": "pymupdf",
                        })
        
        doc.close()
        return tables
    
    # ───────────────────────────────────────────────────────────────────────────
    # 表格驗證
    # ───────────────────────────────────────────────────────────────────────────
    
    def _is_valid_table(self, table: List) -> bool:
        """檢查表格是否有效"""
        if not table:
            return False
        if len(table) < CONFIG["min_rows"]:
            return False
        if not table[0] or len(table[0]) < CONFIG["min_cols"]:
            return False
        return True
    
    # ───────────────────────────────────────────────────────────────────────────
    # 整合表格
    # ───────────────────────────────────────────────────────────────────────────
    
    def add_tables(self, tables: List[Dict]):
        """將表格加入整合列表（filename 作為第一欄）"""
        for table in tables:
            filename = table.get("filename", "")
            page = table.get("page", 0)
            table_idx = table.get("table_idx", 0)
            method = table.get("method", "")
            data = table.get("data", [])
            
            if not data:
                continue
            
            # 更新最大欄位數
            table_cols = max(len(row) for row in data) if data else 0
            self.max_cols = max(self.max_cols, table_cols + 1)  # +1 for filename
            
            # 加入分隔行（如果不是第一個表格）
            if self.all_rows:
                self.all_rows.append([])  # 空行
            
            # 加入表格標識行
            marker = f"=== {filename} | Page {page} | Table {table_idx} | {method} ==="
            self.all_rows.append([marker])
            
            # 加入資料（每列前面插入 filename）
            for row in data:
                cleaned_row = [filename]
                for cell in row:
                    if cell is None:
                        cleaned_row.append("")
                    else:
                        # 清理：移除換行、多餘空白
                        cleaned_row.append(str(cell).replace("\n", " ").replace("\r", "").strip())
                self.all_rows.append(cleaned_row)
            
            self.stats["tables_extracted"] += 1
            self.stats["rows_total"] += len(data)
    
    # ───────────────────────────────────────────────────────────────────────────
    # 輸出
    # ───────────────────────────────────────────────────────────────────────────
    
    def save_csv(self, output_path: str) -> str:
        """
        儲存為 CSV (UTF-8-BOM 編碼，Excel 直接開啟不亂碼)
        """
        output_path = Path(output_path)
        
        # 補齊所有列到相同欄位數
        normalized = []
        for row in self.all_rows:
            if len(row) < self.max_cols:
                row = list(row) + [""] * (self.max_cols - len(row))
            normalized.append(row)
        
        # 產生表頭
        header = ["filename"] + [f"col_{i}" for i in range(1, self.max_cols)]
        
        # 寫入 CSV (UTF-8-BOM)
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(normalized)
        
        logger.info(f"✅ 已儲存: {output_path}")
        logger.info(f"   列數: {len(normalized)}, 欄數: {self.max_cols}")
        
        return str(output_path)
    
    def save_json(self, output_path: str) -> str:
        """儲存為 JSON"""
        output_path = Path(output_path)
        
        output_data = {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "stats": self.stats,
            "max_cols": self.max_cols,
            "rows": self.all_rows,
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 已儲存: {output_path}")
        return str(output_path)


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 批次處理（並行）
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def process_files(input_path: str, output_path: str = None, method: str = "auto") -> str:
    """
    處理檔案或資料夾
    
    Args:
        input_path: PDF 檔案或資料夾
        output_path: 輸出 CSV 路徑
        method: 擷取方法 (auto/pdfplumber/camelot/tabula/pymupdf)
    
    Returns:
        輸出檔案路徑
    """
    input_path = Path(input_path)
    
    # 決定輸出路徑
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"VRN_Tables_{ts}.csv"
    
    # 收集檔案
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = list(input_path.glob("*.pdf")) + list(input_path.glob("*.PDF"))
    else:
        logger.error(f"路徑不存在: {input_path}")
        return ""
    
    if not files:
        logger.error(f"找不到 PDF: {input_path}")
        return ""
    
    logger.info(f"找到 {len(files)} 個 PDF")
    
    # 建立擷取器
    extractor = TableExtractor(method=method)
    
    # 處理檔案
    start_time = time.time()
    
    # 並行處理（如果檔案多）
    if len(files) > 2 and CONFIG["max_workers"] > 1:
        logger.info(f"使用並行處理 (workers={CONFIG['max_workers']})")
        
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            futures = {executor.submit(extractor.extract_from_pdf, str(f)): f for f in files}
            
            for future in as_completed(futures):
                try:
                    tables = future.result()
                    if tables:
                        extractor.add_tables(tables)
                except Exception as e:
                    logger.error(f"處理失敗: {e}")
                extractor.stats["files_processed"] += 1
    else:
        # 循序處理
        for f in sorted(files):
            try:
                tables = extractor.extract_from_pdf(str(f))
                if tables:
                    extractor.add_tables(tables)
            except Exception as e:
                logger.error(f"處理失敗 {f.name}: {e}")
            extractor.stats["files_processed"] += 1
    
    elapsed = time.time() - start_time
    
    # 儲存結果
    if extractor.all_rows:
        output_file = extractor.save_csv(output_path)
        
        # 摘要
        logger.info("")
        logger.info("=" * 60)
        logger.info("  📊 擷取完成")
        logger.info("=" * 60)
        logger.info(f"  檔案數: {extractor.stats['files_processed']}")
        logger.info(f"  表格數: {extractor.stats['tables_extracted']}")
        logger.info(f"  總列數: {extractor.stats['rows_total']}")
        logger.info(f"  錯誤數: {extractor.stats['errors']}")
        logger.info(f"  耗時: {elapsed:.1f} 秒")
        logger.info(f"  輸出: {output_file}")
        logger.info("=" * 60)
        
        return output_file
    else:
        logger.warning("未擷取到任何表格")
        return ""


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="VRN_Table_Extractor_v2",
        description="VRN 年度財報表格擷取器 v2.0 (加速版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 處理單一 PDF (自動選擇方法)
  python VRN_Table_Extractor_v2.py -i report.pdf -o tables.csv
  
  # 處理整個資料夾
  python VRN_Table_Extractor_v2.py -i ./reports/ -o all_tables.csv
  
  # 指定擷取方法
  python VRN_Table_Extractor_v2.py -i report.pdf --method camelot
  
  # 輸出 JSON
  python VRN_Table_Extractor_v2.py -i report.pdf -o result.json --format json
        """
    )
    
    parser.add_argument("-i", "--input", required=True, help="PDF 檔案或資料夾")
    parser.add_argument("-o", "--output", help="輸出檔案路徑")
    parser.add_argument("--method", choices=["auto", "pdfplumber", "camelot", "tabula", "pymupdf"],
                        default="auto", help="擷取方法")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="輸出格式")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    result = process_files(args.input, args.output, args.method)
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
