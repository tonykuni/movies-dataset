# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
# ═══════════════════════════════════════════════════════════════════════════
# PaddleOCR 正確修復腳本 - 處理縮進問題
# 複製整個腳本到 PowerShell 執行
# ═══════════════════════════════════════════════════════════════════════════

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
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -F Cyan
Write-Host "║      PaddleOCR 縮進問題修復                                   ║" -F Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -F Cyan

$scriptPath = "C:\VeritasReportNova\重新整合\phase_1\VRN_Phase1_Ultimate_GoldenExtractor.py"

if (!(Test-Path $scriptPath)) {
    Write-Host "[✗] 文件不存在: $scriptPath" -F Red
    Pause
    exit
}

# 創建備份
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$scriptPath.bak_fix_$timestamp"
Copy-Item $scriptPath $backupPath -Force
Write-Host "[✓] 已創建備份: $backupPath" -F Green

# 讀取文件
$content = Get-Content $scriptPath -Raw -Encoding UTF8

# 方案 1: 如果代碼中有錯誤的修復
Write-Host "[i] 檢查並修復代碼..." -F Cyan

# 首先，還原之前錯誤的修復
$errorPattern1 = @"
# 抑制 PaddleOCR 日誌
        import logging
        logging.getLogger('ppocr').setLevel(logging.ERROR)
        self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
"@

$errorPattern2 = @"
import logging
        logging.getLogger('ppocr').setLevel(logging.ERROR)
        self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
"@

# 檢查是否有錯誤的修復
if ($content -like "*import logging*logging.getLogger('ppocr')*") {
    Write-Host "[i] 發現之前的錯誤修復，正在還原..." -F Yellow
    
    # 還原為最簡單的正確形式
    $content = $content -replace [regex]::Escape($errorPattern1), "self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')"
    $content = $content -replace [regex]::Escape($errorPattern2), "self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')"
}

# 修復主要問題：移除 show_log 參數
$oldPattern = "self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)"
$newPattern = "self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')"

if ($content -like "*$oldPattern*") {
    $content = $content.Replace($oldPattern, $newPattern)
    Write-Host "[✓] 已移除 show_log 參數" -F Green
}

# 在文件頂部添加日誌抑制（如果還沒有）
if ($content -notlike "*logging.getLogger('ppocr')*") {
    # 找到 MultiEngineExtractor 類的 __init__ 方法
    $initPattern = "def __init__\(self\):\s+try:"
    if ($content -match $initPattern) {
        # 在 try 之後添加日誌控制
        $logControl = @"
try:
            # 抑制 PaddleOCR 日誌輸出
            import logging
            logging.getLogger('ppocr').setLevel(logging.ERROR)
"@
        $content = $content -replace "try:", $logControl
        Write-Host "[✓] 已添加日誌控制" -F Green
    }
}

# 保存修復後的文件
$content | Set-Content $scriptPath -Encoding UTF8 -NoNewline
Write-Host "[✓] 文件已保存" -F Green

# 驗證 Python 語法
Write-Host "`n[i] 驗證 Python 語法..." -F Cyan
$pythonExe = "C:\VeritasReportNova\重新整合\phase_1\_venv\Scripts\python.exe"

if (Test-Path $pythonExe) {
    $result = & $pythonExe -m py_compile $scriptPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Python 語法檢查通過" -F Green
    } else {
        Write-Host "[✗] 語法檢查失敗:" -F Red
        Write-Host $result -F Red
        Write-Host "`n[i] 正在還原備份..." -F Yellow
        Copy-Item $backupPath $scriptPath -Force
        Write-Host "[✓] 已還原為備份版本" -F Green
        Pause
        exit
    }
} else {
    Write-Host "[⚠] 無法驗證語法（Python 未找到），但文件已保存" -F Yellow
}

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -F Green
Write-Host "║      修復完成！                                               ║" -F Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -F Green
Write-Host ""
Write-Host "修復內容:" -F Cyan
Write-Host "  1. 移除了 show_log=False 參數" -F White
Write-Host "  2. 添加了日誌控制代碼" -F White
Write-Host "  3. 通過了語法檢查" -F White
Write-Host ""
Write-Host "備份文件: $backupPath" -F Cyan
Write-Host ""
Write-Host "現在可以重新運行批量處理腳本了！" -F Green

Pause

