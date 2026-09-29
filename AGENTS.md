# VCGC 接手必讀

適用本倉。操作員授權與本次指令優先；不得從舊對話推定未跑的實測已成功。

1. 第一個專案操作經 VCGC 的 `token`，使用鎖定的 read / slice / digest / etag；讀檔方式見 `CLAUDE.md`。不要改選工具尾版或全量重跑已成功擷取。
2. 接著經同一入口執行 `handoff check`，讀 `VeritasIntelligenceAnalytics/docs/handoff/HANDOFF_latest.json` 的 findings、pending、reusable_successes。RED／YELLOW 先處理差異，不可略過後宣告成功。
3. 新需求加入中央 `VIA_Requirements_SSOT` 與相應 `VIA_Workflow_*_SSOT`；待辦保留 ID、原因、負責者與下一步。未完成項不能因換人、換模型或新對話而消失。
4. 修改開新版；已鎖成功來源維持原樣。每支新 Python 帶既有加速器橋，PowerShell 沿用既有加速模板。不同資料來源保留不同編號，不以相同數值去重。
5. 只重測相依有變的 case。測試必須經 VCGC 並保留實際命令、rc、目標標記、程式／規則 SHA 與日誌。然後註冊、中央編號、SDD 驗證與 `handoff checkpoint`，再更新 GitHub／CI。
6. 交接 GREEN 只是可續接；`closeout_lamp` 與 SDD 才判定驗收。主機 DB、全樣本、OCR 未測時保留未完成；不拿單元測試冒充主機實測。
7. 舊版薄尾仍可能是依賴，未證明無呼叫前不搬走。TA-Lib 禁用。

當前操作與交付說明：`VeritasIntelligenceAnalytics/docs/handoff/README.md`。機器判準的正主：`VIA_Handoff_Continuity_SSOT_v0100.json`，由 `CGC_MDL140_HandoverConsole` 經 VCGC 管理。
