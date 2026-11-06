# 操作員上傳 · VIA System Integration Engine v1.0(2026-11-06 13:31 三檔)· 入倉紀錄

只讀入倉(byte-exact 進 zip · SHA-256 在 `SHA256.txt`),**不接線、不執行服務、不裝套件**。本文只寫實測到的事。

| 檔 | SHA-256(前 16)| 大小 | 容器實測 |
|---|---|---|---|
| `VIA_SystemIntegrationEngine.py` | `4e580833fde0fdcb` | 84,470 B · 1,303 行 | `python3 -I … --self-test`(隔離夾 · 無 fastapi)→ **21 / 21 OK · rc 0**;全景卡:匯入 28 個標準庫 · 定義 60+ · 問題 3(L1170 / 1173 / 1177 `except Exception: pass`) |
| `VIA_SystemIntegration_QA.json` | `379aa302ef14cf91` | 1,474 B | 自述 result PASS · self_test 21 / 21 · duckdb / polars / browser runtime **未測**(false) |
| `VIA_SystemIntegration_README.md` | `acafed748c6034c0` | 4,513 B | 安裝需 `pip install fastapi uvicorn`(VIA 環境不 pip · 經 VCGC via-install 才裝)|

## 它是什麼(照原檔 · 不加料)

單檔 FastAPI + 內嵌 HTML 的**工作流 DAG 編輯器 / 執行器**:節點型別白名單(數值 / AST 掃描 / 單元 · 整合 · 系統測試 / 政策閘 / 網路探測 / 收尾)·
Kahn 拓撲排序 · SQLite 只增稽核帳(SHA-256 鏈)· 「雙矩陣」= **它自己 5 個階段 × 14 個節點的狀態**與**它自己 10 條治理需求(R0–R9)在 T1–T5 的證據**·
匯出 Mermaid / DOT / React Flow / Cytoscape / X6 / BPMN · 20 個「adapter」只是能力描述(README 自己寫 ADAPTER_ONLY)。

## 與操作員要的「多矩陣管理報告」的關係

操作員同封訊息要的欄位是 **SYSTEM / FUNCTION / DESCRIPTION / MDL-ENG NAME / CLS / FNC / LIBS / ERROR & AST / STATUS**,對象是 VIA 五系統的**每個模組家族**。
這支引擎的矩陣是**它自己示範 DAG 的階段 × 需求**,不讀 VIA 的模組、冊、收據,所以**不能拿來當 VIA 模組矩陣**;
該需求由 `VIA_SettleAll_v0110.py` 的 **⑭ 模組矩陣**(只讀 AST · 用 VIA 自己的 ⑬ 引擎自測 / VCGC 功能帳 / 入口步燈當 STATUS)實作,見 `VIA_SettleAll_v0110.md`。

## 收尾規範下的處置(操作員 2026-11-06 Release Closure:不新增模組 · 不引入新架構 · 不 pip)

- 入倉只為留證(操作員原件 · byte-exact);**不**登 VCGC 盤點冊 / 編號冊(不是 VIA 模組家族)。
- 要在桌機看它的畫布:它自己的 README 指令(`py -m pip install fastapi "uvicorn[standard]"` → `--serve`)**請在獨立 venv 跑**,不要裝進 VIA 的環境;
  預設只綁 127.0.0.1 · `OPTIONAL_NETWORK=False` · 不出網(符合 VIA 網路政策)。
- 若日後要把 VIA 各系統的燈餵進它的畫布:它吃 Drawflow JSON;`VIA_ModuleMatrix_latest.json` 的 rows 可以轉,但那是**新功能**,收尾期不做。
