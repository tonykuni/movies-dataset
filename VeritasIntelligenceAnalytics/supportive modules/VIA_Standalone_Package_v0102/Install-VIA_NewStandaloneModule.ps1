#requires -Version 7.0
param(
    [switch]$ApplyUserPath,
    [switch]$ReviewOnly
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

# =============================================================================
# def PARAMETERS
# =============================================================================
$def_PARAM_PackageDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$def_PARAM_BinDir = Join-Path $def_PARAM_PackageDir "bin"
$def_PARAM_RegistryDir = Join-Path $def_PARAM_PackageDir "_registry"

# =============================================================================
# def HELPERS
# =============================================================================
function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_WriteInstallRegistry {
    def_EnsureDir -Path $def_PARAM_RegistryDir

    $payload = @{
        def_schema = "VIA_STANDALONE_INSTALL_REGISTRY_v0105"
        def_product_name = "VIA_NewStandaloneModule"
        def_product_version = "0.1.0"
        def_package_dir = $def_PARAM_PackageDir
        def_bin_dir = $def_PARAM_BinDir
        def_apply_user_path = [bool]$ApplyUserPath
        def_installed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }

    $path = Join-Path $def_PARAM_RegistryDir "InstallRegistry_v0105.json"
    $payload | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $path -Encoding UTF8
    Write-Host "[OK] Install registry: $path" -ForegroundColor Green
}

function def_AddUserPath {
    param([string]$PathToAdd)

    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @($current -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

    if ($parts -contains $PathToAdd) {
        Write-Host "[OK] PATH already has: $PathToAdd" -ForegroundColor Green
        return
    }

    $new = (($parts + $PathToAdd) -join ";")
    [Environment]::SetEnvironmentVariable("Path", $new, "User")
    Write-Host "[OK] User PATH added: $PathToAdd" -ForegroundColor Green
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · STANDALONE PACKAGE INSTALLER · VIA_NewStandaloneModule v0105" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_EnsureDir -Path $def_PARAM_BinDir
    def_WriteInstallRegistry

    if ($ApplyUserPath) {
        def_AddUserPath -PathToAdd $def_PARAM_BinDir
        def_AddUserPath -PathToAdd $def_PARAM_PackageDir
    } else {
        Write-Host "[REVIEW] User PATH not changed." -ForegroundColor Yellow
        Write-Host "[PLAN] Add PATH if needed:" -ForegroundColor Cyan
        Write-Host "       $def_PARAM_BinDir" -ForegroundColor Cyan
        Write-Host "       $def_PARAM_PackageDir" -ForegroundColor Cyan
    }

    Write-Host "PowerShell remains open." -ForegroundColor Cyan
} catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host "PowerShell remains open." -ForegroundColor Yellow
}

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
