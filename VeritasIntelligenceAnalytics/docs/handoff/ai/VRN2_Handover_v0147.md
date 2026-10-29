# VRN-2 交接報告 · ActivateVRN-2 v0146 · 2026-10-29(v0145 + 本輪:桌機 10:25 實跑 v0145 貼回(2546 秒 · CPU 被佔 87.5% → 1 路 · 冪等閘並行有效 151 秒 · ⑬ duckdb 綠)+ 操作員 U/I 與資料需求 + 上傳共識引擎 v0120 → Workbench v0102(雙語表頭 · 靠上 · 百萬台幣千分位 · 自動縮放 · 左欄輸出夾 · 右欄去重矩陣 + 引擎狀態 · logo 180%)· ⑥e 市場擷取(借共用 MarketFetch)· ⑥f 共識 Combined(FactSet / YFinance 中位數 · 真實年度 EPS / PER)· ⑬b 歷史對齊(至少一期對上才覆蓋 · 刪除區)· ⑬c 舊資料庫整合(問使用者 · 原檔不刪)· 處理器 v0109 · SSOTSync v0101 + 提案冊 · 啟動器 v0146 · 操作員一鍵 v0107 · 本地實測一輪改指;runtime v0145 的 167 個成員一個位元組都不動)

> 給下一個 AI 工作階段:先讀本檔,再讀使用者貼回的貼包(結尾 `NEXT:`)與**驗證摘要**(`VIA_Reports\vrn2\verify_independent\*.digest.txt` · ≤150 行)。不要重讀整份程式;要看程式先用省 Token 卡(`read` / `slice` / `chain`)。
> **操作員裁決(2026-10-18)**:「都是獨立系統 · 完成 VRN-2 及收尾 · 自動完成」→ VRN-2 / VCGC / VDF 三系統各自獨立:VRN-2 不寫進別的系統的家族、不經 VCGC 核號、不登 VCGC 中央冊。
> **操作員令(2026-10-19)**:「開閘 授權 + 完成一切測試修正工作 並生成 HTML U/I 上有驗證過的 OUTPUT」。
> **操作員令(2026-10-20)**:「VRN-1 VRN-2 工具可相互取用 · 可驗證性高精準度還原後表格可改為資料庫形式 PIVOT · 兩個系統元主體邏輯不變但各式可以找缺少的工具 · 獨立系統兩個 MAIN」。
> **操作員重申(2026-10-20)**:「重申VCGC VRN-1  VRN-2 VDF皆是獨立系統有獨立的MAIN獨立運作互不影響」→ 工具相互取用只在執行時**讀**對方的工具冊與檔(逐檔核對 sha256),不改、不複製、不寫對方的夾;對方不在 / 沒有工具冊 / 檔換過 → 各自只用自己的工具照常跑完(灰 / 黃,不是紅)。容器實測兩邊各自單獨跑:VRN-2 關掉借用(`VIA_VRN2_NO_BORROW=1`)→ ⑫ 灰「這次不借」· ⑦ 14 / 14 綠 · ⑧ 完成 · ⑪ 錯值 0;VRN-1 那邊關掉借用(`VRN_NO_BORROW=1`)與 VRN-2 不在場各跑一次 19 份真報告 → FAIL 0 · 收尾完成(VRN-2 不在場時 G23 說「VRN-2 在 …,但還沒有工具冊 → 先跑一次 VRN-2 一鍵 v0131 以上」)。
> **操作員令(2026-10-20)**:「用中文回復 一路實測修復到底 TEST DEBUG OPTIMIZE … FACILITATE … USER-TEST … ACTIVATE … TILL THEY WORKS PERFECTLY. 授權全自動完成」。
> **操作員令(2026-10-21)**:「用vcgc的節省token工具來進行工作之後都是:做好啟動系統實測準備善用vcgc節省token工具進行最後一大修,檢查用ActivateVRN-2.ps1啟動前後端並連結讓使用者在html上用window i/o輸入檔案夾或檔案可以為pdf word txt image檔案夾 分為三種 個股報告/訊息 產業報告/展望 其他投資報告 現在進行的是個股報告/訊息其他功能關閉準備好測試無誤後留意是否都有註冊成功並上傳github github有無衝突問題一併解決 下一步換輸入檔案audit"C:\測試樣本報告"」。
> **操作員令(2026-10-21 · 第二段)**:「integrate into one code to handle all above」—— 把 Windows 實跑(`C:\測試樣本報告` · 534 檔 · 個股 55)抓到的事全部整進同一支啟動器,不再靠一鍵補。
> **操作員令(2026-10-22)**:「自動完成VRN-2所有問題 自己測試自完成」+ 上傳 `VRN2_Closeout_v0104.zip`(另一團隊:啟動器 v0140 · 管理器 v0242 · 驗證器 v0109 · 私有 runtime v0140 落 `functional modules\VRN2`)與 `VRN2_VDF_Closeout_v0103.zip`(v0139 前版 + VDF v0115/v0116 · VDF 本輪不碰)+ v0140 在 `C:\測試樣本報告` 的 U/I 貼回(RED 冪等 神達 3706 · 四點原文核對 FAIL 8 / OCR_PENDING 4 · 輸出冊缺項 6 · 獨立驗證 ✗ 45:6933 AMAX 37 · 凱基 2891 8)。
> **操作員令(2026-10-28)**:「回到電腦本地實測修正」+ 貼回 v0136 線的 52 份本地輸出(U/I 完成頁 · Summary / Rejected / FinancialData / Combined / BasicInfo 五本 CSV);「模板視覺鎖定作為前端 html u/i 與後端連棟整合為一個系統 · 透明去背 logo 無框無特效取代模板 logo」+ 上傳 `VIA_VRN-2_Workbench_-_Standalone.html`(印章圖只在對話裡出現,沒有檔案)。
> **操作員令(2026-10-29)**:桌機跑本地實測一輪 v0100(01:33 · 7305 秒)把主控台貼回;「用中文回復 請問 VRN-2 前後端都完成了嗎 CLOSE OUT 了嗎」→ 答:程式完成、驗收未完成、未 close out;「`C:\Users\tonyk\OneDrive\Pictures\seal-logo-square.png` 用一個 PS 取解決上述所有問題」。
> **操作員令(2026-10-29 · 政策)**:「獨立系統 VRN-2 / VDF / VCGC 3 個都是獨立系統 3 個彼此是有依賴性的但不會直接影響他們 … VRN-2 / VDF 此系統端會產生很多的 SSOT REGEX 同義字 政策上有很多規範都是由基層提出來 如 VDF / VRN-2 但有時 VCGC 也有他們的需求可提出 子系統提出後沒有 SSOT ID 空白 另一個子系統也有提 SSOT ID 空白 VCGC 會提示有衝突 等使用者與 AI 修改無誤後自動生成 SSOT 號碼 子系統看到了也會自動填上補全資料 三者靠使用者及 AI 協調 … 三個系統的這類手冊是一致的 三個系統都有自己的 SYSTEM MANAGER SSOT REGEX 同義字 政策庫及 MAIN() 自測至完成 TEST DEBUG OPTIMIZE TEST DEBUG CONSOLIDATE TEST DEBUG USER-TEST DEBUG ACTIVATE TEST DEBUG TILL THEY WORKS PERFECTLY. VRN-2 幾乎完成 快速收尾 用 HTML U/I 去做 輸出位置可用 WINDOWS I/O 拖曳式 或是連接雲端 … 輸出 PARQUET 增量擷取 增量擷取用 DUCKDB 管理 全景式檢視」(原文口述,錯字依語意校正)。
> **操作員令(2026-10-29 · 10:25 貼回後)**:Gemini 對話(台股代號三形式 · ETF 尾碼 · 台北 / 香港電話 · 評等代碼 0 ~ 5 · 目標價同義字 · 分析師職稱)+「HEADER 用空格取代底線 內容全部靠上對齊 數值呈現在 U/I 上都是以百萬台幣為單位 除每股倍數 要有千分位號」+ v0145 整輪主控台(2546 秒)+ 兩張 Workbench 截圖 +「為何字體常爆出格子不會自動調整自動優化嗎 · 左邊 VRN-1 GATE 要有一格輸出檔案夾來存長線資料庫 增量維護一律用 PARQUET · 若使用者已有舊的資料庫(CSV / GOOGLE SHEET)主動提醒要不要進行資料整合 · 整合成功前千萬不要刪掉原有資料 · 自適應式對齊欄位核對後問使用者 · OK 則整合創立並把舊資料放到 TEMP · 一定要擷取歷史資料去做數字對齊 至少有一期要對 然後歷史覆蓋預估 加減法 乘除法檢驗 被歷史數據刪掉的部分放刪除區 · 右面板第一區要有輸入去重矩陣 目前引擎狀態 · 昨天不是可以擷取 TWSE/TPEX/YFINANCE 資料嗎 現在為何不行」→ 再傳 `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py` +「LOGO 理字邊緣留空更少一點點但不可砍到字 然後高畫質放大到 180% 依舊去背透明無框無特效無色」+ 欄名雙語清單(REPORT_DATE:Report Date / 報告日期 …)+「Report Target Price(Adj) / FactSet Target Price Median / YFinance Target Price Median / 2026 ~ 2028 Diluted EPS (FactSet) / 2026 ~ 2028 PER (FactSet) 在 Combined 目標價後面加上 · n 是今年 2026 · 還原真實年分」。
> **本輪(v0146 · 套件 = 啟動器 v0146 + runtime v0146 = v0145 的 167 個成員不動 + 8 個新成員 · 操作員一鍵 v0107 · 本地實測一輪 v0100 改指)**:① **桌機 10:25 判讀**:87.5% busy by another process at launch → launcher chose 平行 1 路 · 優先權 不變;⑦ ≈1180 (擷取 13 · 驗收+摘要 9 · 輸出冊 969 · 冪等閘 151 (R1 73 / R2 78 · parallel works));⑪ 833 秒;④ 93 + 107 (④ / ④b);⑬ duckdb GREEN · 新檔 0 / 已知 52 (incremental proven);⑥c · ⑤b · ⑫b · Workbench v0101 GREEN · 驗證判決寫回;紅燈 same as 08:14: ⑧b rc 1 ← 四點原文核對 FAIL 1 (3014TT-20231005 POINT_3) · 輸出缺項 3 份年度數據 (Daiwa-6278 · 欣銓 3264 · 華南 6143) → needs VRN2_PasteBack_20261029_102505.zip。判讀:the 969 s 輸出冊 is the native second-reader value verification (10,908 values across 52 PDFs) under CPU starvation (1 lane) + OneDrive I/O; not the idempotence gate any more (151 s). 'Why no TWSE/TPEX/YFinance?': the desktop line's own launcher (manager v0249) has ⑥e; this package line never had it → v0146 adds ⑥e / ⑥f. ② **Workbench v0102**(v0101 薄尾):表頭雙語(清單外底線 → 空格 · 原欄名在 title)· th / td 靠上 · 金額欄依列 ITEM / TABLE 判單位 → 百萬台幣 + 千分位(每股 / 倍數 / % 原值 · 滑鼠停留看原值)· 統計磚 clamp + 逐 px 縮(最小 12px 仍不夠就換行)· 左欄「輸出檔案夾 · 長線資料庫(Parquet 增量)」在其他系統 Gate 之上 · 右欄第一區 = 輸入去重矩陣 + 目前引擎狀態(含 ⑥e / ⑥f / ⑬ / ⑬b / ⑬c)· 舊資料庫整合提問 · 歷史對齊表 · 資料冊多 Combined / FinancialAligned / Deleted · logo 以 alpha 內容框重裁(留白 1.5% · 雜訊 alpha 歸零)+ LANCZOS 180%(44 → 79 px · 頁首 100 px)。③ **⑥e 市場擷取**:啟動器跑完 ⑦ 後借共用夾 `functional modules\VRN\VRN2_MarketFetch_v*.py`(桌機線工具 · 只讀 · 最新號)`--fetch` 再 `--fill` → `market\VRN2_Market_latest.json`;共用夾沒有 → 灰;缺 yfinance → 黃交 VCGC;`VIA_VRN2_NO_MARKET=1` 不抓 —— 回答「為何不行」:桌機線自己的管理器 v0249 有 ⑥e,本套件線(v0243 → v0255)從來沒有。④ **⑥f 共識合併**:上傳的引擎 v0120 原樣內附 runtime;VRN2_ConsensusJoin v0100 以基本資料冊 TICKER 跑它(`--skip-unit-tests --allow-missing-duckdb` · 離線 `--fixture` 供測試)→ `consensus\VRN2_Consensus_latest.json` → **Combined 冊**(每份報告一列 · 欄序照操作員雙語清單 · 目標價後接 TARGET_PRICE(ADJ) · FACTSET / YFINANCE 中位數 · 2026 / 2027 / 2028 真實年度 EPS 與 PER · 最後 TOPIC & SUMMARY · STATUS 寫各欄來源 / 缺的原因)。⑤ **⑬b 歷史對齊**(VRN2_HistoryAlign v0100):科目同義字 → 年度期間 → 倍率自動對 → 至少一期對上才覆蓋 → VALUE_FINAL / VALUE_SOURCE / RECON_* · 差 > 3% 進刪除區 · 加減 / 乘除檢驗只報不改 → FinancialAligned / Deleted 兩冊;原三冊不改。⑥ **⑬c 舊資料庫整合**(VRN2_DataIntegrate v0100 + 處理器 v0109 `vrn2://integrate`):掃輸出夾及其上一層 / legacy_in / `VRN2_INTEGRATE_DIRS` 的 CSV / TSV / XLSX(純 zip + xml 讀)/ Parquet / JSON / Google Sheet 匯出 → 同義字 + 內容型態對齊欄位(對不到保留 X_)→ Workbench 問 → apply:VRN-2 冊 ∪ 舊檔去重(同鍵同值去 · 不同值兩邊留標 CONFLICT)→ 新整合檔 json / csv / parquet → 重讀核對 → **原檔絕不刪**,核對過才複製到 TEMP;同內容整合過 / 選過不要的不再問。⑦ **SSOT 提案冊** v0100(9 條 · ssot_id 空白 · VRN2-PROP-xxxx)經 SSOTSync v0101 併進 ⑤b 請求冊。⑧ **啟動器 v0146**:⑥e / ⑥f 在 ⑦ 後、⑬b / ⑬c 在 ⑬ 後;四步都不轉紅(灰 / 黃);收據 `VRN2_Closeout_v0146.json` 多 market / consensus / history_align / integrate;處理器 v0109 · Workbench v0102 · SSOTSync v0101。容器實測:七支自測全 PASS · pwsh 雜湊鏈全 True · 沙盒 19 份:⑧ 完成 · 冪等閘 GREEN · ⑥f YELLOW(13 / 13 代號 · gate PASS_WITH_WARNINGS · Combined 14 列)· ⑬ YELLOW · ⑬c PENDING_USER · Workbench v0102 GREEN(無頭 Chromium 無錯 · 雙語表頭 · 千分位)· 情境 first rc 1 · again rc 1 · tamper rc 1 · done。桌機還沒跑 v0146。
> **操作員令(2026-10-29 · 08:14 貼回後)**:「先把這兩天有更新的部分抓下來再 PC 測試 先不要讓 GITHUB 影響 這是獨立系統」→ 貼回 v0144 整輪主控台 →「ENSURE THE SYSTEM HAS SYNCHRONIZED WITH HTML U/I AND USER CAN USE THE SYSTEM ON IT. IT TAKE LOTS OF TIME TO LAUNCH. IS IT THE FIRST TIME TO LAUNCH SYSTEM OR ACCELERATORS DIDN'T WORK.」
> **前一輪(v0145 · 套件 = 啟動器 v0145 + runtime v0145 = v0144 的 166 個成員不動 + 管理器 v0255 · 操作員一鍵 v0106 · 本地實測一輪 v0100 改指)**:① **桌機 08:14 判讀**:前後端已連結(⑥c vrn2:// → VRN2_UIAction_v0108 read back equal · ⑤b 前後端已連結 GREEN · ⑫b input block GREEN · 驗證過的輸出 written back (fingerprint 9888cecc1a7f291f) · Workbench v0101 GREEN opened · ⑬ duckdb GREEN 52 files · ⑤b SSOT-ID GREEN pending 371);紅燈只有 ⑧b 收尾收據 rc 1 ← ⑧b closeout rc 1 ← 四點原文核對 FAIL 1 (3014TT-20231005 POINT_3 · second reader did not reproduce the complete source excerpt) · 輸出缺項 3 份年度數據 (Daiwa-6278 · 欣銓 3264 · 華南 6143);時間 總 2422 秒 = 啟動器 2401(⑦ 1201 其中無輸出 ~1050 (heartbeat 距上次輸出 1068 秒 before the manager's [計] lines) · ⑪ 691 · ④ 92)+ 一鍵外殼;快取 擷取沿用 52/52 · 驗收沿用 51/52;加速器 VeritasCeleritas v1141 loaded · PS accelerator bound · accelfix 0 missing · 6-way parallel segment 55 s vs 177 s serial → **不是第一次啟動、加速器有生效**;慢的根因判讀:not a first launch; accelerators worked; the silent 1050 s is consistent with the v0243 idempotence gate: 3 兆豐 PDFs × 2 waves in ONE single-lane subprocess per wave, no extraction cache, serial — main extraction itself was all cache hits。② **管理器 v0255**(釘名前版 v0243;v0244 ~ v0254 是桌機線在 `functional modules\VRN` 用掉的號,本線跳過):冪等閘契約不變(同主跑子行程路徑 · 不吃擷取快取 · R1 / R2 / 主跑紀錄三方比對 · GREEN / STALE_RECORD / NONDETERMINISTIC),改成每波**一份一個單路子行程並行**(預設 3 路 · `VRN2_IDEM_LANES`)、R1 跑完才 R2(同一份的 OCR 快取不會被兩次同時寫)、每 30 秒心跳、R1 / R2 / 每份秒數進 `IDEMPOTENCE_latest.json.timing`;把原生流程的 `_resolve("p1loop")` / `acceptance` / `_out_books` / `_out_html` / `_funnel` / 冪等閘包上計時 → 即時印 `[計] 階段 · X · 完成 · 耗時` · 收尾一行 `[計] 階段耗時` · `VIA_Reports\vrn2\VRN2_Phase_Timing_latest.json`;`completion.manager` = v0255。③ **啟動器 v0145**:只改指管理器 v0255 與收據名 `VRN2_Closeout_v0145.json`;⑤b / ⑬ / 處理器 v0108 / Workbench v0101 / 單機閘 / 上限 / ⑫b 補放照舊。④ **一鍵 v0145 / 操作員 v0106 / 本地實測一輪**:⑤ 摘要多印階段耗時;④ 貼回包改收 v0145 收據 + 階段計時,不再把前版收據與(跑完本來就移除的)鎖檔算「缺」;操作員 v0105 歷史子句被連帶改錯的「v0104 → 一鍵 v0144」改回 v0143。容器實測:啟動器 v0145 自測 PASS · 管理器 v0255 自測 PASS(3 路並行 GREEN · 非冪等 RED · 1 路)· pwsh 雜湊鏈全 True · 沙盒 19 份:⑧ 完成 · 管理器 VRN-2 SystemManager v0255 · 冪等閘 GREEN(R1 3.5 秒 3 路 · R2 4.0 秒)· 階段耗時行 [計] 階段耗時(秒)· 擷取迴圈 p1loop 35 · 驗收 + 摘要 61 · 輸出冊 29 · U/I 輸出冊頁 0 · 冪等閘 8 · 調節輪 0 · 其他 1 · 總 133 · 收據 VRN2_Phase_Timing_latest.json · 其餘數字與 v0144 同一組。桌機還沒跑 v0145。
> **前一輪(v0144 · 套件 = 啟動器 v0144 + runtime v0144 = v0142 的 162 個成員不動 + 4 個新成員:處理器 v0108 · OutputStore v0100 · SSOTSync v0100 · Workbench v0101 · 操作員一鍵 v0105 · 本地實測一輪 v0100 改指 · 協定 `VIA_SSOT_ID_Protocol_v0100.md`)**:① **SSOT-ID 三系統協作(VRN-2 側)**:⑤b 讀本輪 `VRN2_Component_Register_v*.json` 尾版 → 寫核號請求冊 `functional modules\VRN2\contract\VRN2_NUMBER_REQUEST_latest.json`(每條目 `ssot_id` 空白 · `proposed_no` = VRN-2 自己的號 · `vcgc_kind` SSOT / RGX / SYN / PLCY / PRMT … · 同義字 · 正則 · 來源檔與 sha · 自撞檢查)→ 讀 VCGC 核發冊 `VCGC_NUMBER_GRANT_latest.json`(依序 `<VRN-2 程式夾>\contract\` · `<VIA>\VCGC\contract\` · `<VIA>\supportive modules\registry\` · `<VIA>\VIA_Reports\vcgc\` · 全部只讀合併)→ 核發 → 自動補填出**新版**登記冊(`v0101` …)· 衝突 → 「衝突 · 待人判」列在收據與 Workbench 交接分頁 · VCGC 還沒核發 → 待核號(綠 · 不擋);VRN-2 不寫 VCGC 的冊、不自己編 SSOT 號。② **輸出位置 window I/O / 雲端**:處理器 v0108 `vrn2://pick?kind=outdir`(Windows 資料夾對話框 · 可新建)· `vrn2://outdir?reset=1` · `--set-outdir`;Workbench v0101 匯出分頁「輸出位置」面板 + 拖曳區(瀏覽器拿不到拖進來的真路徑,拖曳 → 自動開對話框)· 舊版 U/I 左側「輸出位置(window I/O)」區塊;選 OneDrive / Google Drive / Dropbox 的同步夾 = 連接雲端(本機寫入 · 同步軟體上雲 · 收據印 cloud_hint);`$env:VRN2_OUTPUT_DIR` 可預設。③ **⑬ 輸出 Parquet 增量擷取 · DuckDB 管理**:OutputStore v0100 在收尾收據之後跑 → 鏡像四本冊 + Workbench + 收據到 `<輸出夾>\VRN2\latest\`;增量庫 `<輸出夾>\VRN2\vrn2_store.duckdb`(`catalog` 以原檔 SHA-256 為鍵 · `book_<冊>` 每列帶 run_id / file_sha)· 只追加 SHA-256 新檔的列(同檔再跑 = 0 追加)· Parquet 分區 `parquet\<冊>\run=<id>.parquet` + `catalog.parquet`(DuckDB COPY)· 沒裝 duckdb → pyarrow 備援(黃 · 功能同 · 無 SQL)· 沒選輸出夾 → 灰(輸出留 `VIA_Reports\vrn2\output`)。④ 啟動器 v0144 = v0143 + ⑤b + ⑬ + 處理器 v0108 註冊 + Workbench v0101;收據 `VRN2_Closeout_v0144.json` 多 `ssot_sync` / `output_store`。容器實測:五支自測全過(啟動器 · SSOTSync 9/9 · OutputStore 9/9 · 處理器 14/14 · Workbench 18/18)· 沙盒 19 份真檔整輪(⑤b GREEN · ⑬ YELLOW · 引擎 pyarrow · 新檔 14 / 已知 0 · parquet 5)· venv_duck(duckdb 1.5.6)正式路徑:第一次 sync 新檔 14 · 第二次 0 · catalog 14 檔 · SQL 可查 · pwsh 雜湊鏈全 True。桌機還沒跑 v0144(下一次貼回)。
> **前一輪(v0143 · 套件 = 啟動器 v0143 + runtime v0142 不動 · ChainShip v0101 · 操作員一鍵 v0104 · 本地實測一輪 v0100 改指)**:桌機貼回的三個紅:① **ChainShip ② 紅**(check rc 1 → ship rc 2 → check rc 1:ship 推了東西但 v0248 / v0253 仍缺 → 它們不在桌機的 `functional modules\VRN`)→ **ChainShip v0101**:`ship` 先 `recover` —— 每個缺的環在 VIA 樹(含私有 runtime `functional modules\VRN2`、`VIA_Reports\vrn2\backup`)、`--extra` 夾、`Downloads\VRN2_*` 夾與 zip(含套件 zip 內的 runtime zip)找同名檔,內容唯一且語法 / JSON 過才原樣複製進 VRN 夾再推;兩份不同內容只列 `[FIND?]` 不代選;自測 27/27。② **VRN-2 一鍵 rc 1 · ⑤b 紅**:同一 VIA 根**兩個啟動器重疊**(01:35 與 01:58)→ 可用 RAM 0.16 GB → ⑦ 1500 秒無輸出被停(⑦ 黃)、⑪ 1800 秒超時、⑫b `--refresh-ui` 120 秒超時 → U/I 沒輸入區塊 → ⑤b「前後端沒接上」;⑧ 其實完成(紅 0 黃 4)· 冪等 GREEN · 四點原文 PASS 203 / FAIL 1。→ **啟動器 v0143**:單機閘 `VIA_Reports\vrn2\VRN2_Launcher.lock`(另一個 PID 活著就 `[RED] 單機閘` rc 1 不跑;過期鎖接手;`VRN2_FORCE_PARALLEL=1` 強制)· 子行程上限從環境讀、預設放寬(`VRN2_UI_REFRESH_WAIT` 600 · `VRN2_SILENT_MAX` 3600 · `VRN2_MANIFEST_WAIT` 900 · `VIA_VRN2_VERIFY_WAIT` 3600)· ⑫b 子行程失敗 / 超時 → 本支行程內用同一支 `patch_ui` 補放輸入區塊並改綠註明;收據 `VRN2_Closeout_v0143.json` 多 `guard` / `limits` / `ui_block`。③ **① logo 黃**(當時沒指定印章檔)→ 本地實測一輪 ① 候選加 `OneDrive\Pictures\seal-logo-square.png`(已透明的原樣用)。另:操作員一鍵 v0103 橫幅印「v0102」→ v0104 修正並改指 VRN-2 一鍵 v0143。容器:啟動器 v0143 自測 PASS(鎖 活 / 過期 / 強制 / 他人 · 上限 env / 下限 / 對應 · ⑫b 補放 四情境)· 沙盒 19 份全流程(鎖建立 → 結束移除 · 上限生效 · ⑫b 子行程綠 · 結果與 v0142 逐項相同:⑦ 14/14 · ⑧ 紅 0 黃 3 · 冪等 GREEN · 四點 PASS 52 / OCR 4 · ⑪ 錯值 0 · Workbench GREEN)· 單機閘情境(活 PID 鎖 → `[RED] 單機閘` rc 1 什麼都不跑;死 PID 鎖 → 接手)· 一鍵 v0143 情境見 Verification。**沒做的**:桌機 v0248 / v0253 到底在哪只有 recover 跑了才知道(`[FIND]` / `[FIND?]` / `[FIND-]` 三種貼回我判);兩個啟動器為什麼重疊(第二個 01:35 的來源)要 `VRN2_PasteBack_20261029_013350.zip` 的 transcript 才能判,單機閘先把後果擋掉;⑪ 驗證器 v0110 在桌機 52 份要多久沒有乾淨數據(兩次都在搶 RAM)。
> **前一輪(v0142 · 套件 = v0141 + runtime v0142 · 新增 ENG062 v0117 · VRN2_Workbench v0100 + 字型資產包 · 啟動器 v0142 · 一鍵 v0142 · 操作員一鍵 v0103 · v0141 的 159 個 runtime 成員與啟動器底座一個位元組都不動)**:① **貼回的四點品質**:52 份 × 三點裡 87 個沒有句尾(240 字截斷 · 頁首 / 圖註 / 報告類型列當重點 · 標題重複 · 半句開頭),那是 v0114 的切句;v0115 起逐字切句已無截斷,容器 9 份真檔(52 份裡在容器的真檔)v0116 只剩「開頭帶頁首列 / 標題列 / 小標題」→ **ENG062 v0117**:選完後把左緣移過頁首列(`公司 | Asia Pacific`)、標題列(含黏在第一句前的標題)、短小標題(後面接新句);折行的第一個字、介系詞開頭不動;區間 / 引文 / 雜湊重算 · validate_summary 再驗;9 份真檔只改 2 點(GS-6415 2026 P1 · MS-3661 2025 P2),其餘逐字相同。② **Workbench U/I**:範本是 Claude 設計物(x-dc 範本 + 合成資料);版面 CSS / 標記逐字鎖定,{{ 欄位 }} / sc-for / sc-if 在 Python 端用本輪收據與輸出冊展開(完成判定 · 收尾 · 啟動檢查 · 範圍 · 輸入稽核 · 驗收 · 冪等 · 四點原文 · 環境 · BasicInfo / FinancialData / Summary / Rejected · scope_in SHA-256 去重 · backup 快照 · 鎖定);按鈕接 vrn2://;Gate 只開已登記入口;分頁 / 匯出 / 擷取在瀏覽器端;logo 自動去背(白 → 透明 · 去白暈 · 裁框)、無底色 / 圓角 / 陰影;字型 117 個 woff2 隨資產包。③ **啟動器 v0142**:收尾收據寫完 → 渲染 → 舊版 U/I 頁首加「開啟 Workbench」列 → 開 Workbench(退回舊版)。④ 沙盒 19 份:⑦ 14/14 · ⑧ 完成 紅 0 黃 3 · 冪等 GREEN · 四點 {'PASS': 52, 'OCR_PENDING': 4} · Workbench GREEN · 真瀏覽器 Workbench 17/17 / 舊版 U/I 35/35 · 一鍵情境 first rc 1 · again rc 1 · tamper rc 1 · done。⑤ **沒做的**:印章圖沒有檔案(放 `SSOT\VRN2_Logo.png` 即自動去背);矩陣一刪除 / 回收區唯讀;vrn2:// 處理器 v0104 仍重開舊版 U/I(頁首有 Workbench 連結);剔除冊 / 一格多值是桌機線 v0254 的事。
> **前一輪(v0141 · 套件 = v0140 入口 + runtime v0141 · 新增 ENG062 v0116 · 管理器 v0243 · 原文核對 v0104 · 驗證器 v0110 · 交接報告 v0141 · v0140 的 155 個 runtime 成員與啟動器底座 v0136 一個位元組都不動)**:① **冪等 RED**:v0242 的閘拿「主跑紀錄(可能來自擷取快取或子行程)」和「同行程重跑一次」比,不是像對像、也分不出紀錄過期與引擎非冪等;v0243 走主跑同一條子行程路徑(`python -W ignore ENG397 --shard`)重跑**兩次**:全同 GREEN;重跑一致、主跑不同 = STALE_RECORD → 清該檔擷取快取 → 啟動器 v0141 **自動再跑一輪**(`VRN2_NO_REPASS=1` 關);重跑就不同 = NONDETERMINISTIC(RED · 印第一個差異路徑);收據記錄執行環境(python · -I · fitz · PYTHONHASHSEED · 快取夾 · OCR 階梯)。容器 13 份真實多頁檔三條路徑 ×4 次語意差異 0;神達原檔不在容器。② **四點原文核對 FAIL 8 / 缺項 6**:摘要器 v0115 只挑嚴格句,短訊 / bullet / 英文 update 湊不滿 4 點,空點被 v0103 算 FAIL → ENG062 v0116 先跑 v0115,缺的點用階梯補齊(放寬句 → 單行 bullet → 整頁文字行 · 去掉開頭 bullet / 控制字元),每點仍是來源區塊精確字串(頁碼 · 字元區間 · bbox · 雜湊 · evidence.selection 記層級);原文核對 v0104:缺句 = MISSING(rc 2 待核對)、讀不到的 PDF 一列 FAIL、比對忽略 bullet / 控制字元;驗證器 v0110 四點判決多 MISSING。合成 GFHK / 欣銓式 PDF:v0115 0/4 · 1/4 → v0116 4/4 · 4/4(純數字頁仍 MISSING)。③ **備援「複製執行指令」**:v0242 換成只有 PS7 模板(真瀏覽器 3 條不過)→ v0243 回到 v0136 契約(升優先權 → PS 加速器 → PS7 模板 → 實際啟動器 · 不上船版)。④ **✗ 45**:兩份 PDF 不在容器,財務核心 v0105 不動,要原檔或 digest。⑤ 沙盒 19 份:⑦ 14/14 · ⑧ 完成 紅 0 黃 3 · 冪等 GREEN · 四點 {'PASS': 52, 'OCR_PENDING': 4} · ⑪ 錯值 0 · 自癒情境 第 1 輪 STALE_RECORD → 第 2 輪 GREEN · U/I 35 / 35。
> **前一輪(v0136 · 啟動器 + 獨立驗證器 VRN2_IndependentVerifier_v0105 · 交接報告 v0136 · 處理器 / 管理器鏈 / ENG397 / 摘要器 / 工具橋 / OCR 橋一個位元組都不動)**:操作員在 v0135 合併後再令「integrate INTO ONE CODE TO HANDLE ALL ABOVE」。v0135 之後還留著的四件,全部整進同一支啟動器:① **DUPKEY 82**:Windows 那份 ⑪ 的 82 筆同鍵不同值,一行都沒進「貼給 AI」—— 摘要 150 行的上限先被基本資料 25 筆 + BADITEM 吃掉。v0105 摘要改成每一類錯值先各印 6 筆再補滿,而且 DUPKEY 看位置證據:同鍵兩個值裡只有一個對位(ALIGNED / SUBALIGNED / TRANSALIGNED)→ 那筆保留判決、另一筆才是錯值(⑫ PIVOT 只收對位的格,所以對的那筆進得了 PIVOT);都對位 / 都不對位 → 分不出,照舊兩筆都 DUPKEY。② **標籤對調 3 筆**(MS-6669 現價在目標價標籤旁 · GS-2317 目標價旁沒標籤 · 神達上漲空間在目標價標籤旁):v0105 `_swap_hint` 在目標價 / 現價不在自己標籤旁時再看是不是在對方的標籤旁,訊息直接寫「對調」「現價被填成目標價」「可能把目標價當成現價」—— 值仍 FAIL(照實),擷取端下一輪就有明確證據。③ **MS-6669 EPS**(一標題四重點 2025 年 EPS 251.50 不是年度數據的值):v0105 `_eps_ok` 不符時把年度數據同年度那一格印出來(「年度數據 2025 年 EPS 是 EPS (NT$) 2025E=…」),摘要器下一輪就知道該用哪一格。④ **⑫ 要操作員手動 `git switch main; git pull`**:v0136 啟動器 ⑫a 在借工具前自己做 —— 找 VRN-1 的本機倉(VIA_VRN1_ROOT · C:\Users\tonyk\VIA-VDF-VRN · 家目錄 · VIA 倉旁邊),已追蹤的檔沒改動才動:fetch origin main → 不在 main 就 switch main(原分支名印在說明 · `git switch -` 切得回)→ `merge --ff-only`;有改動 / 沒網路 / 分岔 → 不動、照實說,⑫ 照舊。只 fast-forward、不改寫歷史、不提交、不推(四系統各自獨立)。`VIA_VRN2_NO_VRN1_SYNC=1` 不同步。實測:驗證器 v0105 自測 30 / 30(v0105:v0104 的 26 條 + 4 條:DUPKEY 位置證據 · 對調診斷 · EPS 不符印年度數據那一格 · 摘要每類都出現) · 容器同一本冊(14 份 · 4,905 筆):v0104 與 v0105 判決逐類相同(ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 錯值 0 · 冊指紋相同) · 啟動器 啟動器 --selftest 35 / 35(多 1 條:⑫a VRN-1 倉同步 git 夾具 —— feature 落後 1 → 切回 main 並 fast-forward · 改過 → 黃不動 · 關閉 → 灰;內嵌驗證器檢查改認 v0105) · 沙盒樹(19 份 PDF · 個股 14 · 處理器 v0104 · 驗證器 v0105):A1 ②b 綠(檔 19 · 個股 14 · 範圍外 5)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ 錯值 0(v0105 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 年度 4,905)· ⑫a 綠(容器的 VRN-1 clone 原在 claude/optimistic-goodall-yhalc5 → 切回 main 876a4f6 · fast-forward 0 · 原分支名在說明)· ⑫ 綠 4,653/4,905 · ⑫b 綠 · 註冊核對 全部登記成功;P1 U/I 選資料夾(9 檔 → 個股 5)→ ⑦ 5/5 · ⑪ 0;P2 U/I 選檔案 → ⑦ 2/2 · ⑪ 0;產業 / 其他 拒絕 rc 3;audit 綠 —— 與 v0135 同一組數字(無退步) · 沙盒一鍵 v0135(MAIN)→ v0136:一鍵程式碼雜湊相符 · ③ 舊啟動器 v0135 備份 · v0136 就位(雜湊相符)· 啟動器 ①~⑫ 綠(③ 環境檢查紅 = 沙盒 --no-install 仍缺 7 套件 · ② 船包 / ⑥c vrn2:// 灰 = 非 Windows;與 v0135 情境相同)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ v0105 錯值 0 · ⑫a 綠(VRN-1 倉已在 main 最新)· ⑫ 綠 · ⑫b 綠 · 註冊核對 處理器 v0104 · ⑤b 黃(Linux 沒 HKCU)· ⑤c 黃(無瀏覽器)→ NEXT YELLOW rc 2(Windows 應 GREEN · U/I 自己跳出) · Chromium:既有 U/I 35/35 · 輸入區塊 14/14(一鍵情境頁)。
> **v0135( · 啟動器 + 獨立驗證器 VRN2_IndependentVerifier_v0104 · 交接報告 v0135 · 處理器 / 管理器鏈 / ENG397 / 摘要器 / 工具橋 / OCR 橋一個位元組都不動)**:PR #561(v0134)操作員已合併 MAIN,Codex 在合併前後指出驗證器 v0103 兩點:① P1 空值記號(n.a. / NM / -)原文找不到就一律 NILVAL、沒看該格 —— 擷取出 `Revenue = n.a.` 而原文該列該欄印 `12.3` 會從錯值裡消失 → v0104 `_nil_cell`:先定科目列,用同一套表頭對欄(`_align` · 同一個 dx 門檻)看該格印了什麼:數字 → 仍 FAIL(註記「原文該格是數字」)· 空白 / 別的空值記號 → NILVAL · 定不出科目列或這頁沒有這個期間表頭 → 仍 FAIL;② P2 `_num_cands` 把整列空白全去掉再找,「Price target 3 190」會黏成 3190 → 只接「千分位逗點後的空白」「小數點後的空白」(`3, 190.00` · `1, 234. 5`),`3 190` · `12 345` · `Dec 3, 2025` 不黏。PR #562 上 Codex 再指出 P1:科目在這列、值在鄰列(`_row_hits` 支援的版面)時 `_nil_cell` 只看科目列會把下一列的數字當成空白 → `_val_row` 用與 `_row_hits` 同一套規則定值列(鄰列 < 14 pt · 科目欄不是別的科目 · 互為最近;期間表頭字樣不算值)再看該格。三項都只讓驗證器更嚴。已合併 MAIN 的 v0134 一個檔都不改:出 v0135(啟動器 · 發行夾 `vrn2_release_v0135` · 一鍵 · 本交接)。實測:驗證器 v0104 自測 26 / 26(v0104:v0103 的 23 條 + Codex #561 兩條:空白分開的兩個數不黏 · 空值記號看該格 + Codex #562 一條:值在鄰列也看) · 容器同一本冊(14 份 · 4,905 筆):v0102 · v0103 · v0104 判決逐類相同(ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 錯值 0 · 冊指紋相同) · 啟動器 啟動器 --selftest 34 / 34(內嵌驗證器檢查改認 v0104:_nil_cell · _val_row · _SPLITNUM · 自測 rc 0 · 內嵌清單 v0102 / v0103 / v0104) · 沙盒樹(19 份 PDF · 個股 14 · 處理器 v0104 · 驗證器 v0104):A1 ②b 綠(檔 19 · 個股 14 · 範圍外 5)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ 錯值 0(v0104 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 年度 4,905:ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452)· ⑫ 4,653/4,905 · ⑫b 綠 · 註冊核對 全部登記成功(處理器 v0104);P1 U/I 選資料夾(9 檔 → 個股 5)→ ⑥b 5 · ⑦ 5/5 · ⑪ 0(2,214 筆)· ⑫ 2,056/2,214;P2 U/I 選檔案(2 PDF + txt → 暫存夾)→ ⑦ 2/2 · ⑪ 0(848 筆);產業 / 其他 拒絕 rc 3;audit 綠 —— 與 v0134 同一組數字(無退步) · 沙盒一鍵 v0134(MAIN)→ v0135:一鍵程式碼雜湊相符 · ③ 舊啟動器 v0134 備份 · v0135 就位(雜湊相符)· 啟動器 ①~⑫ 綠(③ 環境檢查紅 = 沙盒 --no-install 仍缺 7 套件 · ② 船包 / ⑥c vrn2:// 灰 = 非 Windows;三者與 v0134 情境相同)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ v0104 錯值 0 · ⑫b 綠 · 註冊核對 處理器 v0104 · ⑤b 黃(Linux 沒 HKCU)· ⑤c 黃(無瀏覽器)→ NEXT YELLOW rc 2(Windows 應 GREEN · U/I 自己跳出) · Chromium:既有 U/I 35/35 · 輸入區塊 14/14(一鍵情境頁)。
> **v0134( · 啟動器 + 處理器 VRN2_UIAction_v0104 + 獨立驗證器 VRN2_IndependentVerifier_v0103 · 交接報告 v0134 · 管理器鏈 / ENG397 / 摘要器 / 工具橋 / OCR 橋一個位元組都不動)**:① 處理器 v0104:個股範圍外的檔名規則取**最新版**管理器的 `_SK_EXCL`(Windows 上整條鏈 v0154~v0239 都在,v0103 取到最舊的 v0210;與 ⑥b 用的尾版同一條)。② 驗證器 v0103(⑪ 自動取最新版 · v0102 留著):標籤旁檢查看前 4 頁、一列裡被字距拆開的數字(「3, 190.00」)也對得到(MS / GS 的現價 · 目標價印在第 3 頁或拆字);一標題四重點的「報告上漲空間」原文沒有上漲空間標籤 → 用基本資料目標價 ÷ 現價 − 1 重算相符就過(註記推算 · GS ×5 / 兆豐 / MS-8210 那 7 筆);原文句 / 標題覆蓋率兩邊去標點再量一次取高者(摘要器用「、」接的句子 · 標題的「|」不再被扣分);科目名去 * † $ 括號再比(MS ModelWare「(NT $ mn)」「EPS (NT$)**」那 23 筆 BADITEM);空值記號(n.a. / - / NM)原文找不到 → NILVAL 不算錯值(Daiwa PBR n.a. 那 1 筆)。③ U/I 開不開只認 `--no-open` / `VRN2_NO_UI=1`:VIA 設定檔(Register-VIA-Commands)設的 `VIA_NO_OPEN=1` 是給別的 VIA 工具的,VRN-2 一鍵的目的就是跳出 U/I。④ ⑨ 上船的交接落地改成「不回退」:內嵌的 `VRN2_Handover_v0134.md` 只在倉裡沒有時寫;`VRN2_Handover_latest.md` = 倉裡版號最高那份(Windows 實跑的 ⑨ 曾把內嵌舊版蓋掉 Codex 兩輪與 GitHub 報告連結 → 以後不會)。⑤ 沒動的(照實說):DUPKEY 82 筆(同鍵不同值 · 要看原文兩張表)· 現價 / 目標價旁邊標籤對調的 3 筆 · MS-6669 POINT_2 的 ModelWare EPS —— 是擷取 / 摘要器的下一輪,本輪驗證器不假裝它們過。
> **v0133( · 啟動器 + U/I 處理器 VRN2_UIAction_v0103 · 交接報告 v0133 · 管理器鏈 / ENG397 / 摘要器 / 獨立驗證器 / 工具橋 / OCR 橋一個位元組都不動)**:① 前端 = `VIA_Reports\vrn2\VRN2_UI_latest.html`,後端 = vrn2:// 協定(HKCU)→ 處理器 v0103 → 啟動器;一鍵 ⑤b 檢查兩端有接上(HKCU 的指令解析成 python + 處理器 · 處理器整條路徑 = 本機 VRN-2 程式夾的 v0103 且檔在 · python 檔在 · U/I 有輸入區塊)· ⑤b 的燈併進最後 NEXT(Codex #550 修正)。② U/I 左側新區塊「輸入(window I/O)」:三類 radio(只有 個股報告/訊息 可選;產業報告/展望 · 其他投資報告 disabled「尚未開放」,處理器收到也拒絕)· 📁 選擇檔案夾(`vrn2://pick?kind=folder&cat=stock` → Windows 原生資料夾對話框)· 📄 選擇檔案(`kind=files` → 多選 pdf / docx / doc / txt / png / jpg / jpeg / tif / tiff / bmp → 複製到 `VIA_Reports\vrn2\input_pick\<時間>\`)· 🔎 重新稽核;選好 → 稽核(型別 · 個股範圍 / 範圍外 · 非 PDF)→ `VRN2_Input_latest.json` → 區塊更新 → 重開 U/I → 按「▶ 完整重跑」。③ 啟動器 ②b 輸入來源:`--source`(一鍵 `$env:VRN2_SOURCE`)> 環境 VIA_VRN_INPUT > U/I 選的 > VRN2_SSOT > 預設 `C:\測試樣本報告`;來源不同就寫新一版 VRN2_SSOT(管理器 vrn2scope 讀它,管理器本身不動)。④ ⑥c vrn2:// 寫完讀回核對 · ⑫b ⑦ 重寫 U/I 之後把輸入區塊補回(同一塊不疊加)· 貼包多一行「註冊核對」(⑤ 元件登記 · ⑥c 協定 · ② 定位登記)。⑤ 非 PDF 照實記「已收下 · 本版主體只擷取 PDF」(ENG397 / 管理器 vrn2scope 只收 PDF,本輪不動主體);型別表與 ENG397 的 EXT 逐鍵核對。容器實測:沙盒樹(倉內 19 份 PDF · OCR 隔離環境是真的 · VRN-1 = 本機倉):A1 預設來源 → ②b 綠(檔 19 · 個股 14 · 範圍外 5)· ⑥b 14 · ⑦ 14 / 14 全綠 · ⑧ 完成 · ⑪ 錯值 0 · ⑫ 事實 4653 / 4905 · ⑫b 綠 · 註冊核對 全部登記成功;P1 U/I 選資料夾(掛鉤 · 子集 9 檔 = PDF 6 · Word 1 · TXT 1 · 影像 1)→ 稽核 個股 5 · 範圍外 1 · 非 PDF 3 → 重跑(不帶環境變數)②b「U/I 選的(資料夾)」· VRN2_SSOT 新一版 · ⑥b 範圍夾只剩 5 · ⑦ 5 / 5 · ⑧ 完成 · ⑪ 錯值 0 · ⑫ 2056 / 2214;P2 U/I 選檔案(2 PDF + 1 txt → 複製到 input_pick\<時間>\)→ ②b「U/I 選的(檔案 → 暫存夾)」· ⑦ 2 / 2 · ⑧ 完成 · ⑪ 錯值 0;產業報告/展望 · 其他投資報告 → 處理器拒絕(rc 3);vrn2://audit 重新稽核 綠 · 輸入歷史 6 筆
> **v0132( · 工具橋 VRN2_ToolBridge_v0101 · 交接報告 v0132 · 啟動器流程 ①~⑫ 與 VRN-2 主體一個位元組都不動)**:① 工具橋 v0101:VRN-1 的倉在、那一版沒有工具冊(例:VRN-1 還在 main)→ ⑫ 灰,說明裡印出 `cd <VRN-1 倉>; git fetch origin; git switch claude/optimistic-goodall-yhalc5`(已合併進 main:`git pull`)· 指令放前面、路徑只出現一次(啟動器那一行最多顯示 260 字 —— 第一版放在後面,長路徑時被截在 `git switch claude/opt`,實測抓到、改掉)· sha256 不符 → 印出在 VRN-1 倉跑 `python VRN_Main_v0100.py build`。 ② VRN-1 這邊(另一團隊的倉 · VRN-1 自己的 MAIN):第十四輪(PR tonykuni/VIA-VDF-VRN#79 的 Codex 三條全部成立、全部修掉):科目括號只去單位 / 限定詞(`Turnover (X)` 週轉率 4 筆曾以營收身分進了驗證過的輸出)· 組合段落要同一頁依序的原文片段 · 代號要在代號的位置(檔名獨立一段 / `2330.TW` · `2330 TT` · `(3017)`)· 19 份真報告驗證過的年度數據 1,686 / 1,725(和第十三輪只差那 8 筆)· PIVOT PASS · 收尾完成 · VRN-2 借的 `table.pivot_db` 檔沒變(sha256 `74b97b8bf02d` 相同)。
> **v0131( · 啟動器 + 工具橋 VRN2_ToolBridge_v0100 · 管理器鏈 / ENG397 / 摘要器 / 驗證器 / 處理器一個位元組都不動)**:兩個系統各寫各的工具橋、各有自己的**工具冊**(每支工具的檔 · sha256 · 入口 · 契約 · 能不能用)· 借之前逐檔核對對方工具冊的 sha256(不符 = 不借 · 照實寫)· 只讀對方的檔(不改 · 不複製 · 載入時不寫 __pycache__)· 借不到 = 只用自己的工具(灰 / 黃,不是紅)。① **② 寫 VRN-2 的借出工具冊** `VIA_Reports\vrn2\tools\VRN2_ToolManifest_v0100.json`:`section.near`(段落標題 —— VRN-2 管理器的第三讀法 + v0239 的 `_sec_near`)· `ocr.image`(OCR 隔離環境)。② **⑫ 借 VRN-1 的 PIVOT 資料庫工具**(`table.pivot_db` · VRN-1 工具冊 `<VRN-1 倉>\functional modules\VRN\ssot\VRN_ToolManifest_v0100.json`)→ `VIA_Reports\vrn2\pivot\`:事實表(一格一列)+ 年度 PIVOT(表層 · 報告層)· SQLite 一定有 · DuckDB 有才寫 · CSV · Parquet · HTML · **只收 ⑪ 獨立驗證判對位的格(冊指紋相同才用)** · 同一格兩個不同的證實值 → 格子留空、列進衝突表(不挑)· U/I 最後多一塊「PIVOT 資料庫」連結。③ 容器實測:沙盒樹(倉內 19 份樣本 · 個股 14)連跑兩次:② 借出工具冊綠(`section.near` 能用 · `ocr.image` 容器沒有隔離環境 → 照實標不能用)· ⑦ 綠 · ⑧ 完成 · ⑨ 上船(船包 19 檔 · 含工具橋)· ⑪ 錯值 0(年度數據 4,905 筆:對位 4,378 · 轉置 75 · 子欄 452)· ⑫ 綠:借 VRN-1 `table.pivot_db`(sha256 與 VRN-1 工具冊相同)· 事實 4,653 / 4,905 收進(沒收的 252 筆是空值記號 - / n.a.)· 年度 PIVOT 1,060 列 · 衝突 18(全在報告層:符號慣例 5 · 跨表同名 13 —— 都回原檔看過,是原檔本身兩張表印的不同,不是 VRN-2 讀錯)· 第二次跑指紋相同(冪等)· U/I 只有一塊 PIVOT 連結 · PIVOT 頁 Chromium 實測 29 / 29 · 啟動器自測 27 / 27 · 工具橋自測 14 / 14。VRN-1 工具冊的 sha256 不同時 ⑫ 照實拒借(已實測)。 ④ VRN-1 這邊(另一團隊的倉 · 只讀 · 修改另以 patch 交給操作員):VRN-1 借 VRN-2 的段落標題(G23 · sha256 核對)→ G21 多剔除 39 筆真錯(MS 3661 第 10 頁右表 Growth(%) / Margins (%) 底下 24 筆 · MS 2308 第 6 頁 QoQ / YoY Growth (%) 底下 15 筆:成長率 / 比率被歸成營收 / 營業利益 / 稅前 / 淨利 / EPS 的金額)· VRN-1 自己的 PIVOT 衝突 4 → 0 · 年度數據 1,694 / 1,733 · 收尾完成;不借(VRN_NO_BORROW=1)時這 39 筆仍在證實輸出裡、PIVOT 衝突表列 4 筆(黃燈)—— 所以兩個系統要一起在。
> **v0129(邊測邊修:管理器 v0239 · 獨立驗證器 v0102 · 啟動器邏輯同 v0128)**:操作員令「繼續完成」→ v0128 推上去後繼續把 U/I「驗證過的輸出」逐表看、逐欄稽核 → **凱基 2637 第 5 頁左「財務比率」、右「投資回報率」兩張表並排、同一高度交錯 → 段落標題(SECTION)互相拿錯**:左表 流動比率 / 速動比率 / 淨負債 拿到右表的公式項「1 - 營業成本/營業收入」· 右表 1 / (營業運用資金 … = 稅後 ROIC 拿到左表的「每股資料分析」/「資產運用狀況」· 右表 銷管費用 / 營業利益率 拿到公式項(共 13 列 65 筆 · **值都對** · 驗證器只查值所以沒抓到)→ 管理器 v0239 依科目欄改回(值一個都不動)· 驗證器 v0102 另查段落標題(SECFAIL)。其他欄位(TICKER / BROKER / 日期 / 期間)與基本資料冊逐筆一致 · 科目折行 1 列(完整存放)。
> **v0128(啟動器依紀錄定位 · 邊測邊修:管理器 v0238 · 獨立驗證器 v0101)**:使用者機器 2026-10-19 第一次跑 v0127:先把 PowerShell 程式貼進 cmd(每行被 cmd 拒絕 · 什麼都沒跑)→ 改用 cmd / PowerShell 都能貼的一行(Windows PowerShell 5.1 · 雜湊相符 · 啟動器 v0122 → v0127)→ 啟動器 ② 紅「找不到 VRN-2 程式夾 functional modules\VRN」rc 2(上次成功是 2026-10-18 23:48 的 v0125 · 船包清單 manager_tail v0235 · 程式夾在 VIA 根\functional modules\VRN)。原因:啟動器以前**環境變數 VIA_ROOT 有設就只看它**(容器把 VIA_ROOT 指錯 → 同一句紅燈)· 不看自己的紀錄。**v0128 依 MAIN 登記紀錄定位**:VIA_ROOT · 交接報告的 VIA 根 · 本支所在夾 · 目前夾 · MAIN 成功紀錄的鎖檔路徑 · git 倉裡找;多個候選選本機登記的 MAIN 管理器(檔在且 sha 相同);② 印來源與登記版號 · 找不到印查過的地方。**邊測邊修再找到一類錯**:把 U/I「驗證過的輸出」逐格看一遍 → 3 列**表頭被當數據**(凱基 2637 現金流量表「NT$百萬 Dec-23A …」· JP 2330「Balance Sheet & Cash Flow Statement FY24A …」· GS 6415「Jul-25 Oct-25」· 共 11 筆)· 獨立驗證器 v0100 判對位(表頭字本來就印在期間那一欄)→ 管理器 v0238 把表頭列移剔除冊(帶理由)· 驗證器 v0101 另查值的種類(HDRVAL)· 年度數據 4,916 → 4,905 · 剔除冊 733 → 744 · 錯值 0。
> **本輪(v0127 · 管理器 v0237 · 獨立驗證器 v0100 內嵌)**:① U/I 第一個分頁「**驗證過的輸出**」:每份個股的基本資料 / 一標題四重點 / 年度數據,每格是值 + 驗證徽章(✓✓ = VRN-2 兩讀取器 + 獨立驗證都對位)② 獨立驗證由啟動器 ⑪ 在背景跑(與 ⑧⑨⑩ 同時)· 判決寫回 U/I · **冊指紋相同才套用** · 寫回後才開 U/I ③ **驗證器自己被驗出洞並補上**:v3 只看「值在不在期間那一欄」,別一列的值也會過(反向測試 3,000 筆裡 2,917 筆漏抓)→ v0100 先定「這個科目那一列」再找值(0 / 3,000 漏抓)· 基本資料目標價 / 股價要在自己的標籤旁 · 重點裡的數字對到基本資料 / 年度數據 ④ 新驗證器一掃抓到兩個輸出問題並修好:**凱基財務比率表 13 列整列漏掉**(擷取把「流動比率 (x) 0.6 0.8 …」塞進一格)· **9 對完全重複的列**(季度段與年度段同一個期間字、兩格同值)。

---

## 1. 系統定義

- **VRN-2** = 獨立子系統:MAIN = `ActivateVRN-2.py` → `VRN-2 SystemManager`;自己的 SSOT(`VRN2_SSOT_v####.json`)、自己的 U/I 協定(`vrn2://`)、**自己的上船位置 `docs/handoff/ai/vrn2_ship/`**、**自己的編號(元件登記冊 `VRN2_Component_Register_v####` · `VRN2-<類>-####`)**。
- **與其他系統的界線(獨立)**:`functional modules\VRN` 夾裡 `VRN_SystemManager_v0114–v0153`、`VRN_ENG062_SummarizerV1_v0101–v0103`、`SSOT\VRN_Config_v0100.json` 是 VCGC 側 VRN 的檔(GitHub 上 git 追蹤中)。VRN-2 只讀取(管理器鏈的前版 · 船包清單記相依)· 不改 · 不封存 · 不提交。
- **VRN-1** = 另一團隊(`C:\Users\tonyk\VIA-VDF-VRN`):互相學方法、不照抄程式碼;**v0131 起工具可相互取用**(兩邊各自的工具冊 + sha256 核對 · 只讀對方的檔 · 不複製):VRN-2 借 VRN-1 的 PIVOT 資料庫工具(⑫)· VRN-1 借 VRN-2 的段落標題讀法(`section.near`)與 OCR(`ocr.image`)。兩個系統各有自己的 MAIN(VRN-1 = `VRN_Main_v0100.py` · VRN-2 = `ActivateVRN-2.py`),主體邏輯各自不變。
- **範圍**:只做個股報告 → FILENAME · 首頁(本文 + 資訊區)· 年度財報頁(年度財報及數據分解)· 100% 還原 · 一標題四重點 · 輸出驗證無誤 · U/I 自動跳出且可操作 · **U/I 上看得到驗過的每一個值**。
- **治理**:只增不減 · 成功即鎖、只准變好 · 精準錨點修正 · 不產生九頭龍 · 每版過修正閘 · 漏斗原則 · 每個 PY / PS 指令接加速器 · 指令第一步提高 CPU / DRAM 效能 · 互不相連的步驟同時跑。

---

## 2. 檔案位置(使用者機器)

VIA 根目錄:`C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`(簡稱 `<ROOT>`)

| 類別 | 位置 | 說明 |
|---|---|---|
| **收尾套件(MAIN)** | `C:\Users\tonyk\Downloads\VRN2_Closeout_v0143\`(一鍵 ③ 解壓;`ActivateVRN-2_v0143.py` + 底座 `ActivateVRN-2_v0136.py` + `VRN2_Runtime_v0142.zip/.json` + 橋 + 原文核對 v0104 + OCR 橋 v0101)| **v0142** · 套件雜湊 `fee4d61db2af` · 見 `docs/handoff/ai/vrn2_release_v0142/VRN2_Release_v0142.json` · v0141 / v0104 套件夾留著 |
| **私有 runtime** | `<ROOT>\functional modules\VRN2\` | v0140 起:runtime 清單逐檔雜湊還原(已在且同 = 沿用 · 不同 = 停不覆寫)· v0142 多 3 檔:ENG062 v0117 · VRN2_Workbench_v0100.py · VRN2_Workbench_Assets_v0100.zip(v0141 的 4 檔照舊)· 共用 `functional modules\VRN` 不碰 |
| **收尾收據** | `<ROOT>\VIA_Reports\vrn2\VRN2_Closeout_v0143.json(v0142 的留著)` · `IDEMPOTENCE_latest.json` · `VRN2_VerbatimVerify_latest.json` | rc 0 / 2 / 1 · 每輪(passes)· 冪等分類 · 四點原文核對 · **`workbench`(燈 · 路徑 · 舊版連結)** |
| **單機鎖** | `<ROOT>\VIA_Reports\vrn2\VRN2_Launcher.lock` | v0143:啟動器開始寫(PID · 版本 · 開始時間)、結束移除;另一個啟動器看到活的 PID 就不跑(rc 1);過期鎖接手;`VRN2_FORCE_PARALLEL=1` 強制並行 |
| **補船收據** | `<ROOT>\VIA_Reports\vrn2\VRN2_ChainShip_latest.json` | ChainShip v0101:check / recover / ship(`recover` 欄:copied · ambiguous · absent · rejected)· 不入倉 |
| **Workbench U/I** | `<ROOT>\VIA_Reports\vrn2\VRN2_Workbench_latest.html` + `VRN2_Workbench_assets\`(字型)| 啟動器 v0142 收尾後渲染並開啟;自己跑:`python "functional modules\VRN2\VRN2_Workbench_v0100.py" render --root <ROOT>`;logo:`<ROOT>\functional modules\VRN\SSOT\VRN2_Logo.png`(或 jpg · 自動去背;`logo <in> <out.png>` 可單獨去背)|
| **工具橋** | `<ROOT>\functional modules\VRN\VRN2_ToolBridge_v0101.py` | v0132 落地(v0131 落的 `VRN2_ToolBridge_v0100.py` 照舊留著 · 只增不改)· 借出 `section.near` / `ocr.image` · 借入 VRN-1 `table.pivot_db` · 進船包 |
| **U/I 處理器** | `<ROOT>\functional modules\VRN\VRN2_UIAction_v0104.py` | v0134 落地(v0102 / v0103 照舊留著 · 只增不改)· 檔名規則取最新版管理器 · 其餘同 v0103(`vrn2://pick` · `--set-source` · `--audit <路徑>` · `--refresh-ui`)|
| **獨立驗證器** | `<ROOT>\functional modules\VRN2\VRN2_IndependentVerifier_v0110.py` | v0141 落地(v0102 ~ v0109 留著)· 財務核心 v0105 · 四點判決 PASS / OCR / MISSING / FAIL |
| **輸入紀錄** | `<ROOT>\VIA_Reports\vrn2\VRN2_Input_latest.json`(+ `VRN2_Input_History.jsonl` 只增 · 多檔暫存 `input_pick\<時間>\`) | U/I 選的來源 + 稽核(型別 · 個股範圍 / 範圍外 · 非 PDF)· 啟動器 ②b 讀它當來源夾 · U/I 區塊顯示它 |
| **借出工具冊** | `<ROOT>\VIA_Reports\vrn2\tools\VRN2_ToolManifest_v0100.json` | ② 寫 · ⑫ 之後再寫一次(本輪才建好的 OCR 隔離環境 → `ocr.image` 標能用)· VRN-1 借之前核對 sha256 |
| **PIVOT 資料庫** | `<ROOT>\VIA_Reports\vrn2\pivot\` | ⑫ 寫:`VRN_Pivot_v0100.sqlite`(+ `.duckdb` 有 duckdb 才寫)· `facts` / `pivot_report_annual` / `pivot_annual` / `conflicts` / `precision_merges` 的 CSV + Parquet · `VRN_Pivot_v0100.html` · `VRN2_Pivot_Borrow_latest.json`(借用紀錄:來源 · sha256)|
| **VRN-1 工具冊** | `C:\Users\tonyk\VIA-VDF-VRN\functional modules\VRN\ssot\VRN_ToolManifest_v0100.json` | VRN-1 的 `build` 寫 · **VRN-1 倉 `claude/optimistic-goodall-yhalc5` 分支(PR tonykuni/VIA-VDF-VRN#79)起才有**(沒有 → ⑫ 灰「借不到」並印出 `git switch` 指令 · VRN-2 照常)· 找 VRN-1:`VIA_VRN1_ROOT` → `C:\Users\tonyk\VIA-VDF-VRN` → 家目錄 → VIA 倉旁邊 |
| 程式夾(本機執行) | `<ROOT>\functional modules\VRN\` | 管理器鏈 v0154–v0239 / ENG397 / ENG062 / 處理器 / **`VRN2_IndependentVerifier_v0102.py`**(v0100 / v0101 留著不刪 · 啟動器用最新版 · VRN-2 的檔都不在 git 追蹤 · 都進船包) |
| **U/I(舊版)** | `<ROOT>\VIA_Reports\vrn2\VRN2_UI_latest.html` | 管理器寫;v0142 起頁首多一條「開啟 VRN-2 Workbench」;vrn2:// 處理器 v0104 重開的是這一頁 · 每檔細節 / 驗證過的輸出仍在這裡 |
| **獨立驗證報告** | `<ROOT>\VIA_Reports\vrn2\verify_independent\VRN2_IndependentVerify_<時間>.json` + `.txt` + **`.digest.txt`(貼給 AI)** | v0127 起啟動器 ⑪ 自動產生(只讀 · 不改輸出)· 報告多 `fp`(冊指紋)· `fin_rows`(每筆判決) |
| **VRN-2 船包(GitHub)** | `<ROOT>\docs\handoff\ai\vrn2_ship\VRN2_Bundle_latest.zip` + `.json` | ⑨ 完成時寫入並提交 · 只含 VRN-2 自己的檔(含獨立驗證器)· 內容沒變位元組就不變 |
| VRN-2 設定冊 | `…\VRN\SSOT\VRN2_SSOT_v####.json` | 來源夾 · 範圍 · 交付項 · 漏斗參數 |
| 輸入設定冊(VRN-2 本機副本) | `…\VRN\SSOT\VRN_Config_v1000 起` | VRN-2 的管理器鏈從這裡讀 input_dir;VCGC 側用 v0100(不同號段) |
| 原始樣本 / 範圍夾 / 範圍冊 | `C:\測試樣本報告` · `<ROOT>\VIA_Reports\vrn2\scope_in\` · `…\vrn2\VRN2_Scope_latest.json` | |
| **輸出冊** | `<ROOT>\VIA_Reports\vrn2\output\` | `VRN2_BasicInfo / FinancialData / Summary / Rejected_latest.{json,csv,parquet}` · 年度數據欄位 `VERIFY` / `SUBCOL` / `ROW` / `SECTION` |
| Parquet 舊檔 | `…\vrn2\output\_stale\` | 本輪寫不出 Parquet(缺 pandas / pyarrow)時上一輪的移到這裡(不刪) |
| 完成判定 / 啟動紀錄 | `…\vrn2\VRN2_Completion_latest.json`(+ `_Rounds.jsonl`)· `VRN2_Activate_latest.json` | |
| 快取 | `…\vrn2\p1_cache\` · `acc_cache\` · `ocr_cache\` · `summary\` | |
| 鎖 / 成功登記 / 元件登記 | `…\VRN\registry\VRN2_Lock_*.json` · `VRN2_Module_Success_Register.json` · `VRN2_Component_Register_v####.json` | 鎖與成功登記帶時間 → 留本機;元件登記冊進船包 |
| 封存 / 隔離 | `…\VRN\_archive_vrn2\`(+ `ARCHIVE_MANIFEST.jsonl`)· `…\VRN\_quarantine\` | ⑩ 只搬 VRN-2 自己的舊版 |
| U/I 處理器 / 協定 | `…\VRN\VRN2_UIAction_v0103.py`(v0102 留著)+ `VRN2_UIAction_Config.json` · `HKCU\Software\Classes\vrn2`(⑥c 寫完讀回核對) | 動作:run · run?nopush=1 · run-clean · restore-archive · **pick · audit** |
| OCR 隔離環境 | `C:\Users\tonyk\envs\vrn2_ocr\` + `VRN2_OCRBridge_v0100.py` | |
| **交接報告** | `<ROOT>\docs\handoff\ai\VRN2_Handover_v0143.md` | 本線(套件線)的交接;`VRN2_Handover_latest.md` 是桌機線(v0145)的,不蓋 |
| 本輪證據 | `<ROOT>\docs\handoff\ai\vrn2_release_v0141\`(v0136:`vrn2_release_v0136\` · v0135:`vrn2_release_v0135\` · v0134:`vrn2_release_v0134\` · v0133:`vrn2_release_v0133\` · v0132:`vrn2_release_v0132\` · v0131:`vrn2_release_v0131\` · v0130:一鍵判定)| 發行清單 · 驗證紀錄 · 日誌 · 截圖 · 測試工具(含驗證器反向測試總表) |

---

## 3. 版本紀錄

### 3.1 現役版本(v0141 套件 · 私有 runtime v0141 逐檔雜湊還原)

| 元件 | 版本 | 大小 | SHA-256(前 12) | 本輪 |
|---|---|---|---|---|
| ActivateVRN-2_v0141.py(套件 · 底座 v0136)| **v0141** | 見發行清單 | 見發行清單 | **新**(= v0140 入口 + 管理器 v0243 + 原文核對 v0104 + runtime v0141 + STALE_RECORD 自動再跑一輪)|
| **VRN_SystemManager** | **v0243**(v0239 底座 · v0240 ~ v0242 留著)| 見 runtime 清單 | 見 runtime 清單 | **新**(冪等閘像對像 ×2 + 分類 + 清過期快取 · 備援指令回 v0136 契約)|
| **VRN_ENG062_SummarizerV1** | **v0116**(v0114 / v0115 留著)| 見 runtime 清單 | 見 runtime 清單 | **新**(四點補齊階梯 · 每點精確字串)|
| **VRN_ENG062_SummarizerV1** | **v0117**(v0114 ~ v0116 留著)| 見 runtime 清單 | 見 runtime 清單 | **新**(開頭頁首 / 標題 / 小標題列去掉 · 區間雜湊重算)|
| **VRN2_Workbench** | **v0100** + Assets v0100(117 woff2 · 4.4 MB)| 見 runtime 清單 | 見 runtime 清單 | **新**(範本視覺鎖定 · 綁收據與輸出冊 · vrn2:// · logo 去背 · 自測 16 · 真瀏覽器 17)|
| **VRN2_ChainShip** | **v0100**(倉 `functional modules/VRN/`)| 26,530 | `cfee9e2d056d` | **新**(PR #570:釘名前版盤點 check · 在位未入倉補船 ship;桌機一鍵貼 `docs/handoff/ai/VRN2_ChainShip_v0100.md` §3)|
| **VRN2_ChainShip** | **v0101**(v0100 留著)| 39,259 | `81b47d7f9b83` | **新**(`recover`:缺的環在 VIA 樹 / 私有 runtime / 備份 / Downloads VRN2_* 夾與 zip 找同名唯一內容 → 複製進 VRN 夾再隨船;`ship --no-recover` 關;自測 27)|
| ActivateVRN-2_v0146.py(套件 · 底座 v0136)| **v0146** | 見發行清單 | `b35f66cb6972` | **新**(⑥e 市場擷取 · ⑥f 共識 Combined · ⑬b 歷史對齊 · ⑬c 整合掃描 · Workbench v0102 · 處理器 v0109 · SSOTSync v0101 · 收據 v0146)|
| **VRN2_Workbench** | **v0102**(薄尾 · v0101 留著)| runtime v0146 | `3aeeb60485b5` | **新**(雙語表頭 · 靠上 · 百萬台幣千分位 · 自動縮放 · 輸出夾格 · 去重矩陣 + 引擎狀態 · 歷史對齊表 · logo 180% · 自測 13 項)|
| **VRN2_UIAction** | **v0109**(薄尾 · v0108 留著)| runtime v0146 | `4177fccbaadb` | **新**(vrn2://integrate?scan / apply / dismiss · --integrate-scan · 自測 6 項)|
| **VRN2_SSOTSync** | **v0101**(薄尾 · v0100 留著)| runtime v0146 | `85694ded092a` | **新**(提案冊併入請求冊 · 自測 6 項)|
| **VRN2_HistoryAlign** | **v0100** | runtime v0146 | `ac973d47a428` | **新**(至少一期對上 · 倍率自動 · 歷史覆蓋預估 · 刪除區 · 加減乘除檢驗 · 自測 14 項)|
| **VRN2_DataIntegrate** | **v0100** | runtime v0146 | `2aa75abd4d49` | **新**(CSV / XLSX / Google Sheet 匯出偵測 · 自適應欄位對齊 · 原檔不刪 · TEMP 副本 · 自測 15 項)|
| **VRN2_ConsensusJoin** | **v0100** | runtime v0146 | `d95ebd73f2af` | **新**(跑共識引擎 · Combined 冊欄序 · 真實年份 · 自測 7 項含引擎離線實跑)|
| **VRN2_SSOT_Proposals** | **v0100.json** | runtime v0146 | `4971a326455c` | **新**(Gemini 對話 9 條提案 · ssot_id 空白)|
| **VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine** | **v0120**(操作員上傳 · 原樣 · 不改一字)| runtime v0146 | `b50b3ba6f06c` | **借用**(FactSet 鉅亨 + YFinance 共識 · 自帶單元測試 · 需 yfinance;duckdb 可缺)|
| ActivateVRN-2_v0145.py(套件 · 底座 v0136)| **v0145** | 見發行清單 | `a4c76d1d1e28` | **新**(改指管理器 v0255 · 收據 v0145;其餘同 v0144)|
| **VRN_SystemManager** | **v0255**(薄尾 · 釘名 v0243;v0243 留著 · v0244 ~ v0254 = 桌機線)| 見 runtime 清單 | `0a73b4efd17f` | **新**(冪等閘每波一份一子行程並行 · 心跳 · timing · 階段計時 · 自測 PASS)|
| ActivateVRN-2_v0144.py(套件 · 底座 v0136)| **v0144** | 見發行清單 | `885632b1f289` | **新**(⑤b SSOT-ID 同步 · ⑬ 輸出位置 / 增量庫 · 處理器 v0108 · Workbench v0101;v0143 的閘 / 上限 / 補放照舊)|
| **VRN2_SSOTSync** | **v0100**(runtime v0144 新成員)| 見 runtime 清單 | `609e049d6068` | **新**(request / apply / sync · 自測 9)|
| **VRN2_OutputStore** | **v0100**(runtime v0144 新成員)| 見 runtime 清單 | `2031a5450d0b` | **新**(鏡像 + DuckDB 增量 Parquet 庫 · pyarrow 備援 · 自測 9)|
| **VRN2_UIAction** | **v0108**(v0104 留著;v0105 / v0107 是桌機線 publish 處理器的號,本線跳過)| 見 runtime 清單 | `617da33b147d` | **新**(`vrn2://pick?kind=outdir` · `outdir?reset=1` · `--set-outdir` · 自測 14)|
| **VRN2_Workbench** | **v0101**(v0100 留著)| 見 runtime 清單 | `5ab386cf3f96` | **新**(匯出分頁 輸出位置面板 + 拖曳區 + 庫收據表 · 交接分頁 SSOT-ID 表 · 自測 18)|
| ActivateVRN-2_v0143.py(套件 · 底座 v0136)| **v0143** | 見發行清單 | `90904b09d7ed` | **新**(單機閘 · 子行程上限 env · ⑫b 本支補放 · 收據 v0143;runtime v0142 不動)|
| **VRN2_VerbatimVerifier** | **v0104**(v0100 ~ v0103 留著)| 見 runtime 清單 | 見 runtime 清單 | **新**(缺句 MISSING · 讀不到 PDF 一列 FAIL · 忽略 bullet / 控制字元)|
| **VRN2_IndependentVerifier** | **v0110**(v0105 核心 · v0106 ~ v0109 留著)| 見 runtime 清單 | 見 runtime 清單 | **新**(四點 MISSING 判決)|
| **VRN2_ToolBridge** | **v0101** | 見發行清單 | 見發行清單 | **新**(= v0100 + 借不到時說清楚下一步 · 借用規則不變)· v0100(v0131)照舊留著 |
| VRN-2 SystemManager | v0231 → … → v0238 → **v0239** | v0231 215,605 · v0232 43,966 · v0233 10,066 · v0234 27,553 · v0235 22,840 · v0236 33,760 · v0237 37,036 · v0238 11,887 · v0239 18,415 | `ddff2743b478` / `42e682ba5074` / `25e33a714860` / `d8a564b2c442` / `53ea452b978e` / `872f7fde9452` / `514962c4f0bd` / `87a3c4d7ab51` / `b1eb69452d1c` | **v0239 新**(薄尾 · 前版必須 v0238 · 段落標題改回同一欄)· v0238:表頭列移剔除冊 |
| **VRN2_IndependentVerifier** | **v0105**(v0102 / v0103 / v0104 留著)| 94,467 | `f16abb73b282` | **新**(v0104 + DUPKEY 位置證據 · 對調診斷 · EPS 格 · 摘要每類都出現 · 自測 30 / 30)|
| **VRN2_IndependentVerifier** | **v0104**(v0102 / v0103 留著)| 85,081 | `7b29cf53cd08` | v0135 內嵌 · 留著 |
| **VRN2_IndependentVerifier** | **v0103**(v0102 留著)| 81,822 | `5a0c2467feea` | v0134 內嵌 · 留著(Codex #561 指出的兩點在 v0104 修)|
| VRN_ENG397_P1Segment | v0127 | 180,699 | `c2e8e39e5584` | 未變 |
| VRN_ENG062_SummarizerV1 | v0114 | 63,825 | `62beeaf65576` | 未變 |
| VRN2_UIAction · VRN2_OCRBridge · rule_catalog | **v0104**(v0102 / v0103 留著)· v0100 · — | — | `0d9df0c87d0e` · `4b21f0694d0e` · `e5b881716c84` | **新**:處理器 v0104 檔名規則取最新版管理器(自測 11 / 11)· 其餘未變 |

### 3.2 版本鏈

| 啟動器 | 管理器 | ENG397 | ENG062 | 主要內容 |
|---|---|---|---|---|
| v0110 – v0118 | v0221 – v0228 | v0119 – v0124 | v0107 – v0111 | 使用者機器第 35 輪 |
| v0119 – v0121 | v0229 – v0231 | v0125 – v0126 | v0112 | 只在沙盒 |
| v0122 | v0231 → v0232 | v0127 | v0112 | 輸出值驗證 · 平行段 · 守門 |
| v0123 | → v0233 | v0127 | v0113 | 獨立上船(船包)· 新電腦還原 |
| v0124 | → v0234 | v0127 | v0114 | 一格多值拆子欄(使用者機器第 38 輪) |
| v0125 | → v0235 | v0127 | v0114 | ⑨ 只送 VRN-2 船包 · 第三讀法閘(使用者機器第 39 輪) |
| v0126 | → v0236 | v0127 | v0114 | 轉置表 · 表頭在表外 · 季度欄移出 · ROW / SECTION |
| **v0127** | → **v0237** | v0127 | v0114 | U/I「驗證過的輸出」· ⑪ 背景獨立驗證寫回 · 一格整列拆開 · 重複列只留一筆 · 驗證器 v0100 |
| v0128 | → v0238 | v0127 | v0114 | 依 MAIN 登記紀錄定位 VRN-2 程式夾(VIA_ROOT 指錯不再擋)· cmd / PowerShell 都能貼的一行 · 表頭列移出 · 驗證器 v0101 |
| v0129 | → v0239 | v0127 | v0114 | 並排表的段落標題改回同一欄 · 驗證器 v0102 SECFAIL |
| (一鍵 v0130) | 同 v0129 | | | 一鍵判定三處(⑪ 三段 · 只驗本輪的冊 · 成功看本輪 ⑧)|
| v0131 | 同 v0239 | v0127 | v0114 | 工具相互取用:② 借出工具冊 · ⑫ 借 VRN-1 PIVOT 資料庫 · 工具橋 v0100 |
| v0132 | 同 v0239 | v0127 | v0114 | 工具橋 v0101:借不到 VRN-1 的工具時說清楚下一步 |
| v0133 | 同 v0239 | v0127 | v0114 | 前後端連結:U/I「輸入(window I/O)」區塊 · 處理器 v0103 · ②b 輸入來源 · ⑥c 讀回核對 · ⑫b · 註冊核對 |
| **v0134** | 同 v0239 | v0127 | v0114 | 整合一支:處理器 v0104 · 驗證器 v0103 · U/I 開不開只認 VRN2_NO_UI · ⑨ 交接不回退 · 主體不動 |
| v0135 / v0136 | 同 v0239 | v0127 | v0114 | Codex #561 / #562 · 整合一支第二回(驗證器 v0104 / v0105 · ⑫a)|
| (另一團隊 v0137 ~ v0140 · 套件 v0102 ~ v0104)| v0240 ~ v0242 | v0127 | v0115 | 私有 runtime · 原文四點(SOURCE_VERBATIM)· 冪等語意比較 · 緊湊 U/I · 完成驗收容許缺值 |
| **v0141** | → **v0243** | v0127 | **v0116** | 收尾套件:四點補齊階梯 · 冪等閘像對像 ×2 + 分類 + 自動再跑一輪 · 原文核對 v0104 · 驗證器 v0110 · 備援指令回 v0136 契約 |
| **v0142** | 同 v0243 | v0127 | **v0117** | 摘要器開頭去頁首 / 標題 / 小標題 · Workbench U/I v0100 收尾後渲染並開啟 · 舊版 U/I 加連結列 · 收據多 workbench · 操作員一鍵 v0103 改指本版 |
| **v0143** | 同 v0243 | v0127 | **v0117** | 單機閘 · ⑫b 600 秒 + 本支補放 · ⑦ 無輸出 3600 秒 · 工具冊 900 秒 · ⑪ 3600 秒 · 收據 v0143(runtime v0142 不動)|

> 使用者機器:GitHub 有 VCGC 側 v0114–v0153;本機有 VRN-2 的 v0154–v0228 → v0231 的前版是 v0228。v0127 依序落地 v0231 → v0237,每支自測過才落下一支。跑過 v0126 → 前六支「已在且 hash 同」,只落 v0237 + 獨立驗證器。v0129 依序落地到 v0239(使用者機器上次成功 v0235 → 落 v0236 → v0237 → v0238 → v0239 + 驗證器 v0102;跑過 v0128 → 只落 v0239 + v0102)。

---

## 4. SSOT 現況

| 冊 | 現況 |
|---|---|
| `VRN2_SSOT_v0100.json` | system VRN-2 · independent true · scope stock_only · 交付項 7 · funnel · 換電腦來源夾不同 → 出 v0101(只增) |
| `VRN_Config_v1000 起` | VRN-2 本機副本(input_dir → 範圍夾) |
| `VRN2_Component_Register_v####` | VRN-2 正式編號 · 獨立系統 → 不送 VCGC 核號 |
| `VRN2_Bundle_latest.json` | 船包清單(路徑 · 大小 · SHA-256 · 相依的 GitHub 檔) |
| 中央冊 | **不登**(獨立系統)· VCGC 只讀監控 |

---

## 5. 完成判定(⑧)與 ⑪ 獨立驗證

| 條件 | 擋完成? |
|---|---|
| 實測退步 · 交互驗證 · 鎖定 + 備份 · 冪等 · ② 覆蓋 ≥97% · ③ 數字回原文 · ⑤ 一標題四重點 · ⑥ AUDIT · 個股四項 | 紅擋 |
| ① 計算驗證 | 同表不平才紅 |
| 輸出冊完整 · 調節輪 · ⑦ 雙讀 · 輸出值驗證(剔除進剔除冊) | 黃提醒 |
| 啟動器:完成判定檔必須本輪寫的 · ⑦ 不紅 · ② / ⑥ 不紅 | 不符 → ⑧ 紅 |
| **⑪ 獨立驗證(v0127)** | **不擋 ⑧**(驗證器也要被驗)· 錯值 0 且寫回 U/I = 綠 · 有待核對 / 超時 / 沒跑完 = 黃 · 摘要進貼包 |

順序:⑦(`vrn2 --run --no-open`)→ ⑪ 背景開始 ∥ ⑧ → ⑨ 上船 → ⑩ 封存 → ⑪ 等結束(最多 30 分 · `VIA_VRN2_VERIFY_WAIT`)· 寫回 U/I → 開 U/I。

---

## 6. 實測結果

### 6.1 使用者機器第 39 輪(v0125 · 52 份)

⑧ 完成 · 紅 0 · 黃 5 · 年度數據 11,544 筆 · P1 黃 11 份(轉置表 / 表頭在表外 → v0126 修)· 沒貼回 ⑨ 那一行與驗證摘要。

### 6.1b 使用者機器 2026-10-19(v0127 第一次跑)

① 把 PowerShell 程式貼進 cmd → 每行被 cmd 拒絕 · 什麼都沒跑 ② 改貼「一行」→ Windows PowerShell 5.1 · 雜湊相符 · 啟動器 v0122 → v0127(舊的備份)· 啟動器 ② 紅「找不到 VRN-2 程式夾 functional modules\VRN」· rc 2 · 輸出冊仍是 v0125 那輪(52 份 · 年度數據 11,544)· 本機另有 131 個別的系統的提交沒推(不是 VRN-2 的)。→ v0128 修定位。

### 6.2 容器實測(v0127 · 19 份真實 PDF · 個股 14 份)

| 項目 | 結果 |
|---|---|
| 自測 | **啟動器 v0127 20/20** · 管理器 v0231 33/33 · v0232 11/11 · v0233 6/6 · v0234 14/14 · v0235 7/7 · v0236 13/13 · **v0237 12/12** · **獨立驗證器 v0100 16/16** · ENG397 34/34 |
| 年度數據(v0236 → v0237) | 4,860 → **4,916**:一格整列拆開 +65(凱基慧洋財務比率表 13 列 × 5 期:流動比率 · 速動比率 · 淨負債 · 每股盈餘 · 每股現金盈餘 · 每股淨值 · 調整後每股淨值 · 每股營收 · EBITDA/Share · 每股現金股利 · 資產周轉率 · Cash Flow Int. Coverage · Cash Flow/Int. & ST Debt)· 完全重複移出 9 · 剔除冊 719 → 733 |
| **獨立驗證 v0100**(14 份 · 3 路平行 · 25 秒) | 基本資料 **194/194** · 一標題四重點 **63/63** · 年度數據 4,916:ALIGNED 4,389 · SUBALIGNED 452 · TRANSALIGNED 75 · **PRESENT 0 · 所有不過類別 0**(v3 時的 PRESENT 10 = 凱基貿聯 EV/EBITDA 值列在科目列上方半行 → 先定列再找值後對位) |
| **驗證器反向測試總表** | 年度數據:下一列的值 v3 漏 2,917 / 3,000 → **v0100 漏 0** · 上一列的值 131 → **0** · 同列鄰欄 20 → **0** · 季度值標成年度 4/4 漏 → **0** · 子欄別列的值 29 / 40 漏 → **0** · 轉置別年 0 · 基本資料目標價 ↔ 股價 → 0 · 評等換成定義頁才有的 → 0 · 重點數字換掉 / EPS 年度對調 / 跨檔對調 → 0 · 原本的 ①~⑩ 10/10 |
| U/I 真瀏覽器(Chromium) | **35/35**(新增 14 項:第一個分頁 · 指紋相同才套用 · **頁面每一格 = 年度數據冊那一筆(4,916 / 4,916)**· 總表 · 選檔 · 徽章 · 提示 · 搜尋 · 只看待核對 · 下載 CSV · 指紋不同不套用) |
| 實跑(新樹 ×2 · 從 v0126 升級的一鍵 PS ×2 · 新電腦 clone)| 每次 ⑧ 完成 紅 0 · ⑪ 綠 錯值 0 · 再跑四本冊逐位元相同 · ⑨ 只送 VRN-2 船包(別的系統本機提交不推)· clone 補回 16/16 · 細節見 `vrn2_release_v0127/VRN2_Verification_v0127.md` |

### 6.4 容器實測(v0129 · 同 19 份 PDF · 個股 14 份)

| 項目 | 結果 |
|---|---|
| 自測 | **啟動器 v0129 23/23**(內嵌 16 個元件)· **管理器 v0239 10/10**(鏈 v0231 33/33 … v0238 7/7 全過)· **獨立驗證器 v0102 18/18** |
| **使用者機器情境重現** | 上次成功 v0125(管理器鏈到 v0235)· Downloads 的啟動器已被一行換成 v0127 · 環境變數 VIA_ROOT 指錯 · 遠端放 v0129 發行分支 → 一行 → 雜湊相符 → ③b 改正 VIA_ROOT → ② 「來源 VIA_ROOT · 登記 VRN_SystemManager_v0235.py sha 相符」→ 落地 v0236 → v0239 + 驗證器 v0102 → ⑧ 完成 · ⑨ 只送 VRN-2 船包 · ⑪ 綠 錯值 0 |
| 從 v0128 升級 + VIA_ROOT 指錯 | 先跑 v0128 並上船 · 遠端被別台推了新提交 · 本機有別的系統的提交 → 一行 → 備份 v0128 → 換 v0129 → ② 登記 VRN_SystemManager_v0238.py sha 相符 → 只落 v0239 + 驗證器 v0102 → ⑧ 完成 · ⑨ 只送船包 · ⑪ 綠 · 第 2 次 已是 v0129 · ⑨ 已是最新 |
| 只跑啟動器(不經 PS)· VIA_ROOT 指到別的夾 | ② 黃「來源 git 倉裡找到 · 登記 VRN_SystemManager_v0239.py sha 相符 · VIA_ROOT … 那裡沒有 VRN-2 程式夾 → 不用」· 其餘全綠 |
| 一行的竄改測試 | 分支上的一鍵程式碼被改一個字 → SHA-256 不對 → 不執行 |
| 新電腦(從遠端 clone) | ② 綠(船包清單的管理器下一步補回)· 船包補回 18/18 · ⑧ 完成 · ⑪ 綠 · 沒設 git 使用者 → ⑨ 黃且一行寫明要跑的 git config · 設了 → ⑨ 上船 |
| 輸出 | 年度數據 **4,905** 筆 · 值與 v0128 逐筆相同 · **段落標題改回 13 列 65 筆**(凱基 2637 P5·F·02·TB → 空白:這兩張表在本表範圍裡沒有自己的段落標題)· 其餘 4,840 筆一個欄位都沒變 · 基本資料 / 一標題四重點 / 剔除冊與 v0128 **逐位元相同** · U/I 冊指紋不變(指紋不含 SECTION)· **獨立驗證 v0102** 194/194 · 63/63 · 4,905 錯值 0(SECFAIL 0 · HDRVAL 0)· 反向測試漏抓 0(新增:段落標題 65 筆放回 → v0102 全抓 · v0101 全漏 · 右表 / 左表換成另一張表才有的標題 140 筆 → 全抓)· U/I 真瀏覽器 35/35 |

### 6.3 容器實測(v0128 · 同 19 份 PDF · 個股 14 份)

| 項目 | 結果 |
|---|---|
| 自測 | **啟動器 v0128 23/23**(新增:依紀錄定位 · 新 clone 的定位說明 · git 失敗訊息一行 · 內嵌 15 個元件)· **管理器 v0238 7/7**(鏈 v0231 33/33 … v0237 12/12 全過)· **獨立驗證器 v0101 17/17** |
| **使用者機器情境重現** | 上次成功 v0125(管理器鏈到 v0235)· Downloads 的啟動器已被一行換成 v0127 · 環境變數 VIA_ROOT 指錯 · 遠端放 v0128 發行分支 → 一行 → 雜湊相符 → ③b 改正 VIA_ROOT(只在這個視窗)→ ② 「來源 VIA_ROOT · 登記 VRN_SystemManager_v0235.py sha 相符」→ 落地 v0236 → v0237 → v0238 + 驗證器 v0101 → ⑧ 完成 · ⑨ 只送 VRN-2 船包 · ⑪ 綠 錯值 0 · U/I 寫回(冊指紋相同) |
| 從 v0126 升級 + VIA_ROOT 指錯 | 一行 → 備份 v0126 → 換 v0128 → ② 登記 VRN_SystemManager_v0236.py sha 相符 → ⑧ 完成 · ⑨ 只送船包 · ⑪ 綠 · 第 2 次 已是 v0128 · ⑨ 已是最新 |
| 只跑啟動器(不經 PS)· VIA_ROOT 指到別的夾 | ② 黃「來源 git 倉裡找到 · 登記 VRN_SystemManager_v0238.py sha 相符 · VIA_ROOT … 那裡沒有 VRN-2 程式夾 → 不用」· 其餘全綠 |
| 一行的竄改測試 | 分支上的一鍵程式碼被改一個字 → SHA-256 不對 → 不執行 |
| 新電腦(從遠端 clone) | ② 綠(船包清單的管理器下一步補回)· 船包補回 17/17 · ⑧ 完成 · ⑪ 綠 · 沒設 git 使用者 → ⑨ 黃且一行寫明要跑的 git config · 設了 → ⑨ 上船 |
| 輸出 | 年度數據 4,916 → **4,905**(表頭列 3 列 11 筆移剔除冊 · 剔除冊 733 → 744)· 基本資料 / 一標題四重點與 v0127 **逐位元相同** · 每次跑出來的四本冊彼此逐位元相同 · **獨立驗證 v0101** 194/194 · 63/63 · 4,905 錯值 0(ALIGNED 4,378 · SUBALIGNED 452 · TRANSALIGNED 75 · HDRVAL 0)· 反向測試漏抓 0(新增:表頭列 11 筆放回 → v0101 全抓 · v0100 全漏 · 混進整本冊 → 一般列不誤標)· U/I 真瀏覽器 35/35 |

---

## 7. 本輪(v0145 → v0146 · 桌機 2026-10-29 10:25 貼回 + 操作員 U/I 與資料需求)

| # | 操作員 | 追到的根因 / 判讀 | v0146 做法 | 實測 |
|---|---|---|---|---|
| 1 | 字體爆出格子不會自動調整? | 統計磚 `.stat b` 固定 24px、格子 nowrap | clamp + 逐 px 縮(最小 12px)· 不夠就換行;td 靠上 + overflow-wrap | Chromium:鎖定版本磚縮到 12px / 換行 · 0 溢出 |
| 2 | 表頭空格 · 靠上 · 百萬台幣千分位(每股 / 倍數例外) | v0101 原欄名 + 原值 | 雙語表頭表 HDR · cell() 依 ITEM / TABLE 判單位(bn ×1000 · thousand ÷1000 · 沒標視為百萬)· 每股 / 倍數 / % 原值 · title 看原值 | Chromium:`Revenue (NT$ bn) 2,894.3 → 2,894,300` · EPS 45.25 · ROE 28.9% · P/E 18.2x |
| 3 | 左邊 Gate 要一格輸出檔案夾(Parquet 長線庫) | 輸出位置只在 03 匯出頁 | 左欄「輸出檔案夾 · 長線資料庫」:目前夾 · 增量庫引擎 / 累計 · 開啟 / 換 / 取消 · 整合提示 | 沙盒:OneDrive 夾 · pyarrow 累計 BasicInfo 14 / FinancialData 4905 |
| 4 | 舊資料庫(CSV / Google Sheet)主動提醒整合 · 整合前不刪 · 自適應欄位 · 舊資料放 TEMP | 沒有 | DataIntegrate v0100 + 處理器 v0109 + ⑬c | 自測 15 項(cp950 雜訊列 · Google Sheet 匯出 · xlsx · 去重 / CONFLICT · 原檔 sha 不變 · TEMP 副本)· 沙盒 ⑬c PENDING_USER 1 份 |
| 5 | 歷史資料對齊 · 至少一期要對 · 歷史覆蓋預估 · 加減乘除檢驗 · 刪除區 | 沒有 | HistoryAlign v0100 + ⑬b | 自測 14 項;沙盒灰(⑥e 沒抓到市場資料) |
| 6 | 右面板第一區 = 輸入去重矩陣 + 目前引擎狀態 | 第一區是統計磚 | 新 `#first` 區塊在統計磚之前 | Chromium:PDF 唯一 13 · 多餘副本 1 · 引擎狀態含 ⑥e / ⑥f / ⑬ / ⑬b / ⑬c |
| 7 | 昨天不是可以擷取 TWSE/TPEX/YFINANCE 嗎 現在為何不行 | 昨天跑的是桌機線自己的啟動器(管理器 v0249 有 ⑥e);本套件線沒有 | ⑥e 借共用 MarketFetch(--fetch / --fill) | 自測(假工具 · 燈號);沙盒灰(樹裡沒共用工具) |
| 8 | 共識引擎 v0120 → Combined 目標價後接 FactSet / YFinance 中位數 · 2026 ~ 2028 EPS / PER(真實年份)| Combined 冊本線沒有 | ConsensusJoin v0100 + ⑥f(引擎原樣內附) | 引擎離線 fixture 實跑 gate PASS_WITH_WARNINGS · 沙盒 Combined 14 列 · Chromium 25 欄雙語表頭 |
| 9 | LOGO 留白更少但不砍字 · 高畫質 180% · 仍透明無框 | v0101 留白 4% · 44px | alpha 內容框重裁 1.5% · LANCZOS ×1.8 · 頁首 100px | 自測 ⑬(角落透明 · 中心紅 · 留白 ≤ 3%) |
| 10 | 2546 秒 | CPU 被佔 87.5% → 1 路;輸出冊 969 秒 = 第二讀取器回查 10,908 值 | 本輪不動(列待辦) | — |

---

## 7.0i 前一輪(v0144 → v0145 · 桌機 2026-10-29 08:14 貼回)

| # | 貼回 | 追到的根因 | v0145 做法 | 實測 |
|---|---|---|---|---|
| 1 | 「花很多時間 · 是第一次啟動還是加速器沒作用」· 2422 秒 | 都不是:快取 52/52 命中、加速器已載;⑦ 1201 秒裡約 1050 秒無輸出 = v0243 冪等閘 3 份 ×2 單路序跑、不吃快取(主跑本身都是快取)| 管理器 v0255:每波一份一子行程並行 · 心跳 · timing · 階段計時 | 自測 PASS · 沙盒冪等閘 GREEN · R1 3.5 秒 3 路 |
| 2 | 「確認已與 HTML U/I 同步、使用者可用」| 貼回已證明:⑥c · ⑤b · ⑫b · ⑬(duckdb)· Workbench v0101 全綠 · 驗證判決寫回指紋相同 | 不改;寫進交接 | — |
| 3 | ⑧b rc 1:四點原文核對 FAIL 1(3014TT POINT_3)· 缺項 3 份年度數據 | 要貼回 zip 的 `VRN2_VerbatimVerify_latest.json` 與原檔 | 本輪不碰(zip 還沒上傳)| — |
| 4 | ④ 貼回包黃「缺 2」(v0143 收據 · 鎖檔)| 清單列了前版收據與跑完必移除的鎖 | 本地實測一輪 ④ 改收 v0145 收據 + 階段計時 | 下一次貼回 |

---

## 7.0h 前一輪(v0143 → v0144 · 操作員 2026-10-29 政策)

| # | 政策 | VRN-2 側做法(v0144)| 實測 |
|---|---|---|---|
| 1 | SSOT / Regex / 同義字 / 政策由基層提出 · ID 空白 → VCGC 提示衝突 → 使用者 + AI 修 → VCGC 核號 → 子系統自動補填 | SSOTSync v0100:請求冊(ssot_id 空白 · proposed_no · vcgc_kind · 自撞)→ 讀核發冊 → 核發補填出新版登記冊 · 衝突列待人判;契約寫在 `VIA_SSOT_ID_Protocol_v0100.md`(VCGC 核發冊的格式是**契約**,VCGC 那邊還沒實作,VRN-2 不代寫)| 自測 9 / 9 · 沙盒 ⑤b GREEN |
| 2 | 輸出位置可用 Windows I/O 拖曳式或連接雲端 | 處理器 v0108 `vrn2://pick?kind=outdir` + Workbench v0101 面板 / 拖曳區(拖曳 → 對話框)+ 舊版 U/I 區塊;OneDrive 等同步夾 = 雲端(cloud_hint)| 處理器自測 14 / 14 · Workbench 18 / 18 · 沙盒 `VRN2_OUTPUT_DIR` 指 OneDrive 式夾 → YELLOW |
| 3 | 輸出 Parquet 增量擷取 · 用 DuckDB 管理 · 全景式檢視 | OutputStore v0100:catalog(SHA-256)+ book_* + Parquet 分區 + catalog.parquet;Workbench 匯出分頁列庫收據(引擎 · 新檔 / 已知 · 追加 · 累計)| venv_duck:新檔 14 → 第二次 0 · SQL join 可查;沙盒(無 duckdb)pyarrow 備援 YELLOW |
| 4 | 三系統獨立 · 各自 MAIN · 手冊一致 | VRN-2 只改自己的 runtime 與冊;VCGC / VDF 檔不碰;協定 md 放 `docs/handoff/ai/`(三系統共讀)| `git status` 只有 VRN-2 的檔 |

---

## 7.0g 前一輪 v0141(v0136 / 另一團隊 v0140 → v0141 · 收尾套件)

| # | 貼回(v0140 · C:\測試樣本報告)| 追到的根因 | v0141 做法 | 實測 |
|---|---|---|---|---|
| 1 | 冪等 RED:神達 3706 主跑紀錄 ≠ 重跑 | v0242 閘:主跑紀錄(快取 / 子行程)vs 同行程重跑一次;分不出紀錄過期與引擎非冪等;神達原檔不在容器 | 管理器 v0243:主跑同一條子行程路徑重跑 ×2 → GREEN / STALE_RECORD(清該檔擷取快取 → 啟動器自動第 2 輪)/ NONDETERMINISTIC(RED · 第一個差異路徑)· 收據記錄執行環境 | 13 份真實檔三路徑 ×4 差異 0 · 沙盒冪等 GREEN · 自癒情境 STALE_RECORD → 第 2 輪 GREEN |
| 2 | 四點原文核對 FAIL 8(GFHK P1~4 · 欣銓 P3~4 · 3014TT · 華南 2606)| v0115 只挑嚴格句;空點被原文核對 v0103 算 FAIL | ENG062 v0116 階梯補齊(每點精確字串 · 去 bullet / 控制字元)· 原文核對 v0104 缺句 = MISSING rc 2 · 驗證器 v0110 | 合成 GFHK / 欣銓式 PDF 0/4 · 1/4 → 4/4 · 4/4;真實 13 份 TOTAL {'PASS': 48, 'FAIL': 0, 'OCR_PENDING': 0, 'MISSING': 0};沙盒 {'PASS': 52, 'OCR_PENDING': 4} |
| 3 | 輸出冊缺項 6 | 同 2 | 同 2 | 沙盒一標題四重點 14 份全 4/4 |
| 4 | U/I 備援「複製執行指令」| v0242 換成只有 PS7 模板 | 管理器 v0243 回 v0136 契約 + PS7 模板 + VRN2_ROOT + finally Restore | Chromium 35 / 35 |
| 5 | 獨立驗證 ✗ 45(6933 AMAX 37 · 凱基 2891 8)| 兩份 PDF 不在容器 | 財務核心 v0105 不動;要原檔或 digest | — |
| 6 | 入口 | 另一團隊的 Invoke-VRN2-Closeout_v0104.ps1 寫死 v0140 | 不出 .ps1:一鍵 `VRN2_OneClick_v0141.md`(③ 套件雜湊 + 套件內逐檔雜湊 · ⑤ 收尾收據 / 冪等閘 · ⑤b 處理器在 functional modules\VRN2)| pwsh 情境見 VRN2_Verification_v0141.md |

---

## 7.0f v0135 → v0136(整合一支 第二回)

| # | v0135 之後還留著的 | 做法(都在啟動器 v0136 內嵌的元件裡) | 實測 |
|---|---|---|---|
| 1 | DUPKEY 82 筆一行都沒進「貼給 AI」(摘要 150 行先被基本資料 25 筆 + BADITEM 吃掉)| 驗證器 v0105 摘要:每一類錯值先各印 6 筆(標題 + 檔分佈)再補滿 150 行;基本資料不過的只印 16 筆 + 一行「另有 n 筆」 | 自測:BADITEM 60 + DUPKEY 60 兩類都在 · ≤ 150 行 |
| 2 | DUPKEY 兩筆都標錯值,分不出哪筆對 | v0105 `dupkey` 看位置證據:同鍵只有一個值對位 → 那筆保留判決(註記)、另一筆 DUPKEY(註記對位的值是多少);都對位 / 都不對位 → 照舊兩筆都 DUPKEY | 自測 3 種組合 · 容器同一本冊判決逐類相同 |
| 3 | 標籤對調 3 筆(MS-6669 · GS-2317 · 神達)只寫「但旁邊是目標價標籤」 | v0105 `_swap_hint`:目標價在股價標籤旁且現價在目標價標籤旁 → 「對調」· 同值在目標價標籤旁 → 「現價被填成目標價」· 單邊 → 「可能把 … 當成 …」;值仍 FAIL | 自測 5 種組合 |
| 4 | MS-6669 一標題四重點 EPS 不是年度數據的值,沒說年度數據是多少 | v0105 `_eps_ok` 不符時印「年度數據 2025 年 EPS 是 EPS (NT$) 2025E=…」 | 自測 |
| 5 | ⑫ 灰:要操作員手動 `cd VIA-VDF-VRN; git switch main; git pull` | 啟動器 v0136 ⑫a:借工具前自己 fetch + fast-forward 到 VRN-1 的 main(已追蹤檔沒改動才動 · 原分支名印出 · 不改寫歷史 · 不提交 · 不推 · `VIA_VRN2_NO_VRN1_SYNC=1` 不同步)| 啟動器自測 git 夾具(feature 落後 1 → main 最新 · 改過 → 黃不動 · 關閉 → 灰)· 啟動器 --selftest 35 / 35(多 1 條:⑫a VRN-1 倉同步 git 夾具 —— feature 落後 1 → 切回 main 並 fast-forward · 改過 → 黃不動 · 關閉 → 灰;內嵌驗證器檢查改認 v0105) |
| 6 | 回歸 | 容器同一本冊(14 份 · 4,905 筆):v0104 與 v0105 判決逐類相同(ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 錯值 0 · 冊指紋相同) | — |
| 7 | 端到端 | 沙盒樹(19 份 PDF · 個股 14 · 處理器 v0104 · 驗證器 v0105):A1 ②b 綠(檔 19 · 個股 14 · 範圍外 5)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ 錯值 0(v0105 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 年度 4,905)· ⑫a 綠(容器的 VRN-1 clone 原在 claude/optimistic-goodall-yhalc5 → 切回 main 876a4f6 · fast-forward 0 · 原分支名在說明)· ⑫ 綠 4,653/4,905 · ⑫b 綠 · 註冊核對 全部登記成功;P1 U/I 選資料夾(9 檔 → 個股 5)→ ⑦ 5/5 · ⑪ 0;P2 U/I 選檔案 → ⑦ 2/2 · ⑪ 0;產業 / 其他 拒絕 rc 3;audit 綠 —— 與 v0135 同一組數字(無退步) | Chromium:既有 U/I 35/35 · 輸入區塊 14/14(一鍵情境頁) |
| 8 | 一鍵 | 沙盒一鍵 v0135(MAIN)→ v0136:一鍵程式碼雜湊相符 · ③ 舊啟動器 v0135 備份 · v0136 就位(雜湊相符)· 啟動器 ①~⑫ 綠(③ 環境檢查紅 = 沙盒 --no-install 仍缺 7 套件 · ② 船包 / ⑥c vrn2:// 灰 = 非 Windows;與 v0135 情境相同)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ v0105 錯值 0 · ⑫a 綠(VRN-1 倉已在 main 最新)· ⑫ 綠 · ⑫b 綠 · 註冊核對 處理器 v0104 · ⑤b 黃(Linux 沒 HKCU)· ⑤c 黃(無瀏覽器)→ NEXT YELLOW rc 2(Windows 應 GREEN · U/I 自己跳出) | — |
| 9 | 沒動(照實說)| 對調 / DUPKEY 另一筆 / EPS 用錯格 的**根因在擷取 / 摘要器**(ENG397 · ENG062 · 管理器),本輪只把證據寫清楚;修擷取端要等 Windows 用 v0136 跑一次、把帶證據的摘要貼回來 | — |

---

## 7.0e v0134 → v0135(Codex #561 / #562)

| # | Codex 指出(驗證器 v0103) | 做法(驗證器 v0104 · 內嵌啟動器 v0135) | 實測 |
|---|---|---|---|
| 1 | **P1** 空值記號(n.a. / NM / -)找不到就一律 NILVAL,沒看原文該格:擷取出 `n.a.` 而原文該格印 `12.3` 會從錯值裡消失 | `_nil_cell(lines, labs, per)`:定科目列 → 該列科目右邊的值用 `_align` 對 `per` 表頭(同一個 dx 門檻)→ 該格是數字 → 仍 FAIL(註記「原文該格是數字 …」)· 別的空值記號 / 空白 → NILVAL · 定不出科目列 / 這頁沒有這個期間表頭 → 仍 FAIL(註記不能確認) | 自測:該格 12.3 → FAIL · — → NILVAL · 空白 → NILVAL · 沒科目列 / 沒表頭 → None |
| 2 | **P2** `_num_cands` 去掉整列空白再找:「Price target 3 190」黏成不存在的 3190,標籤旁檢查誤過 | `_SPLITNUM`:只接「千分位逗點後的空白」「小數點後的空白」(`3, 190.00` · `1, 234. 5` · `4,388. 00`);`3 190` · `12 345` · `Dec 3, 2025` 不黏 | 自測 7 個案例 |
| 2b | **P1(PR #562)** 科目在這列、值在鄰列時 `_nil_cell` 只看科目列,下一列的 12.3 會被當成空白 → NILVAL | `_val_row`:與 `_row_hits` 同一套規則定值列(科目列右邊有值 → 科目列;沒有 → 上下鄰列 < 14 pt、科目欄不是別的科目、互為最近;期間表頭字樣 2024A / FY25 / Dec-25A 不算值)→ 再對 `per` 欄看該格 | 自測:科目在上一列、12.3 在下一列 → FAIL · 鄰列 — → NILVAL · 鄰列該欄空白 → NILVAL · 鄰列是別的科目 → 該格空白 |
| 3 | v0134 已合併 MAIN(PR #561)| 已合併的版本一個檔都不改:出 v0135(啟動器 · `vrn2_release_v0135` · 一鍵 · 本交接);v0103 留在啟動器裡(只增不減 · ⑪ 取最新版 = v0104)| 啟動器 啟動器 --selftest 34 / 34(內嵌驗證器檢查改認 v0104:_nil_cell · _val_row · _SPLITNUM · 自測 rc 0 · 內嵌清單 v0102 / v0103 / v0104) |
| 4 | 回歸 | 容器同一本冊 v0102 / v0103 / v0104 判決逐類相同 | 容器同一本冊(14 份 · 4,905 筆):v0102 · v0103 · v0104 判決逐類相同(ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 錯值 0 · 冊指紋相同) |
| 5 | 端到端 | 沙盒樹(19 份 PDF · 個股 14 · 處理器 v0104 · 驗證器 v0104):A1 ②b 綠(檔 19 · 個股 14 · 範圍外 5)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ 錯值 0(v0104 · 基本資料 PASS 193 OCR 1 · 一標題四重點 PASS 64 OCR 4 · 年度 4,905:ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452)· ⑫ 4,653/4,905 · ⑫b 綠 · 註冊核對 全部登記成功(處理器 v0104);P1 U/I 選資料夾(9 檔 → 個股 5)→ ⑥b 5 · ⑦ 5/5 · ⑪ 0(2,214 筆)· ⑫ 2,056/2,214;P2 U/I 選檔案(2 PDF + txt → 暫存夾)→ ⑦ 2/2 · ⑪ 0(848 筆);產業 / 其他 拒絕 rc 3;audit 綠 —— 與 v0134 同一組數字(無退步) | Chromium:既有 U/I 35/35 · 輸入區塊 14/14(一鍵情境頁) |
| 6 | 一鍵 | 沙盒一鍵 v0134(MAIN)→ v0135:一鍵程式碼雜湊相符 · ③ 舊啟動器 v0134 備份 · v0135 就位(雜湊相符)· 啟動器 ①~⑫ 綠(③ 環境檢查紅 = 沙盒 --no-install 仍缺 7 套件 · ② 船包 / ⑥c vrn2:// 灰 = 非 Windows;三者與 v0134 情境相同)· ⑦ 14/14 · ⑧ 完成 紅 0 黃 4 · ⑪ v0104 錯值 0 · ⑫b 綠 · 註冊核對 處理器 v0104 · ⑤b 黃(Linux 沒 HKCU)· ⑤c 黃(無瀏覽器)→ NEXT YELLOW rc 2(Windows 應 GREEN · U/I 自己跳出) | — |

---

## 7.0d v0133 → v0134(整合一支)

| # | Windows 實跑抓到的 | 做法(都在啟動器 v0134 內嵌的元件裡) | 實測 |
|---|---|---|---|
| 1 | 一鍵才處理 `VIA_NO_OPEN=1`,啟動器自己仍不開 U/I | 啟動器 `no_open` 只認 `--no-open` / `VRN2_NO_UI=1` | 自測:no_open 那行沒有 VIA_NO_OPEN |
| 2 | ⑨ 把內嵌舊版交接蓋掉倉裡較新的 | `_handover_land`:同版已在不蓋 · latest = 最高版號 | 自測:同版不蓋 · latest 跟 v0199 · 空夾落地內嵌版 |
| 3 | 處理器檔名規則取到最舊管理器 v0210 | 處理器 v0104 由大到小找 | 處理器自測 11 / 11 |
| 4 | ⑪ 基本資料「前兩頁沒有這個數」(MS / GS 現價 · 目標價印在第 3 頁或被字距拆開)| 驗證器 v0103 標籤旁看前 4 頁 · 一列去空白再找數字並映回位置 | 驗證器自測 · 容器回歸 容器同一本冊(14 份 · 4,905 筆) |
| 5 | ⑪ 一標題四重點「報告上漲空間不在原文標籤旁」×7 | 原文沒有上漲空間標籤 → 基本資料目標價 ÷ 現價 − 1 重算(容忍 0.6 點)相符就過 · 註記推算 | 驗證器自測 |
| 6 | ⑪ 原文句覆蓋 78 ~ 83% · 標題 75% | 兩邊去標點再量一次取高者(字本身仍要在原文) | 驗證器自測 |
| 7 | ⑪ BADITEM 23(MS ModelWare 科目寫法 `(NT $ mn)` · `EPS (NT$)**`)| 科目名去 * † $ 括號引號再比(BADITEM 與科目列兩處) | 驗證器自測 |
| 8 | ⑪ FAIL 1(Daiwa PBR n.a.)| 空值記號原文找不到 → NILVAL 不算錯值 | 容器回歸 |
| 9 | 沒動(照實說)| DUPKEY 82(同鍵不同值)· 標籤對調 3 筆 · MS-6669 ModelWare EPS → 擷取 / 摘要器下一輪 | — |

一鍵 v0134:沙盒一鍵 v0133 → v0134:一鍵程式碼雜湊相符 · ③ 舊啟動器 v0133 備份 · v0134 就位(雜湊相符)· ①~⑫ 全綠(⑦ 14/14 · ⑪ v0103 錯值 0 · ⑫b 綠 · 註冊核對 處理器 v0104)· ⑤b 黃(Linux 沒 HKCU)· ⑤c 黃(無瀏覽器)→ NEXT YELLOW rc 2(Windows 應 GREEN · U/I 自己跳出)

## 7.0c v0132 → v0133(前後端連結 · U/I window I/O 輸入)

| # | 需求 / 發現 | 做法 | 實測 |
|---|---|---|---|
| 1 | 用 ActivateVRN-2.ps1 啟動前後端並連結 | 一鍵 v0133 = 取得啟動器 → 執行 ①~⑫(前端 U/I · 後端 vrn2:// 處理器 + 啟動器)→ **⑤b 連結檢查**(HKCU 的 vrn2:// 解析成 python + 處理器 · 處理器整條路徑 = 本機 VRN-2 程式夾的 `VRN2_UIAction_v0103.py` 且檔在 · python 檔在 · U/I 有輸入區塊 · 印目前輸入與稽核 · **燈併進最後 NEXT**:紅 → 紅 · 黃 → 最多黃)· `$env:VRN2_SOURCE` 直接指定來源夾 | 一鍵 v0133 沙盒情境(從 v0132 升級 · 雜湊核對 · ①~⑫ · ⑤b 前後端連結檢查 · ⑤b 併進 NEXT):Linux 上 NEXT YELLOW(HKCU 沒註冊 · Windows 應 GREEN)· 見 VRN2_Verification_v0133.md §4 / §4b |
| 2 | 在 HTML 上用 window I/O 輸入檔案夾或檔案(pdf / word / txt / image / 檔案夾)| 處理器 v0103:`vrn2://pick` 開 Windows 原生對話框(FolderBrowserDialog / OpenFileDialog 多選 · STA · tkinter 備援)· 多檔複製到暫存夾 · 稽核 · `VRN2_Input_latest.json` · U/I 區塊更新 · 重開 U/I | 處理器自測 11 / 11(解析 · 型別表 = ENG397 EXT · 稽核分類 · 選資料夾 / 選檔案暫存 · 拒絕未開放 · 取消 · --set-source · v0102 動作照舊) |
| 3 | 分三種:個股報告/訊息 · 產業報告/展望 · 其他投資報告;現在只做個股,其他關閉 | U/I 三個 radio(只有個股可選 · 另外兩類 disabled「尚未開放」)· 處理器收到 cat=industry / other 一律拒絕(rc 3)· 稽核的「範圍外」= 管理器 v0231 同一條檔名規則 + 上輪判定 | U/I 真瀏覽器 輸入區塊真瀏覽器(Chromium)14 / 14 × 3 頁(A1 · P1 · P2):只有一塊 · 三類 radio(個股已選 · 另外兩類 disabled 且點不動)· 三個 vrn2:// 按鈕 · 稽核文字 · 在 190px 面板內、「這次不上船」之後「開啟」之前 · 原 4 個動作不變 · 分頁腳本照常 · 手機寬度 · 無腳本錯誤;既有 U/I 實測(35 條)A1 頁見驗證紀錄 |
| 4 | 選好的輸入要真的被用到 | 啟動器 ②b:U/I 選的 → 寫新一版 VRN2_SSOT(只增)→ 管理器 vrn2scope 讀它(管理器不動)· 貼包第一段就印來源與稽核 | 沙盒:選子集 6 PDF → ⑥b 範圍夾只剩 5 份 · 選 2 PDF + 1 txt → 來源 = 暫存夾(見 §6)|
| 5 | 留意是否都有註冊成功 | ⑥c vrn2:// 寫完讀回核對(不同 → 黃)· 貼包「註冊核對」一行(⑤ 元件登記 · ⑥c 協定 · ② 定位登記)· NEXT 未全綠會說 | 啟動器自測 啟動器 --selftest 31 / 31(多 4 條:內嵌處理器 v0103 · 處理器自測 · 步驟次序 · ②b 來源寫 VRN2_SSOT / 設定檔還沒寫也能稽核) |
| 6 | 非 PDF(word / txt / 影像)| 對話框與稽核都收;主體(ENG397 / vrn2scope)只擷取 PDF → 照實記「已收下 · 本版主體只擷取 PDF」,不假裝有處理;要真的擷取 Word / TXT / 影像是主體的下一輪 | 稽核行:非 PDF n(已收下 · 本版主體只擷取 PDF)|
| 7 | Codex #550(P1 / P2):一鍵最後的燈沒把 ⑤b 算進去(vrn2:// 沒註冊也 GREEN / rc 0)· 處理器只比檔名(舊的 / 搬走的檢出也算接上)| ⑤b 併進 NEXT(紅 → 紅 · 黃 → 最多黃 · GREEN / rc 0 只在前後端真的接上 + 有輸入紀錄)· HKCU 指令解析成 python + 處理器 · 整條路徑正規化後比對 + 檔在(或那一夾有啟動器本輪寫的 `VRN2_UIAction_Config.json` v0133)· python 檔在 · 訊息寫明要的是哪一條路徑 | 單元測試 19 / 19(pwsh · 從 ps1 抽出 Chk5b 與 $lamp / $msg 原文 · 正確 → GREEN rc 0 · 同檔名別的檢出 / 不存在 / v0102 / python 不在 / 沒引號 → RED · 沒註冊 → YELLOW rc 2 · 沒輸入紀錄 → YELLOW · .. 正規化 / v0133 設定檔 / python 別夾 → GREEN)· Linux 沙盒一鍵重跑:①~⑫ 全綠 · ⑤b 黃(HKCU 沒註冊)→ NEXT 由 GREEN 變 YELLOW「vrn2:// 沒註冊 … 把 ⑤b 那兩行貼回」(誠實 · 143 秒)· 一鍵程式碼 SHA-256 21ab900abfd0 |
| 8 | Codex #551(P2 ×2):一行(boot)的早退 `return` 讓 rc 變 0 · ⑤b 沒檢查 `"%1"` | boot 三個紅燈 `exit 1` · 一鍵四個早退紅燈先設 `$global:LASTEXITCODE = 1` · ③ 缺 zip / 發行冊 → 紅燈 · boot `try / catch` 例外 → RED rc 1;`Chk5b` 第三段必須是 `%1` 才綠 | boot 三個紅燈 return → exit 1 · 一鍵四個早退紅燈先設 LASTEXITCODE 1 · ③ 缺 zip / 發行冊 → 紅燈 · boot try/catch 例外 → RED rc 1;⑤b 第三段必須是 "%1";單元測試 22 / 22 · boot 失敗路徑 (a)~(e) 全 rc 1 · 最終一鍵程式碼 SHA-256 149832822f95 |
| 9 | 操作員 Windows 實跑(C:\測試樣本報告):U/I 沒跳出來 —— VIA 的 PS 設定檔把 `VIA_NO_OPEN=1` 設在環境,啟動器尊重它 | 一鍵跑啟動器前拿掉 `VIA_NO_OPEN`(結束還原)· 啟動器紀錄仍寫「沒有自動開啟」就 ⑤c 一鍵 `Start-Process` 開 U/I · `$env:VRN2_NO_UI = 1` 才不開 | 操作員 Windows 實跑 2026-10-21 13:06(C:\測試樣本報告 · 534 檔 · 個股 55):②b 綠 · ⑥c 綠(HKCU 讀回相同)· ⑦ 55 份 綠 44 黃 11 紅 0 · 四項 52 全綠 · ⑧ 完成 · ⑨ 上船 51fd0421e · ⑪ 黃(FAIL 9 + 12 · 年度 11,513 錯值 106)· ⑫ 灰(本機 VIA-VDF-VRN 沒 pull)· 註冊核對 全部登記成功 · ⑤b 綠(整條路徑 · 帶 %1 · pythonw)· U/I 沒自動開(VIA_NO_OPEN=1 來自 PS 設定檔)→ 一鍵 ⑤c 代開 · 程式碼 71bb2c9e228d |
| 10 | Codex #559(P2 ×2):`VRN2_NO_UI=1` 沒真的讓啟動器不開 · 啟動器「開不了」沒代開 | `VRN2_NO_UI=1` → 替啟動器設 `VIA_NO_OPEN=1`;⑤c 把「開不了」也納入代開;一鍵也開不了 → NEXT 最多 YELLOW | VRN2_NO_UI=1 → 替啟動器設 VIA_NO_OPEN=1(結束還原)· ⑤c 把啟動器「開不了」也納入代開 · 一鍵也開不了 → NEXT 最多 YELLOW · 單元 23 / 23 · 一鍵程式碼 0f9af29a5bf2 |

## 7.0b v0131 → v0132(借不到時說清楚下一步)

| # | 需求 / 發現 | 做法 | 實測 |
|---|---|---|---|
| 1 | FACILITATE:VRN-1 的倉在、但那一版沒有工具冊(VRN-1 main 還沒合併第十三輪)→ v0131 的 ⑫ 只說「找不到 VRN-1 的工具冊」,沒說要做什麼 | 工具橋 v0101 找 VRN-1 時記下「有 `functional modules\VRN\VRN_Main_v0100.py` 但沒有工具冊」的那一個倉 → 灰燈的說明印出 `cd <倉>; git fetch origin; git switch claude/optimistic-goodall-yhalc5`(已合併進 main 就 `git pull`)| 工具橋自測 15/15(隔離的暫存倉:有 MAIN 沒工具冊 → 說明裡有 git switch)|
| 2 | FACILITATE:VRN-1 的檔換過、工具冊沒重寫(sha256 不符)| 灰燈說明多一句:在 VRN-1 倉 `functional modules\VRN` 跑 `python VRN_Main_v0100.py build`(VRN-1 自己的 MAIN 重寫它自己的工具冊)| 自測:改一個位元組 → 不借 · 說明有 build 指令 |
| 3 | VRN-1 第十四輪(VRN-1 自己的 MAIN · PR tonykuni/VIA-VDF-VRN#79 的 Codex 三條)| VRN-1 那邊修(科目括號只去單位 · 代號要在代號的位置 · 組合段落要同一頁依序的原文片段)· VRN-2 借的 `table.pivot_db` 檔沒變(工具冊 sha256 相同)| 沙盒樹(倉內 19 份 · 個股 14)· **OCR 隔離環境是真的**(Python 3.11 · rapidocr · 只在暫存區):A 連跑兩次 → ② 借出工具冊 `section.near` / `ocr.image` 都能用 · ⑦ **14 / 14 全綠**(v0131 沙盒沒有 OCR 環境時是 13 綠 + MQ-1560 影像 PDF 首頁紅)· ⑧ 完成 紅 0 黃 4(v0131:黃 7)· ⑪ 錯值 0(年度數據 4,905 · OCR 欄位標 OCR)· ⑫ 綠 事實 4,653 / 4,905 · 年度 1,060 列 · 衝突 18 · 兩次指紋相同 `f4fb28bf836fcfb3`(冪等)· B:VRN-1 = main 工作樹(沒有工具冊)→ ⑫ 灰 + git switch 指令 · VRN-2 照常完成 · C:不借 → ⑫ 灰 · 照常完成。 |

## 7.0 v0129 → v0131(工具相互取用)

| # | 需求 / 發現 | 做法 | 實測 |
|---|---|---|---|
| 1 | 操作員:VRN-1 / VRN-2 工具可相互取用 · 兩個獨立 MAIN · 主體邏輯不變 | 兩邊各寫各的工具橋(VRN-2 `VRN2_ToolBridge_v0100` · VRN-1 `VRN_ToolBridge_v0100`)· 各自的工具冊(`VIA_ToolManifest/1`:檔 · sha256 · 入口 · 契約 · 能不能用)· 借之前逐檔核對 · 依路徑載入、獨立模組名 · 載入時不寫 __pycache__ · 只寫自己的輸出夾 | 工具橋自測(sha256 不同 → 不借 · 對方標不能用 → 不借 · 找不到 → 只用自己的)|
| 2 | 還原後表格可改為資料庫形式 PIVOT | ⑫ 借 VRN-1 的 `table.pivot_db`:VRN-2 年度數據冊 → 契約 `VIA_PivotFacts/1`(VRN-2 這邊自己對欄位:科目照原文 · 段落 › 科目 [子欄] · 同一張表同一個科目字好幾列 → 加 #列號 · 期間 2025E / FY25A / 12/25E / Dec-25F / 2025CT → 年)· **只收 ⑪ 判對位的格**(冊指紋相同才用)→ SQLite / DuckDB / CSV / Parquet / HTML | 容器:事實 4,653 / 4,905 · 年度 1,060 列(表層 1,115)· 衝突 18(報告層 · sign 5 · value 13)· SQLite + CSV + Parquet + HTML(容器的 VRN-2 環境沒有 duckdb → 只寫 SQLite;有 duckdb 才寫 .duckdb 並和原生 PIVOT 逐格比) |
| 3 | 借給 VRN-1:段落標題 | `section.near`:VRN-2 第三讀法(pdfplumber 字詞框)+ v0239 `_sec_near`(本體不改)· 只餵科目欄起點以右的字(並排表左表的數值欄落在右表科目欄 ±40 pt 內 → 以前判成數據列、回空白 · MS 3661 第 10 頁)· 值不在科目那一列(轉置表 / 欄頭在上)→ 不定 | VRN-1 借去之後 G21 剔除 39 筆真錯(成長率 / 比率段落底下被歸成金額的值)|
| 4 | 借給 VRN-1:OCR | `ocr.image`:VRN-2 的 OCR 隔離環境(envs\vrn2_ocr · rapidocr)跑 VRN2_OCRBridge · 形狀同 VRN-1 的 OCR 結果 · OCR 的字照舊不進判讀 | 沙盒樹沒有隔離環境 → 工具冊標「不能用」· VRN-1 照實寫 REFUSED;照 ③b 另建隔離環境(Python 3.11 · rapidocr · numpy<2)後 → 工具冊標能用 · VRN-1 G23 借到 2 / 2 · P22 讀已知圖數字與拉丁字全中 · MQ-1560 影像 PDF 讀到 17,123 字 |

## 7a. v0128 → v0129

| # | 發現 | 修法 | 實測 |
|---|---|---|---|
| 1 | **輸出欄位逐欄稽核(SECTION)→ 並排表段落標題互相拿錯**:凱基 2637 第 5 頁左「財務比率」右「投資回報率」同一高度交錯、擷取成同一個區 → 段落標題規則(往上找只有科目字的列)跨到另一張表:左表 流動比率 / 速動比率 / 淨負債 → 右表公式項「1 - 營業成本/營業收入」· 右表 1 / (營業運用資金 · + 淨固定資產 · + 什項資產 · = 資本周轉率 · 營業利益率 · x 資本周轉率 · x (1 - 有效現金稅率) → 左表「每股資料分析」· = 稅後 ROIC → 左表「資產運用狀況」· 右表 - 銷管費用 · = 營業利益率 → 公式項(13 列 65 筆 · 值都對) | 管理器 **v0239**(薄尾):第三讀法(pdfplumber 字詞框)在**這張表的上下範圍**裡找科目那一列(起點前沒有緊接的字 · 有這一列的值的那一行優先 · 同一欄才依 ROW 排序)→ 上方**同一個科目欄**找這個 SECTION 字 → 找不到或是公式項(1 - … · = … · x …)→ 改成同一欄最近的段落標題(到期間表頭為止 · 沒有 → 空白 · 候選列不一致 → 空白)· 沒有表的範圍 → 不改 · 值一個都不動;驗證器 **v0102**:SECFAIL(pypdfium2 · 標題字要在科目上方同一欄 · 公式項不是標題 · 先定列再找值) | 管理器自測 10/10(英文版面同凱基 2637 第 5 頁)· 驗證器自測 18/18 · 整本冊試跑:只改這 13 列 65 筆 · 反向測試:65 筆放回 → v0102 全抓 · v0101 全漏 · 另一張表才有的標題 140 筆 → 全抓 · 原樣 SECFAIL 0 |

## 7b. v0127 → v0128

| # | 發現 | 修法 | 實測 |
|---|---|---|---|
| 1 | 使用者把 PowerShell 程式貼進 cmd → 全部被 cmd 拒絕 | 「cmd / PowerShell 都能貼的一行」:`powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand …` → 讀分支上的一鍵程式碼 → SHA-256 相符才執行(被改一個字 → 不執行) | 容器 pwsh 7.4 實跑 · 竄改測試 |
| 2 | **啟動器 ② 找不到 VRN-2 程式夾**:環境變數 VIA_ROOT 有設就只看它(指錯 → 找不到 · 不看預設路徑 · 不看自己的紀錄) | v0128 `locate()`:候選 VIA 根(VIA_ROOT 與其下 VeritasIntelligenceAnalytics · 交接報告的 VIA 根 · 本支所在夾 · 目前夾)· MAIN 成功紀錄 `VIA_Reports\vrn2\VRN2_Success_latest.json` 的鎖檔路徑 · git 倉裡找;多個候選 → 本機登記的 MAIN 管理器(`registry\VRN2_Module_Success_Register.json` 檔在且 sha 相同)→ 船包 / 交接紀錄的 manager_tail;② 印來源與登記版號(VIA_ROOT 被略過 → 黃)· 找不到 → 列出查過的地方 · 一鍵 PS 加 ③b 同樣定位 | 啟動器自測新增 1 項 · 容器 VIA_ROOT 指錯實跑 |
| 3 | 新電腦實測(從遠端 clone · 沒設 git 使用者):⑨ 黃燈只印「t your account's default identity.」(git 多行訊息取最後 160 字 · 開頭被切掉)· ② 寫「沒有登記紀錄可比對」(其實船包清單有寫管理器尾版) | `_git_why()`:git 失敗訊息濃縮成一行(沒設使用者 → 直接寫要跑的 `git config --global user.name / user.email` · 其他 → fatal / error / remote 那幾行)· ⑨ 提交 / 抓遠端 / 建提交 / 推送失敗都用它;② 新 clone 寫「船包清單的管理器 VRN_SystemManager_v0237.py 下一步依船包補回」 | 啟動器自測新增 2 項 · 容器新電腦 clone 實跑(沒設使用者 → ⑨ 黃 · 一行說怎麼設;設了 → ⑨ 上船) |
| 4 | **把 U/I「驗證過的輸出」逐格看一遍 → 3 列表頭被當數據**(凱基 2637 P5 現金流量表「NT$百萬 Dec-23A … Dec-27F」5 筆 · JP 2330 P20「Balance Sheet & Cash Flow Statement FY24A … FY27E」4 筆 · GS 6415 P2「Jul-25 Oct-25」Jan-26 / Apr-26 2 筆)· 獨立驗證器 v0100 判對位(表頭字本來就印在期間那一欄 → 位置檢查一定過) | 管理器 **v0238**(薄尾):值是期間字 / 科目整個是期間字 / 一整列的值都等於期間的年份 → 整列移剔除冊(理由「表頭列(…)· 不進年度數據」)· 獨立驗證器 **v0101**:同樣三條另查值的種類(HDRVAL · 跟讀法無關 · 整列都標) | 管理器自測 7/7 · 驗證器自測 17/17 · 反向測試:11 筆放回 → v0101 全抓 · v0100 全漏 · 混進整本冊 → 一般列不誤標 · 年度數據 4,916 → 4,905 · 剔除冊 733 → 744 · ⑪ 錯值 0 |

## 7c. v0126 → v0127

| # | 發現 | 修法 | 實測 |
|---|---|---|---|
| 1 | U/I 只有計數與摘要,看不到驗過的每一個值 | v0237:第一個分頁「驗證過的輸出」· 全部檔案總表 → 選一份 → 基本資料(值 · VRN-2 狀態 · 獨立驗證)· 一標題四重點 · 年度數據格子(列 = 段落 · 科目 · 列號 · 欄 = 期間 · 子欄)· 每格值 + 徽章 · 滑鼠看細節 · 搜尋 · 只看待核對 · 下載 CSV · 資料內嵌(「<」跳脫) | U/I 35/35 |
| 2 | 獨立驗證在 PS 裡另外跑,U/I 看不到結果 | 獨立驗證器內嵌啟動器(`VRN2_IndependentVerifier_v0100.py` 落地 · 進船包)· ⑦ 之後背景跑(與 ⑧⑨⑩ 同時)· 判決依冊內序號寫回 U/I · 冊指紋(7 欄 SHA-256 前 16 碼 · 兩邊各自實作)相同才套用 · 寫回後才開 U/I | ⑪ 綠 |
| 3 | **驗證器 v3 只看「值在期間那一欄」:科目列與下一列(14pt 內)的字一起找 → 別一列的值也算對**(反向測試 3,000 筆漏 2,917)· 子欄只比數值序列不看科目 · 季度段同期間字 | v0100:先定「這個科目那一列」(科目字要相同 · 不是只含:EPS ≠ EPS growth)· 值只從那一列找(科目列沒有數值才看鄰列 · 互為最近)· 並排表到下一個科目字為止 · 值離別的期間表頭更近 = 不是這一欄 · 表頭同期間印兩次只用年度那個 · 子欄那一列的科目要相同 · 同一格兩筆 = DUPROW | 漏抓 0 |
| 4 | 驗證器基本資料只查「原文有這個數」:目標價與股價對調也會過 | 目標價 / 報告日股價 / 上漲空間要在自己的標籤旁(同一列值左邊最近的標籤 · 或上下兩列)· 評等要在前兩頁(定義頁每種評等都有)· 重點裡的目標價 = 基本資料 · 原目標價在「from / 原 / 前次」那一列 · 倍數印成「16x / 16 倍」· EPS = 年度數據同年度 | 反向測試 0 |
| 5 | **凱基財務比率表整列漏掉**:擷取把「流動比率 (x) 0.6 0.8 1.0 1.1 1.5」塞進第一格 · 其他格空白 → 被當段落標題 · 13 列 65 個值不在主冊也不在剔除冊 · 後面的列 SECTION 是那串數字 | v0237:第一格 = 科目 + ≥2 個值 → pypdfium2 與 pdfplumber 各自找到這一列(科目整個相同 · 值序列一個不多一個不少 · 只在本區上下範圍內)· 各自往上找值範圍內的表頭對欄 · 兩邊對出的 {期間: 值} 相同才收 · 段落標題改回 | +65 · 全部獨立驗證 ALIGNED |
| 6 | **9 對完全重複的列**(凱基季度段與年度段同一個期間字 · 兩格同值「-」/「(1)」→ v0236 分不出哪一格是季度)| v0237 同列同期間同值只留一筆 · 其餘移剔除冊 · 驗證器加 DUPROW | v0126 輸出被驗出 18 筆 → v0237 0 |

(v0126 的 6 項 · v0125 的 9 項 · v0124 的 11 項 · v0123 的 8 項 · v0122 的 15 項見各版交接報告第 7 節。)

---

## 8. 已知問題與待辦(依優先序)

| 0 | **(v0146)** 桌機跑 v0146(本地實測一輪的一行 · `VRN_ROUND_NO_SHIP=1` 只測不推):看 ⑥e(共用夾有 MarketFetch v0112 · via_tw_fetch 環境有 yfinance 才綠)· ⑥f(引擎要 yfinance + 網路;`--preflight-only` 可先驗)· ⑬b(⑥e 綠才有歷史)· ⑬c(輸出夾旁有舊 CSV 才問)· Workbench 左欄輸出夾格 / 第一區 / 雙語表頭 / 千分位;貼回 zip 多收 HistoryAlign / Integrate / market / consensus / Combined | 貼回 zip |
| 0a | **(v0146)** 金額欄「沒標單位視為百萬」是前端顯示假設(FinancialData 沒有單位欄):真要對,⑬b 對上歷史後 FinancialAligned 的 VALUE_FINAL 才是確定單位;下一輪可把 UNIT_FINAL 併回主冊顯示 | 下一輪 |
| 0b | **(v0146)** 輸出冊 969 秒(第二讀取器回查)與 ⑪ 833 秒還沒動;CPU 被別的程序佔時啟動器只能降路數 | 看下一次貼回的階段耗時 |
| 0c | **(v0146)** ⑥f 共識引擎的 DuckDB 歷史長表(consensus_history.duckdb)在 `VIA_Reports\vrn2\consensus`;⑬ 增量庫還沒把 Combined / FinancialAligned / Deleted 三冊鏡像進 OutputStore(它只收四本冊)| 下一輪 OutputStore v0101 |
| 0 | **(v0145)** 桌機跑 v0145(本地實測一輪的一行 · `VRN_ROUND_NO_SHIP=1` 只測不推):看 ⑦ 的 `[計] 階段 · … · 耗時` 與 `[計] 冪等閘 · R1 完成 · 耗時`,再看收尾 `[計] 階段耗時` 一行 —— 這就是 2422 秒的拆帳;若冪等閘仍 > 300 秒,下一步是把它移到 ⑪ 同一背景 | 貼回 zip |
| 0a | **(v0145)** 上傳 `VRN2_PasteBack_20261029_081428.zip`:修 3014TT POINT_3 FAIL 1 與 3 份年度數據缺項(Daiwa-6278 · 欣銓 3264 · 華南 6143)要它裡面的四點核對 json 與 PDF | 上傳 |
| 0b | **(v0145)** ⑪ 獨立驗證 691 秒(11513 筆 · 6 路)與 ④ 加速器掃描兩遍 92 秒還沒動;OneDrive 夾 I/O 沒量 | 看階段計時再決定 |
| 0 | **(v0144)** 桌機已跑 v0144(08:14):貼本地實測一輪 v0100 的一行(已改指操作員一鍵 v0105 → VRN-2 一鍵 v0144)→ 看 ⑤b SSOT-ID(待核號 N · 衝突 0)· ⑬(灰 = 沒選輸出夾 → Workbench 匯出分頁「選擇輸出夾…」或 `$env:VRN2_OUTPUT_DIR`;黃 = 沒裝 duckdb → `pip install duckdb`)· 處理器 v0108 註冊 | 貼回 |
| 0a | **(v0144)** VCGC 側核發冊還沒實作(契約在 `VIA_SSOT_ID_Protocol_v0100.md` §3):VCGC 那一線要讀 `functional modules\VRN2\contract\VRN2_NUMBER_REQUEST_latest.json`、寫 `VCGC_NUMBER_GRANT_latest.json`(放 `<VIA>\VCGC\contract\` 或 `<VIA>\VIA_Reports\vcgc\`);VRN-2 不代寫 | VCGC 線 |
| 0b | **(v0144)** 瀏覽器拿不到拖進來的資料夾真路徑(安全限制):拖曳區只當「開對話框」的入口;要真拖曳落地要 vrn2:// 處理器收 File System Access,下一輪 | 不改 |
| 0 | **(v0143)** 桌機 2026-10-29 第一次實跑:② ChainShip 紅(v0248 / v0253 不在桌機 VRN 夾)· ③ rc 1(兩個啟動器重疊 → 全逾時 → ⑤b 紅)· ① logo 黃 | 再貼本地實測一輪 v0100 的一行(已改指 ChainShip v0101 · 操作員一鍵 v0104 → VRN-2 一鍵 v0143 · 印章檔);把 `Downloads\VRN2_PasteBack_<時間>.zip` 上傳 |
| 0a | **(v0143)** 上一輪的 `VRN2_PasteBack_20261029_013350.zip` 還沒上傳:transcript 才能判第二個啟動器(01:35)從哪來、ChainShip ship rc 2 是推被拒還是同名不同內容 | 上傳那個 zip |
| 0b | **(v0143)** recover 若印 `[FIND?]`(同名兩份不同內容)→ 貼回那兩行,我判哪份是鏈上的;`[FIND-]` → 那條線的前版沒生成,桌機線要重出 v0248 / v0253 | 看 ② 的輸出 |
| 0c | **(v0143)** 桌機四點原文核對 FAIL 1(PASS 203 · OCR 4)與 ⑧ 黃 4(缺項 3 份年度數據:Daiwa-6278 · 欣銓 3264 · 華南 6143)還沒修:要貼回包裡的 `VRN2_VerbatimVerify_latest.json` 與輸出冊 | 上傳 zip |
| 0 | **(v0141)** 獨立驗證 ✗ 45(6933 AMAX 37 · 凱基 2891 8)與 神達 / GFHK / 欣銓 原檔不在容器:要操作員用 v0141 跑一次 `C:\測試樣本報告`,把 `VRN2_Closeout_v0141.json` + `IDEMPOTENCE_latest.json` + `verify_independent\*.digest.txt` 貼回 | 下一輪 |
| 0b | **(v0141)** 冪等閘若回 NONDETERMINISTIC:收據 `differences_rerun_vs_rerun` 第一個路徑就是擷取端非冪等的位置(ENG397 v0127 要出 v0128)| 看收據 |
| 0c | **(v0141)** MQ-1560 影像頁四點 OCR_PENDING 是設計(rc 2 黃);要綠需人工核對原圖 | 不改 |

| # | 項目 | 狀態 | 需要 |
|---|---|---|---|
| 0 | **使用者用 v0141 的一行跑**(`vrn2_release_v0141/VRN2_OneClick_v0141.md`)| 待執行 | 預期:③ 套件就位(逐檔核對)· ⑧ 完成 · 冪等 GREEN(或 STALE_RECORD → 自動第 2 輪)· 四點原文核對 PASS / MISSING / OCR · ⑪ v0110 · 貼回 `VRN2_Closeout_v0141.json` + `IDEMPOTENCE_latest.json` + digest(含 6933 / 2891 的 ✗ 證據)|
| 0b | **使用者用 v0136 的一行跑**(`vrn2_release_v0136/VRN2_OneClick_v0136.md`)| 待執行 | 預期:U/I 自己跳出 · ⑪ 用驗證器 v0105 → 「貼給 AI」會有 DUPKEY 的例子(每類至少 6 筆)、對調的 3 筆寫明哪種對調、MS-6669 EPS 寫出年度數據那一格 · ⑫a 自己把 VIA-VDF-VRN fast-forward 到 main → ⑫ 應轉綠(借到 PIVOT 工具)。貼回 ⑪ 驗證摘要 + ⑫a / ⑫ 兩行。 |
| 0c | **使用者用 v0135 的一行跑**(`vrn2_release_v0135/VRN2_OneClick_v0135.md`)| 被 v0136 取代(v0135 已合併 MAIN · 可跑,但 ⑪ 是驗證器 v0104、⑫ 要手動 pull)| 預期:同 v0134(U/I 自己跳出 · ⑪ 用驗證器 v0104 · 註冊核對 處理器 v0104);Daiwa PBR n.a. 那筆會寫「原文該格是 …」:空白 / 別的記號 → NILVAL · 數字 → FAIL 照實留。貼回 ⑪ 驗證摘要 + ②b / ⑤b。 |
| 0d | **使用者用 v0134 的一行跑**(`vrn2_release_v0134/VRN2_OneClick_v0134.md`)| 被 v0135 取代(v0134 已合併 MAIN · 可跑,但 ⑪ 是驗證器 v0103)| 預期:U/I 自己跳出(不用再管 VIA_NO_OPEN)· ⑪ 基本資料 / 一標題四重點 FAIL 從 9 + 12 降(現價 / 目標價頁位 · 上漲空間推算 · 覆蓋去標點)· BADITEM 23 → 0 · NILVAL 1 · DUPKEY 82 照舊待看原文 · ⑨ 不蓋交接。貼回 ⑪ 驗證摘要 + ②b / ⑤b。 |
| 0e | **使用者用 v0133 的一行跑**(`vrn2_release_v0133/VRN2_OneClick_v0133.md` · 可存成 `ActivateVRN-2.ps1`)| **已執行 2026-10-21 13:06(C:\測試樣本報告 · 534 檔 · 個股 55 · ②b / ⑥c / ⑤b / 註冊核對全綠 · ⑦ 綠 44 黃 11 紅 0 · ⑪ 黃 106 筆待核對 · U/I 沒自動開 → ⑤c 修)** | 預期:②b 輸入來源 綠(預設 `C:\測試樣本報告` 或 `$env:VRN2_SOURCE`)· ⑥c vrn2:// 讀回核對相同 · ⑫b U/I 輸入區塊 · ⑤b 前後端已連結(整條路徑 · 檔在)· NEXT 綠(⑤b 不綠 NEXT 就不綠);然後在 U/I 按「📁 選擇檔案夾…」選 `C:\測試樣本報告` → 區塊顯示稽核 → 「▶ 完整重跑」。貼回 ②b / ⑥c / ⑫b / 註冊核對 / ⑤b 幾行。 |
| 0b | **VRN-1 合併 PR tonykuni/VIA-VDF-VRN#79**(另一團隊的倉 · 第十三 / 十四輪 · 操作員決定)| 待操作員 | 合併(或切到該分支)後 VRN-1 的工具冊就在 → VRN-2 ⑫ 才借得到;VRN-1 跑 MAIN 時 G23 借 VRN-2 的段落標題(先跑過一次 VRN-2 v0131,工具冊才在)|
| 1 | 使用者用 v0129 的一行再跑(cmd / PowerShell 都能貼 · v0128 那一行也還能用 · 只是少了段落標題修正) | 待執行 | 預期:一鍵程式碼雜湊相符 · ③b / ② 印出程式夾來源與登記版號(本機上次成功 v0235)· 落地 v0236 → v0237 → v0238 → v0239 + 獨立驗證器 v0102 · ⑧ 完成 · ⑪ 綠 · U/I 自動跳出時第一個分頁就是「驗證過的輸出」· **貼回 ② / ③b / ⑨ / ⑪ 那幾行 + 驗證摘要**(52 份 · 新驗證器第一次在使用者機器跑 · 有 ✗ 格先看原文再判) |
| 2 | 使用者機器其他 P1 黃燈(260914_daiwa_aspeed · GFHK Apple · 南亞 · 啟碁)| 不在容器 | 看 ⑪ 摘要與 U/I ✗ 格 |
| 3 | 期間下有子欄、表頭在表外的表(華南 P4 銷售金額 / 占比)· 季度表 | 不收(剔除冊帶理由) | 若要季度數據 → 另開季度冊 |
| 4 | 一標題四重點 3/4 · MQ-1560 影像 PDF 標題 | 待 OCR / ENG062 | — |
| 5 | ADJ CLOSE · 中文名稱 · `.TW/.TWO` | 待 VDF | — |
| 6 | envcheck「缺必裝」superextract / via-nlp-engine(PyPI 沒有)| 不是 VRN-2 的檔 | 不補裝 |
| 7 | 使用者自己 pull 時船包檔衝突 | `* -merge` 整檔衝突 | `git checkout --theirs -- docs/handoff/ai/vrn2_ship` |

---

## 9. 收尾進度

| 交付項 | 狀態 |
|---|---|
| FILENAME / 首頁 / 年度財報 / 評價資訊 | ✅ 使用者 52/52 全綠(第 39 輪) |
| 年度數據 | ✅ 主冊只留兩個讀取器對得上的年度值 · 一格整列拆開 · 重複列只留一筆 · 🟡 剔除冊帶理由 |
| 一標題四重點 | 🟡 51/52 綠 |
| 輸出驗證無誤 | ✅ 容器三本冊錯值 0(驗證器 v0102 · 反向測試漏抓 0 · 表頭列 0 · 段落標題 0)· 🟡 使用者機器待 v0127 ⑪ 摘要 |
| **HTML U/I 上看得到驗證過的輸出** | ✅ 第一個分頁 · 每格值 + 徽章 · 指紋相同才套用 |
| **還原後表格 → 資料庫形式 PIVOT**(v0131)| ✅ 容器(借 VRN-1 工具 · 只收 ⑪ 判對位的格)· 🟡 使用者機器待 VRN-1 patch |
| **工具相互取用 · 兩個獨立 MAIN**(v0131)| ✅ 兩邊工具冊 + sha256 核對 · 本體不改 |
| 完成後上船 GitHub | 🟡 v0125 起只送船包(使用者機器 ⑨ 結果還沒貼回) |
| 指令接加速器 · 第一步 CPU / DRAM · 平行段 · 驗證背景平行 | ✅ |

---

## 10. 執行方式(v0146:貼 `docs/handoff/ai/VRN2_LocalRound_v0100.md` 頂端的一行(logo → ChainShip v0101 補船 → 操作員一鍵 v0107 → VRN-2 一鍵 v0146 → 貼回包);各關一步 `VIA_VRN2_NO_MARKET / NO_CONSENSUS / NO_HISTORY / NO_INTEGRATE = 1`;擷取 Python `VIA_FETCH_PY`;前一版 v0145:貼 … 操作員一鍵 v0106 → VRN-2 一鍵 v0145 → 貼回包);只測不推先 `$env:VRN_ROUND_NO_SHIP = '1'`;冪等閘並行路數 `$env:VRN2_IDEM_LANES`(預設 3);前一版 v0144:或單跑 `vrn2_release_v0144/VRN2_OneClick_v0144.md` 的一行;輸出夾:跑完在 Workbench 匯出分頁按「選擇輸出夾…」(或 `$env:VRN2_OUTPUT_DIR = 'C:\Users\<你>\OneDrive\VRN2_out'` 再貼一次)· 增量庫要 `pip install duckdb`;前一版 v0143:貼同一行(當時指 操作員一鍵 v0104 → VRN-2 一鍵 v0143);或單跑 `vrn2_release_v0143/VRN2_OneClick_v0143.md` 的一行;前一版 v0141:貼 `vrn2_release_v0141/VRN2_OneClick_v0141.md` 的一行;或 `python <套件夾>\ActivateVRN-2_v0141.py --source C:\測試樣本報告`;`$env:VRN2_NO_REPASS=1` 不自動再跑)

一鍵 v0141(③ 取套件 `VRN2_Closeout_v0141.zip`:雜湊 + `PACKAGE_SHA256.json` 逐檔 · 本機已有也逐檔對已驗證的 zip,不同就重新解壓 → ③b 定位(VRN2_ROOT / VIA_ROOT)→ ④ `ActivateVRN-2_v0141.py`(①~⑫ · ⑧ 冪等閘 STALE_RECORD 自動第 2 輪 · 四點原文核對 → 收據)→ ⑤ 摘要(⑧ · ⑧b 收尾收據 · 冪等閘 · 獨立驗證摘要)→ ⑤b 前後端連結(處理器在 functional modules\VRN2)→ NEXT 燈 = ⑧ + 啟動器 rc + 獨立驗證 + ⑤b):`docs/handoff/ai/vrn2_release_v0141/VRN2_OneClick_v0141.md`(舊版 v0133 ~ v0136 的一行仍可跑,但走的是單檔啟動器,沒有本輪的冪等分類 / 四點補齊 / 驗證器 v0110)

- 不借 VRN-1 的工具:`$env:VIA_VRN2_NO_BORROW = '1'` · VRN-1 不在預設位置:`$env:VIA_VRN1_ROOT = '<VRN-1 倉>'`
- 只實測不上船:PS 檔頭 `$NoPush = $true` · 不跑獨立驗證:`$env:VIA_VRN2_NO_VERIFY = '1'` · 驗證平行路數:`$env:VRN2_VERIFY_PAR = '2'` · 驗證等待上限:`$env:VIA_VRN2_VERIFY_WAIT = '3600'`。
- 新電腦:clone repo → 跑一鍵 PS(② 自動依船包補回 VRN-2 檔 · 含獨立驗證器)。
- U/I 打開後:左上「驗證過的輸出」→ 總表點一份 → 往下看三本冊 · 格子綠 ✓✓ = 兩層都對位 · 有 ✗ 先看滑鼠提示的理由與原文頁。

---

## 10b. 結案輪(2026-10-29 · 操作員:「將所有相關未修復衝突全部修復完 結案」· PR #571 / #572)

| # | 現況 | 根因 | 做法 | 證據 |
|---|---|---|---|---|
| 1 | #571 與 #572 | 檔案零重疊、無文字衝突(`git merge-tree` 乾淨) | 先合 #572(f9ea8805:還原被 VRN-2 auto-merge 蓋掉的 68 檔 + VDF 盤點文件),#571 再合 main(a2b564cf8) | 合併無衝突 |
| 2 | CI VRN job 紅 | `VRN2_ChainShip check` MISSING 2:v0249 / v0254 的釘名前版 **v0248 / v0253 從未進倉**(任何分支 · 任何 zip · 桌機 VRN 夾都沒有;桌機 01:33 `ship` 後仍缺)→ v0254 一載入就 FileNotFoundError | **補環** `VRN_SystemManager_v0248.py`(直通 v0245)· `v0253.py`(直通 v0249 + v0254 從原 v0253 接來的六個名稱 `_blank` `_status_append` `_fill_analyst` `_fin_v2_shape` `_summ_status` `blank_audit`,依 v0254 呼叫處還原最小語意;Headers V3 的 `HEADERS_V3` 只從桌機 SSOT 冊 `SSOT\VRN2_BasicInfo_Headers_v0100.json` 讀,冊不在就空、不手編 39 欄);檔頭寫明「不宣稱原檔內容」;CI 鏈檢查黃(引用冊只在桌機)不再算失敗 | ChainShip check `MISSING 0 · 引用冊缺 8` YELLOW · v0248 自測 8/8 · v0253 11/11 · v0249 `provenance --selftest` 4/4 |
| 3 | CI VDF job 紅(VCGC 閘 `GATE why ["VRN"]`) | CGC_MDL223 v0102 要每系統**最新尾版檔面**有 `def main` / `def selftest`(`VIA_FROM_VCGC` 可沿 PRIOR 鏈繼承 → VRN 鏈到 v0123);桌機線尾版 v0254 的 main 是 `_rebind(getattr(PRIOR,"main"))`,檔面沒有 `def main` → VRN 列 RED → `via-vcgc run` 全擋 | 新尾版 **`VRN_SystemManager_v0256.py`**(釘名 v0254 · 檔面 `def main` / `def selftest` · `__main__` 收 `--selftest` · 不加 VIA_FROM_VCGC 守門,VRN-2 仍獨立)· 三支新檔帶 `[VIA:ACCEL-BRIDGE]` 標記 | 容器 `via-vcgc run VDF_SystemManager --selftest`:閘放行(不再 GATE),接著跑 VDF 自測(容器沒 duckdb 才停;CI 有裝)· v0256 `logic` rc 0 · `provenance --selftest` 6/6 |
| 4 | 號 | v0255 = 私有 runtime 線(ActivateVRN-2 v0145 · 釘名 v0243 · 只在 runtime zip);共用夾桌機線接 v0256 | 兩線分開寫在 §11 規則 | — |

**沒有宣稱 / 桌機要做的**:桌機線的 v0246 / v0247(MarketFetch · V2 規範)與 SSOT 三冊 + `VRN2_BasicInfo_Headers_v0100.json` 只在桌機(`VRN2_Handover_v0145.md` §3 §5);補環 v0248 直通 v0245,跳過 v0246 / v0247 的內容。桌機請先看 `functional modules\VRN\_archive_vrn2\` 有沒有原 v0248 / v0253 / v0246 / v0247,有就用 ChainShip `ship` 推上(同名不同內容會列 `[FIND?]` 交人判);之後可出 v0257 重新釘名到真正的前版。SDD 的 X-REG / X-NUM(註冊冊 · 編號)是 VCGC 的冊,`via-vcgc registry-sync --apply` / `CGC_MDL237 --apply` 要在閘開後由 VCGC 線跑,不在本 PR 代寫。

## 11. 給下一個 AI 的關鍵規則(本輪新增在前)

- **(v0146)** **顯示換算不改冊**:百萬台幣 / 千分位 / 雙語表頭都在瀏覽器端做(`cell()` / `hdr()`),輸出冊的值與欄名一字不動;匯出 CSV / JSON 仍是原欄名原值。單位判不出就寫「視為百萬」並讓使用者看得到原值。
- **(v0146)** **歷史覆蓋要先對上一期**:HistoryAlign 一期都沒對上就不覆蓋(黃),不拿單位猜;被否定的報告值進刪除區帶理由,主冊不改,對齊冊另出。
- **(v0146)** **整合絕不刪原檔**:DataIntegrate 只寫新檔;原檔先 sha → 新檔重讀核對 → 才複製到 TEMP;`--move` 也是核對過才搬。掃描後檔案被改(sha 不同)→ 不整合、要重掃。問過使用者「不要」的同內容不再問。
- **(v0146)** **借用的工具不進自己的夾改**:共用夾的 MarketFetch 只讀最新號;上傳的共識引擎原樣內附(sha 可核)、包裝在 VRN2_ConsensusJoin;引擎 `--fixture` 離線模式是測試用,正式要 yfinance + 網路。
- **(v0146)** **非關鍵步驟不轉紅**:⑥e / ⑥f / ⑬b / ⑬c 只灰 / 黃並寫原因;rc 仍由 ①~⑫ 關鍵步驟決定。
- **(v0146)** **薄尾包裝先存本尊**:`_native_x = PRIOR.x` 再 `PRIOR.x = wrapper`(Workbench v0102 的 logo_data_uri 第一版遞迴 992 層就是沒存本尊)。
- **(v0146)** 版號:Workbench v0102 · 處理器 v0109 · SSOTSync v0101 · 啟動器 v0146 · 操作員 v0107 · 交接 v0147;桌機線的號(處理器 v0105 / v0107 · 管理器 v0244 ~ v0254 · 交接 v0145)照舊跳過。

- **(結案輪)** **鏈斷到找不到原檔時,用「補環」接,不手編原檔內容**:補環 = 直通前版的薄尾 + 檔頭寫明不是原檔 + 原檔依賴的名稱依呼叫處還原最小語意並自測;規格正本在別處(桌機 SSOT 冊)就只讀不編。原檔日後出現 → `[FIND?]` 交人判,再出新版重新釘名。
- **(結案輪)** **VCGC 閘的針看檔面**:每系統最新尾版要有字面的 `def main` / `def selftest`;`_rebind(getattr(PRIOR,"main"))` 閘看不到。`__main__` 要收 `--selftest`(CI 用 `provenance --selftest`)。新 .py 帶 `[VIA:ACCEL-BRIDGE]` 標記,否則 SDD X-ACCEL 紅、啟動器 ④ 會出 v+1。
- **(結案輪)** 兩線版號:共用夾 `functional modules\VRN` 的 VRN_SystemManager 是桌機線(…v0254 → v0256);私有 runtime 線是 v0243 → v0255。出新版前 `chain VRN_SystemManager` 兩邊都看。

- **(v0145)** **慢先拆帳,不猜**:v0255 起 ⑦ 每階段有 `[計] 階段 · X · 耗時` 與收尾 `[計] 階段耗時` 一行(`VRN2_Phase_Timing_latest.json`);貼回來先看這一行,再決定動哪裡。桌機 08:14 的 1050 秒無輸出是推論(v0243 的 R*.log 在 GREEN 時被刪),v0255 的 timing 會證實或推翻。
- **(v0145)** **長時間子行程一定要有心跳**:管理器內部任何 > 30 秒的子行程迴圈要印進度(啟動器的沉默看門狗只認輸出)。
- **(v0145)** **冪等閘的並行只能跨檔、不能跨波**:同一份的 R1 / R2 不能同時跑(共用 OCR 快取會互寫);波內不同檔並行安全。
- **(v0145)** **版號跳過另一條線用掉的號**:管理器 v0244 ~ v0254、處理器 v0105 / v0107、交接 v0145 都是桌機線的;出新版前 `chain <家族>` 看兩線的號,釘名前版、不用 v-1 推。
- **(v0145)** 「GitHub 不影響」= GitHub 只當 git 遠端抓檔 + 核對雜湊;CI 紅綠不擋本機實測;`VRN_ROUND_NO_SHIP=1` 連補船都不推。

- **(v0144)** **SSOT-ID 不自己編**:VRN-2 的登記冊 `ssot_id` 只能從 VCGC 的核發冊補填;VRN-2 自己的號是 `proposed_no`(VRN2-xxx)。請求冊 `contract\VRN2_NUMBER_REQUEST_latest.json` 每輪重寫、核發冊只讀、補填一定出新版登記冊(舊版留著)· 狀態在 `contract\VRN2_NUMBER_STATE_latest.json`。衝突不自己挑,列給人判。
- **(v0144)** **輸出位置只從對話框 / 設定冊 / 環境變數來**:處理器不從網址讀路徑(同 v0133 輸入的規則);拖曳區不是真路徑來源。輸出夾在同步夾裡就是「雲端」,VRN-2 不接雲端 API。
- **(v0144)** **增量以原檔 SHA-256 為準,不以檔名**:同名不同內容 = 新檔;同內容再跑 = 0 追加。庫的真相在 `vrn2_store.duckdb`,Parquet 是分區輸出;沒 duckdb 用 pyarrow 備援(黃),不要在沒庫時假裝綠。
- **(v0144)** **處理器版號跳過桌機線用掉的號**(v0105 / v0107 是 publish 處理器):出新版前先 `chain VRN2_UIAction` 看兩條線的號。
- **(v0144)** 三系統的協作手冊(`VIA_SSOT_ID_Protocol_v0100.md`)是契約:改契約出新版號、三邊同時改;VRN-2 線不替 VCGC / VDF 寫實作。

- **(v0143)** **一台機、一個 VIA 根,同時只跑一個啟動器**:v0143 用 `VRN2_Launcher.lock` 擋;看到 `[RED] 單機閘` 就是有另一個還在跑(U/I 按鈕 · 另一個視窗 · 上一輪沒結束),等它結束再貼;不要用 `VRN2_FORCE_PARALLEL=1` 硬跑(2026-10-29 實跑:RAM 0.16 GB → ⑦ / ⑪ / ⑫b 全逾時)。
- **(v0143)** 子行程上限不寫死:`VRN2_UI_REFRESH_WAIT` / `VRN2_SILENT_MAX` / `VRN2_MANIFEST_WAIT` / `VIA_VRN2_VERIFY_WAIT` 從環境讀,下限 60 秒;桌機 OneDrive 夾慢,預設已放寬,不夠再調環境變數,不出新版。
- **(v0143)** ⑫b 的結果以 U/I 頁裡有沒有 `<!--vrn2-input-->` 區塊為準,不以子行程 rc 為準;子行程失敗就本支補放並在收據 `ui_block.how = in-process` 留痕。
- **(v0143)** 缺的薄尾前版先用 ChainShip v0101 `recover` 在本機找(VIA 樹 · 私有 runtime · 備份 · Downloads 的 VRN2_* 夾與 zip),**不手抄、不重寫前版**;找到兩份不同內容一律交人判。
- **(v0143)** 貼回的主控台文字不夠判「為什麼」(兩個啟動器交錯印在同一個視窗),要 `VRN2_PasteBack_<時間>.zip` 裡的 transcript.txt 與收據;先修後果(閘 · 上限 · 補放),原因等證據。

- **(v0141)** 另一團隊的收尾套件(v0137 ~ v0140 · 私有 runtime `functional modules\VRN2`)是現役入口:改 VRN-2 = 出新 runtime 成員 + 新入口版號,runtime 清單逐檔雜湊、舊成員一個都不少;不要再把元件 base64 內嵌回單檔啟動器。
- **(v0141)** 冪等閘三分類:GREEN / STALE_RECORD(清快取 · 啟動器自動再跑一輪)/ NONDETERMINISTIC(RED);RED 時先看收據 `context`(-I · fitz · PYTHONHASHSEED · 快取夾)與第一個差異路徑,再動擷取端。
- **(v0141)** 四點:缺句是 MISSING(待核對 · 黃),不是 FAIL;FAIL 只留給「有文字但第二讀取器讀不到 / PDF 換過 / 雜湊不對」。階梯補的點 evidence.selection = relaxed / line / page,仍是精確字串。
- **(v0141)** U/I 備援指令契約:升優先權 → PS 加速器 → PS7 模板 → `& $py $A`;不上船版帶 `VIA_VRN2_NO_PUSH='1'`。真瀏覽器測試(`ui_test141.js`)會查。
- **(v0141)** 不出 .ps1;一鍵 md 的 ③ 要核對套件雜湊 + `PACKAGE_SHA256.json` 逐檔。

- **錯值要全部看得到**:貼給 AI 的摘要每一類錯值都要出現(先各印幾筆再補滿),不能讓前面的類別把後面的擠掉 —— DUPKEY 82 筆隱形了一整輪。
- **同鍵不同值用位置證據分**:對位的那筆是對的、保留;不對位的才是錯值;分不出就兩筆都標。
- **借別的系統的倉前先同步它的 main(只 fast-forward)**:乾淨才動、不改寫歷史、不提交、不推;動了就把原分支名印出來。
- **驗證器放寬要看該格(Codex #561 / #562)**:空值記號(n.a. / - / NM)找不到不能直接 NILVAL,先用與 `_row_hits` 同一套規則定值列(值可能在鄰列)、對期間欄看原文該格是什麼(數字 → FAIL · 空白 / 別的記號 → NILVAL · 定不出 → FAIL);字距拆開的數字只接千分位逗點 / 小數點後的空白,空白分開的兩個數不黏。
- **已合併 MAIN 的版本不改**:修正一律出新版號(v0134 合併後 → v0135),發行夾 / 一鍵 / 交接跟著新版號;舊發行夾與舊版元件留著(只增不減),啟動器 ⑪ 取最新版。
- **全部整進一支**:操作員實跑抓到的事(U/I 不開 · ⑨ 回退 · 規則取錯版 · 驗證器的頁位 / 字距 / 標點 / 科目名 / 空值)都改在啟動器內嵌的元件裡(處理器 v0104 · 驗證器 v0103 · 啟動器 v0134),一鍵只是取啟動器 + 摘要 + 備援;下一輪也這樣,不要靠一鍵補主體的洞。
- **驗證器放寬只放「讀法」不放「值」**:前 4 頁、字距、標點、科目符號、空值記號都是讀法;值對不上(標籤對調 · DUPKEY 不同值 · ModelWare EPS)仍是 FAIL,照實留給擷取 / 摘要器。
- **⑨ 交接只增不回退**:內嵌交接同版已在就不蓋,latest 永遠指倉裡最高版號;要更新交接就出新版號檔。

- **GitHub 衝突與分支的交接**(2026-10-21 · PR #550 在 Codex 修正推上前就被合併 → 修正改走 PR #551;不改寫歷史、不強推、每次推之前先 `git fetch origin main` + `git merge-tree` 核對 0 衝突):詳細時間線、檢查方法、其他開著的 PR 狀態與規則見 `docs/handoff/ai/VRN2_GitHub_ConflictHandover_20261021.md`。
- **前後端連結是可驗的,不是假設的**:前端 = U/I 檔,後端 = vrn2:// 協定 + 處理器 + 啟動器;每次都要讀回 HKCU 核對註冊指向目前的處理器、U/I 檔裡要有輸入區塊,兩樣都在才叫「已連結」;**核對整條路徑不只檔名**(別的檢出 / 搬走的 / 不存在的處理器 → 紅)· **⑤b 的燈併進一鍵最後的 NEXT**(⑤b 紅 → NEXT 紅 · 黃 → 最多黃;vrn2:// 沒註冊就不能 GREEN / rc 0 —— Codex #550)。
- **輸入只從對話框與啟動器寫的設定來**:處理器不從網址讀路徑;U/I 選的落在 `VRN2_Input_latest.json`,啟動器 ②b 讀它寫 VRN2_SSOT,管理器照常讀 VRN2_SSOT —— 主體不動。
- **三類只開個股**:產業報告/展望 · 其他投資報告 在 U/I disabled、處理器拒絕;要開放是主體(範圍 / 擷取 / 驗證)的工作,不是把 radio 打開。
- **非 PDF 不假裝處理**:對話框收 word / txt / 影像,稽核照實記「本版主體只擷取 PDF」;真的擷取要改 ENG397 與 vrn2scope(下一輪)。

- **四系統各自獨立(操作員 2026-10-20 重申)**:VCGC · VRN-1 · VRN-2 · VDF 各有自己的 MAIN、各自運作、互不影響。工具相互取用只在執行時讀對方的工具冊與檔;對方不在、沒有工具冊、檔換過 → 自己照常跑完(灰 / 黃)。每一輪都要實測「對方不在」與「關掉借用」兩種情形各自跑得完。
- **借不到要說下一步**:灰燈不是終點 —— 說明裡要有操作員可以照貼的指令(切到有工具冊的版本 · 在對方的倉用它自己的 MAIN 重寫工具冊),不替對方改。
- **工具可以借,程式碼不照抄**:借 = 讀對方的工具冊 → 逐檔核對 sha256 → 依路徑載入(獨立模組名 · 不寫 __pycache__)→ 只寫自己的輸出夾。對方的檔一個都不改、不複製進自己的夾;對方沒有 / 檔改過 / 自己標不能用 → 不借、照實寫(灰 / 黃 · 不是紅)。
- **借讀法,不借判準**:VRN-1 借 VRN-2 的段落標題「讀法」,判準(成長率 / 比率段落底下的金額科目 = 錯)是 VRN-1 自己的;VRN-2 借 VRN-1 的 PIVOT「工具」,哪些格可以進去(⑪ 判對位)是 VRN-2 自己決定的。
- **PIVOT 的衝突表是第二道檢查**:同一格兩個不同的證實值 → 至少一個是錯的或科目字有歧義 → 留空、列出來(sign = 符號慣例 · scale = 單位 · value = 真的不同),不挑。同一個數印的位數不同(4,458 / 4,457.8)不是衝突。
- **同一張表同一個科目字出現在好幾列是不同的量**(現金流量表的 Other adjustments · 每個科目底下的 Percent of Revenues)→ 帶列號;跨表同名(損益表 / 資產負債表的 Minority interest)也是不同的量 → 報告層留空列衝突。
- **值對了還要查每一欄**:SECTION / ITEM / PERIOD / TICKER 都是輸出;驗證器只查值會漏掉欄位錯(v0128 前 SECTION 沒人查)。並排的兩張表同一高度交錯 → 段落標題只能取**同一個科目欄**的;公式項(1 - … / = … / x …)不是標題;改欄位時值一個都不能動(改前改後逐筆比對)。
- **對位不等於是數據**:表頭字本來就印在期間那一欄 → 位置檢查一定判對;驗證器還要查值的種類(值是期間字 · 科目是期間字 · 整列等於年份 → 表頭列 HDRVAL)。每輪把 U/I 的格子看一遍,怪值(Dec-23A · FY24A 當成值)先懷疑表頭。
- **定位靠紀錄,不靠猜**:找程式夾先看 MAIN 自己寫的紀錄(成功紀錄的鎖檔路徑 · 成功登記冊的管理器檔與 sha · 船包清單的 manager_tail);環境變數只是候選之一,指錯要能被略過並說出來。找不到時把查過的地方全部印出來(使用者貼回就能判斷)。
- **先問清楚貼在哪個殼**:提示字元 `C:\…>` = cmd · `PS C:\…>` = PowerShell;給使用者的一鍵指令要兩邊都能貼(`-EncodedCommand` + 雜湊核對)。
- **使用者貼回的紀錄先比時間戳記與雜湊**:同一份紀錄重貼時(開始時間 · 雜湊 · 備份檔名都一樣)不要當成新結果。

- **驗證器要先被驗**:每一種檢查都要做反向測試(把一種真的會發生的錯放回輸出 → 一定要抓到),而且要「量漏抓率」。v3 的「值在期間那一欄」看起來很嚴,反向測試一跑 3,000 筆漏 2,917 → 驗證說「錯值 0」不代表輸出對。
- **先定列,再找值**:找值之前先決定「這個科目是哪一列」(科目字相同 · 不是只含),值只從那一列找;不要拿值去挑列(拿值挑列 → 哪一列有這個值就說對)。鄰列只在科目列沒有數值時用,而且要互為最近。
- **標籤旁才算**:基本資料的數字(目標價 / 股價 / 上漲空間)要在自己的標籤旁 · 「原文有這個數」不夠(目標價和股價都在原文)。
- **驗證結果要綁住被驗的那一份**:U/I 套用驗證判決前比對冊指紋(兩邊各自實作同一算法)· 不同輪不套用。
- **擷取會把整列塞進一格**:「科目 值 值 值」在第一格、其他格空白 → 不是段落標題 · 兩個讀取器各自定列、定表頭,對出的期間一樣才收。
- **同值也要查重複**:DUPKEY 只抓「同一格兩個不同的值」· 兩個相同的值(季度段與年度段同期間字)也是錯 → DUPROW。
- **兩種讀法一致不等於對**:要加跟讀法無關的一致性檢查(DUPKEY / DUPROW)。
- **年度 ≠ 季度**:月-年期間看相鄰欄差幾個月(3 = 季度 · 12 = 年度);同一列表頭同期間印兩次 → 年度數據只對年度那個。
- **表頭不一定在表裡** · **同名科目要帶位置(ROW / SECTION)** · **上船只送自己的檔**(在遠端最新提交上疊一個只含船包的提交再 fast-forward)。
- **主冊只留驗過的值**(對不上就進剔除冊 · 帶理由)· **驗證器跟閘不能用同一種讀法** · **姓名照原文印** · **貼回用摘要(.digest.txt)**。
- **薄尾包裝不可再 rebind 前版的包裝**(會遞迴 · 包裝直接叫 `PRIOR.x(...)`)· 自測要真的跑一次包裝。
- **獨立系統**:VRN-2 不寫進別的系統的家族、不靠 VCGC 核號 / 中央冊;共用夾裡 git 追蹤中的檔是別的系統的 → 只讀。
- 船包要穩定 · 不要用測試替身上船 · 驗收資料不要截斷 · 數字比數值 · 環境相依不能決定燈號 · 平行只放互不相連的步驟 · 先分診再修 · 假綠校正 · 快取鍵包含所有輸入 · 自測不寫真正的 registry。
