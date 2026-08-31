# Veritas Universal Semantic Intelligence Plugin Engine（VUSIPE）v1.0

VUSIPE 是完全獨立、泛用、CPU-first 的語意外掛引擎。它不修改 VOFIE、VSIS、VIA 或宿主模組；任何系統只要能傳送 JSON，就能調用同一組語意能力。

## 四層閉環

1. NLP：中英文正規化、切段、關鍵字、摘要、實體、關係、行動項、向量與相似度。
2. ML：純 Python CPU online linear classifier；模型為可攜 JSON，不依賴 GPU。
3. Deep-learning：內建無下載需求的二層 `tiny-neural-cpu` 非線性向量器，並預留 ONNX Runtime、PyTorch、sentence-transformers 等 CPU backend；缺少外部套件時核心功能不中斷。
4. 知識館：SQLite 投影＋append-only audit，支援新增、去重、語意檢索、回饋與訓練樣本累積。

自適應流程為 `feedback → candidate training → evaluation → challenger/champion comparison → explicit runtime-only promotion`。訓練預設只產生 candidate；只有 `approve_runtime_promotion=true` 且評估不退步才更新 VUSIPE 自己的 champion pointer，絕不改宿主或來源。

## 最快使用

```powershell
python .\VUSIPE.py self-test
python .\VUSIPE.py capabilities
python .\VUSIPE.py --runtime-dir .\runtime invoke --request-file .\examples\request_analyze.json
```

PowerShell 單一入口：

```powershell
& .\Invoke-VUSIPE.ps1 -Mode SelfTest
& .\Invoke-VUSIPE.ps1 -Mode Invoke -RequestFile .\examples\request_analyze.json
```

## 掛到其他模組

Python 直接 Adapter：

```python
from adapter import GenericModuleAdapter

with GenericModuleAdapter("./runtime") as semantic:
    result = semantic.invoke("analyze", {"text": "要分析的文字"})
```

非 Python 模組可選：

- JSONL stdin/stdout：`python adapter.py jsonl`
- 本機 HTTP：`python adapter.py http --host 127.0.0.1 --port 8765`
- CLI JSON：`python VUSIPE.py invoke --request '{"action":"health","payload":{}}'`

HTTP 只綁本機位址為預設，提供 `GET /health`、`GET /capabilities`、`POST /invoke`。沒有自動安裝、沒有外部 API、沒有網路模型下載。

## 統一請求契約

```json
{
  "action": "analyze",
  "payload": {
    "text": "內容或改用 path",
    "top_k": 8
  }
}
```

支援 20 個動作：`analyze / normalize / segment / keywords / classify / entities / relations / summarize / actions / embed / similarity / retrieve / knowledge_upsert / knowledge_search / train / evaluate / evolve / feedback / capabilities / health`。

## 安全邊界

- 來源一律唯讀，檔案讀取前後驗證內容不變。
- 知識與模型只寫入指定 `runtime-dir`。
- Knowledge append-only；相同內容只回報 `SKIP_DUPLICATE`。
- 不支援宿主刪除、覆寫或執行來源程式的 action；未知 action 立即 `FAIL`。
- 演化只升級 VUSIPE runtime champion，不會回寫既有系統。
