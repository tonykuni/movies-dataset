#requires -Version 7.0
<#
.SYNOPSIS
    VIA · ONE POWERSHELL TO HANDLE ALL(加速器版:不卡頓動態進度條)

.DESCRIPTION
    單一入口統包四段驗收,體現 KEY PROMPT 加速器:
      A16 動態進度條:前景 150ms 更新;背景行程做事,長段(GroupIndex)
          直接解析其 log 的 def [NN%] 取得「真實」進度,非假動畫
      A17 動態說明:進度條右側滾動顯示該段 log 最新一行
      A18 非阻塞:每段 Start-Process 背景執行,前景永不阻塞、結尾零 Read-Host

    段序:
      [1] GIT-SYNC       拉最新分支(evidence 先還原)
      [2] SUBSYSTEMS     VAP/VDF/VRN 使用者測試 + 主控台重建(5 情境)
      [3] VRN-CROSSCHECK 多路交叉驗證機制 selftest(4 情境)
      [4] GROUPINDEX     全套件 OneClick(八道閘;-SkipSuite 1 可略)
      [5] MATRIX         彙整全部 gate 輸出紅綠矩陣

.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File .\Invoke-VIA-All-v0100.ps1
#>
[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [int]$SyncRepo = 1,
    [int]$SkipSuite = 0,
    [int]$OpenHtml = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ViaRoot = $PSScriptRoot
$RepoRoot = Split-Path $ViaRoot -Parent
$Branch = "claude/via-group-classification-index-5h274b"
$LogDir = Join-Path $ViaRoot "VIA_Reports\RUN_MASTER_LOGS"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

# via_ 環境自動解析(NexusCore 候選契約)
if ($PythonExe -eq "python") {
    foreach ($cand in @(
            (Join-Path $env:USERPROFILE "envs\via_core_313\Scripts\python.exe"),
            (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe"))) {
        if (Test-Path -LiteralPath $cand) { $PythonExe = $cand; break }
    }
}

$SubsysDir = Join-Path $ViaRoot "functional modules\SubsystemsConsole"
$VrnHarness = Join-Path $ViaRoot "functional modules\VRN\VIA_VRN_CrossCheck_Harness_v0100.py"
$OneClick = Join-Path $ViaRoot "functional modules\GroupIndex\engine\Invoke-VIA-GroupIndex-Suite-OneClick-v0100.ps1"

# ---------------------------------------------------------------- A16 進度條
$SpinFrames = @("|", "/", "-", "\")
$script:SpinI = 0
function def_Bar {
    param([int]$Pct, [string]$Msg)
    if ($Pct -lt 0) { $Pct = 0 } elseif ($Pct -gt 100) { $Pct = 100 }
    $filled = [Math]::Floor($Pct * 40 / 100)
    $bar = ("█" * $filled) + ("░" * (40 - $filled))
    if ($Msg.Length -gt 58) { $Msg = $Msg.Substring(0, 58) }
    $line = ("`r{0} [{1}] {2,3}%  {3}" -f $SpinFrames[$script:SpinI % 4], $bar, $Pct, $Msg)
    $script:SpinI++
    Write-Host ($line.PadRight(118)) -NoNewline
}
function def_BarDone {
    param([int]$Pct, [string]$Msg, [bool]$Ok = $true)
    $filled = [Math]::Floor($Pct * 40 / 100)
    $bar = ("█" * $filled) + ("░" * (40 - $filled))
    $mark = if ($Ok) { "✓" } else { "✗" }
    Write-Host (("`r{0} [{1}] {2,3}%  {3}" -f $mark, $bar, $Pct, $Msg).PadRight(118)) `
        -ForegroundColor ($Ok ? "Green" : "Red")
}

# ------------------------------------------------- A18 非阻塞段執行 + A17 說明
function def_RunStage {
    param(
        [string]$Name, [string]$Exe, [string]$ArgString, [string]$WorkDir,
        [int]$PctFrom, [int]$PctTo,
        [int]$EstSeconds = 60,          # 無真實進度來源時的推進節奏
        [bool]$ParseDefPct = $false     # 解析 log 內 def [NN%](GroupIndex 段)
    )
    $out = Join-Path $LogDir ("{0}_{1}.out.log" -f $Stamp, $Name)
    $err = Join-Path $LogDir ("{0}_{1}.err.log" -f $Stamp, $Name)
    $p = Start-Process -FilePath $Exe -ArgumentList $ArgString `
        -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $t0 = Get-Date
    while (-not $p.HasExited) {
        $pct = $PctFrom
        $msg = $Name
        $tail = @()
        if (Test-Path -LiteralPath $out) {
            $tail = @(Get-Content -LiteralPath $out -Tail 25 -ErrorAction SilentlyContinue)
        }
        if ($ParseDefPct -and $tail.Count -gt 0) {
            $hits = @($tail | Select-String -Pattern 'def \[\s*(\d+)%\]')
            if ($hits.Count -gt 0) {
                $inner = [int]$hits[-1].Matches[0].Groups[1].Value
                $pct = $PctFrom + [int](($PctTo - $PctFrom) * $inner / 100.0)
            }
        }
        else {
            $elapsed = ((Get-Date) - $t0).TotalSeconds
            $pct = $PctFrom + [int](($PctTo - $PctFrom - 1) * [Math]::Min(1.0, $elapsed / $EstSeconds))
        }
        $lastLine = @($tail | Where-Object { $_ -match '\S' })
        if ($lastLine.Count -gt 0) { $msg = ($lastLine[-1] -replace '\s+', ' ').Trim() }
        def_Bar -Pct $pct -Msg $msg
        Start-Sleep -Milliseconds 150
    }
    $ok = ($p.ExitCode -eq 0)
    def_BarDone -Pct $PctTo -Msg ("{0} 完成(exit {1})· log: {2}" -f $Name, $p.ExitCode, (Split-Path $out -Leaf)) -Ok $ok
    return $p.ExitCode
}

# ---------------------------------------------------------------- 主流程
Write-Host ""
Write-Host "VIA · ONE POWERSHELL TO HANDLE ALL · v0100(A16 進度條/A17 說明/A18 非阻塞)" -ForegroundColor Cyan
Write-Host ("Python: {0}" -f $PythonExe) -ForegroundColor DarkGray
Write-Host ""

$results = [ordered]@{}

# [1] GIT-SYNC(快,前景執行 + 條列動畫)
if ($SyncRepo -eq 1 -and (Get-Command git -ErrorAction SilentlyContinue) -and
        (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
    def_Bar -Pct 1 -Msg "GIT-SYNC evidence 還原"
    git -C $RepoRoot restore -- "VeritasIntelligenceAnalytics/functional modules/GroupIndex/evidence" 2>$null
    git -C $RepoRoot restore -- "VeritasIntelligenceAnalytics/functional modules/SubsystemsConsole/evidence" 2>$null
    def_Bar -Pct 3 -Msg "GIT-SYNC fetch/pull $Branch"
    git -C $RepoRoot fetch origin $Branch 2>&1 | Out-Null
    git -C $RepoRoot checkout $Branch 2>&1 | Out-Null
    git -C $RepoRoot pull origin $Branch 2>&1 | Out-Null
    $results["GIT-SYNC"] = 0
    def_BarDone -Pct 5 -Msg "GIT-SYNC 已同步(本 launcher 若被更新,下次執行生效)"
}
else {
    $results["GIT-SYNC"] = 0
    def_BarDone -Pct 5 -Msg "GIT-SYNC 略過"
}

# [2] SUBSYSTEMS USER-TEST + 主控台重建
$results["SUBSYSTEMS"] = def_RunStage -Name "SUBSYSTEMS" -Exe $PythonExe `
    -ArgString ('"{0}"' -f (Join-Path $SubsysDir "VIA_Subsystems_UserTest_v0100.py")) `
    -WorkDir $SubsysDir -PctFrom 5 -PctTo 30 -EstSeconds 120
if ($results["SUBSYSTEMS"] -eq 0) {
    $null = def_RunStage -Name "CONSOLE-BUILD" -Exe $PythonExe `
        -ArgString ('"{0}"' -f (Join-Path $SubsysDir "VIA_Subsystems_Console_Builder_v0100.py")) `
        -WorkDir $SubsysDir -PctFrom 30 -PctTo 34 -EstSeconds 30
}

# [3] VRN 交叉驗證機制
$results["VRN-CROSSCHECK"] = def_RunStage -Name "VRN-CROSSCHECK" -Exe $PythonExe `
    -ArgString ('"{0}" --selftest' -f $VrnHarness) `
    -WorkDir (Split-Path $VrnHarness -Parent) -PctFrom 34 -PctTo 40 -EstSeconds 20

# [4] GROUPINDEX 全套件(真實進度:解析其 def [NN%])
if ($SkipSuite -ne 1) {
    $suiteArgs = ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -SyncRepo 0 -EnforceEnv 1 ' +
                  '-SkipEngines 0 -OpenHtml {1} -KeepOpen 0') -f $OneClick, $OpenHtml
    $results["GROUPINDEX"] = def_RunStage -Name "GROUPINDEX" -Exe "pwsh" `
        -ArgString $suiteArgs -WorkDir (Split-Path $OneClick -Parent) `
        -PctFrom 40 -PctTo 97 -ParseDefPct $true
}
else {
    $results["GROUPINDEX"] = 0
    def_BarDone -Pct 97 -Msg "GROUPINDEX 略過(-SkipSuite 1)"
}

# [5] MATRIX 彙整
def_Bar -Pct 98 -Msg "MATRIX 彙整各 gate"
$gates = @(
    @{ N = "Subsystems USER-TEST"; J = Join-Path $SubsysDir "evidence\RUN_SUBSYSTEMS_USERTEST_V0100\usertest_summary.json"; F = "Status"; E = "SUBSYSTEMS_USERTEST_PASS" },
    @{ N = "SectorFlow";  J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_SECTORFLOW_V0100\run_summary.json"; F = "FinalGate"; E = "CONTROLLED_ACTIVATION_PASS" },
    @{ N = "TradeBT";     J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_SECTORFLOW_TRADE_V0100\trade_run_summary.json"; F = "Status"; E = "TRADE_BACKTEST_PASS" },
    @{ N = "LiveWire";    J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_LIVEWIRE_ADAPTER_V0100\adapter_run_summary.json"; F = "Status"; E = "ADAPTER_VERIFIED_FAIL_CLOSED" },
    @{ N = "ETFConsoles"; J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_ETF_CONSOLES_V0100\etf_consoles_summary.json"; F = "Status"; E = "ETF_CONSOLES_PASS" },
    @{ N = "ChipWarRev";  J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_CHIPWAR_REVENUE_V0100\chipwar_revenue_summary.json"; F = "Status"; E = "CHIPWAR_REVENUE_PASS" },
    @{ N = "Accel20";     J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_ACCEL20_V0100\accel20_summary.json"; F = "Status"; E = "ACCEL20_GOVERNANCE_PASS" },
    @{ N = "VISAdaptive"; J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_VIS_ADAPTIVE_V0100\vis_run_summary.json"; F = "Status"; E = "VIS_ADAPTIVE_PASS" },
    @{ N = "MasterSuite"; J = Join-Path $ViaRoot "functional modules\GroupIndex\evidence\RUN_MASTER_VALIDATION_V0100\master_run_summary.json"; F = "Status"; E = "CONTROLLED_SUITE_ACTIVATION_PASS" }
)
def_BarDone -Pct 100 -Msg "全段完成 — 結果矩陣如下"
Write-Host ""
Write-Host ("{0,-22} {1,-48} {2}" -f "GATE", "VALUE", "VERDICT") -ForegroundColor White
$blocked = @()
if ($results["VRN-CROSSCHECK"] -eq 0) {
    Write-Host ("{0,-22} {1,-48} {2}" -f "VRN-CrossCheck 機制", "MECHANISM_VERIFIED(4 情境)", "PASS") -ForegroundColor Green
}
else {
    Write-Host ("{0,-22} {1,-48} {2}" -f "VRN-CrossCheck 機制", ("selftest exit " + $results["VRN-CROSSCHECK"]), "BLOCKED") -ForegroundColor Red
    $blocked += "VRN-CrossCheck"
}
foreach ($g in $gates) {
    if (Test-Path -LiteralPath $g.J) {
        $v = [string](Get-Content -LiteralPath $g.J -Raw | ConvertFrom-Json).($g.F)
        $ok = $v.StartsWith($g.E)
        Write-Host ("{0,-22} {1,-48} {2}" -f $g.N, $v, ($ok ? "PASS" : "BLOCKED")) `
            -ForegroundColor ($ok ? "Green" : "Red")
        if (-not $ok) { $blocked += $g.N }
    }
    else {
        Write-Host ("{0,-22} {1,-48} {2}" -f $g.N, "(evidence 未生成)", "MISSING") -ForegroundColor Yellow
        $blocked += $g.N
    }
}
Write-Host ""
Write-Host ("Logs: {0}" -f $LogDir) -ForegroundColor DarkGray
if ($blocked.Count -eq 0) {
    Write-Host "ALL GREEN — 全部 gate 通過" -ForegroundColor Green
    exit 0
}
Write-Host ("BLOCKED: {0}" -f ($blocked -join ", ")) -ForegroundColor Red
exit 1
