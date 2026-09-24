# VIA 側線 2026-09-24 第十一段 · 關聯層去重寫入收正典(掉球 Z194)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924j_UpsertCanonAllFamilies.md`(PR #111,已併)。
> 你回了「yes」要做 Z194 那 3 支。本段有一件工作站的事(Z199,只有本機三庫裡有「一個庫檔放多張表」時才要做)和一件要你裁的事(Z200)。

## 一 · 一句話

Z194 記的 3 支(關聯層:SQL 直接從一張表或一個 parquet 寫進另一張表)全收進正典。正典 SUP_MDL753 另立一支 `upsert_select`,
Z191 那支 `upsert_rows` 的 anti-join 也改走它——正典裡同一件事只剩一份 SQL。三支都拿真庫副本做前後對照,結果零差異;
全 VDF 尾版裡私寫的去重寫入 3 → **0**。量的時候另外抓到 3 個舊洞,新舊版都有、不是遷移造成的,新版修掉。

## 二 · 量到的(全部是實量)

| # | 量到什麼 | 怎麼量 |
|---|---|---|
| 1 | 三支語意各不同:ENG065 沒有鍵,用 EXCEPT 整列去重,表不在時整批照搬(連完全重複的列也照搬);ENG079 NULL 也算同鍵、來源同鍵先自己去重、where 只挑一部分、沒有鍵時用 EXCEPT,「計畫」(只數不寫)和「實寫」是兩份 SQL;ENG081 鍵用 =、不先去重、新列另存一張暫存表再落 parquet 增量 | 逐支讀碼 |
| 2 | ENG081 舊版照**位置**插:既有 tw_universe 的欄序跟本支不同時,ticker 和 asof_date 對調寫進去,兩欄都是文字所以不報錯(跟 Z191 ENG052 同一類) | 真庫副本:893 列全對調 |
| 3 | ENG079 `scan`(和不帶 `--apply` 的 `run`)說是「唯讀盤點」,實際在正典庫建空表:容器副本 scan 一次多出 4 張 0 列的表(tw_chips_daily · tw_rest_daily · local_px_daily · local_rest__misc)外加台帳表 via_ingest_ledger;全球庫檔不在時還會建出一個空庫檔。自測 ③ 量了表清單,卻沒拿來比 | 真庫副本 + 自測 |
| 4 | ENG079 同一個庫檔(duckdb/sqlite)裡的多張表取名錯:`Path("store.duckdb::pe").stem` 是 `store`,每張表都叫檔名。沒有鍵的表全併進一張(欄位聯集,不相干的表混在一起);rest 區有 date+ticker 的表 kind 都補成檔名,第二張表同日同票的列被當成重複**整批丟掉**——狀態 OK、不報 | 真庫副本:pe、pb 兩張表 → pe 889 列 0 新增 |
| 5 | ENG079 籌碼區來源沒有 kind 欄時,同日同票但欄位不同的第二個來源(例:法人一檔、融資一檔)0 新增,它的欄在既有列上永遠是 NULL | 合成兩檔實跑,新舊版一樣 → Z200 |
| 6 | 正典 `upsert_rows` 原本的語意:鍵用 =(NULL 鍵不算同鍵)、同一批裡同鍵的兩列都會寫進去。改走 `upsert_select` 後照舊,自測 ㊸ 把這兩條釘住 | 自測 |

## 三 · 改了什麼(全是新版檔)

| 檔 | 版 | 為什麼 | 自測 |
|---|---|---|---|
| `supportive modules/SUP_MDL753_VIACommonUtils_v0111.py` | v0110→v0111 | 新增 `upsert_select`(第四節);`upsert_rows` 的 anti-join 插入改走它(= 鍵、不去重,跟 v0110 原文同) | 43/43(+㊸) |
| `VDF_ENG065_DbImport_v0101.py` | v0100→v0101 | `_import_one` 交正典(`seed_all=True`:表不在時整批照搬) | 9/9(+⑨) |
| `VDF_ENG079_LocalDbConsolidate_v0102.py` | v0101→v0102 | 計畫與實寫交正典(同一條 SQL);順帶修第二節 3、4 兩個舊洞:scan 開唯讀連線(庫檔不在就用記憶體替身)、`_ensure_table(dry=True)` 只算會寫哪幾欄、台帳表只在 `--apply` 建;庫內表取名改用 `_unit_stem()`(取表名) | 15/15(+⑭ +⑮;③ 加驗 scan 不動表清單) |
| `VDF_ENG081_UniverseAlign_v0102.py` | v0101→v0102 | `update` 交正典:計畫用 `plan=True`,實寫用 `stage="_uni_new"`(新列照舊落 parquet 增量);照欄名插 | 13/13(+⑬) |
| `VDF_ENG089_IncrementalFetchGate_v0106.py` | v0105→v0106 | 私有去重寫入普查:實樹名單 9 → 12 族;合成檔加一支綁 `upsert_select` 的(不算私有) | 24/24 |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0489.py` | v0488→v0489 | 四站站名的檢數(原擬 v0488,收尾時批732 先併進 main 用了 v0488 → LL334 改號) | 相關 15 站 OK |
| 冊(就地) | — | 元件冊(新 4:`_qid` · `upsert_select` · `_unit_stem` · `consolidate._open`;變更 232;退役 1:ENG065 `_qcols`)· 正則清冊重建 · 帳一筆 · 掉球 Z194 結、+Z199、+Z200 | — |

## 四 · 正典 `upsert_select` 怎麼用

`upsert_select(con, table, src, keys=None, *, cols=None, where="", null_safe=True, dedup_source=True, create=True, seed_all=False, stage=None, plan=False)`

| 參數 | 意思 |
|---|---|
| `con` | 呼叫端自己的連線(正典不開、不關) |
| `src` | 任一個關聯:表 · 視圖 · 暫存表 · `read_parquet('…')`;`where` 套在它上面(不含 WHERE 字) |
| `keys` | 有鍵:anti-join。`null_safe=True` 用 IS NOT DISTINCT FROM(NULL 也算同鍵);`dedup_source=True` 來源同鍵先留一列(留哪一列不保證) |
| 沒有 `keys` | EXCEPT 整列去重(NULL 視為相等,來源自己的重複列也只留一份) |
| `cols` | 預設 = 表和來源的共同欄(照表的欄序);表不在 = 來源全部欄;自動取欄結果是零 → 回 `None`(誠實跳過,不寫);明給空的 `cols=[]` → ValueError |
| 表不在 | `create=True` 照 cols 從來源建空表(欄型照來源),再走同一條路;`seed_all=True` 那一次整批照搬不去重;`create=False` 回 0 |
| `stage="名"` | 這次的新列另存成一張暫存表(0 列也建),給呼叫端落增量檔 |
| `plan=True` | 只數不寫(數的就是實寫會插的列;表不在時也照數);唯讀連線可以跑 |
| 回傳 | 新增列數(取 INSERT 自己回報的數) |

三支怎麼接:

| 引擎 | 呼叫 |
|---|---|
| ENG065 | `upsert_select(con, table, "read_parquet('…')", seed_all=True)`;回 None → SKIP |
| ENG079 | 計畫 `upsert_select(con, table, src, keys, cols=wcols, where=w, plan=True)`;實寫同一行不帶 plan |
| ENG081 | 計畫與實寫都 `upsert_select(con, "tw_universe", "_uni", ["asof_date", "ticker"], cols=…, null_safe=False, dedup_source=False, …)`,實寫多帶 `stage="_uni_new"` |

## 五 · 怎麼證明

**真庫副本零差異**(對照腳本放在容器暫存區,沒有進倉)。容器裡的 vdf_tw_market、vdf_global_market 各複製兩份,同一批輸入分別給舊版和新版。
比整張表(兩個方向各做一次 EXCEPT ALL,再比欄名欄型)、回傳值、報表(去掉時間戳)、印出來的字:

| 組 | 輸入 | 結果 |
|---|---|---|
| H1 ENG065 新庫 | 十張真表匯出成 parquet(147 萬列)+ 一檔完全重複列 + 一檔不合檔名協定;跑兩次 | 全同(第二次 0 新增;完全重複的列照搬 943 = 893 + 50) |
| H2 ENG065 表都在 | 真庫副本每張表先刪掉同一批列,再匯入補回;另加多一欄 · 少一欄 · 零共同欄 | 全同(補回 210,928 列;零共同欄兩邊都 SKIP) |
| H3 ENG079 | 真資料做的本機三庫(價:裸碼 DATE 型 + 完全重複列 + 兩列 NULL 日 + 非台股碼 + 對不到的碼;中文欄 csv;庫檔內價表;籌碼;協定檔 tw__ / gl__;無鍵 csv)× scan / apply / 再跑 / --force 兩次 | 全同(25,074 + 1,258 列;NULL 日那列只進一次;表內沒有重複鍵)。唯一不同是設計上的:scan 後舊版多出 4 張空表 + 台帳表,新版一張都不多 |
| H3b ENG079 舊洞 | 一個庫檔放四張表(sentiment · rates 沒有鍵;pe · pb 有 date+ticker,各 889 列) | 舊版:pe 0 新增、兩張無鍵表併成 local_rest__store;新版:pe、pb 各 889,local_rest__rates、local_rest__sentiment 分開 |
| H4 ENG081 | 真價表 + 第十段錄下的**真 MI_MARGN** 兩天經 ENG056 落庫 × 七步(dry / apply / 指定日 / 再跑 / 預設規則 / 舊日) | 全同(tw_universe 2,677 列 · parquet 三檔逐檔同) |
| H4b ENG081 舊洞 | 既有 tw_universe 欄序不同 | 舊版 893 列 ticker 欄裝成日期;新版 0 列 |

**改壞測試**(改壞的版本要被自測抓到):

| 範圍 | 改壞版 | 結果 |
|---|---|---|
| 正典 v0111 | 22 個:null_safe 失效 · 不自去重 · 取欄不看表 · 零共同欄回 0 · 空欄不報 · seed_all 失效 · where 失效 · EXCEPT ALL · plan 數錯(三種)· create=False 失效 · stage 存錯 · 回表內列數 · 建表多欄 · upsert_rows 改成 NULL 安全 / 自去重 / 不寫 · 表在判斷 · create=False 不建 stage · plan 真的寫 | 全抓 |
| ENG065 | 3 個(拿掉 seed_all · SKIP 當 OK · 誤加鍵) | 全抓 |
| ENG079 | 16 個(計畫真的寫 · 實寫不帶 where / cols / 鍵 / NULL 安全 / 自去重 · 計畫不帶 where · scan 開可寫連線 · dry 失效兩處 · 台帳照建 · 取名改回三處 · scan 仍加欄 · dry 價表欄少算) | 抓到 14 個 |
| ENG081 | 6 個(不存 stage · 計畫真的寫 · 不給 cols · 鍵少一欄 · 改 NULL 安全 · 改自去重) | 抓到 4 個 |

沒抓到的 4 個都是等價的:ENG079 實寫不給 `cols`(`_ensure_table` 已經讓表和來源的共同欄等於 `wcols`,只差順序,照欄名插不受影響)·
ENG079 dry 時價表欄推算少幾欄(價表一定有鍵,計數只看鍵)· ENG081 改 NULL 安全 / 改自去重(`_uni` 的鍵按構造不會是 NULL、也不會重複)。
ENG089 普查的邏輯沒改;另外把 ENG065 v0100、ENG079 v0101、ENG081 v0101 放進暫存目錄量,舊版照樣被列成私有份(尾版律也對:同目錄有 ENG065 v0101 時 v0100 不列)。

**回歸**:讀 ENG089 的三支(VDF_SystemManager 31 · ENG093 13 · CGC_MDL170 19)和單元測試 34 個全綠;格子 v0489 本段四站 + 增量擷取閘 +
Z191 那十族(總擷取 · 台股回補 · 總擷取執行器 · 籌碼 · 成交值 · 估值 band · FRED · 月營收回補 · ETF×月營收 · 持股史深)共 15 站全 OK;
VCGC 37/37 · ssot verify rc0(黃燈與改前同)· 本機照 CI 綠。以上都在併進 main 4c36da58(PR #112 批732)之後重跑。

## 六 · 工作站

- **Z199**(只有本機三庫裡有「一個庫檔放多張表」才要做):先 `via-vdfdb scan`,看單元清單有沒有「檔::表」屬 rest、同一個檔 2 張以上。
  有的話 `via-vdfdb run --apply --force` 重跑一次(anti-join 冪等,只補缺的)。舊版補成檔名的 kind 列、舊的 local_rest__<檔名> 表只增不減留著,要不要清由你裁。
  路由換了目標的單元(無鍵表)台帳會自動重做,不必 --force。
- `via-vdfdb scan` 從這版起真的不寫庫(唯讀連線)。它跟之前一樣會被別的寫入中的程序擋住,擋住時照舊短等重試。
- 其餘各支叫尾版,指令不變。

## 七 · 要你裁的(Z200)

ENG079 籌碼區:來源沒有 kind 欄時鍵只有 date+ticker,同日同票、欄位不同的第二個來源進不去(第二節第 5 條)。三條路擇一:
① 籌碼也補 kind(= 檔名,跟 rest 一樣)各來源分列;② 允許「只補空欄」(正典 `upsert_select` 加 fill,只補 NULL、不覆寫;
跟 ENG079 宣告的「既有列零觸碰」相衝,要改律);③ 維持原狀,但計畫和報表標出「同鍵異欄 N 列沒進」。

## 八 · 觀察(沒改)

- ENG079 表的欄型由第一個來源決定。第一個來源是窄的 DECIMAL 時,後面放不下的值會大聲失敗(該單元 FAIL、紅燈),不會悄悄截掉。自測夾具踩到過一次,已改用 DOUBLE。
- 普查現在是 0。自測 ㉔ 只擋「收進正典的 12 族不得再長出私有份」,沒有擋「全樹必須是 0」——後者會讓別條線新加的引擎把格子弄紅,要不要收緊由你裁。

## 九 · 還原

程式檔全是新版:把新版檔刪掉(或 `git revert` 本段的提交),尾版就回到上一版。冊是就地改的,`git revert` 就能回去。
本段沒有動任何 `.ps1`、沒有改任何 intake 正本、沒有設任何同意閘或金鑰環境變數、沒有裝任何套件、沒有打任何真端點(MI_MARGN 用的是第十段錄下的回包);真庫一律只用副本。
