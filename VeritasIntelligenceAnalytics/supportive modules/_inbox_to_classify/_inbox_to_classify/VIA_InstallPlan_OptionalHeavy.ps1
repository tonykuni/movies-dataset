param(
    [bool]$InstallHeavyPythonPackages = $false,
    [bool]$KeepPowerShellOpen = $true
)

# Optional heavy package plan.
# Default is review-only. Set -InstallHeavyPythonPackages $true only inside a dedicated sandbox venv.
$packages_light = @("pandas","polars","duckdb","pyarrow","pm4py","networkx","pandera","rich","tqdm")
$packages_heavy = @("docling","paddleocr","ocrmypdf","pytesseract","pdfplumber","pymupdf","camelot-py","tabula-py","opencv-python","unstructured","markitdown","tika","great_expectations")

function def_InstallPipPackageList {
    param([string[]]$Packages)
    foreach ($pkg in $Packages) {
        Write-Host "[PIP] $pkg" -ForegroundColor Cyan
        python -m pip install $pkg
    }
}

Write-Host "Review packages first. Heavy install is disabled by default." -ForegroundColor Yellow
Write-Host "Light packages: $($packages_light -join ', ')"
Write-Host "Heavy packages: $($packages_heavy -join ', ')"

if ($InstallHeavyPythonPackages) {
    def_InstallPipPackageList -Packages $packages_light
    def_InstallPipPackageList -Packages $packages_heavy
} else {
    Write-Host "DRY_RUN: no Python package installed." -ForegroundColor Green
}

if ($KeepPowerShellOpen) {
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
