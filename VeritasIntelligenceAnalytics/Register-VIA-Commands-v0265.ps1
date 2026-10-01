# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0265.ps1 — R42(2026-10-01):+via-realtest(別名 實測)。
#   操作員令「請寫成短指令 via_realtest … 25個加速器 動態進度條 動態百分比 自動跳出報告」= L70 這一次的許可:只加這一件;v0264 以前一字不動。
#   via-realtest [-Resume] [-NoOpen] [-SkipGate] [-StallSec 240] [-MaxMin 60]
#     = Invoke-VIA-RealTest 尾版:25 PS 加速器 + Celeritas PS7 模板 → VCGC 閘 → VDF 鏈 ∥ VRN 鏈 ∥ 工具覆蓋(三條並行 · 各一條動態進度條與百分比 ·
#       停滯提示 · 整體上限看門狗)→ 三合一矩陣頁 + VDF 鏈矩陣 + VRN 鏈證據 + 工具覆蓋矩陣自動跳出(走瀏覽器,不讓 VS Code 開)。
#     via_realtest(底線寫法)同一支。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0264.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:via-realtest {
    $vroot = Split-Path -Parent $global:VIARegisterPath
    $rt = Get-ChildItem -LiteralPath $vroot -Filter "Invoke-VIA-RealTest-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if (-not $rt) { Write-Host "  [via-realtest] 找不到 Invoke-VIA-RealTest-v*.ps1(先 git pull)" -ForegroundColor Red; return }
    & $rt.FullName @args
}
Set-Alias -Name via_realtest -Value via-realtest -Scope Global -Force
Set-Alias -Name 實測 -Value via-realtest -Scope Global -Force
