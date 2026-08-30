#requires -Version 7.0

param(
    [string]$UnifiedInputSSOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json",
    [string]$Action = "status"
)
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

$ErrorActionPreference = "Stop"

function def_ReadJson {
    param([string]$Path)
    if (-not [System.IO.File]::Exists($Path)) {
        throw "UnifiedInputSSOT missing: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function def_GetProp {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($Object.PSObject.Properties.Name -contains $Name) { return $Object.$Name }
    return $null
}

function def_SafeString {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [string]$Value
}

try {
    $cfg = def_ReadJson $UnifiedInputSSOT

    $paths = def_GetProp $cfg "paths"
    $registries = def_GetProp $cfg "registries"
    $modules = def_GetProp $cfg "modules"
    $outputs = def_GetProp $cfg "outputs"

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA ACTIVATION GATEWAY HARDENED" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Action        : $Action"
    Write-Host "SSOT          : $UnifiedInputSSOT"
    Write-Host "Freeze Status : $(def_SafeString (def_GetProp $cfg 'freeze_status'))"
    Write-Host "Root          : $(def_SafeString (def_GetProp $paths 'root'))"
    Write-Host "NexusCore     : $(def_SafeString (def_GetProp $paths 'nexuscore_entry'))"
    Write-Host "VDF Root      : $(def_SafeString (def_GetProp $paths 'vdf_root'))"
    Write-Host "VRN SSOT Root : $(def_SafeString (def_GetProp $paths 'vrn_ssot_root'))"

    $required = @(
        def_SafeString (def_GetProp $paths 'nexuscore_entry'),
        def_SafeString (def_GetProp $registries 'vdf_nexus_registry_json'),
        def_SafeString (def_GetProp $registries 'vdf_vrn_crosslinks'),
        def_SafeString (def_GetProp $registries 'financial_terms_ssot'),
        def_SafeString (def_GetProp $registries 'financial_regex_ssot'),
        def_SafeString (def_GetProp $registries 'financial_synonym_bidir'),
        def_SafeString (def_GetProp $registries 'financial_verification_rules'),
        def_SafeString (def_GetProp $registries 'financial_crosslinks')
    )

    $missing = New-Object System.Collections.ArrayList

    foreach ($p in $required) {
        if ([string]::IsNullOrWhiteSpace($p) -or -not [System.IO.File]::Exists($p)) {
            [void]$missing.Add($p)
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Host "Missing required files:" -ForegroundColor Red
        foreach ($m in $missing) { Write-Host "  $m" -ForegroundColor Red }
        throw "Activation gateway required files missing."
    }

    if ($Action -eq "status") {
        $vdfModules = @()
        if ($null -ne $modules -and ($modules.PSObject.Properties.Name -contains "vdf_functional_modules")) {
            $vdfModules = @($modules.vdf_functional_modules)
        }

        Write-Host ""
        Write-Host "VDF module count: $(@($vdfModules).Count)" -ForegroundColor Green
        Write-Host "Required registries: OK" -ForegroundColor Green
        Write-Host "Gateway status: READY" -ForegroundColor Green
    }
    elseif ($Action -eq "open-report") {
        $html = def_SafeString (def_GetProp $outputs "html_report")
        if ([System.IO.File]::Exists($html)) {
            Start-Process -FilePath $html | Out-Null
            Write-Host "Opened report: $html" -ForegroundColor Green
        }
        else {
            Write-Host "Report missing: $html" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "Supported actions: status, open-report" -ForegroundColor Yellow
    }

    $global:LASTEXITCODE = 0
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
    $global:LASTEXITCODE = 1
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
