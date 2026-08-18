# VeritasPulse (VPL) — Project Deck Engine

Local-first project & time intelligence. This package is the **S0 core + PPT
generation vertical slice**: it turns project data into a polished VIA-locked
PowerPoint deck in ~1 second.

## One-click run (Windows / PS7)

```powershell
pwsh -File .\Build-VeritasPulse.ps1
# force a clean venv rebuild:
pwsh -File .\Build-VeritasPulse.ps1 -Recreate
```

Creates an isolated `vpl_core` venv at `%USERPROFILE%\envs\vpl_core` (py -3.11),
installs pinned deps, builds the deck, opens the `output\` folder.

## Manual run

```bash
python build_deck.py                  # bundled demo project
python build_deck.py --db my.db --pid 1
```

Output: `output/VeritasPulse_ProjectDeck.pptx`

## Structure

```
VeritasPulse/
  vpl/
    theme.py            VIA Visual Lock v1 tokens (single source of truth)
    registry.py         module manifest — the modular-adjust control surface
    core/store.py       VPL-C01/C03  SQLite store + seed (12 entity types)
    core/env_arrange.py VPL-C00      env arrangement via Veritas supportive tools
    charts/optimize.py  VPL-I02/I03  auto-optimize pass + chart builders
    ppt/generate.py     VPL-OUT      python-pptx deck assembler
    app/template.html   data-driven UI shell (all views)
    app/build_app.py    VPL-APP      injects store data -> single-file app
  build_all.py          builds app + deck
  build_deck.py         deck only
  requirements.txt      pinned (numpy >=1.24,<2.0)
  Build-VeritasPulse.ps1  paste-and-run launcher
```

## The interactive app (圖像化 · 結構化 · 模組化)

`python build_all.py` emits `output/VeritasPulse_App.html` — one self-contained,
data-driven file. 12 views render from the embedded store JSON:

Dashboard · 每日清單 · 月曆 · 看板 · 甘特(可點) · 流程(拖節點+箭頭) ·
燈號 · 預算 · 記帳 · 利害關係人 · 資源 · 風險. Charts are pure SVG/CSS (no
runtime deps); static report charts use matplotlib (deck) / Seaborn (later).

### Easy to modularly adjust

Everything routes through `vpl/registry.py`:

```python
# add a feature  -> add one dict entry
{"id": "notes", "group": "EXEC", "label": "Notes", "icon": "check", "enabled": True}
# hide a feature -> "enabled": False
# reorder nav    -> reorder the list
```

The generator ships exactly the ENABLED modules; the UI builds its nav and views
from that manifest. No other file needs editing to toggle a feature.

## Arrange environment with Veritas

VeritasPulse provisions its venv THROUGH the VIA supportive ecosystem rather
than naive pip:

```bash
python -m vpl.core.env_arrange --root "<supportive_module path>" --env vpl_core
```

- HardGate posture recorded (Celeritas parallel **LOCKED**, Aegis network **LOCKED**)
- `VIA_EnvManager.def_scan_all_envs()` snapshots env health + conflicts
- `def_plan_install_request()` gates each dependency (risk routing, via_core
  whitelist, conflict-aware) — **plan-only by default**
- `VIS_InstallHealthRegistry` records the outcome (schema V1)
- VIA-locked HTML report at `output/vpl_env_arrangement.html`

Degrades gracefully (pinned fallback, clearly flagged) if the supportive
modules aren't reachable. The launcher runs this step automatically.

## Deck contents (7 slides)

1. Title (dark) · 2. Executive snapshot (KPI callouts + milestones) ·
3. Gantt timeline · 4. Budget plan-vs-actual + variance ·
5. Risk heatmap + top risks · 6. Stakeholder power/interest matrix ·
7. Closing (dark)

## Auto-optimize

`charts.optimize.optimize(ax)` brands and declutters ANY matplotlib axes:
VIA palette, despined frame, light grid, mono ticks, status colours. Add a new
chart by writing a builder and calling `optimize(ax)` — it inherits the look.

## Next (per architecture v1)

S1 Plan (ProjectBuilder/Gantt/Flow) · S2 Exec (checklist/kanban/reminders) ·
S3 Finance · S4 People & Risk · S5 Intel dashboard · S6 package + Google sync.
Seaborn (burndown/heatmap) joins `via_plot_basic`; Plotly for interactive views.
