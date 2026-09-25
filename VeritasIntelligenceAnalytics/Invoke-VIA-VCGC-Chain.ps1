# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$script:VIACel = $null
$script:VIACelNote = "正主缺,略過"
try {
    $celFile = Join-Path $PSScriptRoot "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $celFile) {
        $script:VIACel = New-Module -Name "VIACeleritasPS7" -ArgumentList $celFile -ErrorAction SilentlyContinue -ScriptBlock {
            param($CelFile)
            $script:CeleritasPS7 = $null
            $OFS = " "
            if (-not (Get-Variable -Name PSNativeCommandArgumentPassing -ErrorAction SilentlyContinue)) { $PSNativeCommandArgumentPassing = $null }
            $null = . $CelFile -RestoreOnly 2>$null
            Export-ModuleMember -Function Restore-CeleritasPS7
        }
        $celOn = $false
        $celSnap = $null
        if ($script:VIACel) { try { $celSnap = & $script:VIACel { Get-CeleritasSnapshot } 2>$null } catch { $celSnap = $null } }
        if ($script:VIACel -and ($null -ne $celSnap)) {
            try { $null = & $script:VIACel { Start-CeleritasPS7 } 2>$null } catch { }
            try { $celOn = [bool](& $script:VIACel { $script:CeleritasPS7.Applied -and ($null -ne $script:CeleritasPS7.Snapshot) } 2>$null) } catch { $celOn = $false }
            if (-not $celOn) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
        }
        $script:VIACelNote = $(if ($celOn) { "本行程減壓已套" } else { "正主在但沒套上,略過" })
    }
} catch { $script:VIACelNote = "正主載入失敗,略過" }
Write-Host ("  [Celeritas] " + $script:VIACelNote)
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
