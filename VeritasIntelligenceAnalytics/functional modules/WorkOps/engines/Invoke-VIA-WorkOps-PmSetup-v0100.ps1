#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-PmSetup v0100 — 分析層完整依賴之「無衝突」隔離安裝
------------------------------------------------------------------------------------------
 金律:pm4py 需 NumPy<2.0,而平台基底是 NumPy 2.x(pandas 3 依賴)。
       絕不把 pm4py 裝進基底(analytics 畫面那句 pip install pm4py 不可照做)。
 本安裝器依平台 EnvManager 隔離法:在 engines\.venv_pm 建專用 venv,
 wheels-only 安裝 numpy<2 / pandas<3 / scikit-learn / pm4py,jieba(純 Python 無 wheel)另裝。
 之後 via-workops analytics / deep 自動優先使用此 venv;venv 不入版控(.gitignore)。
 誠實原則:逐套件回報成敗;任何失敗不中斷其餘;結尾以 import 實測 pm4py。
==========================================================================================
#>
param([switch]$Recreate)
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
$ErrorActionPreference = "Continue"
$Here = $PSScriptRoot
$Venv = Join-Path $Here ".venv_pm"
$VPy  = Join-Path $Venv "Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  WorkOps PmSetup v0100  |  隔離 venv 無衝突安裝(NumPy<2 金律)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

if ($Recreate -and (Test-Path -LiteralPath $Venv)) {
    Write-Host "[0/4] -Recreate:移除舊 venv..." -ForegroundColor DarkYellow
    Remove-Item -LiteralPath $Venv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $VPy)) {
    Write-Host "[1/4] 建立隔離環境 engines\.venv_pm ..." -ForegroundColor Yellow
    & py -m venv $Venv
    if (-not (Test-Path -LiteralPath $VPy)) { Write-Host "[FAIL] venv 建立失敗(py -m venv)— 停止,基底未被觸碰" -ForegroundColor Red; return }
} else {
    Write-Host "[1/4] venv 已在位(-Recreate 可重建)" -ForegroundColor Green
}

Write-Host "[2/4] wheels-only 安裝核心(逐套件,失敗續行)..." -ForegroundColor Yellow
$ok = @(); $fail = @()
foreach ($pkg in @('numpy<2', 'pandas<3', 'scikit-learn', 'pm4py')) {
    & $VPy -m pip install --only-binary=:all: --disable-pip-version-check -q $pkg
    if ($LASTEXITCODE -eq 0) { $ok += $pkg; Write-Host ("  [OK  ] {0}" -f $pkg) -ForegroundColor Green }
    else { $fail += $pkg; Write-Host ("  [FAIL] {0}(wheels-only 無可用輪)" -f $pkg) -ForegroundColor Red }
}
Write-Host "[3/4] jieba(純 Python,無 wheel 故不限 binary)..." -ForegroundColor Yellow
& $VPy -m pip install --disable-pip-version-check -q jieba
if ($LASTEXITCODE -eq 0) { $ok += 'jieba'; Write-Host "  [OK  ] jieba" -ForegroundColor Green }
else { $fail += 'jieba'; Write-Host "  [FAIL] jieba" -ForegroundColor Red }

Write-Host "[4/4] import 實測..." -ForegroundColor Yellow
& $VPy -c "import numpy, pm4py; print('  [VERIFY] numpy', numpy.__version__, '(<2 金律達成)· pm4py', pm4py.__version__)"
if ($LASTEXITCODE -ne 0) { Write-Host "  [VERIFY-FAIL] pm4py import 未過 — analytics 將續用基底(無 pm4py 降級)" -ForegroundColor Red }

Write-Host ("[總結] 成功 {0} / 失敗 {1} · 基底環境零觸碰 · analytics/deep 之後自動優先用此 venv" -f $ok.Count, $fail.Count) -ForegroundColor Green
if ($fail.Count) { Write-Host ("[誠實清單] 未成:{0}" -f ($fail -join ", ")) -ForegroundColor Yellow }

