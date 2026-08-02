#Requires -Version 7.0
# =============================================================================
# VIA_ActiveETF — Route A：桌面捷徑(有 logo、雙擊即開、隱藏黑窗、不會電腦也行)
# 做的事：找最新封裝 AIO → 取得 .ico → 寫保姆 Launcher → 建桌面捷徑(自訂圖示)
#         → 建 Stop 捷徑 → 立即測試一次
# 跑法：pwsh -ExecutionPolicy Bypass -File "本檔路徑"
# =============================================================================
[CmdletBinding(PositionalBinding=$false)]
param(
    [string]$PackageRoot = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\_packages",
    [string]$DeployDir   = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\_deploy\VIA_ActiveETF",
    [int]$Port = 8787,
    [string]$IpAddr = "127.0.0.1",
    [string]$ShortcutName = "Veritas Active ETF",
    [switch]$NoTest
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

function Resolve-Pwsh {
    $g = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($g) { return $g.Source }
    $p = Join-Path $env:ProgramFiles "PowerShell\7\pwsh.exe"
    if (Test-Path -LiteralPath $p) { return $p }
    return "pwsh.exe"
}

function Resolve-Ico {
    param([string]$OutDir)
    # 1) 既有 VIA.ico 最優先
    $existing = Join-Path $DeployDir "VIA.ico"
    if (Test-Path -LiteralPath $existing) {
        $dst = Join-Path $OutDir "VIA.ico"
        Copy-Item -LiteralPath $existing -Destination $dst -Force
        L "OK" "使用既有 VIA.ico"
        return $dst
    }
    # 2) 由 PNG 產生(best effort)
    foreach ($png in @("icon-512.png","VIA_logo.png","icon-192.png")) {
        $src = Join-Path $DeployDir $png
        if (Test-Path -LiteralPath $src) {
            try {
                Add-Type -AssemblyName System.Drawing -ErrorAction Stop
                $img = [System.Drawing.Image]::FromFile($src)
                $bmp = New-Object System.Drawing.Bitmap($img, 256, 256)
                $hicon = $bmp.GetHicon()
                $icon = [System.Drawing.Icon]::FromHandle($hicon)
                $dst = Join-Path $OutDir "VIA.ico"
                $fs = [System.IO.File]::Create($dst)
                $icon.Save($fs); $fs.Close()
                $img.Dispose(); $bmp.Dispose()
                L "OK" ("由 " + $png + " 產生 VIA.ico")
                return $dst
            } catch { L "WARN" ("PNG 轉 ico 失敗: " + $_.Exception.Message) }
        }
    }
    L "WARN" "找不到可用圖示，捷徑將用 pwsh 預設圖示。"
    return $null
}

function New-Shortcut {
    param([string]$LnkPath,[string]$Target,[string]$Arguments,[string]$Ico,[string]$WorkDir,[string]$Desc)
    $ws = New-Object -ComObject WScript.Shell
    $lnk = $ws.CreateShortcut($LnkPath)
    $lnk.TargetPath = $Target
    $lnk.Arguments = $Arguments
    $lnk.WorkingDirectory = $WorkDir
    $lnk.WindowStyle = 7   # minimized（搭配 pwsh -WindowStyle Hidden）
    $lnk.Description = $Desc
    if ($Ico) { $lnk.IconLocation = ($Ico + ",0") }
    $lnk.Save()
}

# =============================================================================
function Main {
    Write-Host ""
    Write-Host "============ VIA Active ETF — Route A：桌面捷徑 ============" -ForegroundColor Cyan

    $aio = Get-LatestAio
    if (-not $aio) { throw "找不到封裝 AIO ($AioLeaf)。請先跑 VIA_ActiveETF_SealedAIO_Build.ps1。" }
    L "OK" ("使用最新 AIO: " + $aio)

    $aioDir = Split-Path $aio -Parent
    $pwsh = Resolve-Pwsh
    L "INFO" ("pwsh: " + $pwsh)

    $ico = Resolve-Ico -OutDir $aioDir

    # ---- 寫保姆 Launcher（已在跑→直接開；沒跑→隱藏啟動→等→開；逾時白話提示）----
    $launcherPath = Join-Path $aioDir "VIA_Launcher.ps1"
    $launcherTpl = @'
#Requires -Version 7.0
$AioPs1 = '@@AIO@@'
$Ip = '@@IP@@'
$Port = @@PORT@@
$Url    = 'http://' + $Ip + ':' + [string]$Port + '/'
$Health = 'http://' + $Ip + ':' + [string]$Port + '/health.json'

function Test-Up {
    try { $r = Invoke-WebRequest -Uri $Health -UseBasicParsing -NoProxy -TimeoutSec 2; return ($r.StatusCode -eq 200) }
    catch { return $false }
}

try {
    if (Test-Up) { Start-Process $Url; return }

    Start-Process $AioPs1 -WindowStyle Hidden
    # 上面用關聯啟動可能不吃 -File，改保險作法：用 pwsh 明確啟動
    if (-not (Test-Up)) {
        Start-Process pwsh -WindowStyle Hidden -ArgumentList @("-NoLogo","-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-File",$AioPs1)
    }

    $ok = $false
    for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Milliseconds 500; if (Test-Up) { $ok = $true; break } }

    if ($ok) { Start-Process $Url }
    else {
        Add-Type -AssemblyName System.Windows.Forms
        [void][System.Windows.Forms.MessageBox]::Show("Veritas Active ETF 啟動逾時。請再雙擊一次圖示。", "Veritas Active ETF")
    }
}
catch {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        [void][System.Windows.Forms.MessageBox]::Show("啟動失敗：" + $_.Exception.Message, "Veritas Active ETF")
    } catch {}
}
'@
    $launcher = $launcherTpl.
        Replace('@@AIO@@', $aio.Replace("'","''")).
        Replace('@@IP@@',  $IpAddr.Replace("'","''")).
        Replace('@@PORT@@', [string]$Port)
    [IO.File]::WriteAllText($launcherPath, $launcher, [System.Text.UTF8Encoding]::new($false))
    L "OK" ("Launcher 已寫: " + $launcherPath)

    # ---- 寫 Stop helper ----
    $stopPath = Join-Path $aioDir "VIA_Stop.ps1"
    $stopTpl = @'
#Requires -Version 7.0
$Port = @@PORT@@
$cs = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
$n = 0
foreach ($op in @($cs | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique)) {
    $pn = $null
    try { $pn = (Get-Process -Id $op -ErrorAction Stop).ProcessName } catch {}
    if ($pn -in @("pwsh","powershell")) { try { Stop-Process -Id $op -Force; $n++ } catch {} }
}
try {
    Add-Type -AssemblyName System.Windows.Forms
    $msg = if ($n -gt 0) { "已停止 Veritas Active ETF。" } else { "目前沒有在執行。" }
    [void][System.Windows.Forms.MessageBox]::Show($msg, "Veritas Active ETF")
} catch {}
'@
    $stop = $stopTpl.Replace('@@PORT@@', [string]$Port)
    [IO.File]::WriteAllText($stopPath, $stop, [System.Text.UTF8Encoding]::new($false))
    L "OK" ("Stop helper 已寫: " + $stopPath)

    # ---- 建桌面捷徑 ----
    $desktop = [Environment]::GetFolderPath("Desktop")
    $startLnk = Join-Path $desktop ($ShortcutName + ".lnk")
    $stopLnk  = Join-Path $desktop ("Stop " + $ShortcutName + ".lnk")

    $startArgs = '-NoLogo -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $launcherPath + '"'
    New-Shortcut -LnkPath $startLnk -Target $pwsh -Arguments $startArgs -Ico $ico -WorkDir $aioDir -Desc "Veritas Active ETF Console"
    L "OK" ("桌面捷徑: " + $startLnk)

    $stopArgs = '-NoLogo -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $stopPath + '"'
    New-Shortcut -LnkPath $stopLnk -Target $pwsh -Arguments $stopArgs -Ico $ico -WorkDir $aioDir -Desc "Stop Veritas Active ETF"
    L "OK" ("停止捷徑: " + $stopLnk)

    Write-Host ""
    Write-Host "==================== DONE ====================" -ForegroundColor Cyan
    Write-Host "桌面已建立兩個圖示：" -ForegroundColor Green
    Write-Host ("  ▸ " + $ShortcutName + "      ← 雙擊就開(有 logo、無黑窗)")
    Write-Host ("  ▸ Stop " + $ShortcutName + " ← 要關掉 server 時雙擊")
    Write-Host ""
    Write-Host "密碼: tonyissohot" -ForegroundColor Yellow

    if (-not $NoTest) {
        Write-Host ""
        L "RUN" "立即測試啟動捷徑..."
        Start-Process $pwsh -ArgumentList @("-NoLogo","-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-File",$launcherPath) -WindowStyle Hidden
        $ok = $false
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Milliseconds 500
            Write-Progress -Id 1 -Activity "測試啟動" -Status ("等待 server... " + [int]($i*0.5) + "s") -PercentComplete (($i*3) % 100)
            try { $r = Invoke-WebRequest -Uri ("http://" + $IpAddr + ":" + [string]$Port + "/health.json") -UseBasicParsing -NoProxy -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}
        }
        Write-Progress -Id 1 -Activity "done" -Completed
        if ($ok) { L "OK" "捷徑可正常啟動 server，瀏覽器應已開啟登入頁。" }
        else { L "WARN" "測試逾時，請手動雙擊桌面圖示確認。" }
    }
}

try { Main }
catch {
    L "FAIL" $_.Exception.Message
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Progress -Id 1 -Activity "done" -Completed
    Write-Host ""
    Write-Host "完成。" -ForegroundColor Cyan
}
