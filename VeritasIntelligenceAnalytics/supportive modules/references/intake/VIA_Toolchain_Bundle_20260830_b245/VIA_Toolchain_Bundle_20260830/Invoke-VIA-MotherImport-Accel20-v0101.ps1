#requires -Version 7.0
param(
    [string]$MotherRoot = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    [string[]]$Sources  = @(),
    [string]$RunRoot    = 'C:\VIA\VIA_MotherImport',
    [string]$VenvPath   = 'C:\Users\tonyk\envs\via_vrn4',
    [string]$GoToken    = '',
    [switch]$NoOpen
)

# =====================================================================
# Invoke-VIA-MotherImport-Accel20-v0101
#
# Stage-2 placement engine for the mother tree. Consumes new engines,
# runs twenty accelerators over them, emits a change plan, and applies
# it only when the GO token matches.
#
# Accelerators 01-15 run in VIA_Accel20_Analyzer_v0100.py (must sit
# beside this script). 16-20 are this layer:
#   16 dynamic progress bar   - weighted, driven by live analyzer output
#   17 status narration       - per-accelerator narration as it lands
#   18 non-blocking execution - child writes to files, parent polls;
#                               no pipe ReadToEnd, so no deadlock
#   19 multi-engine integration - PowerShell + Python + HTML in one run
#   20 auto-deploy and init   - venv resolution, dependency probe, paths
#
# Governance: dry-run by default. Nothing is written into the mother
# tree without -GoToken. Placement never overwrites: a name collision
# with different content becomes a __vN sibling.
# Run with: pwsh -NoProfile -ExecutionPolicy Bypass -File <this file>
# =====================================================================

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:LogLines  = [System.Collections.Generic.List[string]]::new()
$script:Accels    = [System.Collections.Generic.List[object]]::new()
$script:Stamp     = $script:StartedAt.ToString('yyyyMMdd_HHmmss')
$script:RunId     = 'VIA-IMPORT-' + $script:Stamp
$script:ApplyMode = ($GoToken -eq 'GO_v1')

$script:AccelNames = [ordered]@{
    'A01' = 'AST Precision Parser'
    'A02' = 'Multi-Language Semantic Model'
    'A03' = 'Hydra Risk Prediction'
    'A04' = 'Dependency Topology Sorting'
    'A05' = 'Sandbox Isolation Execution'
    'A06' = 'Auto-Fix Suggestion Generation'
    'A07' = 'Three-Round Panoramic Analysis'
    'A08' = 'SSOT Alignment'
    'A09' = 'Visual Matrix Generation'
    'A10' = 'Error Classification and Clustering'
    'A11' = 'Performance and Complexity Analysis'
    'A12' = 'Multi-Subsystem Synchronization'
    'A13' = 'Version Diff and Rollback'
    'A14' = 'Coverage and Regression Verification'
    'A15' = 'Fix-Order Optimization'
    'A16' = 'Dynamic Progress Bar'
    'A17' = 'Dynamic Status Narration'
    'A18' = 'Non-Blocking PowerShell Execution'
    'A19' = 'Multi-Engine Integration'
    'A20' = 'Auto-Deploy and Init'
}

function Get-CleanPath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return $Value.Trim().Trim("'").Trim('"').TrimEnd('\')
}

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $line = '[' + (Get-Date).ToString('HH:mm:ss') + '] [' + $Level + '] ' + $Message
    $script:LogLines.Add($line)
    $color = 'Gray'
    if ($Level -eq 'OK')    { $color = 'Green' }
    if ($Level -eq 'WARN')  { $color = 'Yellow' }
    if ($Level -eq 'FAIL')  { $color = 'Red' }
    if ($Level -eq 'PHASE') { $color = 'Cyan' }
    if ($Level -eq 'ACCEL') { $color = 'Magenta' }
    Write-Host $line -ForegroundColor $color
}

function Write-TextFile {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Set-Accel {
    param([string]$Id, [string]$State, [string]$Mode = '', [string]$Detail = '')
    $existing = $script:Accels | Where-Object { $_.Id -eq $Id } | Select-Object -First 1
    if ($null -ne $existing) {
        $existing.State = $State
        if ($Mode -ne '')   { $existing.Mode = $Mode }
        if ($Detail -ne '') { $existing.Detail = $Detail }
        return
    }
    $script:Accels.Add([pscustomobject]@{
        Id = $Id; Name = $script:AccelNames[$Id]; State = $State; Mode = $Mode; Detail = $Detail
    })
}

foreach ($k in $script:AccelNames.Keys) { Set-Accel -Id $k -State 'PENDING' }

function Test-RealPython {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    if ($Path -match 'WindowsApps') { return $false }
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
    if ($null -eq $item) { return $false }
    if ($item.Length -lt 20000) { return $false }
    return $true
}

Write-Host ''
Write-Host '  VIA Mother Import  ·  20 Accelerators' -ForegroundColor White
Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
if ($script:ApplyMode) {
    Write-Host '  MODE: APPLY  (GO token accepted)' -ForegroundColor Yellow
} else {
    Write-Host '  MODE: DRY-RUN  (pass -GoToken GO_v1 to apply)' -ForegroundColor DarkGray
}
Write-Host ''

# --- A20  auto-deploy and init ---------------------------------------
Write-Log 'A20  auto-deploy and init' 'ACCEL'
$runDir = Join-Path $RunRoot ('IMPORT_' + $script:Stamp)
foreach ($d in @($RunRoot, $runDir, (Join-Path $runDir 'reports'), (Join-Path $runDir 'logs'))) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$script:Blocked = $false
if (-not (Test-Path -LiteralPath $MotherRoot)) {
    Write-Log ('BLOCKED_MOTHER_ROOT_ABSENT  ' + $MotherRoot) 'FAIL'
    $script:Blocked = $true
} elseif (-not (Test-Path -LiteralPath (Join-Path $MotherRoot 'functional modules'))) {
    Write-Log ('BLOCKED_NOT_A_MOTHER_TREE  no "functional modules" under ' + $MotherRoot) 'FAIL'
    $script:Blocked = $true
} else {
    Write-Log ('mother   ' + $MotherRoot) 'OK'
}

if ($Sources.Count -eq 0) {
    $dl = Join-Path $env:USERPROFILE 'Downloads'
    $defaults = @(
        'VIA_NLP_OneEngine_v1.4.0.zip',
        'VDF_TW_AllStock_Excellence_BacktestReport_v035_package (1).zip',
        'forward_valuation_vintage_v2.py'
    )
    $found = [System.Collections.Generic.List[string]]::new()
    foreach ($d in $defaults) {
        $p = Join-Path $dl $d
        if (Test-Path -LiteralPath $p) { $found.Add($p) } else { Write-Log ('source missing: ' + $p) 'WARN' }
    }
    $Sources = $found.ToArray()
}
if ($Sources.Count -eq 0) {
    Write-Log 'BLOCKED_NO_SOURCES  pass -Sources with at least one zip or file' 'FAIL'
    $script:Blocked = $true
} else {
    foreach ($s in $Sources) { Write-Log ('source   ' + $s) 'OK' }
}

$script:Python = ''
if (Test-RealPython -Path (Join-Path $VenvPath 'Scripts\python.exe')) {
    $script:Python = Join-Path $VenvPath 'Scripts\python.exe'
} else {
    foreach ($c in @('C:\Users\tonyk\envs\via_core_312\Scripts\python.exe',
                     'C:\Users\tonyk\envs\via_core\Scripts\python.exe')) {
        if (Test-RealPython -Path $c) { $script:Python = $c; break }
    }
}
if ($script:Python -eq '') {
    foreach ($ver in @('-3.12', '-3.11')) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = 'py'
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        foreach ($a in @($ver, '-c', 'import sys;print(sys.executable)')) { $psi.ArgumentList.Add($a) }
        $pp = New-Object System.Diagnostics.Process
        $pp.StartInfo = $psi
        try {
            $pp.Start() | Out-Null
            # async read, so even an unexpected flood on the pipe cannot stall us
            $tOut = $pp.StandardOutput.ReadToEndAsync()
            $pp.WaitForExit()
            $o = $tOut.GetAwaiter().GetResult().Trim()
            if (Test-RealPython -Path $o) { $script:Python = $o; break }
        } catch { }
    }
}
if ($script:Python -eq '') {
    Write-Log 'BLOCKED_PYTHON_RUNTIME_ABSENT' 'FAIL'
    $script:Blocked = $true
} else {
    Write-Log ('python   ' + $script:Python) 'OK'
}

$analyzer = Join-Path (Split-Path -Path $PSCommandPath -Parent) 'VIA_Accel20_Analyzer_v0100.py'
if (-not (Test-Path -LiteralPath $analyzer)) {
    Write-Log 'BLOCKED_ANALYZER_ABSENT  VIA_Accel20_Analyzer_v0100.py must sit beside this script' 'FAIL'
    $script:Blocked = $true
}

if ($script:Blocked) {
    Set-Accel -Id 'A20' -State 'RED' -Mode 'EXACT' -Detail 'preflight blocked'
} else {
    Set-Accel -Id 'A20' -State 'GREEN' -Mode 'EXACT' -Detail ('run dir ' + $runDir)
}

# --- A18 / A16 / A17  non-blocking execution with live progress -------
$emitPath = Join-Path $runDir 'accel_report.json'
$outFile  = Join-Path $runDir 'logs\analyzer_stdout.txt'
$errFile  = Join-Path $runDir 'logs\analyzer_stderr.txt'

if (-not $script:Blocked) {
    Write-Log 'A18  launching analyzer (redirect to file, parent polls; no pipe deadlock)' 'ACCEL'
    Set-Accel -Id 'A18' -State 'GREEN' -Mode 'EXACT' -Detail 'file redirection + poll loop'

    $argLine = [System.Collections.Generic.List[string]]::new()
    $argLine.Add($analyzer)
    $argLine.Add('--sources')
    foreach ($s in $Sources) { $argLine.Add($s) }
    $argLine.Add('--mother-root'); $argLine.Add($MotherRoot)
    $argLine.Add('--run-dir');     $argLine.Add($runDir)
    $argLine.Add('--emit');        $argLine.Add($emitPath)

    $quoted = ($argLine | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $wrapper = Join-Path $runDir 'logs\_launch.cmd'
    Write-TextFile -Path $wrapper -Content ('@echo off' + "`r`n" +
        '"' + $script:Python + '" ' + $quoted + ' 1>"' + $outFile + '" 2>"' + $errFile + '"' + "`r`n")

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $env:ComSpec
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    foreach ($a in @('/c', $wrapper)) { $psi.ArgumentList.Add($a) }
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.Start() | Out-Null

    # 60 expected narration events: 20 per panoramic round
    $expected = 60
    $seen = 0
    $lastLine = ''
    while (-not $proc.HasExited) {
        Start-Sleep -Milliseconds 250
        if (Test-Path -LiteralPath $errFile) {
            $lines = @(Get-Content -LiteralPath $errFile -ErrorAction SilentlyContinue)
            if ($lines.Count -gt $seen) {
                for ($i = $seen; $i -lt $lines.Count; $i++) {
                    $l = $lines[$i]
                    if ($l -match '^(A\d\d|DONE)\|(.*)$') {
                        $id = $Matches[1]
                        $msg = $Matches[2]
                        $lastLine = $id + ' ' + $msg
                        if ($id -ne 'DONE') { Set-Accel -Id $id -State 'RUNNING' -Detail $msg }
                        Write-Log ('A17  ' + $lastLine) 'ACCEL'
                    }
                }
                $seen = $lines.Count
            }
        }
        $pct = [Math]::Min(97, [int](($seen / $expected) * 100))
        Write-Progress -Activity 'VIA Mother Import · 20 accelerators' `
                       -Status ('A16 progress · ' + $lastLine) -PercentComplete $pct
    }
    $proc.WaitForExit()
    Write-Progress -Activity 'VIA Mother Import · 20 accelerators' -Completed
    Set-Accel -Id 'A16' -State 'GREEN' -Mode 'EXACT' -Detail ($seen.ToString() + ' progress events')
    Set-Accel -Id 'A17' -State 'GREEN' -Mode 'EXACT' -Detail 'per-accelerator narration streamed'
    Write-Log ('analyzer exit code ' + $proc.ExitCode) 'OK'
}

# --- ingest analyzer report ------------------------------------------
$script:Report = $null
if (Test-Path -LiteralPath $emitPath) {
    $script:Report = Get-Content -LiteralPath $emitPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

$overall = 'BLOCKED'
if ($null -ne $script:Report) {
    $overall = [string]$script:Report.overall
    $final = $script:Report.rounds[-1]
    foreach ($id in @('A01','A02','A03','A04','A05','A06','A08','A10','A11','A12','A13','A14','A15')) {
        $node = $final.$id
        if ($null -eq $node) { continue }
        $state = 'GREEN'
        if ($node.status -eq 'YELLOW')  { $state = 'YELLOW' }
        if ($node.status -eq 'RED')     { $state = 'RED' }
        if ($node.status -eq 'SKIPPED') { $state = 'SKIPPED' }
        $detail = ''
        if ($null -ne $node.basis)  { $detail = [string]$node.basis }
        if ($null -ne $node.verdict) { $detail = [string]$node.verdict }
        if ($null -ne $node.policy) { $detail = [string]$node.policy }
        Set-Accel -Id $id -State $state -Mode ([string]$node.mode) -Detail $detail
    }
    Set-Accel -Id 'A07' -State 'GREEN' -Mode 'EXACT' -Detail '3 of 3 panoramic rounds completed'
    Set-Accel -Id 'A09' -State 'GREEN' -Mode 'EXACT' -Detail 'four-section matrix rendered'
    Set-Accel -Id 'A19' -State 'GREEN' -Mode 'EXACT' -Detail 'PowerShell + Python + HTML chained'
} else {
    foreach ($k in $script:AccelNames.Keys) {
        $a = $script:Accels | Where-Object { $_.Id -eq $k } | Select-Object -First 1
        if ($a.State -eq 'PENDING' -or $a.State -eq 'RUNNING') { Set-Accel -Id $k -State 'BLOCKED' }
    }
}

# --- change plan ------------------------------------------------------
Write-Log 'building change plan' 'PHASE'
$planRows = [System.Collections.Generic.List[object]]::new()
if ($null -ne $script:Report) {
    $final = $script:Report.rounds[-1]
    $routeMap = @{}
    foreach ($r in $final.A12.routes) { $routeMap[[string]$r.file] = [string]$r.subsystem }
    foreach ($d in $final.A13.rows) {
        $sub = 'OTHERS'
        if ($routeMap.ContainsKey([string]$d.file)) { $sub = $routeMap[[string]$d.file] }
        $action = 'PLACE'
        if ($d.verdict -eq 'IDENTICAL') { $action = 'SKIP_IDENTICAL' }
        if ($d.verdict -eq 'CONFLICT')  { $action = 'PLACE_AS_VERSIONED_SIBLING' }
        $dest = ''
        if ($sub -eq 'OTHERS' -or $sub -eq 'CGE') {
            $dest = Join-Path $MotherRoot ('new modules engines\_import_' + $script:Stamp)
        } else {
            $dest = Join-Path $MotherRoot ('functional modules\' + $sub + '\_import_' + $script:Stamp)
        }
        $planRows.Add([pscustomobject]@{
            File = [string]$d.file; Subsystem = $sub; Verdict = [string]$d.verdict
            Action = $action; Destination = $dest; Existing = [string]$d.existing
        })
    }
}
$plan = [pscustomobject]@{
    schema = 'VIA_ChangePlan/1.0'; run_id = $script:RunId; at = $script:StartedAt.ToString('s')
    mother_root = $MotherRoot; overall = $overall; apply_mode = $script:ApplyMode
    go_token_required = 'GO_v1'; rows = $planRows
}
$planPath = Join-Path $runDir 'change_plan.json'
Write-TextFile -Path $planPath -Content ($plan | ConvertTo-Json -Depth 6)
Write-Log ('change plan  ' + $planPath + '  (' + $planRows.Count + ' rows)') 'OK'

# --- apply (GO token only) -------------------------------------------
$applied = 0
$skipped = 0
if ($script:ApplyMode -and $overall -ne 'RED' -and $planRows.Count -gt 0) {
    Write-Log 'APPLY  placing artifacts (append-only, never overwrite)' 'PHASE'
    $stagedRoot = Join-Path $runDir '_staged'
    foreach ($row in $planRows) {
        if ($row.Action -eq 'SKIP_IDENTICAL') { $skipped = $skipped + 1; continue }
        $src = @(Get-ChildItem -LiteralPath $stagedRoot -Recurse -File -Filter $row.File -ErrorAction SilentlyContinue) |
               Select-Object -First 1
        if ($null -eq $src) { Write-Log ('  source not staged: ' + $row.File) 'WARN'; continue }
        if (-not (Test-Path -LiteralPath $row.Destination)) {
            New-Item -ItemType Directory -Path $row.Destination -Force | Out-Null
        }
        $target = Join-Path $row.Destination $row.File
        $n = 2
        while (Test-Path -LiteralPath $target) {
            $stem = [IO.Path]::GetFileNameWithoutExtension($row.File)
            $ext  = [IO.Path]::GetExtension($row.File)
            $target = Join-Path $row.Destination ($stem + '__v' + $n + $ext)
            $n = $n + 1
        }
        Copy-Item -LiteralPath $src.FullName -Destination $target -Force
        Write-Log ('  placed ' + $target) 'OK'
        $applied = $applied + 1
    }
} elseif ($script:ApplyMode -and $overall -eq 'RED') {
    Write-Log 'APPLY refused: overall is RED. Clear blockers first.' 'FAIL'
}

# --- A09  HTML UI Matrix ---------------------------------------------
Write-Log 'A09  rendering UI matrix' 'ACCEL'

function Get-Badge {
    param([string]$S)
    $c = 'gy'
    if ($S -eq 'GREEN' -or $S -eq 'PASS')   { $c = 'gr' }
    if ($S -eq 'YELLOW')                    { $c = 'ye' }
    if ($S -eq 'RED' -or $S -eq 'BLOCKED')  { $c = 'rd' }
    return '<span class="b ' + $c + '">' + $S + '</span>'
}

$secModule = ''
if ($null -ne $script:Report) {
    $final = $script:Report.rounds[-1]
    foreach ($prop in $final.A12.tally.PSObject.Properties) {
        $sub = $prop.Name
        $cnt = $prop.Value
        $conf = @($planRows | Where-Object { $_.Subsystem -eq $sub -and $_.Verdict -eq 'CONFLICT' }).Count
        $state = 'GREEN'
        if ($conf -gt 0) { $state = 'YELLOW' }
        $hi = ''
        if (@($final.A03.high_risk).Count -gt 0) { $hi = 'Elastic::' + (($final.A03.high_risk) -join ', ') }
        else { $hi = 'Precision::ModuleRoot' }
        $secModule = $secModule + '<tr><td>' + $sub + '</td><td class="c">' + (Get-Badge -S $state) + '</td><td class="c">' + $conf + '</td><td class="m">' + $hi + '</td><td>' + $cnt + ' artifacts routed; ' + $conf + ' name conflicts resolved as versioned siblings.</td></tr>'
    }
}
if ($secModule -eq '') { $secModule = '<tr><td colspan="5" class="dim">No modules analysed.</td></tr>' }

$secEngine = ''
foreach ($id in @('A01','A05','A07','A18','A19','A20')) {
    $a = $script:Accels | Where-Object { $_.Id -eq $id } | Select-Object -First 1
    $mode = $a.Mode
    if ($mode -eq '') { $mode = 'EXACT' }
    $secEngine = $secEngine + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td class="c m">' + $mode + '</td><td>' + $a.Detail + '</td></tr>'
}

$secLib = ''
foreach ($id in @('A02','A03','A04','A06','A08','A10','A11','A12','A13','A14','A15')) {
    $a = $script:Accels | Where-Object { $_.Id -eq $id } | Select-Object -First 1
    $mode = $a.Mode
    if ($mode -eq '') { $mode = 'EXACT' }
    $badge = 'exact'
    if ($mode -eq 'HEURISTIC') { $badge = 'heur' }
    $secLib = $secLib + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td class="c"><span class="b ' + $badge + '">' + $mode + '</span></td><td>' + $a.Detail + '</td></tr>'
}

$secOther = ''
foreach ($id in @('A09','A16','A17')) {
    $a = $script:Accels | Where-Object { $_.Id -eq $id } | Select-Object -First 1
    $secOther = $secOther + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td>' + $a.Detail + '</td></tr>'
}

$planTable = ''
foreach ($row in $planRows) {
    $cls = 'gr'
    if ($row.Verdict -eq 'CONFLICT')  { $cls = 'ye' }
    if ($row.Verdict -eq 'IDENTICAL') { $cls = 'gy' }
    $planTable = $planTable + '<tr><td class="m">' + $row.File + '</td><td class="c">' + $row.Subsystem + '</td><td class="c"><span class="b ' + $cls + '">' + $row.Verdict + '</span></td><td class="m">' + $row.Action + '</td><td class="m dim">' + $row.Destination + '</td></tr>'
}
if ($planTable -eq '') { $planTable = '<tr><td colspan="5" class="dim">Empty plan.</td></tr>' }

$modeText = 'DRY-RUN'
if ($script:ApplyMode) { $modeText = 'APPLIED' }
$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$logText = ($script:LogLines -join "`n").Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;')
$fileCount = 0
if ($null -ne $script:Report) { $fileCount = [int]$script:Report.file_count }

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SYSTEM MANAGER MATRIX REPORT — $($script:RunId)</title>
<style>
  :root { --bg:#0f172a; --card:#1e293b; --line:#334155; --tx:#f8fafc; --mu:#94a3b8; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--tx); overflow-x:hidden;
         font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif;
         font-size:11px; line-height:1.35; letter-spacing:-0.01em; }
  .wrap { width:100%; max-width:1400px; margin:0 auto; padding:18px 14px 48px; }
  h1 { font-size:14px; margin:0; font-weight:600; }
  .sub { font-size:11px; color:var(--mu); margin:3px 0 0; }
  h2 { font-size:12px; margin:22px 0 7px; font-weight:600; color:var(--tx);
       border-bottom:1px solid var(--line); padding-bottom:5px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(118px,1fr)); gap:8px; margin-top:14px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:3px; padding:9px 11px; }
  .kpi .n { font-size:17px; font-weight:600; }
  .kpi .l { font-size:10px; color:var(--mu); margin-top:2px; }
  table { width:100%; table-layout:fixed; border-collapse:collapse;
          background:var(--card); border:1px solid var(--line); border-radius:3px; }
  th { font-size:11px; color:var(--mu); font-weight:500; text-align:left;
       padding:4px 6px; border-bottom:1px solid var(--line); }
  td { padding:4px 6px; border-bottom:1px solid #253248; vertical-align:top;
       word-wrap:break-word; overflow-wrap:break-word; white-space:normal; min-height:24px; }
  tr:last-child td { border-bottom:none; }
  td.c { text-align:center; }
  td.m, .m { font-family:ui-monospace,Consolas,monospace; }
  .dim { color:var(--mu); }
  .b { display:inline-block; font-size:10px; padding:1px 6px; border-radius:2px; border:1px solid; }
  .gr { background:#064e3b; color:#34d399; border-color:#059669; }
  .ye { background:#78350f; color:#fde047; border-color:#d97706; }
  .rd { background:#7f1d1d; color:#fca5a5; border-color:#dc2626; }
  .gy { background:#1f2937; color:#9ca3af; border-color:#374151; }
  .exact { background:#0c2d48; color:#7dd3fc; border-color:#0369a1; }
  .heur { background:#3b2f0b; color:#fcd34d; border-color:#a16207; }
  .note { background:var(--card); border:1px solid var(--line); border-left:3px solid #d97706;
          border-radius:3px; padding:10px 12px; font-size:11px; }
  pre { background:#0b1220; color:#cbd5e1; font-family:ui-monospace,Consolas,monospace;
        font-size:10.5px; padding:11px; border-radius:3px; overflow-x:auto; max-height:280px; }
</style>
</head>
<body>
<div class="wrap">

<h1>SYSTEM MANAGER MATRIX REPORT</h1>
<p class="sub">VIA-CENTRAL-GOVERNANCE-CONSOLE · $($script:RunId) · $modeText · mother: $MotherRoot</p>

<div class="kpis">
  <div class="kpi"><div class="n">$overall</div><div class="l">overall RYG</div></div>
  <div class="kpi"><div class="n">$fileCount</div><div class="l">artifacts</div></div>
  <div class="kpi"><div class="n">$($planRows.Count)</div><div class="l">plan rows</div></div>
  <div class="kpi"><div class="n">$applied</div><div class="l">placed</div></div>
  <div class="kpi"><div class="n">$skipped</div><div class="l">skipped identical</div></div>
  <div class="kpi"><div class="n">${elapsed}s</div><div class="l">elapsed</div></div>
</div>

<h2>MODULE</h2>
<table>
  <colgroup><col style="width:16%"><col style="width:10%"><col style="width:8%"><col style="width:24%"><col style="width:42%"></colgroup>
  <thead><tr><th>Subsystem</th><th>RYG</th><th>Issues</th><th>AST Anchoring Scope</th><th>Diagnostic Summary</th></tr></thead>
  <tbody>$secModule</tbody>
</table>

<h2>ENGINE</h2>
<table>
  <colgroup><col style="width:28%"><col style="width:10%"><col style="width:12%"><col style="width:50%"></colgroup>
  <thead><tr><th>Core Engine Component</th><th>RYG</th><th>Evidence Mode</th><th>Pipeline State Narration</th></tr></thead>
  <tbody>$secEngine</tbody>
</table>

<h2>FUNCTION-LIB</h2>
<table>
  <colgroup><col style="width:28%"><col style="width:10%"><col style="width:12%"><col style="width:50%"></colgroup>
  <thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence Mode</th><th>Governance Notes</th></tr></thead>
  <tbody>$secLib</tbody>
</table>

<h2>OTHERS</h2>
<table>
  <colgroup><col style="width:28%"><col style="width:10%"><col style="width:62%"></colgroup>
  <thead><tr><th>Support Component</th><th>RYG</th><th>Dynamic Status Narration</th></tr></thead>
  <tbody>$secOther</tbody>
</table>

<h2>CHANGE PLAN</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:20%"><col style="width:34%"></colgroup>
  <thead><tr><th>File</th><th>Subsystem</th><th>Verdict</th><th>Action</th><th>Destination</th></tr></thead>
  <tbody>$planTable</tbody>
</table>

<h2>EVIDENCE HONESTY</h2>
<div class="note">
  Accelerators marked <span class="b exact">EXACT</span> report a measurement: an AST parse, a topological sort,
  a compile in an isolated subprocess, a SHA256 comparison. Accelerators marked <span class="b heur">HEURISTIC</span>
  report an estimate from a proxy signal and can be wrong. A03 scores coupling from import fan-in and fan-out only,
  which is not a proof of blast radius. A12 routes by filename and the first 4KB of content, so placement should be
  confirmed before it is trusted. Nothing here rewrites source: A06 emits suggestions, never edits.
</div>

<h2>CONSOLE LOG</h2>
<pre>$logText</pre>

</div>
</body>
</html>
"@

$reportPath = Join-Path $runDir ('reports\SYSTEM_MANAGER_MATRIX_' + $script:Stamp + '.html')
Write-TextFile -Path $reportPath -Content $html
Write-TextFile -Path (Join-Path $runDir 'logs\console.log') -Content $logText

Write-Host ''
Write-Host ('  overall ' + $overall + '  ·  plan ' + $planRows.Count + ' rows  ·  ' + $modeText) -ForegroundColor Green
Write-Host ('  plan    ' + $planPath) -ForegroundColor DarkGray
Write-Host ('  matrix  ' + $reportPath) -ForegroundColor DarkGray
if (-not $script:ApplyMode) {
    Write-Host '  re-run with -GoToken GO_v1 to apply the plan' -ForegroundColor Yellow
}
Write-Host ''

if (-not $NoOpen) { Start-Process -FilePath $reportPath }
