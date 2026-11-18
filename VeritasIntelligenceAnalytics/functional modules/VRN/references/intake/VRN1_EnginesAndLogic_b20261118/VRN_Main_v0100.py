#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-MAN001 · VRN_Main_v0100 v0100 · ENTRY 獨立 MAIN：實測、自測、建冊、驗冊 =====
# AST 注入（只加註解，AST 不變）：類別 3 · 函式 146；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
r"""
VRN_Main_v0100 — VRN 獨立系統的唯一入口（獨立 MAIN · 獨立註冊 · 獨立 SSOT：REGEX／同義字）

這一版以 2026-09-23 在 106 份真實報告上跑到 FAIL 0 的 VRN 為本體（VRN_Evidence_Core v0100、
首頁引擎 v0104、資料庫引擎 v0103、VRN_AutoTestLoop v0101），不改它們的判讀邏輯，只把它們收成一個
自己站得住的系統：

  獨立 MAIN     本檔。所有動作（建冊、驗冊、實測、單獨複製測試、加速器）都從這裡進。
  獨立註冊      VRN_REGISTRY_v0100.json：VRN 資料夾內每一個檔案（類別、版本、SHA-256、加速器橋）。
                未登記的檔、被改過沒重建的檔 = FAIL。
  獨立 SSOT     ssot/ 底下：
                  VRN_REGEX_SSOT_v0100.json     VRN 程式裡每一條 regex（AST 逐條抽出，含來源檔、函式、旗標）
                  VRN_SYNONYM_SSOT_v0100.json   兩支引擎 + 證據核心「執行期實際生效」的同義字表，跨引擎衝突照列
                  VRN_SSOT_INDEX_v0100.json     VRN 讀的每一本知識書（版本、SHA-256、來源、誰在讀）
                  VRN_Broker_Dict / VRN_Rating_Dict / VIS_VRN_TickerFilenameSSOT   VRN 自己的副本（引擎先讀這裡）
                SSOT／REGEX／同義字由子系統自己生成；衝突只顯示、不自動改（AI＋操作員裁定）。
  加速器        各 .py 檔頭的 [VIA:ACCEL-BRIDGE:v0100] 不變。本入口依序找 --accel-home、環境變數
                VIA_ACCEL_HOME、往上找 supportive modules、母倉預設位置
                （%USERPROFILE%\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules），
                以路徑載入 VIA_SuperAccel_Module（→ SUP_MDL737 最新尾版 → VeritasCeleritas 鎖定版），
                登記後同一行程裡每支 VRN 引擎的橋都接得到；activate() 套用執行緒預算。找不到 = 照實寫
                「無加速」，不影響判讀。本倉不放加速器程式碼。

治理：LIVE 關、不連網、不安裝套件、不設定 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT；
真實報告與真值檔只在操作員手上，不入庫；輸出寫到 --out，不寫回倉庫（build 只重建 ssot/ 與註冊冊）。
自立閘座（FLOW 針相容）：main() 自行設定 VIA_FROM_VCGC=YES；保留 def main / def selftest。

用法（Windows 建議用同資料夾的 Invoke-VRN-Main-v0100.ps1）：
  python VRN_Main_v0100.py run --samples "C:\測試樣本報告" [--truth truth.json] [--out DIR]
                                            # 預設只處理個股報告的檔名、第一頁、年度財報頁；--no-focus = 全部照舊
  python VRN_Main_v0100.py selftest
  python VRN_Main_v0100.py build            # 重建 ssot/ 三本冊 + 註冊冊（改過程式或知識書之後）
  python VRN_Main_v0100.py check            # 只驗，不寫
  python VRN_Main_v0100.py standalone       # 把 VRN 資料夾單獨複製到暫存區再跑，證明不依賴倉庫其他部分
  python VRN_Main_v0100.py accel [--activate]
  python VRN_Main_v0100.py lock             # 已知答案逐組證明，全過的引擎記下指紋（之後邏輯一改，check 就紅燈）
  python VRN_Main_v0100.py lock --status    # 輸出鎖帳本（VRN 資料夾外）與引擎鎖現況；--unlock 檔名 [--part 部位] 解鎖
  python VRN_Main_v0100.py truth-from-matrix 貼文.txt [--out 真值.json]   # 母倉首頁矩陣貼文 → G11 真值檔（只在操作員手上，不入庫）
退出碼：0 = 無 FAIL；1 = 有 FAIL；2 = 用法錯誤。
"""

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

import argparse
import ast
import csv
import contextlib
import hashlib
import html
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import stat
import tempfile
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

# =============================================================================
# 00. 參數（全部集中在這裡）
# =============================================================================
MAIN_VERSION = "v0100"
MAIN_NAME = "VRN_Main_" + MAIN_VERSION
# 啟動器只是登記在冊上的名字，不是本入口要呼叫的東西（它呼叫本入口，反過來不成立）。
LAUNCHER_NAME = "Invoke-VRN-Main-" + MAIN_VERSION + ".ps1"
VRN_ROOT = Path(__file__).resolve().parent
ENGINE_DIR = VRN_ROOT / "engine"
SSOT_DIR = VRN_ROOT / "ssot"
REGISTRY_PATH = VRN_ROOT / "VRN_REGISTRY_v0100.json"
REGEX_BOOK = SSOT_DIR / "VRN_REGEX_SSOT_v0100.json"
SYNONYM_BOOK = SSOT_DIR / "VRN_SYNONYM_SSOT_v0100.json"
INDEX_BOOK = SSOT_DIR / "VRN_SSOT_INDEX_v0100.json"
AUDIT_DIR = VRN_ROOT / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100"
ORACLE_PATH = AUDIT_DIR / "FILENAME_RESULTS.json"
DEFAULT_SAMPLES_WINDOWS = r"C:\測試樣本報告"
MOTHER_ACCEL_DEFAULT = ("OneDrive", "Documents", "movies-dataset", "VeritasIntelligenceAnalytics", "supportive modules")
ACCEL_ENTRY = "VIA_SuperAccel_Module.py"
ACCEL_MARKER = "[VIA:ACCEL-BRIDGE:v0100]"
PS_ACCEL_MARKER = "[VIA:PS-ACCEL20:v0100]"
SAMPLE_SUFFIXES = (".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".tif", ".tiff")

ENGINE_FILES = {
    "first_page": ENGINE_DIR / "VIA_VRN_FirstPageEngine.py",
    "database": ENGINE_DIR / "VRN_Integrated_ReportDatabase_Engine.py",
    "evidence_core": ENGINE_DIR / "VRN_Evidence_Core.py",
    "autotest": ENGINE_DIR / "VRN_AutoTestLoop.py",
    "ticker_master": ENGINE_DIR / "VIA_TW_Ticker_Master_v0210.py",
    "panorama": ENGINE_DIR / "VRN_PanoramaProbe.py",
    "ocr": ENGINE_DIR / "VRN_Ocr_v0100.py",
    "bookcheck": ENGINE_DIR / "VRN_BookCheck_v0100.py",
    "tempstore": ENGINE_DIR / "VRN_TempStore_v0100.py",
    "astid": ENGINE_DIR / "VRN_AstId_v0100.py",
    "localdb": ENGINE_DIR / "VRN_LocalDB_v0100.py",
    "regions": ENGINE_DIR / "VRN_PageRegions_v0100.py",
    "dataframe": ENGINE_DIR / "VRN_DataFrame_v0100.py",
    "titletrim": ENGINE_DIR / "VRN_TitleTrim_v0100.py",
    "lock": ENGINE_DIR / "VRN_Lock_v0100.py",
    "focus": ENGINE_DIR / "VRN_Focus_v0100.py",
    "matrix": ENGINE_DIR / "VRN_Matrix_v0100.py",
    "record": ENGINE_DIR / "VRN_TickerRecord_v0100.py",
    "truthmatrix": ENGINE_DIR / "VRN_TruthMatrix_v0100.py",
    "runcache": ENGINE_DIR / "VRN_RunCache_v0100.py",
    "outputverify": ENGINE_DIR / "VRN_OutputVerify_v0100.py",
    "pivotdb": ENGINE_DIR / "VRN_PivotDB_v0100.py",
    "toolbridge": ENGINE_DIR / "VRN_ToolBridge_v0100.py",
}
# 2026-10-11 母倉引擎（逐位元組，engine/mother/；出處 ssot/VRN_ENGINES_PROVENANCE_v0100.json）：由 regions 依路徑載入。
MOTHER_ENGINE_FILES = (
    "engine/mother/VRN_ENG392_TextCompleteness_v0100.py",
    "engine/mother/VRN_ENG393_DocClassVerify_v0100.py",
    "engine/mother/VRN_ENG394_LayoutRestore_v0100.py",
    "engine/mother/VRN_ENG395_ValuationMethodLexicon_v0100.py",
    "engine/mother/VRN_ENG396_ReportEntities_v0100.py",
    "engine/mother/CGC_MDL249_DataFrameLock_v0100.py",
)
# VRN 執行期程式：REGEX 冊從這些檔抽（測試與凍結稽核包不算執行期）。
REGEX_SOURCES = (
    "VRN_Main_v0100.py",
    "engine/VIA_VRN_FirstPageEngine.py",
    "engine/VRN_Integrated_ReportDatabase_Engine.py",
    "engine/VRN_Evidence_Core.py",
    "engine/VRN_AutoTestLoop.py",
    "engine/VIA_TW_Ticker_Master_v0210.py",
    "engine/VRN_PanoramaProbe.py",
    "engine/VRN_BookCheck_v0100.py",
    "engine/VRN_TempStore_v0100.py",
    "engine/VRN_AstId_v0100.py",
    "engine/VRN_LocalDB_v0100.py",
    "engine/VRN_PageRegions_v0100.py",
    "engine/VRN_DataFrame_v0100.py",
    "engine/VRN_TitleTrim_v0100.py",
    "engine/VRN_Lock_v0100.py",
    "engine/VRN_Focus_v0100.py",
    "engine/VRN_Matrix_v0100.py",
    "engine/VRN_TickerRecord_v0100.py",
    *MOTHER_ENGINE_FILES,
    "ssot/VIS_VRN_TickerFilenameSSOT_v0100.py",
)
# VRN 自己的知識書（INDEX 冊）。copied_from = 倉庫內原書（只做來源比對，VRN 副本為準）。
SSOT_BOOKS = (
    {"path": "ssot/VRN_Broker_Dict_v0100.json", "role": "券商同義字（中文名 → 縮寫／別名）",
     "consumers": ["first_page", "database"], "copied_from": "attachments/VRN_Broker_Dict_v0100.json"},
    {"path": "ssot/VRN_Rating_Dict_v0100.json", "role": "評等同義字（BUY/HOLD/SELL/NOT_RATED/ADD）",
     "consumers": ["first_page", "database"], "copied_from": "attachments/VRN_Rating_Dict_v0100.json"},
    {"path": "ssot/VIS_VRN_TickerFilenameSSOT_v0100.py", "role": "檔名代號 SSOT（代號／三平台 regex、年份帶）",
     "consumers": ["first_page"], "copied_from": "attachments/VIS_VRN_TickerFilenameSSOT_v0100.py"},
    {"path": "knowledge/SYNONYM_LIBRARY_v4.json", "role": "同義字庫 v4（來源分層、差異全保留；broker / rating / target_price 等 scope）",
     "consumers": ["first_page", "database"]},
    {"path": "knowledge/SYNONYM_LIBRARY_v3.json", "role": "同義字庫 v3（v4 的基底，保留）", "consumers": []},
    {"path": "knowledge/VRN_WORKFLOW_SPEC_v0200.md", "role": "VRN 工作流程規格 v0.2.0", "consumers": ["spec"]},
    {"path": "registry/VRN_BROKER_LIST_v01.json", "role": "券商清單 v01（母倉 VRN 冊的鏡像）", "consumers": ["evidence_core"]},
    {"path": "engine/VIA_TW_Ticker_Master_v0210.py", "role": "台股代碼主檔 regex（ETF／個股／三平台）", "consumers": ["first_page", "autotest"]},
    {"path": "references/intake/VIA_SSOT_Additive_Audit_v0100/baseline/VIA_Financial_Institution_SSOT_v0100.json",
     "role": "金融機構 SSOT（28 券商、6 評等鍵；凍結稽核包，只讀）", "consumers": ["evidence_core", "autotest"], "frozen": True},
    {"path": "references/intake/VIA_SSOT_Additive_Audit_v0100/FILENAME_RESULTS.json",
     "role": "106 檔名 oracle（凍結稽核包，只讀）", "consumers": ["autotest", "main"], "frozen": True},
    {"path": "ssot/VRN_REGEX_SSOT_v0100.json", "role": "VRN REGEX 冊（本入口生成）", "consumers": ["main"], "generated": True},
    {"path": "ssot/VRN_SYNONYM_SSOT_v0100.json", "role": "VRN 同義字冊（本入口生成）", "consumers": ["main"], "generated": True},
    # 2026-10-10 從其他對話與母倉 main 收來的冊（操作員「擷取其他對話中的 BROKER DICT RATING LIST TARGET PRICE DICT EMAIL TEL
    # 所有 FINANCIAL ACCOUNT AND VALIDATION METHOD 快整合進入實測階段」）。逐位元副本，出處逐本寫在 VRN_BOOKS_PROVENANCE。
    {"path": "ssot/VRN_BOOKS_PROVENANCE_v0100.json", "role": "收來的冊：出處（母倉路徑、commit、哪個對話建的）、沒收的和為什麼",
     "consumers": ["main", "bookcheck"]},
    {"path": "ssot/VRN_S05_FieldRegistry_v0103.json", "role": "S05 欄位冊：評等清單、目標價字典、電郵網域、40 條 regex、30 基本欄 + 76 財報欄（各帶驗證法）",
     "consumers": ["bookcheck"], "mother": "registry/VRN_S05_FieldRegistry_v0103.json@ef8e3ef9"},
    {"path": "ssot/VRN_Broker_Dict_v0103.json", "role": "券商字典 v0103（28 家正典 + 網域別名；母倉主線 7928007e 刪除，此處只增不減保留）",
     "consumers": ["bookcheck"], "mother": "functional modules/VRN/VRN_Broker_Dict_v0103.json@130040c2"},
    {"path": "ssot/VIA_SSOT_SynonymUnion_v0107.json", "role": "同義字聯集：財報科目 632、評等 189、券商 277（拒絕清單不套用）",
     "consumers": ["bookcheck"], "mother": "registry/VIA_SSOT_SynonymUnion_v0107.json@ef8e3ef9"},
    {"path": "ssot/VRN_FieldRules_SSOT_v0101.json", "role": "欄位規則 v0101：評等找字、目標價、聯絡、財報恆等式 7 條",
     "consumers": ["evidence_core", "bookcheck"], "mother": "registry/VRN_FieldRules_SSOT_v0101.json@ef8e3ef9"},
    {"path": "ssot/VIA_VRN_ReportFieldRules_SSOT_v0101.json", "role": "研報欄位尺 v0101：電話次序與守衛、職稱、網域補遺、檔名評等格位",
     "consumers": ["evidence_core", "bookcheck"], "mother": "registry/VIA_VRN_ReportFieldRules_SSOT_v0101.json@ef8e3ef9"},
    {"path": "ssot/VIA_VRN_FieldSpec_SSOT_v0100.json", "role": "15 欄規格與六態（G12；鏡像缺席時 VRN 自己判）",
     "consumers": ["evidence_core", "autotest", "bookcheck"], "mother": "registry/VIA_VRN_FieldSpec_SSOT_v0100.json@ef8e3ef9"},
    {"path": "ssot/VIA_VRN_ExtractRules_SSOT_v0100.json", "role": "擷取規則：R-CMP-01 對照容差（目標價 0.5%、營收 1%、EPS 1%）",
     "consumers": ["bookcheck"], "mother": "registry/VIA_VRN_ExtractRules_SSOT_v0100.json@ef8e3ef9"},
    {"path": "ssot/VRN_FinLexicon_SSOT_v0109.json", "role": "財報科目字典 v0109：76 個正典科目中英同義字、噪音規則",
     "consumers": ["bookcheck"], "mother": "functional modules/VRN/SSOT/VRN_FinLexicon_SSOT_v0109.json@ef8e3ef9"},
    {"path": "ssot/VRN_Contact_Regex_v0100.json", "role": "聯絡擷取式：目標價、評等、券商片段、電郵、電話",
     "consumers": ["reference"], "mother": "functional modules/VRN/knowledge/VRN_Contact_Regex_v0100.json@ef8e3ef9"},
    {"path": "ssot/VIA_Validation_SSOT_v0100.json", "role": "驗證法登記（VRN：驗證邏輯 5、結果驗證 7、交叉核對 12）",
     "consumers": ["reference"], "mother": "registry/VIA_Validation_SSOT_v0100.json@ef8e3ef9"},
    {"path": "ssot/VRN_03SSOT_PROVENANCE_v0100.json", "role": "操作員本機 03_ssot 收進來的 36 本：母倉路徑、commit、SHA-256；沒收的 17 本與理由",
     "consumers": ["main", "p13"]},
    # 2026-10-11 個股報告拆解與還原（操作員「檔案名稱拆解 首頁的資訊區 本文區切割資訊區 年度財報告面左頁對切 不同圖在上下切 …
    # 還原資料轉為資料庫並擷取到對的輸出值並驗算通過」）：母倉引擎逐位元組在 engine/mother/，讀下面這些冊。
    {"path": "ssot/VRN_ENGINES_PROVENANCE_v0100.json", "role": "母倉引擎 ENG392/393/394/395/396 與它們的冊：母倉路徑、commit、SHA-256；沒收的與理由",
     "consumers": ["main", "regions"]},
    {"path": "ssot/VRN_LayoutRestore_SSOT_v0100.json", "role": "版面還原冊：區（資訊／本文／圖／排除）、字級、XY 切的最小間隙、表格驗算",
     "consumers": ["regions"], "mother": "functional modules/VRN/SSOT/VRN_LayoutRestore_SSOT_v0100.json@c88acc4f"},
    {"path": "ssot/VRN_AnnualExtract_SSOT_v0100.json", "role": "年報擷取冊：79 個財報科目中英列標、年度 regex、比率公式",
     "consumers": ["regions"], "copied_from": "attachments/VRN_AnnualExtract_SSOT_v0100.json"},
    {"path": "ssot/VRN_Method_SSOT_v0100.json", "role": "方法冊 def01–def19：損益、資產負債、現金流恆等式，比率、成長、容差、狀態",
     "consumers": ["regions"], "copied_from": "attachments/VRN_Method_SSOT_v0100.json"},
    {"path": "ssot/VRN_FinIdentity_SSOT_v0100.json", "role": "財報加減除驗算式 39 條（每條註明出處；運算元 = AnnualExtract 的 key）",
     "consumers": ["regions"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0100.json", "role": "VRN 輸出表頭正本：13 張表的欄名、型別、必填、主鍵、最少列數、中文與顯示名（G16 DataFrame 照它驗）",
     "consumers": ["dataframe"]},
    # 2026-10-11 標題分拆、TRIM、鎖（操作員「只擷取個股報告的標題分拆識別 首頁及年度財報頁來進行基本資料清理TRIM後分拆識別
    # 實測實修正 正確鎖功能鎖成功部分及引擎 位成功的持續實測實際修正直到輸出正確可驗證無誤」）。
    {"path": "ssot/VRN_TitleTrim_SSOT_v0100.json", "role": "標題／TRIM／鎖冊：TRIM 動的字元、標題與首頁與年度財報頁的字詞和 regex、狀態、"
     "什麼可以上鎖、哪組已知答案證明哪支引擎", "consumers": ["titletrim", "lock"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0101.json", "role": "VRN 輸出表頭 v0101：v0100 的 13 張原封不動 + G17／G18 五張（標題、部位、"
     "年度財報格、鎖態、待修清單），共 18 張", "consumers": ["dataframe"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0102.json", "role": "VRN 輸出表頭 v0102：v0101 的 18 張原封不動 + G19 聚焦清單一張，共 19 張",
     "consumers": ["dataframe"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0103.json", "role": "VRN 輸出表頭 v0103（實測 2026-10-12）：v0102 + 兩欄改非必填"
     "（資料庫引擎沒印期別的數字、表格沒有列標的數字照實留空）", "consumers": ["dataframe"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0104.json", "role": "VRN 輸出表頭 v0104（2026-10-12 四碼代號 15 欄）：v0103 的 19 張原封不動 + vrn_ticker_record，共 20 張",
     "consumers": ["dataframe"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0105.json", "role": "VRN 輸出表頭 v0105（實測 2026-10-15 產業報告一報告 N 列）：vrn_basic_info 主鍵改成"
     "（ReportID, TW_TICKER），20 張表的欄名／型別／必填原封不動", "consumers": ["dataframe"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0106.json", "role": "VRN 輸出表頭 v0106（實檔實測 2026-10-15 三條報告路徑同步）：vrn_focus_files 多一欄"
     " process（FULL／COVERAGE／REGISTER，G06 照它分流），其餘 20 張表原封不動", "consumers": ["dataframe"]},
    {"path": "ssot/VRN_Output_Header_SSOT_v0107.json", "role": "VRN 輸出表頭 v0107（操作員 2026-10-16 一標題四重點）：多一張 vrn_summary_points"
     "（一份報告四列，鍵 file + point_no），v0106 的 20 張逐字不動", "consumers": ["dataframe"]},
    {"path": "ssot/VRN_TickerRecord_SSOT_v0100.json", "role": "四碼代號 15 欄的合併冊：券商別名、e-mail 網域、評等詞、標籤、regex 從倉內每一本來源冊合併（去重、來源全列、衝突照列不裁）；build-book 生成，舊了 selftest 就紅",
     "consumers": ["record", "main"], "generated": True},
    {"path": "ssot/VRN_EngineLock_SSOT_v0100.json", "role": "引擎鎖：已知答案全過的引擎與冊的 AST／JSON 指紋（VRN_Main_v0100.py lock 寫，"
     "check 驗）", "consumers": ["lock", "main"], "generated": True},
    {"path": "ssot/VRN_OperatorLabels_SSOT_v0100.json", "role": "操作員 2026-10-11 上傳 5 支 .py 挑過的資料：列標、整列標 regex、TWSE/yfinance 欄名對照、券商叫法（候選）",
     "consumers": ["regions"]},
    {"path": "ssot/VRN_TEMP_POLICY_v0100.json", "role": "TEMP 與刪除原則（母倉 R-TEMP-01 同規矩，VRN 更嚴）", "consumers": ["tempstore"]},
    {"path": "ssot/VRN_ID_SSOT_v0100.json", "role": "AST 編號冊：模組、類別、函式的編號、分類、說明、版本（本入口生成）",
     "consumers": ["main", "registry"], "generated": True},
)
# 2026-10-20 操作員「解決 GITHUB 衝突問題」。每一輪 build／lock 會**整個重寫**的檔，
# 但本身不在 SSOT_BOOKS 上 —— 旁邊寫明為什麼不在，不然下一個人會以為是漏填。
GENERATED_OFF_BOOK = (
    {"path": "VRN_REGISTRY_v0100.json", "by": "build",
     "off_book": "它就是註冊冊本身，不是 ssot/ 底下的冊"},
    {"path": "ssot/VRN_SSOT_INDEX_v0100.json", "by": "build",
     "off_book": "INDEX 冊逐本記每一本的 sha256；把自己列進 SSOT_BOOKS 會變成記自己的指紋，寫完當場就對不上"},
    {"path": "ssot/VRN_ToolManifest_v0100.json", "by": "build",
     "off_book": "借出工具冊由 engine/VRN_ToolBridge_v0100.py 自己寫、自己驗（P25 閘）"},
)
# 只往後加、從不改舊行的檔（量過才敢這樣列：兩條分支對 VRN_SYSTEM_v0100.md 都是 913+/0-、327+/0-）。
MERGE_UNION_FILES = ("VRN_SYSTEM_v0100.md",)
GITATTRIBUTES_PATH = VRN_ROOT / ".gitattributes"
# VRN 會「互動」但不屬於 VRN 的東西：缺席時 VRN 照跑（證據核心退回內建表），只在報告裡照實寫。
INTERACTIONS = (
    {"name": "VCGC mirror", "path": "supportive modules/registry", "level": "repo",
     "role": "母倉 VCGC 工具（181 欄位閘 / 182 欄位尺 / SUP_MDL749）與三本規則書；VCGC 的，不是 VRN 的。"
             "CGC_MDL177 批679 拒絕清單 VRN 不套用（操作員 2026-10-10「GF 照原文顯示」）"},
    {"name": "VCGC sync tool", "path": "scripts/VIA_VCGC_Sync.py", "level": "repo", "role": "VCGC 鏡像逐位元檢查（AutoTestLoop G10）"},
    {"name": "TS roster", "path": "src/lib/via/incoming-roster.ts", "level": "repo", "role": "64 個 roster 檔名（AutoTestLoop G03 額外名單）"},
    {"name": "VCGC token 預算", "path": "config/ssot/VIA_SystemMaster.via", "level": "repo",
     "role": "#/token_governance/capsule_policy（REFERENCE_FIRST_DELTA_ONLY · max_chars · max_items）。"
             "操作員 2026-10-16「參數可向其他系統拿，只要不衝突」：VRN 只讀這份正本，不自己訂一份預算。"
             "缺席時用本檔內建上限，並在報告裡標成 engine-default —— 跟 VUE 同一套誠實規則。"},
)
TEXT_SUFFIXES = {".py", ".ps1", ".psm1", ".json", ".jsonl", ".md", ".txt", ".csv", ".html", ".htm", ".yml", ".yaml", ".xml"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
STATUS_ORDER = {"FAIL": 0, "WARN": 1, "SKIP": 2, "PASS": 3}
STATUS_ZH = {"PASS": "綠", "WARN": "黃", "FAIL": "紅", "SKIP": "略"}
RE_CALLS = {"compile", "search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split"}
# positional index of `flags` in each re.* signature (compile(p, flags); search(p, s, flags); sub(p, r, s, count, flags) ...)
FLAG_POSITION = {"compile": 1, "search": 2, "match": 2, "fullmatch": 2, "findall": 2, "finditer": 2,
                 "split": 3, "sub": 4, "subn": 4}
REGEX_TABLE_NAME = re.compile(r"(REGEX|PATTERN|_LOCK$|_RE$|^RX_)")
FAMILY_RULES = (
    ("CONTACT", re.compile(r"@|mail|phone|tel|分機|e-?mail|analyst|分析師", re.I)),
    ("TARGET_PRICE", re.compile(r"target|目標|tp_|\btp\b|price|現價|股價|收盤", re.I)),
    ("RATING", re.compile(r"rating|評等|買進|中立|賣出|buy|hold|sell|outperform", re.I)),
    ("BROKER", re.compile(r"broker|券商|投顧|證券|securities|domain", re.I)),
    ("DATE", re.compile(r"date|年|月|日|month|roc|民國|\(20\)|yy|mmdd|jan|feb", re.I)),
    ("TICKER", re.compile(r"ticker|\bTT\b|\.TW|代號|stock|etf|\[1-9\]\\d\{3\}|1-9\]\[0-9\]\{3\}", re.I)),
    ("FINANCIAL", re.compile(r"eps|營收|毛利|淨利|revenue|margin|table|column|fy|季|ttm|\bq[1-4]\b", re.I)),
    ("TEXT", re.compile(r"\\s|space|blank|punct|unicode|cjk|\\u|一-", re.I)),
)


# =============================================================================
# 01. 小工具
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC001 · LOGIC
def def_console_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


# [VRN-ID] VRN-MAN001-FNC002 · LOGIC
def def_rel(path: Path, root: Path = VRN_ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


# [VRN-ID] VRN-MAN001-FNC003 · LOGIC
def def_sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# [VRN-ID] VRN-MAN001-FNC004 · LOGIC
def def_sha256_file(path: Path) -> str:
    """Text files hash with LF line endings, so a Windows CRLF checkout keeps the same registry."""
    raw = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        raw = raw.replace(b"\r\n", b"\n")
    return def_sha256_bytes(raw)


# [VRN-ID] VRN-MAN001-FNC005 · LOGIC
def def_text_len(path: Path) -> int:
    """Byte length with LF line endings for text files (same rule as def_sha256_file)."""
    raw = path.read_bytes()
    return len(raw.replace(b"\r\n", b"\n")) if path.suffix.lower() in TEXT_SUFFIXES else len(raw)


# [VRN-ID] VRN-MAN001-FNC006 · LOGIC
def def_sha256_stream(path: Path) -> str:
    """Raw SHA-256 of a sample file, read in 1 MiB chunks (reports can be large)."""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# [VRN-ID] VRN-MAN001-FNC007 · IO
def def_write_json(path: Path, payload: Any) -> None:
    """原子換檔寫 JSON（實作在 def_write_atomic，MAIN 這一側只有那一份）。

    2026-10-19：這裡本來是裸的 `write_text`。寫到一半被砍（或兩個行程同寫同一個檔）
    留下的就是半份 JSON，而下一個讀它的人拿到 JSONDecodeError —— 收尾報告正是
    def_sync_blockers 要讀回來的那一份，所以半份報告等於整條收尾鏈斷在看不見的地方。
    四支引擎（AutoTestLoop、RunCache、Lock、TempStore）早就這樣寫了，MAIN 漏了。
    一邊寫一邊讀 400 次：舊寫法讀到半份 296 次，原子換檔 0 次。
    """
    def_write_atomic(path, json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False) + "\n")


# [VRN-ID] VRN-MAN001-FNC128 · IO
def def_write_atomic(path: Path, text: str, newline: Optional[str] = "\n") -> None:
    """原子換檔寫一份完整文字檔 —— MAIN 這一側只有這一個實作。

    tmp 一定在**同一個資料夾**：os.replace 跨檔案系統會失敗。
    `newline=None` 是給那些本來就吃平台換行的檔用的，不在這裡偷偷改掉它們的行尾。

    **為什麼是 mkstemp 而不是自己組檔名**（Codex PR #72 P1，實測證實）：
    我本來組的是 `<名字>.<pid>.<thread>.tmp` —— 可預測。輸出夾若是 /tmp 這種別人也寫得進去的
    地方，攻擊者先在那個名字上放一個 symlink，`write_text` 就會跟著它走：
    實驗裡「受害者檔」被報告內容整個覆蓋，而 report.json 自己變成指向它的 symlink。
    `mkstemp` 用 O_CREAT|O_EXCL 建檔，名字是隨機的，既不可預測、存在就失敗，兩條路都堵住。
    順帶它也解決了撞名（本來靠 pid+thread 擋的那件），uniqueness 由 O_EXCL 保證。

    **權限**（同一輪 Codex P1，也實測證實）：裸的 `write_text` 蓋舊檔會沿用舊檔的 mode，
    換成 tmp＋rename 之後變成沿用 tmp 的 —— 實測 0600 的報告被換成 0644，等於把內容攤開給
    同機器其他人看。所以目標檔存在時，先把它的 mode 抄到 tmp 上再換。
    目標不存在時留 mkstemp 的 0600（比原本的 umask 預設更緊，不會變鬆）。
    **Windows 上這一段幾乎是空的**：那裡 os.chmod 只認唯讀位元，POSIX 權限位不存在，
    而 os.replace 會讓目標沿用來源的 ACL —— 目標原本的 ACL 保不住，stdlib 也沒有 API 能保。
    照實寫在這裡，不假裝那個平台也防住了。

    不 fsync：`os.replace` 保證的是「不會看到半份」，fsync 保證的是「斷電後還在」。
    這些檔每一輪都重寫，斷電後本來就要重跑，為那個保證每次多付幾毫秒不值得。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    keep_mode = None
    try:
        keep_mode = stat.S_IMODE(path.stat().st_mode)  # 舊檔的權限要留住，不是繼承 umask
    except OSError:
        pass
    handle_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        handle = os.fdopen(handle_fd, "w", encoding="utf-8", newline=newline)
    except BaseException:
        os.close(handle_fd)                            # fdopen 自己失敗時 fd 還開著（CI 跑 -W error::ResourceWarning）
        tmp.unlink(missing_ok=True)
        raise
    try:
        with handle:
            handle.write(text)
        if keep_mode is not None:
            os.chmod(tmp, keep_mode)
        def_retry_access(lambda: os.replace(tmp, path))
    except BaseException:
        tmp.unlink(missing_ok=True)                    # 失敗就連 tmp 都不留；原檔一個位元組都沒動
        raise


ACCESS_ATTEMPTS = 20
ACCESS_PAUSE = 0.05                                    # 20 × 50ms ＝ 最多 1 秒


# [VRN-ID] VRN-MAN001-FNC129 · LOGIC
def def_retry_access(action: Callable[[], Any]) -> Any:
    """Windows 上「檔案正被別人開著」是暫時的，不是壞了 —— 等一下再試，不要炸掉。

    2026-10-19 CI 教的（這台 Linux 驗不到）：`os.replace` 在目標檔被另一個握把開著時
    會丟 `PermissionError: [WinError 5]`，讀的那一側在換檔的瞬間開檔也會。
    兩邊都是毫秒級的窗口 —— 讀報告的人、防毒、索引器都會造成它。
    不重試的話，原子寫入在操作員那台會把「讀到半份」換成「這一輪直接炸掉」，那不是改善。
    撐過 1 秒還是不行就照實丟出去：那就不是暫時的了。
    """
    for attempt in range(ACCESS_ATTEMPTS):
        try:
            return action()
        except PermissionError:
            if attempt == ACCESS_ATTEMPTS - 1:
                raise
            time.sleep(ACCESS_PAUSE)
    return None                                        # unreachable：最後一輪不是 return 就是 raise


# [VRN-ID] VRN-MAN001-FNC008 · IO
def def_read_json(path: Path) -> Any:
    """讀的那一側也要撐過換檔的瞬間 —— 見 def_retry_access。檔案不在是 FileNotFoundError，不重試。"""
    def_open = lambda: path.open(encoding="utf-8-sig")  # noqa: E731
    with def_retry_access(def_open) as handle:
        return json.load(handle)


# [VRN-ID] VRN-MAN001-FNC009 · LOGIC
def def_row(gate: str, item: str, status: str, detail: str = "", **extra: Any) -> Dict[str, Any]:
    row = {"gate": gate, "item": item, "status": status, "detail": detail}
    row.update(extra)
    return row


# [VRN-ID] VRN-MAN001-FNC010 · LOGIC
def def_counts(rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    out = {k: 0 for k in STATUS_ORDER}
    for r in rows:
        out[r["status"]] = out.get(r["status"], 0) + 1
    return out


# [VRN-ID] VRN-MAN001-FNC011 · VALIDATE
def def_verdict(rows: Sequence[Dict[str, Any]]) -> str:
    c = def_counts(rows)
    return "RED" if c["FAIL"] else ("AMBER" if c["WARN"] else "GREEN")


# [VRN-ID] VRN-MAN001-FNC012 · LOGIC
def def_progress(step: int, total: int, text: str) -> None:
    pct = int(100 * step / max(1, total))
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
    print(f"[VRN-MAIN {step}/{total} {pct:3d}%] [{bar}] {text}", flush=True)


# [VRN-ID] VRN-MAN001-FNC013 · LOGIC
def def_jsonable(obj: Any) -> Any:
    """Sets / tuples / compiled patterns -> plain JSON, sorted, so every build is byte-identical."""
    if isinstance(obj, dict):
        return {str(k): def_jsonable(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (set, frozenset)):
        return sorted((def_jsonable(x) for x in obj), key=lambda x: json.dumps(x, ensure_ascii=False))
    if isinstance(obj, (list, tuple)):
        return [def_jsonable(x) for x in obj]
    if isinstance(obj, re.Pattern):
        return obj.pattern
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


# [VRN-ID] VRN-MAN001-FNC014 · IO
def def_load_module(name: str, path: Path):
    with _MODULE_LOCK:                                    # 2026-10-13: the pre-steps run side by side; a module is loaded once
        return def_load_module_once(name, path)


_MODULE_LOCK = threading.RLock()


# [VRN-ID] VRN-MAN001-FNC096 · IO
def def_load_module_once(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


# [VRN-ID] VRN-MAN001-FNC015 · LOGIC
@contextlib.contextmanager
def def_quiet():
    """Engines print while loading; book builds must stay silent and deterministic.  While the pre-steps run side by side
    (sys.stdout is a def_ThreadQuietStream) only this thread is silenced: swapping sys.stdout from several threads would lose
    the console for good."""
    sink = io.StringIO()
    if isinstance(sys.stdout, def_ThreadQuietStream):
        stack = _QUIET_TLS.__dict__.setdefault("sinks", [])
        stack.append(sink)
        try:
            yield sink
        finally:
            stack.pop()
        return
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        yield sink


_QUIET_TLS = threading.local()


# [VRN-ID] VRN-MAN001-CLS002 · CLASS
class def_ThreadQuietStream:
    """sys.stdout / sys.stderr while the pre-steps run side by side: a thread inside def_quiet() writes to its own sink."""

    # [VRN-ID] VRN-MAN001-FNC097 · INIT
    def __init__(self, real: Any) -> None:
        self.real = real

    # [VRN-ID] VRN-MAN001-FNC098 · LOGIC
    def write(self, text: str) -> int:
        stack = getattr(_QUIET_TLS, "sinks", None)
        if stack:
            return stack[-1].write(text)
        return self.real.write(text)

    # [VRN-ID] VRN-MAN001-FNC099 · LOGIC
    def flush(self) -> None:
        self.real.flush()

    # [VRN-ID] VRN-MAN001-FNC100 · INIT
    def __getattr__(self, name: str) -> Any:
        return getattr(self.real, name)


# 加速器覆蓋（操作員 2026-10-10「加速器深入所有動作」）：每個動作走哪一條道，照實記下來，P09 列出。
ACCEL_COVERAGE: List[Dict[str, Any]] = []


# [VRN-ID] VRN-MAN001-FNC016 · LOGIC
def def_accel_note(action: str, lane: str, items: int, seconds: float = 0.0, why: str = "",
                   failed: int = 0, by_design: bool = False) -> None:
    # failed / by_design 是結構化的事實（掛了幾塊、逐一跑是不是照設計）：P09 的燈號讀它們，
    # 不去解析 why 那句中文 —— 2026-10-21 第二十四輪。
    ACCEL_COVERAGE.append({"action": action, "lane": lane, "items": items, "seconds": round(seconds, 3), "why": why,
                           "failed": int(failed or 0), "by_design": bool(by_design)})


# [VRN-ID] VRN-MAN001-FNC017 · LOGIC
def def_parallel_map(fn: Callable[[Any], Any], items: Sequence[Any], action: str = "") -> List[Any]:
    """Accelerator lane when it is mounted (accel_map), else the same thread pool from the stdlib.
    Results always come back in input order; `action` names the step in the coverage map."""
    items = list(items)
    started = time.perf_counter()
    accel = sys.modules.get("VIA_SuperAccel_Module") or VIA_ACCEL
    if accel is not None and hasattr(accel, "accel_map"):
        try:
            pairs = accel.accel_map(fn, items)
            if len(pairs) == len(items) and all(isinstance(p, tuple) and len(p) == 2 for p in pairs):
                if all(ok for ok, _v in pairs):
                    if action:
                        def_accel_note(action, "accel_map", len(items), time.perf_counter() - started)
                    return [v for _ok, v in pairs]
        except Exception:
            pass
    with ThreadPoolExecutor(max_workers=min(8, (os.cpu_count() or 2))) as pool:
        out = list(pool.map(fn, items))
    if action:
        def_accel_note(action, "thread_pool", len(items), time.perf_counter() - started, "加速器未掛上：stdlib 執行緒池")
    return out


# =============================================================================
# 02. 加速器（路徑載入；本倉不放加速器程式碼）
# =============================================================================
ACCEL_STATE: Dict[str, Any] = {"loaded": False, "home": "", "source": "", "canonical": "", "celeritas": "",
                                 "activated": {}, "error": ""}


# [VRN-ID] VRN-MAN001-FNC018 · LOGIC
def def_accel_candidates(cli_home: str = "") -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    if cli_home:
        out.append(("--accel-home", Path(cli_home)))
    env = os.environ.get("VIA_ACCEL_HOME", "").strip()
    if env:
        out.append(("VIA_ACCEL_HOME", Path(env)))
    probe = VRN_ROOT
    while True:
        out.append(("walk-up", probe / "supportive modules"))
        if probe.parent == probe:
            break
        probe = probe.parent
    profile = os.environ.get("USERPROFILE", "")
    if profile:
        out.append(("mother default", Path(profile).joinpath(*MOTHER_ACCEL_DEFAULT)))
    return out


# [VRN-ID] VRN-MAN001-FNC019 · IO
def def_load_accelerator(cli_home: str = "", activate: bool = False) -> Dict[str, Any]:
    """Mount VIA_SuperAccel_Module by path; every VRN engine loaded afterwards in this process gets it via its bridge."""
    mod = sys.modules.get("VIA_SuperAccel_Module") or VIA_ACCEL
    if mod is not None:
        ACCEL_STATE.update(loaded=True, source=ACCEL_STATE.get("source") or "bridge (already mounted)",
                           home=ACCEL_STATE.get("home") or str(Path(getattr(mod, "__file__", "")).parent))
    else:
        for source, home in def_accel_candidates(cli_home):
            entry = home / ACCEL_ENTRY
            if not entry.is_file():
                continue
            try:
                mod = def_load_module("VIA_SuperAccel_Module", entry)
                ACCEL_STATE.update(loaded=True, home=str(home), source=source, error="")
                break
            except BaseException as error:  # noqa: BLE001 - a broken accelerator never stops VRN
                ACCEL_STATE.update(error=f"{source}: {error.__class__.__name__}: {error}"[:300])
                mod = None
    if mod is None:
        return ACCEL_STATE
    ACCEL_STATE["canonical"] = str(getattr(mod, "CANONICAL", "") or "")
    # 2026-10-18：一個行程只 activate 一次 —— 最早要求的人套上，後面的人（P04）讀同一份 ACCEL_STATE 回報。
    # 不這樣擋的話，all 鏈在第一步套一次、run 的 P04 再套一次，同一個判斷做兩遍。
    if activate and hasattr(mod, "activate") and not ACCEL_STATE["activated"]:
        try:
            report = mod.activate(apply_limits=True)
            ACCEL_STATE["activated"] = {k: report.get(k) for k in
                                        ("celeritas", "libs_total", "libs_available", "capability_real",
                                         "capability_total", "thread_budget", "mode", "err")}
        except BaseException as error:  # noqa: BLE001
            ACCEL_STATE["activated"] = {"err": f"{error.__class__.__name__}: {error}"[:200]}
    try:
        cel = mod.celeritas() if hasattr(mod, "celeritas") else None
        if cel is not None:
            ACCEL_STATE["celeritas"] = f"{getattr(cel, '__version__', '?')} · {Path(getattr(cel, '__file__', '')).name}"
    except BaseException:  # noqa: BLE001
        pass
    return ACCEL_STATE


# [VRN-ID] VRN-MAN001-FNC020 · GATE
def def_gate_accel(cli_home: str = "", activate: bool = False) -> List[Dict[str, Any]]:
    st = def_load_accelerator(cli_home, activate)
    if not st["loaded"]:
        hint = "放 VIA_ACCEL_HOME=<母倉 supportive modules> 或 --accel-home；" + (st["error"] or "沒有找到 VIA_SuperAccel_Module.py")
        return [def_row("P04 ACCEL", "Python 加速器", "WARN", "未載入 · fallback 無加速（判讀不受影響）· " + hint)]
    detail = f"{st['canonical'] or ACCEL_ENTRY} · 來源 {st['source']} · {st['home']}"
    rows = [def_row("P04 ACCEL", "Python 加速器", "PASS", detail)]
    if st["celeritas"]:
        rows.append(def_row("P04 ACCEL", "VeritasCeleritas", "PASS", st["celeritas"]))
    else:
        rows.append(def_row("P04 ACCEL", "VeritasCeleritas", "WARN", "加速器在，但 Celeritas 本體沒有載入"))
    if st["activated"]:
        a = st["activated"]
        rows.append(def_row("P04 ACCEL", "activate()", "PASS" if not a.get("err") else "WARN",
                            f"執行緒預算 {a.get('thread_budget')} · 模式 {a.get('mode')} · libs {a.get('libs_available')}/{a.get('libs_total')}"
                            + (f" · {a.get('err')}" if a.get("err") else "")))
    return rows


# =============================================================================
# 03. REGEX 冊（AST 逐條抽出）
# =============================================================================
# 掃描器自己的設定表（檔名清單），名字裡有 REGEX 但不是 regex。
SCANNER_CONFIG_TABLES = {"REGEX_SOURCES"}
# 2026-10-10 細分類（操作員「DATE BROKER DICT EMAIL 香港台灣TEL RATING LIST 三種代號 TARGET PRICE … REGEX SSOT 同義字要建構完成」）：
# family 照舊（只增不減），category 再把聯絡拆成 EMAIL／TEL_TW／TEL_HK、代號拆成三種。
CATEGORIES = ("DATE", "BROKER", "EMAIL", "TEL_TW", "TEL_HK", "TEL_INTL", "RATING", "TICKER_TW", "TICKER_YF", "TICKER_BBG",
              "TARGET_PRICE", "NAME", "ADJ_CLOSE", "FINANCIAL", "CONTACT", "TEXT", "OTHER",
              # 2026-10-11：香港／海外代號、年度（民國年、半年、季）、評價法、版面、文件類別
              "TICKER_HK", "TICKER_INTL", "YEAR", "VALUATION", "LAYOUT", "DOC_CLASS")
BOOK_REGEX_CATEGORY = (
    (re.compile(r"^(DATE|QUARTER|YEAR|MONTH)_|(^|\.)date|period"), "DATE"),
    (re.compile(r"TW_YFINANCE|yfinance|\.TW", re.I), "TICKER_YF"),
    (re.compile(r"BLOOMBERG|bloomberg|bbg", re.I), "TICKER_BBG"),
    (re.compile(r"TICKER|ticker|code", re.I), "TICKER_TW"),
    (re.compile(r"EMAIL|e-?mail", re.I), "EMAIL"),
    (re.compile(r"hk_|HK_|_HK|hk_phone|852", re.I), "TEL_HK"),
    (re.compile(r"intl", re.I), "TEL_INTL"),
    (re.compile(r"TEL|phone|tpe|mobile", re.I), "TEL_TW"),
    (re.compile(r"TARGET|UPSIDE|target_price|\btp\b", re.I), "TARGET_PRICE"),
    (re.compile(r"RATING|rating", re.I), "RATING"),
    (re.compile(r"broker", re.I), "BROKER"),
    (re.compile(r"name|title", re.I), "NAME"),
    (re.compile(r"NUMBER|PERCENT|FINANCE|PARENS|CURRENCY|AMOUNT|noise|column|section|unit", re.I), "FINANCIAL"),
)


# [VRN-ID] VRN-MAN001-FNC021 · LOGIC
def def_category(family: str, pattern: str, qualname: str = "") -> str:
    """The finer category of one code regex (family is kept as it was)."""
    if family == "CONTACT":
        if "@" in pattern or "mail" in pattern.lower():
            return "EMAIL"
        if "852" in pattern:
            return "TEL_HK"
        if re.search(r"886|\\d|tel|phone|分機", pattern, re.I):
            return "TEL_TW"
        return "CONTACT"
    if family == "TICKER":
        if re.search(r"\\\.TW|TWO|\.tw", pattern):
            return "TICKER_YF"
        if re.search(r"(?<![A-Za-z])TT(?![A-Za-z])", pattern):
            return "TICKER_BBG"
        return "TICKER_TW"
    if family in ("OTHER", "TEXT") and ("name" in qualname.lower() or "公司" in pattern):
        return "NAME"
    return family


# [VRN-ID] VRN-MAN001-FNC022 · LOGIC
def def_book_category(name: str) -> str:
    for rule, category in BOOK_REGEX_CATEGORY:
        if rule.search(name):
            return category
    return "OTHER"


# [VRN-ID] VRN-MAN001-FNC023 · LOGIC
def def_book_patterns() -> List[Dict[str, Any]]:
    """Every regex the harvested books carry (S05 all_regex, phone order, contact block, FieldRules v0101 rules,
    contact regex, FinLexicon noise rules), named by its place in the book."""
    out: List[Dict[str, Any]] = []
    s05 = def_read_json(SSOT_DIR / "VRN_S05_FieldRegistry_v0103.json")
    for name, spec in (s05.get("all_regex") or {}).items():
        if isinstance(spec, dict) and isinstance(spec.get("pattern"), str):
            out.append({"book": "VRN_S05_FieldRegistry_v0103.json", "name": "all_regex." + name, "text": spec["pattern"],
                        "category": def_book_category(name)})
    rfr = def_read_json(SSOT_DIR / "VIA_VRN_ReportFieldRules_SSOT_v0101.json")
    pattern_keys = {"tw_title", "en_title", "tw_name", "en_name", "tpe_phone", "hk_phone", "email", "tw_mobile_phone", "intl_phone"}
    for part in ("as_given", "corrected", "corrected_v0101"):
        for key, text in ((rfr.get("contact_block") or {}).get(part) or {}).items():
            if isinstance(text, str) and key in pattern_keys:
                out.append({"book": "VIA_VRN_ReportFieldRules_SSOT_v0101.json", "name": f"contact_block.{part}.{key}", "text": text,
                            "category": def_book_category(key)})
    guard = ((rfr.get("phone") or {}).get("guard") or {}).get("cue_rx")
    if isinstance(guard, str):
        out.append({"book": "VIA_VRN_ReportFieldRules_SSOT_v0101.json", "name": "phone.guard.cue_rx", "text": guard, "category": "TEL_TW"})
    fr = (def_read_json(SSOT_DIR / "VRN_FieldRules_SSOT_v0101.json").get("rules") or {})

    # [VRN-ID] VRN-MAN001-FNC024 · LOGIC
    def walk(node: Any, trail: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{trail}.{k}" if trail else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                if isinstance(v, str) and re.search(r"(^|\.)[A-Za-z_]*rx[A-Za-z_]*$|regex|pattern", trail):
                    out.append({"book": "VRN_FieldRules_SSOT_v0101.json", "name": f"rules.{trail}[{i}]", "text": v,
                                "category": def_book_category(trail)})
                else:
                    walk(v, f"{trail}[{i}]")
        elif isinstance(node, str) and re.search(r"(^|\.)[A-Za-z_]*rx[A-Za-z_]*$|(^|\.)(regex|pattern)$", trail):
            out.append({"book": "VRN_FieldRules_SSOT_v0101.json", "name": "rules." + trail, "text": node,
                        "category": def_book_category(trail)})
    walk(fr, "")
    contact = def_read_json(SSOT_DIR / "VRN_Contact_Regex_v0100.json")
    for key, text in (contact.get("patterns") or {}).items():
        if isinstance(text, str):
            out.append({"book": "VRN_Contact_Regex_v0100.json", "name": "patterns." + key, "text": text, "category": def_book_category(key)})
    lex = def_read_json(SSOT_DIR / "VRN_FinLexicon_SSOT_v0109.json")
    for key, text in (lex.get("noise_rules") or {}).items():
        if isinstance(text, str):
            out.append({"book": "VRN_FinLexicon_SSOT_v0109.json", "name": "noise_rules." + key, "text": text, "category": "FINANCIAL"})
    out += def_book_patterns_regions()
    out += def_book_patterns_titletrim()
    return out


# [VRN-ID] VRN-MAN001-FNC078 · LOGIC
def def_book_patterns_regions() -> List[Dict[str, Any]]:
    """2026-10-11: the regexes of the books the page-regions lane reads (LayoutRestore, ReportEntities, DocClass, AnnualExtract),
    the frozen audit pack's ticker / date book (Hong Kong, overseas, ROC year, half-year) and the mother parser book."""
    out: List[Dict[str, Any]] = []

    # [VRN-ID] VRN-MAN001-FNC079 · LOGIC
    def rx_keys(book: str, data: Any, category_of: Any) -> None:
        # [VRN-ID] VRN-MAN001-FNC080 · LOGIC
        def walk(node: Any, trail: str) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, f"{trail}.{k}" if trail else str(k))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{trail}[{i}]")
            elif isinstance(node, str) and re.search(r"(_rx|\.rx|regex|pattern)$", trail):
                out.append({"book": book, "name": trail, "text": node, "category": category_of(trail)})
        walk(data, "")
    rx_keys("VRN_LayoutRestore_SSOT_v0100.json", def_read_json(SSOT_DIR / "VRN_LayoutRestore_SSOT_v0100.json"), lambda _t: "LAYOUT")
    rx_keys("VRN_DocClass_SSOT_v0100.json", def_read_json(SSOT_DIR / "03_ssot" / "VRN_DocClass_SSOT_v0100.json"), lambda _t: "FINANCIAL")
    rx_keys("VRN_ReportEntities_SSOT_v0100.json", def_read_json(SSOT_DIR / "03_ssot" / "VRN_ReportEntities_SSOT_v0100.json"),
            lambda t: "TARGET_PRICE" if t.startswith("target_price") else "VALUATION" if t.startswith("valuation") else "NAME")
    rx_keys("VRN_Report_Parser_Integrated_SSOT.json", def_read_json(SSOT_DIR / "03_ssot" / "VRN_Report_Parser_Integrated_SSOT.json"),
            lambda t: "DATE" if "date" in t else def_book_category(t))
    annual = def_read_json(SSOT_DIR / "VRN_AnnualExtract_SSOT_v0100.json")
    for key, text in (annual.get("year_regex") or {}).items():
        if isinstance(text, str):
            out.append({"book": "VRN_AnnualExtract_SSOT_v0100.json", "name": "year_regex." + key, "text": text, "category": "YEAR"})
    frozen = def_read_json(VRN_ROOT / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100" / "baseline" / "VRN_TickerDate_Regex_v0100.json")
    for key, text in (frozen.get("ticker_patterns") or {}).items():
        if isinstance(text, str):
            cat = ("TICKER_HK" if key.startswith("HK_") else "TICKER_YF" if key.endswith("YFINANCE") and "TW" in key
                   else "TICKER_BBG" if key.endswith("BLOOMBERG") and "TW" in key else "TICKER_TW" if "TW" in key else "TICKER_INTL")
            out.append({"book": "VRN_TickerDate_Regex_v0100.json", "name": "ticker_patterns." + key, "text": text, "category": cat})
    labels = def_read_json(SSOT_DIR / "VRN_OperatorLabels_SSOT_v0100.json") if (SSOT_DIR / "VRN_OperatorLabels_SSOT_v0100.json").is_file() else {}
    for key, spec in (labels.get("operand_patterns") or {}).items():
        for i, text in enumerate(spec.get("regex") or []):
            out.append({"book": "VRN_OperatorLabels_SSOT_v0100.json", "name": f"operand_patterns.{key}[{i}]", "text": text, "category": "FINANCIAL"})
    for key, text in (frozen.get("datetime_patterns") or {}).items():
        if isinstance(text, str):
            cat = "YEAR" if re.search(r"YEAR|QUARTER|HALF", key) else "DATE"
            out.append({"book": "VRN_TickerDate_Regex_v0100.json", "name": "datetime_patterns." + key, "text": text, "category": cat})
    return out


# [VRN-ID] VRN-MAN001-FNC082 · LOGIC
def def_book_patterns_titletrim() -> List[Dict[str, Any]]:
    """2026-10-11: the TitleTrim book's patterns (title, ticker, target-price change, cover, numbers)."""
    path = SSOT_DIR / "VRN_TitleTrim_SSOT_v0100.json"
    if not path.is_file():
        return []
    out: List[Dict[str, Any]] = []
    cat = {"ticker": "TICKER", "tp_change": "TARGET_PRICE", "title": "TEXT", "trim": "TEXT"}

    # [VRN-ID] VRN-MAN001-FNC083 · LOGIC
    def walk(node: Any, trail: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{trail}.{k}" if trail else str(k))
        elif isinstance(node, list):
            if trail.endswith("_rx"):
                for i, v in enumerate(node):
                    if isinstance(v, str):
                        out.append({"book": path.name, "name": f"{trail}[{i}]", "text": v, "category": "DATE"})
        elif isinstance(node, str) and trail.endswith("_rx"):
            leaf = trail.rsplit(".", 1)[-1]
            category = ("CONTACT" if leaf in ("email_rx", "tel_rx", "name_rx") else "DATE" if leaf == "date_rx"
                        else "FINANCIAL" if leaf == "number_rx" else cat.get(trail.split(".", 1)[0], def_book_category(leaf)))
            out.append({"book": path.name, "name": trail, "text": node, "category": category})
    walk(def_read_json(path), "")
    return out


# [VRN-ID] VRN-MAN001-FNC025 · LOGIC
def def_family(qualname: str, pattern: str) -> str:
    hay = qualname + " " + pattern
    for family, rule in FAMILY_RULES:
        if rule.search(hay):
            return family
    return "OTHER"


# [VRN-ID] VRN-MAN001-FNC026 · LOGIC
def def_regex_sites(rel: str, root: Path = VRN_ROOT) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    path = root / rel
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    literal: List[Dict[str, Any]] = []
    dynamic: List[Dict[str, Any]] = []

    # [VRN-ID] VRN-MAN001-FNC027 · LOGIC
    def flags_of(call: ast.Call) -> str:
        position = FLAG_POSITION.get(call.func.attr)  # type: ignore[attr-defined]
        node = call.args[position] if position is not None and len(call.args) > position else None
        for kw in call.keywords:
            if kw.arg == "flags":
                node = kw.value
        if node is None:
            return ""
        return (ast.get_source_segment(source, node) or "").strip()

    # [VRN-ID] VRN-MAN001-FNC028 · LOGIC
    def literal_strings(value: ast.AST) -> Iterable[ast.Constant]:
        """Only plain literal tables (dict values / list / tuple / set items); f-strings and calls are not regex tables."""
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            yield value
        elif isinstance(value, ast.Dict):
            for item in value.values:
                yield from literal_strings(item)
        elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for item in value.elts:
                yield from literal_strings(item)

    # [VRN-ID] VRN-MAN001-FNC029 · LOGIC
    def add_table(qualname: str, name: str, value: ast.AST, line: int) -> None:
        if any(isinstance(sub, (ast.Call, ast.JoinedStr)) for sub in ast.walk(value)):
            return
        for sub in literal_strings(value):
            if not sub.value:
                continue
            try:
                re.compile(sub.value)
            except re.error:
                continue
            literal.append({"qualname": qualname or name, "call": "table:" + name, "flags": "",
                            "pattern": sub.value, "line": getattr(sub, "lineno", line)})

    # [VRN-ID] VRN-MAN001-CLS001 · CLASS
    class Visitor(ast.NodeVisitor):
        # [VRN-ID] VRN-MAN001-FNC030 · INIT
        def __init__(self) -> None:
            self.stack: List[str] = []

        # [VRN-ID] VRN-MAN001-FNC031 · LOGIC
        def _scoped(self, node: ast.AST, name: str) -> None:
            self.stack.append(name)
            self.generic_visit(node)
            self.stack.pop()

        # [VRN-ID] VRN-MAN001-FNC032 · LOGIC
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._scoped(node, node.name)

        # [VRN-ID] VRN-MAN001-FNC033 · LOGIC
        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._scoped(node, node.name)

        # [VRN-ID] VRN-MAN001-FNC034 · LOGIC
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self._scoped(node, node.name)

        # [VRN-ID] VRN-MAN001-FNC035 · LOGIC
        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                if (isinstance(target, ast.Name) and REGEX_TABLE_NAME.search(target.id) and not isinstance(node.value, ast.Call)
                        and target.id not in SCANNER_CONFIG_TABLES):
                    add_table(".".join(self.stack), target.id, node.value, node.lineno)
            self.generic_visit(node)

        # [VRN-ID] VRN-MAN001-FNC036 · LOGIC
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "re"
                    and func.attr in RE_CALLS and node.args):
                first = node.args[0]
                qual = ".".join(self.stack) or "<module>"
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    literal.append({"qualname": qual, "call": func.attr, "flags": flags_of(node),
                                    "pattern": first.value, "line": node.lineno})
                else:
                    dynamic.append({"qualname": qual, "call": func.attr, "line": node.lineno,
                                    "expr": (ast.get_source_segment(source, first) or "")[:160]})
            self.generic_visit(node)

    Visitor().visit(tree)
    return literal, dynamic


# [VRN-ID] VRN-MAN001-FNC037 · BUILD
def def_build_regex_book() -> Dict[str, Any]:
    """One entry per distinct regex (the SSOT unit) with every place that uses it."""
    entries: Dict[str, Dict[str, Any]] = {}
    dynamic_all: List[Dict[str, Any]] = []
    sources = []
    site_total = 0
    present = [rel for rel in REGEX_SOURCES if (VRN_ROOT / rel).is_file()]
    scanned = dict(zip(present, def_parallel_map(def_regex_sites, present, action="REGEX 冊：逐檔 AST 掃描")))
    for rel in present:
        path = VRN_ROOT / rel
        literal, dynamic = scanned[rel]
        for item in literal:
            site_total += 1
            entry = entries.get(item["pattern"])
            if entry is None:
                try:
                    re.compile(item["pattern"])
                    compiles = True
                except re.error:
                    compiles = False
                family = def_family(item["qualname"], item["pattern"])
                entry = {"id": "RX-" + hashlib.sha1(item["pattern"].encode("utf-8")).hexdigest()[:10],
                         "family": family, "pattern": item["pattern"],
                         "compiles": compiles, "sites": [], "category": def_category(family, item["pattern"], item["qualname"])}
                entries[item["pattern"]] = entry
            entry["sites"].append({"file": rel, "qualname": item["qualname"], "call": item["call"],
                                   "flags": item["flags"], "line": item["line"]})
        for item in dynamic:
            dynamic_all.append(dict(file=rel, **item))
        sources.append({"path": rel, "sha256": def_sha256_file(path), "sites": len(literal), "dynamic": len(dynamic)})
    patterns = sorted(entries.values(), key=lambda e: e["id"])
    # harvested books: one entry per distinct pattern; a pattern the code already has is linked, never written twice
    book_entries: Dict[str, Dict[str, Any]] = {}
    for bp in def_book_patterns():
        source = {"book": bp["book"], "name": bp["name"], "category": bp["category"]}
        if bp["text"] in entries:
            entries[bp["text"]].setdefault("book_sources", []).append(source)
            continue
        entry = book_entries.get(bp["text"])
        if entry is None:
            try:
                re.compile(bp["text"])
                ok = True
            except re.error:
                ok = False
            entry = {"id": "BX-" + hashlib.sha1(bp["text"].encode("utf-8")).hexdigest()[:10], "category": bp["category"],
                     "compiles": ok, "sources": []}
            entry["pattern" if ok else "source_text"] = bp["text"]
            book_entries[bp["text"]] = entry
        entry["sources"].append(source)
    book_patterns = sorted(book_entries.values(), key=lambda e: e["id"])
    categories: Dict[str, Dict[str, int]] = {}
    for e in patterns:
        categories.setdefault(e["category"], {"code": 0, "books": 0})["code"] += 1
    for e in book_patterns:
        categories.setdefault(e["category"], {"code": 0, "books": 0})["books"] += 1
    shared = [e["id"] for e in patterns if len(e["sites"]) > 1]
    families: Dict[str, int] = {}
    for e in patterns:
        families[e["family"]] = families.get(e["family"], 0) + 1
    ticker_master: Dict[str, str] = {}
    try:
        with def_quiet():
            tm = def_load_module("VRN_Main_ticker_master", ENGINE_FILES["ticker_master"])
        ticker_master = {k: v for k, v in sorted(getattr(tm, "REGEX_REGISTRY", {}).items()) if isinstance(v, str)}
        ticker_master.update({f"SHAPE.{k}": v for k, v in sorted(getattr(tm, "SHAPE_REGEX", {}).items()) if isinstance(v, str)})
    except Exception as error:  # noqa: BLE001
        ticker_master = {"_error": f"{error.__class__.__name__}: {error}"[:200]}
    return {
        "schema": "VRN_REGEX_SSOT_v0100",
        "owner": "VRN 獨立子系統（VRN_Main_v0100.py build 生成；VCGC 只檢衝突、不改）",
        "policy": "程式裡的 regex 是執行本體；本冊是它們唯一的登記處：一條 regex 一筆，sites 列出每個使用點。"
                  "改了任何一條就重跑 build，check 逐條列出新增／消失／使用點改動（行號變動不算）。"
                  "shared = 同一條 regex 用在多處，是合併候選，不自動合併。"
                  "category 是 2026-10-10 的細分類（EMAIL／TEL_TW／TEL_HK、代號三種…）。book_patterns = 收來的冊上的 regex，"
                  "一條一筆；和程式一模一樣的不重寫，掛在程式那一筆的 book_sources。冊上的 regex 只登記，引擎不因此改判讀。",
        "sources": sources,
        "counts": {"patterns": len(patterns), "sites": site_total, "shared": len(shared), "dynamic_sites": len(dynamic_all),
                   "not_compiling": sum(1 for e in patterns if not e["compiles"]),
                   "families": dict(sorted(families.items())), "ticker_master": len(ticker_master),
                   "book_patterns": len(book_patterns), "book_same_as_code": sum(len(e.get("book_sources", [])) for e in patterns),
                   "book_not_compiling": sum(1 for e in book_patterns if not e["compiles"]),
                   "categories": dict(sorted(categories.items()))},
        "patterns": patterns,
        "book_patterns": book_patterns,
        "shared": shared,
        "ticker_master_registry": ticker_master,
        "dynamic_sites": dynamic_all,
    }


# [VRN-ID] VRN-MAN001-FNC038 · VALIDATE
def def_compare_regex(book: Dict[str, Any], live: Dict[str, Any]) -> List[str]:
    # [VRN-ID] VRN-MAN001-FNC039 · LOGIC
    def sites(e: Dict[str, Any]) -> List[Tuple[str, str, str, str]]:
        return sorted((s["file"], s["qualname"], s["call"], s["flags"]) for s in e.get("sites", []))
    have = {e["id"]: e for e in book.get("patterns", [])}
    now = {e["id"]: e for e in live.get("patterns", [])}
    diffs = []
    for rid in sorted(set(now) - set(have)):
        first = now[rid]["sites"][0]
        diffs.append(f"新增 {rid} {first['file']}:{first['line']} {now[rid]['pattern'][:60]}")
    for rid in sorted(set(have) - set(now)):
        diffs.append(f"消失 {rid} {have[rid]['pattern'][:60]}")
    for rid in sorted(set(have) & set(now)):
        if sites(have[rid]) != sites(now[rid]):
            diffs.append(f"使用點改動 {rid} {now[rid]['pattern'][:40]}")
    if book.get("ticker_master_registry") != live.get("ticker_master_registry"):
        diffs.append("代碼主檔 REGEX_REGISTRY 與冊不同")
    return diffs


# =============================================================================
# 04. 同義字冊（執行期實際生效的表）
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC040 · LOGIC
def def_norm_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


# [VRN-ID] VRN-MAN001-FNC041 · IO
def def_load_engines() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    with def_quiet():
        try:
            fp_mod = def_load_module("VRN_Main_first_page", ENGINE_FILES["first_page"])
            out["fp_mod"] = fp_mod
            out["fpe"] = fp_mod.FirstPageEngine()
        except Exception as error:  # noqa: BLE001
            out["fp_error"] = f"{error.__class__.__name__}: {error}"[:300]
        try:
            out["db"] = def_load_module("VRN_Main_database", ENGINE_FILES["database"])
        except Exception as error:  # noqa: BLE001
            out["db_error"] = f"{error.__class__.__name__}: {error}"[:300]
        try:
            out["ec"] = sys.modules.get("VRN_Evidence_Core") or def_load_module("VRN_Evidence_Core", ENGINE_FILES["evidence_core"])
        except Exception as error:  # noqa: BLE001
            out["ec_error"] = f"{error.__class__.__name__}: {error}"[:300]
    return out


# [VRN-ID] VRN-MAN001-FNC042 · BUILD
def def_build_synonym_book() -> Dict[str, Any]:
    eng = def_load_engines()
    # 評等只讀原文、不分類（操作員 2026-10-10）：rating 只登記「哪些字會被認成評等」，不記等級。
    scopes: Dict[str, Any] = {"broker": {}, "rating": {}, "rating_codes": {},
                              "rating_actions": {}, "target_price_terms": {}, "report_type": {}, "metric": {}}
    knowledge_paths: Dict[str, Any] = {}
    fp_alias: Dict[str, str] = {}
    db_alias: Dict[str, str] = {}
    rating_words: Dict[str, set] = {}
    fpe = eng.get("fpe")
    if fpe is not None:
        brd = fpe.brd
        scopes["broker"]["first_page"] = {k: sorted(v) for k, v in sorted(brd.b.items())}
        rating_words["first_page"] = {w.lower() for words in brd.r.values() for w in words} | {w.lower() for w in brd.fine}
        scopes["rating_codes"]["first_page"] = sorted(getattr(brd, "SHORT", {}))
        scopes["target_price_terms"]["first_page"] = sorted(brd.target_terms)
        scopes["broker"]["first_page_display"] = def_jsonable(brd.display)
        knowledge_paths = {k: (def_rel(Path(v)) if v else None) for k, v in sorted((fpe.knowledge_paths or {}).items())}
        for canon, aliases in brd.b.items():
            for a in aliases:
                fp_alias[a.lower()] = canon
        fp_mod = eng["fp_mod"]
        scopes["rating_actions"]["first_page"] = def_jsonable(getattr(fp_mod, "RATING_ACTIONS", {}))
    db = eng.get("db")
    if db is not None:
        with def_quiet():
            broker = db.load_broker_alias_ssot(None)
            rating = db.load_rating_alias_ssot(None)
        scopes["broker"]["database"] = {k: sorted(set(v)) for k, v in sorted(broker.items())}
        scopes["broker"]["database_display"] = def_jsonable(getattr(db, "BROKER_DISPLAY", {}))
        rating_words["database"] = {str(w).lower() for words in rating.values() for w in words}
        scopes["rating_codes"]["database"] = sorted(getattr(db, "RATING_SHORT_CODES", {}))
        scopes["rating_actions"]["database"] = def_jsonable(getattr(db, "RATING_ACTION_WORDS", ()))
        scopes["target_price_terms"]["database"] = sorted(getattr(db, "TARGET_PRICE_TERMS", []))
        scopes["report_type"]["database"] = def_jsonable(getattr(db, "REPORT_TYPE_ALIASES", {}))
        scopes["metric"]["database"] = def_jsonable(getattr(db, "METRIC_ALIASES", {}))
        for canon, aliases in broker.items():
            for a in aliases:
                db_alias[str(a).lower()] = canon
    ec = eng.get("ec")
    if ec is not None:
        scopes["broker"]["evidence_core_extra"] = def_jsonable(getattr(ec, "EXTRA_BROKER_ALIASES", {}))
        # 不套中央 批679 拒絕清單（操作員 2026-10-10「GF 照原文顯示」）：這幾家照原文認，名單由 VRN 自己持有
        scopes["broker"]["evidence_core_mainland"] = def_jsonable(getattr(ec, "MAINLAND_BROKER_ALIASES", {}))
        scopes["broker"]["evidence_core_mainland_domains"] = def_jsonable(getattr(ec, "MAINLAND_DOMAINS", {}))
        scopes["broker"]["evidence_core_generic"] = def_jsonable(getattr(ec, "GENERIC_BROKER_ALIASES", set()))
        scopes["broker"]["evidence_core_domains"] = def_jsonable(getattr(ec, "DOMAIN_BROKER", {}))
        scopes["broker"]["evidence_core_label_bridge"] = def_jsonable(getattr(ec, "DOMAIN_LABEL_BRIDGE", {}))
        rating_words["evidence_core"] = {str(k).lower() for k in getattr(ec, "RATING_WORDS", {})}
        scopes["rating_codes"]["evidence_core"] = sorted(getattr(ec, "RATING_SHORT", {}))
        scopes["rating_actions"]["evidence_core"] = def_jsonable(getattr(ec, "RATING_ACTION_WORDS", {}))
    for engine_name, words in sorted(rating_words.items()):
        scopes["rating"][engine_name] = sorted(words)
    # 衝突：同一個別名在兩支引擎被解到不同券商 / 同一個字被判成不同評等。只顯示，不改。
    bridge_fp = getattr(eng.get("fp_mod"), "BROKER_CANONICAL_BRIDGE", {}) if eng.get("fp_mod") else {}
    bridge_db = getattr(db, "BROKER_KEY_BRIDGE", {}) if db is not None else {}

    # [VRN-ID] VRN-MAN001-FNC043 · LOGIC
    def canon_fp(c: str) -> str:
        return def_norm_key(bridge_fp.get(c.upper(), c))

    # [VRN-ID] VRN-MAN001-FNC044 · LOGIC
    def canon_db(c: str) -> str:
        return def_norm_key(bridge_db.get(c, bridge_db.get(c.upper(), c)))

    broker_conflicts = []
    for alias in sorted(set(fp_alias) & set(db_alias)):
        a, b = canon_fp(fp_alias[alias]), canon_db(db_alias[alias])
        if a != b:
            broker_conflicts.append({"alias": alias, "first_page": fp_alias[alias], "database": db_alias[alias]})
    all_rating_words = set().union(*rating_words.values()) if rating_words else set()
    rating_not_shared = {name: sorted(all_rating_words - words) for name, words in sorted(rating_words.items())}
    library_multi = []
    lib_path = VRN_ROOT / "knowledge" / "SYNONYM_LIBRARY_v4.json"
    library_scopes: Dict[str, int] = {}
    if lib_path.is_file():
        lib = def_read_json(lib_path)
        for scope, table in sorted((lib.get("scopes") or {}).items()):
            entries = table if isinstance(table, dict) else {}
            library_scopes[scope] = len(entries)
            for term, spec in sorted(entries.items()):
                canon = spec if isinstance(spec, list) else (spec.get("canonical") if isinstance(spec, dict) else None)
                if isinstance(canon, list) and len({str(c) for c in canon}) > 1:
                    library_multi.append({"scope": scope, "term": term, "canonicals": [str(c) for c in canon]})
    external = sorted(k for k, v in knowledge_paths.items() if v and (v.startswith("/") or ":" in v[:3]))
    book_terms, book_vs_runtime = def_book_terms(fp_alias)
    scopes["book_terms"] = book_terms
    return {
        "schema": "VRN_SYNONYM_SSOT_v0100",
        "owner": "VRN 獨立子系統（VRN_Main_v0100.py build 生成；VCGC 只檢衝突、不改）",
        "policy": "表格取自引擎載入完知識書之後的執行期狀態（內建 → SYNONYM_LIBRARY_v4 → ssot/ 字典，一個別名一個主人）。"
                  "評等只讀原文、不分類：rating／rating_codes 只登記哪些字會被認成評等（偵測詞），輸出是報告上印的原文，"
                  "沒有等級對照。conflicts 只顯示、不自動改；改同義字 = 改 ssot/ 或 knowledge/ 的書，再重跑 build。",
        "knowledge_paths_first_page": knowledge_paths,
        "knowledge_outside_vrn": external,
        "load_errors": {k: v for k, v in eng.items() if k.endswith("_error")},
        "counts": {
            "broker_first_page": len(scopes["broker"].get("first_page", {})),
            "broker_database": len(scopes["broker"].get("database", {})),
            "broker_aliases_first_page": len(fp_alias), "broker_aliases_database": len(db_alias),
            "rating_words_first_page": len(rating_words.get("first_page", ())),
            "rating_words_database": len(rating_words.get("database", ())),
            "rating_words_evidence_core": len(rating_words.get("evidence_core", ())),
            "synonym_library_v4_scopes": library_scopes,
            "conflicts_broker_cross_engine": len(broker_conflicts),
            "synonym_library_multi_canonical": len(library_multi),
            "book_terms": {cat: sum(len(v) for v in (spec.get("terms") or {}).values()) for cat, spec in sorted(book_terms.items())},
            "book_broker_split_in_runtime": len(book_vs_runtime["split"]),
            "book_broker_key_names": len(book_vs_runtime["key_names"]),
            "book_broker_aliases_not_in_runtime": sum(len(v) for v in book_vs_runtime["book_only"].values()),
        },
        "scopes": scopes,
        "conflicts": {"broker_cross_engine": broker_conflicts, "synonym_library_multi_canonical": library_multi,
                      "book_broker_vs_runtime": book_vs_runtime},
        "rating_words_not_shared": rating_not_shared,
    }


# [VRN-ID] VRN-MAN001-FNC045 · LOGIC
def def_book_terms(fp_alias: Dict[str, str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Synonyms the harvested books carry, by category (DATE · BROKER · EMAIL · RATING · three ticker forms · TARGET_PRICE ·
    NAME · ADJ_CLOSE · ANALYST · FINANCIAL).  Registered only: the engines' runtime tables are not changed by them.
    Rating words are detection words; the book's own grouping is shown as the book has it, VRN does not classify."""
    s05 = def_read_json(SSOT_DIR / "VRN_S05_FieldRegistry_v0103.json")
    fields = {f.get("name"): f for f in s05.get("basicinfo_fields") or [] if isinstance(f, dict)}

    # [VRN-ID] VRN-MAN001-FNC046 · LOGIC
    def syn(name: str) -> List[str]:
        return list(((fields.get(name) or {}).get("validation_layers") or {}).get("synonyms") or [])

    src = "VRN_S05_FieldRegistry_v0103.json"
    terms: Dict[str, Any] = {
        "DATE": {"source": src, "terms": {"report_date": syn("report_date"), "adj_close_date": syn("adj_close_date")}},
        "TICKER_TW": {"source": src, "terms": {"ticker": syn("ticker")}},
        "TICKER_YF": {"source": src, "terms": {"yfinance_ticker": syn("yfinance_ticker")}},
        "TICKER_BBG": {"source": src, "terms": {"bloomberg_ticker": syn("bloomberg_ticker")}},
        "NAME": {"source": src, "terms": {"name": syn("name"), "name_en": syn("name_en")}},
        "ADJ_CLOSE": {"source": src, "terms": {"adj_close": syn("adj_close")}},
        "TARGET_PRICE": {"source": src, "terms": {"target_price": list((s05.get("target_price_dict") or {}).get("synonyms") or []),
                                                  "previous_target_stopwords": list((s05.get("target_price_dict") or {}).get("stopwords_previous") or [])}},
        "RATING": {"source": src + " · VRN_FieldRules_SSOT_v0101.json", "note": "偵測詞；分組照冊上原樣，VRN 不拿來分類",
                   "terms": {"detection_words": list(((s05.get("rating_list") or {}).get("flat_list_for_matching")) or []),
                             **{f"book_group.{k}": [w for lang in ("chinese", "english") for w in (v or {}).get(lang, [])]
                                for k, v in ((s05.get("rating_list") or {}).get("canonical_v22_2") or {}).items()}}},
        "ANALYST": {"source": src + " · VIA_VRN_ReportFieldRules_SSOT_v0101.json", "terms": {"analyst": syn("analyst")}},
    }
    rfr = def_read_json(SSOT_DIR / "VIA_VRN_ReportFieldRules_SSOT_v0101.json")
    titles = rfr.get("analyst_titles") or {}
    terms["ANALYST"]["terms"].update({"title_zh": list(titles.get("zh") or []), "title_en": list(titles.get("en") or [])})
    domains = {d: str((v or {}).get("broker") or "") for d, v in (s05.get("email_domain_to_broker") or {}).items()}
    for d, b in ((rfr.get("broker_domains_addendum") or {}).get("map") or {}).items():
        domains.setdefault(d, str(b))
    by_broker: Dict[str, List[str]] = {}
    for d, b in sorted(domains.items()):
        by_broker.setdefault(b, []).append(d)
    terms["EMAIL"] = {"source": src + " · VIA_VRN_ReportFieldRules_SSOT_v0101.json", "note": "電郵網域 → 冊上的券商名稱",
                      "terms": by_broker}
    bd = def_read_json(SSOT_DIR / "VRN_Broker_Dict_v0103.json")
    broker_terms: Dict[str, List[str]] = {}
    for key, entry in sorted((bd.get("brokers") or {}).items()):
        names = [entry.get("abbr"), entry.get("chinese_name"), entry.get("english_name")] + list(entry.get("aliases") or [])
        broker_terms[str(key)] = sorted({str(n) for n in names if n})
    terms["BROKER"] = {"source": "VRN_Broker_Dict_v0103.json", "terms": broker_terms}
    lex = def_read_json(SSOT_DIR / "VRN_FinLexicon_SSOT_v0109.json")
    terms["FINANCIAL"] = {"source": "VRN_FinLexicon_SSOT_v0109.json",
                          "terms": {str(r.get("std")): list(r.get("zh") or []) + list(r.get("en") or [])
                                    for r in lex.get("rows") or [] if isinstance(r, dict) and r.get("std")}}
    # 2026-10-11: 評價法、公司名稱常用簡稱、文件類別詞、財報科目（版面還原用的運算元）
    vm = def_read_json(SSOT_DIR / "03_ssot" / "VRN_ValuationMethod_SSOT_v0100.json")
    terms["VALUATION_METHOD"] = {
        "source": "VRN_ValuationMethod_SSOT_v0100.json（ENG395 讀）", "note": "16 種評價法，詞依地區 en / zh_tw / zh_hk / zh_cn",
        "terms": {str(m["id"]): sorted({w for region in ("en", "en_case_sensitive", "zh_tw", "zh_hk", "zh_cn") for w in m.get(region) or []})
                  for m in vm.get("methods") or [] if isinstance(m, dict) and m.get("id")}}
    company = def_read_json(SSOT_DIR / "03_ssot" / "VRN_ReportEntities_SSOT_v0100.json").get("company") or {}
    parser = def_read_json(SSOT_DIR / "03_ssot" / "VRN_Report_Parser_Integrated_SSOT.json")
    alias_terms: Dict[str, List[str]] = {str(s.get("canonical")): list(s.get("aliases") or []) for s in parser.get("via_raw_synonyms") or []
                                         if isinstance(s, dict) and re.match(r"^\d{4,6}\.TW", str(s.get("canonical") or ""))}
    alias_terms.update({f"rule.{k}": list(v) for k, v in company.items() if k.endswith("_suffix_en") or k.endswith("_suffix_zh")
                        if isinstance(v, list)})
    terms["COMPANY_ALIAS"] = {
        "source": "VRN_Report_Parser_Integrated_SSOT.json via_raw_synonyms · VRN_ReportEntities_SSOT_v0100.json company（ENG396 讀）",
        "note": "代號 → 常用名稱；rule.* = 由全名推出簡稱時去掉的字尾（台灣積體電路製造 → 台積電 的推法照 ENG396 name_forms）",
        "terms": alias_terms}
    doc_class = def_read_json(SSOT_DIR / "03_ssot" / "VRN_DocClass_SSOT_v0100.json")
    terms["DOC_CLASS"] = {"source": "VRN_DocClass_SSOT_v0100.json（ENG393 讀）", "note": "只擷取個股報告：其他類別的字詞照列",
                          "terms": {str(k): list(v) for k, v in (doc_class.get("lexicon") or {}).items() if isinstance(v, list)}}
    annual = def_read_json(SSOT_DIR / "VRN_AnnualExtract_SSOT_v0100.json")
    identity = def_read_json(SSOT_DIR / "VRN_FinIdentity_SSOT_v0100.json")
    operands = {str(i["key"]): list(i.get("zh") or []) + list(i.get("en") or []) for i in annual.get("items") or [] if isinstance(i, dict) and i.get("key")}
    operands.update({str(k): list(v.get("labels_zh") or []) + list(v.get("labels_en") or [])
                     for k, v in (identity.get("extra_operands") or {}).items() if isinstance(v, dict)})
    upload = def_read_json(SSOT_DIR / "VRN_OperatorLabels_SSOT_v0100.json") if (SSOT_DIR / "VRN_OperatorLabels_SSOT_v0100.json").is_file() else {}
    for k, v in (upload.get("operand_labels") or {}).items():
        operands.setdefault(str(k), [])
        operands[str(k)] += [x for x in v if x not in operands[str(k)]]
    terms["FIN_OPERAND"] = {"source": "VRN_AnnualExtract_SSOT_v0100.json items · VRN_FinIdentity_SSOT_v0100.json extra_operands · "
                                      "VRN_OperatorLabels_SSOT_v0100.json operand_labels",
                            "note": "表上的列標 → 驗算式的運算元（加減除驗算 39 條用）", "terms": operands}
    terms["FIN_CROSSWALK"] = {"source": "VRN_OperatorLabels_SSOT_v0100.json field_crosswalk（操作員上傳）",
                              "note": "VRN 運算元 → TWSE／twstock／yfinance 欄名（登記；VDF 接官方值時用）",
                              "terms": {k: [f"{s}:{v[s]}" for s in ("twse_tpex", "twstock", "yfinance") if v.get(s)]
                                        for k, v in (upload.get("field_crosswalk") or {}).items()}}
    known = {n.lower() for names in broker_terms.values() for n in names}
    terms["BROKER_UPLOAD"] = {"source": "VRN_OperatorLabels_SSOT_v0100.json broker_candidates（操作員上傳）",
                              "note": "上傳檔的券商叫法裡，VRN 券商字典沒有的；只顯示，併不併入由操作員裁定",
                              "terms": {str(b.get("code")): [n for n in b.get("names") or [] if n.lower() not in known]
                                        for b in upload.get("broker_candidates") or [] if any(n.lower() not in known for n in b.get("names") or [])}}
    # the book's brokers against the first-page engine's runtime owners: shown, never merged
    split, key_names, book_only = [], {}, {}
    for key, names in broker_terms.items():
        owners = sorted({fp_alias[n.lower()] for n in names if n.lower() in fp_alias})
        if len(owners) > 1:
            split.append({"book": key, "runtime_owners": owners,
                          "by_name": {n: fp_alias[n.lower()] for n in names if n.lower() in fp_alias}})
        elif owners and owners[0].upper() != key.upper():
            key_names[key] = owners[0]
        missing = [n for n in names if n.lower() not in fp_alias]
        if missing:
            book_only[key] = missing
    return terms, {"split": split, "key_names": key_names, "book_only": book_only,
                   "note": "split = 冊上同一家，引擎裡分到兩家以上；key_names = 同一家、代碼名不同；book_only = 冊上有、引擎沒有的名字"
                           "（併不併入引擎由操作員裁定，本冊不改引擎）"}


# =============================================================================
# 05. INDEX 冊與註冊冊
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC047 · BUILD
def def_build_index_book() -> Dict[str, Any]:
    books = []
    present = [VRN_ROOT / spec["path"] for spec in SSOT_BOOKS if (VRN_ROOT / spec["path"]).is_file()]
    hashed = dict(zip(present, def_parallel_map(lambda p: (def_sha256_file(p), def_text_len(p)), present,
                                                action="INDEX 冊：逐本 SHA-256")))
    for spec in SSOT_BOOKS:
        path = VRN_ROOT / spec["path"]
        row = {"path": spec["path"], "role": spec["role"], "consumers": spec["consumers"],
               "version": (re.search(r"_v(\d{2,4}|\d)(?=\.|_)", path.name) or [None, ""])[1],
               "present": path.is_file()}
        if path.is_file():
            row.update(sha256=hashed[path][0], bytes=hashed[path][1])
        for flag in ("frozen", "generated"):
            if spec.get(flag):
                row[flag] = True
        if spec.get("copied_from"):
            row["copied_from"] = spec["copied_from"]
            row["source_sha256_at_copy"] = row.get("sha256", "")
        if spec.get("mother"):
            row["mother_source"] = "tonykuni/movies-dataset:VeritasIntelligenceAnalytics/" + spec["mother"]
            row["source_sha256_at_copy"] = row.get("sha256", "")
        books.append(row)
    prov = def_read_json(SSOT_DIR / "VRN_03SSOT_PROVENANCE_v0100.json") if (SSOT_DIR / "VRN_03SSOT_PROVENANCE_v0100.json").is_file() else {}
    for item in prov.get("books") or []:                 # 2026-10-11: the operator's via_02_vrn\03_ssot, mother copies
        path = VRN_ROOT / item["file"]
        row = {"path": item["file"], "role": "母倉 functional modules/VRN/SSOT 副本（操作員本機 via_02_vrn\\03_ssot 的同一份）",
               "consumers": ["p13", "bookcheck"], "version": (re.search(r"_v(\d{2,4}|\d)(?=\.|_)", path.name) or [None, ""])[1],
               "present": path.is_file(), "mother_source": "tonykuni/movies-dataset:" + item["mother_path"] + "@" + item["mother_commit"]}
        if path.is_file():
            row.update(sha256=def_sha256_file(path), bytes=def_text_len(path), source_sha256_at_copy=item["sha256_lf"])
        books.append(row)
    return {
        "schema": "VRN_SSOT_INDEX_v0100",
        "owner": "VRN 獨立子系統（VRN_Main_v0100.py build 生成）",
        "policy": "VRN 只從自己資料夾裡讀知識。copied_from 只是出處：倉庫原書之後若變動，check 顯示 CONFLICT（黃），"
                  "VRN 副本仍為準，要不要跟進由操作員裁定。frozen = 凍結稽核包，只讀不改。",
        "books": books,
        "interactions": [dict(i) for i in INTERACTIONS],
    }


# [VRN-ID] VRN-MAN001-FNC048 · LOGIC
def def_kind(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1]
    if rel == "VRN_Main_v0100.py":
        return "MAIN"
    if rel.startswith("references/intake/"):
        return "REFERENCE_FROZEN"
    if rel.startswith("tests/"):
        return "TEST"
    if rel.startswith("engine/"):
        return "ENGINE"
    if rel.startswith("ssot/"):
        return "SSOT"
    if rel.startswith("knowledge/"):
        return "KNOWLEDGE"
    if rel.startswith("registry/"):
        return "REGISTRY_BOOK"
    if name.endswith(".ps1"):
        return "LAUNCHER"
    if name.endswith(".md"):
        return "DOC"
    return "OTHER"


# [VRN-ID] VRN-MAN001-FNC049 · LOGIC
def def_version_of(path: Path) -> str:
    m = re.search(r"_v(\d{2,4})(?=[._])", path.name)
    if m:
        return "v" + m.group(1)
    if path.suffix == ".py":
        head = path.read_text(encoding="utf-8-sig", errors="replace")[:20000]
        for pattern in (r'^ENGINE_VERSION\s*=\s*"([^"]+)"', r'^LOOP_VERSION\s*=\s*"([^"]+)"',
                        r'^PROBE_VERSION\s*=\s*"([^"]+)"', r'^MODULE_VERSION\s*=\s*"([^"]+)"'):
            m = re.search(pattern, head, re.M)
            if m:
                return m.group(1)
    return ""


# [VRN-ID] VRN-MAN001-FNC050 · LOGIC
def def_bridge_of(path: Path, kind: str) -> str:
    if kind == "REFERENCE_FROZEN":
        return "exempt (frozen)"
    if path.suffix == ".py":
        return "ACCEL-BRIDGE" if ACCEL_MARKER in path.read_text(encoding="utf-8-sig", errors="replace")[:6000] else "MISSING"
    if path.suffix == ".ps1":
        return "PS-ACCEL20" if PS_ACCEL_MARKER in path.read_text(encoding="utf-8-sig", errors="replace") else "MISSING"
    return "n/a"


# [VRN-ID] VRN-MAN001-FNC051 · LOGIC
def def_walk_vrn(root: Path = VRN_ROOT) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith((".pyc", ".pyo")):
                continue
            files.append(Path(dirpath) / name)
    return files


# [VRN-ID] VRN-MAN001-FNC052 · BUILD
def def_build_registry() -> Dict[str, Any]:
    paths = [p for p in def_walk_vrn() if p.resolve() != REGISTRY_PATH.resolve()]
    shas = def_parallel_map(def_sha256_file, paths, action="註冊冊：逐檔 SHA-256（build）")
    entries = []
    ids = (def_read_json(SSOT_DIR / "VRN_ID_SSOT_v0100.json").get("modules") or {}) if (SSOT_DIR / "VRN_ID_SSOT_v0100.json").is_file() else {}
    prov = SSOT_DIR / "VRN_ENGINES_PROVENANCE_v0100.json"
    vendored = {e["file"]: e for e in (def_read_json(prov).get("engines") or [] if prov.is_file() else []) if e.get("file")}
    for path, sha in zip(paths, shas):
        rel = def_rel(path)
        kind = def_kind(rel)
        entry = {"path": rel, "kind": kind, "version": def_version_of(path), "sha256": sha,
                 "bytes": def_text_len(path),
                 "bridge": def_bridge_of(path, kind)}
        if rel in ids:                                    # 2026-10-10：編號、分類、模組版本（AST 注入冊）
            entry.update(id=ids[rel].get("id"), category=ids[rel].get("category"), module_version=ids[rel].get("version"))
        elif rel in vendored:                             # 2026-10-11：母倉引擎（逐位元組，不注入註解）
            entry.update(id=vendored[rel].get("id"), category="VENDORED", module_version=vendored[rel].get("version"),
                         vendored_from=f"{vendored[rel].get('mother_path')}@{vendored[rel].get('mother_commit')}")
        entries.append(entry)
    kinds: Dict[str, int] = {}
    for e in entries:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return {
        "schema": "VRN_REGISTRY_v0100",
        "system": "VRN-1（研究報告）獨立系統",
        "system_note": "2026-10-15 正名 VRN-1：這是一個有自己 MAIN 的獨立系統，不是誰的子系統。"
                       "操作員單一入口是 artifacts/VRN-1.ps1（診斷 + 管線都走它）；"
                       "本檔 VRN_Main_v0100.py 仍是系統的 MAIN，VRN-1.ps1 呼叫它，不取代它。",
        "report_types": "個股報告或資訊（一個個股）· 產業資訊及展望（多個個股）· 其他投資報告；"
                        "各走各的處理路徑，見 ssot/VRN_TitleTrim_SSOT_v0100.json#focus.doc_class_policy",
        "main": "VRN_Main_v0100.py",
        "launcher": LAUNCHER_NAME,
        "policy": "VRN 資料夾內每一個檔案都要在這裡；SHA-256 以 LF 行尾計算（Windows CRLF 取出不影響）。"
                  "未登記、缺檔、內容不符 = FAIL；改了東西就跑 VRN_Main_v0100.py build。",
        "counts": {"files": len(entries), "kinds": dict(sorted(kinds.items()))},
        "files": entries,
    }


# [VRN-ID] VRN-MAN001-FNC053 · GATE
def def_check_registry() -> List[Dict[str, Any]]:
    if not REGISTRY_PATH.is_file():
        return [def_row("P03 REGISTRY", REGISTRY_PATH.name, "FAIL", "註冊冊不存在：先跑 build")]
    book = def_read_json(REGISTRY_PATH)
    have = {e["path"]: e for e in book.get("files", [])}
    live = {def_rel(p): p for p in def_walk_vrn() if p.resolve() != REGISTRY_PATH.resolve()}
    missing = sorted(set(have) - set(live))
    unregistered = sorted(set(live) - set(have))
    both = sorted(set(have) & set(live))
    live_sha = dict(zip(both, def_parallel_map(lambda rel: def_sha256_file(live[rel]), both, action="註冊冊：逐檔 SHA-256（check）")))
    changed = [rel for rel in both if live_sha[rel] != have[rel]["sha256"]]
    bridgeless = sorted(e["path"] for e in have.values() if e.get("bridge") == "MISSING")
    rows = [
        def_row("P03 REGISTRY", f"{len(have)} 個登記檔都在", "FAIL" if missing else "PASS", "; ".join(missing[:8])),
        def_row("P03 REGISTRY", "沒有未登記的檔", "FAIL" if unregistered else "PASS", "; ".join(unregistered[:8])),
        def_row("P03 REGISTRY", "內容與登記 SHA-256 相符", "FAIL" if changed else "PASS", "; ".join(changed[:8])),
        def_row("P03 REGISTRY", "每支 .py / .ps1 都帶加速器橋", "FAIL" if bridgeless else "PASS", "; ".join(bridgeless[:8])),
    ]
    return rows


# [VRN-ID] VRN-MAN001-FNC054 · GATE
def def_check_ssot() -> List[Dict[str, Any]]:
    rows = []
    for path, builder, compare in ((REGEX_BOOK, def_build_regex_book, def_compare_regex),
                                   (SYNONYM_BOOK, def_build_synonym_book, None),
                                   (INDEX_BOOK, def_build_index_book, None)):
        if not path.is_file():
            rows.append(def_row("P02 SSOT", path.name, "FAIL", "冊不存在：先跑 build"))
            continue
        book = def_read_json(path)
        live = def_jsonable(builder())
        if compare is not None:
            diffs = compare(book, live)
        else:
            diffs = [] if json.dumps(def_jsonable(book), ensure_ascii=False, sort_keys=True) == \
                json.dumps(live, ensure_ascii=False, sort_keys=True) else ["內容與目前程式／知識書不同（重跑 build）"]
        rows.append(def_row("P02 SSOT", path.name, "FAIL" if diffs else "PASS", "; ".join(diffs[:6]), diffs=diffs))
        if path == REGEX_BOOK:
            bad = live["counts"]["not_compiling"]
            rows.append(def_row("P02 SSOT", f"REGEX {live['counts']['patterns']} 條（{live['counts']['sites']} 個使用點）全部可編譯",
                                "FAIL" if bad else "PASS", f"{bad} 條編譯失敗" if bad else
                                f"共用 {live['counts']['shared']} 條（合併候選）· 動態組字 {live['counts']['dynamic_sites']} 處"))
        if path == SYNONYM_BOOK:
            c = live["counts"]
            outside = live["knowledge_outside_vrn"]
            rows.append(def_row("P02 SSOT", "引擎只讀 VRN 自己的知識書", "FAIL" if outside else "PASS",
                                ("讀到 VRN 外面：" + ", ".join(outside)) if outside else
                                " · ".join(f"{k}={v}" for k, v in live["knowledge_paths_first_page"].items() if v)))
            n = c["conflicts_broker_cross_engine"]
            rows.append(def_row("P02 SSOT", "跨引擎同義字衝突（只顯示）", "WARN" if n else "PASS",
                                f"券商 {n} · 評等只讀原文不分類（無等級衝突）· 同義字庫多主 {c['synonym_library_multi_canonical']}"))
        if path == INDEX_BOOK:
            for b in book.get("books", []):
                src = b.get("copied_from")
                repo_src = VRN_ROOT.parent.parent / src if src and VRN_ROOT.parent.name == "functional modules" else None
                if repo_src is not None and repo_src.is_file() and def_sha256_file(repo_src) != b.get("source_sha256_at_copy"):
                    rows.append(def_row("P02 SSOT", f"出處 {src} 已變動", "WARN",
                                        f"CONFLICT（只顯示）：VRN 副本 {b['path']} 仍為準，跟不跟進由操作員裁定"))
    rows += def_gate_gitattributes()
    return rows


# [VRN-ID] VRN-MAN001-FNC141 · GATE
def def_gate_gitattributes() -> List[Dict[str, Any]]:
    """`.gitattributes` 要跟「哪些檔是機器重生的」那份宣告逐字相同。

    有這道閘才算把旗標接起來：以後有人加一本 build 會重寫的冊、卻忘了標 `generated`，
    或標了卻沒重跑 build，這裡就紅 —— 而不是等到下一次跨分支合併，
    由 git 把 `<<<<<<<` 寫進那本冊裡才發現。

    每一條規矩都附帶宣告在哪：不是「照清單抄」，是「照宣告生成」。
    """
    want = def_build_gitattributes()
    if not GITATTRIBUTES_PATH.is_file():
        return [def_row("P02 SSOT", ".gitattributes（合併規矩）", "FAIL",
                        f"不存在：機器重生的 {len(def_generated_paths())} 個檔沒有任何合併規矩，"
                        "跨分支合併會把衝突標記寫進 JSON 冊裡（跑 build 生成）")]
    got = GITATTRIBUTES_PATH.read_text(encoding="utf-8")
    if got != want:
        miss = [p for p in def_generated_paths() if f"\n{p} " not in got.replace("\t", " ")
                and not any(line.split(" ")[0] == p for line in got.splitlines())]
        why = (f"少了 {len(miss)} 個重生檔：" + "、".join(miss[:4])) if miss else "內容與宣告不同（排版或註解）"
        return [def_row("P02 SSOT", ".gitattributes（合併規矩）", "FAIL",
                        f"{why} —— 跑 build 重寫；別手改這個檔")]
    return [def_row("P02 SSOT", ".gitattributes（合併規矩）", "PASS",
                    f"{len(def_generated_paths())} 個每輪重生的檔 -merge（合併不逐行併、不把衝突標記寫進 JSON 冊）· "
                    + "、".join(MERGE_UNION_FILES) + " merge=union（兩邊的輪次都留）")]


# [VRN-ID] VRN-MAN001-FNC055 · ENTRY
def def_cmd_inject() -> Dict[str, Any]:
    """AST 注入（操作員「注入AST 分類說明編號 · 所有引擎編號版本註冊 · 目前邏輯不可動」）：只加註解；
    寫回前 AST 必須相同，原檔先備份到 TEMP（VRN_TEMP_POLICY）。"""
    astid = def_load_module("VRN_Main_astid", ENGINE_FILES["astid"])
    temp = def_load_module("VRN_Main_tempstore", ENGINE_FILES["tempstore"])
    opened = temp.current_run() is None
    if opened:
        temp.open_run("VRN_Main")
    try:
        return astid.run(write=True, mapper=lambda fn, xs: def_parallel_map(fn, xs, action="AST 注入：逐檔規劃"),
                         backup=lambda rel, text: temp.put_json("inject_backup", rel, {"path": rel, "text": text}))
    finally:
        if opened:
            temp.close_run()


# [VRN-ID] VRN-MAN001-FNC073 · GATE
def def_gate_localdb() -> List[Dict[str, Any]]:
    """P12: the operator's local VDF database (read-only) -- where it is and what it holds, before the loop runs."""
    try:
        mod = def_load_module("VRN_Main_localdb", ENGINE_FILES["localdb"])
        ldb = mod.LocalDB()
        info = ldb.describe()
        ldb.close()
    except Exception as error:  # noqa: BLE001
        return [def_row("P12 LOCALDB", "VRN_LocalDB", "WARN", f"{error.__class__.__name__}: {error}"[:200])]
    if info["status"] != "OK":
        return [def_row("P12 LOCALDB", f"本機 VDF 資料庫：{info['status']}", "WARN",
                        "公司名稱 / ADJ CLOSE 不補，判讀照常 · " + str(info.get("why", ""))[:300])]
    cols = info.get("columns") or {}
    mapped = " · ".join(f"{t}（{'／'.join(f'{k}={v}' for k, v in c.items() if v)}）" if isinstance(c, dict) else f"{t}：{c}"
                        for t, c in cols.items())
    return [def_row("P12 LOCALDB", f"本機 VDF 資料庫（唯讀，{info.get('source') or 'duckdb'}）{Path(info['path']).name} · 最新價格 "
                    f"{info.get('latest_price_date') or '?'}", "PASS",
                    f"{info['path']} · " + " · ".join(f"{t} {n} 列" for t, n in (info.get("rows") or {}).items())
                    + (f" · 欄位 {mapped}" if mapped else "") + " · 公司名稱與現價取這裡（G17）")]


# [VRN-ID] VRN-MAN001-FNC074 · LOGIC
def def_local_ssot_dir() -> Optional[Path]:
    """The operator's via_02_vrn\\03_ssot (read-only); VRN_LOCAL_SSOT overrides, an empty value turns it off."""
    env = os.environ.get("VRN_LOCAL_SSOT")
    if env is not None:
        return Path(env) if env and Path(env).is_dir() else None
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    path = home / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "via_02_vrn" / "03_ssot"
    return path if path.is_dir() else None


# [VRN-ID] VRN-MAN001-FNC075 · LOGIC
def def_book_family(name: str) -> Tuple[str, int]:
    m = re.search(r"^(.*)_v(\d+)\.(json|csv|jsonl)$", name.replace(".integration.json", ".json"))
    return (m.group(1), int(m.group(2))) if m else (name, -1)


# [VRN-ID] VRN-MAN001-FNC076 · VALIDATE
def def_compare_local_ssot(local: Path) -> Dict[str, Any]:
    """Every file of the local folder against VRN's copies: SAME / DIFFERENT / NEWER (a later version of a book VRN holds) /
    LOCAL_ONLY; and VRN_ONLY for copies the folder no longer has.  Hashes with LF line endings; nothing is written there."""
    mine_root = SSOT_DIR / "03_ssot"
    local_files = {p.relative_to(local).as_posix(): p for p in sorted(local.rglob("*")) if p.is_file()}
    mine_files = {p.relative_to(mine_root).as_posix(): p for p in sorted(mine_root.rglob("*")) if p.is_file()} if mine_root.is_dir() else {}
    vrn_versions: Dict[str, int] = {}
    for p in SSOT_DIR.rglob("*"):
        if p.is_file() and ".integration." not in p.name:
            fam, ver = def_book_family(p.name)
            vrn_versions[fam] = max(vrn_versions.get(fam, -1), ver)
    rows = []
    for rel, p in local_files.items():
        if rel in mine_files:
            state = "SAME" if def_sha256_file(p) == def_sha256_file(mine_files[rel]) else "DIFFERENT"
        else:
            fam, ver = def_book_family(p.name)
            state = "NEWER" if fam in vrn_versions and ver > vrn_versions[fam] >= 0 else "LOCAL_ONLY"
        rows.append({"file": rel, "state": state})
    rows += [{"file": rel, "state": "VRN_ONLY"} for rel in mine_files if rel not in local_files]
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    return {"local": str(local), "counts": counts, "rows": rows}


# [VRN-ID] VRN-MAN001-FNC077 · GATE
def def_gate_local_ssot(out: Optional[Path] = None) -> List[Dict[str, Any]]:
    """P13 (operator 2026-10-11): the operator's local via_02_vrn\\03_ssot, read-only, against VRN's ssot/03_ssot copies."""
    local = def_local_ssot_dir()
    if local is None:
        return [def_row("P13 LOCAL-SSOT", "本機 via_02_vrn\\03_ssot", "SKIP",
                        "這台電腦沒有這個資料夾（或 VRN_LOCAL_SSOT 指的地方不在）；VRN 用自己的 ssot/03_ssot 副本")]
    cmp_ = def_compare_local_ssot(local)
    if out is not None:
        def_write_json(out / "VRN_LocalSSOT_Compare_v0100.json", cmp_)
    c = cmp_["counts"]
    todo = [r["file"] for r in cmp_["rows"] if r["state"] in ("NEWER", "LOCAL_ONLY", "DIFFERENT")]
    order = {"NEWER": 0, "DIFFERENT": 1, "LOCAL_ONLY": 2}
    todo.sort(key=lambda f: order[next(r["state"] for r in cmp_["rows"] if r["file"] == f)])
    return [def_row("P13 LOCAL-SSOT", f"本機 03_ssot：{sum(c.values()) - c.get('VRN_ONLY', 0)} 檔（唯讀）", "PASS", str(local)),
            def_row("P13 LOCAL-SSOT", "相同 {SAME} · 內容不同 {DIFFERENT} · 本機較新 {NEWER} · 只在本機 {LOCAL_ONLY} · 只在 VRN {VRN_ONLY}".format(
                        **{k: c.get(k, 0) for k in ("SAME", "DIFFERENT", "NEWER", "LOCAL_ONLY", "VRN_ONLY")}),
                    "WARN" if todo else "PASS",
                    ("帶進 VRN 要操作員推到母倉或交給我：" + "、".join(todo[:12])) if todo else "VRN 的副本和本機一致")]


# [VRN-ID] VRN-MAN001-FNC081 · GATE
def def_gate_regions(fixtures: bool = False) -> List[Dict[str, Any]]:
    """P14 (operator 2026-10-11): the stock-report lane -- mother engines ENG392-396 and their books load from VRN; with
    `fixtures`, four reports with known answers are taken apart, restored, checked and written to a database."""
    try:
        reg = def_load_module("VRN_Main_regions", ENGINE_FILES["regions"])
        mom = reg.mother()
    except Exception as error:  # noqa: BLE001
        return [def_row("P14 REGIONS", "VRN_PageRegions", "FAIL", f"{error.__class__.__name__}: {error}"[:300])]
    d = mom.describe()
    n_ident = len((mom.books.get("identity") or {}).get("identities") or [])
    rows = [def_row("P14 REGIONS", f"母倉引擎 {len(d['engines'])}/{len(reg.MOTHER_FILES)} · 冊 {len(d['books'])}/{len(reg.BOOK_FILES)} · 驗算式 {n_ident}",
                    "FAIL" if mom.errors else "PASS",
                    "; ".join(f"{k}: {v}" for k, v in mom.errors.items())[:300]
                    or "ENG393 個股分類 · ENG392 XY 切 · ENG394 版面還原 · ENG395 評價法 · ENG396 目標價與公司名"),
            def_row("P14 REGIONS", f"列標 → 運算元 {len(mom.ledger.key_of)} 個", "PASS",
                    f"冊與冊同一列標指到不同運算元 {len(mom.ledger.conflicts)} 處（留第一個，只顯示）"
                    + ("：" + "、".join(c["label"] for c in mom.ledger.conflicts[:6]) if mom.ledger.conflicts else ""))]
    if not fixtures or mom.errors:
        return rows
    if importlib.util.find_spec("fitz") is None:
        return rows + [def_row("P14 REGIONS", "已知答案的報告", "SKIP", "PyMuPDF 沒有安裝：pip install pymupdf（安裝是操作員的手）")]
    with tempfile.TemporaryDirectory(prefix="vrn_p14_") as tmp:
        truths = reg.build_fixtures(Path(tmp) / "fixtures")
        results, lane = reg.analyze_many([(Path(tmp) / "fixtures" / t["file"], t["file"]) for t in truths], temp_dir=Path(tmp) / "work",
                                         mapper=lambda fn, items, action: def_parallel_map(fn, items, action=action),
                                         action="P14 版面還原：子行程逐塊")
        checks = [c for r, t in zip(results, truths) for c in reg.check_fixture(r, t)]
        counts = reg.write_db(results, Path(tmp) / reg.DB_NAME)
        frames = None
        if importlib.util.find_spec("pandas") is not None:
            dfm = def_load_module("VRN_Main_dataframe", ENGINE_FILES["dataframe"])
            book = dfm.load_book()
            book["tables"] = {k: v for k, v in book["tables"].items() if k.startswith("vrn_regions_")}
            frames = dfm.check(tmp, book=book, mapper=lambda fn, items, action: def_parallel_map(fn, items, action=action))
    if lane.get("lane") == "sequential":
        ACCEL_COVERAGE.append({"action": "P14 版面還原：逐檔", "lane": "sequential", "items": lane.get("items", 0),
                               "seconds": lane.get("seconds", 0.0), "why": "檔數太少，不開子行程", "by_design": True})
    bad = [(item, detail) for item, ok, detail in checks if not ok]
    if frames is not None:
        lamps = [r["lamp"] for r in frames["tables"]]
        rows.append(def_row("P14 REGIONS", f"資料庫 {len(lamps)} 張表載成 DataFrame：" + " · ".join(f"{k} {lamps.count(k)}" for k in sorted(set(lamps))),
                            {"GREEN": "PASS", "RED": "FAIL"}.get(frames["verdict"], "WARN"),
                            "; ".join(f"{r['table']}: {'; '.join(r.get('problems') or [])}" for r in frames["tables"] if r["lamp"] != "GREEN")[:400]
                            or "表頭（欄名 · 型別 · 必填 · 主鍵 · 列數）全部照 VRN_Output_Header_SSOT"))
    return rows + [def_row("P14 REGIONS", f"已知答案 {len(truths)} 份：{len(checks) - len(bad)}/{len(checks)}",
                           "FAIL" if bad else "PASS",
                           "; ".join(f"{i} · {d}" for i, d in bad[:6])
                           or "檔名拆解、只取個股、首頁右側資訊區、表格左右對切與上下切、圖在上表在下、數字還原、加減除驗算、"
                              "目標價前→今、評價法倍數×EPS=目標價 · 資料庫 " + " · ".join(f"{k} {v}" for k, v in counts.items()))]


# [VRN-ID] VRN-MAN001-FNC084 · GATE
def def_gate_titletrim() -> List[Dict[str, Any]]:
    """P15 (operator 2026-10-11): title decomposition and TRIM against their known answers (8 titles + 3 messy reports)."""
    if importlib.util.find_spec("fitz") is None:
        return [def_row("P15 TITLETRIM", "已知答案", "SKIP", "PyMuPDF 沒有安裝：pip install pymupdf（安裝是操作員的手）")]
    try:
        tt = def_load_module("VRN_Main_titletrim", ENGINE_FILES["titletrim"])
        with def_quiet():
            _rc, rows = tt.selftest(verbose=False)
    except Exception as error:  # noqa: BLE001
        return [def_row("P15 TITLETRIM", "VRN_TitleTrim", "FAIL", f"{error.__class__.__name__}: {error}"[:300])]
    bad = [r for r in rows if not r[1]]
    return [def_row("P15 TITLETRIM", f"標題分拆與 TRIM 已知答案 {len(rows) - len(bad)}/{len(rows)}", "FAIL" if bad else "PASS",
                    "; ".join(f"{i} · {d}" for i, _ok, d in bad[:6])
                    or "Method def02 八步 TRIM、七段標題、首頁基本資料、年度財報頁 TRIM 救回、兩條讀法一致才 VERIFIED")]


# [VRN-ID] VRN-MAN001-FNC089 · GATE
def def_gate_focus() -> List[Dict[str, Any]]:
    """P17 (operator 2026-10-11「只擷取個股報告中的FILENAME / 1ST PAGE / 年度財報頁進行處理」): a five-page stock report keeps page 1
    and its annual financial page, an industry report is not processed, the focus copy is the same bytes every time."""
    if importlib.util.find_spec("fitz") is None:
        return [def_row("P17 FOCUS", "已知答案", "SKIP", "PyMuPDF 沒有安裝：pip install pymupdf（安裝是操作員的手）")]
    try:
        fc = def_load_module("VRN_Main_focus", ENGINE_FILES["focus"])
        with def_quiet():
            _rc, rows = fc.selftest(verbose=False)
    except Exception as error:  # noqa: BLE001
        return [def_row("P17 FOCUS", "VRN_Focus", "FAIL", f"{error.__class__.__name__}: {error}"[:300])]
    bad = [r for r in rows if not r[1]]
    return [def_row("P17 FOCUS", f"只取個股報告的檔名、第一頁、年度財報頁：已知答案 {len(rows) - len(bad)}/{len(rows)}", "FAIL" if bad else "PASS",
                    "; ".join(f"{i} · {d}" for i, _ok, d in bad[:6])
                    or "五頁個股報告只留第 1、3 頁（本文、季表、免責略過）· 產業報告不處理 · 副本頁文字與原檔一字不差 · 同頁同位元組 · 原檔不動")]


# [VRN-ID] VRN-MAN001-FNC085 · GATE
def def_gate_engine_lock() -> List[Dict[str, Any]]:
    """P16: the engine lock book -- every locked engine / book still has the fingerprint its known answers were proven on."""
    try:
        lk = def_load_module("VRN_Main_lock", ENGINE_FILES["lock"])
        got = lk.check_engine_lock()
    except Exception as error:  # noqa: BLE001
        return [def_row("P16 LOCK", "VRN_Lock", "FAIL", f"{error.__class__.__name__}: {error}"[:300])]
    st = {k: [r for r in got if r["state"] == k] for k in ("HELD", "CHANGED", "MISSING", "UNLOCKED", "NEW", "NO_BOOK")}
    rows = [def_row("P16 LOCK", f"引擎鎖：守住 {len(st['HELD'])} · 改了 {len(st['CHANGED'])} · 不見 {len(st['MISSING'])}",
                    "FAIL" if st["CHANGED"] or st["MISSING"] or st["NO_BOOK"] else "PASS",
                    "; ".join(f"{r['file']}: {r['detail']}" for r in st["CHANGED"] + st["MISSING"] + st["NO_BOOK"])[:500]
                    or "AST 指紋（只加註解不變）與 ssot/VRN_EngineLock_SSOT_v0100.json 相同")]
    if st["UNLOCKED"] or st["NEW"]:
        rows.append(def_row("P16 LOCK", f"未鎖 {len(st['UNLOCKED']) + len(st['NEW'])} 支（沒有已知答案證明，或證明沒過）", "WARN",
                            "; ".join(f"{Path(r['file']).name}: {r['detail']}" for r in st["UNLOCKED"] + st["NEW"])[:500]))
    return rows


# [VRN-ID] VRN-MAN001-FNC086 · LOGIC
def def_run_proofs() -> Dict[str, Tuple[bool, str]]:
    """Every known-answer proof the engine lock is built on (ssot/VRN_TitleTrim_SSOT_v0100.json lock.proofs)."""
    lk = def_load_module("VRN_Main_lock", ENGINE_FILES["lock"])
    out: Dict[str, Tuple[bool, str]] = {}

    # [VRN-ID] VRN-MAN001-FNC087 · LOGIC
    def all_pass(rows: List[Dict[str, Any]]) -> Tuple[bool, str]:
        bad = [r for r in rows if r["status"] != "PASS"]
        return (bool(rows) and not bad), ("; ".join(f"{r['item']} {r['status']}" for r in bad[:3]) or f"{len(rows)} 項全過")
    oracle = def_gate_oracle()
    out["first_page_oracle"] = all_pass([r for r in oracle if r["item"].startswith("first_page")])
    out["database_oracle"] = all_pass([r for r in oracle if r["item"].startswith("database")])
    books_ok, books_d = all_pass(def_gate_books())
    bc_ok, bc_d = lk.run_module_selftest("engine/VRN_BookCheck_v0100.py")
    out["books"] = (books_ok and bc_ok, f"P08 {books_d} · BookCheck {bc_d}")
    out["regions"] = all_pass(def_gate_regions(fixtures=True))
    for name, rel in (("dataframe", "engine/VRN_DataFrame_v0100.py"), ("titletrim", "engine/VRN_TitleTrim_v0100.py"),
                      ("lock", "engine/VRN_Lock_v0100.py"), ("localdb", "engine/VRN_LocalDB_v0100.py"),
                      ("focus", "engine/VRN_Focus_v0100.py"), ("matrix", "engine/VRN_Matrix_v0100.py"), ("record", "engine/VRN_TickerRecord_v0100.py"),
                      ("truthmatrix", "engine/VRN_TruthMatrix_v0100.py"), ("runcache", "engine/VRN_RunCache_v0100.py"),
                      ("tempstore", "engine/VRN_TempStore_v0100.py"),
                      # 2026-10-18：全景探針是倉裡唯一登記了卻鎖不住的引擎 —— 它沒有 selftest(),
                      # 所以每一次 check 都掛著「未鎖 1 支」。補了已知答案之後它才證得起來。
                      ("panorama", "engine/VRN_PanoramaProbe.py"),
                      # 2026-10-19（操作員開閘「接 OCR」）：影像檔的讀法。它的已知答案包含
                      # 「中文會掉字」這件事 —— 寫成已知答案，免得哪天有人以為 OCR 的中文可信。
                      ("ocr", "engine/VRN_Ocr_v0100.py"),
                      # 2026-10-20（操作員「VRN-1 自動修正直到100%正確」）：輸出驗證與自動修正。已知答案是一份畫出來的 PDF：
                      # 對 · 錯期間 · 截斷 · 分組表取到舊值 · 並排表取到右表 · 科目歸錯 · 原文沒有 · 期間不明，各一筆。
                      ("outputverify", "engine/VRN_OutputVerify_v0100.py"),
                      # 2026-10-20（操作員「工具可相互取用 · 還原後表格可改為資料庫形式 PIVOT」）：PIVOT 資料庫與工具橋。
                      ("pivotdb", "engine/VRN_PivotDB_v0100.py"), ("toolbridge", "engine/VRN_ToolBridge_v0100.py")):
        out[name] = lk.run_module_selftest(rel)
    return out


# [VRN-ID] VRN-MAN001-FNC095 · IO
def def_load_truth_file(path: str) -> str:
    """`--truth` is the G11 truth JSON; a file that is not JSON is taken as the mother's matrix pasted into a text file and
    converted first (VRN_TruthMatrix: <file>.truth.json beside it, never inside the VRN tree).  Unreadable -> the path as given."""
    try:
        json.loads(Path(path).read_text(encoding="utf-8-sig"))
        return path
    except Exception:  # noqa: BLE001
        pass
    try:
        tm = def_load_module("VRN_Main_truthmatrix", ENGINE_FILES["truthmatrix"])
        got = tm.convert_matrix_file(path, source=Path(path).name)
    except Exception as error:  # noqa: BLE001
        print(f"[TRUTH-MATRIX] {path} 不是真值 JSON，也轉不成：{error}")
        return path
    if not got.get("out"):
        print(f"[TRUTH-MATRIX] {path} 不是真值 JSON，裡面也沒有矩陣列")
        return path
    s = got["summary"]
    print(f"[TRUTH-MATRIX] {path} 是貼上的矩陣：轉成 {s['rows']} 筆真值（個股 {s['stock']}）→ {got['out']}，G11 用它")
    return got["out"]


# [VRN-ID] VRN-MAN001-FNC088 · ENTRY
def def_cmd_lock(args: argparse.Namespace) -> int:
    """`lock`: prove every engine on its known answers and lock the ones that pass; --status / --unlock for the output ledger."""
    lk = def_load_module("VRN_Main_lock", ENGINE_FILES["lock"])
    if args.unlock:
        home, _why = lk.ledger_home(args.lock_home)
        removed = lk.Ledger(home).unlock(args.unlock, args.part)
        print(f"[LOCK] 解鎖 {len(removed)} 個部位 · {home}" + ("：" + ", ".join(removed[:20]) if removed else "（沒有符合的）"))
        return 0 if removed else 1
    if args.status:
        home, why = lk.ledger_home(args.lock_home)
        print(json.dumps(dict(lk.Ledger(home).status(), home_from=why), ensure_ascii=False, indent=1))
        for r in lk.check_engine_lock():
            print(f"  [{r['state']:8}] {r['file']} · {r['detail']}")
        return 0
    def_progress(1, 3, "已知答案逐組證明（檔名 oracle · 收來的冊 · 版面還原 · DataFrame · 標題與 TRIM · 鎖 · 本機資料庫 · TEMP）")
    with def_quiet():
        proofs = def_run_proofs()
    for name, (ok, detail) in proofs.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} · {detail}")
    def_progress(2, 3, "證明全過的引擎與冊記下指紋 → ssot/VRN_EngineLock_SSOT_v0100.json")
    book = lk.write_engine_lock(proofs)
    def_progress(3, 3, "INDEX 冊與註冊冊（新指紋冊要登記）")
    def_write_json(INDEX_BOOK, def_build_index_book())
    def_write_json(REGISTRY_PATH, def_build_registry())
    print(f"[LOCK] 鎖住 {len(book['files'])} 支引擎與冊 · 未鎖 {len(book['unlocked'])}："
          + "; ".join(f"{Path(k).name}（{v}）" for k, v in book["unlocked"].items())[:600])
    return 0 if all(ok for ok, _d in proofs.values()) else 1


# [VRN-ID] VRN-MAN001-FNC056 · GATE
def def_gate_astid() -> List[Dict[str, Any]]:
    """P11: every VRN module, class and function carries its number; the ID book matches the code."""
    try:
        astid = def_load_module("VRN_Main_astid", ENGINE_FILES["astid"])
        problems = astid.check()
        counts = astid.load_book().get("counts", {})
    except Exception as error:  # noqa: BLE001
        return [def_row("P11 ASTID", "VRN_AstId", "FAIL", f"{error.__class__.__name__}: {error}"[:200])]
    return [def_row("P11 ASTID", f"AST 編號：模組 {counts.get('modules', 0)} · 函式 {counts.get('functions', 0)} · "
                    f"類別 {counts.get('classes', 0)} · 已退役 {counts.get('retired', 0)}（號碼不回收）",
                    "FAIL" if problems else "PASS", "; ".join(problems[:6]) if problems else "只加註解，AST 與原檔相同")]


# [VRN-ID] VRN-MAN001-FNC142 · LOGIC
def def_generated_paths() -> List[str]:
    """每一輪 `build`／`lock` 會**整個重寫**的檔，相對 VRN 根，排序去重。

    一個來源，不是兩份清單：SSOT_BOOKS 上的 `generated` 旗標，加上本身不在冊上的
    GENERATED_OFF_BOOK（為什麼不在冊上，那邊逐條寫了）。

    2026-10-20 之前這個旗標只標到 4 本（REGEX、同義字、引擎鎖、AST 編號），漏了合併冊、
    INDEX 冊、借出工具冊、註冊冊；而且**沒有任何人讀它** —— 宣告了沒人接。
    """
    out = [str(spec["path"]) for spec in SSOT_BOOKS if spec.get("generated")]
    out += [str(spec["path"]) for spec in GENERATED_OFF_BOOK]
    return sorted(set(out))


# [VRN-ID] VRN-MAN001-FNC145 · LOGIC
def def_generated_paths_from(root: Path) -> List[str]:
    """同一份宣告，換算成**相對 `root`** 的路徑 —— git 回報衝突時用的就是這一種。

    2026-10-20 自己踩的：`merge` 第一版拿 `def_rel(VRN_ROOT)` 當前綴，而那支的基準就是
    VRN_ROOT，算出來是 `"."`。對不上 git 的 `functional modules/VRN/...`，結果每一個
    重生檔都被判成「要人判」—— 方向是安全的（停下來），可是指令整個沒用。
    """
    rel = VRN_ROOT.resolve().relative_to(root.resolve()).as_posix().strip("/")
    return [(f"{rel}/{path}" if rel and rel != "." else path) for path in def_generated_paths()]


# [VRN-ID] VRN-MAN001-FNC143 · BUILD
def def_build_gitattributes() -> str:
    """`.gitattributes` 的內容。清單從 `def_generated_paths()` 來，這裡只排版。

    操作員 2026-10-20「解決 GITHUB 衝突問題」。根因量過：兩條分支只要都跑過鏈，
    `git merge` 必定在這幾個檔上撞車 —— 而且 git 會把 `<<<<<<<` 寫進 JSON 冊裡，
    冊當場不再是合法 JSON。手工接回來也只是猜，因為下一次 build 本來就會整個蓋掉。

      `-merge`      不要逐行併。兩邊都改過時，工作區留本地那一份（仍是合法 JSON），
                    路徑照樣標成衝突 —— 沒有任何東西被安靜地選掉。跑 build／lock
                    重生之後才算解掉。只有一邊改過時 git 照常直接取那一邊。
      `merge=union` 只往後加的日誌：兩邊的輪次都留，一行都不刪。

    沒宣告的檔（原始碼、測試、手寫的冊）一個字都不碰：照常出現衝突標記，由人決定。
    """
    lines = [
        "# 這個檔由 VRN_Main_v0100.py build 生成 —— 不要手改（改了 P02 SSOT 閘會紅）。",
        "# 清單的正本是 VRN_Main_v0100.py 的 SSOT_BOOKS `generated` 旗標 + GENERATED_OFF_BOOK。",
        "#",
        "# 為什麼需要它：下面這些檔每一輪 build／lock 都整個重寫。git 不知道這件事，",
        "# 跨分支合併時會把 <<<<<<< 衝突標記寫進 JSON 冊裡，冊當場不再是合法 JSON；",
        "# 而人就算手工接回來也只是猜，因為下一次 build 本來就會把它整個蓋掉。",
        "#",
        "# -merge       = 兩邊都改過時不逐行併：工作區留本地那一份（仍是合法 JSON），",
        "#                路徑照樣算衝突，跑 `VRN_Main_v0100.py merge` 重生之後才算解掉。",
        "# merge=union  = 只往後加的日誌，兩邊的輪次都留。",
        "#",
        "# 沒列在這裡的檔（原始碼、測試、手寫的冊）照 git 原本的規矩走 —— 衝突由人決定。",
        "",
        "# 每一輪 build／lock 重寫的檔",
    ]
    width = max([len(x) for x in def_generated_paths()] + [len(x) for x in MERGE_UNION_FILES])
    lines += [f"{path:<{width}} -merge" for path in def_generated_paths()]
    lines += ["", "# 只往後加、從不改舊行的日誌"]
    lines += [f"{name:<{width}} merge=union" for name in MERGE_UNION_FILES]
    return "\n".join(lines) + "\n"


# [VRN-ID] VRN-MAN001-FNC057 · ENTRY
def def_cmd_build() -> int:
    def_progress(1, 7, "AST 注入（編號、分類、說明；只加註解）")
    inject = def_cmd_inject()
    if inject["refused"]:
        print("[BUILD] AST 注入拒寫：" + "; ".join(inject["refused"]))
        return 1
    def_progress(2, 7, "REGEX 冊")
    regex = def_build_regex_book()
    def_write_json(REGEX_BOOK, regex)
    def_progress(3, 7, "同義字冊")
    def_write_json(SYNONYM_BOOK, def_jsonable(def_build_synonym_book()))
    def_progress(4, 7, "合併冊（四碼代號 15 欄：券商別名／網域／評等詞／標籤／regex，從倉內每本來源冊合併；REGEX 與同義字冊是它的來源，所以在它們之後）")
    try:
        rec = def_load_module("VRN_Main_record", ENGINE_FILES["record"])
        _path, rec_book = rec.write_book()
        rc_counts = rec_book["merge"]["counts"]
        print(f"  合併冊：券商別名 {rc_counts['broker_aliases']}（折 {rc_counts['broker_folded']}）· 網域 {rc_counts['email_domains']} · 評等詞 {rc_counts['rating_words']} · "
              f"regex {rc_counts['regex']} · 衝突 {rc_counts['conflicts']}（照列）")
    except Exception as error:  # noqa: BLE001
        print(f"  合併冊沒重建：{error.__class__.__name__}: {error}")
    def_progress(5, 7, "INDEX 冊")
    def_write_json(INDEX_BOOK, def_build_index_book())
    def_progress(6, 7, "註冊冊 · 借出工具冊")
    reg = def_build_registry()
    def_write_json(REGISTRY_PATH, reg)
    try:                                                   # 2026-10-20：借出工具冊（別的系統借 VRN-1 的工具前核對 sha256）—— AST 注入之後才寫，sha256 才是最後的檔
        tb = def_load_module("VRN_Main_toolbridge", ENGINE_FILES["toolbridge"])
        print(f"  借出工具冊：{def_rel(tb.write_manifest())} · " + "、".join(o["id"] for o in tb.manifest()["offers"]))
    except Exception as error:  # noqa: BLE001
        print(f"  借出工具冊沒寫：{error.__class__.__name__}: {error}")
    def_progress(7, 7, "合併規矩（.gitattributes：機器重生的檔不要逐行併）")
    attrs = def_build_gitattributes()
    if not GITATTRIBUTES_PATH.is_file() or GITATTRIBUTES_PATH.read_text(encoding="utf-8") != attrs:
        GITATTRIBUTES_PATH.write_text(attrs, encoding="utf-8", newline="\n")
        print(f"  合併規矩：{GITATTRIBUTES_PATH.name} 重寫（{len(def_generated_paths())} 個重生檔 -merge · "
              f"{len(MERGE_UNION_FILES)} 個日誌 merge=union）")
    else:
        print(f"  合併規矩：{GITATTRIBUTES_PATH.name} 已是最新（{len(def_generated_paths())} 個重生檔 -merge）")
    print(f"[BUILD] AST 注入 {inject['changed']}/{inject['files']} 檔 · regex {regex['counts']['patterns']} 條／{regex['counts']['sites']} 使用點"
          f"（冊上 {regex['counts']['book_patterns']} 條）· 註冊 {reg['counts']['files']} 檔 · {def_rel(SSOT_DIR)}/ · {REGISTRY_PATH.name}")
    return 0


# =============================================================================
# 06. 檔名 oracle 與單獨複製（獨立性）
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC058 · IO
def def_load_oracle() -> Dict[str, Dict[str, Any]]:
    """FILENAME_RESULTS.json is a list of rows keyed by `filename` (same reader as VRN_AutoTestLoop)."""
    if not ORACLE_PATH.is_file():
        return {}
    try:
        rows = def_read_json(ORACLE_PATH)
    except ValueError:
        return {}
    return {r["filename"]: r for r in rows if isinstance(r, dict) and r.get("filename")}


# [VRN-ID] VRN-MAN001-FNC059 · LOGIC
def def_filename_answers(eng: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    eng = eng or def_load_engines()
    names = list(def_load_oracle())
    out: Dict[str, Any] = {"names": len(names), "first_page": {}, "database": {}}
    fpe, db = eng.get("fpe"), eng.get("db")
    with def_quiet():
        if fpe is not None:
            for name in names:
                f = fpe._filename_fields(name)
                out["first_page"][name] = [f.get("ticker") or "", f.get("date") or "", f.get("broker") or ""]
        if db is not None:
            alias = db.load_broker_alias_ssot(None)
            for name in names:
                ti = db.tokenize_filename(name)
                cands = [c["ticker"] for c in db.extract_filename_ticker_candidates(ti, {}) if c["ticker"]]
                dates = db.parse_date_candidates_from_number_tokens(ti["number_tokens"])
                frags = db.company_fragments_after_ticker(ti["tokens"])
                broker, _, _ = db.match_broker_from_tokens_and_text(ti["chinese_tokens"], ti["english_tokens"], "", alias, frags)
                out["database"][name] = [(cands or [""])[0], dates[0]["date"] if dates else "", broker or ""]
    return out


# [VRN-ID] VRN-MAN001-FNC060 · GATE
def def_gate_oracle(eng: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    oracle = def_load_oracle()
    if not oracle:
        return [def_row("P06 ORACLE", "FILENAME_RESULTS.json", "SKIP", "稽核包不在")]
    answers = def_filename_answers(eng)
    rows = []
    for engine in ("first_page", "database"):
        got = answers[engine]
        if not got:
            rows.append(def_row("P06 ORACLE", engine, "FAIL", "引擎沒有載入"))
            continue
        bad = []
        for name, row in oracle.items():
            exp = [(row.get("ticker_candidates") or [""])[0], row.get("report_date") or "", (row.get("broker") or {}).get("value") or ""]
            if got.get(name) != exp:
                bad.append(f"{name}: got={got.get(name)} exp={exp}")
        rows.append(def_row("P06 ORACLE", f"{engine} 檔名 {len(oracle)} 筆對 oracle", "FAIL" if bad else "PASS", "; ".join(bad[:4])))
    return rows


# [VRN-ID] VRN-MAN001-FNC061 · GATE
def def_gate_books() -> List[Dict[str, Any]]:
    """P08: the books harvested from the other sessions load from ssot/ and agree with their own examples."""
    try:
        bc = def_load_module("VRN_Main_bookcheck", ENGINE_FILES["bookcheck"])
    except Exception as error:  # noqa: BLE001
        return [def_row("P08 BOOKS", "VRN_BookCheck", "FAIL", f"{error.__class__.__name__}: {error}"[:200])]
    loaded = bc.load_books()
    elsewhere = [f"{Path(loaded['paths'][k]).name}（{s}）" for k, s in (loaded.get("sources") or {}).items() if s != "VRN ssot"]
    rows = [def_row("P08 BOOKS", f"收來的冊 {len(loaded['books'])}/{len(bc.BOOK_FILES)} 本（每一家取最新版）", "FAIL" if loaded["missing"] else "PASS",
                    ", ".join(loaded["missing"]) or (("較新的版本取自：" + "、".join(elsewhere)) if elsewhere else ""))]
    for r in bc.book_selftest(loaded):
        rows.append(def_row("P08 BOOKS", f"{r['book']} · {r['name']}", "PASS" if r["ok"] else "WARN",
                            ("冊自己對不上自己的例子（冊的缺陷，只顯示）：" + r["detail"]) if not r["ok"] else ""))
    return rows


# 引擎內部的逐檔判讀：判讀邏輯凍結（操作員「目前邏輯不可動」）——逐檔順序、共用快取都不拆；
# 加速器在 P04 以 activate() 掛在整個行程上，引擎在這個行程裡跑。
ACCEL_BY_DESIGN = (
    ("G06 資料庫引擎整批判讀", "引擎自己的逐檔順序與 upsert，不拆執行緒（判讀邏輯不可動）"),
    ("G07 首頁引擎逐檔判讀", "首頁引擎實例與快取共用，不拆執行緒（判讀邏輯不可動）"),
    ("G08 冪等重跑", "同 G06"),
)
LANE_ZH = {"accel_map": "加速器 accel_map", "process_mount": "加速器行程掛載", "thread_pool": "退回 stdlib 執行緒池",
           "sequential": "逐一（加速器未掛上）", "cache": "TEMP 快取沿用", "worker_process": "子行程分塊"}
# 2026-10-21 第二十四輪：這兩條車道是後來才加的，LANE_ZH 沒跟上（報告上直接印英文 lane 名），
# 燈號那一行也沒跟上（見 def_gate_accel_coverage）。「做完了沒」才是 P09 的判準。


# [VRN-ID] VRN-MAN001-FNC146 · VALIDATE
def def_accel_verdict(e: Dict[str, Any]) -> Tuple[str, str]:
    """一個動作的燈號 ——「它做完了沒」，不是「它跑在哪條車道」。

    2026-10-21 第二十四輪（107 檔實測）：外層 20 個 WARN 裡有 16 個是 P09，其中包含
    `cache · 0.0 秒 · 沿用上次的還原結果`（最好的結果）、`worker_process · 掛掉 0 塊`（成功）、
    `逐一 · 判讀邏輯不可動`（照設計就是不拆）。舊判準 `lane in ("accel_map", "process_mount")`
    只看車道名，完全不看它自己量到的 items / seconds / failed —— 而那兩條車道都要
    `VIA_SuperAccel_Module.py`（在母倉、不在本倉），所以這台機器上每一列在開跑前就註定 WARN。
    「加速器在不在」P04 ACCEL 已經判過一次；同一個判斷做兩遍就是九頭龍，所以這裡不判第二次。
    """
    failed = int(e.get("failed") or 0)
    if failed:                                   # 子行程真的掛了塊 —— 結構化的數字，不是去解析 why 那句中文
        return "WARN", f"掛掉 {failed} 塊"
    if e["lane"] == "sequential" and not e.get("by_design"):
        return "WARN", "一條接一條跑，而且沒說為什麼"
    return "PASS", ""


# [VRN-ID] VRN-MAN001-FNC062 · GATE
def def_gate_accel_coverage(loop_cov: Optional[List[Dict[str, Any]]] = None, with_engines: bool = False) -> List[Dict[str, Any]]:
    """P09: every action and the lane it ran on (accel_map / whole-process mount / fallback), as measured."""
    activated = bool(ACCEL_STATE.get("activated"))
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for e in list(ACCEL_COVERAGE) + list(loop_cov or []):
        key = (e["action"], e["lane"])
        row = merged.setdefault(key, {"action": e["action"], "lane": e["lane"], "items": 0, "seconds": 0.0,
                                      "why": e.get("why", ""), "failed": 0, "by_design": False})
        row["items"] += int(e.get("items") or 0)
        row["seconds"] = round(row["seconds"] + float(e.get("seconds") or 0.0), 3)
        # 2026-10-21：這一段本來只留 action/lane/items/seconds/why —— 掛了幾塊、是不是照設計逐一跑，
        # 在這裡就被丟掉了，燈號想看也看不到。合併要連著結構化的事實一起帶。
        row["failed"] += int(e.get("failed") or 0)
        row["by_design"] = row["by_design"] or bool(e.get("by_design"))
    if with_engines:
        for action, why in ACCEL_BY_DESIGN:
            merged[(action, "design")] = {"action": action, "lane": "process_mount" if activated else "sequential",
                                          "items": 0, "seconds": 0.0, "why": why, "by_design": True}
    rows = []
    for e in merged.values():
        status, note = def_accel_verdict(e)
        detail = LANE_ZH.get(e["lane"], e["lane"]) + (f" · {e['items']} 項 · {e['seconds']} 秒" if e["items"] else "")
        rows.append(def_row("P09 ACCEL", e["action"], status,
                            " · ".join(x for x in (detail, note, e.get("why") or "") if x)))
    lanes = [e["lane"] for e in merged.values()]
    bad = [r for r in rows if r["status"] != "PASS"]
    # 車道分佈照實印出來（資訊不可以不見），但「加速器在不在」不在這裡判第二次 —— 那是 P04 ACCEL 的那一列。
    rows.insert(0, def_row("P09 ACCEL", f"加速器覆蓋：{len(lanes)} 個動作", "WARN" if bad else "PASS",
                           " · ".join(f"{LANE_ZH.get(l, l)} {lanes.count(l)}" for l in sorted(set(lanes)))
                           + (f" · {len(bad)} 個動作沒做完或說不出為什麼逐一跑" if bad else "")))
    return rows


# [VRN-ID] VRN-MAN001-FNC063 · GATE
def def_gate_temp(opened: Dict[str, Any], closed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """P10: the TEMP run of this process and what the deletion rules removed (ssot/VRN_TEMP_POLICY_v0100.json)."""
    if not opened.get("run"):
        return [def_row("P10 TEMP", "TEMP 本輪夾", "WARN", "TEMP 沒有啟用：中介留在記憶體（" + str(opened.get("error", "")) + "）")]
    swept = opened.get("swept") or []
    deleted = [g for g in swept if g.get("deleted")]
    kept = [g for g in swept if not g.get("deleted")]
    return [def_row("P10 TEMP", "TEMP 本輪夾", "PASS", f"{opened['run']} · {closed.get('mb', 0)} MB · 規則冊 VRN_TEMP_POLICY_v0100"),
            def_row("P10 TEMP", f"刪除原則：刪 {len(deleted)} 輪 · 該刪但依規則留下 {len(kept)} 夾", "PASS",
                    "; ".join(f"{g['folder']}（{g.get('rule')}）" for g in deleted[:4])
                    + ("；留下：" + "; ".join(f"{g['folder']}（{g['kept_because']}）" for g in kept[:4]) if kept else ""))] \
        + def_gate_temp_space(opened["run"])



# [VRN-ID] VRN-MAN001-FNC126 · GATE
def def_gate_temp_space(run: str) -> List[Dict[str, Any]]:
    """TEMP 還剩多少 —— 2026-10-19 之前這道閘從來不看。

    P10 報本輪夾、報清掉幾輪，就是不報剩餘空間；而 TEMP 是這條鏈上唯一真的會用完的資源。
    用完的樣子不是一聲乾淨的錯誤：寫到一半的檔留在那裡，下一個讀它的人拿到 JSONDecodeError。
    門檻不自己發明，也不能拿會動的那個數字當尺：`budget` 是「剩餘空間的 25%」算出來的，
    所以 `free < budget` 恆不成立 —— 第一版我就是這樣寫的,那個 WARN 分支永遠跑不到,
    而一道永遠不會警告的閘等於沒有這道閘。改用快取**被設定的上限** VIA_CACHE_MAX_GB
    （預設 10 GB,用引擎自己的 cache_env_num 讀,不另開一套）：剩餘空間連那個都放不下,
    快取就永遠到不了它該有的大小,每一輪都在重做已經算過的東西。
    連 1 GB 都不到就是 FAIL —— 這一輪的中介檔寫不完。
    """
    try:
        import shutil as _shutil
        probe = Path(run)
        while not probe.exists() and probe.parent != probe:
            probe = probe.parent
        usage = _shutil.disk_usage(str(probe))
    except (OSError, ValueError) as error:
        return [def_row("P10 TEMP", "TEMP 剩餘空間", "WARN", f"量不到：{error.__class__.__name__}")]
    free_gb = usage.free / (1 << 30)
    total_gb = usage.total / (1 << 30)
    try:
        cache = def_load_module("VRN_Main_runcache", ENGINE_FILES["runcache"])
        cap_gb = float(cache.cache_env_num("VIA_CACHE_MAX_GB", 10, 0.1, 1024))
    except BaseException:                              # noqa: BLE001 — 讀不到上限就只報空間，不猜
        cap_gb = 0.0
    if free_gb < 1.0:
        status, why = "FAIL", "連 1 GB 都不到：這一輪的中介檔寫不完，會留下半份檔案"
    elif cap_gb and free_gb < cap_gb:
        status, why = "WARN", (f"放不下快取上限 VIA_CACHE_MAX_GB＝{round(cap_gb, 1)} GB："
                               "快取到不了該有的大小，每一輪都在重做算過的東西")
    else:
        status, why = "PASS", (f"快取上限 {round(cap_gb, 1)} GB 放得下" if cap_gb else "")
    return [def_row("P10 TEMP", f"TEMP 剩餘空間 {round(free_gb, 1)} / {round(total_gb, 1)} GB"
                    f"（{round(100 * free_gb / total_gb, 1) if total_gb else 0}%）", status, why)]


# 這支在一輪裡被叫兩次：def_cmd_run_body 一開頭（防線：FAIL 就當場停），以及收尾（回報）。
# 同一支函式、兩個時刻 —— 不是兩套判準。


# [VRN-ID] VRN-MAN001-FNC064 · ENTRY
def def_cmd_standalone(keep: bool = False, accel_home: str = "") -> Tuple[int, List[Dict[str, Any]]]:
    """Copy the VRN folder alone (nothing else from the repository) and prove it answers the same."""
    base = Path(tempfile.mkdtemp(prefix="VRN_standalone_"))
    target = base / "VRN"
    rows: List[Dict[str, Any]] = []
    try:
        shutil.copytree(VRN_ROOT, target, ignore=shutil.ignore_patterns(*SKIP_DIRS, "*.pyc"))
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if accel_home:
            env["VIA_ACCEL_HOME"] = accel_home
        out_json = base / "answers.json"
        cmd = [sys.executable, str(target / Path(__file__).name), "answers", "--json", str(out_json)]
        done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                              stdin=subprocess.DEVNULL, timeout=900)
        if done.returncode != 0 or not out_json.is_file():
            rows.append(def_row("P05 STANDALONE", "單獨複製後可以跑", "FAIL", (done.stdout + done.stderr)[-400:]))
            return 1, rows
        theirs = def_read_json(out_json)
        mine = def_filename_answers()
        rows.append(def_row("P05 STANDALONE", f"單獨複製到 {base}（只有 VRN 資料夾）可以跑", "PASS", ""))
        outside = theirs.get("knowledge_outside_vrn") or []
        rows.append(def_row("P05 STANDALONE", "單獨時引擎讀的知識書都在 VRN 資料夾內", "FAIL" if outside else "PASS",
                            ", ".join(outside) or " · ".join(f"{k}={v}" for k, v in (theirs.get("knowledge_paths") or {}).items() if v)))
        for engine in ("first_page", "database"):
            a, b = mine.get(engine, {}), theirs.get(engine, {})
            diff = sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n))
            rows.append(def_row("P05 STANDALONE", f"{engine} 檔名 {len(a)} 筆：庫內 = 單獨", "WARN" if diff else "PASS",
                                ("差 " + str(len(diff)) + " 筆（VCGC 互動差異）：" + "; ".join(f"{n}: {a.get(n)} -> {b.get(n)}" for n in diff[:4])) if diff else ""))
        return (1 if any(r["status"] == "FAIL" for r in rows) else 0), rows
    except subprocess.TimeoutExpired:
        rows.append(def_row("P05 STANDALONE", "單獨複製後可以跑", "FAIL", "逾時 900 秒"))
        return 1, rows
    finally:
        if not keep:
            shutil.rmtree(base, ignore_errors=True)


# =============================================================================
# 07. 環境與樣本
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC065 · LOGIC
def def_has(module: str) -> bool:
    try:
        with def_quiet():
            importlib.import_module(module)
        return True
    except BaseException:  # noqa: BLE001
        return False


# [VRN-ID] VRN-MAN001-FNC066 · GATE
def def_gate_env() -> List[Dict[str, Any]]:
    rows = [def_row("P01 ENV", "Python", "PASS" if sys.version_info >= (3, 10) else "FAIL",
                    f"{platform.python_version()} · {sys.executable}")]
    live = os.environ.get("VIA_LIVE", "0")
    rows.append(def_row("P01 ENV", "LIVE 關、不連網", "PASS" if live != "1" else "WARN",
                        f"VIA_LIVE={live} VIA_NET={os.environ.get('VIA_NET', '0')}（本入口不設定任何 consent）"))
    deps = {"pdfplumber": "pdfplumber", "fitz": "PyMuPDF", "pandas": "pandas", "pyarrow": "pyarrow", "docx": "python-docx"}
    have = {label: def_has(mod) for mod, label in deps.items()}
    missing = [k for k, v in have.items() if not v]
    pdf_ok = have["pdfplumber"] or have["PyMuPDF"]
    rows.append(def_row("P01 ENV", "PDF 文字層（PyMuPDF / pdfplumber 至少一個）", "PASS" if pdf_ok else "FAIL",
                        " · ".join(f"{k} {'有' if v else '缺'}" for k, v in have.items())))
    if missing:
        rows.append(def_row("P01 ENV", "選配套件", "WARN", "缺 " + ", ".join(missing) +
                            "；安裝是操作員的手：pip install " + " ".join(m.lower() for m in missing)))
    return rows


# [VRN-ID] VRN-MAN001-FNC067 · GATE
def def_gate_samples(samples: str, cache: Any = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not samples:
        return [def_row("P07 SAMPLES", "樣本資料夾", "SKIP", "沒有指定（用合成語料）")], {}
    root = Path(samples)
    if not root.is_dir():
        return [def_row("P07 SAMPLES", str(root), "WARN", "資料夾不存在：改用合成語料")], {}
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SAMPLE_SUFFIXES)
    t0 = time.time()
    if cache is not None and getattr(cache, "enabled", False):   # 2026-10-13: a file not touched since the last run is not read again
        shas = cache.cache_sample_sha(files, mapper=lambda fn, items: def_parallel_map(fn, items, action="P07 樣本：逐檔 SHA-256 存證（改過的才讀）"))
    else:
        shas = def_parallel_map(def_sha256_stream, files, action="P07 樣本：逐檔 SHA-256 存證")
    by_suffix: Dict[str, int] = {}
    for p in files:
        by_suffix[p.suffix.lower()] = by_suffix.get(p.suffix.lower(), 0) + 1
    evidence = {"root": str(root), "files": len(files), "by_suffix": dict(sorted(by_suffix.items())),
                "sha256": {def_rel(p, root): s for p, s in zip(files, shas)}, "hash_seconds": round(time.time() - t0, 2),
                "accelerated": bool(ACCEL_STATE["loaded"])}
    status = "PASS" if files else "WARN"
    return [def_row("P07 SAMPLES", str(root), status,
                    f"{len(files)} 檔 · " + " · ".join(f"{k} {v}" for k, v in evidence["by_suffix"].items()) +
                    f" · SHA-256 {evidence['hash_seconds']} 秒（{'加速器 accel_map' if evidence['accelerated'] else '標準庫執行緒池'}）")], evidence


# =============================================================================
# 08. 報告
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC106 · LOGIC
def def_open_report(html_path, verdict, suppressed=False, ui_ok=True):
    """操作員 2026-10-16「輸出後驗證無誤 自動跳出 U/I」：跑完就把 HTML 報告開起來。

    只有驗證無誤才開，兩道都要過：
      一、結論不是 RED —— 紅燈要看的是終端機上那幾行 FAIL，不是一個漂亮的頁面；
      二、P20 UI 閘過了 —— 頁面上的數字跟 JSON 對得上。數字對不上的頁面比沒有頁面更糟，
          它看起來就像一份完整的報告。
    開不起來絕不讓整跑失敗：沒有桌面環境（CI、SSH、容器）本來就開不了，照實說一行就好。
    """
    if suppressed:
        return "--no-open"
    if not ui_ok:
        print("[UI] HTML 跟 JSON 對不上，不自動開；先看上面的 UI-VERIFY 紅燈")
        return "ui-fail"
    if str(verdict).upper() == "RED":
        print("[UI] 驗證有 FAIL，不自動開報告；先看上面的紅燈")
        return "RED"
    if os.environ.get("VRN_NO_OPEN") or os.environ.get("CI"):
        return "env"
    if os.name != "nt" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print(f"[UI] 沒有桌面環境，不自動開；報告在 {html_path}")
        return "headless"
    try:
        import webbrowser
        if webbrowser.open(Path(html_path).resolve().as_uri()):
            print(f"[UI] 已開啟報告 {html_path}")
            return "opened"
        print(f"[UI] 開不起來（沒有可用的瀏覽器）；報告在 {html_path}")
        return "no-browser"
    except Exception as error:  # noqa: BLE001
        print(f"[UI] 開不起來（{error.__class__.__name__}）；報告在 {html_path}")
        return "error"


# [VRN-ID] VRN-MAN001-FNC120 · GATE
def def_gate_ocr() -> List[Dict[str, Any]]:
    """P22：影像檔的 OCR —— 找得到引擎就說哪一支，找不到就照實說找不到。

    2026-10-19 操作員開閘「接 OCR」。**但 OCR 的字不進判讀**：實測中文會掉字
    （台積電→台電、投資評等→投資等），拿它當 VERIFIED 的兩條讀法之一會製造假綠燈。
    這一列只回報能力在不在；要不要讓 OCR 的值進矩陣，是另一個決定。
    """
    gate = "P22 OCR"
    try:
        ocr = def_load_module("VRN_Main_ocr", ENGINE_FILES["ocr"])
    except Exception as error:  # noqa: BLE001
        return [def_row(gate, "VRN_Ocr", "WARN", f"{error.__class__.__name__}: {error}"[:200])]
    av = ocr.available()
    if not av["engine"]:
        borrowed = def_gate_ocr_borrowed(ocr)
        if borrowed:
            return borrowed
        return [def_row(gate, "OCR 引擎：都不在", "WARN",
                        av["why"] + " —— 影像檔照舊列 OCR_REQUIRED。裝法：系統裝 Tesseract（PyMuPDF 就用得到），"
                                    "或 pip install rapidocr_onnxruntime（純 pip，不需要系統二進位檔）；"
                                    "或先跑一次 VRN-2 啟動器（v0131 起）—— 它建的 OCR 隔離環境 VRN-1 借得到（G23）")]
    rows = [def_row(gate, f"OCR 引擎：{av['engine']}", "PASS", av["why"])]
    try:
        checks = ocr.def_checks()
    except Exception as error:  # noqa: BLE001 - 自測爆掉不該讓整條指令倒掉
        rows.append(def_row(gate, "已知答案", "WARN", f"自測丟了 {error.__class__.__name__}: {error}"[:180]))
        return rows
    # 三態照實畫：GAP 是「這台機器驗不到」，不是過也不是壞 —— 當成 PASS 就是把沒驗到的講成驗過了。
    for name, state, detail in checks:
        rows.append(def_row(gate, name, {"PASS": "PASS", "FAIL": "FAIL", "GAP": "WARN"}[state],
                            str(detail)[:200]))
    rows.append(def_row(gate, "OCR 的字不進判讀", "PASS",
                        "結果一律標 source=OCR／lossy_cjk=True；G06 的影像檔有真的送進 OCR，"
                        "讀到什麼寫在那一列，但那些字不回給判讀"))
    return rows


# [VRN-ID] VRN-MAN001-FNC138 · GATE
def def_gate_ocr_borrowed(ocr: Any) -> List[Dict[str, Any]]:
    """2026-10-20（操作員「工具可相互取用」）：VRN-1 自己的三支 OCR 都不在 → 借 VRN-2 的 OCR 隔離環境（VRN_ToolBridge · sha256 核對過）。
    借到就讀一次已知圖：數字與拉丁字要全中（中文會掉字是 rapidocr 的行為，不算錯）· 借不到 → 回 []（照舊 WARN「都不在」）。"""
    gate = "P22 OCR"
    if os.environ.get("VRN_NO_BORROW") == "1":
        return []
    try:
        tb = def_load_module("VRN_Main_toolbridge", ENGINE_FILES["toolbridge"])
        fn, rec = tb.borrow("ocr.image")
    except Exception:  # noqa: BLE001 - 借不到 = 沒有這條路，回去照舊寫「都不在」
        return []
    rows = [def_row(gate, "OCR 引擎：借用 VRN-2 ocr.image", "PASS",
                    f"VRN-1 自己的三支都不在；{rec['from']} {Path(rec['file']).name}（sha256 {rec['sha256'][:12]} 與工具冊相同）· {rec.get('reader', '')}")]
    try:
        with tempfile.TemporaryDirectory(prefix="vrn_ocr_borrow_") as td:
            got = fn(str(ocr.def_known_image(Path(td))))
    except Exception as error:  # noqa: BLE001
        return rows + [def_row(gate, "借來的 OCR · 已知圖", "WARN", f"{error.__class__.__name__}: {error}"[:200])]
    if got.get("error"):
        return rows + [def_row(gate, "借來的 OCR · 已知圖", "WARN", str(got["error"])[:200])]
    text = got.get("text") or ""
    miss = [k for k in ocr.KNOWN_HARD if k not in text.replace(" ", "")]
    rows.append(def_row(gate, "借來的 OCR · 已知圖：數字與拉丁字全中", "PASS" if not miss else "FAIL",
                        f"{got.get('engine')} · 讀到 {got.get('chars', 0)} 字" + (f" · 少了 {'、'.join(miss)}" if miss else "")))
    rows.append(def_row(gate, "OCR 的字不進判讀", "PASS", "借來的結果也一律 source=OCR／lossy_cjk=True；只進報告，不回給判讀"))
    return rows


CROSS_RULE = "相互對照兩個以上來源相同即算對照成功（判準在 VRN_TitleTrim._vote 的 agree >= 2，這裡只讀回來）"


# [VRN-ID] VRN-MAN001-FNC130 · LOGIC
def def_cross_source_scan(out: Path) -> Dict[str, Any]:
    """每個對照成功（VERIFIED）的部位,都要真的有 >= 2 個來源支持 —— 讀引擎記下的 agree,不自己重判。

    2026-10-19 操作員：「相互對照兩個以上相同即算對照成功」。那條規則本來就在
    `VRN_TitleTrim._vote`（`len(top["groups"]) >= 2`），但以前只活在 why 那句中文裡,
    下游要驗只能解析散文。現在 _vote 一併記下 agree,這裡讀數字。

    **沒有 agree 的 VERIFIED 不是錯,是「沒走共用判準」** —— 例如從別的部位繼承狀態的
    title.core_view,或拿資料庫當其中一個來源的公司名與現價。照實分開數、點名,不混進違規。
    """
    path = out / "autotest" / "round1" / "dataframes" / "vrn_trim_parts.csv"
    got: Dict[str, Any] = {"rule": CROSS_RULE, "verified": 0, "with_agree": 0, "violations": [], "own_path": {},
                           "own_kinds": {}, "path": ""}
    if not path.is_file():
        return got
    got["path"] = str(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if (row.get("state") or "") != "VERIFIED":
                continue
            got["verified"] += 1
            raw = (row.get("agree") or "").strip()
            if not raw:
                part = row.get("part") or "?"
                got["own_path"][part] = got["own_path"].get(part, 0) + 1
                kind = part.split(".", 1)[0] + ".*"          # annual.* / title.* / cover.*：整群都要看得到,不是只看前幾名
                got["own_kinds"][kind] = got["own_kinds"].get(kind, 0) + 1
                continue
            got["with_agree"] += 1
            try:
                if int(raw) < 2:
                    got["violations"].append({"file": row.get("file", ""), "part": row.get("part", ""), "agree": raw})
            except ValueError:
                got["violations"].append({"file": row.get("file", ""), "part": row.get("part", ""), "agree": raw})
    return got


# [VRN-ID] VRN-MAN001-FNC131 · GATE
def def_gate_cross_source(scan: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not scan or not scan.get("path"):
        return []
    bad, own = scan["violations"], scan["own_path"]
    # 標題只說**這條規則真的驗到的那些**。寫「對照成功 1310 個」會被讀成「1310 個都過了兩來源對照」,
    # 而實際上只有 640 個走這條規則 —— 剩下 670 個是別條路徑判的,說成同一件事就是把沒驗到的算成驗過了。
    own_total = sum(own.values())
    detail = CROSS_RULE + f" · VERIFIED {scan['verified']} 個部位裡,走共用判準的 {scan['with_agree']} 個"
    if own:
        detail += (f" · 另外 {own_total} 個沒走共用判準（各自的路徑,這條規則沒驗到,不當成違規也不當成驗過）："
                   + "、".join(f"{k}（{n}）" for k, n in sorted(scan.get("own_kinds", {}).items(), key=lambda kv: -kv[1]))
                   + " · 最多的部位：" + "、".join(f"{k}（{n}）" for k, n in sorted(own.items(), key=lambda kv: -kv[1])[:3]))
    rows = [def_row("P24 CROSS", f"兩個以上來源對上的部位 {scan['with_agree']} 個 · 來源數不足的 {len(bad)} 個"
                                 f" · 各自路徑另計 {own_total} 個",
                    "FAIL" if bad else "PASS", detail)]
    for v in bad[:6]:
        rows.append(def_row("P24 CROSS", f"{v['part']} · agree={v['agree']}", "FAIL",
                            f"{v['file']} 標成對照成功，但支持的來源群組不到 2 個 · {CROSS_RULE}"))
    return rows


TIME_RULE = "時間擷取後一律三種形式之一：YYYY · YYYY-MM · YYYY-MM-DD"
TIME_OK_RX = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
# 欄名按**詞**比，不是子字串也不是正則邊界：
#   子字串      → CompanyNameCan[date] 被誤判成時間欄（29 次）
#   正則詞邊界  → camelCase 的 Report[Date]Display 前後都是字母，整欄漏掉（150 筆斜線日期沒被抓到）
# 兩種我都寫過，兩種都錯。切成詞再比才同時擋住誤判與漏判。
TIME_WORDS = {"date", "dates", "period", "periods", "fiscal", "year", "years", "quarter", "quarters"}
TIME_CJK_RX = re.compile(r"日期|年度|季別")
# 規則管的是「擷取後的資料」。這三類照實排除，而且**在閘的說明欄點名**，不是默默跳過：
#   *_raw / *Raw  原文欄，存在的理由就是留住來源長什麼樣（2024A 旁邊就有正規化好的 period）
#   CreatedAt / UpdatedAt / RunID  系統寫入時戳，不是從報告裡擷取的
TIME_SKIP_RX = re.compile(r"(?:_raw|raw)$|^(?:createdat|updatedat|runid)$", re.I)
# 欄名帶這些詞的，說的是「時間的種類／狀態」而不是擷取到的時間值：
#   PeriodType=FY（期別的種類）· DateConflict=「檔名 X vs 首頁 Y」（為什麼對不上）· PeriodLabelRaw
# 一樣切成詞再比（同一套切法，兩份詞表），一樣在說明欄點名。
# Codex PR #73 P2 教的那一課：這些本來是被「值裡面有沒有連續四位數字」默默濾掉的 ——
# 那條濾網同時也會濾掉**真的違規**（114/12/02、Q1、unknown 都沒有連續四位數字），
# 閘照報 PASS。不知道不等於沒事：濾網拆掉，例外改成照欄名明講。
TIME_ABOUT_WORDS = {"type", "kind", "label", "conflict", "status"}


# [VRN-ID] VRN-MAN001-FNC136 · LOGIC
def def_time_words(name: str) -> set:
    """欄名切成詞（camelCase／底線／數字都切開）—— 切法只有這一份，兩份詞表共用。"""
    return {w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", name or "")}


# [VRN-ID] VRN-MAN001-FNC132 · LOGIC
def def_time_field(name: str) -> bool:
    """欄名是不是時間欄 —— camelCase／底線／CJK 都切成詞再比，判準只有這一份。"""
    return bool(def_time_words(name) & TIME_WORDS) or bool(TIME_CJK_RX.search(name or ""))


# [VRN-ID] VRN-MAN001-FNC137 · LOGIC
def def_time_about(name: str) -> bool:
    """這一欄說的是「時間的種類／狀態」，不是擷取到的時間值（PeriodType、DateConflict）。"""
    return bool(def_time_words(name) & TIME_ABOUT_WORDS)


# [VRN-ID] VRN-MAN001-FNC133 · LOGIC
def def_time_scan(out: Path) -> Dict[str, Any]:
    """把這一輪輸出裡每一個時間欄掃過，分成合規與不合規 —— 規則沒有閘在管就不是規則。

    2026-10-19 操作員：「時間擷取後格式一律為 YYYY / YYYY-MM / YYYY-MM-DD」。
    判準只有 TIME_OK_RX 這一份；排除清單寫在 TIME_SKIP_RX，而且會印進閘的說明欄 ——
    看得到的例外才是例外，看不到的叫漏掉。
    """
    folder = out / "autotest" / "round1" / "dataframes"
    # 2026-10-20：驗證過的輸出（G21 · <round>/verified/）也是輸出 —— 同一條三形規則一起掃
    folders = [folder] + ([folder.parent / "verified"] if (folder.parent / "verified").is_dir() else [])
    ok: Dict[str, int] = {}
    bad: Dict[str, Dict[str, Any]] = {}
    skipped: Dict[str, int] = {}
    structured: Dict[str, int] = {}
    about: Dict[str, int] = {}
    if not folder.is_dir():
        return {"rule": TIME_RULE, "ok": ok, "bad": bad, "skipped": skipped, "structured": structured,
                "about": about, "folder": ""}
    for path in sorted(p for f in folders for p in f.glob("*.csv")):
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except OSError:
            continue
        for column in (rows[0].keys() if rows else []):
            name = str(column or "").lstrip("\ufeff")
            if not def_time_field(name):
                continue
            key = f"{path.name}:{name}"
            if TIME_SKIP_RX.search(name):
                skipped[key] = sum(1 for r in rows if (r.get(column) or "").strip())
                continue
            if def_time_about(name):
                about[key] = sum(1 for r in rows if (r.get(column) or "").strip())
                continue
            for row in rows:
                value = (row.get(column) or "").strip()
                if not value:
                    continue
                # 結構要**先**判:放在「像不像時間」之後的話,一個結構值會因為碰巧沒有連續四位數字
                # 而被默默跳過（測試 fixture 用 {"day":15,"month":9} 就打中了這個洞）。
                if value[:1] in "[{":
                    # 結構不是時間值：PartialDates、DateConflict 這種欄裝的是「為什麼沒擷取到」的診斷
                    # （`{"day":15,"month":9,"status":"YEAR_MISSING"}` —— 沒有年，三種形式本來就表達不了）。
                    # 用通則擋，不為單一欄位開特例。
                    structured[key] = structured.get(key, 0) + 1
                    continue
                # 這裡**不准**再有「看起來不像時間就跳過」那種濾網：非空、欄名在管、不是結構值，
                # 就一定要過 TIME_OK_RX。濾網放過的正是最該抓的那些（114/12/02、Q1、unknown）。
                if TIME_OK_RX.match(value):
                    ok[key] = ok.get(key, 0) + 1
                else:
                    seen = bad.setdefault(key, {"n": 0, "example": value})
                    seen["n"] += 1
    return {"rule": TIME_RULE, "ok": ok, "bad": bad, "skipped": skipped, "structured": structured,
            "about": about, "folder": str(folder)}


# [VRN-ID] VRN-MAN001-FNC134 · GATE
def def_gate_time_format(scan: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not scan or not scan.get("folder"):
        return []
    ok, bad, skipped = scan["ok"], scan["bad"], scan["skipped"]
    total_ok = sum(ok.values())
    total_bad = sum(v["n"] for v in bad.values())
    detail = TIME_RULE + f" · 合規 {total_ok} 筆（{len(ok)} 欄）"
    if skipped:
        detail += " · 原文欄不受規則管：" + "、".join(f"{k.split(':')[-1]}（{n}）" for k, n in sorted(skipped.items())[:5])
    if scan.get("about"):
        detail += (" · 欄名說的是時間的種類／狀態，不是時間值：" +
                   "、".join(f"{k.split(':')[-1]}（{n}）" for k, n in sorted(scan["about"].items())[:4]))
    if scan.get("structured"):
        detail += " · 結構不是時間值：" + "、".join(f"{k.split(':')[-1]}（{n}）" for k, n in sorted(scan["structured"].items())[:4])
    rows = [def_row("P23 TIME", f"時間欄位格式：{len(bad)} 欄不合規", "PASS" if not bad else "FAIL", detail)]
    for key, info in sorted(bad.items(), key=lambda kv: -kv[1]["n"])[:8]:
        rows.append(def_row("P23 TIME", f"{key} × {info['n']}", "FAIL", f"例：{info['example'][:60]} · {TIME_RULE}"))
    return rows


ACCEPT_RULE = ("一份報告 100% 過關 ＝ 逐項驗過，而且待修清單上沒有優先 0／1／2 的項"
               "（優先 3 是 SINGLE：只有一條讀法、鎖不住，不是讀錯）")


# [VRN-ID] VRN-MAN001-FNC127 · LOGIC
def def_fix_rule():
    """待修優先序的門檻住在 VRN_AutoTestLoop（它產生那份清單），這裡只去要答案。

    2026-10-19：這個門檻本來這支檔案自己也有一份（`<= 2` 寫在 def_acceptance 裡），
    而 G00 LOCK 又用「有列就 WARN」自成一套。同一次跑、同樣三項 priority 3 SINGLE，
    P21 驗收說「3/3 份 100% 過關」，G00 LOCK 說「待修 3 項」，並排印給操作員看。
    ACCEPT_RULE 的文字留在這裡（它是給人看的那句話），判斷只留一份，在引擎那邊。
    """
    return def_load_module("VRN_Main_autotest", ENGINE_FILES["autotest"])


# [VRN-ID] VRN-MAN001-FNC118 · LOGIC
def def_acceptance(out: Path) -> Dict[str, Any]:
    """每一份報告過不過關 —— 操作員 2026-10-18「我直接在上面操作看另外 80 個報告是否可達 100% 過關」。

    **這裡不定義「過關」**：每一項的優先序是待修清單（VRN_TitleTrim.fix_rows，對照表在
    ssot/VRN_TitleTrim_SSOT_v0100.json 的 verify.fix_priority）算的，「優先幾算擋住」是
    VRN_AutoTestLoop.def_fix_blocks 判的，這裡只是讀回來按檔分組。
    自己再判一次就是第二顆頭 —— 同一個問題會出現兩個答案，而且遲早不一樣。
    2026-10-19 就真的出現過：這裡寫死 `<= 2`，G00 LOCK 另外算「有列就 WARN」，
    同一次跑同樣三項 priority 3 並排印出 PASS 和 WARN。

    逐項驗過的是個股（status OK）；非個股（NOT_STOCK：晨會、產業展望、盤後）沒有逐項部位可驗，
    照實標成「未逐項驗」，不混進分母假裝過關。
    """
    rounds = sorted(out.glob("autotest/round*/titletrim"))
    if not rounds:
        return {}
    folder = rounds[-1]
    results = def_read_json(folder / "VRN_TitleTrim_Results_v0100.json")
    fixlist = def_read_json(folder / "VRN_FixList_v0100.json")
    if not isinstance(results, list) or not results:
        return {}
    blocks = def_fix_rule().def_fix_blocks
    todo: Dict[str, List[Dict[str, Any]]] = {}
    for r in (fixlist.get("rows") if isinstance(fixlist, dict) else fixlist) or []:
        if blocks(r):
            todo.setdefault(str(r.get("file", "")), []).append(r)
    rows = []
    for r in results:
        name = str(r.get("file", ""))
        checked = r.get("status") == "OK"
        open_items = todo.get(name, [])
        rows.append({"file": name, "doc_class": r.get("doc_class") or "", "checked": checked,
                     "parts": len(r.get("parts") or []), "open": len(open_items),
                     "verdict": ("過關" if not open_items else "待修") if checked else "未逐項驗",
                     "why": "；".join(f"{x.get('part')} {x.get('state')}" for x in open_items[:4])})
    checked = [x for x in rows if x["checked"]]
    passed = [x for x in checked if not x["open"]]
    return {"rows": rows, "checked": len(checked), "passed": len(passed), "files": len(rows),
            "rule": ACCEPT_RULE, "folder": str(folder)}


# [VRN-ID] VRN-MAN001-FNC119 · GATE
def def_gate_acceptance(accept: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not accept:
        return []
    passed, checked = accept["passed"], accept["checked"]
    bad = [x["file"] for x in accept["rows"] if x["verdict"] == "待修"]
    return [def_row("P21 驗收", f"逐項驗過的報告 {passed}/{checked} 份 100% 過關"
                    + (f"（另有 {accept['files'] - checked} 份非個股，沒有逐項部位可驗）" if accept["files"] > checked else ""),
                    "PASS" if checked and passed == checked else "WARN",
                    ACCEPT_RULE if passed == checked else "待修：" + "、".join(bad[:6])
                    + (f" 等 {len(bad)} 份" if len(bad) > 6 else ""))]


# [VRN-ID] VRN-MAN001-FNC140 · REPORT
def def_record_html(out: Path) -> str:
    """代號紀錄（四碼代號 → 15 欄）畫進操作員會開的那份 HTML。

    2026-10-20：這張表以前只有 CSV 和 `matrix --view record` 子命令看得到 —— 一輪實測的收尾
    不畫它，所以第十一輪（代號兩條讀法對上）與第十七輪（上漲空間 DERIVED）修好的東西，
    操作員在 HTML U/I 上一個字都看不到。**欄位、記號、狀態統計一律取自 VRN_Matrix 的
    build_record_matrix，不在這裡另立一套**；連記號說明都用它的 LEGEND。
    """
    try:
        mx = def_load_module("VRN_Main_matrix_html", ENGINE_FILES["matrix"])
        model = mx.build_record_matrix(out)
    except Exception:                                   # noqa: BLE001
        return ""                                       # 畫不出來就不畫，不擋收尾（矩陣自己有閘）
    rows = model.get("rows") or []
    if not rows:
        return ""
    cols = model["columns"]
    tally: Dict[str, int] = {}
    for counter in (model.get("totals") or {}).values():
        for state, n in counter.items():
            tally[state] = tally.get(state, 0) + n
    trs = []
    for r in rows:
        tds = "".join(f"<td>{html.escape(str((r['cells'].get(k) or {}).get('text', '')))}</td>" for k, _zh in cols)
        trs.append(f"<tr><td>{html.escape(str(r.get('file', '')))}</td>{tds}</tr>")
    head = "".join(f"<th>{html.escape(zh)}</th>" for _k, zh in cols)
    return ("<h2>代號紀錄 · 四碼代號 → 15 欄</h2>"
            f"<p class=\"a\">個股報告 <b>{len(rows)}</b> 份 · "
            + " · ".join(f"{s} {n}" for s, n in sorted(tally.items(), key=lambda x: -x[1]))
            + "</p>"
            + f"<p class=\"r\">{html.escape(getattr(mx, 'LEGEND', ''))}</p>"
            + "<div class=\"wide\"><table><thead><tr class=\"hd\"><th>報告</th>" + head + "</tr></thead>"
            + "<tbody class=\"rec\">" + "".join(trs) + "</tbody></table></div>")


# [VRN-ID] VRN-MAN001-FNC068 · IO
def def_write_report(out: Path, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    json_path = out / "VRN_Main_Report_v0100.json"
    html_path = out / "VRN_Main_Report_v0100.html"
    def_write_json(json_path, payload)
    colors = {"PASS": "#1a7f37", "WARN": "#9a6700", "FAIL": "#cf222e", "SKIP": "#6e7781"}
    verdict_color = {"GREEN": "#1a7f37", "AMBER": "#9a6700", "RED": "#cf222e"}.get(payload["verdict"], "#6e7781")
    lines = []
    for r in payload["rows"]:
        c = colors.get(r["status"], "#6e7781")
        lines.append(f"<tr><td>{html.escape(r['gate'])}</td><td>{html.escape(r['item'])}</td>"
                     f"<td style='color:{c};font-weight:600'>{r['status']} {STATUS_ZH.get(r['status'], '')}</td>"
                     f"<td>{html.escape(str(r.get('detail', '')))}</td></tr>")
    accept = payload.get("acceptance") or {}
    accept_html = ""
    if accept.get("rows"):
        mark = {"過關": "#1a7f37", "待修": "#cf222e", "未逐項驗": "#6e7781"}
        trs = []
        for a in accept["rows"]:
            c = mark.get(a["verdict"], "#6e7781")
            trs.append(f"<tr><td>{html.escape(a['file'])}</td><td>{html.escape(a['doc_class'])}</td>"
                       f"<td style='color:{c};font-weight:600'>{a['verdict']}</td>"
                       f"<td>{a['parts'] and str(a['parts']) + ' 個部位' or ''}</td>"
                       f"<td>{html.escape(a['why'])}</td></tr>")
        # 篩選沿用驗證矩陣那一頁同一種寫法（一行 oninput），不另外發明一套。
        accept_html = (
            f"<h2>驗收 · 每一份報告是否 100% 過關</h2>"
            f"<p class=\"a\">逐項驗過的報告 <b>{accept['passed']}/{accept['checked']}</b> 份 100% 過關"
            + (f"；另有 {accept['files'] - accept['checked']} 份非個股，沒有逐項部位可驗。" if accept['files'] > accept['checked'] else "。")
            + f"</p><p class=\"r\">{html.escape(accept['rule'])}</p>"
            + "<input id=\"q\" placeholder=\"篩選（檔名、類別，或打「待修」只看要處理的）\""
              " oninput=\"for(const r of document.querySelectorAll('tbody.acc tr'))"
              "r.style.display=r.textContent.includes(this.value)?'':'none'\">"
            + "<table><thead><tr class=\"hd\"><th>報告</th><th>類別</th><th>驗收</th><th>驗了什麼</th><th>待修的部位</th></tr></thead>"
            + "<tbody class=\"acc\">" + "".join(trs) + "</tbody></table>")
    loop = payload.get("autotest") or {}
    loop_html = ""
    if loop:
        # href 要相對這份報告,不是裸檔名：迴圈明細在 out/autotest/ 底下,只寫檔名會連到不存在的同層檔
        # （2026-10-16 P20 UI 閘第一次真跑就抓到這個壞連結）。
        href = text = ""
        if loop.get("html"):
            target = Path(loop["html"])
            text = target.name
            try:
                href = target.resolve().relative_to(out.resolve()).as_posix()
            except (ValueError, OSError):
                href = text
        loop_html = (f"<h2>自動測試迴圈 {html.escape(loop.get('loop', ''))}</h2><p>結論 <b>{html.escape(str(loop.get('verdict')))}</b> · "
                     + " · ".join(f"{k} {v}" for k, v in (loop.get("counts") or {}).items())
                     + (f" · 明細：<a href='{html.escape(href)}'>{html.escape(text)}</a>" if href else "") + "</p>")
        ver = loop.get("verified") or {}
        if ver.get("html") and Path(ver["html"]).is_file():
            # 2026-10-20：驗證過的輸出（G21）—— 每一筆回原檔逐欄證明，證不出來的不進輸出；連結相對這份報告（P20 會點它）
            try:
                vhref = Path(ver["html"]).resolve().relative_to(out.resolve()).as_posix()
            except (ValueError, OSError):
                vhref = Path(ver["html"]).name
            vfin = (ver.get("counts") or {}).get("financial") or {}
            loop_html += (f"<h2>驗證過的輸出</h2><p>年度數據 {vfin.get('verified', 0) + vfin.get('corrected', 0)}/{vfin.get('in', 0)}"
                          f"（自動修正 {vfin.get('corrected', 0)} · 剔除 {vfin.get('rejected', 0)}）· "
                          f"<a href='{html.escape(vhref)}'>{html.escape(Path(ver['html']).name)}</a></p>")
        pv = loop.get("pivot") or {}
        if pv.get("html") and Path(pv["html"]).is_file():
            # 2026-10-20：PIVOT 資料庫（G22）—— 驗證過的年度數據轉成資料庫形式；連結相對這份報告
            try:
                phref = Path(pv["html"]).resolve().relative_to(out.resolve()).as_posix()
            except (ValueError, OSError):
                phref = Path(pv["html"]).name
            pcn = pv.get("counts") or {}
            loop_html += (f"<h2>PIVOT 資料庫</h2><p>事實 {pcn.get('kept', 0)}/{pcn.get('facts', 0)} · 年度 {pcn.get('pivot_report_annual', 0)} 列 · "
                          f"季度 {pcn.get('pivot_report_quarterly', 0)} 列 · 衝突 {pcn.get('conflicts', 0)} · "
                          f"<a href='{html.escape(phref)}'>{html.escape(Path(pv['html']).name)}</a></p>")
        bw = loop.get("borrow") or {}
        if bw.get("rows"):
            loop_html += ("<h2>借用工具（VRN-2）</h2><p>" + " · ".join(html.escape(f"{r['id']} {r['state']}") for r in bw["rows"])
                          + f"</p><p class='r'>{html.escape(str(bw.get('note') or ''))}</p>")
    doc = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN-1 研究報告系統 · 實測報告</title><style>
body{{font-family:system-ui,"Microsoft JhengHei",sans-serif;margin:16px;color:#1f2328;background:#fff}}
table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border-bottom:1px solid #d0d7de;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f6f8fa}}.v{{font-size:20px;font-weight:700;color:{verdict_color}}}
@media (prefers-color-scheme:dark){{body{{background:#0d1117;color:#e6edf3}}th{{background:#161b22}}td,th{{border-color:#30363d}}}}
/* 手機（2026-10-17 實機測出來的）：四欄硬排會把「狀態」整欄推出畫面外 —— 390px 下量到 736px
   水平溢出，看不到燈號的報告等於沒有報告。窄螢幕改成每列一張卡，四個值各自一行，全部看得見。 */
h2{{font-size:17px;margin:22px 0 6px}}
p.a{{font-size:15px;margin:2px 0}}
p.r{{font-size:12px;color:#57606a;margin:0 0 8px}}
/* box-sizing 不能省：content-box 加上 padding 與 border 會把輸入框推出畫面（390px 下實測溢出 2px）。 */
#q{{box-sizing:border-box;width:min(420px,100%);padding:6px 8px;border:1px solid #d0d7de;border-radius:6px;margin:0 0 8px;font:inherit}}
/* 代號紀錄 16 欄：桌機讓它在自己的框裡橫向捲，不可以把整頁推出畫面（手機仍然走下面的卡片）。 */
.wide{{overflow-x:auto}}.wide table{{font-size:12px}}
@media (min-width:641px){{
.wide td,.wide th{{white-space:nowrap}}
/* 橫向捲到右邊看「上漲%」時，報告名要跟著留在畫面上 —— 不然看得到數字卻不知道是哪一份
   （2026-10-20 實機捲到底截圖就是這樣：第一欄整欄空白）。 */
.wide td:first-child,.wide th:first-child{{position:sticky;left:0;background:#fff;z-index:1}}
}}
@media (min-width:641px) and (prefers-color-scheme:dark){{.wide td:first-child{{background:#0d1117}}.wide th:first-child{{background:#161b22}}}}
@media (max-width:640px){{
table,thead,tbody,tr,td{{display:block;width:auto}}.hd{{display:none}}
tr{{border-bottom:1px solid #d0d7de;padding:8px 0}}
td{{border:0;padding:1px 0;word-break:break-word}}
td:first-child{{font-weight:600;font-size:12px;opacity:.75}}
}}
</style></head><body>
<h1>VRN-1 研究報告系統 · {html.escape(MAIN_NAME)}</h1>
<p class="r">VRN-1（本系統，MAIN 是 {html.escape(MAIN_NAME)}）—— 不是操作員機器上那套 VRN-2（VRN_SystemManager_v0214.py，由 ActivateVRN-2 啟動）。兩套會同時開著，所以這裡寫明是哪一套。</p>
<p class="v">{payload['verdict']} · {' · '.join(f"{k} {v}" for k, v in payload['counts'].items())}</p>
<p>{html.escape(payload['generated'])} · 樣本 {html.escape(str(payload.get('samples') or '合成語料'))} · 加速器 {html.escape(payload['accelerator'].get('canonical') or '未載入')}</p>
<table id="gates"><tr class="hd"><th>閘</th><th>項目</th><th>狀態</th><th>說明</th></tr>{''.join(lines)}</table>
{accept_html}
{def_record_html(out)}
{loop_html}
</body></html>"""
    def_write_atomic(html_path, doc)                # 操作員會開的那份；寫到一半被讀到就是半頁
    return json_path, html_path


# =============================================================================
# 08b. 收尾：VCGC 的 token 預算 · HTML U/I 驗證
# =============================================================================
# VRN 被單獨複製出去時就沒有倉根了（engine/VRN_LocalDB 的 candidates() 是同一套誠實判斷）。
_REPO_ROOT = VRN_ROOT.parent.parent if VRN_ROOT.parent.name == "functional modules" else None
CAPSULE_POLICY_PATH = (_REPO_ROOT / "config" / "ssot" / "VIA_SystemMaster.via") if _REPO_ROOT else None
CAPSULE_POLICY_FALLBACK = {"protocol": "REFERENCE_FIRST_DELTA_ONLY", "max_chars": 12000, "max_items": 24}


# [VRN-ID] VRN-MAN001-FNC109 · LOGIC
def def_capsule_budget() -> Dict[str, Any]:
    """VCGC 的省 token 契約上限。正本在 Root SSOT，VRN 只讀不訂。

    讀得到就用正本、來源標 root-ssot；讀不到就用內建值、來源標 engine-default 並說為什麼 ——
    跟 via_unified_engine 的 def_capsule_policy 同一套誠實規則（同一份正本，不是第二套預算）。
    """
    out = dict(CAPSULE_POLICY_FALLBACK, source="engine-default", why="")
    if CAPSULE_POLICY_PATH is None:
        out["why"] = "VRN 單獨複製在倉外，看不到 Root SSOT（照跑）"
        return out
    try:
        doc = json.loads(CAPSULE_POLICY_PATH.read_text(encoding="utf-8-sig"))
        pol = ((doc.get("token_governance") or {}).get("capsule_policy")) or {}
        if not pol:
            out["why"] = f"{def_rel(CAPSULE_POLICY_PATH)} 裡沒有 token_governance/capsule_policy"
            return out
        for key in ("max_chars", "max_items"):
            if key in pol:
                if not isinstance(pol[key], int):
                    out["why"] = f"{key} 不是整數（SSOT 漂移），改用內建值"
                    return out
                out[key] = pol[key]
        out["protocol"] = pol.get("protocol") or out["protocol"]
        out["source"] = "root-ssot"
    except FileNotFoundError:
        out["why"] = f"沒有 {def_rel(CAPSULE_POLICY_PATH)}（VRN-1 單獨複製出去時就是這樣，照跑）"
    except ValueError as error:
        out["why"] = f"{def_rel(CAPSULE_POLICY_PATH)} 不是合法 JSON：{error}"
    return out


WRAPUP_RULE = "輸出驗證無誤才算收尾完成"


# [VRN-ID] VRN-MAN001-FNC117 · LOGIC
def def_wrapup(counts: Dict[str, Any], ui_rows: Optional[List[Dict[str, Any]]] = None, chain_rc: int = 0) -> Dict[str, Any]:
    """操作員 2026-10-17「輸出的結果應規定驗證無誤後才算是真正的收尾完成」—— 這是那條規則本身。

    三件全過才算完成：
      一、閘沒有 FAIL
      二、P20 UI 對得上（HTML 的結論、計數、列數、連結與 JSON 一致）
      三、鏈上游沒有硬失敗
    **跑完不等於跑對，產得出檔案也不等於那份檔案能拿去用。** 判準只有這一份，
    console 的收尾那一行與交接 capsule 的抬頭都讀它，不會出現「螢幕上說完成、
    檔案裡說沒事」這種兩套說法。
    """
    ui_bad = [r for r in (ui_rows or []) if r.get("status") == "FAIL"]
    blockers: List[str] = []
    if counts.get("FAIL"):
        blockers.append(f"閘 FAIL {counts['FAIL']}")
    if ui_bad:
        blockers.append("UI 驗證對不上：" + "、".join(r["item"] for r in ui_bad))
    if chain_rc:
        blockers.append(f"鏈上游結束碼 {chain_rc}")
    return {"done": not blockers, "blockers": blockers, "rule": WRAPUP_RULE}


# [VRN-ID] VRN-MAN001-FNC114 · IO
def def_write_capsule(paste_path: Path, cap: Dict[str, Any], wrap: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """把貼回檔切成放得進 VCGC 預算的一份（REFERENCE_FIRST_DELTA_ONLY）。

    **內容不是另外算的**，是 def_write_pasteback 那份原文按段切 —— 一份內容、一個預算來源，
    不是第二個摘要器。協定的兩件事都照做：
      reference first  開頭就說完整檔在哪，拿到的人要細節自己去讀，不用再問一輪
      delta only       只帶放得下的整段，被留下的段落逐一點名（哪一段、多少字），不偷偷截斷
    """
    text = paste_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    heads = [i for i, ln in enumerate(lines) if ln.startswith("== ")] or [len(lines)]
    blocks = [("前言", "".join(lines[:heads[0]]))]
    for n, start in enumerate(heads):
        stop = heads[n + 1] if n + 1 < len(heads) else len(lines)
        blocks.append((lines[start].strip().strip("= ").split("：")[0], "".join(lines[start:stop])))

    # 抬頭第一行就講收尾過了沒 —— 一份看起來乾淨的交接摘要，底下卻是沒驗過的結果，
    # 比沒有摘要更危險：拿到的人會直接當它可以用。
    done = (wrap or {}).get("done")
    head = (f"[收尾] 完成 · {WRAPUP_RULE}\n" if done else
            f"[收尾] **未完成** · {WRAPUP_RULE} —— 卡在："
            + "；".join((wrap or {}).get("blockers") or ["還沒驗"])
            + "\n[注意] 以下是現況，不是可以交出去的結果。先把上面那幾項弄綠再談收尾。\n"
            if wrap is not None else "")
    ref = (head
           + f"[完整檔] {paste_path}（{len(text)} 字）\n"
           f"[協定] {cap['protocol']} · 預算 {cap['max_chars']} 字 / {cap['max_items']} 項（來源 {cap['source']}）\n"
           "[讀法] 下面是放得進預算的整段；要被省掉的段落，照上面那個路徑讀，不要再要一次全文。\n\n")
    # 省略那一行本身也要算進預算（Codex PR #55 P2：實測 600 字上限寫出 643 字）。
    # 它多長取決於省掉哪幾段，而省掉哪幾段又取決於留幾段 —— 所以從多到少試到整份放得下為止，
    # 不是先挑完再把尾巴硬塞進去。max_items 擋下的段落一樣要點名：省略不能是默默消失。
    # [VRN-ID] VRN-MAN001-FNC115 · LOGIC
    def shape(keep_n):
        body = "".join(b for _name, b in blocks[:keep_n])
        left = [f"{name}（{len(b)} 字）" for name, b in blocks[keep_n:]]
        tail = ("\n[省略] " + "、".join(left) + " —— 在完整檔裡，按段要。\n") if left else ""
        return body, left, tail

    keep_n = min(len(blocks), cap["max_items"])
    while True:
        body, left, tail = shape(keep_n)
        if len(ref) + len(body) + len(tail) <= cap["max_chars"] or keep_n == 0:
            break
        keep_n -= 1

    doc = ref + body + tail
    out = paste_path.with_name("VRN_PasteBack_Capsule_v0100.txt")
    def_write_atomic(out, doc)
    # chars 回報檔案的**實際長度**，不是選段時算的帳 —— 報一個跟檔案不一樣的數字是另一種假綠燈。
    return {"path": str(out), "chars": len(doc), "kept": keep_n, "left": left,
            "over": max(0, len(doc) - cap["max_chars"])}


# [VRN-ID] VRN-MAN001-CLS003 · CLASS
class _TagBalance(HTMLParser):
    """只數開合標籤；void 元素不入堆疊。解析不過會丟 HTMLParseError 以外的例外由呼叫端接。"""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    # [VRN-ID] VRN-MAN001-FNC110 · INIT
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[str] = []
        self.bad: List[str] = []
        self.rows = 0
        self.hrefs: List[str] = []
        self.headline = ""          # <p class="v"> 的文字：結論與計數就印在這一格
        self._depth_v = 0
        # 2026-10-18 驗收表進來以後，整份文件的 <tr> 不再只有閘列。只數 <table id="gates">
        # 裡面那些 —— 「閘列數與 JSON 相符」比的本來就是閘表格，數到別張表就不是在比同一種量。
        self._in_gates = 0

    # [VRN-ID] VRN-MAN001-FNC111 · LOGIC
    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table" and any(k == "id" and v == "gates" for k, v in attrs):
            self._in_gates = len(self.stack) + 1
        if tag == "tr" and self._in_gates:
            self.rows += 1
        if tag == "a":
            self.hrefs += [v for k, v in attrs if k == "href" and v]
        if self._depth_v or any(k == "class" and "v" in (v or "").split() for k, v in attrs):
            self._depth_v += 1
        if tag not in self.VOID:
            self.stack.append(tag)

    # [VRN-ID] VRN-MAN001-FNC116 · LOGIC
    def handle_data(self, data: str) -> None:
        if self._depth_v:
            self.headline += data

    # [VRN-ID] VRN-MAN001-FNC112 · LOGIC
    def handle_endtag(self, tag: str) -> None:
        if tag in self.VOID:
            return
        if self._depth_v:
            self._depth_v -= 1
        if not self.stack:
            self.bad.append(f"多出來的 </{tag}>")
        elif self.stack[-1] != tag:
            self.bad.append(f"</{tag}> 對不上還開著的 <{self.stack[-1]}>")
        else:
            self.stack.pop()
        if tag == "table" and self._in_gates and len(self.stack) < self._in_gates:
            self._in_gates = 0


# [VRN-ID] VRN-MAN001-FNC113 · GATE
def def_gate_ui_html(json_path: Path, html_path: Path) -> List[Dict[str, Any]]:
    """HTML U/I 的收尾驗證：**存在不算數，要跟 JSON 對得上才算數**。

    比的是同一種量：HTML 是 JSON 那份 payload 畫出來的，所以結論、計數、列數都該一致。
    任何一項對不上就是 FAIL —— 報告長得像一份完整報告、數字卻是另一回事，比沒有報告更糟。
    """
    gate = "P20 UI"
    if not html_path.is_file():
        return [def_row(gate, "HTML 報告", "FAIL", f"沒有寫出來：{html_path}")]
    doc = html_path.read_text(encoding="utf-8", errors="replace")
    payload = def_read_json(json_path) if json_path.is_file() else {}
    if not payload:
        return [def_row(gate, "HTML 報告", "FAIL", f"對不了：讀不到 {json_path.name}（HTML 是它畫出來的）")]

    rows = [def_row(gate, "HTML 報告", "PASS", f"{len(doc)} 字 · {html_path.name}")]

    parser = _TagBalance()
    try:
        parser.feed(doc)
        parser.close()
    except Exception as error:  # noqa: BLE001
        return rows[:0] + [def_row(gate, "標籤解析", "FAIL", f"{error.__class__.__name__}: {error}")]
    unclosed = [t for t in parser.stack if t not in ("html", "body")]
    rows.append(def_row(gate, "標籤開合", "PASS" if not parser.bad and not unclosed else "FAIL",
                        "開合相符" if not parser.bad and not unclosed
                        else " · ".join(parser.bad[:4] + [f"沒收尾的 <{t}>" for t in unclosed[:4]])))

    # 比的是**主標那一格**（<p class="v">），不是整份文件的 substring：文件裡別處也寫著同一個
    # 結論（迴圈摘要、列的說明），拿整份比，主標寫錯了照樣綠燈（Codex PR #55 P2，實測重現）。
    head = " ".join(parser.headline.split())
    verdict = str(payload.get("verdict", ""))
    said = head.split("·")[0].strip()
    rows.append(def_row(gate, "結論與 JSON 相符", "PASS" if verdict and said == verdict else "FAIL",
                        f"{verdict}" if verdict and said == verdict
                        else f"JSON 說 {verdict or '(沒有)'}，主標那一格寫 {said or '(空的)'}"))

    counts = payload.get("counts") or {}
    missing = [f"{k} {v}" for k, v in counts.items() if f"{k} {v}" not in head]
    rows.append(def_row(gate, "計數與 JSON 相符", "PASS" if counts and not missing else "FAIL",
                        " · ".join(f"{k} {v}" for k, v in counts.items()) if not missing
                        else "主標那一格對不上：" + "、".join(missing)))

    want = len(payload.get("rows") or [])
    # 閘列表有一列表頭；迴圈那一段不畫 <tr>，所以列數應該剛好是 rows + 1
    rows.append(def_row(gate, "閘列數與 JSON 相符", "PASS" if parser.rows == want + 1 else "FAIL",
                        f"{want} 列 + 表頭" if parser.rows == want + 1
                        else f"JSON {want} 列，HTML 數到 {parser.rows} 個 <tr>（含表頭）"))

    # 2026-10-20：代號紀錄畫進 HTML 了，就要跟它的來源對得上 —— 畫了一張表、數字卻是另一回事，
    # 和「結論對不上」同一種危險。比兩件事：份數（一份個股一列）與 DERIVED 幾格（這一輪修的就是它）。
    recs = sorted(html_path.parent.glob("autotest/round*/titletrim/vrn_ticker_record.json"))
    if recs and '<tbody class="rec">' in doc:
        source = def_read_json(recs[-1]) or []
        seg = doc.split('<tbody class="rec">', 1)[1].split("</tbody>", 1)[0]
        got_n = seg.count("<tr>")
        want_d = sum(1 for r in source for k, v in r.items() if k.endswith("_state") and v == "DERIVED")
        got_d = seg.count("推")
        good = got_n == len(source) and got_d == want_d
        rows.append(def_row(gate, "代號紀錄與 G20 相符", "PASS" if good else "FAIL",
                            f"{got_n} 份 · 推（DERIVED）{got_d} 格" if good
                            else f"G20 {len(source)} 份／DERIVED {want_d} 格，HTML 數到 {got_n} 份／推 {got_d} 格"))

    # 連結要驗 HTML 裡真正寫的那個 href，不是拿檔名去猜 —— 猜的話壞連結照樣綠燈。
    dead = [h for h in parser.hrefs if not (html_path.parent / h).is_file()]
    if parser.hrefs:
        rows.append(def_row(gate, f"連結連得到（{len(parser.hrefs)} 個）", "PASS" if not dead else "FAIL",
                            " · ".join(parser.hrefs) if not dead
                            else "點不到：" + "、".join(f"{h}（相對 {html_path.parent.name}/）" for h in dead)))
    return rows


# =============================================================================
# 09. 指令
# =============================================================================
# [VRN-ID] VRN-MAN001-FNC069 · ENTRY
def selftest(accel_home: str = "", quiet: bool = False) -> Tuple[int, List[Dict[str, Any]]]:
    """Offline: SSOT books, registry, accelerator, oracle smoke. No samples, no network, no writes."""
    rows: List[Dict[str, Any]] = []
    rows += def_gate_accel(accel_home)          # 先掛加速器，後面每個動作才走得到 accel_map（P09 照實記）
    rows += def_gate_env()[:2]
    rows += def_check_ssot()
    rows += def_check_registry()
    rows += def_gate_oracle()
    rows += def_gate_books()
    rows += def_gate_regions(fixtures=True)
    rows += def_gate_titletrim()
    rows += def_gate_focus()
    rows += def_gate_astid()
    rows += def_gate_engine_lock()
    rows += def_gate_accel_coverage()
    if not quiet:
        for r in rows:
            print(f"  [{r['status']:4}] {r['gate']} · {r['item']}" + (f" · {r['detail']}" if r.get("detail") else ""))
        print(f"[SELFTEST] {def_verdict(rows)} · " + " ".join(f"{k}={v}" for k, v in def_counts(rows).items()))
    return (1 if def_counts(rows)["FAIL"] else 0), rows


# [VRN-ID] VRN-MAN001-FNC101 · LOGIC
def def_open_run_cache(args: argparse.Namespace) -> Tuple[Any, List[Dict[str, Any]]]:
    """P00: what this machine can take (CPU, memory, TEMP) and the run's TEMP cache (one for the whole run, one lock)."""
    try:
        rc = def_load_module("VRN_Main_runcache", ENGINE_FILES["runcache"])
    except Exception as error:  # noqa: BLE001
        return None, [def_row("P00 RESOURCES", "VRN_RunCache", "WARN", f"{error.__class__.__name__}: {error}"[:200] + "：不用快取，照常全部重跑")]
    cache = rc.cache_open(getattr(args, "cache_home", ""), enabled=not getattr(args, "no_cache", False))
    res = rc.cache_resources(cache.home)
    rows = [def_row("P00 RESOURCES", f"CPU {res['cpu']} 核 · 記憶體可用 {res['mem_avail_gb']}/{res['mem_total_gb']} GB · TEMP 剩 {res['temp_free_gb']} GB",
                    "WARN" if res["mem_avail_gb"] and res["mem_avail_gb"] < 2 else "PASS",
                    f"子行程 {res['workers']} 支 · 快取 {res['cache_gb']}/{res['budget_gb']} GB · {res['why']}"),
            def_row("P00 CACHE", "TEMP 快取：輸入、引擎、冊、套件都沒變的步驟沿用上次結果" if cache.enabled else "TEMP 快取：這一輪不用",
                    "PASS" if cache.enabled else "WARN", f"{cache.home}（{cache.why}）" if cache.enabled else cache.why)]
    print(f"[RESOURCES] CPU {res['cpu']} 核 · 記憶體 {res['mem_avail_gb']}/{res['mem_total_gb']} GB 可用 · TEMP 剩 {res['temp_free_gb']} GB · "
          f"子行程 {res['workers']} · 快取 {res['cache_gb']}/{res['budget_gb']} GB" + ("" if cache.enabled else f" · 不用快取：{cache.why}"))
    return cache, rows


# [VRN-ID] VRN-MAN001-FNC102 · LOGIC
def def_close_run_cache(cache: Any, loop_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """After the loop: the cache's hits and the seconds saved; entries that inputs replaced are deleted (logged)."""
    if cache is None:
        return []
    summary = cache.cache_summary()
    pruned = cache.cache_close()
    if not summary.get("enabled"):
        return []
    steps = summary.get("steps") or {}
    detail = " · ".join(f"{k} 命中 {v.get('hit', 0)}／重讀 {v.get('miss', 0)}" for k, v in sorted(steps.items()) if k != "sample_sha")
    sha = steps.get("sample_sha") or {}
    timing = loop_report.get("timing") or []
    return [def_row("P20 CACHE", f"TEMP 快取：省約 {summary.get('saved_seconds', 0)} 秒" + (f" · 樣本 SHA 重讀 {sha.get('reread', 0)}/{sha.get('files', 0)} 檔" if sha else ""),
                    "PASS", f"{detail} · 刪掉用不到的 {pruned.get('deleted', 0)} 筆（{pruned.get('mb', 0)} MB）· {summary.get('home')}"),
            def_row("P20 TIME", "各閘秒數（最慢的在前）", "PASS", " · ".join(f"{r['gate']} {r['seconds']}" for r in timing[:12]) or "沒有計時")]


# [VRN-ID] VRN-MAN001-FNC103 · LOGIC
def def_run_steps_side_by_side(steps: List[Tuple[str, Callable[[], List[Dict[str, Any]]]]]) -> List[Dict[str, Any]]:
    """The independent pre-steps run side by side (threads: they read files, import libraries and hash; none opens a PDF);
    their rows come back in the listed order, so the report reads the same as before.  A step that raises becomes a FAIL row."""
    started = time.perf_counter()
    real_out, real_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = def_ThreadQuietStream(real_out), def_ThreadQuietStream(real_err)
    results: Dict[int, List[Dict[str, Any]]] = {}
    seconds: Dict[int, float] = {}

    # [VRN-ID] VRN-MAN001-FNC104 · LOGIC
    def run(i: int) -> None:
        t0 = time.perf_counter()
        try:
            results[i] = list(steps[i][1]())
        except Exception as error:  # noqa: BLE001
            results[i] = [def_row("P00 STEP", steps[i][0], "FAIL", f"{error.__class__.__name__}: {error}"[:300])]
        seconds[i] = time.perf_counter() - t0
        print(f"  [{len(seconds)}/{len(steps)}] {steps[i][0]} · {round(seconds[i], 1)} 秒", file=real_out, flush=True)
    try:
        with ThreadPoolExecutor(max_workers=len(steps)) as pool:
            list(pool.map(run, range(len(steps))))
    finally:
        sys.stdout, sys.stderr = real_out, real_err
    wall = time.perf_counter() - started
    def_accel_note("P00 六個獨立步驟同時跑（執行緒；不開 PDF）", "thread_pool", len(steps), wall,
                   f"一條接一條要 {round(sum(seconds.values()), 1)} 秒，同時跑 {round(wall, 1)} 秒")
    out: List[Dict[str, Any]] = []
    for i in range(len(steps)):
        out += results.get(i, [])
    return out


# [VRN-ID] VRN-MAN001-FNC107 · ENTRY
def def_cmd_all(args):
    """操作員 2026-10-16「把上述所有指令整合為一」：build → lock → check → run，一條鏈。

    順序不是隨便排的，是相依關係：
      build  先注入 AST 編號、重建三本冊與註冊冊 —— 不先做，新函式沒有編號，lock 會算錯指紋
      lock   跑 14 組已知答案，全過的引擎與冊才記指紋 —— 不先做，改過的引擎在 run 的 G18 會紅
      check  驗 ssot 與註冊冊沒漂移
      run    完整實測 + 報告 + 驗證無誤自動跳 UI

    **第一個硬失敗就停**，不往下跑：鏈上游錯了還往下跑，只會得到一份看起來很完整、
    其實建立在壞地基上的報告。check 的 AMBER（只有 WARN）不算硬失敗，照跑。
    引擎與冊都沒動過時 `--skip-seal` 可以跳過前三步。

    加速器在第一步之前就真的 import 一次，不是只看檔案在不在：
      一、檔案在不等於掛得上（壞掉的加速器會印「掛上」，是假綠燈）
      二、掛上之後 build／lock 的逐檔掃描（AST 注入、REGEX 冊、註冊冊 SHA）才吃得到 accel_map；
          只在 run 裡掛，前三步整段走 stdlib 執行緒池
    加速器在第一步之前就 activate(apply_limits=True)（操作員 2026-10-18「指令第一步為提高 CPU/DRAM 效能」）：
    執行緒預算是加速器自己的機制，本倉不另做一套（補一個＝九頭龍）。本來只掛載、不 activate，
    等到 run 的 P04 才套 —— 那表示 build／lock／check 這前三步整段沒有預算。現在提前套用，
    但回報還是只有 P04 那一列：activate 一個行程只跑一次，P04 讀的是同一份 ACCEL_STATE。
    加速器不在時這一步沒有東西可提高，照實印出來，不假裝有做。
    """
    st = def_load_accelerator(getattr(args, "accel_home", ""), activate=True)
    if st["loaded"]:
        # 沒有預算就不要說「已套用」—— 這一行是操作員唯一看得到的憑據，假綠燈比沒有燈更糟。
        budget = (st["activated"] or {}).get("thread_budget")
        applied = f"執行緒預算 {budget} 已套用" if budget else "這支加速器沒有回報執行緒預算"
        print(f"[ALL] 加速器：掛上 · {st['canonical'] or ACCEL_ENTRY} · 來源 {st['source']} · {st['home']}"
              f" —— {applied}，從這裡起 build／lock 的逐檔掃描也走 accel_map")
    else:
        print("[ALL] 加速器：沒掛上 · 退回 stdlib 執行緒池（判讀不受影響）· "
              f"{st['error'] or '沒有找到 ' + ACCEL_ENTRY}（VRN_Main_v0100.py accel 看找過哪裡）")
    steps = [] if getattr(args, "skip_seal", False) else [
        ("build", "注入編號、重建冊與註冊冊", def_cmd_build),
        ("lock", "已知答案逐組證明、記指紋", lambda: def_cmd_lock(argparse.Namespace(
            status=False, unlock="", part="", lock_home=getattr(args, "lock_home", "")))),
        ("check", "驗 ssot 與註冊冊沒漂移", lambda: _all_check()),
    ]
    for i, (name, why, fn) in enumerate(steps, 1):
        print(f"[ALL {i}/{len(steps) + 1}] {name} · {why}")
        rc = fn()
        if rc:
            print(f"[ALL] {name} 結束碼 {rc} —— 鏈停在這裡，不往下跑（地基沒好，後面那份報告不算數）")
            # 這條路徑也要印收尾那一行：規則少印一次，就等於多了一個「沒說不算數」的出口。
            stop = def_wrapup({"FAIL": 0}, None, chain_rc=rc)
            print(f"[收尾] 未完成 · {stop['rule']} —— 卡在：{name} " + "；".join(stop["blockers"]))
            return rc
    print(f"[ALL {len(steps) + 1}/{len(steps) + 1}] run · 完整實測 + 報告")
    return def_cmd_run(args)


# [VRN-ID] VRN-MAN001-FNC108 · LOGIC
def _all_check():
    """check 的同一段判斷，回結束碼。只有 FAIL 算硬失敗，AMBER（WARN）照跑。"""
    rows = def_check_ssot() + def_check_registry() + def_gate_astid() + def_gate_engine_lock() + def_gate_tool_manifest()
    for r in rows:
        print(f"  [{r['status']:4}] {r['gate']} · {r['item']}" + (f" · {r['detail']}" if r.get("detail") else ""))
    print(f"[CHECK] {def_verdict(rows)} · " + " ".join(f"{k}={v}" for k, v in def_counts(rows).items()))
    return 1 if def_counts(rows)["FAIL"] else 0


# [VRN-ID] VRN-MAN001-FNC139 · GATE
def def_gate_tool_manifest() -> List[Dict[str, Any]]:
    """2026-10-20：借出工具冊（ssot/VRN_ToolManifest_v0100.json）上每支工具的 sha256 要和檔相同 —— 不同 = 別的系統會拒借（FAIL：跑 build 重寫）。"""
    try:
        tb = def_load_module("VRN_Main_toolbridge", ENGINE_FILES["toolbridge"])
        issues = tb.check_manifest()
    except Exception as error:  # noqa: BLE001
        return [def_row("P25 TOOLS", "借出工具冊", "FAIL", f"{error.__class__.__name__}: {error}"[:200])]
    if issues:
        return [def_row("P25 TOOLS", "借出工具冊", "FAIL", "；".join(issues)[:300])]
    return [def_row("P25 TOOLS", "借出工具冊", "PASS", "、".join(o["id"] for o in tb.manifest()["offers"]) + " · sha256 和檔相同（別的系統借之前會核對）")]


# [VRN-ID] VRN-MAN001-FNC070 · ENTRY
def def_cmd_run(args: argparse.Namespace) -> int:
    samples = args.samples
    if not samples and os.name == "nt" and Path(DEFAULT_SAMPLES_WINDOWS).is_dir() and not args.synthetic:
        samples = DEFAULT_SAMPLES_WINDOWS
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"VRN_Main_{time.strftime('%Y%m%dT%H%M%S')}"
    out.mkdir(parents=True, exist_ok=True)
    temp_mod = None
    temp_opened: Dict[str, Any] = {}
    try:
        temp_mod = def_load_module("VRN_Main_tempstore", ENGINE_FILES["tempstore"])
        temp_opened = {"run": str(temp_mod.open_run("VRN_Main")), "swept": list(temp_mod.LAST_SWEEP)}
    except Exception as error:  # noqa: BLE001
        temp_opened = {"error": f"{error.__class__.__name__}: {error}"[:200]}
    try:
        return def_cmd_run_body(args, samples, out, temp_opened)
    finally:
        if temp_mod is not None and temp_opened.get("run"):
            temp_mod.close_run()


# [VRN-ID] VRN-MAN001-FNC071 · ENTRY
def def_cmd_run_body(args: argparse.Namespace, samples: str, out: Path, temp_opened: Dict[str, Any]) -> int:
    total = 7
    rows: List[Dict[str, Any]] = []
    # Codex PR #72 P2：空間閘本來只在收尾時跑（和 P10 其他列擺在一起），也就是 AutoTestLoop
    # 把 TEMP 寫滿**之後**。一道防磁碟耗盡的閘跑在耗盡之後，等於沒有這道閘 ——
    # 而這正是這一輪一直在抓的那個老毛病：閘跑的那一刻，和真正出事的那一刻，不是同一刻。
    # 所以 FAIL 要在動手之前就擋下來。收尾那一次留著，但它只是回報，不是防線。
    short = [r for r in def_gate_temp_space(temp_opened.get("run") or str(out)) if r["status"] == "FAIL"]
    if short:
        for r in short:
            print(f"[FAIL] {r['gate']} · {r['item']} · {r['detail']}")
        print("[STOP] 動手之前就擋下來：TEMP 不夠，這一輪的中介檔寫不完，會留下半份檔案。"
              "清掉 TEMP 或用 --out 指到別的磁碟再跑。")
        return 1
    def_progress(1, total, "P04 加速器（先接上，後面每支引擎的橋都吃得到）· P00 CPU／記憶體／TEMP")
    rows += def_gate_accel(args.accel_home, activate=True)
    cache, res_rows = def_open_run_cache(args)
    rows += res_rows
    def_progress(2, total, "六個獨立步驟同時跑：P01 環境 · P02 SSOT 三本冊 · P03 註冊冊＋P11 AST 編號 · P16 引擎鎖 · P07 樣本 SHA · P08／P13／P14 冊與資料庫")
    evidence_box: Dict[str, Any] = {}

    # [VRN-ID] VRN-MAN001-FNC105 · LOGIC
    def samples_step() -> List[Dict[str, Any]]:
        got_rows, got = def_gate_samples("" if args.synthetic else samples, cache)
        evidence_box["evidence"] = got
        return got_rows
    steps = [("P01 環境", def_gate_env), ("P02 SSOT 三本冊", def_check_ssot),
             ("P03 註冊冊 · P11 AST 編號", lambda: def_check_registry() + def_gate_astid()), ("P16 引擎鎖", def_gate_engine_lock),
             ("P07 樣本", samples_step), ("P08 收來的冊 · P14 本機資料庫 · P13 本機 SSOT", lambda: def_gate_books() + def_gate_localdb() + def_gate_local_ssot(out))]
    rows += def_run_steps_side_by_side(steps)
    evidence = evidence_box.get("evidence") or {}
    if evidence:
        def_write_json(out / "VRN_Samples_Evidence_v0100.json", evidence)
    rows += def_gate_regions()                                       # P15 builds PDFs with PyMuPDF: after the side-by-side steps, alone
    def_progress(6, total, "VRN_AutoTestLoop（G01–G19，逐檔進度如下）")
    loop_json = out / "autotest" / "VRN_AutoTest_Report.json"
    loop_html = out / "autotest" / "VRN_AutoTest_Report.html"
    loop_args = ["--out", str(out / "autotest"), "--rounds", str(args.rounds), "--json", str(loop_json), "--html", str(loop_html)]
    if args.synthetic or not evidence:
        loop_args.append("--synthetic")
    else:
        loop_args += ["--samples", samples]
    if args.truth:
        loop_args += ["--truth", def_load_truth_file(args.truth)]
    if args.no_audit:
        loop_args.append("--no-audit")
    if args.limit:
        loop_args += ["--limit", str(args.limit)]
    if getattr(args, "lock_home", ""):
        loop_args += ["--lock-home", args.lock_home]
    if getattr(args, "no_focus", False):
        loop_args.append("--no-focus")
    if not (cache is not None and cache.enabled):
        loop_args.append("--no-cache")
    try:
        loop = def_load_module("VRN_Main_autotest", ENGINE_FILES["autotest"])
        loop.SHARED_CACHE = cache if (cache is not None and cache.enabled) else None
        loop_rc = int(loop.def_main(loop_args))
    except SystemExit as stop:
        loop_rc = int(stop.code or 0)
    except BaseException as error:  # noqa: BLE001
        loop_rc = 1
        rows.append(def_row("G00 AUTOTEST", "VRN_AutoTestLoop", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    autotest: Dict[str, Any] = {"rc": loop_rc}
    if loop_json.is_file():
        rep = def_read_json(loop_json)
        autotest.update(loop=rep.get("loop", ""), verdict=rep.get("verdict"), counts=rep.get("counts"),
                        json=str(loop_json), html=str(loop_html), rounds=len(rep.get("rounds", [])))
        rows.append(def_row("G00 AUTOTEST", f"{rep.get('loop', '')}（{len(rep.get('rounds', []))} 輪）",
                            "FAIL" if loop_rc == 1 else ("WARN" if rep.get("verdict") == "AMBER" else "PASS"),
                            " · ".join(f"{k} {v}" for k, v in (rep.get("counts") or {}).items())))
        frames = rep.get("dataframes") or {}
        if frames:
            autotest["dataframes"] = frames
            lamps = [v.get("lamp") for v in (frames.get("tables") or {}).values()]
            rows.append(def_row("G00 DATAFRAME", f"輸出 DataFrame {len(lamps)} 張（照 VRN_Output_Header_SSOT 驗表頭）：" + " · ".join(
                f"{k} {lamps.count(k)}" for k in sorted(set(lamps))), {"GREEN": "PASS", "RED": "FAIL"}.get(frames.get("verdict"), "WARN"),
                f"{frames.get('folder')}（每張表 .parquet + .csv）· {frames.get('path')}"))
        focus = rep.get("focus") or {}
        if focus.get("counts"):
            autotest["focus"] = focus
            fc = focus["counts"]
            rows.append(def_row("G00 FOCUS", f"只處理個股 {fc.get('stock', 0)}/{fc.get('files', 0)} 檔的檔名、第一頁、年度財報頁：頁 {fc.get('pages_kept', 0)}/"
                                f"{fc.get('pages_total', 0)}（年度財報頁 {fc.get('annual_pages', 0)}）", "PASS" if fc.get("originals_untouched") else "FAIL",
                                f"非個股 {fc.get('excluded', 0)} 檔不處理 · 清單 {(focus.get('manifest') or {}).get('csv', '')}"))
        trimmed = rep.get("titletrim") or {}
        if trimmed:
            autotest["titletrim"] = trimmed
            st = trimmed.get("states") or {}
            rows.append(def_row("G00 TITLETRIM", f"個股 {trimmed.get('stock', 0)}/{trimmed.get('files', 0)} 檔：標題、首頁、年度財報頁 TRIM 後分拆 · "
                                f"VERIFIED {st.get('VERIFIED', 0)}/{sum(st.values())}",
                                "FAIL" if trimmed.get("trim_loss") or trimmed.get("trim_regression") else "PASS",
                                " · ".join(f"{k} {v}" for k, v in sorted(st.items())) + f" · {trimmed.get('folder')}"))
        locked = rep.get("lock") or {}
        if locked:
            autotest["lock"] = locked
            c = locked.get("counts") or {}
            fix_rows_n = (locked.get("fix_list") or {}).get("rows", 0)
            # 清單是空的就沒有東西能擋（fix_priority 這時是 {}，問門檻只會拿到「算不出來」）；
            # 有列才去問，而「有列但沒有優先序細目」照實算不出來，維持 WARN。
            fix_block = 0 if not fix_rows_n else def_fix_rule().def_fix_blocking_from_counts(locked.get("fix_priority"))
            rows.append(def_row("G00 LOCK", f"鎖：NEW {c.get('NEW', 0)} · HELD {c.get('HELD', 0)} · BROKEN {c.get('BROKEN', 0)} · 待修 "
                                f"{fix_rows_n} 項"
                                + (f"（擋住收尾 {fix_block} 項）" if fix_block is not None else "（擋幾項算不出來：這份報告沒有優先序細目）"),
                                "FAIL" if c.get("BROKEN") else ("PASS" if fix_block == 0 else "WARN"),
                                f"帳本 {locked.get('ledger')} · 待修 {(locked.get('fix_list') or {}).get('txt')}"
                                + (" · 優先 3 鎖不住但不是讀錯，不擋收尾（同 P21 驗收）" if fix_block == 0 and fix_rows_n else "")))
        verified = rep.get("verified") or {}
        if verified.get("counts"):
            autotest["verified"] = verified
            vc = verified["counts"]
            vf = vc["financial"]
            rej = vf["rejected"] + vc["annual"]["rejected"] + vc["record"]["rejected_fields"] + vc["summary"]["rejected"]
            rows.append(def_row("G00 VERIFIED", f"驗證過的輸出（每一筆回原檔逐欄證明 · 證不出來不進輸出）：年度數據 {vf['verified'] + vf['corrected']}/{vf['in']}"
                                f"（自動修正 {vf['corrected']}）· 年度財報格 {vc['annual']['verified']}/{vc['annual']['in']} · 代號紀錄 "
                                f"{vc['record']['verified_fields']}/{vc['record']['in_fields']} 欄 · 一標題四重點 {vc['summary']['verified']}",
                                "PASS" if not rej else "WARN",
                                f"{verified.get('html')} · 剔除 {rej}" + ("：" + "；".join(f"{k} {v}" for k, v in list((verified.get('reasons') or {}).items())[:3]) if rej else "")))
        borrowed = rep.get("borrow") or {}
        if borrowed:
            autotest["borrow"] = borrowed
            got_b = [r for r in borrowed.get("rows") or [] if r.get("state") == "BORROWED"]
            rows.append(def_row("G00 BORROW", f"借用工具（VRN-2 的工具冊 · 逐檔核對 sha256）：借到 {len(got_b)}/{len(borrowed.get('rows') or [])} 支"
                                + (" · " + "、".join(r["id"] for r in got_b) if got_b else ""),
                                "PASS" if borrowed.get("rows") and len(got_b) == len(borrowed["rows"]) else "WARN",
                                str(borrowed.get("note") or "") + "".join(f" · {r['id']} {r['state']}" for r in borrowed.get("rows") or [] if r.get("state") != "BORROWED")))
        pivot = rep.get("pivot") or {}
        if pivot.get("counts"):
            autotest["pivot"] = pivot
            pc = pivot["counts"]
            rows.append(def_row("G00 PIVOT", f"PIVOT 資料庫（驗證過的年度數據 → 事實表 → 年度 / 季度 PIVOT）：事實 {pc['kept']}/{pc['facts']} · 年度 {pc['pivot_report_annual']} 列 · "
                                f"季度 {pc['pivot_report_quarterly']} 列 · 衝突 {pc['conflicts']}",
                                "PASS" if not pc["conflicts"] and (pivot.get("duckdb_check") or {}).get("pivot_check", "OK") == "OK" else "WARN",
                                f"{pivot.get('html')} · {Path(pivot.get('sqlite') or '').name}" + (f" · {Path(pivot['duckdb']).name}" if pivot.get("duckdb") else "")))
        matrix = (rep.get("regions") or {}).get("matrix") or {}
        if matrix:
            autotest["matrix"] = matrix
            rows.append(def_row("G00 MATRIX", "驗證矩陣（每檔一列：引擎原值 · 冊上驗證 · 版面 · 還原 · 加減除驗算 · 目標價與評價）", "PASS",
                                f"{matrix.get('html')} · {Path(matrix.get('csv', '')).name} · {Path(matrix.get('identities_csv', '')).name}"))
    elif loop_rc not in (0,):
        rows.append(def_row("G00 AUTOTEST", "VRN_AutoTestLoop", "FAIL" if loop_rc == 1 else "WARN", f"rc={loop_rc}，沒有報告"))
    loop_cov = (def_read_json(loop_json).get("accel_coverage") if loop_json.is_file() else None) or []
    rows += def_gate_accel_coverage(loop_cov, with_engines=True)
    temp_mod = sys.modules.get("VRN_Main_tempstore")
    rows += def_gate_temp(temp_opened, temp_mod.status() if temp_mod is not None and temp_opened.get("run") else {})
    rows += def_close_run_cache(cache, def_read_json(loop_json) if loop_json.is_file() else {})
    rows += def_gate_ocr()
    accept = def_acceptance(out)
    rows += def_gate_acceptance(accept)
    time_scan = def_time_scan(out)
    rows += def_gate_time_format(time_scan)
    cross_scan = def_cross_source_scan(out)
    rows += def_gate_cross_source(cross_scan)
    def_progress(7, total, "報告")
    payload = {"main": MAIN_NAME, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "samples": samples if evidence else "",
               "verdict": def_verdict(rows), "counts": def_counts(rows), "rows": rows, "accelerator": dict(ACCEL_STATE),
               "autotest": autotest, "out": str(out), "accel_coverage": ACCEL_COVERAGE + loop_cov, "temp": temp_opened,
               "acceptance": accept, "time_format": time_scan, "cross_source": cross_scan}
    json_path, html_path = def_write_report(out, payload)
    print(f"[DONE] {payload['verdict']} · " + " ".join(f"{k}={v}" for k, v in payload["counts"].items()))
    print(f"[REPORT] {html_path}")
    print(f"[JSON]   {json_path}")
    # 收尾目標是「HTML U/I 輸出驗證無誤」—— 寫出來不算數，要跟 JSON 對得上才算數。
    ui_rows = def_gate_ui_html(json_path, html_path)
    ui_bad = [r for r in ui_rows if r["status"] == "FAIL"]
    for r in (ui_bad or ui_rows):
        print(f"[UI-VERIFY] [{r['status']:4}] {r['item']} · {r['detail']}")
    print(f"[UI-VERIFY] {'對上了' if not ui_bad else '對不上 ' + str(len(ui_bad)) + ' 項'} · {len(ui_rows)} 項檢查")
    wrap = def_wrapup(payload["counts"], ui_rows)
    # 2026-10-19：收尾判決本來只活在 console 那一行與交接 capsule 裡，報告 JSON 讀不到它。
    # 下游要判斷「這一輪能不能拿去用」（例如 sync 要不要上傳）時，就只能自己再判一次 ——
    # 那是同一個判斷長出第二顆頭。改成把 def_wrapup 的結果原樣寫回 JSON，只有一份判準。
    # 補寫在 UI 驗證之後是刻意的：wrap 要等 ui_rows 才算得出來。P20 UI 比的是結論、計數、
    # 列數與連結（見 def_gate_ui_html），多一個頂層鍵不在它的比對範圍內。
    # Codex PR #70 P1：收尾判決要帶著**當時那棵樹的指紋**，否則 sync 只知道
    # 「有一輪跑成功過」，不知道那一輪驗的是不是現在要推的這些檔。
    # 用註冊冊的 sha 當指紋：倉內每個受管檔的內容雜湊都在它裡面，改過任何一個
    # 要嘛 check 會紅（冊沒重建），要嘛這個 sha 會變（冊重建了）—— 兩種都抓得到。
    wrap["registry_sha256"] = def_sha256_file(REGISTRY_PATH) if REGISTRY_PATH.is_file() else ""
    payload["wrapup"] = wrap
    def_write_json(json_path, payload)
    if autotest.get("matrix"):
        print(f"[MATRIX] {autotest['matrix'].get('html')}")
    if autotest.get("dataframes"):
        print(f"[DATAFRAME] {autotest['dataframes'].get('verdict')} · {autotest['dataframes'].get('folder')}")
    def_open_report(html_path, payload["verdict"], getattr(args, "no_open", False), ui_ok=not ui_bad)
    if autotest.get("focus"):
        fc = autotest["focus"].get("counts") or {}
        print(f"[FOCUS] 個股 {fc.get('stock', 0)}/{fc.get('files', 0)} 檔 · 頁 {fc.get('pages_kept', 0)}/{fc.get('pages_total', 0)}"
              f"（年度財報頁 {fc.get('annual_pages', 0)}）· {(autotest['focus'].get('manifest') or {}).get('csv', '')}")
    if autotest.get("lock"):
        c = autotest["lock"].get("counts") or {}
        print(f"[LOCK] NEW {c.get('NEW', 0)} · HELD {c.get('HELD', 0)} · BROKEN {c.get('BROKEN', 0)} · OPEN {c.get('OPEN', 0)} · "
              f"{autotest['lock'].get('ledger')}")
        print(f"[FIX]  {(autotest['lock'].get('fix_list') or {}).get('txt')}")
    try:
        paste = def_write_pasteback(out)
        print(f"[PASTE] {paste['path']} · {paste['chars']} 字（整份貼回對話：燈號 · 數字 · 待修清單按部位 · 首頁原文 {paste['evidence_files']} 檔 · 聚焦清冊）")
    except Exception as error:  # noqa: BLE001
        paste = None
        print(f"[PASTE] 沒寫成：{error.__class__.__name__}: {error}")
    # VCGC 的省 token 契約：預算是 Root SSOT 的，VRN 只讀不訂；超了就說超多少，不自己改上限。
    # 自己一個 try —— capsule 垮了不代表貼回檔沒寫成，兩件事分開講（說錯比不說還糟）。
    if paste:
        try:
            cap = def_capsule_budget()
            over = paste["chars"] - cap["max_chars"]
            print(f"[CAPSULE] {cap['protocol']} · 上限 {cap['max_chars']} 字（來源 {cap['source']}"
                  + (f"：{cap['why']}" if cap["why"] else "") + "）· "
                  + (f"貼回檔超出 {over} 字" if over > 0 else f"貼回檔在預算內（還剩 {-over} 字）"))
            caps = def_write_capsule(Path(paste["path"]), cap, wrap)
            print(f"[CAPSULE] {caps['path']} · {caps['chars']} 字 · 帶了 {caps['kept']} 段"
                  + (f"，省略 {'、'.join(caps['left'])}" if caps["left"] else "（全部都放得下）")
                  + " —— 貼這一份就好")
        except Exception as error:  # noqa: BLE001
            print(f"[CAPSULE] 沒切成：{error.__class__.__name__}: {error}（貼回檔在，照上面那個路徑讀）")
    def_show_matrix(out, plain=bool(getattr(args, "plain_matrix", False)), rows=int(getattr(args, "matrix_rows", 0) or 0))
    # 2026-10-20：代號紀錄那一份（四碼代號 15 欄）以前只有 `matrix --view record` 叫得出來，
    # 一輪實測收尾不寫它 —— G20 修好的欄位操作員看不到。這裡順手落檔，畫面上不再印第二張大表。
    if def_show_matrix(out, plain=True, view="record", stream=io.StringIO()) == 0:
        print(f"[MATRIX-RECORD] 代號紀錄 15 欄 · {out / 'VRN_Matrix_Record_v0100.txt'}")
    print(f"[收尾] {'完成' if wrap['done'] else '未完成'} · {wrap['rule']}"
          + ("" if wrap["done"] else " —— 卡在：" + "；".join(wrap["blockers"])))
    return 0 if wrap["done"] else 1


SYNC_COMMIT_PREFIX = "VRN-1 實測收尾"
# 提交訊息尾巴要附的署名，一行一條（`Key: value`）。倉內不寫死內容，由跑鏈的那一方設。
SYNC_TRAILER_ENV = "VRN_SYNC_TRAILER"


# [VRN-ID] VRN-MAN001-FNC121 · LOGIC
def def_git(arguments: Sequence[str], cwd: Path) -> Tuple[int, str]:
    """跑一道 git，回（結束碼, 合併後的輸出）。輸出照原樣帶回來，不裁、不美化。"""
    try:
        done = subprocess.run(["git", *arguments], cwd=str(cwd), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=300)
    except FileNotFoundError:
        return 127, "找不到 git"
    except subprocess.TimeoutExpired:
        return 124, f"git {' '.join(arguments)} 超過 300 秒"
    return done.returncode, (done.stdout + done.stderr).strip()


# [VRN-ID] VRN-MAN001-FNC122 · LOGIC
def def_repo_root(start: Path) -> Optional[Path]:
    code, out = def_git(["rev-parse", "--show-toplevel"], start)
    return Path(out) if code == 0 and out else None


# [VRN-ID] VRN-MAN001-FNC123 · LOGIC
def def_sync_blockers(run: Optional[Path]) -> Tuple[List[str], Dict[str, Any]]:
    """這一輪能不能上傳 —— 判準只讀報告 JSON 裡的 `wrapup`，不自己再判一次。

    收尾過了沒是 `def_wrapup` 說了算（閘沒有 FAIL、P20 UI 對得上、鏈上游沒硬失敗）。
    這裡要是自己重算一次「WARN 可以 FAIL 不行」之類的規則，就是同一個判斷兩顆頭：
    哪天 def_wrapup 的條件改了，上傳這條路會安靜地用舊規則放行。
    """
    if run is None:
        return ["找不到任何一輪實測的報告（先跑 run 或 all）"], {}
    report = run / "VRN_Main_Report_v0100.json"
    if not report.is_file():
        return [f"{run} 裡沒有 VRN_Main_Report_v0100.json"], {}
    payload = def_read_json(report)
    wrap = payload.get("wrapup")
    if not isinstance(wrap, dict):
        return [f"{report.name} 沒有收尾判決（這一輪是舊版 MAIN 跑的；重跑一次 run 或 all）"], payload
    if not wrap.get("done"):
        return ["收尾未完成：" + "；".join(wrap.get("blockers") or ["沒說原因"])], payload
    return [], payload


# [VRN-ID] VRN-MAN001-FNC125 · LOGIC
def def_sync_tree_ok(payload: Dict[str, Any], when: str) -> bool:
    """要推出去的這棵樹，現在**這一刻**撐不撐得住那份報告的綠燈。

    兩件一起問：
      一、倉自己一致嗎 —— 用 `check` 指令那四組，沒有另寫判準；
      二、這份報告驗的是不是現在這棵樹 —— 比報告裡記的註冊冊 sha。

    這個函式會被呼叫**不只一次**，是故意的：快轉會換掉 HEAD 與工作樹，
    所以快轉前問過不算數，快轉後、提交前要照同一套再問一次（Codex PR #71 P1）。
    對得上也印一行 —— 守門靜靜放行，看的人分不出它跑過沒有。
    """
    gate = def_check_ssot() + def_check_registry() + def_gate_astid() + def_gate_engine_lock()
    bad = [r for r in gate if r["status"] == "FAIL"]
    if bad:
        print(f"[SYNC] 不上傳（{when}）· 工作樹跟冊對不上：")
        for r in bad[:4]:
            print(f"[SYNC]   [{r['status']}] {r['gate']} · {r['item']} · {str(r.get('detail'))[:120]}")
        return False
    stamp = (payload.get("wrapup") or {}).get("registry_sha256")
    now_sha = def_sha256_file(REGISTRY_PATH) if REGISTRY_PATH.is_file() else ""
    if stamp and now_sha and stamp != now_sha:
        print(f"[SYNC] 不上傳（{when}）· 這份報告驗的不是現在這棵樹：")
        print(f"[SYNC]   報告跑的時候註冊冊是 {stamp[:12]}…，現在是 {now_sha[:12]}…")
        print("[SYNC]   要推就重跑一輪 run 或 all")
        return False
    if not stamp:
        print(f"[SYNC] （{when}）這份報告沒記註冊冊指紋（舊版 MAIN 跑的）· 只能靠一致性檢查")
    else:
        print(f"[SYNC] （{when}）冊與註冊冊一致（{len(gate)} 項 FAIL 0），報告指紋 {stamp[:12]}… 對得上")
    return True


# [VRN-ID] VRN-MAN001-FNC135 · LOGIC
def def_commit_message(verdict: str, counts: Dict[str, Any], run: Any) -> str:
    """sync 那一顆 commit 的訊息。

    鏈的規矩是「不手動提交」，可是跑鏈的那一方可能被要求在訊息尾巴附署名（trailer）。
    兩件事不該互相擋：署名文字從環境變數 VRN_SYNC_TRAILER 進來（一行一條，`Key: value`），
    **倉內的碼不寫死任何署名內容**。沒設就什麼都不加 —— 既有行為一個字不變。

    訊息是 sync 真正用的那一份（def_cmd_sync 只呼叫這裡），所以測這支就是測那條路。
    """
    message = (f"{SYNC_COMMIT_PREFIX}：{verdict} · "
               + " ".join(f"{k}={v}" for k, v in counts.items())
               + f"\n\n{WRAPUP_RULE}。這一筆由 VRN-1 的 sync 在收尾完成後自動提交。\n"
               + f"報告：{run}\n")
    trailer = (os.environ.get(SYNC_TRAILER_ENV) or "").strip()
    if trailer:
        message += "\n" + "\n".join(line.strip() for line in trailer.splitlines() if line.strip()) + "\n"
    return message


# [VRN-ID] VRN-MAN001-FNC144 · ENTRY
def def_cmd_merge(args: argparse.Namespace) -> int:
    """操作員 2026-10-20「解決 GITHUB 衝突問題」。把另一條分支併進來，一條指令。

    分工是這支的全部重點，而且刻意不對稱：

      · **機器重生的檔**（`def_generated_paths()`）—— 不接、不猜、不手改：跑 build／lock
        整個重生。`.gitattributes` 的 `-merge` 已經確保工作區留著的是合法 JSON 而不是
        插了 `<<<<<<<` 的半成品，所以重生有乾淨的起點。
      · **只往後加的日誌**（`MERGE_UNION_FILES`）—— `merge=union` 已經把兩邊的輪次都留下來，
        這裡只確認它真的不再卡著。
      · **其他任何檔**（原始碼、測試、手寫的冊）—— **一律停下來**。衝突標記原樣留著，
        合併也原樣留在進行中，由人決定。這支一個字都不改。

    為什麼非得是「重生」不是「取一邊」：取一邊會過 —— 冊看起來是合法 JSON、git 也不吵，
    可是它記的是**另一棵樹**的指紋與內容。那種錯要等到下一次 check 或下一次借工具才爆，
    而那時已經推上去了。

    預設空跑：只 fetch、只數、只說要做什麼，不碰工作樹。`--apply` 才真的併。
    """
    here = Path(__file__).resolve().parent
    root = def_repo_root(here)
    if root is None:
        print("[MERGE] 這裡不是 git 工作樹，沒有可以合併的對象")
        return 1
    into = str(getattr(args, "into", "") or "main")
    apply_now = bool(getattr(args, "apply", False))

    dirty = [line for line in def_git(["status", "--porcelain"], root)[1].splitlines() if line.strip()]
    if dirty:
        print(f"[MERGE] 不併 · 工作樹有 {len(dirty)} 個沒提交的改動：併上去之後就分不出哪些是遠端帶來的")
        for line in dirty[:8]:
            print(f"[MERGE]   {line}")
        return 1
    code, branch = def_git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if code != 0 or not branch or branch == "HEAD":
        print(f"[MERGE] 不併 · detached HEAD（{branch or '讀不到'}）")
        return 1
    code, out = def_git(["fetch", "origin", into], root)
    if code != 0:
        print(f"[MERGE] fetch 失敗（什麼都沒做）：{out}")
        return 1
    code, counts_line = def_git(["rev-list", "--left-right", "--count", f"origin/{into}...HEAD"], root)
    parts = counts_line.split() if code == 0 else []
    if len(parts) != 2 or not all(x.isdigit() for x in parts):
        print("[MERGE] 數不出落後／超前，不假設它是 0（什麼都沒做）")
        return 1
    behind, ahead = int(parts[0]), int(parts[1])
    print(f"[MERGE] {branch} 相對 origin/{into}：落後 {behind} · 超前 {ahead}")
    if behind == 0:
        print(f"[MERGE] origin/{into} 的東西都在了，不用併")
        return 0

    attrs_ok = [r for r in def_gate_gitattributes() if r["status"] == "PASS"]
    print(f"[MERGE] 合併規矩：{'對得上宣告' if attrs_ok else '**對不上**（先跑 build）'} · "
          f"{len(def_generated_paths())} 個重生檔 -merge")
    if not attrs_ok:
        print("[MERGE] 不併 · 沒有合併規矩就併，git 會把衝突標記寫進 JSON 冊裡")
        return 1
    if not apply_now:
        print(f"[MERGE] 空跑結束：沒有動工作樹。要真的併請加 --apply")
        return 0

    code, out = def_git(["merge", "--no-commit", "--no-ff", f"origin/{into}"], root)
    stuck = [line for line in def_git(["diff", "--name-only", "--diff-filter=U"], root)[1].splitlines() if line.strip()]
    rel = VRN_ROOT.resolve().relative_to(root.resolve()).as_posix().strip("/")
    mine = set(def_generated_paths_from(root))             # git 回報的是相對倉根的路徑，要換算
    regen = sorted(path for path in stuck if path in mine)
    human = sorted(path for path in stuck if path not in mine)
    print(f"[MERGE] 卡住 {len(stuck)} 個檔 · 機器重生的 {len(regen)} 個 · 要人判的 {len(human)} 個")
    for path in regen:
        print(f"[MERGE]   重生 {path}")
    for path in human:
        print(f"[MERGE]   要人判 {path}")
    if human:
        print("[MERGE] 停在這裡 · 上面那些是原始碼／測試／手寫的冊，怎麼併是人的決定，這支不猜")
        print("[MERGE]   衝突標記原樣留著，合併也留在進行中；整個不要了就 `git merge --abort`")
        return 1
    if code != 0 and not stuck:
        print(f"[MERGE] 合併失敗，而且不是衝突（什麼都沒解）：{out}")
        return 1

    print("[MERGE] 只剩機器重生的檔 —— 跑 build／lock 整個重生，不接、不猜")
    rc = def_cmd_build()
    if rc != 0:
        print("[MERGE] build 沒過，合併留在進行中（`git merge --abort` 可以整個退掉）")
        return 1
    rc = def_cmd_lock(argparse.Namespace(status=False, unlock="", part="", lock_home=""))
    if rc != 0:
        print("[MERGE] lock 沒過，合併留在進行中（`git merge --abort` 可以整個退掉）")
        return 1
    code, out = def_git(["add", "-A", "--", rel or "."], root)
    if code != 0:
        print(f"[MERGE] git add 失敗：{out}")
        return 1
    still = [line for line in def_git(["diff", "--name-only", "--diff-filter=U"], root)[1].splitlines() if line.strip()]
    if still:
        print("[MERGE] 重生之後還卡著（不提交）：" + "、".join(still[:6]))
        return 1
    if _all_check() != 0:
        print("[MERGE] 重生完 check 有 FAIL —— 不提交。合併留在進行中")
        return 1
    message = (f"合併 origin/{into} 進 {branch}：機器重生的 {len(regen)} 個檔由 build／lock 重生\n\n"
               + "重生（不是手接，也不是取一邊 —— 取一邊會留下另一棵樹的指紋）：\n"
               + "".join(f"  {path}\n" for path in regen)
               + "\n只往後加的日誌由 .gitattributes 的 merge=union 併好，兩邊的輪次都留："
               + "、".join(MERGE_UNION_FILES) + "\n"
               + "\n重生之後 check 沒有 FAIL 才提交。這一筆由 VRN-1 的 merge 指令自動提交。\n")
    trailer = (os.environ.get(SYNC_TRAILER_ENV) or "").strip()
    if trailer:
        message += "\n" + "\n".join(line.strip() for line in trailer.splitlines() if line.strip()) + "\n"
    code, out = def_git(["commit", "-m", message], root)
    if code != 0:
        print(f"[MERGE] git commit 失敗：{out}")
        return 1
    print(f"[MERGE] 已併 · {out.splitlines()[0] if out else ''}")
    print("[MERGE] 這棵樹還沒有任何一輪實測驗過：要推之前先跑 run，再跑 sync --apply")
    return 0


# [VRN-ID] VRN-MAN001-FNC124 · ENTRY
def def_cmd_sync(args: argparse.Namespace) -> int:
    """操作員 2026-10-19「成功確認收尾登陸上傳 GITHUB AND SYNC ALL」。

    **只有收尾完成的那一輪才上傳。** 跑完不等於跑對（`def_wrapup`），而一份沒驗過的
    結果被推上 origin，下一個人看到的是「綠的分支」—— 那比沒推更糟。

    預設是**空跑**：把每一步要做什麼原樣印出來，一個位元組都不寫、不連遠端。
    真的要動要 `--apply`，和這個倉既有的規矩一致（VRN-1.ps1 的 -Apply／-SyncRepository
    也是這個意思：一個管寫入、一個管連網）。

    fail-closed 的幾處，都是「寧可停下來也不要猜」：
      · detached HEAD —— 沒有分支就沒有上游，不知道要推去哪；
      · 分支分叉（落後且超前）—— ff 不了，要怎麼併是人的決定，不是這裡猜；
      · 收尾未完成 —— 連看都不用看 git。
    """
    here = Path(__file__).resolve().parent
    root = def_repo_root(here)
    if root is None:
        print("[SYNC] 這裡不是 git 工作樹，沒有可以同步的對象")
        return 1
    run = Path(args.run) if getattr(args, "run", "") else def_latest_run()
    blockers, payload = def_sync_blockers(run)
    if blockers:
        print(f"[SYNC] 不上傳 · {WRAPUP_RULE} —— 卡在：" + "；".join(blockers))
        return 1
    counts = payload.get("counts") or {}
    verdict = payload.get("verdict") or "?"
    print(f"[SYNC] 這一輪收尾完成（{verdict} · " + " ".join(f"{k}={v}" for k, v in counts.items()) + f"）· 報告 {run}")

    code, branch = def_git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if code != 0 or not branch or branch == "HEAD":
        print(f"[SYNC] 不上傳 · detached HEAD（{branch or '讀不到'}）：沒有分支就沒有上游，不猜要推去哪")
        return 1

    # Codex PR #70 P1：**報告要綁在要推出去的那棵樹上**，而且不管有沒有東西要提交。
    # 這裡先問一次是為了快點停下來（還沒碰網路）；真正算數的那一次在快轉之後。
    if not def_sync_tree_ok(payload, "動手之前"):
        return 1

    apply_now = bool(getattr(args, "apply", False))
    changed_now = [line for line in def_git(["status", "--porcelain"], root)[1].splitlines() if line.strip()]
    tag = "" if apply_now else "（空跑；--apply 才真的做）"
    print(f"[SYNC] 分支 {branch} · 未提交 {len(changed_now)} 個檔{tag}")
    for line in changed_now[:12]:
        print(f"[SYNC]   {line}")
    if len(changed_now) > 12:
        print(f"[SYNC]   …另外 {len(changed_now) - 12} 個")
    message = def_commit_message(verdict, counts, run)
    if not apply_now:
        print("[SYNC] 空跑結束：沒有連遠端、沒有提交、沒有推。要真的做請加 --apply")
        return 0

    # Codex PR #70 P2：**先 fetch、先快轉，再做本機 commit**。
    # 反過來的話，遠端有進度時會先長出一顆本機 commit，接著 behind>0 且 ahead>0，
    # 判成「分叉」就停 —— 留下一顆孤兒 commit，而它本來只要快轉就好。
    # Codex PR #70 P2：origin 上**還沒有**這個分支時，`git fetch origin <branch>` 會 fatal。
    # 那不是錯誤，是「第一次推」。先問 ls-remote 分得出這兩種。
    code, remote_ref = def_git(["ls-remote", "--heads", "origin", branch], root)
    if code != 0:
        print(f"[SYNC] 問不到遠端（沒有推）：{remote_ref}")
        return 1
    behind = ahead = None
    if remote_ref.strip():
        code, out = def_git(["fetch", "origin", branch], root)
        if code != 0:
            print(f"[SYNC] fetch 失敗（沒有推）：{out}")
            return 1
        code, counts_line = def_git(["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"], root)
        if code == 0:
            parts = counts_line.split()
            if len(parts) == 2 and all(x.isdigit() for x in parts):
                behind, ahead = int(parts[0]), int(parts[1])
        if behind is None:
            print(f"[SYNC] 數不出落後／超前，不假設它是 0（沒有推）")
            return 1
        print(f"[SYNC] 落後 {behind} · 超前 {ahead}")
        if behind > 0 and ahead > 0:
            print("[SYNC] 不推 · 分支分叉了：ff 併不過去，要怎麼併是人的決定，這裡不猜")
            return 1
        if behind > 0:
            code, out = def_git(["merge", "--ff-only", f"origin/{branch}"], root)
            if code != 0:
                print(f"[SYNC] 快轉失敗（沒有推）：{out}")
                return 1
            print(f"[SYNC] 已快轉 {behind} 顆")
            # Codex PR #71 P1：快轉換掉了 HEAD 與工作樹 —— 剛才問過的那棵樹已經不是這一棵。
            # 遠端帶進來的檔 + 本機還沒提交的改動，這個組合沒有任何一輪實測驗過，
            # 註冊冊指紋也可能因此對不上。所以**提交與推之前，照同一套再問一次**。
            if not def_sync_tree_ok(payload, f"快轉 {behind} 顆之後"):
                print("[SYNC]   （快轉把樹換掉了：遠端帶進來的改動沒有任何一輪實測涵蓋）")
                return 1
            changed_now = [line for line in def_git(["status", "--porcelain"], root)[1].splitlines() if line.strip()]
    else:
        print(f"[SYNC] origin 上還沒有 {branch}（第一次推這個分支）")

    if changed_now:
        code, out = def_git(["add", "-A"], root)
        if code != 0:
            print(f"[SYNC] git add 失敗：{out}")
            return 1
        code, out = def_git(["commit", "-m", message], root)
        if code != 0:
            print(f"[SYNC] git commit 失敗：{out}")
            return 1
        print(f"[SYNC] 已提交 · {out.splitlines()[0] if out else ''}")
    code, out = def_git(["push", "-u", "origin", branch], root)
    if code != 0:
        print(f"[SYNC] push 失敗：{out}")
        return 1
    print(f"[SYNC] 已推上 origin/{branch} · {out.splitlines()[-1] if out else ''}")
    return 0


# [VRN-ID] VRN-MAN001-FNC094 · LOGIC
def def_show_matrix(run: Path, plain: bool = False, rows: int = 0, view: str = "parts", stream: Any = None) -> int:
    """Operator 2026-10-12「output validated results in matrix by rich for my reviewing」: the run's verified results as a matrix
    in the console (rich when installed, text otherwise) and VRN_Matrix_Console_v0100.txt in the run folder.

    stream：收尾順手把代號紀錄那一份寫成檔案時用的 —— 畫面上不再印第二張大表，檔案照樣落地。"""
    try:
        mx = def_load_module("VRN_Main_matrix", ENGINE_FILES["matrix"])
        got = mx.show_report_matrix(Path(run), plain=plain, rows=rows, view=view, stream=stream)
    except Exception as error:  # noqa: BLE001
        print(f"[MATRIX-CONSOLE] 沒畫成：{error.__class__.__name__}: {error}")
        return 1
    if "error" in got:
        print("[MATRIX-CONSOLE] " + got["error"])
        return 1
    return 0


PASTEBACK_NAME = "VRN_PasteBack_v0100.txt"


# [VRN-ID] VRN-MAN001-FNC090 · LOGIC
def def_latest_run(base: Optional[Path] = None) -> Optional[Path]:
    """最近一輪實測的輸出資料夾（鎖帳本那個資料夾不是一輪實測）。

    2026-10-19：本來只找 `%LOCALAPPDATA%\\VRN_Main`，但**沒給 `--out` 的那一輪根本不寫在那裡** ——
    `def_cmd_run` 寫的是 `<暫存目錄>/VRN_Main_<時間戳>`（Windows 上是 ...\\AppData\\Local\\Temp，
    跟 ...\\AppData\\Local\\VRN_Main 是兩個地方）。於是 `matrix`／`pasteback`／`sync` 不帶路徑時
    一律回「找不到任何一輪」，而那一輪明明剛跑完。

    兩個地方都找，取時間最新的那個。`base` 給了就只找 base（呼叫端指定過就不要再自作主張）。
    """
    if base is not None:
        roots = [(base, "*")]
    else:
        roots = [(Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "VRN_Main", "*"),
                 # 暫存目錄是公用的，底下什麼都有（單元測試留下的資料夾裡也有同名報告，實測踩到過）。
                 # 所以這裡只認 def_cmd_run 自己取的名字 VRN_Main_<時間戳>，不是「有報告就算」。
                 (Path(tempfile.gettempdir()), "VRN_Main_*")]
    runs: List[Path] = []
    for root, pattern in roots:
        if not root.is_dir():
            continue
        for d in root.glob(pattern):
            if d.is_dir() and d.name != "locks" and (d / "VRN_Main_Report_v0100.json").is_file():
                runs.append(d)
    return max(runs, key=lambda d: d.stat().st_mtime) if runs else None


# [VRN-ID] VRN-MAN001-FNC092 · LOGIC
def def_paste_table(header: Sequence[str], rows: Sequence[Sequence[Any]]) -> List[str]:
    """One text table (| cells |): the operator asked for text, tables and categories kept apart."""
    cell = lambda v: re.sub(r"\s+", " ", str("" if v is None else v)).replace("|", "｜").strip()   # noqa: E731
    out = ["| " + " | ".join(cell(h) for h in header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return out


# [VRN-ID] VRN-MAN001-FNC091 · IO
def def_write_pasteback(run: Path, cap_sources: int = 200, evidence_files: int = 20, evidence_lines: int = 30) -> Dict[str, Any]:
    """Real run 2026-10-12: one text file to paste back whole, in five parts (operator 2026-10-12 round 3: text, tables and
    categories kept apart): 1 the gate lamps that are not PASS, 2 the numbers, 3 the fix list grouped by part (every priority
    0 / 1 item, the review items, the unmapped labels and single readings as counts), 4 the first-page lines of the files
    whose cover parts conflict (the evidence), 5 the stock rows of the focus manifest.  Nothing new is computed; it gathers."""
    run = Path(run)
    main = def_read_json(run / "VRN_Main_Report_v0100.json")
    loop = def_read_json(run / "autotest" / "VRN_AutoTest_Report.json")
    lines = [f"VRN 貼回 {MAIN_VERSION} · {run.name} · {main.get('generated', '')} · 樣本 {main.get('samples', '')}",
             "（五段：一 燈號 · 二 數字 · 三 待修清單按部位分類 · 四 首頁原文 · 五 聚焦清冊；表格用 | 分欄，原文只在第四段）", ""]
    lamp_rows = [[r.get("status"), r.get("gate"), r.get("item"), str(r.get("detail", ""))[:300]] for r in main.get("rows") or []
                 if r.get("status") != "PASS"]
    for rnd in loop.get("rounds") or []:
        lamp_rows += [[r.get("status"), f"第 {rnd.get('round')} 輪 {r.get('gate')}", r.get("name"), str(r.get("detail", ""))[:300]]
                      for r in rnd.get("rows") or [] if r.get("status") not in ("PASS", "SKIP")]
    lines.append(f"== 一、燈號：{main.get('verdict', '?')} · " + " ".join(f"{k}={v}" for k, v in (main.get("counts") or {}).items())
                 + " · AutoTest " + " · ".join(f"第 {r.get('round')} 輪 {r.get('verdict')} " + " ".join(f"{k}={v}" for k, v in (r.get("counts") or {}).items())
                                            for r in loop.get("rounds") or []) + " ==")
    lines += def_paste_table(["燈", "閘", "項目", "說明"], lamp_rows) + [""]
    fix_json = next(iter(sorted(run.glob("autotest/round*/titletrim/VRN_FixList_v0100.json"))), None)
    fix = def_read_json(fix_json) if fix_json else {}
    h = fix.get("header") or {}
    rows = fix.get("rows") or []
    fc = (loop.get("focus") or {}).get("counts") or {}
    lc = (loop.get("lock") or {}).get("counts") or {}
    pri = Counter(r.get("priority") for r in rows)
    num = [["檔案 / 個股處理", f"{fc.get('files', '')} / {fc.get('stock', '')}"],
           ["個股 PDF 頁：全部 / 讀了 / 年度財報頁", f"{fc.get('pages_total', '')} / {fc.get('pages_kept', '')} / {fc.get('annual_pages', '')}"],
           ["鎖 NEW / HELD / BROKEN / OPEN", f"{lc.get('NEW', 0)} / {lc.get('HELD', 0)} / {lc.get('BROKEN', 0)} / {lc.get('OPEN', 0)}"],
           ["部位", " · ".join(f"{k} {v}" for k, v in (h.get("states") or {}).items())],
           ["待修 優先 0 / 1 / 2 / 3", f"{pri.get(0, 0)} / {pri.get(1, 0)} / {pri.get(2, 0)} / {pri.get(3, 0)}"]]
    lines += ["== 二、數字 =="] + def_paste_table(["項目", "值"], num) + [""]

    # [VRN-ID] VRN-MAN001-FNC093 · LOGIC
    def src(r: Dict[str, Any]) -> Dict[str, Any]:
        raw = r.get("sources")
        if isinstance(raw, dict):
            return raw
        try:
            got = json.loads(str(raw or "{}"))
            return got if isinstance(got, dict) else {"來源": str(raw)}
        except ValueError:
            return {"來源": str(raw)} if raw else {}
    lines.append(f"== 三、待修清單（按部位分類）· {h.get('generated', '')} · 樣本 {h.get('files', 0)} 檔（個股 {h.get('stock', 0)}）==")
    p0 = [r for r in rows if r.get("priority") == 0]
    if p0:
        lines += [f"-- 3.0 已鎖部位退步（BROKEN）· {len(p0)} 項 --"]
        lines += def_paste_table(["檔案", "部位", "這次的值", "說明", "各讀法"],
                                 [[r.get("file"), r.get("part"), r.get("value"), str(r.get("why", ""))[:120], json.dumps(src(r), ensure_ascii=False)[:cap_sources]] for r in p0])
    p1 = [r for r in rows if r.get("priority") == 1]
    by_part: Dict[str, List[Dict[str, Any]]] = {}
    for r in p1:
        by_part.setdefault(str(r.get("part", "")).split("@")[0].split(":")[0], []).append(r)
    lines += [f"-- 3.1 優先 1 讀法不一致／該有沒讀到／TRIM 掉字 · {len(p1)} 項 · 部位 × 次數：" + "、".join(f"{k}×{len(v)}" for k, v in sorted(by_part.items(), key=lambda kv: -len(kv[1]))) + " --"]
    evidence_wanted: List[str] = []
    for part, sel in sorted(by_part.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"· {part} × {len(sel)}")
        trs = []
        for r in sel:
            d = src(r)
            where = " ".join(str(d.get(k, "")) for k in ("區塊", "首頁那一行") if d.get(k))
            readers = {k: v for k, v in d.items() if k not in ("首頁那一行", "首頁上一行", "區塊")}
            trs.append([r.get("file"), f"{r.get('state')}{('/' + r['lock']) if r.get('lock') else ''}", r.get("value"),
                        json.dumps(readers, ensure_ascii=False)[:cap_sources], where[:140]])
            if part.startswith(("cover.", "title.")) and r.get("state") in ("CONFLICT", "MISSING", "TRIM_LOSS", "TRIM_REGRESSION") and r.get("file") not in evidence_wanted:
                evidence_wanted.append(r.get("file"))
        lines += def_paste_table(["檔案", "狀態/鎖", "值", "各讀法", "首頁那一行"], trs)
    p2 = [r for r in rows if r.get("priority") == 2 and r.get("state") != "UNMAPPED"]
    if p2:
        lines += [f"-- 3.2 要人判（多候選、驗算不過）· {len(p2)} 項 --"]
        lines += def_paste_table(["檔案", "部位", "狀態", "值", "說明"], [[r.get("file"), r.get("part"), r.get("state"), r.get("value"), str(r.get("why", ""))[:140]] for r in p2])
    unm = Counter(str(r.get("part", "")).split(":", 1)[-1].rsplit("@", 1)[0] for r in rows if r.get("state") == "UNMAPPED")
    if unm:
        lines += [f"-- 3.3 對不到科目的列標 · {sum(unm.values())} 格 --"] + def_paste_table(["列標", "次數"], unm.most_common(80))
    single = Counter(str(r.get("part", "")).split("@")[0] for r in rows if r.get("priority") == 3)
    if single:
        lines += [f"-- 3.4 只有一條讀法（SINGLE，鎖不住）· {sum(single.values())} 項 --"] + def_paste_table(["部位", "次數"], single.most_common(40))
    lines.append("")
    results_json = next(iter(sorted(run.glob("autotest/round*/titletrim/VRN_TitleTrim_Results_v0100.json"))), None)
    results = def_read_json(results_json) if results_json else []
    by_file = {r.get("file"): r for r in results if isinstance(r, dict)} if isinstance(results, list) else {}
    lines.append(f"== 四、首頁原文（優先 1 有首頁／標題部位衝突或缺讀的檔 {len(evidence_wanted)} 個，列前 {min(len(evidence_wanted), evidence_files)} 個；每檔前 {evidence_lines} 行：行號 [區塊] x座標 原文；★前次 = 前次投資建議底下那一行，不讀）==")
    for name in evidence_wanted[:evidence_files]:
        zones = ((by_file.get(name) or {}).get("cover") or {}).get("zones") or []
        mine = [r for r in p1 if r.get("file") == name]
        parts_here = sorted({str(r.get("part", "")).split("@")[0] for r in mine})
        cited = set()
        for r in mine:                                     # the lines the fix list points at, and their neighbours
            for k in ("首頁那一行", "首頁上一行"):
                m = re.match(r"L(\d+)", str(src(r).get(k, "")))
                if m:
                    cited.update(range(int(m.group(1)) - 1, int(m.group(1)) + 2))
        lines.append(f"-- {name} · 衝突部位：{', '.join(parts_here)} --")
        if not zones:
            lines.append("  （這一檔沒有首頁行：掃描檔或不是 PDF）")
        shown = 0
        for z in zones:                                    # round 4: body lines are left out unless cited (the file was 82 KB)
            if shown >= evidence_lines:
                lines.append(f"  …其餘 {len(zones) - z.get('line', 0) + 1} 行略")
                break
            if z.get("zone") == "SummaryBox" and not z.get("prior") and z.get("line") not in cited:
                continue
            x = f"x{int(z['x0'])}" if z.get("x0") is not None else ""
            lines.append(f"  L{z.get('line')} [{z.get('zone')}] {x} {'★前次 ' if z.get('prior') else ''}{str(z.get('clean', ''))[:90]}")
            shown += 1
    lines.append("")
    manifest = run / "autotest" / "VRN_Focus_Manifest_v0100.csv"
    if manifest.is_file():
        with open(manifest, encoding="utf-8-sig", newline="") as fh:
            table = list(csv.reader(fh))
        if table:
            stock = [r for r in table[1:] if len(r) > 1 and r[1] == "STOCK"]
            lines.append(f"== 五、聚焦清冊：個股 {len(stock)} 列（非個股 {len(table) - 1 - len(stock)} 列不列）==")
            lines += def_paste_table(table[0], stock)
    path = run / PASTEBACK_NAME
    text = "\n".join(lines) + "\n"
    def_write_atomic(path, text, newline=None)      # 這一份本來就吃平台換行，不在這裡改掉
    return {"path": str(path), "chars": len(text), "lines": len(lines), "evidence_files": len(evidence_wanted)}


# [VRN-ID] VRN-MAN001-FNC072 · ENTRY
def main(argv: Optional[Sequence[str]] = None) -> int:
    def_console_utf8()
    os.environ["VIA_FROM_VCGC"] = "YES"   # 自立閘座：獨立 MAIN 自己就是閘（FLOW 針相容），不是 consent
    parser = argparse.ArgumentParser(prog=Path(__file__).name, description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--accel-home", default="", help="加速器所在的 supportive modules 資料夾（或設 VIA_ACCEL_HOME）")
    sub = parser.add_subparsers(dest="command")
    p_run = sub.add_parser("run", help="完整實測：前置閘 + VRN_AutoTestLoop + 報告")
    p_run.add_argument("--samples", default="", help=f"報告資料夾（Windows 預設 {DEFAULT_SAMPLES_WINDOWS} 若存在）")
    p_run.add_argument("--out", default="", help="輸出資料夾（預設暫存目錄）")
    p_run.add_argument("--truth", default="", help="人工真值 JSON（只放操作員手上）")
    p_run.add_argument("--rounds", type=int, default=3)
    p_run.add_argument("--synthetic", action="store_true", help="忽略實檔，用合成語料")
    p_run.add_argument("--no-audit", action="store_true")
    p_run.add_argument("--limit", type=int, default=0, help="合成語料最多幾檔（0 = 全部）")
    p_run.add_argument("--no-focus", action="store_true", help="整份報告、所有檔案照舊全部處理（預設只處理個股報告的檔名、第一頁、年度財報頁）")
    p_run.add_argument("--lock-home", default="", help="輸出鎖帳本資料夾（預設 VRN_LOCK_HOME 或 %%LOCALAPPDATA%%\\VRN_Main\\locks）")
    p_run.add_argument("--plain-matrix", action="store_true", help="跑完的核對矩陣用純文字（不用 rich、不上色）")
    p_run.add_argument("--no-open", action="store_true",
                       help="跑完不要自動開報告（預設：驗證無誤就把 HTML 報告開起來；無桌面環境本來就不會開）")
    p_run.add_argument("--no-cache", action="store_true", help="不用 TEMP 快取，這一輪全部重讀（預設：輸入、引擎、冊、套件都沒變的步驟沿用上次結果）")
    p_run.add_argument("--cache-home", default="", help="快取資料夾（預設 VRN_CACHE_HOME 或 <TEMP 根>/VRN_Main/cache）")
    p_run.add_argument("--matrix-rows", type=int, default=0, help="跑完的核對矩陣只列前 N 檔（0 = 全部）")
    p_all = sub.add_parser("all", parents=[p_run], add_help=False,
                           help="一個指令收掉整條鏈：build → lock → check → run（run 的旗標照吃，例如 --samples／--no-cache）")
    p_all.add_argument("--skip-seal", action="store_true",
                       help="引擎與冊都沒動過時跳過 build／lock／check，直接跑實測")
    p_self = sub.add_parser("selftest", help="離線自測（冊、註冊、加速器、檔名 oracle）")
    p_self.add_argument("--json", default="")
    sub.add_parser("build", help="重建 ssot/ 三本冊 + 註冊冊")
    p_check = sub.add_parser("check", help="只驗 ssot/ 與註冊冊，不寫")
    p_check.add_argument("--json", default="")
    p_sa = sub.add_parser("standalone", help="把 VRN 資料夾單獨複製到暫存區再跑")
    p_sa.add_argument("--keep", action="store_true")
    p_acc = sub.add_parser("accel", help="加速器狀態")
    p_acc.add_argument("--activate", action="store_true", help="套用執行緒預算（只影響本行程）")
    p_lock = sub.add_parser("lock", help="已知答案逐組證明，全過的引擎鎖指紋；--status 看帳本；--unlock 解鎖")
    p_lock.add_argument("--status", action="store_true")
    p_lock.add_argument("--unlock", default="", help="檔名或檔案 SHA-256（前 16 碼即可）")
    p_lock.add_argument("--part", default="", help="只解這一個部位（例：cover.target_price）")
    p_lock.add_argument("--lock-home", default="")
    p_matrix = sub.add_parser("matrix", help="一次實測的核對矩陣畫在 console（rich 有就用；每檔一列、每部位一欄：值＋記號＋鎖）")
    p_matrix.add_argument("--out", default="", help="實測輸出資料夾（預設 %%LOCALAPPDATA%%\\VRN_Main 底下最新的一次）")
    p_matrix.add_argument("--plain", action="store_true", help="純文字、不用 rich、不上色")
    p_matrix.add_argument("--rows", type=int, default=0, help="只列前 N 檔（0 = 全部）")
    p_matrix.add_argument("--view", choices=("parts", "record"), default="parts", help="parts = 部位核對矩陣；record = 四碼代號 15 欄紀錄")
    p_paste = sub.add_parser("pasteback", help="把一次實測的總結、整份待修清單、聚焦清冊個股列寫成一個檔（整份貼回對話）")
    p_paste.add_argument("--out", default="", help="實測輸出資料夾（預設 %%LOCALAPPDATA%%\\VRN_Main 底下最新的一次）")
    p_truth = sub.add_parser("truth-from-matrix", help="母倉首頁矩陣的貼文（報告檔／型別／代號／券商／報告日／官方證券名／TP／評等）→ G11 真值檔（只在操作員手上，不入庫）")
    p_truth.add_argument("src", help="貼文存成的檔（UTF-8／UTF-16 都可）")
    p_truth.add_argument("--out", default="", help="真值 JSON（預設 <src>.truth.json；不能在 VRN 樹裡）")
    p_truth.add_argument("--source", default="", help="來源說明（例如 VIA_VRN_FirstPageEngine v0113 2026-09-11）")
    p_merge = sub.add_parser("merge", help="把另一條分支併進來：機器重生的檔跑 build／lock 重生，其他衝突一律停下來交給人（預設空跑，--apply 才真的做）")
    p_merge.add_argument("--into", default="main", help="要併進來的遠端分支（預設 main）")
    p_merge.add_argument("--apply", action="store_true", help="真的併（預設只 fetch 和數，不動工作樹）")
    p_sync = sub.add_parser("sync", help="收尾完成的那一輪才上傳：提交 → fetch → 快轉 → 推上 origin（預設空跑，--apply 才真的做）")
    p_sync.add_argument("--apply", action="store_true", help="真的提交與推；不給就只印出會做什麼，不寫也不連遠端")
    p_sync.add_argument("--run", default="", help="指定要上傳哪一輪的輸出資料夾（預設取最新一輪）")
    p_ans = sub.add_parser("answers", help=argparse.SUPPRESS)
    p_ans.add_argument("--json", default="")
    args = parser.parse_args(argv)

    if args.command == "run":
        return def_cmd_run(args)
    if args.command == "all":
        return def_cmd_all(args)
    if args.command in (None, "selftest"):
        rc, rows = selftest(args.accel_home)
        if getattr(args, "json", ""):
            def_write_json(Path(args.json), {"main": MAIN_NAME, "verdict": def_verdict(rows), "counts": def_counts(rows), "rows": rows})
        return rc
    if args.command == "sync":
        return def_cmd_sync(args)
    if args.command == "merge":
        return def_cmd_merge(args)
    if args.command == "build":
        return def_cmd_build()
    if args.command == "lock":
        return def_cmd_lock(args)
    if args.command == "check":
        rows = def_check_ssot() + def_check_registry() + def_gate_astid() + def_gate_engine_lock() + def_gate_tool_manifest()
        for r in rows:
            print(f"  [{r['status']:4}] {r['gate']} · {r['item']}" + (f" · {r['detail']}" if r.get("detail") else ""))
        print(f"[CHECK] {def_verdict(rows)} · " + " ".join(f"{k}={v}" for k, v in def_counts(rows).items()))
        if args.json:
            def_write_json(Path(args.json), {"verdict": def_verdict(rows), "counts": def_counts(rows), "rows": rows})
        return 1 if def_counts(rows)["FAIL"] else 0
    if args.command == "standalone":
        rc, rows = def_cmd_standalone(args.keep, args.accel_home)
        for r in rows:
            print(f"  [{r['status']:4}] {r['gate']} · {r['item']}" + (f" · {r['detail']}" if r.get("detail") else ""))
        print(f"[STANDALONE] {def_verdict(rows)}")
        return rc
    if args.command == "accel":
        rows = def_gate_accel(args.accel_home, activate=args.activate)
        for r in rows:
            print(f"  [{r['status']:4}] {r['item']} · {r['detail']}")
        cands = def_accel_candidates(args.accel_home)
        hit = [(s, p) for s, p in cands if (p / ACCEL_ENTRY).is_file()]
        if hit:
            print("  找到：" + " | ".join(f"{s}: {p}" for s, p in hit))
        else:
            # 一個都沒有的時候印一行空的「候選位置：」等於什麼都沒說。
            # 找過哪裡要講出來，操作員才知道 VIA_ACCEL_HOME 該指去哪。
            print(f"  找不到 {ACCEL_ENTRY}。找過這些地方（走訪順序）：")
            for src, path in cands:
                print(f"    [{'有這個資料夾' if path.is_dir() else '沒有  '}] {src:16} {path}")
            print("  掛上去：設 VIA_ACCEL_HOME=<母倉 supportive modules>，或 --accel-home <路徑>（要放在子指令前面）")
        return 0
    if args.command == "matrix":
        run = Path(args.out) if args.out else def_latest_run()
        if run is None or not (run / "VRN_Main_Report_v0100.json").is_file():
            print(f"[MATRIX-CONSOLE] 找不到實測輸出（{run or '%LOCALAPPDATA%\\VRN_Main 底下沒有'}）")
            return 1
        return def_show_matrix(run, plain=args.plain, rows=args.rows, view=args.view)
    if args.command == "pasteback":
        run = Path(args.out) if args.out else def_latest_run()
        if run is None or not (run / "VRN_Main_Report_v0100.json").is_file():
            print(f"[PASTE] 找不到實測輸出（{run or '%LOCALAPPDATA%\\VRN_Main 底下沒有'}）")
            return 1
        paste = def_write_pasteback(run)
        print(f"[PASTE] {paste['path']} · {paste['chars']} 字 · {paste['lines']} 行")
        return 0
    if args.command == "truth-from-matrix":
        tm = def_load_module("VRN_Main_truthmatrix", ENGINE_FILES["truthmatrix"])
        return tm.main(["convert", args.src] + (["--out", args.out] if args.out else []) + (["--source", args.source] if args.source else []))
    if args.command == "answers":
        eng = def_load_engines()
        answers = def_filename_answers(eng)
        fpe = eng.get("fpe")
        paths = {k: (def_rel(Path(v)) if v else None) for k, v in sorted(((fpe.knowledge_paths or {}) if fpe else {}).items())}
        answers["knowledge_paths"] = paths
        answers["knowledge_outside_vrn"] = sorted(k for k, v in paths.items() if v and (v.startswith("/") or ":" in v[:3]))
        answers["load_errors"] = {k: v for k, v in eng.items() if k.endswith("_error")}
        if args.json:
            def_write_json(Path(args.json), answers)
        else:
            print(json.dumps(answers, ensure_ascii=False)[:2000])
        return 0 if not answers["load_errors"] else 1
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
