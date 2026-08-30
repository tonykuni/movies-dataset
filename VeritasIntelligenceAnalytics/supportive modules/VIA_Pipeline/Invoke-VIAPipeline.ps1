#Requires -Version 7.0
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
<#
.SYNOPSIS
  VIA 輪動引擎一鍵 orchestrator(PS7)。sandbox-first:parse=0 才往下,全綠才 promote。

.DESCRIPTION
  順序:① parse 檢查所有 .py(py_compile,任一非 0 即中止)
        ② via_io 編碼自檢
        ③ twse_chip_scraper(真實籌碼;-SkipScraper 可略,離線/沙箱用)
        ④ rotation_engine
        ⑤ devils_advocate(證偽)
        ⑥ via_pipeline(回測+自演化+自我除錯+裁決,多格式輸出)
  每步檢查 $LASTEXITCODE;非 0 立即停。全部成功且 pipeline 裁決為 VALIDATED → 複製產物到 -PromoteDir。

.EXAMPLE
  pwsh ./Invoke-VIAPipeline.ps1 -Demo
  pwsh ./Invoke-VIAPipeline.ps1 -Prices prices.parquet -Themes themes.json -Export json,csv,parquet,duckdb
#>
[CmdletBinding()]
param(
  [string]$Python      = "python",
  [string]$WorkDir     = $PSScriptRoot,
  [string]$Prices      = "",
  [string]$Themes      = "",
  [string]$Stock       = "2330",
  [int]   $Days        = 40,
  [string]$Export      = "json,csv,parquet,duckdb",
  [string]$Out         = "pipeline_result.json",
  [string]$PromoteDir  = "",
  [switch]$Demo,
  [switch]$SkipScraper
)

# ── UTF-8 強制(避免 PS/Console 中文亂碼) ───────────────────────────────────
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = "Stop"
Set-Location $WorkDir

$PyFiles = @("via_io.py","SUP_MDL603_TwseChipScraper.py","rotation_engine.py","devils_advocate.py","SUP_MDL152_Pipeline.py")
$Results = [System.Collections.Generic.List[object]]::new()

function Step([string]$Name, [scriptblock]$Action) {
  Write-Host "`n── $Name ──" -ForegroundColor Cyan
  $sw = [Diagnostics.Stopwatch]::StartNew()
  try { & $Action } catch { Write-Host "[ERR] $Name : $_" -ForegroundColor Red; $script:Failed = $Name; throw }
  $code = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
  $sw.Stop()
  $ok = ($code -eq 0)
  $Results.Add([pscustomobject]@{ Step=$Name; Exit=$code; Sec=[math]::Round($sw.Elapsed.TotalSeconds,1); OK=$ok })
  if (-not $ok) { Write-Host "[STOP] $Name 退出碼 $code → 中止,不 promote。" -ForegroundColor Red; $script:Failed=$Name; throw "exit $code" }
}

try {
  # ① PARSE GATE — 全部 .py 必須 parse=0
  Step "parse-gate (py_compile)" {
    foreach ($f in $PyFiles) {
      if (-not (Test-Path $f)) { Write-Host "[missing] $f" -ForegroundColor Yellow; $global:LASTEXITCODE=2; return }
      & $Python -m py_compile $f
      if ($LASTEXITCODE -ne 0) { return }
      Write-Host "  parse OK: $f" -ForegroundColor DarkGray
    }
    $global:LASTEXITCODE = 0
  }

  # ② 編碼自檢
  Step "via_io 編碼自檢" { & $Python via_io.py --selftest | Out-Host }

  # ③ 真實籌碼(可略)
  if (-not $SkipScraper) {
    Step "twse_chip_scraper" { & $Python SUP_MDL603_TwseChipScraper.py $Stock $Days | Out-Host }
  } else { Write-Host "`n[skip] twse_chip_scraper(-SkipScraper)" -ForegroundColor Yellow }

  # ④ 輪動引擎
  Step "rotation_engine" {
    if ($Demo -or -not $Prices) { & $Python rotation_engine.py --demo --out rotation_data.json | Out-Host }
    else {
      $pyargs = @("rotation_engine.py","--prices",$Prices,"--out","rotation_data.json")
      if ($Themes) { $pyargs += @("--themes",$Themes) }
      & $Python @args | Out-Host
    }
  }

  # ⑤ 證偽
  Step "devils_advocate" { & $Python devils_advocate.py --demo --out devils_verdict.json | Out-Host }

  # ⑥ 統一 pipeline(回測+自演化+自我除錯+裁決+多格式輸出)
  Step "via_pipeline" {
    $pyargs = @("SUP_MDL152_Pipeline.py","--out",$Out,"--export",$Export)
    if ($Demo -or -not $Prices) { $pyargs += "--demo" } else { $pyargs += @("--prices",$Prices); if ($Themes){$pyargs+=@("--themes",$Themes)} }
    & $Python @args | Out-Host
  }

  # ── 裁決 + promote 閘 ──
  Write-Host "`n══════ ORCHESTRATOR 摘要 ══════" -ForegroundColor Green
  $Results | Format-Table -AutoSize | Out-Host

  $verdict = ""
  if (Test-Path $Out) {
    try { $verdict = (Get-Content $Out -Raw -Encoding utf8 | ConvertFrom-Json).verdict } catch {}
  }
  Write-Host "pipeline verdict: $verdict"

  if ($verdict -like "VALIDATED*") {
    if ($PromoteDir) {
      New-Item -ItemType Directory -Force -Path $PromoteDir | Out-Null
      Get-ChildItem -Path . -Include "rotation_data.*","devils_verdict.*","pipeline_result.*","chip_data.json" -Recurse -ErrorAction SilentlyContinue |
        Copy-Item -Destination $PromoteDir -Force
      Write-Host "[PROMOTE] 全綠 → 已複製產物到 $PromoteDir" -ForegroundColor Green
    } else {
      Write-Host "[PROMOTE READY] 全綠;指定 -PromoteDir 即複製到 live 樹。" -ForegroundColor Green
    }
    exit 0
  } else {
    Write-Host "[HOLD] 裁決非 VALIDATED → 不 promote。" -ForegroundColor Yellow
    exit 1
  }
}
catch {
  Write-Host "`n[FAILED] 於步驟:$script:Failed" -ForegroundColor Red
  $Results | Format-Table -AutoSize | Out-Host
  exit 3
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
