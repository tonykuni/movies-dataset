# Invoke-VIA-CentralGov-v0100.ps1 — 中央治理主控台非阻塞啟動器(TOOL-063)
# 不關閉、不阻塞、不卡斷:引擎跑完即回控制台;UI 以 Start-Process 非同步開啟。
# 常備令①:留痕必存;常備令②:動態進度條+誠實敘述由引擎內建。
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logd = Join-Path $root 'VIA_Reports\centralgov_runs'
New-Item -ItemType Directory -Force -Path $logd | Out-Null
$log = Join-Path $logd ("PSLAUNCH_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
Start-Transcript -Path $log | Out-Null
try {
    $eng = Get-ChildItem -Path $PSScriptRoot -Filter 'CGC_MDL075_CentralGov_v0*.py' |
        Sort-Object Name | Select-Object -Last 1   # 動態解析最新版(鐵律)
    Write-Host ("[GOV] 引擎:{0}" -f $eng.Name)
    & py $eng.FullName --no-open
    $rc = $LASTEXITCODE
    $ui = Join-Path $root 'VIA_Reports\VIA_UI_CentralGov.html'
    if (Test-Path $ui) { Start-Process $ui }   # 非阻塞開 UI
    Write-Host ("[GOV] rc={0} · UI 已非同步開啟 · 留痕:{1}" -f $rc, $log)
    exit $rc
} finally { Stop-Transcript | Out-Null }
