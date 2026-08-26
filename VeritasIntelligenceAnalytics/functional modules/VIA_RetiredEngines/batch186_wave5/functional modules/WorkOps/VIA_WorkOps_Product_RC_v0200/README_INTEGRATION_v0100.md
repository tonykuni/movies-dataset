# VIA WorkOps Product RC v0200 — 整編清單 README(v0100)

> 整編令(2026-08-18):integrate consolidate optimize with existing engines and
> modules;除非獨立新功能不另立樹;編號命名;優化強化測試無誤;列清單 README。
> 本檔即該令之「清單 README」交付。

## 一、裁決摘要(批十)

| 上傳件 | 裁決 |
|---|---|
| VeritasWorkOps_v0200_RC.zip | **收容為 WorkOps 正典產品樹**(本目錄;183 檔 manifest 自證) |
| VIA_WorkOps_SmartWorkflow_v0106_2.zip | **併入本樹不另立**——RC 全涵蓋(byte-exact 111 檔;RC 無此包獨有檔);12 件舊版變體收 `docs/history/v0106_variants/`(只增不減);`__pycache__` 殘檔 29 件不收 |
| VIA_WorkOps_M365_Roadmap.pdf | **讓位**(與 `WorkOps/docs/VIA_WorkOps_M365_Roadmap_v13.pdf` byte-exact) |
| VIA_Note_Pro_Standalone.html | **讓位**(與 `VAP/spec/UIUX_Design_Source/` 正典 byte-exact) |

## 二、紅線安檢(誠實聲明)

- 全包 `.Send(` 掃描:**零命中**。
- 郵件鄰域引擎 `workops_outlook_graph_connector` / `workops_mail_event_bridge`:
  再掃 sendMail / send_mail / POST messages / createReply / /send:**零命中**——
  讀取與事件橋接道,無發信能力。
- QA 組態一律 `auto_send_mail: false`。
- BatchMailer 檢疫紅線不受本包影響;`quarantine/*.SEND_QUARANTINED` 原狀不動。

## 三、引擎清單與自動編號(命名冊 TOOL-047 正典對映;實體檔零改名)

39 支引擎,正典號 VIA_ENG104–142(先發先得 append-only):

| 正典號 | 引擎 | FNC/CLS |
|---|---|---|
| VIA_ENG104 | workops_accuracy_benchmark | 4/0 |
| VIA_ENG105 | workops_api_server | 12/10 |
| VIA_ENG106 | workops_attachment_intelligence | 6/0 |
| VIA_ENG107 | workops_autocode | 1/1 |
| VIA_ENG108 | workops_backup_restore | 7/0 |
| VIA_ENG109 | workops_closure_intelligence | 9/0 |
| VIA_ENG110 | workops_commitment_fulfillment | 12/0 |
| VIA_ENG111 | workops_confidence_calibrator | 7/0 |
| VIA_ENG112 | workops_daily_operating_rhythm | 11/0 |
| VIA_ENG113 | workops_diagnostics | 4/0 |
| VIA_ENG114 | workops_evidence_integrity_guard | 6/0 |
| VIA_ENG115 | workops_feedback_weight_optimizer | 5/0 |
| VIA_ENG116 | workops_followup_pack_builder | 9/0 |
| VIA_ENG117 | workops_followup_state | 12/1 |
| VIA_ENG118 | workops_lesson_learned | 7/0 |
| VIA_ENG119 | workops_mail_event_bridge | 9/0 |
| VIA_ENG120 | workops_mandatory_reply_builder | 6/0 |
| VIA_ENG121 | workops_meeting_t2_guard | 7/0 |
| VIA_ENG122 | workops_milestone_manager | 7/0 |
| VIA_ENG123 | workops_missing_information_guard | 4/0 |
| VIA_ENG124 | workops_module_lifecycle_manager | 7/0 |
| VIA_ENG125 | workops_onboarding | 5/0 |
| VIA_ENG126 | workops_orchestrator | 3/0 |
| VIA_ENG127 | workops_outlook_graph_connector | 11/0 |
| VIA_ENG128 | workops_process_mining_kpi_bridge | 5/0 |
| VIA_ENG129 | workops_progress_estimator | 5/0 |
| VIA_ENG130 | workops_project_card_aggregator | 6/0 |
| VIA_ENG131 | workops_project_fusion | 12/0 |
| VIA_ENG132 | workops_project_health | 5/0 |
| VIA_ENG133 | workops_project_registration | 8/0 |
| VIA_ENG134 | workops_retention_manager | 5/0 |
| VIA_ENG135 | workops_smart_escalation | 3/0 |
| VIA_ENG136 | workops_ssot_store | 10/0 |
| VIA_ENG137 | workops_stakeholder_matrix | 10/0 |
| VIA_ENG138 | workops_timeline_dependency | 4/0 |
| VIA_ENG139 | workops_topic_episode | 8/0 |
| VIA_ENG140 | workops_unified_search | 5/0 |
| VIA_ENG141 | workops_unified_work_register | 7/0 |
| VIA_ENG142 | workops_watchlist_prioritizer | 5/0 |

包內自帶 ENG-031~050 manifests 屬 WorkOps 子系統自有名空間,與 VIA 正典號並存
(台帳 coexisting_namespaces 列管),兩不相改。

## 四、測試證據(整編後實跑)

- 本包 pytest:**10/10 PASS**(v0102/v0103/v0106_accuracy/engines)
- 兩包 py 編譯:**71/71 過**(整編前);整編後 RC 樹編譯零壞
- 介面合約 TOOL-041:新編 51,漂移 0
- 命名冊 TOOL-047:新家族 50(VIA_ENG×147)
- 全域快棋盤 grid v0108:OK 26 · FAIL 0(SKIP 6 = 容器缺 Windows 路徑誠實)

## 五、候辦(工作站)

操作員列示之 12 件 Downloads 檔(Subsystem_Integration_Audit_v003 py+md、
VIA_Story_Final_v2、MarketRisk_ScoringSpec、DataFetch_Registry、
Valuation_Earnings_FetchSpec、DataValue_Table、ISM_PMI_12M_v002、
Labor_Detail_Matrix、SurveyResponseRates、RetailSales_YoY、
PublicBroker_BranchTracking_D5)容器不可及——請於工作站
`via-run via-intake` 收編或逐件上傳,屆時依本流程整編配號。
