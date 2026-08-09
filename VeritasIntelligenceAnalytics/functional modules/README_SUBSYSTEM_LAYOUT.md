# VIA · Functional Modules Layout · 功能模組配置

The System Manager (`supportive modules/VIA_Governance_Runtime/v0162B`) discovers
subsystems in this order:

| Subsystem | Discovery roots (relative to Base) |
|---|---|
| VRN | `functional modules/VRN` |
| VDF | `functional modules/VDF`, `functional modules/VeritasDataForge`, `module/VeritasDataForge`, `VeritasDataForge` |
| VAP | `functional modules/VAP`, `module/VAP`, `VAP` |
| VTR | `functional modules/WorkOps/VTR`(2026-08-09 併入 VIA WorkOps;舊根 `functional modules/VTR` 留 VTR_MOVED.md 麵包屑)|
| Others | every other directory under `functional modules/` and `module/` |
| Supportive | `supportive modules/` |

**六槽標準佈局(2026-08-02 起)** — 每個 functional module 統一:
`engine/`(程式,追蹤)· `input/`(輸入;VRN 的研報 PDF git-ignored)·
`db/`(資料庫產品,ignored)· `template/`(模板數據,追蹤)·
`temp/`(暫存,ignored,One-Click 啟動自動清)· `output/`(其他輸出,ignored)。
既有慣例保留:VDF 來源仍讀 repo 根 `data/`;VAP 圖表仍寫 `<Base>/VAP/output`
(治理已鎖)。VRN 研報輸入標準槽為 `VRN/input/incoming/`,Control Tower 的
VRN RUN 優先掃此槽(fallback:Downloads v0156 歷史位置 → 候選清單)。

`VRN/` now carries its **full canonical tree in-repo** (imported 2026-08-02
from the operator workstation survivor copy): core pipeline `VRN_MDL001–008`
(Converter → LayoutExtractor → TableRestorer → OCR table/text → Consolidator →
APIDataFetcher → CrossValidator), VIS table-geometry reconstructors, 12 entry
/ops PS1 (Invoke-VRN, Guarded-Entry v217, PURE-NOHANG v2192, MQ-NoOCR v222,
Lane2/Lane3 preflights), SSOT store, freeze locks and staging evidence — 81
artifacts hash-locked in `VRN_Subsystem_Manifest.json` (py_compile + AST
validated; pip-vendor leaks quarantined under `_quarantine_pip_vendor/`).
Engines still execute on the operator workstation (OCR runtime); Lane2/Lane3
are read-only preflights reachable via `Start-VIA-OneClick.ps1 -VRN`.

`VDF/` originally carried an **integration anchor only** — a subsystem
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
& Stack Composer v009, header 帶 `data-frozen-lock=HEADER_EQUAL_HEIGHT_LOCKED`),
`ui/VAP_Workbench_v010.html` (v009 + 響應式陣列布局:桌機橫式/手機直式自動最
佳化、等大 auto-fill GRID、拖曳式軸槽 Dock、現代微動畫;兩個視覺鎖均保持)
and `spec/VIA_VAP_Spec_SSOT__Standalone.html` (VAP 規範 SSOT — Spec & Library
JSON single source of truth). All are SHA-256 registered in
`VAP_Subsystem_Manifest.json` and are REVIEW-ONLY under the same
no-canonical-mutation governance. The `header_visual_lock` gate is **LOCKED**:
the Veritas Header masthead 1d(鑑 · Veritas Auto Plot)from the design source
(`spec/Veritas_Intelligence_Analytics_UI_Design_Source.html`, Claude Design
project 68463cc8) is applied as the Workbench `#veritasMasthead` brand band —
above, and without touching, the frozen functional header — with the canonical
fragment hash-registered at `spec/Veritas_Header_Masthead_1d.html`.

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


---

## 併入補遺(2026-08-09 操作員令)

**VIA WorkOps 升格獨立子系統**:VMT(原 `supportive modules/VMT_SuperBOM`)與
VTR(原 `functional modules/VTR`)git mv 併入 `functional modules/WorkOps/{VMT,VTR}/`,
全部歷史保留。VIA WorkOps = WorkOps 核心(郵件×專案治理)+ VMT(追蹤自動化資料層)
+ VTR(會議紀錄修復)。SSOT 與支援工具共用不另立:`supportive modules/VIA_SSOT/`、
`WorkOps/engines/workops_lexicon.py`、org_lexicon、AutoCode Registry、audit_tools。
啟動器:`via-vmt`/`via-vmt-init` 已改指新家;`via-one` 前送 v0113;VTR 自帶入口隨樹遷移。
子系統 manifest:`WorkOps/VIA_WorkOps_Subsystem_Manifest.json`。


**商業定名(2026-08-09)**:VIA WorkOps 子系統對外定名 **Veritas WorkOps**;檔名/編號/動詞不動,品牌見板 v0118 起。
