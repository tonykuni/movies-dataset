# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([int]$MaxMin = 60, [int]$KeepRuns = 5, [double]$MaxTempGB = 2.0, [double]$LowRamGB = 2.0, [int]$PyStepSec = 120, [string]$Title = 'VIA 任務', [switch]$NoCleanup, [switch]$KillOrphans, [switch]$NoOpen, [switch]$Demo)
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

# ======================= 骨架主體(只改這裡的 $Lanes) =======================
if (-not $NoCleanup) { Invoke-VCSafeCleanup }
$Run = Initialize-VCTemp; Initialize-VCAccel
$script:LogDir = Join-Path $VIA ("VIA_Reports\review\ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null; $LogDir = $script:LogDir
$Reg = if ($global:VIARegisterPath) { $global:VIARegisterPath } else { (Get-ChildItem $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName }
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
  # 這裡放你的車道;每道可寫 <LogDir>\<id>.progress = "0..100 · 文字" 讓進度條動;python 走 Invoke-VCPython(主執行緒)或車道內同樣的 base64 包法
  $Lanes = @()
  if ($Lanes.Count) { Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir } else { $script:Verdicts.Add("[骨架] 沒定義車道:複製本檔改 `$Lanes,或加 -Demo 看示範") }
}
Show-VCSummary -Title $Title -LogDir $LogDir
