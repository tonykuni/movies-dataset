#requires -Version 7.0
<# =====================================================================
 Invoke-VAP.ps1 — VAP 模組正門入口(README 規範件;VEF SSOT 結構)
 ---------------------------------------------------------------------
 README 約定:pwsh -NoProfile -File .\Invoke-VAP.ps1
 - config.json 優先;缺席退 config.template.json(誠實註記,不擋)
 - 三段順跑(與 via-vapvdf A1-A3 同呼叫式,動態解析最新版,嚴禁寫死版號):
     A1 引擎探測 probe · A2 chartlib 出圖 · A3 selftest 全譜
 - Originals append-only:所有寫出進 tools\RUN_<ts>\(README 約定)
 - 誠實逐段 OK/FAIL/SKIP 不卡斷;末尾終端矩陣 + summary JSON 存證
 用法:Invoke-VAP.ps1 [-Quick] [-SkipCharts]
   -Quick:只跑 A1。-SkipCharts:跳過 A2(無資料環境用,誠實記 SKIP)。
===================================================================== #>
param([switch]$Quick, [switch]$SkipCharts)
$ErrorActionPreference = "Continue"
$VAP  = $PSScriptRoot
$Root = $VAP | Split-Path -Parent | Split-Path -Parent   # VeritasIntelligenceAnalytics
$Eng  = Join-Path $VAP "engine"
$ts   = Get-Date -Format "yyyyMMdd_HHmmss"
$run  = Join-Path $VAP "tools\RUN_$ts"
New-Item -ItemType Directory -Force -Path $run | Out-Null

function Get-Py {
    foreach ($c in @("py", "python3", "python")) {
        $g = Get-Command $c -ErrorAction SilentlyContinue
        if ($g) { return $g.Source }
    }
    throw "python 不在位"
}
function Get-Newest { param([string]$Dir, [string]$Pattern)
    $f = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($f) { return $f.FullName }
}
$py = Get-Py

# ── config:config.json 優先,缺席退 template(誠實) ──────────────────
$cfgPath = Join-Path $VAP "config.json"
$cfgSrc  = "config.json"
if (-not (Test-Path $cfgPath)) {
    $cfgPath = Join-Path $VAP "config.template.json"
    $cfgSrc  = "config.template.json(誠實註記:正式環境請改名 config.json)"
}
$cfg = if (Test-Path $cfgPath) { Get-Content $cfgPath -Raw | ConvertFrom-Json } else { $null }

Write-Host "=== VAP 正門入口 Invoke-VAP · python=$py · $(if($Quick){'QUICK'}else{'FULL'}) ===" -ForegroundColor Cyan
Write-Host "  [config] $cfgSrc" -ForegroundColor DarkGray
Write-Host "  [run]    $run" -ForegroundColor DarkGray

# ── 三段(與 via-vapvdf A1-A3 完全同式)────────────────────────────────
$stages = @()
$stages += , @("A1 引擎探測", @((Get-Newest $Eng "VAP_ENG003_AutoplotSeabornPlotly_v0*.py"), "probe"), $Root)
if (-not $Quick) {
    if ($SkipCharts) {
        $stages += , @("A2 chartlib 出圖", $null, $Root)   # 誠實 SKIP
    } else {
        $stages += , @("A2 chartlib 出圖", @((Get-Newest $Eng "VAP_ENG001_AutoplotEngineChartlib_v0*.py"), "--demo", "--auto", "--base", $Root), $Root)
    }
    $stages += , @("A3 selftest 全譜", @((Get-Newest $Eng "VAP_ENG003_AutoplotSeabornPlotly_v0*.py"), "selftest"), $Root)
}

$results = @()
foreach ($s in $stages) {
    $name = $s[0]; $cmd = $s[1]; $wd = $s[2]
    if (-not $cmd -or -not $cmd[0]) {
        $why = if ($SkipCharts -and $name -like "A2*") { "-SkipCharts 旗標" } else { "引擎不在位(誠實列缺)" }
        Write-Host "  [SKIP] $name — $why" -ForegroundColor Yellow
        $results += [pscustomobject]@{ stage = $name; verdict = "SKIP"; seconds = 0 }
        continue
    }
    Write-Host "  ── $name ──" -ForegroundColor Yellow
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $log = Join-Path $run ("$($name.Split(' ')[0]).log")
    Push-Location $wd
    & $py @cmd 2>&1 | Tee-Object -FilePath $log | ForEach-Object { "     $_" }
    $code = $LASTEXITCODE
    Pop-Location
    $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    $v = if ($code -eq 0) { "OK" } else { "FAIL" }
    $color = if ($v -eq "OK") { "Green" } else { "Red" }
    Write-Host "  [$v] $name · ${sec}s (exit=$code · log=$(Split-Path $log -Leaf))" -ForegroundColor $color
    $results += [pscustomobject]@{ stage = $name; verdict = $v; seconds = $sec }
}

# ── 總結矩陣 + 存證(寫入 RUN 資料夾;originals append-only)──────────
$okN = @($results | Where-Object verdict -eq "OK").Count
$fN  = @($results | Where-Object verdict -eq "FAIL").Count
$sN  = @($results | Where-Object verdict -eq "SKIP").Count
Write-Host "`n=== VAP 總結矩陣 ===" -ForegroundColor Cyan
$w = ($results | ForEach-Object { $_.stage.Length } | Measure-Object -Maximum).Maximum
foreach ($r in $results) {
    Write-Host ("  {0}  {1,-6} {2,6}s" -f $r.stage.PadRight($w), $r.verdict, $r.seconds)
}
Write-Host "  合計:OK $okN · FAIL $fN · SKIP $sN(誠實口徑,不卡斷)" -ForegroundColor Cyan
@{ ts = $ts; config = $cfgSrc; python = "$py"; results = $results } |
    ConvertTo-Json -Depth 4 | Out-File (Join-Path $run "vap_run_summary.json") -Encoding utf8
Write-Host "  存證:$run\vap_run_summary.json" -ForegroundColor Cyan
exit $(if ($fN -eq 0) { 0 } else { 1 })
