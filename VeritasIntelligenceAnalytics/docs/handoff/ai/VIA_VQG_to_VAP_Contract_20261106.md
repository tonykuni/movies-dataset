# VQG → VAP 統一輸出契約(2026-11-06 · VQG v0106 export-vap × VAP v0302)

操作員令:「實測輸出增量 PARQUET 維護資料庫後 · VQG 擷取自資料庫檔案夾整理全部 · 無論有無加工計算 · 統一輸出資料到其他應用如 VAP · 完成全部並收尾 · 確認各系統完全獨立交互支援」。

## 0. 一句話

VDF 增量寫批次 parquet → VQG v0106 `export-vap` 只讀 VDF 庫夾 → 整理全部(目錄)+ 無加工(一票一表 SERIES)+ 有加工(一票一表 INDICATOR_RESULT)+ 連線證據(指紋)+ VAP config → VAP v0302 `--config` 一接就上(容器實測:4 張表 · 使用者流程 7/7 PASS · 雙軸圖有畫出來)。五系統各自獨立:VQG 不 import VAP · VAP 不 import VQG · 兩邊只靠檔案 + 契約(schema + SHA-256 指紋)對話。

## 1. 流向與邊界(不變)

| 方向 | 誰寫 | 誰讀 | 邊界 |
|---|---|---|---|
| VDF → VQG | VDF 引擎(ENG054 等)寫 `<db_home>/output_hub/…/tw_daily_prices_<YYYYmmdd_HHMMSS>.parquet`(每輪一個新批次 · 增量) | VQG 只讀(`VDF_DataHome_SSOT` 尾版的 db_home 或 `$env:VQG_VDF_ROOT`) | VQG 不寫 VDF 的夾(跑前跑後核對檔案清單 + mtime · 收據 `vdf_root_untouched`)· 輸出夾不准在 VDF 庫裡(`OUTPUT_INSIDE_SOURCE_ROOT` rc 2) |
| VQG → VAP | VQG v0106 `export-vap` 寫 `<VIA 根>/VIA_Reports/vqg/vap_export/vap_export_<戳>/` | VAP `--config <輸出夾>/VAP_AllInOne_v0300.config.json` 只讀 | VAP 正式輸入 = VQG(`formalInputAuthority: VQG`)· VDF 不直連 VAP(`vdf_connection_manifest.json` connections 空)· VAP 不補值不重算(`PRESERVE_VQG_OUTPUT_NO_VAP_REPAIR`) |
| 技術指標 | VQG v0104 QuantGuard 公式(三解 · 驗證)· 政策 L50 不用 TA-Lib | — | `taLibPolicy: CALCULATE_ONLY_NO_FETCH` · `pricePolicy: ADJUSTED_PRICE_ONLY` |

增量批次:同一張表多個時間戳批次(除權息後還原價重算 → 同日值不同),`--snapshots latest`(export-vap 預設)只取最新一份;被取代的檔列在 `vqg_vdf_catalog.json`(`superseded: true`)與收據。

## 2. export-vap 輸出夾(`vap_export_<戳>/`)

| 檔 | 類 | 給誰 | 內容 |
|---|---|---|---|
| `vqg_vdf_catalog.json` | 整理全部 | 所有人 | VDF 庫夾每一個 parquet 一列:路徑 · 大小 · 批次戳 · 認得的欄位 · 列數 · 票樣本 · SHA-256 · 是否被新批次取代 · 讀不了 |
| `series/<票>.parquet` + `.csv` | 無加工 SERIES | VAP(一票一表) | v0105 `load_series` 原樣倒出:date · adj_close · volume · turnover…(全空的欄不列)· market · session_index · available_on · source_files · engine_version;x = date 不重複升冪 |
| `vqg_series.parquet` + `.csv` | 無加工 SERIES | 其他應用 | 全部票長表(含 ticker 欄) |
| `indicators/<票>.parquet` + `.csv` | 有加工 INDICATOR_RESULT | VAP(一票一表) | 最近 `--indicator-points`(預設 60)個交易日各跑一次 v0105 `run_local`;x = observation_date;欄 = `<指標>_<窗>_<解>`(例 `SMA_20_S1` · `RSI_14_S2` · `MACD_26_S3`)· 無效值留空 |
| `vqg_indicator_results.parquet` + `.csv` | 有加工 INDICATOR_RESULT | 其他應用 | as-of 當天快照 · 欄位 = v0104 FIELDS 23 欄(長表);`--out-dir` 下既有 `vqg_<uuid>/vqg_result.parquet`(v0104 `calc --export-dir`)一併合入去重 |
| `vqg_connection_manifest.json` | 連線證據 | VAP | schema `VIA-VQG-VAP-CONNECTION-MANIFEST/1.0` · 每張 VAP 表一筆(見 §3) |
| `vdf_connection_manifest.json` | 連線證據 | VAP | schema `VIA-VDF-VAP-CONNECTION-MANIFEST/1.0` · connections `[]`(VDF 不直連) |
| `VAP_AllInOne_v0300.config.json` | VAP 設定 | VAP | `formalInputAuthority: VQG` · 每張表一個來源(authority VQG · engine PARQUET)· allowedRoots 含輸出夾 · loopback 127.0.0.1:8765;輸出夾根另放一份永遠指最新一輪 |
| `export_receipt.json` · `SHA256SUMS.txt` | 收據 | 所有人 | 每步燈 · 每張表的 VAP U/I 閘預檢 · 全檔 SHA-256(含子夾) |

另:`<VIA 根>/VIA_Reports/vqg/VQG_ExportVAP_latest.json`(+ 時間戳副本)= VQG 自己的收據(別的系統只讀這份)。

## 3. 連線證據一筆的欄位(照 VAP v0300 的驗法 · VQG 不 import VAP)

```
contractId   VQG-SERIES-v1 | VQG-INDICATOR-v1        sourceId   VQG-SERIES-<票> | VQG-INDICATOR-<票>(= config 來源 id)
state        AUTHORIZED                               readOnly   true
engine       PARQUET(= 來源 engine)                   sourceSystem VQG
vqgVersion   v0106                                    formulaEngine v0104
datasetType  SERIES | INDICATOR_RESULT                producerInputs ["VDF"]        ticker <票>
limits       {maxInputRows 5000, maxOutputRows 100, maxWindow 252}(= v0104 上限 · VAP 只收 ≤ 這三個)
xField       date | observation_date                  fieldSemantics {每個數值欄: stableId · subject · unit · dataType · frequency · role}
dataFile     series/<票>.parquet                      dataSha256 <檔 SHA-256>        rows <列數>
upstreamEvidence {vdfAuthorized true · vdfRoot · vdfRootFrom · pricePolicy ADJUSTED_PRICE_ONLY · volumePolicy VDF_AS_IS_NO_VQG_FILL ·
                  taLibPolicy CALCULATE_ONLY_NO_FETCH · indicatorEngine "QuantGuard VQG v0104(政策 L50 · 不用 TA-Lib)" ·
                  calendarVerified (曆嚴格才 true) · calendarMode vdf|derive · snapshots strict|latest · network NONE}
authorizedAt ISO 時間
fingerprint  sha256( json.dumps(去掉 fingerprint 的整筆, ensure_ascii=False, sort_keys=True, separators=(",",":")) )
```

VAP 端 `def_vqg_evidence` 逐項驗:找 sourceId + contractId → AUTHORIZED 且 readOnly → sourceSystem VQG → engine 相同 → datasetType 在五種內 → limits ≤ 上限且 > 0 → vdfAuthorized 且 pricePolicy → taLibPolicy → 指紋重算相同;任一不過 = PermissionError = 閘失敗(v0301 起閘失敗不沿用舊快取表)。`fieldSemantics` 同時是 VAP 數值欄白名單(沒列的數值欄不畫),所以 VQG 每個數值欄都列。

## 4. 為什麼一票一表(VAP U/I 的閘)

VAP HTML U/I `validateCatalogTable`:列 ≥ 3 · 有 x · x 不重複(`DUPLICATE_TIME_KEY`)· x 升冪(`TIME_NOT_SORTED`)· 數值欄 ≥ 2(`NUMERIC_PAIR_MISSING`)· 數值欄裡非數值字串 = `INVALID_NUMERIC`(空值只警告);全部表都被拒 → 使用者流程 01 `RESPONSE_REJECTED`。
長表(多票同日 · 或指標快照同一觀測日)一定撞 x → 所以給 VAP 的是一票一表,長表另給其他應用。VQG 匯出前就用同一套規則預檢(收據 `tables[].ui_gate`),過不了的表不寫進 VAP config(燈 🟡 列原因)。

## 5. 這輪實測抓到並修掉的 VAP 缺陷(VAP v0302 · v0300 / v0301 原件不動 · UI 仍 v0301 沒改)

| # | 現象 | 根因 | 修法 |
|---|---|---|---|
| 1 | 任何帶日期欄的 Parquet 一接就 `[VAP] FAIL · TypeError: Object of type date is not JSON serializable` | `def_read_parquet`(duckdb 路)與 `def_read_duckdb` 回的列沒過 `def_normalize_rows`,DATE / DECIMAL 原樣進 catalog → 寫快取 `json.dumps` 炸 | 兩條 duckdb 路都過 `def_normalize_rows`(跟 sqlite / polars / pyarrow 路一樣) |
| 2 | VQG 指標表 X 軸變成 `request_key`(第一欄) | X 軸只靠 `DATE_FIELD_CANDIDATES` 欄名猜,連線證據的 `xField` 沒被用 | `xField` 在表的欄位裡就以它為 X(語意 X_TIME 跟著換) |

VAP 自己的既有狀況(不是這輪造成 · 內嵌 demo 也一樣 · 列給 VAP 線):U/I「執行完整測試」144 項 PASS 132 · FAIL 20(例 TEMPLATE_GOVERNANCE Embedded SHA-256 Verification「Failed To Fetch」);`optionalLibraries.pyarrow false`(容器沒裝 · duckdb / polars 都在所以不影響)。

## 6. 容器實測證據(2026-11-06 · VDF 形狀夾具 2 票 · 兩個批次 · 第二批還原價 ×0.97)

| 步 | 結果 |
|---|---|
| VQG v0105 doctor | `DERIVE_READY` · 日線檔 2 · 多批次 1 張表 · 缺 session_index / available_on / market(VDF 線出了才嚴格綠) |
| VQG v0106 selftest | 12/12 PASS(含 v0105 全部 · 零網路 · 只在沙盒寫) |
| export-vap | 5.9 秒 · 4 張表(2 SERIES + 2 INDICATOR · 60 點)VAP 閘全過 · 長表 556 / 48 列 · 併入舊快照 2 夾 · 燈 YELLOW(曆是推的) |
| VAP v0302 `--run-self-test` | PASS(內嵌 demo) |
| VAP v0302 `--once-refresh --config` | 0 錯 · 4 表 · 全 `vqgVerified true` · x = date / observation_date |
| `/api/health` · `/api/catalog` | READY v0302 · vqgGateway 2→4 筆 AUTHORIZED · vdfGateway 0 筆 |
| HTML U/I(Chromium) | 資料庫對接 → 更新所有連線 → 配對繪圖表單列 4 張 VQG 表 → `indicators_2330_TW` 雙軸 SMA_20_S1 × RSI_14_S1 畫出(60 Pts)· `series_2330_TW` adj_close × volume 畫出 · 使用者流程 01–07 PASS · 主控台 0 錯 |

## 7. 桌機指令(PowerShell 7.6.9 · 倉已拉到分支)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"
python "$r\functional modules\VQG\VQG_AllInOne_v0106.py" selftest
python "$r\functional modules\VQG\VQG_AllInOne_v0106.py" export-vap                     # VDF 庫根照 VDF_DataHome_SSOT;沒有就 --root <庫根>;--max-tickers 0 = 全部
python "$r\functional modules\VAP\intake\allinone_v0300\VAP_AllInOne_v0302.py" --config "$r\VIA_Reports\vqg\vap_export\VAP_AllInOne_v0300.config.json"
```

VAP 開在 http://127.0.0.1:8765(U/I 寫死這個埠 · 換埠 U/I 會 `ERR_CONNECTION_REFUSED`)。要嚴格綠:VDF 日線出 `session_index` / `available_on` / `market`;要更多票:`--max-tickers 0`(每票約 0.1–0.5 秒 × 指標點數)。

## 8. SettleAll v0115 接上(⑧b · ⑰ · ⑯)

- ⑧b VQG→VAP 匯出:⑧ closeout 綠 / 黃且 VDF 家在 → 跑 v0106 `export-vap --max-tickers 3 --indicator-points 20` → 收據燈;容器沒 VDF 家 ⚪。
- ⑰ VQG→VAP 串接:拿 ⑧b 的 config 跑 VAP 尾版 `--once-refresh` → 表數 = 來源數且 0 錯且全 vqgVerified 🟢。
- ⑯ 衝突偵測:跨系統 import · 同名不同內容(撞號)· 撞埠 · 工具鎖 · 鏡像夾 → `VIA_Reports/settle/VIA_Conflicts_latest.md`;⑫ 矩陣三列新增。

## 9. 獨立性與未決

- VQG v0106 不 import VAP(自測 ② 驗)· VAP v0302 不 import VQG · SettleAll 只讀兩邊收據。
- VAP 的 VDF 直連路徑(`def_vdf_evidence`)要求股票類帶 `taLibEvidence.engine == "TA-Lib"`,跟 VIA 政策 L50(不用 TA-Lib)相衝;本契約不走 VDF 直連(connections 空)所以不觸發 · 不改 VAP 這段(VAP 線自己決定)。
- 曆嚴格綠要 VDF 線出欄位(G2 範圍 · 不代改)。
