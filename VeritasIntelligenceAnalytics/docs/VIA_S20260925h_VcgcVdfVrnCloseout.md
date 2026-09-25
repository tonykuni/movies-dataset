# 2026-09-25h · VCGC / VDF / VRN 收尾

操作員裁（2026-09-25）：VDF 目前以個別引擎成功為準，其他擷取器不擋這輪收尾。VRN 實測來源仍是冊上已有的 `C:\` 測試樣本報告夾。FRED 鑰只進這次行程的環境變數，不進倉、不寫進文件。

## 鎖住

| 處 | 燈 |
| --- | --- |
| VDF 政策 / 因子 / 參數 / 橋 / 工具 / 七處 | 綠 |
| VRN 政策 / 邏輯 / 參數 / 同義字 / 紀錄 | 綠 |
| 同意閘 | 工作站那一窗與這次行程都是 NET=YES · SCRAPE=YES |
| FRED 鑰 | 這次行程已設，長度 32。冊上仍是佔位，不把鑰寫回去 |

VDF 其他擷取件（`VDF_MDL004`、`VDF_ENG092`、`VDF_MDL006` 等）依本輪裁定先放下。

## 實測樣本

`VIA_InputConsole_Spec_v0100.json` 的 `user.vrn_dir` 已經是 `C:\` 測試樣本報告夾。這裡看不到那個硬碟，所以燈是 ABSENT，不是路徑設錯。檔數要在工作站那一窗數。

## 仍停

VDF 邏輯仍過期：`sector_rotation_capital_flow_engine` 在 `candidates/`；`VDF_ENG046_FetchMatrixRegistry`、`VDF_ENG049_FiveDayFetch`、`VDF_MDL007_SSOTResolver` 沒有版號。不手改卡書、不代立版號。

兩邊交接仍過期（一頁批715，律冊批2026）。這棵樹不齊，不發佈。

這裡現探缺 pandas、pyarrow。工作站家族境若已有，以那邊 `via-vdfsys launch` 為準。
