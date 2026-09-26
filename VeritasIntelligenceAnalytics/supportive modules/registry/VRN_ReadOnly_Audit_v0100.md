# VRN 唯讀稽核報告

**主要結論：目前 ENG110 報表路徑缺少摘要與財務產物的接線，也未傳入公司名稱所需的官方資料。** 此外，已用實際 PDF 重現「裕民 2606 被辨識為年份 2025」及總頁數一律傳入 1。這些問題需要修正資料接線與欄位判讀；讀取器套件缺少則是另一項缺口。

本報告區分「使用者提供的 Windows 97 份執行結果」、「GitHub 靜態證據」與「本次 4 份 PDF 的隔離元件重播」。未修改或部署修復。

## 一、 稽核執行聲明與工具狀態 (Audit Telemetry & Declaration)

- **儲存庫與版本**：[tonykuni/movies-dataset](https://github.com/tonykuni/movies-dataset)，固定 commit `be5f7b2477214284ee60169edcc89f52cc2cd5c5`。本次結論不外推至後續提交。
- **實際入口**：`VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py`，由其原生載入器追蹤 v0143／v0142、省 Token 工具與 VRN 管理介面。
- **入口驗證範圍**：原版工具及元件重播皆先載入上述 VCGC；元件路由為 VCGC → VRN_SystemManager_v0105 → ENG110_v0107 → v0103 相依元件。GitHub 連接器依入口解析出的相依關係取得唯讀副本。沒有在使用者 Windows 執行 `via-entry`，因此**不能宣稱已驗證實機或服務端 100% 強制單一入口**。
- **唯讀聲明**：本次對遠端儲存庫、正式 VCGC／VRN／VDF、OneDrive 原始測試文件及正式資料庫的寫入／修改操作為 **0**。本地建立了稽核副本、診斷輸出及本報告；這些不等於正式系統寫入。元件重播以 Python audit hook 禁止檔案寫入、子程序及網路連線。
- **原始碼完整性**：16 份本次使用的 GitHub 原始碼副本，其 Git blob SHA 全部與固定 commit 相符。沒有修改原版工具程式或設定；這項比對不等於全系統歷史防竄改鑑證。
- **測試文件覆蓋**：提供的 OneDrive 資料夾列出 106 個檔案：97 PDF、7 DOCX、1 TXT、1 JPG。本次從中重播 4 PDF；未重跑 Windows 的完整 97 份批次。

**實際調用的 Token Saving Tools**

| 原版工具／功能 | 本次作用 | 實際結果與限制 |
| :--- | :--- | :--- |
| CGC_MDL158_VIAPanoramaAuditRepair_v0113：`pack` | 取得稽核副本的尾版索引 | 避免整庫全文灌入上下文；副本索引不代表完整儲存庫 |
| 同工具：`read` | 取得模組骨架與函式位置 | VRN 管理器單次骨架估算省 93.8%；屬工具近似值 |
| 同工具：`slice` | 僅讀取根因相關函式 | 定位 `_one`、`build_basic_info`、`extract_ticker` 與 GateMap |
| 同工具：`digest` | 壓縮元件重播日誌 | 回傳 NODATA／rc=2：自訂 JSON 日誌缺少工具要求的 `[計]` 總表；沒有偽裝成功 |
| 同工具：`--if-etag` | 避免重讀未變索引 | `71a91bd2b0cba9d8` 重讀回傳 `304_NOT_MODIFIED` |
| SUP_MDL866_VIAUnifiedNLPOrchestrator_v0103：`text --brief` | 限縮 NLP 回傳內容 | 呼叫 PASS，但 `nltk=ABSENT`、`points=[]`；不代表摘要已生成 |

新引擎 `VIA_NLP_OneEngine_v1_9_0.py` 已用於 4 份真實首頁文字的純函式正規化測試。4/4 通過該引擎自己的 `def_facts` 指紋一致性檢查；3 份文字有正規化變動、1 份未變。這僅驗證這項檢查，**不等於已驗證語義完全正確、OCR、摘要、財務擷取或完整模型流程**。未把引擎註冊或部署進正式 VRN。

**證據索引**

下表檔名相對於 `VeritasIntelligenceAnalytics/functional modules/VRN/`；點擊可查看固定版本原始碼。

| 證據 | 原始碼 | 關鍵位置 |
| :--- | :--- | :--- |
| S1 | [VRN_ENG110_TabReport_v0107.py](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/functional%20modules/VRN/VRN_ENG110_TabReport_v0107.py) | `_prior` L18–22；`read_page1` L98–130；`run` L133–144 |
| S2 | [VRN_ENG110_TabReport_v0103.py](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/functional%20modules/VRN/VRN_ENG110_TabReport_v0103.py) | `_one` L89–121；`run` L163–207 |
| S3 | [VRN_ENG109_GateMap_v0100.py](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/functional%20modules/VRN/VRN_ENG109_GateMap_v0100.py) | `_basic_ready` L32–42；`_page_ready` L51–60；`map_report` L83–112 |
| S4 | [intake／VIA_VRNLogic_AllInOne_v0201.py](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/functional%20modules/VRN/references/intake/VIA_VRNLogic_AllInOne_v0201_b504/VIA_VRNLogic_AllInOne_v0201.py) | `extract_ticker` L327–338；`reconcile_evidence` L724–752；`build_basic_info` L762–809 |
| S5 | [VIA_VRN_FirstPageEngine_v0129.py](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/functional%20modules/VRN/VIA_VRN_FirstPageEngine_v0129.py) | `filename_facts` L2796–2815 |
| S6 | [VCGC v0144](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/supportive%20modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py) | `systems` L31–50，尤其寫檔 L44–46 |
| S7 | [VRN_SystemManager_v0105.py](https://github.com/tonykuni/movies-dataset/blob/be5f7b2477214284ee60169edcc89f52cc2cd5c5/VeritasIntelligenceAnalytics/functional%20modules/VRN/VRN_SystemManager_v0105.py) | `main` L29–33 |

## 二、 系統架構與路由檢視 (Architecture & Data Flow Review)

1. **VCGC 入口與路由層**：本次以 v0144 作載入入口，使用其 Token roster、原版 panorama 載入器及 VRN 子系統介面。一般 VRN 子系統選取 v0105，再委派 v0104；但 v0144 的 `systems()` 另固定載入 v0104 並寫快照，不能把該命令視為純讀取。為遵守唯讀，本次未執行 `systems()`。

2. **VRN 報表路徑**：ENG110_v0107 主要更新首頁讀取器，`run()` 仍委派固定 v0103。後者用舊 intake `build_basic_info()` 產生基本資料，再把資料送至 ENG109 GateMap。較新的 FirstPageEngine 只被呼叫 `filename_facts()`，結果只用於代號差異統計，沒有替代或修正基本資料，也沒有呼叫其完整處理流程。

3. **VDF 相依範圍**：VCGC 有 VDF 子系統介面，VRN 的 FirstPageEngine 也存在官方名冊／名稱對帳依賴。但本次沒有讀取 VDF 正式資料庫或驗證其完整管線；**不能將 VRN 缺少 `official` 參數判定為 VDF 資料庫故障**。

4. **跨系統與瓶頸**：目前最明確的阻塞在 ENG110 組裝產物的位置：摘要固定空、財務固定空陣列、公司名稱來源未接入。GateMap 擋下未完成資料，避免進入 VERIFIED；這項保護應保留。尚無執行效能量測可支持「VDF 效能瓶頸」或整體 SPOF 已成立的結論。

**使用者提供的 97 份結果如何對應程式**

| 實機回報 | 稽核解釋 |
| :--- | :--- |
| `text=87`；`page_empty=87` | 87 份有文字，但 S2 L110 的摘要固定為空；S3 要求首頁文字與摘要都存在 |
| `financial_empty=97` | S2 L111 無條件把 `[]` 傳給 GateMap；並未送入財務擷取結果 |
| `basic_status=89`；`basic_blank:companyName=8` | 狀態不合格者先被擋下；其餘 8 份接著遇到公司名稱空值。S4 僅由 `official.companyName` 取名稱，而 S2 未提供 `official` |
| `page_not_1=10` | S2 在無文字時把 `page` 設為空字串；此計數不證明曾錯拿第 2 頁當第 1 頁 |
| `ticker_mismatch=7` | 兩條代號路徑不同；本次確認一個真實錯誤機制，未取得原批次七筆逐檔清單 |
| `written=0`；`verified=0` | S2 L201–202 是固定常數；同一函式 L177 仍寫 HTML，不能將這個 0 當「零檔案寫入」的證明 |

上述原因計數會重疊，不應加總成失敗文件數。87 份「讀得到文字」也不代表 87 份已完成報告處理。

**四份實際 PDF：唯讀元件重播**

| 文件 | 首頁文字字元 | 實際總頁數／傳入值 | 重播基本資料結果 | GateMap |
| :--- | ---: | :---: | :--- | :--- |
| 華南投顧-2606-裕民-1141202.pdf | 2744 | 8／1 | 代號錯成 2025；FAIL_CLOSED | basic_status、page_empty、financial_empty |
| 晶心科(6533,N,中立)-CTBC251208.pdf | 3922 | 15／1 | 日期來源衝突；REVIEW_REQUIRED | basic_status、page_empty、financial_empty |
| Citi-3231 20250604.pdf | 4170 | 13／1 | PHASE2_OK，但公司名稱為「—」 | basic_blank:companyName、page_empty、financial_empty |
| 凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf | 4147 | 10／1 | PHASE2_OK，但公司名稱為「—」 | basic_blank:companyName、page_empty、financial_empty |

四份均由原版 v0107 回報 `ENG072_FITZ_LAYOUT`，無 reader error。此標籤由 v0107 的直接 fitz 呼叫回傳，不能據此證明曾調用獨立 ENG072 引擎。

已目視核對兩份首頁：

- **裕民**：標題明確為「裕民(2606)」，首頁含年度財務表，例如 2025(F) 稅後 EPS 4.19、2026(F) 5.07。此處僅作擷取管線的存在性證據，未將數值寫入正式表。舊 parser 卻以首頁年份 2025 當代號；來源衝突有被 GateMap 擋住。
- **晶心科**：首頁日期確實是 2025/12/06，檔名為 CTBC251208。這是來源內容不一致，保留 REVIEW 是合理行為，不應強制改成 GREEN。

## 三、 風險評估矩陣 (Risk Assessment Matrix)

風險等級針對已查到的 VRN 報表功能與資料正確性；未確認 Critical 安全漏洞。

| 風險編號 | 所屬模組 | 風險等級 | 風險項目與觸發條件 | 潛在衝擊 | 具體修復建議（僅供開發團隊參考） |
| :--- | :--- | :---: | :--- | :--- | :--- |
| RISK-01 | VRN | High | S2 `_one` L110–111：所有文件的摘要與財務輸入固定空 | 報表流程無法達成可驗證產物；即使 OCR 成功仍會失敗 | 在受治理的 adapter 接入首頁修復、獨立摘要與既有財務擷取結果；保留頁碼、單位、期間及來源證據，再交 GateMap |
| RISK-02 | VRN | High | S2 L95–107、S4 L782–793：未傳官方公司資料；新檔名事實僅用來計數 | 公司名稱必空；狀態合格的文件仍不能通過 | 使用既有官方／中央名冊契約提供 `official`；統一檔名、頁面與官方證據。資料不可得時列明缺件，不造名稱 |
| RISK-03 | VRN | High | S4 `extract_ticker` L327–338：未排除年份；裕民真樣本重現 2606→2025 | 報表代號錯誤、增加隔離案件；若下游忽略狀態可能錯配公司。本次未證實錯值入庫 | 由現行名冊與欄位位置識別代號；將日期候選與代號候選分開；保留衝突證據及人工審核 |
| RISK-04 | VRN | Medium | S2 L100：`pages=1` 固定傳入 | 多頁文件總頁數錯誤，可能誤導後續資料覆蓋判斷 | 分開「讀取來源頁=1」與「PDF 總頁數」；使用真實 page_count |
| RISK-05 | VRN | Medium | S1 L98–130；實機 RapidOCR 缺席且 10 份無文字 | 視覺讀取分支不可用，部分文件停在 NEEDS_VISUAL | 逐檔記錄 probe 結果與 fallback 嘗試；依既有部署流程補齊所需讀取器。尚未證明十份全是掃描檔 |
| RISK-06 | VRN | Medium | S2 L174–177、201–206；S1 L143：寫入／驗證／OCR 遙測固定值 | 容易把「有 HTML」當處理完成，或把固定 0 當零副作用證明；無法定位七筆差異 | 分開記錄 artifact_writes、db_writes、verified_count；用實際事件記錄 reader/OCR；輸出逐檔原因與下一步 |
| RISK-07 | VCGC | Medium | S6 `systems` L44–46 無條件寫 SYSTEMS_latest.json | 稽核人若把狀態命令當唯讀使用，會改變報告狀態 | 維護者分離純 collect 與 publish；唯讀入口拒絕持久化。本次未執行這條寫入路徑 |
| RISK-08 | VRN | Info | S2 L173 僅非遞迴 `*.pdf` | 測試夾另 9 份非 PDF 不在本命令覆蓋範圍；若預期全夾處理就會漏件 | 明示 PDF-only 契約；需要其他格式時由既有 ingestion 路由接入，並回報 excluded／unsupported |

## 四、 合規性與安全性檢查清單 (Compliance & Security Checklist)

- [ ] **1. 單一入口隔離性：[WARN] 警告**
  - 本次工具與元件載入經 VCGC；S7 的直接 CLI 啟動檢查 `VIA_FROM_VCGC=YES`。環境變數與操作路由本身不足以證明部署層權限隔離；未做外部繞過測試，不能標示 100% 隔離通過。
- [ ] **2. 資料與狀態完整性：[FAIL] 未通過**
  - 已重現代號、總頁數及必填產物缺失。正向證據：GateMap 對四份未完整資料均回 `ready=false`，裕民代號衝突與晶心科日期衝突被保留為非合格狀態。本次未進行正式資料寫入。
- [ ] **3. Token Saving Tools 整合與完整性：[WARN] 警告**
  - roster 列出的 read／slice／digest／pack／etag／NLP brief 已實際調用，16 份來源 blob 比對相符。digest 的輸入格式不相容、NLP brief 未產生 points，且未測全部高消耗路徑，不能把「工具在位」直接等同「全流程整合完整」。
- [ ] **4. 例外處理與錯誤隔離：[WARN] 警告**
  - S2 `_one` 捕捉基本資料／檔名事實例外後只留下空 dict；`_validation` 沒有帶入輸出，彙總只呈現第一個 reader error，會丟失診斷線索。未做崩潰傳播或敏感堆疊洩漏測試。
- [ ] **5. 機敏資訊與權限邊界：[WARN] 警告**
  - 本次未執行全庫憑證掃描、部署權限測試或 VDF 資料庫授權驗證，證據不足以宣稱「無硬編碼憑證或過度授權」。未要求、揭露或修改任何實機憑證。

## 五、 稽核總結與優先改善行動 (Executive Summary & Action Plan)

**整體系統健康度評級：需改善。** 此評級限已檢視的 VRN 報表路徑；不是 VDF 或整個儲存庫的完整健康評分。已查到數個 High 等級的功能／資料品質阻塞，GateMap 的拒絕不完整資料機制仍有保護作用。

**Top 3 優先改善建議**

1. **先完成既有處理鏈的接線。** 由 VCGC 授權 adapter 取得官方公司資料、真正的首頁修復與摘要、帶來源的財務列，再送 GateMap。新 NLP v1.9.0 的正規化已做小樣本測試，可列為接入候選；完整摘要／財務能力仍須分別驗收。保持 intake macro_ssot 與 Token Saving Tools 原件不動。
2. **修正並驗收欄位證據與衝突處理。** 裕民必須保留代號 2606 的正確候選；年份不能當代號。四份總頁數應為 8／15／13／10，同時首頁來源維持第 1 頁。晶心科 12/06 與 12/08 的衝突應持續列入 REVIEW，不以強制 GREEN 掩蓋。
3. **補齊逐檔遙測，再跑完整批次。** 每份記錄選用 reader、OCR 嘗試、欄位來源、阻擋原因、實際寫入與驗證數。先確認四份樣本的空摘要／空財務接線已解除，再檢查完整 97 PDF 的七筆代號差異與十份讀取失敗；另外九份非 PDF 明確列為已路由或不支援。

驗收結果應區分 VERIFIED、REVIEW、NEEDS_VISUAL、UNSUPPORTED 等原因，不能用「97 份全部變綠」取代資料正確性。禁止編造財務值、把後頁當首頁、原文直接充作摘要，或只更改 `validationStatus` 繞過閘門。

本次完成根因定位、原版工具執行與四份真實樣本的唯讀驗證；**尚未部署修復，完整 Windows 批次也尚未重跑**。伴隨的 `VRN_Audit_Evidence.json` 保存使用者回報、重播輸出、來源雜湊及範圍限制，供維護者核對。
