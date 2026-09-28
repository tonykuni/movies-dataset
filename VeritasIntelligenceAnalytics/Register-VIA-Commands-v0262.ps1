# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0262.ps1 — R30:指令除 TA-Lib。via-talib / via-taone 從舊冊帶上來,這裡拆掉。
# 不刪 v0205–v0207。不裝 TA-Lib。不改禁令守衛。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0261.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
foreach ($name in @("via-talib", "via-taone", "via-ta")) {
    Remove-Item -Path "Function:$name" -ErrorAction SilentlyContinue
}
foreach ($name in @("技術指標", "技術指標引擎")) {
    Remove-Item -Path "Alias:$name" -ErrorAction SilentlyContinue
}
