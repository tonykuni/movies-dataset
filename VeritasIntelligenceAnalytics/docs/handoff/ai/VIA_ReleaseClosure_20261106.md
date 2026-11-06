# VIA Release Closure 報告(2026-11-06 · 收尾執行版 · 不擴範圍 · 只寫已驗證的證據)

依操作員「Release Closure Agent」格式;順序 VRN → VDF → VCGC;每一行都有收據或實測來源,沒有的寫「未驗證」。穩定度 = 該系統最近一次完整實測綠站 / 總站。

## 【系統】VRN(VRN-2 主系統 · VRN-1 模組為備援 · 只讀)

| 項 | 內容 |
|---|---|
| 【發現問題】| ① 桌機工作樹停在 main 舊版(VRN_SystemManager v0254 · 分支 v0261),28 支 VRN 舊版檔(ENG062 v0101–0112 · ENG397 v0113–0128 · SystemManager v0152–0153)本機有改、已 `git add`,差異內容尚未取回(v0107 一行會列)② 兆豐 4 份分析師缺(資料源 · 要原文 PDF)③ 非個股車道:v0310 引擎缺 `internal/NON_STOCK_CORE_v0200.py`,hard gate 停(容器實跑確認)|
| 【根因】| ① 桌機 SettleAll 照規矩不合併「真的改了的程式」→ 新版沒進工作樹;② 外部來源沒有(VRN-2 收尾頁已附證據);③ 另一工作階段打包時只給了 engine,核心模組沒隨附(桌機 $HOME 也沒有)|
| 【修正內容】| 收尾頁 DATA_GAP(VRN-2 0 待修 · 資料源 3 · MQ-1560 `--confirm H-fd2ea35f` 已記)· RoundAll v0135 / Handle-All v0127(KPI 行:正確性 + 速度)· 非個股 v0310 引擎入倉 + reuse/vrn2 三支改 VIA 席位轉接(自測 1/4/4 過)· 不改既有商業邏輯 |
| 【UI 優化】| Workbench v0111(窄螢幕 + 寬螢幕鎖定 · 一鍵一行 · 收尾頁自動開);非個股分頁待核心模組到才接(不新增未測功能)|
| 【測試結果】| 容器 RoundAll 111 項自測 PASS;桌機整輪 11-04 PASS → DATA_GAP;非個股 engine selftest **FAIL(hard gate · 缺核心)** |
| 【回歸測試】| 容器 PASS(v0179);桌機 ⑤ status 讀收據 PASS(無新錯)|
| 【穩定度】| 個股車道 95(資料源 3 項非 VRN-2 可控);非個股車道 0(跑不起來)|
| 【九頭龍風險】| PASS:reuse/vrn2 用轉接不複製正本(TableRestorer importlib 轉出)· 版本只增 · 桌機注入橋由 sweep 自己補 |
| 【是否可交付】| 個股車道 **YES(有條件:資料源 3 項外部)**;非個股車道 **NO(等 NON_STOCK_CORE_v0200.py · SHA 92f53d82…)** |
| 【完成度】| 個股 95% · 非個股 60%(引擎 + 三支轉接到位 · 核心缺)|

## 【系統】VDF

| 項 | 內容 |
|---|---|
| 【發現問題】| ① 桌機 `VDF ui` 跑到舊版 v0162 → `AttributeError DB_MOD`(v0155+ 才有)② 日線檔沒有 market / session_index / available_on 三欄(VQG 嚴格綠要)③ 容器全站測:7 站 VDF_SystemManager v0152–v0157 自測 ⑩「前版鏈 v0151 自測紅」· 8 站擷取自測要先有全市場快照(容器無網 / 無 yfinance)|
| 【根因】| ① 桌機工作樹沒同步(同 VRN ①);② 設計缺口(VDF 線);③ 容器環境:無 yfinance / fastparquet / 網路 → 這些站在容器本來就跑不出資料 |
| 【修正內容】| main 另一工作階段 11-04:ENG113 / 115 / 116 v0104 改經 VIA 網路工具(PR #589 轉接漏洞補)· SUP_MDL753 v0113(DuckDB 2.x)· 自測經 VCGC rc 0;本線不改 VDF 檔(對等)|
| 【UI 優化】| VDF 自己的 ui 頁(v0101 容器 6 GREEN);無新增 |
| 【測試結果】| 容器 ui 6 GREEN · 自測 rc 0 PASS;桌機 ④ **未驗證**(舊樹 · 本輪不跑)|
| 【回歸測試】| 容器 PASS;桌機 未驗證 |
| 【穩定度】| 容器 100(ui)· 全站測 VDF 相關站 綠 / 紅 比:見 VCGC_ToolMatrix §5 C 類(紅 15 站全為容器環境 + 前版鏈)|
| 【九頭龍風險】| PASS(本線零改動)|
| 【是否可交付】| **條件 YES**:桌機同步後 ui 綠即可;VQG 嚴格綠要三欄(VDF 線排程)|
| 【完成度】| 85% |

## 【系統】VCGC(含 Agent OS · Graphify · MCP)

| 項 | 內容 |
|---|---|
| 【發現問題】| ① 桌機主控台 rc 1 = 一本小 JSON 壞(行 8 列 1 · 檔名待 v0107 指名)② 容器全站 `test --full` 317 站:綠 252 · 黃 14 · 紅 51(紅:資料 NODATA 20 · 容器環境 24 · VDF 前版鏈 7)③ 交接閘 105 項(57 REQ_CHANGED 黃 · 42 CCWT VRN 舊模組 · 3 ACCEL · 1 UNREG · 1 EVID · 1 STALE)④ Graphify VCGC 那張要 ≥ 6 GB 可用 ⑤ Agent OS 48 項 · 1 錯 = symlink 權限(Windows 環境)|
| 【根因】| ① 桌機 state 冊之一(SubsystemSeat 13 行 416 B 最可疑)被改壞;② 容器沒有桌機的還原點與套件;③ 歷史模組沒宣告測試(逐案補或裁定 · 操作員 10-10 暫緩 manager 案);④ 2 worker 吃 5.2 GB · 1 worker 起始 2.97 GB 仍不夠;⑤ 開發人員模式 |
| 【修正內容】| VQG 入三本冊 + VIA-VCGC-REQ183 · 編號稽核 0/0/0 · 併 main 兩次(MCP Engine v0102 · 主控台 v0192 · 盤點冊 v0185)· MCP 伺服器 MDL279(只讀 · 自測 12/12 · 盤點冊 v0186)· 矩陣三份(工具 · 五系統 · 兩日收尾)· SettleAll v0102 → v0107(50 分 → 2.5 分)|
| 【UI 優化】| 一行 = 1 Click:取檔核 SHA 跑完出收尾頁;Agent OS 儀表板自動開;MCP 用戶端設定一行印出 |
| 【測試結果】| 容器 quick 綠 9 黃 1 紅 0 PASS · full **FAIL(紅 51 · 全為環境 / 資料 / VDF 前版鏈,無 VCGC 程式紅)** · SDD 無紅 · 稽核 0/0/0 |
| 【回歸測試】| 容器 PASS(quick 兩輪一致);桌機 未驗證(舊樹)|
| 【穩定度】| 全站 79(252/317);quick 90 |
| 【九頭龍風險】| PASS:MCP 伺服器與 main 的 MCP Engine 分工明確(用戶端設定 vs 被接伺服器)· 盤點冊撞號取 main 版重登 · 不改他系統正本 |
| 【是否可交付】| **條件 YES**:桌機修壞 JSON + 同步後主控台綠;全站紅 51 要在有套件 / 有網 / 有還原點的桌機重跑才算 |
| 【完成度】| 88% |

## 下一動(最少步驟)
1. 桌機貼 **SettleAll v0107 一行**(1 Click)→ 報告列出 28 支改動差異 + 壞 JSON 檔名 → 你決定提交或還原(1 次決定)→ 再貼一次 → ④ ⑥ 在新樹上跑,MCP 用戶端設定可貼。
2. 上傳 **`VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.zip`**(SHA txt 指的完整包 · `ad7f87c5…`,含 internal/)→ 非個股車道接上 VRN-2 並自測。
3. Graphify VCGC 那張:關掉其他程式 · 可用 ≥ 6 GB 時 `$env:VIA_GRAPHIFY_ONLY='VCGC'` 單跑。
