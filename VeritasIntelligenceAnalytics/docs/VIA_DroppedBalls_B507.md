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
| Z43 | VATETF 實測:`via-vetf` 工作站 **OK 40 筆(PASS 2/REVIEW 38)**;但 eps/forward_pe 覆蓋 0% → ENG085 v0102/v0103 FactSet 稀釋 EPS 兩期碎片(L43)→ 再跑看 coverage_pct.factset_eps_n/forward_pe_n | 未做(等實錄) | 操作員+AI | via-vetf 貼回 |
| Z44 | 個股當沖表:工作站 `via-bus one tw_daytrade_stock` RED(TWSE rwd 回安全頁非 JSON;TPEX rwd 讀逾時)→ ENG055 v0110 L15 改 openapi TWTB4U 優先(同一支已能抓標的冊;量值鍵名防禦對映並印回)→ 再跑貼 note(若 openapi 無量值鍵=候源,量能指標 NULL 誠實) | 未做(等實錄) | 操作員+AI | `via-bus one tw_daytrade_stock` 貼回 note |
| Z45 | 持股史深:工作站 holdings_daily 只有 1 檔 ETF/40 列(2026-09-07);全景 etf_holdings_daily fetch RED「ETF 23 檔 · 缺快照 1034 日格」→ VATETF 只算得到那一檔;補料=`via-etfhist backfill`(觸網;車道 VERIFIED 才呼)| 未做 | 操作員 | via-etfhist 貼回 |
| Z46 | tw_daily_prices min(date)=1900-01-01 哨兵列(via-census -Hygiene 早知)→ TA-Lib/VAP 讀價一律 date≥2020 或以 tw_prices_adj 為源;清哨兵=你的手(census DELETE 只寫不跑) | 候 | 操作員 | — |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件重抽~~ | 已結(批503) | — | 64/64 |
