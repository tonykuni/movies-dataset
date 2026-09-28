#requires -Version 7.0
<#
================================================================================
def Invoke-VIA-MultiFactor-TestValidateSim-v0100.ps1
def Policy: append-only output / no delete / no source mutation / no network / optional HTML open
def Purpose: Launch VIA MultiFactor testing-validating-simulating engine.
================================================================================
#>
param(
    [string]$EnginePath = "$env:USERPROFILE\Downloads\VIA_ENG001_MultiFactorTestValidateSimEngine_v0100.py",
    [string]$SSOTPath = "$env:USERPROFILE\Downloads\SSOT_VPT_ingest.json",
    [string]$OutBase = "$env:USERPROFILE\Downloads\VIA_MF_ENGINE_RUNS",
    [string]$PythonExe = "python",
    [string]$Target = "TARGET_RISK_ASSET",
    [switch]$NoOpen,
    [switch]$KeepPowerShellOpen
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

function def_WriteStep([int]$Pct, [string]$Msg) {
    Write-Progress -Activity "VIA MultiFactor Test Validate Sim" -Status $Msg -PercentComplete $Pct
    Write-Host ("def [{0,3}%] {1}" -f $Pct, $Msg) -ForegroundColor Cyan
}

try {
    def_WriteStep 5 "resolve paths"
    if (-not (Test-Path -LiteralPath $EnginePath)) { throw "ENGINE_NOT_FOUND: $EnginePath" }
    if (-not (Test-Path -LiteralPath $SSOTPath)) { throw "SSOT_NOT_FOUND: $SSOTPath" }
    New-Item -ItemType Directory -Force -Path $OutBase | Out-Null

    def_WriteStep 20 "run python engine append-only"
    $args = @(
        $EnginePath,
        "--ssot", $SSOTPath,
        "--out-base", $OutBase,
        "--target", $Target
    )
    $jsonText = & $PythonExe @args
    if ($LASTEXITCODE -ne 0) { throw "PYTHON_ENGINE_FAILED_EXIT_$LASTEXITCODE" }

    def_WriteStep 80 "parse engine result"
    $result = $jsonText | ConvertFrom-Json
    Write-Host "def EngineStatus : $($result.status)" -ForegroundColor Green
    Write-Host "def RunDir       : $($result.run_dir)" -ForegroundColor White
    Write-Host "def HtmlReport   : $($result.html_report)" -ForegroundColor White
    Write-Host "def HighConfExec : $($result.high_confidence_engine_execution)" -ForegroundColor White

    if (-not $NoOpen -and (Test-Path -LiteralPath $result.html_report)) {
        def_WriteStep 90 "open html report"
        Start-Process -FilePath $result.html_report | Out-Null
    }

    def_WriteStep 100 "complete"
}
catch {
    Write-Host "def FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    throw
}
finally {
    Write-Progress -Activity "VIA MultiFactor Test Validate Sim" -Completed
    if ($KeepPowerShellOpen) {
        Write-Host "def KeepPowerShellOpen enabled. Press Enter to close." -ForegroundColor Yellow
        [void][System.Console]::ReadLine()
    }
}

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
