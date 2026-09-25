#Requires -Version 7.0
# Invoke-VIA-Panorama v0101
# read / slice / digest stay on the panorama tail and do not start a fetch.
# Every other call is unchanged and goes to v0100.
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = 'Stop'
$light = @('read', 'slice', 'digest')
if ($args.Count -ge 1 -and $light -contains [string]$args[0]) {
    $via = Split-Path -Parent $PSScriptRoot
    $reg = Get-ChildItem -LiteralPath $via -Filter 'Register-VIA-Commands-v*.ps1' -File |
        Sort-Object Name | Select-Object -Last 1
    if (-not $reg) { throw '找不到中央 VIA 指令冊' }
    . $reg.FullName
    $py = Get-VIAEnvPython 'vdf'
    $tool = Get-ChildItem -LiteralPath (Join-Path $via 'supportive modules\registry') -Filter 'CGC_MDL158_VIAPanoramaAuditRepair_v*.py' -File |
        Sort-Object Name | Select-Object -Last 1
    if (-not $tool) { throw '全景正主缺席' }
    & $py -X utf8 $tool.FullName @args
    exit $LASTEXITCODE
}
& (Join-Path $PSScriptRoot 'Invoke-VIA-Panorama-v0100.ps1') @args
exit $LASTEXITCODE
