#Requires -Version 7.0
# [批394 T3 真缺陷修]param 區塊原在 L24(加速器橋/Set-StrictMode 等可執行語句之後)=不在合法位置,
# PowerShell 遂把 param(...) 當『指令呼叫』(實測 InvalidOperation: called as if it were a method),
# 導致 -Run/-SafeProbe/-Plan 三開關永遠無法綁定 → 真跑路徑完全不可達(只能跑 SAFE PROBE)。
# 檔案解析仍綠,故 T1 AST 解析閘與 MDL145 皆看不到;唯 T3 CommandAst 檢查抓得到。
# 修法=param 區塊上移至 #Requires 之後(PowerShell 要求 param 為首個語句);語意零變更。
param(
    [switch]$Run,
    [switch]$SafeProbe,
    [switch]$Plan
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

