# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# 不接自動下一步。紅字錯誤留在原指令。文末這一段用黃色，只貼這一段。
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
$py = Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL149_OneDragon_v0100.py"
$env:VIA_FROM_VCGC = 'YES'
$raw = python $py
$rc = $LASTEXITCODE
$on = $false
foreach ($line in $raw) {
    if ($line -eq "BEGIN_PASTE") { $on = $true; Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow; continue }
    if ($line -eq "END_PASTE") { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; $on = $false; continue }
    if ($line.StartsWith("GREEN ")) { Write-Host $line.Substring(6) -ForegroundColor Green; continue }
    if ($on) { Write-Host $line -ForegroundColor Yellow }
}
if ($script:VIACel) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
exit $rc
