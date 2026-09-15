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
| Z15 | via_vdf_312/via_vrn_312 解譯器壞(SRE module mismatch)根因未定:RunGate v0102 三試(-E/-S/-I)+ pyvenv.cfg + PYTHONHOME/PYTHONPATH 現值貼回才定;重建境=操作員的手 | 操作員的手 | 操作員 | 貼回 via-rungate(v0102)與診斷段 |
| Z16 | PARTIAL 16 件(Z1)自批510 起例行跑不再重燒 OCR(部分命中);要重抽=你機器 `via-firstpage -RetryFailed`(涵蓋 PARTIAL);矩陣 vrn_firstpage 應不再 600s TIMEOUT,貼回驗 | 操作員的手 | 操作員 | 貼回 `via-ryg vrn -Timeout 600` 的 vrn_firstpage 秒數 |
| Z17 | 並行線 PANORAMA_HANDOVER-v0103「已列入下一輪」:Windows VRN 三站真實失敗斷言與 OCR runtime 自動收集、VETF 快照日期覆蓋 vs 持股完整性、gap plan 只代表查庫完成;`new modules engines/*` 另線收容件(檔名帶 (2)/(3))候裁入 references/intake | 未做 | AI | 下一批照該檔「已列入下一輪」逐項 |
| Z18 | 批510 我把 vrn_firstpage 600s TIMEOUT 歸因給「16 件 PARTIAL 每跑重燒 OCR」——你的實錄證明那 16 件是數位 PDF(DUAL_ZONES,合計 30.89s);600s 是並行線 panorama 自己的 vrn_firstpage 跑法,不是本線;PARTIAL_HIT 仍有效但歸因改正 | 已在 一-n 更正 | AI | 無 |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件重抽~~ | 已結(批503) | — | 64/64 |
