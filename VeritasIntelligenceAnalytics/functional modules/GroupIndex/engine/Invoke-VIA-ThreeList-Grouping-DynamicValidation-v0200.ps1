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
    [string]$PythonExe = "python",
    [string]$EnginePath = (Join-Path $PSScriptRoot "VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py"),
    [string]$TestPath = (Join-Path $PSScriptRoot "test_VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py"),
    [string]$RunTag = "RUN_FINAL_V0200",
    [int]$OpenHtml = 1,
    [int]$KeepOpen = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function def_WriteBanner {
    param([string]$Title)
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
}

function def_WriteStep {
    param([int]$Percent, [string]$Message, [string]$Status = "INFO")
    $filled = [Math]::Max(0, [Math]::Min(20, [Math]::Floor($Percent / 5)))
    $bar = ("█" * $filled) + ("░" * (20 - $filled))
    Write-Host ("def [{0,3}%] [{1}] [{2}] {3}" -f $Percent, $bar, $Status, $Message)
}

function def-InvokeChecked {
    param([string]$Label, [string[]]$Arguments)
    def_WriteStep -Percent 25 -Message $Label
    & $PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function def-Main {
    def_WriteBanner "VERITAS INTELLIGENCE ANALYTICS · THREE-LIST DYNAMIC VALIDATION v0200"

    if (-not (Test-Path -LiteralPath $EnginePath)) {
        throw "Engine not found: $EnginePath"
    }
    if (-not (Test-Path -LiteralPath $TestPath)) {
        throw "Test file not found: $TestPath"
    }

    def_WriteStep -Percent 8 -Message "Python compile gate"
    & $PythonExe -m py_compile $EnginePath
    if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }

    def_WriteStep -Percent 20 -Message "Unit / governance tests"
    & $PythonExe -m pytest -q -W error $TestPath
    if ($LASTEXITCODE -ne 0) { throw "Pytest failed" }

    def_WriteStep -Percent 40 -Message "Full test-debug-optimize-consolidate-backtest-user-test-activate pipeline"
    & $PythonExe $EnginePath --run-tag $RunTag
    if ($LASTEXITCODE -ne 0) { throw "Full pipeline failed" }

    $RunDirCandidates = @(
        (Join-Path $PSScriptRoot $RunTag),
        (Join-Path (Join-Path $PSScriptRoot "runs") $RunTag)
    )
    $RunDir = $RunDirCandidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ "run_summary.json") } | Select-Object -First 1
    if (-not $RunDir) { throw "Run directory not found for tag: $RunTag" }

    def_WriteStep -Percent 78 -Message "Activation and manifest verification"
    $Activation = Get-Content -LiteralPath (Join-Path $RunDir "activation_status.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $Summary = Get-Content -LiteralPath (Join-Path $RunDir "run_summary.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Activation.Status -notlike "CONTROLLED_ACTIVATION_PASS*") {
        throw "Activation blocked: $($Activation.Status)"
    }
    if (-not $Summary.ManifestVerified) {
        throw "Manifest verification failed"
    }

    def_WriteStep -Percent 94 -Message "User report ready" -Status "PASS"
    $Html = Join-Path $RunDir "index.html"
    Write-Host "def Final Gate : $($Summary.FinalGate)" -ForegroundColor Green
    Write-Host "def Run Dir    : $RunDir" -ForegroundColor White
    Write-Host "def HTML       : $Html" -ForegroundColor White

    if ($OpenHtml -eq 1 -and (Test-Path -LiteralPath $Html)) {
        Start-Process -FilePath $Html
    }

    def_WriteStep -Percent 100 -Message "All governed phases completed" -Status "PASS"
}

try {
    def-Main
}
catch {
    Write-Host "def FAIL : $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    if ($KeepOpen -eq 1) {
        Write-Host "def PowerShell remains open. Press Enter to finish." -ForegroundColor Yellow
        [void](Read-Host)
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
