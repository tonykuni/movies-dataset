#requires -Version 7.0
<#
Start-VIA-VDF-v0102 · gate for the v0160B workbench (Veritas design-lock masthead).
v0160B is a style-only version-forward of the hash-locked v0160A canonical — functional
code identical, masthead aligned to the Veritas design source. v0160A and its v0101 gate
remain untouched in the tree for rollback (point bin/via-vdf.cmd back at v0101).
Same fail-closed gate: SHA256 + AST validation, then hand-off.
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
$Launcher = Join-Path $Base "supportive modules\VIA_Governance_Runtime\v0160B\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160B.ps1"
$ExpectedSHA = "184f5195679715ad0d97a4b08b794c5ac53f784e95298cbc7e3e8de8622d96bc"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "v0160B launcher missing: $Launcher"
}

$ActualSHA = (
    Get-FileHash -LiteralPath $Launcher -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw "v0160B launcher SHA256 mismatch. Expected $ExpectedSHA got $ActualSHA. If this is a fresh checkout, ensure .gitattributes byte-exact rules applied (delete the v0160B folder and 'git checkout -- .' to renormalize)."
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
    throw "v0160B launcher AST validation failed."
}

& $Launcher -Base $Base @args

