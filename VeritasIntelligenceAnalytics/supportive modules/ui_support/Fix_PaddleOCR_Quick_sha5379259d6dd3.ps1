# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
# ========================================================
# PaddleOCR 專用快速修復腳本
# 解決：NumPy 2.x 污染導致 PaddleOCR Bypassed
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
$EnvPath = "$BaseDir\vrn_paddle_env"
$Mirror = "-i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn"

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PaddleOCR 專用修復（NumPy 1.24.3 鎖定）  ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
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
Write-Host "【關鍵步驟】鎖定 NumPy 1.24.3" -ForegroundColor Yellow
& $PIP install numpy==1.24.3 $Mirror.Split(" ")

Write-Host ""
Write-Host "安裝 PaddlePaddle 依賴..." -ForegroundColor White

$packages = @(
    "pillow==10.4.0",
    "protobuf==3.20.3",
    "shapely",
    "pyclipper",
    "imgaug==0.4.0",
    "lmdb",
    "tqdm",
    "visualdl",
    "rapidfuzz",
    "opencv-python-headless==4.10.0.84",
    "scikit-image==0.21.0",
    "paddlepaddle==2.6.2"
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
Write-Host "安裝 PaddleOCR (--no-deps 防止污染)..." -ForegroundColor Yellow
& $PIP install paddleocr==2.9.1 --no-deps $Mirror.Split(" ")

# 修復可能被污染的 NumPy
Write-Host ""
Write-Host "驗證 NumPy 版本..." -ForegroundColor White
$numpyVer = & $PYTHON -c "import numpy; print(numpy.__version__)"

if ($numpyVer -like "2.*") {
    Write-Host "⚠ NumPy 被污染！正在修復..." -ForegroundColor Red
    & $PIP uninstall numpy -y
    & $PIP install numpy==1.24.3 --force-reinstall --no-deps $Mirror.Split(" ")
}

$finalVer = & $PYTHON -c "import numpy; print(numpy.__version__)"
Write-Host "NumPy 最終版本: $finalVer" -ForegroundColor $(if($finalVer -like "1.24.*"){"Green"}else{"Red"})

# 測試
Write-Host ""
Write-Host "測試 PaddleOCR 載入..." -ForegroundColor White
$testResult = & $PYTHON -c "from paddleocr import PaddleOCR; print('SUCCESS')" 2>&1

if ($testResult -like "*SUCCESS*") {
    Write-Host "✓ PaddleOCR 修復成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "使用方式：" -ForegroundColor Cyan
    Write-Host "  $EnvPath\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "  python -c `"from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='ch')`"" -ForegroundColor Gray
} else {
    Write-Host "✗ PaddleOCR 載入失敗" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "按任意鍵關閉..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

