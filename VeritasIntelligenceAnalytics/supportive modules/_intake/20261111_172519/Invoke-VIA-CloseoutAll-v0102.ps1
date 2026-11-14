# CELERITAS-TEMPLATE-JOIN
#Requires -Version 7.0
# VIA CLOSEOUT-ALL v0102 - thin tail over v0101: auto-expands files*.zip / wl*.zip in Downloads and searches recursively (card downloads arrive zipped)
# VIA CLOSEOUT-ALL v0101 - one PS for the four Downloads files:
#   lane A  CGC_Panorama2Roots_v*.py   (launcher Invoke-VIA-Panorama2-v*.ps1 absorbed)
#   lane B  CGC_CloseoutIntegrate_v*.py (launcher Invoke-VIA-Closeout-v*.ps1 absorbed)
# Highest version of each engine in Downloads wins. Two lanes in parallel, live %, merged paste pack <=300 lines, index HTML.
# Writes: RUN dir + whatever the engines already declare (Closeout: _intake new files only, ledger append if exists). Nothing else.

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'
$__env0 = @{ PATH = $env:PATH; TEMP = $env:TEMP; PYTHONUTF8 = $env:PYTHONUTF8; PYTHONPATH = $env:PYTHONPATH; VIA_CELERITAS_ROOT = $env:VIA_CELERITAS_ROOT }

# ---------- 1. safe cleanup (own process only) ----------
[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
try { [System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal' } catch {}
$ts     = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path $env:TEMP "VIA_RUN_${ts}_CLOSEOUT_ALL"
$runA   = Join-Path $runDir 'panorama2'
$runB   = Join-Path $runDir 'closeout'
New-Item -ItemType Directory -Path $runDir, $runA, $runB -Force | Out-Null
$env:PYTHONUTF8 = '1'

# ---------- 2. accelerator (auto-detect, guarded) ----------
$accel = 'NONE'; $vcRoot = $env:VIA_CELERITAS_ROOT
if (-not ($vcRoot -and (Test-Path (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1')))) {
  $probe = @((Join-Path $env:OneDrive 'Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules'),
             (Join-Path $env:USERPROFILE 'VIA_Workbench_Local\movies-dataset\VeritasIntelligenceAnalytics\supportive modules'),
             (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics\supportive modules')) | Where-Object { Test-Path (Join-Path $_ 'VeritasCeleritas.PS7.AutoImport.ps1') } | Select-Object -First 1
  if ($probe) { $vcRoot = $probe; $env:VIA_CELERITAS_ROOT = $probe; $accel = 'AutoDetected' }
}
if ($vcRoot -and (Test-Path (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'))) {
  try { . (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'); $accel += '+AutoImport' } catch { $accel += '+AutoImport-FAILED' }
  $env:PYTHONPATH = $vcRoot
}

# ---------- 3. roots, python, engines (newest version each) ----------
$roots = @(@($env:VIA_ROOT_A,
           (Join-Path $env:OneDrive 'Documents\movies-dataset\VeritasIntelligenceAnalytics'),
           (Join-Path $env:USERPROFILE 'VIA_Workbench_Local\movies-dataset\VeritasIntelligenceAnalytics'),
           (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics'),
           (Join-Path $env:USERPROFILE 'via-vdf-vrn'),
           'C:\VIA') | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique | Select-Object -First 2)
$py = (Get-Command py.exe -ErrorAction SilentlyContinue).Source
$pyArgs = @('-3', '-B')
if (-not $py) { $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source; $pyArgs = @('-B') }
if (-not $py) { Write-Host 'RED no python on PATH' -ForegroundColor Red; return }
$dl = Join-Path $env:USERPROFILE 'Downloads'
$unz = Join-Path $dl '_via_unzip'
New-Item -ItemType Directory -Path $unz -Force | Out-Null
foreach ($z in @(Get-ChildItem -Path $dl -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(files( \(\d+\))?|wl\d{4})\.zip$' })) {
  $dest = Join-Path $unz ($z.BaseName -replace '[^\w\-]', '_')
  if (-not (Test-Path $dest) -or ((Get-Item $dest).LastWriteTime -lt $z.LastWriteTime)) { try { Expand-Archive -LiteralPath $z.FullName -DestinationPath $dest -Force } catch {} }
}
function Newest($pattern) {
  Get-ChildItem -Path $dl, $PSScriptRoot -Recurse -Depth 3 -Filter $pattern -File -ErrorAction SilentlyContinue |
    Sort-Object { [int]([regex]::Match($_.Name, 'v(\d+)').Groups[1].Value) }, LastWriteTime -Descending | Select-Object -First 1
}
$engA = Newest 'CGC_Panorama2Roots_v*.py'
$engB = Newest 'CGC_CloseoutIntegrate_v*.py'
if (-not $engA -or -not $engB) { Write-Host "RED engine missing: Panorama2=$($engA.Name) Closeout=$($engB.Name)" -ForegroundColor Red; return }
Copy-Item $engA.FullName (Join-Path $runA $engA.Name) -Force
Copy-Item $engB.FullName (Join-Path $runB $engB.Name) -Force
$batch = @('CGC_Panorama2Roots_v*.py', 'Invoke-VIA-Panorama2-v*.ps1', 'Invoke-VIA-Closeout-v*.ps1', 'Invoke-VIA-AllInOne-v*.ps1', 'Invoke-VIA-ToolInstall-W4-v*.ps1', 'Invoke-VIA-OneShot-W4-v*.ps1', 'Invoke-VIA-CloseoutAll-v*.ps1') |
  ForEach-Object { Newest $_ } | Where-Object { $_ } | Select-Object -ExpandProperty FullName

Write-Host "`nVIA CLOSEOUT-ALL  accel=$accel  A=$($roots[0])  B=$(if ($roots.Count -gt 1) { $roots[1] } else { '-' })" -ForegroundColor Cyan
Write-Host "engines: $($engA.Name) | $($engB.Name)   run=$runDir" -ForegroundColor Cyan

# ---------- 4. two lanes (each engine = one python verb; stdout -> log; engine writes its own paste_pack/HTML) ----------
$lane = {
  param($py, $pyArgs, $eng, $argv, $log, $cwd)
  Set-Location $cwd
  & $py @pyArgs $eng @argv *> $log
  return $LASTEXITCODE
}
$argA = @($runA) + $roots
$argB = @($runB) + @($roots | Select-Object -First 1) + @($batch)
$logA = Join-Path $runA 'engine.log'; $logB = Join-Path $runB 'engine.log'
$jobs = @{
  A = Start-ThreadJob -ScriptBlock $lane -ArgumentList $py, $pyArgs, (Join-Path $runA $engA.Name), $argA, $logA, $runA
  B = Start-ThreadJob -ScriptBlock $lane -ArgumentList $py, $pyArgs, (Join-Path $runB $engB.Name), $argB, $logB, $runB
}

# ---------- 5. live progress (parse each engine's TOTAL nn% from its log tail) ----------
function Pct($log) {
  if (-not (Test-Path $log)) { return 0 }
  try { $t = Get-Content $log -Raw -ErrorAction SilentlyContinue; $m = [regex]::Matches($t, 'TOTAL\s+(\d{1,3})%'); if ($m.Count) { return [int]$m[$m.Count - 1].Groups[1].Value } } catch {}
  return 0
}
function Bar($p) { $n = [int]($p / 5); return ('#' * $n).PadRight(20, '.') }
function Width { try { return [Math]::Max(60, [Console]::WindowWidth - 1) } catch { return 120 } }
$t0 = Get-Date; $wall = 1500
Write-Host ("`n" * 3)
while ($true) {
  $pa = Pct $logA; $pb = Pct $logB
  $sa = $jobs.A.State; $sb = $jobs.B.State
  if ($sa -eq 'Completed') { $pa = 100 }; if ($sb -eq 'Completed') { $pb = 100 }
  try { [Console]::SetCursorPosition(0, [Math]::Max(0, [Console]::CursorTop - 3)) } catch {}
  $w = Width
  Write-Host ('{0,-26} [{1}] {2,3}% {3}' -f 'A Panorama2 (2 roots+git+graph)', (Bar $pa), $pa, $sa).PadRight($w) -ForegroundColor $(if ($sa -eq 'Completed') { 'Green' } else { 'Cyan' })
  Write-Host ('{0,-26} [{1}] {2,3}% {3}' -f 'B Closeout (6 managers+intake)', (Bar $pb), $pb, $sb).PadRight($w) -ForegroundColor $(if ($sb -eq 'Completed') { 'Green' } else { 'Cyan' })
  Write-Host ('{0,-26} [{1}] {2,3}%  elapsed {3}s' -f 'TOTAL', (Bar ([int](($pa + $pb) / 2))), [int](($pa + $pb) / 2), [int]((Get-Date) - $t0).TotalSeconds).PadRight($w) -ForegroundColor White
  $done = @($jobs.Values | Where-Object { $_.State -in 'Completed', 'Failed', 'Stopped' }).Count
  if ($done -ge 2 -or ((Get-Date) - $t0).TotalSeconds -gt $wall) { break }
  Start-Sleep -Milliseconds 600
}
$rc = @{}
foreach ($k in 'A', 'B') { $j = $jobs[$k]; if ($j.State -eq 'Running') { Stop-Job $j -ErrorAction SilentlyContinue; $rc[$k] = -999 } else { $r = Receive-Job $j -ErrorAction SilentlyContinue; $rc[$k] = $(if ($null -ne $r) { [int]($r | Select-Object -Last 1) } else { -1 }) }; Remove-Job $j -Force -ErrorAction SilentlyContinue }

# ---------- 6. merge paste packs + index HTML ----------
$ppA = Join-Path $runA 'paste_pack.txt'; $ppB = Join-Path $runB 'paste_pack.txt'
$htmlA = Join-Path $runA 'VIA_Panorama2.html'; $htmlB = Join-Path $runB 'VIA_Closeout.html'
$linesA = if (Test-Path $ppA) { @(Get-Content $ppA) } else { @("RED panorama2 no paste_pack rc=$($rc.A) log=$logA") }
$linesB = if (Test-Path $ppB) { @(Get-Content $ppB) } else { @("RED closeout no paste_pack rc=$($rc.B) log=$logB") }
$linesA = @($linesA | Where-Object { $_ -notmatch '^NEXT:' }); $linesB = @($linesB | Where-Object { $_ -notmatch '^NEXT:' })
$capA = [Math]::Min($linesA.Count, 140); $capB = [Math]::Min($linesB.Count, 296 - $capA - 4)
$merged = @("CLOSEOUT-ALL $ts accel=$accel rcA=$($rc.A) rcB=$($rc.B)", '=== A PANORAMA2 ===') + @($linesA | Select-Object -First $capA) + @('=== B CLOSEOUT ===') + @($linesB | Select-Object -First $capB)
$merged = @($merged | Select-Object -First 299) + @('NEXT: paste this pack back; GREEN managers = seal, YELLOW = six-class fix list, RED/CONFLICT first')
$ppAll = Join-Path $runDir 'paste_pack_ALL.txt'
$merged | Set-Content -Path $ppAll -Encoding UTF8
$css = ':root{--g:#2EB872;--y:#F5C518;--r:#E0342B;--k:#9AA3AD}body{font:12px/1.4 "Segoe UI",system-ui;background:#F7F8FA;color:#1F2937;margin:16px}h1{font-size:15px;margin:10px 0 6px}.l{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:6px}.GREEN{background:var(--g)}.YELLOW{background:var(--y)}.GRAY{background:var(--k)}.RED{background:var(--r);animation:bl 1.6s infinite}@keyframes bl{50%{opacity:.25}}table{border-collapse:collapse;background:#fff;width:100%;max-width:1100px}th,td{border:1px solid #E5E7EB;padding:3px 7px;text-align:left}th{background:#EEF1F5}pre{background:#fff;border:1px solid #E5E7EB;padding:8px;max-height:60vh;overflow:auto;font-size:11px}a{color:#1F4E9A}'
$lampA = if ($rc.A -eq 0 -and (Test-Path $htmlA)) { 'GREEN' } elseif ($rc.A -eq -999) { 'YELLOW' } else { 'RED' }
$lampB = if ($rc.B -eq 0 -and (Test-Path $htmlB)) { 'GREEN' } elseif ($rc.B -eq -999) { 'YELLOW' } else { 'RED' }
$enc = { param($s) [System.Net.WebUtility]::HtmlEncode([string]$s) }
$idx = @("<!doctype html><html><head><meta charset='utf-8'><title>VIA CLOSEOUT-ALL $ts</title><style>$css</style></head><body>",
         "<h1>VIA CLOSEOUT-ALL &middot; $ts</h1><table><tr><th></th><th>Lane</th><th>Engine</th><th>rc</th><th>Report</th></tr>",
         "<tr><td><span class='l $lampA'></span></td><td>A Panorama2</td><td>$($engA.Name)</td><td>$($rc.A)</td><td><a href='file:///$($htmlA -replace '\\','/')'>VIA_Panorama2.html</a></td></tr>",
         "<tr><td><span class='l $lampB'></span></td><td>B Closeout</td><td>$($engB.Name)</td><td>$($rc.B)</td><td><a href='file:///$($htmlB -replace '\\','/')'>VIA_Closeout.html</a></td></tr></table>",
         "<h1>Merged paste pack (&le;300 lines)</h1><pre>$(& $enc ($merged -join "`n"))</pre></body></html>")
$htmlAll = Join-Path $runDir "VIA_CLOSEOUT_ALL_${ts}.html"
$idx -join "`n" | Set-Content -Path $htmlAll -Encoding UTF8
try { Invoke-Item $htmlAll } catch {}

# ---------- 7. console summary: yellow = paste back, red = errors ----------
Write-Host "`n==== PASTE BACK ====" -ForegroundColor Yellow
$merged | ForEach-Object { Write-Host $_ -ForegroundColor $(if ($_ -match '^(RED|CONFLICT-)') { 'Red' } else { 'Yellow' }) }
Write-Host "HTML=$htmlAll" -ForegroundColor Yellow
Write-Host "PACK=$ppAll" -ForegroundColor Yellow
try { Set-Clipboard -Value ($merged -join "`r`n"); Write-Host 'CLIPBOARD=copied' -ForegroundColor Yellow } catch {}

# ---------- 8. restore env ----------
$env:PATH = $__env0.PATH; $env:TEMP = $__env0.TEMP; $env:PYTHONUTF8 = $__env0.PYTHONUTF8; $env:VIA_CELERITAS_ROOT = $__env0.VIA_CELERITAS_ROOT
if ($null -eq $__env0.PYTHONPATH) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue } else { $env:PYTHONPATH = $__env0.PYTHONPATH }
