# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0280.ps1 — 2026-11-19:短令整合成幾個 PY 指令(蓋過前版的同名函式;v0279 以前一字不動)
#   操作員令(2026-11-19)「將上述整合成數個 PY 指令導入加速器」(上述 = 212 支短令,30 支沒加速器)。
#   清單正本:supportive modules\registry\VIA_ShortCommand_PyRoute_SSOT_v0101.json(entry 欄:via-vcgc · via-vdf · via-vrn · via-vap)。
#   整合 PY 指令(每步都是帶加速器橋的 PY 尾版;先降壓 → 3~6 道 → 監工;不新增短令名,經既有 via-lanes 跑):
#     via-lanes cmd run vcgc-check    一鍵全檢(唯讀):token → handoff check → test --quick ∥ 加速器自測 ∥ 覆蓋率探針
#                                     (取代 via-all · via-allgreen · via-allinone · via-oneshot · via-realtest · via-review · via-panorama-run 的檢查部分)
#     via-lanes cmd run vcgc-env      環境治理計畫(唯讀 · 離線)(取代 via-envgov-auto · via-envpy 的預設路)
#     via-lanes cmd run vcgc-repair   PS 語法樹掃描 ∥ 合併卡點現況(只看)(取代 via-psrepair · via-unstick 的預設路)
#     via-lanes cmd groups            212 支依入口分組 × 加速器燈 · via-lanes cmd which <短令> 印出背後的 Python
#   舊短令一支都不刪(L117:冊上標 DEPRECATED + replaced_by;寫入步驟照舊叫原短令)。本版只蓋 3 支:
#     via-managers  → CGC_MDL134 cmd run via-managers(原本把 VDF / VRN 管理員釘在 _v0105,沒有加速器橋;改取尾版,只跑它們自己的 --selftest)
#     via-talib · via-taone → 只印退役說明(L50 禁 TA-Lib;目標檔已不在樹上)
#   退回前版:把本檔改名或移走,尾版就回到 v0279(舊的 .ps1 都還在,沒刪)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0279.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:via-managers {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL134_ParallelLanes_v*.py"
    if (-not $eng) { Write-Host "  [via-managers] ABSENT:supportive modules\registry\CGC_MDL134_ParallelLanes_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    Invoke-VIAPython -TimeoutSec (Get-VIALongCap) $eng "cmd" "run" "via-managers" $args
}

function global:via-talib {
    Write-Host "  [via-talib] 已退役(L50:TA-Lib 禁用,只查不裝不刪;技術指標正主 QuantGuard VDF_ENG086)· 看去處:via-lanes cmd which via-talib" -ForegroundColor DarkGray
    $global:LASTEXITCODE = 0
}

function global:via-taone {
    Write-Host "  [via-taone] 已退役(L50:TA-Lib 禁用;技術指標正主 QuantGuard VDF_ENG086)· 看去處:via-lanes cmd which via-taone" -ForegroundColor DarkGray
    $global:LASTEXITCODE = 0
}

Write-Host "  [VIA] Register 尾版 v0280 · 整合 PY 指令:via-lanes cmd run vcgc-check | vcgc-env | vcgc-repair · 分組 via-lanes cmd groups · via-managers 改取三管理員尾版" -ForegroundColor DarkCyan
