# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# 不接自動下一步。紅字錯誤留在原指令。文末這一段用黃色，只貼這一段。
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
$py = Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL149_Closeout_v0100.py"
$raw = python $py
$rc = $LASTEXITCODE
$on = $false
foreach ($line in $raw) {
    if ($line -eq "BEGIN_PASTE") { $on = $true; Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow; continue }
    if ($line -eq "END_PASTE") { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; $on = $false; continue }
    if ($on) { Write-Host $line -ForegroundColor Yellow }
}
if ($script:VIACel) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
exit $rc
