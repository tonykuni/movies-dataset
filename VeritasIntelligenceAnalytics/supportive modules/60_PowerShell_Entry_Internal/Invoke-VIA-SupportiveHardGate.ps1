# def PARAMETERS
$def_SUPPORTIVE_ROOT = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
$def_BRIDGE = Join-Path $def_SUPPORTIVE_ROOT "VIA_Supportive_Runtime_HardGate_Bridge.py"
$def_RUN_ID = "VIA_SUPPORTIVE_GATE_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$def_OUT_DIR = Join-Path $def_SUPPORTIVE_ROOT "_via_supportive_integration_runs\$def_RUN_ID"
$def_REPORT_JSON = Join-Path $def_OUT_DIR "supportive_hardgate_report.json"
$def_REPORT_HTML = Join-Path $def_OUT_DIR "supportive_hardgate_report.html"

# def PREPARE
New-Item -ItemType Directory -Force -Path $def_OUT_DIR | Out-Null

# def PYTHON
$def_PythonCandidates = @(
  "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
  "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
  "C:\Python313\python.exe",
  "python"
)

$def_Python = $null
foreach ($p in $def_PythonCandidates) {
  try {
    & $p --version *> $null
    if ($LASTEXITCODE -eq 0) { $def_Python = $p; break }
  } catch {}
}

if (-not $def_Python) {
  Write-Host "[FAIL] Python not found" -ForegroundColor Red
  return $false
}

# def RUN
$env:VIA_SUPPORTIVE_REPORT_JSON = $def_REPORT_JSON
$env:VIA_SUPPORTIVE_REPORT_HTML = $def_REPORT_HTML

& $def_Python -m py_compile $def_BRIDGE
if ($LASTEXITCODE -ne 0) {
  Write-Host "[FAIL] HardGate bridge compile failed" -ForegroundColor Red
  return $false
}

& $def_Python $def_BRIDGE
if ($LASTEXITCODE -ne 0) {
  Write-Host "[FAIL] HardGate bridge run failed" -ForegroundColor Red
  return $false
}

if (Test-Path $def_REPORT_HTML) {
  Start-Process $def_REPORT_HTML
}

Write-Host "[PASS] VIA Supportive HardGate passed" -ForegroundColor Green
Write-Host "[JSON] $def_REPORT_JSON" -ForegroundColor Green
Write-Host "[HTML] $def_REPORT_HTML" -ForegroundColor Green
return $true
