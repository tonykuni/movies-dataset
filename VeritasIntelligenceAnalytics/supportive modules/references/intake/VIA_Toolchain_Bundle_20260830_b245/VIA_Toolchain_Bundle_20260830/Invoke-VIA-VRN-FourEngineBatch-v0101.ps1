#requires -Version 7.0
param(
    [string]$InputDir    = '',
    [string]$SuiteDir    = '',
    [string]$Baseline    = '',
    [string]$EngineRoot  = 'C:\VIA\VRN_FourEngineBatch',
    [string]$VenvPath    = 'C:\Users\tonyk\envs\via_vrn4',
    [int]$Workers        = 4,
    [int]$Dpi            = 300,
    [int]$Limit          = 0,
    [switch]$SkipInstall,
    [switch]$NoOpen
)

# =====================================================================
# VIA VRN Four-Engine Batch Driver  v0100
#
# VRNFourEngineSuite runs one file per invocation and rejects .docx.
# A broker-attachment folder is 60 pdf + 4 docx. This closes both gaps:
#   - markitdown bridges docx/pptx/xlsx into a corpus-marked .md
#   - every document gets its own four-engine run, then aggregated
#   - fresh PDF-derived figures are reconciled against the prior
#     text-corpus extraction so disagreements surface instead of hiding
#
# Governance: append-only. Each invocation writes BATCH_<timestamp>.
# Run with: pwsh -NoProfile -ExecutionPolicy Bypass -File <this file> ...
# =====================================================================

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:LogLines  = [System.Collections.Generic.List[string]]::new()
$script:Phases    = [System.Collections.Generic.List[object]]::new()
$script:RunId     = 'VIA-VRN4B-' + $script:StartedAt.ToString('yyyyMMdd') + '-' + ('{0:D6}' -f (Get-Random -Minimum 1 -Maximum 999999))

$script:Dirs = [ordered]@{
    root    = $EngineRoot
    engine  = Join-Path $EngineRoot 'engine'
    suite   = Join-Path $EngineRoot 'suite'
    runs    = Join-Path $EngineRoot 'runs'
    logs    = Join-Path $EngineRoot 'logs'
    reports = Join-Path $EngineRoot 'reports'
    data    = Join-Path $EngineRoot 'data'
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
    Write-Host $line -ForegroundColor $color
}

function Save-PhaseLog {
    param([string]$Name, [string]$State, [string]$Detail = '')
    $script:Phases.Add([pscustomobject]@{
        Name = $Name; State = $State; Detail = $Detail; At = (Get-Date).ToString('HH:mm:ss')
    })
}

function Write-TextFile {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Invoke-VIAProcess {
    param([string]$FilePath, [string[]]$ArgumentList, [switch]$Capture, [string]$WorkDir = '')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    if ($WorkDir -ne '') { $psi.WorkingDirectory = $WorkDir }
    foreach ($a in $ArgumentList) { $psi.ArgumentList.Add($a) }
    if ($Capture) {
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
        $psi.StandardErrorEncoding  = [System.Text.Encoding]::UTF8
    }
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $out = ''
    $err = ''
    try {
        $proc.Start() | Out-Null
        if ($Capture) {
            $tOut = $proc.StandardOutput.ReadToEndAsync()
            $tErr = $proc.StandardError.ReadToEndAsync()
            $proc.WaitForExit()
            $out = $tOut.GetAwaiter().GetResult()
            $err = $tErr.GetAwaiter().GetResult()
        } else {
            $proc.WaitForExit()
        }
        return [pscustomobject]@{ Code = $proc.ExitCode; Out = $out; Err = $err }
    } catch {
        return [pscustomobject]@{ Code = -1; Out = ''; Err = $_.Exception.Message }
    }
}

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
Write-Host '  VRN Four-Engine Batch Driver' -ForegroundColor White
Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
Write-Host '  repair / layout / text / table  ·  docx bridge  ·  baseline reconciliation' -ForegroundColor DarkGray
Write-Host ''

# --- Phase 1  paths ---------------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 1/7  paths' -PercentComplete 6
Write-Log 'Phase 1  paths' 'PHASE'
foreach ($k in $script:Dirs.Keys) {
    $p = $script:Dirs[$k]
    if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null; Write-Log ('created ' + $p) 'OK' }
    else { Write-Log ('reuse   ' + $p) }
}
Save-PhaseLog -Name 'Paths' -State 'OK' -Detail $EngineRoot

# --- Phase 2  inputs --------------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 2/7  input gate' -PercentComplete 14
Write-Log 'Phase 2  input gate' 'PHASE'

$script:Blocked = $false
if ($InputDir -eq '' -or -not (Test-Path -LiteralPath $InputDir)) {
    Write-Log 'BLOCKED_INPUT_DIR_ABSENT  pass -InputDir pointing at the folder holding the ORIGINAL pdf/docx attachments' 'FAIL'
    $script:Blocked = $true
}
if ($SuiteDir -eq '' -or -not (Test-Path -LiteralPath (Join-Path $SuiteDir 'four_engine_orchestrator.py'))) {
    Write-Log 'BLOCKED_SUITE_ABSENT  pass -SuiteDir pointing at the unpacked VRNFourEngineSuite folder' 'FAIL'
    $script:Blocked = $true
}
if ($Baseline -ne '' -and -not (Test-Path -LiteralPath (Join-Path $Baseline '01_repair\financial_data.jsonl'))) {
    Write-Log 'baseline path has no 01_repair\financial_data.jsonl; reconciliation will be skipped' 'WARN'
    $Baseline = ''
}
if (-not $script:Blocked) {
    $srcCount = @(Get-ChildItem -LiteralPath $InputDir -Recurse -File -ErrorAction SilentlyContinue).Count
    Write-Log ('input    ' + $InputDir + '  (' + $srcCount + ' files)') 'OK'
    Write-Log ('suite    ' + $SuiteDir) 'OK'
    if ($Baseline -ne '') { Write-Log ('baseline ' + $Baseline) 'OK' } else { Write-Log 'baseline none  (no reconciliation)' 'WARN' }
}
if ($script:Blocked) { Save-PhaseLog -Name 'Input gate' -State 'BLOCKED' -Detail 'missing -InputDir or -SuiteDir' }
else { Save-PhaseLog -Name 'Input gate' -State 'OK' -Detail $InputDir }

# --- Phase 3  python --------------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 3/7  python' -PercentComplete 24
Write-Log 'Phase 3  python runtime' 'PHASE'

$script:BasePython = ''
foreach ($c in @(
    'C:\Users\tonyk\envs\via_core_312\Scripts\python.exe',
    'C:\Users\tonyk\envs\via_core\Scripts\python.exe',
    'C:\Python312\python.exe',
    'C:\Program Files\Python312\python.exe')) {
    if (Test-RealPython -Path $c) { $script:BasePython = $c; break }
}
if ($script:BasePython -eq '') {
    foreach ($ver in @('-3.12', '-3.11', '-3.13')) {
        $probe = Invoke-VIAProcess -FilePath 'py' -ArgumentList @($ver, '-c', 'import sys;print(sys.executable)') -Capture
        if ($probe.Code -eq 0 -and (Test-RealPython -Path $probe.Out.Trim())) { $script:BasePython = $probe.Out.Trim(); break }
    }
}
if ($script:BasePython -eq '') {
    Write-Log 'BLOCKED_PYTHON_RUNTIME_ABSENT  Store aliases rejected; winget install Python.Python.3.12' 'FAIL'
    $script:Blocked = $true
} else {
    Write-Log ('runtime  ' + $script:BasePython) 'OK'
}

$script:VenvPython = Join-Path $VenvPath 'Scripts\python.exe'
$script:VenvReady = $false
if (-not $script:Blocked) {
    if (Test-Path -LiteralPath $script:VenvPython) { Write-Log ('reuse venv  ' + $VenvPath) 'OK'; $script:VenvReady = $true }
    else {
        Write-Log ('create venv ' + $VenvPath)
        $r = Invoke-VIAProcess -FilePath $script:BasePython -ArgumentList @('-m', 'venv', $VenvPath)
        if ($r.Code -eq 0 -and (Test-Path -LiteralPath $script:VenvPython)) { Write-Log 'venv created' 'OK'; $script:VenvReady = $true }
        else { Write-Log ('venv failed: ' + $r.Err) 'FAIL' }
    }
}
if ($script:VenvReady) { Save-PhaseLog -Name 'Python' -State 'OK' -Detail $VenvPath } else { Save-PhaseLog -Name 'Python' -State 'BLOCKED' -Detail '' }

# --- Phase 4  dependencies -------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 4/7  dependencies' -PercentComplete 38
Write-Log 'Phase 4  dependencies' 'PHASE'

$constraints = Join-Path $script:Dirs.engine 'constraints.txt'
Write-TextFile -Path $constraints -Content @'
numpy>=1.24,<2.0
'@

$script:InstallState = 'SKIPPED'
if ($script:VenvReady -and -not $SkipInstall) {
    Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel', '--disable-pip-version-check') | Out-Null
    $pkgs = @('pymupdf', 'pdfplumber', 'markitdown[docx,pptx,xlsx,pdf]', 'pandas', 'pyarrow')
    $allOk = $true
    foreach ($pk in $pkgs) {
        Write-Log ('installing ' + $pk)
        $ri = Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', $pk, '-c', $constraints, '--disable-pip-version-check')
        if ($ri.Code -eq 0) { Write-Log ('  OK   ' + $pk) 'OK' } else { Write-Log ('  FAIL ' + $pk) 'WARN'; $allOk = $false }
    }
    if ($allOk) { $script:InstallState = 'OK' } else { $script:InstallState = 'PARTIAL' }
}
Save-PhaseLog -Name 'Dependencies' -State $script:InstallState -Detail 'pymupdf pdfplumber markitdown pandas pyarrow'

# --- Phase 5  deploy driver ------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 5/7  deploy driver' -PercentComplete 52
Write-Log 'Phase 5  deploy batch driver' 'PHASE'

$driverPath = Join-Path $script:Dirs.engine 'VRN_BatchFourEngine_v0100.py'
$driverSource = Join-Path (Split-Path -Path $PSCommandPath -Parent) 'VRN_BatchFourEngine_v0100.py'
if (Test-Path -LiteralPath $driverSource) {
    Copy-Item -LiteralPath $driverSource -Destination $driverPath -Force
    Write-Log ('driver   ' + $driverPath) 'OK'
    Save-PhaseLog -Name 'Deploy driver' -State 'OK' -Detail $driverPath
} else {
    Write-Log ('BLOCKED_DRIVER_ABSENT  VRN_BatchFourEngine_v0100.py must sit beside this script') 'FAIL'
    $script:Blocked = $true
    Save-PhaseLog -Name 'Deploy driver' -State 'BLOCKED' -Detail $driverSource
}

# --- Phase 6  batch run ----------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 6/7  batch run' -PercentComplete 66
Write-Log 'Phase 6  batch run' 'PHASE'

$emitPath = Join-Path $script:Dirs.data 'vrn4b_last_run.json'
$script:Payload = $null

if ($script:VenvReady -and -not $script:Blocked) {
    $runArgs = @(
        $driverPath,
        '--input-dir', $InputDir,
        '--output-root', $script:Dirs.runs,
        '--suite-dir', $SuiteDir,
        '--workers', $Workers.ToString(),
        '--dpi', $Dpi.ToString(),
        '--emit', $emitPath
    )
    if ($Baseline -ne '') { $runArgs += @('--baseline', $Baseline) }
    if ($Limit -gt 0)     { $runArgs += @('--limit', $Limit.ToString()) }
    Write-Log 'running four engines per document (live progress below)'
    Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList $runArgs | Out-Null
    if (Test-Path -LiteralPath $emitPath) {
        $script:Payload = Get-Content -LiteralPath $emitPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
}

$docTotal = 0
$docPass = 0
$docWarn = 0
$docFail = 0
if ($null -ne $script:Payload -and $null -ne $script:Payload.documents) {
    foreach ($d in $script:Payload.documents) {
        $docTotal = $docTotal + 1
        if ($d.status -eq 'PASS') { $docPass = $docPass + 1 }
        elseif ($d.status -eq 'WARN') { $docWarn = $docWarn + 1 }
        else { $docFail = $docFail + 1 }
    }
}
Write-Log ('documents ' + $docPass + ' PASS / ' + $docWarn + ' WARN / ' + $docFail + ' FAIL') 'PHASE'
Save-PhaseLog -Name 'Batch run' -State ($docPass.ToString() + '/' + $docTotal.ToString() + ' PASS') -Detail ''

# --- Phase 7  console -------------------------------------------------
Write-Progress -Activity 'VRN4B' -Status 'Phase 7/7  console' -PercentComplete 88
Write-Log 'Phase 7  HTML console' 'PHASE'

function Get-Cls {
    param([string]$State)
    if ($State -eq 'PASS') { return 'good' }
    if ($State -eq 'WARN' -or $State -eq 'SKIPPED' -or $State -eq 'NEEDS_OCR') { return 'warn' }
    return 'bad'
}

$stageRows = ''
if ($null -ne $script:Payload -and $null -ne $script:Payload.stage_tally) {
    foreach ($prop in $script:Payload.stage_tally.PSObject.Properties) {
        $cells = ''
        foreach ($sp in $prop.Value.PSObject.Properties) {
            $cells = $cells + '<span class="pill ' + (Get-Cls -State $sp.Name) + '">' + $sp.Name + ' ' + $sp.Value + '</span> '
        }
        $stageRows = $stageRows + '<tr><td class="mono">' + $prop.Name + '</td><td>' + $cells + '</td></tr>'
    }
}

$docRows = ''
if ($null -ne $script:Payload -and $null -ne $script:Payload.documents) {
    foreach ($d in $script:Payload.documents) {
        $name = ''
        if ($d.original -ne '') { $name = Split-Path -Path ([string]$d.original) -Leaf }
        $st = ''
        foreach ($sn in @('repair', 'layout', 'text', 'table')) {
            $sv = 'MISSING'
            if ($null -ne $d.stages.$sn) { $sv = [string]$d.stages.$sn.status }
            $st = $st + '<span class="pill ' + (Get-Cls -State $sv) + '">' + $sn.Substring(0,1).ToUpper() + '</span>'
        }
        $warnText = ''
        if (@($d.warnings).Count -gt 0) { $warnText = ($d.warnings -join ' · ') }
        if ($d.error -ne '') { $warnText = [string]$d.error }
        $docRows = $docRows + '<tr><td class="mono dim">' + $d.index + '</td><td class="mono">' + $name + '</td><td class="mono dim">' + $d.route + '</td><td><span class="pill ' + (Get-Cls -State ([string]$d.status)) + '">' + $d.status + '</span></td><td>' + $st + '</td><td class="mono dim">' + $warnText + '</td></tr>'
    }
}
if ($docRows -eq '') { $docRows = '<tr><td colspan="6" class="dim">No documents processed.</td></tr>' }

$reconBlock = '<div class="note">Reconciliation not run. Pass <span class="mono">-Baseline</span> pointing at the AttachmentFixedOutput root to diff the fresh PDF-derived figures against the earlier text-corpus extraction.</div>'
if ($null -ne $script:Payload -and $script:Payload.reconciliation.enabled) {
    $t = $script:Payload.reconciliation.tally
    $mismRows = ''
    foreach ($m in $script:Payload.reconciliation.sample) {
        $mismRows = $mismRows + '<tr><td class="mono">' + $m.filename + '</td><td class="mono">' + $m.metric + '</td><td class="mono dim">' + $m.period + '</td><td class="mono">' + $m.baseline_values + '</td><td class="mono">' + $m.new_values + '</td></tr>'
    }
    if ($mismRows -eq '') { $mismRows = '<tr><td colspan="5" class="dim">No value disagreements.</td></tr>' }
    $reconBlock = '<div class="kpis" style="margin-bottom:14px">' +
        '<div class="kpi"><div class="n">' + $t.MATCH + '</div><div class="l">match</div></div>' +
        '<div class="kpi"><div class="n">' + $t.MISMATCH + '</div><div class="l">mismatch</div></div>' +
        '<div class="kpi"><div class="n">' + $t.BASELINE_ONLY + '</div><div class="l">baseline only</div></div>' +
        '<div class="kpi"><div class="n">' + $t.NEW_ONLY + '</div><div class="l">new only</div></div>' +
        '</div><table><thead><tr><th>File</th><th>Metric</th><th>Period</th><th>Baseline</th><th>New</th></tr></thead><tbody>' + $mismRows + '</tbody></table>'
}

$phaseRows = ''
foreach ($p in $script:Phases) {
    $phaseRows = $phaseRows + '<tr><td class="mono">' + $p.At + '</td><td>' + $p.Name + '</td><td class="mono">' + $p.State + '</td><td class="mono dim">' + $p.Detail + '</td></tr>'
}

$disc = '0 / 0 / 0'
$bridgeState = 'n/a'
if ($null -ne $script:Payload) {
    $disc = [string]$script:Payload.discovery.native_doc + ' / ' + [string]$script:Payload.discovery.bridged + ' / ' + [string]$script:Payload.discovery.skipped
    if ($script:Payload.bridge.available) { $bridgeState = 'ACTIVE' } else { $bridgeState = 'DORMANT' }
}
$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$logText = ($script:LogLines -join "`n").Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;')
$stampText = $script:StartedAt.ToString('yyyy-MM-dd HH:mm:ss')

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VRN Four-Engine Batch — $($script:RunId)</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;800&family=DM+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root { --bg:#f5f4f0; --paper:#fff; --ink:#1e1d1a; --line:#dbd9d3; --teal:#439a9a; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font-family:"DM Sans",-apple-system,"Segoe UI","Microsoft JhengHei",sans-serif; font-size:14px; line-height:1.6; }
  .wrap { max-width:1220px; margin:0 auto; padding:32px 20px 64px; }
  header { display:flex; gap:16px; align-items:center; }
  .seal { width:44px; height:44px; border-radius:3px; background:#c96b5a; color:#fff;
          display:flex; align-items:center; justify-content:center; font-family:"Syne",serif; font-size:22px; font-weight:800; }
  h1 { font-family:"Syne",sans-serif; font-weight:800; font-size:22px; margin:0; letter-spacing:-0.01em; }
  .sub { font-family:"DM Mono",monospace; font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:#8a877f; margin:2px 0 0; }
  .sub2 { font-family:"DM Mono",monospace; font-size:11px; color:#8a877f; margin:2px 0 0; }
  .strip { height:3px; margin:20px 0 28px; border-radius:2px;
           background:linear-gradient(90deg,#4c78a8,#439a9a,#5a9e6f,#c9a95a,#c96b5a,#a86b9a,#6b7ea8); }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; }
  .kpi { background:var(--paper); border:1px solid var(--line); border-radius:3px; padding:14px 16px; }
  .kpi .n { font-family:"Syne",sans-serif; font-size:24px; font-weight:800; line-height:1.1; }
  .kpi .l { font-family:"DM Mono",monospace; font-size:10px; letter-spacing:0.08em; text-transform:uppercase; color:#8a877f; margin-top:4px; }
  section { margin-top:32px; }
  h2 { font-family:"Syne",sans-serif; font-size:13px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase;
       color:#6d6a63; margin:0 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line); }
  table { width:100%; border-collapse:collapse; background:var(--paper); border:1px solid var(--line); border-radius:3px; overflow:hidden; }
  th { text-align:left; font-family:"DM Mono",monospace; font-size:10px; letter-spacing:0.08em; text-transform:uppercase;
       color:#8a877f; padding:9px 12px; border-bottom:1px solid var(--line); font-weight:500; }
  td { padding:7px 12px; border-bottom:1px solid #eeece7; vertical-align:top; }
  tr:last-child td { border-bottom:none; }
  .mono { font-family:"DM Mono",monospace; font-size:12px; }
  .dim { color:#8a877f; }
  .pill { display:inline-block; font-family:"DM Mono",monospace; font-size:10px; letter-spacing:0.04em;
          padding:2px 7px; border-radius:2px; margin-right:3px; }
  .good { background:rgba(90,158,111,.14); color:#41764f; }
  .warn { background:rgba(201,169,90,.2); color:#8a6c1f; }
  .bad { background:rgba(201,107,90,.16); color:#a1503f; }
  .note { background:var(--paper); border:1px solid var(--line); border-left:3px solid var(--teal);
          border-radius:3px; padding:14px 16px; }
  pre { background:#1e1d1a; color:#d9d6cf; font-family:"DM Mono",monospace; font-size:11.5px;
        padding:16px; border-radius:3px; overflow-x:auto; max-height:320px; line-height:1.55; }
  footer { margin-top:40px; font-family:"DM Mono",monospace; font-size:11px; color:#8a877f;
           border-top:1px solid var(--line); padding-top:14px; }
  @media (max-width:640px) { .wrap { padding:20px 14px 48px; } h1 { font-size:18px; } }
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="seal">牘</div>
  <div>
    <h1>VRN Four-Engine Batch</h1>
    <p class="sub">Veritas Intelligence System</p>
    <p class="sub2">repair · layout · text · table  ·  markitdown docx bridge  ·  baseline reconciliation</p>
  </div>
</header>

<div class="strip"></div>

<div class="kpis">
  <div class="kpi"><div class="n">$docTotal</div><div class="l">documents</div></div>
  <div class="kpi"><div class="n">$docPass</div><div class="l">pass</div></div>
  <div class="kpi"><div class="n">$docWarn</div><div class="l">warn</div></div>
  <div class="kpi"><div class="n">$docFail</div><div class="l">fail</div></div>
  <div class="kpi"><div class="n">$disc</div><div class="l">native / bridged / skipped</div></div>
  <div class="kpi"><div class="n">$bridgeState</div><div class="l">markitdown bridge</div></div>
  <div class="kpi"><div class="n">${elapsed}s</div><div class="l">elapsed</div></div>
</div>

<section>
  <h2>Stage tally</h2>
  <table><thead><tr><th style="width:120px">Stage</th><th>Outcomes</th></tr></thead><tbody>$stageRows</tbody></table>
</section>

<section>
  <h2>Financial reconciliation — fresh extraction vs prior text corpus</h2>
  $reconBlock
</section>

<section>
  <h2>Per-document results</h2>
  <table>
    <thead><tr><th style="width:40px">#</th><th>Document</th><th style="width:150px">Route</th><th style="width:80px">Overall</th><th style="width:120px">R / L / T / Tb</th><th>Warnings</th></tr></thead>
    <tbody>$docRows</tbody>
  </table>
</section>

<section>
  <h2>Run phases</h2>
  <table><thead><tr><th>Time</th><th>Phase</th><th>State</th><th>Detail</th></tr></thead><tbody>$phaseRows</tbody></table>
</section>

<section>
  <h2>Console log</h2>
  <pre>$logText</pre>
</section>

<footer>
  $($script:RunId) · started $stampText · input $InputDir · runs $($script:Dirs.runs)<br>
  Append-only: every invocation writes a fresh BATCH_&lt;timestamp&gt; directory. Figures marked as extracted remain unverified until reconciled against the issuing source.
</footer>

</div>
</body>
</html>
"@

$reportPath = Join-Path $script:Dirs.reports ('VRN4B_Console_' + $script:StartedAt.ToString('yyyyMMdd_HHmmss') + '.html')
Write-TextFile -Path $reportPath -Content $html
$latestPath = Join-Path $script:Dirs.reports 'VRN4B_Console.html'
Write-TextFile -Path $latestPath -Content $html
Write-TextFile -Path (Join-Path $script:Dirs.logs ('vrn4b_' + $script:StartedAt.ToString('yyyyMMdd_HHmmss') + '.log')) -Content $logText

$regLine = (@{
    run_id = $script:RunId; at = $script:StartedAt.ToString('s'); input = $InputDir
    documents = $docTotal; pass = $docPass; warn = $docWarn; fail = $docFail; report = $reportPath
} | ConvertTo-Json -Compress)
[System.IO.File]::AppendAllText((Join-Path $script:Dirs.data 'VRN4B_run_registry.jsonl'), $regLine + "`n", $script:Utf8NoBom)

Write-Progress -Activity 'VRN4B' -Completed
Write-Host ''
Write-Host ('  batch done  ·  ' + $docPass + ' PASS / ' + $docWarn + ' WARN / ' + $docFail + ' FAIL of ' + $docTotal) -ForegroundColor Green
Write-Host ('  runs    ' + $script:Dirs.runs) -ForegroundColor DarkGray
Write-Host ('  console ' + $latestPath) -ForegroundColor DarkGray
Write-Host ''

if (-not $NoOpen) { Start-Process -FilePath $latestPath }
