# VIA HTML Bridge Starter

這是一個可直接執行的本機橋接範本，用於把既有 Python、PowerShell 或命令列引擎銜接到 HTML 操作介面。

## 核心資料流

```text
HTML / JavaScript
      │ fetch(JSON)
      ▼
FastAPI Gateway（127.0.0.1:8765）
      │
      ├─ engine_registry.json：白名單與路由
      ├─ Job Manager：背景工作、狀態、結果
      └─ Adapter
           ├─ python_module：直接 import 現有函式
           └─ process：呼叫 Python／PowerShell／EXE
```

HTML 不直接存取本機 Python、PowerShell、Parquet 或資料夾。所有操作先經由本機 API，避免 `file://`、瀏覽器權限、CORS、任意命令執行及路徑外洩問題。

## 啟動

在 Windows PowerShell 7 執行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\Start-VIA-HTML.ps1
```

瀏覽器會開啟：

```text
http://127.0.0.1:8765/
```

停止：

```powershell
.\Stop-VIA-HTML.ps1
```

也可直接啟動：

```powershell
python -m pip install -r requirements.txt
python VIA_HTML_Gateway.py
```

## 將既有 Python 函式接入

現有引擎最好提供單一入口：

```python
def run(payload: dict) -> dict:
    action = payload["action"]
    params = payload["params"]
    return {"ok": True, "action": action, "params": params}
```

在 `engine_registry.json` 新增：

```json
{
  "my_engine": {
    "label": "我的引擎",
    "description": "既有 Python 模組",
    "adapter": "python_module",
    "module": "engines.my_engine",
    "function": "run",
    "timeout_seconds": 1800
  }
}
```

模組必須能從本專案目錄或 Python Path 匯入。

## 將既有 Python CLI 接入

若原程式只能從命令列啟動，可在註冊表使用 `process`：

```json
{
  "my_legacy_python": {
    "adapter": "process",
    "command": [
      "{python}",
      "C:\\Path\\To\\my_engine_adapter.py",
      "--via-input",
      "{input}",
      "--via-output",
      "{output}"
    ],
    "timeout_seconds": 3600
  }
}
```

Gateway 會將請求寫到 `{input}`，既有程式完成後將 JSON 寫到 `{output}`。可參考 `examples/legacy_python_engine.py`。

## 將既有 PowerShell 接入

```json
{
  "my_powershell": {
    "adapter": "process",
    "command": [
      "{pwsh}",
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      "C:\\Path\\To\\my_adapter.ps1",
      "-ViaInput",
      "{input}",
      "-ViaOutput",
      "{output}"
    ],
    "timeout_seconds": 3600
  }
}
```

可參考 `examples/legacy_powershell_engine.ps1`。

## HTML 呼叫契約

建立工作：

```http
POST /api/jobs
Content-Type: application/json
```

```json
{
  "engine": "demo",
  "action": "run",
  "params": {
    "ticker": "2330.TW",
    "date_start": "2026-01-01"
  }
}
```

查詢工作：

```http
GET /api/jobs/{job_id}
```

狀態值：`queued`、`running`、`succeeded`、`failed`。

## VIA 模組建議路由

```json
{
  "vdf": {"action": "fetch/update/query"},
  "vrn": {"action": "extract/normalize/summarize"},
  "vap": {"action": "plot/export/stack"},
  "grp": {"action": "classify/validate/index/backtest"},
  "vetf": {"action": "universe/holdings/analyze"}
}
```

前端只傳 `engine + action + params`；資料來源、檔案路徑、DuckDB、Parquet 與模組相依關係留在後端 SSOT 管理。

## 測試

```powershell
python -m pytest -q
```

目前測試涵蓋：健康檢查、引擎清單、Python 模組、舊 Python CLI、未註冊引擎拒絕。

## 重要限制

1. 不要用瀏覽器直接開啟 `ui/index.html`；必須從 `http://127.0.0.1:8765/` 開啟。
2. 不要讓 HTML 傳入任意程式路徑或命令；只能使用 `engine_registry.json` 白名單。
3. CPU 密集或長時間引擎優先採 `process` adapter，避免阻塞 Gateway。
4. 大型結果不要直接塞入 JSON；建議後端輸出 Parquet／CSV／PNG，API 僅回傳檔案識別碼與摘要。
5. 對外網路部署前，必須加入 Entra ID／反向代理／HTTPS／權限與稽核；本範本預設只綁定 `127.0.0.1`。
