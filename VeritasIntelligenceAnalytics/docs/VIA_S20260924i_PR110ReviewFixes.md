# VIA 側線 2026-09-24 第九段 · PR #110 審查三條修正(核對先過同意閘 · 候選空不回綠 · 直連尺認得 Session)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924h_UpsertCanonSharesHistory.md`。
> 本段有兩件要你裁(Z192 · Z193),寫在第五節;沒有新的工作站步驟,只換檔名(第六節)。

## 一 · 一句話

PR #110 開了之後,Codex 審出三條。我逐條實量,**三條都屬實**,都修在新版檔裡:成交值 ENG057 v0106 修了兩條，增量擷取閘 ENG089 v0104 修了一條。
同一段也把 main 的批731(PR #109)併了進來,解掉 PR 的衝突。

## 二 · 量到的(全部是實量)

| # | Codex 說的 | 實量 | 結論 |
|---|---|---|---|
| 1 | P1:`xcheck` 沒過引擎自己的同意閘,VIA_SCRAPE_CONSENT=OFF 也會去問 Yahoo | ENG057 的 `run` / `shares` 都先判 `gate_open()`(兩閘都要 YES),`xcheck` 直接交給網路工具;網路工具 SUP_MDL740 v0114 `gate_state()` 閘二寫的是 `bool(VIA_SCRAPE_CONSENT)`(**有值就開**);短令冊 Register v0242 `Set-VIAGateDefaults` 在閘沒設時補的正是 `"OFF"` | 屬實 → v0106 |
| 2 | P2:候選是空的也回 OK | v0105 拿**全域**最新日去套:`--codes` 指定的代號那天沒有嚴格市值(或它那個市場晚一天進庫),候選就空了,回的是「今天已核過 0 檔」的 OK | 屬實 → v0106 |
| 3 | P2:直連尺不認 `session.get` | VDF_ENG051 v0103(**有啟動入口** Register v0242)`def_http_get_text`:via_net 匯入不到就退回自己建的 requests Session `session.get(...)`;ENG089 v0103 只認字面上的 `requests.get`,實跑 ENG051 的直連欄是空的 | 屬實 → v0104 |
| 4 | (追出來的)同意閘「閘二」全樹有三套口徑 | ① 網路工具:有值就開 ② 短令冊 `via-gates` 的說明:http 道只要閘一,爬蟲道要 `I_ACCEPT_RESPONSIBLE_SCRAPING` ③ VDF 引擎自己的 `gate_open()`:兩閘都要 `YES` | 要你裁 → Z192 |
| 5 | (追出來的)ENG051 那條後備**不看任何同意閘** | ENG051 沒有自己的閘;via_net 掛不上(別的 python、啟動層沒載)就直連 | 他線的檔 → Z193 |

## 三 · 改了什麼(全是新版檔)

| 檔 | 版 | 為什麼 | 自測 |
|---|---|---|---|
| `functional modules/VDF/engine/VDF_ENG057_TradingValueBackfill_v0106.py` | v0105→v0106 | `xcheck`:① 在**載入網路工具之前**先判本支 `gate_open()`,閘關就回 DENY,不出網、什麼都不記;今天已核過、不必出網的照舊回報 ② 每個市場各用自己最新一個有嚴格市值的交易日;給了 `--codes` 就每檔用自己的最新日,某個市場晚一天進庫也照核 ③ 候選是空的回 NODATA,講明是哪幾檔 ④ 要核的代號有幾檔沒有嚴格市值就回 PARTIAL(rc 2),那幾檔列在 `missing` ⑤ 每列的 `exchange_date` 用那一列自己的交易日 | 16/16(+⑯) |
| `functional modules/VDF/engine/VDF_ENG089_IncrementalFetchGate_v0104.py` | v0103→v0104 | `audit` 在語法樹上追 requests 的 Session:認得出建構子(`requests.Session()`、`requests.session()`、`requests.sessions.Session()`,以及從 requests 匯入的 Session,含 as 別名);建出來的結果指派給誰(`x = …`、`self.x = …`、`with … as x`),誰就是 Session;回傳 Session 的函式算工廠,工廠的呼叫結果也算,一層層往外傳。直連多記兩種:自己建 Session(`requests.Session`),以及透過 Session 呼叫 get、post、put、patch、delete、head、options、request、send(記成 `requests.Session.get` 之類)。模組層的 `requests.put`、`patch`、`delete`、`head`、`request` 也補上。直連列多標一欄:有沒有啟動入口 | 23/23(+㉓) |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0486.py` | v0485→v0486 | 兩個站名裡的檢數:成交值 十五→十六 · 增量擷取閘 二十二→二十三 | 兩站 OK |
| 冊(就地) | — | 元件冊(新 6 · 變更 100)· 正則清冊重建 · 帳一筆 · 掉球 Z186 追記、+Z192、+Z193 | — |

實樹 `audit`(v0103 對 v0104):直連從 2 支變 3 支,多出來的是 ENG051,**有啟動入口**;真出網 18、有看庫 16、重抓風險 2、只帶網路橋 22,都跟 v0103 一樣,其餘欄位逐支也都沒變。

## 四 · 怎麼證明

| 檔 | 改壞版(全抓) |
|---|---|
| ENG057 v0106 | 新 10 個:閘拿掉 · 預設不讀 `gate_open()` · 改成網路工具「有值就開」的口徑 · 候選空還回 OK · 代號用全域最新日 · 代號按市場分組 · 有幾檔沒有也回 OK · 前 N 大用全域最新日 · 列日期用全域最新日 · 閘搬到網路呼叫之後。v0104、v0105 的舊 13 個在 v0106 上重跑,也全抓 |
| ENG089 v0104 | 新 9 個:不追 Session · 只看名字叫 session · 工廠不往外傳 · 不認 with · 不認 `requests.Session().get` 串接 · 自建 Session 不記 · 不認 `requests.put` · 不認 as 別名 · 工廠只認直接回傳建構子的寫法。v0103 的舊 8 個重跑,也全抓 |

⑯ 的負控全程不動 `os.environ`(自測不設任何同意閘環境變數):「啟動器補 OFF」那一種是把 `gate_open` 函式暫時換成「VIA_SCRAPE_CONSENT=OFF 的判法」,跑完就還原。
㉓ 有四個合成檔:ENG051 原樣的寫法 · 工廠加 as 別名加 with · 串接 · 負控。負控是一個名字叫 session 的 dict、回應物件的 `.get`、`os.environ.get`,這三種都不算直連。
回歸也跑了:讀 ENG089 的三支(VDF_SystemManager 31 · ENG093 13 · CGC_MDL170 19)和單元測試 34 都綠;VCGC 37/37;`ssot verify` rc0,黃燈跟改之前一樣;本機照 CI 跑(契約 · UAT)也綠。

## 五 · 要你裁的

- **Z192 閘二的口徑**。要不要統一，有兩條路:① 網路工具的閘二只認 `YES` 和 `I_ACCEPT_RESPONSIBLE_SCRAPING`,其他值(含 OFF)一律算關 ② 照短令冊 `via-gates` 的說明:http 道只看閘一，爬蟲道才看 token。不管選哪條，全樹每一支經網路工具出網的引擎都會跟著變，所以你裁之前網路工具不動。引擎這一側已經先修好(ENG057 v0106)。
- **Z193 ENG051 的直連後備**。可以拿掉後備(via_net 不在就誠實回 FAIL),也可以在走後備之前先判兩道閘。這是 ENG051 那條線的檔，本側線不改;量的尺已經修好，現在實樹報得出來。

## 六 · 工作站(掉球 Z186 追記)

沒有新步驟。Z186 裡 ENG057 的指令，檔名從 v0105 換成 v0106,v0105 的行為全都保留。`xcheck` 現在要兩道同意閘都是 `YES` 才會出網。

## 七 · 併 main(PR #109 批731)

照第八段第七節的做法併:
- **掉球**:兩邊取聯集。main 的 Z182(已結)和 Z188–Z190 原樣保留;本側線的 Z183–Z187 和 Z191 也原樣保留。
- **帳**:共同前綴 1330 筆，加上兩邊各新增的 4 筆，按時間排。
- **元件冊與正則清冊**:以 main 為底，跑建冊器重建。新增 27 件，都是本側線第五到八段的元件;main 原有的編號一筆都沒動。

第八段全格裡從 PR #105 帶進來的 4 盞紅，併完之後逐站重跑(格子 v0486 `--only`):**3 盞轉綠**——Celeritas 產出契約、加速器控制面、總控頁契約。批731 在 main 上重生了總控頁，八樞紐也補上了加速器橋。
剩下 1 盞是唯一接觸口控制面(CGC_MDL135 撞號),就是批731 記的 Z190,要操作員裁;main 自己也是紅的，本側線不改他線的檔。

## 八 · 還原

程式檔全是新版：把新版檔刪掉(或 `git revert` 本段的提交),尾版就回到上一版。冊是就地改的,`git revert` 就能回去。
本段沒有動任何 `.ps1`、沒有改任何 intake 正本、沒有設任何同意閘或金鑰環境變數、沒有裝任何套件、沒有出網。
