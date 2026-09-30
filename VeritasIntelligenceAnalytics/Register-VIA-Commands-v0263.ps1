# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0263.ps1 — 側線 2026-09-29 g:+via-in(別名 進入環境)—— 進倉 + VCGC 入口流程一句完成。
#   操作員令「加 via-in 短令到命令冊 v0263」= L70 這一次的許可:只加這一個短令;v0262 以前一字不動。
#   via-in [enter 的參數 …]
#     = via-entry(進 $VIA、設環境;$VIA 在倉內,之後 git push 不會再報 not a git repository)
#     → via-vcgc enter(VCGC v0173:第一步 → 只快轉的更新 → 閘 → 加速器 → 工具版本 → 交給 go 跑整輪)。
#   例:via-in · via-in --card(只出卡不啟動)· via-in --no-pull(不更新)· via-in -Full -NoOpen(照傳給 go)。
#   逾時:整輪常超過 Invoke-VIAPython 預設 1800 秒 —— VIA_PY_TIMEOUT_SEC 沒設、不是數字、或比 7200 小時,
#   本次放寬到 7200,結束還原;設 0(不設限)或 ≥ 7200 就照你的。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0262.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-in {
    if (-not $VIA -or -not (Test-Path -LiteralPath $VIA)) { Write-Host "  [via-in] FAIL:`$VIA 不在(先點源命令冊)" -ForegroundColor Red; $global:LASTEXITCODE = 2; return }
    via-entry
    $prevTimeout = $env:VIA_PY_TIMEOUT_SEC
    $cap = 0
    $raise = (-not [int]::TryParse(("" + $prevTimeout), [ref]$cap)) -or ($cap -gt 0 -and $cap -lt 7200)
    if ($raise) {
        $env:VIA_PY_TIMEOUT_SEC = "7200"
        Write-Host "  [via-in] 本次逾時放寬到 7200 秒(整輪常超過 1800 秒;結束還原)" -ForegroundColor DarkGray
    }
    try { via-vcgc enter @args }
    finally { if ($raise) { $env:VIA_PY_TIMEOUT_SEC = $prevTimeout } }
}
Set-Alias -Name 進入環境 -Value via-in -Scope Global -Force
