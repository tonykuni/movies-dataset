#requires -Version 7.0
param(
    [string]$Root      = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    [string]$PythonExe = 'C:\Python313\python.exe',
    [string]$VenvPy    = 'C:\Users\tonyk\envs\via_vrn4\Scripts\python.exe',
    [string]$OutRoot   = 'C:\VIA\VIA_SixStreams',
    [string]$Unified   = 'C:\Users\tonyk\Downloads\Invoke-VIA-Unified-Accel20-v0103.ps1',
    [int]$StreamTimeoutS = 900,
    [string]$GoToken   = '',
    [switch]$NoOpen
)

# =====================================================================
# Invoke-VIA-SixStreams-v0100   (批342)
#
# Six independent pipelines, run concurrently, under the Zero-Hydra rule:
#   - every stream is its own child process with its own log and hard
#     timeout; a hang or crash in one cannot stall or corrupt another
#   - no stream writes into the mother tree unless -GoToken GO_v1, and
#     even then only through generators that keep .bak siblings and
#     re-parse before writing
#   - streams share nothing at run time; the only join point is this
#     script reading their exit codes and log tails afterwards
#
#   S1  代碼層 AST 修復       Unified engine Scan (PS AST) + DeckServer v0119 selftest
#   S2  SSOT / Regex 校準     MDL115 SSOTRegexDict selftest + MDL116 v0110 selftest (thresholds registry)
#   S3  解耦 / 模組註冊       MDL122 IntakeRoster v0102 selftest (three new intakes)
#   S4  性能 / 死碼           Unified engine drift ledger + DefTest audit (report only)
#   S5  沙盒回歸              VAP v025 bundled tests + Unified Verify (pytest)
#   S6  UI Matrix / 部署      MDL116 v0110 regen (+ --open) and this matrix
# =====================================================================

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Stamp = $script:StartedAt.ToString('yyyyMMdd_HHmmss')
$script:Apply = ($GoToken -eq 'GO_v1')
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Log { param([string]$M, [string]$L = 'INFO')
    $c = 'Gray'; if ($L -eq 'OK') { $c = 'Green' }; if ($L -eq 'WARN') { $c = 'Yellow' }; if ($L -eq 'FAIL') { $c = 'Red' }; if ($L -eq 'S') { $c = 'Cyan' }
    Write-Host ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $M) -ForegroundColor $c }

$runDir = Join-Path $OutRoot ('RUN_' + $script:Stamp)
foreach ($d in @($runDir, (Join-Path $runDir 'logs'), (Join-Path $runDir 'reports'))) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }
$reg = Join-Path $Root 'supportive modules\registry'
$vap25 = Join-Path $Root 'functional modules\VAP\references\intake\VAP_v025_Complete_Package'

function Latest { param([string]$Pat) $h = @(Get-ChildItem -LiteralPath $reg -Filter $Pat -File | Sort-Object Name); if ($h.Count) { return $h[-1].FullName }; return '' }

Write-Host ''
Write-Host '  VIA Six Streams  ·  Zero-Hydra  ·  ' + $(if ($script:Apply) { 'APPLY' } else { 'DRY-RUN' }) -ForegroundColor White
Write-Host ''

# ---- stream definitions: each is [name, exe, args[], workdir, weight] ----
$goArg = @(); if ($script:Apply) { $goArg = @('-GoToken', 'GO_v1') }
$streams = @(
    @{ Id='S1'; Zh='代碼層 AST 修復';   Exe='pwsh';      Args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$Unified,'-Mode',$(if($script:Apply){'Repair'}else{'Scan'}),'-Root',$Root,'-OutRoot',(Join-Path $runDir 'S1_unified'),'-NoOpen','-RepairParseErrors') + $goArg; Wd=$Root },
    @{ Id='S1b'; Zh='DeckServer v0119 自測'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL095_DeckServer_v0*.py'),'--selftest'); Wd=$reg },
    @{ Id='S2'; Zh='SSOT/Regex 字典自測'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL115_SSOTRegexDict_v0*.py'),'--selftest'); Wd=$reg },
    @{ Id='S2b'; Zh='門檻冊 SSOT · MDL116 自測'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL116_UnifiedShell_v0*.py'),'--selftest'); Wd=$reg },
    @{ Id='S3'; Zh='上船件冊 註冊三收容'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL122_IntakeRoster_v0*.py'),'--selftest'); Wd=$reg },
    @{ Id='S4'; Zh='死碼/漂移 稽核(唯讀)'; Exe=$VenvPy; Args=@((Join-Path (Split-Path $Unified -Parent) 'VIA_DefTestAudit_v0100.py'),'--root',$Root,'--out',(Join-Path $runDir 'S4_deftest')); Wd=$Root },
    @{ Id='S5'; Zh='VAP v025 套件回歸'; Exe=$PythonExe; Args=@((Join-Path $vap25 'tests\run_all_tests_v025.py')); Wd=$vap25 },
    @{ Id='S5b'; Zh='沙盒 pytest 回歸(Verify)'; Exe='pwsh'; Args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$Unified,'-Mode','Verify','-Root',$Root,'-PythonExe',$VenvPy,'-OutRoot',(Join-Path $runDir 'S5_verify'),'-NoOpen','-MaxTestFiles','25'); Wd=$Root },
    @{ Id='S6'; Zh='四殼再生 + 自動跳出'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL116_UnifiedShell_v0*.py')) + $(if ($NoOpen) { @() } else { @('--open') }); Wd=$reg }
)

# ---- launch all concurrently; file-redirected; no pipes ----
$procs = @{}
foreach ($s in $streams) {
    $log = Join-Path $runDir ('logs\' + $s.Id + '.log')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $s.Exe; $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8; $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $psi.WorkingDirectory = $s.Wd
    foreach ($a in $s.Args) { if ($a -ne '') { $psi.ArgumentList.Add($a) } }
    $p = New-Object System.Diagnostics.Process; $p.StartInfo = $psi
    $sw = [System.IO.StreamWriter]::new($log, $false, $script:Utf8NoBom)
    try {
        $p.Start() | Out-Null
        $tOut = $p.StandardOutput.ReadToEndAsync(); $tErr = $p.StandardError.ReadToEndAsync()
        $procs[$s.Id] = @{ P=$p; Out=$tOut; Err=$tErr; Log=$log; W=$sw; Def=$s; T0=(Get-Date) }
        Write-Log ($s.Id.PadRight(4) + ' launched  ' + $s.Zh) 'S'
    } catch {
        $sw.WriteLine('LAUNCH FAILED: ' + $_.Exception.Message); $sw.Close()
        $procs[$s.Id] = @{ P=$null; Log=$log; Def=$s; Failed=$true }
        Write-Log ($s.Id.PadRight(4) + ' launch failed: ' + $_.Exception.Message) 'FAIL'
    }
}

# ---- poll with progress; hard timeout per stream ----
$done = @{}
while ($done.Count -lt $procs.Count) {
    Start-Sleep -Milliseconds 700
    foreach ($id in $procs.Keys) {
        if ($done.ContainsKey($id)) { continue }
        $e = $procs[$id]
        if ($e.Failed) { $done[$id] = -3; continue }
        $el = ((Get-Date) - $e.T0).TotalSeconds
        if ($e.P.HasExited) {
            $e.P.WaitForExit()
            try { $e.W.Write($e.Out.GetAwaiter().GetResult()); $e.W.Write($e.Err.GetAwaiter().GetResult()) } catch { }
            $e.W.Close(); $done[$id] = $e.P.ExitCode
            Write-Log ($id.PadRight(4) + ' exit ' + $e.P.ExitCode + '  ' + [int]$el + 's  ' + $e.Def.Zh) $(if ($e.P.ExitCode -eq 0) { 'OK' } else { 'WARN' })
        } elseif ($el -ge $StreamTimeoutS) {
            try { $e.P.Kill($true) } catch { }
            try { $e.W.WriteLine('TIMEOUT ' + $StreamTimeoutS + 's (killed; other streams unaffected)') } catch { }
            $e.W.Close(); $done[$id] = -9
            Write-Log ($id.PadRight(4) + ' TIMEOUT ' + $StreamTimeoutS + 's  ' + $e.Def.Zh) 'FAIL'
        }
    }
    $running = @($procs.Keys | Where-Object { -not $done.ContainsKey($_) })
    Write-Progress -Activity 'VIA Six Streams' -Status ('running: ' + ($running -join ' ')) -PercentComplete ([int](100 * $done.Count / [double]$procs.Count))
}
Write-Progress -Activity 'VIA Six Streams' -Completed

# ---- read tallies from logs (each tool's own [計] line is the truth) ----
$rows = foreach ($s in $streams) {
    $id = $s.Id; $rc = $done[$id]; $log = $procs[$id].Log
    $tail = ''; $tally = ''
    if (Test-Path -LiteralPath $log) {
        $lines = @(Get-Content -LiteralPath $log -Encoding UTF8)
        $tail = (($lines | Where-Object { $_.Trim() -ne '' } | Select-Object -Last 1) -as [string])
        # priority: a tool's own [計] line > a JSON top-level status > an 'overall' line > any pass/fail line
        foreach ($pat in @('\[計\]', '^\s*"status"\s*:', 'overall ', 'passed|FAIL \d')) {
            $t = ($lines | Where-Object { $_ -match $pat } | Select-Object -First 1) -as [string]
            if ($t) { $tally = $t.Trim(); break }
        }
    }
    $state = 'GREEN'
    if ($rc -eq -9) { $state = 'RED' } elseif ($rc -ne 0) { $state = 'YELLOW' }
    if ($tally -match 'FAIL [1-9]|failed": [1-9]|overall RED') { $state = 'YELLOW' }
    [pscustomobject]@{ Id=$id; Zh=$s.Zh; Rc=$rc; State=$state; Tally=$tally; Tail=$tail; Log=$log }
}

$overall = 'GREEN'
if (@($rows | Where-Object { $_.State -eq 'RED' }).Count) { $overall = 'RED' } elseif (@($rows | Where-Object { $_.State -eq 'YELLOW' }).Count) { $overall = 'YELLOW' }

function B { param($S) $c='gy'; if($S -eq 'GREEN'){$c='gr'}; if($S -eq 'YELLOW'){$c='ye'}; if($S -eq 'RED'){$c='rd'}; "<span class='b $c'>$S</span>" }
$esc = { param($t) [string]$t -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' }
$trs = ($rows | ForEach-Object { "<tr><td class='m'>$($_.Id)</td><td>$($_.Zh)</td><td class='c'>$(B $_.State)</td><td class='c m'>$($_.Rc)</td><td class='m'>$(& $esc $_.Tally)</td><td class='m dim'>$(& $esc $_.Tail)</td></tr>" }) -join ''
$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA SIX STREAMS — $($script:Stamp)</title>
<style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:16px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:17px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}
table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace}.dim{color:var(--mu)}
.b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}</style></head><body><div class="wrap">
<h1>VIA SIX STREAMS · ZERO-HYDRA MATRIX</h1><p class="sub">$($script:Stamp) · $(if($script:Apply){'APPLY'}else{'DRY-RUN'}) · $elapsed s · $Root</p>
<div class="kpis"><div class="kpi"><div class="n">$overall</div><div class="l">overall RYG</div></div><div class="kpi"><div class="n">$($rows.Count)</div><div class="l">streams</div></div><div class="kpi"><div class="n">$(@($rows|Where-Object{$_.State -eq 'GREEN'}).Count)</div><div class="l">green</div></div><div class="kpi"><div class="n">$(@($rows|Where-Object{$_.State -eq 'YELLOW'}).Count)</div><div class="l">yellow</div></div><div class="kpi"><div class="n">$(@($rows|Where-Object{$_.Rc -eq -9}).Count)</div><div class="l">timed out</div></div></div>
<table><colgroup><col style="width:5%"><col style="width:17%"><col style="width:8%"><col style="width:5%"><col style="width:30%"><col style="width:35%"></colgroup>
<thead><tr><th>ID</th><th>Stream</th><th>RYG</th><th>rc</th><th>Tally (tool's own [計] line)</th><th>Last line</th></tr></thead><tbody>$trs</tbody></table>
<div class="note">Zero-Hydra: every stream ran as an isolated child process with its own log and a $StreamTimeoutS s hard timeout. A timeout or crash in one stream cannot stall or alter another. Tallies are read verbatim from each tool's own selftest line, never recomputed here. Nothing was written into the mother tree$(if(-not $script:Apply){' (dry-run)'}else{' except through generators that keep .bak siblings and re-parse before writing'}). Logs: $runDir\logs</div>
</div></body></html>
"@
$rep = Join-Path $runDir ('reports\SIX_STREAMS_' + $script:Stamp + '.html')
[System.IO.File]::WriteAllText($rep, $html, $script:Utf8NoBom)
$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDir 'six_streams.json') -Encoding UTF8

Write-Host ''
Write-Host ('  overall ' + $overall + '  ·  ' + $rows.Count + ' streams  ·  ' + $elapsed + 's') -ForegroundColor Green
$rows | ForEach-Object { Write-Host ('  ' + $_.Id.PadRight(4) + $_.State.PadRight(7) + ' rc=' + $_.Rc + '  ' + $_.Zh + '   ' + $_.Tally) }
Write-Host ('  matrix  ' + $rep) -ForegroundColor DarkGray
Write-Host ''
if (-not $NoOpen) { try { Start-Process -FilePath $rep } catch { } }
