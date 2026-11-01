# VRN-2 v0156 驗證紀錄(2026-10-31 · 共識引擎經 VIA 網路工具 + 加速器出網 · 套件 v0156 · RoundAll v0112 · Handle-All v0104)

## 1. 要求

操作員 2026-10-31:「新版有版本號 · 加速器跟網路工具最新版都有版本號 · 直接透過 VCGC 的環境工具管理引擎下載所有不足工具及環境並確認無衝突 · 改成經網路工具和加速器出網再抓」
(上傳 `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py` · `VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0111.py`)。

## 2. 做了什麼

| 檔 | 版本 | SHA-256 | 說明 |
|---|---|---|---|
| 共識引擎 Fusion | v0122 | `7eea60fd3019` | v0121(v0120 + 加速器橋)+ 出網一律經 `SUP_MDL740_NetUnified` 最高版號(倉裡 v0119 · 核心鎖冊 AegisNexus v1652):鉅亨 → `http_bytes` · YFinance → `yahoo_quote_summary_raw`;閘關 / DENY = 停,不換道直連;網路工具不在 = `VIA_NET_TOOL_MISSING` |
| 共識引擎 Matrix | v0112 | `573c167d6186` | v0111 + 加速器橋 + 同一套出網改法(交付檔 · 不接進 VRN-2) |
| ConsensusJoin | v0104 | runtime v0156 | v0103 薄尾:requests 探測 · 收據 net_tool / net_deny · 今天的 checkpoint 是直連抓的 + 閘開 → 封存重抓 |
| 啟動器 | v0156 | `75c0bcfe5eec` | 收據 v0156 · ⑥f 用 v0104 |
| RoundAll | v0112 | `5f032bc73f2f` | ⑤ consensus_refresh · 收尾頁 net_deny 負責方 · 除錯列 |
| Handle-All | v0104 | 一行 `986cdad74e65` | ③b 只讀印同意閘 · 指向 RoundAll v0112 |
| 套件 | VRN2_Closeout_v0156.zip | `182bc1486bb4` | runtime v0156 = v0154 的 190 個成員不動 + 引擎 v0122 + ConsensusJoin v0104 |

## 3. VCGC 環境工具(裝缺的 · 查衝突)

```text
[envplan_offline.log]   [快照] Python 3.13.16 · 發行版 98 · pip 衝突 0 條 · 磁碟餘 3.0 GB
[envplan_offline.log]   [快照] EnvManager 母版:導入 OK
[envplan_offline.log]      防:選 camelot=降級(unstructured-client 出衝突);選 unstructured=維持現狀——操作員裁
[envplan_offline.log]      裝:duckdb polars · 由:資料品質查核/高速增量管線——T3/T4/R06/VDF
[envplan_offline.log]      防:duckdb 已在(勿變版!核心庫變版=YELLOW 候裁);polars 原生輪較大
[envplan_offline.log] ── ③ 可行性實測:SKIP(--offline,零網路)──
[installgate_check.log]   [裝前] pip check 衝突 0 條(無衝突 base)
[installgate_check.log]   [裝後] 衝突 0 條 · 新增 0 · 解除 0
[installgate_check.log]   [輔助] Unified:OK · VeritasAegisNexus:OK · VeritasCeleritas:OK · NetSupport:OK · v1:OK
[installgate_duckdb.log] === 安裝治理閘 v0101 · 安裝 duckdb ===
[installgate_duckdb.log]   [裝前] pip check 衝突 0 條(無衝突 base)
[installgate_duckdb.log]   [驗] duckdb 2.0.0 · import OK
[installgate_duckdb.log]   [裝後] 衝突 0 條 · 新增 0 · 解除 0
[installgate_duckdb.log]   [輔助] Unified:OK · VeritasAegisNexus:OK · VeritasCeleritas:OK · NetSupport:OK · v1:OK
```

## 4. 自測

```text
[PASS] 52 收尾頁:共識經 VIA 網路工具被 DENY · 同意閘未開 → 人工(操作員決定 · 不代設)· 合規 DENY → VCGC · Combined 那幾格同樣分
[PASS] 53 同意閘判斷同 VCGC 的 ScrapeGate(YES + YES / 合規 token 才算開 · OFF 不算)· 閘關 → 不排重抓 · 除錯報告寫「共識還沒經 VIA 網路工具 · 操作員決定」
[PASS] 54 ⑤ 自動修:共識是直連引擎抓的 + 同意閘開(替身)→ 經網路工具重抓 ⑥f + 重組 Combined · 閘值不對 → 不排 · 已經經網路工具 → 不排 · 經網路工具的引擎沒跑到出網(缺 requests)→ 不排 · 不列綠
[PASS] 55 除錯報告:共識是經 VIA 網路工具抓的 → 綠列(網路工具版號 · 閘 · 加速器)
[PASS] VRN2_RoundAll v0112 --selftest · 55 項 · 不過 0
[PASS] ① 欄序照操作員清單:目標價 → 調整後目標價 → FactSet / YFinance 中位數 → 2026 / 2027 / 2028 EPS → 2026 / 2027 / 2028 PER → 現價 → 調整後上漲 → 還原收盤 → 主題與摘要 → 狀態
[PASS] ② 代號來自基本資料冊:2330 · 2454 · 9999(去重 · 4 碼)
[PASS] ③ 引擎離線 fixture 實跑:3 代號 · FactSet 中位數 1450 / 1600 · YFinance 中位數 1500 / 1550 · EPS 2026 60 · 2027 75 · 2028 90 · PER 2026 = 1000 / 60 · 收據在 consensus/
[PASS] ④ join:3 列 · 欄序 = 清單 · 2330 調整後目標價 1470.00 · 上漲 45.5 · 還原收盤 1010.50 · NAME 由 VDF 補 · 主題與摘要 = 標題 + 三點(空點略)
[PASS] ⑤ join 共識欄:2330 FactSet 1450.00 · YFinance 1500.00 · 2026 EPS 60.00 · 2028 EPS 90.00 · 2026 PER 16.67 · 2454 2028 空 · 9999 有共識但沒市場 → 調整後目標價空且說缺 · 綠 / 黃
[PASS] ⑥ 輸出:json / csv(+ parquet 有 pyarrow)· 基本資料冊沒動(3 列 · _STATUS 還在)
[PASS] ⑦ VIA_VRN2_NO_CONSENSUS=1 → 灰不跑 · 收據照寫
[PASS] ⑧ 對應表:市場冊 per_ticker → 5274 → 5274.TWO · 2330 → 2330.TW · 壞值不收
[PASS] ⑨ 引擎原本:鉅亨 TWS:5274 → 5274.TW(桌機 404 的根因)· patch 後 → 5274.TWO · 2330 照舊 .TW
[PASS] ① v0101 自測(含 v0100 · 上櫃 .TWO)照過
[PASS] ② 只有 404 頁面不存在的列 → 那幾檔不納入(6933 · 4171)
[PASS] ③ 還有別的不過列(2330 HTTP 500)→ 不動(照 FAIL_CLOSED)· 全部代號都 404 → 不動
[PASS] ④ gate FAIL_CLOSED 只因 404 → 拿掉 6933 · 4171 再跑一次 → 第二次 PASS · 收據記 no_coverage / first_gate
[PASS] ⑤ Combined:沒覆蓋的代號 STATUS 加「鉅亨沒有 FactSet 頁(404)」· 其他列不動
[PASS] ⑥ 啟動器叫的 run / join 與 CLI 的 run / join 都是本版(v0101 · v0100 的模組也指過來)
[PASS] ① v0102 自測(含 v0101 · v0100 · 引擎離線實跑)照過
[PASS] ② 分類:6933 404 = 沒有 FactSet 頁 · 8358 沒有 __NEXT_DATA__ / 2891 連線中斷 = 一時抓不到 · 1234 HTTP 404 / 2330 品質列 = 其他
[PASS] ③ 搬 checkpoint:今天的 [2330,6933,8358] → [2330,8358] 搬 2 份 · 引擎自己的 def_initialize_checkpoint 認它可續跑 · 兩份 payload 讀得回 · 舊的封存
[PASS] ④ 不是今天的 checkpoint → 不搬(照引擎一天一抓)
[PASS] ⑤ 桌機 20:09 重演:404 重試 1 次 → 拿掉 6933 / 4171 再跑 → 8358 / 2891 不再上網(沿用第一次)→ PASS · 綠 · no_coverage 2 · source_gap 0
[PASS] ⑥ 同一劇本給 v0102:第二次清單一變 checkpoint 對不上 → 8358 / 2891 重抓 → FAIL_CLOSED(桌機的樣子 · v0103 才修)
[PASS] ⑦ 一時抓不到:8358 第一次沒有 __NEXT_DATA__ · 第二次有 → 重試 1 次就過閘 · 只重抓 8358 · 綠
[PASS] ⑧ 一直抓不到:2891 抓 3 次(重試 2 次)仍沒有 → source_gap · 拿掉再跑不上網 → PASS 但黃(鉅亨這次沒給)
[PASS] ⑨ 別的不過(HTTP 404 網頁本身不在)→ 不重試、不拿掉 · FAIL_CLOSED 原樣(VRN-2 的事)
[PASS] ① v0103 自測(含 v0102 ~ v0100 · 直連引擎 VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py)照過
[PASS] ② runtime 最高版號的共識引擎經 VIA 網路工具(VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122.py)· 直連引擎留作前版
[PASS] ③ 擷取 Python 檢查:經網路工具的引擎 → 查 requests · 其他呼叫照原樣 · 直連引擎照查 yfinance
[PASS] ⑨ 引擎沒跑到出網那步(擷取環境缺 requests · 沒有「def Net tool」行)→ 不寫 net_tool(不算經網路工具抓過)· net_engine 記引擎名 · why 寫缺 requests 交 VCGC 環境工具
[PASS] ④ 網路工具 DENY:同意閘未開 → net_deny gate_closed · 黃 · why 寫「操作員的決定」· 共識欄清空(這次沒抓)· 合規 DENY → gate_closed False(VCGC 決定)
[PASS] ⑤ 重抓(VIA_VRN2_CONSENSUS_REFRESH=1):今天的 checkpoint 用引擎自己的函式封存 · 檔移走 → 這輪全部經網路工具重抓
[PASS] ⑧ 今天的 checkpoint 是直連引擎抓的(沒有 VRN2_Consensus_NetTool.json)+ 閘開 → 封存 · 經網路工具重抓 · 閘關 → 不封存 · 經網路工具抓過的(記號對得上)→ 照續跑
[PASS] ⑥ 真引擎 + 真網路工具(SUP_MDL740_NetUnified_v0119 · 閘關):開跑前就停 · net_deny gate_closed · 不換道直連
[PASS] ⑦ 啟動器 / CLI 的 run 都是本版(v0103 ~ v0100 的模組都指過來)· join 照 v0103
[PASS] VRN2_ConsensusJoin v0104 --selftest · 不過 0
[VIA 樹外] [SKIP] ⑥ 這個 runtime 夾不在 VIA 樹裡(找不到 supportive modules\network)· 真網路工具那段不跑 · [PASS] VRN2_ConsensusJoin v0104 --selftest · 不過 0
[PASS] v0156: ConsensusJoin v0104 is the active consensus join · engine v0122 (highest in the runtime) goes out through the VIA network tool SUP_MDL740_NetUnified + accelerator bridge · gate closed → 
[PASS] v0154: ConsensusJoin v0103 kept as PRIOR of v0104 (today's payloads resumed on a new code list · 404 / transient retried · still failing → no_coverage / source_gap, out of the gate) · v0102 kep
pwsh 7.4.6 剖析 0 錯 · Handle-All 一行 = 可讀版 · 開機行 = 可讀版(詞序列相同)· 最短一行 0 錯
e2e 結束碼:report rc 0 · auto rc 0 · full rc 0 · tamper rc 0
```

## 5. 引擎經網路工具(本機假伺服器 · 閘用替身擬開 · 真網路工具閘關)

```text
[PASS] VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122 ⓪ 網路工具 = NetUnified 最高版號 · 閘關 · 加速器在 · {"net_tool": "SUP_MDL740_NetUnified_v0119", "gate_open": false, "gate": {"gate1_net_consent": false, "gate2_scrape_token_set": false, "gate1_raw": "(未設)", "scrape_value": "UNSET"}, "accelerator": "VIA_SuperAccel_Module ·
[PASS] VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122 ① 閘關:即時模式開跑前就停(VIA_NET_DENY)· 本機伺服器 0 次請求 · 不換道直連 · VIA_NET_DENY: VIA 網路工具同意閘未開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT · 操作員決定 · 引擎不代設 · 不換道直連)
[PASS] VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122 ② 閘開(替身):鉅亨頁 + 4 個 API 經網路工具 http_bytes 打本機 · Yahoo 經 yahoo_quote_summary_raw · 引擎閘 PASS_WITH_WARNINGS · FactSet 中位數 1450.0 · YFinance 中位數 1500.0 ·  · 請求 ['TWS:2330:STOCK', 'overview']
[PASS] VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122 ③ 輸出:矩陣 CSV · 品質 CSV · HTML · manifest · DuckDB · consensus_checkpoint.json, consensus_checkpoint_payloads, consensus_history.duckdb, consensus_long_current.csv, consensus_long_current.parquet, factset_yfinance_consensus_manifest.json, factset_yfinan
[PASS] VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122 ④ YFinance 分析表(quoteSummary → 同名方法):目標價 · EPS 預估 · 評等摘要 · {"get_analyst_price_targets": true, "get_earnings_estimate": true, "get_revenue_estimate": true, "get_eps_trend": true, "get_eps_revisions": true, "get_growth_estimates": true, "get_recommendations_summary": true}
[PASS] VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122 ⑤ 替身還原後:網路工具照樣 DENY(閘關)· 0 次請求 · {'state': 'DENY', 'note': 'fail-closed:閘一未開(誠實拒絕,零網路)'}
[PASS] VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0112 ⓪ 網路工具 = NetUnified 最高版號 · 閘關 · 加速器在 · {"net_tool": "SUP_MDL740_NetUnified_v0119", "gate_open": false, "gate": {"gate1_net_consent": false, "gate2_scrape_token_set": false, "gate1_raw": "(未設)", "scrape_value": "UNSET"}, "accelerator": "VIA_SuperAccel_Module ·
[PASS] VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0112 ① 閘關:即時模式開跑前就停(VIA_NET_DENY)· 本機伺服器 0 次請求 · 不換道直連 · VIA_NET_DENY: VIA 網路工具同意閘未開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT · 操作員決定 · 引擎不代設 · 不換道直連)
[PASS] VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0112 ② 閘開(替身):鉅亨頁 + 4 個 API 經網路工具 http_bytes 打本機 · Yahoo 經 yahoo_quote_summary_raw · 引擎閘 PASS_WITH_WARNINGS · FactSet 中位數 1450.0 · YFinance 中位數 1500.0 ·  · 請求 ['TWS:2330:STOCK', 'overview']
[PASS] VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0112 ③ 輸出:矩陣 CSV · 品質 CSV · HTML · manifest · factset_yfinance_consensus_manifest.json, factset_yfinance_consensus_matrix.csv, factset_yfinance_consensus_matrix.html, factset_yfinance_consensus_payload.json, factset_yfinance_consensus_quality_mat
[PASS] VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0112 ⑤ 替身還原後:網路工具照樣 DENY(閘關)· 0 次請求 · {'state': 'DENY', 'note': 'fail-closed:閘一未開(誠實拒絕,零網路)'}
[PASS] 共識引擎新版實測 · 不過 0
```

## 6. 最短一行 e2e(沙盒 = 桌機 v0153 狀態 · 倉的網路工具 · 沙盒 GitHub 分支 · pwsh 7.4.6 · 同意閘不設)

```text
[report] [GREEN] boot: Handle-All v0104 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[report] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
[report]   [VCGC] 5 項
[report]   [人工] 2 項
[report] [計] Handle-All 結束 · RoundAll 結束碼 1 · 1 秒(視窗不會關)
[auto] [GREEN] boot: Handle-All v0104 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[auto] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[auto] [計] ④ 自動選模式 repair · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識出網 → 不整輪)(整輪:先貼 $env:VRN2_MODE = 'full')
[auto] [計] ⑤ 自動修計畫:市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)
[auto] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[auto]   [VCGC] 3 項
[auto]   [人工] 2 項
[auto] [計] Handle-All 結束 · RoundAll 結束碼 1 · 3 秒(視窗不會關)
[full] [GREEN] boot: Handle-All v0104 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[full] [計] ④ 模式 full:整輪(取套件 v0156 → 診斷 → 全部自測 → 跑啟動器 v0156(管理器 v0257 · ⑥f ConsensusJoin v0104 · 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)
[full] [YELLOW] ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 via_tw_fetch 缺 yfinance,lxml,pandas,pyarrow,duckdb ; venv_vrn2 缺 yfinance,pyarrow)
[full]   [計] ⑥f 共識合併 · YELLOW · 共識 YELLOW:擷取環境缺 requests(新引擎經 VIA 網路工具 · Yahoo 車道要它 · 交 VCGC 環境工具補)(<v156>/t156a/home/envs/via_tw_fetch/bin/python)→ 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境 · 本輪共識欄留空 · Combined YELLOW:Combined 
[full] [YELLOW] ⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊) · 共識 YELLOW:擷取環境缺 requests(新引擎經 VIA 網路工具 · Yahoo 車道要它 · 交 VCGC 環境工具補)(<v156>/t156a/home/envs/via_tw_fetch/bin/python)→ 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 6 項等 VCGC 決定 / 安裝
[full]   [VCGC] 6 項
[full]     · ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 via_tw_fetch 缺 yfinance,lxml,pandas,pyarrow,duckdb ; venv_vrn2 缺 yfinance,pyarrow)
[full]   [人工] 1 項
[full] [計] Handle-All 結束 · RoundAll 結束碼 2 · 874 秒(視窗不會關)
[tamper] [RED] boot SHA-256 mismatch - not run
```

## 7. 桌機預期

貼 `VRN2_HandleAll_v0104.md` 最上面那行 → ③b 印同意閘 → auto → repair:
閘開 → ⑥f 經 VIA 網路工具重抓 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2**(除錯報告多一列綠的「⑥f 經 VIA 網路工具」);
閘關 → 不重抓 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2**(多「同意閘未開 · 操作員決定」)。
容器做不到:打開操作員的同意閘、連到鉅亨 / Yahoo —— 真的抓要在桌機。
