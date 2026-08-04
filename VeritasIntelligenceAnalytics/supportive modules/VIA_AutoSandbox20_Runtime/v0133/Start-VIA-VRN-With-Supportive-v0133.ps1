#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EntrypointPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1",
    [string]$SupportiveListPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\supportive_loaded_modules.v0133.json",
    [string]$LogDirectory = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_via_live_blocker_adjudication_runs\RUN_20260725_211909_VIA_LIVE_BLOCKER_ADJUDICATE_ACTIVATE_v0133\logs"
)
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
