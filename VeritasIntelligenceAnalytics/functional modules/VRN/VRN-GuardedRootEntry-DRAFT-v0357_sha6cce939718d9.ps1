#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# =============================================================================
# VIA v035.7 Guarded Root Entry
# Project   : VRN
# Candidate : C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1
# =============================================================================
# Default behavior is SAFE PROBE only.
# Full run requires explicit -Run.
# =============================================================================

param(
    [switch]$Run,
    [switch]$SafeProbe,
    [switch]$Plan
)

$SelectedCandidate = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
$ExpectedEntry = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1"

function Write-GuardedLine {
    param([string]$Level,[string]$Message)
    $c="Gray"
    if($Level -eq "OK"){$c="Green"}
    elseif($Level -eq "WARN"){$c="Yellow"}
    elseif($Level -eq "FAIL"){$c="Red"}
    elseif($Level -eq "RUN"){$c="Cyan"}
    Write-Host "[$(Get-Date -Format 'HH:mm:ss.fff')] [$Level] $Message" -ForegroundColor $c
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA v035.7 · VRN Guarded Root Entry" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if(-not(Test-Path -LiteralPath $SelectedCandidate -PathType Leaf)){
    Write-GuardedLine "FAIL" "Selected candidate missing: $SelectedCandidate"
    return
}

try {
    $tokens=$null
    $errors=$null
    [System.Management.Automation.Language.Parser]::ParseFile($SelectedCandidate,[ref]$tokens,[ref]$errors)|Out-Null

    if(@($errors).Count -eq 0){
        Write-GuardedLine "OK" "Candidate parser OK."
    } else {
        Write-GuardedLine "FAIL" "Candidate parser errors: $(@($errors).Count)"
        @($errors | Select-Object -First 10) | ForEach-Object { Write-GuardedLine "FAIL" $_.Message }
        return
    }

    $item=Get-Item -LiteralPath $SelectedCandidate -Force
    $hash=(Get-FileHash -LiteralPath $SelectedCandidate -Algorithm SHA256).Hash
    Write-GuardedLine "OK" "Candidate bytes: $($item.Length)"
    Write-GuardedLine "OK" "Candidate SHA256: $hash"
} catch {
    Write-GuardedLine "FAIL" $_.Exception.Message
    return
}

if($Plan -or -not $Run){
    Write-GuardedLine "OK" "SAFE_PROBE_COMPLETE"
    Write-GuardedLine "WARN" "Default mode does not execute candidate. Use -Run only after production approval."
    Write-GuardedLine "WARN" "Expected entry: $ExpectedEntry"
    return
}

Write-GuardedLine "RUN" "Explicit -Run detected. Invoking selected candidate."
& pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $SelectedCandidate @args