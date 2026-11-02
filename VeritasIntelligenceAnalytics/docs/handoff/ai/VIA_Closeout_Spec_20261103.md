# VIA 收尾規格與現況核實 · 2026-11-03(VRN → VDF → VCGC)

> 來源:操作員 2026-11-02 / 11-03 的文字要求(整理自操作員貼回的對話紀錄)+ 另一工作階段的架構審查與 17 項發現 —— 本檔逐條用**真資料**核實後才寫入。
> 核實基準:GitHub main `2aaff8b02ea1`(PR #586 = 本分支 claude/optimistic-goodall-yhalc5 併入)· 桌機貼回包 2026-11-02 15:18(套件 v0170 · RoundAll v0126 · 閘開整輪)。
> 本檔是**規格與待辦正本**,不是已部署。只增不減;四系統對等獨立(政策 L123),VRN 只改 VRN 自己的檔,VDF / VCGC 的事只列不代修。
> 另一工作階段交付的 `VRN2_Consolidation_v0100/v0101`、`ClickStart v0103`、架構審查 HTML **不在 GitHub 任何分支**(全分支掃過)—— 它們是那邊的下載包,本線沒有它們的原始碼,不得假設已存在。

---

## 1. 收尾原則(操作員原文要點)

- **不擴張範圍**:只修缺陷 / 錯誤 / 穩定性 / 測試 / UI 流程 / 防呆;不新增大型功能、不重構、不改商業邏輯。
- **九頭龍風險 = 0**:一個問題變多個、新增特例分支堆疊、流程循環、隱藏依賴、跨系統耦合、可維護性下降 → 停手、標記、改走最小方案。
- **安全**:不傷害引擎與系統;所有變更可回滾、有紀錄;add-only 新版號,前版一字不改。
- **證據**:不猜、不虛報;所有結論來自實際測試;REVIEW / BLOCKED / DATA_GAP 都不是成功。
- **收尾順序**:VRN(現行收尾中 · 對外顯示一律 **VRN**,檔名 / 版號 / 資料鍵照舊 VRN2)→ VDF → VCGC;一次只動一個系統。
- **UI 目標**:最少必要輸入、≤ 3 次點擊、最快完成;矩陣 / 卡片式結構化,不要散亂文字;資料不可超出格子(自動換行 / 自動調高)。

## 2. 系統關係(核實後的寫法)

| 系統 | 獨立執行 | 本地持有 | 與 VCGC 的契約 |
|---|---|---|---|
| **VRN**(Veritas ReportNova · 原 VRN-2;VRN-1 已併入,不再是可選系統)| 報告輸入 · 解析 · OCR · 財務核對 · 摘要 · 輸出 | 自己的 Main / SystemManager / SSOT·Regex·同義字**候選**與已核准快照 / 資料庫 / 日誌 | 送提案(ssot_id 留空);收 VCGC 核發的號與衝突裁定 |
| **VDF**(Veritas DataForge)| 官方市場 / 財務 / 共識擷取 · 轉換 · 增量庫 | 同上(自己的一套)| 同上 |
| **VCGC**(Veritas Central Governance Console)| 環境 / 工具安裝治理(InstallGate · 工具鎖冊)· 衝突檢查 · **唯一正式編號** · 政策版本 · 稽核 | 中央正本帳冊 · 工具鎖版 | 無衝突才發號;有衝突列待裁定;不直接覆寫運行中子系統 |
| VAP Gate | 保留入口(左欄第三)| — | 缺件顯示「未安裝」,不放無效按鈕 |

更正(避免錯誤寫進規格):
- 「同一套帳」= **同一治理帳冊**(編號 · 政策 · 工具版本),**不是**已實作的共同登入(SSO)—— 沒有證據顯示 SSO 存在。
- 子系統**仍有**自己的領域規則與候選;VCGC 負責共用正本、去衝突、正式發號。不另立 `CFG-000001` 之類新編號體系,沿用 VCGC 既有 AutoCode / Component Inventory 規則。
- 左欄 Gate 順序:**VCGC Gate → VDF Gate → VAP Gate**(語音轉錄的「VC Juicy Gate」= VCGC Gate)。
- 顯示標籤 Title Case、底線改空格;縮寫(VCGC / VDF / VRN / VAP / PDF / EPS / ROE)保持大寫;只改顯示,不改 JSON 欄名 / 函式名 / 版號 / 註冊 ID。

## 3. 網路工具與加速器(核實)

- 桌機 15:18 實跑:⑥f `def Net tool : SUP_MDL740_NetUnified_v0119 · 閘 開 · 加速器 VIA_SuperAccel_Module · VeritasCeleritas_v1141` —— 共識引擎 v0122 確實經 NetUnified v0119;底層核心由 VCGC 工具鎖冊指定(Aegis v1652)。
- **仍待證**:「所有向外擷取的引擎都經網路工具」—— VRN2_MarketFetch v0112 屬共用 / VDF 線工具(VRN 只讀不改),原碼有非拒絕錯誤時的 standalone 直連支路;要 100% 需每個外連動詞的執行收據。這是 VDF / VCGC 階段的事,VRN 不代修。
- 加速器:「未覆蓋 0」是**掛橋標記**覆蓋,不等於每個動詞實際呼叫加速 API,也不等於加速效果。三個指標分開報。

## 4. VRN 現況(15:18 真資料)

| 項目 | 結果 |
|---|---|
| 收尾 | REVIEW · **VRN 0 · VCGC 0** · 人工 1(MQ-1560 四點 · `--confirm H-fd2ea35f`)· 資料源 3 |
| 輸出冊 | FinancialData 11,905 · BasicInfo 52 · Summary 52 · Rejected 2,508 · 冪等 GREEN · ⑪ 錯值 0(PRESENT 101 = 值存在、未強定位期間欄)|
| 共識 | ⑥f 真抓 41/41(404 的 4171 / 6933 依規則排除)· Combined FactSet 中位數 49/52 · Yahoo 48/52 |
| U/I | Workbench v0105(動態前版尾 · 桌機接 v0104)已上線 |
| 尚未過 | 歷史對齊:47 份無歷史 · 覆蓋 0 格 · 512 項檢驗不過 6 · 口徑不明 9 |
| 輸入格式 | Word 7 · TXT 1 · 影像 201 已收下,**主體只擷取 PDF**(收據明寫)|

## 5. 另一工作階段的發現 · 逐條核實

| # | 發現 | 核實 | 負責 | 最小修法(未做 · 待下一輪)|
|---|---|---|---|---|
| F1 | HistoryAlign 的 FinancialAligned **Parquet 沒寫出**(`ArrowInvalid`)| **屬實**。`VRN2_HistoryAlign_v0100._write_books` 把 `None` 換成 `""`,同欄其他列是數字 → 同欄混型 → pyarrow 拒寫;CSV / JSON 正常 11,905 列 | VRN | HistoryAlign 薄尾:空值保留 null、真混型欄才轉字串;前版不動 |
| F2 | Combined `UPSIDE_PCT(ADJ)` 存百分數(`46.0`)不是小數(`0.46`)| **屬實**:42 筆有值,39 筆 \|值\| > 1.5 | VRN | **不能直接改語意**:增量庫已累積舊列,同欄混兩種刻度 = 資料錯。要嗎新增小數欄(例 `UPSIDE_ADJ`)、舊欄照舊並標註;要嗎全庫一次遷移 —— 操作員決定 |
| F3 | Basic Info `NAME` 23/52、`ADJ_CLOSE` 0/52,Combined 51/52 | **屬實** | VRN | Basic Info 是「原文照抄」冊,Combined 是合併冊;U/I 的 Basic 頁改讀 Combined 的已合併欄並標來源(不改冊的語意)|
| F4 | HTML「刪除勾選者」未接後端;拖曳輸入改提示用檔案框 | 需看桌機 Workbench v0104(另一線碼)· 本線 v0102 / v0105 的按鈕走 `vrn2://` 處理器 | VRN | 下一輪實測 v0105 頁 + 處理器 v0110 的 integrate / pick 動作後定 |
| F5 | HTML 匯出下載的是 `.catalog.json` 指標,不是 Parquet 檔 | 待核(頁面行為)| VRN | 同 F4 |
| F6 | 兩線同版號不同內容 · v0169 發行清單雜湊不符 FreezeLock v0103 | 前半已在 v0171 輪處理(合併 main · 本線版號跳開:RoundAll v0127+ · Handle-All v0119+)· 後半是另一線檔 | 另一線 | 不改另一線的檔;本線新版號先查兩邊 |
| F7 | PR #558 / #557 / #555 / #379 / #12 仍開著 | **屬實**(open)| VDF / VCGC / 舊線 | 四系統互不干涉:VRN 不動 |
| F8 | SSOT 500 項待核號 | **屬實**(15:18:待核號 500 · 提案 17 · 自撞 0)| VCGC | VRN 只讀等待 |

## 6. VRN 的 U/I 輸入規格(操作員原文 · 範圍內)

唯一必要輸入:Windows 選檔 / 選資料夾,或拖曳 → 自動生成 Input List:
- 候選分群(只標候選、不自動刪):① 同格式 + **完全相同 bytes**;② 名稱相似 + 同報告日期;③ 同個股 + 券商 + 日期 / 標題。候選群再算 SHA-256,同雜湊才標「完全相同」。
- 點檔名 = 用 Windows 關聯程式開(PDF / Word / 影像),只開清單內登記過的檔。
- Select All / Deselect All / Delete Selected(移出本輪清單,不刪來源檔)/ Confirm Input List → **Start** 一次跑完。
- 輸出正本 **Parquet**(DuckDB 管理);CSV(UTF-8 BOM · 防公式注入)/ JSON / Google Sheets 只在獨立的 Database Export 頁產生。
- 右欄卡片:`min-width:0` · `height:auto` · `overflow-wrap:anywhere` · 寬表只在表格容器內橫捲;1920 / 1366 / 768 / 390 寬與 125% / 150% 縮放都不溢出。
- 範圍界線:XLSX / CSV / JSON **不是**研報擷取的預設輸入;Word / TXT / 影像要有經驗證的適配器才列「支援」,現在誠實列「收下未擷取」。

## 7. Auto Deploy(規劃 · VCGC 階段)

新機預設 `C:\VeritasIntelligenceAnalytics\`,可用 Windows Folder Picker 改位置;installation manifest 記實際根目錄,程式一律相對解析(不寫死 `C:\Users\tonyk`)。**不搬動**操作員現有的 OneDrive / GitHub / Downloads 系統。

## 8. 收尾佇列(依序 · 每階段全 PASS 才進下一個)

1. **VRN P0**:F1(Parquet 混型)· F2(上漲空間刻度 · 待操作員選遷移方式)· F3(U/I Basic 頁讀合併欄)· MQ-1560 `--confirm`(操作員)。
2. **VRN P1**:F4 / F5 實測後修 · 歷史對齊 6 不過 / 9 口徑不明 · Input List 規格(§6)缺的部分。
3. **VDF**:外連動詞 100% 經網路工具的執行收據 · 增量庫 · 桌機倉同步(main `VRN2_Handover_latest.md` 第 13 節 SettleAll v0101)。
4. **VCGC**:SSOT 核號(500 待核)· 工具 / 環境治理 · Auto Deploy · 衝突裁定。

## 9. 操作員規則(持續有效 · 本檔重申)

- 同意閘 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 只由操作員設;任何腳本 / AI 不代設、不繞道。
- 人工核對只有操作員親手打 `--confirm` 才算。
- 安裝經 VCGC InstallGate;InstallGate 只能 `pip --user` 進主 Python 的工具(例 Graphify 這種相依很多的第三方 CLI)走隔離 venv,前後核對主 Python 套件清單不變,並在收據寫明。
- 不推使用者資料 / 原文數值進倉,只寫結論與筆數。

## 10. v0172 輪更新(2026-11-03 · 只增 · 上面各節原文不動)

| 項目 | 狀態 |
|---|---|
| F1 Parquet 混型 | **已修**:`VRN2_HistoryAlign_v0103`(前版照寫 · 沒寫成才依欄位型別重寫 · 讀回比對)· 沙盒:前版 ArrowInvalid → 型別版寫成 · 細節見 `vrn2_release_v0172/VRN2_Verification_v0172.md` |
| F2 上漲空間刻度 | **已修(操作員選「新增小數欄 · 舊欄保留並標註」)**:`VRN2_ConsensusJoin_v0107` 新增 `UPSIDE_ADJ`(純小數)緊接 `UPSIDE_PCT(ADJ)`(百分數 · 保留)· `output/VRN2_Combined_columns_latest.json` 標註 · 增量庫加欄(舊列 NULL)|
| F3 Basic 頁讀合併欄 | **已修**:`VRN2_Workbench_v0107`「Basic Info · 合併檢視」(原文標「原」· Combined 補上標「合」+ 來源 · 兩冊不改)|
| 桌機要做 | 貼 `vrn2_release_v0172/VRN2_HandleAll_v0120.md` 最短一行(收據 ≥ v0170 → repair · 幾分鐘)· MQ-1560 `--confirm`(操作員)|
| ClickStart(另一線)| 3221225786 = 0xC000013A(STATUS_CONTROL_C_EXIT · 視窗被關 / Ctrl+C)· 另一線 v0103 的根因是 venv 父子 PID 不同被誤判逾時 · 內含本線 RoundAll v0127(雜湊相符)· 本線只讀 |
| 非個股摘要器 v0300 | 個股以外的報告(產業 / 晨會 / 總經 / 訊息)屬它;依賴 `NON_STOCK_CORE_v0200` / `reuse/vrn2/` 不在倉 · zip 未上傳 → 本線無法重現;預覽可見品質待修點(行號殘字 · `nan` 點 · 跨公司段落混在一份)→ VRN 之後的階段 |
| Graphify | v0101:根目錄要有系統夾才算 VIA 根(修桌機 4 系統全灰仍印綠)· 一張圖都沒出 → 總結黃 |
| 最嚴格要求 | 操作員 11/03 貼上的 Ultimate Performance Standard → `VIA_Ultimate_Requirements_v0100.md`(UP-0 ~ UP-20 逐條 + 現況 + 負責系統 · 不擴張)|
| 收尾佇列(§8)| 1. VRN P0 → **完成(待桌機 repair 實跑 + 操作員 --confirm)** · 2. VRN P1(F4 / F5 · 歷史對齊 · Input List)· 3. VDF · 4. VCGC 照舊 |
