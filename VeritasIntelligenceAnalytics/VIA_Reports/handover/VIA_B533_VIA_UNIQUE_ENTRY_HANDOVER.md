# VIA B533：唯一接觸口與 VRN／VDF／QuantGuard 中央實測交接

**批次：** B533
**驗收日期：** 2026-09-16（Asia/Taipei）
**控制平面：** `CGC_MDL157_VIAUniqueEntryControl_v0100`
**資料方向：** `VDF/DuckDB → QuantGuard`
**網路模式：** `OFF`；不代替操作員取得同意

## 一、最終結論

B533 已完成 VIA 唯一接觸口的離線控制面與三個子系統的中央派送實測。CGC157 自測為 **GREEN 18/18**，控制狀態為 `ONLY_VIA_ENTRY`。在該閘通過後，固定路由實際執行 VRN、VDF 與 QuantGuard，四個子測試路由全部 return code `0`，中央 dispatch 裁決為 **GREEN**。

這個結果證明目前指定的 VRN、VDF 與 QuantGuard 實測可以先經 VIA 中央閘，再由中央路由執行。它不表示 Windows 使用者資料夾的 60 份 PDF 與 4 份 DOCX 已在本 sandbox 完成內容解析；那些原始檔仍未掛載。倉內 fixture 驗證與真實 Windows 檔案驗收必須分開看待。

## 二、實測矩陣

| 中央路由 | 正主 | 實測結果 | return code |
|---|---|---:|---:|
| `vrn` | `VRN_ENG087_NLPTextSummaryBridge_v0100.py` | NLP Hub、6 項研報服務、證據摘要、DuckDB、VDF bridge、離線與 SuperAccel 橋 **11/11 PASS** | `0` |
| `vdf` | `VDF_ENG073_DataArchitecture_v0100.py` | SSOT 對映、資料盤點、只增不減最佳化、20 擷取加速器與 Zero-Hydra 規則 **9/9 PASS** | `0` |
| `vdf` | `VDF_ENG087_MarketListGovernance_v0101.py` | 股票全集、主動式 ETF、熱門族群跨組重複與成交值去重規則 **10/10 PASS** | `0` |
| `quantguard` | `VDF_ENG086_QuantGuardOneBridge_v0100.py` | 特徵列數、完整因子、adj_close、非當沖量、禁用依賴與輸出檔 **8/8 PASS** | `0` |

中央 dispatch 證據中的 `gate.verdict=GREEN`、`gate.control_state=ONLY_VIA_ENTRY`、`network.default=OFF`、`network.silent_open=false` 與 `verdict=GREEN` 均已保存。CGC156 同步重跑為 **GREEN 23/23，accelerators=25**。

## 三、中央控制與註冊結果

`CGC_MDL157` 稽核 PowerShell command book、唯一 `Invoke-VIAPython` helper、`sitecustomize.py` 單點 bootstrap、網路 fail-closed 設定、VRN/VDF/QuantGuard 子入口與中央 registry contract。所有 18 項檢查均通過。中央 dispatch 不接受任意檔案路徑，而是使用固定正本路由；子程序仍經 VIA bootstrap 注入 25-roster 與 accelerator-control 身份。

CGC054 介面 binding sync 在修正後第二次驗證為 **58/58 OK、DRIFT=0、BUMP=0**。本批精確收斂的六項 contract 為：當沖檔案改用 `--from-file`、月營收代碼改以位置參數、四點摘要改用 `--ticker`、PDFPlumberPlus 收件夾改用 `--scan-dir`、VRN Unified 的 selftest 改存為 `test_verb` 而不冒充 engine verb，以及 CGC155 text 改為位置參數。這些修正沒有修改停止中的資料補庫邏輯。

VCGC registry-sync 已套用，結果為 `active=5027`、`new=1`、`changed=8`、`retired=0`、`AST errors=0`。新增與變更已寫入 Component Inventory、Interface Contract Registry 及中央 InputConsole contract；第二次 interface plan 已確認收斂。

## 四、政策與安全邊界

QuantGuard 是唯一活動技術分析與因子路徑。TA-Lib/talib 不得安裝、import、載入、恢復或掛入活動路由。QuantGuard 只讀取 VDF 或 VDF-owned DuckDB/Parquet 的來源面，產生 features、factors、SSOT 與 evidence outputs；禁止反向修改 VDF 來源、修改來源資料庫 schema、自行觸網或自行取得 operator consent。CGC156 與 QuantGuard bridge 均保留此資料流與來源唯讀政策。

本批沒有啟動 AKShare、沒有重新執行全市場資料補庫，也沒有替使用者開啟網路同意。SuperAccel 的先前實測仍如實保留為 88 個 catalogued、9 個 available、79 個 missing-or-stub；這不會被誤寫成 25 套獨立演算法已全部安裝。25 項是受 VIA 控制的 roster、route 與 evidence contract。

## 五、尚未宣稱完成的項目

第一，sandbox 沒有 `pwsh`、`powershell` 或 `PSScriptAnalyzer`，所以 B533 沒有在 Linux 內假稱 PowerShell runtime parser 已通過。Windows 使用者必須 pull 最新分支後重跑 command-book probe。第二，`C:\測試樣本報告` 的 60 份 PDF 與 4 份 DOCX 本體不在 sandbox；本批只完成倉內 Python fixture 與正主 selftest，不宣稱已解析那些真檔。第三，2023 起始的全市場資料補庫仍按使用者要求保持停止；VDF 的歷史覆蓋不足不能被中央 selftest 的 GREEN 混寫成資料完整。

## 六、Windows 重跑入口

在 Windows PowerShell 7 從 VIA 根目錄 pull 最新分支後，可執行：

```powershell
. .\Register-VIA-Commands-v0208.ps1
via-unique-check
via-central vrn -SelfTest
via-central vdf -SelfTest
via-central quantguard -SelfTest
# 25 項 roster probe（若要驗 Windows scope 與命令冊）
. .\VIA_Reports\handover\VIA_B531_25_ACCELERATOR_CONTROL.ps1
```

若 `via-unique-check` 不是 GREEN，中央入口應停止派送，而不是繞過閘直接執行引擎。若使用檔案 pipeline，應繼續使用 B532 的 `NLP統一 -Pipeline -In 'C:\測試樣本報告'`，並以 VDF coverage gate 的實際結果決定 GREEN、YELLOW 或 BLOCKED。

## 七、交接順序

下一位 AI 應先讀本報告、機器狀態 JSON 與 dispatch JSON，再讀 `VIA_UNIQUE_ENTRY_CONTROL_latest.json`。若需確認中央冊，讀 `VIA_InputConsole_Spec_v0100.json`、`VIA_Workflow_SSOT_v0100.json`、`VIA_ToolRoster_SSOT_v0100.json` 與 `VIA_Component_Inventory_SSOT_v0100.json`。若需確認政策，讀 `VIA_QuantGuard_TA_Lib_Policy_v0100.json`。不要把未掛載的 Windows 真檔、停止中的補庫或 optional SuperAccel 缺件寫成已完成。

## References

[1]: ../../entry/VIA_UNIQUE_ENTRY_CONTROL_latest.json "CGC157 unique-entry control report"
[2]: ../../entry/VIA_UNIQUE_ENTRY_DISPATCH_latest.json "CGC157 all-family dispatch evidence"
[3]: ../../iface_runs/BINDING_SYNC_latest.json "CGC054 interface binding sync"
[4]: ../../accelerator/VIA_ACCELERATOR_CONTROL_latest.json "CGC156 accelerator control report"
[5]: ../../../supportive%20modules/registry/VIA_QuantGuard_TA_Lib_Policy_v0100.json "QuantGuard-only policy SSOT"
[6]: ../../../Register-VIA-Commands-v0208.ps1 "VIA PowerShell command book"

Evidence bundle：`evidence_b533_unique_entry/`，包含 13 個實測輸出／JSON／HTML 檔案；`SHA256SUMS.json` 已完成逐檔核對。

**作者：** Manus AI
