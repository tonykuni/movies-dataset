# VIA · Functional Modules Layout · 功能模組配置

The System Manager (`supportive modules/VIA_Governance_Runtime/v0162B`) discovers
subsystems in this order:

| Subsystem | Discovery roots (relative to Base) |
|---|---|
| VRN | `functional modules/VRN` |
| VDF | `functional modules/VDF`, `functional modules/VeritasDataForge`, `module/VeritasDataForge`, `VeritasDataForge` |
| VAP | `functional modules/VAP`, `module/VAP`, `VAP` |
| Others | every other directory under `functional modules/` and `module/` |
| Supportive | `supportive modules/` |

`VRN/` and `VDF/` here contain **integration anchors only** — a subsystem
manifest that registers the discovery root and its governance gates. The real
canonical trees live on the operator workstation under the same paths and are
never modified by the System Manager (sandbox repair candidates only;
promotion requires a separate hash-locked, operator-reviewed transaction).

`VAP/` carries its anchor manifest **plus the supplied canonical artifacts**:
`spec/VIA_Chart_Layout_Spec_ONE_Standalone.html` (Chart & Layout Spec ONE —
規範 · 套用圖庫 · 實例, visual lock 線粗 1 · 透明度 0.75 · 軸距 2/2.5/5/10) and
`ui/VIA_Intelligence_Platform_v0162C.html` (Intelligence Platform v0162C UI
preview declaring the VRN / VDF / VAP module set). Both are SHA-256 registered
in `VAP_Subsystem_Manifest.json` and are REVIEW-ONLY under the same
no-canonical-mutation governance.

排除規則：`.git`, `__pycache__`, `node_modules`, `venv`, `cache*`, `archive*`,
`backup*`, `staging`, `received_duplicates` 不列入分析。
