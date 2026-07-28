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

排除規則：`.git`, `__pycache__`, `node_modules`, `venv`, `cache*`, `archive*`,
`backup*`, `staging`, `received_duplicates` 不列入分析。
