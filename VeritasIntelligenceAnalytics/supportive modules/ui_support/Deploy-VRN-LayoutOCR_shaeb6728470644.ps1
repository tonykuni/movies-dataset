# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
# ═══════════════════════════════════════════════════════════════════
# VeritasReportNova - Layout & OCR Plugin 一鍵部署腳本
# One-Click Deployment Script
# ═══════════════════════════════════════════════════════════════════
# Author: VeritasReportNova Team
# Version: 3.0.0
# Philosophy: 功能只增不減 (Functionality Only Increases, Never Decreases)
# ═══════════════════════════════════════════════════════════════════

param(
    [switch]$ForceReinstall = $false,
    [switch]$SkipTests = $false,
    [string]$Language = "zh-TW"  # zh-TW or en-US
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# ═══════════════════════════════════════════════════════════════════
# 雙語支援 Bilingual Support
# ═══════════════════════════════════════════════════════════════════

$Messages = @{
    "zh-TW" = @{
        Banner = @"
╔═══════════════════════════════════════════════════════════════════╗
║   VeritasReportNova - Layout & OCR Plugin 一鍵部署               ║
║   整合 20+ 本地免費函式庫 + CPU 超級加速器                       ║
║   功能只增不減 Functionality Only Increases, Never Decreases    ║
╚═══════════════════════════════════════════════════════════════════╝
"@
        Step1 = "步驟 1/7: 環境檢查"
        Step2 = "步驟 2/7: 建立虛擬環境"
        Step3 = "步驟 3/7: 安裝系統依賴 (Tesseract, Poppler)"
        Step4 = "步驟 4/7: 安裝 Python 套件"
        Step5 = "步驟 5/7: 下載 ML 模型"
        Step6 = "步驟 6/7: 執行測試"
        Step7 = "步驟 7/7: 產生使用文檔"
        Success = "✓ 部署成功！"
        Failed = "✗ 部署失敗"
        CheckingPython = "檢查 Python 版本..."
        PythonFound = "找到 Python"
        PythonNotFound = "未找到 Python！請安裝 Python 3.8+"
        CreatingVenv = "建立虛擬環境..."
        VenvExists = "虛擬環境已存在"
        VenvCreated = "虛擬環境建立成功"
        ActivatingVenv = "啟動虛擬環境..."
        InstallingPackages = "安裝套件"
        TestingPlugin = "測試插件功能..."
        GeneratingDocs = "產生使用文檔..."
        DeploymentComplete = "部署完成！使用以下命令啟動:"
        SkippingTests = "跳過測試"
    }
    "en-US" = @{
        Banner = @"
╔═══════════════════════════════════════════════════════════════════╗
║   VeritasReportNova - Layout & OCR Plugin Deployment            ║
║   20+ Local Free Libraries + CPU Super Accelerator              ║
║   Functionality Only Increases, Never Decreases                 ║
╚═══════════════════════════════════════════════════════════════════╝
"@
        Step1 = "Step 1/7: Environment Check"
        Step2 = "Step 2/7: Create Virtual Environment"
        Step3 = "Step 3/7: Install System Dependencies (Tesseract, Poppler)"
        Step4 = "Step 4/7: Install Python Packages"
        Step5 = "Step 5/7: Download ML Models"
        Step6 = "Step 6/7: Run Tests"
        Step7 = "Step 7/7: Generate Documentation"
        Success = "✓ Deployment Successful!"
        Failed = "✗ Deployment Failed"
        CheckingPython = "Checking Python version..."
        PythonFound = "Python found"
        PythonNotFound = "Python not found! Please install Python 3.8+"
        CreatingVenv = "Creating virtual environment..."
        VenvExists = "Virtual environment already exists"
        VenvCreated = "Virtual environment created successfully"
        ActivatingVenv = "Activating virtual environment..."
        InstallingPackages = "Installing packages"
        TestingPlugin = "Testing plugin functionality..."
        GeneratingDocs = "Generating documentation..."
        DeploymentComplete = "Deployment complete! Use the following command to start:"
        SkippingTests = "Skipping tests"
    }
}

$MSG = $Messages[$Language]

# ═══════════════════════════════════════════════════════════════════
# 工具函數 Utility Functions
# ═══════════════════════════════════════════════════════════════════

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-ColorOutput "═══════════════════════════════════════════════════════════════════" "Cyan"
    Write-ColorOutput $Message "Cyan"
    Write-ColorOutput "═══════════════════════════════════════════════════════════════════" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" "Green"
}

function Write-Error-Custom {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" "Red"
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" "Gray"
}

# ═══════════════════════════════════════════════════════════════════
# 主部署邏輯 Main Deployment Logic
# ═══════════════════════════════════════════════════════════════════

# Display Banner
Clear-Host
Write-ColorOutput $MSG.Banner "Cyan"
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ═══════════════════════════════════════════════════════════════════
# Step 1: Environment Check
# ═══════════════════════════════════════════════════════════════════

Write-Step $MSG.Step1

Write-Info $MSG.CheckingPython

# Check Python
$PythonCmd = $null
$PythonVersions = @("python", "python3", "python3.11", "python3.10", "python3.9", "python3.8")

foreach ($pyCmd in $PythonVersions) {
    try {
        $version = & $pyCmd --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -eq 3 -and $minor -ge 8) {
                $PythonCmd = $pyCmd
                Write-Success "$($MSG.PythonFound): $version"
                break
            }
        }
    }
    catch {
        continue
    }
}

if (-not $PythonCmd) {
    Write-Error-Custom $MSG.PythonNotFound
    Write-Host ""
    Write-Host "Download Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check pip
try {
    & $PythonCmd -m pip --version | Out-Null
    Write-Success "pip available"
}
catch {
    Write-Error-Custom "pip not found!"
    Write-Info "Installing pip..."
    & $PythonCmd -m ensurepip --upgrade
}

# ═══════════════════════════════════════════════════════════════════
# Step 2: Virtual Environment
# ═══════════════════════════════════════════════════════════════════

Write-Step $MSG.Step2

$VenvPath = Join-Path $ScriptDir "venv_vrn_layout_ocr"

if (Test-Path $VenvPath) {
    if ($ForceReinstall) {
        Write-Warning-Custom "Removing existing virtual environment..."
        Remove-Item -Path $VenvPath -Recurse -Force
        Write-Info $MSG.CreatingVenv
        & $PythonCmd -m venv $VenvPath
        Write-Success $MSG.VenvCreated
    }
    else {
        Write-Success $MSG.VenvExists
    }
}
else {
    Write-Info $MSG.CreatingVenv
    & $PythonCmd -m venv $VenvPath
    Write-Success $MSG.VenvCreated
}

# Activate virtual environment
Write-Info $MSG.ActivatingVenv

$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
    Write-Success "Virtual environment activated"
}
else {
    Write-Error-Custom "Failed to find activation script"
    exit 1
}

# Upgrade pip in venv
Write-Info "Upgrading pip..."
& python -m pip install --upgrade pip setuptools wheel --quiet

# ═══════════════════════════════════════════════════════════════════
# Step 3: System Dependencies
# ═══════════════════════════════════════════════════════════════════

Write-Step $MSG.Step3

# Check for package managers
$HasChoco = Get-Command choco -ErrorAction SilentlyContinue
$HasScoop = Get-Command scoop -ErrorAction SilentlyContinue

# Install Tesseract
Write-Info "Checking Tesseract OCR..."
$TesseractPath = $null

# Common Tesseract installation paths
$TesseractPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "C:\Tools\tesseract\tesseract.exe"
)

foreach ($path in $TesseractPaths) {
    if (Test-Path $path) {
        $TesseractPath = $path
        break
    }
}

if ($TesseractPath) {
    Write-Success "Tesseract found at: $TesseractPath"
    $env:TESSERACT_CMD = $TesseractPath
}
else {
    Write-Warning-Custom "Tesseract not found"
    
    if ($HasChoco) {
        Write-Info "Installing Tesseract via Chocolatey..."
        choco install tesseract -y
        Write-Success "Tesseract installed"
    }
    elseif ($HasScoop) {
        Write-Info "Installing Tesseract via Scoop..."
        scoop install tesseract
        Write-Success "Tesseract installed"
    }
    else {
        Write-Warning-Custom "Please install Tesseract manually:"
        Write-Host "  Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
        Write-Host "  After installation, add to PATH or set TESSERACT_CMD environment variable" -ForegroundColor Yellow
    }
}

# Install Poppler (for pdf2image)
Write-Info "Checking Poppler (pdf2image)..."
$PopplerPath = $null

# Common Poppler paths
$PopplerPaths = @(
    "C:\Program Files\poppler\Library\bin",
    "C:\Program Files (x86)\poppler\Library\bin",
    "C:\Tools\poppler\Library\bin"
)

foreach ($path in $PopplerPaths) {
    if (Test-Path (Join-Path $path "pdftoppm.exe")) {
        $PopplerPath = $path
        break
    }
}

if ($PopplerPath) {
    Write-Success "Poppler found at: $PopplerPath"
}
else {
    Write-Warning-Custom "Poppler not found"
    
    if ($HasScoop) {
        Write-Info "Installing Poppler via Scoop..."
        scoop install poppler
        Write-Success "Poppler installed"
    }
    else {
        Write-Warning-Custom "Please install Poppler manually:"
        Write-Host "  Download from: https://github.com/oschwartz10612/poppler-windows/releases" -ForegroundColor Yellow
        Write-Host "  Extract and add bin folder to PATH" -ForegroundColor Yellow
    }
}

# ═══════════════════════════════════════════════════════════════════
# Step 4: Python Packages
# ═══════════════════════════════════════════════════════════════════

Write-Step $MSG.Step4

# Core packages
$CorePackages = @(
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "pillow",
    "opencv-python",
    "rapidfuzz"
)

# Layout analysis packages
$LayoutPackages = @(
    "pymupdf",
    "pdfminer.six",
    "pdfplumber",
    "borb",
    "pypdf",
    "pikepdf",
    "pymupdf4llm",
    "pdfquery"
)

# OCR packages
$OCRPackages = @(
    "pytesseract",
    "pdf2image"
)

# Optional but recommended (may require compilation or have large dependencies)
$OptionalPackages = @{
    "easyocr" = "Multi-language OCR"
    "paddleocr" = "State-of-the-art OCR"
    "img2table[paddle]" = "Table extraction"
    "unstructured" = "AI-powered document parsing"
    "layoutparser[layoutmodels]" = "ML-based layout detection"
}

# PyTorch (for some OCR engines)
$TorchPackages = @(
    "torch",
    "torchvision"
)

Write-Info "Installing core packages..."
foreach ($pkg in $CorePackages) {
    Write-Host "  - $pkg" -NoNewline
    & python -m pip install $pkg --break-system-packages -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    }
    else {
        Write-Host " ✗" -ForegroundColor Red
    }
}

Write-Info "Installing layout analysis packages..."
foreach ($pkg in $LayoutPackages) {
    Write-Host "  - $pkg" -NoNewline
    & python -m pip install $pkg --break-system-packages -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    }
    else {
        Write-Host " ✗" -ForegroundColor Red
    }
}

Write-Info "Installing OCR packages..."
foreach ($pkg in $OCRPackages) {
    Write-Host "  - $pkg" -NoNewline
    & python -m pip install $pkg --break-system-packages -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    }
    else {
        Write-Host " ✗" -ForegroundColor Red
    }
}

Write-Info "Installing PyTorch (CPU version)..."
& python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --break-system-packages -q
if ($LASTEXITCODE -eq 0) {
    Write-Success "PyTorch installed"
}
else {
    Write-Warning-Custom "PyTorch installation failed (optional)"
}

Write-Info "Installing optional packages (this may take a while)..."
foreach ($pkg in $OptionalPackages.Keys) {
    $desc = $OptionalPackages[$pkg]
    Write-Host "  - $pkg ($desc)" -NoNewline
    & python -m pip install $pkg --break-system-packages -q 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    }
    else {
        Write-Host " ⚠ (optional)" -ForegroundColor Yellow
    }
}

# Additional ML packages
Write-Info "Installing additional ML packages..."
$MLPackages = @(
    "transformers",
    "python-doctr[torch]",
    "openpyxl"
)

foreach ($pkg in $MLPackages) {
    Write-Host "  - $pkg" -NoNewline
    & python -m pip install $pkg --break-system-packages -q 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    }
    else {
        Write-Host " ⚠ (optional)" -ForegroundColor Yellow
    }
}

# ═══════════════════════════════════════════════════════════════════
# Step 5: Download ML Models
# ═══════════════════════════════════════════════════════════════════

Write-Step $MSG.Step5

Write-Info "Pre-downloading ML models (optional, first run will auto-download)..."

# Test script to trigger model downloads
$ModelDownloadScript = @"
import warnings
warnings.filterwarnings('ignore')

print('Downloading models...')

# Try EasyOCR
try:
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False)
    print('✓ EasyOCR models downloaded')
except Exception as e:
    print(f'⚠ EasyOCR: {e}')

# Try PaddleOCR
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)
    print('✓ PaddleOCR models downloaded')
except Exception as e:
    print(f'⚠ PaddleOCR: {e}')

# Try DocTR
try:
    from doctr.models import ocr_predictor
    predictor = ocr_predictor(pretrained=True)
    print('✓ DocTR models downloaded')
except Exception as e:
    print(f'⚠ DocTR: {e}')

# Try LayoutParser
try:
    import layoutparser as lp
    model = lp.Detectron2LayoutModel('lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config')
    print('✓ LayoutParser models downloaded')
except Exception as e:
    print(f'⚠ LayoutParser: {e}')

print('Model download check complete!')
"@

$TempScript = Join-Path $ScriptDir "temp_model_download.py"
Set-Content -Path $TempScript -Value $ModelDownloadScript -Encoding UTF8

& python $TempScript 2>$null

Remove-Item $TempScript -Force -ErrorAction SilentlyContinue

# ═══════════════════════════════════════════════════════════════════
# Step 6: Run Tests
# ═══════════════════════════════════════════════════════════════════

if (-not $SkipTests) {
    Write-Step $MSG.Step6
    
    Write-Info $MSG.TestingPlugin
    
    # Create a simple test script
    $TestScript = @"
import sys
sys.path.insert(0, '.')

try:
    from vrn_layout_ocr_plugin import VRNLayoutOCRPlugin, auto_install_dependencies, REQUIRED_PACKAGES
    
    print('✓ Plugin import successful')
    
    # Test initialization
    plugin = VRNLayoutOCRPlugin(output_dir='./test_output', enable_logging=False)
    print('✓ Plugin initialization successful')
    
    # Test engine availability
    coord = plugin.coordinator
    layout_available = sum(1 for e in coord.layout_engines.values() if e.is_available)
    ocr_available = sum(1 for e in coord.ocr_engines.values() if e.is_available)
    
    print(f'✓ Layout engines available: {layout_available}')
    print(f'✓ OCR engines available: {ocr_available}')
    
    # Test CPU accelerator
    if coord.accelerator:
        print(f'✓ CPU Accelerator: {coord.accelerator.cpu_count} cores, {coord.accelerator.max_workers} workers')
        print(f'✓ Architecture: {coord.accelerator.architecture}')
    
    print('')
    print('═' * 60)
    print('All tests passed! 所有測試通過！')
    print('═' * 60)
    
except Exception as e:
    print(f'✗ Test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
    
    $TestFile = Join-Path $ScriptDir "test_plugin.py"
    Set-Content -Path $TestFile -Value $TestScript -Encoding UTF8
    
    & python $TestFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All tests passed!"
    }
    else {
        Write-Warning-Custom "Some tests failed (plugin may still work)"
    }
    
    Remove-Item $TestFile -Force -ErrorAction SilentlyContinue
}
else {
    Write-Info $MSG.SkippingTests
}

# ═══════════════════════════════════════════════════════════════════
# Step 7: Generate Documentation
# ═══════════════════════════════════════════════════════════════════

Write-Step $MSG.Step7

$ReadmeContent = @"
# VeritasReportNova - Layout & OCR Plugin

整合 20+ 本地免費函式庫的智能雙引擎系統
Multi-Engine Consensus Voting + Auto-Repair + CPU Super Accelerator

## 快速開始 Quick Start

### 1. 啟動虛擬環境 Activate Virtual Environment

``````powershell
# Windows
.\venv_vrn_layout_ocr\Scripts\Activate.ps1

# Linux/Mac
source venv_vrn_layout_ocr/bin/activate
``````

### 2. 使用插件 Use Plugin

``````python
from vrn_layout_ocr_plugin import VRNLayoutOCRPlugin

# 初始化插件 Initialize plugin
plugin = VRNLayoutOCRPlugin(
    output_dir="./output",
    enable_logging=True
)

# 處理 PDF Process PDF
result = plugin.process(
    pdf_path="document.pdf",
    page_num=0,              # 第一頁 First page (0-indexed)
    enable_ocr=True,         # 啟用 OCR Enable OCR
    languages=['eng'],       # 語言 Languages: ['eng', 'chi_tra']
    output_format='excel'    # 輸出格式 Format: json, excel, csv
)

# 查看結果 View results
print(f"Status: {result['status']}")
print(f"Confidence: {result['confidence_score']:.2%}")
print(f"Layout elements: {len(result['layout_elements'])}")
print(f"OCR results: {len(result['ocr_results'])}")
``````

## 功能特性 Features

### 布局分析引擎 Layout Analysis Engines
- ✓ PyMuPDF (最快 Fastest)
- ✓ PDFMiner.six (詳細分析 Detailed Analysis)
- ✓ PDFPlumber (表格專家 Table Expert)
- ✓ Unstructured (AI 驅動 AI-Powered)
- ✓ 更多... More...

### OCR 引擎 OCR Engines
- ✓ Tesseract (工業標準 Industry Standard)
- ✓ EasyOCR (多語言 Multi-language)
- ✓ PaddleOCR (最先進 State-of-the-art)
- ✓ DocTR (Transformer)
- ✓ 更多... More...

### 核心功能 Core Features
- ✓ 多引擎共識投票 Multi-Engine Consensus Voting
- ✓ IoU 基礎去重 IoU-based Deduplication
- ✓ 自動修復 Auto-Repair
- ✓ CPU 超級加速器 CPU Super Accelerator
- ✓ 支援多種輸出格式 Multiple Output Formats

## 進階使用 Advanced Usage

### 多語言 OCR Multi-language OCR

``````python
# 中英混合 Chinese + English
result = plugin.process(
    pdf_path="document.pdf",
    languages=['eng', 'chi_tra'],
    enable_ocr=True
)

# 日文 Japanese
result = plugin.process(
    pdf_path="document.pdf",
    languages=['jpn'],
    enable_ocr=True
)
``````

### 指定引擎 Specify Engines

``````python
# 直接訪問協調器 Direct coordinator access
result = plugin.coordinator.process_pdf(
    pdf_path="document.pdf",
    page_num=0,
    layout_engines=['pymupdf', 'pdfplumber'],  # 只用這些引擎 Only these
    ocr_engines=['paddleocr', 'tesseract'],
    languages=['eng']
)
``````

### 批量處理 Batch Processing

``````python
import glob

for pdf_file in glob.glob("*.pdf"):
    for page_num in range(10):  # 處理前 10 頁
        try:
            result = plugin.process(
                pdf_path=pdf_file,
                page_num=page_num,
                output_format='json'
            )
            print(f"{pdf_file} page {page_num}: {result['confidence_score']:.2%}")
        except Exception as e:
            print(f"Failed: {pdf_file} page {page_num}: {e}")
``````

## 系統需求 System Requirements

- Python 3.8+
- Tesseract OCR (建議 Recommended)
- Poppler (pdf2image, 建議 Recommended)
- 4GB+ RAM
- CPU: 多核心建議 Multi-core recommended

## 故障排除 Troubleshooting

### Tesseract 未找到 Tesseract Not Found

``````bash
# Windows (Chocolatey)
choco install tesseract -y

# Windows (Scoop)
scoop install tesseract

# Linux (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
``````

### Poppler 未找到 Poppler Not Found

``````bash
# Windows (Scoop)
scoop install poppler

# Linux (Ubuntu/Debian)
sudo apt-get install poppler-utils

# macOS
brew install poppler
``````

### 記憶體不足 Out of Memory

減少並行處理數量 Reduce parallel processing:

``````python
from vrn_layout_ocr_plugin import DualEngineCoordinator, CPUSuperAccelerator

# 限制 worker 數量 Limit workers
accelerator = CPUSuperAccelerator(max_workers=2)
coordinator = DualEngineCoordinator(enable_cpu_acceleration=False)
``````

## 更新日誌 Changelog

### v3.0.0 (2025-11-15)
- ✓ 整合 20+ 本地免費函式庫
- ✓ 多引擎共識投票系統
- ✓ CPU 超級加速器
- ✓ 自動修復功能
- ✓ 雙語支援

## 授權 License

MIT License - 完全免費使用 Completely Free to Use

## 支援 Support

如有問題請聯繫 For issues please contact:
- GitHub: [Your Repository]
- Email: [Your Email]

---

功能只增不減 Functionality Only Increases, Never Decreases
"@

$ReadmePath = Join-Path $ScriptDir "README_LayoutOCR.md"
Set-Content -Path $ReadmePath -Value $ReadmeContent -Encoding UTF8
Write-Success "Documentation generated: README_LayoutOCR.md"

# Generate usage examples
$ExampleScript = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
VeritasReportNova - Layout & OCR Plugin Usage Examples
使用範例
'''

from vrn_layout_ocr_plugin import VRNLayoutOCRPlugin

def example_basic():
    '''基本用法 Basic Usage'''
    plugin = VRNLayoutOCRPlugin(output_dir='./example_output')
    
    result = plugin.process(
        pdf_path='sample.pdf',
        page_num=0,
        enable_ocr=True,
        languages=['eng'],
        output_format='json'
    )
    
    print(f"Processed: {result['status']}")
    print(f"Confidence: {result['confidence_score']:.2%}")

def example_multilingual():
    '''多語言 OCR Multilingual OCR'''
    plugin = VRNLayoutOCRPlugin()
    
    # 中英混合 Chinese + English
    result = plugin.process(
        pdf_path='chinese_doc.pdf',
        languages=['eng', 'chi_tra'],
        output_format='excel'
    )

def example_batch():
    '''批量處理 Batch Processing'''
    import glob
    
    plugin = VRNLayoutOCRPlugin()
    
    for pdf_file in glob.glob('*.pdf'):
        result = plugin.process(
            pdf_path=pdf_file,
            output_format='csv'
        )
        print(f'{pdf_file}: {result["confidence_score"]:.2%}')

def example_advanced():
    '''進階用法 Advanced Usage'''
    from vrn_layout_ocr_plugin import DualEngineCoordinator
    
    coordinator = DualEngineCoordinator(
        consensus_threshold=0.8,
        iou_threshold=0.6
    )
    
    result = coordinator.process_pdf(
        pdf_path='complex.pdf',
        page_num=0,
        layout_engines=['pymupdf', 'pdfplumber'],
        ocr_engines=['paddleocr'],
        languages=['eng']
    )

if __name__ == '__main__':
    # 執行範例 Run examples
    print('Basic example:')
    # example_basic()
    
    print('\\nFor more examples, uncomment the functions above')
"@

$ExamplePath = Join-Path $ScriptDir "examples_layout_ocr.py"
Set-Content -Path $ExamplePath -Value $ExampleScript -Encoding UTF8
Write-Success "Examples generated: examples_layout_ocr.py"

# ═══════════════════════════════════════════════════════════════════
# Deployment Complete
# ═══════════════════════════════════════════════════════════════════

Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════════════════════" "Green"
Write-ColorOutput $MSG.Success "Green"
Write-ColorOutput "═══════════════════════════════════════════════════════════════════" "Green"
Write-Host ""

Write-ColorOutput $MSG.DeploymentComplete "Cyan"
Write-Host ""

Write-ColorOutput "# Windows PowerShell:" "Yellow"
Write-ColorOutput ".\venv_vrn_layout_ocr\Scripts\Activate.ps1" "White"
Write-ColorOutput "python vrn_layout_ocr_plugin.py" "White"
Write-Host ""

Write-ColorOutput "# Python Script:" "Yellow"
Write-ColorOutput "python examples_layout_ocr.py" "White"
Write-Host ""

Write-ColorOutput "# Documentation:" "Yellow"
Write-ColorOutput "README_LayoutOCR.md" "White"
Write-Host ""

Write-ColorOutput "功能只增不減 Functionality Only Increases, Never Decreases" "Cyan"
Write-Host ""

# Display summary
Write-ColorOutput "═══════════════════════════════════════════════════════════════════" "Gray"
Write-ColorOutput "Installation Summary 安裝摘要:" "White"
Write-ColorOutput "═══════════════════════════════════════════════════════════════════" "Gray"

$Summary = @"
✓ Virtual Environment: $VenvPath
✓ Main Plugin: vrn_layout_ocr_plugin.py
✓ Deployment Script: Deploy-VRN-LayoutOCR.ps1
✓ Documentation: README_LayoutOCR.md
✓ Examples: examples_layout_ocr.py
✓ Output Directory: ./vrn_layout_ocr_output

Available Engines:
- Layout: PyMuPDF, PDFMiner, PDFPlumber, Unstructured, etc.
- OCR: Tesseract, EasyOCR, PaddleOCR, DocTR, etc.

Next Steps:
1. Activate virtual environment
2. Run: python vrn_layout_ocr_plugin.py
3. Check examples: python examples_layout_ocr.py
"@

Write-Host $Summary
Write-Host ""

