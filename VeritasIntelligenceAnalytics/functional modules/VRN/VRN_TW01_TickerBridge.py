# -*- coding: utf-8 -*-
r"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║  VRN_TW01_TickerBridge.py                                                                             ║
║  台股代碼偵測橋接器 | Module ID: TW01 | Version: 1.0.0                                                ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  功能:                                                                                                ║
║    1. 從 PDF/Word/TXT/Image→TIFF 轉換後的文本中偵測台股代碼                                           ║
║    2. 使用鎖定的三種 Regex (TW_TICKER / TW_BLOOMBERG / TW_YFINANCE)                                   ║
║    3. 偵測到代碼後直接啟動 TWFinancialData_v5.py 擷取數據                                             ║
║    4. 從輸出資料庫讀取數據                                                                            ║
║                                                                                                       ║
║  數據擷取腳本 (鎖定 - 不修改):                                                                        ║
║    C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\TWFinancialData_v5.py                       ║
║                                                                                                       ║
║  PowerShell 7+ Required                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import re
import os
import sys
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import logging

# =============================================================================
# § TW01 CONFIGURATION
# =============================================================================

MODULE_ID = "TW01"
MODULE_NAME = "TickerBridge"
MODULE_VERSION = "1.0.0"

# ═══════════════════════════════════════════════════════════════════════════════
# 數據擷取腳本路徑 (鎖定 - DO NOT CHANGE)
# ═══════════════════════════════════════════════════════════════════════════════
TWFINANCIAL_DATA_SCRIPT = r"C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\TWFinancialData_v5.py"

# 輸出資料庫目錄
TWSTOCK_OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\Desktop\VRN\output"

# =============================================================================
# § CORE TICKER REGEX DEFINITIONS - 鎖定定義 (EXACT NAMES - DO NOT CHANGE)
# =============================================================================

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ 母代號：純四碼數字，首碼非零（例如 2330）                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
TW_TICKER_REGEX = re.compile(r"\b[1-9]\d{3}\b")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Bloomberg 台股代號：四碼 + 空格 + TT（例如 2330 TT）                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
TW_BLOOMBERG_REGEX = re.compile(r"\b[1-9]\d{3} TT\b")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Yahoo Finance 台股代號：四碼 + .TW 或 .TWO（例如 2330.TW, 2330.TWO）       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
TW_YFINANCE_REGEX = re.compile(r"\b[1-9]\d{3}\.(TW|TWO)\b")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ 統一提取四碼的正則                                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
TW_CODE_EXTRACT = re.compile(r"\b([1-9]\d{3})(?:\s+TT|\.TWO?|\b)")


# =============================================================================
# § TICKER DETECTOR - 代碼偵測器
# =============================================================================

class TickerFormat(Enum):
    TW_PURE = "tw_pure"
    TW_BLOOMBERG = "tw_bloomberg"
    TW_YFINANCE = "tw_yfinance"


@dataclass
class DetectedTicker:
    raw_match: str
    code: str
    format_type: TickerFormat
    position: Tuple[int, int]


def detect_tickers(text: str) -> Dict[str, Any]:
    """
    從文本偵測台股代碼
    
    使用鎖定的三種 Regex:
    - TW_TICKER_REGEX
    - TW_BLOOMBERG_REGEX  
    - TW_YFINANCE_REGEX
    """
    detected = []
    found_codes = set()
    
    # 1. yfinance 格式 (2330.TW / 2330.TWO) - 最高優先
    for match in TW_YFINANCE_REGEX.finditer(text):
        raw = match.group(0)
        code = raw.split(".")[0]
        detected.append(DetectedTicker(raw, code, TickerFormat.TW_YFINANCE, match.span()))
        found_codes.add(code)
    
    # 2. Bloomberg 格式 (2330 TT)
    for match in TW_BLOOMBERG_REGEX.finditer(text):
        raw = match.group(0)
        code = raw.replace(" TT", "").strip()
        if code not in found_codes:
            detected.append(DetectedTicker(raw, code, TickerFormat.TW_BLOOMBERG, match.span()))
            found_codes.add(code)
    
    # 3. 純四碼 (2330) - 過濾年份
    for match in TW_TICKER_REGEX.finditer(text):
        raw = match.group(0)
        code = raw
        if code not in found_codes:
            # 排除可能的年份 (19xx, 20xx 且有年份上下文)
            if not _is_year_context(text, match.start(), code):
                detected.append(DetectedTicker(raw, code, TickerFormat.TW_PURE, match.span()))
                found_codes.add(code)
    
    return {
        "tickers": detected,
        "unique_codes": list(found_codes),
        "count": len(found_codes)
    }


def _is_year_context(text: str, pos: int, code: str) -> bool:
    """檢查是否為年份上下文"""
    if code.startswith("19") or code.startswith("20"):
        ctx = text[max(0, pos-15):min(len(text), pos+len(code)+15)].lower()
        if any(kw in ctx for kw in ["年", "year", "fy", "quarter", "q1", "q2", "q3", "q4"]):
            return True
    return False


# =============================================================================
# § DATA BRIDGE - 數據橋接
# =============================================================================

def trigger_data_fetch(codes: List[str]) -> Dict[str, Any]:
    """
    直接啟動 TWFinancialData_v5.py 擷取數據
    
    Args:
        codes: 偵測到的代碼清單
        
    Returns:
        執行結果
    """
    script_path = Path(TWFINANCIAL_DATA_SCRIPT)
    
    if not script_path.exists():
        return {"success": False, "error": f"Script not found: {script_path}"}
    
    try:
        # 直接啟動腳本
        cmd = [sys.executable, str(script_path)]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(script_path.parent)
        )
        
        return {
            "success": result.returncode == 0,
            "codes": codes,
            "returncode": result.returncode,
            "output_dir": TWSTOCK_OUTPUT_DIR
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "codes": codes}


def read_output_data() -> Dict[str, Any]:
    """從輸出資料庫讀取數據"""
    output_dir = Path(TWSTOCK_OUTPUT_DIR)
    data = {}
    
    if not output_dir.exists():
        return {"error": f"Output dir not found: {output_dir}"}
    
    # 讀取所有輸出檔案
    for ext in ["*.csv", "*.json", "*.parquet"]:
        for f in output_dir.glob(ext):
            data[f.stem] = str(f)
    
    return data


# =============================================================================
# § MAIN WORKFLOW
# =============================================================================

def process_document_text(text: str, auto_fetch: bool = True) -> Dict[str, Any]:
    """
    主流程：偵測代碼 → 觸發數據擷取 → 讀取輸出
    
    Args:
        text: 從 PDF/Word/TXT/Image 轉換的文本
        auto_fetch: 自動觸發數據擷取
    """
    # Step 1: 偵測代碼
    detection = detect_tickers(text)
    
    result = {
        "module_id": MODULE_ID,
        "detection": detection,
        "data_fetch": None
    }
    
    # Step 2: 觸發數據擷取
    if auto_fetch and detection["unique_codes"]:
        result["data_fetch"] = trigger_data_fetch(detection["unique_codes"])
    
    return result


# =============================================================================
# § SELF TEST
# =============================================================================

def self_test():
    print("=" * 70)
    print(f"VRN {MODULE_ID} {MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 70)
    
    # 顯示鎖定的 Regex
    print("\n【Locked Regex Definitions】")
    print(f"  TW_TICKER_REGEX    = {TW_TICKER_REGEX.pattern}")
    print(f"  TW_BLOOMBERG_REGEX = {TW_BLOOMBERG_REGEX.pattern}")
    print(f"  TW_YFINANCE_REGEX  = {TW_YFINANCE_REGEX.pattern}")
    
    print(f"\n【Data Script (Locked)】")
    print(f"  {TWFINANCIAL_DATA_SCRIPT}")
    
    # 測試偵測
    print("\n【Detection Test】")
    test_text = "台積電 2330.TW 目標價上調，2317 TT 表現亮眼，3324 持續成長"
    result = detect_tickers(test_text)
    print(f"  Codes: {result['unique_codes']}")
    
    # 檢查腳本
    print("\n【Script Check】")
    script_exists = Path(TWFINANCIAL_DATA_SCRIPT).exists()
    print(f"  Exists: {script_exists}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    self_test()
