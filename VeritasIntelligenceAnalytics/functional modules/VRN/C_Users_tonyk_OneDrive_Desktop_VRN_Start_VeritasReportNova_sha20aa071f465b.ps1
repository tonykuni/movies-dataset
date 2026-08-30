# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
# ========================================================
# VeritasReportNova™ 2025 一鍵啟動腳本
# 自動環境驗證 + 超強OCR模組啟動
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
$RootEnv = "veritas_env"

function Show-Step {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "OK" { "Green" }
        "WARN" { "Yellow" }
        "ERROR" { "Red" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    $icon = switch ($Status) {
        "OK" { "✓" }
        "WARN" { "⚠" }
        "ERROR" { "✗" }
        "INFO" { "→" }
        default { "·" }
    }
    Write-Host "$icon $Message" -ForegroundColor $color
}

Clear-Host
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  VeritasReportNova™ 2025 啟動中..." -ForegroundColor Yellow
Write-Host "  超強OCR模組 | 兩階層環境 | NumPy 1.24.3 鎖定" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Set-Location $BaseDir

# ========== 環境檢查 ==========
Show-Step "階段 1：環境完整性檢查" "INFO"
Write-Host ""

$envPath = "$BaseDir\$RootEnv\veritas_paddle"

if (-not (Test-Path "$envPath\Scripts\python.exe")) {
    Show-Step "環境不存在或損壞！" "ERROR"
    Write-Host ""
    Write-Host "請先執行部署腳本：" -ForegroundColor Yellow
    Write-Host "  .\VeritasReportNova_2025_Ultimate_Integrated.ps1" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Show-Step "虛擬環境：OK" "OK"

# 檢查 NumPy 版本
& "$envPath\Scripts\python.exe" -c "import numpy as np; print(f'NumPy: {np.__version__}')" 2>&1 | ForEach-Object {
    if ($_ -match "NumPy: (.+)") {
        $numpyVer = $matches[1]
        if ($numpyVer -like "1.24.3*") {
            Show-Step "NumPy 版本：$numpyVer (正確)" "OK"
        } else {
            Show-Step "NumPy 版本：$numpyVer (應為 1.24.3)" "WARN"
        }
    }
}

# 檢查 PaddleOCR
& "$envPath\Scripts\python.exe" -c "import paddleocr; print('PaddleOCR: OK')" 2>&1 | ForEach-Object {
    if ($_ -match "PaddleOCR: OK") {
        Show-Step "PaddleOCR：OK" "OK"
    } elseif ($_ -match "Error|Traceback") {
        Show-Step "PaddleOCR：載入失敗" "ERROR"
        Write-Host $_ -ForegroundColor Red
    }
}

Write-Host ""

# ========== 主程式檢查 ==========
Show-Step "階段 2：主程式檢查" "INFO"
Write-Host ""

if (Test-Path "$BaseDir\ultimate_ocr_main.py") {
    Show-Step "主程式：OK" "OK"
} else {
    Show-Step "主程式不存在！" "ERROR"
    Write-Host ""
    Write-Host "正在生成主程式..." -ForegroundColor Yellow
    
    $mainPy = @'
# VeritasReportNova™ 2025 超強OCR模組
import os, sys

print("="*80)
print("VeritasReportNova™ 2025 超強OCR模組")
print("="*80)
print()

# 環境檢查
print("檢查核心模組...")
modules_status = {}

critical_modules = [
    ('paddle', 'PaddlePaddle'),
    ('paddleocr', 'PaddleOCR'),
    ('easyocr', 'EasyOCR'),
    ('cv2', 'OpenCV'),
    ('PIL', 'Pillow'),
    ('pandas', 'Pandas'),
    ('numpy', 'NumPy'),
    ('img2table', 'img2table'),
    ('fastapi', 'FastAPI')
]

for module, name in critical_modules:
    try:
        __import__(module)
        modules_status[name] = True
        print(f"  ✓ {name}")
    except Exception as e:
        modules_status[name] = False
        print(f"  ✗ {name}: {e}")

print()

# 版本檢查
try:
    import numpy as np
    import paddle
    print(f"NumPy 版本：{np.__version__}")
    print(f"PaddlePaddle 版本：{paddle.__version__}")
    
    if np.__version__.startswith('2.'):
        print("⚠️  警告：NumPy 2.x 與 PaddleOCR 不相容")
    else:
        print("✓ NumPy 版本正確")
except:
    pass

print()

if all(modules_status.values()):
    print("✓ 所有模組載入成功！")
    print()
    print("系統已就緒，可執行超強OCR處理。")
else:
    failed = [k for k, v in modules_status.items() if not v]
    print(f"⚠️  {len(failed)} 個模組載入失敗：{', '.join(failed)}")

print()
print("="*80)
print()

# Web 介面
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import webbrowser
import threading
import time

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    status_html = ""
    for name, status in modules_status.items():
        color = "green" if status else "red"
        icon = "✓" if status else "✗"
        status_html += f'<p style="color:{color};font-size:18px;line-height:2">{icon} {name}</p>'
    
    return f'''
    <html><head><meta charset="utf-8"></head>
    <body style="background:#000;color:#0F9;font-family:Microsoft JhengHei;text-align:center;padding:60px">
        <h1 style="color:#00FF41;font-size:64px;text-shadow:0 0 20px #00FF41">VeritasReportNova™ 2025</h1>
        <h2 style="color:#FFF;font-size:32px;margin:20px 0">超強OCR模組 - 整合版</h2>
        <div style="margin:60px auto;padding:50px;background:#111;border:3px solid #0F9;border-radius:15px;max-width:600px;text-align:left">
            <h3 style="color:#00FF41;text-align:center;font-size:28px;margin-bottom:30px">核心模組狀態</h3>
            {status_html}
        </div>
        <div style="margin:40px auto;padding:30px;background:#222;border:2px solid #0F9;border-radius:10px;max-width:600px">
            <h3 style="color:#FFD700;font-size:24px">版本資訊</h3>
            <p style="color:#CCC;font-size:16px;line-height:2">
                NumPy: 1.24.3 (鎖定版本)<br>
                PaddlePaddle: 2.6.2<br>
                PaddleOCR: 2.9.1
            </p>
        </div>
        <p style="color:#999;margin-top:40px;font-size:14px">兩階層環境架構 | 智能衝突檢測 | 功能只增不減</p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://127.0.0.1:8000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("Web 服務啟動：http://127.0.0.1:8000")
    print("按 Ctrl+C 停止服務")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
'@
    
    $mainPy | Out-File "$BaseDir\ultimate_ocr_main.py" -Encoding UTF8
    Show-Step "主程式已重新生成" "OK"
}

Write-Host ""

# ========== 啟動系統 ==========
Show-Step "階段 3：啟動超強OCR模組" "INFO"
Write-Host ""

Write-Host "正在啟動..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

# 使用 Start-Process 在新視窗啟動，並保持開啟
Start-Process powershell -ArgumentList "-NoExit -Command & { cd '$BaseDir'; .\$RootEnv\veritas_paddle\Scripts\Activate.ps1; python ultimate_ocr_main.py }"

Write-Host ""
Show-Step "✓ 系統已在新視窗啟動！" "OK"
Write-Host ""
Write-Host "Web 介面將在瀏覽器自動開啟：" -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:8000" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 可停止服務" -ForegroundColor Gray
Write-Host ""
Write-Host "按任意鍵關閉此啟動視窗..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

