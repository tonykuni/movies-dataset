param(
    [string]$def_PARAM_WORKER_PS1 = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VIA-IntegrationSecondStep-CloseoutPlanner-v0107-Worker.ps1",
    [int]$def_PARAM_MAX_TOTAL_MINUTES = 45,
    [int]$def_PARAM_IDLE_REVIEW_MINUTES = 8,
    [int]$def_PARAM_POLL_SECONDS = 2
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_SECONDSTEP_v0107_LAUNCHER" -f (Get-Date -Format "yyyyMMdd_HHmmss")
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
$def_SUMMARY_JSON = Join-Path $def_OUTPUT_DIR "VIA_SecondStep_NoStall_Launcher_Summary.json"
$def_REPORT_HTML = Join-Path $def_REPORT_DIR "VIA_SecondStep_NoStall_Launcher_Report_v0107.html"

function def_Log {
    param([string]$Level,[string]$Message,[ConsoleColor]$Color = [ConsoleColor]::Gray)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath $def_PARENT_LOG -Value $line -Encoding UTF8
}

function def_Html {
    param([string]$Text)
    return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

function def_Tail {
    param([string]$Path,[int]$Lines=26)
    try {
        if (Test-Path -LiteralPath $Path) {
            return @(Get-Content -LiteralPath $Path -Tail $Lines -ErrorAction SilentlyContinue)
        }
    } catch {}
    return @()
}

function def_WriteReport {
    param($Summary)

    $outTail = ((def_Tail $def_STDOUT 36 | ForEach-Object { def_Html $_ }) -join "<br/>")
    $errTail = ((def_Tail $def_STDERR 36 | ForEach-Object { def_Html $_ }) -join "<br/>")

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA SecondStep No-Stall Launcher v0107</title>
<style>
body{margin:0;background:#f7f6f2;color:#24231f;font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:9.2px;line-height:1.36}
.wrap{max-width:1500px;margin:0 auto;padding:16px}
h1{font-size:15.5px;margin:0 0 5px}
.sub{color:#706d64;font-size:8.8px;margin-bottom:11px}
.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin-bottom:11px}
.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:7px}
.k{font-size:8px;color:#706d64}.v{font:650 12px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:10px;padding:9px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:10px;margin:0 0 6px}
pre{white-space:pre-wrap;font-family:Consolas,monospace;font-size:8.6px;margin:0}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:8.6px}
td,th{border-bottom:1px solid #ebe8df;padding:3.5px;word-break:break-word;text-align:left}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA SecondStep No-Stall Launcher · v0107</h1>
<div class="sub">Child-isolated execution · dynamic progress · timeout review without Stop-Process</div>

<div class="cards">
<div class="card"><div class="k">Status</div><div class="v">$($Summary.Status)</div></div>
<div class="card"><div class="k">PID</div><div class="v">$($Summary.PID)</div></div>
<div class="card"><div class="k">ExitCode</div><div class="v">$($Summary.ExitCode)</div></div>
<div class="card"><div class="k">Elapsed</div><div class="v">$($Summary.ElapsedMinutes)</div></div>
<div class="card"><div class="k">Idle</div><div class="v">$($Summary.IdleMinutes)</div></div>
<div class="card"><div class="k">Run</div><div class="v">$($Summary.RunId)</div></div>
</div>

<div class="grid">
<div class="sec"><h2>def Child stdout tail</h2><pre>$outTail</pre></div>
<div class="sec"><h2>def Child stderr tail</h2><pre>$errTail</pre></div>
<div class="sec wide">
<h2>def Paths</h2>
<table>
<tr><th>Worker</th><td>$(def_Html $Summary.Worker)</td></tr>
<tr><th>Stdout</th><td>$(def_Html $Summary.Stdout)</td></tr>
<tr><th>Stderr</th><td>$(def_Html $Summary.Stderr)</td></tr>
<tr><th>Launcher Log</th><td>$(def_Html $Summary.ParentLog)</td></tr>
</table>
</div>
</div>
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $def_REPORT_HTML -Value $html -Encoding UTF8
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · INTEGRATION SECONDSTEP · v0107 NO-STALL LAUNCHER" -ForegroundColor Cyan
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
            -Activity "VIA v0107 SecondStep No-Stall Launcher" `
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

    Write-Progress -Activity "VIA v0107 SecondStep No-Stall Launcher" -Completed

    $elapsedFinal = (Get-Date) - $start
    $idleFinal = (Get-Date) - $lastChange

    $summary = [ordered]@{
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
        ReportHtml = $def_REPORT_HTML
        Policy = "No delete; No Stop-Process; child remains running on timeout/idle review."
    }

    $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $def_SUMMARY_JSON -Encoding UTF8
    def_WriteReport $summary

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0107 SECONDSTEP NO-STALL LAUNCHER COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status : $($summary.Status)" -ForegroundColor Green
    Write-Host "PID    : $($summary.PID)" -ForegroundColor Gray
    Write-Host "Exit   : $($summary.ExitCode)" -ForegroundColor Gray
    Write-Host "Report : $def_REPORT_HTML" -ForegroundColor Cyan
    Write-Host "Stdout : $def_STDOUT" -ForegroundColor Cyan
    Write-Host "Stderr : $def_STDERR" -ForegroundColor Cyan

    try { Start-Process -FilePath $def_REPORT_HTML } catch {}

} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed." -ForegroundColor Yellow
}
