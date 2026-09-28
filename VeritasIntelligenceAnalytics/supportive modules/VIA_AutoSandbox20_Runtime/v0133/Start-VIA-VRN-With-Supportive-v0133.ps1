#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EntrypointPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1",
    [string]$SupportiveListPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\supportive_loaded_modules.v0133.json",
    [string]$LogDirectory = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_via_live_blocker_adjudication_runs\RUN_20260725_211909_VIA_LIVE_BLOCKER_ADJUDICATE_ACTIVATE_v0133\logs"
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
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
function EnsureDir([string]$Value) { if (-not (Test-Path -LiteralPath $Value)) { New-Item -ItemType Directory -Path $Value -Force | Out-Null } }
EnsureDir $LogDirectory
$events = @()
try {
    $modules = @(Get-Content -LiteralPath $SupportiveListPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    foreach ($module in $modules) {
        $modulePath = [string]$module.path
        $extension = [System.IO.Path]::GetExtension($modulePath).ToLowerInvariant()
        if (-not (Test-Path -LiteralPath $modulePath)) { throw "Supportive module missing: $modulePath" }
        if ($extension -in @(".psm1",".psd1")) {
            Import-Module -Name $modulePath -Force -ErrorAction Stop
            $events += [pscustomobject]@{path=$modulePath;state="IMPORTED_MODULE";success=$true;error=""}
        }
        elseif ($extension -eq ".ps1") {
            $text = Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8
            $dynamicName = "VIA_SAFE_" + ([System.IO.Path]::GetFileNameWithoutExtension($modulePath) -replace '[^A-Za-z0-9_]','_') + "_" + ([guid]::NewGuid().ToString("N").Substring(0,8))
            $dynamicModule = New-Module -Name $dynamicName -ScriptBlock ([scriptblock]::Create($text))
            Import-Module -ModuleInfo $dynamicModule -Force -ErrorAction Stop
            $events += [pscustomobject]@{path=$modulePath;state="IMPORTED_SAFE_DYNAMIC_MODULE";success=$true;error=""}
        }
        else {
            $events += [pscustomobject]@{path=$modulePath;state="REGISTERED_ONLY_NOT_IMPORTABLE";success=$true;error=""}
        }
    }
    $events | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LogDirectory "VRN_supportive_imports.json") -Encoding UTF8
    if (-not (Test-Path -LiteralPath $EntrypointPath)) { throw "Entrypoint missing: $EntrypointPath" }
    Write-Host "def VRN Supportive Modules : IMPORTED" -ForegroundColor Green
    Write-Host "def VRN Entrypoint          : $EntrypointPath" -ForegroundColor Cyan
    & $EntrypointPath
}
catch {
    $events += [pscustomobject]@{path=$EntrypointPath;state="BOOTSTRAP_OR_RUNTIME_ERROR";success=$false;error=$_.Exception.Message}
    $events | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LogDirectory "VRN_supportive_imports.json") -Encoding UTF8
    Write-Host "def VRN ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Host "def VRN PowerShell remains open." -ForegroundColor Cyan
}

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
