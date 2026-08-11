#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  VRN_M04_OCR_PostProcessor_LEGO_Ultra.py                                     ║
║  Version: 2.0.0 | LEGO Architecture | 金額/日期/表格擷取                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  功能只增不減 | Pipeline Compliant | 合約/財務文件專用                         ║
║  Features: price-parser + dateparser + camelot                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

v2.0.0 Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- price-parser: 精準擷取各種格式的金額 (NT$, USD, ¥, €, etc.)
- dateparser: 智慧解析各種日期格式 (中文、英文、數字)
- camelot: 複雜表格識別與結構化 (PDF 表格)
- Regex fallback: 當套件不可用時的備用方案
"""

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


import sys
import os
import argparse
import logging
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 0: MODULE METADATA
# ═══════════════════════════════════════════════════════════════════════════════
__module_id__ = "M04"
__module_name__ = "OCR_PostProcessor_LEGO_Ultra"
__version__ = "2.0.0"
__author__ = "VRN Team"
__description__ = "OCR Post-processing with price/date/table extraction"
__dependencies__ = ["price-parser", "dateparser", "camelot-py", "pandas", "ghostscript"]

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
class ExtractedPrice:
    """擷取的金額"""
    raw_text: str                 # 原始文字
    amount: float                 # 金額數值
    currency: str                 # 幣別 (TWD, USD, etc.)
    amount_text: str              # 格式化金額文字
    position: int = -1            # 在原文中的位置
    confidence: float = 1.0

@dataclass
class ExtractedDate:
    """擷取的日期"""
    raw_text: str                 # 原始文字
    parsed_date: str              # 解析後日期 (ISO format)
    year: int = 0
    month: int = 0
    day: int = 0
    date_type: str = ""           # 合約日期、到期日、簽約日 etc.
    position: int = -1
    confidence: float = 1.0

@dataclass
class ExtractedTable:
    """擷取的表格"""
    table_id: int
    rows: int
    cols: int
    headers: List[str]
    data: List[List[str]]
    raw_df: Optional[Any] = None  # pandas DataFrame

@dataclass
class PostProcessResult:
    """後處理結果"""
    doc_id: str
    source_file: str
    ocr_text: str                 # 原始 OCR 文字
    cleaned_text: str             # 清理後文字
    
    # 擷取結果
    prices: List[Dict] = field(default_factory=list)
    dates: List[Dict] = field(default_factory=list)
    tables: List[Dict] = field(default_factory=list)
    
    # 統計
    price_count: int = 0
    date_count: int = 0
    table_count: int = 0
    
    # 處理資訊
    processing_time_ms: float = 0.0
    extractors_used: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ProcessingStats:
    """處理統計"""
    total_files: int = 0
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    total_prices: int = 0
    total_dates: int = 0
    total_tables: int = 0
    total_time_ms: float = 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: PRICE EXTRACTOR (price-parser + regex fallback)
# ═══════════════════════════════════════════════════════════════════════════════
class PriceExtractor:
    """金額擷取器"""
    
    # 幣別符號映射
    CURRENCY_MAP = {
        'NT$': 'TWD', 'NT＄': 'TWD', 'NTD': 'TWD', '新台幣': 'TWD', '台幣': 'TWD', '元': 'TWD',
        '$': 'USD', 'US$': 'USD', 'USD': 'USD', '美元': 'USD', '美金': 'USD',
        '¥': 'CNY', 'RMB': 'CNY', '人民幣': 'CNY', '元人民幣': 'CNY',
        '€': 'EUR', 'EUR': 'EUR', '歐元': 'EUR',
        '£': 'GBP', 'GBP': 'GBP', '英鎊': 'GBP',
        '¥': 'JPY', 'JPY': 'JPY', '日圓': 'JPY', '日元': 'JPY',
    }
    
    # Regex patterns for prices
    PRICE_PATTERNS = [
        # NT$1,234,567.89 or NT$ 1,234,567.89
        r'(?:NT\$|NTD|新台幣|台幣)\s*([\d,]+(?:\.\d{1,2})?)',
        # $1,234.56 or US$1,234.56
        r'(?:US\$|\$|USD)\s*([\d,]+(?:\.\d{1,2})?)',
        # ¥1,234 or RMB 1,234
        r'(?:¥|RMB|人民幣)\s*([\d,]+(?:\.\d{1,2})?)',
        # €1,234.56
        r'(?:€|EUR|歐元)\s*([\d,]+(?:\.\d{1,2})?)',
        # 1,234,567 元 or 1,234,567元
        r'([\d,]+(?:\.\d{1,2})?)\s*(?:元|塊|圓)',
        # 金額: 1,234,567
        r'(?:金額|總價|價格|費用|成本)[：:]\s*([\d,]+(?:\.\d{1,2})?)',
    ]
    
    def __init__(self):
        self.price_parser_available = False
        self._init()
    
    def _init(self):
        """初始化 price-parser"""
        try:
            from price_parser import Price
            self.price_parser_available = True
            logger.info("✅ price-parser available")
        except ImportError:
            logger.warning("⚠️ price-parser unavailable (pip install price-parser)")
    
    def extract_prices(self, text: str) -> List[ExtractedPrice]:
        """擷取所有金額"""
        prices = []
        
        # Method 1: price-parser
        if self.price_parser_available:
            prices.extend(self._extract_with_price_parser(text))
        
        # Method 2: Regex fallback
        prices.extend(self._extract_with_regex(text))
        
        # 去重複 (基於金額和位置)
        seen = set()
        unique_prices = []
        for p in prices:
            key = (p.amount, p.currency)
            if key not in seen:
                seen.add(key)
                unique_prices.append(p)
        
        return unique_prices
    
    def _extract_with_price_parser(self, text: str) -> List[ExtractedPrice]:
        """使用 price-parser 擷取"""
        from price_parser import Price
        
        prices = []
        
        # 分割成可能包含價格的片段
        segments = re.split(r'[,，。\n\r]+', text)
        
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            
            # 尋找包含數字的片段
            if re.search(r'\d', seg):
                price = Price.fromstring(seg)
                
                if price.amount is not None:
                    currency = price.currency or 'TWD'
                    
                    # 映射幣別
                    for symbol, code in self.CURRENCY_MAP.items():
                        if symbol in seg:
                            currency = code
                            break
                    
                    prices.append(ExtractedPrice(
                        raw_text=seg,
                        amount=float(price.amount),
                        currency=currency,
                        amount_text=price.amount_text or str(price.amount),
                        confidence=0.9
                    ))
        
        return prices
    
    def _extract_with_regex(self, text: str) -> List[ExtractedPrice]:
        """使用 Regex 擷取"""
        prices = []
        
        for pattern in self.PRICE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    raw_text = match.group(0)
                    amount_str = match.group(1)
                    
                    # 移除千分位逗號
                    amount = float(amount_str.replace(',', ''))
                    
                    # 判斷幣別
                    currency = 'TWD'  # 預設
                    for symbol, code in self.CURRENCY_MAP.items():
                        if symbol in raw_text:
                            currency = code
                            break
                    
                    prices.append(ExtractedPrice(
                        raw_text=raw_text,
                        amount=amount,
                        currency=currency,
                        amount_text=f"{amount:,.2f}",
                        position=match.start(),
                        confidence=0.8
                    ))
                except (ValueError, IndexError):
                    continue
        
        return prices

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: DATE EXTRACTOR (dateparser + regex fallback)
# ═══════════════════════════════════════════════════════════════════════════════
class DateExtractor:
    """日期擷取器"""
    
    # 日期類型關鍵字
    DATE_TYPE_KEYWORDS = {
        '合約日期': ['合約日期', '契約日期', '合同日期'],
        '簽約日': ['簽約日', '簽訂日', '訂約日', '締約日'],
        '生效日': ['生效日', '起始日', '開始日', '起日'],
        '到期日': ['到期日', '截止日', '終止日', '結束日', '迄日'],
        '付款日': ['付款日', '繳款日', '支付日'],
        '交貨日': ['交貨日', '出貨日', '送達日'],
    }
    
    # Regex patterns for dates
    DATE_PATTERNS = [
        # 民國年: 113年12月31日 or 113/12/31
        (r'(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', 'roc'),
        (r'(\d{2,3})[/\-](\d{1,2})[/\-](\d{1,2})', 'roc_slash'),
        # 西元年: 2024年12月31日 or 2024/12/31
        (r'(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', 'ad'),
        (r'(20\d{2})[/\-](\d{1,2})[/\-](\d{1,2})', 'ad_slash'),
        # ISO: 2024-12-31
        (r'(20\d{2})-(\d{2})-(\d{2})', 'iso'),
        # 中文: 二〇二四年十二月三十一日
        (r'([二零〇一三四五六七八九]+)年([一二三四五六七八九十]+)月([一二三四五六七八九十]+)日', 'chinese'),
    ]
    
    def __init__(self):
        self.dateparser_available = False
        self._init()
    
    def _init(self):
        """初始化 dateparser"""
        try:
            import dateparser
            self.dateparser_available = True
            logger.info("✅ dateparser available")
        except ImportError:
            logger.warning("⚠️ dateparser unavailable (pip install dateparser)")
    
    def extract_dates(self, text: str) -> List[ExtractedDate]:
        """擷取所有日期"""
        dates = []
        
        # Method 1: dateparser
        if self.dateparser_available:
            dates.extend(self._extract_with_dateparser(text))
        
        # Method 2: Regex
        dates.extend(self._extract_with_regex(text))
        
        # 去重複
        seen = set()
        unique_dates = []
        for d in dates:
            key = d.parsed_date
            if key not in seen:
                seen.add(key)
                unique_dates.append(d)
        
        return unique_dates
    
    def _extract_with_dateparser(self, text: str) -> List[ExtractedDate]:
        """使用 dateparser 擷取"""
        import dateparser
        
        dates = []
        
        # 分割文字
        segments = re.split(r'[,，。\n\r]+', text)
        
        for seg in segments:
            seg = seg.strip()
            if not seg or len(seg) > 50:
                continue
            
            # 嘗試解析
            parsed = dateparser.parse(
                seg,
                languages=['zh', 'en'],
                settings={
                    'PREFER_DAY_OF_MONTH': 'first',
                    'PREFER_DATES_FROM': 'past',
                    'DATE_ORDER': 'YMD'
                }
            )
            
            if parsed:
                date_type = self._detect_date_type(seg)
                
                dates.append(ExtractedDate(
                    raw_text=seg,
                    parsed_date=parsed.strftime('%Y-%m-%d'),
                    year=parsed.year,
                    month=parsed.month,
                    day=parsed.day,
                    date_type=date_type,
                    confidence=0.9
                ))
        
        return dates
    
    def _extract_with_regex(self, text: str) -> List[ExtractedDate]:
        """使用 Regex 擷取"""
        dates = []
        
        for pattern, fmt in self.DATE_PATTERNS:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                try:
                    raw_text = match.group(0)
                    
                    if fmt in ['roc', 'roc_slash']:
                        # 民國年轉西元
                        year = int(match.group(1)) + 1911
                        month = int(match.group(2))
                        day = int(match.group(3))
                    elif fmt == 'chinese':
                        # 中文數字轉換
                        year = self._chinese_to_number(match.group(1))
                        month = self._chinese_to_number(match.group(2))
                        day = self._chinese_to_number(match.group(3))
                    else:
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                    
                    # 驗證日期
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        date_type = self._detect_date_type(text[max(0, match.start()-20):match.end()+5])
                        
                        dates.append(ExtractedDate(
                            raw_text=raw_text,
                            parsed_date=f"{year:04d}-{month:02d}-{day:02d}",
                            year=year,
                            month=month,
                            day=day,
                            date_type=date_type,
                            position=match.start(),
                            confidence=0.8
                        ))
                        
                except (ValueError, IndexError):
                    continue
        
        return dates
    
    def _detect_date_type(self, context: str) -> str:
        """偵測日期類型"""
        for date_type, keywords in self.DATE_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in context:
                    return date_type
        return ""
    
    def _chinese_to_number(self, chinese: str) -> int:
        """中文數字轉阿拉伯數字"""
        cn_num = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
                  '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        
        if not chinese:
            return 0
        
        result = 0
        temp = 0
        
        for char in chinese:
            if char in cn_num:
                num = cn_num[char]
                if num == 10:
                    if temp == 0:
                        temp = 1
                    result += temp * 10
                    temp = 0
                else:
                    temp = temp * 10 + num
        
        return result + temp

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: TABLE EXTRACTOR (camelot)
# ═══════════════════════════════════════════════════════════════════════════════
class TableExtractor:
    """表格擷取器 - 使用 Camelot"""
    
    def __init__(self):
        self.camelot_available = False
        self._init()
    
    def _init(self):
        """初始化 Camelot"""
        try:
            import camelot
            self.camelot_available = True
            logger.info("✅ camelot available")
        except ImportError:
            logger.warning("⚠️ camelot unavailable (pip install camelot-py[cv] ghostscript)")
    
    def extract_tables(self, file_path: str) -> List[ExtractedTable]:
        """從 PDF 擷取表格"""
        tables = []
        
        if not self.camelot_available:
            return tables
        
        # 只處理 PDF
        if not file_path.lower().endswith('.pdf'):
            return tables
        
        try:
            import camelot
            
            # 嘗試 lattice 模式 (有線框的表格)
            extracted = camelot.read_pdf(file_path, flavor='lattice', pages='all')
            
            if len(extracted) == 0:
                # 退回 stream 模式 (無線框的表格)
                extracted = camelot.read_pdf(file_path, flavor='stream', pages='all')
            
            for i, table in enumerate(extracted):
                df = table.df
                
                # 取得表頭
                headers = df.iloc[0].tolist() if len(df) > 0 else []
                
                # 取得資料
                data = df.iloc[1:].values.tolist() if len(df) > 1 else []
                
                tables.append(ExtractedTable(
                    table_id=i + 1,
                    rows=len(df),
                    cols=len(df.columns),
                    headers=headers,
                    data=data,
                    raw_df=df
                ))
            
            logger.info(f"   📊 Extracted {len(tables)} tables from PDF")
            
        except Exception as e:
            logger.warning(f"Table extraction error: {e}")
        
        return tables
    
    def extract_tables_from_text(self, text: str) -> List[ExtractedTable]:
        """從 OCR 文字中嘗試識別表格結構"""
        tables = []
        
        # 簡單的表格偵測 (基於分隔符或對齊)
        lines = text.split('\n')
        
        # 尋找可能的表格行 (包含多個 tab 或連續空格)
        table_lines = []
        for line in lines:
            # 偵測分隔符
            if '\t' in line or '|' in line or re.search(r'\s{3,}', line):
                table_lines.append(line)
            else:
                if len(table_lines) >= 3:  # 至少3行才算表格
                    table = self._parse_table_lines(table_lines)
                    if table:
                        tables.append(table)
                table_lines = []
        
        # 處理最後一個表格
        if len(table_lines) >= 3:
            table = self._parse_table_lines(table_lines)
            if table:
                tables.append(table)
        
        return tables
    
    def _parse_table_lines(self, lines: List[str]) -> Optional[ExtractedTable]:
        """解析表格行"""
        if not lines:
            return None
        
        # 分割各行
        rows = []
        for line in lines:
            # 使用 tab、| 或多空格分割
            if '|' in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
            elif '\t' in line:
                cells = [c.strip() for c in line.split('\t') if c.strip()]
            else:
                cells = re.split(r'\s{2,}', line.strip())
            
            if cells:
                rows.append(cells)
        
        if len(rows) < 2:
            return None
        
        return ExtractedTable(
            table_id=1,
            rows=len(rows),
            cols=max(len(r) for r in rows),
            headers=rows[0],
            data=rows[1:]
        )

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: TEXT CLEANER
# ═══════════════════════════════════════════════════════════════════════════════
class TextCleaner:
    """文字清理器"""
    
    @staticmethod
    def clean(text: str) -> str:
        """清理 OCR 文字"""
        if not text:
            return ""
        
        # 移除控制字元
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        
        # 標準化空白
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 移除多餘換行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 修正常見 OCR 錯誤
        replacements = {
            '〇': '0',
            'Ｏ': '0',
            'ｏ': '0',
            '－': '-',
            '．': '.',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: MAIN PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════
class M04Processor:
    """M04 後處理器"""
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.price_extractor = PriceExtractor()
        self.date_extractor = DateExtractor()
        self.table_extractor = TableExtractor()
        self.text_cleaner = TextCleaner()
        self.stats = ProcessingStats()
    
    def initialize(self) -> bool:
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info("🔧 M04 Post-Processor initialized")
        logger.info(f"   price-parser: {'✅' if self.price_extractor.price_parser_available else '⚠️ regex only'}")
        logger.info(f"   dateparser: {'✅' if self.date_extractor.dateparser_available else '⚠️ regex only'}")
        logger.info(f"   camelot: {'✅' if self.table_extractor.camelot_available else '⚠️ disabled'}")
        return True
    
    def process(self) -> ProcessingStats:
        logger.info("=" * 60)
        logger.info(f"🚀 VRN M04 Post-Processor v{__version__}")
        logger.info("=" * 60)
        logger.info(f"   Input : {self.input_path}")
        logger.info(f"   Output: {self.output_path}")
        
        start_time = time.time()
        
        # 發現檔案 (主要處理 M03 輸出的 JSON)
        files = self._discover_files()
        self.stats.total_files = len(files)
        
        logger.info(f"📁 Found: {len(files)} files")
        
        for file in files:
            self._process_file(file)
        
        self.stats.total_time_ms = (time.time() - start_time) * 1000
        self._log_summary()
        
        return self.stats
    
    def _discover_files(self) -> List[Path]:
        if not self.input_path.exists():
            return []
        
        if self.input_path.is_file():
            return [self.input_path]
        
        # JSON 和 PDF
        files = []
        for ext in ['*.json', '*.pdf', '*.txt']:
            files.extend(self.input_path.glob(ext))
        
        return sorted(files)
    
    def _process_file(self, file: Path):
        logger.info(f"   Processing: {file.name}...")
        
        start_time = time.time()
        
        try:
            # 讀取內容
            ocr_text = ""
            source_data = {}
            
            if file.suffix.lower() == '.json':
                with open(file, 'r', encoding='utf-8') as f:
                    source_data = json.load(f)
                ocr_text = source_data.get('ocr_text', '')
            elif file.suffix.lower() == '.txt':
                with open(file, 'r', encoding='utf-8') as f:
                    ocr_text = f.read()
            elif file.suffix.lower() == '.pdf':
                # PDF 直接用 camelot 處理表格
                pass
            
            # 清理文字
            cleaned_text = self.text_cleaner.clean(ocr_text)
            
            # 擷取金額
            prices = self.price_extractor.extract_prices(cleaned_text)
            
            # 擷取日期
            dates = self.date_extractor.extract_dates(cleaned_text)
            
            # 擷取表格
            tables = []
            if file.suffix.lower() == '.pdf':
                tables = self.table_extractor.extract_tables(str(file))
            else:
                tables = self.table_extractor.extract_tables_from_text(cleaned_text)
            
            # 建立結果
            elapsed = (time.time() - start_time) * 1000
            
            result = PostProcessResult(
                doc_id=file.stem,
                source_file=str(file.name),
                ocr_text=ocr_text,
                cleaned_text=cleaned_text,
                prices=[asdict(p) for p in prices],
                dates=[asdict(d) for d in dates],
                tables=[{
                    'table_id': t.table_id,
                    'rows': t.rows,
                    'cols': t.cols,
                    'headers': t.headers,
                    'data': t.data
                } for t in tables],
                price_count=len(prices),
                date_count=len(dates),
                table_count=len(tables),
                processing_time_ms=elapsed,
                extractors_used=self._get_extractors_used()
            )
            
            # 保存結果
            self._save_result(result)
            
            # 更新統計
            self.stats.processed += 1
            self.stats.succeeded += 1
            self.stats.total_prices += len(prices)
            self.stats.total_dates += len(dates)
            self.stats.total_tables += len(tables)
            
            status = f"✅ {len(prices)} prices, {len(dates)} dates, {len(tables)} tables"
            logger.info(f"   {status}")
            
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            self.stats.processed += 1
            self.stats.failed += 1
    
    def _get_extractors_used(self) -> List[str]:
        used = []
        if self.price_extractor.price_parser_available:
            used.append("price-parser")
        used.append("price-regex")
        if self.date_extractor.dateparser_available:
            used.append("dateparser")
        used.append("date-regex")
        if self.table_extractor.camelot_available:
            used.append("camelot")
        return used
    
    def _save_result(self, result: PostProcessResult):
        out_file = self.output_path / f"{result.doc_id}_m04.json"
        
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)
    
    def _log_summary(self):
        logger.info("=" * 60)
        logger.info(f"🏁 M04 Complete | {self.stats.succeeded}/{self.stats.total_files} succeeded")
        logger.info(f"   Prices: {self.stats.total_prices} | Dates: {self.stats.total_dates} | Tables: {self.stats.total_tables}")
        logger.info(f"   Time: {self.stats.total_time_ms:.1f}ms")
        logger.info("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: CLI
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description=f"VRN M04 Post-Processor v{__version__}")
    
    parser.add_argument("--input", "-i", help="Input directory or file")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--input_dir", help="Input (legacy)")
    parser.add_argument("--output_dir", help="Output (legacy)")
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
    
    processor = M04Processor(input_path, output_path)
    processor.initialize()
    stats = processor.process()
    
    sys.exit(0 if stats.succeeded > 0 else 1)


if __name__ == "__main__":
    main()
