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

`VRN/` here contains an **integration anchor only** — a subsystem manifest
that registers the discovery root and its governance gates. `VDF/` carries its
anchor manifest plus one canonical artifact, `ui/VIA_VDF_v4.3_Cockpit.html`
(VDF v4.3 Management Cockpit, SHA-256 registered in
`VDF_Subsystem_Manifest.json`). The real canonical trees live on the operator
workstation under the same paths and are never modified by the System Manager
(sandbox repair candidates only; promotion requires a separate hash-locked,
operator-reviewed transaction).

`VAP/` (**VeritasAutoPlot** — VIA 視覺功能管理:icons / templates / 繪圖)
carries its anchor manifest **plus the supplied canonical artifacts**:
`spec/VIA_VAP_Chart_Library_Builder.html` (最佳圖庫建構器 — the unified spec
store and **normative source of the visual lock**: 線粗 1 · 折線透明度 0.9 ·
填色 0.4 · 軸距 2/2.5/5/10 × 5 刻度 · via combo 色序),
`spec/VIA_Chart_Layout_Spec_ONE_Standalone.html` (Chart & Layout Spec ONE —
規範 · 套用圖庫 · 實例;its headline 透明度 0.75 is superseded by the builder
store, per the anchor's `recorded_conflict`),
`ui/VIA_Intelligence_Platform_v0162C.html` (Intelligence Platform v0162C UI
preview declaring the VRN / VDF / VAP module set) and
`ui/VIA_VAP_System.html` (Veritas Process Nexus System UI). All are SHA-256
registered in `VAP_Subsystem_Manifest.json` and are REVIEW-ONLY under the same
no-canonical-mutation governance.

`VAP/engine/via_autoplot_engine_v001.py` is the VeritasAutoPlot plotting
engine: it reads the VDF analytical database (CSV / TSV / JSON / SQLite under
`VDF/db`) and renders **dual-axis comparison charts**(一個資料一個軸,兩軸互比,
兩系列必用不同圖形)as self-contained HTML+SVG under `<Base>/VAP/output`,
zero dependencies, honouring the visual lock. Usage:
`python engine/via_autoplot_engine_v001.py --base <Base> --list | --auto |
--table <t> --left <col> --right <col> [--left-form bar|line|area]`.

排除規則：`.git`, `__pycache__`, `node_modules`, `venv`, `cache*`, `archive*`,
`backup*`, `staging`, `received_duplicates` 不列入分析;引擎自身的 runtime
root(`supportive modules/VIA_Governance_Runtime/v0162B/runtime`,即所有
`run_*` 目錄)自 R3 起也排除——先前 run 的 sandbox 副本與崩潰殘骸不再被
重新分析。R4 起再排除 `_vdf_envs`(內嵌 Python 環境)、`site-packages`
(第三方套件)與 `scope_copy`(快照副本樹);超過 64 MiB 的檔案仍列冊
與雜湊,但跳過內容解析(資料檔不再因 MemoryError 誤判 RED)。
