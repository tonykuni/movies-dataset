# def Install Python libs into isolated VHB venv
$ErrorActionPreference = 'Continue'
$Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VHB"
$Venv = Join-Path $Base "VENDOR\python\vhb_py_venv"
$Req = @(
  "beautifulsoup4",
  "lxml",
  "html5lib",
  "jinja2",
  "pydantic",
  "jsonschema",
  "pandas",
  "polars",
  "pyarrow",
  "duckdb",
  "pillow",
  "cairosvg",
  "imagehash"
)
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Write-Host "[WARN] python not found"; return }
if (-not (Test-Path -LiteralPath $Venv)) { python -m venv $Venv }
$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --upgrade pip
foreach ($p in $Req) { & $Py -m pip install $p }
Write-Host "[OK] Python VHB venv ready: $Venv"

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
