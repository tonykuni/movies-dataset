# -*- coding: utf-8 -*-
r"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║  VRN_TW02_ReportParser.py                                                                             ║
║  投資報告解析器 | Module ID: TW02 | Version: 1.0.0                                                    ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  功能:                                                                                                ║
║    1. Filename 解析 (中英文/標點/空格切分)                                                            ║
║    2. 第一頁解析 (Header/Info Area/Tables)                                                            ║
║    3. 財報頁解析 (Financial Statement Tables)                                                         ║
║    4. 三源交叉核對 (Filename ↔ 第一頁 ↔ 財報頁)                                                       ║
║    5. 偵測到代碼後調用 TWFinancialData_v5.py                                                          ║
║                                                                                                       ║
║  Ticker 規則:                                                                                         ║
║    - 四碼數字，首碼非零                                                                               ║
║    - 避開 2000~2030 區間 (與年份混淆)                                                                 ║
║    - 三種格式交叉核對：TW_TICKER / TW_BLOOMBERG / TW_YFINANCE                                         ║
║                                                                                                       ║
║  數據擷取腳本:                                                                                        ║
║    C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\TWFinancialData_v5.py                       ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
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
import os
import sys
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum
import logging

# =============================================================================
# § TW02 CONFIGURATION
# =============================================================================

MODULE_ID = "TW02"
MODULE_NAME = "ReportParser"
MODULE_VERSION = "1.0.0"

# 數據擷取腳本 (鎖定)
TWFINANCIAL_DATA_SCRIPT = r"C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\TWFinancialData_v5.py"
TWSTOCK_OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\Desktop\VRN\output"

# =============================================================================
# § CORE TICKER REGEX - 鎖定定義 (DO NOT CHANGE)
# =============================================================================

# 母代號：純四碼數字，首碼非零
TW_TICKER_REGEX = re.compile(r"\b[1-9]\d{3}\b")

# Bloomberg 台股代號：四碼 + 空格 + TT
TW_BLOOMBERG_REGEX = re.compile(r"\b[1-9]\d{3} TT\b")

# Yahoo Finance 台股代號：四碼 + .TW 或 .TWO
TW_YFINANCE_REGEX = re.compile(r"\b[1-9]\d{3}\.(TW|TWO)\b")

# 統一提取四碼
TW_CODE_EXTRACT = re.compile(r"\b([1-9]\d{3})(?:\s+TT|\.TWO?|\b)")

# =============================================================================
# § TICKER EXCLUSION - 避開年份區間
# =============================================================================

# 避開 2000~2030 (容易與年份混淆)
TICKER_EXCLUSION_RANGE = range(2000, 2031)

def is_valid_ticker(code: str) -> bool:
    """檢查是否為有效的 ticker (排除年份區間)"""
    if not code.isdigit() or len(code) != 4:
        return False
    num = int(code)
    # 首碼非零 且 不在 2000~2030 區間
    return code[0] != '0' and num not in TICKER_EXCLUSION_RANGE


# =============================================================================
# § DATE REGEX PATTERNS - 報告日期
# =============================================================================

class ReportDatePatterns:
    """報告日期格式"""
    
    # 7~8 個數字: 20250125 或 2025125
    DATE_7_8_DIGITS = re.compile(r"\b(20[2-3]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b")
    
    # 6 個數字省去 20: 250125 → 2025/01/25
    DATE_6_DIGITS = re.compile(r"\b([2-3]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b")
    
    # 4 個數字省去年份: 0125 → 當年/01/25
    DATE_4_DIGITS = re.compile(r"\b(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b")
    
    # ISO 格式: 2025-01-25
    DATE_ISO = re.compile(r"\b(20[2-3]\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b")
    
    # 民國格式: 114/01/25
    DATE_ROC = re.compile(r"\b(1[01]\d)[/-](0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])\b")
    
    # 中文格式: 2025年1月25日
    DATE_ZH = re.compile(r"(20[2-3]\d)\s*年\s*(1?[0-9])\s*月\s*([1-3]?[0-9])\s*日")


# =============================================================================
# § BROKER REGEX - 券商識別
# =============================================================================

BROKER_PATTERNS = {
    # 本土券商
    "元大": ["元大", "Yuanta"],
    "凱基": ["凱基", "KGI"],
    "富邦": ["富邦", "Fubon"],
    "永豐金": ["永豐", "SinoPac"],
    "國泰": ["國泰", "Cathay"],
    "台新": ["台新", "Taishin"],
    "中信": ["中信", "CTBC"],
    "統一": ["統一", "President"],
    "兆豐": ["兆豐", "Mega"],
    "群益": ["群益", "Capital"],
    # 外資券商
    "摩根士丹利": ["摩根士丹利", "Morgan Stanley", "MS"],
    "高盛": ["高盛", "Goldman Sachs", "GS"],
    "花旗": ["花旗", "Citi", "Citigroup"],
    "美林": ["美林", "Merrill Lynch", "BAML"],
    "摩根大通": ["摩根大通", "JPMorgan", "JPM"],
    "瑞銀": ["瑞銀", "UBS"],
    "麥格理": ["麥格理", "Macquarie"],
    "野村": ["野村", "Nomura"],
    "大和": ["大和", "Daiwa"],
    "里昂": ["里昂", "CLSA"],
}

# Email 域名對應券商
EMAIL_DOMAIN_TO_BROKER = {
    "yuanta": "元大",
    "kgi": "凱基",
    "fubon": "富邦",
    "sinopac": "永豐金",
    "cathay": "國泰",
    "taishin": "台新",
    "ctbc": "中信",
    "morganstanley": "摩根士丹利",
    "gs": "高盛",
    "citi": "花旗",
    "jpmorgan": "摩根大通",
    "ubs": "瑞銀",
    "nomura": "野村",
    "clsa": "里昂",
}


# =============================================================================
# § ANALYST REGEX - 分析師識別
# =============================================================================

class AnalystPatterns:
    """分析師識別模式"""
    
    # 中文姓名: 2~4 個中文字
    NAME_ZH = re.compile(r"[\u4e00-\u9fff]{2,4}")
    
    # 英文姓名: Given Name + Family Name
    NAME_EN = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
    
    # 電話 (台灣)
    PHONE_TW = re.compile(r"(?:\+886[-\s]?|0)(?:2[-\s]?\d{4}[-\s]?\d{4}|\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})")
    
    # 電子郵箱
    EMAIL = re.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


# =============================================================================
# § RATING SYSTEM - 評等識別
# =============================================================================

RATING_SYNONYMS = {
    "BUY": [
        "買進", "買入", "增持", "強力買進", "推薦", "加碼", "積極買進",
        "Buy", "Strong Buy", "Outperform", "Overweight", "Accumulate", "Add"
    ],
    "HOLD": [
        "持有", "中立", "觀望", "平衡", "續抱",
        "Hold", "Neutral", "Market Perform", "Equal Weight"
    ],
    "SELL": [
        "賣出", "減持", "下調", "減碼", "避險",
        "Sell", "Reduce", "Underperform", "Underweight", "Strong Sell"
    ],
    "NOT_RATED": [
        "未評等", "未評級", "無評等", "暫無評等",
        "N/A", "Not Rated", "NR", "Not Covered"
    ]
}

RATING_PATTERN = re.compile(
    r"\b(" + "|".join([re.escape(s) for syns in RATING_SYNONYMS.values() for s in syns]) + r")\b",
    re.IGNORECASE
)


# =============================================================================
# § TARGET PRICE REGEX - 目標價
# =============================================================================

TARGET_PRICE_SYNONYMS = [
    "目標價", "目標價位", "合理價", "合理價位", "推測合理價",
    "Target Price", "TP", "Price Target", "PT", "Fair Value", "FV"
]

TARGET_PRICE_PATTERN = re.compile(
    r"(?:" + "|".join([re.escape(s) for s in TARGET_PRICE_SYNONYMS]) + r")[\s:：]*"
    r"(?:NT\$|TWD|NTD)?[\s]*([\d,]+(?:\.\d+)?)\s*(?:元|TWD)?",
    re.IGNORECASE
)


# =============================================================================
# § FINANCIAL METRICS - 財務指標 (2023~2027)
# =============================================================================

FINANCIAL_METRIC_SYNONYMS = {
    "Basic_EPS": [
        "基本每股盈餘", "基本EPS", "每股盈餘", "EPS",
        "Basic EPS", "Earnings Per Share"
    ],
    "Diluted_EPS": [
        "稀釋每股盈餘", "稀釋EPS", "完全稀釋EPS",
        "Diluted EPS", "Fully Diluted EPS"
    ],
    "BVPS": [
        "每股淨值", "每股帳面價值", "BVPS",
        "Book Value Per Share"
    ],
    "DPS": [
        "每股股利", "每股現金股利", "DPS",
        "Dividend Per Share", "Cash Dividend"
    ],
    "ROE": [
        "股東權益報酬率", "ROE",
        "Return on Equity"
    ],
    "Weighted_Shares": [
        "加權平均股本", "加權平均流通股數", "平均股本",
        "Weighted Average Shares", "Avg Shares"
    ],
    "Diluted_Shares": [
        "完全稀釋後股本", "稀釋後股本", "稀釋股數",
        "Fully Diluted Shares", "Diluted Shares"
    ],
    "Net_Profit": [
        "稅後淨利", "淨利", "歸屬母公司淨利", "Net Profit",
        "Net Income", "Profit After Tax"
    ],
    "Book_Value": [
        "帳面價值", "淨值", "股東權益",
        "Book Value", "Shareholders Equity", "Total Equity"
    ]
}

# 年度範圍
FISCAL_YEARS = ["2023", "2024", "2025", "2026", "2027"]


# =============================================================================
# § FILENAME PARSER - 檔名解析
# =============================================================================

class FilenameParser:
    """
    檔名解析器
    
    在中英文、標點符號、空格處切成獨立元件:
    - 連續英文
    - 連續中文
    - 連續數字 (四碼為 tw_ticker)
    """
    
    # 分割模式: 中英文邊界、標點、空格
    SPLIT_PATTERN = re.compile(
        r"(?<=[a-zA-Z])(?=[\u4e00-\u9fff])|"  # 英→中
        r"(?<=[\u4e00-\u9fff])(?=[a-zA-Z])|"  # 中→英
        r"(?<=[a-zA-Z])(?=\d)|"               # 英→數
        r"(?<=\d)(?=[a-zA-Z])|"               # 數→英
        r"(?<=[\u4e00-\u9fff])(?=\d)|"        # 中→數
        r"(?<=\d)(?=[\u4e00-\u9fff])|"        # 數→中
        r"[\s_\-\.,:;!?()（）【】「」《》\[\]]+|"  # 標點空格
        r"(?<=[a-z])(?=[A-Z])"                # camelCase
    )
    
    @classmethod
    def parse(cls, filename: str) -> Dict[str, Any]:
        """解析檔名"""
        # 移除副檔名
        name = Path(filename).stem
        
        # 分割成元件
        components = [c.strip() for c in cls.SPLIT_PATTERN.split(name) if c and c.strip()]
        
        result = {
            "original": filename,
            "stem": name,
            "components": components,
            "chinese": [],
            "english": [],
            "numbers": [],
            "potential_tickers": [],
            "potential_dates": []
        }
        
        for comp in components:
            if re.match(r"^[\u4e00-\u9fff]+$", comp):
                result["chinese"].append(comp)
            elif re.match(r"^[a-zA-Z]+$", comp):
                result["english"].append(comp)
            elif re.match(r"^\d+$", comp):
                result["numbers"].append(comp)
                
                # 四碼數字 → 可能是 ticker
                if len(comp) == 4 and is_valid_ticker(comp):
                    result["potential_tickers"].append(comp)
                
                # 6~8 碼數字 → 可能是日期
                if 6 <= len(comp) <= 8:
                    result["potential_dates"].append(comp)
        
        return result


# =============================================================================
# § PAGE PARSER - 頁面解析
# =============================================================================

class PageParser:
    """頁面解析器"""
    
    @staticmethod
    def parse_first_page(text: str) -> Dict[str, Any]:
        """
        解析第一頁
        
        區域:
        - Header (頂部)
        - Info Area (左上/右上)
        - Main Content
        - Tables
        """
        result = {
            "tickers": {"tw_pure": [], "tw_bloomberg": [], "tw_yfinance": []},
            "dates": [],
            "broker": None,
            "analyst": None,
            "rating": None,
            "target_price": None,
            "company_name": None
        }
        
        # 偵測三種 ticker 格式
        for m in TW_YFINANCE_REGEX.finditer(text):
            code = m.group(0).split(".")[0]
            if is_valid_ticker(code):
                result["tickers"]["tw_yfinance"].append(m.group(0))
        
        for m in TW_BLOOMBERG_REGEX.finditer(text):
            code = m.group(0).replace(" TT", "")
            if is_valid_ticker(code):
                result["tickers"]["tw_bloomberg"].append(m.group(0))
        
        for m in TW_TICKER_REGEX.finditer(text):
            code = m.group(0)
            if is_valid_ticker(code):
                # 額外檢查上下文，排除年份
                ctx = text[max(0, m.start()-10):min(len(text), m.end()+10)]
                if not re.search(r"年|year|fy|quarter", ctx, re.IGNORECASE):
                    result["tickers"]["tw_pure"].append(code)
        
        # 偵測日期
        for pattern in [ReportDatePatterns.DATE_ISO, ReportDatePatterns.DATE_ROC, 
                        ReportDatePatterns.DATE_ZH, ReportDatePatterns.DATE_7_8_DIGITS]:
            for m in pattern.finditer(text):
                result["dates"].append(m.group(0))
        
        # 偵測券商 (含 email 域名)
        for broker, aliases in BROKER_PATTERNS.items():
            for alias in aliases:
                if alias.lower() in text.lower():
                    result["broker"] = broker
                    break
            if result["broker"]:
                break
        
        # 從 email 偵測券商
        for m in AnalystPatterns.EMAIL.finditer(text):
            domain = m.group(2).lower().split(".")[0]
            if domain in EMAIL_DOMAIN_TO_BROKER:
                result["broker"] = EMAIL_DOMAIN_TO_BROKER[domain]
        
        # 偵測分析師
        analysts = []
        for m in AnalystPatterns.NAME_ZH.finditer(text[:500]):  # 前 500 字
            name = m.group(0)
            if len(name) >= 2 and name not in [b for b in BROKER_PATTERNS.keys()]:
                analysts.append(name)
        result["analyst"] = analysts[:3] if analysts else None
        
        # 偵測評等
        rating_match = RATING_PATTERN.search(text)
        if rating_match:
            rating_text = rating_match.group(1)
            for category, synonyms in RATING_SYNONYMS.items():
                if rating_text in synonyms:
                    result["rating"] = category
                    break
        
        # 偵測目標價
        tp_match = TARGET_PRICE_PATTERN.search(text)
        if tp_match:
            result["target_price"] = tp_match.group(1).replace(",", "")
        
        return result
    
    @staticmethod
    def parse_financial_page(text: str) -> Dict[str, Any]:
        """解析財報頁"""
        result = {
            "tickers": [],
            "metrics": {}
        }
        
        # 偵測 ticker
        for m in TW_TICKER_REGEX.finditer(text):
            code = m.group(0)
            if is_valid_ticker(code):
                result["tickers"].append(code)
        
        # 偵測財務指標
        for metric, synonyms in FINANCIAL_METRIC_SYNONYMS.items():
            pattern = re.compile(
                r"(?:" + "|".join([re.escape(s) for s in synonyms]) + r")[\s:：]*"
                r"([\d,.-]+)",
                re.IGNORECASE
            )
            matches = pattern.findall(text)
            if matches:
                result["metrics"][metric] = [m.replace(",", "") for m in matches]
        
        return result


# =============================================================================
# § CROSS VALIDATOR - 三源交叉核對
# =============================================================================

class CrossValidator:
    """
    三源交叉核對
    
    Filename ↔ 第一頁 ↔ 財報頁
    """
    
    @staticmethod
    def validate(filename_data: Dict, first_page_data: Dict, financial_page_data: Dict) -> Dict[str, Any]:
        """
        交叉核對三個來源的 ticker
        
        規則:
        1. 三種格式前四碼必須相同
        2. 排除 2000~2030 區間
        3. 多來源出現增加可信度
        """
        # 收集所有來源的代碼
        all_codes = set()
        source_counts = {}
        
        # Filename 來源
        for code in filename_data.get("potential_tickers", []):
            if is_valid_ticker(code):
                all_codes.add(code)
                source_counts[code] = source_counts.get(code, 0) + 1
        
        # 第一頁來源
        fp_tickers = first_page_data.get("tickers", {})
        
        for ticker in fp_tickers.get("tw_yfinance", []):
            code = ticker.split(".")[0]
            if is_valid_ticker(code):
                all_codes.add(code)
                source_counts[code] = source_counts.get(code, 0) + 2  # yfinance 權重較高
        
        for ticker in fp_tickers.get("tw_bloomberg", []):
            code = ticker.replace(" TT", "")
            if is_valid_ticker(code):
                all_codes.add(code)
                source_counts[code] = source_counts.get(code, 0) + 2
        
        for code in fp_tickers.get("tw_pure", []):
            if is_valid_ticker(code):
                all_codes.add(code)
                source_counts[code] = source_counts.get(code, 0) + 1
        
        # 財報頁來源
        for code in financial_page_data.get("tickers", []):
            if is_valid_ticker(code):
                all_codes.add(code)
                source_counts[code] = source_counts.get(code, 0) + 1
        
        # 計算可信度
        validated_tickers = []
        for code in all_codes:
            confidence = min(source_counts.get(code, 0) / 5.0, 1.0)
            validated_tickers.append({
                "code": code,
                "yfinance": f"{code}.TW",  # 預設上市
                "bloomberg": f"{code} TT",
                "confidence": confidence,
                "sources": source_counts.get(code, 0)
            })
        
        # 按可信度排序
        validated_tickers.sort(key=lambda x: x["confidence"], reverse=True)
        
        # 日期交叉核對 (以第一頁為主)
        validated_date = None
        fp_dates = first_page_data.get("dates", [])
        fn_dates = filename_data.get("potential_dates", [])
        
        if fp_dates:
            validated_date = fp_dates[0]  # 第一頁優先
        elif fn_dates:
            validated_date = fn_dates[0]
        
        return {
            "validated_tickers": validated_tickers,
            "primary_ticker": validated_tickers[0] if validated_tickers else None,
            "validated_date": validated_date,
            "broker": first_page_data.get("broker"),
            "analyst": first_page_data.get("analyst"),
            "rating": first_page_data.get("rating"),
            "target_price": first_page_data.get("target_price"),
            "metrics": financial_page_data.get("metrics", {})
        }


# =============================================================================
# § DATA FETCHER - 數據擷取
# =============================================================================

def fetch_financial_data(tickers: List[str]) -> Dict[str, Any]:
    """
    調用 TWFinancialData_v5.py 擷取數據
    
    Args:
        tickers: 代碼清單 (四碼格式)
    """
    script_path = Path(TWFINANCIAL_DATA_SCRIPT)
    
    if not script_path.exists():
        return {"success": False, "error": f"Script not found: {script_path}"}
    
    # 準備 yfinance 格式
    yf_tickers = [f"{t}.TW" for t in tickers]
    
    try:
        # 直接執行腳本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(script_path.parent)
        )
        
        return {
            "success": result.returncode == 0,
            "tickers": tickers,
            "yfinance_tickers": yf_tickers,
            "output_dir": TWSTOCK_OUTPUT_DIR
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# § MAIN PARSER - 主解析器
# =============================================================================

class TW02_ReportParser:
    """
    投資報告解析器
    
    流程:
    1. 解析 Filename
    2. 解析第一頁
    3. 解析財報頁
    4. 三源交叉核對
    5. 調用數據擷取
    """
    
    def __init__(self):
        self.filename_parser = FilenameParser()
        self.page_parser = PageParser()
        self.validator = CrossValidator()
    
    def parse(self, filename: str, first_page_text: str, 
              financial_page_text: str = "", auto_fetch: bool = True) -> Dict[str, Any]:
        """
        完整解析流程
        
        Args:
            filename: 檔案名稱
            first_page_text: 第一頁文本
            financial_page_text: 財報頁文本
            auto_fetch: 自動擷取數據
        """
        # Step 1: 解析 Filename
        filename_data = self.filename_parser.parse(filename)
        
        # Step 2: 解析第一頁
        first_page_data = self.page_parser.parse_first_page(first_page_text)
        
        # Step 3: 解析財報頁
        financial_page_data = self.page_parser.parse_financial_page(financial_page_text)
        
        # Step 4: 交叉核對
        validated = self.validator.validate(filename_data, first_page_data, financial_page_data)
        
        result = {
            "module_id": MODULE_ID,
            "module_version": MODULE_VERSION,
            "filename_analysis": filename_data,
            "first_page_analysis": first_page_data,
            "financial_page_analysis": financial_page_data,
            "validated_result": validated,
            "data_fetch": None
        }
        
        # Step 5: 自動擷取數據
        if auto_fetch and validated["validated_tickers"]:
            codes = [t["code"] for t in validated["validated_tickers"]]
            result["data_fetch"] = fetch_financial_data(codes)
        
        return result


# =============================================================================
# § SELF TEST
# =============================================================================

def self_test():
    print("=" * 70)
    print(f"VRN {MODULE_ID} {MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 70)
    
    # Test 1: Filename 解析
    print("\n【Test 1】Filename Parser")
    test_filename = "元大_台積電_2330_20250125_目標價調升.pdf"
    fn_result = FilenameParser.parse(test_filename)
    print(f"  Components: {fn_result['components']}")
    print(f"  Chinese: {fn_result['chinese']}")
    print(f"  Tickers: {fn_result['potential_tickers']}")
    
    # Test 2: 第一頁解析
    print("\n【Test 2】First Page Parser")
    test_text = """
    元大證券 投資研究報告
    台積電 (2330.TW) / 2330 TT
    評等: 買進  目標價: NT$1,200
    分析師: 王小明  Tel: 02-2777-1234
    Email: analyst@yuanta.com
    2025年1月25日
    """
    fp_result = PageParser.parse_first_page(test_text)
    print(f"  Tickers: {fp_result['tickers']}")
    print(f"  Broker: {fp_result['broker']}")
    print(f"  Rating: {fp_result['rating']}")
    print(f"  Target Price: {fp_result['target_price']}")
    
    # Test 3: Ticker 排除區間
    print("\n【Test 3】Ticker Validation")
    test_codes = ["2330", "2024", "2025", "3324", "1101", "2000"]
    for code in test_codes:
        valid = is_valid_ticker(code)
        status = "✓" if valid else "✗"
        reason = "(in 2000-2030)" if not valid and 2000 <= int(code) <= 2030 else ""
        print(f"  {status} {code} {reason}")
    
    # Test 4: 交叉核對
    print("\n【Test 4】Cross Validation")
    parser = TW02_ReportParser()
    result = parser.parse(
        filename=test_filename,
        first_page_text=test_text,
        financial_page_text="EPS: 45.2  ROE: 28.5%  2330",
        auto_fetch=False
    )
    print(f"  Primary Ticker: {result['validated_result']['primary_ticker']}")
    print(f"  Broker: {result['validated_result']['broker']}")
    
    print("\n" + "=" * 70)
    print("【Locked Script Path】")
    print(f"  {TWFINANCIAL_DATA_SCRIPT}")
    print("=" * 70)


if __name__ == "__main__":
    self_test()
