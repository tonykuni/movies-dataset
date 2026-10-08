# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([int]$Rounds = 2, [string]$ReportDir = 'C:\測試樣本報告', [string]$HandoverZip = "$env:USERPROFILE\Downloads\VRN_v0108_Complete_Handover.zip", [switch]$RunHandover, [switch]$ForceRestore, [int]$ExtractLimit = 0, [string]$Note = 'VRN 高風險測試前', [int]$MaxMin = 60, [int]$KeepRuns = 5, [double]$MaxTempGB = 2.0, [double]$LowRamGB = 2.0, [int]$PyStepSec = 120, [string]$Title = 'VIA 任務', [switch]$NoCleanup, [switch]$KillOrphans, [switch]$NoOpen, [switch]$Demo)
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# VeritasCeleritas.PS7.Skeleton v0109 — 萬用 PS 加速模板 · all-in-one(v0108 三合一 + 風險收斂:孤兒不預設殺 · TEMP 只清 2 小時前且無人用 · 環境變數退出還原 · python 看門狗先柔後硬)
#   前段固定:① 安全清理(只動本行程)② TEMP 為主記憶體 ③ 加速器(AutoImport 在 supportive modules 任何子夾都找得到)
#   中段:④ 雙軌(或多軌)並行 + **主控台矩陣框原地刷新**(Pad-Visual 中文對齊 · 每道一列:項目 │ 進度條▶ │ 狀態與細節;游標上移重繪,不洗版) ⑤ Invoke-VCPython:PS → python 不會卡的通道(直呼 · base64 argv · python 內看門狗 124)
#   收尾:⑥ 黃字貼 AI · 紅字錯誤(進剪貼簿)⑦ 靜態 HTML U/I 直接跳出(file://,不經伺服器;FormatLock 四燈 · 紅燈慢閃 · 電腦/手機自適應)
#   v0110(2026-10-06):② TEMP 律 L115(只清自家 ps_* · 總量上限 -MaxTempGB 預設 2 · 低 RAM -LowRamGB 預設 2 自動 VIA_LOW_RAM=1 + VIA_SPILL_DIR · RUNNING 鎖 · 一行帳含 bytes/RAM)· ④ 壞行分類器 [OK]/[計] 不當紅 · ⑤ python 看門狗 Timer daemon=True(否則每次等滿 Sec 回 124)
#   v0111(2026-10-06):③ 加速器後援:AutoImport 不在 → 點 supportive modules\ps7\VeritasCeleritas.PS7.ps1(30 加速器,Start-CeleritasPS7 自動套用)再 Set-StrictMode -Off(它的 Latest 不外溢);退出 Restore-CeleritasPS7
#   v0112(2026-10-06):⑨ 啟動器段 Invoke-VCLaunch(L117:所有指令 PY 化並導入加速器;PS 只做啟動與連結 U/I)—找子系統尾版 manager → Invoke-VCPython 跑一個動詞 → 從輸出抓 .html 路徑 → 開瀏覽器;PS 本身不含業務邏輯
#   用法:複製改名 → 只改最底下「骨架主體」的 $Lanes;其餘不動。-Demo 跑示範兩道。
$ErrorActionPreference = 'Continue'
$VIA = if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'supportive modules'))) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'; $env:VIA_FROM_VCGC = 'YES'
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new(); $script:LaneState = [ordered]@{}; $script:Timeline = [System.Collections.Generic.List[object]]::new()
$script:PAL = @{ GREEN = '#16a34a'; YELLOW = '#f59e0b'; RED = '#dc2626'; GRAY = '#9ca3af'; NODATA = '#0891b2' }
$script:Esc = [char]27; $script:C = @{ Grey = "$([char]27)[90m"; Red = "$([char]27)[91m"; Green = "$([char]27)[92m"; Yellow = "$([char]27)[93m"; Cyan = "$([char]27)[96m"; Reset = "$([char]27)[0m"; Bold = "$([char]27)[1m" }
$script:VT = $Host.UI.SupportsVirtualTerminal -and -not $env:VIA_NO_VT
function Pad-Visual([string]$String, [int]$Width, [string]$Alignment = 'Left') {   # 視覺寬度補正:去 ANSI 後,CJK 算 2 格;超寬就截(保留 ANSI 重置)
  $clean = $String -replace "$([char]27)\[[0-9;]*m", ''; $w = 0; $cut = ''; $over = $false
  foreach ($ch in $clean.ToCharArray()) { $cw = if ([int]$ch -gt 255) { 2 } else { 1 }; if ($w + $cw -gt $Width) { $over = $true; break }; $w += $cw; $cut += $ch }
  if ($over) { return $cut + (' ' * ($Width - $w)) }                                   # 截斷版本不帶色(避免殘留 ANSI)
  $pad = ' ' * ($Width - $w); if ($Alignment -eq 'Right') { return $pad + $String } else { return $String + $pad } }
function Get-VCBar([int]$pct, [int]$width = 20, [string]$lamp = 'GREEN') {
  $col = switch ($lamp) { 'RED' { $script:C.Red } 'YELLOW' { $script:C.Yellow } 'GRAY' { $script:C.Grey } default { $script:C.Green } }
  $f = [Math]::Round($pct / 100 * $width); $e = $width - $f; $spark = if ($pct -lt 100 -and $f -gt 0) { "$($script:C.Yellow)▶$col" } else { '' }
  $bar = ('█' * [Math]::Max(0, $f - 1)) + $spark + $(if ($f -gt 0 -and $pct -ge 100) { '█' } else { '' }) + ('░' * $e)
  return "$col$bar$($script:C.Reset) " + (Pad-Visual ("$pct%") 4 'Right') }
function Write-VCBoxFrame([int]$rows) {   # 固定外框:項目 20 │ 進度 40 │ 狀態與細節 38;預留 rows 列,之後原地重繪
  $g = $script:C.Grey; $z = $script:C.Reset
  Write-Host "${g}┌──────────────────────┬──────────────────────────────────────────┬────────────────────────────────────────┐$z"
  Write-Host "${g}│$z " + (Pad-Visual '當前執行項目' 20) + " ${g}│$z " + (Pad-Visual '進度動畫與百分比' 40) + " ${g}│$z " + (Pad-Visual '狀態與優化細節' 38) + " ${g}│$z"
  Write-Host "${g}├──────────────────────┼──────────────────────────────────────────┼────────────────────────────────────────┤$z"
  for ($i = 0; $i -lt $rows; $i++) { Write-Host "${g}│$z " + (' ' * 20) + " ${g}│$z " + (' ' * 40) + " ${g}│$z " + (' ' * 38) + " ${g}│$z" }
  Write-Host "${g}└──────────────────────┴──────────────────────────────────────────┴────────────────────────────────────────┘$z" }
function Update-VCBox([object[]]$lines) {   # lines = @(@{name;pct;lamp;status;detail}) ;游標上移 rows+1 行原地重繪(VT 不支援就只印一次)
  $g = $script:C.Grey; $z = $script:C.Reset; $n = $lines.Count
  if ($script:VT) { Write-Host ("$($script:Esc)[" + ($n + 1) + "A") -NoNewline }
  foreach ($L in $lines) { $col = switch ($L.lamp) { 'RED' { $script:C.Red } 'YELLOW' { $script:C.Yellow } 'GREEN' { $script:C.Green } default { $script:C.Grey } }
    $c1 = Pad-Visual $L.name 20; $c2 = Pad-Visual (Get-VCBar $L.pct 20 $L.lamp) 40; $c3 = Pad-Visual ("$col[" + $L.status + "]$z " + $L.detail) 38
    Write-Host "${g}│$z $c1 ${g}│$z $c2 ${g}│$z $c3 ${g}│$z" }
  Write-Host "${g}└──────────────────────┴──────────────────────────────────────────┴────────────────────────────────────────┘$z" }
function Mark([string]$s, [string]$lamp = 'GRAY') { $script:Timeline.Add([pscustomobject]@{ at = (Get-Date -Format HH:mm:ss); what = $s; lamp = $lamp }); Write-Host ("  " + (Get-Date -Format HH:mm:ss) + "  ▶ " + $s) }

# ---------- ① 安全清理(只動本行程) ----------
function Invoke-VCSafeCleanup {
  $MaxMin = if ($MaxMin) { [int]$MaxMin } else { 60 }
  $before = [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
  [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
  $orphans = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $PID" | Where-Object { $_.Name -match 'python|pwsh' -and ((Get-Date) - $_.CreationDate).TotalMinutes -gt $MaxMin })
  if ($KillOrphans) { foreach ($o in $orphans) { try { Stop-Process -Id $o.ProcessId -Force -ErrorAction SilentlyContinue } catch { } } }
  elseif ($orphans.Count) { $script:Verdicts.Add("[清理] 本行程下有 $($orphans.Count) 支超過 $MaxMin 分的 python/pwsh 子行程 → 只列不殺(要殺加 -KillOrphans;dot-source 進主控台時 `$PID 是主控台,殺了會連你別的工作一起殺)") }
  $after = [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2); $cpu = (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average
  $script:Verdicts.Add("[清理] GC 完成 · 可用 RAM $before → $after GB · CPU $cpu% · 孤兒 $($orphans.Count)" + $(if ($KillOrphans) { "(已殺)" } else { "(只列)" }) + "(不動優先權 · 不 EmptyWorkingSet · 不碰他人行程)"); Mark '清理完' 'GREEN' }

# ---------- ② TEMP 為主記憶體(L107 + L115 TEMP 律:只清自家夾 · 總量上限 · 低 RAM 自動開溢寫 · 一行帳) ----------
function Initialize-VCTemp {
  $KeepRuns = if ($KeepRuns) { [int]$KeepRuns } else { 5 }; $MaxTempGB = if ($MaxTempGB) { [double]$MaxTempGB } else { 2.0 }; $LowRamGB = if ($LowRamGB) { [double]$LowRamGB } else { 2.0 }
  $root = if ($env:VIA_TEMP_ROOT) { $env:VIA_TEMP_ROOT } else { Join-Path $env:LOCALAPPDATA 'Temp\VIA_progress' }
  $run = Join-Path $root ("ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $run | Out-Null; $spill = Join-Path $run 'spill'; New-Item -ItemType Directory -Force -Path $spill | Out-Null
  $script:EnvBackup = @{ TMP = $env:TMP; TEMP = $env:TEMP; TMPDIR = $env:TMPDIR; POLARS_TEMP_DIR = $env:POLARS_TEMP_DIR; VIA_DUCKDB_TEMP_DIR = $env:VIA_DUCKDB_TEMP_DIR; VIA_FROM_VCGC = $env:VIA_FROM_VCGC; VIA_NO_OPEN = $env:VIA_NO_OPEN; VIA_SPILL_DIR = $env:VIA_SPILL_DIR; VIA_LOW_RAM = $env:VIA_LOW_RAM }
  $env:VIA_TEMP_ROOT = $root; $env:TMP = $run; $env:TEMP = $run; $env:TMPDIR = $run; $env:POLARS_TEMP_DIR = $run; $env:VIA_DUCKDB_TEMP_DIR = $run; $env:VIA_SPILL_TO_DISK = '1'; $env:VIA_SPILL_DIR = $spill
  $freeGB = try { [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2) } catch { -1 }
  $env:VIA_LOW_RAM = if ($freeGB -ge 0 -and $freeGB -lt $LowRamGB) { '1' } else { '0' }   # 低 RAM:引擎(VIA_TempSpill)改分塊 + 溢寫 TEMP,不改 pagefile、不 EmptyWorkingSet
  # 只清自家夾(ps_*):滾動留 N 輪,再按總量上限從最舊清;鎖住(Running 檔)或 2 小時內的不清;每清一夾一行帳
  $own = @(Get-ChildItem $root -Directory -Filter 'ps_*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending)
  $sizes = @{}; foreach ($d in $own) { $sizes[$d.Name] = (Get-ChildItem $d.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum }
  $total = ($sizes.Values | Measure-Object -Sum).Sum; $purged = @(); $freed = 0
  foreach ($d in ($own | Select-Object -Skip $KeepRuns)) { if ($d.LastWriteTime -lt (Get-Date).AddHours(-2) -and -not (Test-Path (Join-Path $d.FullName 'RUNNING'))) { $purged += $d } }
  $survivors = @($own | Where-Object { $purged -notcontains $_ } | Sort-Object Name)
  foreach ($d in $survivors) { if ($d.Name -eq ("ps_" + $script:Stamp)) { continue }; if (($total - $freed) -le ($MaxTempGB * 1GB)) { break }; if ($d.LastWriteTime -lt (Get-Date).AddHours(-2) -and -not (Test-Path (Join-Path $d.FullName 'RUNNING'))) { $purged += $d; $freed += [double]$sizes[$d.Name] } }
  foreach ($o in $purged) { $sz = [double]$sizes[$o.Name]; Remove-Item $o.FullName -Recurse -Force -ErrorAction SilentlyContinue; Add-Content (Join-Path $root 'purge_ledger.jsonl') ('{"at":"' + (Get-Date -Format o) + '","purged":"' + $o.Name + '","bytes":' + [int64]$sz + ',"rule":"L115 keep ' + $KeepRuns + ' · cap ' + $MaxTempGB + 'GB","free_ram_gb":' + $freeGB + '}') }
  Set-Content (Join-Path $run 'RUNNING') (Get-Date -Format o)
  $script:Verdicts.Add("[TEMP] $run · 滾動留 $KeepRuns 輪 · 上限 $MaxTempGB GB(現 $([Math]::Round(($total - $freed) / 1GB, 2)) GB)· 清 $($purged.Count) 夾 · 可用 RAM $freeGB GB → 低 RAM 溢寫 $(if ($env:VIA_LOW_RAM -eq '1') { '開' } else { '關' })(VIA_SPILL_DIR=$spill)"); Mark 'TEMP 就位' $(if ($env:VIA_LOW_RAM -eq '1') { 'YELLOW' } else { 'GREEN' }); $run }

# ---------- ③ 加速器 ----------
function Initialize-VCAccel {
  $auto = Join-Path $VIA 'supportive modules\VeritasCeleritas.PS7.AutoImport.ps1'
  if (-not (Test-Path $auto)) { $f = Get-ChildItem (Join-Path $VIA 'supportive modules') -Recurse -Depth 2 -Filter 'VeritasCeleritas.PS7.AutoImport*.ps1' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; if ($f) { $auto = $f.FullName } }
  $core = Join-Path $VIA 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
  $loaded = $null
  if (Test-Path $auto) { try { . $auto; $loaded = 'AutoImport' } catch { $script:Verdicts.Add("[加速器] AutoImport 載入失敗:" + $_.Exception.Message.Split([char]10)[0]) } }
  elseif (Test-Path $core) { try { . $core; Set-StrictMode -Off; $loaded = 'VeritasCeleritas.PS7.ps1' } catch { Set-StrictMode -Off; $script:Verdicts.Add("[加速器] 核心載入失敗:" + $_.Exception.Message.Split([char]10)[0]) } }
  if ($loaded) {
    foreach ($fn in (Get-Command -CommandType Function -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'Celeritas' })) { try { Set-Item -Path ('function:global:' + $fn.Name) -Value $fn.ScriptBlock } catch { } }   # 函式內 dot-source 只活在函式內 → 提升到 global,退出 Restore 才找得到
    $ver = try { if ($script:CeleritasPS7) { $script:CeleritasPS7.Version } else { '?' } } catch { '?' }
    if ((Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) -and $loaded -eq 'AutoImport') { try { if ((Get-Command Start-CeleritasPS7).Parameters.ContainsKey('Profile')) { Start-CeleritasPS7 -Profile aggressive | Out-Null } else { Start-CeleritasPS7 | Out-Null } } catch { } }
    $script:AccelLoaded = $true; $script:Verdicts.Add("[加速器] $loaded 已套用(本 PID · $ver · 退出 Restore)"); Mark '加速器' 'GREEN' }
  else { $script:Verdicts.Add("[加速器] AutoImport 與 ps7\VeritasCeleritas.PS7.ps1 都不在 → fallback 無加速,功能照跑;PS-ACCEL 橋(VIA_PS_Accel_Module)" + $(if (Test-Path "$VIA\supportive modules\VIA_PS_Accel_Module.ps1") { '在' } else { '不在' })); Mark '加速器 fallback' 'YELLOW' } }

# ---------- ⑨ 啟動器(L117:PS 只啟動與連結 U/I;邏輯全在 python manager / 引擎) ----------
function Invoke-VCLaunch {
  param([string]$Sub, [string]$Verb, [string[]]$VerbArgs = @(), [int]$Sec = 600, [string]$Id = 'L')
  $map = @{ VRN = @('functional modules\VRN', 'VRN_SystemManager_v*.py'); VDF = @('functional modules\VDF', 'VDF_SystemManager_v*.py'); VCGC = @('supportive modules\registry', 'CGC_MDL*_HealthMatrix_v*.py') }
  if (-not $map.ContainsKey($Sub)) { $script:Errors.Add("[啟動] 不認識的子系統 $Sub(VRN / VDF / VCGC)"); return $null }
  $dir = Join-Path $VIA $map[$Sub][0]
  $tail = Get-ChildItem -LiteralPath $dir -Filter $map[$Sub][1] -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $tail) { $script:Errors.Add("[啟動] $Sub 尾版 manager 不在 $dir"); return $null }
  $script:Verdicts.Add("[啟動] $Sub → $($tail.Name) $Verb $($VerbArgs -join ' ')")
  $env:VIA_FROM_VCGC = 'YES'
  $out = Invoke-VCPython -Id $Id -Argv (@($tail.FullName, $Verb) + $VerbArgs) -Sec $Sec
  $out | Where-Object { $_ -match '^\[計\]|^\s*\[(RED|YEL|注)\]' } | Select-Object -First 30 | ForEach-Object { if ($_ -match '^\s*\[RED\]') { $script:Errors.Add("[$Sub $Verb] " + $_.Trim()) } else { $script:Verdicts.Add("[$Sub $Verb] " + $_.Trim()) } }
  $htmls = @($out | ForEach-Object { if ($_ -match '([A-Za-z]:\\[^\s"]+?\.html)') { $Matches[1] } } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -Unique)
  foreach ($h in $htmls) { $script:Verdicts.Add("[U/I] $h"); if (-not $NoOpen -and $env:VIA_NO_OPEN -ne '1') { try { Start-Process -FilePath $h } catch { } } }
  return $htmls }

# ---------- ⑤ PS → python 不會卡的通道 ----------
function Invoke-VCPython([string]$Id, [string[]]$Argv, [int]$Sec = 0, [string]$Python = 'python') {
  # 直呼 & python(不包 Job · 不重導向);argv 走 base64(PS 原生參數不拆引號);看門狗在 python 內(Timer → os._exit 124)。回 [string[]] 輸出;rc 進 $script:LastRc
  if (-not $Sec) { $Sec = if ($PyStepSec) { $PyStepSec } else { 120 } }
  $json = ($Argv | ConvertTo-Json -Compress); if ($Argv.Count -eq 1) { $json = "[$json]" }; $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
  $wrap = "import base64,json,os,sys,threading,runpy,_thread; a=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); t1=threading.Timer($Sec, _thread.interrupt_main); t1.daemon=True; t1.start(); t2=threading.Timer($Sec+10, lambda: (sys.stdout.flush(), os._exit(124))); t2.daemon=True; t2.start(); sys.argv=a`nimport contextlib`ntry:`n    runpy.run_path(a[0], run_name='__main__')`nexcept KeyboardInterrupt:`n    sys.stdout.flush(); os._exit(124)"
  $t0 = Get-Date; $o = @(& $Python -c $wrap $b64 2>&1 | ForEach-Object { "" + $_ }); $script:LastRc = $LASTEXITCODE; $dt = [int]((Get-Date) - $t0).TotalSeconds   # v0109:先 KeyboardInterrupt(讓引擎 finally / 原子換名跑完)再 10 秒硬殺
  if ($script:LogDir) { $o | Set-Content (Join-Path $script:LogDir "$Id.out") -Encoding UTF8 }
  if ($script:LastRc -eq 124) { $script:Errors.Add("[看門狗] $Id 超過 $Sec 秒 · 最後:" + (($o | Select-Object -Last 1) -join '')); Mark "$Id 逾時" 'RED' }
  elseif ($script:LastRc -notin 0, 2) { $script:Errors.Add("[$Id] rc $($script:LastRc) · " + (($o | Where-Object { $_ -match 'Error|Traceback|\[FAIL\]|RED' } | Select-Object -Last 2) -join ' | ')); Mark "$Id rc $($script:LastRc)" 'RED' }
  else { Mark "$Id rc $($script:LastRc) · ${dt}s" 'GREEN' }
  return $o }

# ---------- ④ 雙軌 / 多軌並行 + 進度條 ----------
function Invoke-VCDualLane {
  param([hashtable[]]$Lanes, [string]$LogDir)
  $MaxMin = if ($MaxMin) { [int]$MaxMin } else { 60 }; $jobs = [ordered]@{}
  foreach ($L in $Lanes) { $jobs[$L.id] = Start-ThreadJob -Name $L.id -ScriptBlock $L.run -ArgumentList $L.args; $script:LaneState[$L.id] = @{ zh = $L.zh; lamp = 'GRAY'; pct = 0; note = '' }; Mark ("車道啟動 " + $L.id + " · " + $L.zh) }
  $deadline = (Get-Date).AddMinutes($MaxMin); Write-VCBoxFrame $jobs.Count; $tick = 0
  while (($jobs.Values | Where-Object { $_.State -in 'NotStarted', 'Running' }).Count -gt 0) {
    if ((Get-Date) -gt $deadline) { foreach ($k in $jobs.Keys) { if ($jobs[$k].State -in 'NotStarted', 'Running') { Stop-Job $jobs[$k]; $script:Errors.Add("[逾時] 車道 $k 超過 $MaxMin 分,停") } }; break }
    $lines = @(); $sum = 0; $tick++
    foreach ($k in $jobs.Keys) { $pf = Join-Path $LogDir ($k + '.progress'); $raw = if (Test-Path $pf) { Get-Content $pf -Raw -ErrorAction SilentlyContinue } else { '' }
      $running = $jobs[$k].State -in 'NotStarted', 'Running'; $pct = if (-not $running) { 100 } elseif ($raw -match '^\s*(\d{1,3})') { [int]$Matches[1] } else { 0 }; $txt = if ($raw -match '·\s*(.+)$') { $Matches[1].Trim() } else { '' }
      $script:LaneState[$k].pct = $pct; $script:LaneState[$k].note = $txt; $sum += [Math]::Min(100, $pct)
      $lines += @{ name = "$k $($script:LaneState[$k].zh)"; pct = $pct; lamp = $(if ($running) { 'YELLOW' } else { 'GREEN' }); status = $(if ($running) { @('執行中', '執行中.', '執行中..')[$tick % 3] } else { '完成' }); detail = $txt } }
    Update-VCBox $lines; Write-Progress -Activity '並行' -Status ("$([int]($sum / [Math]::Max(1, $jobs.Count)))%") -PercentComplete ([int]($sum / [Math]::Max(1, $jobs.Count))); Start-Sleep -Milliseconds 800 }
  Write-Progress -Activity '並行' -Completed
  foreach ($k in $jobs.Keys) { $out = @(Receive-Job $jobs[$k] -Wait 2>&1 | ForEach-Object { "" + $_ }); $out | Set-Content (Join-Path $LogDir ($k + '.log')) -Encoding UTF8
    $bad = @($out | Where-Object { $_ -notmatch '^\s*\[(OK|計|注|YEL|GRAY)\]' -and $_ -match '^\s*(Traceback|\[FAIL\]|\[RED\])|rc (?!0\b)\d+' }); $good = @($out | Where-Object { $_ -match '\[(OK|GREEN|計)\]|總判|PASS' })
    if ($out.Count -eq 0) { $script:Errors.Add("[$k] 車道零輸出(State $($jobs[$k].State))") }
    if ($bad.Count) { $bad | Select-Object -First 4 | ForEach-Object { $script:Errors.Add("[$k] " + $_.Trim().Substring(0, [Math]::Min(160, $_.Trim().Length))) } }
    $good | Select-Object -Last 3 | ForEach-Object { $script:Verdicts.Add("[$k] " + $_.Trim().Substring(0, [Math]::Min(160, $_.Trim().Length))) }
    $script:LaneState[$k].lamp = if ($bad.Count -or $out.Count -eq 0) { 'RED' } elseif ($good.Count) { 'GREEN' } else { 'YELLOW' }; $script:LaneState[$k].pct = 100; Mark ("車道 $k 完 · " + $script:LaneState[$k].lamp) $script:LaneState[$k].lamp
    Remove-Job $jobs[$k] -Force -ErrorAction SilentlyContinue }
  $final = @(); foreach ($k in $jobs.Keys) { $L = $script:LaneState[$k]; $final += @{ name = "$k $($L.zh)"; pct = 100; lamp = $L.lamp; status = @{ GREEN = '過'; YELLOW = '要人裁'; RED = '紅' }[$L.lamp]; detail = $(if ($L.lamp -eq 'RED') { ($script:Errors | Where-Object { $_ -like "[$k]*" } | Select-Object -First 1) } else { $L.note }) } }
  Update-VCBox $final }

# ---------- ⑦ 靜態 HTML U/I(直接跳出,不經伺服器) ----------
function Write-VCHtml([string]$Title, [string]$LogDir) {
  $e = { param($s) [Net.WebUtility]::HtmlEncode("$s") }; $overall = if ($script:Errors.Count) { 'RED' } elseif (($script:LaneState.Values | Where-Object { $_.lamp -eq 'YELLOW' }).Count) { 'YELLOW' } else { 'GREEN' }
  $css = "@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}:root{--g:$($script:PAL.GREEN);--y:$($script:PAL.YELLOW);--r:$($script:PAL.RED);--k:$($script:PAL.GRAY);--n:$($script:PAL.NODATA);--border:#e5e7eb;--muted:#6b7280;--fs:11px}*{box-sizing:border-box}body{margin:0;font:var(--fs)/1.35 Arial,'Microsoft JhengHei',sans-serif;background:#f6f7f9;color:#111827}.top{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--border);padding:6px 10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}.top b{font-size:13px}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:8px;padding:8px}.card{background:#fff;border:1px solid var(--border);border-radius:6px;padding:7px 9px;min-width:0}.card h3{margin:0 0 4px;font-size:11px;color:var(--muted)}.c3{grid-column:span 3}.c6{grid-column:span 6}.c12{grid-column:span 12}.lamp{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.12)}.lamp.GREEN{background:var(--g)}.lamp.YELLOW{background:var(--y)}.lamp.RED{background:var(--r);animation:via-blink 1.8s ease-in-out infinite}.lamp.GRAY{background:var(--k)}.lamp.NODATA{background:var(--n)}.bar{height:8px;background:#eee;border-radius:4px;overflow:hidden}.bar i{display:block;height:100%;background:var(--g)}.y{color:#92400e}.r{color:#b91c1c}pre{white-space:pre-wrap;margin:0;font:11px Consolas,monospace}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--border);padding:2px 6px;text-align:left}th{background:#f3f4f6}@media (prefers-reduced-motion:reduce){.lamp.RED{animation:none}}@media (max-width:720px){.grid{grid-template-columns:1fr;padding:6px}.c3,.c6,.c12{grid-column:span 1}body{font-size:12px}}"
  $h = [Text.StringBuilder]::new(); [void]$h.Append("<!doctype html><html lang='zh-TW'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'><title>$(& $e $Title)</title><style>$css</style></head><body><div class='top'><b>$(& $e $Title)</b><span><i class='lamp $overall'></i>$overall</span><span style='color:var(--muted)'>$($script:Stamp) · 靜態頁 · 零伺服器 · 色 = VIA_UI_FormatLock</span></div><div class='grid'>")
  [void]$h.Append("<div class='card c3'><h3>車道</h3>"); foreach ($k in $script:LaneState.Keys) { $L = $script:LaneState[$k]; [void]$h.Append("<div><i class='lamp $($L.lamp)'></i><b>$(& $e $k)</b> $(& $e $L.zh)</div><div class='bar'><i style='width:$($L.pct)%'></i></div><div style='color:var(--muted)'>$(& $e $L.note)</div>") }; [void]$h.Append("</div>")
  [void]$h.Append("<div class='card c3'><h3>錯誤 $($script:Errors.Count)</h3>"); foreach ($x in $script:Errors) { [void]$h.Append("<div class='r'><i class='lamp RED'></i>$(& $e $x)</div>") }; if (-not $script:Errors.Count) { [void]$h.Append("<div><i class='lamp GREEN'></i>0 件</div>") }; [void]$h.Append("</div>")
  [void]$h.Append("<div class='card c6'><h3>時間軸</h3><table><tr><th>時刻</th><th>燈</th><th>事件</th></tr>"); foreach ($t in $script:Timeline) { [void]$h.Append("<tr><td>$($t.at)</td><td><i class='lamp $($t.lamp)'></i></td><td>$(& $e $t.what)</td></tr>") }; [void]$h.Append("</table></div>")
  [void]$h.Append("<div class='card c12'><h3>黃字(貼給 AI)</h3><pre class='y'>"); foreach ($v in $script:Verdicts) { [void]$h.Append((& $e $v) + "`n") }; [void]$h.Append("NEXT: " + $(if ($script:Errors.Count) { '把紅字整段貼給 AI' } else { '全綠 → 鎖 LKGC · 下一輪' }) + "</pre></div></div></body></html>")
  $p = Join-Path $LogDir 'VC_UI.html'; [IO.File]::WriteAllText($p, $h.ToString(), [Text.UTF8Encoding]::new($false)); Copy-Item $p "$VIA\VIA_Reports\review\VC_UI_latest.html" -Force -ErrorAction SilentlyContinue; $p }

# ---------- ⑥ 收尾:黃字 · 紅字 · 剪貼簿 · 開頁 ----------
function Show-VCSummary {
  param([string]$Title, [string]$LogDir)
  $y = "`e[93m"; $r = "`e[91m"; $g = "`e[92m"; $d = "`e[90m"; $z = "`e[0m"; $b = "`e[1m"
  Write-Host ""; Write-Host ("$b══════ $Title · $($script:Stamp) ══════$z")
  $gq = $script:C.Grey; $zz = $script:C.Reset   # 收尾矩陣:項目 │ 狀態 │ 關鍵點 │ 細節(Pad-Visual 中文對齊)
  Write-Host "${gq}┌──────────────────────┬──────────────┬──────────────────────────────┬────────────────────────────────────────┐$zz"
  Write-Host "${gq}│$zz " + (Pad-Visual '項目' 20) + " ${gq}│$zz " + (Pad-Visual '狀態' 12) + " ${gq}│$zz " + (Pad-Visual '關鍵點' 28) + " ${gq}│$zz " + (Pad-Visual '細節' 38) + " ${gq}│$zz"
  Write-Host "${gq}├──────────────────────┼──────────────┼──────────────────────────────┼────────────────────────────────────────┤$zz"
  foreach ($k in $script:LaneState.Keys) { $L = $script:LaneState[$k]; $col = switch ($L.lamp) { 'RED' { $r } 'YELLOW' { $y } 'GREEN' { $g } default { $d } }
    $key = ($script:Errors | Where-Object { $_ -like "[$k]*" } | Select-Object -First 1); if (-not $key) { $key = ($script:Verdicts | Where-Object { $_ -like "[$k]*" } | Select-Object -Last 1) }
    Write-Host "${gq}│$zz " + (Pad-Visual "$k $($L.zh)" 20) + " ${gq}│$zz " + (Pad-Visual ("$col[" + @{ GREEN = '完全通過'; YELLOW = '要人裁'; RED = '尚未修復' }[$L.lamp] + "]$z") 12) + " ${gq}│$zz " + (Pad-Visual ("$col" + ("$key" -replace "^\[$k\]\s*", '') + "$z") 28) + " ${gq}│$zz " + (Pad-Visual "$($L.note)" 38) + " ${gq}│$zz" }
  Write-Host "${gq}│$zz " + (Pad-Visual '錯誤合計' 20) + " ${gq}│$zz " + (Pad-Visual $(if ($script:Errors.Count) { "$r[$($script:Errors.Count) 件]$z" } else { "$g[0 件]$z" }) 12) + " ${gq}│$zz " + (Pad-Visual $(if ($script:Errors.Count) { "$r$($script:Errors[0])$z" } else { "$g全綠$z" }) 28) + " ${gq}│$zz " + (Pad-Visual $(if ($script:Errors.Count) { '把紅字整段貼給 AI' } else { '鎖 LKGC · 下一輪' }) 38) + " ${gq}│$zz"
  Write-Host "${gq}└──────────────────────┴──────────────┴──────────────────────────────┴────────────────────────────────────────┘$zz"
  foreach ($v in $script:Verdicts) { Write-Host ("$y$v$z") }
  if ($script:Errors.Count) { Write-Host ("$r$b── 錯誤 $($script:Errors.Count) 件 ──$z"); foreach ($x in $script:Errors) { Write-Host ("$r$x$z") } } else { Write-Host ("$g── 錯誤 0 件 ──$z") }
  $pack = @("# $Title $($script:Stamp)") + ($script:Verdicts | ForEach-Object { "- " + $_ }) + @("## 錯誤") + ($script:Errors | ForEach-Object { "- " + $_ }) + @("NEXT: " + $(if ($script:Errors.Count) { '把紅字整段貼給 AI' } else { '全綠 → 鎖 LKGC · 下一輪' }))
  $pack | Set-Content (Join-Path $LogDir 'paste.md') -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
  $html = Write-VCHtml $Title $LogDir; Write-Host ("$d" + "log $LogDir · 黃字 = 貼給 AI · 紅字 = 錯誤 · U/I $html$z")
  if (-not $NoOpen) { try { Start-Process $html } catch { } }
  if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 | Out-Null } catch { } }
  if ($script:AccelLoaded -and (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue)) { try { Restore-CeleritasPS7 | Out-Null } catch { } }   # 關閉即還原(加速器安全契約)
  if ($Run -and (Test-Path (Join-Path $Run 'RUNNING'))) { Remove-Item (Join-Path $Run 'RUNNING') -Force -ErrorAction SilentlyContinue }   # L115:跑完解除鎖,夾留到滾動期滿
  if ($script:EnvBackup) { foreach ($k in $script:EnvBackup.Keys) { $v = $script:EnvBackup[$k]; if ($null -eq $v -or $v -eq '') { Remove-Item "Env:$k" -ErrorAction SilentlyContinue } else { Set-Item "Env:$k" $v } } }   # v0109:退出還原環境變數(含 VIA_FROM_VCGC,不留後門給之後的指令繞閘)
  $script:Verdicts.Add("[還原] 環境變數與加速器已還原;本支只寫 VIA_Reports\review\ps_<時戳>\ 與 VC_UI_latest.html") }

# ======================= 骨架主體(高風險測試前:① 三系統健康還原點(零紅才鎖)+ git tag ② VRN 自報齊全度(ssot diff · panorama)③ VRN extract 掃測試夾 ④ VDF quote 抓行情 ⑤ 交接包隔離解壓(不覆蓋正式樹);PS 只落地 / 啟動 / 開頁)=======================
# Invoke-VIA-RealTest-v0101.ps1(薄尾:C 段前先 lexicon add 第三批 18 條 + 噪音規則 · 代號濾 09xx · VRN v0149;v0100 不動)(RiskTest 薄尾:C 段改 VRN extract loop — 掃 → triage → 字典安全自動採納 → 只重掃 REVIEW → 完工門檻;G 段三系統完工判定)· 操作員令 2026-10-08:用 VCGC 省 token 工具把 VRN / VDF 實測落地完工 · 原令 2026-10-07:三系統建健康還原點 → VRN 完全獨立做高風險測試:全景檢 VRN 資訊齊全 → 掃 C:\測試樣本報告 → VDF 抓需要的資料 → v0108 年度財報交接包獨立試跑
if (-not $NoCleanup) { Invoke-VCSafeCleanup }
$Run = Initialize-VCTemp; Initialize-VCAccel
$script:LogDir = Join-Path $VIA ("VIA_Reports\review\ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null; $LogDir = $script:LogDir
$RegDir = Join-Path $VIA 'supportive modules\registry'; $VrnDir = Join-Path $VIA 'functional modules\VRN'; $VdfDir = Join-Path $VIA 'functional modules\VDF'
function Install-VIAEmbedded([string]$Path, [string]$B64, [string]$Want, [string]$Tag) {   # 只增不減:不在=寫;在且同 hash=SKIP;異 hash=紅不覆寫
  try {
    $Bytes = [Convert]::FromBase64String(($B64 -replace '\s', '')); $Got = ([BitConverter]::ToString([Security.Cryptography.SHA256]::HashData($Bytes)) -replace '-', '').ToLower()
    if ($Got -ne $Want) { $script:Errors.Add("[落地] $Tag 內嵌 hash 不符(貼文被截?)期望 $($Want.Substring(0, 12)) 實得 $($Got.Substring(0, 12))"); return $false }
    $Dir = [IO.Path]::GetDirectoryName($Path); if (-not (Test-Path -LiteralPath $Dir)) { $script:Errors.Add("[落地] $Tag 目標夾不在:$Dir"); return $false }
    if (Test-Path -LiteralPath $Path) { $Have = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower()
      if ($Have -eq $Want) { $script:Verdicts.Add("[落地] $Tag 已在且 hash 同 → SKIP"); Mark "$Tag 已在" 'GREEN'; return $true }
      $script:Errors.Add("[落地] $Path 已在但 hash 不同 → 不覆寫(只增不減);要換請出新版號"); return $false }
    [IO.File]::WriteAllBytes($Path, $Bytes); $script:Verdicts.Add("[落地] 寫入 $Path · $($Bytes.Length) bytes · sha256 $($Want.Substring(0, 12))"); Mark "$Tag 落地" 'GREEN'; return $true
  } catch { $script:Errors.Add("[落地] $Tag " + $_.Exception.Message.Split([char]10)[0]); return $false } }
function Install-VIATail([string]$Dir, [string]$Stem, [string]$Ver, [string]$B64, [string]$Sha, [string]$Tag) {   # 尾版閘:高於本版不落;低於前一版要先補
  $t = Get-ChildItem -LiteralPath $Dir -Filter ($Stem + '_v*.py') -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  $me = $Stem + '_' + $Ver + '.py'
  if ($t -and $t.Name -gt $me) { $script:Errors.Add("[落地] 樹上已有 $($t.Name) 高於 $Ver → $Tag 不落地"); return $false }
  return (Install-VIAEmbedded -Path (Join-Path $Dir $me) -B64 $B64 -Want $Sha -Tag $Tag) }
$B64Hm = @'
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJDR0MgSGVhbHRoTWF0cml4IHYwMTA4IOKAlCh2MDEwODorcmVzdG9y
ZXBvaW50IG1ha2UvbGlzdCA9IOS4ieezu+e1seWBpeW6t+mChOWOn+m7njrlhYjoroDkuInns7vntbHoh6rloLEgSEVBTFRIKOmbtue0heaJjeWHhikrIFZE
Ri9WUk4gY2hhaW4gKyBnb3Zlcm4g4oaSIOaJk+WMhSBmdW5jdGlvbmFsIG1vZHVsZXMvVlJOwrdWREYgKyBzdXBwb3J0aXZlIG1vZHVsZXMvcmVnaXN0cnkg
KyDkuInku70gSEVBTFRIL+a4heWWriDliLAgVklBX1Jlc3RvcmUvcnBfPHN0YW1wPi56aXAo5pys5qmfLOS4jemAsuWAiSkrIOW4syBWSUFfUmVzdG9yZVBv
aW50X0xlZGdlcl92MDEwMC5qc29ubCh6aXAgc2hhMjU2IMK3IGdpdCBzaGEgwrcg54eIKTvpgoTljp/mjIfku6TljbDlh7os5LiN6Ieq5YuV6KaG6JOLOyh2
MDEwNzorcG9ydGFsID0g5LiA5YCLIFUvSSDpgKPkuInlgIsgU3lzdGVtTWFuYWdlcjroroDlkITlrZDns7vntbHoh6rloLHnmoQgPFNVQj5fVUlfTUFOSUZF
U1QuanNvbihWQ0dDIOiHquW3seS5n+Wvq+S4gOS7vSnihpIgVklBX1JlcG9ydHMvVklBX1VJX2xhdGVzdC5odG1sIOWFpeWPozrkuIrliJfkuInns7vntbHn
h4joiIfliIfmj5vpiJUo5ruR6bygKSzkuIvmlrnovInlhaXmiYDpgbjns7vntbHoh6rlt7HnmoTpoIE75riF5Zau6K6K6aCB5bCx6K6KLOaooeadv+i1sOWG
ijvmr43ns7vntbHkuI3lr6vlrZDns7vntbHpoIE7KHYwMTA2OkwxMTgg5ruR6byg5b6LIOKAlCBWQ0dDIHVpIOaMh+S7pOahhuaXgeWKoCB2aWE6Ly9WQ0dD
L2NvbmZpZy9zZXQg5Z+36KGM6YCj57WQOyh2MDEwNTordGhlbWUgaW5pdC9zaG93ID0g5pqr5pmC5qiZ5rqWIFUvSSDmqKHmnb/lhoogVklBX1VJX1RlbXBs
YXRlX1NTT1RfdjAxMDAodG9rZW4pO3VpL21hdHJpeCDovLjlh7rlpZcgdmFyKC0tdG9rZW4pIOiHqumBqeaHieaPm+aooeadvzvnh4jlm5voibLpjpblrpo7
KHYwMTA0Oitjb25maWco56iL5byP5qqU5qGI5aS+IMK3IOizh+aWmeW6q+ioreWumizlhoogVklBX0NvbmZpZ19TU09UX3YwMTAwLmpzb24pKyB1aSjlhanp
naLmnb865bemID0g5Y+q5pyJ56iL5byP5aS+6IiH6LOH5paZ5bqr5YWp57WE6Kit5a6aIOKGkiDntYTmjIfku6Q75Y+zID0g5YGl5bq355+p6ZmjIMK3IOeS
sOWigyDCtyDlt6Xlhbcgwrcg5rK755CGIMK3IOWFqOaqlCDpoIHnsaQpOyjlgaXlurfmrrUgdjAxMDI65Ymv5pys5qqU5pyA5aSa6buDOyjlkIzmraXlgaXl
urfmrrXljbDlh7rmoLzlvI/kv67mraM7KOWBpeW6t+autSB2MDEwMTrntrLmqYvopoHmnInniYjomZ/mlrDniYg75YW26aSY5ZCMIHYwMTAwKSDkuInns7vn
tbHlgaXlurfnn6npmaPloLHlkYoo5pON5L2c5ZOh5LukIDIwMjYtMTAtMDY6VkNHQy9WUk4vVkRGIOWIl+euoeeahOW8leaTjiDCtyDlip/og70gwrcg5Y+D
5pW4IMK3IFNTT1Qg5YWo5o6M5o+hO+a3uuiJsiDCtyDnt4rmuYogwrcg6Ieq5YuV5pyA5L2z5YyW54mI6Z2iIMK3IOiHqumBqeaHieefqemZozvntIXpu4Pn
tqDnh4jnrKzkuIDmrIQ7CueUqOePvuacieW8leaTjiznnIEgdG9rZW4g5YWo5pmv5o6DOuacieeEoee3qOiZnyDCtyDmnInnhKHniYjmnKzomZ8gwrcg5pyJ
54Sh6Ki75YaKIMK3IOacieeEoeWKoOmAn+WZqCDCtyDmnInnhKHntrLot6/lt6Xlhbcgwrcg54mI5pys6Kqe5oSPIMK3IOato+W4uOmBi+S9nCDCtyDmoYjl
oLTliIbpoZ475ZCEIHN5c3RlbSBtYW5hZ2VyIOiHqueuoeWQqyBsaWIv55Kw5aKDKeOAggogIG1hdHJpeCAgICAgICAgICAgIOKRoCDoh6rlt7EoVkNHQyA9
IHN1cHBvcnRpdmUgbW9kdWxlcynot5HlgaXlurfmrrUg4oaSIFZJQV9SZXBvcnRzL3ZjZ2MvSEVBTFRIX2xhdGVzdC5qc29uO+KRoSDoroAgVklBX1JlcG9y
dHMvdnJufHZkZi9IRUFMVEhfbGF0ZXN0Lmpzb24o5ZCE6IeqIG1hbmFnZXIgaGVhbHRoIOWLleipnuWvq+eahCzmr43ns7vntbHlj6roroApOwogICAgICAg
ICAgICAgICAgICAgIOKRoiDkvbXml6LmnInlvJXmk47mnIDmlrDntZDmnpw6UEFOT1JBTUEoSzHigJNLOCnCtyBFTlZfTUFUUklYIMK3IFRPT0xLSVRfTUFU
UklYIMK3IEdPVkVSTiDCtyBWUk5fRXh0cmFjdF9MZWRnZXIgwrcgRklMRV9NQVRSSVgo5pyJ5bCx5L21LOaykuacieeBsCk74pGjIOWHuiBIRUFMVEhfTUFU
UklYX2xhdGVzdC5odG1sLy5qc29uICsg5Y2hICsg6LK85Zue5YyFCiAgLS1zZWxmdGVzdCAgICAgICAgdGVtcCDmspnnm5IK5Y+q5a+rIFZJQV9SZXBvcnRz
L3ZjZ2MvIMK3IFZJQV9SZXBvcnRzL3Jldmlldy92Y2djX2hlYWx0aC8gwrcgZG9jcy9oYW5kb2ZmL2FpL+OAguaymeebkumNtTpWSUFfUk9PVAoiIiIKZnJv
bSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwoKIyA9PT09PSBbVklBOkFDQ0VMLUJSSURHRTp2MDEwMF0gU3VwZXJBY2NlbCDliqDpgJ/lmajmqYso
5om5MTAyIOWFqOaoueWwjuWFpeS7pDtncmFjZWZ1bCDpm7booYzngrrorormm7QpID09PT09CnRyeToKICAgIGltcG9ydCBzeXMgYXMgX3NhX3N5cwogICAg
ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9zYV9QYXRoCiAgICBfc2FfcCA9IF9zYV9QYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkKICAgIHdoaWxlIF9z
YV9wLnBhcmVudCAhPSBfc2FfcDoKICAgICAgICBpZiAoX3NhX3AgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIiAvICJWSUFfU3VwZXJBY2NlbF9Nb2R1bGUucHki
KS5leGlzdHMoKToKICAgICAgICAgICAgX3NhX3N5cy5wYXRoLmluc2VydCgwLCBzdHIoX3NhX3AgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIikpCiAgICAgICAg
ICAgIGJyZWFrCiAgICAgICAgX3NhX3AgPSBfc2FfcC5wYXJlbnQKICAgIGltcG9ydCBWSUFfU3VwZXJBY2NlbF9Nb2R1bGUgYXMgVklBX0FDQ0VMICAjIG5v
cWE6IEY0MDEKZXhjZXB0IEltcG9ydEVycm9yOgogICAgVklBX0FDQ0VMID0gTm9uZQojID09PT09IFtWSUE6QUNDRUwtQlJJREdFOkVORF0gPT09PT0KCmlt
cG9ydCBkYXRldGltZQppbXBvcnQgaHRtbAppbXBvcnQganNvbgppbXBvcnQgb3MKaW1wb3J0IHJlCmltcG9ydCBzaHV0aWwKaW1wb3J0IHN5cwppbXBvcnQg
dGVtcGZpbGUKaW1wb3J0IHRpbWUKZnJvbSBjb2xsZWN0aW9ucyBpbXBvcnQgQ291bnRlcgpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCk1FID0gUGF0aChf
X2ZpbGVfXykucmVzb2x2ZSgpCk5BTUUgPSBNRS5zdGVtClRBRyA9ICJ2MDEwOCIKTEFNUCA9IHsiR1JFRU4iOiAiIzE2YTM0YSIsICJZRUxMT1ciOiAiI2Y1
OWUwYiIsICJSRUQiOiAiI2RjMjYyNiIsICJHUkFZIjogIiM5Y2EzYWYifQpTVUJTID0gKCJWQ0dDIiwgIlZERiIsICJWUk4iKQoKIyA9PT09PSBbVklBOlNN
LUhFQUxUSDp2MDEwMl0g5a2Q57O757Wx5YGl5bq35q61KHYwMTAyOuWJr+acrOaqlOacgOWkmum7gykodjAxMDE657ay5qmL6KaB44CM5pyJ54mI6Jmf55qE
5paw54mI44CNU1VQX01ETDc0MF9OZXRVbmlmaWVkX3YjIyMjL3ZpYV9uZXRfdW5pZmllZF92IyMjIy9bVklBOk5FVC1CUklER0U6diMjIyNdO+eEoeeJiOiZ
n+iIiuapiz3pu4M757ay6Lev5bel5YW35pys6auU6IiH5Yqg6YCf5Zmo5pys6auU6LGB5YWNO+WJr+acrOaqlOWQjSAoMSkvX3NoYSDmqJkgRE9STUFOVCDl
gJnpgbg75bCN5biz5pS56Jmf6YCg5oiQ55qE54mI6Jmf5rSe5LiN55W26Kqe5oSP6YyvKSjlkIQgU3lzdGVtTWFuYWdlciDoh6rnrqHoh6rloLE65Yqf6IO9
55+p6ZmjIMK3IOihqOmgreWGiiDCtyDnt6jomZ8gwrcg54mI5pys6Kqe5oSPIMK3IOWKoOmAn+WZqCDCtyDntrLmqYsgwrcgbGliL+eSsOWigyDCtyDmnIDo
v5Hoh6rmuKw75Y+q6K6ALOWvq+iHquW3seeahCBIRUFMVEhfbGF0ZXN0Lmpzb24pPT09PT0KZGVmIF9obF92bnVtKG5hbWUpOgogICAgaW1wb3J0IHJlIGFz
IF9yZQogICAgbSA9IF9yZS5zZWFyY2gociJfdihcZHsyLDR9KVtBLVphLXowLTldKig/OlwuW0EtWmEtejAtOV0rKT8kIiwgbmFtZSkKICAgIHJldHVybiBp
bnQobS5ncm91cCgxKSkgaWYgbSBlbHNlIC0xCgoKZGVmIF9obF9yZWFkX2pzb24ocCk6CiAgICBpbXBvcnQganNvbiBhcyBfanNvbgogICAgdHJ5OgogICAg
ICAgIHJldHVybiBfanNvbi5sb2FkcyhwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpCiAgICBleGNlcHQgRXhjZXB0aW9uOiAgIyBub3FhOiBC
TEUwMDEKICAgICAgICByZXR1cm4gTm9uZQoKCmRlZiBfaGxfdGFpbChkLCBwYXQpOgogICAgaGl0cyA9IHNvcnRlZChkLmdsb2IocGF0KSwga2V5PWxhbWJk
YSBxOiBfaGxfdm51bShxLm5hbWUpKSBpZiBkLmlzX2RpcigpIGVsc2UgW10KICAgIHJldHVybiBoaXRzWy0xXSBpZiBoaXRzIGVsc2UgTm9uZQoKCmRlZiBz
bV9oZWFsdGgoc3ViLCBob21lLCByb290LCBvdXRfZGlyLCBub3csIHJlcXVpcmVkX2xpYnM9KCksIG5ldF9yZXF1aXJlZD1GYWxzZSk6CiAgICAiIiLihpIg
ZGljdCjlgaXlurfnn6npmaPnmoTlrZDns7vntbHmrrUp44CCaG9tZSA9IGZ1bmN0aW9uYWwgbW9kdWxlcy88U1VCPjtvdXRfZGlyID0gVklBX1JlcG9ydHMv
PHN1Yj4v44CCIiIiCiAgICBpbXBvcnQgaW1wb3J0bGliLnV0aWwgYXMgX2lsdQogICAgaW1wb3J0IHJlIGFzIF9yZQogICAgaW1wb3J0IHN5cyBhcyBfc3lz
CiAgICBpbXBvcnQganNvbiBhcyBfanNvbgogICAgZnJvbSBjb2xsZWN0aW9ucyBpbXBvcnQgZGVmYXVsdGRpY3QgYXMgX2RkCiAgICBmcm9tIHBhdGhsaWIg
aW1wb3J0IFBhdGggYXMgX1AKICAgIHJlZyA9IGhvbWUgLyAicmVnaXN0cnkiCiAgICBmbSA9IF9obF9yZWFkX2pzb24oX2hsX3RhaWwocmVnLCBzdWIgKyAi
X0Z1bmN0aW9uTWF0cml4X3YqLmpzb24iKSkgaWYgcmVnLmlzX2RpcigpIGVsc2UgTm9uZQogICAgdGggPSBfaGxfcmVhZF9qc29uKF9obF90YWlsKHJlZywg
c3ViICsgIl9UYWJsZUhlYWRlcl92Ki5qc29uIikpIGlmIHJlZy5pc19kaXIoKSBlbHNlIE5vbmUKICAgIG5iID0ge30KICAgIGNlbnRyYWwgPSByb290IC8g
InN1cHBvcnRpdmUgbW9kdWxlcyIgLyAicmVnaXN0cnkiCiAgICBmb3IgcCBpbiAoY2VudHJhbCAvICJWSUFfTnVtYmVyQm9va3MiKS5nbG9iKCJWSUFfTnVt
YmVyQm9va18qX3YqLmpzb25sIikgaWYgKGNlbnRyYWwgLyAiVklBX051bWJlckJvb2tzIikuaXNfZGlyKCkgZWxzZSBbXToKICAgICAgICB0cnk6CiAgICAg
ICAgICAgIGZvciBsbiBpbiBwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikuc3BsaXRsaW5lcygpOgogICAgICAgICAgICAgICAgciA9IF9qc29u
LmxvYWRzKGxuKQogICAgICAgICAgICAgICAgaWYgci5nZXQoInNvdXJjZSIpIGFuZCByLmdldCgiY29kZSIpOgogICAgICAgICAgICAgICAgICAgIG5iW3Jb
InNvdXJjZSJdLnJlcGxhY2UoIlxcIiwgIi8iKV0gPSByWyJjb2RlIl0KICAgICAgICBleGNlcHQgRXhjZXB0aW9uOiAgIyBub3FhOiBCTEUwMDEKICAgICAg
ICAgICAgcGFzcwogICAgcm4gPSBfaGxfcmVhZF9qc29uKGNlbnRyYWwgLyAiVklBX1JlZ2lzdHJ5TnVtYmVyc192MDEwMC5qc29uIikgaWYgKGNlbnRyYWwg
LyAiVklBX1JlZ2lzdHJ5TnVtYmVyc192MDEwMC5qc29uIikuZXhpc3RzKCkgZWxzZSBOb25lCiAgICBybl9rZXlzID0ge2VbImtleSJdOiBlWyJjb2RlIl0g
Zm9yIGUgaW4gKHJuIG9yIHt9KS5nZXQoImVudHJpZXMiLCBbXSkgaWYgZS5nZXQoImtleSIpfQogICAgIyDmqpTmoYjliJc65q+P5pePKOWOu+eJiOiZnynk
uIDliJcKICAgIGZhbXMgPSBfZGQobGlzdCkKICAgIGZvciBwIGluIGhvbWUucmdsb2IoIioucHkiKToKICAgICAgICBpZiBzZXQocC5yZWxhdGl2ZV90byho
b21lKS5wYXJ0c1s6LTFdKSAmIHsicmVmZXJlbmNlcyIsICJpbnRha2UiLCAiX3N1cGVyc2VkZWQiLCAiX19weWNhY2hlX18iLCAiVklBX1JldGlyZWRFbmdp
bmVzIiwgIl9xdWFyYW50aW5lIn06CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZmFtc1socC5wYXJlbnQsIF9yZS5zdWIociJfdlxkezIsNH1bQS1a
YS16MC05XSokIiwgIiIsIHAuc3RlbSkpXS5hcHBlbmQocCkKICAgIHJvd3MgPSBbXQogICAgc2VtX2lzc3VlcyA9IDAKICAgIGNvbGxpc2lvbl9mYW1zID0g
c2V0KCkKICAgIGNsID0gcm9vdCAvICJWSUFfUmVwb3J0cyIgLyAicmV2aWV3IiAvICJ2Y2djX2NvbGxpc2lvbiIgLyAiQ09MTElTSU9OX2xlZGdlci5qc29u
bCIKICAgIGlmIGNsLmV4aXN0cygpOgogICAgICAgIGZvciBsbiBpbiBjbC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04LXNpZyIsIGVycm9ycz0icmVwbGFj
ZSIpLnNwbGl0bGluZXMoKToKICAgICAgICAgICAgbSA9IF9yZS5zZWFyY2gociIoW0EtWmEtejAtOV0rX1N5c3RlbU1hbmFnZXJ8Q0dDX01ETFxkezN9X1tB
LVphLXowLTldKykiLCBsbikKICAgICAgICAgICAgaWYgbToKICAgICAgICAgICAgICAgIGNvbGxpc2lvbl9mYW1zLmFkZChfcmUuc3ViKHIiX3ZcZHs0fSQi
LCAiIiwgbS5ncm91cCgxKSkpCiAgICBmb3IgKGQsIGZhbSksIHBzIGluIHNvcnRlZChmYW1zLml0ZW1zKCksIGtleT1sYW1iZGEgeDogKHN0cih4WzBdWzBd
KSwgeFswXVsxXSkpOgogICAgICAgIHBzLnNvcnQoa2V5PWxhbWJkYSBxOiAoX2hsX3ZudW0ocS5uYW1lKSwgcS5uYW1lKSkKICAgICAgICB0YWlsID0gcHNb
LTFdCiAgICAgICAgdmVycyA9IFtfaGxfdm51bShxLm5hbWUpIGZvciBxIGluIHBzIGlmIF9obF92bnVtKHEubmFtZSkgPj0gMF0KICAgICAgICB0cnk6CiAg
ICAgICAgICAgIHR4dCA9IHRhaWwucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciLCBlcnJvcnM9InJlcGxhY2UiKQogICAgICAgIGV4Y2VwdCBPU0Vy
cm9yOgogICAgICAgICAgICB0eHQgPSAiIgogICAgICAgIGJvZHkgPSB0eHQuc3BsaXQoIlxuZGVmIHNlbGZ0ZXN0KCIpWzBdCiAgICAgICAgYWNjZWwgPSAi
W1ZJQTpBQ0NFTC1CUklER0UiIGluIHR4dCBvciAiVmVyaXRhc0NlbGVyaXRhc192MTE0MSIgaW4gdHh0CiAgICAgICAgbmV0X3VzZSA9IGJvb2woX3JlLnNl
YXJjaChyIl5ccyooPzppbXBvcnR8ZnJvbSlccysocmVxdWVzdHN8aHR0cHh8YWlvaHR0cHx1cmxsaWJcLnJlcXVlc3R8eWZpbmFuY2V8YWtzaGFyZXxmcmVk
YXBpfHBhbmRhc19kYXRhcmVhZGVyKVxiIiwgYm9keSwgX3JlLk0pKSAgICMg6KaB55yf55qEIGltcG9ydCDmiY3nrpflh7rntrIo5q2j5YmH5a2X5Liy6KOh
55qE5a2X5LiN566XKQogICAgICAgIGlzX25ldF90b29sID0gYm9vbChfcmUuc2VhcmNoKHIiKD9pKU5ldFVuaWZpZWR8QWVnaXNOZXh1c3x2aWFfbmV0X3Vu
aWZpZWR8VklBX05ldFN1cHBvcnR8dmlhX2FlZ2lzX25ldGNvcmV8XihyZXF1ZXN0fHByb3h5fGNvbGxlY3Rvcnx1cmxzfGdpdCkkIiwgZmFtKSkgb3IgIm5l
dHdvcmsiIGluIGQucGFydHMgb3IgImFjY2VsZXJhdG9yIiBpbiBkLnBhcnRzIG9yIGZhbS5zdGFydHN3aXRoKCgiVmVyaXRhc0NlbGVyaXRhcyIsICJTVVBf
TURMNzM3IiwgIlZJQV9TdXBlckFjY2VsIiwgInBpcF9zdWJwcm9jZXNzIikpCiAgICAgICAgbmV0X25ldyA9IGJvb2woX3JlLnNlYXJjaChyIlNVUF9NREw3
NDBfTmV0VW5pZmllZF92XGR7NH18dmlhX25ldF91bmlmaWVkX3ZcZHs0fXxcW1ZJQTpORVQtQlJJREdFOnZcZHs0fVxdIiwgYm9keSkpCiAgICAgICAgbmV0
X29sZCA9IChub3QgbmV0X25ldykgYW5kIGJvb2woX3JlLnNlYXJjaChyIlxbVklBOk5FVC1CUklER0V8VklBX05ldFN1cHBvcnRcYnx2aWFfbmV0X3VuaWZp
ZWRcYnxTVVBfTURMNzQwIiwgYm9keSkpCiAgICAgICAgbmV0X29rID0gKG5vdCBuZXRfdXNlKSBvciBpc19uZXRfdG9vbCBvciBuZXRfbmV3IG9yIG5ldF9v
bGQgICAgICAjIOiIiuapi+S4jee0hSjpu4MpLOaykuapi+aJjee0hQogICAgICAgIG5ldF9ub3RlID0gIiIgaWYgKG5vdCBuZXRfdXNlIG9yIGlzX25ldF90
b29sKSBlbHNlICgi5paw54mI57ay5qmLIiBpZiBuZXRfbmV3IGVsc2UgKCLoiIrniYjntrLmqYso54Sh54mI6JmfKeKGkiDmlLnmjqUgU1VQX01ETDc0MF9O
ZXRVbmlmaWVkX3YjIyMjIiBpZiBuZXRfb2xkIGVsc2UgIueEoee2suapiyIpKQogICAgICAgIGp1bmsgPSBib29sKF9yZS5zZWFyY2gociJcc1woXGQrXCkk
fF9zaGFbMC05YS1mXXs4LH0kIiwgdGFpbC5zdGVtKSkgb3IgIiAoMSkiIGluIHRhaWwubmFtZQogICAgICAgIHNlbSA9IFtdCiAgICAgICAgaWYganVuazoK
ICAgICAgICAgICAgc2VtLmFwcGVuZCgi5Ymv5pys5qqU5ZCNKCgxKS9fc2hhKeKGkiBET1JNQU5UIOWAmemBuCIpCiAgICAgICAgaWYgbGVuKHZlcnMpICE9
IGxlbihzZXQodmVycykpOgogICAgICAgICAgICBzZW0uYXBwZW5kKCLlkIzniYjomZ/ph43opIciKQogICAgICAgIGlmIHZlcnMgYW5kIG1heCh2ZXJzKSAt
IG1pbih2ZXJzKSArIDEgIT0gbGVuKHZlcnMpIGFuZCBsZW4odmVycykgPiAxOgogICAgICAgICAgICBzZW0uYXBwZW5kKCgi54mI6Jmf5rSePeWwjeW4s+aU
ueiZnyjlt7LoqJjluLMpIiBpZiBmYW0gaW4gY29sbGlzaW9uX2ZhbXMgZWxzZSAi54mI6Jmf5pyJ5rSeKCVk4oCTJWQg5YWxICVkKSIpICUgKChtaW4odmVy
cyksIG1heCh2ZXJzKSwgbGVuKHZlcnMpKSBpZiBmYW0gbm90IGluIGNvbGxpc2lvbl9mYW1zIGVsc2UgKCkpKQogICAgICAgIGlmIF9obF92bnVtKHRhaWwu
bmFtZSkgPCAwIGFuZCBsZW4ocHMpID4gMToKICAgICAgICAgICAgc2VtLmFwcGVuZCgi5bC+54mI54Sh54mI6JmfIikKICAgICAgICBzZW1faXNzdWVzICs9
IGJvb2woW3ggZm9yIHggaW4gc2VtIGlmICLlt7LoqJjluLMiIG5vdCBpbiB4XSkKICAgICAgICByZWwgPSB0YWlsLnJlbGF0aXZlX3RvKHJvb3QpLmFzX3Bv
c2l4KCkgaWYgc3RyKHRhaWwpLnN0YXJ0c3dpdGgoc3RyKHJvb3QpKSBlbHNlIHRhaWwuYXNfcG9zaXgoKQogICAgICAgIGtleV9tZGwgPSAiJXN8TURMfCVz
fCVzIiAlIChzdWIsIGZhbSwgKCJ2JTA0ZCIgJSBfaGxfdm51bSh0YWlsLm5hbWUpKSBpZiBfaGxfdm51bSh0YWlsLm5hbWUpID49IDAgZWxzZSAidjAwMDAi
KQogICAgICAgIGtleV9lbmcgPSBrZXlfbWRsLnJlcGxhY2UoInxNREx8IiwgInxFTkd8IikKICAgICAgICBjb2RlID0gbmIuZ2V0KHJlbCkgb3Igcm5fa2V5
cy5nZXQoa2V5X21kbCkgb3Igcm5fa2V5cy5nZXQoa2V5X2VuZykgb3IgIiIKICAgICAgICByZWdpc3RlcmVkID0gYm9vbChmbSBhbmQgYW55KGsuc3BsaXQo
InwiKVsxXSA9PSBmYW0gZm9yIGsgaW4gKGZtLmdldCgiaXRlbXMiKSBvciB7fSkgaWYgay5zdGFydHN3aXRoKCgiTURMfCIsICJFTkd8IikpKSkKICAgICAg
ICB0cnk6CiAgICAgICAgICAgIGltcG9ydCBhc3QgYXMgX2FzdAogICAgICAgICAgICBfYXN0LnBhcnNlKHR4dCkKICAgICAgICAgICAgYXN0X29rID0gVHJ1
ZQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246ICAjIG5vcWE6IEJMRTAwMQogICAgICAgICAgICBhc3Rfb2sgPSBGYWxzZQogICAgICAgIGxhbXAgPSAiUkVE
IiBpZiAoKG5vdCBhc3Rfb2sgb3Igbm90IG5ldF9vaykgYW5kIG5vdCBqdW5rKSBlbHNlICgiWUVMTE9XIiBpZiAoanVuayBvciBub3QgYWNjZWwgb3Igbm90
IGNvZGUgb3Igbm90IHJlZ2lzdGVyZWQgb3IgbmV0X29sZCBvciBbeCBmb3IgeCBpbiBzZW0gaWYgIuW3suiomOW4syIgbm90IGluIHhdKSBlbHNlICJHUkVF
TiIpICAgIyDlia/mnKzmqpQoanVuaynmnIDlpJrpu4M65a6D55qE5q245a6/5pivIGRvcm1hbnQs5LiN5piv5L+uCiAgICAgICAgcm93cy5hcHBlbmQoeyJm
YW1pbHkiOiBmYW0sICJkaXIiOiBkLnJlbGF0aXZlX3RvKGhvbWUpLmFzX3Bvc2l4KCkgaWYgc3RyKGQpLnN0YXJ0c3dpdGgoc3RyKGhvbWUpKSBlbHNlIHN0
cihkKSwgInRhaWwiOiB0YWlsLm5hbWUsICJ2ZXJzaW9uIjogKCJ2JTA0ZCIgJSBfaGxfdm51bSh0YWlsLm5hbWUpKSBpZiBfaGxfdm51bSh0YWlsLm5hbWUp
ID49IDAgZWxzZSAi4oCUIiwgIm5fdmVyc2lvbnMiOiBsZW4ocHMpLAogICAgICAgICAgICAgICAgICAgICAibnVtYmVyIjogY29kZSwgInJlZ2lzdGVyZWQi
OiByZWdpc3RlcmVkLCAiYWNjZWwiOiBhY2NlbCwgIm5ldF91c2UiOiBuZXRfdXNlLCAibmV0X29rIjogbmV0X29rLCAibmV0X25vdGUiOiBuZXRfbm90ZSwg
Im5ldF90b29sIjogaXNfbmV0X3Rvb2wsICJhc3Rfb2siOiBhc3Rfb2ssICJzZW1hbnRpYyI6ICI7Ii5qb2luKHNlbSksICJsYW1wIjogbGFtcH0pCiAgICAj
IOWGiiAvIOihqOmgrSAvIOWtl+WFuAogICAgYm9va3MgPSBbXQogICAgZm9yIHNkIGluICgiU1NPVCIsICJyZWdpc3RyeSIsICJrbm93bGVkZ2UiKToKICAg
ICAgICBkID0gaG9tZSAvIHNkCiAgICAgICAgaWYgZC5pc19kaXIoKToKICAgICAgICAgICAgc2VlbiA9IHt9CiAgICAgICAgICAgIGZvciBwIGluIGQuZ2xv
YigiKi5qc29uIik6CiAgICAgICAgICAgICAgICBmYW0gPSBfcmUuc3ViKHIiX3ZcZHsyLDR9W0EtWmEtejAtOV0qJCIsICIiLCBwLnN0ZW0pCiAgICAgICAg
ICAgICAgICBpZiBmYW0gbm90IGluIHNlZW4gb3IgX2hsX3ZudW0ocC5uYW1lKSA+IF9obF92bnVtKHNlZW5bZmFtXS5uYW1lKToKICAgICAgICAgICAgICAg
ICAgICBzZWVuW2ZhbV0gPSBwCiAgICAgICAgICAgIGZvciBmYW0sIHAgaW4gc2Vlbi5pdGVtcygpOgogICAgICAgICAgICAgICAgdGlkID0gX3JlLnN1Yihy
IlteYS16MC05X10rIiwgIl8iLCBmYW0ubG93ZXIoKSkuc3RyaXAoIl8iKQogICAgICAgICAgICAgICAgZW50ID0gKHRoIG9yIHt9KS5nZXQoInRhYmxlcyIs
IHt9KSBpZiB0aCBlbHNlIHt9CiAgICAgICAgICAgICAgICByZWdfdCA9IGFueShrID09IHRpZCBvciBrLnN0YXJ0c3dpdGgodGlkICsgIl8iKSBmb3IgayBp
biBlbnQpCiAgICAgICAgICAgICAgICBudW1fdCA9IGFueSgoayA9PSB0aWQgb3Igay5zdGFydHN3aXRoKHRpZCArICJfIikpIGFuZCB2LmdldCgidGFibGVf
bm8iKSBmb3IgaywgdiBpbiBlbnQuaXRlbXMoKSkKICAgICAgICAgICAgICAgIGJvb2tzLmFwcGVuZCh7ImJvb2siOiBwLm5hbWUsICJkaXIiOiBzZCwgInJl
Z2lzdGVyZWQiOiByZWdfdCwgIm51bWJlcmVkIjogbnVtX3QsICJsYW1wIjogIkdSRUVOIiBpZiBudW1fdCBlbHNlICgiWUVMTE9XIiBpZiByZWdfdCBlbHNl
ICJHUkFZIil9KQogICAgIyBsaWIgLyDnkrDlooMo5pys55u06K2v5ZmoKQogICAgbGlicyA9IFtdCiAgICBmb3IgbmFtZSBpbiByZXF1aXJlZF9saWJzOgog
ICAgICAgIG9rID0gX2lsdS5maW5kX3NwZWMobmFtZSkgaXMgbm90IE5vbmUKICAgICAgICBsaWJzLmFwcGVuZCh7ImxpYiI6IG5hbWUsICJpbXBvcnRhYmxl
Ijogb2ssICJsYW1wIjogIkdSRUVOIiBpZiBvayBlbHNlICJSRUQifSkKICAgICMg5pyA6L+R6Ieq5risIC8g57WQ5p6cCiAgICByZXN1bHRzID0gW10KICAg
IGlmIG91dF9kaXIuaXNfZGlyKCk6CiAgICAgICAgZm9yIHAgaW4gc29ydGVkKG91dF9kaXIuZ2xvYigiUkVTVUxUXypfbGF0ZXN0Lmpzb24iKSlbOjQwXToK
ICAgICAgICAgICAgaW1wb3J0IGRhdGV0aW1lIGFzIF9kdCwgdGltZSBhcyBfdGltZQogICAgICAgICAgICBhZ2UgPSAoX3RpbWUudGltZSgpIC0gcC5zdGF0
KCkuc3RfbXRpbWUpIC8gODY0MDAKICAgICAgICAgICAgcmVzdWx0cy5hcHBlbmQoeyJyZXN1bHQiOiBwLm5hbWUsICJhZ2VfZGF5cyI6IHJvdW5kKGFnZSwg
MSksICJsYW1wIjogIkdSRUVOIiBpZiBhZ2UgPD0gNyBlbHNlICJZRUxMT1cifSkKICAgIGZtX2l0ZW1zID0gKGZtIG9yIHt9KS5nZXQoIml0ZW1zIiwge30p
IGlmIGZtIGVsc2Uge30KICAgIHN1bW1hcnkgPSB7ImZpbGVzIjogbGVuKHJvd3MpLCAicmVkIjogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJsYW1wIl0g
PT0gIlJFRCIpLCAieWVsbG93Ijogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJsYW1wIl0gPT0gIllFTExPVyIpLCAiZ3JlZW4iOiBzdW0oMSBmb3IgciBp
biByb3dzIGlmIHJbImxhbXAiXSA9PSAiR1JFRU4iKSwKICAgICAgICAgICAgICAgIm51bWJlcmVkIjogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJudW1i
ZXIiXSksICJyZWdpc3RlcmVkIjogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJyZWdpc3RlcmVkIl0pLCAiYWNjZWwiOiBzdW0oMSBmb3IgciBpbiByb3dz
IGlmIHJbImFjY2VsIl0pLCAibmV0X2JhZCI6IHN1bSgxIGZvciByIGluIHJvd3MgaWYgbm90IHJbIm5ldF9vayJdKSwgIm5ldF9vbGQiOiBzdW0oMSBmb3Ig
ciBpbiByb3dzIGlmIHJbIm5ldF9ub3RlIl0uc3RhcnRzd2l0aCgi6IiK54mIIikpLCAic2VtYW50aWNfaXNzdWVzIjogc2VtX2lzc3VlcywKICAgICAgICAg
ICAgICAgImZuX2l0ZW1zIjogbGVuKGZtX2l0ZW1zKSwgImZuX251bWJlcmVkIjogc3VtKDEgZm9yIGUgaW4gZm1faXRlbXMudmFsdWVzKCkgaWYgZS5nZXQo
Im51bWJlciIpKSwgInRhYmxlcyI6IGxlbigodGggb3Ige30pLmdldCgidGFibGVzIiwge30pIGlmIHRoIGVsc2Uge30pLCAidGFibGVzX251bWJlcmVkIjog
c3VtKDEgZm9yIHYgaW4gKCh0aCBvciB7fSkuZ2V0KCJ0YWJsZXMiLCB7fSkgaWYgdGggZWxzZSB7fSkudmFsdWVzKCkgaWYgdi5nZXQoInRhYmxlX25vIikp
LAogICAgICAgICAgICAgICAiYm9va3MiOiBsZW4oYm9va3MpLCAibGlic19taXNzaW5nIjogc3VtKDEgZm9yIGwgaW4gbGlicyBpZiBub3QgbFsiaW1wb3J0
YWJsZSJdKSwgInB5dGhvbiI6IF9zeXMuZXhlY3V0YWJsZX0KICAgIGxhbXAgPSAiUkVEIiBpZiAoc3VtbWFyeVsicmVkIl0gb3Igc3VtbWFyeVsibGlic19t
aXNzaW5nIl0pIGVsc2UgKCJZRUxMT1ciIGlmIChzdW1tYXJ5WyJ5ZWxsb3ciXSBvciBub3QgZm0gb3Igbm90IHRoKSBlbHNlICJHUkVFTiIpCiAgICBoZWFs
dGggPSB7InN1YiI6IHN1YiwgInRzIjogbm93LCAicHl0aG9uIjogX3N5cy5leGVjdXRhYmxlLCAibGFtcCI6IGxhbXAsICJzdW1tYXJ5Ijogc3VtbWFyeSwg
ImZpbGVzIjogcm93cywgImJvb2tzIjogYm9va3MsICJsaWJzIjogbGlicywgInJlc3VsdHMiOiByZXN1bHRzLAogICAgICAgICAgICAgICJmbl9tYXRyaXgi
OiAoX2hsX3RhaWwocmVnLCBzdWIgKyAiX0Z1bmN0aW9uTWF0cml4X3YqLmpzb24iKS5uYW1lIGlmIGZtIGVsc2UgTm9uZSksICJ0YWJsZV9oZWFkZXIiOiAo
X2hsX3RhaWwocmVnLCBzdWIgKyAiX1RhYmxlSGVhZGVyX3YqLmpzb24iKS5uYW1lIGlmIHRoIGVsc2UgTm9uZSl9CiAgICBvdXRfZGlyLm1rZGlyKHBhcmVu
dHM9VHJ1ZSwgZXhpc3Rfb2s9VHJ1ZSkKICAgIChvdXRfZGlyIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIpLndyaXRlX3RleHQoX2pzb24uZHVtcHMoaGVhbHRo
LCBlbnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0xKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIHJldHVybiBoZWFsdGgKCgpkZWYgc21faGVhbHRoX3ByaW50
KGgpOgogICAgcyA9IGhbInN1bW1hcnkiXQogICAgcHJpbnQoIlvoqIhdICVzIGhlYWx0aCDCtyDmqpTml48gJWQo57SFICVkIOm7gyAlZCDntqAgJWQpwrcg
5pyJ6JmfICVkIMK3IOW3sueZu+iomCAlZCDCtyDmnInmqYsgJWQgwrcg57ay5qmL57y6ICVkIOiIiuapiyAlZCDCtyDniYjomZ/oqp7mhI8gJWQgwrcg5Yqf
ICVkLyVkIOacieiZnyDCtyDooaggJWQvJWQg5pyJ6JmfIMK3IOWGiiAlZCDCtyBsaWIg57y6ICVkIMK3ICVzIiAlICgKICAgICAgICBoWyJzdWIiXSwgc1si
ZmlsZXMiXSwgc1sicmVkIl0sIHNbInllbGxvdyJdLCBzWyJncmVlbiJdLCBzWyJudW1iZXJlZCJdLCBzWyJyZWdpc3RlcmVkIl0sIHNbImFjY2VsIl0sIHNb
Im5ldF9iYWQiXSwgc1sibmV0X29sZCJdLCBzWyJzZW1hbnRpY19pc3N1ZXMiXSwgc1siZm5fbnVtYmVyZWQiXSwgc1siZm5faXRlbXMiXSwgc1sidGFibGVz
X251bWJlcmVkIl0sIHNbInRhYmxlcyJdLCBzWyJib29rcyJdLCBzWyJsaWJzX21pc3NpbmciXSwgaFsibGFtcCJdKSkKICAgIGZvciByIGluIFt4IGZvciB4
IGluIGhbImZpbGVzIl0gaWYgeFsibGFtcCJdID09ICJSRUQiXVs6MTBdOgogICAgICAgIHByaW50KCIgIFtSRURdICVzICVzIMK3ICVzIiAlIChoWyJzdWIi
XSwgclsidGFpbCJdLCAiQVNUIOWjniIgaWYgbm90IHJbImFzdF9vayJdIGVsc2UgclsibmV0X25vdGUiXSkpCiAgICBmb3IgciBpbiBbeCBmb3IgeCBpbiBo
WyJmaWxlcyJdIGlmIHhbIm5ldF9ub3RlIl0uc3RhcnRzd2l0aCgi6IiK54mIIildWzoxMF06CiAgICAgICAgcHJpbnQoIiAgW1lFTF0gJXMgJXMgwrcgJXMi
ICUgKGhbInN1YiJdLCByWyJ0YWlsIl0sIHJbIm5ldF9ub3RlIl0pKQogICAgZm9yIGwgaW4gW3ggZm9yIHggaW4gaFsibGlicyJdIGlmIG5vdCB4WyJpbXBv
cnRhYmxlIl1dOgogICAgICAgIHByaW50KCIgIFtSRURdICVzIGxpYiDnvLogJXMo5pys55u06K2v5ZmoICVzKSIgJSAoaFsic3ViIl0sIGxbImxpYiJdLCBo
WyJweXRob24iXSkpCiMgPT09PT0gW1ZJQTpTTS1IRUFMVEg6RU5EXSA9PT09PQoKCmRlZiBfbm93KCkgLT4gc3RyOgogICAgcmV0dXJuIGRhdGV0aW1lLmRh
dGV0aW1lLm5vdygpLmlzb2Zvcm1hdCh0aW1lc3BlYz0ic2Vjb25kcyIpCgoKZGVmIF9yb290KCkgLT4gUGF0aDoKICAgIGlmIG9zLmVudmlyb24uZ2V0KCJW
SUFfUk9PVCIpOgogICAgICAgIHJldHVybiBQYXRoKG9zLmVudmlyb25bIlZJQV9ST09UIl0pCiAgICBwID0gTUUKICAgIHdoaWxlIHAucGFyZW50ICE9IHA6
CiAgICAgICAgaWYgKHAgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIikuaXNfZGlyKCkgYW5kIChwIC8gImZ1bmN0aW9uYWwgbW9kdWxlcyIpLmlzX2RpcigpOgog
ICAgICAgICAgICByZXR1cm4gcAogICAgICAgIHAgPSBwLnBhcmVudAogICAgcmV0dXJuIE1FLnBhcmVudHNbMl0KCgpkZWYgX3BhdGhzKCkgLT4gZGljdDoK
ICAgIHIgPSBfcm9vdCgpCiAgICByZXR1cm4geyJyb290IjogciwgInN1cCI6IHIgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIiwgInJlZ2lzdHJ5IjogciAvICJz
dXBwb3J0aXZlIG1vZHVsZXMiIC8gInJlZ2lzdHJ5IiwgInJlcG9ydHMiOiByIC8gIlZJQV9SZXBvcnRzIiwgInJldmlldyI6IHIgLyAiVklBX1JlcG9ydHMi
IC8gInJldmlldyIsCiAgICAgICAgICAgICJvdXQiOiByIC8gIlZJQV9SZXBvcnRzIiAvICJyZXZpZXciIC8gInZjZ2NfaGVhbHRoIiwgImNhcmRzIjogciAv
ICJkb2NzIiAvICJoYW5kb2ZmIiAvICJhaSJ9CgoKZGVmIF9sYXRlc3QoUDogZGljdCwgcmVsOiBzdHIpOgogICAgcCA9IFBbInJldmlldyJdIC8gcmVsCiAg
ICByZXR1cm4gX2hsX3JlYWRfanNvbihwKSBpZiBwLmV4aXN0cygpIGVsc2UgTm9uZQoKCmRlZiBfcGFub19jaGVja3MocGFubykgLT4gZGljdDoKICAgICIi
IlBBTk9SQU1BX2xhdGVzdC5qc29uIOWFqeeoruW9oueLgOmDveaUtjpjaGVja3MgPSBbe2ssbGFtcCwuLi59XSjlhajmma/lvJXmk44p5oiWIHtLMTogbGFt
cH0o5pGY6KaBKeOAgiIiIgogICAgYyA9IChwYW5vIG9yIHt9KS5nZXQoImNoZWNrcyIpCiAgICBpZiBpc2luc3RhbmNlKGMsIGxpc3QpOgogICAgICAgIHJl
dHVybiB7ay5nZXQoImsiKTogay5nZXQoImxhbXAiKSBmb3IgayBpbiBjIGlmIGlzaW5zdGFuY2UoaywgZGljdCl9CiAgICByZXR1cm4gYyBpZiBpc2luc3Rh
bmNlKGMsIGRpY3QpIGVsc2Uge30KCgpkZWYgbWF0cml4KFA6IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdDoKICAgIFAgPSBQIG9yIF9wYXRocygpCiAg
ICB0MCA9IHRpbWUudGltZSgpCiAgICBub3cgPSBfbm93KCkKICAgIHZjZ2MgPSBzbV9oZWFsdGgoIlZDR0MiLCBQWyJzdXAiXSwgUFsicm9vdCJdLCBQWyJy
ZXBvcnRzIl0gLyAidmNnYyIsIG5vdywgKCJwYW5kYXMiLCkpCiAgICBzdWJzID0geyJWQ0dDIjogdmNnY30KICAgIGZvciBzIGluICgiVkRGIiwgIlZSTiIp
OgogICAgICAgIGggPSBfaGxfcmVhZF9qc29uKFBbInJlcG9ydHMiXSAvIHMubG93ZXIoKSAvICJIRUFMVEhfbGF0ZXN0Lmpzb24iKSBpZiAoUFsicmVwb3J0
cyJdIC8gcy5sb3dlcigpIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIpLmV4aXN0cygpIGVsc2UgTm9uZQogICAgICAgIHN1YnNbc10gPSBoCiAgICBwYW5vID0g
X2xhdGVzdChQLCAidmNnY19wYW5vcmFtYS9QQU5PUkFNQV9sYXRlc3QuanNvbiIpCiAgICBlbnYgPSBfbGF0ZXN0KFAsICJ2Y2djX2Vudi9FTlZfTUFUUklY
X2xhdGVzdC5qc29uIikKICAgIHRvb2wgPSBfbGF0ZXN0KFAsICJ2Y2djX3Rvb2xraXQvVE9PTEtJVF9NQVRSSVhfbGF0ZXN0Lmpzb24iKQogICAgZ292ID0g
X2xhdGVzdChQLCAidmNnY19yZWdpc3RyeS9HT1ZFUk5fbGF0ZXN0Lmpzb24iKQogICAgZm0gPSBfbGF0ZXN0KFAsICJ2Y2djX21hdHJpeC9GSUxFX01BVFJJ
WF9sYXRlc3QuanNvbiIpCiAgICBsZWRnZXIgPSBQWyJyZXBvcnRzIl0gLyAidnJuIiAvICJleHRyYWN0IiAvICJWUk5fRXh0cmFjdF9MZWRnZXIuanNvbmwi
CiAgICBleHQgPSBDb3VudGVyKCkKICAgIGlmIGxlZGdlci5leGlzdHMoKToKICAgICAgICBsYXN0ID0ge30KICAgICAgICBmb3IgbG4gaW4gbGVkZ2VyLnJl
YWRfdGV4dChlbmNvZGluZz0idXRmLTgiKS5zcGxpdGxpbmVzKCk6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIHIgPSBqc29uLmxvYWRzKGxu
KQogICAgICAgICAgICAgICAgbGFzdFtyLmdldCgiZmlsZSIpXSA9IHIuZ2V0KCJzdGF0dXMiKQogICAgICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAg
ICAgICAgICAgICAgIHBhc3MKICAgICAgICBleHQgPSBDb3VudGVyKGxhc3QudmFsdWVzKCkpCiAgICBzZWN0aW9ucyA9IHsKICAgICAgICAicGFub3JhbWEi
OiB7ImxhbXAiOiAocGFubyBvciB7fSkuZ2V0KCJsYW1wIiwgIkdSQVkiKSwgImNoZWNrcyI6IF9wYW5vX2NoZWNrcyhwYW5vKSwgInRzIjogKHBhbm8gb3Ig
e30pLmdldCgidHMiKX0sCiAgICAgICAgImVudiI6IHsibGFtcCI6IChlbnYgb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJlbnZzIjogbGVuKChlbnYg
b3Ige30pLmdldCgiZW52cyIsIFtdKSksICJwZGZfdG9vbHMiOiAoZW52IG9yIHt9KS5nZXQoInBkZl90b29sc19vayIpLCAidHMiOiAoZW52IG9yIHt9KS5n
ZXQoInRzIil9LAogICAgICAgICJ0b29sa2l0IjogeyJsYW1wIjogKHRvb2wgb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJmYW1pbGllcyI6IGxlbigo
dG9vbCBvciB7fSkuZ2V0KCJyb3dzIiwgW10pKSwgIm92ZXJsYXBzIjogbGVuKCh0b29sIG9yIHt9KS5nZXQoIm92ZXJsYXBzIiwgW10pKSwgInRzIjogKHRv
b2wgb3Ige30pLmdldCgidHMiKX0sCiAgICAgICAgImdvdmVybiI6IHsibGFtcCI6IChnb3Ygb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJzdW1tYXJ5
IjogKGdvdiBvciB7fSkuZ2V0KCJzdW1tYXJ5IiksICJ0cyI6IChnb3Ygb3Ige30pLmdldCgidHMiKX0sCiAgICAgICAgImZpbGVtYXRyaXgiOiB7ImxhbXAi
OiAoZm0gb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJwZXIiOiAoZm0gb3Ige30pLmdldCgicGVyIiksICJ0cyI6IChmbSBvciB7fSkuZ2V0KCJ0cyIp
fSwKICAgICAgICAiZXh0cmFjdCI6IHsibGFtcCI6ICgiR1JFRU4iIGlmIGV4dCBhbmQgbm90IGV4dC5nZXQoIlJFVklFVyIpIGFuZCBub3QgZXh0LmdldCgi
RVJST1IiKSBlbHNlICgiWUVMTE9XIiBpZiBleHQgZWxzZSAiR1JBWSIpKSwgImNvdW50cyI6IGRpY3QoZXh0KX0sCiAgICB9CiAgICBvcmRlciA9IHsiUkVE
IjogMywgIllFTExPVyI6IDIsICJHUkVFTiI6IDEsICJHUkFZIjogMH0KICAgIGxhbXBzID0gW2hbImxhbXAiXSBmb3IgaCBpbiBzdWJzLnZhbHVlcygpIGlm
IGhdICsgW3ZbImxhbXAiXSBmb3IgdiBpbiBzZWN0aW9ucy52YWx1ZXMoKV0KICAgIGxhbXAgPSBtYXgobGFtcHMsIGtleT1sYW1iZGEgeDogb3JkZXJbeF0p
IGlmIGxhbXBzIGVsc2UgIkdSQVkiCiAgICByZXR1cm4geyJ2ZXJiIjogIm1hdHJpeCIsICJlbmdpbmUiOiBOQU1FLCAidHMiOiBub3csICJyb290Ijogc3Ry
KFBbInJvb3QiXSksICJsYW1wIjogbGFtcCwgInN1YnMiOiBzdWJzLCAic2VjdGlvbnMiOiBzZWN0aW9ucywgInNlY3MiOiByb3VuZCh0aW1lLnRpbWUoKSAt
IHQwLCAxKX0KCgpkZWYgX2h0bWwocmVzOiBkaWN0KSAtPiBzdHI6CiAgICBkZWYgbGFtcChsKToKICAgICAgICByZXR1cm4gIjxpIGNsYXNzPSdscCAlcycg
c3R5bGU9J2JhY2tncm91bmQ6JXMnPjwvaT4iICUgKGwsIExBTVAuZ2V0KGwsIExBTVBbIkdSQVkiXSkpCiAgICBjYXJkcyA9IFtdCiAgICBmb3IgcyBpbiBT
VUJTOgogICAgICAgIGggPSByZXNbInN1YnMiXS5nZXQocykKICAgICAgICBpZiBub3QgaDoKICAgICAgICAgICAgY2FyZHMuYXBwZW5kKCI8ZGl2IGNsYXNz
PSdjYXJkJz48ZGl2IGNsYXNzPSdoZCc+JXMlczwvZGl2PjxkaXYgY2xhc3M9J2t2Jz7lsJrmnKrot5EgPGNvZGU+JXNfU3lzdGVtTWFuYWdlciBoZWFsdGg8
L2NvZGU+PC9kaXY+PC9kaXY+IiAlIChsYW1wKCJHUkFZIiksIHMsIHMpKQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIG0gPSBoWyJzdW1tYXJ5Il0K
ICAgICAgICBjYXJkcy5hcHBlbmQoIjxkaXYgY2xhc3M9J2NhcmQnPjxkaXYgY2xhc3M9J2hkJz4lcyVzIDxzbWFsbD4lczwvc21hbGw+PC9kaXY+PGRpdiBj
bGFzcz0na3YnPuaqlOaXjyA8Yj4lZDwvYj4g57SFICVkIOm7gyAlZCDntqAgJWQgwrcg5pyJ6JmfICVkIMK3IOeZu+iomCAlZCDCtyDmqYsgJWQgwrcg57ay
5qmL57y6ICVkIMK3IOiqnuaEjyAlZDwvZGl2PjxkaXYgY2xhc3M9J2t2Jz7lip8gJWQvJWQg5pyJ6JmfIMK3IOihqCAlZC8lZCDmnInomZ8gwrcg5YaKICVk
IMK3IGxpYiDnvLogJWQ8L2Rpdj48ZGl2IGNsYXNzPSdrdic+PHNtYWxsPiVzPC9zbWFsbD48L2Rpdj48L2Rpdj4iCiAgICAgICAgICAgICAgICAgICAgICUg
KGxhbXAoaFsibGFtcCJdKSwgcywgaFsidHMiXSwgbVsiZmlsZXMiXSwgbVsicmVkIl0sIG1bInllbGxvdyJdLCBtWyJncmVlbiJdLCBtWyJudW1iZXJlZCJd
LCBtWyJyZWdpc3RlcmVkIl0sIG1bImFjY2VsIl0sIG1bIm5ldF9iYWQiXSwgbVsic2VtYW50aWNfaXNzdWVzIl0sIG1bImZuX251bWJlcmVkIl0sIG1bImZu
X2l0ZW1zIl0sIG1bInRhYmxlc19udW1iZXJlZCJdLCBtWyJ0YWJsZXMiXSwgbVsiYm9va3MiXSwgbVsibGlic19taXNzaW5nIl0sIGh0bWwuZXNjYXBlKG0u
Z2V0KCJweXRob24iLCAiIikpKSkKICAgIHNlYyA9IHJlc1sic2VjdGlvbnMiXQogICAgY2hpcHMgPSBbKCLlhajmma8gSzHigJNLOCIsIHNlY1sicGFub3Jh
bWEiXVsibGFtcCJdLCAiICIuam9pbigiJXM9JXMiICUga3YgZm9yIGt2IGluIHNlY1sicGFub3JhbWEiXVsiY2hlY2tzIl0uaXRlbXMoKSkgb3IgIuacqui3
kSIpLAogICAgICAgICAgICAgKCLnkrDlooPlt6XlhbciLCBzZWNbImVudiJdWyJsYW1wIl0sICLnkrDlooMgJXMgwrcgUERGIOmalOmboiAlcyIgJSAoc2Vj
WyJlbnYiXVsiZW52cyJdLCBzZWNbImVudiJdWyJwZGZfdG9vbHMiXSkpLAogICAgICAgICAgICAgKCLovJTliqnlt6XlhbciLCBzZWNbInRvb2xraXQiXVsi
bGFtcCJdLCAi5pePICVzIMK3IOmHjeeWiiAlcyIgJSAoc2VjWyJ0b29sa2l0Il1bImZhbWlsaWVzIl0sIHNlY1sidG9vbGtpdCJdWyJvdmVybGFwcyJdKSks
CiAgICAgICAgICAgICAoIuayu+eQhueZvOiZnyIsIHNlY1siZ292ZXJuIl1bImxhbXAiXSwganNvbi5kdW1wcyhzZWNbImdvdmVybiJdWyJzdW1tYXJ5Il0s
IGVuc3VyZV9hc2NpaT1GYWxzZSlbOjEyMF0gaWYgc2VjWyJnb3Zlcm4iXVsic3VtbWFyeSJdIGVsc2UgIuacqui3kSIpLAogICAgICAgICAgICAgKCLlhajm
qpTnn6npmaMiLCBzZWNbImZpbGVtYXRyaXgiXVsibGFtcCJdLCBqc29uLmR1bXBzKHNlY1siZmlsZW1hdHJpeCJdWyJwZXIiXSwgZW5zdXJlX2FzY2lpPUZh
bHNlKVs6MTIwXSBpZiBzZWNbImZpbGVtYXRyaXgiXVsicGVyIl0gZWxzZSAi5pyq6LeRIiksCiAgICAgICAgICAgICAoIlZSTiDmk7flj5YiLCBzZWNbImV4
dHJhY3QiXVsibGFtcCJdLCBqc29uLmR1bXBzKHNlY1siZXh0cmFjdCJdWyJjb3VudHMiXSwgZW5zdXJlX2FzY2lpPUZhbHNlKSBvciAi5pyq6LeRIildCiAg
ICBjaGlwX2h0bWwgPSAiIi5qb2luKCI8ZGl2IGNsYXNzPSdjaGlwJz4lczxiPiVzPC9iPjxzcGFuPiVzPC9zcGFuPjwvZGl2PiIgJSAobGFtcChsKSwgdCwg
aHRtbC5lc2NhcGUoZCkpIGZvciB0LCBsLCBkIGluIGNoaXBzKQogICAgcm93cyA9IFtdCiAgICBmb3IgcyBpbiBTVUJTOgogICAgICAgIGggPSByZXNbInN1
YnMiXS5nZXQocykKICAgICAgICBmb3IgciBpbiAoaCBvciB7fSkuZ2V0KCJmaWxlcyIsIFtdKToKICAgICAgICAgICAgcm93cy5hcHBlbmQoIjx0ciBkYXRh
LXM9JyVzJyBkYXRhLWw9JyVzJz48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPGRpdiBjbGFzcz0nZGltJz4lczwvZGl2PjwvdGQ+PHRkPiVzPC90ZD48
dGQgY2xhc3M9J24nPiVkPC90ZD48dGQgY2xhc3M9J2NvZGUnPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0
ZCBjbGFzcz0nZGltJz4lczwvdGQ+PC90cj4iCiAgICAgICAgICAgICAgICAgICAgICAgICUgKHMsIHJbImxhbXAiXSwgbGFtcChyWyJsYW1wIl0pLCBzLCBo
dG1sLmVzY2FwZShyWyJmYW1pbHkiXSksIGh0bWwuZXNjYXBlKHJbImRpciJdKSwgclsidmVyc2lvbiJdLCByWyJuX3ZlcnNpb25zIl0sIGh0bWwuZXNjYXBl
KHJbIm51bWJlciJdIG9yICLigJQiKSwgIuKckyIgaWYgclsicmVnaXN0ZXJlZCJdIGVsc2UgIuKAlCIsICLinJMiIGlmIHJbImFjY2VsIl0gZWxzZSAiPGIg
Y2xhc3M9J3InPue8ujwvYj4iLAogICAgICAgICAgICAgICAgICAgICAgICAgICAoKCLinJMiIGlmIG5vdCByWyJuZXRfbm90ZSJdLnN0YXJ0c3dpdGgoIuiI
iueJiCIpIGVsc2UgIjxiIHN0eWxlPSdjb2xvcjojZjU5ZTBiJz7oiIo8L2I+IikgaWYgclsibmV0X29rIl0gZWxzZSAiPGIgY2xhc3M9J3InPue8ujwvYj4i
KSBpZiByWyJuZXRfdXNlIl0gZWxzZSAoIuW3peWFtyIgaWYgci5nZXQoIm5ldF90b29sIikgZWxzZSAiwrciKSwgIuKckyIgaWYgclsiYXN0X29rIl0gZWxz
ZSAiPGIgY2xhc3M9J3InPuWjnjwvYj4iLCBodG1sLmVzY2FwZShyWyJzZW1hbnRpYyJdKSkpCiAgICBib29rcyA9IFtdCiAgICBmb3IgcyBpbiBTVUJTOgog
ICAgICAgIGggPSByZXNbInN1YnMiXS5nZXQocykKICAgICAgICBmb3IgYiBpbiAoaCBvciB7fSkuZ2V0KCJib29rcyIsIFtdKToKICAgICAgICAgICAgYm9v
a3MuYXBwZW5kKCI8dHIgZGF0YS1zPSclcycgZGF0YS1sPSclcyc+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPC90ZD48dGQ+JXM8
L3RkPjx0ZD4lczwvdGQ+PC90cj4iICUgKHMsIGJbImxhbXAiXSwgbGFtcChiWyJsYW1wIl0pLCBzLCBodG1sLmVzY2FwZShiWyJib29rIl0pLCBiWyJkaXIi
XSwgIuKckyIgaWYgYlsicmVnaXN0ZXJlZCJdIGVsc2UgIuKAlCIsICLinJMiIGlmIGJbIm51bWJlcmVkIl0gZWxzZSAi4oCUIikpCiAgICBsaWJzID0gW10K
ICAgIGZvciBzIGluIFNVQlM6CiAgICAgICAgaCA9IHJlc1sic3VicyJdLmdldChzKQogICAgICAgIGZvciBsIGluIChoIG9yIHt9KS5nZXQoImxpYnMiLCBb
XSk6CiAgICAgICAgICAgIGxpYnMuYXBwZW5kKCI8dHIgZGF0YS1zPSclcycgZGF0YS1sPSclcyc+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+
PHRkPiVzPC90ZD48L3RyPiIgJSAocywgbFsibGFtcCJdLCBsYW1wKGxbImxhbXAiXSksIHMsIGxbImxpYiJdLCAi4pyTIiBpZiBsWyJpbXBvcnRhYmxlIl0g
ZWxzZSAiPGIgY2xhc3M9J3InPue8ujwvYj4iKSkKICAgIHJldHVybiAiIiI8IWRvY3R5cGUgaHRtbD48aHRtbCBsYW5nPSJ6aC1IYW50Ij48aGVhZD48bWV0
YSBjaGFyc2V0PSJ1dGYtOCI+PG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCxpbml0aWFsLXNjYWxlPTEiPjx0aXRs
ZT5WSUEg5YGl5bq355+p6ZmjPC90aXRsZT4KPHN0eWxlPgo6cm9vdHstLWJnOiNmZmY7LS1wYW5lbDojZjdmN2Y3Oy0tbGluZTojZTBlMGUwOy0tdHh0OiMx
ZjI5Mzc7LS1kaW06IzZiNzI4MH0KYm9keXtmb250LWZhbWlseToiTWljcm9zb2Z0IEpoZW5nSGVpIFVJIiwiU2Vnb2UgVUkiLEFyaWFsLHNhbnMtc2VyaWY7
YmFja2dyb3VuZDp2YXIoLS1iZyk7Y29sb3I6dmFyKC0tdHh0KTttYXJnaW46MDtwYWRkaW5nOjEycHg7Zm9udC1zaXplOjEycHh9Cmgxe2ZvbnQtc2l6ZTox
NnB4O21hcmdpbjowIDAgNHB4fS5tZXRhe2NvbG9yOnZhcigtLWRpbSk7Zm9udC1zaXplOjExcHg7bWFyZ2luLWJvdHRvbTo4cHh9Ci5ncmlke2Rpc3BsYXk6
Z3JpZDtncmlkLXRlbXBsYXRlLWNvbHVtbnM6cmVwZWF0KGF1dG8tZml0LG1pbm1heCgyNjBweCwxZnIpKTtnYXA6OHB4O21hcmdpbi1ib3R0b206OHB4fQou
Y2FyZHtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsKTtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OHB4O3BhZGRpbmc6OHB4fS5o
ZHtmb250LXdlaWdodDo3MDA7Zm9udC1zaXplOjEzcHg7bWFyZ2luLWJvdHRvbTo0cHh9Lmt2e2ZvbnQtc2l6ZToxMS41cHg7bGluZS1oZWlnaHQ6MS41fQou
Y2hpcHN7ZGlzcGxheTpncmlkO2dyaWQtdGVtcGxhdGUtY29sdW1uczpyZXBlYXQoYXV0by1maXQsbWlubWF4KDIyMHB4LDFmcikpO2dhcDo2cHg7bWFyZ2lu
LWJvdHRvbToxMHB4fS5jaGlwe2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlcjoxcHggc29saWQgdmFyKC0tbGluZSk7Ym9yZGVyLXJhZGl1czo2cHg7
cGFkZGluZzo1cHggOHB4O2ZvbnQtc2l6ZToxMXB4O2Rpc3BsYXk6ZmxleDtnYXA6NnB4O2FsaWduLWl0ZW1zOmNlbnRlcjtmbGV4LXdyYXA6d3JhcH0uY2hp
cCBzcGFue2NvbG9yOnZhcigtLWRpbSl9Ci5scHtkaXNwbGF5OmlubGluZS1ibG9jazt3aWR0aDoxMXB4O2hlaWdodDoxMXB4O2JvcmRlci1yYWRpdXM6NTAl
JTt2ZXJ0aWNhbC1hbGlnbjptaWRkbGU7bWFyZ2luLXJpZ2h0OjRweH0ubHAuUkVEe2FuaW1hdGlvbjpibCAyLjRzIGVhc2UtaW4tb3V0IGluZmluaXRlfUBr
ZXlmcmFtZXMgYmx7MCUlLDEwMCUle29wYWNpdHk6MX01MCUle29wYWNpdHk6LjI1fX0KLmJhciBidXR0b257bWFyZ2luOjAgNHB4IDZweCAwO3BhZGRpbmc6
M3B4IDhweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlci1yYWRpdXM6NnB4O2N1cnNvcjpwb2lu
dGVyO2ZvbnQtc2l6ZToxMXB4fQpkZXRhaWxze21hcmdpbjo2cHggMH1zdW1tYXJ5e2N1cnNvcjpwb2ludGVyO2ZvbnQtd2VpZ2h0OjcwMDtmb250LXNpemU6
MTIuNXB4O3BhZGRpbmc6NHB4IDB9Ci53cmFwe292ZXJmbG93LXg6YXV0b310YWJsZXtib3JkZXItY29sbGFwc2U6Y29sbGFwc2U7d2lkdGg6MTAwJSU7dGFi
bGUtbGF5b3V0OmF1dG99dGgsdGR7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtwYWRkaW5nOjJweCA1cHg7dGV4dC1hbGlnbjpsZWZ0O3ZlcnRpY2Fs
LWFsaWduOnRvcDt3aGl0ZS1zcGFjZTpub3dyYXB9dGh7YmFja2dyb3VuZDojMTExODI3O2NvbG9yOiNmZmY7cG9zaXRpb246c3RpY2t5O3RvcDowO2ZvbnQt
d2VpZ2h0OjYwMH0KdHI6bnRoLWNoaWxkKGV2ZW4pe2JhY2tncm91bmQ6I2ZhZmFmYX10ZC5jb2Rle2ZvbnQtZmFtaWx5OkNvbnNvbGFzLG1vbm9zcGFjZX10
ZC5ue3RleHQtYWxpZ246cmlnaHR9LmRpbXtjb2xvcjp2YXIoLS1kaW0pO2ZvbnQtc2l6ZToxMC41cHg7d2hpdGUtc3BhY2U6bm9ybWFsfS5ye2NvbG9yOiNk
YzI2MjZ9CkBtZWRpYShtYXgtd2lkdGg6NzAwcHgpe2JvZHl7cGFkZGluZzo2cHh9dGgsdGR7cGFkZGluZzoycHggM3B4O2ZvbnQtc2l6ZToxMC41cHh9fQo8
L3N0eWxlPjwvaGVhZD48Ym9keT4KPGgxPlZJQSDlgaXlurfnn6npmaMgwrcgVkNHQyAvIFZERiAvIFZSTjwvaDE+PGRpdiBjbGFzcz0ibWV0YSI+JXMgwrcg
5qC5ICVzIMK3IOWQhCBTeXN0ZW1NYW5hZ2VyIOiHquWgsShoZWFsdGgg5YuV6KmeKSzmr43ns7vntbHlj6roroDljK/nuL0gwrcg57SFID0gQVNUIOWjniAv
IOWHuue2sueEoee2suapiyAvIGxpYiDnvLo76buDID0g54Sh6JmfIC8g5pyq55m76KiYIC8g54Sh5qmLIC8g54mI6Jmf6Kqe5oSPO+e2oCA9IOm9ijvngbAg
PSDlsJrmnKrot5E8L2Rpdj4KPGRpdiBjbGFzcz0iZ3JpZCI+JXM8L2Rpdj4KPGRpdiBjbGFzcz0iY2hpcHMiPiVzPC9kaXY+CjxkaXYgY2xhc3M9ImJhciI+
JXMgPGJ1dHRvbiBvbmNsaWNrPSJmbHQoJycsJycpIj7lhajpg6g8L2J1dHRvbj4gPGJ1dHRvbiBvbmNsaWNrPSJmbHQoJycsJ1JFRCcpIj7lj6rnnIvntIU8
L2J1dHRvbj4gPGJ1dHRvbiBvbmNsaWNrPSJmbHQoJycsJ1lFTExPVycpIj7lj6rnnIvpu4M8L2J1dHRvbj48L2Rpdj4KPGRldGFpbHMgb3Blbj48c3VtbWFy
eT7mqpTmoYggLyDlvJXmk44o5q+P5peP5LiA5YiXKTwvc3VtbWFyeT48ZGl2IGNsYXNzPSJ3cmFwIj48dGFibGUgY2xhc3M9Im0iPjx0aGVhZD48dHI+PHRo
PueHiDwvdGg+PHRoPuezu+e1sTwvdGg+PHRoPuaXjyAvIOWkvjwvdGg+PHRoPuWwvueJiDwvdGg+PHRoPueJiOaVuDwvdGg+PHRoPue3qOiZnzwvdGg+PHRo
PueZu+iomDwvdGg+PHRoPuWKoOmAn+WZqDwvdGg+PHRoPue2suapizwvdGg+PHRoPkFTVDwvdGg+PHRoPueJiOacrOiqnuaEjzwvdGg+PC90cj48L3RoZWFk
Pjx0Ym9keT4lczwvdGJvZHk+PC90YWJsZT48L2Rpdj48L2RldGFpbHM+CjxkZXRhaWxzIG9wZW4+PHN1bW1hcnk+5YaKIC8g6KGo6aCtIC8g5a2X5YW4PC9z
dW1tYXJ5PjxkaXYgY2xhc3M9IndyYXAiPjx0YWJsZSBjbGFzcz0ibSI+PHRoZWFkPjx0cj48dGg+54eIPC90aD48dGg+57O757WxPC90aD48dGg+5YaKPC90
aD48dGg+5aS+PC90aD48dGg+6KGo6aCt55m76KiYPC90aD48dGg+55m86JmfPC90aD48L3RyPjwvdGhlYWQ+PHRib2R5PiVzPC90Ym9keT48L3RhYmxlPjwv
ZGl2PjwvZGV0YWlscz4KPGRldGFpbHM+PHN1bW1hcnk+bGliIC8g55Kw5aKDKOWQhOiHquebtOitr+WZqCk8L3N1bW1hcnk+PGRpdiBjbGFzcz0id3JhcCI+
PHRhYmxlIGNsYXNzPSJtIj48dGhlYWQ+PHRyPjx0aD7nh4g8L3RoPjx0aD7ns7vntbE8L3RoPjx0aD5saWI8L3RoPjx0aD7lj68gaW1wb3J0PC90aD48L3Ry
PjwvdGhlYWQ+PHRib2R5PiVzPC90Ym9keT48L3RhYmxlPjwvZGl2PjwvZGV0YWlscz4KPHNjcmlwdD5mdW5jdGlvbiBmbHQocyxsKXtkb2N1bWVudC5xdWVy
eVNlbGVjdG9yQWxsKCd0YWJsZS5tIHRib2R5IHRyJykuZm9yRWFjaChmdW5jdGlvbih0KXt0LnN0eWxlLmRpc3BsYXk9KCghc3x8dC5kYXRhc2V0LnM9PT1z
KSYmKCFsfHx0LmRhdGFzZXQubD09PWwpKT8nJzonbm9uZSd9KX08L3NjcmlwdD4KPC9ib2R5PjwvaHRtbD4iIiIgJSAocmVzWyJ0cyJdLCBodG1sLmVzY2Fw
ZShyZXNbInJvb3QiXSksICIiLmpvaW4oY2FyZHMpLCBjaGlwX2h0bWwsICIiLmpvaW4oIjxidXR0b24gb25jbGljaz1cImZsdCgnJXMnLCcnKVwiPiVzPC9i
dXR0b24+IiAlIChzLCBzKSBmb3IgcyBpbiBTVUJTKSwgIlxuIi5qb2luKHJvd3MpLCAiXG4iLmpvaW4oYm9va3MpLCAiXG4iLmpvaW4obGlicykpCgoKZGVm
IHBhc3RlX3BhY2socmVzOiBkaWN0KSAtPiBsaXN0OgogICAgTCA9IFsiW+ioiF0gdmNnYyBoZWFsdGggbWF0cml4IMK3IOe4veeHiCAlcyDCtyAlcyDCtyAi
ICUgKHJlc1sibGFtcCJdLCByZXNbInRzIl0pICsgIiDCtyAiLmpvaW4oIiVzPSVzIiAlIChzLCAocmVzWyJzdWJzIl1bc10gb3Ige30pLmdldCgibGFtcCIs
ICJHUkFZKOacqui3kSBoZWFsdGgpIikpIGZvciBzIGluIFNVQlMpXQogICAgZm9yIHMgaW4gU1VCUzoKICAgICAgICBoID0gcmVzWyJzdWJzIl0uZ2V0KHMp
CiAgICAgICAgaWYgbm90IGg6CiAgICAgICAgICAgIEwuYXBwZW5kKCIgIFtHUkFZXSAlcyDlsJrmnKrot5EgJXNfU3lzdGVtTWFuYWdlciBoZWFsdGgiICUg
KHMsIHMpKQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIG0gPSBoWyJzdW1tYXJ5Il0KICAgICAgICBMLmFwcGVuZCgiICBbJXNdICVzIOaqlOaXjyAl
ZCjntIUgJWQg6buDICVkIOe2oCAlZCnCtyDmnInomZ8gJWQgwrcg55m76KiYICVkIMK3IOapiyAlZCDCtyDntrLmqYvnvLogJWQgwrcg6Kqe5oSPICVkIMK3
IOWKnyAlZC8lZCDCtyDooaggJWQvJWQgwrcg5YaKICVkIMK3IGxpYiDnvLogJWQiICUgKHsiUkVEIjogIlJFRCIsICJZRUxMT1ciOiAiWUVMIiwgIkdSRUVO
IjogIk9LIn1baFsibGFtcCJdXSwgcywgbVsiZmlsZXMiXSwgbVsicmVkIl0sIG1bInllbGxvdyJdLCBtWyJncmVlbiJdLCBtWyJudW1iZXJlZCJdLCBtWyJy
ZWdpc3RlcmVkIl0sIG1bImFjY2VsIl0sIG1bIm5ldF9iYWQiXSwgbVsic2VtYW50aWNfaXNzdWVzIl0sIG1bImZuX251bWJlcmVkIl0sIG1bImZuX2l0ZW1z
Il0sIG1bInRhYmxlc19udW1iZXJlZCJdLCBtWyJ0YWJsZXMiXSwgbVsiYm9va3MiXSwgbVsibGlic19taXNzaW5nIl0pKQogICAgICAgIGZvciByIGluIFt4
IGZvciB4IGluIGhbImZpbGVzIl0gaWYgeFsibGFtcCJdID09ICJSRUQiXVs6OF06CiAgICAgICAgICAgIEwuYXBwZW5kKCIgICAgW1JFRF0gJXMgJXMgwrcg
JXMiICUgKHMsIHJbInRhaWwiXSwgIkFTVCDlo54iIGlmIG5vdCByWyJhc3Rfb2siXSBlbHNlICLlh7rntrLnhKHntrLmqYsiKSkKICAgICAgICBmb3IgbCBp
biBbeCBmb3IgeCBpbiBoWyJsaWJzIl0gaWYgbm90IHhbImltcG9ydGFibGUiXV1bOjVdOgogICAgICAgICAgICBMLmFwcGVuZCgiICAgIFtSRURdICVzIGxp
YiDnvLogJXMiICUgKHMsIGxbImxpYiJdKSkKICAgICAgICBzZW0gPSBbeCBmb3IgeCBpbiBoWyJmaWxlcyJdIGlmIHhbInNlbWFudGljIl1dWzo2XQogICAg
ICAgIGZvciByIGluIHNlbToKICAgICAgICAgICAgTC5hcHBlbmQoIiAgICBbWUVMXSAlcyAlcyDCtyAlcyIgJSAocywgclsiZmFtaWx5Il0sIHJbInNlbWFu
dGljIl0pKQogICAgZm9yIGssIHYgaW4gcmVzWyJzZWN0aW9ucyJdLml0ZW1zKCk6CiAgICAgICAgTC5hcHBlbmQoIiAgWyVzXSAlcyDCtyAlcyIgJSAoeyJS
RUQiOiAiUkVEIiwgIllFTExPVyI6ICJZRUwiLCAiR1JFRU4iOiAiT0siLCAiR1JBWSI6ICJHUkFZIn1bdlsibGFtcCJdXSwgaywganNvbi5kdW1wcyh7a2s6
IHZ2IGZvciBraywgdnYgaW4gdi5pdGVtcygpIGlmIGtrIG5vdCBpbiAoImxhbXAiLCAidHMiKX0sIGVuc3VyZV9hc2NpaT1GYWxzZSlbOjE2MF0pKQogICAg
TC5hcHBlbmQoIk5FWFQ6IOe0hSDihpIg6Kmy5a2Q57O757WxIG1hbmFnZXIg5Ye66JaE5bC+KOijnOe2suapiyAvIOS/riBBU1QgLyDoo50gbGliKTvpu4Mg
4oaSIOi3kSBmbi90YWJsZSByZWdpc3RlciArIFZDR0MgZ292ZXJuIOeZvOiZn+OAgeijnCBbVklBOkFDQ0VMLUJSSURHRV3jgIHniYjomZ/oo5zmtJ4754Gw
IOKGkiDlhYjot5HlsI3mh4nlvJXmk4475aCx5ZGKIFZJQV9SZXBvcnRzL3Jldmlldy92Y2djX2hlYWx0aC9IRUFMVEhfTUFUUklYX2xhdGVzdC5odG1sIikK
ICAgIHJldHVybiBMWzozMDBdCgoKZGVmIHdyaXRlX291dHB1dHMocmVzOiBkaWN0LCBwYWNrOiBsaXN0LCBQOiBkaWN0IHwgTm9uZSA9IE5vbmUpIC0+IGRp
Y3Q6CiAgICBQID0gUCBvciBfcGF0aHMoKQogICAgUFsib3V0Il0ubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgUFsiY2FyZHMiXS5t
a2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICAoUFsib3V0Il0gLyAiSEVBTFRIX01BVFJJWF9sYXRlc3QuanNvbiIpLndyaXRlX3RleHQo
anNvbi5kdW1wcyhyZXMsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgaHQgPSBQWyJvdXQiXSAvICJIRUFM
VEhfTUFUUklYX2xhdGVzdC5odG1sIgogICAgaHQud3JpdGVfdGV4dChfaHRtbChyZXMpLCBlbmNvZGluZz0idXRmLTgiKQogICAgbWQgPSBQWyJjYXJkcyJd
IC8gKCJWQ0dDX0hlYWx0aENhcmRfJXMubWQiICUgZGF0ZXRpbWUuZGF0ZXRpbWUubm93KCkuc3RyZnRpbWUoIiVZJW0lZCIpKQogICAgbWQud3JpdGVfdGV4
dCgiXG4iLmpvaW4oWyIjIFZJQSDlgaXlurfnn6npmaPljaEiLCAiIiwgImBgYCJdICsgcGFjayArIFsiYGBgIiwgIiJdKSwgZW5jb2Rpbmc9InV0Zi04IikK
ICAgIHJldHVybiB7Imh0bWwiOiBzdHIoaHQpLCAibWQiOiBzdHIobWQpfQoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJv
bi5nZXQoIlZJQV9GUk9NX1ZDR0MiKSAhPSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAg
ICAgICAgcmV0dXJuIDIKICAgIGEgPSBsaXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQogICAgaWYgIi0tc2VsZnRlc3QiIGlu
IGFbOjJdOgogICAgICAgIHJldHVybiBzZWxmdGVzdCgpCiAgICBpZiBhWzoxXSAhPSBbIm1hdHJpeCJdOgogICAgICAgIHByaW50KCJb5ouS6LeRXSBtYXRy
aXggfCAtLXNlbGZ0ZXN0IikKICAgICAgICByZXR1cm4gMgogICAgcmVzID0gbWF0cml4KCkKICAgIHBhY2sgPSBwYXN0ZV9wYWNrKHJlcykKICAgIG91dCA9
IHdyaXRlX291dHB1dHMocmVzLCBwYWNrKQogICAgZm9yIGxuIGluIHBhY2s6CiAgICAgICAgcHJpbnQobG4pCiAgICBwcmludCgiICBbTUFUUklYXSAlcyIg
JSBvdXRbImh0bWwiXSkKICAgIHByaW50KCIgIFvljaFdICVzIiAlIG91dFsibWQiXSkKICAgIGlmIG9zLmVudmlyb24uZ2V0KCJWSUFfTk9fT1BFTiIpICE9
ICIxIiBhbmQgb3MubmFtZSA9PSAibnQiOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3Muc3RhcnRmaWxlKG91dFsiaHRtbCJdKSAgIyB0eXBlOiBpZ25v
cmVbYXR0ci1kZWZpbmVkXQogICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICBwYXNzCiAgICByZXR1cm4gMSBpZiByZXNbImxhbXAiXSA9PSAi
UkVEIiBlbHNlIDAKCgoKCiMgPT09PT0gW1ZJQTpVSS1USEVNRTp2MDEwMF0g5pqr5pmC5qiZ5rqWIFUvSSDmqKHmnb8o6aGP6ImyL+Wtl+mrlC/plpPot50g
dG9rZW4g5YaKO+acquS+huaOpeS7u+S9leioreioiOaooeadv+WPquaPm+WGiuS4jeaUueW8leaTjjvnh4joibLpjpblrpogVklBX1VJX0Zvcm1hdExvY2sg
5Zub6ImyKT09PT09Cl9USEVNRV9ERUZBVUxUID0gewogICAgInNjaGVtYSI6ICJWSUEuVUkuVGVtcGxhdGUuU1NPVC52MSIsICJ2ZXJzaW9uIjogInYwMTAw
IiwgInN0YXR1cyI6ICJURU1QT1JBUllfU1RBTkRBUkQiLAogICAgInJ1bGUiOiAi5omA5pyJ5a2Q57O757WxIFUvSSDlj6rnlKggdmFyKC0tdG9rZW4pO+aP
m+ioreioiOaooeadvyA9IOWHuuaWsOeJiOWGiuaUuSB0b2tlbnM754eI5Zub6ImyKOe2oC/pu4Mv57SFL+eBsCnpjpblrprkuI3pmqjmqKHmnb/oroo7aGlz
dG9yeSDlj6rlop4iLAogICAgInRva2VucyI6IHsiYmciOiAiI2ZmZmZmZiIsICJwYW5lbCI6ICIjZjdmN2Y3IiwgImxpbmUiOiAiI2UwZTBlMCIsICJ0eHQi
OiAiIzFmMjkzNyIsICJkaW0iOiAiIzZiNzI4MCIsICJhY2MiOiAiIzI1NjNlYiIsICJoZWFkIjogIiMxMTE4MjciLCAiaGVhZC10eHQiOiAiI2ZmZmZmZiIs
ICJ6ZWJyYSI6ICIjZmFmYWZhIiwKICAgICAgICAgICAgICAgImZvbnQiOiAiXCJNaWNyb3NvZnQgSmhlbmdIZWkgVUlcIixcIlNlZ29lIFVJXCIsQXJpYWws
c2Fucy1zZXJpZiIsICJtb25vIjogIkNvbnNvbGFzLG1vbm9zcGFjZSIsICJmcyI6ICIxMnB4IiwgInJhZGl1cyI6ICI4cHgiLCAicGFkIjogIjZweCIsCiAg
ICAgICAgICAgICAgICJsYW1wLWdyZWVuIjogIiMxNmEzNGEiLCAibGFtcC15ZWxsb3ciOiAiI2Y1OWUwYiIsICJsYW1wLXJlZCI6ICIjZGMyNjI2IiwgImxh
bXAtZ3JheSI6ICIjOWNhM2FmIn0sCiAgICAibG9ja2VkIjogWyJsYW1wLWdyZWVuIiwgImxhbXAteWVsbG93IiwgImxhbXAtcmVkIiwgImxhbXAtZ3JheSJd
LCAiaGlzdG9yeSI6IFtdfQpfSEVYMlRPS0VOID0geyIjMTZhMzRhIjogImxhbXAtZ3JlZW4iLCAiI2Y1OWUwYiI6ICJsYW1wLXllbGxvdyIsICIjZGMyNjI2
IjogImxhbXAtcmVkIiwgIiM5Y2EzYWYiOiAibGFtcC1ncmF5IiwgIiNmN2Y3ZjciOiAicGFuZWwiLCAiI2UwZTBlMCI6ICJsaW5lIiwgIiMxZjI5MzciOiAi
dHh0IiwgIiM2YjcyODAiOiAiZGltIiwgIiMyNTYzZWIiOiAiYWNjIiwgIiMxMTE4MjciOiAiaGVhZCIsICIjZmFmYWZhIjogInplYnJhIn0KCgpkZWYgdWlf
dGhlbWVfbG9hZChyb290KToKICAgIGltcG9ydCBqc29uIGFzIF9qCiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX1AKICAgIGZwID0gX1Aocm9v
dCkgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIiAvICJyZWdpc3RyeSIgLyAiVklBX1VJX1RlbXBsYXRlX1NTT1RfdjAxMDAuanNvbiIKICAgIHRyeToKICAgICAg
ICBpZiBmcC5leGlzdHMoKToKICAgICAgICAgICAgZCA9IF9qLmxvYWRzKGZwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpCiAgICAgICAgICAg
IHQgPSBkaWN0KF9USEVNRV9ERUZBVUxUWyJ0b2tlbnMiXSk7IHQudXBkYXRlKGQuZ2V0KCJ0b2tlbnMiKSBvciB7fSkKICAgICAgICAgICAgZm9yIGsgaW4g
X1RIRU1FX0RFRkFVTFRbImxvY2tlZCJdOgogICAgICAgICAgICAgICAgdFtrXSA9IF9USEVNRV9ERUZBVUxUWyJ0b2tlbnMiXVtrXSAgICAgICAgICAjIOeH
iOiJsumOluWumgogICAgICAgICAgICByZXR1cm4gdCwgZnAubmFtZQogICAgZXhjZXB0IEV4Y2VwdGlvbjogICMgbm9xYTogQkxFMDAxCiAgICAgICAgcGFz
cwogICAgcmV0dXJuIGRpY3QoX1RIRU1FX0RFRkFVTFRbInRva2VucyJdKSwgTm9uZQoKCmRlZiB1aV90aGVtZV9jc3ModG9rZW5zKToKICAgIHJldHVybiAi
PHN0eWxlIGlkPVwidmlhLXRoZW1lXCI+OnJvb3R7JXN9PC9zdHlsZT4iICUgIjsiLmpvaW4oIi0tJXM6JXMiICUgKGssIHYpIGZvciBrLCB2IGluIHRva2Vu
cy5pdGVtcygpKQoKCmRlZiB1aV90aGVtZV9hcHBseShodG1sX3RleHQsIHJvb3QpOgogICAgIiIi5oqK6aCB6Z2i6KOh55qE5Zu65a6a6Imy5o+b5oiQIHZh
cigtLXRva2VuLOWbuuWumuiJsikoZmFsbGJhY2sg5L+d55WZKSzkuKblnKggPGhlYWQ+IOW+jOaPkiB0b2tlbiDlhoogQ1NTO+eHiOiJsuS4jeiuiuOAgiIi
IgogICAgdG9rZW5zLCBib29rID0gdWlfdGhlbWVfbG9hZChyb290KQogICAgb3V0ID0gaHRtbF90ZXh0CiAgICBmb3IgaHgsIHRrIGluIF9IRVgyVE9LRU4u
aXRlbXMoKToKICAgICAgICBvdXQgPSBvdXQucmVwbGFjZSgiJ2JhY2tncm91bmQ6JXMnIiAlIGh4LCAiJ2JhY2tncm91bmQ6dmFyKC0tJXMsJXMpJyIgJSAo
dGssIGh4KSkucmVwbGFjZSgiYmFja2dyb3VuZDolcyIgJSBoeCwgImJhY2tncm91bmQ6dmFyKC0tJXMsJXMpIiAlICh0aywgaHgpKS5yZXBsYWNlKCJjb2xv
cjolcyIgJSBoeCwgImNvbG9yOnZhcigtLSVzLCVzKSIgJSAodGssIGh4KSkucmVwbGFjZSgiYm9yZGVyOjFweCBzb2xpZCAlcyIgJSBoeCwgImJvcmRlcjox
cHggc29saWQgdmFyKC0tJXMsJXMpIiAlICh0aywgaHgpKQogICAgY3NzID0gdWlfdGhlbWVfY3NzKHRva2VucykgKyAoIjwhLS0gdGhlbWU6JXMgLS0+IiAl
IChib29rIG9yICJkZWZhdWx0IikpIAogICAgaSA9IG91dC5maW5kKCI8aGVhZD4iKQogICAgb3V0ID0gKG91dFs6aSArIDZdICsgY3NzICsgb3V0W2kgKyA2
Ol0pIGlmIGkgPj0gMCBlbHNlIChjc3MgKyBvdXQpCiAgICByZXR1cm4gb3V0CgoKZGVmIHVpX3RoZW1lX2luaXQocm9vdCwgYXBwbHk9VHJ1ZSk6CiAgICBp
bXBvcnQganNvbiBhcyBfaiwgZGF0ZXRpbWUgYXMgX2R0CiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX1AKICAgIGZwID0gX1Aocm9vdCkgLyAi
c3VwcG9ydGl2ZSBtb2R1bGVzIiAvICJyZWdpc3RyeSIgLyAiVklBX1VJX1RlbXBsYXRlX1NTT1RfdjAxMDAuanNvbiIKICAgIGlmIGZwLmV4aXN0cygpOgog
ICAgICAgIHJldHVybiB7InN0YXR1cyI6ICJFWElTVFMiLCAiZmlsZSI6IGZwLm5hbWV9CiAgICBkID0gZGljdChfVEhFTUVfREVGQVVMVCk7IGRbImNyZWF0
ZWRfYXQiXSA9IF9kdC5kYXRldGltZS5ub3coKS5pc29mb3JtYXQodGltZXNwZWM9InNlY29uZHMiKTsgZFsib3JpZ2luIl0gPSAi5pON5L2c5ZOh5LukIDIw
MjYtMTAtMDY65pyq5L6G6Ieq6YGp5oeJ5byP5pyD5o6l5LiK5Lu75L2VIFUvSSDoqK3oqIjmqKHmnb/poY/oibLnmoTmmqvmmYLmqJnmupbmqKHmnb8iCiAg
ICBpZiBhcHBseToKICAgICAgICBmcC5wYXJlbnQubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgICAgIGZwLndyaXRlX3RleHQoX2ou
ZHVtcHMoZCwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICByZXR1cm4geyJzdGF0dXMiOiAiV1JJVFRFTiIg
aWYgYXBwbHkgZWxzZSAiUExBTiIsICJmaWxlIjogZnAubmFtZSwgInRva2VucyI6IGxlbihkWyJ0b2tlbnMiXSl9CiMgPT09PT0gW1ZJQTpVSS1USEVNRTpF
TkRdID09PT09CgoKIyA9PT09PSBbVklBOlVJLU1PVVNFOnYwMTAwXSBMMTE4IOa7kem8oOW+i+W+jOiZleeQhjrmjIfku6TmoYbml4HliqDjgIzln7fooYwo
5ruR6bygKeOAjT0gdmlhOi8vIOmAo+e1kChXaW5kb3dzIOS6pOe1puWVn+WLleWZqCnCtyDjgIzpgbjmqpTln7fooYzjgI1waWNrPTEgwrcg5pel5pyf5qyE
5pS5IHR5cGU9ZGF0ZTvpjbXnm6TovLjlhaXlj6rlianmnIDlvozmiYvmrrUgPT09PT0KX01PVVNFX0pTID0gIiIiCjxzY3JpcHQ+CihmdW5jdGlvbigpewog
IHZhciBTVUI9JShzdWIpczsKICBmdW5jdGlvbiBidWlsZChjbWQscGljayl7CiAgICB2YXIgbT1jbWQubWF0Y2goL3B5dGhvblxccysiW14iXSsiXFxzKygu
KikkLyk7IGlmKCFtKSByZXR1cm4gJyc7CiAgICB2YXIgdG9rcz1tWzFdLnRyaW0oKS5zcGxpdCgvXFxzKy8pLmZpbHRlcihCb29sZWFuKSwgdmVyYj1bXSwg
YXJncz1bXTsKICAgIGZvcih2YXIgaT0wO2k8dG9rcy5sZW5ndGg7aSsrKXsgaWYoYXJncy5sZW5ndGg9PT0wICYmIHRva3NbaV0uaW5kZXhPZignLS0nKSE9
PTApIHZlcmIucHVzaCh0b2tzW2ldKTsgZWxzZSBhcmdzLnB1c2godG9rc1tpXSk7IH0KICAgIHZhciB1PSd2aWE6Ly8nK1NVQisnLycrdmVyYi5qb2luKCcv
Jyk7IHZhciBxPVtdOyBpZihhcmdzLmxlbmd0aCkgcS5wdXNoKCdhcmdzPScrZW5jb2RlVVJJQ29tcG9uZW50KGFyZ3Muam9pbignICcpKSk7IGlmKHBpY2sp
IHEucHVzaCgncGljaz0xJyk7CiAgICByZXR1cm4gdSsocS5sZW5ndGg/KCc/JytxLmpvaW4oJyYnKSk6JycpOwogIH0KICBmdW5jdGlvbiBzeW5jKCl7IHZh
ciB0PWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdjbWQnKTsgaWYoIXQpIHJldHVybjsgdmFyIGE9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ3J1bicpLCBi
PWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdydW5waWNrJyk7CiAgICBpZihhKXthLmhyZWY9YnVpbGQodC52YWx1ZSxmYWxzZSl8fCcjJzt9IGlmKGIpe2Iu
aHJlZj1idWlsZCh0LnZhbHVlLHRydWUpfHwnIyc7fSB9CiAgdmFyIHQ9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2NtZCcpOyBpZih0KXsgbmV3IE11dGF0
aW9uT2JzZXJ2ZXIoc3luYykub2JzZXJ2ZSh0LHthdHRyaWJ1dGVzOnRydWUsY2hpbGRMaXN0OnRydWUsY2hhcmFjdGVyRGF0YTp0cnVlLHN1YnRyZWU6dHJ1
ZX0pOyB0LmFkZEV2ZW50TGlzdGVuZXIoJ2lucHV0JyxzeW5jKTsgfQogIHZhciBvcmlnU2V0PU9iamVjdC5nZXRPd25Qcm9wZXJ0eURlc2NyaXB0b3IoSFRN
TFRleHRBcmVhRWxlbWVudC5wcm90b3R5cGUsJ3ZhbHVlJyk7CiAgaWYodCYmb3JpZ1NldCYmb3JpZ1NldC5zZXQpeyBPYmplY3QuZGVmaW5lUHJvcGVydHko
dCwndmFsdWUnLHtzZXQ6ZnVuY3Rpb24odil7b3JpZ1NldC5zZXQuY2FsbCh0aGlzLHYpO3N5bmMoKTt9LGdldDpmdW5jdGlvbigpe3JldHVybiBvcmlnU2V0
LmdldC5jYWxsKHRoaXMpO319KTsgfQogIGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoImlucHV0LnNkLCBpbnB1dCNucyIpLmZvckVhY2goZnVuY3Rpb24o
aSl7IGkudHlwZT0nZGF0ZSc7IH0pOwogIHN5bmMoKTsKfSkoKTsKPC9zY3JpcHQ+IiIiCl9NT1VTRV9CVE4gPSAiPGEgaWQ9J3J1bicgY2xhc3M9J2J0biBw
JyBocmVmPScjJyB0aXRsZT0ndmlhOi8vIOWNlOWumiDihpIg5ZWf5YuV5ZmoIFBTIOKGkiBweXRob24g5YuV6KmeIOKGkiDplosgVS9JKOWFiOi3keS4gOas
oSBJbnZva2UtVklBLUxhdW5jaCAtUmVnaXN0ZXJQcm90b2NvbCknPuWft+ihjCjmu5HpvKApPC9hPiA8YSBpZD0ncnVucGljaycgY2xhc3M9J2J0bicgaHJl
Zj0nIycgdGl0bGU9J+WFiOmWiyBXaW5kb3dzIOaqlOahiOmBuOWPluWZqCzpgbjliLDnmoTmqpTmjqXlnKjlj4PmlbjlvownPumBuOaqlOWft+ihjDwvYT4i
Cl9NT1VTRV9DU1MgPSAiPHN0eWxlPmEuYnRue2Rpc3BsYXk6aW5saW5lLWJsb2NrO3BhZGRpbmc6NHB4IDEwcHg7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1s
aW5lLCNlMGUwZTApO2JvcmRlci1yYWRpdXM6NnB4O2JhY2tncm91bmQ6I2ZmZjtjb2xvcjp2YXIoLS10eHQsIzFmMjkzNyk7dGV4dC1kZWNvcmF0aW9uOm5v
bmU7Zm9udC1zaXplOjExcHg7bWFyZ2luOjZweCA0cHggMCAwfWEuYnRuLnB7YmFja2dyb3VuZDp2YXIoLS1hY2MsIzI1NjNlYik7Y29sb3I6I2ZmZjtib3Jk
ZXItY29sb3I6dmFyKC0tYWNjLCMyNTYzZWIpfTwvc3R5bGU+IgoKCmRlZiB1aV9tb3VzZV9hcHBseShodG1sX3RleHQsIHN1Yik6CiAgICAiIiLlnKggPHRl
eHRhcmVhIGlkPSdjbWQn4oCmPjwvdGV4dGFyZWE+IOW+jOaPkuWFqeWAiyB2aWE6Ly8g5oyJ6YiVOzwvYm9keT4g5YmN5o+SIEpTO+aXpeacn+ashOaUuSB0
eXBlPWRhdGXjgILmspLmnInmjIfku6TmoYbnmoTpoIHkuI3li5XjgIIiIiIKICAgIGltcG9ydCByZSBhcyBfcmUKICAgIGlmICJpZD0nY21kJyIgbm90IGlu
IGh0bWxfdGV4dCBhbmQgJ2lkPSJjbWQiJyBub3QgaW4gaHRtbF90ZXh0OgogICAgICAgIHJldHVybiBodG1sX3RleHQKICAgIG91dCA9IF9yZS5zdWIociIo
PHRleHRhcmVhIGlkPVsnXCJdY21kWydcIl1bXj5dKj48L3RleHRhcmVhPikiLCBsYW1iZGEgbTogbS5ncm91cCgxKSArIF9NT1VTRV9CVE4sIGh0bWxfdGV4
dCwgY291bnQ9MSkKICAgIGpzID0gX01PVVNFX0pTICUgeyJzdWIiOiBfX2ltcG9ydF9fKCJqc29uIikuZHVtcHMoc3ViKX0KICAgIGkgPSBvdXQucmZpbmQo
IjwvYm9keT4iKQogICAgb3V0ID0gKG91dFs6aV0gKyBfTU9VU0VfQ1NTICsganMgKyBvdXRbaTpdKSBpZiBpID49IDAgZWxzZSBvdXQgKyBfTU9VU0VfQ1NT
ICsganMKICAgIHJldHVybiBvdXQKIyA9PT09PSBbVklBOlVJLU1PVVNFOkVORF0gPT09PT0KCgojID09PT09IFtWSUE6VUktTUFOSUZFU1Q6djAxMDBdIOWt
kOezu+e1sSBVL0kg5riF5ZauKOiHquWgsSk65YWl5Y+j6aCBIMK3IOmggeexpCDCtyDnh4ggwrcg5YuV6Kme5pW4IMK3IOaooeadv+WGijvmr43ns7vntbHl
haXlj6Plj6roroDmuIXllq7ntYTpoIEs5LiN5a+r5a2Q57O757Wx6aCBID09PT09CmRlZiB1aV9tYW5pZmVzdF93cml0ZShzdWIsIG91dF9kaXIsIGh0bWxf
cGF0aCwgbGFtcCwgZXh0cmE9Tm9uZSk6CiAgICBpbXBvcnQganNvbiBhcyBfaiwgZGF0ZXRpbWUgYXMgX2R0LCByZSBhcyBfcmUKICAgIGZyb20gcGF0aGxp
YiBpbXBvcnQgUGF0aCBhcyBfUAogICAgaHRtbF9wYXRoID0gX1AoaHRtbF9wYXRoKQogICAgdHJ5OgogICAgICAgIGggPSBodG1sX3BhdGgucmVhZF90ZXh0
KGVuY29kaW5nPSJ1dGYtOCIpCiAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICBoID0gIiIKICAgIG5hbWVzID0gW19yZS5zdWIociI8W14+XSs+IiwgIiIs
IHQpLnN0cmlwKCkgZm9yIHQgaW4gX3JlLmZpbmRhbGwociI8YnV0dG9uW14+XSpvbmNsaWNrPVwidGFiXChcZCssdGhpc1wpXCI+KC4qPyk8L2J1dHRvbj4i
LCBoKV0KICAgIHBhZ2VzID0gX3JlLmZpbmRhbGwociI8ZGl2IGNsYXNzPVwicGFnZVteXCJdKlwiW14+XSo+KC4qPyk8L2Rpdj4iLCBoLCBfcmUuUykKICAg
IHNyY3MgPSBbKChfcmUuc2VhcmNoKHIiPGlmcmFtZVtePl0qc3JjPVwiKFteXCJdKilcIiIsIHBnKSBvciBbTm9uZSwgIiJdKVsxXSkgZm9yIHBnIGluIHBh
Z2VzXQogICAgdGFicyA9IFt7Im5hbWUiOiBuLCAic3JjIjogKHNyY3NbaV0gaWYgaSA8IGxlbihzcmNzKSBlbHNlICIiKX0gZm9yIGksIG4gaW4gZW51bWVy
YXRlKG5hbWVzKV0KICAgIHRoZW1lID0gKF9yZS5zZWFyY2gociI8IS0tIHRoZW1lOihbXiA+XSspIC0tPiIsIGgpIG9yIFtOb25lLCAiZGVmYXVsdCJdKVsx
XQogICAgbSA9IHsic2NoZW1hIjogIlZJQS5VSS5NYW5pZmVzdC52MSIsICJzdWIiOiBzdWIsICJ0cyI6IF9kdC5kYXRldGltZS5ub3coKS5pc29mb3JtYXQo
dGltZXNwZWM9InNlY29uZHMiKSwgImVudHJ5IjogaHRtbF9wYXRoLm5hbWUsICJkaXIiOiBzdHIob3V0X2RpciksICJsYW1wIjogbGFtcCwgInRhYnMiOiB0
YWJzLCAidGhlbWUiOiB0aGVtZSwKICAgICAgICAgIm1vdXNlIjogImlkPSdydW4nIiBpbiBoLCAibGVmdF9wYW5lbCI6ICI8YXNpZGU+IiBpbiBofQogICAg
aWYgZXh0cmE6CiAgICAgICAgbS51cGRhdGUoZXh0cmEpCiAgICBmcCA9IF9QKG91dF9kaXIpIC8gKHN1YiArICJfVUlfTUFOSUZFU1QuanNvbiIpCiAgICBm
cC53cml0ZV90ZXh0KF9qLmR1bXBzKG0sIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJuIGZwCiMg
PT09PT0gW1ZJQTpVSS1NQU5JRkVTVDpFTkRdID09PT09CgoKIyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIAgdjAxMDQ6Y29uZmlnKOeoi+W8j+WkviDCtyDos4fmlpnluqspwrcgdWko5YWp6Z2i5p2/KSDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKX0NGRyA9ICJWSUFfQ29uZmlnX1NTT1RfdjAx
MDAuanNvbiIKCgpkZWYgY29uZmlnX2xvYWQoUDogZGljdCB8IE5vbmUgPSBOb25lKSAtPiBkaWN0OgogICAgUCA9IFAgb3IgX3BhdGhzKCkKICAgIGZwID0g
UFsicmVnaXN0cnkiXSAvIF9DRkcKICAgIGlmIGZwLmV4aXN0cygpOgogICAgICAgIHRyeToKICAgICAgICAgICAgcmV0dXJuIGpzb24ubG9hZHMoZnAucmVh
ZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciKSkKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcGFzcwogICAgY2ZnID0geyJzY2hl
bWEiOiAiVklBLkNvbmZpZy5TU09ULnYxIiwgInZlcnNpb24iOiAidjAxMDAiLCAiY3JlYXRlZF9hdCI6IF9ub3coKSwgInJ1bGUiOiAiVkNHQyDlj6rmnInl
hanntYToqK3lrpo656iL5byP5qqU5qGI5aS+KFZJQSDmoLkp6IiH6LOH5paZ5bqrO+aUueWLlSBoaXN0b3J5IOWPquWinjvlrZDns7vntbHlhorkuI3lnKjp
gJnoo6EiLAogICAgICAgICAgICJwcm9ncmFtIjogeyJyb290Ijogc3RyKFBbInJvb3QiXSksICJ1cGRhdGVkX2F0IjogX25vdygpfSwKICAgICAgICAgICAi
ZGIiOiB7ImtpbmQiOiAiZHVja2RiIiwgInBhdGgiOiBzdHIoUFsicm9vdCJdIC8gIlZJQV9EYXRhIiAvICJ2aWEuZHVja2RiIiksICJwYXJxdWV0X3Jvb3Qi
OiBzdHIoUFsicm9vdCJdIC8gIlZJQV9EYXRhIiAvICJwYXJxdWV0IiksICJtZW1vcnlfbGltaXQiOiAiMkdCIiwgInRocmVhZHMiOiA0LCAidXBkYXRlZF9h
dCI6IF9ub3coKX0sICJoaXN0b3J5IjogW119CiAgICBQWyJyZWdpc3RyeSJdLm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhpc3Rfb2s9VHJ1ZSkKICAgIGZwLndy
aXRlX3RleHQoanNvbi5kdW1wcyhjZmcsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJuIGNmZwoK
CmRlZiBjb25maWdfc2V0KHNlY3Rpb246IHN0ciwga2V5OiBzdHIsIHZhbHVlOiBzdHIsIFA6IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdDoKICAgIFAg
PSBQIG9yIF9wYXRocygpCiAgICBjZmcgPSBjb25maWdfbG9hZChQKQogICAgaWYgc2VjdGlvbiBub3QgaW4gKCJwcm9ncmFtIiwgImRiIik6CiAgICAgICAg
cmV0dXJuIHsib2siOiBGYWxzZSwgIndoeSI6ICLlj6rmnIkgcHJvZ3JhbSAvIGRiIOWFqee1hCJ9CiAgICBhbGxvd2VkID0geyJwcm9ncmFtIjogKCJyb290
IiwpLCAiZGIiOiAoImtpbmQiLCAicGF0aCIsICJwYXJxdWV0X3Jvb3QiLCAibWVtb3J5X2xpbWl0IiwgInRocmVhZHMiKX1bc2VjdGlvbl0KICAgIGlmIGtl
eSBub3QgaW4gYWxsb3dlZDoKICAgICAgICByZXR1cm4geyJvayI6IEZhbHNlLCAid2h5IjogIiVzIOWPquiDveaUuSAlcyIgJSAoc2VjdGlvbiwgIi8iLmpv
aW4oYWxsb3dlZCkpfQogICAgb2xkID0gY2ZnW3NlY3Rpb25dLmdldChrZXkpCiAgICBjZmdbc2VjdGlvbl1ba2V5XSA9IGludCh2YWx1ZSkgaWYga2V5ID09
ICJ0aHJlYWRzIiBhbmQgc3RyKHZhbHVlKS5pc2RpZ2l0KCkgZWxzZSB2YWx1ZQogICAgY2ZnW3NlY3Rpb25dWyJ1cGRhdGVkX2F0Il0gPSBfbm93KCkKICAg
IGNmZ1siaGlzdG9yeSJdLmFwcGVuZCh7InRzIjogX25vdygpLCAic2VjdGlvbiI6IHNlY3Rpb24sICJrZXkiOiBrZXksICJmcm9tIjogb2xkLCAidG8iOiBj
Zmdbc2VjdGlvbl1ba2V5XX0pCiAgICAoUFsicmVnaXN0cnkiXSAvIF9DRkcpLndyaXRlX3RleHQoanNvbi5kdW1wcyhjZmcsIGVuc3VyZV9hc2NpaT1GYWxz
ZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJuIHsib2siOiBUcnVlLCAic2VjdGlvbiI6IHNlY3Rpb24sICJrZXkiOiBrZXksICJm
cm9tIjogb2xkLCAidG8iOiBjZmdbc2VjdGlvbl1ba2V5XX0KCgpkZWYgdWkoUDogZGljdCB8IE5vbmUgPSBOb25lKSAtPiBkaWN0OgogICAgUCA9IFAgb3Ig
X3BhdGhzKCkKICAgIHJlcyA9IG1hdHJpeChQKQogICAgcGFjayA9IHBhc3RlX3BhY2socmVzKQogICAgd3JpdGVfb3V0cHV0cyhyZXMsIHBhY2ssIFApCiAg
ICBjZmcgPSBjb25maWdfbG9hZChQKQogICAgbWUgPSBzdHIoTUUpCiAgICBkZWYgbHAobCk6CiAgICAgICAgcmV0dXJuICI8aSBjbGFzcz0nbHAgJXMnIHN0
eWxlPSdiYWNrZ3JvdW5kOiVzJz48L2k+IiAlIChsLCBMQU1QLmdldChsLCBMQU1QWyJHUkFZIl0pKQogICAgZGVmIGYoc2VjdGlvbiwga2V5LCBzaXplPTQw
KToKICAgICAgICByZXR1cm4gIjxsYWJlbD4lczwvbGFiZWw+PGlucHV0IGlkPSclc18lcycgdmFsdWU9JyVzJyBzaXplPSclZCc+IiAlIChrZXksIHNlY3Rp
b24sIGtleSwgaHRtbC5lc2NhcGUoc3RyKGNmZ1tzZWN0aW9uXS5nZXQoa2V5LCAiIikpKSwgc2l6ZSkKICAgIGNhcmRzID0gIiIuam9pbigiPGRpdiBjbGFz
cz0nY2FyZCc+JXM8Yj4lczwvYj4gPHNtYWxsPiVzPC9zbWFsbD48L2Rpdj4iICUgKGxwKChyZXNbInN1YnMiXS5nZXQocykgb3Ige30pLmdldCgibGFtcCIs
ICJHUkFZIikpLCBzLCAoKHJlc1sic3VicyJdLmdldChzKSBvciB7fSkuZ2V0KCJ0cyIpIG9yICLmnKrot5EiKSkgZm9yIHMgaW4gU1VCUykKICAgIHBhZ2Ug
PSAiIiI8IWRvY3R5cGUgaHRtbD48aHRtbCBsYW5nPSJ6aC1IYW50Ij48aGVhZD48bWV0YSBjaGFyc2V0PSJ1dGYtOCI+PG1ldGEgbmFtZT0idmlld3BvcnQi
IGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCxpbml0aWFsLXNjYWxlPTEiPjx0aXRsZT5WQ0dDIFUvSTwvdGl0bGU+CjxzdHlsZT46cm9vdHstLWxpbmU6
I2UwZTBlMDstLXBhbmVsOiNmN2Y3Zjc7LS10eHQ6IzFmMjkzNzstLWRpbTojNmI3MjgwOy0tYWNjOiMyNTYzZWJ9Ym9keXtmb250LWZhbWlseToiTWljcm9z
b2Z0IEpoZW5nSGVpIFVJIiwiU2Vnb2UgVUkiLEFyaWFsO2NvbG9yOnZhcigtLXR4dCk7bWFyZ2luOjA7Zm9udC1zaXplOjEycHg7YmFja2dyb3VuZDojZmZm
O2hlaWdodDoxMDB2aDtkaXNwbGF5OmdyaWQ7Z3JpZC10ZW1wbGF0ZS1jb2x1bW5zOjMyMHB4IDFmcjtncmlkLXRlbXBsYXRlLXJvd3M6YXV0byAxZnJ9Cmhl
YWRlcntncmlkLWNvbHVtbjoxLzM7cGFkZGluZzo4cHggMTJweDtib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1saW5lKTtkaXNwbGF5OmZsZXg7Z2Fw
OjEycHg7YWxpZ24taXRlbXM6Y2VudGVyfWhlYWRlciBoMXtmb250LXNpemU6MTVweDttYXJnaW46MH1oZWFkZXIgc21hbGx7Y29sb3I6dmFyKC0tZGltKX1h
c2lkZXtib3JkZXItcmlnaHQ6MXB4IHNvbGlkIHZhcigtLWxpbmUpO3BhZGRpbmc6MTBweDtvdmVyZmxvdzphdXRvO2JhY2tncm91bmQ6dmFyKC0tcGFuZWwp
fW1haW57ZGlzcGxheTpmbGV4O2ZsZXgtZGlyZWN0aW9uOmNvbHVtbjtvdmVyZmxvdzpoaWRkZW59CmxhYmVse2Rpc3BsYXk6YmxvY2s7Zm9udC1zaXplOjEx
cHg7Y29sb3I6dmFyKC0tZGltKTttYXJnaW46OHB4IDAgMnB4fWlucHV0LHRleHRhcmVhe3dpZHRoOjEwMCUlO2JveC1zaXppbmc6Ym9yZGVyLWJveDtmb250
OjEycHggQ29uc29sYXMsbW9ub3NwYWNlO3BhZGRpbmc6NHB4IDZweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6NnB4O2Jh
Y2tncm91bmQ6I2ZmZn1idXR0b257cGFkZGluZzo0cHggMTBweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JhY2tncm91bmQ6I2ZmZjtib3JkZXIt
cmFkaXVzOjZweDtjdXJzb3I6cG9pbnRlcjtmb250LXNpemU6MTFweDttYXJnaW46NnB4IDRweCAwIDB9Ci5jYXJke2JhY2tncm91bmQ6I2ZmZjtib3JkZXI6
MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OHB4O3BhZGRpbmc6NnB4IDhweDttYXJnaW46NnB4IDA7Zm9udC1zaXplOjExLjVweH0uZGlt
e2NvbG9yOnZhcigtLWRpbSl9LnRhYnN7ZGlzcGxheTpmbGV4O2dhcDo0cHg7cGFkZGluZzo2cHggMTBweDtib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIo
LS1saW5lKTtmbGV4LXdyYXA6d3JhcH0udGFicyBidXR0b24ub257YmFja2dyb3VuZDojMTExODI3O2NvbG9yOiNmZmY7Ym9yZGVyLWNvbG9yOiMxMTE4Mjd9
LnBhZ2Vze2ZsZXg6MTtwb3NpdGlvbjpyZWxhdGl2ZX0ucGFnZXtwb3NpdGlvbjphYnNvbHV0ZTtpbnNldDowO2Rpc3BsYXk6bm9uZX0ucGFnZS5vbntkaXNw
bGF5OmJsb2NrfWlmcmFtZXt3aWR0aDoxMDAlJTtoZWlnaHQ6MTAwJSU7Ym9yZGVyOjB9Ci5scHtkaXNwbGF5OmlubGluZS1ibG9jazt3aWR0aDoxMXB4O2hl
aWdodDoxMXB4O2JvcmRlci1yYWRpdXM6NTAlJTt2ZXJ0aWNhbC1hbGlnbjptaWRkbGU7bWFyZ2luLXJpZ2h0OjRweH0ubHAuUkVEe2FuaW1hdGlvbjpibCAy
LjRzIGVhc2UtaW4tb3V0IGluZmluaXRlfUBrZXlmcmFtZXMgYmx7MCUlLDEwMCUle29wYWNpdHk6MX01MCUle29wYWNpdHk6LjI1fX1AbWVkaWEobWF4LXdp
ZHRoOjgwMHB4KXtib2R5e2dyaWQtdGVtcGxhdGUtY29sdW1uczoxZnI7Z3JpZC10ZW1wbGF0ZS1yb3dzOmF1dG8gYXV0byAxZnJ9YXNpZGV7Ym9yZGVyLXJp
Z2h0OjA7Ym9yZGVyLWJvdHRvbToxcHggc29saWQgdmFyKC0tbGluZSk7bWF4LWhlaWdodDo0MHZofX08L3N0eWxlPjwvaGVhZD48Ym9keT4KPGhlYWRlcj48
aDE+VkNHQyDCtyDmr43ns7vntbE8L2gxPjxzbWFsbD4lcyDCtyDlt6Y65Y+q5pyJ5YWp57WE6Kit5a6aKOeoi+W8j+aqlOahiOWkviDCtyDos4fmlpnluqsp
wrcg5Y+zOuWkmumggeWxleekuiDCtyA8c3BhbiBzdHlsZT0iY29sb3I6IzE2YTM0YSI+4pePPC9zcGFuPue2oCA8c3BhbiBzdHlsZT0iY29sb3I6I2Y1OWUw
YiI+4pePPC9zcGFuPum7gyA8c3BhbiBzdHlsZT0iY29sb3I6I2RjMjYyNiI+4pePPC9zcGFuPue0hSA8c3BhbiBzdHlsZT0iY29sb3I6IzljYTNhZiI+4peP
PC9zcGFuPueBsDwvc21hbGw+PC9oZWFkZXI+Cjxhc2lkZT4KICA8ZGl2IGNsYXNzPSdjYXJkJz48Yj7nqIvlvI/mqpTmoYjlpL48L2I+JXM8YnV0dG9uIG9u
Y2xpY2s9InNldHYoJ3Byb2dyYW0nLCdyb290JykiPuaUuTwvYnV0dG9uPjwvZGl2PgogIDxkaXYgY2xhc3M9J2NhcmQnPjxiPuizh+aWmeW6qzwvYj4lcyVz
JXMlcyVzPGJ1dHRvbiBvbmNsaWNrPSJzZXR2KCdkYicsJ3BhdGgnKSI+5pS5IHBhdGg8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InNldHYoJ2RiJywncGFy
cXVldF9yb290JykiPuaUuSBwYXJxdWV0PC9idXR0b24+PGJ1dHRvbiBvbmNsaWNrPSJzZXR2KCdkYicsJ21lbW9yeV9saW1pdCcpIj7mlLkgbWVtb3J5PC9i
dXR0b24+PGJ1dHRvbiBvbmNsaWNrPSJzZXR2KCdkYicsJ3RocmVhZHMnKSI+5pS5IHRocmVhZHM8L2J1dHRvbj48L2Rpdj4KICA8bGFiZWw+5oyH5LukKOiy
vOWIsCBQb3dlclNoZWxsKTwvbGFiZWw+PHRleHRhcmVhIGlkPSdjbWQnIHJvd3M9JzQnIHJlYWRvbmx5PjwvdGV4dGFyZWE+PGJ1dHRvbiBvbmNsaWNrPSdj
b3B5aXQoKSc+6KSH6KO9PC9idXR0b24+CiAgJXMKICA8c2NyaXB0PnZhciBQWT0lcztmdW5jdGlvbiBzZXR2KHMsayl7dmFyIHY9ZG9jdW1lbnQuZ2V0RWxl
bWVudEJ5SWQocysnXycraykudmFsdWU7ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2NtZCcpLnZhbHVlPSckZW52OlZJQV9GUk9NX1ZDR0M9IllFUyI7IHB5
dGhvbiAiJytQWSsnIiBjb25maWcgc2V0IC0tc2VjdGlvbiAnK3MrJyAtLWtleSAnK2srJyAtLXZhbHVlICInK3YrJyInfQogIGZ1bmN0aW9uIGNvcHlpdCgp
e3ZhciB0PWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdjbWQnKTt0LnNlbGVjdCgpO3RyeXtuYXZpZ2F0b3IuY2xpcGJvYXJkLndyaXRlVGV4dCh0LnZhbHVl
KX1jYXRjaChlKXtkb2N1bWVudC5leGVjQ29tbWFuZCgnY29weScpfX0KICBmdW5jdGlvbiB0YWIoaSxiKXtkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCcu
cGFnZScpLmZvckVhY2goZnVuY3Rpb24ocCxqKXtwLmNsYXNzTGlzdC50b2dnbGUoJ29uJyxpPT09ail9KTtkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCcu
dGFicyBidXR0b24nKS5mb3JFYWNoKGZ1bmN0aW9uKHgpe3guY2xhc3NMaXN0LnJlbW92ZSgnb24nKX0pO2IuY2xhc3NMaXN0LmFkZCgnb24nKX08L3Njcmlw
dD4KPC9hc2lkZT4KPG1haW4+CiAgPGRpdiBjbGFzcz0idGFicyI+PGJ1dHRvbiBjbGFzcz0ib24iIG9uY2xpY2s9InRhYigwLHRoaXMpIj7lgaXlurfnn6np
maM8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InRhYigxLHRoaXMpIj7nkrDlooPlt6Xlhbc8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InRhYigyLHRoaXMp
Ij7ovJTliqnlt6Xlhbc8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InRhYigzLHRoaXMpIj7lhajmqpTnn6npmaM8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9
InRhYig0LHRoaXMpIj5WREYgVS9JPC9idXR0b24+PGJ1dHRvbiBvbmNsaWNrPSJ0YWIoNSx0aGlzKSI+VlJOIFUvSTwvYnV0dG9uPjwvZGl2PgogIDxkaXYg
Y2xhc3M9InBhZ2VzIj4KICAgIDxkaXYgY2xhc3M9InBhZ2Ugb24iPjxpZnJhbWUgc3JjPSJIRUFMVEhfTUFUUklYX2xhdGVzdC5odG1sIj48L2lmcmFtZT48
L2Rpdj4KICAgIDxkaXYgY2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi92Y2djX2Vudi9FTlZfTUFUUklYX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rp
dj4KICAgIDxkaXYgY2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi92Y2djX3Rvb2xraXQvVE9PTEtJVF9NQVRSSVhfbGF0ZXN0Lmh0bWwiPjwvaWZyYW1l
PjwvZGl2PgogICAgPGRpdiBjbGFzcz0icGFnZSI+PGlmcmFtZSBzcmM9Ii4uL3ZjZ2NfbWF0cml4L0ZJTEVfTUFUUklYX2xhdGVzdC5odG1sIj48L2lmcmFt
ZT48L2Rpdj4KICAgIDxkaXYgY2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi8uLi92ZGYvVkRGX1VJX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4K
ICAgIDxkaXYgY2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi8uLi92cm4vVlJOX1VJX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4KICA8L2Rpdj4K
PC9tYWluPjwvYm9keT48L2h0bWw+IiIiICUgKHJlc1sidHMiXSwgZigicHJvZ3JhbSIsICJyb290IiksIGYoImRiIiwgImtpbmQiLCAxMiksIGYoImRiIiwg
InBhdGgiKSwgZigiZGIiLCAicGFycXVldF9yb290IiksIGYoImRiIiwgIm1lbW9yeV9saW1pdCIsIDgpLCBmKCJkYiIsICJ0aHJlYWRzIiwgNCksIGNhcmRz
LCBqc29uLmR1bXBzKG1lKSkKICAgIGZwID0gUFsib3V0Il0gLyAiVkNHQ19VSV9sYXRlc3QuaHRtbCIKICAgIGZwLndyaXRlX3RleHQodWlfbW91c2VfYXBw
bHkodWlfdGhlbWVfYXBwbHkocGFnZSwgUFsicm9vdCJdKSwgIlZDR0MiKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIGhtID0gUFsib3V0Il0gLyAiSEVBTFRI
X01BVFJJWF9sYXRlc3QuaHRtbCIKICAgIGlmIGhtLmV4aXN0cygpOgogICAgICAgIGhtLndyaXRlX3RleHQodWlfdGhlbWVfYXBwbHkoaG0ucmVhZF90ZXh0
KGVuY29kaW5nPSJ1dGYtOCIpLCBQWyJyb290Il0pLCBlbmNvZGluZz0idXRmLTgiKQogICAgb3BlbmVkID0gRmFsc2UKICAgIGlmIG9zLmVudmlyb24uZ2V0
KCJWSUFfTk9fT1BFTiIpICE9ICIxIiBhbmQgb3MubmFtZSA9PSAibnQiOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3Muc3RhcnRmaWxlKHN0cihmcCkp
ICAjIHR5cGU6IGlnbm9yZVthdHRyLWRlZmluZWRdCiAgICAgICAgICAgIG9wZW5lZCA9IFRydWUKICAgICAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICAg
ICAgcGFzcwogICAgcmV0dXJuIHsidmVyYiI6ICJ1aSIsICJodG1sIjogc3RyKGZwKSwgImxhbXAiOiByZXNbImxhbXAiXSwgIm9wZW5lZCI6IG9wZW5lZH0K
CgpfTUFJTl8wMTAzID0gbWFpbgoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9GUk9NX1ZDR0MiKSAh
PSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJuIDIKICAgIGEgPSBs
aXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQoKICAgIGRlZiBvcHQoZmxhZywgZGVmYXVsdD1Ob25lKToKICAgICAgICByZXR1
cm4gYVthLmluZGV4KGZsYWcpICsgMV0gaWYgZmxhZyBpbiBhIGFuZCBhLmluZGV4KGZsYWcpICsgMSA8IGxlbihhKSBlbHNlIGRlZmF1bHQKICAgIGlmIGFb
OjFdID09IFsiY29uZmlnIl06CiAgICAgICAgaWYgYVsxOjJdID09IFsic2V0Il06CiAgICAgICAgICAgIHIgPSBjb25maWdfc2V0KG9wdCgiLS1zZWN0aW9u
IiwgIiIpLCBvcHQoIi0ta2V5IiwgIiIpLCBvcHQoIi0tdmFsdWUiLCAiIikpCiAgICAgICAgICAgIHByaW50KCJb6KiIXSB2Y2djIGNvbmZpZyBzZXQgwrcg
JXMiICUganNvbi5kdW1wcyhyLCBlbnN1cmVfYXNjaWk9RmFsc2UpKQogICAgICAgICAgICByZXR1cm4gMCBpZiByLmdldCgib2siKSBlbHNlIDEKICAgICAg
ICBjID0gY29uZmlnX2xvYWQoKQogICAgICAgIHByaW50KCJb6KiIXSB2Y2djIGNvbmZpZyDCtyDnqIvlvI/lpL4gJXMgwrcgZGIgJXMgJXMgwrcgcGFycXVl
dCAlcyDCtyBtZW1vcnkgJXMgwrcgdGhyZWFkcyAlcyDCtyBoaXN0b3J5ICVkIiAlIChjWyJwcm9ncmFtIl1bInJvb3QiXSwgY1siZGIiXVsia2luZCJdLCBj
WyJkYiJdWyJwYXRoIl0sIGNbImRiIl1bInBhcnF1ZXRfcm9vdCJdLCBjWyJkYiJdWyJtZW1vcnlfbGltaXQiXSwgY1siZGIiXVsidGhyZWFkcyJdLCBsZW4o
Y1siaGlzdG9yeSJdKSkpCiAgICAgICAgcmV0dXJuIDAKICAgIGlmIGFbOjFdID09IFsidGhlbWUiXToKICAgICAgICByID0gdWlfdGhlbWVfaW5pdChfcGF0
aHMoKVsicm9vdCJdLCBhcHBseT0oIi0tZHJ5IiBub3QgaW4gYSkpCiAgICAgICAgdCwgYm9vayA9IHVpX3RoZW1lX2xvYWQoX3BhdGhzKClbInJvb3QiXSkK
ICAgICAgICBwcmludCgiW+ioiF0gdmNnYyB0aGVtZSDCtyAlcyDCtyAlcyDCtyB0b2tlbnMgJWQgwrcg54eI6Y6WIDQgwrcg5o+b5qih5p2/ID0g5Ye65paw
54mI5YaK5pS5IHRva2VucyIgJSAoclsic3RhdHVzIl0sIHJbImZpbGUiXSwgbGVuKHQpKSkKICAgICAgICByZXR1cm4gMAogICAgaWYgYVs6MV0gPT0gWyJ1
aSJdOgogICAgICAgIHVpX3RoZW1lX2luaXQoX3BhdGhzKClbInJvb3QiXSwgYXBwbHk9VHJ1ZSkKICAgICAgICB1ID0gdWkoKQogICAgICAgIHByaW50KCJb
6KiIXSB2Y2djIHVpIMK3ICVzIMK3ICVzIMK3IOW3sumWiyAlcyIgJSAodVsiaHRtbCJdLCB1WyJsYW1wIl0sIHVbIm9wZW5lZCJdKSkKICAgICAgICBwcmlu
dCgiICBbVS9JXSAlcyIgJSB1WyJodG1sIl0pCiAgICAgICAgcmV0dXJuIDAKICAgIHJldHVybiBfTUFJTl8wMTAzKGFyZ3YpCgoKCgpkZWYgcG9ydGFsKFA6
IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdDoKICAgICIiIuWFpeWPo+mggTrlj6roroDkuInku70gVUkg5riF5Zau57WE6aCB44CC5a2Q57O757Wx5rKS
6LeRIHVpIOWwseeBsCzkuI3lgYfoo53jgIIiIiIKICAgIFAgPSBQIG9yIF9wYXRocygpCiAgICByZXBvcnRzID0gUFsicm9vdCJdIC8gIlZJQV9SZXBvcnRz
IgogICAgc3VicyA9IFsoIlZDR0MiLCBQWyJvdXQiXSksICgiVkRGIiwgcmVwb3J0cyAvICJ2ZGYiKSwgKCJWUk4iLCByZXBvcnRzIC8gInZybiIpXQogICAg
bWFucyA9IHt9CiAgICBmb3Igc3ViLCBkIGluIHN1YnM6CiAgICAgICAgZnAgPSBkIC8gKHN1YiArICJfVUlfTUFOSUZFU1QuanNvbiIpCiAgICAgICAgdHJ5
OgogICAgICAgICAgICBtYW5zW3N1Yl0gPSBqc29uLmxvYWRzKGZwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpIGlmIGZwLmV4aXN0cygpIGVs
c2UgTm9uZQogICAgICAgIGV4Y2VwdCBWYWx1ZUVycm9yOgogICAgICAgICAgICBtYW5zW3N1Yl0gPSBOb25lCiAgICBvdXRfZnAgPSByZXBvcnRzIC8gIlZJ
QV9VSV9sYXRlc3QuaHRtbCIKICAgIGRlZiByZWwoZCwgbmFtZSk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICByZXR1cm4gKFBhdGgoZCkgLyBuYW1lKS5y
ZXNvbHZlKCkucmVsYXRpdmVfdG8ob3V0X2ZwLnBhcmVudC5yZXNvbHZlKCkpLmFzX3Bvc2l4KCkKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAg
ICAgICAgcmV0dXJuIHN0cihQYXRoKGQpIC8gbmFtZSkKICAgIGRlZiBscChsKToKICAgICAgICByZXR1cm4gIjxpIGNsYXNzPSdscCAlcycgc3R5bGU9J2Jh
Y2tncm91bmQ6JXMnPjwvaT4iICUgKGwsIExBTVAuZ2V0KGwsIExBTVBbIkdSQVkiXSkpCiAgICBidG5zLCBwYWdlcyA9IFtdLCBbXQogICAgZm9yIGksIChz
dWIsIGQpIGluIGVudW1lcmF0ZShzdWJzKToKICAgICAgICBtID0gbWFuc1tzdWJdCiAgICAgICAgbGFtcCA9IChtIG9yIHt9KS5nZXQoImxhbXAiLCAiR1JB
WSIpCiAgICAgICAgc3JjID0gcmVsKGQsIG1bImVudHJ5Il0pIGlmIG0gZWxzZSAiIgogICAgICAgIHRzID0gKG0gb3Ige30pLmdldCgidHMiLCAi5pyq6LeR
IHVpIikKICAgICAgICBudGFiID0gbGVuKChtIG9yIHt9KS5nZXQoInRhYnMiLCBbXSkpCiAgICAgICAgYnRucy5hcHBlbmQoIjxidXR0b24gY2xhc3M9J3N5
c2J0biVzJyBvbmNsaWNrPVwicGljayglZCx0aGlzKVwiPiVzPGI+JXM8L2I+PHNtYWxsPiVzIMK3IOmggeexpCAlZCDCtyAlczwvc21hbGw+PC9idXR0b24+
IiAlICgiIG9uIiBpZiBpID09IDAgZWxzZSAiIiwgaSwgbHAobGFtcCksIHN1YiwgdHNbOjE2XSwgbnRhYiwgaHRtbC5lc2NhcGUoKG0gb3Ige30pLmdldCgi
dGhlbWUiLCAi4oCUIikpKSkKICAgICAgICBwYWdlcy5hcHBlbmQoIjxkaXYgY2xhc3M9J3BhZ2Ulcyc+JXM8L2Rpdj4iICUgKCIgb24iIGlmIGkgPT0gMCBl
bHNlICIiLCAoIjxpZnJhbWUgc3JjPSclcyc+PC9pZnJhbWU+IiAlIGh0bWwuZXNjYXBlKHNyYykpIGlmIHNyYyBlbHNlICI8ZGl2IGNsYXNzPSdlbXB0eSc+
JXMg5bCa5pyq55SiIFUvSTrlnKjllZ/li5Xlmajot5EgLVN1YiAlcyAtVmVyYiB1aTwvZGl2PiIgJSAoc3ViLCBzdWIpKSkKICAgIHBhZ2UgPSAiIiI8IWRv
Y3R5cGUgaHRtbD48aHRtbCBsYW5nPSJ6aC1IYW50Ij48aGVhZD48bWV0YSBjaGFyc2V0PSJ1dGYtOCI+PG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9
IndpZHRoPWRldmljZS13aWR0aCxpbml0aWFsLXNjYWxlPTEiPjx0aXRsZT5WSUEgVS9JPC90aXRsZT4KPHN0eWxlPjpyb290ey0tbGluZTojZTBlMGUwOy0t
cGFuZWw6I2Y3ZjdmNzstLXR4dDojMWYyOTM3Oy0tZGltOiM2YjcyODA7LS1hY2M6IzI1NjNlYjstLWhlYWQ6IzExMTgyN31ib2R5e2ZvbnQtZmFtaWx5OiJN
aWNyb3NvZnQgSmhlbmdIZWkgVUkiLCJTZWdvZSBVSSIsQXJpYWw7bWFyZ2luOjA7aGVpZ2h0OjEwMHZoO2Rpc3BsYXk6ZmxleDtmbGV4LWRpcmVjdGlvbjpj
b2x1bW47Y29sb3I6dmFyKC0tdHh0KTtmb250LXNpemU6MTJweDtiYWNrZ3JvdW5kOiNmZmZ9CmhlYWRlcntkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6c3Ry
ZXRjaDtnYXA6NnB4O3BhZGRpbmc6NnB4IDEwcHg7Ym9yZGVyLWJvdHRvbToxcHggc29saWQgdmFyKC0tbGluZSk7YmFja2dyb3VuZDp2YXIoLS1wYW5lbCl9
aGVhZGVyIGgxe2ZvbnQtc2l6ZToxNHB4O21hcmdpbjowIDEycHggMCAwO2FsaWduLXNlbGY6Y2VudGVyfQouc3lzYnRue2Rpc3BsYXk6ZmxleDtmbGV4LWRp
cmVjdGlvbjpjb2x1bW47YWxpZ24taXRlbXM6ZmxleC1zdGFydDtnYXA6MnB4O3BhZGRpbmc6NnB4IDEycHg7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5l
KTtib3JkZXItcmFkaXVzOjhweDtiYWNrZ3JvdW5kOiNmZmY7Y3Vyc29yOnBvaW50ZXI7bWluLXdpZHRoOjE2MHB4O3RleHQtYWxpZ246bGVmdH0uc3lzYnRu
Lm9ue2JvcmRlci1jb2xvcjp2YXIoLS1hY2MpO2JveC1zaGFkb3c6MCAwIDAgMnB4IHZhcigtLWFjYykgaW5zZXR9LnN5c2J0biBzbWFsbHtjb2xvcjp2YXIo
LS1kaW0pO2ZvbnQtc2l6ZToxMC41cHh9Ci5wYWdlc3tmbGV4OjE7cG9zaXRpb246cmVsYXRpdmV9LnBhZ2V7cG9zaXRpb246YWJzb2x1dGU7aW5zZXQ6MDtk
aXNwbGF5Om5vbmV9LnBhZ2Uub257ZGlzcGxheTpibG9ja31pZnJhbWV7d2lkdGg6MTAwJSU7aGVpZ2h0OjEwMCUlO2JvcmRlcjowfS5lbXB0eXtwYWRkaW5n
OjIwcHg7Y29sb3I6dmFyKC0tZGltKX0KLmxwe2Rpc3BsYXk6aW5saW5lLWJsb2NrO3dpZHRoOjExcHg7aGVpZ2h0OjExcHg7Ym9yZGVyLXJhZGl1czo1MCUl
O3ZlcnRpY2FsLWFsaWduOm1pZGRsZTttYXJnaW4tcmlnaHQ6NHB4fS5scC5SRUR7YW5pbWF0aW9uOmJsIDIuNHMgZWFzZS1pbi1vdXQgaW5maW5pdGV9QGtl
eWZyYW1lcyBibHswJSUsMTAwJSV7b3BhY2l0eToxfTUwJSV7b3BhY2l0eTouMjV9fQpAbWVkaWEobWF4LXdpZHRoOjcwMHB4KXtoZWFkZXJ7ZmxleC13cmFw
OndyYXB9LnN5c2J0bnttaW4td2lkdGg6NDYlJX19PC9zdHlsZT48L2hlYWQ+PGJvZHk+CjxoZWFkZXI+PGgxPlZJQTwvaDE+JXM8c3BhbiBzdHlsZT0iYWxp
Z24tc2VsZjpjZW50ZXI7Y29sb3I6dmFyKC0tZGltKTttYXJnaW4tbGVmdDphdXRvIj4lcyDCtyDlhaXlj6Plj6roroDlkITns7vntbHoh6rloLHmuIXllq47
6aCB6Zqo5ZCEIG1hbmFnZXIg6K6KLOiJsumaqOaooeadv+WGiuiuijwvc3Bhbj48L2hlYWRlcj4KPGRpdiBjbGFzcz0icGFnZXMiPiVzPC9kaXY+CjxzY3Jp
cHQ+ZnVuY3Rpb24gcGljayhpLGIpe2RvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoJy5wYWdlJykuZm9yRWFjaChmdW5jdGlvbihwLGope3AuY2xhc3NMaXN0
LnRvZ2dsZSgnb24nLGk9PT1qKX0pO2RvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoJy5zeXNidG4nKS5mb3JFYWNoKGZ1bmN0aW9uKHgpe3guY2xhc3NMaXN0
LnJlbW92ZSgnb24nKX0pO2IuY2xhc3NMaXN0LmFkZCgnb24nKX08L3NjcmlwdD48L2JvZHk+PC9odG1sPiIiIiAlICgiIi5qb2luKGJ0bnMpLCBfbm93KCks
ICIiLmpvaW4ocGFnZXMpKQogICAgb3V0X2ZwLnBhcmVudC5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICBvdXRfZnAud3JpdGVfdGV4
dCh1aV90aGVtZV9hcHBseShwYWdlLCBQWyJyb290Il0pLCBlbmNvZGluZz0idXRmLTgiKQogICAgb3BlbmVkID0gRmFsc2UKICAgIGlmIG9zLmVudmlyb24u
Z2V0KCJWSUFfTk9fT1BFTiIpICE9ICIxIiBhbmQgb3MubmFtZSA9PSAibnQiOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3Muc3RhcnRmaWxlKHN0cihv
dXRfZnApKSAgIyB0eXBlOiBpZ25vcmVbYXR0ci1kZWZpbmVkXQogICAgICAgICAgICBvcGVuZWQgPSBUcnVlCiAgICAgICAgZXhjZXB0IE9TRXJyb3I6CiAg
ICAgICAgICAgIHBhc3MKICAgIHJldHVybiB7InZlcmIiOiAicG9ydGFsIiwgImh0bWwiOiBzdHIob3V0X2ZwKSwgInN1YnMiOiB7czogKChtYW5zW3NdIG9y
IHt9KS5nZXQoImxhbXAiLCAiR1JBWSIpKSBmb3IgcywgXyBpbiBzdWJzfSwgIm1pc3NpbmciOiBbcyBmb3IgcywgXyBpbiBzdWJzIGlmIG5vdCBtYW5zW3Nd
XSwgIm9wZW5lZCI6IG9wZW5lZH0KCgpfTUFJTl8wMTA2ID0gbWFpbgoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5n
ZXQoIlZJQV9GUk9NX1ZDR0MiKSAhPSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAg
ICAgcmV0dXJuIDIKICAgIGEgPSBsaXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQogICAgaWYgYVs6MV0gPT0gWyJwb3J0YWwi
XToKICAgICAgICByID0gcG9ydGFsKCkKICAgICAgICBwcmludCgiW+ioiF0gdmNnYyBwb3J0YWwgwrcgJXMgwrcgJXMgwrcg5pyq6LeRIHVpOiVzIMK3IOW3
sumWiyAlcyIgJSAoclsiaHRtbCJdLCAiICIuam9pbigiJXM9JXMiICUga3YgZm9yIGt2IGluIHJbInN1YnMiXS5pdGVtcygpKSwgIiwiLmpvaW4oclsibWlz
c2luZyJdKSBvciAi54ShIiwgclsib3BlbmVkIl0pKQogICAgICAgIHByaW50KCIgIFtVL0ldICVzIiAlIHJbImh0bWwiXSkKICAgICAgICByZXR1cm4gMAog
ICAgaWYgYVs6MV0gPT0gWyJ1aSJdOgogICAgICAgIHJjID0gX01BSU5fMDEwNihhKQogICAgICAgIHRyeToKICAgICAgICAgICAgUCA9IF9wYXRocygpCiAg
ICAgICAgICAgIHVpX21hbmlmZXN0X3dyaXRlKCJWQ0dDIiwgUFsib3V0Il0sIFBbIm91dCJdIC8gIlZDR0NfVUlfbGF0ZXN0Lmh0bWwiLCAoanNvbi5sb2Fk
cygoUFsib3V0Il0gLyAiSEVBTFRIX01BVFJJWF9sYXRlc3QuanNvbiIpLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpLmdldCgibGFtcCIsICJH
UkFZIikgaWYgKFBbIm91dCJdIC8gIkhFQUxUSF9NQVRSSVhfbGF0ZXN0Lmpzb24iKS5leGlzdHMoKSBlbHNlICJHUkFZIiksIHsibWFuYWdlciI6IE1FLm5h
bWV9KQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZXhjOiAgIyBub3FhOiBCTEUwMDEKICAgICAgICAgICAgcHJpbnQoIiAgW+azqF0gVkNHQyDmuIXl
lq7mnKrlr6s6JXMiICUgZXhjKQogICAgICAgIHJldHVybiByYwogICAgcmV0dXJuIF9NQUlOXzAxMDYoYSkKCgoKCiMg4pSA4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSAIHYwMTA4OnJlc3RvcmVwb2ludCjkuInns7vntbHlgaXlurfp
goTljp/pu54s6YCy6auY6aKo6Zqq5ris6Kmm5YmNKSDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIAKZGVmIHJlc3RvcmVwb2ludF9tYWtlKFA6IGRpY3QgfCBOb25lID0gTm9uZSwgbm90ZTogc3RyID0gIiIsIGdpdF9zaGE6IHN0
ciA9ICIiLCBhbGxvd195ZWxsb3c6IGJvb2wgPSBUcnVlLCBmb3JjZTogYm9vbCA9IEZhbHNlKSAtPiBkaWN0OgogICAgaW1wb3J0IGhhc2hsaWIKICAgIGlt
cG9ydCBzaHV0aWwKICAgIGltcG9ydCB6aXBmaWxlCiAgICBQID0gUCBvciBfcGF0aHMoKQogICAgbm93ID0gX25vdygpCiAgICBzdGFtcCA9IG5vdy5yZXBs
YWNlKCItIiwgIiIpLnJlcGxhY2UoIjoiLCAiIilbOjE1XQogICAgcmVwb3J0cyA9IFBbInJvb3QiXSAvICJWSUFfUmVwb3J0cyIKICAgIHJlcyA9IG1hdHJp
eChQKQogICAgbGFtcHMgPSB7czogKChyZXNbInN1YnMiXS5nZXQocykgb3Ige30pLmdldCgibGFtcCIpIG9yICJHUkFZIikgZm9yIHMgaW4gU1VCU30KICAg
IHJlZHMgPSBbcyBmb3IgcywgbCBpbiBsYW1wcy5pdGVtcygpIGlmIGwgPT0gIlJFRCJdCiAgICBncmF5cyA9IFtzIGZvciBzLCBsIGluIGxhbXBzLml0ZW1z
KCkgaWYgbCA9PSAiR1JBWSJdCiAgICBvdXQgPSB7InZlcmIiOiAicmVzdG9yZXBvaW50IiwgInN0YW1wIjogc3RhbXAsICJ0cyI6IG5vdywgImxhbXBzIjog
bGFtcHMsICJyZWRzIjogcmVkcywgImdyYXlzIjogZ3JheXMsICJub3RlIjogbm90ZSwgImdpdF9zaGEiOiBnaXRfc2hhfQogICAgaWYgKHJlZHMgb3IgZ3Jh
eXMgb3IgKG5vdCBhbGxvd195ZWxsb3cgYW5kIGFueShsID09ICJZRUxMT1ciIGZvciBsIGluIGxhbXBzLnZhbHVlcygpKSkpIGFuZCBub3QgZm9yY2U6CiAg
ICAgICAgb3V0LnVwZGF0ZShzdGF0dXM9IlJFRlVTRUQiLCB3aHk9Iuaciee0hSAlcyAvIOacqui3kSAlczrpgoTljp/pu57lj6rpjpblgaXlurfnmoTni4Dm
hYs75L+u5LqG5YaN5L6GLOaIliAtLWZvcmNlIOS4puWvq+aYjueQhueUsSIgJSAocmVkcywgZ3JheXMpLCBsYW1wPSJSRUQiKQogICAgICAgIHJldHVybiBv
dXQKICAgIHJwX2RpciA9IFBbInJvb3QiXSAvICJWSUFfUmVzdG9yZSIKICAgIHJwX2Rpci5ta2RpcihleGlzdF9vaz1UcnVlKQogICAgenBhdGggPSBycF9k
aXIgLyAoInJwXyVzLnppcCIgJSBzdGFtcCkKICAgIGluY2x1ZGUgPSBbKCJmdW5jdGlvbmFsIG1vZHVsZXMvVlJOIiwgUFsicm9vdCJdIC8gImZ1bmN0aW9u
YWwgbW9kdWxlcyIgLyAiVlJOIiksICgiZnVuY3Rpb25hbCBtb2R1bGVzL1ZERiIsIFBbInJvb3QiXSAvICJmdW5jdGlvbmFsIG1vZHVsZXMiIC8gIlZERiIp
LCAoInN1cHBvcnRpdmUgbW9kdWxlcy9yZWdpc3RyeSIsIFBbInJlZ2lzdHJ5Il0pLAogICAgICAgICAgICAgICAoIlZJQV9SZXBvcnRzL3Jldmlldy92Y2dj
X2hlYWx0aCIsIFBbIm91dCJdKSwgKCJWSUFfUmVwb3J0cy92ZGYiLCByZXBvcnRzIC8gInZkZiIpLCAoIlZJQV9SZXBvcnRzL3ZybiIsIHJlcG9ydHMgLyAi
dnJuIildCiAgICBza2lwX2RpcnMgPSB7Il9zdXBlcnNlZGVkIiwgIl9fcHljYWNoZV9fIiwgIm91dHB1dF9odWIiLCAiX3ZkZl9sb2dzIiwgIl92ZGZfc3lz
dGVtIiwgInRhcmdldCIsICIuZmluZ2VycHJpbnQifQogICAgc2tpcF9leHQgPSB7Ii56aXAiLCAiLnBhcnF1ZXQiLCAiLmR1Y2tkYiIsICIucHljIn0KICAg
IG4gPSAwCiAgICB0b3RhbCA9IDAKICAgIHdpdGggemlwZmlsZS5aaXBGaWxlKHpwYXRoLCAidyIsIHppcGZpbGUuWklQX0RFRkxBVEVEKSBhcyB6OgogICAg
ICAgIGZvciByZWwsIGQgaW4gaW5jbHVkZToKICAgICAgICAgICAgaWYgbm90IGQuaXNfZGlyKCk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAg
ICAgICBmb3IgcCBpbiBkLnJnbG9iKCIqIik6CiAgICAgICAgICAgICAgICBpZiBub3QgcC5pc19maWxlKCkgb3IgKHNldChwLnJlbGF0aXZlX3RvKGQpLnBh
cnRzWzotMV0pICYgc2tpcF9kaXJzKSBvciBwLnN1ZmZpeC5sb3dlcigpIGluIHNraXBfZXh0IG9yIHAuc3RhdCgpLnN0X3NpemUgPiA1MCAqIDEwMjQgKiAx
MDI0OgogICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICB6LndyaXRlKHAsIHJlbCArICIvIiArIHAucmVsYXRpdmVfdG8oZCku
YXNfcG9zaXgoKSkKICAgICAgICAgICAgICAgIG4gKz0gMQogICAgICAgICAgICAgICAgdG90YWwgKz0gcC5zdGF0KCkuc3Rfc2l6ZQogICAgICAgIHoud3Jp
dGVzdHIoIlJFU1RPUkVQT0lOVC5qc29uIiwganNvbi5kdW1wcyh7InN0YW1wIjogc3RhbXAsICJ0cyI6IG5vdywgImxhbXBzIjogbGFtcHMsICJub3RlIjog
bm90ZSwgImdpdF9zaGEiOiBnaXRfc2hhLCAiZmlsZXMiOiBuLCAiYnl0ZXMiOiB0b3RhbCwgImhvd190b19yZXN0b3JlIjogImdpdCBjaGVja291dCBycC88
c3RhbXA+IC0tIDxwYXRoPiDmiJYgRXhwYW5kLUFyY2hpdmUg5YiwIHN0YWdpbmcg5aS+5b6M6YCQ5aS+5q+U5bCN5YaN6KaG6JOLO+S4jeiHquWLleimhuiT
iyJ9LCBlbnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0xKSkKICAgIHNoYSA9IGhhc2hsaWIuc2hhMjU2KHpwYXRoLnJlYWRfYnl0ZXMoKSkuaGV4ZGlnZXN0
KCkKICAgIHJlYyA9IHsic3RhbXAiOiBzdGFtcCwgInRzIjogbm93LCAiemlwIjogenBhdGgubmFtZSwgInppcF9zaGEyNTYiOiBzaGEsICJmaWxlcyI6IG4s
ICJieXRlcyI6IHRvdGFsLCAibGFtcHMiOiBsYW1wcywgImdpdF9zaGEiOiBnaXRfc2hhLCAiZ2l0X3RhZyI6ICJycC8iICsgc3RhbXAsICJub3RlIjogbm90
ZSwgImZvcmNlZCI6IGZvcmNlLCAic3RhdHVzIjogIkxPQ0tFRCJ9CiAgICB3aXRoIG9wZW4oUFsicmVnaXN0cnkiXSAvICJWSUFfUmVzdG9yZVBvaW50X0xl
ZGdlcl92MDEwMC5qc29ubCIsICJhIiwgZW5jb2Rpbmc9InV0Zi04IikgYXMgZmg6CiAgICAgICAgZmgud3JpdGUoanNvbi5kdW1wcyhyZWMsIGVuc3VyZV9h
c2NpaT1GYWxzZSkgKyAiXG4iKQogICAgb3V0LnVwZGF0ZShyZWMsIHN0YXR1cz0iTE9DS0VEIiwgbGFtcD0iR1JFRU4iIGlmIG5vdCBmb3JjZSBlbHNlICJZ
RUxMT1ciLCB6aXBfcGF0aD1zdHIoenBhdGgpKQogICAgcmV0dXJuIG91dAoKCmRlZiByZXN0b3JlcG9pbnRfbGlzdChQOiBkaWN0IHwgTm9uZSA9IE5vbmUp
IC0+IGxpc3Q6CiAgICBQID0gUCBvciBfcGF0aHMoKQogICAgZnAgPSBQWyJyZWdpc3RyeSJdIC8gIlZJQV9SZXN0b3JlUG9pbnRfTGVkZ2VyX3YwMTAwLmpz
b25sIgogICAgaWYgbm90IGZwLmV4aXN0cygpOgogICAgICAgIHJldHVybiBbXQogICAgcmV0dXJuIFtqc29uLmxvYWRzKGxuKSBmb3IgbG4gaW4gZnAucmVh
ZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpLnNwbGl0bGluZXMoKSBpZiBsbi5zdHJpcCgpXQoKCl9NQUlOXzAxMDcgPSBtYWluCgoKZGVmIG1haW4oYXJndj1O
b25lKSAtPiBpbnQ6CiAgICBpZiBvcy5lbnZpcm9uLmdldCgiVklBX0ZST01fVkNHQyIpICE9ICJZRVMiOgogICAgICAgIHByaW50KCJbVkNHQ10g5ouS57WV
44CC5Y+q6IO957aTIHZpYS12Y2dj44CCIikKICAgICAgICByZXR1cm4gMgogICAgYSA9IGxpc3Qoc3lzLmFyZ3ZbMTpdIGlmIGFyZ3YgaXMgTm9uZSBlbHNl
IGFyZ3YpCgogICAgZGVmIG9wdChmbGFnLCBkZWZhdWx0PSIiKToKICAgICAgICByZXR1cm4gYVthLmluZGV4KGZsYWcpICsgMV0gaWYgZmxhZyBpbiBhIGFu
ZCBhLmluZGV4KGZsYWcpICsgMSA8IGxlbihhKSBlbHNlIGRlZmF1bHQKICAgIGlmIGFbOjFdID09IFsicmVzdG9yZXBvaW50Il06CiAgICAgICAgaWYgYVsx
OjJdID09IFsibGlzdCJdOgogICAgICAgICAgICByb3dzID0gcmVzdG9yZXBvaW50X2xpc3QoKQogICAgICAgICAgICBwcmludCgiW+ioiF0g6YKE5Y6f6bue
ICVkIiAlIGxlbihyb3dzKSkKICAgICAgICAgICAgZm9yIHIgaW4gcm93c1stMTA6XToKICAgICAgICAgICAgICAgIHByaW50KCIgIFtPS10gJXMgwrcgJXMg
wrcgJWQg5qqUICUuMWYgTUIgwrcgJXMgwrcgZ2l0ICVzIMK3ICVzIiAlIChyWyJzdGFtcCJdLCAiICIuam9pbigiJXM9JXMiICUga3YgZm9yIGt2IGluIHJb
ImxhbXBzIl0uaXRlbXMoKSksIHJbImZpbGVzIl0sIHJbImJ5dGVzIl0gLyAxMDQ4NTc2LCByWyJ6aXBfc2hhMjU2Il1bOjEyXSwgKHIuZ2V0KCJnaXRfc2hh
Iikgb3IgIuKAlCIpWzo4XSwgci5nZXQoIm5vdGUiLCAiIikpKQogICAgICAgICAgICByZXR1cm4gMAogICAgICAgIHIgPSByZXN0b3JlcG9pbnRfbWFrZShu
b3RlPW9wdCgiLS1ub3RlIiksIGdpdF9zaGE9b3B0KCItLWdpdCIpLCBhbGxvd195ZWxsb3c9KCItLXN0cmljdCIgbm90IGluIGEpLCBmb3JjZT0oIi0tZm9y
Y2UiIGluIGEpKQogICAgICAgIGlmIHJbInN0YXR1cyJdID09ICJSRUZVU0VEIjoKICAgICAgICAgICAgcHJpbnQoIiAgW1JFRF0g6YKE5Y6f6bue5ouS6Y6W
OiVzIiAlIHJbIndoeSJdKQogICAgICAgICAgICByZXR1cm4gMQogICAgICAgIHByaW50KCJb6KiIXSDpgoTljp/pu54gTE9DS0VEIMK3ICVzIMK3ICVzIMK3
ICVkIOaqlCAlLjFmIE1CIMK3IHppcCAlcyDCtyBzaGEgJXMgwrcgdGFnICVzIMK3ICVzIiAlIChyWyJzdGFtcCJdLCAiICIuam9pbigiJXM9JXMiICUga3Yg
Zm9yIGt2IGluIHJbImxhbXBzIl0uaXRlbXMoKSksIHJbImZpbGVzIl0sIHJbImJ5dGVzIl0gLyAxMDQ4NTc2LCByWyJ6aXAiXSwgclsiemlwX3NoYTI1NiJd
WzoxMl0sIHJbImdpdF90YWciXSwgclsibGFtcCJdKSkKICAgICAgICBwcmludCgiICBbUlBdICVzIiAlIHJbInppcF9wYXRoIl0pCiAgICAgICAgcHJpbnQo
IiAgW1RBR10gJXMiICUgclsiZ2l0X3RhZyJdKQogICAgICAgIHJldHVybiAwCiAgICByZXR1cm4gX01BSU5fMDEwNyhhKQoKCmRlZiBzZWxmdGVzdCgpIC0+
IGludDoKICAgIHAgPSBmID0gMAoKICAgIGRlZiBjaGsobmFtZSwgY29uZCk6CiAgICAgICAgbm9ubG9jYWwgcCwgZgogICAgICAgIGlmIGNvbmQ6CiAgICAg
ICAgICAgIHAgKz0gMQogICAgICAgICAgICBwcmludCgiICBbT0tdICVzIiAlIG5hbWUpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZiArPSAxCiAgICAg
ICAgICAgIHByaW50KCIgIFtGQUlMXSAlcyIgJSBuYW1lKQoKICAgIHRkID0gUGF0aCh0ZW1wZmlsZS5ta2R0ZW1wKHByZWZpeD0iY2djaGVhbHRoLSIpKQog
ICAgb3MuZW52aXJvblsiVklBX1JPT1QiXSA9IHN0cih0ZCkKICAgIG9zLmVudmlyb25bIlZJQV9OT19PUEVOIl0gPSAiMSIKICAgIFAgPSBfcGF0aHMoKQog
ICAgY2hrKCLikaAg5rKZ55uSIiwgYWxsKHN0cih2KS5zdGFydHN3aXRoKHN0cih0ZCkpIGZvciB2IGluIFAudmFsdWVzKCkpKQogICAgQSA9ICIjIFtWSUE6
QUNDRUwtQlJJREdFOnYwMTAwXVxuIgogICAgKFBbInJlZ2lzdHJ5Il0pLm1rZGlyKHBhcmVudHM9VHJ1ZSkKICAgIChQWyJyZWdpc3RyeSJdIC8gIkNHQ19N
REwwMDFfWF92MDEwMC5weSIpLndyaXRlX3RleHQoQSArICJ4PTFcbiIsIGVuY29kaW5nPSJ1dGYtOCIpCiAgICAoUFsic3VwIl0gLyAiVklBX09sZC5weSIp
LndyaXRlX3RleHQoImltcG9ydCByZXF1ZXN0c1xuIiwgZW5jb2Rpbmc9InV0Zi04IikKICAgIChQWyJyZXBvcnRzIl0gLyAidnJuIikubWtkaXIocGFyZW50
cz1UcnVlKQogICAgKFBbInJlcG9ydHMiXSAvICJ2cm4iIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIpLndyaXRlX3RleHQoanNvbi5kdW1wcyh7InN1YiI6ICJW
Uk4iLCAidHMiOiAidCIsICJsYW1wIjogIkdSRUVOIiwgInN1bW1hcnkiOiB7ImZpbGVzIjogMiwgInJlZCI6IDAsICJ5ZWxsb3ciOiAwLCAiZ3JlZW4iOiAy
LCAibnVtYmVyZWQiOiAyLCAicmVnaXN0ZXJlZCI6IDIsICJhY2NlbCI6IDIsICJuZXRfYmFkIjogMCwgInNlbWFudGljX2lzc3VlcyI6IDAsICJmbl9pdGVt
cyI6IDUsICJmbl9udW1iZXJlZCI6IDUsICJ0YWJsZXMiOiAxLCAidGFibGVzX251bWJlcmVkIjogMSwgImJvb2tzIjogMSwgImxpYnNfbWlzc2luZyI6IDAs
ICJweXRob24iOiAicHkifSwgImZpbGVzIjogW10sICJib29rcyI6IFtdLCAibGlicyI6IFtdfSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICAoUFsicmV2aWV3
Il0gLyAidmNnY19wYW5vcmFtYSIpLm1rZGlyKHBhcmVudHM9VHJ1ZSkKICAgIChQWyJyZXZpZXciXSAvICJ2Y2djX3Bhbm9yYW1hIiAvICJQQU5PUkFNQV9s
YXRlc3QuanNvbiIpLndyaXRlX3RleHQoanNvbi5kdW1wcyh7InRzIjogInQiLCAibGFtcCI6ICJZRUxMT1ciLCAiY2hlY2tzIjogeyJLMSI6ICJHUkVFTiIs
ICJLMiI6ICJZRUxMT1cifX0pLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmVzID0gbWF0cml4KFApCiAgICBjaGsoIuKRoSBWQ0dDIOiHquW3sei3keWBpeW6
t+autShzdXBwb3J0aXZlIG1vZHVsZXMpOjIg5pePIMK3IFZJQV9PbGQg5Ye657ay54Sh57ay5qmL57SFIiwgcmVzWyJzdWJzIl1bIlZDR0MiXVsic3VtbWFy
eSJdWyJmaWxlcyJdID09IDIgYW5kIHJlc1sic3VicyJdWyJWQ0dDIl1bInN1bW1hcnkiXVsibmV0X2JhZCJdID09IDEpCiAgICBjaGsoIuKRoiBWUk4g6K6A
6Ieq5aCxKOe2oCnCtyBWREYg5pyq6LeRID0gTm9uZSjngbApIiwgcmVzWyJzdWJzIl1bIlZSTiJdWyJsYW1wIl0gPT0gIkdSRUVOIiBhbmQgcmVzWyJzdWJz
Il1bIlZERiJdIGlzIE5vbmUpCiAgICBjaGsoIuKRoyDml6LmnInlvJXmk47ntZDmnpzkvbXlhaU65YWo5pmvIEsxL0syIMK3IOeSsOWigy/lt6Xlhbcv5rK7
55CGIOacqui3kSA9IEdSQVkiLCByZXNbInNlY3Rpb25zIl1bInBhbm9yYW1hIl1bImNoZWNrcyJdID09IHsiSzEiOiAiR1JFRU4iLCAiSzIiOiAiWUVMTE9X
In0gYW5kIHJlc1sic2VjdGlvbnMiXVsiZW52Il1bImxhbXAiXSA9PSAiR1JBWSIpCiAgICBwYWNrID0gcGFzdGVfcGFjayhyZXMpCiAgICBvdXQgPSB3cml0
ZV9vdXRwdXRzKHJlcywgcGFjaywgUCkKICAgIGh0bSA9IFBhdGgob3V0WyJodG1sIl0pLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQogICAgY2hrKCLi
kaQgSFRNTDrmt7roibIgwrcg6Ieq6YGp5oeJKGF1dG8tZml0IGdyaWQgwrcgdmlld3BvcnQpwrcg54eI56ys5LiA5qyEIMK3IOWbm+iJsiB0b2tlbiDCtyDn
tIXnh4jmhaLploMgwrcg5Y+v5oyJ57O757WxL+eHiOevqSIsICJhdXRvLWZpdCIgaW4gaHRtIGFuZCAidmlld3BvcnQiIGluIGh0bSBhbmQgYWxsKGMgaW4g
aHRtIGZvciBjIGluIExBTVAudmFsdWVzKCkpIGFuZCAiQGtleWZyYW1lcyBibCIgaW4gaHRtIGFuZCAiZmx0KCdWUk4nLCcnKSIgaW4gaHRtKQogICAgY2hr
KCLikaUg6LK85Zue5YyFIOKJpDMwMCDCtyBORVhUOiDCtyDnuL3nh4jntIUoVkNHQyDmnInntIUpwrcg5Y2h5ZyoIiwgbGVuKHBhY2spIDw9IDMwMCBhbmQg
cGFja1stMV0uc3RhcnRzd2l0aCgiTkVYVDoiKSBhbmQgcmVzWyJsYW1wIl0gPT0gIlJFRCIgYW5kIFBhdGgob3V0WyJtZCJdKS5leGlzdHMoKSkKICAgIGNo
aygi4pGmIOWUr+iugDpWSUFfUmVwb3J0cy92Y2djL0hFQUxUSF9sYXRlc3QuanNvbiDmmK/llK/kuIDmlrDlr6vlnKggcmVwb3J0cy92Y2djIOeahOaqlCIs
IChQWyJyZXBvcnRzIl0gLyAidmNnYyIgLyAiSEVBTFRIX2xhdGVzdC5qc29uIikuZXhpc3RzKCkpCiAgICBjMCA9IGNvbmZpZ19sb2FkKFApCiAgICByMSA9
IGNvbmZpZ19zZXQoImRiIiwgIm1lbW9yeV9saW1pdCIsICI0R0IiLCBQKQogICAgcjIgPSBjb25maWdfc2V0KCJkYiIsICJub3BlIiwgIngiLCBQKQogICAg
dSA9IHVpKFApCiAgICB1aCA9IFBhdGgodVsiaHRtbCJdKS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIGNoaygi4pGoIHYwMTA0IGNvbmZpZzro
h6rlu7rlhoogcHJvZ3JhbS9kYiDCtyBzZXQgbWVtb3J5IDRHQihoaXN0b3J5IDEpwrcg6Z2e55m95ZCN5Zau6Y215ouSIMK3IHVpIOWFqemdouadvyjlt6bl
j6rmnInnqIvlvI/lpL4r6LOH5paZ5bqrIMK3IOWPsyA2IOmggeexpCkiLCBjMFsicHJvZ3JhbSJdWyJyb290Il0gPT0gc3RyKFBbInJvb3QiXSkgYW5kIHIx
WyJvayJdIGFuZCBjb25maWdfbG9hZChQKVsiZGIiXVsibWVtb3J5X2xpbWl0Il0gPT0gIjRHQiIgYW5kIG5vdCByMlsib2siXSBhbmQgIueoi+W8j+aqlOah
iOWkviIgaW4gdWggYW5kICLos4fmlpnluqsiIGluIHVoIGFuZCAodWguY291bnQoJzxkaXYgY2xhc3M9InBhZ2UiJykgKyB1aC5jb3VudCgnPGRpdiBjbGFz
cz0icGFnZSBvbiInKSkgPT0gNiBhbmQgIlZERl9VSV9sYXRlc3QuaHRtbCIgaW4gdWgpCiAgICB0aCA9IHVpX3RoZW1lX2luaXQoUFsicm9vdCJdKQogICAg
dWgyID0gUGF0aCh1WyJodG1sIl0pLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQogICAgdTIgPSB1aShQKQogICAgdWgyID0gUGF0aCh1MlsiaHRtbCJd
KS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIGNoaygi4pGpIHYwMTA1IHRoZW1lOuWGiuiHquW7uiDCtyB1aSDlpZcgdmFyKC0tdG9rZW4pIMK3
IOeHiOiJsuS7jeeCuumOluWumuWbm+iJsiBmYWxsYmFjayIsIHRoWyJzdGF0dXMiXSBpbiAoIldSSVRURU4iLCAiRVhJU1RTIikgYW5kIChQWyJyZWdpc3Ry
eSJdIC8gIlZJQV9VSV9UZW1wbGF0ZV9TU09UX3YwMTAwLmpzb24iKS5leGlzdHMoKSBhbmQgJ2lkPSJ2aWEtdGhlbWUiJyBpbiB1aDIgYW5kICJ2YXIoLS1s
YW1wLXJlZCwjZGMyNjI2KSIgaW4gdWgyIGFuZCAiLS1wYW5lbDoiIGluIHVoMikKICAgIHVoMyA9IFBhdGgodWkoUClbImh0bWwiXSkucmVhZF90ZXh0KGVu
Y29kaW5nPSJ1dGYtOCIpCiAgICBjaGsoIuKRqiB2MDEwNiDmu5HpvKDlvos6VkNHQyB1aSDmnInln7fooYwo5ruR6bygKXZpYTovLyDmjInpiJUiLCAiaWQ9
J3J1biciIGluIHVoMyBhbmQgInZpYTovLyIgaW4gdWgzKQogICAgdWlfbWFuaWZlc3Rfd3JpdGUoIlZDR0MiLCBQWyJvdXQiXSwgUFsib3V0Il0gLyAiVkNH
Q19VSV9sYXRlc3QuaHRtbCIsICJZRUxMT1ciLCB7Im1hbmFnZXIiOiBNRS5uYW1lfSkKICAgIHByID0gcG9ydGFsKFApCiAgICBwaCA9IFBhdGgocHJbImh0
bWwiXSkucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCiAgICBjaGsoIuKRqyB2MDEwNyBwb3J0YWw65LiJ57O757Wx6YiVIMK3IFZDR0Mg5pyJ6aCBIMK3
IFZERi9WUk4g5pyq6LeRIHVpIOaomeeBsOS4jeWBh+ijnSDCtyDmqKHmnb8gQ1NTIiwgcGguY291bnQoImNsYXNzPSdzeXNidG4iKSA9PSAzIGFuZCAiVkNH
Q19VSV9sYXRlc3QuaHRtbCIgaW4gcGggYW5kIHNldChwclsibWlzc2luZyJdKSA9PSB7IlZERiIsICJWUk4ifSBhbmQgJ2lkPSJ2aWEtdGhlbWUiJyBpbiBw
aCkKICAgIHIwID0gcmVzdG9yZXBvaW50X21ha2UoUCwgbm90ZT0idCIsIGdpdF9zaGE9ImFiYyIpCiAgICByMSA9IHJlc3RvcmVwb2ludF9tYWtlKFAsIG5v
dGU9InQiLCBnaXRfc2hhPSJhYmMiLCBmb3JjZT1UcnVlKQogICAgY2hrKCLikawgdjAxMDggcmVzdG9yZXBvaW50OuacieeBsC/ntIXmi5LpjpYgwrcgLS1m
b3JjZSDmiY3pjpYo6buDKcK3IHppcCArIOW4syArIHNoYSIsIHIwWyJzdGF0dXMiXSA9PSAiUkVGVVNFRCIgYW5kIHIxWyJzdGF0dXMiXSA9PSAiTE9DS0VE
IiBhbmQgUGF0aChyMVsiemlwX3BhdGgiXSkuZXhpc3RzKCkgYW5kIChQWyJyZWdpc3RyeSJdIC8gIlZJQV9SZXN0b3JlUG9pbnRfTGVkZ2VyX3YwMTAwLmpz
b25sIikuZXhpc3RzKCkgYW5kIGxlbihyMVsiemlwX3NoYTI1NiJdKSA9PSA2NCBhbmQgcmVzdG9yZXBvaW50X2xpc3QoUClbLTFdWyJzdGFtcCJdID09IHIx
WyJzdGFtcCJdKQogICAgYm9keSA9IE1FLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQogICAgY2hrKCLikacg5bi25Yqg6YCf5Zmo5qmLIMK3IOWBpeW6
t+WFseeUqOautSDCtyBWSUFfRlJPTV9WQ0dDIOmWmCIsICJbVklBOkFDQ0VMLUJSSURHRTp2MDEwMF0iIGluIGJvZHkgYW5kICJbVklBOlNNLUhFQUxUSDp2
MDEwMF0iIGluIGJvZHkgYW5kICJWSUFfRlJPTV9WQ0dDIiBpbiBib2R5KQogICAgZm9yIGsgaW4gKCJWSUFfUk9PVCIsICJWSUFfTk9fT1BFTiIpOgogICAg
ICAgIG9zLmVudmlyb24ucG9wKGssIE5vbmUpCiAgICBzaHV0aWwucm10cmVlKHRkLCBpZ25vcmVfZXJyb3JzPVRydWUpCiAgICBwcmludCgiW+ioiF0gJXMg
6Ieq5risICVkLyVkIMK3ICVzIiAlIChOQU1FLCBwLCBwICsgZiwgIlBBU1MiIGlmIGYgPT0gMCBlbHNlICJGQUlMIikpCiAgICByZXR1cm4gMCBpZiBmID09
IDAgZWxzZSAxCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJhaXNlIFN5c3RlbUV4aXQobWFpbigpKQo=
'@
$B64Vdf = @'
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJWREZfU3lzdGVtTWFuYWdlciB2MDE0NyDigJQg6JaE5bC+OnF1b3Rl
IOWLleipnijmk43kvZzlk6Hku6QgMjAyNi0xMC0wNzpWUk4g5o6D5o+P5YCL6IKh5aCx5ZGK5pmCLOmcgOimgeeahOihjOaDhS/ln7rmnKzos4fmlpnpgI/p
gY4gVkRGIOaKkzvlj6/lvp7os4fmlpnluqvmiJblvJXmk44p44CCCiAgcXVvdGUgLS10aWNrZXJzIDIzMzAsMzcwNiBbLS1hc29mIFlZWVktTU0tRERdIFst
LWRheXMgNV0KICAgICAgICDmr4/mqpQ64pGgIOWFiOafpeacrOWcsChvdXRwdXRfaHViL2V4cG9ydC92ZGZfdHdfbWFya2V0X3R3X2RhaWx5X3ByaWNlcy5j
c3Yg5LmL6aGe55qE5Yyv5Ye6O+acieWwsSBzb3VyY2U9ZGIp4pGhIOaykuaciSDihpIg5byV5pOOIHlmaW5hbmNlKDzku6PomZ8+LlRXLOWGjeippiAuVFdP
O3NvdXJjZT1lbmdpbmUpCiAgICAgICAg4oaSIFZJQV9SZXBvcnRzL3ZkZi9SRVNVTFRfcXVvdGVfbGF0ZXN0Lmpzb24o5q+P5qqUOnRpY2tlciDCtyBhc29m
IMK3IGNsb3NlIMK3IHByZXZfY2xvc2Ugwrcgc291cmNlIMK3IGVuZ2luZSDCtyBvay93aHkpKyDosrzlm57ljIU75LiN56KwIFZERiDlhooK5YW26aSY5YuV
6Kme54Wn5YmN54mI6Y+I44CCCiIiIgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgojID09PT09IFtWSUE6QUNDRUwtQlJJREdFOnYwMTAw
XSBTdXBlckFjY2VsIOWKoOmAn+WZqOapiyjmibkxMDIg5YWo5qi55bCO5YWl5LukO2dyYWNlZnVsIOmbtuihjOeCuuiuiuabtCkgPT09PT0KdHJ5OgogICAg
aW1wb3J0IHN5cyBhcyBfc2Ffc3lzCiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX3NhX1BhdGgKICAgIF9zYV9wID0gX3NhX1BhdGgoX19maWxl
X18pLnJlc29sdmUoKQogICAgd2hpbGUgX3NhX3AucGFyZW50ICE9IF9zYV9wOgogICAgICAgIGlmIChfc2FfcCAvICJzdXBwb3J0aXZlIG1vZHVsZXMiIC8g
IlZJQV9TdXBlckFjY2VsX01vZHVsZS5weSIpLmV4aXN0cygpOgogICAgICAgICAgICBfc2Ffc3lzLnBhdGguaW5zZXJ0KDAsIHN0cihfc2FfcCAvICJzdXBw
b3J0aXZlIG1vZHVsZXMiKSkKICAgICAgICAgICAgYnJlYWsKICAgICAgICBfc2FfcCA9IF9zYV9wLnBhcmVudAogICAgaW1wb3J0IFZJQV9TdXBlckFjY2Vs
X01vZHVsZSBhcyBWSUFfQUNDRUwgICMgbm9xYTogRjQwMQpleGNlcHQgSW1wb3J0RXJyb3I6CiAgICBWSUFfQUNDRUwgPSBOb25lCiMgPT09PT0gW1ZJQTpB
Q0NFTC1CUklER0U6RU5EXSA9PT09PQoKIyA9PT09PSBbVklBOk5FVC1CUklER0U6djAxMDBdIOe1seWMhee2sui3r+W3peWFt+apiyjmibkxMTUgVkRGIOWF
qOWwjuWFpeS7pDtncmFjZWZ1bCDpm7booYzngrrorormm7QpID09PT09ClZJQV9ORVRfVE9PTF9QQVRIID0gTm9uZQp0cnk6CiAgICBmcm9tIHBhdGhsaWIg
aW1wb3J0IFBhdGggYXMgX25iX1BhdGgKICAgIF9uYl9wID0gX25iX1BhdGgoX19maWxlX18pLnJlc29sdmUoKQogICAgd2hpbGUgX25iX3AucGFyZW50ICE9
IF9uYl9wOgogICAgICAgIF9uYl9kaXIgPSBfbmJfcCAvICJzdXBwb3J0aXZlIG1vZHVsZXMiIC8gIm5ldHdvcmsiCiAgICAgICAgaWYgX25iX2Rpci5leGlz
dHMoKToKICAgICAgICAgICAgX25iX2hpdHMgPSBzb3J0ZWQoX25iX2Rpci5nbG9iKCJ2aWFfbmV0X3VuaWZpZWRfdioucHkiKSkKICAgICAgICAgICAgaWYg
X25iX2hpdHM6CiAgICAgICAgICAgICAgICBWSUFfTkVUX1RPT0xfUEFUSCA9IHN0cihfbmJfaGl0c1stMV0pCiAgICAgICAgICAgIGJyZWFrCiAgICAgICAg
X25iX3AgPSBfbmJfcC5wYXJlbnQKZXhjZXB0IEV4Y2VwdGlvbjoKICAgIFZJQV9ORVRfVE9PTF9QQVRIID0gTm9uZQoKCmRlZiBfdmlhX25ldCgpOgogICAg
IiIi57Wx5YyF5ZSv5LiA57ay6Lev5bel5YW35oOw5oCn6LyJ5YWlKOazlemBtembmemWmCBWSUFfTkVUX0NPTlNFTlQpO+e8uuW4reWbniBOb25lKOiqoOWv
pikiIiIKICAgIGlmIFZJQV9ORVRfVE9PTF9QQVRIIGlzIE5vbmU6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIHRyeToKICAgICAgICBpbXBvcnQgaW1wb3J0
bGliLnV0aWwgYXMgX25iX2lsdQogICAgICAgIHNwZWMgPSBfbmJfaWx1LnNwZWNfZnJvbV9maWxlX2xvY2F0aW9uKCJWSUFfTkVUX1VOSUZJRUQiLCBWSUFf
TkVUX1RPT0xfUEFUSCkKICAgICAgICBtb2R1bGUgPSBfbmJfaWx1Lm1vZHVsZV9mcm9tX3NwZWMoc3BlYykKICAgICAgICBzcGVjLmxvYWRlci5leGVjX21v
ZHVsZShtb2R1bGUpCiAgICAgICAgcmV0dXJuIG1vZHVsZQogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gTm9uZQojID09PT09IFtWSUE6
TkVULUJSSURHRTpFTkRdID09PT09CgojID09PT09IFtWSUE6TElCLUJSSURHRTp2MDEwMF0g5LiJ5bqr5q2j5YW45qmLKOaJuTU5NzvnvLrluK3lpKfogbLm
i4ss5LiNIGdyYWNlZnVsKSA9PT09PQppbXBvcnQgc3lzIGFzIF9sYl9zeXMKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9sYl9QYXRoCl9sYl9wID0g
X2xiX1BhdGgoX19maWxlX18pLnJlc29sdmUoKQp3aGlsZSBfbGJfcC5wYXJlbnQgIT0gX2xiX3A6CiAgICBpZiAoX2xiX3AgLyAic3VwcG9ydGl2ZSBtb2R1
bGVzIikuaXNfZGlyKCk6CiAgICAgICAgX2xiX3N5cy5wYXRoLmluc2VydCgwLCBzdHIoX2xiX3AgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIikpCiAgICAgICAg
YnJlYWsKICAgIF9sYl9wID0gX2xiX3AucGFyZW50CmltcG9ydCBWSUFfTGliQ2Fub24gYXMgX0xJQiAgICAgICAgICAjIOato+WFuOe8uuW4rT3lpKfogbLm
i4ss5LiN5YGH6KOd5pyJKExMMTUxKQojID09PT09IFtWSUE6TElCLUJSSURHRTpFTkRdID09PT09CgppbXBvcnQgY3N2CmltcG9ydCBkYXRldGltZQppbXBv
cnQgaW1wb3J0bGliLnV0aWwKaW1wb3J0IGpzb24KaW1wb3J0IG9zCmltcG9ydCByZQppbXBvcnQgc3lzCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAoKSEVS
RSA9IFBhdGgoX19maWxlX18pLnJlc29sdmUoKS5wYXJlbnQKX1NURU0gPSAiVkRGX1N5c3RlbU1hbmFnZXIiClRBRyA9ICJ2MDE0NyIKCgpkZWYgX3ZudW1f
djAxNDcocGF0aCkgLT4gaW50OgogICAgbSA9IHJlLnNlYXJjaChyIl92KFxkezR9KSQiLCBQYXRoKHBhdGgpLnN0ZW0pCiAgICByZXR1cm4gaW50KG0uZ3Jv
dXAoMSkpIGlmIG0gZWxzZSAtMQoKCmRlZiBfbG9hZF92MDE0NyhwYXRoOiBQYXRoLCBuYW1lOiBzdHIpOgogICAgaWYgbmFtZSBub3QgaW4gc3lzLm1vZHVs
ZXM6CiAgICAgICAgc3BlYyA9IGltcG9ydGxpYi51dGlsLnNwZWNfZnJvbV9maWxlX2xvY2F0aW9uKG5hbWUsIHBhdGgpCiAgICAgICAgbW9kID0gaW1wb3J0
bGliLnV0aWwubW9kdWxlX2Zyb21fc3BlYyhzcGVjKQogICAgICAgIHN5cy5tb2R1bGVzW25hbWVdID0gbW9kCiAgICAgICAgc3BlYy5sb2FkZXIuZXhlY19t
b2R1bGUobW9kKQogICAgcmV0dXJuIHN5cy5tb2R1bGVzW25hbWVdCgoKUFJJT1JfUEFUSCA9IG1heCgocCBmb3IgcCBpbiBIRVJFLmdsb2IoX1NURU0gKyAi
X3YqLnB5IikgaWYgMCA8PSBfdm51bV92MDE0NyhwKSA8IF92bnVtX3YwMTQ3KF9fZmlsZV9fKSksIGtleT1fdm51bV92MDE0NykKUFJJT1IgPSBfbG9hZF92
MDE0NyhQUklPUl9QQVRILCBfU1RFTSArICJfcHJpb3JfZm9yXyIgKyBQYXRoKF9fZmlsZV9fKS5zdGVtKQoKCmRlZiBfX2dldGF0dHJfXyhuYW1lKToKICAg
IHJldHVybiBnZXRhdHRyKFBSSU9SLCBuYW1lKQoKCmRlZiBfZGJfbG9va3VwKGhvbWU6IFBhdGgsIHRpY2tlcjogc3RyLCBhc29mOiBzdHIpIC0+IGRpY3Qg
fCBOb25lOgogICAgIiIi5pys5Zyw5Yyv5Ye6IGNzdiDoo6Hmib4gdGlja2VyIOWcqCBhc29mKOaIluS5i+WJjeacgOi/keS4gOaXpSnnmoTmlLbnm6Q75qyE
5ZCN5a+s6ayGKHRpY2tlci9zeW1ib2wv5Luj6JmfIMK3IGRhdGUv5pel5pyfIMK3IGNsb3NlL+aUtuebpCnjgIIiIiIKICAgIGNhbmRzID0gc29ydGVkKCho
b21lIC8gIm91dHB1dF9odWIiIC8gImV4cG9ydCIpLmdsb2IoIipkYWlseV9wcmljZXMqLmNzdiIpKSArIHNvcnRlZCgoaG9tZSAvICJvdXRwdXRfaHViIiAv
ICJleHBvcnQiKS5nbG9iKCIqcHJpY2VzX2FkaiouY3N2IikpIGlmIChob21lIC8gIm91dHB1dF9odWIiIC8gImV4cG9ydCIpLmlzX2RpcigpIGVsc2UgW10K
ICAgIGJlc3QgPSBOb25lCiAgICBmb3IgZnAgaW4gY2FuZHM6CiAgICAgICAgdHJ5OgogICAgICAgICAgICB3aXRoIGZwLm9wZW4oZW5jb2Rpbmc9InV0Zi04
LXNpZyIsIGVycm9ycz0icmVwbGFjZSIpIGFzIGZoOgogICAgICAgICAgICAgICAgcmQgPSBjc3YuRGljdFJlYWRlcihmaCkKICAgICAgICAgICAgICAgIGNv
bHMgPSB7Yy5sb3dlcigpOiBjIGZvciBjIGluIChyZC5maWVsZG5hbWVzIG9yIFtdKX0KICAgICAgICAgICAgICAgIHRrID0gbmV4dCgoY29sc1tjXSBmb3Ig
YyBpbiAoInRpY2tlciIsICJzeW1ib2wiLCAi5Luj6JmfIiwgInN0b2NrX2lkIiwgImNvZGUiKSBpZiBjIGluIGNvbHMpLCBOb25lKQogICAgICAgICAgICAg
ICAgZHQgPSBuZXh0KChjb2xzW2NdIGZvciBjIGluICgiZGF0ZSIsICLml6XmnJ8iLCAidHJhZGVfZGF0ZSIsICJhc29mIikgaWYgYyBpbiBjb2xzKSwgTm9u
ZSkKICAgICAgICAgICAgICAgIGNsID0gbmV4dCgoY29sc1tjXSBmb3IgYyBpbiAoImNsb3NlIiwgIuaUtuebpCIsICJhZGpfY2xvc2UiLCAi5pS255uk5YO5
IikgaWYgYyBpbiBjb2xzKSwgTm9uZSkKICAgICAgICAgICAgICAgIGlmIG5vdCAodGsgYW5kIGR0IGFuZCBjbCk6CiAgICAgICAgICAgICAgICAgICAgY29u
dGludWUKICAgICAgICAgICAgICAgIGZvciByb3cgaW4gcmQ6CiAgICAgICAgICAgICAgICAgICAgdCA9IHJlLnN1YihyIlwuVFdPPyQiLCAiIiwgc3RyKHJv
dy5nZXQodGssICIiKSkuc3RyaXAoKSkKICAgICAgICAgICAgICAgICAgICBpZiB0ICE9IHRpY2tlcjoKICAgICAgICAgICAgICAgICAgICAgICAgY29udGlu
dWUKICAgICAgICAgICAgICAgICAgICBkID0gc3RyKHJvdy5nZXQoZHQsICIiKSlbOjEwXQogICAgICAgICAgICAgICAgICAgIGlmIGQgPD0gYXNvZiBhbmQg
KGJlc3QgaXMgTm9uZSBvciBkID4gYmVzdFsiZGF0ZSJdKToKICAgICAgICAgICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgICAgICAg
ICAgYmVzdCA9IHsiZGF0ZSI6IGQsICJjbG9zZSI6IGZsb2F0KHN0cihyb3cuZ2V0KGNsLCAiIikpLnJlcGxhY2UoIiwiLCAiIikpLCAiZmlsZSI6IGZwLm5h
bWV9CiAgICAgICAgICAgICAgICAgICAgICAgIGV4Y2VwdCBWYWx1ZUVycm9yOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgcGFzcwogICAgICAgIGV4
Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICBjb250aW51ZQogICAgcmV0dXJuIGJlc3QKCgpkZWYgX2VuZ2luZV9sb29rdXAodGlja2VyOiBzdHIsIGFzb2Y6
IHN0ciwgZGF5czogaW50KSAtPiBkaWN0OgogICAgdHJ5OgogICAgICAgIGltcG9ydCB5ZmluYW5jZSBhcyB5ZiAgIyBub3FhOiBXUFM0MzMKICAgIGV4Y2Vw
dCBJbXBvcnRFcnJvcjoKICAgICAgICByZXR1cm4geyJvayI6IEZhbHNlLCAid2h5IjogInlmaW5hbmNlIOS4jeWcqOacrOeSsOWigyhWREZfRmV0Y2hTeXN0
ZW0g55qE5aKD5omN5pyJO+aIliBwaXAgaW5zdGFsbCB5ZmluYW5jZSkifQogICAgZW5kID0gZGF0ZXRpbWUuZGF0ZS5mcm9taXNvZm9ybWF0KGFzb2YpICsg
ZGF0ZXRpbWUudGltZWRlbHRhKGRheXM9MSkKICAgIHN0YXJ0ID0gZW5kIC0gZGF0ZXRpbWUudGltZWRlbHRhKGRheXM9bWF4KGRheXMsIDUpICsgMTApCiAg
ICBmb3Igc3VmIGluICgiLlRXIiwgIi5UV08iKToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGggPSB5Zi5UaWNrZXIodGlja2VyICsgc3VmKS5oaXN0b3J5
KHN0YXJ0PXN0YXJ0Lmlzb2Zvcm1hdCgpLCBlbmQ9ZW5kLmlzb2Zvcm1hdCgpLCBhdXRvX2FkanVzdD1GYWxzZSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9u
IGFzIGV4YzogICMgbm9xYTogQkxFMDAxCiAgICAgICAgICAgIHJldHVybiB7Im9rIjogRmFsc2UsICJ3aHkiOiAiJXM6JXMiICUgKHR5cGUoZXhjKS5fX25h
bWVfXywgc3RyKGV4YylbOjgwXSl9CiAgICAgICAgaWYgaCBpcyBub3QgTm9uZSBhbmQgbGVuKGgpID49IDE6CiAgICAgICAgICAgIGggPSBoW2guaW5kZXgu
c3RyZnRpbWUoIiVZLSVtLSVkIikgPD0gYXNvZl0gaWYgaGFzYXR0cihoLmluZGV4LCAic3RyZnRpbWUiKSBlbHNlIGgKICAgICAgICAgICAgaWYgbGVuKGgp
ID09IDA6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBsYXN0ID0gaC5pbG9jWy0xXQogICAgICAgICAgICBwcmV2ID0gaC5pbG9jWy0y
XSBpZiBsZW4oaCkgPj0gMiBlbHNlIE5vbmUKICAgICAgICAgICAgcmV0dXJuIHsib2siOiBUcnVlLCAic3ltYm9sIjogdGlja2VyICsgc3VmLCAiZGF0ZSI6
IGguaW5kZXhbLTFdLnN0cmZ0aW1lKCIlWS0lbS0lZCIpLCAiY2xvc2UiOiBmbG9hdChsYXN0WyJDbG9zZSJdKSwgInByZXZfY2xvc2UiOiAoZmxvYXQocHJl
dlsiQ2xvc2UiXSkgaWYgcHJldiBpcyBub3QgTm9uZSBlbHNlIE5vbmUpLCAidm9sdW1lIjogaW50KGxhc3QuZ2V0KCJWb2x1bWUiLCAwKSBvciAwKX0KICAg
IHJldHVybiB7Im9rIjogRmFsc2UsICJ3aHkiOiAieWZpbmFuY2Ug54ShICVzLlRXLy5UV08g6LOH5paZIiAlIHRpY2tlcn0KCgpkZWYgcXVvdGUodGlja2Vy
czogbGlzdCwgYXNvZjogc3RyIHwgTm9uZSA9IE5vbmUsIGRheXM6IGludCA9IDUpIC0+IGRpY3Q6CiAgICBob21lID0gUGF0aChvcy5lbnZpcm9uLmdldCgi
VklBX1ZERl9IT01FIikgb3IgSEVSRSkKICAgIG91dF9kaXIgPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJWSUFfVkRGX0hFQUxUSF9PVVQiKSBvciAoaG9tZS5w
YXJlbnRzWzFdIC8gIlZJQV9SZXBvcnRzIiAvICJ2ZGYiKSkKICAgIG91dF9kaXIubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgYXNv
ZiA9IGFzb2Ygb3IgZGF0ZXRpbWUuZGF0ZS50b2RheSgpLmlzb2Zvcm1hdCgpCiAgICByb3dzID0gW10KICAgIGZvciB0IGluIHRpY2tlcnM6CiAgICAgICAg
dCA9IHJlLnN1YihyIlxEIiwgIiIsIHQpCiAgICAgICAgaWYgbm90IHQ6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZGIgPSBfZGJfbG9va3VwKGhv
bWUsIHQsIGFzb2YpCiAgICAgICAgaWYgZGI6CiAgICAgICAgICAgIHJvd3MuYXBwZW5kKHsidGlja2VyIjogdCwgImFzb2YiOiBhc29mLCAiZGF0ZSI6IGRi
WyJkYXRlIl0sICJjbG9zZSI6IGRiWyJjbG9zZSJdLCAic291cmNlIjogImRiIiwgImVuZ2luZSI6IGRiWyJmaWxlIl0sICJvayI6IFRydWV9KQogICAgICAg
ICAgICBjb250aW51ZQogICAgICAgIGVuZyA9IF9lbmdpbmVfbG9va3VwKHQsIGFzb2YsIGRheXMpIGlmIG9zLmVudmlyb24uZ2V0KCJWSUFfUVVPVEVfTk9f
RU5HSU5FIikgIT0gIjEiIGVsc2UgeyJvayI6IEZhbHNlLCAid2h5IjogIuW8leaTjumXnChWSUFfUVVPVEVfTk9fRU5HSU5FPTEpIn0KICAgICAgICByb3dz
LmFwcGVuZChkaWN0KHsidGlja2VyIjogdCwgImFzb2YiOiBhc29mLCAic291cmNlIjogImVuZ2luZSIsICJlbmdpbmUiOiAieWZpbmFuY2UifSwgKiplbmcp
KQogICAgb3V0ID0geyJ2ZXJiIjogInF1b3RlIiwgInRzIjogZGF0ZXRpbWUuZGF0ZXRpbWUubm93KCkuaXNvZm9ybWF0KHRpbWVzcGVjPSJzZWNvbmRzIiks
ICJhc29mIjogYXNvZiwgInJvd3MiOiByb3dzLCAib2siOiBzdW0oMSBmb3IgciBpbiByb3dzIGlmIHIuZ2V0KCJvayIpKSwgIm4iOiBsZW4ocm93cyksICJk
YiI6IHN1bSgxIGZvciByIGluIHJvd3MgaWYgci5nZXQoInNvdXJjZSIpID09ICJkYiIgYW5kIHIuZ2V0KCJvayIpKSwgImVuZ2luZSI6IHN1bSgxIGZvciBy
IGluIHJvd3MgaWYgci5nZXQoInNvdXJjZSIpID09ICJlbmdpbmUiIGFuZCByLmdldCgib2siKSl9CiAgICBvdXRbImxhbXAiXSA9ICJHUkVFTiIgaWYgb3V0
WyJvayJdID09IG91dFsibiJdIGFuZCBvdXRbIm4iXSBlbHNlICgiWUVMTE9XIiBpZiBvdXRbIm9rIl0gZWxzZSAiUkVEIikKICAgIChvdXRfZGlyIC8gIlJF
U1VMVF9xdW90ZV9sYXRlc3QuanNvbiIpLndyaXRlX3RleHQoanNvbi5kdW1wcyhvdXQsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGlu
Zz0idXRmLTgiKQogICAgcmV0dXJuIG91dAoKCmRlZiBfcHJpbnRfcXVvdGUobzogZGljdCkgLT4gTm9uZToKICAgIHByaW50KCJb6KiIXSBWREYgcXVvdGUg
wrcgJWQg5qqUIMK3IOaIkCAlZChkYiAlZCDCtyDlvJXmk44gJWQpwrcgYXNvZiAlcyDCtyAlcyIgJSAob1sibiJdLCBvWyJvayJdLCBvWyJkYiJdLCBvWyJl
bmdpbmUiXSwgb1siYXNvZiJdLCBvWyJsYW1wIl0pKQogICAgZm9yIHIgaW4gb1sicm93cyJdWzo0MF06CiAgICAgICAgaWYgci5nZXQoIm9rIik6CiAgICAg
ICAgICAgIHByaW50KCIgIFtPS10gJXMgwrcgJXMgwrcg5pS2ICVzIMK3ICVzIiAlIChyWyJ0aWNrZXIiXSwgci5nZXQoImRhdGUiKSwgci5nZXQoImNsb3Nl
IiksIHJbInNvdXJjZSJdKSkKICAgICAgICBlbHNlOgogICAgICAgICAgICBwcmludCgiICBbWUVMXSAlcyDCtyAlcyIgJSAoclsidGlja2VyIl0sIHIuZ2V0
KCJ3aHkiKSkpCgoKZGVmIG1haW4oYXJndj1Ob25lKSAtPiBpbnQ6CiAgICBhcmdzID0gbGlzdChzeXMuYXJndlsxOl0gaWYgYXJndiBpcyBOb25lIGVsc2Ug
YXJndikKICAgIGlmICItLXNlbGZ0ZXN0IiBpbiBhcmdzWzoyXToKICAgICAgICByZXR1cm4gc2VsZnRlc3QoKQogICAgaWYgYXJnc1s6MV0gPT0gWyJxdW90
ZSJdOgogICAgICAgIGRlZiBvcHQoZmxhZywgZGVmYXVsdD1Ob25lKToKICAgICAgICAgICAgcmV0dXJuIGFyZ3NbYXJncy5pbmRleChmbGFnKSArIDFdIGlm
IGZsYWcgaW4gYXJncyBhbmQgYXJncy5pbmRleChmbGFnKSArIDEgPCBsZW4oYXJncykgZWxzZSBkZWZhdWx0CiAgICAgICAgdGtzID0gW3ggZm9yIHggaW4g
cmUuc3BsaXQociJbLFxzXSsiLCBvcHQoIi0tdGlja2VycyIsICIiKSBvciAiIikgaWYgeF0KICAgICAgICBpZiBub3QgdGtzOgogICAgICAgICAgICBwcmlu
dCgiW+aLkui3kV0gcXVvdGUgLS10aWNrZXJzIDIzMzAsMzcwNiBbLS1hc29mIFlZWVktTU0tRERdIFstLWRheXMgNV0iKQogICAgICAgICAgICByZXR1cm4g
MgogICAgICAgIG8gPSBxdW90ZSh0a3MsIG9wdCgiLS1hc29mIiksIGludChvcHQoIi0tZGF5cyIsICI1Iikgb3IgNSkpCiAgICAgICAgX3ByaW50X3F1b3Rl
KG8pCiAgICAgICAgcmV0dXJuIDEgaWYgb1sibGFtcCJdID09ICJSRUQiIGVsc2UgMAogICAgcmV0dXJuIFBSSU9SLm1haW4oYXJncykKCgpkZWYgc2VsZnRl
c3QoKSAtPiBpbnQ6CiAgICBpbXBvcnQgc2h1dGlsCiAgICBpbXBvcnQgdGVtcGZpbGUKICAgIHAgPSBmID0gMAoKICAgIGRlZiBjaGsobmFtZSwgY29uZCk6
CiAgICAgICAgbm9ubG9jYWwgcCwgZgogICAgICAgIGlmIGNvbmQ6CiAgICAgICAgICAgIHAgKz0gMQogICAgICAgICAgICBwcmludCgiICBbT0tdICVzIiAl
IG5hbWUpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZiArPSAxCiAgICAgICAgICAgIHByaW50KCIgIFtGQUlMXSAlcyIgJSBuYW1lKQoKICAgIHRkID0g
UGF0aCh0ZW1wZmlsZS5ta2R0ZW1wKHByZWZpeD0idmRmcS0iKSkKICAgIGhvbWUgPSB0ZCAvICJmdW5jdGlvbmFsIG1vZHVsZXMiIC8gIlZERiIKICAgICho
b21lIC8gIm91dHB1dF9odWIiIC8gImV4cG9ydCIpLm1rZGlyKHBhcmVudHM9VHJ1ZSkKICAgIHNhdmVkID0ge2s6IG9zLmVudmlyb24uZ2V0KGspIGZvciBr
IGluICgiVklBX1ZERl9IT01FIiwgIlZJQV9WREZfSEVBTFRIX09VVCIsICJWSUFfUVVPVEVfTk9fRU5HSU5FIil9CiAgICBvcy5lbnZpcm9uLnVwZGF0ZSh7
IlZJQV9WREZfSE9NRSI6IHN0cihob21lKSwgIlZJQV9WREZfSEVBTFRIX09VVCI6IHN0cih0ZCAvICJWSUFfUmVwb3J0cyIgLyAidmRmIiksICJWSUFfUVVP
VEVfTk9fRU5HSU5FIjogIjEifSkKICAgIChob21lIC8gIlZERl9TeXN0ZW1NYW5hZ2VyX3YwMTAwLnB5Iikud3JpdGVfdGV4dCgiaW1wb3J0IHN5c1xuZGVm
IG1haW4oYXJndj1Ob25lKTpcbiAgICByZXR1cm4gMFxuIiwgZW5jb2Rpbmc9InV0Zi04IikKICAgIChob21lIC8gIm91dHB1dF9odWIiIC8gImV4cG9ydCIg
LyAidmRmX3R3X21hcmtldF90d19kYWlseV9wcmljZXMuY3N2Iikud3JpdGVfdGV4dCgidGlja2VyLGRhdGUsY2xvc2VcbjIzMzAuVFcsMjAyNi0xMC0wMSwx
MjAwXG4yMzMwLlRXLDIwMjYtMTAtMDMsMTI1MFxuMzcwNiwyMDI2LTEwLTAyLDg4LjVcbiIsIGVuY29kaW5nPSJ1dGYtOCIpCiAgICBvID0gcXVvdGUoWyIy
MzMwIiwgIjM3MDYiLCAiOTk5OSJdLCBhc29mPSIyMDI2LTEwLTAyIikKICAgIFIgPSB7clsidGlja2VyIl06IHIgZm9yIHIgaW4gb1sicm93cyJdfQogICAg
Y2hrKCLikaAgZGIg5ZG95LitOjIzMzAg5Y+WIGFzb2Yg5YmN5pyA6L+R5pelIDEwLTAxIDEyMDAo6Z2eIDEwLTAzKcK3IDM3MDYgODguNSDCtyA5OTk5IOeE
oSDihpIg5byV5pOO6ZecIFlFTCIsIFJbIjIzMzAiXVsiY2xvc2UiXSA9PSAxMjAwIGFuZCBSWyIyMzMwIl1bImRhdGUiXSA9PSAiMjAyNi0xMC0wMSIgYW5k
IFJbIjM3MDYiXVsiY2xvc2UiXSA9PSA4OC41IGFuZCBub3QgUlsiOTk5OSJdWyJvayJdIGFuZCBvWyJkYiJdID09IDIgYW5kIG9bImxhbXAiXSA9PSAiWUVM
TE9XIikKICAgIGNoaygi4pGhIOe1kOaenOaqlCBSRVNVTFRfcXVvdGVfbGF0ZXN0Lmpzb24iLCAodGQgLyAiVklBX1JlcG9ydHMiIC8gInZkZiIgLyAiUkVT
VUxUX3F1b3RlX2xhdGVzdC5qc29uIikuZXhpc3RzKCkpCiAgICBwcmludCgiICDilIDilIAg5YmN54mI6Y+I6Ieq5risKOWOn+aoo+WNsOWHuinilIDilIAi
KQogICAgcHJjID0gMCBpZiBvcy5lbnZpcm9uLmdldCgiVklBX1NLSVBfUFJJT1JfU0VMRlRFU1QiKSA9PSAiMSIgZWxzZSBQUklPUi5zZWxmdGVzdCgpCiAg
ICBjaGsoIuKRoiDliY3niYjpj4ggJXMg6Ieq5risIHJjIDAiICUgUFJJT1JfUEFUSC5zdGVtLCBwcmMgPT0gMCkKICAgIGJvZHkgPSBQYXRoKF9fZmlsZV9f
KS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIGNoaygi4pGjIOS4ieapiyIsIGFsbCh0IGluIGJvZHkgZm9yIHQgaW4gKCJbVklBOkFDQ0VMLUJS
SURHRTp2MDEwMF0iLCAiW1ZJQTpORVQtQlJJREdFOnYwMTAwXSIsICJbVklBOkxJQi1CUklER0U6djAxMDBdIikpKQogICAgZm9yIGssIHYgaW4gc2F2ZWQu
aXRlbXMoKToKICAgICAgICBpZiB2IGlzIE5vbmU6CiAgICAgICAgICAgIG9zLmVudmlyb24ucG9wKGssIE5vbmUpCiAgICAgICAgZWxzZToKICAgICAgICAg
ICAgb3MuZW52aXJvbltrXSA9IHYKICAgIHNodXRpbC5ybXRyZWUodGQsIGlnbm9yZV9lcnJvcnM9VHJ1ZSkKICAgIHByaW50KCJb6KiIXSBWREZfU3lzdGVt
TWFuYWdlcl92MDE0NyDoh6rmuKwgJWQvJWQgwrcgJXMiICUgKHAsIHAgKyBmLCAiUEFTUyIgaWYgZiA9PSAwIGVsc2UgIkZBSUwiKSkKICAgIHJldHVybiAw
IGlmIGYgPT0gMCBlbHNlIDEKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcmFpc2UgU3lzdGVtRXhpdChtYWluKCkpCg==
'@
$ExH = Get-ChildItem -LiteralPath $RegDir -Filter 'CGC_MDL*_HealthMatrix_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($ExH -and $ExH.Name -match '^(CGC_MDL\d{3})_' -and $ExH.Name -lt ($Matches[1] + '_HealthMatrix_v0108.py')) { Install-VIAEmbedded -Path (Join-Path $RegDir ($Matches[1] + '_HealthMatrix_v0108.py')) -B64 $B64Hm -Want 'ece2fad2e50c68de42b3ff9a1a567c5c3f82d92902b47e36e664c8a100067d87' -Tag '健康矩陣引擎 v0108(restorepoint)' | Out-Null }
$okVdf = Install-VIATail $VdfDir 'VDF_SystemManager' 'v0147' $B64Vdf '855759b2b4f348033315bd77ceb8ae849564537038d65ea4e3c3e183167ea3a5' 'VDF v0147(quote:db → 引擎)'
$B64Vrn = @'
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJWUk5fU3lzdGVtTWFuYWdlciB2MDE0OSDigJQg6JaE5bC+KDIwMjYt
MTAtMDgg56ysIDEg6Lyq5a+m5risIDk3IOaqlCA3Ny4zJSDlvoznmoTkv64pOgogIOKRoCBsZXhpY29uIGFkZCAtLWZpbGUgPOijgeWumiBqc29uPiAgIOaT
jeS9nOWToStBSSDoo4HlrprnmoQgc3RkL+WIpeWQjeaJueasoemAsiBGaW5MZXhpY29uIOaWsOeJiCjlj6rlop475ZCMIHN0ZCDkvbXliKXlkI0s5pawIHN0
ZCDliqDliJc7cHJvdmVuYW5jZSnCtyDlkIzmmYLmioogbm9pc2VfcnVsZXMg5a2Y6YCy5YaKKHRyaWFnZSDlmarpn7Popo/liYcpCiAg4pGhIGV4dHJhY3Qg
dHJpYWdlIOWZqumfs+mBjua/viAgICAgICAgICDml6XmnJ8gLyDmrITpoK0oUW9RJSkvIOeroOWQjShCYWxhbmNlIFNoZWV0KS8g6KmV562JKOWinuWKoOaM
geiCoSkvIOS7o+iZnygwMDIyNzMuU1opLyDllq7kvY3lsL4g4oaSIOS4jeeul+OAjOiqjeS4jeWHuuWIl+aomeOAjSzlj6boqIjjgIzpnZ7liJfmqJkgTiDn
qK7jgI0KICDikaIgZXh0cmFjdCBsb29wIOesrCAyIOi8qui1t+eahCBSRVZJRVcg5riF5Zau5pS55b6e5pO35Y+W5biz6K6AKOWJjeeJiOW+nue1kOaenOeJ
qeS7tuiugOS4jeWIsOi3r+W+kSDihpIg6YeN5o6DIDApCiAg4pGjIGxleGljb24gcnVsZXMgICAgICAgICAgICAgICAgICAg5Y2w5YaK5LiK5Zmq6Z+z6KaP
5YmHCuWFtumkmOWLleipnueFp+WJjeeJiOmPiOOAggoiIiIKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwoKIyA9PT09PSBbVklBOkFDQ0VM
LUJSSURHRTp2MDEwMF0gU3VwZXJBY2NlbCDliqDpgJ/lmajmqYso5om5MTAyIOWFqOaoueWwjuWFpeS7pDtncmFjZWZ1bCDpm7booYzngrrorormm7QpID09
PT09CnRyeToKICAgIGltcG9ydCBzeXMgYXMgX3NhX3N5cwogICAgZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9zYV9QYXRoCiAgICBfc2FfcCA9IF9z
YV9QYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkKICAgIHdoaWxlIF9zYV9wLnBhcmVudCAhPSBfc2FfcDoKICAgICAgICBpZiAoX3NhX3AgLyAic3VwcG9ydGl2
ZSBtb2R1bGVzIiAvICJWSUFfU3VwZXJBY2NlbF9Nb2R1bGUucHkiKS5leGlzdHMoKToKICAgICAgICAgICAgX3NhX3N5cy5wYXRoLmluc2VydCgwLCBzdHIo
X3NhX3AgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIikpCiAgICAgICAgICAgIGJyZWFrCiAgICAgICAgX3NhX3AgPSBfc2FfcC5wYXJlbnQKICAgIGltcG9ydCBW
SUFfU3VwZXJBY2NlbF9Nb2R1bGUgYXMgVklBX0FDQ0VMICAjIG5vcWE6IEY0MDEKZXhjZXB0IEltcG9ydEVycm9yOgogICAgVklBX0FDQ0VMID0gTm9uZQoj
ID09PT09IFtWSUE6QUNDRUwtQlJJREdFOkVORF0gPT09PT0KCmltcG9ydCBkYXRldGltZQppbXBvcnQgaW1wb3J0bGliLnV0aWwKaW1wb3J0IGpzb24KaW1w
b3J0IG9zCmltcG9ydCByZQppbXBvcnQgc3lzCmZyb20gY29sbGVjdGlvbnMgaW1wb3J0IENvdW50ZXIKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpIRVJF
ID0gUGF0aChfX2ZpbGVfXykucmVzb2x2ZSgpLnBhcmVudApfU1RFTSA9ICJWUk5fU3lzdGVtTWFuYWdlciIKVEFHID0gInYwMTQ5IgoKCmRlZiBfdm51bV92
MDE0OShwYXRoKSAtPiBpbnQ6CiAgICBtID0gcmUuc2VhcmNoKHIiX3YoXGR7NH0pJCIsIFBhdGgocGF0aCkuc3RlbSkKICAgIHJldHVybiBpbnQobS5ncm91
cCgxKSkgaWYgbSBlbHNlIC0xCgoKZGVmIF9sb2FkX3YwMTQ5KHBhdGg6IFBhdGgsIG5hbWU6IHN0cik6CiAgICBpZiBuYW1lIG5vdCBpbiBzeXMubW9kdWxl
czoKICAgICAgICBzcGVjID0gaW1wb3J0bGliLnV0aWwuc3BlY19mcm9tX2ZpbGVfbG9jYXRpb24obmFtZSwgcGF0aCkKICAgICAgICBtb2QgPSBpbXBvcnRs
aWIudXRpbC5tb2R1bGVfZnJvbV9zcGVjKHNwZWMpCiAgICAgICAgc3lzLm1vZHVsZXNbbmFtZV0gPSBtb2QKICAgICAgICBzcGVjLmxvYWRlci5leGVjX21v
ZHVsZShtb2QpCiAgICByZXR1cm4gc3lzLm1vZHVsZXNbbmFtZV0KCgpQUklPUl9QQVRIID0gbWF4KChwIGZvciBwIGluIEhFUkUuZ2xvYihfU1RFTSArICJf
dioucHkiKSBpZiAwIDw9IF92bnVtX3YwMTQ5KHApIDwgX3ZudW1fdjAxNDkoX19maWxlX18pKSwga2V5PV92bnVtX3YwMTQ5KQpQUklPUiA9IF9sb2FkX3Yw
MTQ5KFBSSU9SX1BBVEgsIF9TVEVNICsgIl9wcmlvcl9mb3JfIiArIFBhdGgoX19maWxlX18pLnN0ZW0pCgoKZGVmIF9fZ2V0YXR0cl9fKG5hbWUpOgogICAg
cmV0dXJuIGdldGF0dHIoUFJJT1IsIG5hbWUpCgoKX0RFRkFVTFRfTk9JU0UgPSB7ImRhdGUiOiByIl4oXGR7MSwyfeaciFxzKlxkezEsMn0sP1xzKlxkezR9
fFvkuIDkuozkuInlm5vkupTlha3kuIPlhavkuZ3ljYFdK+aciFxzKlxkezEsMn0sP1xzKlxkezR9fFxkezR9Wy8tXVxkezEsMn1bLy1dXGR7MSwyfSkkIiwg
ImNvbHVtbl9oZWFkIjogciIoP2kpXihxb3F8eW95fG1vbXx5dGR8JXxcKCVcKXxxb3FcKCVcKXx5b3lcKCVcKXxjaGd8Y2hhbmdlfGVzdFwuP3xjb25zXC4/
fGFjdHVhbHxkaWZmKSQiLAogICAgICAgICAgICAgICAgICAic2VjdGlvbiI6IHIiKD9pKV4oYmFsYW5jZSBzaGVldHxpbmNvbWUgc3RhdGVtZW50fGNhc2gg
P2Zsb3coc3wgc3RhdGVtZW50KT98cmF0aW9zP3x2YWx1YXRpb258ZmluYW5jaWFsIHN1bW1hcnl8a2V5IGRhdGEpJCIsICJyYXRpbmciOiByIl4o5aKe5Yqg
5oyB6IKhfOmZjeS9juaMgeiCoXzosrfpgLJ86LOj5Ye6fOS4reeri3zmjIHmnIl85rib56K8fOWKoOeivHzlhKrmlrzlpKfnm6R85Yqj5pa85aSn55ukfOWN
gOmWk+aTjeS9nCkkIiwKICAgICAgICAgICAgICAgICAgInRpY2tlciI6IHIiXlxkezQsNn0oXC4oVFd8VFdPfFNafFNIfEhLfFQpKT8oIFRUKT8kIiwgInVu
aXRfdGFpbCI6IHIiKD9pKV4obnRcJHx1c1wkfHJtYnznmb7okKx85Y2DfOWEhCk/XHMqKG18bW58Ym58ayk/JCJ9CgoKZGVmIF9sZXhfdGFpbCgpOgogICAg
aGl0cyA9IHNvcnRlZCgoUFJJT1IuX2hvbWUoKSAvICJTU09UIikuZ2xvYigiVlJOX0ZpbkxleGljb25fU1NPVF92Ki5qc29uIiksIGtleT1sYW1iZGEgcTog
X3ZudW1fdjAxNDkocS5zdGVtKSkKICAgIHJldHVybiBoaXRzWy0xXSBpZiBoaXRzIGVsc2UgTm9uZQoKCmRlZiBub2lzZV9ydWxlcygpIC0+IGRpY3Q6CiAg
ICB0ID0gX2xleF90YWlsKCkKICAgIGlmIHQ6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkID0ganNvbi5sb2Fkcyh0LnJlYWRfdGV4dChlbmNvZGluZz0i
dXRmLTgtc2lnIikpCiAgICAgICAgICAgIGlmIGQuZ2V0KCJub2lzZV9ydWxlcyIpOgogICAgICAgICAgICAgICAgcmV0dXJuIGRbIm5vaXNlX3J1bGVzIl0K
ICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcGFzcwogICAgcmV0dXJuIGRpY3QoX0RFRkFVTFRfTk9JU0UpCgoKZGVmIGlzX25vaXNl
KGxhYmVsOiBzdHIsIHJ1bGVzOiBkaWN0IHwgTm9uZSA9IE5vbmUpIC0+IHN0ciB8IE5vbmU6CiAgICBzID0gcmUuc3ViKHIiXHMrIiwgIiAiLCBzdHIobGFi
ZWwgb3IgIiIpKS5zdHJpcCgpCiAgICBmb3IgaywgcnggaW4gKHJ1bGVzIG9yIG5vaXNlX3J1bGVzKCkpLml0ZW1zKCk6CiAgICAgICAgdHJ5OgogICAgICAg
ICAgICBpZiByZS5zZWFyY2gocngsIHMpOgogICAgICAgICAgICAgICAgcmV0dXJuIGsKICAgICAgICBleGNlcHQgcmUuZXJyb3I6CiAgICAgICAgICAgIGNv
bnRpbnVlCiAgICByZXR1cm4gTm9uZQoKCmRlZiBsZXhpY29uX2FkZChydWxpbmdzOiBkaWN0LCBhcHBseTogYm9vbCA9IFRydWUpIC0+IGRpY3Q6CiAgICB0
YWlsID0gX2xleF90YWlsKCkKICAgIGlmIG5vdCB0YWlsOgogICAgICAgIHJldHVybiB7InN0YXR1cyI6ICJOT19CT09LIiwgImxhbXAiOiAiUkVEIn0KICAg
IGJvb2sgPSBqc29uLmxvYWRzKHRhaWwucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciKSkKICAgIHJvd3MgPSBib29rLnNldGRlZmF1bHQoInJvd3Mi
LCBbXSkKICAgIGJ5X3N0ZCA9IHtyWyJzdGQiXTogciBmb3IgciBpbiByb3dzfQogICAgYWRkZWRfc3RkLCBhZGRlZF9hbGlhcyA9IDAsIDAKICAgIG5vdyA9
IGRhdGV0aW1lLmRhdGV0aW1lLm5vdygpLmlzb2Zvcm1hdCh0aW1lc3BlYz0ic2Vjb25kcyIpCiAgICBmb3IgciBpbiBydWxpbmdzLmdldCgiYWRkIiwgW10p
OgogICAgICAgIHN0ZCA9IHJbInN0ZCJdCiAgICAgICAgaWYgc3RkIGluIGJ5X3N0ZDoKICAgICAgICAgICAgY3VyID0gYnlfc3RkW3N0ZF0KICAgICAgICAg
ICAgZm9yIGZsZCBpbiAoInpoIiwgImVuIik6CiAgICAgICAgICAgICAgICBmb3IgYSBpbiByLmdldChmbGQpIG9yIFtdOgogICAgICAgICAgICAgICAgICAg
IGlmIGEgbm90IGluIChjdXIuZ2V0KCJ6aCIpIG9yIFtdKSBhbmQgYSBub3QgaW4gKGN1ci5nZXQoImVuIikgb3IgW10pOgogICAgICAgICAgICAgICAgICAg
ICAgICBjdXIuc2V0ZGVmYXVsdChmbGQsIFtdKS5hcHBlbmQoYSkKICAgICAgICAgICAgICAgICAgICAgICAgY3VyLnNldGRlZmF1bHQoInByb3ZlbmFuY2Ui
LCBbXSkuYXBwZW5kKHsiYWxpYXMiOiBhLCAidHMiOiBub3csICJydWxlIjogIuaTjeS9nOWToStBSSDoo4HlrprmibnmrKEiLCAiYmF0Y2giOiBydWxpbmdz
LmdldCgib3JpZ2luIiwgIiIpWzo2MF19KQogICAgICAgICAgICAgICAgICAgICAgICBhZGRlZF9hbGlhcyArPSAxCiAgICAgICAgZWxzZToKICAgICAgICAg
ICAgbmV3ID0geyJzdGQiOiBzdGQsICJjYXQiOiByLmdldCgiY2F0IiwgIk9USEVSIiksICJ6aCI6IGxpc3Qoci5nZXQoInpoIikgb3IgW10pLCAiZW4iOiBs
aXN0KHIuZ2V0KCJlbiIpIG9yIFtdKSwgInByb3ZlbmFuY2UiOiBbeyJ0cyI6IG5vdywgInJ1bGUiOiAi5pON5L2c5ZOhK0FJIOijgeWumuaJueasoSjmlrAg
c3RkKSIsICJiYXRjaCI6IHJ1bGluZ3MuZ2V0KCJvcmlnaW4iLCAiIilbOjYwXX1dfQogICAgICAgICAgICByb3dzLmFwcGVuZChuZXcpCiAgICAgICAgICAg
IGJ5X3N0ZFtzdGRdID0gbmV3CiAgICAgICAgICAgIGFkZGVkX3N0ZCArPSAxCiAgICBpZiBydWxpbmdzLmdldCgibm9pc2VfcnVsZXMiKToKICAgICAgICBu
ciA9IGRpY3QoYm9vay5nZXQoIm5vaXNlX3J1bGVzIikgb3Ige30pCiAgICAgICAgbnIudXBkYXRlKHJ1bGluZ3NbIm5vaXNlX3J1bGVzIl0pCiAgICAgICAg
Ym9va1sibm9pc2VfcnVsZXMiXSA9IG5yCiAgICBvdXQgPSB7InN0YXR1cyI6ICJQTEFOIiwgInRhaWwiOiB0YWlsLm5hbWUsICJhZGRlZF9zdGQiOiBhZGRl
ZF9zdGQsICJhZGRlZF9hbGlhcyI6IGFkZGVkX2FsaWFzLCAicm93cyI6IGxlbihyb3dzKSwgIm5vaXNlX3J1bGVzIjogbGVuKGJvb2suZ2V0KCJub2lzZV9y
dWxlcyIpIG9yIHt9KSwgImxhbXAiOiAiR1JFRU4ifQogICAgaWYgYXBwbHkgYW5kIChhZGRlZF9zdGQgb3IgYWRkZWRfYWxpYXMgb3IgcnVsaW5ncy5nZXQo
Im5vaXNlX3J1bGVzIikpOgogICAgICAgIG52ID0gInYlMDRkIiAlIChfdm51bV92MDE0OSh0YWlsLnN0ZW0pICsgMSkKICAgICAgICBuZXcgPSB0YWlsLndp
dGhfbmFtZSgiVlJOX0ZpbkxleGljb25fU1NPVF8lcy5qc29uIiAlIG52KQogICAgICAgIGJvb2tbInZlcnNpb24iXSwgYm9va1sicHJpb3IiXSA9IG52LCB0
YWlsLm5hbWUKICAgICAgICBib29rWyJvcmlnaW4iXSA9IChib29rLmdldCgib3JpZ2luIiwgIiIpICsgIjsiICsgcnVsaW5ncy5nZXQoIm9yaWdpbiIsICLo
o4HlrprmibnmrKEiKSlbOjMwMDBdCiAgICAgICAgbmV3LndyaXRlX3RleHQoanNvbi5kdW1wcyhib29rLCBlbnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0x
KSwgZW5jb2Rpbmc9InV0Zi04IikKICAgICAgICBvdXQudXBkYXRlKHN0YXR1cz0iV1JJVFRFTiIsIG5ldz1uZXcubmFtZSkKICAgIHJldHVybiBvdXQKCgpf
VFJJXzQ4ID0gUFJJT1IuX3Jlc29sdmUoImV4dHJhY3RfdHJpYWdlIikKCgpkZWYgZXh0cmFjdF90cmlhZ2UodG9wOiBpbnQgPSA0MCkgLT4gZGljdDoKICAg
IG8gPSBfVFJJXzQ4KHRvcD0yMDApIGlmIF9UUklfNDggZWxzZSB7InVubWF0Y2hlZF9sYWJlbHMiOiBbXSwgImxhbXAiOiAiR1JBWSJ9CiAgICBydWxlcyA9
IG5vaXNlX3J1bGVzKCkKICAgIGtlZXAsIG5vaXNlID0gW10sIENvdW50ZXIoKQogICAgZm9yIHUgaW4gby5nZXQoInVubWF0Y2hlZF9sYWJlbHMiLCBbXSk6
CiAgICAgICAgayA9IGlzX25vaXNlKHUuZ2V0KCJsYWJlbCIsICIiKSwgcnVsZXMpCiAgICAgICAgaWYgazoKICAgICAgICAgICAgbm9pc2Vba10gKz0gMQog
ICAgICAgIGVsc2U6CiAgICAgICAgICAgIGtlZXAuYXBwZW5kKHUpCiAgICBvWyJ1bm1hdGNoZWRfbGFiZWxzIl0gPSBrZWVwWzp0b3BdCiAgICBvWyJub2lz
ZSJdID0gZGljdChub2lzZSkKICAgIG9bImxhbXAiXSA9ICJZRUxMT1ciIGlmIGtlZXAgZWxzZSAiR1JFRU4iCiAgICByZXR1cm4gbwoKCl9MT09QXzQ4ID0g
UFJJT1IuZXh0cmFjdF9sb29wCgoKZGVmIGV4dHJhY3RfbG9vcChkOiBQYXRoLCByb3VuZHM6IGludCA9IDIsIGxpbWl0OiBpbnQgPSAwLCBtaW5fZG9jczog
aW50ID0gMikgLT4gZGljdDoKICAgICIiIuWQjCB2MDE0OCzkvYbnrKwgMiDovKrotbcgUkVWSUVXIOa4heWWruW+nuW4s+iugDt0cmlhZ2Ug55So5pys54mI
KOW3sua/vuWZqumfsynjgIIiIiIKICAgIGV4dF9mbiA9IFBSSU9SLl9yZXNvbHZlKCJleHRyYWN0IikKICAgIGZpbGVzID0gc29ydGVkKHAgZm9yIHAgaW4g
ZC5yZ2xvYigiKi5wZGYiKSkgaWYgZC5pc19kaXIoKSBlbHNlIFtdCiAgICBvdXQgPSB7InZlcmIiOiAiZXh0cmFjdF9sb29wIiwgImRpciI6IHN0cihkKSwg
InJvdW5kcyI6IFtdLCAibGFtcCI6ICJHUkFZIn0KICAgIGlmIG5vdCAoZXh0X2ZuIGFuZCBmaWxlcyk6CiAgICAgICAgb3V0LnVwZGF0ZSh3aHk9IumPiOS4
iuaykuaciSBleHRyYWN0IiBpZiBub3QgZXh0X2ZuIGVsc2UgIuWkvuijoeaykuaciSBQREYiLCBsYW1wPSJSRUQiKQogICAgICAgIHJldHVybiBvdXQKICAg
IHRvZG8gPSBmaWxlcwogICAgYWQgPSB7ImFkb3B0ZWQiOiBbXSwgInBlbmRpbmciOiBbXX0KICAgIGZvciByIGluIHJhbmdlKDEsIHJvdW5kcyArIDEpOgog
ICAgICAgIHJlcyA9IGV4dF9mbih0b2RvLCAoInBkZnBsdW1iZXIiLCAiY2FtZWxvdCIsICJ0YWJ1bGEiKSwgbGltaXQgaWYgciA9PSAxIGVsc2UgMCkKICAg
ICAgICBjb3VudHMgPSBDb3VudGVyKCh4LmdldCgic3RhdHVzIikgb3IgIj8iKSBmb3IgeCBpbiByZXMuZ2V0KCJkb2NzIiwgcmVzLmdldCgiZmlsZXMiLCBb
XSkpIGlmIGlzaW5zdGFuY2UoeCwgZGljdCkpCiAgICAgICAgdHJpID0gZXh0cmFjdF90cmlhZ2UoKQogICAgICAgIGFkID0gUFJJT1IubGV4aWNvbl9hdXRv
X2Fkb3B0KHRyaS5nZXQoInVubWF0Y2hlZF9sYWJlbHMiLCBbXSksIG1pbl9kb2NzPW1pbl9kb2NzLCBhcHBseT1UcnVlKQogICAgICAgIGxlZCA9IFBSSU9S
Ll9sZWRnZXJfc3RhdHVzKCkKICAgICAgICB3YW50ID0ge3N0cihwLnJlc29sdmUoKSkubG93ZXIoKSBmb3IgcCBpbiBmaWxlc30KICAgICAgICByZXZpZXdf
ZmlsZXMgPSBbXQogICAgICAgIGZvciBrLCBqIGluIGxlZC5pdGVtcygpOgogICAgICAgICAgICBpZiAoai5nZXQoInN0YXR1cyIpIGluICgiUkVWSUVXIiwg
Ik5PREFUQSIpKToKICAgICAgICAgICAgICAgIHB0aCA9IGouZ2V0KCJwYXRoIikgb3Igai5nZXQoImZpbGUiKSBvciBrCiAgICAgICAgICAgICAgICB0cnk6
CiAgICAgICAgICAgICAgICAgICAgcHAgPSBQYXRoKHB0aCkKICAgICAgICAgICAgICAgICAgICBpZiBwcC5leGlzdHMoKSBhbmQgc3RyKHBwLnJlc29sdmUo
KSkubG93ZXIoKSBpbiB3YW50OgogICAgICAgICAgICAgICAgICAgICAgICByZXZpZXdfZmlsZXMuYXBwZW5kKHBwKQogICAgICAgICAgICAgICAgZXhjZXB0
IChPU0Vycm9yLCBWYWx1ZUVycm9yKToKICAgICAgICAgICAgICAgICAgICBwYXNzCiAgICAgICAgcmV2aWV3X2ZpbGVzID0gc29ydGVkKHNldChyZXZpZXdf
ZmlsZXMpKQogICAgICAgIG91dFsicm91bmRzIl0uYXBwZW5kKHsicm91bmQiOiByLCAic2Nhbm5lZCI6IGxlbih0b2RvKSwgImNvdW50cyI6IGRpY3QoY291
bnRzKSwgImFkb3B0ZWQiOiBsZW4oYWRbImFkb3B0ZWQiXSksICJwZW5kaW5nIjogbGVuKGFkWyJwZW5kaW5nIl0pLCAibm9pc2UiOiB0cmkuZ2V0KCJub2lz
ZSIsIHt9KSwgImxleGljb24iOiBhZC5nZXQoIm5ldyIpIG9yIGFkLmdldCgidGFpbCIpLCAicmV2aWV3X25leHQiOiBsZW4ocmV2aWV3X2ZpbGVzKX0pCiAg
ICAgICAgaWYgbm90IGFkWyJhZG9wdGVkIl0gb3Igbm90IHJldmlld19maWxlczoKICAgICAgICAgICAgYnJlYWsKICAgICAgICB0b2RvID0gcmV2aWV3X2Zp
bGVzCiAgICBnYXRlID0gUFJJT1IuZXh0cmFjdF9nYXRlKCkKICAgIG91dC51cGRhdGUoZ2F0ZT1nYXRlLCBwZW5kaW5nX2xhYmVscz1hZFsicGVuZGluZyJd
Wzo0MF0sIGxhbXA9Z2F0ZVsibGFtcCJdKQogICAgcmV0dXJuIG91dAoKCmRlZiBfcHJpbnRfbG9vcChvOiBkaWN0KSAtPiBOb25lOgogICAgaWYgby5nZXQo
IndoeSIpOgogICAgICAgIHByaW50KCJb6KiIXSBWUk4gZXh0cmFjdCBsb29wIMK3ICVzIMK3ICVzIiAlIChvWyJ3aHkiXSwgb1sibGFtcCJdKSkKICAgICAg
ICByZXR1cm4KICAgIGZvciByIGluIG9bInJvdW5kcyJdOgogICAgICAgIHByaW50KCJb6KiIXSBleHRyYWN0IGxvb3Ag56ysICVkIOi8qiDCtyDmjoMgJWQg
wrcgJXMgwrcg6Ieq5YuV5o6h57SNICVkIMK3IOacquinoyAlZCDCtyDpnZ7liJfmqJkgJXMgwrcg5YaKICVzIMK3IOS4i+i8qumHjeaOgyAlZCIgJSAoclsi
cm91bmQiXSwgclsic2Nhbm5lZCJdLCAiICIuam9pbigiJXM9JWQiICUga3YgZm9yIGt2IGluIHNvcnRlZChyWyJjb3VudHMiXS5pdGVtcygpKSksIHJbImFk
b3B0ZWQiXSwgclsicGVuZGluZyJdLCAiICIuam9pbigiJXM9JWQiICUga3YgZm9yIGt2IGluIHNvcnRlZChyWyJub2lzZSJdLml0ZW1zKCkpKSBvciAiMCIs
IHJbImxleGljb24iXSwgclsicmV2aWV3X25leHQiXSkpCiAgICBnID0gb1siZ2F0ZSJdCiAgICBwcmludCgiW+ioiF0g5a6M5bel6ZaA5qq7IMK3IOaqlCAl
ZCDCtyAlcyDCtyDoia/njocgJS4xZiUlIMK3IFJFVklFVyAlZCDCtyBFUlJPUiAlZCDCtyAlcyDCtyAlcyIgJSAoZ1sibiJdLCAiICIuam9pbigiJXM9JWQi
ICUga3YgZm9yIGt2IGluIHNvcnRlZChnWyJjb3VudHMiXS5pdGVtcygpKSksIGdbImdvb2RfcmF0aW8iXSAqIDEwMCwgZ1sicmV2aWV3Il0sIGdbImVycm9y
Il0sIGdbInJ1bGUiXSwgZ1sibGFtcCJdKSkKICAgIGZvciB4IGluIG8uZ2V0KCJwZW5kaW5nX2xhYmVscyIsIFtdKVs6NDBdOgogICAgICAgIHByaW50KCIg
IFtZRUxdIOWIl+aomSAlcyDCtyAlZCDmrKEgwrcgJWQg5qqUKOetieaTjeS9nOWToStBSSkiICUgKHguZ2V0KCJsYWJlbCIpLCB4LmdldCgibiIsIDApLCB4
LmdldCgiZG9jcyIsIDApKSkKICAgIHByaW50KCJORVhUOiAlcyIgJSAoIuWujOW3pTpWUk4g5a+m5ris6YGO6ZaA5qq7IiBpZiBnWyJsYW1wIl0gPT0gIkdS
RUVOIiBlbHNlICLmioogW1lFTF0g5YiX5qiZ6LK857WmIEFJIOKGkiBsZXhpY29uIGFkZCDihpIg5YaN6LeRIGV4dHJhY3QgbG9vcCjlj6rph43mjoMgUkVW
SUVXKSIpKQoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgYXJncyA9IGxpc3Qoc3lzLmFyZ3ZbMTpdIGlmIGFyZ3YgaXMgTm9uZSBlbHNlIGFy
Z3YpCiAgICBvcy5lbnZpcm9uLnNldGRlZmF1bHQoIlZJQV9GUk9NX1ZDR0MiLCAiWUVTIikKICAgIGlmICItLXNlbGZ0ZXN0IiBpbiBhcmdzWzoyXToKICAg
ICAgICByZXR1cm4gc2VsZnRlc3QoKQoKICAgIGRlZiBvcHQoZmxhZywgZGVmYXVsdD1Ob25lKToKICAgICAgICByZXR1cm4gYXJnc1thcmdzLmluZGV4KGZs
YWcpICsgMV0gaWYgZmxhZyBpbiBhcmdzIGFuZCBhcmdzLmluZGV4KGZsYWcpICsgMSA8IGxlbihhcmdzKSBlbHNlIGRlZmF1bHQKICAgIGlmIGFyZ3NbOjJd
ID09IFsibGV4aWNvbiIsICJhZGQiXToKICAgICAgICBmcCA9IFBhdGgob3B0KCItLWZpbGUiLCAiIikpCiAgICAgICAgaWYgbm90IGZwLmV4aXN0cygpOgog
ICAgICAgICAgICBwcmludCgiW+aLkui3kV0gbGV4aWNvbiBhZGQgLS1maWxlIDzoo4HlrpoganNvbj4iKQogICAgICAgICAgICByZXR1cm4gMgogICAgICAg
IHIgPSBsZXhpY29uX2FkZChqc29uLmxvYWRzKGZwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpLCBhcHBseT0oIi0tZHJ5IiBub3QgaW4gYXJn
cykpCiAgICAgICAgcHJpbnQoIlvoqIhdIFZSTiBsZXhpY29uIGFkZCDCtyAlcyDCtyAlcyDihpIgJXMgwrcg5pawIHN0ZCAlZCDCtyDmlrDliKXlkI0gJWQg
wrcg5YiXICVkIMK3IOWZqumfs+imj+WJhyAlZCDCtyAlcyIgJSAoclsic3RhdHVzIl0sIHIuZ2V0KCJ0YWlsIiksIHIuZ2V0KCJuZXciLCAi4oCUIiksIHIu
Z2V0KCJhZGRlZF9zdGQiLCAwKSwgci5nZXQoImFkZGVkX2FsaWFzIiwgMCksIHIuZ2V0KCJyb3dzIiwgMCksIHIuZ2V0KCJub2lzZV9ydWxlcyIsIDApLCBy
WyJsYW1wIl0pKQogICAgICAgIHJldHVybiAwIGlmIHJbImxhbXAiXSAhPSAiUkVEIiBlbHNlIDEKICAgIGlmIGFyZ3NbOjJdID09IFsibGV4aWNvbiIsICJy
dWxlcyJdOgogICAgICAgIGZvciBrLCB2IGluIG5vaXNlX3J1bGVzKCkuaXRlbXMoKToKICAgICAgICAgICAgcHJpbnQoIiAgW09LXSAlcyDCtyAlcyIgJSAo
aywgdikpCiAgICAgICAgcmV0dXJuIDAKICAgIGlmIGFyZ3NbOjJdID09IFsiZXh0cmFjdCIsICJ0cmlhZ2UiXToKICAgICAgICBvID0gZXh0cmFjdF90cmlh
Z2UoKQogICAgICAgIHByaW50KCJb6KiIXSBleHRyYWN0IHRyaWFnZSDCtyDmqpQgJXMgwrcg6KqN5LiN5Ye65YiX5qiZICVkIOeoriDCtyDpnZ7liJfmqJkg
JXMgwrcgJXMiICUgKG8uZ2V0KCJkb2NzIiksIGxlbihvWyJ1bm1hdGNoZWRfbGFiZWxzIl0pLCAiICIuam9pbigiJXM9JWQiICUga3YgZm9yIGt2IGluIHNv
cnRlZChvLmdldCgibm9pc2UiLCB7fSkuaXRlbXMoKSkpIG9yICIwIiwgb1sibGFtcCJdKSkKICAgICAgICBmb3IgeCBpbiBvWyJ1bm1hdGNoZWRfbGFiZWxz
Il06CiAgICAgICAgICAgIHByaW50KCIgIFtZRUxdIOWIl+aomSAlcyDCtyAlZCDmrKEgwrcgJWQg5qqUIiAlICh4WyJsYWJlbCJdLCB4WyJuIl0sIHhbImRv
Y3MiXSkpCiAgICAgICAgcmV0dXJuIDAKICAgIGlmIGFyZ3NbOjJdID09IFsiZXh0cmFjdCIsICJsb29wIl06CiAgICAgICAgbyA9IGV4dHJhY3RfbG9vcChQ
YXRoKG9wdCgiLS1kaXIiKSBvciAoSEVSRSAvICJpbnB1dCIgLyAiaW5jb21pbmciKSksIGludChvcHQoIi0tcm91bmRzIiwgIjIiKSBvciAyKSwgaW50KG9w
dCgiLS1saW1pdCIsICIwIikgb3IgMCksIGludChvcHQoIi0tbWluLWRvY3MiLCAiMiIpIG9yIDIpKQogICAgICAgIF9wcmludF9sb29wKG8pCiAgICAgICAg
cmV0dXJuIDEgaWYgb1sibGFtcCJdID09ICJSRUQiIGVsc2UgMAogICAgcmV0dXJuIFBSSU9SLm1haW4oYXJncykKCgpkZWYgc2VsZnRlc3QoKSAtPiBpbnQ6
CiAgICBpbXBvcnQgc2h1dGlsCiAgICBpbXBvcnQgdGVtcGZpbGUKICAgIHAgPSBmID0gMAoKICAgIGRlZiBjaGsobmFtZSwgY29uZCk6CiAgICAgICAgbm9u
bG9jYWwgcCwgZgogICAgICAgIGlmIGNvbmQ6CiAgICAgICAgICAgIHAgKz0gMQogICAgICAgICAgICBwcmludCgiICBbT0tdICVzIiAlIG5hbWUpCiAgICAg
ICAgZWxzZToKICAgICAgICAgICAgZiArPSAxCiAgICAgICAgICAgIHByaW50KCIgIFtGQUlMXSAlcyIgJSBuYW1lKQoKICAgIHRkID0gUGF0aCh0ZW1wZmls
ZS5ta2R0ZW1wKHByZWZpeD0idnJubGV4LSIpKQogICAgaG9tZSA9IHRkIC8gImZ1bmN0aW9uYWwgbW9kdWxlcyIgLyAiVlJOIgogICAgKGhvbWUgLyAiU1NP
VCIpLm1rZGlyKHBhcmVudHM9VHJ1ZSkKICAgIHNhdmVkID0gb3MuZW52aXJvbi5nZXQoIlZJQV9WUk5fU1NPVF9IT01FIikKICAgIG9zLmVudmlyb25bIlZJ
QV9WUk5fU1NPVF9IT01FIl0gPSBzdHIoaG9tZSkKICAgIChob21lIC8gIlNTT1QiIC8gIlZSTl9GaW5MZXhpY29uX1NTT1RfdjAxMDIuanNvbiIpLndyaXRl
X3RleHQoanNvbi5kdW1wcyh7InZlcnNpb24iOiAidjAxMDIiLCAicm93cyI6IFt7InN0ZCI6ICJyZXZlbnVlIiwgImNhdCI6ICJJUyIsICJ6aCI6IFsi54ef
5qWt5pS25YWlIl0sICJlbiI6IFsiUmV2ZW51ZSJdfV19LCBlbnN1cmVfYXNjaWk9RmFsc2UpLCBlbmNvZGluZz0idXRmLTgiKQogICAgciA9IGxleGljb25f
YWRkKHsib3JpZ2luIjogInQiLCAiYWRkIjogW3sic3RkIjogInJldmVudWUiLCAiY2F0IjogIklTIiwgInpoIjogWyLnh5/mpa3mlLbnm4oiXSwgImVuIjog
W119LCB7InN0ZCI6ICJpbnRlcmVzdF9leHBlbnNlIiwgImNhdCI6ICJJUyIsICJ6aCI6IFsi5Yip5oGv6LK755SoIl0sICJlbiI6IFsiSW50ZXJlc3QgZXhw
ZW5zZSJdfV0sICJub2lzZV9ydWxlcyI6IF9ERUZBVUxUX05PSVNFfSkKICAgIGJvb2sgPSBqc29uLmxvYWRzKChob21lIC8gIlNTT1QiIC8gIlZSTl9GaW5M
ZXhpY29uX1NTT1RfdjAxMDMuanNvbiIpLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKSkKICAgIGNoaygi4pGgIGxleGljb24gYWRkOuWQjCBzdGQg5L21
5Yil5ZCNKOeHn+alreaUtuebiuKGknJldmVudWUpwrcg5pawIHN0ZCDliqDliJcgwrcgbm9pc2VfcnVsZXMg5YWl5YaKIMK3IOWHuiB2MDEwMyIsIHJbInN0
YXR1cyJdID09ICJXUklUVEVOIiBhbmQgclsiYWRkZWRfc3RkIl0gPT0gMSBhbmQgclsiYWRkZWRfYWxpYXMiXSA9PSAxIGFuZCAi54ef5qWt5pS255uKIiBp
biBuZXh0KHggZm9yIHggaW4gYm9va1sicm93cyJdIGlmIHhbInN0ZCJdID09ICJyZXZlbnVlIilbInpoIl0gYW5kIGJvb2suZ2V0KCJub2lzZV9ydWxlcyIp
KQogICAgY2hrKCLikaEg5Zmq6Z+zOuS6lOaciCAxOSwgMjAyNj1kYXRlIMK3IFFvUSglKT1jb2x1bW5faGVhZCDCtyBCYWxhbmNlIFNoZWV0PXNlY3Rpb24g
wrcg5aKe5Yqg5oyB6IKhPXJhdGluZyDCtyAwMDIyNzMuU1o9dGlja2VyIMK3IOe4vSDnh58g5qWtIOWkliDmlLYg5YWlIOS4jeaYr+WZqumfsyIsIGlzX25v
aXNlKCLkupTmnIggMTksIDIwMjYiKSA9PSAiZGF0ZSIgYW5kIGlzX25vaXNlKCJRb1EoJSkiKSA9PSAiY29sdW1uX2hlYWQiIGFuZCBpc19ub2lzZSgiQmFs
YW5jZSBTaGVldCIpID09ICJzZWN0aW9uIiBhbmQgaXNfbm9pc2UoIuWinuWKoOaMgeiCoSIpID09ICJyYXRpbmciIGFuZCBpc19ub2lzZSgiMDAyMjczLlNa
IikgPT0gInRpY2tlciIgYW5kIGlzX25vaXNlKCLnuL0g54efIOalrSDlpJYg5pS2IOWFpSIpIGlzIE5vbmUpCiAgICBwcmludCgiICDilIDilIAg5YmN54mI
6Y+I6Ieq5risKOWOn+aoo+WNsOWHuinilIDilIAiKQogICAgcHJjID0gMCBpZiBvcy5lbnZpcm9uLmdldCgiVklBX1NLSVBfUFJJT1JfU0VMRlRFU1QiKSA9
PSAiMSIgZWxzZSBQUklPUi5zZWxmdGVzdCgpCiAgICBjaGsoIuKRoiDliY3niYjpj4ggJXMg6Ieq5risIHJjIDAiICUgUFJJT1JfUEFUSC5zdGVtLCBwcmMg
PT0gMCkKICAgIGJvZHkgPSBQYXRoKF9fZmlsZV9fKS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIGNoaygi4pGjIOW4tuWKoOmAn+WZqOapiyDC
tyDlj6rlop4iLCAiW1ZJQTpBQ0NFTC1CUklER0U6djAxMDBdIiBpbiBib2R5IGFuZCAoaG9tZSAvICJTU09UIiAvICJWUk5fRmluTGV4aWNvbl9TU09UX3Yw
MTAyLmpzb24iKS5leGlzdHMoKSkKICAgIGlmIHNhdmVkIGlzIE5vbmU6CiAgICAgICAgb3MuZW52aXJvbi5wb3AoIlZJQV9WUk5fU1NPVF9IT01FIiwgTm9u
ZSkKICAgIGVsc2U6CiAgICAgICAgb3MuZW52aXJvblsiVklBX1ZSTl9TU09UX0hPTUUiXSA9IHNhdmVkCiAgICBzaHV0aWwucm10cmVlKHRkLCBpZ25vcmVf
ZXJyb3JzPVRydWUpCiAgICBwcmludCgiW+ioiF0gVlJOX1N5c3RlbU1hbmFnZXJfdjAxNDkg6Ieq5risICVkLyVkIMK3ICVzIiAlIChwLCBwICsgZiwgIlBB
U1MiIGlmIGYgPT0gMCBlbHNlICJGQUlMIikpCiAgICByZXR1cm4gMCBpZiBmID09IDAgZWxzZSAxCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAg
IHJhaXNlIFN5c3RlbUV4aXQobWFpbigpKQo=
'@
$okVrn = Install-VIATail $VrnDir 'VRN_SystemManager' 'v0149' $B64Vrn '2371519950d7a0b1760eb6653a67d88830fb70c2b2fba31123dc0c329340dc06' 'VRN v0149(lexicon add · triage 噪音 · loop 讀帳)'
$PyHm = (Get-ChildItem -LiteralPath $RegDir -Filter 'CGC_MDL*_HealthMatrix_v*.py' | Sort-Object Name | Select-Object -Last 1).FullName
$PyVrn = (Get-ChildItem -LiteralPath $VrnDir -Filter 'VRN_SystemManager_v*.py' | Sort-Object Name | Select-Object -Last 1).FullName
$PyVdf = (Get-ChildItem -LiteralPath $VdfDir -Filter 'VDF_SystemManager_v*.py' | Sort-Object Name | Select-Object -Last 1).FullName
$Repo = $VIA; while ($Repo -and -not (Test-Path -LiteralPath (Join-Path $Repo '.git'))) { $Repo = [IO.Path]::GetDirectoryName($Repo) }
$GitSha = if ($Repo) { (& git -C $Repo rev-parse --short HEAD 2>$null) } else { '' }
$env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'
if ($Demo) {
  $Lanes = @(
    @{ id = 'A'; zh = '示範:PS 短令(via-vcgc token)'; args = @($VIA, $Reg, $LogDir); run = { param($VIA, $Reg, $LogDir) Set-Location $VIA; . $Reg | Out-Null; Set-Content (Join-Path $LogDir 'A.progress') '30 · token' -Encoding UTF8; via-vcgc token 2>&1 | Select-String '\[計\]|已啟用|GREEN|RED' | ForEach-Object { $_.Line.Trim() } | Select-Object -Last 3; Set-Content (Join-Path $LogDir 'A.progress') '100 · 完' -Encoding UTF8 } },
    @{ id = 'B'; zh = '示範:python 引擎自測(MDL256)'; args = @($VIA, $LogDir, $PyStepSec); run = { param($VIA, $LogDir, $Sec) Set-Location $VIA; Set-Content (Join-Path $LogDir 'B.progress') '20 · selftest' -Encoding UTF8
        $eng = "$VIA\supportive modules\registry\CGC_MDL256_AiVerbBridge_v0100.py"; if (-not (Test-Path $eng)) { "[RED] $eng 不在"; return }
        $json = (@($eng, '--selftest') | ConvertTo-Json -Compress); $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
        $wrap = "import base64,json,os,sys,threading,runpy; a=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); threading.Timer($Sec, lambda: (sys.stdout.flush(), os._exit(124))).start(); sys.argv=a; runpy.run_path(a[0], run_name='__main__')"
        & python -c $wrap $b64 2>&1 | Select-String '\[計\]|FAIL' | ForEach-Object { $_.Line.Trim() }; "rc $LASTEXITCODE"; Set-Content (Join-Path $LogDir 'B.progress') '100 · 完' -Encoding UTF8 } })
  Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir
} else {
  function Add-VIAPyLines { param([string]$Id, [string[]]$Lines, [int]$Max = 40)
    $Lines | Where-Object { $_ -match '^\[計\]|^\s*\[(OK|YEL|RED|注|RP|TAG|U\/I|MATRIX)\]|^NEXT:' } | Select-Object -First $Max | ForEach-Object { $l = $_.Trim(); if ($l -match '^\s*\[RED\]') { $script:Errors.Add("[$Id] $l") } else { $script:Verdicts.Add("[$Id] $l") } } }
  # ---------- A ∥ B:還原點(零紅才鎖)∥ VRN 自報齊全度 ----------
  $LaneA = { param($VIA, $PyHm, $Note, $GitSha, $Repo, $LogDir, $Force)
    Set-Content -LiteralPath (Join-Path $LogDir 'A.progress') '20 · 三系統健康' -Encoding UTF8
    $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'
    $fa = @(); if ($Force) { $fa = @('--force') }
    $o = @(& python $PyHm 'restorepoint' '--note' $Note '--git' $GitSha @fa 2>&1 | ForEach-Object { "" + $_ })
    $o | Where-Object { $_ -match '^\[計\]|^\s*\[(RED|RP|TAG)\]' } | ForEach-Object { $_ }
    $tag = ($o | Where-Object { $_ -match '^\s*\[TAG\] (rp/\S+)' } | ForEach-Object { $Matches[1] } | Select-Object -First 1)
    if ($tag -and $Repo) { & git -C $Repo tag -f $tag 2>&1 | Out-Null; & git -C $Repo push -f origin $tag 2>&1 | Out-Null; "[計] git tag $tag @ $GitSha 已推 origin(還原:git checkout $tag -- <path>)" }
    Set-Content -LiteralPath (Join-Path $LogDir 'A.progress') '100 · 完' -Encoding UTF8; "rc 0" }
  $LaneB = { param($VIA, $PyVrn, $LogDir)
    Set-Content -LiteralPath (Join-Path $LogDir 'B.progress') '20 · ssot diff' -Encoding UTF8
    $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'
    foreach ($v in @(@('ssot', 'inventory'), @('ssot', 'diff'), @('panorama'))) {
      $o = @(& python $PyVrn @v 2>&1 | ForEach-Object { "" + $_ })
      $o | Where-Object { $_ -match '^\[計\]|^\s*\[(RED|YEL)\]' } | Select-Object -First 14 | ForEach-Object { "[" + ($v -join ' ') + "] " + $_.Trim() } }
    Set-Content -LiteralPath (Join-Path $LogDir 'B.progress') '100 · 完' -Encoding UTF8; "rc 0" }
  $Lanes = @(@{ id = 'A'; zh = '三系統健康還原點(零紅才鎖)+ git tag'; args = @($VIA, $PyHm, $Note, $GitSha, $Repo, $LogDir, [bool]$ForceRestore); run = $LaneA }, @{ id = 'B'; zh = 'VRN 自報齊全度(ssot inventory/diff · panorama)'; args = @($VIA, $PyVrn, $LogDir); run = $LaneB })
  Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir
  foreach ($lane in @('A', 'B')) { $lf = Join-Path $LogDir "$lane.log"; if (Test-Path -LiteralPath $lf) { Add-VIAPyLines $lane (Get-Content -LiteralPath $lf | ForEach-Object { $_ -replace '\x1b\[[0-9;]*m', '' }) 30 } }
  $Locked = ($script:Verdicts | Where-Object { $_ -match '\[A\] \[計\] 還原點 LOCKED' }).Count -gt 0
  if (-not $Locked) { $script:Errors.Add('[A] 還原點沒鎖(有紅或未跑)→ 高風險測試不開跑;修了再來,或 python <HealthMatrix> restorepoint --force --note 理由') }
  else {
    # ---------- C:VRN extract 掃測試夾(只 PDF;docx/txt/jpg 列出不掃)----------
    $Rul = Join-Path $LogDir 'FinLexicon_rulings_batch3.json'
    @'
{
 "origin": "2026-10-08 extract loop 第 1 輪 97 檔 未解 30 → 操作員+AI 裁定第三批(18 條;非列標 12 條進 triage 噪音規則)",
 "add": [
  {
   "std": "non_operating_income",
   "cat": "IS",
   "zh": [
    "總營業外收入",
    "營業外收入",
    "業外收入"
   ],
   "en": [
    "Non-operating income",
    "Total non-operating income"
   ]
  },
  {
   "std": "non_operating_expense",
   "cat": "IS",
   "zh": [
    "總營業外費用",
    "營業外費用",
    "業外支出"
   ],
   "en": [
    "Non-operating expenses"
   ]
  },
  {
   "std": "interest_expense",
   "cat": "IS",
   "zh": [
    "利息費用",
    "利息支出"
   ],
   "en": [
    "Interest expense"
   ]
  },
  {
   "std": "interest_income",
   "cat": "IS",
   "zh": [
    "利息收入"
   ],
   "en": [
    "Interest income"
   ]
  },
  {
   "std": "investment_income",
   "cat": "IS",
   "zh": [
    "投資收益",
    "採用權益法之投資收益"
   ],
   "en": [
    "Investment income"
   ]
  },
  {
   "std": "fx_gain",
   "cat": "IS",
   "zh": [
    "匯兌損益",
    "兌換利益"
   ],
   "en": [
    "Exchange gain",
    "FX gain/loss"
   ]
  },
  {
   "std": "extraordinary_items",
   "cat": "IS",
   "zh": [
    "非常項目"
   ],
   "en": [
    "Extraordinary items"
   ]
  },
  {
   "std": "net_income_before_extraordinary",
   "cat": "IS",
   "zh": [
    "非常項目前稅後純益"
   ],
   "en": [
    "Net income before extraordinary items"
   ]
  },
  {
   "std": "revenue",
   "cat": "IS",
   "zh": [
    "營業收益"
   ],
   "en": []
  },
  {
   "std": "revenue_growth",
   "cat": "RATIO",
   "zh": [
    "營業收益增長",
    "營收成長率",
    "營收年增"
   ],
   "en": [
    "Revenue growth",
    "Sales growth"
   ]
  },
  {
   "std": "rd_expense",
   "cat": "IS",
   "zh": [
    "研發費用",
    "研究發展費用"
   ],
   "en": [
    "R&D",
    "R&D expenses",
    "Research and development"
   ]
  },
  {
   "std": "amortization",
   "cat": "CF",
   "zh": [
    "攤提",
    "攤銷"
   ],
   "en": [
    "Amortization",
    "Amortisation"
   ]
  },
  {
   "std": "operating_cash_flow",
   "cat": "CF",
   "zh": [],
   "en": [
    "Cashflow from operations",
    "Cash flow from operations"
   ]
  },
  {
   "std": "other_assets",
   "cat": "BS",
   "zh": [
    "其他資產"
   ],
   "en": [
    "Other assets"
   ]
  },
  {
   "std": "other_current_liabilities",
   "cat": "BS",
   "zh": [
    "其他流動負債"
   ],
   "en": [
    "Other ST liabilities",
    "Other current liabilities"
   ]
  },
  {
   "std": "share_capital",
   "cat": "BS",
   "zh": [
    "股本",
    "普通股股本"
   ],
   "en": [
    "Common shares",
    "Share capital"
   ]
  },
  {
   "std": "roe",
   "cat": "RATIO",
   "zh": [
    "股東權益報酬率"
   ],
   "en": [
    "Return on Equity",
    "ROE"
   ]
  },
  {
   "std": "equity_value",
   "cat": "VAL",
   "zh": [
    "權益價值"
   ],
   "en": [
    "Equity Value"
   ]
  },
  {
   "std": "residual_income",
   "cat": "VAL",
   "zh": [
    "剩餘收益"
   ],
   "en": [
    "Residual Income"
   ]
  }
 ],
 "noise_rules": {
  "date": "^(\\d{1,2}月\\s*\\d{1,2},?\\s*\\d{4}|[一二三四五六七八九十]+月\\s*\\d{1,2},?\\s*\\d{4}|\\d{4}[/-]\\d{1,2}[/-]\\d{1,2})$",
  "column_head": "(?i)^(qoq|yoy|mom|ytd|%|\\(%\\)|qoq\\(%\\)|yoy\\(%\\)|chg|change|est\\.?|cons\\.?|actual|diff)$",
  "section": "(?i)^(balance sheet|income statement|cash ?flow(s| statement)?|ratios?|valuation|financial summary|key data)$",
  "rating": "^(增加持股|降低持股|買進|賣出|中立|持有|減碼|加碼|優於大盤|劣於大盤|區間操作)$",
  "ticker": "^\\d{4,6}(\\.(TW|TWO|SZ|SH|HK|T))?( TT)?$",
  "unit_tail": "(?i)^(nt\\$|us\\$|rmb|百萬|千|億)?\\s*(m|mn|bn|k)?$"
 }
}
'@ | Set-Content -LiteralPath $Rul -Encoding UTF8
    Add-VIAPyLines 'C_lex' (Invoke-VCPython -Id 'C_lex' -Argv @($PyVrn, 'lexicon', 'add', '--file', $Rul) -Sec $PyStepSec) 6
    if (Test-Path -LiteralPath $ReportDir) {
      $all = Get-ChildItem -LiteralPath $ReportDir -File; $pdf = @($all | Where-Object { $_.Extension -ieq '.pdf' }); $other = @($all | Where-Object { $_.Extension -ine '.pdf' })
      $script:Verdicts.Add("[C] 測試夾 $ReportDir · 檔 $($all.Count) · PDF $($pdf.Count) · 非 PDF $($other.Count)(" + (($other | Group-Object Extension | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ' ') + ")→ 非 PDF 本輪不掃,列待辦")
      $argv = @($PyVrn, 'extract', 'loop', '--dir', $ReportDir, '--rounds', "$Rounds"); if ($ExtractLimit -gt 0) { $argv += @('--limit', "$ExtractLimit") }
      Add-VIAPyLines 'C_loop' (Invoke-VCPython -Id 'C_loop' -Argv $argv -Sec ([Math]::Max($PyStepSec, 5400))) 70 }
    else { $script:Errors.Add("[C] 測試夾不在:$ReportDir") }
    # ---------- D:代號 → VDF quote(db → 引擎)----------
    $tks = @(); $led = Join-Path $VIA 'VIA_Reports\vrn\extract\VRN_Extract_Ledger.jsonl'
    if (Test-Path -LiteralPath $led) { Get-Content -LiteralPath $led | ForEach-Object { try { $j = $_ | ConvertFrom-Json; if ($j.ticker) { $tks += "$($j.ticker)" } elseif ($j.filename -and $j.filename.ticker) { $tks += "$($j.filename.ticker)" } } catch { } } }
    if (-not $tks.Count -and (Test-Path -LiteralPath $ReportDir)) { Get-ChildItem -LiteralPath $ReportDir -File | ForEach-Object { if ($_.Name -match '(?<![\d])(\d{4})(?![\d])') { $tks += $Matches[1] } } }
    $tks = @($tks | Where-Object { $_ -match '^(00\d{2}|[1-9]\d{3})$' } | Select-Object -Unique)   # 台股四碼 1000–9999 或 00xx(ETF);09xx 是檔名日期不是代號
    if ($tks.Count) { Add-VIAPyLines 'D_quote' (Invoke-VCPython -Id 'D_quote' -Argv @($PyVdf, 'quote', '--tickers', ($tks -join ','), '--asof', (Get-Date -Format 'yyyy-MM-dd')) -Sec ([Math]::Max($PyStepSec, 900))) 45 } else { $script:Verdicts.Add('[D] 沒抓到四碼代號 → quote 略') }
    # ---------- E:交接包隔離解壓(intake 名冊區,不覆蓋正式樹;試跑另開視窗,-RunHandover 才在這裡跑)----------
    if (Test-Path -LiteralPath $HandoverZip) {
      $Intake = Join-Path $VrnDir 'intake\VRN_v0108_Annual'
      if (-not (Test-Path -LiteralPath $Intake)) { New-Item -ItemType Directory -Force -Path $Intake | Out-Null; Expand-Archive -LiteralPath $HandoverZip -DestinationPath $Intake -Force; $script:Verdicts.Add("[E] 交接包解壓 → $Intake(隔離;正式 VRN 模組零覆蓋)") } else { $script:Verdicts.Add("[E] 交接包已在 $Intake(不重解)") }
      $root = Get-ChildItem -LiteralPath $Intake -Directory | Select-Object -First 1; $pk = if ($root -and -not (Test-Path (Join-Path $Intake 'RunAndVerify.ps1'))) { $root.FullName } else { $Intake }
      $n = @(Get-ChildItem -LiteralPath $pk -Recurse -File).Count; $script:Verdicts.Add("[E] 包根 $pk · 檔 $n · 入口 " + ((@('RunAndVerify.ps1', 'StartAnnual.ps1', 'README_FIRST.txt') | Where-Object { Test-Path (Join-Path $pk $_) }) -join ' / '))
      $rd = Join-Path $pk 'README_FIRST.txt'; if (Test-Path $rd) { Get-Content -LiteralPath $rd -TotalCount 12 | ForEach-Object { $script:Verdicts.Add('[E] README ' + $_.Trim()) } }
      $py312 = @(& py -0p 2>$null | Where-Object { $_ -match '3\.12' }); $script:Verdicts.Add("[E] Python 3.12 在本機:" + $(if ($py312.Count) { 'YES ' + ($py312[0] -replace '\s+', ' ') } else { 'NO(包要 3.12;py -0p 沒列出 → 先 winget install Python.Python.3.12)' }))
      if ($RunHandover -and (Test-Path (Join-Path $pk 'RunAndVerify.ps1'))) {
        $script:Verdicts.Add('[E] -RunHandover:在包根執行 RunAndVerify.ps1 -InstallDependencies(獨立境,逾時 40 分)')
        $ho = Join-Path $LogDir 'E.handover.log'
        $p = Start-Process -FilePath (Get-Command pwsh).Source -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', "Set-Location '$pk'; & .\RunAndVerify.ps1 -InstallDependencies *>&1 | Tee-Object -FilePath '$ho'") -PassThru -WindowStyle Minimized
        if (-not $p.WaitForExit(2400000)) { try { $p.Kill() } catch { }; $script:Errors.Add('[E] 交接包試跑逾時 40 分(已停)') }
        if (Test-Path $ho) { Get-Content -LiteralPath $ho | Where-Object { $_ -match '(?i)error|fail|pass|verified|一致|通過|rerun_output|traceback' } | Select-Object -Last 25 | ForEach-Object { if ($_ -match '(?i)error|fail|traceback') { $script:Errors.Add('[E] ' + $_.Trim()) } else { $script:Verdicts.Add('[E] ' + $_.Trim()) } } } }
      else { $script:Verdicts.Add("[E] 試跑另開視窗(Windows 實機未驗證,獨立境):Set-Location '$pk'; & .\RunAndVerify.ps1 -InstallDependencies   — 或本支加 -RunHandover 由我代跑") } }
    else { $script:Verdicts.Add("[E] 交接包不在 $HandoverZip → 略") }
    # ---------- F:三系統健康 + 入口頁 ----------
    Add-VIAPyLines 'F_vrn_health' (Invoke-VCPython -Id 'F_vrn_health' -Argv @($PyVrn, 'health') -Sec $PyStepSec) 6
    Add-VIAPyLines 'F_vdf_health' (Invoke-VCPython -Id 'F_vdf_health' -Argv @($PyVdf, 'health') -Sec $PyStepSec) 6
    Add-VIAPyLines 'F_portal' (Invoke-VCPython -Id 'F_portal' -Argv @($PyHm, 'portal') -Sec $PyStepSec) 4
    # ---------- G:完工判定(三條門檻都要) ----------
    $gVrn = ($script:Verdicts | Where-Object { $_ -match '\[C_loop\] \[計\] 完工門檻' } | Select-Object -Last 1); $vrnOK = ($gVrn -match 'GREEN')
    $gVdf = ($script:Verdicts | Where-Object { $_ -match '\[D_quote\] \[計\] VDF quote' } | Select-Object -Last 1); $vdfOK = ($gVdf -match '· GREEN')
    $rp = ($script:Verdicts | Where-Object { $_ -match '\[A\] \[計\] 還原點 LOCKED' }).Count -gt 0
    $script:Verdicts.Add("[G] 完工判定 · 還原點 $(if ($rp) { 'LOCKED' } else { '✗' }) · VRN 擷取門檻 $(if ($vrnOK) { 'GREEN' } else { '未過' }) · VDF 行情 $(if ($vdfOK) { 'GREEN' } else { '未過' }) · " + $(if ($rp -and $vrnOK -and $vdfOK) { '三條齊 → VRN / VDF 實測完工' } else { '未完工:看上面 [YEL] 列標 / [YEL] 代號,貼 AI 出下一版後重跑(只重掃 REVIEW,幾分鐘)' }))
    if ($rp -and $vrnOK -and $vdfOK) { Mark '完工' 'GREEN' }
    $Mx = Join-Path $VIA 'VIA_Reports\VIA_UI_latest.html'; if ((Test-Path -LiteralPath $Mx) -and -not $NoOpen) { Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue; try { Start-Process -FilePath $Mx } catch { } } }
  $script:Verdicts = [System.Collections.Generic.List[string]]::new([string[]]@($script:Verdicts | Select-Object -Unique))
  $script:Verdicts.Add("[結算] 還原點:VIA_Restore\rp_<stamp>.zip(本機,不進倉)+ registry\VIA_RestorePoint_Ledger_v0100.jsonl + git tag rp/<stamp>(已推);還原不自動覆蓋:git checkout rp/<stamp> -- <path> 或解壓比對 · VRN 掃描結果 VIA_Reports\vrn\extract\<sha8>\ + 帳 · VDF 行情 VIA_Reports\vdf\RESULT_quote_latest.json · 交接包在 VRN\intake\VRN_v0108_Annual(隔離,未接入正式 manager)")
}
Show-VCSummary -Title 'VRN / VDF 實測完工(還原點 → 擷取迴圈 → 行情 → 完工判定)' -LogDir $LogDir
