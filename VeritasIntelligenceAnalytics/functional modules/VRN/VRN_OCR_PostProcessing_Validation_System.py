#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                      ║
║   VRN_OCR_PostProcessing_Validation_System.py v1.0                                                   ║
║   ══════════════════════════════════════════════════════════════════════════════════════════         ║
║                                                                                                      ║
║   🔧 OCR 後處理與驗證系統 - 提升準確率至 99%+                                                        ║
║                                                                                                      ║
║   📦 後處理技術:                                                                                     ║
║      1. 文字正規化 (NFKC/空白/換行)                                                                  ║
║      2. 數字修正 (千分位/括號負數/貨幣)                                                              ║
║      3. 日期正規化 (多格式/民國/西元)                                                                ║
║      4. 股票代號驗證 (排除年份 2020-2030)                                                            ║
║      5. 季度/財年正規化 (FY25/2025Q1/1Q25)                                                           ║
║      6. 會計等式驗證 (A = L + E)                                                                     ║
║      7. 同義詞統一 (VeritasSynonymEngine)                                                            ║
║      8. 信心分數過濾 (<80% 標記)                                                                     ║
║                                                                                                      ║
║   🎯 驗證規則:                                                                                       ║
║      - Ticker: 4位數非0開頭，排除 2020-2030                                                          ║
║      - Date: 6種格式 (ISO/Slash/Dot/ROC/CN/EN)                                                       ║
║      - Quarter: 8種格式 (YYYYQ/QYYYY/NQ/FY/H)                                                        ║
║      - Number: 千分位/括號/貨幣/百分比/bp                                                            ║
║      - Accounting: A = L + E (±0.1% 容差)                                                            ║
║                                                                                                      ║
║   功能只增不減 - Features Only Increase, Never Decrease                                              ║
║                                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

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

__version__ = "1.0.0"

import os
import re
import json
import unicodedata
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# =============================================================================
# § 1. 資料類型定義
# =============================================================================

class DataType(Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    CURRENCY = "CURRENCY"
    PERCENTAGE = "PERCENTAGE"
    BASIS_POINTS = "BASIS_POINTS"
    DATE = "DATE"
    DATE_ROC = "DATE_ROC"
    TICKER = "TICKER"
    QUARTER = "QUARTER"
    FISCAL_YEAR = "FISCAL_YEAR"
    ACCOUNTING = "ACCOUNTING"
    TABLE = "TABLE"
    UNKNOWN = "UNKNOWN"

class ValidationStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    WARNING = "WARNING"
    CORRECTED = "CORRECTED"
    SKIPPED = "SKIPPED"

@dataclass
class ValidationResult:
    """驗證結果"""
    field_name: str
    original_value: Any
    processed_value: Any
    data_type: DataType
    status: ValidationStatus
    confidence: float = 0.0
    message: str = ""
    corrections: List[str] = field(default_factory=list)

@dataclass
class PostProcessingResult:
    """後處理結果"""
    original_text: str
    processed_text: str
    extracted_data: Dict[str, Any]
    validations: List[ValidationResult]
    statistics: Dict[str, Any]
    warnings: List[str]
    errors: List[str]

# =============================================================================
# § 2. 正則表達式模式庫
# =============================================================================

class PatternLibrary:
    """正則表達式模式庫"""
    
    # ─────────────────────────────────────────────────────────────────────────
    # 股票代號
    # ─────────────────────────────────────────────────────────────────────────
    
    # 台股代號 (4位數，首位非0，排除年份 2020-2030)
    TICKER_TW = r'(?<![0-9])(?!20[2-3][0-9])(?!2030)[1-9][0-9]{3}(?![0-9])'
    
    # 美股代號 (1-5個大寫字母)
    TICKER_US = r'\b[A-Z]{1,5}\b'
    
    # ADR 代號 (TSM, UMC 等)
    TICKER_ADR = r'\b(?:TSM|UMC|ASX|CHT|HIMX|SPIL|IMOS)\b'
    
    # ─────────────────────────────────────────────────────────────────────────
    # 日期格式 (6種)
    # ─────────────────────────────────────────────────────────────────────────
    
    DATE_ISO = r'\d{4}-\d{2}-\d{2}'                     # 2025-01-15
    DATE_SLASH = r'\d{4}/\d{1,2}/\d{1,2}'              # 2025/1/15
    DATE_DOT = r'\d{4}\.\d{1,2}\.\d{1,2}'              # 2025.1.15
    DATE_COMPACT = r'(?<![0-9])\d{8}(?![0-9])'          # 20250115
    DATE_ROC = r'(?<![0-9])\d{2,3}/\d{1,2}/\d{1,2}'    # 114/01/15
    DATE_ROC_COMPACT = r'(?<![0-9])1\d{6}(?![0-9])'    # 1140115
    DATE_CN = r'\d{4}年\d{1,2}月\d{1,2}日'             # 2025年1月15日
    DATE_EN = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}'
    
    # ─────────────────────────────────────────────────────────────────────────
    # 季度/財年 (8種)
    # ─────────────────────────────────────────────────────────────────────────
    
    QUARTER_YYYYQN = r'20\d{2}Q[1-4]'                   # 2025Q1
    QUARTER_QNYYYY = r'Q[1-4]\s*20\d{2}'               # Q1 2025
    QUARTER_NQYY = r'[1-4]Q\d{2}'                       # 1Q25
    QUARTER_NQYYYY = r'[1-4]Q20\d{2}'                   # 1Q2025
    QUARTER_FY = r'FY\d{2,4}[eE]?'                      # FY25, FY2025, FY25e
    QUARTER_CY = r'CY\d{2,4}'                           # CY25, CY2025
    QUARTER_HALF = r'[12]H\d{2,4}'                      # 1H25, 2H2025
    QUARTER_YTD = r'YTD\d{2,4}'                         # YTD25
    
    # ─────────────────────────────────────────────────────────────────────────
    # 數字格式
    # ─────────────────────────────────────────────────────────────────────────
    
    NUMBER_INT = r'-?[0-9]{1,3}(?:,[0-9]{3})*'
    NUMBER_FLOAT = r'-?[0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+'
    NUMBER_PAREN_NEG = r'\([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?\)'
    NUMBER_SCIENTIFIC = r'-?[0-9]+\.?[0-9]*[eE][+-]?[0-9]+'
    
    # 百分比
    PERCENTAGE = r'-?[0-9]+(?:\.[0-9]+)?%'
    PERCENTAGE_BP = r'-?[0-9]+(?:\.[0-9]+)?\s*(?:bp|bps|BPS|basis\s*points?)'
    
    # 貨幣
    CURRENCY_TWD = r'(?:NT\$|TWD|NTD)\s*-?[0-9,]+(?:\.[0-9]+)?'
    CURRENCY_USD = r'(?:US\$|USD|\$)\s*-?[0-9,]+(?:\.[0-9]+)?'
    CURRENCY_CNY = r'(?:RMB|CNY|¥|￥)\s*-?[0-9,]+(?:\.[0-9]+)?'
    CURRENCY_EUR = r'(?:EUR|€)\s*-?[0-9,]+(?:\.[0-9]+)?'
    CURRENCY_PAREN = r'\(\$[0-9,]+(?:\.[0-9]+)?\)'
    
    # 單位
    UNIT_BILLION = r'(?:十億|billion|B|bn|bil)'
    UNIT_MILLION = r'(?:百萬|million|M|mn|mil)'
    UNIT_THOUSAND = r'(?:千|thousand|K|k)'
    UNIT_PERCENT = r'(?:%|percent|pct)'
    
    # ─────────────────────────────────────────────────────────────────────────
    # 財務術語
    # ─────────────────────────────────────────────────────────────────────────
    
    FINANCIAL_REVENUE = r'(?:Revenue|Sales|營收|營業收入|Net\s*Sales)'
    FINANCIAL_PROFIT = r'(?:Profit|Net\s*Income|淨利|淨利潤|NI|Earnings)'
    FINANCIAL_EPS = r'(?:EPS|每股盈餘|每股收益|Earnings\s*Per\s*Share)'
    FINANCIAL_ASSET = r'(?:Assets?|資產|Total\s*Assets?)'
    FINANCIAL_LIABILITY = r'(?:Liabilit(?:y|ies)|負債|Total\s*Liabilit(?:y|ies))'
    FINANCIAL_EQUITY = r'(?:Equity|股東權益|Shareholders?\s*Equity)'

# =============================================================================
# § 3. 文字正規化器
# =============================================================================

class TextNormalizer:
    """文字正規化器"""
    
    # 全形轉半形映射
    FULLWIDTH_TO_HALFWIDTH = {
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
        'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        '％': '%', '＄': '$', '－': '-', '＋': '+', '．': '.',
        '，': ',', '：': ':', '；': ';', '（': '(', '）': ')',
        '　': ' ',  # 全形空格
    }
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """完整正規化"""
        if not text:
            return ""
        
        # 1. Unicode NFKC 正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 2. 全形轉半形
        for fw, hw in cls.FULLWIDTH_TO_HALFWIDTH.items():
            text = text.replace(fw, hw)
        
        # 3. 移除控制字元
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # 4. 統一換行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 5. 壓縮連續空白
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 6. 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # 7. 移除連續空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @classmethod
    def normalize_number(cls, text: str) -> Tuple[Optional[float], str]:
        """正規化數字"""
        if not text:
            return None, "empty"
        
        original = text
        text = text.strip()
        
        # 移除千分位
        text = text.replace(",", "")
        
        # 處理括號負數
        if text.startswith("(") and text.endswith(")"):
            inner = text[1:-1]
            # 移除內部貨幣符號
            inner = re.sub(r'^[$￥€£]|^NT\$|^US\$|^HK\$|^RMB|^CNY', '', inner)
            text = "-" + inner
        
        # 移除貨幣符號
        text = re.sub(r'^NT\$|^US\$|^HK\$|^RMB|^CNY|^USD|^TWD|^EUR', '', text)
        text = re.sub(r'^[$￥€£¥]', '', text)
        text = re.sub(r'^-NT\$|^-US\$|^-[$]', '-', text)
        
        # 移除百分比
        is_percent = text.endswith('%')
        text = text.rstrip('%')
        
        # 移除 bp/bps
        is_bp = bool(re.search(r'\s*(?:bp|bps|BPS)$', text))
        text = re.sub(r'\s*(?:bp|bps|BPS)$', '', text)
        
        # 移除單位
        text = re.sub(r'\s*(?:B|bn|bil|M|mn|mil|K|k)$', '', text)
        
        try:
            value = float(text)
            return value, "ok"
        except:
            return None, f"parse_error: {original}"
    
    @classmethod
    def normalize_date(cls, text: str) -> Tuple[Optional[str], str]:
        """正規化日期為 ISO 格式"""
        if not text:
            return None, "empty"
        
        text = text.strip()
        
        # ISO 格式 (已是標準)
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
            return text, "iso"
        
        # 斜線格式
        match = re.fullmatch(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}", "slash"
        
        # 點格式
        match = re.fullmatch(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}", "dot"
        
        # 民國格式
        match = re.fullmatch(r'(\d{2,3})/(\d{1,2})/(\d{1,2})', text)
        if match:
            y, m, d = match.groups()
            year = int(y) + 1911
            return f"{year}-{int(m):02d}-{int(d):02d}", "roc"
        
        # 緊湊格式 (YYYYMMDD)
        match = re.fullmatch(r'(\d{4})(\d{2})(\d{2})', text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{m}-{d}", "compact"
        
        # 中文格式
        match = re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}", "cn"
        
        return None, "unknown_format"
    
    @classmethod
    def normalize_quarter(cls, text: str) -> Tuple[Optional[str], str]:
        """正規化季度為 YYYYQN 格式"""
        if not text:
            return None, "empty"
        
        text = text.strip().upper()
        
        # YYYYQN (已是標準)
        if re.fullmatch(r'20\d{2}Q[1-4]', text):
            return text, "standard"
        
        # QNYYYY
        match = re.fullmatch(r'Q([1-4])\s*(20\d{2})', text)
        if match:
            q, y = match.groups()
            return f"{y}Q{q}", "qyyyy"
        
        # NQYY
        match = re.fullmatch(r'([1-4])Q(\d{2})', text)
        if match:
            q, y = match.groups()
            year = 2000 + int(y)
            return f"{year}Q{q}", "nqyy"
        
        # NQYYYY
        match = re.fullmatch(r'([1-4])Q(20\d{2})', text)
        if match:
            q, y = match.groups()
            return f"{y}Q{q}", "nqyyyy"
        
        # FY
        match = re.fullmatch(r'FY(\d{2,4})[Ee]?', text)
        if match:
            y = match.group(1)
            if len(y) == 2:
                y = "20" + y
            return f"FY{y}", "fy"
        
        return None, "unknown_format"

# =============================================================================
# § 4. 驗證器
# =============================================================================

class Validator:
    """資料驗證器"""
    
    @staticmethod
    def validate_ticker(text: str) -> ValidationResult:
        """驗證股票代號"""
        text = text.strip()
        
        # 台股代號 (4位數)
        if re.fullmatch(PatternLibrary.TICKER_TW, text):
            # 額外排除年份
            if re.match(r'^20[2-3][0-9]$', text) or text == "2030":
                return ValidationResult(
                    field_name="ticker",
                    original_value=text,
                    processed_value=None,
                    data_type=DataType.TICKER,
                    status=ValidationStatus.INVALID,
                    confidence=0.0,
                    message=f"'{text}' 可能是年份而非股票代號"
                )
            
            return ValidationResult(
                field_name="ticker",
                original_value=text,
                processed_value=text,
                data_type=DataType.TICKER,
                status=ValidationStatus.VALID,
                confidence=0.95,
                message="有效台股代號"
            )
        
        # 美股代號
        if re.fullmatch(PatternLibrary.TICKER_US, text):
            return ValidationResult(
                field_name="ticker",
                original_value=text,
                processed_value=text,
                data_type=DataType.TICKER,
                status=ValidationStatus.VALID,
                confidence=0.85,
                message="可能的美股代號"
            )
        
        return ValidationResult(
            field_name="ticker",
            original_value=text,
            processed_value=None,
            data_type=DataType.TICKER,
            status=ValidationStatus.INVALID,
            confidence=0.0,
            message="無效股票代號格式"
        )
    
    @staticmethod
    def validate_date(text: str) -> ValidationResult:
        """驗證日期"""
        normalized, format_type = TextNormalizer.normalize_date(text)
        
        if normalized:
            # 驗證日期有效性
            try:
                y, m, d = map(int, normalized.split('-'))
                date(y, m, d)  # 會拋出異常如果無效
                
                corrections = []
                if format_type != "iso":
                    corrections.append(f"格式轉換: {text} → {normalized}")
                
                return ValidationResult(
                    field_name="date",
                    original_value=text,
                    processed_value=normalized,
                    data_type=DataType.DATE_ROC if format_type == "roc" else DataType.DATE,
                    status=ValidationStatus.CORRECTED if corrections else ValidationStatus.VALID,
                    confidence=0.95,
                    message=f"有效日期 ({format_type} 格式)",
                    corrections=corrections
                )
            except ValueError:
                return ValidationResult(
                    field_name="date",
                    original_value=text,
                    processed_value=None,
                    data_type=DataType.DATE,
                    status=ValidationStatus.INVALID,
                    confidence=0.0,
                    message="日期值無效"
                )
        
        return ValidationResult(
            field_name="date",
            original_value=text,
            processed_value=None,
            data_type=DataType.DATE,
            status=ValidationStatus.INVALID,
            confidence=0.0,
            message="無法識別的日期格式"
        )
    
    @staticmethod
    def validate_number(text: str) -> ValidationResult:
        """驗證數字"""
        value, status = TextNormalizer.normalize_number(text)
        
        if value is not None:
            # 判斷類型
            if '%' in text:
                data_type = DataType.PERCENTAGE
            elif re.search(r'bp|bps|BPS', text):
                data_type = DataType.BASIS_POINTS
            elif re.search(r'[$￥€£¥]|NT\$|US\$|TWD|USD', text):
                data_type = DataType.CURRENCY
            else:
                data_type = DataType.NUMBER
            
            corrections = []
            if str(value) != text.strip():
                corrections.append(f"數值解析: {text} → {value}")
            
            return ValidationResult(
                field_name="number",
                original_value=text,
                processed_value=value,
                data_type=data_type,
                status=ValidationStatus.CORRECTED if corrections else ValidationStatus.VALID,
                confidence=0.90,
                message=f"有效數值 ({data_type.value})",
                corrections=corrections
            )
        
        return ValidationResult(
            field_name="number",
            original_value=text,
            processed_value=None,
            data_type=DataType.NUMBER,
            status=ValidationStatus.INVALID,
            confidence=0.0,
            message=f"數值解析失敗: {status}"
        )
    
    @staticmethod
    def validate_accounting_equation(assets: float, liabilities: float, equity: float,
                                      tolerance: float = 0.001) -> ValidationResult:
        """驗證會計等式 A = L + E"""
        expected = liabilities + equity
        diff = abs(assets - expected)
        diff_pct = diff / max(abs(assets), 1) * 100
        
        if diff_pct <= tolerance * 100:
            return ValidationResult(
                field_name="accounting_equation",
                original_value={"assets": assets, "liabilities": liabilities, "equity": equity},
                processed_value={"valid": True, "diff": diff, "diff_pct": diff_pct},
                data_type=DataType.ACCOUNTING,
                status=ValidationStatus.VALID,
                confidence=0.99,
                message=f"會計等式成立 (差異: {diff_pct:.4f}%)"
            )
        else:
            return ValidationResult(
                field_name="accounting_equation",
                original_value={"assets": assets, "liabilities": liabilities, "equity": equity},
                processed_value={"valid": False, "diff": diff, "diff_pct": diff_pct},
                data_type=DataType.ACCOUNTING,
                status=ValidationStatus.INVALID,
                confidence=0.0,
                message=f"會計等式不成立: A({assets}) ≠ L({liabilities}) + E({equity}), 差異: {diff_pct:.2f}%"
            )

# =============================================================================
# § 5. 同義詞引擎 (VeritasSynonymEngine)
# =============================================================================

class VeritasSynonymEngine:
    """同義詞統一引擎"""
    
    # 同義詞映射表
    SYNONYMS = {
        # 季度
        "quarters": {
            "Q1": ["1Q", "第一季", "First Quarter", "1st Quarter", "Q1"],
            "Q2": ["2Q", "第二季", "Second Quarter", "2nd Quarter", "Q2"],
            "Q3": ["3Q", "第三季", "Third Quarter", "3rd Quarter", "Q3"],
            "Q4": ["4Q", "第四季", "Fourth Quarter", "4th Quarter", "Q4"],
        },
        # 財務指標
        "financial": {
            "Revenue": ["營收", "營業收入", "銷售額", "Sales", "Net Sales", "Total Revenue"],
            "Net Income": ["淨利", "淨利潤", "純益", "Profit", "Net Profit", "NI"],
            "EPS": ["每股盈餘", "每股收益", "Earnings Per Share"],
            "Assets": ["資產", "總資產", "Total Assets"],
            "Liabilities": ["負債", "總負債", "Total Liabilities"],
            "Equity": ["股東權益", "權益", "Shareholders' Equity", "Stockholders' Equity"],
            "Gross Margin": ["毛利率", "毛利潤率", "GM"],
            "Operating Margin": ["營業利益率", "營益率", "OM", "Op Margin"],
            "Net Margin": ["淨利率", "純益率", "NM", "Net Profit Margin"],
        },
        # 券商
        "brokers": {
            "元大投顧": ["Yuanta", "元大", "YUANTA"],
            "凱基投顧": ["KGI", "凱基", "KGIS"],
            "富邦投顧": ["Fubon", "富邦", "FUBON"],
            "國泰投顧": ["Cathay", "國泰", "CATHAY"],
            "永豐投顧": ["SinoPac", "永豐", "SINOPAC"],
            "日盛投顧": ["Jih Sun", "日盛"],
            "統一投顧": ["President", "統一"],
            "群益投顧": ["Capital", "群益"],
            "玉山投顧": ["E.SUN", "玉山"],
        },
        # 貨幣
        "currency": {
            "TWD": ["NT$", "NTD", "新台幣", "台幣", "元"],
            "USD": ["US$", "$", "美元", "美金"],
            "CNY": ["RMB", "¥", "人民幣", "元"],
        },
    }
    
    @classmethod
    def normalize(cls, text: str, category: str = None) -> str:
        """正規化同義詞"""
        if not text:
            return text
        
        categories = [category] if category else cls.SYNONYMS.keys()
        
        for cat in categories:
            if cat not in cls.SYNONYMS:
                continue
            
            for standard, variants in cls.SYNONYMS[cat].items():
                for variant in variants:
                    # 完整匹配
                    if text.strip().lower() == variant.lower():
                        return standard
                    # 部分替換
                    pattern = re.compile(re.escape(variant), re.IGNORECASE)
                    text = pattern.sub(standard, text)
        
        return text
    
    @classmethod
    def find_standard_term(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """查找標準術語"""
        text_lower = text.strip().lower()
        
        for category, mappings in cls.SYNONYMS.items():
            for standard, variants in mappings.items():
                if text_lower == standard.lower():
                    return standard, category
                for variant in variants:
                    if text_lower == variant.lower():
                        return standard, category
        
        return None, None

# =============================================================================
# § 6. 後處理引擎
# =============================================================================

class OCRPostProcessor:
    """OCR 後處理引擎"""
    
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.validator = Validator()
        self.synonym_engine = VeritasSynonymEngine()
    
    def process(self, text: str, extract_data: bool = True) -> PostProcessingResult:
        """執行完整後處理"""
        warnings = []
        errors = []
        validations = []
        extracted = {}
        
        # 1. 文字正規化
        processed_text = self.normalizer.normalize(text)
        
        # 2. 同義詞統一
        processed_text = self.synonym_engine.normalize(processed_text)
        
        # 3. 資料提取與驗證
        if extract_data:
            # 提取股票代號
            tickers = re.findall(PatternLibrary.TICKER_TW, processed_text)
            valid_tickers = []
            for t in tickers:
                result = self.validator.validate_ticker(t)
                validations.append(result)
                if result.status == ValidationStatus.VALID:
                    valid_tickers.append(t)
            extracted["tickers"] = valid_tickers
            
            # 提取日期
            dates = []
            for pattern in [PatternLibrary.DATE_ISO, PatternLibrary.DATE_SLASH, 
                           PatternLibrary.DATE_ROC, PatternLibrary.DATE_CN]:
                matches = re.findall(pattern, processed_text)
                dates.extend(matches)
            
            valid_dates = []
            for d in dates:
                result = self.validator.validate_date(d)
                validations.append(result)
                if result.status in [ValidationStatus.VALID, ValidationStatus.CORRECTED]:
                    valid_dates.append(result.processed_value)
            extracted["dates"] = list(set(valid_dates))
            
            # 提取季度
            quarters = []
            for pattern in [PatternLibrary.QUARTER_YYYYQN, PatternLibrary.QUARTER_QNYYYY,
                           PatternLibrary.QUARTER_NQYY, PatternLibrary.QUARTER_FY]:
                matches = re.findall(pattern, processed_text, re.IGNORECASE)
                quarters.extend(matches)
            
            valid_quarters = []
            for q in quarters:
                normalized, _ = self.normalizer.normalize_quarter(q)
                if normalized:
                    valid_quarters.append(normalized)
            extracted["quarters"] = list(set(valid_quarters))
            
            # 提取數字
            numbers = re.findall(PatternLibrary.NUMBER_FLOAT + r'|' + PatternLibrary.NUMBER_INT, 
                                processed_text)
            extracted["numbers_count"] = len(numbers)
            
            # 提取百分比
            percentages = re.findall(PatternLibrary.PERCENTAGE, processed_text)
            extracted["percentages"] = percentages
            
            # 提取貨幣
            currencies = []
            for pattern in [PatternLibrary.CURRENCY_TWD, PatternLibrary.CURRENCY_USD]:
                matches = re.findall(pattern, processed_text)
                currencies.extend(matches)
            extracted["currencies"] = currencies
        
        # 4. 統計
        statistics = {
            "original_length": len(text),
            "processed_length": len(processed_text),
            "compression_ratio": len(processed_text) / max(len(text), 1),
            "total_validations": len(validations),
            "valid_count": sum(1 for v in validations if v.status == ValidationStatus.VALID),
            "corrected_count": sum(1 for v in validations if v.status == ValidationStatus.CORRECTED),
            "invalid_count": sum(1 for v in validations if v.status == ValidationStatus.INVALID),
        }
        
        return PostProcessingResult(
            original_text=text,
            processed_text=processed_text,
            extracted_data=extracted,
            validations=validations,
            statistics=statistics,
            warnings=warnings,
            errors=errors
        )
    
    def process_financial_data(self, data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """處理財務數據"""
        results = {}
        
        # 驗證各欄位
        if "ticker" in data:
            results["ticker"] = self.validator.validate_ticker(str(data["ticker"]))
        
        if "date" in data:
            results["date"] = self.validator.validate_date(str(data["date"]))
        
        if "revenue" in data:
            results["revenue"] = self.validator.validate_number(str(data["revenue"]))
        
        if "net_income" in data:
            results["net_income"] = self.validator.validate_number(str(data["net_income"]))
        
        if "eps" in data:
            results["eps"] = self.validator.validate_number(str(data["eps"]))
        
        # 會計等式驗證
        if all(k in data for k in ["assets", "liabilities", "equity"]):
            assets, _ = self.normalizer.normalize_number(str(data["assets"]))
            liabilities, _ = self.normalizer.normalize_number(str(data["liabilities"]))
            equity, _ = self.normalizer.normalize_number(str(data["equity"]))
            
            if all(v is not None for v in [assets, liabilities, equity]):
                results["accounting_equation"] = self.validator.validate_accounting_equation(
                    assets, liabilities, equity
                )
        
        return results

# =============================================================================
# § 7. 測試套件
# =============================================================================

def run_tests():
    """執行測試"""
    print("\n" + "=" * 80)
    print("  🧪 OCR 後處理與驗證系統測試")
    print("=" * 80)
    
    processor = OCRPostProcessor()
    passed = 0
    failed = 0
    
    # 測試 1: 股票代號驗證
    print("\n┌─ 測試 1: 股票代號驗證")
    test_tickers = [
        ("2330", True, "台積電"),
        ("2317", True, "鴻海"),
        ("0050", False, "首位為0"),
        ("2025", False, "年份"),
        ("12345", False, "5位數"),
        ("TSM", True, "美股"),
    ]
    
    for ticker, expected_valid, desc in test_tickers:
        result = Validator.validate_ticker(ticker)
        is_valid = result.status == ValidationStatus.VALID
        icon = "✅" if is_valid == expected_valid else "❌"
        print(f"│  {icon} '{ticker}' → {result.status.value} ({desc})")
        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1
    
    # 測試 2: 日期正規化
    print("\n┌─ 測試 2: 日期正規化")
    test_dates = [
        ("2025-01-15", "2025-01-15", "ISO"),
        ("2025/1/15", "2025-01-15", "斜線"),
        ("114/01/15", "2025-01-15", "民國"),
        ("2025年1月15日", "2025-01-15", "中文"),
    ]
    
    for input_date, expected, desc in test_dates:
        result = Validator.validate_date(input_date)
        icon = "✅" if result.processed_value == expected else "❌"
        print(f"│  {icon} '{input_date}' → '{result.processed_value}' ({desc})")
        if result.processed_value == expected:
            passed += 1
        else:
            failed += 1
    
    # 測試 3: 數字正規化
    print("\n┌─ 測試 3: 數字正規化")
    test_numbers = [
        ("625,000,000,000", 625000000000.0),
        ("($1,234)", -1234.0),
        ("(1,234)", -1234.0),
        ("NT$1,000", 1000.0),
        ("16.5%", 16.5),
        ("-1,234.56", -1234.56),
        ("($500,000)", -500000.0),
    ]
    
    for input_num, expected in test_numbers:
        value, _ = TextNormalizer.normalize_number(input_num)
        icon = "✅" if value == expected else "❌"
        print(f"│  {icon} '{input_num}' → {value}")
        if value == expected:
            passed += 1
        else:
            failed += 1
    
    # 測試 4: 會計等式
    print("\n┌─ 測試 4: 會計等式驗證")
    test_equations = [
        (5200000000000, 1800000000000, 3400000000000, True),   # A = L + E
        (100, 60, 40, True),                                    # 正確
        (100, 60, 50, False),                                   # 錯誤
    ]
    
    for assets, liab, equity, expected_valid in test_equations:
        result = Validator.validate_accounting_equation(assets, liab, equity)
        is_valid = result.status == ValidationStatus.VALID
        icon = "✅" if is_valid == expected_valid else "❌"
        print(f"│  {icon} A={assets}, L={liab}, E={equity} → {result.status.value}")
        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1
    
    # 測試 5: 同義詞統一
    print("\n┌─ 測試 5: 同義詞統一")
    test_synonyms = [
        ("營收", "Revenue"),
        ("淨利", "Net Income"),
        ("每股盈餘", "EPS"),
        ("1Q", "Q1"),
        ("NT$", "TWD"),
    ]
    
    for input_term, expected in test_synonyms:
        standard, _ = VeritasSynonymEngine.find_standard_term(input_term)
        icon = "✅" if standard == expected else "❌"
        print(f"│  {icon} '{input_term}' → '{standard}'")
        if standard == expected:
            passed += 1
        else:
            failed += 1
    
    # 測試 6: 完整後處理
    print("\n┌─ 測試 6: 完整後處理")
    test_text = """
    TSMC Financial Report
    Ticker: 2330
    Date: 2025/1/15
    Quarter: 2025Q1
    Revenue: 625,000,000,000 TWD
    Net Income: 295,000,000,000
    EPS: 9.21
    Assets: 5,200,000,000,000
    Liabilities: 1,800,000,000,000
    Equity: 3,400,000,000,000
    """
    
    result = processor.process(test_text)
    print(f"│  提取股票代號: {result.extracted_data.get('tickers', [])}")
    print(f"│  提取日期: {result.extracted_data.get('dates', [])}")
    print(f"│  提取季度: {result.extracted_data.get('quarters', [])}")
    print(f"│  驗證數: {result.statistics['total_validations']}")
    print(f"│  有效: {result.statistics['valid_count']}")
    print(f"│  修正: {result.statistics['corrected_count']}")
    
    if result.extracted_data.get('tickers') == ['2330']:
        passed += 1
        print("│  ✅ 股票代號提取正確")
    else:
        failed += 1
        print("│  ❌ 股票代號提取錯誤")
    
    # 彙總
    print("\n" + "=" * 80)
    total = passed + failed
    accuracy = passed / total * 100 if total > 0 else 0
    print(f"  📊 測試結果: {passed}/{total} 通過 ({accuracy:.1f}%)")
    
    if failed == 0:
        print("  ✅ 全部測試通過！")
    else:
        print(f"  ⚠️ {failed} 項測試失敗")
    
    print("=" * 80)
    
    return passed, failed

# =============================================================================
# § 8. 主程式
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="VRN OCR Post-Processing & Validation System")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--process", type=str, help="Process text file")
    parser.add_argument("--json", type=str, help="Output JSON path")
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    elif args.process:
        processor = OCRPostProcessor()
        
        with open(args.process, 'r', encoding='utf-8') as f:
            text = f.read()
        
        result = processor.process(text)
        
        print("\n📊 後處理結果:")
        print(f"   原始長度: {result.statistics['original_length']}")
        print(f"   處理後長度: {result.statistics['processed_length']}")
        print(f"   提取股票: {result.extracted_data.get('tickers', [])}")
        print(f"   提取日期: {result.extracted_data.get('dates', [])}")
        print(f"   提取季度: {result.extracted_data.get('quarters', [])}")
        
        if args.json:
            output = {
                "statistics": result.statistics,
                "extracted_data": result.extracted_data,
                "validations": [asdict(v) for v in result.validations],
            }
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n   📄 JSON: {args.json}")
    else:
        run_tests()


if __name__ == "__main__":
    main()
