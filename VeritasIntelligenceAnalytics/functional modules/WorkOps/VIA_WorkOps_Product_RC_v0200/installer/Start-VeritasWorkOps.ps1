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
