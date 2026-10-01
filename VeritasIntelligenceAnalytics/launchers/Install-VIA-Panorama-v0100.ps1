#Requires -Version 7.0
# ===== Parameters / environment entry =====
param(
    [string]$ViaRoot = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
    [ValidateRange(1,24)][int]$Months = 2,
    [ValidateRange(1,86400)][int]$StationTimeout = 600,
    [ValidateRange(1,86400)][int]$FetchTimeout = 7200,
    [ValidateRange(1,100)][int]$BatchSize = 20,
    [switch]$Fetch
)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

Set-Location -LiteralPath $ViaRoot
$ErrorActionPreference = 'Stop'
$Register = Get-ChildItem -LiteralPath $ViaRoot -Filter 'Register-VIA-Commands-v*.ps1' -File | Sort-Object Name | Select-Object -Last 1
if (-not $Register) { throw '缺少 VIA 指令冊，請確認專案位置' }
. $Register.FullName
Set-Location -LiteralPath $ViaRoot
$FamilyPython = Get-VIAEnvPython 'vrn'
if (-not (Test-Path -LiteralPath $FamilyPython -PathType Leaf)) { throw "VRN 環境缺席：$FamilyPython" }
. (Join-Path $ViaRoot 'supportive modules\VIA_PS_Accel_Module.ps1')
$Roster = Get-VIAAccelRoster
if ($Roster.Count -ne 20) { throw 'PS 20項加速器冊未完整載入' }
$Roster.GetEnumerator() | Format-Table Key,Value -AutoSize | Out-Host

# ===== Verify complete plan before adding versioned code =====
function def_InstallPayload {
    $Manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
    $Plan = @()
    foreach ($Item in $Manifest) {
        $Relative = [string]$Item.path
        if ([IO.Path]::IsPathRooted($Relative) -or '..' -in ($Relative -split '[/\\]')) { throw '不合法套件路徑' }
        $Source = Join-Path (Join-Path $PSScriptRoot 'payload') $Relative
        $Target = Join-Path $ViaRoot $Relative
        if ((Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash -ne $Item.sha256) { throw "套件雜湊不符：$Relative" }
        if ($Source.EndsWith('.ps1',[StringComparison]::OrdinalIgnoreCase)) {
            $Tokens = $null
            $ParseErrors = $null
            $null = [Management.Automation.Language.Parser]::ParseFile($Source,[ref]$Tokens,[ref]$ParseErrors)
            if ($ParseErrors.Count -gt 0) { throw "PowerShell 語法檢查失敗：$Relative`n$($ParseErrors | Out-String)" }
        }
        $Present = Test-Path -LiteralPath $Target
        if ($Present) {
            $SourceText = [IO.File]::ReadAllText($Source).Replace("`r`n","`n")
            $TargetText = [IO.File]::ReadAllText($Target).Replace("`r`n","`n")
            if ($SourceText -cne $TargetText) { throw "保留本機修改，停止補版：$Target" }
        }
        $Plan += [pscustomobject]@{Source=$Source;Target=$Target;Present=$Present}
    }
    $Index = 0
    foreach ($Item in $Plan) {
        $Index++
        Write-Progress -Activity 'VIA 全景補版' -Status "$Index / $($Plan.Count)" -PercentComplete (100*$Index/$Plan.Count)
        if (-not $Item.Present) {
            New-Item -ItemType Directory -Path (Split-Path $Item.Target -Parent) -Force | Out-Null
            [IO.File]::Copy($Item.Source,$Item.Target,$false)
            Write-Host "新增：$($Item.Target)"
        }
    }
    Write-Progress -Activity 'VIA 全景補版' -Completed
}

def_InstallPayload
& (Join-Path $ViaRoot 'launchers\Invoke-VIA-Panorama-v0100.ps1') -ViaRoot $ViaRoot -Months $Months -StationTimeout $StationTimeout -FetchTimeout $FetchTimeout -BatchSize $BatchSize -Fetch:$Fetch
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
