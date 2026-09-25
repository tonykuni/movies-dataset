# VIA NLP Fusion Engine v2.1.0

VERITAS INTELLIGENCE ANALYTICS  
DISCIPLINA • PRUDENTIA • INTEGRITAS  
AI-Powered Research & Decision Intelligence Platform

本版本在 v2.0.0 的 18 階段 NLP、SQLite SSOT、證據鏈與多格式擷取上，新增兩個受治理子系統：

1. `VIA CPU/DRAM Adaptive Resource Framework v2.1.0`
2. `VIA Bilingual Financial Keyword Governance v2.1.0`

所有第三方函式庫均為本機選配：引擎不自動安裝、不呼叫雲端、不修改來源檔案。缺少套件時使用標準函式庫或保留 CSV／SQLite 輸出，不會因為非必要套件缺失而中斷。

## 一鍵 PowerShell 7

```powershell
& ".\Invoke-VIA-NLP-Fusion-OneClick-v0210.ps1" `
    -InputPath "C:\AuthorizedDocuments" `
    -OutputDir "C:\VIA_NLP_Runs\RUN_20260818" `
    -KeywordDb "C:\VIA_SSOT\VIA_NLP_Keyword_SSOT.sqlite3" `
    -NonKeywordDb "C:\VIA_SSOT\VIA_NLP_NonKeyword_SSOT.sqlite3" `
    -SsotDb "C:\VIA_SSOT\VIA_NLP_Fusion_SSOT.sqlite3" `
    -ResourceMode "BALANCED" `
    -MaxCpuPercent 85 `
    -MaxMemoryPercent 82 `
    -BatchSize 16 `
    -MaxWorkers 4 `
    -NativeThreadLimit 2 `
    -RunTests $true `
    -OpenHtml
```

`-OpenHtml` 會啟動只綁定 `127.0.0.1` 的關鍵字審核服務，使用隨機 Token，閒置 30 分鐘後自動關閉。PowerShell 不會自動關閉。

## Top 15 本機免費資源函式庫

| Rank | Library | 實際整合用途 |
|---:|---|---|
| 1 | psutil | CPU、DRAM、可用記憶體與程序 RSS 監測 |
| 2 | threadpoolctl | 限制 BLAS／OpenMP 執行緒，避免 CPU 過度訂閱 |
| 3 | joblib | 受控本機平行 SHA-256 前置處理 |
| 4 | diskcache | SSD 解析快取；降低重複解析與 DRAM 常駐 |
| 5 | orjson | 低負擔 JSON 位元組序列化 |
| 6 | xxhash | 非權威快速指紋；SHA-256 仍是稽核權威 |
| 7 | zstandard | JSON 與磁碟溢寫壓縮 |
| 8 | lz4 | zstd 不可用時的低 CPU 壓縮路徑 |
| 9 | polars | 欄式資料框與 Parquet 匯出 |
| 10 | pyarrow | Polars 不可用時的 Parquet 後備 |
| 11 | duckdb | 受控記憶體與本次執行資料夾 SSD 溢寫分析 |
| 12 | tqdm | 終端批次進度 |
| 13 | charset-normalizer | 編碼偵測與解碼品質證據 |
| 14 | ftfy | Mojibake／Unicode 修復 |
| 15 | RapidFuzz | C++ 最佳化模糊相似度輔助 |

若要手動安裝全部選配套件：

```powershell
python -m pip install -r ".\requirements-local-free.txt"
```

引擎本身不會執行上述安裝命令。

## 動態 CPU／DRAM 行為

- `CONSERVATIVE`：縮小批次與工作數，適合低 DRAM 電腦。
- `BALANCED`：預設；依 CPU／DRAM 壓力縮小批次，並限制原生執行緒。
- `PERFORMANCE`：資源正常時放大批次，但仍受上限與 Fail-Closed 政策限制。
- DRAM 或 CPU 進入 `HIGH`／`CRITICAL` 時，執行垃圾回收、降低批次／工作數並記錄壓力事件。
- SSD 暫存只建立在本次輸出資料夾 `_resource_runtime\ssd_spill`，不刪除舊執行資料，也不觸碰來源檔案。

## 五大中英文金融關鍵字領域

- 全球金融市場／Global Financial Markets
- 產業分析／Industry Analysis
- 總體經濟／Macroeconomics
- 地緣政治／Geopolitics
- 財政收支／Fiscal Balance

擷取結果同時包含受治理雙語詞庫命中與待審候選詞。每個 HTML 候選詞是獨立方框，右上角有 `×`：

1. 以本機審核服務開啟 HTML：按 `×` 後立即追加寫入 `VIA_NLP_NonKeyword_SSOT.sqlite3`。
2. 直接開啟靜態 HTML：按 `×` 後先保留於瀏覽器本機儲存，按「匯出離線否決決策」下載 JSON。
3. 下次執行加入 `-KeywordReviewPath`，即可匯入離線決策並追加寫入非關鍵字資料庫。
4. 後續擷取會先載入非關鍵字資料庫，已否決詞不再成為候選關鍵字。

```powershell
& ".\Invoke-VIA-NLP-Fusion-OneClick-v0210.ps1" `
    -InputPath "C:\AuthorizedDocuments" `
    -OutputDir "C:\VIA_NLP_Runs\RUN_20260819" `
    -NonKeywordDb "C:\VIA_SSOT\VIA_NLP_NonKeyword_SSOT.sqlite3" `
    -KeywordReviewPath "C:\Users\tonyk\Downloads\VIA_NLP_Keyword_Review_Decisions.json" `
    -OpenHtml
```

非關鍵字資料庫採 Append-Only 註冊與 SHA-256 稽核鏈；重複否決為冪等操作，不會重複寫入。

## 主要輸出

- `VIA_NLP_Fusion_Result.json`
- `VIA_NLP_Fusion_Result.json.zst`／`.lz4`／`.gz`
- `VIA_NLP_Fusion_Command_Center.html`
- `VIA_NLP_Resource_Evidence.json`
- `VIA_NLP_Financial_Keyword_Candidates.csv`
- `VIA_NLP_NonKeyword_Registry.csv`
- `VIA_NLP_NonKeyword_SSOT.sqlite3`
- `VIA_NLP_Fusion_SSOT.sqlite3`
- `VIA_NLP_Keyword_SSOT.sqlite3`
- 選配 Parquet 與 `VIA_NLP_Analytics.duckdb`

## 直接執行 Python

```powershell
python ".\via_nlp_fusion_engine.py" `
    --input "C:\AuthorizedDocuments" `
    --output "C:\VIA_NLP_Runs\RUN_20260818" `
    --non-keyword-db "C:\VIA_SSOT\VIA_NLP_NonKeyword_SSOT.sqlite3" `
    --resource-mode BALANCED `
    --max-cpu-percent 85 `
    --max-memory-percent 82 `
    --batch-size 16 `
    --max-workers 4 `
    --native-thread-limit 2
```
