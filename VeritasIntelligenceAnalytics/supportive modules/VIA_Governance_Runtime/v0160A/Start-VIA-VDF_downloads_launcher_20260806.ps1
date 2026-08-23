#requires -Version 7.0
$ErrorActionPreference = "Stop"

$Launcher = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0160A\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160A.ps1"
$ExpectedSHA = "778ced5d0c127d61a8d104bfcca77bcb1a6597e010b12dda80d7c23d1e43f021"
$Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Canonical VDF launcher missing: $Launcher"
}

$ActualSHA = (
    Get-FileHash -LiteralPath $Launcher -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw "Canonical VDF launcher SHA256 mismatch."
}

$Tokens = $null
$Errors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $Launcher,
    [ref]$Tokens,
    [ref]$Errors
) | Out-Null

if (@($Errors).Count -gt 0) {
    $Errors | Format-Table -AutoSize -Wrap
    throw "Canonical VDF launcher AST validation failed."
}

& $Launcher -Base $Base

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
