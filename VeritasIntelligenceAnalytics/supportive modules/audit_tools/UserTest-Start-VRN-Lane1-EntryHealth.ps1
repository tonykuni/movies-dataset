#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VRN · VRN-Lane1-EntryHealth" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Mode        : READ_ONLY_USER_TEST"
Write-Host "Target Path : C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_SAFE_PARALLEL_GATE_v02872_20260611_205436\launchers\Start-VRN-Lane1-EntryHealth.ps1"
Write-Host ""

# Safety policy:
# - No DB write
# - No canonical merge
# - No source repair
# - No destructive delete
# - No Stop-Process
# - No network I/O
# - No parallel accelerator execution
# This command is a user-test viewer / read-only opener.

$TargetPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_SAFE_PARALLEL_GATE_v02872_20260611_205436\launchers\Start-VRN-Lane1-EntryHealth.ps1"

if ([string]::IsNullOrWhiteSpace($TargetPath)) {
    Write-Host "[WARN] Target path is empty." -ForegroundColor Yellow
}
elseif (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
    Write-Host "[OK] Target file exists." -ForegroundColor Green
    Write-Host "File: $TargetPath"

    if ($TargetPath -match '\.html?$') {
        Start-Process $TargetPath
    }
    elseif ($TargetPath -match '\.json$') {
        try {
            $j = Get-Content -LiteralPath $TargetPath -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Host "Status : $($j.status)"
            Write-Host "Risk   : $($j.risk)"
        } catch {
            Write-Host "[WARN] JSON read issue: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    elseif ($TargetPath -match '\.ps1$') {
        Write-Host "PowerShell script is present. Not executing automatically by policy."
        Write-Host "Manual command if needed:"
        Write-Host "pwsh -NoProfile -ExecutionPolicy Bypass -File `"$TargetPath`"" -ForegroundColor Cyan
    }
}
elseif (Test-Path -LiteralPath $TargetPath -PathType Container) {
    Write-Host "[OK] Target directory exists." -ForegroundColor Green
    Write-Host "Directory: $TargetPath"

    $latestHtml = Get-ChildItem -LiteralPath $TargetPath -Recurse -File -Filter "*.html" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($latestHtml) {
        Write-Host "Opening latest HTML:"
        Write-Host $latestHtml.FullName
        Start-Process $latestHtml.FullName
    }
    else {
        Write-Host "No HTML found. Opening directory."
        Start-Process $TargetPath
    }
}
else {
    Write-Host "[WARN] Target path does not exist." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "PowerShell remains open. No exit. No Stop-Process. No destructive delete." -ForegroundColor Green