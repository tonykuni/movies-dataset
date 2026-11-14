# CELERITAS-TEMPLATE-JOIN
#Requires -Version 7.0
# VIA TOOL INSTALL W4 v0101 - 5 lanes parallel, timeout per lane, dynamic % progress, HTML lamp matrix
# S1 Graphify install --project | S2 Graphify code-only graph | S3 Playwright detect | S4 tool 5-check registry | S5 Env snapshot
# Rules: detect-only for anything not already decided; never touches dict\VDF\_active / functional modules\VDF / canonical

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'
$__env0 = @{ PATH = $env:PATH; TEMP = $env:TEMP; PYTHONUTF8 = $env:PYTHONUTF8 }

# ---------- 1. safe cleanup (own process only) ----------
[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
try { [System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal' } catch {}
$ts     = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path $env:TEMP "VIA_RUN_${ts}_W4_TOOLS"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$env:PYTHONUTF8 = '1'

# ---------- 2. accelerator (guarded) ----------
$vcRoot = $env:VIA_CELERITAS_ROOT
$accel  = 'NONE'
if ($vcRoot -and (Test-Path (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'))) {
  try { . (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'); $accel = 'AutoImport' } catch { $accel = 'AutoImport-FAILED' }
}

# ---------- 3. auto-detect roots ----------
$cands = @($env:VIA_ROOT,
           (Join-Path $env:OneDrive 'Documents\movies-dataset\VeritasIntelligenceAnalytics'),
           (Join-Path $env:USERPROFILE 'VIA-VDF-VRN'),
           'C:\VIA') | Where-Object { $_ -and (Test-Path $_) }
$root = $cands | Select-Object -First 1
$vcgc = $null
if ($root) {
  $vcgc = Get-ChildItem -Path $root -Directory -Recurse -Depth 2 -Filter 'via_00_vcgc' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
}
$target = if ($vcgc) { $vcgc } else { $root }

# ---------- 4. lane scriptblocks (each writes lane_N.json with pct/state) ----------
$laneBlock = {
  param($id, $name, $runDir, $root, $target, $timeout)
  $f = Join-Path $runDir "lane_$id.json"
  $log = Join-Path $runDir "lane_$id.log"
  function Put($pct, $state, $msg) {
    @{ id = $id; name = $name; pct = $pct; state = $state; msg = $msg; t = (Get-Date -Format 'HH:mm:ss') } | ConvertTo-Json -Compress | Set-Content -Path $f -Encoding UTF8
  }
  function Run($exe, $argv, $cwd) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe; $psi.Arguments = $argv; $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.RedirectStandardInput = $true
    $psi.CreateNoWindow = $true
    if ($cwd) { $psi.WorkingDirectory = $cwd }
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.StandardInput.Close()
    $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($timeout * 1000)) { try { $p.Kill($true) } catch {}; return @{ exit = -999; out = 'TIMEOUT' } }
    return @{ exit = $p.ExitCode; out = (($so.Result + "`n" + $se.Result).Trim()) }
  }
  try {
    Put 5 'RUN' 'start'
    switch ($id) {
      1 {
        $g = Get-Command graphify -ErrorAction SilentlyContinue
        if (-not $g) { Put 100 'RED' 'graphify not on PATH (uv tool update-shell)'; break }
        $v = Run $g.Source '--version' $null
        Put 40 'RUN' "ver=$($v.out)"
        if (-not $root) { Put 100 'YELLOW' "no VIA root; ver=$($v.out)"; break }
        $r = Run $g.Source 'install --project' $root
        Add-Content $log $r.out
        $tail = ($r.out -split "`n" | Select-Object -Last 2) -join ' | '
        if ($r.exit -eq 0) { Put 100 'GREEN' "ver=$($v.out) project-skill OK: $tail" } elseif ($r.exit -eq -999) { Put 100 'YELLOW' 'install --project TIMEOUT (interactive?)' } else { Put 100 'RED' "install exit=$($r.exit) $tail" }
      }
      2 {
        $g = Get-Command graphify -ErrorAction SilentlyContinue
        if (-not $g -or -not $target) { Put 100 'YELLOW' 'skip: graphify or target missing'; break }
        $ig = Join-Path $target '.graphifyignore'
        if (-not (Test-Path $ig)) { @('.venv/','venv/','node_modules/','_superseded/','__pycache__/','*.parquet','*.duckdb','*.db') | Set-Content -Path $ig -Encoding UTF8 }
        Put 15 'RUN' "extract $target"
        $t0 = Get-Date
        $r = Run $g.Source "extract `"$target`" --code-only --no-viz" $target
        Add-Content $log $r.out
        $sec = [int]((Get-Date) - $t0).TotalSeconds
        $gj = Join-Path $target 'graphify-out\graph.json'
        if ($r.exit -eq -999) { Put 100 'YELLOW' "extract TIMEOUT ${timeout}s - narrow target"; break }
        if (Test-Path $gj) {
          $j = Get-Content $gj -Raw | ConvertFrom-Json
          Put 100 'GREEN' "nodes=$($j.nodes.Count) edges=$($j.edges.Count) sec=$sec"
        } else { Put 100 'RED' "exit=$($r.exit) no graph.json sec=$sec" }
      }
      3 {
        $npx = Get-Command npx -ErrorAction SilentlyContinue
        $py  = Get-Command python -ErrorAction SilentlyContinue
        $m = @()
        if ($npx) { $m += 'npx=OK' } else { $m += 'npx=MISSING(Node needed for MCP)' }
        Put 40 'RUN' ($m -join ' ')
        if ($py) {
          $r = Run $py.Source '-c "import importlib.util as u;print(\"pw=\"+(\"OK\" if u.find_spec(\"playwright\") else \"MISSING\"))"' $null
          $m += ($r.out -split "`n" | Select-Object -Last 1)
        } else { $m += 'python=MISSING' }
        $st = if (($m -join ' ') -match 'MISSING') { 'YELLOW' } else { 'GREEN' }
        Put 100 $st ($m -join ' ')
      }
      4 {
        $tools = @(
          @{ id='TOOL-0001'; name='Graphify';       exe='graphify';  argv='--version' },
          @{ id='TOOL-0002'; name='Ponytail';       exe='node';      argv='--version' },
          @{ id='TOOL-0003'; name='OmniRoute';      exe='';          argv='' },
          @{ id='TOOL-0004'; name='Playwright';     exe='npx';       argv='--version' },
          @{ id='TOOL-0005'; name='AgentReach';     exe='';          argv='' },
          @{ id='TOOL-0006'; name='Scrapling';      exe='python';    argv='-c "import importlib.util as u;print(bool(u.find_spec(\"scrapling\")))"' },
          @{ id='TOOL-0007'; name='ChartDB';        exe='docker';    argv='--version' },
          @{ id='TOOL-0008'; name='diagram-design'; exe='';          argv='' },
          @{ id='TOOL-0009'; name='autoharness';    exe='';          argv='' },
          @{ id='TOOL-0010'; name='WordPressMCP';   exe='';          argv='' }
        )
        $rows = @(); $i = 0
        foreach ($t in $tools) {
          $i++; Put ([int](10 + 85 * $i / $tools.Count)) 'RUN' $t.name
          $st = 'GRAY'; $ver = 'not-registered'
          if ($t.exe) {
            $c = Get-Command $t.exe -ErrorAction SilentlyContinue
            if ($c) { $r = Run $c.Source $t.argv $null; $ver = (($r.out -split "`n") | Select-Object -First 1); $st = if ($r.exit -eq 0 -and $ver -notmatch 'False|TIMEOUT') { 'GREEN' } else { 'YELLOW' } }
            else { $st = 'YELLOW'; $ver = "$($t.exe) missing" }
          }
          $rows += [pscustomobject]@{ id=$t.id; name=$t.name; lamp=$st; version=$ver }
        }
        $rows | ConvertTo-Json | Set-Content (Join-Path $runDir 'VIA_ToolRegistry_W4_detect.json') -Encoding UTF8
        $gc = ($rows | Where-Object lamp -eq 'GREEN').Count
        Put 100 $(if ($gc -ge 2) { 'GREEN' } else { 'YELLOW' }) ("green=$gc yellow=" + ($rows | Where-Object lamp -eq 'YELLOW').Count + " gray=" + ($rows | Where-Object lamp -eq 'GRAY').Count)
      }
      5 {
        $m = @("root=$root", "target=$target", "pwsh=$($PSVersionTable.PSVersion)")
        $uv = Get-Command uv -ErrorAction SilentlyContinue
        $m += $(if ($uv) { 'uv=OK' } else { 'uv=MISSING' })
        $wg = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
        $m += $(if (Test-Path $wg) { 'winget=present-not-on-PATH' } else { 'winget=MISSING' })
        $m += "home-skill-stray=" + (Test-Path (Join-Path $env:USERPROFILE '.claude\skills\graphify'))
        Put 100 $(if ($root) { 'GREEN' } else { 'RED' }) ($m -join ' ')
      }
    }
  } catch { Put 100 'RED' ("EXC " + $_.Exception.Message) }
}

$names = @{ 1='S1 Graphify install --project'; 2='S2 Graphify code-only graph'; 3='S3 Playwright detect'; 4='S4 Tool 5-check (detect-only)'; 5='S5 Env snapshot' }
$jobs = @{}
foreach ($i in 1..5) {
  $to = if ($i -eq 2) { 420 } else { 90 }
  $jobs[$i] = Start-ThreadJob -ScriptBlock $laneBlock -ArgumentList $i, $names[$i], $runDir, $root, $target, $to -ThrottleLimit 5
}

# ---------- 5. dynamic progress (in-place redraw) ----------
function Read-Lane($i) {
  $f = Join-Path $runDir "lane_$i.json"
  if (Test-Path $f) { try { return (Get-Content $f -Raw | ConvertFrom-Json) } catch {} }
  return [pscustomobject]@{ id=$i; name=$names[$i]; pct=0; state='WAIT'; msg='' }
}
function Bar($p) { $n = [int]($p / 5); return ('#' * $n).PadRight(20, '.') }
$t0 = Get-Date; $wall = 480
Write-Host "`nVIA W4 TOOLS  accel=$accel  run=$runDir" -ForegroundColor Cyan
Write-Host ("`n" * 6)
while ($true) {
  $lanes = 1..5 | ForEach-Object { Read-Lane $_ }
  $tot = [int](($lanes | Measure-Object pct -Sum).Sum / 5)
  [Console]::SetCursorPosition(0, [Math]::Max(0, [Console]::CursorTop - 6))
  foreach ($l in $lanes) {
    $col = switch ($l.state) { 'GREEN' { 'Green' } 'YELLOW' { 'Yellow' } 'RED' { 'Red' } 'RUN' { 'Cyan' } default { 'DarkGray' } }
    $line = ('{0,-34} [{1}] {2,3}% {3,-6} {4}' -f $l.name, (Bar $l.pct), $l.pct, $l.state, ($l.msg -replace '\s+',' '))
    Write-Host $line.Substring(0, [Math]::Min($line.Length, [Console]::WindowWidth - 1)).PadRight([Console]::WindowWidth - 1) -ForegroundColor $col
  }
  Write-Host ('{0,-34} [{1}] {2,3}%  elapsed {3}s' -f 'TOTAL', (Bar $tot), $tot, [int]((Get-Date) - $t0).TotalSeconds).PadRight([Console]::WindowWidth - 1) -ForegroundColor White
  $done = ($jobs.Values | Where-Object { $_.State -in 'Completed','Failed','Stopped' }).Count
  if ($done -ge 5 -or ((Get-Date) - $t0).TotalSeconds -gt $wall) { break }
  Start-Sleep -Milliseconds 400
}
foreach ($j in $jobs.Values) { if ($j.State -eq 'Running') { Stop-Job $j -ErrorAction SilentlyContinue } ; Receive-Job $j -ErrorAction SilentlyContinue | Out-Null; Remove-Job $j -Force -ErrorAction SilentlyContinue }
$lanes = 1..5 | ForEach-Object { Read-Lane $_ }
foreach ($l in $lanes) { if ($l.state -in 'RUN','WAIT') { $l.state = 'YELLOW'; $l.msg = 'interrupted (wall timeout)' } }

# ---------- 6. HTML lamp matrix (static, pops from file) ----------
$reg = Join-Path $runDir 'VIA_ToolRegistry_W4_detect.json'
$toolRows = if (Test-Path $reg) { Get-Content $reg -Raw | ConvertFrom-Json } else { @() }
$css = @'
:root{--lamp-red:#E0342B;--lamp-yellow:#F5C518;--lamp-green:#2EB872;--lamp-gray:#9AA3AD;--bg:#F7F8FA;--ink:#1F2937;--line:#E5E7EB}
body{font:12px/1.4 "Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink);margin:16px}
h1{font-size:15px;margin:0 0 8px}table{border-collapse:collapse;width:100%;max-width:1100px;background:#fff}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}th{background:#EEF1F5;font-weight:600}
.l{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle}
.GREEN{background:var(--lamp-green)}.YELLOW{background:var(--lamp-yellow)}.GRAY{background:var(--lamp-gray)}
.RED{background:var(--lamp-red);animation:bl 1.6s ease-in-out infinite}@keyframes bl{50%{opacity:.25}}
.p{height:6px;background:#E5E7EB;border-radius:3px;overflow:hidden}.p>i{display:block;height:100%;background:var(--lamp-green)}
small{color:#6B7280}
'@
$h = New-Object System.Text.StringBuilder
[void]$h.Append("<!doctype html><html><head><meta charset='utf-8'><title>VIA W4 TOOLS $ts</title><style>$css</style></head><body>")
[void]$h.Append("<h1>VIA W4 TOOL INSTALL &middot; 5 lanes &middot; $ts</h1><small>accel=$accel &middot; root=$root &middot; target=$target &middot; lamp colours = VIA_UI_FormatLock tokens (replace :root vars with typekit when linked)</small>")
[void]$h.Append("<h1 style='margin-top:12px'>Lanes</h1><table><tr><th></th><th>Lane</th><th>%</th><th>Result</th><th>Time</th></tr>")
foreach ($l in $lanes) { [void]$h.Append("<tr><td><span class='l $($l.state)'></span></td><td>$($l.name)</td><td style='width:120px'><div class='p'><i style='width:$($l.pct)%'></i></div>$($l.pct)%</td><td>$([System.Net.WebUtility]::HtmlEncode([string]$l.msg))</td><td>$($l.t)</td></tr>") }
[void]$h.Append("</table><h1 style='margin-top:12px'>Tool registry (detect-only)</h1><table><tr><th></th><th>ID</th><th>Tool</th><th>Version / state</th></tr>")
foreach ($r in $toolRows) { [void]$h.Append("<tr><td><span class='l $($r.lamp)'></span></td><td>$($r.id)</td><td>$($r.name)</td><td>$([System.Net.WebUtility]::HtmlEncode([string]$r.version))</td></tr>") }
[void]$h.Append("</table></body></html>")
$html = Join-Path $runDir "VIA_W4_TOOLS_${ts}.html"
$h.ToString() | Set-Content -Path $html -Encoding UTF8
try { Invoke-Item $html } catch {}

# ---------- 7. console summary: yellow = paste back, red = errors ----------
Write-Host "`n==== PASTE BACK ====" -ForegroundColor Yellow
Write-Host "RUN=$runDir" -ForegroundColor Yellow
Write-Host "ACCEL=$accel ROOT=$root TARGET=$target" -ForegroundColor Yellow
foreach ($l in $lanes) {
  $c = if ($l.state -eq 'RED') { 'Red' } else { 'Yellow' }
  Write-Host ("{0} {1} {2}" -f $l.state, $l.name, ($l.msg -replace '\s+',' ')) -ForegroundColor $c
}
foreach ($r in $toolRows) { Write-Host ("{0} {1} {2} {3}" -f $r.lamp, $r.id, $r.name, $r.version) -ForegroundColor $(if ($r.lamp -eq 'RED') { 'Red' } else { 'Yellow' }) }
Write-Host "HTML=$html" -ForegroundColor Yellow
Write-Host "NEXT: paste yellow lines back" -ForegroundColor Yellow

# ---------- 8. restore env ----------
$env:PATH = $__env0.PATH; $env:TEMP = $__env0.TEMP; $env:PYTHONUTF8 = $__env0.PYTHONUTF8
