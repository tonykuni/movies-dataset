#requires -Version 7.0
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
[CmdletBinding()]
param(
    [string]$EntrypointPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VDF.ps1",
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
    $events | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LogDirectory "VDF_supportive_imports.json") -Encoding UTF8
    if (-not (Test-Path -LiteralPath $EntrypointPath)) { throw "Entrypoint missing: $EntrypointPath" }
    Write-Host "def VDF Supportive Modules : IMPORTED" -ForegroundColor Green
    Write-Host "def VDF Entrypoint          : $EntrypointPath" -ForegroundColor Cyan
    & $EntrypointPath
}
catch {
    $events += [pscustomobject]@{path=$EntrypointPath;state="BOOTSTRAP_OR_RUNTIME_ERROR";success=$false;error=$_.Exception.Message}
    $events | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LogDirectory "VDF_supportive_imports.json") -Encoding UTF8
    Write-Host "def VDF ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Host "def VDF PowerShell remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
