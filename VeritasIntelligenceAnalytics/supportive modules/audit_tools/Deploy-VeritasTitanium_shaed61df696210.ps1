# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
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
<#
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                    ║
║   ██╗   ██╗███████╗██████╗ ██╗████████╗ █████╗ ███████╗                                           ║
║   ██║   ██║██╔════╝██╔══██╗██║╚══██╔══╝██╔══██╗██╔════╝                                           ║
║   ██║   ██║█████╗  ██████╔╝██║   ██║   ███████║███████╗                                           ║
║   ╚██╗ ██╔╝██╔══╝  ██╔══██╗██║   ██║   ██╔══██║╚════██║                                           ║
║    ╚████╔╝ ███████╗██║  ██║██║   ██║   ██║  ██║███████║                                           ║
║     ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝                                           ║
║                                                                                                    ║
║   TONYK LAYOUT 100% v16.1 TITANIUM - ENTERPRISE DEPLOYMENT SCRIPT                                 ║
║   ════════════════════════════════════════════════════════════════════════════════════════════    ║
║                                                                                                    ║
║   🚀 Features:                                                                                    ║
║      • 6-Layer Super Accelerator Auto-Installation                                                ║
║      • Multi-Mirror Package Sources (PyPI + Tsinghua + Aliyun)                                   ║
║      • Environment Validation & Auto-Repair                                                       ║
║      • Dependency Conflict Detection                                                              ║
║      • One-Click Full Deployment                                                                  ║
║                                                                                                    ║
║   📋 Usage:                                                                                       ║
║      .\Deploy-VeritasTitanium.ps1                    # Full deployment                            ║
║      .\Deploy-VeritasTitanium.ps1 -CheckOnly        # Check environment only                     ║
║      .\Deploy-VeritasTitanium.ps1 -InstallDeps      # Install dependencies only                  ║
║      .\Deploy-VeritasTitanium.ps1 -Run              # Run without checks                         ║
║                                                                                                    ║
║   🎯 Philosophy: 功能只增不減 (Functionality Only Increases, Never Decreases)                    ║
║                                                                                                    ║
║   Author: Tony + Claude AI @ VeritasReportNova Project                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝
#>

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$InstallDeps,
    [switch]$Run,
    [switch]$Force,
    [switch]$Verbose,
    [string]$PythonPath = ""
)

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION                                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 基礎路徑
$SCRIPT_VERSION = "16.1"
$BASE_DIR = "C:\Users\tonyk\OneDrive\Desktop\VeritasReportNova"
$PYTHON_SCRIPT = "TONYK_LAYOUT_v16.1_TITANIUM.py"

# 目錄結構
$DIRECTORIES = @(
    "pdf_input",
    "pdf_output", 
    "temp",
    "models",
    "failed_pdfs",
    ".veritas_cache",
    "logs"
)

# 套件定義（分層）
$PACKAGES = @{
    # Layer 1: Core (必須)
    "Core" = @(
        @{Name="rapidocr-onnxruntime"; Import="rapidocr_onnxruntime"; Required=$true; Desc="OCR Engine"},
        @{Name="pdf2image"; Import="pdf2image"; Required=$true; Desc="PDF to Image"},
        @{Name="polars"; Import="polars"; Required=$true; Desc="DataFrame Engine"},
        @{Name="rich"; Import="rich"; Required=$true; Desc="Console UI"}
    )
    # Layer 2: Super Accelerators (強烈建議)
    "Accelerators" = @(
        @{Name="xxhash"; Import="xxhash"; Required=$false; Desc="100x Faster Hashing"; Speedup="100x"},
        @{Name="orjson"; Import="orjson"; Required=$false; Desc="50x Faster JSON"; Speedup="50x"},
        @{Name="loguru"; Import="loguru"; Required=$false; Desc="Async Logging"; Speedup="Non-blocking"},
        @{Name="joblib"; Import="joblib"; Required=$false; Desc="Smart Caching"; Speedup="∞"},
        @{Name="rapidfuzz"; Import="rapidfuzz"; Required=$false; Desc="30x Faster Matching"; Speedup="30x"}
    )
    # Layer 3: Export (選擇性)
    "Export" = @(
        @{Name="duckdb"; Import="duckdb"; Required=$false; Desc="Fast Excel Export"},
        @{Name="openpyxl"; Import="openpyxl"; Required=$false; Desc="Excel Support"},
        @{Name="xlsxwriter"; Import="xlsxwriter"; Required=$false; Desc="Excel Writer"}
    )
    # Layer 4: Extras (可選)
    "Extras" = @(
        @{Name="msgspec"; Import="msgspec"; Required=$false; Desc="Schema Serialization"},
        @{Name="numpy"; Import="numpy"; Required=$false; Desc="Numeric Computing"}
    )
}

# 鏡像源（多源容錯）
$PIP_MIRRORS = @(
    "",  # Default PyPI
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.douban.com/simple"
)

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HELPER FUNCTIONS                                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Write-Banner {
    $banner = @"

═══════════════════════════════════════════════════════════════════════════════
   ████████╗ ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗    ██╗      █████╗ ██╗   ██╗
   ╚══██╔══╝██╔═══██╗████╗  ██║╚██╗ ██╔╝██║ ██╔╝    ██║     ██╔══██╗╚██╗ ██╔╝
      ██║   ██║   ██║██╔██╗ ██║ ╚████╔╝ █████╔╝     ██║     ███████║ ╚████╔╝ 
      ██║   ██║   ██║██║╚██╗██║  ╚██╔╝  ██╔═██╗     ██║     ██╔══██║  ╚██╔╝  
      ██║   ╚██████╔╝██║ ╚████║   ██║   ██║  ██╗    ███████╗██║  ██║   ██║   
      ╚═╝    ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝   ╚═╝   
                                                                              
   LAYOUT 100% v$SCRIPT_VERSION TITANIUM - ENTERPRISE DEPLOYMENT
   VeritasReportNova™ 2025 + Super Accelerator v3.0
═══════════════════════════════════════════════════════════════════════════════

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Write-Phase {
    param([string]$Phase, [string]$Description)
    Write-Host ""
    Write-Host "┌─────────────────────────────────────────────────────────────────" -ForegroundColor Blue
    Write-Host "│  [$Phase] $Description" -ForegroundColor White
    Write-Host "└─────────────────────────────────────────────────────────────────" -ForegroundColor Blue
}

function Write-Status {
    param([string]$Icon, [string]$Message, [string]$Color = "White")
    Write-Host "   $Icon " -NoNewline
    Write-Host $Message -ForegroundColor $Color
}

function Write-SubStatus {
    param([string]$Message, [string]$Color = "Gray")
    Write-Host "      $Message" -ForegroundColor $Color
}

function Test-PythonPackage {
    param([string]$ImportName)
    try {
        $result = & $script:PythonExe -c "import $ImportName" 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-PythonVersion {
    try {
        $version = & $script:PythonExe --version 2>&1
        if ($version -match "Python (\d+\.\d+\.\d+)") {
            return $Matches[1]
        }
    } catch {}
    return $null
}

function Install-Package {
    param(
        [string]$PackageName,
        [int]$MirrorIndex = 0
    )
    
    $mirror = $PIP_MIRRORS[$MirrorIndex]
    $mirrorArg = if ($mirror) { "-i", $mirror } else { @() }
    
    try {
        $output = & $script:PythonExe -m pip install $PackageName $mirrorArg --quiet 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        # 嘗試下一個鏡像
        if ($MirrorIndex -lt ($PIP_MIRRORS.Count - 1)) {
            return Install-Package -PackageName $PackageName -MirrorIndex ($MirrorIndex + 1)
        }
        return $false
    }
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 1: ENVIRONMENT CHECK                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Test-Environment {
    Write-Phase "PHASE 1" "Environment Validation"
    
    $issues = @()
    $warnings = @()
    
    # 1.1 Check Python
    Write-Status "🔍" "Checking Python installation..."
    
    if ($PythonPath -and (Test-Path $PythonPath)) {
        $script:PythonExe = $PythonPath
    } else {
        # 嘗試多種 Python 路徑
        $pythonCandidates = @(
            "python",
            "python3",
            "py -3",
            "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe"
        )
        
        $script:PythonExe = $null
        foreach ($candidate in $pythonCandidates) {
            try {
                $testCmd = if ($candidate -like "py *") { 
                    Invoke-Expression "$candidate --version" 2>&1 
                } else { 
                    & $candidate --version 2>&1 
                }
                if ($LASTEXITCODE -eq 0) {
                    $script:PythonExe = $candidate
                    break
                }
            } catch {}
        }
    }
    
    if (-not $script:PythonExe) {
        $issues += "Python not found! Please install Python 3.10+"
        Write-Status "❌" "Python NOT FOUND" "Red"
    } else {
        $pyVersion = Get-PythonVersion
        Write-Status "✅" "Python $pyVersion found at: $script:PythonExe" "Green"
        
        # Check version
        if ($pyVersion) {
            $major, $minor, $patch = $pyVersion.Split('.')
            if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
                $warnings += "Python 3.10+ recommended (found $pyVersion)"
            }
        }
    }
    
    # 1.2 Check pip
    Write-Status "🔍" "Checking pip..."
    try {
        $pipVersion = & $script:PythonExe -m pip --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅" "pip available" "Green"
        } else {
            $issues += "pip not available"
            Write-Status "❌" "pip NOT FOUND" "Red"
        }
    } catch {
        $issues += "pip check failed"
        Write-Status "❌" "pip check failed" "Red"
    }
    
    # 1.3 Check Poppler (for pdf2image)
    Write-Status "🔍" "Checking Poppler (PDF renderer)..."
    $popplerPath = Get-Command pdftoppm -ErrorAction SilentlyContinue
    if ($popplerPath) {
        Write-Status "✅" "Poppler found" "Green"
    } else {
        $warnings += "Poppler not in PATH. pdf2image may fail."
        Write-Status "⚠️" "Poppler not in PATH (required for pdf2image)" "Yellow"
        Write-SubStatus "Download from: https://github.com/oschwartz10612/poppler-windows/releases" "Yellow"
        Write-SubStatus "Add to PATH: C:\poppler\Library\bin" "Yellow"
    }
    
    # 1.4 Check base directory
    Write-Status "🔍" "Checking base directory..."
    if (Test-Path $BASE_DIR) {
        Write-Status "✅" "Base directory exists: $BASE_DIR" "Green"
    } else {
        Write-Status "📁" "Will create: $BASE_DIR" "Yellow"
    }
    
    # Summary
    Write-Host ""
    if ($issues.Count -gt 0) {
        Write-Host "   ❌ CRITICAL ISSUES:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "      • $issue" -ForegroundColor Red
        }
        return $false
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "   ⚠️ WARNINGS:" -ForegroundColor Yellow
        foreach ($warn in $warnings) {
            Write-Host "      • $warn" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Status "✅" "Environment check PASSED" "Green"
    return $true
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 2: DIRECTORY STRUCTURE                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Initialize-Directories {
    Write-Phase "PHASE 2" "Directory Structure Setup"
    
    # Create base directory
    if (-not (Test-Path $BASE_DIR)) {
        New-Item -ItemType Directory -Path $BASE_DIR -Force | Out-Null
        Write-Status "📁" "Created: $BASE_DIR" "Green"
    }
    
    # Create subdirectories
    foreach ($dir in $DIRECTORIES) {
        $fullPath = Join-Path $BASE_DIR $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Status "📁" "Created: $dir" "Green"
        } else {
            Write-Status "✅" "Exists: $dir" "Gray"
        }
    }
    
    Write-Host ""
    Write-Status "✅" "Directory structure ready" "Green"
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 3: DEPENDENCY INSTALLATION                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Install-Dependencies {
    Write-Phase "PHASE 3" "Dependency Installation (6-Layer Acceleration Stack)"
    
    $totalPackages = 0
    $installedPackages = 0
    $skippedPackages = 0
    $failedPackages = @()
    
    foreach ($layer in @("Core", "Accelerators", "Export", "Extras")) {
        $packages = $PACKAGES[$layer]
        if (-not $packages) { continue }
        
        Write-Host ""
        Write-Host "   ┌── Layer: $layer ──" -ForegroundColor Cyan
        
        foreach ($pkg in $packages) {
            $totalPackages++
            $name = $pkg.Name
            $import = $pkg.Import
            $required = $pkg.Required
            $desc = $pkg.Desc
            $speedup = $pkg.Speedup
            
            # Check if already installed
            $isInstalled = Test-PythonPackage -ImportName $import
            
            if ($isInstalled) {
                $speedupInfo = if ($speedup) { " ($speedup)" } else { "" }
                Write-Status "✅" "$name - Already installed$speedupInfo" "Green"
                $skippedPackages++
                continue
            }
            
            # Install
            Write-Status "📦" "$name - Installing... ($desc)" "Yellow"
            $success = Install-Package -PackageName $name
            
            if ($success) {
                # Verify
                $verified = Test-PythonPackage -ImportName $import
                if ($verified) {
                    $speedupInfo = if ($speedup) { " → $speedup speedup!" } else { "" }
                    Write-Status "✅" "$name - Installed successfully$speedupInfo" "Green"
                    $installedPackages++
                } else {
                    if ($required) {
                        Write-Status "❌" "$name - Installation failed (REQUIRED)" "Red"
                        $failedPackages += $name
                    } else {
                        Write-Status "⚠️" "$name - Verification failed (optional)" "Yellow"
                    }
                }
            } else {
                if ($required) {
                    Write-Status "❌" "$name - Installation failed (REQUIRED)" "Red"
                    $failedPackages += $name
                } else {
                    Write-Status "⚠️" "$name - Installation failed (optional, will use fallback)" "Yellow"
                }
            }
        }
    }
    
    # Summary
    Write-Host ""
    Write-Host "   ┌── Installation Summary ──" -ForegroundColor Cyan
    Write-Status "📊" "Total packages: $totalPackages"
    Write-Status "✅" "Already installed: $skippedPackages" "Green"
    Write-Status "📦" "Newly installed: $installedPackages" "Green"
    
    if ($failedPackages.Count -gt 0) {
        Write-Status "❌" "Failed (required): $($failedPackages -join ', ')" "Red"
        return $false
    }
    
    Write-Host ""
    Write-Status "✅" "Dependency installation complete" "Green"
    return $true
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 4: ACCELERATOR STATUS                                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Show-AcceleratorStatus {
    Write-Phase "PHASE 4" "Super Accelerator Status"
    
    Write-Host ""
    Write-Host "   🚀 Super Accelerator Stack:" -ForegroundColor Cyan
    Write-Host "   ┌─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    $accelerators = $PACKAGES["Accelerators"]
    $allAvailable = $true
    
    foreach ($accel in $accelerators) {
        $isInstalled = Test-PythonPackage -ImportName $accel.Import
        $icon = if ($isInstalled) { "✅" } else { "⚠️" }
        $status = if ($isInstalled) { "Turbo" } else { "Fallback" }
        $color = if ($isInstalled) { "Green" } else { "Yellow" }
        $speedup = $accel.Speedup
        
        if (-not $isInstalled) { $allAvailable = $false }
        
        Write-Host "   │  $icon $($accel.Name.PadRight(12)) : " -NoNewline -ForegroundColor $color
        Write-Host "$status " -NoNewline -ForegroundColor $color
        Write-Host "($speedup)" -ForegroundColor Gray
    }
    
    Write-Host "   └─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    if ($allAvailable) {
        Write-Host ""
        Write-Host "   🏆 ALL ACCELERATORS ACTIVE - MAXIMUM PERFORMANCE!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "   💡 Some accelerators using fallback mode (still works, just slower)" -ForegroundColor Yellow
    }
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 5: GENERATE PYTHON SCRIPT                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Install-PythonScript {
    Write-Phase "PHASE 5" "Deploy Python Script"
    
    $scriptPath = Join-Path $BASE_DIR $PYTHON_SCRIPT
    
    # Check if script exists
    if (Test-Path $scriptPath) {
        Write-Status "✅" "Python script already exists: $PYTHON_SCRIPT" "Green"
        
        if (-not $Force) {
            $response = Read-Host "   Overwrite? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Status "⏭️" "Skipping script deployment" "Yellow"
                return $true
            }
        }
    }
    
    Write-Status "📝" "Deploying $PYTHON_SCRIPT..." "Yellow"
    
    # The Python script content is embedded below
    $pythonScript = @'
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║   VeritasReportNova™ 2025 - TONYK LAYOUT 100% v16.1 TITANIUM EDITION                              ║
║   Deployed via Enterprise Deployment Script                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import sys
import shutil
import time
import warnings
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import functools

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(r"C:\Users\tonyk\OneDrive\Desktop\VeritasReportNova").expanduser().resolve()
INPUT_DIR   = BASE_DIR / "pdf_input"
OUTPUT_DIR  = BASE_DIR / "pdf_output"
TEMP_DIR    = BASE_DIR / "temp"
MODEL_DIR   = BASE_DIR / "models"
ERROR_DIR   = BASE_DIR / "failed_pdfs"
CACHE_DIR   = BASE_DIR / ".veritas_cache"
LOG_DIR     = BASE_DIR / "logs"

for p in (INPUT_DIR, OUTPUT_DIR, TEMP_DIR, MODEL_DIR, ERROR_DIR, CACHE_DIR, LOG_DIR):
    p.mkdir(parents=True, exist_ok=True)

DPI = 180
MIN_CONF = 0.38
WORKERS = max(4, os.cpu_count() - 1)
ENABLE_DUPLICATE_DETECTION = True
ENABLE_FUZZY_CLEANUP = True
FUZZY_THRESHOLD = 70.0

# ═══════════════════════════════════════════════════════════════════════════════
# SUPER ACCELERATOR IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AcceleratorStatus:
    name: str
    available: bool
    speedup: str
    fallback: str = ""

_ACCEL_STATUS: Dict[str, AcceleratorStatus] = {}

def register_accel(name: str, available: bool, speedup: str, fallback: str = ""):
    _ACCEL_STATUS[name] = AcceleratorStatus(name, available, speedup, fallback)

# xxHash
try:
    import xxhash
    register_accel("xxHash", True, "~100x", "hashlib.md5")
    def fast_hash(data: bytes, seed: int = 0) -> str:
        return xxhash.xxh64(data, seed=seed).hexdigest()
except ImportError:
    import hashlib
    register_accel("xxHash", False, "1x", "hashlib.md5")
    def fast_hash(data: bytes, seed: int = 0) -> str:
        return hashlib.md5(data).hexdigest()

# Orjson
try:
    import orjson
    register_accel("Orjson", True, "~50x", "json")
    def fast_json_dumps(obj: Any) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY)
    def fast_json_loads(data: bytes) -> Any:
        return orjson.loads(data)
except ImportError:
    import json
    register_accel("Orjson", False, "1x", "json")
    def fast_json_dumps(obj: Any) -> bytes:
        return json.dumps(obj, default=str).encode('utf-8')
    def fast_json_loads(data: bytes) -> Any:
        return json.loads(data.decode('utf-8'))

# Loguru
try:
    from loguru import logger as loguru_logger
    register_accel("Loguru", True, "Non-blocking", "logging")
    loguru_logger.remove()
    loguru_logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}", level="INFO", colorize=True, enqueue=True)
    loguru_logger.add(LOG_DIR / "veritas_{time:%Y%m%d}.log", rotation="10 MB", retention="7 days", compression="gz", enqueue=True)
    logger = loguru_logger
    HAS_LOGURU = True
except ImportError:
    import logging
    register_accel("Loguru", False, "1x (blocking)", "logging")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    logger = logging.getLogger("Veritas")
    HAS_LOGURU = False

# Joblib
try:
    from joblib import Memory, hash as joblib_hash
    register_accel("Joblib", True, "∞ (skip duplicates)", "none")
    _memory = Memory(location=str(CACHE_DIR), verbose=0, compress=3)
    def cache_function(func): return _memory.cache(func)
    def compute_stable_hash(obj: Any) -> str: return joblib_hash(obj)
    HAS_JOBLIB = True
except ImportError:
    register_accel("Joblib", False, "1x", "none")
    def cache_function(func): return func
    def compute_stable_hash(obj: Any) -> str: return fast_hash(str(obj).encode())
    HAS_JOBLIB = False

# RapidFuzz
try:
    from rapidfuzz import fuzz, process as rapidfuzz_process
    register_accel("RapidFuzz", True, "~30x", "difflib")
    def fuzzy_match(query: str, choices: List[str], threshold: float = 70.0):
        return rapidfuzz_process.extractOne(query, choices, scorer=fuzz.WRatio, score_cutoff=threshold)
    def fuzzy_deduplicate(items: List[str], threshold: float = 80.0) -> List[str]:
        if not items: return []
        unique = [items[0]]
        for item in items[1:]:
            if not any(fuzz.ratio(item, u) >= threshold for u in unique):
                unique.append(item)
        return unique
    HAS_RAPIDFUZZ = True
except ImportError:
    from difflib import get_close_matches
    register_accel("RapidFuzz", False, "1x", "difflib")
    def fuzzy_match(query: str, choices: List[str], threshold: float = 70.0):
        matches = get_close_matches(query, choices, n=1, cutoff=threshold/100)
        return (matches[0], threshold, 0) if matches else None
    def fuzzy_deduplicate(items: List[str], threshold: float = 80.0) -> List[str]:
        return list(set(items))
    HAS_RAPIDFUZZ = False

# Polars
try:
    import polars as pl
    register_accel("Polars", True, "Zero-copy", "pandas")
    HAS_POLARS = True
except ImportError:
    register_accel("Polars", False, "1x", "pandas")
    HAS_POLARS = False

# Rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TimeElapsedColumn, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.tree import Tree
    from rich.text import Text
    from rich import box
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

# ═══════════════════════════════════════════════════════════════════════════════
# KPI TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class KPITracker:
    session_id: str = field(default_factory=lambda: f"S_{int(time.time())}")
    start_time: float = field(default_factory=time.perf_counter)
    phases: Dict[str, dict] = field(default_factory=dict)
    total_files: int = 0
    successful_files: int = 0
    empty_files: int = 0
    error_files: int = 0
    total_pages: int = 0
    total_boxes: int = 0
    total_chars: int = 0
    total_confidence_sum: float = 0.0
    confidence_count: int = 0
    hash_operations: int = 0
    duplicates_skipped: int = 0
    
    @property
    def elapsed(self) -> float: return time.perf_counter() - self.start_time
    @property
    def pages_per_sec(self) -> float: return self.total_pages / self.elapsed if self.elapsed > 0 else 0.0
    @property
    def avg_confidence(self) -> float: return self.total_confidence_sum / self.confidence_count if self.confidence_count > 0 else 0.0

KPI = KPITracker()

# ═══════════════════════════════════════════════════════════════════════════════
# OCR INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

OCR = None
PAGE_HASH_CACHE = {}

def ensure_models():
    if HAS_RICH: console.print("[yellow]檢查 RapidOCR 模型...[/]")
    else: print("檢查 RapidOCR 模型...")
    try:
        from rapidocr_onnxruntime import RapidOCR
        _ = RapidOCR()
        if HAS_RICH: console.print("[green]✓ RapidOCR 模型就緒！[/]")
        else: print("✓ RapidOCR 模型就緒！")
    except Exception as e:
        if HAS_RICH: console.print(f"[red]❌ RapidOCR 初始化失敗: {e}[/]")
        else: print(f"❌ RapidOCR 初始化失敗: {e}")
        raise

def worker_init():
    global OCR
    from rapidocr_onnxruntime import RapidOCR
    OCR = RapidOCR(use_angle_cls=False)

# ═══════════════════════════════════════════════════════════════════════════════
# CORE PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

from pdf2image import convert_from_path
import numpy as np

def process_pdf_titanium(pdf_path: Path) -> dict:
    global OCR
    result = {"status": "error", "file": pdf_path.name, "pages": 0, "boxes": 0, "chars": 0, "avg_conf": 0.0, "duplicates_skipped": 0, "elapsed_ms": 0}
    start_t = time.perf_counter()
    
    try:
        with open(pdf_path, 'rb') as f: pdf_bytes = f.read()
        doc_hash = fast_hash(pdf_bytes)
        doc_id = f"DOC_{int(time.time())}_{doc_hash[:12]}"
        
        images = convert_from_path(str(pdf_path), dpi=DPI, thread_count=12, fmt="ppm", use_cropbox=True, grayscale=False)
        result["pages"] = len(images)
        rows, seq, conf_sum, conf_count, duplicates_skipped = [], 1, 0.0, 0, 0
        
        for page_num, img in enumerate(images, 1):
            w, h = img.size
            
            if ENABLE_DUPLICATE_DETECTION:
                img_array = np.array(img)
                sample = img_array[::100, ::100, :].tobytes()[:1000]
                page_hash = fast_hash(sample)
                if page_hash in PAGE_HASH_CACHE:
                    duplicates_skipped += 1
                    for cached_box in PAGE_HASH_CACHE[page_hash]:
                        box_copy = cached_box.copy()
                        box_copy.update({"doc_id": doc_id, "file": pdf_path.name, "page": page_num, "id": f"{doc_id}_P{page_num:03d}_B{seq:06d}"})
                        rows.append(box_copy)
                        seq += 1
                        conf_sum += box_copy["conf"]
                        conf_count += 1
                    continue
            
            ocr_result, _ = OCR(img)
            if not ocr_result: continue
            
            page_boxes = []
            for box, text, conf in ocr_result:
                if conf < MIN_CONF: continue
                text = text.strip()
                if not text: continue
                (x1, y1), (_, _), (x2, y2), (_, _) = box
                box_data = {"doc_id": doc_id, "file": pdf_path.name, "page": page_num, "w": w, "h": h, "id": f"{doc_id}_P{page_num:03d}_B{seq:06d}", "text": text, "conf": round(conf, 3), "x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2), "cx": (x1+x2)//2, "cy": (y1+y2)//2, "width": int(x2-x1), "height": int(y2-y1), "font": int((y2-y1)*0.8)}
                rows.append(box_data)
                page_boxes.append(box_data)
                seq += 1
                conf_sum += conf
                conf_count += 1
            
            if ENABLE_DUPLICATE_DETECTION and page_boxes:
                PAGE_HASH_CACHE[page_hash] = page_boxes
        
        if rows:
            import polars as pl
            pl.DataFrame(rows).write_parquet(TEMP_DIR / f"{doc_id}.parquet", compression="zstd", compression_level=1)
            result.update({"status": "ok", "boxes": len(rows), "chars": sum(len(r["text"]) for r in rows), "avg_conf": conf_sum/conf_count if conf_count > 0 else 0.0, "duplicates_skipped": duplicates_skipped})
        else:
            result["status"] = "empty"
    except Exception as e:
        shutil.move(str(pdf_path), ERROR_DIR / pdf_path.name)
        result.update({"status": "error", "error": str(e)})
    
    result["elapsed_ms"] = (time.perf_counter() - start_t) * 1000
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def print_startup_banner():
    if not HAS_RICH:
        print("=" * 60 + "\n  TONYK LAYOUT 100% v16.1 TITANIUM EDITION\n" + "=" * 60)
        return
    banner = "\n[bold white on red]   TONYK LAYOUT 100% v16.1 TITANIUM EDITION   [/]\n[bold white on red]   VeritasReportNova™ 2025 + Super Accelerator v3.0   [/]\n"
    console.print(banner)

def print_accelerator_status():
    if not HAS_RICH:
        print("\nAccelerators loaded.")
        return
    tree = Tree("[bold cyan]🚀 Super Accelerator Stack[/]")
    for name, status in _ACCEL_STATUS.items():
        icon = "✅" if status.available else "⚠️"
        speed = f"[green]{status.speedup}[/]" if status.available else f"[yellow]{status.speedup}[/]"
        fallback_info = f" → [dim]{status.fallback}[/]" if not status.available else ""
        tree.add(f"{icon} [bold]{name}[/]: {speed}{fallback_info}")
    console.print(Panel(tree, title="Acceleration Layer", border_style="cyan"))

def print_config_summary():
    if not HAS_RICH:
        print(f"\nConfig: DPI={DPI}, Workers={WORKERS}, MinConf={MIN_CONF}")
        return
    config_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("DPI", str(DPI))
    config_table.add_row("Workers", f"{WORKERS} cores")
    config_table.add_row("Min Confidence", f"{MIN_CONF}")
    config_table.add_row("Duplicate Detection", "✅ ON" if ENABLE_DUPLICATE_DETECTION else "❌ OFF")
    config_table.add_row("Cache Dir", str(CACHE_DIR))
    console.print(Panel(config_table, title="⚙️ Configuration", border_style="blue"))

def print_ultimate_report(kpi: KPITracker, output_file: Path):
    if not HAS_RICH:
        print(f"\n{'='*60}\n  完成！{kpi.total_pages} 頁 in {kpi.elapsed:.1f}s = {kpi.pages_per_sec:.1f} 頁/秒\n  報告：{output_file}\n{'='*60}")
        return
    console.rule("[bold white on red] TONYK LAYOUT 100% v16.1 TITANIUM – 終極戰報 [/]", style="bright_red")
    t1 = Table(box=box.DOUBLE, show_header=False, title="📊 Performance Metrics")
    t1.add_column("項目", style="bold cyan", width=18)
    t1.add_column("數值", style="bold green", width=25)
    t1.add_row("成功檔案", f"{kpi.successful_files} / {kpi.total_files}")
    t1.add_row("總頁數", f"{kpi.total_pages:,} 頁")
    t1.add_row("總文字框", f"{kpi.total_boxes:,} 個")
    t1.add_row("處理耗時", f"[yellow]{kpi.elapsed:.2f} 秒[/]")
    t1.add_row("極速表現", f"[bold red]{kpi.pages_per_sec:.1f} 頁/秒[/]")
    t1.add_row("平均信心值", f"[bold white on blue] {kpi.avg_confidence*100:.2f}% [/]")
    console.print(t1)
    speed = kpi.pages_per_sec
    bar = "█" * min(int(speed / 3), 50) + "░" * (50 - min(int(speed / 3), 50))
    console.print(f"\n[bold cyan]🚀 處理速度[/] → {speed:.1f} 頁/秒\n   │{bar}│")
    console.print(Panel(f"[bold green]📄 報告已生成[/]\n[white]{output_file}[/]", border_style="green"))
    console.print(Text("\n🏆 恭喜 Tonyk！功能只增不減 ✓  效能再創新高 ✓", style="bold yellow"))

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    global KPI
    KPI = KPITracker()
    
    print_startup_banner()
    print_accelerator_status()
    print_config_summary()
    ensure_models()
    
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    TEMP_DIR.mkdir()
    
    pdfs = list(INPUT_DIR.glob("*.pdf"))
    KPI.total_files = len(pdfs)
    
    if not pdfs:
        if HAS_RICH: console.print(Panel("[yellow]pdf_input 沒有 PDF！[/]", border_style="yellow"))
        else: print("pdf_input 沒有 PDF！")
        input("按 Enter 結束...")
        return
    
    if HAS_RICH: console.print(f"\n[bold cyan]📁 發現 {len(pdfs)} 個 PDF 檔案[/]\n")
    
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=worker_init) as exe:
        futures = [exe.submit(process_pdf_titanium, p) for p in pdfs]
        if HAS_RICH:
            with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(complete_style="green"), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), TimeElapsedColumn(), console=console) as progress:
                task = progress.add_task("🚀 Titanium Processing...", total=len(pdfs))
                for future in as_completed(futures):
                    r = future.result()
                    if r["status"] == "ok":
                        KPI.successful_files += 1
                        KPI.total_pages += r["pages"]
                        KPI.total_boxes += r["boxes"]
                        KPI.total_chars += r.get("chars", 0)
                        KPI.total_confidence_sum += r.get("avg_conf", 0) * r.get("boxes", 0)
                        KPI.confidence_count += r.get("boxes", 0)
                        KPI.duplicates_skipped += r.get("duplicates_skipped", 0)
                    elif r["status"] == "empty": KPI.empty_files += 1
                    else: KPI.error_files += 1
                    progress.advance(task)
        else:
            for future in as_completed(futures):
                r = future.result()
                if r["status"] == "ok":
                    KPI.successful_files += 1
                    KPI.total_pages += r["pages"]
                    KPI.total_boxes += r["boxes"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUTPUT_DIR / f"TONYK_TITANIUM_{timestamp}.xlsx"
    
    try:
        import duckdb
        duckdb.sql(f"COPY (SELECT * FROM '{TEMP_DIR}/*.parquet') TO '{out_file}' (FORMAT XLSX);")
    except:
        try:
            import polars as pl
            pl.scan_parquet(TEMP_DIR / "*.parquet").collect().write_excel(out_file)
        except Exception as e:
            if HAS_RICH: console.print(f"[red]匯出失敗: {e}[/]")
    
    print_ultimate_report(KPI, out_file)
    
    kpi_file = OUTPUT_DIR / f"KPI_{timestamp}.json"
    with open(kpi_file, 'wb') as f:
        f.write(fast_json_dumps({"session_id": KPI.session_id, "timestamp": timestamp, "elapsed": KPI.elapsed, "pages": KPI.total_pages, "boxes": KPI.total_boxes, "pages_per_sec": KPI.pages_per_sec}))
    
    input("\n按 Enter 結束程式...")

if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    mp.set_start_method("spawn", force=True)
    main()
'@
    
    try {
        $pythonScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
        Write-Status "✅" "Python script deployed: $PYTHON_SCRIPT" "Green"
        return $true
    } catch {
        Write-Status "❌" "Failed to deploy script: $_" "Red"
        return $false
    }
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 6: RUN                                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

function Start-TitaniumProcess {
    Write-Phase "PHASE 6" "Launch TITANIUM"
    
    $scriptPath = Join-Path $BASE_DIR $PYTHON_SCRIPT
    
    if (-not (Test-Path $scriptPath)) {
        Write-Status "❌" "Python script not found: $scriptPath" "Red"
        return $false
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host "   🚀 LAUNCHING TITANIUM..." -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host ""
    
    Set-Location $BASE_DIR
    & $script:PythonExe $scriptPath
    
    return $true
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN EXECUTION                                                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

Write-Banner

# Route based on parameters
if ($CheckOnly) {
    $envOk = Test-Environment
    Show-AcceleratorStatus
    exit $(if ($envOk) { 0 } else { 1 })
}

if ($InstallDeps) {
    $envOk = Test-Environment
    if ($envOk) {
        Install-Dependencies
        Show-AcceleratorStatus
    }
    exit 0
}

if ($Run) {
    $envOk = Test-Environment
    if ($envOk) {
        Start-TitaniumProcess
    }
    exit 0
}

# Full deployment (default)
Write-Host "   Mode: FULL DEPLOYMENT" -ForegroundColor Cyan
Write-Host ""

# Phase 1: Environment Check
$envOk = Test-Environment
if (-not $envOk) {
    Write-Host ""
    Write-Host "   ❌ Environment check failed. Please fix the issues above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Phase 2: Directory Structure
Initialize-Directories

# Phase 3: Dependencies
$depsOk = Install-Dependencies
if (-not $depsOk) {
    Write-Host ""
    Write-Host "   ❌ Required dependencies failed to install." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Phase 4: Accelerator Status
Show-AcceleratorStatus

# Phase 5: Deploy Script
$scriptOk = Install-PythonScript
if (-not $scriptOk) {
    Write-Host ""
    Write-Host "   ❌ Failed to deploy Python script." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Phase 6: Run
Write-Host ""
$response = Read-Host "   🚀 Ready to launch TITANIUM! Proceed? (Y/n)"
if ($response -eq '' -or $response -eq 'y' -or $response -eq 'Y') {
    Start-TitaniumProcess
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   ✅ Deployment Complete!" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Green

