#requires -Version 7.0
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
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Launcher = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0162B\bin\Invoke-VIA-SystemManager-AllInOne-v0162B.ps1'
$ExpectedSHA = '3707335b1ec911730305715bc1b14b5f43ec7d3903182b787e4e1c3314fb019a'
$Base = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'

if (-not (
    Test-Path `
        -LiteralPath $Launcher `
        -PathType Leaf
)) {
    throw (
        "VIA System Manager canonical launcher is missing: " +
        $Launcher
    )
}

$ActualSHA = (
    Get-FileHash `
        -LiteralPath $Launcher `
        -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw (
        "VIA System Manager canonical SHA256 mismatch. " +
        "Expected=$ExpectedSHA Actual=$ActualSHA"
    )
}

$Tokens = $null
$Errors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $Launcher,
    [ref]$Tokens,
    [ref]$Errors
) | Out-Null

if (@($Errors).Count -gt 0) {
    Write-Host ""
    Write-Host (
        "def CANONICAL AST : FAIL"
    ) -ForegroundColor Red

    foreach ($ParseError in @($Errors)) {
        Write-Host (
            "Line {0}, Column {1}: {2}" -f
            $ParseError.Extent.StartLineNumber,
            $ParseError.Extent.StartColumnNumber,
            $ParseError.Message
        ) -ForegroundColor Red
    }

    throw (
        "VIA System Manager canonical AST validation failed."
    )
}

& $Launcher -Base $Base
