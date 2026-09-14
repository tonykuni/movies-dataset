# -*- coding: utf-8 -*-
r"""
VIA_VRN_FirstPageEngine  v0113
ALL-IN-ONE engine consolidating the VRN first-page extraction & cross-validation logic.

Modules (single file, one entry point `FirstPageEngine.run`):
  1 SSOT loader          - load _RAW_REGEX/_RAW_SYNONYMS from SSOT .py, else locked fallback
  2 TickerFilename       - tokenize, 4-digit ticker / 6-8 digit date, disambiguation ladder,
                           year-band reclaim, tri-code cross-check, email->analyst/broker
  3 Layout               - font-hierarchy (MAIN_TITLE..FOOTER), element_type, boilerplate,
                           company-name (largest+bold), sentence linking (break at period)
  4 TableGeometry        - reconstruct hidden-gridline tables via x/y clustering, period headers
  5 NLPRepair            - real via_nlp bridge (v1.8.0 TextProcessor) + heuristic fallback
  6 FinancialValidation  - Add/Sub tolerance layering, Division two-stage, Historical YoY
  7 PriceAdjustment      - adjusted-price consistency + TP sanity gate
  8 CrossValidation      - filename <-> text <-> table <-> financials
Governance: append-only; raw + repaired coexist; TABLE/FIGURE never enter NLP.

====================================================================
v0101 → v0102(批426):九項升級,每一項都由本會期的實跑證據帶出來
====================================================================
【崩潰修】
 A. FinancialValidation.multiply / add_sub 遇 None 會 TypeError 當場崩——
    而 None 正是抽取器找不到數字時的**常態回傳**。實測:
      multiply(None,10,5)  → TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'
      add_sub(None,[1,2])  → TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'
    → 全面 None-safe,無值一律 N/A(不猜、不當 0)。

【死掛鉤修】
 B. NLPRepair 的外接掛鉤呼叫 self.ext.repaired(raw),但 via_nlp 的 TextProcessor
    **沒有 repaired() 這個方法**(它叫 repair(),且回 dict 不回 str)。
    後果:掛鉤永遠 AttributeError → 靜默退回啟發式後備,外接引擎等於沒接。
    這是「捕捉到卻不顯示」的變體:失敗被 except 吃掉,對外看不出來。
    → 改用真實 API(repair/normalize/split_sentences),並新增 route() 讓呼叫端
      看得見這一次走的是 HUB / DIRECT / HEURISTIC 哪一條。
 C. 新增 SUP_MDL744_NLPApplicationHub 自動掛載(尾版律,現為 v1.8.0/39 模組),
    不必由呼叫端自己 import。橋缺席=誠實退後備並留因由。

【檔名拆解】(操作員批420 規格)
 D. 民國年七碼日期:1141202 → 2025-12-02(v0101 回 None;操作員真檔名正在用)。
 E. 名字-KY 也是公司名稱:慧洋-KY 不再被切成「慧洋」+「KY」。

【抽取覆蓋】
 F. 目標價 regex 加寬到 Target price / Price Target / PT / 目標價(v0101 只認
    NT$ 與 目標價,GS/MS 的 "Price Target 650"、"PT 78" 全部漏抽)。

【判定誠實】
 G. report_kind 分類(個股/產業/大盤晨報/海外/研討會)+ kind_expects_ticker():
    非個股報告本來就沒有代號與目標價,不得因此被判失敗(批418 的 DONE_NS 律)。
 H. TP 合理性閘(TP/價 落在 0.2–5.0 之外=TP_SUSPECT),且 upside 只接受
    **已復權**價:拿原始 close 算復權升幅一律拒算(批425:引擎誠實拒絕頂替是對的)。
 I. 總判 aggregate_verdict() 必須讀到**所有**子閘(含 TP 合理性)——
    批422 的假綠就是上游閘抓到了、下游判定不讀它。

【其他】
 J. CLI 真的接線(--file/--dir/--ssot/--json/--selftest),且自測用攔真實呼叫證明
    旗標有傳到;批425 一連四例都是「參數在、線沒接」。
 K. TableGeometry 最近群聚查找由 O(n·m) min() 改 bisect(大頁面明顯有感)。
 L. 移除死碼(v0101 line 168 的 core lambda 定義後從未使用)。
 M. --selftest 零觸碰任何正本(批424:自測寫正本冊,十餘跑就把 66 筆灌成 78 筆)。

====================================================================
v0102 → v0103(批427):兩項——報告型別次序修 + 代號↔證券名稱對帳
====================================================================
【N. 型別分類:次序錯 + 詞冊缺】(操作員令「AI-PCB AI-CCL」)
  實跑證據:GS-AI PCB CCL 20251204.pdf → v0102 判「未分類」。
  拆開來看是**兩個**病,不是一個:
   N1 詞冊缺:_SECTOR_KW 只有「產業/類股/族群/策略/展望/sector/industry」,
      沒有任何科技主題詞——PCB/CCL/ABF/CoWoS/HBM/TPU/GPU/供應鏈/半導體…全不認得。
   N2 次序錯:classify_kind 先掃型別詞、**後**才看有沒有代號。只補 N1 的話,
      「台新AI伺服器-2317鴻海」會因為含「伺服器」被判成產業報告——把個股判成產業,
      比原本的未分類更糟。這是補洞補出新洞的典型,兩個一起修才算修。
  → 重排階梯:① 強非個股標記(晨報/晨會/盤勢/研討會/論壇,縱使檔名帶代號也不是
    個股報告——晨會本來就列一串代號)② 有四碼代號=個股(產業詞不得越過代號)
    ③ 無代號→海外 ④ 無代號→產業/主題詞冊(中文 in;英文走詞界 regex,
    否則 "review" 會被 "ev" 命中)⑤ 無代號→有界啟發:≥2 個全大寫科技縮寫
    (扣掉券商/市場/評等停用詞 GS/MS/TT/TW/KY/FY/EPS/BUY…)⑥ 未分類。
  次序改動一併把「法說」從強標記降為弱標記:2330 法說會報告**是**個股報告,
  v0102 會把它判成研討會。這是本次重排順手治好的第二個誤判。

【O. 代號 → 證券名稱 對帳】(操作員令:「台新 BROKER 2317 TICKER 鴻海 股票名稱,
  可透過 TICKER 去 TWSE/TPEX 找證券名稱抓回來對照,也可以 VDF 系統建立的
  股票清單每日更新去對帳」)
  → TickerFilename.name_hint():取檔名裡**與代號相鄰**的公司名(先 X-KY 整體,
    再代號之後,再代號之前;濾掉券商與「報告/個股/研究/投顧/評等…」通用詞)。
    台新AI伺服器-2317鴻海 → 台新=券商、2317=代號、鴻海=名稱,三者各歸各位。
  → NameReconciler:四階梯,離線優先——
      ① SSOT 同義詞冊(_RAW_SYNONYMS,本檔已載)
      ② VDF 正典庫 tw_universe / tw_listings(ENG081 每日更新;唯讀開庫,
         庫不在/被鎖/無 duckdb=誠實 SKIP,絕不建庫)
      ③ VRN_MDL010_CodeRegistry 預設冊
      ④ TWSE/TPEX 線上 OpenAPI —— **只在操作員自己開妥雙閘後才走**;
         閘未開=SKIP_NO_CONSENT,本引擎絕不代設 VIA_NET_CONSENT(治理鐵律),
         且走的是正典 SUP_MDL740 http_json,不自建抓取(零九頭龍)。
    比對容差:NFKC → 去 -KY/*/股份有限公司/控股 → 任一方含另一方即 MATCH
    (台積電 ⊂ 台灣積體電路)。查不到官方名=UNKNOWN,**不是** PASS。
  → 總判新增 name_match 閘:MATCH=PASS、MISMATCH=FAIL、查不到/無名稱提示=N/A。
    誠實三態:來源不可得時給 N/A 而不是綠——批422 的假綠正是「不可得當成沒問題」。
  【誠實聲明】階梯 ④ 的線上實跑在本沙箱**未驗證**:沙箱零同意閘,依治理律不代設。
    ①②③ 皆已實跑。④ 第一次真跑會在工作站、由操作員自己開閘之後。

====================================================================
v0103 → v0104(批427b):--dir 三病合一,而且路徑是我給錯的
====================================================================
【P. 工作站實錄:`--dir "VIA_Reports\\incoming"` → `[絕] 無可處理檔`】
  操作員照我上一則的一貼即跑打了指令,得到一句沒有資訊量的拒絕。查下去是三個病:

   P1 **路徑是我給錯的**。正典收件夾不是 VIA_Reports/incoming,是
      functional modules/VRN/input/incoming(∪ input_reports)——冊在
      supportive modules/registry/VIA_InputConsole_Spec_v0100.json
      families.vrn.input,MDL141/MDL139 全走這條。我憑印象寫路徑,沒查冊。
      這是本會期第三次同型錯誤(批425 猜站名、批426 猜斷言值、這次猜路徑),
      都是「我以為我記得」——記得不算證據,grep 才算。

   P2 **三種原因壓成一句話**。夾不存在 / 夾在但空 / 夾在有檔但沒有 .pdf,
      三者對操作員的下一步完全不同(換路徑 / 放檔 / 改副檔名),
      v0103 一律回「[絕] 無可處理檔」。這正是我這幾批一直在修的病
      (批422 假綠、批425 靜默退後備)出現在我自己的碼裡:
      **把不同的失敗壓成同一個訊息,等於把診斷資訊丟掉**。

   P3 **副檔名只認小寫 .pdf**。glob("*.pdf") 漏掉 .PDF;而冊上 extensions
      明明寫 [".pdf", ".docx"],v0103 連 .docx 看都不看。

  → v0104:
    · 綁正典冊(load_input_spec)取 dir_default / incoming / extensions,
      不自寫第二份路徑(零九頭龍);冊缺=誠實退內建預設並印明。
    · 報告夾律照 MDL141 批399/400:--dir > user.vrn_dir > 冊 dir_default,
      **incoming 一律併入**;不給 --dir 也能跑(預設就走正典兩夾)。
    · 副檔名比對走 suffix.lower(),.PDF/.Pdf 一律收;.docx 收進來但
      **誠實標明只做檔名層**(本引擎只讀 PDF 文字層,不假裝讀了 Word)。
    · 找不到檔時**分三種原因講**,並列出夾內實際有哪些副檔名、各幾個,
      以及正典收件夾的絕對路徑——讓操作員一眼知道下一步該做什麼。

【Q. 補 P 的時候當場撞出來的假紅】
  修完 P 拿混合夾實跑,台新AI伺服器-2317鴻海.docx 檔名層全對
  (台新=券商、2317=代號、鴻海=名稱、對帳 MATCH),卻被判 **FAIL**——
  因為 target_price 抽不到。但 .docx 本來就沒有 PDF 文字層,
  **讀不到 ≠ 抽錯**。這是假紅,和批422 的假綠是同一枚硬幣的兩面:
  證據不可得的時候,燈要給 N/A,不是給顏色。
  → run() 產出 text_state;aggregate_verdict 在無文字層時把文字類的閘
    (target_price / tp_sanity / zone_presence / filename_vs_page / historical)
    一律降成 N/A_NO_TEXT,而**檔名類的閘照常判**——代號、券商、名稱對帳
    正是 .docx 仍然有用的部分,名稱對不上照樣要紅。

====================================================================
v0104 → v0105(批428):純文字車道 + 四分頁矩陣報告
====================================================================
操作員令:「先拿裡面的報告實測,跳出四頁式,字小一點比較專業,矩陣報告:
  1. detailed summary matrix and error matrix  2. basic info  3. financial data」

【R. 純文字車道】操作員的 incoming 是空的,但**庫裡有 64 份真報告的全文**
  (functional modules/VRN/references/intake/AttachmentFixedOutput_*/01_repair/documents/*.pdf.txt,
  批245 收容的真語料)。v0104 只吃 PDF 字元幾何,這批語料一份都用不上。
  → run(filename, text=...) 純文字車道;text_state 由二態擴為三態:
      OK        有字元幾何(PDF)——版面/分區/字級階層全可判
      TEXT_ONLY 只有純文字——TP/評等/券商/電話/分句照抽,**版面幾何類的不判**
      NO_TEXT   兩者皆無(.docx/掃描檔)——文字類的閘一律 N/A(批427b-Q)
  三態不可合併成二態:TEXT_ONLY 能抽到的東西遠多於 NO_TEXT,
  把它併進 NO_TEXT 就是把 64 份真語料的證據丟掉。

【S. 四分頁矩陣報告】--report <out.html> 產出四分頁(純 CSS 分頁,零 JS 框架、零 CDN):
   ① DETAILED SUMMARY MATRIX  逐報告 × 全欄位 + 每一個閘的燈(引擎實跑)
   ② ERROR MATRIX             只放紅黃:引擎閘 FAIL/WARN 逐筆列因由
                              + 庫 vrn_report_crosscheck 非 OK 列(first_page vs table 比值)
   ③ BASIC INFO               庫 vrn_report_basic(代號/官方名/券商/日期/評等/TP/價/upside 三態)
   ④ FINANCIAL DATA           庫 vrn_report_financial + vrn_report_metrics(逐科目 × 期間 × 狀態)
  字級沿用 ENG072 既有房規(10.5px 基底)再收一級:表格 9px、頁首 13px——
  操作員要的「小一點比較專業」是這個尺度,不是另立一套視覺。
  庫缺席/無 duckdb = 該分頁誠實印「庫不可得」並說明為何,**不留白讓人以為沒資料**。

【T. 拿操作員 64 份真檔名實測,54 對 10 錯——五類全修】
  操作員把 64 份真報告放進正典收件夾並貼出檔名。**先不寫碼,先全跑一遍**:
   T1 `2026` 被當成四碼代號(3 筆:第一場/第二場/第三場 全判成個股 2026)。
      但**不能用「排除 2000–2030」修**——那會誤殺一整排真代號:
      2002 中鋼、2015 豐興、2023 燁輝、2027 大成鋼、2030 彰源…整個鋼鐵類股都在裡面。
      正解是**拿庫對帳**:四碼在 tw_listings_industry(1978 檔)冊上才算代號,
      不在冊上且落在 1990–2100 就是年份。這正是操作員原令「用 VDF 股票清單對帳」。
      庫不可得=沿用舊行為但在 kind_reason 標明「未經庫對帳」,不假裝驗過。
   T2 晨報家族漏字:投資早報 / 統一投顧-投資早報 / 凱基期貨晨間解盤 三筆判未分類
      (冊上只有 晨報/晨會/盤勢/盤前/盤後,沒有 早報/晨間/解盤)。
      另補「第N場」為強標記→研討會(第一/二/三場 是法說會場次)。
   T3 主題詞漏:MS-Automation / MS-Thermal Solutions ×2 / UBS-Asia Hardware Insights
      四筆判未分類(缺 automation/thermal/hardware)。
   T4 **兩筆假紅**(最嚴重,比未分類糟):
      · 凱基投顧_2891 中信金_施志鴻 → 名稱提示取到「施志鴻」(分析師)→ MISMATCH。
        根因:「中信金」含券商別名「中信」,被 broker_of_token 當成券商濾掉了。
        修法:券商判定改嚴——token 去掉機構後綴(證券/投顧/投信/期貨/證期/研究部)後
        **等於**別名才算券商;單純「含有」不算。中信金≠中信,是股票名。
      · 晶心科(6533,N,中立)-CTBC → 名稱提示取到「中立」(評等)→ MISMATCH。
        修法:name_hint 一併濾掉評等詞;濾掉之後 after 窗落空,
        自然退到 before 窗取到真名「晶心科」。
   T5 券商冊漏:國泰(【國泰證期研究部】)、CLST、GF、JP(冊有 jpm 沒有 jp)。
      同時把 ASCII 別名改走**詞界**比對——"jp" 用 in 掃會命中 "jpy",
      這是 N1 主題詞冊踩過的同一個坑,不能在券商冊再踩一次。

【誠實邊界】② 的庫側錯誤列來自先前 ENG073/ENG074 的入庫成果(沙箱 n=30);
  ①② 的引擎側每一格都是本次實跑當場算出來的。兩者來源不同,頁上分開標明,
  不混成一鍋讓人以為都是新鮮的。

====================================================================
v0105 → v0106(批429):工作站真 PDF 實跑,錯得有系統——四病一根
====================================================================
操作員拿 64 份**真 PDF**(不是文字語料)跑 v0105,貼回全表。錯得有系統:

【W1 TP 抽到的是代號本身】
  泓德能源(6873) → TP=6873 · 神達(3706) → TP=3706 · 望隼(4771) → TP=4771
  根因:extract_target_price 取**第一個**命中就回,不排序不過濾。
  「公司名(代號)」裡的四碼就在觸發詞附近,於是代號被當成目標價。
  → 改候選評分:收全部候選 → 過濾(代號回音/日期回音/年份/括號內緊接中文名)
    → 排序(帶貨幣符號 > 觸發詞命中 > 距觸發詞近 > 有小數)。

【W2 TP 量級離譜卻沒人擋】
  奇鋐 TP=1780 · 中信金 TP=1.0 · 健策 TP=2.0 · MS-Thermal TP=14503/17382。
  TP 合理性閘(0.2–5.0)要**現價**才能判,而現價來自庫——庫不在,閘就睡著了。
  → 加一道不需要現價的幣別合理帶:台股目標價落在 1–5000 元之外=TP_RANGE_SUSPECT。
    這是**幣別合理性**不是精準驗證,所以給黃燈並標明,不是紅也不是靜音。

【W3 非個股報告從內文亂撈代號】
  晨會報告 代號=1163/4441 · MS-Thermal 代號=3017 · UBS-Asia 代號=8722。
  產業報告提到 3017 奇鋐,**不會使它變成一份 3017 的報告**。
  → 非個股型別:內文代號一律移到 mentioned(內文提及),ticker 留空。

【W4 一個缺件同時廢掉三個能力】←這是根
  操作員的 OneDrive 副本沒有 vdf_tw_market.duckdb。庫一不在:
    · 代號冊空 → is_valid_bare 無冊可對 → 內文四碼全收(W3 更嚴重)
    · 名稱對帳全 UNKNOWN(64 份裡只有 4 份靠 MDL010 僥倖命中)
    · TP 合理性閘拿不到現價 → 睡著(W2 無人擋)
  → 新增**離線代號冊** VRN_TWRoster_Offline_v0100.json(1978 檔,由庫快照而來,
    帶 asof 與來源)。這不是第二份實作,是同一份事實的副本;庫在時仍以庫為準。
    階梯:庫 → 離線冊 → MDL010。冊過期與否看得見,不是黑箱。

【X. 版面(操作員令「自小一點 · 矩陣格式自動最佳化 · 堆疊矩陣 · 擷取結果驗證」)】
  · 字級再收一級:基底 10.5→9.5px、表格 9→8.5px、頁首 13→12px
  · 欄寬自動最佳化:掃該欄實際內容長度定寬,短欄不再被平均分掉
  · 堆疊矩陣:同一報告的多列證據(欄位/來源/值/燈/因由)堆在一起看,
    橫表看不出「同一份報告的證據彼此矛盾」,堆疊才看得出來
  · 新增第⑤頁「擷取結果驗證」:逐欄位 × 抽到什麼 × 哪裡抽的 × 為何信/不信

====================================================================
v0106 → v0107(批430):百分比不是價格 + 開頁旗標 + 另庫勘查
====================================================================
【Y1 TP 抽到的是百分比/倍數】工作站 v0106 實跑:
  志強-KY TP=23.0——報告寫的是「潛在上漲空間**23%**」;
  泓德能源 22.7、神達 41.9 同型(上漲空間/報酬率)。
  根因:_TP 的 [^\d\-]{0,20} 會**跨過**「潛在上漲空間」這種詞去撈後面的數字。
  → 三道新剔除:數字後接 %/％/ppts(百分比)、後接 x/倍/PER(本益比倍數)、
    觸發詞與數字之間夾著「上漲空間/報酬率/殖利率/漲幅」(講幅度不是價格)。
  修後:泓德能源 208 · 神達 128 · 志強-KY 145——與報告原文一致。

【Y2 沒有自動跳出報告】操作員:「沒有自動跳出 html u/i matrix report」。
  治理律是**零彈窗**(批340:引擎不得自作主張開視窗),所以 v0106 產完只印路徑。
  → 加 --open:操作員明打就是他要開,那不是自作主張。
    若他殼裡 VIA_NO_OPEN=1(短指令梭一律設)照樣不開——那是他自己的閘,不代解;
    但要把「為何沒開、怎麼改」講清楚,不是靜靜不動作讓人以為壞了。

【Y3 另一庫勘查(操作員令:看 tonykuni/VIA-VDF-VRN,需要就複製來用)】
  掛進來跑了他們的 test:vrn —— **36/36 全綠**。但操作員說「他也還沒成功」。
  看了 src/lib/via/nlp-extract.ts:109:
      grab("K1", /(?:目標價|潛在上漲|評價方式)[:：]\s*(.+)/);
  **把「目標價」和「潛在上漲」當成同一個欄位**——正是本批 Y1 修掉的那個病;
  而且要求觸發詞後緊接冒號,真報告多半寫「目標價145」沒有冒號,直接抽不到。
  所以那 36/36 是跑在有冒號的 fixture 上,不是跑在操作員的 64 份真報告上。
  **結論:沒有可複製進來的東西,本引擎的抽取層比它前面。** 誠實回報,不硬抄。

====================================================================
v0107 → v0108(批431):文內自洽交叉核對(不靠庫、不靠網)
====================================================================
【Z 先講我**不做**什麼,以及為什麼】
  殘留問題是 TP 量級可疑(奇鋐 1780 · 中信金 1.0 · MS-3661 4388 · 貿聯 2600),
  要判準需要現價。我試過兩條路,兩條都**誠實走不通**,所以都不做:
   ① 離線收盤快照:從庫導出 865 檔成功,但 3017/2891/3661/3665/2330/6768
      **一檔都不在裡面**——庫裡那張 tw_trading_daily 是局部測試資料(4 天、889 檔)。
      出一個對所有相關個股都查不到的檔案是**假能力**:看起來有用,閘照樣睡著。
      已產出、已驗證、已刪除。不出。
   ② 文內現價:64 份語料裡只有 1 份疑似帶現價,而那個「股價10」其實是
      「評價位於股價10-11x」的本益比。也走不通。
  → 能做的是第三條:**文內自洽**。報告若同時寫了目標價與上漲空間,
    兩者互相隱含一個現價:隱含現價 = TP ÷ (1 + 上漲空間%)。
    志強-KY:145 ÷ 1.23 = 117.9,而報告原文的收盤價是 118.00——對得上。
    【我寫這段時預測它會抓到 GS-2383(6000 ÷ 1.32 = 4545),實跑打臉:
      4545 落在合理帶 1–5000 之內,判 PASS。而且 4545 在台股並非不可能
      (大立光曾站上 6000)。**這個檢查證明的是「文內一致」,不是「外部正確」**——
      目標價與上漲空間若是**一起**被抽錯,它們仍然自洽。
      它能抓的是**粗錯**:TP=1.0 配上漲空間 20% ⇒ 隱含現價 0.83,低於合理帶。
      不誇大它的能力;預測錯了就改寫,不改斷言去遷就預測。】
    覆蓋率誠實講:64 份裡只有 7 份同時有這兩個數(11%)。有就查,沒有就不立閘。

====================================================================
v0108 → v0109(批432):雙方檔案互取除錯法
====================================================================
操作員令「雙方檔案中找除錯的方法」。兩邊各有對方缺的東西:

【他們有、我沒有】via-vdf-vrn 的 src/lib/via/fin-audit.ts 開宗明義:
  「一列必須是原子事實。**P 級不得掛綠**」——每個欄位帶證據等級 V/M/P,
  證據弱的不准掛綠燈。我這邊 TP 只有「有值/沒值」,沒人問它**證據多強**,
  於是 中信金 TP=1.0、Daiwa-3653 TP=2.0 這種孤證照樣掛 PASS。
  → 移植 AA2 證據分級。

【我有、他們沒有】逐候選 trace(⑥擷取驗證頁)與 64 份真報告語料。
  → 補 AA3 --trace:把候選表印到主控台讓操作員貼回來。
    **我看不到他的 PDF,就修不了我看不見的東西**;給他一個能把現場拍給我看的工具,
    比我在這邊猜十次有用。

【AA1 工作站每跑必噴的警告】
  SyntaxWarning: invalid escape sequence '\d' ——本檔模組 docstring 裡引用了
  正則 [^\d\-]{0,20} 與 [:：]\s*,而 docstring 不是 raw string。
  把模組 docstring 改成 raw 字串即解(在說明裡寫三引號會把 docstring 自己終止——
  我剛剛就這樣把檔案寫壞了一次)。不是大病,但**每跑必噴的警告會訓練人忽略警告**,
  那才是大病。

【AA4 神達新回歸(誠實記錄)】
  工作站 v0108 實跑:神達 TP 從 v0107 的 128 變成 **119715**,
  而 tp_self_consistency **FAIL 抓到了**(119715÷1.419=84,365 荒謬)。
  我看不到他的 PDF 文字層,無從得知 119715 從哪來——這正是 AA3 要解的。
  在拿到 trace 之前**不猜、不硬改**;閘已經把它擋在綠燈外,這是誠實的中間狀態。

====================================================================
v0109 → v0110(批433):trace 把答案送回來了
====================================================================
【AB1 神達 119715 —— 排序權重又錯一層】
  操作員跑 --trace 神達,候選表直接給出答案:
        41.9  觸發詞 Y Y 225.0  剔(上漲空間)
     119,715  觸發詞 Y - 220.0  留 ← 被採用
        3706  觸發詞 - - 200.0  剔(代號回音)
          78  觸發詞 - - 200.0  留 ← **這才是真正的目標價**
  78 ÷ 1.419 = 54.97,神達當時就在 55 上下,完全合理。
  119,715 輸在哪?**它多了一個貨幣記號(+20 分)就贏了 78。**
  根因:我把「帶貨幣記號」排在「落在合理股價帶」之上。但
  **六位數帶千分位的數字不是股價**——那是營收/市值,而且這個訊號
  比有沒有一個「元」字強得多。批429 我修過一次排序權重(來源 > 貨幣),
  這是同一課的第二層:**合理性 > 貨幣記號**。
  → 合理帶進評分:在帶內 +40、在帶外 −60。
    119,715 → 220−60 = 160;78 → 200+40 = 240。78 勝。

【AB2 台股目標價的下界不是 1 元】
  中信金 TP=1.0(實際約 45)、Daiwa-3653 TP=2.0(健策數百)——兩者都落在
  舊帶 [1, 5000] 之內,所以連黃燈都沒有。券商報告給出低於 5 元的目標價
  極其罕見(全額交割股才那個價位,而那種股票不會有目標價報告)。
  → 合理帶下界 1 → 5。**這是提醒不是判死**:低於 5 元的目標價確實存在,
    所以給黃燈要人看一眼,不是剔除。

【誠實邊界】AB1 是**真修好了**(有 trace 為證,78 是可驗證的正解);
  AB2 只是**把可疑的標出來**——我仍然沒有現價,判不了 1780/4388/2600 誰對誰錯。

====================================================================
v0110 → v0111(批434):黃燈太多,其中一半是我自己造的
====================================================================
操作員問「可以修到全部成功嗎」。誠實盤點:64 份裡 49 個非綠燈格,
**約 28 個是我自己過度標記**,那些我修;剩下的是真的,不硬壓成綠。

【AC1 我把他們的律套過頭了】
  via-vdf-vrn 的 fin-audit.ts 寫的是「**P 級**不得掛綠」——**只講 P**。
  我批432 移植時讓 M 級也掛黃(18 格裡 16 格是 M),於是
  MS-2308 TP=1288、JP-2330 TP=1275 這種乾乾淨淨的抽取,
  只因為數字旁邊沒有「元」字就被拉成黃燈。
  而**英文報告本來就不會寫「元」**——用貨幣記號當必要條件是中文報告偏見。
  → M 級 tp_evidence 回 PASS(等級仍原樣寫進 tp_grade 與矩陣,資訊不消失);
    只有 P 級才 WARN 並連帶降 target_price。照他們寫的那句話辦,不加碼。

【AC2 非個股沒有資訊區】
  zone_presence 檢查的是「目標價/評等/券商」三件套有沒有出現在本文分句裡。
  晨報/海外/研討會**本來就沒有這三件套**,拿它來判等於問一份晨報
  「你的目標價段落呢」。12 格 WARN 幾乎全是這樣來的。
  → 非個股 zone_presence 一律 N/A_NON_STOCK,與 target_price 同律(批418/426-G)。

【AC3 更正我自己說錯的話】
  我上一則說「奇鋐 TP=1780 可疑」。操作員跑 --trace 奇鋐,候選表顯示
  報告裡**只有 1,780 這一個數字**(寫了兩次、帶貨幣記號、等級 V),
  而奇鋐 2025 年本來就在千元以上。**1780 是對的,是我的懷疑沒有根據。**
  trace 不只用來抓錯,也用來洗刷冤枉——這次它洗掉的是我自己造的懷疑。

====================================================================
v0111 → v0112(批435):多工具核對的本文——但那東西早就造好了
====================================================================
操作員令:「另外一邊有最新的 NLP 引擎 / LAYOUT 引擎,將第一頁真正的內容
相關本文及表格(不含底部小字體頁尾),同一個 LAYOUT 識別及修正工具及 NLP
讀取後本文是否相同,多工具核對,至少兩種解取工具還原文字及表格後是一致的,
先看驗證後的本文」。

【先查再造:VRN_ENG072 v0107 已經有了】
  法A = fitz 分區(標題帶/左本文/右資訊區/頁尾帶,底 8% 當雜訊)
  法B = pdfplumber words 同判準分區 + extract_tables 表格還原
  法C = GenericLayoutEngine v2.1.0(九宮分區 + 字重階層 + 本文字級推定)
  句級 = NLP OneEngine TextProcessor(帶 ssot_lexicon)修復後再 split_sentences
  compare_zones 逐區 difflib:**≥0.90 AGREE / ≥0.60 PARTIAL / 低 DIVERGE**
  產物 = VIA_Reports/first_page_text/<檔名>.json,鍵有
        body(法A)· plumber.body(法B)· gle(法C)· sentences · tables · compare · footer

【那我這支引擎在幹嘛?——它自己又判了一次版面】
  本引擎從 v0101 起就用自己的 _pdf_chars + Layout 判版面,**完全沒去讀 sidecar**。
  於是同一份 PDF 被判兩次版面,而且下游用的是**沒有經過雙法核對**的那一份。
  這是我造出來的重複,也是操作員這次問題的真正答案:
  **不是「要做多工具核對」,是「已經做了,但我沒接」。**
  → 新增 SidecarBridge:有 sidecar 就用**驗證後的本文**(compare.body 達 AGREE),
    沒有就退回自判並誠實標明。新閘 text_consensus:
      AGREE=PASS · PARTIAL=WARN · DIVERGE=FAIL · 無 sidecar=N/A_NO_SIDECAR
    **DIVERGE 判 FAIL 不判黃**:兩個獨立工具對同一頁讀出不同的字,
    那不是「有點疑慮」,是下游拿到的字可能根本不是報告寫的。
  → --body <關鍵字> 印出驗證後的本文 + 表格 + 哪幾法一致(先看驗證後的本文)。

用法:
  python3 VIA_VRN_FirstPageEngine_v0114.py --selftest
  python3 VIA_VRN_FirstPageEngine_v0114.py --file <報告.pdf> [--ssot <SSOT.py>] [--json]
  python3 VIA_VRN_FirstPageEngine_v0114.py --dir <報告夾> [--json]
  python3 VIA_VRN_FirstPageEngine_v0114.py --dir <報告夾> --report --open  六分頁矩陣+開頁
  python3 VIA_VRN_FirstPageEngine_v0114.py --dir <報告夾> --trace 神達     印出候選表(貼回來給我看)
  python3 VIA_VRN_FirstPageEngine_v0114.py --dir <報告夾> --body 志強       印出**驗證後的本文**與表格
  python3 VIA_VRN_FirstPageEngine_v0114.py --dir <報告夾> --struct 志強     印出**文件結構**(階層/列化/表圖還原)

v0113→v0114(批437 文內自洽從「驗證」升格為「仲裁」):
  操作員給了三包(VIA_NLP_v1.6.1 / Discussion Reconstruction / NLP_Application_System_v1.8.0)。
  先查再造的結果:**三包裡沒有一支庫內沒有的引擎碼**——上傳的 v1.8.0 與
  庫內 references/intake/VIA_NLP_Application_System_v1.8.0 逐檔相同,v1.6.1 是
  它的舊版子集,Discussion 包是資料不是引擎。缺的從來不是碼,是**呼叫**。
  而且庫裡本來就躺著那 64 份報告的**第二份取字**
  (references/intake/AttachmentFixedOutput_v1.0.0_b245/.../01_repair/documents/*.txt),
  我卻一直在跟操作員要 --trace 貼回來。

  六修,每一條都有實據:
   A1 自洽仲裁:報告若自陳上漲空間,則「目標價 ÷ (1+空間)」必須等於同頁的現價。
      這條訊號比觸發詞、比貨幣記號都強——CLST-6669 4,200÷1.27=3,307≈同頁 3,300
      (文中明寫 potential +27%),中信金 63÷1.137=55.41≈同頁收盤價 55.40。
   A2 四條剔除律:「from A to B」的 A 是前次 · 「hi/lo」是 52 週高低不是目標價 ·
      「Target price: n.a.」是本報告沒有目標價 · 數字後接月份縮寫是日期。
   A3 文件結構層第二階層來源:接 SUP_MDL744 的 layout()/roles();沒 gle 不再整份當本文。
   A4 期間樣式的裸民國年 1[0-2]\d 會吃掉**目標價 125** → 只認「民國 1xx」與七碼日期。
   A5 有表頭無資料列 ⇒ 不是表(工作站印出「無表格訊號」卻同時印表頭,自相矛盾)。
   A6 --fixtures:庫內第二取字直接當來源,不必等操作員貼 trace。
  python3 VIA_VRN_FirstPageEngine_v0114.py --text-dir <語料夾> --report   純文字語料
  python3 VIA_VRN_FirstPageEngine_v0114.py --fixtures --trace 中信金         庫內第二取字(批437)
"""
import bisect
import datetime as _dt
import html
import json
import os
import subprocess
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ENGINE_NAME = "VIA_VRN_FirstPageEngine"
ENGINE_VERSION = "v0113"

# =====================================================================
# 1 · SSOT LOADER
# =====================================================================
_LOCK = {
    "TW_STOCK_CODE_4DIGIT": r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
    "TW_YFINANCE_TICKER":   r"([1-9]\d{3})\.(TW|TWO)",
    "TW_BLOOMBERG_TICKER":  r"([1-9]\d{3})\s+TT",
}


def load_ssot_blocks(ssot_path):
    blocks = {}
    if not (ssot_path and os.path.exists(ssot_path)):
        return blocks
    txt = open(ssot_path, encoding="utf-8", errors="replace").read()
    for var in ("_RAW_REGEX", "_RAW_LISTS", "_RAW_SYNONYMS"):
        m = re.search(var + r"\s*[:=][^=]*=?\s*json\.loads\(r'''(.*?)'''\)", txt, re.S)
        if m:
            try:
                blocks[var] = json.loads(m.group(1))
            except Exception:
                blocks[var] = []
    return blocks


# =====================================================================
# 1b · via_nlp 橋(批426-C):自動掛 SUP_MDL744_NLPApplicationHub 尾版
# ---------------------------------------------------------------------
# v0101 要呼叫端自己把 engine 傳進來,實務上沒人傳=外接引擎形同虛設。
# 這裡自己找橋:supportive modules/70_VRN_Rules/SUP_MDL744_*.py(尾版律 glob)。
# 橋缺席不是錯誤,是**誠實降級**——留因由,由 route() 對外交代。
# =====================================================================
def _find_via_root(start: Path) -> Path | None:
    p = start.resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return None


def mount_nlp_hub(explicit_dir=None):
    """回 (hub_module | None, why)。零網路;失敗只降級不拋。"""
    root = Path(explicit_dir) if explicit_dir else _find_via_root(Path(__file__).parent)
    if root is None:
        return None, "找不到 VIA 根(需同時有 supportive modules/ 與 functional modules/)"
    d = root / "supportive modules" / "70_VRN_Rules"
    hits = sorted(d.glob("SUP_MDL744_NLPApplicationHub_v*.py")) if d.is_dir() else []
    if not hits:
        return None, f"SUP_MDL744 缺檔({d})"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("via_nlp_hub_fpe", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod          # 延後註解要靠這行
        spec.loader.exec_module(mod)
        st = mod.mount()
        if st.get("state") in ("ABSENT", "FAILED"):
            return None, f"橋在位但掛載 {st.get('state')}:{st.get('why', '')}"
        return mod, ""
    except Exception as exc:
        return None, f"橋載入失敗 {type(exc).__name__}:{str(exc)[:90]}"


# =====================================================================
# 2 · TICKER / FILENAME
# =====================================================================
class TickerFilename:
    _PUN = ("　 \t\r\n．。,、;:()()【】〔〕「」『』《》〈〉[]{}<>"
            "·•‧//\\|—–-_~＿＝=＋+＊*＆&%%#＃@＠!!??＂\"＇'｀`^$＄.,;:!?\"'()[]{}<>")
    _SEP = re.compile("[" + re.escape(_PUN) + "]+")
    # ── 批426-G(承 批418):報告型別冊。非個股本來就沒有代號與目標價,
    #    不得因此被判失敗——這是操作員 63 份真報告裡 19 份的常態。
    # ── 批427-N:v0102 的次序是「先掃型別詞、後看代號」,詞冊一補就會把
    #    「台新AI伺服器-2317鴻海」判成產業報告。故拆成強/弱兩層:
    #    強標記=縱使檔名帶四碼代號也不是個股報告(晨會本來就列一串代號);
    #    弱標記=只在**沒有代號**時才作數。「法說」由強降弱:2330 法說會報告
    #    是個股報告,v0102 會把它判成研討會。
    _STRONG_NONSTOCK = (
        # 批428-T2:操作員 64 份真檔名實測補字——投資早報 / 統一投顧-投資早報 /
        # 凱基期貨晨間解盤 三筆原判未分類,冊上只有 晨報/晨會/盤勢/盤前/盤後。
        ("大盤晨報", ("晨報", "早報", "晨間", "晨訊", "解盤", "晨會", "盤勢", "盤前",
                      "盤後", "盤中", "收盤", "每日觀察", "盤中速報", "投資日報",
                      "morning", "daily wrap", "market wrap", "daily brief")),
        # 批428-T2:「第一場/第二場/第三場」是法說會場次,不是個股報告
        ("研討會",   ("研討會", "論壇", "峰會", "conference", "summit", "expert call",
                      "roadshow", "corporate day", "第一場", "第二場", "第三場",
                      "第四場", "第五場", "說明會")),
    )
    _WEAK_NONSTOCK = (
        ("海外",     ("海外", "美股", "陸股", "港股", "日股", "全球", "跨國",
                      "global", "offshore", "overseas")),
        ("研討會",   ("法說", "法人說明會", "earnings call")),
    )
    # 產業/主題詞冊(批427-N1)。中文用 in;英文另走詞界 regex,否則
    # "review" 會被 "ev" 命中、"preview" 會被 "ic" 命中——這類短縮寫用 in 掃必炸。
    _SECTOR_KW = (
        "產業", "類股", "族群", "策略", "展望", "供應鏈", "產業鏈", "價值鏈",
        "半導體", "晶圓", "晶圓代工", "先進封裝", "封測", "記憶體", "面板", "被動元件",
        "印刷電路板", "銅箔基板", "載板", "散熱", "伺服器", "資料中心", "光通訊",
        "網通", "電動車", "太陽能", "風電", "重電", "儲能", "電池", "機器人",
        "低軌衛星", "矽光子", "生技", "軍工", "航運", "鋼鐵", "水泥", "金融股",
        "資安", "車用", "手機", "消費性電子", "工具機", "紡織", "食品股", "觀光股",
        # 批428-T3:64 份實測補——自動化 / 散熱方案 / 硬體 三類原本判未分類
        "自動化", "機械", "硬體", "散熱模組", "水冷", "液冷", "銅箔", "玻纖",
    )
    _SECTOR_KW_EN = (
        "sector", "industry", "supply chain", "value chain", "semiconductor",
        "foundry", "packaging", "osat", "memory", "dram", "nand", "panel",
        "pcb", "ccl", "abf", "substrate", "cowos", "hbm", "tpu", "gpu", "asic",
        "mlcc", "euv", "cpo", "sic", "gan", "server", "data center", "datacenter",
        "networking", "optical", "solar", "battery", "robotics", "humanoid",
        "quantum", "satellite", "handset", "smartphone", "automotive", "shipping",
        # 批428-T3:MS-Automation / MS-Thermal Solutions ×2 / UBS-Asia Hardware Insights
        # 四筆原判未分類(停用詞扣掉 MS/UBS 之後縮寫只剩一個,啟發也不救)
        "automation", "thermal", "cooling", "hardware", "insights", "supply",
        "power", "connector", "fabless", "display", "sensor", "component",
    )
    # 有界啟發用的停用詞:券商/市場/評等/單位縮寫不算科技主題(批427-N)
    _ACRONYM_STOP = frozenset((
        "GS", "MS", "JPM", "UBS", "CS", "DB", "BOFA", "BAML", "CLSA", "HSBC",
        "CITI", "BNP", "MQ", "NOMURA", "SC", "CIMB", "KGI", "SINO", "IBTS",
        "TT", "TW", "TWO", "TWSE", "TPEX", "OTC", "KY", "ADR", "GDR",
        "FY", "CY", "YTD", "QOQ", "YOY", "MOM", "CAGR", "NTD", "NT", "USD",
        "TWD", "RMB", "JPY", "EPS", "PER", "PE", "PBR", "PB", "ROE", "ROA",
        "EV", "EBIT", "EBITDA", "DCF", "NAV", "PT", "TP", "OP", "GM", "OPM",
        "BUY", "HOLD", "SELL", "OW", "UW", "EW", "NR", "NA", "PDF", "REV",
    ))
    # 批426-E:名字-KY 也是公司名稱(慧洋-KY / 貿聯-KY / AMAX-KY)
    # 批428-T6:結尾用 (?![A-Za-z0-9]) 不用 \b——底線是 word char,
    # 「6933_AMAX-KY_個股介紹報告」的 KY 後面接 _,\b 不成立,整個 -KY 抓不到,
    # 名稱提示落空判 NO_HINT(官方名明明就是 AMAX-KY)。底線分隔的檔名一整類都中招。
    _KY = re.compile(r"([一-鿿A-Za-z0-9]+)\s*-\s*KY(?![A-Za-z0-9])", re.I)

    def __init__(self, ssot_path=None, official_set=None, roster=None):
        # 批428-T1:代號冊(VDF tw_listings_industry 1978 檔)。空=未經庫對帳。
        self.roster = frozenset(roster or ())
        self.roster_state = (f"冊在 {len(self.roster)} 檔" if self.roster
                             else "冊不可得(未經庫對帳)")
        b = load_ssot_blocks(ssot_path)
        rules = {r.get("rule_name") or r.get("name"): r for r in b.get("_RAW_REGEX", [])}

        def pat(name):
            r = rules.get(name)
            return r["pattern"] if (r and r.get("pattern")) else _LOCK[name]

        self.rx_bare_strict = re.compile(r"(?<!\d)" + pat("TW_STOCK_CODE_4DIGIT") + r"(?!\d)")
        self.rx_bare_any = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
        self.rx_yf = re.compile(r"(?<!\d)" + pat("TW_YFINANCE_TICKER") + r"\b", re.I)
        self.rx_bb = re.compile(r"(?<!\d)" + pat("TW_BLOOMBERG_TICKER") + r"\b", re.I)
        self.alias2tk, self.tk2name = {}, {}
        for s in b.get("_RAW_SYNONYMS", []):
            canon = s.get("canonical", "")
            mt = re.match(r"(\d{4})", canon)
            if not mt:
                continue
            tk = mt.group(1)
            names = [a for a in s.get("aliases", [])
                     if not re.match(r"^\d{4}(\s+TT|\.TW[O]?)?$", a)]
            cn = next((a for a in names if re.search(r"[一-鿿]", a)),
                      (names[0] if names else ""))
            self.tk2name[tk] = cn
            for a in s.get("aliases", []) + [canon]:
                self.alias2tk[a] = tk
        self.official_set = set(official_set) if official_set else None

    def is_valid_bare(self, t):
        """四碼數字是不是代號?(批428-T1)

        操作員 64 份真檔名實測:「第一場 2026年投資大趨勢」的 2026 被當成代號。
        **但不能用「排除 2000–2030」修**——那會誤殺一整排真代號:
          2002 中鋼 · 2015 豐興 · 2023 燁輝 · 2027 大成鋼 · 2030 彰源 …
        整個鋼鐵類股都住在那個區間裡。年份與代號在字形上無法分辨,
        只能**拿冊對帳**——這正是操作員原令「用 VDF 每日更新的股票清單去對帳」。

        判法(只在年份形狀時才動手,其餘一律照收,避免誤殺新上市):
          冊在 且 落在 1990–2100 且 不在冊上 → 年份,不是代號
          其餘                              → 代號
        冊不可得 → 沿用舊行為,但 roster_state 記「未經庫對帳」,不假裝驗過。
        """
        if not re.fullmatch(r"[1-9]\d{3}", t or ""):
            return False
        roster = getattr(self, "roster", None)
        if roster and 1990 <= int(t) <= 2100 and t not in roster:
            return False
        return True

    @staticmethod
    def numtoken_to_date(tok):
        """8 碼西元 / 7 碼民國 / 6 碼西元兩位年 → ISO 日期。
        批426-D:v0101 缺 7 碼民國(1141202),而操作員真檔名正在用
        (華南投顧-2637-慧洋-KY-1141202)。民國年上限 200 以免把 4 碼代號誤讀。"""
        if not (tok and tok.isdigit()):
            return None
        if len(tok) == 8:
            y, mo, d = tok[:4], tok[4:6], tok[6:8]
        elif len(tok) == 7:                       # 民國:114 1202 → 2025-12-02
            roc = int(tok[:3])
            if not (1 <= roc <= 200):
                return None
            y, mo, d = str(roc + 1911), tok[3:5], tok[5:7]
        elif len(tok) == 6:
            y, mo, d = "20" + tok[:2], tok[2:4], tok[4:6]
        else:
            return None
        try:
            iy, im, idd = int(y), int(mo), int(d)
        except ValueError:
            return None
        if 1990 <= iy <= 2099 and 1 <= im <= 12 and 1 <= idd <= 31:
            return "%04d-%02d-%02d" % (iy, im, idd)
        return None

    @staticmethod
    def _cls(ch):
        if ch.isdigit():
            return "DIGIT"
        o = ord(ch)
        if (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF):
            return "CJK"
        if "A" <= ch.upper() <= "Z":
            return "LATIN"
        return "OTHER"

    def tokenize(self, name):
        stem = re.sub(r"\.(pdf|docx?|pptx?|png|jpe?g|tiff?|webp|heic)$", "",
                      name or "", flags=re.I)
        stem = unicodedata.normalize("NFKC", stem)
        stem = self._SEP.sub(" ", stem)
        out = []
        for chunk in stem.split():
            cur, ck = "", None
            for ch in chunk:
                k = self._cls(ch)
                if k == "OTHER":
                    if cur:
                        out.append((cur, ck))
                    cur, ck = "", None
                    continue
                if ck is None or k == ck:
                    cur += ch
                    ck = k
                else:
                    out.append((cur, ck))
                    cur, ck = ch, k
            if cur:
                out.append((cur, ck))
        return out

    @classmethod
    def _en_rx(cls, words):
        """英文主題詞→詞界 regex(快取一次)。用前後非英數的環視而不是 \\b,
        這樣 "AI-PCB" 的 PCB 命中、"review" 的 ev 不命中(批427-N1)。"""
        key = "_rx_cache_" + str(id(words))
        rx = cls.__dict__.get(key)
        if rx is None:
            alts = "|".join(r"\s*".join(re.escape(w) for w in t.split()) for t in words)
            rx = re.compile(r"(?<![A-Za-z0-9])(?:" + alts + r")(?![A-Za-z0-9])", re.I)
            setattr(cls, key, rx)
        return rx

    def classify_kind(self, name, has_ticker):
        """批427-N:報告型別。回 (kind, reason)。
        次序即判準,不可交換——v0102 先掃詞後看代號,補上主題詞冊之後
        「台新AI伺服器-2317鴻海」就會被判成產業報告(個股誤判成產業)。
          ① 強非個股標記:晨會/研討會縱使列了一串代號也不是個股報告
          ② 有四碼代號 = 個股(主題詞不得越過代號)
          ③ 無代號 → 海外 / 法說
          ④ 無代號 → 產業主題詞冊(中文 in;英文詞界 regex)
          ⑤ 無代號 → 有界啟發:≥2 個全大寫科技縮寫(扣掉券商/市場/評等停用詞)
          ⑥ 未分類(誠實留白,不硬塞)
        """
        raw = unicodedata.normalize("NFKC", name or "")
        low = raw.lower()
        for kind, kws in self._STRONG_NONSTOCK:                      # ①
            hit = next((k for k in kws if k.lower() in low), None)
            if hit:
                return kind, f"檔名含強標記「{hit}」(縱使有代號亦非個股報告)"
        if has_ticker:                                                # ②
            return "個股", "有四碼代號(主題詞不得越過代號:批427-N2)"
        for kind, kws in self._WEAK_NONSTOCK:                        # ③
            hit = next((k for k in kws if k.lower() in low), None)
            if hit:
                return kind, f"無代號且檔名含「{hit}」"
        hit = next((k for k in self._SECTOR_KW if k in raw), None)   # ④
        if hit:
            return "產業", f"無代號且檔名含主題詞「{hit}」"
        m = self._en_rx(self._SECTOR_KW_EN).search(raw)
        if m:
            return "產業", f"無代號且檔名含主題詞「{m.group(0)}」"
        acr = self.tech_acronyms(raw)                                 # ⑤
        if len(acr) >= 2:
            return "產業", f"無代號且有 {len(acr)} 個科技縮寫{acr}(有界啟發,非詞冊命中)"
        return "未分類", "無代號、無型別關鍵詞、科技縮寫不足二(誠實留白)"

    @classmethod
    def tech_acronyms(cls, raw):
        """全大寫 2–5 字縮寫,扣掉券商/市場/評等/單位停用詞。回排序後清單。
        GS-AI PCB CCL → GS 被扣,留 AI/PCB/CCL 三個(批427-N)。"""
        seen = []
        for t in re.findall(r"(?<![A-Za-z0-9])([A-Z]{2,5})(?![A-Za-z0-9])", raw or ""):
            if t in cls._ACRONYM_STOP or t in seen:
                continue
            seen.append(t)
        return sorted(seen)

    @staticmethod
    def kind_expects_ticker(kind):
        """非個股不該被要求要有代號/目標價(批418 DONE_NS 律)。"""
        return kind == "個股"

    def parse_filename(self, name):
        res = {"tickers": [], "dates": [], "cjk": [], "latin": [],
               "names": [], "kind": "", "kind_reason": ""}
        # 批426-E:先把 X-KY 整體收成公司名,避免被分隔符切斷
        for m in self._KY.finditer(unicodedata.normalize("NFKC", name or "")):
            res["names"].append(m.group(0).replace(" ", ""))
        for tok, kind in self.tokenize(name):
            if kind == "DIGIT":
                if len(tok) == 4 and self.is_valid_bare(tok):
                    res["tickers"].append(tok)
                else:
                    d = self.numtoken_to_date(tok)
                    if d:
                        res["dates"].append(d)
            elif kind == "CJK":
                res["cjk"].append(tok)
            elif kind == "LATIN":
                res["latin"].append(tok)
        res["kind"], res["kind_reason"] = self.classify_kind(name, bool(res["tickers"]))
        res["roster_state"] = self.roster_state
        hint, pos = self.name_hint(name, res["tickers"][0] if res["tickers"] else None,
                                   ky_names=res["names"])
        res["name_hint"], res["name_hint_pos"] = hint, pos
        return res

    # 檔名裡的「通用詞」——是報告種類不是公司名(批427-O)
    _NOT_A_NAME = ("報告", "個股", "研究", "投顧", "證券", "投信", "分析", "評等",
                   "評級", "更新", "初次", "首次", "深度", "快報", "追蹤", "評論",
                   "紀要", "摘要", "速報", "月報", "週報", "季報", "年報", "法說",
                   "報吿", "簡報", "重點", "觀察", "報表")

    def name_hint(self, name, ticker, ky_names=None):
        """回 (檔名裡與代號相鄰的公司名, 取法)。取不到=(None, "")。
        批427-O 操作員令:「台新 BROKER 2317 TICKER 鴻海 股票名稱」——
        三者在同一個檔名裡各有其位,券商在前、代號居中、名稱貼著代號。
          先 X-KY 整體(批426-E:慧洋-KY 是公司名,不是「慧洋」+「KY」)
          再代號**之後**兩格內的中文詞(2317鴻海 / 2317 鴻海)
          再代號**之前**兩格內的中文詞(鴻海(2317))
        濾掉券商與通用詞;「台新AI伺服器」裡的「伺服器」不是公司名,
        「兆豐個股報告」整團含「報告」也不是——不濾就會拿主題詞去對帳,
        對出來的 MISMATCH 全是自己造的假紅。"""
        if ky_names:
            return ky_names[0], "KY"
        if not ticker:
            return None, ""
        toks = self.tokenize(name)
        idx = next((i for i, (t, k) in enumerate(toks)
                    if k == "DIGIT" and t == ticker), None)
        if idx is None:
            return None, ""
        for span, pos in ((range(idx + 1, min(idx + 3, len(toks))), "after"),
                          (range(idx - 1, max(idx - 3, -1), -1), "before")):
            for i in span:
                tok, kind = toks[i]
                if kind != "CJK":
                    continue
                if any(w in tok for w in self._NOT_A_NAME):
                    continue
                if BrokerRatingDict.broker_of_token(tok):
                    continue
                if BrokerRatingDict.is_rating_token(tok):     # 批428-T4:「中立」不是公司名
                    continue
                return tok, pos
        return None, ""

    @staticmethod
    def parse_email(text):
        return [{"analyst_id": m.group(1), "broker_domain": m.group(2)}
                for m in re.finditer(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)", text or "")]

    def resolve(self, filename, title="", body=""):
        fn, title, body = filename or "", title or "", body or ""

        def suf(src):
            m = self.rx_yf.search(src) or self.rx_bb.search(src)
            return m.group(1) if m else None

        tk = suf(fn)
        if tk:
            return self._ok(tk, "FILE_SUFFIX")
        m = self.rx_bare_strict.search(fn)
        if m:
            return self._ok(m.group(1), "FILE_BARE")
        if any(k in fn for k in self._SECTOR_KW):
            return self._sec("SECTOR_FILE")
        tk = suf(title)
        if tk:
            return self._ok(tk, "TITLE_SUFFIX")
        for a, t in self.alias2tk.items():
            if a and len(a) >= 2 and re.search(r"[一-鿿A-Za-z]", a) and a in title:
                return self._ok(t, "TITLE_SYNONYM")
        tk = suf(body)
        if tk:
            return self._ok(tk, "BODY_SUFFIX")
        if any(k in title for k in self._SECTOR_KW):
            return self._sec("SECTOR_TITLE")
        for src, why in ((fn, "FILE"), (title, "TITLE")):
            m = self.rx_bare_any.search(src)
            if m:
                cand = m.group(1)
                if 2021 <= int(cand) <= 2030:
                    if ((self.official_set and cand in self.official_set)
                            or (cand == suf(fn + " " + title + " " + body))):
                        return self._ok(cand, "RECLAIM_" + why)
                else:
                    return self._ok(cand, why + "_BARE_ANY")
        m = self.rx_bare_strict.search(body[:600])
        if m:
            return self._ok(m.group(1), "BODY_BARE")
        return self._sec("NONE")

    def _ok(self, tk, method):
        return {"ticker": tk, "name": self.tk2name.get(tk, ""),
                "method": method, "is_sector": False}

    def _sec(self, method):
        return {"ticker": "", "name": "", "method": method, "is_sector": True}

    def cross_check(self, filename_ticker, raw=None, yf=None, bbg=None):
        # 批426-L:v0101 這裡有個 core lambda 定義後從未使用(死碼),已移除。
        res = {"filename_ticker": filename_ticker, "checks": [], "verdict": "PASS"}

        def core4(c):
            m = re.match(r"([1-9]\d{3})", c or "")
            return m.group(1) if m else None

        def add(label, v, ok, msg):
            res["checks"].append({"code": label, "value": v, "ok": ok, "msg": msg})
            if not ok:
                res["verdict"] = "FAIL"

        if raw is not None:
            add("TW_TICKER", raw,
                self.is_valid_bare(raw) and core4(raw) == filename_ticker, "raw core4")
        if yf is not None:
            add("TW_YFINANCE", yf,
                bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", yf, re.I))
                and core4(yf) == filename_ticker, "yf")
        if bbg is not None:
            add("TW_BLOOMBERG", bbg,
                bool(re.fullmatch(r"[1-9]\d{3}\s+TT", bbg, re.I))
                and core4(bbg) == filename_ticker, "bbg")
        return res


# =====================================================================
# 3 · LAYOUT  (font hierarchy + element_type + sentence linking)
# =====================================================================
class Layout:
    _BOILER = ("投顧", "研究部", "免責", "disclosure", "bloomberg", "reuters",
               "not investment advice", "for information only")

    def __init__(self, page_height=842.0):
        self.H = page_height

    @staticmethod
    def _lines_from_chars(chars):
        """group chars into text lines by rounded 'top', ordered top->bottom, left->right."""
        rows = defaultdict(list)
        for c in chars:
            rows[round(c["top"] / 3.0)].append(c)
        lines = []
        for key in sorted(rows):
            cs = sorted(rows[key], key=lambda c: c["x0"])
            text = "".join(c["text"] for c in cs)
            size = statistics.median([c["size"] for c in cs]) if cs else 0
            bold = sum(1 for c in cs if "bold" in (c.get("fontname") or "").lower()) > len(cs) / 2
            top = min(c["top"] for c in cs)
            x0 = min(c["x0"] for c in cs)
            lines.append({"text": text, "size": round(size, 2), "bold": bold,
                          "top": top, "x0": x0, "chars": cs})
        return lines

    def classify(self, chars):
        lines = self._lines_from_chars(chars)
        if not lines:
            return {"lines": [], "body_size": 0, "company_name": "",
                    "main_text": "", "footer": ""}
        sizes = [l["size"] for l in lines]
        body_size = statistics.median(sizes)
        for l in lines:
            r = l["size"] / body_size if body_size else 1
            low = l["text"].lower()
            if l["top"] >= self.H * 0.88 or any(b in low for b in self._BOILER):
                l["level"] = "FOOTER"
            elif r >= 1.8:
                l["level"] = "MAIN_TITLE"
            elif r >= 1.4:
                l["level"] = "HEADLINE"
            elif r >= 1.15:
                l["level"] = "H2"
            elif r <= 0.8:
                l["level"] = "FOOTER"
            else:
                l["level"] = "BODY"
        cands = [l for l in lines if l["level"] in ("MAIN_TITLE", "HEADLINE")]
        company = ""
        if cands:
            cands.sort(key=lambda l: (-l["size"], not l["bold"], l["top"]))
            company = cands[0]["text"].strip()
        body_lines = [l["text"] for l in lines if l["level"] == "BODY"]
        main_text = self._link_sentences(body_lines)
        footer = " ".join(l["text"] for l in lines if l["level"] == "FOOTER")
        return {"lines": lines, "body_size": body_size, "company_name": company,
                "main_text": main_text, "footer": footer}

    @staticmethod
    def _link_sentences(body_lines):
        """rightward+downward link; break only at sentence-final punctuation."""
        buf, out = "", []
        for ln in body_lines:
            ln = ln.strip()
            if not ln:
                continue
            buf = (buf + " " + ln).strip() if buf else ln
            while True:
                m = re.search(r"[。.!?!?]", buf)
                if not m:
                    break
                cut = m.end()
                out.append(buf[:cut].strip())
                buf = buf[cut:].strip()
        if buf:
            out.append(buf)
        return " ".join(out)


# =====================================================================
# 4 · TABLE GEOMETRY (hidden gridline reconstruction)
# =====================================================================
class TableGeometry:
    @staticmethod
    def _cluster(vals, gap):
        vals = sorted(vals)
        if not vals:
            return []
        groups = [[vals[0]]]
        for v in vals[1:]:
            if v - groups[-1][-1] <= gap:
                groups[-1].append(v)
            else:
                groups.append([v])
        return [statistics.mean(g) for g in groups]

    @staticmethod
    def _nearest(centers, v):
        """批426-K:v0101 用 min(range(n), key=...) 逐格線性掃,
        每個字元 O(欄數+列數);一頁上萬字元時明顯拖慢。
        centers 本來就是排序好的 → 改二分,O(log n)。答案完全相同。"""
        if not centers:
            return 0
        i = bisect.bisect_left(centers, v)
        if i == 0:
            return 0
        if i >= len(centers):
            return len(centers) - 1
        return i if (centers[i] - v) < (v - centers[i - 1]) else i - 1

    def reconstruct(self, chars, col_gap=18.0, row_gap=6.0):
        """cluster chars by x (columns) and y (rows) -> 2D grid of cell text."""
        if not chars:
            return {"rows": [], "n_cols": 0}
        row_centers = self._cluster([c["top"] for c in chars], row_gap)
        col_centers = self._cluster([c["x0"] for c in chars], col_gap)
        grid = [["" for _ in col_centers] for _ in row_centers]
        by_row = defaultdict(list)
        for c in chars:
            by_row[self._nearest(row_centers, c["top"])].append(c)
        for ri, cs in by_row.items():
            cs.sort(key=lambda c: c["x0"])
            for c in cs:
                grid[ri][self._nearest(col_centers, c["x0"])] += c["text"]
        rows = [[cell.strip() for cell in r] for r in grid]
        return {"rows": rows, "n_cols": len(col_centers),
                "col_centers": col_centers, "row_centers": row_centers}

    @staticmethod
    def restore_period_header(cells):
        """期間表頭正規化。批426b:改吃 parse_period()——v0101 只認 12/24A 與 2023
        兩型,操作員規格要的 FY-23 / F23 / 20230102 / 230102 / 民國 全部漏。
        回鍵沿用 raw/period/kind 以維持相容,另加 basis(A實際/E預估/F預測)與 roc。"""
        out = []
        for c in cells:
            r = parse_period(c)
            out.append({"raw": r["raw"], "period": r["period"], "kind": r["kind"],
                        "basis": r["basis"], "roc": r["roc"]})
        return out


# =====================================================================
# 5 · NLP REPAIR  (批426-B/C:真 API + 自動掛橋 + 走哪條看得見)
# =====================================================================
class NLPRepair:
    """v0101 的掛鉤呼叫 self.ext.repaired(raw),但 via_nlp 的 TextProcessor
    **沒有 repaired()**(它是 repair(),而且回 dict 不回 str)。
    後果:每次都 AttributeError → 被 except 吃掉 → 靜默退啟發式,
    外接引擎等於沒接,而且對外看不出來(「捕捉到卻不顯示」)。
    v0102:用真 API,而且把這一次走的路徑對外交代。"""

    def __init__(self, external_engine=None, auto_hub=True, via_root=None):
        self.ext = external_engine
        self._route = "HEURISTIC"
        self._why = ""
        self.hub = None
        if self.ext is not None:
            self._route = "DIRECT"
        elif auto_hub:
            hub, why = mount_nlp_hub(via_root)
            self.hub = hub
            self._why = why
            if hub is not None:
                tp = hub.text_processor()
                if tp is not None:
                    self.ext = tp
                    self._route = "HUB"
                else:
                    self._why = self._why or "橋在位但 text_processor() 回 None"

    def route(self) -> dict:
        """走哪一條、為何沒走到更好的那條——都要說得出來。"""
        st = self.hub.mount() if self.hub is not None else {}
        return {"route": self._route, "why": self._why,
                "hub_dir": st.get("dir_name", ""), "hub_state": st.get("state", "")}

    def repair_text(self, raw):
        if self.ext is not None:
            try:
                r = self.ext.repair(raw)              # 真 API:回 dict
                if isinstance(r, dict):
                    for k in ("repaired", "text", "output", "result"):
                        if isinstance(r.get(k), str) and r[k].strip():
                            return r[k]
                elif isinstance(r, str) and r.strip():
                    return r
            except Exception as exc:
                self._why = f"repair() 例外 {type(exc).__name__}(已退後備)"
            try:
                n = self.ext.normalize(raw)           # 次選:正規化也算修復
                if isinstance(n, str) and n.strip():
                    return n
            except Exception:
                pass
        t = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw or "")
        return re.sub(r"\s+", " ", t).strip()

    def split_sentences(self, text):
        if self.ext is not None:
            try:
                s = self.ext.split_sentences(text)
                if isinstance(s, list) and s:
                    return s
            except Exception as exc:
                self._why = f"split_sentences() 例外 {type(exc).__name__}(已退後備)"
        parts = re.split(r"(?<=[。.!?!?])\s+", text or "")
        return [p.strip() for p in parts if p.strip()]


# =====================================================================
# 5b · 正典驗證橋(批426 新增;操作員令「整合如果關聯 驗證法」)
# ---------------------------------------------------------------------
# 操作員另附兩支同族正典,關聯明確:
#   VRN_MDL008_CrossValidator  → 單位正規化 to_million/std_val、
#                                 容差分層 tolerance(依量級,非相對誤差)、
#                                 compare_one/classify_mismatch/fallback_resolve
#   VRN_TW02_ReportParser      → CrossValidator.validate 三源交叉核對
#                                 (Filename ↔ 第一頁 ↔ 財報頁)、is_valid_ticker
# 本檔 v0101 的 _band() 其實是 MDL008 tolerance() 的**粗糙複製品**,而且模型不同:
#   MDL008 = 依金額量級給絕對容差(百萬元;>=1000 大、>=100 中、其餘小)
#   v0101  = 一律相對誤差 1%/5%/10%
# 零九頭龍:不再寫第三份,改**綁正典**;正典缺席才退本地 band,並且說得出退了。
# =====================================================================
class XValBridge:
    """掛載 MDL008 / TW02 正典。缺席=誠實降級,絕不假裝有。"""

    def __init__(self, via_root=None, mdl008_path=None, tw02_path=None):
        self.mdl008, self.tw02 = None, None
        self.why = {"mdl008": "", "tw02": ""}
        root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
        for key, explicit, globs in (
                ("mdl008", mdl008_path, ("VRN_MDL008_CrossValidator*.py",)),
                ("tw02", tw02_path, ("VRN_TW02_ReportParser*.py",))):
            hit = Path(explicit) if explicit else None
            if hit is None and root is not None:
                for g in globs:
                    found = sorted((root / "functional modules" / "VRN").glob(g))
                    if found:
                        hit = found[-1]
                        break
            if hit is None or not Path(hit).exists():
                self.why[key] = f"{globs[0]} 未尋獲(functional modules/VRN/)"
                continue
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"via_{key}_fpe", hit)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                setattr(self, key, mod)
            except Exception as exc:
                self.why[key] = f"載入失敗 {type(exc).__name__}:{str(exc)[:80]}"

    def status(self):
        return {"mdl008": self.mdl008 is not None, "tw02": self.tw02 is not None,
                "why": {k: v for k, v in self.why.items() if v}}

    # ---- MDL008:單位正規化 + 量級容差 ----
    def std_val(self, value, unit="million"):
        if self.mdl008 is not None:
            try:
                return self.mdl008.std_val(value, unit)
            except Exception:
                pass
        try:
            return float(str(value).replace(",", "").replace(",", "").strip())
        except Exception:
            return None

    def tolerance(self, v):
        """回 (絕對容差, 來源)。正典缺席=None 表示「用相對誤差 band」。"""
        if self.mdl008 is not None:
            try:
                return self.mdl008.tolerance(v), "MDL008"
            except Exception:
                pass
        return None, "LOCAL_BAND"

    # ---- TW02:三源交叉核對 ----
    def three_way(self, filename_data, first_page_data, financial_page_data):
        if self.tw02 is None:
            return None
        try:
            return self.tw02.CrossValidator.validate(
                filename_data, first_page_data, financial_page_data)
        except Exception as exc:
            self.why["tw02"] = f"validate 例外 {type(exc).__name__}:{str(exc)[:80]}"
            return None

    def is_valid_ticker(self, code):
        if self.tw02 is not None:
            try:
                return bool(self.tw02.is_valid_ticker(code))
            except Exception:
                pass
        return bool(re.fullmatch(r"[1-9]\d{3}", code or "")) and not (2000 <= int(code or 0) <= 2030)


# =====================================================================
# 5b · NAME RECONCILER  (批427-O:代號 → 證券名稱 對帳)
# =====================================================================
class NameReconciler:
    """代號→證券名稱四階梯對帳。離線優先;網路一律由操作員自己開閘。

    操作員令(批427):「台新 BROKER 2317 TICKER 鴻海 股票名稱,可透過 TICKER 去
    TWSE/TPEX 去找名稱證券名稱抓回來對照,也可以 VDF 系統建立的股票清單
    每日更新去對帳」——這裡就是那條對帳線,四階梯由近而遠:

      ① SSOT   _RAW_SYNONYMS(本檔已載,零 I/O)
      ② VDF_DB tw_universe / tw_listings —— ENG081 每日更新的正典股票清單。
                唯讀開庫;庫不在 / 被別的行程鎖住 / 無 duckdb = 誠實 SKIP,
                **絕不建庫**(建出一個空庫比查不到更糟:下游會當它是真的)。
      ③ MDL010 VRN_MDL010_CodeRegistry 預設冊(離線後備)
      ④ WEB    TWSE / TPEX OpenAPI —— 只在操作員自己開妥雙閘後才走。
                閘未開 = SKIP_NO_CONSENT,本引擎**絕不代設 VIA_NET_CONSENT**;
                真要走也是走正典 SUP_MDL740.http_json,不自建抓取(零九頭龍)。

    查不到官方名 = UNKNOWN,不是 PASS。來源不可得就給 N/A 而不是綠——
    批422 的假綠正是「不可得當成沒問題」。
    """

    TWSE_TPEX_ENDPOINTS = (
        ("TWSE", "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL"),
        ("TPEX", "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"),
    )
    # 庫內查名次序。批427-O 實測:本會期沙箱正典庫 vdf_tw_market.duckdb 裡
    # **沒有** tw_universe / tw_listings,真正帶 code+name 的是
    # tw_listings_industry(1978 檔,鴻海/慧洋-KY/志強-KY 三檔操作員真報告全在)。
    # 只寫 ENG081 的 UNIVERSE 表名等於整條階梯空轉——所以三張表都排進來,
    # 有哪張用哪張,誰都沒有就誠實 SKIP。
    DB_TABLES = (("tw_universe", " ORDER BY asof_date DESC"),
                 ("tw_listings", ""),
                 ("tw_listings_industry", ""))
    _CODE_KEYS = ("Code", "code", "SecuritiesCompanyCode", "股票代號", "證券代號")
    _NAME_KEYS = ("Name", "name", "CompanyName", "公司名稱", "股票名稱", "證券名稱")
    # 名稱正規化要剝掉的尾綴(比對容差用)
    _STRIP = ("股份有限公司", "有限公司", "控股公司", "控股", "公司",
              "-KY", "-ky", "KY", "*", "﹡", "(TW)", "(TWO)")

    def __init__(self, via_root=None, tk2name=None, db=None, net_tool=None):
        self.tk2name = dict(tk2name or {})
        self.root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
        self.why = {}
        self._db = Path(db) if db else None
        self._reg = None            # MDL010 惰性
        self._web_cache = {}        # 端點名冊惰性(一次抓、整份留)
        self.industry = None        # 庫階梯順手帶回的官方產業別(tw_listings_industry)
        self._net = net_tool        # 可注入(自測用替身,不出網)
        self._net_probed = net_tool is not None
        if self._db is None:
            self._db = self._locate_db()

    # ---- 位置解析:綁 ENG081 的常數,不自己另寫一份路徑(零九頭龍) ----
    def _locate_db(self):
        if self.root is None:
            self.why["db"] = "找不到 VIA 根(functional modules/ + supportive modules/)"
            return None
        eng = sorted((self.root / "functional modules" / "VDF" / "engine")
                     .glob("VDF_ENG081_UniverseAlign_v*.py")) if self.root else []
        if eng:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("via_eng081_fpe", eng[-1])
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                self._eng081 = mod
                return Path(getattr(mod, "DB_TW"))
            except Exception as exc:
                self.why["db"] = f"ENG081 載入失敗 {type(exc).__name__}:{str(exc)[:70]}"
        self._eng081 = None
        return (self.root / "functional modules" / "VDF" / "output_hub" / "mega"
                / "vdf_tw_market.duckdb")

    # ---- 名稱正規化 ----
    @classmethod
    def norm_name(cls, s):
        t = unicodedata.normalize("NFKC", str(s or "")).strip()
        for w in cls._STRIP:
            t = t.replace(w, "")
        return re.sub(r"[\s\u3000().,、·\-_]+", "", t)

    @classmethod
    def same_name(cls, a, b):
        """三層,由嚴到寬。每放寬一層都會多收一點假綠,所以每層都設界:
          ① 正規化後完全相等
          ② 包含:鴻海 ⊂ 鴻海精密、慧洋 ⊂ 慧洋-KY。兩字以下不做包含判
            (「大」⊂「大同」會誤綠)
          ③ 中文縮寫:短名是長名的**有序子序列**且首字相同。
            台積電 ⊂ 台灣積體電路(台…積…電)、中鋼 ⊂ 中國鋼鐵、台泥 ⊂ 台灣水泥——
            這是台股簡稱的通則,②的包含判抓不到(台積電並非連續子字串;
            批427-O 自審實錄:我原本斷言②抓得到,實跑打臉,是斷言錯不是碼錯)。
            設界:短名 ≥2 且全中文、長名 ≥4、首字必須相同。
            首字這一刀擋掉「台泥 vs 台灣化學纖維」這種只共用一個字的偽同名。"""
        x, y = cls.norm_name(a), cls.norm_name(b)
        if not x or not y:
            return False
        if x == y:
            return True
        if min(len(x), len(y)) < 2:
            return False
        if (x in y) or (y in x):
            return True
        short, long_ = (x, y) if len(x) <= len(y) else (y, x)
        if len(long_) < 4 or short[0] != long_[0]:
            return False
        if not all("\u4e00" <= c <= "\u9fff" for c in short):
            return False
        it = iter(long_)
        return all(c in it for c in short)

    # ---- 階梯 ① SSOT ----
    def _from_ssot(self, tk):
        n = self.tk2name.get(tk)
        return (n, "SSOT") if n else (None, "")

    # ---- 階梯 ② VDF 正典庫(唯讀;絕不建庫) ----
    def _from_vdf(self, tk):
        if not self._db or not Path(self._db).exists():
            self.why.setdefault("db", f"庫不在:{self._db}(誠實 SKIP;不建庫)")
            return None, ""
        try:
            import duckdb
        except Exception:
            self.why["db"] = "本環境無 duckdb(誠實 SKIP)"
            return None, ""
        con = None
        try:
            con = duckdb.connect(str(self._db), read_only=True)
            have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
            for tbl, order in self.DB_TABLES:
                if tbl not in have:
                    continue
                # DuckDB DESCRIBE 回 (column_name, column_type, null, key, ...):
                # 欄名是 c[0]。批427-O 自審實錄:初版寫 c[1] 收到的是**型別**,
                # 於是 "name" 永遠不在集合裡 → 整條庫階梯靜靜空轉,
                # 三檔 -KY 全判 UNKNOWN。錯一個索引,一整層樓不亮。
                cols = {c[0] for c in con.execute(f'DESCRIBE "{tbl}"').fetchall()}
                if "name" not in cols:
                    continue
                key = "code" if "code" in cols else ("ticker" if "ticker" in cols else None)
                if key is None:
                    continue
                od = order if "asof_date" in cols else ""
                ind = ', "industry_name"' if "industry_name" in cols else ", NULL"
                row = con.execute(
                    f'SELECT "name"{ind} FROM "{tbl}" '
                    f'WHERE CAST("{key}" AS VARCHAR)=?{od} LIMIT 1', [tk]).fetchone()
                if row and row[0]:
                    self.industry = str(row[1]) if len(row) > 1 and row[1] else None
                    return str(row[0]), f"VDF_DB:{tbl}"
            self.why["db"] = f"庫在但 {'/'.join(t for t, _ in self.DB_TABLES)} 查無此代號"
            return None, ""
        except Exception as exc:
            self.why["db"] = f"開庫失敗(多為別的行程持鎖){type(exc).__name__}:{str(exc)[:70]}"
            return None, ""
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass

    def code_roster(self):
        """庫裡的四碼代號全集(批428-T1:給 is_valid_bare 判年份 vs 代號)。
        唯讀、只取 code 欄、只跑一次;庫不可得=空集合(誠實,不是零筆)。"""
        if getattr(self, "_roster", None) is not None:
            return self._roster
        self._roster = frozenset()
        if not self._db or not Path(self._db).exists():
            self.why.setdefault("roster", f"庫不在:{self._db}")
            return self._roster_offline()
        try:
            import duckdb
        except Exception:
            self.why["roster"] = "本環境無 duckdb"
            return self._roster_offline()
        con = None
        try:
            con = duckdb.connect(str(self._db), read_only=True)
            have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
            codes = set()
            for tbl, _ in self.DB_TABLES:
                if tbl not in have:
                    continue
                cols = {c[0] for c in con.execute(f'DESCRIBE "{tbl}"').fetchall()}
                key = "code" if "code" in cols else ("ticker" if "ticker" in cols else None)
                if key is None:
                    continue
                codes |= {str(r[0]).strip()
                          for r in con.execute(f'SELECT DISTINCT "{key}" FROM "{tbl}"').fetchall()
                          if r[0] is not None}
            self._roster = frozenset(c for c in codes if re.fullmatch(r"[1-9]\d{3}", c))
            if not self._roster:
                self.why["roster"] = "庫在但三張表都取不到 code 欄"
        except Exception as exc:
            self.why["roster"] = f"開庫失敗 {type(exc).__name__}:{str(exc)[:60]}"
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
        return self._roster or self._roster_offline()

    def _roster_offline(self):
        """庫取不到代號冊時的離線後備(批429-W4)。回空=真的什麼都沒有。"""
        off = self._offline()
        self._roster = frozenset(c for c in off if re.fullmatch(r"[1-9]\d{3}", c))
        if self._roster:
            self.why["roster"] = (self.why.get("roster", "") +
                                  f" → 退離線冊 {len(self._roster)} 檔"
                                  f"(asof {getattr(self, 'offline_asof', '?')})")
        return self._roster

    # ---- 階梯 ②b 離線代號冊(批429-W4) ----
    OFFLINE_ROSTER = "VRN_TWRoster_Offline_v*.json"

    def _offline(self):
        """離線代號冊。批429-W4:操作員的 OneDrive 副本沒有 vdf_tw_market.duckdb,
        庫一不在,**一個缺件同時廢掉三個能力**——代號冊空(內文四碼全收)、
        名稱對帳全 UNKNOWN、TP 合理性閘拿不到現價也睡著。
        這份冊是庫的快照(帶 asof 與來源),不是第二份實作;庫在時仍以庫為準。"""
        if getattr(self, "_off", None) is not None:
            return self._off
        self._off = {}
        hit = sorted((self.root / "functional modules" / "VRN")
                     .glob(self.OFFLINE_ROSTER)) if self.root else []
        if not hit:
            self.why["offline"] = f"{self.OFFLINE_ROSTER} 未尋獲"
            return self._off
        try:
            d = json.loads(hit[-1].read_text(encoding="utf-8"))
            self._off = d.get("codes") or {}
            self.offline_asof = d.get("asof", "?")
            self.offline_n = d.get("n", len(self._off))
        except Exception as exc:
            self.why["offline"] = f"離線冊讀取失敗 {type(exc).__name__}:{str(exc)[:60]}"
        return self._off

    def _from_offline(self, tk):
        rec = self._offline().get(str(tk))
        if not rec or not rec.get("name"):
            return None, ""
        self.industry = rec.get("industry") or self.industry
        return str(rec["name"]), f"OFFLINE({getattr(self, 'offline_asof', '?')})"

    # ---- 階梯 ③ MDL010 預設冊 ----
    def _from_registry(self, tk):
        if self._reg is None:
            self._reg = False
            hit = sorted((self.root / "functional modules" / "VRN")
                         .glob("VRN_MDL010_CodeRegistry*.py")) if self.root else []
            if not hit:
                self.why["mdl010"] = "VRN_MDL010_CodeRegistry*.py 未尋獲"
            else:
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("via_mdl010_fpe", hit[-1])
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                    self._reg = mod.VRN_MDL010_CodeRegistry()
                except Exception as exc:
                    self.why["mdl010"] = f"載入失敗 {type(exc).__name__}:{str(exc)[:70]}"
        if not self._reg:
            return None, ""
        try:
            r = self._reg.resolve(tk)
            nm = str(r.get("name") or "")
            # MDL010 對任何四碼都會 regex_autofill 出 name="TW:2637" 並回 ok=True。
            # 那是**代號的回音**,不是證券名稱。收下它的話,慧洋-KY 會被判成
            # MISMATCH——自己造一盞假紅,比查不到還糟(批427-O 實測踩到)。
            synthetic = (r.get("source") == "regex_autofill"
                         or bool(re.fullmatch(r"(?:TW|TWO|TWSE|TPEX)[:\-]?\d{3,6}", nm))
                         or self.norm_name(nm) == self.norm_name(tk))
            if r.get("ok") and nm and not synthetic:
                return nm, "MDL010"
            if synthetic:
                self.why["mdl010"] = f"只給得出佔位名「{nm}」(代號回音,不採計)"
        except Exception as exc:
            self.why["mdl010"] = f"resolve 例外 {type(exc).__name__}:{str(exc)[:70]}"
        return None, ""

    # ---- 同意閘:只讀,永不代設 ----
    def _net_mod(self):
        if self._net_probed:
            return self._net
        self._net_probed = True
        hit = sorted((self.root / "supportive modules" / "network")
                     .glob("SUP_MDL740_NetUnified_v*.py")) if self.root else []
        if not hit:
            self.why["web"] = "正典網路工具 SUP_MDL740_NetUnified_v*.py 未尋獲"
            return None
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("via_net740_fpe", hit[-1])
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            self._net = mod
        except Exception as exc:
            self.why["web"] = f"網路正典載入失敗 {type(exc).__name__}:{str(exc)[:70]}"
        return self._net

    def gate(self):
        """回 (閘開?, 說明)。只讀環境變數;**絕不代設**(治理鐵律)。"""
        net = self._net_mod()
        if net is None:
            return False, self.why.get("web", "網路正典缺席")
        try:
            g = net.gate_state()
        except Exception as exc:
            return False, f"gate_state 例外 {type(exc).__name__}"
        if g.get("open"):
            return True, "雙閘已由操作員開妥"
        return False, ("閘一 VIA_NET_CONSENT 未開" if not g.get("gate1_net_consent")
                       else "閘二 VIA_SCRAPE_CONSENT 未設")

    # ---- 階梯 ④ TWSE/TPEX 線上 ----
    def _from_web(self, tk):
        ok, why = self.gate()
        if not ok:
            self.why["web"] = f"SKIP_NO_CONSENT:{why}(引擎不代設同意閘)"
            return None, ""
        net = self._net_mod()
        for mkt, url in self.TWSE_TPEX_ENDPOINTS:
            roster = self._web_cache.get(mkt)
            if roster is None:
                try:
                    r = net.http_json(url, timeout=30)
                except Exception as exc:
                    self.why["web"] = f"http_json 例外 {type(exc).__name__}:{str(exc)[:60]}"
                    continue
                if not isinstance(r, dict) or r.get("state") != "OK":
                    self.why["web"] = f"{mkt} {r.get('state') if isinstance(r, dict) else '?'}:" \
                                      f"{(r or {}).get('note', '')[:70]}"
                    continue
                roster = {}
                for row in (r.get("data") or []):
                    if not isinstance(row, dict):
                        continue
                    c = next((str(row[k]).strip() for k in self._CODE_KEYS if row.get(k)), "")
                    n = next((str(row[k]).strip() for k in self._NAME_KEYS if row.get(k)), "")
                    if c and n:
                        roster[c] = n
                self._web_cache[mkt] = roster
            if tk in roster:
                return roster[tk], f"WEB:{mkt}"
        return None, ""

    # ---- 對外 ----
    def lookup(self, tk, allow_web=True):
        """回 (官方名, 來源, 走過的階梯)。四階梯依序,先中先回。"""
        trail = []
        for label, fn in (("SSOT", self._from_ssot), ("VDF_DB", self._from_vdf),
                          ("OFFLINE", self._from_offline),
                          ("MDL010", self._from_registry), ("WEB", self._from_web)):
            if label == "WEB" and not allow_web:
                trail.append("WEB:未嘗試(allow_web=False)")
                break
            name, src = fn(tk)
            trail.append(f"{label}:{'命中' if name else '未中'}")
            if name:
                return name, src, trail
        return None, "", trail

    def reconcile(self, ticker, name_hint, allow_web=True):
        """回對帳結果。誠實三態:
             MATCH        官方名與檔名提示同名
             MISMATCH     兩邊都有、卻不同名(真紅:檔名代號與公司名對不上)
             NO_HINT      檔名沒帶公司名(不是錯,只是無從對)
             UNKNOWN      四階梯都查不到官方名(來源不可得 ≠ 沒問題)
             NO_TICKER    沒有代號可查
        """
        base = {"ticker": ticker, "hint": name_hint, "official": None,
                "source": "", "trail": [], "why": {}}
        if not ticker:
            return dict(base, verdict="NO_TICKER", note="檔名無四碼代號")
        self.industry = None
        official, src, trail = self.lookup(ticker, allow_web=allow_web)
        base.update({"official": official, "source": src, "trail": trail,
                     "industry": self.industry, "why": dict(self.why)})
        if official is None:
            return dict(base, verdict="UNKNOWN",
                        note="四階梯皆未取得官方證券名稱(不可得≠沒問題,故非 PASS)")
        if not name_hint:
            return dict(base, verdict="NO_HINT",
                        note=f"官方名={official},但檔名未帶公司名可對")
        same = self.same_name(official, name_hint)
        return dict(base, verdict="MATCH" if same else "MISMATCH",
                    note=(f"檔名「{name_hint}」{'≡' if same else '≠'}官方「{official}」"
                          f"(來源 {src})"))


# =====================================================================
# 6 · FINANCIAL VALIDATION  (批426-A None-safe;綁 MDL008 容差)
# =====================================================================
class FinancialValidation:
    def __init__(self, xval: "XValBridge | None" = None):
        self.xv = xval

    @staticmethod
    def _num(x):
        """批426-A:None / 空字串 / 帶逗號字串 一律安全轉數;不可轉=None。
        v0101 直接拿 None 去算術,multiply(None,10,5) 當場 TypeError——
        而 None 正是抽取器找不到數字時的常態回傳。"""
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return None if isinstance(x, float) and x != x else float(x)
        try:
            return float(str(x).replace(",", "").replace(",", "").strip())
        except Exception:
            return None

    def _band(self, err, expected=None):
        """容差判定。有 MDL008=用它的量級絕對容差;缺席=退相對誤差 band 並註明。"""
        a = abs(err)
        if self.xv is not None and expected is not None:
            tol, src = self.xv.tolerance(expected)
            if tol is not None:
                diff = abs(err * expected)
                if diff <= tol:
                    return "PASS", 1.0, src
                if diff <= tol * 5:
                    return "WARN", 0.65, src
                return "FAIL", 0.45, src
        if a <= 0.01:
            return "PASS", 1.0, "LOCAL_BAND"
        if a <= 0.05:
            return "PASS-SOFT", 0.85, "LOCAL_BAND"
        if a <= 0.10:
            return "WARN", 0.65, "LOCAL_BAND"
        return "FAIL", 0.45, "LOCAL_BAND"

    def add_sub(self, total, parts):
        """total ?= sum(parts)。無值一律 N/A(不猜、不當 0)。"""
        t = self._num(total)
        ps = [self._num(p) for p in (parts or [])]
        if t is None or not ps or any(p is None for p in ps):
            return {"verdict": "N/A", "conf": 0.0, "rel_err": None,
                    "why": "無值(total 或 parts 有 None)"}
        if t == 0:
            return {"verdict": "N/A", "conf": 0.0, "rel_err": None, "why": "total=0"}
        s = sum(ps)
        err = (s - t) / t
        v, c, src = self._band(err, t)
        return {"verdict": v, "conf": c, "rel_err": round(err, 4),
                "computed": s, "reported": t, "tol_src": src}

    def multiply(self, actual, a, b, scale_percent=False):
        """actual ?= a * b(TargetPrice = PER × EPS;NetIncome = EPS × Shares)。"""
        av, x, y = self._num(actual), self._num(a), self._num(b)
        if av is None or x is None or y is None:
            return {"verdict": "N/A", "conf": 0.0, "why": "無值"}
        expected = x * y
        if scale_percent:
            expected /= 100.0
        if expected == 0:
            return {"verdict": "N/A", "conf": 0.0, "why": "expected=0"}
        err = (av - expected) / expected
        v, c, src = self._band(err, expected)
        return {"verdict": v, "conf": c, "expected": round(expected, 4),
                "actual": av, "rel_err": round(err, 4), "tol_src": src}

    def division(self, actual, numer, denom, scale_percent=False):
        """兩段:A 量級 0.5x–3.0x、B 容差。處理 ROE %/小數。"""
        av, n, d = self._num(actual), self._num(numer), self._num(denom)
        if av is None or n is None or d is None or d == 0 or av == 0:
            return {"verdict": "N/A", "conf": 0.0, "why": "無值或分母/實際為 0"}
        expected = n / d
        if scale_percent:
            expected *= 100.0
        if expected == 0:
            return {"verdict": "N/A", "conf": 0.0, "why": "expected=0"}
        ratio = av / expected
        stage_a = 0.5 <= ratio <= 3.0
        err = (av - expected) / expected
        v, c, src = self._band(err, expected)
        if v == "FAIL" and stage_a:
            v, c = "PASS-RANGE", 0.6      # 量級對(平均 vs 期末權益之類),不判死
        return {"verdict": v, "conf": c, "expected": round(expected, 4),
                "actual": av, "ratio": round(ratio, 3),
                "stageA_magnitude_ok": stage_a, "tol_src": src}

    def historical_yoy(self, series):
        """series: list[(year, value)] ascending。無值那一年回 None,不外插。"""
        out = []
        s = sorted(series or [])
        for i in range(1, len(s)):
            (_, v0), (y1, v1) = s[i - 1], s[i]
            a, b = self._num(v0), self._num(v1)
            if a in (None, 0) or b is None:
                out.append({"year": y1, "yoy": None})
                continue
            out.append({"year": y1, "yoy": round((b - a) / abs(a), 4)})
        return out


# =====================================================================
# 5c · 期間/日期正規化(批426b;操作員規格)
# ---------------------------------------------------------------------
# 操作員規格三條:
#   ① 整合到「百萬」,小數點後**兩位**
#   ② 補不足能力
#   ③ 數字 / 英文+數字 / 民國,且**有前綴**:FY-23、F23、2023、20230102、230102
# v0101 的 restore_period_header 只認 12/24A 與 2023 兩型,其餘全回 None。
# 這裡把研報實務上會出現的寫法一次收齊,並且**分開回報「期間」與「基準」**
# (A=實際 / E=預估 / F=預測),因為把預估當實際比對就是製造假訊息。
# =====================================================================
MILLION_DECIMALS = 2                     # 規格①:百萬 + 小數點後兩位

_BASIS = {"A": "actual", "E": "estimate", "F": "forecast"}


def _yy_to_year(yy: int) -> int:
    """兩位年展開:00–79 → 20xx,80–99 → 19xx(研報實務不會出現 1980 前預估)。"""
    return 2000 + yy if yy <= 79 else 1900 + yy


def parse_period(tok):
    """任一期間/日期記號 → 結構化。認不出回 kind=None(誠實,不硬猜)。
    回 {"raw","kind","period","basis","roc"};kind ∈ date|year|quarter|month|None"""
    s = unicodedata.normalize("NFKC", str(tok or "")).strip()
    if not s:
        return {"raw": tok, "kind": None, "period": None, "basis": None, "roc": False}

    def out(kind, period, basis=None, roc=False):
        return {"raw": tok, "kind": kind, "period": period, "basis": basis, "roc": roc}

    # 民國:114年 / 民國114 / ROC114
    m = re.fullmatch(r"(?:民國|ROC)?\s*(\d{2,3})\s*年", s, re.I)
    if m and 1 <= int(m.group(1)) <= 200:
        return out("year", str(int(m.group(1)) + 1911), None, True)

    # 純數字:8 碼西元日 / 7 碼民國日 / 6 碼西元日 / 4 碼年
    if s.isdigit():
        if len(s) in (6, 7, 8):
            d = TickerFilename.numtoken_to_date(s)
            if d:
                return out("date", d, None, len(s) == 7)
        if len(s) == 4 and 1990 <= int(s) <= 2099:
            return out("year", s)
        return out(None, None)

    # 帶分隔的日期:2023-01-02 / 2023/1/2 / 114-12-02(民國)
    m = re.fullmatch(r"(\d{2,4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        roc = False
        if y <= 200:                                  # 民國年
            y, roc = y + 1911, True
        elif y < 1000:
            y = _yy_to_year(y)
        if 1990 <= y <= 2099 and 1 <= mo <= 12 and 1 <= dd <= 31:
            return out("date", "%04d-%02d-%02d" % (y, mo, dd), None, roc)

    # 季:1Q25 / 25Q1 / Q1 2025 / 1Q2025
    m = (re.fullmatch(r"([1-4])Q\s*(\d{2,4})", s, re.I)
         or re.fullmatch(r"Q([1-4])\s*(\d{2,4})", s, re.I))
    if m:
        q, y = int(m.group(1)), int(m.group(2))
        y = y if y >= 1000 else _yy_to_year(y)
        return out("quarter", "%04d-Q%d" % (y, q))
    m = re.fullmatch(r"(\d{2,4})\s*Q([1-4])", s, re.I)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        y = y if y >= 1000 else _yy_to_year(y)
        return out("quarter", "%04d-Q%d" % (y, q))

    # 月:12/24A → 2024-12(actual);12/25E → 2025-12(estimate)
    m = re.fullmatch(r"(\d{1,2})/(\d{2})([AEF])?", s, re.I)
    if m:
        mo, yy = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return out("month", "%04d-%02d" % (_yy_to_year(yy), mo),
                       _BASIS.get((m.group(3) or "").upper()))

    # 會計年度前綴:FY-23 / FY23 / FY 2023 / F23 / E23 / A23 / 23F / 2023F
    m = re.fullmatch(r"FY[\s\-_]?(\d{2,4})([AEF])?", s, re.I)
    if m:
        y = int(m.group(1))
        return out("year", str(y if y >= 1000 else _yy_to_year(y)),
                   _BASIS.get((m.group(2) or "").upper()))
    m = re.fullmatch(r"([AEF])[\s\-_]?(\d{2,4})", s, re.I)       # F23 / E-23
    if m:
        y = int(m.group(2))
        return out("year", str(y if y >= 1000 else _yy_to_year(y)),
                   _BASIS[m.group(1).upper()])
    m = re.fullmatch(r"(\d{2,4})[\s\-_]?([AEF])", s, re.I)       # 23F / 2023E
    if m:
        y = int(m.group(1))
        return out("year", str(y if y >= 1000 else _yy_to_year(y)),
                   _BASIS[m.group(2).upper()])

    return out(None, None)


def to_million_2dp(value, unit="million", unit_mult=None):
    """規格①:任何單位 → 百萬,固定小數點後兩位。
    unit_mult 可傳 MDL008 的 UNIT_MULT 以共用同一份單位冊(零九頭龍)。
    無值 / 不可轉 → None(不當 0)。"""
    mult = (unit_mult or {}).get(unit)
    if mult is None:
        mult = {"million": 1.0, "billion": 1000.0, "hundred_million": 100.0,
                "million_ntd": 1.0, "thousand_ntd": 0.001, "thousand": 0.001,
                "ntd": 1e-6, "yuan": 1e-6, "元": 1e-6, "千元": 0.001,
                "百萬": 1.0, "億": 100.0, "十億": 1000.0}.get(unit, 1.0)
    try:
        v = float(str(value).replace(",", "").replace(",", "").strip()) * mult
    except Exception:
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return round(v, MILLION_DECIMALS)


# =====================================================================
# 7 · PRICE ADJUSTMENT (批426-H:復權誠實 + TP 合理性閘)
# =====================================================================
class PriceAdjustment:
    # 批419 工作站實錄:37 份真報告裡三份的 TP/價 比是 0.020 / 0.019 / 0.005
    # ——目標價只有股價的 1/50 到 1/200,那是抽錯的數。把它印成
    # 「潛在上漲空間 -98%」比不印更糟,讀的人會以為那是預測。
    TP_SANITY_LO, TP_SANITY_HI = 0.2, 5.0

    @staticmethod
    def to_adjusted(raw_price, cum_adjust_factor):
        """passed ex-div/ex-rights → 乘累積因子使序列可比。"""
        if raw_price is None or cum_adjust_factor in (None, 0):
            return raw_price
        return round(raw_price * cum_adjust_factor, 4)

    def normalize_series(self, prices, factors):
        return [self.to_adjusted(p, f) for p, f in zip(prices, factors)]

    def tp_sanity(self, target_price, price):
        """回 (態, 比值)。OK / TP_SUSPECT(帶外=疑抽錯)/ NA(算不了)。
        只 flag 不丟棄:我們不知道哪個數字才對,丟棄等於替操作員決定。"""
        try:
            if target_price is None or not price:
                return "NA", None
            r = float(target_price) / float(price)
        except Exception:
            return "NA", None
        return ("OK" if self.TP_SANITY_LO <= r <= self.TP_SANITY_HI else "TP_SUSPECT"), r

    def upside(self, target_price, current_price_adj, is_adjusted=True):
        """批426-H:current_price_adj 必須是**已復權**價。
        批425 實證:ENG080 在價表缺 adj_close 時誠實拒絕拿 close 頂替
        (「Adjusted 與原始不混用」)=正確行為。這裡照同一條律:
        is_adjusted=False 一律拒算,回 None 並由呼叫端交代,不悄悄用原始價。"""
        if not is_adjusted:
            return None
        if target_price is None or not current_price_adj:
            return None
        return round((float(target_price) - float(current_price_adj))
                     / float(current_price_adj), 4)


# =====================================================================
# 8 · CROSS VALIDATION
# =====================================================================
class BrokerRatingDict:
    BROKER = {
        "KGI": ["凱基", "kgi", "kgieworld"], "YUANTA": ["元大", "yuanta"],
        "FUBON": ["富邦", "fubon"], "CAPITAL": ["群益", "capital"],
        "PRESIDENT": ["統一", "pscnet"], "CTBC": ["中信", "中國信託", "ctbc"],
        "JPMORGAN": ["摩根", "jp morgan", "j.p. morgan", "jpm", "jpmorgan"],
        "GOLDMAN": ["高盛", "goldman", "gs"], "BOFA": ["美銀", "美林", "bofa", "merrill"],
        "MACQUARIE": ["麥格理", "macquarie", "mq"], "CITI": ["花旗", "citi"],
        "UBS": ["瑞銀", "ubs"], "DAIWA": ["大和", "daiwa"], "NOMURA": ["野村", "nomura"],
        "MORGANSTANLEY": ["摩根士丹利", "morgan stanley", "ms"], "CLSA": ["里昂", "clsa"],
        "MEGA": ["兆豐"], "HUANAN": ["華南", "華南永昌"], "TAISHIN": ["台新"],
        "SINOPAC": ["永豐"], "FIRST": ["第一金"], "MASTERLINK": ["元富"],
        # 批428-T5:64 份實測補——【國泰證期研究部】/ CLST-6669 / GF-Thoughts /
        # JP-2330(冊有 jpm 沒有 jp)四家原本判不出券商
        "CATHAY": ["國泰", "國泰證期", "cathay"], "CLST": ["clst", "clsa taiwan"],
        "GF": ["廣發", "gf securities"], "SINOPAC_SEC": [],
    }
    # JP 單獨一詞只在**詞界**成立(見 _ascii_rx):"jp" 用 in 掃會命中 "jpy",
    # 這是主題詞冊 N1 踩過的同一個坑,不在券商冊再踩一次(批428-T5)。
    BROKER_ASCII_EXTRA = {"JPMORGAN": ["jp"], "GF": ["gf"], "CLST": ["clst"]}
    # 機構後綴:去掉之後**等於**券商別名才算券商(批428-T4)。
    # 「中信金」去不掉任何後綴,「中信金」≠「中信」→ 不是券商,是股票名 2891。
    BROKER_SUFFIX = ("證券投顧", "投顧", "投信", "證券", "證期", "期貨",
                     "研究部", "研究處", "海外商品部", "自營部", "顧問")
    RATING = {
        "BUY": ["買進", "強力買進", "加碼", "逢低加碼", "buy", "outperform",
                "overweight", "strong buy"],
        "HOLD": ["中立", "持有", "區間", "區間操作", "neutral", "hold",
                 "market perform", "equal-weight", "equalweight"],
        "SELL": ["賣出", "減碼", "sell", "underperform", "underweight", "reduce"],
        "ADD": ["逢低", "accumulate", "add"],
        "NOT_RATED": ["未評等", "無評等", "not rated", "nr", "n/r"],
    }

    def __init__(self, extra_broker=None, extra_rating=None):
        self.b = {k: set(x.lower() for x in v) for k, v in self.BROKER.items()}
        self.r = {k: set(x.lower() for x in v) for k, v in self.RATING.items()}
        for k, v in (extra_broker or {}).items():
            self.b.setdefault(k, set()).update(x.lower() for x in v)
        for k, v in (extra_rating or {}).items():
            self.r.setdefault(k, set()).update(x.lower() for x in v)

    @classmethod
    def broker_of_token(cls, tok):
        """不建實例就能問「這個 token 是不是券商」(批427-O:name_hint 要用,
        而 TickerFilename 手上沒有 BrokerRatingDict 實例)。

        批428-T4 **改嚴**:原本是「token 含券商別名就算券商」,於是
        「中信金」(2891 中信金控)因為含「中信」被當成 CTBC 濾掉,
        名稱提示落到後面的分析師「施志鴻」→ 判 MISMATCH = **自己造一盞假紅**。
        現在要 token 去掉機構後綴(證券/投顧/投信/期貨/證期/研究部…)後
        **等於**別名才算券商:
          凱基投顧 → 凱基 ✓   兆豐證券 → 兆豐 ✓   國泰證期研究部 → 國泰 ✓
          中信金 → 中信金 ≠ 中信 ✗(正確:它是股票名)
        """
        raw = unicodedata.normalize("NFKC", str(tok or "")).strip()
        if not raw:
            return None
        cands = {raw, raw.lower()}
        cut = raw
        for _ in range(3):                      # 可能疊兩層:國泰證期研究部
            for sfx in cls.BROKER_SUFFIX:
                if cut.endswith(sfx) and len(cut) > len(sfx):
                    cut = cut[:-len(sfx)]
                    break
            else:
                break
        cands |= {cut, cut.lower()}
        for canon, al in cls.BROKER.items():
            if any(a.lower() in {c.lower() for c in cands} for a in al):
                return canon
        for canon, al in cls.BROKER_ASCII_EXTRA.items():
            if raw.lower() in [a.lower() for a in al]:
                return canon
        return None

    @classmethod
    def is_rating_token(cls, tok):
        """token 整個就是評等詞?(批428-T4:晶心科(6533,N,中立) 的「中立」
        被當成公司名去對帳 → MISMATCH 假紅。評等不是公司名。)"""
        t = unicodedata.normalize("NFKC", str(tok or "")).strip().lower()
        if not t:
            return False
        return any(t == a.lower() for al in cls.RATING.values() for a in al)

    @staticmethod
    def _ascii_rx(alias):
        """ASCII 別名走詞界(批428-T5)。"gs"/"ms"/"jp" 用 in 掃會命中
        "gsm"/"msci"/"jpy";中文別名沒有詞界問題,照樣用 in。"""
        return re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", re.I)

    # 批428-V1:台灣的金控幾乎全是券商母公司——元大2885 富邦2881 國泰2882
    # 中信2891 統一1216 永豐2890 第一金2892 兆豐2886 台新2887 華南2880 凱基2883。
    # 在**整篇報告文字**上掃中文券商別名,命中的極可能是內文提到的**股票**,
    # 不是發文券商。實測:凱基投顧_2891 中信金 → 頁面券商判成 CTBC(內文的「中信金」)、
    # GS-1590 → KGI、華南投顧-2762 → TAISHIN,再拿去跟檔名券商比 → 一整排假紅。
    # 故頁面文字一律走 strict:中文別名**必須**後接機構詞才算券商;
    # ASCII 只認撞不到台股公司名的長名(gs/ms/jp 這種兩字縮寫在全文裡太危險)。
    INST_WORD = ("證券", "投顧", "投信", "證期", "期貨", "研究部", "研究處",
                 "投資顧問", "國際", "綜合證券")
    # 批428-V1b 實測:把 "capital" 放進來,Daiwa-1319 的頁面券商判成 CAPITAL(群益)。
    # 因為 Daiwa 的全名就是 **Daiwa Capital Markets**,而 capital 又是英文常用字
    # (capital expenditure / working capital)。券商英文別名只要撞到普通英文字,
    # 詞界也救不了——只能整個不收,或要求它帶機構詞。這和 N1 主題詞冊、T5 券商冊
    # 是同一課:**別名愈短愈常見,愈不能單獨採信**。
    STRICT_EN = ("goldman", "goldman sachs", "morgan stanley", "j.p. morgan",
                 "jpmorgan", "ubs", "citigroup", "daiwa", "nomura",
                 "macquarie", "clsa", "clst", "merrill", "hsbc", "kgieworld",
                 "yuanta", "fubon", "pscnet", "ctbc", "sinopac",
                 "capital securities", "cathay securities")

    def broker_normalize(self, s, strict=False):
        if not s:
            return None
        low = s.lower()
        if strict:
            for canon, al in self.b.items():
                for a in al:
                    if a.isascii():
                        if a in self.STRICT_EN and self._ascii_rx(a).search(low):
                            return canon
                    else:
                        rx = re.compile(re.escape(a) + r"\s*(?:" +
                                        "|".join(self.INST_WORD) + r")")
                        if rx.search(s):
                            return canon
            return None
        for canon, al in self.b.items():
            for a in al:
                if a.isascii():
                    if self._ascii_rx(a).search(low):
                        return canon
                elif a in low:
                    return canon
        for canon, al in self.BROKER_ASCII_EXTRA.items():
            if any(self._ascii_rx(a).search(low) for a in al):
                return canon
        return None

    def rating_normalize(self, s):
        if not s:
            return None
        low = s.lower()
        for canon, al in self.r.items():
            if any(re.search(r"\b" + re.escape(a) + r"\b", low) or a in low for a in al):
                return canon
        return None

    def validate_rating(self, s):
        c = self.rating_normalize(s)
        return {"raw": s, "canonical": c, "in_dict": c is not None}


class FieldValidation:
    _TEL = re.compile(r"(?:\+?886[-\s]?|\(0\d\)\s?|0)\d(?:[-\s]?\d){7,9}")
    # 批426-F:v0101 只認 NT$ 與 目標價,GS/MS 的 "Price Target 650"、"PT 78"
    # 全部漏抽(實測皆回 None)。加寬到與 VRN_ENG073 TP_RX 同一組觸發詞。
    # 批430-Y1:觸發詞後面若先遇到「潛在上漲空間/上漲空間/報酬率」等詞,
    # 那一段講的是**幅度**不是價格。用 [^\d\-]{0,20} 跨過去會直接撈到百分比。
    _TP_DECOY = re.compile(r"潛在上漲|上漲空間|下跌空間|報酬率|殖利率|漲幅|跌幅")
    _TP = re.compile(
        r"(?:Target\s*price|Price\s*Target|\bPT\b|目標價)"
        r"[^\d\-]{0,20}(?:NT\$|NT\s?\$|新台幣)?\s*([0-9][0-9,]*\.?\d*)", re.I)
    _TP_BARE = re.compile(r"(?:NT\$|NT\s?\$)\s*([0-9][0-9,]*\.?\d*)", re.I)

    def __init__(self, brd=None, price=None):
        self.brd = brd or BrokerRatingDict()
        self.price = price or PriceAdjustment()

    def extract_tel(self, text):
        out = []
        for m in self._TEL.finditer(text or ""):
            t = m.group(0).strip()
            if 8 <= len(re.sub(r"\D", "", t)) <= 12:
                out.append(t)
        return out

    def validate_email(self, email, broker_canon=None):
        m = re.match(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)$", email or "")
        if not m:
            return {"email": email, "valid": False, "broker_match": None}
        domain = m.group(2)
        dom_broker = self.brd.broker_normalize(domain)
        return {"email": email, "valid": True, "domain": domain,
                "domain_broker": dom_broker,
                "broker_match": (broker_canon is None) or (dom_broker == broker_canon)}

    # 批429-W1:「公司名(代號)」——括號內緊接中文名的數字是代號不是價格
    _PAREN_CODE = re.compile(r"[\u4e00-\u9fff][\s]*[（(][\s]*$")
    # 台股目標價的合理帶(批429-W2;批433-AB2 下界 1→5)。
    # 券商報告給出低於 5 元的目標價極罕見——那個價位是全額交割股,
    # 而那種股票不會有目標價報告。中信金 TP=1.0、Daiwa-3653 TP=2.0
    # 都落在舊帶 [1,5000] 內所以連黃燈都沒有。
    # 這是**提醒不是判死**:低於 5 元的目標價確實存在,所以給黃燈要人看一眼。
    TP_LO, TP_HI = 5.0, 5000.0
    #: 批437-A1 自洽仲裁加分。要壓得過「觸發詞(200)對裸 NT$(100)」的來源落差,
    #: 才能讓文內自洽真的當家;265(觸發詞+幣+小) vs 165+150=315。
    SELF_ARB = 150

    _UPSIDE = re.compile(
        r"(?:潛在上漲空間|上漲空間|下跌空間|upside|downside)"
        r"[^0-9\-+]{0,12}([+\-]?\d+(?:\.\d+)?)\s*[%％]", re.I)
    #: 批437-A1b:凱基/中信的表頭把單位寫在括號裡——「上漲空間 (%)\n13.7」,
    #: % 在數字**之前**。舊式要求 % 在數字之後,於是中信金的 13.7 一個都抓不到,
    #: 自洽仲裁就無從發動。這不是加寬,是原本就漏掉的另一種寫法。
    _UPSIDE_UNIT = re.compile(
        r"(?:潛在上漲空間|上漲空間|下跌空間|upside|downside|potential)"
        r"\s*[(（]?\s*[%％]\s*[)）]?[^0-9\-+]{0,8}([+\-]?\d+(?:\.\d+)?)", re.I)
    #: 報告自陳的現價(報告日原始價 raw,不是復權價)。強標在前、弱標在後——
    #: 「股價」太弱,志強-KY 的「目前評價位於**股價**10-11x」講的是本益比。
    _CLOSE_STRONG = re.compile(
        r"(?:收盤價|最新收盤|現價|Last\s*close|Closing\s*price|Share\s*price|Price\s*as\s*of)"
        r"[^\d\-]{0,24}(?:NT\$|NT\s?\$|TWD|新台幣)?\s*([0-9][0-9,]*\.?\d*)", re.I)
    _CLOSE_WEAK = re.compile(r"股價|收盤")
    #: 標籤與數字之間常常卡著一個日期——「收盤價 **May 19** (NT$) 55.40」。
    #: 用 [^\d]{0,24} 去跨會被 19 攔住,於是抓到 19 當收盤價(批437 自審實測)。
    #: 先把窗裡的日期樣式挖掉,再抓第一個數字。
    _DATEISH = re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*\d{1,2}\b"
        r"|\b\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b"
        r"|\d{4}\s*[/.\-年]\s*\d{1,2}\s*[/.\-月]\s*\d{1,2}\s*日?"
        r"|\b\d{1,2}\s*/\s*\d{1,2}\b", re.I)
    _NUM = re.compile(r"([0-9][0-9,]*\.?\d*)")
    _NOT_PRICE_TAIL = re.compile(r"\s*(?:[xX倍]|%|％|ppts?|bn|mn|tn|億|兆|百萬|千元)", re.I)
    #: 批437-A2:四條剔除律,全部來自庫內第二取字的實據
    _FROM = re.compile(r"\b(?:from|自|由)\s*(?:NT\s?\$|TWD|新台幣)?\s*$", re.I)
    _HILO = re.compile(r"hi\s*/\s*lo|52[-\s]?week|52\s*週|最高/最低|高低", re.I)
    _NA_TP = re.compile(r"\bn\.?\s?a\.?\b|\bN/A\b|not\s+rated|未評等|不評等|無評等", re.I)
    _MONTH = re.compile(r"\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
                        r"[a-z]*\b", re.I)
    _PER_TAIL = re.compile(r"\s*[-~–—]?\s*[0-9.]*\s*[xX倍]")

    #: 收盤價標籤(強)。弱標 `股價` 另走,因為它常常指本益比的「股價 10-11x」。
    _CLOSE_LABEL = re.compile(
        r"收盤價|最新收盤|現價|Last\s*close|Closing\s*price|Share\s*price|Price\s*as\s*of",
        re.I)

    def doc_close(self, text):
        """報告自陳的現價/收盤價。批437-A1:自洽仲裁的支點。
        **這是報告日的原始價(raw)**,與 VDF 側的復權價差一個除權息因子,
        所以它只用在文內,不跨到庫側去比(批431 律)。

        作法:找標籤 → 取其後 48 字的窗 → **先把日期樣式挖掉** → 抓第一個數字。
        先挖日期是必要的,不是保險:中信金寫「維持收盤價 May 19 (NT$) 55.40」,
        不挖就抓到 19(批437 自審實測,差點讓仲裁拿錯支點)。"""
        t = text or ""
        for rx in (self._CLOSE_LABEL, self._CLOSE_WEAK):
            for m in rx.finditer(t):
                win = self._DATEISH.sub(" ", t[m.end():m.end() + 48])
                nm = self._NUM.search(win)
                if not nm:
                    continue
                if self._NOT_PRICE_TAIL.match(win[nm.end():nm.end() + 8]) or \
                        self._PER_TAIL.match(win[nm.end():nm.end() + 8]):
                    continue          # 「股價10-11x」是本益比;「+3.3ppts」是幅度
                try:
                    v = float(nm.group(1).replace(",", ""))
                except ValueError:
                    continue
                if self.TP_LO <= v <= self.TP_HI:
                    return v
        return None

    #: 批437-A1c:外資報告寫成「12M price target NT$4,200.00±% **potential +27%**」。
    #: potential 是個普通英文字(growth potential…),所以這一式**強制要有正負號**
    #: ——「potential to grow 20%」沒有號,不會誤中;「potential +27%」才算。
    _UPSIDE_POT = re.compile(r"potential[^0-9+\-]{0,4}([+\-]\d+(?:\.\d+)?)\s*[%％]", re.I)

    def stated_upside(self, text):
        """三種寫法都要認:
             「上漲空間23%」        (標準)
             「上漲空間 (%) 13.7」  (凱基/中信把單位寫在括號裡,% 在數字**之前**)
             「potential +27%」     (外資;強制要有正負號才算)"""
        v = self.extract_upside(text)
        if v is not None:
            return v
        for rx in (self._UPSIDE_UNIT, self._UPSIDE_POT):
            m = rx.search(text or "")
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    continue
        return None

    def extract_upside(self, text):
        """報告自陳的上漲空間(%)。批431-Z:它與目標價互相隱含一個現價。"""
        m = self._UPSIDE.search(text or "")
        if not m:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None

    def implied_price(self, tp, upside_pct):
        """隱含價 = TP ÷ (1 + 上漲空間%)。兩者皆在同一頁,不靠庫不靠網。

        **這是報告日的原始價(raw),不是復權價(adj),也不是今天的價。**
        操作員批431 令:「因為過了除權息所有股價資料都用 adj 價格」——
        VDF 側一律是復權價,而報告寫的收盤價是當日原始價。
        兩者中間差一個除權息因子,**不可直接相比**;要比必須先經
        VRN_ENG080 的除權息調整(批386/425)。這裡只做文內自洽,
        不跨到庫側去比——跨過去而不調整,就是拿兩把不同的尺量同一件事。
        """
        if tp is None or upside_pct is None:
            return None
        denom = 1.0 + upside_pct / 100.0
        if denom <= 0:
            return None
        return round(tp / denom, 2)

    def tp_candidates(self, text, ticker=None):
        """回候選清單(已評分排序)。批429-W1:v0105 取**第一個**命中就回,
        於是「泓德能源(6873)」的 TP 抽成 6873——代號回音。真檔 64 份至少 4 份中招。
        改成先收全部候選、逐一講清楚為何留為何剔,再排序。"""
        t = text or ""
        cands = []
        # 批429-W1 自審:初版把裸 NT$ 的底分(120)排在觸發詞(100)之上,結果
        # 文中任何一個 NT$ 都壓過真正的「目標價 145」——志強-KY 145→125、
        # GS-2317 844→2.4、儒鴻 367→1.0,**比不修還爛**。
        # 「目標價」旁邊的數字是強證據;NT$ 在報告裡到處都是,是弱證據。
        # 來源權重必須壓過貨幣加分,不能讓加分翻轉來源。
        for rx, src, base in ((self._TP, "觸發詞", 200), (self._TP_BARE, "NT$", 100)):
            for m in rx.finditer(t):
                raw = m.group(1)
                try:
                    val = float(raw.replace(",", ""))
                except ValueError:
                    continue
                head = t[max(0, m.start(1) - 12):m.start(1)]
                # 窗要夠寬:實測「逢低買進 $145 前次 投資建議 2025.08.06: 目標價125 元」
                # 裡的「前次」距離觸發詞約 20 字,14 字的窗看不到它(批429-W1b)
                lead = t[max(0, m.start(0) - 28):m.start(0)]      # 觸發詞之前
                tail = t[m.end(1):m.end(1) + 12]                  # 數字之後
                whole = m.group(0)
                gap = t[m.end(0) - len(m.group(1)) - 20:m.start(1)]
                # 觸發詞與數字之間的那一段原文(批437-A2c 判 n.a. 用;
                # 用 whole 切比重算位移安全——whole 就是這一次命中的全文)
                gap_txt = whole[:whole.rfind(raw)] if raw in whole else whole
                cur = bool(re.search(r"NT\s?\$|新台幣|元", whole + t[m.end(1):m.end(1) + 4]))
                dec = "." in raw
                rej, rej_code = "", ""
                if ticker and raw.replace(",", "") == str(ticker):
                    rej = f"等於本檔代號 {ticker}=代號回音"
                elif self._PAREN_CODE.search(head):
                    rej = "括號內緊接中文公司名=代號不是價格"
                elif re.fullmatch(r"\d{8}", raw) and 19000101 <= val <= 21001231:
                    rej = "八碼日期形狀"
                elif (re.fullmatch(r"\d{4}", raw) and 1990 <= val <= 2100
                      and not cur and not dec):
                    rej = "四碼年份且無貨幣符號無小數"
                elif self._TP_DECOY.search(whole[:whole.find(raw)] if raw in whole else ""):
                    rej = "觸發詞與數字之間夾著「上漲空間/報酬率」=講幅度不是價格"
                elif re.match(r"\s*(?:%|％|個百分點|ppts?|pp\b)", tail):
                    # 批430-Y1 工作站實錄:志強-KY 抽到 TP=23.0,而報告寫的是
                    # 「潛在上漲空間**23%**」——抽到的是百分比不是價格。
                    # 泓德能源 22.7、神達 41.9 同型(上漲空間/報酬率)。
                    rej = f"數字後接「{tail.strip()[:4]}」=百分比不是股價"
                elif re.match(r"\s*(?:[xX倍]\b|[xX]\s*(?:20\d\d|PER|EPS))", tail):
                    # 「13x 2026(F)PER」的 13 是本益比倍數,不是目標價
                    rej = f"數字後接「{tail.strip()[:6]}」=倍數(本益比)不是股價"
                elif re.search(r"(?:bn|mn|tn|trillion|billion|million|k)\b",
                               tail, re.I) or re.match(r"\s*[億兆]|\s*百萬|\s*千元", tail):
                    # 批429-W1b 實測:GS-2317 抽到 NT$2.4**trillion**、
                    # MS-Thermal 抽到 NT$48.5**bn** 與 NT$17,382**mn**——那是**營收**,
                    # 不是目標價。裸 NT$ 車道在外資報告裡撈到的多半是財務數字。
                    rej = f"數字後接量級後綴「{tail.strip()[:8]}」=營收/金額不是股價"
                elif re.search(r"前次|原目標|舊目標|previous|prior\s+(?:tp|pt|target)",
                               lead, re.I):
                    # 批429-W1b 實測:志強-KY 的 125 是「**前次** 投資建議
                    # 2025.08.06: 目標價125 元」,現在的目標價是 145。
                    # 前次目標價是歷史,拿它當現值就是把舊資訊當新資訊。
                    rej = f"前綴「{lead.strip()[-6:]}」=前次目標價,非本次"
                elif self._FROM.search(head):
                    # 批437-A2a 實據 CLST-6669:「raise our TP **from** NT$3,600
                    # **to** NT$4,200」——from 後面那個是**前次**目標價。
                    # 與「前次/previous」同一族,只是英文報告改用 from…to 寫。
                    rej = "前綴「from」=調整前的舊目標價(from A to B 的 A)"
                elif self._HILO.search(lead + head) or re.match(r"\s*/\s*[0-9]", tail):
                    # 批437-A2b 實據 CLST-6669:「12M **hi/lo** NT$3,425.00/1,570.00」
                    # ——那是 52 週高低,不是目標價;斜線後緊接另一個數字=區間。
                    rej = "「hi/lo」或斜線接數字=52 週高低區間,不是目標價"
                elif src == "觸發詞" and self._NA_TP.search(gap_txt):
                    # 批437-A2c 實據 Daiwa-3653:報告白紙黑字寫
                    # 「Target price: **n.a.**」,而 v0113 跨過 n.a. 撈到後面
                    # 「Share price (**2** Oct)」的 2,於是 TP=2.0 還掛了 M 級。
                    # 觸發詞後面明寫 n.a./未評等 ⇒ 這份報告就是沒有目標價,
                    # 不得再往後撈——往後撈到的一定是別的欄位。
                    rej = "觸發詞後緊接「n.a./未評等」=本報告未給目標價,不得再往後撈"
                    rej_code = "TP_DECLARED_NA"
                elif self._MONTH.match(tail):
                    # 批437-A2d:「(2 Oct)」「(19 May)」——數字後接月份縮寫是日期
                    rej = f"數字後接月份「{tail.strip()[:5]}」=日期不是價格"
                cands.append({"value": val, "raw": raw, "src": src, "pos": m.start(1),
                              "currency": cur, "decimal": dec, "reject": rej,
                              "rej_code": rej_code,
                              # 批433-AB1:合理帶**壓過**貨幣記號。
                              # trace 實證:119,715 只因為多一個「元」就贏了 78,
                              # 但六位數帶千分位的數字不是股價,是營收/市值。
                              # 批429 修過一次排序(來源 > 貨幣),這是同一課的第二層。
                              "score": (base + (40 if self.TP_LO <= val <= self.TP_HI
                                                else -60)
                                        + (20 if cur else 0) + (5 if dec else 0)
                                        - m.start(1) / 100000.0)})
        # ── 批437-A1:文內自洽**仲裁** ──────────────────────────────
        # 批431 造了自洽,但只拿來「驗證」——選完才問對不對。真正能決勝的用法
        # 是**仲裁**:報告自陳上漲空間時,目標價 ÷ (1+空間) 必須等於同頁的現價。
        # 這條訊號比觸發詞強,也比貨幣記號強——批429(來源>貨幣)、
        # 批433(合理帶>貨幣)之後,這是同一課的第三層:**自洽 > 觸發詞**。
        #   CLST-6669  4,200÷1.27 = 3,307 ≈ 同頁 3,300;文中明寫 potential +27%
        #   中信金      63÷1.137  = 55.41 ≈ 同頁收盤價 55.40;文中寫 上漲空間 13.7
        #   志強-KY    145÷1.23   = 117.89 ≈ 報告原文收盤價 118.00
        up = self.stated_upside(t)
        if up is not None:
            close = self.doc_close(t)
            alive = [c["value"] for c in cands if not c["reject"]]
            for c in cands:
                if c["reject"]:
                    continue
                imp = self.implied_price(c["value"], up)
                if imp is None:
                    continue
                why = ""
                if close and abs(imp - close) <= max(0.02 * close, 0.01):
                    why = f"÷(1+{up}%)={imp}≈自陳收盤價 {close}"
                else:
                    near = [v for v in alive
                            if v != c["value"] and abs(imp - v) <= max(0.02 * v, 0.01)]
                    if near:
                        why = f"÷(1+{up}%)={imp}≈同頁候選 {near[0]}(現價)"
                if why:
                    c["score"] += self.SELF_ARB
                    c["arb"] = why
        cands.sort(key=lambda c: -c["score"])
        return cands

    @staticmethod
    def tp_grade(best, keep):
        """證據等級 V/M/P。移植自 via-vdf-vrn 的 src/lib/via/fin-audit.ts:
        「一列必須是原子事實。**P 級不得掛綠**」(批432)。

        我這邊原本只有「有值/沒值」,沒人問它**證據多強**,於是
        中信金 TP=1.0、Daiwa-3653 TP=2.0 這種孤證照樣掛 PASS。
          V 已驗:觸發詞車道 **且** 帶貨幣記號(NT$/元/新台幣)——最強
          M 提及:觸發詞車道但無貨幣記號——中等
          P 推定:只有裸 NT$ 車道撈到,沒有任何觸發詞——最弱,**不得掛綠**
        佐證與衝突都要算進來(批432 自審:初版只算衝突不算佐證,於是志強-KY 的 145
        被**三個候選同時命中**、又被文內自洽確認,卻只給 M——同值多次命中是佐證,
        不是中性。只罰不賞的分級會把對的東西一起壓低,那也是一種不誠實):
          同值多次命中          → 升一級
          不同值互相打架        → 降一級(兩者同時發生:先賞後罰,淨值為零)
        """
        if best is None:
            return "", ""
        vals = {c["value"] for c in keep}
        same_n = sum(1 for c in keep if c["value"] == best["value"])
        g = "V" if (best["src"] == "觸發詞" and best["currency"]) else (
            "M" if best["src"] == "觸發詞" else "P")
        why = {"V": "觸發詞命中且帶貨幣記號", "M": "觸發詞命中但無貨幣記號",
               "P": "只有裸 NT$ 撈到,無觸發詞佐證"}[g]
        up, down = {"P": "M", "M": "V", "V": "V"}, {"V": "M", "M": "P", "P": "P"}
        if same_n >= 2:
            g = up[g]
            why += f";同值命中 {same_n} 次=互相佐證,升一級"
        if len(vals) > 1:
            g = down[g]
            why += f";另有 {len(vals)} 個不同存活候選{sorted(vals)}打架,降一級"
        if best.get("arb"):
            # 批437-A1:文內自洽是**這一頁自己**給出的交叉驗算,不是外部推測。
            # 它比同值多次命中更強——同值命中只證明抽得一致,自洽證明算得通。
            g = up[g]
            why += f";文內自洽 {best['arb']},升一級"
        return g, why

    def extract_target_price(self, text, ticker=None, want_detail=False):
        cands = self.tp_candidates(text, ticker)
        keep = [c for c in cands if not c["reject"]]
        best = keep[0] if keep else None
        if want_detail:
            g, why = self.tp_grade(best, keep)
            return (best["value"] if best else None), cands, g, why
        return best["value"] if best else None

    def validate_target_price(self, tp, per=None, eps=None, current=None,
                              fin=None, current_is_adjusted=True, arb=""):
        res = {"target_price": tp, "checks": []}
        if tp is None or tp <= 0:
            res["checks"].append({"name": "positive", "ok": False})
            res["verdict"] = "FAIL"
            res["tp_state"] = "NA"
            return res
        res["checks"].append({"name": "positive", "ok": True})
        # 批429-W2:TP 合理性閘(0.2–5.0)要**現價**才能判,而現價來自庫;
        # 庫不在,閘就睡著了——真檔實測 奇鋐 TP=1780、中信金 TP=1.0、
        # 健策 TP=2.0、MS-Thermal TP=17382 全部無人擋。
        # 這一道不需要現價:台股目標價的**幣別合理帶**。
        # 是合理性不是精準驗證,所以給黃並標明,不是紅也不是靜音。
        if not (FieldValidation.TP_LO <= tp <= FieldValidation.TP_HI):
            # 批437 自審:GS-2383 TP=6,000 超出帶,但文內自洽算得通
            # (6000÷1.32=4,545=報告同頁自陳的現價)——「抽錯欄」這個可能已被排除。
            # 那要不要就此轉綠?**不轉**。帶確實沒過,而且自洽排除的是抽錯欄,
            # 排除不了「這份報告以外幣計價」。自己把黃壓成綠就是假綠,
            # 批422 的教訓。所以燈照黃,但把仲裁結果寫進註記讓人一眼看得到。
            res["checks"].append({"name": "twd_band", "ok": False,
                                  "note": f"{tp} 不在台股目標價合理帶 "
                                          f"{FieldValidation.TP_LO}–{FieldValidation.TP_HI} 元"
                                          "(可能抽錯欄,或這份報告以外幣計價)"
                                          + (f";但文內自洽 {arb}=抽錯欄已排除,"
                                             "剩下的可能只有幣別,請人看一眼"
                                             if arb else "")})
            res["tp_range_suspect"] = True
        if per and eps and fin:
            mul = fin.multiply(tp, per, eps)
            res["checks"].append({"name": "TP=PER*EPS",
                                  "ok": mul["verdict"] in ("PASS", "PASS-SOFT", "N/A"),
                                  "detail": mul})
        # 批426-H:合理性閘進 checks(不是只擺著)——批422 的假綠就是閘抓到了下游不讀
        st, ratio = self.price.tp_sanity(tp, current)
        res["tp_state"], res["tp_ratio"] = st, (round(ratio, 4) if ratio else None)
        if st != "NA":
            res["checks"].append({"name": "tp_sanity", "ok": st == "OK",
                                  "state": st, "ratio": res["tp_ratio"],
                                  "band": [self.price.TP_SANITY_LO, self.price.TP_SANITY_HI]})
        if current:
            up = self.price.upside(tp, current, is_adjusted=current_is_adjusted)
            res["checks"].append({"name": "upside_sane",
                                  "ok": (up is not None and abs(up) <= 2.0),
                                  "upside": up,
                                  "why": "" if current_is_adjusted
                                         else "現價非復權=拒算(Adjusted 與原始不混用)"})
        res["verdict"] = "PASS" if all(c["ok"] for c in res["checks"]) else "WARN"
        return res


class CrossValidation:
    @staticmethod
    def four_way(filename_ticker, title_ticker, table_ticker=None, financials_ticker=None):
        vals = [("filename", filename_ticker), ("title", title_ticker),
                ("table", table_ticker), ("financials", financials_ticker)]
        present = [(k, v) for k, v in vals if v]
        agree = len({v for _, v in present}) <= 1
        return {"verdict": "PASS" if agree and present else ("FAIL" if present else "N/A"),
                "sources": dict(present)}

    @staticmethod
    def filename_vs_page(fn, page):
        out = {"fields": {}, "verdict": "PASS"}
        for key in ("ticker", "broker", "date"):
            a, b = fn.get(key), page.get(key)
            if a and b:
                ok = (a == b)
                out["fields"][key] = {"filename": a, "page": b, "match": ok}
                if not ok:
                    out["verdict"] = "FAIL"
            else:
                out["fields"][key] = {"filename": a, "page": b, "match": None}
        return out

    @staticmethod
    def zone_presence(info_zone_fields, body_zone_fields):
        return {"info_zone": {"has_data": bool(info_zone_fields),
                              "n": len(info_zone_fields or [])},
                "body_zone": {"has_data": bool(body_zone_fields),
                              "n": len(body_zone_fields or [])},
                "verdict": "PASS" if (info_zone_fields and body_zone_fields) else "WARN"}

    @staticmethod
    def historical_vs_source(report_vals, source_vals, tol=0.05):
        out = {"years": {}, "verdict": "PASS"}
        for y in sorted(set(report_vals) & set(source_vals)):
            rv, sv = report_vals[y], source_vals[y]
            if sv in (None, 0) or rv is None:
                out["years"][y] = {"report": rv, "source": sv, "match": None}
                continue
            err = abs((rv - sv) / sv)
            ok = err <= tol
            out["years"][y] = {"report": rv, "source": sv,
                               "rel_err": round(err, 4), "match": ok}
            if not ok:
                out["verdict"] = "FAIL"
        return out


# =====================================================================
# ORCHESTRATOR
# =====================================================================
class FirstPageEngine:
    def __init__(self, ssot_path=None, official_set=None, nlp_engine=None,
                 via_root=None, auto_hub=True):
        # 批428-T1:先起對帳器把代號冊取回來,TickerFilename 才有冊可對
        #(次序不可換:冊要在 tokenize 之前就位,否則 2026 又會被當代號)
        self.nr = NameReconciler(via_root=via_root)
        # 批435:ENG072 已用三法做完核對,去讀它,不再自己判第二次版面
        self.sc = SidecarBridge(via_root=via_root)
        self.ds = DocStructure(via_root=via_root)      # 批436 文件結構層
        self.tf = TickerFilename(ssot_path, official_set, roster=self.nr.code_roster())
        self.nr.tk2name = dict(self.tf.tk2name)
        self.layout = Layout()
        self.tg = TableGeometry()
        self.nlp = NLPRepair(nlp_engine, auto_hub=auto_hub, via_root=via_root)
        self.xval = XValBridge(via_root)
        self.fin = FinancialValidation(self.xval)
        self.price = PriceAdjustment()
        self.brd = BrokerRatingDict()
        self.fv = FieldValidation(self.brd, self.price)
        self.xv = CrossValidation()

    # ---- 規格①:單位冊與 MDL008 共用(零九頭龍) ----
    def to_million(self, value, unit="million"):
        um = getattr(self.xval.mdl008, "UNIT_MULT", None) if self.xval.mdl008 else None
        return to_million_2dp(value, unit, um)

    def _filename_fields(self, filename):
        p = self.tf.parse_filename(filename)
        ticker = p["tickers"][0] if p["tickers"] else None
        date = p["dates"][0] if p["dates"] else None
        broker = None
        for tok in p["cjk"] + p["latin"]:
            b = self.brd.broker_normalize(tok)
            if b:
                broker = b
                break
        return {"ticker": ticker, "broker": broker, "date": date,
                "name_hint": p.get("name_hint"), "parse": p}

    @staticmethod
    def aggregate_verdict(out):
        """批426-I:總判必須讀到**所有**子閘。
        批422 的假綠就是上游閘抓到了(ENG080 TP_SUSPECT)、下游判定不讀它,
        於是一份目標價只有股價 1/200 的報告被印成 DONE。
        這裡把每個子判定逐一列出來,任何一個 FAIL 就 FAIL,任何 WARN 就 WARN,
        並回 gates 讓呼叫端看得見是誰把燈拉下來的——不做沉默彙總。"""
        gates = {}
        for key, path in (("ticker_cross", ("cross_check", "verdict")),
                          ("filename_vs_page", ("xv_filename_vs_page", "verdict")),
                          ("zone_presence", ("xv_zone_presence", "verdict")),
                          ("target_price", ("target_price", "verdict")),
                          ("historical", ("xv_historical", "verdict"))):
            node = out.get(path[0])
            if isinstance(node, dict) and node.get(path[1]):
                gates[key] = node[path[1]]
        tp_state = (out.get("target_price") or {}).get("tp_state")
        if tp_state == "TP_SUSPECT":
            gates["tp_sanity"] = "FAIL"          # 不得被無聲吞掉
        if (out.get("target_price") or {}).get("tp_range_suspect"):
            gates["tp_twd_band"] = "WARN"        # 批429-W2:不需現價的幣別合理帶
        # 批432-AA2:P 級不得掛綠(移植 via-vdf-vrn fin-audit.ts 的分級律)。
        # 證據弱不等於值錯,但**不得以綠燈示人**——那是把「沒人反駁」當成「已驗證」。
        _g = out.get("tp_grade")
        # 批432-AA2b:文內自洽是**獨立的**佐證來源(目標價與上漲空間是兩個不同的數),
        # 過了就該升一級。分級講的是證據強度,而通過獨立交叉核對本身就是證據。
        # 批437 自審:v0113 在這裡**又**升了一級,而批437 的仲裁已經在 tp_grade()
        # 裡升過——同一件事算兩次,中信金 63.0 的說明長出兩句「升一級」。
        # 而且兩者強度天差地別:v0113 看的只是「隱含價落在 5–5000 帶內」,
        # 那是**沒有矛盾**,不是佐證;真正的佐證是隱含價**對上同頁自陳的收盤價**。
        # 拿「沒有矛盾」當「有證據」,就是批434 那個過度標記的反面——過度加分。
        if _g and out.get("implied_price_state") == "OK" \
                and not out.get("tp_arbitration"):
            out["tp_grade_why"] = (out.get("tp_grade_why") or "") + \
                ";隱含價在合理帶內(僅表示無矛盾,不足以升級)"
        if _g:
            # 批434-AC1:他們的律寫的是「**P 級**不得掛綠」——只講 P。
            # 我批432 移植時讓 M 也掛黃,於是 MS-2308 TP=1288、JP-2330 TP=1275
            # 這種乾淨抽取,只因為數字旁沒有「元」字就被拉黃;
            # 而英文報告本來就不寫「元」——拿貨幣記號當必要條件是中文報告偏見。
            # 等級仍原樣寫進 tp_grade 與矩陣,資訊不消失,只是不再拉燈。
            gates["tp_evidence"] = {"V": "PASS", "M": "PASS", "P": "WARN"}[_g]
            if _g == "P" and gates.get("target_price") == "PASS":
                gates["target_price"] = "WARN"
        # 批431-Z:文內自洽。有就查,沒有就不立閘(64 份裡只有 6 份同時有這兩個數)
        if out.get("implied_price_state") == "IMPLIED_SUSPECT":
            gates["tp_self_consistency"] = "FAIL"
        elif out.get("implied_price_state") == "OK":
            gates["tp_self_consistency"] = "PASS"
        # 批427-O:代號↔證券名稱對帳也是子閘,一樣不得被無聲吞掉。
        # 查不到官方名 = N/A(來源不可得≠沒問題),不是綠——批422 假綠的教訓。
        # 批428-V3:TP 缺席要分兩種,現在全部一律 FAIL 是把兩件事混為一談:
        #   文中**有**觸發詞卻抽不到數字 → 真的抽取失敗,FAIL
        #   文中**一個觸發詞都沒有**     → 這份報告本來就沒有目標價,WARN(請人看一眼)
        # 實測 GS-3706 / MQ-1560 / 三份華南 Memo:全文 grep 不到
        # Target price / Price Target / PT / 目標價 任何一個,引擎找了、真的沒有。
        # 把「沒有」講成「失敗」,錯誤矩陣就會被不是錯的東西灌滿,真的錯反而被淹掉。
        if (gates.get("target_price") == "FAIL"
                and (out.get("target_price") or {}).get("target_price") is None
                and not out.get("tp_trigger_seen")):
            gates["target_price"] = "WARN"
        # 批437-A2c:報告自己寫「Target price: n.a.」=第三種缺席。
        # v0113 在 Daiwa-3653/6278 兩份上是**假綠**——跨過 n.a. 抓到
        # 「Share price (**21** May)」的 21 當目標價還掛 PASS。擋下來是對的,
        # 但擋成 FAIL 就換成假紅了:報告明說沒有,引擎沒有抽錯。
        if (gates.get("target_price") == "FAIL"
                and (out.get("target_price") or {}).get("target_price") is None
                and out.get("tp_declared_na")):
            gates["target_price"] = "N/A_TP_DECLARED_NA"
        # 批428-V2:未評等(NR / 未評等 / Not Rated)的報告**本來就沒有目標價**。
        # 實測「瑞基(4171,NR_未評等)-CTBC251208」檔名自己寫著未評等,
        # 卻因為抽不到 TP 被判 FAIL——那不是抽錯,是它根本沒有。
        if (gates.get("target_price") == "FAIL"
                and (out.get("rating") or {}).get("canonical") == "NOT_RATED"
                and (out.get("target_price") or {}).get("target_price") is None):
            gates["target_price"] = "N/A_NOT_RATED"
        # 批435:兩個獨立工具對同一頁讀出不同的字,那不是「有點疑慮」,
        # 是下游拿到的字可能根本不是報告寫的——所以 DIVERGE 判紅不判黃。
        _tc = (out.get("text_consensus") or {}).get("state")
        if _tc:
            gates["text_consensus"] = {
                "AGREE": "PASS", "PARTIAL": "WARN", "DIVERGE": "FAIL",
                "BOTH_EMPTY": "N/A", "SINGLE_TOOL": "WARN",
                "NO_SIDECAR": "N/A_NO_SIDECAR"}.get(_tc, "N/A")
        nrv = (out.get("name_reconcile") or {}).get("verdict")
        if nrv:
            gates["name_match"] = {"MATCH": "PASS", "MISMATCH": "FAIL"}.get(nrv, "N/A")
        if out.get("text_state", "OK") == "NO_TEXT":
            # 檔名類的閘(代號/券商/名稱對帳)照常判——那正是 .docx 仍然有用的部分
            for k in ("target_price", "tp_sanity", "zone_presence",
                      "filename_vs_page", "historical"):
                if k in gates:
                    gates[k] = "N/A_NO_TEXT"
        kind = ((out.get("filename_parse") or {}).get("kind")) or ""
        if not TickerFilename.kind_expects_ticker(kind):
            # 批418/426-G:非個股沒有代號與目標價是**正常**,不因此判紅。
            # 批428-U 修:原本只降 FAIL/WARN,**PASS 原封不動**——於是
            # 「20251205兆豐晨會報告(二)-公司訪談摘要」抽到 TP=4441(晨會報告
            # 根本不該有目標價,4441 是文中某個數字被撈走)卻印成 target_price=PASS。
            # 沒有目標價的報告給出目標價的綠燈,是批422 假綠的同型。
            # 一律降 N/A_NON_STOCK,不分顏色——非個股的這些閘本來就無意義。
            # 批434-AC2:zone_presence 查的是「目標價/評等/券商」三件套有沒有
            # 出現在本文分句裡。晨報/海外/研討會本來就沒有這三件套,
            # 拿它來判等於問一份晨報「你的目標價段落呢」。與 target_price 同律。
            for k in ("ticker_cross", "target_price", "tp_sanity", "name_match",
                      "zone_presence"):
                if k in gates:
                    gates[k] = "N/A_NON_STOCK"
            # 但「抽到了不該有的東西」本身要講出來:不是紅,是一盞黃,
            # 意思是「這份非個股報告裡撈到一個目標價,請人看一眼」。
            if (out.get("target_price") or {}).get("target_price") is not None:
                gates["nonstock_tp_leak"] = "WARN"
        vals = [v for v in gates.values() if not str(v).startswith("N/A")]
        verdict = ("FAIL" if any(v == "FAIL" for v in vals)
                   else "WARN" if any(v in ("WARN", "PASS-SOFT", "PASS-RANGE") for v in vals)
                   else "PASS" if vals else "N/A")
        return {"verdict": verdict, "gates": gates, "kind": kind,
                "text_state": out.get("text_state", "OK"),
                "non_stock": not TickerFilename.kind_expects_ticker(kind)}

    def run(self, filename, chars=None, text=None, title_codes=None, table_chars=None,
            per=None, eps=None, current_price=None, current_is_adjusted=True,
            source_historical=None, report_historical=None,
            first_page_data=None, financial_page_data=None,
            allow_web_names=False):
        out = {"engine": ENGINE_NAME, "version": ENGINE_VERSION,
               "filename": filename,
               "governance": "append-only; raw+repaired coexist"}
        fnf = self._filename_fields(filename)
        out["filename_parse"] = fnf["parse"]
        out["filename_fields"] = {k: fnf[k]
                                  for k in ("ticker", "broker", "date", "name_hint")}
        # 批427-O:券商/代號/名稱三者各歸各位之後,拿代號去對官方證券名稱。
        # 線上階梯預設關(allow_web=False):網路要走一定是操作員自己開閘、
        # 自己下 --web-names,引擎不代設 VIA_NET_CONSENT、也不偷連。
        out["name_reconcile"] = self.nr.reconcile(
            fnf["ticker"], fnf["name_hint"], allow_web=allow_web_names)
        # 批428-R:純文字車道。操作員的 64 份真報告在庫裡有全文 .txt
        # (批245 收容語料),但沒有字元幾何——v0104 只吃幾何,一份都用不上。
        # 批435:sidecar 在就用**經過多工具核對的本文**;不在才退回自判。
        # 順序不可換——自判的版面沒經過核對,拿它當主、核對當輔就是本末倒置。
        ver = SidecarBridge.verified(self.sc.load(filename))
        out["text_consensus"] = {k: ver[k] for k in ("state", "ratio", "tools")}
        out["tables_verified"] = ver["tables"]
        if ver["state"] in ("AGREE", "PARTIAL", "DIVERGE") and ver["body"].strip():
            lay = {"company_name": "", "main_text": ver["body"],
                   "footer": ver["footer"], "lines": []}
            out["text_source"] = f"ENG072 sidecar({ver['state']};{'+'.join(ver['tools'])})"
        else:
            lay = (self.layout.classify(chars) if chars
                   else {"company_name": "", "main_text": (text or ""),
                         "footer": "", "lines": []})
            out["text_source"] = ("本引擎自判版面(未經多工具核對:"
                                  + (self.sc.why or ver["state"]) + ")")
        out["layout"] = {"company_name": lay["company_name"],
                         "footer_excluded": bool(lay["footer"])}
        title, body = lay["company_name"], lay["main_text"]
        full_text = (" ".join(l["text"] for l in lay.get("lines", []))
                     or (lay["footer"] + " " + body))
        # 批427b-Q:文字層在不在,必須讓總判看得見。
        # .docx / 掃描影像 PDF / 缺 PyMuPDF 時 chars=None,文字類的閘全都無料可判;
        # v0104 初版照樣把 target_price 判 FAIL ——**讀不到 ≠ 抽錯**,那是假紅。
        # 這與批422 假綠是同一枚硬幣的兩面:證據不可得時,燈要給 N/A 不是給顏色。
        # 三態不可併成二態:TEXT_ONLY 抽得到的東西遠多於 NO_TEXT
        # (TP/評等/券商/電話/分句全可抽,只是沒有版面幾何),
        # 把它併進 NO_TEXT 就是把 64 份真語料的證據丟掉(批428-R)。
        out["text_state"] = ("OK" if chars else
                             "TEXT_ONLY" if full_text.strip() else "NO_TEXT")
        out["ticker"] = self.tf.resolve(filename, title, body)
        # 批429-W3:產業報告提到 3017 奇鋐,**不會使它變成一份 3017 的報告**。
        # 真檔實測:晨會報告 代號=1163/4441、MS-Thermal 代號=3017、UBS-Asia 代號=8722
        # ——全是從內文撈的第一個四碼。非個股型別一律把它移到「內文提及」。
        if not TickerFilename.kind_expects_ticker(fnf["parse"]["kind"]):
            if out["ticker"].get("ticker"):
                out["ticker"]["mentioned"] = out["ticker"]["ticker"]
                out["ticker"]["ticker"] = None
                out["ticker"]["why"] = ("非個股報告:內文四碼移為「內文提及」"
                                        "——提到某檔股票不等於這是那檔的報告(批429-W3)")
        out["main_text_raw"] = body
        out["main_text_repaired"] = self.nlp.repair_text(body)
        out["nlp_route"] = self.nlp.route()          # 批426-B:走哪條看得見
        out["xval_bridge"] = self.xval.status()      # 正典在不在也看得見

        emails = self.tf.parse_email(full_text)
        out["emails"] = emails
        out["tel"] = self.fv.extract_tel(full_text)
        # 批428-V1:頁面文字走 strict(中文別名須後接機構詞),
        # 否則內文提到的金控股票名會冒充發文券商
        page_broker = self.brd.broker_normalize(full_text, strict=True)
        out["broker"] = page_broker
        out["rating"] = self.brd.validate_rating(full_text)
        tp, tp_cands, tp_grade, tp_grade_why = self.fv.extract_target_price(
            full_text, ticker=fnf["ticker"], want_detail=True)
        out["tp_candidates"] = tp_cands
        _tp_arb = next((c.get("arb") for c in (tp_cands or [])
                        if not c["reject"] and c.get("arb")), "")
        out["tp_arbitration"] = _tp_arb
        # 批437-A2c:報告白紙黑字寫「Target price: n.a.」——那不是抽不到,
        # 是它**明說沒有**。這是第三種缺席,與前兩種(無觸發詞=WARN、
        # 未評等=N/A)同族,不得判 FAIL,否則又是批434 那種自己造的紅。
        out["tp_declared_na"] = any(c.get("rej_code") == "TP_DECLARED_NA"
                                    for c in (tp_cands or []))
        out["tp_grade"] = tp_grade
        out["tp_grade_why"] = tp_grade_why
        # 批428-V3:觸發詞在不在,是「抽不到」與「本來就沒有」的分界
        # 批431-Z:文內自洽——目標價與上漲空間互相隱含一個現價
        _up = self.fv.stated_upside(full_text)     # 批437-A1b:兩種寫法都認
        _imp = self.fv.implied_price(tp, _up)
        out["upside_stated"] = _up
        out["implied_price"] = _imp
        if _imp is not None:
            ok = FieldValidation.TP_LO <= _imp <= FieldValidation.TP_HI
            out["implied_price_state"] = "OK" if ok else "IMPLIED_SUSPECT"
            out["implied_price_basis"] = "RAW_AT_REPORT_DATE"   # 批431:非復權、非今日
            out["implied_price_note"] = (
                f"報告自陳上漲空間 {_up}% + 目標價 {tp} ⇒ 隱含**報告日原始價** {_imp} 元"
                f"(raw,非復權;VDF 側為 adj,兩者差一個除權息因子,不可直接相比)"
                + ("" if ok else f"——不在台股合理帶 {FieldValidation.TP_LO}–"
                                 f"{FieldValidation.TP_HI},目標價與上漲空間至少一個抽錯"))
        out["tp_trigger_seen"] = bool(
            re.search(r"target\s*price|price\s*target|\bPT\b|目標價", full_text or "", re.I))
        out["target_price"] = self.fv.validate_target_price(
            tp, per=per, eps=eps, current=current_price, fin=self.fin,
            current_is_adjusted=current_is_adjusted, arb=_tp_arb)
        if emails:
            e0 = emails[0]["analyst_id"] + "@" + emails[0]["broker_domain"]
            out["email_validation"] = self.fv.validate_email(e0, page_broker)

        page_date = fnf["date"]
        out["xv_filename_vs_page"] = self.xv.filename_vs_page(
            fnf, {"ticker": out["ticker"]["ticker"] or None,
                  "broker": page_broker, "date": page_date})
        info_zone = [x for x in [tp, out["rating"]["canonical"], page_broker] if x]
        out["xv_zone_presence"] = self.xv.zone_presence(
            info_zone, self.nlp.split_sentences(body))
        if title_codes:
            out["cross_check"] = self.tf.cross_check(out["ticker"]["ticker"], **title_codes)
        if table_chars:
            tbl = self.tg.reconstruct(table_chars)
            if tbl["rows"]:
                tbl["period_header"] = self.tg.restore_period_header(tbl["rows"][0])
            out["table"] = tbl
        if source_historical and report_historical:
            out["xv_historical"] = self.xv.historical_vs_source(
                report_historical, source_historical)
        # 批426:TW02 三源交叉核對(正典在位才跑;缺席誠實 None)
        if first_page_data is not None and financial_page_data is not None:
            tw = self.xval.three_way(
                {"potential_tickers": fnf["parse"]["tickers"],
                 "dates": fnf["parse"]["dates"]},
                first_page_data, financial_page_data)
            out["xv_three_source"] = tw if tw is not None else {
                "skipped": True, "why": self.xval.status()["why"].get("tw02", "TW02 缺席")}
        # ── 批436:字體階層 → 接句 → 列化 → 表/圖還原 ──
        _sc = self.sc.load(filename)
        _els = ((_sc or {}).get("gle") or {}).get("elements") or []
        _bf = ((_sc or {}).get("gle") or {}).get("body_font")
        _has_tk = bool(fnf["ticker"])
        _tiered, _inapp = [], False
        if _els:
            for el in _els:
                head = str(el.get("head") or "").strip()
                if not head:
                    continue
                if DocStructure._APPENDIX.match(head):
                    _inapp = True
                _tiered.append((self.ds.tier_of(el.get("size"), el.get("bold"),
                                                _bf, head, _has_tk, _inapp), head))
            _tier_src = f"gle.elements({len(_els)} 塊,本文字級 {_bf})"
        else:
            # 批437-A3:沒有 gle 不代表沒有結構。SUP_MDL744 早就開通了
            # layout()/roles()(它自己的註解寫著「VRN 引擎直接消費的四道」),
            # 而 v0113 只消費了 text_processor() 一道——這是批435 那一課的第三次:
            # 能力已經造好,我沒接。角色層給不了字級,但給得了**本文/非本文**,
            # 所以頁尾、導覽、來源封裝可以被踢出本文,不再整份當 BODY。
            _roles = self.ds.role_tiers(body, self.nlp.hub)
            if _roles:
                _tiered, _tier_src = _roles["tiered"], _roles["why"]
                _inapp = _roles["in_appendix"]
            else:
                for ln in (body or "").splitlines():
                    if DocStructure._APPENDIX.match(ln.strip()):
                        _inapp = True
                    _tiered.append(("APPENDIX" if _inapp else "BODY", ln))
                _tier_src = ("無 gle.elements、NLP 角色層亦缺"
                             f"({self.ds.role_why or '未掛載'})"
                             "=退純文字弱啟發(字級/字重不可得,一律當本文)")
        _joined = self.ds.join_body(_tiered)
        out["doc_tier_source"] = _tier_src
        out["doc_rows"] = self.ds.rows(_joined, {
            "date": fnf["date"], "filename": filename, "broker": out.get("broker")
            or fnf["broker"]})
        out["doc_table"] = self.ds.restore_table(
            [t for tier, t in _tiered if tier not in ("FOOTER", "APPENDIX")])
        out["stmt_book"] = self.ds.stmt_why
        out["summary"] = self.aggregate_verdict(out)
        return out


# =====================================================================
# CLI(批426-J:真的接線;批425 一連四例都是「參數在、線沒接」)
# =====================================================================
def _argval(args, flag):
    if flag not in args:
        return None
    i = args.index(flag) + 1
    if i >= len(args) or args[i].startswith("--"):
        print(f"[旗標] {flag} 後面沒有值=忽略(誠實提示,不當作預設)")
        return None
    return args[i]


def _pdf_chars(path):
    """PyMuPDF 抽字元幾何;缺庫=誠實 None(不假裝抽到)。
    批427b-P3:冊上 extensions 含 .docx,但本引擎**只讀 PDF 文字層**。
    收 .docx 進來是對的(檔名層的代號/券商/型別/名稱對帳照樣做),
    但不能讓它走進 fitz 然後吐一句看不懂的例外——誠實講「只做檔名層」。"""
    if Path(path).suffix.lower() != ".pdf":
        return None, f"{Path(path).suffix or '(無副檔名)'} 非 PDF=只做檔名層(本引擎只讀 PDF 文字層)"
    try:
        import fitz
    except Exception:
        return None, "PyMuPDF(fitz)未安裝=無法取字元幾何"
    try:
        with fitz.open(str(path)) as doc:
            if not doc.page_count:
                return [], "空 PDF"
            pg = doc[0]
            chars = []
            for b in pg.get_text("dict")["blocks"]:
                for ln in b.get("lines", []):
                    for sp in ln.get("spans", []):
                        for ch in sp.get("text", ""):
                            chars.append({"text": ch, "top": sp["bbox"][1],
                                          "x0": sp["bbox"][0], "size": sp.get("size", 10),
                                          "fontname": sp.get("font", "")})
            return chars, ""
    except Exception as exc:
        return None, f"{type(exc).__name__}: {str(exc)[:90]}"


# =====================================================================
# 8c · 文件結構層(批436:操作員全規格)
#   一標題 · 一句話 · 一資料分類
#   欄位 REPORT DATE / FILENAME / BROKER / CATEGORY(表圖文) / TYPE
# =====================================================================
class DocStructure:
    """字體階層 → 斷句 → 列化 → 表/圖還原。

    操作員 批436 規格逐條:
      · 接斷句直到句號;**標題沒有句號**(字體較大或粗)→ 用階層判,不用句號判
      · 去空格 TRIM;表格內除了分隔符號,欄內資料也 TRIM
      · 股票名稱及代號 = 最大最粗
      · 文章主題(一句話,不含股票名稱及代號)= 最大最粗
      · 大標題 / 中標題 / 小標題 / 本文 / 頁尾不相關小字 / 報告後方附錄及其標題
      · 表:表號:說明 · 一兩個表頭(或許合併儲存格)· 表的資料來源
      · 表被誤判成文字時的還原:連續的時間(可能是表頭也可能是第一欄)、
        可對齊的數字;**表頭第一格空著就先填 item**,才容易還原
      · 圖:圖號:說明 · 圖中資料 · 圖來源
      · 財報表分類綁 SSOT(vrn_finlex STMT_ZH),缺的補同義字

    零九頭龍:字級/字重/分區**不自己再偵測一次**——吃 ENG072 sidecar 的
    gle.elements(批435 已接);沒有 gle 才退回用純文字的弱啟發並標明。
    """

    TIERS = ("TICKER_NAME", "SUBJECT", "H1", "H2", "H3", "BODY", "FOOTER", "APPENDIX")
    # 字級比(相對本文字級)。邊界寫在這裡,不散在判斷式裡。
    H1, H2, H3, FOOT = 1.60, 1.35, 1.15, 0.85
    _APPENDIX = re.compile(r"^\s*(?:附錄|附件|Appendix|Disclaimer|免責|重要聲明|"
                           r"法律聲明|Analyst Certification)", re.I)
    _END = "。．.!！?？;；"
    _TBL_NO = re.compile(r"^\s*(?:表|Table|Exhibit)\s*([0-9０-９一二三四五六七八九十]+)"
                         r"\s*[:：.、]?\s*(.*)$", re.I)
    _FIG_NO = re.compile(r"^\s*(?:圖|Figure|Fig|Chart)\s*([0-9０-９一二三四五六七八九十]+)"
                         r"\s*[:：.、]?\s*(.*)$", re.I)
    _SRC = re.compile(r"^\s*(?:資料來源|來源|Source|Sources)\s*[:：]?\s*(.*)$", re.I)
    # 期間樣式:連續出現 ≥3 個就是表頭或第一欄(批436 操作員指認)
    # 批437-A4 工作站實錄:裸民國年 `1[0-2]\d` 沒有邊界,於是
    # 「目標價**125** 元」被當成民國 125 年,一行湊到 3 個期間就被判成表頭,
    # 印出一張沒有資料列的假表。民國年單獨出現時本來就與價格**形狀相同**,
    # 分不開就不該猜——只認有上下文的兩種:「民國 114」與七碼日期 1141202。
    _PERIOD = re.compile(r"(?<![\d.])(?:20\d{2}|[1-4]Q\d{2}|\d{2}Q[1-4]|FY\d{2}|"
                         r"\d{4}[FEA]|1[0-2]\d[01]\d[0-3]\d|\d{1,2}/\d{2})(?![\d.])"
                         r"|民國\s*1[0-2]\d")
    # 財報表冊:綁 vrn_finlex 的 STMT_ZH;批436 補「評價分析」(冊上原本沒有)
    STMT_EXTRA = {"VALUATION": ("評價分析", "Valuation",
                                ["評價分析", "評價", "估值", "Valuation", "Valuation Analysis"])}

    def __init__(self, via_root=None):
        self.root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
        self.stmt, self.stmt_why = self._load_stmt()
        self.role_why = ""

    # ---- 財報表冊(綁 SSOT,缺的補) ----
    def _load_stmt(self):
        book = dict(self.STMT_EXTRA)
        hit = sorted((self.root / "functional modules" / "VRN")
                     .glob("vrn_finlex_v*.py")) if self.root else []
        if not hit:
            return book, "vrn_finlex_v*.py 未尋獲=只有本檔補的評價分析"
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("via_finlex_fpe", hit[-1])
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            base = dict(getattr(mod, "STMT_ZH", {}) or {})
            added = [k for k in book if k not in base]
            base.update({k: v for k, v in book.items() if k not in base})
            return base, (f"綁 {hit[-1].name}"
                          + (f";補同義字 {added}(冊上原本沒有)" if added else ""))
        except Exception as exc:
            return book, f"finlex 載入失敗 {type(exc).__name__}:{str(exc)[:50]}"

    def stmt_kind(self, line):
        """這一行是哪一張財報表?回 (鍵, 中文, 命中的同義字);不是則 (None,'','')。"""
        t = unicodedata.normalize("NFKC", line or "")
        for key, val in self.stmt.items():
            syns = val[2] if isinstance(val, (list, tuple)) and len(val) > 2 else [val]
            for sy in syns:
                if sy and sy.lower() in t.lower():
                    zh = val[0] if isinstance(val, (list, tuple)) else key
                    return key, zh, sy
        return None, "", ""

    # ---- 字體階層 ----
    def tier_of(self, size, bold, body_font, text, has_ticker, in_appendix):
        """字級+字重 → 階層。**股票名稱及代號與文章主題同為最大最粗**,
        用「這一行有沒有四碼代號/公司名」分開它們(批436 操作員規格)。"""
        if in_appendix:
            return "APPENDIX"
        bf = body_font or size or 1.0
        r = (size or bf) / bf
        if r < self.FOOT:
            return "FOOTER"
        if r >= self.H1 and bold:
            return "TICKER_NAME" if has_ticker else "SUBJECT"
        if r >= self.H1:
            return "H1"
        if r >= self.H2:
            return "H2"
        if r >= self.H3:
            return "H3"
        return "BODY"

    @staticmethod
    def is_title(tier):
        """標題沒有句號——所以標題不參與接句(批436)。"""
        return tier in ("TICKER_NAME", "SUBJECT", "H1", "H2", "H3")

    def join_body(self, lines):
        """接斷句直到句號。TRIM 後再接;標題自成一列不接。
        回 [(tier, 文字)];tier 由呼叫端在 lines 內先標好。"""
        out, buf = [], ""
        for tier, raw in lines:
            t = (raw or "").strip()
            if not t:
                continue
            if self.is_title(tier) or tier in ("FOOTER", "APPENDIX"):
                if buf:
                    out.append(("BODY", buf.strip()))
                    buf = ""
                out.append((tier, t))
                continue
            buf = (buf + " " + t).strip() if buf else t
            while buf and buf[-1] in self._END:
                out.append(("BODY", buf.strip()))
                buf = ""
                break
        if buf:
            out.append(("BODY", buf.strip()))
        return out

    # ---- 表/圖 ----
    def caption(self, line):
        """回 (kind, 編號, 說明);不是表圖題則 (None,'','')。"""
        m = self._TBL_NO.match(line or "")
        if m:
            return "表", m.group(1), m.group(2).strip()
        m = self._FIG_NO.match(line or "")
        if m:
            return "圖", m.group(1), m.group(2).strip()
        return None, "", ""

    def source_of(self, line):
        m = self._SRC.match(line or "")
        return m.group(1).strip() if m else ""

    def restore_table(self, lines):
        """把被誤判成文字的表格還原(批436 操作員指認的兩個訊號)。

        訊號一:一行裡連續出現 ≥3 個期間樣式(2024 2025F 2026F / 1Q25 2Q25…)
               ——那是**表頭**,也可能是**第一欄**。
        訊號二:一行裡有 ≥2 個用兩個以上空白隔開的數字——可對齊,就是資料列。
        **表頭第一格空著就先填 item**:少一格整列就對不齊,填了才還原得回來。
        回 {"header": [...], "rows": [[...]], "why": "..."};不是表則 header 為空。
        """
        hdr, rows, why = [], [], ""
        for raw in lines:
            t = (raw or "").strip()
            if not t:
                continue
            cells = [c.strip() for c in re.split(r"\s{2,}|\t|\|", t) if c.strip()]
            periods = self._PERIOD.findall(t)
            nums = re.findall(r"-?[\d,]+\.?\d*%?", t)
            if not hdr and len(periods) >= 3:
                hdr = cells
                # 表頭第一格若是期間(代表首欄標題整格空著)→ 補 item
                if hdr and self._PERIOD.fullmatch(hdr[0] or ""):
                    hdr = ["item"] + hdr
                    why = "表頭第一格空著(首格就是期間)→ 補 item 才對得齊欄位"
                continue
            if len(cells) >= 2 and len(nums) >= 2:
                rows.append(cells)
        if hdr and rows:
            w = max(len(hdr), max(len(r) for r in rows))
            hdr = hdr + [""] * (w - len(hdr))
            rows = [r + [""] * (w - len(r)) for r in rows]
            return {"header": hdr, "rows": rows,
                    "why": why or f"連續期間 ≥3 + 可對齊數字 ≥2 → 還原 {len(rows)} 列"}
        # 批437-A5 工作站實錄:v0113 印出「表格還原:無表格訊號」**同時**又印了
        # 一列表頭,自己打自己的臉。根因是 why 只在 hdr and rows 時才寫,
        # 而 header 照回不誤。一列表頭沒有任何資料列,那就不是表——
        # 與其回半張表讓下游自己猜,不如誠實說「只有表頭訊號」。
        if hdr:
            return {"header": [], "rows": [],
                    "why": f"有表頭訊號({len(hdr)} 格)但一列資料都沒有=不是表"}
        return {"header": [], "rows": [], "why": "無表格訊號"}

    # ---- 第二階層來源:NLP 角色層(批437-A3) ----
    ROLE_TIER = {"header_footer": "FOOTER", "source_wrapper": "FOOTER",
                 "navigation": "FOOTER", "advertisement": "FOOTER",
                 "metadata": "FOOTER", "blank": "FOOTER",
                 "primary_body": "BODY", "supporting_evidence": "BODY",
                 "code_evidence": "BODY", "uncertain": "BODY"}

    def role_tiers(self, body, hub):
        """用 SUP_MDL744 的 roles() 把每一列標成 BODY/FOOTER/APPENDIX。
        回 None 表示這條路走不通,並把**為何**留在 self.role_why——
        靜默退後備正是批426-B/批419e 修掉的那個病,不再犯第三次。

        誠實邊界:角色層看的是**語意**不是字級,所以它分得出
        「本文 vs 頁尾/導覽/來源封裝」,分不出「大標題 vs 中標題」。
        階層來源要照實寫成「角色層(無字級)」,不得冒充 gle 的字級階層。"""
        self.role_why = ""
        if hub is None:
            self.role_why = "SUP_MDL744 未掛載"
            return None
        try:
            r = hub.roles(body or "")
        except Exception as exc:
            self.role_why = f"roles() 例外 {type(exc).__name__}:{str(exc)[:60]}"
            return None
        recs = (r or {}).get("records") or []
        if not recs:
            self.role_why = f"roles() 回空(鍵={sorted((r or {}))[:4]})"
            return None
        tiered, inapp, kinds = [], False, {}
        for rec in recs:
            txt = str(rec.get("source_text") or "").strip()
            if not txt:
                continue
            if self._APPENDIX.match(txt):
                inapp = True
            role = str(rec.get("role") or "uncertain")
            tier = "APPENDIX" if inapp else self.ROLE_TIER.get(role, "BODY")
            kinds[role] = kinds.get(role, 0) + 1
            tiered.append((tier, txt))
        if not tiered:
            self.role_why = "roles() 有列但每一列都是空字串"
            return None
        top = ",".join(f"{k}×{v}" for k, v in
                       sorted(kinds.items(), key=lambda kv: -kv[1])[:3])
        return {"tiered": tiered, "in_appendix": inapp,
                "why": f"SUP_MDL744.roles({len(tiered)} 列;{top})"
                       "=角色層(語意;無字級,分得出本文/頁尾,分不出標題層級)"}

    # ---- 列化:一標題 一句話 一資料分類 ----
    def rows(self, tiered, meta):
        """回逐列 dict:REPORT_DATE / FILENAME / BROKER / CATEGORY / TYPE / TEXT。
        CATEGORY=表/圖/文(操作員規格);TYPE=字體階層。"""
        out, cur_cap = [], ("", "", "")
        for tier, t in tiered:
            kind, no, desc = self.caption(t)
            src = self.source_of(t)
            if kind:
                cur_cap = (kind, no, desc)
                cat = kind
            elif src:
                cat = cur_cap[0] or "文"
            else:
                cat = cur_cap[0] if cur_cap[0] and tier == "BODY" else "文"
            stmt_key, stmt_zh, stmt_hit = self.stmt_kind(t)
            out.append({
                "REPORT_DATE": meta.get("date") or "",
                "FILENAME": meta.get("filename") or "",
                "BROKER": meta.get("broker") or "",
                "CATEGORY": cat,
                "TYPE": tier,
                "TEXT": t.strip(),
                "CAPTION_NO": no or (cur_cap[1] if cat in ("表", "圖") else ""),
                "CAPTION_DESC": desc or (cur_cap[2] if cat in ("表", "圖") else ""),
                "SOURCE": src,
                "STMT": stmt_key or "", "STMT_ZH": stmt_zh, "STMT_HIT": stmt_hit,
            })
        return out


# =====================================================================
# 8b · SIDECAR 橋(批435):去讀 ENG072 已經做好的多工具核對結果
# =====================================================================
class SidecarBridge:
    """讀 VRN_ENG072 的 first_page_text sidecar。

    ENG072 v0107 早就用三法(fitz / pdfplumber+表格 / GenericLayoutEngine)
    加 NLP 句級修復做完了逐區 difflib 對照,而本引擎從 v0101 起自己又判一次版面,
    下游拿到的是**沒經過核對**的那一份。這座橋就是把那個重複接回去。

    零九頭龍:不重算版面、不重跑對照——只讀、只判「能不能信」。
    """

    REL = "VIA_Reports/first_page_text"
    AGREE, PARTIAL = 0.90, 0.60          # 與 ENG072 compare_zones 同門檻

    def __init__(self, via_root=None, explicit=None):
        self.dir = (Path(explicit) if explicit else
                    ((Path(via_root) if via_root
                      else _find_via_root(Path(__file__).parent) or Path("."))
                     / self.REL))
        self.why = "" if self.dir.is_dir() else f"sidecar 夾不在:{self.dir}"

    def load(self, filename):
        """回 sidecar dict;缺=None 並留因由(不假裝有)。"""
        if not self.dir.is_dir():
            return None
        stem = Path(filename).stem
        for cand in (self.dir / f"{stem}.json", self.dir / f"{Path(filename).name}.json"):
            if cand.exists():
                try:
                    return json.loads(cand.read_text(encoding="utf-8"))
                except Exception as exc:
                    self.why = f"sidecar 讀取失敗 {type(exc).__name__}:{str(exc)[:60]}"
                    return None
        self.why = f"此檔無 sidecar(ENG072 尚未跑過?):{stem}.json"
        return None

    @classmethod
    def verified(cls, sc):
        """回驗證後的本文與判定。

        **只回 compare 達標的本文**——兩法讀出不同的字時,回哪一份都是在猜,
        所以回 DIVERGE 讓呼叫端知道這一頁的字不可信,而不是挑一份給它。
        """
        if not sc:
            return {"state": "NO_SIDECAR", "body": "", "ratio": None,
                    "tools": [], "tables": [], "footer": "", "sentences": []}
        cmp_body = ((sc.get("compare") or {}).get("body") or {})
        ratio = cmp_body.get("ratio")
        verdict = str(cmp_body.get("verdict") or "")
        a = str(sc.get("body") or "")
        b = str(((sc.get("plumber") or {}).get("body")) or "")
        tools = [t for t, v in (("fitz", a), ("pdfplumber", b)) if v.strip()]
        if (sc.get("gle") or {}).get("available"):
            tools.append("GLE")
        if sc.get("sentences"):
            tools.append("NLP句級")
        state = ("AGREE" if verdict == "AGREE" or (ratio is not None and ratio >= cls.AGREE)
                 else "PARTIAL" if (ratio is not None and ratio >= cls.PARTIAL)
                 else "BOTH_EMPTY" if verdict == "BOTH_EMPTY"
                 else "DIVERGE" if ratio is not None
                 else "SINGLE_TOOL")
        if state in ("AGREE",):
            body = a or b
        elif state == "BOTH_EMPTY":
            body = ""
        else:
            body = a or b              # 仍給出來供人看,但 state 已標明不可信
        return {"state": state, "body": body, "ratio": ratio, "tools": tools,
                "tables": sc.get("tables") or [], "footer": str(sc.get("footer") or ""),
                "sentences": sc.get("sentences") or []}


# =====================================================================
# 9 · 四分頁矩陣報告(批428-S)
#   零 CDN、零 JS 框架:分頁用 <input type=radio> + CSS 同層選擇器,
#   離線雙擊即開。字級沿用 ENG072 房規(10.5px)再收一級——
#   操作員要的「小一點比較專業」是這個尺度,不是另立一套視覺。
# =====================================================================
class DbFacts:
    """庫側事實(唯讀)。四分頁的 ②③④ 要用到先前 ENG073/ENG074 的入庫成果。
    庫不可得 = 該分頁誠實印「庫不可得 + 為何」,**不留白讓人以為沒資料**。"""

    WANT = ("vrn_report_basic", "vrn_report_financial",
            "vrn_report_crosscheck", "vrn_report_metrics")

    def __init__(self, db=None, via_root=None):
        self.db = Path(db) if db else NameReconciler(via_root=via_root)._db
        self.why = ""
        self.data = {t: [] for t in self.WANT}
        self.cols = {t: [] for t in self.WANT}
        self._load()

    def _load(self):
        if not self.db or not Path(self.db).exists():
            self.why = f"庫不在:{self.db}"
            return
        try:
            import duckdb
        except Exception:
            self.why = "本環境無 duckdb"
            return
        con = None
        try:
            con = duckdb.connect(str(self.db), read_only=True)
            have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
            miss = [t for t in self.WANT if t not in have]
            for t in self.WANT:
                if t not in have:
                    continue
                cols = [c[0] for c in con.execute(f'DESCRIBE "{t}"').fetchall()]
                self.cols[t] = cols
                self.data[t] = [dict(zip(cols, row))
                                for row in con.execute(f'SELECT * FROM "{t}"').fetchall()]
            if miss:
                self.why = "庫在,但缺表:" + "、".join(miss)
        except Exception as exc:
            self.why = f"開庫失敗(多為別的行程持鎖){type(exc).__name__}:{str(exc)[:70]}"
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass

    def ok(self):
        return any(self.data[t] for t in self.WANT)


_LAMP = {"PASS": "ok", "WARN": "wa", "FAIL": "no", "N/A": "na",
         "N/A_NON_STOCK": "na", "N/A_NO_TEXT": "na", "N/A_NOT_RATED": "na",
         "N/A_TP_DECLARED_NA": "na",
         "MATCH": "ok", "MISMATCH": "no", "NO_HINT": "na",
         "NO_TICKER": "na", "UNKNOWN": "wa", "OK": "ok", "TEXT_ONLY": "wa",
         "NO_TEXT": "na"}


def _esc(v):
    return html.escape("" if v is None else str(v))


def _chip(v):
    return f'<span class="c {_LAMP.get(str(v), "na")}">{_esc(v)}</span>' if v not in (None, "") else '<span class="dim">-</span>'


_TAG = re.compile(r"<[^>]+>")


def _plain(c):
    return _TAG.sub("", str(c))


def _table(headers, rows, cls=""):
    """批429-X2 欄寬自動最佳化:掃該欄**實際內容**的長度定寬。
    v0105 讓瀏覽器平均分欄,結果「代號」「燈」這種 4 字欄被撐得跟「為何」一樣寬,
    真正需要空間的長文欄反而被擠到換行。短欄 nowrap、長欄按內容比例給寬。"""
    if not rows:
        return '<div class="dim pad">(無列)</div>'
    n = len(headers)
    widest = []
    for i in range(n):
        w = len(_plain(headers[i]))
        for r in rows:
            if i < len(r):
                # 中日韓字寬約兩倍
                txt = _plain(r[i])[:120]
                w = max(w, len(txt) + sum(1 for ch in txt if "\u2e80" <= ch <= "\u9fff"))
        widest.append(max(w, 2))
    total = sum(widest) or 1
    th, tc = [], []
    for i, h in enumerate(headers):
        short = widest[i] <= 10
        th.append(f'<th class="nw" style="width:{widest[i] * 100 / total:.1f}%">{_esc(h)}</th>'
                  if short else
                  f'<th style="width:{widest[i] * 100 / total:.1f}%">{_esc(h)}</th>')
        tc.append("nw" if short else "")
    body = []
    for r in rows:
        tds = []
        for i, c in enumerate(r):
            k = tc[i] if i < len(tc) else ""
            txt = _plain(c)
            if k == "nw" and re.fullmatch(r"[\d.,\-]+", txt.strip() or "x"):
                k = "num"
            tds.append(f'<td class="{k}">{c}</td>' if k else f"<td>{c}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{"".join(th)}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


_CSS = """
:root{--bg:#0b1220;--pn:#111a2e;--bd:#1e2a44;--tx:#c7d3e8;--dim:#7e8db0;
--hi:#e8eefb;--ac:#4f8ef7;--ok:#2f9e6d;--wa:#c9922a;--no:#c4483f;--na:#3c4a66}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--tx);margin:0;padding:12px 14px;
font:9.5px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif}
h1{font-size:12px;color:var(--hi);margin:0 0 2px;font-weight:600;letter-spacing:.2px}
.sub{color:var(--dim);font-size:9px;margin-bottom:9px}
.kpi{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:9px}
.kpi div{background:var(--pn);border:1px solid var(--bd);border-radius:5px;
padding:3px 7px;font-size:9px}
.kpi b{color:var(--hi);font-size:11px;font-weight:600;margin-right:4px;
font-variant-numeric:tabular-nums}
nav{display:flex;gap:4px;border-bottom:1px solid var(--bd);margin-bottom:9px}
nav label{padding:4px 9px;font-size:9.5px;color:var(--dim);cursor:pointer;
border:1px solid transparent;border-bottom:none;border-radius:5px 5px 0 0;
margin-bottom:-1px;white-space:nowrap}
nav label:hover{color:var(--tx)}
input[name=tab]{display:none}
.pg{display:none}
#t1:checked~nav label[for=t1],#t2:checked~nav label[for=t2],
#t3:checked~nav label[for=t3],#t4:checked~nav label[for=t4],
#t5:checked~nav label[for=t5],#t6:checked~nav label[for=t6]
{color:var(--hi);background:var(--pn);border-color:var(--bd);border-bottom-color:var(--pn)}
#t1:checked~#p1,#t2:checked~#p2,#t3:checked~#p3,#t4:checked~#p4,
#t5:checked~#p5,#t6:checked~#p6{display:block}
nav{overflow-x:auto}
section{background:var(--pn);border:1px solid var(--bd);border-radius:6px;
padding:7px 8px;margin-bottom:7px}
h2{font-size:10px;color:var(--ac);margin:0 0 6px;font-weight:600}
h2 small{color:var(--dim);font-weight:400;margin-left:6px;font-size:9px}
.tw{overflow-x:auto;max-height:none}
table{border-collapse:collapse;width:100%;font-size:8.5px;
font-variant-numeric:tabular-nums}
th{position:sticky;top:0;background:#16203a;color:var(--dim);text-align:left;
padding:2px 5px;border-bottom:1px solid var(--bd);font-weight:600;
white-space:nowrap;z-index:1}
td{padding:2px 5px;border-bottom:1px solid #17223a;vertical-align:top;
max-width:280px;overflow-wrap:anywhere}
tbody tr:nth-child(even){background:#0f1830}
tbody tr:hover{background:#18233d}
.c{display:inline-block;padding:0 5px;border-radius:3px;font-size:8px;
line-height:13px;color:#fff;white-space:nowrap}
.c.ok{background:var(--ok)}.c.wa{background:var(--wa)}
.c.no{background:var(--no)}.c.na{background:var(--na);color:#9fb0cf}
.dim{color:var(--dim)}
.pad{padding:5px 2px}
.fn{color:var(--hi);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
max-width:300px;display:inline-block;vertical-align:bottom}
.why{background:#1a1410;border:1px solid #4a3720;border-radius:5px;
padding:6px 8px;color:#e0b070;font-size:9.5px;margin-bottom:8px}
.src{font-size:9px;color:var(--dim);margin:-2px 0 6px}
td.num{text-align:right;white-space:nowrap}
td.nw,th.nw{white-space:nowrap}
/* 批429-X:堆疊矩陣——同一份報告的證據堆在一起看。橫表看不出
   「同一份報告的證據彼此矛盾」(檔名說 A、頁面說 B),堆疊才看得出來 */
.stk{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:6px}
.card{background:#0f1830;border:1px solid var(--bd);border-radius:5px;padding:6px 7px}
.card h3{font-size:9.5px;color:var(--hi);margin:0 0 4px;font-weight:600;
overflow-wrap:anywhere}
.card table{font-size:8.5px}
.card td:first-child{color:var(--dim);width:34%;white-space:nowrap}
.card .bar{height:3px;border-radius:2px;margin:4px 0 5px;display:flex;overflow:hidden}
.card .bar i{display:block;height:100%}
.rej{color:#c98b84;text-decoration:line-through}
.kept{color:#79c9a4;font-weight:600}
footer{color:var(--dim);font-size:9px;margin-top:10px;
border-top:1px solid var(--bd);padding-top:7px}
"""


def render_matrix_html(reports, facts, meta=None):
    """四分頁矩陣報告。回 HTML 字串(零 CDN、零外部資源)。
      ① DETAILED SUMMARY MATRIX  逐報告 × 全欄位 + 每一個閘(引擎本次實跑)
      ② ERROR MATRIX             只放紅黃 + 庫側 crosscheck 非 OK 列
      ③ BASIC INFO               庫 vrn_report_basic
      ④ FINANCIAL DATA           庫 vrn_report_financial + vrn_report_metrics
    """
    meta = meta or {}
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    gate_keys, tal = [], {"PASS": 0, "WARN": 0, "FAIL": 0}
    for r in reports:
        for k in (r.get("summary") or {}).get("gates", {}):
            if k not in gate_keys:
                gate_keys.append(k)
    for r in reports:
        v = (r.get("summary") or {}).get("verdict")
        if v in tal:
            tal[v] += 1

    # ── ① DETAILED SUMMARY MATRIX ──
    # 檔名層與頁面層**分開列**——兩者不一致正是 filename_vs_page 這盞燈在講的事,
    # 擠成一欄就看不出是哪一邊抓錯(批428-S)
    hd1 = (["報告檔", "型別", "代號(檔名)", "代號(頁面)", "券商(檔名)", "券商(頁面)",
            "報告日", "名稱(檔名)", "官方證券名", "對帳", "產業別",
            "TP", "TP態", "評等", "文字層", "總判"] + gate_keys)
    rows1 = []
    for r in reports:
        ff = r.get("filename_fields") or {}
        nr = r.get("name_reconcile") or {}
        tp = r.get("target_price") or {}
        sm = r.get("summary") or {}
        g = sm.get("gates", {})
        rows1.append([
            f'<span class="fn" title="{_esc(r.get("filename"))}">{_esc(r.get("filename"))}</span>',
            _chip(r.get("filename_parse", {}).get("kind")),
            _esc(ff.get("ticker") or "-"),
            _esc((r.get("ticker") or {}).get("ticker") or "-"),
            _esc(ff.get("broker") or "-"), _esc(r.get("broker") or "-"),
            _esc(ff.get("date") or "-"), _esc(nr.get("hint") or "-"),
            _esc(nr.get("official") or "-"), _chip(nr.get("verdict")),
            _esc(nr.get("industry") or "-"),
            _esc(tp.get("target_price") if tp.get("target_price") is not None else "-"),
            _esc(tp.get("tp_state") or "-"),
            _esc((r.get("rating") or {}).get("canonical") or "-"),
            _chip(r.get("text_state")), _chip(sm.get("verdict")),
        ] + [_chip(g.get(k)) for k in gate_keys])

    # ── ② ERROR MATRIX ──
    rows2 = []
    for r in reports:
        sm = r.get("summary") or {}
        nr = r.get("name_reconcile") or {}
        for k, v in sm.get("gates", {}).items():
            if v not in ("FAIL", "WARN"):
                continue
            why = {
                "name_match": nr.get("note", ""),
                "target_price": ((r.get("target_price") or {}).get("note", "")
                                 or ("全文無目標價觸發詞(target price/PT/目標價)"
                                     "——多半這份報告本來就沒有目標價,不是抽取失敗"
                                     if not r.get("tp_trigger_seen")
                                     else "文中有觸發詞卻抽不到數字=真的抽取失敗")),
                "tp_sanity": f"TP/價={(r.get('target_price') or {}).get('tp_ratio', '?')}",
                "nonstock_tp_leak": f"非個股報告卻抽到目標價 {(r.get('target_price') or {}).get('target_price')}"
                                    "——多半是文中某個數字被撈走,請人看一眼",
                "zone_presence": "資訊區要素未出現在本文分句裡(多為版面分區或無幾何)",
                "filename_vs_page": "檔名與頁面三要素(代號/券商/日期)對不上",
            }.get(k, "")
            rows2.append([
                f'<span class="fn" title="{_esc(r.get("filename"))}">{_esc(r.get("filename"))}</span>',
                _chip(v), _esc(k),
                _esc(r.get("filename_parse", {}).get("kind")),
                _chip(r.get("text_state")), _esc(why)])
    cc = [x for x in facts.data.get("vrn_report_crosscheck", [])
          if str(x.get("state", "")).upper() not in ("OK", "MATCH", "PASS", "")]
    rows2b = [[_esc(x.get("report_file")), _chip(x.get("state")), _esc(x.get("dimension")),
               _esc(x.get("period")), _esc(x.get("first_page_value")),
               _esc(x.get("table_value")), _esc(x.get("ratio")), _esc(x.get("note"))]
              for x in cc]

    # ── ③ BASIC INFO / ④ FINANCIAL ──
    def dbtab(table, prefer=()):
        rows = facts.data.get(table, [])
        if not rows:
            return None, None
        cols = [c for c in prefer if c in facts.cols[table]] or facts.cols[table]
        lamp = {"upside_state", "price_state", "ssot_state", "status", "state"}
        out = [[(_chip(r.get(c)) if c in lamp else _esc(r.get(c))) for c in cols]
               for r in rows]
        return cols, out

    h3, r3 = dbtab("vrn_report_basic",
                   ("report_file", "ticker", "name_official", "broker", "report_date",
                    "rating_raw", "rating_code", "target_price", "price", "price_db",
                    "upside_report", "upside_calc", "upside_db", "upside_state",
                    "price_state", "ssot_state", "report_kind", "analyst_names"))
    h4, r4 = dbtab("vrn_report_financial",
                   ("report_file", "page", "canonical", "raw_label", "period",
                    "status", "value", "raw_text"))
    h4b, r4b = dbtab("vrn_report_metrics",
                     ("report_file", "metric", "period", "status", "value", "raw_text"))

    # ── ⑤ 堆疊矩陣(批429-X:同一份報告的證據堆在一起)──
    def _stack(r):
        ff = r.get("filename_fields") or {}
        nr = r.get("name_reconcile") or {}
        tp = r.get("target_price") or {}
        sm = r.get("summary") or {}
        tk = r.get("ticker") or {}
        g = sm.get("gates", {})
        cnt = {"ok": 0, "wa": 0, "no": 0, "na": 0}
        for v in g.values():
            cnt[_LAMP.get(str(v), "na")] += 1
        tot = sum(cnt.values()) or 1
        bar = "".join(f'<i class="c {k}" style="width:{cnt[k] * 100 / tot:.0f}%"></i>'
                      for k in ("ok", "wa", "no", "na") if cnt[k])
        pairs = [
            ("型別", _chip(r.get("filename_parse", {}).get("kind")),
             _esc(r.get("filename_parse", {}).get("kind_reason", ""))),
            ("代號", (_esc(ff.get("ticker") or "-") + " <span class='dim'>檔名</span> / "
                    + _esc(tk.get("ticker") or "-") + " <span class='dim'>頁面</span>"),
             _esc(tk.get("why") or ("內文提及 " + str(tk.get("mentioned")))
                  if tk.get("mentioned") else "")),
            ("券商", (_esc(ff.get("broker") or "-") + " <span class='dim'>檔名</span> / "
                    + _esc(r.get("broker") or "-") + " <span class='dim'>頁面</span>"), ""),
            ("證券名", _esc(nr.get("hint") or "-") + " → " + _esc(nr.get("official") or "?"),
             _chip(nr.get("verdict")) + " " + _esc(nr.get("source") or "")),
            ("目標價", _esc(tp.get("target_price") if tp.get("target_price") is not None else "-"),
             _esc(tp.get("tp_state") or "") + (
                 " <span class='c wa'>幣別帶可疑</span>" if tp.get("tp_range_suspect") else "")),
            ("評等", _esc((r.get("rating") or {}).get("canonical") or "-"), ""),
            ("文字層", _chip(r.get("text_state")), _esc(r.get("chars_why", ""))[:60]),
        ]
        tr = "".join(f"<tr><td>{k}</td><td>{v}</td><td class='dim'>{w}</td></tr>"
                     for k, v, w in pairs)
        gl = " ".join(f'<span class="c {_LAMP.get(str(v), "na")}" title="{_esc(k)}">'
                      f'{_esc(k)}</span>' for k, v in g.items())
        return (f'<div class="card"><h3>{_chip(sm.get("verdict"))} '
                f'{_esc(r.get("filename"))}</h3><div class="bar">{bar}</div>'
                f'<table><tbody>{tr}</tbody></table>'
                f'<div style="margin-top:4px">{gl}</div></div>')

    stacks = "".join(_stack(r) for r in reports)

    # ── ⑥ 擷取結果驗證(批429:每個候選為何留、為何剔,攤開)──
    rows6 = []
    for r in reports:
        for c in (r.get("tp_candidates") or []):
            kept = not c["reject"]
            rows6.append([
                f'<span class="fn" title="{_esc(r.get("filename"))}">{_esc(r.get("filename"))}</span>',
                "目標價",
                (f'<span class="kept">{_esc(c["raw"])}</span>' if kept
                 else f'<span class="rej">{_esc(c["raw"])}</span>'),
                _esc(c["src"]), "有" if c["currency"] else "-",
                "有" if c["decimal"] else "-", f'{c["score"]:.1f}',
                (_chip("PASS") if kept else _chip("FAIL")),
                _esc(c["reject"] or "採用(同組最高分)")])
    kept6 = sum(1 for r in reports for c in (r.get("tp_candidates") or []) if not c["reject"])
    rej6 = sum(1 for r in reports for c in (r.get("tp_candidates") or []) if c["reject"])

    dbwhy = (f'<div class="why"><b>庫不可得</b> — {_esc(facts.why)}<br>'
             f'③④ 兩頁的資料來自先前 ENG073/ENG074 的入庫成果;庫取不到就是取不到,'
             f'這裡誠實留下原因而不是印一張空表讓人以為「跑過了沒資料」。</div>'
             ) if facts.why else ""

    src_note = ('<div class="src">①② 的<b>引擎側</b>每一格都是本次實跑當場算出來的;'
                '②下半與③④ 來自<b>庫側</b>(先前 ENG073/ENG074 的入庫成果)。'
                '兩者來源不同、時點不同,分開標明,不混成一鍋。</div>')

    nonstock = sum(1 for r in reports
                   if (r.get("summary") or {}).get("non_stock"))
    kinds = {}
    for r in reports:
        k = r.get("filename_parse", {}).get("kind") or "?"
        kinds[k] = kinds.get(k, 0) + 1

    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN 報告矩陣 · {_esc(ts)}</title><style>{_CSS}</style></head><body>
<h1>VRN 個股報告解讀矩陣<small class="dim"> · {ENGINE_NAME} {ENGINE_VERSION}</small></h1>
<div class="sub">{_esc(ts)} · {len(reports)} 件 · 來源 {_esc(meta.get('source', '-'))}
 · 代號冊 {_esc(meta.get('roster', '-'))} · NLP {_esc(meta.get('nlp', '-'))}
 · 正典 {_esc(meta.get('bridges', '-'))}</div>
<div class="kpi">
 <div><b>{len(reports)}</b>報告</div>
 <div><b>{tal['PASS']}</b>PASS</div><div><b>{tal['WARN']}</b>WARN</div>
 <div><b>{tal['FAIL']}</b>FAIL</div>
 <div><b>{len(rows2)}</b>引擎側異常格</div>
 <div><b>{len(rows2b)}</b>庫側對不上</div>
 <div><b>{nonstock}</b>非個股</div>
 <div><b>{kept6}</b>/{kept6 + rej6} TP候選採用</div>
 <div>{' · '.join(f'{k} {v}' for k, v in sorted(kinds.items(), key=lambda x: -x[1]))}</div>
</div>
<input type="radio" name="tab" id="t1" checked><input type="radio" name="tab" id="t2">
<input type="radio" name="tab" id="t3"><input type="radio" name="tab" id="t4">
<input type="radio" name="tab" id="t5"><input type="radio" name="tab" id="t6">
<nav><label for="t1">① DETAILED SUMMARY MATRIX</label>
<label for="t2">② ERROR MATRIX</label>
<label for="t3">③ BASIC INFO</label>
<label for="t4">④ FINANCIAL DATA</label>
<label for="t5">⑤ STACKED MATRIX 堆疊</label>
<label for="t6">⑥ EXTRACTION AUDIT 擷取驗證</label></nav>
<div class="pg" id="p1">{src_note}
 <section><h2>逐報告 × 全欄位 × 全閘<small>引擎本次實跑 · {len(reports)} 列 × {len(hd1)} 欄</small></h2>
 {_table(hd1, rows1)}</section></div>
<div class="pg" id="p2">{src_note}
 <section><h2>引擎側異常格<small>只放 FAIL/WARN;每一格附因由 · {len(rows2)} 格</small></h2>
 {_table(["報告檔", "燈", "閘", "型別", "文字層", "為何"], rows2)}</section>
 <section><h2>庫側交叉核對對不上<small>vrn_report_crosscheck 非 OK 列(首頁值 vs 表格值) · {len(rows2b)} 列</small></h2>
 {dbwhy if not facts.data.get('vrn_report_crosscheck') else ''}
 {_table(["報告檔", "狀態", "維度", "期間", "首頁值", "表格值", "比值", "註"], rows2b)}</section></div>
<div class="pg" id="p3">{dbwhy}
 <section><h2>BASIC INFO<small>庫 vrn_report_basic · {len(r3 or [])} 列</small></h2>
 {_table(h3 or [], r3 or [])}</section></div>
<div class="pg" id="p4">{dbwhy}
 <section><h2>FINANCIAL DATA<small>庫 vrn_report_financial · {len(r4 or [])} 列</small></h2>
 {_table(h4 or [], r4 or [])}</section>
 <section><h2>METRICS<small>庫 vrn_report_metrics · {len(r4b or [])} 列</small></h2>
 {_table(h4b or [], r4b or [])}</section></div>
<div class="pg" id="p5">{src_note}
 <section><h2>堆疊矩陣<small>同一份報告的證據堆在一起——橫表看不出「檔名說 A、頁面說 B」,
 堆疊才看得出來 · {len(reports)} 份</small></h2>
 <div class="stk">{stacks}</div></section></div>
<div class="pg" id="p6">
 <section><h2>擷取結果驗證 · 目標價候選<small>每一個候選為何留、為何剔,全部攤開 ·
 採用 {kept6} · 剔除 {rej6}</small></h2>
 <div class="src">這一頁回答的是「你憑什麼說目標價是這個數字」。
 v0105 取**第一個**命中就回,於是「泓德能源(6873)」的目標價抽成 6873;
 外資報告的 NT$48.5<b>bn</b> 是營收也被當成股價。現在每個候選都要通過
 代號回音/日期形狀/年份/量級後綴/前次目標價 五道剔除,再按
 來源(觸發詞 > 裸 NT$)→ 貨幣符號 → 小數 → 出現位置 排序。</div>
 {_table(["報告檔", "欄位", "候選值", "來源", "貨幣", "小數", "分數", "採用", "為何"], rows6)}
 </section></div>
<footer>零 CDN · 零外部資源 · 離線雙擊即開。燈號語意:
<span class="c ok">綠</span>過 · <span class="c wa">黃</span>存疑要人看
 · <span class="c no">紅</span>不過 · <span class="c na">灰</span>不適用/證據不可得。
灰**不是**綠——證據取不到時給灰,不給顏色。</footer>
</body></html>"""


# 批427b-P1:正典收件冊。路徑**不自己記**——冊在這裡,MDL139/MDL141 全走這條。
# 我上一則憑印象給了 VIA_Reports/incoming,錯的;本會期第三次同型錯誤
# (批425 猜站名、批426 猜斷言值、這次猜路徑)。記得不算證據,查冊才算。
SPEC_REL = "supportive modules/registry/VIA_InputConsole_Spec_v0100.json"
_SPEC_FALLBACK = {"dir_default": "functional modules/VRN/input_reports",
                  "incoming": "functional modules/VRN/input/incoming",
                  "extensions": [".pdf", ".docx"], "user_vrn_dir": ""}


def load_input_spec(via_root=None):
    """回 (families.vrn.input 區塊, 來源說明)。冊缺/壞=誠實退內建預設並說明,
    不靜默——靜默退後備正是批426-B 修掉的那個病。"""
    root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
    if root is None:
        return dict(_SPEC_FALLBACK), "找不到 VIA 根 → 內建預設"
    sp = root / SPEC_REL
    if not sp.exists():
        return dict(_SPEC_FALLBACK), f"冊不在({sp.name}) → 內建預設"
    try:
        d = json.loads(sp.read_text(encoding="utf-8-sig"))
        blk = d["families"]["vrn"]["input"]
        return ({"dir_default": blk.get("dir_default", _SPEC_FALLBACK["dir_default"]),
                 "incoming": blk.get("incoming", _SPEC_FALLBACK["incoming"]),
                 "extensions": blk.get("extensions", _SPEC_FALLBACK["extensions"]),
                 "user_vrn_dir": str((d.get("user") or {}).get("vrn_dir") or "").strip()},
                f"冊 {sp.name}")
    except Exception as exc:
        return dict(_SPEC_FALLBACK), f"冊讀取失敗 {type(exc).__name__} → 內建預設"


def fixtures_dir(via_root=None):
    """庫內修復文字語料夾(批437-A6)。回 (Path|None, 說明)。

    零九頭龍:這裡**不生文字**,只指路——文字是 VRNTextRepairEngine 1.0.0
    產的(four_engine_manifest.json 記著 run_id / sha256 / 64 records),
    本引擎只是把它當第二取字來源讀。找不到就誠實說找不到,不自己造語料。
    """
    root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
    if root is None:
        return None, "找不到 VIA 根"
    base = root / "functional modules" / "VRN" / "references" / "intake"
    if not base.is_dir():
        return None, f"intake 夾不在({base})"
    hits = sorted(base.glob("AttachmentFixedOutput_v*/*/01_repair/documents"))
    hits = [h for h in hits if h.is_dir() and any(h.glob("*.txt"))]
    if not hits:
        return None, f"intake 下沒有 AttachmentFixedOutput_v*/*/01_repair/documents(含 .txt)"
    d = hits[-1]                      # 尾版律
    return d, f"{d.relative_to(root)}({len(list(d.glob('*.txt')))} 份)"


def vrn_report_dirs(given=None, via_root=None):
    """報告夾律(與 CGC_MDL141 批399/400 同律,不另立一套):
       --dir > user.vrn_dir > 冊 dir_default;**incoming 一律併入**。
    回 (夾清單, 副檔名 tuple, 冊來源說明)。"""
    blk, why = load_input_spec(via_root)
    root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
    exts = tuple(str(x).lower() for x in blk["extensions"])
    dirs = []
    raw = str(given or blk.get("user_vrn_dir") or "").strip()
    if raw:
        q = Path(raw)
        dirs.append(q if q.is_absolute() else ((root / q) if root else q))
    elif root is not None:
        dirs.append(root / blk["dir_default"])
    if root is not None:
        inc = root / blk["incoming"]
        if inc not in dirs:
            dirs.append(inc)
    return dirs, exts, why


def collect_targets(dirs, exts):
    """回 (目標檔清單, 每夾診斷)。副檔名比對 suffix.lower()——.PDF/.Pdf 一律收
    (批427b-P3:v0103 的 glob("*.pdf") 在大小寫敏感的檔系上會漏)。
    診斷分三態,因為操作員的下一步完全不同:
      夾不存在        → 換路徑
      夾是空的        → 放檔進去
      夾有檔但沒報告檔 → 看副檔名(所以連夾裡有哪些副檔名、各幾個都列出來)"""
    files, diag = {}, []
    for d in dirs:
        if not d.exists():
            diag.append({"dir": str(d), "state": "夾不存在", "n": 0, "other": {}})
            continue
        if not d.is_dir():
            diag.append({"dir": str(d), "state": "不是資料夾", "n": 0, "other": {}})
            continue
        hit, other = 0, {}
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            sfx = f.suffix.lower()
            if sfx in exts:
                files.setdefault(f.name, f)
                hit += 1
            else:
                k = sfx or "(無副檔名)"
                other[k] = other.get(k, 0) + 1
        diag.append({"dir": str(d), "n": hit, "other": other,
                     "state": ("有報告檔" if hit else
                               "夾是空的" if not other else "夾有檔但沒有報告檔")})
    return list(files.values()), diag


def _open_report(dest, want):
    """批430-Y2:操作員說「沒有自動跳出 html u/i matrix report」。
    治理律是**零彈窗**(批340:引擎不得自作主張開視窗),所以預設不開;
    但操作員明打 --open 就是他要開,那不是自作主張。
    若他的殼設了 VIA_NO_OPEN=1(短指令梭一律設),照樣不開——
    那是他自己設的閘,我不代解;但要把「為何沒開、怎麼改」講清楚,
    不是靜靜不動作讓人以為壞了。"""
    if not want:
        print("[提示] 要跑完自動開頁請加 --open(治理律零彈窗:預設不開,"
              "引擎不自作主張開視窗)")
        return
    if os.environ.get("VIA_NO_OPEN") == "1":
        print("[未開頁] 你的殼設了 VIA_NO_OPEN=1(短指令梭一律設此旗)。"
              "這是你自己的閘,引擎不代解。本窗要開:$env:VIA_NO_OPEN=0 後重跑,"
              "或直接雙擊上面那個路徑。")
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(dest))                      # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(dest)])
        else:
            subprocess.Popen(["xdg-open", str(dest)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[已開頁] 預設瀏覽器")
    except Exception as exc:
        print(f"[開頁失敗] {type(exc).__name__}:{str(exc)[:70]} → 請手動雙擊上面的路徑")


def run_cli(args):
    ssot = _argval(args, "--ssot")
    as_json = "--json" in args
    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    one, many = _argval(args, "--file"), _argval(args, "--dir")
    via_root = _argval(args, "--via-root")
    # 批427-O:線上證券名稱查核**預設關**。要走網路必須操作員自己
    #   ① 開妥雙閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)② 明打 --web-names。
    #   引擎永不代設同意閘,也不在沒下旗標時偷連。
    web_names = "--web-names" in args
    eng = FirstPageEngine(ssot_path=ssot, via_root=via_root)
    if web_names:
        ok, why = eng.nr.gate()
        print(f"[名稱線上階梯] 旗標=開 · 同意閘={'開' if ok else '關'}({why})"
              + ("" if ok else " → 本跑不出網,只走 SSOT/VDF庫/MDL010 三離線階梯"))
    tdir = _argval(args, "--text-dir")
    if "--fixtures" in args and not tdir:
        # 批437-A6:我一直在跟操作員要 `--trace 貼回來`,而那 64 份報告的
        # **第二份取字**本來就躺在庫裡——references/intake 的
        # AttachmentFixedOutput(VRNTextRepairEngine 1.0.0 修復後的全文)。
        # 「我看不見他的 PDF 就修不了看不見的東西」不成立了:看得見。
        # 這不是第二套實作,是同一批報告的另一種取字,正好拿來當多工具核對的對照側。
        fx, fwhy = fixtures_dir(via_root)
        if fx is None:
            print(f"[絕] --fixtures 找不到庫內修復文字語料:{fwhy}")
            return 2
        tdir = str(fx)
        print(f"[庫內第二取字] {fwhy}")
    if tdir:
        # 批428-R:純文字語料車道(*.txt / *.pdf.txt)。庫裡的 64 份真報告全文
        # 就住在這種夾裡;它們不是 .pdf,冊上的 extensions 管不到,故走獨立旗標
        # ——不偷偷把 .txt 塞進正典 extensions 去擴張冊的約定。
        td = Path(tdir)
        if not td.is_dir():
            print(f"[絕] --text-dir 不是資料夾:{td}")
            return 2
        targets = sorted(td.glob("*.txt"))
        diag, exts, spec_why = ([{"dir": str(td), "state": "文字語料夾",
                                  "n": len(targets), "other": {}}], (".txt",),
                                "純文字語料車道(--text-dir)")
        if not targets:
            print(f"[絕] {td} 裡沒有 .txt")
            return 2
    elif one:
        targets, diag, exts, spec_why = [Path(one)], [], (), ""
        if not Path(one).exists():
            print(f"[絕] --file 指的檔不存在:{Path(one).resolve()}")
            return 2
    else:
        # 批427b-P1/P2:不給 --dir 也能跑——預設就走正典兩夾(冊 dir_default ∪ incoming)
        dirs, exts, spec_why = vrn_report_dirs(many, via_root)
        targets, diag = collect_targets(dirs, exts)
    if not targets:
        # 批427b-P2:三病分開講。v0103 一律回「[絕] 無可處理檔」,
        # 把「夾不存在/夾是空的/副檔名不對」壓成同一句——操作員看到「沒檔案」,
        # 真相卻是「夾根本不存在」,下一步完全走錯。把不同的失敗壓成同一個訊息,
        # 等於把診斷資訊丟掉,和批422 假綠是同一種病。
        print(f"[絕] 找不到可處理的報告檔。以下是**每個夾各自**的真實狀況"
              f"(報告夾律 --dir > user.vrn_dir > 冊 dir_default,incoming 一律併入;"
              f"來源={spec_why}):")
        for d in diag:
            extra = "、".join(f"{k}×{v}" for k, v in sorted(d["other"].items()))
            print(f"   · {d['state']:<8} {d['dir']}"
                  + (f"   [夾內其他檔:{extra}]" if extra else ""))
        print(f"   認的副檔名={'/'.join(exts) or '(無)'}(大小寫不拘)")
        print("   下一步:把報告放進下面這個**正典收件夾**,或用 --dir 指到你真正放報告的夾")
        print(f"     {diag[-1]['dir'] if diag else '(找不到 VIA 根)'}")
        return 2
    reports, bad = [], 0
    for p in targets:
        if p.suffix.lower() == ".txt":
            # 語料檔名是 "003_20251204兆豐個股報告-志強-KY(6768).pdf.txt",
            # 前綴序號與 .txt 都要剝掉才是真檔名(檔名層全靠它)
            disp = re.sub(r"^\d{3}_", "", p.name)
            disp = disp[:-4] if disp.lower().endswith(".txt") else disp
            chars, why = None, "純文字語料(--text-dir):無字元幾何,走 TEXT_ONLY"
            r = eng.run(disp, text=p.read_text(encoding="utf-8", errors="replace"),
                        allow_web_names=web_names)
        else:
            disp = p.name
            chars, why = _pdf_chars(p)
            r = eng.run(disp, chars=chars or None, allow_web_names=web_names)
        r["chars_why"] = why
        p = Path(disp)
        reports.append(r)
        s = r["summary"]
        if s["verdict"] == "FAIL":
            bad += 1
        if not as_json:
            fp = r["filename_parse"]
            tp = r["target_price"]
            # 批427 自審:報告可能是被攔截/部分產出的(檢⑩ 就用替身 run()),
            # 印表器不該因為少一個鍵就整支倒——.get 取,缺就印 -。
            nr = r.get("name_reconcile") or {}
            # f-string 運算式不得含 {} 字面(Py3.11 會當成替換欄),先取值
            ffd = r.get("filename_fields") or {}
            brk = r["broker"] or ffd.get("broker") or "-"
            # 批428-R:三態要各自講。TEXT_ONLY **有**文字(只是沒有版面幾何),
            # 印成「文字層=無」是把它和真的沒文字的 NO_TEXT 混為一談。
            nosrc = {"OK": "", "TEXT_ONLY": " 文字層=純文字",
                     "NO_TEXT": " 文字層=無"}.get(r.get("text_state", "OK"), "")
            src = ("/" + nr["source"]) if nr.get("source") else ""
            gate = f" · 閘 {s['gates']}" if s["verdict"] != "PASS" else ""
            print(f"  [{s['verdict']:<4}] {p.name[:44]:<46} 型別={fp['kind']:<6} "
                  f"代號={r['ticker']['ticker'] or '-':<5} 券商={brk:<8} "
                  f"TP={tp.get('target_price') or '-'} ({tp.get('tp_state', '-')})"
                  f"{nosrc} 名稱={nr.get('hint') or '-'}→{nr.get('official') or '?'}"
                  f"[{nr.get('verdict', '-')}{src}]{gate}")
    tr = _argval(args, "--trace")
    if tr:
        # 批432-AA3:我看不到操作員的 PDF,就修不了我看不見的東西。
        # 給他一個能把現場拍給我看的工具,比我在這邊猜十次有用。
        hit = [r for r in reports if tr.lower() in str(r.get("filename", "")).lower()]
        print(f"\n═══ TRACE「{tr}」· {len(hit)} 件 ═══")
        for r in hit:
            tp = r.get("target_price") or {}
            print(f"\n── {r.get('filename')}")
            print(f"   型別={r.get('filename_parse', {}).get('kind')} "
                  f"代號(檔名)={(r.get('filename_fields') or {}).get('ticker')} "
                  f"文字層={r.get('text_state')} 字元數={len(r.get('main_text_raw') or '')}")
            print(f"   採用 TP={tp.get('target_price')} 等級={r.get('tp_grade') or '-'}"
                  f"({r.get('tp_grade_why') or '-'})")
            if r.get("upside_stated") is not None:
                print(f"   報告自陳上漲空間={r['upside_stated']}% ⇒ 隱含報告日原始價="
                      f"{r.get('implied_price')} [{r.get('implied_price_state')}]")
            print(f"   {'值':>12}  {'來源':<6}{'幣':<3}{'小':<3}{'分數':>7}  留/剔")
            for c in (r.get("tp_candidates") or []):
                mark = "留" if not c["reject"] else "剔"
                note = c["reject"] or (f"⟨自洽⟩ {c['arb']}" if c.get("arb") else "")
                print(f"   {c['raw']:>12}  {c['src']:<6}{'Y' if c['currency'] else '-':<3}"
                      f"{'Y' if c['decimal'] else '-':<3}{c['score']:>7.1f}  {mark} "
                      f"{note}")
            print(f"   閘 {r.get('summary', {}).get('gates')}")
        print("\n(把這段貼回來,我就看得到你的 PDF 文字層長什麼樣)")
    bd = _argval(args, "--body")
    if bd:
        hit = [r for r in reports if bd.lower() in str(r.get("filename", "")).lower()]
        print(f"\n═══ 驗證後的本文「{bd}」· {len(hit)} 件 ═══")
        for r in hit:
            tc = r.get("text_consensus") or {}
            print(f"\n── {r.get('filename')}")
            print(f"   核對={tc.get('state')} 相似度={tc.get('ratio')} "
                  f"工具={'+'.join(tc.get('tools') or []) or '-'}")
            print(f"   來源={r.get('text_source')}")
            body = (r.get("main_text_repaired") or r.get("main_text_raw") or "").strip()
            print("   ┌─ 本文(不含頁尾小字) " + "─" * 40)
            for ln in (body or "(空)").splitlines() or ["(空)"]:
                print(f"   │ {ln}")
            print("   └" + "─" * 60)
            tb = r.get("tables_verified") or []
            print(f"   表格 {len(tb)} 張" + ("" if tb else "(本頁無表格,或兩法都沒還原出來)"))
            for i, t in enumerate(tb[:3], 1):
                rows = t if isinstance(t, list) else (t.get("rows") if isinstance(t, dict) else [])
                print(f"   ── 表 {i}:{len(rows or [])} 列")
                for row in (rows or [])[:6]:
                    print("      | " + " | ".join(str(c or "")[:18] for c in (row or [])))
        print("\n(核對=AGREE 才是兩法讀出來一樣;DIVERGE 代表這一頁的字不可信)")
    st = _argval(args, "--struct")
    if st:
        hit = [r for r in reports if st.lower() in str(r.get("filename", "")).lower()]
        print(f"\n═══ 文件結構「{st}」· {len(hit)} 件 ═══")
        for r in hit:
            print(f"\n── {r.get('filename')}")
            print(f"   階層來源={r.get('doc_tier_source')}")
            print(f"   財報表冊={r.get('stmt_book')}")
            rows = r.get("doc_rows") or []
            print(f"   {'TYPE':<12}{'CAT':<4}{'表/圖號':<8}{'財報表':<10}內容")
            print("   " + "─" * 96)
            for d in rows[:40]:
                cap = (d["CAPTION_NO"] or "") + ("·" + d["CAPTION_DESC"][:10]
                                                 if d["CAPTION_DESC"] else "")
                print(f"   {d['TYPE']:<12}{d['CATEGORY']:<4}{cap[:8]:<8}"
                      f"{(d['STMT_ZH'] or '-'):<10}{d['TEXT'][:56]}")
                if d["SOURCE"]:
                    print(f"   {'':<12}{'':<4}{'':<8}{'':<10}└ 來源:{d['SOURCE'][:44]}")
            tb = r.get("doc_table") or {}
            print(f"\n   表格還原:{tb.get('why')}")
            if tb.get("header"):
                print("      表頭 | " + " | ".join(str(c)[:14] for c in tb["header"]))
                for row in (tb.get("rows") or [])[:8]:
                    print("           | " + " | ".join(str(c)[:14] for c in row))
        print("\n(一標題 一句話 一資料分類;TYPE=字體階層,CAT=表/圖/文)")
    rep_out = _argval(args, "--report")
    if rep_out or "--report" in args:
        root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
        dest = Path(rep_out) if rep_out else (
            (root / "VIA_Reports" / "vrn" / "VRN_REPORT_MATRIX.html") if root
            else Path("VRN_REPORT_MATRIX.html"))
        facts = DbFacts(via_root=via_root)
        nlp0 = reports[0].get("nlp_route") or {}
        xb0 = reports[0].get("xval_bridge") or {}
        meta = {"source": spec_why or str(one or ""),
                "roster": f"{len(eng.tf.roster)} 檔 · {eng.tf.roster_state}",
                "nlp": nlp0.get("route", "-"),
                "bridges": f"MDL008={'在' if xb0.get('mdl008') else '缺'}"
                           f"/TW02={'在' if xb0.get('tw02') else '缺'}"}
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_matrix_html(reports, facts, meta), encoding="utf-8")
        _open_report(dest, "--open" in args)
        print(f"[六分頁] {dest}  ({dest.stat().st_size / 1024:.0f} KB · 零 CDN · 離線可開)"
              + (f"  · 庫:{facts.why}" if facts.why else
                 f"  · 庫:basic {len(facts.data['vrn_report_basic'])}"
                 f"/financial {len(facts.data['vrn_report_financial'])}"
                 f"/crosscheck {len(facts.data['vrn_report_crosscheck'])} 列"))
    if as_json:
        print(json.dumps(reports, ensure_ascii=False, indent=1, default=str))
    else:
        nlp = reports[0]["nlp_route"]
        xb = reports[0]["xval_bridge"]
        print(f"[計] {len(reports)} 件 · FAIL {bad} · NLP 路徑={nlp['route']}"
              + (f"({nlp['hub_dir']})" if nlp.get("hub_dir") else "")
              + (f" · **為何**:{nlp['why']}" if nlp.get("why") else "")
              + f" · 正典 MDL008={'在' if xb['mdl008'] else '缺'}"
                f"/TW02={'在' if xb['tw02'] else '缺'}")
        nr0 = reports[0].get("name_reconcile") or {}
        nw = nr0.get("why") or {}
        print(f"[名稱對帳] 階梯={' → '.join(nr0.get('trail') or ['(未跑)'])}"
              + (f" · **為何**:{'; '.join(f'{k}={v}' for k, v in nw.items())}" if nw else ""))
    return 1 if bad else 0


# =====================================================================
# SELFTEST(批426-M:零觸碰任何正本;批424 的教訓——自測寫正本冊,
#          十餘跑就把 escalation_log 從 66 筆灌成 78 筆)
# =====================================================================
def _ast_calls(src, skip_funcs=()):
    """回 (被呼叫的屬性名集合, 屬性名→所在函式名)。
    批426 自審:v0102 初版的檢②⑪ 用「原始碼裡有沒有這串字」來判,結果掃到
    **斷言自己寫的那串字**=自指偽陽(批423 SUP_MDL743 踩過同一個坑)。
    掃 AST 看的是真實呼叫節點,字串常數不會被算進來。"""
    import ast as _ast
    tree = _ast.parse(src)
    where, names = {}, set()
    for fn in _ast.walk(tree):
        if not isinstance(fn, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            continue
        if fn.name in skip_funcs:
            continue
        for n in _ast.walk(fn):
            if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute):
                names.add(n.func.attr)
                where.setdefault(n.func.attr, fn.name)
    return names, where


def selftest() -> int:
    fails = []

    done = []

    def chk(name, cond, note=""):
        # 批437 自審:檢數原本是**手寫**的 n = 28,加了兩檢卻忘了改,
        # 於是「三十檢 OK 28」自己打自己的臉。會被忘記的數字就不該用手寫。
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    fin = FinancialValidation()
    # ① 崩潰修(v0101 實測 TypeError)
    r1, r2 = fin.multiply(None, 10, 5), fin.add_sub(None, [1, 2])
    r3 = fin.division(None, 1, 2)
    chk("① None 不再當場崩(批426-A:v0101 multiply(None,10,5) 與 add_sub(None,[1,2]) "
        "皆 TypeError,而 None 正是抽取器找不到數字時的常態回傳)",
        r1["verdict"] == "N/A" and r2["verdict"] == "N/A" and r3["verdict"] == "N/A"
        and fin.multiply(1275, 25, 51)["verdict"] in ("PASS", "PASS-SOFT", "WARN", "FAIL"),
        f"(multiply={r1['verdict']} add_sub={r2['verdict']} division={r3['verdict']})")

    # ② NLP 真 API(v0101 呼叫不存在的 repaired())
    src = Path(__file__).read_text(encoding="utf-8")
    nlp = NLPRepair(auto_hub=False)
    _calls, _ = _ast_calls(src)
    _dehy = nlp.repair_text("a-\n b   c")      # f-string 運算式不得含反斜線 → 先取值
    chk("② NLP 掛鉤用真 API(批426-B:v0101 呼叫 self.ext.repaired(),而 TextProcessor "
        "只有 repair()——每次 AttributeError 被 except 吃掉→靜默退後備,外接引擎等於沒接。"
        "本檢用 AST 看真實呼叫節點,不掃字串——掃字串會掃到斷言自己寫的那串字)",
        "repaired" not in _calls and "repair" in _calls
        and "split_sentences" in _calls and "normalize" in _calls
        and nlp.route()["route"] == "HEURISTIC"
        # 後備行為兩件事各驗一次:換行連字號要**接回**(a- \n b → ab,這是
        # 研報 PDF 換行斷字的常態),連續空白要壓成一個。
        and _dehy == "ab c"
        and nlp.repair_text("x   y\n\n z") == "x y z",
        f"(呼叫到 repair={'repair' in _calls} repaired={'repaired' in _calls};"
        f"去連字號={_dehy!r};無外接時 route={nlp.route()['route']})")

    # ③ 民國七碼(v0101 回 None)
    chk("③ 民國七碼日期(批426-D:操作員真檔名 華南投顧-2637-慧洋-KY-1141202 正在用;"
        "v0101 只認 8/6 碼,1141202 回 None)",
        TickerFilename.numtoken_to_date("1141202") == "2025-12-02"
        and TickerFilename.numtoken_to_date("20251202") == "2025-12-02"
        and TickerFilename.numtoken_to_date("251202") == "2025-12-02"
        and TickerFilename.numtoken_to_date("3014") is None,
        "(四碼代號不得被當日期)")

    # ④ -KY 公司名 + 型別分類
    tf = TickerFilename()
    p = tf.parse_filename("華南投顧-2637-慧洋-KY-1141202.pdf")
    p2 = tf.parse_filename("20251205兆豐晨會報告-當日新聞與重要訊息評論.pdf")
    chk("④ 名字-KY 整體收為公司名 + 報告型別分類(批426-E/G;v0101 把 慧洋-KY 切成"
        "「慧洋」+「KY」,且無型別概念=非個股會被當失敗)",
        "慧洋-KY" in p["names"] and p["tickers"] == ["2637"]
        and p["dates"] == ["2025-12-02"] and p["kind"] == "個股"
        and p2["kind"] == "大盤晨報"
        and TickerFilename.kind_expects_ticker("個股")
        and not TickerFilename.kind_expects_ticker("大盤晨報"),
        f"(names={p['names']} kind={p['kind']} / {p2['kind']})")

    # ⑤ 目標價 regex 加寬(v0101 兩型皆回 None)
    fv = FieldValidation()
    got = {s: fv.extract_target_price(s) for s in
           ("目標價:145 元", "NT$1,275", "12-month target price: NT$1,275",
            "Price Target 650", "PT 78")}
    chk("⑤ 目標價觸發詞加寬(批426-F:v0101 只認 NT$ 與 目標價,GS/MS 的 "
        "Price Target / PT 全部漏抽——實測皆回 None)",
        got["Price Target 650"] == 650.0 and got["PT 78"] == 78.0
        and got["12-month target price: NT$1,275"] == 1275.0
        and got["目標價:145 元"] == 145.0,
        f"({got})")

    # ⑥ 期間前綴(操作員規格③)
    pp = {t: parse_period(t) for t in
          ("FY-23", "F23", "2023", "20230102", "230102", "1141202",
           "12/25E", "1Q25", "114年", "2023F")}
    chk("⑥ 期間前綴全收(操作員規格③:FY-23 / F23 / 2023 / 20230102 / 230102 / 民國;"
        "並分開回報基準 A實際/E預估/F預測——把預估當實際比對就是製造假訊息)",
        pp["FY-23"]["period"] == "2023" and pp["F23"]["period"] == "2023"
        and pp["F23"]["basis"] == "forecast" and pp["2023"]["kind"] == "year"
        and pp["20230102"]["period"] == "2023-01-02"
        and pp["230102"]["period"] == "2023-01-02"
        and pp["1141202"]["period"] == "2025-12-02" and pp["1141202"]["roc"]
        and pp["12/25E"]["period"] == "2025-12" and pp["12/25E"]["basis"] == "estimate"
        and pp["1Q25"]["period"] == "2025-Q1" and pp["114年"]["period"] == "2025"
        and pp["2023F"]["basis"] == "forecast",
        f"(FY-23→{pp['FY-23']['period']} · F23→{pp['F23']['basis']} · "
        f"1141202→{pp['1141202']['period']} · 1Q25→{pp['1Q25']['period']})")

    # ⑦ 百萬兩位小數(操作員規格①)
    chk("⑦ 統一到百萬、小數點後兩位(操作員規格①;不可轉=None 不當 0)",
        to_million_2dp("22,500.049") == 22500.05
        and to_million_2dp(1, "billion") == 1000.0
        and to_million_2dp("1,234", "thousand_ntd") == 1.23
        and to_million_2dp(None) is None and to_million_2dp("n/a") is None
        and MILLION_DECIMALS == 2,
        f"(22,500.049→{to_million_2dp('22,500.049')} · "
        f"1 billion→{to_million_2dp(1, 'billion')})")

    # ⑧ TP 合理性閘 + 復權誠實
    pa = PriceAdjustment()
    chk("⑧ TP 合理性閘 + 復權誠實(批419 工作站:三份真報告 TP/價 比 0.020/0.019/0.005"
        "=抽錯的數,印成「上漲 -98%」比不印更糟;批425:現價非復權一律拒算,"
        "不拿原始 close 頂替)",
        pa.tp_sanity(38.0, 942.0)[0] == "TP_SUSPECT"
        and pa.tp_sanity(1275.0, 1130.0)[0] == "OK"
        and pa.tp_sanity(None, 100)[0] == "NA"
        and pa.upside(1275, 1130) == 0.1283
        and pa.upside(1275, 1130, is_adjusted=False) is None,
        f"(0.040→{pa.tp_sanity(38.0, 942.0)[0]} · "
        f"非復權→{pa.upside(1275, 1130, is_adjusted=False)})")

    # ⑨ 總判必須讀到所有子閘(批422 假綠)
    eng = FirstPageEngine(auto_hub=False)
    bad = {"filename_parse": {"kind": "個股"},
           "target_price": {"verdict": "PASS", "tp_state": "TP_SUSPECT"}}
    ns = {"filename_parse": {"kind": "大盤晨報"},
          "target_price": {"verdict": "FAIL", "tp_state": "NA"}}
    a, b = eng.aggregate_verdict(bad), eng.aggregate_verdict(ns)
    chk("⑨ 總判讀得到 TP 合理性閘,且非個股不被判紅(批422 假綠:上游閘抓到 TP_SUSPECT、"
        "下游判定不讀它,於是目標價只有股價 1/200 的報告被印成 DONE;批418:"
        "非個股沒有代號與目標價是正常)",
        a["verdict"] == "FAIL" and a["gates"].get("tp_sanity") == "FAIL"
        and b["verdict"] != "FAIL" and b["non_stock"] is True
        and b["gates"].get("target_price") == "N/A_NON_STOCK",
        f"(個股+TP_SUSPECT→{a['verdict']} · 非個股+FAIL→{b['verdict']})")

    # ⑩ CLI 真的接線(批425 一連四例)
    import contextlib, io
    seen = {}
    real_run, real_argv = FirstPageEngine.run, sys.argv
    try:
        FirstPageEngine.run = lambda self, filename, **kw: (
            seen.update({"filename": filename, "kw": sorted(kw)}) or {
                "summary": {"verdict": "PASS", "gates": {}},
                "filename_parse": {"kind": "個股"}, "ticker": {"ticker": "2330"},
                "broker": "GS", "target_price": {"target_price": 1, "tp_state": "OK"},
                "nlp_route": {"route": "HEURISTIC", "why": ""},
                "xval_bridge": {"mdl008": False, "tw02": False, "why": {}}})
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "GS-2330 20251205.pdf"
            f.write_bytes(b"%PDF-1.4\n%%EOF\n")
            sys.argv = ["x", "--file", str(f)]
            rc = run_cli(sys.argv[1:])
            # 缺值對照組:不得 IndexError。批427b 起 rc=2 而非 0——
            # 旗標打壞卻回成功,對串鏈的呼叫端就是一句謊(via-closeout --run
            # 靠 rc≠0 才會誠實停)。所以這裡要的是「不崩 + 回非零 + 說得出為什麼」。
            sys.argv = ["x", "--file"]
            _cap2 = io.StringIO()
            with contextlib.redirect_stdout(_cap2):
                rc2 = run_cli(sys.argv[1:])
            _msg2 = _cap2.getvalue()
    finally:
        FirstPageEngine.run, sys.argv = real_run, real_argv
    chk("⑩ CLI 旗標真的接到 run()(批425:ENG073 main() 光禿禿 return run()、"
        "ENG074 寫死 run(d,None,..)、MDL141 不解析 --db、AllGreen $StageTimeoutSec "
        "宣告沒用過——四天內同一模式四次。缺值時誠實忽略不得 IndexError)",
        rc == 0 and seen.get("filename") == "GS-2330 20251205.pdf"
        and rc2 == 2 and "沒有值=忽略" in _msg2 and "找不到可處理的報告檔" in _msg2,
        f"(收到 filename={seen.get('filename')};缺值 rc={rc2} 且有講原因="
        f"{'找不到可處理的報告檔' in _msg2})")

    # ⑪ 正典橋誠實三態 + 零觸碰正本
    xb = XValBridge(via_root="/__no_such_via_root__")
    _prod_calls, _ = _ast_calls(src, skip_funcs=("selftest",))   # 正式碼路徑
    # 批428-S:--report 產四分頁是**正當產出**,當然要落檔。但「允許落檔」不等於
    # 「不用管」——改成指名唯一的落檔者:只有 run_cli 可以寫,而且寫的是
    # VIA_Reports(已 gitignore),正本冊一個都不許碰。多一個函式會寫就要紅。
    import ast as _a11
    _writers = {}
    for _fn in _a11.walk(_a11.parse(src)):
        if not isinstance(_fn, (_a11.FunctionDef, _a11.AsyncFunctionDef)) \
                or _fn.name == "selftest":
            continue
        for _nd in _a11.walk(_fn):
            if isinstance(_nd, _a11.Call) and isinstance(_nd.func, _a11.Attribute) \
                    and _nd.func.attr in ("write_text", "write_bytes", "mkdir", "escalate"):
                _writers.setdefault(_nd.func.attr, set()).add(_fn.name)
    chk("⑪ 正典橋缺席=誠實說缺(不假裝有),且本檔自測零觸碰任何正本"
        "(批424:自測寫正本冊,十餘跑把 66 筆灌成 78 筆)",
        xb.status()["mdl008"] is False and xb.status()["tw02"] is False
        and xb.status()["why"] and xb.tolerance(500)[1] == "LOCAL_BAND"
        and xb.is_valid_ticker("2330") and not xb.is_valid_ticker("2025")
        and "escalate" not in _writers
        and "write_bytes" not in _writers
        and set(_writers.get("write_text", set())) <= {"run_cli"}
        and set(_writers.get("mkdir", set())) <= {"run_cli"},
        f"(why={list(xb.status()['why'])};落檔者="
        f"{ {k: sorted(v) for k, v in sorted(_writers.items())} or '無'})")

    # ⑫ 表格幾何:bisect 與線性掃答案必須完全相同(批426-K 只換速度不換答案)
    import random
    random.seed(7)
    centers = sorted(random.uniform(0, 800) for _ in range(60))
    probes = [random.uniform(-50, 850) for _ in range(400)]
    same = all(TableGeometry._nearest(centers, v)
               == min(range(len(centers)), key=lambda i: abs(centers[i] - v))
               for v in probes)
    chk("⑫ bisect 最近群聚與原線性掃**答案完全相同**(批426-K 是效能改寫,"
        "不是行為改寫;400 組亂數探針對照)",
        same and TableGeometry._nearest([], 1) == 0)

    # ⑬ 型別分類:次序即判準 + 對照組(批427-N)
    tf13 = TickerFilename()
    cases = [
        # (檔名, 有代號?, 應得型別, 這一條在守什麼)
        ("GS-AI PCB CCL 20251204.pdf",      False, "產業",     "操作員本次點名:主題詞冊補 PCB/CCL"),
        ("GS TPU GPU outlook.pdf",          False, "產業",     "主題詞冊補 TPU/GPU"),
        ("台新AI伺服器-2317鴻海.pdf",         True,  "個股",     "對照組:有代號時主題詞不得越過代號"),
        ("2330法說會報告.pdf",               True,  "個股",     "對照組:法說由強降弱,個股法說仍是個股"),
        ("20251205兆豐晨會報告.pdf",          False, "大盤晨報", "強標記:晨會縱使列代號也非個股"),
        ("半導體產業展望2026.pdf",            False, "產業",     "中文主題詞"),
        ("MS review of preview.pdf",        False, "未分類",   "反例:ev/ic 不得被 in 掃中(詞界)"),
        ("KGI 2454 MediaTek update.pdf",    True,  "個股",     "反例:英文主題詞不得越過代號"),
        ("海外券商看盤前重點.pdf",             False, "大盤晨報", "強標記優先於弱標記"),
    ]
    bad13 = [(f, want, tf13.classify_kind(f, ht)[0])
             for f, ht, want, _ in cases if tf13.classify_kind(f, ht)[0] != want]
    chk("⑬ 型別分類次序正確且詞冊夠用(批427-N:v0102 把 GS-AI PCB CCL 判成未分類;"
        "但**只補詞冊不改次序**會把「台新AI伺服器-2317鴻海」判成產業——"
        "把個股判成產業比未分類更糟。九例含四組對照組,少一組就證不出次序)",
        not bad13 and tf13.tech_acronyms("GS-AI PCB CCL") == ["AI", "CCL", "PCB"],
        f"(不合={bad13 or '無'};GS 被停用詞扣掉={tf13.tech_acronyms('GS-AI PCB CCL')})")

    # ⑭ 代號↔證券名稱對帳:階梯、佔位名、同意閘(批427-O)
    import ast as _ast14
    tree14 = _ast14.parse(src)
    env_writes = []
    for nd in _ast14.walk(tree14):
        if isinstance(nd, (_ast14.Assign, _ast14.AugAssign)):
            tgts = nd.targets if isinstance(nd, _ast14.Assign) else [nd.target]
            for t in tgts:
                if isinstance(t, _ast14.Subscript) and "environ" in _ast14.dump(t.value):
                    env_writes.append(getattr(nd, "lineno", 0))
        if isinstance(nd, _ast14.Call) and isinstance(nd.func, _ast14.Attribute) \
                and nd.func.attr in ("putenv", "setdefault") \
                and "environ" in _ast14.dump(nd.func.value):
            env_writes.append(getattr(nd, "lineno", 0))

    class _NetSpy:                      # 閘關時**一次都不許**被碰到的替身
        called = []

        @staticmethod
        def gate_state():
            return {"gate1_net_consent": False, "gate2_scrape_token_set": False,
                    "gate1_raw": "(未設)", "open": False}

        @staticmethod
        def http_json(url, timeout=30):
            _NetSpy.called.append(url)
            raise AssertionError("閘關竟然出網")

    nr14 = NameReconciler(via_root="/__no_such_via_root__", tk2name={"2317": "鴻海"},
                          net_tool=_NetSpy)
    web_name, web_src = nr14._from_web("2317")
    gate_open, gate_why = nr14.gate()
    r_ssot = nr14.reconcile("2317", "鴻海")
    r_bad = nr14.reconcile("2317", "鴻準")
    r_nohint = nr14.reconcile("2317", None)
    r_unk = nr14.reconcile("9999", "查無此股")
    chk("⑭ 名稱對帳四階梯 + 同意閘鐵律(批427-O:①離線先行 ②佔位名不採計——"
        "MDL010 對任何四碼都回 name=\"TW:2637\" 且 ok=True,收下它就會把慧洋-KY "
        "判成 MISMATCH,自己造一盞假紅 ③閘關=零出網,且本檔全域**不存在**任何"
        "寫環境變數的節點:引擎永不代設 VIA_NET_CONSENT)",
        not env_writes and not _NetSpy.called and web_name is None
        and gate_open is False and "未開" in gate_why
        and r_ssot["verdict"] == "MATCH" and r_ssot["source"] == "SSOT"
        and r_bad["verdict"] == "MISMATCH" and r_nohint["verdict"] == "NO_HINT"
        and r_unk["verdict"] == "UNKNOWN"
        and NameReconciler.same_name("慧洋-KY", "慧洋")            # ②包含
        and NameReconciler.same_name("台積電", "台灣積體電路")        # ③縮寫子序列
        and NameReconciler.same_name("中鋼", "中國鋼鐵")            # ③縮寫子序列
        and not NameReconciler.same_name("鴻海", "鴻準")           # 對照:真的不同股
        and not NameReconciler.same_name("台泥", "台灣化學纖維")     # 對照:只共用首字
        and not NameReconciler.same_name("大同", "大")             # 對照:二字以下不包含
        and TickerFilename().name_hint("台新AI伺服器-2317鴻海.pdf", "2317") == ("鴻海", "after")
        and TickerFilename().name_hint("兆豐個股報告-2317-2025.pdf", "2317")[0] is None,
        f"(寫環境變數的節點={env_writes or '無'};閘關時出網次數={len(_NetSpy.called)};"
        f"UNKNOWN 而非 PASS={r_unk['verdict']})")

    # ⑮ 收件三態 + 報告夾律綁正典冊(批427b-P)
    import shutil, tempfile as _tf15
    _root15 = Path(_tf15.mkdtemp(prefix="via_fpe_dirlaw_"))
    (_root15 / "supportive modules" / "registry").mkdir(parents=True)
    (_root15 / "functional modules").mkdir(parents=True)
    _spec15 = {"families": {"vrn": {"input": {
        "dir_default": "functional modules/VRN/input_reports",
        "incoming": "functional modules/VRN/input/incoming",
        "extensions": [".pdf", ".docx"]}}}, "user": {"vrn_dir": ""}}
    (_root15 / SPEC_REL).write_text(json.dumps(_spec15, ensure_ascii=False),
                                    encoding="utf-8")
    _d_miss = _root15 / "夾不存在"                       # 態① 根本沒建
    _d_empty = _root15 / "空夾"; _d_empty.mkdir()        # 態② 建了但空
    _d_wrong = _root15 / "副檔名不對"; _d_wrong.mkdir()   # 態③ 有檔但不是報告
    (_d_wrong / "note.txt").write_text("x", encoding="utf-8")
    (_d_wrong / "sheet.xlsx").write_text("x", encoding="utf-8")
    _d_ok = _root15 / "有報告"; _d_ok.mkdir()
    (_d_ok / "GS-2330.PDF").write_text("x", encoding="utf-8")   # 大寫副檔名
    (_d_ok / "兆豐-2317鴻海.docx").write_text("x", encoding="utf-8")
    (_d_ok / "readme.md").write_text("x", encoding="utf-8")
    _blk15, _why15 = load_input_spec(_root15)
    _dirs15, _exts15, _ = vrn_report_dirs(None, _root15)
    _t15, _g15 = collect_targets([_d_miss, _d_empty, _d_wrong, _d_ok], _exts15)
    _states = [g["state"] for g in _g15]
    _docx_why = _pdf_chars(_d_ok / "兆豐-2317鴻海.docx")[1]
    try:
        chk("⑮ 收件三態分開講 + 報告夾律綁正典冊(批427b-P:操作員照我給的路徑打 "
            "--dir VIA_Reports\\incoming 得到「[絕] 無可處理檔」——P1 路徑是我憑印象"
            "給錯的(正典在 functional modules/VRN/input/incoming,冊裡寫著);"
            "P2 夾不存在/夾是空的/副檔名不對三種原因壓成同一句,操作員的下一步完全不同;"
            "P3 glob(\"*.pdf\") 漏大寫 .PDF,冊上還認 .docx 卻看都不看)",
            _states == ["夾不存在", "夾是空的", "夾有檔但沒有報告檔", "有報告檔"]
            and _g15[2]["other"] == {".txt": 1, ".xlsx": 1}
            and _g15[3]["other"] == {".md": 1}
            and sorted(f.name for f in _t15) == ["GS-2330.PDF", "兆豐-2317鴻海.docx"]
            and _exts15 == (".pdf", ".docx") and "冊 " in _why15
            and _blk15["incoming"] == "functional modules/VRN/input/incoming"
            and [d.name for d in _dirs15] == ["input_reports", "incoming"]
            and "非 PDF" in _docx_why,
            f"(三態={_states};大寫.PDF 與 .docx 都收到={len(_t15)} 件;"
            f"冊來源={_why15};docx={_docx_why[:28]})")
    finally:
        shutil.rmtree(_root15, ignore_errors=True)

    # ⑯ 無文字層=文字類閘一律 N/A,檔名類閘照常判(批427b-Q)
    eng16 = FirstPageEngine(auto_hub=False)
    # 批428-V3 之後,TP=FAIL 還要看觸發詞在不在——這裡測的是「無文字層」那一刀,
    # 故明講有觸發詞,免得測到 V3 的分支還以為 ⑯ 壞了(斷言要指名它在測什麼)
    base16 = {"filename_parse": {"kind": "個股"}, "tp_trigger_seen": True,
              "rating": {"canonical": "BUY"},
              "target_price": {"verdict": "FAIL", "tp_state": "NA"},
              "xv_zone_presence": {"verdict": "WARN"},
              "xv_filename_vs_page": {"verdict": "PASS"},
              "name_reconcile": {"verdict": "MATCH"}}
    v_txt = eng16.aggregate_verdict(dict(base16, text_state="OK"))
    v_non = eng16.aggregate_verdict(dict(base16, text_state="NO_TEXT"))
    v_bad = eng16.aggregate_verdict(dict(base16, text_state="NO_TEXT",
                                         name_reconcile={"verdict": "MISMATCH"}))
    chk("⑯ 讀不到文字層≠抽錯:文字類閘給 N/A,檔名類閘照常判(批427b-Q 實跑證據——"
        "台新AI伺服器-2317鴻海.docx 走檔名層 2317/鴻海 全對,卻因為 target_price "
        "抽不到而被判 FAIL。**讀不到 ≠ 抽錯**,那是假紅;與批422 假綠是同一枚硬幣的兩面:"
        "證據不可得時燈要給 N/A,不是給顏色。但名稱對錯是檔名層的事,無文字層照樣要紅)",
        v_txt["verdict"] == "FAIL"
        and v_non["verdict"] == "PASS"
        and v_non["gates"]["target_price"] == "N/A_NO_TEXT"
        and v_non["gates"]["zone_presence"] == "N/A_NO_TEXT"
        and v_non["gates"]["name_match"] == "PASS"
        and v_non["text_state"] == "NO_TEXT"
        and v_bad["verdict"] == "FAIL" and v_bad["gates"]["name_match"] == "FAIL",
        f"(有文字層={v_txt['verdict']} · 無文字層={v_non['verdict']} "
        f"· 無文字層但名稱對不上={v_bad['verdict']})")

    # ⑰ 檔名層:操作員 64 份真檔名回歸(批428-T1..T6)
    tf17 = TickerFilename(roster=frozenset({"2891", "6533", "1476", "6933",
                                            "2002", "2015", "2023", "2027", "2030"}))
    c17 = [
        # (檔名, 期望型別, 期望代號, 期望名稱提示, 這條在守什麼)
        ("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf", "研討會", None, None,
         "T1 2026 不在冊=年份不是代號 · T2 第N場=研討會"),
        ("凱基投顧_鋼鐵產業_2002 中鋼_20260518.pdf", "個股", "2002", "中鋼",
         "T1 對照組:2002 中鋼在冊,不可因為長得像年份被誤殺"),
        ("投資早報251209.pdf", "大盤晨報", None, None, "T2 早報"),
        ("凱基期貨晨間解盤20251205.pdf", "大盤晨報", None, None, "T2 晨間/解盤"),
        ("MS-Thermal Solutions 20251007.pdf", "產業", None, None, "T3 thermal"),
        ("UBS-Asia Hardware Insights 20251205.pdf", "產業", None, None, "T3 hardware"),
        ("凱基投顧_2891 中信金_施志鴻_20260519.pdf", "個股", "2891", "中信金",
         "T4 中信金是股票名不是券商 CTBC(原取到分析師=假紅)"),
        ("晶心科(6533,N,中立)-CTBC251208.pdf", "個股", "6533", "晶心科",
         "T4 中立是評等不是公司名(原取到評等=假紅)"),
        ("6933_AMAX-KY_個股介紹報告.pdf", "個股", "6933", "AMAX-KY",
         "T6 底線分隔:KY 後接 _ 時 \\b 不成立,整個 -KY 抓不到"),
    ]
    bad17 = []
    for fn, wk, wt, wh, _ in c17:
        pr = tf17.parse_filename(fn)
        got = (pr["kind"], (pr["tickers"] or [None])[0], pr["name_hint"])
        if got != (wk, wt, wh):
            bad17.append((fn[:26], (wk, wt, wh), got))
    chk("⑰ 檔名層對操作員 64 份真檔名回歸(批428-T:先全跑一遍才寫碼——"
        "54 對 10 錯,其中**兩筆假紅**最嚴重:中信金被當成券商 CTBC 濾掉→名稱取到"
        "分析師「施志鴻」;中立是評等卻被當公司名。九例含 T1 對照組——"
        "2026 要擋掉,但 2002 中鋼不可誤殺:年份與代號字形不可分,只能拿冊對帳)",
        not bad17 and tf17.is_valid_bare("2002") and not tf17.is_valid_bare("2026"),
        f"(不合={bad17 or '無'};2002在冊={tf17.is_valid_bare('2002')} "
        f"2026不在冊={not tf17.is_valid_bare('2026')})")

    # ⑱ 券商嚴格模式 + TP 缺席二分(批428-V)
    brd18 = BrokerRatingDict()
    page_daiwa = "Daiwa Capital Markets  Equity Research  1319 東陽"
    page_kgi = "凱基投顧 個股報告 2891 中信金 目標價 63 元"
    page_loose = "本報告提及中信金控與元大金控之持股變化"
    e18 = FirstPageEngine(auto_hub=False)
    r_nr = e18.aggregate_verdict({
        "filename_parse": {"kind": "個股"}, "tp_trigger_seen": True,
        "rating": {"canonical": "NOT_RATED"},
        "target_price": {"verdict": "FAIL", "target_price": None}})
    r_notrig = e18.aggregate_verdict({
        "filename_parse": {"kind": "個股"}, "tp_trigger_seen": False,
        "rating": {"canonical": None},
        "target_price": {"verdict": "FAIL", "target_price": None}})
    r_trig = e18.aggregate_verdict({
        "filename_parse": {"kind": "個股"}, "tp_trigger_seen": True,
        "rating": {"canonical": "BUY"},
        "target_price": {"verdict": "FAIL", "target_price": None}})
    chk("⑱ 頁面券商嚴格模式 + TP 缺席二分(批428-V:台灣金控幾乎全是券商母公司——"
        "中信2891 元大2885 富邦2881 統一1216…內文提到這些**股票**就冒充發文券商;"
        "而 Daiwa 的全名就叫 Daiwa **Capital** Markets,capital 又是群益的英文別名。"
        "另:文中一個目標價觸發詞都沒有=這份報告本來就沒有目標價(WARN),"
        "與有觸發詞卻抽不到數字(FAIL)是兩件事,混在一起錯誤矩陣會被灌滿假紅)",
        brd18.broker_normalize(page_daiwa, strict=True) == "DAIWA"
        and brd18.broker_normalize(page_kgi, strict=True) == "KGI"
        and brd18.broker_normalize(page_loose, strict=True) is None
        # 寬鬆模式**仍會誤中**——這正是要證的事。命中哪一家取決於 BROKER 冊的
        # 迭代次序(元大在中信之前),斷言綁死某一家就是在測字典順序,不是測行為。
        and brd18.broker_normalize(page_loose) is not None
        and r_nr["gates"]["target_price"] == "N/A_NOT_RATED"
        and r_notrig["gates"]["target_price"] == "WARN"
        and r_trig["gates"]["target_price"] == "FAIL",
        f"(Daiwa Capital Markets→{brd18.broker_normalize(page_daiwa, strict=True)};"
        f"內文提及金控→{brd18.broker_normalize(page_loose, strict=True)};"
        f"未評等={r_nr['gates']['target_price']} 無觸發詞={r_notrig['gates']['target_price']} "
        f"有觸發詞抽不到={r_trig['gates']['target_price']})")

    # ⑲ 六分頁矩陣:六頁齊、零 CDN、錯誤矩陣不吞紅黃、庫缺席印為何(批428-S)
    class _NoDb:
        why = "自測替身:庫不可得"
        data = {t: [] for t in DbFacts.WANT}
        cols = {t: [] for t in DbFacts.WANT}
    rep19 = [
        {"filename": "GS-2330.pdf", "filename_parse": {"kind": "個股"},
         "filename_fields": {"ticker": "2330", "broker": "GOLDMAN", "date": "2025-12-05"},
         "ticker": {"ticker": "2330"}, "broker": "GOLDMAN", "rating": {"canonical": "BUY"},
         "name_reconcile": {"verdict": "MATCH", "hint": "台積電", "official": "台積電"},
         "target_price": {"target_price": 1275.0, "tp_state": "OK"}, "text_state": "OK",
         "summary": {"verdict": "PASS", "gates": {"target_price": "PASS"}}},
        {"filename": "兆豐晨會報告.pdf", "filename_parse": {"kind": "大盤晨報"},
         "filename_fields": {}, "ticker": {}, "broker": "MEGA", "rating": {},
         "name_reconcile": {"verdict": "NO_TICKER"},
         "target_price": {"target_price": 4441.0}, "text_state": "TEXT_ONLY",
         "summary": {"verdict": "WARN", "non_stock": True,
                     "gates": {"target_price": "N/A_NON_STOCK",
                               "nonstock_tp_leak": "WARN"}}},
    ]
    h19 = render_matrix_html(rep19, _NoDb(), {"source": "自測"})
    ext19 = re.findall(r'(?:src|href)\s*=\s*["\']([^"\']+)', h19)
    # f-string 運算式不得含反斜線(Py3.11)——先取值再進格式字串
    _ntab, _ncard = h19.count('name="tab"'), h19.count('class="card"')
    chk("⑲ 四分頁矩陣:四頁齊 + 零 CDN + 紅黃不吞 + 庫缺席印為何(批428-S:"
        "操作員令「跳出四頁式、字小一點比較專業、detailed summary matrix and "
        "error matrix / basic info / financial data」。庫取不到就印為何,"
        "**不印一張空表讓人以為跑過了沒資料**)",
        all(t in h19 for t in ("DETAILED SUMMARY MATRIX", "ERROR MATRIX",
                               "BASIC INFO", "FINANCIAL DATA",
                               "STACKED MATRIX", "EXTRACTION AUDIT"))
        and h19.count('name="tab"') == 6
        and h19.count('class="card"') == len(rep19)      # 堆疊每份一張
        and 'style="width:' in h19                        # 欄寬自動最佳化
        and "http://" not in h19 and "https://" not in h19 and not ext19
        and "<script" not in h19
        and "nonstock_tp_leak" in h19 and "非個股報告卻抽到目標價" in h19
        and "庫不可得" in h19 and "自測替身" in h19
        and "代號(檔名)" in h19 and "代號(頁面)" in h19,
        f"(分頁數={_ntab};堆疊卡={_ncard};"
        f"外部資源={ext19 or '無'};{len(h19) // 1024} KB)")

    # ⑳ 工作站真 PDF 實跑四病(批429-W)
    fv20 = FieldValidation()
    # 這段是**依工作站症狀重建**的,不是庫裡的語料。庫裡那份 .txt 寫的是
    # 「同步下修目標價至208 元」(正確);操作員的真 PDF 版面把代號排到了
    # 「目標價」旁邊,文字層攤平後就成了「目標價 6873」——我看不到他的 PDF,
    # 只能照症狀把那個形狀造出來測。造的是**形狀**不是結論,誠實標明。
    t20 = ("泓德能源 目標價 6873 買進 目標價:208 元 "
           "前次 投資建議 2025.08.06: 目標價125 元 "
           "November revenue of NT$17,382mn (+6% YoY) 報告日期 20251204")
    v20, c20, _g20, _w20 = fv20.extract_target_price(t20, ticker="6873", want_detail=True)
    why20 = {c["raw"]: c["reject"] for c in c20}
    e20 = FirstPageEngine(auto_hub=False)
    band_hi = e20.fv.validate_target_price(17382.0)
    band_ok = e20.fv.validate_target_price(208.0)
    ns20 = e20.aggregate_verdict({
        "filename_parse": {"kind": "產業"},
        "target_price": {"verdict": "PASS", "target_price": 14503.0,
                         "tp_range_suspect": True}})
    chk("⑳ 工作站真 PDF 四病(批429-W:操作員拿 64 份**真 PDF** 跑 v0105,錯得有系統——"
        "W1 泓德能源(6873)→TP=6873 是**代號回音**(取第一個命中就回);"
        "外資報告的 NT$17,382**mn** 是營收也被當股價;「**前次** 目標價125」是歷史值。"
        "W2 TP 合理性閘要現價,庫不在就睡著→加一道不需現價的台股幣別合理帶 1–5000。"
        "W3 產業報告提到 3017 奇鋐**不會使它變成一份 3017 的報告**)",
        v20 == 208.0
        and any("代號回音" in (w or "") for w in why20.values())
        and any("量級後綴" in (w or "") for w in why20.values())
        and any("前次" in (w or "") for w in why20.values())
        and band_hi.get("tp_range_suspect") and not band_ok.get("tp_range_suspect")
        and ns20["gates"].get("tp_twd_band") == "WARN"
        and ns20["gates"].get("target_price") == "N/A_NON_STOCK",
        f"(選中={v20};剔除理由={sorted({w.split('=')[0] for w in why20.values() if w})})")

    # ㉑ 離線代號冊:一個缺件不得同時廢掉三個能力(批429-W4)
    off21 = NameReconciler(db="/__no_such_db__")
    roster21 = off21.code_roster()
    r21 = off21.reconcile("6873", "泓德能源")
    tf21 = TickerFilename(roster=roster21)
    chk("㉑ 庫不在時退離線代號冊(批429-W4 **這是根**:操作員的 OneDrive 副本沒有 "
        "vdf_tw_market.duckdb,庫一不在就同時廢掉三個能力——代號冊空(內文四碼全收)、"
        "名稱對帳全 UNKNOWN、TP 合理性閘拿不到現價也睡著。離線冊是庫的快照帶 asof,"
        "不是第二份實作;庫在時仍以庫為準)",
        len(roster21) > 1000
        and r21["verdict"] == "MATCH" and r21["source"].startswith("OFFLINE")
        and "OFFLINE:命中" in r21["trail"]
        and tf21.is_valid_bare("2002") and not tf21.is_valid_bare("2026")
        and "退離線冊" in off21.why.get("roster", ""),
        f"(離線冊={len(roster21)} 檔;6873→{r21['official']}/{r21['source']};"
        f"why={off21.why.get('roster', '')[-28:]})")

    # ㉒ 百分比/倍數不是價格 + 開頁旗標(批430-Y)
    fv22 = FieldValidation()
    cases22 = [
        ("我們上修目標價145(13x 2026(F)PER),潛在上漲空間23%。", "6768", 145.0),
        ("目標價:208 元 潛在上漲空間 22.7%", "6873", 208.0),
        ("Target price NT$1,275 implies 12% upside", "2330", 1275.0),
        ("目標價 潛在上漲空間 23%", "6768", None),      # 只有幅度沒有價格=誠實回 None
    ]
    bad22 = [(t[:18], w, fv22.extract_target_price(t, ticker=tk))
             for t, tk, w in cases22 if fv22.extract_target_price(t, ticker=tk) != w]
    # 斷言要指名它在測什麼:上面四例裡「23%」「13x」根本沒有觸發詞在前面,
    # 壓根不會成為候選,自然不會有剔除理由——我第一版就是這樣誤斷(又一次)。
    # 三道新剔除要各自用**會產生該候選**的句子去驗。
    probes22 = ("PT 23%", "目標價 13x 2026(F)PER", "目標價 潛在上漲空間 23%")
    why22 = {}
    for t in probes22:
        for c in fv22.tp_candidates(t, None):
            if c["reject"]:
                why22[t + "|" + c["raw"]] = c["reject"]
    src22 = Path(__file__).read_text(encoding="utf-8")
    chk("㉒ 百分比/倍數不是價格 + 開頁要操作員明打(批430-Y1:工作站 v0106 實跑 "
        "志強-KY TP=23.0,而報告寫的是「潛在上漲空間**23%**」;泓德能源 22.7、"
        "神達 41.9 同型。根因是 _TP 的 [^\\d\\-]{0,20} 會**跨過**「潛在上漲空間」"
        "去撈後面的數字。Y2:治理律零彈窗,--open 是操作員明打才開,"
        "VIA_NO_OPEN=1 照樣不開但要講清楚為何)",
        not bad22
        and any("百分比" in (w or "") for w in why22.values())
        and any("倍數" in (w or "") for w in why22.values())
        and any("講幅度不是價格" in (w or "") for w in why22.values())
        and "_open_report" in src22 and 'os.environ.get("VIA_NO_OPEN")' in src22
        and '"--open" in args' in src22,
        f"(不合={bad22 or '無'};剔除={sorted({w.split('=')[-1][:6] for w in why22.values() if w})})")

    # ㉓ 文內自洽 + adj/raw 分野(批431-Z)
    fv23 = FieldValidation()
    up23 = fv23.extract_upside("維持逢低買進,潛在上漲空間23%。")
    ip23 = fv23.implied_price(145.0, 23.0)
    e23 = FirstPageEngine(auto_hub=False)
    g_ok = e23.aggregate_verdict({"filename_parse": {"kind": "個股"},
                                  "implied_price_state": "OK"})
    g_no = e23.aggregate_verdict({"filename_parse": {"kind": "個股"},
                                  "implied_price_state": "IMPLIED_SUSPECT"})
    src23 = Path(__file__).read_text(encoding="utf-8")
    chk("㉓ 文內自洽(不靠庫不靠網)+ adj/raw 分野(批431-Z:殘留的 TP 量級可疑要現價才判得準,"
        "而①離線收盤快照從庫導出 865 檔但 3017/2891/3661/3665/2330/6768 **一檔都不在**"
        "(庫裡是 4 天 889 檔的局部資料)——出一個對所有相關個股都查不到的檔案是**假能力**,"
        "已產出已驗證已刪除;②文內現價 64 份只有 1 份疑似有,那個「股價10」其實是本益比。"
        "能做的只有第三條:報告若同時寫了目標價與上漲空間,兩者互相隱含一個價。"
        "**但那是報告日的原始價(raw),不是復權價(adj)**——操作員令「過了除權息所有股價"
        "資料都用 adj」,VDF 側是 adj,兩者差一個除權息因子,不可直接相比。"
        "覆蓋率誠實講:64 份裡只有 7 份同時有這兩個數)",
        up23 == 23.0 and ip23 == 117.89          # 145÷1.23;報告原文收盤價 118.00
        and fv23.implied_price(1.0, 20.0) == 0.83   # 粗錯:低於合理帶
        and fv23.implied_price(None, 23.0) is None
        and g_ok["gates"].get("tp_self_consistency") == "PASS"
        and g_no["gates"].get("tp_self_consistency") == "FAIL"
        and "RAW_AT_REPORT_DATE" in src23
        and "不可直接相比" in src23,
        f"(上漲空間={up23}% · 145÷1.23={ip23}(報告原文收盤價 118.00)· "
        f"粗錯 TP=1.0 上漲20% ⇒ {fv23.implied_price(1.0, 20.0)})")

    # ㉔ 雙方互取除錯法(批432):他們的 P 級不得掛綠 + 我的逐候選 trace
    fv24 = FieldValidation()
    _, _, g_v, _ = fv24.extract_target_price("目標價:208 元", want_detail=True)
    _, _, g_m, _ = fv24.extract_target_price("Price Target 650", want_detail=True)
    _, _, g_p, _ = fv24.extract_target_price("NT$1,275", want_detail=True)
    _, _, g_up, w_up = fv24.extract_target_price(
        "目標價 145 元 · 目標價 145 元", want_detail=True)       # 同值兩次=佐證
    _, _, g_dn, w_dn = fv24.extract_target_price(
        "目標價 145 元 · 目標價 999 元", want_detail=True)       # 不同值=打架
    e24 = FirstPageEngine(auto_hub=False)
    g_lo = e24.aggregate_verdict({"filename_parse": {"kind": "個股"}, "tp_grade": "P",
                                  "target_price": {"verdict": "PASS", "target_price": 1.0}})
    g_hi = e24.aggregate_verdict({"filename_parse": {"kind": "個股"}, "tp_grade": "M",
                                  "implied_price_state": "OK",
                                  "target_price": {"verdict": "PASS", "target_price": 145.0}})
    src24 = Path(__file__).read_text(encoding="utf-8")
    chk("㉔ 雙方互取除錯法(批432 操作員令「雙方檔案中找除錯的方法」:"
        "**他們有我沒有**——via-vdf-vrn 的 fin-audit.ts「一列必須是原子事實,P 級不得掛綠」,"
        "我這邊 TP 只有有值/沒值,沒人問證據多強,於是 中信金 1.0 這種孤證照樣掛 PASS;"
        "**我有他們沒有**——逐候選 trace,我看不到操作員的 PDF 就修不了看不見的東西。"
        "自審:初版只罰衝突不賞佐證,志強-KY 的 145 被三個候選同時命中又通過文內自洽"
        "卻只給 M——只罰不賞會把對的東西一起壓低,那也是一種不誠實)",
        g_v == "V" and g_m == "M" and g_p == "P"
        and g_up == "V" and "升一級" in w_up
        # 斷言又錯一次(本會期第四次):「目標價 145 元 · 目標價 999 元」帶著「元」,
        # 起點是 V 不是 M,打架降一級到 **M**。降級規則沒錯,是我算錯起點。
        and g_dn == "M" and "打架" in w_dn
        and g_lo["gates"]["tp_evidence"] == "WARN"
        and g_lo["gates"]["target_price"] == "WARN"       # P 級不得掛綠
        and g_hi["gates"]["tp_evidence"] == "PASS"        # M + 自洽 → V
        # 批432 自審:初版這行寫成 `... or True`,整條尾巴變空洞——
        # 「or True」是斷言的毒藥,前面寫再多都白寫。我抓了一整個會期的空洞斷言,
        # 結果自己在同一分鐘內寫了一個。改成真的在驗兩件事:
        and "--trace" in src24                                   # AA3 trace 在
        and src24.startswith('# -*- coding: utf-8 -*-\nr"""'),   # AA1 docstring 是 raw
        f"(V/M/P={g_v}/{g_m}/{g_p} · 同值佐證→{g_up} · 打架→{g_dn} · "
        f"P級 target_price={g_lo['gates']['target_price']} · M+自洽→{g_hi['gates']['tp_evidence']})")

    # ㉕ 合理帶壓過貨幣記號(批433-AB1;由操作員 --trace 神達 帶回的真形狀)
    fv25 = FieldValidation()
    t25 = "神達(3706) 目標價 NT$119,715 · 目標價 78 元 · 潛在上漲空間41.9%"
    v25, c25, g25, _ = fv25.extract_target_price(t25, ticker="3706", want_detail=True)
    sc = {c["raw"]: c["score"] for c in c25}
    band = [FieldValidation.TP_LO <= x <= FieldValidation.TP_HI
            for x in (1.0, 2.0, 78.0, 145.0, 1780.0, 6000.0)]
    chk("㉕ 合理帶壓過貨幣記號 + 下界 1→5(批433:操作員跑 --trace 神達,候選表直接給出答案"
        "——119,715 只因為多一個貨幣記號(+20)就贏了 78,而 78÷1.419=54.97,"
        "神達當時就在 55 上下。**六位數帶千分位的數字不是股價**,這訊號比一個「元」字強得多。"
        "批429 修過一次排序(來源>貨幣),這是同一課的第二層:合理性>貨幣記號。"
        "AB2:中信金 TP=1.0、Daiwa-3653 TP=2.0 都落在舊帶 [1,5000] 內連黃燈都沒有"
        "——券商報告給低於 5 元的目標價極罕見,下界改 5。是提醒不是判死)",
        v25 == 78.0 and sc["78"] > sc["119,715"]
        and band == [False, False, True, True, True, False]
        and fv25.implied_price(78.0, 41.9) == 54.97,
        f"(選中={v25} 級={g25};78 分={sc['78']:.0f} > 119,715 分={sc['119,715']:.0f};"
        f"隱含價={fv25.implied_price(78.0, 41.9)})")

    # ㉖ 不過度標記,也不硬壓成綠(批434-AC1/AC2)
    e26 = FirstPageEngine(auto_hub=False)
    m26 = e26.aggregate_verdict({"filename_parse": {"kind": "個股"}, "tp_grade": "M",
                                 "target_price": {"verdict": "PASS", "target_price": 1288.0}})
    p26 = e26.aggregate_verdict({"filename_parse": {"kind": "個股"}, "tp_grade": "P",
                                 "target_price": {"verdict": "PASS", "target_price": 1275.0}})
    ns26 = e26.aggregate_verdict({"filename_parse": {"kind": "大盤晨報"},
                                  "xv_zone_presence": {"verdict": "WARN"}})
    st26 = e26.aggregate_verdict({"filename_parse": {"kind": "個股"},
                                  "xv_zone_presence": {"verdict": "WARN"}})
    chk("㉖ 不過度標記,也不硬壓成綠(批434:操作員問「可以修到全部成功嗎」。"
        "誠實盤點 64 份 49 個非綠格,**約半數是我自己造的**——"
        "AC1 他們的律寫的是「**P 級**不得掛綠」只講 P,我批432 移植時讓 M 也掛黃,"
        "於是 MS-2308 TP=1288 這種乾淨抽取只因數字旁沒有「元」字就被拉黃;"
        "而英文報告本來就不寫「元」,拿貨幣記號當必要條件是中文報告偏見。"
        "AC2 zone_presence 查的是目標價/評等/券商三件套在不在本文分句裡,"
        "晨報本來就沒有這三件套,拿它來判等於問晨報「你的目標價段落呢」。"
        "修完 PASS 25→47、非綠格 49→25,**剩下的 25 格逐一核過全是真的,不壓**)",
        m26["gates"]["tp_evidence"] == "PASS"           # M 不再獨自拉燈
        and m26["gates"]["target_price"] == "PASS"
        and p26["gates"]["tp_evidence"] == "WARN"       # P 仍不得掛綠
        and p26["gates"]["target_price"] == "WARN"
        and ns26["gates"]["zone_presence"] == "N/A_NON_STOCK"
        and st26["gates"]["zone_presence"] == "WARN",   # 個股照判,不一起放水
        f"(M→{m26['gates']['tp_evidence']}/{m26['gates']['target_price']} · "
        f"P→{p26['gates']['tp_evidence']}/{p26['gates']['target_price']} · "
        f"非個股 zone={ns26['gates']['zone_presence']} · 個股 zone={st26['gates']['zone_presence']})")

    # ㉗ 多工具核對的本文(批435:先查再造——ENG072 早就做好了)
    V = SidecarBridge.verified
    sc_ok = {"body": "本文A", "plumber": {"body": "本文A"}, "footer": "頁尾小字",
             "gle": {"available": True}, "sentences": ["本文A"], "tables": [],
             "compare": {"body": {"ratio": 1.0, "verdict": "AGREE"}}}
    sc_div = {"body": "本文A", "plumber": {"body": "完全不同的字"}, "footer": "",
              "compare": {"body": {"ratio": 0.12, "verdict": "DIVERGE"}}}
    sc_part = {"body": "本文A", "plumber": {"body": "本文A 但有點不同"}, "footer": "",
               "compare": {"body": {"ratio": 0.72, "verdict": "PARTIAL"}}}
    v_ok, v_div, v_part, v_no = V(sc_ok), V(sc_div), V(sc_part), V(None)
    e27 = FirstPageEngine(auto_hub=False)
    g = {k: e27.aggregate_verdict({"filename_parse": {"kind": "個股"},
                                   "text_consensus": {"state": k}})["gates"]["text_consensus"]
         for k in ("AGREE", "PARTIAL", "DIVERGE", "NO_SIDECAR")}
    src27 = Path(__file__).read_text(encoding="utf-8")
    chk("㉗ 多工具核對的本文(批435 操作員令「至少兩種解取工具還原文字及表格後一致」。"
        "**先查再造**:VRN_ENG072 v0107 早就用三法(fitz / pdfplumber+表格 / "
        "GenericLayoutEngine)加 NLP 句級修復做完逐區 difflib 對照,產物就在 "
        "VIA_Reports/first_page_text/*.json。而本引擎從 v0101 起自己又判一次版面,"
        "下游拿到的是**沒經過核對**的那一份——這是我造出來的重複。"
        "真正的答案不是「要做多工具核對」,是「已經做了,但我沒接」。"
        "DIVERGE 判**紅**不判黃:兩個獨立工具對同一頁讀出不同的字,"
        "不是有點疑慮,是下游拿到的字可能根本不是報告寫的)",
        v_ok["state"] == "AGREE" and v_ok["body"] == "本文A"
        and v_ok["footer"] == "頁尾小字"                    # 頁尾分開,不混進本文
        and set(v_ok["tools"]) >= {"fitz", "pdfplumber", "GLE", "NLP句級"}
        and v_div["state"] == "DIVERGE" and v_part["state"] == "PARTIAL"
        and v_no["state"] == "NO_SIDECAR" and v_no["body"] == ""
        and g == {"AGREE": "PASS", "PARTIAL": "WARN",
                  "DIVERGE": "FAIL", "NO_SIDECAR": "N/A_NO_SIDECAR"}
        and "--body" in src27,
        f"(四態={v_ok['state']}/{v_part['state']}/{v_div['state']}/{v_no['state']} · "
        f"工具={'+'.join(v_ok['tools'])} · 閘={g})")

    # ㉘ 文件結構層:階層→接句→列化→表圖還原(批436 操作員全規格)
    ds28 = DocStructure()
    # ① 字體階層:最大最粗,有代號=股票名,無代號=文章主題
    t_name = ds28.tier_of(20, True, 12, "志強-KY(6768)", True, False)
    t_subj = ds28.tier_of(20, True, 12, "世足賽帶來新一輪出貨高峰", False, False)
    tiers28 = [ds28.tier_of(sz, bd, 12, "x", False, False)
               for sz, bd in ((20, False), (17, False), (14, False), (12, False), (9, False))]
    t_app = ds28.tier_of(12, False, 12, "x", False, True)
    # ② 接斷句直到句號;標題不接(標題沒有句號)
    j28 = ds28.join_body([("H2", "合併損益表"), ("BODY", "本季營收"), ("BODY", "成長 12%。"),
                          ("BODY", "毛利率下滑"), ("H3", "風險"), ("BODY", "匯率波動。")])
    # ③ 表被誤判成文字的還原:首格空著補 item
    r28 = ds28.restore_table(["          2024    2025F   2026F",
                              "營業收入   41,430  52,180  61,900",
                              "營業利益    2,100   4,980   6,310"])
    # ④ 表/圖題與來源、財報表冊(含本檔補的評價分析)
    k1, n1, d1 = ds28.caption("表 3：合併損益表")
    k2, n2, _ = ds28.caption("圖 2：毛利率趨勢")
    src28 = ds28.source_of("資料來源:公司財報,兆豐投顧預估")
    chk("㉘ 文件結構層(批436 操作員全規格:一標題 一句話 一資料分類;"
        "股票名稱與代號和文章主題**同為最大最粗**,用有沒有代號分開;"
        "**標題沒有句號**所以不參與接句;表被誤判成文字時用「連續期間」與"
        "「可對齊數字」還原,而**表頭第一格空著就先填 item**——少一格整列就對不齊;"
        "財報表分類綁 vrn_finlex STMT_ZH,冊上沒有「評價分析」故補同義字)",
        t_name == "TICKER_NAME" and t_subj == "SUBJECT"
        and tiers28 == ["H1", "H2", "H3", "BODY", "FOOTER"] and t_app == "APPENDIX"
        # 斷言又錯(本會期第五次):遇到標題前要**先把沒收尾的句子吐出來**,
        # 所以「毛利率下滑」排在「風險」之**前**。碼的次序是對的,是我寫反了。
        and j28 == [("H2", "合併損益表"), ("BODY", "本季營收 成長 12%。"),
                    ("BODY", "毛利率下滑"), ("H3", "風險"), ("BODY", "匯率波動。")]
        and r28["header"][0] == "item" and len(r28["header"]) == 4
        and all(len(x) == 4 for x in r28["rows"]) and "補 item" in r28["why"]
        and (k1, n1, d1) == ("表", "3", "合併損益表") and (k2, n2) == ("圖", "2")
        and src28.startswith("公司財報")
        and ds28.stmt_kind("評價分析")[1] == "評價分析"
        and ds28.stmt_kind("合併損益表")[1] == "損益表"
        and "VALUATION" in ds28.stmt,
        f"(最大最粗:有代號={t_name}/無代號={t_subj} · 階層={tiers28} · "
        f"表頭={r28['header']} · 冊={ds28.stmt_why[:34]})")

    # ㉙ 批437-A1/A2:文內自洽**仲裁** + 四條剔除律
    fv29 = FieldValidation()
    u_std = fv29.stated_upside("潛在上漲空間23%")
    u_unit = fv29.stated_upside("上漲空間 (%)\n13.7")            # 凱基:% 在數字之前
    u_pot = fv29.stated_upside("12M price target NT$4,200.00±% potential +27%")
    u_no = fv29.stated_upside("potential to grow 20%")            # 無正負號=不算
    c_date = fv29.doc_close("維持收盤價 May 19 (NT$)\n55.40")     # 標籤與數字之間卡著日期
    c_per = fv29.doc_close("目前評價位於股價10-11x,低於過往區間")   # 本益比不是收盤價
    c_zh = fv29.doc_close("結論與建議2025/12/03收盤價:118.00")
    t29 = ("Wiwynn NT$3,300.00 - OUTPERFORM We lift EPS and raise our TP from "
           "NT$3,600 to NT$4,200. 12M hi/lo NT$3,425.00/1,570.00 "
           "12M price target NT$4,200.00±% potential +27%")
    c29 = fv29.tp_candidates(t29, ticker="6669")
    keep29 = [c for c in c29 if not c["reject"]]
    best29 = keep29[0]
    g29, w29 = fv29.tp_grade(best29, keep29)
    rej29 = {c["raw"]: c["reject"] for c in c29 if c["reject"]}
    t29b = "Taiwan Information Technology Target price: n.a.\nShare price (21 May): TWD223.00"
    c29b = fv29.tp_candidates(t29b, ticker="6278")
    chk("㉙ 文內自洽從「驗證」升格為「仲裁」+ 四條剔除律(批437-A1/A2:批431 造了自洽,"
        "卻只拿來選完之後驗證;真正能決勝的用法是**仲裁**——報告自陳上漲空間時,"
        "目標價÷(1+空間) 必須等於同頁的現價。批429 學到來源>貨幣、批433 學到合理帶>貨幣,"
        "這是同一課第三層:**自洽>觸發詞**。CLST-6669 真文實測:4,200÷1.27=3,307≈同頁 3,300,"
        "而 3,425 是 52 週高低、3,600 是「from A to B」的 A、3,300 是現價不是目標價。"
        "另:Daiwa-6278 白紙黑字寫 Target price: n.a.,v0113 跨過去抓「(21 May)」的 21 "
        "當目標價還掛 PASS=**假綠**;擋下來後若判 FAIL 就換成假紅,所以是第三種缺席 N/A)",
        u_std == 23.0 and u_unit == 13.7 and u_pot == 27.0 and u_no is None
        and c_date == 55.4 and c_per is None and c_zh == 118.0
        and best29["value"] == 4200.0 and bool(best29.get("arb"))
        and g29 == "V" and "自洽" in w29
        and "52 週高低" in rej29.get("3,425.00", "")
        and "from" in rej29.get("3,600", "")
        and all(c["rej_code"] == "TP_DECLARED_NA" for c in c29b if c["reject"])
        and not [c for c in c29b if not c["reject"]],
        f"(上漲空間三式={u_std}/{u_unit}/{u_pot}(無號={u_no}) · 收盤價 跨日期={c_date} "
        f"本益比={c_per} 中文={c_zh} · 仲裁選中={best29['value']} 級={g29} · "
        f"n.a. 存活候選={len([c for c in c29b if not c['reject']])})")

    # ㉚ 批437-A3/A4/A5:階層來源第二階 + 期間邊界 + 有表頭無資料列不是表
    ds30 = DocStructure()
    per30 = [ds30._PERIOD.findall(x) for x in
             ("目標價125 元", "2024 2025F 2026F", "民國 114 年", "1141202", "股價118")]
    # 工作站那一行:A4 之後「目標價125」不再算民國年,期間只剩兩個 → 根本不成表頭
    r30a = ds30.restore_table(["投資評等目標價 前次投資建議2025. 08. 06: 目標價125 元 報告日期:2025. 1"])
    # 真的有三個期間、卻一列資料都沒有 → 這才是 A5 要擋的那一種
    r30 = ds30.restore_table(["   2024   2025F   2026F"])
    r30b = ds30.restore_table(["          2024    2025F   2026F",
                               "營業收入   41,430  52,180  61,900"])
    none30 = ds30.role_tiers("本文", None)      # 橋缺席要留因由,不得靜默
    # role_why 會被下一次呼叫清掉,所以**當場**收走。
    # (本會期第七次斷言寫錯就是錯在這:我在 got30 之後才讀 role_why,早就被重設了。)
    why30 = ds30.role_why

    class _StubHub:
        @staticmethod
        def roles(t):
            return {"records": [{"role": "primary_body", "source_text": "本季營收成長。"},
                                {"role": "header_footer", "source_text": "第 1 頁 共 8 頁"},
                                {"role": "navigation", "source_text": "www.example.com"},
                                # 免責聲明是附錄起點——它之後一律 APPENDIX,
                                # 即使角色層說那是本文(斷言第六次寫錯就是錯在這:
                                # 我以為它會停在 FOOTER)
                                {"role": "primary_body", "source_text": "免責聲明 本報告僅供參考"},
                                {"role": "primary_body", "source_text": "分析師聲明"}]}

    got30 = ds30.role_tiers("x", _StubHub())
    chk("㉚ 階層來源第二階=NLP 角色層 + 期間邊界 + 有表頭無資料列不是表(批437-A3/A4/A5:"
        "A3 SUP_MDL744 自己的註解寫著「VRN 引擎直接消費的四道」,而 v0113 只消費了 "
        "text_processor() 一道,layout()/roles() 掛在那裡沒人接——批435 那一課的第三次。"
        "角色層給不了字級,但分得出本文/頁尾/導覽,所以沒 gle 不再整份當本文;"
        "橋缺席要把**為何**留在 role_why,不得靜默退後備(批426-B/批419e 同一病)。"
        "A4 裸民國年 1[0-2]\\d 沒有邊界,把「目標價**125** 元」當成民國 125 年,"
        "一行湊到三個期間就印出一張沒有資料列的假表——分不開就不該猜,"
        "只認「民國 114」與七碼日期 1141202。A5 v0113 印「無表格訊號」卻同時印表頭,自打嘴巴)",
        per30[0] == [] and len(per30[1]) == 3 and per30[2] == ["民國 114"]
        and per30[3] == ["1141202"] and per30[4] == []
        and r30a["header"] == [] and r30a["why"] == "無表格訊號"
        and r30["header"] == [] and "不是表" in r30["why"]
        and r30b["header"][0] == "item" and len(r30b["rows"]) == 1
        and none30 is None and "未掛載" in why30
        and got30 and [t for t, _ in got30["tiered"]] == [
            "BODY", "FOOTER", "FOOTER", "APPENDIX", "APPENDIX"]
        and "角色層" in got30["why"],
        f"(期間:目標價125→{per30[0]} 表頭→{len(per30[1])} 民國→{per30[2]} "
        f"七碼→{per30[3]} 股價118→{per30[4]} · 工作站那行→{r30a['why']} · "
        f"橋缺席因由={why30} · "
        f"只有表頭→{r30['why'][:26]} · "
        f"角色層→{[t for t, _ in (got30 or {'tiered': []})['tiered']]})")

    print(f"  [計] 三十檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== {ENGINE_NAME} {ENGINE_VERSION} · 二十八檢自測"
              "(零網路;零觸碰正本;含 v0101 實測缺陷對照)===")
        return selftest()
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
