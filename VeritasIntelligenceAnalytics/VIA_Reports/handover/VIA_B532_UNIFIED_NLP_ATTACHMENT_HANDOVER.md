# VIA B532：Unified NLP 與附件受控整合交接報告

**批次：** B532
**目的：** 將既有 NLP 能力、VRN→VDF 文字管線與本批 7 個附件納入同一個 VIA 中央控制入口，同時避免把資料抓取器、程式治理器或介面治理器誤標為 NLP 引擎。
**最新離線驗收：** 2026-09-16（Asia/Taipei）。

## 一、最終結論

本批已建立並註冊 `SUP_MDL866_VIAUnifiedNLPOrchestrator_v0100.py`。它以 `SUP_MDL744_NLPApplicationHub_v0102.py` 作為 NLP 能力正主，提供文字正規化、無損切段、表格擷取、版面分塊、內容角色與證據型摘要。對 PDF、DOCX 與影像，統一入口不另造第二套解析器，而是受控轉派既有 `VRN_ENG087_NLPTextSummaryBridge_v0100.py`，再由 ENG072、SUP_MDL744、ENG073 與 VDF 狀態閘完成中央鏈。

**NLP 控制面與核心能力為 GREEN。** `SUP_MDL866` 十項 selftest 為 10/10，`SUP_MDL744` 為 12/12，`VRN_ENG087` 為 11/11。以倉內 synthetic DOCX 做檔案級實測時，ENG072 產生 1 個 sidecar，NLP 處理 1/1，證據摘要 1/1，ENG073 return code 為 0，測試 DuckDB 為 GREEN，並保存 `vrn_nlp_text_summary` 與 `vrn_pipeline_runs`；整體管線裁決為 **YELLOW**，原因是 VDF 市場資料覆蓋閘未達 2023 起始要求。這個 YELLOW 是正確阻擋，不是 NLP 失敗，也不是假綠。

七個附件中，AKShare 是 VDF 外部資料 adapter，VES 是唯讀引擎治理與 AI 協作車道，VCAF 是治理自動修正候選，CGE 是介面合約適配候選。它們已納入中央 intake manifest，但不是七個 NLP 實作。所有 adapter 均標示 `INTAKE_ONLY` 或 `COLLECTED_NOT_RUN`；沒有啟動外部網路、排程、套件安裝、來源覆寫或自動修碼。

## 二、中央控制面與註冊

| 控制站 | 實際結果 | 證據 |
|---|---:|---|
| Unified NLP orchestrator | `SUP_MDL866`，selftest 10/10 | `VIA_Reports/nlp_unified/VIA_UNIFIED_NLP_latest.json` |
| NLP provider | `SUP_MDL744`，selftest 12/12；6/6 研報服務在位 | `evidence_b532_unified_nlp/sup_mdl744_nlp_selftest.txt` |
| VRN file bridge | `VRN_ENG087`，selftest 11/11 | `evidence_b532_unified_nlp/vrn_eng087_nlp_selftest.txt` |
| InputConsole | `central/acceptance/via_unified_nlp` 已登錄，支援 `text` 與 `pipeline` | `supportive modules/registry/VIA_InputConsole_Spec_v0100.json` |
| Workflow SSOT | `via_unified_nlp_pipeline` 已登錄 | `supportive modules/registry/VIA_Workflow_SSOT_v0100.json` |
| ToolRoster | provider、bridge、manifest、offline policy 已登錄 | `supportive modules/registry/VIA_ToolRoster_SSOT_v0100.json` |
| Engine Catalog | `SUP_MDL866_VIAUnifiedNLPOrchestrator` 已登錄 | `supportive modules/registry/VIA_Engine_Catalog_v0100.json` |
| Component Inventory | VCGC active 5,014，新增 pipeline/tool records | `evidence_b532_unified_nlp/cgc149_registry_postpipeline_apply.txt` |
| Interface registry | `VIA-IFACE-4014` 已登錄，`drift_count=0` | `supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json` |
| Naming registry | `SUP_MDL866` 已登錄，SUP counter 865→866 | `supportive modules/registry/VIA_Naming_Registry_v0100.json` |
| Accelerator control | CGC156 `GREEN · 23/23 · accelerators=25` | `evidence_b532_unified_nlp/cgc156_dataflow_control.txt` |

VCGC post-pipeline registry-sync 的套用結果為 `active=5,014`、`new=2`、`changed=14`、`retired=0`、`AST errors=0`；加入 QuantGuard data-flow guard 後再套用 16 項變更，最後唯讀 idempotent plan 收斂為 `active=5,014`、`new=0`、`changed=0`、`retired=0`、`AST errors=0`。新增項目來自 unified pipeline 擴充與本批 Windows handover tool，並已再完成 Python compile。CGC_MDL054 binding sync 顯示 `50 OK / 6 DRIFT / 1 BUMP`；6 個 DRIFT 是既有歷史 InputConsole contract drift，未在本批盲改。`via_unified_nlp` 的 `BUMP` 是新加入中央冊的版本前進，並非執行失敗。

## 三、附件角色矩陣

| 附件 | 中央角色 | NLP 判定 | 執行狀態 | 實測結果 |
|---|---|---|---|---|
| `Invoke-VIA-AKShareSuperEngine.ps1` | VDF AKShare launcher | 非 NLP data adapter | `COLLECTED_NOT_RUN` | 與既有 VAKE b367 intake SHA256 相同；未觸網 |
| `VDF_AkshareFetcher.py` | VDF fetcher | 非 NLP data adapter | `COLLECTED_NOT_RUN` | Python compile PASS；`scan --offline` 因環境缺 `akshare` 阻擋；未安裝 |
| `Invoke-VIA-EngineStandardizer.ps1` | VES launcher | NLP 支援治理 | `INTAKE_ONLY` | PowerShell runtime 待 Windows；未執行寫回 |
| `via_engine_standardizer.py` | 引擎清冊、風險、AI handoff | NLP 支援治理 | `INTAKE_ONLY` | selftest 103/103 PASS |
| `VES_AI_COLLAB.md` | 多 AI 協作協定 | NLP handover protocol | `INTAKE_ONLY` | 已收容並以 SHA256 登錄 |
| `VIA_CGC_ABC_AutoFixEngine_v0100.py` | CGC governance auto-fix candidate | 非 NLP auto-fix | `INTAKE_ONLY` | Python compile PASS；`--all` temporary fixture dry-run rc=0，原始樹未動 |
| `via_cge_adaptive.py` | adaptive interface registry candidate | 非 NLP interface governance | `INTAKE_ONLY` | selftest 25/25 PASS；只用暫存 fixture |

完整檔案、來源雜湊、路由與網路政策位於 `supportive modules/registry/VIA_UnifiedNLP_Attachment_Manifest_v0100.json`。該 manifest 明定 **SUP_MDL744 才是 NLP capability provider**；附件不可自動變成 NLP 執行路徑。

## 四、實測矩陣

| 測試 | 結果 | 說明 |
|---|---:|---|
| SUP_MDL866 selftest | PASS 10/10，rc=0 | manifest、Hub、6 服務、文字、表格、版面、摘要、fail-closed、offline、ENG087 bridge |
| SUP_MDL744 selftest | PASS 12/12，rc=0 | 尾版 v1.8.0、39 可載入模組、表格、版面、角色、證據摘要 |
| VRN_ENG087 selftest | PASS 11/11，rc=0 | Hub、摘要 span、DuckDB、ENG072/073、VDF bridge、offline、SuperAccel |
| Unified text probe | PASS，rc=0 | normalized text、1 table、3 layout blocks、3 evidence points |
| Unified DOCX fixture pipeline | **YELLOW**，downstream rc=2 | NLP 1/1、ENG073 rc=0、DuckDB GREEN；VDF coverage gate false，保留 YELLOW |
| CGC156 | GREEN 23/23，rc=0 | 25 roster、QuantGuard policy、VDF/DuckDB→QuantGuard 單向資料流、accelerator control |
| VDF_ENG086 QuantGuard bridge | GREEN 8/8，rc=0 | `VDF_DUCKDB_TO_QUANTGUARD`；source read-only，before/after frame hash 相等 |
| VES attachment | PASS 103/103 | 只讀暫存 selftest；未用 `--apply` |
| CGE attachment | PASS 25/25 | 只讀暫存 selftest；未寫母樹 |
| VCAF attachment | PASS compile；dry-run rc=0 | temporary fixture；健康度 75/100，非 active auto-fix |
| AKShare attachment | Python compile PASS；offline scan BLOCKED | 缺 `akshare`；遵守不安裝、不補庫、不觸網 |
| VRN_ENG078 legacy bridge | **FAIL 4/6** | 舊 selftest 硬編 v1.5.0；目前中央尾版是 v1.8.0；未列為 Unified NLP active route |
| PowerShell runtime | PENDING | 本 sandbox 沒有 `pwsh`、`powershell` 或 PSScriptAnalyzer；Windows 需 pull 後重跑 |

## 五、政策與限制

所有 Python 實測均可經 `supportive modules/bootstrap/sitecustomize.py` 單點載入。最新 VDF bootstrap status 顯示 `VIA_ACCELERATOR_ROSTER=VIA_PS_Accelerators_25_Roster_v0100:25`、`VIA_ACCELERATOR_CONTROL=CGC_MDL156_VIAAcceleratorControl_v0100`、`sitecustomize=True`、`VIA_FAMILY=vdf`、`network_consent=OFF`。本批沒有重啟資料補庫，也沒有使用 AKShare 網路抓取。

QuantGuard-only 政策仍有效。資料流方向固定為 **VDF／VDF-owned DuckDB or Parquet read surface → QuantGuard → features/factors/SSOT/evidence outputs**。QuantGuard 不回頭抓 VDF，不反向改寫 VDF source，不修改來源資料庫 schema，不自行觸網，也不自行取得 operator consent；`VDF_ENG086` 會 clone source frame 並保存 before/after hash。活動 `SUP_MDL116_DataTransformEngine.py` 已移除可選 legacy import 與後端分支，改走 QuantGuard-owned deterministic formula surface。活動樹的 `import talib`、`from talib` 與 `import ta_lib` 精準掃描為零。TA-Lib/talib 未被安裝、import、啟動或恢復為活動路徑；本報告只保留歷史檔案名稱或治理文字的差異，不把它們宣稱為活動接線。Windows `C:\測試樣本報告` 的 60 份 PDF 與 4 份 DOCX 原始檔仍未掛載到 sandbox，因此本批沒有對該批真檔做內容級解析宣稱。DOCX pipeline 測試使用倉內 fixture，不能替代 Windows 真檔驗收。

## 六、Windows 一貼式命令

Pull 最新分支後，在 PowerShell 7 於 VIA 根目錄執行：

```powershell
. .\Register-VIA-Commands-v0208.ps1
NLP統一 -SelfTest
NLP統一 -Status
NLP統一 -Pipeline -In 'C:\測試樣本報告' -Points 5
```

`-Pipeline` 會經 VIA 中央 `SUP_MDL866` 轉派 `VRN_ENG087`。若 VDF 覆蓋閘仍未達 2023-01-01，應看到 YELLOW 或 BLOCKED，而不是假 GREEN。Windows 首次 runtime probe 曾發現舊版 PowerShell scope 使 25 項回退為 20 項；該 scope fix 已推送，但本批仍需使用者在 Windows pull 最新版本後重跑。

## 七、交接重點

下一位 AI 先讀本報告的「一、最終結論」與 `VIA_B532_UNIFIED_NLP_ATTACHMENT_STATUS.json`，再讀 `VIA_UnifiedNLP_Attachment_Manifest_v0100.json`。若只需驗 NLP 核心，執行 `SUP_MDL866 ... selftest`；若要驗檔案鏈，使用 `pipeline` 並查看輸出的 `NLP_VRN_VDF_RESULT.json`。若裁決為 YELLOW，先讀 `vdf_gate.blockers`，不可把資料覆蓋不足誤判為 NLP 或 DuckDB 失敗。

## References

[1]: ../../supportive%20modules/70_VRN_Rules/SUP_MDL866_VIAUnifiedNLPOrchestrator_v0100.py "SUP_MDL866 Unified NLP orchestrator"
[2]: ../../supportive%20modules/registry/VIA_UnifiedNLP_Attachment_Manifest_v0100.json "B532 attachment control manifest"
[3]: ../../functional%20modules/VRN/VRN_ENG087_NLPTextSummaryBridge_v0100.py "VRN NLP to VDF bridge"
[4]: ../../supportive%20modules/70_VRN_Rules/SUP_MDL744_NLPApplicationHub_v0102.py "NLP application hub"
[5]: ../nlp_unified/VIA_UNIFIED_NLP_latest.json "Machine-readable unified NLP evidence"
