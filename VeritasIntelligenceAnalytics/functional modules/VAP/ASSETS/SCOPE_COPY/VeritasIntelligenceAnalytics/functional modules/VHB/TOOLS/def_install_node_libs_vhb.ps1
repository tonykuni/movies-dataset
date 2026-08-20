# def Install Node libs locally into VHB vendor
$ErrorActionPreference = 'Continue'
$Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VHB"
$NodeDir = Join-Path $Base "VENDOR\node"
New-Item -ItemType Directory -Path $NodeDir -Force | Out-Null
Set-Location $NodeDir
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Host "[WARN] npm not found"; return }
if (-not (Test-Path -LiteralPath "package.json")) { npm init -y }
npm install plotly.js-dist-min echarts chart.js d3 interactjs gridstack sortablejs moveable floating-ui lucide
Write-Host "[OK] Node local libs ready: $NodeDir"
