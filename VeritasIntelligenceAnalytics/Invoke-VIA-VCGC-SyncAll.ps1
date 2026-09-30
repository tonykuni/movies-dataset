# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# ===== [VIA:PS-TEMPLATE:v0100] Celeritas 模板章(L102 ②;不包裹接法 L103 ③:不 cd、不動 param()、只動 $PID、關閉即還原;模板 StrictMode 不外溢) =====
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
try {
    $VIACelProbe = $PSScriptRoot
    while ($VIACelProbe -and (Split-Path $VIACelProbe -Parent)) {
        $VIACelPS7 = Join-Path $VIACelProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
        if (Test-Path -LiteralPath $VIACelPS7) { . $VIACelPS7 -RestoreOnly; break }
        $VIACelProbe = Split-Path $VIACelProbe -Parent
    }
    Set-StrictMode -Off
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
        if (-not (Get-EventSubscriber -SourceIdentifier PowerShell.Exiting -ErrorAction SilentlyContinue)) { $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { try { Restore-CeleritasPS7 } catch { } } }
        [void](Start-CeleritasPS7)
    }
} catch { }
# ===== [VIA:PS-TEMPLATE:END] =====
#Requires -Version 7.0
# 依序：本倉 autocrlf、參數雜湊、知識資產、狀態鎖、探測鎖、行情鎖、前瞻鎖、三管理器。不套用 registry，不改母冊。
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $via
Set-Location -LiteralPath $root
git config core.autocrlf true
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Set-Location -LiteralPath $via
$env:VIA_FROM_VCGC = "YES"
$reg = Join-Path $via "supportive modules/registry"
$steps = @(
    (Join-Path $reg "CGC_MDL192_MacroParamSync_v0101.py"),
    (Join-Path $reg "CGC_MDL191_KnowledgeAsset_v0100.py"),
    (Join-Path $reg "CGC_MDL193_StatusLock_v0105.py"),
    (Join-Path $reg "CGC_MDL193_ProbeLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_MarketSync_v0101.py"),
    (Join-Path $reg "CGC_MDL193_ForwardVintageLock_v0101.py"),
    (Join-Path $reg "CGC_SystemManager_v0100.py"),
    (Join-Path $reg "CGC_MDL193_VrnTabLock_v0101.py"),
    (Join-Path $reg "CGC_MDL193_TabFieldLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_GateMapLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_ReportMeasureLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_ReportMeasureLock_v0101.py"),
    (Join-Path $reg "CGC_MDL197_NlpOneEngine_v0100.py"),
    (Join-Path $reg "CGC_MDL197_NlpRoster_v0100.py"),
    (Join-Path $reg "CGC_MDL193_AuditFixLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_ReportWireLock_v0100.py"),
    (Join-Path $reg "CGC_MDL198_Closeout_v0100.py"),
    (Join-Path $reg "CGC_MDL193_StockIdentityLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_BrokerMarketLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_BrokerShowLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_FinancialReadLock_v0100.py"),
    (Join-Path $reg "CGC_MDL193_FinancialShownLock_v0100.py"),
    (Join-Path $reg "CGC_MDL199_SupportTier_v0100.py"),
    (Join-Path $reg "CGC_MDL199_NlpUses_v0100.py"),
    (Join-Path $reg "CGC_MDL200_RelatedIntake_v0100.py"),
    (Join-Path $reg "CGC_MDL201_VrnManagerRead_v0100.py"),
    (Join-Path $reg "CGC_MDL202_LayoutEngine_v0100.py"),
    (Join-Path $reg "CGC_MDL203_LayoutCodes_v0101.py"),
    (Join-Path $reg "CGC_MDL204_NlpCodes_v0100.py"),
    (Join-Path $reg "CGC_MDL205_TalibBan_v0100.py"),
    (Join-Path $reg "CGC_MDL206_TalibPolicy_v0101.py"),
    (Join-Path $reg "CGC_MDL207_PolicyRun_v0101.py"),
    (Join-Path $reg "CGC_MDL208_VdfMeasure_v0100.py")
)
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
foreach ($py in $steps) {
    & python $py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
        if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
        exit $LASTEXITCODE
    }
}
foreach ($py in @(
    (Join-Path $via "functional modules\VDF\VDF_SystemManager_v0105.py"),
    (Join-Path $via "functional modules\VRN\VRN_SystemManager_v0105.py"),
    (Join-Path $via "functional modules\VRN\VRN_SystemManager_v0106.py")
)) {
    & python $py --selftest
    if ($LASTEXITCODE -ne 0) {
        Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
        if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
        exit $LASTEXITCODE
    }
}
$refresh = Join-Path $via "functional modules/VDF/engine/VDF_ENG113_MacroMethod_v0101.py"
if ([string]::IsNullOrWhiteSpace($env:FRED_API_KEY)) {
    Write-Host '{"via":"vcgc","refresh":"SKIP","why":"FRED_API_KEY is not set"}'
} else {
    & python $refresh --refresh
}
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
exit $LASTEXITCODE
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
