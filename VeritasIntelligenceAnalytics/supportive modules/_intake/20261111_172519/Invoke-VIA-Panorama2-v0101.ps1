# CELERITAS-TEMPLATE-JOIN
#Requires -Version 7.0
# VIA PANORAMA2 v0101 - L117 command shape: PS lands files, launches ONE python verb (CGC_Panorama2Roots_v0101.py), opens the U/I it produces.
# Two-root panoramic scan + local git + Graphify + tool enablement. Read-only toward VIA roots; proposals land in RUN dir.

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'
$__env0 = @{ PATH = $env:PATH; TEMP = $env:TEMP; PYTHONUTF8 = $env:PYTHONUTF8; VIA_CELERITAS_ROOT = $env:VIA_CELERITAS_ROOT }

# ---------- 1. safe cleanup ----------
[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
try { [System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal' } catch {}
$ts     = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path $env:TEMP "VIA_RUN_${ts}_PANORAMA2"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$env:PYTHONUTF8 = '1'

# ---------- 2. accelerator (auto-detect, guarded) ----------
$accel = 'NONE'
$vcRoot = $env:VIA_CELERITAS_ROOT
if (-not ($vcRoot -and (Test-Path (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1')))) {
  $probe = @((Join-Path $env:OneDrive 'Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules'),
             (Join-Path $env:USERPROFILE 'VIA_Workbench_Local\movies-dataset\VeritasIntelligenceAnalytics\supportive modules'),
             (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics\supportive modules')) | Where-Object { Test-Path (Join-Path $_ 'VeritasCeleritas.PS7.AutoImport.ps1') } | Select-Object -First 1
  if ($probe) { $vcRoot = $probe; $env:VIA_CELERITAS_ROOT = $probe; $accel = 'AutoDetected' }
}
if ($vcRoot -and (Test-Path (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'))) {
  try { . (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'); $accel += '+AutoImport' } catch { $accel += '+AutoImport-FAILED' }
}

# ---------- 3. roots (two folders) + engine file ----------
$rootCands = @($env:VIA_ROOT_A,
               (Join-Path $env:OneDrive 'Documents\movies-dataset\VeritasIntelligenceAnalytics'),
               (Join-Path $env:USERPROFILE 'VIA_Workbench_Local\movies-dataset\VeritasIntelligenceAnalytics'),
               (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics'),
               (Join-Path $env:USERPROFILE 'VIA-VDF-VRN'),
               'C:\VIA') | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
$roots = @($rootCands | Select-Object -First 2)
$dl  = Join-Path $env:USERPROFILE 'Downloads'
$eng = Get-ChildItem -Path $dl, $PSScriptRoot -Filter 'CGC_Panorama2Roots_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object { [int]([regex]::Match($_.Name, 'v(\d+)').Groups[1].Value) } -Descending | Select-Object -First 1
if (-not $eng) { Write-Host 'RED engine CGC_Panorama2Roots_v*.py not found in Downloads' -ForegroundColor Red; return }
$engRun = Join-Path $runDir $eng.Name
Copy-Item -LiteralPath $eng.FullName -Destination $engRun -Force
if ($vcRoot) { $env:PYTHONPATH = $vcRoot }

Write-Host "`nVIA PANORAMA2  accel=$accel  A=$($roots[0])  B=$(if ($roots.Count -gt 1) { $roots[1] } else { '-' })  run=$runDir" -ForegroundColor Cyan

# ---------- 4. ONE python verb via bridge ----------
$argv = @($runDir) + $roots
$rc = -1
if (Get-Command Invoke-VCPython -ErrorAction SilentlyContinue) {
  try { Invoke-VCPython -Script $engRun -Arguments $argv; $rc = $LASTEXITCODE } catch { $rc = -2; Write-Host "RED Invoke-VCPython: $($_.Exception.Message)" -ForegroundColor Red }
}
if ($rc -ne 0) {
  $py = Get-Command py.exe -ErrorAction SilentlyContinue
  if ($py) { & $py.Source -3 -B $engRun @argv; $rc = $LASTEXITCODE }
  else { $py = Get-Command python.exe -ErrorAction SilentlyContinue; if ($py) { & $py.Source -B $engRun @argv; $rc = $LASTEXITCODE } else { Write-Host 'RED no python' -ForegroundColor Red } }
}

# ---------- 5. open U/I + paste pack ----------
$html = Join-Path $runDir 'VIA_Panorama2.html'
if (Test-Path $html) { try { Invoke-Item $html } catch {} }
$pp = Join-Path $runDir 'paste_pack.txt'
Write-Host "`n==== PASTE BACK (<=300 lines) ====" -ForegroundColor Yellow
if (Test-Path $pp) { Get-Content $pp | ForEach-Object { Write-Host $_ -ForegroundColor $(if ($_ -match '^(RED|CONFLICT-)') { 'Red' } else { 'Yellow' }) } }
else { Write-Host "RED paste_pack missing rc=$rc run=$runDir" -ForegroundColor Red }
Write-Host "RC=$rc ACCEL=$accel RUN=$runDir" -ForegroundColor Yellow

# ---------- 6. restore env ----------
$env:PATH = $__env0.PATH; $env:TEMP = $__env0.TEMP; $env:PYTHONUTF8 = $__env0.PYTHONUTF8; $env:VIA_CELERITAS_ROOT = $__env0.VIA_CELERITAS_ROOT
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
