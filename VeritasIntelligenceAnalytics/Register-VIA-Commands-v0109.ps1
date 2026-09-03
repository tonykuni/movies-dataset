# =====================================================================
# Register-VIA-Commands-v0108.ps1 — VIA 短指令唯一定義處(批254 立;批260 +via-all;批316 +via-pipeline;批323 +via-accel/via-accel-check;批325 +via-rotation/via-repo-optimize)
# =====================================================================
# 批254 摩擦修:舊制=Register-Profile 把函式全文塞 $PROFILE(要跑 via
# +開新視窗+每加一指令就 v010x 重貼)。新制=點源架構:
#   ①本檔=十指令唯一定義處(global 域;git pull 即最新)
#   ②$PROFILE 只留一行點源(VIA.ps1 自動補;舊 v010x 段無害,點源
#     在後=後定義勝)
#   ③當場生效:. "<本檔路徑>"(不用新視窗不用 via)
# =====================================================================
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path

function global:Get-VIANewest([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}

function global:regen-all { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL096_SyncStatus_v*.py") --regen-all }
function global:via { powershell -NoProfile -ExecutionPolicy Bypass -File "$VIA\VIA.ps1" }
function global:via-status { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL096_SyncStatus_v*.py") --open }
function global:via-selftest { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL064_SelftestGrid_v*.py") @args }
function global:selftest { via-selftest @args }
function global:via-intake { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Collect-VIA-Intake-v*.ps1") @args }
function global:via-help { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL102_CommandRoster_v*.py") --print }
function global:via-md { python (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG075_DocToMarkdown_v*.py") run @args }
function global:via-prompt { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL109_PromptManager_v*.py") @args }
function global:via-analysis { python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG068_ETFConsensusAnalysis_v*.py") run; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG069_RevenueConsensusAnalysis_v*.py") run }
function global:via-manager { python (Get-VIANewest "$VIA" "VIA_SYSTEM_MANAGER_v*.py") @args }
function global:via-rootcheck { & cmd /c "$VIA\VIA-ROOTCHECK.cmd" }
function global:via-tower-reset { & cmd /c "$VIA\VIA-TOWER-RESET.cmd" }
function global:via-ssot { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL115_SSOTRegexDict_v*.py") @args }
function global:via-register { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL113_UnifiedRegistry_v*.py") @args }
function global:via-health { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL114_CommandCenterBridge_v*.py") run }
function global:via-tpn { python (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG011_TemplateRegistry_v*.py") @args }
function global:via-psrepair { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-PSRepair-v*.ps1") @args }
function global:via-all { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-All-v*.ps1") @args }
# 批323:加速器啟動報告(SUP_MDL737 尾版 --activate/--libs)+覆蓋×啟動稽核(CGC_MDL117)
function global:via-accel { python (Get-VIANewest "$VIA\supportive modules" "SUP_MDL737_SuperAccelModule_v*.py") $(if ($args) { $args } else { "--activate" }) }
function global:via-accel-check { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL117_AccelCoverage_v*.py") run }
# 批325:故事族群輪動橋接(ENG072 尾版;run 預設,可帶 export/preflight/--pkgtest)+repo 衛生一鍵(只宜工作站)
function global:via-rotation { python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG072_StoryRotationBridge_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-repo-optimize { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-RepoOptimizer-v*.ps1") @args }
# 批316:族群分類一鍵管線(補料→ENG070 自測+run→ENG071 自測+run→開頁;pwsh 缺退 powershell)
function global:via-pipeline { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-GroupPipeline-v*.ps1") @args }

# --- 自註冊:$PROFILE 補一行點源(冪等;標記 v0200) -------------------
try {
    # 批260:profile 行改尾版 glob(v0200 曾寫死 v0100 路徑=新版不自動吃)
    $mark = "# [VIA:PROFILE:v0201] 點源尾版(pull 即最新;永久免重貼)"
    if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
    if (-not (Select-String -Path $PROFILE -Pattern "VIA:PROFILE:v0201" -Quiet -ErrorAction SilentlyContinue)) {
        $dir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $line = '. (Get-ChildItem "' + $dir + '\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
        @("", $mark, $line) | Add-Content -Path $PROFILE -Encoding UTF8
        Write-Host "  [註冊] profile 點源一行已入(以後 pull 即自動最新)" -ForegroundColor Green
    }
} catch { }
Write-Host "  [VIA] 短指令已生效於本視窗:regen-all/via/via-status/selftest/via-intake/via-help/via-md/via-tpn/via-psrepair/via-all/via-prompt/via-analysis/via-manager/via-rootcheck/via-tower-reset/via-ssot/via-register/via-health/via-pipeline/via-accel/via-accel-check/via-rotation/via-repo-optimize" -ForegroundColor Cyan
