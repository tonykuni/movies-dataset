# VOFIE v1.4 Failure Recovery Playbook

本文件維持一般 8 stages × Top 20 failures。多點連動、可能修壞整套系統的九頭龍風險由獨立 `HYDRA_RISK_PLAYBOOK.md` 與 `config/hydra_risk_catalog.json` 管理，不混入本表。

正式 SSOT：`config/failure_catalog.json`  
契約：`veritas.vofie-failure-catalog/1.1`

## 覆蓋範圍

| Stage | Top failures | 已實作解法組 |
|---|---:|---|
| `INTAKE` | 20 | validate input、normalize path、selection dedup、five-file limit、diagnostic |
| `READER` | 20 | encoding fallback、stdlib reader、file isolation、chunking、retain original、diagnostic |
| `SEMANTIC` | 20 | fence normalization、chunking、deterministic NLP、retain original、reindex、diagnostic |
| `CONSOLIDATION` | 20 | retain original、mark duplicate、reindex、candidate-only、disable optional、diagnostic |
| `VSIS_NLP` | 20 | approved-path discovery、deterministic NLP、disable optional、retain original、diagnostic |
| `EXPORT` | 20 | new output dir、one atomic retry、safe filename、inline assets、output validation、diagnostic |
| `WINDOW_UI` | 20 | native file dialog、disable DnD、preserve state、five-file limit、diagnostic |
| `GOVERNANCE` | 20 | retain original、reindex、output validation、diagnostic、hold activation |

總數：`8 × 20 = 160`。每個 failure 展開後都包含 stage 的多個 handler IDs；不存在只有文字建議、沒有函式的 solution。

## 安全層級

1. `DRY_RUN`：復原 handler 自測；不得寫檔、不得改來源。
2. `APPLIED`：只修改記憶體狀態、新輸出目錄或候選檔。
3. `DISABLE_OPTIONAL`：只停用失敗的選用 Adapter，核心繼續。
4. `FAIL_CLOSED`：來源雜湊、內容保留、Registry 或格式契約不成立。
5. `HOLD_ACTIVATION`：self-test、user-test、handler coverage 任一失敗。

## Debug 指令

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py dependencies
python .\Veritas_OmniFormat_Intelligence_Engine.py failure-catalog
python .\Veritas_OmniFormat_Intelligence_Engine.py self-test
python .\Veritas_OmniFormat_Intelligence_Engine.py user-test
python .\Veritas_OmniFormat_Intelligence_Engine.py activate
```

## Add-only 擴充方式

新增 failure 時先新增新的 stage version 或排名，不覆寫既有 failure ID。新增 solution 時：

1. 在主 Python 以完整 `def recover_<name>(context)` 實作。
2. 登記到 `RECOVERY_HANDLERS`。
3. 在 failure catalog 的 stage `handlers` 加入 handler ID。
4. 補單元測試，驗證 dry-run `source_mutated=false`。
5. 執行 `activate`；未全綠不得宣告 ACTIVE。

## 必守不變量

- 來源：`READ_ONLY / NO DELETE / NO MOVE / NO CANONICAL MUTATION`。
- 去重：`MARK_AND_RETAIN`。
- 程式優化：`CANDIDATE_ONLY_EQUIVALENCE_GATE`。
- GUI：錯誤後保留已選檔案與參數，不隱藏例外。
- 輸出：非空目錄建立新 sibling；不得覆寫既有產物。
- SYSTEM：治理資料只進 `_system/`；ENGINE 不得偷偷產生 sidecar。
