# VIA WorkOps 擇優功能去重 + 缺口檢視 v0100(2026-08-09)

操作員令:VMT/VTR 已併入(實體 git mv 完成)→ 擇優功能去重 → 全功能缺口檢視補強。
本文為裁定正本(只增不減;變更以新版追加)。

## 一、擇優去重裁定(重疊功能 × 正本歸屬)

| 重疊功能 | 競逐者 | 擇優裁定 | 理由 |
|---|---|---|---|
| 回覆解析 | ENG-029 三層(V/T/K) vs VMT vmt_reply_ingest | **ENG-029 = 狀態判讀正本**;vmt_reply_ingest 專職問卷 overrides(答案→convergence_params 改寫) | ENG-029 輕量、已入 ALL [2b]、實測;VMT 版綁 SuperBOM 問卷流 — 分工不重疊 |
| 確認佇列 UI | WopConfirmQueue(歸戶) vs VMT ConfirmationQueue(回覆收斂) | **兩者皆正本,對象不同**;UI 模式(預選+chips+一鍵)統一設計語言 | 歸戶確認≠回覆確認;合併會混淆學習記憶兩本帳 |
| 三層分流 | 八層路由 AUTO/ASK/QUARANTINE vs VMT 收斂 AUTO/CONFIRMED/ASK/QUARANTINE | **歸戶=八層路由正本;回覆收斂=VMT 正本** | 同構不同物 — 分流哲學共用(能全自動絕不半自動),帳本各自 |
| 流程探勘 | analytics PM4Py+可攜dot vs PMIS fallback SVG vs vmt_process_mining | **analytics = 郵件語料正本**;PMIS SVG=降級路(既接);vmt 版=SuperBOM 事件流專用 | 三源三對象;報表正本可歸檔原則 |
| 排程 | VMT CPM(關鍵路徑) | **唯一,VMT 正本** — 板④頁唯讀消費既接 | 無競逐 |
| 專名詞庫 | org_lexicon(SSOT 萃取 186)vs VTR 五詞庫(人工核准) | **本輪擇優合流**:VTR products/projects(enabled,48 詞)併入 S9 源(lexicon v0101)→ 總 234 名;人名庫刻意排除(常見姓名易誤中);partnumbers 候補 L3 規則源 | VTR 人工核准=高質專名,不用白不用;正本各自留,載入器合流 |
| 事件流 | reply_events.jsonl vs vmt eventstream vs analytics 事件表 | 各自正本(來源不同);週報彙總=消費層 | 事實流不合併,狀態層才彙總 |
| 備份 | ENG-031(本線側車) vs RC backup(產品線) | **兩線各自**;語義同軸(sha+staging-only) | 資料域不同 |
| 詞條治理 | VTR enabled=false 草稿+核准人 vs 命名帳本 approved 永不覆蓋 | **治理原則統一宣告**:人工核准=最高真相、未核准=草稿弱效 — 兩帳本各自執行 | 同一鐵律的兩個實例 |

## 二、全功能缺口檢視(補強狀態)

| 缺口 | 狀態 |
|---|---|
| VTR 詞庫→S9 共享 | ✅ 本輪補強(lexicon v0101) |
| VMT 資料層布建 | ⏳ 操作員端:`via-vmt-init` 實跑(碼齊,板④頁即活) |
| VTR 模型層(修復 3-8 步)+ JS 引擎 | ⏳ 規格齊,候令開工 |
| VTR partnumbers → L3 product_code 規則源 | 候補(料號 regex 自動生成規則) |
| 隱性阻塞偵測(等/卡/未回 詞入控管表狀態) | 候補(MailOps Reconcile 深改) |
| T1/T2/T3 已發留痕狀態機 | 候補(M3 已通,可接寄件備份比對) |
| RC 7 類產品功能(里程碑/結案智能/統一搜尋/保留政策/onboarding) | 候 payload zip 到貨逐模組去重 |
| mega 引擎盤點表 VMT 路徑更新 | 候補(缺席誠實列 missing 不致崩) |
| Gold Set 首輪實測 | ⏳ 操作員端:accuracy template→核對→run |

紅線不變:絕不代寄 · 唯讀 · 編號永不變 · 只增不減 · 人工核准=最高真相。
