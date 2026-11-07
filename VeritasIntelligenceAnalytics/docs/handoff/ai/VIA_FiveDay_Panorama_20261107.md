# 五日全景檢視 2026-11-02 ~ 11-08(由 main 的 168 個提交與本倉收據量出來)

量法:`git log --since=2026-11-02 origin/main`(168 提交 · 18 個 PR 合併)+ 盤點冊 / 功能帳 / 串測 / 交接冊
+ `VIA_WorkflowViz_v0100.py all` 的三表實測。全部是本倉自報值,不是記憶推定。

## 一、每日提交與合併

| 日 | 提交 | 合併的 PR |
|---|---|---|
| 11-02 | 4 | — |
| 11-03 | 16 | — |
| 11-04 | 38 | #587 #588 |
| 11-05 | 19 | #590 #591 #592 #593 #594 |
| 11-06 | 76 | #595 #596 #597 |
| 11-07 | 14 | #598 #599 #600 #601 #602 #603 #604 |
| 11-08 | 1 | #605 |

76 個提交落在 11-06 一天 —— 那天是五系統收尾 + 交接案逐案重跑(209 案)+ 編號鏈,量最大。

## 二、五系統 × 五日(提交數由訊息比對關鍵詞算出;一個提交可能計入多個系統)

| 系統 | 提交 | 五日內主要落地 | 目前燈(自報) |
|---|---|---|---|
| **VCGC** | 132 | 省 Token 全啟用(NLP v0108 鎖冊)· 交接案 209 重跑 · 編號鏈(盤點冊 v0188→v0193)· 需求冊 v0213→v0220 · MCP v0101 啟用 + `.mcp.json` · 串測 test --quick/--full · DesktopFourBlocks v0100 · WorkflowViz v0100 | 串測 GREEN(站 11 · 綠 9 黃 2 紅 0)· 交接閘既有紅照實 |
| **VDF** | 27 | 分階層輸入輸出矩陣 LayerMatrix v0100 · 橋 AST 覆蓋 100%(23/23 加速 · 6/6 網路)· MDL012 五流擷取可 2015-01-01 起增量 | 引擎可運作;真抓要桌機(容器無網、無 curl_cffi/yfinance) |
| **VRN-1** | 4 | 作 VRN-2 備援;容器 clone pull 到 0993c2d(其倉 PR #82) | 只讀;不在本倉 |
| **VRN-2** | 21 | SystemManager v0262(provenance 動詞順序修)· 非個股摘要器 v0310 引擎入倉 · 邏輯冊重建 ENG062 v0113 | 六案「rc 0 標記沒印」仍在;非個股車道等 NON_STOCK_CORE_v0200.py |
| **VQG** | 17 | v0106 → v0107(Codex #600 版本律:四項修正 · 12/12)· export-vap 薄尾 + manifest 指紋 | 站 C-vqg-v0107 綠 |
| **VAP** | 12 | v0301 / v0302(duckdb DATE 欄 · xField · Codex P1 ×2)· 外部 config 實測 /api/catalog | 站 E-vap-allinone-v0302 綠 |

## 三、流程錯誤與根因(五日內真正發生過的,非推測)

| # | 現象 | 根因 | 怎麼解的 |
|---|---|---|---|
| 1 | 桌機貼回三包 ③ 同步被擋 | 14 支未追蹤的舊發布文件擋住 merge | SettleAll v0117:備份移走再重試一次(v0116 一字不動) |
| 2 | Codex #600 指版本律違反 | 已發布的 VQG v0106 / SettleAll v0115 被原地改 | 還原成 main 位元組 → 出 v0107 / v0116 新版號 |
| 3 | 交接案 32 紅 | 舊版案指向已被薄尾蓋掉的模組 · loader 尾版未登 | MDL225 補登 loader · MDL183 v0106 名冊豁免 · 7 案帶理由轉態 |
| 4 | `test --only desktop-four` 匹配 0 站 | `--only` 是**前綴**比對,不是子字串 | 改用完整站 id `C-desktop-four-blocks-v0100` |
| 5 | PR #604 Windows Chromium UAT 紅 | 與 diff 無關(同 job 在 #603 綠)· `page.goto` 10 s 逾時 | 在 PR 說明一次 + 用掉唯一一次重跑 → 綠 |
| 6 | Codex #605 四項(本輪) | `--resume` 只憑段名沿用 · rc 2 當綠 · 壞設定檔被覆寫 · argparse `%` 未轉義 | 指紋閘 ctx · rc 2 一律黃 · 有檔就誠實停 · `%%` |
| 7 | WorkflowViz 第一版 441/933 節點被判成環(本輪) | 會籍關係畫成雙向邊 → `lane→station→family→lane` 必然成環 | 會籍改用 `layer` 欄位;跨車道改畫車道到車道 → 真環只剩 2 |
| 8 | WorkflowViz 第一版重跑會洗掉時序(本輪) | `persist` 覆寫 `metrics_ts.json` 且 DuckDB `DELETE FROM metrics_ts` | 快照與累積庫分開;metrics_ts 只增不刪 + 回歸測 |
| 9 | 環報「705 個節點在環裡」(本輪) | Kahn 把「在環裡」與「在環下游」混成一類 | Tarjan 縮點 → 兩者分開報(真環 2 · 下游 766) |
| 10 | VDF 在非 Windows 建出 `C:\Users\...` 字面資料夾 | VDF ui 的輸出路徑未按平台分支 | 已備份移除並記為 VDF 車道工作項(不代修他系統) |

## 四、WorkflowViz 三表實測矩陣(2026-11-07 容器)

| 車道 | 節點 | 跨車道交接(出) |
|---|---|---|
| VCGC | 854 | → VDF 68 · → VRN-2 12 · → VQG 3 · → VAP 2 |
| VDF | 50 | — |
| VRN-2 | 13 | — |
| VQG | 9 | → VCGC 1 · → VDF 4 |
| VAP | 3 | — |
| VRN-1 | 1 | — |
| UNKNOWN | 3 | — |

燈:GRAY 487(沒收據,照實不猜)· GREEN 379 · YELLOW 59 · RED 8。
真環:`lane:VCGC ⇄ lane:VQG`(VQG 的站用 VCGC 的編號家族;VCGC 的站測 VQG 的家族)——
依 L123 屬「只讀互看 · 各走自己入口」,不是越界。

## 五、五日內沒解決的(照實列,不消失)

| 項 | 車道 | 擋在哪 |
|---|---|---|
| `C:\測試樣本報告` VRN 實測修正到成功 | VRN-2 | 桌機未經 Remote Control 供出資料夾 → 雲端讀不到 |
| 桌機 Downloads 22 條路徑的整合 | VCGC | 同上;其中 4 份本輪已上傳並入倉 |
| 2022-01-01 起真抓落庫 | VDF | 容器無網路;要桌機跑 DesktopFourBlocks ④ |
| 非個股摘要器接 VRN-2 車道 | VRN-2 | 等 `internal/NON_STOCK_CORE_v0200.py` |
| VRN-2 六案「rc 0 標記沒印」 | VRN-2 | 待該車道處理 |
| ChatGPT 分享頁 / Perplexity 專案內容 | — | 登入牆,容器讀回 NO_CONTENT |
