# 需求碼順延說明(導入 PR #439 時)

PR #439(`codex/vqg-polars-ssot-20261003`)與側線 `claude/ecstatic-brahmagupta-ec19u9` 從同一基準 `e09994c4` 出發,
各自發了 VCGC-REQ132–134 與 VIA_Requirements_SSOT v0153–v0155 / VIA_VCGC_FunctionInventory_SSOT v0136–v0138。
main 已先收側線的 REQ132(#438)、側線的 REQ133 先登中央編號冊,依「同號異物 → 後到讓位、已發不改」:

| #439 原碼 | 導入後 |
|---|---|
| VCGC-REQ132 VQG Polars 三解與 SSOT 編號、工具強化及車道驗證 | **VCGC-REQ136** |
| VCGC-REQ133 智慧資產候選 SSOT 自動編號註冊管理 | **VCGC-REQ137** |
| VCGC-REQ134 L1 本地 Regex 與同義詞工具整合 | **VCGC-REQ138** |
| VCGC-REQ135 單一引擎 SSOT Regex 同義字自動同步與中央發號 | VCGC-REQ135(不撞,照舊) |

冊版:需求冊 #439 v0153–v0158 → **v0156–v0161**(疊在側線 v0155 上);盤點冊 #439 v0136–v0139 → **v0139–v0142**(疊在側線 v0138 上)。
工作流冊 VIA_Workflow_VCGC_SSOT v0112–v0117 與 VIA_QuantGuard_ToolRisk_SSOT v0100 內的需求碼同步改寫。
本夾的跑測紀錄(*.txt / evidence.json / runs.json …)是 #439 當時的原始證據,**一字不改**;讀到 REQ132–134 請照上表對應。
中央編號(VIA-VCGC-MDL…)在合併後由 CGC_MDL237 重新為 #439 的新檔發號(#439 分支上發的號沒進 main,不算改身分)。
