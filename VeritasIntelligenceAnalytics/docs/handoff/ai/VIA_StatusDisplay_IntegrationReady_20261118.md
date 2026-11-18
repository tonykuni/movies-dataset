# VIA 現況顯示 · 整合就緒說明(2026-11-18)

操作員 2026-11-18:「現況顯示功能引擎及展現方式最佳化準備被整合」。
這份是給做整合的人或 AI 看的。現況顯示引擎本身**沒有改任何入口、MCP 門面、收據契約冊、功能盤點冊**;下面列的是接線時要做的事。

## 有什麼

| 家族 | 尾版 | 號 | 做什麼 |
|---|---|---|---|
| `CGC_MDL282_LocalMonitor` | v0102 | VIA-VCGC-MDL1651 | 偵測:十七個區塊 + 管理面覆蓋;延伸偵測有增量快取 |
| `CGC_MDL283_CardMatrixFeedback` | v0103 | VIA-VCGC-MDL1652 | 兩段篩選 · 對帳 · 成功鎖 · 更新回饋 · 卡片與矩陣頁 · 收據 |
| `VIA_UI_WorkPlatform_TemplateLock` | v0101 | (沒有號) | 版面鎖冊;燈上的字四色一律白 |

每一版都是薄尾,前版一字不動。整合說明的機器可讀版:`via-vcgc run CGC_MDL283_CardMatrixFeedback manifest`。

## 怎麼叫

```
via-vcgc run CGC_MDL283_CardMatrixFeedback run --actor claude     # 或 chatgpt;也可設環境變數 VIA_ACTOR
```

- rc:0 綠 · 2 黃 · 1 紅(對帳不符也是 1)· 3 找不到 VIA 夾。
- 程式內呼叫:載家族尾版後 `status(via=None, actor="", budget=300, out=None)`,不印東西,回傳收據 dict(多一個 `rc`)。
- 輸出都在 `VIA_Reports/vcgc`(倉裡已忽略):`STATUS_latest.json` · `WORKPLATFORM_latest.html` · `FEEDBACK_DELTA_latest.txt` · `FEEDBACK_latest.txt` · `FEEDBACK_FULL_latest.jsonl`。

## 收據 `STATUS_latest.json`

共通欄照收據契約:`lamp`(GREEN / YELLOW / RED)· `at` · `version` · `summary`。另有 `lamp_scope`(這盞燈只代表現況偵測的彙總,不是任何系統的業務驗收)·
`host.counts_as_host_run`(不是 Windows 主機就是 false)· `by_class` · `systems` · `groups` · `gaps`(管理面覆蓋仍灰的面向)· `checks` · `ok` · `paths`。

## 接線要做的(都還沒做)

1. **入口**:VCGC 主控台加 `monitor` 動詞 → 呼叫 `status()`,印 `lamp` · `summary` · `next` 三行,回對應 rc。VDF / VRN-2 的 `monitor` 各自做,不經 VCGC。
2. **MCP 唯讀門面**:登一把鍵 `vcgc/status` → `VIA_Reports/vcgc/STATUS_latest.json`(門面尾版是 v0105,加鍵要出 v0106)。
3. **收據契約冊**:VCGC 節加一筆 `status-display`(`lamp_key` lamp · `at_keys` [at, ts] · `required` [lamp, at, version, summary])。
4. **功能盤點冊 · 需求冊 · 工作流冊**:補登這兩個家族;之後跑整輪 `test` 與 `handoff checkpoint`。
5. **其他系統要進同一頁**:各自的管理器把項目寫成項目冊(`items`:section · system · lamp · id · title · detail · ver · at · needs · rollup),用 `--in <檔>` 餵進來;本引擎不讀也不改他系統內部。

## 整合時要留意

- 編號 `VIA-VCGC-MDL1645`–`MDL1652` 是在 #629 這條線上發的,與 gifted-dijkstra 分支已用的號重疊;後併的一方要重編。
- 這條線上還有兩支尾版沒有號:`CGC_MDL140_HandoverConsole_v0108` · `CGC_MDL279_MCPServer_v0105`(現況矩陣把它們報成退步:鎖過的綠變黃)。
- 全部只在容器實跑過;沒有 Windows 主機收據。剪貼簿那段沒在 Windows 上跑過。
- 分流是字樣判別;彙總列不另計靠來源標 `rollup`。來源只有 v0100 / v0101 時照跑,只是彙總列會另算一項。
- 項目層的成功鎖與上一輪快照在 `VIA_Reports/vcgc`,是每台機器各自的;換機器等於第一輪。
