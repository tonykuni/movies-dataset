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
| **W** | 8 件 FAIL_HIT 首頁件要用新次序重抽 | `via-firstpage -RetryFailed`(忽略 TTL 只重試 FAIL)。 |
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
