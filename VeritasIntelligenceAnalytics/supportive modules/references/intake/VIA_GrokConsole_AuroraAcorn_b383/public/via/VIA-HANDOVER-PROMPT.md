# VIA TAKEOVER PROMPT — 鮮況 2026-09-07 15:09 CST → 接手日 2026-09-08
# Paste this entire file as the first message to the next human or AI.
# Language: follow the operator (Tony). Code/ids stay ASCII. Do not recreate conda. Do not force-push.

You are taking over **Veritas Intelligence Analytics (VIA)** after overnight close 2026-09-07 02:07 CST, refreshed **2026-09-07 15:09 CST**. Read this before any edit, install, or git command.

## 0. Who / where / what is NOT the same repo

| World | Path | Role |
|---|---|---|
| Operator | Tony, Windows, pwsh 7 only | Only person who runs git/conda/uv |
| Mother cwd | `C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics` | Where Tony types commands |
| Git root | `C:\Users\tonyk\movies-dataset` (repo `tonykuni/movies-dataset`) | Nested layout: files live under `VeritasIntelligenceAnalytics/` |
| Branch | `claude/via-system-followup-tz7k9t` | Last push `fd42f5d5` — **only** `VeritasIntelligenceAnalytics/logs/via_handover.md` (7 lines) |
| GitHub data lake | `C:\Users\tonyk\Github\movies-dataset\data\vdf\` | parquet hive; COPY_ONLY; do not delete originals |
| Local three DBs | `C:\新增資料夾\新增資料夾\VIA_db_part1_prices` / `VIA_db_part2_chips` / `VIA_db_part3_rest` | ingest sources; never delete |
| Seal packs | `C:\新增資料夾\新增資料夾\VETF_FINAL_SEAL_20260829_013330 (2)` and `VIA_ActiveETF_FINAL (1)` | AETF engines/UI; do not rewrite |
| Grok sandbox | Linux `/workspace` TypeScript console (this app) | **Not** the mother git tree. Mother has **no `src/`**. |

If a tool suggests `git add src`, it is wrong for the mother repo.

## 1. Invariants (never violate)

1. **ISO99** — isolate, do not delete. `via_iso_*` only. Ban: `conda remove`, `pip uninstall`, `Stop-Process`, `Remove-Item` on envs, `--force` git, BFG.
2. **功能只增不減** — no breaking changes; aliases stay; tools never leave the roster.
3. **LIVE is OFF** unless Tony explicitly opens dual gates (NET + KEY). Default `VIA_NET=0`.
4. **COPY_ONLY ingest** — year-partition with DuckDB from date/as_of/ym; ROC `1150826` → Gregorian `1911+year`.
5. **LKGC 2026-09-06** — uv index winner **Tsinghua**. Do not switch mirrors without consent. Additive only.
6. **Base stays thin.** Conflicting pins go to `via_iso_*` (numpy 1.26.4 base vs 2.1.1 via_vdf → `via_iso_numpy`). plotly already `via_iso_plotly`.
7. **DCT01–20 sealed.** Do not reopen. AST precision = py/ts; elastic = ps1/html/json.
8. **One console.** VIA Central Governance Console is the unique entry. Not a second system.
9. **pwsh 7.** Never cmd. Never `cd /d` inside pwsh. First command is enter-root, not random `.\scripts\...` from `%USERPROFILE%`.
10. **Git add splat** — a 1-element `$add` becomes a string; `git add -- @add` splits into characters. Always:
    `foreach ($p in $add) { git add -- $p }`
    Never `git add -A -- src` (pathspec fails; mother has no src).

## 2. What is DONE (do not redo)

- AETF universe **29** active TW ETFs. Book names + TW/GL scope. CACHE board matches mother HTML.
  - Leader **00981A 主動統一台股增長 ~2880 億, premium ~+3.52%**.
  - Flow all **0** because stats parquet has **no Δunits**. Do not invent LIVE flow.
  - `as_of` ROC handled; ETF book `as_of` was `1150824–1150826`.
  - Holdings × consensus: TARGET_PRICE = **MEDIAN**. FS +-% vs Adj; YF +-% vs YF last, not vs Adj.
  - iNAV: TWSE JSON `h` = **navPrev** (previous NAV), never MIS `h` (high).
- Ingest 2023→2026 COPY_ONLY into hive `year=YYYY` via DuckDB; akshare SKIP.
- EnvManager overlay: 拔除＝isolate; R3 “delete dead code”＝do not delete files; `via_isolated_*` renamed `via_iso_*`.
- uv: 3-mirror race + UVT-01–08 clash tools. GA-01–20 ≠ PS-01–20 ≠ UVT-01–08 (do not mix IDs).
- Central entry: PATH prepend `.venv-via_vdf\Scripts` if present; **iso slots never on PATH**.
- VIA_U **Taiwan Stock Revenue Analysis** = **VDF_ENG075** (aliases `VDF_REV`, `TWN_REV_ENG`, `VIA_U`). MOPS monthly **sii/otc files**, not per-ticker loop. `REV_START_YM=2023-01`. LIVE off. Quarter reports are a different table.
- Right rail (console + engine + WPF CmdMatrix): via-entry / via-path / via-aea / via-rev / via-gh / via-hand / via-handle. Chinese notes. Narrow, no overlap with left PS.
- Mega-prompt **sealed** 2026-09-06; future work uses `GOV_MEGA_BIND` overlay only.
- Last successful git: `fd42f5d5` on `claude/via-system-followup-tz7k9t` → `https://github.com/tonykuni/movies-dataset.git`.

## 3. OPEN / dirty (start here)

```
git -C C:\Users\tonyk\movies-dataset status -sb
```

Expected leftover (verify, do not assume):

- `VeritasIntelligenceAnalytics/VIA-ALL.cmd` may still be modified **unstaged** (listed in ADD but last commit was 1 file: handover.md only).
- `VeritasIntelligenceAnalytics/logs/via_aetf_board.html` untracked. Add only if `$env:VIA_GH_HTML='1'`.
- Mother cwd has no `src/`, `public/via`, `package.json` at the inner folder — those exist in the Grok sandbox, not necessarily here.
- AETF daily px for `00xxA` empty; holdings coverage yellow; cash flow needs units×navPrev when LIVE opens.
- `via_vdf` conda env may be missing; do **not** `conda create`. Use `.venv-via_vdf` if present, else report.
- CPython 3.13 on mother often has **no pandas** — DuckDB only (`fetchdf` will fail).

## 4. How to run (mother pwsh)

```
pwsh -NoLogo
Set-Location -LiteralPath C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics
$env:PYTHONNOUSERSITE='1'; $env:VIA_NET='0'; $env:VIA_LKGC='2026-09-06'
```

Short commands (after pasting CmdMatrix): `via-enter`, `via-path`, `via-aea`, `via-rev`, `via-hand`, `via-handle`, `via-gh`.

Git push pattern (preview first):

```
$prefer = @('VIA-ALL.cmd','logs/via_handover.md')
[string[]]$add = @($prefer | Where-Object { Test-Path $_ })
foreach ($p in $add) { git add -- $p }
git status -sb
# only then:
$env:VIA_GH_YES='1'
git commit -m 'message'
git push -u origin HEAD
```

Do not wrap logs in a PowerShell here-string that contains markdown fences — that truncates the paste (Tony already Ctrl+C’d one). Write log with `Set-Content` line arrays. Do not put `#requires` in the middle of an open session.

## 5. Product map (SSOT ids)

- Console 00 unique entry; VDF 01 lake; VRN 02 filings; Engine 03 SSOT; VAR 04 audit.
- AEA = VIA_AEA / VDF_ENG076. U = VIA_U / VDF_ENG075. CNS = VIA_CNS / VDF_ENG077 (FactSet×YF median).
- G1–G6 pipelines, write zones mutually exclusive (Zero-Hydra).
- Zones: MODULE / ENGINE / FUNCTION-LIB / OTHERS.
- Dual gates: NET, NLP. Accel mounts by default.

## 6. What to do next (ordered)

1. `git status -sb` from **git root** `movies-dataset`. Stage leftover `VIA-ALL.cmd` with foreach add if Tony wants it.
2. Confirm handover file at `VeritasIntelligenceAnalytics/logs/via_handover.md` on GitHub.
3. Do **not** open LIVE, akshare, yfinance, or MOPS fetch.
4. If asked to “complete AETF”: fill holdings/px from seal + lake only; no fake 2023 empty series.
5. If asked to “fix U”: keep monthly file planner `t21sc03_{year}_{month}_0.html`; CACHE analysis; latest complete month rule (before day 11, lag 2 months).
6. If asked env: scan pins, isolate numpy, uv Tsinghua, write `logs/env_governance.log`. Consent before APPLY. This host/sandbox does not spawn conda/uv.
7. UI: keep right rail small, Chinese wrap, left PS unobstructed.

## 7. Tone / delivery

Tony wants panoramic matrices, Chinese labels, one-paste pwsh, non-destructive, LEGO/SSOT. Do not give `cd /d` for pwsh. Do not gold-plate. Verify before claiming done. Features only increase.

When you reply, first print: branch, dirty files, AEA 29 check, U=ENG075 LIVE off, then the single next command — not a new architecture.
