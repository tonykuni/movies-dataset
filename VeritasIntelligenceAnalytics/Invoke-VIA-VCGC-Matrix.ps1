# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# 只讀已同步的結果。不叫 VDF，不重跑報告。
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
python (Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL149_GreenMatrix_v0100.py")
