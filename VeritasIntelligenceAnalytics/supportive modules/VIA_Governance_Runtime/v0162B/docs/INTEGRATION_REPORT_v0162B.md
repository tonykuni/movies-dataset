# VIA 整體系統整合收尾報告 · System Integration Completion Report
**v0162B · Integration Build R2 + VAP · 2026-07-28**
**Scope 範圍: supportive modules / VRN / VDF / VAP**

> **VAP 整合 · VAP integration (2026-07-28)** — VAP(**VeritasAutoPlot**,
> VIA 視覺功能管理:icons / templates / 繪圖)anchor
> (`functional modules/VAP/VAP_Subsystem_Manifest.json`) 註冊完成,並收入
> 兩件 canonical 產物:Chart & Layout Spec ONE 獨立規範套件
> (`spec/`,sha256 `dc416087…`,8,132,473 bytes;VISUAL LOCK 線粗 1 ·
> 透明度 0.75 · 軸距 2/2.5/5/10 已寫入 anchor 治理)與 Intelligence
> Platform v0162C UI 預覽(`ui/`,sha256 `377f7f09…`,91,026 bytes)。
> 引擎 v0162B 原生探索 VAP root(SYSTEM_MANAGER_CONTRACT 已含 VAP),
> 三輪實跑重新執行:subsystems = VRN / VDF / VAP / SUPPORTIVE,
> 15 files analyzed · 15 GREEN · 0 YELLOW · 0 RED · 0 Hydra · 56 functions,
> 閘門仍為 GREEN。兩個 VAP HTML 帶 UTF-8 BOM,引擎僅於 sandbox 產生
> 正規化候選(CANDIDATE_ONLY_NO_CANONICAL_MUTATION),canonical 未動。

> **R2 修正 · R2 fix (2026-07-28)** — 第一次 Windows 使用者實測(py 3.13.7)
> 暴露出參數引號缺陷:`Start-Process` 以陣列傳遞引數時不加引號,含空格的
> 引擎路徑(`supportive modules`)在空格處被切斷,Python 以 Errno 2 失敗。
> R2 對所有含空白的引數明確加上引號並以單一命令列傳遞;兩個每日啟動器
> 已重新鎖定至 R2 啟動器 SHA(`ae3bdbd5…`,102,697 bytes)。引號行為已在
> PowerShell 7.4.6 以含空格路徑實測驗證。

## 1. 結論 · Outcome

The v0162B System Manager package is now complete, internally consistent, and
hash-locked end to end. The one missing canonical artifact — the AllInOne
launcher — was reconstructed from the byte-verified audit copies, every SHA
gate was re-locked, and the full QA suite (including the Microsoft PowerShell
AST parser and a live three-round engine run) passes.

最終引擎閘門 · Final engine gate:
`UNIFIED_SANDBOX_GREEN_RUNTIME_DEPLOYED_NO_CANONICAL_MUTATION`
(5 files analyzed · 5 GREEN · 0 YELLOW · 0 RED · 0 Hydra risks · 41 functions registered)

## 2. 起點狀態 · Starting state

The supplied v0162B artifact set contained the manifest, the audit Python
engine, the UI preview, and two byte-identical SHA-gated daily entrypoints —
but **not** the canonical `Invoke-VIA-SystemManager-AllInOne-v0162B.ps1`
(143,477 bytes, sha256 `e6155465…`) that both entrypoints gate on. As shipped,
the entrypoints could never launch: the gate file was absent.

Verified against the manifest before integration:

| Artifact | Manifest SHA-256 | Verified |
|---|---|---|
| `engine/via_system_manager_engine_v0162B.py` | `4d6c9837…dd426` | ✅ byte-identical |
| `ui/VIA_SystemManager_v0162B_Preview.html` | `4f653c4a…64152` | ✅ byte-identical |

## 3. 整合作業 · Integration work

1. **AllInOne reconstruction** (`bin/Invoke-VIA-SystemManager-AllInOne-v0162B.ps1`,
   102,697 bytes, sha256 `ae3bdbd5…82c114` (R2)), built strictly to the v0162B
   repair contract:
   - single-quoted literal here-strings only — zero expandable here-strings
     (the v0162A root cause), verified by token scan;
   - embedded engine + workbench materialized with **exact-SHA verification**
     before anything executes;
   - daily launchers generated from one literal template via placeholder
     replacement, then AST-validated with detailed parse-error output and
     rolled back on failure;
   - governance enforced: `AUTO_LAUNCH_ALL` default, `-UiOnly` switch, sandbox
     repair only, no canonical mutation, no network install, no
     stop-process (on timeout the worker is left running, never killed),
     register-all/import-approved-only.
2. **SHA gate re-lock**: both `StartVIASystemManager.ps1` and
   `StartVIAUnified.ps1` regenerated from the same template, now gating on the
   reconstructed launcher's SHA (`ae3bdbd5…`). Entrypoints remain
   byte-identical to each other (sha256 `7ceefc2b…`).
3. **VRN / VDF integration anchors**: `functional modules/VRN` and
   `functional modules/VDF` now carry subsystem manifests registering the
   discovery roots and governance gates (enabled=false draft intake for VRN,
   Incremental/Refresh/ValidateOnly/DryRun modes for VDF, promotion only via a
   separate hash-locked operator transaction). The engine discovers and
   analyzes both — confirmed in the live run (`subsystems: VRN, VDF, SUPPORTIVE`).
4. **Manifest updated** with the reconstructed artifact hashes, the entrypoint
   hashes, the integration record, and refreshed QA states.

## 4. QA 證據 · QA evidence (`qa/`)

| Gate | Result |
|---|---|
| AllInOne AST (Microsoft parser, PowerShell 7.4.6) | PASS |
| Both daily entrypoints AST | PASS |
| Generated-launcher AST (template output) | PASS |
| Expandable here-string token scan | PASS (0 found) |
| Embedded engine roundtrip → sha `4d6c9837…` | PASS |
| Embedded workbench roundtrip → sha `4f653c4a…` | PASS |
| Entrypoint template roundtrip (byte-exact vs shipped) | PASS |
| Python engine `py_compile` (3.11) | PASS |
| Preview JavaScript `node --check` | PASS |
| All package JSON parse | PASS |
| Engine three-round live run (with pwsh AST workers) | PASS · gate GREEN |

Evidence files: `qa/evidence/powershell_ast_qa_results.json`,
`qa/evidence/engine_run_final_summary.json`,
`qa/evidence/engine_run_round_summaries.json`,
`qa/evidence/VIA_Unified_Panoramic_Matrix_v0162B.html`.
The AST/roundtrip suite is reproducible via
`qa/Invoke-VIA-QA-AST-v0162B.ps1 -PackageRoot <Base> -OutputJson <file>`.

## 5. 剩餘閘門 · Remaining explicit gates

Per contract these are **not** claimed automatically:

- `windows_runtime_user_test = REQUIRED` — operator runs
  `StartVIASystemManager.ps1` (or `StartVIAUnified.ps1`) on the Windows
  workstation; the exact-SHA gate, Windows AST pass, engine run, and workbench
  launch all execute there.
- **Canonical promotion** — any sandbox repair candidate is written under the
  run directory only; writing back into VRN / VDF / VAP canonical trees
  requires the separate hash-locked, operator-reviewed transaction.

## 6. 部署 · Deployment onto the workstation

Copy the contents of `VeritasIntelligenceAnalytics/` over
`C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\` (the two Start
scripts at the base root, `supportive modules` and `functional modules`
merged in place; existing VRN/VDF canonical content is untouched — the
anchors only add one manifest file to each root). Then run
`StartVIASystemManager.ps1` in PowerShell 7.
