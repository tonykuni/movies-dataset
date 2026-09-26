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
    (Join-Path $reg "CGC_MDL198_Closeout_v0100.py")
)
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
foreach ($py in $steps) {
    & python $py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
}
foreach ($py in @(
    (Join-Path $via "functional modules\VDF\VDF_SystemManager_v0105.py"),
    (Join-Path $via "functional modules\VRN\VRN_SystemManager_v0105.py")
)) {
    & python $py --selftest
    if ($LASTEXITCODE -ne 0) {
        Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
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
exit $LASTEXITCODE
