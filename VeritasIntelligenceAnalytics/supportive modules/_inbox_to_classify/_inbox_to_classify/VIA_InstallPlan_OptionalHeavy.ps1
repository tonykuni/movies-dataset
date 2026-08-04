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
