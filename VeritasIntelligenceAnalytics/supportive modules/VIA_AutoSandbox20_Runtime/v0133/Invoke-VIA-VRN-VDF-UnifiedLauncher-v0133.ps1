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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
