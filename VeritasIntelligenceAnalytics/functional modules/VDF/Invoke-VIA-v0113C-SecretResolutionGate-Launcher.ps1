param(
    [string]$def_PARAM_WORKER_PS1 = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VIA-v0113C-SecretResolutionGate-Worker.ps1",
    [int]$def_PARAM_MAX_TOTAL_MINUTES = 30,
    [int]$def_PARAM_IDLE_REVIEW_MINUTES = 6,
    [int]$def_PARAM_POLL_SECONDS = 2
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113C_SECRET_RESOLUTION_LAUNCHER" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF"
$def_RUN_DIR = Join-Path $def_ROOT "_nostall_turbo_launcher\$def_RUN_ID"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"

foreach ($d in @($def_RUN_DIR,$def_LOG_DIR,$def_REPORT_DIR,$def_OUTPUT_DIR)) {
    if (-not (Test-Path -LiteralPath $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}

$def_STDOUT = Join-Path $def_LOG_DIR "child_stdout.log"
$def_STDERR = Join-Path $def_LOG_DIR "child_stderr.log"
$def_PARENT_LOG = Join-Path $def_LOG_DIR "launcher.log"
$def_SUMMARY_JSON = Join-Path $def_OUTPUT_DIR "VIA_v0113C_NoStall_Launcher_Summary.json"
$def_REPORT_HTML = Join-Path $def_REPORT_DIR "VIA_v0113C_NoStall_Launcher_Report.html"

function def_Log {
    param([string]$Level,[string]$Message,[ConsoleColor]$Color = [ConsoleColor]::Gray)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath $def_PARENT_LOG -Value $line -Encoding UTF8
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0113C SECRET RESOLUTION GATE · NO-STALL LAUNCHER" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    if (-not (Test-Path -LiteralPath $def_PARAM_WORKER_PS1)) {
        throw "Worker script missing: $def_PARAM_WORKER_PS1"
    }

    $item = Get-Item -LiteralPath $def_PARAM_WORKER_PS1
    if ($item.Length -lt 1000) {
        throw "Worker script too small or empty: $def_PARAM_WORKER_PS1"
    }

    def_Log "OK" "Worker exists. Size=$($item.Length)" Green

    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$def_PARAM_WORKER_PS1`""
    $proc = Start-Process -FilePath "pwsh" -ArgumentList $arg -WorkingDirectory (Split-Path -Parent $def_PARAM_WORKER_PS1) -RedirectStandardOutput $def_STDOUT -RedirectStandardError $def_STDERR -PassThru -WindowStyle Hidden

    def_Log "OK" "Child started. PID=$($proc.Id)" Green

    $start = Get-Date
    $lastChange = Get-Date
    $lastOut = 0
    $lastErr = 0
    $status = "RUNNING"
    $exitCode = ""

    while (-not $proc.HasExited) {
        Start-Sleep -Seconds $def_PARAM_POLL_SECONDS

        $now = Get-Date
        $elapsed = $now - $start

        $outSize = 0
        $errSize = 0
        if (Test-Path -LiteralPath $def_STDOUT) { $outSize = (Get-Item -LiteralPath $def_STDOUT).Length }
        if (Test-Path -LiteralPath $def_STDERR) { $errSize = (Get-Item -LiteralPath $def_STDERR).Length }

        if ($outSize -ne $lastOut -or $errSize -ne $lastErr) {
            $lastChange = $now
            $lastOut = $outSize
            $lastErr = $errSize
        }

        $idle = $now - $lastChange
        $pct = [int][Math]::Min(99, ($elapsed.TotalMinutes / [Math]::Max(1,$def_PARAM_MAX_TOTAL_MINUTES)) * 100)

        Write-Progress `
            -Activity "VIA v0113C Secret Resolution Launcher" `
            -Status ("PID={0} | elapsed={1:n2}m | idle={2:n2}m | stdout={3} | stderr={4}" -f $proc.Id,$elapsed.TotalMinutes,$idle.TotalMinutes,$outSize,$errSize) `
            -PercentComplete $pct

        if ($elapsed.TotalMinutes -ge $def_PARAM_MAX_TOTAL_MINUTES) {
            $status = "TIMEOUT_REVIEW_CHILD_STILL_RUNNING"
            def_Log "WARN" "Max total minutes reached. Child remains running by policy. PID=$($proc.Id)" Yellow
            break
        }

        if ($idle.TotalMinutes -ge $def_PARAM_IDLE_REVIEW_MINUTES) {
            $status = "IDLE_REVIEW_CHILD_STILL_RUNNING"
            def_Log "WARN" "Idle review threshold reached. Child remains running by policy. PID=$($proc.Id)" Yellow
            break
        }
    }

    if ($proc.HasExited) {
        $exitCode = [string]$proc.ExitCode
        if ($proc.ExitCode -eq 0) {
            $status = "CHILD_COMPLETED_OK"
            def_Log "OK" "Child completed ExitCode=0" Green
        } else {
            $status = "CHILD_COMPLETED_NONZERO"
            def_Log "WARN" "Child completed ExitCode=$($proc.ExitCode)" Yellow
        }
    }

    Write-Progress -Activity "VIA v0113C Secret Resolution Launcher" -Completed

    $elapsedFinal = (Get-Date) - $start
    $idleFinal = (Get-Date) - $lastChange

    $summary = [pscustomobject][ordered]@{
        Status = $status
        RunId = $def_RUN_ID
        PID = [string]$proc.Id
        ExitCode = [string]$exitCode
        ElapsedMinutes = "{0:n2}" -f $elapsedFinal.TotalMinutes
        IdleMinutes = "{0:n2}" -f $idleFinal.TotalMinutes
        Worker = $def_PARAM_WORKER_PS1
        Stdout = $def_STDOUT
        Stderr = $def_STDERR
        ParentLog = $def_PARENT_LOG
        Policy = "No delete; No Stop-Process; child remains running on timeout/idle review."
    }

    $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $def_SUMMARY_JSON -Encoding UTF8

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113C NO-STALL LAUNCHER COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status : $($summary.Status)" -ForegroundColor Green
    Write-Host "PID    : $($summary.PID)" -ForegroundColor Gray
    Write-Host "Exit   : $($summary.ExitCode)" -ForegroundColor Gray
    Write-Host "Stdout : $def_STDOUT" -ForegroundColor Cyan
    Write-Host "Stderr : $def_STDERR" -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed." -ForegroundColor Yellow
}
