# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
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
$reply = Join-Path $PSScriptRoot "VIA_Reports\vcgc\REPLY_latest.txt"
$pending = ""
if (Test-Path -LiteralPath $reply) {
    $pending = python (Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v0143.py") chain --selftest
}
if (-not (Test-Path -LiteralPath $reply)) {
    $envPy = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot "supportive modules\registry") -Filter "CGC_MDL135_EnvGovernance_v*.py" | Sort-Object Name | Select-Object -Last 1
    if ($envPy) { python $envPy.FullName tools }
}
python (Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v0143.py") chain
$rc = $LASTEXITCODE
if ($script:VIACel) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
exit $rc
