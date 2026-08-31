param(
    [switch]$NoBrowser,
    [switch]$SkipDeps,
    [switch]$SelfTestOnly
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

# ==============================================================================
# Start-VIA.ps1  -  VIA_Forge 一鍵啟動器（樞 SystemManager + 3 強引擎 + HTML U/I）
#   15 個加速階段 + 動態進度條（Write-Progress）；不卡斷：批次安裝、即時回報。
#   遵守 LL：param() 最前、無別名、無 Read-Host、無 exit/Stop-Process、UTF8。
# ==============================================================================

$ErrorActionPreference = "Stop"
$Root    = $PSScriptRoot
$VenvDir = Join-Path $Root ".venv"
$VenvPy  = Join-Path $VenvDir "Scripts\python.exe"
$Server  = Join-Path $Root "via_server.py"

# ---- 15 個加速階段（動態進度條依此推進） ----
$Total = 15
$Step  = 0
function Step-Progress {
    param([string]$Label, [string]$Detail = "")
    $script:Step++
    $pct = [int](($script:Step / $Total) * 100)
    Write-Progress -Activity "VIA_Forge 啟動加速器" -Status ("[{0}/{1}] {2}" -f $script:Step, $Total, $Label) -PercentComplete $pct -CurrentOperation $Detail
    Write-Host ("  [{0,2}/{1}] {2}" -f $script:Step, $Total, $Label) -ForegroundColor Cyan
}

function Find-Python {
    foreach ($c in @("py -3.12", "py -3.11", "py -3.13", "python")) {
        $parts = $c.Split(" "); $exe = $parts[0]; $a = @()
        if ($parts.Count -gt 1) { $a = $parts[1..($parts.Count - 1)] }
        try {
            $v = & $exe @a "-c" "import sys;print(sys.version.split()[0])" 2>$null
            if ($LASTEXITCODE -eq 0 -and $v) {
                return [pscustomobject]@{ Exe = $exe; Args = $a; Version = ("" + $v).Trim() }
            }
        } catch { }
    }
    return $null
}

function Install-Group {
    param([string]$Name, [string[]]$Pkgs)
    # 批次安裝（一次呼叫，遠快於逐個）；失敗不中斷（optional）
    try {
        & $VenvPy "-m" "pip" "install" @Pkgs "--quiet" "--disable-pip-version-check" 2>$null | Out-Null
    } catch { }
}

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  VIA_Forge  -  樞 SystemManager  -  一鍵啟動（15 加速器）" -ForegroundColor Cyan
Write-Host "  位置：$Root" -ForegroundColor DarkGray
Write-Host "===============================================================" -ForegroundColor Cyan

if (-not (Test-Path $Server)) {
    Write-Host "找不到 via_server.py（請在內層 VIA_Forge 資料夾執行）" -ForegroundColor Red
    return
}

# 1 定位
Step-Progress "定位根目錄" $Root

# 2 偵測 Python
Step-Progress "偵測 Python"
$py = Find-Python
if ($null -eq $py) {
    Write-Progress -Activity "VIA_Forge" -Completed
    Write-Host "  找不到 Python。請裝 Python 3.12 並勾選 Add to PATH：https://www.python.org/downloads/" -ForegroundColor Red
    return
}
Write-Host ("       -> {0} {1} (Python {2})" -f $py.Exe, ($py.Args -join " "), $py.Version) -ForegroundColor Green

# 3 venv
Step-Progress "準備虛擬環境 .venv"
if (-not (Test-Path $VenvPy)) {
    try {
        & $py.Exe @($py.Args) "-m" "venv" $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "venv 失敗" }
    } catch {
        Write-Host ("       venv 失敗，改用系統 Python：{0}" -f $_.Exception.Message) -ForegroundColor DarkYellow
        $VenvPy = $py.Exe
    }
}

# 4 升級 pip
Step-Progress "升級 pip"
if (-not $SkipDeps -and $VenvPy -ne $py.Exe) {
    try { & $VenvPy "-m" "pip" "install" "--upgrade" "pip" "--quiet" "--disable-pip-version-check" 2>$null | Out-Null } catch { }
}

# 5-7 批次安裝三組依賴（不逐個、不卡斷）
if (-not $SkipDeps -and $VenvPy -ne $py.Exe) {
    Step-Progress "安裝核心依賴（office/pdf/text）"
    Install-Group "core" @("python-docx", "python-pptx", "pypdf", "pikepdf", "odfpy", "beautifulsoup4", "charset-normalizer", "striprtf", "rich")
    Step-Progress "安裝資料依賴（pandas/openpyxl）"
    Install-Group "data" @("pandas", "openpyxl", "pillow")
    Step-Progress "安裝連接器依賴（google/msal/pywin32）"
    Install-Group "conn" @("google-auth-oauthlib", "google-api-python-client", "msal", "pywin32")
} else {
    Step-Progress "略過依賴（-SkipDeps）"
    Step-Progress "略過依賴"
    Step-Progress "略過依賴"
}

Push-Location $Root

# 8 驗證 3 強引擎可載入
Step-Progress "載入 3 強引擎（庫/牡/觀）"
& $VenvPy "-c" "import via_dataforge,via_mailhub,via_insight" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "       -> 庫 DataForge / 牡 MailHub / 觀 Insight 就緒" -ForegroundColor Green }

# 9 樞 self-test
Step-Progress "SystemManager 自我測試"
& $VenvPy "via_manager.py" "--selftest"
if ($LASTEXITCODE -ne 0) { Write-Host "       self-test 有紅字（仍可啟動）" -ForegroundColor DarkYellow }

# 10 驗收矩陣快檢
Step-Progress "驗收矩陣快檢（可略）"
if (-not $SelfTestOnly) {
    & $VenvPy "-c" "import via_dataforge,via_mailhub,via_insight,via_manager,via_server; print('imports OK')" 2>$null | Out-Null
}

Pop-Location

if ($SelfTestOnly) {
    Write-Progress -Activity "VIA_Forge" -Completed
    Write-Host "（--SelfTestOnly：僅測試，未啟動）" -ForegroundColor DarkGray
    return
}

# 11 選埠
Step-Progress "選用埠 127.0.0.1:8780-8800"

# 12 預熱狀態
Step-Progress "預熱共用語料狀態（樞）"

# 13 背景：等待就緒後開瀏覽器
Step-Progress "掛載 HTML U/I 開啟器"
$browserJob = $null
if (-not $NoBrowser) {
    $browserJob = Start-Job -ScriptBlock {
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Milliseconds 500
            foreach ($p in 8780..8800) {
                try {
                    $c = New-Object System.Net.Sockets.TcpClient
                    $c.Connect("127.0.0.1", $p)
                    if ($c.Connected) {
                        $c.Close()
                        Start-Process ("http://127.0.0.1:{0}/" -f $p)
                        return
                    }
                } catch { }
            }
        }
    }
}

# 14 啟動後端（前景，串流；Ctrl+C 可停）
Step-Progress "啟動後端 server（前景）"

# 15 完成進度條，交棒給 server
Step-Progress "連結 HTML U/I → 就緒"
Write-Progress -Activity "VIA_Forge 啟動加速器" -Completed
Write-Host "---------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  後端啟動中；瀏覽器就緒後自動開啟 HTML U/I。" -ForegroundColor Green
Write-Host "  停止：在此視窗按 Ctrl+C。" -ForegroundColor DarkGray
Write-Host "---------------------------------------------------------------" -ForegroundColor Cyan

Push-Location $Root
$serverArgs = @("via_server.py", "--no-browser")
try {
    & $VenvPy @serverArgs
} finally {
    Pop-Location
    if ($null -ne $browserJob) { Remove-Job -Job $browserJob -Force -ErrorAction SilentlyContinue }
}
Write-Host "VIA_Forge 已停止。" -ForegroundColor Cyan

