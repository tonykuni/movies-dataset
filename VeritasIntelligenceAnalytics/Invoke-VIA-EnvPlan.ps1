# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
$script:VIACel = $null
$script:VIACelNote = "正主缺,略過"
try {
    $celFile = $null
    $celProbe = $PSScriptRoot
    while ($celProbe -and (Split-Path $celProbe -Parent)) {
        $celTry = Join-Path $celProbe "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
        if (Test-Path -LiteralPath $celTry) { $celFile = $celTry; break }
        $celProbe = Split-Path $celProbe -Parent
    }
    if ($celFile) {
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
} catch {
    $script:VIACelNote = "正主載入失敗,略過"
}
Write-Host ("  [Celeritas] " + $script:VIACelNote)
$plan = Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL135_EnvPlan_v0100.py"
python $plan
$rc = $LASTEXITCODE
if ($script:VIACel) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
if ($rc -ne 0) {
    Write-Output "NEXT: 環境計畫自測未過,先不要裝"
    exit $rc
}
Write-Output "NEXT: Invoke-VIACeleritasScoped { via-envgov tools }"
exit 0
