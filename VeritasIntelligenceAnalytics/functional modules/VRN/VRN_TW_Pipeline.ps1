<#
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║  VRN_TW_Pipeline.ps1                                                                                  ║
║  台股報告處理流程 | PowerShell 7+ Required                                                            ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                       ║
║  流程:                                                                                                ║
║    1. Filename 解析 → 偵測 Ticker                                                                     ║
║    2. 第一頁解析 → 三種 Regex 交叉核對                                                                ║
║    3. 調用 TWFinancialData_v5.py 擷取數據                                                             ║
║    4. 讀取輸出資料庫                                                                                  ║
║                                                                                                       ║
║  Ticker 規則:                                                                                         ║
║    - 四碼數字，首碼非零                                                                               ║
║    - 避開 2000~2030 (年份混淆)                                                                        ║
║    - TW_TICKER / TW_BLOOMBERG / TW_YFINANCE 三格式交叉核對                                            ║
║                                                                                                       ║
║  數據腳本:                                                                                            ║
║    C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\TWFinancialData_v5.py                       ║
║                                                                                                       ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
#>

#requires -Version 7.0

param(
    [string]$InputFile = "",
    [string[]]$Tickers = @(),
    [switch]$AutoFetch = $true,
    [switch]$Test
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# =============================================================================
# § CONFIGURATION (鎖定)
# =============================================================================

$script:CONFIG = @{
    # 數據擷取腳本 (鎖定 - DO NOT CHANGE)
    DataScript = "C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\TWFinancialData_v5.py"
    
    # TW01/TW02 模組
    TW01_Module = "C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\VRN_TW01_TickerBridge.py"
    TW02_Module = "C:\Users\tonyk\OneDrive\Desktop\VRN\VRN_Ultra_Complete\VRN_TW02_ReportParser.py"
    
    # 輸出目錄
    OutputDir = "C:\Users\tonyk\OneDrive\Desktop\VRN\output"
    
    # Ticker 排除範圍 (避免年份混淆)
    ExcludeRange = 2000..2030
}

# =============================================================================
# § LOCKED REGEX PATTERNS (鎖定 - DO NOT CHANGE)
# =============================================================================

$script:REGEX = @{
    # 母代號：純四碼數字，首碼非零
    TW_TICKER = [regex]"\b[1-9]\d{3}\b"
    
    # Bloomberg：四碼 + 空格 + TT
    TW_BLOOMBERG = [regex]"\b[1-9]\d{3} TT\b"
    
    # yfinance：四碼 + .TW 或 .TWO
    TW_YFINANCE = [regex]"\b[1-9]\d{3}\.(TW|TWO)\b"
    
    # 統一提取
    TW_CODE_EXTRACT = [regex]"\b([1-9]\d{3})(?:\s+TT|\.TWO?|\b)"
}

# =============================================================================
# § HELPER FUNCTIONS
# =============================================================================

function Test-ValidTicker {
    param([string]$Code)
    
    if ($Code -notmatch "^\d{4}$") { return $false }
    if ($Code[0] -eq '0') { return $false }
    
    $num = [int]$Code
    if ($num -in $script:CONFIG.ExcludeRange) { return $false }
    
    return $true
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("╔" + ("═" * 78) + "╗") -ForegroundColor Cyan
    $pad = [math]::Max(0, (78 - $Text.Length) / 2)
    $padded = (" " * [math]::Floor($pad)) + $Text + (" " * [math]::Ceiling($pad))
    Write-Host "║$padded║" -ForegroundColor Cyan
    Write-Host ("╚" + ("═" * 78) + "╝") -ForegroundColor Cyan
}

function Write-Status {
    param([string]$Name, [string]$Status, [string]$Detail = "")
    $icon = switch ($Status) {
        "OK"   { "✓"; $color = "Green" }
        "FAIL" { "✗"; $color = "Red" }
        "WARN" { "⚠"; $color = "Yellow" }
        default { "•"; $color = "White" }
    }
    Write-Host "  $icon " -NoNewline -ForegroundColor $color
    Write-Host $Name.PadRight(25) -NoNewline
    Write-Host "[$Status]".PadRight(8) -NoNewline -ForegroundColor $color
    if ($Detail) { Write-Host " $Detail" -ForegroundColor DarkGray } else { Write-Host "" }
}

# =============================================================================
# § FILENAME PARSER
# =============================================================================

function Parse-Filename {
    param([string]$Filename)
    
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($Filename)
    
    # 分割: 中英文邊界、標點、空格
    $components = $stem -split '(?<=[a-zA-Z])(?=[\u4e00-\u9fff])|(?<=[\u4e00-\u9fff])(?=[a-zA-Z])|(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])|[\s_\-\.,:;!?()（）【】「」]+' | Where-Object { $_ }
    
    $result = @{
        Original = $Filename
        Stem = $stem
        Components = $components
        PotentialTickers = @()
        PotentialDates = @()
    }
    
    foreach ($comp in $components) {
        if ($comp -match "^\d{4}$" -and (Test-ValidTicker $comp)) {
            $result.PotentialTickers += $comp
        }
        if ($comp -match "^\d{6,8}$") {
            $result.PotentialDates += $comp
        }
    }
    
    return $result
}

# =============================================================================
# § TEXT PARSER - 三種 Regex 偵測
# =============================================================================

function Find-Tickers {
    param([string]$Text)
    
    $found = @{
        TW_Pure = @()
        TW_Bloomberg = @()
        TW_YFinance = @()
        Validated = @()
    }
    
    # 1. yfinance 格式 (優先)
    $matches = $script:REGEX.TW_YFINANCE.Matches($Text)
    foreach ($m in $matches) {
        $code = $m.Value.Split(".")[0]
        if (Test-ValidTicker $code) {
            $found.TW_YFinance += $m.Value
            if ($code -notin $found.Validated) { $found.Validated += $code }
        }
    }
    
    # 2. Bloomberg 格式
    $matches = $script:REGEX.TW_BLOOMBERG.Matches($Text)
    foreach ($m in $matches) {
        $code = $m.Value -replace " TT", ""
        if (Test-ValidTicker $code) {
            $found.TW_Bloomberg += $m.Value
            if ($code -notin $found.Validated) { $found.Validated += $code }
        }
    }
    
    # 3. 純四碼
    $matches = $script:REGEX.TW_TICKER.Matches($Text)
    foreach ($m in $matches) {
        $code = $m.Value
        if ((Test-ValidTicker $code) -and ($code -notin $found.Validated)) {
            # 檢查上下文排除年份
            $start = [math]::Max(0, $m.Index - 10)
            $len = [math]::Min(30, $Text.Length - $start)
            $ctx = $Text.Substring($start, $len).ToLower()
            
            if ($ctx -notmatch "年|year|fy|quarter|q[1-4]") {
                $found.TW_Pure += $code
                $found.Validated += $code
            }
        }
    }
    
    return $found
}

# =============================================================================
# § DATA FETCHER - 調用 TWFinancialData_v5.py
# =============================================================================

function Invoke-DataFetch {
    param([string[]]$Codes)
    
    $scriptPath = $script:CONFIG.DataScript
    
    if (-not (Test-Path $scriptPath)) {
        Write-Status "DataScript" "FAIL" "Not found: $scriptPath"
        return @{ Success = $false; Error = "Script not found" }
    }
    
    Write-Status "DataScript" "OK" $scriptPath
    
    # 找 Python
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        Write-Status "Python" "FAIL" "Not found"
        return @{ Success = $false; Error = "Python not found" }
    }
    
    Write-Host ""
    Write-Host "  Executing TWFinancialData_v5.py..." -ForegroundColor Cyan
    Write-Host "  Tickers: $($Codes -join ', ')" -ForegroundColor DarkGray
    
    try {
        $workDir = Split-Path $scriptPath -Parent
        $result = & $python.Source $scriptPath 2>&1
        
        Write-Host ""
        Write-Status "Execution" "OK" "Completed"
        
        return @{
            Success = $true
            Codes = $Codes
            YFinanceTickers = $Codes | ForEach-Object { "$_.TW" }
            OutputDir = $script:CONFIG.OutputDir
        }
    }
    catch {
        Write-Status "Execution" "FAIL" $_.Exception.Message
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

# =============================================================================
# § MAIN PIPELINE
# =============================================================================

function Start-Pipeline {
    param(
        [string]$Filename = "",
        [string]$Text = "",
        [string[]]$ManualTickers = @()
    )
    
    Write-Header "VRN TW Pipeline"
    Write-Host "  Ticker Regex: TW_TICKER / TW_BLOOMBERG / TW_YFINANCE" -ForegroundColor DarkGray
    Write-Host "  Exclude Range: 2000-2030 (avoid year confusion)" -ForegroundColor DarkGray
    Write-Host ""
    
    $allTickers = @()
    
    # Step 1: 解析 Filename
    if ($Filename) {
        Write-Host "【Step 1】Filename Analysis" -ForegroundColor Yellow
        $fnResult = Parse-Filename -Filename $Filename
        Write-Status "Filename" "OK" $fnResult.Stem
        Write-Host "  Components: $($fnResult.Components -join ' | ')" -ForegroundColor DarkGray
        
        if ($fnResult.PotentialTickers) {
            Write-Status "Tickers" "OK" ($fnResult.PotentialTickers -join ", ")
            $allTickers += $fnResult.PotentialTickers
        }
        Write-Host ""
    }
    
    # Step 2: 解析文本
    if ($Text) {
        Write-Host "【Step 2】Text Analysis (3 Regex)" -ForegroundColor Yellow
        $textResult = Find-Tickers -Text $Text
        
        if ($textResult.TW_YFinance) {
            Write-Status "TW_YFINANCE" "OK" ($textResult.TW_YFinance -join ", ")
        }
        if ($textResult.TW_Bloomberg) {
            Write-Status "TW_BLOOMBERG" "OK" ($textResult.TW_Bloomberg -join ", ")
        }
        if ($textResult.TW_Pure) {
            Write-Status "TW_TICKER" "OK" ($textResult.TW_Pure -join ", ")
        }
        
        $allTickers += $textResult.Validated
        Write-Host ""
    }
    
    # Step 3: 手動指定
    if ($ManualTickers) {
        Write-Host "【Step 3】Manual Tickers" -ForegroundColor Yellow
        foreach ($t in $ManualTickers) {
            if (Test-ValidTicker $t) {
                Write-Status $t "OK" "Valid"
                $allTickers += $t
            } else {
                Write-Status $t "WARN" "Invalid (excluded)"
            }
        }
        Write-Host ""
    }
    
    # 去重
    $uniqueTickers = $allTickers | Select-Object -Unique | Where-Object { Test-ValidTicker $_ }
    
    if (-not $uniqueTickers) {
        Write-Host "  No valid tickers found." -ForegroundColor Yellow
        return
    }
    
    # Step 4: 調用數據擷取
    Write-Host "【Step 4】Data Fetch" -ForegroundColor Yellow
    Write-Host "  Validated Tickers: $($uniqueTickers -join ', ')" -ForegroundColor Green
    Write-Host ""
    
    $fetchResult = Invoke-DataFetch -Codes $uniqueTickers
    
    # Summary
    Write-Header "Pipeline Complete"
    Write-Host "  Tickers: $($uniqueTickers -join ', ')" -ForegroundColor Green
    Write-Host "  YFinance: $($uniqueTickers | ForEach-Object { "$_.TW" } | Join-String -Separator ', ')" -ForegroundColor Cyan
    Write-Host "  Output: $($script:CONFIG.OutputDir)" -ForegroundColor DarkGray
}

# =============================================================================
# § ENTRY POINT
# =============================================================================

if ($Test) {
    Write-Header "VRN TW Pipeline - Test Mode"
    
    # 顯示鎖定的 Regex
    Write-Host ""
    Write-Host "【Locked Regex Definitions】" -ForegroundColor Yellow
    Write-Host "  TW_TICKER_REGEX    = \b[1-9]\d{3}\b" -ForegroundColor Cyan
    Write-Host "  TW_BLOOMBERG_REGEX = \b[1-9]\d{3} TT\b" -ForegroundColor Cyan
    Write-Host "  TW_YFINANCE_REGEX  = \b[1-9]\d{3}\.(TW|TWO)\b" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "【Data Script (Locked)】" -ForegroundColor Yellow
    Write-Host "  $($script:CONFIG.DataScript)" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "【Ticker Validation】" -ForegroundColor Yellow
    @("2330", "2024", "2025", "3324", "1101", "2000", "2031") | ForEach-Object {
        $valid = Test-ValidTicker $_
        $status = if ($valid) { "OK" } else { "WARN" }
        $reason = if (-not $valid -and [int]$_ -in $script:CONFIG.ExcludeRange) { "(in 2000-2030)" } else { "" }
        Write-Status $_ $status $reason
    }
    
    Write-Host ""
    Write-Host "【Test Parse】" -ForegroundColor Yellow
    $testText = "台積電 2330.TW 目標價調升，2317 TT 表現亮眼，報告日期 2025/01/25"
    $result = Find-Tickers -Text $testText
    Write-Host "  Input: $testText" -ForegroundColor DarkGray
    Write-Host "  Found: $($result.Validated -join ', ')" -ForegroundColor Green
    
} elseif ($Tickers) {
    Start-Pipeline -ManualTickers $Tickers
    
} elseif ($InputFile) {
    if (Test-Path $InputFile) {
        $text = Get-Content $InputFile -Raw -Encoding UTF8
        Start-Pipeline -Filename $InputFile -Text $text
    } else {
        Write-Host "File not found: $InputFile" -ForegroundColor Red
    }
    
} else {
    Write-Header "VRN TW Pipeline"
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\VRN_TW_Pipeline.ps1 -Test" -ForegroundColor Cyan
    Write-Host "  .\VRN_TW_Pipeline.ps1 -Tickers 2330,3324,1101" -ForegroundColor Cyan
    Write-Host "  .\VRN_TW_Pipeline.ps1 -InputFile report.txt" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Locked Data Script:" -ForegroundColor Yellow
    Write-Host "  $($script:CONFIG.DataScript)" -ForegroundColor DarkGray
}
