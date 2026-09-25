# Active Taiwan ETFs only. Refresh the master list, then fill holdings
# from listing without repeating days already stored.
# A universe rc of 2 means a name left the official book. The csv of the
# names that remain is still usable, so holdings continue.
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
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$reg = Get-ChildItem -LiteralPath $root -Filter 'Register-VIA-Commands-v*.ps1' |
    Sort-Object Name | Select-Object -Last 1
if (-not $reg) { throw "Register-VIA-Commands not found under $root" }
. $reg.FullName
via-etfuniv
$rc = $LASTEXITCODE
$csv = Join-Path $root 'functional modules\VDF\output_hub\active_tw_etf\active_tw_etf_ssot\ActiveTWETF_Latest.csv'
if ($rc -eq 2 -and (Test-Path -LiteralPath $csv)) {
    Write-Host '[宇宙] rc=2 官方冊有缺檔;已寫下的總清單照舊補持股'
} elseif ($rc -ne 0) {
    exit $rc
}
via-etfhist backfill
exit $LASTEXITCODE
