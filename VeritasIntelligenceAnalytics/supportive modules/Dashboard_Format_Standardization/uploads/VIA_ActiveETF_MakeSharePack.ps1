#Requires -Version 7.0
# =============================================================================
# VIA_ActiveETF — 分享包打包器（情境B：給不會電腦的人）
# 產出：一個可攜資料夾 + zip，內含
#   Run_VIA_ActiveETF_Sealed_AIO_B.ps1  (系統本體；BASE 改為包內 data\ 可攜)
#   啟動.cmd            (偵測 PS7→沒有就 winget 裝→不行就 MSI 靜默裝→啟動→開瀏覽器)
#   安裝桌面捷徑.cmd     (在對方電腦生成有 logo 的桌面捷徑)
#   VIA.ico             (狼盾圖示)
#   說明.txt
# 跑法：pwsh -ExecutionPolicy Bypass -File "本檔路徑"
# =============================================================================
[CmdletBinding(PositionalBinding=$false)]
param(
    [string]$PackageRoot = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\_packages",
    [string]$DeployDir   = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\_deploy\VIA_ActiveETF",
    [int]$Port = 8787,
    [string]$Password = "tonyissohot"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AioLeaf = "Run_VIA_ActiveETF_Sealed_AIO_B.ps1"

function L {
    param([string]$Level,[string]$Message)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = switch ($Level) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} "INFO"{"Cyan"} "RUN"{"White"} default{"Gray"} }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

function Get-LatestAio {
    if (-not (Test-Path -LiteralPath $PackageRoot)) { return $null }
    $hit = @(Get-ChildItem -LiteralPath $PackageRoot -Recurse -Filter $AioLeaf -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending)
    if ($hit.Count -gt 0) { return $hit[0].FullName }
    return $null
}

function Make-Portable {
    param([string]$AioText)
    $t = $AioText
    # 1) 拿掉 #Requires 7.0，讓 5.1 後備也能跑（萬一 PS7 安裝被取消）
    $t = $t -replace '(?m)^#Requires -Version 7\.0\s*\r?\n', ''
    # 2) BASE / DICT 改為包內可攜路徑（整行替換，零反引號零吃字元）
    $lines = $t -split "`r`n|`n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\$BaseDir\s*=') { $lines[$i] = '$BaseDir = (Join-Path $PSScriptRoot "data\BASE")' }
        elseif ($lines[$i] -match '^\$DictDir\s*=') { $lines[$i] = '$DictDir = (Join-Path $PSScriptRoot "data\DICT")' }
    }
    return ($lines -join "`r`n")
}

# =============================================================================
function Main {
    Write-Host ""
    Write-Host "============ VIA Active ETF — 分享包打包器 ============" -ForegroundColor Cyan

    $aio = Get-LatestAio
    if (-not $aio) { throw "找不到封裝 AIO ($AioLeaf)。請先跑 VIA_ActiveETF_SealedAIO_Build.ps1。" }
    L "OK" ("使用最新 AIO: " + $aio)

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $packName = "VIA_ActiveETF_SharePack_$stamp"
    $packDir = Join-Path $PackageRoot $packName
    $dataDir = Join-Path $packDir "data"
    New-Item -ItemType Directory -Path $packDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $dataDir "BASE") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $dataDir "DICT") -Force | Out-Null

    # ---- 1) 複製並可攜化 AIO ----
    L "RUN" "可攜化 AIO（拿掉 #Requires、BASE 改包內 data\）"
    $aioText = [IO.File]::ReadAllText($aio)
    $portable = Make-Portable -AioText $aioText
    $aioDst = Join-Path $packDir $AioLeaf
    [IO.File]::WriteAllText($aioDst, $portable, [System.Text.UTF8Encoding]::new($false))
    # 語法檢查
    $tok=$null; $errs=$null
    [void][System.Management.Automation.Language.Parser]::ParseInput($portable, [ref]$tok, [ref]$errs)
    if ($errs -and @($errs).Count -gt 0) {
        foreach ($e in @($errs) | Select-Object -First 6) { L "FAIL" ("  L" + $e.Extent.StartLineNumber + ": " + $e.Message) }
        throw "可攜化後語法錯誤"
    }
    L "OK" "AIO 已可攜化並通過語法檢查"

    # ---- 2) 圖示 ----
    $icoSrc = Join-Path $DeployDir "VIA.ico"
    $icoDst = Join-Path $packDir "VIA.ico"
    if (Test-Path -LiteralPath $icoSrc) { Copy-Item -LiteralPath $icoSrc -Destination $icoDst -Force; L "OK" "VIA.ico 已附入" }
    else { L "WARN" "找不到 VIA.ico，捷徑將用預設圖示" }

    # ---- 3) 啟動.cmd ----
    $startCmd = @'
@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title Veritas Active ETF

set "PS1=%~dp0Run_VIA_ActiveETF_Sealed_AIO_B.ps1"
set "URL=http://127.0.0.1:8787/"
set "PSEXE="

echo.
echo  Veritas Active ETF - 啟動中...
echo.

rem === 1) 找 PowerShell 7 ===
where pwsh >nul 2>nul
if %errorlevel%==0 (
  set "PSEXE=pwsh"
  goto :HAVE_PS
)

rem === 2) 沒有 PS7 -> 嘗試 winget 安裝（會跳一次 UAC，請按「是」）===
echo  偵測到未安裝 PowerShell 7，嘗試自動安裝...
echo  （若彈出「是否允許變更裝置」請按「是」）
echo.
where winget >nul 2>nul
if %errorlevel%==0 (
  winget install --id Microsoft.PowerShell -e --accept-source-agreements --accept-package-agreements --silent
  where pwsh >nul 2>nul
  if %errorlevel%==0 ( set "PSEXE=pwsh" & goto :HAVE_PS )
  rem winget 裝完 PATH 可能未更新，試固定路徑
  if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" ( set "PSEXE=%ProgramFiles%\PowerShell\7\pwsh.exe" & goto :HAVE_PS )
)

rem === 3) winget 不行 -> 下載官方 MSI 靜默安裝 ===
echo  改用官方安裝檔...
set "MSI=%TEMP%\PowerShell-7-x64.msi"
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -Uri 'https://github.com/PowerShell/PowerShell/releases/latest/download/PowerShell-7.4.6-win-x64.msi' -OutFile '%MSI%' -UseBasicParsing}catch{exit 1}"
if exist "%MSI%" (
  msiexec /i "%MSI%" /qn /norestart ADD_PATH=1
  if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" ( set "PSEXE=%ProgramFiles%\PowerShell\7\pwsh.exe" & goto :HAVE_PS )
)

rem === 4) 都失敗 -> 退回 Windows 內建 5.1（零安裝，照樣能跑）===
echo  自動安裝未完成，改用系統內建 PowerShell（功能相同）。
set "PSEXE=powershell"

:HAVE_PS
echo  使用：%PSEXE%
echo.

rem 解除下載封鎖
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "Unblock-File -LiteralPath '%PS1%' -ErrorAction SilentlyContinue" >nul 2>nul

rem 背景啟動 server（隱藏視窗）
start "" %PSEXE% -NoLogo -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%PS1%"

rem 等候 server 起來再開瀏覽器
echo  啟動中，請稍候...
timeout /t 5 /nobreak >nul
start "" "%URL%"

echo.
echo  已開啟。瀏覽器若沒自動跳，請手動開： %URL%
echo  登入密碼：__PWD__
echo.
timeout /t 3 /nobreak >nul
endlocal
'@
    $startCmd = $startCmd.Replace('__PWD__', $Password)
    [IO.File]::WriteAllText((Join-Path $packDir "啟動.cmd"), $startCmd, [System.Text.UTF8Encoding]::new($true))
    L "OK" "啟動.cmd 已寫（PS7偵測→winget→MSI→5.1後備）"

    # ---- 4) 安裝桌面捷徑.cmd（呼叫內嵌 ps1 建捷徑）----
    $shortcutCmd = @'
@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -File "%~dp0_make_shortcut.ps1"
echo.
echo  桌面捷徑已建立：Veritas Active ETF
timeout /t 3 /nobreak >nul
'@
    [IO.File]::WriteAllText((Join-Path $packDir "安裝桌面捷徑.cmd"), $shortcutCmd, [System.Text.UTF8Encoding]::new($true))

    $mkShortcutPs1 = @'
$ErrorActionPreference = "SilentlyContinue"
$here = $PSScriptRoot
$cmd  = Join-Path $here "啟動.cmd"
$ico  = Join-Path $here "VIA.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "Veritas Active ETF.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = "cmd.exe"
$sc.Arguments = '/c "' + $cmd + '"'
$sc.WorkingDirectory = $here
$sc.WindowStyle = 7
$sc.Description = "Veritas Active ETF Console"
if (Test-Path -LiteralPath $ico) { $sc.IconLocation = ($ico + ",0") }
$sc.Save()
'@
    [IO.File]::WriteAllText((Join-Path $packDir "_make_shortcut.ps1"), $mkShortcutPs1, [System.Text.UTF8Encoding]::new($false))
    L "OK" "安裝桌面捷徑.cmd + _make_shortcut.ps1 已寫"

    # ---- 5) 說明.txt ----
    $readme = @'
========================================
 Veritas Active ETF — 使用說明
========================================

【怎麼開】
 1. 解壓縮整個資料夾到任意位置（例如桌面）。
 2. 雙擊「啟動.cmd」。
 3. 第一次若電腦沒有 PowerShell 7，會自動安裝：
    跳出「是否允許這個 App 變更你的裝置？」時，請按「是」。
    （若不想安裝，按「否」也可以，程式會自動改用系統內建版本繼續執行。）
 4. 稍等幾秒，瀏覽器會自動開啟登入頁。
 5. 輸入密碼後即可使用。

【登入密碼】
 __PWD__

【想要桌面有圖示】
 雙擊「安裝桌面捷徑.cmd」一次，桌面就會出現「Veritas Active ETF」圖示，
 之後直接雙擊桌面圖示即可開啟。

【資料存哪】
 你儲存/擷取的資料會放在本資料夾的 data 子資料夾裡：
   data\BASE\DATA      一般資料
   data\BASE\SNAPSHOT  快照
   data\BASE\LOG       日誌
 （整個資料夾可以複製到別的電腦，資料跟著走。）

【關閉】
 關掉瀏覽器分頁即可。背景服務會在電腦重開機後自動結束；
 若想立刻停止，重開機，或結束工作管理員裡的 pwsh / powershell。

【網址（手動開啟用）】
 http://127.0.0.1:8787/

【需要協助】
 若雙擊沒反應，請確認已「全部解壓縮」（不要直接從 zip 裡點），再試一次。

----------------------------------------
 VERITAS INTELLIGENCE ANALYTICS
========================================
'@
    $readme = $readme.Replace('__PWD__', $Password)
    [IO.File]::WriteAllText((Join-Path $packDir "說明.txt"), $readme, [System.Text.UTF8Encoding]::new($true))
    L "OK" "說明.txt 已寫"

    # ---- 6) 壓成 zip ----
    L "RUN" "壓縮分享包..."
    $zip = Join-Path $PackageRoot ($packName + ".zip")
    if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
    Compress-Archive -Path (Join-Path $packDir "*") -DestinationPath $zip -Force
    $zipSize = (Get-Item -LiteralPath $zip).Length
    L "OK" ("分享包 zip：" + $zip + "（" + [math]::Round($zipSize/1MB,2) + " MB）")

    Write-Host ""
    Write-Host "==================== DONE ====================" -ForegroundColor Cyan
    Write-Host ("分享資料夾 : " + $packDir) -ForegroundColor Green
    Write-Host ("分享 zip   : " + $zip) -ForegroundColor Green
    Write-Host ""
    Write-Host "把那個 zip 傳給對方即可。對方：解壓 → 雙擊「啟動.cmd」。" -ForegroundColor Yellow
    Write-Host ("登入密碼：" + $Password) -ForegroundColor Yellow
    Write-Host ""
    Write-Host "提醒：對方第一次若沒 PS7，會跳一次 UAC 請按「是」；按「否」也會自動改用內建版繼續。" -ForegroundColor DarkCyan

    Start-Process $packDir
}

try { Main }
catch {
    L "FAIL" $_.Exception.Message
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Host ""
    Write-Host "完成。" -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
