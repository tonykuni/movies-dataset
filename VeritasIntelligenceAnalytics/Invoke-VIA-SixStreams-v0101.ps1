#requires -Version 7.0
param(
    [string]$Root      = '',
    [string]$PythonExe = '',
    [string]$VenvPy    = '',
    [string]$OutRoot   = '',
    [string]$Unified   = '',
    [int]$StreamTimeoutS = 900,
    [int]$BeatSec = 5,
    [string]$GoToken   = '',
    [switch]$NoOpen
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

# =====================================================================
# Invoke-VIA-SixStreams-v0101   (批342 平行沙盒線 v0100 原件版前進;批342 Zero-Hydra 合流)
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
#   S1  代碼層 AST 修復       Unified engine Scan (PS AST)         S1b DeckServer 尾版自測
#   S2  SSOT / Regex 校準     MDL115 SSOTRegexDict selftest        S2b MDL116 尾版自測(門檻冊 SSOT)
#   S3  解耦 / 模組註冊       MDL122 IntakeRoster 尾版自測
#   S4  性能 / 死碼           DefTest audit (report only)
#   S5  沙盒回歸              VAP v025 bundled tests               S5b Unified Verify (pytest)
#   S6  UI Matrix / 部署      MDL116 尾版 regen (+ --open) and this matrix
#
# v0100→v0101(批342 合流;操作員令「加入二十個加速器 PY指令導入加入引擎 動態進度條」):
#   ①PS-ACCEL 20 加速器橋(每支 py 子流程自帶 ACCEL-BRIDGE=引擎側加速)
#   ②路徑動態解析(v0100 寫死 Downloads/C:\VIA/venv):-Root 預設本檔所在;python=PATH>C:\Python313>py;
#     venv 缺=退主 python;Unified-Accel20=倉根>intake>Downloads 尾版;DefTestAudit=Unified 同夾>
#     intake b245 工具鏈 bundle>Downloads;OutRoot=VIA_Reports\six_streams(gitignored)
#   ③缺件=誠實 SKIP(灰;rc -4;不算 RED/YELLOW;log 寫明缺什麼);零假綠
#   ④文字動態進度條每 BeatSec 秒一行([■■■□□□] 3/9 33% · 37s · running: S1 S4)=log 可讀
#     (Write-Progress 保留);每流 exit 即印
#   ⑤Write-Host 字串串接修正(v0100 'a' + $(...) 印成「a + …」)
#   tally 律不變:每流 [計] 行逐字取自各工具自測,本檔永不重算。
# =====================================================================

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'; $env:PYTHONUNBUFFERED = '1'
$script:StartedAt = Get-Date
$script:Stamp = $script:StartedAt.ToString('yyyyMMdd_HHmmss')
$script:Apply = ($GoToken -eq 'GO_v1')
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Log { param([string]$M, [string]$L = 'INFO')
    $c = 'Gray'; if ($L -eq 'OK') { $c = 'Green' }; if ($L -eq 'WARN') { $c = 'Yellow' }; if ($L -eq 'FAIL') { $c = 'Red' }; if ($L -eq 'S') { $c = 'Cyan' }; if ($L -eq 'SKIP') { $c = 'DarkGray' }
    Write-Host ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $M) -ForegroundColor $c }
function Bar { param([int]$Done, [int]$Total, [int]$W = 16)
    if ($Total -lt 1) { $Total = 1 }; $fill = [int][math]::Round($W * $Done / $Total)
    return ('[' + ('■' * $fill) + ('□' * ($W - $fill)) + '] ' + $Done + '/' + $Total + ' ' + [int](100 * $Done / $Total) + '%') }
function NewestIn { param([string]$Dir, [string]$Pat)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) { return '' }
    $h = @(Get-ChildItem -LiteralPath $Dir -Filter $Pat -File -ErrorAction SilentlyContinue | Sort-Object Name); if ($h.Count) { return $h[-1].FullName }; return '' }
function NewestDeep { param([string]$Dir, [string]$Pat)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) { return '' }
    $h = @(Get-ChildItem -LiteralPath $Dir -Filter $Pat -File -Recurse -ErrorAction SilentlyContinue | Sort-Object Name); if ($h.Count) { return $h[-1].FullName }; return '' }

# ---- 路徑動態解析(批342 v0101;零寫死;缺=誠實 SKIP)----
if (-not $Root) { $Root = $PSScriptRoot }
$reg = Join-Path $Root 'supportive modules\registry'
$intake = Join-Path $Root 'supportive modules\references\intake'
$dl = Join-Path $env:USERPROFILE 'Downloads'
if (-not $PythonExe) {
    $c = Get-Command python -ErrorAction SilentlyContinue
    if ($c) { $PythonExe = $c.Source } elseif (Test-Path 'C:\Python313\python.exe') { $PythonExe = 'C:\Python313\python.exe' } else { $PythonExe = 'py' } }
if (-not $VenvPy) { $VenvPy = Join-Path $env:USERPROFILE 'envs\via_vrn4\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $VenvPy)) { $VenvPy = $PythonExe }
if (-not $OutRoot) { $OutRoot = Join-Path $Root 'VIA_Reports\six_streams' }
if (-not $Unified) { $Unified = NewestIn $Root 'Invoke-VIA-Unified-Accel20-v*.ps1' }
if (-not $Unified) { $Unified = NewestDeep $intake 'Invoke-VIA-Unified-Accel20-v*.ps1' }
if (-not $Unified) { $Unified = NewestIn $dl 'Invoke-VIA-Unified-Accel20-v*.ps1' }
$defTest = ''
if ($Unified) { $defTest = NewestIn (Split-Path $Unified -Parent) 'VIA_DefTestAudit_v*.py' }
if (-not $defTest) { $defTest = NewestDeep (Join-Path $intake 'VIA_Toolchain_Bundle_20260830_b245') 'VIA_DefTestAudit_v*.py' }
if (-not $defTest) { $defTest = NewestIn $dl 'VIA_DefTestAudit_v*.py' }
$vap25 = Join-Path $Root 'functional modules\VAP\references\intake\VAP_v025_Complete_Package'
$vap25Test = Join-Path $vap25 'tests\run_all_tests_v025.py'

$runDir = Join-Path $OutRoot ('RUN_' + $script:Stamp)
foreach ($d in @($runDir, (Join-Path $runDir 'logs'), (Join-Path $runDir 'reports'))) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }
function Latest { param([string]$Pat) return (NewestIn $reg $Pat) }

Write-Host ''
Write-Host ('  VIA Six Streams  ·  Zero-Hydra  ·  ' + $(if ($script:Apply) { 'APPLY' } else { 'DRY-RUN' }) + '  ·  v0101(PS-ACCEL ' + $(if (Get-Variable -Name VIAPSAccelMod -ErrorAction SilentlyContinue) { if (Test-Path $VIAPSAccelMod) { 'ON' } else { 'OFF' } } else { 'OFF' }) + ')') -ForegroundColor White
Write-Host ('  root ' + $Root) -ForegroundColor DarkGray
Write-Host ('  python ' + $PythonExe + '  ·  venv ' + $VenvPy) -ForegroundColor DarkGray
Write-Host ('  unified ' + $(if ($Unified) { $Unified } else { '(缺;S1/S5b SKIP)' }) + '  ·  deftest ' + $(if ($defTest) { $defTest } else { '(缺;S4 SKIP)' })) -ForegroundColor DarkGray
Write-Host ('  out ' + $runDir) -ForegroundColor DarkGray
Write-Host ''

# ---- stream definitions: each is [id, zh, exe, args[], workdir, need(缺件=SKIP 理由)] ----
$goArg = @(); if ($script:Apply) { $goArg = @('-GoToken', 'GO_v1') }
$streams = @(
    @{ Id='S1'; Zh='代碼層 AST 修復';   Exe='pwsh';      Args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$Unified,'-Mode',$(if($script:Apply){'Repair'}else{'Scan'}),'-Root',$Root,'-OutRoot',(Join-Path $runDir 'S1_unified'),'-NoOpen','-RepairParseErrors') + $goArg; Wd=$Root; Need=$Unified; NeedZh='Invoke-VIA-Unified-Accel20-v*.ps1(倉根/intake/Downloads 皆缺)' },
    @{ Id='S1b'; Zh='DeckServer 尾版自測'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL095_DeckServer_v0*.py'),'--selftest'); Wd=$reg; Need=(Latest 'CGC_MDL095_DeckServer_v0*.py'); NeedZh='CGC_MDL095_DeckServer_v0*.py' },
    @{ Id='S2'; Zh='SSOT/Regex 字典自測'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL115_SSOTRegexDict_v0*.py'),'--selftest'); Wd=$reg; Need=(Latest 'CGC_MDL115_SSOTRegexDict_v0*.py'); NeedZh='CGC_MDL115_SSOTRegexDict_v0*.py' },
    @{ Id='S2b'; Zh='門檻冊 SSOT · MDL116 尾版自測'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL116_UnifiedShell_v0*.py'),'--selftest'); Wd=$reg; Need=(Latest 'CGC_MDL116_UnifiedShell_v0*.py'); NeedZh='CGC_MDL116_UnifiedShell_v0*.py' },
    @{ Id='S3'; Zh='上船件冊 註冊收容'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL122_IntakeRoster_v0*.py'),'--selftest'); Wd=$reg; Need=(Latest 'CGC_MDL122_IntakeRoster_v0*.py'); NeedZh='CGC_MDL122_IntakeRoster_v0*.py' },
    @{ Id='S4'; Zh='死碼/漂移 稽核(唯讀)'; Exe=$VenvPy; Args=@($defTest,'--root',$Root,'--out',(Join-Path $runDir 'S4_deftest')); Wd=$Root; Need=$defTest; NeedZh='VIA_DefTestAudit_v*.py(Unified 同夾/intake b245/Downloads 皆缺)' },
    @{ Id='S5'; Zh='VAP v025 套件回歸'; Exe=$PythonExe; Args=@($vap25Test); Wd=$vap25; Need=$(if (Test-Path -LiteralPath $vap25Test) { $vap25Test } else { '' }); NeedZh='VAP_v025_Complete_Package\tests\run_all_tests_v025.py(intake 包缺)' },
    @{ Id='S5b'; Zh='沙盒 pytest 回歸(Verify)'; Exe='pwsh'; Args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$Unified,'-Mode','Verify','-Root',$Root,'-PythonExe',$VenvPy,'-OutRoot',(Join-Path $runDir 'S5_verify'),'-NoOpen','-MaxTestFiles','25'); Wd=$Root; Need=$Unified; NeedZh='Invoke-VIA-Unified-Accel20-v*.ps1' },
    @{ Id='S6'; Zh='四殼再生 + 自動跳出'; Exe=$PythonExe; Args=@((Latest 'CGC_MDL116_UnifiedShell_v0*.py')) + $(if ($NoOpen) { @() } else { @('--open') }); Wd=$reg; Need=(Latest 'CGC_MDL116_UnifiedShell_v0*.py'); NeedZh='CGC_MDL116_UnifiedShell_v0*.py' }
)

# ---- launch all concurrently; file-redirected; no pipes; 缺件=SKIP ----
$procs = [ordered]@{}
foreach ($s in $streams) {
    $log = Join-Path $runDir ('logs\' + $s.Id + '.log')
    if (-not $s.Need) {
        [System.IO.File]::WriteAllText($log, ('SKIP: 缺件 ' + $s.NeedZh + "`r`n"), $script:Utf8NoBom)
        $procs[$s.Id] = @{ P=$null; Log=$log; Def=$s; Skipped=$true }
        Write-Log ($s.Id.PadRight(4) + ' SKIP      缺件 ' + $s.NeedZh) 'SKIP'
        continue
    }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $s.Exe; $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8; $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $psi.WorkingDirectory = $s.Wd
    $psi.Environment['PYTHONIOENCODING'] = 'utf-8'; $psi.Environment['PYTHONUTF8'] = '1'; $psi.Environment['PYTHONUNBUFFERED'] = '1'
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

# ---- poll with progress; hard timeout per stream; 文字進度條心跳(批342 v0101)----
$done = @{}
$lastBeat = Get-Date
$spin = '◐◓◑◒'; $beatN = 0
while ($done.Count -lt $procs.Count) {
    Start-Sleep -Milliseconds 700
    foreach ($id in @($procs.Keys)) {
        if ($done.ContainsKey($id)) { continue }
        $e = $procs[$id]
        if ($e.Skipped) { $done[$id] = -4; continue }
        if ($e.Failed) { $done[$id] = -3; continue }
        $el = ((Get-Date) - $e.T0).TotalSeconds
        if ($e.P.HasExited) {
            $e.P.WaitForExit()
            try { $e.W.Write($e.Out.GetAwaiter().GetResult()); $e.W.Write($e.Err.GetAwaiter().GetResult()) } catch { }
            $e.W.Close(); $done[$id] = $e.P.ExitCode
            Write-Log ($id.PadRight(4) + ' exit ' + $e.P.ExitCode + '  ' + [int]$el + 's  ' + $e.Def.Zh + '  ' + (Bar $done.Count $procs.Count)) $(if ($e.P.ExitCode -eq 0) { 'OK' } else { 'WARN' })
        } elseif ($el -ge $StreamTimeoutS) {
            try { $e.P.Kill($true) } catch { }
            try { $e.W.WriteLine('TIMEOUT ' + $StreamTimeoutS + 's (killed; other streams unaffected)') } catch { }
            $e.W.Close(); $done[$id] = -9
            Write-Log ($id.PadRight(4) + ' TIMEOUT ' + $StreamTimeoutS + 's  ' + $e.Def.Zh) 'FAIL'
        }
    }
    $running = @($procs.Keys | Where-Object { -not $done.ContainsKey($_) })
    Write-Progress -Activity 'VIA Six Streams' -Status ('running: ' + ($running -join ' ')) -PercentComplete ([int](100 * $done.Count / [double]$procs.Count))
    if ($running.Count -and ((Get-Date) - $lastBeat).TotalSeconds -ge [math]::Max(1, $BeatSec)) {
        $lastBeat = Get-Date; $beatN++
        $elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
        Write-Host ('  ' + $spin[$beatN % 4] + ' ' + (Bar $done.Count $procs.Count) + ' · ' + $elapsed + 's · running: ' + ($running -join ' ')) -ForegroundColor DarkCyan
    }
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
    if ($rc -eq -4) { $state = 'SKIP' } elseif ($rc -eq -9) { $state = 'RED' } elseif ($rc -ne 0) { $state = 'YELLOW' }
    if ($state -ne 'SKIP' -and $tally -match 'FAIL [1-9]|failed": [1-9]|overall RED') { $state = 'YELLOW' }
    [pscustomobject]@{ Id=$id; Zh=$s.Zh; Rc=$rc; State=$state; Tally=$tally; Tail=$tail; Log=$log }
}

$overall = 'GREEN'
if (@($rows | Where-Object { $_.State -eq 'RED' }).Count) { $overall = 'RED' } elseif (@($rows | Where-Object { $_.State -eq 'YELLOW' }).Count) { $overall = 'YELLOW' }
$nSkip = @($rows | Where-Object { $_.State -eq 'SKIP' }).Count

function B { param($S) $c='gy'; if($S -eq 'GREEN'){$c='gr'}; if($S -eq 'YELLOW'){$c='ye'}; if($S -eq 'RED'){$c='rd'}; "<span class='b $c'>$S</span>" }
$esc = { param($t) [string]$t -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' }
$trs = ($rows | ForEach-Object { "<tr><td class='m'>$($_.Id)</td><td>$($_.Zh)</td><td class='c'>$(B $_.State)</td><td class='c m'>$($_.Rc)</td><td class='m'>$(& $esc $_.Tally)</td><td class='m dim'>$(& $esc $_.Tail)</td></tr>" }) -join ''
$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,"><title>VIA SIX STREAMS — $($script:Stamp)</title>
<style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:16px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:17px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}
table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace}.dim{color:var(--mu)}
.b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}</style></head><body><div class="wrap">
<h1>VIA SIX STREAMS · ZERO-HYDRA MATRIX</h1><p class="sub">$($script:Stamp) · $(if($script:Apply){'APPLY'}else{'DRY-RUN'}) · $elapsed s · $Root · v0101</p>
<div class="kpis"><div class="kpi"><div class="n">$overall</div><div class="l">overall RYG</div></div><div class="kpi"><div class="n">$($rows.Count)</div><div class="l">streams</div></div><div class="kpi"><div class="n">$(@($rows|Where-Object{$_.State -eq 'GREEN'}).Count)</div><div class="l">green</div></div><div class="kpi"><div class="n">$(@($rows|Where-Object{$_.State -eq 'YELLOW'}).Count)</div><div class="l">yellow</div></div><div class="kpi"><div class="n">$nSkip</div><div class="l">skipped (缺件·誠實)</div></div><div class="kpi"><div class="n">$(@($rows|Where-Object{$_.Rc -eq -9}).Count)</div><div class="l">timed out</div></div></div>
<table><colgroup><col style="width:5%"><col style="width:17%"><col style="width:8%"><col style="width:5%"><col style="width:30%"><col style="width:35%"></colgroup>
<thead><tr><th>ID</th><th>Stream</th><th>RYG</th><th>rc</th><th>Tally (tool's own [計] line)</th><th>Last line</th></tr></thead><tbody>$trs</tbody></table>
<div class="note">Zero-Hydra: every stream ran as an isolated child process with its own log and a $StreamTimeoutS s hard timeout. A timeout or crash in one stream cannot stall or alter another. Tallies are read verbatim from each tool's own selftest line, never recomputed here. SKIP = required file missing on this machine (rc -4; never counted as green). Nothing was written into the mother tree$(if(-not $script:Apply){' (dry-run)'}else{' except through generators that keep .bak siblings and re-parse before writing'}). Logs: $runDir\logs</div>
</div></body></html>
"@
$rep = Join-Path $runDir ('reports\SIX_STREAMS_' + $script:Stamp + '.html')
[System.IO.File]::WriteAllText($rep, $html, $script:Utf8NoBom)
try { [System.IO.File]::WriteAllText((Join-Path $OutRoot 'SIX_STREAMS_LATEST.html'), $html, $script:Utf8NoBom) } catch { }
$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDir 'six_streams.json') -Encoding UTF8

Write-Host ''
Write-Host ('  overall ' + $overall + '  ·  ' + $rows.Count + ' streams  ·  skip ' + $nSkip + '  ·  ' + $elapsed + 's  ·  ' + (Bar $rows.Count $rows.Count)) -ForegroundColor Green
$rows | ForEach-Object { Write-Host ('  ' + $_.Id.PadRight(4) + $_.State.PadRight(7) + ' rc=' + $_.Rc + '  ' + $_.Zh + '   ' + $_.Tally) }
Write-Host ('  matrix  ' + $rep) -ForegroundColor DarkGray
Write-Host ''
if (-not $NoOpen) { try { Start-Process -FilePath $rep } catch { } }
