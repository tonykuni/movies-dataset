# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0279.ps1 — 2026-11-18:舊短指令背後改走 Python · 第一批 4 支(蓋過前版的同名函式;v0278 以前一字不動)
#   操作員令(2026-11-18)「一些舊的短指令背後指令全部要改為 PY 指令,且依照規定也要安裝加速器 × 3~5 步驟同步進行安全進行機制」
#   「跑完後回報燈號,接著列短指令清單分批改成 PY」「自動完成」;道數已統一 3~6。
#   清單正本:supportive modules\registry\VIA_ShortCommand_PyRoute_SSOT_v*.json 尾版(212 支全列;看清單:via-lanes cmd list · 查橋:via-lanes cmd check)。
#   本版只改這 4 支,PS 只留「進環境 + 轉呼叫」,邏輯全在 Python(容器自測過;本檔未在主機 PowerShell 實跑):
#     via-vrnrun        → VRN 自己的啟動器 VRN_MDL260_SafeParallelLaunch 尾版 run(原:Invoke-VIA-VRN-v*.ps1)
#     via-vdffetch      → VDF 自己的啟動器 VDF_MDL022_SafeParallelLaunch 尾版 run(原:Invoke-VIA-VdfFetch-v*.ps1)
#     via-six           → CGC_MDL127_SixStreams 尾版 run(拿掉 --ps 分支;原:--ps 時走 Invoke-VIA-SixStreams-v*.ps1)
#     via-panorama-all  → CGC_MDL134_ParallelLanes 尾版 cmd run via-panorama-all(原:VIA_B535_PANORAMA_ALL_IN_ONE.ps1)
#   兩支啟動器與 cmd run 都自己做「先降壓 → 依機器能力 3~6 道 → 監工過熱減道」;VRN / VDF 的兩支不經 VCGC。
#   退回前版:把本檔改名或移走,尾版就回到 v0278(舊的 .ps1 都還在,沒刪)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0278.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:Get-VIALongCap {
    # 長跑的 python 天花板:你自己設 0(不設限)或 >= 14400 就照你的;其餘給 14400 秒。
    $c = "" + $env:VIA_PY_TIMEOUT_SEC
    if ($c -match '^\d+$') { if (([int]$c -eq 0) -or ([int]$c -ge 14400)) { return [int]$c } }
    return 14400
}

function global:via-vrnrun {
    $a = ConvertTo-VIACleanArgs $args
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_MDL260_SafeParallelLaunch_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnrun] ABSENT:functional modules\VRN\VRN_MDL260_SafeParallelLaunch_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $py = Get-VIAEnvPython "vrn"
    Invoke-VIAPython -Family "vrn" -Python $py -TimeoutSec (Get-VIALongCap) $eng "run" $a
}

function global:via-vdffetch {
    $a = ConvertTo-VIACleanArgs $args
    $eng = Get-VIANewest "$VIA\functional modules\VDF" "VDF_MDL022_SafeParallelLaunch_v*.py"
    if (-not $eng) { Write-Host "  [via-vdffetch] ABSENT:functional modules\VDF\VDF_MDL022_SafeParallelLaunch_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $py = Get-VIAEnvPython "vdf"
    Invoke-VIAPython -Family "vdf" -Python $py -TimeoutSec (Get-VIALongCap) $eng "run" $a
}

function global:via-six {
    $a = @($args | Where-Object { $_ -ne "--ps" })
    if ($args -contains "--ps") { Write-Host "  [via-six] --ps 分支已停用:六流程只走 Python(CGC_MDL127_SixStreams)" -ForegroundColor Yellow }
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL127_SixStreams_v*.py"
    if (-not $eng) { Write-Host "  [via-six] ABSENT:supportive modules\registry\CGC_MDL127_SixStreams_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    Invoke-VIAPython $eng "run" $a
}

function global:via-panorama-all {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL134_ParallelLanes_v*.py"
    if (-not $eng) { Write-Host "  [via-panorama-all] ABSENT:supportive modules\registry\CGC_MDL134_ParallelLanes_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    Invoke-VIAPython -TimeoutSec (Get-VIALongCap) $eng "cmd" "run" "via-panorama-all" $args
}

Write-Host "  [VIA] Register 尾版 v0279 · 短指令改走 Python 第一批 4 支:via-vrnrun · via-vdffetch · via-six · via-panorama-all(清單 via-lanes cmd list;各自先降壓 → 3~6 道 → 監工)" -ForegroundColor DarkCyan
