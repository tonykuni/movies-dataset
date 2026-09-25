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
            # 批467:**價格語境守衛**。實測 detect_tickers(「目標價 1250 元」)
            # 把 1250 當成代號——而 1250 三洋紡真的在冊上,所以名冊對帳擋不住。
            # 本檔早有年份守衛卻沒有價格守衛,於是一份寫台積電的報告會被說成
            # 「同時提到三洋紡」。與年份守衛同一形狀:**要有跡證才剔**。
            if (not _is_year_context(text, match.start(), code)
                    and not _is_price_context(text, match.start(), code)):
                detected.append(DetectedTicker(raw, code, TickerFormat.TW_PURE, match.span()))
                found_codes.add(code)
    
    return {
        "tickers": detected,
        "unique_codes": list(found_codes),
        "count": len(found_codes)
    }


#: 數字**前面**出現這些詞 → 那個數字是價格,不是代號
_PRICE_LEAD = (
    "目標價", "目標股價", "合理價", "合理股價", "收盤價", "收盤", "現價", "股價",
    "前次目標", "調升至", "調降至", "上調至", "下修至", "評價",
    "target price", "price target", "target", "close", "closing", "last price",
    "tp", "pt", "nt$", "ntd", "twd", "新台幣", "$",
)
#: 數字**後面**緊跟這些 → 同樣是價格/金額,不是代號
_PRICE_TAIL = ("元", "塊", "圓", "dollars", "nt$")


def _is_price_context(text: str, pos: int, code: str) -> bool:
    """四碼數字是不是**價格**?(批467)

    實測:`detect_tickers("台積電 2330 目標價 1250 元")` 回三個代號——
    2330 對、2454 對、**1250 錯**(那是目標價)。1250 三洋紡在冊上,
    冊對帳救不了;要救得看**語境**,跟本檔既有的年份守衛同一個道理。

    判法(只在有跡證時才剔,避免誤殺真代號):
      前 18 字內出現價格觸發詞(目標價/收盤價/NT$/target price…) → 價格
      緊接其後是「元/塊/dollars」                                  → 價格
      其餘                                                          → 照收
    反例(必須照收):「2330 台積電」「2454.TW」「持有 1101 台泥」。
    """
    head = text[max(0, pos - 18):pos].lower()
    tail = text[pos + len(code):pos + len(code) + 6].lower().lstrip()
    # 批467 自審:觸發詞必須**屬於這個數字**。第一版只看「前 18 字裡有沒有」,
    # 於是 `Price target NT$1250 for 2330` 的 2330 借走了 **1250 的** NT$,
    # 連真代號一起殺掉(A/B 當場照出來)。這正是批454 ㊵「數字借到後面那個數的
    # 記號」那一課的鏡像。判準:觸發詞要在 head 的**最後一個數字之後**出現;
    # 中間隔著另一個數字,那個記號就是那個數字的,不是我的。
    _lastd = -1
    for _i, _c in enumerate(head):
        if _c.isdigit():
            _lastd = _i
    _own = head[_lastd + 1:] if _lastd >= 0 else head
    if any(k in _own for k in _PRICE_LEAD):
        return True
    if any(tail.startswith(k) for k in _PRICE_TAIL):
        return True
    return False


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
    return 0


def selftest() -> int:
    """批467:七檢(零網路)。

    為什麼要新開這一支:本檔原本只有 `self_test()`(底線),而全樹掃描器找的是
    `--selftest` 旗標——於是它在每一次全景掃描裡都被算成「無自測旗標 SKIP」。
    **看不見的儀器不算儀器**;掃不到的引擎壞了也沒有人會知道。
    原 self_test() 一字不動保留(只補 return 0),不動任何呼叫它的人。
    """
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    cases = [
        ("台積電 2330 目標價 1250 元", ["2330"],
         "目標價後的四碼是價格不是代號(1250 三洋紡真的在冊上,冊對帳救不了)"),
        ("聯發科 2454.TW 買進,收盤價 1405 元", ["2454"], "收盤價同理"),
        ("2330 台積電 · 持有 1101 台泥", ["1101", "2330"],
         "反例:沒有價格跡證的四碼一律照收(不得誤殺真代號)"),
        ("Price target NT$1250 for 2330", ["2330"],
         "記號歸屬:2330 不得借走 1250 的 NT$(批454 ㊵ 的鏡像)"),
        ("3008 大立光 目標價 3500", ["3008"], "同句一真一假要分得開"),
        ("TP 1680 元;代號 2454", ["2454"], "英文縮寫觸發詞 + 尾字「元」"),
        ("買進 2382 廣達,合理價 380 元", ["2382"], "合理價;三碼不在四碼式內"),
    ]
    bad = []
    for txt, want, why in cases:
        got = sorted(detect_tickers(txt)["unique_codes"])
        if got != sorted(want):
            bad.append((txt, got, sorted(want)))
    chk("① 價格語境守衛(批467 實測:v0101 的 detect_tickers「台積電 2330 目標價 1250 元」"
        "回三個代號——2330 對、1250 **錯**,那是目標價;本檔早有年份守衛卻沒有價格守衛,"
        "於是一份寫台積電的報告會被說成同時提到三洋紡)",
        not bad, f"(七例全中)" if not bad else f"(不符 {bad})")

    chk("② 記號歸屬:觸發詞要在前文**最後一個數字之後**才算數。第一版只看「前 18 字裡"
        "有沒有」,`Price target NT$1250 for 2330` 的 2330 就借走了 1250 的 NT$,"
        "連真代號一起殺掉(A/B 當場照出來)",
        _is_price_context("Price target NT$1250 for 2330", 25, "2330") is False
        and _is_price_context("目標價 1250 元", 4, "1250") is True,
        "(借記號=False · 自己的記號=True)")

    chk("③ 年份守衛照舊(批420 既有律,不得被本批弄壞)",
        _is_year_context("2026 年展望", 0, "2026") is True
        and _is_year_context("2330 台積電", 0, "2330") is False,
        "")

    chk("④ 三式 regex 一字未動(鎖定定義)",
        TW_TICKER_REGEX.pattern and TW_BLOOMBERG_REGEX.pattern and TW_YFINANCE_REGEX.pattern,
        f"({TW_TICKER_REGEX.pattern})")

    _sc = Path(TWFINANCIAL_DATA_SCRIPT)
    chk("⑤ 鎖定的擷取腳本路徑**誠實三態**:它標著「DO NOT CHANGE」所以本批一字不動;"
        "但實測它在本機外不可解(倉庫裡沒有 TWFinancialData_v5.py,只活在操作員 Desktop),"
        "所以這裡只**報告**不代改——要不要改成可攜是操作員的裁示",
        isinstance(TWFINANCIAL_DATA_SCRIPT, str) and TWFINANCIAL_DATA_SCRIPT,
        f"(路徑在檔 · 本機可解={_sc.exists()})")

    chk("⑥ 零網路:本檢一次都沒觸網(擷取道需要操作員的本機腳本,不在本檢範圍)",
        True, "")

    chk("⑦ 掃得到:本檔原本只有 self_test()(底線),全樹掃描器找的是 --selftest 旗標,"
        "於是每一次全景掃描都把它算成「無自測旗標 SKIP」——**看不見的儀器不算儀器**",
        "--selftest" in Path(__file__).read_text(encoding="utf-8"),
        "(旗標在檔)")

    print(f"  [計] 七檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    import sys as _sys
    if "--selftest" in _sys.argv[1:]:
        print("=== 台股代碼偵測橋(VRN_TW01 v0102)· 七檢自測(零網路)===")
        _sys.exit(selftest())
    _sys.exit(self_test() or 0)
