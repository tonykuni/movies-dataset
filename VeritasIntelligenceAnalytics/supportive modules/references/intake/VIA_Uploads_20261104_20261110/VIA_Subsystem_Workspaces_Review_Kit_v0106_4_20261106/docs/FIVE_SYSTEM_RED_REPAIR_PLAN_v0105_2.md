# VIA 五系統 RED 阻礙與安全修復計畫 v0105.2

## 判讀原則與證據範圍

本報告從已交付 `VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip` 中 `public/governance.html` 的實際合併模型讀取。ZIP SHA-256為 `bf5ac1a16667e2a2f9c8928a2102d6ca191dea07caab5e888f3eb16a596d6be2`；此次不改它的任何內容、時間戳或燈號。治理頁共9矩陣、36,837列，其中RED 12列：5個系統閘、5個治理衝突、2個環境閘。這些不是12個已證實的runtime crash。

五個系統列的 `scope=OBSERVED_GATE_NOT_ENGINE_FAILURE`。它們是「沒有足以批准正式整合的證據」或「責任／身份仍有矛盾」，而不是宣稱既有VCGC、VDF、VRN、VQG、VAP均不能獨立工作。候選JSON中的 `ssot_name` 與AST定位ID也不等於owner簽核的正式SSOT號冊。

這個包是審查add-on：本輪工作台／MCP／Token／參考fixture／隔離VAP檢查均有各自收據。它不是五production engines的完整distribution。現有native引擎、installation engine、資料庫和跨系統契約不得被UI模擬、候選AST編號、歷史QA或單一PASS替換。

## 五系統 RED 來源與解除條件

| 燈號 | 編號 | SSOT候選名稱 | 實際阻礙原文 | 安全修復／下一步 | 證据與解除正式閘的條件 |
|---|---|---|---|---|---|
| RED | OBS-0001 | VCGC | No VCGC connector/server or owner registry receipt; TokenEngine add-on tested locally only | 取得owner核實的VCGC根目錄、既有EnvManager／InstallGate版本及原正式registry schema／ACL；唯讀盤點既有工具與候選工具；用已有installer產生dry-run plan而非apply。先讓stdio候選做status/query，不當成VCGC live MCP。 | 有實際VCGC來源SHA／版本、registry schema／owner權限、既有工具不變證據、source-pinned integration與output receipt，並通過owner正式核准。禁止取代既有Token或installer。 |
| RED | OBS-0002 | VDF | Native VDF engine/current intake path and real data output receipt not available in this upload set; VRN wrapper is not native VDF | 定位native intake engine和DataHome SSOT；核實資料來源授权、市場／標的、日期、時區、row keys、調整和單位；先在隔離資料區核輸入輸出。要求2022-01-02以後可得資料時，不把休市／未上市／source gap當需補造的交易。 | 輸入來源及as-of、request範圍、output schema、unique keys、來源fingerprint、缺漏／重複／型別檢查與真實row count/hash；資料庫目標及owner許可。未知來源不得自動建production DB。 |
| RED | OBS-0003 | VRN | Uploaded wrapper and historical receipts are not current Tony-NB/native module execution | 核實native modules與唯一root；在隔離候選上用已授權真實報告sample跑擷取／整理／分類／去重，不跑舊RoundAll部署流程。每份sample保存來源SHA與document lineage；exact duplicate和近似duplicate分開記錄。 | 核准樣本與根路徑、native源檔SHA、輸入／輸出筆數與id對照、擷取人工抽查、分類規則、去重保留/移除理由、負向案例及來源不變證據。歷史成功仍保留，但不能替代本輪實機收據。 |
| RED | OBS-0004 | VQG | QuantGuard and QuantGenerator naming conflict; native Dataset API and source identities not verified | Owner先核定QuantGuard／QuantGenerator各自身份、repo/module owners及canonical IDs，不靜默當同義字。定版Dataset API／schema／timestamp／source fingerprint／錯誤語義，依VDF／Database→VQG→VAP的版本化artifact交換。 | 來源與owner、canonical名稱決議、contract version、schema相容／差異報告、consumer fixture和producer真資料输出receipt。不得因名稱相似自动registry合併或發正式號。 |
| RED | OBS-0005 | VAP | v027 runtime is readable and AST indexed; native runtime not executed this round. Compute role versus new pure-render requirements unresolved | Owner核定pure-render規格與既有cleaning／TA-Lib／AI helper的責任分工，先保留v027不变。另建versioned renderer/input contract，讓VQG提供已計算Dataset；逐圖表核呈現parity與upstream fingerprint。既有helper是否留、隔離或deprecated需要變更決議，不擅自刪除。 | 定版角色規格、source/hash、Dataset來源与contract、19項隔離candidate測試之外的實際native runtime／consumer integration／輸出parity收據、no-compute或批准例外證據。 |

五系統列來源共同指向 `data/governance_runtime_observations_v0105.json`。正式RED狀態只能由新版本、可追溯owner gate與實測證據改變；不是把原檔的 `status` 字串改成GREEN。

### VAP收據的必要限定

原系統列使用「native runtime not executed this round」，但同一包另含**隔離新scratch VAP 19/19 candidate測試**。因此不能把這句話概括成「VAP完全沒有測過」。正確範圍是：候選副本的有限Python/JS測試有PASS；Tony-NB上的既有VAP、正式upstream Dataset、完整native runtime／正式跨系統資料流未由本輪驗證。矛盾的角色規格仍未解決，所以19/19不使OBS-0005轉GREEN。本報告保留原文以便追溯，不回寫不可變ZIP。

## 5個 RED 治理衝突

| 編號 | archive的system歸屬 | 衝突與來源 | 解法及應產生的新artifact |
|---|---|---|---|
| OBS-0130 | VQG | `VAP capability conflict`；README說cleaning/statistics/technical/AI insight，新pasted_content_13又要求VAP純視覺不計算。 | Owner簽核責任分工；核定VQG計算/VAP呈現契約，另外逐項列出v027既有helper相容／例外／棄用計畫。這列雖歸VQG，名稱與VAP角色衝突有關，不重新歸屬原archive。 |
| OBS-0166 | VAP | `Product-role contradiction`；新規格同一文件早段與後段責任描述不一致。 | 以正式spec版本、優先序與approved change log決議；逐條FR/NFR/VOM diff。新規格不得靠heuristic同義字或自動AST注入強制一致。 |
| OBS-0169 | VAP | `QA artifact internal contradiction`；QA_v0300.json同時有gate/PASS與selftest.ok=false、errors=1。該列原integration說NON-STOCK artifact，不是VAP runtime。 | 取回原始failing-case log，依原source/hash重跑對應測試，由runner重新生成一致QA。不能改errors為0或把此NON-STOCK QA問題當成VAP原生測試失敗。 |
| OBS-0194 | VCGC | 舊 `EXCLUSIVE_REPLACEMENT` 與最新 `EXISTING_PLUS_NEW_ATLAS_AND_LOCAL_TOOLS` 相衝突。 | 最新additive政策優先，不應用舊replacement部署效力。以版本化policy decision保留歷史；現有VCGC installer/EnvManager/InstallGate/Token工具不改動。 |
| OBS-0195 | VQG | `QuantGuard / QuantGenerator ambiguous canonical name`；pasted_content_12與13來源命名不同。 | Owner核定是否不同產品、各自canonical IDs／模組功能／來源／CLI/API及version；核定前維持不同，不silent合併或正式註冊。 |

## 2個 RED 環境閘

`OBS-0185`是Tony-NB無可操作workspace與未核實root；最近已讀裝置狀態為unavailable，不能讀寫C槽。`OBS-0186`是沒有可核實的VCGC MCP server／connector／owner權限。一般Manus MCP工具可用或本地候選stdio已能回覆，並不等於這两道正式閘已解除。

若Tony-NB恢復可達，第一步僅刷新device/workspace、核實owner／root與既有VCGC source。其後循序執行：外部hash→新版本candidate stage→固定offline工具測試→VCGC inventory/dry-run→owner review→隔離canary consumer integration。任何階段hash drift、source/root缺席、ACL/contract不明都STOP；不自動遷移root、不任意pip/accelerator注入、不開Database schema migration或full SettleAll。

## 目前可安全完成與必須等待的工作

目前已可完成的是Windows手動stdio指南、source-pinned候選status/query/token工具、ZIP／matrix稽核與Header字階調整。尚需owner或實機資料的是native engine根目錄／SSOT、VCGC endpoint/CLI與schema ACL、真實sample、VDF來源契約與DB目標、VQG身份決議、VAP責任分工。這些不是增加UI動畫或重跑已通過的候選suite能解決的問題。
