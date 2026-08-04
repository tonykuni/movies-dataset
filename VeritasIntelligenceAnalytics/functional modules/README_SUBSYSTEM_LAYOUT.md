# VIA · Functional Modules Layout · 功能模組配置

The System Manager (`supportive modules/VIA_Governance_Runtime/v0162B`) discovers
subsystems in this order:

| Subsystem | Discovery roots (relative to Base) |
|---|---|
| VRN | `functional modules/VRN` |
| VDF | `functional modules/VDF`, `functional modules/VeritasDataForge`, `module/VeritasDataForge`, `VeritasDataForge` |
| VAP | `functional modules/VAP`, `module/VAP`, `VAP` |
| VTR | `functional modules/VTR` |
| Others | every other directory under `functional modules/` and `module/` |
| Supportive | `supportive modules/` |

`VRN/` and `VDF/` here contain **integration anchors only** — a subsystem
manifest that registers the discovery root and its governance gates. The real
canonical trees live on the operator workstation under the same paths and are
never modified by the System Manager (sandbox repair candidates only;
promotion requires a separate hash-locked, operator-reviewed transaction).

`VAP/` (**VeritasAutoPlot** — VIA 視覺功能管理:icons / templates / 繪圖)
carries its anchor manifest **plus the supplied canonical artifacts**:
`spec/VIA_Chart_Layout_Spec_ONE_Standalone.html` (Chart & Layout Spec ONE —
規範 · 套用圖庫 · 實例, visual lock 線粗 1 · 透明度 0.75 · 軸距 2/2.5/5/10) and
`ui/VIA_Intelligence_Platform_v0162C.html` (Intelligence Platform v0162C UI
preview declaring the VRN / VDF / VAP module set). Both are SHA-256 registered
in `VAP_Subsystem_Manifest.json` and are REVIEW-ONLY under the same
no-canonical-mutation governance.

`VTR/` (**DG-IN Meeting Transcript Restoration Engine** — 中英文會議紀錄修復引擎)
carries its anchor manifest **plus the canonical specification set**: the shared
`contracts/vtr-document.schema.json` data contract, four engineering specs under
`docs/` (architecture · Python engine · JavaScript engine · SSOT Lexicon), and an
**executable SSOT Lexicon** under `lexicon/` (JSON Schema, five seed word-banks,
generated index, and `tools/validate_lexicon.py` as the CI gate). Every artifact is
SHA-256 registered in `VTR_Subsystem_Manifest.json`. Engine code (`vtr_py`,
`@dg-in/vtr-js`) is **not yet implemented** — see `VTR/README.md`. Lexicon intake
follows the VRN policy (new entries are `enabled=false` drafts; enabling requires
`provenance.approved_by`, enforced by the validator), and the restoration engine
produces candidates plus an append-only patch log only — it never mutates a
canonical transcript.

排除規則：`.git`, `__pycache__`, `node_modules`, `venv`, `cache*`, `archive*`,
`backup*`, `staging`, `received_duplicates` 不列入分析。
