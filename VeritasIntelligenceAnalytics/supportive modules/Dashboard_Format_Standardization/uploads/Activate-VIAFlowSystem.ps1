#requires -Version 7.0
param(
    [string]$Cmd = "all",
    [string]$PythonExe = "",
    [switch]$NoOpen
)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====


# VDF-FLOW-LAUNCHER-16  Activate-VIAFlowSystem.ps1
# One launcher: activates env, runs PY back-end (synth->calibrate->run->ui),
# syncs the front-end index.html and opens it.
# LL-compliant: param() first; line comments only; full cmdlet names;
# ProcessStartInfo + ArgumentList.Add per-arg + async drain (no 64KB deadlock);
# Start-Process only to open the HTML report; no Start-Job/Read-Host/exit in main.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:Root    = $PSScriptRoot
$script:Manager = Join-Path $script:Root "engines/FLOW_ENG009_FlowManager.py"
$script:Report  = Join-Path $script:Root "index.html"
$script:WorldMap = Join-Path $script:Root "world_flow.html"
$script:TierMap  = Join-Path $script:Root "tier_flow.html"
$script:MapSim   = Join-Path $script:Root "global_map_sim.html"
$script:PerfTrend= Join-Path $script:Root "perf_trend.html"
$script:Monitor  = Join-Path $script:Root "flow_monitor.html"
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
if ((Test-Path $script:Report) -and (-not $NoOpen)) {
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
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
