# VRN-2 v0179 驗證紀錄(2026-11-04)

套件 **v0178 不動**(啟動器 v0178 · runtime v0167 · SHA-256 `f6378dcb2210`)· **RoundAll v0135**(`89adba80ba2b`)· **Handle-All v0127**(一行 `eb49448b400f` · 開機行 `bdc04a88a8e2`)。

| 檢查 | 結果 |
|---|---|
| RoundAll v0135 自測 | [PASS] VRN2_RoundAll v0135 --selftest · 111 項 · 不過 0 |
| 新增 108 · 108b · 108c · 108d | ⑥e 提示只在 last_error.txt 在時指它 · `--confirm` 連提示字貼上只記代碼 · 指令單獨一格 · ⑥ 收尾 KPI(正確性 + 速度)|
| PowerShell 7 解析(6 支一行 / 原始檔)| 0 錯 · 一行 = 原始檔雜湊相同 |
| 沙盒端到端(沿用 v0178 沙盒 · 收據 v0178)| repair1 rc 0 · confirm junk rc 0 · tamper rc 0 · 指令格 6 · 收尾頁「這輪的數據」最前兩列 = ⑥ 收尾 KPI · 正確性 / ⑥ 收尾 KPI · 速度(CPU / DRAM) · 提示字貼上 → 黃字忽略 1 行、代碼照記 · 竄改開機檔 → `[RED] boot SHA-256 mismatch - not run` |
| 桌機貼回包重算 KPI | 達標(不符 0):基本資料 708 / 711 · 待人工 3 · 四點 255 / 260 · 待人工 5 · 年度數據 11971 / 11971 · 原文核對 204 / 208 · 待人工 4 |
| 桌機速度 KPI | 收據 2287 秒(2 輪) · 最慢步驟 ⑦ 啟動 VRN-2 344 / ⑪ 獨立驗證(背景 ·  289 / ④ 加速器覆蓋 26 · 沒計時 1508 秒 · 管理器 326.5 秒 · 最慢 輸出冊 243 秒(74%) · CPU 8 核 · 執行緒上限 7 · 可用 RAM 6.8 GB · 忙 22% · 平行 3 路 · ④b 6 段 24 秒(依序 54 秒 · 2.3 倍) · CPU 用滿(執行緒上限 = 核數 − 1) |
| VRN_SystemManager v0261(VRN-2 底座 · 補 VCGC 對接口)| [計] VRN-2 SystemManager v0261(VRN_SystemManager_v0261.py)自測 6/6 · PASS · 鏈 v0261→v0256→v0254→v0253→v0249→v0248→v0245→v0244→v0242→v0239 · ChainShip check MISSING 0(黃 = 桌機才有的冊 · 同前)|
| SUP_MDL753 v0113(DuckDB 2.x)| 自測 PASS(v0112 44 項經包裝 + 2.x 3 項)· VDF_SystemManager 自測經 VCGC rc 0 |
| VCGC registry-sync --apply | [VCGC 元件自動編號冊] APPLIED · 活元件 19353 · 新 17 · 變更 142 · 退役 0 · AST錯 0 · {'class': 660, 'engine': 160, 'environment': 43, 'feature': 150, 'function': 17378, 'module |
| VCGC 編號稽核 | [編號只增稽核] YELLOW · 基準 dbe24e520492 · 列 119547 → 119575(+28) · 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1 |
| VCGC SSOT 全景 | 前 `[SSOT 全景] RED · 上下單向 VCGC → VDF → VRN → SUP · 探針 7(沿用 1)· 46.4s` → 後 `[SSOT 全景] YELLOW · 上下單向 VCGC → VDF → VRN → SUP · 探針 7(沿用 3)· 13.6s` |
| VCGC 交接閘 | `[交接防遺漏] RED · 驗收 RED · {"requirements": 226, "watched_files": 3554, "pending": 217, "reusable": 178, "findings": 359, "f`(結構性 · 見 VIA_FourSystem_KPI_v0179.md §4)|

沒做 / 做不到(照實):MQ-1560 四點要操作員看原圖後親手 `--confirm`;VCGC 交接閘的舊檔測試宣告是 VCGC 線的事;VDF 自報收尾收據要桌機 ActivateVDF;華南投顧報告(背景花)WORD / TXT / IMAGE 讀取要原 PDF 上傳後才能測。
