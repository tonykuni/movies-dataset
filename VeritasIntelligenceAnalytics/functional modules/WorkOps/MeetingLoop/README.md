# VIA MeetingLoop Intelligence Engine v003

## 合併內容

- v001 Transcript Restoration / Summary / Action Engine
- v002 Zero-Training Mouse-First Workbench
- SQLite append-only SSOT
- Review JSON append-only import
- Consolidated current-state export
- Failure Mode Gate framework
- JSON parameters and data contract
- Optional Parquet Bronze/Silver/Gold
- Optional DuckDB views
- N-3 / N-1 DraftOnly
- Doctor and automated self-test
- PowerShell one-entry launcher

## 能力降級

核心模式不要求任何額外安裝。

當 `pyarrow`、`duckdb` 不存在：

```text
DATA_GATE = DEGRADED
Storage = SQLite + JSONL
```

當兩者存在：

```text
Storage = SQLite + Parquet
Analytics = DuckDB Views
```

系統不會因為 Parquet 套件缺少而失去逐字稿、摘要、Action 或審核功能。

## PowerShell 7

```powershell
$Root = "$env:USERPROFILE\Downloads\VIA_MeetingLoop_Intelligence_Engine_v003"
$Runner = Join-Path $Root "Start-VIA-MeetingLoop-v003.ps1"

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

& $Runner -Mode Doctor
& $Runner -Mode SelfTest
& $Runner -Mode Process -OpenWorkbench
```

## 審核結果

在 Workbench 點擊「匯出確認結果 JSON」，再執行：

```powershell
& $Runner -Mode ImportReview
```

## 建立目前狀態

```powershell
& $Runner -Mode Consolidate -MeetingId "MTG-BUX-20260801-001"
```

## 測試

```powershell
python .\tests\test_engine.py
```

## 安全界線

- 原始來源不修改
- 正式紀錄不由 AI 自動提交
- 不自動寄信
- 不刪除事件歷史
- Owner、Due Date、Decision、Completed 必須人工確認
- 資料 schema 不合時進 quarantine
