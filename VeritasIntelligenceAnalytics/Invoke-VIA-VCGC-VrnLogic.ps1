# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
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
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$eng = Join-Path $via "functional modules\VRN\VRN_ENG113_LogicRollup_v0100.py"
if (-not (Test-Path -LiteralPath $eng)) {
    Write-Host "  [vrn-logic] ABSENT: $eng" -ForegroundColor Yellow
    Write-Host "  [vrn-logic] 這台還沒有這支。先 git pull，log 要到 8e87e26c 之後。" -ForegroundColor Yellow
    exit 2
}
$env:VIA_FROM_VCGC = "YES"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
python $eng
$code = $LASTEXITCODE
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
