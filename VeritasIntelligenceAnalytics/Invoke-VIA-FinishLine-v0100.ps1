#Requires -Version 7.0
<#
=============================================================================
Invoke-VIA-FinishLine-v0100 — 唯一文件夾整併收官統包器(TOOL-094,批89)
=============================================================================
操作員令:「INTEGRATE ALL INTO ONE POWERSHELL CODE TO HANDLE ALL AND THE
REMAINING PROCESSES」。

殘局(工作站實證):本地歷史裡卡著含 194MB/128MB 回滾快照的 commit
(reset --soft 那步未生效+pull 又疊 merge),雙推連撞 GH001。本器一次
收官(冪等,怎麼亂都能壓平):
  F1 前檢(PATH 錨定新正典 bin/py 解析/加速器)
  F2 fetch origin main(退避重試)
  F3 壓平:git reset --soft origin/main(本地歷史重寫為「遠端最新+
     一顆乾淨 commit」;工作樹零觸碰=檔案全保全)
  F4 卸載不入 git 者(留本地):gitignore 命中(含回滾快照夾)+
     >95MB 超大檔,逐批 restore --staged
  F5 commit(標準尾標;無 staged=誠實 SKIP)
  F6 pull --no-rebase 對齊遠端
  F7 雙推 main+claude(退避 2/4/8/16s)
  F8 復驗:battery 看門狗+自動摘印最新 GRID 之 FAIL 列
  F9 誠實三態總結矩陣+JSON 存證
用法(單行全自動;-Plan=唯讀演練不動 git):
  pwsh -NoProfile -ExecutionPolicy Bypass -File Invoke-VIA-FinishLine-v0100.ps1
=============================================================================
#>
param(
    [string]$NewRepo = 'C:\Users\tonyk\Downloads\movies-dataset',
    [int]$BatteryTimeoutSec = 1800,
    [switch]$SkipBattery,
    [switch]$Plan
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'
$NewVia = Join-Path $NewRepo 'VeritasIntelligenceAnalytics'
$Ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
$EvDir = Join-Path $NewVia 'VIA_Reports\unify_runs'
$null = New-Item -ItemType Directory -Force -Path $EvDir
$Steps = [System.Collections.Generic.List[object]]::new()

function Write-Line { param([string]$Level, [string]$Msg)
    $c = switch ($Level) { 'OK' {'Green'} 'FAIL' {'Red'} 'WARN' {'Yellow'} 'RUN' {'Cyan'} 'SKIP' {'DarkYellow'} default {'Gray'} }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [$Level] $Msg" -ForegroundColor $c
}
function Add-Step { param([string]$Name, [string]$State, [string]$Note = '')
    $Steps.Add([pscustomobject]@{ step = $Name; state = $State; note = $Note })
    Write-Line $State "$Name $Note"
}
function Invoke-Guarded { param([string]$Name, [string]$Exe, [string[]]$CmdArgs, [int]$TimeoutSec = 900)
    $argStr = ($CmdArgs | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
    Write-Line 'RUN' $Name
    $p = Start-Process -FilePath $Exe -ArgumentList $argStr -NoNewWindow -PassThru -WorkingDirectory $NewRepo
    $t0 = Get-Date
    while (-not $p.HasExited) {
        $el = [int]((Get-Date) - $t0).TotalSeconds
        if ($el -ge $TimeoutSec) { try { $p.Kill($true) } catch {}; Write-Line 'FAIL' "$Name 逾時截停"; return 124 }
        Write-Progress -Id 9 -Activity '收官統包器(動態進度)' -Status "$Name · $el s / $TimeoutSec s" `
            -PercentComplete ([Math]::Min(99, [int](100 * $el / $TimeoutSec)))
        Start-Sleep -Milliseconds 800
    }
    Write-Progress -Id 9 -Activity '收官統包器(動態進度)' -Completed
    return $p.ExitCode
}
function Invoke-GitRetry { param([string]$Name, [string[]]$GitArgs, [int]$TimeoutSec = 900)
    foreach ($d in @(0, 2, 4, 8, 16)) {
        if ($d) { Write-Line 'WARN' "$Name 重試前等待 $d s…"; Start-Sleep -Seconds $d }
        $rc = Invoke-Guarded $Name 'git' (@('-C', $NewRepo) + $GitArgs) $TimeoutSec
        if ($rc -eq 0) { return 0 }
    }
    return 1
}

Write-Host ''
Write-Host '================================================================================' -ForegroundColor Cyan
Write-Host "VIA 收官統包器 v0100 · TOOL-094(批89)$(if($Plan){' · Plan 唯讀演練'})" -ForegroundColor Cyan
Write-Host '================================================================================' -ForegroundColor Cyan
Start-Transcript -Path (Join-Path $EvDir "FINISH_$Ts.log") -Append | Out-Null

# F1 前檢
$env:Path = (Join-Path $NewVia 'bin') + ';' + $env:Path
git -C $NewRepo config core.longpaths true
Add-Step 'F1 前檢' 'OK' "PATH 錨定新正典 bin · longpaths=true"

# F2 fetch
$rc = Invoke-GitRetry 'F2 git fetch origin main' @('fetch', 'origin', 'main')
Add-Step 'F2 fetch' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc"

# F3 壓平(冪等:HEAD==origin/main 則 SKIP)
$head = (git -C $NewRepo rev-parse HEAD).Trim()
$remote = (git -C $NewRepo rev-parse origin/main).Trim()
if ($Plan) {
    Add-Step 'F3 壓平' 'SKIP' 'Plan 唯讀'
} elseif ($head -eq $remote) {
    Add-Step 'F3 壓平' 'SKIP' "HEAD 已在 origin/main($($remote.Substring(0,8)))"
} else {
    $rc = Invoke-Guarded 'F3 git reset --soft origin/main' 'git' @('-C', $NewRepo, 'reset', '--soft', 'origin/main') 300
    Add-Step 'F3 壓平' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "本地歷史壓平至 $($remote.Substring(0,8))(工作樹零觸碰)"
}

# F4 卸載:gitignore 命中+>95MB(全部留本地)
if ($Plan) {
    Add-Step 'F4 卸載' 'SKIP' 'Plan'
} else {
    $staged = @(git -C $NewRepo diff --cached --name-only)
    if ($staged.Count -eq 0) {
        Add-Step 'F4 卸載' 'SKIP' '無 staged 項'
    } else {
        $tmpAll = Join-Path $EvDir "FINISH_${Ts}_staged.txt"
        [System.IO.File]::WriteAllLines($tmpAll, $staged)
        $ignored = [System.Collections.Generic.HashSet[string]]::new()
        (Get-Content -LiteralPath $tmpAll | git -C $NewRepo check-ignore --stdin --no-index) |
            ForEach-Object { $null = $ignored.Add($_) }
        $big = @($staged | Where-Object {
                $fp = Join-Path $NewRepo $_
                (Test-Path -LiteralPath $fp) -and ((Get-Item -LiteralPath $fp).Length -gt 95MB)
            })
        $drop = [System.Collections.Generic.HashSet[string]]::new($ignored)
        foreach ($b in $big) { $null = $drop.Add($b) }
        if ($drop.Count -gt 0) {
            $tmpDrop = Join-Path $EvDir "FINISH_${Ts}_drop.txt"
            [System.IO.File]::WriteAllLines($tmpDrop, $drop)
            $rc = Invoke-Guarded 'F4 restore --staged(卸載清單)' 'git' @('-C', $NewRepo, 'restore', '--staged', "--pathspec-from-file=$tmpDrop") 600
            Add-Step 'F4 卸載' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "staged $($staged.Count) → 卸 gitignore $($ignored.Count)+超大 $($big.Count)(檔留本地)"
        } else {
            Add-Step 'F4 卸載' 'OK' "staged $($staged.Count) · 無須卸載"
        }
    }
}

# F5 commit
if ($Plan) { Add-Step 'F5 commit' 'SKIP' 'Plan' }
else {
    git -C $NewRepo diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        $msgFile = Join-Path $EvDir "FINISH_${Ts}_msg.txt"
        @('批89 收官:唯一文件夾整併抓回定版(回滾快照/超大檔留本地不入 git)', '',
          'Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>',
          'Claude-Session: https://claude.ai/code/session_01R2d69oa1AGvnPVwjSUdSv5'
        ) | Set-Content -LiteralPath $msgFile -Encoding UTF8
        $rc = Invoke-Guarded 'F5 git commit' 'git' @('-C', $NewRepo, 'commit', '-F', $msgFile) 300
        Add-Step 'F5 commit' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc"
    } else { Add-Step 'F5 commit' 'SKIP' '無 staged 變更(可能已乾淨)' }
}

# F6 對齊+F7 雙推
if ($Plan) { Add-Step 'F6 對齊' 'SKIP' 'Plan'; Add-Step 'F7 雙推' 'SKIP' 'Plan' }
else {
    $rc = Invoke-GitRetry 'F6 git pull origin main --no-rebase' @('pull', 'origin', 'main', '--no-rebase')
    Add-Step 'F6 對齊' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc"
    $rc1 = Invoke-GitRetry 'F7a push main' @('push', 'origin', 'HEAD:main')
    $rc2 = Invoke-GitRetry 'F7b push claude 分支' @('push', '-u', 'origin', 'HEAD:claude/via-system-followup-tz7k9t')
    Add-Step 'F7 雙推' ($(if ($rc1 -eq 0 -and $rc2 -eq 0) { 'OK' } else { 'FAIL' })) "main rc=$rc1 · claude rc=$rc2"
}

# F8 復驗+GRID FAIL 摘印
if ($Plan -or $SkipBattery) { Add-Step 'F8 復驗' 'SKIP' $(if ($Plan) { 'Plan' } else { '-SkipBattery' }) }
else {
    $bin = Join-Path $NewVia 'bin'
    $rc = Invoke-Guarded 'F8 via-run via-wrapup --battery' 'cmd.exe' @('/c', (Join-Path $bin 'via-run.cmd'), 'via-wrapup', '--battery') $BatteryTimeoutSec
    $gridNote = ''
    $gj = Get-ChildItem -LiteralPath (Join-Path $NewVia 'VIA_Reports\selftest_runs') -Filter 'GRID_*.json' -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($gj) {
        $gd = Get-Content -LiteralPath $gj.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $failsG = @($gd.results | Where-Object { $_.state -eq 'FAIL' })
        $gridNote = "$($gj.Name):FAIL $($failsG.Count)"
        foreach ($f in $failsG) { Write-Line 'FAIL' "GRID 紅站:$($f.name) · $($f.note)" }
    }
    Add-Step 'F8 復驗' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "battery rc=$rc · $gridNote"
}

# F9 總結
Write-Host ''
Write-Host '=== 收官統包器 · 總結矩陣(誠實三態)===' -ForegroundColor Cyan
$Steps | Format-Table -AutoSize | Out-String | Write-Host
$ok = @($Steps | Where-Object state -eq 'OK').Count
$fail = @($Steps | Where-Object state -eq 'FAIL').Count
$skip = @($Steps | Where-Object state -eq 'SKIP').Count
[pscustomobject]@{ schema = 'VIA.FinishLine.v1'; ts = $Ts; plan = [bool]$Plan; steps = $Steps
    ok = $ok; fail = $fail; skip = $skip } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $EvDir "FINISH_$Ts.json") -Encoding UTF8
Write-Line ($(if ($fail -eq 0) { 'OK' } else { 'FAIL' })) "OK $ok · FAIL $fail · SKIP $skip · 存證 VIA_Reports\unify_runs\FINISH_$Ts.json"
Stop-Transcript | Out-Null
exit $(if ($fail -eq 0) { 0 } else { 1 })
