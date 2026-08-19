$ErrorActionPreference = "Stop"
$PidFile = Join-Path $PSScriptRoot ".via-monitor.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "No VIA monitor PID file was found."
    exit 0
}

$ServerPid = Get-Content $PidFile
$Process = Get-Process -Id $ServerPid -ErrorAction SilentlyContinue
if ($Process) {
    Stop-Process -Id $ServerPid
    Write-Host "Stopped VIA monitor server PID $ServerPid."
}
Remove-Item $PidFile -Force

