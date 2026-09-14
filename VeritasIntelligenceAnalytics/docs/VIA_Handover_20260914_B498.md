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
