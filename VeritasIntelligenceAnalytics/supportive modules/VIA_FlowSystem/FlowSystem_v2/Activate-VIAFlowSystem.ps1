#requires -Version 7.0
param(
    [string]$Cmd = "all",
    [string]$PythonExe = "",
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

# VDF-FLOW-LAUNCHER-16  Activate-VIAFlowSystem.ps1
# One launcher: activates env, runs PY back-end (synth->calibrate->run->ui),
# syncs the front-end index.html and opens it.
# LL-compliant: param() first; line comments only; full cmdlet names;
# ProcessStartInfo + ArgumentList.Add per-arg + async drain (no 64KB deadlock);
# Start-Process only to open the HTML report; no Start-Job/Read-Host/exit in main.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# v0100R fix: wrapper 委派可能傳入空字串 -Cmd — 空值一律回預設 all(實機 via-wf flowsystem 爆出)
if (-not $Cmd) { $Cmd = "all" }

$script:Root    = $PSScriptRoot
$script:Manager = Join-Path $script:Root "engines/FLOW_ENG009_FlowManager.py"
$script:Report  = Join-Path $script:Root "index.html"
$script:WorldMap = Join-Path $script:Root "world_flow.html"
$script:TierMap  = Join-Path $script:Root "tier_flow.html"
$script:MapSim   = Join-Path $script:Root "global_map_sim.html"
$script:PerfTrend= Join-Path $script:Root "perf_trend.html"
$script:Monitor  = Join-Path $script:Root "flow_monitor.html"
$script:Hub     = Join-Path $script:Root "flow_hub.html"
$script:Calib   = Join-Path $script:Root "data/output/calibration.json"

function Resolve-PythonExe {
    param([string]$Override)
    if ($Override -and (Test-Path $Override)) { return $Override }
    # Auto-Locator: probe known VIA venvs, then py launcher, then PATH python
    $candidates = @(
        "C:\Users\tonyk\envs\via_plot_basic\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_ds_light\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
        "C:\Users\tonyk\envs\venv_core\Scripts\python.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    $py = Get-Command "py" -ErrorAction SilentlyContinue
    if ($py) { return "py" }
    return "python"
}

function Invoke-PyDrained {
    param([string]$Exe, [string[]]$PyArgs, [string]$WorkDir)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = $Exe
    $psi.WorkingDirectory = $WorkDir
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    foreach ($a in $PyArgs) { $psi.ArgumentList.Add($a) }

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    # async drain BOTH streams to avoid the 64KB pipe-buffer deadlock
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $proc.WaitForExit()
    [System.Threading.Tasks.Task]::WaitAll(@($outTask, $errTask))
    return [pscustomobject]@{
        Code   = $proc.ExitCode
        StdOut = $outTask.Result
        StdErr = $errTask.Result
    }
}

Write-Host ("=== VIA-FlowSystem launcher  ·  cmd={0} ===" -f $Cmd) -ForegroundColor Cyan

$script:PyExe = Resolve-PythonExe -Override $PythonExe
Write-Host ("[env] python: {0}" -f $script:PyExe)

if (-not (Test-Path $script:Manager)) {
    Write-Host ("[fatal] manager not found: {0}" -f $script:Manager) -ForegroundColor Red
    return
}

# --- back-end ---
$run = Invoke-PyDrained -Exe $script:PyExe -PyArgs @($script:Manager, $Cmd) -WorkDir $script:Root
if ($run.StdOut) { Write-Host $run.StdOut }
if ($run.Code -ne 0) {
    Write-Host ("[fatal] back-end exit {0}" -f $run.Code) -ForegroundColor Red
    if ($run.StdErr) { Write-Host $run.StdErr -ForegroundColor DarkYellow }
    return
}

# --- read verdict from JSON (front/back-end sync point) ---
if (Test-Path $script:Calib) {
    $v = Get-Content -Path $script:Calib -Raw -Encoding UTF8 | ConvertFrom-Json
    $color = if ($v.status -eq "PROVED_VALID") { "Green" } else { "Red" }
    Write-Host ("[verdict] {0}  —  {1}" -f $v.status, $v.reason) -ForegroundColor $color
    if ($v.best) {
        Write-Host ("[params ] W={0}  kappa={1}  tier={2}  score={3}" -f `
            $v.best.window, $v.best.kappa, $v.best.min_tier, $v.best.train_score)
    }
}

# --- front-end: open the synced HTML (LL#12 override: auto-open HTML allowed) ---
if ((Test-Path $script:Hub) -and (-not $NoOpen)) {
    # v0100R 介面整合令:只開整合 Hub 一窗(理論總覽+六視圖側欄切換),不再彈六窗
    Write-Host ("[ui] opening HUB(one window) {0}" -f $script:Hub)
    Start-Process $script:Hub
} elseif ((Test-Path $script:Report) -and (-not $NoOpen)) {
    Write-Host ("[ui] opening {0}" -f $script:Report)
    Start-Process $script:Report
    if (Test-Path $script:WorldMap) {
        Write-Host ("[ui] opening {0}" -f $script:WorldMap)
        Start-Process $script:WorldMap
    }
    if (Test-Path $script:TierMap) {
        Write-Host ("[ui] opening {0}" -f $script:TierMap)
        Start-Process $script:TierMap
    }
    if (Test-Path $script:MapSim) {
        Write-Host ("[ui] opening {0}" -f $script:MapSim)
        Start-Process $script:MapSim
    }
    if (Test-Path $script:PerfTrend) {
        Write-Host ("[ui] opening {0}" -f $script:PerfTrend)
        Start-Process $script:PerfTrend
    }
    if (Test-Path $script:Monitor) {
        Write-Host ("[ui] opening {0}" -f $script:Monitor)
        Start-Process $script:Monitor
    }
} elseif (-not (Test-Path $script:Report)) {
    Write-Host "[ui] index.html not produced (run cmd 'all' or 'ui')" -ForegroundColor DarkYellow
}

Write-Host "=== done ===" -ForegroundColor Cyan

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
