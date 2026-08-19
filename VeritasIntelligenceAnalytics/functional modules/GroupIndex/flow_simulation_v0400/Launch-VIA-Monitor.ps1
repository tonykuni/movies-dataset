param(
    [int]$Port = 8765,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }
$OutputDir = Join-Path $ProjectRoot "data\output"
$DashboardName = "VIA_TW_Group_Flow_Simulation_System_v0400.html"
$PidFile = Join-Path $ProjectRoot ".via-monitor.pid"

if (-not $SkipBuild) {
    & $Python (Join-Path $ProjectRoot "run_system.py") all --config (Join-Path $ProjectRoot "config\system_config.json")
    if ($LASTEXITCODE -ne 0) { throw "VIA engine stopped at a fail-closed gate." }
}

if (-not (Test-Path (Join-Path $OutputDir $DashboardName))) {
    throw "Dashboard does not exist. Run without -SkipBuild first."
}

if (Test-Path $PidFile) {
    $ExistingPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($ExistingPid -and (Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue)) {
        Write-Host "VIA monitor server is already running (PID $ExistingPid)."
        Start-Process "http://127.0.0.1:$Port/$DashboardName"
        exit 0
    }
}

$Server = Start-Process -FilePath $Python -ArgumentList @(
    "-m", "http.server", "$Port", "--bind", "127.0.0.1", "--directory", $OutputDir
) -PassThru -WindowStyle Hidden
Set-Content -Path $PidFile -Value $Server.Id -Encoding Ascii
Start-Sleep -Milliseconds 600
Start-Process "http://127.0.0.1:$Port/$DashboardName"
Write-Host "VIA monitor opened. Background server PID: $($Server.Id)"
