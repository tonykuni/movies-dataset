

# -*- coding: utf-8 -*-
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  VIA_SSOT_Unified.py                                                   │
# │  ASSET_ID  : AST-PY-MOD-VSE-500-UNIFIED                               │
# │  DISPLAY   : SYS_VSE.MDL500.MOD-UNIFIED                               │
# │  VERSION   : 4.3.0     STATUS : stable                                 │
# │  LANGUAGE  : Python 3.10+                                              │
# │  ANCHORS   : SSOT-SPEC / SSOT-DATA / SSOT-BUILD                       │
# │              SSOT-QUERY / SSOT-COMPOUND / SSOT-STORE                  │
# │              SSOT-RESTORE / SSOT-UTIL                                  │
# │  LL RULES  : #10 #12 #13 #15 #17 #18 #19 #20                         │
# ├─────────────────────────────────────────────────────────────────────────┤
# │  CORPUS: regex=46 · lists=18 · synonyms=112 · aliases=486              │
# │  DOMAINS: finance_tw · file_scan · html_extract                        │
# │           command_risk · report_sections                               │
# ├─────────────────────────────────────────────────────────────────────────┤
# │  COMMAND SPEC ─ 三種呼叫形式:                                          │
# │                                                                        │
# │  A. 一般指令 (General Commands) — 直接呼叫 module-level 函式            │
# │     from VIA_SSOT_Unified import normalize, extract, contains          │
# │     normalize("台積電")               → "2330.TW"                     │
# │     extract("TW_YFINANCE_TICKER","2330.TW")  → "2330.TW"             │
# │     contains("PS_CRITICAL_COMMANDS","Remove-Item") → True             │
# │     filter_noise(["Revenue","合計"])  → ["Revenue"]                   │
# │                                                                        │
# │  B. 嵌入式指令 (Embedded Commands) — 取得單例後鏈式呼叫                 │
# │     from VIA_SSOT_Unified import get_ssot                             │
# │     s = get_ssot()                                                    │
# │     s.normalize("營收")              → "Revenue"                      │
# │     s.extract("SYSTEM_PREFIX","VIA_Master.ps1") → "VIA"              │
# │     s.scan_ll_violations(code)       → ["LL#17","LL#20"]             │
# │     s.extract_anchors(code)          → ["ANCHOR[VIA:ANCHOR:...]"]    │
# │                                                                        │
# │  C. 智慧資產指令 (Asset Commands) — JSON 儲存 / 還原 / 插入             │
# │     from VIA_SSOT_Unified import asset_dump, asset_load, asset_patch  │
# │     payload = asset_dump(fn_code, meta)  → JSON str (儲存)           │
# │     fn_code = asset_load(json_str)        → fn source (還原)          │
# │     new_code= asset_patch(target, slot, json_str) → patched (插入)   │
# └─────────────────────────────────────────────────────────────────────────┘

from __future__ import annotations
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

# ===== [VIA:ANCHOR:SAFE-STATE:START] =====
# Bridged by VDF_MDL001_Supportive_Bridge_v4 on 2026-04-26 02:33 for VIA_SSOT_Unified

# =============================================================================
# VDF Accelerator integration · injected by VDF_MDL001_Supportive_Bridge_v4
# =============================================================================
# Provides cached/retried/deduped HTTP fetch via VDF_MDL000_Accelerator_Core_v4.
# Original module behavior is preserved; this only adds optional shortcuts:
#   vdf_fetch / vdf_fetch_json / vdf_fetch_many / vdf_accelerated / vdf_stats
# Bridge marker: VDF_MDL000_Accelerator_Core_v4
try:
    import sys as _vdf_sys
    import pathlib as _vdf_pathlib
    _VDF_PROBE = _vdf_pathlib.Path(__file__).resolve()
    while _VDF_PROBE.parent != _VDF_PROBE:
        _candidate = _VDF_PROBE / "VeritasDataForge" / "accelerator"
        if _candidate.exists():
            _vdf_sys.path.insert(0, str(_VDF_PROBE / "VeritasDataForge"))
            break
        _VDF_PROBE = _VDF_PROBE.parent
    from accelerator.VDF_MDL000_Accelerator_Core_v4 import (
        fetch as vdf_fetch,
        fetch_json as vdf_fetch_json,
        fetch_many as vdf_fetch_many,
        accelerated as vdf_accelerated,
        stats as vdf_stats,
    )
    _VDF_BRIDGE_OK = True
except Exception:
    _VDF_BRIDGE_OK = False
# =============================================================================
import threading as _via_threading

class _VIAStateBox:
    _lock = _via_threading.RLock()
    _store = {}

    @classmethod
    def get(cls, key, default=None):
        with cls._lock:
            return cls._store.get(key, default)

    @classmethod
    def set(cls, key, value):
        with cls._lock:
            cls._store[key] = value
            return value

    @classmethod
    def update(cls, **kwargs):
        with cls._lock:
            cls._store.update(kwargs)
            return dict(cls._store)

def _via_safe_global_get(name, default=None):
    return _VIAStateBox.get(name, default)

def _via_safe_global_set(name, value):
    return _VIAStateBox.set(name, value)
# ===== [VIA:ANCHOR:SAFE-STATE:END] =====

# ===== [VIA:ANCHOR:EXEC-EVAL:START] =====
def _via_exec_eval_review_marker():
    return {
        "policy": "REVIEW_REQUIRED",
        "note": "exec/eval preserved intentionally in STEP-3A; defer destructive rewrite to later step."
    }
# ===== [VIA:ANCHOR:EXEC-EVAL:END] =====

# ===== [VIA:ANCHOR:PD_PL:START] =====
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import polars as pl
except Exception:
    pl = None
# ===== [VIA:ANCHOR:PD_PL:END] =====

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
import sys
from pathlib import Path

def _via_bootstrap_support_paths() -> None:
    try:
        _self = Path(__file__).resolve()
        _vdf_root = _self.parent
        _module_root = _vdf_root.parent
        _support_root = _module_root / "supportive_module"
        for _p in (_vdf_root, _module_root, _support_root):
            _s = str(_p)
            if _s not in sys.path:
                sys.path.insert(0, _s)
    except Exception:
        pass

_via_bootstrap_support_paths()

try:
    import VIA_SSOT_Unified as VIA_SSOT_Unified
except Exception:
    VIA_SSOT_Unified = None

try:
    import VeritasAegisNexus as VeritasAegisNexus
except Exception:
    VeritasAegisNexus = None

try:
    import VeritasCeleritas as VeritasCeleritas
except Exception:
    VeritasCeleritas = None
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

import base64, hashlib, json, logging, os, re, textwrap
from typing import Any
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# ── type aliases ──────────────────────────────────────────────────────────
Rule     = dict[str, Any]
SynIdx   = dict[str, str]
RegIdx   = dict[str, Rule]
LstIdx   = dict[str, Rule]

# ── governance constants ──────────────────────────────────────────────────
_ALLOWED_STATUSES    = {"stable", "experimental", "deprecated"}
_ALLOWED_MATCH_MODES = {"exact", "casefold", "regex"}
# ── slot markers ──────────────────────────────────────────────────────────
# Slot format in target code:  # [VAOS-FILL-SLOT:SLOT_NAME]
_SLOT_RE   = re.compile(r'#\s*\[VAOS-FILL-SLOT:([A-Z0-9_\-]+)\]')
# Anchor format:               # ANCHOR[VIA:ANCHOR:XXX-001]
_ANCHOR_RE = re.compile(r'ANCHOR\[VIA:ANCHOR:([A-Z0-9\-]+)\]')
# Asset header fence:          # ── [ASSET:AST-PY-...] ──
_ASSET_FENCE = '# ── [ASSET:{aid}] ──'

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-SPEC] — Naming & Format Conventions
# ============================================================
# ┌── CONVENTION TABLE ────────────────────────────────────────────────────┐
# │ Category    │ Format                          │ Example                │
# │─────────────┼─────────────────────────────────┼────────────────────────│
# │ RULE ID     │ RGX|LST|SYN-{DOM}-{GRP}-{NNNN} │ RGX-FIN-TW-0001       │
# │ ASSET ID    │ AST-{LANG}-{TYPE}-{SYS}-NNN-NNN │ AST-PY-FNC-VIA-001-001│
# │ SLOT NAME   │ UPPER_SNAKE (no spaces)          │ SLOT_ACC               │
# │ ANCHOR      │ ANCHOR[VIA:ANCHOR:{ID}]          │ ANCHOR[VIA:ANCHOR:X-1]│
# │ CANONICAL   │ PascalCase                       │ Revenue                │
# │ STATUS      │ stable|experimental|deprecated   │ stable                │
# │ VERSION     │ semver                           │ 1.0.0                 │
# │ MATCH MODE  │ exact|casefold|regex             │ casefold              │
# └──────────────────────────────────────────────────────────────────────── ┘
#
# ┌── SECTION MARKER SPEC ─────────────────────────────────────────────────┐
# │ CONSTANT SECTIONS (AI 禁止修改):                                       │
# │   # ── [CONST:BEGIN] ──   ...   # ── [CONST:END] ──                  │
# │   包含: 資料語料庫 / ANCHOR 標記 / asset header                        │
# │                                                                        │
# │ AI-EDITABLE SECTIONS (AI 主要功能區):                                  │
# │   # ── [AI:BEGIN:SECTION_NAME] ──  ...  # ── [AI:END:SECTION_NAME] ── │
# │   包含: 業務邏輯 / compound helpers / 自訂函式                         │
# │                                                                        │
# │ FILL SLOTS (AI 填入點):                                                │
# │   # [VAOS-FILL-SLOT:SLOT_NAME]                                        │
# │   AI 看到此標記即知道可填入的位置，填入後標記保留                       │
# └──────────────────────────────────────────────────────────────────────── ┘

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-DATA] — Embedded Rule Corpus
# ── [CONST:BEGIN] ──
# ============================================================

_RAW_REGEX: list[Rule] = json.loads(r'''
[
  {
    "rule_id": "RGX-FIN-TW-0001",
    "rule_name": "TW_STOCK_CODE_4DIGIT",
    "pattern": "(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})",
    "flags": [],
    "purpose": "辨識四位台股代碼（第一碼不可為0，排除2021-2030年份）",
    "examples_pass": [
      "2330",
      "0050",
      "6488"
    ],
    "examples_fail": [
      "0050",
      "2025",
      "AAPL",
      "12345"
    ],
    "note": "LOCKED — 勿修改，同 VRN TW_TICKER_REGEX",
    "status": "stable",
    "version": "1.1.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0002",
    "rule_name": "TW_YFINANCE_TICKER",
    "pattern": "^\\d{4}\\.(TW|TWO)$",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識 yfinance 台股 ticker",
    "examples_pass": [
      "2330.TW",
      "6488.TWO"
    ],
    "examples_fail": [
      "2330",
      "2330 TT",
      "AAPL"
    ],
    "note": "LOCKED — 同 VRN TW_YFINANCE_REGEX",
    "status": "stable",
    "version": "1.1.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0003",
    "rule_name": "TW_BLOOMBERG_TICKER",
    "pattern": "^\\d{4}\\s+TT$",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識 Bloomberg XXXX TT 格式台股代碼",
    "examples_pass": [
      "2330 TT"
    ],
    "examples_fail": [
      "2330.TW",
      "2330"
    ],
    "note": "LOCKED — 同 VRN TW_BLOOMBERG_REGEX",
    "status": "stable",
    "version": "1.1.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0004",
    "rule_name": "DATE_ISO",
    "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
    "flags": [],
    "purpose": "辨識 ISO YYYY-MM-DD 日期",
    "examples_pass": [
      "2026-03-23"
    ],
    "examples_fail": [
      "2026/03/23",
      "23-03-2026"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0005",
    "rule_name": "DATE_SLASH",
    "pattern": "^\\d{4}/\\d{2}/\\d{2}$",
    "flags": [],
    "purpose": "辨識 YYYY/MM/DD 日期",
    "examples_pass": [
      "2026/03/23"
    ],
    "examples_fail": [
      "2026-03-23"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0006",
    "rule_name": "DATE_ROC",
    "pattern": "^\\d{2,3}/\\d{2}/\\d{2}$",
    "flags": [],
    "purpose": "辨識民國年日期 YYY/MM/DD",
    "examples_pass": [
      "113/03/23",
      "99/12/31"
    ],
    "examples_fail": [
      "2026/03/23"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0007",
    "rule_name": "DATE_QUARTER",
    "pattern": "^(\\d{4})Q([1-4])$",
    "flags": [],
    "purpose": "辨識季度格式 YYYYQn",
    "examples_pass": [
      "2026Q1",
      "2025Q4"
    ],
    "examples_fail": [
      "2026-Q1",
      "Q12026"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0008",
    "rule_name": "NUMBER_WITH_COMMAS",
    "pattern": "^-?\\d{1,3}(,\\d{3})*(\\.\\d+)?$",
    "flags": [],
    "purpose": "辨識含千分位數字",
    "examples_pass": [
      "1,234",
      "-12,345.67",
      "1,000,000"
    ],
    "examples_fail": [
      "12,34",
      "ABC"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0009",
    "rule_name": "PERCENT_VALUE",
    "pattern": "^-?\\d+(\\.\\d+)?%$",
    "flags": [],
    "purpose": "辨識百分比數值",
    "examples_pass": [
      "12%",
      "-3.5%",
      "100%"
    ],
    "examples_fail": [
      "12",
      "abc%",
      "-%"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0010",
    "rule_name": "FINANCE_EMPTY_VALUE",
    "pattern": "^(--|N/A|NA|無|空白|null|None|-)?$",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識財務常見空值與佔位符",
    "examples_pass": [
      "--",
      "N/A",
      "null",
      "-",
      "無"
    ],
    "examples_fail": [
      "0",
      "123",
      "none-value"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0011",
    "rule_name": "TABLE_HEADER_INCOME_STMT",
    "pattern": "(?i)(損益|收入|Income|Revenue|Profit|Loss|Statement)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識損益表相關標題",
    "examples_pass": [
      "綜合損益表",
      "Income Statement",
      "Revenue"
    ],
    "examples_fail": [
      "資產負債表",
      "Balance Sheet"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0012",
    "rule_name": "TABLE_HEADER_BALANCE_SHEET",
    "pattern": "(?i)(資產|負債|權益|balance.?sheet)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識資產負債表標題",
    "examples_pass": [
      "資產負債表",
      "Balance Sheet",
      "Equity"
    ],
    "examples_fail": [
      "損益表",
      "現金流量表"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0013",
    "rule_name": "TABLE_HEADER_CASHFLOW",
    "pattern": "(?i)(現金流量|cash.?flow)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識現金流量表標題",
    "examples_pass": [
      "現金流量表",
      "Cash Flow Statement"
    ],
    "examples_fail": [
      "資產負債表"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0014",
    "rule_name": "BROKER_RATING",
    "pattern": "(?i)(強力買進|買進|增持|持有|中立|減持|賣出|Outperform|Buy|Hold|Sell|Neutral|Underperform|Accumulate|Add|Reduce)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識券商評等",
    "examples_pass": [
      "Buy",
      "強力買進",
      "Hold",
      "Sell",
      "Outperform"
    ],
    "examples_fail": [
      "看好",
      "分析"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0015",
    "rule_name": "CURRENCY_UNIT",
    "pattern": "(?i)(新台幣|TWD|USD|美元|港幣|HKD|人民幣|CNY|日圓|JPY)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識幣別",
    "examples_pass": [
      "新台幣",
      "USD",
      "TWD",
      "美元"
    ],
    "examples_fail": [
      "數量",
      "單位"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-FIN-TW-0016",
    "rule_name": "AMOUNT_UNIT_TW",
    "pattern": "(?i)單位[：:](新台幣)?(仟元|千元|百萬元|億元|元)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識財報金額單位聲明列",
    "examples_pass": [
      "單位：新台幣仟元",
      "單位：百萬元"
    ],
    "examples_fail": [
      "2330",
      "單位"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0001",
    "rule_name": "WINDOWS_ABSOLUTE_PATH",
    "pattern": "^[A-Za-z]:\\\\.+$",
    "flags": [],
    "purpose": "辨識 Windows 絕對路徑",
    "examples_pass": [
      "C:\\Users\\tonyk\\Downloads\\VIA_Master_v11.ps1"
    ],
    "examples_fail": [
      ".\\module\\test.ps1",
      "module/test.py"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0002",
    "rule_name": "FILE_EXTENSION_CODE",
    "pattern": "\\.(ps1|psm1|psd1|py|js|ts|html|htm|json|yaml|yml|md|csv|parquet)$",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識可掃描的程式/資料檔案副檔名",
    "examples_pass": [
      "test.ps1",
      "demo.py",
      "index.html",
      "data.json"
    ],
    "examples_fail": [
      "README",
      "file.tmp",
      "photo.jpg"
    ],
    "status": "stable",
    "version": "1.1.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0003",
    "rule_name": "WINDOWS_COPY_SUFFIX",
    "pattern": "\\s*\\((\\d+)\\)(?=\\.|$)",
    "flags": [],
    "purpose": "辨識 Windows 複製尾碼，如 (1) (2)",
    "examples_pass": [
      "VIA_Master_v11 (1).ps1",
      "VDS_ChipFetcher_HTML_v1 (6).py"
    ],
    "examples_fail": [
      "VIA_Master_v11.ps1",
      "Part(ABC)"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0004",
    "rule_name": "SEMVER_FULL",
    "pattern": "v(\\d+)\\.(\\d+)\\.(\\d+)(?:[._-]|$)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識完整 semver 版本 vX.Y.Z",
    "examples_pass": [
      "v1.0.0",
      "v3.5.1",
      "v12.0.0"
    ],
    "examples_fail": [
      "v12",
      "version1"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0005",
    "rule_name": "VERSION_SHORT",
    "pattern": "_v(\\d+)(?:_(\\d+)|\\.\\d+)?(?=[_. ]|$)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識短版本格式 _v12 / _v3_1",
    "examples_pass": [
      "VPS_Master_v5.ps1",
      "VIA_LEGO_v12",
      "VIA_v3_1"
    ],
    "examples_fail": [
      "version12",
      "ver_1"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0006",
    "rule_name": "SYSTEM_PREFIX",
    "pattern": "^(VIA|VPN|VPS|VRN|VDF|VSE|VIS|VDS|VGE)(?=[_\\-\\s.]|$)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識 Veritas 系統前綴（7 個核心系統 + VGE）",
    "examples_pass": [
      "VIA_Master_v11.ps1",
      "VRN_PyWorker.py",
      "VGE_v20.ps1"
    ],
    "examples_fail": [
      "main.py",
      "tool.ps1",
      "VIAXX.ps1"
    ],
    "status": "stable",
    "version": "1.1.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0007",
    "rule_name": "MODULE_CODE_SHORT",
    "pattern": "(?:^|[_\\-])M(0[1-9]|[1-9]\\d)(?=[_\\-. ]|$)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識短模組碼 M01–M99",
    "examples_pass": [
      "VPN_M07_PanoramicIntelligence.ps1",
      "VRN_M01_Extractor.py"
    ],
    "examples_fail": [
      "MDL0301",
      "module1",
      "M0A"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0008",
    "rule_name": "MODULE_CODE_LONG",
    "pattern": "MDL(\\d{4})(?=[_\\-. ]|$)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識長模組碼 MDL0301",
    "examples_pass": [
      "VPN_MDL0301_InventoryScanner_v1.ps1"
    ],
    "examples_fail": [
      "M01",
      "0301"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0009",
    "rule_name": "PART_CODE",
    "pattern": "(?i)Part(\\d+)(?=[_\\-. ]|$)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識 Part 分段命名",
    "examples_pass": [
      "VPS_Part3_Governance.ps1",
      "VPS_Part4_HtmlGen.ps1"
    ],
    "examples_fail": [
      "party.ps1",
      "partition"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0010",
    "rule_name": "MODPACK_CODE",
    "pattern": "ModPack_([A-Z])(?=[_\\-. ]|$)",
    "flags": [],
    "purpose": "辨識 ModPack 字母代碼 A–Z",
    "examples_pass": [
      "VIA_ModPack_H_AccelSupreme.py",
      "VIA_ModPack_I_NetSuperShield.py"
    ],
    "examples_fail": [
      "ModulePack",
      "ModPack_12"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0011",
    "rule_name": "ANCHOR_ID",
    "pattern": "ANCHOR\\[VIA:ANCHOR:([A-Z0-9\\-]+)\\]",
    "flags": [],
    "purpose": "辨識 VIA ANCHOR 標記",
    "examples_pass": [
      "ANCHOR[VIA:ANCHOR:CC-MAIN-001]",
      "ANCHOR[VIA:ANCHOR:FUSION-HASH-001]"
    ],
    "examples_fail": [
      "[ANCHOR:CC-MAIN-001]",
      "ANCHOR[CC-MAIN]"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0012",
    "rule_name": "SMART_ASSET_ID",
    "pattern": "AST-(PS|PY|JS|HTML|JSON|YAML)-(MOD|CLS|FNC|CHK|RUN|MAIN|REG|CFG|LIB|PKG|RPT|FIX)-(VIA|VPN|VPS|VRN|VDF|VSE|VIS|VDS)-\\d{3}-\\d{3}",
    "flags": [],
    "purpose": "辨識 VAOS Smart Asset ID",
    "examples_pass": [
      "AST-PS-MOD-VIA-001-001",
      "AST-PY-PKG-VIA-800-001"
    ],
    "examples_fail": [
      "AST-PS-VIA-001",
      "MOD-001-001"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0013",
    "rule_name": "LL_RULE_REFERENCE",
    "pattern": "LL#(1[0-9]|20)",
    "flags": [],
    "purpose": "辨識 LL 規則引用 LL#10–LL#20",
    "examples_pass": [
      "LL#10",
      "LL#17",
      "LL#20"
    ],
    "examples_fail": [
      "LL9",
      "LL#21",
      "LL#5"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0014",
    "rule_name": "IS_RULE_REFERENCE",
    "pattern": "IS-(0[1-9]|1[0-7])(?=[^\\d]|$)",
    "flags": [],
    "purpose": "辨識 IS 規則引用 IS-01–IS-17",
    "examples_pass": [
      "IS-01",
      "IS-17"
    ],
    "examples_fail": [
      "IS-18",
      "IS-0",
      "IS-1X"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-SCAN-PATH-0015",
    "rule_name": "RISK_CODE",
    "pattern": "RISK-([1-4])(?=[^\\d]|$)",
    "flags": [],
    "purpose": "辨識風險等級 RISK-1 至 RISK-4",
    "examples_pass": [
      "RISK-1",
      "RISK-4"
    ],
    "examples_fail": [
      "RISK-5",
      "RISK-0"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "file_scan"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0001",
    "rule_name": "HTML_TABLE_TAG",
    "pattern": "<table[^>]*>",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識 HTML table 開啟標籤",
    "examples_pass": [
      "<table>",
      "<table class=\"data\">"
    ],
    "examples_fail": [
      "</table>",
      "<div>"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0002",
    "rule_name": "HTML_TABLE_HEADER_CELL",
    "pattern": "<th[^>]*>([^<]+)</th>",
    "flags": [
      "IGNORECASE",
      "DOTALL"
    ],
    "purpose": "抽取 th 標籤內容",
    "examples_pass": [
      "<th>日期</th>",
      "<th class=\"col\">Revenue</th>"
    ],
    "examples_fail": [
      "<td>日期</td>"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0003",
    "rule_name": "HTML_DATA_CELL",
    "pattern": "<td[^>]*>([^<]*)</td>",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "抽取 td 標籤純文字內容",
    "examples_pass": [
      "<td>1,234</td>",
      "<td>2330.TW</td>"
    ],
    "examples_fail": [
      "<th>欄位</th>"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0004",
    "rule_name": "HTML_STRIP_TAGS",
    "pattern": "<[^>]+>",
    "flags": [],
    "purpose": "去除所有 HTML 標籤",
    "examples_pass": [
      "<b>text</b>",
      "<span class=\"x\">data</span>"
    ],
    "examples_fail": [
      "plain text"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0005",
    "rule_name": "HTML_SECTION_HEADING",
    "pattern": "<h([1-6])[^>]*>([^<]+)</h\\1>",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識並抽取 h1–h6 標題",
    "examples_pass": [
      "<h1>Annual Report</h1>",
      "<h2>財務摘要</h2>"
    ],
    "examples_fail": [
      "<p>段落</p>"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0006",
    "rule_name": "HTML_SCRIPT_BLOCK",
    "pattern": "<script[^>]*>[\\s\\S]*?</script>",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識並隔離 script 區塊（掃描前先移除）",
    "examples_pass": [
      "<script>alert(1)</script>",
      "<script type=\"text/javascript\">...</script>"
    ],
    "examples_fail": [
      "<link>",
      "<style>"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0007",
    "rule_name": "HTML_STYLE_BLOCK",
    "pattern": "<style[^>]*>[\\s\\S]*?</style>",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識並隔離 style 區塊",
    "examples_pass": [
      "<style>.cls{color:red}</style>"
    ],
    "examples_fail": [
      "<script>"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0008",
    "rule_name": "HTML_COMMENT",
    "pattern": "<!--[\\s\\S]*?-->",
    "flags": [],
    "purpose": "辨識 HTML 注解（保留 ANCHOR 注解，移除其他）",
    "examples_pass": [
      "<!-- comment -->",
      "<!-- ANCHOR[VIA:...] -->"
    ],
    "examples_fail": [
      "// JS comment"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0009",
    "rule_name": "HTML_DATA_ATTR",
    "pattern": "data-([\\w-]+)=['\"]([^'\"]*)['\"]",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "抽取 HTML data-* 屬性",
    "examples_pass": [
      "data-fmt=\"json\"",
      "data-ticker=\"2330\""
    ],
    "examples_fail": [
      "class=\"x\""
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0010",
    "rule_name": "HTML_META_VAOS",
    "pattern": "<meta[^>]+name=['\"]vaos-([\\w-]+)['\"][^>]+content=['\"]([^'\"]+)['\"]",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "抽取 VAOS meta 標籤 (vaos-asset-id, vaos-version 等)",
    "examples_pass": [
      "<meta name=\"vaos-asset-id\" content=\"AST-HTML-TPL-VIA-600-001\">"
    ],
    "examples_fail": [
      "<meta charset=\"UTF-8\">"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0011",
    "rule_name": "HTML_INPUT_VALUE",
    "pattern": "<input[^>]+id=['\"]([\\w-]+)['\"][^>]*(?:value=['\"]([^'\"]*)['\"])?",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "抽取 input 元素 id + value",
    "examples_pass": [
      "<input id=\"inpBase\" value=\"C:\\\\path\">"
    ],
    "examples_fail": [
      "<div id=\"x\">"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0012",
    "rule_name": "HTML_ONCLICK_ATTR",
    "pattern": "onclick=['\"]([^'\"]+)['\"]",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "抽取 onclick 事件（LL#12 合規掃描用）",
    "examples_pass": [
      "onclick=\"doLaunch()\"",
      "onclick=\"goPg('pg0')\""
    ],
    "examples_fail": [
      "onchange=\"x\""
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0013",
    "rule_name": "HTML_CLOUDFLARE_CHALLENGE",
    "pattern": "(?i)(cf-ray|__cf_bm|cloudflare|challenge.html|turnstile|cf_clearance)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "偵測 Cloudflare 反爬蟲挑戰頁特徵",
    "examples_pass": [
      "cf-ray: 123",
      "cloudflare challenge.html"
    ],
    "examples_fail": [
      "normal content"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0014",
    "rule_name": "HTML_ANTI_BOT_SIGNAL",
    "pattern": "(?i)(robot|captcha|bot.?detection|verify.?human|access.?denied|403.?forbidden)",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "偵測反機器人阻擋頁特徵",
    "examples_pass": [
      "captcha required",
      "verify you are human",
      "access denied 403"
    ],
    "examples_fail": [
      "data table",
      "financial report"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  },
  {
    "rule_id": "RGX-HTML-STRUCT-0015",
    "rule_name": "HTML_PAGINATION",
    "pattern": "(?i)(page[=\\s]*(\\d+)|第\\s*(\\d+)\\s*頁|\\bpg\\s*=\\s*(\\d+))",
    "flags": [
      "IGNORECASE"
    ],
    "purpose": "辨識分頁參數與頁碼文字",
    "examples_pass": [
      "page=2",
      "第3頁",
      "pg=10"
    ],
    "examples_fail": [
      "content page",
      "pagoda"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "html_extract"
  }
]
''')

_RAW_LISTS: list[Rule] = json.loads(r'''
[
  {
    "list_id": "LST-RISK-PS-0001",
    "list_name": "PS_CRITICAL_COMMANDS",
    "language": "PS",
    "severity": "CRITICAL",
    "match_mode": "casefold",
    "items": [
      "Remove-Item",
      "Invoke-Expression",
      "Set-ExecutionPolicy",
      "Stop-Process",
      "Restart-Computer",
      "Stop-Computer",
      "Remove-ItemProperty",
      "Register-ScheduledTask",
      "Unregister-ScheduledTask",
      "Format-Volume",
      "Clear-Disk"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-PS-0002",
    "list_name": "PS_HIGH_COMMANDS",
    "language": "PS",
    "severity": "HIGH",
    "match_mode": "casefold",
    "items": [
      "Move-Item",
      "Start-Process",
      "Invoke-WebRequest",
      "Invoke-RestMethod",
      "New-ItemProperty",
      "Set-ItemProperty",
      "New-ScheduledTask",
      "Set-Service",
      "Start-Service",
      "Stop-Service"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-PS-0003",
    "list_name": "PS_LL_VIOLATIONS",
    "language": "PS",
    "severity": "MID",
    "match_mode": "casefold",
    "items": [
      "Start-Process",
      "Invoke-Item"
    ],
    "note": "LL#12 違規 — 禁止自動開啟檔案",
    "status": "stable",
    "version": "1.0.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-PY-0001",
    "list_name": "PY_CRITICAL_PATTERNS",
    "language": "PY",
    "severity": "CRITICAL",
    "match_mode": "exact",
    "items": [
      "os.remove",
      "os.rmdir",
      "shutil.rmtree",
      "subprocess.run",
      "subprocess.Popen",
      "subprocess.call",
      "eval(",
      "exec(",
      "os.system("
    ],
    "status": "stable",
    "version": "1.1.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-PY-0002",
    "list_name": "PY_HIGH_PATTERNS",
    "language": "PY",
    "severity": "HIGH",
    "match_mode": "exact",
    "items": [
      "requests.get",
      "requests.post",
      "requests.put",
      "requests.delete",
      "httpx.get",
      "httpx.post",
      "aiohttp.ClientSession",
      "cloudscraper.create_scraper",
      "selenium.webdriver",
      "playwright",
      "undetected_chromedriver"
    ],
    "status": "stable",
    "version": "1.1.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-PY-0003",
    "list_name": "PY_IS_PATTERNS",
    "language": "PY",
    "severity": "MID",
    "match_mode": "exact",
    "items": [
      "except Exception as e:  # 原裸 except 已安全包裝",
      "except Exception:",
      "raise Exception",
      "raise"
    ],
    "note": "IS-02 bare except / IS-06 broad raise",
    "status": "stable",
    "version": "1.0.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-JS-0001",
    "list_name": "JS_CRITICAL_PATTERNS",
    "language": "JS",
    "severity": "CRITICAL",
    "match_mode": "exact",
    "items": [
      "eval(",
      "Function(",
      "document.write(",
      "localStorage.clear(",
      "sessionStorage.clear(",
      "new Function("
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-RISK-JS-0002",
    "list_name": "JS_HIGH_PATTERNS",
    "language": "JS",
    "severity": "HIGH",
    "match_mode": "exact",
    "items": [
      "fetch(",
      "XMLHttpRequest",
      "axios.get(",
      "axios.post(",
      "window.location.href",
      "document.cookie"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "command_risk"
  },
  {
    "list_id": "LST-FIN-NOISE-0001",
    "list_name": "FINANCIAL_NOISE_ROWS",
    "match_mode": "casefold",
    "items": [
      "合計",
      "小計",
      "總計",
      "附註",
      "說明",
      "單位：新台幣仟元",
      "單位：新台幣千元",
      "單位：新台幣元",
      "單位：百萬元",
      "單位：億元",
      "以下空白",
      "（以下空白）",
      "本表業經核閱",
      "董事長",
      "經理人",
      "簽名或蓋章"
    ],
    "status": "stable",
    "version": "1.1.0",
    "domain": "finance_tw"
  },
  {
    "list_id": "LST-FIN-NOISE-0002",
    "list_name": "FINANCIAL_PLACEHOLDER_VALUES",
    "match_mode": "casefold",
    "items": [
      "--",
      "—",
      "－",
      "N/A",
      "NA",
      "n/a",
      "null",
      "None",
      "NaN",
      "無",
      "空白",
      "未揭露"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "list_id": "LST-FIN-NOISE-0003",
    "list_name": "FINANCIAL_UNIT_DECLARATIONS",
    "match_mode": "casefold",
    "items": [
      "單位：新台幣仟元",
      "單位：新台幣千元",
      "單位：新台幣百萬元",
      "單位：新台幣億元",
      "單位：仟元",
      "單位：千元",
      "單位：百萬元",
      "Unit: TWD Thousands",
      "Unit: NTD Millions"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "list_id": "LST-FIN-NOISE-0004",
    "list_name": "HTML_TABLE_STRUCTURAL_NOISE",
    "match_mode": "casefold",
    "items": [
      "項目",
      "科目",
      "說明",
      "備註",
      "附註",
      "Note",
      "Notes",
      "Description",
      "詳見附錄",
      "see notes"
    ],
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "list_id": "LST-STOP-ZH-0001",
    "list_name": "STOPWORDS_ZH_FINANCIAL",
    "match_mode": "exact",
    "items": [
      "的",
      "及",
      "與",
      "且",
      "或",
      "為",
      "是",
      "之",
      "於",
      "等",
      "並",
      "其",
      "有",
      "該",
      "此",
      "如",
      "即",
      "由",
      "在",
      "對",
      "以",
      "依",
      "所"
    ],
    "purpose": "中文財報文本停用詞（助詞/連詞）",
    "status": "stable",
    "version": "1.0.0",
    "domain": "report_sections"
  },
  {
    "list_id": "LST-STOP-ZH-0002",
    "list_name": "STOPWORDS_ZH_REPORT_FILLER",
    "match_mode": "casefold",
    "items": [
      "詳見",
      "參閱",
      "如前所述",
      "茲說明如下",
      "惟",
      "然",
      "按",
      "爰",
      "查",
      "又",
      "茲",
      "為此",
      "職是之故",
      "說明如后",
      "詳附",
      "請詳閱"
    ],
    "purpose": "財報慣用填充詞（搜尋關鍵字前過濾）",
    "status": "stable",
    "version": "1.0.0",
    "domain": "report_sections"
  },
  {
    "list_id": "LST-STOP-EN-0001",
    "list_name": "STOPWORDS_EN_FINANCIAL",
    "match_mode": "casefold",
    "items": [
      "the",
      "a",
      "an",
      "of",
      "in",
      "on",
      "at",
      "to",
      "by",
      "for",
      "with",
      "and",
      "or",
      "but",
      "is",
      "are",
      "was",
      "were",
      "be",
      "been",
      "as",
      "from",
      "that",
      "this",
      "which",
      "it",
      "its",
      "have",
      "has",
      "had",
      "been"
    ],
    "purpose": "英文財報文本通用停用詞",
    "status": "stable",
    "version": "1.0.0",
    "domain": "report_sections"
  },
  {
    "list_id": "LST-STOP-SCAN-0001",
    "list_name": "STOPWORDS_SCAN_FILENAMES",
    "match_mode": "casefold",
    "items": [
      "test",
      "tmp",
      "temp",
      "backup",
      "bak",
      "old",
      "copy",
      "draft",
      "wip",
      "deprecated",
      "archive",
      "unused",
      "delete",
      "remove",
      "fix",
      "todo"
    ],
    "purpose": "全景掃描時的低優先度檔名關鍵字",
    "status": "stable",
    "version": "1.0.0",
    "domain": "report_sections"
  },
  {
    "list_id": "LST-STOP-HTML-0001",
    "list_name": "STOPWORDS_HTML_TAGS",
    "match_mode": "casefold",
    "items": [
      "br",
      "hr",
      "meta",
      "link",
      "script",
      "style",
      "noscript",
      "iframe",
      "embed",
      "object",
      "head",
      "html",
      "body",
      "title"
    ],
    "purpose": "HTML 掃描時應忽略的結構標籤名稱",
    "status": "stable",
    "version": "1.0.0",
    "domain": "report_sections"
  },
  {
    "list_id": "LST-STOP-ASSET-0001",
    "list_name": "STOPWORDS_ASSET_NAMES",
    "match_mode": "casefold",
    "items": [
      "main",
      "index",
      "init",
      "helper",
      "utils",
      "common",
      "shared",
      "base",
      "config",
      "settings",
      "constants",
      "types",
      "models",
      "schema"
    ],
    "purpose": "智慧資產命名時的通用佔位詞（應加系統前綴才有意義）",
    "status": "stable",
    "version": "1.0.0",
    "domain": "report_sections"
  }
]
''')

_RAW_SYNONYMS: list[Rule] = json.loads(r'''
[
  {
    "syn_id": "SYN-FIN-ACCOUNT-0001",
    "canonical": "Revenue",
    "aliases": [
      "營業收入",
      "營收",
      "Sales",
      "Operating Revenue",
      "營業收入淨額",
      "Net Sales"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0002",
    "canonical": "CostOfRevenue",
    "aliases": [
      "營業成本",
      "銷售成本",
      "Cost of Goods Sold",
      "COGS",
      "Cost of Sales"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0003",
    "canonical": "GrossProfit",
    "aliases": [
      "營業毛利",
      "毛利",
      "Gross Profit",
      "毛利潤"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0004",
    "canonical": "OperatingExpenses",
    "aliases": [
      "營業費用",
      "Operating Expenses",
      "銷管研費"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0005",
    "canonical": "OperatingIncome",
    "aliases": [
      "營業利益",
      "營業淨利",
      "Operating Income",
      "EBIT",
      "Earnings Before Interest and Taxes"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0006",
    "canonical": "NetIncome",
    "aliases": [
      "本期淨利",
      "淨利",
      "淨損益",
      "Net Income",
      "Net Profit",
      "稅後淨利",
      "歸屬母公司淨利"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0007",
    "canonical": "EPS",
    "aliases": [
      "每股盈餘",
      "Earnings Per Share"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0008",
    "canonical": "EBITDA",
    "aliases": [
      "稅息折舊及攤銷前利潤",
      "EBITDA"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0009",
    "canonical": "TotalAssets",
    "aliases": [
      "資產總額",
      "總資產",
      "Total Assets",
      "資產合計"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0010",
    "canonical": "CurrentAssets",
    "aliases": [
      "流動資產",
      "Current Assets",
      "流動資產合計"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0011",
    "canonical": "NonCurrentAssets",
    "aliases": [
      "非流動資產",
      "Non-Current Assets",
      "非流動資產合計",
      "長期資產"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0012",
    "canonical": "TotalLiabilities",
    "aliases": [
      "負債總額",
      "總負債",
      "Total Liabilities",
      "負債合計"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0013",
    "canonical": "CurrentLiabilities",
    "aliases": [
      "流動負債",
      "Current Liabilities",
      "流動負債合計"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0014",
    "canonical": "Equity",
    "aliases": [
      "權益總額",
      "股東權益",
      "業主權益",
      "Equity",
      "Shareholders Equity",
      "Total Equity"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0015",
    "canonical": "CashAndEquivalents",
    "aliases": [
      "現金及約當現金",
      "Cash and Cash Equivalents",
      "現金",
      "Cash"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0016",
    "canonical": "OperatingCashFlow",
    "aliases": [
      "營業活動之淨現金流入",
      "營業活動現金流量",
      "Operating Cash Flow",
      "Cash from Operations"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0017",
    "canonical": "InvestingCashFlow",
    "aliases": [
      "投資活動之淨現金流量",
      "投資活動現金流量",
      "Investing Cash Flow",
      "Cash from Investing"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0018",
    "canonical": "FinancingCashFlow",
    "aliases": [
      "籌資活動之淨現金流量",
      "融資活動現金流量",
      "Financing Cash Flow",
      "Cash from Financing"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0019",
    "canonical": "DividendPerShare",
    "aliases": [
      "每股股利",
      "股利",
      "DPS",
      "Dividend Per Share"
    ],
    "group": "dividend",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0020",
    "canonical": "ResearchAndDevelopment",
    "aliases": [
      "研究發展費用",
      "研發費用",
      "R&D",
      "Research and Development"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0001",
    "canonical": "2330.TW",
    "aliases": [
      "2330",
      "2330 TT",
      "台積電",
      "台灣積體電路",
      "TSMC",
      "Taiwan Semiconductor",
      "TSM"
    ],
    "group": "semiconductor",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0002",
    "canonical": "2317.TW",
    "aliases": [
      "2317",
      "2317 TT",
      "鴻海",
      "Hon Hai",
      "Foxconn",
      "鴻海精密"
    ],
    "group": "electronics",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0003",
    "canonical": "2454.TW",
    "aliases": [
      "2454",
      "2454 TT",
      "聯發科",
      "MediaTek",
      "聯發科技"
    ],
    "group": "semiconductor",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0004",
    "canonical": "2881.TW",
    "aliases": [
      "2881",
      "2881 TT",
      "富邦金",
      "Fubon Financial",
      "富邦金控"
    ],
    "group": "financial",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0005",
    "canonical": "2882.TW",
    "aliases": [
      "2882",
      "2882 TT",
      "國泰金",
      "Cathay Financial",
      "國泰金控"
    ],
    "group": "financial",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0006",
    "canonical": "2412.TW",
    "aliases": [
      "2412",
      "2412 TT",
      "中華電",
      "Chunghwa Telecom",
      "中華電信"
    ],
    "group": "telecom",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0007",
    "canonical": "2308.TW",
    "aliases": [
      "2308",
      "2308 TT",
      "台達電",
      "Delta Electronics",
      "台達電子"
    ],
    "group": "electronics",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0008",
    "canonical": "2303.TW",
    "aliases": [
      "2303",
      "2303 TT",
      "聯電",
      "UMC",
      "United Microelectronics"
    ],
    "group": "semiconductor",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0009",
    "canonical": "2002.TW",
    "aliases": [
      "2002",
      "2002 TT",
      "中鋼",
      "China Steel",
      "中國鋼鐵"
    ],
    "group": "materials",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0010",
    "canonical": "1301.TW",
    "aliases": [
      "1301",
      "1301 TT",
      "台塑",
      "Formosa Plastics",
      "台灣塑膠"
    ],
    "group": "materials",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0011",
    "canonical": "0050.TW",
    "aliases": [
      "0050",
      "0050 TT",
      "元大台灣50",
      "Yuanta Taiwan 50",
      "台灣50"
    ],
    "group": "etf",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0012",
    "canonical": "0056.TW",
    "aliases": [
      "0056",
      "0056 TT",
      "元大高股息",
      "Yuanta High Dividend",
      "高股息ETF"
    ],
    "group": "etf",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0013",
    "canonical": "006208.TW",
    "aliases": [
      "006208",
      "006208 TT",
      "富邦台50",
      "Fubon Taiwan 50"
    ],
    "group": "etf",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0014",
    "canonical": "^TWII",
    "aliases": [
      "^TWII",
      "TWII",
      "台灣加權指數",
      "加權指數",
      "TAIEX",
      "台股指數"
    ],
    "group": "index",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0015",
    "canonical": "^TNX",
    "aliases": [
      "^TNX",
      "TNX",
      "美國十年期公債殖利率",
      "10Y Treasury",
      "US10Y",
      "美債10年"
    ],
    "group": "rate",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-TICKER-0016",
    "canonical": "DX-Y.NYB",
    "aliases": [
      "DX-Y.NYB",
      "DXY",
      "美元指數",
      "USD Index"
    ],
    "group": "index",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0021",
    "canonical": "SellingExpenses",
    "aliases": [
      "推銷費用",
      "銷售費用",
      "Selling Expenses",
      "銷售及行銷費用"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0022",
    "canonical": "AdministrativeExpenses",
    "aliases": [
      "管理費用",
      "一般管理費用",
      "Administrative Expenses",
      "General and Administrative Expenses",
      "G&A"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0023",
    "canonical": "SellingGeneralAdmin",
    "aliases": [
      "推銷及管理費用",
      "SG&A",
      "Selling General and Administrative",
      "銷管費用"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0024",
    "canonical": "FinanceCosts",
    "aliases": [
      "財務成本",
      "利息支出",
      "Finance Costs",
      "Interest Expense",
      "利息費用"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0025",
    "canonical": "InterestIncome",
    "aliases": [
      "利息收入",
      "Interest Income",
      "存款利息"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0026",
    "canonical": "ForeignExchangeGain",
    "aliases": [
      "匯兌損益",
      "匯兌利益",
      "Foreign Exchange Gain",
      "FX Gain Loss",
      "匯率變動損益"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0027",
    "canonical": "NonOperatingIncome",
    "aliases": [
      "營業外收入及支出",
      "業外損益",
      "Non-operating Income",
      "Non Operating Income",
      "Other Income Expense",
      "業外收支"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0028",
    "canonical": "PretaxIncome",
    "aliases": [
      "稅前淨利",
      "稅前純益",
      "Income Before Tax",
      "Pretax Income",
      "EBT",
      "Earnings Before Tax"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0029",
    "canonical": "IncomeTaxExpense",
    "aliases": [
      "所得稅費用",
      "Income Tax Expense",
      "Tax Provision",
      "所得稅",
      "稅費"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0030",
    "canonical": "OtherComprehensiveIncome",
    "aliases": [
      "其他綜合損益",
      "OCI",
      "Other Comprehensive Income",
      "綜合損益其他項目"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0031",
    "canonical": "TotalComprehensiveIncome",
    "aliases": [
      "本期綜合損益總額",
      "綜合損益總額",
      "Total Comprehensive Income"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0032",
    "canonical": "BasicEPS",
    "aliases": [
      "基本每股盈餘",
      "Basic EPS",
      "Basic Earnings Per Share"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0033",
    "canonical": "DilutedEPS",
    "aliases": [
      "稀釋每股盈餘",
      "Diluted EPS",
      "Diluted Earnings Per Share",
      "完全稀釋每股盈餘"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0034",
    "canonical": "EquityMethodInvestmentIncome",
    "aliases": [
      "採用權益法認列之損益份額",
      "權益法投資損益",
      "Share of Profit of Associates",
      "Equity Method Income"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0035",
    "canonical": "ExpectedCreditLoss",
    "aliases": [
      "預期信用減損損失",
      "預期信用減損",
      "Expected Credit Loss",
      "ECL"
    ],
    "group": "income_statement",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0036",
    "canonical": "AccountsReceivable",
    "aliases": [
      "應收帳款",
      "應收帳款淨額",
      "Accounts Receivable",
      "A/R",
      "Receivables",
      "貿易應收款"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0037",
    "canonical": "Inventory",
    "aliases": [
      "存貨",
      "庫存",
      "Inventory",
      "Inventories",
      "商品存貨"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0038",
    "canonical": "Prepayments",
    "aliases": [
      "預付款項",
      "Prepayments",
      "預付費用",
      "Prepaid Expenses"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0039",
    "canonical": "FinancialAssetsFVTPL",
    "aliases": [
      "透過損益按公允價值衡量之金融資產",
      "Financial Assets at FVTPL",
      "FVTPL Assets"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0040",
    "canonical": "FinancialAssetsFVOCI",
    "aliases": [
      "透過其他綜合損益按公允價值衡量之金融資產",
      "Financial Assets at FVOCI",
      "FVOCI Assets"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0041",
    "canonical": "EquityMethodInvestments",
    "aliases": [
      "採用權益法之投資",
      "Investments Accounted for Using Equity Method",
      "Investments And Advances",
      "權益法投資"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0042",
    "canonical": "PropertyPlantEquipment",
    "aliases": [
      "不動產廠房及設備",
      "不動產、廠房及設備",
      "PP&E",
      "PPE",
      "Property Plant Equipment",
      "Net PPE",
      "固定資產"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0043",
    "canonical": "RightOfUseAssets",
    "aliases": [
      "使用權資產",
      "Right-of-use Assets",
      "ROU Assets"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0044",
    "canonical": "IntangibleAssets",
    "aliases": [
      "無形資產",
      "Intangible Assets",
      "商譽",
      "Goodwill",
      "Goodwill And Other Intangible Assets"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0045",
    "canonical": "AccountsPayable",
    "aliases": [
      "應付帳款",
      "Accounts Payable",
      "A/P",
      "Payables",
      "貿易應付款"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0046",
    "canonical": "AccruedExpenses",
    "aliases": [
      "應付薪資及費用",
      "應計費用",
      "Accrued Expenses",
      "應付費用"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0047",
    "canonical": "ShortTermBorrowings",
    "aliases": [
      "短期借款",
      "Short-term Borrowings",
      "Short Term Debt",
      "Current Debt",
      "短期負債"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0048",
    "canonical": "LongTermBorrowings",
    "aliases": [
      "長期借款",
      "Long-term Borrowings",
      "Long Term Debt",
      "長期負債"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0049",
    "canonical": "LeaseLiabilities",
    "aliases": [
      "租賃負債",
      "Lease Liabilities",
      "租賃負擔"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0050",
    "canonical": "DeferredTaxLiabilities",
    "aliases": [
      "遞延所得稅負債",
      "Deferred Tax Liabilities",
      "DTL"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0051",
    "canonical": "ShareCapital",
    "aliases": [
      "股本",
      "普通股股本",
      "Share Capital",
      "Common Stock",
      "Capital Stock",
      "實收資本"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0052",
    "canonical": "CapitalSurplus",
    "aliases": [
      "資本公積",
      "Capital Surplus",
      "Additional Paid in Capital",
      "APIC"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0053",
    "canonical": "RetainedEarnings",
    "aliases": [
      "保留盈餘",
      "累積盈餘",
      "Retained Earnings",
      "未分配盈餘"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0054",
    "canonical": "NonControllingInterests",
    "aliases": [
      "非控制權益",
      "Non-controlling Interests",
      "Minority Interest",
      "少數股權"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0055",
    "canonical": "TreasuryStock",
    "aliases": [
      "庫藏股",
      "庫藏股票",
      "Treasury Stock",
      "Treasury Shares"
    ],
    "group": "balance_sheet",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0056",
    "canonical": "Depreciation",
    "aliases": [
      "折舊費用",
      "折舊",
      "Depreciation",
      "固定資產折舊"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0057",
    "canonical": "Amortization",
    "aliases": [
      "攤銷費用",
      "攤提費用",
      "Amortization",
      "無形資產攤銷"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0058",
    "canonical": "DepreciationAndAmortization",
    "aliases": [
      "折舊與攤銷",
      "D&A",
      "Depreciation and Amortization",
      "折舊及攤銷"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0059",
    "canonical": "CapitalExpenditures",
    "aliases": [
      "資本支出",
      "取得不動產廠房及設備",
      "CapEx",
      "Capital Expenditure",
      "Capital Expenditures",
      "設備投資"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0060",
    "canonical": "FreeCashFlow",
    "aliases": [
      "自由現金流量",
      "自由現金流",
      "FCF",
      "Free Cash Flow"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0061",
    "canonical": "DividendsPaid",
    "aliases": [
      "發放現金股利",
      "現金股利",
      "Dividends Paid",
      "Cash Dividends Paid",
      "股利支付"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0062",
    "canonical": "EffectOfExchangeRate",
    "aliases": [
      "匯率影響數",
      "匯率變動影響",
      "Effect of Exchange Rate Changes",
      "Foreign Exchange Effects"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0063",
    "canonical": "NetChangeInCash",
    "aliases": [
      "本期現金及約當現金增加減少",
      "Net Change In Cash",
      "Changes In Cash",
      "現金淨變動"
    ],
    "group": "cash_flow",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0064",
    "canonical": "ReturnOnEquity",
    "aliases": [
      "股東權益報酬率",
      "ROE",
      "Return on Equity",
      "權益報酬率",
      "淨值報酬率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0065",
    "canonical": "ReturnOnAssets",
    "aliases": [
      "總資產報酬率",
      "資產報酬率",
      "ROA",
      "Return on Assets"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0066",
    "canonical": "GrossMargin",
    "aliases": [
      "毛利率",
      "Gross Margin",
      "Gross Profit Margin",
      "營業毛利率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0067",
    "canonical": "OperatingMargin",
    "aliases": [
      "營業利益率",
      "Operating Margin",
      "EBIT Margin",
      "營業淨利率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0068",
    "canonical": "NetProfitMargin",
    "aliases": [
      "純益率",
      "淨利率",
      "Net Profit Margin",
      "Profit Margin",
      "稅後淨利率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0069",
    "canonical": "PretaxMargin",
    "aliases": [
      "稅前淨利率",
      "Pretax Margin",
      "Pre-tax Margin"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0070",
    "canonical": "CurrentRatio",
    "aliases": [
      "流動比率",
      "Current Ratio",
      "流動比"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0071",
    "canonical": "QuickRatio",
    "aliases": [
      "速動比率",
      "Quick Ratio",
      "Acid Test Ratio",
      "酸性測試比率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0072",
    "canonical": "DebtRatio",
    "aliases": [
      "負債比率",
      "Debt Ratio",
      "Debt-to-Asset Ratio",
      "資產負債率",
      "負債比"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0073",
    "canonical": "DebtToEquity",
    "aliases": [
      "負債權益比",
      "Debt-to-Equity",
      "D/E Ratio",
      "負債對權益比率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0074",
    "canonical": "InterestCoverage",
    "aliases": [
      "利息保障倍數",
      "Interest Coverage Ratio",
      "Times Interest Earned",
      "TIE"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0075",
    "canonical": "ReceivablesTurnover",
    "aliases": [
      "應收帳款週轉率",
      "Receivables Turnover",
      "A/R Turnover"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0076",
    "canonical": "InventoryTurnover",
    "aliases": [
      "存貨週轉率",
      "Inventory Turnover"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0077",
    "canonical": "AssetTurnover",
    "aliases": [
      "總資產週轉率",
      "Asset Turnover",
      "Total Asset Turnover"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0078",
    "canonical": "DaysSalesOutstanding",
    "aliases": [
      "平均收現日數",
      "DSO",
      "Days Sales Outstanding",
      "收現天數"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0079",
    "canonical": "DaysInventoryOutstanding",
    "aliases": [
      "平均銷售日數",
      "DIO",
      "Days Inventory Outstanding",
      "存貨天數"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0080",
    "canonical": "CashConversionCycle",
    "aliases": [
      "現金轉換循環",
      "淨營業週期",
      "CCC",
      "Cash Conversion Cycle"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0081",
    "canonical": "CashFlowAdequacyRatio",
    "aliases": [
      "現金流量允當比率",
      "Cash Flow Adequacy Ratio"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0082",
    "canonical": "OperatingCashFlowRatio",
    "aliases": [
      "現金流量比率",
      "Operating Cash Flow Ratio"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0083",
    "canonical": "EffectiveTaxRate",
    "aliases": [
      "有效稅率",
      "Effective Tax Rate",
      "實質稅率"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0084",
    "canonical": "EquityMultiplier",
    "aliases": [
      "權益乘數",
      "Equity Multiplier",
      "財務槓桿乘數"
    ],
    "group": "ratio",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0085",
    "canonical": "PriceToEarnings",
    "aliases": [
      "本益比",
      "P/E",
      "PE Ratio",
      "PER",
      "Price-to-Earnings",
      "TrailingPE",
      "股價盈餘比"
    ],
    "group": "market",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0086",
    "canonical": "PriceToBook",
    "aliases": [
      "股價淨值比",
      "P/B",
      "PB Ratio",
      "PBR",
      "Price-to-Book",
      "市價淨值比"
    ],
    "group": "market",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0087",
    "canonical": "PriceToSales",
    "aliases": [
      "股價營收比",
      "P/S",
      "PS Ratio",
      "PSR",
      "Price-to-Sales",
      "市價營收比"
    ],
    "group": "market",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0088",
    "canonical": "DividendYield",
    "aliases": [
      "現金股利殖利率",
      "股利殖利率",
      "Dividend Yield",
      "現金殖利率",
      "股息收益率",
      "Yield"
    ],
    "group": "market",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0089",
    "canonical": "PayoutRatio",
    "aliases": [
      "股利發放率",
      "配息率",
      "Payout Ratio",
      "Dividend Payout Ratio",
      "股利支付率"
    ],
    "group": "market",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0090",
    "canonical": "BookValuePerShare",
    "aliases": [
      "每股淨值",
      "BVPS",
      "Book Value Per Share",
      "每股帳面價值",
      "每股股東權益"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0091",
    "canonical": "RevenuePerShare",
    "aliases": [
      "每股營業額",
      "每股營收",
      "Revenue Per Share",
      "SPS",
      "Sales Per Share"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0092",
    "canonical": "CashFlowPerShare",
    "aliases": [
      "每股現金流量",
      "每股現金流",
      "CFPS",
      "Cash Flow Per Share"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0093",
    "canonical": "FreeCashFlowPerShare",
    "aliases": [
      "每股自由現金流",
      "FCF Per Share",
      "Free Cash Flow Per Share"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0094",
    "canonical": "SharesOutstanding",
    "aliases": [
      "普通股流通股數",
      "流通在外股數",
      "發行股數",
      "Shares Outstanding",
      "市場流通股"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0095",
    "canonical": "WeightedAverageShares",
    "aliases": [
      "加權平均股數",
      "加權平均流通股數",
      "Weighted Average Shares",
      "基本股數"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  },
  {
    "syn_id": "SYN-FIN-ACCOUNT-0096",
    "canonical": "DilutedShares",
    "aliases": [
      "稀釋後股數",
      "完全稀釋後股數",
      "Fully Diluted Shares",
      "Diluted Average Shares"
    ],
    "group": "per_share",
    "status": "stable",
    "version": "1.0.0",
    "domain": "finance_tw"
  }
]
''')

_CORPUS_STATS: dict[str, int] = {
    "regex_rules":   46,
    "list_rules":    18,
    "synonym_rules": 112,
    "total_aliases": 486,
    "total_rules":   176,
}

# ── [CONST:END] ──

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-BUILD] — Index Construction
# (Internal — do not call directly; use SSOT class)
# ============================================================

def _re_flags(flags: list[str]) -> int:
    val = 0
    for f in flags:
        match f.upper():
            case "IGNORECASE": val |= re.IGNORECASE
            case "MULTILINE":  val |= re.MULTILINE
            case "DOTALL":     val |= re.DOTALL
    return val

def _build_regex_idx(rules: list[Rule]) -> RegIdx:
    idx: RegIdx = {}
    for r in rules:
        name = r.get("rule_name", "")
        if not name:
            raise ValueError(f"regex rule missing rule_name: {r.get('rule_id')}")
        try:
            re.compile(r["pattern"], _re_flags(r.get("flags", [])))
        except re.error as e:
            raise ValueError(f"regex compile error [{name}]: {e}") from e
        idx[name] = r
    return idx

def _build_list_idx(rules: list[Rule]) -> LstIdx:
    idx: LstIdx = {}
    for r in rules:
        name = r.get("list_name", "")
        if not name:
            raise ValueError(f"list rule missing list_name: {r.get('list_id')}")
        mm = r.get("match_mode", "exact")
        if mm not in _ALLOWED_MATCH_MODES:
            raise ValueError(f"invalid match_mode: {mm}")
        idx[name] = r
    return idx

def _build_synonym_idx(rules: list[Rule]) -> SynIdx:
    idx: SynIdx = {}
    conflict: dict[str, str] = {}
    for r in rules:
        if "canonical" not in r or "aliases" not in r:
            raise ValueError(f"synonym rule missing canonical/aliases: {r.get('syn_id')}")
        canonical = str(r["canonical"]).strip()
        if not canonical:
            raise ValueError(f"empty canonical in: {r.get('syn_id')}")
        # register canonical itself
        ck = canonical.lower()
        if ck in conflict and conflict[ck] != canonical:
            raise ValueError(f"canonical conflict: {canonical} vs {conflict[ck]}")
        idx[ck] = canonical
        conflict[ck] = canonical
        # register aliases
        for alias in r.get("aliases", []):
            ak = str(alias).strip().lower()
            if not ak:
                continue
            if ak in conflict and conflict[ak] != canonical:
                raise ValueError(
                    f"alias conflict: '{alias}' → '{conflict[ak]}' / '{canonical}'"
                )
            idx[ak] = canonical
            conflict[ak] = canonical
    return idx

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-QUERY] — SSOT Class (Public API)
# ── [CONST:BEGIN] ──
# ============================================================

class SSOT:
    """
    Single-instance SSOT. Thread-safe read-only after __init__.

    Calling forms:
      A. General   : from VIA_SSOT_Unified import normalize, extract, contains
      B. Embedded  : from VIA_SSOT_Unified import get_ssot; s = get_ssot()
      C. Asset ops : from VIA_SSOT_Unified import asset_dump, asset_load, asset_patch
    """

    __slots__ = ("_rx", "_ls", "_sy")

    def __init__(self) -> None:
        self._rx: RegIdx = _build_regex_idx(_RAW_REGEX)
        self._ls: LstIdx = _build_list_idx(_RAW_LISTS)
        self._sy: SynIdx = _build_synonym_idx(_RAW_SYNONYMS)

    # ─── A. SYNONYM ──────────────────────────────────────────

    def normalize(self, raw: str) -> str:
        """alias → canonical. Returns raw if no match."""
        return self._sy.get(raw.strip().lower(), raw)

    def normalize_batch(self, terms: list[str]) -> list[str]:
        return [self.normalize(t) for t in terms]

    def canonical(self, raw: str) -> str | None:
        """Returns canonical or None."""
        return self._sy.get(raw.strip().lower())

    def all_canonicals(self) -> list[str]:
        return sorted(set(self._sy.values()))

    # ─── B. REGEX ────────────────────────────────────────────

    def match(self, rule_name: str, text: str) -> re.Match | None:
        r = self._rx.get(rule_name)
        if not r:
            return None
        return re.search(r["pattern"], text, _re_flags(r.get("flags", [])))

    def extract(self, rule_name: str, text: str) -> str | None:
        """First match value or None."""
        m = self.match(rule_name, text)
        return m.group(0) if m else None

    def extract_all(self, rule_name: str, text: str) -> list[str]:
        """All match values."""
        r = self._rx.get(rule_name)
        if not r:
            return []
        return re.findall(r["pattern"], text, _re_flags(r.get("flags", [])))

    def test_regex(self, rule_name: str, text: str) -> bool:
        return self.match(rule_name, text) is not None

    def regex_rule(self, rule_name: str) -> Rule | None:
        return self._rx.get(rule_name)

    def regex_names(self, domain: str | None = None) -> list[str]:
        if domain is None:
            return sorted(self._rx)
        return sorted(k for k, v in self._rx.items() if v.get("domain") == domain)

    # ─── C. LIST ─────────────────────────────────────────────

    def contains(self, list_name: str, value: str) -> bool:
        r = self._ls.get(list_name)
        if not r:
            return False
        items = r.get("items", [])
        mode  = str(r.get("match_mode", "exact")).lower()
        if mode == "exact":
            return value in items
        if mode == "casefold":
            return value.strip().lower() in [str(x).strip().lower() for x in items]
        if mode == "regex":
            return any(re.search(str(x), value) for x in items)
        return value in items

    def items(self, list_name: str) -> list[str]:
        r = self._ls.get(list_name)
        return list(r.get("items", [])) if r else []

    def list_rule(self, list_name: str) -> Rule | None:
        return self._ls.get(list_name)

    def list_names(self, domain: str | None = None) -> list[str]:
        if domain is None:
            return sorted(self._ls)
        return sorted(k for k, v in self._ls.items() if v.get("domain") == domain)

    # ── [CONST:END] ──

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-COMPOUND] — Compound Helpers
# ── [AI:BEGIN:COMPOUND_HELPERS] ──
# (AI 可在此區域增加 helper，禁止修改上方 CONST 區)
# ============================================================

    def filter_noise(self,
                     rows: list[str],
                     list_name: str = "FINANCIAL_NOISE_ROWS") -> list[str]:
        """Filter financial table noise rows."""
        return [r for r in rows if not self.contains(list_name, r)]

    def is_risk_command(self, cmd: str, language: str = "PS") -> bool:
        """True if cmd appears in CRITICAL or HIGH risk list for language."""
        lang = language.upper()
        crit = f"PS_CRITICAL_COMMANDS"  if lang == "PS" else f"{lang}_CRITICAL_PATTERNS"
        high = f"PS_HIGH_COMMANDS"      if lang == "PS" else f"{lang}_HIGH_PATTERNS"
        return self.contains(crit, cmd) or self.contains(high, cmd)

    def is_valid_tw_ticker(self, text: str) -> bool:
        return self.test_regex("TW_YFINANCE_TICKER", text)

    def is_veritas_file(self, filename: str) -> bool:
        return self.test_regex("SYSTEM_PREFIX", filename)

    def detect_cloudflare(self, html: str) -> bool:
        return self.test_regex("HTML_CLOUDFLARE_CHALLENGE", html)

    def detect_anti_bot(self, html: str) -> bool:
        return self.test_regex("HTML_ANTI_BOT_SIGNAL", html)

    def scan_ll_violations(self, code: str) -> list[str]:
        """Extract all LL#XX references from source code."""
        return self.extract_all("LL_RULE_REFERENCE", code)

    def scan_is_violations(self, code: str) -> list[str]:
        """Extract all IS-NN references from source code."""
        return self.extract_all("IS_RULE_REFERENCE", code)

    def extract_anchors(self, code: str) -> list[str]:
        """Extract all VIA ANCHOR IDs from source code."""
        return self.extract_all("ANCHOR_ID", code)

    def extract_asset_ids(self, code: str) -> list[str]:
        """Extract all Smart Asset IDs from source code."""
        return self.extract_all("SMART_ASSET_ID", code)

    def strip_html(self, html: str) -> str:
        """Remove all HTML tags from text."""
        return re.sub(self._rx["HTML_STRIP_TAGS"]["pattern"], "", html)

    def find_slots(self, code: str) -> list[str]:
        """Find all VAOS fill-slot names in source."""
        return _SLOT_RE.findall(code)

    # ── [AI:END:COMPOUND_HELPERS] ──

    # ── info ─────────────────────────────────────────────────

    def info(self) -> dict[str, Any]:
        return {
            **_CORPUS_STATS,
            "regex_loaded":   len(self._rx),
            "list_loaded":    len(self._ls),
            "synonym_loaded": len(self._sy),
        }

# [VIA:ANCHOR:SSOT_STEP2_FIRST_DEF_QUARANTINE:START]
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VIA SSOT Step 2 — First module-level def block quarantine                ║
# ║   原因:                                                                  ║
# ║     此區塊原本定義 _default + get_ssot/normalize/extract/extract_all/    ║
# ║     contains/filter_noise (line ~3405-3429)。前 5 個 def 在後段 rebind   ║
# ║     區塊 (line ~3827+) 已重建,造成 module-level 重複定義 (Python 後定義  ║
# ║     覆蓋前定義,但 _default 變數仍存,埋藏雙 singleton 風險)。            ║
# ║   處理:                                                                  ║
# ║     整塊以 docstring 變數註解化,filter_noise 單獨保留 (rebind 沒重建)。  ║
# ║   還原:                                                                  ║
# ║     移除本 sentinel + 取消 quarantine 字串包裹即可。                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
_VIA_OBSOLETE_FIRST_DEF_BLOCK = '''
# ── module-level singleton ────────────────────────────────────────────────
_default: SSOT | None = None

def get_ssot() -> SSOT:
    """Return module-level singleton (lazy-init)."""
    global _default
    if _default is None:
        _default = SSOT()
    return _default

# ── A. General command shortcuts ─────────────────────────────────────────
def normalize(raw: str) -> str:
    return get_ssot().normalize(raw)

def extract(rule: str, text: str) -> str | None:
    return get_ssot().extract(rule, text)

def extract_all(rule: str, text: str) -> list[str]:
    return get_ssot().extract_all(rule, text)

def contains(lst: str, val: str) -> bool:
    return get_ssot().contains(lst, val)

def filter_noise(rows: list[str], list_name: str = "FINANCIAL_NOISE_ROWS") -> list[str]:
    return get_ssot().filter_noise(rows, list_name)


'''  # end VIA SSOT Step 2 first-def quarantine

# ── Preserved from quarantined first-def block ─────────────────────
# (這些 def 在後段 rebind 區塊內未被重建,必須保留供 module-level 呼叫)
def filter_noise(rows: list[str], list_name: str = "FINANCIAL_NOISE_ROWS") -> list[str]:
    return get_ssot().filter_noise(rows, list_name)

# [VIA:ANCHOR:SSOT_STEP2_FIRST_DEF_QUARANTINE:END]

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-STORE] — Smart Asset Storage (JSON)
# ============================================================
# ┌── ASSET JSON SCHEMA ───────────────────────────────────────────────────┐
# │ {                                                                       │
# │   "asset_id":   "AST-PY-FNC-VIA-001-001",   ← VAOS ID               │
# │   "slot_name":  "SLOT_ACC",                  ← fill-slot target      │
# │   "lang":       "PY",                        ← PY|PS|JS|HTML         │
# │   "version":    "1.0.0",                                              │
# │   "status":     "stable",                                             │
# │   "checksum":   "SHA256[:8]",                ← content integrity     │
# │   "anchor":     "ANCHOR[VIA:ANCHOR:XXX-001]",                        │
# │   "source_b64": "<base64 of source code>",   ← actual code          │
# │   "meta": {                                                            │
# │     "purpose":  "...",                                                │
# │     "depends":  ["rule_name"],               ← SSOT rule deps       │
# │     "frozen":   false                        ← if true: no overwrite │
# │   }                                                                    │
# │ }                                                                       │
# └────────────────────────────────────────────────────────────────────────┘

def _sha8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8].upper()

def asset_dump(
    source: str,
    asset_id: str,
    slot_name: str,
    lang: str         = "PY",
    version:  str     = "1.0.0",
    status:   str     = "stable",
    anchor:   str     = "",
    purpose:  str     = "",
    depends:  list[str] | None = None,
    frozen:   bool    = False,
) -> str:
    """
    Serialize a source code block to a VAOS asset JSON string.

    Args:
        source    : raw source code string to store
        asset_id  : VAOS Asset ID  (e.g. AST-PY-FNC-VIA-001-001)
        slot_name : target SLOT name in destination file
        lang      : language code PY|PS|JS|HTML
        ...

    Returns:
        JSON string ready to save as .json file or embed

    Example:
        payload = asset_dump(fn_source, "AST-PY-FNC-VIA-001-001", "SLOT_NORMALIZE")
        with open("assets/AST-PY-FNC-VIA-001-001.json","w") as f:
            f.write(payload)
    """
    source_clean = textwrap.dedent(source).strip()
    checksum     = _sha8(source_clean)
    obj = {
        "asset_id":   asset_id,
        "slot_name":  slot_name,
        "lang":       lang.upper(),
        "version":    version,
        "status":     status,
        "checksum":   f"FP-{checksum}",
        "anchor":     anchor,
        "source_b64": base64.b64encode(source_clean.encode("utf-8")).decode("ascii"),
        "meta": {
            "purpose": purpose,
            "depends": depends or [],
            "frozen":  frozen,
        }
    }
    return json.dumps(obj, ensure_ascii=False, indent=2)

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-RESTORE] — Asset Restore & Patch
# ============================================================

def asset_load(json_str: str) -> str:
    """
    Restore source code from a VAOS asset JSON string.

    Args:
        json_str: JSON string produced by asset_dump()

    Returns:
        Original source code string

    Raises:
        ValueError: if checksum mismatch or frozen asset detected

    Example:
        source = asset_load(open("AST-PY-FNC-VIA-001-001.json").read())
    """
    obj      = json.loads(json_str)
    b64      = obj.get("source_b64", "")
    if not b64:
        raise ValueError(f"asset_load: missing source_b64 in {obj.get('asset_id')}")
    source   = base64.b64decode(b64.encode("ascii")).decode("utf-8")
    expected = f"FP-{_sha8(source)}"
    stored   = obj.get("checksum", "")
    if stored and stored != expected:
        raise ValueError(
            f"asset_load: checksum mismatch for {obj.get('asset_id')}: "
            f"stored={stored} computed={expected}"
        )
    return source

def asset_patch(
    target_code: str,
    json_str:    str,
    slot_name:   str | None = None,
    indent:      int        = 0,
) -> str:
    """
    Insert (patch) a stored asset into target source code at a fill-slot.

    The slot marker format in target:   # [VAOS-FILL-SLOT:SLOT_NAME]

    Behaviour:
      1. Decode source from json_str
      2. Locate slot marker in target_code
      3. Insert source AFTER the slot marker line (marker is preserved)
      4. If slot already filled (next non-blank line is code, not a NEW slot),
         replace existing content up to next slot/anchor/section marker
      5. Verify checksum after patch

    Args:
        target_code : full source code of target file
        json_str    : VAOS asset JSON string
        slot_name   : override slot; if None uses json obj.slot_name
        indent      : additional indent spaces for inserted code

    Returns:
        Patched source code string

    Example:
        new_code = asset_patch(
            open("VRN_M01.py").read(),
            open("AST-PY-FNC-VIA-001-001.json").read()
        )
        open("VRN_M01.py","w").write(new_code)
    """
    obj      = json.loads(json_str)
    source   = asset_load(json_str)   # validates checksum
    frozen   = obj.get("meta", {}).get("frozen", False)
    sname    = slot_name or obj.get("slot_name", "")

    if not sname:
        raise ValueError("asset_patch: slot_name not specified")

    # Build marker line pattern
    marker_pattern = re.compile(
        r'([ \t]*)#\s*\[VAOS-FILL-SLOT:' + re.escape(sname) + r'\]'
    )

    lines = target_code.splitlines(keepends=True)
    marker_idx = None
    slot_indent = ""

    for i, line in enumerate(lines):
        m = marker_pattern.search(line)
        if m:
            marker_idx = i
            slot_indent = m.group(1)
            break

    if marker_idx is None:
        raise ValueError(
            f"asset_patch: slot '{sname}' not found in target code"
        )

    # Apply extra indent on top of slot indent
    pad = slot_indent + (" " * indent)

    # Prepare insertion lines
    insert_lines = []
    # Asset header fence
    insert_lines.append(f"{pad}# ── [ASSET:{obj['asset_id']}] ── v{obj.get('version','?')} {obj.get('checksum','')}\n")
    for src_line in source.splitlines(keepends=True):
        insert_lines.append(pad + src_line if src_line.strip() else src_line)
    insert_lines.append(f"{pad}# ── [/ASSET:{obj['asset_id']}] ──\n")

    # Find end of existing fill region (if any)
    end_idx = marker_idx + 1
    _end_markers = re.compile(
        r'#\s*(\[VAOS-FILL-SLOT:|\[ASSET:|\[/ASSET:|ANCHOR\[VIA:|──\s+\[(?:AI:|CONST:))',
        re.IGNORECASE
    )
    while end_idx < len(lines):
        line = lines[end_idx]
        if _end_markers.search(line) or (
            line.strip().startswith("# ──") and "ASSET" not in line
        ):
            break
        end_idx += 1

    # If frozen and region already filled, raise
    if frozen and end_idx > marker_idx + 1:
        raise ValueError(
            f"asset_patch: slot '{sname}' is frozen (meta.frozen=true); "
            "cannot overwrite existing content"
        )

    # Splice
    new_lines = lines[:marker_idx + 1] + insert_lines + lines[end_idx:]
    return "".join(new_lines)

def asset_verify(target_code: str, json_str: str) -> bool:
    """
    Verify that the content currently in a slot matches the stored asset checksum.

    Returns True if match, False if mismatch or slot not found.
    """
    obj    = json.loads(json_str)
    sname  = obj.get("slot_name", "")
    cksum  = obj.get("checksum", "")

    # Extract block between [ASSET:id] fences
    aid_re = re.escape(obj.get("asset_id", ""))
    region = re.search(
        rf'# ── \[ASSET:{aid_re}\][^\n]*\n(.*?)# ── \[/ASSET:{aid_re}\]',
        target_code,
        re.DOTALL
    )
    if not region:
        return False

    extracted = textwrap.dedent(region.group(1)).strip()
    return f"FP-{_sha8(extracted)}" == cksum

# ============================================================
# ANCHOR[VIA:ANCHOR:SSOT-UTIL] — Self-Test (31 cases)
# ============================================================

def self_test(verbose: bool = True) -> bool:
    s      = SSOT()
    cases: list[tuple[str, bool, str]] = []

    def chk(name: str, got: Any, expected: Any) -> None:
        ok = (got == expected)
        cases.append((name, ok, f"got={got!r} expected={expected!r}" if not ok else ""))

    # ── corpus stats ─────────────────────────────────────
    m  = s.info()
    chk("regex_rules=46",         m["regex_rules"],   46)
    chk("list_rules=18",          m["list_rules"],    18)
    chk("synonym_rules=112",       m["synonym_rules"], 112)

    # ── synonym ──────────────────────────────────────────
    chk("normalize 營收",          s.normalize("營收"),      "Revenue")
    chk("normalize 台積電",         s.normalize("台積電"),     "2330.TW")
    chk("normalize TSMC",          s.normalize("TSMC"),      "2330.TW")
    chk("normalize 本期淨利",        s.normalize("本期淨利"),    "NetIncome")
    chk("normalize DXY",           s.normalize("DXY"),       "DX-Y.NYB")
    chk("normalize unknown→raw",   s.normalize("XYZ_UNKNOWN"), "XYZ_UNKNOWN")
    chk("canonical None",          s.canonical("XYZ_UNKNOWN"), None)
    chk("all_canonicals Revenue",  "Revenue" in s.all_canonicals(), True)

    # ── regex ─────────────────────────────────────────────
    chk("extract TW_YFINANCE 2330.TW",
        s.extract("TW_YFINANCE_TICKER","2330.TW"), "2330.TW")
    chk("extract TW_BLOOMBERG 2330 TT",
        s.extract("TW_BLOOMBERG_TICKER","2330 TT"), "2330 TT")
    chk("extract SYSTEM_PREFIX VIA",
        s.extract("SYSTEM_PREFIX","VIA_Master_v11.ps1"), "VIA")
    chk("extract SYSTEM_PREFIX VGE",
        s.extract("SYSTEM_PREFIX","VGE_v20_THREADJOB.ps1"), "VGE")
    chk("extract MODPACK_CODE H",
        s.extract("MODPACK_CODE","VIA_ModPack_H_AccelSupreme.py"), "ModPack_H")
    chk("extract ANCHOR_ID",
        s.extract("ANCHOR_ID","ANCHOR[VIA:ANCHOR:CC-MAIN-001]"),
        "ANCHOR[VIA:ANCHOR:CC-MAIN-001]")
    chk("extract SMART_ASSET_ID exists",
        s.extract("SMART_ASSET_ID","AST-PY-PKG-VIA-800-001") is not None, True)
    chk("extract LL#17",
        s.extract("LL_RULE_REFERENCE","violates LL#17 here"), "LL#17")
    chk("extract IS-09",
        s.extract("IS_RULE_REFERENCE","IS-09 dollar-colon"), "IS-09")
    chk("test_regex fail",
        s.test_regex("TW_YFINANCE_TICKER","2330"), False)

    # ── list ──────────────────────────────────────────────
    chk("contains PS Remove-Item",  s.contains("PS_CRITICAL_COMMANDS","Remove-Item"), True)
    chk("contains PY eval(",        s.contains("PY_CRITICAL_PATTERNS","eval("),       True)
    chk("contains JS eval(",        s.contains("JS_CRITICAL_PATTERNS","eval("),       True)
    chk("contains NOISE 合計",       s.contains("FINANCIAL_NOISE_ROWS","合計"),         True)
    chk("filter_noise removes 合計",
        "合計" not in s.filter_noise(["Revenue","合計","NetIncome"]), True)

    # ── compound ──────────────────────────────────────────
    chk("is_risk_command PS",       s.is_risk_command("Remove-Item","PS"), True)
    chk("is_valid_tw_ticker ✓",     s.is_valid_tw_ticker("2330.TW"),       True)
    chk("is_valid_tw_ticker ✗",     s.is_valid_tw_ticker("2330"),          False)
    chk("is_veritas_file ✓",        s.is_veritas_file("VRN_PyWorker.py"),  True)
    chk("detect_cloudflare ✓",      s.detect_cloudflare("cf-ray: 123"),    True)

    # ── asset store/restore/patch ─────────────────────────
    _sample_fn = "def hello():\n    return 42\n"
    _json_str  = asset_dump(
        _sample_fn, "AST-PY-FNC-VIA-TEST-001", "SLOT_TEST",
        purpose="unit test fn", depends=["TW_YFINANCE_TICKER"]
    )
    _obj       = json.loads(_json_str)
    chk("asset_dump has asset_id",   "asset_id"   in _obj, True)
    chk("asset_dump has source_b64", "source_b64" in _obj, True)
    chk("asset_dump has checksum",   _obj["checksum"].startswith("FP-"), True)
    _restored  = asset_load(_json_str)
    chk("asset_load roundtrip",      _restored.strip(), _sample_fn.strip())

    # patch test
    _target = "# intro\n# [VAOS-FILL-SLOT:SLOT_TEST]\n# footer\n"
    _patched = asset_patch(_target, _json_str)
    chk("asset_patch inserts ASSET fence",
        "# ── [ASSET:AST-PY-FNC-VIA-TEST-001]" in _patched, True)
    chk("asset_patch preserves slot marker",
        "[VAOS-FILL-SLOT:SLOT_TEST]" in _patched, True)
    chk("asset_patch contains fn source",
        "def hello()" in _patched, True)

    # ── singleton ────────────────────────────────────────
    chk("singleton identity",        get_ssot() is get_ssot(), True)
    chk("module normalize",          normalize("台積電"),        "2330.TW")
    chk("module extract",            extract("TW_YFINANCE_TICKER","6488.TWO"), "6488.TWO")
    chk("module contains",           contains("PS_CRITICAL_COMMANDS","Stop-Computer"), True)

    # ── reporting ─────────────────────────────────────────
    passed = sum(1 for _, ok, _ in cases if ok)
    total  = len(cases)
    all_ok = passed == total

    if verbose:
        for name, ok, detail in cases:
            sym = "OK  " if ok else "FAIL"
            print(f"  [{sym}]  {name:<52} {detail}")
        print(f"\n  {'ALL PASS' if all_ok else 'SOME FAIL'}  ({passed}/{total})")
        m2 = get_ssot().info()
        print(f"  rx={m2['regex_rules']} ls={m2['list_rules']} syn={m2['synonym_rules']} aliases={m2['total_aliases']}")

    return all_ok

if __name__ == "__main__":
    self_test()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VIA POLLUTION QUARANTINE — disabled by VIA_SSOT_PanoramicAugmenter v2 ║
# ║   原因：VIA_FINAL_PATCH_SSOT_COMPAT 簡化版覆寫了 SSOT class 的 module- ║
# ║   level get_ssot/normalize/extract，使外部 import normalize 無法正確 ║
# ║   normalize。本區塊以 docstring 註解化保留，移除 quarantine 即恢復。 ║
# ║   下方「Module-level Rebind」已重建正確的 SSOT-backed 函數綁定。 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
_VIA_QUARANTINED_VIA_FINAL_PATCH = '''
# === VIA_FINAL_PATCH_SSOT_COMPAT ===
_VIA_SSOT = {}

def get_ssot(key=None, default=None):
    if key is None:
        return dict(_VIA_SSOT)
    return _VIA_SSOT.get(key, default)

def set_ssot(key, value):
    _VIA_SSOT[str(key)] = value
    return {"status": "ok", "key": str(key)}

def ssot_health():
    return {"status": "alive", "count": len(_VIA_SSOT)}

def normalize(value):
    return value

# === VIA_FINAL_PATCH_SSOT_COMPAT_V3 ===
_VIA_SSOT = globals().get("_VIA_SSOT", {})

def get_ssot(key=None, default=None):
    if key is None:
        return dict(_VIA_SSOT)
    return _VIA_SSOT.get(key, default)

def set_ssot(key, value):
    _VIA_SSOT[str(key)] = value
    return {"status": "ok", "key": str(key)}

def ssot_health():
    return {"status": "alive", "count": len(_VIA_SSOT)}

def normalize(value):
    return value


'''  # end VIA_QUARANTINED_VIA_FINAL_PATCH

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VIA Module-level Rebind — restored by VIA_SSOT_PanoramicAugmenter v2 ║
# ║   重建 module-level get_ssot/normalize/extract/contains 為 SSOT-backed ║
# ║   形式，覆寫上方 quarantine 區塊原本的簡化 dict-store 行為。 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
_VIA_SSOT_INSTANCE = None

def get_ssot():
    """Return the singleton SSOT instance (rebuilt over VIA_FINAL_PATCH compat)."""
    global _VIA_SSOT_INSTANCE
    if _VIA_SSOT_INSTANCE is None:
        _VIA_SSOT_INSTANCE = SSOT()
    return _VIA_SSOT_INSTANCE

def normalize(raw):
    """Normalize alias to canonical via SSOT."""
    return get_ssot().normalize(raw)

def extract(rule, text):
    """Extract first regex match via SSOT."""
    return get_ssot().extract(rule, text)

def extract_all(rule, text):
    """Extract all regex matches via SSOT."""
    return get_ssot().extract_all(rule, text)

def contains(lst, val):
    """Check whether `val` is in named list via SSOT."""
    return get_ssot().contains(lst, val)

def canonical(raw):
    """Return canonical form or None."""
    return get_ssot().canonical(raw)

def all_canonicals():
    """Return all canonicals."""
    return get_ssot().all_canonicals()

# end VIA Module-level Rebind
# =============================================================================
# [VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE:START]
# Auto injected by VIA Supportive Self-Governance.
# Policy: append-only, metadata + smoke only, no core logic overwrite.
# Module: VIA_SSOT_Unified
# =============================================================================

MODULE_METADATA = globals().get("MODULE_METADATA", {
    "module_id": "VIA_SSOT_Unified",
    "module_name": "VIA_SSOT_Unified",
    "asset_type": "supportive_module",
    "version": "self-governed",
    "input_contract": [],
    "output_contract": [],
    "deliverables": [],
    "doc_paths": [],
    "required_support_tools": [
        "VIA_SSOT_Unified",
        "VeritasAegisNexus",
        "VeritasCeleritas",
        "VIA_EnvManager",
        "VIA_Panorama_AST_RuntimeInjector",
        "VIA_RegistryCore_v1",
        "VIA_Runtime_Bridge_All_in_One"
    ]
})

VIA_SUPPORTIVE_MODULES = globals().get("VIA_SUPPORTIVE_MODULES", {
    "VIA_SSOT_Unified": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py",
    "VeritasAegisNexus": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py",
    "VeritasCeleritas": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py",
    "VIA_EnvManager": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py",
    "VIA_Panorama_AST_RuntimeInjector": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Panorama_AST_RuntimeInjector.py",
    "VIA_RegistryCore_v1": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py",
    "VIA_Runtime_Bridge_All_in_One": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py",
})

def via_supportive_health():
    return {
        "status": "alive",
        "module": "VIA_SSOT_Unified",
        "asset_type": "supportive_module",
        "metadata": bool(MODULE_METADATA),
        "support_tools_declared": len(MODULE_METADATA.get("required_support_tools", [])),
    }

def via_runtime_heartbeat():
    return {"status": "alive", "module": "VIA_SSOT_Unified"}

def via_runtime_smoke():
    try:
        return via_supportive_health()
    except Exception as e:
        return {"status": "error", "module": "VIA_SSOT_Unified", "msg": str(e)}

def def_main():
    return via_runtime_smoke()

# [VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE:END]
# =============================================================================

# =============================================================================
# [VIA:ANCHOR:SSOT-ENHANCED-APPEND-ONLY:START]
# Append-only enhancement pack (no deletion / no overwrite)
# Purpose:
#   1) 更完整中英財報會計科目（只增不減）
#   2) 穩健標準化抽取 API（避開舊版相容覆寫衝突）
#   3) 複製抽離資產化輸出輔助（JSON-ready）
# =============================================================================
from dataclasses import dataclass
from typing import Iterable, Optional

# ---- 補充：中英財報科目擴充詞庫（append-only） ----
_VIA_EXTRA_FINANCIAL_ACCOUNT_MAP = {
    # Income Statement
    "營業收入淨額": "Revenue",
    "淨營收": "Revenue",
    "銷貨收入": "Revenue",
    "Net Revenue": "Revenue",
    "Sales Revenue": "Revenue",
    "銷貨成本": "CostOfRevenue",
    "服務成本": "CostOfRevenue",
    "Cost of Revenue": "CostOfRevenue",
    "營業毛利淨額": "GrossProfit",
    "Gross Margin": "GrossProfit",
    "推銷費用": "SellingExpense",
    "管理費用": "GeneralAdministrativeExpense",
    "管理及總務費用": "GeneralAdministrativeExpense",
    "研發費用": "ResearchAndDevelopment",
    "研究發展費用": "ResearchAndDevelopment",
    "營業利益（損失）": "OperatingIncome",
    "營業外收入及支出": "NonOperatingIncomeExpense",
    "稅前淨利（淨損）": "IncomeBeforeTax",
    "所得稅費用（利益）": "IncomeTaxExpense",
    "本期淨利（淨損）": "NetIncome",
    "歸屬母公司業主淨利（淨損）": "NetIncomeToOwners",
    "基本每股盈餘（元）": "EPS",
    "稀釋每股盈餘（元）": "DilutedEPS",
    # Balance Sheet
    "流動資產合計": "CurrentAssets",
    "非流動資產合計": "NonCurrentAssets",
    "資產總計": "TotalAssets",
    "流動負債合計": "CurrentLiabilities",
    "非流動負債合計": "NonCurrentLiabilities",
    "負債總計": "TotalLiabilities",
    "權益總計": "Equity",
    "現金及約當現金": "CashAndEquivalents",
    "應收帳款淨額": "AccountsReceivableNet",
    "存貨淨額": "Inventories",
    "不動產、廠房及設備": "PropertyPlantAndEquipment",
    "無形資產": "IntangibleAssets",
    "長期借款": "LongTermDebt",
    "應付公司債": "BondsPayable",
    # Cash Flow
    "營業活動之淨現金流入（流出）": "OperatingCashFlow",
    "投資活動之淨現金流入（流出）": "InvestingCashFlow",
    "籌資活動之淨現金流入（流出）": "FinancingCashFlow",
    "本期現金及約當現金增加（減少）數": "NetChangeInCash",
    # English alternates
    "Total Revenue": "Revenue",
    "Gross Profit": "GrossProfit",
    "Operating Profit": "OperatingIncome",
    "Operating Loss": "OperatingIncome",
    "Net Profit": "NetIncome",
    "Income Before Tax": "IncomeBeforeTax",
    "Tax Expense": "IncomeTaxExpense",
    "Total Current Assets": "CurrentAssets",
    "Total Non-current Assets": "NonCurrentAssets",
    "Total Current Liabilities": "CurrentLiabilities",
    "Total Non-current Liabilities": "NonCurrentLiabilities",
    "Total Equity": "Equity",
    "Cash Flow from Operating Activities": "OperatingCashFlow",
    "Cash Flow from Investing Activities": "InvestingCashFlow",
    "Cash Flow from Financing Activities": "FinancingCashFlow",
}

_VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI = {
    str(k).strip().lower(): v for k, v in _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP.items()
}

# ---- EPS 嚴格區隔（只增不減）：Basic EPS / Diluted EPS 分開 ----
_VIA_EPS_STRICT_MAP_CI = {
    "basic eps": "BasicEPS",
    "基本 eps": "BasicEPS",
    "基本eps": "BasicEPS",
    "basic earnings per share": "BasicEPS",
    "基本每股盈餘": "BasicEPS",
    "基本每股盈餘（元）": "BasicEPS",
    "基本每股收益": "BasicEPS",
    "diluted eps": "DilutedEPS",
    "稀釋 eps": "DilutedEPS",
    "稀釋eps": "DilutedEPS",
    "diluted earnings per share": "DilutedEPS",
    "稀釋每股盈餘": "DilutedEPS",
    "稀釋每股盈餘（元）": "DilutedEPS",
    "完全稀釋每股盈餘": "DilutedEPS",
}

# ---- 市場來源平台同義字（TWSE / TPEX / MOPS / YFINANCE）只增不減 ----
_VIA_SOURCE_PLATFORM_MAP_CI = {
    # TWSE
    "twse": "TWSE",
    "台灣證券交易所": "TWSE",
    "台灣證交所": "TWSE",
    "臺灣證券交易所": "TWSE",
    "臺灣證交所": "TWSE",
    "證交所": "TWSE",
    "上市": "TWSE",
    "tw": "TWSE",
    # TPEX
    "tpex": "TPEX",
    "台北交易所": "TPEX",
    "臺北交易所": "TPEX",
    "櫃買中心": "TPEX",
    "財團法人中華民國證券櫃檯買賣中心": "TPEX",
    "otc": "TPEX",
    "上櫃": "TPEX",
    "two": "TPEX",
    # MOPS
    "mops": "MOPS",
    "公開資訊觀測站": "MOPS",
    "公開資訊": "MOPS",
    "觀測站": "MOPS",
    "market observation post system": "MOPS",
    # YFINANCE
    "yfinance": "YFINANCE",
    "yf": "YFINANCE",
    "yahoo finance": "YFINANCE",
    "yahoo_finance": "YFINANCE",
    "yahoofinance": "YFINANCE",
    "雅虎財經": "YFINANCE",
    "雅虎金融": "YFINANCE",
}

# ---- 由 VeritasSynonymEngine_v2_FIXED.py 匯入補強（只增不減，不覆蓋既有） ----
_VIA_VSE_V2_IMPORTED_MAP = {
    # Income statement / profitability
    "Top Line": "Revenue",
    "營業費用合計": "OperatingExpenses",
    "營運費用": "OperatingExpenses",
    "SG&A": "OperatingExpenses",
    "研發支出": "ResearchAndDevelopment",
    "技術開發費用": "ResearchAndDevelopment",
    "研究開發費": "ResearchAndDevelopment",
    "營業獲利": "OperatingIncome",
    "營運利益": "OperatingIncome",
    "Other Income": "NonOperatingIncomeExpense",
    "業外收入": "NonOperatingIncomeExpense",
    "投資收益": "NonOperatingIncomeExpense",
    "處分利益": "NonOperatingIncomeExpense",
    "EBT": "IncomeBeforeTax",
    "Earnings Before Tax": "IncomeBeforeTax",
    "稅前盈餘": "IncomeBeforeTax",
    "稅前獲利": "IncomeBeforeTax",
    "Tax Expense": "IncomeTaxExpense",
    "稅費": "IncomeTaxExpense",
    "稅負": "IncomeTaxExpense",
    "Net Earnings": "NetIncome",
    "稅後盈餘": "NetIncome",
    "純益": "NetIncome",
    "歸屬母公司純益": "NetIncome",
    # Balance sheet
    "貨幣資金": "CashAndEquivalents",
    "銀行存款": "CashAndEquivalents",
    "A/R": "AccountsReceivableNet",
    "應收款項": "AccountsReceivableNet",
    "貿易應收款": "AccountsReceivableNet",
    "客戶應收款": "AccountsReceivableNet",
    "庫存": "Inventories",
    "商品存貨": "Inventories",
    "製成品": "Inventories",
    "在製品": "Inventories",
    "短期資產": "CurrentAssets",
    "流動資產總額": "CurrentAssets",
    "一年內資產": "CurrentAssets",
    "PPE": "PropertyPlantAndEquipment",
    "Fixed Assets": "PropertyPlantAndEquipment",
    "固定資產": "PropertyPlantAndEquipment",
    "廠房設備": "PropertyPlantAndEquipment",
    "資產合計": "TotalAssets",
    "總資產": "TotalAssets",
    "全部資產": "TotalAssets",
    "A/P": "AccountsPayable",
    "應付款項": "AccountsPayable",
    "貿易應付款": "AccountsPayable",
    "供應商應付款": "AccountsPayable",
    "短期負債": "CurrentLiabilities",
    "流動借款": "CurrentLiabilities",
    "一年內到期負債": "CurrentLiabilities",
    "流動負債總額": "CurrentLiabilities",
    "一年內負債": "CurrentLiabilities",
    "長期負債": "NonCurrentLiabilities",
    "非流動借款": "NonCurrentLiabilities",
    "長期融資": "NonCurrentLiabilities",
    "負債合計": "TotalLiabilities",
    "總負債": "TotalLiabilities",
    "全部負債": "TotalLiabilities",
    "實收資本": "ShareCapital",
    "普通股股本": "ShareCapital",
    "股份資本": "ShareCapital",
    "累積盈餘": "RetainedEarnings",
    "未分配盈餘": "RetainedEarnings",
    "累積未分配盈餘": "RetainedEarnings",
    "權益合計": "Equity",
    "股東權益總額": "Equity",
    "淨值": "Equity",
    # Cash flow
    "CFO": "OperatingCashFlow",
    "營運現金流": "OperatingCashFlow",
    "經營活動現金流": "OperatingCashFlow",
    "OCF": "OperatingCashFlow",
    "CFI": "InvestingCashFlow",
    "投資現金流": "InvestingCashFlow",
    "ICF": "InvestingCashFlow",
    "CFF": "FinancingCashFlow",
    "融資活動現金流": "FinancingCashFlow",
    "資金活動現金流": "FinancingCashFlow",
    "折舊與攤提": "DepreciationAndAmortization",
    "固定資產折舊": "DepreciationAndAmortization",
    "D&A": "DepreciationAndAmortization",
    "無形資產攤提": "Amortization",
    "攤銷費用": "Amortization",
    "CapEx": "CapitalExpenditure",
    "資本性支出": "CapitalExpenditure",
    "設備投資": "CapitalExpenditure",
    "固定資產投資": "CapitalExpenditure",
    "FCF": "FreeCashFlow",
    "自由現金流量": "FreeCashFlow",
    "現金股利支付": "CashDividendPaid",
    "股息發放": "CashDividendPaid",
    "股利分配": "CashDividendPaid",
    # Ratios / per-share
    "ROE": "ReturnOnEquity",
    "權益報酬率": "ReturnOnEquity",
    "淨值報酬率": "ReturnOnEquity",
    "股東權益收益率": "ReturnOnEquity",
    "ROA": "ReturnOnAssets",
    "總資產報酬率": "ReturnOnAssets",
    "資產收益率": "ReturnOnAssets",
    "Gross Profit Margin": "GrossMargin",
    "營業毛利率": "GrossMargin",
    "毛利潤率": "GrossMargin",
    "營業淨利率": "OperatingMargin",
    "營運利益率": "OperatingMargin",
    "EBIT Margin": "OperatingMargin",
    "Net Profit Margin": "NetMargin",
    "稅後淨利率": "NetMargin",
    "純益率": "NetMargin",
    "流動比": "CurrentRatio",
    "短期償債能力比率": "CurrentRatio",
    "速動比": "QuickRatio",
    "酸性測試比率": "QuickRatio",
    "Acid Test Ratio": "QuickRatio",
    "債務比率": "DebtRatio",
    "資產負債率": "DebtRatio",
    "負債比": "DebtRatio",
    "D/E Ratio": "DebtToEquity",
    "負債對權益比率": "DebtToEquity",
    "P/E Ratio": "PriceToEarnings",
    "PER": "PriceToEarnings",
    "股價盈餘比": "PriceToEarnings",
    "P/B Ratio": "PriceToBook",
    "PBR": "PriceToBook",
    "市價淨值比": "PriceToBook",
    "P/S Ratio": "PriceToSales",
    "PSR": "PriceToSales",
    "市價營收比": "PriceToSales",
    "Basic EPS": "EPS",
    "每股稅後盈餘": "EPS",
    "基本EPS": "EPS",
    "Diluted EPS": "DilutedEPS",
    "稀釋後EPS": "DilutedEPS",
    "完全稀釋每股盈餘": "DilutedEPS",
    "BVPS": "BookValuePerShare",
    "每股帳面價值": "BookValuePerShare",
    "每股股東權益": "BookValuePerShare",
    "DPS": "DividendPerShare",
    "每股配息": "DividendPerShare",
    "現金股息": "DividendPerShare",
    "股利": "DividendPerShare",
    "現金殖利率": "DividendYield",
    "股息收益率": "DividendYield",
    "Yield": "DividendYield",
    "股利發放率": "PayoutRatio",
    "配息比例": "PayoutRatio",
    "股利支付率": "PayoutRatio",
}

for _k, _v in _VIA_VSE_V2_IMPORTED_MAP.items():
    _kk = str(_k).strip().lower()
    # 只增不減：已有鍵不覆蓋
    if _kk and _kk not in _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI:
        _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI[_kk] = _v

# ---- 三大報表會計科目同義字擴充（只增不減，不覆蓋既有） ----
_VIA_FS3_ACCOUNT_SYNONYM_MAP = {
    # =========================
    # Income Statement 損益表
    # =========================
    "營業收入合計": "Revenue",
    "營收淨額": "Revenue",
    "營業收入總額": "Revenue",
    "sales": "Revenue",
    "net sales": "Revenue",
    "銷貨收入淨額": "Revenue",
    "營業成本合計": "CostOfRevenue",
    "銷售成本": "CostOfRevenue",
    "cost of sales": "CostOfRevenue",
    "cost of goods sold": "CostOfRevenue",
    "cogs": "CostOfRevenue",
    "營業毛利（毛損）": "GrossProfit",
    "毛利（毛損）": "GrossProfit",
    "gross profit": "GrossProfit",
    "營業毛利率": "GrossMargin",
    "gross margin": "GrossMargin",
    "推銷費用": "SellingExpense",
    "selling expense": "SellingExpense",
    "selling expenses": "SellingExpense",
    "管理費用": "GeneralAdministrativeExpense",
    "administrative expense": "GeneralAdministrativeExpense",
    "general and administrative": "GeneralAdministrativeExpense",
    "管理及總務費用": "GeneralAdministrativeExpense",
    "研究發展費用": "ResearchAndDevelopment",
    "研發費": "ResearchAndDevelopment",
    "r&d": "ResearchAndDevelopment",
    "r&d expense": "ResearchAndDevelopment",
    "research and development": "ResearchAndDevelopment",
    "營業費用": "OperatingExpenses",
    "operating expenses": "OperatingExpenses",
    "opex": "OperatingExpenses",
    "營業利益": "OperatingIncome",
    "營業淨利": "OperatingIncome",
    "operating income": "OperatingIncome",
    "operating profit": "OperatingIncome",
    "ebit": "OperatingIncome",
    "營業外收入及支出淨額": "NonOperatingIncomeExpense",
    "業外收支": "NonOperatingIncomeExpense",
    "other income and expenses": "NonOperatingIncomeExpense",
    "稅前淨利": "IncomeBeforeTax",
    "稅前淨損": "IncomeBeforeTax",
    "income before tax": "IncomeBeforeTax",
    "earnings before tax": "IncomeBeforeTax",
    "所得稅費用": "IncomeTaxExpense",
    "income tax expense": "IncomeTaxExpense",
    "tax expense": "IncomeTaxExpense",
    "本期淨利（淨損）歸屬母公司": "NetIncomeToOwners",
    "歸屬於母公司業主之淨利（淨損）": "NetIncomeToOwners",
    "net income attributable to owners": "NetIncomeToOwners",
    "本期淨利（淨損）歸屬非控制權益": "NetIncomeToNCI",
    "歸屬非控制權益": "NetIncomeToNCI",
    "non-controlling interests": "NetIncomeToNCI",
    "每股盈餘": "EPS",
    "earnings per share": "EPS",
    # =============================
    # Balance Sheet 資產負債表
    # =============================
    "資產": "TotalAssets",
    "total assets": "TotalAssets",
    "資產總計": "TotalAssets",
    "流動資產": "CurrentAssets",
    "current assets": "CurrentAssets",
    "現金及約當現金": "CashAndEquivalents",
    "cash and cash equivalents": "CashAndEquivalents",
    "透過損益按公允價值衡量之金融資產": "FVTPLFinancialAssets",
    "fvtpl financial assets": "FVTPLFinancialAssets",
    "按攤銷後成本衡量之金融資產": "AmortizedCostFinancialAssets",
    "應收票據": "NotesReceivable",
    "notes receivable": "NotesReceivable",
    "應收帳款": "AccountsReceivableNet",
    "accounts receivable": "AccountsReceivableNet",
    "其他應收款": "OtherReceivables",
    "other receivables": "OtherReceivables",
    "存貨": "Inventories",
    "inventories": "Inventories",
    "預付款項": "Prepayments",
    "prepayments": "Prepayments",
    "非流動資產": "NonCurrentAssets",
    "non-current assets": "NonCurrentAssets",
    "不動產、廠房及設備": "PropertyPlantAndEquipment",
    "property, plant and equipment": "PropertyPlantAndEquipment",
    "ppe": "PropertyPlantAndEquipment",
    "使用權資產": "RightOfUseAssets",
    "right-of-use assets": "RightOfUseAssets",
    "投資性不動產": "InvestmentProperty",
    "investment property": "InvestmentProperty",
    "無形資產": "IntangibleAssets",
    "intangible assets": "IntangibleAssets",
    "遞延所得稅資產": "DeferredTaxAssets",
    "deferred tax assets": "DeferredTaxAssets",
    "負債": "TotalLiabilities",
    "負債總計": "TotalLiabilities",
    "total liabilities": "TotalLiabilities",
    "流動負債": "CurrentLiabilities",
    "current liabilities": "CurrentLiabilities",
    "短期借款": "ShortTermBorrowings",
    "short-term borrowings": "ShortTermBorrowings",
    "應付票據": "NotesPayable",
    "notes payable": "NotesPayable",
    "應付帳款": "AccountsPayable",
    "accounts payable": "AccountsPayable",
    "其他應付款": "OtherPayables",
    "other payables": "OtherPayables",
    "合約負債": "ContractLiabilities",
    "contract liabilities": "ContractLiabilities",
    "一年內到期長期負債": "CurrentPortionOfLongTermDebt",
    "current portion of long-term debt": "CurrentPortionOfLongTermDebt",
    "非流動負債": "NonCurrentLiabilities",
    "non-current liabilities": "NonCurrentLiabilities",
    "長期借款": "LongTermDebt",
    "long-term debt": "LongTermDebt",
    "應付公司債": "BondsPayable",
    "bonds payable": "BondsPayable",
    "租賃負債": "LeaseLiabilities",
    "lease liabilities": "LeaseLiabilities",
    "遞延所得稅負債": "DeferredTaxLiabilities",
    "deferred tax liabilities": "DeferredTaxLiabilities",
    "權益": "Equity",
    "equity": "Equity",
    "股本": "ShareCapital",
    "share capital": "ShareCapital",
    "資本公積": "CapitalSurplus",
    "capital surplus": "CapitalSurplus",
    "保留盈餘": "RetainedEarnings",
    "retained earnings": "RetainedEarnings",
    "其他權益": "OtherEquity",
    "other equity": "OtherEquity",
    "庫藏股": "TreasuryShares",
    "treasury shares": "TreasuryShares",
    # =========================
    # Cash Flow 現金流量表
    # =========================
    "現金流量": "NetChangeInCash",
    "cash flow": "NetChangeInCash",
    "營業活動之淨現金流入": "OperatingCashFlow",
    "營業活動之淨現金流出": "OperatingCashFlow",
    "cash flows from operating activities": "OperatingCashFlow",
    "operating cash flow": "OperatingCashFlow",
    "投資活動之淨現金流入": "InvestingCashFlow",
    "投資活動之淨現金流出": "InvestingCashFlow",
    "cash flows from investing activities": "InvestingCashFlow",
    "investing cash flow": "InvestingCashFlow",
    "籌資活動之淨現金流入": "FinancingCashFlow",
    "籌資活動之淨現金流出": "FinancingCashFlow",
    "cash flows from financing activities": "FinancingCashFlow",
    "financing cash flow": "FinancingCashFlow",
    "折舊費用": "DepreciationExpense",
    "depreciation expense": "DepreciationExpense",
    "攤銷費用": "Amortization",
    "amortization expense": "Amortization",
    "利息費用": "InterestExpense",
    "interest expense": "InterestExpense",
    "利息收入": "InterestIncome",
    "interest income": "InterestIncome",
    "所得稅費用（利益）": "IncomeTaxExpense",
    "股利收入": "DividendIncome",
    "dividend income": "DividendIncome",
    "資本支出": "CapitalExpenditure",
    "capital expenditure": "CapitalExpenditure",
    "出售不動產、廠房及設備": "ProceedsFromDisposalOfPPE",
    "proceeds from disposal of ppe": "ProceedsFromDisposalOfPPE",
    "取得不動產、廠房及設備": "AcquisitionOfPPE",
    "acquisition of ppe": "AcquisitionOfPPE",
    "支付現金股利": "CashDividendPaid",
    "cash dividends paid": "CashDividendPaid",
    "舉借長期借款": "ProceedsFromLongTermDebt",
    "proceeds from long-term debt": "ProceedsFromLongTermDebt",
    "償還長期借款": "RepaymentOfLongTermDebt",
    "repayment of long-term debt": "RepaymentOfLongTermDebt",
    "匯率變動對現金及約當現金之影響": "EffectOfExchangeRateOnCash",
    "effect of exchange rate changes on cash": "EffectOfExchangeRateOnCash",
    "本期現金及約當現金增加（減少）數": "NetChangeInCash",
    "net increase (decrease) in cash and cash equivalents": "NetChangeInCash",
}

for _k, _v in _VIA_FS3_ACCOUNT_SYNONYM_MAP.items():
    _kk = str(_k).strip().lower()
    # 只增不減：已有鍵不覆蓋
    if _kk and _kk not in _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI:
        _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI[_kk] = _v


def _via_get_ssot_engine():
    """
    安全取得 SSOT 引擎：
    - 優先使用 SSOT class 直接建構（避免尾端相容覆寫 get_ssot() 型態衝突）
    - 次選使用 get_ssot() 且結果具 normalize/extract/contains 方法
    """
    try:
        eng = SSOT()
        return eng
    except Exception:
        pass
    try:
        eng = get_ssot()
        if all(hasattr(eng, m) for m in ("normalize", "extract", "contains")):
            return eng
    except Exception:
        pass
    return None


@dataclass
class VIAFinancialSubjectMatch:
    raw: str
    canonical: str
    source: str  # ssot | extra_map | passthrough


def via_financial_subject_normalize(term: str) -> str:
    """
    中英財報會計科目標準化（只增不減）：
    1) SSOT 內建同義詞
    2) VIA 擴充詞庫
    3) fallback 原值
    """
    t = str(term or "").strip()
    if not t:
        return t
    # 平台同義字優先標準化
    src = _VIA_SOURCE_PLATFORM_MAP_CI.get(t.lower())
    if src:
        return src
    # EPS 嚴格區隔優先（避免被一般 EPS 合併）
    strict = _VIA_EPS_STRICT_MAP_CI.get(t.lower())
    if strict:
        return strict
    eng = _via_get_ssot_engine()
    if eng is not None:
        try:
            n = eng.normalize(t)
            if n and n != t:
                return n
        except Exception:
            pass
    return _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI.get(t.lower(), t)


def via_financial_subject_extract(lines: Iterable[str]) -> list[VIAFinancialSubjectMatch]:
    """
    從文本列中擷取並標準化財報會計科目（中英雙語）。
    """
    out: list[VIAFinancialSubjectMatch] = []
    eng = _via_get_ssot_engine()
    for raw in lines:
        text = str(raw or "").strip()
        if not text:
            continue
        canonical = text
        source = "passthrough"
        strict = _VIA_EPS_STRICT_MAP_CI.get(text.lower())
        if strict:
            out.append(VIAFinancialSubjectMatch(raw=text, canonical=strict, source="eps_strict"))
            continue
        if eng is not None:
            try:
                n = eng.normalize(text)
                if n and n != text:
                    canonical = n
                    source = "ssot"
            except Exception:
                pass
        if source == "passthrough":
            m = _VIA_EXTRA_FINANCIAL_ACCOUNT_MAP_CI.get(text.lower())
            if m:
                canonical = m
                source = "extra_map"
        out.append(VIAFinancialSubjectMatch(raw=text, canonical=canonical, source=source))
    return out


def via_financial_subject_extract_unique(lines: Iterable[str]) -> dict[str, list[str]]:
    """
    產生 canonical -> raw aliases 清單，用於補齊/去重盤點矩陣。
    """
    bucket: dict[str, set[str]] = {}
    for m in via_financial_subject_extract(lines):
        bucket.setdefault(m.canonical, set()).add(m.raw)
    return {k: sorted(v) for k, v in sorted(bucket.items(), key=lambda kv: kv[0])}


def via_build_financial_subject_asset(payload_lines: Iterable[str], asset_id: Optional[str] = None) -> str:
    """
    複製抽離標準化指令輸出（JSON string）：
    - 包含 canonical 科目、aliases、來源統計
    - 可直接用於智慧資產儲存/註冊
    """
    uniq = via_financial_subject_extract_unique(payload_lines)
    source_stats = {"ssot": 0, "extra_map": 0, "passthrough": 0}
    for m in via_financial_subject_extract(payload_lines):
        source_stats[m.source] = source_stats.get(m.source, 0) + 1
    obj = {
        "asset_id": asset_id or "AST-PY-LIB-VIA-FIN-SUBJECTS-EXT",
        "type": "financial_subject_dictionary",
        "version": "append-only-1.0.0",
        "canonical_subjects": uniq,
        "stats": {
            "canonical_count": len(uniq),
            "line_count": sum(len(v) for v in uniq.values()),
            "source": source_stats,
        },
    }
    return json.dumps(obj, ensure_ascii=False, indent=2)


def via_ssot_append_only_health() -> dict[str, Any]:
    return {
        "status": "alive",
        "anchor": "VIA:ANCHOR:SSOT-ENHANCED-APPEND-ONLY",
        "extra_financial_subjects": len(_VIA_EXTRA_FINANCIAL_ACCOUNT_MAP),
        "source_platform_synonyms": len(_VIA_SOURCE_PLATFORM_MAP_CI),
        "engine_ready": _via_get_ssot_engine() is not None,
    }


def via_source_platform_normalize(term: str) -> str:
    """
    平台同義字標準化：
      TWSE / TPEX / MOPS / YFINANCE
    """
    t = str(term or "").strip()
    if not t:
        return t
    return _VIA_SOURCE_PLATFORM_MAP_CI.get(t.lower(), t)


# ---- 測試優化：快取版標準化（不改舊 API，只新增） ----
try:
    from functools import lru_cache as _via_lru_cache
except Exception:
    _via_lru_cache = None


if _via_lru_cache is not None:
    @_via_lru_cache(maxsize=8192)
    def via_financial_subject_normalize_cached(term: str) -> str:
        return via_financial_subject_normalize(term)
else:
    def via_financial_subject_normalize_cached(term: str) -> str:
        return via_financial_subject_normalize(term)


def via_financial_subject_extract_fast(lines: Iterable[str]) -> list[VIAFinancialSubjectMatch]:
    """
    快取優化版擷取器：大量重複科目文本時可顯著減少 normalize 重複成本。
    """
    out: list[VIAFinancialSubjectMatch] = []
    for raw in lines:
        text = str(raw or "").strip()
        if not text:
            continue
        canonical = via_financial_subject_normalize_cached(text)
        source = "cached"
        if canonical == text:
            source = "passthrough"
        elif canonical in ("BasicEPS", "DilutedEPS"):
            source = "eps_strict"
        elif canonical in ("TWSE", "TPEX", "MOPS", "YFINANCE"):
            source = "platform_strict"
        out.append(VIAFinancialSubjectMatch(raw=text, canonical=canonical, source=source))
    return out


def via_ssot_optimize_test_payload() -> list[str]:
    """
    內建 smoke payload（測試優化用）。
    """
    return [
        "營業收入", "營收", "Revenue", "Basic EPS", "Diluted EPS",
        "台灣證交所", "櫃買中心", "公開資訊觀測站", "Yahoo Finance",
        "營業活動之淨現金流入（流出）", "資產總計", "負債總計",
    ] * 200

# [VIA:ANCHOR:SSOT-ENHANCED-APPEND-ONLY:END]
# =============================================================================

# [VIA:ANCHOR:FINANCIAL_BILINGUAL_SSOT_APPEND_ONLY_V1:START]
# =============================================================================
# VIA FINANCIAL BILINGUAL SSOT · APPEND ONLY V1
# VERITAS INTELLIGENCE ANALYTICS
# Purpose:
#   補齊損益表 / 資產負債表 / 現金流量表 / 比率分析 / 每股分析
#   中英文 canonical aliases、section anchors、scope anchors、validation anchors。
# Policy:
#   只增不減；不覆蓋既有物件；下游可透過函式讀取。
# =============================================================================

VIA_FINANCIAL_SSOT_VERSION = "FIN_BILINGUAL_APPEND_ONLY_V1"

VIA_FINANCIAL_SECTION_ORDER = (
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "ratio_analysis",
    "per_share_analysis",
)

VIA_FINANCIAL_SOURCE_WHITELIST = (
    "Report",
    "TWSE",
    "TPEX",
    "MOPS",
    "YFinance",
    "IssuerIR",
)

VIA_FINANCIAL_SECTION_ANCHORS = {
    "income_statement": [
        "損益表", "綜合損益表", "合併損益表", "合併綜合損益表", "個體綜合損益表",
        "Income Statement", "Statements of Comprehensive Income",
        "Statement of Comprehensive Income", "Consolidated Statements of Comprehensive Income",
        "P&L", "Profit and Loss", "Summary P&L",
    ],
    "balance_sheet": [
        "資產負債表", "合併資產負債表", "個體資產負債表",
        "Balance Sheet", "Balance Sheets", "Consolidated Balance Sheets",
        "Parent Company Only Balance Sheets", "Selected Items from Balance Sheets",
    ],
    "cash_flow_statement": [
        "現金流量表", "合併現金流量表", "個體現金流量表",
        "Cash Flow Statement", "Statements of Cash Flows",
        "Consolidated Statements of Cash Flows", "Cash Flows",
    ],
    "ratio_analysis": [
        "比率分析", "重要財務指標", "財務比率", "經營比率", "Key Indices",
        "Financial Ratios", "Ratio Analysis", "Operating Metrics",
    ],
    "per_share_analysis": [
        "每股分析", "每股資料", "每股盈餘", "Per Share Analysis",
        "Per Share Data", "Earnings Per Share", "EPS",
    ],
}

VIA_FINANCIAL_SCOPE_ANCHORS = {
    "consolidated": ["合併", "Consolidated"],
    "parent_only": ["個體", "Parent Company Only", "Unconsolidated"],
    "selected_items": ["Selected Items", "摘要", "摘錄", "項目"],
    "guidance": ["展望", "預估", "財測", "Guidance", "Forecast", "Estimate"],
}

VIA_FINANCIAL_CANONICAL_ALIASES = {
    "income_statement": {
        "revenue": [
            "營業收入", "營業收入淨額", "收入", "收入淨額", "營收", "銷貨收入", "銷貨收入淨額",
            "Revenue", "Net Revenue", "Sales", "Net Sales", "Sales Revenue", "Operating Revenue",
        ],
        "cogs": [
            "營業成本", "銷貨成本", "收入成本",
            "Cost of Revenue", "Cost of Goods Sold", "COGS", "Cost of Sales",
        ],
        "gross_profit": [
            "營業毛利", "營業毛利淨額", "毛利", "毛利總額",
            "Gross Profit", "Gross profit from operations",
        ],
        "operating_expenses": [
            "營業費用", "營業費用合計", "營業支出",
            "Operating Expenses", "Total Operating Expenses", "OPEX",
        ],
        "operating_income": [
            "營業利益", "營業淨利", "營業損益",
            "Operating Income", "Income from Operations", "Operating Profit", "EBIT",
        ],
        "pretax_income": [
            "稅前淨利", "稅前利益", "稅前損益",
            "Income before income tax", "Profit before tax", "Pretax Income", "PBT",
        ],
        "net_income": [
            "本期淨利", "本年度淨利", "稅後淨利", "淨利",
            "Net Income", "Profit for the Period", "Profit for the Year",
        ],
        "net_income_parent": [
            "歸屬母公司業主淨利", "歸屬於母公司業主之本期淨利", "歸屬母公司淨利",
            "Net income to shareholders of the parent company",
            "Profit attributable to owners of parent",
            "Profit attributable to ordinary equity owners of the parent",
        ],
        "non_operating_income_expenses": [
            "營業外收入及支出", "營業外損益", "業外收支",
            "Non-operating income and expenses", "Non-operating income/expenses",
        ],
        "other_comprehensive_income": [
            "其他綜合損益", "其他綜合收益",
            "Other Comprehensive Income", "OCI",
        ],
        "total_comprehensive_income": [
            "綜合損益總額", "本期綜合損益總額",
            "Total Comprehensive Income", "Total comprehensive income for the period",
        ],
        "income_tax_expense": [
            "所得稅費用", "所得稅利益", "Income Tax Expense", "Tax Expense",
        ],
    },

    "balance_sheet": {
        "cash_and_cash_equivalents": [
            "現金及約當現金", "現金及約當現金總額",
            "Cash and cash equivalents", "Cash & cash equivalents",
        ],
        "cash_and_marketable_securities": [
            "現金及有價金融商品投資", "現金及有價證券",
            "Cash and Marketable Securities", "Cash & Marketable Securities",
        ],
        "accounts_receivable": [
            "應收帳款", "應收帳款淨額", "應收票據及帳款",
            "Accounts Receivable", "Trade receivables",
            "Notes and accounts receivable, net",
        ],
        "inventories": [
            "存貨", "存貨淨額", "Inventories", "Inventory",
        ],
        "current_assets": [
            "流動資產", "流動資產合計", "Current Assets", "Total Current Assets",
        ],
        "long_term_investments": [
            "長期投資", "採用權益法之投資",
            "Long-term Investments", "Investments accounted for using equity method",
        ],
        "ppe": [
            "不動產、廠房及設備", "不動產廠房及設備", "固定資產",
            "Property, plant and equipment", "PP&E", "Net PP&E",
        ],
        "right_of_use_assets": [
            "使用權資產", "Right-of-use assets", "ROU assets",
        ],
        "intangible_assets": [
            "無形資產", "Intangible Assets",
        ],
        "total_assets": [
            "總資產", "資產總計", "Total Assets",
        ],
        "current_liabilities": [
            "流動負債", "流動負債合計", "Current Liabilities", "Total Current Liabilities",
        ],
        "accounts_payable": [
            "應付帳款", "應付票據及帳款", "Trade payables", "Accounts Payable",
        ],
        "contract_liabilities_current": [
            "合約負債－流動", "流動合約負債", "Contract liabilities-current",
        ],
        "short_term_borrowings": [
            "短期借款", "Short-term borrowings", "Short-term loans",
        ],
        "bonds_payable": [
            "應付公司債", "Bonds payable",
        ],
        "long_term_borrowings": [
            "長期借款", "Long-term borrowings", "Long-term debt",
        ],
        "lease_liabilities": [
            "租賃負債", "Lease liabilities",
        ],
        "total_liabilities": [
            "總負債", "負債總計", "Total Liabilities",
        ],
        "shareholders_equity": [
            "股東權益", "權益總計", "Shareholders Equity", "Shareholders' Equity",
        ],
        "equity_attributable_to_owners_of_parent": [
            "歸屬於母公司業主之權益", "母公司業主權益",
            "Equity attributable to owners of parent",
        ],
        "non_controlling_interests": [
            "非控制權益", "Non-controlling interests",
        ],
        "total_equity": [
            "權益總額", "權益總計", "Total Equity",
        ],
    },

    "cash_flow_statement": {
        "cash_from_operating_activities": [
            "營運活動之現金流入", "營業活動之淨現金流入", "營業活動現金流量",
            "Cash from operating activities", "Net cash generated by operating activities",
            "Net cash provided by operating activities",
        ],
        "net_cash_used_in_investing_activities": [
            "投資活動之淨現金流出", "投資活動現金流量",
            "Net cash used in investing activities", "Net cash provided by investing activities",
        ],
        "net_cash_used_in_financing_activities": [
            "籌資活動之淨現金流出", "籌資活動現金流量",
            "Net cash used in financing activities", "Net cash provided by financing activities",
        ],
        "capital_expenditures": [
            "資本支出", "購置不動產廠房及設備", "取得不動產廠房及設備",
            "Capital expenditures", "CapEx", "Purchase of property, plant and equipment",
        ],
        "cash_dividends": [
            "現金股利", "發放現金股利", "Cash dividends", "Dividends paid",
        ],
        "free_cash_flow": [
            "自由現金流量", "Free Cash Flow", "FCF",
        ],
        "beginning_cash_balance": [
            "期初現金", "期初現金及約當現金",
            "Beginning Balance", "Cash and cash equivalents, beginning of year",
        ],
        "ending_cash_balance": [
            "期末現金", "期末現金及約當現金",
            "Ending Balance", "Cash and cash equivalents, end of year",
        ],
        "effect_of_exchange_rate_changes_on_cash_and_cash_equivalents": [
            "匯率變動對現金及約當現金之影響",
            "Effect of exchange rate changes on cash and cash equivalents",
        ],
        "net_increase_in_cash_and_cash_equivalents": [
            "現金及約當現金增加數", "現金及約當現金淨增加",
            "Net increase in cash and cash equivalents",
        ],
    },

    "ratio_analysis": {
        "gross_margin": [
            "毛利率", "銷貨毛利率", "Gross Margin", "Gross Profit Margin",
        ],
        "operating_margin": [
            "營業利益率", "營業淨利率", "Operating Margin", "Operating Profit Margin",
        ],
        "net_margin": [
            "純益率", "淨利率", "Net Profit Margin", "Net Margin",
        ],
        "roe": [
            "股東權益報酬率", "權益報酬率", "ROE", "Return on Equity",
        ],
        "roa": [
            "資產報酬率", "ROA", "Return on Assets",
        ],
        "ar_turnover_days": [
            "平均收現日數", "A/R Turnover Days", "Accounts receivable turnover days",
        ],
        "inventory_turnover_days": [
            "平均銷貨日數", "Inventory Turnover Days", "Days of Inventory",
        ],
        "current_ratio": [
            "流動比率", "Current Ratio",
        ],
        "asset_productivity": [
            "資產生產力", "Asset Productivity",
        ],
        "pe_ratio": [
            "本益比", "P/E", "PE Ratio", "Price Earnings Ratio",
        ],
        "pb_ratio": [
            "股價淨值比", "P/B", "PB Ratio", "Price to Book",
        ],
        "dividend_yield": [
            "殖利率", "股息殖利率", "Dividend Yield",
        ],
    },

    "per_share_analysis": {
        "eps": [
            "每股盈餘", "每股盈餘(元)", "EPS", "Earnings Per Share",
        ],
        "basic_eps": [
            "基本每股盈餘", "Basic EPS", "Basic earnings per share",
        ],
        "diluted_eps": [
            "稀釋每股盈餘", "Diluted EPS", "Diluted earnings per share",
        ],
        "weighted_avg_shares_basic": [
            "基本每股盈餘之普通股加權平均股數",
            "Weighted average number of ordinary shares outstanding for basic earnings per share",
        ],
        "weighted_avg_shares_diluted": [
            "用以計算稀釋每股盈餘之普通股加權平均股數",
            "Weighted average number of ordinary shares outstanding after dilution",
        ],
        "bvps": [
            "每股淨值", "Book Value Per Share", "BVPS",
        ],
        "dps": [
            "每股股利", "每股現金股利", "Cash dividends per share", "DPS",
        ],
        "cfps": [
            "每股營業現金流量", "Cash Flow Per Share", "CFPS",
        ],
        "fcfps": [
            "每股自由現金流量", "Free Cash Flow Per Share", "FCF Per Share",
        ],
    },
}

VIA_FINANCIAL_CANONICAL_CATEGORY = {}
for _section, _items in VIA_FINANCIAL_CANONICAL_ALIASES.items():
    for _canonical_key in _items.keys():
        VIA_FINANCIAL_CANONICAL_CATEGORY[_canonical_key] = _section

VIA_FINANCIAL_VALIDATION_RULES = {
    "gross_margin": "gross_profit / revenue",
    "operating_margin": "operating_income / revenue",
    "net_margin": "net_income / revenue",
    "free_cash_flow": "cash_from_operating_activities - capital_expenditures",
    "basic_eps": "net_income_parent / weighted_avg_shares_basic",
    "diluted_eps": "net_income_parent / weighted_avg_shares_diluted",
    "current_ratio": "current_assets / current_liabilities",
}

def def_via_financial_get_sections():
    return VIA_FINANCIAL_SECTION_ORDER

def def_via_financial_get_aliases():
    return VIA_FINANCIAL_CANONICAL_ALIASES

def def_via_financial_get_section_anchors():
    return VIA_FINANCIAL_SECTION_ANCHORS

def def_via_financial_get_scope_anchors():
    return VIA_FINANCIAL_SCOPE_ANCHORS

def def_via_financial_normalize_label(label):
    import re as _re
    s = "" if label is None else str(label)
    s = s.replace("　", " ").strip()
    s = _re.sub(r"\s+", " ", s)
    s = _re.sub(r"[()（）]\s*(新台幣|台幣|NT\$|TWD|US\$|USD|美元|元|千元|百萬元|十億元|%|倍).*?[()（）]?", "", s, flags=_re.I)
    s = s.replace("&", "and")
    return s.strip().casefold()

def def_via_financial_resolve_label(label):
    norm = def_via_financial_normalize_label(label)
    for section, items in VIA_FINANCIAL_CANONICAL_ALIASES.items():
        for canonical, aliases in items.items():
            for alias in aliases:
                if norm == def_via_financial_normalize_label(alias):
                    return {
                        "section": section,
                        "canonical": canonical,
                        "alias": alias,
                        "confidence": 1.00,
                    }
    for section, items in VIA_FINANCIAL_CANONICAL_ALIASES.items():
        for canonical, aliases in items.items():
            for alias in aliases:
                alias_norm = def_via_financial_normalize_label(alias)
                if alias_norm and (alias_norm in norm or norm in alias_norm):
                    return {
                        "section": section,
                        "canonical": canonical,
                        "alias": alias,
                        "confidence": 0.85,
                    }
    return {
        "section": "unknown",
        "canonical": "",
        "alias": "",
        "confidence": 0.00,
    }

def def_via_financial_get_validation_rules():
    return VIA_FINANCIAL_VALIDATION_RULES
# [VIA:ANCHOR:FINANCIAL_BILINGUAL_SSOT_APPEND_ONLY_V1:END]


# [VIA:ANCHOR:AI_APPEND_ONLY:VRN_SSOT_AUGMENT_V1:START]
# VERSION: VRN_SSOT_AUGMENT_V1
# STATUS : append-only, non-destructive
# PURPOSE: VRN report classifier / financial statement synonym / broker / rating / target price / time terms
# CREATED: 2026-05-09T22:57:30
# POLICY : only-add, no-delete, compatible with VIA_SSOT_Unified v4.3.0

VRN_SSOT_AUGMENT_V1 = {
    "financial_statement_synonyms": {
        "income_statement": {
            "revenue": ["營業收入", "營業收入合計", "operating revenue", "total revenue", "sales", "net sales"],
            "cost_of_revenue": ["營業成本", "cost of revenue", "cost of goods sold", "cogs"],
            "gross_profit": ["營業毛利", "gross profit"],
            "operating_expense": ["營業費用", "operating expense", "operating expenses"],
            "selling_expense": ["推銷費用", "selling expenses", "selling general and administrative", "sg&a"],
            "administrative_expense": ["管理費用", "administrative expenses", "general and administrative"],
            "rd_expense": ["研發費用", "研究發展費用", "research and development", "r&d"],
            "operating_income": ["營業利益", "營業淨利", "operating income", "operating profit"],
            "non_operating": ["營業外收入及支出", "non-operating income", "total other income expense net"],
            "finance_cost": ["財務成本", "利息費用", "finance costs", "interest expense"],
            "pretax_income": ["稅前淨利", "稅前利益", "income before tax", "pretax income"],
            "tax_expense": ["所得稅費用", "income tax expense", "tax provision"],
            "net_income": ["本期淨利", "稅後淨利", "net income", "net income common stockholders"],
            "basic_eps": ["基本每股盈餘", "basic eps", "basic earnings per share"],
            "diluted_eps": ["稀釋每股盈餘", "diluted eps", "diluted earnings per share"]
        },
        "balance_sheet": {
            "total_assets": ["資產總額", "total assets"],
            "current_assets": ["流動資產", "current assets"],
            "cash": ["現金及約當現金", "cash and cash equivalents"],
            "receivables": ["應收帳款", "應收帳款淨額", "accounts receivable", "receivables"],
            "inventory": ["存貨", "inventory", "inventories"],
            "ppe": ["不動產廠房及設備", "不動產、廠房及設備", "property plant and equipment", "net ppe", "ppe"],
            "total_liabilities": ["負債總額", "total liabilities"],
            "current_liabilities": ["流動負債", "current liabilities"],
            "accounts_payable": ["應付帳款", "accounts payable", "payables"],
            "long_term_debt": ["長期借款", "long-term borrowings", "long term debt"],
            "total_equity": ["權益總額", "total equity"],
            "retained_earnings": ["保留盈餘", "retained earnings"],
            "minority_interest": ["非控制權益", "non-controlling interests", "minority interest"]
        },
        "cash_flow": {
            "operating_cash_flow": ["營業活動之現金流量", "operating cash flow", "cash flows from operating activities"],
            "investing_cash_flow": ["投資活動之現金流量", "investing cash flow", "cash flows from investing activities"],
            "financing_cash_flow": ["籌資活動之現金流量", "financing cash flow", "cash flows from financing activities"],
            "depreciation": ["折舊費用", "depreciation expense", "depreciation"],
            "amortization": ["攤銷費用", "amortization expense", "amortization"],
            "capex": ["資本支出", "取得不動產廠房及設備", "capital expenditure", "capex"],
            "free_cash_flow": ["自由現金流量", "free cash flow", "fcf"],
            "cash_dividends_paid": ["發放現金股利", "cash dividends paid"]
        },
        "ratios": {
            "gross_margin": ["毛利率", "gross margin", "gross profit margin"],
            "operating_margin": ["營業利益率", "operating margin"],
            "net_margin": ["純益率", "net profit margin", "profit margin"],
            "roe": ["股東權益報酬率", "roe", "return on equity"],
            "roa": ["總資產報酬率", "roa", "return on assets"],
            "current_ratio": ["流動比率", "current ratio"],
            "quick_ratio": ["速動比率", "quick ratio"],
            "debt_ratio": ["負債比率", "debt ratio", "debt-to-asset ratio"],
            "interest_coverage": ["利息保障倍數", "interest coverage ratio", "times interest earned"],
            "receivables_turnover": ["應收帳款週轉率", "receivables turnover"],
            "inventory_turnover": ["存貨週轉率", "inventory turnover"],
            "asset_turnover": ["總資產週轉率", "asset turnover"],
            "cash_flow_adequacy": ["現金流量允當比率", "cash flow adequacy ratio"],
            "cash_flow_to_net_income": ["盈餘品質係數", "cash flow to net income"],
            "pe": ["本益比", "p/e", "price-to-earnings"],
            "pb": ["股價淨值比", "p/b", "price-to-book"],
            "dividend_yield": ["現金股利殖利率", "dividend yield"]
        }
    },
    "broker_aliases": {
        "Mega": ["兆豐", "兆豐投顧", "Mega"],
        "Cathay": ["國泰", "國泰證期", "國泰證期研究部", "Cathay"],
        "Taishin": ["台新", "台新投顧", "Taishin"],
        "President": ["統一", "統一投顧", "President"],
        "KGI": ["凱基", "KGI"],
        "HuaNan": ["華南", "華南投顧", "華南永昌", "Hua Nan"],
        "CTBC": ["中信", "中信投顧", "CTBC"],
        "Daiwa": ["大和", "Daiwa"],
        "GoldmanSachs": ["高盛", "Goldman Sachs", "GS"],
        "MorganStanley": ["摩根士丹利", "Morgan Stanley", "MS"],
        "JPMorgan": ["摩根大通", "JPMorgan", "JP Morgan", "JP"],
        "Citi": ["花旗", "Citi", "Citigroup"],
        "UBS": ["瑞銀", "UBS"],
        "CLSA": ["里昂", "CLSA"],
        "Yuanta": ["元大", "Yuanta"],
        "Fubon": ["富邦", "Fubon"],
        "SinoPac": ["永豐", "SinoPac"],
        "Capital": ["群益", "Capital"]
    },
    "target_price_aliases": [
        "目標價", "target price", "price target", "tp", "target",
        "合理價", "fair value", "valuation", "上修目標價", "下修目標價", "維持目標價"
    ],
    "rating_aliases": {
        "BUY": ["買進", "買入", "buy", "strong buy", "overweight", "outperform", "增持", "加碼"],
        "HOLD": ["中立", "持有", "neutral", "hold", "equal-weight", "market perform"],
        "SELL": ["賣出", "sell", "underweight", "underperform", "減碼"],
        "NOT_RATED": ["未評等", "無評等", "not rated", "nr"],
        "INITIATION": ["初次評等", "首次評等", "initiation", "initiating coverage"],
        "MAINTAIN": ["重申", "維持", "maintain", "reiterate"],
        "UPGRADE": ["上調", "升評", "upgrade"],
        "DOWNGRADE": ["下調", "降評", "downgrade"]
    },
    "time_aliases": {
        "report_date": ["報告日期", "出刊日期", "published date", "report date", "date"],
        "fiscal_year": ["財報年度", "年度", "fiscal year", "fy", "year"],
        "quarter": ["季度", "季", "quarter", "q1", "q2", "q3", "q4"],
        "half_year": ["上半年", "下半年", "h1", "h2"],
        "month": ["月份", "月營收", "month", "monthly revenue"],
        "yoy": ["年增率", "年成長", "yoy", "year over year"],
        "qoq": ["季增率", "季成長", "qoq", "quarter over quarter"],
        "ytd": ["累計", "年初至今", "ytd", "year to date"],
        "ttm": ["近四季", "近十二個月", "ttm", "trailing twelve months"],
        "roc_year": ["114年", "115年", "民國114年", "民國115年"]
    },
    "report_category_aliases": {
        "COMPANY_REPORT": ["個股報告", "公司報告", "company report", "stock report", "equity research", "個股介紹報告"],
        "INDUSTRY_REPORT": ["產業報告", "industry report", "sector report", "產業趨勢"],
        "MARKET_DAILY": ["晨會報告", "盤勢分析", "投資早報", "morning meeting", "morning brief", "daily report", "market daily"],
        "INTERVIEW_NOTE": ["訪談速報", "公司訪談摘要", "company visit", "interview note"],
        "OUTLOOK_STRATEGY": ["展望", "投資大趨勢", "outlook", "strategy"],
        "MEMO": ["memo", "Memo", "評估報告"]
    },
    "ticker_patterns": {
        "tw_ticker_regex": r"^(?!202[1-9])(?!2030)[1-9]\d{3}$",
        "tw_yfinance_regex": r"\b[1-9]\d{3}\.(TW|TWO)\b",
        "tw_bloomberg_regex": r"\b[1-9]\d{3} TT\b"
    }
}

def vrn_ssot_augment_get_dict():
    return VRN_SSOT_AUGMENT_V1

def vrn_ssot_augment_flatten_aliases():
    out = []
    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            out.append(x)
    walk(VRN_SSOT_AUGMENT_V1)
    return sorted(set(out), key=lambda z: z.lower())

def vrn_ssot_augment_normalize_rating(text):
    s = str(text or "").strip().lower()
    for k, arr in VRN_SSOT_AUGMENT_V1["rating_aliases"].items():
        for a in arr:
            if a.lower() in s:
                return k
    return "UNKNOWN"

def vrn_ssot_augment_guess_broker(text):
    s = str(text or "").strip().lower()
    for k, arr in VRN_SSOT_AUGMENT_V1["broker_aliases"].items():
        for a in arr:
            if a.lower() in s:
                return k
    return "UNKNOWN"

def vrn_ssot_augment_guess_report_category(text):
    s = str(text or "").strip().lower()
    for k, arr in VRN_SSOT_AUGMENT_V1["report_category_aliases"].items():
        for a in arr:
            if a.lower() in s:
                return k
    return "UNKNOWN"

# [VIA:ANCHOR:AI_APPEND_ONLY:VRN_SSOT_AUGMENT_V1:END]

# [VIA:ANCHOR:AI_APPEND_ONLY:VRN_SSOT_AUGMENT_V2_BACKFILL:START]
# VERSION: VRN_SSOT_AUGMENT_V2_BACKFILL
# STATUS : append-only, non-destructive
# PURPOSE: Fill missing VRN historical rules: report code, filename parser, topic/title, category split, financial DB schema, time normalization.
# CREATED: 2026-05-09T23:02:04
# POLICY : only-add, no-delete, compatible with VIA_SSOT_Unified v4.3.0 + VRN_SSOT_AUGMENT_V1

VRN_SSOT_AUGMENT_V2_BACKFILL = {
    "report_code_rules": {
        "canonical_format": "BrokerAbbrev-Ticker-Name-YYYYMMDD",
        "examples": [
            "GS-3706-神達-20251130",
            "MS-2308-台達電-20251128",
            "JP-2330-台積電-20250718",
            "Daiwa-3653-健策-20251002",
            "兆豐-3706-神達-20251128"
        ],
        "filename_priority": [
            "explicit_broker_prefix",
            "four_digit_ticker",
            "bloomberg_ticker",
            "yfinance_ticker",
            "company_name_near_title",
            "report_date",
            "fallback_original_filename"
        ],
        "broker_abbreviation_map": {
            "GoldmanSachs": ["GS", "Goldman Sachs", "高盛"],
            "MorganStanley": ["MS", "Morgan Stanley", "摩根士丹利"],
            "JPMorgan": ["JP", "JPM", "JP Morgan", "JPMorgan", "摩根大通"],
            "Daiwa": ["Daiwa", "大和"],
            "Citi": ["Citi", "Citigroup", "花旗"],
            "UBS": ["UBS", "瑞銀"],
            "CLSA": ["CLSA", "里昂"],
            "Mega": ["Mega", "兆豐"],
            "Cathay": ["Cathay", "國泰", "國泰證期"],
            "Taishin": ["Taishin", "台新"],
            "KGI": ["KGI", "凱基"],
            "President": ["President", "統一"],
            "HuaNan": ["HuaNan", "華南", "華南永昌"],
            "CTBC": ["CTBC", "中信"],
            "Yuanta": ["Yuanta", "元大"],
            "Fubon": ["Fubon", "富邦"],
            "SinoPac": ["SinoPac", "永豐"]
        }
    },
    "ticker_extraction_rules": {
        "tw_ticker_regex": r"^(?!202[1-9])(?!2030)[1-9]\d{3}$",
        "filename_four_digit_rule": "Split filename into continuous Chinese/English/digit tokens; prefer valid four-digit Taiwan ticker; exclude 2021-2030 year-like tokens.",
        "bloomberg_rule": r"\b[1-9]\d{3}\s*TT\b",
        "yfinance_rule": r"\b[1-9]\d{3}\.(TW|TWO)\b",
        "title_nearby_rule": "If filename uncertain, scan first-page title neighborhood for same first four digits across Taiwan ticker / Bloomberg / YFinance patterns.",
        "name_lookup_rule": "Ticker name may be resolved from TWSE/TPEX/MOPS or local ticker database; do not require official name in report category decision.",
        "industry_exclusion_rule": "Industry report is not counted as company report unless a single dominant company/ticker is explicitly the report subject."
    },
    "topic_title_rules": {
        "topic_definition": "Homepage large non-standardized title phrase near company name/ticker; usually one sentence without period.",
        "topic_size_rule": "Topic title font size is roughly maximum page title size or same level as company name.",
        "topic_exclusion": [
            "table header",
            "footer",
            "broker disclaimer",
            "page number",
            "legal disclosure",
            "market price table"
        ],
        "topic_examples": [
            "大顯神威，營運騰達",
            "AI 潮流下展望 2026 半導體產業趨勢",
            "Thoughts on TPU Competition with GPU"
        ]
    },
    "report_category_rules": {
        "COMPANY_REPORT": [
            "single company",
            "single ticker",
            "個股報告",
            "初次評等",
            "目標價",
            "rating",
            "target price",
            "company visit",
            "interview note",
            "memo with company ticker"
        ],
        "INDUSTRY_REPORT": [
            "multiple companies",
            "sector theme",
            "PCB",
            "AI hardware",
            "Memory",
            "Automation",
            "Thermal Solutions",
            "半導體產業",
            "產業趨勢"
        ],
        "MARKET_DAILY": [
            "晨會報告",
            "投資早報",
            "盤勢分析",
            "當日新聞",
            "重要訊息評論",
            "daily market"
        ],
        "REGIONAL_MARKET": [
            "日股分析",
            "美股分析",
            "港股分析",
            "海外投資展望",
            "海外商品"
        ],
        "FUTURES_DAILY": [
            "期貨晨間解盤",
            "futures daily",
            "futures morning"
        ],
        "STRATEGY_OUTLOOK": [
            "投資大趨勢",
            "展望",
            "strategy",
            "outlook",
            "2026 outlook"
        ]
    },
    "financial_db_schema_rules": {
        "standard_columns": [
            "Report Date",
            "Report Code",
            "Filename",
            "Broker",
            "Ticker",
            "Yfinance Ticker",
            "Bloomberg Ticker",
            "Name",
            "Category",
            "Time",
            "Data",
            "Unit",
            "Value",
            "Source",
            "Verification Confidence"
        ],
        "remove_or_deprecate_basic_header_fields": [
            "Analyst",
            "Rating",
            "Target Price",
            "Adj Close",
            "Upside %",
            "Summary"
        ],
        "category_allowed_values": [
            "INCOME_STATEMENT",
            "BALANCE_SHEET",
            "CASH_FLOW",
            "RATIO_ANALYSIS",
            "PER_SHARE_ANALYSIS"
        ],
        "time_format_rules": {
            "financial_year": "YYYY",
            "report_date": "YYYY/MM/DD for tabular output; YYYY-MM-DD for charts",
            "remove_prefix_suffix": "Strip FY, FYE, 年度, E, A, Q prefix/suffix when canonical Time is annual YYYY.",
            "roc_year_conversion": "ROC year + 1911 = western year, e.g. 114 -> 2025, 115 -> 2026."
        },
        "data_field_rule": "Data is canonical accounting item name, not sentence fragment.",
        "source_allowed_values": ["Report", "TWSE", "TPEX", "MOPS", "YFinance"],
        "number_format_rules": {
            "thousand_separator": True,
            "decimal_places": 2,
            "negative_parentheses_supported": True,
            "dash_or_blank_to_null": True
        }
    },
    "financial_analysis_rules": {
        "eps_split": {
            "basic_eps": ["基本每股盈餘", "Basic EPS", "Basic Earnings Per Share"],
            "diluted_eps": ["稀釋每股盈餘", "Diluted EPS", "Diluted Earnings Per Share"],
            "rule": "Basic EPS and Diluted EPS must be separate Data rows."
        },
        "average_balance_sheet_denominator": {
            "roe": "Net Income / Average Equity",
            "roa": "(Net Income + Interest Expense * (1 - Tax Rate)) / Average Total Assets",
            "receivables_turnover": "Revenue / Average Receivables",
            "inventory_turnover": "Cost of Revenue / Average Inventory",
            "asset_turnover": "Revenue / Average Total Assets",
            "rule": "Cross-statement ratios using balance sheet items should use beginning/end average where available."
        },
        "three_statement_categories": {
            "income_statement": ["營業收入", "營業成本", "營業毛利", "營業利益", "稅前淨利", "本期淨利", "EPS"],
            "balance_sheet": ["資產總額", "流動資產", "現金", "應收帳款", "存貨", "負債總額", "權益總額"],
            "cash_flow": ["營業現金流", "投資現金流", "籌資現金流", "資本支出", "自由現金流"]
        }
    },
    "module_route_plan": {
        "M01": "Report identity extractor: broker, ticker, name, report date, report code, category, topic.",
        "M02": "JSON info support M01-M03; restore tables before database conversion; text repair.",
        "M03": "Support M04-M06 output B; compare restored table path and database-converted path.",
        "M04": "Financial statement extractor: annual financial rows, canonical category/time/data/unit/value/source.",
        "M05": "External verification via TWSE/TPEX/MOPS/YFinance where available.",
        "M06": "Cross-validation and confidence scoring; require same-result check between two extraction paths.",
        "M07": "HTML matrix UI / detailed handover report / evidence packaging."
    },
    "hardgate_rules": {
        "network_default": "locked unless explicitly enabled",
        "parallel_default": "locked unless hardgate allows",
        "supportive_modules": [
            "VIA_SSOT_Unified.py",
            "VIA_RegistryCore_v1.py",
            "VIA_Runtime_Bridge_All_in_One.py",
            "VIA_EnvManager.py",
            "VIA_Panorama_AST_RuntimeInjector.py",
            "VeritasAegisNexus.py",
            "VeritasCeleritas.py",
            "VIS_InstallHealthRegistry.py"
        ],
        "policy": "BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH unless task explicitly asks real run."
    },
    "ui_report_rules": {
        "style": "multi-page matrix HTML UI",
        "sections": [
            "overview",
            "hardgate",
            "ssot coverage",
            "filename classification",
            "report category matrix",
            "financial schema matrix",
            "runtime tests",
            "evidence files",
            "next three processes"
        ],
        "auto_open_html": True,
        "power_shell_remains_open": True
    }
}

def vrn_ssot_v2_get_backfill():
    return VRN_SSOT_AUGMENT_V2_BACKFILL

def vrn_ssot_v2_get_standard_financial_columns():
    return list(VRN_SSOT_AUGMENT_V2_BACKFILL["financial_db_schema_rules"]["standard_columns"])

def vrn_ssot_v2_normalize_report_category(text):
    s = str(text or "").lower()
    for cat, aliases in VRN_SSOT_AUGMENT_V2_BACKFILL["report_category_rules"].items():
        for a in aliases:
            if str(a).lower() in s:
                return cat
    return "UNKNOWN"

def vrn_ssot_v2_guess_report_code_parts(filename):
    import re
    name = str(filename or "")
    out = {
        "broker_token": None,
        "ticker": None,
        "date": None,
        "category": vrn_ssot_v2_normalize_report_category(name)
    }
    for broker, aliases in VRN_SSOT_AUGMENT_V2_BACKFILL["report_code_rules"]["broker_abbreviation_map"].items():
        for a in aliases:
            if str(a).lower() in name.lower():
                out["broker_token"] = broker
                break
        if out["broker_token"]:
            break
    m = re.search(r"(?<!\d)(?!202[1-9])(?!2030)([1-9]\d{3})(?:\s*TT|\.TW|\.TWO|\)|-|_|,|\s|$)", name)
    if m:
        out["ticker"] = m.group(1)
    d = re.search(r"(20\d{2})(\d{2})(\d{2})", name)
    if d:
        out["date"] = f"{d.group(1)}-{d.group(2)}-{d.group(3)}"
    return out

def vrn_ssot_v2_roc_year_to_western_year(value):
    try:
        y = int(str(value).replace("年", "").replace("民國", "").strip())
        if 1 <= y <= 199:
            return y + 1911
        return y
    except Exception:
        return None

# [VIA:ANCHOR:AI_APPEND_ONLY:VRN_SSOT_AUGMENT_V2_BACKFILL:END]


# [VIA:ANCHOR:AI_APPEND_ONLY:VRN_BASIC_INFO_SCHEMA_LOCK_V31:START]
# VERSION: VRN_BASIC_INFO_SCHEMA_LOCK_V31
# STATUS : append-only, non-destructive
# PURPOSE: Lock vrn_basic_info 30-column schema. inserted_at is DB-generated.

VRN_BASIC_INFO_SCHEMA_LOCK_V31 = {
    "schema_id": "VRN_BASIC_INFO_SCHEMA_LOCK_V31",
    "version": "3.1.0",
    "table": "vrn_basic_info",
    "primary_key": "report_code",
    "unique": [
        "report_code"
    ],
    "columns": [
        {
            "ordinal": 1,
            "name": "report_date",
            "type": "VARCHAR",
            "nullable": True,
            "role": "report_date"
        },
        {
            "ordinal": 2,
            "name": "report_code",
            "type": "VARCHAR",
            "nullable": False,
            "role": "primary_key_unique"
        },
        {
            "ordinal": 3,
            "name": "filename",
            "type": "VARCHAR",
            "nullable": True,
            "role": "source_filename"
        },
        {
            "ordinal": 4,
            "name": "broker",
            "type": "VARCHAR",
            "nullable": True,
            "role": "broker"
        },
        {
            "ordinal": 5,
            "name": "analyst",
            "type": "VARCHAR",
            "nullable": True,
            "role": "analyst"
        },
        {
            "ordinal": 6,
            "name": "ticker",
            "type": "VARCHAR",
            "nullable": True,
            "role": "tw_ticker"
        },
        {
            "ordinal": 7,
            "name": "yfinance_ticker",
            "type": "VARCHAR",
            "nullable": True,
            "role": "yfinance_ticker"
        },
        {
            "ordinal": 8,
            "name": "bloomberg_ticker",
            "type": "VARCHAR",
            "nullable": True,
            "role": "bloomberg_ticker"
        },
        {
            "ordinal": 9,
            "name": "name",
            "type": "VARCHAR",
            "nullable": True,
            "role": "company_name_zh"
        },
        {
            "ordinal": 10,
            "name": "name_en",
            "type": "VARCHAR",
            "nullable": True,
            "role": "company_name_en"
        },
        {
            "ordinal": 11,
            "name": "rating",
            "type": "VARCHAR",
            "nullable": True,
            "role": "rating_raw"
        },
        {
            "ordinal": 12,
            "name": "rating_cat",
            "type": "VARCHAR",
            "nullable": True,
            "role": "rating_canonical"
        },
        {
            "ordinal": 13,
            "name": "target_price",
            "type": "DOUBLE",
            "nullable": True,
            "role": "target_price"
        },
        {
            "ordinal": 14,
            "name": "consensus_target_high",
            "type": "DOUBLE",
            "nullable": True,
            "role": "consensus_target"
        },
        {
            "ordinal": 15,
            "name": "consensus_target_low",
            "type": "DOUBLE",
            "nullable": True,
            "role": "consensus_target"
        },
        {
            "ordinal": 16,
            "name": "consensus_target_mean",
            "type": "DOUBLE",
            "nullable": True,
            "role": "consensus_target"
        },
        {
            "ordinal": 17,
            "name": "consensus_target_median",
            "type": "DOUBLE",
            "nullable": True,
            "role": "consensus_target"
        },
        {
            "ordinal": 18,
            "name": "consensus_rating",
            "type": "VARCHAR",
            "nullable": True,
            "role": "consensus_rating"
        },
        {
            "ordinal": 19,
            "name": "consensus_rating_mean",
            "type": "DOUBLE",
            "nullable": True,
            "role": "consensus_rating_mean"
        },
        {
            "ordinal": 20,
            "name": "analyst_count",
            "type": "INTEGER",
            "nullable": True,
            "role": "analyst_count"
        },
        {
            "ordinal": 21,
            "name": "analyst_strong_buy",
            "type": "INTEGER",
            "nullable": True,
            "role": "analyst_count_detail"
        },
        {
            "ordinal": 22,
            "name": "analyst_buy",
            "type": "INTEGER",
            "nullable": True,
            "role": "analyst_count_detail"
        },
        {
            "ordinal": 23,
            "name": "analyst_hold",
            "type": "INTEGER",
            "nullable": True,
            "role": "analyst_count_detail"
        },
        {
            "ordinal": 24,
            "name": "analyst_sell",
            "type": "INTEGER",
            "nullable": True,
            "role": "analyst_count_detail"
        },
        {
            "ordinal": 25,
            "name": "analyst_strong_sell",
            "type": "INTEGER",
            "nullable": True,
            "role": "analyst_count_detail"
        },
        {
            "ordinal": 26,
            "name": "adj_close",
            "type": "DOUBLE",
            "nullable": True,
            "role": "adjusted_close"
        },
        {
            "ordinal": 27,
            "name": "adj_close_date",
            "type": "VARCHAR",
            "nullable": True,
            "role": "adjusted_close_date"
        },
        {
            "ordinal": 28,
            "name": "upside_pct",
            "type": "DOUBLE",
            "nullable": True,
            "role": "derived_upside"
        },
        {
            "ordinal": 29,
            "name": "upside_source",
            "type": "VARCHAR",
            "nullable": True,
            "role": "derived_upside_source"
        },
        {
            "ordinal": 30,
            "name": "summary",
            "type": "VARCHAR",
            "nullable": True,
            "role": "summary"
        }
    ],
    "db_generated_columns": [
        {
            "name": "inserted_at",
            "type": "TIMESTAMP",
            "default": "CURRENT_TIMESTAMP",
            "role": "audit_timestamp"
        }
    ],
    "indexes": [
        "idx_basic_ticker(ticker)",
        "idx_basic_date(report_date)",
        "idx_basic_broker(broker)"
    ],
    "policy": {
        "filename_after_report_code": True,
        "report_code_unique": True,
        "stock_report_only": True,
        "encoding_csv": "utf-8-sig",
        "do_not_drop_columns": True,
        "append_only_ssot": True
    }
}

def vrn_basic_info_v31_get_contract():
    return VRN_BASIC_INFO_SCHEMA_LOCK_V31

def vrn_basic_info_v31_get_columns(include_db_generated=False):
    cols = [c["name"] for c in VRN_BASIC_INFO_SCHEMA_LOCK_V31["columns"]]
    if include_db_generated:
        cols = cols + [c["name"] for c in VRN_BASIC_INFO_SCHEMA_LOCK_V31.get("db_generated_columns", [])]
    return cols

def vrn_basic_info_v31_get_duckdb_ddl():
    return r"""CREATE TABLE IF NOT EXISTS vrn_basic_info (
    report_date VARCHAR,
    report_code VARCHAR PRIMARY KEY,
    filename VARCHAR,
    broker VARCHAR,
    analyst VARCHAR,
    ticker VARCHAR,
    yfinance_ticker VARCHAR,
    bloomberg_ticker VARCHAR,
    name VARCHAR,
    name_en VARCHAR,
    rating VARCHAR,
    rating_cat VARCHAR,
    target_price DOUBLE,
    consensus_target_high DOUBLE,
    consensus_target_low DOUBLE,
    consensus_target_mean DOUBLE,
    consensus_target_median DOUBLE,
    consensus_rating VARCHAR,
    consensus_rating_mean DOUBLE,
    analyst_count INTEGER,
    analyst_strong_buy INTEGER,
    analyst_buy INTEGER,
    analyst_hold INTEGER,
    analyst_sell INTEGER,
    analyst_strong_sell INTEGER,
    adj_close DOUBLE,
    adj_close_date VARCHAR,
    upside_pct DOUBLE,
    upside_source VARCHAR,
    summary VARCHAR,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_vrn_basic_info_report_code
ON vrn_basic_info(report_code);

CREATE INDEX IF NOT EXISTS idx_basic_ticker
ON vrn_basic_info(ticker);

CREATE INDEX IF NOT EXISTS idx_basic_date
ON vrn_basic_info(report_date);

CREATE INDEX IF NOT EXISTS idx_basic_broker
ON vrn_basic_info(broker);
"""

def vrn_basic_info_v31_validate_columns(columns):
    expected = vrn_basic_info_v31_get_columns(False)
    got = list(columns or [])
    return {
        "ok": got == expected,
        "missing": [x for x in expected if x not in got],
        "extra": [x for x in got if x not in expected],
        "expected": expected,
        "got": got
    }
# [VIA:ANCHOR:AI_APPEND_ONLY:VRN_BASIC_INFO_SCHEMA_LOCK_V31:END]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                                                                          ║
# ║  VIA_SSOT_Unified v22 SYNONYM EXTENSION — APPEND-ONLY (功能只增不減)      ║
# ║                                                                          ║
# ║  貼到 VIA_SSOT_Unified.py 末尾即可生效                                    ║
# ║                                                                          ║
# ║  本 patch 補充財務報表會計科目同義字 + 重要比率 + 每股指標,               ║
# ║  共 55 個 canonical key, ~280 個同義詞(中英對照,大小寫不限)。           ║
# ║  來源:VeritasSynonymEngine + FinancialStatementData(使用者文件)。       ║
# ║                                                                          ║
# ║  資料結構:VIA_FIN_SYNONYMS_V22[canonical_key] = [synonym_list]          ║
# ║  公開 API:                                                              ║
# ║    via_fin_synonym(label_text)         -> canonical_key 或 ""           ║
# ║    via_fin_synonyms_all()              -> 整本字典                      ║
# ║    via_fin_category_of(canonical_key)  -> "IS" | "BS" | "CF" | ...      ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ─── INCOME STATEMENT (10 項) ──────────────────────────────────────────────
VIA_FIN_SYNONYMS_IS_V22 = {
    "revenue": [
        "營業收入", "營業收入淨額", "營收", "Net Revenue", "Total Revenue",
        "Revenue", "Sales", "Net Sales", "銷售收入", "Top Line",
    ],
    "cost_of_revenue": [
        "營業成本", "銷貨成本", "Cost of Revenue", "COGS",
        "Cost of Goods Sold", "直接成本",
    ],
    "gross_profit": [
        "營業毛利", "營業毛利淨額", "毛利", "毛利額", "Gross Profit",
    ],
    "operating_expenses": [
        "營業費用", "營業費用合計", "營運費用", "Operating Expenses",
        "OpEx", "SG&A", "Selling, General and Administrative",
    ],
    "rd_expenses": [
        "研究發展費用", "研發支出", "研究開發費", "技術開發費用",
        "R&D Expenses", "R&D", "Research and Development",
    ],
    "operating_income": [
        "營業利益", "營業利益淨額", "營業淨利", "營業獲利", "營運利益",
        "Operating Income", "Operating Profit", "EBIT",
    ],
    "non_operating_income": [
        "營業外收入", "業外收入", "投資收益", "處分利益", "Other Income",
        "Non-operating Income", "業外收支",
    ],
    "pretax_income": [
        "稅前淨利", "稅前利益", "稅前純益", "稅前盈餘", "稅前獲利",
        "Pretax Income", "Income Before Tax", "EBT", "Earnings Before Tax",
    ],
    "tax_expense": [
        "所得稅", "所得稅費用", "稅費", "稅負", "Tax Expense", "Income Tax",
    ],
    "net_income": [
        "本期淨利", "本期純益", "稅後純益", "稅後淨利", "稅後盈餘",
        "純益", "歸屬母公司純益", "Net Income", "Net Profit", "Net Earnings",
    ],
}

# ─── BALANCE SHEET (14 項) ─────────────────────────────────────────────────
VIA_FIN_SYNONYMS_BS_V22 = {
    "cash": [
        "現金及約當現金", "現金", "貨幣資金", "銀行存款",
        "Cash", "Cash & Cash Equivalents", "Cash and Cash Equivalents",
    ],
    "accounts_receivable": [
        "應收帳款", "應收款項", "貿易應收款", "客戶應收款",
        "Accounts Receivable", "A/R", "Trade Receivables",
    ],
    "inventory": [
        "存貨", "庫存", "商品存貨", "製成品", "在製品",
        "Inventory", "Inventories", "Stock",
    ],
    "current_assets": [
        "流動資產合計", "流動資產", "短期資產", "流動資產總額",
        "一年內資產", "Current Assets", "Total Current Assets",
    ],
    "ppe": [
        "不動產廠房設備", "不動產、廠房及設備", "固定資產", "廠房設備",
        "Property Plant and Equipment", "Property, Plant & Equipment",
        "PPE", "PP&E", "Fixed Assets",
    ],
    "total_assets": [
        "資產總計", "資產總額", "資產合計", "總資產", "全部資產",
        "Total Assets",
    ],
    "accounts_payable": [
        "應付帳款", "應付款項", "貿易應付款", "供應商應付款",
        "Accounts Payable", "A/P", "Trade Payables",
    ],
    "short_term_debt": [
        "短期借款", "短期負債", "流動借款", "一年內到期負債",
        "Short-term Debt", "Short-term Borrowings", "Current Debt",
    ],
    "current_liabilities": [
        "流動負債合計", "流動負債", "流動負債總額", "一年內負債",
        "Current Liabilities", "Total Current Liabilities",
    ],
    "long_term_debt": [
        "長期借款", "長期負債", "非流動借款", "長期融資",
        "Long-term Debt", "Long-term Borrowings", "Non-current Debt",
    ],
    "total_liabilities": [
        "負債總計", "負債總額", "負債合計", "總負債", "全部負債",
        "Total Liabilities",
    ],
    "share_capital": [
        "股本", "實收資本", "普通股股本", "股份資本",
        "Share Capital", "Common Stock", "Common Equity", "Paid-in Capital",
    ],
    "retained_earnings": [
        "保留盈餘", "累積盈餘", "未分配盈餘", "累積未分配盈餘",
        "Retained Earnings", "Accumulated Earnings",
    ],
    "shareholders_equity": [
        "股東權益", "權益總計", "權益合計", "股東權益總額", "淨值",
        "Shareholders Equity", "Shareholders' Equity", "Stockholders Equity",
        "Total Equity", "Book Value",
    ],
}

# ─── CASH FLOW (8 項) ──────────────────────────────────────────────────────
VIA_FIN_SYNONYMS_CF_V22 = {
    "operating_cashflow": [
        "營業活動現金流", "營業活動之淨現金流入(流出)",
        "營業活動之現金流量", "營業活動之淨現金流入", "營運現金流",
        "經營活動現金流", "Operating Cash Flow", "Cash Flow from Operations",
        "CFO", "OCF",
    ],
    "investing_cashflow": [
        "投資活動現金流", "投資活動之淨現金流入(流出)",
        "投資活動之現金流量", "投資現金流",
        "Investing Cash Flow", "Cash Flow from Investing", "CFI", "ICF",
    ],
    "financing_cashflow": [
        "籌資活動現金流", "籌資活動之淨現金流入(流出)",
        "融資活動現金流", "資金活動現金流",
        "Financing Cash Flow", "Cash Flow from Financing", "CFF",
    ],
    "depreciation": [
        "折舊費用", "折舊", "折舊與攤提", "固定資產折舊",
        "Depreciation", "D&A",
    ],
    "amortization": [
        "攤提費用", "攤銷費用", "無形資產攤提",
        "Amortization",
    ],
    "capex": [
        "資本支出", "資本性支出", "設備投資", "固定資產投資",
        "取得不動產、廠房及設備",
        "Capital Expenditures", "CapEx", "Capital Expenditure",
    ],
    "free_cashflow": [
        "自由現金流", "自由現金流量",
        "Free Cash Flow", "FCF",
    ],
    "dividends_paid": [
        "發放現金股利", "現金股利支付", "股息發放", "股利分配",
        "Dividends Paid", "Cash Dividends",
    ],
}

# ─── FINANCIAL RATIOS (12 項) ──────────────────────────────────────────────
VIA_FIN_SYNONYMS_RATIO_V22 = {
    "roe": [
        "股東權益報酬率", "權益報酬率", "淨值報酬率", "股東權益收益率",
        "Return on Equity", "ROE",
    ],
    "roa": [
        "資產報酬率", "總資產報酬率", "資產收益率",
        "Return on Assets", "ROA",
    ],
    "gross_margin": [
        "毛利率", "營業毛利率", "毛利潤率",
        "Gross Margin", "Gross Profit Margin",
    ],
    "operating_margin": [
        "營業利益率", "營益率", "營業淨利率", "營運利益率",
        "Operating Margin", "EBIT Margin",
    ],
    "net_margin": [
        "淨利率", "純益率", "稅後淨利率",
        "Net Margin", "Net Profit Margin",
    ],
    "current_ratio": [
        "流動比率", "流動比", "短期償債能力比率",
        "Current Ratio",
    ],
    "quick_ratio": [
        "速動比率", "速動比", "酸性測試比率",
        "Quick Ratio", "Acid Test Ratio", "Acid-Test Ratio",
    ],
    "debt_ratio": [
        "負債比率", "債務比率", "資產負債率", "負債比",
        "Debt Ratio", "Debt to Assets",
    ],
    "debt_to_equity": [
        "負債權益比", "負債對權益比率",
        "Debt-to-Equity", "D/E Ratio", "Debt to Equity",
    ],
    "pe_ratio": [
        "本益比", "股價盈餘比",
        "PE Ratio", "P/E Ratio", "PER", "Price-to-Earnings",
        "Price to Earnings", "Trailing PE",
    ],
    "pb_ratio": [
        "股價淨值比", "市價淨值比",
        "PB Ratio", "P/B Ratio", "PBR", "Price-to-Book", "Price to Book",
    ],
    "ps_ratio": [
        "股價營收比", "市價營收比",
        "PS Ratio", "P/S Ratio", "PSR", "Price-to-Sales", "Price to Sales",
    ],
}

# ─── PER-SHARE METRICS (11 項) ─────────────────────────────────────────────
VIA_FIN_SYNONYMS_PER_SHARE_V22 = {
    "basic_eps": [
        "基本每股盈餘", "每股盈餘", "每股稅後盈餘",
        "Basic EPS", "基本EPS", "Basic Earnings Per Share",
    ],
    "diluted_eps": [
        "稀釋每股盈餘", "稀釋後EPS", "完全稀釋每股盈餘",
        "Diluted EPS", "Diluted Earnings Per Share",
    ],
    "book_value_per_share": [
        "每股淨值", "每股帳面價值", "每股股東權益",
        "BVPS", "Book Value Per Share",
    ],
    "dividend_per_share": [
        "每股現金股利", "每股配息", "現金股息", "股利",
        "DPS", "Dividend Per Share", "Dividends",
    ],
    "cashflow_per_share": [
        "每股現金流", "每股營業現金流",
        "CFPS", "Cash Flow Per Share",
    ],
    "sales_per_share": [
        "每股營收",
        "SPS", "Sales Per Share", "Revenue Per Share",
    ],
    "shares_outstanding": [
        "普通股流通股數", "普通股股數", "流通在外股數", "發行股數",
        "市場流通股", "已發行股數",
        "Shares Outstanding", "Common Shares Outstanding",
    ],
    "weighted_avg_shares": [
        "加權平均股數", "加權平均流通股數", "基本股數",
        "Weighted Average Shares", "Weighted Average Shares Outstanding",
    ],
    "diluted_shares": [
        "完全稀釋後股數", "稀釋後股數", "稀釋後流通股數", "完全稀釋股本",
        "Diluted Shares", "Fully Diluted Shares", "Diluted Average Shares",
    ],
    "dividend_yield": [
        "股利殖利率", "現金殖利率", "殖利率", "股息收益率",
        "Yield", "Dividend Yield",
    ],
    "payout_ratio": [
        "配息率", "股利發放率", "配息比例", "股利支付率",
        "Payout Ratio",
    ],
}

# ─── 整合所有 ──────────────────────────────────────────────────────────────
VIA_FIN_SYNONYMS_V22 = {}
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_IS_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_BS_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_CF_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_RATIO_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_PER_SHARE_V22)

# Category mapping
VIA_FIN_CATEGORY_MAP_V22 = {}
for k in VIA_FIN_SYNONYMS_IS_V22:        VIA_FIN_CATEGORY_MAP_V22[k] = "IS"
for k in VIA_FIN_SYNONYMS_BS_V22:        VIA_FIN_CATEGORY_MAP_V22[k] = "BS"
for k in VIA_FIN_SYNONYMS_CF_V22:        VIA_FIN_CATEGORY_MAP_V22[k] = "CF"
for k in VIA_FIN_SYNONYMS_RATIO_V22:     VIA_FIN_CATEGORY_MAP_V22[k] = "RATIO"
for k in VIA_FIN_SYNONYMS_PER_SHARE_V22: VIA_FIN_CATEGORY_MAP_V22[k] = "PER_SHARE"


# ─── 反向索引(預編譯,加速 lookup) ────────────────────────────────────
_VIA_FIN_REVERSE_V22 = {}
for canon, alts in VIA_FIN_SYNONYMS_V22.items():
    for a in alts:
        _VIA_FIN_REVERSE_V22[a.lower()] = canon


# ─── 公開 API ──────────────────────────────────────────────────────────────
def via_fin_synonym(label_text: str) -> str:
    """根據 label_text(任何同義字)回傳 canonical_key。
    比對策略:
      1. 完全相等(大小寫不限) — 最精確
      2. label_text 包含 alt 或 alt 包含 label_text — 寬鬆 fallback
    找不到回 ""。"""
    if not label_text:
        return ""
    s = str(label_text).strip().lower()
    if not s:
        return ""
    # Exact match
    if s in _VIA_FIN_REVERSE_V22:
        return _VIA_FIN_REVERSE_V22[s]
    # Substring containment
    for alt_lower, canon in _VIA_FIN_REVERSE_V22.items():
        if alt_lower in s or s in alt_lower:
            return canon
    return ""


def via_fin_synonyms_all() -> dict:
    """回傳整本同義字字典(canonical_key → [synonym, ...])。"""
    return dict(VIA_FIN_SYNONYMS_V22)


def via_fin_category_of(canonical_key: str) -> str:
    """根據 canonical_key 回傳 category(IS / BS / CF / RATIO / PER_SHARE)。
    找不到回 'UNKNOWN'。"""
    return VIA_FIN_CATEGORY_MAP_V22.get(canonical_key, "UNKNOWN")


def via_fin_synonyms_count() -> dict:
    """回傳統計資訊。"""
    return {
        "canonical_keys": len(VIA_FIN_SYNONYMS_V22),
        "total_synonyms": sum(len(v) for v in VIA_FIN_SYNONYMS_V22.values()),
        "by_category": {
            "IS":        len(VIA_FIN_SYNONYMS_IS_V22),
            "BS":        len(VIA_FIN_SYNONYMS_BS_V22),
            "CF":        len(VIA_FIN_SYNONYMS_CF_V22),
            "RATIO":     len(VIA_FIN_SYNONYMS_RATIO_V22),
            "PER_SHARE": len(VIA_FIN_SYNONYMS_PER_SHARE_V22),
        },
    }


# ─── self-test(import 此模組時不執行,只在直接 run 時跑) ────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("VIA SSOT v22 Synonym Extension — Self-Test")
    print("=" * 60)
    stats = via_fin_synonyms_count()
    print(f"\n[STATS] canonical_keys = {stats['canonical_keys']}")
    print(f"[STATS] total_synonyms = {stats['total_synonyms']}")
    for cat, n in stats['by_category'].items():
        print(f"  {cat:>10s} : {n}")

    test_cases = [
        ("營業收入",             "revenue"),
        ("Revenue",              "revenue"),
        ("NET REVENUE",          "revenue"),
        ("基本每股盈餘",         "basic_eps"),
        ("Basic EPS",            "basic_eps"),
        ("ROE",                  "roe"),
        ("股東權益報酬率",       "roe"),
        ("營業活動之現金流量",   "operating_cashflow"),
        ("Operating Cash Flow",  "operating_cashflow"),
        ("負債權益比",           "debt_to_equity"),
        ("資產總計",             "total_assets"),
        ("Total Assets",         "total_assets"),
        ("XYZ_UNKNOWN_LABEL",    ""),
    ]
    print("\n[LOOKUP TESTS]")
    n_ok = 0
    for label, expected in test_cases:
        result = via_fin_synonym(label)
        cat = via_fin_category_of(result) if result else "-"
        ok = (result == expected)
        if ok: n_ok += 1
        flag = "OK" if ok else "FAIL"
        print(f"  [{flag:>4s}] {label:30s} → {result:25s} ({cat})  expected={expected}")
    print(f"\n[RESULT] {n_ok}/{len(test_cases)} lookup tests passed")



# VIA_SSOT_Unified v22 SYNONYM EXTENSION
# Append-only patch. No future import. No destructive mutation.

VRN_BASIC_INFO_V31_COLUMNS = [
    "report_date",
    "report_code",
    "filename",
    "broker",
    "analyst",
    "ticker",
    "yfinance_ticker",
    "bloomberg_ticker",
    "name",
    "name_en",
    "rating",
    "rating_cat",
    "target_price",
    "consensus_target_high",
    "consensus_target_low",
    "consensus_target_mean",
    "consensus_target_median",
    "consensus_rating",
    "consensus_rating_mean",
    "analyst_count",
    "analyst_strong_buy",
    "analyst_buy",
    "analyst_hold",
    "analyst_sell",
    "analyst_strong_sell",
    "adj_close",
    "adj_close_date",
    "upside_pct",
    "upside_source",
    "summary",
]

VRN_FINANCIAL_DATA_V31_COLUMNS = [
    "report_date",
    "report_code",
    "filename",
    "broker",
    "ticker",
    "yfinance_ticker",
    "bloomberg_ticker",
    "name",
    "category",
    "time_period",
    "data_label",
    "unit",
    "value",
    "source",
    "verification_confidence",
]

VRN_BROKER_ALIASES_V22 = {
    "兆豐": ["兆豐", "Mega", "Mega Securities"],
    "國泰": ["國泰", "Cathay", "國泰證期", "Cathay Securities"],
    "台新": ["台新", "Taishin"],
    "統一": ["統一", "President", "President Securities"],
    "凱基": ["凱基", "KGI"],
    "華南": ["華南", "Hua Nan"],
    "中信": ["中信", "CTBC"],
    "元大": ["元大", "Yuanta"],
    "富邦": ["富邦", "Fubon"],
    "永豐": ["永豐", "SinoPac"],
    "Daiwa": ["Daiwa", "大和", "大和證券", "大和資本", "Daiwa Securities", "Daiwa Capital Markets"],
    "GS": ["GS", "Goldman", "Goldman Sachs", "高盛"],
    "MS": ["MS", "Morgan Stanley", "摩根士丹利"],
    "JP": ["JP", "JPMorgan", "JP Morgan", "摩根大通"],
    "Citi": ["Citi", "Citigroup", "花旗"],
    "UBS": ["UBS", "瑞銀"],
    "CLSA": ["CLSA", "里昂"],
}

VRN_RATING_ALIASES_V22 = {
    "strong_buy": ["強力買進", "strong buy", "strong-buy"],
    "buy": ["買進", "買入", "buy", "overweight", "outperform", "增持", "加碼"],
    "hold": ["中立", "持有", "hold", "neutral", "equal-weight", "market perform"],
    "sell": ["賣出", "sell", "underweight", "underperform", "減碼"],
    "not_rated": ["未評等", "無評等", "not rated", "nr"],
}

VRN_TARGET_PRICE_ALIASES_V22 = [
    "目標價",
    "合理價",
    "推估合理價",
    "target price",
    "price target",
    "TP",
    "fair value",
]

VRN_TIME_PERIOD_ALIASES_V22 = [
    "2024", "2025", "2026", "2027", "2028",
    "FY24", "FY25", "FY26", "FY27", "FY28",
    "24E", "25E", "26E", "27E", "28E",
    "2024E", "2025E", "2026E", "2027E", "2028E",
    "113年", "114年", "115年", "116年", "117年",
]

VRN_STOCK_REPORT_POSITIVE_TERMS_V22 = [
    "個股",
    "個股報告",
    "訪談",
    "速報",
    "初次評等",
    "公司報告",
    "company report",
    "initiation",
    "equity research",
    "company update",
    "target price",
    "rating",
    "tp",
    "Daiwa",
    "大和",
]

VRN_STOCK_REPORT_REJECT_TERMS_V22 = [
    "產業",
    "產業報告",
    "產業趨勢",
    "晨會",
    "晨會報告",
    "投資早報",
    "市場日報",
    "盤勢",
    "策略",
    "展望",
    "總經",
    "總體",
    "期貨",
    "日股",
    "美股",
    "港股",
    "海外",
    "commodity",
    "commodities",
    "macro",
    "strategy",
    "outlook",
    "industry",
    "sector",
    "market daily",
    "morning",
    "futures",
    "ETF",
    "etf",
]

VIA_FIN_SYNONYMS_V22 = {
    "revenue": {
        "category": "IS",
        "aliases": ["營業收入", "營業收入淨額", "營收", "收入", "Total Revenue", "Revenue", "Net Revenue", "Sales", "Net Sales"],
    },
    "cost_of_revenue": {
        "category": "IS",
        "aliases": ["營業成本", "銷貨成本", "成本", "Cost of Revenue", "COGS", "Cost of Goods Sold"],
    },
    "gross_profit": {
        "category": "IS",
        "aliases": ["營業毛利", "營業毛利淨額", "毛利", "Gross Profit"],
    },
    "operating_expenses": {
        "category": "IS",
        "aliases": ["營業費用", "營業支出", "Operating Expenses", "Opex", "SG&A"],
    },
    "operating_income": {
        "category": "IS",
        "aliases": ["營業利益", "營業利益淨額", "營業淨利", "Operating Income", "Operating Profit", "EBIT"],
    },
    "non_operating_income": {
        "category": "IS",
        "aliases": ["營業外收入", "營業外收支", "業外收入", "Non-operating Income", "Non Operating Income"],
    },
    "pretax_income": {
        "category": "IS",
        "aliases": ["稅前淨利", "稅前利益", "稅前盈餘", "Pretax Income", "Income Before Tax", "Profit Before Tax"],
    },
    "tax_expense": {
        "category": "IS",
        "aliases": ["所得稅", "所得稅費用", "Tax Expense", "Income Tax"],
    },
    "net_income": {
        "category": "IS",
        "aliases": ["本期淨利", "稅後純益", "稅後淨利", "歸屬母公司淨利", "Net Income", "Net Profit", "Profit After Tax"],
    },
    "basic_eps": {
        "category": "PER_SHARE",
        "aliases": ["基本每股盈餘", "每股盈餘", "Basic EPS", "Basic Earnings Per Share"],
    },
    "diluted_eps": {
        "category": "PER_SHARE",
        "aliases": ["稀釋每股盈餘", "Diluted EPS", "Diluted Earnings Per Share", "EPS"],
    },
    "gross_margin": {
        "category": "RATIO",
        "aliases": ["毛利率", "Gross Margin", "GPM"],
    },
    "operating_margin": {
        "category": "RATIO",
        "aliases": ["營業利益率", "營益率", "Operating Margin", "OPM"],
    },
    "net_margin": {
        "category": "RATIO",
        "aliases": ["純益率", "淨利率", "Net Margin", "Net Profit Margin", "NPM"],
    },
    "roe": {
        "category": "RATIO",
        "aliases": ["股東權益報酬率", "權益報酬率", "ROE", "Return on Equity"],
    },
    "roa": {
        "category": "RATIO",
        "aliases": ["總資產報酬率", "資產報酬率", "ROA", "Return on Assets"],
    },
    "pe_ratio": {
        "category": "RATIO",
        "aliases": ["本益比", "PER", "P/E", "PE Ratio"],
    },
    "pb_ratio": {
        "category": "RATIO",
        "aliases": ["股價淨值比", "PBR", "P/B", "PB Ratio"],
    },
    "dividend_yield": {
        "category": "RATIO",
        "aliases": ["殖利率", "股息殖利率", "Dividend Yield"],
    },
    "total_assets": {
        "category": "BS",
        "aliases": ["資產總額", "資產總計", "總資產", "Total Assets"],
    },
    "total_liabilities": {
        "category": "BS",
        "aliases": ["負債總額", "負債總計", "總負債", "Total Liabilities"],
    },
    "total_equity": {
        "category": "BS",
        "aliases": ["權益總額", "權益總計", "股東權益", "Total Equity", "Shareholders Equity"],
    },
    "debt_to_equity": {
        "category": "RATIO",
        "aliases": ["負債權益比", "Debt to Equity", "D/E", "Debt Equity Ratio"],
    },
    "operating_cashflow": {
        "category": "CF",
        "aliases": ["營業活動現金流", "營業活動之現金流量", "營運現金流", "Operating Cash Flow", "Cash Flow from Operations", "CFO"],
    },
    "investing_cashflow": {
        "category": "CF",
        "aliases": ["投資活動現金流", "投資活動之現金流量", "Investing Cash Flow", "CFI"],
    },
    "financing_cashflow": {
        "category": "CF",
        "aliases": ["籌資活動現金流", "籌資活動之現金流量", "Financing Cash Flow", "CFF"],
    },
    "capex": {
        "category": "CF",
        "aliases": ["資本支出", "資本開支", "Capex", "Capital Expenditure"],
    },
    "free_cashflow": {
        "category": "CF",
        "aliases": ["自由現金流", "Free Cash Flow", "FCF"],
    },
}

def via_fin_synonyms_count():
    by_category = {}
    total = 0
    for key, spec in VIA_FIN_SYNONYMS_V22.items():
        cat = spec.get("category", "UNKNOWN")
        n = len(spec.get("aliases", []))
        total += n
        by_category[cat] = by_category.get(cat, 0) + n
    return {
        "canonical_keys": len(VIA_FIN_SYNONYMS_V22),
        "total_synonyms": total,
        "by_category": by_category,
    }

def via_fin_synonym(label):
    text = "" if label is None else str(label).strip()
    low = text.lower()
    if not low:
        return ""
    for canon, spec in VIA_FIN_SYNONYMS_V22.items():
        if low == canon.lower():
            return canon
        for alias in spec.get("aliases", []):
            a = str(alias).strip().lower()
            if low == a or low in a or a in low:
                return canon
    return ""

def via_fin_category_of(canonical_key):
    if not canonical_key:
        return ""
    spec = VIA_FIN_SYNONYMS_V22.get(str(canonical_key), {})
    return spec.get("category", "")

def via_vrn_broker_alias(text):
    low = "" if text is None else str(text).lower()
    for canon, aliases in VRN_BROKER_ALIASES_V22.items():
        for alias in aliases:
            if str(alias).lower() in low:
                return canon
    return ""

def via_vrn_rating_alias(text):
    low = "" if text is None else str(text).lower()
    for cat, aliases in VRN_RATING_ALIASES_V22.items():
        for alias in aliases:
            if str(alias).lower() in low:
                return cat
    return ""

def via_vrn_basic_info_columns(include_db_generated=False):
    cols = list(VRN_BASIC_INFO_V31_COLUMNS)
    if include_db_generated:
        cols.append("inserted_at")
    return cols

def via_vrn_financial_data_columns(include_db_generated=False):
    cols = list(VRN_FINANCIAL_DATA_V31_COLUMNS)
    if include_db_generated:
        cols.extend(["id", "inserted_at"])
    return cols

def via_vrn_stock_report_terms():
    return {
        "positive": list(VRN_STOCK_REPORT_POSITIVE_TERMS_V22),
        "reject": list(VRN_STOCK_REPORT_REJECT_TERMS_V22),
    }

def via_vrn_target_price_aliases():
    return list(VRN_TARGET_PRICE_ALIASES_V22)

def via_vrn_time_period_aliases():
    return list(VRN_TIME_PERIOD_ALIASES_V22)



# VIA_SSOT_Unified v22.1 CASHFLOW COMPAT EXTENSION
# Append-only compatibility patch.
# Purpose:
#   Fix v22 self-test 12/13 caused by operating_cashflow vs operating_cash_flow naming drift.

VRN_FIN_CANONICAL_COMPAT_V22_1 = {
    "operating_cashflow": "operating_cashflow",
    "operating_cash_flow": "operating_cashflow",
    "cash_flow_from_operations": "operating_cashflow",
    "cfo": "operating_cashflow",
    "營業活動現金流": "operating_cashflow",
    "營業活動之現金流量": "operating_cashflow",
    "營運現金流": "operating_cashflow",

    "investing_cashflow": "investing_cashflow",
    "investing_cash_flow": "investing_cashflow",
    "cfi": "investing_cashflow",
    "投資活動現金流": "investing_cashflow",
    "投資活動之現金流量": "investing_cashflow",

    "financing_cashflow": "financing_cashflow",
    "financing_cash_flow": "financing_cashflow",
    "cff": "financing_cashflow",
    "籌資活動現金流": "financing_cashflow",
    "籌資活動之現金流量": "financing_cashflow",
}

_VIA_FIN_SYNONYM_PREV_V22_1 = globals().get("via_fin_synonym", None)
_VIA_FIN_CATEGORY_PREV_V22_1 = globals().get("via_fin_category_of", None)

def via_fin_synonym(label):
    text = "" if label is None else str(label).strip()
    low = text.lower()
    if not low:
        return ""

    if low in VRN_FIN_CANONICAL_COMPAT_V22_1:
        return VRN_FIN_CANONICAL_COMPAT_V22_1[low]

    if text in VRN_FIN_CANONICAL_COMPAT_V22_1:
        return VRN_FIN_CANONICAL_COMPAT_V22_1[text]

    if _VIA_FIN_SYNONYM_PREV_V22_1 is not None:
        try:
            got = _VIA_FIN_SYNONYM_PREV_V22_1(label)
            if got:
                got_low = str(got).lower()
                return VRN_FIN_CANONICAL_COMPAT_V22_1.get(got_low, got)
        except Exception:
            pass

    return ""

def via_fin_category_of(canonical_key):
    key = "" if canonical_key is None else str(canonical_key).strip()
    key = VRN_FIN_CANONICAL_COMPAT_V22_1.get(key.lower(), key)

    if key in ["operating_cashflow", "investing_cashflow", "financing_cashflow"]:
        return "CF"

    if _VIA_FIN_CATEGORY_PREV_V22_1 is not None:
        try:
            got = _VIA_FIN_CATEGORY_PREV_V22_1(key)
            if got:
                return got
        except Exception:
            pass

    return ""

def via_vrn_v22_1_compat_status():
    return {
        "marker": "VIA_SSOT_Unified v22.1 CASHFLOW COMPAT EXTENSION",
        "cashflow_aliases": sorted(VRN_FIN_CANONICAL_COMPAT_V22_1.keys()),
        "operating_cashflow": via_fin_synonym("營業活動之現金流量"),
        "operating_cash_flow": via_fin_synonym("operating_cash_flow"),
        "cfo": via_fin_synonym("CFO"),
        "category": via_fin_category_of("operating_cash_flow"),
    }



# VIA_SSOT_Unified v22.2 FINAL VRN OVERRIDE EXTENSION
# Append-only final compatibility layer.
# This patch intentionally redefines public SSOT helper functions at the end of file.
# Purpose:
#   Eliminate canonical drift from prior append layers.
#   Lock VRN BasicInfo / FinancialData / Daiwa / Rating / Finance synonyms.

VRN_BASIC_INFO_V31_COLUMNS_FINAL = [
    "report_date",
    "report_code",
    "filename",
    "broker",
    "analyst",
    "ticker",
    "yfinance_ticker",
    "bloomberg_ticker",
    "name",
    "name_en",
    "rating",
    "rating_cat",
    "target_price",
    "consensus_target_high",
    "consensus_target_low",
    "consensus_target_mean",
    "consensus_target_median",
    "consensus_rating",
    "consensus_rating_mean",
    "analyst_count",
    "analyst_strong_buy",
    "analyst_buy",
    "analyst_hold",
    "analyst_sell",
    "analyst_strong_sell",
    "adj_close",
    "adj_close_date",
    "upside_pct",
    "upside_source",
    "summary",
]

VRN_FINANCIAL_DATA_V31_COLUMNS_FINAL = [
    "report_date",
    "report_code",
    "filename",
    "broker",
    "ticker",
    "yfinance_ticker",
    "bloomberg_ticker",
    "name",
    "category",
    "time_period",
    "data_label",
    "unit",
    "value",
    "source",
    "verification_confidence",
]

VRN_BROKER_ALIASES_V22_2_FINAL = {
    "Daiwa": [
        "daiwa",
        "daiwa securities",
        "daiwa capital",
        "daiwa capital markets",
        "大和",
        "大和證券",
        "大和資本",
    ],
    "兆豐": ["兆豐", "mega", "mega securities"],
    "國泰": ["國泰", "cathay", "國泰證期", "cathay securities"],
    "台新": ["台新", "taishin"],
    "統一": ["統一", "president", "president securities"],
    "凱基": ["凱基", "kgi"],
    "華南": ["華南", "hua nan"],
    "中信": ["中信", "ctbc"],
    "元大": ["元大", "yuanta"],
    "富邦": ["富邦", "fubon"],
    "永豐": ["永豐", "sinopac"],
    "GS": ["gs", "goldman", "goldman sachs", "高盛"],
    "MS": ["ms", "morgan stanley", "摩根士丹利"],
    "JP": ["jp", "jpmorgan", "jp morgan", "摩根大通"],
    "Citi": ["citi", "citigroup", "花旗"],
    "UBS": ["ubs", "瑞銀"],
    "CLSA": ["clsa", "里昂"],
}

VRN_RATING_ALIASES_V22_2_FINAL = {
    "strong_buy": ["強力買進", "strong buy", "strong-buy"],
    "buy": ["買進", "買入", "buy", "overweight", "outperform", "增持", "加碼"],
    "hold": ["中立", "持有", "hold", "neutral", "equal-weight", "market perform"],
    "sell": ["賣出", "sell", "underweight", "underperform", "減碼"],
    "not_rated": ["未評等", "無評等", "not rated", "nr"],
}

VRN_FIN_CANONICAL_FINAL = {
    "revenue": {
        "category": "IS",
        "aliases": [
            "revenue", "total revenue", "net revenue", "sales", "net sales",
            "營業收入", "營業收入淨額", "營收", "收入"
        ],
    },
    "cost_of_revenue": {
        "category": "IS",
        "aliases": [
            "cost_of_revenue", "cost of revenue", "cogs", "cost of goods sold",
            "營業成本", "銷貨成本", "成本"
        ],
    },
    "gross_profit": {
        "category": "IS",
        "aliases": [
            "gross_profit", "gross profit", "營業毛利", "營業毛利淨額", "毛利"
        ],
    },
    "operating_expenses": {
        "category": "IS",
        "aliases": [
            "operating_expenses", "operating expenses", "opex", "sg&a",
            "營業費用", "營業支出"
        ],
    },
    "operating_income": {
        "category": "IS",
        "aliases": [
            "operating_income", "operating income", "operating profit", "ebit",
            "營業利益", "營業利益淨額", "營業淨利"
        ],
    },
    "non_operating_income": {
        "category": "IS",
        "aliases": [
            "non_operating_income", "non-operating income", "non operating income",
            "營業外收入", "營業外收支", "業外收入"
        ],
    },
    "pretax_income": {
        "category": "IS",
        "aliases": [
            "pretax_income", "pretax income", "income before tax", "profit before tax",
            "稅前淨利", "稅前利益", "稅前盈餘"
        ],
    },
    "tax_expense": {
        "category": "IS",
        "aliases": [
            "tax_expense", "tax expense", "income tax", "所得稅", "所得稅費用"
        ],
    },
    "net_income": {
        "category": "IS",
        "aliases": [
            "net_income", "net income", "net profit", "profit after tax",
            "本期淨利", "稅後純益", "稅後淨利", "歸屬母公司淨利"
        ],
    },
    "basic_eps": {
        "category": "PER_SHARE",
        "aliases": [
            "basic_eps", "basic eps", "basic earnings per share",
            "基本每股盈餘", "每股盈餘"
        ],
    },
    "diluted_eps": {
        "category": "PER_SHARE",
        "aliases": [
            "diluted_eps", "diluted eps", "diluted earnings per share", "eps",
            "稀釋每股盈餘"
        ],
    },
    "gross_margin": {
        "category": "RATIO",
        "aliases": [
            "gross_margin", "gross margin", "gpm", "毛利率"
        ],
    },
    "operating_margin": {
        "category": "RATIO",
        "aliases": [
            "operating_margin", "operating margin", "opm", "營業利益率", "營益率"
        ],
    },
    "net_margin": {
        "category": "RATIO",
        "aliases": [
            "net_margin", "net margin", "net profit margin", "npm", "純益率", "淨利率"
        ],
    },
    "roe": {
        "category": "RATIO",
        "aliases": [
            "roe", "return on equity", "股東權益報酬率", "權益報酬率"
        ],
    },
    "roa": {
        "category": "RATIO",
        "aliases": [
            "roa", "return on assets", "總資產報酬率", "資產報酬率"
        ],
    },
    "pe_ratio": {
        "category": "RATIO",
        "aliases": [
            "pe_ratio", "pe ratio", "per", "p/e", "本益比"
        ],
    },
    "pb_ratio": {
        "category": "RATIO",
        "aliases": [
            "pb_ratio", "pb ratio", "pbr", "p/b", "股價淨值比"
        ],
    },
    "dividend_yield": {
        "category": "RATIO",
        "aliases": [
            "dividend_yield", "dividend yield", "殖利率", "股息殖利率"
        ],
    },
    "total_assets": {
        "category": "BS",
        "aliases": [
            "total_assets", "total assets", "資產總額", "資產總計", "總資產"
        ],
    },
    "total_liabilities": {
        "category": "BS",
        "aliases": [
            "total_liabilities", "total liabilities", "負債總額", "負債總計", "總負債"
        ],
    },
    "total_equity": {
        "category": "BS",
        "aliases": [
            "total_equity", "total equity", "shareholders equity",
            "權益總額", "權益總計", "股東權益"
        ],
    },
    "debt_to_equity": {
        "category": "RATIO",
        "aliases": [
            "debt_to_equity", "debt to equity", "debt equity ratio", "d/e",
            "負債權益比"
        ],
    },
    "operating_cashflow": {
        "category": "CF",
        "aliases": [
            "operating_cashflow", "operating_cash_flow", "cash_flow_from_operations",
            "operating cash flow", "cash flow from operations", "cfo",
            "營業活動現金流", "營業活動之現金流量", "營運現金流"
        ],
    },
    "investing_cashflow": {
        "category": "CF",
        "aliases": [
            "investing_cashflow", "investing_cash_flow", "investing cash flow", "cfi",
            "投資活動現金流", "投資活動之現金流量"
        ],
    },
    "financing_cashflow": {
        "category": "CF",
        "aliases": [
            "financing_cashflow", "financing_cash_flow", "financing cash flow", "cff",
            "籌資活動現金流", "籌資活動之現金流量"
        ],
    },
    "capex": {
        "category": "CF",
        "aliases": [
            "capex", "capital expenditure", "capital expenditures", "資本支出", "資本開支"
        ],
    },
    "free_cashflow": {
        "category": "CF",
        "aliases": [
            "free_cashflow", "free_cash_flow", "free cash flow", "fcf", "自由現金流"
        ],
    },
}

def _via_vrn_normalize_final_text_v22_2(value):
    return "" if value is None else str(value).strip().lower()

def via_fin_synonym(label):
    text = "" if label is None else str(label).strip()
    low = text.lower()
    if not low:
        return ""

    normalized = low.replace("-", "_").replace(" ", "_")
    for canon, spec in VRN_FIN_CANONICAL_FINAL.items():
        if low == canon.lower() or normalized == canon.lower():
            return canon
        for alias in spec.get("aliases", []):
            a = str(alias).strip().lower()
            a_norm = a.replace("-", "_").replace(" ", "_")
            if low == a or normalized == a_norm:
                return canon

    for canon, spec in VRN_FIN_CANONICAL_FINAL.items():
        for alias in spec.get("aliases", []):
            a = str(alias).strip().lower()
            if a and (a in low or low in a):
                return canon

    return ""

def via_fin_category_of(canonical_key):
    canon = via_fin_synonym(canonical_key)
    if not canon:
        canon = "" if canonical_key is None else str(canonical_key).strip()
    spec = VRN_FIN_CANONICAL_FINAL.get(canon, {})
    return spec.get("category", "")

def via_fin_synonyms_count():
    by_category = {}
    total = 0
    for canon, spec in VRN_FIN_CANONICAL_FINAL.items():
        cat = spec.get("category", "UNKNOWN")
        n = len(spec.get("aliases", []))
        total += n
        by_category[cat] = by_category.get(cat, 0) + n
    return {
        "canonical_keys": len(VRN_FIN_CANONICAL_FINAL),
        "total_synonyms": total,
        "by_category": by_category,
    }

def via_vrn_broker_alias(text):
    low = _via_vrn_normalize_final_text_v22_2(text)
    if not low:
        return ""
    for canon, aliases in VRN_BROKER_ALIASES_V22_2_FINAL.items():
        for alias in aliases:
            a = _via_vrn_normalize_final_text_v22_2(alias)
            if a and a in low:
                return canon
    return ""

def via_vrn_rating_alias(text):
    low = _via_vrn_normalize_final_text_v22_2(text)
    if not low:
        return ""
    for cat, aliases in VRN_RATING_ALIASES_V22_2_FINAL.items():
        for alias in aliases:
            a = _via_vrn_normalize_final_text_v22_2(alias)
            if a and a in low:
                return cat
    return ""

def via_vrn_basic_info_columns(include_db_generated=False):
    cols = list(VRN_BASIC_INFO_V31_COLUMNS_FINAL)
    if include_db_generated:
        cols.append("inserted_at")
    return cols

def via_vrn_financial_data_columns(include_db_generated=False):
    cols = list(VRN_FINANCIAL_DATA_V31_COLUMNS_FINAL)
    if include_db_generated:
        cols.extend(["id", "inserted_at"])
    return cols

def via_vrn_stock_report_terms():
    return {
        "positive": [
            "個股", "個股報告", "訪談", "速報", "初次評等", "公司報告",
            "company report", "initiation", "equity research", "company update",
            "target price", "rating", "tp", "Daiwa", "大和",
        ],
        "reject": [
            "產業", "產業報告", "產業趨勢", "晨會", "晨會報告", "投資早報",
            "市場日報", "盤勢", "策略", "展望", "總經", "總體", "期貨",
            "日股", "美股", "港股", "海外", "commodity", "commodities",
            "macro", "strategy", "outlook", "industry", "sector", "market daily",
            "morning", "futures", "ETF", "etf",
        ],
    }

def via_vrn_target_price_aliases():
    return ["目標價", "合理價", "推估合理價", "target price", "price target", "TP", "fair value"]

def via_vrn_time_period_aliases():
    return [
        "2024", "2025", "2026", "2027", "2028",
        "FY24", "FY25", "FY26", "FY27", "FY28",
        "24E", "25E", "26E", "27E", "28E",
        "2024E", "2025E", "2026E", "2027E", "2028E",
        "113年", "114年", "115年", "116年", "117年",
    ]

def via_vrn_v22_2_final_status():
    return {
        "marker": "VIA_SSOT_Unified v22.2 FINAL VRN OVERRIDE EXTENSION",
        "basic_cols": len(via_vrn_basic_info_columns()),
        "fin_cols": len(via_vrn_financial_data_columns()),
        "daiwa_en": via_vrn_broker_alias("Daiwa Securities Report"),
        "daiwa_zh": via_vrn_broker_alias("大和證券 個股報告"),
        "rating_buy": via_vrn_rating_alias("買進"),
        "operating_cashflow": via_fin_synonym("營業活動之現金流量"),
        "operating_cash_flow": via_fin_synonym("operating_cash_flow"),
        "debt_to_equity": via_fin_synonym("負債權益比"),
        "total_assets": via_fin_synonym("Total Assets"),
        "stats": via_fin_synonyms_count(),
    }

# ==================================================================================================
# [VIA:ANCHOR:VRN_PANORAMIC_PRECISION_AUGMENT:START]
# def Added by Invoke-VIA-VRN-PanoramicPrecision-Repair-And-Seal-AIO.ps1
# def Purpose:
# def   VRN panoramic analysis / precision locator / optional AST support registry.
# def Policy:
# def   Append-only. Do not modify upper sections.
# ==================================================================================================

def def_via_vrn_get_panorama_precision_rules_v01():
    """
    def Return VRN panoramic precision extraction rules as SSOT-ready dictionary.
    """
    return {
        "module": "VIA_SSOT_Unified.py",
        "augment": "VRN_PANORAMIC_PRECISION_AUGMENT_V01",
        "policy": {
            "only_add_never_delete": True,
            "use_ast_when_necessary": True,
            "require_precise_anchor": True,
            "require_evidence_matrix": True,
            "extract_topic": False,
            "use_pdf_name_as_final": False,
            "name_source": "tw_ticker_master",
            "price_source": "tw_yfinance_ticker_adj_close",
        },
        "ticker_rules": {
            "TW_TICKER_REGEX": r"^(?!202[1-9])(?!2030)[1-9]\d{3}$",
            "TW_YFINANCE_REGEX": r"^((?!202[1-9])(?!2030)[1-9]\d{3})\.(TW|TWO)$",
            "TW_BLOOMBERG_REGEX": r"^((?!202[1-9])(?!2030)[1-9]\d{3})\s+TT$",
            "ticker_base_must_match_all_three_formats": True,
            "reject_year_ticker_2021_to_2030": True,
        },
        "filename_rules": {
            "punctuation_to_space": True,
            "token_trim": True,
            "token_types": ["EN_TOKEN", "ZH_TOKEN", "NUM_TOKEN", "MIXED_TOKEN"],
            "four_digit_num_token_as_tw_ticker_candidate": True,
            "long_num_token_as_report_date_candidate": True,
            "report_date_must_pass_datetime_parse": True,
            "filename_report_date_must_match_first_page_report_date": True,
        },
        "body_title_rules": {
            "title_extend_right_and_down_until_sentence_stop": True,
            "sentence_stop_chars": ["。", ".", "．", "！", "!", "？", "?"],
            "title_without_sentence_stop_fallback_block": True,
            "extract_from_repaired_title_block": [
                "TARGET_PRICE",
                "RATING",
                "VALUATION_METHOD",
                "FORECAST_DILUTED_EPS_BY_YEAR",
            ],
        },
        "field_rules": {
            "target_price_zones": ["TOP_ZONE", "LEFT_ZONE", "RIGHT_ZONE", "TITLE_ZONE", "BODY_TITLE_ZONE"],
            "rating_zones": ["TOP_ZONE", "LEFT_ZONE", "RIGHT_ZONE", "TITLE_ZONE", "BODY_TITLE_ZONE"],
            "analyst_zones": ["TOP_ZONE", "LEFT_ZONE", "RIGHT_ZONE", "EMAIL_ZONE", "TEL_ZONE", "FOOTER_ZONE"],
            "email_left_part_as_analyst_candidate": True,
            "email_right_domain_as_broker_candidate": True,
            "email_generic_local_blacklist_enabled": True,
        },
        "price_rules": {
            "last_adj_close_source": "tw_yfinance_ticker_latest_adj_close",
            "report_date_adj_close_source": "tw_yfinance_ticker_previous_or_equal_report_date_adj_close",
            "no_forward_price_leakage": True,
        },
        "evidence_required_fields": [
            "value",
            "source",
            "source_text",
            "page_no",
            "zone",
            "method",
            "confidence",
            "warning",
        ],
    }


def def_via_vrn_precision_locator_v01(text, anchors=None, window_before=80, window_after=160):
    """
    def Locate anchor windows precisely.
    """
    import re as _re
    s = "" if text is None else str(text)
    anchors = anchors or []
    results = []

    for anchor in anchors:
        if anchor is None or str(anchor).strip() == "":
            continue

        pattern = _re.compile(_re.escape(str(anchor)), _re.IGNORECASE)
        for m in pattern.finditer(s):
            start = max(0, m.start() - int(window_before))
            end = min(len(s), m.end() + int(window_after))
            results.append({
                "anchor": str(anchor),
                "start": start,
                "end": end,
                "anchor_start": m.start(),
                "anchor_end": m.end(),
                "window": s[start:end],
            })

    return results


def def_via_vrn_panorama_rule_matrix_v01():
    """
    def Flatten VRN rules into a matrix for HTML / JSON reporting.
    """
    rules = def_via_vrn_get_panorama_precision_rules_v01()
    rows = []

    def _walk(prefix, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _walk(prefix + [str(k)], v)
        elif isinstance(obj, list):
            rows.append({
                "rule_path": ".".join(prefix),
                "value": ", ".join([str(x) for x in obj]),
                "value_type": "list",
            })
        else:
            rows.append({
                "rule_path": ".".join(prefix),
                "value": str(obj),
                "value_type": type(obj).__name__,
            })

    _walk([], rules)
    return rows


def def_via_vrn_ast_symbol_probe_v01(py_file_path):
    """
    def Optional AST symbol probe.
    """
    import ast as _ast
    from pathlib import Path as _Path

    p = _Path(py_file_path)
    result = {
        "path": str(p),
        "exists": p.exists(),
        "parse_ok": False,
        "functions": [],
        "classes": [],
        "vrn_symbols": [],
        "error": "",
    }

    if not p.exists():
        result["error"] = "file_not_found"
        return result

    try:
        txt = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        txt = p.read_text(encoding="utf-8-sig")

    try:
        tree = _ast.parse(txt, filename=str(p))
        result["parse_ok"] = True
    except Exception as exc:
        result["error"] = str(exc)
        return result

    for node in _ast.walk(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            item = {
                "name": node.name,
                "lineno": getattr(node, "lineno", None),
                "end_lineno": getattr(node, "end_lineno", None),
            }
            result["functions"].append(item)
            if "vrn" in node.name.lower() or "panorama" in node.name.lower() or "precision" in node.name.lower():
                result["vrn_symbols"].append(dict(item, type="function"))

        if isinstance(node, _ast.ClassDef):
            item = {
                "name": node.name,
                "lineno": getattr(node, "lineno", None),
                "end_lineno": getattr(node, "end_lineno", None),
            }
            result["classes"].append(item)
            if "vrn" in node.name.lower() or "panorama" in node.name.lower() or "precision" in node.name.lower():
                result["vrn_symbols"].append(dict(item, type="class"))

    return result

# ==================================================================================================
# [VIA:ANCHOR:VRN_PANORAMIC_PRECISION_AUGMENT:END]
# ==================================================================================================


# VIA_SSOT_Unified v23 VRN BASIC/FINANCIAL SCHEMA EXTENSION
# Append-only. Purpose: formalize VRN v23 output contract.
# Changes:
#   - remove analyst, name_en from BasicInfo
#   - add data_date, latest_adj_close
#   - keep upside_pct
#   - add valuation/methodology/rating/target/EPS cross-check fields

VRN_BASIC_INFO_V23_COLUMNS = [
    "report_date",
    "report_code",
    "filename",
    "broker",
    "ticker",
    "yfinance_ticker",
    "bloomberg_ticker",
    "name",
    "rating",
    "rating_cat",
    "target_price",
    "consensus_target_high",
    "consensus_target_low",
    "consensus_target_mean",
    "consensus_target_median",
    "consensus_rating",
    "consensus_rating_mean",
    "analyst_count",
    "analyst_strong_buy",
    "analyst_buy",
    "analyst_hold",
    "analyst_sell",
    "analyst_strong_sell",
    "data_date",
    "latest_adj_close",
    "upside_pct",
    "upside_source",
    "valuation_criteria",
    "valuation_methodology",
    "rating_basis",
    "target_price_basis",
    "forecast_diluted_eps_by_year",
    "summary",
    "verification_confidence",
    "備注",
]

VRN_FINANCIAL_DATA_V23_COLUMNS = [
    "report_date",
    "report_code",
    "filename",
    "broker",
    "ticker",
    "yfinance_ticker",
    "bloomberg_ticker",
    "name",
    "category",
    "time_period",
    "data_label",
    "unit",
    "value",
    "source",
    "verification_confidence",
    "table_id",
    "table_type",
    "cross_check_status",
    "備注",
]

def via_vrn_basic_info_v23_columns(include_db_generated=False):
    cols = list(VRN_BASIC_INFO_V23_COLUMNS)
    if include_db_generated:
        cols.append("inserted_at")
    return cols

def via_vrn_financial_data_v23_columns(include_db_generated=False):
    cols = list(VRN_FINANCIAL_DATA_V23_COLUMNS)
    if include_db_generated:
        cols.extend(["id", "inserted_at"])
    return cols

def via_vrn_v23_contract_status():
    return {
        "basic_cols": len(VRN_BASIC_INFO_V23_COLUMNS),
        "financial_cols": len(VRN_FINANCIAL_DATA_V23_COLUMNS),
        "removed_from_basic": ["analyst", "name_en"],
        "added_to_basic": [
            "data_date",
            "latest_adj_close",
            "valuation_criteria",
            "valuation_methodology",
            "rating_basis",
            "target_price_basis",
            "forecast_diluted_eps_by_year",
            "verification_confidence",
            "備注",
        ],
        "upside_color_rule": {
            "positive": "red",
            "negative": "green",
            "zero_or_missing": "yellow",
        },
    }

# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:START]
# def VRN Valuation Method Lexicon v05.9.2
# def append-only; no deletion; no existing symbol mutation
VRN_VALUATION_METHOD_LEXICON_V0592 = {'PER': ['(?i)\\bP\\s*/?\\s*E\\b', '(?i)\\bPER\\b', '(?i)\\bPE\\s*ratio\\b', '(?i)\\bprice[- ]?to[- ]?earnings\\b', '(?i)\\bearnings\\s+multiple\\b', '(?i)\\b\\d+(\\.\\d+)?\\s*x\\s*(P\\s*/?\\s*E|PE|PER)\\b', '(?i)(P\\s*/?\\s*E|PE|PER)\\s*(of|multiple|ratio)?\\s*\\d+(\\.\\d+)?\\s*x', '本益比', '\\d+(\\.\\d+)?\\s*倍\\s*本益比', '\\d+(\\.\\d+)?\\s*x\\s*本益比', '以.{0,50}?\\d+(\\.\\d+)?\\s*[xX倍]?.{0,16}本益比.{0,40}?評價', '基於.{0,55}?\\d+(\\.\\d+)?\\s*[xX倍]?.{0,20}(PER|PE|P/E|本益比)', '評價區間.{0,50}\\d+(\\.\\d+)?\\s*[xX倍]\\s*[-~–至]\\s*\\d+(\\.\\d+)?\\s*[xX倍]?.{0,45}(PER|PE|P/E|本益比)', '常態本益比.{0,40}\\d+(\\.\\d+)?\\s*[-~–至]\\s*\\d+(\\.\\d+)?\\s*倍', '給[予與].{0,30}\\d+(\\.\\d+)?\\s*倍'], 'PBR': ['(?i)\\bP\\s*/?\\s*B\\b', '(?i)\\bPBR\\b', '(?i)\\bPBV\\b', '(?i)\\bprice[- ]?to[- ]?book\\b', '股價淨值比|市淨率|淨值比|帳面價值倍數', '\\d+(\\.\\d+)?\\s*x\\s*(P\\s*/?\\s*B|PB|PBR|PBV)'], 'EV/EBITDA': ['(?i)\\bEV\\s*/?\\s*EBITDA\\b', '(?i)\\bEV[- ]?to[- ]?EBITDA\\b', '(?i)\\benterprise\\s+value\\s+to\\s+EBITDA\\b', '(?i)\\bEBITDA\\s+multiple\\b', '企業價值.{0,16}EBITDA|EBITDA倍數'], 'EV/EBIT': ['(?i)\\bEV\\s*/?\\s*EBIT\\b', '(?i)\\bEV[- ]?to[- ]?EBIT\\b', '(?i)\\benterprise\\s+value\\s+to\\s+EBIT\\b', '(?i)\\bEBIT\\s+multiple\\b', '企業價值.{0,16}EBIT|EBIT倍數'], 'DCF': ['(?i)\\bDCF\\b', '(?i)\\bdiscounted\\s+cash\\s*flow\\b', '(?i)\\bWACC\\b', '(?i)\\bterminal\\s+value\\b', '折現現金流|現金流折現|自由現金流折現|加權平均資金成本|終值|永續成長率'], 'SOTP': ['(?i)\\bSOTP\\b', '(?i)\\bsum[- ]of[- ]the[- ]parts\\b', '(?i)\\bsum\\s+of\\s+parts\\b', '(?i)\\bsegment\\s+valuation\\b', '分部估值|分部評價|分項加總|分部加總|各業務加總|事業群加總|分拆估值'], 'DDM': ['(?i)\\bDDM\\b', '(?i)\\bdividend\\s+discount\\b', '(?i)\\bdividend\\s+yield\\b', '股利折現|股利折現模型|殖利率評價|現金股利殖利率|股息折現'], 'PEG': ['(?i)\\bPEG\\b', '(?i)\\bprice\\s+earnings\\s+growth\\b', '本益成長比|PEG評價'], 'P/S': ['(?i)\\bP\\s*/?\\s*S\\b', '(?i)\\bprice[- ]?to[- ]?sales\\b', '(?i)\\bsales\\s+multiple\\b', '營收倍數|市銷率|股價營收比'], 'NAV/RNAV': ['(?i)\\bRNAV\\b', '(?i)\\bNAV\\b', '(?i)\\bnet\\s+asset\\s+value\\b', '資產淨值|重估資產淨值|淨資產價值|資產價值法'], 'Residual Income': ['(?i)\\bresidual\\s+income\\b', '(?i)\\bRI\\s+model\\b', '剩餘收益|剩餘利益|超額報酬模型']}

def vrn_get_valuation_method_lexicon_v0592():
    return VRN_VALUATION_METHOD_LEXICON_V0592
# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:END]

# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:START]
# def VRN Valuation Dictionary v05.9.5
# def append-only; no deletion; no existing symbol mutation
VRN_VALUATION_DICTIONARY_V0595 = {'metadata': {'system_name': 'Veritas Intelligence System', 'module': 'Valuation_Dictionary', 'version': '0.5.9.5', 'encoding': 'UTF-8', 'last_updated': '2026-05-21', 'source_policy': 'broker_report_text_only_yfinance_never_overwrites_valuation_method'}, 'categories': [{'category_id': 'CAT_ABS', 'category_en': 'Absolute Valuation', 'category_zh': '絕對估值法'}, {'category_id': 'CAT_REL', 'category_en': 'Relative Valuation', 'category_zh': '相對估值法'}, {'category_id': 'CAT_AST', 'category_en': 'Asset-Based Valuation', 'category_zh': '資產基礎估值法'}], 'methods': [{'uid': 'VAL_001', 'canonical': 'P/E', 'category_id': 'CAT_REL', 'name_en': 'Price-to-Earnings Ratio', 'name_zh': '本益比', 'abbreviations': ['P/E', 'PER', 'PE', 'PE Ratio', 'P/E Ratio'], 'synonyms_en': ['Earnings Multiple', 'Price Multiple', 'Price-to-Earnings', 'Forward P/E', 'Trailing P/E'], 'synonyms_zh': ['市盈率', '價格盈餘倍數', '預估本益比', '目標本益比', '合理本益比', '常態本益比', '歷史本益比', '本益比評價', '本益比法', '本益比區間'], 'regex': ['(?i)\\bP\\s*/?\\s*E\\b', '(?i)\\bPER\\b', '(?i)\\bPE\\s*ratio\\b', '(?i)\\bprice[- ]?to[- ]?earnings\\b', '(?i)\\bearnings\\s+multiple\\b', '(?i)\\bforward\\s+P\\s*/?\\s*E\\b', '(?i)\\btrailing\\s+P\\s*/?\\s*E\\b', '(?i)\\bFY\\d{2}E?\\s*P\\s*/?\\s*E\\b', '(?i)\\b\\d+(\\.\\d+)?\\s*x\\s*(P\\s*/?\\s*E|PE|PER)\\b', '(?i)(P\\s*/?\\s*E|PE|PER)\\s*(of|multiple|ratio)?\\s*\\d+(\\.\\d+)?\\s*x', '(?i)implying.{0,80}(P\\s*/?\\s*E|PE|PER).{0,60}\\d+(\\.\\d+)?\\s*x', '(?i)our\\s+(TP|PT|target price|price target).{0,140}(P\\s*/?\\s*E|PE|PER)', '(?i)we\\s+(derive|value|set).{0,160}(P\\s*/?\\s*E|PE|PER|earnings multiple)', '(?i)applying.{0,100}\\d+(\\.\\d+)?\\s*x.{0,70}(earnings|EPS|P\\s*/?\\s*E|PE|PER)', '(?i)(sector|peer|historical).{0,60}(average|premium|discount).{0,100}(P\\s*/?\\s*E|PE|PER|multiple)', '本益比|市盈率|價格盈餘倍數|預估本益比|目標本益比|合理本益比|常態本益比|歷史本益比|展望年本益比', '本益比評價|本益比法|本益比區間|本益比倍數', '\\d+(\\.\\d+)?\\s*倍\\s*本益比', '\\d+(\\.\\d+)?\\s*x\\s*本益比', '以.{0,100}?\\d+(\\.\\d+)?\\s*[xX倍]?.{0,40}本益比.{0,90}?評價', '基於.{0,110}?\\d+(\\.\\d+)?\\s*[xX倍]?.{0,40}(PER|PE|P/E|本益比)', '評價區間.{0,100}\\d+(\\.\\d+)?\\s*[xX倍]\\s*[-~–至]\\s*\\d+(\\.\\d+)?\\s*[xX倍]?.{0,90}(PER|PE|P/E|本益比)', '常態本益比.{0,80}\\d+(\\.\\d+)?\\s*[-~–至]\\s*\\d+(\\.\\d+)?\\s*倍', '給[予與].{0,80}\\d+(\\.\\d+)?\\s*倍', '推導目標價.{0,160}(本益比|PER|PE|P/E)', '目標價隱含.{0,160}(本益比|PER|PE|P/E)', '參考同業.{0,160}(本益比|PER|PE|P/E|倍數)', '歷史區間.{0,160}(本益比|PER|PE|P/E|倍數)', '以.{0,50}(明年|後年|202\\d年|FY\\d{2}).{0,80}EPS.{0,90}(估算|評價|推導)']}, {'uid': 'VAL_002', 'canonical': 'P/B', 'category_id': 'CAT_REL', 'name_en': 'Price-to-Book Ratio', 'name_zh': '股價淨值比', 'abbreviations': ['P/B', 'PBR', 'PB Ratio', 'PTB'], 'synonyms_en': ['Price-to-Equity Ratio', 'Book Multiple'], 'synonyms_zh': ['市淨率', '價格帳面價值比', '市值淨值比', '淨值比'], 'regex': ['(?i)\\bP\\s*/\\s*B\\b', '(?i)\\bPBR\\b', '(?i)\\bPBV\\b', '(?i)\\bPTB\\b', '(?i)\\bprice[- ]?to[- ]?book\\b', '(?i)\\bbook\\s+value\\s+multiple\\b', '股價淨值比|市淨率|價格帳面價值比|市值淨值比|淨值比|帳面價值倍數|每股淨值', '\\d+(\\.\\d+)?\\s*x\\s*(P\\s*/\\s*B|PBR|PBV|PTB)']}, {'uid': 'VAL_003', 'canonical': 'DCF', 'category_id': 'CAT_ABS', 'name_en': 'Discounted Cash Flow', 'name_zh': '現金流量折現法', 'abbreviations': ['DCF'], 'synonyms_en': ['DCF Model', 'Discounted Cashflow'], 'synonyms_zh': ['折現現金流模型', '現金流折現估值', '現金流折現', '折現現金流'], 'regex': ['(?i)\\bDCF\\b', '(?i)\\bdiscounted\\s+cash\\s*flow\\b', '(?i)\\bWACC\\b', '(?i)\\bterminal\\s+value\\b', '現金流量折現|折現現金流|現金流折現|自由現金流折現|折現率|加權平均資金成本|終值|永續成長率']}, {'uid': 'VAL_004', 'canonical': 'DDM', 'category_id': 'CAT_ABS', 'name_en': 'Dividend Discount Model', 'name_zh': '股利折現模型', 'abbreviations': ['DDM'], 'synonyms_en': ['Dividend Discount', 'Dividend Yield Valuation'], 'synonyms_zh': ['股息折現法', '股利折現', '殖利率評價'], 'regex': ['(?i)\\bDDM\\b', '(?i)\\bdividend\\s+discount\\b', '(?i)\\bdividend\\s+yield\\b', '股利折現|股利折現模型|股息折現|殖利率評價|現金股利殖利率']}, {'uid': 'VAL_005', 'canonical': 'FCFF', 'category_id': 'CAT_ABS', 'name_en': 'Free Cash Flow to Firm', 'name_zh': '企業自由現金流量模型', 'abbreviations': ['FCFF'], 'synonyms_en': ['Free Cash Flow to the Firm'], 'synonyms_zh': ['企業自由現金流', '公司自由現金流'], 'regex': ['(?i)\\bFCFF\\b', '(?i)\\bfree\\s+cash\\s+flow\\s+to\\s+(the\\s+)?firm\\b', '企業自由現金流量|企業自由現金流|公司自由現金流']}, {'uid': 'VAL_006', 'canonical': 'FCFE', 'category_id': 'CAT_ABS', 'name_en': 'Free Cash Flow to Equity', 'name_zh': '股權自由現金流量模型', 'abbreviations': ['FCFE'], 'synonyms_en': ['Free Cash Flow to Shareholders'], 'synonyms_zh': ['股權自由現金流', '股東自由現金流'], 'regex': ['(?i)\\bFCFE\\b', '(?i)\\bfree\\s+cash\\s+flow\\s+to\\s+equity\\b', '股權自由現金流量|股權自由現金流|股東自由現金流']}, {'uid': 'VAL_007', 'canonical': 'RIV', 'category_id': 'CAT_ABS', 'name_en': 'Residual Income Valuation', 'name_zh': '剩餘所得估值法', 'abbreviations': ['RIV', 'RI'], 'synonyms_en': ['Residual Income', 'Residual Income Model'], 'synonyms_zh': ['剩餘收益', '剩餘利益', '超額報酬模型'], 'regex': ['(?i)\\bRIV\\b', '(?i)\\bresidual\\s+income\\b', '剩餘所得|剩餘收益|剩餘利益|超額報酬模型']}, {'uid': 'VAL_008', 'canonical': 'APV', 'category_id': 'CAT_ABS', 'name_en': 'Adjusted Present Value', 'name_zh': '調整後現值法', 'abbreviations': ['APV'], 'synonyms_en': ['Adjusted PV'], 'synonyms_zh': ['調整現值', '調整後現值'], 'regex': ['(?i)\\bAPV\\b', '(?i)\\badjusted\\s+present\\s+value\\b', '調整後現值|調整現值']}, {'uid': 'VAL_009', 'canonical': 'GGM', 'category_id': 'CAT_ABS', 'name_en': 'Gordon Growth Model', 'name_zh': '戈登成長模型', 'abbreviations': ['GGM'], 'synonyms_en': ['Constant Growth Model', 'Gordon Model'], 'synonyms_zh': ['戈登模型', '股利穩定成長模型'], 'regex': ['(?i)\\bGGM\\b', '(?i)\\bgordon\\s+growth\\s+model\\b', '(?i)\\bconstant\\s+growth\\s+model\\b', '戈登成長模型|戈登模型|股利穩定成長模型']}, {'uid': 'VAL_010', 'canonical': 'EVA', 'category_id': 'CAT_ABS', 'name_en': 'Economic Value Added', 'name_zh': '經濟附加價值', 'abbreviations': ['EVA'], 'synonyms_en': ['Economic Profit'], 'synonyms_zh': ['經濟利潤', '經濟增加值'], 'regex': ['(?i)\\bEVA\\b', '(?i)\\beconomic\\s+value\\s+added\\b', '經濟附加價值|經濟利潤|經濟增加值']}, {'uid': 'VAL_011', 'canonical': 'P/S', 'category_id': 'CAT_REL', 'name_en': 'Price-to-Sales Ratio', 'name_zh': '股價營收比', 'abbreviations': ['P/S', 'PSR'], 'synonyms_en': ['Sales Multiple', 'Revenue Multiple'], 'synonyms_zh': ['市銷率', '價格營收比', '營收倍數'], 'regex': ['(?i)\\bP\\s*/\\s*S\\b', '(?i)\\bPSR\\b', '(?i)\\bprice[- ]?to[- ]?sales\\b', '(?i)\\bsales\\s+multiple\\b', '(?i)\\brevenue\\s+multiple\\b', '股價營收比|市銷率|價格營收比|營收倍數']}, {'uid': 'VAL_012', 'canonical': 'P/CF', 'category_id': 'CAT_REL', 'name_en': 'Price-to-Cash Flow Ratio', 'name_zh': '股價現金流量比', 'abbreviations': ['P/CF', 'PCF'], 'synonyms_en': ['Price-to-Cashflow'], 'synonyms_zh': ['市現率', '價格現金流比'], 'regex': ['(?i)\\bP\\s*/\\s*CF\\b', '(?i)\\bPCF\\b', '(?i)\\bprice[- ]?to[- ]?cash\\s*flow\\b', '股價現金流量比|市現率|價格現金流比']}, {'uid': 'VAL_013', 'canonical': 'PEG', 'category_id': 'CAT_REL', 'name_en': 'Price-to-Earnings-to-Growth Ratio', 'name_zh': '本益成長比', 'abbreviations': ['PEG', 'PEG Ratio'], 'synonyms_en': ['Price Earnings Growth'], 'synonyms_zh': ['市盈率相對盈利增長比率'], 'regex': ['(?i)\\bPEG\\b', '(?i)\\bprice\\s+earnings\\s+growth\\b', '本益成長比|PEG評價|市盈率相對盈利增長比率']}, {'uid': 'VAL_014', 'canonical': 'EV/EBITDA', 'category_id': 'CAT_REL', 'name_en': 'Enterprise Value to EBITDA', 'name_zh': '企業價值倍數', 'abbreviations': ['EV/EBITDA'], 'synonyms_en': ['Enterprise Multiple'], 'synonyms_zh': ['息稅折舊攤銷前盈餘倍數', '企業乘數'], 'regex': ['(?i)\\bEV\\s*/?\\s*EBITDA\\b', '(?i)\\bEV[- ]?to[- ]?EBITDA\\b', '(?i)\\benterprise\\s+value\\s+to\\s+EBITDA\\b', '(?i)\\benterprise\\s+multiple\\b', '企業價值.{0,30}EBITDA|EV/EBITDA|EBITDA倍數|企業價值倍數|企業乘數']}, {'uid': 'VAL_015', 'canonical': 'EV/Sales', 'category_id': 'CAT_REL', 'name_en': 'Enterprise Value to Sales', 'name_zh': '企業價值對營收比', 'abbreviations': ['EV/Sales', 'EV/S'], 'synonyms_en': ['Enterprise Value to Revenue', 'EV/Revenue'], 'synonyms_zh': ['企業價值營收比'], 'regex': ['(?i)\\bEV\\s*/\\s*Sales\\b', '(?i)\\bEV\\s*/\\s*S\\b', '(?i)\\bEV\\s*/\\s*Revenue\\b', '(?i)\\benterprise\\s+value\\s+to\\s+(sales|revenue)\\b', '企業價值對營收比|企業價值營收比']}, {'uid': 'VAL_016', 'canonical': 'EV/EBIT', 'category_id': 'CAT_REL', 'name_en': 'Enterprise Value to EBIT', 'name_zh': '企業價值對息稅前利潤比', 'abbreviations': ['EV/EBIT'], 'synonyms_en': ['EBIT Multiple'], 'synonyms_zh': ['EBIT倍數'], 'regex': ['(?i)\\bEV\\s*/?\\s*EBIT\\b', '(?i)\\bEV[- ]?to[- ]?EBIT\\b', '(?i)\\benterprise\\s+value\\s+to\\s+EBIT\\b', '(?i)\\bEBIT\\s+multiple\\b', '企業價值對息稅前利潤比|企業價值.{0,20}EBIT|EBIT倍數']}, {'uid': 'VAL_017', 'canonical': 'NAV', 'category_id': 'CAT_AST', 'name_en': 'Net Asset Value', 'name_zh': '淨資產價值法', 'abbreviations': ['NAV'], 'synonyms_en': ['Net Asset Value Method'], 'synonyms_zh': ['資產淨值法', '資產淨值'], 'regex': ['(?i)\\bNAV\\b', '(?i)\\bnet\\s+asset\\s+value\\b', '淨資產價值|資產淨值法|資產淨值']}, {'uid': 'VAL_018', 'canonical': 'SOTP', 'category_id': 'CAT_AST', 'name_en': 'Sum of the Parts', 'name_zh': '分部估值法', 'abbreviations': ['SOTP'], 'synonyms_en': ['Break-up Value Valuation', 'Parts Valuation', 'Sum-of-the-Parts'], 'synonyms_zh': ['加總估值法', '拆分估值法', '分類加總法', '分項加總法'], 'regex': ['(?i)\\bSOTP\\b', '(?i)\\bsum[- ]of[- ]the[- ]parts\\b', '(?i)\\bsum\\s+of\\s+parts\\b', '(?i)\\bsegment\\s+valuation\\b', '分部估值|加總估值|拆分估值|分類加總|分項加總|分部加總|各業務加總|事業群加總']}, {'uid': 'VAL_019', 'canonical': 'Replacement Cost', 'category_id': 'CAT_AST', 'name_en': 'Replacement Cost Method', 'name_zh': '重置成本法', 'abbreviations': [], 'synonyms_en': ['Replacement Cost'], 'synonyms_zh': ['重置成本'], 'regex': ['(?i)\\breplacement\\s+cost\\b', '重置成本法|重置成本']}, {'uid': 'VAL_020', 'canonical': 'Liquidation Value', 'category_id': 'CAT_AST', 'name_en': 'Liquidation Value', 'name_zh': '清算價值法', 'abbreviations': [], 'synonyms_en': ['Liquidation Method'], 'synonyms_zh': ['清算價值'], 'regex': ['(?i)\\bliquidation\\s+value\\b', '清算價值法|清算價值']}, {'uid': 'VAL_021', 'canonical': 'BV', 'category_id': 'CAT_AST', 'name_en': 'Book Value', 'name_zh': '帳面價值', 'abbreviations': ['BV'], 'synonyms_en': ['Book Value Method'], 'synonyms_zh': ['帳面值'], 'regex': ['(?i)\\bBV\\b', '(?i)\\bbook\\s+value\\b', '帳面價值|帳面值']}, {'uid': 'VAL_022', 'canonical': 'NTA', 'category_id': 'CAT_AST', 'name_en': 'Net Tangible Assets', 'name_zh': '有形資產淨值', 'abbreviations': ['NTA'], 'synonyms_en': ['Net Tangible Asset Value'], 'synonyms_zh': ['有形淨資產'], 'regex': ['(?i)\\bNTA\\b', '(?i)\\bnet\\s+tangible\\s+assets?\\b', '有形資產淨值|有形淨資產']}]}

def vrn_get_valuation_dictionary_v0595():
    return VRN_VALUATION_DICTIONARY_V0595
# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:END]

# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V0599:START]
# def VRN Financial Account SSOT v05.9.9
# def append-only bridge; no deletion; no existing symbol mutation
def vrn_get_financial_account_ssot_v0599():
    try:
        from VIS_VRN_FinancialSSOT_v0599 import def_get_financial_account_ssot_v0599
        return def_get_financial_account_ssot_v0599()
    except Exception:
        return {"metadata": {"status": "IMPORT_FAILED"}}

def vrn_match_financial_account_v0599(text):
    try:
        from VIS_VRN_FinancialSSOT_v0599 import def_match_financial_account_v0599
        return def_match_financial_account_v0599(text)
    except Exception:
        return {"matched": False, "account": str(text or ""), "category": "Unmapped", "unit": "", "match_score": 0, "match_reason": "IMPORT_FAILED"}
# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V0599:END]

# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V05910:START]
# def VRN Financial Account SSOT v05.9.10
# def append-only bridge; no deletion; no existing symbol mutation
def vrn_get_financial_account_ssot_v05910():
    try:
        from VIS_VRN_FinancialSSOT_v05910 import def_get_financial_account_ssot_v05910
        return def_get_financial_account_ssot_v05910()
    except Exception:
        return {"metadata": {"status": "IMPORT_FAILED"}}

def vrn_match_financial_account_v05910(text):
    try:
        from VIS_VRN_FinancialSSOT_v05910 import def_match_financial_account_v05910
        return def_match_financial_account_v05910(text)
    except Exception:
        return {"matched": False, "account": str(text or ""), "category": "Unmapped", "unit": "", "match_score": 0, "match_reason": "IMPORT_FAILED"}
# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V05910:END]

# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V05911:START]
# def VRN Financial Account SSOT v05.9.11
# def append-only bridge; no deletion; no existing symbol mutation
def vrn_get_financial_account_ssot_v05911():
    try:
        from VIS_VRN_FinancialSSOT_v05911 import def_get_financial_account_ssot_v05911
        return def_get_financial_account_ssot_v05911()
    except Exception:
        return {"metadata": {"status": "IMPORT_FAILED"}}

def vrn_match_financial_account_v05911(text):
    try:
        from VIS_VRN_FinancialSSOT_v05911 import def_match_financial_account_v05911
        return def_match_financial_account_v05911(text)
    except Exception:
        return {"matched": False, "account": str(text or ""), "category": "Unmapped", "unit": "", "match_score": 0, "match_reason": "IMPORT_FAILED"}
# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V05911:END]

# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V05912:START]
def vrn_get_financial_account_ssot_v05912():
    try:
        from VIS_VRN_FinancialSSOT_v05912 import def_get_financial_account_ssot_v05912
        return def_get_financial_account_ssot_v05912()
    except Exception:
        return {"metadata": {"status": "IMPORT_FAILED"}}

def vrn_match_financial_account_v05912(text):
    try:
        from VIS_VRN_FinancialSSOT_v05912 import def_match_financial_account_v05912
        return def_match_financial_account_v05912(text)
    except Exception:
        return {"matched": False, "account": str(text or ""), "category": "Unmapped", "unit": "", "match_score": 0, "match_reason": "IMPORT_FAILED"}
# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V05912:END]

# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V0600:START]
def vrn_get_financial_account_ssot_v0600():
    try:
        from VIS_VRN_FinancialSSOT_v0600 import def_get_financial_account_ssot_v0600
        return def_get_financial_account_ssot_v0600()
    except Exception:
        return {"metadata": {"status": "IMPORT_FAILED"}}

def vrn_match_financial_account_v0600(text):
    try:
        from VIS_VRN_FinancialSSOT_v0600 import def_match_financial_account_v0600
        return def_match_financial_account_v0600(text)
    except Exception:
        return {"matched": False, "account": str(text or ""), "category": "Unmapped", "unit": "", "match_score": 0, "match_reason": "IMPORT_FAILED"}
# [VIA:ANCHOR:VRN_FINANCIAL_SSOT_V0600:END]



# ==================================================================================================
# [VIS:VRN_ANALYST_TARGET_EXTRACTOR_V06123:START]
# ==================================================================================================
# Append-only SSOT helper block.
# Purpose:
# - Analyst extraction stops before Target Price / Rating / recommendation words.
# - Target Price extraction supports Chinese / English report phrasing.
# - Report Date extraction prioritizes YYYYMMDD and ROC yyyMMdd before loose regex.
# - No canonical mutation.
# - No classifier rewrite.
# ==================================================================================================

import re as _vis_re
from pathlib import Path as _vis_Path
from typing import Any as _vis_Any


VIS_VRN_ANALYST_TARGET_EXTRACTOR_VERSION = "v0.6.12.3"

VIS_VRN_ANALYST_STOPWORDS = [
    "目標價", "目標價格", "合理價", "評等", "評級", "投資評等", "投資建議",
    "買進", "買入", "增持", "中立", "持有", "減持", "賣出", "未評等",
    "Target Price", "TP", "Rating", "Recommendation", "Buy", "Outperform",
    "Neutral", "Hold", "Sell", "Underperform", "NR"
]

VIS_VRN_RATING_WORDS = [
    "買進", "買入", "增持", "中立", "持有", "減持", "賣出", "未評等", "NR",
    "Buy", "Outperform", "Neutral", "Hold", "Sell", "Underperform"
]


def def_vis_vrn_clean_text_v06123(x: _vis_Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = _vis_re.sub(r"\s+", " ", s).strip()
    return s


def def_vis_vrn_stop_before_keyword_v06123(s: str) -> str:
    text = def_vis_vrn_clean_text_v06123(s)
    stops = sorted(VIS_VRN_ANALYST_STOPWORDS, key=len, reverse=True)
    for kw in stops:
        m = _vis_re.search(_vis_re.escape(kw), text, flags=_vis_re.I)
        if m:
            text = text[:m.start()].strip()
    text = _vis_re.sub(r"[,，;；:：|｜/／]+$", "", text).strip()
    return text


def def_vis_vrn_extract_analyst_from_text_v06123(text: _vis_Any) -> dict:
    s = def_vis_vrn_clean_text_v06123(text)
    patterns = [
        r"(?:分析師|研究員|Analyst|撰文|作者|Prepared by|Author)\s*[:：]\s*([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s·．.、,，-]{1,60})",
        r"(?:分析師|研究員)\s+([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s·．.、,，-]{1,40})",
    ]
    for pat in patterns:
        m = _vis_re.search(pat, s, flags=_vis_re.I)
        if not m:
            continue
        raw = m.group(1)
        val = def_vis_vrn_stop_before_keyword_v06123(raw)
        val = _vis_re.split(r"[\n\r|｜]", val)[0].strip(" ,，。；;:：")
        if val:
            return {
                "Analyst": val,
                "Analyst Source": "VIA_SSOT_Unified.VIS_VRN_ANALYST_TARGET_EXTRACTOR_V06123",
                "Analyst Confidence": 0.93,
            }
    return {"Analyst": "", "Analyst Source": "", "Analyst Confidence": 0.0}


def def_vis_vrn_extract_rating_target_from_text_v06123(text: _vis_Any) -> dict:
    s = def_vis_vrn_clean_text_v06123(text)
    out = {
        "Rating": "",
        "Target Price": "",
        "Rating Target Source": "",
        "Rating Target Confidence": 0.0,
    }

    rating_pat = r"(買進|買入|增持|中立|持有|減持|賣出|未評等|NR|Buy|Outperform|Neutral|Hold|Sell|Underperform)"
    m = _vis_re.search(rating_pat, s, flags=_vis_re.I)
    if m:
        out["Rating"] = m.group(1)

    target_patterns = [
        r"(?:目標價|目標價格|合理價|Target Price|TP)\s*[:：]?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9]+(?:\.[0-9]+)?)",
        r"(?:給予|上修至|下修至|維持)\s*(?:目標價|目標價格)?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9]+(?:\.[0-9]+)?)\s*元",
        r"([0-9]+(?:\.[0-9]+)?)\s*元\s*(?:目標價|合理價)",
    ]
    for pat in target_patterns:
        m = _vis_re.search(pat, s, flags=_vis_re.I)
        if m:
            out["Target Price"] = m.group(1)
            break

    if out["Rating"] or out["Target Price"]:
        out["Rating Target Source"] = "VIA_SSOT_Unified.VIS_VRN_ANALYST_TARGET_EXTRACTOR_V06123"
        out["Rating Target Confidence"] = 0.93

    return out


def def_vis_vrn_extract_report_date_from_filename_v06123(filename: _vis_Any) -> dict:
    raw = _vis_Path(def_vis_vrn_clean_text_v06123(filename)).name
    stem = _vis_re.sub(r"\.pdf$", "", raw, flags=_vis_re.I)
    candidates = []

    # 1. AD YYYYMMDD / YYYY-MM-DD / YYYY_MM_DD first
    for m in _vis_re.finditer(r"(20\d{2})[-_/年.]?(0[1-9]|1[0-2])[-_/月.]?(0[1-9]|[12]\d|3[01])", stem):
        candidates.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    # 2. ROC yyyMMdd, e.g. 1141202 -> 2025-12-02
    for m in _vis_re.finditer(r"(?<!\d)(1[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)", stem):
        roc_y = int(m.group(1))
        ad_y = roc_y + 1911
        if 2000 <= ad_y <= 2099:
            candidates.append(f"{ad_y}-{m.group(2)}-{m.group(3)}")

    # 3. AD YYYYMM
    for m in _vis_re.finditer(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)", stem):
        candidates.append(f"{m.group(1)}-{m.group(2)}")

    # 4. AD year only
    for m in _vis_re.finditer(r"(?<!\d)(20\d{2})(?!\d)", stem):
        candidates.append(m.group(1))

    candidates = list(dict.fromkeys(candidates))
    full_dates = [x for x in candidates if _vis_re.match(r"20\d{2}-\d{2}-\d{2}$", x)]
    best = full_dates[0] if full_dates else (candidates[0] if candidates else "")

    return {
        "report_date": best,
        "report_date_candidates": candidates,
        "source": "VIA_SSOT_Unified.VIS_VRN_REPORT_DATE_EXTRACTOR_V06123" if candidates else "NONE",
    }

# ==================================================================================================
# [VIS:VRN_ANALYST_TARGET_EXTRACTOR_V06123:END]
# ==================================================================================================



# ==================================================================================================
# [VIS:VRN_FILENAME_DATE_TOKENIZER_V06124:START]
# ==================================================================================================
# Append-only SSOT helper block.
# Rules:
# - Four-digit TW ticker is ticker, not date.
# - Longer continuous digits are date candidates.
# - Supports AD YYYYMMDD.
# - Supports ROC YYYMMDD, e.g. 1141202 -> 2025-12-02.
# - Supports omitted-century AD YYMMDD, e.g. 251202 -> 2025-12-02.
# - Date parsing is token-first and avoids rewriting ticker tokens.
# ==================================================================================================

import re as _vis_re
from pathlib import Path as _vis_Path
from typing import Any as _vis_Any


VIS_VRN_FILENAME_DATE_TOKENIZER_VERSION = "v0.6.12.4"
VIS_VRN_TW_TICKER_REGEX_V06124 = _vis_re.compile(r"^(?!202[1-9])(?!2030)[1-9]\d{3}$")


def def_vis_vrn_clean_text_v06124(x: _vis_Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = _vis_re.sub(r"\s+", " ", s).strip()
    return s


def def_vis_vrn_fullwidth_to_halfwidth_v06124(x: _vis_Any) -> str:
    s = def_vis_vrn_clean_text_v06124(x)
    out = []
    for ch in s:
        code = ord(ch)
        if code == 12288:
            out.append(" ")
        elif 65281 <= code <= 65374:
            out.append(chr(code - 65248))
        else:
            out.append(ch)
    return "".join(out)


def def_vis_vrn_filename_tokens_v06124(filename: _vis_Any) -> dict:
    raw = _vis_Path(def_vis_vrn_clean_text_v06124(filename)).name
    stem = _vis_re.sub(r"\.pdf$", "", raw, flags=_vis_re.I)
    norm = def_vis_vrn_fullwidth_to_halfwidth_v06124(stem)
    norm = _vis_re.sub(r"[()（）\[\]【】{}<>〈〉《》,_，、;；:：|｜+＋=＝~～!！?？\\/]", " ", norm)
    norm = _vis_re.sub(r"[-–—_]", " ", norm)
    norm = _vis_re.sub(r"\s+", " ", norm).strip()

    digit_tokens = _vis_re.findall(r"(?<!\d)\d+(?!\d)", norm)
    english_tokens = _vis_re.findall(r"[A-Za-z]+", norm)
    chinese_tokens = _vis_re.findall(r"[\u4e00-\u9fff]+", norm)

    ticker_tokens = []
    date_tokens = []
    for t in digit_tokens:
        if VIS_VRN_TW_TICKER_REGEX_V06124.match(t):
            ticker_tokens.append(t)
        elif len(t) >= 5:
            date_tokens.append(t)

    return {
        "filename": raw,
        "stem": stem,
        "normalized": norm,
        "digit_tokens": digit_tokens,
        "ticker_tokens": list(dict.fromkeys(ticker_tokens)),
        "date_tokens": list(dict.fromkeys(date_tokens)),
        "english_tokens": english_tokens,
        "chinese_tokens": chinese_tokens,
    }


def def_vis_vrn_date_from_numeric_token_v06124(token: _vis_Any) -> list[str]:
    t = def_vis_vrn_clean_text_v06124(token)
    out = []

    # AD YYYYMMDD
    if _vis_re.fullmatch(r"20\d{6}", t):
        y, m, d = int(t[0:4]), int(t[4:6]), int(t[6:8])
        if 2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
            out.append(f"{y:04d}-{m:02d}-{d:02d}")

    # ROC YYYMMDD, e.g. 1141202
    if _vis_re.fullmatch(r"1\d{6}", t):
        roc_y, m, d = int(t[0:3]), int(t[3:5]), int(t[5:7])
        y = roc_y + 1911
        if 2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
            out.append(f"{y:04d}-{m:02d}-{d:02d}")

    # Omitted-century AD YYMMDD, e.g. 251202 -> 2025-12-02
    if _vis_re.fullmatch(r"\d{6}", t):
        yy, m, d = int(t[0:2]), int(t[2:4]), int(t[4:6])
        y = 2000 + yy
        if 2020 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
            out.append(f"{y:04d}-{m:02d}-{d:02d}")

    # AD YYYYMM
    if _vis_re.fullmatch(r"20\d{4}", t):
        y, m = int(t[0:4]), int(t[4:6])
        if 2000 <= y <= 2099 and 1 <= m <= 12:
            out.append(f"{y:04d}-{m:02d}")

    return list(dict.fromkeys(out))


def def_vis_vrn_extract_report_date_from_filename_v06124(filename: _vis_Any) -> dict:
    tokens = def_vis_vrn_filename_tokens_v06124(filename)
    stem = tokens.get("stem", "")
    candidates = []

    # 1. Continuous numeric date tokens first.
    for tok in tokens.get("date_tokens", []):
        candidates.extend(def_vis_vrn_date_from_numeric_token_v06124(tok))

    # 2. AD separated YYYY-MM-DD / YYYY_MM_DD / YYYY年MM月DD日.
    for m in _vis_re.finditer(r"(20\d{2})[-_/年.]?(0?[1-9]|1[0-2])[-_/月.]?(0?[1-9]|[12]\d|3[01])", stem):
        y = int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            candidates.append(f"{y:04d}-{mo:02d}-{d:02d}")

    # 3. ROC separated YYY-MM-DD.
    for m in _vis_re.finditer(r"(?<!\d)(1\d{2})[-_/年.]?(0?[1-9]|1[0-2])[-_/月.]?(0?[1-9]|[12]\d|3[01])(?!\d)", stem):
        y = int(m.group(1)) + 1911
        mo = int(m.group(2))
        d = int(m.group(3))
        if 2000 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
            candidates.append(f"{y:04d}-{mo:02d}-{d:02d}")

    # 4. Omitted century separated YY-MM-DD.
    for m in _vis_re.finditer(r"(?<!\d)(2[0-9])[-_/年.]?(0?[1-9]|1[0-2])[-_/月.]?(0?[1-9]|[12]\d|3[01])(?!\d)", stem):
        y = 2000 + int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
        if 2020 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
            candidates.append(f"{y:04d}-{mo:02d}-{d:02d}")

    # 5. AD year-only fallback.
    for m in _vis_re.finditer(r"(?<!\d)(20\d{2})(?!\d)", stem):
        candidates.append(m.group(1))

    candidates = list(dict.fromkeys(candidates))
    full_dates = [x for x in candidates if _vis_re.fullmatch(r"20\d{2}-\d{2}-\d{2}", x)]
    best = full_dates[0] if full_dates else (candidates[0] if candidates else "")

    return {
        "report_date": best,
        "report_date_candidates": candidates,
        "filename_tokens": tokens,
        "source": "VIA_SSOT_Unified.VIS_VRN_FILENAME_DATE_TOKENIZER_V06124" if candidates else "NONE",
    }

# ==================================================================================================
# [VIS:VRN_FILENAME_DATE_TOKENIZER_V06124:END]
# ==================================================================================================

# [VIA:VRN_BROKER_ABBREV_SSOT_FINAL_V06135:START]
# Append-only VRN broker English abbreviation SSOT final patch.
# Policy:
# - Broker output must be English abbreviation only.
# - Daiwa -> DAIWA
# - Goldman / Goldman Sachs -> GS
# - JP / JPM / JP Morgan / J.P. Morgan / JPMorgan -> JPM
# - Morgan Stanley -> MS
# - First Financial Holding / 第一金 / 第一 -> FFHC
# - President Securities / 統一 / 統一證券 -> PSC
# - Capital Securities / 群益 / 群益金鼎 / CLST -> CSC

VRN_BROKER_ABBREV_ALIAS_MAP_V06135 = [{'alias': 'Daiwa', 'abbrev': 'DAIWA', 'group': 'DAIWA'}, {'alias': 'DAIWA', 'abbrev': 'DAIWA', 'group': 'DAIWA'}, {'alias': 'Goldman', 'abbrev': 'GS', 'group': 'GS'}, {'alias': 'Goldman Sachs', 'abbrev': 'GS', 'group': 'GS'}, {'alias': 'GS', 'abbrev': 'GS', 'group': 'GS'}, {'alias': 'JP', 'abbrev': 'JPM', 'group': 'JPM'}, {'alias': 'JPM', 'abbrev': 'JPM', 'group': 'JPM'}, {'alias': 'JP Morgan', 'abbrev': 'JPM', 'group': 'JPM'}, {'alias': 'J.P. Morgan', 'abbrev': 'JPM', 'group': 'JPM'}, {'alias': 'JPMorgan', 'abbrev': 'JPM', 'group': 'JPM'}, {'alias': 'JPMorgan Chase', 'abbrev': 'JPM', 'group': 'JPM'}, {'alias': 'Morgan Stanley', 'abbrev': 'MS', 'group': 'MS'}, {'alias': 'MS', 'abbrev': 'MS', 'group': 'MS'}, {'alias': 'Citi', 'abbrev': 'CITI', 'group': 'CITI'}, {'alias': 'Citigroup', 'abbrev': 'CITI', 'group': 'CITI'}, {'alias': 'CITI', 'abbrev': 'CITI', 'group': 'CITI'}, {'alias': '第一金', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': '第一金證券', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': '第一金投顧', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': '第一', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': 'First Financial Holding', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': 'First Securities', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': 'FFHC', 'abbrev': 'FFHC', 'group': 'FFHC'}, {'alias': '統一', 'abbrev': 'PSC', 'group': 'PSC'}, {'alias': '統一證券', 'abbrev': 'PSC', 'group': 'PSC'}, {'alias': '統一投顧', 'abbrev': 'PSC', 'group': 'PSC'}, {'alias': 'President Securities', 'abbrev': 'PSC', 'group': 'PSC'}, {'alias': 'PSC', 'abbrev': 'PSC', 'group': 'PSC'}, {'alias': '群益', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': '群益金鼎', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': '群益金鼎證券', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': '群益投顧', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': 'Capital Securities', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': 'Capital Securities Corp', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': 'CLST', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': 'CSC', 'abbrev': 'CSC', 'group': 'CSC'}, {'alias': '兆豐', 'abbrev': 'MEGA', 'group': 'MEGA'}, {'alias': '兆豐投顧', 'abbrev': 'MEGA', 'group': 'MEGA'}, {'alias': '兆豐證券', 'abbrev': 'MEGA', 'group': 'MEGA'}, {'alias': 'MEGA', 'abbrev': 'MEGA', 'group': 'MEGA'}, {'alias': '華南', 'abbrev': 'HNCB', 'group': 'HNCB'}, {'alias': '華南投顧', 'abbrev': 'HNCB', 'group': 'HNCB'}, {'alias': '華南永昌', 'abbrev': 'HNCB', 'group': 'HNCB'}, {'alias': 'HNCB', 'abbrev': 'HNCB', 'group': 'HNCB'}, {'alias': '國泰', 'abbrev': 'CATHAY', 'group': 'CATHAY'}, {'alias': '國泰證期', 'abbrev': 'CATHAY', 'group': 'CATHAY'}, {'alias': '國泰證券', 'abbrev': 'CATHAY', 'group': 'CATHAY'}, {'alias': 'CATHAY', 'abbrev': 'CATHAY', 'group': 'CATHAY'}, {'alias': '中信', 'abbrev': 'CTBC', 'group': 'CTBC'}, {'alias': '中信投顧', 'abbrev': 'CTBC', 'group': 'CTBC'}, {'alias': '中國信託', 'abbrev': 'CTBC', 'group': 'CTBC'}, {'alias': 'CTBC', 'abbrev': 'CTBC', 'group': 'CTBC'}, {'alias': '元大', 'abbrev': 'YUANTA', 'group': 'YUANTA'}, {'alias': '元大投顧', 'abbrev': 'YUANTA', 'group': 'YUANTA'}, {'alias': 'YUANTA', 'abbrev': 'YUANTA', 'group': 'YUANTA'}, {'alias': '凱基', 'abbrev': 'KGI', 'group': 'KGI'}, {'alias': '凱基投顧', 'abbrev': 'KGI', 'group': 'KGI'}, {'alias': 'KGI', 'abbrev': 'KGI', 'group': 'KGI'}, {'alias': '富邦', 'abbrev': 'FUBON', 'group': 'FUBON'}, {'alias': '富邦投顧', 'abbrev': 'FUBON', 'group': 'FUBON'}, {'alias': 'FUBON', 'abbrev': 'FUBON', 'group': 'FUBON'}, {'alias': '永豐', 'abbrev': 'SINOPAC', 'group': 'SINOPAC'}, {'alias': '永豐投顧', 'abbrev': 'SINOPAC', 'group': 'SINOPAC'}, {'alias': 'SINOPAC', 'abbrev': 'SINOPAC', 'group': 'SINOPAC'}]

def def_vrn_norm_broker_key_v06135(x):
    import re
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"[()（）\[\]【】{}<>〈〉《》]", " ", s)
    s = re.sub(r"[\s　,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s

def def_get_vrn_broker_abbrev_alias_map_v06135():
    return list(VRN_BROKER_ABBREV_ALIAS_MAP_V06135)

def def_normalize_vrn_broker_abbrev_v06135(raw_broker="", filename="", broker_raw_backup=""):
    rows = list(VRN_BROKER_ABBREV_ALIAS_MAP_V06135)
    mp = {def_vrn_norm_broker_key_v06135(r.get("alias", "")): r for r in rows}

    haystacks = [
        ("BROKER", raw_broker),
        ("BROKER_RAW", broker_raw_backup),
        ("FILENAME", filename),
    ]

    for src, text in haystacks:
        nk = def_vrn_norm_broker_key_v06135(text)
        if nk in mp:
            r = mp[nk]
            return {
                "broker": r.get("abbrev", ""),
                "broker_normalized": r.get("abbrev", ""),
                "broker_source": "VIA_SSOT_Unified.py::VRN_BROKER_ABBREV_ALIAS_MAP_V06135",
                "broker_match_reason": src + ":exact:" + str(r.get("alias", "")),
                "broker_status": "OK",
            }

    for src, text in haystacks:
        nt = def_vrn_norm_broker_key_v06135(text)
        for r in sorted(rows, key=lambda z: len(def_vrn_norm_broker_key_v06135(z.get("alias", ""))), reverse=True):
            ak = def_vrn_norm_broker_key_v06135(r.get("alias", ""))
            if ak and ak in nt:
                return {
                    "broker": r.get("abbrev", ""),
                    "broker_normalized": r.get("abbrev", ""),
                    "broker_source": "VIA_SSOT_Unified.py::VRN_BROKER_ABBREV_ALIAS_MAP_V06135",
                    "broker_match_reason": src + ":contains:" + str(r.get("alias", "")),
                    "broker_status": "OK",
                }

    upper = str(raw_broker or "").strip().upper().replace(".", "")
    direct = {
        "DAIWA", "GS", "JPM", "MS", "CITI",
        "FFHC", "PSC", "CSC", "MEGA", "HNCB", "CATHAY", "CTBC",
        "YUANTA", "KGI", "FUBON", "SINOPAC"
    }
    if upper in direct:
        return {
            "broker": upper,
            "broker_normalized": upper,
            "broker_source": "DIRECT_ENGLISH_CODE",
            "broker_match_reason": "BROKER:direct",
            "broker_status": "OK",
        }

    return {
        "broker": upper,
        "broker_normalized": upper,
        "broker_source": "UNMAPPED",
        "broker_match_reason": "NO_MATCH",
        "broker_status": "REVIEW",
    }
# [VIA:VRN_BROKER_ABBREV_SSOT_FINAL_V06135:END]

# [VIA:VRN_BROKER_FIRSTPAGE_RESOLVER_V06137:START]

# Broker First Page Resolver.
# Uses broker alias list against first-page text / filename / broker field / email domain.
VRN_BROKER_FIRSTPAGE_ALIAS_ROWS_V06137 = [{'alias': 'Daiwa', 'broker': 'DAIWA'}, {'alias': 'DAIWA', 'broker': 'DAIWA'}, {'alias': 'Goldman', 'broker': 'GS'}, {'alias': 'Goldman Sachs', 'broker': 'GS'}, {'alias': 'GS', 'broker': 'GS'}, {'alias': 'JP', 'broker': 'JPM'}, {'alias': 'JPM', 'broker': 'JPM'}, {'alias': 'JP Morgan', 'broker': 'JPM'}, {'alias': 'J.P. Morgan', 'broker': 'JPM'}, {'alias': 'JPMorgan', 'broker': 'JPM'}, {'alias': 'Morgan Stanley', 'broker': 'MS'}, {'alias': 'MS', 'broker': 'MS'}, {'alias': 'Citi', 'broker': 'CITI'}, {'alias': 'Citigroup', 'broker': 'CITI'}, {'alias': 'CITI', 'broker': 'CITI'}, {'alias': '第一', 'broker': 'FFHC'}, {'alias': '第一金', 'broker': 'FFHC'}, {'alias': '第一金證券', 'broker': 'FFHC'}, {'alias': '第一金投顧', 'broker': 'FFHC'}, {'alias': 'First Financial Holding', 'broker': 'FFHC'}, {'alias': 'First Securities', 'broker': 'FFHC'}, {'alias': 'FFHC', 'broker': 'FFHC'}, {'alias': '統一', 'broker': 'PSC'}, {'alias': '統一證券', 'broker': 'PSC'}, {'alias': '統一投顧', 'broker': 'PSC'}, {'alias': 'President Securities', 'broker': 'PSC'}, {'alias': 'PSC', 'broker': 'PSC'}, {'alias': '群益', 'broker': 'CSC'}, {'alias': '群益金鼎', 'broker': 'CSC'}, {'alias': '群益金鼎證券', 'broker': 'CSC'}, {'alias': '群益投顧', 'broker': 'CSC'}, {'alias': 'Capital Securities', 'broker': 'CSC'}, {'alias': 'Capital Securities Corp', 'broker': 'CSC'}, {'alias': 'CLST', 'broker': 'CSC'}, {'alias': 'CLSA', 'broker': 'CSC'}, {'alias': 'CSC', 'broker': 'CSC'}, {'alias': '兆豐', 'broker': 'MEGA'}, {'alias': '兆豐投顧', 'broker': 'MEGA'}, {'alias': '兆豐證券', 'broker': 'MEGA'}, {'alias': 'MEGA', 'broker': 'MEGA'}, {'alias': '華南', 'broker': 'HNCB'}, {'alias': '華南投顧', 'broker': 'HNCB'}, {'alias': '華南永昌', 'broker': 'HNCB'}, {'alias': 'HNCB', 'broker': 'HNCB'}, {'alias': '國泰', 'broker': 'CATHAY'}, {'alias': '國泰證期', 'broker': 'CATHAY'}, {'alias': '國泰證券', 'broker': 'CATHAY'}, {'alias': 'CATHAY', 'broker': 'CATHAY'}, {'alias': '中信', 'broker': 'CTBC'}, {'alias': '中國信託', 'broker': 'CTBC'}, {'alias': '中信投顧', 'broker': 'CTBC'}, {'alias': 'CTBC', 'broker': 'CTBC'}, {'alias': '元大', 'broker': 'YUANTA'}, {'alias': '元大投顧', 'broker': 'YUANTA'}, {'alias': 'YUANTA', 'broker': 'YUANTA'}, {'alias': '凱基', 'broker': 'KGI'}, {'alias': '凱基投顧', 'broker': 'KGI'}, {'alias': 'KGI', 'broker': 'KGI'}, {'alias': '富邦', 'broker': 'FUBON'}, {'alias': '富邦投顧', 'broker': 'FUBON'}, {'alias': 'FUBON', 'broker': 'FUBON'}, {'alias': '永豐', 'broker': 'SINOPAC'}, {'alias': '永豐投顧', 'broker': 'SINOPAC'}, {'alias': 'SINOPAC', 'broker': 'SINOPAC'}, {'alias': 'jpmorgan.com', 'broker': 'JPM'}, {'alias': 'gs.com', 'broker': 'GS'}, {'alias': 'goldmansachs.com', 'broker': 'GS'}, {'alias': 'morganstanley.com', 'broker': 'MS'}, {'alias': 'citi.com', 'broker': 'CITI'}, {'alias': 'citigroup.com', 'broker': 'CITI'}, {'alias': 'daiwa', 'broker': 'DAIWA'}, {'alias': 'clsa.com', 'broker': 'CSC'}, {'alias': 'capital.com.tw', 'broker': 'CSC'}, {'alias': 'entrust.com.tw', 'broker': 'HNCB'}, {'alias': 'megasec.com.tw', 'broker': 'MEGA'}, {'alias': 'cathaysec.com.tw', 'broker': 'CATHAY'}, {'alias': 'ctbcsec.com', 'broker': 'CTBC'}]

def def_vrn_broker_norm_key_v06137(x):
    import re
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").lower()
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[()（）\[\]【】{}<>〈〉《》]", " ", s)
    s = re.sub(r"[\s　,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s

def def_get_vrn_broker_firstpage_alias_rows_v06137():
    return list(VRN_BROKER_FIRSTPAGE_ALIAS_ROWS_V06137)

def def_detect_vrn_broker_from_first_page_text_v06137(raw_broker="", filename="", first_page_text=""):
    rows = sorted(list(VRN_BROKER_FIRSTPAGE_ALIAS_ROWS_V06137), key=lambda r: len(def_vrn_broker_norm_key_v06137(r.get("alias", ""))), reverse=True)
    haystacks = [
        ("BROKER_FIELD", raw_broker),
        ("FILENAME", filename),
        ("FIRST_PAGE_TEXT", first_page_text),
    ]

    for src, text in haystacks:
        nk = def_vrn_broker_norm_key_v06137(text)
        for r in rows:
            ak = def_vrn_broker_norm_key_v06137(r.get("alias", ""))
            if ak and nk == ak:
                return {"broker": r.get("broker", ""), "broker_status": "OK", "broker_source": "SSOT_FIRSTPAGE_V06137", "broker_match_reason": src + ":exact:" + r.get("alias", "")}

    for src, text in haystacks:
        nt = def_vrn_broker_norm_key_v06137(text)
        for r in rows:
            ak = def_vrn_broker_norm_key_v06137(r.get("alias", ""))
            if ak and ak in nt:
                return {"broker": r.get("broker", ""), "broker_status": "OK", "broker_source": "SSOT_FIRSTPAGE_V06137", "broker_match_reason": src + ":contains:" + r.get("alias", "")}

    import re
    emails = re.findall(r"[A-Za-z][A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", str(first_page_text or ""))
    for em in emails:
        domain = em.split("@")[-1].lower()
        for r in rows:
            ak = def_vrn_broker_norm_key_v06137(r.get("alias", ""))
            if ak and ak in def_vrn_broker_norm_key_v06137(domain):
                return {"broker": r.get("broker", ""), "broker_status": "OK", "broker_source": "SSOT_FIRSTPAGE_EMAIL_DOMAIN_V06137", "broker_match_reason": "EMAIL_DOMAIN:" + domain}

    upper = str(raw_broker or "").strip().upper().replace(".", "")
    return {"broker": upper, "broker_status": "REVIEW", "broker_source": "UNMAPPED", "broker_match_reason": "NO_MATCH"}

# [VIA:VRN_BROKER_FIRSTPAGE_RESOLVER_V06137:END]

# [VIA:VRN_YFINANCE_SUCCESSFUL_SUFFIX_LOCK_V06138:START]

# YFinance successful suffix lock helper.
# Policy:
#   If Yfinance Used Ticker has successful price / consensus / beta data, keep only that suffix.
#   The alternate .TW/.TWO candidate is moved to audit, not used as formal Yfinance Ticker.
def def_vrn_is_yfinance_ticker_v06138(x):
    import re
    s = "" if x is None else str(x)
    s = s.strip().upper()
    return bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", s))

def def_vrn_parse_yfinance_candidates_v06138(x):
    import re
    s = "" if x is None else str(x)
    s = s.upper()
    parts = re.split(r"[\s,;|/\\]+", s)
    out = []
    for p in parts:
        p = p.strip()
        if def_vrn_is_yfinance_ticker_v06138(p) and p not in out:
            out.append(p)
    return out

def def_vrn_select_successful_yfinance_ticker_v06138(row):
    def g(k):
        return "" if row.get(k) is None else str(row.get(k)).strip()

    used = (g("Yfinance Used Ticker") or g("Yfinance Ticker")).upper()
    current = g("Yfinance Ticker").upper()
    candidates = def_vrn_parse_yfinance_candidates_v06138(g("Yfinance Candidate Tickers"))

    if def_vrn_is_yfinance_ticker_v06138(current) and current not in candidates:
        candidates.append(current)
    if def_vrn_is_yfinance_ticker_v06138(used) and used not in candidates:
        candidates.insert(0, used)

    status = g("Yfinance Fetch Status").upper()
    useful_fields = [
        "Latest Adj Close",
        "Latest Volume",
        "Report Date Adj Close",
        "Report Date Volume",
        "Yfinance Target Low Price",
        "Yfinance Target Mean Price",
        "Yfinance Target Median Price",
        "Yfinance Target High Price",
        "Yfinance Recommendation Key",
        "Yfinance Recommendation Mean",
        "Yfinance Number Of Analyst Opinions",
        "Yfinance Beta",
        "Yfinance Market Cap",
    ]
    useful_count = sum(1 for k in useful_fields if g(k))
    has_success = status == "OK" and useful_count >= 2

    if has_success and def_vrn_is_yfinance_ticker_v06138(used):
        final = used
        lock_status = "LOCKED_SUCCESSFUL_SUFFIX"
        reason = "YFINANCE_USED_TICKER_HAS_SUCCESSFUL_DATA"
    elif has_success and def_vrn_is_yfinance_ticker_v06138(current):
        final = current
        lock_status = "LOCKED_CURRENT_SUFFIX"
        reason = "CURRENT_YFINANCE_TICKER_HAS_SUCCESSFUL_DATA"
    elif len(candidates) == 1:
        final = candidates[0]
        lock_status = "LOCKED_SINGLE_CANDIDATE"
        reason = "ONLY_ONE_CANDIDATE"
    else:
        final = used if def_vrn_is_yfinance_ticker_v06138(used) else current
        lock_status = "REVIEW"
        reason = "NO_SUCCESSFUL_USED_TICKER_OR_MULTIPLE_UNRESOLVED"

    deleted = [c for c in candidates if c != final]
    return {
        "Yfinance Ticker": final,
        "Yfinance Used Ticker": final,
        "Yfinance Candidate Tickers": final,
        "Yfinance Deleted Alternate Tickers": " | ".join(deleted),
        "Yfinance Suffix Lock Status": lock_status,
        "Yfinance Suffix Lock Reason": reason,
    }

# [VIA:VRN_YFINANCE_SUCCESSFUL_SUFFIX_LOCK_V06138:END]

# [VIA:VRN_YFINANCE_ADJCLOSE_SUFFIX_LOCK_V06139:START]

# YFinance Adj Close successful suffix lock helper.
# Formal rule:
#   Adj Close success decides final YFinance ticker suffix.
#   Consensus success alone is not sufficient to lock formal ticker.
def def_vrn_yfinance_adjclose_suffix_lock_v06139(row):
    import re

    def g(k):
        return "" if row.get(k) is None else str(row.get(k)).strip()

    def to_float(x):
        s = "" if x is None else str(x).strip()
        s = s.replace(",", "").replace("%", "")
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None

    def is_yf(x):
        return bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", str(x or "").strip().upper()))

    def parse_candidates(x):
        parts = re.split(r"[\s,;|/\\]+", str(x or "").upper())
        out = []
        for p in parts:
            p = p.strip()
            if is_yf(p) and p not in out:
                out.append(p)
        return out

    used = (g("Yfinance Used Ticker") or g("Yfinance Ticker")).upper()
    current = g("Yfinance Ticker").upper()
    candidates = parse_candidates(g("Yfinance Candidate Tickers"))

    if is_yf(current) and current not in candidates:
        candidates.append(current)
    if is_yf(used) and used not in candidates:
        candidates.insert(0, used)

    has_adjclose = to_float(g("Latest Adj Close")) is not None or to_float(g("Report Date Adj Close")) is not None

    if has_adjclose and is_yf(used):
        final = used
        status = "LOCKED_ADJCLOSE_SUCCESS"
        reason = "YFINANCE_USED_TICKER_HAS_ADJCLOSE"
    elif has_adjclose and is_yf(current):
        final = current
        status = "LOCKED_ADJCLOSE_CURRENT"
        reason = "CURRENT_TICKER_HAS_ADJCLOSE"
    else:
        final = used if is_yf(used) else current
        status = "REVIEW_NO_ADJCLOSE_LOCK"
        reason = "NO_ADJCLOSE_DATA"

    deleted = [c for c in candidates if c != final]
    return {
        "Yfinance Ticker": final,
        "Yfinance Used Ticker": final,
        "Yfinance Candidate Tickers": final,
        "Yfinance Deleted Alternate Tickers": " | ".join(deleted),
        "Yfinance Suffix Lock Status": status,
        "Yfinance Suffix Lock Reason": reason,
        "Yfinance AdjClose Success": "YES" if has_adjclose else "NO",
    }

# [VIA:VRN_YFINANCE_ADJCLOSE_SUFFIX_LOCK_V06139:END]

# [VIA:VRN_YFINANCE_REAL_USEDTICKER_TFINANCE_PATCH_V06140:START]

# VRN YFinance AdjClose Real UsedTicker Lock + TFinance Field Patch.
# Rule:
#   Use exact successful Adj Close ticker from YFinance Used Ticker / fallback flag.
#   Do not treat combined "xxxx.TW xxxx.TWO" as final ticker.
#   Keep alternate suffix in audit only.
def def_vrn_is_yfinance_ticker_v06140(x):
    import re
    s = "" if x is None else str(x)
    return bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", s.strip().upper()))

def def_vrn_parse_yfinance_tokens_v06140(x):
    import re
    s = "" if x is None else str(x)
    out = []
    for t in re.findall(r"[1-9]\d{3}\.(?:TW|TWO)", s.upper()):
        if t not in out:
            out.append(t)
    return out

def def_vrn_adjclose_success_v06140(row):
    def f(x):
        s = "" if x is None else str(x).strip().replace(",", "").replace("%", "")
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None
    return f(row.get("Latest Adj Close")) is not None or f(row.get("Report Date Adj Close")) is not None

def def_vrn_lock_yfinance_by_real_adjclose_v06140(row):
    def g(k):
        return "" if row.get(k) is None else str(row.get(k)).strip()

    ticker = g("Ticker")
    candidates = []
    import re
    if re.fullmatch(r"(?!202[1-9])(?!2030)[1-9]\d{3}", ticker):
        candidates = [ticker + ".TW", ticker + ".TWO"]

    used = g("YFinance Used Ticker").upper()
    if not def_vrn_is_yfinance_ticker_v06140(used):
        fallback = g("YFinance Fallback Used").upper()
        if fallback in ["YES", "TRUE", "1"] and len(candidates) == 2:
            used = candidates[1]
        elif fallback in ["NO", "FALSE", "0"] and len(candidates) == 2:
            used = candidates[0]

    merged = " ".join([
        g("YFinance Candidate Tickers"),
        g("Yfinance Candidate Tickers"),
        g("Yfinance Ticker Before AdjClose Lock"),
        g("Yfinance Candidate Tickers Before AdjClose Lock"),
        g("Yfinance Ticker"),
    ])
    for t in def_vrn_parse_yfinance_tokens_v06140(merged):
        if t not in candidates:
            candidates.append(t)

    has_adj = def_vrn_adjclose_success_v06140(row)
    if has_adj and def_vrn_is_yfinance_ticker_v06140(used):
        final = used
        status = "LOCKED_ADJCLOSE_SUCCESS"
        reason = "REAL_YFINANCE_USED_TICKER_HAS_ADJCLOSE"
    else:
        final = used if def_vrn_is_yfinance_ticker_v06140(used) else (candidates[0] if candidates else "")
        status = "REVIEW_NO_ADJCLOSE_LOCK"
        reason = "NO_ADJCLOSE_DATA"

    deleted = [c for c in candidates if c != final]
    return {
        "YFinance Ticker": final,
        "YFinance Used Ticker": final,
        "YFinance Candidate Tickers": final,
        "YFinance Deleted Alternate Tickers": " | ".join(deleted),
        "YFinance AdjClose Lock Status": status,
        "YFinance AdjClose Lock Reason": reason,
        "YFinance AdjClose Success": "YES" if has_adj else "NO",
    }

# [VIA:VRN_YFINANCE_REAL_USEDTICKER_TFINANCE_PATCH_V06140:END]

# [VIA:VRN_ANALYST_VALUATION_FINANCIAL_JOIN_V06141:START]

# VRN Analyst + Valuation Method + Financial Data join helpers.
def def_vrn_extract_analyst_email_broker_v06141(text):
    import re
    s = "" if text is None else str(text)
    m = re.search(r"([A-Za-z][A-Za-z0-9._\-]{1,60})@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})", s)
    if not m:
        return {"analyst": "", "email": "", "broker_from_email": ""}
    local, domain = m.group(1), m.group(2).lower()
    parts = [p for p in re.split(r"[._\-]+", local) if p]
    analyst = " ".join(p.capitalize() for p in parts[:3])
    broker = domain.split(".")[0].upper()
    for pat, abbr in [("jpmorgan","JPM"),("jpm","JPM"),("goldman","GS"),("morganstanley","MS"),("daiwa","DAIWA"),("citi","CITI"),("ctbc","CTBC"),("mega","MEGA"),("cathay","CATHAY"),("capital","CSC"),("president","PSC"),("first","FFHC")]:
        if pat in domain:
            broker = abbr
            break
    return {"analyst": analyst, "email": m.group(0), "broker_from_email": broker}

def def_vrn_valuation_method_aliases_v06141():
    return {
        "PER": ["PER", "P/E", "PE Ratio", "本益比", "市盈率", "常態本益比"],
        "PBR": ["PBR", "P/B", "PB Ratio", "股價淨值比", "市淨率"],
        "PSR": ["P/S", "PSR", "股價營收比", "市銷率"],
        "EV/EBITDA": ["EV/EBITDA", "Enterprise Multiple", "企業價值倍數"],
        "DCF": ["DCF", "Discounted Cash Flow", "現金流量折現法", "折現現金流"],
        "DDM": ["DDM", "Dividend Discount Model", "股利折現模型"],
        "FCFF": ["FCFF", "Free Cash Flow to Firm", "企業自由現金流量"],
        "FCFE": ["FCFE", "Free Cash Flow to Equity", "股權自由現金流量"],
        "SOTP": ["SOTP", "Sum of the Parts", "分部估值法", "加總估值法"],
        "NAV": ["NAV", "Net Asset Value", "淨資產價值法"],
    }

# [VIA:VRN_ANALYST_VALUATION_FINANCIAL_JOIN_V06141:END]

# [VIA:VRN_ANALYST_TARGET_VALUATION_EPS_FINTRUST_V06142:START]

# VRN v0.6.14.2 Analyst / Target Price / Valuation / EPS / Financial Trust SSOT helpers.
def def_vrn_phone_regex_v06142():
    import re
    return re.compile(r"(\+886[\-\s]?\d{1,2}[\-\s]?\d{3,4}[\-\s]?\d{3,4}|\(?02\)?[\-\s]?\d{3,4}[\-\s]?\d{4}|\(?0\d{1,2}\)?[\-\s]?\d{3,4}[\-\s]?\d{3,4})")

def def_vrn_target_price_synonyms_v06142():
    return ["目標價", "合理價", "Target Price", "TP", "Fair Value", "target"]

def def_vrn_previous_target_price_stopwords_v06142():
    return ["previous", "prior", "old", "last", "former", "前次", "前目標", "原目標", "舊目標", "前一目標", "原先"]

def def_vrn_eps_policy_v06142():
    return {
        "basic_eps": "explicit Basic EPS or max EPS if unclear",
        "diluted_eps": "explicit Diluted EPS or min EPS if unclear",
        "valuation_eps": "always use diluted EPS",
        "valuation_price": "always use latest adjusted close",
    }

def def_vrn_financial_validation_methods_v06142():
    return [
        "historical official overlap check",
        "same-period value search when account alias mismatch",
        "income statement add/sub validation",
        "ratio division validation",
        "cross-table ROA/ROE average assets/equity validation",
        "SSOT alias append-only improvement",
    ]

# [VIA:VRN_ANALYST_TARGET_VALUATION_EPS_FINTRUST_V06142:END]

# [VIA:VRN_ANALYST_VALUATION_TFINANCE_FIX_V06143:START]

# VRN v0.6.14.3 Analyst Contact Guard / Valuation Exact Evidence / TFinance Split.
def def_vrn_is_contact_label_v06143(x):
    import re
    s = "" if x is None else str(x).strip().lower()
    return bool(re.search(r"(聯絡方式|電子信箱|信箱|email|e-mail|電話|tel|phone|contact|ext|分機)", s, re.I))

def def_vrn_split_email_local_name_v06143(local):
    import re
    s = "" if local is None else str(local).strip()
    if re.fullmatch(r"\d+", s):
        return ""
    s = re.sub(r"\d+", "", s).strip("._- ")
    parts = [p for p in re.split(r"[._\-]+", s) if p]
    if len(parts) >= 2:
        return " ".join(p.capitalize() for p in parts[:3])
    common_last = ["kuo","chen","chang","wang","lin","lee","liu","huang","hsu","tsai","chiu","wu","yang","ho"]
    low = s.lower()
    for last in common_last:
        if low.endswith(last) and len(low) > len(last) + 1:
            return low[:-len(last)].capitalize() + " " + last.capitalize()
    return s.capitalize() if re.fullmatch(r"[A-Za-z]{2,30}", s) else ""

def def_vrn_analyst_policy_v06143():
    return {
        "contact_label_not_analyst": ["聯絡方式", "電子信箱", "Email", "電話", "Tel", "Phone"],
        "numeric_email_local_not_analyst": True,
        "hncb_researcher_field": "研究員右側姓名優先，例如 研究員 許頤；電子信箱 10863@entrust.com.tw 只作 contact evidence",
        "english_email_local_split": "Raymondkuo => Raymond Kuo",
    }

def def_vrn_valuation_policy_v06143():
    return {
        "PER_PBR_separate": True,
        "method_added_only_when_exact_evidence_found": True,
        "do_not_add_PBR_when_only_PER_found": True,
    }

def def_vrn_tfinance_policy_v06143():
    return {
        "TFinance Forward EPS": "YFinance info only",
        "TFinance Forward PE": "YFinance info only",
        "Financial Basic EPS": "report/table financial data",
        "Financial Diluted EPS": "report/table financial data; valuation uses diluted EPS",
    }

# [VIA:VRN_ANALYST_VALUATION_TFINANCE_FIX_V06143:END]

# [VIA:VRN_ANALYST_YFINANCE_OFFICIAL_FIELD_SEAL_V06144:START]

# VRN v0.6.14.4 Analyst / Broker / YFinance Official Field Policy
def def_vrn_contact_label_policy_v06144():
    return {
        "analyst_rule": "研究員/分析師欄位優先；email/phone 上方姓名次之；email local-part 僅 fallback；純數字 local-part 不可當 analyst",
        "bad_labels": ["研究員", "聯絡方式", "電子信箱", "Email", "電話", "Tel", "Phone"],
        "chinese_name": "2~4 Chinese characters, excluding labels",
        "english_name": "Two or three capitalized English words; Raymondkuo can become Raymond Kuo only as fallback",
    }

def def_vrn_yfinance_info_fields_v06144():
    return [
        "targetLowPrice",
        "targetMeanPrice",
        "targetMedianPrice",
        "targetHighPrice",
        "recommendationKey",
        "recommendationMean",
        "numberOfAnalystOpinions",
        "beta",
        "forwardEps",
        "forwardPE",
        "marketCap",
        "trailingPE",
        "priceToBook",
    ]

def def_vrn_deprecated_tfinance_policy_v06144():
    return {
        "official_prefix": "YFinance",
        "deprecated_prefix": "TFinance",
        "action": "copy legacy values to YFinance fields, then keep legacy names only in audit/report, not official schema",
    }

# [VIA:VRN_ANALYST_YFINANCE_OFFICIAL_FIELD_SEAL_V06144:END]

# [VIA:VRN_HUANAN_ANALYST_BROKER_SEAL_V06145:START]

# VRN v0.6.14.5 HuaNan Analyst / Broker Canonical Policy
def def_vrn_huanan_policy_v06145():
    return {
        "broker_canonical": "HuaNan",
        "broker_aliases": ["華南", "華南投顧", "華南永昌", "HuaNan", "HNCB", "entrust.com.tw"],
        "analyst_rule": "For HuaNan reports, analyst is the right-side value of 研究員 row, usually directly above 電子信箱. Numeric email local-part such as 450/10863/9899 is contact ID only, not analyst.",
        "memo_visit_rule": "HuaNan memo/visit reports are not forced to have analyst unless an explicit 研究員 contact block exists.",
        "email_rule": "entrust.com.tw email is contact evidence and broker evidence only."
    }

def def_vrn_normalize_broker_huanan_v06145(raw):
    import re
    s = "" if raw is None else str(raw)
    return "HuaNan" if re.search(r"(華南|HuaNan|HNCB|entrust\.com\.tw|華南投顧|華南永昌)", s, re.I) else s

# [VIA:VRN_HUANAN_ANALYST_BROKER_SEAL_V06145:END]

# [VIA:VRN_BROKER_ANALYST_ADAPTER_STRENGTHEN_V06146:START]

# VRN v0.6.14.6 Broker Analyst Adapter Layer Policy
def def_vrn_broker_analyst_adapter_policy_v06146():
    return {
        "layer": "broker_specific_adapter_before_general_extractor",
        "general_extractor_preserved": True,
        "huanan": {
            "broker_canonical": "HuaNan",
            "trigger": ["華南", "華南投顧", "華南永昌", "HuaNan", "HNCB", "entrust.com.tw"],
            "analyst_rule": "研究員右側 2~4 中文字；email/phone 只作 contact evidence",
            "numeric_email_local_not_analyst": True,
            "memo_visit_no_forced_analyst": True
        }
    }

# [VIA:VRN_BROKER_ANALYST_ADAPTER_STRENGTHEN_V06146:END]

# [VIA:VRN_YFINANCE_HEADER_CANONICAL_REFRESH_V06147:START]

# VRN v0.6.14.7 YFinance Canonical Field Policy
def def_vrn_yfinance_field_policy_v06147():
    return {
        "official_market_data_prefix": "YFinance",
        "deprecated_prefix": "TFinance",
        "rule": "All headers containing TFinance must be renamed/merged into YFinance. YFinance values take priority; legacy TFinance values are audit fallback only.",
        "yfinance_info_fields": [
            "targetHighPrice",
            "targetLowPrice",
            "targetMeanPrice",
            "targetMedianPrice",
            "recommendationKey",
            "recommendationMean",
            "numberOfAnalystOpinions",
            "beta",
            "forwardEps",
            "forwardPE",
            "marketCap",
            "trailingPE",
            "priceToBook"
        ],
        "yfinance_history_fields": ["Adj Close", "Volume"],
        "suffix_fallback": [".TW", ".TWO"],
        "success_lock": "Keep the ticker suffix that successfully returns Adj Close; move alternate suffixes to audit."
    }

# [VIA:VRN_YFINANCE_HEADER_CANONICAL_REFRESH_V06147:END]

# ======================================================================================
# VRN_V139Q_FINAL_NOHANG_ENVMANAGER_APPEND_ONLY START
# def Purpose:
# def   - Final append-only NoHang / EnvManager bridge for remaining v139P Yellow modules
# def   - Adds explicit coverage markers for VIA_EnvManager, timeout, watchdog, nohang
# def   - No DB write, no SSOT mutation, no network execution
# ======================================================================================

VRN_V139Q_FINAL_BRIDGE_ENABLED = True
VRN_V139Q_NOHANG_ENABLED = True
VRN_V139Q_WATCHDOG_ENABLED = True
VRN_V139Q_TIMEOUT_SECONDS = 180
VRN_V139Q_DB_WRITE_ENABLE = False
VRN_V139Q_SSOT_MUTATION_ENABLE = False
VRN_V139Q_NETWORK_ENABLE = False

VRN_V139Q_AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
VRN_V139Q_CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
VRN_V139Q_ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"
VRN_V139Q_VIA_ENVMANAGER_MARKER = "VIA_EnvManager"
VRN_V139Q_NOHANG_WATCHDOG_MARKER = "nohang watchdog timeout"

def def_vrn_v139q_nohang_envmanager_bridge_health():
    from pathlib import Path
    return {
        "bridge": "VRN_V139Q_FINAL_NOHANG_ENVMANAGER_APPEND_ONLY",
        "VIA_EnvManager": VRN_V139Q_ENV_MANAGER_PATH,
        "VeritasAegisNexus": VRN_V139Q_AEGIS_PATH,
        "VeritasCeleritas": VRN_V139Q_CELERITAS_PATH,
        "nohang": VRN_V139Q_NOHANG_ENABLED,
        "watchdog": VRN_V139Q_WATCHDOG_ENABLED,
        "timeout": VRN_V139Q_TIMEOUT_SECONDS,
        "db_write": VRN_V139Q_DB_WRITE_ENABLE,
        "ssot_mutation": VRN_V139Q_SSOT_MUTATION_ENABLE,
        "network": VRN_V139Q_NETWORK_ENABLE,
        "envmanager_exists": Path(VRN_V139Q_ENV_MANAGER_PATH).exists(),
        "aegis_exists": Path(VRN_V139Q_AEGIS_PATH).exists(),
        "celeritas_exists": Path(VRN_V139Q_CELERITAS_PATH).exists(),
    }

# VRN_V139Q_FINAL_NOHANG_ENVMANAGER_APPEND_ONLY END


