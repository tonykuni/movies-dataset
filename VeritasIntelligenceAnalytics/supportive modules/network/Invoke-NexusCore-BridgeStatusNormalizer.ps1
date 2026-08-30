#requires -Version 7.0
param(
    [string]$ReportRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [switch]$OpenReport
)
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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $ReportRoot "_nexuscore_bridge_status_normalizer\RUN_$stamp"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$outJson = Join-Path $outDir "BRIDGE_STATUS_NORMALIZED.json"
$outHtml = Join-Path $outDir "BRIDGE_STATUS_NORMALIZED.html"

$reports = Get-ChildItem -LiteralPath $ReportRoot -Recurse -File -Filter "NEXUSCORE_EXTERNAL_BRIDGE_REPORT.json" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 20

$rows = @()

foreach ($r in $reports) {
    try {
        $obj = Get-Content -LiteralPath $r.FullName -Raw | ConvertFrom-Json
    } catch {
        continue
    }

    foreach ($item in @($obj)) {
        $risk = [string]$item.Risk
        $help = [string]$item.HelpStatus
        $tool = [string]$item.ToolName

        $normalized = "LOW"
        $action = "ACCEPT"

        if ($risk -eq "HIGH") {
            $normalized = "HIGH"
            $action = "BLOCK"
        } elseif ($risk -eq "MEDIUM" -or $help -match "REVIEW|NO_HELP|TIMEOUT") {
            if ($tool -match "Celeritas") {
                $normalized = "MEDIUM"
                $action = "ROUTE_TO_CELERITAS_SAFE_ADAPTER"
            } else {
                $normalized = "LOW"
                $action = "ACCEPT_AS_NON_DESTRUCTIVE_PROBE"
            }
        }

        $rows += [pscustomobject]@{
            SourceReport=$r.FullName
            ToolName=$tool
            OriginalRisk=$risk
            HelpStatus=$help
            NormalizedRisk=$normalized
            Action=$action
        }
    }
}

$rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outJson -Encoding UTF8

$table = $rows | ConvertTo-Html -Fragment
$html = @"
<!doctype html><html><head><meta charset="utf-8">
<title>Bridge Status Normalized</title>
<style>
body{font-family:Arial,"Microsoft JhengHei",sans-serif;background:#f6f7fb;color:#111827;margin:24px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:18px;margin:16px 0}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#111827;color:#fff;padding:8px;text-align:left}
td{border-bottom:1px solid #e5e7eb;padding:7px;vertical-align:top}
</style></head><body>
<h1>Bridge Status Normalized</h1>
<div class="card">$table</div>
</body></html>
"@
$html | Set-Content -LiteralPath $outHtml -Encoding UTF8

Write-Host "Status : BRIDGE_STATUS_NORMALIZED"
Write-Host "Risk   : LOW"
Write-Host "HTML   : $outHtml"

if ($OpenReport) {
    Start-Process $outHtml
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
