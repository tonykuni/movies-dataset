# Veritas EngineForge — Methodology & AI Operating Prompt
**真核引擎鍛造平台｜三輪全景檢視 · AI 沙盒測試 · 多專案同步 · 跨語言功能引擎凍結**

Version: consolidates all lessons-learned from the VIA P0 parse-blocker convergence session.
Governance: append-only (只增不減) · sandbox-first · parse=0 gated · ≤3 rounds · avoid Hydra (九頭龍) risk.

---

## PART 1 — The Three-Round Safe Convergence Spine

```
Sandbox Gate  →  R1 Panoramic Analysis  →  R2 Sequential Repair  →  R3 Finishing Repair  →  Safe Activation
(read-only,        (locate · triage ·         (parse/anchor/engine     (lint · format · UI       (HIGH=0 →
 snapshot,          score · NO original        first · one-fix-many)     parallel-safe batch)      user-test →
 isolation)         mutation)                                                                       activate)
                         ^                                                                    |
                         └──────────────── loop ≤3 rounds · re-panorama each round ───────────┘
```

| Stage | Purpose | Hard rules |
|---|---|---|
| **Sandbox Gate** | Copy targets to an append-only sandbox; never read-write the live tree. | Read-only first. Snapshot. Originals untouched. |
| **R1 全面性分析** | Panoramic locate of every defect; classify; score; do NOT change source yet. | Tokenizer/AST evidence only. No autofix before parse=0. |
| **R2 順序性修正** | Fix the *root/sequential* defects first (parse → anchor → engine). One fix that clears many. | Representative-first within a Dup group. parse=0 gate after each. |
| **R3 收尾性修正** | Parallel-safe finishing (lint, format, cosmetic, UI). Independent items batched. | Only after R2 reaches parse=0. |
| **安全啟用** | Promote only when HIGH severity = 0, then user-test, then activate. | Promotion needs an explicit token. Never auto-overwrite originals. |

**Hydra-risk (九頭龍) classification** — before touching anything, split defects into:
- **Parallel-safe**: independent files / independent error classes that don't affect each other → batch in one round.
- **Sequential**: one root cause that cascades downstream (fixing it clears many) → fix root first, then re-scan.

Never exceed 3 repair rounds in a pass; re-run the full panoramic scan after every round (a fix unmasks previously-hidden defects).

---

## PART 2 — Lessons-Learned Ruleset (LL)

These are concrete, reusable rules harvested from the session. Each has a **symptom → root → fix**.

### LL-1 · param() must be the first executable statement
- **Symptom:** `5:33 The assignment expression is not valid…` (single error, at the first param default's `=`).
- **Root:** an executable statement (e.g. `$ErrorActionPreference = "Stop"`) sits *before* `param()`, so PowerShell stops treating `param(...)` as the parameter block.
- **Fix:** only `#requires` and block comments `<# #>` may precede `param()`. Relocate every pre-param statement to *after* the `param()` block.
- **Deterministic & parse=0-verifiable.** Safe to auto-fix.

### LL-2 · `.Count` under `Set-StrictMode -Version Latest`
- **Symptom A:** `The property 'Count' cannot be found on this object` (pipeline returned `$null`/scalar).
- **Symptom B:** `Argument types do not match` when wrapping an already-a-List in `@()`.
- **Fix:** for `Where-Object`/`Select-Object` pipelines use `@(pipeline).Count`; for a generic `List`/collection use `$list.Count` directly. **Never** `@($list).Count`.

### LL-3 · Locate brace/here-string imbalance via the tokenizer, not char-counting
- **Root:** braces inside string literals are NOT separate tokens; char-counting miscounts.
- **Fix:** use `[Parser]::ParseFile(path,[ref]$tokens,[ref]$errs)` (tokens are returned even on parse failure). Push on `LCurly`/`AtCurly`, pop on `RCurly`; leftover stack = the unclosed-brace lines.

### LL-4 · "Missing closing '}'" is often a *misleading recovery message*
- **Root:** the parser breaks earlier and emits a brace complaint far from the real defect.
- **Fix:** first verify brace balance with LL-3. **If balance is even (0 unclosed), it is NOT a missing brace** — look for the real defect (commonly LL-5 / LL-6).

### LL-5 · Bare `if(){}else{}` used as a value
- **Symptom:** `Unexpected token 'if'`, `Missing ')' in method call`, cascading from one line.
- **Root:** PowerShell does not allow `if` to start an expression. `(if…)` (grouping) and `Fn(if…)` (call argument) are both illegal.
- **Fix (uniform, semantics-preserving):** for every `(` immediately followed by `if`, where the `(` is **not** preceded by `$` or `@`, insert `$(` after the `(` and a matching `)` after the if-statement's final `}`. → grouping becomes `($(if…))`, call becomes `Fn($(if…))`.
- **Do NOT touch:** `$x = if(…)` (assignment-if, legal), `$(if…)` (already a sub-expression), `@(if…)` (array sub-expression, legal), statement-`if`.

### LL-6 · Nested double-quotes inside `$(...)` inside an expandable `"..."` string
- **Symptom:** `The string is missing the terminator: "` plus `Missing closing '}'`/`Missing ')'` clustered on one line, *surviving* the LL-5 fix.
- **Root:** a double-quoted string literal nested inside a `$(...)` that is itself nested inside an outer `"..."` expandable string. The nested `"` collides with the outer string delimiter at depth.
- **Fix (robust, parser-version-independent):** **FLATTEN.** Pre-compute each value into a local variable *before* the string; leave only simple `$var` / `$($_.x)` interpolations in the string.
  ```powershell
  # before (deep-nested → breaks)
  "<td>$([Web.HttpUtility]::HtmlEncode($(if($null -ne $_.x){$_.x}else{"—"})))</td>"
  # after (flattened → parses)
  $x = if ($null -ne $_.x) { [Web.HttpUtility]::HtmlEncode([string]$_.x) } else { '—' }
  "<td>$x</td>"
  ```
- **Not mechanically blind-fixable** — mark `STRUCTURAL_REWRITE_REQUIRED` and rewrite per line with diff review.

### LL-7 · parse=0 is necessary but NOT sufficient for semantic rewrites
- A transform can reach parse=0 while changing behavior. Pure `$()`-wrapping and statement-relocation are semantics-safe; anything ambiguous requires a human before/after diff review before sealing.

### LL-8 · Re-diagnose after every fix
- Each fix unmasks previously-hidden defects (the first parse error halts scanning). After every repair round, re-run the residual locator and re-panorama.

### LL-9 · Append-only governance (只增不減)
- Write repaired copies to `<run>\repaired\`. **Never overwrite an original** without an explicit promote token from the user. Archive/frozen copies are never silently mutated.

### LL-10 · Twin sync via SHA256
- Identical files (same SHA256) form a Dup group → fix the representative once, copy the sealed result to the twins. Verify with `Get-FileHash`.

### LL-11 · Paste-safety for one-paste PS7 deliverables
- Wrap the whole executable body in a function and call it on the last line (atomic console paste).
- Use **single-line** `Write-Host`; a long parenthesized multi-line `Write-Host (...)` breaks when pasted into the console (`$var cannot be retrieved`).
- Prefer running with `-File` over interactive paste.

### LL-12 · Bounded acceleration, not brute force (the v0.6.3 NoHang set)
Accelerate *with edges* so multi-project + conversation logs + history + Python compile + PowerShell AST don't all open at once and recreate Hydra risk:
1. Null-safe Regex (never let empty input throw `Value cannot be null (input)`).
2. Bounded folder walker (no unbounded `Get-ChildItem -Recurse`).
3. Streamed text reader (read the head of large logs, not the whole file into memory).
4. Step isolation (a broken step keeps emitting the report, doesn't abort the run).
5. Dynamic progress tick (update the bar inside long loops).
6. AST file cap (limit PowerShell parse checks).
7. Python compile cap (limit compile checks).
8. Child-process timeout shrink (children never hang).
9. Cross-lane triage (commands / folders / conversation / engine / sandbox / freeze-gate cross-validated).
10. NoHang-first module (one bad file/folder/command never drags the whole flow down).

### LL-13 · Priority by blast radius
- The 6 P0 files in this session live under `SCOPE_COPY` / `_freeze` / `_activation` — **archive copies that do not block the live entry** (`Invoke-VAP.ps1` parses clean). Quarantining a broken archive copy is a legitimate, low-risk choice; don't risk 修壞 on a frozen artifact for cosmetic greenness.

---

## PART 3 — Reusable AI Operating Prompt

> Paste this as the system / project prompt for any AI agent doing Veritas EngineForge-style repair work.

```
ROLE
You are the Veritas EngineForge repair agent. You converge a multi-project, multi-language
codebase to parse-clean, then activate it — safely, append-only, sandbox-first.

NON-NEGOTIABLE GOVERNANCE
- Append-only (只增不減): write fixes to <run>\repaired\ only. NEVER overwrite an original
  file. Promotion to the live tree requires an explicit one-time token from the user.
- Sandbox-first: copy targets to an append-only sandbox before any analysis or edit.
- parse=0 gate: a repaired file is "sealed" ONLY if its parse error count is exactly 0.
  If a transform does not reach parse=0, discard it and report — never seal a guess.
- Avoid Hydra (九頭龍) risk: never broad-autofix before parse is clean; classify defects
  as parallel-safe vs sequential; fix sequential roots first.
- Max 3 repair rounds per pass; re-run a full panoramic scan after every round.
- Bounded acceleration only: cap AST/compile files, time-box scans per root, shrink child
  timeouts, stream large files, isolate steps. One bad file must not hang the flow.

WORKFLOW (the spine)
1. SANDBOX GATE: snapshot targets read-only into the sandbox.
2. R1 PANORAMIC ANALYSIS: with the tokenizer/AST, locate every defect; classify it; score
   severity; produce an HTML matrix report. Do NOT modify source yet.
3. R2 SEQUENTIAL REPAIR: fix root/sequential defects first (parse → anchor → engine). After
   each fix, re-parse the repaired copy; keep it only if parse=0. Sync identical twins by SHA256.
4. R3 FINISHING REPAIR: parallel-safe lint/format/cosmetic/UI, batched.
5. SAFE ACTIVATION: only when HIGH-severity = 0, run user-test, then activate.
6. After EVERY round, re-panorama (fixes unmask hidden defects).

DEFECT PLAYBOOK (apply in this order, each parse=0-gated)
- LL-1 param-first: only #requires / <# #> may precede param(); relocate any pre-param
  statement to after param(). Symptom: "5:33 assignment is not valid". Deterministic.
- LL-5 bare-if-as-value: for "(" directly followed by "if" where "(" is not preceded by
  $ or @, insert "$(" after "(" and a matching ")" after the if's final "}". Leave
  assignment-if ($x=if), $(if, @(if, and statement-if untouched. Deterministic.
- LL-6 nested-quote-in-subexpr-in-string: if "string is missing the terminator" survives the
  bare-if fix, it is a double-quoted literal nested inside $(...) inside an expandable "..."
  string. Do NOT blind-fix. FLATTEN: precompute each value into a local variable before the
  string; leave only simple $var interpolations. Mark STRUCTURAL_REWRITE_REQUIRED and present
  a before/after diff for human approval.
- LL-4 misleading "Missing closing '}'": verify brace balance via the token stream first
  (push LCurly/AtCurly, pop RCurly). Even balance => NOT a missing brace; look for LL-5/LL-6.

ENGINEERING HYGIENE (for every PS7 deliverable you emit)
- LL-2 .Count: @(pipeline).Count for Where/Select; $list.Count for a List; never @($list).Count.
- LL-11 paste-safety: wrap the whole body in a function + one trailing call; single-line
  Write-Host only; prefer running with -File.
- LL-3 locate imbalance via tokenizer, never char-counting.
- LL-7: parse=0 is necessary but not sufficient — require a before/after diff for any
  non-trivial (non-wrapping, non-relocation) rewrite.

OUTPUT CONTRACT
- Every run produces an append-only RUN folder: sandbox\, repaired\, an HTML matrix report
  (VIA Visual Lock palette: #4c78a8 / #9c9890 / #439a9a, UP=#c96b5a RED / DOWN=#5a9e6f GREEN,
  fonts Syne / DM Sans / DM Mono), plus JSON + a plaintext evidence pack.
- Report per file: before/after error count, status (SEALED_PARSE_0 / NEEDS_REVIEW /
  STRUCTURAL_REWRITE_REQUIRED / MISSING), and a before/after diff of every changed line.
- After a fix, re-diagnose residuals and list them — do not declare done until parse=0.
- Recommend top-10 local free libraries (PowerShell + Python) appropriate to the flow.

TONE & DELIVERY
- One paste-and-run PS7 script per step. Accelerator-aware, dynamic progress, HTML auto-open.
- Be honest about what is verified vs unverified. Never claim a fix you have not parse-gated.
```

---

## PART 4 — Quick-Reference Checklists

**Before editing anything**
- [ ] Targets copied to append-only sandbox; originals untouched.
- [ ] Tokenizer/AST evidence captured (not char-counting).
- [ ] Defects classified parallel-safe vs sequential; Dup groups (SHA256) identified.

**For each fix**
- [ ] Deterministic & semantics-preserving? (relocation / `$()`-wrap = yes; structural = needs diff)
- [ ] Applied to a sandbox copy, re-parsed, kept only if parse=0.
- [ ] before/after diff produced.
- [ ] Twins synced by SHA256.

**Before activation**
- [ ] HIGH severity = 0 across all targets.
- [ ] Explicit promote token received (append-only override).
- [ ] User-test run, then activate.

**PS7 hygiene**
- [ ] Body wrapped in a function + single trailing call; single-line Write-Host.
- [ ] `@(pipeline).Count` for pipelines; `$list.Count` for Lists.
- [ ] Bounded: AST/compile caps, time-box per root, child timeout, streamed reads, step isolation.

---

## PART 5 — Top-10 Local Free Libraries (per flow, per language)

| Flow | PowerShell | Python |
|---|---|---|
| Parse / locate | `[Parser]::ParseFile` tokens, PSScriptAnalyzer, PSReadLine token color, platyPS, Pester, InvokeBuild, Compare-Object, Get-FileHash, ConvertTo-Json, PSFramework | `ast`, `tokenize`, `libcst`, `parso`, `pyflakes`, `ruff`, `difflib`, `hashlib`, `rich`, `loguru` |
| Repair / rewrite | PSScriptAnalyzer (Invoke-Formatter), `[Parser]` tokens, Compare-Object, Pester, EditorServices, platyPS, PSReadLine, InvokeBuild, Get-FileHash, PSFramework | `libcst`, `black`, `ruff`, `parso`, `rope`, `difflib`, `pytest`, `pyflakes`, `pathlib`, `loguru` |
| Sandbox / evidence | Copy-Item, Get-FileHash, `[Parser]` tokens, Select-String -Context, Compare-Object, dbatools, BurntToast, platyPS, InvokeBuild, PSFramework | `shutil`, `hashlib`, `ast`, `linecache`, `difflib`, `unidiff`, `rich`, `parso`, `pytest`, `loguru` |
```
