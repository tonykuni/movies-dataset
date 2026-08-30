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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
