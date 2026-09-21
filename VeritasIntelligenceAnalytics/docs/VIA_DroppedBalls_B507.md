# VIA 掉球清單(漏球審計)· 批507(2026-09-14)· 涵蓋 批474–506

> 律:操作員說過、沒做也沒寫進這裡=掉球。只增不減;結案用 ~~刪除線~~ 加「已結(批NNN)」。狀態:未做 / 候(等操作員裁) / 操作員的手(閘·裝件·決策) / 容器紅(容器沒料,他機器綠或未驗)。

| 代號 | 事 | 狀態 | 誰 | 下一步 |
|------|----|------|----|--------|
| A | 姊妹倉 tonykuni/VIA-VDF-VRN 同步 | 候 | 工具層權限 | 操作員在工具層授權後再做 |
| D | 批416 F2 逐家投信 PCF 端點查實 | 操作員的手 | 需網路+閘 | 開閘後跑 ENG078 sync |
| G | VRN_MDL 數量 300 vs 294 | 未做 | AI | 同一把尺再量 |
| I/P | VDF SSOT 化;`_repo_` 副本庫哪本正本 | 候 | 操作員 | 冊講明後 census 對冊 |
| R | ENG072 起手 GLE 探 7 後端 140 秒未快取 | 未做 | AI | 探測結果落 24h 快取 |
| S | 資料家第二步:31 處散落件 link 進鏡根 | 候 | 操作員 | `via-datahome plan` 核准後 link |
| T | via-vrnuni 官方名冊 CSV 橋 | 未做 | AI | tw_listings → code/name/yf_ticker/industry |
| U | VDF 正境 via_vdf(登錄 py3.12)vs via_vdf_312(3.13.7 未登錄) | 候 | 操作員 | 一句話定案後改工具冊 |
| V | via_vap_312 pyarrow 半拆/pandas/seaborn;via_paddle_311 paddlepaddle(paddle_ppstructure 相依錯)、easyocr 模型檔;Tesseract 已有 chi_tra | 操作員的手 | 閘+Approve | `via-rungate` → `via-vcgc check` → `via-envtools -Apply -Approve` |
| X | ENG072 ⑤ 空夾誠實 rc2 | 容器紅 | — | v0116 基線同紅;他機器未見紅 |
| Y | 「Table … does not exist」現為 NODATA | 已改(批498) | — | 冊上有而缺料=查 census -Tables |
| Z1 | VRN PARTIAL 16 件(互核一致但標示未全還原;操作員律第二句) | 未做 | AI | 逐件看 labels_ok=False 的 repair 紀錄;決定要不要追=操作員 |
| Z2 | 未登冊引擎家族 40(VCGC audit) | 候 | 操作員核准 | `via-vcgc register-plan` 清單;核准後逐支登站 |
| Z3 | 倉衛生未刪八類(ICON_FORGE 餘量 1.1GB、SCOPE_COPY、安裝器三版、ui_support 大頁、.dup.csv、跑批產出、收件夾、sha701 巨檔副本) | 候 | 操作員 | 逐類定案;刪必附證據 |
| Z4 | MOPS 三大報表解析(收容件自述 brittle;ENG082 只探路) | 未做 | AI | 有真回應樣本後再寫解析;`tw_financial` 現靠 yfinance 車道 |
| Z5 | fin_statements 真抓未驗(via_vdf_312 有無 yfinance?閘?) | 操作員的手 | 閘 | `via-finstat -Dry` → 開閘 `via-finstat run --only 2330,2317` 貼回 |
| Z6 | vdf/vetf 真跑未驗(容器無料;矩陣預設只跑 vrn,vap) | 操作員的手 | 閘 | `via-ryg vdf,vrn -Timeout 600` + `via-vetf`,`via-bus tails` 貼回 |
| Z7 | ENG074 ⑬ 三方對照夾具(NO_TICKER/NO_DATE) | 容器紅 | — | v0106 基線同紅;他機器批466 曾 18/18;若他機器也紅=AI 修 |
| Z8 | 格子 3 站 present=False(ChipWar 編譯檢、TWREV 編譯檢=PYCODE 特殊站;selftest grid 自指) | 非掉球 | — | VCGC v0101 標「特殊」不當缺 |
| Z9 | ENG074 公式檢(AllInOne validate_formulas)未接進 crosscheck | 未做 | AI | 加 dimension=formula 列(PASS/FAIL) |
| Z10 | 五本真庫政策表曾被自測污染兩次(批504/505) | 已修(批506 ENG082 v0107) | 操作員復原 | `via-vrnlogic sync-db` 一次;`via-vrnlogic` 應 同步 6 |
| Z11 | 主控台冊 GOV 類治理任務只在 Deck,不在規格冊 families | 未做 | AI | 規格冊加 gov 家族或 VCGC 頁直接列(現已列 Deck 64 任務) |
| Z12 | MasterControl 總控頁未隨 Manager v0124–v0126 再生(容器再生會覆蓋真頁;L22) | 操作員的手 | — | 他機器 `via-manager` 再生一次 |
| Z13 | 批508 環境復原(L24)真跑:你機器 `via-envrecover` → `-Execute -Approve`(① 還原)→ `via-rungate` → 再 `-Execute -Approve`(② 順序裝);容器只有唯讀計畫 | 操作員的手 | 操作員 | 貼回 `via-envrecover` 與 `via-vcgc` 二段 |
| ~~Z14~~ | ~~操作員機器上的並行線不在遠端任何分支;要先推到側枝才能併~~ | **已結(批511)**:側枝 `local/parallel-b508-09151416` 已推、已併入本線(撞名者高版號另起;律/lessons 聯集;.via_envmanager 不入倉;孿生去重 45 件) | — | — |
| ~~Z15~~ | ~~via_vdf_312 解譯器壞(SRE module mismatch)~~ 已結(批515):根因=母殼 PYTHONHOME(批514 L32 三處撤除),實錄 `via-rungate --family vdf` GREEN 8/8 · [INTERP] OK 3.13.7 · 必要庫 4/4;殼層根治另立 Z25 | 已結(批515) | — | vrn 族同樣跑一次(`via-rungate --family vrn`;INSTALL_OK 要兩族 24h 內綠) |
| Z16 | PARTIAL 16 件(Z1)自批510 起例行跑不再重燒 OCR(部分命中);要重抽=你機器 `via-firstpage -RetryFailed`(涵蓋 PARTIAL);矩陣 vrn_firstpage 應不再 600s TIMEOUT,貼回驗 | 操作員的手 | 操作員 | 貼回 `via-ryg vrn -Timeout 600` 的 vrn_firstpage 秒數 |
| Z17 | 並行線 PANORAMA_HANDOVER-v0103「已列入下一輪」:Windows VRN 三站真實失敗斷言與 OCR runtime 自動收集、VETF 快照日期覆蓋 vs 持股完整性、gap plan 只代表查庫完成;`new modules engines/*` 另線收容件(檔名帶 (2)/(3))候裁入 references/intake | 未做 | AI | 下一批照該檔「已列入下一輪」逐項 |
| Z18 | 批510 我把 vrn_firstpage 600s TIMEOUT 歸因給「16 件 PARTIAL 每跑重燒 OCR」——你的實錄證明那 16 件是數位 PDF(DUAL_ZONES,合計 30.89s);600s 是並行線 panorama 自己的 vrn_firstpage 跑法,不是本線;PARTIAL_HIT 仍有效但歸因改正 | 已在 一-n 更正 | AI | 無 |
| Z19 | 並行線 `via-panorama` 的 policy_append/registry_sync 會自動寫律冊與元件冊;併線後冊已聯集(L26–L29 orig_id),它再跑可能重複追加 → 先不要跑;要對表(它的 id 判斷 vs 聯集後 id) | 未做 | AI | 批513 對表後放行 |
| Z20 | 「類似參數功能引擎就整合優化」(L30)候選:RunGate 站環境→已改用匯流排 child_env(批512);VCGC panorama 動詞 vs MDL135 recover(還原/補抓);`new modules engines/*` 副本引擎 vs functional modules 正本;VIA_UI_* 多頁再生器 | 部分做 | AI | 逐對比對,只留一處 |
| Z21 | L31 彈性嫁接/自適應合約 路線圖:①綁定合約層 sync/connect/graft(批513 做了;靜態 AST)②執行期 connect/sync 接 via_iface_autosync 五階段管道(mapping→connecting→syncing→testing→debugging)③新引擎 I/O 封包(VIA_Engine_Contract io_envelope+Pydantic)採用率量測 ④匯流排讀 contract 欄自動補未暴露旗標 | 部分做 | AI | 批514 起逐項 |
| Z22 | `supportive modules/_inbox_to_classify/_inbox_to_classify/` 六個與標準庫同名的檔(遮蔽地雷;現不在任何 sys.path 上);批514 證據(md5/大小):abc.py d016c5a4/1519B · inspect.py a210c663/3806B · json.py 954c5c0d/5660B · logging.py 49dd2df7/12737B · token.py 498b7001/6855B · traceback.py 2bac3313/36490B → 候裁:改名或入 intake | 候 | 操作員 | 裁「改名」或「入 intake」我就動 |
| Z23 | 你的樹卡在批508(Grid v0302、RunGate v0101、Register v0200):`git pull --ff-only` 那行沒生效,多半是本機發佈頁被改動擋住;批513 區塊改 stash+pull 並要求貼 pull 輸出 | 已解(批513 stash+pull 後 HEAD 4728252d=批513) | — | 每批區塊仍帶 stash+pull |
| Z24 | 中央治理家族深併候裁(L30):主控台 URN 發碼 vs VCGC registry-sync 元件編號冊(兩本冊、兩套代號);同名整併 ps1 vs L23 倉衛生流程;檔案優先序 vs MDL054 scan/匯流排 catalog;下行控制能力冊 vs Deck 任務冊/匯流排;詞彙引擎 v0100 vs CGC_MDL001 v0401 語料線 + VIA_SSOT_RegexDict。批514 先入台(擁有者 CGC_MDL150、十一段、dry-run),各對只留一處=下一批逐對比對 | 未做 | AI | 逐對出比對表(欄位/代號/輸出)再裁 |
| Z25 | 殼層 PYTHONHOME 根治:你的視窗仍帶 PYTHONHOME=…uv\python\cpython-3.12(站已免疫,但手動跑/其他工具仍會中);一-q 四問(User/Machine 環境變數、$PROFILE、via_core Activate)貼回後決定拿掉哪一處 | 操作員的手 | 操作員 | 貼回四問;拿掉後 Register 載入不再印黃 |
| Z26 | VRN 實測 TAB3:工作站 `via-console tab3` 報告 0=主控台開錯庫(寫死主路徑;ENG073 寫在資料家那本;LL27)→ MDL139 v0106 主庫資料家優先 + `[庫解析]` 行;容器實跑 71 份 OK | 未做(等實錄) | 操作員+AI | 貼回 `via-console tab3 --n 3`(含 [庫解析] 行) |
| Z27 | VDF 五額外試跑:實錄 GREEN 2(月營收/主動ETF持股)· GATED 3(macro_fred/fin_statements/global_universe 是**雙閘** NET+SCRAPE;FRED 另要 FRED_API_KEY)→ 區塊改雙閘 + `-Ids` 只跑三件 | 操作員的手 | 操作員 | `$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'; via-vdf-extra5 -Ids macro_fred,fin_statements,global_universe` |
| Z28 | via-cgconsole 工作站 RED 理由:貼回(批517 區塊)=**[FAIL] G17 3 循環** + [WARN] G03 1049 組/G04 10 檔/G16 1457/G18 2858/G22 未探針 → 批518 對回檔名:退役件兩圈 + 收容件一圈(零觸碰)+ 活樹一圈=舊啟動器 Invoke-VRN-Activate-And-Validate.ps1 呼叫批180 已退役 VRN_ENG008 → git mv 退役 wave8 後活樹 0(L38);G03 依 L23 刪 6 留 122;G04/G16/G18/G22 設計上不擋 | 已判(批518;`via-cgfamily cycles` 在你機器複驗) | AI | 貼回 `via-cgfamily cycles` 圈列 |
| Z29 | via-cgrouter 891 秒(OneDrive 樹 43,319 檔):路由器逐檔讀 magic bytes;OneDrive 佔位檔會觸發下載——下一批加排除規則(VIA_Reports/_governance/.git/envs)與 --budget-mb 預設調低,或改讀 file_index 快取 | 未做 | AI | 量 file_index.json 的擋下分類再定 |
| Z30 | 「以 VIA 為中央管理 全部 SSOT 化 唯一接觸口」(L20 延伸):冊外仍有寫死路徑/自帶輸出夾的件(中央治理家族五件、VETF 封印包 adapter、ENG075 OUTDIR);逐件改成讀冊(Spec/DataHome/契約)=下一批盤點表 | 未做 | AI | 出「寫死路徑清單」再逐件改冊 |
| Z31 | VRN_MDL001_Converter v0121 自測太重:容器 82.7s、工作站 >180s TIMEOUT(渲染 A4 200/600 DPI 點陣頁 ×9 檢)→ Grid v0310 站逾時 600 先讓閘判真;候優化:自測改小頁(A6)或只算一次 pixmap | 未做 | AI | v0122 自測瘦身,量到 <30s |
| Z32 | ~~摘要批跑器自測出網(Summarizer 取價器沒看閘)~~ 已結(批516):Summarizer v0102 閘 + digest v0115 VIA_SELFTEST=1;容器帶 VIA_NET_CONSENT=YES 跑自測零 404 | 已結(批516) | — | 工作站 `via-rungate --family vrn` 尾行不再有 HTTP 404 即證 |
| Z33 | ENG069 月營收×共識:工作站 via-vtmra v0108 **OK**(⑦ 合成庫去重過;27.5s);家族閘 YELLOW 只剩 TA-Lib 未裝 | 已結(批521) | — | — |
| Z34 | TA-Lib 裝:numpy<2 釘版在 Python 3.13 境從原始碼編譯失敗(LL39)→ 正確裝法 `& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -m pip install "TA-Lib>=0.6"`(wheel 自帶 C 庫;容器 0.8.0+numpy 2.4.6 self-test PASS);`via-taone probe` 依境印令 → 裝後 selftest-engine → run → vap | 操作員的手 | 操作員 | 裝後貼回 via-taone selftest-engine/run/vap |
| Z35 | VDF 短缺口「逐日全市場」道(L37 ⑤):ENG054/064 只有逐檔道(一檔一請求;5 日≈16 分);TWSE MI_INDEX ALLBUT0999 / TPEX 日成交行情一日一請求可補 ≤10 日缺口 → ENG054 v0105 --lane bulk-day(anti-join 同律;同意閘不變) | 未做 | AI | 先量端點欄位(需你開閘試一次)再建 |
| Z36 | VIA_Discussion_Reconstruction_Package_v1.6.1(61MB JSON 知識傾印;上傳 zip 內)不入倉:資料落資料家 `VIA System\via_database\nlp\`?由你裁;整理結果 md 已收 _b283 | 候 | 操作員 | 裁落點後我建 link 冊 |
| Z37 | 工作站 via-vcgc 註冊稽核「中央冊 4836/4837 缺 1」=你樹上一件未編號元件(容器 4836 全齊)→ `via-vcgc registry-sync --apply` 在你機器跑一次(會改 SSOT 冊=先 git stash 再 pull 的流程要留意) | 操作員的手 | 操作員 | 跑後貼回 registry-sync 一行 |
| Z38 | 五矩陣 3 紅具名(VCGC 頁貼回):vrn_firstpage TIMEOUT 600s → 冊項 timeout 1500 + Bus v0127;vrn_structdb ㉞/vrn_finpages ⑯ Windows 路徑字串比對 → ENG073 v0126/ENG074 v0109 as_posix(LL41)| 已修(批521;工作站 via-ryg vrn 複驗) | AI | via-ryg vrn 貼回 |
| Z39 | 主控台 G03 餘量:快照側副本 122 件(SCOPE_COPY 惰性存檔/_output 快照夾)byte 同活件卻被 VAP_Param_Registry src/AllDocuments 清單/asset_scan/Invoke-VAP-* 以檔名引用 → L23 不刪;要清就先改冊引用(你裁);主控台把 .json/.md/.html 與 VIA_Reports 也算組=工作站 1049 vs 容器程式檔 325 | 候(由你裁) | 操作員 | 裁「留」即結案;裁「清」我先改冊再刪 |
| Z40 | VRN_BatchFourEngine_v0100.py 第三次上傳(md5 同 b245/b383):它驅動的 VRNFourEngineSuite(four_engine_orchestrator.run_all_engines)**不在倉**→ 驅動器只收不掛;要用就上傳套件(或指出它在哪);docx→md 橋/批次/對帳已有正主(ENG075/匯流排/ENG074) | 候(由你) | 操作員 | 上傳套件或裁「不用」 |
| Z41 | VETF_FINAL_SEAL(b242 同件)的 React/Vinext 網站原始碼與 Standalone HTML:React 要 npm(觸網、CDN 外鏈)=不掛線;Standalone_Current 可當收容靜態頁(U/I 契約列為收容件;不在 ui_support 不連)· VATETF 現役=冊上項 vdf_vetf_consensus + `via-vetf`(v0206 資料家優先) | 候 | 操作員 | 裁 Standalone 是否複製入 ui_support(零 CDN 檢過才收) |
| Z42 | 工作流重組台 LIVE:頁面現只探 /api/console/status 判樞紐;「按下即跑」要 DeckServer 新端點(workflow_run 任務+權杖)——零彈窗/閘律下先不做,執行走 `via-workflow run <id>`;下批若要=Deck +workflow_run(net 依節點) | 候 | AI | 操作員點頭再做 |
| Z43 | VATETF EPS/forward P/E 覆蓋:批521 v0103 只給 FactSet 稀釋 EPS,但工作站 via-vetf 假綠(adapter APPEND_ONLY_CONFLICT 一字未寫)→ v0104 每跑一夾 RUN_<ts>(L44);FactSet 目標價只 4/40 檔 → forward P/E 覆蓋上限 10% 誠實 | 候 | 操作員 | via-vetf 重跑貼回 [audit] coverage_pct |
| Z44 | 個股當沖量值來源:openapi TWTB4U=標的冊(無量值;鍵 Date/Code/Name/Suspension)· rwd/TPEX 對 python 客戶端 WAF 安全導向(容器再證 swagger 都擋)→ ENG055 v0111 檔案收容道(L45):瀏覽器存 CSV → daytrade_files 夾或 via-daytrade --from-file | 候 | 操作員 | 存 CSV → via-daytrade --from-file → via-taone check-data |
| Z45 | 持股史深:工作站 holdings_daily 只有 1 檔 ETF/40 列(2026-09-07);全景 etf_holdings_daily fetch RED「ETF 23 檔 · 缺快照 1034 日格」→ VATETF 只算得到那一檔;補料=`via-etfhist backfill`(觸網;車道 VERIFIED 才呼)| 未做 | 操作員 | via-etfhist 貼回 |
| Z46 | tw_daily_prices min(date)=1900-01-01 哨兵列(via-census -Hygiene 早知)→ TA-Lib/VAP 讀價一律 date≥2020 或以 tw_prices_adj 為源;清哨兵=你的手(census DELETE 只寫不跑) | 候 | 操作員 | — |
| Z47 | OCR 車道 via_paddle_311 境壞:python 不在(FileNotFoundError)/pyvenv.cfg 缺(rc=106)→ ENG072 v0129 預檢 SKIP 誠實(L47);重建=你的手 `via-rebuild --env via_paddle_311` → `via-vrnlogic reset-backends` | 候 | 操作員 | via-ryg vrn ㉜/㊷ |
| Z48 | vrn 境無 opencc → OCR 道簡→繁直通(㉙);裝=你的手 `<vrn python> -m pip install opencc-python-reimplemented`;裝前 tag 標 [未繁化:樞紐無 opencc] | 候 | 操作員 | via-ryg vrn ㉙ |
| Z49 | 第一頁邏輯收容件的 Layout 字級階層/公司名 與 TableGeometry 隱藏格線表格重建要 chars 幾何;ENG072 sidecar 無 chars → 未接線(候);財務容差帶候接 ENG074/ENG080 | 候 | AI | 下一批看 ENG072 能否留 chars 幾何 sidecar |
| Z50 | QuantGuard 唯一活動技術指標路徑(L50)靠 polars:工作站 via_vdf_312 要裝 `pip install "polars>=1.21,<2"`(容器已證 1.44.2 → 8/8);沒裝=ABSENT 誠實不報紅(ENG086 v0101) | 候 | 操作員 | via-quantguard probe 貼回 |
| Z51 | Windows `C:\測試樣本報告` 60 份 PDF + 4 份 DOCX 未掛載到任何 AI 境;B526–B533 的 NLP/VRN 實測都只跑倉內夾具,不等於真檔已解析 | 候 | 操作員 | `NLP統一 -Pipeline -In 'C:\測試樣本報告'` 貼回 |
| Z52 | VDF 價格資料最早 2024-01-02,未達要求的 2023-01-01;補庫按你的指示停止中 → CGC154 功能驗收與 VDF 覆蓋閘會誠實非綠,不是引擎壞 | 候(你喊停) | 操作員 | 要恢復補庫再說 |
| Z53 | TA-Lib 橋 ENG083 v0100–v0103 於 commit fd51913f 被直接刪除(未進退役夾、無退役冊);L50 禁復活故不還原程式,已在退役冊補記可自 git 歷史取回 | 已記 | AI | docs/VIA_Retired_TALib_B534.json |
| Z54 | 全景掃描報位置待令三類(活樹):PINVER 150(釘死版號當路徑用)· HARDIMP 106(模組頂硬相依重庫,缺件會 Traceback=假紅)· SYSEXE 2(裸 sys.executable 派別支引擎)。會改行為,本器不自動改;逐檔逐行在 PANORAMA 報告 TAB② | 候令 | 操作員 | 說要修哪一類我就分批修 |
| Z55 | VERB 9 件的 main/parse_args 形狀不合樣板(CLI 套件與舊引擎),誠實 skip 不猜改;要統一動詞契約需逐檔手改 | 候令 | AI | 下批可逐檔處理 |
| Z56 | 外資報告目標價在側欄,修復文字沒有那一塊(批537 量出):GS 五份 · MQ 一份 · Daiwa-PCB · AMAX-KY · 華南四份 Memo · 瑞基 NR,共 16 份個股報告通篇無「目標價/Target Price/TP/PT」線索詞 → 不是抓漏,是我們手上的文字沒有這一欄(誠實四態記 `ABSENT_IN_TEXT`);要補得回原 PDF 側欄/表格幾何,與 Z49 同一條路 | 候 | 操作員 | 原 PDF 在 `C:\測試樣本報告`,本境沒有 |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件重抽~~ | 已結(批503) | — | 64/64 |
| Z57 | 前 session(VIA Integration · session_01RLMQGZLcigd5Bt5aN6J4Ck)批680 五檔已 stage 未 commit(post_turn:awaiting go to run full linter LL117);收尾階段不落地即遺失;本線(claude/awesome-bardeen-h0wm5v)自 批681 起算避免撞號 | 候 | 操作員 | 回該 session 按 go(全格子→commit→push)或裁「棄」;併線時版號對表 |
| Z58 | 一頁交接三處(倉根 VIA_HANDOVER_LATEST.md / docs ONEPAGE / 頁)停在 批554(2026-09-17),律冊已 批662、逐批 B 文已 679;L15 三處同一份但都舊;收尾清單#2 `via-vcgc page --publish` 自 批554 未跑 | 未做 | AI | 下一批發布前先 `via-vcgc status` 看容器 ABSENT 段;工作站跑更準 |
| Z59 | 律冊 lessons 停在 LL305(批662);批663–679d 的 LL306–LL335 只在 docs/commit 訊息,未入 VIA_Policy_Laws_SSOT(政策庫是批號正本,VCGC 因此印 批662) | 未做 | AI | 逐條從 docs/commit 收回冊(只增不減;id 不改;先對表再寫) |
| ~~Z60~~ | ~~六層鏈跑器 MDL172 對 import 缺件判 RED(容器 16 紅:VRN_SystemManager 拆成 缺件 10+ · 缺料 1 · 其餘 5);L16 缺件≠壞掉;Z54 HARDIMP 同族~~ | **已結(批686)**:MDL172 v0102 `_missing_module()` → ABSENT 具名套件,修法指 via-rungate --approve-install(裝=操作員的手);㉔ 釘住 | AI | — |
| Z61 | 讀券商冊的活尾版 9/10 未過拒絕閘(CGC_MDL176 status 實跑;含中央樞紐 SUP_MDL749 v0110 與 ENG086 v0109;只有 vrn_finlex v0107 過閘) | 未做 | AI(單獨一批) | SUP_MDL749 解析道改走 resolve()(拒絕→正典→疊加→聯集)+ 自測;側線 PR #53 的 v0111 也要一起看 |
| Z62 | ADJ 車道 30 件卡「上市所整個不在 ADJ 表」(tw_daily_prices / tw_prices_adj / prices_canonical 都是 892 檔 TPEX only);RAW 車道 29 件已算成(批677) | 操作員的手 | 閘 | `$env:VIA_NET_CONSENT='YES'; via-market-lists; via-price` → `via-repairprice --apply` → `via-vrnmatrix` 貼回 |
| Z63 | finlex 對帳 19 欄待一句話(ebit→operating_income?ocf 三名一路?)+ 5 個券商同義候選 PENDING_OPERATOR(GF/MORGANSTANLEY/UBS/CAPITAL/DAIWA)+ 12 個 UNKEPT 收容夾 + regen_revert 備份夾 40+ | 候 | 操作員 | `via-finlex --reconcile` 逐欄指名「A 併到 B」 |
| Z64 | 側線 PR #53(claude/busy-bell-97sa4f;+35,834 行 46 檔;dirty):SUP_MDL749 v0111 · VRN_ENG088 · Register v0241 · Manager v0147 · Deck v0158 · Grid v0431(批679c 已併其三站);P1–P6 與 36 條候選待裁;併不併=操作員 | 候 | 操作員 | 裁併/關;併後 `via-vcgc registry-sync --apply` 與 `via-vrnbook build` |
| Z65 | VRN_SystemManager(批681)七處只做四處(引擎 / 規格項 vrn_system / 格子 v0433 兩站 / 台帳+交接);Register 短令、根與 bin 梭、Deck 任務、Manager 正式名稱 未做:L70 未許可 + v0241/v0147/v0158 已被 PR #53 佔號(LL334) | 操作員的手 | 操作員 | 一句「准改 Register」→ 短令+梭+Deck+Manager 四面一起補(取 v0242/v0148/v0159 或 PR #53 併後順號) |
| Z66 | VCGC 自測 ⑬ 在 main 容器 FAIL:中央冊 ACTIVE 5909/5908(批679c 撤 Grid v0431 後一筆 ACTIVE 未退役)→ 批681 `registry-sync --apply` 後複驗 | 已修(批681 複驗) | AI | 貼回 `via-vcgc --selftest` 尾行 |
| Z67 | 姊妹倉 VIA-VDF-VRN 7 個 open PR(#2/#3/#5 自 09-10 起 dirty;#23 含 VRN_PanoramaProbe 未併;#21/#29;#35 效能 7.9×)· main 無 functional modules/VRN · 20 支 vrn-*.ts(2,470 行含測試)與母倉 VRN 引擎無對表 | 候 | 操作員 | 裁哪些關/併;要對表我就出 |
| Z68 | 姊妹倉 VIA_EnvManager.py:main 4,218 行(v0300)vs 操作員 clone 328 行(批469 已知,未見「已拉最新」實錄);.vercel/output 內另有 39 行舊產物 | 操作員的手 | 操作員 | `git -C C:\Users\tonyk\Github\VIA-VDF-VRN pull` 後貼回 `python public\via\VIA_EnvManager.py --help` 首行 |
| Z69 | 側線 PR #53 的 VRN 件已於 批682 原樣收進本線(ENG088 · 749 v0111 · 收容包 31 · 單元測試 · 交接文 · Deck v0158 · Manager v0147 · Register v0241 · 啟動器 v0101 · 梭);PR #53 剩 VDF 審視文 + Grid v0431 + 它自己的再生冊;併 PR #53 時元件冊/台帳/索引冊/規格冊/總控頁會衝突 | 候 | 操作員 | 以本線為準併(再 `via-vcgc registry-sync --apply`)或關 PR #53 改併本線 |
| Z70 | 第三條線 `claude/brave-goldberg-ri5k42`:側線 session(01YJPv…)07:52 狀態「awaiting push of claude/brave-goldberg-ri5k42 to read session VRN logic」;遠端尚無此分支;出現後三線對表(版號 LL334 · 台帳 · 冊)再併 | 候 | 操作員 | 推上來後貼回分支名,我出對表 |
| Z71 | Register v0241 / Invoke-VIA-VRN v0101 / via-ssotadd 兩梭:側線在操作員令「註冊這些」下造(L70 逐次許可寫在其交接文二-3);批682 原樣搬入本線未改一位元;若不認可刪三檔即回退;`via-vrnsys` 仍未登,下一版 v0242 | 候 | 操作員 | 認可=不動;不認可=刪檔 |
| Z72 | 實測樣本夾(操作員 2026-09-21 令「實測樣本(隨時更新):C:\測試樣本報告」)已登冊 `user.vrn_dir`(via-console set;changelog 留痕);以後不帶 --in 的 VRN 跑法都吃它;容器 ABSENT 誠實;Z51 掛進 AI 境仍是你的手 | 操作員的手 | 操作員 | 工作站 `via-vrnrun` 貼回 V2 取件數(應 ≈ 60 PDF + 4 DOCX,隨時更新以貼回為準) |
| Z73 | VRN_ENG088(側線稽核件)掛在索引冊 OFF_BOOK_PENDING(via_vrn_logic_book v0105):上不上架構冊、上哪一層(L3 驗證?)=架構裁定 | 候 | 操作員 | 一句「上 L3」或「不上」我就落冊 |
| Z74 | PS 版史 21 支(同族非尾版:OneShot v0100–0102 · VdfFetch v0100–0103 · AllInOne v0104–0110 · VRNAudit v0100–0104 · OneKey v0100 · VRN v0100)未注 PS-ACCEL(批670:尺不把版史當資產);要全注=`CGC_MDL124 --ps --apply`(不加 --ps-tail)一句話 | 候 | 操作員 | 裁「注」即跑 |
| Z75 | PS 語法閘棘輪基線 5 支/53 筆舊債(含 `VIA_Canonical_Units/Invoke-VIA-VRN-Fallback-Activation-v0136.ps1` foreach 缺 in),容器 pwsh 7.4.6 量到;不是本批弄壞的;修=另開版號檔 | 候 | AI | 裁「修」我就逐支修(pwsh 可在容器複驗) |
| Z76 | 832 支 .ps1 帶 [VIA:PS-ACCEL:v0100]「20」註解,實際 dot-source 同一個 25 冊模組;要不要把註解統一成 v0101(改 832 支只動一行註解)=你裁 | 候 | 操作員 | 裁「統一」我就用 v0106 換標記(逐字、零行為) |
| Z77 | PR #57(local/parallel-b600-bus-v0128;側線 11 commit + 工作站 EngineBus v0128)與 main 衝突 5 檔=舊快照 vs 只增不減冊;批684 已把它真正新的兩件(EngineBus v0128 · VDF 審視文)收進本線,其餘 ⊂ 本線 → PR #57 與 PR #53 都可關;`_patches/` 的 v0128 副本不收(第二顆頭) | 候 | 操作員 | 關 PR #57 / #53;要保留 `_patches` 副本再說 |
| ~~Z78~~ | ~~B600 補丁包產物 `CGC_MDL148_EngineBus_v0128.py` 自 09-18 起只在工作站(尾版律:工作站矩陣跑 v0128、倉裡任何人跑 v0127;`_patches/` 補丁包在樹上、產物不在),批604–606 刻意不碰但沒登進本清單~~ | **已結(批682B)**:操作員依 L25 推側枝 `local/parallel-b600-bus-v0128`(da89abbc)→ 本線 cherry-pick ee9c4a53;v0127+diff 位元同 · md5 213a6412 · 四十八檢 49/49;批684 同一小時收進位元相同的一份,自動合併不撞;`_patches/` 副本兩線都不收(L23) | — | PR #57 可關(內容 ⊂ 本線與批684);`.bak_b600_*` 由操作員留刪 |
| ~~Z79~~ | ~~VCGC ⑬ 把執行期產物 `VIA_Reports/env_governance/TOOLS_PLAN_latest.json` 的虛境 `(未路由:加速器通用件)`(VIA-ENV-0001)算進活元件等式:工作站有這份檔=活、容器沒有=退役。批681/682/682B 各自在容器 `registry-sync --apply` 都把它退役;併入 main 後工作站 ⑬ 會變「缺 1」,工作站再 `--apply` 又復活,容器再紅(兩台機器互翻;不是誰修錯,是尺把執行期的列算進等式)~~ | **已結(批682B)**:MDL149 v0119 把 TOOLS_PLAN 來的境標 runtime 另列(覆寫鍵 `VIA_TOOLS_PLAN_LATEST`;㉕ 合成檢有檔/無檔活元件數相同);已退役的 VIA-ENV-0001 留著不動;PR #58 Codex P1 同一判斷 · **工作站實錄(批687 收,main b45c9380 · v0119)**:registry-sync PLAN 活 5991 · 新 0 · 變更 0 · 退役 0;二十五檢 OK 25;⑬ 5991/5991 · runtime 另列 1;㉕ 有檔/無檔 5991——兩台機器都量過,互翻結束 | — | 工作站併入後 `via-vcgc --selftest` ⑬ 應綠,且 `registry-sync` 不再復活它 |
| ~~Z80~~ | ~~VDF_ENG090 ㉔:`roster()` 走 ABSENT 早退分支(名冊缺/duckdb 缺/庫缺/`tw_daily_prices` 缺)時 note 沒帶「不代設」字樣,㉔ 自檢在沒有價表的環境必紅(批682B 容器:補料前紅、補料後綠)~~ | **已結(批687)**:ENG090 v0105 初始 `out` 的 note 就帶「本閘不代設」,四態全帶;+㉕ 合成 ABSENT(正典庫指到不存在的路)釘住;24 檢 OK 24 | — | — |
| ~~Z81~~ | ~~容器 SessionStart 開機更新器 ⓪ 環境自補:jieba 在 Debian setuptools 68/wheel 0.42 建輪失敗(`install_layout`),pip 把整份 `VIA_Env_Requirements_v0100.txt` 一起放棄 → 29 條 `No module named duckdb/pandas`,OmniFetch 15 車道全假敗;`pip install --use-pep517 jieba` 可過(批682B 實證,補裝後重跑收尾 YELLOW)~~ | **已結(批687)**:`via_boot_update.sh` ⓪ 改逐件退路(整份 rc≠0 → 逐件裝,失敗再試 `--use-pep517`,只列名不放棄其餘;覆寫鍵 `VIA_ENV_REQ` 只給合成檢);合成檢 bogus+jieba → 整份 rc=1 → 逐件 2 件 · 失敗 1(bogus)· jieba 過 | — | 明天容器首開的 BOOT_*.log ⓪ 段應印「逐件補裝」而不是 29 條 No module named |
| Z82 | 財報恆等式 7 條裡 5 條的運算元正典(cogs/opex/op_margin/net_margin/total_assets/total_liabilities/equity/shares)不在 VRN_Financial_Synonyms_SSOT(營業成本/營業費用/資產總計/負債總計/權益總計 normalize_metric 回原文=UNKNOWN):ENG074 v0113 驗算多為 INSUFFICIENT 並點名,直到登錄;登錄=只增不減、你定(批504 律) | 候 | 操作員 | 一句「登錄這幾個」我就寫進 SSOT + 重跑 `via-vrnrun`;冊 `rules.financial.verify.unregistered_canonicals` 就是清單 |
| Z83 | 官方年度核對(ENG074 v0113 official_check)的料是 VDF_ENG082 的 `tw_financial`(yfinance 車道;MOPS 只探路),容器/工作站都還沒抓;沒料=NO_OFFICIAL_TABLE 誠實略;同意閘 VIA_NET_CONSENT 你設 | 操作員的手 | 操作員 | `$env:VIA_NET_CONSENT='YES'; via-py vdf "functional modules\VDF\engine\VDF_ENG082_FinStatements_v0100.py" run --only 2330,2454`(先兩檔試)→ `via-py vrn "functional modules\VRN\VRN_ENG074_FinancialPages_v0113.py" --verify` 貼回 `[官方核對]` 行 |
| Z84 | 工作站 V2 三盞紅有兩盞根因未定:SUP_MDL746 九檢 FAIL 1 · CGC_MDL141 十四檢 FAIL 1(容器兩支全綠)。**批686 更正**:鏈跑器 v0101 的「量到什麼」只印最後一行,所以看到的 `[OK] ⑨` / `[OK] ⑭` 不是紅的那一檢——批685 把 MDL141 的紅記成 ⑭ 是猜錯;v0102 起 rc≠0 先印 [FAIL] 行 | 候 | 操作員 | 拉 批686 後 `via-vrnrun`,兩格會直接印 [FAIL] 行;貼回那兩行 |
| Z85 | ENG068 ⑨ features_daily 2026-09-14 因子覆蓋 530/1978=26.8%:⑨ 要求最新完整日 100%;是因子鏈沒跑全宇宙(資料缺),不是引擎壞 | 操作員的手 | 操作員 | `via-vdffetch`(3a/3b 因子段)後 `via-vrnrun` 看 ⑨ |
| Z86 | **VCGC v0119 撞號**:main(PR #58 brave-goldberg:執行期境不進等式 ㉕)與側線 busy-bell(`+vdf_system` 段 ㉕)各有一份**內容不同**的 `CGC_MDL149_…_v0119.py`;Grid v0434 亦只在 busy-bell(本線已取 v0435 避開)。併 busy-bell 時 VCGC 必撞 | 候 | 操作員/側線 | 側線那份改 v0120 並把 main v0119 的執行期境律一起帶上,再併;或先併本線再由我出聯集版 | ← 側線 b 已解:VCGC **v0120** 疊在主線 v0119 上(主線 ㉕ 原樣保留,VDF 檢改 ㉖,二十六檢 26/26;PR #53) |

| Z87 | **第二顆頭的庫**:工作站 V4 量到 `functional modules\VRN\output\vrn_reports.duckdb`(舊路徑;105 列;最後寫於 09-20 07:54)也有 vrn_report_basic,與資料家正典 `vdf_tw_market.duckdb`(09-21 18:14)並存;讀的人與寫的人可能指到不同檔(Zero-Hydra)。矩陣已具名點出,不代刪 | 候 | 操作員 | 確認沒人再讀舊路徑後,把它改名封存(例如 `vrn_reports.duckdb.b686_retired`);要保留就說一聲,我在冊上登成刻意保留 |
| Z88 | 財報頁列只覆蓋 30/105 份(48 份非個股 N/A;**27 份個股沒有 vrn_report_financial 列**=財報頁擷取未覆蓋或表格未被判成財務頁),驗算與官方核對的分母被它壓住;v0114 起分母印在畫面 | 操作員的手 | 操作員 | `via-py vrn "functional modules\VRN\VRN_ENG074_FinancialPages_v0114.py" run` 後 `--verify` 貼回分母行;仍不上去的那些貼回檔名,我看是判準還是表格形狀 |

## 側線 2026-09-21 b 追記(VDF 子系統管理對接口;編號接續主線 Z88 → Z89–Z94;本線先取 Z74–Z78 撞主線批683,再取 Z82–Z86 撞主線批685/686,第三次取 Z88–Z93 又撞主線批687(awesome-bardeen)的 Z88,第四次才空——側線的 Z 號只能在併線當下取,而且每併一次都要重看;來源 docs/VIA_S20260921b_VDFSystemManager.md 七)

| 代號 | 事 | 狀態 | 誰 | 下一步 |
|------|----|------|----|--------|
| Z89 | Register `via-vdfsys` / `via-vrnsys`:操作員「依你建議執行」= L70 許可 → Register v0242 + 根/bin 四支梭(守門版);Z65 一併結 | 已結 | 側線 | 工作站 `via-fresh` 或重點源 v0242 |
| Z90 | VeritasCeleritas 三副本兩個版本(accelerator/ f6ecbfc4 237,382 B vs 根+50_Protection d9b107e2 237,062 B;VDF 對接口工具域 STALE) | 候裁 | 操作員 | 裁哪份是正典,另兩份對齊;對接口自轉綠 |
| Z91 | VDF engine/ 8 支無版號 .py(ENG046/049 · MDL002/003/007 只有無版號檔且卡書指著;ENG047/050/051 旁邊另有尾版檔=疑似舊複本)+ 卡書 45 張是舊快照(冊有樹無 1 · 樹有冊無 3) | 候裁 | 主線 | 立版號/清複本 → 卡書重建(不手改) |
| Z92 | VDF 獨立鏈容器沒跑過(對接口引擎域 NODATA)· 一頁交接 批554 < 律冊 批662(交接域 STALE;VRN 門同報) | 待跑 | 操作員 | `via-vdfchain run` · `via-vcgc page --publish` |
| Z93 | 工作站樹是 awesome-bardeen 批684,還沒有 VDF 對接口;本線已含 批684,快轉即可(`git merge --ff-only origin/claude/busy-bell-97sa4f`;先 stash 再生的 VIA_VRN_LogicArchitecture_SSOT 冊) | 待做 | 操作員 | 快轉後 via-vcgc 應印 v0120 |
| Z94 | `via_boot_update.ps1` 缺 ④a ENG077 主動 ETF 宇宙 · ④b ENG078 持股史(第 46–79 行從 ③ ENG056 直接跳 ④ ENG051;`via_boot_update.sh` 第 83/85 行有)——走 VIA.ps1/launch.ps1 的工作站,主動 ETF 宇宙與持股史不會自動更新(PR #53 Codex P1 審查照出;VDF 審視文 11.1/11.4 已改口) | 候准 | 操作員 | 准 .ps1 新版補兩步(L70),或改走 .sh / 手動 via-etfuniv · via-etfhist |
