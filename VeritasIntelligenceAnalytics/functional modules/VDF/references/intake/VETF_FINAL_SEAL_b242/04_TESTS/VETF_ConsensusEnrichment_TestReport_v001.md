# VETF Consensus Enrichment Adapter v001｜測試報告

## 測試結論

**PASS：16／16；FAIL：0；ERROR：0。**

本版已能在 sandbox candidate 模式完成：主動式台股 ETF 最新持股選取、台股 ticker 正規化、最新 Adj Close as-of join、FactSet／YFinance 目標價對接、FactSet N／N+1／N+2 EPS 對接、Forward P/E、品質旗標、來源稽核與 Append-Only 輸出。

正式 canonical 寫入仍維持鎖定，未執行任何來源修改、正式資料庫寫入或覆寫。

## 測試環境

| 項目 | 結果 |
|---|---|
| Python | 3.12.13 |
| 核心測試框架 | `unittest` |
| Pandas | 2.2.3，可偵測 |
| Polars | 未安裝 |
| PyArrow | 未安裝 |
| DuckDB | 未安裝 |
| 核心 CSV／JSON | 已實際驗證 |
| Parquet／DuckDB | 選用後端缺少，正確標記 `SKIPPED_MISSING_BACKEND` |

目前容器的 Pandas／NumPy 版本不代表使用者 Windows `via_core_312` 的正式相依版本；正式部署仍應遵守既定環境鎖定。

## 測試矩陣

| # | 測試項目 | 結果 |
|---:|---|---|
| 1 | TWSE／TPEX ticker 正規化 | PASS |
| 2 | 每檔 ETF 僅取基準日前最新持股快照 | PASS |
| 3 | Adj Close as-of join 阻擋未來價格 | PASS |
| 4 | FactSet as-of join 阻擋未來 Consensus | PASS |
| 5 | YFinance Target 欄位別名與 Upside 計算 | PASS |
| 6 | FactSet N Forward P/E | PASS |
| 7 | FactSet N+1 Forward P/E | PASS |
| 8 | FactSet N+2 Forward P/E | PASS |
| 9 | 舊式 `EPS 2026／2027／2028` 映射 N～N+2 | PASS |
| 10 | 負 EPS、零 EPS、缺失 EPS Fail-Closed | PASS |
| 11 | 價格／Consensus 幣別不符時阻擋衍生值 | PASS |
| 12 | FactSet 與 YFinance 分欄、不跨來源平均 | PASS |
| 13 | ticker＋ISIN／公司名／Provider ID 雙重身分 | PASS |
| 14 | FactSet／YFinance 目標價差異警示 | PASS |
| 15 | Append-Only：相同跳過、不同內容拒絕覆寫 | PASS |
| 16 | JSON 端到端 Pipeline 與 manifest／CSV／JSON 輸出 | PASS |

## 公式驗證範例

測試輸入：

- 分析日：2026-06-22
- 最新可用 Adj Close：110
- 未來日 2026-06-23 價格：120，應被阻擋
- EPS N／N+1／N+2 Mean：5／6／7

計算結果：

| 欄位 | 計算 | 結果 |
|---|---:|---:|
| `fs_forward_pe_n` | 110 ÷ 5 | 22.00000000 |
| `fs_forward_pe_n1` | 110 ÷ 6 | 18.33333333 |
| `fs_forward_pe_n2` | 110 ÷ 7 | 15.71428571 |

2026-06-23 的 Future Price 與 Future FactSet Snapshot 均未進入 2026-06-22 分析結果，確認沒有 Look-Ahead Bias。

## 安全與治理檢查

| 檢查 | 結果 |
|---|---|
| 預設 `write_mode=candidate` | PASS |
| `canonical_write_enabled=false` | PASS |
| 未有 P0／P1 時拒絕 canonical | PASS |
| 未通過雙重身分時拒絕 canonical | PASS |
| 同日期不同內容拒絕覆寫 | PASS |
| 輸入檔 SHA-256 provenance | PASS |
| FactSet／YFinance 不跨來源平均 | PASS |
| 無 `eval`／`exec`／`subprocess`／刪除操作 | PASS |
| 無 DROP／DELETE／UPDATE／INSERT SQL | PASS |

## 尚未在本容器實跑的項目

1. PyArrow Parquet 實際讀寫：本容器未安裝 PyArrow。
2. DuckDB candidate table 實際寫入：本容器未安裝 DuckDB。
3. FactSet 正式 API：需要使用者既有授權與現有資料表，不在測試資料中呼叫外部服務。
4. Windows `D:\VDF\databases\` 掃描：該路徑不在目前工作區。
5. 既有 VETF／持股聚合引擎的正式函式掛接：原始 PY 尚未附上，因此本版採低耦合檔案／資料表 Adapter。

上述項目未被誤標為通過；待放入使用者 `via_core_312` 並提供實際資料表後，應執行 P0 Real-Data Gate，再決定是否進入 P1 canonical 接受。
