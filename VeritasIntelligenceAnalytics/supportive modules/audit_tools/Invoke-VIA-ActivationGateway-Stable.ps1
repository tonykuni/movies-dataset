#requires -Version 7.0

param(
    [string]$UnifiedInputSSOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json",
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

function Get-JsonObject {
    param([string]$Path)
    if (-not [System.IO.File]::Exists($Path)) {
        throw "Unified input SSOT missing."
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Get-PropValue {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return "" }
    if ($Object.PSObject.Properties.Name -contains $Name) {
        return [string]$Object.$Name
    }
    return ""
}

try {
    $cfg = Get-JsonObject -Path $UnifiedInputSSOT
    $paths = $cfg.paths
    $registries = $cfg.registries
    $modules = $cfg.modules

    $root = Get-PropValue -Object $paths -Name "root"
    $nexus = Get-PropValue -Object $paths -Name "nexuscore_entry"
    $vdfRoot = Get-PropValue -Object $paths -Name "vdf_root"
    $vrnSsotRoot = Get-PropValue -Object $paths -Name "vrn_ssot_root"

    $requiredFiles = New-Object System.Collections.ArrayList
    [void]$requiredFiles.Add($nexus)
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "vdf_nexus_registry_json"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "vdf_vrn_crosslinks"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "financial_terms_ssot"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "financial_regex_ssot"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "financial_synonym_bidir"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "financial_verification_rules"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "financial_crosslinks"))
    [void]$requiredFiles.Add((Get-PropValue -Object $registries -Name "financial_period_normalization"))

    $missing = New-Object System.Collections.ArrayList

    foreach ($filePath in $requiredFiles) {
        if ([string]::IsNullOrWhiteSpace($filePath) -or -not [System.IO.File]::Exists($filePath)) {
            [void]$missing.Add($filePath)
        }
    }

    if (-not [System.IO.Directory]::Exists($vdfRoot)) {
        [void]$missing.Add($vdfRoot)
    }

    if (-not [System.IO.Directory]::Exists($vrnSsotRoot)) {
        [void]$missing.Add($vrnSsotRoot)
    }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA ACTIVATION GATEWAY STABLE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Action        : $Action"
    Write-Host "SSOT          : $UnifiedInputSSOT"
    Write-Host "Root          : $root"
    Write-Host "NexusCore     : $nexus"
    Write-Host "VDF Root      : $vdfRoot"
    Write-Host "VRN SSOT Root : $vrnSsotRoot"

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Host "Gateway status: REVIEW" -ForegroundColor Red
        foreach ($m in $missing) {
            Write-Host "Missing: $m" -ForegroundColor Red
        }
        throw "Stable activation gateway found missing required file or directory."
    }

    $moduleCount = 0
    if ($null -ne $modules -and ($modules.PSObject.Properties.Name -contains "vdf_functional_modules")) {
        $moduleCount = @($modules.vdf_functional_modules).Count
    }

    Write-Host ""
    Write-Host "VDF module count: $moduleCount" -ForegroundColor Green
    Write-Host "Required files  : OK" -ForegroundColor Green
    Write-Host "Required folders: OK" -ForegroundColor Green
    Write-Host "Gateway status  : READY" -ForegroundColor Green
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "PowerShell remains open. No exit was called." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
