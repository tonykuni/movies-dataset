# 批690 · VDF 一族的誠實燈(Z92 前五支)· 2026-09-21

> 操作員令(批689B 續,「GO ON」):全景式檢視 · 識別錯誤 · 避免傷害引擎跟系統 · 避免九頭龍 · TEST DEBUG TILL IT WORKS。
> 本批對象=容器全格子剩下的 14 盞同一型病(Z92):**表不在時 SQL 直接炸**。先 VDF 五支;VAP/中央 9 盞下一批。
> **撞號**:Grid v0440 已在 busy-bell 線(LL334),本線跳 **v0441**;批690 掃全部遠端未撞。
> 同時開了 **VRN 線** session_01GkJosEQeEZpMhCyJpF8BuZ(操作員令「開一個 vrn」;批691 起、只做 VRN;本線不再碰 VRN 引擎)。

## 一 · 尺沒動,燈改對(L16)

一張表不在,舊行為是 `CatalogException` 把整支自測炸掉——一行 FAIL 都不印,格子記紅。這不是量測,是崩潰。
批584(ENG072)、批538(ENG060/061/062 綁 2330 的假紅)、批689B(VRN 五盞)都是同一條律:**缺料記 NODATA rc2 並指路;表在、數字不合才 FAIL**。
門檻(≥95% 列數、≥10 群、≥30 碼…)一個字沒動;本批不是「為了綠改尺」,是把崩潰改成量測。

| 引擎 | 檔(版號) | 缺哪張表=NODATA | 指路 | 自測(容器,無料) |
|------|-----------|-----------------|------|-------------------|
| 產業混合分類冊 | `VDF_ENG058_IndustryUnifiedMap_v0101.py` | tw_listings_industry | `$env:VIA_NET_CONSENT='YES'; via-market-lists`(容器 openapi 三車道回非 JSON=固定缺) | ① OK · ② NODATA · ③–⑥ SKIP · rc2 |
| 調整後價格層 | `VDF_ENG060_AdjPriceLayer_v0105.py` | tw_daily_prices | `via-price`(ENG054 boot ②)→ `VDF_ENG060 build`(②b) | ① NODATA · ②–⑧ SKIP · rc2 |
| 因子庫 | `VDF_ENG061_FeatureStore_v0103.py` | tw_prices_adj · prices_canonical(視圖;SHOW TABLES 含視圖已實證) | `via-price` → ENG060 build → `VDF_ENG061 build`(②c) | ① OK · ② NODATA · ③–⑨ SKIP · rc2 |
| 族群聚合因子層 | `VDF_ENG062_GroupFeatureLayer_v0103.py` | features_daily | `VDF_ENG061 build` | ② NODATA · ③–⑦ SKIP · ⑧ OK(兩條路共用一處判準)· rc2 |
| 故事輪動橋 | `VDF_ENG072_StoryRotationBridge_v0102.py` | tw_listings · tw_daily_prices · tw_prices_adj + 籌碼三張(六張一次探) | 缺哪一族指哪一條(名冊/價→調整層/籌碼·當沖) | ① OK · ② NODATA · ③–⑧ SKIP · rc2 |

預設 CLI 路(boot 日更呼的 `build`)同樣先探表:缺=印 `[NODATA] … 指路` rc2,不再 Traceback。
每支各帶一個六行的 `_missing_tables(db, need)`(庫檔不在=全缺;`SHOW TABLES` 含視圖)——沒抽成共用模組:五支引擎各自可獨立執行(尾版 glob 檔),跨檔 import 版號檔=新的分岔;判準只有「表在不在」一句。

Grid **v0441**:五站 `rc0 → nodata_ok`(rc0 或 rc2 皆 OK;rc1 才紅),站數不變。

## 二 · Z91 對表(交給 VRN 線裁;本線不動程式)

| 件(尾版) | 活樹誰引用 | 六層冊 | 建議 |
|-----------|-----------|--------|------|
| SUP_MDL015_VISVRNBrokerAliasFullList_v0100 | SUP_MDL115_ControlTower.py · via_vrn_logic_book(家族指標) | L0 節點 | **改綁**(讀冊走 ENG086/樞紐) |
| VRN_ENG062_SummarizerV1_v0102 | VIA_SYSTEM_MANAGER_v0147 | L4 節點 | **改綁** |
| VIS_VRN_BrokerAlias_Extension_v0224 | 只剩 CGC_MDL177 稽核 · SUP_MDL560 編譯探針 | 無 | 退役候 |
| VIS_VRN_Q1_AliasRoutePatch_v0100 | 只剩 CGC_MDL177 稽核 · 編譯探針 · 舊登記 JSON | 無 | 退役候 |
| VIS_VRN_BrokerAlias_Compatibility_v0222 | 只被 SUP_MDL015 引 | 無 | 退役候(MDL015 改綁後即孤兒) |
| VIS_VRN_PDFTextLayerFallbackPlan_v0222 | SUP_MDL115_ControlTower.py · 舊 ps1 | 無 | 候(ControlTower 還指著) |
| vrn_report_digest_v0116 | CGC_MDL081_SubsystemManagerV2 · 舊格子 | 無 | 候 |

## 三 · 沒動的(避免傷害/九頭龍)

VAP/中央那 9 盞(VAP 模板跑器 matplotlib · 全球市場觀測 · 寬表刷新器 · 市場分析引擎 · 引擎簡化稽核 · 治理主控台 · 治理台 UI Matrix · 系統同步樞紐 · 資料庫目錄台)一支未動——下一批一族一批。VRN 引擎一個字沒改(VRN 線接手)。正典冊/聯集冊/律冊未改。

## 四 · 全格子 v0441(容器;PATH 帶 /opt/pwsh)

OK 266 · FAIL 9 · SKIP 6 · TIMEOUT 0(235s;GRID_20260921_125458)。對 批689B 收尾那一跑(OK 261 · FAIL 14):**新紅 0 · 消失 5**(五站全綠,NODATA rc2 被 nodata_ok 收)。剩 9 盞全是 VAP/中央一族:VAP 模板跑器(matplotlib)· 全球市場觀測 · 寬表刷新器 · 市場分析引擎 · 引擎簡化稽核 · 治理主控台 · 治理台 UI Matrix(綠燈率門檻,隨其他站走)· 系統同步樞紐 · 資料庫目錄台。regen gate 還原再生物後才 commit。

## 五 · 收件:姊妹倉 VRN 交接膠囊(跨 session;已對正本驗過)

2026-09-21 13:18Z 收到姊妹倉 `tonykuni/VIA-VDF-VRN` 那邊 Claude session(session_019RDuSzMmVQmsRCnPaDxbMX)排程送來的交接:操作員令「將專案中所有的 VRN 接到此處理」。
**正本**:該倉分支 `claude/festive-ptolemy-ts2yyh` commit c1989e6 的 `docs/VIA_VRN_HANDOVER.md`(103 行;PR #23)。本線已 fetch 讀過:內容與通知一致。
注意:PR #23 **未併**進姊妹倉 main(88de4b0,至 PR #35);是該分支把 main 併進自己(a270174)。膠囊只在分支上。

| 膠囊給的 | 一句話 |
|----------|--------|
| 二 對表(Z67 要的) | 20 支 `vrn-*.ts` + `VRN_PanoramaProbe.py`(1073 行,十段探針 S01–S10)+ `VIA_BridgeInjector.py` + attachments 23 件 ↔ 母倉 MDL001–008 · VRN_SystemManager v0103 · vrn_d8b_filename_parser · FirstPageEngine v0127 · vrn_method_kernel v0102 · vrn_finlex v0107 · vrn_finaudit v0105 · vrn_report_digest v0116 · knowledge/ 六本 · registry/VRN_BROKER_LIST_v01.json |
| 三 交叉驗證(64 件檔名) | TS parseFilename vs 探針 64/64;母 `vrn_d8b` vs 探針 代號/日期 64/64、券商 50/64(母解析器不吃「兆豐/台新/凱基…」中文後綴 13 件;探針不列 GF 1 件);TS knowledge.ts 缺「兆豐」。建議統一接 `registry/VRN_BROKER_LIST_v01.json`(LL63) |
| 四 橋實測(唯讀) | 姊妹倉正典 ACCEL-BRIDGE 在母樹 RESOLVED → SUP_MDL737 v0105;NET 橋 via_net_unified_v0101;母 VRN 368 py 有 367 早帶同一區塊(零重複);48 ps1 有 47 帶 PS-ACCEL,注入器只加 $VIAPS20 車道 |
| 六 你的手 | a. 裁 PanoramaProbe 落地(併姊妹倉 main 或 L04 新版號檔進母 VRN)· b. 工作站真跑探針把 64 件 BLOCKED 變真結果 · c. 券商正本對齊 · d. 母樹 PS 車道注入器 dry-run(--apply 操作員)· e. 七處登冊 + 掉球 A/Z67 結案、Z68 依姊妹倉 main v0300 復核 |
| 七 VDF session 的手 | VDF_PricesCanonical/VDF_FactorLibrary 已帶橋;對接點 digest-four.ts / vrn-field-cache.ts(57 欄)/ vdf-prices-factor.ts;探針 JSON 可餵「只量不動手」格子;PS20 ↔ VIA_ACCEL25 對照表待出 |

**本線的處置**:VRN 的部分(a/c/e 的 AI 端)轉交 **VRN 線** session_01GkJosEQeEZpMhCyJpF8BuZ(它只做 VRN、批691 起);b/d 與 --apply 是操作員的手;七節 VDF 對接點登本線待辦(下一批看)。掉球 A / Z67 / Z68 更新如清單;不劃線(併不併 PR、關不關 #2/#3/#5/#21/#29 是操作員裁)。

## 六 · 實錄讀出(工作站貼回 2026-09-21;母倉 9637ace5)

| 你貼的 | 讀出 | 修 |
|--------|------|----|
| VDF_ENG060 v0105 `--selftest` | 八檢 OK 8 · FAIL 0(台 2,193,186 列 · 全 223,470;③ 2330.TW 因子數學對合;④ 守恆 4510=4510) | 無——有料走完整檢,NODATA 路不干擾 |
| VDF_ENG061 v0103 | 九檢 OK 9(台 2,193,186 · 1990 檔;ret_1d 2,191,196 · ma20 2,155,382) | 無 |
| VDF_ENG062 v0103 | 八檢 OK 8 · SKIP 0(ROTATION_TW_20260914_ENG070;37,751 列 · 33 群 · 193 成員;④ (8, 8)) | 無 |
| VDF_ENG058 v0101 | 六檢 OK 6(35 碼;TWSE_ONLY 7 · TPEX_ONLY 2;ELEC 910 / FIN 41 / TRAD 1030) | 無 |
| VDF_ENG072 v0102 | 六檢 OK 6(七輸入檔全出:full_market_daily 2,193,186 · monthly_revenue 92,334 …;preflight rc=0) | 無 |
| 姊妹倉 `VRN_PanoramaProbe.py`(64 件;膠囊六節 2) | verdict **AMBER**;S01–S05 OK 64(S04 格式 WARN 4=四份 docx)· S06 OCR 路由 OK 41 / WARN 23 · S07 NLP SKIP 64(閘關=政策)· S08–S10 READY 64;**卡點:無**;契約風險 GREEN 41 · YELLOW 23 · RED 0。根因:RC3_DEPS_ABSENT 選配套件 9/18 缺(polars, xxhash, pypdf, docx, markitdown, paddleocr, pytesseract, rapidfuzz, psutil)· RC5 檔名契約黃燈 23 件(晨會/產業/無代號;依規不轉紅)· RC6 NLP 閘關(VIA_NET=0;政策非故障)。VRN tree PRESENT · modules 14/14 · deps 9/18 · accel bridge RESOLVED · python 3.13.7 | 裝 9 個選配套件到 via_vrn 境=操作員的手(VIA_EnvManager;不動 base);黃燈 23 件不發明代號;轉交 VRN 線 |

讀法:五支引擎在有料的機器上走的是原本的完整檢,容器上走的是 NODATA 路——同一支檔兩種誠實。探針 64 件沒有一段 BLOCKED/FAIL,AMBER 來自缺件(RC3)與黃燈(RC5),不是引擎壞。

## 七 · 併 PR #53(busy-bell)後的重疊與 Codex 兩條

**撞名**(LL334,先併 main 的贏):側線同日也開了 `VDF_ENG058 v0101`(只探庫檔)與 Grid v0441(其後 v0442/v0443);併線取 main 那兩份,本線內容改疊到 main 上開下一版——

| 本線原件 | 疊到 main 後 | 差在哪 |
|----------|-------------|--------|
| ENG058 v0101(本線) | **v0102**(=側線 v0101 + 探到表) | 側線只探「庫檔在不在」;庫在但 `tw_listings_industry` 不在(容器固定缺)build 仍炸 |
| Grid v0441(本線,從 v0439 長) | **v0445**(=main v0444(批691B)+ 三站 nodata_ok + 輪動橋站名;本線 v0444 又與 PR #67 撞名,再讓一次) | 側線 v0440–v0443 已含 批689B 各站與 ENG058/目錄台/全球市場/治理主控台/排版規格 nodata_ok |
| ENG086 v0110 / 總管 v0103(本線) | 側線 v0112 / v0104 已含本線內容(併 PR #63 時聯集) | 不必再疊;VRN 線接手後續 |

**Codex(PR #65)兩條都真,都修**:

| 條 | 讀出 | 修 |
|----|------|----|
| P1 ENG072:export 回 NODATA 沒設 err,run()/CLI export 只認 err → export rc0、run 接著 preflight 吃舊一次 export 的陳料 | 真:v0102 的 NODATA 路只在自測收尾,run/export 兩條 CLI 路漏了 | **v0103**:NODATA 在 preflight 之前就 rc2 停(run 與 `export` 兩路),印因由;容器實測 export rc2 · run rc2 |
| P2 ENG060:NODATA 早退把 ⑦ boot 接線 / ⑧ 紀律宣告一起退掉,nodata_ok 站在容器永遠走這條路 → 拿掉 boot 登記格子仍綠 | 真(早退不准把承諾一起退掉,批687 同律);ENG061 ⑨ 同病 | **ENG060 v0106** `_chk78()` · **ENG061 v0104** `_chk9()`:不吃料的檢兩條路共用一處判準都跑;紅=rc1 不被 NODATA 蓋住。容器實測:ENG060 OK 2 · NODATA 1 · SKIP 5;ENG061 OK 2 · NODATA 1 · SKIP 6 |

併後鏈(main 尾版):VCGC **v0122** 二十八檢 28/28 · 總管 v0148 總控頁 92 任務 · 契約 OK · registry-sync 活 6141 · 新 7。

## 八 · 併後全格子 v0444(容器;PATH 帶 /opt/pwsh)

OK 271 · FAIL 6 · SKIP 8 · TIMEOUT 0(301s;GRID_20260921_165618)。對併前 run16(FAIL 9):**新紅 0 · 消失 3**(VAP 模板跑器 · 全球市場觀測 · 治理主控台——側線 c 修的)。剩 6 盞:寬表刷新器 · 市場分析引擎 · 引擎簡化稽核 · 治理台 UI Matrix(綠燈率門檻)· 系統同步樞紐 · 資料庫目錄台(側線站已改 nodata_ok,引擎在容器仍 rc1=引擎那邊還沒改)。下一批一族一批。

**再併一次**:推完 fdc325bf 後 main 又進了 PR #67(envmanager 線 批691/691B:Grid v0444 · VCGC v0123)。本線 v0444 撞名讓位,內容疊到 **v0445**;併後鏈 VCGC v0123 廿九檢 29/29 · 契約 OK · registry-sync 活 6169 · 新 7。

**全格子 v0445**(再併後):OK 273 · FAIL 5 · SKIP 8 · TIMEOUT 0(228s;GRID_20260921_170450)——對 v0444 那一跑新紅 0、消失 1(治理台 UI Matrix 綠燈率過門檻);剩 5 盞=Z92 餘族。

## 九 · 實錄讀出(二)——工作站 via-vrnrun V2–V5 與姊妹倉 VIA_EnvManager scan/plan(2026-09-21 晚)

| 你貼的 | 讀出 | 誰的手 |
|--------|------|--------|
| V2 鏈證據表(105 份 × 7 欄)後 **rc=1** | 七欄燈:代號 GREEN 57/NA 48 · 報告日 97/NODATA 8 · 券商 90/15 · 評等 72/33 · 目標價 38/NODATA 58/YELLOW 9 · 上漲空間 36/67/2 · 分析師 71/34。rc=1 那一站的 [FAIL] 行在你貼的上方沒進來 | 貼回 V2 段最上面的 [FAIL] 行(交 VRN 線) |
| V3 repair-price | 列 105 · 有改動 10 · 新拿到庫價 0;價出自 tw_daily_prices 56、(無代號或無報告日)49;ADJ 上漲空間算得出 39(ADJ_OK 25 + 因子1 14)· ADJ_NO_KEY 49 · ADJ_NO_TARGET 17;目標價年齡 STALE_365 15 · FRESH_90 10 · AGING_180 8 · EXPIRED_OVER_1Y 6(描述性,不判燈) | — |
| V4 驗真矩陣 ENG083 v0119 | 格子 735:GREEN 461 · YELLOW 11 · NODATA 215 · NA 48;判對率 100%(461/461)· 可判率 62.7%(扣不適用 67.1%);**第二顆頭仍在**:`functional modules\VRN\output\vrn_reports.duckdb`(105 列 · 最後寫於 09-20 07:54)與資料家正典並存(Z88) | Z88 封存=操作員的手(改名即可) |
| V5 via-console build | 3064 KB 零 CDN,rc=0 | — |
| 姊妹倉 `VIA_EnvManager.py scan` | 全 GREEN(UVT-01–08 · LOCAL-FREE · uv · ISO99)· PLAN YELLOW「待同意 · 母機 launch.ps1 · 本檔不 spawn」 | — |
| 姊妹倉 `VIA_EnvManager.py plan` | ENV-FLEET 47 境/管 41;UVT findings 335 · **FAIL 1** · WARN 44;DRY_RUN_PASS:S03 via_core OPTIMIZE(13 pins)· S28 via_nlp(3)· S36 via_vdf(37)· S42/S43 ISOLATE rapidocr/img2table;其餘 36 步 VERIFY_ONLY DEFERRED(未登錄環境,--verify-legacy 才驗);RED ACTION 5 條全是 LEGACY_POLICY advisory(camelot_311/paddle_311/vif_aio/vif_core 保留不遷移;vmt_pm 退役候選要明示 --retire-environment)。**計畫裡沒有 via_vrn 的裝件步驟**:探針缺的 9 個選配套件(polars/xxhash/pypdf/docx/markitdown/paddleocr/pytesseract/rapidfuzz/psutil)不會因 apply 而裝上,要用母機 launch.ps1 的 -AddTool(或把它們登進 via_vrn 的 manifest)另開一步 | 裝件=操作員的手;VRN 線可先把 9 個套件登進膠囊的處置清單 |
| 姊妹倉分支又前進 | `claude/festive-ptolemy-ts2yyh` 965504f「PyMuPDF table fallback · real import checks · honest dependency warnings · correct corpus count」 | VRN 線取件時拉最新 |

**第三次併 main**(f9600d5d,PR #66 VRN 線 批691:ENG086 v0113、膠囊收件、Z109–Z113):台帳 1303;全格子 v0445 OK 273 · FAIL 5 逐站相同(GRID_20260921_171422)。Z112(ENG086 站名二十二→二十三檢)留給 VRN 線在本 PR 併後開 v0446——Grid 版號一天撞三次,不再在本線疊。
