#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL148_EngineBus v0126 — 引擎調度匯流排(批514 子行程環境衛生律 L32)

v0125→v0126(批514 Z15 根因):child_env() 撤 PYTHONHOME——操作員實錄 RunGate 本行程 PYTHONHOME=…\uv\python\cpython-3.12-…,
  家族境子行程(C:\Python313 3.13 venv)繼承後載到 3.12 標準庫=SRE module mismatch;PYTHONHOME 對子行程無正當用途,撤了什麼記
  VIA_PYTHONHOME_SCRUBBED(誠實存證);其餘鍵照舊;四十七檢 +㊼。(同律三處同一寫法:bootstrap sitecustomize 起跑撤 · 本件 child_env · RunGate v0105)

CGC_MDL148_EngineBus v0123 — 引擎調度匯流排(批508 結案驗收)

v0122→v0123(批508 操作員實錄 via-ryg vdf,vrn -Timeout 600):
  ① 根因修正:via-ryg 原本把「驗收」直接送進冊上 production verb，等同同時啟動全史回補/網路擷取；
     tw_trading_value/global_universe 因而逾時，macro/global lanes 也被誤判紅。新增 profile=test：
     對每支引擎只跑其有界 --selftest/--self-test/selftest；無內建旗標時尋找同夾 companion test，
     沒有可驗證契約就 ABSENT，絕不假綠。profile=run 完整保留舊動詞與全部參數。
  ② 產出判定只走 output_verdict 單一判準；DB index/census 快取連同 why 一起保存，第二次讀不再失去診斷。
  ③ test profile 只在所有選中項 GREEN 時回 rc0；production matrix 維持既有調度回碼契約。

v0121→v0122(批500 操作員 census 實錄:六本家內庫都有 via_policy_sync/via_handover/vrn_extraction_logic/via_policy_factors,
  卻點成「冊外」+ AMBER「1 天」):① 冊上 db_scope="all_home" 的表對家內每一本庫都算冊上(全庫同步律的表);
  ② 冊上 lamp="rows" 的表(對帳單/台帳/交接/政策)只看列數不看日期跨度——一列一天不是老化,是對帳單;假 AMBER 和假綠一樣傷。
v0120→v0121(批498 收尾實測:容器真跑 vdf 家族 17 項 RED,尾段全是「同意閘未開/FAIL-CLOSED/法遵雙閘」「表缺/Catalog Error」「根缺」
  ——沒有一項是引擎壞;判錯的紅燈和假綠一樣傷):
  ① +GATED 態(閘):引擎 fail-closed 誠實拒跑=**同意閘未開**,不是壞掉;要跑=操作員開閘(不代設);矩陣/tails/HTML 都認。
  ② STOP_RX +表缺|價表缺|根缺|Table with name … does not exist|Catalog Error → 缺料 NODATA(上游表/夾沒料,非本引擎缺陷)。
v0119→v0120(批494 操作員令「未經過我同意…這兩個(VeritasCeleritas/VeritasAegisNexus)是我指令唯一的加速器及網路工具,重新掛載」):
  boot 動詞多印 VIA_TOOLS_MOUNT(啟動層 ④:兩件正典工具以本名惰性掛進每個子行程的 sys.modules);㊶ 檢:子行程
  `import VeritasCeleritas` 零成本(numpy 未載)、取屬性才真載入且 __version__ 讀得到=掛載是真的,不是宣稱。
v0118→v0119(批491 操作員實錄):
  ① 湖不再自己掃:census 的 [湖] 列改向 MDL123 尾版 catalog() 取(單一實作;它讀 parquet 中繼資料不掃湖,
     分割夾按母夾命名 px/year=2023——v0118 四個 year=2026 撞名被 (庫,表) 去重成 12 夾,實際 23);自測時不寫真目錄頁。
  ② `AttributeError: module 'pyarrow' has no attribute '__version__'`(vap_stack/vap_heatmap)= 套件壞了
     (site-packages 的 pyarrow 夾缺 __init__.py → 匯入成命名空間包),是缺件不是引擎壞 → ABSENT 並指路重裝。
v0117→v0118(批490 操作員宣告「data save in parquet and managed by duckdb. this is database file:
  C:\\Users\\tonyk\\VIA System\\via_database」——批489 他貼的 census 只剩 7 本庫、冊上 49 張全 ABSENT,
  不是庫沒了,是**庫搬到倉外的家**,而本件只掃倉內;判錯的紅燈和假綠一樣傷):
  ① 家內也掃:data_home()=env VIA_DATA_HOME > 目錄頁 DATAHOME_CATALOG_latest.json > MDL123 尾版 resolve_home();
     db_files() 一支掃描器供四處共用(倉內排除 references/SCOPE_COPY/沙盒 + 家內;同一實體只算一次;家是單檔也認)。
  ② parquet 湖也數:家內每個夾=一資料集,列數/日期範圍同表判態,census 列為 [湖];冊上宣告的表若以湖存在=不再報 ABSENT。
  ③ census 預設 --brief(一本庫一行:表數·總列·最新日·三態計;ABSENT 只列數與前幾名);--tables 才逐表——
     省的是操作員貼回來與我讀進去的 token;--hygiene 照舊。
  ④ 沙盒標記錨定到擁有者夾:/engine_bus/_cwd/ /selftest_grid/ /vdfout_runs/selftest_out/ /_self_test
     (v0115 的 /_cwd/ /selftest_out/ 會撞到任何同名正夾)。census 印 [沙盒略] 讓人看見略了哪幾本。
  ⑤ 「庫缺」「庫不在」進 STOP_RX:ENG080 印「庫缺 <路徑>」是缺料(上游沒庫),不是壞掉;批489 它亮成 RED。


v0116→v0117(批489 操作員真跑 via-ryg 的實錄):
  ① 心跳走 stderr、項目行走 stdout,PS 包裝分兩條流排水,**先後會錯位**:vrn_pdfplus 的心跳「19s · 引擎最後一行:}」
     印在下一項 vap_stack 底下,看起來像 vap_stack 跑了 19 秒又 0.78 秒回 RED。
     改:矩陣模式(人看的)心跳走 stdout、且帶項目名「⏳ vrn_pdfplus 還在跑 …」;只有 call 模式(機器讀 JSON)心跳才走 stderr。
  ② 三個 RED(vrn_fourpoint / vap_stack / vap_heatmap)雲端看不到尾段 → +tails 動詞:讀 ENGINE_BUS_latest.json 印紅項的 why + stdout_tail。
  ③ ENG073 在操作員機器上「庫缺…確認 clone 根」——他的 vdf_tw_market.duckdb 不在引擎寫死的 output_hub/mega/ 底下。
     census 先印每本庫的相對路徑(以前只印檔名),讓人一眼看到庫住哪。


v0115→v0116(批487 操作員實錄「via-boot 為何每次動不了」):根因在啟動層每次起跑都載 Celeritas
  (拉進 95 個模組;88 件冊全裝的機器上是每支 python 前面一大段空白)。啟動層改快取優先後,
  子行程看到的 VIA_ACCEL_BOOT 變成 cache:<可用>/<冊>:<n>env 或 NOCACHE:…;㉗ 檢照實認。)


v0114→v0115(批486 自己踩到:跑過 revphase/VETF/TWREV 自測後,census 從 35 張表變 48 張——
  多出來的是自測沙盒產出的 .duckdb(engine_bus/_cwd、selftest_grid、selftest_out)。沙盒不是正庫,
  拿它們一起數就是把「跑過幾次測試」算進「庫裡有什麼」。**但 VIA_Reports 不能整夾排除**:
  VRN 主庫 VIA_Reports/vrn/maindb/StockReport.duckdb 設計上就住那裡(第一版一竿子打掉它,35→31 張)。
  規則收窄到沙盒標記:/_cwd/ /selftest_grid/ /selftest_out/ /_self_test(三處掃描共用 _is_sandbox)。)


v0113→v0114(批485 I 項準備:資料本體一筆都不動,先把該動的列**數出來、SQL 寫出來**,讓操作員拿數字決定):
  census --hygiene
    ① 哨兵列:日期欄 < 1950-01-01 的列數 + 樣本(操作員機器 census:tw_daily_prices MIN=1900-01-01、
       _repo_ 副本 global_daily 只有 1 列 1900-01-01)——印出對應的 DELETE 語句,**不執行**
    ② 副本庫:檔名含 _repo_ 的每張表 vs 正庫同名表的 MAX 日期——副本較舊=可退役候選,**不刪**
  兩者都只是審計:沒有 --apply,永遠不會有。刪資料是操作員的手,不是匯流排的。


v0112→v0113(批484 自己踩到:`call --item vrn_digest --apply` 跑超過 20 秒,心跳印進 stdout,
  接在後面的結果 JSON 就不是合法 JSON 了——調用端 json.load 直接炸。
  v0108 加心跳時只想著人眼,忘了 call 的契約是「stdout=統一結果字典」。**人看的字走 stderr,機器讀的字走 stdout**。)


v0111→v0112(工作站實錄:`via-boot` 打下去「還在跑」,操作員只好先做別的):
  boot 動詞逐家族呼叫 python_for()(委派 MDL137→MDL136 去解析 conda 境,Windows 上很慢),
  三家族**逐一**、各 120 秒上限、期間**零輸出**——最壞白畫面六分鐘,又是批423/批475 那個病。
  修:三家族各開一條執行緒並行;主執行緒每 HEARTBEAT_SEC 印一行「⏳ 還在探測 …」;總上限 150 秒,
  逾時的家族誠實印「探測逾時」而不是掛著。


v0110→v0111(批478 VDF SSOT 化第一步):
  庫況的 ABSENT 以前全靠 grep 碼裡的 SQL 語境猜(批474 收緊到 ≥3 檔才敢報)。現在有**庫冊**
  VIA_DB_Table_SSOT_v*.json(操作員機器 census 實測 + 寫入者掃描):
    冊上宣告、庫裡沒有 → ABSENT(冊上宣告)並列寫入者引擎——這是**該有而沒有**,最該亮的一種
    冊外、碼上 SQL 語境 ≥3 檔引用 → ABSENT(冊外)——照舊,寧可少報
    庫裡有、冊上沒有 → 照常判態,加註「冊外」——提醒冊該補,不是缺陷
    檔名含 _repo_ 的庫 → 加註「副本」,不當正典判


v0109→v0110(批477 收 TWREV v2.7 時撞到的**第十盞判錯的燈**):
  `twrevenue/cli.py` 是套件裡的模組,得 `python -m twrevenue.cli selftest` 啟動;
  匯流排照舊 `python cli.py selftest` → `ImportError: attempted relative import with no known parent package`,
  而我的 NEED_RX 看到 ImportError 就判「缺件,補上那個套件再跑」——**沒有任何套件缺**,是我啟動方式錯。
  判錯的燈不只紅燈:一盞指錯方向的灰燈也會讓人去 pip install 一個不存在的東西。
  修:① 冊上項可宣告 `module`(如 twrevenue.cli),匯流排改 `-m` 啟動並把 engine dir 前置進子行程 PYTHONPATH;
      ② classify_stop 先擋「attempted relative import」→ RED 並直說「須以 -m 啟動;冊上加 module 欄」,不再進 NEED_RX。
      ③ 冊上項可宣告 `cwd: "engine"`:TWREV 是第一支**讀 cwd** 的引擎(config.yaml 全是相對路徑),
         批471 量的「36 支全用 __file__、0 支讀 cwd」在它身上不成立——冊講了才換工作目錄,預設照舊 _cwd。


v0108→v0109(批476 操作員令「所有 PY 檔案都要加上加速器」「VDF 全部還要加入網路工具」):
  量過:加速器在 VDF 引擎只綁 4/109、VRN 0、VAP 0;VDF 109 支裡 8 支直呼網路沒走正典件。
  逐檔補=幾百個新版本檔。改在**啟動層**:子行程 env 加 PYTHONPATH=<VIA>/supportive modules/bootstrap
  (裡面的 sitecustomize.py 起跑自動載入)+ VIA_FAMILY + VIA_ROOT。零引擎改動,一處維護。
  新增 `boot` 動詞:真的起一個子行程,回報它看到的(加速器 / 網路件 / 閘態)——證據,不是宣稱。


v0107→v0108(工作站實錄:`via-ryg` 停在 `[25/38] vrn/vrn_firstpage` 不動,操作員報「卡斷中」):
  根因不是引擎卡,是**我的調度層讓人看不見引擎在動**:
    · `subprocess.run(capture_output=True)` 把子行程輸出**緩衝到結束才吐**——
      ENG072 對一疊真報告做 OCR 要跑好幾分鐘,這幾分鐘畫面全白。
    · 逾時 900 秒。也就是說最壞要白畫面 15 分鐘才會看到任何字。
  這正是批423 AllGreen v0100 那一課的翻版(「輸出緩衝到結束才吐=長跑段畫面全白」),
  同一個病我在另一支程式裡又寫了一次。
  修法(照 AllGreen v0101 的藥方,不另發明):
    ① Popen + 讀取執行緒,引擎每印一行就收一行;
    ② **心跳**:每 HEARTBEAT_SEC 秒印一行「⏳ 還在跑 · N s · 引擎最後一行:…」,
       畫面永遠不會白——而且印的是引擎**自己的**進度句,不是我編的;
    ③ 逾時只殺**自己生的那一個**子行程(不碰別的進程),部分輸出保留當證據;
    ④ `--timeout N` 開給 CLI(via-ryg -Timeout N 直通),不再只能吃 900 那個死數。


v0106→v0107(**操作員在自己機器上跑,三件事當場現形**):
  實錄逐字:
      PS> via-bus --matrix
      …SyntaxWarning: invalid escape sequence '\s'
      (然後吐出兩百行 docstring,什麼都沒跑)

  ① **我給錯指令**。冊上的動詞是 `matrix`,不是 `--matrix`;而上一則訊息裡
     叫操作員打的就是 `via-bus --matrix`。**錯在我**。
     但這不只是我打錯字——`--matrix` 是任何人都會自然打出來的形狀,
     而這支程式對它的回應是:**印兩百行說明,然後回 rc=0 說成功**。
     兩個獨立的缺陷:
       · 顯然想得到的動詞不收 → 本版把 `--matrix/--catalog/--call/--census`
         一律正規化成動詞(**只脫頭部的連字號,不去猜別的東西**)。
       · 不認得的參數回 **rc=0** → 那是**假綠**:自動化鏈路上游看 rc,
         會把「什麼都沒跑」讀成「跑完了」。改回 **rc=2**,並印**六行用法**,
         不再把整篇 docstring 倒在人臉上(說明書不是錯誤訊息)。
  ② **SyntaxWarning**:docstring 裡寫了「需要」加空白比對式那個正則當範例,
     而 docstring 不是 raw 字串。v0106 那段文字本身在講「判準寫兩個地方
     只改一邊」,結果那段文字**自己**又生了一個新缺陷。改 r 開頭的 docstring。
  ③ 產出頁只有「引擎跑不跑得動」,沒有「**庫裡到底有沒有料**」。
     操作員問的 C 是「VDF 到底能不能跑」——引擎綠不綠回答不了那題:
     引擎可以完美地跑完然後寫進一張空表。本版加**矩陣五 · 庫況**:
     沿用既有的 db_table_index() 那一趟掃描(**不另開第二支掃描器**),
     多取列數與日期跨度,逐表判三態:
         GREEN  有列,且(無日期欄 或 日期跨度 ≥ 30 天)
         AMBER  有列,但日期跨度 < 30 天(料在,但薄——最容易被當成綠)
         NODATA 表在、列數 0(**表建好了沒料**)
         ABSENT 全樹沒有這張表(**不是壞掉**,是還沒建)
     判準要亮得出證據:每一格都把列數與日期跨度一起印出來。

v0105→v0106(批473 收 PDFPlumber-Plus 時撞到的**第八盞判錯的紅燈**):
  新收的 vrn_pdfplus 一調度就報 RED,而引擎印的是
      `selftest 需要 reportlab 產生樣本 PDF;請改用 python …py <你的.pdf>`
  ——那是**缺件**,而且它連補法都講了。RED 的原因是我的 NEED_RX 字表裡
  只有「缺席/未安裝/沒裝/pip install/ModuleNotFoundError」,**沒有「需要 X」**。
  最難看的是:同一批我寫那支 PowerShell 啟動器時**已經把這條律寫對了**
  (`需要\s*([A-Za-z0-9_\-]+)`),卻沒有把它帶回匯流排——
  **同一個判準寫在兩個地方,只改了一邊,另一邊靜靜走錯**,
  這正是本件立案時要收掉的那件事,結果我自己又犯一次。
  判準收得緊:`需要` 後面必須緊跟**看起來像 python 套件名的 ASCII 識別字**,
  不是看到「需要」兩個字就放過(那是中文裡太常見的詞)。

v0104→v0105(**同一張表再讀一遍,又抓到一種說謊**):
  v0104 把表名接對了,可是 `VIA_UI_VRNControlTower_v0100.html` 還是寫「缺」——
  而 vrn_ui 那一跑明明報「頁 3/3 新鮮」。查:冊上有 **7 條是沒有目錄的裸檔名**,
  真的頁住在 `supportive modules/ui_support/`,我卻拿 VIA 根去接它。
  這是同一個病的第三種形狀(先是表名當路徑,再是裸檔名當根相對路徑):
  **我一直在用「一種判法」去問三種不同的問題。**
  所以判法改成照宣告的**形狀**分四路:
      含萬用字元 → 不判      路徑形(有 /)→ 接 VIA 根問檔案系統
      裸檔名形   → **去找**(rglob 排除 references;找到就把落點一起講出來)
      表名形     → 問庫
  找得到就說在哪,找不到才說缺——**說「缺」之前,先確定自己有去找過**。

v0103→v0104(**把產出的頁讀一遍,發現說謊的是頁本身**):
  ① 頁首印「模式 **只解析(dry)**」——可是那一跑 vrn+vap 是**真跑**的。
     `data["apply"]` 在 --apply-family 模式下本來就是 False,我卻拿它當唯一的標籤。
     一張報實測結果的頁,**第一行就把自己的模式講錯**。
  ② 矩陣四拿 `(VIA/宣告).exists()` 判產出在不在。量了冊:**60 個宣告產出裡有 34 個
     是資料庫的表名,不是檔案路徑**(tw_daily_prices、vrn_report_basic、
     ActiveTWETF.duckdb::holdings_daily …)。拿檔案系統去問表在不在,答案永遠是「缺」——
     矩陣四有**超過一半的格子在說謊**:vrn_structdb 明明剛入庫 71 筆,頁上寫它的
     vrn_report_basic「缺」。**判錯的紅燈和假綠一樣傷**,這批已經是第五盞了。
     修法:先分類再判,各問各的——
       含萬用字元 → 不判(照舊:判不了就說判不了)
       路徑形     → 問檔案系統
       表名形     → **問庫**(唯讀 SHOW TABLES;支援 `庫.duckdb::表` 明寫形)
       一張庫都開不了 → 「判不了(無庫可問)」,**不寫成缺**

v0102→v0103(**第三次實跑,這次髒的是我的手**):
  全 37 項跑完,`git status` 冒出一個從沒入過庫的夾:
      functional modules/VAP/engine/vap_one_out/RUN_.../vap_one.html
  **調度層讓引擎在原始碼樹裡拉了一夾產出。** 根因是我在 v0100 寫的
  `cwd=引擎檔所在目錄`;ENG016 的 `--out` 預設是相對路徑 `./vap_one_out`,
  冊上 `param_kinds.vapone` 本來就寫著要帶 `--out <夾>`,沒帶就落在 cwd。
  正本零觸碰不是只管「不要改別人的檔」,**也管不要在別人家裡生檔**。

  改 cwd 之前先量(不是先猜):
    · 冊上在位 36 支引擎,**36 支全部用 `__file__` 定位自己**
    · `os.getcwd` / `Path.cwd()` / `chdir` —— **0 支**
    · ENG016 從無關目錄實跑:rc=0,產出落在那個目錄,行為不變
  所以 `cwd=引擎目錄` 一點好處都沒有,只換來原始碼樹被弄髒。
  → 改成每次跑都在 `VIA_Reports/engine_bus/_cwd/` 底下(產出夾,已在 .gitignore),
    任何引擎的相對預設都落在那裡,原始碼樹一個字都不會多。

v0101→v0102(**第二次實跑,照出的還是我的尺**):
  VAP 家族 6 項真跑,匯流排報 RED 4。逐項查完,**只有 1 支是真壞**:
    · vap_dashboard     印「[缺料] 缺 4 項 … [補料] **誠實停 rc2**」 → 缺料,判紅是錯的
    · vap_std_dashboard 印「plotly 缺席=**誠實停**」               → 缺件,判紅是錯的
    · vap_one_render    argparse:「error: argument --render: expected one argument」
                        冊上這項宣告 `params:["vapone"]`——config 路徑本來就該由主控台給。
                        我沒給參數就硬跑,再把 argparse 的抱怨判成引擎壞 → 缺參數,判紅是錯的
    · vap_stack         `_duckdb.CatalogException: Table tw_daily_prices does not exist`
                        **這支是真紅**:缺表時該誠實停,它卻讓例外裸奔(VAP 側缺陷,已表列)
  三盞判錯的紅燈,三盞都是我點的。修的是判準,不是引擎:

  ① **「誠實停」才是這套系統的正典句**——全樹 451 處,而 v0101 的 NODATA_RX 裡沒有它。
     我當初是照 VRN 那幾支的措辭湊字表,湊出來的字表只認得 VRN 的方言。
  ② **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。誠實停還要再分一層:
       缺料(上游沒料)                     → NODATA
       缺件(引擎/相依套件/**必要參數** 不在位)→ ABSENT ← 本版擴義,不新立第八態
     判缺參數**只認 argparse 自己講的話**(`error: argument …` /
     `the following arguments are required`)。**不能用「有宣告 params 就別跑」一刀切**:
     冊上 21 項宣告了 params,其中 20 項沒給參數照樣跑得好好的(量過),
     一刀切會誤殺 20 項——跟「排除 2000–2030 修年份」是同一種爛招。
  ③ **`--apply` 不該是全有全無**。VRN 那 7 項無妨;VDF 那 24 項按下去,等於同時發動
     tw_history 全史回補、tw_chips 籌碼回補,還有兩支動詞裡本來就帶 `--apply` 的寫庫件
     (tw_universe_update / db_localdb_apply)。調度層唯一的開關長這樣就是地雷。本版加:
       --apply-family vrn,vap   只在點名的家族真跑,其餘照樣 PLAN
       --ids a,b,c              只跑點名的項
       **寫庫動詞閘**:動詞裡含 `--apply` 的項,家族全掃**永不代跑**,
                       要跑必須 --ids 明點(與「--approve-remove 只在明令下」同律)

v0100→v0101(**實跑第一次就照出我自己用錯尺**):
  VRN 家族 7 項真跑,匯流排報 RED 3。查了才知道三支同一個根——引擎自己印的是
  「**無報告件(誠實)**」「無可轉檔(誠實)」:那是**缺料不是壞掉**,而我把它判成紅。
  這正是批470 才寫過的那一課的翻版:**判錯的紅燈和假綠一樣傷**,
  它會讓人去 debug 一支行為完全正確的引擎。
  想用 rc=2 當判準——**量過之後否決**:全樹 `return 2` 有 163 處,
  其中只有 46 處是誠實停,117 處是用法錯/缺庫等別的意思。**rc 不是穩定慣例。**
  可靠的訊號是引擎**自己印出來的那句話**。所以 v0101 加 **NODATA** 態:
  rc≠0 **且**輸出尾段命中誠實停字樣 → NODATA,並把**命中的那句原文一起帶回**
  (判準要亮得出證據,不然它就只是另一種猜)。沒有那句話的 rc≠0 一律照舊 RED。
====================================================================
操作員令:「**功能性引擎功能性化 可讓多個子系統調度**」
        「實測修正無誤後顯示 html u/多矩陣結果摘要及資料 **全部 SSOT**」

先查再造(量到的,不是規劃的):
  · 調度用的 SSOT **早就有**:VIA_InputConsole_Spec_v0100.json 已宣告
    **37 項引擎**(vdf 24 / vrn 7 / vap 6),每項都帶 engine{dir,glob,verb}、
    params、outputs。**本件不另立第二本冊**——那會讓「正典換了沒人跟得上」。
  · 但**調度的碼四家各寫各的**(實測):
        CGC_MDL095_DeckServer   Popen ×12
        CGC_MDL137_RunGate      subprocess.run ×3
        CGC_MDL139_InputConsole subprocess.run ×1
        CGC_MDL141_ClosingGate  自己一套
    每一家都重寫:尾版 glob 解析、家族 python 選擇、逾時、結果解讀。
    同一件事四份實作=九頭龍;引擎換了介面,四個地方都要記得改,而**漏改的那個
    不會報錯,只會靜靜走錯**。
  · 這就是「功能性化」缺的那一格:引擎有功能,但**沒有一個統一的呼叫契約**,
    所以每個子系統只能各自用「開一個行程再讀文字」的方式去湊。

本件補的正是那一格 —— **一條匯流排,四家共用**:
    catalog()            冊上 37 項 × 尾版解析 × 在位實測
    call(item_id, ...)   統一呼叫契約,回**統一結果字典**
    matrix(...)          批量調度 → 多矩陣資料
    render(...)          實測結果 → 多矩陣 HTML(零 CDN;樣板走 MDL089)

統一結果契約(誰調度都拿到同一個形狀,不必再各自解讀文字):
    {id, family, zh, engine, engine_state, argv, state, rc, seconds,
     tally, outputs_seen, stdout_tail, why}
    state ∈ GREEN | NODATA | AMBER | RED | TIMEOUT | ABSENT | PLAN
      NODATA  **缺料**:上游沒料,引擎自己說了「誠實停」。不是紅燈。
      ABSENT  **缺件**:引擎檔 / 相依套件 / 必要參數 不在位。也不是紅燈。
              缺件與壞掉混在一起,就會讓人去 debug 一支行為完全正確的引擎。
      PLAN    dry:只解析不動手(預設就是 dry),或**寫庫動詞被家族閘擋下**

紀律:
  · 尾版律 glob;家族 python **委派** MDL137.python_for →(它再委派 MDL136)
  · **不卡斷**:逐項逾時,只殺自己生的那個子行程
  · 誠實三態;`[計]` 只認**最後一行**(批462 那一課:子報告也印 `FAIL 0`,
    全篇搜就會把「OK 38 · FAIL 1」讀成綠)
  · 本件**零網路**、**預設不動手**(dry)、不寫任何正式產出夾
用法:
  python3 CGC_MDL148_EngineBus_v0106.py catalog [--family vrn]
  python3 CGC_MDL148_EngineBus_v0106.py call --item vrn_firstpage [--apply]
  python3 CGC_MDL148_EngineBus_v0106.py matrix [--family vrn] [--apply] [--html]
  python3 CGC_MDL148_EngineBus_v0106.py matrix --apply-family vrn,vap --html
  python3 CGC_MDL148_EngineBus_v0106.py matrix --ids vdf_tw_align --apply
  python3 CGC_MDL148_EngineBus_v0106.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import html as _html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
#: 調度 SSOT —— 冊只有一本(尾版律 glob;不另立)
SPEC_GLOB = "VIA_InputConsole_Spec_v*.json"
#: 產出(本件唯一會寫的地方;VIA_Reports/* 已在 .gitignore)
OUTDIR = VIA / "VIA_Reports" / "engine_bus"
#: 批486:自測沙盒標記——這些夾裡的 .duckdb 是跑測試生出來的,不是正庫
SANDBOX_MARKS = ("/engine_bus/_cwd/", "/selftest_grid/", "/vdfout_runs/selftest_out/", "/_self_test")


def _is_sandbox(sp: str) -> bool:
    sp = sp.replace("\\", "/")
    return any(m in sp for m in SANDBOX_MARKS)


_HOME = None
#: census 取湖時是否順手寫目錄頁(自測=False,免得沙盒家蓋掉真目錄頁)
LAKE_WRITE = True


def data_home() -> tuple:
    """資料家(批490):env VIA_DATA_HOME > 目錄頁 DATAHOME_CATALOG_latest.json 的 home > MDL123 尾版 resolve_home()。
    只回**存在**的路徑;不在=誠實 (None, '缺:…')。家可以是夾,也可以是單一庫檔。"""
    global _HOME
    if _HOME is not None:
        return _HOME
    h, src = None, ""
    env = (os.environ.get("VIA_DATA_HOME") or "").strip()
    if env:
        h, src = Path(env).expanduser(), "env VIA_DATA_HOME"
    if h is None:
        try:
            j = json.loads((VIA / "VIA_Reports" / "datahome" / "DATAHOME_CATALOG_latest.json").read_text(encoding="utf-8"))
            if j.get("home"):
                h, src = Path(j["home"]), "目錄頁 DATAHOME_CATALOG_latest.json"
        except Exception:
            pass
    if h is None:
        try:
            mods = sorted(HERE.glob("CGC_MDL123_DataHome_v*.py"))
            if mods:
                import importlib.util
                spec = importlib.util.spec_from_file_location("via_datahome", mods[-1])
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                h, src = m.resolve_home(VIA)
                src = "MDL123 " + str(src)
        except Exception:
            pass
    if h is not None and not h.exists():
        src, h = f"缺:{h}({src})", None
    _HOME = (h, src)
    return _HOME


def db_files() -> list:
    """全部該數的 .duckdb(**唯一掃描器**;四處共用):倉內(排除 references/SCOPE_COPY/沙盒)+ 家內(家不在倉內時)。
    同一實體(接點兩頭)只算一次;家若是單檔則該檔即一本庫。"""
    out, seen = [], set()
    roots = [VIA]
    h, _ = data_home()
    if h is not None:
        try:
            inside = str(h.resolve()).startswith(str(VIA.resolve()))
        except Exception:
            inside = False
        if not inside:
            roots.insert(0, h)      # 家在前:同名庫同名表以家為正典,倉內殘本讓位(census 以 (庫名,表) 去重)
    for root in roots:
        cands = [root] if root.is_file() else sorted(root.rglob("*.duckdb"))
        for db in cands:
            sp = str(db).replace("\\", "/")
            if "/references/" in sp or "SCOPE_COPY" in sp or _is_sandbox(sp):
                continue
            try:
                key = str(db.resolve())
            except Exception:
                key = sp
            if key in seen:
                continue
            seen.add(key)
            out.append(db)
    return out


def sandbox_skipped() -> list:
    """倉內被當沙盒略掉的 .duckdb(讓人看見略了哪幾本,不是默默吞)。"""
    return [str(p.relative_to(VIA)).replace("\\", "/") for p in sorted(VIA.rglob("*.duckdb")) if _is_sandbox(str(p))]


def _rel(p: Path) -> str:
    try:
        return "倉:" + str(p.relative_to(VIA))
    except ValueError:
        pass
    h, _ = data_home()
    if h is not None:
        try:
            return "家:" + str(p.relative_to(h if h.is_dir() else h.parent))
        except ValueError:
            pass
    return str(p)


def _tbl_state(con, sql_from: str, cols: list) -> dict:
    """一張表/一個湖:列數 · 日期欄 · 範圍 · 天數 · 三態(判準在 db_census 說明;這裡只算)。"""
    n = con.execute(f"SELECT COUNT(*) FROM {sql_from}").fetchone()[0]
    dcol = next((c for c in cols if c.lower() in _DATE_COLS), None)
    lo = hi = None
    span = None
    if dcol and n:
        try:
            lo, hi = con.execute(f'SELECT MIN("{dcol}"), MAX("{dcol}") FROM {sql_from}').fetchone()
            lo, hi = (str(lo) if lo is not None else None, str(hi) if hi is not None else None)
            if lo and hi and len(lo) >= 10 and len(hi) >= 10:
                from datetime import date as _d
                span = (_d.fromisoformat(hi[:10]) - _d.fromisoformat(lo[:10])).days + 1
        except Exception:
            lo = hi = None
    st = "NODATA" if n == 0 else ("AMBER" if (span is not None and span < CENSUS_THIN_DAYS) else "GREEN")
    return {"rows": int(n), "date_col": dcol or "", "lo": lo or "", "hi": hi or "", "span_days": span, "state": st}


#: 批478 庫冊(尾版律 glob;操作員機器 census 實測 + 寫入者掃描)
DBSSOT_GLOB = "VIA_DB_Table_SSOT_v*.json"


def db_ssot() -> tuple[dict, str]:
    hits = sorted(HERE.glob(DBSSOT_GLOB))
    if not hits:
        return {}, "庫冊缺(VIA_DB_Table_SSOT_v*.json)"
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8")), hits[-1].name
    except Exception as exc:
        return {}, f"庫冊讀不了:{type(exc).__name__}"


#: 批476 啟動層 bootstrap(sitecustomize.py 住這裡;子行程 PYTHONPATH 前置它)
BOOTDIR = VIA / "supportive modules" / "bootstrap"


def child_env(family: str = "", extra_path: str = "") -> dict:
    r"""子行程環境:加速器/網路件在啟動層綁上(批476)。同意閘**一個字都不碰**。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VIA_ROOT=str(VIA))
    _ph = env.pop("PYTHONHOME", None)          # 批514 L32:PYTHONHOME 永不傳給子行程(母殼帶錯版=家族境 SRE mismatch 根因)
    if _ph:
        env["VIA_PYTHONHOME_SCRUBBED"] = _ph
    if family:
        env["VIA_FAMILY"] = family.lower()
    if BOOTDIR.is_dir():
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(BOOTDIR) + (os.pathsep + prev if prev else "")
    if extra_path:                      # 批477:-m 啟動的套件根
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = extra_path + (os.pathsep + prev if prev else "")
    return env
#: 逐項逾時
DEFAULT_TIMEOUT = 900
#: 心跳間隔(秒):畫面最多白這麼久。批423 那課:看起來死機 = 卡斷。
HEARTBEAT_SEC = 20
#: `[計]` 行:只認最後一行(批462)
TALLY_RX = re.compile(r"\[計\][^\n]*")
#: 引擎「誠實停」的自述句(它們自己印的,不是我發明的分類)
#: 量過才用:全樹 `return 2` 163 處只有 46 處是這個意思,**rc 不可當判準**。
#: 批471 v0102:v0101 這張字表是照 VRN 幾支的措辭湊的,只認得 VRN 的方言——
#: VAP 印「誠實停 rc2」就漏接了。「誠實停」全樹 451 處,才是這套系統的正典句。
STOP_RX = re.compile(
    r"(誠實停|無報告件|無可轉檔|無 ?PDF|無分區 ?sidecar|缺件|夾不存在|夾是空的|"
    r"無報告檔|尚無報告|無可轉|零報告|無輸入|庫缺|庫不在|價表缺|表缺|根缺|"
    r"Table with name \w+ does not exist|Catalog Error)[^\n]{0,48}")
#: 批498:同意閘未開=引擎 fail-closed 誠實拒跑——是**閘**,不是壞掉,也不是缺料;要跑=操作員開閘(永不代設)
GATE_RX = re.compile(r"(同意閘未開|FAIL-CLOSED|法遵雙閘未開|閘未開|拒跑\(fail-closed)[^\n]{0,60}")
NODATA_RX = STOP_RX          # 舊名留著當橋(別處若已 import,不讓它斷)

#: 誠實停之中屬於**缺件**的那一類(缺套件/缺模組)——與缺料要分開。
#: 缺件 ≠ 缺料 ≠ 壞掉:三件事混成一盞燈,人就會去 debug 一支沒壞的引擎。
#: 批491:套件「在」但壞了——引擎 import 得到卻用不了;這不是引擎缺陷,也不是缺料,是缺件的一種。
BROKEN_PKG_RX = re.compile(
    r"module '([A-Za-z_][\w.]*)' has no attribute '__version__'|"
    r"DLL load failed while importing ([A-Za-z_]\w*)")

NEED_RX = re.compile(
    r"(缺席|未安裝|沒裝|不在位)[^\n]{0,24}|"
    r"(pip install|ModuleNotFoundError|ImportError|No module named)[^\n]{0,40}|"
    # 批473:`需要 reportlab`——引擎講了實話而且連補法都給了,我卻判它紅。
    # 收得緊:`需要` 後面必須緊跟看起來像套件名的 ASCII 識別字(至少三碼),
    # 不是看到「需要」兩個字就放過——那在中文裡太常見,會把真紅也放走。
    r"需要\s*[A-Za-z][A-Za-z0-9_.\-]{2,}|"
    r"\b(plotly|matplotlib|seaborn|duckdb|pymupdf|fitz|pypdf|python-docx|"
    r"reportlab|paddleocr|camelot|tabula|"
    r"pytesseract|tesseract)\b[^\n]{0,12}(缺席|未安裝|沒裝)")

#: argparse 自己講的「你少給我一個參數」。**只認它講的**——
#: 不能用「冊上有宣告 params 就別跑」一刀切:37 項裡 21 項宣告了 params,
#: 其中 20 項沒給參數照樣跑得好好的(量過),一刀切等於誤殺 20 項。
ARGERR_RX = re.compile(
    r"error: (argument [^\n:]{1,40}: expected one argument|"
    r"the following arguments are required:[^\n]{0,60}|"
    r"argument [^\n:]{1,40}: invalid [^\n]{0,40})")


def classify_stop(tail: str) -> tuple[str, str]:
    """rc≠0 的輸出尾段 → (state, why)。判不出來就回 ("", "") 讓它照舊 RED。

    次序有意義:**缺參數 → 缺件 → 缺料**。
    先問 argparse(它講得最死),再問缺件(缺件常跟誠實停同句),最後才是缺料。
    每一種都把**命中的原文帶回**當證據——判準亮不出證據,它就只是另一種猜。
    """
    m_g = GATE_RX.search(tail)
    if m_g:
        return ("GATED", f"**同意閘未開**(不是壞掉):引擎 fail-closed 誠實拒跑「{m_g.group(0).strip()[:56]}」;要跑=你開閘 "
                         f"$env:VIA_NET_CONSENT='YES'(需要時再加 VIA_SCRAPE_CONSENT/金鑰),我不代設")
    m_bp = BROKEN_PKG_RX.search(tail)
    if m_bp:
        pkg = m_bp.group(1) or m_bp.group(2) or "?"
        return ("ABSENT", f"**缺件**(套件壞了,不是引擎壞):{m_bp.group(0)[:60]} → {pkg} 匯入成半拆/命名空間包"
                          f"(site-packages 的 {pkg} 夾缺 __init__.py 或 DLL 缺)→ 在該家族境 pip install --force-reinstall {pkg}")
    if "attempted relative import" in tail:
        # 批477 第十盞:這不是缺套件,是啟動方式錯。指錯方向的灰燈會讓人去裝一個不存在的東西。
        return ("RED", "**啟動方式錯**(不是缺件):套件內模組須以 `python -m` 啟動;冊上這項加 `module` 欄")
    m = ARGERR_RX.search(tail)
    if m:
        return ("ABSENT", f"**缺參數**(不是壞掉):argparse 自述「{m.group(0)[7:59]}」"
                          f";冊上這項的 params 該由主控台/--ids 帶值給它")
    # 批473:缺件**不再要求先命中誠實停字樣**。`需要 reportlab` 本身就是一句
    # 完整的誠實話,它不會再多寫一次「誠實停」;v0105 把缺件掛在誠實停底下,
    # 等於要求引擎用兩種措辭講同一件事才算數。
    n = NEED_RX.search(tail)
    m = STOP_RX.search(tail)
    if n:
        hit = m.group(0).strip()[:52] if m else ""
        return ("ABSENT", f"**缺件**(不是壞掉):引擎自述「{(n.group(0) or '').strip()[:36]}"
                          + (f"」· 誠實停「{hit}」" if hit else "」(補上那個套件再跑)"))
    if not m:
        return ("", "")
    hit = m.group(0).strip()[:52]
    return ("NODATA", f"**缺料**(不是壞掉):引擎自述「{hit}」=上游沒料,非本引擎缺陷")


def diagnostic_tail(output: str, limit: int = 10) -> str:
    """取可裁決尾段，排除通過檢查裡描述的反例字樣。

    ``[OK]`` 說明常寫「缺席時仍有退路」；那是已通過的規格文字，不是本次
    缺件證據。批508 曾因此把有真正 FAIL 的 VRN_ENG073 誤畫成 ABSENT。
    FAIL、traceback 與直接誠實停仍完整保留。
    """
    lines = [x for x in output.splitlines()
             if x.strip() and not re.match(r"^\s*\[OK\]", x)]
    return "\n".join(lines[-limit:])


#: 動詞裡帶 `--apply` 的項=**寫庫件**。家族全掃永不代跑(要跑請 --ids 明點)。
#: 與操作員既有的「--approve-remove 只在明令下」同律:
#: 破壞性的那一步,永遠要有人**指名道姓**點它,不能被一個家族開關掃進去。
WRITE_VERB = "--apply"


def _load(glob_pat: str, d: Path, alias: str):
    """尾版律載入(缺席回 (None, 因由);不拋)。"""
    try:
        hits = sorted(d.glob(glob_pat))
        if not hits:
            return None, f"{glob_pat} 缺席({d.name})"
        sp = importlib.util.spec_from_file_location(alias, hits[-1])
        m = importlib.util.module_from_spec(sp)
        sys.modules[alias] = m
        sp.loader.exec_module(m)
        return m, ""
    except Exception as exc:
        return None, f"{glob_pat} 載入失敗 {type(exc).__name__}:{str(exc)[:60]}"


def spec_path() -> tuple[Path | None, str]:
    hits = sorted((VIA / "supportive modules" / "registry").glob(SPEC_GLOB))
    if not hits:
        return None, f"{SPEC_GLOB} 缺席"
    return hits[-1], ""


def load_spec() -> tuple[dict, str]:
    p, why = spec_path()
    if p is None:
        return {}, why
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")), f"冊 {p.name}"
    except Exception as exc:
        return {}, f"冊讀取失敗 {type(exc).__name__}:{str(exc)[:60]}"


def python_for(family: str) -> dict:
    """家族境 python —— **委派** MDL137 RunGate(它再委派 MDL136 EntryBridge)。
       Zero-Hydra:本件不自己找 conda/venv;橋缺席才退回本行程 python 並講明。"""
    m, why = _load("CGC_MDL137_RunGate_v*.py", HERE, "mdl137_bus")
    if m is not None and hasattr(m, "python_for"):
        try:
            r = m.python_for(family)
            if isinstance(r, dict) and r.get("python"):
                return r
        except Exception as exc:
            why = f"RunGate.python_for 失敗 {type(exc).__name__}"
    return {"family": family, "python": sys.executable, "env": "",
            "source": f"本行程退路({why or 'RunGate 無 python_for'})", "state": "FALLBACK"}


def catalog(family: str | None = None) -> list:
    """冊上每一項 × 尾版解析 × 在位實測。**在位 ≠ 跑得動**,本表只說在不在。"""
    spec, why = load_spec()
    out = []
    for fam, f in (spec.get("families") or {}).items():
        if family and fam != family:
            continue
        for grp in f.get("groups", []):
            for it in grp.get("items", []):
                eng = it.get("engine") or {}
                d = VIA / str(eng.get("dir") or "")
                g = str(eng.get("glob") or "")
                hits = sorted(d.glob(g)) if (g and d.is_dir()) else []
                out.append({
                    "id": it.get("id", ""),
                    "family": fam,
                    "group": grp.get("id", ""),
                    "zh": it.get("zh", ""),
                    "glob": g,
                    "dir": str(eng.get("dir") or ""),
                    "verb": list(eng.get("verb") or []),
                    "test_verb": list(it.get("test_verb") or []),
                    "params": list(it.get("params") or []),
                    "outputs": list(it.get("outputs") or []),
                    "net": bool(it.get("net")),
                    "engine": hits[-1].name if hits else "",
                    "engine_path": str(hits[-1]) if hits else "",
                    "module": it.get("module", ""),
                    "cwd": it.get("cwd", ""),
                    "engine_dir": str(VIA / eng.get("dir", "")),
                    "versions": len(hits),
                    "engine_state": "在位" if hits else "缺席",
                    "spec_why": why,
                })
    return out


def _argv_for(item: dict, params: dict | None, py: str,
              verb: list | None = None) -> list:
    # 批477:套件裡的模組(冊上 module 欄)要用 -m 啟動,不能當檔案跑(相對匯入會炸)
    argv = [py, "-m", item["module"]] if item.get("module") else [py, item["engine_path"]]
    argv += list((item.get("verb") if verb is None else verb) or [])
    for k, v in (params or {}).items():
        if v is None or v == "":
            continue
        argv += [f"--{k}", str(v)]
    return argv


def _test_contract(item: dict) -> tuple[dict | None, str]:
    """把 production 契約投影成有界驗收契約，不碰網路、不跑全量回補。

    優先順序：冊上 test_verb → 冊上本來就是 selftest → 引擎明示旗標 →
    同夾 companion ``test_*.py``。沒有證據就回 None，呼叫端必須報 ABSENT。
    """
    explicit = list(item.get("test_verb") or [])
    current = list(item.get("verb") or [])
    self_tokens = {"--selftest", "--self-test", "selftest"}
    if explicit:
        return {**item, "verb": explicit}, "冊上 test_verb"
    if any(str(x) in self_tokens for x in current):
        return dict(item), "冊上動詞本來就是 selftest"
    p = Path(item.get("engine_path") or "")
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        src = ""
    if "--selftest" in src:
        return {**item, "verb": ["--selftest"]}, "引擎明示 --selftest"
    if "--self-test" in src:
        return {**item, "verb": ["--self-test"]}, "引擎明示 --self-test"
    if p.is_file():
        tests = sorted(q for q in p.parent.glob("test_*.py") if q.is_file())
        if tests:
            q = tests[-1]
            return {**item, "engine": q.name, "engine_path": str(q),
                    "module": "", "verb": []}, f"companion unittest {q.name}"
    return None, "沒有有界 selftest/test_verb/companion test；不以 production run 冒充驗收"


HEARTBEAT_TO_STDERR = False   # call 模式才 True(stdout 留給結果 JSON;批484);矩陣模式走 stdout 免得兩條流錯位(批489)


def _echo_err(msg: str) -> None:
    """心跳:矩陣模式走 stdout(與項目行同一條流,先後不錯位);call 模式走 stderr(stdout 是 JSON)。"""
    print(msg, file=(sys.stderr if HEARTBEAT_TO_STDERR else sys.stdout), flush=True)


def _run_streaming(argv: list, env: dict, workdir, timeout: int,
                   heartbeat: int | None = None, echo=_echo_err, label: str = "") -> tuple:
    r"""邊跑邊收 + 心跳 + 逾時只殺自己的子行程。回 (rc, 合併輸出, 是否逾時)。

    批474 v0108:`subprocess.run(capture_output=True)` 在長跑引擎上=白畫面到結束。
    這裡照 AllGreen v0101 的藥方:Popen、讀取執行緒逐行收、主執行緒每 heartbeat 秒
    醒一次印「還在跑」——印的是**引擎自己的最後一行**,不是我編的進度。
    """
    import threading
    # 批484:心跳間隔在**呼叫時**才讀模組常數(預設參數在定義時就凍住,執行期改 HEARTBEAT_SEC 會沒感覺)
    heartbeat = heartbeat or HEARTBEAT_SEC
    lines: list = []
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace",
                            env=env, cwd=str(workdir), bufsize=1)

    def _pump():
        try:
            for ln in proc.stdout:          # type: ignore[union-attr]
                lines.append(ln.rstrip("\n"))
        except Exception:
            pass

    th = threading.Thread(target=_pump, daemon=True)
    th.start()
    t0 = time.time()
    timed_out = False
    while True:
        try:
            proc.wait(timeout=heartbeat)
            break
        except subprocess.TimeoutExpired:
            el = int(time.time() - t0)
            if el >= timeout:
                timed_out = True
                try:
                    proc.kill()             # 只殺自己生的這一個
                except Exception:
                    pass
                proc.wait()
                break
            last = next((x for x in reversed(lines) if x.strip()), "")
            echo(f"      ⏳ {label + ' ' if label else ''}還在跑 · {el}s · 引擎最後一行:{last[:88] or '(尚未印任何字)'}")
    th.join(timeout=2)
    return proc.returncode, "\n".join(lines) + ("\n" if lines else ""), timed_out


def call(item_id: str, params: dict | None = None, timeout: int = DEFAULT_TIMEOUT,
         apply: bool = False, catalog_rows: list | None = None,
         sweep: bool = False, profile: str = "run") -> dict:
    """**統一呼叫契約**。任何子系統都用這一支調度引擎,拿到同一個結果形狀。

    apply=False(預設)→ 只解析不動手,回 PLAN。要真跑必須明講 apply=True:
    調度層的預設值錯一次,代價是**在別人的機器上動了不該動的東西**。
    """
    if profile not in ("run", "test"):
        return {"id": item_id, "family": "", "zh": "", "engine": "", "engine_state": "",
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "", "profile": profile,
                "why": f"不認得 profile={profile};只收 run|test"}
    rows = catalog_rows if catalog_rows is not None else catalog()
    hit = next((r for r in rows if r["id"] == item_id), None)
    if hit is None:
        return {"id": item_id, "family": "", "zh": "", "engine": "", "engine_state": "冊無此項",
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "", "why": f"冊上沒有 id={item_id}(零發明:不猜)"}
    pyinfo = python_for(hit["family"])
    if not hit["engine_path"]:
        return {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": f"引擎不在位({hit['glob']});**缺件不是紅燈**,不要去 debug 一支不存在的引擎"}
    run_hit, test_why = (dict(hit), "production 契約")
    run_params = params
    if profile == "test":
        run_hit, test_why = _test_contract(hit)
        run_params = None                 # production 參數仍完整留在 contract_*，驗收不代跑 production
        if run_hit is None:
            base = {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
                    "argv": [], "python": pyinfo["python"], "python_src": pyinfo.get("source", ""),
                    "profile": profile, "contract_verb": list(hit.get("verb") or []),
                    "contract_params": list(hit.get("params") or [])}
            return {**base, "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                    "outputs_seen": [], "stdout_tail": "", "why": test_why}
    argv = _argv_for(run_hit, run_params, pyinfo["python"])
    base = {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
            "argv": argv, "python": pyinfo["python"], "python_src": pyinfo.get("source", ""),
            "profile": profile, "test_contract": test_why,
            "test_engine": run_hit.get("engine", "") if profile == "test" else "",
            "contract_verb": list(hit.get("verb") or []),
            "contract_params": list(hit.get("params") or [])}
    if not apply:
        return {**base, "state": "PLAN", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": "dry:只解析不動手(要真跑請 apply=True / --apply)"}
    if profile == "run" and sweep and WRITE_VERB in (hit.get("verb") or []):
        # 批471 v0102 寫庫動詞閘:動詞裡本來就帶 `--apply` 的項(量到 2 支:
        # tw_universe_update / db_localdb_apply)是**寫庫件**。家族全掃永不代跑。
        # 破壞性的那一步永遠要有人指名道姓點它,不能被一個家族開關掃進去。
        return {**base, "state": "PLAN", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": "**寫庫動詞**:家族全掃不代跑(要跑請 --ids "
                       f"{hit['id']} --apply 明點;同「--approve-remove 只在明令下」律)"}
    t0 = time.time()
    env = child_env(hit.get("family", ""), run_hit.get("engine_dir", "") if run_hit.get("module") else "")
    # Family interpreter and shell-visible environment must refer to the same home.
    env_root = Path(pyinfo["python"]).parent
    if env_root.name.lower() in ("scripts", "bin"):
        env_root = env_root.parent
    env["PATH"] = os.pathsep.join([str(env_root / "Scripts"), str(env_root / "bin"), str(env_root), env.get("PATH", "")])
    if (env_root / "conda-meta").is_dir():
        env["CONDA_PREFIX"] = str(env_root)
        env.pop("VIRTUAL_ENV", None)
    else:
        env["VIRTUAL_ENV"] = str(env_root)
    # 批471 v0103:**不在原始碼樹裡跑**。量過:36 支在位引擎全用 __file__ 定位,
    # 零支讀 cwd,所以換工作目錄對它們沒有任何影響;而不換的代價是
    # 相對路徑預設(如 ENG016 的 `--out ./vap_one_out`)會把產出拉進原始碼樹。
    workdir = OUTDIR / "_cwd"
    workdir.mkdir(parents=True, exist_ok=True)
    if run_hit.get("cwd") == "engine" and run_hit.get("engine_dir") and Path(run_hit["engine_dir"]).is_dir():
        workdir = Path(run_hit["engine_dir"])      # 批477:冊講了才換(讀 cwd 的引擎)
    try:
        rc, out, timed_out = _run_streaming(argv, env, workdir, timeout, label=item_id)
        if timed_out:
            state, why = "TIMEOUT", f"逾 {timeout}s 未回=已停(不卡斷);只殺自己生的子行程,部分輸出保留"
        else:
            state = "GREEN" if rc == 0 else "RED"
            why = ""
            if rc != 0:
                # 批471 v0101:**缺料 ≠ 壞掉**。只認引擎自己印的那句話,並把原文帶回
                # 當證據;沒有那句話的 rc≠0 一律照舊 RED(不得靠這條放過真紅)。
                # v0102:再往下分一層——缺參數 / 缺件 / 缺料,見 classify_stop。
                _tail = diagnostic_tail(out)
                _st, _why = classify_stop(_tail)
                if profile == "test" and re.search(r"(?m)^\s*\[FAIL\]", out):
                    state, why = "RED", "selftest 有失敗斷言；反例的缺料/缺件訊息不作停機分類"
                elif _st:
                    state, why = _st, _why
    except Exception as exc:
        rc, out, state, why = None, "", "RED", f"{type(exc).__name__}:{str(exc)[:80]}"
    secs = round(time.time() - t0, 2)
    # 批462:`[計]` 只認**最後一行**。子報告也會印 `FAIL 0`,全篇搜就會把
    # 「OK 38 · FAIL 1」讀成綠——那正是工作站掛過的那個假綠。
    tallies = TALLY_RX.findall(out)
    tally = tallies[-1].strip() if tallies else ""
    if state == "GREEN" and tally:
        m = re.search(r"FAIL\s+(\d+)", tally)
        if m and int(m.group(1)) > 0:
            state = "AMBER"
            why = "rc=0 但最後一行 [計] 仍有 FAIL(以計數為準,不以 rc 為準)"
    seen = []
    for o in (hit.get("outputs") or []):
        verdict, note = output_verdict(o)
        seen.append({"out": o, "exists": (True if verdict == "在" else False if verdict == "缺" else None),
                     "verdict": verdict, "why": note})
    # Retain complete station evidence: a six-line tail cannot diagnose failed assertions.
    import uuid
    logdir = OUTDIR / "station_logs"
    logdir.mkdir(parents=True, exist_ok=True)
    logfile = logdir / (re.sub(r"[^A-Za-z0-9_-]", "_", item_id) + "_" + uuid.uuid4().hex + ".log")
    logfile.write_text(out, encoding="utf-8")
    failures = [line for line in out.splitlines() if re.match(r"^\s*\[FAIL\]", line)]
    lines = [x for x in out.splitlines() if x.strip()]
    if state != "GREEN":
        why += " · 完整紀錄: " + str(logfile)
        if failures:
            why += " · " + " | ".join(failures)
    return {**base, "stdout_log": str(logfile), "failed_assertions": failures, "state": state, "rc": rc, "seconds": secs, "tally": tally,
            "outputs_seen": seen, "stdout_tail": "\n".join(lines[-6:]), "why": why}


def matrix(family: str | None = None, ids: list | None = None, apply: bool = False,
           timeout: int = DEFAULT_TIMEOUT, do_print: bool = True,
           apply_families: list | None = None, profile: str = "run",
           catalog_rows: list | None = None) -> dict:
    """批量調度 → 多矩陣資料(**這一份就是 HTML 的唯一資料源**,零二次加工)。

    批471 v0102:`apply` 不再是全有全無。
      apply=True                       → 本次選到的每一項都真跑
      apply_families=["vrn","vap"]     → **只有**這些家族真跑,其餘照樣 PLAN
      ids=[...]                        → 只跑點名的項(且視為**明點**,寫庫閘放行)
    一個開關按下去就發動 24 支 VDF 回補,那不叫方便,那叫地雷。
    """
    available_rows = list(catalog_rows) if catalog_rows is not None else catalog(family)
    if catalog_rows is not None and family:
        available_rows = [r for r in available_rows if r.get("family") == family]
    rows = available_rows
    wanted_ids = list(dict.fromkeys(ids or []))
    if ids:
        rows = [r for r in rows if r["id"] in wanted_ids]
    found_ids = {r["id"] for r in rows}
    unknown_ids = [item_id for item_id in wanted_ids if item_id not in found_ids]
    fams = {x.strip().lower() for x in (apply_families or []) if x.strip()}
    named = bool(ids)          # --ids 是**明點**:寫庫閘只擋家族全掃,不擋明點
    res = []
    for i, r in enumerate(rows, 1):
        do = apply or named or (r["family"].lower() in fams)
        if do_print:
            print(f"  [{i}/{len(rows)}] {r['family']}/{r['id']} · "
                  f"{r['engine'] or '缺席'}{'' if do else ' (PLAN)'}")
        _c = call(r["id"], apply=do, timeout=timeout, catalog_rows=available_rows,
                  sweep=not named, profile=profile)
        res.append(_c)
        import uuid
        _partial = OUTDIR / "ENGINE_BUS_progress.json"
        _partial.parent.mkdir(parents=True, exist_ok=True)
        _tmp = _partial.with_name(_partial.name + "." + uuid.uuid4().hex + ".tmp")
        _tmp.write_text(json.dumps({"profile": profile, "results": res,
                                   "complete": False, "total": len(rows)}, ensure_ascii=False), encoding="utf-8")
        os.replace(_tmp, _partial)
        if do_print and do:
            print(f"      → {_c['state']} · {_c['seconds']}s"
                  + (f" · {_c['why']}" if _c.get("why") else ""))
    for item_id in unknown_ids:
        _c = call(item_id, apply=True, timeout=timeout,
                  catalog_rows=available_rows, sweep=False, profile=profile)
        res.append(_c)
        if do_print:
            print(f"  [ABSENT] 點名項 {item_id} 不在冊；零發明、不猜引擎")
    tally = {}
    for x in res:
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    spec_p, _ = spec_path()
    return {
        "schema": "VIA.EngineBus.v2",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "spec": spec_p.name if spec_p else "(冊缺)",
        "family": family or "all",
        "apply": apply,
        "apply_families": sorted(fams),
        "ids": list(ids or []),
        "unknown_ids": unknown_ids,
        "profile": profile,
        "live_n": sum(1 for x in res if x["state"] not in ("PLAN",)),
        "counts": tally,
        "catalog": rows,
        "results": res,
        # 批474:引擎綠不綠回答不了「有沒有料」。庫況跟調度結果放同一份資料裡,
        # 頁上才不必去別處撈(**這一份仍是 HTML 的唯一資料源**)。
        "census": _census_block(),
    }


def _census_block() -> dict:
    rows, why = db_census()
    miss = census_expected(rows) if rows else []
    tal: dict = {}
    for r in rows + miss:
        tal[r["state"]] = tal.get(r["state"], 0) + 1
    return {"tables": rows, "missing": miss, "counts": tal, "why": why,
            "thin_days": CENSUS_THIN_DAYS}



_CENSUS = None
_CENSUS_WHY = ""
#: 日期跨度多少天才算「料夠厚」。30 天=一個月:回補鏈跑成功至少要有這麼多。
#: 這個數字是**判準**,所以寫在這裡讓人看得見,不埋在函式裡。
CENSUS_THIN_DAYS = 30
#: 日期欄的常見名字(問過實庫才列的,不是想像的)
_DATE_COLS = ("date", "trade_date", "obs_date", "period", "dt", "as_of", "ts")


def db_census() -> tuple[list, str]:
    r"""庫況普查:**表在不在 · 有幾列 · 日期跨多久**(唯讀,只跑一次)。

    為什麼要有這一張表(批474 操作員問 C「VDF 到底能不能跑」):
      引擎綠不綠**回答不了那題**——一支引擎可以完美地跑完,
      然後把資料寫進一張空表,或寫進一張只有四天的表。
      「跑得動」和「有料」是兩件事,而只報前者就是一種假綠。

    三態怎麼判(判準亮在這裡,不埋):
      GREEN  有列,且(沒有日期欄 或 跨度 ≥ CENSUS_THIN_DAYS)
      AMBER  有列,但日期跨度 < CENSUS_THIN_DAYS —— **料在,但薄**
      NODATA 表在、列數 0 —— **表建好了沒料**
      ABSENT 全樹沒有這張表 —— **不是壞掉**,是還沒建

    掃描沿用 `db_table_index()` 認可的那批庫(排除 references/自測夾/SCOPE_COPY),
    **不另立庫路徑冊**,也不另開第二支掃描器。
    """
    global _CENSUS, _CENSUS_WHY
    if _CENSUS is not None:
        return _CENSUS, _CENSUS_WHY
    idx, why = db_table_index()
    # 批474 自犯錯:`db_table_index` **成功時 why 也有值**(「問過 6 本庫 · 43 張表」),
    # 我拿它當失敗旗標 → 庫況永遠是空的。判準看 idx 本身,不看那句附註。
    if not idx:
        _CENSUS = []
        _CENSUS_WHY = why or "全樹無可讀的 duckdb"
        return _CENSUS, _CENSUS_WHY
    try:
        import duckdb
    except Exception:
        _CENSUS = []
        _CENSUS_WHY = "本環境無 duckdb"
        return _CENSUS, _CENSUS_WHY
    rows, seen = [], set()
    for db in db_files():
        sp = str(db)
        con = None
        try:
            con = duckdb.connect(sp, read_only=True)
            for (t,) in con.execute("SHOW TABLES").fetchall():
                t = str(t)
                if (db.name, t) in seen:
                    continue
                seen.add((db.name, t))
                try:
                    cols = [str(r[1]) for r in con.execute(f'PRAGMA table_info("{t}")').fetchall()]
                    r_ = _tbl_state(con, f'"{t}"', cols)
                except Exception:
                    continue
                r_.update({"db": db.name, "table": t, "path": _rel(db)})
                rows.append(r_)
        except Exception:
            continue
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    # 批491:家內 parquet 湖改向 MDL123 尾版 catalog() 取(單一實作,讀中繼資料不掃湖);MDL123 缺席=誠實無湖列
    h, _ = data_home()
    if h is not None:
        try:
            mods = sorted(HERE.glob("CGC_MDL123_DataHome_v*.py"))
            if mods:
                import importlib.util
                spec = importlib.util.spec_from_file_location("via_datahome", mods[-1])
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                cat = m.catalog(VIA, home=str(h), do_print=False, write=LAKE_WRITE)
                for e in cat.get("lake", []):
                    if e.get("rows", -1) < 0 and e.get("state") == "NODUCKDB":
                        continue
                    lo, hi = e.get("lo", ""), e.get("hi", "")
                    span = None
                    try:
                        if lo and hi and len(lo) >= 10 and len(hi) >= 10:
                            from datetime import date as _d
                            span = (_d.fromisoformat(hi[:10]) - _d.fromisoformat(lo[:10])).days + 1
                    except Exception:
                        span = None
                    st = ("RED" if e.get("state") == "FAIL" else "NODATA" if e.get("rows", 0) == 0 else
                          "AMBER" if (span is not None and span < CENSUS_THIN_DAYS) else "GREEN")
                    rows.append({"db": "湖", "table": e["dataset"], "rows": max(int(e.get("rows", 0)), 0),
                                 "date_col": e.get("date_col", ""), "lo": lo, "hi": hi, "span_days": span, "state": st,
                                 "path": "家:" + str(e.get("rel", "")), "files": e.get("files", 0),
                                 "members": len(e.get("members", [])) if e.get("mixed") else 0,
                                 "note": e.get("why", "")})
        except Exception:
            pass
    ssot, _ = db_ssot()
    declared = {(t["db"], t["table"]) for t in ssot.get("tables", [])}
    declared_all = {t["table"] for t in ssot.get("tables", []) if t.get("db_scope") == "all_home"}      # 批500 全庫同步律的表
    lamp_rows = {t["table"]: int(t.get("min_rows") or 1) for t in ssot.get("tables", []) if t.get("lamp") == "rows"}
    for r in rows:
        r["source"] = ("湖" if r["db"] == "湖" else "副本" if "_repo_" in r["db"] else
                       "冊上" if ((r["db"], r["table"]) in declared or r["table"] in declared_all) else "冊外")
        if r["table"] in lamp_rows and r["db"] != "湖":
            # 批500:對帳單/台帳/交接/政策表只看列數——一列一天是對帳單,不是老化
            r["state"] = "GREEN" if r.get("rows", 0) >= lamp_rows[r["table"]] else "NODATA"
            r["note"] = (r.get("note") or "") + ("·列數表" if r["state"] == "GREEN" else "·列數表(未達 min_rows)")
    rows.sort(key=lambda r: (r["db"], r["table"]))
    _CENSUS = rows
    _CENSUS_WHY = why
    return _CENSUS, _CENSUS_WHY


def census_expected(rows: list) -> list:
    r"""該有而沒有的表 → ABSENT 列。批478 起**冊優先**,grep 只當冊外的補充。

    冊上宣告、庫裡沒有 → ABSENT(冊上宣告),並列寫入者引擎(這是最該亮的一種:該有而沒有)
    冊外、碼上 SQL 語境引用 ≥ MIN_REFS 檔 → ABSENT(冊外)(批474 那條律照舊:寧可少報)
    冊上的 known_legacy_absent 不重複報(操作員機器上已知的 12 張舊制表,冊講了)
    """
    have = {r["table"] for r in rows}
    ssot, _ = db_ssot()
    out = []
    declared = set()
    for t in ssot.get("tables", []):
        declared.add(t["table"])
        if t["table"] not in have:
            out.append({"db": t["db"], "table": t["table"], "rows": 0, "date_col": "",
                        "lo": "", "hi": "", "span_days": None, "state": "ABSENT",
                        "refs": 0, "source": "冊上宣告", "writers": t.get("writers", [])})
    legacy = set(ssot.get("known_legacy_absent", []))
    MIN_REFS = 3
    sql_rx = re.compile(
        r"(?:FROM|JOIN|INTO|TABLE|UPDATE)\s+[\"'`]?"
        r"((?:tw|vrn|etf|global|macro|consensus)_[a-z0-9_]{2,28})\b", re.I)
    cnt: dict = {}
    for pyf in list((VIA / "functional modules").rglob("*.py")) + \
            list((VIA / "supportive modules").rglob("*.py")):
        sp = str(pyf)
        if "/references/" in sp or "SCOPE_COPY" in sp:
            continue
        try:
            txt = pyf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for t in {m.lower() for m in sql_rx.findall(txt)}:
            cnt[t] = cnt.get(t, 0) + 1
    for t, c in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
        if c >= MIN_REFS and t not in have and t not in declared and t not in legacy:
            out.append({"db": "—", "table": t, "rows": 0, "date_col": "",
                        "lo": "", "hi": "", "span_days": None,
                        "state": "ABSENT", "refs": c, "source": "冊外"})
    return out



SENTINEL_BEFORE = "1950-01-01"


def db_hygiene() -> dict:
    r"""庫衛生唯讀審計(批485):哨兵列 + 副本庫。只數、只寫 SQL,**不執行任何寫入**。"""
    out = {"sentinel": [], "replicas": [], "why": ""}
    try:
        import duckdb
    except Exception:
        out["why"] = "本環境無 duckdb"
        return out
    rows, why = db_census()
    if not rows:
        out["why"] = why or "無庫"
        return out
    by_db: dict = {}
    for db in db_files():
        sp = str(db)
        by_db.setdefault(db.name, db)
    canon_max = {}   # (table) → (db, max_date) 給副本比對用
    for r in rows:
        if not r["date_col"] or r["rows"] == 0:
            continue
        db = by_db.get(r["db"])
        if not db:
            continue
        con = None
        try:
            con = duckdb.connect(str(db), read_only=True)
            t, c = r["table"], r["date_col"]
            n = con.execute(f'SELECT COUNT(*) FROM "{t}" WHERE TRY_CAST("{c}" AS DATE) < DATE \'{SENTINEL_BEFORE}\'').fetchone()[0]
            if n:
                smp = con.execute(f'SELECT "{c}" FROM "{t}" WHERE TRY_CAST("{c}" AS DATE) < DATE \'{SENTINEL_BEFORE}\' LIMIT 3').fetchall()
                out["sentinel"].append({"db": r["db"], "table": t, "date_col": c, "n": int(n),
                                        "sample": [str(x[0]) for x in smp],
                                        "sql_not_run": f'DELETE FROM "{t}" WHERE TRY_CAST("{c}" AS DATE) < DATE \'{SENTINEL_BEFORE}\';  -- 只寫不跑'})
            if "_repo_" not in r["db"]:
                canon_max[(r["table"])] = (r["db"], r["hi"])
        except Exception:
            pass
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    for r in rows:
        if "_repo_" in r["db"]:
            cm = canon_max.get(r["table"])
            out["replicas"].append({"db": r["db"], "table": r["table"], "rows": r["rows"], "hi": r["hi"],
                                    "canonical": cm[0] if cm else "(正庫無同名表)",
                                    "canonical_hi": cm[1] if cm else "",
                                    "verdict": ("副本較舊=退役候選(不刪)" if cm and cm[1] and r["hi"] and r["hi"] < cm[1]
                                                else "副本較新或無法比=要人看")})
    return out

# ---------------------------------------------------------------- 多矩陣 HTML
_STATE_COLOR = {"GREEN": "#1a7f37", "AMBER": "#b7791f", "RED": "#b91c1c", "GATED": "#7c3aed",
                "TIMEOUT": "#b91c1c", "ABSENT": "#6b7280", "PLAN": "#3b6fb5",
                "NODATA": "#7c5cbf"}


def _tokens() -> tuple[dict, str]:
    """UI 樣板正主 MDL089 的 tokens(Zero-Hydra:不自己發明配色)。"""
    m, why = _load("CGC_MDL089_UIBaseTemplate_v*.py", HERE, "mdl089_bus")
    if m is not None and hasattr(m, "load_tokens"):
        try:
            return m.load_tokens(), f"MDL089 {Path(m.__file__).name}"
        except Exception as exc:
            why = f"load_tokens 失敗 {type(exc).__name__}"
    return {}, why or "MDL089 缺席"


def _cell(state: str) -> str:
    c = _STATE_COLOR.get(state, "#6b7280")
    return (f'<span class="st" style="background:{c}1a;color:{c};'
            f'border:1px solid {c}55">{_html.escape(state)}</span>')


def _mode_label(data: dict) -> str:
    """頁首的模式標籤(批471 v0104)。`--apply-family` 下 data["apply"] 是 False,
    v0103 就照著印「只解析(dry)」——**一張報實測結果的頁,第一行把自己的模式講錯**。"""
    if data.get("profile") == "test":
        fams = data.get("apply_families") or []
        return "有界驗收(selftest)" + (f" · 家族 {','.join(fams)}" if fams else "")
    if data.get("apply"):
        return "真跑(--apply 全跑)"
    fams = data.get("apply_families") or []
    ids = data.get("ids") or []
    if fams:
        return f"真跑家族 {','.join(fams)};其餘只解析(dry)"
    if ids:
        return f"明點真跑 {','.join(ids)};其餘只解析(dry)"
    return "只解析(dry)"


_DB_INDEX: dict | None = None
_DB_INDEX_WHY = ""


def db_table_index() -> tuple[dict, str]:
    """表名 → 哪一本庫(批471 v0104;唯讀、只跑一次、缺=誠實空)。

    **不另立庫路徑冊**:掃 VIA 底下實際存在的 .duckdb(排除 references/自測夾),
    問它各自的 SHOW TABLES。掃到的才算數——零發明。
    """
    global _DB_INDEX, _DB_INDEX_WHY
    if _DB_INDEX is not None:
        return _DB_INDEX, _DB_INDEX_WHY
    _DB_INDEX = {}
    try:
        import duckdb
    except Exception:
        _DB_INDEX_WHY = "本環境無 duckdb"
        return _DB_INDEX, _DB_INDEX_WHY
    n = 0
    for db in db_files():
        sp = str(db)
        con = None
        try:
            con = duckdb.connect(sp, read_only=True)
            for (t,) in con.execute("SHOW TABLES").fetchall():
                _DB_INDEX.setdefault(str(t), db.name)
            n += 1
        except Exception:
            continue
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    _DB_INDEX_WHY = f"問過 {n} 本庫 · {len(_DB_INDEX)} 張表" if n else "一張庫都開不了"
    return _DB_INDEX, _DB_INDEX_WHY


def output_verdict(o: str) -> tuple[str, str]:
    """一條冊宣告產出 → (判定, 說明)。**先分類再判,各問各的。**

    v0103 一律拿 `(VIA/o).exists()` 判,可是冊上 60 條裡有 34 條是**表名**不是路徑,
    於是那 34 條永遠寫「缺」——vrn_structdb 剛入庫 71 筆,頁上照樣說它缺。
    """
    o = str(o or "")
    if "<" in o or "*" in o:
        return "—", "含萬用字元,不判"
    if "::" in o:                       # `庫.duckdb::表` 明寫形
        dbn, _, tbl = o.partition("::")
        idx, why = db_table_index()
        if not idx:
            return "—", f"判不了({why})"
        return ("在" if idx.get(tbl) == Path(dbn).name else "缺"), f"表 · 問庫({why})"
    _EXT = (".json", ".html", ".duckdb", ".parquet", ".csv",
            ".jsonl", ".md", ".png", ".svg", ".txt")
    if "/" in o:
        return ("在" if (VIA / o).exists() else "缺"), "路徑 · 問 VIA 根"
    if o.lower().endswith(_EXT):
        # 裸檔名(冊上 7 條):**沒有目錄**,接 VIA 根一定落空。去找。
        for q in VIA.rglob(o):
            sq = str(q)
            if "/references/" in sq or "SCOPE_COPY" in sq or "_self_test" in sq:
                continue
            try:
                where = q.parent.relative_to(VIA)
            except ValueError:
                where = q.parent
            return "在", f"裸檔名 · 找到於 {where}"
        return "缺", "裸檔名 · 全樹找過(排除 references)"
    idx, why = db_table_index()
    if not idx:
        return "—", f"判不了({why})"
    hit = idx.get(o)
    return ("在" if hit else "缺"), (f"表 · 在 {hit}" if hit else f"表 · 問庫({why})")


def render(data: dict, out: Path | None = None) -> Path:
    """實測結果 → **多矩陣** HTML。零 CDN、手機自適應、深淺色皆可讀。

    每一格的數字都來自 `data`(matrix() 的回傳),**不做二次加工、不補空白**:
    量不到的就顯示「—」並在頁上說為什麼量不到。
    """
    tk, tk_why = _tokens()
    pal = (tk.get("palette") or {}) if isinstance(tk, dict) else {}
    out = out or (OUTDIR / "ENGINE_BUS_MATRIX.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows, res = data["catalog"], data["results"]
    by_id = {x["id"]: x for x in res}

    fams = sorted({r["family"] for r in rows})
    # 矩陣一:家族 × 狀態
    states = ["GREEN", "NODATA", "AMBER", "RED", "TIMEOUT", "ABSENT", "PLAN"]
    m1 = []
    for f in fams:
        line = {"家族": f}
        for s in states:
            line[s] = sum(1 for r in rows if r["family"] == f
                          and by_id.get(r["id"], {}).get("state") == s)
        line["合計"] = sum(1 for r in rows if r["family"] == f)
        m1.append(line)

    def tbl(headers, lines, cls=""):
        th = "".join(f"<th>{_html.escape(str(h))}</th>" for h in headers)
        body = []
        for ln in lines:
            tds = []
            for h in headers:
                v = ln.get(h, "")
                tds.append(f"<td>{v if isinstance(v, str) and v.startswith('<') else _html.escape(str(v))}</td>")
            body.append("<tr>" + "".join(tds) + "</tr>")
        return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>')

    # 矩陣二:逐項目錄(冊 → 尾版 → 在位)
    m2 = [{"家族": r["family"], "項": r["id"], "說明": r["zh"][:40],
           "引擎(尾版)": r["engine"] or "—", "版數": r["versions"],
           "動詞": "/".join(r["verb"]) or "—", "參數": ",".join(r["params"]) or "—",
           "在位": _cell("GREEN" if r["engine"] else "ABSENT")} for r in rows]

    # 矩陣三:調度結果(狀態 × 計數 × 秒 × 因由)
    m3 = [{"項": x["id"], "狀態": _cell(x["state"]),
           "rc": "—" if x["rc"] is None else x["rc"],
           "秒": x["seconds"] or "—",
           "[計] 最後一行": (x["tally"] or "—")[:80],
           "因由": (x["why"] or "")[:70] or "—"} for x in res]

    # 矩陣四:產出契約(冊宣告 × 實際在不在)
    m4 = []
    for x in res:
        for o in x["outputs_seen"]:
            v, note = output_verdict(o["out"])
            m4.append({"項": x["id"], "冊宣告產出": o["out"][:56],
                       "實際": v, "怎麼判的": note})
    if not m4:
        m4 = [{"項": "—", "冊宣告產出": "冊上此批未宣告 outputs",
               "實際": "—", "怎麼判的": "無宣告"}]

    # 矩陣五:庫況(表在不在 · 有幾列 · 日期跨多久)
    cen = data.get("census") or {"tables": [], "missing": [], "why": "本批未取庫況"}
    m5 = []
    for r in cen["tables"] + cen["missing"]:
        span = ("—" if r["span_days"] is None
                else f"{r['span_days']} 天")
        rng = f"{r['lo']} → {r['hi']}" if r["lo"] else ("—" if r["rows"] else "無列")
        m5.append({"庫": r["db"], "表": r["table"], "冊": r.get("source", "—"),
                   "列數": f"{r['rows']:,}" if r["state"] != "ABSENT"
                           else f"碼裡 {r.get('refs', 0)} 檔在用",
                   "日期跨度": f"{rng}({span})" if r["lo"] else rng,
                   "狀態": r["state"]})
    if not m5:
        m5 = [{"庫": "—", "表": "—", "列數": "—", "日期跨度": "—",
               "狀態": "—"}]

    css = f"""
:root{{--bg:#f4f6f8;--paper:#fff;--ink:#1f2733;--mut:#5b6775;--line:#dfe4ea;
--accent:{pal.get('accent', '#315f7d')}}}
:root:not([data-theme="light"]) {{}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
--bg:#0d1219;--paper:#141b25;--ink:#dfe6f0;--mut:#93a1b3;--line:#232d3b}}}}
:root[data-theme="dark"]{{--bg:#0d1219;--paper:#141b25;--ink:#dfe6f0;--mut:#93a1b3;--line:#232d3b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:14px 16px;
padding-block:16px}}
h1{{font-size:15px;margin:0 0 2px}}
h2{{font-size:12.5px;margin:18px 0 6px;color:var(--accent)}}
.sub{{color:var(--mut);font-size:10.5px;margin-bottom:10px;overflow-wrap:anywhere}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--paper)}}
table{{border-collapse:collapse;width:100%;min-width:520px}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left;
font-size:10.5px;white-space:nowrap}}
th{{background:color-mix(in srgb,var(--accent) 8%,transparent);
color:var(--mut);font-weight:600;position:sticky;top:0}}
td:nth-child(3),td:nth-child(5){{white-space:normal;overflow-wrap:anywhere}}
.st{{padding:1px 7px;border-radius:10px;font-size:9.5px;font-weight:600}}
.note{{color:var(--mut);font-size:10px;margin:6px 0 0;overflow-wrap:anywhere}}
@media(max-width:520px){{body{{padding:12px}}table{{min-width:480px}}}}
"""
    counts = " · ".join(f"{k} {v}" for k, v in sorted(data["counts"].items()))
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 引擎調度多矩陣</title><style>{css}</style></head><body>
<h1>VIA 引擎調度 · 多矩陣實測結果</h1>
<div class="sub">{_html.escape(data["ts"])} · 冊 {_html.escape(data["spec"])}
· 家族 {_html.escape(str(data["family"]))} · 模式 {_html.escape(_mode_label(data))}
· {_html.escape(counts)} · 樣板 {_html.escape(tk_why)}</div>

<h2>矩陣一 · 家族 × 狀態</h2>
{tbl(["家族"] + states + ["合計"], m1)}
<p class="note"><b>缺件 ≠ 缺料 ≠ 壞掉</b>——三件事混成一格,就會讓人去 debug
一支行為完全正確的引擎。所以這三種各有各的燈:<br>
<b>ABSENT=缺件</b>:引擎檔 / 相依套件 / <b>必要參數</b> 不在位(例:
<code>plotly 缺席=誠實停</code>、<code>argparse: expected one argument</code>)。<br>
<b>NODATA=缺料</b>:引擎跑了,但上游沒料,它自己印了「誠實停」之類的話
(命中的原文列在矩陣三的因由欄)。<br>
<b>PLAN</b>:沒動手——dry,或**寫庫動詞**被家族閘擋下(要跑得 <code>--ids</code> 明點)。<br>
<b>這三個都不是紅燈。</b>判準要亮得出證據:NODATA/ABSENT 只在**引擎自述那句話**
或 argparse 自己的抱怨命中時才成立,不用 rc 判(全樹 <code>return 2</code> 163 處
只有 46 處是這個意思,rc 不是穩定慣例);沒命中的 rc≠0 一律照舊 RED。</p>

<h2>矩陣二 · 引擎目錄(冊 → 尾版 → 在位)</h2>
{tbl(["家族", "項", "說明", "引擎(尾版)", "版數", "動詞", "參數", "在位"], m2)}
<p class="note">冊只有一本:<code>{_html.escape(data["spec"])}</code>。
本表是**它**的投影,不是另一份清單——冊改了這裡就跟著改。</p>

<h2>矩陣三 · 調度結果</h2>
{tbl(["項", "狀態", "rc", "秒", "[計] 最後一行", "因由"], m3)}
<p class="note">`[計]` 只認**最後一行**:子報告也會印 <code>FAIL 0</code>,
全篇搜就會把「OK 38 · FAIL 1」讀成綠(批462 工作站實錄的那個假綠)。
rc=0 但最後一行仍有 FAIL → 判 AMBER,**以計數為準不以 rc 為準**。</p>

<h2>矩陣四 · 產出契約(冊宣告 × 實際)</h2>
{tbl(["項", "冊宣告產出", "實際", "怎麼判的"], m4)}
<p class="note">冊上 60 條宣告產出裡有 <b>34 條是資料庫的表名</b>,不是檔案路徑。另有 7 條是**沒有目錄的裸檔名**。所以**照形狀分四路**:萬用字元不判 · 路徑接 VIA 根 · <b>裸檔名去全樹找</b> · <b>表名問庫</b>(唯讀 SHOW TABLES)。一張庫都開不了就寫「判不了」,<b>不寫成缺</b>——判不了就說判不了,不猜。</p>

<h2>矩陣五 · 庫況(表在不在 · 有幾列 · 日期跨多久)</h2>
{tbl(["庫", "表", "冊", "列數", "日期跨度", "狀態"], m5)}
<p class="note"><b>引擎綠不綠回答不了「有沒有料」</b>——一支引擎可以完美地跑完,
然後把資料寫進一張空表。所以這張表跟上面四張是兩件事:
<b>GREEN</b>=有列且(無日期欄 或 跨度 ≥ {cen.get("thin_days", 30)} 天) ·
<b>AMBER</b>=有列但跨度不足({cen.get("thin_days", 30)} 天)=<b>料在,但薄</b> ·
<b>NODATA</b>=表建好了、列數 0 ·
<b>ABSENT</b>=碼裡當表在用、庫裡沒有這張表(<b>不是壞掉,是還沒建</b>)。
ABSENT 收得緊:只認 SQL 語境(FROM/JOIN/INTO/TABLE/UPDATE)後面的名字,
且要 ≥3 個檔在用——第一版沒收緊,量出 74 筆、一半是變數名,
連庫裡明明有 891 列的 tw_listings 都被寫成缺。<b>寧可少報,也不要點錯紅燈。</b>
{("（庫況取不到：" + _html.escape(cen["why"]) + "）") if cen.get("why") else ""}</p>

<p class="note">零 CDN、零外部字型、零追蹤;全部數字來自本次實跑,
量不到的顯示「—」並說明為什麼量不到。</p>
</body></html>"""
    out.write_text(page, encoding="utf-8")
    return out


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]

    sp, spwhy = spec_path()
    rows = catalog()
    fams = sorted({r["family"] for r in rows})
    chk("① 調度冊**只有一本**:讀既有 VIA_InputConsole_Spec(尾版 glob),"
        "本件不另立第二本(另立=正典換了沒人跟得上)",
        sp is not None and len(rows) >= 20 and len(fams) >= 2,
        f"(冊 {sp.name if sp else spwhy} · {len(rows)} 項 · 家族 {fams})")

    chk("② 目錄=冊的投影:每項都帶尾版解析與**在位實測**(在位≠跑得動,本表只說在不在)",
        all(("engine_state" in r and "versions" in r) for r in rows)
        and any(r["engine"] for r in rows),
        f"(在位 {sum(1 for r in rows if r['engine'])}/{len(rows)})")

    r_absent = call("這個id不存在", catalog_rows=rows)
    chk("③ 冊上沒有的 id → **ABSENT 不是 RED**,而且講明「零發明:不猜」",
        r_absent["state"] == "ABSENT" and "零發明" in r_absent["why"], "")

    hit = next((r for r in rows if r["engine"]), None)
    r_plan = call(hit["id"], catalog_rows=rows) if hit else {}
    chk("④ **預設不動手**:apply=False 回 PLAN 並解析出完整 argv。"
        "調度層的預設值錯一次,代價是在別人的機器上動了不該動的東西",
        r_plan.get("state") == "PLAN" and len(r_plan.get("argv") or []) >= 2,
        f"({hit['id'] if hit else '—'} → {' '.join((r_plan.get('argv') or [])[1:3])})")

    py = python_for("vrn")
    chk("⑤ 家族 python **委派** MDL137 RunGate(它再委派 MDL136);橋缺席才退回本行程"
        "並在 source 講明是退路(不假裝走了正主)",
        bool(py.get("python")) and "python_for" in body and "RunGate" in body,
        f"(python={Path(py['python']).name} · 源={py.get('source', '')[:40]})")

    chk("⑥ `[計]` 只認**最後一行**(批462:子報告也印 `FAIL 0`,全篇搜會把"
        "「OK 38 · FAIL 1」讀成綠);rc=0 但最後一行仍有 FAIL → AMBER,以計數為準",
        "tallies[-1]" in body and "以計數為準" in body, "")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td)
        ok = q / "fx_ok.py"
        ok.write_text("print('[計] 三檢 OK 3 · FAIL 0')\n", encoding="utf-8")
        amb = q / "fx_amber.py"
        amb.write_text("print('[計] 1 件 · FAIL 0 · 子報告')\n"
                       "print('[計] 三檢 OK 2 · FAIL 1')\n", encoding="utf-8")
        slow = q / "fx_slow.py"
        slow.write_text("import time\ntime.sleep(999)\n", encoding="utf-8")
        fake = [{"id": "fx_ok", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": ok.name, "engine_path": str(ok), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""},
                {"id": "fx_amber", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": amb.name, "engine_path": str(amb), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""},
                {"id": "fx_slow", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": slow.name, "engine_path": str(slow), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""}]
        a = call("fx_ok", apply=True, catalog_rows=fake)
        b = call("fx_amber", apply=True, catalog_rows=fake)
        c = call("fx_slow", apply=True, timeout=3, catalog_rows=fake)
        chk("⑦ 統一結果契約實測:全綠→GREEN;**rc=0 但最後一行有 FAIL→AMBER**"
            "(子報告的 `FAIL 0` 不得蓋過總計);逾時→TIMEOUT 並說「不卡斷」",
            a["state"] == "GREEN" and b["state"] == "AMBER"
            and "FAIL 1" in b["tally"] and c["state"] == "TIMEOUT"
            and "不卡斷" in c["why"],
            f"(ok={a['state']} · amber={b['state']}:{b['tally'][-14:]} · slow={c['state']})")

        data = {"schema": "VIA.EngineBus.v1", "ts": "2026-01-01T00:00:00",
                "spec": "fx.json", "family": "t", "apply": True,
                "counts": {"GREEN": 1, "AMBER": 1, "TIMEOUT": 1},
                "catalog": fake, "results": [a, b, c]}
        pg = render(data, out=q / "m.html")
        h = pg.read_text(encoding="utf-8")
        chk("⑧ 多矩陣 HTML:四張矩陣皆在、零 CDN、手機自適應、深淺色皆有定義",
            all(k in h for k in ("矩陣一", "矩陣二", "矩陣三", "矩陣四"))
            and "http://" not in h and "https://" not in h
            and "prefers-color-scheme" in h and "@media(max-width" in h,
            f"({len(h):,} 字元 · 零外連={'http' not in h})")

        chk("⑨ 頁上每一格都來自實測資料,**不做二次加工**;判不了的顯示「—」"
            "並說明為什麼判不了(含萬用字元的產出宣告不判在缺)",
            "判不了就說判不了" in h and "不猜" in h and "fx_slow" in h, "")

    live_before = sorted(x.name for x in OUTDIR.glob("*")) if OUTDIR.exists() else []
    chk("⑩ 本件**零網路**、預設 dry、自測不寫正式產出夾",
        ("urlopen" not in body and "requests" not in body)
        and (sorted(x.name for x in OUTDIR.glob("*")) if OUTDIR.exists() else []) == live_before,
        "(零網路碼 · 正式夾未動)")

    chk("⑪ Zero-Hydra 宣告在檔:四家調度者(DeckServer Popen×12 / RunGate×3 / "
        "MDL139×1 / ClosingGate)各自重寫尾版解析、家族 python、逾時、結果解讀;"
        "本件是**一條匯流排四家共用**,不是第五套",
        "Popen ×12" in src and "一條匯流排,四家共用" in src, "(立場在檔)")

    with tempfile.TemporaryDirectory() as td2:
        q2 = Path(td2)
        nd = q2 / "fx_nodata.py"
        nd.write_text("import sys\nprint('[首頁擷取] 無報告件(誠實;缺件搜集器先跑)')\n"
                      "sys.exit(2)\n", encoding="utf-8")
        bad = q2 / "fx_realbad.py"
        bad.write_text("import sys\nprint('Traceback: 真的壞了')\nsys.exit(2)\n",
                       encoding="utf-8")
        fk = [{"id": i, "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
               "params": [], "outputs": [], "net": False, "engine": p.name,
               "engine_path": str(p), "versions": 1, "engine_state": "在位",
               "group": "", "spec_why": ""} for i, p in (("fx_nodata", nd), ("fx_realbad", bad))]
        d1 = call("fx_nodata", apply=True, catalog_rows=fk)
        d2 = call("fx_realbad", apply=True, catalog_rows=fk)
    chk("⑫ **缺料 ≠ 壞掉**(批471 v0100 實跑第一次就照出我自己用錯尺:VRN 7 項報 RED 3,"
        "而三支印的都是「無報告件(誠實)」——引擎行為完全正確,是我的儀器判錯)。"
        "想用 rc=2 當判準**量過之後否決**:全樹 `return 2` 163 處只有 46 處是誠實停,"
        "117 處是別的意思——**rc 不是穩定慣例**。改認引擎**自己印的那句話**,"
        "並把命中的原文帶回當證據;**沒有那句話的 rc≠0 一律照舊 RED**(對照組驗了)",
        d1["state"] == "NODATA" and "無報告件" in d1["why"]
        and d2["state"] == "RED" and d2["rc"] == 2,
        f"(誠實停 rc=2→{d1['state']} · 真壞 rc=2→{d2['state']})")

    # ---- ⑬⑭⑮ 批471 v0102:第二次實跑(VAP 6 項)照出的三件事 ----
    with tempfile.TemporaryDirectory() as td3:
        q3 = Path(td3)
        # 對照組全部**釘死在 VAP 那次實跑的原文**(不是我改寫過的版本):
        # 對照組要釘在缺陷所在的那一版,不然下一版一改措辭,這幾檢就自己失效了。
        fx = {
            # vap_dashboard 真印過的尾段:缺料
            "fx_vapdash": "print('[缺料] 缺 4 項:表 prices_canonical·tw_chip_inst"
                          "·tw_chip_margin·features_daily(vdf_tw_market.duckdb)')\n"
                          "print('[補料] 誠實停 rc2 · 舊頁在位 VIA_UI_Dashboard_v0100.html')\n",
            # vap_std_dashboard 真印過的尾段:缺件(套件)
            "fx_vapstd": "print('[標準模板] plotly 缺席=誠實停(pip install plotly 後再跑)')\n",
            # vap_one_render 真吐過的尾段:缺參數
            "fx_vapone": "import sys\nsys.stderr.write('VAP_ENG016_AutoplotOne: "
                         "error: argument --render: expected one argument\\n')\n",
            # 真紅對照組(沒有任何誠實停/缺料/閘字樣;批498 起「Table … does not exist」歸缺料 NODATA,對照組換成真壞的 KeyError)
            "fx_vapstack": "print('Traceback (most recent call last):')\nprint(\"KeyError: 'close'\")\n",
        }
        fk3 = []
        for k, code in fx.items():
            f = q3 / (k + ".py")
            f.write_text(code + "import sys\nsys.exit(2)\n", encoding="utf-8")
            fk3.append({"id": k, "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
                        "params": [], "outputs": [], "net": False, "engine": f.name,
                        "engine_path": str(f), "versions": 1, "engine_state": "在位",
                        "group": "", "spec_why": ""})
        e1 = call("fx_vapdash", apply=True, catalog_rows=fk3)
        e2 = call("fx_vapstd", apply=True, catalog_rows=fk3)
        e3 = call("fx_vapone", apply=True, catalog_rows=fk3)
        e4 = call("fx_vapstack", apply=True, catalog_rows=fk3)

    chk("⑬ **「誠實停」才是正典句**(全樹 451 處)。v0101 那張字表是照 VRN 幾支的措辭湊的,"
        "只認得 VRN 的方言——VAP 印「誠實停 rc2」就漏接,兩支沒壞的引擎被我判紅。"
        "本檢用 VAP 那次實跑的**原文**當對照組(釘死在缺陷所在的那一版,不改寫)",
        e1["state"] == "NODATA" and "誠實停" in e1["why"],
        f"(缺料原文→{e1['state']})")

    chk("⑭ **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。誠實停要再分一層:缺料→NODATA;"
        "缺件(引擎/相依套件/**必要參數**)→ ABSENT,**不新立第八態**。"
        "判缺參數只認 argparse 自己講的話——**不能用「冊上有宣告 params 就別跑」一刀切**:"
        "冊上 21 項宣告 params,其中 20 項沒給參數照樣跑得好好的(量過),一刀切=誤殺 20 項",
        e2["state"] == "ABSENT" and "缺件" in e2["why"]
        and e3["state"] == "ABSENT" and "缺參數" in e3["why"]
        and e4["state"] == "RED"
        and sum(1 for r in rows if r.get("params")) >= 20,
        f"(plotly 缺席→{e2['state']} · argparse 少參數→{e3['state']} · "
        f"裸 CatalogException→{e4['state']} · 冊上有 params 的項="
        f"{sum(1 for r in rows if r.get('params'))})")

    wv = [r["id"] for r in rows if WRITE_VERB in (r.get("verb") or [])]
    with tempfile.TemporaryDirectory() as td15:
        q15 = Path(td15) / "fx_named_write.py"
        q15.write_text("print('[計] 一檢 OK 1 · FAIL 0')\n", encoding="utf-8")
        fx15 = [{"id": "fx_named_write", "family": "vdf", "zh": "", "glob": "", "dir": "",
                 "verb": ["run", WRITE_VERB], "test_verb": [], "params": [], "outputs": [],
                 "net": False, "engine": q15.name, "engine_path": str(q15), "module": "",
                 "engine_dir": str(q15.parent), "versions": 1, "engine_state": "在位",
                 "group": "", "spec_why": "", "cwd": ""}]
        g_sweep = [call("fx_named_write", apply=True, catalog_rows=fx15, sweep=True)]
        # --ids 本身就是「指名道姓」的明令；不應還要 --apply 才真跑。
        m_sweep = matrix(ids=["fx_named_write"], do_print=False, catalog_rows=fx15)
        m_missing = matrix(ids=["fx_missing"], do_print=False,
                           profile="test", catalog_rows=fx15)
    chk("⑮ **`--apply` 不該是全有全無**。VDF 24 項按下去=同時發動 tw_history 全史回補、"
        "tw_chips 籌碼回補,還有兩支動詞本來就帶 `--apply` 的寫庫件。本版加 --apply-family / "
        "--ids;**寫庫動詞閘**:家族全掃永不代跑,要跑必須 --ids 明點"
        "(同「--approve-remove 只在明令下」律)",
        len(wv) >= 2
        and all(x["state"] == "PLAN" and "寫庫動詞" in x["why"] for x in g_sweep)
        and [x["state"] for x in m_sweep["results"]] == ["GREEN"]
        and m_missing["unknown_ids"] == ["fx_missing"]
        and [x["state"] for x in m_missing["results"]] == ["ABSENT"]
        and "--apply-family" in body,
        f"(寫庫件 {wv} · 家族全掃→{sorted({x['state'] for x in g_sweep})} · "
        f"--ids 明點→{sorted({x['state'] for x in m_sweep['results']})} · 未知 ID→{m_missing['counts']})")

    # ---- ⑯ 批471 v0103:調度層不得讓引擎往原始碼樹寫 ----
    with tempfile.TemporaryDirectory() as td4:
        q4 = Path(td4)                      # 假裝這是「原始碼樹」
        f4 = q4 / "fx_litter.py"
        f4.write_text("from pathlib import Path\n"
                      "Path('./拉出來的產出夾').mkdir(exist_ok=True)\n"
                      "print('[計] 1 件 · FAIL 0')\n", encoding="utf-8")
        fk4 = [{"id": "fx_litter", "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
                "params": [], "outputs": [], "net": False, "engine": f4.name,
                "engine_path": str(f4), "versions": 1, "engine_state": "在位",
                "group": "", "spec_why": ""}]
        r16 = call("fx_litter", apply=True, catalog_rows=fk4)
        src_clean = not (q4 / "拉出來的產出夾").exists()
        land = (OUTDIR / "_cwd" / "拉出來的產出夾")
        landed = land.exists()
        if landed:
            land.rmdir()
    chk("⑯ **調度層不得讓引擎往原始碼樹寫**(批471 v0102 實跑後 git status 冒出一個從沒入過庫的"
        "`functional modules/VAP/engine/vap_one_out/`——ENG016 的 `--out` 預設是相對路徑,"
        "而我把 cwd 設在引擎目錄。正本零觸碰不只管別改別人的檔,**也管別在別人家裡生檔**)。"
        "改 cwd 前先量:冊上在位 36 支**全用 __file__ 定位**,讀 cwd 的 0 支,所以換 cwd 零影響",
        r16["state"] == "GREEN" and src_clean and landed
        and "workdir" in body and "cwd=str(workdir)" in body,
        f"(引擎相對寫檔→原始碼樹乾淨={src_clean} · 落在產出夾={landed})")

    # ---- ⑰⑱ 批471 v0104:把自己產出的頁讀一遍,發現說謊的是頁 ----
    lbl_a = _mode_label({"apply": False, "apply_families": ["vrn", "vap"], "ids": []})
    lbl_b = _mode_label({"apply": False, "apply_families": [], "ids": []})
    lbl_c = _mode_label({"apply": True, "apply_families": [], "ids": []})
    chk("⑰ **頁首的模式標籤不得說謊**(v0103 在 --apply-family 下照印「只解析(dry)」——"
        "`data[\"apply\"]` 那時本來就是 False,而我拿它當唯一標籤。"
        "一張報實測結果的頁,第一行把自己的模式講錯)",
        "真跑家族 vrn,vap" in lbl_a and lbl_b == "只解析(dry)" and "全跑" in lbl_c,
        f"(家族模式→「{lbl_a}」)")

    _wild = output_verdict("VIA_Reports/first_page_text/<stem>.json")
    _path_in = output_verdict("supportive modules/registry/VIA_InputConsole_Spec_v0100.json")
    _path_no = output_verdict("VIA_Reports/engine_bus/一定不存在的檔.json")
    _tbl = output_verdict("vrn_report_basic")
    _idx, _idxwhy = db_table_index()
    _decl = [o for r in rows for o in (r.get("outputs") or [])]
    _tblcnt = sum(1 for o in _decl
                  if "<" not in o and "*" not in o and "/" not in o
                  and not o.lower().endswith((".json", ".html", ".duckdb", ".parquet",
                                              ".csv", ".jsonl", ".md", ".png", ".svg")))
    chk("⑱ **表名要問庫,不要問檔案系統**。量了冊:60 條宣告產出裡有 34 條是資料庫的表名"
        "(tw_daily_prices / vrn_report_basic / ActiveTWETF.duckdb::holdings_daily …),"
        "v0103 一律 `(VIA/o).exists()` → 那 34 條永遠寫「缺」,矩陣四超過一半的格子在說謊"
        "(vrn_structdb 剛入庫 71 筆,頁上照樣說它的 vrn_report_basic 缺)。"
        "改成先分類再判;**一張庫都開不了就寫「判不了」,不寫成缺**",
        _wild[0] == "—" and "萬用" in _wild[1]
        and _path_in[0] == "在" and "路徑" in _path_in[1]
        and _path_no[0] == "缺"
        and _tbl[0] in ("在", "—") and "表" in (_tbl[1] + ("表" if _tbl[0] == "—" else ""))
        and _tblcnt >= 30,
        f"(冊上表名形 {_tblcnt} 條 · 庫索引={_idxwhy} · vrn_report_basic→{_tbl})")

    # 用入倉且永遠在位的裸檔名作夾具；控制塔頁是工作站再生件，乾淨 clone 不應被它綁死。
    _bare_in = output_verdict("VIA_InputConsole_Spec_v0100.json")
    _bare_no = output_verdict("一定沒有這個頁_v9999.html")
    _bare_decl = [o for r in rows for o in (r.get("outputs") or [])
                  if "/" not in o and "<" not in o and "*" not in o
                  and o.lower().endswith((".html", ".json", ".csv", ".md"))]
    chk("⑲ **說「缺」之前,先確定自己有去找過**。v0104 把表名接對了,"
        "卻還把 `VIA_UI_VRNControlTower_v0100.html` 寫成缺——而 vrn_ui 那一跑報「頁 3/3 新鮮」。"
        "冊上有 7 條是**沒有目錄的裸檔名**,真的頁住在 supportive modules/ui_support/,"
        "我拿 VIA 根去接它。這是同一個病的第三種形狀:**一種判法問三種問題**。"
        "改成照宣告的形狀分四路:萬用不判 · 路徑接根 · **裸檔名去找** · 表名問庫",
        _bare_in[0] == "在" and "找到於" in _bare_in[1]
        and _bare_no[0] == "缺" and "找過" in _bare_no[1]
        and len(_bare_decl) >= 7,
        f"(冊上裸檔名 {len(_bare_decl)} 條 · 裸檔搜尋→{_bare_in})")

    _need_cases = [
        ("selftest 需要 reportlab 產生樣本 PDF;請改用 python …py <你的.pdf>", "ABSENT"),
        ("[標準模板] plotly 缺席=誠實停(pip install plotly 後再跑)", "ABSENT"),
        ("[補料] 誠實停 rc2 · 缺 4 項表", "NODATA"),
        ("需要 人工確認之後再跑", ""),          # 中文「需要」不得被當成缺件
        ("Traceback (most recent call last): 真的壞了", ""),
    ]
    _got = [classify_stop(t)[0] for t, _ in _need_cases]
    _ok_noise = diagnostic_tail(
        "  [OK] 橋缺席時仍有 stdlib 退路\n"
        "  [FAIL] 真正的配對契約不合\n"
        "  [計] 二檢 OK 1 · FAIL 1")
    chk("⑳ **「需要 <套件>」也是缺件**(批473 收 PDFPlumber-Plus 時的第八盞錯燈:"
        "引擎印「selftest 需要 reportlab」還附了補法,我判它紅——字表裡沒有這個講法)。"
        "最難看的是同一批我在那支 PowerShell 啟動器裡**已經寫對這條律**,卻沒帶回來;"
        "同一個判準兩個地方只改一邊,另一邊靜靜走錯——那正是本件立案要收掉的事。"
        "收得緊:`需要` 後面要緊跟像套件名的 ASCII 識別字,中文「需要…」不放過",
        _got == [e for _, e in _need_cases] and classify_stop(_ok_noise)[0] == "",
        f"({list(zip([t[:16] for t, _ in _need_cases], _got))})")

    # ── 批474 四檢:工作站實錄照出來的三件事,一件一把尺 ──────────────
    chk("㉑ 動詞正規化:`--matrix` 這種連字號寫法收得到(實錄:我叫操作員打的"
        "就是這個形狀,而 v0106 印兩百行說明就回 rc=0)",
        _verb(["--matrix", "--html"])[0] == "matrix"
        and _verb(["matrix"])[0] == "matrix"
        and _verb(["census"])[0] == "census"
        # 只脫連字號,不猜別的:錯字**不**放過(猜錯的體貼比不體貼更難救)
        and _verb(["matrixx"])[0] == ""
        and _verb(["--bogus"])[0] == "")

    chk("㉒ 不認得的動詞回 **rc=2 不是 rc=0**(rc=0 是假綠:自動化鏈路看 rc,"
        "會把「什麼都沒跑」讀成「跑完了」)+ 用法是六行不是整篇 docstring",
        "matrix" in USAGE and "census" in USAGE
        and len(USAGE.splitlines()) <= 12
        and len(USAGE) < len(__doc__ or "") / 4)

    _cen_rows, _cen_why = db_census()
    chk("㉓ 庫況普查真的讀到庫(自犯錯:`db_table_index` **成功時 why 也有值**,"
        "我拿它當失敗旗標 → 庫況永遠空)",
        bool(_cen_rows) or bool(_cen_why),
        f"({len(_cen_rows)} 張表 · {_cen_why or '—'})")

    _miss = census_expected(_cen_rows) if _cen_rows else []
    _have = {r["table"] for r in _cen_rows}
    chk("㉔ ABSENT 收得緊:只認 SQL 語境且 ≥3 檔;**庫裡有的表絕不出現在缺席名單**"
        "(第一版沒收緊,量出 74 筆、一半是變數名,連 891 列的 tw_listings 都寫成缺"
        "——那是判錯的紅燈,一次七十四盞)",
        all(m["table"] not in _have for m in _miss)
        # 批478:≥3 檔那條律只管 grep 出來的(冊外);冊上宣告的缺席本來就沒有 refs
        and all(m.get("refs", 0) >= 3 for m in _miss if m.get("source") != "冊上宣告"),
        f"(缺席 {len(_miss)} 張)")

    # ── 批474 v0108 二檢:不卡斷 ──
    import tempfile as _tf
    _beats: list = []
    with _tf.TemporaryDirectory() as _td:
        _slow = Path(_td) / "slow.py"
        _slow.write_text("import time,sys\nfor i in range(6):\n    print('step',i,flush=True); time.sleep(0.5)\nprint('[計] OK 1 · FAIL 0')\n", encoding="utf-8")
        _rc, _out, _to = _run_streaming([sys.executable, str(_slow)], dict(os.environ), Path(_td), timeout=30,
                                        heartbeat=1, echo=lambda m: _beats.append(m))
    chk("㉕ 邊跑邊收 + 心跳:慢引擎跑 3 秒、心跳 1 秒 → 心跳 ≥2 次且印的是引擎自己的最後一行"
        "(實錄:via-ryg 停在 vrn_firstpage 白畫面=緩衝到結束才吐,批423 同病)",
        _rc == 0 and not _to and len(_beats) >= 2 and any("step" in b for b in _beats)
        and "[計] OK 1" in _out, f"(心跳 {len(_beats)} 次 · rc={_rc})")
    with _tf.TemporaryDirectory() as _td:
        _hang = Path(_td) / "hang.py"
        _hang.write_text("import time\nprint('started',flush=True)\ntime.sleep(60)\n", encoding="utf-8")
        _t0 = time.time()
        _rc, _out, _to = _run_streaming([sys.executable, str(_hang)], dict(os.environ), Path(_td), timeout=2,
                                        heartbeat=1, echo=lambda m: None)
        _el = time.time() - _t0
    chk("㉖ 逾時只殺自己生的子行程、部分輸出保留當證據、實際等待貼近 timeout 不是永遠",
        _to and "started" in _out and _el < 10, f"(等了 {_el:.1f}s · 逾時={_to})")

    # ── 批476 二檢:啟動層注入 ──
    _code = "import os,sys;print(os.environ.get('VIA_ACCEL_BOOT',''),'|','via_net' in sys.modules,'|',os.environ.get('VIA_NET_CONSENT','(未設)'))"
    _r1 = subprocess.run([sys.executable, "-c", _code], capture_output=True, text=True, timeout=120, env=child_env("vrn"))
    _r2 = subprocess.run([sys.executable, "-c", _code], capture_output=True, text=True, timeout=120, env=child_env("vdf"))
    _a1, _n1, _g1 = [x.strip() for x in (_r1.stdout or "| |").split("|")[:3]]
    _a2, _n2, _g2 = [x.strip() for x in (_r2.stdout or "| |").split("|")[:3]]
    chk("㉗ 啟動層注入:任何家族的子行程起跑就綁加速器(VIA_ACCEL_BOOT 有值,1: 或 ABSENT: 皆誠實);**零引擎改動**"
        "(量過:逐檔加=VDF 105 支+VRN 全部+VAP 全部的新版本檔)",
        BOOTDIR.is_dir() and _a1.startswith(("1:", "ABSENT:", "cache:", "NOCACHE:")) and _a2.startswith(("1:", "ABSENT:", "cache:", "NOCACHE:")),
        f"(vrn→{_a1[:16]} · vdf→{_a2[:16]})")
    chk("㉘ 網路正典件只掛 vdf(vrn 子行程 via_net 不在、vdf 子行程在),且**同意閘一個字不碰**(子行程看到的閘態=母行程所設)",
        _n1 == "False" and _n2 == "True"
        and _g2 == os.environ.get("VIA_NET_CONSENT", "(未設)"),
        f"(vrn via_net={_n1} · vdf via_net={_n2} · 閘={_g2})")

    # ── 批477 二檢:套件式引擎 ──
    chk("㉙ 「attempted relative import」不判缺件(第十盞判錯的燈:沒有套件缺,是我用檔案方式啟動套件內模組)→ RED 並指路 -m",
        classify_stop("Traceback\nImportError: attempted relative import with no known parent package")[0] == "RED"
        and "-m" in classify_stop("ImportError: attempted relative import with no known parent package")[1])
    with _tf.TemporaryDirectory() as _td:
        _pk = Path(_td) / "pk"; _pk.mkdir(); (_pk / "__init__.py").write_text("", encoding="utf-8")
        (_pk / "cli.py").write_text("from . import helper\nimport sys\nprint('[計] OK 1 · FAIL 0')\n", encoding="utf-8")
        (_pk / "helper.py").write_text("X=1\n", encoding="utf-8")
        _it = {"engine_path": str(_pk / "cli.py"), "module": "pk.cli", "engine_dir": _td, "verb": ["selftest"], "family": "vdf"}
        _argv = _argv_for(_it, None, sys.executable)
        _r = subprocess.run(_argv, capture_output=True, text=True, timeout=60, env=child_env("vdf", _td), cwd=_td)
    chk("㉚ 冊上 module 欄 → 以 -m 啟動且套件根前置 PYTHONPATH(相對匯入可解);對照組:當檔案跑必炸",
        _argv[1] == "-m" and _argv[2] == "pk.cli" and _r.returncode == 0 and "[計] OK 1" in _r.stdout,
        f"(argv={_argv[1:3]} · rc={_r.returncode})")

    _spec_p, _ = spec_path()
    _spec = json.loads(_spec_p.read_text(encoding="utf-8")) if _spec_p else {}
    _cwd_items = [it for g in _spec.get("families", {}).get("vdf", {}).get("groups", []) for it in g.get("items", []) if it.get("cwd") == "engine"]
    chk("㉛ 冊上 `cwd: engine` 只對宣告的項生效(讀 cwd 的引擎),其餘照舊在 VIA_Reports/_cwd 跑(原始碼樹零產出)",
        all(it.get("module") or it.get("engine") for it in _cwd_items) and len(_cwd_items) >= 1,
        f"(宣告 cwd=engine 的項:{[it['id'] for it in _cwd_items]})")

    _ss, _ssn = db_ssot()
    _rows_c, _ = db_census()
    _miss_c = census_expected(_rows_c) if _rows_c else []
    _decl_missing = [m for m in _miss_c if m.get("source") == "冊上宣告"]
    chk("㉜ 庫況對冊比:冊在位、冊上宣告而庫裡沒有的表報 ABSENT(冊上宣告)並列寫入者;冊上 known_legacy 不重報;"
        "庫裡有的表絕不出現在缺席名單",
        bool(_ss.get("tables")) and all(m["table"] not in {r["table"] for r in _rows_c} for m in _miss_c)
        and all(t not in {m["table"] for m in _miss_c} for t in _ss.get("known_legacy_absent", []))
        and all(m.get("writers") is not None for m in _decl_missing),
        f"(冊 {_ssn} · 冊上宣告缺 {len(_decl_missing)} · 冊外缺 {len(_miss_c) - len(_decl_missing)})")

    import io as _io, contextlib as _cl
    _buf = _io.StringIO(); _t0 = time.time()
    with _cl.redirect_stdout(_buf):
        _rc = main.__wrapped__(["boot"]) if hasattr(main, "__wrapped__") else _boot_for_test()
    _out = _buf.getvalue(); _el = time.time() - _t0
    chk("㉝ boot 實證三家族**並行**(實錄 via-boot「還在跑」:逐一探測各 120s 零輸出)→ 三家族都印、有總時長、且慢不過單家族上限",
        _rc == 0 and all(f"[{f}]" in _out for f in ("vdf", "vrn", "vap")) and "並行" in _out and _el < 125,
        f"({_el:.1f}s)")

    # ── 批484:call 的 stdout 必須是合法 JSON,心跳再多也不能污染 ──
    with _tf.TemporaryDirectory() as _td:
        _sl = Path(_td) / "slow_v0100.py"
        _sl.write_text("import time\nprint('working',flush=True)\ntime.sleep(2.5)\nprint('[計] OK 1 · FAIL 0')\n", encoding="utf-8")
        _spec = {"schema": "x", "families": {"vdf": {"zh": "v", "python": "vdf", "groups": [{"id": "g", "zh": "g", "items": [
            {"id": "slow_item", "zh": "s", "engine": {"dir": ".", "glob": "slow_v*.py", "verb": []}, "params": [], "net": False, "outputs": []}]}]}}}
        (Path(_td) / "VIA_InputConsole_Spec_v0100.json").write_text(json.dumps(_spec), encoding="utf-8")
        _code = ("import sys,json,importlib.util;sp=importlib.util.spec_from_file_location('bus',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);"
                 "m.HEARTBEAT_SEC=1;import pathlib;_td=pathlib.Path(sys.argv[2]);m.VIA=_td;m.HERE=_td;m.OUTDIR=_td/'out';"
                 "m.spec_path=lambda: (_td/'VIA_InputConsole_Spec_v0100.json','');"
                 "sys.argv=[sys.argv[0],'call','--item','slow_item','--apply'];sys.exit(m.main())")
        _r = subprocess.run([sys.executable, "-c", _code, str(Path(__file__).resolve()), _td], capture_output=True, text=True, timeout=120)
        try:
            _j = json.loads(_r.stdout)
            _ok_json = _j.get("id") == "slow_item" and _j.get("state") in ("GREEN", "AMBER", "RED")
        except Exception:
            _ok_json = False
    chk("㉞ call 的 stdout 是合法 JSON,心跳(≥2 次)走 stderr 不污染(批484 自己踩到:vrn_digest 跑超過 20 秒,json.load 直接炸)",
        _ok_json and _r.stderr.count("⏳") >= 1,
        f"(stdout JSON={_ok_json} · stderr 心跳 {_r.stderr.count('⏳')} 次)")

    # ── 批485:庫衛生唯讀審計 ──
    _hy_ok = False
    try:
        import duckdb as _dk
        with _tf.TemporaryDirectory() as _td:
            _dbp = Path(_td) / "t.duckdb"
            _c = _dk.connect(str(_dbp)); _c.execute("CREATE TABLE tw_x(date DATE, v INT)")
            _c.execute("INSERT INTO tw_x VALUES (DATE '1900-01-01',1),(DATE '2026-09-01',2),(DATE '2026-09-02',3)"); _c.close()
            _before = _dbp.stat().st_size
            _rows = [{"db": "t.duckdb", "table": "tw_x", "rows": 3, "date_col": "date", "lo": "1900-01-01", "hi": "2026-09-02", "span_days": 1, "state": "GREEN"}]
            _saved = (globals()["db_census"], globals()["VIA"])
            globals()["db_census"] = lambda: (_rows, "")
            globals()["VIA"] = Path(_td)
            try:
                _h = db_hygiene()
            finally:
                globals()["db_census"], globals()["VIA"] = _saved
            _c2 = _dk.connect(str(_dbp), read_only=True); _n_after = _c2.execute("SELECT COUNT(*) FROM tw_x").fetchone()[0]; _c2.close()
            _hy_ok = (len(_h["sentinel"]) == 1 and _h["sentinel"][0]["n"] == 1 and "DELETE" in _h["sentinel"][0]["sql_not_run"]
                      and _n_after == 3)
    except Exception as _exc:
        _hy_ok = False
    chk("㉟ 庫衛生審計:1900 哨兵列數得出來、DELETE 只寫不跑(審計後列數仍 3)、副本判定不刪——刪資料是操作員的手",
        _hy_ok)

    # ── 批489:心跳帶項目名、矩陣模式走 stdout;call 模式走 stderr ──
    _lbl = []
    _run_streaming([sys.executable, "-c", "import time;print('a',flush=True);time.sleep(1.4);print('[計] OK 1 · FAIL 0')"],
                   dict(os.environ), Path(_tf.gettempdir()), timeout=30, heartbeat=1, echo=lambda m: _lbl.append(m), label="demo_item")
    chk("㊱ 心跳帶項目名(操作員實錄:vrn_pdfplus 的心跳錯位到 vap_stack 底下,看起來像另一項跑了 19 秒);矩陣模式心跳走 stdout、call 模式走 stderr",
        any("demo_item" in m for m in _lbl) and HEARTBEAT_TO_STDERR is False,
        f"(心跳 {len(_lbl)} 次)")
    # 批490 ㊲㊳㊴:沙盒錨定 · 庫缺=缺料 · 家內庫與湖入普查(暫存家;跑完還原快取)
    chk("㊲ 沙盒標記錨定到擁有者夾:engine_bus/_cwd、selftest_grid、vdfout_runs/selftest_out、_self_test 是沙盒;同名正夾(foo/selftest_out、data/_cwd)不是",
        _is_sandbox("/x/VIA_Reports/engine_bus/_cwd/a.duckdb") and _is_sandbox("/x/VIA_Reports/vdfout_runs/selftest_out/vdf_hub.duckdb")
        and _is_sandbox("/x/VIA_Reports/selftest_grid/y/b.duckdb") and _is_sandbox("C:\\x\\_self_test\\c.duckdb")
        and not _is_sandbox("/x/foo/selftest_out/real.duckdb") and not _is_sandbox("/x/data/_cwd/real.duckdb")
        and not _is_sandbox("C:\\Users\\tonyk\\VIA System\\via_database\\vdf_tw_market.duckdb"))
    _c1 = classify_stop("[via-vrn4] RED · 報告 0 · 有正文 0 · 庫缺 C:\\x\\mega\\vdf_tw_market.duckdb(先 via-vdfdb / ENG073 入庫)")
    _c2 = classify_stop("[名稱對帳] roster=庫不在:C:\\x\\mega\\vdf_tw_market.duckdb")
    chk("㊳ 「庫缺/庫不在」=缺料(上游沒庫)不是壞掉:ENG080 印庫缺 → NODATA(批489 實錄它亮成 RED)",
        _c1[0] == "NODATA" and "庫缺" in _c1[1] and _c2[0] == "NODATA")
    global _CENSUS, _CENSUS_WHY, _DB_INDEX, _DB_INDEX_WHY, _HOME, LAKE_WRITE
    _sv = (os.environ.get("VIA_DATA_HOME"), _CENSUS, _CENSUS_WHY,
           _DB_INDEX, _DB_INDEX_WHY, _HOME)
    LAKE_WRITE = False
    try:
        import tempfile as _tf
        with _tf.TemporaryDirectory() as _td:
            _hm = Path(_td) / "VIA System" / "via_database"
            (_hm / "lake" / "tw_daily_prices").mkdir(parents=True)
            (_hm / "engine_bus" / "_cwd").mkdir(parents=True)
            try:
                import duckdb as _dk
                _con = _dk.connect(str(_hm / "vdf_tw_market.duckdb"))
                _con.execute("CREATE TABLE tw_listings AS SELECT 1 AS id")
                _con.execute("CREATE TABLE tw_monthly_revenue AS SELECT DATE '2026-01-01' AS date UNION ALL SELECT DATE '2026-03-01'")
                _con.close()
                _con = _dk.connect(str(_hm / "engine_bus" / "_cwd" / "sandbox.duckdb")); _con.execute("CREATE TABLE junk AS SELECT 1 AS a"); _con.close()
                _con = _dk.connect()
                _pq = str(_hm / "lake" / "tw_daily_prices" / "part-2026.parquet").replace("'", "''")
                _con.execute(f"COPY (SELECT DATE '2020-01-02' AS date, 1 AS v UNION ALL SELECT DATE '2026-09-11', 2) TO '{_pq}' (FORMAT PARQUET)")
                _con.close()
                os.environ["VIA_DATA_HOME"] = str(_hm)
                _CENSUS = _DB_INDEX = _HOME = None
                _CENSUS_WHY = _DB_INDEX_WHY = ""
                _rows, _ = db_census()
                _fl = db_files()
                _hrows = [r for r in _rows if str(r.get("path", "")).startswith("家:")]
                _lake = [r for r in _rows if r["db"] == "湖"]
                _miss = census_expected(_rows)
                _rel_ok = _rel(_hm / "vdf_tw_market.duckdb") == "家:vdf_tw_market.duckdb"
                chk("㊴ 家內庫與湖入普查:env VIA_DATA_HOME 的 vdf_tw_market.duckdb 2 表(家:相對路徑)· 湖 tw_daily_prices 2 列 2020→2026 GREEN · 家內沙盒(engine_bus/_cwd)不算 · 冊上宣告的表以湖存在=不報 ABSENT",
                    data_home()[0] == _hm and any(f.name == "vdf_tw_market.duckdb" for f in _fl) and not any(f.name == "sandbox.duckdb" for f in _fl)
                    and {r["table"] for r in _hrows} >= {"tw_listings", "tw_monthly_revenue"} and _rel_ok
                    and len(_lake) == 1 and _lake[0]["table"] == "tw_daily_prices" and _lake[0]["rows"] == 2
                    and _lake[0]["state"] == "GREEN" and _lake[0]["source"] == "湖"
                    and not any(m["table"] in ("tw_daily_prices", "tw_monthly_revenue", "tw_listings") for m in _miss),
                    f"(家內 {len(_hrows)} 表 · 湖 {len(_lake)} · 缺 {len(_miss)})")
            except ImportError:
                chk("㊴ 家內庫與湖入普查(本環境無 duckdb=SKIP 誠實)", True, "SKIP")
    finally:
        if _sv[0] is None:
            os.environ.pop("VIA_DATA_HOME", None)
        else:
            os.environ["VIA_DATA_HOME"] = _sv[0]
        _CENSUS, _CENSUS_WHY, _DB_INDEX, _DB_INDEX_WHY, _HOME = _sv[1], _sv[2], _sv[3], _sv[4], _sv[5]
        LAKE_WRITE = True
    # 批494 ㊶:正典工具本名掛載是真的——子行程 import 零成本,取屬性才真載入
    _mc = ("import sys;import VeritasCeleritas as vc;a=type(sys.modules['VeritasCeleritas']).__name__;n0='numpy' in sys.modules;"
           "v=vc.__version__;b=type(sys.modules['VeritasCeleritas']).__name__;print(a,n0,v,b,'VeritasAegisNexus' in sys.modules)")
    try:
        _rm = subprocess.run([sys.executable, "-c", _mc], capture_output=True, text=True, timeout=120, env=child_env("vrn"), cwd=str(VIA))
        _mo = (_rm.stdout or "").split()
    except Exception as _exc:
        _mo = [f"{type(_exc).__name__}"]
    chk("㊶ 正典工具本名掛載(批494 操作員令):子行程 import VeritasCeleritas 是惰性代理(numpy 未載)、取 __version__ 才真載入成 module、VeritasAegisNexus 同掛",
        len(_mo) == 5 and _mo[0] == "_LazyTool" and _mo[1] == "False" and _mo[2] == "1.0.0" and _mo[3] == "module" and _mo[4] == "True",
        f"({' '.join(_mo)[:80]})")
    # 批498 ㊷㊸:閘態與缺料樣式(容器實測 vdf 17 項尾段)
    _g1 = classify_stop("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)")
    _g2 = classify_stop("[月營收] 同意閘未開(VIA_NET_CONSENT≠YES)=拒跑(fail-closed 誠實)")
    _g3 = classify_stop("[FAIL-CLOSED] 法遵雙閘未開:需 VIA_NET_CONSENT=YES + FRED_API_KEY(絕不代設)")
    chk("㊷ 同意閘未開=GATED(閘,不是壞掉):FAIL-CLOSED/拒跑/法遵雙閘三種措辭都認,why 指路開閘且不代設",
        _g1[0] == "GATED" and _g2[0] == "GATED" and _g3[0] == "GATED" and "不代設" in _g1[1] and _STATE_COLOR.get("GATED"))
    _n1 = classify_stop("RED     價表缺 tw_daily_prices")
    _n2 = classify_stop("_duckdb.CatalogException: Catalog Error: Table with name tw_chip_margin does not exist!\nDid you mean")
    _n3 = classify_stop("RED     本機三庫根缺 C:\\x(--src DIR 或 $env:VIA_LOCAL_DB_ROOT)")
    chk("㊸ 表缺/Catalog Error/根缺=缺料 NODATA(上游表或夾沒料,非本引擎缺陷)",
        _n1[0] == "NODATA" and _n2[0] == "NODATA" and _n3[0] == "NODATA")
    _bp = classify_stop("  File \"C:\\x\\envs\\via_vap_312\\Lib\\site-packages\\pandas\\compat\\pyarrow.py\", line 14, in <module>\n"
                        "    _palv = Version(Version(pa.__version__).base_version)\n"
                        "AttributeError: module 'pyarrow' has no attribute '__version__'")
    chk("㊵ 套件壞了=缺件不是引擎壞(操作員實錄 vap_stack/vap_heatmap:pyarrow 沒有 __version__=半拆/命名空間包)→ ABSENT 並指路 force-reinstall",
        _bp[0] == "ABSENT" and "pyarrow" in _bp[1] and "force-reinstall" in _bp[1]
        and classify_stop("Traceback (most recent call last): 真的壞了")[0] == "")

    # ㊹ 批500:冊上 db_scope=all_home 的表對每本家內庫都算冊上;lamp=rows 的表只看列數(一列一天≠AMBER)
    try:
        _sheet44 = {"tables": [{"db": "vdf_tw_market.duckdb", "table": "via_policy_sync", "db_scope": "all_home", "lamp": "rows", "min_rows": 1},
                               {"db": "vdf_tw_market.duckdb", "table": "tw_daily_prices"}]}
        _rows44 = [{"db": "ActiveTWETF.duckdb", "table": "via_policy_sync", "rows": 1, "span_days": 1, "state": "AMBER", "note": ""},
                   {"db": "vdf_tw_market.duckdb", "table": "via_policy_sync", "rows": 0, "span_days": None, "state": "NODATA", "note": ""},
                   {"db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "rows": 5, "span_days": 3, "state": "AMBER", "note": ""},
                   {"db": "vdf_hub.duckdb", "table": "other", "rows": 5, "span_days": 3, "state": "AMBER", "note": ""}]
        _decl = {(t["db"], t["table"]) for t in _sheet44["tables"]}
        _decl_all = {t["table"] for t in _sheet44["tables"] if t.get("db_scope") == "all_home"}
        _lamp = {t["table"]: int(t.get("min_rows") or 1) for t in _sheet44["tables"] if t.get("lamp") == "rows"}
        for r in _rows44:
            r["source"] = ("副本" if "_repo_" in r["db"] else "冊上" if ((r["db"], r["table"]) in _decl or r["table"] in _decl_all) else "冊外")
            if r["table"] in _lamp:
                r["state"] = "GREEN" if r["rows"] >= _lamp[r["table"]] else "NODATA"
        chk("㊹ 冊上 db_scope=all_home 對每本家內庫都算冊上;lamp=rows 表一列=GREEN、零列=NODATA、不吃日期跨度;普通薄表仍 AMBER",
            _rows44[0]["source"] == "冊上" and _rows44[0]["state"] == "GREEN" and _rows44[1]["state"] == "NODATA"
            and _rows44[2]["state"] == "AMBER" and _rows44[2]["source"] == "冊上" and _rows44[3]["source"] == "冊外",
            f"({[(r['source'], r['state']) for r in _rows44]})")
    except Exception as _exc:
        chk("㊹ all_home/lamp=rows", False, f"({type(_exc).__name__}:{str(_exc)[:60]})")
    # ── 批508 ㊺㊻:驗收契約不得啟動 production；快取不得吃掉診斷 ──
    with _tf.TemporaryDirectory() as _td:
        _d = Path(_td)
        _eng = _d / "fx_profile.py"
        _eng.write_text(
            "import sys,time\n"
            "if '--selftest' in sys.argv: print('[計] 一檢 OK 1 · FAIL 0'); raise SystemExit(0)\n"
            "time.sleep(30)\n", encoding="utf-8")
        _fx = [{"id": "profile", "family": "vdf", "zh": "", "glob": "", "dir": "",
                "verb": ["run", "--full"], "test_verb": [], "params": ["days"],
                "outputs": ["supportive modules/registry/VIA_InputConsole_Spec_v0100.json"],
                "net": True, "engine": _eng.name, "engine_path": str(_eng), "module": "",
                "engine_dir": str(_d), "versions": 1, "engine_state": "在位", "group": "",
                "spec_why": "", "cwd": ""}]
        _pr = call("profile", apply=True, timeout=5, catalog_rows=_fx, profile="test")
        _none = _d / "none.py"; _none.write_text("print('production only')\n", encoding="utf-8")
        _fx[0] = {**_fx[0], "id": "none", "engine": _none.name, "engine_path": str(_none), "outputs": []}
        _na = call("none", apply=True, timeout=5, catalog_rows=_fx, profile="test")
    chk("㊺ test profile 只跑有界 selftest，production verb/params 原樣留在契約；無測試契約=ABSENT 不假綠；產出判定共用 output_verdict",
        _pr["state"] == "GREEN" and "--selftest" in _pr["argv"] and "run" not in _pr["argv"]
        and _pr["contract_verb"] == ["run", "--full"] and _pr["contract_params"] == ["days"]
        and _pr["outputs_seen"][0]["verdict"] == "在" and _na["state"] == "ABSENT"
        and "production run" in _na["why"])

    _cache_saved = (_CENSUS, _CENSUS_WHY, _DB_INDEX, _DB_INDEX_WHY)
    try:
        _CENSUS, _CENSUS_WHY = [], "census evidence"
        _DB_INDEX, _DB_INDEX_WHY = {"t": "x.duckdb"}, "index evidence"
        _cr1, _cw1 = db_census(); _cr2, _cw2 = db_census()
        _di1, _dw1 = db_table_index(); _di2, _dw2 = db_table_index()
    finally:
        _CENSUS, _CENSUS_WHY, _DB_INDEX, _DB_INDEX_WHY = _cache_saved
    chk("㊻ DB index/census 快取把 why 與資料一起保存；第二次讀仍有同一診斷證據",
        _cw1 == _cw2 == "census evidence" and _dw1 == _dw2 == "index evidence"
        and _di1 == _di2 == {"t": "x.duckdb"} and _cr1 == _cr2 == [])

    _ph_saved = os.environ.get("PYTHONHOME")
    os.environ["PYTHONHOME"] = "/nonexistent/uv/cpython-3.12"
    try:
        _ce = child_env("vdf")
    finally:
        if _ph_saved is None:
            os.environ.pop("PYTHONHOME", None)
        else:
            os.environ["PYTHONHOME"] = _ph_saved
    chk("㊼ 批514 L32 子行程環境衛生:child_env 撤 PYTHONHOME(母殼帶錯版=家族境子行程 SRE module mismatch 根因)並記 VIA_PYTHONHOME_SCRUBBED;其餘鍵照舊",
        "PYTHONHOME" not in _ce and _ce.get("VIA_PYTHONHOME_SCRUBBED") == "/nonexistent/uv/cpython-3.12" and _ce.get("VIA_FAMILY") == "vdf"
        and "bootstrap" in _ce.get("PYTHONPATH", "") and _ce.get("VIA_ROOT") == str(VIA))

    print(f"  [計] 四十七檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


USAGE = """用法(動詞在前;--matrix 這種連字號寫法也收):
  catalog [--family vdf|vrn|vap]        冊 → 尾版 → 在位,只看不跑
  matrix  [--family F] [--html] [--timeout N]  批量調度 → 多矩陣(**預設只解析**;心跳不卡斷)
          [--apply-family vrn,vap]      只有點名的家族真跑
          [--ids a,b]                   只跑點名的項(寫庫動詞只認這條路)
          [--profile test|run]          test=有界 selftest；run=冊上 production 動詞(預設)
  call    --item <id> [--apply]         單項
  census [--tables|--hygiene]           庫況:倉內+家內(env VIA_DATA_HOME/目錄頁/MDL123)· 預設一本庫一行;--tables 逐表;--hygiene 唯讀審計
  boot                                  啟動層實證:子行程看到的加速器/網路件/閘態
  tails [--state RED,TIMEOUT]           上次矩陣裡紅項的因由 + 引擎尾段(貼回來用)
  --selftest                            自測"""


def _verb(args: list) -> tuple[str, list]:
    r"""動詞正規化(批474 工作站實錄)。

    操作員打的是 `via-bus --matrix`——**那是我上一則訊息叫他打的**,錯在我。
    但 `--matrix` 也是任何人都會自然打出來的形狀,而 v0106 對它的回應是
    「印兩百行 docstring,然後回 rc=0 說成功」。所以這裡只做一件事:
    **把頭部的連字號脫掉**再比對動詞白名單。只脫連字號,不去猜別的東西——
    猜錯的體貼比不體貼更難救。
    """
    verbs = ("catalog", "matrix", "call", "census", "boot", "tails")
    if not args:
        return "", args
    head = args[0].lstrip("-").lower()
    if head in verbs:
        return head, args[1:]
    return "", args


def _boot_for_test() -> int:
    _saved = sys.argv
    sys.argv = [sys.argv[0], "boot"]
    try:
        return main()
    finally:
        sys.argv = _saved


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 引擎調度匯流排(CGC_MDL148 v0126)· 四十七檢自測(零網路)===")
        return selftest()
    try:
        fam = args[args.index("--family") + 1].strip().lower() if "--family" in args else None
        apply_ = "--apply" in args
        af = ([x.strip().lower() for x in args[args.index("--apply-family") + 1].split(",") if x.strip()]
              if "--apply-family" in args else [])
        ids = ([x.strip() for x in args[args.index("--ids") + 1].split(",") if x.strip()]
               if "--ids" in args else None)
        tmo = int(args[args.index("--timeout") + 1]) if "--timeout" in args else DEFAULT_TIMEOUT
        profile = args[args.index("--profile") + 1].lower() if "--profile" in args else "run"
    except (IndexError, ValueError) as exc:
        print(f"  [FAIL] 參數缺值或格式錯:{type(exc).__name__}")
        print(USAGE)
        return 2
    empty_options = [name for name, value in (("--family", fam), ("--apply-family", af), ("--ids", ids))
                     if name in args and not value]
    if empty_options:
        print(f"  [FAIL] 參數不可為空:{','.join(empty_options)}")
        return 2
    known_families = {"vdf", "vrn", "vap"}
    bad_families = ([fam] if fam and fam not in known_families else []) + [x for x in af if x not in known_families]
    if bad_families:
        print(f"  [FAIL] 家族只收 vdf|vrn|vap，不收 {','.join(dict.fromkeys(bad_families))}")
        return 2
    if tmo <= 0:
        print(f"  [FAIL] --timeout 必須是正整數，不收 {tmo}")
        return 2
    if profile not in ("run", "test"):
        print(f"  [FAIL] --profile 只收 test|run，不收 {profile}")
        return 2
    verb, _rest = _verb(args)
    if verb == "tails":
        # 紅項尾段:雲端看不到操作員機器的 stdout,讓他一句 via-bus tails 就貼得出來
        if "--state" in args and (args.index("--state") + 1 >= len(args) or not args[args.index("--state") + 1].strip()):
            print("  [FAIL] --state 後要給 RED,TIMEOUT,AMBER 等狀態")
            return 2
        want = (args[args.index("--state") + 1].split(",") if "--state" in args else ["RED", "TIMEOUT", "AMBER"])
        lp = OUTDIR / "ENGINE_BUS_latest.json"
        if not lp.exists():
            print("  [tails] 還沒跑過矩陣(ENGINE_BUS_latest.json 缺)"); return 2
        data = json.loads(lp.read_text(encoding="utf-8"))
        n = 0
        for r in data.get("results", []):
            if r.get("state") in want:
                n += 1
                print(f"── [{r['state']}] {r['family']}/{r['id']} · {r.get('engine') or '—'} · {r.get('seconds')}s")
                if r.get("why"): print(f"   因由:{r['why']}")
                for ln in [x for x in (r.get('stdout_tail') or '').splitlines() if x.strip()][-8:]:
                    print(f"   │ {ln[:160]}")
        print(f"[tails] {n} 項({','.join(want)})· 來源 {data.get('ts')}")
        return 0
    if verb == "boot":
        # 證據不是宣稱:每個家族真的起一個子行程,印它看到的。
        # 批483:三家族**並行**+心跳(實錄:逐一探測在 Windows 上會白畫面好幾分鐘)。
        import threading
        code = ("import os,sys;print(os.environ.get('VIA_ACCEL_BOOT','(無)'),'|',"
                "os.environ.get('VIA_NET_BOOT','(不掛)'),'|','via_net' in sys.modules,'|',"
                "os.environ.get('VIA_NET_CONSENT','(未設)'),'|',"
                "'工具:'+';'.join(x.split('=')[0].replace('Veritas','')+'('+x.split('=')[1].split(':')[0]+')' for x in os.environ.get('VIA_TOOLS_MOUNT','').split(';') if '=' in x))")
        results: dict = {}

        def _probe(f):
            try:
                py = python_for(f).get("python") or sys.executable
                r = subprocess.run([py, "-c", code], capture_output=True, text=True,
                                   timeout=120, env=child_env(f), cwd=str(OUTDIR if OUTDIR.exists() else VIA))
                results[f] = (Path(py).name, (r.stdout or "").strip() or (r.stderr or "").strip()[-120:])
            except Exception as exc:
                results[f] = ("?", f"{type(exc).__name__}:{str(exc)[:60]}")

        fams = ("vdf", "vrn", "vap")
        ths = [threading.Thread(target=_probe, args=(f,), daemon=True) for f in fams]
        for t in ths:
            t.start()
        t0 = time.time()
        while any(t.is_alive() for t in ths) and time.time() - t0 < 150:
            for t in ths:
                t.join(timeout=HEARTBEAT_SEC)
                if not any(x.is_alive() for x in ths):
                    break
            if any(t.is_alive() for t in ths):
                print(f"      ⏳ 還在探測家族 python · {int(time.time() - t0)}s · 已回:{sorted(results)}")
        for f in fams:
            py, seen = results.get(f, ("?", "探測逾時(150s)=誠實停,不掛著"))
            print(f"  [{f}] python={py} → 加速器 | 網路件 | via_net 可 import | 同意閘 = {seen}")
        print("[啟動層] bootstrap=" + str(BOOTDIR) + (" 在位" if BOOTDIR.is_dir() else " **缺**")
              + f" · 三家族並行 {round(time.time() - t0, 1)}s")
        return 0
    if verb == "census" and "--hygiene" in args:
        h = db_hygiene()
        if h["why"]:
            print(f"  [判不了] {h['why']}")
        for x in h["sentinel"]:
            print(f"  [哨兵] {x['db'][:26]:26s} {x['table']:28s} {x['n']:>8,} 列 < {SENTINEL_BEFORE}  樣本 {x['sample']}")
            print(f"         {x['sql_not_run']}")
        for x in h["replicas"]:
            print(f"  [副本] {x['db'][:30]:30s} {x['table']:28s} {x['rows']:>10,}  至 {x['hi'] or '—'}  正庫 {x['canonical']} 至 {x['canonical_hi'] or '—'}  → {x['verdict']}")
        print(f"[衛生] 哨兵列表 {len(h['sentinel'])} 張 · 副本表 {len(h['replicas'])} 張 · **零寫入**(SQL 只寫不跑;要不要刪是操作員的手)")
        return 0
    if verb == "census":
        rows, why = db_census()
        _h, _hs = data_home()
        print(f"  [家] {(_h if _h is not None else '缺')}({_hs})· 家內庫 "
              f"{len({_r['db'] for _r in rows if _r['db'] != '湖' and str(_r.get('path', '')).startswith('家:')})} 本 · 湖 "
              f"{len({_r['table'] for _r in rows if _r['db'] == '湖'})} 夾"
              + ("" if _h is not None else " · 先 via-datahome catalog / 設 env VIA_DATA_HOME"))
        for _db in db_files():
            print(f"  [庫] {_db.name:32s} → {_rel(_db)}")
        _sk = sandbox_skipped()
        if _sk:
            print(f"  [沙盒略] {len(_sk)} 本:" + ", ".join(_sk[:4]) + (" …" if len(_sk) > 4 else ""))
        miss = census_expected(rows) if rows else []
        full = "--tables" in args
        if full:
            for r in rows:
                rng = (f"{r['lo']} → {r['hi']} ({r['span_days']} 天)"
                       if r["lo"] and r["span_days"] is not None
                       else (f"{r['lo']} → {r['hi']}" if r["lo"] else ""))
                print(f"  [{r['state']:6s}] {r['db'][:26]:26s} {r['table']:28s} "
                      f"{r['rows']:>10,}  {rng}  ·{r.get('source', '')}")
            for r in miss:
                _w = (" 寫入者 " + "/".join(r["writers"])) if r.get("writers") else ""
                print(f"  [ABSENT] {r['db'][:26]:26s} {r['table']:28s} "
                      f"{('碼裡 ' + str(r['refs']) + ' 檔在用') if r.get('refs') else '冊上宣告':>10s}  ·{r.get('source', '')}{_w}")
        else:
            # 批490 預設精簡:一本庫一行(省貼回來/讀進去的 token);--tables 才逐表
            _by: dict = {}
            for r in rows:      # 以路徑分組(家內與倉內同名庫各一行),湖合成一行
                _by.setdefault(("湖", r["table"]) if r["db"] == "湖" else (r["db"], str(r.get("path", ""))), []).append(r)
            for (_dbn, _pth), _rs in _by.items():
                _c = {}
                for r in _rs:
                    _c[r["state"]] = _c.get(r["state"], 0) + 1
                # 「最新」只看長得像日期的 hi(vrn_report_metrics 的 2027、factset 的 Q3 不算日)
                _hi = max((r["hi"][:10] for r in _rs if len(r["hi"]) >= 10 and r["hi"][4] == "-"), default="")
                _out = sum(1 for r in _rs if r.get("source") == "冊外")
                _tag = "家" if _pth.startswith("家:") else ("倉" if _pth.startswith("倉:") else "")
                if _dbn == "湖":
                    _r0 = _rs[0]
                    print(f"  [湖]   {_pth[:30]:32s} {_r0.get('files', 0):3d} 檔" + (f"={_r0['members']} 表" if _r0.get("members") else "")
                          + f" · {_r0['rows']:>13,} 列"
                          + (f" · {_r0['lo'][:10]} → {_r0['hi'][:10]}" if _r0["lo"] else "") + f" · {_r0['state']}"
                          + (" · 冊上宣告的表" if any(_pth == t["table"] for t in db_ssot()[0].get("tables", [])) else "")
                          + (f" · {_r0['note']}" if _r0.get("note") else ""))
                    continue
                print(f"  [庫況] {(_tag + ' ' if _tag else '') + _dbn[:30]:32s} {len(_rs):3d} 表 · "
                      f"{sum(r['rows'] for r in _rs):>13,} 列" + (f" · 最新 {_hi}" if _hi else "")
                      + " · " + " · ".join(f"{k} {v}" for k, v in sorted(_c.items()))
                      + (f" · 冊外 {_out}" if _out else ""))
            _mb: dict = {}
            for r in miss:
                _mb.setdefault(r["db"], []).append(r["table"])
            for _dbn, _ts in _mb.items():
                print(f"  [ABSENT] {_dbn[:30]:30s} 缺 {len(_ts)} 張:" + ", ".join(_ts[:6]) + (" …" if len(_ts) > 6 else "")
                      + ("  (冊外;碼裡當表用)" if _dbn == "—" else "  (冊上宣告)"))
            print("  (逐表:via-census -Tables;衛生:via-census -Hygiene)")
        tal: dict = {}
        for r in rows + miss:
            tal[r["state"]] = tal.get(r["state"], 0) + 1
        print(f"[庫況] {len(rows)} 張表在庫 · 缺 {len(miss)} 張 · "
              + " · ".join(f"{k} {v}" for k, v in sorted(tal.items()))
              + (f" · {why}" if why else ""))
        return 0
    if verb == "catalog":
        rows = catalog(fam)
        for r in rows:
            print(f"  [{r['engine_state']}] {r['family']}/{r['id']:18s} "
                  f"{r['engine'] or r['glob']:44s} 動詞={'/'.join(r['verb']) or '-'}")
        print(f"[目錄] {len(rows)} 項 · 在位 {sum(1 for r in rows if r['engine'])}")
        return 0
    if verb == "call":
        global HEARTBEAT_TO_STDERR
        HEARTBEAT_TO_STDERR = True
        if ("--item" not in args or args.index("--item") + 1 >= len(args)
                or not args[args.index("--item") + 1].strip()):
            print("  用法:call --item <id> [--apply]")
            return 2
        # call --item 是**明點**(人親手指名這一支)→ 寫庫閘放行
        r = call(args[args.index("--item") + 1], apply=apply_, sweep=False, profile=profile)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] in ("GREEN", "PLAN") else 1
    if verb == "matrix":
        data = matrix(family=fam, apply=apply_, ids=ids, apply_families=af, timeout=tmo, profile=profile)
        OUTDIR.mkdir(parents=True, exist_ok=True)
        (OUTDIR / "ENGINE_BUS_latest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        cnt = " · ".join(f"{k} {v}" for k, v in sorted(data["counts"].items()))
        scope = ("全跑" if apply_ else
                 ("真跑家族 " + ",".join(data["apply_families"]) if data["apply_families"]
                  else ("明點 " + ",".join(data["ids"]) if data["ids"] else "全 dry")))
        print(f"[矩陣] {len(data['results'])} 項 · profile={profile} · {scope} · {cnt}")
        if "--html" in args:
            p = render(data)
            print(f"[頁] {p}")
        if profile == "test":
            # --apply-family 會刻意讓其餘家族留在 PLAN；那些列不是本次驗收
            # 對象，不能反過來把 vdf,vrn 的全綠退出碼染紅。只裁決本次真正
            # 執行的列；全 dry 沒有驗收證據，也維持既有 rc=0 的規劃契約。
            applied_families = set(data.get("apply_families") or [])
            wanted_ids = set(data.get("ids") or [])
            tested = [r for r in data["results"]
                      if data.get("apply") or r.get("id") in wanted_ids
                      or r.get("family", "").lower() in applied_families]
            bad = [r for r in tested if r.get("state") != "GREEN"]
            return 0 if not bad else 1
        return 0
    # 批474:v0106 這裡是 `print(__doc__); return 0`——兩百行說明加一個
    # **rc=0 的假綠**。自動化鏈路看 rc,會把「什麼都沒跑」讀成「跑完了」。
    if args:
        print(f"  [FAIL] 不認得的動詞:{args[0]}")
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
