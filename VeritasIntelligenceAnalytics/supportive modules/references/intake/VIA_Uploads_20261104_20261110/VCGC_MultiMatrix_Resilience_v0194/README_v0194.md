# VCGC MultiMatrix Resilience v0194

本版以 v0193 為基礎，強化中央治理的自適應監看、失敗隔離、版本化安裝、註冊續跑與證據失效。維持一個 Python 後端、一個離線 HTML，左側為 VCGC／VDF／VRN／VQG／VAP 五個獨立入口；無 HTTP UI 伺服器。

**交付狀態：程式與隔離測試已完成；Tony 的 Windows C: 目錄、PowerShell 原生 AST、全套 VDF／VRN／VQG／VAP 業務輸出尚未在本次環境執行。未更新 GitHub。**

## 版本差異與合併

v0193 → v0194：頂層函式／類別新增 25、修改 24、保留不變 40、移除 0。逐項名稱與來源 SHA256 見 UpgradeComparison_v0194.json。舊版跨套件合併評估沿用已讀取的 v0193 MERGE_BASELINE，保留在 M15；本輪不把未知的其他對話內容視作已取得程式碼。

v0194 安裝器保留 v0192／v0193 原始檔；非 matrix 動詞沿既有版本鏈交回原生 VCGC。已知前版才允許準備升級；同版不同內容、更高尾版或多個主控根會停止，不自動覆蓋。三份原生 SSOT 產生下一版，新增需求、功能站與工作流程。正式中央編號及 checkpoint 仍由原生治理裁定；命令執行完成不等於正式結案。

## 使用方式（Windows PowerShell）

解壓縮後，在同時含 PY、HTML 的資料夾開啟 PowerShell。使用既有 Python 3.12 環境；PowerShell AST 需要 pwsh。Parquet 匯出需要該 Python 環境已安裝 pyarrow；缺少時 JSON／CSV 可用，Parquet 會明列 NOT_AVAILABLE。

先執行本版內建的兩組測試：

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix selftest
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix resilience-test
```

掃描兩個預設根目錄並持續監看，會自動開啟 HTML：

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix auto --activate-tools --open
```

預設來源：

- C:\Users\tonyk\OneDrive\Documents\movies-dataset
- C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics

預設輸出：`$HOME\AppData\Local\VCGC\MultiMatrix_v0194`。HTML 按「連接報告資料夾」選此資料夾。支援資料夾 API 的 Chrome／Edge 可送入本機佇列；不支援時使用「匯入掃描 JSON」。純 HTML 不能自行啟動 Python 或取得任意磁碟權限。

整合進既有 VCGC（新增版本、註冊與檢查）：

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix install --apply --activate-tools --watch --open
```

省略 `--apply` 只產生安裝計畫。安裝前執行原生 token、handoff check、functions、token chain、ssot panorama、test --quick；未通過就停止寫入。若兩個根目錄都有活躍主控，須用 `--roots` 明確指定要升級的唯一主控倉庫，例如：

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix install --apply --roots "C:\Users\tonyk\OneDrive\Documents\movies-dataset"
```

完成後可用上方 `matrix auto` 再掃描兩個根。多主控歧義會顯示警告，仍可唯讀盤點來源檔；不假定哪個主控有權覆蓋另一個。

## 自適應的實際範圍

1. 每 15 秒觀測來源樹；每 300 秒加做程式內容雜湊核對。連續兩次觀測穩定，且距離上次嘗試至少 30 秒，才重新掃描。參數集中於 PY 頂部。
2. SHA256 與解析版本相同才重用快取。變更的 Python 來源檔交給獨立子程序解析，最多 4 路；單檔失敗保留在清冊，不阻斷整批。
3. AST 函式／類別與原生 stations 自動形成 M18 功能清冊，記錄新增、變更、移除。函式發現不等於平台 Skill 安裝、正式中央註冊或業務功能啟用。
4. 每次掃描重算來源、資料、環境及治理規則脈絡，過期或雜湊不符的測試證據不沿用綠燈。
5. 完整輸出成功後才切換 current.json 所指的快照；前端核對快照 SHA256、版本、批次及結構。不完整新輸出不取代上一批有效快照。
6. session 到期前輪換，前端每次送工作前重讀；停止監看時使 session 過期。輸入佇列僅允許 scan／native-quick／selftest／resilience-test／export，不接受任意 shell。

## 20 項重大失敗分析

P0／P1 是工程處置優先級，不是根據生產事故資料估算的發生機率。每項都有對應測試名稱，見 FailureMatrix_v0194.json；22 項故障測試涵蓋以下 20 類，另含「復原不可刪除使用者修改」及「暫時 PS 失敗必須重試」案例。

| 編號 | 等級 | 主要失敗情境 | 防護與處置 |
|---|---|---|---|
| F01 | P0 | 根目錄不存在／OneDrive 未完整落地 | 讀取根目錄與連結狀態，明列未覆蓋範圍；保留分母 |
| F02 | P1 | Python／PowerShell／套件缺失 | 能力檢測；缺原生 PS parser 或 Parquet reader 保留未驗狀態 |
| F03 | P0 | 主控版本已升級或相容鏈不成立 | 接受已知 v0192／v0193；新尾版與同版異內容停止套用 |
| F04 | P0 | SSOT 結構漂移／重號／多主控來源 | 欄位與 station ID 檢查；主控根多義時停止寫入 |
| F05 | P0 | 掃描或套用期間來源變動 | 穩定讀取、前後 SHA256 與發布前重新核對 |
| F06 | P0 | 崩潰遺留鎖／多程序同時升級 | OS 鎖隨程序死亡釋放；原生根與輸出目錄均獨占 |
| F07 | P0 | 磁碟不足／輸出寫到一半 | 空間預留；完整 generation 才更新 current 指標 |
| F08 | P0 | 安裝中斷留下半套檔案 | 先寫 journal 與 staged 檔，主入口最後發布；復原只處理雜湊及檔案身分相符項 |
| F09 | P0 | 註冊只成功一半或執行結果不明 | 逐步收據續跑；RUNNING 中斷先核對，不盲目重播 |
| F10 | P1 | 快取損毀／舊解析器結果誤用 | SQLite integrity、逐筆 checksum、隔離壞庫並重建 |
| F11 | P1 | 單檔 AST 失控／記憶體不足 | 變更檔獨立子程序、有界併行與逾時；Linux 加記憶體上限，失敗保留分母 |
| F12 | P1 | PowerShell 一個壞檔拖垮整批 | 失敗批次二分拆解到單檔，未取得原生 AST 不算通過 |
| F13 | P0 | 命令卡死／取消留下子程序 | 逾時與中斷均清理自己的程序樹，保留日誌與退出碼 |
| F14 | P0 | 重複工作／半寫 JSON／偽造指令 | allowlist、session、檔名 ID、防重播與寫入安定期；不覆寫已成功收據 |
| F15 | P0 | 來源／資料／環境已變，仍沿用舊綠燈 | 雜湊、環境、規則、有效期失效；新掃描重算證據 |
| F16 | P0 | exit 0／假斷言／NaN 被當作正確結果 | 嚴格 JSON、預期與實際值核對、工具探針型別限制 |
| F17 | P1 | 429／5xx／連線逾時與重試風暴 | 既有 governed transport 可選用有界退避；401／403／PermissionError 即停止 |
| F18 | P0 | 工具雜湊不符／API 不相容 | 鎖版與呼叫結果檢查；缺件降級本地掃描，不繞網路政策 |
| F19 | P1 | 前端讀舊資料／session 過期／JSON 不相容 | current manifest 與內容 SHA256、版本與 schema 檢查；session 重新讀取 |
| F20 | P1 | 新增功能漏登／連續更新觸發掃描風暴 | AST＋原生 station 差異清冊；穩定兩次觀測與冷卻後自動重掃 |

## 矩陣與測試位置

- M00–M16 保留 v0193 的檔案／AST、加速網路、輸入、輸出、參數、指標、圖形、SSOT、測試、錯誤、修正、效能、版本、Skill、舊版比較、註冊。
- **M09**：逐檔 UNIT／INTEGRATION／SYSTEM／RESULT VALIDATION／CLOSE-OUT。
- **M17**：20 項失敗防護、優先級、版本、日期、解法、實作函式、故障測試與本機驗證狀態。
- **M18**：功能發現與新增／變更／移除清單。
- M17 的 `PASS_ISOLATED_FIXTURE_ONLY` 只表示同一引擎 SHA256 的隔離防護測試通過；第一欄本機燈號仍可能是黃燈。
- 本地 ID 與正式 SSOT ID 分離；未正式裁定不偽造中央號碼。

## 中斷與復原

安裝先記錄交易、寫 staged 檔，再發布新版本；主控 PY 最後發布。重新執行 install 時會先檢查未完成交易。需單獨復原時：

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix recover
```

復原僅刪除與本交易 SHA256、檔案身分及發布意圖相符的新檔。檔案已被人修改或不明衝突時保留檔案並回報 RECOVERY_CONFLICT。請保留相同 `--out`，其中有原交易與註冊紀錄；換一個空輸出目錄不能憑空重建歷史證據。

註冊分步記錄；失敗後重新執行相同 install，或 `matrix register`，會跳過具有效日誌的已完成步驟。若紀錄停在 RUNNING，表示副作用可能已發生但沒有完成收據；會回報 IN_DOUBT_REQUIRES_NATIVE_RECONCILIATION，不自動重播。須檢查原生日誌、numbering audit 與 registry 狀態後人工對帳，避免重號。

快取損毀會隔離為 .quarantine 檔並重建。報告 generation、舊快取與原生版本不自動刪除；需依留存規則另行整理磁碟。

## 加速、網路、NLP 與平台 Skill

本版啟用本身的有界處理、內容快取、增量掃描、分批 PS 解析、延遲 AST 明細與差異清冊。`--activate-tools` 嘗試載入已鎖定且雜湊相符的既有加速器；缺件或不符會保留未驗狀態。本輪不憑標記宣稱所有 PS／PY 加速器執行覆蓋 100%。

`bounded_network_call()` 是給既有受治理 transport 使用的可選轉接函式，可有限次重試 429／5xx／Timeout／ConnectionError；403／401／PermissionError 立即停止。它尚未在您的 VDF 外抓引擎逐一接線與實測，不代表所有引擎已換成最新網路工具。未使用替代網路路徑繞過拒絕政策。

NLP／跨平台工具與 22 項技能清冊保留於 M14。沒有遠端帳戶的執行權限或呼叫證據時仍標 NOT_CONNECTED；不因本機掃描完成就聲稱 Claude／ChatGPT／Manus／Gemini／Copilot 已啟用。

Claude Project 可將本 README、最新功能差異、指定系統的契約與少量有效收據作為專案知識，要求先讀增量再開相關 AST。此 ZIP 是程式升級包，並非可直接匯入平台的 Skill 包；本機執行需有實際本機工具與授權。

## 本次驗證

| 驗證 | 結果 | 範圍 |
|---|---|---|
| 既有回歸 | 45／45 通過 | Python 隔離測試 |
| 故障注入 | 22／22 通過 | 20 類風險＋保留修改／暫時失敗重試 |
| 整合驗收 | 13 通過、1 跳過 | 模擬原生主控、實際檔案交易／命令／收據；缺 pwsh |
| 背景監看 | 4／4 通過 | 真實暫存檔案修改、自動重掃、新函式、停止過期 |
| 前端資料驗證 | 7／7 通過 | 實際出貨 JS 函式＋模擬資料夾介面 |
| UI 操作 | 已觀察通過 | 共享 Chromium、入口、矩陣、搜尋、明細、啟動指引 |

每組 JSON 報告附於 ZIP。這些測試不證明投資資料、VRN 報告解析或 VQG 計算業務正確；仍需各系統的 golden reference 與本機 U/I/S/R/C 收據。AST 解析覆蓋、AST 動作執行覆蓋、加速器覆蓋與測試覆蓋是四個不同量。

Windows 限制：本次未執行原生 PowerShell AST、Windows 鎖與 taskkill 分支或檔案選擇器。Linux 子程序設有記憶體硬上限；Windows 目前為有界併行與逾時，尚無 Job Object 記憶體硬限制。程序樹清理不保證收回已脫離父程序的工作。斷電／磁碟硬體故障不等同本次模擬的程序中斷。

最後關卡仍為實際主機完成：掃描範圍無缺口 → PS／PY 原生 AST → 每檔加速與每個外連出口的真實呼叫證據 → 各系統 U/I/S/R/C → 原生中央註冊與 checkpoint。
