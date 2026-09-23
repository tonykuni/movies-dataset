#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_params_central_v0106 — 中央參數樞紐(TOOL-069)
====================================================================
操作員令(批41,2026-08-18):「參數統儘量中央化管理」。
v0100→v0101(批43):+第 17 冊 VRN_METHOD(VRN 方法冊 def01-20:
五區抽取/雙層保存/官方對照/算術勾稽/證據仲裁;TOOL-071 方法核之
SSOT 正本)。
v0101→v0102(批44):+三冊財務字庫(TOOL-072 收割自倉內正本):
VRN_BROKER(券商縮寫 29 家)/VRN_FINDATA_SYN(153 canonical 中英
同義,多源並列)/VRN_FINSTMT_SYN(7 表 141 科目歸屬)——20 冊。
v0102→v0103(批45):+VRN_RATING(評等四級+關鍵字六集)/
VRN_TICKDATE(多市場 ticker+日期 regex 38 式)——22 冊。
v0103→v0104(批49):+VRN_TRIFILL(操作員核定 195 條三語補齊冊,
LOCKED 域=核定值不由引擎自改)——23 冊。
v0104→v0105(批52-54):+TW_GROUP_CLASS(族群分類 v1.1 策展冊
149 檔 31 群轉錄)/TW_EQUITY(個股清單 SSOT)——25 冊。
v0105→v0106(批98-99/103 續波):+三子系統參數冊(VRN/VDF/VAP
_Param_Registry,glob 動態接最新版)——28 冊;新增 canonical 裁決
解析 API canonical_get(sub,name):六形態(<TODAY> 預設今日可覆寫/
<DYNAMIC> 動態 VIA 根/<UNION> 變體聯集/SCOPED 各引擎自持/字面值)
=引擎改讀 canonical 參數層的統一入口;CLI --canon SUB [NAME]。
原則:
  ① 單一真相不搬家 — 各參數 SSOT 冊留在原位為正本;本樞紐只建
     「指標索引冊」(路徑+sha256+葉數+頂鍵),零複製零改寫。
  ② 衝突可見 — 同一參數鍵(dotted 葉路徑)在多冊出現且值不同
     =列 CONFLICT(建議燈,不自動改;裁決權在操作員)。
  ③ LOCKED 對齊 — regex 治理中心 LOCKED 條目跨冊比對,DRIFT 即紅。
  ④ 誠實三態 — 冊缺=MISSING(工作站 .local 冊在容器缺屬誠實)。
  ⑤ 供程式讀 — central_get(key) 供各引擎統一查參數(先冊後鍵)。
用法:
  via-params                → 全掃描+索引冊+理印 U/I
  via-params --get KEY      → 跨冊查參數(dotted 路徑或關鍵字)
  via-params --check        → 只驗衝突/LOCKED 對齊(rc1=有紅)
  via-params --canon SUB [NAME] [--date YYYY-MM-DD]
                            → canonical 裁決解析(SUB=VRN/VDF/VAP)
  via-params --selftest     → 九檢(沙盒零網路)
  via-params --no-open      → 不開 U/I(容器/批次)
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

import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
INDEX_PATH = HERE / "VIA_Central_Params_SSOT_v0100.json"
UI_PATH = REPORTS / "VIA_UI_CentralParams.html"

MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"

# ── 參數 SSOT 冊登記表(指標不搬家;conflict_scope=入衝突比對圈)──
# domain:LOCKED=治理鎖 / CONFIG=運行參數 / KNOWLEDGE=知識庫 / REGISTRY=登記冊
BOOKS = [
    {"id": "SYNONYM_REGEX", "domain": "LOCKED", "conflict_scope": True,
     "path": "supportive modules/registry/VIA_Central_Synonym_Regex_v0100.json",
     "note": "Regex 治理中心(7 LOCKED+7 同義集)"},
    {"id": "BRAND_SSOT", "domain": "LOCKED", "conflict_scope": True,
     "path": "supportive modules/registry/VIA_Brand_SSOT_v0100.json",
     "note": "品牌銘言 Observa·Intellege·Praevide"},
    {"id": "VDF_UNIFIED", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VDF/VDF_Unified_Params_v0100.json",
     "note": "VDF 統一輸入參數+六格式輸出樞紐"},
    {"id": "FLOW_PARAMS", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/params.json",
     "note": "FlowSystem 主參數"},
    {"id": "FLOW_TW_ETF", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Active_ETF_Registry_v0100.json",
     "note": "台灣主動式 ETF 清單 SSOT"},
    {"id": "FLOW_GLOBAL_ETF", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/Global_ETF_Universe_v0100.json",
     "note": "全球 ETF 五類宇宙"},
    {"id": "FLOW_UNIVERSE", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/universe.json",
     "note": "FlowSystem 標的宇宙"},
    {"id": "FLOW_MACRO", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/macro.json",
     "note": "宏觀疊圖參數"},
    {"id": "FLOW_SIM", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/sim.json",
     "note": "模擬參數"},
    {"id": "FLOW_PERF", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/perf.json",
     "note": "績效參數"},
    {"id": "VRN_LEXICON", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_Lexicon_v0100.json",
     "note": "中英文字庫+K1-K8 知識樹(162 條級)"},
    {"id": "VRN_DIGEST", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VRN/knowledge/VRN_Digest_Params_v0100.json",
     "note": "個股報告摘要批跑參數(TOOL-070)"},
    {"id": "VRN_METHOD", "domain": "LOCKED", "conflict_scope": True,
     "path": "functional modules/VRN/knowledge/VRN_Method_SSOT_v0100.json",
     "note": "VRN 方法冊 def01-20(五區抽取/雙層保存/官方對照/算術勾稽/證據仲裁;TOOL-071)"},
    {"id": "VRN_BROKER", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json",
     "note": "券商縮寫字典 29 家(TOOL-072 收割自 Summarizer)"},
    {"id": "VRN_FINDATA_SYN", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_FinData_Synonym_v0100.json",
     "note": "財務數據中英文同義字庫 153 canonical(pattern庫+MOPS+MDL008+方法冊四源)"},
    {"id": "VRN_FINSTMT_SYN", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_FinStatement_Synonym_v0100.json",
     "note": "財務報表同義字庫 7 表 141 科目歸屬(TOOL-072)"},
    {"id": "VRN_RATING", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_Rating_Dict_v0100.json",
     "note": "評等字庫四級 zh/en+score_range+關鍵字六集(TOOL-072 v0101)"},
    {"id": "VRN_TICKDATE", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_TickerDate_Regex_v0100.json",
     "note": "多市場 ticker+日期時間 regex 38 式(TW 寬鬆式不入 LOCKED 圈)"},
    {"id": "VRN_TRIFILL", "domain": "LOCKED", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_Canonical_Trilingual_Fill_v0100.json",
     "note": "操作員核定 195 條三語補齊冊(批49;findata 空欄權威回填源)"},
    {"id": "TW_GROUP_CLASS", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Group_Classification_v0110.json",
     "note": "族群分類 v1.1 策展冊(149 檔 31 群 L/P/G;T4 佔位候 VDF 誠實)"},
    {"id": "TW_EQUITY", "domain": "CONFIG", "conflict_scope": False,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Equity_Registry_v0100.json",
     "note": "台股個股清單 SSOT(TOOL-075 --refresh-equity 官方 OpenAPI 併冊)"},
    {"id": "VRN_PARAM_REG", "domain": "CONFIG", "conflict_scope": False,
     "path": "functional modules/VRN/VRN_Param_Registry_v0100.json",
     "note": "VRN 引擎參數收割冊+canonical 裁決區(批98-99;append-only)"},
    {"id": "VDF_PARAM_REG", "domain": "CONFIG", "conflict_scope": False,
     "path": "functional modules/VDF/VDF_Param_Registry_v0100.json",
     "note": "VDF 引擎參數收割冊+canonical 裁決區(批98-99;append-only)"},
    {"id": "VAP_PARAM_REG", "domain": "CONFIG", "conflict_scope": False,
     "path": "functional modules/VAP/VAP_Param_Registry_v0100.json",
     "note": "VAP 引擎參數收割冊+canonical 裁決區(批98-99;append-only)"},
    {"id": "FINAL_PARAMS", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_FinalParameters_CanonicalRegistry.json",
     "note": "歷史最終參數正典冊"},
    {"id": "VRN_FIELD_SPEC", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_VRN_FieldSpec_SSOT_v0100.json",
     "note": "批712 操作員逐欄給定的研報 15 欄規格;CGC_MDL181 讀它對帳。"
             "REGISTRY 域、不進衝突圈——它是**欄位定義**不是共用參數值,"
             "拿它去跟別本冊比值只會生假紅"},
    {"id": "VDF_TW_ENDPOINTS", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_VDF_TWMarketEndpoints_SSOT_v0100.json",
     "note": "批720 操作員逐項給定的 TWSE/TPEX 端點冊(三大法人/融資券/當沖/成交量值/市值)。"
             "三態 VERIFIED / CANDIDATE / **UNKNOWN(不知道就不編一個)**;VDF_ENG092 讀它。"
             "另存 SMA 兩次裁定的留痕(先『保留好了』後『全數刪除』)與減前的下游量測。"
             "REGISTRY 域、不進衝突圈:它是**端點清單**不是共用參數值"},
    {"id": "CELERITAS_POLICY_BASELINE", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_CeleritasPolicy_Baseline_v0100.json",
     "note": "批715 L102 執法基線:.ps1 既有債 838 支 · 凍結夾具名豁免 4 支 · 批345 舊正本 sha256。"
             "**基線放資料檔不放碼裡**(批709 那 102 條字面路徑的教訓)。CGC_MDL183 讀它。"
             "REGISTRY 域、不進衝突圈:它是**清單**不是共用參數值"},
    {"id": "VRN_REPORT_FIELD_RULES", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_VRN_ReportFieldRules_SSOT_v0100.json",
     "note": "批713 補尺冊(檔名括號槽位式評等 · 研究員職稱表 · 券商網域補遺 · 電話鄰域守衛 · "
             "中文姓名機構詞擋板);CGC_MDL182 讀它。電話與姓名的式子**不在這本**——"
             "只留 alias_source 指向正本 VRN_FieldRules_SSOT(抄了就是第二顆會漂移的頭)。"
             "REGISTRY 域、不進衝突圈:它是**規則定義**不是共用參數值"},
    {"id": "AUTOCODE_REG", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_AutoCode_Registry_v0100.json",
     "note": "自動編號命名冊(append-only;編號永不變)"},
    {"id": "IFACE_REG", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json",
     "note": "介面契約冊(2,000+ 模組)"},
    {"id": "MASTER_GOV_LOCAL", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_MasterGovernance_SSOT_v0100.local.json",
     "note": "主治理冊(工作站 .local;容器缺=誠實 MISSING)"},

    # ═══ 批635 補冊:操作員令「重新檢視整合 VRN VDF 所有 SSOT 參數邏輯」═══
    #   量出來的事實:v0106 的名冊只有 28 本,而活樹裡**有引擎在讀、帶參數**的
    #   VRN/VDF 冊有 49 本不在名冊上——其中包括批628 起一路在擴充的
    #   `VRN_FieldRules_SSOT`。所以「衝突 0」不是因為沒有衝突,
    #   **是因為只看了 28 本**(L83:只有一半的路被走過就不算跑過)。
    #
    #   選件規則(量得出來的,不是我挑的):活樹 × 有引擎在讀 × 葉 ≥5 ×
    #   非收容/鏡像/範本/過渡產物(Preview/Hotfix/DryRun)。同名雙份留
    #   `supportive modules/registry` 那一份,另一份記在 TWIN_BOOKS。
    #
    #   **只有 CONFIG / LOCKED 域進衝突圈**。KNOWLEDGE / REGISTRY 的
    #   `version` / `generated_at` / `status` 本來就各本各有,放進衝突圈
    #   只會生出一堆假紅——我第一版全鍵掃描量到 91 條「同鍵不同值」,
    #   逐條看下去幾乎全是這種中繼資料(判準太鈍,鍵名相同不等於同一個參數)。
    {"id": "VDF_CONTRACT_SUMMARY", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/GroupIndex/flow_simulation_v0400/evidence/vdf_contract_summary.json",
     "note": "批635 補冊;葉 12"},
    {"id": "VDF_FETCHONE_MATRIX_REGISTRY_V0100", "domain": "REGISTRY", "conflict_scope": False,
     "path": "functional modules/VDF/VDF_FetchOne_Matrix_Registry_v0100.json",
     "note": "批635 補冊;葉 3739"},
    {"id": "VDF_USMACRO_DETAIL_FETCH_ROSTER_V0", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VDF/VDF_USMacro_Detail_Fetch_Roster_v0100.json",
     "note": "批635 補冊;葉 226"},
    {"id": "VDF_FETCH_CONTRACT", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VDF/registry/VIA_VDF_Fetch_Contract.json",
     "note": "批635 補冊;葉 5002"},
    {"id": "VRN_RESEARCHREPORT_SSOT_ACTIVE", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VRN/SSOT/VRN_ResearchReport_SSOT.active.json",
     "note": "批635 補冊;葉 24"},
    {"id": "VRN_TWROSTER_OFFLINE_V0100", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/VRN_TWRoster_Offline_v0100.json",
     "note": "批635 補冊;葉 7917"},
    {"id": "VRN_KEYWORDSSOT_V0100", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/dict/VRN_KeywordSSOT_v0100.json",
     "note": "批635 補冊;葉 17097"},
    {"id": "VRN_ANNUALEXTRACT_SSOT_V0100", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VRN/knowledge/VRN_AnnualExtract_SSOT_v0100.json",
     "note": "批635 補冊;葉 600"},
    {"id": "INVESTMENT_REPORT_TYPE_SSOT", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VRN/webscraping_dualengine_v20260819/VIA_Investment_Report_Type_SSOT.json",
     "note": "批635 補冊;葉 317"},
    {"id": "WEBSCRAPING_COMPLIANCE_SSOT", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VRN/webscraping_dualengine_v20260819/VIA_WebScraping_Compliance_SSOT.json",
     "note": "批635 補冊;葉 34"},
    {"id": "MACRO_SSOT", "domain": "CONFIG", "conflict_scope": True,
     "path": "new modules engines/VDF_final/config/macro_ssot.json",
     "note": "批635 補冊;葉 2039"},
    {"id": "MASTER_SSOT", "domain": "CONFIG", "conflict_scope": True,
     "path": "new modules engines/VDF_final/config/via_master_ssot.json",
     "note": "批635 補冊;葉 3479"},
    {"id": "VRN_BROKERALIASSSOT_V029SSOT1B", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "supportive modules/environment/VRN_BrokerAliasSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 175"},
    {"id": "VRN_FINANCIALACCOUNTALIASSSOT_V029", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "supportive modules/environment/VRN_FinancialAccountAliasSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 168"},
    {"id": "VRN_RATINGALIASSSOT_V029SSOT1B", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "supportive modules/environment/VRN_RatingAliasSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 64"},
    {"id": "VDF_DATASCOPE_HEADERREGISTRY_SSOT", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_DataScope_HeaderRegistry_SSOT.json",
     "note": "批635 補冊;葉 239"},
    {"id": "VDF_MDL401_REGISTRYSCHEMA", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_MDL401_RegistrySchema.json",
     "note": "批635 補冊;葉 248"},
    {"id": "VDF_MDL402_REGISTRYSAMPLE", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_MDL402_RegistrySample.json",
     "note": "批635 補冊;葉 475"},
    {"id": "VDF_MDL403_REGISTRYFULL", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_MDL403_RegistryFull.json",
     "note": "批635 補冊;葉 5162"},
    {"id": "VDF_NEXUSCORE_MODULEREGISTRY", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_NexusCore_ModuleRegistry.json",
     "note": "批635 補冊;葉 204"},
    {"id": "VDF_STORYGROUP_REGISTRY_V0100", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_StoryGroup_Registry_v0100.json",
     "note": "批635 補冊;葉 275"},
    {"id": "VDF_STORYGROUP_REGISTRY_V0101", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VDF_StoryGroup_Registry_v0101.json",
     "note": "批635 補冊;葉 362"},
    {"id": "VRN_LOGICARCHITECTURE_SSOT_V0100", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_VRN_LogicArchitecture_SSOT_v0100.json",
     "note": "批635 補冊;葉 184"},
    {"id": "VRN_EXTRACTIONLOGIC_SSOT_V0100", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/registry/VRN_ExtractionLogic_SSOT_v0100.json",
     "note": "批635 補冊;葉 92"},
    {"id": "VRN_FIELDRULES_SSOT_V0100", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/registry/VRN_FieldRules_SSOT_v0100.json",
     "note": "批635 補冊;葉 502"},
    {"id": "VRN_MATRIXAPPLICABILITY_SSOT_V0100", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/registry/VRN_MatrixApplicability_SSOT_v0100.json",
     "note": "批635 補冊;葉 24"},
    {"id": "VRN_VERIFIED_MODULE_REGISTRY", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VRN_Verified_Module_Registry.json",
     "note": "批635 補冊;葉 3600"},
    {"id": "VDF_AKSHARE_CANONICALMAPPINGRULES_", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VDF_AkShare_CanonicalMappingRules_v0277.json",
     "note": "批635 補冊;葉 41"},
    {"id": "VDF_AKSHARE_NARROWSOURCE_CANONICAL", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VDF_AkShare_NarrowSource_CanonicalKeyContract_v02782.json",
     "note": "批635 補冊;葉 27"},
    {"id": "VDF_AKSHARE_SMARTREMAPRULES_V02781", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VDF_AkShare_SmartRemapRules_v027811.json",
     "note": "批635 補冊;葉 10"},
    {"id": "VRN_ACTIVE_STAGE_POINTER_CANDIDATE", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_ACTIVE_STAGE_POINTER_CANDIDATE_v029SSOT1B.json",
     "note": "批635 補冊;葉 32"},
    {"id": "VRN_BASICINFODEFINITIONSSOT_V029SS", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_BasicInfoDefinitionSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 42"},
    {"id": "VRN_DATEPERIODREGEXSSOT_V029SSOT1B", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_DatePeriodRegexSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 24"},
    {"id": "VRN_FINANCIALREGEX_SSOT", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_FinancialRegex_SSOT.json",
     "note": "批635 補冊;葉 135"},
    {"id": "VRN_FINANCIALVALIDATIONRULESSSOT_V", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_FinancialValidationRulesSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 75"},
    {"id": "VRN_SSOT_SOURCEINVENTORY_V029SSOT1", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "supportive modules/ssot/VRN_SSOT_SourceInventory_v029SSOT1B.json",
     "note": "批635 補冊;葉 3534"},
    {"id": "VRN_TICKERREGEXSSOT_V0100", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json",
     "note": "批635 補冊;葉 46"},
    {"id": "VRN_TICKERREGEXSSOT_V029SSOT1B", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/ssot/VRN_TickerRegexSSOT_v029SSOT1B.json",
     "note": "批635 補冊;葉 31"},
    # 批679:這兩本冊原本沒有任何 .py 提到它們的檔名,所以 ⑩ 的「有引擎在讀」那一關把它們濾掉了。
    #   CGC_MDL177 陸券清除閘逐字寫出它們的路徑之後,它們**就有讀者了**——⑩ 當場照紅,
    #   而且照得對:有人在讀、帶參數、又不在名冊上,就是漏登。不是把尺調鬆,是把冊補上(L93)。
    {"id": "VRN_REPORT_PARSER_INTEGRATED_SSOT_V0", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/SSOT/VRN_Report_Parser_Integrated_SSOT.json",
     "note": "研報解析整合冊(券商別名/來源層);批679 起有讀者=CGC_MDL177"},
    {"id": "VRN_S05_FIELD_REGISTRY_V0102", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "supportive modules/registry/VRN_S05_FieldRegistry_v0102.json",
     "note": "S05 欄位冊(含 email 網域→券商);批679 起有讀者=CGC_MDL177"},
]

# 批635:同名雙份的另一份。**不進名冊但要留名**——
#   「名冊上沒有」和「樹上不存在」是兩件事,不寫下來下一個人會以為是後者。
TWIN_BOOKS = {
 "VDF_MDL402_RegistrySample.json": [
  "functional modules/VDF/VDF_MDL402_RegistrySample.json"
 ],
 "VDF_MDL401_RegistrySchema.json": [
  "functional modules/VDF/VDF_MDL401_RegistrySchema.json"
 ],
 "VDF_NexusCore_ModuleRegistry.json": [
  "supportive modules/_nexus_registry/VDF_NexusCore_ModuleRegistry.json"
 ]
}


LEAF_CAP = 20000  # 大冊葉數上限(超出誠實截記,防 REGISTRY 巨冊拖垮)


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:動態進度條(單行覆寫,不卡斷)"""
    w = 24
    k = int(w * i / max(n, 1))
    bar = "█" * k + "░" * (w - k)
    sys.stdout.write(f"\r  [{bar}] {i}/{n} {msg[:40]:<40}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


def flatten(obj, prefix="", out=None, cap=LEAF_CAP):
    """JSON → dotted 葉路徑表;list 以 [i] 記;超 cap 誠實截斷"""
    if out is None:
        out = {}
    if len(out) >= cap:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, f"{prefix}.{k}" if prefix else str(k), out, cap)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if len(out) >= cap:
                break
            flatten(v, f"{prefix}[{i}]", out, cap)
    else:
        if len(out) < cap:
            out[prefix] = obj
    return out


def scan_book(book: dict, root: Path) -> dict:
    p = root / book["path"]
    rec = {"id": book["id"], "domain": book["domain"], "path": book["path"],
           "note": book["note"], "conflict_scope": book["conflict_scope"]}
    if not p.exists():
        rec.update({"state": "MISSING", "sha256": "", "bytes": 0,
                    "leaf_count": 0, "top_keys": [], "truncated": False})
        return rec
    raw = p.read_bytes()
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["bytes"] = len(raw)
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        rec.update({"state": "FAIL", "error": str(exc)[:120],
                    "leaf_count": 0, "top_keys": [], "truncated": False})
        return rec
    leaves = flatten(data)
    rec["state"] = "OK"
    rec["leaf_count"] = len(leaves)
    rec["truncated"] = len(leaves) >= LEAF_CAP
    rec["top_keys"] = list(data.keys())[:12] if isinstance(data, dict) else [f"<{type(data).__name__}>"]
    rec["_leaves"] = leaves  # 記憶體內供衝突比對;不落索引冊
    return rec


# 元資料鍵:**每一本冊本來就各有一份**,不是共用參數。
#   批635 把名冊從 28 本補到 66 本之後,新冒出來的「衝突」逐條看下去
#   幾乎全是這一類——`generated_at` 兩本時間不同、`status` 兩本狀態不同、
#   `owner` 一本寫 Tony 一本寫模組名。那不是衝突,是我把中繼資料丟進了衝突圈。
#   判準鈍一點就會生出一堆假紅,而**假紅和假綠一樣傷**:看的人第二次就不看了。
META_KEYS = {"schema", "note", "_note", "policy", "updated", "updated_at", "generated",
             # ── 批635 量到的(補冊之後才冒出來的六個)──
             "generated_at", "status", "owner", "title", "risk", "next_step",
             "version", "schema_version", "ts", "batch", "date", "created",
             "created_at", "author", "source_file", "target_file", "check_message",
             "description", "desc", "why", "zh", "purpose", "id", "name"}


def find_conflicts(records: list[dict]) -> list[dict]:
    """衝突圈內:同 dotted 葉路徑跨冊出現且值不同=CONFLICT。
    排除:①元資料鍵(各冊本應自述,不是共用參數);②list 索引鍵
    (etfs[0].ticker 類位置鍵跨冊比對無語意,實為不同集合)。"""
    seen: dict[str, list[tuple[str, object]]] = {}
    for r in records:
        if r.get("state") != "OK" or not r["conflict_scope"]:
            continue
        for k, v in r.get("_leaves", {}).items():
            if "[" in k or k.rsplit(".", 1)[-1] in META_KEYS:
                continue
            seen.setdefault(k, []).append((r["id"], v))
    out = []
    for k, pairs in seen.items():
        if len(pairs) < 2:
            continue
        vals = {json.dumps(v, ensure_ascii=False, sort_keys=True) for _, v in pairs}
        if len(vals) > 1:
            out.append({"key": k,
                        "books": [{"book": b, "value": str(v)[:80]} for b, v in pairs]})
    return sorted(out, key=lambda c: c["key"])


def locked_alignment(records: list[dict]) -> list[dict]:
    """LOCKED regex 跨冊對齊:治理中心 pattern vs 他冊同名鍵"""
    gov = next((r for r in records if r["id"] == "SYNONYM_REGEX" and r.get("state") == "OK"), None)
    if not gov:
        return [{"name": "SYNONYM_REGEX", "state": "MISSING", "note": "治理中心冊缺,無從對齊"}]
    locked = {}
    for k, v in gov["_leaves"].items():
        m = re.match(r"regex\.([A-Za-z0-9_]+)\.pattern$", k)
        if m:
            locked[m.group(1)] = v
    out = []
    for name, pat in sorted(locked.items()):
        drift = []
        for r in records:
            if r["id"] == "SYNONYM_REGEX" or r.get("state") != "OK":
                continue
            for k, v in r.get("_leaves", {}).items():
                # 鍵尾段全等才視為同名宣告(LOOSE_ 等變體名≠LOCKED 競爭者)
                if (k.rsplit(".", 1)[-1] == name and isinstance(v, str)
                        and v.strip() and ("\\d" in v or "^" in v)):
                    if v != pat:
                        drift.append({"book": r["id"], "key": k, "value": str(v)[:80]})
        out.append({"name": name, "state": "DRIFT" if drift else "ALIGNED",
                    "pattern": pat, "drift": drift})
    return out


def central_get(key: str, root: Path = VIA) -> list[dict]:
    """跨冊查參數:dotted 路徑精確或關鍵字包含;回 [{book,key,value}]"""
    hits = []
    for book in BOOKS:
        p = root / book["path"]
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for k, v in flatten(data).items():
            if k == key or key.lower() in k.lower():
                hits.append({"book": book["id"], "key": k, "value": v})
                if len(hits) >= 50:
                    return hits
    return hits


# ── canonical 裁決解析(批99 四裁 R1-R7;引擎改讀統一入口)──────
CANON_SUBS = ("VRN", "VDF", "VAP")


def _canon_registry_path(sub: str, root: Path = VIA) -> Path | None:
    """glob 動態接最新版參數冊(鐵律:嚴禁寫死版號)"""
    hits = sorted((root / "functional modules" / sub).glob(f"{sub}_Param_Registry_v*.json"))
    return hits[-1] if hits else None


def _literal(txt: str):
    import ast as _ast
    try:
        return _ast.literal_eval(txt)
    except Exception:
        return txt  # 誠實後備:無法求值即回原字串


def _resolve_ruling(entry: dict, override=None, root: Path = VIA):
    """六形態裁決→具體值。回 (value, mode)。
    <TODAY>=今日可覆寫 / <DYNAMIC>=VIA 根 Path 字串 / <UNION>=變體聯集 /
    SCOPED=各引擎自持(override 優先,否則 None)/ 其餘=字面值。"""
    r = str(entry.get("ruling", ""))
    if r.startswith("<TODAY"):
        if override:
            return str(override), "TODAY_OVERRIDE"
        return datetime.now().strftime("%Y-%m-%d"), "TODAY"
    if r.startswith("<DYNAMIC"):
        return str(root), "DYNAMIC_ROOT"
    if r.startswith("<UNION"):
        merged_set, merged_dict, saw_dict = set(), {}, False
        for v in entry.get("variants", []):
            val = _literal(v) if isinstance(v, str) else v
            if isinstance(val, dict):
                saw_dict = True
                for k2, v2 in val.items():
                    merged_dict.setdefault(k2, v2)
            elif isinstance(val, (set, frozenset, list, tuple)):
                for item in val:
                    try:
                        merged_set.add(item)
                    except TypeError:
                        merged_set.add(json.dumps(item, ensure_ascii=False, sort_keys=True))
            else:
                merged_set.add(val)
        if saw_dict and not merged_set:
            return merged_dict, "UNION"
        return sorted(merged_set, key=lambda x: str(x)), "UNION"
    if r.startswith("SCOPED"):
        return (override, "SCOPED_OVERRIDE") if override is not None else (None, "SCOPED")
    return _literal(r), "LITERAL"


def canonical_get(sub: str, name: str, override=None, root: Path = VIA):
    """引擎統一入口:canonical_get('VDF','END_DATE') → 具體值。
    冊缺/鍵缺=KeyError(誠實 fail-closed,不編造預設)。"""
    sub = sub.upper()
    if sub not in CANON_SUBS:
        raise KeyError(f"unknown sub: {sub}(限 {CANON_SUBS})")
    p = _canon_registry_path(sub, root)
    if p is None:
        raise KeyError(f"{sub} 參數冊缺(容器/工作站樹不齊=誠實 MISSING)")
    canon = json.loads(p.read_text(encoding="utf-8-sig")).get("canonical", {})
    if name not in canon:
        raise KeyError(f"{sub}.{name} 不在 canonical 區({len(canon)} 鍵)")
    value, mode = _resolve_ruling(canon[name], override=override, root=root)
    return value


def canonical_list(sub: str, root: Path = VIA) -> dict:
    p = _canon_registry_path(sub.upper(), root)
    if p is None:
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig")).get("canonical", {})


def build_index(records: list[dict], conflicts, locked) -> dict:
    slim = []
    for r in records:
        s = {k: v for k, v in r.items() if k != "_leaves"}
        slim.append(s)
    n_ok = sum(1 for r in slim if r["state"] == "OK")
    n_missing = sum(1 for r in slim if r["state"] == "MISSING")
    n_fail = sum(1 for r in slim if r["state"] == "FAIL")
    return {"schema": "VIA.CentralParamsSSOT.v1",
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "policy": "指標索引冊;單一真相留原冊不搬家;衝突=建議燈候操作員裁決",
            "books_total": len(slim), "books_ok": n_ok,
            "books_missing": n_missing, "books_fail": n_fail,
            "leaf_total": sum(r.get("leaf_count", 0) for r in slim),
            "conflicts": conflicts, "locked_alignment": locked,
            "books": slim}


# ── 理印紙墨 U/I ──────────────────────────────────────────────
CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1200px}
h1{font-size:20px;margin:0 0 2px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}.bad{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}
.dim{color:#6b6a64}
"""


def render_ui(idx: dict, out: Path) -> None:
    rows = []
    for b in idx["books"]:
        cls = {"OK": "ok", "MISSING": "warn", "FAIL": "bad"}.get(b["state"], "dim")
        rows.append(
            f"<tr><td class='mono'>{b['id']}</td><td>{b['domain']}</td>"
            f"<td class='mono dim'>{b['path']}</td>"
            f"<td class='{cls}'>{b['state']}</td>"
            f"<td>{b.get('leaf_count', 0)}{'(截)' if b.get('truncated') else ''}</td>"
            f"<td class='mono dim'>{b.get('sha256', '')[:8]}</td>"
            f"<td>{'●' if b['conflict_scope'] else '—'}</td>"
            f"<td class='dim'>{b['note']}</td></tr>")
    crows = "".join(
        f"<tr><td class='mono'>{c['key']}</td><td class='mono dim'>"
        + "<br>".join(f"{p['book']}: {p['value']}" for p in c["books"]) + "</td></tr>"
        for c in idx["conflicts"]) or "<tr><td colspan=2 class='ok'>零衝突</td></tr>"
    lrows = "".join(
        f"<tr><td class='mono'>{a['name']}</td>"
        f"<td class='{'ok' if a['state'] == 'ALIGNED' else 'bad'}'>{a['state']}</td>"
        f"<td class='mono dim'>{a.get('pattern', '')}</td></tr>"
        for a in idx["locked_alignment"])
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA 中央參數樞紐</title><style>{CSS}</style></head><body>
<div class="card"><h1>中央參數樞紐 · Central Params SSOT</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">生成 {idx['generated']} · 冊 {idx['books_total']}(OK {idx['books_ok']} / MISSING {idx['books_missing']} / FAIL {idx['books_fail']})· 葉 {idx['leaf_total']:,} · 政策:{idx['policy']}</div></div>
<div class="card"><h1>參數 SSOT 冊索引(指標不搬家)</h1>
<table><tr><th>冊</th><th>域</th><th>路徑</th><th>態</th><th>葉數</th><th>sha8</th><th>衝突圈</th><th>說明</th></tr>{''.join(rows)}</table></div>
<div class="card"><h1>跨冊衝突(建議燈,候操作員裁決)</h1>
<table><tr><th>參數鍵</th><th>各冊值</th></tr>{crows}</table></div>
<div class="card"><h1>LOCKED Regex 對齊</h1>
<table><tr><th>名</th><th>態</th><th>pattern</th></tr>{lrows}</table></div>
</body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def run_scan(check_only=False, no_open=True, root: Path = VIA,
             index_path: Path = INDEX_PATH, ui_path: Path = UI_PATH) -> int:
    records = []
    for i, b in enumerate(BOOKS, 1):
        _sweep(f"掃 {b['id']}", i, len(BOOKS))
        records.append(scan_book(b, root))
    conflicts = find_conflicts(records)
    locked = locked_alignment(records)
    idx = build_index(records, conflicts, locked)
    n_drift = sum(1 for a in locked if a["state"] == "DRIFT")
    if not check_only:
        index_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
        render_ui(idx, ui_path)
        print(f"  [冊] 索引 {index_path.name} · U/I {ui_path.name}")
    print(f"  [計] 冊 OK {idx['books_ok']} · MISSING {idx['books_missing']} · FAIL {idx['books_fail']}"
          f" · 葉 {idx['leaf_total']:,} · 衝突 {len(conflicts)} · LOCKED DRIFT {n_drift}")
    for c in conflicts[:10]:
        print(f"  [衝] {c['key']} → " + " | ".join(f"{p['book']}={p['value'][:40]}" for p in c["books"]))
    red = idx["books_fail"] + n_drift
    return 1 if (check_only and red) else 0


# ── 七檢自測(沙盒零網路)───────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    # ① 冊登記表健全:路徑唯一、id 唯一
    paths = [b["path"] for b in BOOKS]
    ids = [b["id"] for b in BOOKS]
    chk("冊登記表唯一性", len(set(paths)) == len(paths) and len(set(ids)) == len(ids),
        f"({len(BOOKS)} 冊)")

    # ② flatten 葉數正確(巢狀+list)
    leaves = flatten({"a": {"b": 1, "c": [2, {"d": 3}]}, "e": "x"})
    chk("flatten 葉路徑", leaves == {"a.b": 1, "a.c[0]": 2, "a.c[1].d": 3, "e": "x"})

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # 合成兩冊:同鍵不同值=衝突;同鍵同值=無衝突
        (sand / "b1.json").write_text(json.dumps({"th": {"x": 1}, "same": 9}), encoding="utf-8")
        (sand / "b2.json").write_text(json.dumps({"th": {"x": 2}, "same": 9}), encoding="utf-8")
        recs = [scan_book({"id": "B1", "domain": "CONFIG", "conflict_scope": True,
                           "path": "b1.json", "note": ""}, sand),
                scan_book({"id": "B2", "domain": "CONFIG", "conflict_scope": True,
                           "path": "b2.json", "note": ""}, sand)]
        con = find_conflicts(recs)
        # ③ 衝突偵測:th.x 抓到
        chk("衝突偵測(異值)", len(con) == 1 and con[0]["key"] == "th.x")
        # ④ 同值不誤報
        chk("同值零誤報", all(c["key"] != "same" for c in con))
        # ⑤ sha 穩定+MISSING 誠實
        r_miss = scan_book({"id": "BX", "domain": "CONFIG", "conflict_scope": False,
                            "path": "nohere.json", "note": ""}, sand)
        chk("sha 穩定+缺冊誠實", recs[0]["sha256"] == scan_book(
            {"id": "B1", "domain": "CONFIG", "conflict_scope": True,
             "path": "b1.json", "note": ""}, sand)["sha256"]
            and r_miss["state"] == "MISSING")
        # ⑥ 索引冊寫讀 schema
        idx = build_index(recs + [r_miss], con, [])
        ip = sand / "idx.json"
        ip.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
        back = json.loads(ip.read_text(encoding="utf-8"))
        chk("索引冊 schema 寫讀", back["schema"] == "VIA.CentralParamsSSOT.v1"
            and back["books_ok"] == 2 and back["books_missing"] == 1
            and not any("_leaves" in b for b in back["books"]))
        # ⑦ U/I 產出含銘言刊頭+衝突列
        up = sand / "ui.html"
        render_ui(idx, up)
        h = up.read_text(encoding="utf-8")
        chk("U/I 銘言+衝突呈現", MOTTO in h and "th.x" in h)

        # ⑧ canonical 裁決解析六形態(沙盒合成冊)
        canon_dir = sand / "functional modules" / "VXX"
        canon_dir.mkdir(parents=True)
        (canon_dir / "VXX_Param_Registry_v0100.json").write_text(json.dumps({"canonical": {
            "D": {"ruling": "<TODAY;可覆寫 YYYY-MM-DD>"},
            "P": {"ruling": "<DYNAMIC:自引擎位置向上解析 VIA 根>"},
            "U": {"ruling": "<UNION:聯集>", "variants": ["['a','b']", "['b','c']"]},
            "S": {"ruling": "SCOPED(per-engine)"},
            "L": {"ruling": "'zh-TW'"}, "N": {"ruling": "20"}}}), encoding="utf-8")
        (canon_dir / "VXX_Param_Registry_v0101.json").write_text(json.dumps({"canonical": {
            "L": {"ruling": "'zh-TW'"}, "N": {"ruling": "25"}}}), encoding="utf-8")
        cx = json.loads((canon_dir / "VXX_Param_Registry_v0100.json").read_text())["canonical"]
        r_u, _ = _resolve_ruling(cx["U"])
        r_d, _ = _resolve_ruling(cx["D"], override="2026-01-01")
        chk("canonical 六形態解析",
            r_u == ["a", "b", "c"] and r_d == "2026-01-01"
            and _resolve_ruling(cx["S"])[0] is None
            and _resolve_ruling(cx["L"])[0] == "zh-TW" and _resolve_ruling(cx["N"])[0] == 20
            and len(_resolve_ruling(cx["D"])[0]) == 10)
        # ⑨ glob 最新版接任(v0101 蓋 v0100)+鍵缺誠實 KeyError
        newest = _canon_registry_path("VXX", sand)
        keyerr = False
        try:
            json.loads(newest.read_text())["canonical"]["NOPE"]
        except KeyError:
            keyerr = True
        chk("canonical glob 最新版+缺鍵誠實",
            newest.name.endswith("v0101.json") and keyerr
            and json.loads(newest.read_text())["canonical"]["N"]["ruling"] == "25")

    # central_get 實冊煙測(唯讀;冊缺容器亦過——找治理中心 LOCKED)
    hits = central_get("TW_TICKER_LOCKED.pattern")
    print(f"  [註] central_get 實冊煙測:{len(hits)} 命中(唯讀)")
    for _sub in CANON_SUBS:
        _n = len(canonical_list(_sub))
        print(f"  [註] canonical 實冊煙測:{_sub} {_n} 鍵(唯讀;0=冊缺誠實)")
    # ══ 批635 補二檢 ═══════════════════════════════════════════════
    import re as _re
    _here = Path(__file__).resolve().parent
    _via = _here.parent.parent
    _on = {Path(b["path"]).name for b in BOOKS}
    _skip = ("/.git/", "VIA_RetiredEngines", "node_modules", "regen_revert",
             "VIA_Reports/", "SCOPE_COPY", ".venv", "site-packages", "/candidates/",
             "references/intake", "/intake/", "config.template", "config.example",
             "freeze.lock", "/_output/", "/input/", "/output/", "schema.v", "_integration_")
    def _sk(q):
        t = str(q).replace("\\", "/")
        return any(x in t for x in _skip) or "_sha" in q.name
    # **自我指涉閘(LL133)**:問「這本冊有沒有讀者」的時候,要先把**自己家族**排掉。
    #   本器的 BOOKS 名冊裡逐字寫著每一本冊的路徑——不排掉自己,
    #   「有讀者」就會變成「名冊上有」,而那是同一句話講兩遍。
    #   制度健全度稽核 CGC_MDL164 的 ⑰ 當場抓到我這一版,抓得對。
    #   排法用樹上的正典記號 `_SELF_FAMILY`——閘認的就是這個名字(或字面
    #   `startswith("…")`)。我第一版寫成 `_self_fam`,閘照樣判 NO_EXCLUDE:
    #   **自己知道有排掉不算,要用看得懂的寫法讓閘也看得出來。**
    _SELF_FAMILY = "via_params_central"
    _src = []
    for q in _via.rglob("*.py"):
        if _sk(q) or q.name.startswith(_SELF_FAMILY):
            continue
        try:
            _src.append(q.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass
    _all = "\n".join(_src)
    _ver = _re.compile(r"_v\d{3,4}(?=\.json$)")
    _gap = []
    for q in _via.rglob("*.json"):
        if _sk(q) or q.name in _on:
            continue
        _t = (q.name + "|" + str(q)).upper()
        if not ("VRN" in _t or "VDF" in _t):
            continue
        if not _re.search(r"(SSOT|Registry|Rules|Params|Dict|Contract|Roster)", q.name, _re.I):
            continue
        if _re.search(r"(Preview|Hotfix|DryRun|Canonicalizer)", q.name, _re.I):
            continue
        if not any(len(k) > 8 and k in _all for k in
                   {q.name, _ver.sub("", q.name), q.stem, _ver.sub("_v*", q.name)}):
            continue
        try:
            _d = json.loads(q.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        def _lv(o):
            if isinstance(o, dict):
                return sum(_lv(v) for v in o.values())
            if isinstance(o, list):
                return sum(_lv(v) for v in o)
            return 1
        if _lv(_d) >= 5:
            _gap.append(q.name)
    chk("⑩ 名冊覆蓋:活樹 × 有引擎在讀 × 帶參數(葉≥5)的 VRN/VDF 冊,"
        "**一本都不可以漏在名冊外**。v0106 名冊 28 本,而這種冊有 49 本不在上面"
        "——所以當時的「衝突 0」不是沒有衝突,是只看了 28 本(L83)。"
        "這一檢釘住覆蓋,名冊再縮回去就會紅",
        not _gap, f"(漏在名冊外 {len(_gap)} 本{': ' + ', '.join(sorted(_gap)[:3]) if _gap else ''})")
    _fake = [
        {"id": "A", "state": "OK", "conflict_scope": True,
         "_leaves": {"x.generated_at": "2026-01-01", "x.status": "READY", "x.rate": 0.5}},
        {"id": "B", "state": "OK", "conflict_scope": True,
         "_leaves": {"x.generated_at": "2026-02-02", "x.status": "DONE", "x.rate": 0.7}},
    ]
    _fc = {c["key"] for c in find_conflicts(_fake)}
    chk("⑪ 中繼資料鍵**不准進衝突圈**:兩本冊的 `generated_at` / `status` 不同"
        "本來就該不同,算成衝突就是製造假紅——而假紅跟假綠一樣傷,"
        "看的人第二次就不看了。真的參數(x.rate)照樣要照得出來",
        _fc == {"x.rate"}, f"(照出 {sorted(_fc)})")
    # 批635:檢數現場計。原本寫死 `9 - len(fails)`,加了兩檢它還是印九
    #   ——寫死的檢數會把新加的檢從帳上抹掉(LL213)。
    n_all = 11
    n = n_all - len(fails)
    print(f"  [計] {n_all} 檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 中央參數樞紐 v0106 · 九檢自測(沙盒零網路)===")
        return selftest()
    if "--get" in args:
        i = args.index("--get")
        key = args[i + 1] if i + 1 < len(args) else ""
        if not key:
            print("[用法] via-params --get <dotted鍵或關鍵字>")
            return 2
        hits = central_get(key)
        if not hits:
            print(f"  [查] 「{key}」零命中(誠實)")
            return 0
        for h in hits:
            print(f"  [{h['book']}] {h['key']} = {str(h['value'])[:100]}")
        print(f"  [計] {len(hits)} 命中")
        return 0
    if "--canon" in args:
        i = args.index("--canon")
        rest = args[i + 1:]
        if not rest:
            print("[用法] via-params --canon <VRN|VDF|VAP> [NAME] [--date YYYY-MM-DD]")
            return 2
        sub = rest[0].upper()
        name = rest[1] if len(rest) > 1 and not rest[1].startswith("--") else ""
        ov = None
        if "--date" in args:
            j = args.index("--date")
            ov = args[j + 1] if j + 1 < len(args) else None
        if name:
            try:
                val = canonical_get(sub, name, override=ov)
                print(f"  [{sub}] {name} = {json.dumps(val, ensure_ascii=False, default=str)[:200]}")
                return 0
            except KeyError as exc:
                print(f"  [缺] {exc}(誠實)")
                return 1
        canon = canonical_list(sub)
        if not canon:
            print(f"  [缺] {sub} 參數冊缺或 canonical 區空(誠實)")
            return 1
        for k, e in sorted(canon.items()):
            v, mode = _resolve_ruling(e)
            print(f"  [{mode:>14}] {k} = {json.dumps(v, ensure_ascii=False, default=str)[:90]}")
        print(f"  [計] {sub} canonical {len(canon)} 鍵")
        return 0
    check_only = "--check" in args
    no_open = "--no-open" in args or check_only
    print(f"=== 中央參數樞紐 v0106 · {'驗證' if check_only else '全掃描'} · {len(BOOKS)} 冊(指標不搬家)===")
    rc = run_scan(check_only=check_only, no_open=no_open)
    if not no_open and UI_PATH.exists():
        try:
            import webbrowser
            webbrowser.open(UI_PATH.as_uri())
        except Exception:
            pass
    return rc


if __name__ == "__main__":
    sys.exit(main())
