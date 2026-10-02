# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0267.ps1 — 側線 2026-10-02:+via-tools(別名 工具盤點)· +via-cmds(別名 短令清單)。
#   操作員令「給我一個進入環境指令及本系統近期常用的短指令清單與顯示 … 自動用目前的全景式工具 自動檢查注入 AST 搭配自動編號及分類及說明
#   及子系統及來源 導入 PY 加速器 · VDF 導入網路工具 · PS 導入最強模板 HTML U/I」= L70 這一次的許可:只加這兩件;v0266 以前一字不動。
#   via-tools [路徑 …] [--all-versions] [--no-open] [--json]
#     = via-vcgc run CGC_MDL253_ToolingInventory scan:全景 AST(鎖版 CGC_MDL158)+ 中央編號冊 + 短令冊 + L103 三導入 → VIA_Reports\tooling\TOOLING_latest.html(自動開)
#   via-tools card <檔>    單支一張卡(編號 · 子系統 · 分類 · 說明 · 來源 · 入口 · 旗標 · 短令 · L103 · AST 錨點 · 函數)
#   via-cmds [--recent N] [--json]
#     = 短令冊:Register 尾版**順點源鏈**往回讀(via-help 只讀尾版一支,v0266 起只看得到 1 個),新增的在前;--recent 0 = 全部。
#   進入環境照舊:via-in(別名 進入環境)。獨立用(沒點源命令冊)跑 .\Inspect-VIA-Tooling-v0100.ps1。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0266.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:via-tools {
    if ($args.Count -ge 1 -and ("" + $args[0]) -eq 'card') { via-vcgc run CGC_MDL253_ToolingInventory @args; return }
    via-vcgc run CGC_MDL253_ToolingInventory scan @args
}
function global:via-cmds { via-vcgc run CGC_MDL253_ToolingInventory cmds @args }
Set-Alias -Name 工具盤點 -Value via-tools -Scope Global -Force
Set-Alias -Name 短令清單 -Value via-cmds -Scope Global -Force
