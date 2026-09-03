#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_SYSTEM_MANAGER — 總系統管理器(批304;UI 操作收斂)
====================================================================
操作員令:「應該用一個總 VIA_SYSTEM_MANAGER.py 管理一切:銜接 sync、
html u/i、輸入參數、windows i/o、拖曳式、下拉選單、勾選控管元件;
engine / module list 要清楚」。
一總管六職(Zero-Hydra=全複用正主,零重造):
  ①sync   安全同步(唯一 stash 證據→目前分支 upstream→ff-only→按 hash 套回；
          安全備份保留，分支分流即誠實停，不 reset --hard)
  ②list   引擎/模組清單清楚列印(=MDL112 Atlas gather 直取)
  ③run    任務執行(=MDL095 任務冊 argv 白名單 subprocess;
          任意指令拒絕=安全鐵則)
  ④serve  帶起唯一本機 API 樞紐。
  ⑤template 產生使用者可編輯 HTML，日常再生不覆寫。
  ⑥ui     總控頁再生+開啟(Windows I/O:os.startfile 正道/
          webbrowser 後備):
          左=可收合的最少操作輸入，參數由任務契約動態顯示。
          右=運轉總覽、結果矩陣、Plotly、引擎、模組、規劃與連線分頁。
          控管元件僅由同源 /master 以 CSRF 權杖 POST /run；
          離線檔與可編輯模板只讀預覽，不執行工作。
v0100→v0101(批283 操作員令「由一個 VIA_SystemManager.py 整合
全部連結」):⑤serve 職=帶起唯一 API 樞紐(MDL095 尾版 127.0.0.1
:8765；現行 v0114 已移除跨站 CORS，file:// 只作預覽)+總控頁右欄 API 連結冊
(全部端點一表=全部連結歸一總管)。
v0107→v0108(批304 操作員令「輸入全放可收左側、右側多分頁
矩陣、固定頁首頁尾、正式名稱、引擎/模組/讀取規劃、Plotly
Dashboard、使用者測試」):
  ①輸入治理:所有操作輸入集中可收合左欄;預設僅任務+選填代號,
    批次與收件置於進階區,降低非必要輸入。
  ②結果治理:右側七分頁=運轉總覽/結果矩陣/Plotly 分析/
    引擎清單/模組清單/讀取規劃/系統連線;目前輸入與真實 /status 同頁呈現。
  ③視覺治理:固定單一 Header/Footer、淺色高密度、正式中文為主;
    程式識別碼預設隱藏,僅維運人員可切換顯示。
  ④圖表治理:已產生的離線 Plotly 正本以 iframe 讀取;前置資料
    未建立時顯示缺料原因與次序，不畫假圖、不依賴 CDN。
  ⑤品質治理:修正未定義 CSS 狀態色;加入鍵盤分頁、ARIA、窄螢幕
    抽屜、JS 語法/DOM/UAT 契約;另產可獨立優化 HTML 模板。
v0106→v0107(批303 操作員令「字體小一點比較專業 layout 緊湊
一點」):全字階 -1~2px+間距收 25%(與 MDL116 v0101 同階;
結構/元件/檢點零變)。
v0105→v0106(批302 操作員令「總控及各子系統弄成如圖示 UI」+
「不管色票只管 layout 及內容輸入介面」+「pc 水平長方形 手機垂直
長方形 響應式 自動最佳化 顏色最後統一」):
  ①版型入統一殼語言(MDL116 同律:左欄品牌+編號導航+底部狀態格
    /主區麵包屑+規格帶+大數字統計卡+內容卡;四正本萃取)
  ②參數契約卡(圖2 式):任務下拉+codes+儲存參數(localStorage
    via_master_params;try/catch 容錯)+回復預設;載頁自動回填
  ③響應雙態:PC=左欄+主區水平;手機=頂條+導航橫捲垂直;clamp
    流體字級;色票=中性(統一色票候操作員終裁)
  ④工法:CSS/JS 全遷 raw 常數(__MCSS__/__APPJS__ 佔位符)=
    f-string 吃括號根絕(批285 兩犯教訓收官)
v0104→v0105(批301 操作員令「輸入參數最少化 WINDOW I/O 拖曳式
下拉選單」;六維稽核實錘=拖曳誠實 v1 只列名):拖曳收件升真收 v2
——FileReader→base64→POST 樞紐 /intake(text/plain 簡單請求免
preflight);逐件回執 ✓已落+sha8/SKIP 同 hash/✗誠實拒(逾 50MB);
樞紐未開=誠實降級列名+via-intake 指引(=舊 v1 行為);API 連結冊
+POST /intake;+/vapdeck 已在冊(四系統入口齊)。
v0102→v0103(批292 操作員令「不卡斷 20個加速器 動態進度條」):
狀態矩陣每任務列+真進度條(pct 有值=實寬條;running 無 pct=
流動條紋動畫=誠實不假估;ok/fail=滿條定色)。零輪詢加重(同一
/status 資料)=不卡斷不變。
v0101→v0102(批285 操作員令「狀態的顯現/輸入參數/運作結果的
顯現」):總控頁三顯迴路——狀態矩陣(輪詢 /status 每 4s RYG 點
+elapsed+pct;樞紐離線=誠實標一次)+結果窗(點任務列→log 尾)。
v0108→v0109(批333 操作員令「用此檔案為 U/I 自動連結」):Codex 線 v0108 原件
(intake b305)版前進為現役正主;②檢盤點數改動態(只增不減:引擎≥194/模組≥85
且唯一)、⑧檢 Plotly 就緒分支以「頁面檔案更新」證據句判(缺料分支維持誠實句);
頁=同源 /master 由 DeckServer v0115 注入權杖供應。
v0109→v0110(批334):正式名稱冊 +4(system_ui/group_class/group_backtest/story_rotation
=DeckServer v0116 任務冊 36);②檢任務數改 ≥32(只增不減)。
v0110→v0111(批335):正式名稱冊 +complete_all(DeckServer v0117 任務冊 37)。
v0111→v0112(批336):系統連線分頁 +上船件冊卡(IntakeRoster/StoryRotation/VapStack/System 真連結)。
用法:python3 VIA_SYSTEM_MANAGER_v0112.py sync|list|run <task>|serve|ui
      |template [--force]|--selftest [--no-open]
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

import ast
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

VIA = Path(__file__).resolve().parent
REG = VIA / "supportive modules" / "registry"
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_MasterControl_v0100.html")
TEMPLATE_OUT = (VIA / "supportive modules" / "ui_support"
                / "VIA_UI_PlotlyDashboard_EditableTemplate_v0100.html")
STD_DASHBOARD_OUT = (VIA / "supportive modules" / "ui_support"
                     / "VIA_UI_StdDashboard_v0100.html")

UI_VERSION = "v0108"
BRIDGE_URL = "http://127.0.0.1:8765"
ACTIVATION_STATE = "待人工啟用審查"
RETIRE_SUBSYSTEM = "VIA_RetiredEngines"

SUBSYSTEM_FORMAL_NAMES = {
    "ChipWar": "市場籌碼與輪動分析",
    "GroupIndex": "台股族群指數與輪動",
    "SuperDocExtractor": "泛用文件智慧擷取",
    "VAP": "視覺分析與自動繪圖",
    "VDF": "資料擷取與鍛造",
    "VRN": "研究報告解析與知識化",
    "WorkOps": "工作流程與專案治理",
    RETIRE_SUBSYSTEM: "已退役引擎存證區",
}

ENGINE_FORMAL_NAMES = {
    "CHW_ENG005_RotationEngine": "市場輪動判讀引擎",
    "GRP_ENG040_GroupingRotationRunner": "台股族群輪動執行引擎",
    "GRP_ENG041_RotationMethodLab": "族群輪動方法驗證實驗室",
    "PLG_ENG001_SuperExtract": "泛用文件內容擷取引擎",
    "VAP_ENG001_AutoplotEngineChartlib": "自動繪圖元件庫引擎",
    "VAP_ENG002_AutoplotEngine": "自動繪圖核心引擎",
    "VAP_ENG003_AutoplotSeabornPlotly": "Seaborn 與 Plotly 雙渲染引擎",
    "VAP_ENG004_TAFactory": "技術分析圖表工廠",
    "VAP_ENG005_TemplateRunner": "圖表模板執行引擎",
    "VAP_ENG006_AcceptanceAudit": "視覺輸出驗收稽核引擎",
    "VAP_ENG007_RawWideRefresh": "寬表資料更新引擎",
    "VAP_ENG008_TestConsole": "繪圖測試與除錯控制台",
    "VAP_ENG009_DashboardUI": "視覺分析儀表板介面引擎",
    "VAP_ENG010_ChartLibrarySSOT": "圖表規格單一真實來源引擎",
    "VAP_ENG011_TemplateRegistry": "圖表模板註冊引擎",
    "VAP_ENG012_GovernedImageStore": "治理式圖像儲存引擎",
    "VAP_ENG013_MarketAnalytics": "金融市場分析引擎",
    "VAP_ENG014_StdDashboardTemplate": "標準儀表板模板引擎",
    "VDF_ENG019_MDL501FetchContractManager": "資料擷取契約管理引擎",
    "VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher": "全球金融行情擷取引擎",
    "VDF_ENG045_OutputHub": "資料輸出中樞引擎",
    "VDF_ENG046_FetchMatrixRegistry": "資料擷取矩陣註冊引擎",
    "VDF_ENG047_USMacroDetailFetcher": "美國總體經濟明細擷取引擎",
    "VDF_ENG048_TAFactory": "技術分析資料工廠",
    "VDF_ENG049_FiveDayFetch": "五日行情增量擷取引擎",
    "VDF_ENG050_OrderFetch": "排程式資料擷取引擎",
    "VDF_ENG051_ActiveTWETF_Holdings": "主動式台股 ETF 每日持股擷取引擎",
    "VDF_ENG052_MegaFetch": "多來源資料整合擷取引擎",
    "VDF_ENG053_ParamEngineMap": "參數與引擎映射管理引擎",
    "VDF_ENG054_TWDailyBackfill": "台股日資料歷史回補引擎",
    "VDF_ENG055_OmniFetch": "全域資料擷取協調引擎",
    "VDF_ENG056_ChipBackfill": "台股籌碼資料歷史回補引擎",
    "VDF_ENG057_TradingValueBackfill": "台股成交值歷史回補引擎",
    "VDF_ENG058_IndustryUnifiedMap": "產業分類統一映射引擎",
    "VDF_ENG059_EstimateBands": "共識估值區間計算引擎",
    "VDF_ENG060_AdjPriceLayer": "調整後價格標準層引擎",
    "VDF_ENG061_FeatureStore": "市場特徵儲存引擎",
    "VDF_ENG062_GroupFeatureLayer": "族群特徵計算層引擎",
    "VDF_ENG063_MonthlyRevenue": "台股月營收擷取與分析引擎",
    "VDF_ENG064_HistoryBackfill": "跨市場歷史資料回補引擎",
    "VDF_ENG065_DbImport": "資料庫匯入與對帳引擎",
    "VDF_ENG066_GlobalUniverse": "全球金融商品清單擷取引擎",
    "VDF_ENG067_ConsensusEnrichment": "ETF 持股共識資料增益引擎",
    "VDF_ENG068_ETFConsensusAnalysis": "主動式 ETF 共識分析引擎",
    "VDF_ENG069_RevenueConsensusAnalysis": "月營收與共識交叉分析引擎",
    "VRN_ENG017_MDL004OCRFetchingPDFTable": "PDF 表格 OCR 擷取引擎",
    "VRN_ENG018_MDL005OCRFetchingPDFText": "PDF 文字 OCR 擷取引擎",
    "VRN_ENG023_MDL011DailyFetcher": "研究報告每日擷取引擎",
    "VRN_ENG049_ContentReconcile": "文件內容對帳引擎",
    "VRN_ENG050_ContentStore": "文件內容儲存引擎",
    "VRN_ENG052_DocxEngine": "Word 文件處理引擎",
    "VRN_ENG055_OfficeMerge": "Office 文件合併引擎",
    "VRN_ENG056_PdfForensics": "PDF 結構鑑識引擎",
    "VRN_ENG057_ScanOcrRescue": "掃描文件 OCR 救援引擎",
    "VRN_ENG058_TableOmni": "泛用表格擷取引擎",
    "VRN_ENG059_GapMultirescue": "內容缺口多路救援引擎",
    "VRN_ENG060_TextOmni": "泛用文字擷取與還原引擎",
    "VRN_ENG062_SummarizerV1": "研究內容摘要引擎",
    "VRN_ENG063_Lexicon": "金融語彙管理引擎",
    "VRN_ENG064_KnowledgeStack": "研究知識庫管理引擎",
    "VRN_ENG065_MailIntel": "郵件內容智慧分析引擎",
    "VRN_ENG066_NLPSupportHub": "自然語言處理支援中樞",
    "VRN_ENG067_MindMapSSOT": "心智圖單一真實來源引擎",
    "VRN_ENG068_DailyBrief": "每日研究摘要引擎",
    "VRN_ENG069_ConsensusDB": "市場共識資料庫引擎",
    "VRN_ENG070_YahooConsensus": "Yahoo Finance 共識擷取引擎",
    "VRN_ENG071_CnyesFusion": "鉅亨 FactSet 與 Yahoo 共識融合引擎",
    "VRN_ENG072_FirstPageText": "研究報告首頁文字擷取引擎",
    "VRN_ENG073_ReportStructuredDB": "研究報告結構化入庫引擎",
    "VRN_ENG074_FinancialPages": "財務報表頁面與表格擷取引擎",
    "VRN_ENG075_DocToMarkdown": "文件轉 Markdown 引擎",
    "VRN_ENG076_RegressionGate": "文件抽取鏈迴歸驗證引擎",
    "VRN_ENG077_OmniFormatBridge": "全格式文件轉接引擎",
    "VRN_ENG078_NLPOneBridge": "泛用自然語言單引擎橋接器",
    "VIA_ENG150_BuildDeck": "簡報自動建置引擎",
    "VIA_ENG170_WorkPulseUnified": "工作脈動統一分析引擎",
}

# 原始 docstring 含治理口令、內部代碼或英文化工作名時，使用可讀候核名稱；
# 這些仍會附 E 序號，不冒充人工核定正名。
ENGINE_CANDIDATE_NAMES = {
    "CHW_ENG006_RotationDashboard": "族群資金相對強弱輪動象限圖引擎",
    "CHW_ENG014_BlocEngine": "科技與傳統產業比較引擎",
    "CHW_ENG015_ChipwarEngine": "跨市場情境合成分析引擎",
    "CHW_ENG016_ChipwarVapDashboard": "全鏈成果視覺圖庫引擎",
    "CHW_ENG017_FomoIndexEngine": "錯失恐懼綜合指數引擎",
    "CHW_ENG021_SocialEngine": "社群情緒錯失恐懼分析引擎",
    "CHW_ENG024_XmktEngine": "台美市場錯失恐懼因子引擎",
    "VDF_ENG042_MoviesIntake": "電影資料集收件與鍛造引擎",
    "VIA_ENG003_TALibEngine": "技術分析指標計算引擎",
    "VIA_ENG060_WorkopsAuditBundle": "工作機制研究稽核成果包引擎",
    "VIA_ENG061_WorkopsBackup": "工作流程安全車道驗收引擎",
    "VIA_ENG075_WorkopsMlLab": "機器學習與深度學習實驗引擎",
    "VIA_ENG081_WorkopsSelftest": "整合與系統測試一鍵引擎",
    "VIA_ENG083_WorkopsSummaryMatrix": "詳細摘要結果與資料庫矩陣引擎",
    "VIA_ENG087_WorkopsWopIdentifier": "多訊號融合與工作專案化引擎",
    "VRN_ENG027_PipelineRunner": "研究報告生產管線執行引擎",
    "VRN_ENG053_DocxMerge": "Word 產物主表合併引擎",
    "VRN_ENG054_InputMatrixValidator": "研究報告輸入矩陣驗證引擎",
}

TASK_FORMAL_NAMES = {
    "boot": "全系統每日資料更新",
    "backfill": "歷史資料增量回補",
    "consensus": "鉅亨 FactSet 市場共識更新",
    "revenue": "台股全市場月營收更新",
    "revenue_groups": "台股族群月營收排行榜",
    "global": "全球金融商品資料更新",
    "firstpage": "研究報告首頁文字擷取",
    "structdb": "研究報告結構化入庫",
    "finpages": "財務報表頁面與表格擷取",
    "etf_enrich": "ETF 持股與市場共識資料增益",
    "etf_analysis": "主動式 ETF 與市場共識分析",
    "unified_register": "統一編號註冊表更新",
    "cmdcenter": "全系統健康狀態圖更新",
    "nlp": "自然語言單引擎橋接",
    "revenue_consensus": "月營收與市場共識交叉分析",
    "mdconvert": "文件轉 Markdown",
    "regression": "文件抽取鏈迴歸驗證",
    "vofie": "全格式文件重構",
    "deps_scan": "相依性全景掃描",
    "deps_mirror": "套件鏡像速度檢測",
    "rebuild_scan": "環境重建規劃快巡",
    "rebuild_full": "環境完整重建與執行檔產出",
    "lessons": "教訓台帳與基線檢視",
    "ocr_probe": "OCR 執行車道探測",
    "ocr_plan": "OCR 隔離環境安裝規劃",
    "selftest_fast": "全系統矩陣快速自我測試",
    "etf_fetch": "主動式台股 ETF 每日持股更新",
    "chat2doc": "對話轉文章與程式規格",
    "uispec": "使用者介面元件三語轉碼",
    "govcon": "中央治理六管線控制台",
    "std_dashboard": "標準 Plotly 分析儀表板",
    "system_ui": "系統總台六主體快照再生",
    "complete_all": "一鍵完工鏈(未完工作自動化)",
    "group_class": "族群分類與價格指數",
    "group_backtest": "族群回測",
    "story_rotation": "故事族群輪動橋接",
    "ui": "全系統使用者介面再生",
}

FORMAL_TERM_MAP = {
    "AutoCode": "自動編碼", "Registry": "註冊管理", "Manifest": "清單",
    "Fetch": "擷取", "Adapter": "轉接", "Build": "建置",
    "Package": "套件", "Pointer": "版本指標", "Spec": "規格",
    "Subsystem": "子系統", "Page": "頁面", "Audit": "稽核",
    "Article": "文章", "Intake": "收件", "AutoPilot": "自動協調",
    "Autocoder": "自動編碼", "Command": "指令", "Log": "紀錄",
    "Dedup": "去重", "Index": "索引", "Dependency": "相依性",
    "Downloads": "下載資料夾", "Organizer": "整理", "Cross": "交叉",
    "Analysis": "分析", "Environment": "環境", "Plan": "規劃",
    "Rebuild": "重建", "Router": "路由", "Governance": "治理",
    "Console": "控制台", "Interface": "介面", "Contract": "契約",
    "Input": "輸入", "Precheck": "前置檢查", "Install": "安裝",
    "Gate": "閘門", "Lessons": "教訓台帳", "Master": "總體",
    "Hub": "中樞", "Number": "編號", "Panorama": "全景",
    "RegistryUnionmerge": "註冊表整併", "Selftest": "自我測試",
    "SSOT": "單一真實來源", "Evolve": "演進", "Structure": "結構",
    "Forge": "鍛造", "Support": "支援", "Bridge": "橋接",
    "Import": "匯入", "System": "系統", "Manager": "管理",
    "Name": "名稱", "Product": "產品", "UI": "使用者介面",
    "Engine": "引擎", "Catalog": "目錄", "Accelerator": "加速器",
    "Central": "中央", "Government": "治理", "Syntax": "語法",
    "Rescue": "救援", "Rename": "重新命名", "Tree": "檔案樹",
    "Atlas": "全景圖", "Matrix": "矩陣", "Wrapup": "收斂",
    "Autorun": "自動執行", "Triage": "分流", "Issue": "問題",
    "Arbiter": "仲裁", "Canonical": "正本", "Test": "測試",
    "Pyramid": "金字塔", "Status": "狀態", "Sync": "同步",
    "Task": "任務", "Report": "報告", "Data": "資料",
    "Plotly": "Plotly", "Dashboard": "儀表板", "Rotation": "輪動",
    "Group": "族群", "Market": "市場", "Financial": "財務",
    "Document": "文件", "OCR": "OCR", "NLP": "自然語言處理",
}

PLAN_STAGES = (
    ("01", "執行環境與根目錄確認", "確認 VIA 正本、權限、Python 與 PowerShell；僅讀取，不變更。", "唯讀前置檢查"),
    ("02", "引擎與模組自動盤點", "掃描功能模組、支援模組、任務冊與頁面清單。", "現況真值盤點"),
    ("03", "功能與資料契約分類", "依子系統、輸入、輸出、相依性與風險標準化分類。", "待執行結果"),
    ("04", "介面與資料流銜接", "建立模組對模組、參數對引擎及支援工具的契約關係。", "待執行結果"),
    ("05", "正本與正式名稱校準", "統一正式中文名稱、識別碼、版本與單一真實來源。", "規格已定義"),
    ("06", "中央註冊表同步", "將通過契約的項目同步至 append-only 註冊表。", "待執行結果"),
    ("07", "二十道治理閘驗證", "執行語法、依賴、資料、介面、回歸與安全驗證。", "待執行結果"),
    ("08", "矩陣報告輸出", "產生輸入、狀態、結果、問題與解決方案矩陣。", "本頁已提供容器"),
    ("09", "HTML 使用者介面再生", "由正本管理器產生固定頁首、可收輸入與多分頁結果頁。", "已建置"),
    ("10", "人工啟用審查", "所有驗證通過後仍由操作員人工核准；系統不自行啟用。", ACTIVATION_STATE),
)


def _mod(pat: str):
    p = sorted(REG.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _formalize_identifier(identifier: str, item_type: str) -> str:
    """將技術識別碼轉成使用者可讀正式名稱；識別碼仍留作維運搜尋。"""
    if item_type == "engine" and identifier in ENGINE_FORMAL_NAMES:
        return ENGINE_FORMAL_NAMES[identifier]
    core = re.sub(r"^(?:CGC_MDL\d+_|[A-Z]{2,4}_ENG\d+_)", "", identifier)
    core = re.sub(r"(?:_?sha)?[0-9a-f]{8,}$", "", core, flags=re.I)
    core = re.sub(r"_v\d+[A-Za-z0-9]*$", "", core)
    core = core.replace("_", " ")
    for source, target in sorted(FORMAL_TERM_MAP.items(),
                                 key=lambda item: len(item[0]), reverse=True):
        core = re.sub(re.escape(source), f" {target} ", core, flags=re.I)
    parts = []
    for chunk in core.split():
        if re.fullmatch(r"(?:MDL|ENG)?\d+", chunk, re.I):
            continue
        if re.search(r"[\u4e00-\u9fff]", chunk):
            parts.append(chunk)
            continue
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|\d+",
                           chunk)
        parts.extend(words or [chunk])
    label = " ".join(dict.fromkeys(p for p in parts if p)).strip()
    label = re.sub(r"\s+", " ", label)
    suffix = "引擎" if item_type == "engine" else "治理模組"
    if not label:
        label = "未命名項目"
    if suffix not in label:
        label = f"{label} {suffix}"
    return label


def _docstring_formal_name(path: Path | None, item_type: str) -> str | None:
    """抽取可送人工候核的中文名稱；治理批號與程式橋名不得進主名稱。"""
    if path is None or not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        doc = ast.get_docstring(tree, clean=True) or ""
    except (OSError, SyntaxError, UnicodeError):
        return None
    first = next((line.strip() for line in doc.splitlines() if line.strip()), "")
    if not re.search(r"[\u4e00-\u9fff]", first):
        return None
    for marker in ("—", "－", "--", " - "):
        if marker in first:
            first = first.split(marker, 1)[1].strip()
            break
    first = re.sub(
        r"^(?:CGC_MDL\d+_|[A-Z]{2,4}_ENG\d+_)[A-Za-z0-9_]+\s*", "", first)
    # 括號內若是批次、內部工具、提示詞或版本治理資訊，一律整段移除。
    governance = (r"批\s*\d+|操作員令|TOOL[- ]?\d+|SPEC[- ]?\d+|"
                  r"9hh5to|mega[- ]?prompt|def\s*\d+|v\d{3,}")
    first = re.sub(rf"[（(][^）)]*(?:{governance})[^）)]*[）)]", "", first,
                   flags=re.I)
    # 來源標題偶有未閉合括號；遇治理標記即截斷，不能把殘句冒充名稱。
    first = re.split(rf"[（(][^）)]*(?:{governance})", first,
                     maxsplit=1, flags=re.I)[0]
    # 其餘括號多為實作備註而非名稱；未閉合時直接截斷，避免殘句上榜。
    first = re.sub(r"[（(][^）)]*[）)]", "", first)
    first = re.split(r"[（(]", first, maxsplit=1)[0]
    formal_terms = {
        r"SYSTEM\s+MANAGER": "系統管理",
        r"U\s*/?\s*I": "使用者介面",
        r"MATRIX": "矩陣",
        r"HTML": "網頁",
        r"JSON": "結構化資料",
        r"REGEX": "正規表示式",
        r"PROMPT": "提示詞",
        r"PORTAL": "入口",
        r"CRITICAL": "重大",
        r"AIO": "整合式",
        r"AST": "語法樹",
        r"SLIDES?": "簡報",
        r"ONEDRIVE": "雲端同步資料夾",
        r"VAP\s*/\s*VDF\s*/\s*VRN": "三大分析子系統",
        r"DOWNLOADS": "下載資料夾",
        r"ENVMANAGER": "環境管理",
        r"NOSTALL": "防停滯",
        r"SSOT": "單一真實來源",
    }
    for source, target in formal_terms.items():
        first = re.sub(rf"\b(?:{source})\b", target, first, flags=re.I)
    first = re.sub(r"\bv\d+\b|\b[WT]\d+\b", "", first, flags=re.I)
    first = first.replace("+", "與")
    first = re.sub(r"\s+", " ", first)
    first = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", first)
    first = re.sub(r"入口\s*入口", "入口", first)
    first = first.strip(" ：:;；-+·。()（）「」'")
    # 程式橋名、檔名、步驟句、雜湊與殘留治理代碼不是候核名稱。
    if re.search(r"[A-Za-z]{2,}_[A-Za-z0-9_]+|\.(?:json|py)\b|"
                 r"第\d+步|\bv\d{3,}\b|\b(?:TOOL|SPEC)[- ]?\d+\b|"
                 r"9hh5to|[0-9a-f]{12,}", first, re.I):
        return None
    if (not first or len(first) > 72
            or not re.search(r"[\u4e00-\u9fff]", first)):
        return None
    suffix = "引擎" if item_type == "engine" else "治理模組"
    return first if suffix in first else f"{first} {suffix}"


def _formal_task_name(task_id: str, fallback: str) -> str:
    """任務選項一律顯示正式名稱，不將程式鍵值暴露為主標籤。"""
    if task_id in TASK_FORMAL_NAMES:
        return TASK_FORMAL_NAMES[task_id]
    cleaned = re.sub(r"[（(][^）)]*(?:批\d+|ENG\d+|MDL\d+|--[a-z-]+)"
                     r"[^）)]*[）)]", "", fallback)
    return cleaned.strip() or "未命名任務"


def _engine_category(identifier: str) -> str:
    """依正式功能語意提供可篩選分類；不宣稱執行成功。"""
    checks = (
        (r"OCR|Pdf|Doc|Text|Table|Report|Content|Markdown", "文件與研究報告"),
        (r"Revenue|Consensus|Estimate|Financial", "財務與市場共識"),
        (r"ETF|Holding", "ETF 與持股"),
        (r"Group|Rotation|Sector|Flow", "族群與資金流"),
        (r"Fetch|Backfill|Import|Store|Data|Universe|Price", "資料擷取與儲存"),
        (r"Plot|Chart|Dashboard|Image|Template|Visual", "圖表與使用者介面"),
        (r"NLP|Lexicon|Knowledge|MindMap|Summary|Mail", "語意與知識管理"),
        (r"Test|Audit|Validate|Regression|Acceptance", "測試與驗證"),
    )
    for pattern, label in checks:
        if re.search(pattern, identifier, re.I):
            return label
    return "系統協調與支援"


def _engine_rows(d: dict) -> list[dict]:
    """建立引擎庫存列；Atlas 只證明盤點存在，不等同註冊或成功。"""
    rows = []
    candidate_number = 0
    active_ids = {identifier for subsystem, family in d["engines"].items()
                  if subsystem != RETIRE_SUBSYSTEM for identifier in family}
    retired_ids = set(d["engines"].get(RETIRE_SUBSYSTEM, {}))
    order = sorted(d["engines"], key=lambda name: (name == RETIRE_SUBSYSTEM, name))
    for subsystem in order:
        family = d["engines"][subsystem]
        retired = subsystem == RETIRE_SUBSYSTEM
        root = VIA / "functional modules" / subsystem
        file_index = {path.name: path for path in root.rglob("*.py")} \
            if root.exists() else {}
        for identifier, filename in sorted(family.items()):
            if retired and identifier in active_ids:
                continue
            official_name = ENGINE_FORMAL_NAMES.get(identifier)
            candidate_name = (ENGINE_CANDIDATE_NAMES.get(identifier)
                              or _docstring_formal_name(
                                  file_index.get(filename), "engine"))
            if official_name:
                name = official_name
            else:
                candidate_number += 1
                candidate_id = f"E{candidate_number:03d}"
                if candidate_name:
                    name = f"{candidate_name}（候核序號 {candidate_id}）"
                else:
                    kind = "歷史功能引擎" if retired else "現役功能引擎"
                    name = (f"{kind}（正式名稱待治理 · "
                            f"候核序號 {candidate_id}）")
            state = "已退役存證" if retired else "已盤點・尚未執行"
            if not retired and identifier in retired_ids:
                state = "現役位置已盤點・另有退役副本・尚未執行"
            rows.append({
                "name": name,
                "subsystem": SUBSYSTEM_FORMAL_NAMES.get(subsystem, subsystem),
                "category": _engine_category(identifier),
                "state": state,
                "state_class": "retired" if retired else "surveyed",
                "identifier": identifier,
            })
    return rows


def _module_rows(d: dict) -> list[dict]:
    """建立中央治理模組盤點列，候核名稱唯一、技術識別碼預設隱藏。"""
    rows = []
    for candidate_number, (identifier, filename) in enumerate(
            sorted(d["mods"].items()), start=1):
        candidate_id = f"M{candidate_number:03d}"
        candidate_name = _docstring_formal_name(REG / filename, "module")
        if candidate_name:
            name = f"{candidate_name}（候核序號 {candidate_id}）"
        else:
            name = ("中央治理功能模組（正式名稱待治理 · "
                    f"候核序號 {candidate_id}）")
        rows.append({
            "name": name,
            "category": _engine_category(identifier),
            "state": "已盤點・尚未執行",
            "identifier": identifier,
        })
    return rows


def _table_rows(rows: list[dict], columns: tuple[str, ...]) -> str:
    """集中產生可搜尋表列並 HTML encode，避免動態資料破壞 DOM。"""
    cells = []
    for row in rows:
        search_text = " ".join(str(row.get(k, "")) for k in row).lower()
        tds = "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>"
                      for key in columns)
        tech = html.escape(str(row.get("identifier", "")))
        cells.append(f'<tr data-search="{html.escape(search_text)}">{tds}'
                     f'<td class="tech-id">{tech}</td></tr>')
    return "".join(cells)


def do_sync() -> int:
    """遵循目前分支 upstream；保存本地修改，只允許 fast-forward。"""
    def g(*a):
        return subprocess.run(["git", "-C", str(VIA), *a],
                              capture_output=True, text=True)

    upstream_result = g("rev-parse", "--abbrev-ref", "--symbolic-full-name",
                        "@{upstream}")
    upstream = upstream_result.stdout.strip()
    if upstream_result.returncode != 0 or "/" not in upstream:
        print("[MGR:sync] 目前分支沒有可確認的 upstream，同步已停止")
        return 2
    remote = upstream.split("/", 1)[0]
    dirty = bool(g("status", "--porcelain").stdout.strip())
    stash_hash = None
    if dirty:
        message = ("MGR-safe-sync-" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                   + f"-{os.getpid()}")
        pushed = g("stash", "push", "--include-untracked", "-m", message)
        if pushed.returncode != 0:
            print("[MGR:sync] 本地修改無法安全保存，同步已停止")
            return 2
        matches = []
        for line in g("stash", "list", "--format=%H%x09%s").stdout.splitlines():
            commit, _, subject = line.partition("\t")
            if message in subject:
                matches.append(commit)
        if len(matches) != 1:
            print("[MGR:sync] 無法唯一確認本次 stash，同步已停止；既有 stash 未動")
            return 2
        stash_hash = matches[0]

    def restore() -> bool:
        if not stash_hash:
            return True
        restored = g("stash", "apply", "--index", stash_hash)
        if restored.returncode != 0:
            print("[MGR:sync] 本地修改套回發生衝突；"
                  f"安全備份 {stash_hash} 仍保留，已停止")
            return False
        print(f"[MGR:sync] 本地修改已回復；安全備份 {stash_hash} 保留供確認")
        return True

    fetch = g("fetch", remote, "--prune")
    if fetch.returncode != 0:
        restore()
        print(f"[MGR:sync] 無法連線 {upstream}；保留現有版本")
        return 2
    r = g("merge", "--ff-only", upstream)
    if r.returncode != 0:
        restore()
        print("[MGR:sync] 分支無法 fast-forward；未重置、未刪除任何本地修改")
        return 2
    if not restore():
        return 2
    print(f"[MGR:sync] {upstream} fast-forward 完成；本地修改已保留")
    return 0


def do_list(do_print: bool = True) -> dict:
    """引擎/模組清單清楚(MDL112 Atlas 資料層直取)"""
    d = _mod("CGC_MDL112_SystemAtlas_v*.py").gather()
    if do_print:
        for sub, fam in d["engines"].items():
            print(f"[ENGINE] {sub}({len(fam)} 族)")
            for b in sorted(fam):
                print(f"    {b}")
        print(f"[MODULE] CGC 治理模組 {len(d['mods'])} 族")
        for b in sorted(d["mods"]):
            print(f"    {b}")
    return d


def do_run(task: str, extra: list[str] | None = None) -> int:
    """白名單任務執行(MDL095 任務冊=唯一 SSOT;任意指令拒絕)"""
    T = _mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    if task not in T:
        print(f"[MGR:run] '{task}' 不在白名單任務冊=拒絕(安全鐵則)。"
              f"可用:{' '.join(sorted(T))}")
        return 2
    argv = list(T[task]["argv"]) + list(extra or [])
    print(f"[MGR:run] {task}:{T[task]['zh']}")
    return subprocess.run(argv, stdin=subprocess.DEVNULL).returncode


def render(d: dict, tasks: dict) -> str:
    """產生總控頁；操作輸入集中左欄、真值結果集中右側分頁。"""
    engine_rows = _engine_rows(d)
    module_rows = _module_rows(d)
    active_engines = sum(1 for row in engine_rows
                         if not row["state"].startswith("已退役"))
    retired_engines = len(d["engines"].get(RETIRE_SUBSYSTEM, {}))
    retired_unique = sum(1 for row in engine_rows
                         if row["state"].startswith("已退役"))
    task_options = []
    for task_id, meta in tasks.items():
        task_options.append(
            f'<option value="{html.escape(task_id)}" '
            f'data-codes="{str(bool(meta.get("codes"))).lower()}" '
            f'data-range="{str(bool(meta.get("range"))).lower()}" '
            f'data-cats="{str(bool(meta.get("cats"))).lower()}">'
            f'{html.escape(_formal_task_name(task_id, meta.get("zh", task_id)))}'
            '</option>')
    batch_ids = ("boot", "revenue", "consensus", "etf_analysis",
                 "revenue_consensus", "regression", "selftest_fast")
    batch_checks = "".join(
        f'<label class="check-row"><input type="checkbox" '
        f'value="{html.escape(task_id)}"><span>'
        f'{html.escape(_formal_task_name(task_id, tasks[task_id].get("zh", task_id)))}'
        '</span></label>' for task_id in batch_ids if task_id in tasks)
    engine_table = _table_rows(
        engine_rows, ("name", "subsystem", "category", "state"))
    module_table = _table_rows(module_rows, ("name", "category", "state"))
    plan_table = "".join(
        f'<tr><td>{no}</td><td>{html.escape(name)}</td>'
        f'<td>{html.escape(action)}</td><td>{html.escape(state)}</td></tr>'
        for no, name, action, state in PLAN_STAGES)
    if STD_DASHBOARD_OUT.exists():
        plotly_modified = datetime.fromtimestamp(
            STD_DASHBOARD_OUT.stat().st_mtime).astimezone()
        plotly_modified_iso = plotly_modified.isoformat(timespec="seconds")
        plotly_modified_text = plotly_modified.strftime("%Y-%m-%d %H:%M:%S %z")
        plotly_view = (
            '<div class="plotly-ready-note" id="plotlyFreshness">'
            '頁面檔案更新：<time datetime="'
            f'{html.escape(plotly_modified_iso)}">'
            f'{html.escape(plotly_modified_text)}</time>。此時間只證明頁面檔案更新，'
            '不等同來源行情或財務資料已更新。</div>'
            '<iframe id="plotlyFrame" title="VIA 標準 Plotly 分析儀表板" '
            'src="VIA_UI_StdDashboard_v0100.html" loading="lazy" '
            'sandbox="allow-scripts" referrerpolicy="no-referrer"></iframe>')
        plotly_state = "頁面已產生・資料新鮮度待核"
    else:
        plotly_view = (
            '<div class="empty-state" id="plotlyEmpty">'
            '<span class="empty-icon">◇</span><h3>Plotly 分析儀表板尚未產生</h3>'
            '<p>目前共識或月營收資料尚未完成。請先在左側執行「全系統每日資料更新」，'
            '資料表建立後再執行「標準 Plotly 分析儀表板」。本頁不顯示模擬行情或假圖。</p>'
            '<code>via → via-analysis → via-manager</code></div>')
        plotly_state = "等待來源資料"
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="via-csrf" content="">
<title>VIA 系統運轉與分析總控台</title><style>__MCSS__</style></head>
<body data-rail="open">
<header class="app-header" id="appHeader">
 <button type="button" id="railToggle" class="rail-toggle" aria-controls="controlRail"
  aria-label="開啟或關閉執行輸入"
  aria-expanded="true"><span aria-hidden="true">☰</span><span>執行輸入</span></button>
 <div class="identity"><span class="seal">理</span><div>
  <div class="product">Veritas Intelligence Analytics</div>
  <div class="motto">判天地之美，析萬物之理。</div></div></div>
 <div class="header-meta"><span class="build">總控台 {UI_VERSION}</span>
  <span id="bridgeState" class="connection unknown" aria-live="polite">連線尚未檢測</span></div>
</header>
<div class="app-shell">
<aside class="control-rail" id="controlRail" aria-label="執行輸入"
 aria-hidden="false">
 <div class="rail-scroll">
  <section class="rail-section primary-input">
   <div class="section-kicker">執行輸入</div><h1>選擇要完成的工作</h1>
   <p class="rail-note" id="parameterHint">系統只顯示該任務真正需要的參數。</p>
   <label for="task">工作項目</label>
   <select id="task" data-testid="task">{''.join(task_options)}</select>
   <div id="codesField" class="conditional-field" hidden>
    <label for="codes">股票代號</label>
    <input type="text" id="codes" inputmode="numeric" autocomplete="off"
     maxlength="349" aria-describedby="codesHelp inputValidation"
     placeholder="例如 2330, 2317"><small id="codesHelp">可輸入最多 50 個 4–6 位數代號，以逗號分隔。</small>
   </div>
   <div id="dateRangeField" class="conditional-field date-pair" hidden>
    <div><label for="dateStart">開始日期</label><input type="date" id="dateStart"
     aria-describedby="inputValidation"></div>
    <div><label for="dateEnd">結束日期</label><input type="date" id="dateEnd"
     aria-describedby="inputValidation"></div>
   </div>
   <div id="categoriesField" class="conditional-field" hidden>
    <label for="categories">資料分類</label>
    <input type="text" id="categories" autocomplete="off" maxlength="80"
     aria-describedby="inputValidation"
     placeholder="例如 idx,etf,us_macro"><small>可用分類：idx、etf、us_jp、fin_reports、oil、fx、cmdty、crypto、us_macro、fed、us_fiscal_rates。</small>
   </div>
   <div id="inputValidation" class="validation-message" role="alert" hidden></div>
   <div class="rail-actions">
    <button type="button" id="runOneButton" class="primary">執行選定工作</button>
    <button type="button" id="pingButton">檢測連線</button>
   </div>
   <div class="rail-actions compact">
    <button type="button" id="saveParamsButton" class="quiet">儲存</button>
    <button type="button" id="resetParamsButton" class="quiet">回復預設</button>
   </div>
  </section>
  <details class="rail-section">
   <summary>依序執行多項工作 <span>進階</span></summary>
   <p class="rail-note">下一項會等上一項完成後才啟動；任一項失敗即停止佇列。</p>
   <div id="batchChecks">{batch_checks}</div>
   <button type="button" id="runBatchButton" class="primary full">依序執行勾選工作</button>
  </details>
  <details class="rail-section">
   <summary>文件與資料收件 <span>選用</span></summary>
   <div id="drop" tabindex="0" role="button" aria-controls="filePicker">
    拖曳檔案到這裡，或按 Enter 選擇檔案
    <small>單檔上限 50 MB；指揮台未開時只列檔名，不假裝入庫。</small>
   </div>
   <input type="file" id="filePicker" multiple hidden>
   <ul id="files" class="file-results" aria-live="polite"></ul>
  </details>
  <details class="rail-section">
   <summary>清單篩選 <span>維運</span></summary>
   <label for="catalogSearch">搜尋正式名稱或技術識別碼</label>
   <input type="search" id="catalogSearch" placeholder="搜尋引擎或模組">
   <label class="check-row"><input type="checkbox" id="showTechnicalIds">
    <span>顯示技術識別碼</span></label>
  </details>
  <nav class="system-links" aria-label="子系統入口">
   <a href="VIA_UI_Shell_CGC_v0100.html">中央治理系統</a>
   <a href="VIA_UI_Shell_VDF_v0100.html">資料擷取與鍛造系統</a>
   <a href="VIA_UI_Shell_VRN_v0100.html">研究報告解析系統</a>
   <a href="VIA_UI_Shell_VAP_v0100.html">視覺分析與自動繪圖系統</a>
  </nav>
 </div>
 <div class="rail-log"><div class="section-kicker">操作紀錄</div>
  <pre id="log" aria-live="polite">待命。尚未執行任何工作。</pre></div>
</aside>
<button type="button" id="railBackdrop" class="rail-backdrop"
 aria-label="關閉執行輸入" hidden></button>
<main class="workspace" id="workspace">
 <div class="workspace-heading"><div>
  <div class="eyebrow">VIA 母系統 / 系統運轉與分析</div>
  <h2>現況輸入與運轉結果</h2>
  <p>真實狀態取自本機指揮台；沒有來源資料時顯示待命或缺料，不顯示假綠。</p></div>
  <div class="snapshot"><span>畫面產生時間</span><b>{html.escape(d['ts'])}</b></div>
 </div>
 <nav class="view-tabs" id="viewTabs" role="tablist" aria-label="總控台報告分頁">
  <button role="tab" id="tab-overview" aria-controls="panel-overview" aria-selected="true">運轉總覽</button>
  <button role="tab" id="tab-matrix" aria-controls="panel-matrix" aria-selected="false" tabindex="-1">結果矩陣</button>
  <button role="tab" id="tab-plotly" aria-controls="panel-plotly" aria-selected="false" tabindex="-1">分析圖表</button>
  <button role="tab" id="tab-engines" aria-controls="panel-engines" aria-selected="false" tabindex="-1">引擎清單</button>
  <button role="tab" id="tab-modules" aria-controls="panel-modules" aria-selected="false" tabindex="-1">模組清單</button>
  <button role="tab" id="tab-plan" aria-controls="panel-plan" aria-selected="false" tabindex="-1">讀取規劃</button>
  <button role="tab" id="tab-links" aria-controls="panel-links" aria-selected="false" tabindex="-1">系統連線</button>
 </nav>
 <section class="tab-panel" id="panel-overview" role="tabpanel" aria-labelledby="tab-overview">
  <div class="stats">
   <article class="stat"><b>{len(tasks)}</b><span>正式工作項目</span></article>
   <article class="stat"><b>{active_engines}</b><span>現役引擎族</span></article>
   <article class="stat"><b>{len(module_rows)}</b><span>中央治理模組</span></article>
   <article class="stat muted"><b>{retired_engines}</b><span>退役存證引擎</span></article>
  </div>
  <div class="overview-grid">
   <article class="card"><div class="card-head"><div><span class="section-kicker">目前輸入</span>
    <h3>送入引擎前的參數摘要</h3></div>
    <span id="inputStateBadge" class="honesty">尚未送出</span></div>
    <div class="table-wrap"><table class="summary-table"><tbody>
     <tr><th>工作項目</th><td id="summaryTask">—</td></tr>
     <tr><th>股票代號</th><td id="summaryCodes">不適用</td></tr>
     <tr><th>日期範圍</th><td id="summaryDates">不適用</td></tr>
     <tr><th>資料分類</th><td id="summaryCategories">不適用</td></tr>
     <tr><th>批次工作</th><td id="summaryBatch">未勾選</td></tr>
     <tr><th>待收文件</th><td id="summaryFiles">0 件</td></tr>
    </tbody></table></div>
   </article>
   <article class="card"><div class="card-head"><div><span class="section-kicker">運轉分布</span>
    <h3>本機指揮台即時狀態</h3></div><span id="statusSource" class="honesty">等待連線</span></div>
    <div id="statusDistribution" class="status-distribution" aria-label="任務狀態分布"></div>
    <div id="overviewEmpty" class="inline-empty">尚未取得運轉狀態。</div>
   </article>
  </div>
  <article class="card"><div class="card-head"><div><span class="section-kicker">選定結果</span>
   <h3 id="selectedResultTitle">尚未選取工作</h3></div><span id="selectedResultState" class="honesty">待命</span></div>
   <pre id="result">請在「結果矩陣」選取工作，或從左側執行一項工作。</pre>
  </article>
 </section>
 <section class="tab-panel" id="panel-matrix" role="tabpanel" aria-labelledby="tab-matrix" hidden>
  <article class="card"><div class="card-head"><div><span class="section-kicker">矩陣報告</span>
   <h3>工作狀態、進度、結果與解決建議</h3></div><span>每 4 秒更新</span></div>
   <div id="matrixNotice" class="notice" aria-live="polite">正在連接本機指揮台…</div>
   <div class="table-wrap"><table class="matrix-table" id="statusMatrix">
    <thead><tr><th>正式工作名稱</th><th>狀態</th><th>開始</th><th>經過</th>
     <th>心跳延遲</th><th>紀錄</th><th>完成／進度</th><th>回傳碼</th><th>解決建議</th></tr></thead>
    <tbody id="statusMatrixBody"><tr><td colspan="9">尚未取得資料。</td></tr></tbody>
   </table></div>
  </article>
 </section>
 <section class="tab-panel" id="panel-plotly" role="tabpanel" aria-labelledby="tab-plotly" hidden>
  <article class="card plotly-card"><div class="card-head"><div><span class="section-kicker">Plotly Dashboard</span>
   <h3>標準金融分析儀表板</h3></div><span class="honesty">{plotly_state}</span></div>
   {plotly_view}
  </article>
 </section>
 <section class="tab-panel" id="panel-engines" role="tabpanel" aria-labelledby="tab-engines" hidden>
  <article class="card"><div class="card-head"><div><span class="section-kicker">引擎表列</span>
   <h3>現役與退役引擎治理清單</h3></div><span>{active_engines} 現役 · {retired_engines} 存證</span></div>
   <p class="notice">「已盤點」只代表 Atlas 找到檔案，不代表已註冊、通過測試或本次執行成功；
    真實運轉結果請見結果矩陣。候核名稱及候核序號只供人工核定，不冒充正式名稱。
    退役存證共 {retired_engines} 族，其中 1 族與現役正本同識別碼，主清單去重後列 {retired_unique} 族。</p>
   <div class="table-wrap roster-wrap"><table class="roster-table" id="engineTable">
    <thead><tr><th>正式名稱／候核名稱</th><th>所屬系統</th><th>功能分類</th><th>治理狀態</th><th class="tech-id">技術識別碼</th></tr></thead>
    <tbody>{engine_table}</tbody></table></div>
  </article>
 </section>
 <section class="tab-panel" id="panel-modules" role="tabpanel" aria-labelledby="tab-modules" hidden>
  <article class="card"><div class="card-head"><div><span class="section-kicker">模組表列</span>
   <h3>中央治理與支援模組清單</h3></div><span>{len(module_rows)} 個模組</span></div>
   <p class="notice">模組狀態只代表 Atlas 已盤點到檔案，不證明註冊、測試或啟用；
    未有人工核定名稱者顯示清洗後候核名稱及唯一候核序號。</p>
   <div class="table-wrap roster-wrap"><table class="roster-table" id="moduleTable">
    <thead><tr><th>正式名稱／候核名稱</th><th>功能分類</th><th>治理狀態</th><th class="tech-id">技術識別碼</th></tr></thead>
    <tbody>{module_table}</tbody></table></div>
  </article>
 </section>
 <section class="tab-panel" id="panel-plan" role="tabpanel" aria-labelledby="tab-plan" hidden>
  <article class="card"><div class="card-head"><div><span class="section-kicker">讀取與銜接規劃</span>
   <h3>從現況盤點到人工啟用的十階段治理流程</h3></div><span>{ACTIVATION_STATE}</span></div>
   <div class="plan-flow" aria-label="系統讀取規劃">
    <span>環境確認</span><i>→</i><span>自動盤點</span><i>→</i><span>契約分類</span>
    <i>→</i><span>介面銜接</span><i>→</i><span>驗證矩陣</span><i>→</i><span>人工審查</span>
   </div>
   <div class="table-wrap"><table class="plan-table"><thead><tr><th>階段</th><th>正式名稱</th>
    <th>輸入／處理／輸出</th><th>目前狀態</th></tr></thead><tbody>{plan_table}</tbody></table></div>
  </article>
 </section>
 <section class="tab-panel" id="panel-links" role="tabpanel" aria-labelledby="tab-links" hidden>
  <div class="link-grid">
   <article class="card"><span class="section-kicker">本機指揮台</span><h3>白名單執行橋</h3>
    <div class="table-wrap"><table><tbody>
     <tr><th>健康檢測</th><td><code>GET /ping</code></td></tr>
     <tr><th>工作執行</th><td><code>POST /run</code></td></tr>
     <tr><th>狀態矩陣</th><td><code>GET /status</code></td></tr>
     <tr><th>文件收件</th><td><code>POST /intake</code></td></tr>
    </tbody></table></div></article>
   <article class="card"><span class="section-kicker">上船件冊(批336)</span><h3>今日上船七件 × 整合鏈</h3>
    <p><a href="VIA_UI_IntakeRoster_v0100.html">上船件冊 IntakeRoster</a> · <a href="VIA_UI_StoryRotation_v0100.html">故事族群輪動 v0.5</a> · <a href="VIA_UI_VapStack_v0100.html">Seaborn 圖組 VapStack</a> · <a href="VIA_UI_System_v0100.html">系統總台 System</a> · <a href="VIA_UI_GovernanceConsole_v0100.html">中央治理主控台</a></p>
    <p class="notice">收容包=references/intake(hash 冊;原件零觸碰);整合點逐件驗在位。</p></article>
   <article class="card"><span class="section-kicker">啟動方式</span><h3>Windows 與 PowerShell</h3>
    <p>先執行 <code>via</code> 或 <code>VIA-ALL</code> 帶起本機指揮台，
    再使用左側工作項目。總控頁再生：<code>via-manager</code>。</p>
    <p class="notice">執行閘只接受任務冊白名單；本頁不接受任意命令。</p></article>
  </div>
 </section>
</main></div>
<footer class="app-footer" id="appFooter">
 <span>VIA · 真值直取 · 零 CDN · 本機白名單</span>
 <span id="footerConnection">指揮台：尚未檢測</span>
 <span>啟用狀態：{ACTIVATION_STATE}</span>
</footer>
<script>__APPJS__
__STATUSJS__
__DROPJS__
</script></body></html>"""


MCSS = r"""
:root{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;
--ink2:#465365;--mut:#596778;--mut2:#5d6a7b;--line:#dfe4ea;
--line2:#edf0f3;--soft:#eef3f6;--acc:#315f7d;--acc2:#dce9f1;
--ok:#2f7652;--warn:#765418;--bad:#a64f46;--retired:#6e6077;
--header-h:48px;--footer-h:28px;--rail-w:260px;--radius:8px;
--shadow:0 8px 24px rgba(32,40,51,.07)}
*{box-sizing:border-box}
[hidden]{display:none!important}
[inert]{pointer-events:none;user-select:none}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink)}
body{overflow-x:hidden;font:11px/1.45 "Segoe UI","Noto Sans TC",Inter,
system-ui,sans-serif}
button,input,select{font:inherit;color:inherit}
button,input,select,[role=tab],#drop{outline:none}
button:focus-visible,input:focus-visible,select:focus-visible,[role=tab]:focus-visible,
#drop:focus-visible,a:focus-visible{box-shadow:0 0 0 3px rgba(49,95,125,.22);
border-color:var(--acc)!important}
button{min-height:38px;border:1px solid var(--line);border-radius:7px;
background:var(--paper);cursor:pointer;padding:6px 10px}
button:hover{border-color:#aeb9c5;background:var(--paper2)}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:700}
button.primary:hover{background:#264f6a}
button.quiet{min-height:32px;color:var(--acc);background:transparent}
button:disabled{opacity:.55;cursor:not-allowed}
code,pre,.tech-id{font-family:"DM Mono",Consolas,"SFMono-Regular",monospace}
code{font-size:10px;color:var(--acc);overflow-wrap:anywhere}
.app-header{position:fixed;z-index:80;inset:0 0 auto 0;height:var(--header-h);
display:flex;align-items:center;gap:12px;padding:0 14px;background:rgba(255,255,255,.97);
border-bottom:1px solid var(--line);backdrop-filter:blur(10px)}
.rail-toggle{display:flex;align-items:center;gap:7px;min-height:32px;padding:4px 9px;
border-color:var(--line);background:var(--paper2);font-weight:700}
.identity{display:flex;align-items:center;gap:8px;min-width:0}
.seal{width:27px;height:27px;display:grid;place-items:center;background:#9b3d35;
color:#fff;border-radius:5px;font:700 14px/1 "Noto Serif TC",serif;flex:none}
.product{font-size:12px;font-weight:800;letter-spacing:.025em;white-space:nowrap}
.motto{font-size:9px;color:var(--mut);letter-spacing:.1em}
.header-meta{margin-left:auto;display:flex;align-items:center;gap:7px}
.build,.connection,.honesty{display:inline-flex;align-items:center;min-height:23px;
padding:2px 8px;border:1px solid var(--line);border-radius:999px;background:var(--paper2);
font-size:9.5px;font-weight:700;color:var(--mut);white-space:nowrap}
.connection::before{content:"";width:7px;height:7px;border-radius:50%;margin-right:5px;
background:var(--mut2)}
.connection.online{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}
.connection.online::before{background:var(--ok)}
.connection.offline{color:var(--bad);border-color:#e3c0bc;background:#fff5f3}
.connection.offline::before{background:var(--bad)}
.connection.invalid{color:var(--bad);border-color:#e3c0bc;background:#fff5f3}
.connection.invalid::before{background:var(--bad)}
.honesty.ok{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}
.honesty.running{color:var(--warn);border-color:#e2cfaa;background:#fff9eb}
.honesty.fail,.honesty.blocked,.honesty.offline{color:var(--bad);border-color:#e3c0bc;
background:#fff5f3}
.honesty.stale{color:var(--mut);border-color:#cbd2da;background:#f1f3f5}
.app-shell{min-height:100vh}
.control-rail{position:fixed;z-index:60;left:0;top:var(--header-h);bottom:var(--footer-h);
width:var(--rail-w);display:flex;flex-direction:column;background:var(--paper);
border-right:1px solid var(--line);transition:transform .22s ease,width .22s ease;
box-shadow:4px 0 18px rgba(32,40,51,.03)}
.rail-scroll{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:9px}
.rail-section{margin:0 0 8px;padding:10px;border:1px solid var(--line);
border-radius:var(--radius);background:var(--paper)}
.rail-section h1{font-size:14px;line-height:1.25;margin:2px 0 3px}
.section-kicker,.eyebrow{font-size:8.5px;font-weight:800;letter-spacing:.17em;
text-transform:uppercase;color:var(--mut2)}
.rail-note{font-size:9.5px;color:var(--mut);margin:4px 0 8px}
.rail-section>label,.conditional-field label,.date-pair label{display:block;margin:7px 0 3px;
font-size:9.5px;font-weight:700;color:var(--ink2)}
.rail-section select,.rail-section input[type=text],.rail-section input[type=search],
.rail-section input[type=date]{width:100%;min-height:36px;border:1px solid var(--line);
border-radius:6px;background:var(--paper);padding:6px 8px}
.conditional-field small,#drop small{display:block;color:var(--mut);font-size:9px;margin-top:3px}
.validation-message{margin-top:7px;padding:6px 7px;border:1px solid #e3c0bc;
border-radius:6px;background:#fff5f3;color:var(--bad);font-size:9.5px;font-weight:700}
[aria-invalid=true]{border-color:var(--bad)!important;background:#fff8f7!important}
.date-pair{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.rail-actions{display:grid;grid-template-columns:1.35fr .8fr;gap:6px;margin-top:9px}
.rail-actions.compact{grid-template-columns:1fr 1fr;margin-top:6px}
.rail-section summary{cursor:pointer;font-weight:750;color:var(--ink2);padding:1px 0;
list-style-position:outside}
.rail-section summary span{float:right;color:var(--mut2);font-size:8.5px;
letter-spacing:.08em;text-transform:uppercase}
.check-row{display:flex!important;align-items:flex-start;gap:7px;margin:5px 0!important;
font-size:10px!important;font-weight:500!important;cursor:pointer}
.check-row input{accent-color:var(--acc);margin:2px 0 0;flex:none}
.full{width:100%;margin-top:8px}
#drop{border:1.5px dashed #b9c3cd;border-radius:7px;padding:13px 8px;text-align:center;
color:var(--ink2);cursor:pointer;background:var(--paper2)}
#drop.on{border-color:var(--acc);background:#eef6fa;color:var(--acc)}
.file-results{list-style:none;padding:0;margin:7px 0 0;max-height:120px;overflow:auto}
.file-results li{padding:4px 0;border-bottom:1px solid var(--line2);font-size:9.5px;
overflow-wrap:anywhere}
.system-links{display:grid;grid-template-columns:1fr 1fr;gap:5px;padding:1px}
.system-links a{display:flex;align-items:center;min-height:34px;padding:6px 7px;
border:1px solid var(--line);border-radius:6px;color:var(--ink2);text-decoration:none;
font-size:9.5px;background:var(--paper)}
.system-links a:hover{border-color:#b7c3ce;color:var(--acc)}
.rail-log{flex:none;padding:8px 9px;border-top:1px solid var(--line);background:var(--paper2)}
#log{margin:4px 0 0;max-height:92px;overflow:auto;white-space:pre-wrap;
font-size:9px;color:var(--ink2)}
.workspace{min-width:0;width:auto;margin-left:var(--rail-w);padding:calc(var(--header-h) + 14px)
16px calc(var(--footer-h) + 16px);transition:margin-left .22s ease}
body[data-rail=collapsed] .control-rail{transform:translateX(-100%)}
body[data-rail=collapsed] .workspace{margin-left:0}
.rail-backdrop{display:none;position:fixed;z-index:50;inset:var(--header-h) 0 var(--footer-h) 0;
width:100%;height:auto;border:0;border-radius:0;background:rgba(32,40,51,.18);padding:0}
.rail-backdrop:focus-visible{box-shadow:inset 0 0 0 3px rgba(49,95,125,.55)}
.workspace-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;
padding:0 2px 10px}
.design-template-banner{margin:0 0 9px;padding:8px 10px;border:1px solid #d7bd86;
border-radius:7px;background:#fff8e7;color:#785a20;font-weight:750}
.workspace-heading h2{font-size:18px;margin:2px 0 1px}
.workspace-heading p{margin:0;color:var(--mut);font-size:10px}
.snapshot{text-align:right;white-space:nowrap;color:var(--mut);font-size:9px}
.snapshot b{display:block;color:var(--ink2);font-size:10.5px}
.view-tabs{position:sticky;z-index:40;top:var(--header-h);display:flex;gap:3px;
overflow-x:auto;padding:5px;background:rgba(244,246,248,.96);border:1px solid var(--line);
border-radius:8px;margin-bottom:9px;backdrop-filter:blur(8px)}
.view-tabs button{min-height:32px;flex:0 0 auto;border-color:transparent;background:transparent;
padding:5px 10px;color:var(--mut);font-weight:700}
.view-tabs button[aria-selected=true]{background:var(--paper);border-color:var(--line);
color:var(--ink);box-shadow:0 2px 7px rgba(32,40,51,.05)}
.tab-panel[hidden]{display:none}
.stats{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:7px;margin-bottom:8px}
.stat{display:flex;align-items:baseline;gap:8px;background:var(--paper);border:1px solid var(--line);
border-radius:var(--radius);padding:8px 10px;box-shadow:0 2px 8px rgba(32,40,51,.025)}
.stat b{font-size:20px;font-variant-numeric:tabular-nums}
.stat span{font-size:9.5px;color:var(--mut)}
.stat.muted b{color:var(--retired)}
.overview-grid,.link-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.card{min-width:0;margin-bottom:8px;padding:11px 12px;background:var(--paper);
border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}
.card h3{font-size:12px;margin:2px 0;color:var(--ink)}
.card p{color:var(--ink2)}
.card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;
padding-bottom:7px;border-bottom:1px solid var(--line2);margin-bottom:7px}
.card-head>span:not(.honesty){font-size:9px;color:var(--mut);white-space:nowrap}
.table-wrap{width:100%;max-width:100%;overflow:auto;overscroll-behavior:contain}
table{width:100%;border-collapse:collapse;font-size:10px}
th,td{padding:6px 7px;text-align:left;border-bottom:1px solid var(--line2);
vertical-align:top;overflow-wrap:anywhere}
thead th{position:sticky;top:0;background:var(--paper2);z-index:2;color:var(--mut);
font-size:8.5px;letter-spacing:.04em;white-space:nowrap}
tbody tr:hover{background:#fafcfd}
.summary-table th{width:100px;color:var(--mut);font-weight:650}
.summary-table td{font-weight:650;color:var(--ink2)}
.status-distribution{display:grid;gap:6px;margin-top:6px}
.dist-row{display:grid;grid-template-columns:62px 1fr 30px;align-items:center;gap:7px}
.dist-label{font-size:9.5px;color:var(--ink2)}
.dist-track{height:8px;background:var(--line2);border-radius:99px;overflow:hidden}
.dist-fill{height:100%;min-width:0;border-radius:99px;transition:width .35s ease}
.dist-fill.idle{background:var(--mut2)}.dist-fill.running{background:var(--warn)}
.dist-fill.ok{background:var(--ok)}.dist-fill.fail{background:var(--bad)}
.status-distribution.stale .dist-fill{background:var(--mut)!important}
.dist-count{text-align:right;font-variant-numeric:tabular-nums;font-weight:700}
.inline-empty,.empty-state{color:var(--mut);text-align:center;padding:22px 12px}
#result{min-height:96px;max-height:260px;margin:0;overflow:auto;white-space:pre-wrap;
background:var(--paper2);border:1px solid var(--line);border-radius:6px;padding:9px;
font-size:9.5px;color:var(--ink2)}
.notice{padding:7px 9px;margin:6px 0;background:var(--paper2);border:1px solid var(--line);
border-radius:6px;color:var(--mut);font-size:9.5px}
.matrix-table{min-width:1040px}
.matrix-table tbody tr{cursor:pointer}
.matrix-table tbody tr:focus-within{outline:2px solid var(--acc);outline-offset:-2px}
.task-link{min-height:28px;padding:2px 5px;border:0;background:transparent;color:var(--acc);
font-weight:700;text-align:left}
.state-pill{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;font-weight:750}
.state-pill::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--mut2)}
.state-pill.running{color:var(--warn)}.state-pill.running::before{background:var(--warn)}
.state-pill.ok{color:var(--ok)}.state-pill.ok::before{background:var(--ok)}
.state-pill.fail{color:var(--bad)}.state-pill.fail::before{background:var(--bad)}
.state-pill.stale{color:var(--mut)}.state-pill.stale::before{background:var(--mut)}
.matrix-table tbody tr.stale{background:#f3f5f7;color:var(--mut)}
.matrix-table tbody tr.stale .task-link{color:var(--mut)}
.matrix-table tbody tr.stale .progress-fill{background:var(--mut)!important}
.progress-cell{min-width:110px}.progress-track{height:5px;background:var(--line2);
border-radius:9px;overflow:hidden;margin-top:3px}.progress-fill{height:100%;background:var(--acc)}
.roster-wrap{max-height:calc(100vh - 225px)}
.roster-table{min-width:780px}.roster-table td:first-child{font-weight:700;color:var(--ink2)}
.tech-id{display:none!important;font-size:8.5px;color:var(--mut)}
body.show-tech .tech-id{display:table-cell!important}
.plotly-card{min-height:calc(100vh - 155px)}
#plotlyFrame{width:100%;height:calc(100vh - 205px);min-height:520px;border:1px solid var(--line);
border-radius:7px;background:#fff}
.plotly-ready-note{font-size:9px;color:var(--mut);margin-bottom:6px}
.empty-state{max-width:620px;margin:6vh auto}.empty-state h3{font-size:15px}
.empty-state p{font-size:10.5px;line-height:1.65}.empty-icon{display:block;font-size:30px;color:var(--mut2)}
.plan-flow{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 0 10px}
.plan-flow span{padding:5px 8px;border:1px solid var(--line);border-radius:999px;
background:var(--paper2);font-size:9.5px;font-weight:700}.plan-flow i{color:var(--mut2)}
.plan-table{min-width:780px}.plan-table td:first-child{font-weight:800;color:var(--acc)}
.app-footer{position:fixed;z-index:90;inset:auto 0 0 0;height:var(--footer-h);
display:flex;align-items:center;justify-content:space-between;gap:12px;padding:0 12px;
background:#eef1f4;border-top:1px solid var(--line);color:var(--ink2);font-size:8.5px;
letter-spacing:.025em}
body[data-preview-only=true] #drop{cursor:not-allowed;opacity:.72}
body[data-preview-only=true] .design-template-banner{border-color:#bd8743;background:#fff6dd;
color:#684b15}
@media(max-width:960px){.stats{grid-template-columns:1fr 1fr}.overview-grid,.link-grid{grid-template-columns:1fr}}
@media(max-width:768px){
 :root{--rail-w:min(320px,calc(100vw - 42px))}
 .control-rail{box-shadow:10px 0 28px rgba(32,40,51,.18)}
 .workspace{margin-left:0;padding-left:9px;padding-right:9px}
 body[data-rail=open]{overflow:hidden}
 body[data-rail=open] .rail-backdrop{display:block;left:var(--rail-w);width:calc(100vw - var(--rail-w))}
 .header-meta .build{display:none}.product{font-size:10.5px}.motto{display:none}
 .workspace-heading{align-items:flex-start}.snapshot{display:none}
 .view-tabs{margin-left:-2px;margin-right:-2px}
 .app-footer span:first-child{display:none}.app-footer{justify-content:space-between}
}
@media(max-width:460px){
 .rail-toggle span:last-child{position:absolute;width:1px;height:1px;padding:0;margin:-1px;
  overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
 .identity{gap:6px}.connection{max-width:105px;overflow:hidden}
 .stats{grid-template-columns:1fr 1fr}.stat{display:block}.stat b{font-size:17px;display:block}
 .workspace-heading h2{font-size:15px}.workspace-heading p{font-size:9px}
 .date-pair{grid-template-columns:1fr}.app-footer{font-size:8.5px}
}
@media(max-width:360px){.product{max-width:92px;overflow:hidden;text-overflow:ellipsis}
 .app-header{gap:8px;padding-left:8px;padding-right:8px}.header-meta{gap:3px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
@media print{.app-header,.control-rail,.app-footer,.view-tabs{position:static!important;display:none!important}
 .workspace{margin:0;padding:0}.tab-panel[hidden]{display:block}.card{box-shadow:none;break-inside:avoid}}
"""

APPJS = r"""
"use strict";
const BRIDGE_ORIGIN="http://127.0.0.1:8765";
const API_BASE=location.origin===BRIDGE_ORIGIN?location.origin:BRIDGE_ORIGIN;
const PKEY="via_master_params";
const RAIL_KEY="via_master_rail";
const TAB_KEY="via_master_tab";
const TASK_IDS=new Set([...document.querySelectorAll("#task option")].map(item=>item.value));
const EDITABLE_PREVIEW=document.body.dataset.editableTemplate==="true";
const LIVE_SAME_ORIGIN=location.origin===BRIDGE_ORIGIN;
const CSRF_TOKEN=(document.querySelector('meta[name="via-csrf"]')?.content||"").trim();
const HAS_LIVE_TOKEN=/^[A-Za-z0-9_-]{20,200}$/.test(CSRF_TOKEN)
 && !CSRF_TOKEN.startsWith("__VIA_");
const DEFAULT_RUN_TIMEOUT_MS=45*60*1000;
const LONG_RUN_TIMEOUTS={boot:2*60*60*1000,backfill:2*60*60*1000,
 rebuild_full:90*60*1000,ocr_plan:60*60*1000};
const GLOBAL_CATEGORIES=new Set(["idx","etf","us_jp","fin_reports","oil","fx",
 "cmdty","crypto","us_macro","fed","us_fiscal_rates"]);
let pendingFileCount=0;
let executionMutex=null;
let lastSubmittedTask=null;
let connectionRevision=0;
let appliedConnectionRevision=0;
let railIsMobile=matchMedia("(max-width:768px)").matches;

function byId(id){return document.getElementById(id);}
function plainObject(value){
 return Boolean(value)&&typeof value==="object"&&!Array.isArray(value)
  && Object.getPrototypeOf(value)===Object.prototype;
}
class ApiError extends Error{
 constructor(kind,message,status=0){super(message);this.name="ApiError";this.kind=kind;this.status=status;}
}
function logLine(message){
 const el=byId("log");
 const stamp=new Date().toLocaleTimeString("zh-TW",{hour12:false});
 el.textContent+=(el.textContent?"\n":"")+"["+stamp+"] "+message;
 el.scrollTop=el.scrollHeight;
}
function taskFormalName(taskId){
 const option=[...byId("task").options].find(item=>item.value===taskId);
 return option?option.textContent.trim():"未命名工作";
}
function beginConnectionObservation(){return ++connectionRevision;}
function updateConnectionState(state,detail,revision=connectionRevision){
 if(revision<appliedConnectionRevision)return;
 appliedConnectionRevision=revision;
 const head=byId("bridgeState");
 const foot=byId("footerConnection");
 head.className="connection "+state;
 if(state==="online"){
  head.textContent="本機指揮台在線";
  foot.textContent="指揮台：在線"+(detail?" · "+detail:"");
 }else if(state==="offline"){
  head.textContent="本機指揮台離線";
  foot.textContent="指揮台：離線 · 狀態可能過期";
 }else if(state==="invalid"){
  head.textContent="指揮台回應異常";
  foot.textContent="指揮台：回應格式異常 · 不採信";
 }else{
  head.textContent="連線尚未檢測";
  foot.textContent="指揮台：尚未檢測";
 }
}
function isMobileRail(){return matchMedia("(max-width:768px)").matches;}
function applyRailIsolation(open,moveFocus=false){
 const mobile=isMobileRail();
 const rail=byId("controlRail");
 const backdrop=byId("railBackdrop");
 rail.inert=!open;
 rail.setAttribute("aria-hidden",String(!open));
 if(mobile&&open){
  rail.setAttribute("role","dialog");rail.setAttribute("aria-modal","true");
  byId("workspace").inert=true;byId("appFooter").inert=true;
  backdrop.hidden=false;
  if(moveFocus)setTimeout(()=>byId("task").focus(),0);
 }else{
  rail.removeAttribute("role");rail.removeAttribute("aria-modal");
  byId("workspace").inert=false;byId("appFooter").inert=false;
  backdrop.hidden=true;
 }
}
function toggleRail(force,persist=true,moveFocus=false){
 const body=document.body;
 const open=force!==undefined?Boolean(force):body.dataset.rail!=="open";
 body.dataset.rail=open?"open":"collapsed";
 byId("railToggle").setAttribute("aria-expanded",String(open));
 applyRailIsolation(open,moveFocus&&open);
 if(persist){try{localStorage.setItem(RAIL_KEY,open?"open":"collapsed");}catch(_) {}}
 if(!open&&moveFocus)byId("railToggle").focus();
 resizePlotlyFrame();
}
function activateTab(tabId,moveFocus=false){
 const tab=byId(tabId);
 if(!tab||tab.getAttribute("role")!=="tab")return;
 document.querySelectorAll('[role="tab"]').forEach(item=>{
  const active=item===tab;
  item.setAttribute("aria-selected",String(active));
  item.tabIndex=active?0:-1;
  const panel=byId(item.getAttribute("aria-controls"));
  if(panel)panel.hidden=!active;
 });
 if(moveFocus)tab.focus();
 try{localStorage.setItem(TAB_KEY,tabId);}catch(_) {}
 if(tabId==="tab-plotly")resizePlotlyFrame();
}
function setupTabs(){
 const tabs=[...document.querySelectorAll('[role="tab"]')];
 tabs.forEach((tab,index)=>{
  tab.addEventListener("click",()=>activateTab(tab.id));
  tab.addEventListener("keydown",event=>{
   let next=index;
   if(event.key==="ArrowRight")next=(index+1)%tabs.length;
   else if(event.key==="ArrowLeft")next=(index-1+tabs.length)%tabs.length;
   else if(event.key==="Home")next=0;
   else if(event.key==="End")next=tabs.length-1;
   else return;
   event.preventDefault();activateTab(tabs[next].id,true);
  });
 });
 try{activateTab(localStorage.getItem(TAB_KEY)||"tab-overview");}
 catch(_){activateTab("tab-overview");}
}
function selectedTaskContract(){
 const option=byId("task").selectedOptions[0];
 return {codes:option?.dataset.codes==="true",range:option?.dataset.range==="true",
  cats:option?.dataset.cats==="true"};
}
function taskContract(taskId){
 const option=[...byId("task").options].find(item=>item.value===taskId);
 return {codes:option?.dataset.codes==="true",range:option?.dataset.range==="true",
  cats:option?.dataset.cats==="true"};
}
function setInputBadge(text,state=""){
 const badge=byId("inputStateBadge");badge.textContent=text;
 badge.className="honesty"+(state?" "+state:"");
}
function markInputEdited(){
 if(!executionMutex)setInputBadge("已修改・尚未送出");
 clearValidation();
}
function updateParameterVisibility(){
 const contract=selectedTaskContract();
 byId("codesField").hidden=!contract.codes;
 byId("dateRangeField").hidden=!contract.range;
 byId("categoriesField").hidden=!contract.cats;
 byId("parameterHint").textContent=contract.codes||contract.range||contract.cats
  ?"以下只顯示此工作需要的參數。":"此工作不需要額外輸入，可直接執行。";
 syncInputSummary();
}
function collectParams(){
 const contract=selectedTaskContract();
 return {task:byId("task").value,
  codes:contract.codes?byId("codes").value.trim():"",
  start:contract.range?byId("dateStart").value:"",
  end:contract.range?byId("dateEnd").value:"",
  cats:contract.cats?byId("categories").value.trim():""};
}
function syncInputSummary(){
 const params=collectParams();
 const checked=[...document.querySelectorAll('#batchChecks input:checked')]
  .map(item=>taskFormalName(item.value));
 byId("summaryTask").textContent=taskFormalName(params.task);
 byId("summaryCodes").textContent=params.codes||"不適用";
 byId("summaryDates").textContent=params.start||params.end
  ?(params.start||"未設定")+" 至 "+(params.end||"未設定"):"不適用";
 byId("summaryCategories").textContent=params.cats||"不適用";
 byId("summaryBatch").textContent=checked.length?checked.join("、"):"未勾選";
 byId("summaryFiles").textContent=pendingFileCount+" 件";
}
function clearValidation(){
 const message=byId("inputValidation");message.hidden=true;message.textContent="";
 for(const id of ["task","codes","dateStart","dateEnd","categories"])
  byId(id).removeAttribute("aria-invalid");
}
function showValidation(errors){
 clearValidation();if(!errors.length)return;
 const message=byId("inputValidation");message.textContent=errors.map(x=>x.message).join("；");
 message.hidden=false;
 errors.forEach(error=>byId(error.id)?.setAttribute("aria-invalid","true"));
 byId(errors[0].id)?.focus();
}
function validateTaskParams(taskId,source){
 const contract=taskContract(taskId);const errors=[];
 const params={task:taskId,codes:"",start:"",end:"",cats:""};
 if(!TASK_IDS.has(taskId))errors.push({id:"task",message:"工作項目不在本頁白名單"});
 if(contract.codes){
  const raw=String(source.codes||"").trim();
  if(raw){
   const tokens=raw.split(/[\s,，]+/).filter(Boolean);
   if(raw.length>349||tokens.length>50||tokens.some(token=>!/^\d{4,6}$/.test(token)))
    errors.push({id:"codes",message:"股票代號須為最多 50 個 4–6 位數字"});
   else params.codes=[...new Set(tokens)].join(",");
  }
 }
 if(contract.range){
  params.start=String(source.start||"");params.end=String(source.end||"");
  if(Boolean(params.start)!==Boolean(params.end)){
   errors.push({id:params.start?"dateEnd":"dateStart",message:"日期範圍必須同時填寫開始與結束"});
  }else if(params.start&&(!validIsoDate(params.start)||!validIsoDate(params.end)
    ||params.start>params.end)){
   errors.push({id:"dateStart",message:"日期格式不正確，或開始日期晚於結束日期"});
  }
 }
 if(contract.cats){
  const raw=String(source.cats||"").trim().toLowerCase();
  const tokens=raw?raw.split(",").map(item=>item.trim()).filter(Boolean):[];
  if(raw&&(raw.length>80||!tokens.length||tokens.some(item=>
    !/^[a-z_]+$/.test(item)||!GLOBAL_CATEGORIES.has(item))))
   errors.push({id:"categories",message:"資料分類不在允許清單，或格式不正確"});
  else params.cats=[...new Set(tokens)].join(",");
 }
 return {ok:errors.length===0,params,errors};
}
function validIsoDate(value){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
 const parsed=new Date(value+"T00:00:00Z");
 return !Number.isNaN(parsed.getTime())&&parsed.toISOString().slice(0,10)===value;
}
function validateCurrentParams(){return validateTaskParams(byId("task").value,collectParams());}
function applyNormalizedParams(params){
 if(params.task!==byId("task").value)return;
 byId("codes").value=params.codes;byId("dateStart").value=params.start;
 byId("dateEnd").value=params.end;byId("categories").value=params.cats;
 syncInputSummary();
}
function validatePing(payload){
 const allowed=new Set(["ok","via","v","accel"]);
 if(!plainObject(payload)||Object.keys(payload).some(key=>!allowed.has(key))
   ||payload.ok!==true||payload.via!=="deck-bridge"||typeof payload.v!=="string"
   ||payload.v.length>40||typeof payload.accel!=="boolean")
  throw new ApiError("schema","健康檢測回應格式不符");
 return payload;
}
function validRunId(value){return typeof value==="string"&&/^[A-Za-z0-9._:-]{8,128}$/.test(value);}
function validateRunResponse(payload,expectedParams){
 if(!plainObject(payload)||typeof payload.ok!=="boolean")
  throw new ApiError("schema","執行回應格式不符");
 const allowed=new Set(["ok","run_id","accepted_params","err"]);
 if(Object.keys(payload).some(key=>!allowed.has(key)))
  throw new ApiError("schema","執行回應含契約外欄位");
 if(payload.ok&&!validRunId(payload.run_id))
  throw new ApiError("schema","執行回應缺少有效 run_id，為避免誤判已停止監看");
 if(payload.ok){
  const accepted=payload.accepted_params;
  const fields=["task","codes","start","end","cats"];
  if(!plainObject(accepted)||Object.keys(accepted).length!==fields.length
    ||fields.some(key=>typeof accepted[key]!=="string"))
   throw new ApiError("schema","執行回應缺少完整 accepted_params");
  if(fields.some(key=>accepted[key]!==String(expectedParams[key]||"")))
   throw new ApiError("policy","指揮台接受參數與畫面送出參數不一致，已停止監看");
 }
 if(!payload.ok&&typeof payload.err!=="string")
  throw new ApiError("schema","拒絕回應缺少原因");
 if(typeof payload.err==="string"&&payload.err.length>800)
  throw new ApiError("schema","拒絕原因超過安全上限");
 return payload;
}
function boundedNumber(value,min,max){
 return typeof value==="number"&&Number.isFinite(value)&&value>=min&&value<=max;
}
function validateStatus(payload){
 if(!plainObject(payload)||Object.keys(payload).length>TASK_IDS.size)
  throw new ApiError("schema","狀態矩陣外層格式不符");
 const allowed=new Set(["zh","state","run_id","started","started_epoch","updated_at",
  "elapsed","beat","kb","done","pct","rc","fix","tail"]);
 for(const [taskId,item] of Object.entries(payload)){
  if(!TASK_IDS.has(taskId)||!plainObject(item)
    ||Object.keys(item).some(key=>!allowed.has(key)))
   throw new ApiError("schema","狀態矩陣含未知工作或欄位");
  if(!["idle","running","ok","fail"].includes(item.state))
   throw new ApiError("schema","狀態值不在契約內");
  if(item.state!=="idle"&&!validRunId(item.run_id))
   throw new ApiError("schema","運轉列缺少有效 run_id");
  for(const key of ["elapsed","beat","kb"])
   if(item[key]!=null&&!boundedNumber(item[key],0,1e12))
    throw new ApiError("schema",key+" 欄位格式不符");
  if(item.started_epoch!=null&&!boundedNumber(item.started_epoch,0,1e12))
   throw new ApiError("schema","started_epoch 欄位格式不符");
  if(item.pct!=null&&!boundedNumber(item.pct,0,100))
   throw new ApiError("schema","進度欄位超出 0–100");
  if(item.rc!=null&&(!Number.isInteger(item.rc)||Math.abs(item.rc)>1e9))
   throw new ApiError("schema","回傳碼格式不符");
  for(const key of ["zh","started","updated_at","fix","tail"])
   if(item[key]!=null&&(typeof item[key]!=="string"||item[key].length>(key==="tail"?2000:800)))
    throw new ApiError("schema",key+" 文字欄位格式不符");
  if(item.done!=null&&!(typeof item.done==="string"||boundedNumber(item.done,0,1e9)))
   throw new ApiError("schema","完成數欄位格式不符");
 }
 return payload;
}
function validateIntake(payload){
 const allowed=new Set(["ok","saved","sha256","skip","err"]);
 if(!plainObject(payload)||Object.keys(payload).some(key=>!allowed.has(key))
   ||typeof payload.ok!=="boolean")
  throw new ApiError("schema","收件回應格式不符");
 if(payload.ok&&(!/^[0-9a-f]{64}$/i.test(String(payload.sha256||""))
   ||typeof payload.saved!=="string"||payload.saved.length>1000
   ||(payload.skip!=null&&typeof payload.skip!=="string")))
  throw new ApiError("schema","收件成功回應缺少檔案證據");
 if(!payload.ok&&typeof payload.err!=="string")
  throw new ApiError("schema","收件拒絕回應缺少原因");
 if(typeof payload.err==="string"&&payload.err.length>800)
  throw new ApiError("schema","收件拒絕原因超過安全上限");
 return payload;
}
async function fetchJson(path,options={},timeoutMs=8000,validator=value=>value){
 const url=new URL(path,API_BASE+"/");
 if(url.origin!==BRIDGE_ORIGIN)throw new ApiError("policy","API 來源不在本機白名單");
 const controller=new AbortController();
 const timeout=setTimeout(()=>controller.abort(),timeoutMs);
 try{
  const response=await fetch(url,{cache:"no-store",credentials:"same-origin",
   redirect:"error",...options,signal:controller.signal});
  const text=await response.text();
  if(text.length>2_000_000)throw new ApiError("schema","API 回應超過安全上限");
  let value;try{value=JSON.parse(text);}catch(_){throw new ApiError("schema","回應不是有效 JSON");}
  if(!response.ok){
   const detail=plainObject(value)&&typeof value.err==="string"?value.err:"HTTP "+response.status;
   throw new ApiError("http",detail,response.status);
  }
  return validator(value);
 }catch(error){
  if(error?.name==="AbortError")throw new ApiError("timeout","本機指揮台回應逾時");
  if(error instanceof ApiError)throw error;
  throw new ApiError("network",error?.message||"本機指揮台無法連線");
 }finally{clearTimeout(timeout);}
}
function mutationAllowed(){return LIVE_SAME_ORIGIN&&HAS_LIVE_TOKEN&&!EDITABLE_PREVIEW;}
function setMutationControls(){
 const allowed=mutationAllowed();const busy=Boolean(executionMutex);
 for(const id of ["runOneButton","runBatchButton"])
  byId(id).disabled=!allowed||busy;
 byId("filePicker").disabled=!allowed||busy;
 byId("drop").setAttribute("aria-disabled",String(!allowed||busy));
 byId("drop").tabIndex=!allowed||busy?-1:0;
 document.body.dataset.previewOnly=String(!allowed);
}
function acquireExecution(owner){
 if(executionMutex){logLine("同頁已有工作或收件進行中，未重複送出。");return false;}
 executionMutex=owner;setMutationControls();return true;
}
function releaseExecution(owner){
 if(executionMutex===owner)executionMutex=null;
 setMutationControls();
}
function connectionStateForError(error,revision){
 updateConnectionState(["network","timeout"].includes(error.kind)?"offline":"invalid",
  error.message,revision);
}
async function callTask(taskId,params={},owner=executionMutex){
 if(!mutationAllowed()){
  const err="此頁是離線／設計預覽；請由本機指揮台 /master 開啟後操作";
  logLine(err);return {ok:false,err,policy:true};
 }
 if(!owner||executionMutex!==owner){
  const err="同頁執行鎖未取得，工作未送出";logLine(err);return {ok:false,err,policy:true};
 }
 const revision=beginConnectionObservation();
 try{
  const body={task:taskId,codes:params.codes||"",start:params.start||"",
   end:params.end||"",cats:params.cats||""};
  const result=await fetchJson("/run",{method:"POST",headers:{"Accept":"application/json",
   "Content-Type":"application/json","X-VIA-CSRF":CSRF_TOKEN},body:JSON.stringify(body)},
   10000,value=>validateRunResponse(value,body));
  updateConnectionState("online","",revision);
  logLine((result.ok?"已接受：":"拒絕：")+taskFormalName(taskId)
   +(result.err?" · "+result.err:""));
  return result;
 }catch(error){
  connectionStateForError(error,revision);
  logLine("無法送出「"+taskFormalName(taskId)+"」："+error.message+"。");
  return {ok:false,err:error.message,offline:["network","timeout"].includes(error.kind)};
 }
}
async function runOne(){
 const checked=validateCurrentParams();
 if(!checked.ok){showValidation(checked.errors);setInputBadge("輸入未通過驗證","fail");return;}
 clearValidation();const owner="single";if(!acquireExecution(owner))return;
 const params=checked.params;applyNormalizedParams(params);
 lastSubmittedTask=params.task;currentTask=params.task;
 setInputBadge("已送出・等待指揮台接受","running");syncInputSummary();
 try{
  const accepted=await callTask(params.task,params,owner);
  if(!accepted.ok){setInputBadge("未接受・請查看紀錄","fail");return;}
  setInputBadge("執行中・監看 run_id","running");
  showPendingResult(params.task,accepted.run_id);
  const terminal=await waitForTerminal(params.task,accepted.run_id,
   LONG_RUN_TIMEOUTS[params.task]||DEFAULT_RUN_TIMEOUT_MS);
  finishObservedExecution(params.task,terminal);
 }finally{releaseExecution(owner);}
}
function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}
async function waitForTerminal(taskId,runId,timeoutMs=DEFAULT_RUN_TIMEOUT_MS){
 if(!validRunId(runId))return {state:"unknown",observation_error:true,
  tail:"run_id 無效，未開始監看"};
 const started=Date.now();let consecutiveErrors=0;
 while(Date.now()-started<timeoutMs){
  const revision=beginConnectionObservation();
  try{
   const status=await fetchJson("/status",{},8000,validateStatus);
   consecutiveErrors=0;updateConnectionState("online","",revision);
   const item=status&&status[taskId];
   if(item&&item.run_id===runId&&["ok","fail"].includes(item.state))return item;
   if(item&&item.run_id!==runId&&item.state!=="idle")
    return {state:"unknown",observation_error:true,
     tail:"指揮台回傳另一個 run_id，為避免串錯執行已停止監看"};
  }catch(error){
   consecutiveErrors+=1;connectionStateForError(error,revision);
   logLine("等待工作完成時連線異常("+consecutiveErrors+"/3)："+error.message);
   if(consecutiveErrors>=3)return {state:"unknown",observation_error:true,
    tail:"連續三次無法可靠讀取狀態；工作可能仍在執行，請稍後重新檢測"};
  }
  await sleep(Date.now()-started<20000?1500:3000);
 }
 return {state:"unknown",observation_error:true,
  tail:"監看已達合理逾時上限；不判定工作失敗，請在結果矩陣重新確認"};
}
function showPendingResult(taskId,runId){
 byId("selectedResultTitle").textContent=taskFormalName(taskId);
 byId("selectedResultState").textContent="執行中";
 byId("selectedResultState").className="honesty running";
 byId("result").textContent="正式工作："+taskFormalName(taskId)+
  "\n狀態：已接受，等待 run_id 對應終態\n執行識別："+runId;
}
function finishObservedExecution(taskId,item){
 if(item.observation_error){
  setInputBadge("監看停止・狀態待確認","stale");
  byId("selectedResultTitle").textContent=taskFormalName(taskId);
  byId("selectedResultState").textContent="狀態待確認";
  byId("selectedResultState").className="honesty stale";
  byId("result").textContent="正式工作："+taskFormalName(taskId)+"\n\n"+item.tail;
  return;
 }
 setInputBadge(item.state==="ok"?"執行完成":"執行失敗",item.state);
 if(typeof lastStatus!=="undefined")lastStatus[taskId]=item;
 if(typeof selectResult==="function")selectResult(taskId);
}
async function runChecked(){
 const queue=[...document.querySelectorAll('#batchChecks input:checked')].map(item=>item.value);
 if(!queue.length){logLine("尚未勾選批次工作。");return;}
 const owner="batch";if(!acquireExecution(owner))return;
 setInputBadge("批次佇列執行中","running");
 logLine("依序佇列開始，共 "+queue.length+" 項；任一項失敗即停止。");
 try{
  for(const taskId of queue){
   logLine("準備執行："+taskFormalName(taskId));
   const source=taskId===byId("task").value?collectParams():{task:taskId};
   const checked=validateTaskParams(taskId,source);
   if(!checked.ok){
    showValidation(checked.errors);setInputBadge("批次停止・輸入未通過驗證","fail");
    logLine("佇列停止：輸入未通過驗證。");break;
   }
   applyNormalizedParams(checked.params);
   lastSubmittedTask=taskId;currentTask=taskId;
   const accepted=await callTask(taskId,checked.params,owner);
   if(!accepted.ok){
    setInputBadge("批次停止・工作未被接受","fail");
    logLine("佇列停止：工作未被接受。");break;
   }
   showPendingResult(taskId,accepted.run_id);
   const terminal=await waitForTerminal(taskId,accepted.run_id,
    LONG_RUN_TIMEOUTS[taskId]||DEFAULT_RUN_TIMEOUT_MS);
   finishObservedExecution(taskId,terminal);
   logLine("工作結束："+taskFormalName(taskId)+" · "+terminal.state);
   if(terminal.state!=="ok"){
    logLine("佇列依安全政策停止，後續工作未執行。");break;
   }
  }
 }finally{releaseExecution(owner);}
}
async function ping(){
 if(!LIVE_SAME_ORIGIN){
  logLine(EDITABLE_PREVIEW?"設計模板為預覽模式，不連接執行橋。":"離線頁僅供檢視；正在探測同源 /master。");
  if(!EDITABLE_PREVIEW)await preferSameOriginBridge();return;
 }
 const revision=beginConnectionObservation();
 try{
  const result=await fetchJson("/ping",{},5000,validatePing);
  updateConnectionState("online",result.v?"版本 "+result.v:"",revision);
  window.VIA_STATUS?.resume();
  logLine("本機指揮台連線正常"+(result.v?"，版本 "+result.v:"")+"。");
 }catch(error){
  connectionStateForError(error,revision);
  logLine("本機指揮台未連線："+error.message+"。請先執行 via 或 VIA-ALL。");
 }
}
function saveParams(){
 try{
  const checked=[...document.querySelectorAll('#batchChecks input:checked')]
   .map(item=>item.value);
  localStorage.setItem(PKEY,JSON.stringify({...collectParams(),checked}));
  logLine("參數已儲存於本機瀏覽器。");
 }catch(_){logLine("瀏覽器封存區不可用，參數未儲存。");}
}
function resetParams(){
 try{localStorage.removeItem(PKEY);}catch(_) {}
 byId("task").selectedIndex=0;
 for(const id of ["codes","dateStart","dateEnd","categories"])byId(id).value="";
 document.querySelectorAll('#batchChecks input').forEach(item=>item.checked=false);
 updateParameterVisibility();markInputEdited();logLine("已回復預設值。");
}
function restoreParams(){
 try{
  const saved=JSON.parse(localStorage.getItem(PKEY)||"null");
  if(!saved)return;
  if(saved.task)byId("task").value=saved.task;
  for(const [key,id] of [["codes","codes"],["start","dateStart"],["end","dateEnd"],
   ["cats","categories"]])if(saved[key])byId(id).value=saved[key];
  (saved.checked||[]).forEach(value=>{
   const item=document.querySelector('#batchChecks input[value="'+CSS.escape(value)+'"]');
   if(item)item.checked=true;
  });
  logLine("已回填上次儲存的參數。");
 }catch(_){logLine("已忽略無法解析的舊參數。");}
}
function filterCatalog(){
 const value=byId("catalogSearch").value.trim().toLowerCase();
 document.querySelectorAll('.roster-table tbody tr').forEach(row=>{
  row.hidden=Boolean(value)&&!row.dataset.search.includes(value);
 });
}
function toggleTechnicalIds(){
 document.body.classList.toggle("show-tech",byId("showTechnicalIds").checked);
}
function resizePlotlyFrame(){
 const frame=byId("plotlyFrame");if(!frame)return;
 setTimeout(()=>{try{
  const target=frame.contentWindow;
  if(target?.Plotly)target.document.querySelectorAll('.js-plotly-plot')
   .forEach(plot=>target.Plotly.Plots.resize(plot));
 }catch(_){}},260);
}
async function preferSameOriginBridge(){
 if(EDITABLE_PREVIEW||location.protocol!=="file:")return false;
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),1400);
 try{
  await fetch(BRIDGE_ORIGIN+"/probe",{mode:"no-cors",cache:"no-store",
   redirect:"follow",signal:controller.signal});
  location.replace(BRIDGE_ORIGIN+"/master");return true;
 }catch(_){return false;}finally{clearTimeout(timeout);}
}
function handleViewportChange(){
 const mobile=isMobileRail();
 if(mobile!==railIsMobile){
  railIsMobile=mobile;
  if(mobile)toggleRail(false,false,false);
  else{
   let saved="open";try{saved=localStorage.getItem(RAIL_KEY)||"open";}catch(_){}
   toggleRail(saved==="open",false,false);
  }
 }else applyRailIsolation(document.body.dataset.rail==="open",false);
 resizePlotlyFrame();
}
async function initialize(){
 setupTabs();restoreParams();updateParameterVisibility();syncInputSummary();
 let savedRail=null;try{savedRail=localStorage.getItem(RAIL_KEY);}catch(_) {}
 toggleRail(railIsMobile?false:(savedRail?savedRail==="open":true),false,false);
 byId("railToggle").addEventListener("click",()=>toggleRail(undefined,true,true));
 byId("railBackdrop").addEventListener("click",()=>toggleRail(false,true,true));
 document.addEventListener("keydown",event=>{
  if(event.key==="Escape"&&isMobileRail()&&document.body.dataset.rail==="open"){
   event.preventDefault();toggleRail(false,true,true);
  }
 });
 byId("task").addEventListener("change",()=>{updateParameterVisibility();markInputEdited();});
 for(const id of ["codes","dateStart","dateEnd","categories"])
  byId(id).addEventListener("input",()=>{syncInputSummary();markInputEdited();});
 document.querySelectorAll('#batchChecks input').forEach(item=>
  item.addEventListener("change",()=>{syncInputSummary();markInputEdited();}));
 byId("runOneButton").addEventListener("click",runOne);
 byId("runBatchButton").addEventListener("click",runChecked);
 byId("pingButton").addEventListener("click",ping);
 byId("saveParamsButton").addEventListener("click",saveParams);
 byId("resetParamsButton").addEventListener("click",resetParams);
 byId("catalogSearch").addEventListener("input",filterCatalog);
 byId("showTechnicalIds").addEventListener("change",toggleTechnicalIds);
 window.addEventListener("resize",handleViewportChange,{passive:true});
 setMutationControls();
 if(EDITABLE_PREVIEW){
  setInputBadge("設計預覽・禁止執行","stale");
  logLine("可編輯模板只供版面預覽；任務執行與文件收件已停用。");
 }else if(!mutationAllowed()){
  setInputBadge("離線檢視・請由 /master 操作","stale");
  await preferSameOriginBridge();
 }
}
initialize();
window.VIA_UI={activateTab,toggleRail,collectParams,callTask,waitForTerminal,
 updateConnectionState,syncInputSummary,filterCatalog,validateTaskParams,
 preferSameOriginBridge,getExecutionMutex:()=>executionMutex};
"""

DROPJS = r"""
const dropZone=byId("drop");
const filePicker=byId("filePicker");

function appendFileResult(message){
 const item=document.createElement("li");item.textContent=message;byId("files").append(item);
}
async function readFileBase64(file){
 return new Promise((resolve,reject)=>{
  const reader=new FileReader();
  reader.onload=()=>resolve(String(reader.result||"").split(",")[1]||"");
  reader.onerror=()=>reject(reader.error||new Error("檔案讀取失敗"));
  reader.readAsDataURL(file);
 });
}
async function processFiles(fileList){
 const files=[...fileList];
 byId("files").replaceChildren();
 if(!files.length){appendFileResult("沒有選取檔案。");return;}
 const owner="intake";
 if(!mutationAllowed()){
  appendFileResult("預覽頁禁止收件；請由本機指揮台 /master 開啟正式操作頁。");return;
 }
 if(!acquireExecution(owner)){
  appendFileResult("同頁已有工作或收件進行中，本次未送出。");return;
 }
 setInputBadge("文件收件處理中","running");
 pendingFileCount=files.length;syncInputSummary();
 appendFileResult("準備處理 "+files.length+" 件檔案…");
 try{
  for(const file of files){
   const revision=beginConnectionObservation();
   try{
    if(file.size>50*1024*1024){
     appendFileResult("拒絕："+file.name+"（超過 50 MB 上限）");continue;
    }
    const b64=await readFileBase64(file);
    const result=await fetchJson("/intake",{method:"POST",headers:{
     "Accept":"application/json","Content-Type":"application/json",
     "X-VIA-CSRF":CSRF_TOKEN},body:JSON.stringify({name:file.name,b64})},30000,
     validateIntake);
    const action=result.skip?"相同內容已存在，略過":"已存入 "+String(result.saved);
    appendFileResult("完成："+file.name+" · "+action+" · SHA "+result.sha256.slice(0,8));
    updateConnectionState("online","",revision);
   }catch(error){
    if(error.kind==="http")updateConnectionState("online","請求已被安全拒絕",revision);
    else connectionStateForError(error,revision);
    appendFileResult("未入庫："+file.name+" · "+error.message+"。");
   }finally{
    pendingFileCount=Math.max(0,pendingFileCount-1);syncInputSummary();
   }
  }
 }finally{
  filePicker.value="";setInputBadge("文件收件處理完成");releaseExecution(owner);
 }
}
dropZone.addEventListener("dragover",event=>{
 event.preventDefault();
 if(dropZone.getAttribute("aria-disabled")!=="true")dropZone.classList.add("on");
});
dropZone.addEventListener("dragleave",()=>dropZone.classList.remove("on"));
dropZone.addEventListener("drop",event=>{
 event.preventDefault();dropZone.classList.remove("on");
 if(dropZone.getAttribute("aria-disabled")!=="true")processFiles(event.dataTransfer.files);
});
dropZone.addEventListener("click",()=>{
 if(dropZone.getAttribute("aria-disabled")!=="true")filePicker.click();
});
dropZone.addEventListener("keydown",event=>{
 if((event.key==="Enter"||event.key===" ")
  &&dropZone.getAttribute("aria-disabled")!=="true"){
  event.preventDefault();filePicker.click();
 }
});
filePicker.addEventListener("change",()=>processFiles(filePicker.files));
window.VIA_FILES={processFiles};
"""

STATUSJS = r"""
const STATE_LABELS={idle:"待命",running:"執行中",ok:"完成",fail:"失敗",
 skip:"略過",blocked:"受阻",offline:"離線","no-data":"無資料"};
let hubDown=false;
let currentTask=null;
let lastStatus={};
let pollInFlight=false;
let statusIsStale=true;
let lastStatusSuccessAt=null;
let consecutivePollErrors=0;
let pollTimer=null;

function cleanState(value){
 const state=String(value||"idle").toLowerCase();
 return Object.prototype.hasOwnProperty.call(STATE_LABELS,state)?state:"idle";
}
function clampPercent(value){
 const number=Number(value);return Number.isFinite(number)?Math.max(0,Math.min(100,number)):null;
}
function createCell(text){const cell=document.createElement("td");cell.textContent=text;return cell;}
function formatMetric(value,suffix=""){
 return value===undefined||value===null||value===""?"—":String(value)+suffix;
}
function renderStatusDistribution(status){
 const container=byId("statusDistribution");container.replaceChildren();
 container.classList.remove("stale");
 const entries=Object.values(status||{});
 const total=entries.length;
 const counts={idle:0,running:0,ok:0,fail:0};
 entries.forEach(item=>{const state=cleanState(item.state);counts[state]=(counts[state]||0)+1;});
 byId("overviewEmpty").hidden=total>0;
 for(const state of ["running","ok","fail","idle"]){
  const row=document.createElement("div");row.className="dist-row";
  const label=document.createElement("span");label.className="dist-label";
  label.textContent=STATE_LABELS[state];
  const track=document.createElement("div");track.className="dist-track";
  const fill=document.createElement("div");fill.className="dist-fill "+state;
  fill.style.width=(total?counts[state]/total*100:0)+"%";track.append(fill);
  const count=document.createElement("span");count.className="dist-count";
  count.textContent=String(counts[state]);row.append(label,track,count);container.append(row);
 }
}
function renderStatusMatrix(status){
 const body=byId("statusMatrixBody");body.replaceChildren();
 const entries=Object.entries(status||{});
 if(!entries.length){
  const row=document.createElement("tr");const cell=createCell("指揮台目前沒有任務狀態資料。");
  cell.colSpan=9;row.append(cell);body.append(row);renderStatusDistribution({});return;
 }
 for(const [taskId,item] of entries){
  const state=cleanState(item.state);const pct=clampPercent(item.pct);
  const row=document.createElement("tr");row.dataset.taskId=taskId;
  const nameCell=document.createElement("td");const select=document.createElement("button");
  select.type="button";select.className="task-link";select.textContent=taskFormalName(taskId);
  select.addEventListener("click",()=>selectResult(taskId));nameCell.append(select);row.append(nameCell);
  const stateCell=document.createElement("td");const pill=document.createElement("span");
  pill.className="state-pill "+state;pill.textContent=STATE_LABELS[state];stateCell.append(pill);row.append(stateCell);
  row.append(createCell(formatMetric(item.started)),createCell(formatMetric(item.elapsed," 秒")),
   createCell(formatMetric(item.beat," 秒前")),createCell(formatMetric(item.kb," KB")));
  const progressCell=document.createElement("td");progressCell.className="progress-cell";
  const progressLabel=document.createElement("span");
  progressLabel.textContent=item.done!=null?String(item.done)+(pct!=null?" · "+pct+"%":""):
   (pct!=null?pct+"%":"—");
  const track=document.createElement("div");track.className="progress-track";
  const fill=document.createElement("div");fill.className="progress-fill";
  fill.style.width=(pct!=null?pct:(state==="ok"?100:0))+"%";
  track.setAttribute("role","progressbar");track.setAttribute("aria-label","工作完成進度");
  track.setAttribute("aria-valuemin","0");track.setAttribute("aria-valuemax","100");
  if(pct!=null)track.setAttribute("aria-valuenow",String(pct));
  else track.setAttribute("aria-valuetext",state==="ok"?"工作已完成":"未回報可量化進度");
  if(state==="fail")fill.style.background="var(--bad)";
  else if(state==="ok")fill.style.background="var(--ok)";
  else if(state==="running")fill.style.background="var(--warn)";
  track.append(fill);progressCell.append(progressLabel,track);row.append(progressCell);
  row.append(createCell(formatMetric(item.rc)),createCell(item.fix||"—"));body.append(row);
 }
 renderStatusDistribution(status);
}
function selectResult(taskId){
 currentTask=taskId;const item=lastStatus[taskId]||{};const state=cleanState(item.state);
 byId("selectedResultTitle").textContent=taskFormalName(taskId);
 byId("selectedResultState").textContent=statusIsStale
  ?STATE_LABELS[state]+"・資料過期":STATE_LABELS[state];
 byId("selectedResultState").className="honesty "+(statusIsStale?"stale":state);
 const lines=["正式工作："+taskFormalName(taskId),"狀態："+STATE_LABELS[state]];
 if(item.run_id)lines.push("執行識別："+item.run_id);
 if(item.started)lines.push("開始："+item.started);
 if(item.elapsed!=null)lines.push("經過："+item.elapsed+" 秒");
 if(item.beat!=null)lines.push("心跳延遲："+item.beat+" 秒前");
 if(item.rc!=null)lines.push("回傳碼："+item.rc);
 if(statusIsStale)lines.push("資料註記：本列為上次成功取得的快照，不代表目前狀態。");
 lines.push("",item.tail||"尚無執行紀錄。");
 if(item.fix)lines.push("","建議處理："+item.fix);
 byId("result").textContent=lines.join("\n");
}
function markStatusRowsStale(reason){
 statusIsStale=true;
 byId("statusDistribution").classList.add("stale");
 document.querySelectorAll("#statusMatrixBody tr[data-task-id]").forEach(row=>{
  row.classList.add("stale");
  const pill=row.querySelector(".state-pill");
  if(pill){
   const original=STATE_LABELS[cleanState(lastStatus[row.dataset.taskId]?.state)];
   pill.className="state-pill stale";pill.textContent=original+"・資料過期";
  }
 });
 byId("statusSource").textContent="資料過期・不作狀態裁決";
 byId("statusSource").className="honesty stale";
 if(currentTask)selectResult(currentTask);
 if(reason)byId("matrixNotice").textContent=reason;
}
async function poll(){
 if(!LIVE_SAME_ORIGIN){
  markStatusRowsStale(EDITABLE_PREVIEW
   ?"設計模板為預覽模式，不讀取本機執行狀態。"
   :"目前為離線檔案檢視；請由本機指揮台 /master 開啟即時狀態。");
  return;
 }
 if(pollInFlight||document.hidden)return;pollInFlight=true;
 const revision=beginConnectionObservation();
 try{
  const status=await fetchJson("/status",{},8000,validateStatus);
  lastStatus=status;hubDown=false;statusIsStale=false;consecutivePollErrors=0;
  lastStatusSuccessAt=new Date();updateConnectionState("online","",revision);
  byId("matrixNotice").textContent=Object.keys(status).length
   ?"狀態取自本機指揮台；最後成功更新 "+lastStatusSuccessAt.toLocaleTimeString("zh-TW",{hour12:false})+
    "。點選正式工作名稱可查看紀錄。"
   :"指揮台在線，但目前沒有工作狀態資料。";
  byId("statusSource").textContent="本機即時資料";
  byId("statusSource").className="honesty";
  renderStatusMatrix(status);if(currentTask)selectResult(currentTask);
  if(lastSubmittedTask&&status[lastSubmittedTask]){
   const submitted=status[lastSubmittedTask];
   if(submitted.state==="running")setInputBadge("執行中・run_id 已核對","running");
   else if(["ok","fail"].includes(submitted.state)&&!executionMutex)
    setInputBadge(submitted.state==="ok"?"執行完成":"執行失敗",submitted.state);
  }
 }catch(error){
  consecutivePollErrors+=1;connectionStateForError(error,revision);
  const stopped=consecutivePollErrors>=3;
  markStatusRowsStale("本機指揮台離線或回應異常："+error.message+
   "。既有列已中性化為過期快照。"+(stopped?" 連續三次錯誤，自動輪詢已暫停。":""));
  if(!hubDown){hubDown=true;logLine("狀態輪詢中斷："+error.message);}
  if(stopped&&pollTimer){clearInterval(pollTimer);pollTimer=null;}
 }
 finally{pollInFlight=false;}
}
function resumePolling(){
 if(!LIVE_SAME_ORIGIN)return;
 consecutivePollErrors=0;
 if(!pollTimer)pollTimer=setInterval(poll,4000);
 poll();
}
document.addEventListener("visibilitychange",()=>{if(!document.hidden)resumePolling();});
if(LIVE_SAME_ORIGIN)resumePolling();else poll();
window.VIA_STATUS={poll,resume:resumePolling,renderStatusMatrix,selectResult,
 markStatusRowsStale,getLast:()=>lastStatus};
"""


def _build_page(d: dict, tasks: dict) -> str:
    """組裝單檔零 CDN 頁面；所有動態片段在 Python 端先完成編碼。"""
    return (render(d, tasks).replace("__MCSS__", MCSS)
            .replace("__APPJS__", APPJS)
            .replace("__STATUSJS__", STATUSJS)
            .replace("__DROPJS__", DROPJS))


def _atomic_write(path: Path, content: str) -> None:
    """先完整寫暫存檔再原子替換，避免中斷留下半份 HTML。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=path.parent,
                prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            temporary_name = stream.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()


def do_template(force: bool = False) -> int:
    """建立可獨立優化模板；預設不覆寫使用者已修改的模板。"""
    if TEMPLATE_OUT.exists() and not force:
        print(f"[MGR:template] 已存在=保留使用者版本 · {TEMPLATE_OUT.name}")
        return 0
    d = do_list(do_print=False)
    tasks = _mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    page = _build_page(d, tasks)
    page = page.replace("<title>VIA 系統運轉與分析總控台</title>",
                        "<title>VIA Plotly Dashboard 可編輯模板</title>")
    page = page.replace("<body data-rail=\"open\">",
                        '<body data-rail="open" data-editable-template="true">')
    page = page.replace('id="runOneButton" class="primary"',
                        'id="runOneButton" class="primary" disabled')
    page = page.replace('id="runBatchButton" class="primary full"',
                        'id="runBatchButton" class="primary full" disabled')
    page = page.replace('id="filePicker" multiple hidden',
                        'id="filePicker" multiple hidden disabled')
    page = page.replace('id="drop" tabindex="0" role="button"',
                        'id="drop" tabindex="-1" role="button" aria-disabled="true"')
    page = page.replace('<div class="workspace-heading">',
                        '<div class="design-template-banner">可編輯設計模板 · 僅供版面預覽，'
                        '任務執行與文件收件已停用；此檔不會被 via-manager 日常再生覆寫，'
                        '核定後再回填正主管理器。'
                        '</div><div class="workspace-heading">', 1)
    page = "<!-- VIA:EDITABLE-DESIGN-TEMPLATE:v0100 -->\n" + page
    _atomic_write(TEMPLATE_OUT, page)
    print(f"[MGR:template] 可編輯 HTML 模板已產生 · {TEMPLATE_OUT.name}")
    return 0


def _preferred_ui_target() -> str:
    """橋 v0114+ 在線時使用同源 /master；否則保留 file 離線檢視。"""
    try:
        from urllib.request import Request, urlopen
        request = Request(f"{BRIDGE_URL}/ping", headers={"Accept": "application/json"})
        with urlopen(request, timeout=0.7) as response:
            payload = json.loads(response.read(4096).decode("utf-8"))
        version = re.search(r"(\d+)", str(payload.get("v", "")))
        if (payload.get("ok") is True and payload.get("via") == "deck-bridge"
                and version and int(version.group(1)) >= 114):
            return f"{BRIDGE_URL}/master"
    except Exception:
        pass
    return OUT.as_uri()


def do_ui(open_after: bool = True) -> int:
    d = do_list(do_print=False)
    tasks = _mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    _atomic_write(OUT, _build_page(d, tasks))
    if not TEMPLATE_OUT.exists():
        do_template(force=False)
    print(f"[MGR:ui] 總控頁再生 · 正式任務 {len(tasks)} · {OUT.name}")
    if open_after:
        target = _preferred_ui_target()
        try:
            os.startfile(target)              # Windows I/O 正道
        except AttributeError:
            try:
                import webbrowser
                webbrowser.open(target)        # 跨平台後備
            except Exception:
                pass
    return 0


def selftest() -> int:
    """檢查產生器契約；瀏覽器幾何與互動另由 Playwright 驗證。"""
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    d = do_list(do_print=False)
    tasks = _mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    page = _build_page(d, tasks)
    rc = 0
    engine_rows = _engine_rows(d)
    module_rows = _module_rows(d)
    rail = page[page.index('<aside class="control-rail"'):
                page.index('</aside>')]
    task_option_text = " ".join(_formal_task_name(k, v.get("zh", k))
                                for k, v in tasks.items())
    chk("① 管理器六職完整",
        rc == 0 and all(f"def do_{k}" in src for k in
                        ("sync", "list", "run", "template", "ui"))
        and 'a[0] == "serve"' in src)
    chk("② 盤點數量、候核名稱與唯一識別碼一致",
        len(tasks) >= 32 and len(engine_rows) >= 194
        and len({r["identifier"] for r in engine_rows}) == len(engine_rows)
        and len({r["name"] for r in engine_rows}) == len(engine_rows)
        and len(module_rows) >= 85
        and len({r["name"] for r in module_rows}) == len(module_rows),
        f"(任務 {len(tasks)} · 引擎 {len(engine_rows)} · 模組 {len(module_rows)};v0109 盤點動態=只增不減)")
    chk("③ 所有操作輸入集中在可收合左欄",
        all(f'id="{field}"' in rail for field in
            ("task", "codes", "dateStart", "dateEnd", "categories",
             "runOneButton", "runBatchButton", "drop"))
        and 'aria-expanded="true"' in page and "data-rail" in page
        and "rail.inert=!open" in page and 'id="railBackdrop"' in page)
    chk("④ 必要參數由任務契約動態顯示",
        all(token in page for token in
            ('data-codes="true"', 'data-range="true"', 'data-cats="true"',
             "updateParameterVisibility", "syncInputSummary")))
    chk("⑤ 右側七分頁、固定頁首與固定頁尾",
        page.count('<button role="tab"') == 7
        and page.count('role="tabpanel"') == 7
        and ".app-header{position:fixed" in page
        and ".app-footer{position:fixed" in page)
    chk("⑥ 主要工作名稱無程式化鍵值",
        not any(re.search(rf"\b{re.escape(key)}\b", task_option_text)
                for key in tasks) and len(TASK_FORMAL_NAMES) == len(tasks))
    chk("⑦ 引擎、模組與讀取規劃已表列",
        all(x in page for x in
            ('id="engineTable"', 'id="moduleTable"', 'class="plan-table"',
             "正式名稱待治理", "候核序號", ACTIVATION_STATE))
        and "已註冊・尚未執行" not in page)
    chk("⑧ Plotly 有真實頁面或缺料降級，且零 CDN",
        (('id="plotlyFrame"' in page and "此時間只證明頁面檔案更新" in page)
         or ('id="plotlyEmpty"' in page and "本頁不顯示模擬行情或假圖" in page))
        and not re.search(r'<(?:script|link)[^>]+https?://', page, re.I))
    chk("⑨ 狀態安全編碼、連線誠實、真正依序佇列",
        "textContent" in page and "waitForTerminal" in page
        and 'name="via-csrf" content=""' in page
        and 'fetchJson("/run",{method:"POST"' in page
        and "accepted_params" in page and "run_id" in page
        and "GET /run?" not in page
        and "任一項失敗即停止佇列" in page
        and "MANAGER · LIVE" not in page)
    chk("⑩ 白名單鐵則、原子寫入與可編輯模板保護",
        do_run("rm -rf /") == 2 and "os.replace" in src
        and "if TEMPLATE_OUT.exists() and not force" in src
        and "__APPJS__" not in page and "__STATUSJS__" not in page
        and "__DROPJS__" not in page and "__MCSS__" not in page)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 總系統管理器(VIA_SYSTEM_MANAGER)· 十檢自測(零外網)===")
        return selftest()
    if a and a[0] == "sync":
        return do_sync()
    if a and a[0] == "list":
        do_list()
        return 0
    if a and a[0] == "serve":
        deck = sorted(REG.glob("CGC_MDL095_DeckServer_v*.py"))[-1]
        print(f"[MGR:serve] 帶起唯一 API 樞紐:{deck.name}(Ctrl+C 停)")
        return subprocess.run([sys.executable, str(deck), "serve"]).returncode
    if a and a[0] == "run":
        return do_run(a[1] if len(a) > 1 else "", a[2:])
    if a and a[0] == "template":
        return do_template(force="--force" in a)
    return do_ui(open_after="--no-open" not in a)


if __name__ == "__main__":
    sys.exit(main())
