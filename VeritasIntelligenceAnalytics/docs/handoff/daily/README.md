# VIA 每日進度交接(十點一張憑證)

每天收工跑一次:`via-vcgc handoff daily`(正主 `CGC_MDL140_HandoverConsole` v0104 的 `daily` 動詞;VCGC-REQ127)。

| 點 | 讀哪裡(既有正主) | 燈 |
|---|---|---|
| ① Git SHA-16 | 本機 git(分支 · HEAD · 未提交 · stash · 對 origin/main,不 fetch) | 有未提交 / stash / 落後 = 黃 |
| ② 運行日誌 | `VIA_Reports/vcgc/events/EVENTS_YYYYMMDD.jsonl`(或 `--ledger`) | rc 2 / 失敗 = 黃 · 壞行 = 紅 |
| ③ 資料指紋 | DataFrame 鎖帳 + `--data` 夾內檔 SHA-256(資料不進 git,只記指紋) | 當日沒指紋 = 無資料 |
| ④ 模組版本 | 當日動到的版號家族 · 子系統尾版 | 就地改 / 改號 = 黃 · 刪 = 紅 |
| ⑤ Schema | 鎖帳同表 header_sha 漂移 | 漂移 = 黃 |
| ⑥ 測試 | `VIA_Reports/vcgc/TEST_latest.json` | 報告 head ≠ HEAD = 黃(過期) |
| ⑦ 例外佇列 | 當日非 OK 事件 · BLOCKED 待辦 · `--flagged` 夾 | 有件 = 黃 |
| ⑧ 暫存 | `*.sdd_bak` · `*.tmp` · OCR 快取 · `__pycache__` | 要清的只印指令(`-WhatIf` / `-print`),不刪 |
| ⑨ T+1 | `--next` 先,其餘取交接閘 pending 前 3 條 | 照交接閘燈 |
| ⑩ 清單 | 本夾 `panorama.manifest.json` | 契約不過 = 紅且不寫 |

整張燈取最差;無資料算黃(黃不是綠)。rc:GREEN 0 · YELLOW 2 · RED 1。

- 本夾(進版、極小):`panorama.manifest.json`(最新一份,自身 SHA-256)· `VIA_Daily_Handover_Ledger_v0100.jsonl`(每跑一次只增一行)。
- 本機(不進版):`VIA_Reports/handover/daily/` 的 sqlite WAL 帳(觸發器擋改 / 刪)與全量 log。
- `--dry-run` 只算只印 · `--json` 印整份 · `--verify` 驗本夾清單 · `--replay [YYYY-MM-DD]` 從本機帳重播。
- 選用函式庫(GitPython · Rich · Pydantic · DuckDB · Polars · Loguru · xxhash)在就用、不在走標準庫;清單 `toolset` 照實記,不裝套件。

設定檔(選填)`docs/handoff/daily/handover.toml`,夾路徑可帶 `{day}`、相對路徑以倉根起算:

```toml
data_dirs = ["C:/Users/tonyk/Github/movies-dataset/data/output/{day}"]
flagged_dirs = []
next = ["T01: 修復表格跨頁縫合邏輯"]
```
