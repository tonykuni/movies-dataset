#Requires -Version 5.1
<#
  VIA Active ETF — 控制台 (Orchestrator)
  選單式 UI：偵測/升級 PowerShell 7、裝環境、設 PATH、部署、啟動、更新、健康檢查。
  跑法（任何版本 PowerShell 皆可）：
    powershell -ExecutionPolicy Bypass -File "本檔路徑"
    或  pwsh -ExecutionPolicy Bypass -File "本檔路徑"
#>
[CmdletBinding(PositionalBinding=$false)]
param(
    [string]$PackName = "VIA_ActiveETF_SharePack_20260603_163235",
    [int]$Port = 8787,
    [string]$Password = "tonyissohot",
    [switch]$AutoAll   # 非互動：一次跑完 全自動部署+啟動，不顯示選單
)

$ErrorActionPreference = "Stop"

# ---- 固定路徑 ----
$Root      = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics"
$PackDir   = Join-Path (Join-Path $Root "_packages") $PackName
$AioPath   = Join-Path $PackDir "Run_VIA_ActiveETF_Sealed_AIO_B.ps1"
$DataDir   = Join-Path $PackDir "data"
$Ip        = "127.0.0.1"
$Url       = "http://$Ip`:$Port/"
$HealthUrl = "http://$Ip`:$Port/health.json"

# =============================================================================
# 基礎
# =============================================================================
function L {
    param([string]$Level,[string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    $color = switch ($Level) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} "INFO"{"Cyan"} "RUN"{"White"} "STEP"{"Magenta"} default{"Gray"} }
    Write-Host ("[" + $ts + "] [" + $Level + "] " + $Message) -ForegroundColor $color
}

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $pr = New-Object Security.Principal.WindowsPrincipal($id)
    return $pr.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Get-Pwsh7Path {
    $g = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($g) { return $g.Source }
    $p = Join-Path $env:ProgramFiles "PowerShell\7\pwsh.exe"
    if (Test-Path -LiteralPath $p) { return $p }
    return $null
}

function Test-ServerUp {
    try {
        $r = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
        return ($r.StatusCode -eq 200)
    } catch { return $false }
}

function Test-PortListening {
    param([int]$P)
    $c = [System.Net.Sockets.TcpClient]::new()
    try { $i = $c.BeginConnect($Ip, $P, $null, $null); $ok = $i.AsyncWaitHandle.WaitOne(400)
          if ($ok -and $c.Connected) { $c.EndConnect($i); return $true }; return $false }
    catch { return $false } finally { $c.Close() }
}

# =============================================================================
# 動作
# =============================================================================
function Action-Diagnose {
    Write-Host ""
    L "STEP" "環境診斷"
    L "INFO" ("執行中 PowerShell 版本: " + $PSVersionTable.PSVersion.ToString() + " (" + $PSVersionTable.PSEdition + ")")
    L "INFO" ("系統管理員: " + (Test-Admin))

    $p7 = Get-Pwsh7Path
    if ($p7) { L "OK" ("PowerShell 7: " + $p7) } else { L "WARN" "PowerShell 7: 未安裝" }

    $wg = Get-Command winget -ErrorAction SilentlyContinue
    if ($wg) { L "OK" "winget: 可用" } else { L "WARN" "winget: 不可用（自動升級將改用 MSI）" }

    if (Test-Path -LiteralPath $PackDir) { L "OK" ("分享包資料夾: " + $PackDir) } else { L "FAIL" ("分享包資料夾不存在: " + $PackDir) }
    if (Test-Path -LiteralPath $AioPath) { L "OK" "系統本體 AIO: 存在" } else { L "FAIL" "系統本體 AIO: 不存在" }
    if (Test-Path -LiteralPath $DataDir) { L "OK" ("BASE data: " + $DataDir) } else { L "WARN" "BASE data: 尚未建立（首次啟動會建）" }

    if (Test-ServerUp) { L "OK" ("Server 執行中: " + $Url) }
    elseif (Test-PortListening -P $Port) { L "WARN" ("Port " + $Port + " 被占用，但非本系統") }
    else { L "INFO" "Server: 未執行" }
}

function Action-UpgradePwsh {
    Write-Host ""
    L "STEP" "升級 / 安裝 PowerShell 7（最新版）"
    if (Get-Pwsh7Path) { L "INFO" "已安裝 PS7，仍嘗試更新到最新版..." }

    $done = $false
    $wg = Get-Command winget -ErrorAction SilentlyContinue
    if ($wg) {
        L "RUN" "用 winget 安裝/升級 Microsoft.PowerShell..."
        try {
            $args = @("install","--id","Microsoft.PowerShell","-e","--accept-source-agreements","--accept-package-agreements","--silent")
            $p = Start-Process winget -ArgumentList $args -NoNewWindow -PassThru -Wait
            if (Get-Pwsh7Path) { $done = $true; L "OK" "winget 安裝/升級完成" }
            else { L "WARN" ("winget 結束碼 " + $p.ExitCode + "，PS7 仍未偵測到") }
        } catch { L "WARN" ("winget 失敗: " + $_.Exception.Message) }
    } else { L "WARN" "winget 不可用" }

    if (-not $done) {
        L "RUN" "改用官方 MSI 靜默安裝（需系統管理員）..."
        if (-not (Test-Admin)) { L "WARN" "目前非系統管理員，MSI 安裝可能失敗。建議以系統管理員重開本控制台。" }
        try {
            $msi = Join-Path $env:TEMP "PowerShell-7-x64.msi"
            $dl = "https://github.com/PowerShell/PowerShell/releases/latest/download/PowerShell-7.4.6-win-x64.msi"
            L "RUN" "下載 MSI..."
            Invoke-WebRequest -Uri $dl -OutFile $msi -UseBasicParsing
            L "RUN" "安裝 MSI..."
            $p = Start-Process msiexec -ArgumentList @("/i", $msi, "/qn", "/norestart", "ADD_PATH=1") -PassThru -Wait
            if (Get-Pwsh7Path) { $done = $true; L "OK" "MSI 安裝完成" }
            else { L "WARN" ("MSI 結束碼 " + $p.ExitCode + "，請重開終端再偵測") }
        } catch { L "FAIL" ("MSI 安裝失敗: " + $_.Exception.Message) }
    }

    if ($done) { L "OK" ("PowerShell 7 就緒: " + (Get-Pwsh7Path)) }
    else { L "WARN" "PS7 未就緒；系統仍可用內建 PowerShell 5.1 啟動（功能相同）。" }
}

function Action-SetupEnv {
    Write-Host ""
    L "STEP" "建立環境 / 路徑 / data 結構"
    foreach ($d in @($DataDir, (Join-Path $DataDir "BASE"), (Join-Path $DataDir "DICT"),
                     (Join-Path $DataDir "BASE\DATA"), (Join-Path $DataDir "BASE\LOG"),
                     (Join-Path $DataDir "BASE\EXPORT"), (Join-Path $DataDir "BASE\SNAPSHOT"),
                     (Join-Path $DataDir "BASE\TEMP"))) {
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null; L "OK" ("建立: " + $d) }
        else { L "INFO" ("已存在: " + $d) }
    }
    # 解除封鎖
    Get-ChildItem -LiteralPath $PackDir -Filter "*.ps1" -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue
    L "OK" "已解除 .ps1 下載封鎖"

    # 把 pwsh 加進 PATH（append-only：已存在則略過）
    $p7 = Get-Pwsh7Path
    if ($p7) {
        $p7dir = Split-Path $p7 -Parent
        $cur = [Environment]::GetEnvironmentVariable("Path","User")
        if ($cur -notlike "*$p7dir*") {
            [Environment]::SetEnvironmentVariable("Path", ($cur.TrimEnd(";") + ";" + $p7dir), "User")
            L "OK" ("已將 PS7 加入使用者 PATH: " + $p7dir)
        } else { L "INFO" "PS7 已在使用者 PATH" }
    }
}

function Action-Activate {
    Write-Host ""
    L "STEP" "啟動系統"
    if (-not (Test-Path -LiteralPath $AioPath)) { L "FAIL" ("找不到系統本體: " + $AioPath); return }

    if (Test-ServerUp) { L "OK" "Server 已在執行，直接開啟瀏覽器。"; Start-Process $Url; return }

    $psexe = Get-Pwsh7Path
    if (-not $psexe) { $psexe = "powershell"; L "WARN" "用內建 PowerShell 5.1 啟動" } else { L "INFO" ("用 " + $psexe + " 啟動") }

    Unblock-File -LiteralPath $AioPath -ErrorAction SilentlyContinue
    L "RUN" "背景啟動 server（隱藏視窗）..."
    Start-Process $psexe -WindowStyle Hidden -ArgumentList @("-NoLogo","-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-File",$AioPath)

    $ok = $false
    for ($i = 1; $i -le 60; $i++) {
        Start-Sleep -Milliseconds 500
        Write-Progress -Id 1 -Activity "啟動 server" -Status ("等待 port " + $Port + "... " + [int]($i*0.5) + "s") -PercentComplete ([int](($i/60)*100))
        if (Test-PortListening -P $Port) { $ok = $true; break }
    }
    Write-Progress -Id 1 -Activity "done" -Completed

    if ($ok) {
        L "OK" "Server 已啟動，開啟瀏覽器登入頁。"
        Start-Process $Url
        L "INFO" ("登入密碼: " + $Password)
    } else { L "FAIL" "啟動逾時，請看是否被防毒攔或埠被占。" }
}

function Action-Update {
    Write-Host ""
    L "STEP" "更新（重新封裝最新成品）"
    L "INFO" "此動作會呼叫你的 Build 腳本以最新成品重封 AIO。"
    $build = $null
    foreach ($cand in @(
        (Join-Path $env:USERPROFILE "Downloads\VIA_ActiveETF_SealedAIO_Build.ps1"),
        (Join-Path ([Environment]::GetFolderPath("Desktop")) "VIA_ActiveETF_SealedAIO_Build.ps1")
    )) { if (Test-Path -LiteralPath $cand) { $build = $cand; break } }

    if (-not $build) { L "WARN" "找不到 VIA_ActiveETF_SealedAIO_Build.ps1（請放 Downloads 或桌面）。略過更新。"; return }

    $psexe = Get-Pwsh7Path
    if (-not $psexe) { L "FAIL" "更新需要 PowerShell 7（Build 腳本用到 7 的語法）。請先用選單 [2] 升級。"; return }

    Unblock-File -LiteralPath $build -ErrorAction SilentlyContinue
    L "RUN" "執行 Build（-ForceSync）..."
    Start-Process $psexe -Wait -ArgumentList @("-NoLogo","-NoProfile","-ExecutionPolicy","Bypass","-File",$build,"-ForceSync")
    L "OK" "Build 完成。如需重做分享包，請另跑 MakeSharePack。"
}

function Action-Health {
    Write-Host ""
    L "STEP" "健康檢查"
    if (Test-ServerUp) {
        try {
            $r = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 5
            L "OK" "health.json 回應 200："
            Write-Host $r.Content -ForegroundColor Gray
        } catch { L "WARN" ("讀取失敗: " + $_.Exception.Message) }
    } else { L "INFO" "Server 未執行。先用選單 [4] 啟動。" }
}

function Action-Stop {
    Write-Host ""
    L "STEP" "停止 server"
    $cs = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($cs.Count -eq 0) { L "INFO" "目前沒有在執行。"; return }
    $n = 0
    foreach ($op in @($cs | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique)) {
        $pn = $null
        try { $pn = (Get-Process -Id $op -ErrorAction Stop).ProcessName } catch {}
        if ($pn -in @("pwsh","powershell")) { try { Stop-Process -Id $op -Force; $n++ } catch {} }
    }
    L "OK" ("已停止 " + $n + " 個 server 行程。")
}

function Action-OpenFolder {
    if (Test-Path -LiteralPath $PackDir) { Start-Process $PackDir; L "OK" "已開啟分享包資料夾。" }
    else { L "FAIL" "分享包資料夾不存在。" }
}

function Action-DeployAll {
    L "STEP" "全自動部署 + 啟動"
    Action-Diagnose
    if (-not (Get-Pwsh7Path)) { Action-UpgradePwsh }
    Action-SetupEnv
    Action-Activate
    Write-Host ""
    L "OK" "全自動流程完成。"
}

# =============================================================================
# UI
# =============================================================================
function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "   VERITAS INTELLIGENCE ANALYTICS" -ForegroundColor White
    Write-Host "   Veritas Active ETF — 控制台 (Orchestrator)" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    $verTxt = $PSVersionTable.PSVersion.ToString()
    $p7 = if (Get-Pwsh7Path) { "已裝" } else { "未裝" }
    $srv = if (Test-ServerUp) { "執行中" } else { "停止" }
    Write-Host ("   目前 PS: " + $verTxt + "   |   PS7: " + $p7 + "   |   Server: " + $srv) -ForegroundColor DarkGray
    Write-Host ("   包: " + $PackName) -ForegroundColor DarkGray
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
}

function Show-Menu {
    Write-Host ""
    Write-Host "   [1] 環境診斷" -ForegroundColor White
    Write-Host "   [2] 升級 / 安裝 PowerShell 7（最新版）" -ForegroundColor White
    Write-Host "   [3] 建立環境 / 路徑 / data 結構" -ForegroundColor White
    Write-Host "   [4] 啟動系統（開瀏覽器登入頁）" -ForegroundColor White
    Write-Host "   [5] 健康檢查 (health.json)" -ForegroundColor White
    Write-Host "   [6] 停止 server" -ForegroundColor White
    Write-Host "   [7] 更新（重封最新成品，需 PS7）" -ForegroundColor White
    Write-Host "   [8] 開啟分享包資料夾" -ForegroundColor White
    Write-Host ""
    Write-Host "   [A] 全自動：診斷→升級→建環境→啟動 (一鍵)" -ForegroundColor Green
    Write-Host "   [Q] 離開" -ForegroundColor DarkGray
    Write-Host ""
}

# =============================================================================
# 進入點
# =============================================================================
try {
    if ($AutoAll) {
        Action-DeployAll
    }
    else {
        $loop = $true
        while ($loop) {
            Show-Banner
            Show-Menu
            $choice = Read-Host "   選擇"
            switch ($choice.ToUpper()) {
                "1" { Action-Diagnose }
                "2" { Action-UpgradePwsh }
                "3" { Action-SetupEnv }
                "4" { Action-Activate }
                "5" { Action-Health }
                "6" { Action-Stop }
                "7" { Action-Update }
                "8" { Action-OpenFolder }
                "A" { Action-DeployAll }
                "Q" { $loop = $false }
                default { L "WARN" "無效選項" }
            }
            if ($loop) {
                Write-Host ""
                Write-Host "   按 Enter 回到選單..." -ForegroundColor DarkGray
                [void](Read-Host)
            }
        }
        Write-Host ""
        L "OK" "已離開控制台。"
    }
}
catch {
    L "FAIL" $_.Exception.Message
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Progress -Id 1 -Activity "done" -Completed
}
