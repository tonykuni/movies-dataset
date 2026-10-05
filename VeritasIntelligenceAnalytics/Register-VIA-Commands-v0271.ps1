# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0271.ps1 — 2026-10-05:+via-precheck(別名 via_precheck · 總檢)
#   操作員令「設一個短令 via_precheck 動用 VCGC 所有功能 · 每個編號分類說明 · 加速 / 網路覆蓋 100% · 有編號就有註冊 ·
#   全景分析檢查所有引擎綠燈 · 黃紅燈先定位定點修」(VCGC-REQ167)= L70 這一次的許可:只加這一件;v0270 以前一字不動。
#   L113(PS 骨架律)裁定:被點源的函式庫豁免骨架,仍帶兩章(L106)。
#   本體在 Python(CGC_MDL263_Precheck):14 站 → 每個黃 / 紅給 PC-### 編號 · 類 · 說明 · 檔:行 · 歸屬 · 下一步;
#   報告 VIA_Reports\precheck\PRECHECK_latest.json(不進 git)。rc:0 全綠 · 2 有黃 · 1 有紅。
#   via-precheck [--only 站,站] [--skip 站,站] [--json]
#   站名:token bridge celer ast sync number ssot sdd handoff test rungate_vdf rungate_vrn rungate_vap matrix accel temp
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0270.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:via-precheck {
    # 不加引號的 token,bridge 在 PS 是陣列:攤平回逗號字串(L112 三檢:RunGate 同一坑)
    $a = @($args | ForEach-Object { if ($_ -is [array]) { ($_ | ForEach-Object { "$_" }) -join ',' } else { "$_" } })
    Write-Host ("  [via-precheck] CGC_MDL263_Precheck " + ($a -join ' ')) -ForegroundColor Cyan
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) {
        Invoke-VIACeleritasScoped { via-vcgc run CGC_MDL263_Precheck @a }
    } else {
        via-vcgc run CGC_MDL263_Precheck @a
    }
    $rc = [int]$global:LASTEXITCODE
    $rep = Join-Path (Split-Path -Parent $global:VIARegisterPath) "VIA_Reports\precheck\PRECHECK_latest.json"
    if (Test-Path -LiteralPath $rep) { Write-Host ("  [via-precheck] 報告 " + $rep) -ForegroundColor Gray }
    $global:LASTEXITCODE = $rc
}
Set-Alias -Name via_precheck -Value via-precheck -Scope Global -Force
Set-Alias -Name 總檢 -Value via-precheck -Scope Global -Force
