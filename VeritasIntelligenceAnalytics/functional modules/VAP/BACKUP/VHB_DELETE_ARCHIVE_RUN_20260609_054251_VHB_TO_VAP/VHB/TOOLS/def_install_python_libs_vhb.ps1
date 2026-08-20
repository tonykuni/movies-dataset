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
