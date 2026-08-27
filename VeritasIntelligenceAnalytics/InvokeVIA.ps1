#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# =============================================================================
# VIA v035.7 Guarded Root Entry
# Project   : VIA
# Candidate : C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-UltimateEngineForge-AIO-v060.ps1
# =============================================================================
# Default behavior is SAFE PROBE only.
# Full run requires explicit -Run.
# =============================================================================

param(
    [switch]$Run,
    [switch]$SafeProbe,
    [switch]$Plan
)

$SelectedCandidate = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-UltimateEngineForge-AIO-v060.ps1"
$ExpectedEntry = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VIA.ps1"

function Write-GuardedLine {
    param([string]$Level,[string]$Message)
    $c="Gray"
    if($Level -eq "OK"){$c="Green"}
    elseif($Level -eq "WARN"){$c="Yellow"}
    elseif($Level -eq "FAIL"){$c="Red"}
    elseif($Level -eq "RUN"){$c="Cyan"}
    Write-Host "[$(Get-Date -Format 'HH:mm:ss.fff')] [$Level] $Message" -ForegroundColor $c
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA v035.7 · VIA Guarded Root Entry" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if(-not(Test-Path -LiteralPath $SelectedCandidate -PathType Leaf)){
    Write-GuardedLine "FAIL" "Selected candidate missing: $SelectedCandidate"
    return
}

try {
    $tokens=$null
    $errors=$null
    [System.Management.Automation.Language.Parser]::ParseFile($SelectedCandidate,[ref]$tokens,[ref]$errors)|Out-Null

    if(@($errors).Count -eq 0){
        Write-GuardedLine "OK" "Candidate parser OK."
    } else {
        Write-GuardedLine "FAIL" "Candidate parser errors: $(@($errors).Count)"
        @($errors | Select-Object -First 10) | ForEach-Object { Write-GuardedLine "FAIL" $_.Message }
        return
    }

    $item=Get-Item -LiteralPath $SelectedCandidate -Force
    $hash=(Get-FileHash -LiteralPath $SelectedCandidate -Algorithm SHA256).Hash
    Write-GuardedLine "OK" "Candidate bytes: $($item.Length)"
    Write-GuardedLine "OK" "Candidate SHA256: $hash"
} catch {
    Write-GuardedLine "FAIL" $_.Exception.Message
    return
}

if($Plan -or -not $Run){
    Write-GuardedLine "OK" "SAFE_PROBE_COMPLETE"
    Write-GuardedLine "WARN" "Default mode does not execute candidate. Use -Run only after production approval."
    Write-GuardedLine "WARN" "Expected entry: $ExpectedEntry"
    return
}

Write-GuardedLine "RUN" "Explicit -Run detected. Invoking selected candidate."
& pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $SelectedCandidate @args

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
