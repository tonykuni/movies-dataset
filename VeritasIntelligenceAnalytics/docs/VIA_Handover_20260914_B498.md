# VIA 交接紀錄 · 批498(2026-09-14)

> 立案:操作員令「**修正收尾 實測修正 VDF/VRN 將邏輯因子政策入庫 更新 GITHUB 母系統 HANDOVER REPORT**」。
> 前一份:`docs/VIA_Handover_20260913_B474.md`(批474–497 逐批紀錄仍在那裡,本份不重抄)。
> 這份檔的目的只有一個:**下一個接手的人不必看對話紀錄就能接上**。對話會卡斷,檔案不會。

---

## 〇 · 先想省 token,想好才動(批475 律,仍在)

- 不重讀大檔:`grep -n` 要改的那段,前後看幾行。
- 操作員貼回來的實測輸出**直接當量測結果**。
- 一問題一小版本檔;一批一 push;不順手擴大範圍。
- 自測輸出只印判定行與 `[計]`。

## 〇-b · 批490–498 新收到的律(原文照錄)

1. 「**data save in parquet and managed by duckdb**. this is database file: `C:\Users\tonyk\VIA System\via_database` integrate and consolidate into database storage structure which saving the largest token when fetching and testing.」→ 資料家律(批490–491):家在倉外;鏡根 `via_database\movies-dataset\data`;搬=`link`(junction,hash 定生死,零刪除),**不複製**(三副本病);刪資料是操作員的手。
2. 「**vrn 非 ocr 擷取式必要使用**,若還抓不到改用 ocr 從較簡單的工具組往雙引擎往 paddle;成功包含資料標示還原、文字修復;非 ocr 有兩個相同的相互核對,再跟非 ocr 核對;邏輯方法及其他驗證擷取方法成功後存於**中央邏輯庫**。」(批493)
3. 「**透過 envmanager 安全地導入全部工具**,基於目前環境衝突問題修復後。」(批495)
4. 「未經過我同意,目前這兩個是我指令**唯一的加速器及網路工具**,重新掛載」→ VeritasCeleritas / VeritasAegisNexus(批494;737/740 留作橋,不直 import)。
5. 「**先使用非 ocr 擷取修正驗證,失敗的輸入採用輕量型 ocr 往重型 ocr;如果都失敗,先把 dpi 提高 300~350**。」(批496)
6. 「**中高風險者直接拉出獨立環境及相關工具單獨隔離**;numpy 這種常撞的可多環境多版本搭配多 Python;加速器及網路工具中的工具很多**請勿遺漏**。」(批497)
7. 「修正收尾 實測修正 VDF/VRN 將**邏輯因子政策入庫** 更新 GITHUB 母系統 HANDOVER REPORT」(批498,本批)。

---

## 一 · 批498 做了什麼(收尾批,七件)

| # | 件 | 檔 | 自測 |
|---|----|----|-----|
| ① | **邏輯因子政策入庫**:`sync-db` 把中央邏輯庫台帳 + 律冊/工具冊/資料家冊/Baseline 的政策因子攤平寫進 DuckDB 兩張表 `vrn_extraction_logic`、`via_policy_factors`(CREATE OR REPLACE,不動其他表;庫忙=BUSY 誠實) | `VRN_ENG082_ExtractionLogic_v0102.py`(`resolve_db`:--db > `VIA_DB_VDF_TW_MARKET` > 資料家 rglob 最新 > output_hub/mega) | 14/14 |
| ② | ENG072 每次跑完 `[邏輯庫]` 後**自動 sync-db**(失敗只印一行不擋主流程) | `VRN_ENG072_FirstPageText_v0121.py` | 36/37(⑤ 空夾誠實 rc2 = 容器舊紅,v0116 基線同紅) |
| ③ | 庫表冊 +2 表(51 表;寫入端 VRN_ENG082) | `VIA_DB_Table_SSOT_v0100.json` | — |
| ④ | 匯流排**同意閘誠實態 GATED**(紫燈):引擎 fail-closed 拒跑不是壞掉;停因序 GATED → 缺件(套件壞)→ 相對 import → 缺參數 → 缺件 → 缺料 NODATA(含「Table … does not exist」「Catalog Error」「根缺」)→ 才是 RED | `CGC_MDL148_EngineBus_v0121.py` | 43/43;容器 VDF 矩陣 ABSENT 2 · GATED 12 · GREEN 6 · NODATA 5 · PLAN 18 · **RED 0** |
| ⑤ | **via_core 白名單律**收尾:無家族的加速器通用件列 `[未路由]`(69 件)永不排進 via_core;via_core 非白名單缺件(容器例:joblib)只留置 `WHITELIST_HOLD` 不排裝;白名單單一來源=`VIA_EnvManager.py def_PARAM_VIA_CORE_WHITELIST`(21 件,讀不到才用內建備份) | `CGC_MDL135_EnvGovernance_v0104.py` | 38/38 |
| ⑥ | 母系統登錄:Deck +4 任務(`vrn_logic` / `vrn_logic_syncdb` / `datahome_catalog` / `env_tools`;正式任務 60);Manager 正式名稱 +5 任務 +3 引擎;總控頁再生 | `CGC_MDL095_DeckServer_v0138.py`、`VIA_SYSTEM_MANAGER_v0123.py`、`ui_support/VIA_UI_MasterControl_v0100.html` | 25/25 |
| ⑦ | 工具冊記實測:四境 `python_measured` 3.13.7、via_paddle_311 `never_install`(opencv 兩件)、`fleet_measured_2026-09-14` | `VIA_ToolRoster_SSOT_v0100.json` | — |

**沒做、也不該做的**:再生出來的 `VIA_VDFArchitecture_v0100.json` / `VIA_UI_VDFArchitecture` / `VIA_UI_VapStack` / 可編輯模板 —— 容器沙盒庫是空的,再生會把正本改成 0 列,**一律 revert**(可編輯模板排除律,批498 起)。

---

## 一-b · 批499 · 你貼的 `via-firstpage -RetryFailed` 實錄 + 兩條新令

> 令一:「**所有的庫政策邏輯因子庫都要同步更新**」 → 全庫同步律。
> 令二:「修最後一回 同步更新 **母檔案夾、資料庫及 github 路徑都要有 handover report**」 → 交接三處律。

### 實錄讀出(直接當量測,不重跑)

| 現象(你貼的) | 根因 | 修 |
|------|------|----|
| `OCR_BUDGET(已用 404s / 257s / 1138s / 328s > 150s)` | 第二階把**整份 PDF** 餵給編排器=全卷 OCR;40 頁簡報就是 1138 秒。預算只在階與階之間查,單一階殺不掉 | ENG072 v0122 ① OCR 只送第 1 頁(fitz 切一頁暫存,同檔只切一次)③ 直呼 tesseract 車道 `subprocess timeout=剩餘預算`(硬殺)④ 每階耗時入 tag `耗時(simple 12s, …)` |
| `via-vrnlogic` 印「後端:尚無紀錄」,但 OCR 明明跑了 | `tesseract:PASS/0元素` 與 `easyocr:SKIPPED_UNAVAILABLE` 都不記;車道整階「不在位」不記;PPP `UNAVAILABLE` 不記 → **每一件都重載 Paddle 模型、重探 easyocr** | ② 全記:跑了零元素=EMPTY、UNAVAILABLE/SKIPPED=BROKEN、有字=OK;**分境鍵** `name`(本境)/`name@via_paddle_311`(車道)/`ppp:paddleocr`(道二);下一件直接 SKIP |
| `lane=via_paddle_311:本境無此階後端:paddleocr,…(在位:apache_pdfbox,marker)` | 車道只講「不在位」,查不了 | 執行器 SUP_MDL747 v0101 逐支照抄 GLE 探針 message(缺 paddlepaddle?缺主程式?)+ `probe` 欄 + `pages` |
| `tesseract:PASS/0元素`(而 `[OCR 語言]` 說 chi_tra 在) | 編排器的 tesseract 零元素,看不出是影像空白還是讀不出 | 直呼 tesseract 車道回 **墨量%**:近空白=渲染出問題;有墨讀不出=升 DPI/換後端 |
| `easyocr:SKIPPED_UNAVAILABLE 探針=requires easyocr, torch, and cached models` | via_vrn_312 無 easyocr;via_paddle_311 有 easyocr 但無 torch/模型檔 | **你的手**(裝 + 模型檔要網路,閘你開) |
| PPP:`paddlepaddle is not installed`(via_vrn_312 有 paddleocr 3.7 無 paddle) | 道二在本境永遠壞,卻每件重試 | 記 `ppp:paddleocr`+本境 `paddleocr` BROKEN(24h);`[OCR 就緒]` 帶「標壞 n」 |
| `[入庫]` 一行都沒印 | 你那次跑的是 pull 前的 ENG082(還沒有 sync_db) | v0122 缺 sync_db 時印 `[入庫] 缺:…git pull 後重跑` |

### 兩條新律怎麼落地

- **全庫同步律**(ENG082 v0103):`sync-db` 預設對**資料家每本 .duckdb**(沙盒除外)+ `VIA_DB_*` + 首選庫寫同一份 `vrn_extraction_logic` / `via_policy_factors`(同一個 hash),每本各留一列 `via_policy_sync` 對帳單;`via-vrnlogic` 印 `[入庫同步] n 庫 · 同步 x · 落後 y · 未入 z`。政策因子多了**後端健康**(哪支在哪境壞、為什麼)與判準統計。`--db PATH` 仍可單庫。
- **交接三處律**:交接報告在 ① `docs/VIA_Handover_*.md`(github 正本)② 倉根 `VIA_HANDOVER_LATEST.md`(母檔案夾;隨 git pull 到;ENG082 ⑯ 檢 sha 同一份)③ 每本庫 `via_handover` 表 + 資料家根 `VIA_HANDOVER_LATEST.md`(資料庫路徑;sync-db 落)。`via-vrnlogic` 印 `[交接三處]`。
- 庫表冊 53 表(+`via_policy_sync`、`via_handover`;三張政策表 db 欄改「全庫」)。

### 你的手(裝件都要閘 + Approve)

- `via_paddle_311` 缺 **paddlepaddle**(paddleocr 3.3.1 沒 paddle 等於沒裝)→ `via-envtools` 會列 INSTALL_TOOLS;裝完 `via-vrnlogic reset-backends`。
- 雙引擎階要 **torch + easyocr 模型檔**(via_paddle_311)。
- 裝好之前,階梯會誠實 SKIP 標壞的後端,不再每件燒幾百秒。

### 一貼即用(批499)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic reset-backends       # ① 清舊健康標記(新鍵分境)
via-firstpage -RetryFailed        # ② 4 件重試:看每階 耗時(…)、tesseract_direct 墨量%、lane probe 因由;跑完 [入庫] 全庫 + [交接]
via-vrnlogic                      # ③ 後端逐支 OK/EMPTY/BROKEN@境 + [入庫同步] + [交接三處]
via-census -Tables                # ④ 每本庫應多 via_policy_sync / via_handover
via-envtools                      # ⑤ via_paddle_311 該列 paddlepaddle/torch;裝=你開閘:$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve
```

---

## 一-c · 批500 · 你貼的 `via-census -Tables` 與 `via-envtools` 實錄

| 現象(你貼的) | 讀出 | 修 |
|------|------|----|
| 六本家內庫都有 `via_handover`/`via_policy_sync`/`via_policy_factors`/`vrn_extraction_logic`(同一時間戳 20:42) | **全庫同步律成了** | — |
| 這四張表在每本庫都點「冊外」,而且 `via_policy_sync`/`via_handover` 點 AMBER「1 天」 | 冊上 db 欄寫的是「全庫(…)」機器對不上;對帳單一列一天不是老化,是**假 AMBER**(判錯的燈和假綠一樣傷) | 匯流排 v0122:冊上 `db_scope=all_home` 的表對每本家內庫都算冊上;`lamp=rows` 的表只看列數(列數≥min_rows=GREEN、零列=NODATA)。庫冊四表 +`via_ingest_ledger` 標 lamp=rows |
| `via_paddle_311 ABSENT pymupdf(No module named 'fitz')`,其餘 12 件 OK(paddlepaddle/paddleocr/easyocr/torch 都在) | **這就是車道「本境無此階後端」的根因**:GLE 的 OCR 轉接器要 fitz 渲染頁面,fitz 不在,整批轉接器 off,只剩 apache_pdfbox/marker | T01 `INSTALL_TOOLS via_paddle_311 pymupdf`——**你的手**(閘 + Approve)。裝完 `via-vrnlogic reset-backends` 再 `via-firstpage -RetryFailed`,paddle 階就會真的跑 |
| `via_vap_312`:pandas BROKEN(pyarrow 無 `__version__`)、pyarrow 半拆、seaborn 缺 | 半拆件 | T03 REPAIR + T04 INSTALL——你的手 |
| `[未路由] 69 件` 裡有 numpy/pandas/pyarrow/duckdb/requests/openpyxl/orjson/polars/rich/loguru | 這些在 `def_PARAM_VIA_CORE_WHITELIST` 上,**白名單制=白名單件該進 via_core**,不該列未路由 | MDL135 v0105:無家族但在白名單上的加速器件路由到 via_core(只增);未路由只剩非白名單件 |
| `via_iso_ml_cuda_H → via_ml`,要把 jax+tensorflow 裝進既有 torch 境 | 違反「中高風險者直接拉出獨立環境」 | MDL135 v0105:HIGH 家族只認同名獨立境(ENSURE_ENV `via_iso_ml_cuda_H`),不借 alt;MEDIUM 家族仍可用 alt |
| `via_mix_http_M → via_core`(httpx/aiohttp ABSENT、anyio 留置) | httpx/aiohttp 在白名單,進 via_core 合律;anyio 不在,留置對 | — |

自測:匯流排 四十四檢 44/44;MDL135 四十檢 40/40(㊲ 改白名單件進 via_core;㊴ HIGH 不借 alt);庫冊 53 表(批500)。

### 一貼即用(批500)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-envtools                      # ① 計畫應變:未路由變少(白名單件進 via_core);via_iso_ml_cuda_H 改 ENSURE_ENV 獨立境
# $env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve   # ② 你決定要裝才跑:T01 via_paddle_311 pymupdf 是 OCR 車道的關鍵一件
via-vrnlogic reset-backends       # ③ 裝完清健康標記
via-firstpage -RetryFailed        # ④ paddle 階應真的跑(lane=via_paddle_311 不再「本境無此階後端」)
via-census -Tables                # ⑤ 四張政策表應「冊上」+ GREEN
```

---

## 一-d · 批501 · 你貼的 `-RetryFailed` 與 `census` 尾段(批500 之後)

| 現象(你貼的) | 讀出 | 修 |
|------|------|----|
| `候OCR 4 → 1`;`第二場…海外投資展望.pdf · OCR_simple:tesseract_direct(dpi=300,墨量 15.4%,3s) · SUCCESS` | **直呼 tesseract 車道把三件失敗抽回來了**,每件 3 秒 | — |
| 剩的一件 `第一場 2026年投資大趨勢(57 頁)`:`tesseract_direct:EMPTY(墨量 97.7%;有墨讀不出)`,HQ300 也 97.7% | 黑底白字簡報封面;tesseract 不反白讀不到 | ENG072 v0123 ① 墨量 >50% 先反白再 OCR(直呼車道 + 第三階高畫質重繪都做;tag 帶 [反白]);容器黑底白字合成頁反白後讀得到 |
| `頁1/57`、`耗時(simple 4s, dual 3s, paddle 0s, ppp 0s)` | 只送第 1 頁成了:57 頁簡報 OCR 從 1138 秒變 4 秒 | — |
| `lane=via_paddle_311:本境無此階後端:paddleocr(探針無此名)…(在位:apache_pdfbox,marker,paddleocr_ppstructure,poppler,tesseract)` | pymupdf 裝進去後 tesseract 在位了;但**兩套名對不上**:階梯用轉接器名(paddleocr/paddle_ppstructure/paddle_pdf_pipeline/easyocr),後端矩陣回的是規格名(paddleocr_ppstructure/tesseract/…,沒有 easyocr 這格)→ paddle 三支永遠「不在位」 | 執行器 SUP_MDL747 v0102 `ADAPTER_REQ`:照抄 GLE 各 adapter.probe(paddle 三支=paddleocr+paddle 模組;easyocr=easyocr+torch;tesseract=pytesseract+主程式);ENG072 v0123 ② 行程內派送 import 同一份(同一判準只寫一處) |
| `壞後端 ['easyocr','paddle_pdf_pipeline@via_paddle_311','paddle_ppstructure@via_paddle_311','paddleocr','paddleocr@via_paddle_311','ppp:paddleocr']` | 分境健康記錄成了;但 `@via_paddle_311` 那三筆是名對不上造成的**誤標** | pull 後 `via-vrnlogic reset-backends` 一次,新判準重探 |
| `[入庫] OK ×6 · 全庫同步 OK · hash 5febb3ff2983`、`[交接] 資料家根 ←`、census 四張政策表全「冊上」GREEN、`AMBER 32→12` | 全庫同步律 + 交接三處律 + 燈修全成了 | — |

### 一貼即用(批501)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic reset-backends       # ① 清掉名對不上造成的 @via_paddle_311 誤標
via-firstpage -RetryFailed        # ② 剩的一件:應見 [反白];paddle 階應派到 via_paddle_311 真的跑(不再「探針無此名」)
via-vrnlogic                      # ③ 後端 paddleocr@via_paddle_311 應 OK/EMPTY,不再 BROKEN
```

---

## 一-e · 批502 · 你貼的 `-RetryFailed` 與 `via-vrnlogic`(批501 之後)

| 現象(你貼的) | 讀出 | 修 |
|------|------|----|
| `paddle:OCR_EMPTY[…paddleocr:PASS/0元素; paddle_ppstructure:FAIL 錯=RuntimeError: A dependency error occurred during pipeline cr…][lane=via_paddle_311]`,耗時 paddle 27s | **paddle 車道真的在 via_paddle_311 跑了**(名對上了);paddleocr 跑了零元素(送的是未反白的黑底頁);另兩支是 PaddleX 相依錯(訊息被切在 160 字,尾巴才寫「請裝 …」) | ENG082 v0104 後端 why 記 400 字、status 印 150 字 → 下次貼回來就知道要裝哪個 extra |
| 第三階 `paddle:SKIP(lane=via_paddle_311 後端皆標壞 paddle_ppstructure,paddle_pdf_pipeline)`——車道的 paddleocr 明明只是 EMPTY | **我的 bug**:本境標壞的 `paddleocr`(PPP 壞)被我從**車道**候選名單一起剔掉,車道只剩兩支壞的 | ENG072 v0124 ① 本境鍵與車道鍵分開:派車道用整階名單,車道自己濾 @境 鍵(㊷) |
| `dual:OCR_EMPTY[tesseract+easyocr;…easyocr:SKIPPED_UNAVAILABLE…]`(本境跑了 3 秒) | 本境沒 easyocr,雙引擎階在本境只是重跑 tesseract=白跑;easyocr+torch 在 via_paddle_311 | ② 本階「新增的後端」本境不就緒 → 直接派車道境,不在本境重跑上一階試過的後端 |
| `tesseract_direct:EMPTY(墨量 97.7%[反白])`,HQ300 反白後 `墨量 15.3%` 仍零字 | 反白成了,但封面大字疏排,tesseract 預設版面分析(psm 3)常找不到 | ③ 零字再試 `--psm 11`(疏字)→ `--psm 6`(整塊),tag 帶 `psm=3→11→6`(㊸) |
| `後端 paddleocr@via_paddle_311 EMPTY`、`[入庫同步] 6 庫 · 同步 6`、`[交接三處] 倉根 同 · 資料家根 同` | 分境健康、全庫同步、交接三處全成了 | — |

自測:ENG072 四十三檢 42/43(⑤ 容器舊紅);ENG082 十六檢 16/16。

### 一貼即用(批502)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic reset-backends       # ① 清掉 160 字被切的舊紀錄
via-firstpage -RetryFailed        # ② 剩的一件:dual 應派車道(easyocr 在 via_paddle_311);第三階 paddle 應跑反白頁;直呼車道 psm=3→11→6
via-vrnlogic                      # ③ 後端 paddle_ppstructure@via_paddle_311 的錯全文(尾巴的「請裝 …」)貼回來——那是你的手
```

---

## 一-f · 批503 · 批502 跑到了:64 件全部抽出

| 你貼的 | 讀出 |
|------|------|
| `[OCR_simple:tesseract_direct(dpi=300,l=chi_tra+chi_sim+eng,psm=3→11,墨量 97.7%[反白],5s)[繁化]] 第一場 2026年投資大趨勢.pdf · 124 字` | 最後一件:反白 + `--psm 11`(疏字)5 秒讀出;psm 3 讀不到、psm 11 讀到=封面大字疏排,版面分析要選疏字模式 |
| `[計] 64 件 · 候OCR 0`;`件 64:PARTIAL 16 · SUCCESS 48`;`壞後端 無` | **首頁擷取 64/64**;四件掃描件全走直呼 tesseract 車道(3–22 秒/件),雙引擎與 paddle 階這一輪沒有需要用到 |
| `[入庫] OK ×6 · hash fc135c673f24 · [入庫同步] 同步 6 · [交接三處] 同/同` | 全庫同步 + 交接三處成了(policy 78 列=後端健康表清掉後少了 6 列,對) |
| `via-vrnlogic` 把 `tesseract_direct(dpi=300,…,墨量 14.8%,22s)` 四件列成四種「法」各 1 | 法名帶了每件參數;ENG082 v0105 法名切到「(」為止,同法一行 |

下一個品質前線(不是故障,是操作員律的第二句「成功包含資料標示還原」):**PARTIAL 16** 件=互核 AGREE 但標示未全還原;台帳 `labels_ok=False` 的件在 `LOGIC_LEDGER.jsonl`,`via-vrnlogic` 可數。要不要追,你定。

還掛在你的手上的三件(不影響 64/64,但雙引擎/paddle 階要真的能用得先裝):
- `paddle_ppstructure@via_paddle_311` PaddleX 相依錯(下次跑到會記 400 字全文,尾巴的「請裝 …」)。
- `easyocr` 模型檔(via_paddle_311 有 easyocr+torch,缺 cached models;網路,閘你開)。
- 道二 PPP 在 via_vrn_312 缺 paddlepaddle(paddleocr 3.7 無 paddle)——不裝也行,paddle 階走車道。

---

## 一-g · 批504 · 你上傳的五件財務邏輯 + `via-vrnlogic`「同步 1 · 落後 5」

### 先認錯:五本真庫的政策表被我的自測污染了

`[入庫同步] 同步 1 · 落後 5(hash fe4d7cff83b3)`——那個 hash 是 **ENG072 自測時的台帳狀態**。批498 我把 ENG072 自測 ㊲ 的首選庫導向暫存,
但批499 全庫同步律之後 `sync_targets` 還會掃 `VIA_DATA_HOME` 與 `VIA_DB_*`,所以 `via-ryg` 跑格子自測時,把 8 筆 fixture 寫進了你
**五本真庫**的 `vrn_extraction_logic` / `via_policy_factors` / `via_policy_sync` / `via_handover`(vdf_tw_market 因為被導向暫存而倖免;其餘表零觸碰)。
修:ENG082 v0106 `VIA_SELFTEST=1` 時 `sync_targets` 只認 env 指定的那一本(不掃家、不掃 VIA_DB_*);ENG072 v0125 自測期間設旗 + 家指暫存 + 暫撤其他 VIA_DB_*(結束還原);
兩邊各加一檢(ENG082 ⑰、ENG072 ㊹)。**復原=你跑一次 `via-vrnlogic sync-db`**(CREATE OR REPLACE 覆寫回真台帳,其餘表不動)。

### 五件上傳量測(先量再造)

| 件 | 量測 | 處置 |
|---|------|------|
| `VIA_VRNLogic_AllInOne_v0201.py` | **新**。VIA-VRN-LOGIC-001 2.1.0;純標準庫;離線;容器 `--selftest` 十六檢 16/16;有 `--install apply` 自裝功能 | 收容 `references/intake/VIA_VRNLogic_AllInOne_v0201_b504/` + MANIFEST;**永不 apply**;掛載走橋 |
| `vdf_fetchers_financials.py` | **新**。TW→MOPS(存根,實際回空)→退 yfinance;直呼 requests/yfinance | 收容 `VDF/references/intake/vdf_fetchers_financials_b504/`;**只收不掛線**(批494 律:網路只認 AegisNexus) |
| `financial_data_standardization.py` | 與倉內 `functional modules/VRN/` 同本(CRLF 差);合併損傷件(class 先於 imports;`__main__` 示範缺 5 法),程式庫面可用(28 欄對照、15 正則、評等/期間關鍵字、交互驗證) | 不重複收容;橋以 sys.modules 登錄後 import(dataclass 註記解析才過——這就是 finlex 走 AST 的原因) |
| `VRN_ENG074_FinancialPages_v0106.py` | 與倉內尾版同本(CRLF 差) | 不收;本批出 v0107 |
| `VDF_MDL006_FinancialModel.py` | = 倉內 `VDF_MDL006_FinancialModel_sha3da0113e.py` 去掉加速/網路橋頭的原件(45 行差全是橋頭) | 不重複收容 |

### 造了什麼

- **SUP_MDL748 財務邏輯統轄橋 v0100**(只掛不搬):`second_opinion(科目)`(AllInOne FINANCIAL_SYNONYMS + FDS 28 欄)、`rating_of`(BUY/HOLD/SELL/NOT_RATED)、`parse_filename`、`validate_formulas`、`policy_rows()`(兩本冊攤平 130 列);九檢 9/9。
- **ENG074 v0107**:SSOT `normalize_metric` 未命中(UNKNOWN)才問第二意見,只寫在 raw_text 註記 `[二見 total_assets@allinone]` 與跑完的「候 register」清單,**canonical 不改**(單一真相仍是 `VRN_Financial_Synonyms_SSOT`;要不要登錄=你定)。量過:SSOT 沒有 總資產/股東權益/營業活動現金流/營業毛利/流動比率,兩本冊都有——這就是二見的價值。十九檢 18/19(⑬ 容器舊紅:v0106 基線同紅,NO_TICKER/NO_DATE 在容器的 crosscheck 夾具;你機器上批466 曾 18/18)。
- **ENG082 v0106**:政策因子 +橋兩本冊(via_policy_factors 84 → 210 列左右);自測零污染律;十八檢 18/18。
- 登冊:Register v0197 `via-finlogic [status|opinion <科目>|rating <字>] | -SelfTest`(別名 財務邏輯);Deck v0139 `fin_logic`(釘 61);Manager v0124 正式名稱;格子 v0299 +一站;主控台冊 +`fin_logic`。

### 一貼即用(批504)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 覆寫回真台帳(政策表 +財務兩本冊);6 庫應同一 hash
via-vrnlogic                      # ② [入庫同步] 應 同步 6
via-finlogic -SelfTest            # ③ 九檢
via-finlogic                      # ④ 橋現況 + 二見範例
via-vrn4                          # ⑤ 四站鏈重跑:ENG074 v0107 末行 [二見] 候 register 清單貼回來(要不要登錄 SSOT=你定)
via-ryg -Timeout 300              # ⑥ 跑完再 via-vrnlogic 一次:應仍 同步 6(自測不再污染真庫)
```

---

## 一-h · 批505 · 你貼的 `via-ryg` 矩陣 + 「實測 vdf vrn vetf」

| 你貼的 | 讀出 | 修/做 |
|------|------|------|
| `[37/44] vrn/vrn_logic · VRN_ENG082 v0106 → RED` | ENG082 自測 ⑮/⑰ 在你機器上跑:bootstrap 匯出的 `VIA_DB_*` 真庫全進了 `sync_targets`,目標數對不上=FAIL;**而且 ⑮ 又把 fixture 寫進真庫**(容器加一個 `VIA_DB_FAKE1` 就重現:假庫多出四張政策表) | ENG082 v0107:整段自測先撤 `VIA_DB_*`/`VIA_DATA_HOME`、設 `VIA_SELFTEST=1`,結束還原;⑲ 證明;容器帶假 VIA_DB_* 跑 19/19 且假庫零觸碰。**你 pull 後跑一次 `via-vrnlogic sync-db` 復原** |
| `[12/44] vdf/fin_statements · 缺席 (PLAN)` | 主控台冊這格從批442 起就是 PLANNED、母倉無引擎;你上傳的 `vdf_fetchers_financials.py` 就是它 | **VDF_ENG082_FinStatements v0100 上船**(只掛收容件不搬):雙閘 fail-closed(`gate_state`;閘你開)、yfinance 車道以 AegisNexus `ResilientHTTPClient` session 注入(新版 yfinance 拒收就退原生並講明)、MOPS 走 NetUnified `http_text` 探路(解析=候)、`tw_financial` 23 欄+fetched_at 派生層冪等、parquet 由 duckdb COPY 落 `mega/fin`(零 pyarrow);八檢 8/8;`via-bus catalog` 已見 `[在位] vdf/fin_statements … 動詞=run` |
| VDF 26 項全 PLAN | 矩陣預設「真跑 vrn,vap;其餘只解析」;帶 `--apply` 的寫庫動詞永不代跑(要 `--ids` 明點) | 實測 vdf=`via-ryg vdf,vrn -Timeout 600`;紫=閘未開(你開閘再跑);PLAN=寫庫動詞要 `--ids`;紅才是要修 |
| `[38/44] vrn/fin_logic → GREEN`、`vrn_finpages v0107 GREEN`(UNKNOWN 科目 69/59=候 register) | 批504 的橋與二見上線了 | `via-vrn4` 跑完看 ENG074 末行 `[二見]` 清單 |
| vap 三項 ABSENT(pyarrow 半拆 / pandas 缺) | 同批500:T03/T04 你的手 | `$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve` |

登冊:主控台冊 `fin_statements` 接引擎(SHIPPED);庫表冊 +`tw_financial`(54 表);Register v0198 `via-finstat [run|status|-Dry] [--only …] [--limit N] [--years N]`(別名 三大報表);Deck v0140 `fin_statements`(釘 62);Manager v0125;格子 v0300 +一站。
(批505 第一次 commit d80adde4 只上了一半——登冊腳本在 Deck 說明行的錨點上斷了;本段與 Deck/Manager/Grid/台帳在 批505b 補齊。)

### 一貼即用(批505:實測 vdf · vrn · vetf)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 先復原被自測污染的五本真庫(覆寫回真台帳;其餘表不動)
via-vrnlogic                      # ② [入庫同步] 應 同步 6;vrn_logic 站之後應 GREEN
via-finstat -Dry --only 2330,2317 # ③ 三大報表:只列目標,不碰網路
# $env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='<你的>'; via-finstat run --only 2330,2317 --years 5   # 你開閘才跑;via_vdf_312 要有 yfinance(缺=缺件誠實停)
via-ryg vdf,vrn -Timeout 600      # ④ 實測 vdf+vrn(vetf=vdf 家族第 21 項 vdf_vetf_consensus):紫=閘未開 · PLAN=寫庫動詞要 --ids · 紅才是要修
via-vetf                          # ⑤ VETF 持股×Consensus 獨跑(candidate 沙盒)
via-bus tails                     # ⑥ 紅項因由 + 引擎尾段,貼回來
```

---

## 一-i · 批506 · 大令:倉衛生 · 政策庫 · Veritas Central Governance Console(唯一對接口)· 安裝核可律 · 一頁交接

| 令 | 做了 | 證據 |
|---|------|------|
| 檢視母資料夾/GitHub 多餘資料與大量 HTML,刪 | 先量:38,917 追蹤檔、1,113 HTML、14,625 SVG、12,656 PNG、pack 560MB、VAP 3.1GB(ICON_FORGE 1.5GB)。**只刪有 md5 證據且檔名未被引用的重複件 394 件 464MB**(ICON_FORGE/ASSETS 同 md5 孿生 323 · BACKUP 孿生 71);未刪候裁八類列在報告 | `docs/VIA_RepoHygiene_B506.md/.json`(每筆 md5 + 保留孿生);批506a |
| 所有上述要求 → 政策庫 + lessons-learned | `VIA_Policy_Laws_SSOT_v0100.json`:23 律(L01–L23)+ 10 lessons;ENG082 v0108 攤平入 `via_policy_factors`(sync-db 全庫同步) | `via-vrnlogic sync-db` 後 `via-census -Tables` |
| Veritas Central Governance Console 為唯一對接口 | `CGC_MDL149_VeritasCentralGovernanceConsole v0100`(只讀不造):政策庫/邏輯庫/因子庫/資料庫/引擎調度(Deck 64 任務·規格 44 項·格子 217 站·Register 109 指令含用法與別名=**指令參數不丟失**)/多矩陣/環境工具/自動編號註冊表/註冊稽核/L19 安裝核可/一頁交接;十一檢 11/11 | `via-vcgc [status|page|onepage|audit|register-plan|check] [-Publish]`(別名 中央控管) |
| 所有引擎模組功能工具環境都要註冊 | 註冊稽核:硬碟引擎家族(尾版)227 · 已登冊 186 · **未登冊 41**(誠實列於一頁交接第六段);`via-vcgc register-plan` 出建議登冊清單(只列不寫;核准後另批登冊) | `VIA_Reports/vcgc/REGISTER_PLAN.md` |
| 環境統一測式無誤後才可核可安裝 | 律 L19:MDL135 v0106 `tools --apply --approve` 與 `apply --approve` 在同意閘之後再過 RunGate 閘(判定 GREEN 且 24h 內),否則 BLOCKED_UNITEST 零動作;㊵ 三態證明;VCGC `check` 同律 | `via-rungate` → `via-vcgc check` → 才 `via-envtools -Apply -Approve` |
| 詳細 handover 整合成同一頁 + 環境工具管理 + 自動編號註冊表 | VCGC 一頁交接 `docs/VIA_Handover_ONEPAGE.md`(八段:政策庫/安裝核可與環境工具/邏輯因子資料庫/引擎調度與多矩陣/指令與參數/註冊稽核/自動編號註冊表/交接本文三四五段);倉根 `VIA_HANDOVER_LATEST.md` = 同一頁;每本庫 `via_handover` 表隨 sync-db 入 | 動態段以你機器 `via-vcgc onepage -Publish` 為準;倉內是 commit 時快照 |
| 實測 vdf/vrn 通過即可 | vrn 五矩陣 GREEN(vrn_logic 站修好);vdf 真跑=你機器 `via-ryg vdf,vrn`(閘你開;寫庫動詞 --ids) | 貼回 `via-bus tails` |

登冊:Register v0199 `via-vcgc`;Deck v0141 `vcgc_status`/`vcgc_page`(釘 64);Manager v0126;格子 v0301 +一站;MDL135 站→v0106(四十檢);ENG082(VRN)→v0108(十九檢)。

### 一貼即用(批506)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h     # 會刪 394 件重複件(git 可回溯)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 政策庫 23 律 + lessons + 交接一頁入六本庫
via-vcgc                          # ② 唯一對接口現況(八庫一眼)
via-vcgc page -Publish            # ③ 一頁交接 + 頁(以你機器的報告為準;-Publish 才寫 docs/倉根/頁)
via-rungate                       # ④ 環境統一測式(RunGate)
via-vcgc check                    # ⑤ L19:GREEN 且 24h 內 → INSTALL_OK,才准 via-envtools -Apply -Approve
via-vcgc register-plan            # ⑥ 未登冊 41 家族的登冊建議(只列;你核准我再登)
via-ryg vdf,vrn -Timeout 600      # ⑦ 實測 vdf+vrn;via-bus tails 貼回來
```


## 一-j · 批507 · 「這是多 AI 寫作的工具?要一個 prompt 完整引導下一個 AI 接手不掉球;檢查掉球紀錄;格式長久使用;收尾更新母檔案夾/資料庫夾/GitHub」

| 令 | 做了 | 證據 |
|---|------|------|
| 是不是多 AI 接力寫的 | **是**。每一段對話都會被壓縮/換人,AI 自己沒有記憶;**檔案是唯一的記憶**(倉 = 母檔案夾 = 每本庫的 `via_handover` 表三處同一頁)。所以「不掉球」= 把球寫進檔、寫進台帳、寫進掉球清單,並由 VCGC 一頁交接把三者攤在同一頁 | `docs/VIA_AI_Handover_Prompt_v0100.md` D 段 |
| 一個 prompt 完整引導下一個 AI | `docs/VIA_AI_Handover_Prompt_v0100.md` **A 段**=開場提示詞(整段貼進新對話即可:讀三個檔 → 12 條律 → 接手驗收三指令 → 工作節奏 → 掉球定義);VCGC 一頁交接 **〇 段** 原文嵌入,所以 `VIA_HANDOVER_LATEST.md` 一開就是提示詞 | `via-vcgc onepage` 第 〇 段 |
| 給交接者(離場 AI)的收尾 | 同檔 **B 段**=收尾清單 8 條(每條要證據路徑:commit/push 乾淨、台帳、交接本文 一-N 段、掉球清單、sync-db、page -Publish、自測、母檔案夾拉齊);做不到的寫「沒做+為什麼」,不准沉默 | 本段就是照 B 段收的 |
| 格式長久使用 | 同檔 **C 段**=交接紀錄固定格式 〇–八(批號/令/做了/證據/沒做/掉球/一貼即用/驗收貼回);交接本文每批一節 `一-N` 就是這格式;掉球清單只增不減、結案劃線 | `docs/VIA_DroppedBalls_B507.md`(24 列 · 未結 23 · ~~W~~ 已結) |
| 檢查上述掉球為紀錄 | 掉球審計:A/D/G/I/P/R/S/T/U/V/X/Y 舊球 + Z1–Z12 本輪新球(Z1 PARTIAL 16 標示還原、Z2 未登冊 40 家族、Z3 衛生第二階、Z4 MOPS 解析、Z5/Z6 vdf·vetf·三大報表真跑=操作員的手、Z9 公式驗證、Z11 治理項入規格、Z12 MasterControl 你機器重生);每列有 狀態/誰/下一步 | VCGC 一頁交接 **九 段** 自動帶入(列數/未結數) |
| VCGC 帶提示詞與掉球 | `CGC_MDL149 v0101`:`prompt_doc()`(尾版 `docs/VIA_AI_Handover_Prompt_v*.md`)、`dropped_balls()`(尾版 `docs/VIA_DroppedBalls_B*.md`);一頁 〇/九 兩段;頁卡;格子站「特殊」標示(PYCODE/自我引用站不判紅);十二檢 12/12 | `via-vcgc page -Publish` |
| 收尾:母檔案夾 / 資料庫夾 / GitHub | GitHub:批507 commit+push;母檔案夾=你 `git pull` 後倉根 `VIA_HANDOVER_LATEST.md`(sha 與 docs/ONEPAGE 同);資料庫夾(可不用):`via-vrnlogic sync-db` 把同一頁寫進每本庫 `via_handover` + 資料家根副本 | 下方一貼即用 |

沒做(誠實):Z1–Z12 都還掛著(見九段);本輪沒有新裝任何套件、沒有設任何同意閘、沒有動正本。

### 一貼即用(批507)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 同一頁交接(含提示詞 + 掉球)入每本庫 via_handover + 資料家根
via-vcgc                          # ② 唯一對接口現況
via-vcgc page -Publish            # ③ 以你機器的報告重生一頁交接(〇 提示詞 … 九 掉球)+ 倉根 + 頁
via-rungate                       # ④ 環境統一測式
via-vcgc check                    # ⑤ L19 安裝核可(GREEN 且 24h 內才 INSTALL_OK)
via-ryg vdf,vrn -Timeout 600      # ⑥ 實測 vdf+vrn
via-bus tails                     # ⑦ 貼回來
```

**給下一個 AI 的第一句話**:打開 `VIA_HANDOVER_LATEST.md`,第 〇 段照貼,第 九 段是你的待辦,第 八 段是史。


## 一-k · 批508 · 「環境安裝出了問題可以先還原原本前次環境然後把所有工具順序安裝上 中高風險一律單獨隔離」

| 令 | 做了 | 證據 |
|---|------|------|
| 先還原原本前次環境 | 律 **L24 環境復原律** 入政策庫冊(+LL11);MDL135 v0107 新動詞 `recover`(`via-envrecover`):① 還原前次 = LKGC lock 逐境 `uv pip install -r lock`(非破壞);`sync` 破壞段只在 `-ApproveRemove`;無 LKGC → Baseline 原本規劃重建 | `via-envrecover`(plan 唯讀)→ `VIA_Reports\env_governance\RECOVER_latest.json/.ps1` |
| 然後把所有工具順序安裝上 | 順序安裝律:段依境層級 **CORE 白名單 → LOW 家族境 → MEDIUM 隔離境 → HIGH 隔離境 → 外部本體 → 驗證**(同境內 建境→修復→安裝→驗證);`via-envtools` 同序;recover 模式下隔離境 `uv venv` 可建(只增) | `.ps1` 第 ② 段;㊶ 段序證明 |
| 中高風險一律單獨隔離 | `_M` 家族比照 `_H`:只認同名獨立境,**不借 alt 境**(webui 不借 via_vap_312、ml_boost 不借 via_ml/via_vdf、http_async 不借 via_core);隔離境不在 → 建同名境,件不進 alt 境(借境封鎖) | 工具冊 `risk_policy.MEDIUM` 改;㊶ 有 alt 在位仍 ENV_ABSENT |
| 閘 | ① 不受 L19 擋(LKGC 本身即曾 GREEN;同意閘仍要)② 新裝段過 L19(`via-rungate` GREEN 24h 內)否則 **RESTORED_BLOCKED_UNITEST** 誠實停,先 rungate 再跑一次(① 已做段 no-op);無同意閘 = BLOCKED_CONSENT 零動作 | ㊶;MDL135 四十一檢 41/41 |
| 登冊 | Register v0200 `via-envrecover`(別名 環境復原)· Deck v0142 `env_recover`(釘 65)· Manager v0127 · Grid v0302 · VCGC v0102 二段 +環境復原 · 台帳 1043 | `via-vcgc` 二段 |

沒做(誠實):容器裡沒有你的境,recover 只能出 Baseline 模式的唯讀計畫;你機器上有 LKGC_latest 才會走 lock 還原。真跑=你的手(下方 ⑤)。

### 一貼即用(批508)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-envgov lkgc                   # ① 有沒有前次基線(LKGC_latest;沒有=recover 走 Baseline 原本規劃)
via-envrecover                    # ② 復原計畫(唯讀):①還原 ②順序裝 ③隔離;看 RECOVER_latest.ps1
via-vcgc                          # ③ 二段看 環境復原 燈
# 真跑(你的手):$env:VIA_NET_CONSENT='YES'; via-envrecover -Execute -Approve        # sync 破壞段另加 -ApproveRemove
via-rungate                       # ④ ① 做完後環境統一測式;GREEN 才放行 ②
# $env:VIA_NET_CONSENT='YES'; via-envrecover -Execute -Approve                      # ⑤ 再跑一次:② 順序裝(① no-op)
via-vrnlogic sync-db              # ⑥ 律 L24 入每本庫 via_policy_factors
```

---

## 二 · 操作員機器實況(他貼的 EnvManager v0300 AUDIT,run ENV-20260914_112000;直接當量測)

| 事實 | 影響 |
|------|------|
| 48 境在 `C:\Users\tonyk\envs` | 工具冊 `VIA_ENV_ROOT` 對得上 |
| `via_vrn_312` / `via_vdf_312` / `via_vap_312` / `via_paddle_311` 全是 **Python 3.13.7**(名不符實) | 冊上記 `python_measured`;不改名(EnvManager 才是境主) |
| `via_paddle_311`:easyocr 1.7.2 · paddleocr 3.3.1 · pytesseract | ENG072 OCR 派送目標(`_ocr_env_python()` 找它;`VIA_OCR_DISPATCH=1` 強制) |
| `via_vrn_312`:paddleocr 3.7.0 · torch · pymupdf · pdfplumber · reportlab;**無 easyocr** | 雙引擎階梯的 easyocr 段走 paddle 境 |
| `via_vap_312`:**pyarrow 半拆**(dist 名單缺)、seaborn 缺 | `via-envtools` 會列 REPAIR/INSTALL;裝是他的手 |
| `via_core` 14 件白名單境 | 批498 ⑤:永不排裝非白名單件 |
| `via_vdf`(38 件,py3.12,numpy 1.26.4)= 登錄 profile;`via_vdf_312` 未登錄(advisory) | **哪一境是 VDF 正境=操作員決定**(見三-U) |
| MIGRATION_REQUIRED:camelot_311 · paddle_311 · vif_aio · vif_core · vmt_pm | EnvManager 的事,本系統只讀不搬 |
| `paddleocr 3.x` 不吃 2.x 參數(`show_log` / `use_gpu` / `use_angle_cls`) | ENG082 `install_paddle_compat()` 已剝(批493 900 秒根因) |

---

## 三 · 還掛著的事

| 代號 | 事 | 卡在哪 |
|------|----|-------|
| **A** | 姊妹倉 `tonykuni/VIA-VDF-VRN` 同步 | 工具層權限(聊天授權 ≠ 工具授權)。 |
| **D** | 批416 F2 逐家投信 PCF 端點查實 | 需網路 + 同意閘;**閘由操作員自己設**。 |
| **G** | VRN_MDL 數量 300 vs 294 | 同一把尺再量,先記不判。 |
| **I** | VDF SSOT 化 | 冊 + census 對冊比在;`_repo_` 副本庫(P)哪本是正本要冊講。 |
| **P** | `vdf_tw_market_repo_a7752b3` 等副本庫與正庫並存 | 三副本病;`via-census -Hygiene` 只數不刪;刪=他的手。 |
| **R** | ENG072 起手 140 秒靜默(GLE 探 7 個 OCR 後端) | 後端健康已入邏輯庫(BROKEN/OK 24h);GLE 探測本身仍未快取。 |
| **S** | 資料家第二步:parquet 本體 + duckdb VIEW 匯出/接點 | `via-datahome catalog/plan/link` 在;要不要把 31 處散落件 link 進鏡根=他決定。 |
| **T** | `via-vrnuni` 官方名冊 CSV(`tw_listings` → code/name/yf_ticker/industry) | 小橋,未做。 |
| **U** | **VDF 正境:`via_vdf`(登錄,py3.12)還是 `via_vdf_312`(實為 3.13.7,未登錄)** | 治理問題,不是技術問題;工具冊目前路由到 `via_vdf_312`。他一句話定案後改冊。 |
| **V** | via_vap_312 pyarrow 半拆 / seaborn 缺;Tesseract `chi_tra`、easyocr 模型檔 | 全是「裝」——`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`,他的手。 |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件要用新次序重抽~~ | **已結(批503)**:64/64 抽齊,候OCR 0;最後一件 57 頁深底簡報反白 + psm 11 讀出 124 字。 |
| **X** | 容器 ENG072 ⑤ 空夾誠實 rc2 | 容器舊紅(v0116 基線同紅);操作員機器上未見紅。 |
| **Y** | 「Table … does not exist」現在是 NODATA 不是 RED | 若他機器上該表本應存在(冊上有)而燈是 NODATA,那是缺料燈點對了、料真的缺——去查 `via-census -Tables`。 |

---

## 四 · 紀律(每條都付過代價)

1. 先查再造 / 先量再改;判錯的紅燈和假綠一樣傷。
2. 缺件 ≠ 缺料 ≠ 壞掉 ≠ **閘未開**(批498 起四態:ABSENT / NODATA / RED / GATED)。
3. 只增不減 · 正本零觸碰(`references/intake/` 不編輯)· 尾版律(引擎改=新版號檔;無版號檔如 `sitecustomize.py`/JSON 冊才就地改)· Zero-Hydra · 零 CDN · 零彈窗。
4. 同意閘(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` / 金鑰)**一律操作員自己設,我不代設**;`Set-VIAGateDefaults`/`setdefault` 只在未設時給預設。
5. 零 force push · 不 `Stop-Process` · 不 `Remove-Item`/`conda remove`/`pip uninstall` 環境 · `--approve-remove` 只在明令下 · 裝套件=他的手(`--approve` + 閘)。
6. **加速器與網路工具只認 VeritasCeleritas / VeritasAegisNexus**(批494 令);737/740 留作橋。via_core 白名單境永不排裝非白名單件。
7. 資料:parquet 存、duckdb 管、家在 `via_database`;搬=link 不複製;刪=他的手;`census --hygiene` 永無 apply。
8. `VIA_Reports/*` 不入 git;**容器空沙盒再生的冊/頁不 commit**(VDFArchitecture 冊、VDF/Vap 架構頁、可編輯模板)。
9. SSOT 正本 `VIA_Financial_Institution_SSOT_v0100.py` READ_ONLY 不改;台帳 `VIA_AutoCode_Registry_v0100.json` indent=1,衝突取聯集。
10. VDF 價格皆 adj;報告價是原始價;不可直接比。
11. 新引擎/工具=功能註冊只增不減(規格項、格子站、Register 指令、Deck 任務、Manager 正式名稱、台帳、交接)。
12. commit 訊息 `批NNN:…`;倉內產物不放模型識別字。我不 merge、不 approve PR。

---

## 五 · 一貼即用(操作員工作站)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-boot                          # ① 每家族應印「工具:Celeritas(lazy);AegisNexus(lazy)」+ 資料家 VIA_DB_*
via-envtools                      # ② 工具冊導入計畫(唯讀):看 [未路由]/[白名單留置]/[樞紐]/[風險];貼回來
via-firstpage -RetryFailed        # ③ 只重試上次 FAIL 的 8 件(非 OCR→驗證→輕 OCR→重 OCR→DPI 300~350;派送 via_paddle_311)
via-vrnlogic                      # ④ 邏輯庫現況(法/後端健康);跑完 ③ 應多出新法、後端有紀錄
via-vrnlogic sync-db              # ⑤ 邏輯因子政策入庫(vrn_extraction_logic / via_policy_factors)
via-census -Tables                # ⑥ 兩張新表應在 vdf_tw_market.duckdb 列出
via-ryg -Timeout 300              # ⑦ 五矩陣燈:紫=GATED(閘未開,不是壞);紅才是要修的
# 你決定要裝時才跑(裝前 freeze 存證;我不代設閘):
# $env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve
```
