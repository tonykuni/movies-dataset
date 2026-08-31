# Veritas OmniFormat Intelligence Engine（VOFIE）v1.4

正式名稱：**Veritas 全格式智慧重構、元件整合與模板生成引擎**  
VIA Subsystem ID：`VIA-SUBSYS-VOFIE-001`  
Registry namespace：`veritas.omniformat`

VOFIE v1.4 是 add-only 升級：保留 v1.0 full convert、v1.1 simple-five、v1.2 JavaScript／PowerShell Top-20、VSIS 1.2 與 v1.3 NoHydra；新增三輪真實唯讀 post-scan、受核准的版本化 Runtime Copy、四態 hash state machine、rollback dry-run 與 20 列離線 HTML 管理矩陣。

## 不變承諾

1. 來源檔只讀；前後以 `byte_size + BLAKE2s` 驗證，禁止刪除、移動、覆寫 canonical。
2. 文字依主題重構；程式不論語言都寫入 Component IR，API 簽章只可保留或另存候選。
3. 去重只設定 `duplicate_of`；duplicate 與 quarantine 仍保留在 IR／Component Specs JSON。
4. HTML 同時抽取內容與 UI Spec；來源 script 不執行，產生的 HTML 無 CDN。
5. VSIS 1.2 執行 `normalize / segment / categorize / semantic_check`；缺少時使用 deterministic local NLP。
6. AI 仍是 candidate-only；沒有等價測試不得直接套用。

## 最簡單的使用方式

Windows / Python 視窗：

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py gui
```

或 PowerShell 7：

```powershell
& ".\Invoke-Veritas-VOFIE.ps1" -Gui
```

視窗可用「選取檔案」或拖放輸入，最多 5 檔。若 `tkinterdnd2` 不存在，拖放自動降級成原生多檔選取，核心功能不受影響。

## 固定五個主要輸出

`simple` 模式只在輸出根目錄放 5 個主要檔：

| # | 檔案 | 定位 |
|---:|---|---|
| 1 | `Veritas_VOFIE_Reconstructed.md` | 完整人可讀內容、ST、整合索引與來源追溯 |
| 2 | `Veritas_VOFIE.html` | CSS／JS／JSON 全內嵌的離線互動頁 |
| 3 | `Veritas_VOFIE_ComponentSpecs.json` | UI／程式元件、整合視圖、failure framework 與完整 Universal IR |
| 4 | `Veritas_VOFIE_Reconstructed.docx` | Word 參考指南；python-docx 缺少時用 stdlib OOXML 降級 |
| 5 | `Veritas_VOFIE_TopicMatrix.csv` | UTF-8 BOM Topic Matrix |

ENGINE 角色只產生上述 5 檔；SYSTEM 角色仍只顯示這 5 個主要檔，但另在 `_system/` 保存 10 個治理 sidecars，包含 NoHydra audit／HTML matrix、Runtime Copy safety、工具與測試證據。

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py simple `
  .\input-a.md .\input-b.html .\module.py `
  --output .\Veritas_VOFIE_Output `
  --role ENGINE `
  --operations text_merge,code_merge,restructure,deduplicate,optimize
```

SYSTEM 角色：

```powershell
& ".\Invoke-Veritas-VOFIE.ps1" `
  -Simple -Role SYSTEM `
  -InputPaths @("C:\input\notes.md", "C:\input\ui.html") `
  -OutputPath "C:\output\VOFIE_Run"
```

## 五個整合動作

固定順序：`text_merge → code_merge → restructure → deduplicate → optimize`。

| Action | 行為 | 不變量 |
|---|---|---|
| `text_merge` | 依 taxonomy 建立文字主題整合索引 | 原 Topic 不刪 |
| `code_merge` | 依 language／symbol 建立跨語言元件索引 | API 簽章不改 |
| `restructure` | 建立可讀的分類視圖 | 原順序與行號保留 |
| `deduplicate` | 視圖只顯示 canonical | duplicate 仍在 IR |
| `optimize` | 產生結構候選與數量摘要 | 不直接改來源 |

## Top 20 Failures × 8 環節

`config/failure_catalog.json` 是失敗 SSOT，共 8 個環節、每環節 20 項、合計 160 項。每項繼承該環節至少 5 個已實作 recovery handlers；`failure-catalog` 會展開成可機讀的逐項規格。

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py failure-catalog --report .\FailureCatalog.json
python .\Veritas_OmniFormat_Intelligence_Engine.py dependencies --report .\Dependencies.json
```

八個環節：`INTAKE / READER / SEMANTIC / CONSOLIDATION / VSIS_NLP / EXPORT / WINDOW_UI / GOVERNANCE`。詳細處理方式見 `FAILURE_PLAYBOOK.md`。

## 九頭龍風險避免 Top 20

`config/hydra_risk_catalog.json` 獨立管理 20 個多點連動風險，避免與一般 160 failures 混用。每項都有 cause、detectors、breakers、至少三個 solutions、SOP、never-again control 與 repair lane。

- canonical 永遠唯讀；修復只可進 Runtime Copy proposal。
- 最多三輪；parallel fixer 最多 2、global concurrency cap 4。
- 高風險一律 `HOLD`，不自動修復、不自動啟用。
- 預設不 import 被掃模組、不連網、不啟 child process、不寫 DB／來源。
- Activation 必須同時通過 Hydra、self-test、user-test、recovery 與 rollback-ready 契約。

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py hydra-audit `
  .\engine.py .\launcher.ps1 `
  --report .\Veritas_VOFIE_HYDRA_RISK_AUDIT.json
```

完整表格與處理流程見 `HYDRA_RISK_PLAYBOOK.md`。

## v1.4 Runtime Copy 與 rollback

Canonical／SSOT 不可直接寫入。真實寫入只允許在新建的版本化 run-local Runtime Copy，並要求精確核准 token；沒有 token 必定 `HOLD`。四態規則固定為 `MISSING→APPLY`、`PROPOSED→SKIP`、`ORIGINAL→BACKUP_APPLY`、`OTHER→FAIL_CLOSED`。

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py runtime-copy .\input.md `
  --output .\runtime --approval-token YES_FOR_ANY_REAL_WRITE `
  --report .\RuntimeCopyReport.json

python .\Veritas_OmniFormat_Intelligence_Engine.py rollback-check `
  .\runtime\RuntimeCopyManifest.json --report .\RollbackCheck.json

& ".\Invoke-Veritas-VOFIE.ps1" -RuntimeCopy `
  -RuntimeTargets @(".\input.md") -RuntimeOutput ".\runtime" `
  -RuntimeApprovalToken "YES_FOR_ANY_REAL_WRITE"
```

`rollback-check` 只驗證復原所需 hash 與 manifest，不執行真實 rollback，也不提升 Runtime Copy 為 canonical。

## JavaScript／PowerShell Top 20 CPU 工具

`config/polyglot_tool_catalog.json` 固定登記 JavaScript 20 項與 PowerShell 20 項免費工具，並映射到 syntax、static analysis、format、unit test、coverage、dependency graph、unused code、codemod、schema/UI validate、build 十個功能。Python／JavaScript／PowerShell 三語言合計固定 30 列能力矩陣。

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py tool-audit `
  --language all --probe-installed `
  --report .\Veritas_VOFIE_POLYGLOT_TOOL_AUDIT.json
```

- JavaScript 工具只進 `via-ui`，PowerShell 工具只進 `via-ps`；base 不安裝。
- VOFIE 只偵測，不自動安裝；缺少工具標記 `NOT_INSTALLED`。
- 每個工具都有 CPU 成本、license、machine-output 與 fallback。
- 外部 lint／format／build／refactor 預設 `PLAN_ONLY`。

需求式調用：

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py tool-plan .\module.js `
  --functions syntax_parse,static_analysis,dependency_graph

python .\Veritas_OmniFormat_Intelligence_Engine.py tool-plan .\launcher.ps1 `
  --functions syntax_parse,unit_test,build_automation `
  --execute-safe

& ".\Invoke-Veritas-VOFIE.ps1" -ToolPlan `
  -ToolTarget ".\launcher.ps1" `
  -ToolFunctions syntax_parse,unit_test,build_automation `
  -ExecuteSafe
```

`--execute-safe` 只允許唯讀 syntax quick check；其他功能回傳工具、替代工具與 fallback，不使用 fix/write，不修改來源。

## 測試、除錯與啟用

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py self-test
python .\Veritas_OmniFormat_Intelligence_Engine.py user-test
python .\Veritas_OmniFormat_Intelligence_Engine.py activate --report .\Veritas_VOFIE_ACTIVATION.json
python .\Veritas_OmniFormat_Intelligence_Engine.py hydra-audit --report .\Veritas_VOFIE_HYDRA_RISK_AUDIT.json
python .\Veritas_OmniFormat_Intelligence_Engine.py tool-audit --language all
```

`activate` 只在 core self-test、recovery dry-run 與 ENGINE／SYSTEM user-test 全部 PASS 時回報 `ACTIVE`，否則為 `HOLD`；不啟動外部程式、不更動來源。

## 完整模式仍保留

v1.0 的所有輸出與入口未移除：

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py convert `
  .\input-a.md .\input-b.html .\module.py `
  --output .\Veritas_VOFIE_Full `
  --formats md,json,docx,pptx,xlsx,csv,html,css,js
```

## 未來新增工具的唯一入口

工具增減分兩層管理：`config/tool_registry.json` 是 VIA 整合入口，`config/polyglot_tool_catalog.json` 是 JavaScript／PowerShell 候選與 capability 映射：

- 新副檔名加到 `input_overlays` 或 `code_language_overlays`。
- 升級同類工具時新增 `tool_id`；舊工具只設 `enabled: false`，不可刪除。
- 新 Reader 加入 Python `READERS`；新 recovery 加入 `RECOVERY_HANDLERS`。
- 雙語言候選只在 `polyglot_tool_catalog.json` append／disable，不直接改 engine base。
- 不得覆寫 `ST-FROZEN`、Universal IR、source hash gate、五檔契約與來源唯讀政策。

## 專案結構

```text
Veritas_OmniFormat_Intelligence_Engine_v0140/
├── Veritas_OmniFormat_Intelligence_Engine.py
├── Invoke-Veritas-VOFIE.ps1
├── adapters/                         # PPTX/XLSX + JS/PS Tool Bridges
├── config/
│   ├── tool_registry.json            # 工具增減 SSOT
│   ├── polyglot_tool_catalog.json     # JS／PS 各 Top 20 CPU 工具
│   ├── hydra_risk_catalog.json         # NoHydra Top 20 + breakers／solutions
│   └── failure_catalog.json          # 8 × Top 20 failures
├── schemas/                         # IR／Invocation／Polyglot／Hydra contracts
├── tests/
│   ├── test_vofie.py
│   └── Invoke-VOFIE.PowerShell.Tests.ps1
├── FAILURE_PLAYBOOK.md
├── HYDRA_RISK_PLAYBOOK.md
├── FORMAT_CONTRACT.md
├── INTEGRATION_SPEC.md
└── TEST_REPORT.md
```
