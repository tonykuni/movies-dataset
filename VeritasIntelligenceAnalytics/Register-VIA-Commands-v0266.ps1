# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0266.ps1 — R49(2026-10-02):+via-review(別名 總檢)。
#   操作員令「整合成一次完整快速檢視系統狀態的工具 … all in one ps to review all 錯誤都要標註 ast 精準或彈性定位點」= L70 這一次的許可:只加這一件;v0265 以前一字不動。
#   via-review [-Install] [-Sync] [-Lists] [-Optimize] [-NoOpen] [-NoClipboard] [-Since yyyy-MM-dd] [-Dry]
#     = Invoke-VIA-Review 尾版:① Git 整合檢視(唯讀;-Sync 才交 MergeMedic)② 撞名閘 MDL165 ③ 環境 MDL240 check(-Install 才接 MDL135 → MDL137 補裝)
#       ④ sdd check + ssot panorama + 受控 .py 無編號 / 未註冊 = 紅 ⑤ 全景 AST 錨點(PAN-SCAN / PAN-READ / PS Parser;每條錯誤標 AST精準 / 彈性 / 行程)
#       ⑥ -Lists 清單七步(v0108 原表)⑦ -Optimize 全部優化一回(RealTestCore 尾版)⑧ 多頁矩陣 HTML 自動開 + 貼回包進剪貼簿。
#     v0105 起同一個指令再併 VIA-VERB-ENGINE 五支入口(⑨ health · global_read · fullcheck · 收尾鎖;-VerbEngine <夾> · -NoVerb)—— 指令整合為一。
#     via_review(底線寫法)同一支。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0265.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:via-review {
    $vroot = Split-Path -Parent $global:VIARegisterPath
    $rv = Get-ChildItem -LiteralPath $vroot -Filter "Invoke-VIA-Review-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if (-not $rv) { Write-Host "  [via-review] 找不到 Invoke-VIA-Review-v*.ps1(先 git pull)" -ForegroundColor Red; return }
    & $rv.FullName @args
}
Set-Alias -Name via_review -Value via-review -Scope Global -Force
Set-Alias -Name 總檢 -Value via-review -Scope Global -Force
