# def Install Python libs into isolated VHB venv
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

