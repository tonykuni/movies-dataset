# VIA Safe Polyglot Optimizer AIO v0102

Generated: 2026-06-17 20:16:13

This is a conservative single-file PowerShell orchestrator for Tony's Veritas Intelligence Analytics supportive modules.

## What it does

- Resolves these local files by default:
  - `C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Read_Me_VeritasNexusCore.md`
  - `C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VeritasNexusCore.ps1`
  - `C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1`
- Copies them into a sandbox run directory.
- Runs three capped panoramic analysis rounds.
- Performs PowerShell AST parsing and safety pattern scanning.
- Generates CSV / JSON / HTML matrix reports.
- Generates 10 workflow function areas × 3 languages × Top 15 local free tools.
- Embeds Top 25 failures and solutions.
- Writes a registry and active pointer under `_nexus_registry`.
- Optionally writes a launcher `Invoke-VIA-SafePolyglotOptimizer.ps1`.

## Safety policy

Default mode is report-only. The AIO script itself does not execute destructive delete, recycle-bin clearing, process-kill, or Docker volume-prune commands. It writes only reports, registry JSON, copied sandbox files, and an optional launcher.

## Recommended run

```powershell
pwsh -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1" -SelfTest -RegisterLauncher -OpenReport
```

## Optional child self-test

Only when you are ready to execute copied child scripts in the sandbox:

```powershell
pwsh -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1" -SelfTest -RegisterLauncher -OpenReport -RunSandboxSelfTest
```

The child self-test mode runs copied `.ps1` files with `-SelfTest -NoBrowser` and captures logs. It does not run the originals directly.
