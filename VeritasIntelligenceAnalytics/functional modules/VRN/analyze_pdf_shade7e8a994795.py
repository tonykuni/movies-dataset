#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║              VeritasReportNova™ Multi-Engine PDF Analyzer                     ║
║                     Python Backend Processing Engine                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

支援引擎:
- PyMuPDF (fitz): 高速文本提取與頁面渲染
- Camelot: 專業表格檢測與提取
- pdfplumber: 文本與表格混合分析
- PaddleOCR: OCR文字識別
- Tesseract: 備用OCR引擎

Author: Tony K.
Version: 2.0.0
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# 依賴檢查與導入
# ═══════════════════════════════════════════════════════════════════════════════

REQUIRED_PACKAGES = {
    'pymupdf': 'PyMuPDF',
    'camelot': 'camelot-py[cv]',
    'pdfplumber': 'pdfplumber',
    'paddleocr': 'paddleocr',
    'pytesseract': 'pytesseract'
}

def check_dependencies():
    """檢查並報告缺失的依賴"""
    missing = []
    available_engines = []
    
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
            available_engines.append(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        logging.warning(f"缺失依賴: {', '.join(missing)}")
        logging.info(f"安裝命令: pip install {' '.join(missing)} --break-system-packages")
    
    return available_engines

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import camelot
    HAS_CAMELOT = True
except ImportError:
    HAS_CAMELOT = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# ═══════════════════════════════════════════════════════════════════════════════
# 日誌配置
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('VRN-PDF-Analyzer')

# ═══════════════════════════════════════════════════════════════════════════════
# 引擎抽象基類
# ═══════════════════════════════════════════════════════════════════════════════

class PDFEngine:
    """PDF分析引擎基類"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.results = {}
        
    def extract_text(self) -> Dict[str, Any]:
        """提取文本內容"""
        raise NotImplementedError
        
    def extract_tables(self) -> List[Dict[str, Any]]:
        """提取表格結構"""
        raise NotImplementedError
        
    def get_metadata(self) -> Dict[str, Any]:
        """獲取PDF元數據"""
        raise NotImplementedError

# ═══════════════════════════════════════════════════════════════════════════════
# PyMuPDF引擎實現
# ═══════════════════════════════════════════════════════════════════════════════

class PyMuPDFEngine(PDFEngine):
    """PyMuPDF高速引擎"""
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.doc = fitz.open(str(self.pdf_path))
        
    def extract_text(self) -> Dict[str, Any]:
        """提取全文本"""
        logger.info(f"PyMuPDF: 提取文本 ({len(self.doc)} 頁)")
        
        pages = []
        for page_num, page in enumerate(self.doc, start=1):
            text = page.get_text("text")
            blocks = page.get_text("blocks")
            
            pages.append({
                'page_number': page_num,
                'text': text,
                'blocks': len(blocks),
                'width': page.rect.width,
                'height': page.rect.height
            })
        
        return {
            'engine': 'PyMuPDF',
            'total_pages': len(self.doc),
            'pages': pages,
            'extraction_time': datetime.now().isoformat()
        }
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """PyMuPDF不直接支持表格提取"""
        logger.warning("PyMuPDF: 不支援直接表格提取,建議使用Camelot")
        return []
    
    def get_metadata(self) -> Dict[str, Any]:
        """獲取PDF元數據"""
        metadata = self.doc.metadata
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'mod_date': metadata.get('modDate', ''),
            'page_count': len(self.doc)
        }
    
    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()

# ═══════════════════════════════════════════════════════════════════════════════
# Camelot引擎實現
# ═══════════════════════════════════════════════════════════════════════════════

class CamelotEngine(PDFEngine):
    """Camelot專業表格引擎"""
    
    def extract_tables(self, flavor='lattice', pages='all') -> List[Dict[str, Any]]:
        """提取表格結構
        
        Args:
            flavor: 'lattice' (帶邊框) 或 'stream' (無邊框)
            pages: 'all' 或 '1,2,3' 或 '1-5'
        """
        logger.info(f"Camelot: 提取表格 (flavor={flavor}, pages={pages})")
        
        try:
            tables = camelot.read_pdf(
                str(self.pdf_path),
                flavor=flavor,
                pages=pages
            )
            
            results = []
            for idx, table in enumerate(tables, start=1):
                results.append({
                    'table_id': idx,
                    'page': table.page,
                    'accuracy': table.accuracy,
                    'whitespace': table.whitespace,
                    'order': table.order,
                    'shape': table.df.shape,
                    'data': table.df.to_dict('records')
                })
            
            logger.info(f"Camelot: 找到 {len(tables)} 個表格")
            return results
            
        except Exception as e:
            logger.error(f"Camelot提取失敗: {e}")
            return []
    
    def extract_text(self) -> Dict[str, Any]:
        """Camelot專注表格,不提供文本提取"""
        return {'engine': 'Camelot', 'note': 'Use PyMuPDF for text extraction'}
    
    def get_metadata(self) -> Dict[str, Any]:
        return {}

# ═══════════════════════════════════════════════════════════════════════════════
# pdfplumber引擎實現
# ═══════════════════════════════════════════════════════════════════════════════

class PdfPlumberEngine(PDFEngine):
    """pdfplumber混合引擎"""
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.pdf = pdfplumber.open(str(self.pdf_path))
        
    def extract_text(self) -> Dict[str, Any]:
        """提取文本"""
        logger.info(f"pdfplumber: 提取文本 ({len(self.pdf.pages)} 頁)")
        
        pages = []
        for page_num, page in enumerate(self.pdf.pages, start=1):
            text = page.extract_text()
            
            pages.append({
                'page_number': page_num,
                'text': text or '',
                'width': page.width,
                'height': page.height,
                'chars': len(page.chars)
            })
        
        return {
            'engine': 'pdfplumber',
            'total_pages': len(self.pdf.pages),
            'pages': pages,
            'extraction_time': datetime.now().isoformat()
        }
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """提取表格"""
        logger.info("pdfplumber: 提取表格")
        
        all_tables = []
        table_counter = 0
        
        for page_num, page in enumerate(self.pdf.pages, start=1):
            tables = page.extract_tables()
            
            for table in tables:
                table_counter += 1
                all_tables.append({
                    'table_id': table_counter,
                    'page': page_num,
                    'rows': len(table),
                    'cols': len(table[0]) if table else 0,
                    'data': table
                })
        
        logger.info(f"pdfplumber: 找到 {len(all_tables)} 個表格")
        return all_tables
    
    def get_metadata(self) -> Dict[str, Any]:
        """獲取元數據"""
        metadata = self.pdf.metadata or {}
        return {
            'title': metadata.get('Title', ''),
            'author': metadata.get('Author', ''),
            'subject': metadata.get('Subject', ''),
            'creator': metadata.get('Creator', ''),
            'producer': metadata.get('Producer', ''),
            'page_count': len(self.pdf.pages)
        }
    
    def __del__(self):
        if hasattr(self, 'pdf'):
            self.pdf.close()

# ═══════════════════════════════════════════════════════════════════════════════
# 主分析協調器
# ═══════════════════════════════════════════════════════════════════════════════

class PDFAnalyzer:
    """多引擎PDF分析協調器"""
    
    def __init__(self, pdf_path: str, engines: List[str] = None):
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 確定可用引擎
        self.available_engines = check_dependencies()
        self.engines = engines or self.available_engines
        
        logger.info(f"初始化分析器: {self.pdf_path.name}")
        logger.info(f"使用引擎: {', '.join(self.engines)}")
        
    def analyze(self, extract_text=True, extract_tables=True, extract_metadata=True) -> Dict[str, Any]:
        """執行完整分析"""
        results = {
            'file': str(self.pdf_path),
            'timestamp': datetime.now().isoformat(),
            'engines_used': self.engines,
            'text': {},
            'tables': {},
            'metadata': {}
        }
        
        # 文本提取
        if extract_text:
            if 'pymupdf' in self.engines and HAS_PYMUPDF:
                engine = PyMuPDFEngine(str(self.pdf_path))
                results['text']['pymupdf'] = engine.extract_text()
                results['metadata']['pymupdf'] = engine.get_metadata()
            
            if 'pdfplumber' in self.engines and HAS_PDFPLUMBER:
                engine = PdfPlumberEngine(str(self.pdf_path))
                results['text']['pdfplumber'] = engine.extract_text()
                results['metadata']['pdfplumber'] = engine.get_metadata()
        
        # 表格提取
        if extract_tables:
            if 'camelot' in self.engines and HAS_CAMELOT:
                engine = CamelotEngine(str(self.pdf_path))
                results['tables']['camelot'] = engine.extract_tables()
            
            if 'pdfplumber' in self.engines and HAS_PDFPLUMBER:
                engine = PdfPlumberEngine(str(self.pdf_path))
                results['tables']['pdfplumber'] = engine.extract_tables()
        
        return results
    
    def save_results(self, results: Dict[str, Any], output_path: Optional[str] = None):
        """保存分析結果"""
        if output_path is None:
            output_path = self.pdf_path.with_suffix('.analysis.json')
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"結果已保存: {output_path}")
        return output_path

# ═══════════════════════════════════════════════════════════════════════════════
# 命令行介面
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='VeritasReportNova™ PDF Multi-Engine Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('pdf', help='PDF文件路徑')
    parser.add_argument('-e', '--engines', nargs='+', 
                       choices=['pymupdf', 'camelot', 'pdfplumber', 'paddleocr', 'tesseract'],
                       help='指定使用的引擎')
    parser.add_argument('-o', '--output', help='輸出JSON文件路徑')
    parser.add_argument('--no-text', action='store_true', help='不提取文本')
    parser.add_argument('--no-tables', action='store_true', help='不提取表格')
    parser.add_argument('--no-metadata', action='store_true', help='不提取元數據')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # 創建分析器
        analyzer = PDFAnalyzer(args.pdf, args.engines)
        
        # 執行分析
        logger.info("開始分析...")
        results = analyzer.analyze(
            extract_text=not args.no_text,
            extract_tables=not args.no_tables,
            extract_metadata=not args.no_metadata
        )
        
        # 保存結果
        output_path = analyzer.save_results(results, args.output)
        
        # 輸出摘要
        print(json.dumps({
            'status': 'success',
            'output': str(output_path),
            'engines_used': results['engines_used'],
            'timestamp': results['timestamp']
        }, indent=2))
        
        return 0
        
    except Exception as e:
        logger.error(f"分析失敗: {e}", exc_info=args.verbose)
        print(json.dumps({
            'status': 'error',
            'message': str(e)
        }, indent=2))
        return 1

if __name__ == '__main__':
    sys.exit(main())
