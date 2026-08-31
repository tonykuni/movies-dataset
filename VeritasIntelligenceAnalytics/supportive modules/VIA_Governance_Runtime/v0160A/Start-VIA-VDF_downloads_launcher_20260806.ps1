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
$ErrorActionPreference = "Stop"

$Launcher = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0160A\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160A.ps1"
$ExpectedSHA = "778ced5d0c127d61a8d104bfcca77bcb1a6597e010b12dda80d7c23d1e43f021"
$Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Canonical VDF launcher missing: $Launcher"
}

$ActualSHA = (
    Get-FileHash -LiteralPath $Launcher -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw "Canonical VDF launcher SHA256 mismatch."
}

$Tokens = $null
$Errors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $Launcher,
    [ref]$Tokens,
    [ref]$Errors
) | Out-Null

if (@($Errors).Count -gt 0) {
    $Errors | Format-Table -AutoSize -Wrap
    throw "Canonical VDF launcher AST validation failed."
}

& $Launcher -Base $Base

