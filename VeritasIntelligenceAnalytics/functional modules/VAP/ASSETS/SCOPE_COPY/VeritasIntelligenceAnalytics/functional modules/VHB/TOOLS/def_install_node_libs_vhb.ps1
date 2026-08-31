# def Install Node libs locally into VHB vendor
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
$NodeDir = Join-Path $Base "VENDOR\node"
New-Item -ItemType Directory -Path $NodeDir -Force | Out-Null
Set-Location $NodeDir
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Host "[WARN] npm not found"; return }
if (-not (Test-Path -LiteralPath "package.json")) { npm init -y }
npm install plotly.js-dist-min echarts chart.js d3 interactjs gridstack sortablejs moveable floating-ui lucide
Write-Host "[OK] Node local libs ready: $NodeDir"

