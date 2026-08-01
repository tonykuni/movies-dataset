#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Launcher = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0162B\bin\Invoke-VIA-SystemManager-AllInOne-v0162B.ps1'
$ExpectedSHA = 'da26caaf308e85fcae1cfbd37361fdbe498f9339ab1199b16cd5abc6bcc84046'
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