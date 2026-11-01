# VRN-2 交接報告 · ActivateVRN-2 v0157 + VRN2_RoundAll_v0113 + VRN2_HandleAll_v0105 · 2026-10-31(③ 預設只檢查 · 缺的經 VCGC 安裝閘 CGC_MDL056_InstallGate 最高版號;管理器 envcheck 的本環境 pip + numpy<2 約束不再用;runtime v0156 原樣;桌機 04:13 v0104 repair = BLOCKED · 人工 3(閘二 VIA_SCRAPE_CONSENT 未設))

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
> **桌機 2026-10-31 02:06(最短一行 → Handle-All v0102 repair · 608 秒)**:⑥f 用 ConsensusJoin v0103 重跑:搬 38 / 43 份 · 只重抓 5 檔 · **8358 / 2891 抓到** · 4171 / 6933 / 7728 重試仍 404 → 不納入閘 → 搬 40 / 40 份 → GREEN。收尾卻 OPEN「VRN-2 1」= Combined 冊 GFHK Apple(AAPL)共識欄空 → v0110 算 VRN-2(v0109 是碰巧算資料源)。之前兩次又貼了 9,000 字元的長行 → PSReadLine 當掉 → 加了 443 字元的最短一行(`vrn2_release_v0154/VRN2_HandleAll_v0102_short.md` · 開機檔 `VRN2_HandleAll_v0102_boot.txt`)。
> **本輪(v0157)**:操作員「預設關掉 ③ 的 pip 補裝，改經 VCGC 安裝」→ **啟動器 v0157** 攔下 ③ 的 envcheck:只檢查 → 缺的一個一個交 VCGC 安裝閘(最高版號 · 倉裡 v0104)→ 再檢查 · 裝不起來 24 小時不重試(`VIA_Reports\vrn2\VRN2_VCGCInstall_latest.json`)· `--no-install` 只檢查 · 舊的本環境 pip 只有 `--pip-install` / `VIA_VRN2_PIP_INSTALL=1`;**RoundAll v0113**(② 提示 · 除錯列 · 貼回包)· **Handle-All v0105**(最短一行 443 字元 · `vrn2_release_v0157/VRN2_HandleAll_v0105_boot.txt`)· runtime v0156 原樣。桌機 04:13 v0104 repair:③b 閘二 `VIA_SCRAPE_CONSENT` 未設 → BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2(預期內)。
> **本輪(v0156)**:操作員「新版有版本號 · 加速器跟網路工具最新版都有版本號 · 直接透過 VCGC 的環境工具管理引擎下載所有不足工具及環境並確認無衝突 · 改成經網路工具和加速器出網再抓」→ **Fusion v0122**(v0121 + 出網經 `SUP_MDL740_NetUnified` 最高版號 · 鉅亨 http_bytes · YFinance yahoo_quote_summary_raw · 不用 yfinance 套件 · 要 requests)· **Matrix v0112**(交付檔)· **ConsensusJoin v0104** · **啟動器 v0156** · **RoundAll v0112** · **Handle-All v0104**(最短一行 443 字元 · 開機檔 `vrn2_release_v0156/VRN2_HandleAll_v0104_boot.txt`)。VCGC:EnvPlan --offline 衝突 0 · InstallGate --check-only 衝突 0 · InstallGate duckdb(沙盒 venv)前後衝突 0。同意閘是操作員的(VRN-2 / AI 永不代設):閘關 → repair 不重抓 · 整輪 ⑥f DENY → 人工。容器沒辦法開操作員的閘、也不是桌機網路 → 真抓沒在容器驗(假伺服器 + 閘替身驗車道 · 真網路工具閘關 = DENY 0 請求)。
> **本輪(v0155 · 小輪)**:**RoundAll v0111**:共識欄空、代號不是台股 4 碼 → 資料源(空白 → 人工)· 自測 51 項;**Handle-All v0103** 指向 RoundAll v0111(`vrn2_release_v0155`)· 最短一行 / 開機行 / cmd 一行同 v0102;套件 v0154 不動。沙盒:最短一行 → report / auto(→ repair)都 VRN-2 0 · 開機檔被改 → 不執行。
> **桌機 2026-10-30 20:09(Handle-All v0101 → RoundAll v0109 整輪 · 2225 秒)**:⑪ 錯值 0 · 年度 11505 筆 · **沒有 DUPKEY**(管理器 v0257 改名 37 · 剔除 8 —— v0153 修的生效)· 收尾 **OPEN · VRN-2 2 · VCGC 1 · 人工 2 · 資料源 2**:VRN-2 那兩項都是 ⑥f 共識 —— 第一次 43 檔 · 6933 / 7728 / 4171 回 404 → ConsensusJoin v0102 拿掉這三檔再跑 → 引擎 checkpoint 的雜湊含代號清單 → 第二次 40 檔**全部重抓**(沒有一行 Resume)→ 8358 / 2891 `ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__` → gate FAIL_CLOSED。Combined 6 列被算成 404,其中 8358 / 2891 是因為 join 把整批摘要(含「…不納入閘:4171,6933,7728」)抄進每一列。之後貼 8.7k 字元的一行 → PSReadLine 2.4.5 `IndexOutOfRangeException`。
> **本輪(v0154)**:① **ConsensusJoin v0103**(薄尾 · PRIOR v0102 · 引擎一字不改):每次跑引擎前,checkpoint 是今天的、清單不同 → 用引擎自己的函式把抓到的 payload 搬進這次清單的 checkpoint(續跑不上網)· 不過列分 404 / 一時抓不到 / 其他 · 前兩種等一下重試(只重抓沒抓到的 · 30 秒 × n · 一時抓不到 2 次 · 404 1 次)· 還是不過 → no_coverage / source_gap(黃 · 資料源)拿掉再跑 · 其他 → FAIL_CLOSED 照舊 · join 每列寫自己的原因 · 引擎這次沒有產出 → 不沿用上次的矩陣。② **RoundAll v0110**:收尾頁 ⑥f 照 v0103 的三類判負責方(v0103 以前做的一時抓不到 → VRN-2 寫根因)· Combined 每列原因 · ⑥f 各列 + Combined「共識缺」= 一項 · **⑤ 自動修**:用套件 runtime 的 v0103(只增不覆寫補放)重跑 ⑥f。③ **Handle-All v0102**:auto → **repair**(收據 v0153 以後 · 輸出冊在)· **短開機行**(ASCII 1,719 字元 · 從 GitHub 取 md、核對 Handle-All 那一行的 SHA-256 才執行)+ cmd 一行(pwsh -EncodedCommand)。④ **沙盒**:沙盒(桌機 20:09 ⑥f 狀態 · 13 檔版):RoundAll v0109 = v0109 before · 收尾 OPEN 未結案 {"VCGC": 4, "VRN-2": 2, "人工": 1, "資料源": 1} → v0110 = v0110 before · 收尾 OPEN 未結案 {"VCGC": 4, "VRN-2": 1, "人工": 1} → v0110 repair = v0110 repair · 收尾 BLOCKED 等 VCGC {"資料源": 2, "VCGC": 5, "人工": 1}
> **桌機 2026-10-30 18:34(Handle-All v0100 → RoundAll v0108 verify · 527 秒)**:③ 舊套件夾 `VRN2_Closeout_v0151` 以系統管理員身分 icacls /reset → 讀得到了 · auto 選 verify · ⑪b IndependentVerifier v0114:Daiwa aspeed PBR 26E → NILVAL(年度 FAIL 0)· 收尾 **BLOCKED · VRN-2 0 · VCGC 3 · 人工 5 · 資料源 2**。但驗證器還數到 **DUPKEY 45**:`6933_AMAX-KY_個股介紹報告.pdf` 第 8 頁兩張表並排(資產負債表 ∥ 損益表)右表的值被掛在左表科目下(流動資產 2020 = 1,331,956 又 = 3,411,492 · 權益總額 = 699,650 又 = -0.54)37 筆 · 凱基 2891 第 5 頁沒有列號的同鍵兩值 8 筆 —— 收尾頁卻算「人工」。同時上傳了 VDF 自己的 `VDF_v0102_Redownload_4.zip`(VDF 獨立系統 v0102 · 經 VCGC 安裝)—— VRN-2 只讀不動。
> **本輪(v0153)**:① **管理器 v0257**(薄尾 · PRIOR v0255):同檔 · 頁 · 表 · 列號 · 科目 · 期間 · 段落 · 子欄卻有不同值 → 那一列最左邊的格留給本列科目;右邊的值取同一列自己的科目名(改名 · VERIFY 註明)或移剔除冊(帶理由);沒有列號 → 都移剔除冊;同一個科目字在不同列(MS-3661 Percent of Revenues · MS-2308 Other adjustments)不動。桌機這份年度數據冊拿來試:剔除正好那 45 筆;容器 14 份真檔 0 列變動。② **RoundAll v0109**:⑪ 的 DUPKEY > 0 → VRN-2 · 收尾頁同一件事只列一次(⑪b + 收據 ⑪ · 四點 + 輸出缺項(四點)· ⑥e 步驟 + last_error + MOPS)→ 18:34 那 14 列重算 = BLOCKED · VCGC 1 · 人工 3 · 資料源 2(DUPKEY 還在 → OPEN · VRN-2 1)· 自測 46 項。③ **Handle-All v0101**:auto 只在收據是啟動器 v0153 時選 verify,不然整輪(輸出冊要由 v0257 重做)。④ **沙盒**:桌機情境(複製 v0151 沙盒:只有 v0151 收據)貼 Handle-All v0101 → auto 選 full → 套件 v0153 · ③ 自測 14 支 · 綠 14 · 紅 / 黃 0 · 啟動器 v0153(管理器 v0257)→ 年度數據冊與 v0255 做的逐列完全相同 → 再貼 auto 選 verify → report;收尾 BLOCKED(VRN-2 0);RoundAll 被竄改 → ⑤ 紅、不執行。
> **桌機 2026-10-30 17:06(RoundAll v0107 只重做報告 · 快速模式)**:① 用新夾 `VRN2_Closeout_v0151_20261030_133517`(原夾讀不到)· Combined 代號缺口 = GFHK Apple(TICKER `AAPL`)→ 資料源 · 收尾 OPEN「VRN-2 1 · VCGC 3 · 人工 4 · 資料源 2」—— VRN-2 那 1 項 = ⑪ 年度數據 FAIL 證據(驗證器讀法 · 原文相符):`260914_daiwa_aspeed.pdf` 表頭「Year to 31 Dec 26E 27E 28E」· 科目列「PBR (x) n.a. 29.2 16.8」→ 26E 原文就是 n.a. = 冊值。操作員:「GENERATE A PS CODE TO HANDLE ALL」。
> **本輪(v0152)**:① **IndependentVerifier v0114**(結構複本 · v0113 留著):核心判 FAIL 時用第二種讀法(PDFium 整頁文字 / pdfplumber 文字行 · 一次只用一種)取科目列上方最近、含該期的表頭,值與期別個數相等才依順序對齊 → 該期原文 = 冊值:NILVAL(空值記號)/ PRESENT(數字);不同或對不齊照樣 FAIL(附那一欄的原文值)。容器整輪回歸 4905 筆與 v0113 完全相同;變造(冊值改成 n.a. · 換欄 · 亂碼)照樣 FAIL。② **RoundAll v0108**:新步驟 `verify`(⑪b 只重跑獨立驗證 · 套件 runtime 最新的驗證器只增不覆寫地放進 `functional modules\VRN2` → 上一輪輸出冊重驗 → 收據 ⑪ 換成這次結果、先備份)· 這版收據還沒有就**沿用前版收據**(桌機只有 v0151 的)· 收據修正紀錄合併不覆蓋 · 自測 44 項。③ **Handle-All v0100**(`vrn2_release_v0152/VRN2_HandleAll_v0100.md` · PowerShell 7 一段碼 · 一行版 + 可讀版語法樹相同):工具 → 別的 VRN-2 在跑嗎 → 舊套件夾讀不讀得到(答 y 才以系統管理員身分 icacls /reset)→ 模式 auto / full / verify / report → 取 RoundAll v0108 核對 SHA-256 → 跑 → 印收尾狀態與各負責方待辦。④ **沙盒**:桌機情境(複製 v0151 沙盒:只有啟動器 v0151 的收據 + 上一輪輸出)貼 Handle-All → auto 選 verify → 套件 v0152 → ⑪b v0114 → 收尾 BLOCKED(VRN-2 0)· 34 秒;report 1 秒;RoundAll 被竄改 → ⑤ 紅、不執行。全新沙盒 auto → full(③ 自測 14 支 · 綠 14 · 紅 / 黃 0 · 啟動器 v0152 · ⑪ v0114)→ 再貼 auto → verify → report,收尾都是 BLOCKED、VRN-2 0。
> **桌機 2026-10-30 14:41(RoundAll v0105 · 3977 秒)**:紅 0 · 黃 16 · ⑪ 基本資料 FAIL 0(MS-6669 / 3661 / 8358 / 8210 都好了)· 年度 BADITEM 19 → 0(PRESENT 82 → 101 · v0113 生效)· 年度 FAIL 1(Daiwa aspeed PBR 26E n.a.)· 收尾 OPEN「VRN-2 2 項」= ② CPU 忙碌 93% + ⑥ Combined 1 格「基本資料冊代號不是 4 碼」(分類規則不夠細)· `icacls` 對舊套件 zip:Access is denied(`/reset` 非系統管理員也被拒)。**RoundAll v0106**:② CPU → 提醒 · 代號不是 4 碼 → 冊裡 TICKER 空白 = 人工 / 有值 = 資料源 · 空格原因列檔名 · 新「⑪ 年度數據 FAIL 證據」(讀原 PDF 那頁的表頭 + 科目列依欄位對齊 → 原文該期間的值 vs 冊值)· 套件安裝改成正常建夾 + 逐檔複製(v0104 / v0105 把 Python 3.13 只給擁有者權限的暫存夾整個搬進 Downloads → 某次系統管理員身分跑過就讀不到)。用 14:41 那 10 項重算 → BLOCKED(VRN-2 0 · VCGC 3)。**RoundAll v0107**(給桌機前先補):只重做報告(--only report,closeout,pasteback)時找讀得到啟動器的套件夾(含 <套件>_<時間>)、不跑啟動器就不需要套件 · 原夾讀不到時沿用既有新夾(不再每輪多 8 MB)。
> **桌機 2026-10-30 13:15 / 13:21(PowerShell 7.6.9 原生一行跑 RoundAll v0104)**:兩次都在 ① 讀 `Downloads\VRN2_Closeout_v0151\VRN2_Closeout_v0151.zip` 時 `PermissionError [Errno 13]` → Traceback(沒有收尾頁 / 貼回包;隔 6 分鐘一樣 → 不是防毒短暫鎖)。**RoundAll v0105**:讀不到重試 → 印證據(啟動器鎖 PID · icacls · attrib)→ 改從 GitHub 取 → 原套件夾用不了換新夾 `VRN2_Closeout_v0151_<時間>` · 每一步出例外只記紅不中斷 · 收尾頁 / 貼回包照產生(讀不到的檔略過並記下)· ⑥f 過時的 Combined 黃 → 提醒。自測 34 項 · 沙盒模擬讀不到 → 改 GitHub → 照跑完。套件 / 一鍵 / 操作員 / 本地實測一輪逐位元不變。
> **收尾輪(2026-10-29 · 操作員「解決剩餘系統問題 HTML U/I CLOSE OUT」· 貼回的是 19:00 那輪的主控台 · v0150 已處理的不重做 · 分支 #573 已合進 main → 快轉後接著做)**:
> **本輪(v0151 · 套件 = 啟動器 v0151 + runtime v0151 = v0150 的 186 個成員不動 + IndependentVerifier v0113 · 一支 Python `vrn2_release_v0151/VRN2_RoundAll_v0104.py` · 一鍵 v0151 · 操作員一鍵 v0112 · 本地實測一輪 v0101)**:① **IndependentVerifier v0113**(結構複本 · v0112 留著):桌機年度數據 BADITEM 19(MS-3665 ×7 · MS-8358 ×6 · MS-8210 ×4 · Daiwa aspeed ×2 ·「ModelWare net inc (NT $ mn)」「Prior EPS (NT$)**」「DPS」· 值都在該頁)只有字元框讀法說「科目本頁原文沒有」(跟 v0112 修的側欄同一個讀法)→ 判 BADITEM 前先用第二種讀法(PDFium 整頁文字 + pdfplumber 文字行)找科目(整個 · 折行 · 兩字以上依序在三列內);造假 / 改名的科目照樣 BADITEM、註記帶原文最像的那一列;值不在該頁的 FAIL 註記帶科目那一列。容器:原樣 4,378 筆 0 差異 · 變造科目名 60 / 60 照樣 BADITEM · 模擬桌機讀壞科目列 59 / 59 回到 PRESENT · 整支跑 v0112 vs v0113 年度 4,905 筆逐筆同判。② **RoundAll v0104 · ⑧ 收尾頁** `VIA_Reports\vrn2\VRN2_CloseoutUI_latest.html`(+ .json · 進貼回包 · Windows 跑完自動開):每列非綠結果判負責方(VRN-2 要修 / 交 VCGC / 人工核對 / 資料源沒有 / 提醒 / 彙總 · 認不出 = VRN-2),結案狀態 OPEN > BLOCKED > REVIEW > DATA_GAP > PASS(只有 PASS 是成功);用 19:00 那輪 39 列試算 = **BLOCKED**(VRN-2 0 · VCGC 3 · 人工 8 · 資料源 4)。Combined 空格照原因分(原文沒有目標價不是缺)。③ **端到端(沙盒仿桌機 · pwsh 一行指令從假 GitHub 分支取 RoundAll v0104)**:RoundAll 全流程 NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 14(綠 34 · 黃 14 · 紅 3 · 灰 10)· ③ 自測 14 支 · 綠 14 · 紅的步驟:④ 跑啟動器 ActivateVRN-2_v0151.py / ⑥ 收尾收據 / ⑥ 步驟 ③ 環境檢查與補裝 · Combined 14 列 · 收尾頁 BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 9 項等 VCGC 決定 / 安裝(見 ⑧ 列);只修回合:只修回合 NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 14(綠 22 · 黃 14 · 紅 2):⑤ 計畫 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據) · 收尾頁 BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 8 項等 VCGC 決定 / 安裝;修後收尾頁:BLOCKED · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝 · {"VCGC": 5, "人工": 2}。
> **桌機貼回(2026-10-29 19:00 · 跑 VRN2_RoundAll_v0102 · 52 份 · 5957 秒 · 紅 0 黃 20 · rc 2)**:上一輪的三個問題都好了 —— 四點原文核對 FAIL 0(3014TT 第 3 點 PASS)· SyntaxWarning 沒了 · ⑥e 選到合 VDF 界線的 C:\Python313 並真的跑了引擎。剩下:⑪ 基本資料 FAIL 4(MS-6669 / MS-3661 / MS-8358 現價 · MS-8210 上漲)· ⑥f gate FAIL_CLOSED(6933 / 4171 鉅亨 404)· ⑥e 財報 4 次 PermissionError「Existing VIA network bridge denied」→ ⑬b 無歷史 44 · RoundAll ⑤ 又把 ⑥e 重抓一輪(約 35 分鐘)· 年度 FAIL 1(daiwa aspeed n.a.)。
> **前一輪(v0150 · 套件 = 啟動器 v0150 + runtime v0150 = v0149 的 184 個成員不動 + IndependentVerifier v0112 + ConsensusJoin v0102 · 一支 Python `vrn2_release_v0150/VRN2_RoundAll_v0103.py` · 一鍵 v0150 · 操作員一鍵 v0111)**:① **IndependentVerifier v0112**(結構複本 · 分片子行程跑本檔):RoundAll v0102 印的證據顯示 MS-6669 / MS-3661 的冊值就等於原文「Shr price, close (…) NT$3,510.00 / 3,190.00」→ 驗證器誤判(字元框讀法在桌機的函式庫版本漏讀 / 配錯 MS 側欄;同一份 MS-3661 在容器 PASS)。字元框說不對時,換第二種讀法(PDFium 整頁文字 + pdfplumber 文字行)只看同一列數字前最近的標籤(或緊接著的「% upside」「price target」);容器回歸 193 PASS 不變 · 目標價 ↔ 現價對調 12 / 12 照樣 FAIL · 真 MS-3661 模擬字元框漏讀 → PASS、對調 → FAIL。② **ConsensusJoin v0102**:品質矩陣不過的列全是「statusCode=404 頁面或商品不存在」(鉅亨沒有 FactSet 頁)→ 這幾檔不納入、同一個引擎再跑一次(續跑);有別的不過列照 FAIL_CLOSED;Combined STATUS 註記 404。③ **啟動器 v0150**:⑥e 明細寫出擷取 Python 與「合 VDF 界線」(不再寫「Python 本行程」)。④ **RoundAll v0103**:⑥e 經 MarketFetchRun 跑過就不重抓 · ⑪ 證據逐值(數字相等 · 跳過 Email / 電話行)· MOPS DENY 的說明 · 自測 23 項。⑤ **端到端(沙盒仿桌機 · pwsh 一行指令從假 GitHub 分支取 RoundAll v0103)**:RoundAll 全流程 NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 13(綠 34 · 黃 13 · 紅 3 · 灰 10)· ③ 自測 14 支 · 綠 14 · 紅的步驟:④ 跑啟動器 ActivateVRN-2_v0150.py / ⑥ 收尾收據 / ⑥ 步驟 ③ 環境檢查與補裝 · Combined 14 列 · 整合 APPLIED(套用 1 · 略過 無);只修回合:只修回合 NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 14(綠 21 · 黃 14 · 紅 2):⑤ 計畫 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據) · 歷史對齊 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6) · 長線庫 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "Deleted": 12}(Combined 值變了的列另存一版,舊版留著)。**沒修 / 要決定**:MOPS 財報被 VIA 鎖版網路工具的合規層拒絕(DENY · 不繞)→ 交 VCGC · MS-8358 / MS-8210 等 v0103 逐值證據 · daiwa aspeed 年度 1 格 · ⑥e 每輪重抓價格約 30 分鐘(操作員規則)。
> **桌機貼回(2026-10-29 17:01 · 跑 VRN2_RoundAll_v0101 · 52 份 · 2345 秒 · 紅 4 黃 11 · 殼印 PowerShell 5.1,操作員說自己的是 7.6.9)**:紅 = ④ 啟動器 rc 1 · ⑥ 收尾收據 rc 1 · ⑥ 四點原文核對 FAIL(3014TT-20231005.pdf 第 3 點 · rc 1 的唯一原因)· ⑥ 四點 FAIL 摘錄;黃 = ⑥e 擷取「缺套件」(MarketFetch 自己用了 envs\via_tw_fetch)· ⑥f gate FAIL_CLOSED(共識 41 / 43 · 缺 6933 · 4171)· ⑪ 基本資料 FAIL 4(MS-3661 / 6669 / 8358 現價 · MS-8210 上漲)· 年度 FAIL 1(daiwa aspeed `n#a#`)…;另 `SyntaxWarning: invalid escape sequence '\l'`。
> **前一輪(v0149 · 套件 = 啟動器 v0149 + runtime v0149 = v0148 的 181 個成員不動 + VerbatimVerifier v0105 + IndependentVerifier v0111 + MarketFetchRun v0100 · 一支 Python `vrn2_release_v0149/VRN2_RoundAll_v0102.py` · 一鍵 v0149 · 操作員一鍵 v0110)**:① **VerbatimVerifier v0105**(收尾閘 · 薄尾 · v0104 也在套件):摘錄(pdfplumber)「Type-」換行「C PD」,PDFium 寫成「Type\ufffeC」;v0104 只在下一字小寫時接合 · 不認 U+FFFE → FAIL。v0105 比對時 U+FFFE → 「-」+ 換行,任何「-」+ 換行都接(兩邊同法)· 冊裡的摘錄不動 · 用 PyMuPDF 產生的 PDF 重現 v0104 FAIL / v0105 PASS · 沙盒 52 點回歸不變。② **IndependentVerifier v0111**:v0110 的摘錄讀法換成 v0105(⑪ 一標題四重點 FAIL 1 就是同一點)。③ **MarketFetchRun v0100**:MarketFetch v0112 的 `fetch_python()` 只要 `envs\via_tw_fetch\Scripts\python.exe` 在就用它(啟動器給的 VIA_FETCH_PY 不管)→ 桌機那個環境什麼都沒裝(VDF 引擎上一輪在那裡 pip 失敗);容器用 Windows 版面重現(`repro_marketfetch149.log`)。runner 載入共用 MarketFetch(不改不抄)只換 `fetch_python()` → 第一個通過 VDF 引擎自己 `def_missing_dependencies()` 的 Python(界線從引擎檔 ast 讀 · 3.11+ · 再加 MarketFetch 自己的匯入探測);都不合 → 不啟動引擎(不 pip)· 填值用能匯入 pandas + pyarrow 的 Python · 收據 ⑥e 多 `fetch_python`(每個候選缺什麼,裝了但不在界線內寫出版本)。④ **RoundAll v0102**:套件 v0149 · docstring 反斜線成對(⑯ 編譯不准出 SyntaxWarning)· ② 用同一支 runner 照 VDF 界線診斷 + 交 VCGC 的指令帶界線加引號 · ⑥ 印 ⑪ 基本資料 FAIL 證據(冊值 + 原 PDF 前 4 頁那行 → `VRN2_FailEvidence_latest.json`)· ⑪ 驗證器版本 · ⑥f 共識閘 FAIL 列 · ③ 多跑 VerbatimVerifier v0105 / MarketFetchRun v0100 · 20 項過 · 一行指令 **pwsh** 與 powershell 兩種。⑤ **端到端(沙盒仿桌機:殼有 VIA_ROOT · envs 有退役環境 + 沒裝套件的 via_tw_fetch · 用 pwsh 一行指令從假 GitHub 分支取 RoundAll)**:RoundAll 全流程 NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 13(綠 34 · 黃 13 · 紅 3 · 灰 10)· ③ 自測 14 支 · 綠 14 · 紅的步驟:④ 跑啟動器 ActivateVRN-2_v0149.py / ⑥ 收尾收據 / ⑥ 步驟 ③ 環境檢查與補裝 · Combined 14 列 · 整合 APPLIED(套用 1 · 略過 無);只修回合:只修回合 NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 14(綠 21 · 黃 14 · 紅 2):⑤ 計畫 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據) · 歷史對齊 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6) · 長線庫 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "Deleted": 12}(Combined 值變了的列另存一版,舊版留著)。**沒修 / 要證據**:MS 四份 ⑪ FAIL(容器同檔 PASS → v0102 下一輪會印證據)· 桌機沒有合 VDF 界線的 Python 時 ⑥e 會一直黃(要 VCGC 建 via_tw_fetch;VRN-2 不裝、不改 VDF)· ⑥f 閘 FAIL_CLOSED(FactSet 沒覆蓋的代號;引擎語意不改)· daiwa aspeed 年度 1 格。
> **桌機貼回(2026-10-29 14:40 · 第一次跑 VRN2_RoundAll_v0100 · 52 份 · 2069 秒 · 紅 4 黃 10)**:紅 = ③ UIAction v0109 自測 ④ · ④ 啟動器 rc 1 · ⑥ 收尾收據 rc 1 · ⑥ 四點原文核對 FAIL(3014TT 第 3 點);黃 = ② 擷取 Python 選到 `envs\via_core.retired-20260914_111946` · ⑥e VDF 引擎 5 個視窗 rc1「致命錯」(VDF 先自己用 pip 建 via_tw_fetch)· ⑥f 8 檔 Yahoo 404 + gate FAIL_CLOSED · ⑬b 無歷史 44 · 檢驗 534 不過 120 · ⑪ 驗證 FAIL 4(MS 四份現價 / 上漲)· 缺年度 3 份 …;另 PowerShell 裡打 `python "%USERPROFILE%\…"` 找不到檔。
> **前一輪(v0148 · 套件 = 啟動器 v0148 + runtime v0148 = v0147 的 178 個成員不動 + UIAction v0110 + ConsensusJoin v0101 + HistoryAlign v0102 · 一支 Python `vrn2_release_v0148/VRN2_RoundAll_v0101.py` · 一鍵 v0148 · 操作員一鍵 v0109)**:① **UIAction v0110**:v0109 的 rerender() 在設定檔沒 root 時讀環境變數 VIA_ROOT,桌機的殼有它 → 自測真的重渲染了 Workbench、印的不是「沒有 VIA 根」→ ④ FAIL;容器設 VIA_ROOT 重現(`VRN2_UIAction_v0109_selftest_with_VIA_ROOT.log`)· v0110 自測時拿掉再還原 · 7 項過。② **ConsensusJoin v0101**:鉅亨對上櫃股也回 `TWS:####`,引擎 `def_cnyes_symbol_to_yfinance_ticker` 一律 `.TW` → Yahoo 404;對應表改從 ⑥e 市場冊(MarketFetch / VDF 身分表 TWSE .TW · TPEX .TWO)· 引擎檔不動,由本檔 `--engine-shim` 在同一個 Python 帶起並只換那個函式 · 同日 checkpoint 用錯尾碼抓的代號重抓 · 11 項過(含引擎原本 5274 → .TW、patch 後 .TWO)。③ **HistoryAlign v0102**:檢驗不過多半是科目對錯列(Other Revenue · Taxes payable · Total liabs & equity · Minorities · 調整後 / 核心 · 部門成長率)+ 成本寫負數 + 預估調整表同年三個值取到舊估;v0102 排除這些列、成本取絕對值、ROE 可用平均權益、同年同科目取重複出現的值、差到不像同口徑標 UNCLEAR —— 容器資料 不過 74 / 218 → 5 / 192(剩的 5 筆是合成資料故意改錯的淨利)。④ **RoundAll v0101**:擷取 Python 候選略過 retired / backup / bak / old / deprecated / archive 夾 · 除錯報告印四點 FAIL 那一點的摘錄原文、`market\vdf\last_error.txt` 最後幾行、Yahoo 404 代號與上櫃數 · 最後印完整路徑的重跑指令(cmd / PowerShell 都能貼)· 16 項過。⑤ **操作員一鍵 v0109**:v0108 的 md 被 build147 的整段取代把歷史段落也改成 v0108 / v0147;v0109 從 v0107 的 md 還原歷史(v0108 檔不改)。⑥ **端到端(沙盒仿桌機:殼有 VIA_ROOT · envs 有退役環境 · 套件從假 GitHub 分支取 · 輸出夾在 OneDrive)**:RoundAll 全流程 NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 11(綠 30 · 黃 11 · 紅 3 · 灰 10)· ③ 自測 12 支 · 綠 12 · 紅的步驟:④ 跑啟動器 ActivateVRN-2_v0148.py / ⑥ 收尾收據 / ⑥ 步驟 ③ 環境檢查與補裝 · Combined 14 列 · 整合 APPLIED(套用 1 · 略過 家用記帳.csv);只修回合:只修回合 NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 12(綠 20 · 黃 12 · 紅 2):⑤ 計畫 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據) · 歷史對齊 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6) · 長線庫 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "Deleted": 12}(Combined 值變了的列另存一版,舊版留著)。**沒修 / 要貼回 zip 才能修**:3014TT 第 3 點 FAIL(rc 1 的原因)· MS-3661 / 6669 / 8358 / 8210 現價 / 上漲 FAIL(桌機這輪擷取沿用快取;同一份 MS-3661 在容器新跑是 PASS)· ⑥e VDF 致命錯的原因(VDF 的檔 VRN-2 不改)· 3 份缺年度數據。
> **操作員令(2026-10-29 · v0146 推上之後)**:「generate a py code to handle all above and fix all test all debug all」。
> **前一輪(v0147 · 套件 = 啟動器 v0147 + runtime v0147 = v0146 的 175 個成員不動 + OutputStore v0101 + DataIntegrate v0101 + HistoryAlign v0101 · 一支 Python `vrn2_release_v0147/VRN2_RoundAll_v0100.py` · 一鍵 v0147 · 操作員一鍵 v0108)**:① **VRN2_RoundAll_v0100.py**(只用標準庫 · 釘死套件 SHA-256):⓪ 找 VIA 根(參數 → 環境變數 → 本檔所在的倉 → 啟動器記的 Runtime_Context → vrn2:// 註冊 → 預設位置)→ ① 套件(本機 zip 雜湊 + 逐檔 → 否則 git archive 分支 / main → 竄改整夾改名備份)→ ② 診斷(VRN-2 Python 套件 · 擷取 Python yfinance 等 · 共用 MarketFetch / VDF 引擎 · 鎖 · 輸出夾可寫 · 來源夾 · 磁碟 · CPU · git;缺的只列、照印 VCGC 指令)→ ③ runtime zip 解到 TEMP 逐檔核對 · 十支 --selftest + 啟動器 --selftest → ④ 跑啟動器(預設不上船 · 心跳)→ ⑤ 自動修(⑥e 用錯 Python 重抓 · 有 yfinance 的 Python 重跑 ⑥f · 市場比歷史新重跑 ⑬b · Combined 重組 · ⑬ 補寫 · Workbench 重渲染 · 舊資料庫問使用者 · 清過期鎖;收尾收據先備份 .before_roundall.json)→ ⑥ 除錯報告(每個非綠步驟 + 下一步 · 四點核對不過的檔 / 點 · 缺項 · 完成判定 · 冪等閘 · 階段耗時前三 · Combined 欄序 / 空格 · Workbench 標記 · 市場 / 歷史 / 庫 / 整合 / SSOT → VRN2_RoundAll_latest.json)→ ⑦ 貼回包(Downloads)。一行啟動在 `VRN2_RoundAll_v0100.md`(cmd / PowerShell 都能貼 · 核對 py 的 SHA-256 · CRLF 也驗得過)。② **做它時測出並修掉的缺陷**:(a)⑬ 長線庫只追加「沒見過的原檔」→ 桌機 52 份已知時新冊永遠 0 列 → OutputStore v0101 以「冊 × 原檔 SHA × 列雜湊」判缺(已知原檔的新冊 / 改過的列也進庫,同列不重寫)+ 收 Combined / FinancialAligned / Deleted;(b)⑬b 在 ⑬ 之後 → 本輪對齊冊進不了庫 → 移到前面;(c)DataIntegrate v0100 用 rglob 走整棵樹(輸出夾在 OneDrive 時上一層 = 整個 OneDrive)且任何 CSV 都問 → v0101 限深 scandir + 只問像 VRN-2 的檔;(d)⑥e 用 VRN-2 的 Python 跑 MarketFetch(--fill 要 pandas)· fetch 失敗就不 fill → 用擷取 Python · 照樣 fill;(e)啟動器 --selftest 在真套件夾找不到 runtime 模組(v0144 ~ v0146)→ 從 runtime zip 取;(f)啟動器 --selftest 在設了 VRN2_OUTPUT_DIR / 上限變數的殼會自己失敗(v0144 起)→ 自測時清掉再還原(RoundAll 第一次端到端就抓到);(g)RoundAll 自己:`--launcher-args "--no-install"` 被 argparse 當選項 → 併成 `=` 形式;(h)⑬b HistoryAlign v0100 只要「同年同科目」就比,報告寫百萬元 / 億元或成長率列也拿千元歷史去比 → 沙盒 100 列誤進刪除區 → v0101:換算後對得上才覆蓋、別的單位對得上只覆蓋不刪、同量級(0.5 ~ 2 倍)且差 >3% 才刪、其餘標「不明」不動、成長率 / % 段落只做比率檢驗(沙盒 100 → 39 刪 · 44 不明)。③ **端到端(沙盒仿桌機:套件從假 GitHub 分支取 · 共用 MarketFetch 在但沒 yfinance · 輸出夾在 OneDrive · 有舊 Google Sheet CSV + 不相干的家用記帳 CSV)**:RoundAll 全流程 NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 11(綠 29 · 黃 11 · 紅 3 · 灰 10)· ③ 自測 12 支 · 綠 12 · 紅的步驟:④ 跑啟動器 ActivateVRN-2_v0147.py / ⑥ 收尾收據 / ⑥ 步驟 ③ 環境檢查與補裝 · Combined 14 列 · 整合 APPLIED(套用 1 · 略過 家用記帳.csv);第二次只修(`--skip-run`,先放一份合成的市場資料)只修回合 NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 12(綠 19 · 黃 12 · 紅 2):⑤ 計畫 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據) · 歷史對齊 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 110 格 · 刪除區 39 列 · 檢驗 218(不過 85) · 長線庫 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "Deleted": 39}(Combined 值變了的列另存一版,舊版留著)。桌機還沒跑 v0147 / RoundAll。
> **操作員令(2026-10-29 · 10:25 貼回後)**:Gemini 對話(台股代號三形式 · ETF 尾碼 · 台北 / 香港電話 · 評等代碼 0 ~ 5 · 目標價同義字 · 分析師職稱)+「HEADER 用空格取代底線 內容全部靠上對齊 數值呈現在 U/I 上都是以百萬台幣為單位 除每股倍數 要有千分位號」+ v0145 整輪主控台(2546 秒)+ 兩張 Workbench 截圖 +「為何字體常爆出格子不會自動調整自動優化嗎 · 左邊 VRN-1 GATE 要有一格輸出檔案夾來存長線資料庫 增量維護一律用 PARQUET · 若使用者已有舊的資料庫(CSV / GOOGLE SHEET)主動提醒要不要進行資料整合 · 整合成功前千萬不要刪掉原有資料 · 自適應式對齊欄位核對後問使用者 · OK 則整合創立並把舊資料放到 TEMP · 一定要擷取歷史資料去做數字對齊 至少有一期要對 然後歷史覆蓋預估 加減法 乘除法檢驗 被歷史數據刪掉的部分放刪除區 · 右面板第一區要有輸入去重矩陣 目前引擎狀態 · 昨天不是可以擷取 TWSE/TPEX/YFINANCE 資料嗎 現在為何不行」→ 再傳 `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py` +「LOGO 理字邊緣留空更少一點點但不可砍到字 然後高畫質放大到 180% 依舊去背透明無框無特效無色」+ 欄名雙語清單(REPORT_DATE:Report Date / 報告日期 …)+「Report Target Price(Adj) / FactSet Target Price Median / YFinance Target Price Median / 2026 ~ 2028 Diluted EPS (FactSet) / 2026 ~ 2028 PER (FactSet) 在 Combined 目標價後面加上 · n 是今年 2026 · 還原真實年分」。
> **前一輪(v0146 · 套件 = 啟動器 v0146 + runtime v0146 = v0145 的 167 個成員不動 + 8 個新成員 · 操作員一鍵 v0107 · 本地實測一輪 v0100 改指)**:① **桌機 10:25 判讀**:87.5% busy by another process at launch → launcher chose 平行 1 路 · 優先權 不變;⑦ ≈1180 (擷取 13 · 驗收+摘要 9 · 輸出冊 969 · 冪等閘 151 (R1 73 / R2 78 · parallel works));⑪ 833 秒;④ 93 + 107 (④ / ④b);⑬ duckdb GREEN · 新檔 0 / 已知 52 (incremental proven);⑥c · ⑤b · ⑫b · Workbench v0101 GREEN · 驗證判決寫回;紅燈 same as 08:14: ⑧b rc 1 ← 四點原文核對 FAIL 1 (3014TT-20231005 POINT_3) · 輸出缺項 3 份年度數據 (Daiwa-6278 · 欣銓 3264 · 華南 6143) → needs VRN2_PasteBack_20261029_102505.zip。判讀:the 969 s 輸出冊 is the native second-reader value verification (10,908 values across 52 PDFs) under CPU starvation (1 lane) + OneDrive I/O; not the idempotence gate any more (151 s). 'Why no TWSE/TPEX/YFinance?': the desktop line's own launcher (manager v0249) has ⑥e; this package line never had it → v0146 adds ⑥e / ⑥f. ② **Workbench v0102**(v0101 薄尾):表頭雙語(清單外底線 → 空格 · 原欄名在 title)· th / td 靠上 · 金額欄依列 ITEM / TABLE 判單位 → 百萬台幣 + 千分位(每股 / 倍數 / % 原值 · 滑鼠停留看原值)· 統計磚 clamp + 逐 px 縮(最小 12px 仍不夠就換行)· 左欄「輸出檔案夾 · 長線資料庫(Parquet 增量)」在其他系統 Gate 之上 · 右欄第一區 = 輸入去重矩陣 + 目前引擎狀態(含 ⑥e / ⑥f / ⑬ / ⑬b / ⑬c)· 舊資料庫整合提問 · 歷史對齊表 · 資料冊多 Combined / FinancialAligned / Deleted · logo 以 alpha 內容框重裁(留白 1.5% · 雜訊 alpha 歸零)+ LANCZOS 180%(44 → 79 px · 頁首 100 px)。③ **⑥e 市場擷取**:啟動器跑完 ⑦ 後借共用夾 `functional modules\VRN\VRN2_MarketFetch_v*.py`(桌機線工具 · 只讀 · 最新號)`--fetch` 再 `--fill` → `market\VRN2_Market_latest.json`;共用夾沒有 → 灰;缺 yfinance → 黃交 VCGC;`VIA_VRN2_NO_MARKET=1` 不抓 —— 回答「為何不行」:桌機線自己的管理器 v0249 有 ⑥e,本套件線(v0243 → v0255)從來沒有。④ **⑥f 共識合併**:上傳的引擎 v0120 原樣內附 runtime;VRN2_ConsensusJoin v0100 以基本資料冊 TICKER 跑它(`--skip-unit-tests --allow-missing-duckdb` · 離線 `--fixture` 供測試)→ `consensus\VRN2_Consensus_latest.json` → **Combined 冊**(每份報告一列 · 欄序照操作員雙語清單 · 目標價後接 TARGET_PRICE(ADJ) · FACTSET / YFINANCE 中位數 · 2026 / 2027 / 2028 真實年度 EPS 與 PER · 最後 TOPIC & SUMMARY · STATUS 寫各欄來源 / 缺的原因)。⑤ **⑬b 歷史對齊**(VRN2_HistoryAlign v0100):科目同義字 → 年度期間 → 倍率自動對 → 至少一期對上才覆蓋 → VALUE_FINAL / VALUE_SOURCE / RECON_* · 差 > 3% 進刪除區 · 加減 / 乘除檢驗只報不改 → FinancialAligned / Deleted 兩冊;原三冊不改。⑥ **⑬c 舊資料庫整合**(VRN2_DataIntegrate v0100 + 處理器 v0109 `vrn2://integrate`):掃輸出夾及其上一層 / legacy_in / `VRN2_INTEGRATE_DIRS` 的 CSV / TSV / XLSX(純 zip + xml 讀)/ Parquet / JSON / Google Sheet 匯出 → 同義字 + 內容型態對齊欄位(對不到保留 X_)→ Workbench 問 → apply:VRN-2 冊 ∪ 舊檔去重(同鍵同值去 · 不同值兩邊留標 CONFLICT)→ 新整合檔 json / csv / parquet → 重讀核對 → **原檔絕不刪**,核對過才複製到 TEMP;同內容整合過 / 選過不要的不再問。⑦ **SSOT 提案冊** v0100(9 條 · ssot_id 空白 · VRN2-PROP-xxxx)經 SSOTSync v0101 併進 ⑤b 請求冊。⑧ **啟動器 v0146**:⑥e / ⑥f 在 ⑦ 後、⑬b / ⑬c 在 ⑬ 後;四步都不轉紅(灰 / 黃);收據 `VRN2_Closeout_v0146.json` 多 market / consensus / history_align / integrate;處理器 v0109 · Workbench v0102 · SSOTSync v0101。容器實測:七支自測全 PASS · pwsh 雜湊鏈全 True · 沙盒 19 份:⑧ 完成 · 冪等閘 GREEN · ⑥f YELLOW(13 / 13 代號 · gate PASS_WITH_WARNINGS · Combined 14 列)· ⑬ YELLOW · ⑬c PENDING_USER · Workbench v0102 GREEN(無頭 Chromium 無錯 · 雙語表頭 · 千分位)· 情境 first rc 1 · again rc 1 · tamper rc 1 · done。桌機還沒跑 v0146。
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
| **VRN2_HandleAll_v0105.md**(發行夾 · 最短一行 + 開機行 + 一段碼 · 不是 .ps1)| **v0105** | `vrn2_release_v0157` | 一行版 `c3a93278037a` · 開機檔 `c943f58e9ece` | **新**(RoundAll v0113 · 最短一行 443 字元)|
| **VRN2_RoundAll_v0113.py**(發行夾 · 一支入口 · 不在套件內)| **v0113** | `vrn2_release_v0157` | `891df58a576e` | **新**(套件 v0157 · ③ 經 VCGC 安裝閘的除錯列 / 收尾頁 · ② 磁碟 → 人工 · 自測 57 項)|
| ActivateVRN-2_v0157.py(套件 · 底座 v0136 · runtime v0156)| **v0157** | 見發行清單 | `850c0d07d38d` | **新**(③ 只檢查 · 缺的經 VCGC 安裝閘 · 收據 v0157 · 自測多一段 v0157)|
| **VRN2_HandleAll_v0104.md**(發行夾 · 最短一行 + 開機行 + 一段碼 · 不是 .ps1)| **v0104** | `vrn2_release_v0156` | 一行版 `986cdad74e65` · 開機檔 `5d39098af267` | **新**(RoundAll v0112 · ③b 只讀印同意閘 · 最短一行 443 字元)|
| **VRN2_RoundAll_v0112.py**(發行夾 · 一支入口 · 不在套件內)| **v0112** | `vrn2_release_v0156` | `5f032bc73f2f` | 被 v0113 取代(③ 本環境 pip)· (套件 v0156 · ⑤ consensus_refresh · net_deny → 人工 / VCGC · 自測 55 項)|
| ActivateVRN-2_v0156.py(套件 · 底座 v0136)| **v0156** | 見發行清單 | `75c0bcfe5eec` | **新**(收據 v0156 · CONSENSUS_JOIN v0104 · 自測多一段 v0156)|
| **VRN2_ConsensusJoin** | **v0104**(薄尾 · v0103 ~ v0100 留著)| runtime v0156 | 見 runtime 清單 | **新**(引擎經網路工具 · requests 探測 · net_tool / net_deny · 直連抓的 checkpoint + 閘開 → 封存重抓 · 自測 ① ~ ⑨)|
| **VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine** | **v0122**(v0121 + 網路工具)| runtime v0156 · 發行夾 | `7eea60fd3019` | **新**(出網經 SUP_MDL740_NetUnified 最高版號 + 加速器橋 · 閘關 / DENY = 停 · v0120 留作直連前版)|
| **VIA_FactSet_YFinance_Consensus_Matrix_Engine** | **v0112**(v0111 + 加速器橋 + 網路工具)| 發行夾(不接進 VRN-2)| `573c167d6186` | **新**(交付檔)|
| **VRN2_HandleAll_v0103.md**(發行夾 · 最短一行 + 開機行 + 一段碼 · 不是 .ps1)| **v0103** | `vrn2_release_v0155` | 一行版 `c407fd42f103` · 開機檔 `ddc3139d3d60` | **新**(RoundAll v0111 · 最短一行 443 字元)|
| **VRN2_RoundAll_v0111.py**(發行夾 · 一支入口 · 不在套件內)| **v0111** | `vrn2_release_v0155` | `1d094c0d5c36` | 被 v0112 取代(套件 v0154 · 共識直連)· (Combined 代號不是台股 4 碼的共識空格 → 資料源 · 自測 51 項 · 套件 v0154)|
| **VRN2_HandleAll_v0102.md**(發行夾 · PowerShell 7 短開機行 + 一段碼 · 不是 .ps1)| **v0102** | `vrn2_release_v0154` | 一行版 `a3d4dc8b9f8b` · 短開機行 `62d8706c9992` | **新**(套件 v0154 · RoundAll v0110 · auto → repair · 短開機行 ASCII 1719 字元 · cmd 一行)|
| **VRN2_RoundAll_v0110.py**(發行夾 · 一支入口 · 不在套件內)| **v0110** | `vrn2_release_v0154` | `cc1d4b5d7a04` | 被 v0111 取代(AAPL 共識空格算 VRN-2)· 套件 v0154 · ⑥f 三類負責方 · Combined 每列原因 · ⑤ 用 v0103 重跑 ⑥f · 自測 50 項)|
| ActivateVRN-2_v0154.py(套件 · 底座 v0136)| **v0154** | 見發行清單 | `91e27fdeb537` | **新**(收據 v0154 · CONSENSUS_JOIN v0103 · 自測多一段 v0154)|
| **VRN2_ConsensusJoin** | **v0103**(薄尾 · v0102 / v0101 / v0100 留著)| runtime v0154 | `01b02104ba23` | **新**(今天的 payload 搬進新清單的 checkpoint · 404 / 一時抓不到重試 · no_coverage / source_gap · 不沿用上次的矩陣 · 13 項)|
| **VRN2_HandleAll_v0101.md**(發行夾 · PowerShell 7 一段碼 · 不是 .ps1)| **v0101** | `vrn2_release_v0153` | 一行版 `c4374130f9f6` | **新**(套件 v0153 · RoundAll v0109 · auto:收據不是 v0153 → 整輪)|
| **VRN2_RoundAll_v0109.py**(發行夾 · 一支入口 · 不在套件內)| **v0109** | `vrn2_release_v0153` | `716bfe2bd911` | 被 v0110 取代(⑥f 一時抓不到算「別的不過」· Combined 404 抄整批摘要)· 套件 v0153 · ⑪ DUPKEY → VRN-2 · 收尾頁同一件事只列一次 · 自測 46 項)|
| ActivateVRN-2_v0153.py(套件 · 底座 v0136)| **v0153** | 見發行清單 | `fbab46f20202` | **新**(收據 v0153 · 管理器 v0257 · 自測多一段 v0153)|
| **VRN_SystemManager**(VRN-2 私有 runtime 線)| **v0257**(薄尾 · PRIOR v0255 · v0256 是共用夾的桌機線)| runtime v0153 | `250cc93df1a4` | **新**(一列一科目:並排表右表值改名 / 剔除 · 沒有列號的同鍵兩值剔除)|
| **VRN2_HandleAll_v0100.md**(發行夾 · PowerShell 7 一段碼 · 不是 .ps1)| **v0100** | `vrn2_release_v0152` | 一行版 `d4efc02c12b2` | **新**(自動選模式 · 取 RoundAll v0108 核對 SHA-256 · 舊套件夾權限可選擇還原 · 印收尾狀態)|
| **VRN2_RoundAll_v0108.py**(發行夾 · 一支入口 · 不在套件內)| **v0108** | `vrn2_release_v0152` | `58576a79c441` | 被 v0109 取代(DUPKEY 算人工 · 收尾頁同一件事列好幾次)· 套件 v0152 · ⑪b 只重跑獨立驗證 · 沿用前版收據 · 自測 44 項)|
| ActivateVRN-2_v0152.py(套件 · 底座 v0136)| **v0152** | 見發行清單 | `dfea97b78013` | **新**(收據 v0152 · 自測多一段 v0152 · 步驟不變)|
| **VRN2_IndependentVerifier** | **v0114**(結構複本 · v0113 留著)| runtime v0152 | `a8b88bc49b89` | **新**(年度 FAIL 依欄位對齊 · 值不同 / 對不齊照樣 FAIL)|
| **VRN2_RoundAll_v0107.py**(發行夾 · 一支入口 · 不在套件內)| **v0107** | `vrn2_release_v0151` | `cbaec6a53e35` | 被 v0108 取代(沒有 ⑪b · 套件 v0151)· 略過取套件時找讀得到啟動器的套件夾(含 <套件>_<時間> · 新的先)· 不跑啟動器 / 自測就不需要套件 · 原夾讀不到時沿用既有新夾 · 自測 41 項)|
| **VRN2_RoundAll_v0106.py**(發行夾 · 一支入口 · 不在套件內)| **v0106** | `vrn2_release_v0151` | `5870c77d1708` | 被 v0107 取代(2026-10-30 14:41 桌機貼回:收尾分類 ② CPU → 提醒 · Combined 代號不是 4 碼 → 人工 / 資料源 + 列檔名 · ⑪ 年度 FAIL 證據(原文表頭 + 科目列依欄位對齊)· 套件安裝不搬暫存夾(Python 3.13 暫存夾權限)· 自測 39 項)|
| **VRN2_RoundAll_v0105.py**(發行夾 · 一支入口 · 不在套件內)| **v0105** | `vrn2_release_v0151` | `9edb8912770f` | 被 v0106 取代(2026-10-30 桌機:v0104 ① 讀本機套件 zip PermissionError → Traceback;讀不到重試 → 證據 → 改從 GitHub 取 → 原夾用不了換新夾 · 每步出例外不中斷 · 收尾頁 / 貼回包照產生 · 自測 34 項)|
| **VRN2_RoundAll_v0104.py**(發行夾 · 一支入口 · 不在套件內)| **v0104** | `vrn2_release_v0151` | `8333c1719127` | 被 v0105 取代(①  讀不到本機 zip 會當掉)· 套件 v0151 · ⑧ 收尾頁 HTML U/I · Combined 空格照原因分 · 自測 29 項)|
| ActivateVRN-2_v0151.py(套件 · 底座 v0136)| **v0151** | 見發行清單 | `a09bbb82bd61` | **新**(收據 v0151 · 自測多一段 v0151 · 步驟不變)|
| **VRN2_IndependentVerifier** | **v0113**(結構複本 · v0112 留著)| runtime v0151 | `da4bd18fa735` | **新**(BADITEM 第二種讀法 · 造假科目照 BADITEM · FAIL 帶科目列)|
| VRN2_LocalRound_v0101.md(docs/handoff/ai · v0100 在 main 不動)| **v0101** | `docs/handoff/ai` | 見 md | **新**(指 操作員一鍵 v0112 → VRN-2 一鍵 v0151 · 貼回包帶收尾頁)|
| **VRN2_RoundAll_v0103.py**(發行夾 · 一支入口 · 不在套件內)| **v0103** | `vrn2_release_v0150` | `71e60ad40352` | **新**(套件 v0150 · 不重抓 ⑥e · ⑪ 證據逐值 · MOPS DENY 說明 · 自測 23 項)|
| ActivateVRN-2_v0150.py(套件 · 底座 v0136)| **v0150** | 見發行清單 | `bc14be14ce1e` | **新**(ConsensusJoin v0102 · ⑥e 明細寫出 Python · 收據 v0150 · 自測 8 段)|
| **VRN2_IndependentVerifier** | **v0112**(結構複本 · v0111 留著)| runtime v0150 | `446a024b312b` | **新**(價格標籤第二種讀法 · 同列標籤 · 對調照 FAIL)|
| **VRN2_ConsensusJoin** | **v0102**(薄尾 · v0101 / v0100 留著)| runtime v0150 | `cb3daed8e631` | **新**(404 無覆蓋代號不納閘 · 再跑一次 · 6 項)|
| **VRN2_RoundAll_v0102.py**(發行夾 · 一支入口 · 不在套件內)| **v0102** | `vrn2_release_v0149` | `d8848103bcb0` | **新**(套件 v0149 · pwsh 一行 · ② / ⑤ 擷取 Python 照 VDF 界線 · ⑥ ⑪ FAIL 證據 / 驗證器版本 / ⑥f 閘列 · docstring 反斜線 · 自測 20 項)|
| ActivateVRN-2_v0149.py(套件 · 底座 v0136)| **v0149** | 見發行清單 | `94c3ee0841aa` | **新**(收尾閘 VerbatimVerifier v0105 · ⑥e 經 MarketFetchRun · 收據 v0149 · 自測 7 段)|
| **VRN2_VerbatimVerifier** | **v0105**(薄尾 · v0104 留著)| 套件 + runtime v0149 | `6c9ec7a226bf` | **新**(行尾連字號 U+FFFE / U+0002 / 「-」+ 換行 · 5 項)|
| **VRN2_IndependentVerifier** | **v0111**(結構複本 · v0110 留著)| runtime v0149 | `011de746dec5` | **新**(摘錄讀法 = VerbatimVerifier v0105 · 自測 30/30 + v0110 + v0111)|
| **VRN2_MarketFetchRun** | **v0100**(新家族 · 只用標準庫)| runtime v0149 | `1d245a05e88f` | **新**(⑥e:共用 MarketFetch 的 fetch_python 換成合 VDF 界線的 Python · 都不合不啟動引擎 · 9 項)|
| **VRN2_RoundAll_v0101.py**(發行夾 · 一支入口 · 不在套件內)| **v0101** | `vrn2_release_v0148` | `ee9500d3a352` | **新**(套件 v0148 · 擷取 Python 不用退役環境 · 除錯帶摘錄 / 錯誤原文 · 重跑指令兩種殼都能貼 · 自測 16 項)|
| ActivateVRN-2_v0148.py(套件 · 底座 v0136)| **v0148** | 見發行清單 | `9996f6ded67c` | **新**(指向 UIAction v0110 / ConsensusJoin v0101 / HistoryAlign v0102 · 收據 v0148 · 自測 6 段)|
| **VRN2_UIAction** | **v0110**(薄尾 · v0109 留著)| runtime v0148 | `b103d1f0f9b7` | **新**(自測不受 VIA_ROOT / VRN2_* 影響 · 7 項)|
| **VRN2_ConsensusJoin** | **v0101**(薄尾 · v0100 與共識引擎 v0120 留著)| runtime v0148 | `1fc0d0ec7cff` | **新**(上櫃 .TWO 對應表來自市場冊 · 引擎經 shim 帶起 · 11 項)|
| **VRN2_HistoryAlign** | **v0102**(薄尾 · v0101 / v0100 留著)| runtime v0148 | `783da69350ca` | **新**(科目對應排除部分 / 別口徑列 · 檢驗 UNCLEAR vs FAIL · 11 項)|
| **VRN2_RoundAll_v0100.py**(發行夾 · 一支入口 · 不在套件內)| **v0100** | `vrn2_release_v0147` | `2b74f8ea1435` | **新**(取套件 → 診斷 → 全部自測 → 跑 → 自動修 → 除錯 → 貼回包 · 自測 12 項)|
| ActivateVRN-2_v0147.py(套件 · 底座 v0136)| **v0147** | 見發行清單 | `756103406fce` | **新**(OutputStore v0101 / DataIntegrate v0101 · ⑬b 在 ⑬ 前 · ⑥e 擷取 Python · 自測從 runtime zip 取模組 + 不受環境影響)|
| **VRN2_OutputStore** | **v0101**(薄尾 · v0100 留著)| runtime v0147 | `624fd409bd0e` | **新**(七冊 · 冊 × 原檔 × 列雜湊判缺 · pyarrow / duckdb 自測各 8 項)|
| **VRN2_DataIntegrate** | **v0101**(薄尾 · v0100 留著)| runtime v0147 | `da98e05bc6a6` | **新**(限深走訪 · 只問像 VRN-2 的檔 · 自測 7 項)|
| **VRN2_HistoryAlign** | **v0101**(薄尾 · v0100 留著)| runtime v0147 | `8791b4a37b36` | **新**(單位換算後才比 · 別的單位只覆蓋不刪 · 同量級才刪 · 不明不動 · 成長率段只做比率 · 自測 6 項)|
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

## 7. 本輪(v0153 → v0154 + ConsensusJoin v0103 + VRN2_RoundAll_v0110 + VRN2_HandleAll_v0102 · 桌機 20:09 整輪貼回)

| # | 剩下的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | ⑥f gate FAIL_CLOSED(8358 / 2891 `ASSIGNED_JSON_NOT_FOUND`)· 收尾 VRN-2 2 項 | v0102 拿掉 404 代號再跑 → 引擎 checkpoint 雜湊含代號清單 → 整批重抓 → 鉅亨第二輪回沒有資料的頁 | ConsensusJoin v0103:今天的 payload 搬進新清單的 checkpoint · 404 / 一時抓不到重試 · 還是不過 → 不納入閘(暫缺 = 黃 · 資料源)| 自測 13(含不連網的引擎實跑)· 桌機狀態重演:v0109 OPEN VRN-2 2 → v0110 repair BLOCKED VRN-2 0 |
| b | Combined 6 列算成 404(其中 2 列不是)| join 把整批摘要抄進每列;收尾頁用字串找「鉅亨沒有 FactSet 頁」| v0103 join 每列寫自己的原因 · RoundAll v0110 每列看代號 | 自測 ⑩ ㊺ |
| c | 修 ⑥f 要再整輪 37 分鐘 | RoundAll 沒有只重跑 ⑥f 的路 | ⑤ 自動修:套件 runtime 的 v0103 補放 → 重跑 ⑥f → Combined;Handle-All auto → repair | 沙盒 e2e:auto → repair 29 秒 · 再一次 → 沒有要修的 |
| d | PowerShell 7 貼 8.7k 字元一行就當掉 | PSReadLine 2.4.5 在 133 × 33 視窗的已知毛病 | 短開機行(ASCII 1,719 字元 · 約 13 行)取 md 核對 SHA-256 才執行 · cmd 一行不經輸入列 | 剖析 0 錯 · 詞序列相同 · 竄改 → 不執行 |
| e | (沙盒整輪測出)引擎整批沒抓到時讀上次的矩陣當這次的 | v0101 只看矩陣檔在不在 | v0103 看矩陣時間:比這次早 → 不沿用 · engine_no_output → 收尾頁算資料源 | 自測 ⑫ ㊿ · 沙盒整輪(全部連不上)|
| — | MOPS DENY(VCGC)· MQ-1560 OCR 4 點 / 年度缺項 3 份(人工)· Apple 非台股 / 神達 · 緯穎報告日前沒有還原價 / 鉅亨沒有 FactSet 頁(資料源)| VCGC 決定 / 要人看原文 / 外部來源 | 不在 VRN-2 | 收尾頁分好 |

## 7.0q 前一輪(v0152 → v0153 + 管理器 v0257 + VRN2_RoundAll_v0109 + VRN2_HandleAll_v0101 · 桌機 18:34 Handle-All 貼回)

| # | 剩下的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | ⑪ DUPKEY 45(6933 AMAX 第 8 頁 37 · 凱基 2891 第 5 頁 8)| 並排兩張表擷取成一列 → 右表的值掛在左表科目下;沒有列號的同鍵兩值 | 管理器 v0257 一列一科目(改名 / 剔除 · 不猜)| 自測 10 · 桌機冊重放剔除正好 45 · 容器 14 份 0 變動 |
| b | 收尾頁把 DUPKEY 算人工 · 同一件事列 2~3 次 | 規則只看燈號與步驟名 | RoundAll v0109 DUPKEY → VRN-2 · 同根合一 | 自測 ㊸ ㊹ · 18:34 那 14 列重算 |
| c | Handle-All auto 在舊輸出冊上只重驗 | v0100 只看收據 ≥ v0151 | v0101:收據不是 v0153 → 整輪 | 沙盒桌機情境 auto → full |
| — | MOPS DENY(VCGC)· MQ-1560 OCR / EST 1 / 年度缺項 3 份(人工)· Apple 非台股 / 神達 · 緯穎報告日前一週沒有還原價(VDF 日線視窗 PARTIAL · 資料源)· VDF v0102 安裝 | VCGC 決定 / 要人看原文 / 外部來源 / VDF 自己的系統 | **沒修**(收尾頁分給負責方 · VDF 只讀)| — |

---

## 7.0p 前一輪(v0151 → v0152 + VRN2_RoundAll_v0108 + VRN2_HandleAll_v0100 · 操作員「GENERATE A PS CODE TO HANDLE ALL」)

| # | 剩下的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | ⑪ 年度數據 FAIL 1(Daiwa aspeed PBR (x) 26E 冊值 n.a.)| 字元框讀法讀不出該頁科目列 / 表頭;原文 26E 就是 n.a. | IndependentVerifier v0114:FAIL 用第二種讀法依欄位對齊(同一讀法 · 個數相等才對)| 自測 · 整輪 4905 筆與 v0113 相同 · 變造照樣 FAIL |
| b | 改驗證器要重跑整輪 66 分鐘 | RoundAll 沒有單獨重驗的步驟 | RoundAll v0108 `verify`(⑪b)· 沿用前版收據 | 自測 ㊵ ㊶ ㊷ · 沙盒桌機情境 |
| c | 每次要記好幾行指令 / 環境變數 | — | Handle-All v0100(PowerShell 7 一段碼 · auto 選模式)| 沙盒 auto(verify / full)· report · 竄改 · 錯模式 · 非 git 倉 · 讀不到的舊夾 |
| — | MOPS DENY(VCGC)· MQ-1560 OCR 4 點 / 年度缺項 3 份(人工)· Apple 非台股 / 報告日前沒有日資料(資料源)· 舊套件夾 ACL | VCGC 決定 / 要人看原文 / 外部來源 / 以前用系統管理員身分跑過 | **沒修**(收尾頁分給負責方 · ACL 答 y 才動)| — |

---

## 7.0o 前一輪(v0150 → v0151 + VRN2_RoundAll_v0104 · 收尾輪 · 操作員「解決剩餘系統問題 HTML U/I CLOSE OUT」)

| # | 剩下的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | ⑪ 年度 BADITEM 19(MS-3665 / MS-8358 / MS-8210 / Daiwa aspeed · 值都在該頁)| 「科目本頁原文沒有」只問字元框讀法(桌機的函式庫版本讀壞科目列 · 同 v0112 的側欄)| IndependentVerifier v0113:先用第二種讀法找科目 | 原樣 0 差異 · 造假 60 / 60 BADITEM · 模擬讀壞 59 / 59 回 PRESENT · 整支跑同判 |
| b | 跑完不知道結案沒有、剩下的是誰的 | 總表只有燈號數 | RoundAll v0104 ⑧ 收尾頁(負責方 · 結案狀態 · 待辦表 · 檔案 · 下次指令)| 自測 ㉓ ~ ㉗ · 桌機 19:00 那輪試算 BLOCKED · chromium 桌面 / 深色 / 手機 390 無水平捲動 · 無 JS 錯誤 |
| c | Combined「調整後目標價空 15」| 報告本來沒有目標價的列也算缺 | 空格照原因分 | 自測 ㉕ |
| — | MOPS DENY · MQ-1560 OCR 4 點 · 年度缺項 3 份 · ⑥e 30 分鐘 | VCGC 決定 / 要人看原文 / 操作員規則 | **沒修**(收尾頁分給負責方)| — |

---

## 7.0n 前一輪(v0149 → v0150 + VRN2_RoundAll_v0103 · 桌機 2026-10-29 19:00 跑 RoundAll v0102 的貼回)

| # | 桌機看到的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | ⑪ MS-6669 現價 3510 FAIL「在目標價標籤旁」· MS-3661 現價 3190 FAIL「前 4 頁沒有這個數」 | 冊值 = 原文那行(v0102 證據);字元框讀法在桌機漏讀 / 配錯側欄 | IndependentVerifier v0112:第二種讀法 · 同列標籤 | 真 MS-3661 模擬漏讀 → PASS · 對調 → FAIL · 回歸 193 不變 · 變造 12 / 12 |
| b | ⑥f gate FAIL_CLOSED | 只因 6933 / 4171 鉅亨 404(沒有 FactSet 頁)| ConsensusJoin v0102:不納入 · 再跑一次 | 自測 ④(假引擎)+ v0101 離線引擎實跑 |
| c | ⑤ 又把 ⑥e 重抓一輪(約 35 分鐘)| 明細「Python 本行程」被 v0102 當成用錯 Python | 啟動器 v0150 明細寫路徑 + 合界線 · RoundAll v0103 經 runner 跑過不重抓 | 自測 ⑳ |
| d | ⑪ 證據只看到電話行 | 字串包含(730 ⊂ 2730-2869 · 38 ⊂ 4388)| RoundAll v0103 逐值 · 數字相等 · 跳過聯絡行 | 自測 ㉑ · 真 MS-3661 三個值各對到自己那行 |
| e | ⑥e 財報 PermissionError「Existing VIA network bridge denied」· ⑬b 無歷史 | VIA 鎖版網路工具合規層對 MOPS 回 DENY | **不繞**;RoundAll v0103 印說明 → 交 VCGC | 自測 ㉒ |
| — | MS-8358 / MS-8210 · daiwa 年度 1 格 · ⑥e 30 分鐘 | 要證據 / 操作員規則 | **沒修** | — |

---

## 7.0m 前一輪(v0148 → v0149 + VRN2_RoundAll_v0102 · 桌機 2026-10-29 17:01 跑 RoundAll v0101 的貼回 · 操作員「我的PS是7.6.9請用一個指令完成剩餘工作完成系統」)

| # | 桌機看到的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | 收尾 rc 1:四點原文核對 3014TT 第 3 點 FAIL(⑪ 一標題四重點 FAIL 1)| PDFium 把行尾連字號寫成 U+FFFE、吃掉換行;v0104 只在下一字小寫時接合 | VerbatimVerifier v0105 + IndependentVerifier v0111 | 產生的 PDF:v0104 FAIL · v0105 PASS · 沙盒 52 點不變 · 啟動器自測 v0149 段 |
| b | ⑥e「擷取環境缺套件(…\envs\via_tw_fetch\Scripts\python.exe)」· last_error = VDF pip exit 1 | MarketFetch v0112 的 fetch_python() 只要 via_tw_fetch 在就用,不管啟動器給的 Python | MarketFetchRun v0100(只換 fetch_python · 照 VDF 引擎自己的界線挑 · 都不合不啟動引擎)| Windows 版面重現 · runner 9 項(假 venv:沒裝 / 下界 / 上界 / 退役 / VIA_FETCH_PY 不合)· 端到端 ⑥e 收據帶每個候選缺什麼 |
| c | `SyntaxWarning: invalid escape sequence '\l'` | v0101 docstring 的 `market\vdf\…` 單一反斜線 | RoundAll v0102 全部成對 | `-W error` 編譯:v0101 SyntaxError 重現 · v0102 乾淨 · 自測 ⑯ |
| d | ⑪ 基本資料 FAIL 4(MS 三份現價 · MS-8210 上漲)| 容器同一份 MS-3661 擷取 3190.00 · PASS → 桌機的冊值不同,看不到 | RoundAll v0102 ⑥ 印證據(冊值 + 原文那行)+ `VRN2_FailEvidence_latest.json` | 自測 ⑱ · 真 MS-3661:「Shr price, close (Dec 3, 2025) NT$3,190.00」|
| e | ⑥f gate FAIL_CLOSED | 共識引擎品質閘:FactSet 沒覆蓋的代號 | 不改引擎語意;⑥ 印閘不過的列 | 自測 ⑰ |
| f | 「我的 PS 是 7.6.9」 | 舊一行用 powershell(5.1)| pwsh 與 powershell 兩行(同一段開機碼)| pwsh 7.4.6 跑 pwsh 那行完成端到端 · 兩行解碼 = 開機碼 |
| — | ⑥e 沒有合界線的 Python · MS FAIL 真因 · daiwa 年度 1 格 | 要 VCGC 建環境 / 要證據 | **沒修**(VRN-2 不裝不改 VDF;證據下一輪印)| — |

---

## 7.0l 前一輪(v0147 → v0148 + VRN2_RoundAll_v0101 · 桌機 2026-10-29 14:40 第一次跑 RoundAll 的貼回)

| # | 桌機看到的 | 根因 | 修法 | 實測 |
|---|---|---|---|---|
| a | ③ UIAction v0109 --selftest ④ FAIL(容器過)| rerender() 讀殼的 VIA_ROOT → 自測真的重渲染 Workbench | UIAction v0110:自測先拿掉 VIA_ROOT / VRN2_* 再還原 | 容器設 VIA_ROOT:v0109 FAIL 重現 · v0110 7 項過 · 端到端殼有 VIA_ROOT 照綠 |
| b | ⑥f 8 檔 Yahoo 404 `####.TW` · gate FAIL_CLOSED | 鉅亨對上櫃也回 TWS:#### → 引擎一律 .TW | ConsensusJoin v0101:市場冊對應表 + 引擎 shim · 同日快取用錯尾碼的重抓 | 自測 11 項(引擎原本 5274 → .TW · patch → .TWO · 離線 fixture .TWO 拿到 YFinance 中位數)|
| c | ② 擷取 Python = `envs\via_core.retired-…` | RoundAll 把 envs 下任何裝齊套件的夾都當候選 | RoundAll v0101 略過 retired / backup / bak / old / deprecated / archive | 自測 ⑫ · 端到端放一個退役夾 → 略過並列出 |
| d | ⑬b 檢驗 534 不過 120 | 科目對錯列(其他營收 · 應付所得稅 · 負債與權益合計 · 少數 · 調整後 · 部門成長率)+ 成本負數 + 預估調整表三個值 | HistoryAlign v0102 | 自測 11 項 · 容器資料不過 74 / 218 → 5 / 192 |
| e | PowerShell 裡 `python "%USERPROFILE%\…"` 找不到檔 | %USERPROFILE% 只有 cmd 展開 | RoundAll v0101 最後印完整路徑的重跑指令;md 分 cmd / PowerShell 寫 | 自測 ⑮ |
| f | 四點 FAIL / ⑥e 紅在主控台只有一行 | 證據只在貼回包 | RoundAll v0101 除錯報告印摘錄原文 · last_error 最後幾行 · Yahoo 404 / 上櫃數 | 自測 ⑬ ⑭ |
| g | (建置)操作員一鍵 v0108 md 的歷史段落被改成 v0108 / v0147 | build147 對整份 md 做 .replace("v0107", "v0108") | v0109 從 v0107 的 md 還原歷史段落(v0108 檔不改)| 讀 md 比對 |
| — | 3014TT 第 3 點 FAIL → rc 1 · MS 四份現價 / 上漲 FAIL · ⑥e VDF 致命錯 · 缺年度 3 份 | 要原 PDF / 貼回包 | **沒修**(容器只有合成小 PDF;MS-3661 真檔在容器新跑是 PASS → 桌機的值來自擷取快取)| — |

---

## 7.0k 前一輪(v0146 → v0147 + VRN2_RoundAll_v0100 · 操作員「generate a py code to handle all above and fix all test all debug all」)

| # | 缺陷 | 怎麼抓到的 | 修法 | 實測 |
|---|---|---|---|---|
| a | 長線 Parquet 庫的新冊永遠 0 列(已知原檔不再追加)| 寫 RoundAll ⑤「庫裡還沒有新冊」判斷時讀 OutputStore v0100 | OutputStore v0101:冊 × 原檔 SHA × 列雜湊判缺 · 七冊 · 舊庫列沒有列雜湊就現算 | 自測 8 項 × pyarrow / duckdb · 端到端 Combined / FinancialAligned 進庫 · 再跑不重寫 |
| b | ⑬b 在 ⑬ 之後 → 本輪對齊冊進不了庫 | 同上 | 啟動器 v0147 對調 | 啟動器自測檢查順序 |
| c | 舊資料庫掃描走整個 OneDrive · 任何 CSV 都問 | 讀 DataIntegrate v0100 的 rglob | DataIntegrate v0101 限深 + 像不像 VRN-2 | 自測 7 項 · 端到端家用記帳 CSV 略過 |
| d | ⑥e 用 VRN-2 的 Python(--fill 要 pandas)· fetch 失敗不 fill | 讀 MarketFetch --fill | 擷取 Python · 照樣 fill | 啟動器自測 |
| e | 啟動器 --selftest 在真套件夾 FileNotFoundError(v0144 ~ v0146)| 把 v0146 套件放在隔離夾跑自測 | 從 runtime zip 取模組 | 隔離夾自測 PASS;v0146 同條件重現失敗 |
| f | 啟動器 --selftest 在設了 VRN2_OUTPUT_DIR 的殼自己失敗(v0144 起)| RoundAll 第一次端到端 ③ 紅 | 自測時清掉再還原 | 帶 VRN2_OUTPUT_DIR / 上限 / 開關變數跑自測 PASS |
| g | RoundAll `--launcher-args "--no-install"` 被當選項 | 端到端第一次啟動 | 併成 `--launcher-args=…` | RoundAll 自測 ⑪ |
| h | ⑬b 歷史對齊把別的單位 / 成長率列誤進刪除區(沙盒 100 列,其中 61 列是單位或成長率)| RoundAll 只修回合放合成市場資料後看刪除區 | HistoryAlign v0101:換算後才比 · 同量級才刪 · 不明不動 · 成長率段只做比率 | 自測 6 項 · 同一份沙盒資料刪除 100 → 39 · 不明 44 |

---

## 7.0j 前一輪(v0145 → v0146 · 桌機 2026-10-29 10:25 貼回 + 操作員 U/I 與資料需求)

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

| 0 | **(v0157)** 桌機 PowerShell 7 貼 `vrn2_release_v0157/VRN2_HandleAll_v0105.md` **最上面那行(443 字元)**→ auto → repair → 閘照舊預期 BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2;要經網路工具抓共識 → 操作員先設 `$env:VIA_SCRAPE_CONSENT='YES'`(VIA_NET_CONSENT 已是 YES)→ 人工 2;整輪時 ③ 缺的經 VCGC 安裝閘 → 收尾頁 VCGC 列沒裝起來的 | 貼回 |
| 0 | **(v0156)** 桌機 PowerShell 7 貼 `vrn2_release_v0156/VRN2_HandleAll_v0104.md` **最上面那行(443 字元)**→ 看 ③b 同意閘:要經網路工具抓 → 操作員自己先設 `$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'` → auto → repair → 閘開預期 BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2(除錯報告「⑥f 經 VIA 網路工具」綠)· 閘關預期人工 3;⑥f 黃 / VRN-2 有項 → 貼回包 | 貼回 |
| 0 | **(v0155 · 2026-10-31 02:06 後)** 桌機 PowerShell 7 貼 `vrn2_release_v0155/VRN2_HandleAll_v0103.md` **最上面那行(443 字元)**→ auto → repair → 收尾頁應 BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2;不是 → 貼回包 | 貼回 |
| 0 | **(v0154 · 2026-10-30 20:09 後)** 桌機 PowerShell 7 貼 `vrn2_release_v0154/VRN2_HandleAll_v0102.md` **最上面那行短的**(cmd 視窗用 cmd 那行)→ auto 選 repair(幾分鐘 · 不整輪)→ ⑥f 用 ConsensusJoin v0103 重跑 → 收尾頁 ⑥f 應是綠或資料源 · VRN-2 0;還是 VRN-2 → 貼回包 | 貼回 |
| 0 | **(v0153 · 2026-10-30 18:34 後)** 桌機 PowerShell 7.6.9 貼 `vrn2_release_v0153/VRN2_HandleAll_v0101.md` 的**那一行**(auto → full · 約 66 分鐘:管理器 v0257 重做輸出冊)· ⑪ DUPKEY 應為 0 · 收尾頁應為 BLOCKED(VCGC 1 · 人工 3 · 資料源 2);DUPKEY 不是 0 或「VRN-2 要修」不是 0 → 貼回包 | 貼回 |
| 0 | **(v0152 · 2026-10-30 17:06 後)** 桌機 PowerShell 7.6.9 貼 `vrn2_release_v0152/VRN2_HandleAll_v0100.md` 的**那一行**(auto → verify:套件 v0152 · ⑪b 用 v0114 重驗 · 收尾頁)· 收尾頁「VRN-2 要修」應為 0;不是 0 → 貼回包 | 貼回 |
| 0 | **(v0151 · 2026-10-30 14:41 後)** 桌機 PowerShell 7.6.9 貼 `vrn2_release_v0151/VRN2_RoundAll_v0107.md` 的 **PowerShell 7 原生一行**(只重做報告 + 收尾頁:先 `$env:VRN2_ROUNDALL_ARGS = '--only report,closeout,pasteback'`) · 看收尾頁 ⑪ 年度數據 FAIL 證據(Daiwa aspeed PBR 26E)對齊的結論 · 舊套件夾要清就以系統管理員身分 icacls /reset | 貼回 |
| 0 | **(v0151 · 2026-10-30)** 桌機 PowerShell 7.6.9 貼 `vrn2_release_v0151/VRN2_RoundAll_v0105.md` 的 **PowerShell 7 原生一行**(v0104 在 ① 讀本機套件 zip PermissionError 當掉 · 兩次)· 看 ① 那列 GRAY 證據(icacls / 啟動器鎖 PID)找出誰佔著那個檔 | 貼回 |
| 0 | **(v0151)** 桌機(cmd 或 PowerShell 7.6.9)貼 `vrn2_release_v0151/VRN2_RoundAll_v0104.md` 的 **pwsh 那一行** · 跑完看自動開的收尾頁:狀態若是 BLOCKED / REVIEW 就照負責方處理;OPEN 才是 VRN-2 要修 → 貼回包 | 貼回 |
| 0b | **(v0151)** 收尾頁「人工核對」:MQ-1560 影像頁 4 點對原圖 · ⑪ 還標著的值看逐值原文 · 年度缺項 3 份確認原文有沒有年度表 | 操作員 |
| 0 | **(v0150)** 桌機(cmd 或 PowerShell 7.6.9)貼 `vrn2_release_v0150/VRN2_RoundAll_v0103.md` 的 **pwsh 那一行** · 跑完看 ⑪ 是否只剩 MS-8358 / MS-8210 與它們的逐值證據 | 貼回 |
| 0a | **(v0150)** MOPS 財報:VIA 鎖版網路工具合規層 DENY → VCGC 決定要不要放行 mops.twse.com.tw(⑬b 歷史對齊靠它)| VCGC |
| 0 | **(v0149)** 桌機(PowerShell 7.6.9)貼 `vrn2_release_v0149/VRN2_RoundAll_v0102.md` 的 **pwsh 那一行**(一個指令:取 RoundAll v0102 → 核對 → 跑完全流程 → 貼回包)· 跑完看 `⑥ ⑪ 基本資料 FAIL 證據` 那幾行(或上傳 `Downloads\VRN2_PasteBack_<時間>.zip`)| 貼回 |
| 0a | **(v0149)** ⑥e:② 若印「沒有合 pandas>=2.2,<3 … 的 Python」→ 交 VCGC 照印的指令建 `envs\via_tw_fetch`(帶界線、加引號);建好後 ⑥e 會自動選它 | VCGC |
| 0 | **(v0148)** 桌機貼 `vrn2_release_v0148/VRN2_RoundAll_v0101.md` 的一行(或 cmd:`python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0101.py"` · PowerShell:`python "$env:USERPROFILE\Downloads\VRN2_RoundAll_v0101.py"`)· 跑完**上傳 `Downloads\VRN2_PasteBack_<時間>.zip`**(3014TT 第 3 點 · MS 四份 · VDF 致命錯都要它)| 貼回 zip |
| 0a | **(v0148)** ⑥e VDF 引擎第一次會自己用 pip 建 `envs\via_tw_fetch`(桌機這輪就在下載);建好後下一輪 RoundAll ② 就用它(不再碰退役環境)· 仍致命錯 → 看貼回包 `vrn2/market/vdf/last_error.txt`(VDF 的事,VRN-2 只讀)| 貼回 zip |
| 0b | **(v0148)** 擷取快取:桌機「擷取沿用 52 / 52」—— 若 MS 四份的值是舊引擎留下的,要清這幾份的擷取快取再跑(先看貼回 zip 的 BasicInfo 再決定)| 貼回 zip |
| 0 | **(v0147)** 桌機跑一支 Python:貼 `vrn2_release_v0147/VRN2_RoundAll_v0100.md` 的一行(或 `python Downloads\VRN2_RoundAll_v0100.py`)· 跑完上傳 `Downloads\VRN2_PasteBack_<時間>.zip`;要只修不重跑 → `--skip-run`;建好 via_tw_fetch 環境後 `--skip-run` 會自動重抓市場 / 共識並補庫 | 貼回 zip |
| 0a | **(v0147)** RoundAll ⑤ 的修正只做「重跑某一步」:四點原文核對 FAIL / 年度數據缺項 / 冪等 NONDETERMINISTIC 這類要看原 PDF 的,只列清單不自動改 | 貼回 zip |
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

## 9b. 結案判定(CLOSE OUT · v0151)

VRN-2 自己的收尾頁:`VIA_Reports\vrn2\VRN2_CloseoutUI_latest.html`(RoundAll v0104 寫 · 只讀其他系統的檔)。VCGC 的 `closeout_lamp` 才是 VCGC 驗收(四系統對等 · 只讀互看)。

| 狀態 | 意思 | 算不算成功 |
|---|---|---|
| OPEN | VRN-2 還有要修的(貼回包給 AI)| 否 |
| BLOCKED | VRN-2 側沒有待修 · 剩 VCGC 的決定 / 安裝(例:MOPS 被 VIA 網路工具 DENY)| 否 |
| REVIEW | 剩要人看原文的(OCR 影像頁 · ⑪ 待核對值 · 缺年度數據)| 否 |
| DATA_GAP | 剩外部來源本來沒有的(鉅亨 404 · Yahoo / TWSE 沒有)· 已附證據 | 否(VRN-2 側結案)|
| PASS | 全綠(或只剩提醒)| 是 |

**v0157(2026-10-31)**:③ 預設只檢查 · 缺的經 VCGC 安裝閘(不再本環境 pip + numpy<2 約束)· 啟動器 v0157 · RoundAll v0113 · Handle-All v0105 · runtime v0156 原樣。

**v0156(2026-10-31)**:共識引擎 v0122 / Matrix v0112 經 VIA 網路工具 + 加速器出網 · ConsensusJoin v0104 · 啟動器 v0156 · RoundAll v0112 · Handle-All v0104 · VCGC 環境工具衝突 0;真抓待桌機。

**v0155(2026-10-31)**:桌機 02:06 repair → ⑥f GREEN;收尾 OPEN VRN-2 1 是 v0110 的分類錯(AAPL)· v0111 修 · 預期 BLOCKED · VRN-2 0。

**v0154(2026-10-30)**:桌機 20:09 = OPEN(VRN-2 2 = ⑥f 共識 · 管理器 v0257 生效 DUPKEY 0);v0154 修 ⑥f(ConsensusJoin v0103)· 收尾頁 ⑥f 分類 · repair 模式 · 短開機行;沙盒重演 repair 後 VRN-2 0。

**v0153(2026-10-30)**:桌機 18:34 = BLOCKED(VRN-2 0 · VCGC 3 · 人工 5 · 資料源 2),但 ⑪ DUPKEY 45 是 VRN-2 的輸出冊問題(v0109 起算 VRN-2);v0257 整輪後預期 BLOCKED · VCGC 1 · 人工 3 · 資料源 2,以桌機收尾頁為準。

**v0152(2026-10-30)**:桌機 17:06 v0107 快速模式 = OPEN(VRN-2 1 · VCGC 3 · 人工 4 · 資料源 2);VRN-2 那 1 項由 v0114 處理 → 預期 BLOCKED(VRN-2 0),以桌機跑 Handle-All 後的收尾頁為準。

目前(桌機 19:00 那輪試算 · v0151 還沒在桌機跑):**BLOCKED** —— VRN-2 0 · VCGC 3(MOPS DENY)· 人工 8 · 資料源 4。下一輪桌機跑 v0151 後以收尾頁為準。

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

- **(v0157)** **VRN-2 不 pip**:缺的套件一律交 VCGC 安裝閘 `CGC_MDL056_InstallGate`(最高版號 · 只呼叫 · 不改它);它只裝進呼叫它的 Python(`--user`)· 要 `VIA_NET_CONSENT=YES`(SuperAccel 安裝道)。沙盒 / 容器測試別讓它真的裝(同意閘不設 = 誠實 FAIL)。
- **(v0157)** **沙盒整輪前後比 `pip freeze`**:v0156 的整輪讓管理器 envcheck 改了容器 venv(numpy 降版)而沒人發現;v0157 起 e2e 腳本前後比對。

- **(v0156)** **出網一律經 VIA 網路工具(SUP_MDL740_NetUnified 最高版號)**:DENY = 停,不換道直連、不重試;同意閘 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 是操作員的決定,VRN-2 / AI **永不代設**,只讀、只告訴操作員怎麼開。
- **(v0156)** **換了出網方式要看 checkpoint 是誰抓的**:引擎版號字串 v0120 / v0122 都是 2.0.0、input_hash 一樣 → 直接續跑就沿用了直連抓的 payload(等於沒「再抓」);ConsensusJoin v0104 用 `consensus\VRN2_Consensus_NetTool.json` 記哪份 checkpoint 是經網路工具抓的。
- **(v0156)** **裝套件只經 VCGC 的環境工具**(EnvPlan 計畫 / InstallGate 裝 · 前後 pip check 衝突 0);VRN-2 只檢查、不 pip。

- **(v0155)** **改分類規則後要拿上一次桌機的每一列重算一次**:拿掉一個「碰巧對」的條件(整批摘要字樣)會讓本來靠它的列(AAPL)掉到預設的 VRN-2;每個空格原因都要有自己的條件。
- **(v0155)** **操作員貼的東西越短越好**:長碼放 md,貼一行 ASCII 的短行去取、核對 SHA-256 再執行;回覆裡只放那一行,不要把長的也貼出來讓人選錯。

- **(v0154)** **「續跑沿用」要用引擎自己的規則驗**:共識引擎的 checkpoint 雜湊含代號清單 / 日期 / 模式 —— 換清單就是新的一份。要沿用就用它自己的函式(雜湊 · payload 路徑 · sha256 · 封存)搬,不要自己算。
- **(v0154)** **一時抓不到 ≠ 程式錯**:`ASSIGNED_JSON_NOT_FOUND` / 逾時 / 429 / 5xx / 連線中斷 → 先等一下重試、只重抓那幾檔;重試後還是沒有 → 寫明「鉅亨這次沒給」(黃 · 資料源)。404 頁面不存在也可能一時的(7728)。
- **(v0154)** **每列的原因要是那一列自己的**:不要把整批摘要抄進每列,收尾頁也不要用字串搜整批摘要來判斷某一檔。
- **(v0154)** **引擎沒產出時不讀舊檔**:rc ≠ 0、沒有 Gate 行 → 矩陣 / 品質矩陣都可能是上次的;看檔案時間。
- **(v0154)** **給操作員貼的一行要短**:PowerShell 7 的輸入列(PSReadLine)在小視窗貼很長的一行會當掉;長碼放 md,貼一行短的(ASCII)去取、核對 SHA-256 再執行。

- **(v0153)** **收尾頁「VRN-2 0」不等於輸出冊乾淨**:每次桌機貼回都要看驗證摘要的 DUPKEY / PRESENT 理由行;驗證器寫「錯值」的就是 VRN-2 的事,不能留在「人工」。
- **(v0153)** **撞鍵要把 ROW / SECTION / SUBCOL 算進鍵**:只用 (檔 · 頁 · 表 · 科目 · 期間) 會把「同一個科目字在不同列」(Percent of Revenues · YoY (%))誤當錯;真正的錯是同一列同科目同期間兩個值。
- **(v0153)** **修輸出冊的薄尾只動撞鍵的列**:找得到同一列自己的科目名才改名,找不到就移剔除冊(帶理由)· 不猜科目 · 先拿桌機那份冊重放、再拿容器真檔確認 0 變動。
- **(v0153)** **別的系統的包(例 VDF v0102)只讀**:看它的說明與證據,告訴操作員跟 VRN-2 剩下的項目有沒有關;安裝 / 修改是那個系統與 VCGC 的事。

- **(v0152)** **驗證器說 FAIL 也要被驗**:FAIL 證據顯示原文 = 冊值時,是驗證器讀法的問題 → 修驗證器(出新版號 · 結構複本),不是改輸出;放寬一定配變造(冊值改 n.a. · 換欄 · 亂碼)確認還是 FAIL。
- **(v0152)** **只改了驗證器就不要叫使用者重跑整輪**:RoundAll `verify`(⑪b)用上一輪輸出冊重驗;收據沒有這版的就沿用前版的,改之前先備份、修正紀錄合併。
- **(v0152)** **給 PowerShell 7 的一段碼**:包在 `& { … }`、錯了 `return` 不 `exit`(視窗不關)· 一行版由可讀版機械合併(上一行 `{` 結尾或下一行 `}` 開頭用空白,其他用 `; `)· `} else {` / `} catch {` 要同一行 · 兩版用 PowerShell 剖析器比對詞序列 · 中文緊接變數時寫 `$($x)`。
- **(v0152)** **權限修復要使用者同意**:讀不到的舊夾只列出來、不擋;答 y 才跳 UAC 跑 `icacls /reset`(還原成繼承 · 不刪檔)。

- **(v0151 · 2026-10-30)** **不要把 tempfile.mkdtemp 建的夾整個搬到使用者看得到的地方**:Python 3.13 在 Windows 給它只限擁有者的權限,搬過去跟著走;要在目的地正常建夾、逐檔複製。
- **(v0151 · 2026-10-30)** **收尾分類規則認不出來 = VRN-2 是對的預設,但每次桌機出現新的「VRN-2 要修」都要回頭看是不是規則不夠細**(CPU 忙 · 代號不是 4 碼),補規則時寫清楚理由。
- **(v0151 · 2026-10-30)** **一支入口不准整支當掉**:每一步都包起來(例外只記那一步紅),收尾頁 / 貼回包一定要產生;讀不到的檔先重試、再印證據、再繞路(GitHub / 新夾),原檔不動。
- **(v0151)** **已發行的同名檔不換內容**:改 RoundAll 時套件 zip 的 README 也提到它 → 套件雜湊會變;已發行的套件 / 一鍵 / 操作員 / 本地實測要逐位元比對不變,只出新版號的那支。
- **(v0151)** **「結案」看收尾頁的負責方,不看燈號數**:BLOCKED / REVIEW / DATA_GAP 都不是成功;認不出來的列一律算 VRN-2(寧可未結案)。新增步驟名時,收尾頁的 `owner_of` 規則要一起看。
- **(v0151)** **一個讀法說「沒有」之前,換另一個讀法找**(v0112 價格標籤 · v0113 科目);放寬一定配造假變造(改名科目 / 對調價格)確認還抓得到。
- **(v0151)** **分支的 PR 被合進 main 後**:先快轉到 main 再做;main 裡的檔(例 `VRN2_LocalRound_v0100.md`)不再改,出新版(v0101)。

- **(v0150)** **驗證器說 FAIL 先看證據再改**:冊值 = 原文那行 → 是驗證器的讀法問題(換讀法 · 只放寬到同一列的標籤),不是去改擷取;放寬後一定跑對調變造(目標價 ↔ 現價)確認還抓得到。
- **(v0150)** **品質閘的「沒有資料」和「抓失敗」要分開**:鉅亨 404 頁面不存在 = 沒有覆蓋,不納入閘再跑;其他不過照 FAIL_CLOSED。引擎檔不改。
- **(v0150)** **收據的文字是給程式讀的**:「Python 本行程」讓下游誤判又重抓 35 分鐘;明細要寫出路徑與判斷依據(合 VDF 界線),下游看結構欄位(runner / fetch_python)不看字串。
- **(v0150)** **證據比對用數字相等,不用字串包含**(730 ⊂ 2730-2869),並跳過 Email / 電話行。
- **(v0150)** **VIA 網路工具 DENY 一律不繞**:要的資料被拒就說清楚是誰拒、交給誰決定(VCGC)。

- **(v0149)** **第二讀取器的比對形式要涵蓋各家 PDF 函式庫的寫法**:PDFium 把行尾連字號寫成 U+FFFE(舊版 U+0002)並吃掉換行;pdfplumber 留「-」+ 換行。只改比對形式,不改冊裡的摘錄。
- **(v0149)** **借來的工具會自己挑 Python 時,要換掉它挑的那一步**(MarketFetch 的 fetch_python 不看 VIA_FETCH_PY);挑的標準用**被呼叫的引擎自己的檢查**(VDF 的 DEPENDENCY_REQUIREMENTS 界線),不要只看能不能 import。
- **(v0149)** **不要讓別的系統的引擎在我們這輪自己 pip**:都不合界線就不啟動它,印每個候選缺什麼 + 交 VCGC 的指令(界線加引號:cmd 的 `<` 是導向)。
- **(v0149)** **Python 原始碼裡的 Windows 路徑一律成對反斜線**(docstring 也是);建置後用 `-W error` 編譯一次。
- **(v0149)** **使用者說 PowerShell 版本就給那一版的指令**:PS 7 = `pwsh`,5.1 = `powershell`;同一段 -EncodedCommand 兩邊都能跑。
- **(v0149)** **看不到桌機的值就讓下一輪印出來**:⑪ FAIL 印冊值 + 原文那一行,比猜擷取 / 驗證哪邊錯可靠。

- **(v0148)** **自測只能在乾淨的環境變數下判**:任何模組的 --selftest 都要先拿掉 VIA_ROOT / VRN2_ROOT / VRN2_OUTPUT_DIR / VRN2_INTEGRATE_* 等會改行為的變數再跑、結束還原;桌機的殼有 VIA_ROOT。
- **(v0148)** **Yahoo 代號的上市 / 上櫃只信 VDF 身分表(市場冊 yfinance_ticker)**,不信鉅亨 symbol 的前綴(上櫃也回 TWS)。
- **(v0148)** **擷取 Python 不用退役環境**:名字有 retired / backup / bak / old / deprecated / archive 的 envs 夾一律略過;via_tw_fetch 是 VDF 自己建的環境。
- **(v0148)** **檢驗不過先看是不是科目對錯列**:其他 / 部門 / 應付 / 負債 / 少數 / 調整後 / 核心 這些列不是那個科目;同年同科目多個值(預估調整表)取報告裡重複出現的;差到不像同口徑標 UNCLEAR 不算不過。
- **(v0148)** **建置腳本不要對整份 md 做版號取代**:歷史段落會被一起改掉(v0108 md 就這樣);只換程式碼區塊與指定的行。
- **(v0148)** 給使用者的指令要分 cmd / PowerShell(`%USERPROFILE%` vs `$env:USERPROFILE`),或直接給完整路徑。

- **(v0147)** **一支入口 = VRN2_RoundAll**:取套件 / 診斷 / 自測 / 跑 / 修 / 除錯 / 打包都在它;下一輪改套件版號時同步改它的常數(PACKAGE · RELEASE_REL · LAUNCHER · RECEIPT · SELFTESTS)並出 v0101,套件雜湊由建置填(build147 的 `PACKAGE_SHA256` 取代)。
- **(v0147)** **自動修只做可重跑、不刪資料的**:重跑一步 · 重組冊 · 補庫 · 重渲染 · 清過期鎖;收尾收據先備份 `.before_roundall.json` 才標註。要看原 PDF 的(四點 FAIL · 缺項 · 非冪等)只列不改。
- **(v0147)** **自測必須不受殼的環境變數影響**:會改行為的變數(輸出夾 · 上限 · 步驟開關 · fixture)在自測開頭清掉、結束還原;RoundAll 的 ③ 用使用者真實的殼跑自測,就是為了抓這種事。
- **(v0147)** **自測要在真套件夾測**:不能只在建置夾(旁邊有 new/)測;把套件 zip 解到隔離夾再跑一次。
- **(v0147)** **增量庫以「冊 × 原檔」判缺**,不是只看原檔新舊;新加的冊會自動把已知原檔補進來一次。
- **(v0147)** 掃使用者的夾一律限深 + 項目上限,不用 rglob;只問像 VRN-2 冊的檔。
- **(v0147)** **刪除區只收「確定是同一個數、量級相同卻對不上」的列**:單位不同 / 成長率 / 看不出來的一律不刪,只標「不明」留給人看;改這段規則先看刪除區列數有沒有暴增。

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
