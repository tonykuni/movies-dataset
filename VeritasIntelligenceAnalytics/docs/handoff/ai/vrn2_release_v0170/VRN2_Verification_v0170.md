# VRN-2 v0170 驗證紀錄(2026-11-02 · Workbench v0105 U/I · ConsensusJoin v0106 共識欄快照補位 · 套件 v0170 · RoundAll v0126 · Handle-All v0118)

## 1. 這輪要解的(操作員 2026-11-02)

「開閘共識欄 · 要有共識資料 · Workbench 面板緊湊 / 字體比頁首略小 / 有底色的字白色 / 矩陣欄寬自動 / 紅黃綠資料驗證燈 · 授權自行完成 VRN-2 收尾」。
同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)仍只由操作員設 —— 本輪**沒有**任何程式代設;「開閘共識欄」用的是**碟上快照補位 + ASOF 寫實標示**。

## 2. 改了什麼(add-only · 引擎 / 管理器 / 驗證器都不動)

| 件 | 內容 |
|---|---|
| VRN2_Workbench_v0105(runtime 新成員)| **動態前版薄尾**:同夾找版號比自己小的最高前版(桌機 = v0104 · 本倉 runtime = v0102;v0103 / v0104 是桌機另一條線加的,原始碼不在本倉 → 不指名、不重寫,前版先渲染、v0105 只做後處理)。CSS 蓋版(面板緊湊 · 面板最大字 17px < 頁首 h1 20px · .pill / .sm-st 實底白字 · 矩陣 table-layout:auto + 表頭 sticky + 緊湊 padding)+ `<main>` 開頭插兩個自包含面板:「資料驗證狀況」(9 列紅黃綠灰燈:原文值核對 · 獨立驗證 · 冪等 · 完成判定 · ⑥e · ⑥f · ⑬b · ⑬ · Combined 共識欄)與「共識資料」(兩家目標價中位數矩陣 · 快照輪次紅底白字 ASOF 徽章)。前版簽章用 inspect 讀(不假設 v0104 跟 v0102 一樣)· 後處理失敗前版頁照出(黃字) |
| VRN2_ConsensusJoin_v0106(runtime 新成員)| v0105 薄尾:**只在「net_deny.gate_closed = True 且 per_code 空」**時,用碟上最新共識快照 `consensus/factset_yfinance_consensus_matrix.csv`(引擎上次成功落盤 · 只讀)補位 per_code;收據寫 `snapshot_reused{asof · source · codes}`,why 開頭「快照補位(ASOF …)」。合規 DENY(VCGC 判定)不補位 · 快照沒有這批代號不補位(原因寫實)· `VIA_VRN2_NO_SNAPSHOT=1` 關掉 · 開閘輪次照舊真抓並蓋掉快照 |
| ActivateVRN-2_v0170(套件)| WORKBENCH 指到 v0105 · CONSENSUS_JOIN_ACTIVE 指到 v0106 · 收據鍵多收 snapshot_reused · 自測多 v0170 段(v0106 鏈改接 run / join · 沒快照誠實不補)· **跳過 v0169 啟動器號**(發行夾 v0169 只換 RoundAll)|
| VRN2_Runtime_v0160 | = v0159 的 198 個成員逐位元組不動 + 上面兩個新模組(200 個成員)|
| VRN2_RoundAll_v0126 | ⑤ 自動修新步 **consensus_snapshot**(閘未開 DENY · per_code 空 · 閘仍關 · 碟上有快照 → 跑 ConsensusJoin v0106 → 重組 Combined → 增量庫 / Workbench 跟著)· 收尾頁負責方:⑥f 列帶「快照補位」→ **提醒**(比「同意閘未開 → 人工」優先)· 自測 93 項 |
| VRN2_HandleAll_v0118 | 指到 v0170 · 整輪 + 閘未開的提問改寫實:「有快照 → 補位(列提醒);沒有 → 留空(列人工)」· 照舊永不代設閘 |

## 3. 測試(全部綠)

| 項目 | 結果 |
|---|---|
| RoundAll v0126 自測 | [PASS] VRN2_RoundAll v0126 --selftest · 93 項 · 不過 0 |
| Workbench v0105 自測 | [GREEN] VRN2_Workbench v0105 自測 全過(10 項)(含:對桌機 13:01 真 v0104 頁的乾跑 —— CSS / 區塊 / 9 燈注入成功 · Combined 空時共識燈誠實紅)|
| ConsensusJoin v0106 自測 | [GREEN] VRN2_ConsensusJoin v0106 自測 全過(11 項) |
| 啟動器 v0170 自測 | [PASS] v0143: v0142 checks + single-instance lock (live / stale / forced / foreign), child limits (env · floor · mapping), ⑫b in-process fallback (missing page  |
| PowerShell 剖析 | pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| e2e(最短一行 · 沙盒含三份原文 + 合成快照)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto 整輪(閘關 · Workbench v0105 面板已渲染)→ repair → 竄改開機檔不執行 · 收尾狀態 {"auto1": {"state": "OPEN", "per_owner": {"VCGC": 8, "VRN-2": 3, "人工": 8}}, "auto2": {"state": "OPEN", "per_owner": {"VCGC": 6, "VRN-2": 3, "人工": 8}}}(VRN-2 3 項 = 沙盒 numpy/scikit 環境令 3 份新 PDF 摘要缺 · 桌機沒這問題 · v0166 起已記錄)|
| DENY → 快照補位(沙盒到不了同意閘 → 邊界實測)| 邊界實測(沙盒樹 · 前版 run 換成桌機 13:01 形狀的 DENY 收據(合成)· 其餘全真程式):補位 6 檔 · ASOF 2026-11-01 · Combined 17 列 · FactSet 中位數 6 · Yahoo 中位數 6 · 收尾列「提醒」 · Workbench ASOF 徽章在;整輪 e2e 裡 Workbench v0105 over v0102 已渲染 |

## 4. 桌機下一步(一行 · 不用先開閘)

直接貼 `vrn2_release_v0170/VRN2_HandleAll_v0118.md` 的最短一行(443 字元)→ auto = **整輪**(新啟動器 v0170 · 約 40 分鐘):
⑥f 被 DENY 後會自動用桌機碟上的 2026-11-01 快照補回 Combined 共識欄(收尾列「提醒」· Workbench 紅底白字標 ASOF)。
要**最新**共識才需要先貼 `$env:VIA_NET_CONSENT = 'YES'; $env:VIA_SCRAPE_CONSENT = 'YES'`(同一個 PowerShell 視窗 · 操作員決定)。
開機檔 `vrn2_release_v0170/VRN2_HandleAll_v0118_boot.txt` SHA-256 `47dd726d9bec` · Handle-All 一行 `3d233d8e8e88` · RoundAll v0126 `174df7b572c0` · 套件 `bb4a7b041035`。

## 5. VRN-2 收尾的終點(不變)

收尾頁 **VRN-2 0 · VCGC 0**;人工項(MQ-1560 四點 H-fd2ea35f 等 · 以收尾頁列的代碼為準)由操作員親手 `--confirm` 記錄後 → **DATA_GAP(只剩資料源)**。
PASS 要外部缺口全消(⑥e VDF rc 2 PARTIAL 與 AAPL 非台股是來源的事)。SSOT 517 件待 VCGC 核號(四系統對等 · VRN-2 只讀等待)。

## 6. 沒做 / 待辦

- 人工確認只有操作員親手打 `--confirm`(AI 不代確認 —— 即使在「授權自行完成收尾」之下,這是操作員 v0165 輪定的規則)。
- 3014TT 四點(第 2 點從句中開始 · 第 1 / 3 點重複)· MQ-1560 OCR 字詞錯(chi players 應為 chip layers)→ 要改摘要器 + 整輪,操作員點頭才做。
- 桌機 Workbench v0103 / v0104 的原始碼在桌機那條線(本倉沒有);v0105 動態接前版,桌機那邊再出新版(≤ v0104)也照接。
