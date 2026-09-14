# =====================================================================
#  TWREV 台股月營收動能引擎 — 非阻塞啟動器 (launch.ps1)
#  用法:
#     .\launch.ps1              # 完整流程: fetch -> analyze -> report -> 開啟儀表板
#     .\launch.ps1 -Mode demo   # 免網路, 用合成資料跑完整流程 (驗證安裝)
#     .\launch.ps1 -Mode test   # 只跑 20 項內建測試
#     .\launch.ps1 -Background  # 丟到背景執行, 不佔用這個視窗、不卡斷
#  說明:
#     MOPS 有速率限制, 首次抓 36 個月全市場約需 20-40 分鐘 (之後走快取)。
#     -Background 會把 stdout/stderr 導到 logs\ 並立刻交還提示字元。
# =====================================================================
[CmdletBinding()]
param(
    [ValidateSet('run', 'demo', 'fetch', 'analyze', 'report', 'groups', 'breakout', 'test')]
    [string]$Mode = 'run',
    [switch]$Background,
    [switch]$NoOpen,
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $Root

$LogDir = Join-Path $Root 'logs'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Write-Step($msg) { Write-Host "  [TWREV] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [ OK ] $msg" -ForegroundColor Green }
function Write-Warn2($m)  { Write-Host "  [WARN] $m" -ForegroundColor Yellow }

# ---- 1. 環境檢查與自動配置 ----------------------------------------
Write-Step "檢查 Python 環境..."
try {
    $pyv = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
} catch {
    throw "找不到 Python。請安裝 Python 3.10+ 並確認 'python' 在 PATH 中, 或用 -Python 指定路徑。"
}
if (-not $pyv) { throw "無法執行 '$Python'。請用 -Python 指定 python.exe 完整路徑。" }
Write-Ok "Python $pyv"

$VenvDir = Join-Path $Root '.venv'
$VenvPy  = Join-Path $VenvDir 'Scripts\python.exe'
if (-not (Test-Path $VenvPy)) {
    Write-Step "建立虛擬環境 .venv (只做一次)..."
    & $Python -m venv $VenvDir
    Write-Ok "虛擬環境建立完成"
}

Write-Step "檢查相依套件..."
$needInstall = $true
try {
    & $VenvPy -c "import pandas, requests, yaml, lxml, pyarrow" 2>$null
    if ($LASTEXITCODE -eq 0) { $needInstall = $false }
} catch { }
if ($needInstall) {
    Write-Step "安裝相依套件 (首次執行約 1-2 分鐘)..."
    & $VenvPy -m pip install --upgrade pip --quiet
    & $VenvPy -m pip install -r (Join-Path $Root 'requirements.txt') --quiet
    Write-Ok "相依套件安裝完成"
} else {
    Write-Ok "相依套件齊備"
}

foreach ($d in @('data', 'output', 'data\raw_cache')) {
    $p = Join-Path $Root $d
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

# ---- 2. 執行 -------------------------------------------------------
$cliArgs = @('-m', 'twrevenue.cli', $(if ($Mode -eq 'test') { 'selftest' } else { $Mode }))
$LogOut = Join-Path $LogDir "twrev_${Mode}_${Stamp}.log"
$LogErr = Join-Path $LogDir "twrev_${Mode}_${Stamp}.err.log"

if ($Background) {
    Write-Step "背景啟動 ($Mode) — 不關閉、不阻塞、不卡斷"
    $p = Start-Process -FilePath $VenvPy -ArgumentList $cliArgs -WorkingDirectory $Root `
        -RedirectStandardOutput $LogOut -RedirectStandardError $LogErr `
        -WindowStyle Hidden -PassThru
    Write-Ok "PID $($p.Id) 已啟動"
    Write-Host ""
    Write-Host "  即時追蹤: Get-Content -Wait '$LogOut'" -ForegroundColor DarkGray
    Write-Host "  查看狀態: Get-Process -Id $($p.Id)"                 -ForegroundColor DarkGray
    Write-Host "  停止    : Stop-Process -Id $($p.Id)"                -ForegroundColor DarkGray
    return
}

Write-Step "執行 $Mode ..."
& $VenvPy @cliArgs 2>&1 | Tee-Object -FilePath $LogOut
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Warn2 "結束碼 $code — 詳見 $LogOut"
    exit $code
}
Write-Ok "$Mode 完成  (log: $LogOut)"

# ---- 3. 自動跳出 HTML UI Matrix ------------------------------------
if (-not $NoOpen -and $Mode -in @('run', 'demo', 'report')) {
    $html = Join-Path $Root 'output\monthly_revenue_dashboard.html'
    if (Test-Path $html) {
        Write-Step "開啟儀表板..."
        Start-Process $html
        Write-Ok $html
    } else {
        Write-Warn2 "找不到儀表板檔案: $html"
    }
}
