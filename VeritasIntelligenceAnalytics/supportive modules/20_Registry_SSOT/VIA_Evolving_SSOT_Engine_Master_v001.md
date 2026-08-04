# VIA · Evolving SSOT Engine · Master Architecture v001

Generated: 2026-07-05
命題：把台股資料庫、題材/產品分類、總經因子、資金流/籌碼、因果、驗證、回測、支援工具鏈——**全部收進一個會演化的單一真相源（SSOT）**。
六大不變律（承你既有原則）：**只增不減 append-only · sandbox-first · review-only · 無 canonical 覆寫/刪除 · 證據分級 · provenance 必附 · 版本演化**。

---

## 0. 什麼叫「會演化的 SSOT」
- **單一真相**：任何資料/因子/檔案/UI，都只有一筆 canonical 記錄，其餘皆為版本或衍生。
- **會演化**：真相**不被刪改，只被 supersede**（版本 +1，舊版保留、標 superseded_by）；資料品質提升時 **M→V 升級**、因子 生效/衰退 狀態隨時間流動。
- **可稽核**：每筆帶 provenance + evidence + as_of + lineage，任何結論可重現。
- **安全**：進 canonical 前一律 sandbox → review → staged activation，禁止一次全 activate。

---

## 1. SSOT 通用記錄（所有東西都登記成這個）

```json
{
  "ssot_id": "VIA-<DOMAIN>-<hash8>",
  "domain": "STOCK | TAXONOMY | MACRO | FLOW | FACTOR | VALIDATION | BACKTEST | SUPPORTIVE | UI | GOVERNANCE",
  "kind": "table | registry | factor | dataset | script | ui | rule | run",
  "entity": "2330.TW | US_CPI_headline | D1_leverage | ...",
  "version": "v001",
  "status": "active | superseded | quarantine | review | deprecated",
  "superseded_by": null,
  "evidence_status": "V | M | P | Est | Syn",
  "data_type": "LEVEL|RATE_PCT|YOY|MOM|INDEX|DIFFUSION|RATIO|SHARE_PCT|ZSCORE|NA",
  "source_form": "API|TABLE|TEXT|EVERNOTE|GRAPH_OCR|CODE",
  "as_of": "2026-07-05",
  "provenance": "url|file|note_id",
  "lineage": ["parent_ssot_id", ...],
  "risk_flag": "SAFE|LOW|MED|HIGH|CRITICAL",
  "keep_decision": "KEEP_CORE|KEEP_UI|KEEP_DATA|KEEP_DOC|QUARANTINE|REVIEW",
  "hash": "sha256",
  "created_ts": "..."
}
```
> 這是全系統唯一的「戶口名簿」。資料點、檔案、因子、UI、腳本、跑批——全部先在這裡有一筆，才存在。

---

## 2. 七大域（Domains）與對應

| Domain | 內容 | 既有產物/檔案 |
|---|---|---|
| **STOCK** | 個股資料骨架 | tw_stock_master / price_daily / market_cap / dividend_yield / factset_consensus / yfinance_consensus / valuation → `vw_tw_stock_daily_snapshot` |
| **TAXONOMY** | 分類：產業→次產業→產品→題材→Leader/Peer/Laggard | 本文 §4；HyperBOM 產品軸；StockFlow 族群 |
| **MACRO** | 總經因子 | ISM_PMI_12M · CPI_PPI_Detail · Labor_Detail · RetailSales · Official_vs_Unofficial · SurveyResponseRates · MajorIndices · US_Macro_DataPack |
| **FLOW** | 資金流/籌碼 | TW_StockFlow_Indicators(D2) · PublicBroker_BranchTracking(D5) · GovFunds_MarketFlow(D5) · AppendixB FIS(D8) · FIS harness |
| **FACTOR** | 因果/因子/評分規則 | ObservationParams(D1–D9) · ScoringSpec(R1–R9) · PushPull_Causal_FieldMap |
| **VALIDATION** | 證據/驗證/攝入 | AppendixA Registry · Ingestion_Classification_Schema · Extraction_Matrix |
| **BACKTEST** | 回測/評分/演化 | FIS_Backtest_Harness · Dragon-9 scoring · OOS/Walk-Forward |
| （橫向）**SUPPORTIVE / UI / GOVERNANCE** | 支援/介面/治理 | VPNS Libs · Accelerators · Consoles · SandboxPatch · SelfBuild |

---

## 3. SSOT 分層資料流（骨架 → 因子 → 分數 → UI）

```
[STOCK] 個股日快照  ┐
[TAXONOMY] 族群/題材 ┤→ [FACTOR] D1–D9 觀察參數 → 標準化(z/pct, ScoringSpec R1–R9)
[FLOW] 籌碼/資金流   ┤        │
[MACRO] 總經因子     ┘        ▼
                     [VALIDATION] 攝入分類軸 + 證據分級 + 交叉驗證
                              ▼
                     [BACKTEST] OOS / Walk-Forward / IC / 三分數(verified/breadth/dq_adjusted)
                              ▼
                     [UI] Master Overview Router → Flow Console / Dashboards
```
- 每一跳都**只增不減**、帶 provenance；GRAPH_OCR/synthetic 不得進 verified 分數。

---

## 4. 分類法（回答 BY STORY / CATEGORY / PRODUCT ＋ 檢視你的分組）

### 4.1 四軸分類（不要把它們混成一軸——你原本的分組就混了）
| 軸 | 內容 | 例 |
|---|---|---|
| **CATEGORY 產業** | 官方產業別 | 電機機械、半導體、金融 |
| **CHAIN 價值鏈位置** | 上/中/下游 | 上游配電、中游系統整合、下游發電營運 |
| **PRODUCT 產品線** | 具體產品 | 電纜、重電/配電、系統整合、發電 |
| **STORY 題材** | 市場敘事 | 重電、綠電、AI 電力、資料中心 |

> 分完四軸，才在**乾淨的子群**內做 Leader/Peer/Laggard。

### 4.2 檢視你貼的「電機機械」分組（近三月漲跌）
| 股 | 你的標記 | 漲跌 | SSOT 修正判斷 |
|---|---|---:|---|
| 台汽電 | 下游發電營運 | +81.51% | **IPP 民營電廠**，商業模式≠設備商 → 應獨立為「發電營運」題材，不與電纜/重電同群（Leader 但異質，離群）|
| 亞力 | 上游配電系統 | +16.48% | 重電/配電 |
| 中鼎 | 營造設置 | +13.78% | **工程統包**，屬營造題材，非電機設備 → 移出 |
| 大東電/合機/宏泰/大山 | 電纜 | +11.5%~−1.8% | **電纜子群，最內聚**（區間窄）→ 保留為一族 |
| 巨路 | 中游系統整合 | +2.28% | 系統整合 |
| 華城 | 上游配電系統 | −9.71% | **與亞力同標「配電系統」卻反向（+16 vs −10）→ 群內走勢背離** |
| 源大環能 | 中游/汽電共生 | −19.54% | 綠電/汽電共生題材 → 另群 |

**三個要修的問題**
1. **軸混用**：把「上中下游」和「電纜/配電/發電」混在同一欄——拆成 CHAIN 軸 + PRODUCT 軸。
2. **異質離群**：台汽電(IPP)、中鼎(工程)、源大環能(綠電) 商業模式不同，硬塞同群會污染族群訊號 → 各自歸題材。
3. **群內背離（呼應你先前的規則）**：亞力 vs 華城 同為「配電系統」卻走勢相反 → **群組內聚檢定不過 → 該子群要重分或細分**（見 §4.3）。

### 4.3 族群有效性檢定（Leader/Peer/Laggard 前置閘）
- **內聚**：子群成員兩兩報酬相關 median ≥ 門檻（對窗 z）→ 才算「一群」。
- **分離**：Leader vs Peer 兩條線若相關過高（走勢幾乎一樣）→ **合併**（不要硬分兩群）；若成員與群心相關過低（如華城 vs 亞力）→ **踢出/細分**。
- 過閘後才排 Leader（群內最強且領先有效）/ Peer（同步）/ Laggard。
- **Laggard 處理**：你說「落後就刪」——SSOT 折衷（守 append-only）：**不硬刪，降為 `status=dormant` 監控層**，不佔運算、但保留（落後者可能翻身、也是族群廣度訊號）。要硬刪再由你逐檔核可。

---

## 5. Evolution 機制（怎麼「演化」而不亂）
| 事件 | 動作 |
|---|---|
| 新資料/新版本 | version+1、舊版 status=superseded、superseded_by 指向新版（**不刪**）|
| 資料品質提升 | evidence M→V（官方數列補齊後）；重算 verified 分數 |
| 因子失效/生效 | factor status: 生效中/監控中/衰退中（只增不減，不刪因子）|
| 重複檔案 | hash+mtime+title 比對 → 標 duplicate/snapshot_duplicate，留最新、舊版 dormant |
| 衝突 | 兩來源不一致 → status=CONFLICT，走交叉驗證，不自動選邊 |
| 分組調整 | 族群重分 → 新 taxonomy 版本，舊版保留 lineage |

---

## 6. Governance Gate（安全框架，承 PanoramaSync/Stabilizer）
```
Gate: VIA_SSOT_REVIEW_READY_ONLY
Allowed : inventory · hash compare · schema extraction · md/html table extract ·
          py_compile · PowerShell AST check · duplicate detect · matrix report · sandbox dry-run
Blocked : canonical overwrite · production activation · direct DB write ·
          delete · rename original · auto-patch original source · Stop-Process
```
- 三輪 panorama（R1 全面/平行安全 → R2 序列 → R3 打磨）、Hydra-9 風險閘、預設 dry-run、append-only。
- 進 canonical 前必經：sandbox → review-only HTML matrix → **operator approval** → staged activation。

---

## 7. 整併地圖（你貼的檔案 → SSOT 域/表）
| 檔案 | Domain | SSOT 記錄 | keep_decision |
|---|---|---|---|
| tw_stock_master / price / mktcap / dividend / consensus | STOCK | 各對應 parquet + wide view | KEEP_CORE |
| AppendixA Registry (md/xlsx/pdf) | VALIDATION | data_validation_registry；pdf 降 evidence | KEEP_DATA/DOC |
| Ingestion Classification Schema | VALIDATION | 攝入軸規則 | KEEP_CORE |
| Extraction_Matrix (md/html×N) | VALIDATION | extraction_method_registry；html 去重留最新 | KEEP_DOC/REVIEW |
| PushPull_Causal_FieldMap | FACTOR | factor_causal_map | KEEP_CORE |
| ObservationParams / ScoringSpec | FACTOR | D1–D9 + R1–R9 規則 | KEEP_CORE |
| TW_StockFlow_Indicators | FLOW | stock_flow_indicator_registry(D2) | KEEP_CORE |
| PublicBroker_BranchTracking / GovFunds | FLOW | D5 proxy 規格 | KEEP_CORE |
| AppendixB FIS / FIS_Backtest_Harness | FLOW/BACKTEST | D8 + backtest_run | KEEP_CORE |
| Macro MDs (ISM/CPI/PPI/Labor/Retail/…) | MACRO | macro_factor_registry | KEEP_DATA |
| MajorIndices / Official_vs_Unofficial / SurveyRates | MACRO | 對應 factor rows | KEEP_DATA |
| Run_VIS_HyperBOM | TAXONOMY | tw_product_axis_registry | KEEP_CORE(sandbox) |
| VPNS_Libs / Accelerators | SUPPORTIVE | supportive/accelerator registry | KEEP_DOC |
| SandboxPatch v025 / SelfBuild | GOVERNANCE | sandbox_patch_plan / build lane | REVIEW(sandbox-only) |
| ONE_Master_Overview / Flow_Console (html×N) | UI | dashboard_router / workflow_ui；去重 | KEEP_UI/REVIEW |

---

## 8. 目錄（SSOT 引擎）
```
VIA_SSOT_ENGINE/
├─ 00_ssot/                # 戶口名簿：manifest、lineage、version、duplicate matrix
│  ├─ ssot_registry.parquet
│  ├─ lineage_graph.json
│  └─ integration_decision.json
├─ 01_stock/               # STOCK 域（7 表 + wide view）
├─ 02_taxonomy/            # CATEGORY/CHAIN/PRODUCT/STORY + Leader/Peer/Laggard bridge
├─ 03_macro/               # MACRO 域（各因子 parquet）
├─ 04_flow/                # FLOW 域（法人/分點/大戶/融資/gov/FIS）
├─ 05_factor/              # FACTOR 域（D1–D9、R1–R9、causal map）
├─ 06_validation/          # 攝入軸、AppendixA、Extraction Matrix、evidence report
├─ 07_backtest/            # FIS harness、OOS/WF、三分數
├─ 08_supportive/          # VPNS libs、accelerators、sandbox patch（review-only）
├─ 09_ui/                  # Master Router、Flow Console、Dashboards
└─ 99_runs/                # RUN_YYYYMMDD_*_REVIEW_ONLY
```

---

## 9. 落地順序（staged，不許一次全 activate）
1. **Inventory**：掃全檔 → 每個進 ssot_registry（hash/size/mtime/title）。
2. **Duplicate/Role**：去重、分域、keep_decision。
3. **Schema/Classify**：套攝入分類軸（§1、data_type/evidence/source_form）。
4. **Register**：寫 00_ssot 戶口名簿 + lineage。
5. **Validate（sandbox）**：AppendixA 規則 + 交叉驗證 + py_compile/AST。
6. **Review-only HTML matrix** → **operator approval**。
7. **Staged activation**：先 STOCK+MACRO（V 級）跑 verified 分數；FLOW/FACTOR 補齊後升級；TAXONOMY 過內聚檢定後上線。
8. 全程 append-only、dry-run 預設、canonical 不覆寫。

---

## 10. 一句話
**SSOT 引擎 = 一本只增不減、帶證據與血緣的戶口名簿 + 七大域的資料/因子/分數/UI + sandbox-first 的治理閘。** 你貼的所有檔案都不是「新系統」，是這本名簿裡的一筆筆記錄；它們透過 lineage 連起來、隨資料品質 M→V 演化，最後在同一把 z/百分位尺上被比較、評分、呈現——而且永遠可回溯、永遠不被一次性 activate 搞爛。
