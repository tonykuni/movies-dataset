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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
