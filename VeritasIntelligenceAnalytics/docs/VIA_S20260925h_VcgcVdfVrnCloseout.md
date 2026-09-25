# 2026-09-25h · VCGC / VDF / VRN 收尾

工作站 2026-09-25 18:07 實跑。五個回傳碼都是 0：門、VCGC 自測、VDF 自測、VRN 自測、樣本矩陣。自測過是尺沒壞，不是每盞燈都綠。

## 鎖住

| 處 | 結果 |
| --- | --- |
| 橋 | 加速器四系 100%。VDF 網路橋 242/242（這次補 8）。PS 尾版 846/846 |
| VCGC 自測 | v0128 · 37/37 · rc 0 |
| VDF 自測 | v0104 · 31/31 · rc 0。啟動綠。引擎鏈 10 綠 |
| VRN 自測 | v0104 · 27/27 · 本口 rc 0。樣本夾 `C:\` 測試樣本報告 綠 |
| 矩陣 | 105 份 × 7 欄。判對率 425/425。可判率全格 57.8%，扣掉不適用 61.9% |

## 自測過了仍不綠

VDF 對接口仍是 rc 2。邏輯過期：卡書有 `sector_rotation_capital_flow_engine` 樹上不是尾版；無版號三支 `VDF_ENG046_FetchMatrixRegistry`、`VDF_ENG049_FiveDayFetch`、`VDF_MDL007_SSOTResolver`；樹上有、卡書沒有九支（含 `VDF_ENG092_TWFlowsAdjConsensus`、`VDF_MDL004_TWFullMarketEngine`、`VDF_MDL006_FinancialModel`）。工具過期：`VeritasCeleritas.py` 兩份不同，`VeritasAegisNexus.py` 一份。

VRN 矩陣上漲空間整欄零綠。原因是調整表不在（`tw_daily_prices` 缺 39），不是這次鏈沒跑。另有第二顆頭：`functional modules/VRN/output/vrn_reports.duckdb` 與資料家 `vdf_tw_market.duckdb` 都有 `vrn_report_basic`。

VCGC 現況不是全綠：邏輯庫 FAIL 1、落後 6；SSOT 黃 7；中央治理家族 console RED、downward ABSENT、samename ABSENT；安裝核可 BLOCKED_UNITEST；環境復原存證不在。
