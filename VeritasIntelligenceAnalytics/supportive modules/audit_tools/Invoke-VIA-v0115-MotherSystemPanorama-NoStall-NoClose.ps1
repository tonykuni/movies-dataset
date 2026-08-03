$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$ManagerPy = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_via_mother_system_manager\VIA_MotherSystemManager_v0115.py"
$RunRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_integration_v0115_mother_system_panorama"
$RunId = "RUN_{0}_VIA_v0115_MOTHER_SYSTEM_PANORAMA_IAM" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$RunDir = Join-Path $RunRoot $RunId

function Step($n,$t,$m){
    $pct = [int](($n / [Math]::Max(1,$t)) * 100)
    Write-Progress -Activity "VIA v0115 Mother System Panorama" -Status $m -PercentComplete $pct
    Write-Host "[$n/$t] $m" -ForegroundColor Cyan
}

function EnsureDir($p){
    if (-not (Test-Path -LiteralPath $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
    }
}

function FindPython {
    $venv = Join-Path $Base "_envs\via_operation_optimizer_2026\Scripts\python.exe"
    if (Test-Path -LiteralPath $venv) { return $venv }
    foreach ($cmd in @("python","py")) {
        try {
            $null = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0 -or $?) { return $cmd }
        } catch {}
    }
    throw "Python not found."
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0115 · Mother System Panorama Launcher" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: local-only · no external call · no apply · no source mutation · no DB write" -ForegroundColor Yellow

    Step 1 5 "Prepare run folder"
    EnsureDir $RunDir

    Step 2 5 "Find Python"
    $Python = FindPython
    Write-Host "[OK] Python: $Python" -ForegroundColor Green

    Step 3 5 "Run Python mother system manager"
    $Args = @($ManagerPy, "--base", $Base, "--run-dir", $RunDir, "--threads", "8", "--max-hash-mb", "25")
    if ($Python -eq "py") {
        & py -3 @Args
    } else {
        & $Python @Args
    }

    Step 4 5 "Open report and output"
    $Report = Join-Path $RunDir "report\VIA_v0115_MotherSystemPanorama_IAM_Report.html"
    $Output = Join-Path $RunDir "output"
    $Candidates = Join-Path $RunDir "_iam_registry_ssot_candidates"

    if (Test-Path -LiteralPath $Report) { Start-Process -FilePath $Report }
    if (Test-Path -LiteralPath $Output) { Start-Process -FilePath $Output }
    if (Test-Path -LiteralPath $Candidates) { Start-Process -FilePath $Candidates }

    Step 5 5 "Complete"
    Write-Progress -Activity "VIA v0115 Mother System Panorama" -Completed

    Write-Host ""
    Write-Host "[READY] VIA v0115 Mother System Panorama completed." -ForegroundColor Green
    Write-Host "RunDir    : $RunDir" -ForegroundColor Cyan
    Write-Host "Report    : $Report" -ForegroundColor Cyan
    Write-Host "Output    : $Output" -ForegroundColor Cyan
    Write-Host "Candidate : $Candidates" -ForegroundColor Cyan
    Write-Host "[SAFE] No apply. No source mutation. No DB write. No external call." -ForegroundColor Yellow

} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host "PowerShell remains open. No apply. No mutation. No DB write." -ForegroundColor Yellow
    return
} finally {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · PowerShell remains open" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
}
