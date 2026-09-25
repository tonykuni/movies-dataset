#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$GateFile = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\activation_gate.v0133.json",
    [string]$VrnBootstrap = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\Start-VIA-VRN-With-Supportive-v0133.ps1",
    [string]$VdfBootstrap = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\Start-VIA-VDF-With-Supportive-v0133.ps1",
    [string]$PythonPath = "C:\Python313\python.exe",
    [string]$EnginePath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\SUP_MDL114_UnifiedPythonEngine_v0133.py",
    [string]$HtmlReportPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_AutoSandbox20_Runtime\v0133\VIA_LiveBlocker_Adjudication_Activation_Matrix_v0133.html",
    [string]$LauncherLogDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_via_live_blocker_adjudication_runs\RUN_20260725_211909_VIA_LIVE_BLOCKER_ADJUDICATE_ACTIVATE_v0133\logs",
    [int]$UiPort = 8765
)
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
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
function EnsureDir([string]$Value) { if (-not (Test-Path -LiteralPath $Value)) { New-Item -ItemType Directory -Path $Value -Force | Out-Null } }
EnsureDir $LauncherLogDir
$gate = Get-Content -LiteralPath $GateFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$gate.gate -ne "FULL_ACTIVATION_ELIGIBLE") { throw "Activation blocked. Gate=$($gate.gate)" }
$pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$processes = @()
$vrn = Start-Process -FilePath $pwsh -ArgumentList @("-NoLogo","-NoProfile","-NoExit","-ExecutionPolicy","Bypass","-File",$VrnBootstrap) -PassThru
$processes += [pscustomobject]@{subsystem="VRN";pid=$vrn.Id;path=$VrnBootstrap;started_at=(Get-Date).ToString("o")}
$vdf = Start-Process -FilePath $pwsh -ArgumentList @("-NoLogo","-NoProfile","-NoExit","-ExecutionPolicy","Bypass","-File",$VdfBootstrap) -PassThru
$processes += [pscustomobject]@{subsystem="VDF";pid=$vdf.Id;path=$VdfBootstrap;started_at=(Get-Date).ToString("o")}
if ((Test-Path -LiteralPath $PythonPath) -and (Test-Path -LiteralPath $EnginePath)) {
    $ui = Start-Process -FilePath $PythonPath -ArgumentList @($EnginePath,"--serve-root",(Split-Path -Parent $HtmlReportPath),"--port",$UiPort) -PassThru
    $processes += [pscustomobject]@{subsystem="PYTHON_UI";pid=$ui.Id;path=$EnginePath;started_at=(Get-Date).ToString("o")}
    Start-Sleep -Milliseconds 900
    $url = "http://127.0.0.1:$UiPort/" + [uri]::EscapeDataString((Split-Path -Leaf $HtmlReportPath))
    Start-Process -FilePath $url
}
else {
    Start-Process -FilePath $HtmlReportPath
}
$processes | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LauncherLogDir "activation_processes.json") -Encoding UTF8
Write-Host "def Gate              : FULL_ACTIVATION_ELIGIBLE" -ForegroundColor Green
Write-Host "def VRN               : STARTED AFTER SUPPORTIVE IMPORT" -ForegroundColor Green
Write-Host "def VDF               : STARTED AFTER SUPPORTIVE IMPORT" -ForegroundColor Green
Write-Host "def HTML UI           : STARTED NON-BLOCKING" -ForegroundColor Green
Write-Host "def Launcher remains open; child systems continue independently." -ForegroundColor Cyan

