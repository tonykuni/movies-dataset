# Z233 正式名稱待治理:工作清單(側線 2026-09-28 · R10)

MasterControl 頁上的 **486 處「正式名稱待治理」其實是 243 列**:每列在頁上出現兩次。容器實測:引擎 135 列(現役 47、退役存證 88;另有 1 支退役副本與現役同名,頁上不另列),治理模組 108 列。

**為什麼 AI 不自己補名字**:頁上的名字是從尾版 docstring 的第一行取的。這 243 支的第一行是英文變更說明,或者沒有說明字串。
我試過兩種自動取法:① 往回找較舊版本的第一行,只救回 23 列,其中幾列是「→:操作員…」這類殘句;② 在前六行裡找中文行,也大多是「用法 引擎」「產出 引擎」這種片段。
把這種殘句放上頁,比誠實寫「待治理」更糟,所以**正式名稱由操作員或 via 核定**(ruling 1「一擬建議」:只擬清單,不自動上名)。

**核定後怎麼上頁**:把核定的名稱寫進管理器的 `ENGINE_CANDIDATE_NAMES`(引擎)或各模組 docstring 第一行(模組,L04 開新版號)。這要開 VIA_SYSTEM_MANAGER 的新尾版,並重生 MasterControl 追蹤頁(CI test_11)。
自測 ⑦ 要求頁上仍有「正式名稱待治理」字樣,所以退役存證那批留著「待治理」是合規的。

## 現役功能引擎(47)

| 識別碼 | 尾版檔 | docstring 第一行(提示,不是名稱) | 擬名 |
|---|---|---|---|
| `VDF_ENG070_GroupClassificationIndex` | `VDF_ENG070_GroupClassificationIndex_v0112.py` | (v0111→v0112 批596「VDF_ENG070 真紅修」:根因=capital_style 空表守衛的欄位清單… |  |
| `VDF_ENG072_StoryRotationBridge` | `VDF_ENG072_StoryRotationBridge_v0103.py` | v0102→v0103(批690 PR #65 Codex P1):export() 回 NODATA 時沒設 err,… |  |
| `VDF_ENG074_FredMacroSSOT` | `VDF_ENG074_FredMacroSSOT_v0105.py` | VDF_ENG074_FredMacroSSOT tail. The newest file carries both … |  |
| `VDF_ENG075_MonthlyRevenueBackfill` | `VDF_ENG075_MonthlyRevenueBackfill_v0105.py` | VDF_ENG075_MonthlyRevenueBackfill tail. The newest file carr… |  |
| `VDF_ENG077_ActiveETFUniverse` | `VDF_ENG077_ActiveETFUniverse_v0104.py` | VDF_ENG077_ActiveETFUniverse tail. The newest file carries b… |  |
| `VDF_ENG078_ActiveETFHoldingsHistory` | `VDF_ENG078_ActiveETFHoldingsHistory_v0112.py` | VDF_ENG078_ActiveETFHoldingsHistory tail. The newest file ca… |  |
| `VDF_ENG087_MarketListGovernance` | `VDF_ENG087_MarketListGovernance_v0104.py` | VDF_ENG087 v0104 — two daily lists, both checked. |  |
| `VDF_ENG094_ActiveETFActivity` | `VDF_ENG094_ActiveETFActivity_v0100.py` | Active ETF interval analytics; offline, source-backed, expli… |  |
| `VDF_ENG095_InstrumentIdentity` | `VDF_ENG095_InstrumentIdentity_v0100.py` | VDF_ENG095 — display identity for a Taiwan ticker. |  |
| `VDF_ENG096_ActiveETFMeasures` | `VDF_ENG096_ActiveETFMeasures_v0100.py` | Measures from rows already stored. This file does not fetch. |  |
| `VDF_ENG097_GlobalETFFlow` | `VDF_ENG097_GlobalETFFlow_v0100.py` | VDF_ENG097 — classify global ETFs and compute net cash flow. |  |
| `VDF_ENG098_SameDayAlign` | `VDF_ENG098_SameDayAlign_v0100.py` | VDF_ENG098 — one Taiwan stock, one date. |  |
| `VDF_ENG099_IndexSameDay` | `VDF_ENG099_IndexSameDay_v0100.py` | VDF_ENG099 — TAIEX and TPEx index rows follow the stock day. |  |
| `VDF_ENG100_FinStatementQuery` | `VDF_ENG100_FinStatementQuery_v0101.py` | VDF_ENG100 v0101 — bare EPS, actuals, and display dates. |  |
| `VDF_ENG101_SourceProbe` | `VDF_ENG101_SourceProbe_v0100.py` | VDF_ENG101 — who is allowed into the next live test. |  |
| `VDF_ENG102_SourceLane` | `VDF_ENG102_SourceLane_v0101.py` | VDF_ENG102 v0101 — live check of two names. No database writ… |  |
| `VDF_ENG103_ListingName` | `VDF_ENG103_ListingName_v0100.py` | Short names for tickers already cut from a filename. Uses EN… |  |
| `VDF_ENG109_USMacroList` | `VDF_ENG109_USMacroList_v0100.py` | VCGC door into the US macro lists. Read-only. Does not fetch… |  |
| `VDF_ENG110_AKShareProbe` | `VDF_ENG110_AKShareProbe_v0102.py` | AKShare probe. Refuses a raw python call. The central launch… |  |
| `VDF_ENG110_USMacroProbe` | `VDF_ENG110_USMacroProbe_v0101.py` | Same one-point probe. The key comes from the environment or … |  |
| `VDF_ENG110_USMacroTree` | `VDF_ENG110_USMacroTree_v0100.py` | VCGC door for the US macro tree. Checks the process SSOT. Do… |  |
| `VDF_ENG111_USMacroAgency` | `VDF_ENG111_USMacroAgency_v0100.py` | VCGC door for agency sources. Read-only. Does not fetch. |  |
| `VDF_ENG112_FedMore` | `VDF_ENG112_FedMore_v0100.py` | VCGC door for the extra Fed series. Read-only. |  |
| `VDF_ENG113_MacroMethod` | `VDF_ENG113_MacroMethod_v0101.py` | Same Fed-method refresh. The live us_macro table has three c… |  |
| `VDF_ENG114_PmiPair` | `VDF_ENG114_PmiPair_v0100.py` | Two PMI prints per economy that this AKShare actually has. D… |  |
| `VDF_ENG115_SentimentFetch` | `VDF_ENG115_SentimentFetch_v0101.py` | AAII: spreadsheet first, survey page second. A block page st… |  |
| `VDF_ENG116_AAIIWorkbook` | `VDF_ENG116_AAIIWorkbook_v0101.py` | Load the AAII workbook. Dates must be YYYY-MM-DD and numbers… |  |
| `VDF_ENG117_ForwardVintage` | `VDF_ENG117_ForwardVintage_v0101.py` | Point-in-time forward valuation vintage reference implementa… |  |
| `VDF_ENG117_ForwardVintageDoor` | `VDF_ENG117_ForwardVintageDoor_v0100.py` | Run the VDF copy of the forward-vintage engine. Does not edi… |  |
| `VDF_ENG118_ExportDesk` | `VDF_ENG118_ExportDesk_v0100.py` | Show the fetch inputs and database inventory. Export a short… |  |
| `VDF_ENG118_TWMarket` | `VDF_ENG118_TWMarket_v0100.py` | One TWSE list and one TPEX list. A code that answers decides… |  |
| `VDF_ENG119_StartTestRegister` | `VDF_ENG119_StartTestRegister_v0102.py` | Tail of the start-test register. v0101 still draws the matri… |  |
| `VRN_ENG036_FinalizeCoreV2` | `VRN_ENG036_FinalizeCoreV2.py` | VRN Finalize AIO - embedded Python core |  |
| `VRN_ENG079_ControlTowerDashboard` | `VRN_ENG079_ControlTowerDashboard_v0101.py` | v0100→v0101(批732;操作員 09-24「上漲空間都要用最新的ADJ CLOSE」;Z157 共識線的 VR… |  |
| `VRN_ENG080_FourPointDigest` | `VRN_ENG080_FourPointDigest_v0110.py` | v0109→v0110(批730 操作員 2026-09-24 令「自測實測自AUDIT直到完工 結果也要實測正確性」)… |  |
| `VRN_ENG087_NLPTextSummaryBridge` | `VRN_ENG087_NLPTextSummaryBridge_v0101.py` | VRN_ENG087_NLPTextSummaryBridge v0100 |  |
| `VRN_ENG103_SourceLaneJoin` | `VRN_ENG103_SourceLaneJoin_v0100.py` | VRN reads the sealed TWSE/TPEX/yfinance rows. It does not fe… |  |
| `VRN_ENG104_FilenameCut` | `VRN_ENG104_FilenameCut_v0100.py` | Cut a report filename at every script change. Rules stay on … |  |
| `VRN_ENG105_PageCrosscheck` | `VRN_ENG105_PageCrosscheck_v0100.py` | Three ticker forms must share one core. Zones must agree bef… |  |
| `VRN_ENG106_ReadLanes` | `VRN_ENG106_ReadLanes_v0100.py` | Say whether a page was read by one engine, two engines, or s… |  |
| `VRN_ENG107_TextRestore` | `VRN_ENG107_TextRestore_v0100.py` | Join wrapped lines and cut sentences. Does not invent a char… |  |
| `VRN_ENG108_StatementCheck` | `VRN_ENG108_StatementCheck_v0100.py` | Read one statement table and check it. Basic EPS and diluted… |  |
| `VRN_ENG109_GateMap` | `VRN_ENG109_GateMap_v0100.py` | Map a logic result onto the store gate. The original row is … |  |
| `VRN_ENG109_TabStore` | `VRN_ENG109_TabStore_v0101.py` | Same tab store. The engine tree and the database root may be… |  |
| `VRN_ENG110_TabReport` | `VRN_ENG110_TabReport_v0116.py` | Show every broker as its English short name. 兆豐 is MEGA. WAT… |  |
| `VRN_ENG111_StockIdentity` | `VRN_ENG111_StockIdentity_v0104.py` | Every broker shows its English short name. 兆豐 is MEGA. WATER… |  |
| `VRN_ENG112_FinancialRead` | `VRN_ENG112_FinancialRead_v0100.py` | Read labeled financial lines. An actual covers a forecast. A… |  |

## 中央治理模組(108)

| 識別碼 | 尾版檔 | docstring 第一行(提示,不是名稱) | 擬名 |
|---|---|---|---|
| `CGC_MDL023_AutoCodeRegistryEngine` | `CGC_MDL023_AutoCodeRegistryEngine.py` | def VDF_AutoCodeRegistryEngine.py |  |
| `CGC_MDL028_ManifestFetchAdapter` | `CGC_MDL028_ManifestFetchAdapter.py` | VDF Manifest Fetch Adapter |  |
| `CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573` | `CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573.py` | (無說明字串) |  |
| `CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE` | `CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE_v0611.py` | (無說明字串) |  |
| `CGC_MDL040_PyAudit7ae60dd6d6134056bfab27bb6751e35d` | `CGC_MDL040_PyAudit7ae60dd6d6134056bfab27bb6751e35d.py` | (無說明字串) |  |
| `CGC_MDL043_AutocoderEngine` | `CGC_MDL043_AutocoderEngine_v0100.py` | (無說明字串) |  |
| `CGC_MDL048_DownloadsRegisterAllCrossAnalysisBuilderV20260702` | `CGC_MDL048_DownloadsRegisterAllCrossAnalysisBuilderV20260702.py` | VIA Downloads Register All + Cross Analysis Builder |  |
| `CGC_MDL059_MasterHub` | `CGC_MDL059_MasterHub_v0108.py` | via_master_hub_v0108 — VIA Central Governance Console(活數補齊版) |  |
| `CGC_MDL064_SelftestGrid` | `CGC_MDL064_SelftestGrid_v0498.py` | v0497→v0498(側線 2026-09-25 第十六段 · TA-Lib 全拔;主線批號由併線的手指定 L25): |  |
| `CGC_MDL066_StructureForge` | `CGC_MDL066_StructureForge.py` | VIA Structure Forge v2.0 |  |
| `CGC_MDL069_SystemManager` | `CGC_MDL069_SystemManager_v0114.py` | SYSTEM MANAGER: discover engine headers using AST, expose th… |  |
| `CGC_MDL075_CentralGov` | `CGC_MDL075_CentralGov_v0106.py` | via_central_gov_v0104 — VIA Central Governance Console(TOOL-… |  |
| `CGC_MDL095_DeckServer` | `CGC_MDL095_DeckServer_v0160.py` | v0159→v0160(批733;操作員 09-24「上漲空間都要用最新的ADJ CLOSE」;掉球 Z157 的指揮台… |  |
| `CGC_MDL098_DataCatalog` | `CGC_MDL098_DataCatalog_v0103.py` | # v0102→v0103(批693 Z92 誠實燈):v0102 只探「庫檔在不在」;庫在但一張表都沒有(容器/新機)… |  |
| `CGC_MDL122_IntakeRoster` | `CGC_MDL122_IntakeRoster_v0113.py` | CGC_MDL122_IntakeRoster v0113 — 上船件冊(批383 +Grok 主控台接回冊(river… |  |
| `CGC_MDL124_BridgeSweeper` | `CGC_MDL124_BridgeSweeper_v0107.py` | v0106→v0107(批731 操作員 2026-09-24「PS PY檔案都要依規定裝加速器」): |  |
| `CGC_MDL127_SixStreams` | `CGC_MDL127_SixStreams_v0102.py` | CGC_MDL127_SixStreams v0102 — 六流程零九頭龍派工引擎(批365 旗艦 Mega-Promp… |  |
| `CGC_MDL131_ProjectCompletion` | `CGC_MDL131_ProjectCompletion_v0106.py` | CGC_MDL131_ProjectCompletion v0106 — 四專案完工矩陣(批390 工作站實錄「AETF… |  |
| `CGC_MDL135_EnvGovernance` | `CGC_MDL135_EnvGovernance_v0117.py` | v0116→v0117(批734 全景代讀量到 DUPDEF 1;原 PR #104 修在 v0115,main 已升 … |  |
| `CGC_MDL135_EnvPlan` | `CGC_MDL135_EnvPlan_v0100.py` | Environment plan on top of the existing conflict lists. It d… |  |
| `CGC_MDL143_MergeMedic` | `CGC_MDL143_MergeMedic_v0104.py` | CGC_MDL143_MergeMedic v0102 — 拉齊醫生(批393 工作站實況抓到真 bug:同名雙物正規式… |  |
| `CGC_MDL144_CopyDoctor` | `CGC_MDL144_CopyDoctor_v0102.py` | CGC_MDL144_CopyDoctor v0101 — 副本醫生(批391 我方指令寫死版號之錯(給 v0175 但… |  |
| `CGC_MDL149_BoxesFlow` | `CGC_MDL149_BoxesFlow_v0100.py` | VCGC door. Column reading order. Read-only. |  |
| `CGC_MDL149_ChainAll` | `CGC_MDL149_ChainAll_v0101.py` | One VCGC pass. A missing param_ids no longer drops the other… |  |
| `CGC_MDL149_Closeout` | `CGC_MDL149_Closeout_v0101.py` | VCGC closeout. The console stops here. Open lamps stay open.… |  |
| `CGC_MDL149_EntryLock` | `CGC_MDL149_EntryLock_v0101.py` | Entry lock. The policy hash ignores line endings. Does not r… |  |
| `CGC_MDL149_FilenameCut` | `CGC_MDL149_FilenameCut_v0100.py` | VCGC door: cut sample filenames, then ask VDF for the exchan… |  |
| `CGC_MDL149_GreenMatrix` | `CGC_MDL149_GreenMatrix_v0100.py` | Green matrix of the synced stock-report rows. Reads the file… |  |
| `CGC_MDL149_Identity` | `CGC_MDL149_Identity_v0100.py` | VIA and VCGC are one door. Not two systems. |  |
| `CGC_MDL149_Integrate` | `CGC_MDL149_Integrate_v0100.py` | VCGC door. One read-only pass over the pieces already measur… |  |
| `CGC_MDL149_LayoutUse` | `CGC_MDL149_LayoutUse_v0100.py` | VCGC door. Use the existing four-zone cut. Read-only. |  |
| `CGC_MDL149_OneDragon` | `CGC_MDL149_OneDragon_v0100.py` | One read-only pass: policy sections, environment inspection,… |  |
| `CGC_MDL149_PageCrosscheck` | `CGC_MDL149_PageCrosscheck_v0100.py` | VCGC door. Filename to three codes. PDF engines are listed, … |  |
| `CGC_MDL149_PasteBlock` | `CGC_MDL149_PasteBlock_v0101.py` | Compact JSON paste. Log, handover, and lessons are collected… |  |
| `CGC_MDL149_ReadLanes` | `CGC_MDL149_ReadLanes_v0100.py` | Re-judge stock first pages. Paddle is reported, not called. |  |
| `CGC_MDL149_RoundMatrix` | `CGC_MDL149_RoundMatrix_v0100.py` | One round. Classify first. This round writes nothing in the … |  |
| `CGC_MDL149_SourceLane` | `CGC_MDL149_SourceLane_v0101.py` | VCGC door for the two-name live check. Does not open the gat… |  |
| `CGC_MDL149_StatementCheck` | `CGC_MDL149_StatementCheck_v0100.py` | VCGC door. Read statement pages already on disk. No quote re… |  |
| `CGC_MDL149_Sync` | `CGC_MDL149_Sync_v0102.py` | One VCGC pass over stock reports. VDF supplies the name. VRN… |  |
| `CGC_MDL149_TableTake` | `CGC_MDL149_TableTake_v0101.py` | VCGC door. pdfplumber accuracy. Still read-only. |  |
| `CGC_MDL149_TextGrade` | `CGC_MDL149_TextGrade_v0100.py` | VCGC door. Grade the text layer. Do not OCR. |  |
| `CGC_MDL149_UnitScale` | `CGC_MDL149_UnitScale_v0101.py` | CGC_MDL149 UnitScale v0101. From VCGC. No fetch. No policy-b… |  |
| `CGC_MDL149_VRNEnter` | `CGC_MDL149_VRNEnter_v0101.py` | Lock the green lamps from the 03:23 measurement, then read V… |  |
| `CGC_MDL149_VRNLive` | `CGC_MDL149_VRNLive_v0100.py` | VCGC to VRN: sealed quotes, then filename survey of the samp… |  |
| `CGC_MDL149_VeritasCentralGovernanceConsole` | `CGC_MDL149_VeritasCentralGovernanceConsole_v0162.py` | Console tail v0162. Only `layout ... --selftest` changes. |  |
| `CGC_MDL149_WorkflowMatrix` | `CGC_MDL149_WorkflowMatrix_v0100.py` | Seven gates, one matrix. A failed gate stays on the matrix. … |  |
| `CGC_MDL155_VIAUnifiedSSOTAutoCode` | `CGC_MDL155_VIAUnifiedSSOTAutoCode_v0101.py` | CGC_MDL155 — VIA Unified SSOT / AutoCode Gateway. |  |
| `CGC_MDL156_VIAAcceleratorControl` | `CGC_MDL156_VIAAcceleratorControl_v0110.py` | CGC_MDL156: VIA 25-accelerator control plane. |  |
| `CGC_MDL157_VIAUniqueEntryControl` | `CGC_MDL157_VIAUniqueEntryControl_v0105.py` | CGC_MDL157: VIA unique entry-point control plane. |  |
| `CGC_MDL164_GovernanceCompletenessAudit` | `CGC_MDL164_GovernanceCompletenessAudit_v0109.py` | v0108→v0109(批691B:⑰ 把 **L77 的排除清單**誤讀成「這支在回答誰引用」): |  |
| `CGC_MDL165_CommandRunGate` | `CGC_MDL165_CommandRunGate_v0101.py` | CGC_MDL165:短令能跑閘(批584;操作員令「我不懂程式系統,請幫我完成這些」)。 |  |
| `CGC_MDL166_LibraryConsolidationGate` | `CGC_MDL166_LibraryConsolidationGate_v0100.py` | CGC_MDL166:四庫整合遺漏閘(批585;操作員令「參數庫/邏輯庫/政策庫/因子庫 整合有無遺漏」)。 |  |
| `CGC_MDL186_EnvGovernance_8Hub` | `CGC_MDL186_EnvGovernance_8Hub_v0100.py` | Eight local conflict checks and a guarded uv install lane fo… |  |
| `CGC_MDL189_GitHubSyncEngine` | `CGC_MDL189_GitHubSyncEngine_v0101.py` | GitHub sync plus a skeleton pack. The pack is written outsid… |  |
| `CGC_MDL190_TALibLock` | `CGC_MDL190_TALibLock_v0100.py` | VCGC entry check. A live file may not import TA-Lib. |  |
| `CGC_MDL191_KnowledgeAsset` | `CGC_MDL191_KnowledgeAsset_v0100.py` | VCGC knowledge-asset check. Read-only. Does not move files o… |  |
| `CGC_MDL192_MacroParamSync` | `CGC_MDL192_MacroParamSync_v0101.py` | Same parameter check. Line endings are not a drift. |  |
| `CGC_MDL193_AuditFixLock` | `CGC_MDL193_AuditFixLock_v0100.py` | The audit's confirmed ticker and page-count fixes are presen… |  |
| `CGC_MDL193_BrokerMarketLock` | `CGC_MDL193_BrokerMarketLock_v0100.py` | DAIWA and HuaNan are on the broker list. The exchange list p… |  |
| `CGC_MDL193_BrokerShowLock` | `CGC_MDL193_BrokerShowLock_v0100.py` | The shown broker is the short canonical name, and a filename… |  |
| `CGC_MDL193_FinancialReadLock` | `CGC_MDL193_FinancialReadLock_v0100.py` | Financial rows are labeled observations. Actual covers forec… |  |
| `CGC_MDL193_FinancialShownLock` | `CGC_MDL193_FinancialShownLock_v0100.py` | Record the financial rows that were shown. Do not reread the… |  |
| `CGC_MDL193_ForwardVintageLock` | `CGC_MDL193_ForwardVintageLock_v0101.py` | Same forward-vintage lock. LF and CRLF of the same text are … |  |
| `CGC_MDL193_GateMapLock` | `CGC_MDL193_GateMapLock_v0100.py` | Lock the store-gate mapping. It does not read a report or wr… |  |
| `CGC_MDL193_MarketSync` | `CGC_MDL193_MarketSync_v0101.py` | Same market lock. AAII is the loaded workbook, not the old a… |  |
| `CGC_MDL193_ProbeLock` | `CGC_MDL193_ProbeLock_v0100.py` | Lock the 19:15 probe. Read-only. Does not refetch and does n… |  |
| `CGC_MDL193_ReportMeasureLock` | `CGC_MDL193_ReportMeasureLock_v0101.py` | Lock the later report measurement. It does not reread the fo… |  |
| `CGC_MDL193_ReportWireLock` | `CGC_MDL193_ReportWireLock_v0100.py` | The report command exists, and the new door does not invent … |  |
| `CGC_MDL193_StatusLock` | `CGC_MDL193_StatusLock_v0105.py` | Lock pass. The printed path is the path that runs. |  |
| `CGC_MDL193_StockIdentityLock` | `CGC_MDL193_StockIdentityLock_v0100.py` | The stock path keeps the filename code when the page repeats… |  |
| `CGC_MDL193_TabFieldLock` | `CGC_MDL193_TabFieldLock_v0100.py` | Lock the three VRN tab field lists. Does not read a report. |  |
| `CGC_MDL193_VrnTabLock` | `CGC_MDL193_VrnTabLock_v0101.py` | Lock the split between the engine tree and the database root… |  |
| `CGC_MDL194_ReportUpdate` | `CGC_MDL194_ReportUpdate_v0101.py` | Status report from the normalized lock check. Does not chang… |  |
| `CGC_MDL195_FetchMatrix` | `CGC_MDL195_FetchMatrix_v0100.py` | Read the VDF fetch matrix. Does not download and does not ed… |  |
| `CGC_MDL196_RouteDeck` | `CGC_MDL196_RouteDeck_v0100.py` | Panorama of the VCGC route and the prepared left/right page.… |  |
| `CGC_MDL197_NlpOneEngine` | `CGC_MDL197_NlpOneEngine_v0100.py` | Register NLP OneEngine 1.9.0. It does not read PDFs or fill … |  |
| `CGC_MDL197_NlpRoster` | `CGC_MDL197_NlpRoster_v0100.py` | Register the new NLP entry beside the old engines. None of t… |  |
| `CGC_MDL198_Closeout` | `CGC_MDL198_Closeout_v0100.py` | Closeout. VCGC and VDF managers pass their own tests. VRN st… |  |
| `CGC_MDL199_NlpUses` | `CGC_MDL199_NlpUses_v0100.py` | Name the NLP uses that already sit inside 1.8. Do not call t… |  |
| `CGC_MDL199_SupportTier` | `CGC_MDL199_SupportTier_v0100.py` | Support tier. Accelerator, network, and NLP sit together. Ea… |  |
| `CGC_MDL200_RelatedIntake` | `CGC_MDL200_RelatedIntake_v0100.py` | Register related tools that were not already in VCGC. |  |
| `CGC_MDL201_VrnManagerRead` | `CGC_MDL201_VrnManagerRead_v0100.py` | Lock the VRN manager reading. Do not run the body and do not… |  |
| `CGC_MDL202_LayoutEngine` | `CGC_MDL202_LayoutEngine_v0100.py` | Register the layout tail. Do not rerun the 45 tests and do n… |  |
| `CGC_MDL203_LayoutCodes` | `CGC_MDL203_LayoutCodes_v0101.py` | Layout code lock. A checker named Talib is not the TA-Lib pa… |  |
| `CGC_MDL204_NlpCodes` | `CGC_MDL204_NlpCodes_v0100.py` | Confirm the NLP roster now has central codes. Do not call th… |  |
| `CGC_MDL205_TalibBan` | `CGC_MDL205_TalibBan_v0100.py` | L50 panoramic check. TA-Lib must not be installed and no liv… |  |
| `CGC_MDL206_TalibPolicy` | `CGC_MDL206_TalibPolicy_v0101.py` | Confirm L50 is wired. LF and CRLF are one book, not two hash… |  |
| `CGC_MDL207_PolicyRun` | `CGC_MDL207_PolicyRun_v0101.py` | Run the one policy executor on the newest tail. Still one en… |  |
| `CGC_MDL208_VdfMeasure` | `CGC_MDL208_VdfMeasure_v0100.py` | Measure VDF through its own gate. No second manager and no f… |  |
| `CGC_MDL209_VdfStart` | `CGC_MDL209_VdfStart_v0100.py` | Start the VDF manager from VCGC. Status only. No fetch. |  |
| `CGC_MDL210_TWBackfillLock` | `CGC_MDL210_TWBackfillLock_v0100.py` | VCGC record of the measured backfill tail. Read-only. No fet… |  |
| `CGC_MDL211_FlowGate` | `CGC_MDL211_FlowGate_v0101.py` | Flow gate tail. The policy read stays. The panoramic ban run… |  |
| `CGC_MDL212_DataSeat` | `CGC_MDL212_DataSeat_v0100.py` | One computer, one database root. GitHub is not that root. |  |
| `CGC_MDL213_ShutdownRecord` | `CGC_MDL213_ShutdownRecord_v0100.py` | The books stay at the pre-shutdown Git records. This door do… |  |
| `CGC_MDL214_VdfHandover` | `CGC_MDL214_VdfHandover_v0100.py` | Handover of the successful VDF version. v0109 stays. This do… |  |
| `CGC_MDL215_TWProbe` | `CGC_MDL215_TWProbe_v0100.py` | The one-ticker probe stays a record. It does not refetch and… |  |
| `CGC_MDL216_NlpLayoutDoor` | `CGC_MDL216_NlpLayoutDoor_v0100.py` | One outside door for NLP and Layout. The engines stay where … |  |
| `CGC_MDL217_ManagerMatrix` | `CGC_MDL217_ManagerMatrix_v0100.py` | Manager matrix. One list of the three system managers and th… |  |
| `CGC_MDL218_BookPointer` | `CGC_MDL218_BookPointer_v0100.py` | Point the new VCGC routes at the locked policy, logic, and p… |  |
| `CGC_MDL219_RegexParamSync` | `CGC_MDL219_RegexParamSync_v0100.py` | Record that the regex book, the synonym book, and the parame… |  |
| `CGC_MDL220_SuccessLedger` | `CGC_MDL220_SuccessLedger_v0100.py` | Read the success ledger. Older locks stay. Later greens are … |  |
| `CGC_MDL221_SystemBackup` | `CGC_MDL221_SystemBackup_v0100.py` | Register the VCGC and VDF tails that just passed. This door … |  |
| `CGC_MDL222_SubsystemProbe` | `CGC_MDL222_SubsystemProbe_v0100.py` | Probe the subsystem tails from VCGC and sync the seat when a… |  |
| `CGC_MDL223_FlowConsistency` | `CGC_MDL223_FlowConsistency_v0100.py` | Run the VCGC policy, sync the subsystem managers, then allow… |  |
| `CGC_MDL224_ScrapeGate` | `CGC_MDL224_ScrapeGate_v0100.py` | One scrape ruler. Empty and OFF stay closed. YES and the com… |  |
| `CGC_MDL224_TestAuto` | `CGC_MDL224_TestAuto_v0100.py` | Run the VCGC selftests in one pass. Nothing is fetched and n… |  |
| `CGC_MDL225_VersionPanorama` | `CGC_MDL225_VersionPanorama_v0100.py` | Panorama of the four live engines. Each one must be a versio… |  |
| `CGC_MDL226_StepMatrix` | `CGC_MDL226_StepMatrix_v0100.py` | Mandatory step matrix. Every VCGC action passes these steps … |  |

## 退役存證引擎(歷史,最後處理)(88)

| 識別碼 | 尾版檔 | docstring 第一行(提示,不是名稱) | 擬名 |
|---|---|---|---|
| `CHW_ENG008_PurifiedSectorRotationAccuracyEngineV2` | `CHW_ENG008_PurifiedSectorRotationAccuracyEngineV2.py` | (無說明字串) |  |
| `CHW_ENG010_SsotMatchingTestingEngine` | `CHW_ENG010_SsotMatchingTestingEngine.py` | (無說明字串) |  |
| `CHW_ENG011_ViaEngineVerificationSuite` | `CHW_ENG011_ViaEngineVerificationSuite.py` | (無說明字串) |  |
| `CHW_ENG012_ViaExactDatasetTestEngine` | `CHW_ENG012_ViaExactDatasetTestEngine.py` | (無說明字串) |  |
| `CHW_ENG013_ViaSystemIntegrationTestSuite` | `CHW_ENG013_ViaSystemIntegrationTestSuite_v0101.py` | (無說明字串) |  |
| `CHW_ENG018_FomoIndexReport` | `CHW_ENG018_FomoIndexReport.py` | FOMO Index report — Visual Lock + FlowSystem verdict style. |  |
| `CHW_ENG020_RotationPlugInEngine` | `CHW_ENG020_RotationPlugInEngine.py` | (無說明字串) |  |
| `CHW_ENG022_SocialReport` | `CHW_ENG022_SocialReport.py` | Social FOMO lane report — Visual Lock. |  |
| `CHW_ENG025_XmktReport` | `CHW_ENG025_XmktReport.py` | Cross-market FOMO factor lab report — Visual Lock. |  |
| `CHW_ENG026_CodeArtifact3` | `CHW_ENG026_CodeArtifact3.py` | (無說明字串) |  |
| `GRP_ENG002_ActiveStockETFMocktest` | `GRP_ENG002_ActiveStockETFMocktest.py` | VIA_ActiveStockETF_mocktest.py |  |
| `GRP_ENG004_ChipWarRevenueEvidence` | `GRP_ENG004_ChipWarRevenueEvidence_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG005_ETFConsolesEvidence` | `GRP_ENG005_ETFConsolesEvidence_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG010_GroupIndexMasterValidation` | `GRP_ENG010_GroupIndexMasterValidation_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG011_LiveWireContractAdapter` | `GRP_ENG011_LiveWireContractAdapter_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG012_SectorFlowAdaptiveChainedIndex` | `GRP_ENG012_SectorFlowAdaptiveChainedIndex_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG013_SectorFlowDashboardBuilder` | `GRP_ENG013_SectorFlowDashboardBuilder_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG014_SectorFlowSignalTradeBacktest` | `GRP_ENG014_SectorFlowSignalTradeBacktest_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG016_ThreeListGroupingDynamicValidationPipeline` | `GRP_ENG016_ThreeListGroupingDynamicValidationPipeline_v0201.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `GRP_ENG038_SubgroupSandboxValidation` | `GRP_ENG038_SubgroupSandboxValidation_v0100.py` | VERITAS INTELLIGENCE ANALYTICS |  |
| `VDF_ENG006_MDL004TWFullMarketEngine` | `VDF_ENG006_MDL004TWFullMarketEngine.py` | ============================================================… |  |
| `VDF_ENG011_MDL102FormatUpgrader` | `VDF_ENG011_MDL102FormatUpgrader.py` | ============================================================… |  |
| `VDF_ENG017_MDL302FinalActivation` | `VDF_ENG017_MDL302FinalActivation.py` | ============================================================… |  |
| `VDF_ENG020_MDL097VrnFinancialdataFinalEvidenceSelectorV06149FINANCIALDATAV06149` | `VDF_ENG020_MDL097VrnFinancialdataFinalEvidenceSelectorV06149FINANCIALDATAV06149.py` | (無說明字串) |  |
| `VDF_ENG021_MDL215VrnFinancialdataTriflowStagingV06153FINANCIALDATAV06153` | `VDF_ENG021_MDL215VrnFinancialdataTriflowStagingV06153FINANCIALDATAV06153.py` | (無說明字串) |  |
| `VDF_ENG022_MDL218VrnFinancialDataConfirmVerifyV06125FINANCIALDATAV06125` | `VDF_ENG022_MDL218VrnFinancialDataConfirmVerifyV06125FINANCIALDATAV06125.py` | (無說明字串) |  |
| `VDF_ENG023_MDL252VrnFinancialFinalSealV06127FINANCIALDATAV06127` | `VDF_ENG023_MDL252VrnFinancialFinalSealV06127FINANCIALDATAV06127.py` | (無說明字串) |  |
| `VDF_ENG024_MDL253VrnFinancialFinalSealV06127FINANCIALDATAV06127` | `VDF_ENG024_MDL253VrnFinancialFinalSealV06127FINANCIALDATAV06127.py` | (無說明字串) |  |
| `VDF_ENG031_MDL001TWUniverseVerify` | `VDF_ENG031_MDL001TWUniverseVerify.py` | ============================================================… |  |
| `VDF_ENG039_Inject` | `VDF_ENG039_Inject.py` | VIA_Inject — 第5步：把 VIA_VDF_Bridge 標準輸出 → 兩模板各自的資料結構並注入 HTML |  |
| `VDF_ENG043_MDL201ForecastMatrixIntegratedV1` | `VDF_ENG043_MDL201ForecastMatrixIntegratedV1.py` | VDF_MDL201_ForecastMatrix_Integrated_v1 |  |
| `VIA_ENG001_MultiFactorTestValidateSimEngine` | `VIA_ENG001_MultiFactorTestValidateSimEngine_v0100.py` | VIA MultiFactor Test / Validate / Simulate Engine v0.1.00 |  |
| `VIA_ENG018_DuckParquetAcceptance` | `VIA_ENG018_DuckParquetAcceptance.py` | (無說明字串) |  |
| `VIA_ENG019_MeetingloopEngine` | `VIA_ENG019_MeetingloopEngine.py` | (無說明字串) |  |
| `VIA_ENG020_SuperBOMContentParser` | `VIA_ENG020_SuperBOMContentParser_v0100.py` | (無說明字串) |  |
| `VIA_ENG021_MasterEngine` | `VIA_ENG021_MasterEngine_v0103.py` | ============================================================… |  |
| `VIA_ENG022_VmtConvergence` | `VIA_ENG022_VmtConvergence.py` | ============================================================… |  |
| `VIA_ENG023_VmtPlanningCpm` | `VIA_ENG023_VmtPlanningCpm.py` | ============================================================… |  |
| `VIA_ENG024_VmtProcessMining` | `VIA_ENG024_VmtProcessMining.py` | ============================================================… |  |
| `VIA_ENG025_VmtReplyIngest` | `VIA_ENG025_VmtReplyIngest.py` | ============================================================… |  |
| `VIA_ENG026_VmtSuperbomAttachRouter` | `VIA_ENG026_VmtSuperbomAttachRouter.py` | ============================================================… |  |
| `VIA_ENG027_VmtSuperbomBridge` | `VIA_ENG027_VmtSuperbomBridge.py` | ============================================================… |  |
| `VIA_ENG028_VmtSuperbomEventstream` | `VIA_ENG028_VmtSuperbomEventstream.py` | ============================================================… |  |
| `VIA_ENG029_VmtSurvey` | `VIA_ENG029_VmtSurvey.py` | ============================================================… |  |
| `VIA_ENG047_ValidateLexicon` | `VIA_ENG047_ValidateLexicon.py` | VTR SSOT Lexicon validator / indexer. |  |
| `VIA_ENG048_BuildManifest` | `VIA_ENG048_BuildManifest.py` | 重算 VTR_Subsystem_Manifest.json。 |  |
| `VIA_ENG055_EmailActionDb` | `VIA_ENG055_EmailActionDb.py` | email_action_db.py  v1.0 |  |
| `VIA_ENG056_EmailSuperEngine` | `VIA_ENG056_EmailSuperEngine.py` | email_super_engine.py  v1.1 |  |
| `VIA_ENG057_EngineAnalytics` | `VIA_ENG057_EngineAnalytics.py` | engine_analytics.py  v1.3 |  |
| `VIA_ENG066_WorkopsCorpusBridge` | `VIA_ENG066_WorkopsCorpusBridge.py` | (無說明字串) |  |
| `VIA_ENG068_WorkopsDecisionLog` | `VIA_ENG068_WorkopsDecisionLog.py` | (無說明字串) |  |
| `VIA_ENG069_WorkopsEnvmanagerBridge` | `VIA_ENG069_WorkopsEnvmanagerBridge.py` | (無說明字串) |  |
| `VIA_ENG070_WorkopsGraphvizSetup` | `VIA_ENG070_WorkopsGraphvizSetup.py` | (無說明字串) |  |
| `VIA_ENG076_WorkopsNamer` | `VIA_ENG076_WorkopsNamer.py` | (無說明字串) |  |
| `VIA_ENG105_WorkopsApiServer` | `VIA_ENG105_WorkopsApiServer.py` | Localhost-only FastAPI product server. |  |
| `VIA_ENG106_WorkopsAttachmentIntelligence` | `VIA_ENG106_WorkopsAttachmentIntelligence.py` | ENG-065 Local attachment metadata/text parser. No OCR. |  |
| `VIA_ENG110_WorkopsCommitmentFulfillment` | `VIA_ENG110_WorkopsCommitmentFulfillment.py` | ENG-043 Commitment Fulfillment Engine. |  |
| `VIA_ENG111_WorkopsConfidenceCalibrator` | `VIA_ENG111_WorkopsConfidenceCalibrator.py` | ENG-047 Confidence Calibration & Accuracy Gate. |  |
| `VIA_ENG112_WorkopsDailyOperatingRhythm` | `VIA_ENG112_WorkopsDailyOperatingRhythm.py` | ENG-041 Daily Operating Rhythm. |  |
| `VIA_ENG113_WorkopsDiagnostics` | `VIA_ENG113_WorkopsDiagnostics.py` | ENG-058 Diagnostics + IT governance evidence. |  |
| `VIA_ENG114_WorkopsEvidenceIntegrityGuard` | `VIA_ENG114_WorkopsEvidenceIntegrityGuard.py` | ENG-046 Evidence Integrity & Contradiction Guard. |  |
| `VIA_ENG115_WorkopsFeedbackWeightOptimizer` | `VIA_ENG115_WorkopsFeedbackWeightOptimizer.py` | ENG-048 Feedback Weight Optimizer. |  |
| `VIA_ENG119_WorkopsMailEventBridge` | `VIA_ENG119_WorkopsMailEventBridge.py` | ENG-061 bridge normalized Outlook mail into the standalone F… |  |
| `VIA_ENG120_WorkopsMandatoryReplyBuilder` | `VIA_ENG120_WorkopsMandatoryReplyBuilder.py` | ENG-031 Mandatory Reply Builder. |  |
| `VIA_ENG121_WorkopsMeetingT2Guard` | `VIA_ENG121_WorkopsMeetingT2Guard.py` | ENG-042 Meeting T-2 Preparation Guard. |  |
| `VIA_ENG123_WorkopsMissingInformationGuard` | `VIA_ENG123_WorkopsMissingInformationGuard.py` | ENG-037 Missing Information Guard: converts vague work into … |  |
| `VIA_ENG126_WorkopsOrchestrator` | `VIA_ENG126_WorkopsOrchestrator.py` | ENG-060 central WorkOps orchestrator. |  |
| `VIA_ENG128_WorkopsProcessMiningKpiBridge` | `VIA_ENG128_WorkopsProcessMiningKpiBridge.py` | ENG-045 Process Mining KPI Bridge. |  |
| `VIA_ENG135_WorkopsSmartEscalation` | `VIA_ENG135_WorkopsSmartEscalation.py` | ENG-064 Smart escalation recommendations only. |  |
| `VIA_ENG136_WorkopsSsotStore` | `VIA_ENG136_WorkopsSsotStore.py` | ENG-052 SSOT persistence. Preferred DuckDB + Parquet; SQLite… |  |
| `VIA_ENG139_WorkopsTopicEpisode` | `VIA_ENG139_WorkopsTopicEpisode.py` | ENG-066 Thread -> new-content -> topic episode reconstructio… |  |
| `VIA_ENG142_WorkopsWatchlistPrioritizer` | `VIA_ENG142_WorkopsWatchlistPrioritizer.py` | (無說明字串) |  |
| `VIA_ENG144_RcAcceptance` | `VIA_ENG144_RcAcceptance.py` | Release Candidate acceptance tests. No network and no Outloo… |  |
| `VIA_ENG151_VplDesktop` | `VIA_ENG151_VplDesktop.py` | VeritasPulse desktop launcher — wraps the single-file app in… |  |
| `VRN_ENG001_ACTIVATEANDCROSSVALIDATE` | `VRN_ENG001_ACTIVATEANDCROSSVALIDATE.py` | ACTIVATE_AND_CROSS_VALIDATE.py |  |
| `VRN_ENG006_CompleteOCREngineRegistry` | `VRN_ENG006_CompleteOCREngineRegistry.py` | ╔═══════════════════════════════════════════════════════════… |  |
| `VRN_ENG007_FinalizeCoreV21` | `VRN_ENG007_FinalizeCoreV21.py` | VRN Finalize AIO - embedded Python core |  |
| `VRN_ENG009_M03ChineseOCRLEGOUltra` | `VRN_ENG009_M03ChineseOCRLEGOUltra_v22.py` | ╔═══════════════════════════════════════════════════════════… |  |
| `VRN_ENG010_M03LayoutOCRUltra` | `VRN_ENG010_M03LayoutOCRUltra.py` | ╔═══════════════════════════════════════════════════════════… |  |
| `VRN_ENG011_M03TIFFOCRUltra` | `VRN_ENG011_M03TIFFOCRUltra.py` | ╔═══════════════════════════════════════════════════════════… |  |
| `VRN_ENG012_M04OCRPostProcessorLEGOUltra` | `VRN_ENG012_M04OCRPostProcessorLEGOUltra.py` | ╔═══════════════════════════════════════════════════════════… |  |
| `VRN_ENG014_MDL001StockReportPipeline` | `VRN_ENG014_MDL001StockReportPipeline.py` | (無說明字串) |  |
| `VRN_ENG024_MDL239VrnNewReportFormatSystemDefaultInstallerV06155REPORTV06155` | `VRN_ENG024_MDL239VrnNewReportFormatSystemDefaultInstallerV06155REPORTV06155.py` | (無說明字串) |  |
| `VRN_ENG025_MDL259VrnReportDateWindowTableRestoreV0597REPORT` | `VRN_ENG025_MDL259VrnReportDateWindowTableRestoreV0597REPORT_v0597.py` | (無說明字串) |  |
| `VRN_ENG026_OCRPostProcessingValidationSystem` | `VRN_ENG026_OCRPostProcessingValidationSystem.py` | ╔═══════════════════════════════════════════════════════════… |  |
| `VRN_ENG046_ContentExtractCandidate` | `VRN_ENG046_ContentExtractCandidate_v0100.py` | (無說明字串) |  |
| `VRN_ENG047_ContentExtract` | `VRN_ENG047_ContentExtract_v0101.py` | (無說明字串) |  |
| `VRN_ENG048_ContentProbe` | `VRN_ENG048_ContentProbe_v0100.py` | (無說明字串) |  |
