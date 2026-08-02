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

`VAP/` (**VeritasAutoPlot** — VIA 視覺功能管理:icons / templates / 繪圖)
carries its anchor manifest **plus the supplied canonical artifacts**:
`spec/VIA_Chart_Layout_Spec_ONE_Standalone.html` (Chart & Layout Spec ONE —
規範 · 套用圖庫 · 實例, visual lock 線粗 1 · 透明度 0.75 · 軸距 2/2.5/5/10) and
`ui/VIA_Intelligence_Platform_v0162C.html` (Intelligence Platform v0162C UI
preview declaring the VRN / VDF / VAP module set),
`ui/VAP_Workbench_v009.html` (VeritasAutoPlot 工作台 — High-Resolution Export
& Stack Composer v009, header 帶 `data-frozen-lock=HEADER_EQUAL_HEIGHT_LOCKED`)
and `spec/VIA_VAP_Spec_SSOT__Standalone.html` (VAP 規範 SSOT — Spec & Library
JSON single source of truth). All are SHA-256 registered in
`VAP_Subsystem_Manifest.json` and are REVIEW-ONLY under the same
no-canonical-mutation governance. A `header_visual_lock` gate is registered
PENDING_DESIGN_SOURCE for the Veritas Header design (Claude Design project
68463cc8); it activates once the design source file lands in the repo.

`VAP/engine/via_autoplot_engine_v001.py` is the VeritasAutoPlot plotting
engine: it reads the VDF analytical database (CSV / TSV / JSON / SQLite under
`VDF/db`) and renders **dual-axis comparison charts**(一個資料一個軸,兩軸互比,
兩系列必用不同圖形)as self-contained HTML+SVG under `<Base>/VAP/output`,
zero dependencies, honouring the visual lock. Usage:
`python engine/via_autoplot_engine_v001.py --base <Base> --list | --auto |
--table <t> --left <col> --right <col> [--left-form bar|line|area]`.

`VDF/engine/vdf_movies_intake_v001.py` is the VDF movies-dataset intake
forge(電影資料集鍛造引擎): it reads the repository dataset
(`<Repo>/data/*.csv` — movie_metadata / tmdb_5000_movies /
movies_genres_summary)and materializes the VDF analytical database
`VDF/db/movies_dataset.sqlite`(tables: `movies_genres_summary`,
`yearly_box_office`, `yearly_tmdb` — year-keyed so AutoPlot auto-pairing
works), zero dependencies, sources read-only, atomic Refresh. Usage:
`python engine/vdf_movies_intake_v001.py --base <Base>
[--mode Refresh|ValidateOnly|DryRun] [--source <dir>]`. Each Refresh writes
`qa/evidence/movies_intake_summary.json`(source sha256 · row counts · gate).
AutoPlot then discovers the database through its canonical `VDF/db` root with
no `--db` override — end-to-end:
`intake --mode Refresh` → `autoplot --auto`. The built database and chart
outputs are **products**(git-ignored); only engines and QA evidence are
tracked.

排除規則：`.git`, `__pycache__`, `node_modules`, `venv`, `cache*`, `archive*`,
`backup*`, `staging`, `received_duplicates` 不列入分析。
