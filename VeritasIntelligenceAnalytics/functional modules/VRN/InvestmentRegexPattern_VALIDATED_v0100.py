#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                         InvestmentRegexPattern_VALIDATED.py v3.0                                      ║
║                   📊 投資財務報表正則表達式模式庫 (完整驗證版)                                        ║
╠═══════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                       ║
║  涵蓋範圍:                                                                                            ║
║    1. 三大報表 (資產負債表、損益表、現金流量表)                                                       ║
║    2. 比率分析 (流動性、償債能力、獲利能力、經營效率)                                                 ║
║    3. 每股分析 (EPS、每股淨值、每股現金流等)                                                          ║
║    4. 資料驗證 (完整性、合理性、一致性檢查)                                                           ║
║                                                                                                       ║
║  適用:                                                                                                ║
║    - 台灣上市櫃公司財務報表                                                                           ║
║    - 投資研究報告                                                                                     ║
║    - 財務分析文件                                                                                     ║
║                                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝
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

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Pattern, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime

import os

# ═══════════════════════════════════════════════════════════════════════════════
# VIS MEGA Accelerator V12 Integration (Auto-Injected)
# ═══════════════════════════════════════════════════════════════════════════════
_VIS_ACCEL = False
_VIS_ACCEL_VERSION = "FALLBACK"
_OPTIMAL_WORKERS = min(8, (os.cpu_count() or 4) + 4)

def _fb_parallel_map(fn, data, max_workers=None, **kw):
    from concurrent.futures import ThreadPoolExecutor
    if not data: return []
    try:
        with ThreadPoolExecutor(max_workers=max_workers or _OPTIMAL_WORKERS) as ex:
            return list(ex.map(fn, data))
    except: return list(map(fn, data))

def _fb_json_dumps(obj, **kw):
    import json
    kw.setdefault('ensure_ascii', False)
    kw.setdefault('separators', (',', ':'))
    return json.dumps(obj, **kw)

def _fb_json_loads(s):
    import json
    return json.loads(s)

def _fb_hash(d):
    import hashlib
    return hashlib.md5(str(d).encode()).hexdigest()

class _FbTimer:
    def __init__(self, n="", l=None): self.name, self.logger, self.elapsed = n, l, 0.0
    def __enter__(self): import time; self._s = time.perf_counter(); return self
    def __exit__(self, *a): import time; self.elapsed = time.perf_counter() - self._s

class _FbHardwareTuner:
    @classmethod
    def optimize(cls): return {"status": "fallback"}

class _FbGCTuner:
    @classmethod
    def optimize(cls): import gc; gc.set_threshold(50000, 500, 100); return {}
    @classmethod
    def collect(cls): import gc; return gc.collect()

parallel_map = _fb_parallel_map
fast_json_dumps = _fb_json_dumps
fast_json_loads = _fb_json_loads
fast_hash = _fb_hash
Timer = _FbTimer
HardwareTuner = _FbHardwareTuner
GCTuner = _FbGCTuner

try:
    from pathlib import Path as _Path
    _accel_path = _Path(__file__).parent / "VIS_UltimateAccelerator_V12_MEGA.py"
    if _accel_path.exists():
        import sys
        if str(_accel_path.parent) not in sys.path:
            sys.path.insert(0, str(_accel_path.parent))
        import VIS_UltimateAccelerator_V12_MEGA as _accel
        for _n in ['parallel_map','fast_json_dumps','fast_json_loads','fast_hash','Timer','HardwareTuner','GCTuner']:
            if hasattr(_accel, _n): globals()[_n] = getattr(_accel, _n)
        if hasattr(_accel, 'HardwareTuner'): _accel.HardwareTuner.optimize()
        if hasattr(_accel, 'GCTuner'): _accel.GCTuner.optimize()
        _VIS_ACCEL = True
        _VIS_ACCEL_VERSION = "V12"
except Exception as _e:
    pass  # Keep using fallback
# ═══════════════════════════════════════════════════════════════════════════════


__version__ = "3.0.0"
__author__ = "VRN System"

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 枚舉定義
# ═══════════════════════════════════════════════════════════════════════════════

class StatementType(Enum):
    """報表類型"""
    BALANCE_SHEET = "資產負債表"
    INCOME_STATEMENT = "損益表"
    CASH_FLOW = "現金流量表"
    EQUITY_CHANGE = "權益變動表"
    NOTES = "附註"


class CategoryType(Enum):
    """科目類別"""
    # 資產負債表
    CURRENT_ASSET = "流動資產"
    NON_CURRENT_ASSET = "非流動資產"
    CURRENT_LIABILITY = "流動負債"
    NON_CURRENT_LIABILITY = "非流動負債"
    EQUITY = "權益"
    
    # 損益表
    REVENUE = "營業收入"
    COST = "營業成本"
    GROSS_PROFIT = "毛利"
    OPERATING_EXPENSE = "營業費用"
    OPERATING_INCOME = "營業利益"
    NON_OPERATING = "營業外損益"
    NET_INCOME = "淨利"
    
    # 現金流量表
    OPERATING_CF = "營業活動現金流"
    INVESTING_CF = "投資活動現金流"
    FINANCING_CF = "籌資活動現金流"
    
    # 比率
    RATIO = "財務比率"
    PER_SHARE = "每股指標"


class ValidationLevel(Enum):
    """驗證等級"""
    CRITICAL = auto()  # 必要欄位
    IMPORTANT = auto()  # 重要欄位
    OPTIONAL = auto()   # 選填欄位


# ═══════════════════════════════════════════════════════════════════════════════
# 資料類別
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PatternDef:
    """正則表達式模式定義"""
    name: str
    name_en: str
    patterns: List[str]
    category: CategoryType
    statement: StatementType
    validation_level: ValidationLevel = ValidationLevel.OPTIONAL
    unit: str = "元"
    description: str = ""
    compiled: List[Pattern] = field(default_factory=list)
    
    def __post_init__(self):
        self.compiled = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.patterns]
    
    def match(self, text: str) -> Optional[re.Match]:
        """匹配文字"""
        for pattern in self.compiled:
            match = pattern.search(text)
            if match:
                return match
        return None
    
    def findall(self, text: str) -> List[str]:
        """找出所有匹配"""
        results = []
        for pattern in self.compiled:
            results.extend(pattern.findall(text))
        return results


@dataclass
class ExtractedValue:
    """提取的數值"""
    field_name: str
    field_name_en: str
    value: float
    unit: str
    confidence: float
    source_text: str
    category: CategoryType
    statement: StatementType


@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    missing_critical: List[str] = field(default_factory=list)
    missing_important: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    completeness_score: float = 0.0
    consistency_score: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 一、資產負債表 (Balance Sheet) 模式
# ═══════════════════════════════════════════════════════════════════════════════

BALANCE_SHEET_PATTERNS = {
    # ─────────────────────────────────────────────────────────────────────────
    # 流動資產 (Current Assets)
    # ─────────────────────────────────────────────────────────────────────────
    "cash": PatternDef(
        name="現金及約當現金",
        name_en="Cash and Cash Equivalents",
        patterns=[
            r"現金及約當現金",
            r"現金與約當現金",
            r"現金及現金等價物",
            r"cash\s*(?:and|&)?\s*cash\s*equivalents?",
            r"現金(?:$|[^\u4e00-\u9fff])",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
        description="包含庫存現金、活期存款、定期存款、可隨時轉換現金之短期投資"
    ),
    
    "short_term_investment": PatternDef(
        name="短期投資",
        name_en="Short-term Investments",
        patterns=[
            r"(?:透過損益|透過其他綜合損益)按公允價值衡量之金融資產[－—-]?流動",
            r"按攤銷後成本衡量之金融資產[－—-]?流動",
            r"短期投資",
            r"流動金融資產",
            r"short[- ]?term\s*investments?",
            r"marketable\s*securities",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "accounts_receivable": PatternDef(
        name="應收帳款",
        name_en="Accounts Receivable",
        patterns=[
            r"應收帳款淨額",
            r"應收帳款[－—-]?淨額",
            r"應收帳款",
            r"accounts?\s*receivable",
            r"trade\s*receivables?",
            r"A/R",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "notes_receivable": PatternDef(
        name="應收票據",
        name_en="Notes Receivable",
        patterns=[
            r"應收票據淨額",
            r"應收票據",
            r"notes?\s*receivable",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "other_receivables": PatternDef(
        name="其他應收款",
        name_en="Other Receivables",
        patterns=[
            r"其他應收款",
            r"其他應收款項",
            r"other\s*receivables?",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "inventory": PatternDef(
        name="存貨",
        name_en="Inventory",
        patterns=[
            r"存貨淨額",
            r"存貨",
            r"inventor(?:y|ies)",
            r"merchandise",
            r"原物料",
            r"在製品",
            r"製成品",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "prepaid_expenses": PatternDef(
        name="預付款項",
        name_en="Prepaid Expenses",
        patterns=[
            r"預付款項",
            r"預付費用",
            r"預付貨款",
            r"prepaid\s*(?:expenses?|items?)",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "contract_assets": PatternDef(
        name="合約資產",
        name_en="Contract Assets",
        patterns=[
            r"合約資產",
            r"contract\s*assets?",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "other_current_assets": PatternDef(
        name="其他流動資產",
        name_en="Other Current Assets",
        patterns=[
            r"其他流動資產",
            r"other\s*current\s*assets?",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "total_current_assets": PatternDef(
        name="流動資產合計",
        name_en="Total Current Assets",
        patterns=[
            r"流動資產[合總]計",
            r"流動資產小計",
            r"total\s*current\s*assets?",
        ],
        category=CategoryType.CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 非流動資產 (Non-current Assets)
    # ─────────────────────────────────────────────────────────────────────────
    "long_term_investment": PatternDef(
        name="長期投資",
        name_en="Long-term Investments",
        patterns=[
            r"採用權益法之投資",
            r"長期股權投資",
            r"長期投資",
            r"(?:透過損益|透過其他綜合損益)按公允價值衡量之金融資產[－—-]?非流動",
            r"long[- ]?term\s*investments?",
            r"equity\s*method\s*investments?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "property_plant_equipment": PatternDef(
        name="不動產廠房及設備",
        name_en="Property, Plant and Equipment",
        patterns=[
            r"不動產[、,]?廠房及設備淨額",
            r"不動產[、,]?廠房及設備",
            r"固定資產淨額",
            r"固定資產",
            r"property[,\s]*plant\s*(?:and|&)\s*equipment",
            r"PP&?E",
            r"PPE",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "right_of_use_assets": PatternDef(
        name="使用權資產",
        name_en="Right-of-use Assets",
        patterns=[
            r"使用權資產",
            r"right[- ]?of[- ]?use\s*assets?",
            r"ROU\s*assets?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "investment_property": PatternDef(
        name="投資性不動產",
        name_en="Investment Property",
        patterns=[
            r"投資性不動產",
            r"investment\s*property",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "other_noncurrent_assets": PatternDef(
        name="其他非流動資產",
        name_en="Other Non-current Assets",
        patterns=[
            r"其他非流動資產",
            r"other\s*non[- ]?current\s*assets?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "intangible_assets": PatternDef(
        name="無形資產",
        name_en="Intangible Assets",
        patterns=[
            r"無形資產",
            r"商譽",
            r"專利權",
            r"商標權",
            r"intangible\s*assets?",
            r"goodwill",
            r"patents?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "deferred_tax_assets": PatternDef(
        name="遞延所得稅資產",
        name_en="Deferred Tax Assets",
        patterns=[
            r"遞延所得稅資產",
            r"遞延稅項資產",
            r"deferred\s*(?:income\s*)?tax\s*assets?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "total_non_current_assets": PatternDef(
        name="非流動資產合計",
        name_en="Total Non-current Assets",
        patterns=[
            r"非流動資產[合總]計",
            r"非流動資產小計",
            r"total\s*non[- ]?current\s*assets?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "total_assets": PatternDef(
        name="資產總計",
        name_en="Total Assets",
        patterns=[
            r"資產總[計額]",
            r"資產[合總]計",
            r"total\s*assets?",
        ],
        category=CategoryType.NON_CURRENT_ASSET,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 流動負債 (Current Liabilities)
    # ─────────────────────────────────────────────────────────────────────────
    "short_term_borrowings": PatternDef(
        name="短期借款",
        name_en="Short-term Borrowings",
        patterns=[
            r"短期借款",
            r"短期銀行借款",
            r"short[- ]?term\s*(?:borrowings?|loans?|debt)",
            r"bank\s*(?:borrowings?|loans?)",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "accounts_payable": PatternDef(
        name="應付帳款",
        name_en="Accounts Payable",
        patterns=[
            r"應付帳款",
            r"accounts?\s*payable",
            r"trade\s*payables?",
            r"A/P",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "notes_payable": PatternDef(
        name="應付票據",
        name_en="Notes Payable",
        patterns=[
            r"應付票據",
            r"notes?\s*payable",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "other_payables": PatternDef(
        name="其他應付款",
        name_en="Other Payables",
        patterns=[
            r"其他應付款",
            r"應付費用",
            r"other\s*payables?",
            r"accrued\s*expenses?",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "contract_liabilities": PatternDef(
        name="合約負債",
        name_en="Contract Liabilities",
        patterns=[
            r"合約負債",
            r"contract\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "other_current_liabilities": PatternDef(
        name="其他流動負債",
        name_en="Other Current Liabilities",
        patterns=[
            r"其他流動負債",
            r"other\s*current\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "current_portion_long_term_debt": PatternDef(
        name="一年內到期長期負債",
        name_en="Current Portion of Long-term Debt",
        patterns=[
            r"一年內到期長期[負負]債",
            r"一年(?:內|以內)到期(?:之)?長期借款",
            r"current\s*portion\s*(?:of\s*)?long[- ]?term\s*debt",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "lease_liabilities_current": PatternDef(
        name="租賃負債-流動",
        name_en="Lease Liabilities - Current",
        patterns=[
            r"租賃負債[－—-]?流動",
            r"lease\s*liabilit(?:y|ies)[- ]?current",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "lease_liabilities_noncurrent": PatternDef(
        name="租賃負債-非流動",
        name_en="Lease Liabilities - Non-current",
        patterns=[
            r"租賃負債[－—-]?非流動",
            r"lease\s*liabilit(?:y|ies)[- ]?non[- ]?current",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "total_current_liabilities": PatternDef(
        name="流動負債合計",
        name_en="Total Current Liabilities",
        patterns=[
            r"流動負債[合總]計",
            r"流動負債小計",
            r"total\s*current\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 非流動負債 (Non-current Liabilities)
    # ─────────────────────────────────────────────────────────────────────────
    "long_term_borrowings": PatternDef(
        name="長期借款",
        name_en="Long-term Borrowings",
        patterns=[
            r"長期借款",
            r"長期銀行借款",
            r"long[- ]?term\s*(?:borrowings?|loans?|debt)",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "bonds_payable": PatternDef(
        name="應付公司債",
        name_en="Bonds Payable",
        patterns=[
            r"應付公司債",
            r"公司債",
            r"bonds?\s*payable",
            r"corporate\s*bonds?",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "other_noncurrent_liabilities": PatternDef(
        name="其他非流動負債",
        name_en="Other Non-current Liabilities",
        patterns=[
            r"其他非流動負債",
            r"other\s*non[- ]?current\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "deferred_tax_liabilities": PatternDef(
        name="遞延所得稅負債",
        name_en="Deferred Tax Liabilities",
        patterns=[
            r"遞延所得稅負債",
            r"遞延稅項負債",
            r"deferred\s*(?:income\s*)?tax\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "total_non_current_liabilities": PatternDef(
        name="非流動負債合計",
        name_en="Total Non-current Liabilities",
        patterns=[
            r"非流動負債[合總]計",
            r"非流動負債小計",
            r"total\s*non[- ]?current\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "total_liabilities": PatternDef(
        name="負債總計",
        name_en="Total Liabilities",
        patterns=[
            r"負債總[計額]",
            r"負債[合總]計",
            r"total\s*liabilit(?:y|ies)",
        ],
        category=CategoryType.NON_CURRENT_LIABILITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 權益 (Equity)
    # ─────────────────────────────────────────────────────────────────────────
    "common_stock": PatternDef(
        name="普通股股本",
        name_en="Common Stock",
        patterns=[
            r"普通股股本",
            r"股本",
            r"實收資本",
            r"common\s*stock",
            r"capital\s*stock",
            r"share\s*capital",
            r"paid[- ]?in\s*capital",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "preferred_stock": PatternDef(
        name="特別股股本",
        name_en="Preferred Stock",
        patterns=[
            r"特別股股本",
            r"特別股",
            r"preferred\s*stock",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "capital_surplus": PatternDef(
        name="資本公積",
        name_en="Capital Surplus",
        patterns=[
            r"資本公積",
            r"股本溢價",
            r"capital\s*surplus",
            r"additional\s*paid[- ]?in\s*capital",
            r"share\s*premium",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "retained_earnings": PatternDef(
        name="保留盈餘",
        name_en="Retained Earnings",
        patterns=[
            r"保留盈餘",
            r"累積盈餘",
            r"未分配盈餘",
            r"法定盈餘公積",
            r"特別盈餘公積",
            r"retained\s*earnings?",
            r"accumulated\s*(?:profits?|earnings?)",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "other_equity": PatternDef(
        name="其他權益",
        name_en="Other Equity",
        patterns=[
            r"其他權益",
            r"其他綜合損益",
            r"累計其他綜合損益",
            r"other\s*(?:comprehensive\s*)?(?:income|equity)",
            r"accumulated\s*other\s*comprehensive\s*(?:income|loss)",
            r"AOCI",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "treasury_stock": PatternDef(
        name="庫藏股票",
        name_en="Treasury Stock",
        patterns=[
            r"庫藏股[票]?",
            r"treasury\s*stock",
            r"treasury\s*shares?",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "non_controlling_interest": PatternDef(
        name="非控制權益",
        name_en="Non-controlling Interest",
        patterns=[
            r"非控制權益",
            r"少數股權",
            r"minority\s*interest",
            r"non[- ]?controlling\s*interest",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "total_equity": PatternDef(
        name="權益總計",
        name_en="Total Equity",
        patterns=[
            r"權益總[計額]",
            r"權益[合總]計",
            r"股東權益[合總]計",
            r"total\s*(?:shareholders?['\s]?)?equity",
            r"total\s*stockholders?['\s]?\s*equity",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "total_liabilities_equity": PatternDef(
        name="負債及權益總計",
        name_en="Total Liabilities and Equity",
        patterns=[
            r"負債及權益總[計額]",
            r"負債[及與和]權益[合總]計",
            r"total\s*liabilit(?:y|ies)\s*(?:and|&)\s*(?:shareholders?['\s]?)?equity",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 二、損益表 (Income Statement) 模式
# ═══════════════════════════════════════════════════════════════════════════════

INCOME_STATEMENT_PATTERNS = {
    # ─────────────────────────────────────────────────────────────────────────
    # 營業收入 (Revenue)
    # ─────────────────────────────────────────────────────────────────────────
    "revenue": PatternDef(
        name="營業收入",
        name_en="Revenue",
        patterns=[
            r"營業收入(?:淨額)?",
            r"營業收入[合總]計",
            r"銷貨收入",
            r"營收",
            r"(?:net\s*)?(?:sales|revenue)",
            r"total\s*(?:net\s*)?(?:sales|revenue)",
        ],
        category=CategoryType.REVENUE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "sales_revenue": PatternDef(
        name="銷貨收入",
        name_en="Sales Revenue",
        patterns=[
            r"銷貨收入",
            r"商品銷售收入",
            r"產品銷售收入",
            r"sales\s*revenue",
        ],
        category=CategoryType.REVENUE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "service_revenue": PatternDef(
        name="勞務收入",
        name_en="Service Revenue",
        patterns=[
            r"勞務收入",
            r"服務收入",
            r"service\s*revenue",
        ],
        category=CategoryType.REVENUE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 營業成本 (Cost of Sales)
    # ─────────────────────────────────────────────────────────────────────────
    "cost_of_sales": PatternDef(
        name="營業成本",
        name_en="Cost of Sales",
        patterns=[
            r"營業成本",
            r"銷貨成本",
            r"服務成本",
            r"cost\s*of\s*(?:goods\s*)?(?:sold|sales|revenue)",
            r"COGS",
        ],
        category=CategoryType.COST,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 毛利 (Gross Profit)
    # ─────────────────────────────────────────────────────────────────────────
    "gross_profit": PatternDef(
        name="營業毛利",
        name_en="Gross Profit",
        patterns=[
            r"營業毛利(?:\(損\))?",
            r"毛利(?:\(損\))?",
            r"銷貨毛利",
            r"gross\s*(?:profit|margin)",
        ],
        category=CategoryType.GROSS_PROFIT,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 營業費用 (Operating Expenses)
    # ─────────────────────────────────────────────────────────────────────────
    "selling_expenses": PatternDef(
        name="推銷費用",
        name_en="Selling Expenses",
        patterns=[
            r"推銷費用",
            r"銷售費用",
            r"行銷費用",
            r"selling\s*(?:and\s*marketing\s*)?expenses?",
            r"S&M\s*expenses?",
        ],
        category=CategoryType.OPERATING_EXPENSE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "admin_expenses": PatternDef(
        name="管理費用",
        name_en="Administrative Expenses",
        patterns=[
            r"管理費用",
            r"一般及管理費用",
            r"(?:general\s*(?:and|&)\s*)?admin(?:istrative)?\s*expenses?",
            r"G&?A\s*expenses?",
        ],
        category=CategoryType.OPERATING_EXPENSE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "rd_expenses": PatternDef(
        name="研究發展費用",
        name_en="R&D Expenses",
        patterns=[
            r"研究發展費用",
            r"研發費用",
            r"research\s*(?:and|&)\s*development\s*expenses?",
            r"R&?D\s*expenses?",
        ],
        category=CategoryType.OPERATING_EXPENSE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "total_operating_expenses": PatternDef(
        name="營業費用合計",
        name_en="Total Operating Expenses",
        patterns=[
            r"營業費用[合總]計",
            r"total\s*operating\s*expenses?",
        ],
        category=CategoryType.OPERATING_EXPENSE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 營業利益 (Operating Income)
    # ─────────────────────────────────────────────────────────────────────────
    "operating_income": PatternDef(
        name="營業利益",
        name_en="Operating Income",
        patterns=[
            r"營業利益(?:\(損失\))?",
            r"營業淨利",
            r"營業損益",
            r"operating\s*(?:income|profit|loss)",
            r"EBIT(?!DA)",
        ],
        category=CategoryType.OPERATING_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "ebitda": PatternDef(
        name="稅息折舊攤銷前盈餘",
        name_en="EBITDA",
        patterns=[
            r"稅息折舊攤銷前(?:盈餘|利潤|損益)",
            r"EBITDA",
            r"earnings?\s*before\s*interest\s*tax\s*depreciation\s*amortization",
        ],
        category=CategoryType.OPERATING_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 營業外收支 (Non-operating Income/Expenses)
    # ─────────────────────────────────────────────────────────────────────────
    "interest_income": PatternDef(
        name="利息收入",
        name_en="Interest Income",
        patterns=[
            r"利息收入",
            r"interest\s*income",
        ],
        category=CategoryType.NON_OPERATING,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "interest_expense": PatternDef(
        name="利息費用",
        name_en="Interest Expense",
        patterns=[
            r"利息費用",
            r"利息支出",
            r"interest\s*expense",
        ],
        category=CategoryType.NON_OPERATING,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "other_income": PatternDef(
        name="其他收入",
        name_en="Other Income",
        patterns=[
            r"其他收入",
            r"其他收益",
            r"other\s*income",
        ],
        category=CategoryType.NON_OPERATING,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "other_expenses": PatternDef(
        name="其他支出",
        name_en="Other Expenses",
        patterns=[
            r"其他支出",
            r"其他費用",
            r"其他損失",
            r"other\s*expenses?",
        ],
        category=CategoryType.NON_OPERATING,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "non_operating_income": PatternDef(
        name="營業外收入及支出",
        name_en="Non-operating Income and Expenses",
        patterns=[
            r"營業外收入及支出(?:淨額)?",
            r"營業外損益",
            r"非營業損益",
            r"non[- ]?operating\s*(?:income|expenses?)",
        ],
        category=CategoryType.NON_OPERATING,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 稅前/稅後淨利 (Net Income)
    # ─────────────────────────────────────────────────────────────────────────
    "income_before_tax": PatternDef(
        name="稅前淨利",
        name_en="Income Before Tax",
        patterns=[
            r"稅前淨利(?:\(損\))?",
            r"稅前利益",
            r"繼續營業單位稅前淨利",
            r"(?:income|profit|earnings?)\s*before\s*(?:income\s*)?tax",
            r"pre[- ]?tax\s*(?:income|profit)",
            r"EBT",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "income_tax": PatternDef(
        name="所得稅費用",
        name_en="Income Tax Expense",
        patterns=[
            r"所得稅(?:費用|利益)",
            r"income\s*tax\s*(?:expense|benefit)",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "net_income": PatternDef(
        name="本期淨利",
        name_en="Net Income",
        patterns=[
            r"本期淨利(?:\(損\))?",
            r"稅後淨利",
            r"淨利(?:\(損\))?",
            r"繼續營業單位本期淨利",
            r"net\s*(?:income|profit|loss)",
            r"(?:income|profit|earnings?)\s*after\s*tax",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "net_income_parent": PatternDef(
        name="歸屬母公司淨利",
        name_en="Net Income Attributable to Parent",
        patterns=[
            r"歸屬於?母公司(?:業主)?(?:之)?(?:本期)?淨利",
            r"母公司淨利",
            r"net\s*(?:income|profit)\s*attributable\s*to\s*(?:parent|owners?\s*of\s*(?:the\s*)?parent)",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 綜合損益 (Comprehensive Income)
    # ─────────────────────────────────────────────────────────────────────────
    "other_comprehensive_income": PatternDef(
        name="其他綜合損益",
        name_en="Other Comprehensive Income",
        patterns=[
            r"其他綜合損益",
            r"other\s*comprehensive\s*(?:income|loss)",
            r"OCI",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "total_comprehensive_income": PatternDef(
        name="本期綜合損益總額",
        name_en="Total Comprehensive Income",
        patterns=[
            r"本期綜合損益總額",
            r"綜合損益總額",
            r"total\s*comprehensive\s*(?:income|loss)",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "discontinued_operations": PatternDef(
        name="停業單位損益",
        name_en="Discontinued Operations",
        patterns=[
            r"停業單位(?:損益|淨利)",
            r"discontinued\s*operations",
        ],
        category=CategoryType.NET_INCOME,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 三、現金流量表 (Cash Flow Statement) 模式
# ═══════════════════════════════════════════════════════════════════════════════

CASH_FLOW_PATTERNS = {
    # ─────────────────────────────────────────────────────────────────────────
    # 營業活動現金流 (Operating Activities)
    # ─────────────────────────────────────────────────────────────────────────
    "net_income_cf": PatternDef(
        name="本期淨利(現金流)",
        name_en="Net Income (CF)",
        patterns=[
            r"稅前淨利(?:\(損失\))?",
            r"本期稅前淨利",
            r"net\s*(?:income|profit)\s*before\s*tax",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "depreciation": PatternDef(
        name="折舊費用",
        name_en="Depreciation",
        patterns=[
            r"折舊費用",
            r"折舊",
            r"depreciation\s*(?:expense)?",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "amortization": PatternDef(
        name="攤銷費用",
        name_en="Amortization",
        patterns=[
            r"攤銷費用",
            r"攤銷",
            r"amortization\s*(?:expense)?",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "depreciation_amortization": PatternDef(
        name="折舊及攤銷",
        name_en="Depreciation and Amortization",
        patterns=[
            r"折舊[及與和]攤銷",
            r"D&?A",
            r"depreciation\s*(?:and|&)\s*amortization",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "change_in_receivables": PatternDef(
        name="應收帳款變動",
        name_en="Change in Accounts Receivable",
        patterns=[
            r"應收帳款[（\(]?增[加]?[）\)]?減[少]?",
            r"應收帳款(?:之)?(?:增減|變動)",
            r"(?:increase|decrease)\s*in\s*(?:accounts?\s*)?receivables?",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "change_in_inventory": PatternDef(
        name="存貨變動",
        name_en="Change in Inventory",
        patterns=[
            r"存貨[（\(]?增[加]?[）\)]?減[少]?",
            r"存貨(?:之)?(?:增減|變動)",
            r"(?:increase|decrease)\s*in\s*inventor(?:y|ies)",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "change_in_payables": PatternDef(
        name="應付帳款變動",
        name_en="Change in Accounts Payable",
        patterns=[
            r"應付帳款[（\(]?增[加]?[）\)]?減[少]?",
            r"應付帳款(?:之)?(?:增減|變動)",
            r"(?:increase|decrease)\s*in\s*(?:accounts?\s*)?payables?",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "operating_cash_flow": PatternDef(
        name="營業活動淨現金流入(出)",
        name_en="Net Cash from Operating Activities",
        patterns=[
            r"營業活動[之的]?(?:淨)?現金流[入出量]?(?:[合總]計)?",
            r"營運活動現金流量",
            r"(?:net\s*)?cash\s*(?:flows?\s*)?(?:from|provided\s*by|used\s*in)\s*operating\s*activities",
            r"CFO",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 投資活動現金流 (Investing Activities)
    # ─────────────────────────────────────────────────────────────────────────
    "capex": PatternDef(
        name="購置不動產廠房設備",
        name_en="Capital Expenditure",
        patterns=[
            r"取得不動產[、,]?廠房及設備",
            r"購置不動產[、,]?廠房及設備",
            r"購買固定資產",
            r"資本支出",
            r"(?:purchase|acquisition)\s*of\s*(?:property[,\s]*plant\s*(?:and|&)\s*equipment|PP&?E|fixed\s*assets?)",
            r"capital\s*expenditure",
            r"CAPEX",
        ],
        category=CategoryType.INVESTING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "sale_of_ppe": PatternDef(
        name="處分不動產廠房設備",
        name_en="Sale of Property, Plant and Equipment",
        patterns=[
            r"處分不動產[、,]?廠房及設備",
            r"出售固定資產",
            r"(?:sale|disposal)\s*of\s*(?:property[,\s]*plant\s*(?:and|&)\s*equipment|PP&?E|fixed\s*assets?)",
        ],
        category=CategoryType.INVESTING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "acquisition_of_investments": PatternDef(
        name="取得投資",
        name_en="Acquisition of Investments",
        patterns=[
            r"取得(?:金融資產|投資)",
            r"購買投資",
            r"(?:purchase|acquisition)\s*of\s*investments?",
        ],
        category=CategoryType.INVESTING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "investing_cash_flow": PatternDef(
        name="投資活動淨現金流入(出)",
        name_en="Net Cash from Investing Activities",
        patterns=[
            r"投資活動[之的]?(?:淨)?現金流[入出量]?(?:[合總]計)?",
            r"(?:net\s*)?cash\s*(?:flows?\s*)?(?:from|provided\s*by|used\s*in)\s*investing\s*activities",
            r"CFI",
        ],
        category=CategoryType.INVESTING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 籌資活動現金流 (Financing Activities)
    # ─────────────────────────────────────────────────────────────────────────
    "short_term_borrowings_change": PatternDef(
        name="短期借款變動",
        name_en="Change in Short-term Borrowings",
        patterns=[
            r"短期借款(?:之)?(?:增減|變動)",
            r"(?:增加|減少)短期借款",
            r"(?:increase|decrease)\s*in\s*short[- ]?term\s*(?:borrowings?|loans?)",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "long_term_borrowings_proceeds": PatternDef(
        name="舉借長期借款",
        name_en="Proceeds from Long-term Borrowings",
        patterns=[
            r"舉借長期借款",
            r"長期借款增加",
            r"proceeds\s*from\s*long[- ]?term\s*(?:borrowings?|loans?|debt)",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "repayment_of_debt": PatternDef(
        name="償還借款",
        name_en="Repayment of Debt",
        patterns=[
            r"償還(?:長期)?借款",
            r"repayment\s*of\s*(?:long[- ]?term\s*)?(?:borrowings?|loans?|debt)",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "dividends_paid": PatternDef(
        name="發放現金股利",
        name_en="Dividends Paid",
        patterns=[
            r"發放現金股利",
            r"支付股利",
            r"現金股利(?:支付|發放)",
            r"(?:cash\s*)?dividends?\s*paid",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "interest_paid": PatternDef(
        name="支付利息",
        name_en="Interest Paid",
        patterns=[
            r"支付利息",
            r"利息支付",
            r"interest\s*paid",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "income_tax_paid": PatternDef(
        name="支付所得稅",
        name_en="Income Tax Paid",
        patterns=[
            r"支付所得稅",
            r"所得稅支付",
            r"income\s*tax\s*paid",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "stock_issuance": PatternDef(
        name="現金增資",
        name_en="Stock Issuance",
        patterns=[
            r"現金增資",
            r"發行新股",
            r"(?:issuance|issue)\s*of\s*(?:common\s*)?(?:stock|shares?)",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "treasury_stock_purchase": PatternDef(
        name="購買庫藏股",
        name_en="Treasury Stock Purchase",
        patterns=[
            r"購買庫藏股",
            r"買回庫藏股",
            r"(?:purchase|repurchase)\s*of\s*treasury\s*(?:stock|shares?)",
            r"stock\s*buyback",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    
    "financing_cash_flow": PatternDef(
        name="籌資活動淨現金流入(出)",
        name_en="Net Cash from Financing Activities",
        patterns=[
            r"籌資活動[之的]?(?:淨)?現金流[入出量]?(?:[合總]計)?",
            r"融資活動現金流量",
            r"(?:net\s*)?cash\s*(?:flows?\s*)?(?:from|provided\s*by|used\s*in)\s*financing\s*activities",
            r"CFF",
        ],
        category=CategoryType.FINANCING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 現金變動匯總
    # ─────────────────────────────────────────────────────────────────────────
    "net_change_in_cash": PatternDef(
        name="現金及約當現金淨增減",
        name_en="Net Change in Cash",
        patterns=[
            r"現金及約當現金(?:之)?(?:淨增減|淨變動|增減數)",
            r"(?:net\s*)?(?:increase|decrease|change)\s*in\s*cash",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "beginning_cash": PatternDef(
        name="期初現金",
        name_en="Beginning Cash",
        patterns=[
            r"期初現金及約當現金",
            r"期初現金餘額",
            r"(?:beginning|opening)\s*cash\s*(?:balance)?",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    
    "ending_cash": PatternDef(
        name="期末現金",
        name_en="Ending Cash",
        patterns=[
            r"期末現金及約當現金",
            r"期末現金餘額",
            r"(?:ending|closing)\s*cash\s*(?:balance)?",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.CRITICAL,
    ),
    
    "free_cash_flow": PatternDef(
        name="自由現金流量",
        name_en="Free Cash Flow",
        patterns=[
            r"自由現金流量?",
            r"free\s*cash\s*flow",
            r"FCF",
        ],
        category=CategoryType.OPERATING_CF,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 三之一、權益變動表 (Statement of Changes in Equity) 模式
# ═══════════════════════════════════════════════════════════════════════════════

EQUITY_CHANGE_PATTERNS = {
    "equity_beginning_balance": PatternDef(
        name="本期期初餘額",
        name_en="Beginning Balance",
        patterns=[
            r"本期期初餘額",
            r"期初權益餘額",
            r"beginning\s*balance",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.EQUITY_CHANGE,
        validation_level=ValidationLevel.CRITICAL,
    ),
    "equity_increase": PatternDef(
        name="本期權益增加",
        name_en="Increase in Equity",
        patterns=[
            r"本期權益增加",
            r"權益增加",
            r"increase\s*in\s*equity",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.EQUITY_CHANGE,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    "equity_decrease": PatternDef(
        name="本期權益減少",
        name_en="Decrease in Equity",
        patterns=[
            r"本期權益減少",
            r"權益減少",
            r"decrease\s*in\s*equity",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.EQUITY_CHANGE,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    "equity_ending_balance": PatternDef(
        name="本期期末餘額",
        name_en="Ending Balance",
        patterns=[
            r"本期期末餘額",
            r"期末權益餘額",
            r"ending\s*balance",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.EQUITY_CHANGE,
        validation_level=ValidationLevel.CRITICAL,
    ),
    "appropriation_legal_reserve": PatternDef(
        name="提列法定盈餘公積",
        name_en="Appropriation of Legal Reserve",
        patterns=[
            r"提列法定盈餘公積",
            r"法定盈餘公積",
            r"legal\s*reserve\s*appropriation",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.EQUITY_CHANGE,
        validation_level=ValidationLevel.OPTIONAL,
    ),
    "dividend_distribution": PatternDef(
        name="盈餘分配",
        name_en="Dividend Distribution",
        patterns=[
            r"盈餘分配",
            r"股利分配",
            r"dividend\s*distribution",
        ],
        category=CategoryType.EQUITY,
        statement=StatementType.EQUITY_CHANGE,
        validation_level=ValidationLevel.IMPORTANT,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 四、財務比率 (Financial Ratios) 模式
# ═══════════════════════════════════════════════════════════════════════════════

RATIO_PATTERNS = {
    # ─────────────────────────────────────────────────────────────────────────
    # 流動性比率 (Liquidity Ratios)
    # ─────────────────────────────────────────────────────────────────────────
    "current_ratio": PatternDef(
        name="流動比率",
        name_en="Current Ratio",
        patterns=[
            r"流動比率",
            r"current\s*ratio",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="流動資產 / 流動負債 × 100%"
    ),
    
    "quick_ratio": PatternDef(
        name="速動比率",
        name_en="Quick Ratio",
        patterns=[
            r"速動比率",
            r"酸性測試比率",
            r"quick\s*ratio",
            r"acid[- ]?test\s*ratio",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="(流動資產 - 存貨 - 預付款項) / 流動負債 × 100%"
    ),
    
    "cash_ratio": PatternDef(
        name="現金比率",
        name_en="Cash Ratio",
        patterns=[
            r"現金比率",
            r"cash\s*ratio",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="%",
        description="現金及約當現金 / 流動負債 × 100%"
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 償債能力比率 (Solvency Ratios)
    # ─────────────────────────────────────────────────────────────────────────
    "debt_ratio": PatternDef(
        name="負債比率",
        name_en="Debt Ratio",
        patterns=[
            r"負債比率",
            r"負債佔資產比率",
            r"debt\s*ratio",
            r"debt\s*to\s*assets?\s*ratio",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="負債總額 / 資產總額 × 100%"
    ),
    
    "debt_equity_ratio": PatternDef(
        name="負債權益比率",
        name_en="Debt to Equity Ratio",
        patterns=[
            r"負債[對占佔]?權益比率",
            r"負債權益比",
            r"債務權益比",
            r"debt\s*(?:to\s*)?equity\s*ratio",
            r"D/E\s*ratio",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="負債總額 / 權益總額 × 100%"
    ),
    
    "interest_coverage": PatternDef(
        name="利息保障倍數",
        name_en="Interest Coverage Ratio",
        patterns=[
            r"利息保障倍數",
            r"interest\s*coverage\s*ratio",
            r"times\s*interest\s*earned",
            r"TIE",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="倍",
        description="(稅前淨利 + 利息費用) / 利息費用"
    ),
    
    "long_term_debt_ratio": PatternDef(
        name="長期資金占固定資產比率",
        name_en="Long-term Fund to Fixed Asset Ratio",
        patterns=[
            r"長期資金[占佔]固定資產比率",
            r"long[- ]?term\s*fund\s*to\s*fixed\s*asset\s*ratio",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="%",
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 獲利能力比率 (Profitability Ratios)
    # ─────────────────────────────────────────────────────────────────────────
    "gross_margin": PatternDef(
        name="毛利率",
        name_en="Gross Margin",
        patterns=[
            r"毛利率",
            r"營業毛利率",
            r"gross\s*(?:profit\s*)?margin",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="毛利 / 營業收入 × 100%"
    ),
    
    "operating_margin": PatternDef(
        name="營業利益率",
        name_en="Operating Margin",
        patterns=[
            r"營業利益率",
            r"營業淨利率",
            r"operating\s*(?:profit\s*)?margin",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="營業利益 / 營業收入 × 100%"
    ),
    
    "net_profit_margin": PatternDef(
        name="淨利率",
        name_en="Net Profit Margin",
        patterns=[
            r"淨利率",
            r"稅後淨利率",
            r"純益率",
            r"net\s*(?:profit\s*)?margin",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="淨利 / 營業收入 × 100%"
    ),
    
    "roe": PatternDef(
        name="股東權益報酬率",
        name_en="Return on Equity",
        patterns=[
            r"股東權益報酬率",
            r"權益報酬率",
            r"return\s*on\s*equity",
            r"ROE",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="淨利 / 平均股東權益 × 100%"
    ),
    
    "roa": PatternDef(
        name="資產報酬率",
        name_en="Return on Assets",
        patterns=[
            r"資產報酬率",
            r"總資產報酬率",
            r"return\s*on\s*assets?",
            r"ROA",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="%",
        description="淨利 / 平均總資產 × 100%"
    ),
    
    "roic": PatternDef(
        name="投入資本報酬率",
        name_en="Return on Invested Capital",
        patterns=[
            r"投入資本報酬率",
            r"投資資本報酬率",
            r"return\s*on\s*invested\s*capital",
            r"ROIC",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="%",
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 經營效率比率 (Efficiency Ratios)
    # ─────────────────────────────────────────────────────────────────────────
    "asset_turnover": PatternDef(
        name="資產週轉率",
        name_en="Asset Turnover",
        patterns=[
            r"(?:總)?資產週轉率",
            r"asset\s*turnover",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="次",
        description="營業收入 / 平均總資產"
    ),
    
    "inventory_turnover": PatternDef(
        name="存貨週轉率",
        name_en="Inventory Turnover",
        patterns=[
            r"存貨週轉率",
            r"存貨周轉率",
            r"inventory\s*turnover",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="次",
        description="營業成本 / 平均存貨"
    ),
    
    "inventory_days": PatternDef(
        name="平均售貨天數",
        name_en="Days Inventory Outstanding",
        patterns=[
            r"平均售貨天數",
            r"存貨週轉天數",
            r"days\s*inventor(?:y|ies)\s*(?:outstanding)?",
            r"DIO",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="天",
        description="365 / 存貨週轉率"
    ),
    
    "receivable_turnover": PatternDef(
        name="應收帳款週轉率",
        name_en="Receivables Turnover",
        patterns=[
            r"應收(?:帳|款項?)款?週轉率",
            r"receivables?\s*turnover",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="次",
        description="營業收入 / 平均應收帳款"
    ),
    
    "receivable_days": PatternDef(
        name="平均收現天數",
        name_en="Days Sales Outstanding",
        patterns=[
            r"平均收現天數",
            r"應收帳款週轉天數",
            r"days\s*sales\s*outstanding",
            r"DSO",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="天",
        description="365 / 應收帳款週轉率"
    ),
    
    "payable_turnover": PatternDef(
        name="應付帳款週轉率",
        name_en="Payables Turnover",
        patterns=[
            r"應付(?:帳|款項?)款?週轉率",
            r"payables?\s*turnover",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="次",
    ),
    
    "payable_days": PatternDef(
        name="平均付款天數",
        name_en="Days Payable Outstanding",
        patterns=[
            r"平均付款天數",
            r"應付帳款週轉天數",
            r"days\s*payable\s*outstanding",
            r"DPO",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="天",
    ),
    
    "cash_conversion_cycle": PatternDef(
        name="現金轉換週期",
        name_en="Cash Conversion Cycle",
        patterns=[
            r"現金(?:轉換|循環)週期",
            r"cash\s*conversion\s*cycle",
            r"CCC",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="天",
        description="存貨週轉天數 + 應收帳款週轉天數 - 應付帳款週轉天數"
    ),
    
    "fixed_asset_turnover": PatternDef(
        name="固定資產週轉率",
        name_en="Fixed Asset Turnover",
        patterns=[
            r"固定資產週轉率",
            r"不動產[、,]?廠房及設備週轉率",
            r"fixed\s*asset\s*turnover",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="次",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 五、每股指標 (Per Share Metrics) 模式
# ═══════════════════════════════════════════════════════════════════════════════

PER_SHARE_PATTERNS = {
    "eps_basic": PatternDef(
        name="基本每股盈餘",
        name_en="Basic EPS",
        patterns=[
            r"基本每股盈餘",
            r"基本每股(?:淨)?(?:利|損)",
            r"每股盈餘[（\(]基本[）\)]",
            r"basic\s*(?:earnings?\s*per\s*share|EPS)",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
        unit="元",
        description="歸屬母公司淨利 / 加權平均流通在外股數"
    ),
    
    "eps_diluted": PatternDef(
        name="稀釋每股盈餘",
        name_en="Diluted EPS",
        patterns=[
            r"稀釋每股盈餘",
            r"稀釋每股(?:淨)?(?:利|損)",
            r"每股盈餘[（\(]稀釋[）\)]",
            r"diluted\s*(?:earnings?\s*per\s*share|EPS)",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.CRITICAL,
        unit="元",
    ),
    
    "book_value_per_share": PatternDef(
        name="每股淨值",
        name_en="Book Value Per Share",
        patterns=[
            r"每股淨值",
            r"每股帳面價值",
            r"book\s*value\s*per\s*share",
            r"BVPS",
            r"NAV\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.CRITICAL,
        unit="元",
        description="股東權益 / 流通在外股數"
    ),
    
    "cash_per_share": PatternDef(
        name="每股現金",
        name_en="Cash Per Share",
        patterns=[
            r"每股現金(?:及約當現金)?",
            r"cash\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.BALANCE_SHEET,
        validation_level=ValidationLevel.IMPORTANT,
        unit="元",
    ),
    
    "operating_cf_per_share": PatternDef(
        name="每股營業現金流",
        name_en="Operating Cash Flow Per Share",
        patterns=[
            r"每股營業?活動?現金流(?:量)?",
            r"每股營運現金流",
            r"operating\s*cash\s*flow\s*per\s*share",
            r"CFO\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
        unit="元",
    ),
    
    "free_cf_per_share": PatternDef(
        name="每股自由現金流",
        name_en="Free Cash Flow Per Share",
        patterns=[
            r"每股自由現金流(?:量)?",
            r"free\s*cash\s*flow\s*per\s*share",
            r"FCF\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.CASH_FLOW,
        validation_level=ValidationLevel.IMPORTANT,
        unit="元",
    ),
    
    "dividend_per_share": PatternDef(
        name="每股股利",
        name_en="Dividend Per Share",
        patterns=[
            r"每股股利",
            r"每股(?:現金)?股息",
            r"dividend\s*per\s*share",
            r"DPS",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="元",
    ),
    
    "cash_dividend_per_share": PatternDef(
        name="每股現金股利",
        name_en="Cash Dividend Per Share",
        patterns=[
            r"每股現金股利",
            r"現金股利每股",
            r"cash\s*dividend\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="元",
    ),
    
    "stock_dividend_per_share": PatternDef(
        name="每股股票股利",
        name_en="Stock Dividend Per Share",
        patterns=[
            r"每股股票股利",
            r"股票股利每股",
            r"stock\s*dividend\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="元",
    ),
    
    "revenue_per_share": PatternDef(
        name="每股營收",
        name_en="Revenue Per Share",
        patterns=[
            r"每股營(?:業)?收(?:入)?",
            r"revenue\s*per\s*share",
            r"sales\s*per\s*share",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.INCOME_STATEMENT,
        validation_level=ValidationLevel.OPTIONAL,
        unit="元",
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # 估值指標 (Valuation Metrics)
    # ─────────────────────────────────────────────────────────────────────────
    "pe_ratio": PatternDef(
        name="本益比",
        name_en="P/E Ratio",
        patterns=[
            r"本益比",
            r"市盈率",
            r"P/?E\s*ratio",
            r"price[- ]?(?:to[- ]?)?earnings?\s*ratio",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="倍",
        description="股價 / 每股盈餘"
    ),
    
    "pb_ratio": PatternDef(
        name="股價淨值比",
        name_en="P/B Ratio",
        patterns=[
            r"股價淨值比",
            r"市淨率",
            r"P/?B\s*ratio",
            r"price[- ]?(?:to[- ]?)?book\s*ratio",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.CRITICAL,
        unit="倍",
        description="股價 / 每股淨值"
    ),
    
    "ps_ratio": PatternDef(
        name="股價營收比",
        name_en="P/S Ratio",
        patterns=[
            r"股價營收比",
            r"市銷率",
            r"P/?S\s*ratio",
            r"price[- ]?(?:to[- ]?)?sales\s*ratio",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="倍",
    ),
    
    "pcf_ratio": PatternDef(
        name="股價現金流量比",
        name_en="P/CF Ratio",
        patterns=[
            r"股價現金流(?:量)?比",
            r"P/?CF\s*ratio",
            r"price[- ]?(?:to[- ]?)?cash\s*flow\s*ratio",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="倍",
    ),
    
    "ev_ebitda": PatternDef(
        name="企業價值倍數",
        name_en="EV/EBITDA",
        patterns=[
            r"企業價值倍數",
            r"EV/?EBITDA",
            r"enterprise\s*value\s*(?:to\s*)?EBITDA",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="倍",
    ),
    
    "dividend_yield": PatternDef(
        name="殖利率",
        name_en="Dividend Yield",
        patterns=[
            r"(?:現金)?股利?殖利率",
            r"股息(?:收益)?率",
            r"dividend\s*yield",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="%",
        description="每股股利 / 股價 × 100%"
    ),
    
    "payout_ratio": PatternDef(
        name="配息率",
        name_en="Payout Ratio",
        patterns=[
            r"配息率",
            r"股利發放率",
            r"dividend\s*payout\s*ratio",
            r"payout\s*ratio",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="%",
        description="每股股利 / 每股盈餘 × 100%"
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # 投資研究報告常用 (目標價、評等、成長率)
    # ─────────────────────────────────────────────────────────────────────────
    "target_price": PatternDef(
        name="目標價",
        name_en="Target Price",
        patterns=[
            r"目標價(?:格)?",
            r"target\s*price",
            r"TP\s*[：:]?\s*\d+",
        ],
        category=CategoryType.PER_SHARE,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="元",
    ),
    "investment_rating": PatternDef(
        name="投資評等",
        name_en="Investment Rating",
        patterns=[
            r"投資評等",
            r"評等[：:]?\s*(?:買進|持有|賣出|加碼|減碼|中立|優於大盤|劣於大盤)",
            r"investment\s*rating",
            r"recommendation",
            r"(?:買進|持有|賣出|加碼|減碼|中立|Buy|Hold|Sell|Overweight|Underweight)",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
    ),
    "revenue_growth": PatternDef(
        name="營收成長率",
        name_en="Revenue Growth Rate",
        patterns=[
            r"營收成長率",
            r"營收(?:YoY|YOY|年增|年減|成長)",
            r"revenue\s*growth",
            r"sales\s*growth",
            r"YoY\s*[：:]?\s*[-+]?\d",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.IMPORTANT,
        unit="%",
    ),
    "eps_growth": PatternDef(
        name="每股盈餘成長率",
        name_en="EPS Growth Rate",
        patterns=[
            r"每股盈餘成長率",
            r"EPS(?:成長|YoY|年增)",
            r"EPS\s*growth",
        ],
        category=CategoryType.RATIO,
        statement=StatementType.NOTES,
        validation_level=ValidationLevel.OPTIONAL,
        unit="%",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 六、數值提取模式
# ═══════════════════════════════════════════════════════════════════════════════

NUMBER_PATTERNS = {
    "amount_tw": re.compile(
        r'(?:NT\$?|新?[臺台]?幣?)?\s*([-−]?\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*(?:元|千元|萬元|百萬|億|仟元)?'
    ),
    "amount_parenthesis": re.compile(
        r'\(?\s*([-−]?\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*\)?'
    ),
    "percentage": re.compile(
        r'([-−+]?\d+(?:\.\d+)?)\s*[%％]'
    ),
    "ratio": re.compile(
        r'([-−]?\d+(?:\.\d+)?)\s*(?:倍|次|天|日)'
    ),
    "eps": re.compile(
        r'(?:每股[盈虧][餘損]?|EPS)[：:\s]*([-−]?\d+(?:\.\d+)?)'
    ),
    "per_share": re.compile(
        r'每股[^\d]*([-−]?\d+(?:\.\d+)?)'
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 統一模式字典
# ═══════════════════════════════════════════════════════════════════════════════

ALL_PATTERNS: Dict[str, PatternDef] = {}
ALL_PATTERNS.update(BALANCE_SHEET_PATTERNS)
ALL_PATTERNS.update(INCOME_STATEMENT_PATTERNS)
ALL_PATTERNS.update(CASH_FLOW_PATTERNS)
ALL_PATTERNS.update(EQUITY_CHANGE_PATTERNS)
ALL_PATTERNS.update(RATIO_PATTERNS)
ALL_PATTERNS.update(PER_SHARE_PATTERNS)


# ═══════════════════════════════════════════════════════════════════════════════
# 主要類別
# ═══════════════════════════════════════════════════════════════════════════════

class InvestmentPatternMatcher:
    """投資報表模式匹配器"""
    
    def __init__(self):
        self.patterns = ALL_PATTERNS
        self.number_patterns = NUMBER_PATTERNS
    
    def extract_value(self, text: str, field_key: str) -> Optional[ExtractedValue]:
        """提取指定欄位的數值"""
        pattern_def = self.patterns.get(field_key)
        if not pattern_def:
            return None
        
        match = pattern_def.match(text)
        if not match:
            return None
        
        # 找到匹配位置後，嘗試提取數值
        match_pos = match.end()
        remaining_text = text[match_pos:match_pos + 100]
        
        # 嘗試提取數值
        value = None
        if pattern_def.unit == "%":
            num_match = self.number_patterns["percentage"].search(remaining_text)
        elif pattern_def.unit in ["倍", "次", "天"]:
            num_match = self.number_patterns["ratio"].search(remaining_text)
        else:
            num_match = self.number_patterns["amount_tw"].search(remaining_text)
        
        if num_match:
            try:
                value_str = num_match.group(1).replace(',', '').replace('，', '').replace('−', '-')
                value = float(value_str)
            except ValueError:
                return None
            
            return ExtractedValue(
                field_name=pattern_def.name,
                field_name_en=pattern_def.name_en,
                value=value,
                unit=pattern_def.unit,
                confidence=0.9,
                source_text=text[match.start():match_pos + num_match.end()],
                category=pattern_def.category,
                statement=pattern_def.statement
            )
        
        return None
    
    def extract_all(self, text: str) -> Dict[str, ExtractedValue]:
        """提取所有可識別的數值"""
        results = {}
        
        for field_key in self.patterns:
            value = self.extract_value(text, field_key)
            if value:
                results[field_key] = value
        
        return results
    
    def extract_by_statement(self, text: str, statement: StatementType) -> Dict[str, ExtractedValue]:
        """按報表類型提取"""
        results = {}
        
        for field_key, pattern_def in self.patterns.items():
            if pattern_def.statement == statement:
                value = self.extract_value(text, field_key)
                if value:
                    results[field_key] = value
        
        return results


class FinancialDataValidator:
    """財務資料驗證器"""
    
    def __init__(self, patterns: Dict[str, PatternDef] = None):
        self.patterns = patterns or ALL_PATTERNS
    
    def validate_completeness(self, extracted_data: Dict[str, Any], 
                             statement_type: StatementType = None) -> ValidationResult:
        """驗證資料完整性"""
        result = ValidationResult(is_valid=True)
        
        total_critical = 0
        found_critical = 0
        total_important = 0
        found_important = 0
        
        for field_key, pattern_def in self.patterns.items():
            # 如果指定了報表類型，只檢查該類型
            if statement_type and pattern_def.statement != statement_type:
                continue
            
            if pattern_def.validation_level == ValidationLevel.CRITICAL:
                total_critical += 1
                if field_key in extracted_data:
                    found_critical += 1
                else:
                    result.missing_critical.append(pattern_def.name)
                    result.is_valid = False
            
            elif pattern_def.validation_level == ValidationLevel.IMPORTANT:
                total_important += 1
                if field_key in extracted_data:
                    found_important += 1
                else:
                    result.missing_important.append(pattern_def.name)
        
        # 計算完整性分數
        if total_critical > 0:
            critical_score = found_critical / total_critical
        else:
            critical_score = 1.0
        
        if total_important > 0:
            important_score = found_important / total_important
        else:
            important_score = 1.0
        
        result.completeness_score = critical_score * 0.7 + important_score * 0.3
        
        return result
    
    def validate_consistency(self, data: Dict[str, float]) -> ValidationResult:
        """驗證資料一致性"""
        result = ValidationResult(is_valid=True)
        
        # 1. 資產負債表平衡檢查
        if "total_assets" in data and "total_liabilities_equity" in data:
            diff = abs(data["total_assets"] - data["total_liabilities_equity"])
            tolerance = abs(data["total_assets"]) * 0.001  # 0.1% 容差
            if diff > tolerance:
                result.errors.append(
                    f"資產負債表不平衡: 資產={data['total_assets']}, 負債+權益={data['total_liabilities_equity']}"
                )
                result.is_valid = False
        
        # 2. 流動資產加總檢查
        if "total_current_assets" in data:
            current_asset_items = ["cash", "short_term_investment", "accounts_receivable", 
                                  "notes_receivable", "inventory", "prepaid_expenses"]
            calculated_total = sum(data.get(item, 0) for item in current_asset_items)
            if calculated_total > 0:
                diff = abs(data["total_current_assets"] - calculated_total)
                if diff > abs(data["total_current_assets"]) * 0.1:  # 10% 容差
                    result.warnings.append(
                        f"流動資產明細加總與合計有差異: 合計={data['total_current_assets']}, 計算={calculated_total}"
                    )
        
        # 3. 毛利計算檢查
        if "revenue" in data and "cost_of_sales" in data and "gross_profit" in data:
            calculated_gross = data["revenue"] - data["cost_of_sales"]
            diff = abs(data["gross_profit"] - calculated_gross)
            if diff > abs(data["gross_profit"]) * 0.01:
                result.warnings.append(
                    f"毛利計算不一致: 報表毛利={data['gross_profit']}, 計算毛利={calculated_gross}"
                )
        
        # 4. 營業利益計算檢查
        if "gross_profit" in data and "total_operating_expenses" in data and "operating_income" in data:
            calculated_op = data["gross_profit"] - data["total_operating_expenses"]
            diff = abs(data["operating_income"] - calculated_op)
            if diff > abs(data["operating_income"]) * 0.01:
                result.warnings.append(
                    f"營業利益計算不一致: 報表={data['operating_income']}, 計算={calculated_op}"
                )
        
        # 5. 現金流量表檢查
        if all(k in data for k in ["operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_change_in_cash"]):
            calculated_change = (data["operating_cash_flow"] + 
                               data["investing_cash_flow"] + 
                               data["financing_cash_flow"])
            diff = abs(data["net_change_in_cash"] - calculated_change)
            if diff > abs(data["net_change_in_cash"]) * 0.01:
                result.warnings.append(
                    f"現金變動計算不一致: 報表={data['net_change_in_cash']}, 計算={calculated_change}"
                )
        
        # 6. 每股盈餘合理性檢查
        if "eps_basic" in data:
            if abs(data["eps_basic"]) > 100:
                result.warnings.append(f"EPS 數值異常高: {data['eps_basic']}")
            if "eps_diluted" in data and data["eps_diluted"] > data["eps_basic"]:
                result.warnings.append("稀釋 EPS 高於基本 EPS (異常)")
        
        # 計算一致性分數
        error_penalty = len(result.errors) * 0.2
        warning_penalty = len(result.warnings) * 0.05
        result.consistency_score = max(0, 1.0 - error_penalty - warning_penalty)
        
        return result
    
    def validate_ratios(self, data: Dict[str, float]) -> ValidationResult:
        """驗證財務比率合理性"""
        result = ValidationResult(is_valid=True)
        
        # 比率合理範圍
        ratio_ranges = {
            "current_ratio": (0, 1000),      # 0% ~ 1000%
            "quick_ratio": (0, 1000),
            "debt_ratio": (0, 100),           # 0% ~ 100%
            "gross_margin": (-100, 100),      # -100% ~ 100%
            "operating_margin": (-100, 100),
            "net_profit_margin": (-100, 100),
            "roe": (-100, 200),
            "roa": (-50, 100),
            "pe_ratio": (0, 500),             # 0 ~ 500 倍
            "pb_ratio": (0, 100),
            "dividend_yield": (0, 30),        # 0% ~ 30%
        }
        
        for ratio_key, (min_val, max_val) in ratio_ranges.items():
            if ratio_key in data:
                value = data[ratio_key]
                if value < min_val or value > max_val:
                    result.warnings.append(
                        f"{ratio_key} 數值超出合理範圍: {value} (合理範圍: {min_val} ~ {max_val})"
                    )
        
        return result
    
    def full_validation(self, extracted_data: Dict[str, Any]) -> ValidationResult:
        """完整驗證"""
        # 提取數值
        data_values = {}
        for key, value in extracted_data.items():
            if isinstance(value, ExtractedValue):
                data_values[key] = value.value
            elif isinstance(value, (int, float)):
                data_values[key] = value
        
        # 執行各項驗證
        completeness_result = self.validate_completeness(extracted_data)
        consistency_result = self.validate_consistency(data_values)
        ratio_result = self.validate_ratios(data_values)
        
        # 合併結果
        final_result = ValidationResult(
            is_valid=completeness_result.is_valid and consistency_result.is_valid,
            missing_critical=completeness_result.missing_critical,
            missing_important=completeness_result.missing_important,
            warnings=completeness_result.warnings + consistency_result.warnings + ratio_result.warnings,
            errors=completeness_result.errors + consistency_result.errors + ratio_result.errors,
            completeness_score=completeness_result.completeness_score,
            consistency_score=consistency_result.consistency_score
        )
        
        return final_result


# ═══════════════════════════════════════════════════════════════════════════════
# 報表分析類
# ═══════════════════════════════════════════════════════════════════════════════

class FinancialStatementAnalyzer:
    """財務報表分析器"""
    
    def __init__(self):
        self.matcher = InvestmentPatternMatcher()
        self.validator = FinancialDataValidator()
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """分析財務報表文本"""
        # 提取所有數據
        extracted = self.matcher.extract_all(text)
        
        # 按報表分類
        by_statement = {
            "balance_sheet": {},
            "income_statement": {},
            "cash_flow": {},
            "equity_change": {},
            "ratios": {},
            "per_share": {}
        }
        
        for key, value in extracted.items():
            if value.statement == StatementType.BALANCE_SHEET:
                by_statement["balance_sheet"][key] = value
            elif value.statement == StatementType.INCOME_STATEMENT:
                by_statement["income_statement"][key] = value
            elif value.statement == StatementType.CASH_FLOW:
                by_statement["cash_flow"][key] = value
            elif value.statement == StatementType.EQUITY_CHANGE:
                by_statement["equity_change"][key] = value
            elif value.category == CategoryType.RATIO:
                by_statement["ratios"][key] = value
            elif value.category == CategoryType.PER_SHARE:
                by_statement["per_share"][key] = value
        
        # 驗證
        validation = self.validator.full_validation(extracted)
        
        return {
            "extracted": extracted,
            "by_statement": by_statement,
            "validation": validation,
            "summary": {
                "total_fields": len(extracted),
                "completeness_score": validation.completeness_score,
                "consistency_score": validation.consistency_score,
                "is_valid": validation.is_valid
            }
        }
    
    def get_missing_fields(self, statement_type: StatementType = None) -> List[str]:
        """取得缺失的必要欄位"""
        missing = []
        for key, pattern_def in ALL_PATTERNS.items():
            if statement_type and pattern_def.statement != statement_type:
                continue
            if pattern_def.validation_level == ValidationLevel.CRITICAL:
                missing.append(pattern_def.name)
        return missing


# ═══════════════════════════════════════════════════════════════════════════════
# 標準接口
# ═══════════════════════════════════════════════════════════════════════════════

def get_version() -> str:
    """取得版本"""
    return __version__


def get_status() -> Dict[str, Any]:
    """取得狀態"""
    return {
        "module": "InvestmentRegexPattern_VALIDATED",
        "version": __version__,
        "total_patterns": len(ALL_PATTERNS),
        "balance_sheet_patterns": len(BALANCE_SHEET_PATTERNS),
        "income_statement_patterns": len(INCOME_STATEMENT_PATTERNS),
        "cash_flow_patterns": len(CASH_FLOW_PATTERNS),
        "equity_change_patterns": len(EQUITY_CHANGE_PATTERNS),
        "ratio_patterns": len(RATIO_PATTERNS),
        "per_share_patterns": len(PER_SHARE_PATTERNS),
        "ready": True
    }


def run_test() -> bool:
    """執行測試"""
    logger.info("Testing InvestmentRegexPattern_VALIDATED...")
    
    try:
        # 測試資產負債表模式
        test_text = """
        資產負債表
        現金及約當現金 1,234,567,890
        應收帳款 456,789,012
        存貨 234,567,890
        流動資產合計 2,000,000,000
        不動產廠房及設備 3,500,000,000
        資產總計 6,000,000,000
        應付帳款 300,000,000
        流動負債合計 800,000,000
        負債總計 2,000,000,000
        股本 2,500,000,000
        保留盈餘 1,500,000,000
        權益總計 4,000,000,000
        負債及權益總計 6,000,000,000
        """
        
        matcher = InvestmentPatternMatcher()
        results = matcher.extract_by_statement(test_text, StatementType.BALANCE_SHEET)
        assert len(results) > 0, "應該提取到資產負債表項目"
        
        # 測試損益表模式
        income_text = """
        損益表
        營業收入 5,000,000,000
        營業成本 3,500,000,000
        營業毛利 1,500,000,000
        營業費用合計 500,000,000
        營業利益 1,000,000,000
        稅前淨利 1,050,000,000
        本期淨利 850,000,000
        基本每股盈餘 8.5 元
        """
        
        income_results = matcher.extract_by_statement(income_text, StatementType.INCOME_STATEMENT)
        assert len(income_results) > 0, "應該提取到損益表項目"
        
        # 測試現金流量表模式
        cf_text = """
        現金流量表
        營業活動淨現金流入 1,200,000,000
        投資活動淨現金流出 -500,000,000
        籌資活動淨現金流出 -300,000,000
        現金及約當現金淨增減 400,000,000
        """
        
        cf_results = matcher.extract_by_statement(cf_text, StatementType.CASH_FLOW)
        assert len(cf_results) > 0, "應該提取到現金流量表項目"
        
        # 測試比率模式
        ratio_text = """
        財務比率
        流動比率 250%
        速動比率 180%
        負債比率 33.3%
        毛利率 30%
        營業利益率 20%
        淨利率 17%
        股東權益報酬率 21.25%
        資產報酬率 14.17%
        本益比 12 倍
        每股淨值 40 元
        """
        
        ratio_results = matcher.extract_all(ratio_text)
        ratio_count = sum(1 for k, v in ratio_results.items() 
                        if v.category in [CategoryType.RATIO, CategoryType.PER_SHARE])
        assert ratio_count > 0, "應該提取到比率指標"
        
        # 測試驗證器
        validator = FinancialDataValidator()
        validation = validator.validate_completeness(results, StatementType.BALANCE_SHEET)
        assert validation.completeness_score >= 0, "應該計算出完整性分數"
        
        # 測試分析器
        analyzer = FinancialStatementAnalyzer()
        full_analysis = analyzer.analyze(test_text + income_text + cf_text + ratio_text)
        assert full_analysis["summary"]["total_fields"] > 0, "應該分析出多個欄位"
        
        logger.info("All tests passed!")
        logger.info(f"Total patterns: {len(ALL_PATTERNS)}")
        logger.info(f"Extracted fields: {full_analysis['summary']['total_fields']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 主程式
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
    
    print("=" * 70)
    print("InvestmentRegexPattern_VALIDATED v" + __version__)
    print("=" * 70)
    
    status = get_status()
    print(f"\n📊 模式統計:")
    print(f"   資產負債表模式: {status['balance_sheet_patterns']} 個")
    print(f"   損益表模式: {status['income_statement_patterns']} 個")
    print(f"   現金流量表模式: {status['cash_flow_patterns']} 個")
    print(f"   權益變動表模式: {status['equity_change_patterns']} 個")
    print(f"   財務比率模式: {status['ratio_patterns']} 個")
    print(f"   每股指標模式: {status['per_share_patterns']} 個")
    print(f"   總計: {status['total_patterns']} 個模式")
    
    print("\n🧪 執行測試...")
    if run_test():
        print("\n✅ 所有測試通過!")
    else:
        print("\n❌ 測試失敗!")
