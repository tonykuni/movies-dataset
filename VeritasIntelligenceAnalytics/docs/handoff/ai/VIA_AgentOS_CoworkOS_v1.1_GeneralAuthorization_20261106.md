# VIA AgentOS · Claude Cowork 最強版 v1.1 (2026-11-06)

本倉沒有操作員的 Cowork OS 正本(`SUPREME LAW` / `MCP 啟動 · SYNC ALL` / `VIA_PolicySSOT.json` / `VIA_WorkflowLedger.jsonl` 都不在倉內),所以把操作員 2026-11-06 的三項更新**原文入檔**,作為本倉側的授權紀錄;正本請在 Cowork OS 文件照此套用。

## UPDATE · SUPREME LAW 末尾追加

`LAW-6 預授權:GENERAL AUTHORIZATION 範圍內免問即做;範圍外一行 NEED_APPROVAL: 收尾,不停等`

## NEW · 插入於「MCP 啟動 · SYNC ALL」之前

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERAL AUTHORIZATION · 泛用授權(Tony 2026-11-06 簽發)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
適用範圍:
- 所有 VIA 任務(PS/PY/HTML U/I/報告/擷取/治理/文件/記憶)
- 任何「自動完成 / 幫我做完 / 你懂你決定」的泛用任務,不限 VIA
- 本 OS 全段對上述一律生效,無需每次重述

預授權(免問、免等、直接做):
A1 建新版本檔(薄尾)、標 DEPRECATED、產 README/QA/Ledger
A2 沙盒實測、原地執行引擎(cwd=引擎目錄)、Invoke-VCLaunch 真跑
A3 S4~S10 完整迴圈自動修正最多 3 輪
A4 開 HTML U/I、模擬使用者點擊、寫入 QA JSON / Ledger
A5 擷取:快取、增量、斷點續傳、quarantine 寫入、探測矩陣
A6 產生安裝腳本(detect-only)、環境完整性檢查
A7 Delta sync、記憶寫入(限 Validated/Approved)
A8 在 VIA_PolicySSOT.json 末尾 append 新條目(只增)
A9 泛用任務:選最保守、可回滾方案執行,假設寫入 ASSUMED:

仍需明確批准(一行 NEED_APPROVAL: 收尾,其餘車道照跑):
G1 canonical 寫入 / promote(如 V019B、AkShare v0282 DB write)
G2 觸碰保護路徑 dict\VDF\_active、functional modules\VDF
G3 刪除任何檔案、覆寫無備份檔
G4 關機/休眠(維持 30s 對話框機制)、HKLM、Stop-Process 他人 PID
G5 付費外部 API、新增網路出口
G6 修改或移除既有 SSOT 政策條目(只能 append)
G7 任何不可逆、或成本/風險超出前述範圍之動作

模糊時的預設:
- 不問 → 選保守可回滾路徑 → 執行 → CLOSEOUT 列 ASSUMED: 一行
- 同一任務最多出現 1 次 NEED_APPROVAL,集中於末尾,不中途打斷
- 3 輪未過 → RED 交回 + 一行診斷,不硬改

泛用任務的 S4~S10 替代:
- 文件/文字 → S4 一致性檢查、S7 格式/引用驗證、S8 讀者視角走讀
- 資料/表格 → S4 schema+dtype、S7 列數/空值/hash、S8 抽樣目視
- 流程/決策 → S4 依賴 DAG 完整性、S7 Gate 條件、S8 反例測試
其餘步驟不變

授權記錄:本段 SHA256 寫入 VIA_WorkflowLedger.jsonl;Tony 一行「撤回授權」即失效
```

## UPDATE · CLOSEOUT 追加兩行

```
[ASSUMED]          預設假設,每行一條(無則省略)
[NEED_APPROVAL]    僅 G1~G7,一行(無則省略)
```

## 授權記錄

- 本段(GENERAL AUTHORIZATION 原文)SHA-256:`77463f3418e5104286d219dd9a214bcd910d16368457fdc27864064cc3836b26`
- 已追加到 `docs/handoff/ai/VIA_WorkflowLedger.jsonl`(本倉側 · 只增;操作員桌機的同名帳請照 A7 同步)
- 撤回:操作員一行「撤回授權」即失效

## 本倉已照此執行的對照(2026-11-06)

- A1 薄尾新版:SettleAll v0110–v0114 · MCP 伺服器 v0101 · MDL156 v0115 · VAP v0301
- A2 / A4:容器沙盒實測、HTML U/I Chromium 點擊、QA / Ledger 寫入
- G2 守住:本輪沒有改 `functional modules/VDF` 任何檔(雙橋在 VDF 已 100 %)
- G3:只刪了容器自測產生的暫存(VRN/contract · VAP state),沒刪任何倉內已追蹤檔;`git checkout` 還原的 34 支一行釘住件是回到 HEAD bytes

## 操作員同時給的桌機參數(記錄 · 不代改)

- VRN 測試樣本:`C:\測試樣本報告`(RoundAll / Handle-All 的輸入夾)
- VDF 資料範圍:2022 ~ 現在(VDF 擷取 as-of / 期間;屬 G2 保護路徑,本倉不代改 VDF 冊 → 見 CLOSEOUT NEED_APPROVAL)
