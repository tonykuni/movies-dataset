#requires -Version 7.0
<#
Start-VIA-VDF-v0103 · gate for the v0160C workbench (plain browser HTML U/I).
v0160C serves the same Veritas design-lock workbench as a regular HTML page in the
default browser over a localhost HTTP bridge (ports 8766/8768/8776) — mshta/ActiveX
removed, all seven parameters and worker actions preserved via /api endpoints.
Rollback chain: v0102 gates v0160B (HTA, design-lock masthead), v0101 gates v0160A
(original canonical) — repoint bin/via-vdf.cmd to step back.
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
$Launcher = Join-Path $Base "supportive modules\VIA_Governance_Runtime\v0160C\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160C.ps1"
$ExpectedSHA = "1cc63429dd1b3d619338efd08b6951cc588803206a2072672738f26b36534a6e"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "v0160C launcher missing: $Launcher"
}

$ActualSHA = (
    Get-FileHash -LiteralPath $Launcher -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw "v0160C launcher SHA256 mismatch. Expected $ExpectedSHA got $ActualSHA. If this is a fresh checkout, ensure .gitattributes byte-exact rules applied (delete the v0160C folder and 'git checkout -- .' to renormalize)."
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
    throw "v0160C launcher AST validation failed."
}

& $Launcher -Base $Base @args

