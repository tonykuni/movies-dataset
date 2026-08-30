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
$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · Run All Sandbox Adapter Smoke · v0110" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
$rows = @()

Write-Host '[RUN] VDF' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VDF\Invoke-VIA_VDF_SandboxSmoke_v0110.ps1'
    $rows += [pscustomobject]@{ Project='VDF'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VDF\Invoke-VIA_VDF_SandboxSmoke_v0110.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VDF'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VDF\Invoke-VIA_VDF_SandboxSmoke_v0110.ps1'; Message=$_.Exception.Message }
}

Write-Host '[RUN] VIA' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\Invoke-VIA_VIA_SandboxSmoke_v0110.ps1'
    $rows += [pscustomobject]@{ Project='VIA'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\Invoke-VIA_VIA_SandboxSmoke_v0110.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VIA'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\Invoke-VIA_VIA_SandboxSmoke_v0110.ps1'; Message=$_.Exception.Message }
}

Write-Host '[RUN] VRN' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\Invoke-VIA_VRN_SandboxSmoke_v0110.ps1'
    $rows += [pscustomobject]@{ Project='VRN'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\Invoke-VIA_VRN_SandboxSmoke_v0110.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VRN'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\Invoke-VIA_VRN_SandboxSmoke_v0110.ps1'; Message=$_.Exception.Message }
}

$out = Join-Path (Split-Path -Parent $PSCommandPath) "VIA_RunAllSandboxSmoke_Result_v0110.csv"
$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8
Write-Host "[OK] Result: $out" -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
