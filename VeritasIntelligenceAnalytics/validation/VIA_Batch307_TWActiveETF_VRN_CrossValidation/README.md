# 批307 — 台股主動式 ETF 清單更新+VRN 三資料集多方法交叉驗證

操作員令(2026-09-02):①測試主動式台股 ETF 是否可以更新清單;
②測試 VRN 產生的 BASIC INFO / SUMMARY / FINANCIAL DATA 多方法核對無誤;
③產出 HTML U/I Matrix 報告。

## 件冊

| 件 | 角色 |
|---|---|
| `batch307_crossvalidate_core.py` | 驗證核心:甲 ETF 清單(E1–E7)/乙 BASIC INFO(B1–B7)/丙 SUMMARY(S1–S6)/丁 FINANCIAL(F1–F8),六方法道 |
| `batch307_uimatrix_render.py` | U/I Matrix 渲染器(批306 Codex 模板語言;零手寫數字,自真值渲染) |
| `Batch307_CrossValidation_Results.json` | 機讀驗證結果(schema batch307-crossvalidation-results-v1) |
| `VIA_Batch307_TWActiveETF_VRN_UIMatrix_v0100.html` | U/I Matrix 報告(自含式紀錄工件;Chromium 截圖驗收) |
| `twse_t187ap47_L_snapshot_20260902.json` | 法二獨立傳輸證跡(curl 快照,271 筆,出表日期 1150901) |

## 用法

```
python3 batch307_crossvalidate_core.py [--offline]   # 跑驗證(--offline 跳過法六實連)
python3 batch307_uimatrix_render.py                  # 再生 U/I Matrix 頁
```

## 本波結論(2026-09-02)

- **清單可更新**:FLOW_ENG023 `--refresh` 實連 TWSE OpenAPI 成功——名錄收 271 筆、
  新增 1(00409A)、核符 26、官方改正 6、總 38 檔(VERIFIED 33/候驗 5)。
  前置修補:SUP_MDL737 v0103(fetch 無 UA 遭官方 WAF 擋+擋頁毒快取自癒)。
- **三檔 A 尾衝突定奪**:官方證實批104 矩陣對映(00980A 野村/00981A 統一/00982A 群益),
  種子冊為三環錯位;三檔 D 尾(00982D/983D/984D)冊載名≠官方名,官方為準改正。
- **核對結果**:23 PASS / 4 WARN / 1 FAIL。唯一 FAIL=真缺陷 B7:三列會議簡報
  檔名年份「2026」誤植入 Ticker 欄(候修,不改正身留痕)。
  SUMMARY 雜湊鏈全合(sha256 重算=指標宣告);FINANCIAL 189 事實列
  value↔raw_value 零漂移。

誠實界線:候驗 5 檔上市/上櫃/興櫃名錄皆查無——不定奪;正典 parquet 在工作站,倉內不在。
