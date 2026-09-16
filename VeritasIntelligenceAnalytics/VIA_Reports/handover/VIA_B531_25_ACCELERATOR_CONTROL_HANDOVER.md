# VIA B531：25 項 PowerShell 加速器與 Python 單點掛載交接

**批次：** B531
**日期：** 2026-09-16（Asia/Taipei）
**分支：** `claude/via-envmanager-governance-7cls8h`
**治理所有者：** VIA Central Governance
**主要控制器：** `CGC_MDL156_VIAAcceleratorControl_v0100.py`

## 一、裁決

B531 已完成 **25 項加速器控制面、PowerShell roster、Python bootstrap 身份、SuperAccel/Celeritas/Aegis 掛載、QuantGuard 禁用政策與中央冊註冊**。離線控制面實測為 **GREEN 20/20，`READY_FOR_25`**；25 項是中央治理、路由與證據 roster，不代表已安裝 25 套獨立第三方演算法。

**QuantGuard 是唯一活動技術分析／因子路徑；TA-Lib 永久禁用。** Canonical Celeritas 與 QuantGuard bridge 已移除 TA-Lib 可選載入與同名 fallback，改由 QuantGuard／純 Python deterministic fallback 承接。`VIA_RetiredEngines`、`functional modules/TALib` 與歷史 intake 仍保留為封存／參考材料，沒有被本批重新接回活動路由。

B531 的整體中央同步摘要為 8 站中 **7 站通過、1 站保留既有歷史介面漂移**。`iface_sync=1` 不是 CGC156 25 項控制面失敗，而是 InputConsole 內 6 個既有引擎 contract drift；本批沒有盲改它們，也沒有宣稱全樹零漂移。

## 二、實測矩陣

| 測試項目 | 實際結果 | 裁決 |
|---|---:|---|
| CGC156 25 項控制面 | 20/20 | **GREEN** |
| SSOT roster | ID `01..25`、數量 25 | **PASS** |
| PowerShell roster 靜態計數 | 25 entries | **PASS** |
| PS 相容 runtime | 靜態 roster 25；Windows 首次 probe 發現 scope 回退 20，已修正 global state | **待 Windows 重跑** |
| Python active tree | 3,111 files receive bootstrap path contract | **PASS（控制面檢查）** |
| Python bootstrap probe | roster `:25`、CGC156 identity、`VIA_NET_BOOT=1`、Celeritas/Aegis lazy mount | **PASS，RC=0** |
| SuperAccel activation | 88 libraries catalogued；9 available；79 missing/stub；17 thread-budget env applied | **PASS／誠實列缺件** |
| QuantGuard bridge | 8/8 selftest checks | **PASS，RC=0** |
| Canonical active TA-Lib scan | no forbidden import/path token in canonical mounts | **PASS** |
| Naming registry | 2,939 families；new 245；AST errors 0 | **PASS** |
| VCGC component registry | ACTIVE 4,996/4,996；AST errors 0 | **PASS** |
| VCGC family audit | 237/237 registered；unregistered 0 | **PASS** |
| Interface scan | new 0；drift 0；stable 2,784；one syntax-skipped file | **PASS（scan）** |
| Interface apply/sync | 1；6 legacy drift items remain | **YELLOW／限制** |

## 三、中央控制與掛載設計

PowerShell 正本為 `VIA_PS_Accelerators_25_Roster_v0100.ps1`，由 `VIA_PS_Accel_Module.ps1` dot-source。既有 `$VIA_ACCEL20` 不移除；完整 `$VIA_ACCEL25` 與 `Get-VIAAccelRoster` 供新入口使用。`via-accel` 的 `selftest|status|manifest|routes` 統一委派 CGC156；`--activate` 先執行 SuperAccel activate，再由 CGC156 驗收。

所有經 VIA 啟動且由 `Set-VIABoot` 將 bootstrap 放入 `PYTHONPATH` 的 Python 行程，均由 `supportive modules/bootstrap/sitecustomize.py` 設定：

- `VIA_ACCELERATOR_ROSTER=VIA_PS_Accelerators_25_Roster_v0100:25`。
- `VIA_ACCELERATOR_CONTROL=CGC_MDL156_VIAAcceleratorControl_v0100`。
- 快取優先套用加速執行緒預算，避免每支 Python 冷啟動重載大型套件。
- `VeritasCeleritas` 與 `VeritasAegisNexus` 使用 lazy canonical mount。
- `VIA_FAMILY=vdf` 才掛 `via_net`；網路同意仍由操作員持有，預設 fail-closed。

這個設計是「單點掛載」，不是逐一修改數千支 Python 檔；未經 VIA bootstrap 直接裸跑的 Python 不會自動得到這些環境身份，這是刻意保留的啟動邊界。

## 四、政策與安全狀態

**TA-Lib：** 不安裝、不 import、不復活。QuantGuard bridge 的 selftest 顯示 `legacy_indicator_library=FORBIDDEN_NOT_USED`，價格基準為 `adj_close`，成交量基準為 `non_day_trade_volume`。本批只修 canonical active Celeritas 與 QuantGuard intake mount；退休目錄與歷史附件未刪除，避免破壞 append-only intake，但不納入活動路由。

**網路：** roster 的 network accelerator 是明確的 ID `23`，但 `network_default` 為 `OFF`。離線驗收未啟動資料補庫，也沒有替操作員設定網路同意。VDF 的 `via_net` 只在 `VIA_FAMILY=vdf` 掛載，仍受既有 consent gate 控制。

**資料補庫：** B530 指示的 ENG054 全市場補庫仍停止。B531 沒有重新啟動網路抓取，也沒有宣稱 2023 或 2024+ 全市場資料完整。

## 五、未完成與限制

第一，sandbox 沒有 `pwsh`、`powershell` 或 PSScriptAnalyzer，因此 PowerShell 本體 parser／Windows runtime 尚未在本環境實測；目前已完成檔案級 roster 計數、入口靜態檢查與 Python 控制面驗證。請在 Windows pull 後執行附帶的一貼式 probe。

第一次 Windows probe 已實際發現並修正一個 PowerShell dot-source scope 問題：舊版模組雖讀到 25 項檔案，卻未把 `$VIA_ACCEL25` 公開到工作站全域，導致 `Get-VIAAccelRoster` 回傳前 20 項。修正版改用 global canonical state、以 `Count` 強制重建，並在 roster 非 25 項時立即停止。Windows 端需重新 pull 最新 commit 後再跑 probe；在重跑前不宣稱 PowerShell runtime GREEN。

第二，InputConsole contract sync 留下 6 個歷史 drift：`vdf/tw_daytrade_files`、`vdf/tw_revenue_codes`、`vrn/vrn_fourpoint`、`vrn/vrn_pdfplus`、`vrn/vrn_unified`、`central/via_ssot_autocode`。其中包含參數旗標與 verb 差異；若要修正，必須逐引擎確認真實 CLI 後再 version-forward，不可在本批盲改。

第三，SuperAccel catalog 的 88 項可用 9 項、缺少 79 項只表示環境能力狀態；不應將其說成 25 個獨立演算法全部已安裝。25 項目前是治理 roster／route／evidence contract。

第四，Windows `C:\測試樣本報告` 的原始 PDF/DOCX 本體仍未掛載到 sandbox；本報告沒有宣稱已完成該批真檔的內容解析。既有 VRN fixture 測試與 VRN DuckDB 狀態仍維持其原本的 synthetic／fixture 限定。

## 六、Windows 一貼式驗證

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
. .\VIA_Reports\handover\VIA_B531_25_ACCELERATOR_CONTROL.ps1
```

腳本只做本地 roster／中央 selftest／路由查詢與 QuantGuard status，不抓網路、不補 VDF 資料、不執行 TA-Lib。若要做 2024 至最新資料庫功能驗收，另行使用 `VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1`；其 `-RunTAOne` 僅保留為相容參數，會輸出 `BLOCKED`，不會執行 legacy path。

## 七、接棒順序

下一位 AI 應先讀本報告、`VIA_B531_25_ACCELERATOR_CONTROL_STATUS.json` 與 evidence bundle，再查看 `VIA_ACCELERATOR_CONTROL_latest.json`。若要處理 interface drift，先逐一讀 `/home/ubuntu/work/accelerator_control_b531/iface_sync.txt` 的 6 項明細，再做真實 CLI 對照；不要把 `iface_sync=1` 改寫成 B531 控制面失敗，也不要把 25 roster 說成 25 個獨立套件已安裝。

本批沒有執行 Windows 真實 PDF/DOCX 內容測試、沒有恢復外部補庫、沒有安裝 TA-Lib。

## 證據

完整機器證據位於 `evidence_b531_accelerator_control/`；三頁 Muji／Seaborn 風格狀態頁為 `VIA_B531_25_ACCELERATOR_CONTROL.html`。所有證據檔另有 `SHA256SUMS.json`。
