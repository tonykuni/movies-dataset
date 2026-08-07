# VIA Forge · Consolidated Stack

把 DocForge v2 + TextLab + DocFetch Stack 的能力**整併成少數幾支強引擎 + HTML 前端**。
一鍵 PowerShell 啟動:裝環境、建路徑、self-test、起後端、開 UI。

只增不減:合併後是**能力超集**,DocForge 一個功能都沒掉。

---

## 架構(2 強引擎 + 1 前端)

```
VIA_Forge_Launcher.ps1  = Orchestrator
   偵測 Python → venv → 裝套件 → 建路徑 → self-test → 起後端 → 開 UI → 健康檢查 → 關閉
        │
        ▼  ProcessStartInfo
via_server.py  = 薄後端(stdlib http.server,零額外依賴)
   GET /  ·  /api/health · /api/config · POST /api/scan · /api/export · /api/shutdown
        │
        ▼  fetch()  loopback JSON API
ui/index.html  = 前端(控制台 + Dashboard 合一,Visual Lock)
        │
        ▼  委派
via_forge.py   = 單一強引擎(全部核心能力)
```

**為什麼 PowerShell 不當傳輸層**:PS 專責環境治理與生命週期;前後端用 localhost
JSON API 對接,單一 port、零跨機、無資料外流。

---

## via_forge.py — 單一強引擎(能力超集)

| 區塊 | 能力 |
|---|---|
| **A 加速器** | LazyTools · Bloom(`size=`) · Memo+Disk Cache · 分塊 sha256 · ThreadPool · Progress · Timer |
| **B Config** | SSOT JSON,展開 `{root}`、AUTO fallback、自動建目錄 |
| **C 格式** | Office(docx/xlsx/pptx)· Legacy(.doc/.xls/.ppt)· ODF · PDF · RTF · HTML · EML · MSG · Image · Google 指標 · TEXT(txt/csv/tsv/md/json/xml)|
| **D 修復 Fix** | 編碼 · zip 容器 · PDF 線性化 · 影像 · legacy → OK/REPAIRED/DAMAGED/UNREADABLE |
| **E 抽取** | native readers + OCR(圖片/影像式 PDF)+ soffice + 結構化摘要 |
| **F TextLab** | 正規化 · s2twp · 斷句 · 錯字修復 · jieba 關鍵字 · 信件結構 |
| **G 分類** | domain(FINANCE/LEGAL/HR/TECHNICAL/SALES)· sensitivity · PII 升敏 · language · evidence M/P/Est |
| **H 治理** | BloomFilter 去重 · append-only ledger · auto-ID · per-file meta |
| **I 匯出** | json / csv / xlsx / html(Visual Lock) |

Record schema 與 DocForge 完全一致,舊 dashboard 與新前端都吃得動。

**self-test 合計 26/26 PASS**(forge 22 + server 4)。

---

## 參數統一在 JSON(SSOT,只增不減)

- `via_forge_config.json` — 路徑/環境/加速器/讀取/textlab/分類/PII/evidence/ID/ledger/server/匯出/Visual Lock/治理
- `via_forge_registry.json` — 領域關鍵字 + 敏感度 + 錯字修正表(沿用你上傳的 registry,原封不動)

引擎一律讀 JSON,**不硬編碼**。

---

## 執行

```powershell
.\VIA_Forge_Launcher.ps1          # 一鍵:裝環境 + self-test + 起後端 + 開 UI
.\VIA_Forge_Launcher.ps1 -NoBrowser
.\VIA_Forge_Launcher.ps1 -Stop    # 優雅關閉
```

不經 PS 直接跑(除錯用):
```bash
python via_forge.py --selftest              # 22/22
python via_forge.py --scan <dir> --fix --export html
python via_forge.py --caps                  # 工具能力矩陣
python via_server.py --no-browser           # 起後端
```

前端沒後端也能看:開 `ui/index.html` 按「示範資料」。

---

## 治理界線

- 只讀本機/已授權磁碟檔;不做雲端隱蔽抽取。
- Google 指標檔只解析 `export_url`,下載需 stage-2 授權連接器(Gmail/Drive OAuth2、Outlook Graph),回來的檔直接丟回引擎閉環。
- Server 綁 `127.0.0.1`;PII 偵測即升敏感度;ledger append-only、UTF-8 no-BOM;重複只標 DUPLICATE 不刪。
```

---

## via_connect.py — 授權連接器(輔)· 19/19

stage-2:只走官方 API + OAuth2 + **readonly** scope。拉下的信件/文件丟回 forge 閉環。

| 連接器 | 授權 | scope |
|---|---|---|
| Gmail | OAuth2 (client_secret.json) | gmail.readonly |
| Google Drive | OAuth2 | drive.readonly（gdoc/gsheet/gslides 官方 export）|
| Outlook | Microsoft Graph device flow | Mail.Read |
| **local_outlook** | 繼承 Windows 登入身分 (pywin32 COM) | 讀你自己收件匣，不存密碼 |

- 連接器本體無 send/delete/modify 方法（self-test 驗）
- ledger 每筆標 `AUTHORIZED_OAUTH` / `scope=readonly`
- **界線**：僅自己帳號、自己授權；不做監控規避。公司環境請透明使用、走租戶授權。

## via_pmine.py — 流程探勘/控管/SSOT(綱)· 20/20

把 forge records 轉成可管理、可探勘的產出：

- **事件日誌**：(case_id, activity, timestamp) → CSV / 極簡 XES（PM4Py 相容）
- **自演化規則**：電子業 PN/部門/優先度/期限；高頻未分類代碼 → 建議納入（append-only，只建議不自動改規則）
- **控管表**：Excel 條件格式（High 紅/Medium 黃/已完成 綠）+ 多分頁（總表 + 急件）
- **流程探勘**：相鄰重複折疊（虛擬重工過濾）+ Top-K 變體（80/20）+ DFG 直接跟隨圖（純 Python，pm4py 可選加速）
- **自演化 SSOT**：依 UID 去重 + 增量融合 + **保留手動狀態不覆蓋**（Parquet 優先，無 pyarrow 降級 JSONL）

全部優雅降級：polars→pandas、parquet→JSONL、pm4py→純 Python、win32com→缺則停用。

---

## 四引擎 + 前端 · 65/65 self-test

| 引擎 | 印 | 職責 | test |
|---|---|---|---|
| via_forge.py | 庫 | 擷取/修復/OCR/TextLab/分類/去重/帳本/匯出 | 22 |
| via_connect.py | 輔 | Gmail/Drive/Outlook/本機 Outlook 授權連接 | 19 |
| via_pmine.py | 綱 | 事件日誌/控管表/流程探勘/SSOT | 20 |
| via_server.py | — | 薄後端 API（scan/connect/pmine/export）| 4 |
| ui/index.html | — | 前端（本機來源 + 授權連接 + Dashboard + 流程探勘）| — |

## API

```
GET  /api/health · /api/config · /api/connect/status
POST /api/scan · /api/connect/pull · /api/pmine · /api/export · /api/shutdown
```

## 執行

```powershell
.\VIA_Forge_Launcher.ps1        # 一鍵,四引擎 self-test 全跑
```
```bash
python via_pmine.py --scan <dir> --context Electronics --control --mine --ssot
python via_connect.py --status
```

## via_status.py — 詳細矩陣總覽(rich)

一眼看完整個系統狀態,結構化呈現:

```bash
python via_status.py            # 完整 rich 矩陣
python via_status.py --test     # 順便實跑四引擎 self-test(有實測數)
python via_status.py --plain    # 強制純文字(無 rich 環境)
```

顯示:引擎陣列(印/職責/self-test)· 工具能力矩陣(分組 ✓/✗)· 支援格式家族(39 副檔名)· 連接器狀態 · 分類 Registry · SSOT 路徑 · 治理旗標。缺 `rich` 自動降級純文字。

## via_sink.py — 多重格式持久化(儀)· 13/13

作業中用 JSON;收尾匯出到多重 sink:

| 格式 | 引擎 | 治理 |
|---|---|---|
| JSON | 原生 | 人讀快照 |
| Parquet | polars→pandas+pyarrow | 列式壓縮 |
| **DuckDB** | duckdb | **顯式匯出 sink,append-only upsert(依 doc_id,不刪)**;與唯讀掃描分離,不在掃描中途寫 DB |
| CSV | csv | UTF-8-SIG,Excel 友善 |
| XLSX | pandas→openpyxl | 表單 |
| HTML | forge | Visual Lock 報告 |
| Google Sheet | — | 產出 upload-ready xlsx;或設定 spreadsheets 寫入授權後推送自己的 Sheet |

缺套件自動降級。DuckDB 為顯式交付物,尊重 `no_db_write`(掃描不寫 DB)。

## 利害關係人系統(綱 · via_pmine 內)

從 records 的 email_structure 自動萃取:參與者/組織 → 統計互動頻率、關聯領域與單號、推斷角色(品保/研發/採購/製造/供應商/客戶)、計算影響力(High/Medium/Low)。`VIA-STK-{blake2s}` ID,append-only registry。

## 五引擎 + 前端 · 86/86

| 引擎 | 印 | test |
|---|---|---|
| via_forge | 庫 | 22 |
| via_connect | 輔 | 19 |
| via_pmine | 綱 | 28 |
| via_sink | 儀 | 13 |
| via_server | — | 4 |

前端字級已縮小為專業緊湊風;新增多重匯出列與利害關係人面板。

## via_panorama.py — 全景分析(觀)· 19/19

把 Tony 一貫的「熟悉功能」整合進統合層：

**A. Dragon-9 九維風險引擎**（權重和=25，分數域 25–75，五帶 SAFE/LOW/MED/HIGH/CRITICAL）
套用到文件治理風險：PII 曝露 / 敏感度集中 / 不可讀 / 重複 / 未分類 / 低信心 / 證據完整 / 覆蓋缺口 / 未知黑箱(D9 權重最高 5)。governance rules：HIGH/CRITICAL→強制 sequential、禁 parallel、要求多源查證；D9 黑箱 medium+→停輪不碰。

**B. 證據誠實分層** V/M/P/Est/Syn；缺值標 NeedsFetch，絕不捏造；Syn 信心硬上限 59。

**C. 全景三輪自我稽核** comprehensive→sequential→polish，每輪跑全引擎 self-test + config/registry gate，回歸閘（輪間問題數不得增加），Parse=0 gate。

**D. 全景矩陣報告**（Visual Lock HTML，觀印，判天地之美析萬物之理）。

## 六引擎 + 前端 · 105/105

| 引擎 | 印 | 職責 | test |
|---|---|---|---|
| via_forge | 庫 | 擷取/修復/分類/去重/帳本/匯出 | 22 |
| via_connect | 輔 | 授權連接器 | 19 |
| via_pmine | 綱 | 流程探勘/控管/SSOT/利害關係人 | 28 |
| via_sink | 儀 | 多重格式持久化 | 13 |
| via_panorama | 觀 | Dragon-9/證據/三輪稽核/報告 | 19 |
| via_server | — | 薄後端 API | 4 |

```bash
python via_panorama.py --scan <dir>   # Dragon-9 + 三輪稽核 + 全景報告
python via_panorama.py --audit        # 只跑三輪自我稽核
python via_status.py                   # rich 六引擎矩陣
```

## Invoke-VIA-SupportiveCore-PromptInjection.ps1 — 治理式 Prompt 導入(理)

把六個 Python 支援模組(Celeritas/EnvManager/AST-Injector/RegistryCore/Runtime-Bridge/SSOT)+ Aegis 網路模組 + 三個 PowerShell 入口(NexusCore→CentralGovernance→CodexNexus)整合成**受治理的系統**。一貼可用。

**靜態優先、絕不越界**：只做靜態驗證(Python ast+py_compile、PowerShell Parser AST),**絕不 import/執行未驗證目標、不安裝、不碰網路、不改 canonical、不自動啟用 Bridge**。三個 .ps1 內容未提供 → 只驗 Parser、不假定其參數正確。

**治理鏈**：固定導入順序 · Dragon/Hydra 風險 · Accelerator SAFE profile · Network gate(缺 Aegis→DEGRADED,不宣稱完整導入)· Runtime Bridge 只做決策不啟用 · SSOT run-local overlay · 三輪(靜態→sandbox→hardening)+ 回歸閘 · Hash State Machine 冪等(重複貼上安全)· append-only 證據鏈。

**輸出**(run-local,`~\Downloads\VIA_SupportiveCore_RunLocal\<RunId>\`):16 個 JSON/CSV/HTML,含 RYG 全景矩陣、最終 Gate(READY / READY_WITH_WARNINGS / REVIEW_REQUIRED / BLOCKED)。

```powershell
.\Invoke-VIA-SupportiveCore-PromptInjection.ps1 -PromptSource "你的 prompt" -OpenReport
.\Invoke-VIA-SupportiveCore-PromptInjection.ps1 -PromptFile "C:\path\prompt.txt"
```

LL 全遵守:param 首位、無別名、無 Read-Host、無 exit/Stop-Process、ProcessStartInfo 跑 python、UTF8-no-BOM、三空白路徑錯字自動修正為 canonical。

## 治理式 Prompt 導入 — 一鍵 + 意圖偵測(本輪新增)

**一鍵入口**:
- 雙擊 `governance.bat` → 輸入 prompt → 靜態治理驗證 → 自動開 RYG 全景報告
- 或 `.\activate.ps1 -Governance -PromptSource "你的 prompt" -OpenReport`
- 或 `.\VIA_Forge_Launcher.ps1 -Governance -PromptFile "C:\path\prompt.txt"`

**Prompt 意圖偵測(證據誠實)**:`def_AnalyzePromptIntent` 掃描 prompt 是否要求網路/加速/Bridge,**誠實記錄需求**到 overlay(`def_network_required` 等),但 `*_permitted` 仍需明確 switch + Gate + Aegis 才放行。要求網路卻未授權 → 警告「需 operator 明確核准」、gate 轉 READY_WITH_WARNINGS。**記錄需求 ≠ 放行**。

實測:
| Prompt | 判定 |
|---|---|
| 「…從 TWSE 抓取…平行加速…需要網路擷取」 | network/accel_required=True · READY_WITH_WARNINGS · 警告需核准 |
| 「把郵件分類成控管表」 | 全 False · READY · 無警告 |
