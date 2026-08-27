# VIA.ps1 — 單一 PowerShell 總入口(批206;操作員令「一個 PowerShell 解決一切」)
# 用法:
#   首次安裝(貼一次,桌面出現「VIA」捷徑,以後雙擊即一切):
#     powershell -ExecutionPolicy Bypass -File "<此檔完整路徑>" -Install
#   直接跑(=捷徑雙擊同效):全自動模式——日更全鏈+回補續跑+開三頁 UI
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
    foreach ($f in @("VIA_UI_SystemHub_v0100.html",
                     "VIA_UI_CommandDeck_v0100.html",
                     "VIA_UI_GovernanceMatrix_v0100.html")) {
        $p = Join-Path $VIA "supportive modules\ui_support\$f"
        if (Test-Path $p) { Start-Process $p }
    }
    Write-Host "  [UI] 樞紐+指揮台+治理矩陣 已開" -ForegroundColor Green
}

function Invoke-All {
    $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"
    Write-Host "[VIA] 全自動模式:日更全鏈+歷史回補續跑+開 UI(全背景不卡)" -ForegroundColor Yellow
    Start-Background "日更全鏈(boot ①-⑨)" (Join-Path $VIA "supportive modules\registry\via_boot_update.ps1") @()
    $bf = Newest (Join-Path $VIA "functional modules\VDF\engine") "VDF_ENG064_HistoryBackfill_v*.py"
    if ($bf) { Start-Background "歷史回補 2020~(增量續跑)" $bf @("run") }
    Open-UIs
    Write-Host "[VIA] 完成派工。進度:VIA_Reports\boot_update_logs\ 最新 log;UI 稍後重新整理即最新。" -ForegroundColor Yellow
}

if ($Install) { New-DesktopShortcut; Read-Host "按 Enter 關閉"; exit 0 }

if ($Menu) {
    while ($true) {
        Write-Host "`n=== VIA 選單(輸入數字按 Enter)===" -ForegroundColor Cyan
        Write-Host " 1) 全自動(日更+回補+UI)  2) 只跑日更全鏈"
        Write-Host " 3) 只跑歷史回補 2020~      4) 只開 UI 三頁"
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
