#requires -Version 7.0
<#
Start-VIA-VDF-v0102 · gate for the v0160B workbench (Veritas design-lock masthead).
v0160B is a style-only version-forward of the hash-locked v0160A canonical — functional
code identical, masthead aligned to the Veritas design source. v0160A and its v0101 gate
remain untouched in the tree for rollback (point bin/via-vdf.cmd back at v0101).
Same fail-closed gate: SHA256 + AST validation, then hand-off.
#>
$ErrorActionPreference = "Stop"

$Base = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Launcher = Join-Path $Base "supportive modules\VIA_Governance_Runtime\v0160B\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160B.ps1"
$ExpectedSHA = "184f5195679715ad0d97a4b08b794c5ac53f784e95298cbc7e3e8de8622d96bc"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "v0160B launcher missing: $Launcher"
}

$ActualSHA = (
    Get-FileHash -LiteralPath $Launcher -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw "v0160B launcher SHA256 mismatch. Expected $ExpectedSHA got $ActualSHA. If this is a fresh checkout, ensure .gitattributes byte-exact rules applied (delete the v0160B folder and 'git checkout -- .' to renormalize)."
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
    throw "v0160B launcher AST validation failed."
}

& $Launcher -Base $Base @args

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
