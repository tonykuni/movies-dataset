# VOFIE v1.4 九頭龍（NoHydra）Top-20 Risk Playbook

契約：`veritas.vofie-hydra-risk-catalog/1.0`  
ST：`ST-HYDRA`  
模式：`REVIEW_ONLY_DRY_RUN`  
核心原則：canonical source read-only；Runtime Copy proposal-first；高風險一律 `HOLD`。

九頭龍風險是「一個修正會同時牽動多個引擎、Registry、環境、程序或寫入者，並可能擴散成系統性破壞」的風險。它獨立於一般 8 stages × Top 20 failures，不共用判定責任。

## Top 20

| ID | 可能失敗原因 | Breaker | 多重解決方案摘要 |
|---|---|---|---|
| HYDRA-F01 | 多寫入者共改 canonical | Single-writer lease | 唯一 MotherRoot；Runtime Copy；順序核准單一 commit |
| HYDRA-F02 | SSOT／Registry authority 重複 | Authority uniqueness | 選 canonical；其餘 alias；hash-chain 記錄 |
| HYDRA-F03 | 循環相依與互相回呼 | Cycle breaker | 提升 interface；切斷 reverse import；事件回傳 |
| HYDRA-F04 | Launcher／Runner 遞迴自啟 | Re-entry token | 不可重入；controller/worker 分離；child process 預設封鎖 |
| HYDRA-F05 | Thread／worker 爆量 | Concurrency cap | 全域 4；fixer 2；超額轉順序 queue |
| HYDRA-F06 | 不同 Lane 共寫相同路徑 | Lane-local staging | 隔離 staging；contract payload；單一整合器 |
| HYDRA-F07 | Registry／Pointer 過期漂移 | Pointer freeze | Target/hash 驗證；hash pin；last-known-good |
| HYDRA-F08 | 跨環境版本／契約漂移 | Environment isolation | Fingerprint；Adapter negotiation；不相容 HOLD |
| HYDRA-F09 | 部分寫入形成半成品 | Atomic commit | Temporary→replace；新 run；manifest 最後 seal |
| HYDRA-F10 | 無限重試／Retry storm | Retry breaker | Retry budget；jitter backoff；同錯誤開 breaker |
| HYDRA-F11 | 缺 Circuit Breaker | Bulkhead isolation | 每 Adapter breaker；隔離 lane；fallback／HOLD |
| HYDRA-F12 | 輸入／queue／記憶體無上限 | Size gate | Byte cap；bounded queue；chunk + checkpoint |
| HYDRA-F13 | 自動安裝污染 Base | Detect-only | Lane 環境；禁止 PATH mutation；NOT_INSTALLED fallback |
| HYDRA-F14 | Import／載入產生副作用 | AST no-import | AST-only；副作用移入函式；main guard |
| HYDRA-F15 | 外部 API／網路 fan-out | Network blocked | Fixture；request dedup；rate limit + checkpoint |
| HYDRA-F16 | DB 寫入無交易／冪等 | DB write lock | Transaction；rollback；run_id + grain key |
| HYDRA-F17 | Canonical hash／audit chain 破裂 | Integrity gate | 立即 HOLD；保存差異；由已驗來源重建 Runtime Copy |
| HYDRA-F18 | AI／Auto-fix 直寫來源 | Candidate-only | Proposal；等價測試；人工核准可回復變更 |
| HYDRA-F19 | 沒有 Rollback／last-known-good | Rollback-ready gate | Pre-snapshot；manifest；restore dry-run |
| HYDRA-F20 | 未 post-test 就 Activation | Activation hard gate | Hydra/self/user/recovery 全 PASS；每輪 post-scan；三輪後 HOLD |

每個項目的完整 cause、detectors、breakers、至少三個 solutions、SOP 與 never-again control 都在 `config/hydra_risk_catalog.json`。

## 三輪上限

1. Round 1 — `PANORAMA_READ_ONLY`：只盤點 evidence、ownership、dependency、write-set 與 hash。
2. Round 2 — `PARALLEL_SAFE_PROPOSAL`：最多兩個 fixer，只產生互不共寫的提案。
3. Round 3 — `SEQUENTIAL_DEPENDENCY_REVIEW`：有依賴的提案依序審查；剩餘高風險一律 HOLD／人工處理。

每輪後必須重新 post-scan。不可因達到第三輪而放寬 Gate。

## 使用方式

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py hydra-audit `
  .\engine.py .\launcher.ps1 `
  --report .\Veritas_VOFIE_HYDRA_RISK_AUDIT.json

& ".\Invoke-Veritas-VOFIE.ps1" -HydraAudit `
  -HydraTargets @(".\engine.py", ".\launcher.ps1")
```

偵測到任何 Hydra evidence 時，命令以 `HOLD` 結束；報告會列出 risk、evidence、breaker、solutions 與 SOP，但不執行修復、不啟動程序、不連網、不寫來源。
