# VIA Matrix Governance v0105 — 現況與安全接入

日期：2026-11-06。這是 **Preview-only 治理工作台與本機候選 add-on**，不是五個 production 引擎的整批更新／啟用。VCGC、VDF、VRN、VQG、VAP 保持獨立；既有 VCGC installer、EnvManager、InstallGate、Token 工具均未改寫。

## 1. 新 LOGO 與介面

使用您上傳的「繁茂金色生命之樹品牌標誌.png」，只作等比例縮小，保留 RGBA alpha、原色與完整圖文，沒有加底色、邊框、陰影或重畫。`data/brand_asset_v0105.json` 保存原件及嵌入 PNG 的 SHA-256。Logo 高度由 ResizeObserver 設為 Header 三行文字容器實際高度的 1.08 倍；三個視口驗收允許 1.05–1.12 倍，圖文不可重疊。固定 ENG049 三個標題仍保留。

左、中、右面板有固定標題，左右可獨立隱藏／恢復，偏好只存在 localStorage。資料表採 50 列分頁與可讀寬欄，中央內部橫向捲動；桌機／平板鎖住前三欄，手機只橫向鎖燈號，以免其餘資料被遮住。CSV 防公式注入；JSON／CSV 匯出不回寫來源。

## 2. 九個矩陣與燈號

所有矩陣都以 **燈號 → 編號 → SSOT名稱** 開頭，以 **錯誤詳細說明** 結尾。點選列或鍵盤 Enter／Space 可在右側查看未截短的欄位。紅燈以 2.8 秒慢速 pulse；黃／綠不動畫。系統設定 reduced-motion 時全部停止動畫。

| 矩陣 | 內容與限制 |
|---|---|
| 系統 | 五個獨立 peer，加一個 VIA 本機 review 工作台。RED 是正式整合閘未過，不表示已有歷史成功的獨立引擎突然失敗。 |
| 參數 I/O | 原始 Python 函式參數、CLI 宣告、return 表達式、JSON 葉節點、XLSX 摘要，以及候選 Token／MCP 契約。`JSON_LEAF_IO` 不等於 native engine CLI；return 表達式不等於已驗證輸出。 |
| 指令 CLS-FNC-LIB | 原始來源路徑／ZIP member、名稱、版本、SHA、行號、qualname、AST 位階與候選 locator。另有 Token／MCP 候選工具定義。 |
| 全部文件 | 30 份明確輸入、6 個不同 SHA 的 ZIP、129 個 ZIP 成員；159 個檔案／成員紀錄。重複 ZIP 保留 aliases，不重複解析內容。 |
| 環境工具 | Tony-NB／connector 觀測、隔離 PyArrow lock，以及 402 個原始 LIB 宣告。LIB 宣告不代表已安裝、可 import 或相容；未觀测依賴是 YELLOW。 |
| 衝突 | 舊 replacement 政策、VQG 名稱、VAP helper／pure-render 界線、上游 fingerprint 綁定與其他静态待核對項。 |
| SSOT／REGEX／同義字政策 | 來源條款、regex／alias 舉證與當前 owner 限制。金融資料必須從 VDF／Database 流向 QuantGuard；QuantGenerator 不會被悄悄合併為同一 registry identity。 |
| 測試輸出驗證 | 本輪實跑、上傳歷史 QA 與 NOT_RUN 分列，不讓 parent PASS 推導每個函式／參數都通過。 |
| VAP 需求 | 完整保存 29 FR、23 NFR、20 VOM，共 72 條；文字規格不是已完成實作或效能驗收。 |

**GREEN** 只表示列明 scope 的證據成立，例如檔案可安全解析或某組本機 fixture 通過。**YELLOW** 是候選、宣告、未知或待驗證。**RED** 是阻擋／衝突／失敗。零解析錯誤不等於零治理阻礙。

## 3. AST 編號位階與登錄意義

原始附件中有 20 份 Python source 經 `ast.parse`；沒有 import／執行這批來源。Python 的階層包括：

```text
FILE（來源檔案及 SHA）
 ├─ LIB（Import / ImportFrom 宣告）
 ├─ CLS（ClassDef）
 │   └─ FNC（FunctionDef / AsyncFunctionDef）
 │       ├─ PARAM（參數、註記、default；含 self / args / kwargs 等）
 │       └─ OUTPUT_EXPRESSION（return 的靜態表達式）
 └─ FNC（模組層函式；亦可能含巢狀函式）
```

原始 AST 定位矩陣包含 41 CLS、1,259 FNC、402 LIB、2,583 PARAM、1,482 OUTPUT_EXPRESSION 與20 FILE紀錄。`CMD-…` 是此盤點列 ID；`AST-…` 是來源身份／qualname／kind 所導出的候選 locator。行號、end_line、hierarchy 和 source SHA 是定位證據。**這些不是正式 SSOT 號冊，不是自動 AST 注入，也不是100% line／branch／path／runtime coverage。** JavaScript／TypeScript／PowerShell 若以文字定位則明示 `STATIC_TEXT_NOT_AST`。

候選工具在 `scripts/`，固定 TokenEngine 在 `engines/tooling/via_agent_os_unified_readonly_hardened.py`；來源位置以 portable path 和 ZIP member 表達。`attachments/...` 是上傳來源身份，並非 Tony-NB 安裝位置；此 add-on 不包含所有原始上傳包，也不將其中舊版引擎當最新部署檔案。owner 正式註冊位置、真正部署根、ACL、environment lock 與實機收據目前均未核實。

## 4. 本輪實跑證據

| 執行 | 結果 | 真實範圍 |
|---|---:|---|
| 靜態 intake 安全／AST 白箱 | 28/28 | 原始附件及合成安全案例；需要原始 uploads，portable runner不假稱重新執行這28項。 |
| 治理 UI builder 白箱 | 24/24 | 新builder、新LOGO SHA、strict JSON、CSP、固定欄位、fixture隔離、scope。 |
| MCP protocol 白箱 | 31/31 | 真正本機 stdio 子程序、initialize/list/call/EOF、固定 inventory SHA與Token subprocess。不是全 MCP 認證。 |
| v0105 stage 安全白箱 | 12/12 | 外部SHA、CRC、精確members、Windows路徑、links、false flags、缺rootSTOP、新candidate零覆寫。 |
| Token CLI | 5/5 | 本機1.0.2-hardened；provider calls=0，非正式VCGC工具啟用。 |
| 三裝置治理UI | 85/85 | 1440×900、768×1024、390×844，九矩陣、最後錯誤欄、LOGO高度／SHA、側欄、sticky、可讀寬欄、CSV、CSP、零外連／零頁面錯誤／零viewport overflow。 |
| VAP v027 新隔離副本 | 19/19 | 18 Python靜態／runtime HTTP／SQLite fixtures，1 Node module suite；30 manifest pins。未執行aggregate installer、sealer或browser UAT。 |
| 上傳Matrix reference | 63/63 | 先保留原環境60/63失敗，再在全新scratch venv锁PyArrow26.0.1及wheel SHA重測。只用loopback fixture，不修VCGC環境。 |

Matrix reference 的 143 次 network attempts 都屬本機 loopback fixture，external fixture calls=0；128行壓測約32.16行／秒，結束owned worker=0、active connection=0、fixture已停止。這不是遠端抓資料或native VDF效能。CSV四筆精確資料與manifest三個hash另有獨立讀回證據；Parquet roundtrip由其selftest執行。正式 Go-Live 固定false。

VAP本輪驗證只限新candidate：它確實有可讀原生runtime與契約。`--seal-source`會改manifest，故不能把整個helper概稱唯讀。刷新／catalog流程保留VQG輸出，但仍有可呼叫的TA-Lib和缺值修補helper；不能認證整個模組完全pure-render。VQG契約內`producerInputs`與布林upstreamEvidence不能取代VDF contractId／source ID／fingerprint的獨立綁定。這些限制留在矩陣，不刪除或替換既有功能。

## 5. MCP／Token 本機候選接入

既有 Manus 通用 MCP 已用於此次工作；目前查不到可用的 VCGC 專屬 connector/server。此輪另完成 `scripts/via_governance_mcp_v0105.py`，提供三個固定本機工具：

- `via_status`：候選scope與未正式登錄狀態。
- `via_inventory_query`：必須給 `package_root` 與 `inventory_sha`，最多返回50列；只查固定原始inventory，不含UI supplemental evidence merge。
- `via_token_prepare`：只处理caller傳入文字；以SHA-pinned TokenEngine subprocess執行，1MiB輸入上限、最多400行，預設不允許有損抽取。

啟動adapter的實際CLI**不接受額外參數**：

```powershell
py -3 -B .\scripts\via_governance_mcp_v0105.py
```

這是 newline JSON-RPC stdio，不是HTTP server；應由支援stdio的本機MCP client傳送initialize／initialized／tools call。它在stdin EOF後退出，無 daemon、OAuth 或provider calls。`package_root`是`via_inventory_query`的tools/call參數，**不是CLI flag**。目前protocol固定2025-06-18 subset，不宣稱最新／完整MCP相容。

Token估算是 heuristic，不是provider tokenizer／billing。JSON compact只有strict JSON語義roundtrip成立時才稱lossless；query抽取要明確opt-in `allow_lossy`。秘密遮罩是部分模式，caller仍不得傳入敏感資料。政策永遠是 **既有VCGC工具 + 新候選工具 + VIA System Atlas**，不是替換。

## 6. 一條命令與三個同步步驟

1. **分析準備**：讀固定inventory/evidence與source pins，先驗ZIP／來源／政策／缺件；不執行原始附件或安裝依賴。
2. **安全執行**：重建到新的output，依固定allowlist跑UI/MCP/stage/Token與本機UI；不啟動peer engine／registry／DB／Git同步。
3. **驗證與下一步**：收據核對重建HTML一致、source bytes未改、scope与數量；正式owner／environment／endpoint／contract檢查留待Tony-NB可操作後。

在已審閱、已stage的candidate根執行：

```powershell
py -3 -B .\scripts\run_governance_checks_v0105.py --out .\artifacts\local_check_v0105_001
```

需先有可用Python、Node、Chromium及Playwright；缺件會STOP，不調用pip或VCGC installer。Linux Sandbox已實跑，Windows不保證當下環境可跑；應先讓既有VCGC EnvManager做owner核准的inventory／plan，再提供相容lock。輸出必須新名稱，既存輸出會STOP；不要把output設在engines/data/public/scripts/tests。

## 7. Tony-NB candidate stage，不是部署

```powershell
$Root = 'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics'
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'STOP：既有owner根不存在；不自動建立' }
$Zip = 'C:\Downloads\VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip'
$Sidecar = "$Zip.sha256"
$Expected = ((Get-Content -LiteralPath $Sidecar -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$Actual = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Actual -ne $Expected) { throw 'STOP：外部SHA不符' }
# stager應先由這次交付的獨立腳本取得並審閱，不先執行ZIP內的其他檔案。
py -3 -B .\stage_governance_addon_v0105.py --zip $Zip --sha256 $Expected --root $Root
```

stager在既存root下新增`VIA_Review_Candidates\v0105_<UTC>`，驗完所有member與政策後才stage；不跑任何engine。外部SHA必须来自此交付sidecar／最終外部驗證收據，而不是archive自己聲稱。`SHA256SUMS`覆蓋payload，manifest/SUMS本身由外部archive SHA保護，避免self-hash cycle。此包是治理／Token／MCP review add-on，非全部native引擎更新包，沒有替代UCC SYNCHRONIZER／industry profile套件。既有v0104.1 archive未改。

目前Tony-NB狀態unavailable／workspaces=[]，VCGC endpoint／owner SSOT／實機環境及DB未核實。不能把此Sandbox stage／fixture PASS改成正式SSOT登錄、真機啟用、GitHub-PC一致性或production release。
