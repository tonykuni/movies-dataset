# CELERITAS-TEMPLATE-JOIN
#Requires -Version 7.0
# VIA ONE-SHOT W4 v0102 - handles everything in Downloads from this batch:
#   Invoke-VIA-ToolInstall-W4-v*.ps1 · files (*).zip · wl01*.zip · Invoke-VIA-WorkbenchLocal-v*.ps1
# L1 discover+unpack (staging, originals untouched) · L2 accelerator join coverage -> 100% via joined copies
# L3 land token-tools artifacts into VIA root (append-only) · L4 run W4 installer in own window · L5 run newest WorkbenchLocal in own window
# Never touches dict\VDF\_active / functional modules\VDF / canonical. No Invoke-Expression, no WebClient, no HKLM, no Stop-Process on other PIDs.

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'
$__env0 = @{ PATH = $env:PATH; TEMP = $env:TEMP; PYTHONUTF8 = $env:PYTHONUTF8 }

# ---------- 1. safe cleanup (own process only) ----------
[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
try { [System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal' } catch {}
$ts      = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir  = Join-Path $env:TEMP "VIA_RUN_${ts}_ONESHOT_W4"
$staging = Join-Path $runDir 'staging'
$joinDir = Join-Path $runDir '_vcjoin'
New-Item -ItemType Directory -Path $runDir, $staging, $joinDir -Force | Out-Null
$env:PYTHONUTF8 = '1'

# ---------- 2. accelerator (guarded) ----------
$vcRoot = $env:VIA_CELERITAS_ROOT
$accel  = 'NONE'
if ($vcRoot -and (Test-Path (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'))) {
  try { . (Join-Path $vcRoot 'VeritasCeleritas.PS7.AutoImport.ps1'); $accel = 'AutoImport' } catch { $accel = 'AutoImport-FAILED' }
}

# ---------- 3. auto-detect roots & inputs ----------
$dl    = Join-Path $env:USERPROFILE 'Downloads'
$cands = @($env:VIA_ROOT,
           (Join-Path $env:OneDrive 'Documents\movies-dataset\VeritasIntelligenceAnalytics'),
           (Join-Path $env:USERPROFILE 'VIA-VDF-VRN'),
           'C:\VIA') | Where-Object { $_ -and (Test-Path $_) }
$root  = $cands | Select-Object -First 1
$zips  = @(Get-ChildItem -Path $dl -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(files( \(\d+\))?|wl\d{4})\.zip$' })
$w4    = Get-ChildItem -Path $dl -Filter 'Invoke-VIA-ToolInstall-W4-v*.ps1' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$wbDl  = @(Get-ChildItem -Path $dl -Filter 'Invoke-VIA-WorkbenchLocal-v*.ps1' -File -ErrorAction SilentlyContinue)

# ---------- 4. lane block ----------
$laneBlock = {
  param($id, $name, $runDir, $staging, $joinDir, $root, $dl, $zipPaths, $w4Path, $wbDlPaths, $timeout)
  $f = Join-Path $runDir "lane_$id.json"
  function Put($pct, $state, $msg) {
    @{ id = $id; name = $name; pct = $pct; state = $state; msg = $msg; t = (Get-Date -Format 'HH:mm:ss') } | ConvertTo-Json -Compress | Set-Content -Path $f -Encoding UTF8
  }
  function WaitLane($n, $sec) {
    $g = Join-Path $runDir "lane_$n.json"; $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $sec) {
      if (Test-Path $g) { try { $o = Get-Content $g -Raw | ConvertFrom-Json; if ($o.pct -ge 100) { return $o } } catch {} }
      Start-Sleep -Milliseconds 500
    }
    return $null
  }
  function RunWindow($ps1, $sec, $cwd) {
    $argv = @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$ps1`"")
    $p = if ($cwd) { Start-Process pwsh -ArgumentList $argv -WorkingDirectory $cwd -PassThru } else { Start-Process pwsh -ArgumentList $argv -PassThru }
    $done = $p.WaitForExit($sec * 1000)
    return @{ pid = $p.Id; done = $done; exit = $(if ($done) { $p.ExitCode } else { -999 }) }
  }
  try {
    Put 5 'RUN' 'start'
    switch ($id) {
      1 {
        $inv = @(); $n = 0
        foreach ($z in $zipPaths) {
          $n++; Put ([int](5 + 60 * $n / [Math]::Max(1, $zipPaths.Count))) 'RUN' "unzip $(Split-Path $z -Leaf)"
          $dest = Join-Path $staging ([IO.Path]::GetFileNameWithoutExtension($z) -replace '[^\w\-]', '_')
          try { Expand-Archive -LiteralPath $z -DestinationPath $dest -Force; $cnt = (Get-ChildItem $dest -Recurse -File).Count; $inv += "$(Split-Path $z -Leaf)=$cnt files" }
          catch { $inv += "$(Split-Path $z -Leaf)=UNZIP-FAIL $($_.Exception.Message)" }
        }
        foreach ($p in $wbDlPaths) { Copy-Item -LiteralPath $p -Destination (Join-Path $staging (Split-Path $p -Leaf)) -Force }
        if ($w4Path) { Copy-Item -LiteralPath $w4Path -Destination (Join-Path $staging (Split-Path $w4Path -Leaf)) -Force }
        $all = Get-ChildItem $staging -Recurse -File
        $ps  = @($all | Where-Object Extension -eq '.ps1'); $py = @($all | Where-Object Extension -eq '.py')
        $wbs = @($all | Where-Object { $_.Name -match '^Invoke-VIA-WorkbenchLocal-v(\d+)\.ps1$' }) | Sort-Object { [int]([regex]::Match($_.Name, 'v(\d+)').Groups[1].Value) } -Descending
        $newestWb = if ($wbs.Count) { $wbs[0].FullName } else { '' }
        @{ zips = $inv; total = $all.Count; ps1 = $ps.Count; py = $py.Count; newestWorkbench = $newestWb; workbenches = @($wbs.Name) } | ConvertTo-Json | Set-Content (Join-Path $runDir 'inventory.json') -Encoding UTF8
        Put 100 'GREEN' ("files=$($all.Count) ps1=$($ps.Count) py=$($py.Count) newestWB=" + (Split-Path $newestWb -Leaf) + ' | ' + ($inv -join ' ; '))
      }
      2 {
        $w = WaitLane 1 120
        if (-not $w) { Put 100 'YELLOW' 'L1 not ready'; break }
        $files = @(Get-ChildItem $staging -Recurse -File | Where-Object { $_.Extension -in '.ps1', '.py' })
        if (-not $files.Count) { Put 100 'YELLOW' 'no ps1/py to scan'; break }
        $rows = @(); $i = 0; $full = 0; $hdr = 0; $none = 0
        foreach ($fi in $files) {
          $i++; Put ([int](10 + 80 * $i / $files.Count)) 'RUN' $fi.Name
          $txt = Get-Content -LiteralPath $fi.FullName -Raw -ErrorAction SilentlyContinue
          if ($null -eq $txt) { $txt = '' }
          $rel = $fi.FullName.Substring($staging.Length).TrimStart('\')
          $dst = Join-Path $joinDir $rel
          New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
          if ($fi.Extension -eq '.ps1') {
            $hasMarker = $txt -match 'CELERITAS-TEMPLATE-JOIN'
            $hasImport = $txt -match 'AutoImport\.ps1|VeritasCeleritas\.PS7\.Template\.ps1'
            $hasBody   = $txt -match 'Invoke-CeleritasGenerated'
            $parseErr  = $null; $null = [System.Management.Automation.Language.Parser]::ParseFile($fi.FullName, [ref]$null, [ref]$parseErr)
            $pe = if ($parseErr) { $parseErr.Count } else { 0 }
            if ($hasMarker -and $hasImport -and $hasBody) { $st = 'FULL'; $full++; Copy-Item -LiteralPath $fi.FullName -Destination $dst -Force }
            elseif ($hasMarker -and $hasImport) { $st = 'HEADER'; $hdr++; Copy-Item -LiteralPath $fi.FullName -Destination $dst -Force }
            else {
              $st = 'JOINED-COPY'; $hdr++
              $h = @('# CELERITAS-TEMPLATE-JOIN  [VIA:PS-ACCEL] joined-copy ' + (Get-Date -Format 'yyyy-MM-dd') + ' (original untouched)',
                     '#Requires -Version 7.0',
                     'if ($env:VIA_CELERITAS_ROOT -and (Test-Path (Join-Path $env:VIA_CELERITAS_ROOT "VeritasCeleritas.PS7.AutoImport.ps1"))) { . (Join-Path $env:VIA_CELERITAS_ROOT "VeritasCeleritas.PS7.AutoImport.ps1") }',
                     '')
              $body = $txt -replace '(?m)^\s*#Requires -Version [\d\.]+\s*$', ''
              ($h -join "`r`n") + $body | Set-Content -LiteralPath $dst -Encoding UTF8
            }
            $rows += [pscustomobject]@{ file = $rel; kind = 'ps1'; join = $st; parse_errors = $pe }
          } else {
            $hasVc = $txt -match 'VeritasCeleritas_v\d+'
            $hasShield = $txt -match '@vc\.shield'
            $hasInput  = $txt -match '(?m)^\s*[^#]*\binput\('
            if ($hasVc -and $hasShield) { $st = 'FULL'; $full++; Copy-Item -LiteralPath $fi.FullName -Destination $dst -Force }
            elseif ($hasVc) { $st = 'HEADER'; $hdr++; Copy-Item -LiteralPath $fi.FullName -Destination $dst -Force }
            else {
              $st = 'JOINED-COPY'; $hdr++
              $h = @('# [VIA:ACCEL-BRIDGE] joined-copy ' + (Get-Date -Format 'yyyy-MM-dd') + ' (original untouched)',
                     'try:', '    import VeritasCeleritas_v1141 as vc', 'except Exception:', '    vc = None', '')
              ($h -join "`n") + $txt | Set-Content -LiteralPath $dst -Encoding UTF8
            }
            if ($hasInput) { $st += '+input()' }
            $rows += [pscustomobject]@{ file = $rel; kind = 'py'; join = $st; parse_errors = 0 }
          }
        }
        $rows | ConvertTo-Json | Set-Content (Join-Path $runDir 'coverage.json') -Encoding UTF8
        $covSrc = [int](100 * $full / $files.Count)
        $perr = ($rows | Measure-Object parse_errors -Sum).Sum
        $st2 = if ($perr -gt 0) { 'RED' } elseif ($full -eq $files.Count) { 'GREEN' } else { 'YELLOW' }
        Put 100 $st2 "scanned=$($files.Count) full=$full header/joined=$hdr parse_errors=$perr | source-coverage=$covSrc% joined-copy-coverage=100% -> $joinDir"
      }
      3 {
        $w = WaitLane 1 120
        if (-not $root) { Put 100 'RED' 'VIA root not found; set $env:VIA_ROOT'; break }
        $m = @()
        $blk = Get-ChildItem $staging, $dl -Recurse -File -Filter 'CLAUDE.md.VIA-TOKEN-BLOCK.md' -ErrorAction SilentlyContinue | Select-Object -First 1
        $ign = Get-ChildItem $staging, $dl -Recurse -File -Filter '.claudeignore' -ErrorAction SilentlyContinue | Select-Object -First 1
        $man = Get-ChildItem $staging, $dl -Recurse -File -Filter 'VIA_Workflow_VCGC_TokenTools.json' -ErrorAction SilentlyContinue | Select-Object -First 1
        Put 30 'RUN' 'landing'
        $cl = Join-Path $root 'CLAUDE.md'
        if ($blk) {
          $cur = if (Test-Path $cl) { Get-Content $cl -Raw } else { '' }
          if ($cur -notmatch 'VIA TOKEN BLOCK') { Add-Content -Path $cl -Value ("`r`n" + (Get-Content $blk.FullName -Raw)) -Encoding UTF8; $m += 'CLAUDE.md=appended' } else { $m += 'CLAUDE.md=already' }
        } else { $m += 'CLAUDE.md=block-missing' }
        $ci = Join-Path $root '.claudeignore'
        if ($ign) {
          $have = if (Test-Path $ci) { @(Get-Content $ci) } else { @() }
          $new  = @(Get-Content $ign.FullName) | Where-Object { $_ -and ($have -notcontains $_) }
          if ($new.Count) { Add-Content -Path $ci -Value $new -Encoding UTF8 }
          $m += ".claudeignore=+$($new.Count)"
        } else { $m += '.claudeignore=missing' }
        if ($man) {
          $wf = Join-Path $root 'workflows'; New-Item -ItemType Directory -Path $wf -Force | Out-Null
          $to = Join-Path $wf $man.Name
          if (-not (Test-Path $to)) { Copy-Item $man.FullName $to; $m += 'manifest=landed' } else { $m += 'manifest=already' }
        } else { $m += 'manifest=missing' }
        $ctx = Join-Path $root '.claude\ctx'; New-Item -ItemType Directory -Path $ctx -Force | Out-Null
        $made = 0
        foreach ($s in 'vcgc','vdf','vrn2','vap') {
          $p = Join-Path $ctx "$s.md"
          if (-not (Test-Path $p)) { @("# $($s.ToUpper()) context (<=120 lines, read only when a task names $s)", "- entry: via-$s", "- status: see RC-1 matrix") | Set-Content $p -Encoding UTF8; $made++ }
        }
        $m += "ctx-stubs=+$made"
        Put 100 $(if (($m -join ' ') -match 'missing') { 'YELLOW' } else { 'GREEN' }) ($m -join ' ')
      }
      4 {
        if (-not $w4Path) { Put 100 'YELLOW' 'W4 installer not in Downloads'; break }
        Put 20 'RUN' "launch $(Split-Path $w4Path -Leaf) (own window)"
        $before = @(Get-ChildItem $env:TEMP -Directory -Filter 'VIA_RUN_*_W4_TOOLS' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
        $r = RunWindow $w4Path $timeout $null
        $after = Get-ChildItem $env:TEMP -Directory -Filter 'VIA_RUN_*_W4_TOOLS' -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.FullName } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $after) { Put 100 'YELLOW' "W4 pid=$($r.pid) exit=$($r.exit) no run dir found"; break }
        $sub = @()
        foreach ($k in 1..5) { $lj = Join-Path $after.FullName "lane_$k.json"; if (Test-Path $lj) { $o = Get-Content $lj -Raw | ConvertFrom-Json; $sub += "S$k=$($o.state)" } }
        $reg = Join-Path $after.FullName 'VIA_ToolRegistry_W4_detect.json'
        if (Test-Path $reg) { Copy-Item $reg (Join-Path $runDir 'VIA_ToolRegistry_W4_detect.json') -Force }
        $st = if (($sub -join ' ') -match 'RED') { 'RED' } elseif ($r.done) { 'GREEN' } else { 'YELLOW' }
        Put 100 $st ("exit=$($r.exit) " + ($sub -join ' ') + " run=$($after.Name)")
      }
      5 {
        $w = WaitLane 1 120
        $inv = Join-Path $runDir 'inventory.json'
        $wb = ''
        if (Test-Path $inv) { $wb = (Get-Content $inv -Raw | ConvertFrom-Json).newestWorkbench }
        if (-not $wb) { $wb = @($wbDlPaths | Sort-Object { [int]([regex]::Match($_, 'v(\d+)\.ps1$').Groups[1].Value) } -Descending) | Select-Object -First 1 }
        if (-not $wb) { Put 100 'YELLOW' 'no WorkbenchLocal found'; break }
        $parseErr = $null; $null = [System.Management.Automation.Language.Parser]::ParseFile($wb, [ref]$null, [ref]$parseErr)
        if ($parseErr -and $parseErr.Count) { Put 100 'RED' ("ParseFile errors=$($parseErr.Count) in " + (Split-Path $wb -Leaf) + ': ' + $parseErr[0].Message); break }
        Put 30 'RUN' "launch $(Split-Path $wb -Leaf) (own window)"
        $r = RunWindow $wb $timeout (Split-Path $wb)
        if ($r.done) { Put 100 $(if ($r.exit -eq 0) { 'GREEN' } else { 'YELLOW' }) ("exit=$($r.exit) " + (Split-Path $wb -Leaf)) }
        else { Put 100 'YELLOW' ("still running pid=$($r.pid) (left open) " + (Split-Path $wb -Leaf)) }
      }
    }
  } catch { Put 100 'RED' ("EXC " + $_.Exception.Message) }
}

$names = @{ 1='L1 Discover + unpack'; 2='L2 Accelerator join coverage'; 3='L3 Land token-tools (append-only)'; 4='L4 Run W4 tool installer'; 5='L5 Run newest WorkbenchLocal' }
$zipPaths = @($zips | Select-Object -ExpandProperty FullName)
$wbPaths  = @($wbDl | Select-Object -ExpandProperty FullName)
$w4Path   = if ($w4) { $w4.FullName } else { '' }
$jobs = @{}
foreach ($i in 1..5) {
  $to = switch ($i) { 4 { 900 } 5 { 300 } default { 180 } }
  $jobs[$i] = Start-ThreadJob -ScriptBlock $laneBlock -ArgumentList $i, $names[$i], $runDir, $staging, $joinDir, $root, $dl, $zipPaths, $w4Path, $wbPaths, $to -ThrottleLimit 5
}

# ---------- 5. dynamic progress (in-place redraw) ----------
function Read-Lane($i) {
  $f = Join-Path $runDir "lane_$i.json"
  if (Test-Path $f) { try { return (Get-Content $f -Raw | ConvertFrom-Json) } catch {} }
  return [pscustomobject]@{ id=$i; name=$names[$i]; pct=0; state='WAIT'; msg='' }
}
function Bar($p) { $n = [int]($p / 5); return ('#' * $n).PadRight(20, '.') }
function Width { try { return [Math]::Max(60, [Console]::WindowWidth - 1) } catch { return 120 } }
$t0 = Get-Date; $wall = 960
Write-Host "`nVIA ONE-SHOT W4  accel=$accel  root=$root  zips=$($zipPaths.Count)  run=$runDir" -ForegroundColor Cyan
Write-Host ("`n" * 6)
while ($true) {
  $lanes = 1..5 | ForEach-Object { Read-Lane $_ }
  $tot = [int](($lanes | Measure-Object pct -Sum).Sum / 5)
  try { [Console]::SetCursorPosition(0, [Math]::Max(0, [Console]::CursorTop - 6)) } catch {}
  $w = Width
  foreach ($l in $lanes) {
    $col = switch ($l.state) { 'GREEN' { 'Green' } 'YELLOW' { 'Yellow' } 'RED' { 'Red' } 'RUN' { 'Cyan' } default { 'DarkGray' } }
    $line = ('{0,-34} [{1}] {2,3}% {3,-6} {4}' -f $l.name, (Bar $l.pct), $l.pct, $l.state, ($l.msg -replace '\s+',' '))
    if ($line.Length -gt $w) { $line = $line.Substring(0, $w) }
    Write-Host $line.PadRight($w) -ForegroundColor $col
  }
  Write-Host ('{0,-34} [{1}] {2,3}%  elapsed {3}s' -f 'TOTAL', (Bar $tot), $tot, [int]((Get-Date) - $t0).TotalSeconds).PadRight($w) -ForegroundColor White
  $done = ($jobs.Values | Where-Object { $_.State -in 'Completed','Failed','Stopped' }).Count
  if ($done -ge 5 -or ((Get-Date) - $t0).TotalSeconds -gt $wall) { break }
  Start-Sleep -Milliseconds 400
}
foreach ($j in $jobs.Values) { if ($j.State -eq 'Running') { Stop-Job $j -ErrorAction SilentlyContinue }; Receive-Job $j -ErrorAction SilentlyContinue | Out-Null; Remove-Job $j -Force -ErrorAction SilentlyContinue }
$lanes = 1..5 | ForEach-Object { Read-Lane $_ }
foreach ($l in $lanes) { if ($l.state -in 'RUN','WAIT') { $l.state = 'YELLOW'; $l.msg = 'interrupted (wall timeout)' } }

# ---------- 6. HTML lamp matrix ----------
$covPath = Join-Path $runDir 'coverage.json'
$cov = if (Test-Path $covPath) { @(Get-Content $covPath -Raw | ConvertFrom-Json) } else { @() }
$regPath = Join-Path $runDir 'VIA_ToolRegistry_W4_detect.json'
$toolRows = if (Test-Path $regPath) { @(Get-Content $regPath -Raw | ConvertFrom-Json) } else { @() }
$css = @'
:root{--lamp-red:#E0342B;--lamp-yellow:#F5C518;--lamp-green:#2EB872;--lamp-gray:#9AA3AD;--bg:#F7F8FA;--ink:#1F2937;--line:#E5E7EB}
body{font:12px/1.4 "Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink);margin:16px}
h1{font-size:15px;margin:12px 0 6px}table{border-collapse:collapse;width:100%;max-width:1100px;background:#fff}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}th{background:#EEF1F5;font-weight:600}
.l{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle}
.GREEN,.FULL{background:var(--lamp-green)}.YELLOW,.HEADER,.JOINED-COPY{background:var(--lamp-yellow)}.GRAY{background:var(--lamp-gray)}
.RED{background:var(--lamp-red);animation:bl 1.6s ease-in-out infinite}@keyframes bl{50%{opacity:.25}}
.p{height:6px;background:#E5E7EB;border-radius:3px;overflow:hidden}.p>i{display:block;height:100%;background:var(--lamp-green)}small{color:#6B7280}
'@
$enc = { param($s) [System.Net.WebUtility]::HtmlEncode([string]$s) }
$h = New-Object System.Text.StringBuilder
[void]$h.Append("<!doctype html><html><head><meta charset='utf-8'><title>VIA ONE-SHOT W4 $ts</title><style>$css</style></head><body>")
[void]$h.Append("<h1>VIA ONE-SHOT W4 &middot; $ts</h1><small>accel=$accel &middot; root=$root &middot; staging=$staging &middot; joined copies=$joinDir (originals untouched)</small>")
[void]$h.Append("<h1>Lanes</h1><table><tr><th></th><th>Lane</th><th>%</th><th>Result</th><th>Time</th></tr>")
foreach ($l in $lanes) { [void]$h.Append("<tr><td><span class='l $($l.state)'></span></td><td>$($l.name)</td><td style='width:120px'><div class='p'><i style='width:$($l.pct)%'></i></div>$($l.pct)%</td><td>$(& $enc $l.msg)</td><td>$($l.t)</td></tr>") }
[void]$h.Append("</table><h1>Accelerator join coverage</h1><table><tr><th></th><th>File</th><th>Kind</th><th>Join</th><th>Parse errors</th></tr>")
foreach ($r in $cov) { $lp = if ($r.parse_errors -gt 0) { 'RED' } elseif ($r.join -like 'FULL*') { 'GREEN' } else { 'YELLOW' }; [void]$h.Append("<tr><td><span class='l $lp'></span></td><td>$(& $enc $r.file)</td><td>$($r.kind)</td><td>$($r.join)</td><td>$($r.parse_errors)</td></tr>") }
[void]$h.Append("</table><h1>Tool registry (from W4, detect-only)</h1><table><tr><th></th><th>ID</th><th>Tool</th><th>Version / state</th></tr>")
foreach ($r in $toolRows) { [void]$h.Append("<tr><td><span class='l $($r.lamp)'></span></td><td>$($r.id)</td><td>$($r.name)</td><td>$(& $enc $r.version)</td></tr>") }
[void]$h.Append("</table></body></html>")
$html = Join-Path $runDir "VIA_ONESHOT_W4_${ts}.html"
$h.ToString() | Set-Content -Path $html -Encoding UTF8
try { Invoke-Item $html } catch {}

# ---------- 7. console summary: yellow = paste back, red = errors ----------
Write-Host "`n==== PASTE BACK ====" -ForegroundColor Yellow
Write-Host "RUN=$runDir" -ForegroundColor Yellow
Write-Host "ACCEL=$accel ROOT=$root ZIPS=$($zipPaths.Count) W4=$(Split-Path $w4Path -Leaf) WB=$($wbPaths.Count)" -ForegroundColor Yellow
foreach ($l in $lanes) { Write-Host ("{0} {1} {2}" -f $l.state, $l.name, ($l.msg -replace '\s+',' ')) -ForegroundColor $(if ($l.state -eq 'RED') { 'Red' } else { 'Yellow' }) }
$full = @($cov | Where-Object { $_.join -like 'FULL*' }).Count
Write-Host ("COVERAGE source-full={0}/{1} joined-copies={1}/{1}" -f $full, $cov.Count) -ForegroundColor Yellow
foreach ($r in @($cov | Where-Object { $_.parse_errors -gt 0 })) { Write-Host ("RED PARSE {0} errors={1}" -f $r.file, $r.parse_errors) -ForegroundColor Red }
foreach ($r in $toolRows) { Write-Host ("{0} {1} {2} {3}" -f $r.lamp, $r.id, $r.name, $r.version) -ForegroundColor $(if ($r.lamp -eq 'RED') { 'Red' } else { 'Yellow' }) }
Write-Host "HTML=$html" -ForegroundColor Yellow
Write-Host "NEXT: paste yellow lines back" -ForegroundColor Yellow

# ---------- 8. restore env ----------
$env:PATH = $__env0.PATH; $env:TEMP = $__env0.TEMP; $env:PYTHONUTF8 = $__env0.PYTHONUTF8
