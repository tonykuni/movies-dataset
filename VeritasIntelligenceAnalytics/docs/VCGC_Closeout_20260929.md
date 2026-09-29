# VCGC／VRN／VDF 2026-09-29 實測交接

本輪結果：中央入口、版本辨識、Manager 委派與因子註冊已修正；**完整系統收尾仍為 OPEN**。靜態治理 YELLOW、RED 0，不等於完整工作流執行成功。原有成功擷取與 Layout 核心保持鎖定。

## 範圍與正本

- GitHub：`tonykuni/movies-dataset`；比較基準 `cb3727e78efdabd9361187d2180d30df5e3b8f6d`。
- 工作分支：`codex/vcgc-closeout-20260929`；本報告不表示已合併 main。
- 三日回顧：2026-09-26 21:38:47 至 2026-09-29 21:38:47（Asia/Taipei），328 個提交；另一個 `tonykuni/VIA-VDF-VRN` 倉在此區間無提交。
- 程式、政策與 SSOT 以 GitHub 為正本，主機保管資料庫。本輪未連入使用者主機，未寫入正式資料庫，未重抓已成功驗證的台股清單。
- 唯一入口：`CGC_MDL149_VeritasCentralGovernanceConsole_v0176.py`。Manager／編號器／檢核皆由此入口派送。既有 PowerShell `go` 執行路徑保留。

## 已修正並有實測證據

| 現行版本 | 修正與沿用關係 | 本輪結果 |
| --- | --- | --- |
| VCGC v0176 | 沿用 v0175 的 SSOT 說明卡；修正子引擎 `--selftest` 被中央攔截；支援 `STEM`／`_STEM` 薄模組繼承盤點 | 92 檢通過 |
| NumberingSystem v0106 | 沿用 v0105 的連字號版本與字母尾碼辨識；在原中央收集／發號器追加 FAC K25 | 36 檢通過 |
| VDF SystemManager v0119 | 恢復 `read`／`read_engine`／`measure` 與屬性委派；CLI 使用同一個現行 facade 與原同意閘 | 8 檢通過 |
| VRN SystemManager 現行版 | 經原 LogicRollup 檢查 6 層、55 個現行節點 | missing 0、updated 0、lock_success true |

另有 VDF `measure` 實跑 rc=0、8 個領域 GREEN、引擎數據 NODATA；`fetched=false`、`chain_written=false`。它證明 Manager 可讀與量測，不代表正式行情資料已更新。

三個新版本的通過證據與原始碼 SHA-256 收入交付包的 `CONTRACT_CHECKPOINT.json`。這是可重現的契約測試快照，不替代完整工作流 LampLock。

**撤銷早期錯誤證據：** v0175 曾將子引擎測試參數誤當中央自測；`sdd-selftests.log`、`vdf-manager-final-selftest.log`、`numbering-105-selftest.log` 不可用作子引擎成功證據。不得引用早期「52 個全通過」。v0176 已修正派送，替代證據詳見 `INVALIDATED_TEST_EVIDENCE.json`。歷史 v0175 檔案保留，但不得作為獨立 CLI 入口。

## SSOT、自動編號與保留政策

中央元件冊 13,957 筆，現行 13,639 筆；對基準新增 170 筆、恢復先前盤點遺漏的 320 筆，刪除 0、改號 0、新退役 0、重號 0。

中央分類編號共 **101,100 筆**，相較基準 96,502 筆新增 **4,598 筆**，全部經既有中央編號器配置。28 條註冊工作流（VCGC／VDF／VRN 27 條，另 VAP 1 條）、104 步、99 項需求共 231 個 WKF／STP／REQ 識別完整。

| 類別 | 筆數 | 類別 | 筆數 |
| --- | ---: | --- | ---: |
| MDL 模組 | 4,154 | ENG 引擎 | 694 |
| CLS 類別 | 3,758 | FNC 函式 | 85,886 |
| LIB 函式庫 | 270 | ENV 環境 | 454 |
| PLCY 政策 | 1,025 | PRMT 參數 | 888 |
| LGC 邏輯 | 634 | FAC 因子 | 7 |
| SSOT | 501 | RGX | 105 |
| SYN 同義字 | 890 | TOOL | 18 |
| WKF 工作流 | 28 | STP 步驟 | 104 |
| REQ 需求 | 99 | TST 測試 | 439 |
| FD | 47 | BI | 27 |
| MRC | 292 | FM | 272 |
| IDX | 63 | OPT | 439 |
| XSRC | 6 | | |

- 7 因子、30 邏輯、14 參數、12 政策參照既有 QuantGuard 凍結 SSOT：保留來源指標、宣告版本與定義指紋，不複製公式、不建立第二套正主。
- 修正 428 筆歷史錯判版本：舊號與歷史列保留，正確版本追加新鍵／新號。補齊 3 筆模組／引擎時間缺口，依真實 Git 提交時間，不造時間。
- 現行 MDL／ENG 冊的版本與更新時間欄無空缺；這只表示欄位完整，不表示所有模組均已實跑。
- LIB 中 142 筆仍是「未釘」、10 筆是最低版本條件、118 筆屬 stdlib；另 5 筆歷史時間仍為 `uncommitted`。主機套件版本尚未驗證，不冒填版本或時間。
- 73 本檢核範圍內 SSOT 無衝突，12 條鎖定 regex 對齊；中央同步 `pending=false`、`aligned=true`。分類 SSOT 共 501 筆與檢核 73 本屬不同範圍。
- 只增不減：既有 key／code 保持、人工備註保留；衝突另列。工具停止維護時先留下替代關係與退役原因，不自動刪除歷史。
- TA-Lib 遵循既有 L50 禁用政策；現行尾版掃描 import 0。QuantGuard 的執行仍受本環境缺少 Polars 影響。

## 已鎖定的擷取與工具

本基準的 Layout 政策鎖定 **11 個來源**；逐一 SHA-256 與政策相符，且與基準 main 位元組相同。既有 `.py`／`.ps1` 程式未修改，本輪只追加 5 個版本化 `.py`。歷史另一份測試的 13 檔鎖定不套用至本基準。

六工具鎖維持：Celeritas v1141、AegisNexus v1652（NetUnified v0118）、GenericLayoutHub v0109、UnifiedNLPOrchestrator v0105、Panorama v0116、frame v0100。已使用 token、read／slice／digest、pack、ETag 304 與 NLP brief；六項工具啟用／自測通過。ToolVersionLock 未修改。

現有 FirstPage v0139 已具非 OCR 優先、區域裁切、OCR 預算、後端隔離及 DPI 300–350 分級；現行 Layout／Figure 路徑已有原生幾何與快取能力。下一步以這些能力擴充品質升級路由，詳細設計在 `VRN_Adaptive_Extraction_Design_20260929.md`。**本輪沒有宣稱部署全新的自適應 OCR 控制器或量測其速度提升。**

## 完整實測及紅黃綠狀態

| 範圍 | 燈號 | 證據與限制 |
| --- | --- | --- |
| 本輪三個修正版契約 | GREEN | 92／36／8 檢通過，各自有原碼與證據指紋 |
| 註冊、編號、來源鎖、SSOT 衝突檢核 | GREEN | 同步對齊，舊號不變，來源鎖未動 |
| 整體靜態治理 | YELLOW | 14 個既有未完成需求；新尾版待完整工作流重新鎖定 |
| SDD 54 目標診斷 | RED／FINDING | 34 OK、16 FAIL、2 FINDING、2 CANON（上游參照） |
| 正式工作流／主機資料庫 | 未完成 | 無主機連線；本境缺 PowerShell／DuckDB／Polars；未寫正式庫 |
| 最終收尾 | OPEN | 現行 LampLock 與本次檢核指紋不一致，不套用假綠鎖 |

SDD 原始診斷實際測的是 Numbering v0105；v0106 隨後獨立通過 36 檢。本輪不改寫原始報告冒充同一次結果。16 個 FAIL 的記錄主要涉及 DuckDB 缺少；FirstPage 55/56 的失敗是臨時 DuckDB fixture 無法建立。兩個 FINDING 分別涉及 QuantGuard 的 Polars 與 MarketListGovernance 的 DuckDB。環境補齊後仍須實跑，不能推定會全過。

完整 REAL 聚合：NOT_RUN 8、FAIL 13、OK 5、FINDING 1、REGISTERED_ONLY 1。靜態指紋 `58d5bc014d05` 是 SDD 檢核指紋，並非 Git commit SHA。舊 LampLock 的 workflow 指紋為 `8593371c7960`；收尾顯示 14 條歷史已鎖、13 條未鎖，未寫入新的全通過 LampLock。

## GitHub 與主機後續

現有 Windows GitHub Actions 工作流已追加中央入口、Numbering、VDF Manager 及 VRN logic 契約檢查，全部由 VCGC 派送。沿用現有 DuckDB／pandas 安裝步驟；本輪未新增任意套件安裝或第二個生產執行器。CI 的實際結果須以對應提交的 Actions 為準，這份本機報告不代表 Windows CI 已通過。

第一次 Windows CI（run 36584690120）在既有 `test_11_committed_page_matches_generator` 失敗：註冊資料更新後，追蹤中的 MasterControl 頁與正主產出不同步，後續步驟因而被跳過。後續透過 VCGC 派送原 VIA System Manager 再生此頁，保留原測試；新增契約檢查改為未取消時獨立執行，其他步驟失敗仍維持整體 CI 失敗狀態。第一次失敗證據保留，重跑結果另列。

主機測試已獲使用者授權；使用者指定樣本資料夾 `C:\測試樣本報告`，每次後續作業先用 VCGC token，沿用 Panorama v0116 的 read → slice → digest 與 ETag。目前執行環境是 Linux，沒有該 C 槽掛載或可用主機遠端入口，不能宣稱已讀取此資料夾。取得入口後，使用 GitHub 該分支的程式與 SSOT，經 VCGC `enter` → 原 `go` → Manager，完成依賴盤點、指定樣本與正式工作流驗證及資料庫檢核，再按真實結果更新 LampLock。不得為了綠燈修改成功擷取邏輯、繞過現有 consent gate、把 NODATA 當成資料更新，或自行建構另一條執行路徑。

使用者另已核准 GitHub 測試資料／資料庫對接。既有 `VIA_DataHome_SSOT_v0100.json` 宣告資料庫根目錄 `C:\Users\tonyk\VIA System\via_database`，其 `VIA_DATA_HOME`／`VIA_DB_<庫名>` 解析與目錄頁優先規則沿用；樣本路徑亦已存在 VRN 邏輯中，不另建資料副本。`VIA_SyncHub_Endpoints_SSOT_v0100.json` 的 endpoints 為空；它的用途是唯讀副本／API 盤點，不是 Windows 遠端執行器。授權已足夠，目前真正缺少的是可達的 Windows 主機執行入口。

交付包是指定基準的增量更新，包含新版本、SSOT 變更、CI、設計與實測證據；不是含資料庫的完整獨立系統。套用前核對基準，衝突時依現行冊增量合併，勿覆蓋較新的主機或 GitHub 資料。
