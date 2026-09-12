# VIA AI Workflow v0100

`VIA_AI_Workflow_v0100` 是既有 VIA 母系統的治理附加層，不是第二套母系統。它把 AI 指令、AST 索引、自動編號、Task Context Pack 與交接證據整理為可驗證的 JSON 契約。

## Canonical anchors

| Role | Existing canonical unit |
|---|---|
| Mother system | `VIA_SYSTEM_MANAGER_v0121.py` |
| Central registry | `supportive modules/20_Registry_SSOT/VIA_RegistryCore_v1.py` |
| Unified SSOT | `supportive modules/20_Registry_SSOT/VIA_SSOT_Unified.py` |
| AST runtime | `supportive modules/VIA_Panorama_AST_RuntimeInjector.py` |
| Runtime bridge | `supportive modules/VIA_Runtime_Bridge_All_in_One.py` |
| Governance engine | `supportive modules/VIA_Central_Governance/CGC_MDL001_CentralGovernanceEngine_v0401.py` |
| AI workflow bridge proposal | `supportive modules/20_Registry_SSOT/VIA_AI_Workflow_v0100/src/via_mother_system_bridge.py` |

上述既有檔案維持原狀。本套件只提供契約、索引與交接橋接，不直接 Promotion、不改名、不刪除舊版本。

`via_mother_system_bridge.py` 保留 `CGC_MDL142` 候選身分，但放在本套件內，不進入母系統 live registry 掃描。只有完成 MasterControl 再生比對、Zero-Hydra 審查與人工核准後，才可依 Registration Proposal 移入正式 registry。

## Six-layer instruction model

| Layer | ID | Responsibility |
|---|---|---|
| ① Preflight | `VIA-AI-000001` | 範圍、SSOT、分支、風險與資料界線 |
| ② Data | `VIA-AI-000002` | DuckDB／Parquet／Schema／增量資料契約 |
| ③ Core | `VIA-AI-000003` | 單一 canonical engine 與依賴串接 |
| ④ UI | `VIA-AI-000004` | UI 輸入、狀態、輸出與資料主詞契約 |
| ⑤ QA | `VIA-AI-000005` | AST、Contract、Sandbox、Integration、User-Test gates |
| ⑥ Ops | `VIA-AI-000006` | GitHub、Checkpoint、Handoff 與人工 Promotion |

ID 是 registry identity，不要求修改實體檔名。Registry 採 append-only event ledger；多 AI 並行前應先在整合分支租用不重疊 ID range。

## Quick start

```powershell
pwsh -NoProfile -File .\Invoke-VIA-AIWorkflow-v0100.ps1 -Action Validate
pwsh -NoProfile -File .\Invoke-VIA-AIWorkflow-v0100.ps1 -Action AstIndex -ScanRoot ..\..\..\..
pwsh -NoProfile -File .\Invoke-VIA-AIWorkflow-v0100.ps1 -Action Status
```

直接使用 Python：

```powershell
python .\src\via_ai_workflow.py validate
python .\src\via_ai_workflow.py allocate --layer CORE --slug example --owner ChatGPT
python .\src\via_ai_workflow.py lease --agent ChatGPT --size 20
python .\src\via_ai_workflow.py ast-index --root ..\..\..\..
python .\src\via_ai_workflow.py context-pack --task .\templates\task_context_pack.template.json
```

所有命令預設 fail-closed。`validate` 有錯誤時回傳非零 exit code；任何寫入均先鎖定、寫入暫存檔、原子替換，且不覆寫已存在的 module manifest。

## Multi-AI handoff

1. 從最新 `main` 建立每個 AI 的獨立 branch／worktree。
2. 先建立 Task Context Pack，只列出本次允許讀取的檔案與 symbols。
3. 由整合者租用 ID range；各 AI 僅使用分配範圍。
4. 一次只負責一個模組或互不重疊的 symbols。
5. 完成 AST、Contract、Sandbox、Integration、User-Test gates。
6. 產出 handoff packet，記錄 base/head SHA、變更、測試、風險及下一步。
7. Pull Request 只提出 Promote Plan；由人工核准後才合併。

## Repository and data boundary

- GitHub 保存程式碼、JSON Schema、migration、lockfile、小型 fixture、摘要證據與 handoff。
- DuckDB、Parquet、PDF、模型、金鑰、完整 log 與完整回測明細留在本機資料面。
- 優先根目錄為 `C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics`；`C:\Users\tonyk\Github` 只作為候選 clone 根目錄。
- 所有資料路徑由 `config/VIA_MotherSystem_Database_Bridge.v0100.json` 或環境變數注入，不寫死到引擎邏輯。

## Test

```powershell
python -m unittest discover -s .\tests -v
python .\src\via_ai_workflow.py validate
```
