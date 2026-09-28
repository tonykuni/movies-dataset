#requires -Version 7.0

param(
    [string]$UnifiedInputSSOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json",
    [string]$Action = "status"
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

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
