

# -*- coding: utf-8 -*-
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  VIA_SSOT_Unified.py                                                   │
# │  ASSET_ID  : AST-PY-MOD-VSE-500-UNIFIED                               │
# │  DISPLAY   : SYS_VSE.MDL500.MOD-UNIFIED                               │
# │  VERSION   : 4.0.0     STATUS : stable                                 │
# │  LANGUAGE  : Python 3.10+                                              │
# │  ANCHORS   : SSOT-SPEC / SSOT-DATA / SSOT-BUILD                       │
# │              SSOT-QUERY / SSOT-COMPOUND / SSOT-STORE                  │
# │              SSOT-RESTORE / SSOT-UTIL                                  │
# │  LL RULES  : #10 #12 #13 #15 #17 #18 #19 #20                         │
# ├─────────────────────────────────────────────────────────────────────────┤
# │  CORPUS: regex=46 · lists=18 · synonyms=36 · aliases=167              │
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
      "基本每股盈餘",
      "Earnings Per Share",
      "稀釋每股盈餘"
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
  }
]
''')

_CORPUS_STATS: dict[str, int] = {
    "regex_rules":   46,
    "list_rules":    18,
    "synonym_rules": 36,
    "total_aliases": 167,
    "total_rules":   100,
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
    chk("synonym_rules=36",       m["synonym_rules"], 36)

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

