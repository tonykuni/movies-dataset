# VIA.ps1 — 單一 PowerShell 總入口(批206;操作員令「一個 PowerShell 解決一切」)
# 用法:
#   首次安裝(貼一次,桌面出現「VIA」捷徑,以後雙擊即一切):
#     powershell -ExecutionPolicy Bypass -File "<此檔完整路徑>" -Install
#   直接跑(=捷徑雙擊同效):全自動模式——先 git 同步+斷點修復(批213),
#   再日更全鏈+回補續跑+開三頁 UI
#   選單模式:加 -Menu
# 背景作業=獨立進程(Start-Process):關掉本視窗不中斷(不卡斷紀律)
param([switch]$Install, [switch]$Menu)
$ErrorActionPreference = "Continue"
$VIA = $PSScriptRoot
# ===== [VIA:PS-ACCEL:v0100] PS 加速模組掛載(graceful 缺席零影響) =====
$PSAccel = Join-Path $VIA "supportive modules\VIA_PS_Accel_Module.ps1"
if (Test-Path $PSAccel) { try { . $PSAccel } catch { } }
# ===== [VIA:PS-ACCEL:END] =====

function New-DesktopShortcut {
    $desk = [Environment]::GetFolderPath("Desktop")
    $lnk = Join-Path $desk "VIA.lnk"
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut($lnk)
    $sc.TargetPath = "powershell.exe"
    $sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $sc.WorkingDirectory = $VIA
    $sc.IconLocation = "shell32.dll,137"
    $sc.Description = "VIA 一鍵啟動(全自動日更+回補+UI)"
    $sc.Save()
    Write-Host "[VIA] 桌面捷徑已建立:$lnk(以後雙擊它=一切)" -ForegroundColor Green
}

function Start-Background([string]$label, [string]$file, [string[]]$argv) {
    # 獨立進程=關窗不斷;log 由各引擎自落
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass")
    if ($file -like "*.ps1") { $args += @("-File", $file) + $argv }
    else { $args = $null }
    if ($args) {
        Start-Process powershell -ArgumentList $args -WindowStyle Minimized | Out-Null
    } else {
        Start-Process python -ArgumentList (@("`"$file`"") + $argv) -WindowStyle Minimized | Out-Null
    }
    Write-Host "  [背景] $label 已啟動(獨立進程;關窗不斷)" -ForegroundColor Cyan
}

function Newest([string]$dir, [string]$pat) {
    (Get-ChildItem -Path $dir -Filter $pat -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}

function Open-UIs {
    Start-Sleep -Seconds 2
    # 批222:總入口 Portal 單頁=一鍵到全介面(先重生=尾版清單最新)
    $pg = Newest (Join-Path $VIA "supportive modules\registry") "CGC_MDL097_PortalUI_v*.py"
    if ($pg) { python "$pg" | Out-Null }
    $portal = Join-Path $VIA "supportive modules\ui_support\VIA_UI_Portal_v0100.html"
    if (Test-Path $portal) { Start-Process $portal
        Write-Host "  [UI] 總入口 Portal 已開(內含全介面連結;橋接=指揮台直跑)" -ForegroundColor Green }
    else { Start-Process "http://127.0.0.1:8765/"
        Write-Host "  [UI] Portal 缺=後備開指揮台(誠實)" -ForegroundColor Yellow }
}

function Sync-Repo {
    # 批213:啟動先同步;批214:工作站實錄雙修——
    # ①再生頁=衍生物(引擎每跑必重生)→pull 前還原本地副本,消結構性衝突
    # ②舊版回補進程先收束(中斷安全=checkpoint 零損失),隨後由尾版重啟
    try {
        Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction Stop |
          Where-Object { $_.CommandLine -match "VDF_ENG064_HistoryBackfill" } |
          ForEach-Object { Stop-Process -Id $_.ProcessId -Force
                           Write-Host "  [同步] 收束舊回補進程 PID $($_.ProcessId)(斷點在=零損失)" -ForegroundColor Yellow }
    } catch { }
    git -C $VIA checkout -- "supportive modules/ui_support" 2>$null   # 再生頁還原(pull 後引擎重生最新)
    try {
        $out = git -C $VIA pull --ff-only 2>&1
        Write-Host "  [同步] git pull:$($out | Select-Object -Last 1)" -ForegroundColor Cyan
    } catch {
        Write-Host "  [同步] pull 失敗(離線/本地改動)=誠實續用現版" -ForegroundColor Yellow
    }
    $bf = Newest (Join-Path $VIA "functional modules\VDF\engine") "VDF_ENG064_HistoryBackfill_v*.py"
    if ($bf) { python "$bf" --rebuild-ckpt }   # 真斷點重建(批212 債修;零網路)
}

function Invoke-All {
    $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"
    Write-Host "[VIA] 全自動模式:同步+日更全鏈+回補續跑+開 UI(全背景不卡)" -ForegroundColor Yellow
    Sync-Repo
    Start-Background "日更全鏈(boot ①-⑨)" (Join-Path $VIA "supportive modules\registry\via_boot_update.ps1") @()
    # 批208:指揮台執行橋(按下=直接執行;127.0.0.1 白名單)
    $ds = Get-ChildItem (Join-Path $VIA "supportive modules\registry") -Filter "CGC_MDL095_DeckServer_v*.py" | Sort-Object Name | Select-Object -Last 1
    if ($ds) { Start-Process python -ArgumentList @("`"$($ds.FullName)`"", "serve") -WindowStyle Minimized | Out-Null
               Write-Host "  [背景] 指揮台橋接 http://127.0.0.1:8765/ 已啟動" -ForegroundColor Cyan }
    $bf = Newest (Join-Path $VIA "functional modules\VDF\engine") "VDF_ENG064_HistoryBackfill_v*.py"
    if ($bf) { Start-Background "歷史回補 2022~(增量續跑;2020/21 終止批212)" $bf @("run") }
    Open-UIs
    Write-Host "[VIA] 完成派工。進度:VIA_Reports\boot_update_logs\ 最新 log;UI 稍後重新整理即最新。" -ForegroundColor Yellow
}

if ($Install) { New-DesktopShortcut; Read-Host "按 Enter 關閉"; exit 0 }

if ($Menu) {
    while ($true) {
        Write-Host "`n=== VIA 選單(輸入數字按 Enter)===" -ForegroundColor Cyan
        Write-Host " 1) 全自動(日更+回補+UI)  2) 只跑日更全鏈"
        Write-Host " 3) 只跑歷史回補 2022~      4) 只開總入口 Portal"
        Write-Host " 5) 建桌面捷徑              0) 離開"
        switch (Read-Host "選") {
            "1" { Invoke-All }
            "2" { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"
                  Start-Background "日更全鏈" (Join-Path $VIA "supportive modules\registry\via_boot_update.ps1") @() }
            "3" { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"
                  $bf = Newest (Join-Path $VIA "functional modules\VDF\engine") "VDF_ENG064_HistoryBackfill_v*.py"
                  if ($bf) { Start-Background "歷史回補" $bf @("run") } }
            "4" { Open-UIs }
            "5" { New-DesktopShortcut }
            "0" { exit 0 }
            default { Write-Host "無效選項" }
        }
    }
}

Invoke-All
Read-Host "按 Enter 關閉此視窗(背景作業續跑不中斷)"
