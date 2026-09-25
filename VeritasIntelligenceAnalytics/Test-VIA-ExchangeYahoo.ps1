# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# First test: VCGC, then accelerator and network bridges, then TWSE/TPEX/yfinance.
# -Live also runs monthly revenue and the statement status. Default does not fetch.
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
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$template = Join-Path $via 'supportive modules\ps7\VeritasCeleritas.PS7.Template.ps1'
if (Test-Path -LiteralPath $template) { . $template }
$reg = Get-ChildItem -LiteralPath $via -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if (-not $reg) { throw "Register-VIA-Commands not found under $via" }
. $reg.FullName
$live = $args -contains '-Live'
via-vcgc status
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
via-bridge-sweep --subsystems --apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
via-bridge-sweep --ps --ps-tail --apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$py = Get-VIAEnvPython 'vdf'
& $py (Get-VIANewest "$via\functional modules\VDF\engine" 'VDF_ENG063_MonthlyRevenue_v*.py') --selftest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py (Get-VIANewest "$via\functional modules\VDF\engine" 'VDF_ENG082_FinStatements_v*.py') --selftest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py (Get-VIANewest "$via\functional modules\VDF\engine" 'VDF_ENG101_SourceProbe_v*.py') --selftest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
via-finstat status
via-vrnfin status
if ($live) {
    via-revfill status
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
exit $LASTEXITCODE
