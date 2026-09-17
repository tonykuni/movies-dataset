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


## 一-l · 批509 · 你貼的實錄(via-envrecover 不存在 · via-vcgc v0103 · RunGate RED「必要庫缺」其實是 SRE module mismatch)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `via-envrecover` 不認得;`via-vcgc` 印 **v0103 批508**、律 27、lessons 14、227/227 登冊、中央冊 4734;台帳 **1041**;Grid 仍 v0301 | 遠端分支 = 我的 HEAD(5814e09e),遠端所有分支都沒有 v0103/律 27 → **你機器上有另一條 AI 並行線**(從批506b 分出,沒拉我的批507/508);你的 `git pull` 多半因分歧沒併(貼裡看不到那段) | 律 **L25 多 AI 交會律** + LL13;接手提示詞第 0 步=先對齊遠端;掉球 Z14;一貼即用:先把那條線 commit 到側枝並 push,再把工作分支對齊遠端 → 我出批510 併線(只增不減) |
| `via-rungate` RED:vdf/vrn 全站 0.2s `assert _sre.MAGIC == MAGIC, "SRE module mismatch"`,卻判「必要庫缺:duckdb,pandas,numpy,pyarrow」並開補庫令 | **判錯的紅燈**:家族境 python 連 `import re` 都不行=解譯器壞(標準庫錯配),補庫是錯藥;第一次 via-vcgc 還是 RunGate GREEN,之後才壞=中間有東西動了境或環境變數 | RunGate **v0102**:先探解譯器,-E/-S/-I 三試分病因(環境變數 PYTHONHOME/PYTHONPATH · site 層 · venv 本體),存證 pyvenv.cfg 與現值;RED 理由=解譯器壞(不列缺庫);補庫 SKIP;不探庫不跑站;次步=診斷+重建境(候裁);十二檢 12/12 + LL12 |
| 同病會傳到工具冊/復原 | v0107 探針失敗會把整境當 UNKNOWN/缺件 | MDL135 **v0108**:探針帶 SRE/MAGIC/encodings → 境 ENV_BROKEN_INTERP · 件 INTERP_BROKEN · 只出 REBUILD_ENV 候裁段(印 Remove-Item/uv venv/lock 三行;永不自跑,--approve-remove 亦不跑=境刪除是你的手);㊷ 四十二檢 42/42 |
| 啟動層快取套變數 | `sitecustomize` 會把 ACCEL_ACTIVATION 快取 applied 裡所有大寫鍵設進 env——若哪天快取帶了 PYTHONHOME/PYTHONPATH,子行程家族境就是這個病 | 護欄:PYTHON*/PATH/VIRTUAL_ENV/CONDA_PREFIX 永不從快取套(就地改;無版號檔) |
| 掛著 | SRE 根因要你機器的三試結果才定;並行線要你推側枝才能併 | Z14 / Z15 |

### 一貼即用(批509;三段:① 保住並行線並對齊 ② 診斷解譯器 ③ 復原計畫)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 30; git log --oneline -3; git branch --show-current                     # ① 先量:哪些檔是那條線的
git switch -c local/parallel-b508; git add -A; git commit -m "本機並行線快照(VCGC v0103/Register v0200/律 27;未併)"; git push -u origin local/parallel-b508
git switch -C claude/via-envmanager-governance-7cls8h origin/claude/via-envmanager-governance-7cls8h                  # 工作分支對齊遠端(那條線已在側枝,零遺失)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
$env:PYTHONHOME; $env:PYTHONPATH                                                                                     # ② 診斷:這兩個值直接貼回
Get-Content C:\Users\tonyk\envs\via_vdf_312\pyvenv.cfg
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -c "import sys;print(sys.version)"
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -E -c "import re;print('E ok')"
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -S -c "import re;print('S ok')"
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -I -c "import re;print('I ok')"
via-rungate                       # v0102:印 [INTERP] 病因 + 三試;次步不再叫你 pip install
via-envrecover                    # ③ 復原計畫(唯讀;解譯器壞境列 REBUILD_ENV 候裁行)
via-vcgc                          # 二段:環境復原燈
```


## 一-m · 批510 · 你問「沒有 OCR 引擎嗎??」(矩陣 vrn_firstpage TIMEOUT 600 · 螢幕停著 PPP「OCR 引擎載入失敗…paddle_static」)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `[VIA_PDFPlumberPlusEngine] OCR 引擎載入失敗,掃描頁將標記為 NO_OCR:RuntimeError: Engine 'paddle_static…` 停在「引擎最後一行」280 秒 | 那是**道二 PPP 收容件自己的 paddle 載入器**(paddleocr 2.x API 對不上你機器的 3.x),失敗一次記 BROKEN 24h 跳過;**不是沒有 OCR 引擎**:tesseract 直道(chi_tra+chi_sim+eng;批469 裝、批503 讀出 57 頁反白簡報 124 字)在做工,easyocr 要模型檔,paddle 走 via_paddle_311 車道。「最後一行」只是螢幕上最後印的那行,OCR 在跑時不印字 | LL14;答在本段 |
| 矩陣 `vrn_firstpage TIMEOUT 600.23`;你上次 `-RetryFailed` 也是 OCR_BUDGET 404/257/1138/328s | 燒時間的是 **16 件 PARTIAL 每跑都重燒整條階梯**:邏輯庫 lookup 只認 SUCCESS=HIT、FAIL=FAIL_HIT,PARTIAL 一律 None → 16 × 階梯(tesseract→easyocr→paddle 車道→HQ)≫ 600s | ENG082 **v0109** +PARTIAL_HIT(產物在且 TTL 內不重燒;⑳ 二十檢 20/20);ENG072 **v0126** 印 `[LOGIC_PARTIAL_HIT]`、卡片自舊產物重建、跑完印「部分命中 N」;`-RetryFailed` 涵蓋 PARTIAL(印 `[RETRY_PARTIAL]`);㊺ 四十五檢 |
| 你的樹還是 Grid v0301、台帳 1041 | 批509 的對齊區塊還沒跑(那條並行線還在你機器上跑 PANORAMA/policy_append/registry_sync) | 先跑批509 ① 保住並行線再對齊,否則這批也拉不到 |

### 一貼即用(批510;接在批509 ① 對齊之後)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
tesseract --version | Select-Object -First 1; tesseract --list-langs                    # OCR 引擎本體與語言包(chi_tra 要在)
via-vrnlogic                                                                          # 後端健康表:壞後端 = 24h 內跳過的那些
via-firstpage                                                                         # 例行跑:64 件應為 命中 48 · 部分命中 16(秒級)
via-ryg vrn -Timeout 600                                                              # vrn_firstpage 不該再 TIMEOUT
# 要重抽 16 件 PARTIAL(慢;每件走整條階梯):via-firstpage -RetryFailed
```


## 一-n · 批511 · 「vdf也加進來整合去重」+ 你貼的實錄(側枝已推 · tesseract 3 語 · via-firstpage 48/16 · via-ryg vrn GREEN 10)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `git branch --show-current` = **main**(8071a062 = origin/main + 本線 c93ad32e 的本機合併);136 檔未推的並行線 → 側枝 `local/parallel-b508-09151416`(7cc9031f)已推;工作分支已對齊本線 | 你機器一直在 main 上跑,不是本分支;並行線 = panorama-v0103(VCGC v0102/v0103、RunGate v0102、Bus v0123–v0125、ENG072 v0126/v0127、ENG073 v0125、ENG074 v0108、VDF ENG057/063/064/066/078 新版、launchers/Invoke-VIA-Panorama、律 L24–L27、lessons LL11–LL14、元件冊 4734)+ `.via_envmanager/` 163 MB 執行期狀態 | **併線**:`git merge` 側枝,8 個衝突照 L25 解——撞名四檔(Register v0200/ENG072 v0126/RunGate v0102/MDL149 v0102)留並行線內容,本線改動移到更高版號並帶上對方功能:**Register v0201**(+via-envrecover/via-panorama)、**ENG072 v0128**(並行 v0127 夾具 + PARTIAL_HIT;45/45,連容器舊紅 ⑤ 都綠了)、**RunGate v0103**(並行假綠修 + 解譯器探針;12/12)、**MDL149 v0104**(並行 registry-sync/panorama + 復原段;14/14);律冊聯集 29 律 19 lessons(並行線 L24–L27→L26–L29、LL11–LL14→LL15–LL18,orig_id 保留);`.via_envmanager/` 不入倉(.gitignore;側枝保有) |
| 併入後新增 734 件:374 件與倉內 byte 同(git blob 同 sha)、48 件互為孿生、312 件獨有 | 「整合去重」= 只刪 byte 同且路徑/檔名未被引用者 | 刪 45(VeritasPulse_v14 15 · VDF_final 13 · VAP 6 · taiwan_revenue 4 · output 2 · 帶 (2)/(3) 的副本 5);留 377(路徑或檔名被引用);獨有 312 一律留;報告 `docs/VIA_RepoHygiene_B511.md/.json` |
| 並行線引擎在併線樹上自測 | Bus v0125 46/46 · ENG073 v0125 36/36 · ENG074 v0108 19/19 · VDF ENG064 v0111 9/9 · ENG078 v0108 29/29 · ENG066 v0102 8/8 · ENG063 v0105 9/9 · ENG057 v0101 6/6 | 全綠;VCGC v0104 `registry-sync --apply`:活元件 4749 · 新 16 · 變更 430 · 退役 1 |
| 並行線 VCGC ⑩ 釘死兩串固定字(「操作員最後一棒」「bounded matrix 已 38/38 GREEN」)——那份 handover 沒進倉,⑩ 在任何人的樹上都紅 | 判錯的紅燈 | v0104 ⑩ 改結構判準:八段真的嵌了尾版交接本文(來源名 + 最後一個 ## 標題降級後在頁裡) |
| `tesseract v5.3.3` · chi_sim/chi_tra/eng;`via-vrnlogic` 64 件 PARTIAL 16 · SUCCESS 48;壞後端 無 | OCR 引擎在、語言包在 | 答了「沒有 OCR 引擎嗎」:有三條,那行是道二 PPP 的載入器 |
| `via-firstpage`(批509 樹):命中 48,16 件 PARTIAL **全是數位 PDF DUAL_ZONES**,合計秒級;`via-ryg vrn -Timeout 600`:vrn_firstpage **GREEN 30.89s**,vrn 10 GREEN · vrn_markdown NODATA(缺料) | **批510 的歸因錯了**:600s TIMEOUT 不是 PARTIAL 重燒 OCR,是並行線 panorama 自己的 vrn_firstpage 跑法;PARTIAL_HIT 仍有效(少做 16 次非 OCR 重抽) | Z18 記錯;LL14 文字下批修 |

沒做(誠實):`new modules engines/*`(另線引擎收容件,檔名帶 (2)/(3))只去重未入 intake 冊上(Z17);並行線 `via-panorama` 的 policy_append/registry_sync 會自動寫律冊與元件冊——併線後冊已聯集,它再跑可能重複追加 → **先不要跑 via-panorama**,批512 對表後放行(Z19);SRE 三試(Z15)仍等你貼。

### 一貼即用(批511)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h                 # 併線後的樹(含你那條線 + vdf 新版)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0201
via-vrnlogic sync-db              # 律 29 + lessons 19 入六本庫
via-vcgc                          # 唯一對接口:元件冊 4749 · 二段環境復原燈
via-rungate                       # 並行線預設:vdf,vrn 各 3 站有界;v0103 會印 [INTERP] 解譯器病因(貼回)
via-ryg vdf,vrn -Timeout 600      # 並行線預設 profile=test(有界);production 用 -Full
via-firstpage                     # 應為 命中 48 · 部分命中 16(秒級)
$env:PYTHONHOME; $env:PYTHONPATH; Get-Content C:\Users\tonyk\envs\via_vdf_312\pyvenv.cfg   # Z15 診斷,一起貼
```


## 一-o · 批512 · 「要用的閘就打開 類似參數功能引擎就整合優化」+ Z15 診斷實錄(PYTHONHOME 空 · PYTHONPATH=bootstrap · venv=C:\Python313 3.13.7)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `$env:PYTHONHOME` 空;`$env:PYTHONPATH` 只有 bootstrap;`via_vdf_312\pyvenv.cfg`:home=C:\Python313、3.13.7、`python -m venv` 建的 | 環境變數層清白;venv 是標準 venv,不是 uv | 三試(-E/-S/-I)你沒跑到,但 RunGate 自己的 `-c` 探針已證明:**-c 在倉根 import re 過**,**站以檔案起跑必炸**(vdf/vrn/vap 全站 0.2s SRE module mismatch);而匯流排在同一 via_vap_312 跑 vap 引擎正常(pyarrow 半拆、pandas 缺是真的缺) → 病在「站的子行程環境/cwd 層」,不是 venv 本體 |
| 你的樹還是批509(Register v0200、Grid v0302、Bus v0122、ENG072 v0125) | 批510/511 沒拉;`git pull --ff-only` 那行沒跑 | 這批區塊第一行還是 pull |
| RunGate 與匯流排各寫一套子行程環境 | 兩處=Hydra(L30) | **RunGate v0104**:站環境改用匯流排 `child_env()`(只寫一處)、cwd 改匯流排慣例暫存夾(批477 那課)、站 FAIL 印 **where**(traceback 最內層 File 路徑=哪一份 re/_compiler.py)、解譯器探針加「引擎夾當 cwd」試 + `re.__file__` 對 base_prefix(不在 base 下=STDLIB_SHADOW 印路徑)、庫探針本身炸=探針失敗不是缺庫(不再開補庫令)、`--approve-install` 過同意閘(L07);十五檢 15/15 |
| 「要用的閘就打開」 | 操作員授權:一貼即用可直接列 `$env:VIA_NET_CONSENT='YES'` 與 `--approve-install`(你貼=你的手);AI 端仍不自設 | L07 加 note;安裝仍過 L19(RunGate GREEN)——RunGate RED 的根因是解譯器,裝庫治不了,所以次序是:診斷 → 修解譯器層 → RunGate → 補庫 |
| 「類似參數功能引擎就整合優化」 | 立 **L30 相似整合律**;批511 v0103 併線切片把 10 個既有函式複製了一份(自測仍綠看不出)→ LL21 | v0104 從並行 v0102 乾淨重建;Z20 列整合候選(VCGC panorama vs recover、new modules engines 副本、UI 再生器) |

沒做(誠實):SRE 根因仍要你機器的 where 路徑才定(v0104 會印);`via-panorama` 仍先不要跑(Z19)。

### 一貼即用(批512;閘照你的令直接列)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0201
via-rungate --family vdf                                                       # v0104:看 [INTERP] re=… 與每站 where: 那行
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe "functional modules\VDF\engine\vdf_input_matrix_v0100.py" --selftest 2>&1 | Select-Object -First 14   # 完整 traceback
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -c "import re,sys;print(re.__file__);print(sys.path)"
Test-Path C:\Python313\python313.zip; Get-ChildItem C:\Python313 -Filter *.zip
git ls-files --others "functional modules\VDF\engine" "functional modules\VRN" "functional modules\VAP\engine" | Where-Object { $_ -match '\.py$' } | Select-Object -First 20   # 未追蹤的 .py=遮蔽嫌疑
# where 指到 C:\Python313\Lib 以外的 re → 那個檔/夾就是遮蔽,刪掉(你的手)再 via-rungate
# where 指到 C:\Python313\Lib\re 本身 → venv 本體錯配,重建(你的手):
#   Remove-Item -Recurse -Force C:\Users\tonyk\envs\via_vdf_312; C:\Python313\python.exe -m venv C:\Users\tonyk\envs\via_vdf_312
#   $env:VIA_NET_CONSENT='YES'; via-rungate --family vdf --approve-install      # 補庫道(不受 L19;閘照你的令)
```


## 一-p · 批513 · 「未來所有引擎會因為不同需求彈性調配嫁接,interface 合約自適應式 connect sync 功能要強大完善」+ 你貼的診斷(re 從 C:\Python313\Lib 載、無 zip、無未追蹤 .py)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `via-rungate` 仍印 Grid v0302、Register v0200、無 [INTERP] 行 | 你的樹卡在**批508**(RunGate v0101);批509–512 全沒拉,`git pull --ff-only` 那行沒生效(多半是本機發佈頁被改動擋住,你沒貼那段) | Z23;這批區塊改 `git stash` + `git pull --ff-only` + `git stash list`,並要求貼 pull 輸出 |
| `-c` 模式 `re.__file__` = C:\Python313\Lib\re;sys.path 正常;無 python313.zip;引擎夾無未追蹤 .py | `-c` 過、以檔案起跑炸,環境變數/venv 本體/遮蔽檔三個嫌疑都排除 → 剩「站的子行程層」;RunGate v0104 的 where 行會直接印出是哪一份 re/_compiler.py | 拉到 v0104 再跑一次就有答案;手動 traceback 的路徑改對:`vdf_input_matrix_v0100.py` 在 `functional modules\VDF\`(不在 engine\) |
| 新令:彈性嫁接 + 自適應合約 + connect/sync | 冊裡已有三件同題:MDL054 靜態合約(TOOL-041)、via_iface_autosync 執行期自湊(TOOL-089)、主控台冊=匯流排真正執行的綁定合約 → L30:不另起第四套,在冊的擁有者 MDL054 上加**綁定合約層** | **MDL054 v0102**:`sync`(冊 id→引擎 glob/verb/params × 尾版引擎 AST 旗標:VERB_DRIFT/PARAM_DRIFT/ENGINE_ABSENT/VERSION_BUMP/未暴露;`--apply` 只增 contract+contract_history,尾版一出合約自動追)· `connect --need`(嫁接候選只列 argv)· `graft --item --engine`(換引擎前驗旗標相容;`--apply` 只增候選,engine.glob 換不換=冊主)· `status`;八檢 8/8;律 **L31** |
| 真跑 `sync`(唯讀) | 44 項綁定:OK 40 · DRIFT 4:vdf/tw_revenue_codes(VDF_ENG063_MonthlyRevenue_v0105.py:PARAM_DRIFT:冊 params 旗標不在引擎裡 codes→--ticker,codes→--tickers); vrn/vrn_fourpoint(VRN_ENG080_FourPointDigest_v0105.py:PARAM_DRIFT:冊 params 旗標不在引擎裡 codes→--tickers); vrn/vrn_pdfplus(VIA_PDFPlumberPlusEngine.py:PARAM_DRIFT:冊 params 旗標不在引擎裡 dir→--dir); vrn/vrn_unified(VIA_VRN_UnifiedReportEngine_v0100.py:VERB_DRIFT:冊 verb 旗標不在引擎裡 --selftest) | 這就是「合約追碼」第一次量到的漂移;要不要 `--apply` 入冊、要不要修引擎旗標=你定 |
| 登冊 | Register v0202 `via-iface`(別名 合約;-Dry/-Apply/-Need/-Family/-Item/-Engine/-Dir)· Deck v0143 `iface_sync`(釘 66)· Manager v0129 · Grid v0307 +站 · 台帳 1048 | 七處 |

沒做(誠實):執行期 connect/sync(模組對模組欄位自湊)仍是 via_iface_autosync 那站,尚未與綁定層接線(Z21 ②);I/O 封包採用率未量(Z21 ③);`_inbox_to_classify` 六個同名標準庫檔候裁(Z22)。

### 一貼即用(批513)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b513 工作站樹快照(發佈頁等)"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 這四行的輸出貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 應為 v0202
via-rungate --family vdf                                                       # v0104:[INTERP] re=… 與每站 where: 行
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe "functional modules\VDF\vdf_input_matrix_v0100.py" --selftest 2>&1 | Select-Object -First 14
via-iface sync                                                                 # 綁定合約:44 項 DRIFT 列出;要入冊再 via-iface sync -Apply
via-iface connect -Need 首頁,ocr -Family vrn                                    # 嫁接候選(只列)
```

---

## 一-q · 批514 · 「將中央管理系統不足的部分補上」+ 你貼的實錄([INTERP] STDLIB_MISMATCH · PYTHONHOME=…\uv\python\cpython-3.12 · 手動 venv 直跑 13/13 · connect need ['首頁 ocr'] 命中 0)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `via-rungate --family vdf`(v0104):`[INTERP] STDLIB_MISMATCH … -E 即好 · PYTHONHOME=C:\Users\tonyk\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none`;同視窗手動 `via_vdf_312\Scripts\python.exe vdf_input_matrix --selftest` 13/13 | **Z15 根因定案**:跑閘的那個 python 行程帶著 PYTHONHOME 指到 uv 的 3.12(母殼/via_core 啟動/profile 帶進來;側枝 .via_envmanager/env_report.json 也記到同一值 + VIRTUAL_ENV=via_core),家族境 3.13 venv 子行程繼承後載 3.12 標準庫 → `_sre.MAGIC` 不合;`-E` 即好=環境變數層;手動直跑過=那個殼當下沒帶。四輪(批509–513)都在子行程/cwd/遮蔽檔層打轉=LL22 | **律 L32 子行程環境衛生**:PYTHONHOME 永不傳給子行程,三處同律撤除——bootstrap `sitecustomize` 起跑撤(每支 VIA python 都生效)· 匯流排 **v0126** `child_env`(47/47)· RunGate **v0105** interp/probe/station(17/17;`[ENV]` 行 + `rep.host` + 次步講根治=你的手);撤了什麼記 `VIA_PYTHONHOME_SCRUBBED`;Register v0203 載入時母殼帶 PYTHONHOME 就印黃 |
| `via-iface connect -Need 首頁,ocr` → need `['首頁 ocr']` 命中 0 | PowerShell 把 `首頁,ocr` 拆成陣列,Register 用空白合回 | MDL054 **v0103** `split_need()` 逗號/空白/分號/全形逗號/頓號皆可(9/9)+ Register v0203 `-Need` 以逗號合回 |
| 你上傳五件「中央管理系統」(主控台 VIA-SYS-MGR-001 · 詞彙引擎 VIA-GOV-ENG-001 · 下行控制 VIA-SYS-MGR-003 · 檔案優先序 VIA-SYS-ENG-003 · 同名整併 ps1) | md5 與 `new modules engines/` 內 8 個 `(1)/(2)/(3)/(4)` 副本 **byte 全同**(批511 已列候歸位);冊上零登錄(Register/Deck/Grid/Manager/VCGC 皆無)、各自寫死根與輸出、變更類動作無統一閘=「不足」的實體 | 歸位一份 `supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/`(原名零觸碰:套件內以檔名互呼;`MANIFEST_b514.json` md5 冊)、8 副本刪(`docs/VIA_RepoHygiene_B514`);擁有者 **CGC_MDL150 v0100**(status/plan/console/engine/router/downward/samename;工作夾 `VIA_Reports\central_governance\`;預設 dry-run;`--commit/--probe/--token/-Commit` 只在你明給才傳;子行程=匯流排 child_env;8/8);登冊七處:Register v0203 六令(`via-cgfamily/via-cgconsole/via-cgengine/via-cgrouter/via-cgdownward/via-samename`;別名 中央治理家族/中央主控台/詞彙引擎/優先路由/下行控制/同名整併)· Deck v0144 `cg_family_status/cg_router`(釘 68)· Manager v0130 · Grid v0308 +站 · VCGC **v0105** 十一段(15/15;registry-sync --apply 活元件 4799 新 50)· 台帳 1049 |
| 容器內 dry-run:詞彙引擎 selftest PASS(0.1s)· 路由器 GREEN · 主控台 AMBER(13 閘 WARN 6 FAIL 0;registry 夾 704 檔 11.8s) | 五件離線可跑;主控台快照落 `<root>\output\SYS` + `<root>\configs`(.gitignore 收 `output/`、`configs/*.preview.json`、`system_parameters.json`;`--commit` 台帳可入倉) | 掉球 Z24:深併候裁(URN 發碼 vs VCGC 元件冊 · 同名整併 vs L23 · 路由器 vs MDL054/catalog · 下行能力冊 vs Deck · 詞彙引擎 v0100 vs CGC_MDL001 v0401) |

沒做(誠實):根治(殼層/profile/via_core Activate/使用者環境變數的 PYTHONHOME)是你的手,程式不動殼層;`via-cgdownward`/`via-samename` 要 pwsh 7,容器只驗 argv 閘律;各對只留一處(Z24)下一批;`_inbox_to_classify` 六檔證據已列(Z22)候你裁。

### 一貼即用(批514)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b514 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行輸出貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 應為 v0203;若印黃「母殼帶 PYTHONHOME」= 根因就在這個視窗
$env:PYTHONHOME; [Environment]::GetEnvironmentVariable('PYTHONHOME','User'); [Environment]::GetEnvironmentVariable('PYTHONHOME','Machine'); Select-String -Path $PROFILE -Pattern 'PYTHONHOME' -ErrorAction SilentlyContinue; Get-Content C:\Users\tonyk\envs\via_core\pyvenv.cfg -ErrorAction SilentlyContinue   # Z15 根因四問,貼回
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue   # 你的手:本窗先拿掉(v0105 站已免疫;這行讓手動跑也乾淨)
via-rungate --family vdf                                   # v0105:[ENV] 行 + 真燈;只有「必要庫缺」才會列補庫令
$env:VIA_NET_CONSENT='YES'; via-rungate --family vdf --approve-install   # 只在上一行列出必要庫缺時跑(你的手;批512 令「要用的閘就打開」)
via-iface connect -Need 首頁,ocr -Family vrn                # v0103:need 應為 ['首頁','ocr']
via-cgfamily plan; via-cgrouter; via-cgengine; via-cgconsole; via-cgfamily   # 中央治理家族 dry-run(via-cgdownward/via-samename 要 pwsh 7,先看 plan)
via-vcgc                                                    # v0105:第十一段 中央治理家族
```

---

## 一-r · 批515 · 你貼的批514 實錄 + 新令「將中央功能 VIA VDF VRN VETF 完成;VDF 擷取五個額外資料試跑即可;VRN 實測 TAB3;VETF 改名 VATETF 應用端;VDF 基金只抓主動式台股 ETF;TEST DEBUG…ACTIVATE;以 VIA 為中央管理全部 SSOT 化唯一接觸口」

| 量到(批514 區塊) | 判讀 | 做了 |
|---|------|------|
| `via-rungate --family vdf`(v0105):`[ENV] 母行程 PYTHONHOME=…uv\cpython-3.12 → 子行程已撤` · `[INTERP] OK 3.13.7 re=C:\Python313\Lib\re` · 8 站 OK · **GREEN vdf 必要庫 4/4 引擎 8/8** | Z15 至閘結案:SRE mismatch 消失,站免疫;殼層仍帶 PYTHONHOME(根治=你的手,Z25) | Z15 劃線;`via-vcgc` 印 RunGate GREEN→**BLOCKED_UNITEST** 是因為只跑了 vdf(L19 要 VDF+VRN 兩族 24h 內綠)→ 這批區塊加 `via-rungate --family vrn` |
| `via-iface connect -Need 首頁,ocr` → need `['首頁','ocr']` 命中 10 | v0103 寬收成立 | — |
| `via-cgrouter` AMBER 進佇列 124 擋下 43,195 簽章異常 3 · **891 s** | OneDrive 樹 43k 檔逐檔讀 magic bytes(佔位檔觸發下載) | Z29(排除規則/預算) |
| `via-cgconsole` **RED rc=1 192 s**,尾行只有別家引擎的 SyntaxWarning | 擁有者把 stderr 尾行當結果,RED 理由沒印(LL25) | **MDL150 v0101**:stdout 優先;status 列 Gate FAIL/WARN code/title/detail + 重複家族/解析失敗數;貼回即知(Z28) |
| `via-cgfamily` 五成員全 **MD5_DRIFT** | 不是檔案被改:Windows git autocrlf 簽出 LF→CRLF(LL24) | MDL150 v0101 md5 內容正規化(CRLF→LF、去 BOM);10/10 |
| `via-vcgc` v0105:律 32 · lessons 23 · Deck 68 · 格子 219 · Register 118 · 中央冊 4799/4800 缺 1 · 家族 PARTIAL | 台在位;缺 1=你樹上一件未同步元件(下次 `via-vcgc registry-sync --apply` 即補) | — |
| Grid v0308:396 `SyntaxWarning invalid escape '\V'` 每次載入都印 | 文件字串非 raw | **Grid v0309** raw 文件字串(編譯零警告) |

**新令怎麼落(每條=律或件,不是口號)**

| 令 | 落點 |
|---|---|
| VDF 擷取五個額外資料試跑即可 | 五額外=冊上核心台股日交易/籌碼之外五組:`tw_revenue_codes`(月營收 ENG063)· `fin_statements`(三大報表 ENG082)· `etf_holdings_daily`(主動 ETF 持股 ENG078)· `macro_fred`(FRED ENG074)· `global_universe`(國際 11 類 ENG066)→ **Register v0204 `via-vdf-extra5`**(別名 五額外;匯流排 `matrix --apply-family vdf --ids … --profile run`;閘未開自動退 `-Test` 有界)· Deck v0145 `vdf_extra5`(釘 69)· Manager v0131;真抓=你的手(Z27) |
| VRN 實測 TAB3:DATE FILENAME FIXED CONTENTS(修正識別 LAYOUT 去空格去斷行 分類別 自動換行 標註類型/次分類/頁數)/ SUMMARY | 擁有者兩處(L30):**ENG082 v0110 `fix_contents()`**(repair_text → 中文字任一側空白去除 → 段內斷行接回 → 類型/次分類(冊提示優先:首頁·標題帶/右資訊區/本文、財報頁·科目、指標、全文;無提示關鍵字自判 財務/評等/風險/展望/標題/本文)→ 每 40 字自動換行 → 段首【類型·次分類·p頁】;21/21)+ **MDL139 v0105** `vrn_tabs()` 每份報告把 sidecar 分區 + 財報頁列 + 指標列 + ENG075 全文 md 交給它,TAB3 欄序 **DATE · FILENAME · FIXED CONTENTS · SUMMARY**(舊欄照留;SUMMARY 空退四點文摘;欄 pre-wrap);新動詞 `via-console tab3 [--n 3]` 印前三列給你貼(Z26);自審:①②⑥ 從批505 起就紅(判準釘著 fin_statements=PLANNED;LL26)→ 判準追上,15/15 |
| VETF 改名 VATETF;直接抓 VDF 擷取的資料庫來用,他是應用端 | **律 L34**;`via-vatetf`/`主動ETF應用` = 同一函式雙名(只增不減);契約 `VIA_Panorama_Contract` +`names` 鍵;VCGC v0106 十段/頁標題 VATETF(舊名 VETF) |
| VDF 基金只抓主動式台股 ETF 其他基金不抓 | **律 L35**(ENG077 A 碼律宇宙 + ENG078 持股;被動 ETF 只到價格;其他基金不抓不建表) |
| TEST DEBUG OPTIMIZE TEST DEBUG CONSOLIDATE TEST DEBUG USER-TEST DEBUG ACTIVATE TEST DEBUG | **律 L33 工序律**;本批照走:ENG082/MDL139/MDL150 各 測→修→整併→測,操作員實測=這批區塊 |
| 以 VIA 為中央管理 全部 SSOT 化 唯一接觸口 | L20 已立;冊外寫死路徑件盤點=Z30(中央治理家族五件、VETF adapter、ENG075 OUTDIR) |

沒做(誠實):五額外真抓與 TAB3 真報告實測都要你的手貼回;殼層 PYTHONHOME 我不動;`via-cgdownward`/`via-samename` 仍未在工作站跑過(pwsh 7);Z29/Z30 下一批。

### 一貼即用(批515)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b515 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 應為 v0204
via-rungate --family vrn                                   # 兩族 24h 內都綠 → via-vcgc 才會 INSTALL_OK(L19)
via-cgfamily                                               # v0101:MD5 應全 OK;console RED 的 [FAIL]/[WARN] 行貼回(Z28)
via-console tab3 --n 3                                     # TAB3 = DATE / FILENAME / FIXED CONTENTS / SUMMARY 前三列貼回(Z26;0 份=先 via-vrnval)
$env:VIA_NET_CONSENT='YES'; via-vdf-extra5                  # 五額外資料試跑(真抓=你的手;閘沒開會自動只跑 -Test 有界;Z27)
via-vcgc                                                    # v0106:VATETF 名 · 律 35 / lessons 26 · 十一段
```

---

## 一-s · 批516 · 你貼的批515 實錄 + 令「除錯成功後才 Veritas Taiwan Monthly Revenue Analysis VTMRA · TA-LIB 確認測試無誤」

| 量到 | 判讀 | 做了 |
|---|------|------|
| `via-rungate --family vrn`:[INTERP] OK 3.13.7 · 7/8 OK · **VRN_MDL001_Converter_v0121 TIMEOUT 180s** → RED | 轉檔器自測=渲染 A4 200/600 DPI 點陣頁 ×9 檢,容器 82.7s、OneDrive 工作站更慢;不是壞(Z31) | Grid **v0310** 該站逾時 180→600(判真);候瘦身 |
| 同一輪 `vrn_report_digest_v0114` 尾行 `HTTP Error 404 quoteSummary 3661.TWO` | 自測宣稱零網路,卻經 Summarizer 尾版 yfinance 取價**真的出網**;RunGate 已撤同意閘仍出網=取價器沒看閘(L07 破口) | **Summarizer v0102** `AdjCloseFetcher.fetch` 加閘(VIA_SELFTEST=1 或 VIA_NET_CONSENT≠YES → GATED)+ **digest v0115** 自測起手 VIA_SELFTEST=1;容器帶 CONSENT=YES 跑 31/31 零 404(Z32 結) |
| `via-cgfamily` **TypeError: object of type 'int' has no len()** | 你機器上主控台快照的 duplicate_groups 是數不是表(LL28) | **MDL150 v0102** `_count()` 型別寬收(11/11) |
| `via-console tab3` 報告 0 · 修正識別 ABSENT,而 `via-vcgc` 邏輯庫 64 件、資料家 OK | 主控台開的是寫死主路徑 `MEGA/vdf_tw_market.duckdb`,ENG073 早已「資料家優先」寫進 VIA_DATA_HOME 那本=「庫就在那裡,是我找不到那個庫」第三次(LL27) | **MDL139 v0106** `mega_db()` 資料家優先(與 ENG073 同序)+ status 預設主庫走它 + tab3 印 `[庫解析]` 路徑/表在不在;容器實跑 71 份(16/16) |
| `via-vdf-extra5`:GREEN 2(月營收/主動ETF持股)· GATED 3 | macro_fred/fin_statements/global_universe 是**雙閘**(NET+SCRAPE;FRED 另要 FRED_API_KEY);你只開了 NET | 區塊改雙閘 + `-Ids` 只補跑三件(Z27) |
| `via-vcgc` v0106:律 35 · Deck 70 · Register 119 · RunGate RED → BLOCKED_UNITEST | 一切如實;RED 只因 Converter TIMEOUT | 上列修法後重跑 vrn 應綠 → 兩族 24h 內綠才 INSTALL_OK |
| SyntaxWarning 每次載入印(MDL139:15 `\.`、VesBridge:23 `\(`) | 文件字串非 raw | MDL139 v0106 / **VesBridge v0104** raw(編譯零警告) |

**新令(除錯成功後才做的部分,本批已備好,等你的實錄判「除錯成功」)**

| 令 | 落點 |
|---|---|
| VTMRA = Veritas Taiwan Monthly Revenue Analysis | **律 L36**:家族名不是第四套引擎;成員 ENG063/075/069/076 · TWREV v2.7 · CrossGroupPhase v030 · TA-Lib;**CGC_MDL152 VtmraGate**(`via-vtmra`;別名 月營收分析):家族境 vdf 真跑七成員自測 → `VIA_Reports\vtmra\VTMRA_latest.json/.html`;判定 全 OK=GREEN · 只有 TA-Lib 未裝=YELLOW · 任一 FAIL/TIMEOUT=RED;7/7;容器實跑:eng063/075/076 OK · twrev OK(工作家從收容包種入)· revphase OK · **eng069 FAIL(容器無庫;Z33)** · talib ABSENT |
| TA-LIB 確認測試無誤 | **CGC_MDL151 TaLibGate**(`via-talib`;別名 技術指標):import/版本/函式數 + SMA5/EMA5/RSI14/MACD hist/BBANDS mid **對手算**;未裝=ABSENT 印補庫令不代裝(L07/L19;6/6);工具冊 `VIA_ToolRoster_SSOT` TA-Lib 入 via_vdf_312/via_vap_312(LOW;0.5+ wheel 內含 C 庫);Deck v0147 `vtmra_tests/talib_probe`(釘 72)· Manager v0133(VTMRA 子系統名)· Grid v0310 兩站 · VCGC **v0107** 四段 VTMRA 行(16/16;元件冊 4836) |

沒做(誠實):除錯是否「成功」由你下一輪實錄判(vrn 轉綠、cgfamily 有理由、tab3 有列);TA-Lib 未裝(Z34 你的手);ENG069 工作站結果未見(Z33);Converter 自測瘦身(Z31)下一批。

### 一貼即用(批516)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b516 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 應為 v0205
via-rungate --family vrn                                   # 轉檔器站逾時 600、摘要器自測不出網 → 應 GREEN;尾行不得再有 HTTP 404
via-cgfamily                                               # v0102:不再 TypeError;console RED 的 [FAIL]/[WARN] 行貼回(Z28)
via-console tab3 --n 3                                     # v0106:[庫解析] 行講看了哪本庫;0 份就是那本沒 VRN 表 → 先 via-vrnval
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'; via-vdf-extra5 -Ids macro_fred,fin_statements,global_universe   # 三件雙閘(你的手;FRED 另要 FRED_API_KEY)
via-vtmra                                                  # VTMRA 家族測試閘(七成員;零網路)→ 矩陣貼回(eng069 列尤其要看;Z33)
via-talib                                                  # TA-Lib 閘:ABSENT=未裝 → 你的手:& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -m pip install TA-Lib ;裝後再 via-talib 應 OK 五數值檢
via-vcgc                                                    # v0107:VTMRA 行 · 律 36 / lessons 28
```

---

## 一-t · 批517 · 你問「VDF 擷取前有無先檢視庫現況/定義範圍/批次不重複/為何五個交易日那麼慢/母系統在哪/資料庫在哪/有更新嗎/討論更新到邏輯庫」+ 實錄 + 令「VRN 實測 NLP 工具要導入」

**答(照碼講,不照印象講)**

| 問 | 答 |
|---|---|
| 擷取前有無先檢視庫現況、定義範圍? | 有,而且是律(L37):價量增量 ENG054 v0101 起「依庫內各標的 MAX(date) 只抓缺口(最後交易日已達=零請求;缺口起點=MAX(date)−3 日重疊,upsert 冪等)」;史深 ENG064 「checkpoint {段:[done]} 已成永不重抓;每批 anti-join INSERT 只補缺鍵;中斷零損失」;持股 ENG078 `--gap-mode plan` 先列缺口。BATCH FETCHING 不重複=每批落盤+checkpoint+鍵去重,已是現況 |
| 為何之前多個五天交易日那麼慢? | 慢不在重抓、在**道的單位**(LL29):ENG054/064 抓取單位是**每檔一請求**(yf_history 0.54s/檔 × 1,800 檔 ≈ 16 分;chart 直連更慢),缺口 5 日或 500 日成本一樣。短缺口該走**一日一請求的全市場道**(TWSE MI_INDEX/TPEX 日行情),目前沒有這條道=Z35 候建 |
| 母系統在哪? | `C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`(你 cd 進去的那份;main 已併 PR #35 = 本線全部);短令一律 `Set-Location` 那裡再點源 Register |
| 資料庫在哪? | 資料家 `C:\Users\tonyk\VIA System\via_database`(VCGC 資料家 OK;啟動層把 VIA_DATA_HOME/VIA_DB_* 放進 env);舊主路徑 `functional modules\VDF\output_hub\mega\vdf_tw_market.duckdb` 是退路。ENG073/ENG069(v0106 起)/MDL139(v0106 起)都先找資料家 |
| 有更新嗎? | 五額外實錄 GREEN 2(月營收 ENG063 · 主動 ETF 持股 ENG078)=有寫;要看到「更新到哪一天」:`via-console status` 印每表 rows/max 日;`via-census` 對冊 |
| 討論內容更新到邏輯庫 | 政策庫=`VIA_Policy_Laws_SSOT`(本批 +L37/LL29–LL31),`via-vrnlogic sync-db` 把律攤平入 `via_policy_factors`(VCGC「政策因子」列數會增);VRN 擷取邏輯庫(ENG082)照舊 |

| 量到(批516 區塊) | 判讀 | 做了 |
|---|------|------|
| `via-vtmra` RED:eng063/075/076/twrev/revphase OK · **eng069 FAIL rc=1** · talib ABSENT | ENG069 `DB_TW` 寫死主路徑(LL30;第四次「庫就在那裡」),資料家那本沒被找;容器同病印「交集 0/0」 | **ENG069 v0106** resolve_db 資料家優先 + 表在零列=誠實缺料 rc2 |
| `via-vcgc`:RunGate **GREEN → BLOCKED_UNITEST**(vdf 早上綠、vrn 晚上綠) | VCGC 只讀 RUNGATE_latest(最後一跑只有 vrn)=判錯的紅燈 | **VCGC v0108** 每個必驗族取 24h 內最新一跑(RUNGATE_*.json 史);兩族各自綠即 INSTALL_OK(17/17) |
| 五額外(雙閘後)`GREEN 2 · NODATA 1` | 三件雙閘裡一件無料(哪件被截掉;下次貼整段) | — |
| 中央治理家族:MD5 全 OK;console RED(理由仍未貼) | v0102 已能列 Gate 理由 | 貼回 `via-cgfamily` 全段(Z28) |

**令「VRN 實測 NLP 工具要導入」**:NLP v1.8.0 **批421 早已收容**(intake 頂層 109 檔)、正主 **SUP_MDL744 NLPApplicationHub**(`via-nlp`;尾版語意取 v1.8.0;11 檢綠)——差的是「導入 VRN 實測鏈」與「摘要服務」:① 冊 +`vrn_nlp`(綁正主 `demo`;`via-ryg vrn` 實測就會跑它)② **SUP_MDL744 v0102** `summarize()`=v1.8.0 證據型摘要(每點帶 source_span/sha256;12/12)③ **MDL139 v0107** TAB3 +「NLP 摘要」欄,SUMMARY 空時退 NLP 點(17/17)④ v1.6.1 收容 `_b283`(整理結果 md 一併);61MB 討論重建 JSON 不入倉(Z36 你裁落點)⑤ v1.8.0 自家 115 測試容器全過(2 skip)。

### 一貼即用(批517)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b517 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0205
via-vcgc                                                    # v0108:RunGate 應 INSTALL_OK(vdf+vrn 各自 24h 內綠)· 律 37 / lessons 31
via-vtmra                                                  # eng069 v0106:OK 或誠實缺料(rc2)→ 列貼回
via-nlp demo                                               # 正主 v0102:表格/版面/摘要 3 點(零網路)
via-console tab3 --n 3                                     # v0107:多一欄 NLP 摘要;[庫解析] 行講看了哪本庫
via-ryg vrn                                                # VRN 實測(有界):新項 vrn_nlp 在列
via-console status | Select-String "tw_daily_prices|tw_monthly_revenue|holdings_daily|max"   # 更新到哪一天
via-vrnlogic sync-db                                       # 討論內容(律 L37/LL29–LL31)攤平入 via_policy_factors
via-cgfamily                                               # 整段貼回(console RED 的 [FAIL]/[WARN] 行;Z28)
```

---

## 一-u · 批518 · 你貼回批517 區塊結果(via-ryg vrn RED 3 · status|Select-String 印空 · sync-db OK · via-cgfamily 全段:console RED 的理由)

| 量到(你貼的) | 判讀 | 做了 |
|---|------|------|
| `via-ryg vrn` 45 項 · GREEN 9 · PLAN 33 · **RED 3**(哪 3 項被截掉) | 矩陣頁有、終端沒貼全;紅項因由與尾段都在 ENGINE_BUS_latest.json | 不重跑:`via-bus tails`(早有的動詞)印紅項因由+尾段 → 貼回(Z38) |
| `via-console status \| Select-String "tw_daily_prices\|…\|max"` **印出空** | status 終端只印一句「庫表 51」,每表 rows/max 只落 CONSOLE_latest.json;我在一-t 寫「印每表 max 日」是沒看 print 段就講(LL32;判錯的綠燈) | **MDL139 v0108** `tables_lines()`:status 印「更新到哪一天」——帶日期欄的表逐行 列/最新/滯後(容器:analyst_estimates 2026-09-14 滯後 1 · etf_stats_daily 2026-09-15 …;`etf_book` 最新 1150908 是民國日字串 → 滯後 ? 誠實);18/18 |
| `via-vrnlogic sync-db` OK 6 庫 · via_policy_factors 474 列 | 律 L37/LL29–LL31 已攤平入資料家 | — |
| `via-cgfamily`(v0102):五件 md5 OK;**console RED**:`[FAIL] G17 NO_DEPENDENCY_CYCLE 3 個循環` + `[WARN] G03 1049 組/2702 份 · G04 10 檔無法解析 · G16 1457 呼叫無 URN · G18 爆炸半徑 2858 · G22 未探針`;router OK queued=124;downward/samename ABSENT | 快照只存 URN(files/duplicate_*/unresolved 全是計數),RED 對不回檔名 → 容器在行程內驅動主控台(dry-run)對回:**四圈(你機器 3)= 退役件兩圈(batch186 WorkOps lifecycle↔ENG126;batch180 VRN_ENG008↔ENG027)+ 收容件一圈(OmniFormat b245 引擎↔Invoke-Veritas-VOFIE.ps1)+ 活樹一圈:舊部署啟動器 `Invoke-VRN-Activate-And-Validate.ps1` 仍呼叫批180 已退役的 VRN_ENG008**(啟動器沒隨引擎退) | **MDL150 v0103** `cycles` 動詞(URN→檔名→區:活樹/新模組/存檔/收容/退役;活樹圈才是債;→ CYCLES_latest.json;status/plan 併讀;12/12)· 啟動器 **git mv 退役 wave8**(可回滾;引用僅存舊部署清單)→ 複跑 **活樹 0 → GREEN** · **VCGC v0109** 十一段一行「G17 循環判讀」(18/18)· 律 **L38** 治理閘處置律 |
| G03 1049 組重複 | 主控台把 .json/.md/.html 與 VIA_Reports 也算;容器只算 git 追蹤程式檔=325 組/494 份;快照側候選 128 件裡 122 件被 VAP_Param_Registry src/AllDocuments 清單/asset_scan/Invoke-VAP-* 以檔名引用 → L23 不刪(SCOPE_COPY 是 VAP 惰性存檔,VAP_ENG006 早列 INERT) | 刪 6 件雙 sha 尾綴副本(byte 同、零引用;`docs/VIA_RepoHygiene_B518`);其餘由你裁(Z39) |
| G04 10 檔無法解析 | 退役/收容件的原始語法錯(batch180/183、GroupIndex intake、new modules bundle)+ VeritasPulse_v14 的空 `__init__.py`(合法 Python;工具把空檔當無法解析)→ 零觸碰;容器 3.11 多 12 件 f-string 反斜線=3.12 以下語法差,你的 3.13 不算 | 記錄(不是債) |
| G16 / G18 / G22 | 外部函式庫呼叫本無 URN;爆炸半徑只擋「自動覆寫」而我們從不 --commit;探針會動態載入模組頂層=你的手 | 設計上 WARN,不擋(L38 ④) |

**沒做/等你**:vrn 的 3 個 RED(`via-bus tails` 貼回)· Z33 eng069 v0106 在你機器 `via-vtmra` 列 · Z34 TA-Lib 裝=你的手 · Z37 中央冊缺 1 · Z39 G03 餘量由你裁。

### 一貼即用(批518)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b518 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0205(本批不動)
via-bus tails                                              # 上次 via-ryg vrn 的 3 個 RED:因由 + 引擎尾段(貼回;不必重跑矩陣)
via-console status                                         # v0108:多了「更新到哪一天」每表 MAX(date) 行(不再需要 Select-String)
via-cgfamily cycles                                        # v0103:G17 循環對回檔名+分區(1-3 分;活樹圈才是債)→ 圈列貼回
via-cgfamily                                               # 主控台行下多一行「G17 循環判讀」;仍 RED 的理由都在 [FAIL]/[WARN] 行
via-vcgc                                                   # v0109:十一段多一行循環判讀 · 律 38 / lessons 33
via-vtmra                                                  # (批517 未貼)eng069 v0106:OK 或誠實缺料 rc2 → 列貼回
```

---

## 一-v · 批519 · 三上傳(VETF seal 2 · VRN_BatchFourEngine · VIA_TALib_OneEngine)+ 令「全景式分析 解決所有問題 小數量實測 規劃好所有 U/I 自小一點更專業 中央自適應連結對接 U/I WORKFLOW 圖可重整引擎 對接口合約自適應 自動跳出實測結果 VIA/VRN/VDF 庫分類歸納/VATETF/VTMRA 真測除錯 介面 HTML 對接規格 更新母資料夾/資料庫/GITHUB」+ 批518 區塊實錄

**你貼回(批518 區塊)→ 判讀**

| 量到 | 判讀 | 做了 |
|---|---|---|
| `via-cgfamily cycles`:掃 12,891 檔 · 3 圈 · **活樹 0 → GREEN**(收容 1 · 退役 2) | 與容器同(工作站少一圈=退役件間的那圈沒被它算到;無妨) | Z28 收 |
| `via-cgfamily`:console 仍 RED(G17 FAIL 3 + 五 WARN)但多了一行 `[GREEN] G17 循環判讀 3 圈 活樹 0` | 工具 RED ≠ 活樹 RED(L38);其餘 WARN 設計上不擋 | — |
| `via-vcgc` v0109:律 38/lessons 33 · 因子 484 · RunGate GREEN→INSTALL_OK · 多矩陣 RED 3 · 中央冊 4847/4848 缺 1 | RED 3 還是沒具名(`via-bus tails` 沒貼到);缺 1=Z37 | 區塊再放 `via-bus tails` |
| `via-vtmra`:**eng069 FAIL rc=1**(v0106;其餘 OK;talib ABSENT) | 工作站庫在=走全檢,全檢把「市場檔數>1000/交集>0」當程式檢 → 資料側不足就 rc=1(LL36);容器無庫走誠實缺料二檢=判不到 | **ENG069 v0107**:資料側 YELLOW 不計 FAIL;資料在位卻誠實停 rc2=資料側;例外才 FAIL(印類別+訊息) |

**三上傳(先對 md5 再收;LL34)**

| 件 | 對照 | 處置 |
|---|---|---|
| `VETF_FINAL_SEAL_20260829_013330_2.zip`(126 檔 7.9MB;含 React 網站原始碼) | SHA256SUMS 與 b242 收容件逐行**全同** | 不再收;VATETF 現役=冊上 `vdf_vetf_consensus` + `via-vetf`(v0206 找庫改資料家優先;LL35);React/npm 不掛線(Z41) |
| `VRN_BatchFourEngine_v0100.py` | md5 與 b245/b383 兩處**全同**(第三次) | 不再收;它要的 four_engine_orchestrator 套件不在倉(Z40);功能對回正主:docx→md=ENG075(markitdown)· 批次=匯流排 · 對帳=ENG074 |
| `VIA_TALib_OneEngine_v0100.zip`(10 檔;v1.0.0=退役件 ENG003 的整合升級版;TA-Lib Abstract API 全函數;DuckDB 唯讀;VAP Catalog) | 倉內零同名/同 md5 → **新件** | 收容 `functional modules/TALib/references/intake/VIA_TALib_OneEngine_v0100_b519/`(md5 冊)+ 正主橋 **VDF_ENG083_TALibOneBridge**(`via-taone` probe/selftest-engine/catalog/run;庫解析律;TA-Lib 缺=ABSENT 印 pip 令=你的手;7/7)+ VTMRA 家族 **v0101 八員**(+talib_one 軟缺席)+ 冊項 `vdf_talib_one` |

**U/I 與工作流(正主 CGC_MDL153 WorkflowComposer;12/12;律 L39/L40)**

- `via-workflow catalog`:46 個引擎積木=冊上三家族項(id/verb/params/net/outputs)。
- `via-workflow validate|run <id>`:冊 `VIA_Workflow_SSOT_v0100.json` 種子八條(vrn_report_chain / vrn_logic_nlp / vdf_daily_update / vatetf_pipeline / vtmra_family / vdf_db_governance / vdf_talib_features / vap_charts);合約自適應逐邊 OK/DEFAULT/NEED_INPUT/GATED/ABSENT;執行只經匯流排 `call --item --apply --profile`(閘不變)。**容器小數量實測:`run vrn_logic_nlp --profile test` → GREEN 3/3(ENG082 21 檢 · 財務邏輯 9 檢 · NLP 12 檢真跑);`validate vatetf_pipeline` → GATED(兩個觸網項誠實)**。
- `via-workflow ui-contract --apply`:掃 ui_support 66 頁 + 產生器引用 → `VIA_UI_Contract_v0100.json`(擁有者=頁名詞幹相扣的產生器尾版;家族;在/新鮮/大小/再生短令;規格:零 CDN/SNAPSHOT-LIVE/零彈窗/一頁一產生器/樣式 tokens 12.5px 緊湊)。
- `via-workflow db-summary`:VDF 庫分類歸納 51 表 9 類(容器實錄:價量 GREEN 滯後 1 · 籌碼 YELLOW 4 · ETF GREEN 0 · 宏觀 **RED 76**(cross_macro 2026-07-01)· 國際 YELLOW 5 · 營收/VRN/治理 NODATA(無日期欄)· 其他 RED 45)。
- `via-workflow page --publish`:工作流重組台頁(左 目錄積木 · 中 工作流+SVG 鏈圖+驗合約+執行短令+JSON 匯出 · 右 實測面板自動展開(工作流/五矩陣/RunGate/VTMRA/主控台/循環判讀)+ 庫分類 + U/I 對接表)→ 入倉 `ui_support/VIA_UI_WorkflowComposer_v0100.html`(零 CDN;手機單欄)。
- **VCGC v0110 十二段「U/I 對接與工作流」**:中央自適應連結(頁在=file:// 連、不在=ABSENT)+ 工作流最新一跑 + 庫分類每類一燈(19/19)。
- 登冊:Grid v0312(+2 站)· Deck v0148(+talib_one/workflow_page/ui_contract;釘 75)· Manager v0134(總控頁再生;契約測試 19 OK)· Register v0206(`via-taone`/技術指標引擎 · `via-workflow`/工作流)。

**沒做/等你**:vrn 的 3 個 RED(`via-bus tails`)· eng069 v0107 在你機器再看(仍 FAIL 就貼尾段;Z33)· TA-Lib 裝=你的手(Z34 有釘版 pip 令)· Z37 中央冊缺 1 · Z40 four-engine 套件 · Z41 VETF Standalone 頁是否入 ui_support · Z42 頁面按下即跑(要 Deck 端點,等你點頭)。

### 一貼即用(批519)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b519 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0206
via-bus tails                                              # vrn 的 3 個 RED 因由+尾段(這次貼)
via-vtmra                                                  # v0101 八員;eng069 v0107 應 OK/YELLOW;仍 FAIL → 貼:& "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe" ".\functional modules\VDF\engine\VDF_ENG069_RevenueConsensusAnalysis_v0107.py" --selftest 2>&1 | Select-Object -Last 25
via-taone                                                  # TA-Lib OneEngine 橋 probe(vdf 境):ABSENT 會印釘版 pip 令(裝=你的手;裝後 via-taone selftest-engine)
via-workflow ui-contract --apply                           # U/I 對接契約(你機器的頁/新鮮度)
via-workflow db-summary                                    # VDF 庫分類歸納(每類一燈;哪類該補)
via-workflow run vrn_logic_nlp --profile test              # 小數量實測(零網路;應 GREEN 3/3)
via-workflow run vdf_db_governance --profile run           # 三庫盤點→覆蓋→缺口→架構矩陣(零網路;真跑)
via-workflow page --publish; via-open ".\supportive modules\ui_support\VIA_UI_WorkflowComposer_v0100.html"   # 重組台(實測面板自動帶最新一跑)
via-vcgc page --publish                                    # v0110 十二段(頁面自適應連結)
via-vetf                                                   # VATETF 應用端(v0206 資料家優先找 ActiveTWETF/vdf_tw_market)→ 審計行貼回
```

---

## 一-w · 批520 · 你貼回批519 區塊 + 令「TA-LIB 只取用股票的 ADJ 價格;成交量值要有扣除當沖跟沒扣除;計算指標一律使用扣除後」

**你貼回 → 判讀 → 做了**

| 量到 | 判讀 | 做了 |
|---|---|---|
| `via-vtmra` eng069 **v0107 仍 FAIL**:② 每檔唯一最新月 | 工作站 `monthly_revenue_analysis` 同 (code,ym) 多列(多來源/重跑殘留),latest 子查詢只鎖 ym → JOIN 放大;容器空庫判不到(LL38) | **ENG069 v0108**:QUALIFY ROW_NUMBER 去重 + 印重複列數(庫零觸碰)+ 合成庫自測 ⑦(容器證 join 不放大) |
| `via-taone` ABSENT,印的 pip 令 `numpy>=1.26,<2.0`(沒引號) | PowerShell 會把 `>` 當導向=貼了會炸(Z34) | **ENG083 v0101** PINS 逐項引號 |
| `via-vetf`:資料家找到 ActiveTWETF/vdf_tw_market ✓ → adapter **FAIL_CLOSED「Need a DataFrame with at least one column」** | adapter 只認自己的欄名別名;VDF 正本 holdings_daily 叫 portfolio_date/etf_ticker/holding_ticker/weight_pct、價表 ticker 帶 .TW → 每列被丟成 0 筆 → 寫候選空表炸;**對接口沒合約**(LL37) | **VDF_ENG085 VatetfBridge**(`via-vetf` v0207 → 它):家族境建暫存輸入庫(每檔 ETF asof 前最新日持股、代碼去尾綴、欄改 adapter 別名;價 45 日;consensus_latest 依 source 分 FactSet/其他)→ adapter candidate 沙盒 → audit 摘要;`status` 印庫解析/合約缺欄/最新 audit;8/8 |
| ui-contract 71 頁 · db-summary 9 類 · `run vrn_logic_nlp` GREEN 3/3 · `run vdf_db_governance` GREEN 4/4 · 重組台/VCGC 頁發佈 | 工作流真跑在你機器成立 | — |

**令 → 律 L41(TA-Lib 量值政策)**:①價只用 adj(tw_prices_adj;缺則因子還原)②量值四欄同留(raw/ex_daytrade × volume/turnover)③指標一律以扣當沖量值算(display_mode/indicator_volume_bases=ex_daytrade)④無當沖日=NULL 不冒充 ⑤扣法 ex_volume=成交股數−當沖股數、ex_turnover=成交金額−(買+賣)/2 ⑥源:ENG060 價 · ENG057 值 · ENG055 L15 當沖(TWSE/TPEX;WAF 擋=誠實缺)。
落實:`functional modules/TALib/VIA_TALib_OneEngine.via.config.json`(收容件 config 副本+覆寫;原檔零觸碰)+ `VIA_TALib_Policy_v0100.json`;**ENG083 v0101** `run` 改 `--query`(adj ⟕ 成交金額 ⟕ 當沖;表缺哪張就少哪欄)+ `check-data`(三表覆蓋;容器:價 575,295 列 · 值 2,660 列 · 當沖 ABSENT → YELLOW 誠實)+ `policy`;冊 +`tw_daytrade_stock`(ENG055 L15;觸網)· 工作流 `vdf_talib_features` = 當沖→架構→TA-Lib。
登冊:Grid v0313 · Deck v0149(+vatetf_app;76)· Manager v0135 · Register v0207 · VCGC v0111(批號改讀政策庫)。
**批520a(容器真跑補測)**:`via-vetf run` 先盤點持股表,缺=NODATA 誠實(ENG085 v0101);`via-taone run` 引擎錯誤 JSON 在 stderr、「輸入資料為空」=NODATA 資料側(ENG083 v0102);容器:`--codes 1240` 鏈通到 TA-Lib 匯入=ABSENT 誠實。

### 一貼即用(批520)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b520 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0207
via-vtmra                                                  # eng069 v0108 應 OK(去重);仍 FAIL → 貼那一列
via-vetf status                                            # ENG085:庫解析/表列數/合約缺欄/最新 audit(唯讀)
via-vetf                                                   # = run:暫存輸入庫 → adapter candidate → audit 摘要(貼回 [對接]/[audit] 行)
via-taone check-data                                       # 價/值/當沖三表覆蓋(當沖表在不在;L41)
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'; via-bus one tw_daytrade_stock   # 個股當沖(ENG055 L15;TWSE/TPEX;你開閘)→ 抓不到=誠實 FAIL 貼回
via-taone check-data                                       # 再看覆蓋 %
# TA-Lib 裝(你的手;vdf 境 numpy 2.x 要先降):
& "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe" -m pip install "numpy>=1.26,<2.0" "pandas>=2.1,<2.2" "TA-Lib>=0.4.28,<0.5"
via-taone selftest-engine                                  # 裝後:360 筆合成 OHLCV 真跑 → OK 帶 coverage
via-taone run --since 2026-06-01 --codes 2330,2317         # 小數量實測:adj 價 + 扣當沖量值算指標(當沖缺=量能 NULL 誠實)→ VIA_Reports\talib_one\RUN_*
via-vcgc page --publish                                    # v0111(批號讀政策庫)
```

---

## 一-x · 批521 · 你貼回批520 區塊 + VCGC 頁 + 令「全面性解決 TA-LIB 輸入為 VDF 產出的資料庫,未來輸出給 VAP 或其他專題繪圖;完成 VIA VRN VDF」+「CONSENSUS EPS SHOULD BE DILUTED EPS ONLY IN FACTSET CONSENSUS」

**你貼回 → 判讀 → 做了**

| 量到 | 判讀 | 做了 |
|---|---|---|
| `via-vtmra` YELLOW:eng069 **v0108 OK** | 去重生效(LL38 收) | — |
| `via-vetf` OK 40 筆(PASS 2 · REVIEW 38)但 **eps/forward_pe 覆蓋 0%** | 橋只餵目標價欄,adapter 的 EPS 碎片(period n/n1、fiscal_year、eps_mean)沒餵 → forward P/E 算不出;你令「共識 EPS 只用 FactSet 稀釋 EPS」 | **ENG085 v0102** 餵 EPS 碎片 → **v0103** 只有 `source LIKE '%factset%'` 的列給 eps(n=eps_fy0/n1=eps_fy1;`eps_basis=FACTSET_DILUTED_EPS`;cnyes estimateProfit feMean 年度均值),YAHOO/EXTERNAL 只給目標價不給 EPS;10/10 → **律 L43** |
| `via-taone` ABSENT;貼的 pip 令 `numpy<2` 在 **3.13 境編譯失敗**(clang/Meson) | via_vdf_312 其實是 Python 3.13 venv + numpy 2.x;收容件釘版(numpy<2)是舊境藥方 | **ENG083 v0103** `probe` 讀 python/numpy 版 → 依境印令:3.13 或 numpy 2 → `"TA-Lib>=0.6"`(wheel 內含 C 庫,**不降 numpy**;容器證 talib 0.8.0 + numpy 2.4.6 self-test PASS);舊境才印釘版 → **LL39**;`functional modules/TALib/VIA_TALib_requirements.via.txt` |
| `run --codes 2330,2317` 被併成一字串 | PowerShell 把逗號串當一個 arg | `split_codes`(逗號/空白/分號/全形逗號/頓號)→ **LL40** |
| `via-bus one tw_daytrade_stock` **RED**(TWSE rwd 非 JSON / TPEX 逾時);`check-data` 當沖表 ABSENT | rwd 端點有 WAF;openapi `TWTB4U` 在你機器可達(批517 資格清單走過) | **ENG055 v0110** L15 openapi 優先(鍵名子字串比對 Code/成交股數/買進/賣出;民國日轉西元;**無量欄=印鍵名貼回**)+ rwd/TPEX 備援;9/9;Z44 |
| VCGC 頁五矩陣 **3 紅**:`vrn_firstpage` TIMEOUT · `vrn_structdb` ㉞ · `vrn_finpages` ⑯ | ㉞/⑯ 是 Windows `\` vs `/` 路徑字串比對=**自測假紅**(LL41);firstpage 600s 不夠 OCR 派送 | **ENG073 v0126 / ENG074 v0109** `as_posix()` 比對(36/36 · 19/19);冊項 `vrn_firstpage.timeout=1500` + **Bus v0127** `call()` 讀冊項逾時(48/48) |
| 令「TA-LIB 輸入=VDF 庫 → 輸出給 VAP」 | 鏈要在容器整條證過才算 | **ENG083 v0103** `-c` 墊片載收容件(補 `json_default` bytes→str;零觸碰;LL42)+ `latest`(manifest 摘要/function_errors/L41 註)+ `vap`(每檔 parquet → VAP ONE:K 線 adj + 量基(扣當沖有料才用,缺=raw 誠實標)+ SMA20 雙軸 + RSI14;圖規過 ENG016 驗證)+ 引擎 YELLOW rc=2 認黃(LL43);16/16;冊項 `vdf_talib_vap`;工作流 `vdf_talib_features` 四站 |

**容器全鏈證(批521)**:`probe` OK(3.11/numpy 2.4.6/talib 0.8.0)→ `selftest-engine` OK coverage=1.0 rows=360 → `run --since 2026-08-01 --codes 1240` **YELLOW** 31 列 · 577 欄 · 覆蓋 0.93 · 函數錯誤 34 全是 `MissingActivityBasis`(容器無當沖表 → 量能函數 NULL,L41 不冒充)→ `latest` 印 parquet/csv 路徑 → `vap --codes 1240` **OK** 圖 3(`vap_one.svg/html`,量基 volume_raw 誠實標)。`via-vetf status` 容器 NODATA(holdings 缺)誠實;`validate vdf_talib_features` GATED(觸網項等你開閘)。

### 一貼即用(批521)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b521 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0207
via-taone probe                                            # vdf 境 python/numpy/talib(不裝);ABSENT 印的令已依境
& "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe" -m pip install "TA-Lib>=0.6"   # 你的手(wheel 內含 C 庫;不降 numpy;LL39)
via-taone selftest-engine                                  # 360 筆合成 OHLCV → OK coverage=1.0
via-taone run --since 2026-06-01 --codes 2330,2317         # adj 價+扣當沖量值;當沖表缺 → YELLOW(量能函數 NULL 誠實)
via-taone latest                                           # 列/檔/日期範圍/函數錯誤分類/parquet 路徑
via-taone vap                                              # 特徵 → VAP ONE:VIA_Reports\talib_one\vap\<code>\RUN_*\vap_one.html(貼回 [OK]/[FAIL] 行)
via-vetf                                                   # ENG085 v0103:FactSet 稀釋 EPS 專用 → 貼回 [audit] eps/forward_pe 覆蓋
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'; via-bus one tw_daytrade_stock   # ENG055 v0110 openapi 優先;印「鍵名」就整段貼回
via-taone check-data                                       # 當沖表覆蓋 %(有料後重跑 via-taone run → 量能函數應有值)
via-ryg vrn                                                # 三紅應消(㉞/⑯ 路徑比對;firstpage 逾時 1500s 冊定)
via-vcgc page --publish
```

---

## 一-y · 批522 · 你貼回批521 區塊 + 上傳 VIA_VRN_FirstPageEngine v0101 + 令「收尾;更新今天進度到母系統;掌握資料庫現況;HANDOVER REPORT IN DETAILS;因子庫/邏輯庫/參數庫/政策全更新;整理資料庫在哪;附件看能否修第一頁邏輯缺失;GITHUB SYNC ALL」

**你貼回 → 判讀 → 做了**

| 量到(批521 區塊) | 判讀 | 做了 |
|---|---|---|
| `pip install "TA-Lib>=0.6"` → **ta_lib-0.8.0-cp313 wheel 裝上**;`selftest-engine` OK coverage=1.0 rows=360;`run --since 2026-06-01 --codes 2330,2317` **YELLOW 148 列/577 欄/覆蓋 0.93**;`latest` 函數錯誤 68 全 MissingActivityBasis;`vap` **OK 2317/2330 各圖 3** | TA-Lib 全鏈在你機器成立(Z34 收);黃=當沖表缺(L41 不冒充) | — (等當沖量值進庫後重跑即綠) |
| `via-vetf` 印 **OK records 40** 但 adapter 尾段 `FileExistsError APPEND_ONLY_CONFLICT … asof=2026-09-15/manifest.json 已存在`;audit 仍 eps/forward_pe 0% | **假綠**:adapter 一字未寫,橋退回舊夾的 audit 當結果(LL44) | **ENG085 v0104**:每跑一夾 `VIA_Reports/vatetf/out/RUN_<ts>`(律 L44)· 只認本跑新產 audit · error_type=FAIL 帶因由;11/11 |
| `via-bus one tw_daytrade_stock` RED:`TWSE-openapi:無量值鍵(鍵=['Date','Code','Name','Suspension'])` · rwd/TPEX 安全導向 | openapi TWTB4U 是**標的冊**沒量值;兩交易所個股當沖頁對 python 客戶端 WAF(容器再證:swagger 都擋、TPEX 302 Security Redirect) | **ENG055 v0111** L15 三態:openapi=標的冊只計數 · rwd/TPEX 誠實候源 · **檔案收容道**(律 L45 只收不掛線):瀏覽器存 CSV/JSON → `functional modules/VDF/references/intake/daytrade_files/`(README 寫了兩個網址)或 `via-daytrade --from-file A,B --date`;表頭關鍵字對映/民國日/千分位/已收冊;10/10 |
| `via-ryg vrn`:structdb **GREEN** · finpages **GREEN**(批521 修對)· firstpage **RED** ㉙ 樞紐在但 OCR 道仍簡體 · ㉜ `OCR_RUN_FAIL(lane=via_paddle_311:FileNotFoundError)` · ㊷ `執行器無 JSON;rc=106;failed to locate pyvenv.cfg` | ㉙=vrn 境沒 **opencc**(ENG064 normalizer 靠它,缺=直通;LL46)· ㉜=車道 via_paddle_311 的 python 不在=**境壞**不是 OCR 壞 · ㊷=夾具 symlink 的是 venv 啟動器,離開 venv 夾就找不到 pyvenv.cfg(LL47) | **ENG072 v0129**:簡繁探針(樞紐三態:缺/在無轉換器→tag 印裝法/在能轉)· 車道境**預檢**(python/pyvenv.cfg/基底解譯器;壞=BROKEN+SKIP;律 L47)· 夾具改連 `sys._base_executable` · +㊻;46/46 |
| 上傳 `VIA_VRN_FirstPageEngine_2.py`(v0101 ALL-IN-ONE 八模組) | 收容(md5 d4cdaedf…;零觸碰);它的 SSOT loader 期望的區塊 VIA 正典沒有;券商/評等字典子字串撞詞;缺台灣本土券商 | **VRN_ENG086 FirstPageLogicBridge v0100**(正主橋):名冊改自 VDF `tw_listings`(唯讀)· 橋側防呆(券商詞界/評等線索詞/目標價旁四碼=代碼不算/多公司摘要不取)· 本土券商補冊 30 家 · 民國 7 碼 · `enrich`(ENG072 sidecar → `.logic86.json` append-only;律 L46)· `bench`(76 份真檔名)· `gap`;10/10 |

**容器實測(小數量,真資料)**:`via-fplogic bench` 76 份真檔名 → 代碼 **54/57**(3 漏=舊真值把年份 2026 當代碼,階梯拒收是對的)· 券商 **50/50** · 日期 64/75(真值日期另有來源);`via-fplogic enrich` 71 件 sidecar → 代碼法 FILE_BARE 46/BODY_BARE 5/NONE 14/BODY_SUFFIX 2/FILE_SUFFIX 1/SECTOR_FILE 3 · 檔名×首頁代碼一致 45/71 · 券商 41/71 · 評等 26/71 · 目標價 39/71(晨會/摘要類不取=誠實)。收容件八模組:接線 4(代碼階梯/券商評等/欄位驗證/互核)· 候 4(版面字級/隱藏格線表格要 chars 幾何;財務容差帶候接 ENG074/ENG080;NLPRepair 不疊床)。

**登冊**:冊項 `vrn_firstpage_logic`(ENG086 enrich)· `tw_daytrade_files`(ENG055 --from-file)· 工作流 `vrn_firstpage_logic_chain` / `vdf_daytrade_file_chain`(validate NEED_INPUT 誠實)· Grid v0314 · Deck v0150(釘 77)· Manager v0136(契約測試 19)· Register v0208 `via-fplogic`(首頁邏輯)/`via-daytrade`(當沖量值)· 律 **L44–L47** · 教訓 **LL44–LL49** · 邏輯庫 `VRN_ExtractionLogic_SSOT` +`firstpage_logic` 區塊 · 台帳 1058。
**庫要你的手才會更新**(容器碰不到你的庫):`via-vrnlogic sync-db`(邏輯庫/因子庫/政策庫入每本 duckdb)· `via-cgfamily`(參數庫 `configs/system_parameters.json`)· `via-census -Tables`(現況)。

### 一貼即用(批522)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b522 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0208
via-vetf                                                   # ENG085 v0104:每跑一夾 RUN_<ts>;貼回 [audit] coverage_pct(factset_eps_n/forward_pe_n)
via-fplogic status                                         # ENG086:收容件 md5/名冊 tw_listings/首頁 sidecar 件數
via-fplogic bench                                          # 76 份真檔名命中率(貼回第一行 + [漏] 行)
via-fplogic enrich                                         # ENG072 sidecar → VIA_Reports\first_page_logic\*.logic86.json(貼回第一行)
& "C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe" -m pip install opencc-python-reimplemented   # 你的手:㉙ 簡→繁(vrn 境;純 python)
via-rebuild --env via_paddle_311                           # 你的手:㉜/㊷ 車道境壞(python/pyvenv.cfg 缺);重建後 ↓
via-vrnlogic reset-backends
via-ryg vrn                                                # firstpage 三紅應消(㉙ 繁化 · ㉜ 境壞=SKIP 誠實 · ㊷ 夾具基底解譯器)
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'; via-daytrade   # 線上三源誠實;印 hint=照 README 用瀏覽器存 CSV
# via-daytrade --from-file "C:\Users\tonyk\Downloads\TWTB4U_20260912.csv" --date 2026-09-12   # 檔案收容道(存好 CSV 後)
via-taone check-data                                       # 當沖表覆蓋 → via-taone run --since 2026-06-01 --codes 2330,2317 → via-taone vap
via-vrnlogic sync-db                                       # 邏輯庫/因子庫/政策庫(L44–L47/LL44–LL49/firstpage_logic)入每本 duckdb
via-cgfamily                                               # 參數庫 configs\system_parameters.json + 治理快照
via-census -Tables                                         # 資料庫現況(貼回;對照交接「六」)
via-vcgc page --publish
```

---

## 一-z · 批534 · 接手 B533(另一 AI 的四份交接檔)+ 令「TAKE OVER TEST DEBUG OPTIMIZE TEST DEBUG CONSOLIDATE TEST DEBUG USER」+ 上傳 VIA_CodeChain_ALL_1.zip「導入」

**先對帳(L25 多 AI 交會律)**:`git fetch` → 遠端比本地多 **19 個 commit**(B526→B533,作者 Manus AI),ff-only 併入。他就地改寫了 `Register-VIA-Commands-v0208.ps1`(同名不同容),我批522 的 via-fplogic/via-daytrade 仍在=他有併不是覆蓋;往前出 **v0209**,不回頭改他的檔(LL53)。

**他宣稱 → 我在本境逐項重跑 → 真實結果**

| B533 宣稱 | 我的容器實測 | 判讀 |
|---|---|---|
| CGC157 唯一接觸口 18/18 GREEN | **18/18 GREEN**(但只認位置動詞 `selftest`;`--selftest` rc=2) | 真;動詞契約與全樹不一致 |
| CGC156 加速器控制面 23/23、roster 25 | **23/23 GREEN** | 真 |
| VRN_ENG087 NLP 橋 11/11 | **11/11**(同樣只認位置動詞) | 真 |
| VDF_ENG073 資料架構 9/9 · VDF_ENG087 市場清單 10/10 | **9/9 · 10/10**(`--selftest` 可) | 真 |
| VDF_ENG086 QuantGuard 8/8 | **rc=1 Traceback:`ModuleNotFoundError: No module named 'polars'`** | **他境的綠**;裝了 polars 1.44.2 後才 8/8(LL50) |
| 中央 dispatch 全路由 GREEN | **RED**(quantguard 那條 traceback) | 至少沒假綠;但缺件被判成 RED=假紅 |

**拆到四條根因(都在中央控制面,不在子系統)**

| 根因 | 症狀 | 修 |
|---|---|---|
| ① 派送不分家族境:`subprocess.run([sys.executable, ...])` | 中央用哪個 python 起、子系統就被迫用哪個境 → 工作站上 VRN 路由跑在非 vrn 境 → 缺件 → **母機三紅** | **CGC157 v0101**:每條路由走匯流排 `python_for(family)`(退路 `VIA_PY_<FAM>`),子行程環境走 `child_env`(PYTHONHOME 清洗)→ **律 L51** |
| ② 判讀只有 GREEN/RED | 本境缺 polars = RED(假紅);判錯的紅燈和假綠一樣傷 | v0101 **誠實四態**:ABSENT(缺件)/NODATA(缺料)/TIMEOUT/RED,總裁決 GREEN/YELLOW/RED → **律 L52** |
| ③ 版號釘死 | 命令冊釘 `v0208`、QuantGuard 釘 `v0100`:照尾版律出新版,中央永遠跑舊的還說 GREEN | v0101 全改 **newest-glob** → **律 L54** |
| ④ 動詞契約分歧 | 新引擎只認位置 `selftest`,全樹格子站/匯流排/Deck 用 `--selftest` | 五支引擎(CGC156/157、CGC155、VRN087、SUP_MDL866、VDF086)加**旗標=位置動詞等價轉換** → **律 L53** |

**另修**:`VDF_ENG086 v0101` 把 `import polars` 從模組頂搬進探針——缺 polars 印 ABSENT + pip 令(你的手,不代裝)、rc=3;新增 `probe` 動詞列 polars/numpy/duckdb/收容件在不在(LL51)。TA-Lib 三支橋在 B526 被直接刪除、沒進退役夾也沒冊 → 補退役冊 `docs/VIA_Retired_TALib_B534.json`(L50 禁復活,故不還原程式,只記可自 commit `fd51913f` 稽核取回;LL54)。

**再測(修完)**:CGC157 **21/21**(18+新三檢)· CGC156 23/23 · VRN087 11/11 · VDF086 8/8 · VDF087 10/10 · VDF073 9/9 · CGC155 rc0 · SUP_MDL866 rc0;`dispatch --family all` **GREEN 4/4**,且逐路由印出家族境 python 與實際版號(全部尾版:VRN087 v0101 / VDF086 v0101 / VDF087 v0101)。

**整併(CONSOLIDATE)**:B526–B533 的八支新引擎**一支都沒進格子站/Deck/Manager**(只進了 InputConsole 冊)→ 補齊:**Grid v0315**(+7 站,全部 `--selftest`;CGC154 是資料驗收閘不是自測站,不進格子避免假紅)· **Deck v0151**(+unique_entry/accel_control/quantguard/nlp_unified/func_acceptance;釘 77→**80**)· **Manager v0137**(5 正式名稱 + 5 引擎名;總控頁再生 80 項;契約測試 **19 passed**)· **Register v0209**(`via-central dispatch` 一令跑完三家族;控制面身分不再釘死 v0100)。

**收容**:`VIA_CodeChain_ALL_1.zip`(md5 f39ffbdd…)→ `supportive modules/references/intake/VIA_CodeChain_ALL_b534/` 39 檔逐檔 md5 冊;對倉內既有 `registry/vcg`:**8 檔不同、31 檔倉內沒有**(多 kno.lexicon/codechain/index/product/governance registry、versions/、kno_classifier 訓練集、ledger、兩份 SPEC、AutoCodeGenerator 與倉內 v0100 md5 不同)。**本批只收不接線**(正本零觸碰);要接哪一塊等你說。

### 一貼即用(批534)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 10; git stash push -m "b534 工作站樹快照"; git pull --ff-only origin claude/via-envmanager-governance-7cls8h; git stash list; git log --oneline -1   # 四行貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0209
via-quantguard probe                                       # polars/numpy/duckdb 在不在(缺=ABSENT 印裝法,不代裝)
& "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe" -m pip install "polars>=1.21,<2"   # 你的手(QuantGuard 唯一活動技術指標路徑靠它;容器證 1.44.2 → 8/8)
via-unique-check                                           # CGC157 v0101 閘:應 GREEN 21/21
via-central dispatch                                       # 批534 新令:三家族一次跑完(家族境 python·誠實四態)→ 貼回最後那幾行
via-central vrn -SelfTest ; via-central vdf -SelfTest ; via-central quantguard -SelfTest
via-ryg vrn                                                # 批522 三紅是否消(㉙ 要先裝 opencc;㉜/㊷ 要先 via-rebuild --env via_paddle_311)
via-vcgc page --publish
```

---

## 一-aa · 批535 · 令「整成一個 PowerShell 全包:進環境→全景式分析→AST 精準/彈性定位→列出所有問題類型與位置→不傷系統不生九頭龍下,能同時修的同時修、不能同時修的順序修→25 加速器→動態進度條→自動跳出多 TAB 矩陣報告(TAB1 給 AI 與我、內附 JSON/MD;TAB2 起逐項測試結果)→紅黃綠燈、分系統分範疇;所有 PY 檔加指令加速器;VDF 引擎加網路工具」+「授權自動修正測試無誤」

**交付兩件**

| 件 | 是什麼 |
|---|---|
| `VIA_B535_PANORAMA_ALL_IN_ONE.ps1` | 一貼式:進環境(切目錄/尾版命令冊/家族境 python)→ 25 加速器名冊(CGC_MDL156)→ 跑正主 → **Write-Progress 動態進度條**(解析引擎的 `@@PROGRESS|pct|msg`)→ 終端印紅黃綠總表 → **自動跳出多 TAB HTML**;`-Apply` 才寫檔,不加就是乾跑 |
| `CGC_MDL158_VIAPanoramaAuditRepair_v0100.py` | 全景稽核修復**正主**(一功能一主 L30):AST 精準定位七類問題 → 分類分系統紅黃綠 → 平行/順序修 → 多 TAB 報告 HTML/JSON/MD。自測 **13/13** |

**七類問題(AST 精準,彈性退路)**

| 類 | 處置 | 判準(避免假紅) |
|---|---|---|
| ACCEL 加速器橋缺席 | **自動修(平行)** | 無 `[VIA:ACCEL-BRIDGE]` 標記 |
| NET VDF 網路工具橋缺席 | **自動修(平行)** | VDF engine 夾內無 `[VIA:NET-BRIDGE]`;惰性載入=import 時零網路 |
| VERB 自測動詞契約不齊 | **自動修(順序)** | argparse 有 `selftest` 位置動詞但不吃 `--selftest`;**形狀不合就誠實 skip 不猜改** |
| HARDIMP 模組頂硬相依重庫 | 報位置 | 只算不在 try/探針內的重庫(polars/talib/paddle…);家族基底 pandas/numpy 不算 |
| PINVER 釘死版號 | 報位置 | **只有真的當路徑/執行目標用**才算;報告文字、docstring 不算 |
| SYSEXE 裸 sys.executable 派送 | 報位置 | **只有派到別支引擎**才算;自跑自己不算 |
| SYNTAX 語法錯 | 報位置 | compile 失敗;本器不猜改 |

**活樹律(新 L55)**:第一次掃描報 1426 項,**八成落在舊版本檔(v0101…v0136)與 `_sha…` 凍結副本**——那些不是活樹,對它們報紅就是假紅。加上「同 stem 只取尾版、凍結副本不算、收容件/退役夾/pycache/VIA_Reports/vcg 不掃」之後:**活樹 1576 檔 / 397 問題**,才是真正要處理的(LL55)。

**自動修三態(新 L56)**:純增量零行為變更且冪等 → 可同時修(以檔為單位平行,一檔一工人,互不交疊);動到 main/parse_args 入口 → 順序修;會改行為或需判斷 → 只報位置等令。每次修改前後都 `ast.parse`,失敗整檔回滾;語法本來就壞的檔**拒修**。

**本批實修結果**:加速器橋 **+125 檔**、VDF 網路工具橋 **+5 檔**,共 **127 檔改動、全部 compile 通過**;VERB 8 個目標形狀不合樣板 → 誠實 skip 列入報告(LL57)。覆蓋率:指令加速器橋、VDF 網路工具橋(逐檔數字見報告 TAB⑥)。

**登冊**:Grid v0316(+全景站)· Deck v0152(+panorama_audit;釘 81)· Manager v0138(正式名稱+引擎名;總控頁 81;契約測試 19 passed)· Register v0210(`via-panorama` / 別名 全景修復、`via-panorama-all` / 別名 全景一貼)· 冊項 `via_panorama_audit` · 工作流 `via_panorama_chain` · 律 L55/L56 · 教訓 LL55–LL57。

### 一貼即用(批535)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h
.\VIA_B535_PANORAMA_ALL_IN_ONE.ps1                  # 乾跑:先看問題(不寫檔)
.\VIA_B535_PANORAMA_ALL_IN_ONE.ps1 -Apply           # 實修 + 實測 + 自動跳出多 TAB 報告
# 或載入命令冊後用短令:
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0210
全景一貼 -Apply                                      # = via-panorama-all -Apply
全景修復 scan                                        # = via-panorama scan(只看問題)
```

報告在 `VIA_Reports\panorama_audit\PANORAMA_AUDIT_latest.html`(同夾另有 `.json` / `.md` 給 AI 直接吃)。

**本批自己踩到的九頭龍(已修,值得記)**:第一版把產物寫進 `VIA_Reports\panorama`,那是 L19 安裝核可閘在讀的檔名;schema 不同 → 那道閘把每種情境都判 BLOCKED_PANORAMA,VCGC 自測從 19/19 掉到 18/19。讓出名字改 `panorama_audit`,VCGC 回 19/19,並在稽核器自測 ⑬a 釘死不准再碰(LL59)。另外同一批兩次踩到 f-string 巢狀引號/括號在 Python 3.11 會炸——我的報告渲染器一次、別人 bundle 檔一次(兩處都修好,後者原本整支不能 import;LL58)。

---

## 一-ab · 批536 · 令「再同步修正一次,不必生成 PowerShell,自主完成全部並上傳」(+ 授權自動完成)

**先對帳**:遠端無他人更動(3ca5863f = 本地)。

**一、判準精準化(CGC_MDL158 v0101;15/15)**——批535 報的 267 項裡有一半是稽核器自己的誤報:

| 誤報型 | 為什麼是誤報 | 修法 |
|---|---|---|
| SYSEXE 2 件 | 兩件都是 `subprocess.run([sys.executable, Path(__file__)…])`=**引擎自測跑自己**,不是跨家族派送 | 自跑自己不算 → SYSEXE **真數 0** |
| PINVER 122 件 | 自測段/探針函式在暫存夾寫的假命令冊(`Register-VIA-Commands-v0174.ps1`)、假引擎名(`X_ENG001_A_v0100.py`) | 所在函式是自測/探針就不算 → PINVER 151→**23** |
| 候選夾/打包副本 | `candidates/`、`bundle/`、`launchers/panorama_tests/` 不是活樹 | 併入非活樹 |

**二、逐檔修真問題**(每支改後都跑自測驗)

| 檔 | 問題 | 修法 | 驗 |
|---|---|---|---|
| VDF_ENG087 → **v0102** | 五條引擎路徑釘死版號 | `_newest_rel()` 尾版 glob(L54) | 10/10 |
| CGC_MDL156 → **v0102** | QuantGuard 與 25-roster 路徑釘死 | 尾版 glob(v0101 起 QuantGuard 是 polars 探針版,釘 v0100 會指到舊的) | GREEN 23/23 |
| SUP_MDL115 控制塔 | 5 個「特定版號存在」燈 | 改 `glob(…_v*.py)`,新版上線燈才不會誤熄 | compile OK |
| VDF_ENG051 | 模組頂 `import requests/bs4`=缺件即 Traceback(假紅) | 探針式載入 + `_require_net_libs()` 誠實 ABSENT 印裝法(不代裝) | compile OK |
| VAP_ENG003 → **v0101** · CGC_MDL055 → **v0101** | 只認位置動詞 | `--selftest` 等價轉換(L53) | 8 PASS/2 SKIP · 3/3(兩種寫法都通) |

**結果**:全景問題 **267 → 140(精準化)→ 129(逐檔修)**;SYSEXE 歸零。剩下的 HARDIMP 100 / PINVER 23 / VERB 6 都在非核心區(VeritasPulse、GroupIndex、CLI 套件、new modules engines),會改行為,依 L56 **報位置待令**,逐檔逐行在報告 TAB②。

**核心回歸**:CGC157 21/21 · 匯流排 48/48 · CGC156 23/23 · VCGC 19/19 · ENG087 10/10 · 稽核器 15/15 · registry-sync 5081。

**我自己又學到兩件**(已入教訓庫):稽核器的判準要能分辨「正式路由」與「自測夾具」,否則誤報會蓋住真問題(LL60);自測用字串切點取原始碼,切點必須唯一——我在文件字串裡寫了同一句話,把切點提前,害兩檢無故變紅(LL61)。

---

## 一-ac · 批536b · 令「先完成 VIA 上傳,再透過 VIA 跑修正實測 VRN」+「用同義字去抓 SSOT/檔名拆解法」+「NLP 工具 LAYOUT 工具」+「邏輯方法查備用引擎或 via-vdf-vrn」

**你貼的 64 份 `C:\測試樣本報告`**:原 PDF 不在本境,但收容件 `AttachmentFixedOutput_v1.0.0_b245` 裡有**同一批 64 份的修復文字**(`01_repair/documents/`)與**版面元素**(`02_layout/logical_layout.json` 232 元素)。所以這批是**內容級真測**,不是夾具。

**ENG086 v0101 新增 `corpus` 動詞**(收容件唯讀零觸碰),並照你的令接三件正主工具:

| 工具 | 接到哪 | 實際 |
|---|---|---|
| 券商同義字 SSOT | `VRN_BROKER_LIST_v01.json`(SUP_MDL015 管的正本) | 20 家 · 97 別名;正典名跟正本(兆豐=MEGABANK、高盛=GOLDMANSACHS),我的補冊只補正本沒有的,別名撞上就讓位 |
| LAYOUT 工具 | 收容件 `02_layout/logical_layout.json` | 64 檔 · 232 元素;有版面用版面標題**加上**前段文字(相加,不是二選一) |
| NLP 工具 | `VRN_ENG066` 樞紐 normalize | 簡→繁可轉;**逐行**做(整段做會把換行吃掉,逐行判準全失效) |

**64 份真研報實測(修前 → 修後)**

| 指標 | 修前 | 修後 | 說明 |
|---|---:|---:|---|
| 個股報告代碼 | 47/64 | **42/42** | 另 22 份是產業/晨會/市場/策略類,**本來就沒有**單一個股代碼(先分類再算,分母才對) |
| 券商 | 38/64 | **64/64** | 接上 SSOT 正本 + 頁面認不出就用檔名 |
| 評等 | 17/64 | **33/38** | 五法:線索詞(容得下「調降至」)/標題行(外資 `…; Buy (on CL)`)/引號內(`維持「持有」評等`)/前段獨立行/檔名;明示「未評等」記 NR。另 26 份文中根本沒有評等字樣=誠實 N/A |
| 個股目標價 | — | **28/42** | 文中沒有目標價線索就不給值(原本弱正則把 MS-Thermal 的 17382 當目標價=假資料) |
| 檔名日期 | — | **61/64** | |

**備用倉 `tonykuni/via-vdf-vrn` 查到的現成教訓**(同一批語料踩過的坑,直接用):①「目標價」與「潛在上漲空間」是兩個欄位,混在一起會把 23% 當價格 ②真報告多半寫「目標價145」沒有冒號,硬要求冒號會整片抽不到。兩點都已進 ENG086。

**登冊**:冊項 `vrn_firstpage_corpus` · 教訓 LL62–LL65 · 台帳 1063。產物 `VIA_Reports\first_page_logic\CORPUS_latest.json/.md`(逐檔一列,可直接對照)。

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

---

## 六 · 資料庫現況(批522;你貼的量測直接當量測;刷新=`via-census -Tables` / `via-taone check-data` / `via-vetf status` / `via-workflow db-summary`)

**在哪(資料家律:parquet 存、duckdb 管;搬=link 不複製;刪=你的手)**

| 層 | 路徑 | 說明 |
|---|---|---|
| 母資料夾(倉) | `C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics` | 程式/冊/交接;`VIA_Reports\*` 不入 git |
| 資料家 home | `C:\Users\tonyk\VIA System\via_database`(`VIA_DATA_HOME`) | 庫的家;引擎解析律 `VIA_DB_*` → home rglob → 舊 output_hub 路徑 |
| 鏡根 | `…\via_database\movies-dataset\data\VeritasIntelligenceAnalytics\functional modules\VDF\output_hub\` | 倉內 output_hub 的搬家位 |
| VDF 主庫 | `…\output_hub\mega\vdf_tw_market.duckdb`(`VIA_DB_VDF_TW_MARKET`) | 台股價/量/值/當沖/名冊/共識/月營收 |
| 主動 ETF 庫 | `…\output_hub\active_tw_etf\active_tw_etf_holdings\ActiveTWETF.duckdb` | holdings_daily |
| 邏輯/因子/政策表 | 每本 duckdb 內 `vrn_extraction_logic` / `via_policy_factors`(`via-vrnlogic sync-db` 寫) | 政策庫冊 `VIA_Policy_Laws_SSOT`(47 律 · 49 教訓)+ `VRN_ExtractionLogic_SSOT`(+firstpage_logic)攤平入表 |
| 參數庫 | `configs\system_parameters.json`(`via-cgfamily` 中央治理家族再生;不入 git) | system_governance / subsystem_configs |
| 產物 | `VIA_Reports\talib_one\RUN_*`(特徵 parquet/csv)· `VIA_Reports\talib_one\vap\<code>\RUN_*`(圖)· `VIA_Reports\vatetf\out\RUN_*`(候選沙盒)· `VIA_Reports\first_page_text\*.json`(ENG072)· `VIA_Reports\first_page_logic\*.logic86.json`(ENG086) | 不入 git |

**表現況(2026-09-15 你貼的)**

| 庫 · 表 | 列 | 日期範圍 | 燈 | 缺什麼 / 下一步 |
|---|---|---|---|---|
| vdf_tw_market · tw_prices_adj | 2,128,168 | 2020-01-02 ~ 2026-09-11 | GREEN | TA-Lib 價源(adj) |
| vdf_tw_market · tw_daily_prices | 2,183,362 | 1900-01-01 ~ 2026-09-14 | YELLOW | 1900-01-01 哨兵列(Z46;清=你的手) |
| vdf_tw_market · tw_trading_daily | 2,028,638 | 2020-01-02 ~ 2026-09-14 | GREEN | 成交金額源 |
| vdf_tw_market · tw_daytrade_stock | — | — | **ABSENT** | 量值走檔案收容道(L45)→ TA-Lib 量能函數 68 個才有值 |
| vdf_tw_market · tw_listings | 891(容器) | — | GREEN | ENG086 名冊(名→碼) |
| vdf_tw_market · consensus_latest(view) | 40 檔中 factset 4 · yfinance 26 | 2026-09 | YELLOW | FactSet 稀釋 EPS 只 4 檔 → forward P/E 覆蓋上限 10%(Z43) |
| vdf_tw_market · monthly_revenue_analysis | (eng069 v0108 OK) | — | GREEN | 去重生效 |
| ActiveTWETF · holdings_daily | 40 | 2026-09-07(1 檔 ETF) | YELLOW | 持股史 23 檔 · 缺快照 1034 日格(Z45;`via-etfhist backfill` 觸網) |
| VIA_Reports\talib_one · RUN_20260915_223005 | 148 列 · 2 檔 · 577 欄 | 2026-06-01 ~ 2026-09-11 | YELLOW | MissingActivityBasis 68(當沖缺) |
| VIA_Reports\first_page_text | (容器 71 件;你的機器 `via-fplogic status` 看) | — | — | `via-fplogic enrich` |

**還掛著(你的手)**:Z34 收 · Z43 VATETF EPS(v0104 重跑貼回)· Z44 當沖檔案收容(瀏覽器存 CSV)· Z45 持股史 · Z46 哨兵列 · Z47 via_paddle_311 境壞(重建)· Z48 vrn 境裝 opencc · Z49 第一頁版面/表格幾何(候)。

---

## 一-ad|批537 VRN 真報告第二輪:券商假綠拆掉、誠實分母立起來(VRN_ENG086 v0102)

批536b 那張成績單是「64/64 券商、33/38 評等、30/64 目標價」。好看,但**逐列查過就知道有三處不誠實**——這一批把它們拆開。

**① 券商 64/64 裡有四份判錯家(假綠)。**
`Daiwa-3653 / Daiwa-6278 / Daiwa-PCB` 被判成 CATHAY。文內唯一的 `cathay` 出自分析師信箱 `…@daiwacm-cathay.com.tw`(大和國泰合資體的網域),而 `cathay`(6 字)比 `daiwa`(5 字)長,最長別名優先就讓它贏。
`凱基投顧_2891 中信金_施志鴻_20260519.pdf` 被判成 CTBC:內文只有標的公司名「中信金」,真正的券商「凱基投顧」寫在檔名上。
修法兩條:
- **證據分級**(L58):判券商前先把 email/URL 挖掉 → 文內 > 檔名 > 電郵網域(弱)。每一列帶 `broker_how`,以後假綠看得見。
- **標的公司名否決**(LL67):用與代碼相鄰的兩條鐵證把標的名讀出來——文內 `台灣中信金(2891.TW/2891 TT)` 的括號前、檔名 `…_2891 中信金_…` 的代碼後。**不靠庫**:本境 tw_listings 只有 892 檔、2891 不在內(LL49),靠庫的否決在你的工作站有效、在這裡失效,那等於留著假綠。

**② 評等 5 份掛零,其中 3 份是我們的字彙不夠。**
凱基三份個股報告全寫「增加持股」(Outperform),收容件的 RATING 冊沒有這個詞。補上本土券商自己的尺度(增加持股/減少持股/優於大盤/劣於大盤/同步大盤/區間操作),而且**只看前段**——內文的「外資持有」「增持庫藏股」不是評等(LL68)。另外兩份是 MS 產業報告與 UBS 市場分析,本來就沒有單一評等。

**③ 分母不誠實=自己造判錯的紅燈(L57)。**「目標價 30/64」看起來漏了 34 份,實際上:2 份是報告自己寫 `Target price: n.a.`(Daiwa),16 份是**我們手上的修復文字裡根本沒有目標價欄**(GS/MQ 的側欄沒被修復出來),16 份是產業/晨會類不需要。真正「有線索卻抓不到」= **0**。判錯的紅燈和假綠一樣傷,所以四態各自列清楚。

**這一批量到的(64 份真研報 · 修復文字 · 原 PDF 不在本境)**

| 欄 | 誠實分態 |
|---|---|
| 個股代碼 | 42/42(另 22 份產業/晨會/市場/策略類本來就無單一代碼) |
| 券商 | 64/64 · 證據:文內 36 · 檔名 28 · 電郵網域(弱) 0 |
| 評等 | 命中 36 · 文中無評等字樣 8 · 非個股(不需) 20 · **有字樣抓不到(RED) 0** |
| 目標價 | 命中 30 · 報告自述 n.a. 2 · 文字無此欄 16 · 非個股(不需) 16 · **有線索抓不到(RED) 0** |
| 檔名日期 | 命中 61 · 檔名無日期 3 · **有數字解不出(RED) 0** |

`VRN_ENG086_FirstPageLogicBridge_v0102.py` 十五檢自測 15/15(⑪ 電郵網域 · ⑫ 目標價四態 · ⑬ 日期三態 · ⑭ 標的否決(空名冊也要成立)+ 本土尺度 · ⑮ 評等四態)。
產物:`VIA_Reports\first_page_logic\CORPUS_latest.json` / `.md`(表多了「證據 / 等態 / 價態 / 期態」四欄,逐列可查)。
你的機器:`via-fplogic corpus`(尾版律自動吃 v0102)。

**還沒做、等你的手**:GS/MQ 那 16 份要真的補出目標價,得回到原 PDF 的側欄(修復文字沒有那一塊)=Z49 第一頁版面/表格幾何那一條。

---

## 一-ae|批537 AST 頁與摘要:把「修過的」放進去(CGC_MDL158 v0102)

你說「FIXED CONTENT IN THE AST PAGE AND SUMMARY」。查了頁,毛病是真的:

- **TAB③「已修」在乾跑時只印一句「本次未套用」**。整張 AST 頁於是只講「還沒修的 129 個問題」,看不出批535–537 到底修過什麼。
- **摘要只有「問題 129 · 自動修 0」**。129 是什麼?可以自動修的幾個、要等你下令的幾個、真紅燈幾個?一個都看不出來。

**修法一:已修冊 + 活樹複驗(新律 L59)。**
新 SSOT `supportive modules/registry/VIA_PanoramaFixed_SSOT_v0100.json`(擁有者 CGC_MDL158)。每一筆修都帶可複驗的憑據,三種:
`class_zero`(該範疇活樹件數必須為 0)、`coverage_pct`(覆蓋率欄位 ≥ 門檻)、`tail_contains`(該族**尾版**檔必須含某些字、且不得含某些字)。
稽核器每跑一次就拿活樹重量一次——**冊說修好、現在也還是修好=GREEN;冊說修好、現在又量到=RED(回歸),而且回歸會把總裁決拉成 RED,不准被 YELLOW 蓋過去;量不了=ABSENT,誠實講量不了,不當綠。**
`tail_contains` 是特意設的:尾版律下最容易掉的就是「修沒帶進新版」(LL71——批536 的 HARDIMP 修寫進了 `VDF_ENG051` 的無版號檔,活樹尾版其實是 `_v0102`;那一版本來就乾淨所以沒出事,但下次不一定)。

**修法二:摘要四處同一句。** 主控台、頁首、TAB①、Markdown 全部走同一個 `summary_line()`,不會各講各的:

```
問題 129(可同時修 0 · 順序修 6 · 只報位置待令 123 · 真 RED 0)
· 已修冊 7 筆複驗 GREEN 7 / 回歸 0 / 待驗 0 · 本次自動修 0 處 · 實測 17/17 綠
```

**修法三:乾跑不印 OK。** TAB③ 改名「本次修復」,乾跑時結果欄誠實寫「乾跑(未寫檔)」配灰燈,不再印成綠色 OK。

**頁現在九個分頁**:① 總覽 ② 問題明細 ③ 本次修復 ④ **已修冊複驗**(新)⑤ 實測結果 ⑥ 中央派送 ⑦ 覆蓋率 ⑧ JSON ⑨ Markdown。

**這一跑量到的**(`via-panorama all`,尾版自動吃 v0102):總裁決 YELLOW · 掃 1516 檔 · 問題 129(順序修 6 · 待令 123 · 真 RED 0)· 已修冊 7 筆全 GREEN、回歸 0 · 實測 17/17 綠 · 加速器橋 100% · VDF 網路工具 100%。

**順帶量出來的一件事**:第一次跑 v0102 時總裁決是 RED,因為 VCGC ⑬ 元件冊少了 6 個元件(就是我剛加的那幾個函數)——`registry-sync --apply` 之後回綠。這正是這張頁該有的樣子:新東西沒登記,它就報紅,不會替我圓場。

CGC_MDL158 v0102 十八檢自測 18/18(⑭ 複驗三態 · ⑮a 摘要四處同句 · ⑮b 冊在位且本器擁有)。Grid v0317 把站名的「十三檢」改成「十八檢」。

---

## 一-af|批538 照你點的順序 VIA → VRN → VDF:自測格 18 紅 → 0 紅

你說「解決 VIA VRN VDF 照順序」。我先做的一件事是**把 18 個紅站一站一站單獨跑過**,拿真正的 FAIL 行——
因為我前一批把它們整批歸成「本境空庫」,那句話裡至少有一站是錯的:**其中一盞紅燈是我自己造的**。

### 分類結果(逐站,不是整批)

| 類 | 件 | 說明 |
|---|---:|---|
| 我自己造的紅燈 | 1 | 批535 加速器橋掃補插進 md5 冊管的正本 |
| 真缺陷(會騙下游) | 3 | 旗標打壞卻回成功 · 表在≠有料還照樣落報告 · 缺件 Traceback |
| 判錯的紅燈(判準錯) | 9 | 寫死天花板/寫死驗算標的/釘死版號/要求剛好 100% |
| 誠實缺料被印成紅 | 5 | 缺庫、缺鑰、缺選配畫圖庫 → 應為 SKIP |

### 一、VIA 段(六站)

**① 中央治理家族 md5 對冊——我自己造的。** 批535 的加速器橋全樹掃補,把 `[VIA:ACCEL-BRIDGE]` 插進了
`VIA_CentralGovernanceFamily_b514/` 四個檔,那是你上傳、`MANIFEST_b514.json` md5 冊管著的正本。
md5 一變就紅,自批535 紅到現在,而我先前把它歸成「本境空庫」。兩重錯:先造了紅燈,又把它推給環境。
四件已自 `67855ffc` 還原;保護一般化成**規則**——夾內有帶 md5 的 `*MANIFEST*.json` 就零觸碰,
而且這類檔連覆蓋率分母都不進(不然 100% 永遠掉到 99.7%,再生一盞判錯的紅燈)。

**② 憲章稽核 talib——假綠。** 本境我為了稽核裝過 talib,import 探針就把它判成「在位」:政策說退役、稽核說在位。
改成退役冊命中的一律 missing 標「退役(L50)」,hits 只列接班人 QuantGuard。憲章是你的定義正典,一個字都沒改。

**③ 殘餘盤點**卡「≤90」寫死天花板(實測 115,但與候裁冊逐檔對得起來);**④ 輸入主控台**的 `params` 由 `codes`
漂成 `code`/`ticker`,與引擎 CLI/頁/契約三方對不上;**⑤ 雙橋稽核**兩個中央稽核器對同一棵樹講不同的話
(範圍不同:非尾版舊版與 `_output/` 建置夾);**⑥ sysman Gate** 的唯一紅燈是退役夾裡一支 PS 的語法錯。

### 二、VRN 段(三站)

**真缺陷:`--file` 後面沒有值時,舊行為印一句「忽略」然後退回掃預設收件夾。** 收件夾空的時候看起來沒事;
本境 `incoming/` 躺著兩份 .docx,同一條指令就變成默默處理另一批檔、而且回 rc=0。旗標打壞卻回成功,
對串鏈的呼叫端就是一句謊(`via-closeout --run` 靠 rc≠0 才會誠實停)。改成缺值=參數錯,當場 rc=2。

另兩件:**每日觀察摘要**要求因子覆蓋剛好 100%,少的那一列是 3718.TWO 上市未滿 20 天、20 日均線天生算不出
(真實市場每有新股掛牌就會紅);**NLP 橋**釘死 v1.5.0/35 模組,收容夾已有 v1.6.1/36 模組。

### 三、VDF 段(四站)

**真缺陷:ETF×共識的 `_data_ready()` 只問表在不在、不問有沒有列。** 本境共識 0 列、持股 1125 列,
探測說「資料在位」,走完整車道再報三個 FAIL;更糟的是 `run()` 還照樣落了一份「共識可加權 0 檔」的 JSON/HTML
——下游讀到會當成有效結果。改成兩側都要有**列**才算在位,缺料在**產出之前**就停。

另三件:**調整層/因子庫**把驗算標的寫死 2330.TW(本境庫 892 檔沒有 2330,可是同一張表有 378,752 列 factor≠1,
隨便挑一列都能驗);**族群聚合層**缺快照時先報三紅再被 `CatalogException` 炸掉。

### 四、收尾(VAP/GroupIndex/格子)

seaborn 未裝報紅 → SKIP + pip 行(不代裝),而且**跳過的不算 OK**(舊計數印「十檢 OK 10」是小一號的假綠);
FRED 鑰缺席時那一檢本來就不可能綠 → SKIP;族群全球冊 48/51 改成**指名**缺 `BZ=F / CL=F / GC=F` 與補法;
格子加期望 `nodata_ok`(rc 0 或 2)給 VAP 驗收稽核——它的 rc=2 是誠實 NODATA,不是紅燈,而能嚴的站不放寬。

### 量到的

自測格 233 站:**OK 209 → 226 · FAIL 18 → 0 · SKIP 6**(誠實三態)。
治理台 UI Matrix 綠燈率 226/233 = 97.0%,八檢 8/8。VCGC 19/19、MasterControl 合約測 19/19、元件冊 5121 活元件。
剩下的 6 個 SKIP 全是誠實缺件:TA-Lib 三站(L50 退役,本來就該缺)、TA 工廠兩站、reconcile 對帳。

**還沒做、等你的手**:Z43 FactSet 共識覆蓋(共識 0 列)· FRED 鑰(`output_hub/mega/.fred_api_key`)·
全球期貨三檔 `BZ=F/CL=F/GC=F` · 族群分類快照(`via-datahome link` / `group_class`)· `pip install seaborn`。
這些補上之後,上面那 6 個 SKIP 會自己變成可驗的綠或真紅——那時候的紅才是要修的紅。

---

## 一-ag|批539 TA-Lib 拔線:刪檔不等於退役(新律 L60)

你貼回來一份舊區塊,裡面有 `pip install "TA-Lib>=0.6"` 和五條 `via-taone`。**那條路已經不存在了**:
`via-taone` 在批534 隨 TA-Lib 退役時就從指令書移除(尾版是 Register v0210),
它呼叫的 `VDF_ENG083_TALibOneBridge`、`CGC_MDL151_TaLibGate` 也都刪了。你貼的那份是批521 時代的區塊。

但這件事真正要追究的不是舊區塊,是**系統為什麼還會把人帶回去**。查完發現:批534 只刪了檔,**接線沒拔乾淨**。

| 還指著已刪引擎的地方 | 它一直在印什麼 |
|---|---|
| 總管理器引擎名冊(4 筆) | 名字還在冊上,看起來像現役 |
| 自測格 4 站 | 「引擎缺/自指佔位(誠實)」 |
| 繪圖資料律稽核冊(2 筆) | TA 工廠是技術分析正主 |
| VTMRA 家族(2 員) | 家族態永遠掛一個 ABSENT |
| 工具階梯 TA_INDICATOR | lv1 已刪的 TAFactory、lv2 `talib C 庫(候裝)` |

「引擎缺」這句話讀起來像**有東西該在卻不在**,實際是**退役**。誠實不只是別說謊,還要說清楚是哪一種缺
(缺件 / 未裝 / 退役)——這是 LL82。

### 這一批做的六件

1. **總管理器 v0140**:名冊拔掉 `CGC_MDL151_TaLibGate` / `VDF_ENG083_TALibOneBridge` / `VAP_ENG004_TAFactory` / `VDF_ENG048_TAFactory`。
2. **自測格 v0319**:拔掉四個指向已刪引擎的 TA 站(233 → 229 站)。技術分析只留 **QuantGuard 正主橋八檢**。
3. **繪圖資料律 v0102**:稽核冊兩個 TA 工廠 → 改列 `VDF_ENG086 QuantGuard 正主橋(L50 唯一活動技術分析路徑)`。
4. **VTMRA 閘 v0102**:家族八員 → 六員;**同一版把 verdict 裡給 `talib` 的「軟缺席=YELLOW」豁免一起拔掉**
   ——成員都拔了、豁免留著,就是替不存在的成員開後門,哪天有人用同一個 id 塞回來會被默默放行(LL83)。
5. **工具階梯 v0102 + 階梯冊**:`TA_INDICATOR` 兩級都失效(lv1 已刪、lv2 L50 禁用)→ 單級 QuantGuard;
   舊級原文存進 `retired_rungs_b539`,不是刪掉。自測 ⑧ 改成「階梯不得再有可升到 talib 的那一級」。
6. **本境 `pip uninstall TA-Lib`(0.8.0)**:那是我先前為了稽核自己裝的。L50 說不得安裝,**那就包含我的稽核用途**;
   拔掉之後 import 探針與政策才真的一致(LL84)。

### 新律 L60 退役拔線律

> 退役不是把檔刪掉就算完。要一次做完四件:① 檔進退役夾或記入退役冊 ② 所有接線拔掉並指向接班人
> ③ 判定律裡給退役件的豁免口一併拔掉(不留後門給不存在的成員)④ 每一處拔線逐條記帳。
> 做不到就不要宣稱退役。

### 量到的

活樹尾版 1455 檔,AST 層級掃過:**指向已刪 TA 引擎或 `import talib` 的接線 = 0**
(剩下的字面命中全是這一批自己的退役註記)。
自測格 **229 站:OK 227 · FAIL 0 · SKIP 2**(reconcile 對帳=環境缺件、selftest grid=自指)。
VCGC 19/19 · MasterControl 合約測 19/19 · VTMRA 七檢 7/7 · 工具階梯 十檢 10/10 · 總管理器 v0140 10/10。

### 技術分析現在走這裡

`via-quantguard`(`VDF_ENG086_QuantGuardOneBridge`),動詞 `status | probe | run | selftest`。
缺 polars = 誠實 ABSENT(rc=3)並附 pip 行,**不代裝**;階梯不得再往 talib 升。

---

## 一-ah|批540 VRN 規則收斂第一步:先把真相收斂到一處,再談動刀(新律 L61)

你要的是「相同邏輯相同規則整合去重 · 有錯誤一起討論 · 只增不減 · 不影響現有功能 · 不要九頭龍」。
所以這一批**一行現役引擎的行為都沒改**,做的是把散掉的真相收攏,並把落差攤在桌上。

### 量到的硬落差(這就是要一起討論的錯誤)

同一套評等詞彙,四支**現役**引擎各有各的版本:

| 引擎 | 評等規則 | 少了什麼 |
|---|---:|---|
| **ENG086 第一頁橋 v0102**(64 份真研報驗過) | **38/38** | 正本 |
| ENG073 報告結構庫 v0127 | 17/38 | 沒載收容件字典(自己寫死一份)→ 英文評等缺 13;本土尺度缺 8(**增加持股/減少持股**) |
| TW02 報告解析器 v0101 | 12/38 | 英文評等缺 14;本土尺度缺 12 |
| 首頁全能引擎 v0125 | 25/38 | 有載字典,但本土尺度缺 13 |
| ENG080 四點文摘 v0105 | 不適用 | 它只抽目標價,拿評等量它是無中生有 |

**白話**:凱基寫「增加持股」時 ENG086 讀得到、ENG073 讀不到;而 ENG073 正是報告**入庫**那一支。
這跟 ENG086 批538 修掉的那個漏是同一個,只是還沒修到它身上。

### 這一批做了什麼

1. **規則正本冊** `supportive modules/registry/VRN_FieldRules_SSOT_v0100.json`
   —— 把**已驗過的那一套**(ENG086 v0102)立為正本並鎖住:評等 38 詞、目標價線索、券商證據分級、
   email/電話出處、財報樞紐指向,連每條規則背後的教訓編號一起記。
2. **唯一讀冊口** `supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0100.py`(七檢 7/7)
   - `drift` —— 逐支引擎列出落差(上表就是它印的)
   - `rating_of / tp_of / broker_of` —— **惰性轉交正本實作**,不是只給詞表。
     光補詞表不補守衛會製造假評等,所以連 ENG086 踩過的三個坑一起繼承:
     本土尺度只看前段(LL68)· 幅度不是價格(LL64)· 券商證據挖掉電郵網域(LL66/LL67)。
   - 零改線:import 這支樞紐不碰任何引擎;不落檔;不改寫任何現役引擎。
3. **順手打出一個潛伏的假評等** —— `safe_rating` 的獨立短行分支寫著「≤8 字**剛好是**別名」,
   實作卻用包含比對:「外資持有比重上升」剛好 8 字、含「持有」→ 判成 HOLD。
   64 份真研報裡**還沒咬到**(走那條路的三份都是 `買進`/`Buy` 自成一行的真評等),所以是潛伏的假綠。
   → **ENG086 v0103** 改成整行等於別名;64 份實測**零回歸**(評等仍 36、目標價 30、券商 64/64、真 RED 0)。

### 新律 L61 規則收斂律

> 同一件事的規則不得散在多支引擎各抄一份。**先收斂真相、再動刀**:
> ① 立一本正本冊(取已在真資料上驗過的那一套)+ 一個讀冊口,落差逐條攤開 —— 這一步零改線;
> ② 攤開之後才由操作員決定誰改、一支一支改、每支都要在同一份真語料上驗零回歸。
> 跳過第一步直接合併,就是把四個會漂移的真相,換成一個沒人驗過的新真相。

### 下一步等你一句話

三支落差引擎要不要接上樞紐,建議**一支一支來**,每支接完都用同一份 64 份語料驗零回歸:

| 順序 | 引擎 | 理由 | 風險 |
|---|---|---|---|
| 1 | **ENG073 報告結構庫** | 它是入庫那一支,漏評等直接進資料庫 | 中:要同時補「只看前段」守衛,否則內文誤判 |
| 2 | 首頁全能引擎 v0125 | 已載字典,只缺本土尺度 | 低 |
| 3 | TW02 報告解析器 | 落差最大,但下游用量最小 | 低 |

你說一個,我就接一個;不說,現況照舊跑,一位元都沒動。

---

## 批541 —— 去衝突 · 邊實測邊長同義字 · 收容件導入驗證(仍零改線)

操作員令:「完成整合測試 邏輯整合去衝突 ssot 同義字 等下邊實側邊更新同義字」
追令三句:「clsa = clst」·「CTBC 中信」·「加這個檢查導入」

### 一、去衝突:同一家不得有兩個正典名

合併三張券商表(收容件字典 × SSOT 正本 × 橋側補冊)掃出 **17 個原始撞名**,合併後還剩 **2 個活的**
——同一個別名對到兩個正典名,下游一 join 就散:

| 撞名別名 | 對到 | 根因 | 處置 |
|---|---|---|---|
| `clst` | CLSA / CLST | 冊上把里昂分成兩筆 | **操作員裁定「clsa = clst」** → CLST 併入 CLSA(20→19 家;CLST 原文留在 `merged_b541` 鍵下,只增不減) |
| `jp` `jpm` `jpmorgan` `j.p. morgan` | J.P.MORGAN / JPMORGAN | 讓位規則的洞:只 pop「不在 SSOT **且不在補冊**」的鍵,而 JPMORGAN 兩邊都有 → 永遠 pop 不掉 | 改成「別名被 SSOT 收編,非 SSOT 的鍵一律讓位」 |

新增 `broker_conflicts()` 與自測 ⑯',**鎖住零撞名**——同一家兩個正典名再也回不來。
合併後 45 家、撞名 0。

### 二、邊實測邊長同義字(harvest):只提候選,絕不自己寫進正本冊

樞紐加 `harvest` 動詞:拿 64 份真語料跑一輪,把「該有卻沒命中」的欄位旁邊的候選詞端出來,
一律標 `PENDING_OPERATOR`,附檔名與證據。**不代設**——正本要長,是你點頭那一刻才長。

濾網修了四輪,每一輪都是實測打回來的:

| 輪 | 端出來的 | 為什麼是假的 |
|---|---|---|
| ① | 12 條噪音 | 只掃檔名開頭,連日期段都當機構 |
| ② | `晶心科`、`瑞基` | 這兩種檔名是 `<標的>(代碼,評等)-<券商><日期>`,開頭是**標的公司名** |
| ③ | `公司訪談摘要`、`PCB` | 一個是報告段名、一個是產品類別;它們的檔名裡**早就有**兆豐 / Daiwa |
| ④ | **0 條** | 加閘:檔名裡任何一處已有在冊別名 → 這份本來就認得出券商,生不出「新」券商 |

### 三、修到 0 之後,那個 0 本身變可疑 —— 加負控

一個**永遠回 0** 的濾網,跟一盞假綠燈沒有兩樣(LL77 的同族)。
所以加自測 ⑩:合成兩列,假候選(檔名已有「兆豐」)要擋掉、真候選(全新機構名「寰宇投顧」)要放得出來,
而且一份檔名只端一個(不把標的公司名一起撈進來)。**兩邊都對才算這道濾網在工作。**

### 四、「加這個檢查導入」—— 舊那一檢比它看起來弱

同一份 `VIA_VRN_FirstPageEngine.py` 今天又被上傳兩份(30,115 bytes,md5 `d4cdaedf…`,
跟 9/9、9/15 那兩份也一樣)。量過:它**早就在收容件裡,位元一個不差**,自測 ① 每次都綠。

那為什麼還要加一檢?因為 ① 是拿**檔案的 md5** 去對**同一個資料夾裡的冊**——
檔案跟冊一起被換掉,兩邊還是一致,綠燈照亮,騙的是自己(跟 LL74 先建後斷言同一種形狀)。
而且它只驗位元,不驗「導入」本身:檔案在、位元對,但 import 就炸、或宣告的模組被改名,① 一樣是綠的。

**ENG086 v0105 加 ⑱ 三段,全過才算導入成立:**
① 位元錨 —— 期望 md5/sha256/bytes **寫死在程式碼裡**(`INTAKE_ANCHOR`),檔案=錨=冊 三方一致;
② 真的 `exec_module` 導得進來(不是「看得到就算」);
③ 冊上宣告的 11 個模組一個不少(`load_ssot_blocks` + 10 個類別)。

再加 **⑱' 負控**:在產物夾沙盒裡把檔案與冊**一起**換掉(收容件零觸碰),當場證明
**舊檢綠 · ⑱ 紅**。擋不住這一手的檢查,綠燈只是自己對自己點頭。

### 五、「CTBC 中信」—— 量過,已成立,零改動

CTBC 合併後有 7 個別名:`中信 / 中信金 / 中國信託 / ctbc / CTBC / 中信投顧 / 中信證券`。
文內只出現「中信證券」也判得出 CTBC(證據層「文內」);而 `凱基投顧_2891 中信金_…` 那份
**仍然被標的否決擋住**(veto = {中信金, 台灣中信金},別名「中信」是它的一部分 → 不算券商證據),
退到檔名層得 KGI。兩件事同時成立,所以這一句不需要改任何東西——只需要被量一次。

### 本批實測

| 量尺 | 結果 |
|---|---|
| ENG086 v0105 自測 | **十九檢 19/19** |
| 64 份真研報 | **零回歸**:券商 64/64(文內 36 + 檔名 28)· 評等 36 · 目標價 30 · 檔名日期 61 · **真 RED 0** |
| 樞紐 SUP_MDL749 v0101 | **十檢 10/10**(撞名 0 · 合併後 45 家 · 候選 0 條) |
| 自測格 v0321 | 230 站 · OK 227 / FAIL 1 / SKIP 2;那 1 紅是 VCGC 等本批 `registry-sync`,同步後 **19/19** |

新教訓 **LL88**(檔案在≠導得進來;檔案對冊≠驗過,錨要放在外面)·
**LL89**(永遠回 0 的濾網=假綠燈,濾網必配負控)·
**LL90**(同義的裁定權在操作員不在冊)。

### 下一步還是等你那一句

批540 列的三支落差引擎(ENG073 → 首頁全能 → TW02)**一支都還沒接**,現況照舊跑,一位元沒動。
你說一個,我就接一個,每接完一支都用同一份 64 份語料驗零回歸。

### 批541b 補洞:短令 `via-vrnrules`

批540 立了規則正本樞紐卻**沒給短令**——功能註冊七處少一處,等於你在工作站叫不出它。
Register **v0211** 補上(pwsh 語法解析 OK · 12465 tokens):

```
via-vrnrules             一行狀態(冊在不在 · 評等詞幾個 · 券商證據分級 · 消費端幾支)
via-vrnrules drift       逐支現役引擎列「正本有、它沒有」的規則(只量它真的在抽的欄位)
via-vrnrules conflicts   去衝突:同一別名對到多個正典名 = 撞名,必須是 0
via-vrnrules harvest     邊實測邊長同義字:端出候選,一律 PENDING_OPERATOR(絕不自己寫進正本冊)
via-vrnrules selftest    十檢自測(含候選閘門負控)
```

---

## 批542 —— 「跑太慢」的根因不在加速器,在每道指令都要穿的那件外套

操作員令:「前一個指令跑太慢 請加入25個PS加速器 請確認所有PY指令都有加入加速器」

### 一、先量再說:你要的兩件,量出來都已完成

| 你問的 | 量到的 | 憑據 |
|---|---|---|
| 加 25 個 PS 加速器 | **早就是 25 個** | `VIA_Accelerator_Roster_SSOT` accelerators=25 · `VIA_PS_Accelerators_25_Roster_v0100.ps1` 25 條 · `$global:VIA_ACCEL25` 由它生成 · MDL156 二十三檢 GREEN |
| 所有 PY 指令都有加速器 | **活樹 100%** | `via-sweep --audit`:活樹 **797** 支 · `accel_have 797` · **`accel_miss 0`** · 網路橋 50/50 |

非活樹另有 accel 缺 66、net 缺 6——66 支全是**舊版號檔**(`VIA_VRN_FirstPageEngine_v0104…v0122` 那種),
6 支在**凍結產出夾**。依 L55 活樹律這兩類不是活樹,對它們報缺就是假紅(批538 已經處理過同一件事)。

短令側也早就接好:`Register-VIA-Commands` 第 24~33 行就是 `[VIA:PS-ACCEL]` 橋,
而且**所有 py 指令一律走 `Invoke-VIAPython`** 這個中央唯一入口,沒有繞道。

**所以照著你說的再加 25 個,只會把已經 100% 的東西變成 100%,慢照樣慢。**

### 二、真的慢在哪:拆秒數

| 段 | 耗時 |
|---|---|
| python 本身(`-c pass`) | **~20 ms** |
| `Invoke-VIAPython` 外套 | **279 ms** |
| 開視窗第一道再加點燈 | **+1,137 ms** |

拆開是三筆,全在 `supportive modules/VIA_PS_PyProgress_Module.ps1`:

1. **點燈純動畫 625 ms** —— 快取模式每格 `Start-Sleep -Milliseconds 25` × 25 格。
   快取模式**根本沒有東西要等**,那 625 ms 是畫給人看的,不是工作。
2. **固定 250 ms 輪詢** —— 每道指令平均多付 125 ms、最壞 250 ms,才發現它其實早就跑完了。
   而短指令(`--selftest` / `status` / `conflicts`,python 側 0.0~2.5 s)佔絕大多數,卻全額付這個稅。
3. **`Write-Progress` 每 250 ms 無條件重繪** —— Windows 主控台是重繪整條橫幅,很貴;
   即使那一秒什麼都沒變也照畫。400 ms 就結束的指令還會閃一條橫幅再消失。

### 三、改法(只動輪詢節奏,不動排水邏輯)

- 快取點燈**零睡眠**
- **自適應輪詢**:10 ms 起跳、倍增退到 250 ms —— 短跑幾乎零延遲,長跑照樣 250 ms 一次,CPU 不多花
- **進度條節流**:秒數或狀態行變了才畫;**400 ms 內免橫幅**

### 四、實測(同一棵樹、同一條快取路徑量的)

| | 改前 | 改後 | |
|---|---:|---:|---|
| 首發(含點燈 25 格) | 1,137 ms | **280 ms** | −75% |
| 後續每道 | 279 ms | **37 ms** | −87% |
| 六檢行為 | FAIL 0 | FAIL 0 | 零變更 |

七道一組的區塊(上一則我給你的那種):**3.2 s → 0.5 s,省約 2.7 秒的純外套稅。**

### 五、行為用六檢釘住(快不能拿正確性換)

改外套最怕的是「快了,但吞掉一行 stdout / 吞掉一個 rc」。新增
`supportive modules/VIA_PS_PyProgress_Selftest_v0100.ps1`(短令 **`via-pyprog`**):

```
① 短跑 stdout 一行不少地回到 pipeline   ② rc 0 照實回
③ 長跑邊跑邊轉播、結束仍收齊            ④ 非零 rc 不吞
⑤ stderr 不混進 stdout pipeline         ⑥ 逾時 rc 124、不卡斷
```
**改前改後跑同一組六檢,都是 FAIL 0。**

### 六、加一道「別改回去」閘,並且做了負控

`CGC_MDL156` v0103(二十三檢 → **二十八檢**)靜態斷言那三個加速還在、外套六檢在位。
負控當場做過:**把外套改回舊版 → RED 25/28;還原 → GREEN 28/28。**
(這正是 LL89——一個永遠會過的檢查跟假綠燈沒兩樣。)

新教訓 **LL91**:「跑太慢」的時候,先把秒數拆開再決定加什麼。量不出來就不要加。
