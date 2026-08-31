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
class FinancialDataTester:
    """財務數據測試框架 - 擴展版"""
    
    def __init__(self):
        self.mapper = FinancialFieldsMapper()
        self.validator = ValidationEngine()
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> Dict:
        """載入測試案例 - 包含外部同義字測試"""
        return {
            "positive_cases": {
                "revenue": ["營業收入", "Revenue", "Sales", "總收入", "營收", "OperatingRevenue", "合併營收"],
                "basic_eps": ["基本每股盈餘", "Basic EPS", "每股盈餘(基本)", "basicEPS", "EPSb"],
                "current_ratio": ["流動比率", "Current Ratio", "1.5x", "150%"],
                "external_aliases": ["Net Revenue", "Net Sales", "consolidated sales"]  # 來自JSON的新同義字
            },
            "negative_cases": {
                "invalid_currency": ["abc", "N/A", "--", ""],
                "invalid_percentage": ["abc%", "-%", "infinite"],
                "invalid_ratio": ["x", "ratio", "abc:def"]
            },
            "edge_cases": {
                "zero_values": ["0", "0.0", "0%", "0x"],
                "negative_values": ["-100", "-5.5%", "-1.2x"],
                "large_values": ["999999999", "1000000%", "9999x"]
            },
            "integration_cases": {
                "json_aliases": {
                    "revenue": ["Net Revenue", "OperatingRevenue", "consolidated sales"],
                    "cogs": ["Cost of Goods Sold", "Cost of revenue"],
                    "pe_ratio": ["本益比", "P/E", "PER"]
                }
            }
        }
    
    def run_field_mapping_tests(self) -> Dict[str, bool]:
        """運行欄位映射測試 - 包含擴展同義字測試"""
        results = {}
        
        # 測試所有欄位是否有完整映射
        for category in ['income_statement_fields', 'balance_sheet_fields', 'cashflow_fields', 'ratio_fields']:
            fields = getattr(self.mapper, category)
            for field_key, mapping in fields.items():
                test_name = f"{category}_{field_key}_mapping"
                results[test_name] = all([
                    mapping.chinese_name,
                    mapping.english_name,
                    mapping.twse_tpex_field,
                    mapping.yfinance_field
                ])
        
        # 測試per_share_fields如果存在
        if hasattr(self.mapper, 'per_share_fields'):
            for field_key, mapping in self.mapper.per_share_fields.items():
                test_name = f"per_share_fields_{field_key}_mapping"
                results[test_name] = all([
                    mapping.chinese_name,
                    mapping.english_name,
                    mapping.twse_tpex_field,
                    mapping.yfinance_field
                ])
        
        # 測試外部同義字整合
        for field_name, expected_aliases in self.test_cases["integration_cases"]["json_aliases"].items():
            standardized = self.mapper.standardize_field_name(field_name)
            if standardized:
                all_aliases = self.mapper.get_all_aliases_for_field(standardized)
                test_name = f"external_aliases_{field_name}"
                results[test_name] = any(alias in all_aliases for alias in expected_aliases)
        
        return results
    
    def run_alias_expansion_tests(self) -> Dict[str, bool]:
        """測試同義字擴展功能"""
        results = {}
        
        # 測試動態添加同義字
        test_alias = "測試營收"
        add_result = self.mapper.add_new_alias("revenue", test_alias)
        results["dynamic_alias_addition"] = add_result
        
        # 測試新同義字是否可以被識別
        if add_result:
            standardized = self.mapper.standardize_field_name(test_alias)
            results["dynamic_alias_recognition"] = (standardized == "revenue")
        
        # 測試同義字不重複
        original_count = len(self.mapper.get_all_aliases_for_field("revenue"))
        self.mapper.add_new_alias("revenue", test_alias)  # 重複添#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財務數據標準化規則與驗證系統
包含正則表達式、同義字對照、欄位映射和交互驗證機制
"""

import re
import json
from typing import Dict, List, Union, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field

# =====================================
# 📋 常數定義：正則表達式模式
# =====================================

class RegexPatterns:
    """正則表達式模式集合"""
    
    # ✅ 台股代號格式
    TW_TICKER_BASIC = r"^[1-9]\d{3}$"                          # 基本四碼：2330
    TW_TICKER_TWSE_YFINANCE = r"^[1-9]\d{3}\.TW$"             # TWSE上市：2330.TW
    TW_TICKER_TPEX_YFINANCE = r"^[1-9]\d{3}\.TWO$"            # TPEX上櫃：6488.TWO
    TW_TICKER_BLOOMBERG = r"^[1-9]\d{3}\s+TT$"                # Bloomberg：2330 TT
    
    # ✅ 日期格式
    DATE_NUMERIC = r"\b\d{4}[-\/._\s]?\d{1,2}[-\/._\s]?\d{1,2}\b"                    # 2024/12/31
    DATE_EN_SHORT_MDY = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b"  # Jan 15, 2024
    DATE_EN_SHORT_DMY = r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b"     # 15 Jan 2024
    DATE_EN_SHORT_YMD = r"\b\d{4}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b"     # 2024 Jan 15
    DATE_EN_FULL_MDY = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
    DATE_ROC_NUMERIC = r"\b(1\d{2}|2\d{2})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b"     # 民國113/12/31
    DATE_ROC_CHINESE = r"民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"      # 民國113年12月31日
    
    # ✅ 財務年度期間
    FISCAL_YEAR = r"(20\d{2}[AEFCT]?|FY\d{2,4}|FY-\d{2,4}|12/\d{2}[AEF]?|[1-4]Q\d{2,4}|Q[1-4][\s\-]?\d{2,4}|\d{4}[Ee]|\d{4}[Ff]|年度|會計年度|year|fiscalYear)"
    
    # ✅ 財務數據格式
    CURRENCY_AMOUNT = r"[\$\¥\€\£\₩\₪]?[\d,]+\.?\d*[KMBTkmbt]?"                    # $1.23M, ¥1,234K
    PERCENTAGE = r"\d+\.?\d*\s*%"                                                   # 15.5%
    RATIO = r"\d+\.?\d*[xX]"                                                        # 15.2x

# =====================================
# 📊 財務欄位標準化對照表
# =====================================

@dataclass
class FinancialFieldMapping:
    """財務欄位對照結構"""
    chinese_name: str
    english_name: str
    twse_tpex_field: str
    yfinance_field: str
    synonyms: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)

class FinancialFieldsMapper:
    """財務欄位對照表管理器"""
    
    def __init__(self):
        self.income_statement_fields = self._init_income_statement()
        self.balance_sheet_fields = self._init_balance_sheet()
        self.cashflow_fields = self._init_cashflow()
        self.ratio_fields = self._init_ratios()
        
        # 建立反向查找索引
        self._build_lookup_indices()
    
    def _init_income_statement(self) -> Dict[str, FinancialFieldMapping]:
        """損益表欄位對照"""
        return {
            "revenue": FinancialFieldMapping(
                chinese_name="營業收入",
                english_name="Revenue / Sales",
                twse_tpex_field="營業收入",
                yfinance_field="totalRevenue",
                synonyms=["sales", "總收入", "銷售收入", "revenue", "營收", "收入"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "cost_of_revenue": FinancialFieldMapping(
                chinese_name="營業成本",
                english_name="Cost of Goods Sold (COGS)",
                twse_tpex_field="營業成本",
                yfinance_field="costOfRevenue",
                synonyms=["COGS", "銷貨成本", "cost_of_sales", "營運成本"],
                validation_rules=["must_be_positive", "currency_format", "less_than_revenue"]
            ),
            "gross_profit": FinancialFieldMapping(
                chinese_name="毛利",
                english_name="Gross Profit",
                twse_tpex_field="營業毛利",
                yfinance_field="grossProfit",
                synonyms=["毛利潤", "總毛利", "gross_margin", "營業毛利"],
                validation_rules=["currency_format", "equals_revenue_minus_cogs"]
            ),
            "operating_expenses": FinancialFieldMapping(
                chinese_name="營業費用",
                english_name="Operating Expenses",
                twse_tpex_field="營業費用",
                yfinance_field="operatingExpenses",
                synonyms=["營運費用", "經營費用", "opex", "運營開支"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "operating_income": FinancialFieldMapping(
                chinese_name="營業利益",
                english_name="Operating Income",
                twse_tpex_field="營業利益",
                yfinance_field="operatingIncome",
                synonyms=["營業利潤", "營運利益", "EBIT", "經營利益"],
                validation_rules=["currency_format"]
            ),
            "other_income_expense": FinancialFieldMapping(
                chinese_name="營業外收支",
                english_name="Non-operating Income/Expense",
                twse_tpex_field="營業外收入及支出",
                yfinance_field="otherIncomeExpense",
                synonyms=["營業外損益", "非營業收支", "其他收支", "業外收支"],
                validation_rules=["currency_format"]
            ),
            "income_before_tax": FinancialFieldMapping(
                chinese_name="稅前淨利",
                english_name="Income Before Tax",
                twse_tpex_field="稅前淨利",
                yfinance_field="incomeBeforeTax",
                synonyms=["稅前利潤", "稅前收益", "pretax_income", "EBT"],
                validation_rules=["currency_format"]
            ),
            "income_tax_expense": FinancialFieldMapping(
                chinese_name="所得稅費用",
                english_name="Income Tax Expense",
                twse_tpex_field="所得稅費用",
                yfinance_field="incomeTaxExpense",
                synonyms=["稅務費用", "所得稅", "稅費", "tax_expense"],
                validation_rules=["currency_format"]
            ),
            "net_income": FinancialFieldMapping(
                chinese_name="本期淨利",
                english_name="Net Income",
                twse_tpex_field="本期淨利",
                yfinance_field="netIncome",
                synonyms=["淨利潤", "淨收益", "本期淨收益", "net_profit", "純益"],
                validation_rules=["currency_format"]
            ),
            "basic_eps": FinancialFieldMapping(
                chinese_name="每股盈餘（基本）",
                english_name="Basic Earnings Per Share (Basic EPS)",
                twse_tpex_field="基本每股盈餘",
                yfinance_field="basicEPS",
                synonyms=["基本EPS", "每股基本盈餘", "基本每股收益"],
                validation_rules=["decimal_format", "reasonable_eps_range"]
            ),
            "diluted_eps": FinancialFieldMapping(
                chinese_name="每股盈餘（稀釋）",
                english_name="Diluted Earnings Per Share (Diluted EPS)",
                twse_tpex_field="稀釋每股盈餘",
                yfinance_field="dilutedEPS",
                synonyms=["稀釋EPS", "每股稀釋盈餘", "完全稀釋每股收益"],
                validation_rules=["decimal_format", "reasonable_eps_range", "less_than_or_equal_basic_eps"]
            )
        }
    
    def _init_balance_sheet(self) -> Dict[str, FinancialFieldMapping]:
        """資產負債表欄位對照"""
        return {
            "current_assets": FinancialFieldMapping(
                chinese_name="流動資產",
                english_name="Current Assets",
                twse_tpex_field="流動資產",
                yfinance_field="currentAssets",
                synonyms=["短期資產", "流動性資產"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "non_current_assets": FinancialFieldMapping(
                chinese_name="非流動資產",
                english_name="Non-current Assets",
                twse_tpex_field="非流動資產",
                yfinance_field="nonCurrentAssets",
                synonyms=["長期資產", "固定資產", "非流動性資產"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "total_assets": FinancialFieldMapping(
                chinese_name="資產總額",
                english_name="Total Assets",
                twse_tpex_field="資產總額",
                yfinance_field="totalAssets",
                synonyms=["總資產", "資產合計"],
                validation_rules=["must_be_positive", "currency_format", "equals_current_plus_noncurrent_assets"]
            ),
            "current_liabilities": FinancialFieldMapping(
                chinese_name="流動負債",
                english_name="Current Liabilities",
                twse_tpex_field="流動負債",
                yfinance_field="currentLiabilities",
                synonyms=["短期負債", "流動性負債"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "non_current_liabilities": FinancialFieldMapping(
                chinese_name="非流動負債",
                english_name="Non-current Liabilities",
                twse_tpex_field="非流動負債",
                yfinance_field="nonCurrentLiabilities",
                synonyms=["長期負債", "非流動性負債"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "total_liabilities": FinancialFieldMapping(
                chinese_name="負債總額",
                english_name="Total Liabilities",
                twse_tpex_field="負債總額",
                yfinance_field="totalLiabilities",
                synonyms=["總負債", "負債合計"],
                validation_rules=["must_be_positive", "currency_format", "equals_current_plus_noncurrent_liabilities"]
            ),
            "total_equity": FinancialFieldMapping(
                chinese_name="股東權益",
                english_name="Shareholders' Equity",
                twse_tpex_field="權益總額",
                yfinance_field="totalEquity",
                synonyms=["股東權益", "權益合計", "淨值", "stockholders_equity"],
                validation_rules=["currency_format", "equals_assets_minus_liabilities"]
            )
        }
    
    def _init_cashflow(self) -> Dict[str, FinancialFieldMapping]:
        """現金流量表欄位對照"""
        return {
            "operating_cashflow": FinancialFieldMapping(
                chinese_name="營業活動現金流量",
                english_name="Operating Cash Flow",
                twse_tpex_field="營業活動現金流量",
                yfinance_field="operatingCashflow",
                synonyms=["營運現金流", "經營現金流", "OCF"],
                validation_rules=["currency_format"]
            ),
            "investing_cashflow": FinancialFieldMapping(
                chinese_name="投資活動現金流量",
                english_name="Investing Cash Flow",
                twse_tpex_field="投資活動現金流量",
                yfinance_field="investingCashflow",
                synonyms=["投資現金流", "ICF"],
                validation_rules=["currency_format"]
            ),
            "financing_cashflow": FinancialFieldMapping(
                chinese_name="籌資活動現金流量",
                english_name="Financing Cash Flow",
                twse_tpex_field="籌資活動現金流量",
                yfinance_field="financingCashflow",
                synonyms=["融資現金流", "籌資現金流", "FCF"],
                validation_rules=["currency_format"]
            ),
            "cash_and_equivalents": FinancialFieldMapping(
                chinese_name="本期現金及約當現金",
                english_name="Cash and Cash Equivalents",
                twse_tpex_field="現金及約當現金期末餘額",
                yfinance_field="cashAndCashEquivalents",
                synonyms=["現金餘額", "現金及現金等價物", "期末現金"],
                validation_rules=["must_be_positive", "currency_format"]
            ),
            "free_cashflow": FinancialFieldMapping(
                chinese_name="自由現金流",
                english_name="Free Cash Flow (FCF)",
                twse_tpex_field="自由現金流",
                yfinance_field="freeCashflow",
                synonyms=["自由現金流量", "FCF"],
                validation_rules=["currency_format", "calculated_from_operating_minus_capex"]
            )
        }
    
    def _init_ratios(self) -> Dict[str, FinancialFieldMapping]:
        """財務比率對照"""
        return {
            "return_on_assets": FinancialFieldMapping(
                chinese_name="ROA",
                english_name="Return on Assets (ROA)",
                twse_tpex_field="資產報酬率",
                yfinance_field="returnOnAssets",
                synonyms=["資產收益率", "總資產報酬率", "ROA"],
                validation_rules=["percentage_format", "reasonable_roa_range"]
            ),
            "return_on_equity": FinancialFieldMapping(
                chinese_name="ROE",
                english_name="Return on Equity (ROE)",
                twse_tpex_field="股東權益報酬率",
                yfinance_field="returnOnEquity",
                synonyms=["股東權益收益率", "淨值報酬率", "ROE"],
                validation_rules=["percentage_format", "reasonable_roe_range"]
            ),
            "current_ratio": FinancialFieldMapping(
                chinese_name="流動比率",
                english_name="Current Ratio",
                twse_tpex_field="流動比率",
                yfinance_field="currentRatio",
                synonyms=["流動性比率"],
                validation_rules=["ratio_format", "reasonable_current_ratio_range"]
            ),
            "debt_ratio": FinancialFieldMapping(
                chinese_name="負債比率",
                english_name="Debt Ratio",
                twse_tpex_field="負債比率",
                yfinance_field="debtRatio",
                synonyms=["負債率", "債務比率"],
                validation_rules=["percentage_format", "reasonable_debt_ratio_range"]
            ),
            "ebitda": FinancialFieldMapping(
                chinese_name="EBITDA",
                english_name="EBITDA",
                twse_tpex_field="EBITDA",
                yfinance_field="ebitda",
                synonyms=["息稅折舊攤銷前利潤"],
                validation_rules=["currency_format"]
            )
        }
    
    def _build_lookup_indices(self):
        """建立反向查找索引"""
        self.field_lookup = {}
        self.synonym_lookup = {}
        
        all_fields = {
            **self.income_statement_fields,
            **self.balance_sheet_fields,
            **self.cashflow_fields,
            **self.ratio_fields
        }
        
        for field_key, field_mapping in all_fields.items():
            # 主要欄位名稱索引
            self.field_lookup[field_mapping.chinese_name.lower()] = field_key
            self.field_lookup[field_mapping.english_name.lower()] = field_key
            self.field_lookup[field_mapping.twse_tpex_field.lower()] = field_key
            self.field_lookup[field_mapping.yfinance_field.lower()] = field_key
            
            # 同義字索引
            for synonym in field_mapping.synonyms:
                self.synonym_lookup[synonym.lower()] = field_key

# =====================================
# 🔍 同義字與關鍵字規則
# =====================================

class KeywordRules:
    """關鍵字規則管理器"""
    
    # EPS 相關模式
    EPS_PATTERNS = {
        "basic_eps": [
            r"(Adj\.?\s*EPS|每股盈餘|Basic\s+EPS|EPS\s*\(Basic\)|基本每股盈餘|EPSb|BasicEPS|基本EPS|basicEarningsPerShare|basicEPS)",
            r"基本每股盈餘",
            r"每股盈餘.*基本"
        ],
        "diluted_eps": [
            r"(Diluted\s+EPS|EPS.*diluted|稀釋每股盈餘|FD\s*EPS|DilutedEPS|稀釋EPS|dilutedEarningsPerShare|dilutedEPS)",
            r"稀釋每股盈餘",
            r"每股盈餘.*稀釋"
        ]
    }
    
    # 股票評等關鍵字
    RATING_KEYWORDS = {
        "strong_buy": ["強力買進", "Strong Buy", "積極買進", "Outperform"],
        "buy": ["買進", "買入", "增持", "推薦", "加碼", "Buy", "Accumulate", "Add", "Long"],
        "hold": ["持有", "中立", "觀望", "平衡", "Hold", "Neutral", "Market Perform"],
        "sell": ["賣出", "減持", "賣超", "Sell", "Underperform", "Reduce"],
        "strong_sell": ["強力賣出", "Strong Sell", "避免", "Avoid"],
        "not_rated": ["未評等", "未評級", "無評等", "暫無評等", "N/A", "Not Rated", "No Rating", "NR"]
    }
    
    # 時間期間關鍵字
    TIME_PERIOD_KEYWORDS = {
        "annual": ["年度", "年報", "全年", "Annual", "Yearly", "FY"],
        "quarterly": ["季度", "季報", "Q1", "Q2", "Q3", "Q4", "Quarterly"],
        "monthly": ["月度", "月報", "Monthly"],
        "ttm": ["過去十二個月", "TTM", "Trailing Twelve Months", "最近十二個月"]
    }

# =====================================
# ✅ 驗證規則引擎
# =====================================

class ValidationEngine:
    """財務數據驗證引擎"""
    
    @staticmethod
    def validate_positive_number(value: Union[str, float]) -> bool:
        """驗證正數"""
        try:
            num = float(str(value).replace(',', '').replace('$', '').replace('%', ''))
            return num > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_currency_format(value: str) -> bool:
        """驗證貨幣格式"""
        pattern = r'^[\$\¥\€\£\₩\₪]?[\d,]+\.?\d*[KMBTkmbt]?$'
        return bool(re.match(pattern, value.strip()))
    
    @staticmethod
    def validate_percentage_format(value: str) -> bool:
        """驗證百分比格式"""
        pattern = r'^\d+\.?\d*\s*%?$'
        return bool(re.match(pattern, value.strip()))
    
    @staticmethod
    def validate_eps_range(eps_value: float) -> bool:
        """驗證EPS合理範圍"""
        return -1000 <= eps_value <= 1000
    
    @staticmethod
    def validate_ratio_format(value: str) -> bool:
        """驗證比率格式"""
        pattern = r'^\d+\.?\d*[xX]?$'
        return bool(re.match(pattern, value.strip()))
    
    @staticmethod
    def cross_validate_financial_data(data: Dict) -> List[str]:
        """交互驗證財務數據一致性"""
        errors = []
        
        # 驗證資產負債表平衡
        if all(k in data for k in ['total_assets', 'total_liabilities', 'total_equity']):
            assets = float(data['total_assets'])
            liabilities = float(data['total_liabilities'])
            equity = float(data['total_equity'])
            
            if abs(assets - (liabilities + equity)) > 1000:  # 允許1000的誤差
                errors.append("資產負債表不平衡：資產總額 ≠ 負債總額 + 權益總額")
        
        # 驗證毛利計算
        if all(k in data for k in ['revenue', 'cost_of_revenue', 'gross_profit']):
            revenue = float(data['revenue'])
            cogs = float(data['cost_of_revenue'])
            gross_profit = float(data['gross_profit'])
            
            if abs(gross_profit - (revenue - cogs)) > 1000:
                errors.append("毛利計算錯誤：毛利 ≠ 營業收入 - 營業成本")
        
        # 驗證稀釋EPS <= 基本EPS
        if all(k in data for k in ['basic_eps', 'diluted_eps']):
            basic_eps = float(data['basic_eps'])
            diluted_eps = float(data['diluted_eps'])
            
            if diluted_eps > basic_eps:
                errors.append("EPS邏輯錯誤：稀釋每股盈餘不應大於基本每股盈餘")
        
        return errors

# =====================================
# 🧪 測試框架
# =====================================

class FinancialDataTester:
    """財務數據測試框架"""
    
    def __init__(self):
        self.mapper = FinancialFieldsMapper()
        self.validator = ValidationEngine()
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> Dict:
        """載入測試案例"""
        return {
            "positive_cases": {
                "revenue": ["營業收入", "Revenue", "Sales", "總收入", "營收"],
                "basic_eps": ["基本每股盈餘", "Basic EPS", "每股盈餘(基本)", "basicEPS"],
                "current_ratio": ["流動比率", "Current Ratio", "1.5x", "150%"]
            },
            "negative_cases": {
                "invalid_currency": ["abc", "N/A", "--", ""],
                "invalid_percentage": ["abc%", "-%", "infinite"],
                "invalid_ratio": ["x", "ratio", "abc:def"]
            },
            "edge_cases": {
                "zero_values": ["0", "0.0", "0%", "0x"],
                "negative_values": ["-100", "-5.5%", "-1.2x"],
                "large_values": ["999999999", "1000000%", "9999x"]
            }
        }
    
    def run_field_mapping_tests(self) -> Dict[str, bool]:
        """運行欄位映射測試"""
        results = {}
        
        # 測試所有欄位是否有完整映射
        for category in ['income_statement_fields', 'balance_sheet_fields', 'cashflow_fields', 'ratio_fields']:
            fields = getattr(self.mapper, category)
            for field_key, mapping in fields.items():
                test_name = f"{category}_{field_key}_mapping"
                results[test_name] = all([
                    mapping.chinese_name,
                    mapping.english_name,
                    mapping.twse_tpex_field,
                    mapping.yfinance_field
                ])
        
        return results
    
    def run_validation_tests(self) -> Dict[str, bool]:
        """運行驗證規則測試"""
        results = {}
        
        # 測試正數驗證
        for value in ["100", "1,234.56", "$1,000"]:
            results[f"positive_validation_{value}"] = self.validator.validate_positive_number(value)
        
        # 測試貨幣格式驗證
        for value in ["$1,234.56", "¥100,000", "1234.56"]:
            results[f"currency_validation_{value}"] = self.validator.validate_currency_format(value)
        
        # 測試百分比格式驗證
        for value in ["15.5%", "100%", "0.1"]:
            results[f"percentage_validation_{value}"] = self.validator.validate_percentage_format(value)
        
        return results
    
    def run_cross_validation_tests(self) -> Dict[str, List[str]]:
        """運行交互驗證測試"""
        test_data = {
            "balanced_sheet": {
                "total_assets": "1000000",
                "total_liabilities": "600000",
                "total_equity": "400000"
            },
            "unbalanced_sheet": {
                "total_assets": "1000000",
                "total_liabilities": "600000",
                "total_equity": "500000"  # 不平衡
            },
            "gross_profit_correct": {
                "revenue": "1000000",
                "cost_of_revenue": "600000",
                "gross_profit": "400000"
            },
            "gross_profit_incorrect": {
                "revenue": "1000000",
                "cost_of_revenue": "600000",
                "gross_profit": "500000"  # 錯誤計算
            }
        }
        
        results = {}
        for test_name, data in test_data.items():
            errors = self.validator.cross_validate_financial_data(data)
            results[test_name] = errors
        
        return results

# =====================================
# 🎯 主要介面類別
# =====================================

class FinancialDataStandardizer:
    """財務數據標準化主介面"""
    
    def __init__(self):
        self.patterns = RegexPatterns()
        self.mapper = FinancialFieldsMapper()
        self.validator = ValidationEngine()
        self.tester = FinancialDataTester()
        self.keywords = KeywordRules()
    
    def standardize_field_name(self, field_name: str) -> Optional[str]:
        """標準化欄位名稱"""
        field_name_lower = field_name.lower().strip()
        
        # 先查找主要欄位
        if field_name_lower in self.mapper.field_lookup:
            return self.mapper.field_lookup[field_name_lower]
        
        # 再查找同義字
        if field_name_lower in self.mapper.synonym_lookup:
            return self.mapper.synonym_lookup[field_name_lower]
        
        return None
    
    def validate_ticker_format(self, ticker: str) -> Dict[str, bool]:
        """驗證股票代號格式"""
        return {
            "basic_format": bool(re.match(self.patterns.TW_TICKER_BASIC, ticker)),
            "twse_yfinance": bool(re.match(self.patterns.TW_TICKER_TWSE_YFINANCE, ticker)),
            "tpex_yfinance": bool(re.match(self.patterns.TW_TICKER_TPEX_YFINANCE, ticker)),
            "bloomberg": bool(re.match(self.patterns.TW_TICKER_BLOOMBERG, ticker))
        }
    
    def extract_dates(self, text: str) -> List[str]:
        """提取文本中的日期"""
        date_patterns = [
            self.patterns.DATE_NUMERIC,
            self.patterns.DATE_EN_SHORT_MDY,
            self.patterns.DATE_EN_SHORT_DMY,
            self.patterns.DATE_ROC_NUMERIC,
            self.patterns.DATE_ROC_CHINESE
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return dates
    
    def run_comprehensive_tests(self) -> Dict:
        """運行完整測試套件"""
        return {
            "field_mapping_tests": self.tester.run_field_mapping_tests(),
            "validation_tests": self.tester.run_validation_tests(),
            "cross_validation_tests": self.tester.run_cross_validation_tests(),
            "test_summary": {
                "total_patterns": len([attr for attr in dir(self.patterns) if not attr.startswith('_')]),
                "total_fields": sum([
                    len(self.mapper.income_statement_fields),
                    len(self.mapper.balance_sheet_fields),
                    len(self.mapper.cashflow_fields),
                    len(self.mapper.ratio_fields)
                ]),
                "total_validation_rules": 15  # 目前實作的驗證規則數量
            }
        }

# =====================================
# 📋 使用範例 - 整合版
# =====================================

if __name__ == "__main__":
    # 初始化標準化器
    standardizer = FinancialDataStandardizer()
    
    print("="*60)
    print("🏦 財務數據標準化系統 - 整合版")
    print("="*60)
    
    # 測試欄位標準化（包含JSON/CSV同義字）
    test_fields = [
        "營業收入", "Revenue", "Net Revenue", "consolidated sales",  # 來自JSON
        "basicEPS", "每股盈餘", "ROE", "股東權益報酬率",
        "P/E", "本益比", "EBITDA", "資本支出"
    ]
    print("\n🔍 欄位標準化測試（包含外部同義字）")
    print("-" * 50)
    for field in test_fields:
        standardized = standardizer.standardize_field_name(field)
        field_info = standardizer.get_field_info(field) if standardized else None
        print(f"📊 {field:<20} -> {standardized}")
        if field_info:
            print(f"   中文: {field_info['chinese_name']}")
            print(f"   YFinance: {field_info['yfinance_field']}")
    
    # 測試動態添加同義字
    print(f"\n➕ 動態同義字添加測試")
    print("-" * 50)
    custom_alias = "公司營收"
    add_result = standardizer.add_custom_alias("revenue", custom_alias)
    print(f"添加 '{custom_alias}' 到 revenue: {add_result}")
    
    # 驗證新同義字
    new_standardized = standardizer.standardize_field_name(custom_alias)
    print(f"驗證新同義字 '{custom_alias}': {new_standardized}")
    
    # 測試模糊搜尋
    print(f"\n🔎 模糊搜尋測試")
    print("-" * 50)
    search_results = standardizer.search_similar_fields("營收", threshold=0.3)
    for result in search_results[:5]:  # 顯示前5個結果
        print(f"相似度 {result['similarity']:.2f}: {result['matched_alias']} -> {result['field_key']}")
    
    # 測試批量標準化
    print(f"\n📦 批量標準化測試")
    print("-" * 50)
    batch_fields = ["Total Revenue", "Cost of revenue", "Free Cash Flow", "Return on Equity"]
    batch_results = standardizer.batch_standardize(batch_fields)
    for original, standardized in batch_results.items():
        print(f"{original:<20} -> {standardized}")
    
    # 股票代號驗證
    test_tickers = ["2330", "2330.TW", "6488.TWO", "2330 TT", "0001"]
    print(f"\n📈 股票代號格式驗證")
    print("-" * 50)
    for ticker in test_tickers:
        validation = standardizer.validate_ticker_format(ticker)
        valid_formats = [k for k, v in validation.items() if v]
        print(f"{ticker:<10}: {valid_formats}")
    
    # 日期提取測試
    test_text = "報告期間：2024/12/31，民國113年度財報，截至Dec 31, 2024，January 15, 2025發布"
    print(f"\n📅 日期提取測試")
    print("-" * 50)
    print(f"測試文本: {test_text}")
    dates = standardizer.extract_dates(test_text)
    print(f"提取的日期: {dates}")
    
    # 生成統計資訊
    print(f"\n📊 系統統計資訊")
    print("-" * 50)
    stats = standardizer.generate_alias_statistics()
    print(f"總欄位數: {stats['total_fields']}")
    print(f"總同義字數: {stats['total_aliases']}")
    print(f"平均每欄位同義字數: {stats['avg_aliases_per_field']}")
    print(f"唯一同義字數: {stats['unique_alias_count']}")
    
    print(f"\n🏆 同義字最多的欄位 (Top 3):")
    for field_key, count in stats['fields_with_most_aliases'][:3]:
        field_info = standardizer.get_field_info(field_key)
        if field_info:
            print(f"  {field_info['chinese_name']}: {count} 個同義字")
    
    print(f"\n📂 各類別統計:")
    for category, info in stats['category_breakdown'].items():
        print(f"  {category}: {info['field_count']} 欄位, {info['alias_count']} 同義字")
    
    # 運行完整測試
    print(f"\n🧪 完整測試執行")
    print("-" * 50)
    test_results = standardizer.run_comprehensive_tests()
    
    # 顯示測試結果摘要
    field_mapping_passed = sum(1 for v in test_results["field_mapping_tests"].values() if v)
    field_mapping_total = len(test_results["field_mapping_tests"])
    
    validation_passed = sum(1 for v in test_results["validation_tests"].values() if v)
    validation_total = len(test_results["validation_tests"])
    
    alias_expansion_passed = sum(1 for v in test_results["alias_expansion_tests"].values() if v)
    alias_expansion_total = len(test_results["alias_expansion_tests"])
    
    print(f"✅ 欄位映射測試: {field_mapping_passed}/{field_mapping_total} 通過")
    print(f"✅ 驗證規則測試: {validation_passed}/{validation_total} 通過")
    print(f"✅ 同義字擴展測試: {alias_expansion_passed}/{alias_expansion_total} 通過")
    
    # 顯示系統指標
    metrics = test_results["statistics"]["system_metrics"]
    print(f"\n📏 系統指標:")
    print(f"  正則表達式模式: {metrics['total_patterns']}")
    print(f"  總欄位數: {metrics['total_fields']}")
    print(f"  驗證規則數: {metrics['total_validation_rules']}")
    print(f"  JSON整合: {'✅' if metrics['json_integration'] else '❌'}")
    print(f"  CSV整合: {'✅' if metrics['csv_integration'] else '❌'}")
    
    print(f"\n🎯 系統特色:")
    print("  ✅ 可增不可減的同義字管理")
    print("  ✅ 多來源資料整合 (JSON + CSV)")
    print("  ✅ 動態同義字添加")
    print("  ✅ 模糊搜尋功能")
    print("  ✅ 交互驗證機制")
    print("  ✅ 完整的測試框架")
    
    print("="*60)
    print("🚀 財務數據標準化系統整合完成！")
    print("="*60)
