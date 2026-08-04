#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Launcher = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0162C\bin\Invoke-VIA-SystemManager-AllInOne-v0162C.ps1'
$ExpectedSHA = '5e13d9a21538a891c0aebb59068851a7610eb0376ccc3338c77baa56723a0b49'
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