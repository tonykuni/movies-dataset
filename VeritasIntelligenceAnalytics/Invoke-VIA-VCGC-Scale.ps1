# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# 從 VCGC 往下。上漲空間用調整後收盤，不看報告放了多久。不重抓、不改政策冊。
# 紅字錯誤留在原指令。文末這一段用黃色，只貼這一段。
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$script:VIAAccelPairNote = "正主缺,略過"
try {
    $join = Join-Path $PSScriptRoot "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $join) {
        . $join
        $script:VIAAccelPairNote = "套對 $($script:CeleritasPS7.Version) · 已套"
    }
} catch {
    $script:VIAAccelPairNote = "正主載入失敗,略過"
}
Write-Host ("  [加速器] " + $script:VIAAccelPairNote)
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL149_UnitScale_v0101.py"
$raw = python $py
$on = $false
foreach ($line in $raw) {
    if ($line -eq "BEGIN_PASTE") { $on = $true; Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow; continue }
    if ($line -eq "END_PASTE") { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; continue }
    if ($on) { Write-Host $line -ForegroundColor Yellow }
}
exit $LASTEXITCODE
