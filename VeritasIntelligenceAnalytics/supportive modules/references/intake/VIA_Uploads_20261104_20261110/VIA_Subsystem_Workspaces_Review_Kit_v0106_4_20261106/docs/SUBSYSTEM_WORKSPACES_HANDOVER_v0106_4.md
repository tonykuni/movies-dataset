# VIA 六系統獨立工作台與 AI 交接指南 v0106.4

這是 **ENG049 視覺鎖的唯讀候選工作台＋有限 MCP/Token 工具審查包**，不是 VCGC、VDF、VRN、VQG、VAP、Database 的完整正式安裝包。新畫面、資料與交接 artifact 可共用規格；各原系統 runtime、環境治理與正式登錄仍独立。既有 VCGC Installer／EnvManager／InstallGate／Token 功能不被替換。

最新畫面為 v0106.4；v0106.1 全量 PDF 容量失敗、v0106.2 匯出/測試落差均另存證據。v0106.3 已補全全量 Markdown 來源 hash 與 Database 歷史區；分卷保留原來源每一列及重複出現的紀錄，不靜默去重。v0106.4／Global v0105.3 額外修正 ResizeObserver：觀測回呼只排程下一影格，pixel 整數化且數值不變就不寫；不吞 error、不隱藏警告。7頁連續縮放／字級／側欄的42項 native RO 專測 PASS，delivery phase 的 layout writes 為0；domain model hash不變。UI、來源快照與 Token/MCP 工具版號分開，後者仍固定原本受測版本。

## 1. 開啟與三頁資料關係

解壓至新的審閱目錄後，開啟 `public/index.html` 或 `public/subsystems-v0106.4.html`；不需要 HTTP server、CDN、外部圖片或 DB。請使用支援 `DecompressionStream` 和 Web Crypto 的現代 Edge/Chrome。Manus 版本在 **Preview** 檢视，未公開發布。

每個子系統各有一個獨立畫面。中央第一頁「摘要」由最後頁 `LAST_MATRIX` 動態計算，不另造一份矛盾系統狀態；中間「驗證」區分該系統專屬測試資料、shared/session 收據及 native 未測邊界；最後「管理」頁為預設畫面，上方顯示流程／關係證據圖，下方是該系統全部已盤點矩陣。第一欄為燈號、第二欄編號、第三欄 SSOT 名稱，最後一欄保留錯誤詳細說明。左右面板可獨立收合，標題 sticky，主 Header 字級略大於面板字級；金色生命樹 Logo 真透明、無底框。

| 系統 | 精確專屬列 | RED | YELLOW | GREEN |
| --- | ---: | ---: | ---: | ---: |
| VCGC | 22 | 3 | 19 | 0 |
| VDF | 50 | 1 | 49 | 0 |
| VRN | 24,426 | 1 | 24,382 | 43 |
| VQG | 33 | 3 | 30 | 0 |
| VAP | 2,135 | 3 | 2,097 | 35 |
| Database | 0 | 0 | 0 | 0 |

精確條件是 `row.system == 當前系統`。116 列 relevant shared evidence 另行呈現，不能加到每個系統專屬列，也不能把同一筆 shared PASS 算成五次 native PASS。VCGC add-on 的 Token/MCP 候選、其他 AgentOS 等 shared 系統仍可在全域治理頁／獨立 shared 區檢閱，不被錯算為 native VCGC 原碼。

Database 在固定 v0105 合併模型沒有專屬列；其頁面明示 `NO_OWNED_SOURCE_ROWS / UNAVAILABLE / NOT_RUN`，零列不等於 GREEN。先前 Database 治理資料若列於歷史區，只是另綁 SHA 的歷史來源，不表示本輪資料庫已連線或建立。

## 2. 流程圖不是虛構的 live 架構

圖上的點來自可追溯的來源列，帶有來源編號、版本、檔案/模組名稱、scope 及 source。點擊節點會顯示同一矩陣列的 Inspector。大系統的可視圖有明示數量限制；未畫出的列仍完整存在於矩陣和全量匯出中，不能把圖中點數當成全部已安裝／已註冊工具數。

每個節點獨立列出 Install、Registration、Normal operating、Auto test。缺證據是 `UNKNOWN / NOT_REGISTERED / NOT_RUN / NOT_OBSERVED`，不由檔案存在、AST 或其他 fixture PASS 推論為正常運行。GREEN 只適用該筆來源 status 的既定範圍；例如 VRN 的 43 個檔案 GREEN 不等於 43 個 runtime 已啟動。正式整合仍顯示 **ACTUAL · RED / BLOCKED**。

只有明確 source/target 或來源契約支持的關係才畫 `DECLARED`，不畫成 LIVE；沒有足夠證據則為 `OFF`，節點故意不連線。未知 completion_time/tools/version 保留 `NOT_OBSERVED`；畫面產生時間不可冒充每個引擎完工時間。Python AST 編號是候選 locator，不是正式 SSOT 註冊。CLS/FNC/LIB、JSON 葉節點、静態文字來源也不是同一種可執行指令。

只有紅色圓燈有 2.8 秒慢速閃動，黃綠靜態；開啟系統 reduced-motion 時紅燈也靜態。燈號不具備「點一下即正式修復／開閘」功能。

## 3. 右上角匯出：全部與 AI 接續各自適用

| 匯出 | 用途與完整性 |
| --- | --- |
| 全量 JSON | 該系統九分類完整 raw `LAST_MATRIX`、shared evidence、來源/觀測 SHA 與安全 metadata；原型別保留。若另有 `DISPLAY_MATRIX`，它只是加入顯示用 NOT_OBSERVED 的衍生層，原資料不變。 |
| 全量 Markdown | 所有系統專屬列、所有欄位與來源資訊；VRN 檔案很大，適合封存/分段處理，不宜整份塞進 AI context。 |
| AI handover MD | 適合同一個 AI 下一輪續作的精簡交接：具體 RED ID/原文、source hashes、測試 scope、未完成閘與 owner 待辦；不是隱藏阻礙的成功摘要。 |
| AI 交接 PDF | 預設較短的狀態、流程圖、RED 與 provenance 報告；由 browser 列印／另存 PDF。 |
| 全量分卷 PDF | 明確選擇卷號後，包含該卷每筆紀錄所有欄位，顯示起訖列、總列數、總卷數、來源 hash。需分別保存各卷，不能把單卷稱作全量。 |
| CSV | 匯出目前篩選的完整集合，不限畫面 50 列；公式前綴以純文字保護。 |

JSON/MD/CSV 透過 Blob 下載到瀏覽器設定的 Downloads；PDF 按鈕啟動列印對話框，請選「另存為 PDF」和下載位置。網頁無權直接寫 `C:\Users\tonyk\Downloads`，也不會冒稱 PDF 已自動保存。

**實際修補原因：** v0106.1 將 VRN 的 24,426 列、數十個欄位一次交給 Chromium，`Page.printToPDF` 真實失敗。v0106.4 因而改成有界分卷和精簡 AI PDF，並保留失敗來源。這不是刪資料；JSON/MD 全量保留。首末卷／摘要 PDF 的實測不能擴大為每一卷都已逐份渲染；請以最終收據的 PDF 範圍為準。

## 4. 本轮已實跑能力與不能跨越的界線

本輪 AllInOne v0100 在新 scratch 的 reference lifecycle 為 63/63，有限 loopback UI startup 7 項檢查後正常停機；它不是 native 五系統通用認證器。Token candidate CLI 5/5，五系統非敏感摘要的 JSON compact／semantic round-trip 5/5，MCP stdio 有限候選 session 已實跑並正常結束；provider calls=0。這些候選工具沒有全域常駐啟用，也沒有修改 VCGC 原有 Token 引擎。

非敏感摘要的 TokenEngine **heuristic** 降幅 VCGC 25.32%、VDF 22.93%、VRN 26.35%、VQG 24.67%、VAP 25.13%；只是這五筆測試樣本，不是實際模型 tokenizer、帳單省幅或所有工作負載保證。

GitHub 本輪成功完成 authenticated 三個限定 GET、沒有 write／push／merge／workflow 觸發。它只證明当次 repository metadata 可讀，不證明 Tony-NB checkout 與 GitHub hash 一致。Tony-NB 當次仍 unavailable、無 workspace；PC/Windows、正式 VCGC connector、SSOT 登錄、Database、VDF/VRN/VQG/VAP native 整合仍 NOT_RUN/BLOCKED。

## 5. Windows 安全 stage 與原參考引擎啟動

先核對交付 ZIP 與 `.sha256` 側檔。把以下 `$Zip` 與 `$BootstrapStage` 換成您實際下載/審閱的位置；stage 工具可以先從 SHA 已核實的 ZIP 在 Downloads 新目錄取出，不要先解到正式系統根。

```powershell
$Zip = 'C:\Users\tonyk\Downloads\VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip'
$Sidecar = "$Zip.sha256"
$Expected = ((Get-Content -LiteralPath $Sidecar -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$Actual = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Expected -notmatch '^[a-f0-9]{64}$' -or $Actual -ne $Expected) { throw 'STOP: ZIP SHA mismatch' }
$OwnerRoot = 'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics'
if (-not (Test-Path -LiteralPath $OwnerRoot -PathType Container)) { throw 'STOP: owner root missing' }
$BootstrapDir = Join-Path 'C:\Users\tonyk\Downloads' ('VIA_review_bootstrap_' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $BootstrapDir) { throw 'STOP: bootstrap target already exists' }
Expand-Archive -LiteralPath $Zip -DestinationPath $BootstrapDir -ErrorAction Stop
$BootstrapStage = Join-Path $BootstrapDir 'scripts\stage_subsystem_workspaces_v0106_4.py'
py -3 -B $BootstrapStage --zip $Zip --sha256 $Expected --root $OwnerRoot
if ($LASTEXITCODE -ne 0) { throw 'STOP: stage failed' }
```

stager 驗 external SHA、CRC、精確 manifest、每檔 SHA/bytes、SHA256SUMS、Windows 安全路徑、symlink/reparse、候選 false flags；只在已存在根下面新增 `VIA_Review_Candidates\v0106.4_<timestamp>`，不執行引擎或覆寫根。該 root 不見就 STOP，不能自動改到 `C:\VeritasIntelligenceAnalytics`。

接著將 stage 回傳的確切 `target` 設為 `$Candidate`，只跑新副本，不猜最新目錄：

```powershell
$Candidate = '<stage returned target>'
& "$Candidate\scripts\Start-VIA-MatrixGovernance-Candidate-v0106_1.ps1" `
  -DownloadRoot 'C:\Users\tonyk\Downloads' `
  -OwnerRoot $OwnerRoot
```

此 launcher 只核對使用者指定 Downloads 的原始三檔、既有 Python/依賴，另創參考 candidate、跑 doctor/self-test。它不安裝、不繞過 ExecutionPolicy、不修改 VCGC EnvManager、不跑任意修補、不建立 tunnel/service。`-LaunchUI` 是額外選用的前景 loopback UI；URL 由來源終端機真實印出，按 Ctrl+C 停止，不能當 MCP HTTP endpoint。Windows PowerShell parser/native 執行尚未在 Tony-NB 實測。

MCP stdio 接入詳見另附 `MCP_WINDOWS_COMPLETE_GUIDE_v0105_2.md`。最新 server 仍是固定 `scripts/via_governance_mcp_v0105.py`，不接受 `--package-root` 啟動參數；package_root 由 tools/call 的參數傳入。支援三個工具 `via_status`、`via_inventory_query`、`via_token_prepare`，不是任意 Windows shell／全系統安裝器。stdio 沒有 URL，不要使用虛構 localhost `/mcp`。

## 6. 一條命令：必要有限驗收

在新候選包根目錄使用既有 Python、Chromium、Playwright、pdftotext，輸出到包外不存在的目錄：

```powershell
py -3 -B scripts\run_subsystem_checks_v0106_4.py `
  --package-root $Candidate --out '<existing-parent>\new_unique_receipt_dir'
```

runner 固定來源/命令，不自行發現執行任何 `test_*.py`。流程是 UI 白箱、安全 stager、MCP 白箱、Token 5 項、有限 MCP stdio，再跑六頁三視口和 PDF/交接下載 E2E；缺工具停止，不自動 pip/npm 或下載 browser。收據只表示當次實跑 scope；選 `--skip-ui` 就必須記作 UI NOT_RUN，不得沿用外層 PASS 充當 UI 成功。

## 7. 真正啟動前仍須完成

先取得可操作 PC workspace、owner 根與權限；核對 native 各系統 manifest/hash、既有 EnvManager、SSOT/名稱衝突、允許的 Dataset/Network 契約、版本/依賴與 real fixture。再逐系統隔離做 unit → standalone → contract/integration → system → output read-back/rollback。依 evidence artifact 交換，不合併五個 runtime；候選通過不能自动開正式閘。詳見另附五系統 RED 修復計畫；沒有相對應 native receipt 就保持 RED/BLOCKED。
