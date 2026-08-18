#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeritasSynonymEngine™ - 財務分類規則完整版
Financial Classification Rules - Complete Edition

Version: 3.0
Author: Tony's Development Team
Philosophy: 功能只增不減 (Functionality Only Increases, Never Decreases)

資料來源整合:
- TWSE/TPEX API 欄位
- TWSTOCK 套件欄位
- YFINANCE 每季財報欄位
- 其他同義字擴充
"""

import re
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# ◆◆◆ SECTION 1: TICKER REGEX PATTERNS 股票代碼正則表達式 ◆◆◆
# =============================================================================

class TickerRegex:
    """
    台灣股票代碼 REGEX 定義
    
    格式說明:
    - TICKER (Pure)       : 2330 (TWSE/TPEX/twstock 使用)
    - YFINANCE_TICKER     : 2330.TW / 2330.TWO (yfinance 使用)
    - BLOOMBERG_TICKER    : 2330 TT (Bloomberg Terminal 使用)
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # 台股專用 REGEX (首碼非零的四位數字)
    # ═══════════════════════════════════════════════════════════════════════
    
    # 1️⃣ 母代號格式（寬鬆）：純四碼數字，首碼非零
    TW_TICKER_REGEX = re.compile(r"\b[1-9]\d{3}\b")
    # ✅ Examples: 2330, 2454, 2317, 3008, 6505
    
    # 2️⃣ Yahoo Finance 格式（次嚴格）：四碼 + .TW/.TWO
    TW_YFINANCE_REGEX = re.compile(r"\b[1-9]\d{3}\.(TW|TWO)\b")
    # ✅ Examples: 2330.TW (上市), 6488.TWO (上櫃)
    
    # 3️⃣ Bloomberg 格式（最嚴格）：四碼 + 空格 + TT
    TW_BLOOMBERG_REGEX = re.compile(r"\b[1-9]\d{3} TT\b")
    # ✅ Examples: 2330 TT, 2454 TT
    
    # 4️⃣ 萬用提取器（智能識別所有格式）
    TW_CODE_EXTRACT = re.compile(r"\b([1-9]\d{3})(?:\s+TT|\.(?:TW|TWO))?\b")
    # ✅ 從任何格式提取母代號
    
    # ═══════════════════════════════════════════════════════════════════════
    # 其他市場 TICKER REGEX (擴充用)
    # ═══════════════════════════════════════════════════════════════════════
    
    # 美股
    US_TICKER_REGEX = re.compile(r"\b[A-Z]{1,5}\b")
    US_BLOOMBERG_REGEX = re.compile(r"\b[A-Z]{1,5}\s+US(?:\s+Equity)?\b")
    US_YFINANCE_REGEX = re.compile(r"\b[A-Z]{1,5}\b")
    
    # 港股
    HK_TICKER_REGEX = re.compile(r"\b\d{4,5}\b")
    HK_BLOOMBERG_REGEX = re.compile(r"\b\d{4,5}\s+HK(?:\s+Equity)?\b")
    HK_YFINANCE_REGEX = re.compile(r"\b\d{4,5}\.HK\b")
    
    # 日股
    JP_TICKER_REGEX = re.compile(r"\b\d{4}\b")
    JP_BLOOMBERG_REGEX = re.compile(r"\b\d{4}\s+JP(?:\s+Equity)?\b")
    JP_YFINANCE_REGEX = re.compile(r"\b\d{4}\.T\b")
    
    # 中國 A 股
    CN_TICKER_REGEX = re.compile(r"\b[036]\d{5}\b")
    CN_BLOOMBERG_REGEX = re.compile(r"\b[036]\d{5}\s+CH(?:\s+Equity)?\b")
    CN_YFINANCE_REGEX = re.compile(r"\b[036]\d{5}\.(SS|SZ)\b")
    
    # 外匯
    FOREX_REGEX = re.compile(r"\b[A-Z]{3}[/-]?[A-Z]{3}\b")
    FOREX_YFINANCE_REGEX = re.compile(r"\b[A-Z]{6}=X\b")
    
    # 加密貨幣
    CRYPTO_REGEX = re.compile(r"\b[A-Z]{3,5}-USD\b")
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, re.Pattern]:
        """取得所有 Ticker Pattern"""
        return {
            'TW_TICKER': cls.TW_TICKER_REGEX,
            'TW_YFINANCE': cls.TW_YFINANCE_REGEX,
            'TW_BLOOMBERG': cls.TW_BLOOMBERG_REGEX,
            'TW_EXTRACT': cls.TW_CODE_EXTRACT,
            'US_TICKER': cls.US_TICKER_REGEX,
            'US_BLOOMBERG': cls.US_BLOOMBERG_REGEX,
            'HK_TICKER': cls.HK_TICKER_REGEX,
            'HK_BLOOMBERG': cls.HK_BLOOMBERG_REGEX,
            'HK_YFINANCE': cls.HK_YFINANCE_REGEX,
            'JP_TICKER': cls.JP_TICKER_REGEX,
            'JP_BLOOMBERG': cls.JP_BLOOMBERG_REGEX,
            'JP_YFINANCE': cls.JP_YFINANCE_REGEX,
            'CN_TICKER': cls.CN_TICKER_REGEX,
            'CN_BLOOMBERG': cls.CN_BLOOMBERG_REGEX,
            'CN_YFINANCE': cls.CN_YFINANCE_REGEX,
            'FOREX': cls.FOREX_REGEX,
            'FOREX_YFINANCE': cls.FOREX_YFINANCE_REGEX,
            'CRYPTO': cls.CRYPTO_REGEX,
        }


# =============================================================================
# ◆◆◆ SECTION 2: DATE & TIME REGEX PATTERNS 日期時間正則表達式 ◆◆◆
# =============================================================================

class DateTimeRegex:
    """
    完整日期時間 REGEX 定義
    包含: 年度、年季、月份、日期格式
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # 年度 REGEX (Year Patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    # 西元年 (1900-2099)
    WESTERN_YEAR_REGEX = re.compile(r"\b(19|20)\d{2}\b")
    # ✅ 2024, 2023, 1999
    
    # 民國年 (數字)
    ROC_YEAR_REGEX = re.compile(r"\b(民國)?\s*(\d{2,3})\s*年\b")
    # ✅ 民國113年, 113年, 民國 112 年
    
    # 會計年度 (Fiscal Year)
    FISCAL_YEAR_REGEX = re.compile(
        r"\b(FY|財年|會計年度|fiscal[\s\-]?year)\s*[-]?\s*(\d{2,4})\b",
        re.IGNORECASE
    )
    # ✅ FY2024, FY-2024, FY24, 財年2024, 會計年度2024
    
    # 年度估計/實際標記
    YEAR_ESTIMATE_REGEX = re.compile(r"\b(20\d{2})([AEFCTaefct])\b")
    # ✅ 2024E (估計), 2024A (實際), 2024F (預測), 2024C (共識)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 年季 REGEX (Quarter Patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    # 季度格式 (中文)
    QUARTER_ZH_REGEX = re.compile(r"\b(第)?([一二三四1-4])\s*季\b")
    # ✅ 第一季, 一季, 第1季, 1季
    
    # 季度格式 (英文 Q1-Q4)
    QUARTER_EN_REGEX = re.compile(r"\b[Qq]([1-4])\b")
    # ✅ Q1, Q2, q3, Q4
    
    # 季度格式 (英文 1Q-4Q)
    QUARTER_EN_ALT_REGEX = re.compile(r"\b([1-4])[Qq]\b")
    # ✅ 1Q, 2Q, 3q, 4Q
    
    # 年度+季度複合格式
    YEAR_QUARTER_REGEX = re.compile(
        r"\b(?:"
        r"([1-4])Q(\d{2,4})|"           # 1Q24, 1Q2024
        r"(\d{2,4})Q([1-4])|"           # 2024Q1, 24Q1
        r"Q([1-4])[\s\-/]?(\d{2,4})|"   # Q1 2024, Q1-2024
        r"FY(\d{2,4})Q([1-4])"          # FY2024Q1
        r")\b"
    )
    # ✅ 1Q24, 2024Q1, Q1 2024, FY2024Q1
    
    # 半年度
    HALF_YEAR_REGEX = re.compile(
        r"\b(上半年|下半年|[HhＨｈ][12]|1H|2H|"
        r"first[\s\-]?half|second[\s\-]?half)\b",
        re.IGNORECASE
    )
    # ✅ 上半年, 下半年, H1, H2, 1H, 2H
    
    # ═══════════════════════════════════════════════════════════════════════
    # 月份 REGEX (Month Patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    # 月份 (數字 01-12)
    MONTH_NUM_REGEX = re.compile(r"\b(0?[1-9]|1[0-2])\s*月?\b")
    # ✅ 1, 01, 12, 1月, 12月
    
    # 月份 (中文)
    MONTH_ZH_REGEX = re.compile(
        r"\b([一二三四五六七八九十]?[一二三四五六七八九十])\s*月\b"
    )
    # ✅ 一月, 十二月
    
    # 月份 (英文簡寫)
    MONTH_EN_ABBR_REGEX = re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\b",
        re.IGNORECASE
    )
    # ✅ Jan, Feb, Mar, Jan., Sept
    
    # 月份 (英文全稱)
    MONTH_EN_FULL_REGEX = re.compile(
        r"\b(January|February|March|April|May|June|"
        r"July|August|September|October|November|December)\b",
        re.IGNORECASE
    )
    # ✅ January, February, December
    
    # ═══════════════════════════════════════════════════════════════════════
    # 完整日期 REGEX (Full Date Patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    # 西元日期 (數字格式，分隔符: / - . _ 空白)
    DATE_NUMERIC_REGEX = re.compile(
        r"\b\d{4}[-\/._\s]?\d{1,2}[-\/._\s]?\d{1,2}\b"
    )
    # ✅ 2024/07/25, 2024-07-25, 20240725, 2024.07.25
    
    # 英文日期 (MMM DD, YYYY)
    DATE_EN_MDY_REGEX = re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE
    )
    # ✅ Jan 5, 2024, Dec. 25, 2023
    
    # 英文日期 (DD MMM YYYY)
    DATE_EN_DMY_REGEX = re.compile(
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{4}\b",
        re.IGNORECASE
    )
    # ✅ 5 Jan 2024, 25 Dec 2023
    
    # 英文日期完整月份 (Month DD, YYYY)
    DATE_EN_FULL_MDY_REGEX = re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE
    )
    # ✅ January 5, 2024, December 25, 2023
    
    # 民國日期 (數字格式 YYY/MM/DD)
    ROC_DATE_NUMERIC_REGEX = re.compile(
        r"\b(1\d{2}|2\d{2})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b"
    )
    # ✅ 113/07/25, 112-1-5, 101.12.31
    
    # 民國日期 (中文格式)
    ROC_DATE_ZH_REGEX = re.compile(
        r"民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    )
    # ✅ 民國113年7月25日, 民國 112 年 1 月 5 日
    
    # ISO 8601 日期時間
    ISO_DATETIME_REGEX = re.compile(
        r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
    )
    # ✅ 2024-01-15T10:30:00Z, 2024-01-15T10:30:00+08:00
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, re.Pattern]:
        """取得所有日期時間 Pattern"""
        return {
            # 年度
            'WESTERN_YEAR': cls.WESTERN_YEAR_REGEX,
            'ROC_YEAR': cls.ROC_YEAR_REGEX,
            'FISCAL_YEAR': cls.FISCAL_YEAR_REGEX,
            'YEAR_ESTIMATE': cls.YEAR_ESTIMATE_REGEX,
            # 季度
            'QUARTER_ZH': cls.QUARTER_ZH_REGEX,
            'QUARTER_EN': cls.QUARTER_EN_REGEX,
            'QUARTER_EN_ALT': cls.QUARTER_EN_ALT_REGEX,
            'YEAR_QUARTER': cls.YEAR_QUARTER_REGEX,
            'HALF_YEAR': cls.HALF_YEAR_REGEX,
            # 月份
            'MONTH_NUM': cls.MONTH_NUM_REGEX,
            'MONTH_ZH': cls.MONTH_ZH_REGEX,
            'MONTH_EN_ABBR': cls.MONTH_EN_ABBR_REGEX,
            'MONTH_EN_FULL': cls.MONTH_EN_FULL_REGEX,
            # 完整日期
            'DATE_NUMERIC': cls.DATE_NUMERIC_REGEX,
            'DATE_EN_MDY': cls.DATE_EN_MDY_REGEX,
            'DATE_EN_DMY': cls.DATE_EN_DMY_REGEX,
            'DATE_EN_FULL_MDY': cls.DATE_EN_FULL_MDY_REGEX,
            'ROC_DATE_NUMERIC': cls.ROC_DATE_NUMERIC_REGEX,
            'ROC_DATE_ZH': cls.ROC_DATE_ZH_REGEX,
            'ISO_DATETIME': cls.ISO_DATETIME_REGEX,
        }


# =============================================================================
# ◆◆◆ SECTION 3: FINANCIAL CLASSIFICATION 財務分類規則 ◆◆◆
# =============================================================================

# ═══════════════════════════════════════════════════════════════════════════
# 損益表指標 Income Statement Features
# ═══════════════════════════════════════════════════════════════════════════

INCOME_FEATURES: Dict[str, Dict[str, Any]] = {
    # ────────────────────────────────────────────────────────────────────────
    # 營業收入 Revenue
    # ────────────────────────────────────────────────────────────────────────
    "Revenue": {
        "regex": r"(營業收入|Revenue|營收|Sales|Net\s+Revenue|Net\s+Sales|"
                 r"Total\s+Revenue|totalRevenue|totalSales|operatingRevenue|"
                 r"revenueTTM|銷售收入|主營業務收入|營業收入合計|營業收入淨額)",
        "twse_tpex": "營業收入",
        "twstock": "revenue",
        "yfinance": "totalRevenue",
        "synonyms": ["營業收入", "Revenue", "營收", "Sales", "銷售收入", 
                     "Net Revenue", "Net Sales", "Total Revenue", "主營業務收入"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 營業成本 Cost of Revenue
    # ────────────────────────────────────────────────────────────────────────
    "CostOfRevenue": {
        "regex": r"(營業成本|Cost\s+of\s+Revenue|COGS|Cost\s+of\s+Goods\s+Sold|"
                 r"銷貨成本|costOfRevenue|costOfGoodsSold|直接成本|製造成本)",
        "twse_tpex": "營業成本",
        "twstock": "cost",
        "yfinance": "costOfRevenue",
        "synonyms": ["營業成本", "Cost of Revenue", "COGS", "銷貨成本", 
                     "Cost of Goods Sold", "直接成本", "製造成本"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 營業毛利 Gross Profit
    # ────────────────────────────────────────────────────────────────────────
    "GrossProfit": {
        "regex": r"(毛利|Gross\s+Profit|營業毛利|GP|毛利額|Gross\s+Income|"
                 r"grossProfit|毛利合計|營業毛利合計|銷售毛利|毛益)",
        "twse_tpex": "營業毛利（毛損）",
        "twstock": "gross_profit",
        "yfinance": "grossProfit",
        "synonyms": ["毛利", "Gross Profit", "營業毛利", "GP", "毛利額",
                     "Gross Income", "毛益", "銷售毛利"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 營業費用 Operating Expenses
    # ────────────────────────────────────────────────────────────────────────
    "OperatingExpenses": {
        "regex": r"(營業費用|Operating\s+Expenses|OpEx|SG&A|營業費用合計|"
                 r"operatingExpenses|totalOperatingExpenses|營運費用|管銷費用)",
        "twse_tpex": "營業費用",
        "twstock": "operating_expenses",
        "yfinance": "operatingExpenses",
        "synonyms": ["營業費用", "Operating Expenses", "OpEx", "SG&A",
                     "營運費用", "管銷費用", "銷售及管理費用"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 研發費用 R&D Expenses
    # ────────────────────────────────────────────────────────────────────────
    "RDExpenses": {
        "regex": r"(研發費用|R&D\s+Expenses|研究發展費用|研發支出|"
                 r"researchAndDevelopment|rdExpenses|技術開發費用|研究費)",
        "twse_tpex": "研究發展費用",
        "twstock": "rd_expenses",
        "yfinance": "researchAndDevelopment",
        "synonyms": ["研發費用", "R&D Expenses", "研究發展費用", "研發支出",
                     "R&D", "技術開發費用", "研究費"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 營業利益 Operating Income
    # ────────────────────────────────────────────────────────────────────────
    "OperatingProfit": {
        "regex": r"(營業利益|Operating\s+Profit|Operating\s+Income|EBIT|"
                 r"營業獲利|operatingIncome|totalOperatingIncome|營業損益|"
                 r"營業利潤|Operating\s+Earnings|營業盈利)",
        "twse_tpex": "營業利益（損失）",
        "twstock": "operating_income",
        "yfinance": "operatingIncome",
        "synonyms": ["營業利益", "Operating Profit", "Operating Income", "EBIT",
                     "營業利潤", "營業獲利", "營業損益", "Operating Earnings"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 營業外收入 Non-operating Income
    # ────────────────────────────────────────────────────────────────────────
    "NonOperatingIncome": {
        "regex": r"(營業外收入|Non-operating\s+Income|業外收入|Other\s+Income|"
                 r"otherIncomeExpense|nonOperatingIncome|投資收益)",
        "twse_tpex": "營業外收入及支出",
        "twstock": "non_operating_income",
        "yfinance": "otherIncomeExpense",
        "synonyms": ["營業外收入", "Non-operating Income", "業外收入",
                     "Other Income", "投資收益", "業外收益"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 稅前純益 Pre-tax Income
    # ────────────────────────────────────────────────────────────────────────
    "PreTaxIncome": {
        "regex": r"(稅前純益|Pre-tax\s+Income|EBT|Earnings\s+Before\s+Tax|"
                 r"稅前盈餘|pretaxIncome|incomeBeforeTax|稅前利益)",
        "twse_tpex": "稅前淨利（淨損）",
        "twstock": "pretax_income",
        "yfinance": "incomeBeforeTax",
        "synonyms": ["稅前純益", "Pre-tax Income", "EBT", "Earnings Before Tax",
                     "稅前盈餘", "稅前利益", "稅前淨利"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 本期淨利 Net Income
    # ────────────────────────────────────────────────────────────────────────
    "NetIncome": {
        "regex": r"(本期淨利|稅後淨利|Net\s+Income|Net\s+Profit|淨利|"
                 r"Earnings\s+after\s+tax|Profit\s+after\s+tax|netIncome|"
                 r"稅後純益|本期純益|歸屬母公司淨利|稅後損益)",
        "twse_tpex": "本期淨利（淨損）",
        "twstock": "net_income",
        "yfinance": "netIncome",
        "synonyms": ["本期淨利", "Net Income", "Net Profit", "稅後淨利",
                     "淨利", "Profit After Tax", "稅後純益", "歸屬母公司淨利"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # EBITDA
    # ────────────────────────────────────────────────────────────────────────
    "EBITDA": {
        "regex": r"(EBITDA|息前稅前折舊攤銷前利益|稅息折舊攤銷前盈餘|"
                 r"ebitda|Earnings\s+Before\s+Interest.*Depreciation)",
        "twse_tpex": "--",
        "twstock": "--",
        "yfinance": "ebitda",
        "synonyms": ["EBITDA", "息前稅前折舊攤銷前利益", "稅息折舊攤銷前盈餘"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 每股指標 Per Share Metrics
    # ────────────────────────────────────────────────────────────────────────
    "BasicEPS": {
        "regex": r"(每股盈餘|Basic\s+EPS|EPS|基本每股盈餘|EPSb|basicEPS|"
                 r"basicEps|basicEarningsPerShare|每股稅後盈餘|每股淨利)",
        "twse_tpex": "基本每股盈餘",
        "twstock": "eps",
        "yfinance": "basicEps",
        "synonyms": ["每股盈餘", "Basic EPS", "EPS", "基本每股盈餘",
                     "每股稅後盈餘", "每股淨利", "每股純益"]
    },
    
    "DilutedEPS": {
        "regex": r"(稀釋每股盈餘|Diluted\s+EPS|完全稀釋EPS|EPSd|dilutedEPS|"
                 r"dilutedEps|FD\s*EPS|稀釋後每股盈餘)",
        "twse_tpex": "稀釋每股盈餘",
        "twstock": "diluted_eps",
        "yfinance": "dilutedEps",
        "synonyms": ["稀釋每股盈餘", "Diluted EPS", "完全稀釋EPS",
                     "FD EPS", "稀釋後每股盈餘"]
    },
    
    "DPS": {
        "regex": r"(每股現金股利|DPS|Dividend\s+per\s+share|股息|現金股利|"
                 r"dividendRate|每股派息|CashDividendPerShare)",
        "twse_tpex": "每股現金股利",
        "twstock": "dividend",
        "yfinance": "dividendRate",
        "synonyms": ["每股現金股利", "DPS", "Dividend per share", "股息",
                     "現金股利", "每股派息", "每股股利"]
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# 資產負債表指標 Balance Sheet Features
# ═══════════════════════════════════════════════════════════════════════════

BALANCE_FEATURES: Dict[str, Dict[str, Any]] = {
    # ────────────────────────────────────────────────────────────────────────
    # 資產類
    # ────────────────────────────────────────────────────────────────────────
    "TotalAssets": {
        "regex": r"(資產總額|Total\s+Assets|資產總計|總資產|totalAssets|"
                 r"資產合計|全部資產)",
        "twse_tpex": "資產總額",
        "twstock": "total_assets",
        "yfinance": "totalAssets",
        "synonyms": ["資產總額", "Total Assets", "資產總計", "總資產", "資產合計"]
    },
    
    "CurrentAssets": {
        "regex": r"(流動資產|Current\s+Assets|短期資產|currentAssets|"
                 r"流動資產總額|流動資產合計)",
        "twse_tpex": "流動資產",
        "twstock": "current_assets",
        "yfinance": "currentAssets",
        "synonyms": ["流動資產", "Current Assets", "短期資產", "流動資產總額"]
    },
    
    "Cash": {
        "regex": r"(現金及約當現金|Cash|Cash\s+Equivalents|現金|"
                 r"cashAndCashEquivalents|貨幣資金)",
        "twse_tpex": "現金及約當現金",
        "twstock": "cash",
        "yfinance": "cashAndCashEquivalents",
        "synonyms": ["現金及約當現金", "Cash", "Cash Equivalents", "現金", "貨幣資金"]
    },
    
    "AccountsReceivable": {
        "regex": r"(應收帳款|Accounts\s+Receivable|A/R|應收款項|"
                 r"accountsReceivable|應收帳款淨額)",
        "twse_tpex": "應收帳款",
        "twstock": "accounts_receivable",
        "yfinance": "accountsReceivable",
        "synonyms": ["應收帳款", "Accounts Receivable", "A/R", "應收款項"]
    },
    
    "Inventory": {
        "regex": r"(存貨|Inventory|庫存|商品存貨|inventory|存貨淨額)",
        "twse_tpex": "存貨",
        "twstock": "inventory",
        "yfinance": "inventory",
        "synonyms": ["存貨", "Inventory", "庫存", "商品存貨"]
    },
    
    "PPE": {
        "regex": r"(不動產廠房設備|PPE|Property\s+Plant\s+Equipment|"
                 r"固定資產|propertyPlantEquipment|廠房設備)",
        "twse_tpex": "不動產、廠房及設備",
        "twstock": "ppe",
        "yfinance": "propertyPlantEquipment",
        "synonyms": ["不動產廠房設備", "PPE", "Property Plant Equipment", "固定資產"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 負債類
    # ────────────────────────────────────────────────────────────────────────
    "TotalLiabilities": {
        "regex": r"(負債總額|Total\s+Liabilities|負債總計|總負債|"
                 r"totalLiabilities|負債合計)",
        "twse_tpex": "負債總額",
        "twstock": "total_liabilities",
        "yfinance": "totalLiabilities",
        "synonyms": ["負債總額", "Total Liabilities", "負債總計", "總負債"]
    },
    
    "CurrentLiabilities": {
        "regex": r"(流動負債|Current\s+Liabilities|短期負債|"
                 r"currentLiabilities|流動負債總額)",
        "twse_tpex": "流動負債",
        "twstock": "current_liabilities",
        "yfinance": "currentLiabilities",
        "synonyms": ["流動負債", "Current Liabilities", "短期負債"]
    },
    
    "TotalDebt": {
        "regex": r"(總負債|Total\s+Debt|Debt|借款總額|totalDebt|"
                 r"長短期借款合計)",
        "twse_tpex": "借款",
        "twstock": "total_debt",
        "yfinance": "totalDebt",
        "synonyms": ["總負債", "Total Debt", "Debt", "借款總額"]
    },
    
    "ShortTermDebt": {
        "regex": r"(短期借款|Short\s+Term\s+Debt|shortTermDebt|短期負債)",
        "twse_tpex": "短期借款",
        "twstock": "short_term_debt",
        "yfinance": "shortTermDebt",
        "synonyms": ["短期借款", "Short Term Debt", "短期負債"]
    },
    
    "LongTermDebt": {
        "regex": r"(長期借款|Long\s+Term\s+Debt|longTermDebt|長期負債)",
        "twse_tpex": "長期借款",
        "twstock": "long_term_debt",
        "yfinance": "longTermDebt",
        "synonyms": ["長期借款", "Long Term Debt", "長期負債"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 股東權益類
    # ────────────────────────────────────────────────────────────────────────
    "TotalEquity": {
        "regex": r"(股東權益|Total\s+Equity|Shareholders'\s+Equity|權益總額|"
                 r"totalStockholderEquity|totalEquity|淨資產|股東權益總額)",
        "twse_tpex": "權益總額",
        "twstock": "total_equity",
        "yfinance": "totalStockholderEquity",
        "synonyms": ["股東權益", "Total Equity", "Shareholders' Equity",
                     "權益總額", "淨資產", "股東權益總額"]
    },
    
    "RetainedEarnings": {
        "regex": r"(保留盈餘|Retained\s+Earnings|未分配盈餘|retainedEarnings|"
                 r"累計盈餘)",
        "twse_tpex": "保留盈餘",
        "twstock": "retained_earnings",
        "yfinance": "retainedEarnings",
        "synonyms": ["保留盈餘", "Retained Earnings", "未分配盈餘", "累計盈餘"]
    },
    
    "BVPS": {
        "regex": r"(每股淨值|BVPS|Book\s+Value\s+Per\s+Share|每股帳面價值|"
                 r"bookValuePerShare|NAV\s+per\s+share|股東權益每股淨值)",
        "twse_tpex": "每股淨值",
        "twstock": "bvps",
        "yfinance": "bookValue",
        "synonyms": ["每股淨值", "BVPS", "Book Value Per Share", "每股帳面價值",
                     "NAV Per Share", "每股淨資產"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 股數
    # ────────────────────────────────────────────────────────────────────────
    "SharesOutstanding": {
        "regex": r"(流通在外股數|Shares\s+Outstanding|發行股數|sharesOutstanding|"
                 r"普通股股數|市場流通股)",
        "twse_tpex": "普通股股數",
        "twstock": "shares_outstanding",
        "yfinance": "sharesOutstanding",
        "synonyms": ["流通在外股數", "Shares Outstanding", "發行股數", "普通股股數"]
    },
    
    "WeightedAvgShares": {
        "regex": r"(加權平均普通股數|Weighted\s+Avg\s+Shares|加權平均股數|"
                 r"Average\s+Shares|基本股數)",
        "twse_tpex": "加權平均普通股數",
        "twstock": "weighted_avg_shares",
        "yfinance": "--",
        "synonyms": ["加權平均普通股數", "Weighted Avg Shares", "加權平均股數"]
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# 現金流量表指標 Cash Flow Features
# ═══════════════════════════════════════════════════════════════════════════

CASHFLOW_FEATURES: Dict[str, Dict[str, Any]] = {
    "OperatingCashFlow": {
        "regex": r"(營業活動現金流|Operating\s+Cash\s+Flow|CFO|OCF|"
                 r"operatingCashflow|營運現金流|營業現金流量)",
        "twse_tpex": "營業活動之淨現金流入（流出）",
        "twstock": "operating_cashflow",
        "yfinance": "operatingCashflow",
        "synonyms": ["營業活動現金流", "Operating Cash Flow", "CFO", "OCF", "營運現金流"]
    },
    
    "InvestingCashFlow": {
        "regex": r"(投資活動現金流|Investing\s+Cash\s+Flow|CFI|"
                 r"investingCashflow|投資現金流)",
        "twse_tpex": "投資活動之淨現金流入（流出）",
        "twstock": "investing_cashflow",
        "yfinance": "investingCashflow",
        "synonyms": ["投資活動現金流", "Investing Cash Flow", "CFI", "投資現金流"]
    },
    
    "FinancingCashFlow": {
        "regex": r"(籌資活動現金流|Financing\s+Cash\s+Flow|CFF|"
                 r"financingCashflow|融資現金流|理財活動現金流)",
        "twse_tpex": "籌資活動之淨現金流入（流出）",
        "twstock": "financing_cashflow",
        "yfinance": "financingCashflow",
        "synonyms": ["籌資活動現金流", "Financing Cash Flow", "CFF", "融資現金流"]
    },
    
    "CapEx": {
        "regex": r"(資本支出|CapEx|Capital\s+Expenditures|capitalExpenditures|"
                 r"資本性支出|固定資產投資)",
        "twse_tpex": "資本支出",
        "twstock": "capex",
        "yfinance": "capitalExpenditures",
        "synonyms": ["資本支出", "CapEx", "Capital Expenditures", "資本性支出"]
    },
    
    "FCF": {
        "regex": r"(自由現金流|FCF|Free\s+Cash\s+Flow|freeCashflow|"
                 r"自由現金流量)",
        "twse_tpex": "--",
        "twstock": "fcf",
        "yfinance": "freeCashflow",
        "synonyms": ["自由現金流", "FCF", "Free Cash Flow", "自由現金流量"]
    },
    
    "DividendsPaid": {
        "regex": r"(現金股利發放|Dividends\s+Paid|股息支付|dividendsPaid|"
                 r"現金股利支付|股利發放)",
        "twse_tpex": "發放現金股利",
        "twstock": "dividends_paid",
        "yfinance": "dividendsPaid",
        "synonyms": ["現金股利發放", "Dividends Paid", "股息支付", "股利發放"]
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# KPI / 財務比率指標 KPI Features
# ═══════════════════════════════════════════════════════════════════════════

KPI_FEATURES: Dict[str, Dict[str, Any]] = {
    # ────────────────────────────────────────────────────────────────────────
    # 獲利能力
    # ────────────────────────────────────────────────────────────────────────
    "ROE": {
        "regex": r"(ROE|股東權益報酬率|Return\s+on\s+Equity|淨值報酬率|"
                 r"returnOnEquity|ROAE|權益報酬率|股東權益回報率)",
        "twse_tpex": "股東權益報酬率",
        "twstock": "roe",
        "yfinance": "returnOnEquity",
        "synonyms": ["ROE", "股東權益報酬率", "Return on Equity", "淨值報酬率",
                     "ROAE", "權益報酬率"]
    },
    
    "ROA": {
        "regex": r"(ROA|資產報酬率|Return\s+on\s+Assets|總資產報酬率|"
                 r"returnOnAssets|ROAA|資產回報率)",
        "twse_tpex": "資產報酬率",
        "twstock": "roa",
        "yfinance": "returnOnAssets",
        "synonyms": ["ROA", "資產報酬率", "Return on Assets", "總資產報酬率", "ROAA"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 利潤率
    # ────────────────────────────────────────────────────────────────────────
    "GrossMargin": {
        "regex": r"(毛利率|Gross\s+Margin|Gross\s+Profit\s+Margin|"
                 r"grossMargin|營業毛利率|毛利潤率)",
        "twse_tpex": "毛利率",
        "twstock": "gross_margin",
        "yfinance": "grossMargins",
        "synonyms": ["毛利率", "Gross Margin", "Gross Profit Margin", "營業毛利率"]
    },
    
    "OperatingMargin": {
        "regex": r"(營業利益率|Operating\s+Margin|EBIT\s+Margin|"
                 r"operatingMargin|營業淨利率|營運利益率)",
        "twse_tpex": "營業利益率",
        "twstock": "operating_margin",
        "yfinance": "operatingMargins",
        "synonyms": ["營業利益率", "Operating Margin", "EBIT Margin", "營業淨利率"]
    },
    
    "NetMargin": {
        "regex": r"(淨利率|Net\s+Margin|Net\s+Profit\s+Margin|NPM|"
                 r"profitMargin|純益率|稅後淨利率)",
        "twse_tpex": "淨利率",
        "twstock": "net_margin",
        "yfinance": "profitMargins",
        "synonyms": ["淨利率", "Net Margin", "Net Profit Margin", "純益率", "NPM"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 成長率
    # ────────────────────────────────────────────────────────────────────────
    "YOY": {
        "regex": r"(年增率|YoY|Year\s+over\s+Year|同比增長|yoyGrowth|"
                 r"年對年成長率|同期比較)",
        "twse_tpex": "年增率",
        "twstock": "yoy",
        "yfinance": "--",
        "synonyms": ["年增率", "YoY", "Year over Year", "同比增長", "年對年成長率"]
    },
    
    "QOQ": {
        "regex": r"(季增率|QoQ|Quarter\s+over\s+Quarter|環比增長|qoqGrowth|"
                 r"季對季成長率)",
        "twse_tpex": "季增率",
        "twstock": "qoq",
        "yfinance": "--",
        "synonyms": ["季增率", "QoQ", "Quarter over Quarter", "環比增長"]
    },
    
    "RevenueGrowth": {
        "regex": r"(營收成長率|Revenue\s+Growth|營收年增率|revenueGrowth|"
                 r"銷售成長率)",
        "twse_tpex": "營收成長率",
        "twstock": "revenue_growth",
        "yfinance": "revenueGrowth",
        "synonyms": ["營收成長率", "Revenue Growth", "營收年增率", "銷售成長率"]
    },
    
    "EPSGrowth": {
        "regex": r"(EPS成長率|EPS\s+Growth|每股盈餘成長率|epsGrowth|"
                 r"每股盈餘年增率)",
        "twse_tpex": "EPS成長率",
        "twstock": "eps_growth",
        "yfinance": "earningsGrowth",
        "synonyms": ["EPS成長率", "EPS Growth", "每股盈餘成長率"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 估值指標
    # ────────────────────────────────────────────────────────────────────────
    "PE": {
        "regex": r"(本益比|P/E|PE\s+Ratio|PER|市盈率|trailingPE|forwardPE|"
                 r"股價盈餘比)",
        "twse_tpex": "本益比",
        "twstock": "pe_ratio",
        "yfinance": "trailingPE",
        "synonyms": ["本益比", "P/E", "PE Ratio", "PER", "市盈率", "股價盈餘比"]
    },
    
    "PB": {
        "regex": r"(股價淨值比|P/B|PB\s+Ratio|PBR|市淨率|priceToBook|"
                 r"市價淨值比)",
        "twse_tpex": "股價淨值比",
        "twstock": "pb_ratio",
        "yfinance": "priceToBook",
        "synonyms": ["股價淨值比", "P/B", "PB Ratio", "PBR", "市淨率"]
    },
    
    "PS": {
        "regex": r"(股價營收比|P/S|PS\s+Ratio|PSR|市銷率|priceToSales)",
        "twse_tpex": "股價營收比",
        "twstock": "ps_ratio",
        "yfinance": "priceToSales",
        "synonyms": ["股價營收比", "P/S", "PS Ratio", "PSR", "市銷率"]
    },
    
    "DividendYield": {
        "regex": r"(股利殖利率|Dividend\s+Yield|殖利率|dividendYield|"
                 r"現金殖利率|配息率)",
        "twse_tpex": "現金殖利率",
        "twstock": "dividend_yield",
        "yfinance": "dividendYield",
        "synonyms": ["股利殖利率", "Dividend Yield", "殖利率", "現金殖利率"]
    },
    
    # ────────────────────────────────────────────────────────────────────────
    # 財務結構
    # ────────────────────────────────────────────────────────────────────────
    "DebtRatio": {
        "regex": r"(負債比率|Debt\s+Ratio|負債率|debtRatio|總負債比率)",
        "twse_tpex": "負債比率",
        "twstock": "debt_ratio",
        "yfinance": "--",
        "synonyms": ["負債比率", "Debt Ratio", "負債率", "總負債比率"]
    },
    
    "DebtToEquity": {
        "regex": r"(負債權益比|Debt\s+to\s+Equity|D/E\s+Ratio|debtToEquity|"
                 r"負債對權益比率|槓桿比率)",
        "twse_tpex": "負債權益比",
        "twstock": "debt_to_equity",
        "yfinance": "debtToEquity",
        "synonyms": ["負債權益比", "Debt to Equity", "D/E Ratio", "槓桿比率"]
    },
    
    "CurrentRatio": {
        "regex": r"(流動比率|Current\s+Ratio|currentRatio|短期償債能力)",
        "twse_tpex": "流動比率",
        "twstock": "current_ratio",
        "yfinance": "currentRatio",
        "synonyms": ["流動比率", "Current Ratio", "短期償債能力"]
    },
    
    "QuickRatio": {
        "regex": r"(速動比率|Quick\s+Ratio|quickRatio|酸性測驗比率)",
        "twse_tpex": "速動比率",
        "twstock": "quick_ratio",
        "yfinance": "quickRatio",
        "synonyms": ["速動比率", "Quick Ratio", "酸性測驗比率"]
    },
}


# =============================================================================
# ◆◆◆ SECTION 4: BROKER LIST 券商列表 ◆◆◆
# =============================================================================

BROKER_LIST: List[Dict[str, Any]] = [
    # ═══════════════════════════════════════════════════════════════════════
    # 美國投資銀行 US Investment Banks
    # ═══════════════════════════════════════════════════════════════════════
    {
        "code": "MS",
        "en": "Morgan Stanley",
        "zh": "摩根士丹利",
        "aliases": ["MS", "Morgan Stanley", "摩根士丹利", "摩根史坦利", "大摩"],
        "country": "US",
        "type": "Investment Bank"
    },
    {
        "code": "GS",
        "en": "Goldman Sachs",
        "zh": "高盛",
        "aliases": ["GS", "Goldman Sachs", "Goldman", "高盛", "高盛集團"],
        "country": "US",
        "type": "Investment Bank"
    },
    {
        "code": "JPM",
        "en": "JPMorgan Chase",
        "zh": "摩根大通",
        "aliases": ["JPM", "JPMorgan Chase", "JPMorgan", "JP Morgan", "摩根大通", "JP摩根", "小摩"],
        "country": "US",
        "type": "Investment Bank"
    },
    {
        "code": "CITI",
        "en": "Citigroup",
        "zh": "花旗銀行",
        "aliases": ["CITI", "Citigroup", "Citi", "花旗銀行", "花旗集團", "花旗"],
        "country": "US",
        "type": "Investment Bank"
    },
    {
        "code": "BAML",
        "en": "Bank of America Merrill Lynch",
        "zh": "美國銀行美林證券",
        "aliases": ["BAML", "Bank of America", "BofA", "Merrill Lynch", "美國銀行美林證券", "美林", "美銀美林"],
        "country": "US",
        "type": "Investment Bank"
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 歐洲銀行 European Banks
    # ═══════════════════════════════════════════════════════════════════════
    {
        "code": "UBS",
        "en": "UBS Group AG",
        "zh": "瑞銀集團",
        "aliases": ["UBS", "UBS Group AG", "UBS Group", "瑞銀集團", "瑞銀"],
        "country": "CH",
        "type": "Investment Bank"
    },
    {
        "code": "CS",
        "en": "Credit Suisse",
        "zh": "瑞士信貸",
        "aliases": ["CS", "Credit Suisse", "瑞士信貸", "瑞信"],
        "country": "CH",
        "type": "Investment Bank"
    },
    {
        "code": "DB",
        "en": "Deutsche Bank",
        "zh": "德意志銀行",
        "aliases": ["DB", "Deutsche Bank", "德意志銀行", "德銀"],
        "country": "DE",
        "type": "Investment Bank"
    },
    {
        "code": "HSBC",
        "en": "HSBC Holdings",
        "zh": "滙豐控股",
        "aliases": ["HSBC", "HSBC Holdings", "滙豐控股", "匯豐", "滙豐", "滙豐銀行"],
        "country": "UK/HK",
        "type": "Investment Bank"
    },
    {
        "code": "BARCLAYS",
        "en": "Barclays",
        "zh": "巴克萊銀行",
        "aliases": ["BARCLAYS", "Barclays", "巴克萊銀行", "巴克萊"],
        "country": "UK",
        "type": "Investment Bank"
    },
    {
        "code": "RBC",
        "en": "Royal Bank of Canada",
        "zh": "加拿大皇家銀行",
        "aliases": ["RBC", "Royal Bank of Canada", "RBC Capital", "加拿大皇家銀行", "RBC資本"],
        "country": "CA",
        "type": "Investment Bank"
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 日本券商 Japanese Brokers
    # ═══════════════════════════════════════════════════════════════════════
    {
        "code": "NMR",
        "en": "Nomura Securities",
        "zh": "野村證券",
        "aliases": ["NMR", "Nomura", "Nomura Securities", "野村證券", "野村", "野村控股"],
        "country": "JP",
        "type": "Securities"
    },
    {
        "code": "MIZUHO",
        "en": "Mizuho Financial Group",
        "zh": "みずほ金融集團",
        "aliases": ["MIZUHO", "Mizuho", "Mizuho Financial Group", "みずほ金融集團", "瑞穗", "みずほ證券"],
        "country": "JP",
        "type": "Securities"
    },
    {
        "code": "SMBC",
        "en": "Sumitomo Mitsui Banking Corp.",
        "zh": "三井住友銀行",
        "aliases": ["SMBC", "Sumitomo Mitsui", "三井住友銀行", "SMBC日興"],
        "country": "JP",
        "type": "Securities"
    },
    {
        "code": "MUFG",
        "en": "Mitsubishi UFJ Financial Group",
        "zh": "三菱UFJ銀行",
        "aliases": ["MUFG", "Mitsubishi UFJ", "三菱UFJ銀行", "三菱UFJ摩根士丹利"],
        "country": "JP",
        "type": "Securities"
    },
    {
        "code": "DAIWA",
        "en": "Daiwa Securities",
        "zh": "大和證券",
        "aliases": ["DAIWA", "Daiwa", "Daiwa Securities", "大和證券", "大和"],
        "country": "JP",
        "type": "Securities"
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 台灣券商 Taiwan Brokers
    # ═══════════════════════════════════════════════════════════════════════
    {
        "code": "YUANTA",
        "en": "Yuanta Securities",
        "zh": "元大證券",
        "aliases": ["元大", "Yuanta", "Yuanta Securities", "元大證券", "元大投顧", "元大金控"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "FUBON",
        "en": "Fubon Securities",
        "zh": "富邦證券",
        "aliases": ["富邦", "Fubon", "Fubon Securities", "富邦證券", "富邦投顧", "富邦金控"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "CATHAY",
        "en": "Cathay Securities",
        "zh": "國泰證券",
        "aliases": ["國泰", "Cathay", "Cathay Securities", "國泰證券", "國泰投顧", "國泰金控"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "SINOPAC",
        "en": "SinoPac Securities",
        "zh": "永豐金證券",
        "aliases": ["永豐", "SinoPac", "SinoPac Securities", "永豐金證券", "永豐投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "CAPITAL",
        "en": "Capital Securities",
        "zh": "群益證券",
        "aliases": ["群益", "Capital", "Capital Securities", "群益證券", "群益投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "KGI",
        "en": "KGI Securities",
        "zh": "凱基證券",
        "aliases": ["凱基", "KGI", "KGI Securities", "凱基證券", "凱基投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "TAISHIN",
        "en": "Taishin Securities",
        "zh": "台新證券",
        "aliases": ["台新", "Taishin", "Taishin Securities", "台新證券", "台新投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "FIRST",
        "en": "First Securities",
        "zh": "第一金證券",
        "aliases": ["第一", "First", "First Securities", "第一金證券", "第一金投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "MEGA",
        "en": "Mega Securities",
        "zh": "兆豐證券",
        "aliases": ["兆豐", "Mega", "Mega Securities", "兆豐證券", "兆豐投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "SHINKONG",
        "en": "Shin Kong Securities",
        "zh": "新光證券",
        "aliases": ["新光", "Shin Kong", "Shin Kong Securities", "新光證券", "新光投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "CTBC",
        "en": "CTBC Securities",
        "zh": "中國信託證券",
        "aliases": ["中信", "CTBC", "CTBC Securities", "中國信託證券", "中信投顧"],
        "country": "TW",
        "type": "Securities"
    },
    {
        "code": "ESUN",
        "en": "E.SUN Securities",
        "zh": "玉山證券",
        "aliases": ["玉山", "ESUN", "E.SUN", "E.SUN Securities", "玉山證券", "玉山投顧"],
        "country": "TW",
        "type": "Securities"
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 中國券商 China Brokers
    # ═══════════════════════════════════════════════════════════════════════
    {
        "code": "CICC",
        "en": "China International Capital Corporation",
        "zh": "中金公司",
        "aliases": ["CICC", "China International Capital", "中金公司", "中國國際金融"],
        "country": "CN",
        "type": "Securities"
    },
    {
        "code": "CITIC",
        "en": "CITIC Securities",
        "zh": "中信證券",
        "aliases": ["CITIC", "CITIC Securities", "中信證券", "中信建投"],
        "country": "CN",
        "type": "Securities"
    },
    {
        "code": "HAITONG",
        "en": "Haitong Securities",
        "zh": "海通證券",
        "aliases": ["Haitong", "Haitong Securities", "海通證券"],
        "country": "CN",
        "type": "Securities"
    },
    {
        "code": "GUOTAIJUNAN",
        "en": "Guotai Junan Securities",
        "zh": "國泰君安證券",
        "aliases": ["Guotai Junan", "國泰君安", "國泰君安證券"],
        "country": "CN",
        "type": "Securities"
    },
]


# =============================================================================
# ◆◆◆ SECTION 5: RATING LIST 評等列表 ◆◆◆
# =============================================================================

RATING_DICT: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════════════════
    # 買進類 BUY Level (Score: 4.0-5.0)
    # ═══════════════════════════════════════════════════════════════════════
    "BUY": {
        "level": 1,
        "score_range": (4.0, 5.0),
        "sentiment": "positive",
        "zh": [
            "買進", "買入", "增持", "強力買進", "推薦", "加碼", "積極買進",
            "強烈推薦", "建議買進", "值得買進", "優於大盤", "超配",
            "強力推薦", "極力推薦", "買進評等", "推薦買進", "優先買進"
        ],
        "en": [
            "Buy", "Strong Buy", "Outperform", "Overweight", "Accumulate",
            "Add", "Long", "Conviction Buy", "Top Pick", "Recommended Buy",
            "Strong Outperform", "Aggressive Buy", "Active Buy", "Sector Outperform"
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 持有類 HOLD Level (Score: 2.5-3.9)
    # ═══════════════════════════════════════════════════════════════════════
    "HOLD": {
        "level": 2,
        "score_range": (2.5, 3.9),
        "sentiment": "neutral",
        "zh": [
            "持有", "中立", "觀望", "平衡", "續抱", "維持",
            "中性", "觀望評等", "持有評等", "中立評等",
            "符合大盤", "持平", "標準配置", "區間操作"
        ],
        "en": [
            "Hold", "Neutral", "Market Perform", "Equal Weight",
            "Wait and see", "Maintain", "Peer Perform", "In-Line",
            "Market Weight", "Sector Perform", "Fair Value", "Sector Weight"
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 賣出類 SELL Level (Score: 1.0-2.4)
    # ═══════════════════════════════════════════════════════════════════════
    "SELL": {
        "level": 3,
        "score_range": (1.0, 2.4),
        "sentiment": "negative",
        "zh": [
            "賣出", "減持", "下調", "減碼", "避險", "轉弱",
            "建議賣出", "劣於大盤", "低配", "強烈賣出",
            "賣出評等", "建議減碼", "不推薦"
        ],
        "en": [
            "Sell", "Reduce", "Underperform", "Underweight",
            "Strong Sell", "Short", "Trim", "Lighten",
            "Avoid", "Below Market", "Downgrade", "Sector Underperform"
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # 未評等類 NOT RATED Level (Score: 0)
    # ═══════════════════════════════════════════════════════════════════════
    "NOT_RATED": {
        "level": 0,
        "score_range": (0, 0),
        "sentiment": "unknown",
        "zh": [
            "未評等", "未評級", "無評等", "暫無評等", "無覆蓋",
            "不予評等", "暫不評等", "尚未評級", "無研究覆蓋"
        ],
        "en": [
            "N/A", "Not Rated", "No Rating", "NR", "Not Covered",
            "No Recommendation", "Under Review", "Rating Suspended",
            "No Opinion", "Not Available", "Coverage Dropped"
        ]
    }
}

# 扁平化 Rating List (向後兼容)
RATING_LIST: List[str] = []
for category_data in RATING_DICT.values():
    RATING_LIST.extend(category_data["zh"])
    RATING_LIST.extend(category_data["en"])


# =============================================================================
# ◆◆◆ SECTION 6: HELPER FUNCTIONS 輔助函數 ◆◆◆
# =============================================================================

def get_feature_category(feature_name: str) -> str:
    """
    取得指標所屬分類
    
    Args:
        feature_name: 指標名稱
        
    Returns:
        分類名稱 (損益表/資產負債表/現金流量表/財務比率/未分類)
    """
    if feature_name in INCOME_FEATURES:
        return "損益表"
    elif feature_name in BALANCE_FEATURES:
        return "資產負債表"
    elif feature_name in CASHFLOW_FEATURES:
        return "現金流量表"
    elif feature_name in KPI_FEATURES:
        return "財務比率"
    return "未分類"


def get_all_features() -> Dict[str, Dict[str, Any]]:
    """取得所有財務指標"""
    all_features = {}
    all_features.update(INCOME_FEATURES)
    all_features.update(BALANCE_FEATURES)
    all_features.update(CASHFLOW_FEATURES)
    all_features.update(KPI_FEATURES)
    return all_features


def get_feature_regex(feature_name: str) -> Optional[re.Pattern]:
    """
    取得指標的 REGEX Pattern
    
    Args:
        feature_name: 指標名稱
        
    Returns:
        re.Pattern 物件或 None
    """
    all_features = get_all_features()
    if feature_name in all_features:
        return re.compile(all_features[feature_name]["regex"], re.IGNORECASE)
    return None


def find_broker(text: str) -> Optional[Dict[str, Any]]:
    """
    從文字中識別券商
    
    Args:
        text: 待搜尋的文字
        
    Returns:
        匹配的券商資訊或 None
    """
    text_upper = text.upper()
    for broker in BROKER_LIST:
        for alias in broker["aliases"]:
            if alias.upper() in text_upper:
                return broker
    return None


def find_rating(text: str) -> Optional[Tuple[str, str, int]]:
    """
    從文字中識別評等
    
    Args:
        text: 待搜尋的文字
        
    Returns:
        (評等類別, 匹配詞, 層級) 或 None
    """
    text_upper = text.upper()
    for category, data in RATING_DICT.items():
        for term in data["zh"] + data["en"]:
            if term.upper() in text_upper:
                return (category, term, data["level"])
    return None


def convert_ticker(ticker: str, target_format: str = "pure") -> Optional[str]:
    """
    轉換台股代碼格式
    
    Args:
        ticker: 原始代碼
        target_format: 目標格式 (pure/yfinance/yfinance_two/bloomberg)
        
    Returns:
        轉換後的代碼或 None
    """
    match = TickerRegex.TW_CODE_EXTRACT.search(ticker)
    if not match:
        return None
    
    base = match.group(1)
    
    format_map = {
        "pure": base,
        "yfinance": f"{base}.TW",
        "yfinance_two": f"{base}.TWO",
        "bloomberg": f"{base} TT"
    }
    
    return format_map.get(target_format.lower(), base)


# =============================================================================
# ◆◆◆ SECTION 7: FEATURE SET SHORTCUTS 快速集合 ◆◆◆
# =============================================================================

# 簡化版集合 (向後兼容原始格式)
INCOME_FEATURE_SET: Set[str] = set(INCOME_FEATURES.keys())
BALANCE_FEATURE_SET: Set[str] = set(BALANCE_FEATURES.keys())
CASHFLOW_FEATURE_SET: Set[str] = set(CASHFLOW_FEATURES.keys())
KPI_FEATURE_SET: Set[str] = set(KPI_FEATURES.keys())
ALL_FEATURE_SET: Set[str] = INCOME_FEATURE_SET | BALANCE_FEATURE_SET | CASHFLOW_FEATURE_SET | KPI_FEATURE_SET


# =============================================================================
# ◆◆◆ SECTION 8: SUMMARY STATISTICS 統計摘要 ◆◆◆
# =============================================================================

def print_summary():
    """印出模組統計摘要"""
    print("=" * 80)
    print("VeritasSynonymEngine™ - 財務分類規則完整版 v3.0")
    print("=" * 80)
    print(f"📊 損益表指標 (Income):       {len(INCOME_FEATURES)} 項")
    print(f"📊 資產負債表指標 (Balance):  {len(BALANCE_FEATURES)} 項")
    print(f"📊 現金流量表指標 (CashFlow): {len(CASHFLOW_FEATURES)} 項")
    print(f"📊 財務比率指標 (KPI):        {len(KPI_FEATURES)} 項")
    print("-" * 40)
    print(f"📈 總財務指標數:              {len(ALL_FEATURE_SET)} 項")
    print(f"🏦 券商數量:                  {len(BROKER_LIST)} 家")
    print(f"⭐ 評等詞彙數:                {len(RATING_LIST)} 個")
    print(f"📅 日期 REGEX 模式:           {len(DateTimeRegex.get_all_patterns())} 種")
    print(f"💹 Ticker REGEX 模式:         {len(TickerRegex.get_all_patterns())} 種")
    print("=" * 80)


if __name__ == "__main__":
    print_summary()
