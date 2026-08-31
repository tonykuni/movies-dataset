# VUSIPE v1.0 測試報告

測試日期：2026-08-31  
最終 Gate：**PASS**

| 驗證項目 | 結果 |
|---|---:|
| Python unit／integration | 26 / 26 PASS |
| 內建 self-test | 9 / 9 PASS |
| Python compile | PASS |
| JSONL Adapter | PASS |
| Wheel build／隔離安裝後 self-test | PASS／9 of 9 |
| Capability actions | 20 / 20 registered |
| CPU embedding backend | hashed-cpu PASS |
| Tiny neural CPU backend | two-layer／64 dimensions PASS |
| NLP 中英文混合 | PASS |
| 知識 append／duplicate skip／search | PASS |
| ML train／evaluate | PASS |
| Evolution candidate-only default | PASS |
| Explicit runtime-only promotion | PASS |
| File source immutability | PASS |
| Unknown action fail-closed | PASS |

## 重要限制揭露

- 本次已實際驗證的是標準函式庫 CPU backend；不需要 GPU。
- ONNX Runtime、PyTorch、sentence-transformers、scikit-learn 為可選未安裝 Adapter，不宣稱已執行。
- 內建 tiny-neural backend 是固定二層非線性 CPU 向量投影；適合離線相似度與小型知識檢索。大型語意模型可日後透過相同 embedding contract 插入，不改宿主接口。
- 自動演化不代表無條件自動上線：candidate 必須通過 evaluation 且收到明確 runtime promotion 核准。

## 結論

VUSIPE 可獨立執行，也能以 Python、CLI、JSONL 或 localhost HTTP 外掛到其他模組。測試過程沒有修改既有 VOFIE、VSIS、VIA 或輸入來源。
