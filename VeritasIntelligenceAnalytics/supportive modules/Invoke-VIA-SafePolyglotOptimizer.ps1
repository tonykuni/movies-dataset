#requires -Version 7.0
param(
    [switch]$OpenReport,
    [switch]$RunSandboxSelfTest,
    [switch]$SelfTest
)
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
$ErrorActionPreference = "Continue"
$scriptPath = ""
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "AIO script not found: $scriptPath"
}
$argsList = @("-ExecutionPolicy", "Bypass", "-File", $scriptPath, "-RegisterLauncher")
if ($OpenReport) { $argsList += "-OpenReport" }
if ($RunSandboxSelfTest) { $argsList += "-RunSandboxSelfTest" }
if ($SelfTest) { $argsList += "-SelfTest" }
& pwsh @argsList

