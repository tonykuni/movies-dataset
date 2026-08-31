#requires -Version 7.0
<#
Start-VIA-VDF-v0101 · repo-rooted successor of the recovered Downloads-era Start-VIA-VDF.ps1
(archived byte-exact at supportive modules/VIA_Governance_Runtime/installers/Start-VIA-VDF_20260805.ps1).
Same fail-closed gate: SHA256 + AST validation of the canonical v0160A launcher, then hand-off.
Paths are self-locating so the gate holds wherever the repo is cloned.
#>
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

$Base = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Launcher = Join-Path $Base "supportive modules\VIA_Governance_Runtime\v0160A\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160A.ps1"
$ExpectedSHA = "778ced5d0c127d61a8d104bfcca77bcb1a6597e010b12dda80d7c23d1e43f021"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Canonical VDF launcher missing: $Launcher"
}

$ActualSHA = (
    Get-FileHash -LiteralPath $Launcher -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw "Canonical VDF launcher SHA256 mismatch. Expected $ExpectedSHA got $ActualSHA. If this is a fresh checkout, ensure .gitattributes byte-exact rules applied (delete the v0160A folder and 'git checkout -- .' to renormalize)."
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

& $Launcher -Base $Base @args

