# MeetingLoop 歸位裁定(2026-08-10)

## 收件與去重
12 件上傳 → 9 唯一(3 對位元組重複);引擎兩變體僅差版本字串(v005/v003)→ **v005 為正本**。

## 容器 QA(誠實)
- 紅線掃描 7 件全 CLEAN(Send/Move 零)· py_compile ×3 OK · 四支 ps1 AST OK
- 引擎 doctor 實跑 gate=GREEN(無 duckdb/pyarrow 誠實降級 SQLite+JSONL — 套件設計如此)
- self-test 需套件內 sample_meeting.txt(未上傳)→ 容器無法全跑;套件自帶
  PACKAGE_INTEGRITY_REPORT 載 3 測試 PASS(轉述,實機驗證待操作員)

## 生產宣稱(照套件自己的話)
V005_VALIDATION_STATUS:`production_claim = NOT_YET_VALIDATED_ON_USER_WINDOWS` —
實機驗收 = 操作員跑 Test-VIA-FullUXData-Acceptance-v005.ps1(必要時先
Install-VIA-DataEnvironment-v005.ps1 裝 duckdb/pyarrow 達 FULL_UX_DATA_ACCEPTED)。

## 與 VTR 的擇優關係(待令)
VTR = 會議逐字稿「確定性修復」正本(49 測試、freeze.lock 治理)— 不動。
MeetingLoop = 修復+摘要+Action+滑鼠工作台+SSOT(SQLite/Parquet/DuckDB)— 能力更寬。
重疊層(逐字稿修復)之擇優合流待操作員明令;現階段共存:VTR 修復正本、MeetingLoop
以摘要/Action/工作台為主用途。N-3/N-1 一律 DraftOnly(絕不代寄相容)。

## 補遺(2026-08-10 操作員實機首跑後)

- 實機 doctor GREEN 且 duckdb/pyarrow/rapidfuzz/dateparser/sklearn 全在(僅 opencc 缺=
  繁簡轉換降級)— 比容器更完整。
- SelfTest WinError 2 根因=套件兩檔未上傳:`sample_meeting.txt` 與
  `templates/mouse_first_workbench.html`。本席自建補齊:樣本逐字稿(含決議/行動/風險
  線索,覆蓋九斷言)+ 滑鼠工作台模板(__EMBEDDED_DATA__ 契約;chips 全滑鼠、
  匯出 review.json → import-review 吸收;不回寫正本)。容器全跑 self-test 9/9 PASS。
  若原廠模板日後上傳,依擇優去重比對後裁定正本。
