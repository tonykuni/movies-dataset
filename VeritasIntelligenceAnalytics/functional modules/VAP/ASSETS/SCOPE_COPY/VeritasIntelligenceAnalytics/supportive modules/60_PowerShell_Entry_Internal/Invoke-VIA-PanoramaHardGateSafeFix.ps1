# def PARAMETERS
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
$def_ROOT = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module"
$def_SUPPORTIVE_ROOT = Join-Path $def_ROOT "supportive_module"
$def_HARDGATE_RUNNER = Join-Path $def_SUPPORTIVE_ROOT "Invoke-VIA-SupportiveHardGate.ps1"
$def_RUN_ID = "VIA_PANORAMA_HARDGATE_SAFE_FIX_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$def_RUN_DIR = Join-Path $def_ROOT "_via_panorama_hardgate_runs\$def_RUN_ID"
$def_JSON = Join-Path $def_RUN_DIR "panorama_hardgate_matrix.json"
$def_HTML = Join-Path $def_RUN_DIR "panorama_hardgate_matrix.html"

# def TARGETS
$def_TARGET_DIRS = @(
  Join-Path $def_ROOT "VDF",
  Join-Path $def_ROOT "VRN",
  Join-Path $def_ROOT "VAP",
  Join-Path $def_ROOT "supportive_module"
)

# def PATTERNS
$def_ANCHOR_PATTERNS = @(
  "ANCHOR\[VIA:ANCHOR:",
  "\[VIA:ANCHOR:",
  "ANC-",
  "\[ANC:",
  "def_PARAM",
  "def PARAMETERS",
  "def MAIN",
  "SAFE-STATE",
  "SUPPORT:BOOTSTRAP",
  "AI_APPEND_ONLY",
  "CONST:BEGIN",
  "AI:BEGIN"
)

$def_RISK_PATTERNS = @{
  "NETWORK_IO" = "requests\.|httpx\.|aiohttp|urllib|fetch_|download|cloudscraper|playwright|selenium"
  "PARALLEL_ACCEL" = "ThreadPool|ProcessPool|multiprocessing|joblib|ray|dask|xmap|xbatch|xfetch"
  "DESTRUCTIVE" = "Remove-Item|rm -rf|shutil\.rmtree|os\.remove|unlink|Stop-Process|taskkill|exit\("
  "EXEC_EVAL" = "eval\(|exec\("
  "ENV_MUTATION" = "pip install|pip uninstall|conda install|uv pip|poetry add"
  "SLEEP_BLOCK" = "time\.sleep|Start-Sleep"
}

# def PREPARE
New-Item -ItemType Directory -Force -Path $def_RUN_DIR | Out-Null
$def_ROWS = New-Object System.Collections.Generic.List[object]

# def HARDGATE
$def_HardGatePass = $false
if (Test-Path -LiteralPath $def_HARDGATE_RUNNER) {
  try {
    $def_HardGatePass = (. $def_HARDGATE_RUNNER)
  } catch {
    $def_HardGatePass = $false
  }
}

# def SCAN
foreach ($dir in $def_TARGET_DIRS) {
  if (-not (Test-Path -LiteralPath $dir)) { continue }

  Get-ChildItem -LiteralPath $dir -Recurse -File -Include *.py,*.ps1,*.psm1,*.html,*.json |
    Where-Object { $_.FullName -notmatch "_via_|__pycache__|\.venv|node_modules" } |
    ForEach-Object {
      $file = $_
      $text = ""
      try { $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 } catch { $text = "" }

      $anchors = @()
      foreach ($p in $def_ANCHOR_PATTERNS) {
        if ($text -match $p) { $anchors += $p }
      }

      $risks = @()
      foreach ($k in $def_RISK_PATTERNS.Keys) {
        if ($text -match $def_RISK_PATTERNS[$k]) { $risks += $k }
      }

      $riskLevel = "GREEN"
      if ($risks.Count -gt 0) { $riskLevel = "YELLOW" }
      if ($risks -contains "DESTRUCTIVE" -or $risks -contains "ENV_MUTATION" -or $risks -contains "NETWORK_IO") {
        $riskLevel = "RED_LOCKED"
      }

      $safeAction = "AUDIT_ONLY"
      if ($def_HardGatePass -and $riskLevel -eq "GREEN" -and $anchors.Count -gt 0) {
        $safeAction = "SAFE_FIX_ALLOWED_WITH_BACKUP"
      } elseif ($def_HardGatePass -and $riskLevel -eq "YELLOW") {
        $safeAction = "PLAN_ONLY_REQUIRE_GATE"
      }

      $def_ROWS.Add([ordered]@{
        File = $file.FullName
        Name = $file.Name
        Extension = $file.Extension
        SizeKB = [math]::Round($file.Length / 1KB, 2)
        Anchors = ($anchors -join ", ")
        AnchorCount = $anchors.Count
        Risks = ($risks -join ", ")
        RiskLevel = $riskLevel
        SafeAction = $safeAction
        HardGatePass = $def_HardGatePass
        LastWriteTime = $file.LastWriteTime.ToString("s")
      })
    }
}

# def EXPORT JSON
$payload = [ordered]@{
  RunId = $def_RUN_ID
  GeneratedAt = (Get-Date).ToString("s")
  HardGatePass = $def_HardGatePass
  Root = $def_ROOT
  Policy = "HardGate -> Panorama -> Anchor Locator -> Risk Classifier -> SafeFix Plan -> HTML Matrix"
  Rows = $def_ROWS
}
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $def_JSON -Encoding UTF8

# def HTML
$trs = foreach ($r in $def_ROWS) {
  $color = "#16a34a"
  if ($r.RiskLevel -eq "YELLOW") { $color = "#ca8a04" }
  if ($r.RiskLevel -eq "RED_LOCKED") { $color = "#dc2626" }

  "<tr>
<td>$($r.Name)</td>
<td><code>$($r.File)</code></td>
<td>$($r.Extension)</td>
<td>$($r.AnchorCount)</td>
<td>$($r.Anchors)</td>
<td style='color:$color;font-weight:800'>$($r.RiskLevel)</td>
<td>$($r.Risks)</td>
<td><b>$($r.SafeAction)</b></td>
</tr>"
}

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Panorama HardGate SafeFix Matrix</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;background:#f5f4f0;color:#1f2937;margin:20px}
.card{background:#fff;border:1px solid #ddd6c7;border-radius:14px;padding:16px;margin-bottom:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
h1{margin:0;font-size:22px}
h2{margin:4px 0 0;color:#4c78a8;font-size:13px;letter-spacing:.08em}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{border:1px solid #ddd6c7;padding:7px;vertical-align:top}
th{background:#edecea;position:sticky;top:0}
code{font-size:10px}
.ok{color:#16a34a;font-weight:800}
.bad{color:#dc2626;font-weight:800}
</style>
</head>
<body>
<div class="card">
<h1>VIA Panorama HardGate SafeFix Matrix</h1>
<h2>VERITAS INTELLIGENCE ANALYTICS</h2>
<p>Generated: $(Get-Date -Format s)</p>
<p>HardGatePass: <span class="$(if($def_HardGatePass){'ok'}else{'bad'})">$def_HardGatePass</span></p>
<p>Policy: HardGate → Panorama Audit → Anchor Locator → Risk Classifier → SafeFix Plan → HTML Matrix</p>
</div>
<div class="card">
<table>
<thead>
<tr>
<th>Name</th><th>Path</th><th>Ext</th><th>Anchors</th><th>Anchor Detail</th><th>Risk</th><th>Risk Detail</th><th>Safe Action</th>
</tr>
</thead>
<tbody>
$($trs -join "`n")
</tbody>
</table>
</div>
</body>
</html>
"@

Set-Content -LiteralPath $def_HTML -Value $html -Encoding UTF8

# def OPEN
Start-Process $def_HTML

# def SUMMARY
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VIA Panorama HardGate SafeFix Matrix 完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[HardGate] $def_HardGatePass" -ForegroundColor Green
Write-Host "[JSON] $def_JSON" -ForegroundColor Green
Write-Host "[HTML] $def_HTML" -ForegroundColor Green
Write-Host "[Policy] 不直接修正；先產生定位點、風險、修正許可矩陣。" -ForegroundColor Yellow

