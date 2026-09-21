# 批685 · 上傳的整合引擎收容不嫁接;你的邏輯逐條對回正主,真缺的三件補上

本批進來三樣東西:① 上傳 `VRN_Integrated_ReportDatabase_Engine.py`(78,094 B · md5 `58120333d3043d6a9d7ce4d77d4fdb34`)② 工作站實錄(`via-vrnrun` V1–V5 · `via-vcgc status`)③ 你的 VRN 擷取邏輯逐字敘述。先量再做(LL329):上傳件的每一支函式樹上都有正主而且尺更嚴,所以**收容零嫁接**;真缺的三件不在上傳件裡,在你的敘述裡——標題格式、官方年度核對、加減除驗算——本批補上,規則全放冊上。

併線註:本批開工時 origin/main 已併 PR #58(第三條線 `claude/brave-goldberg-ri5k42`,批682B:VCGC v0119 · EngineBus v0129),先併回本線(三檔衝突全是只增不減冊/再生物 → 聯集;台帳 1280+2+2=1284)再開工。Z70 結。

## 一 · 上傳件量出來的(收容 `references/intake/VRN_Integrated_ReportDatabase_Engine_b685/`,L03 零觸碰)

| 上傳件做的事 | 上傳實作 | 樹上正主 | 量證(容器) |
|---|---|---|---|
| 檔名切分(中/英/數/標點)、4 碼=ticker、長數字=日期 | `tokenize_filename` + 三支 date regex + `(20)+260131` 拼接 | **VRN_ENG084_FilenameTokenParse**(保護→切分→歸類;規則自 SUP_MDL749) | `凱基_神達3706 TT_初次評等_(20)260131_TargetPrice 168.pdf` → 代號 3706(鎖平台 3706 TT)· 日期 2026-01-31 · 券商 KGI;`2330.TW` 鎖平台;`1140122` → 2025-01-22 |
| 日期(西元 8/6 碼、民國 7 碼、114/08/22、(20)250122) | 4 個 parser | **SUP_MDL749.parse_date_any**(冊上 12 樣式) | `(20)260131`/`260131`/`20260131`/`1140822`/`114/08/22`/`2025-01-22`/`Jan 22, 2025` 全解 |
| 名稱以四碼向 TWSE/TPEX 查(OpenAPI t187ap03_L / mopsfin_t187ap03_O) | `urllib.request.urlopen` 直連 | **CGC_MDL142_TWNameBook**(正典 tw_listings_industry 1,978 檔;`refresh` 委派 VDF_ENG055 同兩支 OpenAPI;同意閘不代設) | 容器名冊 ABSENT 誠實(庫空);工作站 1,978 |
| 券商同義字 + 檔名局部識別 | 內建 22 家別名表 + 子字串 | **SUP_MDL749.broker_of** + **CGC_MDL176** 聯集閘(拒絕→正典→疊加→聯集) | 凱基/KGI/凱基證券/元大/GS/Goldman Sachs/兆豐/Megabank/國票 9/9 命中 |
| 評等同義字 | 4 鍵別名表,`re.search` 無詞界 | **SUP_MDL749.rating_of**(收容冊+本土尺度+詞界守衛) | 買進評等/Buy/增加持股/Outperform/中立 5/5 |
| 首頁上/左/右資料區 | top 42%、左右 45–55% 切塊;**無字級** | **VRN_ENG072.extract_page1_zones**(header/right/body/footer + 字級≥13/粗體標題;法 C GLE 字重階層) | 四區 + 兩級字級在位;五層階層仍候 chars 幾何(Z49) |
| 一行一句、接到句點、TRIM | `repair_sentences_until_period`(240 字硬切) | **VRN_ENG082.repair_text/fix_contents** · SUP_MDL749.repair · ENG072.split_sentences_repaired · ENG085 還原 | 在位 |
| 檔名×首頁代號合流 | 加權計分 2.0/2.3/+0.4 | **SUP_MDL749.source_priority/reconcile**(本文 > 周邊 > 檔名;衝突三值都列)+ ticker_crosscheck | 冊上 order 讀得到 |
| 目標價 / 現價 / 上漲空間 | 兩條 regex;現價=文字抓 | **SUP_MDL749.tp_of**(`目標價:$345` 亦解)· **ENG073** ADJ/RAW 車道(新鮮度閘)· **ENG080** K1(L99 除權息基準) | tp_of 6/6 |
| 財報表格 → long format | pdfplumber `extract_tables` + 25 科目別名 + 期間標籤 | **VRN_ENG074_FinancialPages**(財務頁判準 · 期間表頭 · 數據列 · 同義字 SSOT · 單位只認宣告 · MOPS 列優先序 · 三方對照) | 二十五檢 → 本批三十一檢 |
| Parquet 唯一主庫 + 累積 upsert;CSV/JSON/DuckDB 派生 | pandas/pyarrow | **VRN_ENG081_ParquetMainDB**(L90:DuckDB 正典 → Parquet ⊎ 去重 → 派生) | 在位 |
| HTML 矩陣 / 信心分數 | 加權 0.18/0.22/… | **VRN_ENG083_VerifiedMatrix**(四態燈 + N/A;判對率/可判率;不用分數用誠實態) | 工作站 V4 100% = 461/461 |
| Google Sheet 車道 | gspread 憑證 | 樹上無;不收(憑證=你的手) | — |

上傳件 `--self-test` 在容器 PASS(離線、零落檔)。不嫁接的三條律:L09(網路件只收不掛線,它直連不走 AegisNexus 也沒同意閘)· L90(Parquet 是派生層)· L05/L30(每件功能正主都在,再抄一份就是第二把尺)。

## 二 · 你的邏輯逐條對表

| # | 你的原話(節) | 正主 | 態 |
|---|---|---|---|
| C1 | 非股票名稱都透過四碼向 TWSE/TPEX/MOPS 取得;KY 公司表達沒問題 | MDL142 name_of(簡稱正典)· ENG073 v0116 四階梯官方名 | GREEN(工作站);容器名冊 ABSENT 誠實 |
| C2 | FILENAME 中英文/標點交接處斷開再 TRIM;4 碼=台股 ticker,與第一頁其他代碼型式對照前 4 碼相同 | ENG084 + SUP_MDL749 ticker_crosscheck/platform_matrix(九型×三平台) | GREEN(實測四例) |
| C3 | 較長數字是日期;可能民國;可能 (20)250122 | SUP_MDL749.parse_date_any | GREEN(實測 8 例) |
| C4 | 其他中英文=公司或券商;券商從同義字比對;檔名允許券商局部識別 | broker_of + MDL176;公司名走 C1 不用檔名字 | GREEN(9/9) |
| C5 | 第一頁分上左右資料區,layout 可識別 | ENG072 四區 + pdfplumber 法 B 雙法對照 | GREEN |
| C6 | 字體大中小階層+粗細 → 大標題/中標題/小標題/本文;不相干小字頁尾/備註 | ENG072 字級≥13 或粗體≥11 兩級 + footer 區;**五層階層與「公司名=最大且粗體」候 chars 幾何** | PARTIAL(Z49) |
| C7 | 修正過的本文分類標註;一行一句一資料;標題沒句點;銜接斷句+空格 TRIM | ENG082 fix_contents(類別/次分類/頁數標)· repair · ENG085 | GREEN |
| C8 | 修復中的本文可查目標價/評價方式/邏輯 | tp_of + ENG080 extract_val_method/extract_basis(批554/558 修復後尋找) | GREEN |
| C9 | **第一點標題 台積電(2330.TW)-本文標題**(公司名+括號代碼+大字標題) | **缺** → **ENG080 v0109 compose_headline**:名只認 name_official/名冊;.TW/.TWO 只認查得到的市場(查不到用裸碼不盲猜);標題已含代號=原句 | **本批補**(三十檢 30/30) |
| C10 | 第一點:上漲空間 % 用最新調整後收盤價算;目標價;評價方法邏輯理由 | ENG080 K1(L99 因子鏈 · TP 合理帶 · 基準日律) | GREEN;算得出幾份=價表涵蓋(Z62) |
| C11 | 第二點:稀釋 EPS 內容與成長性原因理由 | ENG080 K2(EPS n～n+3 · YoY · 主要原因) | GREEN |
| C12 | 剩餘內容分 2 點;內容都是第一頁 | ENG080 K3/K4 remainder_two(48 行) | GREEN |
| C13 | 年度財務報表頁將所有資料截取下來 | ENG074(全列入庫;UNKNOWN 科目誠實候 register) | GREEN |
| C14 | **對 TWSE/TPEX/MOPS 年度資料核對;至少一起對起來就確認相同;都有時以歷史數據為主** | **缺**(三方對照從沒對過官方)→ **ENG074 v0113 official_check**:× VDF_ENG082 `tw_financial` 同檔同年;AGREE/ROUNDING/UNIT_SCALE/DIVERGE/ONLY_REPORT/NO_OFFICIAL_*;`winner=OFFICIAL` · `value_final=官方`;每份 `__alignment__` CONFIRMED=至少一項對得起來 | **本批補**;料=VDF_ENG082 run(同意閘你的手,Z83) |
| C15 | **其他數據用加減法跟除法來驗證** | **缺對正典表的**(vrn_finaudit 讀舊 Digest_Matrix;MDL008 退役)→ **ENG074 v0113 arith_check**:冊上 7 條恆等式 PASS/FAIL/UNIT_SCALE/INSUFFICIENT/DIV_ZERO;缺運算元**點名缺哪個正典** | **本批補**;5 條等正典登錄(Z82) |
| C16 | SSOT REGEX 同義字及 VIA 中擷取 VRN 是關鍵參考 | VRN_FieldRules_SSOT(SUP_MDL749 讀冊)· MDL176 聯集閘;本批的核對/驗算規則也**只放這本冊**(`rules.financial.verify`),引擎零影子規則、零容差數字 | GREEN |

## 三 · 本批做了什麼(檔)

| 件 | 檔 | 驗 |
|---|---|---|
| 收容 | `functional modules/VRN/references/intake/VRN_Integrated_ReportDatabase_Engine_b685/`(原字節 + `_INTAKE_MANIFEST_b685.json`:逐函式→正主對照表) | md5 對上傳位元相同;`.gitattributes` `-text` 鎖位元 |
| 規則冊(只增) | `supportive modules/registry/VRN_FieldRules_SSOT_v0100.json` +`rules.financial.verify`:官方表/欄位對照 16 欄/優先序 OFFICIAL_WINS/態表;恆等式 7 條(GP_SUB · GM_DIV · OP_SUB · OPM_DIV · NM_DIV · BS_ADD · EPS_DIV)+ 容差;未登錄正典清單 | 照原格式寫回(indent 1 · ASCII 跳脫 · 無尾換行;LL333 round-trip 斷言) |
| 財報頁 | `VRN_ENG074_FinancialPages_v0113.py`:`verify_rules()`(只從冊上取)· `official_check()` · `arith_check()` · run 同輪 · `--verify/--arith/--official` · status 分佈 | **三十一檢 31/31**(㉖–㉛:規則只從冊 · 驗算三態 · 官方核對端到端 · 歷史數據為主 · 誠實略 · 冪等+正典零觸碰) |
| 四點文摘 | `VRN_ENG080_FourPointDigest_v0109.py`:`compose_headline()` · `_yf_known()`(不盲猜)· `_name_known()` · `headline_fmt` 加欄 | **三十檢 30/30**(㉚ 七例 + fixture) |
| 格子 | `CGC_MDL064_SelftestGrid_v0435.py`(**v0434 跳過**:側線 busy-bell 已佔)兩站改名;站數 287 不變 | 全格子見五 |
| 元件冊/索引冊/總控頁 | registry-sync(VCGC v0119)活 6004 · 新 11 · 變更 212;VRN 索引冊 build 引擎指標 44;總控頁再生;契約 19/19 | — |

## 四 · 工作站實錄怎麼讀(你貼回的 V1–V5 · vcgc)

**V2 六層鏈 GREEN 29 · RED 3 · NODATA 14**

| 紅 | 容器 | 讀法 | 下一步 |
|---|---|---|---|
| SUP_MDL746 九檢 FAIL 1 | 9/9 綠 | 九檢裡吃真檔的是 ⑥(全庫 PDF 密度分得開)⑦(THIN 不降級);工作站掃的是 `C:\測試樣本報告` 64 份,容器是倉內 18 份 → 最可能是真檔上的密度閘;**哪一檢沒貼到** | 貼回 FAIL 那一行(六節 PS) |
| CGC_MDL141 ⑭ | 14/14 綠 | ⑭ 用**固定夾具** 比 MDL139.vrn_report_dirs 與本檔 _report_dirs 解出來是否一致,與 incoming 有幾份無關;工作站紅=兩邊解出不同 → 候選根因:工作站 registry 夾裡 MDL139 尾版與容器不同(併 PR #56/#58 後多版) | 貼回 ⑭ 括號裡的 `正本在位=… 兩邊解出一致=… 夾=…` |
| VRN_ENG068 ⑨ features_daily 2026-09-14 530/1978=26.8% | — | ⑨ 要求最新完整日**因子覆蓋 100%**;530/1978 = 因子表只算了 530 檔 → **資料缺,不是引擎壞** | 重跑因子鏈(`via-vdffetch` 3a/3b 因子段)後 `via-vrnrun`(Z85) |

NODATA 14:ENG072 逾時 60s(鏈跑器站別逾時,Z60 同族=缺件/逾時≠壞)· ENG064 缺料 · 其餘缺料。

**V2 資料驗證 105 × 7 欄**:target_price NODATA 58 = Z56 側欄 16 份 + 修復文字沒那一欄;rating NODATA 33 · analyst 34 → 非個股 48 份佔大半(N/A 律,分母已扣)。
**V3 修價**:ADJ_NO_KEY 49 = 上市所整個不在 ADJ 表(Z62)→ 同意閘 + `via-market-lists` + `via-price` → `via-repairprice --apply`。
**V4 矩陣**:判對率 100% = 461/461;可判率 62.7%/67.1%(扣 N/A)。
**vcgc**:邏輯庫同步落後 6 → `via-vrnlogic sync-db`;註冊稽核缺 1 → 本批併 PR #58 後 registry-sync 已重跑;中央治理家族 RED(console RED)→ 貼回 `via-vcgc --selftest` 尾三行;七處 4/7 = Z65 等「准改 Register」。

## 五 · 本批實測(容器)

```
ENG074 v0113 --selftest          三十一檢 OK 31 · FAIL 0(㉖ 規則只從冊 · ㉗ 驗算 PASS/FAIL/INSUFFICIENT 點名 · ㉘ 官方核對 AGREE/UNIT_SCALE/NO_OFFICIAL_TICKER · ㉙ 歷史數據為主 · ㉚ 誠實略 · ㉛ 冪等+正典零觸碰)
ENG080 v0109 --selftest          三十檢 OK 30 · FAIL 0(㉚ 七例組字 + fixture Citi TITLE_HAS_CODE + 不盲猜)
SUP_MDL749 v0111 --selftest      48 檢 OK 48(規則冊 +verify 段零回歸)
VCGC v0119 --selftest            二十五檢 OK 25(併 PR #58 後 registry-sync 重跑)
VRN_SystemManager v0101          廿五檢 OK 25;records 收容包 21(含 _b685)
registry-sync --apply            活 6004 · 新 11 · 變更 212 · 退役 0
契約 test_master_control_contract 19/19 OK
全格子 v0435(LL117)             OK 255 · FAIL 20 · SKIP 6 · TIMEOUT 0(282s;GRID_20260921_095933)· 對 批684 第七跑逐站相同:只在本批紅 0 · 只在 批684 紅 0(20 紅=容器無料/無境,與 main 基線相同)
上傳件 --self-test               PASS(離線;零落檔)
```

## 六 · 你的手(工作站)

1. 拉本線 → `via-reload`(或 `git pull origin claude/awesome-bardeen-h0wm5v`)→ `via-vcgc registry-sync --apply` → `via-vrnbook build`。
2. **兩行紅燈的原文**(Z84):
   `via-py vrn "supportive modules\70_VRN_Rules\SUP_MDL746_PDFPlumberPlusHub_v0100.py" --selftest` 貼 FAIL 行;
   `via-py vrn "supportive modules\registry\CGC_MDL141_ClosingGate_v0109.py" --selftest` 貼 ⑭ 行。
3. **官方年度核對要料**(Z83):`$env:VIA_NET_CONSENT='YES'`(你的手)→ `via-py vdf "functional modules\VDF\engine\VDF_ENG082_FinStatements_v0100.py" run --only 2330,2454` → `via-py vrn "functional modules\VRN\VRN_ENG074_FinancialPages_v0113.py" --verify` 貼 `[官方核對]` 與 `[驗算]` 兩行。
4. 標題格式看得到:`via-vrn4`(ENG080 尾版自動接 v0109)→ `via-vrn4 show 2330` 看第一行是不是 `名(代號.TW)-標題`。
5. 因子覆蓋(Z85):`via-vdffetch` 後 `via-vrnrun` 看 ENG068 ⑨。
6. 正典登錄(Z82):告訴我「登錄 cogs/opex/…」哪幾個,我就寫進 VRN_Financial_Synonyms_SSOT。
7. 側線併前(Z86):busy-bell 的 VCGC v0119 改 v0120 再併,否則撞 main 的 v0119。

## 七 · 掉球

+Z82(恆等式運算元正典未登錄)· Z83(tw_financial 要先抓;同意閘)· Z84(工作站兩盞紅要原文)· Z85(features_daily 因子覆蓋 26.8%=資料缺)· Z86(VCGC v0119 側線撞號)。Z70(第三條線)結:PR #58 已併 main。
