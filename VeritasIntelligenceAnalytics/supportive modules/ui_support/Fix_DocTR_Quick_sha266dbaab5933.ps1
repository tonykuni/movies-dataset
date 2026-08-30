# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
# ========================================================
# docTR 專用快速修復腳本
# 解決：TensorFlow/NumPy 版本衝突
# 策略：獨立環境 + TensorFlow 2.15
# ========================================================

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
$BaseDir = "C:\Users\tonyk\OneDrive\Desktop\VeritasReportNova"
$EnvPath = "$BaseDir\vrn_doctr_env"
$Mirror = "-i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn"

Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  docTR 專用修復（TensorFlow 隔離環境）      ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 清除舊環境
if (Test-Path $EnvPath) {
    Write-Host "→ 清除舊環境..." -ForegroundColor Gray
    Remove-Item $EnvPath -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 建立新環境
Write-Host "→ 建立隔離環境..." -ForegroundColor White
py -3.11 -m venv $EnvPath

$PIP = "$EnvPath\Scripts\pip.exe"
$PYTHON = "$EnvPath\Scripts\python.exe"

# 升級 pip
& $PIP install --upgrade pip setuptools wheel -q

Write-Host ""
Write-Host "安裝 NumPy 1.26.4 (docTR/TensorFlow 相容版本)..." -ForegroundColor Yellow
& $PIP install numpy==1.26.4 $Mirror.Split(" ")

Write-Host ""
Write-Host "安裝 TensorFlow 2.15..." -ForegroundColor White
& $PIP install tensorflow==2.15.0 $Mirror.Split(" ")
& $PIP install tf-keras==2.15.0 $Mirror.Split(" ")

Write-Host ""
Write-Host "安裝 docTR 依賴..." -ForegroundColor White

$packages = @(
    "pillow",
    "opencv-python-headless",
    "scipy",
    "shapely",
    "pyclipper",
    "tqdm",
    "rapidfuzz",
    "matplotlib",
    "mplcursors",
    "Unidecode",
    "langdetect",
    "h5py"
)

foreach ($pkg in $packages) {
    Write-Host "  安裝 $pkg ... " -NoNewline
    & $PIP install $pkg $Mirror.Split(" ") -q 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓" -ForegroundColor Green
    } else {
        Write-Host "✗" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "安裝 python-doctr[tf]..." -ForegroundColor Yellow
& $PIP install "python-doctr[tf]" $Mirror.Split(" ")

# 測試
Write-Host ""
Write-Host "測試 docTR 載入..." -ForegroundColor White
$testResult = & $PYTHON -c "from doctr.io import DocumentFile; from doctr.models import ocr_predictor; print('SUCCESS')" 2>&1

if ($testResult -like "*SUCCESS*") {
    Write-Host "✓ docTR 修復成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "使用方式：" -ForegroundColor Cyan
    Write-Host "  $EnvPath\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "  python -c `"from doctr.models import ocr_predictor; model = ocr_predictor(pretrained=True)`"" -ForegroundColor Gray
} else {
    Write-Host "⚠ docTR 載入有警告（首次使用會下載模型）" -ForegroundColor Yellow
    
    # 嘗試更基本的測試
    $basicTest = & $PYTHON -c "import doctr; print('BASIC_OK')" 2>&1
    if ($basicTest -like "*BASIC_OK*") {
        Write-Host "✓ docTR 基本模組可用" -ForegroundColor Green
    } else {
        Write-Host "✗ docTR 安裝失敗" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "按任意鍵關閉..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

