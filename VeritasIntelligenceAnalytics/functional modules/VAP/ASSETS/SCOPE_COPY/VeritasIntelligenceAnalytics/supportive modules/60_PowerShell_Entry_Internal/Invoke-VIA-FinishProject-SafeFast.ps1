# def PARAMETERS
$def_ROOT = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module"
$def_SUPPORTIVE_ROOT = Join-Path $def_ROOT "supportive_module"
$def_RUN_ID = "VIA_VRN_FULL_INTEGRATION_SAFE_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$def_RUN_DIR = Join-Path $def_ROOT "_via_project_finish_runs\$def_RUN_ID"
$def_JSON = Join-Path $def_RUN_DIR "via_finish_project_matrix.json"
$def_HTML = Join-Path $def_RUN_DIR "via_finish_project_matrix.html"
$def_HARDGATE = Join-Path $def_SUPPORTIVE_ROOT "Invoke-VIA-SupportiveHardGate.ps1"

$def_TARGET_DIRS = @(
  (Join-Path $def_ROOT "VRN"),
  (Join-Path $def_ROOT "VDF"),
  (Join-Path $def_ROOT "VAP"),
  (Join-Path $def_ROOT "supportive_module")
)

$def_SUPPORTIVE_MODULES = @(
  "VIA_SSOT_Unified.py",
  "VIA_RegistryCore_v1.py",
  "VIA_Runtime_Bridge_All_in_One.py",
  "VIA_EnvManager.py",
  "VIA_Panorama_AST_RuntimeInjector.py",
  "VeritasCeleritas.py",
  "VeritasAegisNexus.py"
)

$def_RISK_PATTERNS = [ordered]@{
  "DESTRUCTIVE" = "Remove-Item|Stop-Process|taskkill|rm -rf|shutil\.rmtree|os\.remove|unlink\("
  "NETWORK_IO" = "requests\.|httpx\.|aiohttp|urllib|cloudscraper|playwright|selenium|fetch_|download"
  "ENV_MUTATION" = "pip install|pip uninstall|conda install|uv pip|poetry add"
  "PARALLEL_ACCEL" = "ThreadPool|ProcessPool|multiprocessing|joblib|ray|dask|xmap|xbatch|xfetch"
  "EXEC_EVAL" = "eval\(|exec\("
  "BLOCK_SLEEP" = "time\.sleep|Start-Sleep"
}

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

# def PREPARE
New-Item -ItemType Directory -Force -Path $def_RUN_DIR | Out-Null

# def FIND PYTHON
$def_PythonCandidates = @(
  "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
  "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
  "C:\Python313\python.exe",
  "python"
)

$def_PYTHON = $null
foreach ($p in $def_PythonCandidates) {
  try {
    & $p --version *> $null
    if ($LASTEXITCODE -eq 0) { $def_PYTHON = $p; break }
  } catch {}
}

# def HARDGATE
$def_HardGatePass = $false
if (Test-Path -LiteralPath $def_HARDGATE) {
  try {
    $def_HardGatePass = (. $def_HARDGATE)
  } catch {
    $def_HardGatePass = $false
  }
}

# def ROWS
$def_ROWS = New-Object System.Collections.Generic.List[object]
$def_SUPPORT_ROWS = New-Object System.Collections.Generic.List[object]

# def SUPPORTIVE CHECK
foreach ($m in $def_SUPPORTIVE_MODULES) {
  $p = Join-Path $def_SUPPORTIVE_ROOT $m
  $exists = Test-Path -LiteralPath $p
  $compile = $false
  $err = ""

  if ($exists -and $def_PYTHON -and $m.EndsWith(".py")) {
    & $def_PYTHON -m py_compile $p 2>$null
    $compile = ($LASTEXITCODE -eq 0)
  }

  $def_SUPPORT_ROWS.Add([ordered]@{
    Module = $m
    Path = $p
    Exists = $exists
    Compile = $compile
    Role = "SUPPORTIVE_GATE"
  })
}

# def FILE SCAN
foreach ($dir in $def_TARGET_DIRS) {
  if (-not (Test-Path -LiteralPath $dir)) { continue }

  Get-ChildItem -LiteralPath $dir -Recurse -File -Include *.py,*.ps1,*.psm1,*.html,*.json |
    Where-Object { $_.FullName -notmatch "_via_|__pycache__|\.venv|node_modules|_backup" } |
    ForEach-Object {
      $file = $_
      $text = ""
      try { $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 } catch { $text = "" }

      $anchors = @()
      foreach ($a in $def_ANCHOR_PATTERNS) {
        if ($text -match $a) { $anchors += $a }
      }

      $risks = @()
      foreach ($k in $def_RISK_PATTERNS.Keys) {
        if ($text -match $def_RISK_PATTERNS[$k]) { $risks += $k }
      }

      $risk = "GREEN"
      if ($risks.Count -gt 0) { $risk = "YELLOW" }
      if ($risks -contains "DESTRUCTIVE" -or $risks -contains "ENV_MUTATION" -or $risks -contains "NETWORK_IO") {
        $risk = "RED_LOCKED"
      }

      $action = "AUDIT_ONLY"
      if ($def_HardGatePass -and $risk -eq "GREEN" -and $anchors.Count -gt 0) {
        $action = "SAFE_FIX_READY_WITH_BACKUP"
      } elseif ($def_HardGatePass -and $risk -eq "YELLOW") {
        $action = "PLAN_ONLY_REQUIRE_GATE"
      } elseif ($risk -eq "RED_LOCKED") {
        $action = "LOCKED_REVIEW_REQUIRED"
      }

      $system = "GENERAL"
      if ($file.FullName -match "\\VRN\\") { $system = "VRN" }
      elseif ($file.FullName -match "\\VDF\\") { $system = "VDF" }
      elseif ($file.FullName -match "\\VAP\\") { $system = "VAP" }
      elseif ($file.FullName -match "\\supportive_module\\") { $system = "SUPPORTIVE" }

      $def_ROWS.Add([ordered]@{
        System = $system
        Name = $file.Name
        Path = $file.FullName
        Ext = $file.Extension
        SizeKB = [math]::Round($file.Length / 1KB, 2)
        AnchorCount = $anchors.Count
        Anchors = ($anchors -join ", ")
        RiskLevel = $risk
        Risks = ($risks -join ", ")
        SafeAction = $action
        LastWriteTime = $file.LastWriteTime.ToString("s")
      })
    }
}

# def SUMMARY
$summary = [ordered]@{
  RunId = $def_RUN_ID
  GeneratedAt = (Get-Date).ToString("s")
  Root = $def_ROOT
  Python = $def_PYTHON
  HardGatePass = $def_HardGatePass
  TotalFiles = $def_ROWS.Count
  Green = @($def_ROWS | Where-Object {$_.RiskLevel -eq "GREEN"}).Count
  Yellow = @($def_ROWS | Where-Object {$_.RiskLevel -eq "YELLOW"}).Count
  RedLocked = @($def_ROWS | Where-Object {$_.RiskLevel -eq "RED_LOCKED"}).Count
  VRNFiles = @($def_ROWS | Where-Object {$_.System -eq "VRN"}).Count
  VDFFiles = @($def_ROWS | Where-Object {$_.System -eq "VDF"}).Count
  VAPFiles = @($def_ROWS | Where-Object {$_.System -eq "VAP"}).Count
  Policy = "Safety first, fast completion: HardGate -> Panorama -> Anchors -> Risk -> SafeFix Plan. No destructive edit."
}

$payload = [ordered]@{
  Summary = $summary
  SupportiveModules = $def_SUPPORT_ROWS
  Rows = $def_ROWS
}

$payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $def_JSON -Encoding UTF8

# def HTML
$trsSupport = foreach ($r in $def_SUPPORT_ROWS) {
  $c = if ($r.Exists -and $r.Compile) { "#16a34a" } else { "#dc2626" }
  "<tr><td>$($r.Module)</td><td><code>$($r.Path)</code></td><td>$($r.Exists)</td><td style='color:$c;font-weight:800'>$($r.Compile)</td><td>$($r.Role)</td></tr>"
}

$trs = foreach ($r in $def_ROWS) {
  $c = "#16a34a"
  if ($r.RiskLevel -eq "YELLOW") { $c = "#ca8a04" }
  if ($r.RiskLevel -eq "RED_LOCKED") { $c = "#dc2626" }

  "<tr>
<td>$($r.System)</td>
<td>$($r.Name)</td>
<td><code>$($r.Path)</code></td>
<td>$($r.AnchorCount)</td>
<td>$($r.Anchors)</td>
<td style='color:$c;font-weight:800'>$($r.RiskLevel)</td>
<td>$($r.Risks)</td>
<td><b>$($r.SafeAction)</b></td>
</tr>"
}

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Finish Project SafeFast Matrix</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;background:#f5f4f0;color:#1f2937;margin:20px}
.card{background:#fff;border:1px solid #ddd6c7;border-radius:14px;padding:16px;margin-bottom:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
h1{margin:0;font-size:22px}
h2{margin:4px 0 0;color:#4c78a8;font-size:13px;letter-spacing:.08em}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}
.kpi{background:#fafaf8;border:1px solid #ddd6c7;border-radius:10px;padding:10px;text-align:center}
.kpi .n{font-size:18px;font-weight:800}
.kpi .l{font-size:10px;color:#6b7280}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{border:1px solid #ddd6c7;padding:7px;vertical-align:top}
th{background:#edecea;position:sticky;top:0}
code{font-size:10px}
.ok{color:#16a34a;font-weight:800}
.bad{color:#dc2626;font-weight:800}
.warn{color:#ca8a04;font-weight:800}
</style>
</head>
<body>
<div class="card">
<h1>VIA / VRN Finish Project SafeFast Matrix</h1>
<h2>VERITAS INTELLIGENCE ANALYTICS</h2>
<p>Generated: $($summary.GeneratedAt)</p>
<p>Policy: Safety first, fast completion. 不破壞、不刪檔、不開網路、不開並行，先全景定位與修正許可矩陣。</p>
<p>HardGatePass: <span class="$(if($def_HardGatePass){'ok'}else{'bad'})">$def_HardGatePass</span></p>
</div>

<div class="card grid">
<div class="kpi"><div class="n">$($summary.TotalFiles)</div><div class="l">Total Files</div></div>
<div class="kpi"><div class="n">$($summary.VRNFiles)</div><div class="l">VRN</div></div>
<div class="kpi"><div class="n">$($summary.VDFFiles)</div><div class="l">VDF</div></div>
<div class="kpi"><div class="n">$($summary.VAPFiles)</div><div class="l">VAP</div></div>
<div class="kpi"><div class="n" style="color:#16a34a">$($summary.Green)</div><div class="l">GREEN</div></div>
<div class="kpi"><div class="n" style="color:#ca8a04">$($summary.Yellow)</div><div class="l">YELLOW</div></div>
<div class="kpi"><div class="n" style="color:#dc2626">$($summary.RedLocked)</div><div class="l">RED LOCKED</div></div>
</div>

<div class="card">
<h3>Supportive Module Gate</h3>
<table>
<thead><tr><th>Module</th><th>Path</th><th>Exists</th><th>Compile</th><th>Role</th></tr></thead>
<tbody>
$($trsSupport -join "`n")
</tbody>
</table>
</div>

<div class="card">
<h3>Panorama Risk / Anchor Matrix</h3>
<table>
<thead>
<tr><th>System</th><th>Name</th><th>Path</th><th>Anchors</th><th>Anchor Detail</th><th>Risk</th><th>Risk Detail</th><th>Safe Action</th></tr>
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
Start-Process $def_HTML

# def OUTPUT
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VIA / VRN PROJECT FINISH SAFEFAST MATRIX" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[HardGate] $def_HardGatePass" -ForegroundColor Green
Write-Host "[Total]    $($summary.TotalFiles)" -ForegroundColor Green
Write-Host "[VRN]      $($summary.VRNFiles)" -ForegroundColor Green
Write-Host "[GREEN]    $($summary.Green)" -ForegroundColor Green
Write-Host "[YELLOW]   $($summary.Yellow)" -ForegroundColor Yellow
Write-Host "[RED]      $($summary.RedLocked)" -ForegroundColor Red
Write-Host "[JSON]     $def_JSON" -ForegroundColor Green
Write-Host "[HTML]     $def_HTML" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "下一步：只處理 GREEN + SAFE_FIX_READY_WITH_BACKUP；YELLOW 先 gate；RED_LOCKED 只人工審查。" -ForegroundColor Yellow

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
