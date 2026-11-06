# VIA_SettleAll v0110(操作員 2026-11-06「SYSTEM / FUNCTION / DESCRIPTION / MDL-ENG NAME / CLS / FNC / LIBS / ERROR & AST / STATUS · 逐步將多矩陣管理報告完善 · 先整理各系統矩陣第一欄三個燈號」)

v0109 一字不動。新增 **⑭ 模組矩陣**(在 ⑬ 之後 · ⑫ 之前):七個系統夾每個模組家族的**尾版**一列,只 `ast.parse`、不執行、不改檔。

| 欄 | 來源(只讀)|
|---|---|
| **SYSTEM**(第一欄 · 三個燈)| 該系統這輪的燈,與 ⑫ 同源:VRN-2 = ⑤ · VDF = ④ · VCGC / VCGC·支援 = ⑥ · VCGC·Agent OS = ⑨ · VQG = ⑧ · VAP ⚪;那一步沒跑就 ⚪(不冒充)|
| **FUNCTION** | 家族名(檔名去 `_vNNNN.py`)|
| **DESCRIPTION** | 模組 docstring 首行;沒有就取前 20 行第一個註解行 |
| **MDL / ENG NAME** | 尾版檔名 + **VCGC 編號**(`VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl` · 讀一次快取;沒登寫「未登號」)|
| **CLS / FNC** | 類個數 · 函式個數(含方法)|
| **LIBS** | 第三方套件(標準庫不算;VIA 內部模組另計「+N 內部」)|
| **ERROR & AST** | 語法 / 編譯錯(檔:行)· 重複頂層定義 · 無加速器橋 · 網路 import 沒網路橋 |
| **STATUS** | 只從本輪證據:VDF 用 ⑬ 自測(rc 0 🟢 · rc 2 🟡 · 其他 🔴 · 預算外 ⚪)· VCGC 用 **VCGC 自己的功能帳** `VIA_VCGC_FunctionLedger_v0100.jsonl`(家族最後一筆 lamp · 版本 · UTC 時間;帳上版 ≠ 尾版 → 🟡)· 系統入口家族用該步的燈 · 其餘 ⚪ 未實測 · 語法錯一律 🔴 |
| **上次綠** | 只增帳 `VIA_Reports/settle/VIA_ModuleMatrix_Ledger.jsonl`(綠的列每輪追加:時間 · 檔 · 版本 · VCGC 編號 · 狀態)|

輸出:`VIA_Reports/settle/VIA_ModuleMatrix_latest.json / .md(一系統一表)/ .html(一表 · 可按文字篩)`;⑫ 系統矩陣多一列「模組矩陣 ⑭」;報告 `SETTLE_latest.md` 有各系統小計表;貼回包含四檔。
自測 41 / 41(新 ㉗ 模組卡 · ㉘ 模組矩陣:尾版 / 隔離夾 / 第一欄 / 三種 STATUS 來源 / 只增帳 / 欄名)。

## 容器實跑(2026-11-06 13:57 · `--only scan,policy,vdfeng,modmatrix,matrix,report` · 沒跑 ④⑤⑥⑧⑨ 所以第一欄全 ⚪)

| 系統 | 模組尾版 | 🟢 | 🟡 | 🔴 | ⚪ | AST 錯 | 無加速器橋 | 網路 import 沒橋 | 未登 VCGC 號 |
|---|---|---|---|---|---|---|---|---|---|
| VRN-2 | 90 | 0 | 0 | 0 | 90(⑤ 這輪沒跑)| 0 | 1 | 1 | 65 |
| VDF | 98 | 83 | 9 | 6 | 0 | 0 | 0 | 0 | 78 |
| VCGC(CGC_)| 283 | 278 | 0 | 4 | 1(MCP 伺服器:功能帳還沒這家族)| 0 | 0 | 3 | 0 |
| VCGC·支援 | 33 | 0 | 0 | 0 | 33 | 0 | 0 | 1 | 1 |
| VCGC·Agent OS | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |
| VQG | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| VAP | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| **合計** | **508** | **361** | **9** | **10** | **128** | **0** | **1** | **6** | **144** |

⑭ 耗時 5 秒(508 檔 AST)。⑬ 本輪 98 家族 🟢 83 🟡 9 🔴 6(292 秒 · 比上輪少 7 紅 = 容器環境差異,不是程式變了)。

### 這輪 ⑬ / ⑭ 指出的事(VDF 自己的 · 本檔只讀不改)

- 🔴 `VDF_ENG049_FiveDayFetch_v0100`(八檢 FAIL 1)· `VDF_ENG053_ParamEngineMap_v0102`(十一檢 FAIL 1)· `VDF_ENG082_FinStatements_v0107`(4/5)· `VDF_MDL008_FetchSystem_v0107`(5/6 · v0106 PASS)· `VDF_ENG051_ActiveTWETF_Holdings_v0103`(duckdb ResourceInUse:connection 還有未取完的結果)· `VDF_MDL001_TWEquityEngine_v0100`(逾時 120 秒)。
- **`VDF_MDL001_TWEquityEngine` 自測在非 Windows 會把硬寫的 `C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\dict\1-2-TWStockData` 當成相對路徑建成一個資料夾**(容器裡出現在 `functional modules/VDF/C:\Users\…\reports\vdf_mdl001_deployment_*.json`;已刪 · 未提交)。桌機是 Windows 不會發生,但那條路徑是桌機舊家(`via_database\vdf_database` 才是 VDF 冊 v0101 的第一家)。
- VCGC 功能帳 4 個 RED 家族:`CGC_MDL095_DeckServer_v0161` · `CGC_MDL224_TestAuto_v0106` · `CGC_MDL237_NumberingSystem_v0119` · `CGC_MDL278_NumberGrant_v0100`(帳是 2026-11-01 的 · VCGC 自己的 test 會更新)。
- `VIA_AgentOS_v0102`:重複頂層定義 `build_dashboard_data / main / upgrade_dashboard_document`(後者蓋前者 · Python 合法但 MDL158 也會報 DUPDEF)+ 網路 import 沒網路橋(它自己有 fail-closed 網路閘)。
- 144 個模組家族沒有 VCGC 編號(VDF 78 · VRN-2 65 · 支援 1 = `VeritasCeleritas_v1141`):VCGC 的 `run CGC_MDL237_NumberingSystem --apply --scope <夾>` 之事,見下。

## 桌機一行(PowerShell 7 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0110";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0110.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0110.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'7CAAD8650A332FD7149CBFE05D30CF196355232E27F509A894967BEF149B674E'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

預期:③ 從 HEAD 還原 28 支 git rm 的舊版 + 1 本壞 JSON → 合併 → ④⑤⑥⑦⑧⑨ 全有燈 → ⑬ 98 引擎 → **⑭ 508 列模組矩陣(第一欄有燈)** → ⑫ 系統矩陣 → 自動開兩張 HTML(`VIA_SystemMatrix_latest.html` · 模組矩陣在 `VIA_Reports\settle\VIA_ModuleMatrix_latest.html`)→ 貼回包 `Downloads\VIA_Settle_<時間>.zip`。
