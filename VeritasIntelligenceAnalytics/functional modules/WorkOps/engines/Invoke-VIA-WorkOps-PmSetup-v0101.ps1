#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-PmSetup v0101 — 分析層完整依賴之「無衝突」隔離安裝(誠實校驗版)
------------------------------------------------------------------------------------------
 v0101 裁定(2026/08/08 操作員實跑證據):
   1) 舊 numpy<2 釘選已過時 — 現代 Python 的 PyPI 輪只有 2.1.0 起
      (實跑:ERROR: Could not find a version that satisfies the requirement numpy<2),
      且 pm4py 2.7.23.3 於 numpy 2.5.1 上實證可跑(深度鏈 386 封全程成功)。
      故 v0101 不再嘗試 numpy<2,由 pm4py 自帶相容 numpy。
   2) 金律不變的部分:pm4py 一族絕不裝進平台基底(analytics 畫面那句
      pip install pm4py 不可照做)— 隔離 venv engines\.venv_pm 照舊。
   3) 舊版 [VERIFY] 硬寫「(<2 金律達成)」即使 numpy 2.5.1 也照印 — 不誠實,
      v0101 只回報實際版本,不做未驗證的宣稱。
   4) 新增 graphviz 偵測:analytics 的 DFG 流程圖需 dot 執行檔在 PATH,
      缺席時誠實提示(分析其餘照常,略過該圖 — 引擎本有優雅降級)。
 誠實原則:逐套件回報成敗;任何失敗不中斷其餘;結尾以 import 實測並印真實版本。
 回退:刪本檔即回 v0100(不建議 — v0100 的 numpy<2 於現代 PyPI 必敗)。
==========================================================================================
#>
param([switch]$Recreate)
$ErrorActionPreference = "Continue"
$Here = $PSScriptRoot
$Venv = Join-Path $Here ".venv_pm"
$VPy  = Join-Path $Venv "Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  WorkOps PmSetup v0101  |  隔離 venv 無衝突安裝(誠實校驗)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

if ($Recreate -and (Test-Path -LiteralPath $Venv)) {
    Write-Host "[0/5] -Recreate:移除舊 venv..." -ForegroundColor DarkYellow
    Remove-Item -LiteralPath $Venv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $VPy)) {
    Write-Host "[1/5] 建立隔離環境 engines\.venv_pm ..." -ForegroundColor Yellow
    & py -m venv $Venv
    if (-not (Test-Path -LiteralPath $VPy)) { Write-Host "[FAIL] venv 建立失敗(py -m venv)— 停止,基底未被觸碰" -ForegroundColor Red; return }
} else {
    Write-Host "[1/5] venv 已在位(-Recreate 可重建)" -ForegroundColor Green
}

Write-Host "[2/5] wheels-only 安裝核心(逐套件,失敗續行;numpy 由 pm4py 自帶相容版)..." -ForegroundColor Yellow
$ok = @(); $fail = @()
foreach ($pkg in @('pandas<3', 'scikit-learn', 'pm4py')) {
    & $VPy -m pip install --only-binary=:all: --disable-pip-version-check -q $pkg
    if ($LASTEXITCODE -eq 0) { $ok += $pkg; Write-Host ("  [OK  ] {0}" -f $pkg) -ForegroundColor Green }
    else { $fail += $pkg; Write-Host ("  [FAIL] {0}(wheels-only 無可用輪)" -f $pkg) -ForegroundColor Red }
}
Write-Host "[3/5] jieba(純 Python,無 wheel 故不限 binary)..." -ForegroundColor Yellow
& $VPy -m pip install --disable-pip-version-check -q jieba
if ($LASTEXITCODE -eq 0) { $ok += 'jieba'; Write-Host "  [OK  ] jieba" -ForegroundColor Green }
else { $fail += 'jieba'; Write-Host "  [FAIL] jieba" -ForegroundColor Red }

Write-Host "[4/5] import 實測(只報真實版本,不做宣稱)..." -ForegroundColor Yellow
& $VPy -c "import numpy, pm4py; print('  [VERIFY] numpy', numpy.__version__, '· pm4py', pm4py.__version__, '· 於隔離 venv 共存實測通過(基底零觸碰)')"
if ($LASTEXITCODE -ne 0) { Write-Host "  [VERIFY-FAIL] pm4py import 未過 — analytics 將續用基底(無 pm4py 降級)" -ForegroundColor Red }

Write-Host "[5/5] graphviz 偵測(DFG 流程圖選配)..." -ForegroundColor Yellow
$dot = Get-Command dot -ErrorAction SilentlyContinue
if ($dot) {
    Write-Host ("  [OK  ] dot 在 PATH:{0} — analytics 可輸出 DFG 圖" -f $dot.Source) -ForegroundColor Green
} else {
    Write-Host "  [提示] 未偵測到 graphviz 的 dot — analytics 會誠實略過 DFG 圖(其餘照常)。" -ForegroundColor DarkYellow
    Write-Host "         欲補上:winget install Graphviz.Graphviz(裝後重開終端讓 PATH 生效)" -ForegroundColor DarkYellow
}

Write-Host ("[總結] 成功 {0} / 失敗 {1} · 基底環境零觸碰 · analytics/deep 之後自動優先用此 venv" -f $ok.Count, $fail.Count) -ForegroundColor Green
if ($fail.Count) { Write-Host ("[誠實清單] 未成:{0}" -f ($fail -join ", ")) -ForegroundColor Yellow }
