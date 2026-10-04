# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Samples = 'C:\測試樣本報告', [int]$MaxMin = 50, [int]$Lanes = 0, [switch]$NoPush, [switch]$NoLock)
# AI 產出必須接入模板。只動 $PID,關閉即還原。新規定:前段 安全清理 · TEMP · 加速器 · 雙軌;收尾 黃字貼 AI · 紅字錯誤。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-TestFixLock-v0101.ps1 — 邊測 · 邊修 · 邊更新 · 邊鎖(操作員 2026-10-03)
#   軌 A:子系統全景(ssot panorama --full · 編號 audit)→ VDF‖VRN 引擎自測多軌(EngineLanes v0102:紅的帶 Traceback 檔:行 AST 錨點)
#   軌 B:C:\測試樣本報告 實測(RealTest v0103:25 風險 ‖ VRN 輸出 → 清點 → 249)
#   收口:綠的 → registry-sync --apply → commit → push → 每支一個 LKGC tag(lkgc/<引擎>/<版>@<sha>)+ 只增帳 ENGINE_LOCK_LEDGER.jsonl
#         紅的 → 檔:行 錨點 + 判決 → 貼回包(AI 出薄尾;一次全部,不排隊)
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent; Set-Location -LiteralPath $VIA
$env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()
$skel = Get-ChildItem $VIA -Filter 'VeritasCeleritas.PS7.Skeleton-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if (-not $skel) { Write-Host "骨架不在(VeritasCeleritas.PS7.Skeleton-v*.ps1)" -ForegroundColor Red; return }
$skelText = Get-Content $skel.FullName -Raw -Encoding UTF8; $cut = $skelText.IndexOf('# ======================= 骨架主體'); Invoke-Expression $skelText.Substring(0, $cut)

Invoke-VCSafeCleanup; $Run = Initialize-VCTemp; Initialize-VCAccel
$LogDir = Join-Path $VIA ("VIA_Reports\review\tfl_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Reg = if ($global:VIARegisterPath) { $global:VIARegisterPath } else { (Get-ChildItem $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName }
$lanesPs = (Get-ChildItem $VIA -Filter 'Invoke-VIA-EngineLanes-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName
$rtPs = (Get-ChildItem $VIA -Filter 'Invoke-VIA-RealTest-VRN-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName
git -C $Repo tag -f "pre-tfl/$($script:Stamp)" HEAD | Out-Null; $script:Verdicts.Add("[還原點] tag pre-tfl/$($script:Stamp) · " + (git -C $Repo rev-parse --short=12 HEAD))

# ===== 雙軌 =====
$LanesDef = @(
  @{ id = 'A-panorama-readiness'; zh = '子系統全景 + 編號稽核 + VDF‖VRN 引擎自測(AST 錨點)'; args = @($VIA, $Reg, $lanesPs, $Lanes, $MaxMin, $LogDir); run = { param($VIA, $Reg, $lanesPs, $Lanes, $MaxMin, $LogDir) Set-Location $VIA; . $Reg | Out-Null; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'; $pf = Join-Path $LogDir 'A-panorama-readiness.progress'
      Set-Content $pf '5 · 全景' -Encoding UTF8; "## 全景"; via-vcgc ssot panorama --full 2>&1 | Select-String '\[(GREEN|YELLOW|RED)\]|總判|族總判' | ForEach-Object { $_.Line.Trim() } | Select-Object -First 16
      Set-Content $pf '20 · 編號稽核' -Encoding UTF8; "## 編號"; via-vcgc run --family core CGC_MDL237_NumberingSystem audit 2>&1 | Select-String '遺失|改身分|重號|缺號|FPSTALE|UNCOMMITTED' | ForEach-Object { $_.Line.Trim() } | Select-Object -First 6
      Set-Content $pf '30 · 引擎自測起' -Encoding UTF8; "## 引擎自測"; if ($lanesPs) { & $lanesPs -Family @('vdf', 'vrn') -Lanes $Lanes -MaxMin ([Math]::Max(10, $MaxMin - 10)) -ProgressFile $pf 2>&1 | Select-String '\[(計|RED|GREEN|NODATA)\]|總判|GREEN \d|RED \d' | ForEach-Object { $_.Line.Trim() } | Select-Object -Last 8 } else { "[FAIL] EngineLanes 腳本不在" } } },
  @{ id = 'B-realtest'; zh = "實測 $Samples(25 風險 ‖ VRN 輸出 → 清點 → 249)"; args = @($VIA, $Reg, $rtPs, $Samples, $MaxMin, $LogDir); run = { param($VIA, $Reg, $rtPs, $Samples, $MaxMin, $LogDir) Set-Location $VIA; . $Reg | Out-Null; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'; Set-Content (Join-Path $LogDir 'B-realtest.progress') '10 · 實測起' -Encoding UTF8
      if ($rtPs) { & $rtPs -Samples $Samples -MaxMin ([Math]::Max(10, $MaxMin - 10)) 2>&1 | ForEach-Object { "" + $_ } | Where-Object { $_ -match '^\[(清點|判|風險|249|車道)\]|^\[A-risk25\]|^\[B-outputs\]|錯誤' } } else { "[FAIL] RealTest 腳本不在" } } })
Invoke-VCDualLane -Lanes $LanesDef -LogDir $LogDir

# ===== 收口 ①:讀引擎矩陣 → 綠 / 紅名單 =====
$csv = "$VIA\VIA_Reports\review\ENGINE_READINESS_latest.csv"
$green = @(); $red = @()
if (Test-Path $csv) { $rows = Import-Csv $csv -Encoding UTF8 | Where-Object { (Get-Item $csv).LastWriteTime -gt (Get-Date).AddMinutes(-$MaxMin) }
  $green = @($rows | Where-Object { $_.燈 -eq 'GREEN' }); $red = @($rows | Where-Object { $_.燈 -eq 'RED' })
  $script:Verdicts.Add("[矩陣] 引擎 $($rows.Count) · 綠 $($green.Count) · 紅 $($red.Count) · 沒料 $(@($rows | Where-Object { $_.燈 -eq 'NODATA' }).Count)")
} else { $script:Errors.Add("[矩陣] ENGINE_READINESS_latest.csv 不在(軌 A 沒跑完或 EngineLanes 沒落檔)") }

# ===== 收口 ②:綠的 → 登冊 → 提交推 → 每支鎖一個 LKGC tag + 只增帳 =====
if ($green.Count -gt 0) {
  $null = via-vcgc registry-sync --apply 2>&1
  git -C $Repo add -A -- 'VeritasIntelligenceAnalytics/supportive modules' 'VeritasIntelligenceAnalytics/functional modules' 2>&1 | Out-Null
  git -C $Repo commit -q -m "TestFixLock ($($script:Stamp)): $($green.Count) engines GREEN (selftest) · registry-sync applied · append-only" 2>&1 | Out-Null
  $branch = git -C $Repo rev-parse --abbrev-ref HEAD; $sha = git -C $Repo rev-parse --short=12 HEAD
  if (-not $NoPush) { $pu = git -C $Repo push origin $branch 2>&1; if ($LASTEXITCODE -ne 0) { $null = via-medic sync --apply 2>&1; $pu = git -C $Repo push origin $branch 2>&1 }; $script:Verdicts.Add("[推] $branch · $sha · " + $(if ($LASTEXITCODE -eq 0) { 'OK' } else { '被拒(看 git status)' })) }
  if (-not $NoLock) {
    $ledger = "$VIA\VIA_Reports\lkgc\ENGINE_LOCK_LEDGER.jsonl"; New-Item -ItemType Directory -Force -Path (Split-Path $ledger) | Out-Null; $n = 0
    foreach ($g in $green) { $eng = $g.引擎; $ver = if ($eng -match '_v(\d{4})$') { $Matches[1] } else { '0000' }; $stem = $eng -replace '_v\d{4}$', ''
      $tag = "lkgc/$stem/v$ver"; git -C $Repo tag -f $tag HEAD 2>&1 | Out-Null; $n++
      Add-Content $ledger ('{"at":"' + (Get-Date -Format o) + '","engine":"' + $eng + '","tag":"' + $tag + '","sha":"' + $sha + '","verdict":"GREEN","by":"TestFixLock-v0101","rule":"成功一個鎖一個;只增不減"}') -Encoding UTF8 }
    if (-not $NoPush) { git -C $Repo push -q origin --tags 2>&1 | Out-Null }
    $script:Verdicts.Add("[鎖] $n 支綠引擎各一個 LKGC tag(lkgc/<引擎>/v<版>@$sha)· 帳 VIA_Reports\lkgc\ENGINE_LOCK_LEDGER.jsonl(只增)") }
} else { $script:Verdicts.Add("[鎖] 本輪 0 支綠 → 不登不推不鎖") }

# ===== 收口 ③:紅的 → 錨點清單(AI 一次全修,不排隊) =====
foreach ($r in $red) { $script:Errors.Add("[紅] $($r.家族) $($r.引擎) · $($r.判決) · 錨 $($r.錨點)") }
$rt = Get-Content "$VIA\VIA_Reports\vrn\realtest\paste.md" -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 10
foreach ($l in $rt) { if ($l -match '\[RED\]') { $script:Errors.Add("[實測] " + $l) } else { $script:Verdicts.Add("[實測] " + $l) } }
$pan = Get-Content (Join-Path $LogDir 'A-panorama-readiness.log') -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { $_ -match '族總判|總判|遺失|缺號|UNCOMMITTED|FPSTALE' } | Select-Object -First 8
foreach ($l in $pan) { $script:Verdicts.Add("[全景] " + $l.Trim()) }
Show-VCSummary -Title '邊測 · 邊修 · 邊鎖(TestFixLock v0101)' -LogDir $LogDir
Write-Host "`e[90mNEXT: 把上面紅字整段貼給 AI → AI 一次出全部薄尾 → 再跑本支;綠的已鎖、紅的只會變少`e[0m"
