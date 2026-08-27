#requires -Version 7.0
[CmdletBinding()]
param([string]$AppRoot = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference="Stop"
Set-Location $AppRoot
$Candidates=@(
    (Join-Path (Split-Path -Parent $AppRoot) "venv\Scripts\python.exe"),
    "C:\Python313\python.exe",
    "C:\Python312\python.exe"
)
$Python=$null
foreach($p in $Candidates){if(Test-Path $p){$Python=$p;break}}
if(-not $Python){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$Python=$cmd.Source}
}
if(-not $Python){throw "Python not found."}
Write-Host "def Veritas WorkOps" -ForegroundColor Cyan
Write-Host "def AppRoot : $AppRoot"
Write-Host "def Python  : $Python"
Write-Host "def URL     : http://127.0.0.1:8775/"
Start-Process -FilePath $Python -ArgumentList @("engines\VIA_ENG105_WorkopsApiServer.py") -WorkingDirectory $AppRoot
Start-Sleep -Milliseconds 900
Start-Process "http://127.0.0.1:8775/"

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
