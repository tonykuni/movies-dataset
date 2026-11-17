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
# Invoke-VIA-VCGC-ExternalTools-v0100.ps1 — 2026-11-17。以上是 VeritasCeleritas.PS7.Skeleton-v0112 原文一字不動;只有這一段是本支的。
#   操作員 2026-11-17:「外部工具導入啟用並與內部工具完整搭配」;選 Graphify(只用本機 AST)· Prettier · Ponytail · OmniRoute;
#   「先把本機環境與工具安裝設置沒衝突問題後再進行」。
#   C0(主執行緒,先跑):預檢 — 真 Python · Node 版本 · npm · git · Claude Code CLI · PATH 上既有 graphify / prettier · 既有 Ponytail / OmniRoute ·
#      連接埠 20128 · 磁碟 · 記憶體 · 工具夾不在 OneDrive · 倉內 VIA_Graphify v0101 開機行 sha。每支工具一盞燈:紅 = 那支這次不裝。
#   道 A:VIA_ExternalToolsGate all — 只裝沒紅的;全部裝在 %LOCALAPPDATA%\VIA\tools(不改 PATH · 不 -g · 不碰 OneDrive);
#      Graphify 走倉內既有 VIA_Graphify v0101(釘 0.9.100 · 隔離 venv · --code-only · GRAPHIFY_BACKEND=none);
#      Prettier 本地釘 3.3.3、只檢不寫;Ponytail 用 claude plugin(CLI 不行就給你兩行 /plugin);OmniRoute 釘 v2.9.5 只建不啟動、不寫模型金鑰。
#   道 B(唯讀,並行):VCGC token 卡 · VCGC MCP 自測(有 v0104 用 v0104,否則 v0103)。
#   收據:VIA_Reports\vcgc\tools\VIA_ExternalTools_latest.{json,md,html} · VIA_ExternalTools_Preflight_latest.json · VIA_PrettierCheck_latest.json
#      (VCGC MCP v0104 的 tools/* 資源直接讀)。開關:VIA_EXT_TOOLS=graphify,prettier,ponytail,omniroute(預設四支)· VIA_EXT_DRY=1 只預檢不裝。
#   不做:不代設同意閘 · 不裝 Node / Python(缺了報紅給一行指令)· 不改任何系統的檔 · 不推 git · 不碰 TA-Lib · 不啟動 OmniRoute。
if (-not (Test-Path -LiteralPath ("$VIA" + '\supportive modules\registry'))) {
  $cands = @(@($env:VIA_ROOT, (Join-Path $env:USERPROFILE 'OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'), (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics')) | Where-Object { $_ -and (Test-Path -LiteralPath ("$_" + '\supportive modules\registry')) })
  if ($cands.Count) { $VIA = $cands[0]; Set-Location -LiteralPath $VIA }
  else { Write-Host "`e[91m[根] 找不到 VIA 主 checkout(要有 supportive modules\registry)。什麼都沒跑、沒寫。`e[0m"; Write-Host "`e[93mNEXT: 把 `$env:VIA_ROOT 設成主 checkout 的 VeritasIntelligenceAnalytics 夾後重跑`e[0m"; return } }
if (-not $PSBoundParameters.ContainsKey('Title')) { $Title = 'VCGC 外部工具啟用 · 先查衝突 → 才裝 → 自測 → 搭配' }
if (-not $PSBoundParameters.ContainsKey('MaxMin')) { $MaxMin = 240 }   # Graphify 四系統畫圖 + OmniRoute npm ci / build 可能各要幾十分
if (-not $NoCleanup) { Invoke-VCSafeCleanup }
$Run = Initialize-VCTemp; Initialize-VCAccel
$script:LogDir = Join-Path $VIA ("VIA_Reports\review\ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null; $LogDir = $script:LogDir
$StartAt = Get-Date
$Want = if ("$env:VIA_EXT_TOOLS") { "$env:VIA_EXT_TOOLS" } else { 'graphify,prettier,ponytail,omniroute' }
$Dry = ($env:VIA_EXT_DRY -eq '1')
$script:Verdicts.Add("[計畫] 要裝:$Want" + $(if ($Dry) { ' · VIA_EXT_DRY=1 → 只預檢、不裝' } else { ' · 預檢紅的那支自動跳過' }) + " · 工具夾 " + (Join-Path $env:LOCALAPPDATA 'VIA\tools'))

# ---------- 落地輔助檔(本輪 log 夾,不進任何系統的夾) ----------
$GatePy = Join-Path $LogDir 'VIA_ExternalToolsGate_v0100.py'
@'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ExternalToolsGate v0100 — 外部工具「先查衝突 → 沒衝突才裝 → 自測 → 與 VCGC 內部工具接上」

操作員 2026-11-17:「外部工具導入啟用並與內部工具完整搭配」;選 Graphify(只用本機 AST)· Prettier · Ponytail · OmniRoute;
「先把本機環境與工具安裝設置沒衝突問題後再進行」。
動詞:
  preflight  只讀:Python 是真的(不是 WindowsApps 假捷徑)· Node 版本(Ponytail 鉤子要 node;OmniRoute v2.9.5 要 18–23)· git ·
             Claude Code CLI · 既有安裝(PATH 上的 graphify / prettier · ~/.claude 外掛 · 工具夾)· 連接埠 20128 · 磁碟 · 記憶體 ·
             工具夾不在 OneDrive · VIA_Graphify v0101 開機行 sha。每支工具一盞燈;紅 = 這支不裝。
  install    只裝預檢沒紅的那幾支,全部裝在 %LOCALAPPDATA%\\VIA\\tools(不碰 OneDrive · 不改 PATH · 不動全域 npm / pip):
             graphify  → 跑倉內既有 VIA_Graphify v0101(graphifyy 0.9.100 · 隔離 venv · --code-only · GRAPHIFY_BACKEND=none · 一系統一張圖)
             prettier  → npm install --prefix <工具夾>\\prettier prettier@3.3.3(本地,不 -g)
             ponytail  → claude plugin marketplace add DietrichGebert/ponytail · claude plugin install ponytail@ponytail
             omniroute → git clone --depth 1 OmniRoute(標籤 v2.9.5,沒有就預設分支)→ npm ci → npm run build;只建不啟動,只綁本機 20128;
                         .env 由 .env.example 複製,只填本機必填的隨機密鑰與資料夾,不寫任何模型金鑰(G-03:只送程式碼與 schema)
  verify     每支版本 + 煙霧測試;Prettier 只檢不寫(--check;鎖定 U/I 檔排除)→ PrettierCheck 收據
  report     收據 JSON / MD / HTML(四燈 · 第一欄燈)寫到 VIA_Reports/vcgc/tools/,VCGC MCP v0104 的 tools/* 資源直接讀
不做:不代設同意閘 · 不裝 Node / Python(缺了只報紅,給一行指令)· 不改任何系統的檔 · 不推 git · 不碰 TA-Lib · 不啟動 OmniRoute。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

TOOL = "VIA_ExternalToolsGate v0100"
PAL = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
TOOLS = ("graphify", "prettier", "ponytail", "omniroute")
PRETTIER_VER = "3.3.3"
OMNI_TAG = "v2.9.5"   # package.json engines node >=18 <24 · .env.example PORT=20128
GRAPHIFY_MD = "docs/handoff/ai/via_graphify_v0101/VIA_Graphify_v0101.md"
GRAPHIFY_SHA = "49002982269b4567f4de9855fe77b0dcefad91de485ac61a1458669403089a10"
PAIRING = [
    {"tool": "graphify", "internal": "CGC_MDL158 read · slice · pack · chain(省 Token 全景)",
     "how": "Graphify 管「誰呼叫誰、跨檔走向」的導航;要引用證據仍用 MDL158 骨架卡。圖收據 graphify/latest 經 VCGC MCP 讀。",
     "boundary": "只解析程式碼(--code-only · GRAPHIFY_BACKEND=none · 離線);文件與圖片不送任何模型;圖不是正式證據"},
    {"tool": "prettier", "internal": "VIA_UI_FormatLock · VIA_UI_Template_SSOT(鎖定色票字體)",
     "how": "只檢不寫(--check):列出 Markdown / HTML / JS 排版不一致的檔;鎖定 U/I 檔與報告夾排除。收據 tools/prettier-check。",
     "boundary": "不改任何鎖定值;不碰 .py / .ps1;不自動 --write"},
    {"tool": "ponytail", "internal": "薄尾新版規則 · 貼回包(verb-interaction)· CLAUDE.md",
     "how": "讓 Claude Code 少寫碼、先找既有件;與「不重寫、出薄尾新版」同向。CLAUDE.md 的規則仍優先。",
     "boundary": "只在操作員本機 Claude Code;倉內零改動;移除:node scripts/uninstall.js → /plugin remove ponytail"},
    {"tool": "omniroute", "internal": "VIA_MCP_Engine v0103(各 AI 平台設定)· VCGC MCP 唯讀門面",
     "how": "本機 AI 閘道,依任務換模型;VIA 引擎的執行路徑一律不經過它。",
     "boundary": "G-03:只送程式碼結構與 schema;市場資料 / 研報 / 庫內容不送;只綁本機;金鑰由操作員自己填;不自動啟動"},
]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def say(*a):
    print(*a, flush=True)


def run(cmd, cwd=None, sec=120, env=None):
    exe = shutil.which(cmd[0]) or cmd[0]
    try:
        r = subprocess.run([exe, *cmd[1:]], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=sec, env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except FileNotFoundError:
        return 127, "not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as exc:
        return 126, str(exc)


def first_ver(txt):
    m = re.search(r"(\d+\.\d+\.\d+)", txt or "")
    return m.group(1) if m else ""


def tools_home():
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "VIA" / "tools"


def graphify_line(via: Path):
    f = via / GRAPHIFY_MD
    if not f.exists():
        return None, "倉內沒有 " + GRAPHIFY_MD
    md = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.search(r"(?s)<!-- graphify line -->\n```powershell\n(.*?)\n```", md)
    if not m:
        return None, "找不到 graphify line 區塊"
    code = m.group(1)
    sha = hashlib.sha256(code.encode("utf-8")).hexdigest()
    return (code, "sha OK") if sha == GRAPHIFY_SHA else (None, "sha %s ≠ %s" % (sha[:12], GRAPHIFY_SHA[:12]))


# ───────────────────────── preflight ─────────────────────────
def preflight(via: Path, want):
    rows, block = [], {t: [] for t in TOOLS}

    def add(item, lamp, note, blocks=()):
        rows.append({"item": item, "lamp": lamp, "note": note, "blocks": list(blocks)})
        if lamp == "RED":
            for t in blocks:
                block[t].append(item)
    home = tools_home()
    add("作業系統", "GREEN" if os.name == "nt" else "YELLOW", sys.platform + ("" if os.name == "nt" else " · 不是 Windows(沙盒預演)"))
    exe = sys.executable
    add("Python 是真的", "RED" if "WindowsApps" in exe else "GREEN", exe + " · " + sys.version.split()[0], ("graphify",) if "WindowsApps" in exe else ())
    rc, out = run(["node", "--version"])
    nv = first_ver(out) if rc == 0 else ""
    if not nv:
        add("Node", "RED", "沒有 node → Prettier / Ponytail(鉤子要 node)/ OmniRoute 不裝 · 修:winget install OpenJS.NodeJS.LTS(操作員自己裝,裝完重跑)",
            ("prettier", "ponytail", "omniroute"))
    else:
        major = int(nv.split(".")[0])
        okomni = 18 <= major < 24
        add("Node", "GREEN" if okomni else "YELLOW", "node " + nv + ("" if okomni else " · OmniRoute v2.9.5 要 Node 18–23 → OmniRoute 不裝"))
        if not okomni:
            block["omniroute"].append("Node 版本")
            rows[-1]["blocks"] = ["omniroute"]
    rc, out = run(["npm", "--version"])
    add("npm", "GREEN" if rc == 0 else ("RED" if nv else "GRAY"), ("npm " + first_ver(out)) if rc == 0 else "沒有 npm", () if rc == 0 else ("prettier", "omniroute"))
    rc, out = run(["git", "--version"])
    add("git", "GREEN" if rc == 0 else "RED", first_ver(out) or "沒有 git", () if rc == 0 else ("omniroute",))
    rc, out = run(["claude", "--version"])
    add("Claude Code CLI", "GREEN" if rc == 0 else "RED", ("claude " + first_ver(out)) if rc == 0 else
        "沒有 claude 指令 → Ponytail 改由你在 Claude Code(或桌面版 Code 分頁)送兩行:/plugin marketplace add DietrichGebert/ponytail · /plugin install ponytail@ponytail",
        () if rc == 0 else ("ponytail",))
    g = shutil.which("graphify")
    if g:
        rc, out = run(["graphify", "--version"])
        add("PATH 上已有 graphify", "YELLOW", "%s · %s → 和 VIA 隔離版(0.9.100)並存;正式證據只認 VIA 隔離版" % (g, first_ver(out) or "版本不明"))
    else:
        add("PATH 上已有 graphify", "GREEN", "沒有 → 不會撞")
    p = shutil.which("prettier")
    add("PATH 上已有 prettier", "YELLOW" if p else "GREEN", (p + " → 本支用工具夾裡釘版 " + PRETTIER_VER + ",不動全域那份") if p else "沒有 → 不會撞")
    plug = Path.home() / ".claude" / "plugins"
    hit = [str(x) for x in plug.rglob("*ponytail*")][:1] if plug.is_dir() else []
    add("Ponytail 已裝", "GREEN", ("已在 " + hit[0] + " → 只驗不重裝") if hit else "還沒裝")
    omni = home / "OmniRoute"
    add("OmniRoute 工具夾", "GREEN", ("已有 " + str(omni) + " → 只驗不重裝") if (omni / "package.json").exists() else "還沒有")
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 20128)); busy = False
    except OSError:
        busy = True
    finally:
        s.close()
    add("連接埠 20128(OmniRoute 預設)", "YELLOW" if busy else "GREEN", "被占用 → 本支只建不啟動;要啟動時改 .env 的 PORT" if busy else "空的")
    try:
        free = shutil.disk_usage(str(home.anchor if home.anchor else home)).free // 2**30
    except OSError:
        free = -1
    add("磁碟(工具夾那顆)", "GREEN" if free >= 5 else "RED", "%s GB 可用(要 ≥ 5)" % free, () if free >= 5 else TOOLS)
    avail = None
    try:
        import psutil  # noqa: PLC0415
        avail = psutil.virtual_memory().available // 2**20
    except Exception:
        pass
    add("可用記憶體", "GRAY" if avail is None else ("GREEN" if avail >= 6144 else "YELLOW"),
        "量不到" if avail is None else "%d MB(Graphify 畫 VCGC 峰值約 5.5 GB;不足時它會報紅,不會整台卡死)" % avail)
    add("工具夾不在 OneDrive", "RED" if "onedrive" in str(home).lower() else "GREEN", str(home), TOOLS if "onedrive" in str(home).lower() else ())
    code, why = graphify_line(via)
    add("VIA_Graphify v0101 開機行", "GREEN" if code else "RED", why, () if code else ("graphify",))
    for t in TOOLS:
        if t not in want:
            block[t].append("這次沒選")
    plan = {t: ("裝" if not block[t] else "不裝:" + "、".join(block[t])) for t in TOOLS}
    lamp = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")
    return {"tool": TOOL, "at": now(), "lamp": lamp, "home": str(home), "rows": rows, "plan": plan}


# ───────────────────────── install / verify ─────────────────────────
def install_one(t, via: Path, home: Path, logs: Path):
    home.mkdir(parents=True, exist_ok=True)
    log = []
    if t == "graphify":
        code, why = graphify_line(via)
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not (code and ps):
            return "RED", "沒跑:" + (why if not code else "沒有 pwsh"), ""
        env = dict(os.environ, GRAPHIFY_BACKEND="none", VRN2_ROOT=str(via))
        rc, out = run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code], cwd=str(via), sec=5400, env=env)
        log.append(out)
        lamp = "GREEN" if rc == 0 and "[RED]" not in out else ("YELLOW" if rc == 0 else "RED")
        note = "VIA_Graphify v0101 rc %s · %s" % (rc, (re.findall(r"\[(?:GREEN|YELLOW|RED)\][^\n]*", out) or ["(無判決行)"])[-1][:160])
    elif t == "prettier":
        d = home / "prettier"; d.mkdir(exist_ok=True)
        rc, out = run(["npm", "install", "--prefix", str(d), "prettier@" + PRETTIER_VER, "--no-audit", "--no-fund", "--loglevel=error"], sec=900)
        log.append(out)
        ign = d / ".prettierignore"
        if not ign.exists():
            ign.write_text("\n".join(["**/node_modules/**", "**/VIA_Reports/**", "**/*UI*.html", "**/VIA_UI_*", "**/*_UI_latest.html",
                                      "**/*.min.*", "**/intake/**", "**/references/**", "**/*.py", "**/*.ps1"]) + "\n", encoding="utf-8")
        lamp, note = ("GREEN", "prettier@%s 裝在 %s(本地,不 -g)" % (PRETTIER_VER, d)) if rc == 0 else ("RED", "npm rc %s · %s" % (rc, out.strip()[-160:]))
    elif t == "ponytail":
        rc1, o1 = run(["claude", "plugin", "marketplace", "add", "DietrichGebert/ponytail"], sec=300)
        rc2, o2 = run(["claude", "plugin", "install", "ponytail@ponytail"], sec=300)
        log += [o1, o2]
        if rc1 == 0 and rc2 == 0:
            lamp, note = "GREEN", "claude plugin install ponytail@ponytail · rc 0"
        else:
            lamp, note = "YELLOW", ("CLI 裝不了(rc %s/%s:%s)→ 請在 Claude Code 分兩次送:/plugin marketplace add DietrichGebert/ponytail · /plugin install ponytail@ponytail"
                                    % (rc1, rc2, (o2 or o1).strip()[-100:]))
    elif t == "omniroute":
        d = home / "OmniRoute"
        if not (d / "package.json").exists():
            rc, out = run(["git", "clone", "--depth", "1", "--branch", OMNI_TAG, "https://github.com/diegosouzapw/OmniRoute.git", str(d)], sec=900)
            if rc != 0:
                rc, out = run(["git", "clone", "--depth", "1", "https://github.com/diegosouzapw/OmniRoute.git", str(d)], sec=900)
            log.append(out)
            if rc != 0:
                return "RED", "git clone rc %s · %s" % (rc, out.strip()[-160:]), "\n".join(log)
        data = home / "omniroute-data"; data.mkdir(exist_ok=True)
        envf = d / ".env"
        if not envf.exists():
            import secrets  # noqa: PLC0415
            base = (d / ".env.example").read_text(encoding="utf-8") if (d / ".env.example").exists() else ""
            setv = {"JWT_SECRET": secrets.token_hex(32), "API_KEY_SECRET": secrets.token_hex(32), "INITIAL_PASSWORD": secrets.token_urlsafe(15),
                    "DATA_DIR": str(data), "PORT": "20128", "ENABLE_REQUEST_LOGS": "false", "NODE_ENV": "production"}
            lines, seen = [], set()
            for ln in base.splitlines():
                k = ln.split("=", 1)[0].strip()
                if k in setv and not ln.lstrip().startswith("#"):
                    lines.append("%s=%s" % (k, setv[k])); seen.add(k)
                else:
                    lines.append(ln)
            lines += ["%s=%s" % (k, v) for k, v in setv.items() if k not in seen]
            envf.write_text("# VIA:本機必填的隨機密鑰與資料夾由 VIA_ExternalToolsGate 產生;模型金鑰由操作員自己填(G-03:只送程式碼結構與 schema)\n"
                            + "\n".join(lines) + "\n", encoding="utf-8")
        rc, out = run(["npm", "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=str(d), sec=2400)
        log.append(out)
        if rc == 0:
            rc, out = run(["npm", "run", "build"], cwd=str(d), sec=2400)
            log.append(out)
        lamp, note = ("GREEN", "建好(沒啟動)· %s · 資料 %s · 啟動:cd 該夾 → npm run start(http://localhost:20128;初始密碼在該夾 .env 的 INITIAL_PASSWORD)" % (d, data)) if rc == 0 else \
            ("RED", "npm rc %s · %s" % (rc, out.strip()[-160:]))
    else:
        return "GRAY", "未知工具", ""
    (logs / ("install_%s.log" % t)).write_text("\n".join(log), encoding="utf-8")
    return lamp, note, "\n".join(log)


def verify_one(t, via: Path, home: Path, out_dir: Path):
    if t == "graphify":
        rec = via / "VIA_Reports" / "graphify" / "VIA_Graphify_latest.json"
        if rec.exists():
            try:
                j = json.loads(rec.read_text(encoding="utf-8"))
                return j.get("lamp", "YELLOW"), "圖收據 %s · lamp %s" % (rec.name, j.get("lamp")), j.get("graphifyy") or j.get("version") or ""
            except ValueError:
                return "YELLOW", "圖收據讀不了", ""
        return "YELLOW", "還沒有圖收據 VIA_Reports/graphify/VIA_Graphify_latest.json", ""
    if t == "prettier":
        b = home / "prettier" / "node_modules" / ".bin" / ("prettier.cmd" if os.name == "nt" else "prettier")
        if not b.exists():
            return "GRAY", "沒裝", ""
        rc, out = run([str(b), "--version"])
        ver = first_ver(out)
        targets = [str(p) for p in sorted((via / "docs" / "handoff" / "ai").glob("*.md"))[:200]]
        bad, rc2 = [], 0
        if targets:
            rc2, out2 = run([str(b), "--check", "--ignore-path", str(home / "prettier" / ".prettierignore"), *targets], sec=600)
            bad = [ln.replace("[warn]", "").strip() for ln in out2.splitlines() if ln.startswith("[warn]") and "Code style issues" not in ln]
        doc = {"tool": TOOL, "at": now(), "prettier": ver, "mode": "check-only", "scanned": len(targets), "needs_format": len(bad), "files": bad[:400],
               "lamp": "GREEN" if not bad else "YELLOW", "note": "只檢不寫;鎖定 U/I 檔、報告夾、.py / .ps1 排除"}
        (out_dir / "VIA_PrettierCheck_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        return ("GREEN" if rc == 0 else "RED"), "prettier %s · 檢 %d 份 Markdown · 排版不一致 %d 份(只列不改)" % (ver, len(targets), len(bad)), ver
    if t == "ponytail":
        rc, out = run(["claude", "plugin", "list"], sec=60)
        plug = Path.home() / ".claude" / "plugins"
        hit = ("ponytail" in out.lower()) or (plug.is_dir() and any(plug.rglob("*ponytail*")))
        return ("GREEN" if hit else "YELLOW"), ("外掛清單有 ponytail" if hit else "外掛清單看不到 ponytail(若是在 Claude Code 手動裝,重開後再跑一次)"), ""
    if t == "omniroute":
        d = home / "OmniRoute"
        if not (d / "package.json").exists():
            return "GRAY", "沒裝", ""
        try:
            ver = json.loads((d / "package.json").read_text(encoding="utf-8")).get("version", "")
        except ValueError:
            ver = ""
        built = any((d / x).exists() for x in (".next", "dist", "build"))
        envf = (d / ".env").read_text(encoding="utf-8") if (d / ".env").exists() else ""
        keys = re.findall(r"^((?:OPENAI|ANTHROPIC|CLAUDE|GEMINI|GOOGLE|DEEPSEEK|GROQ|OPENROUTER|MISTRAL|XAI|QWEN|KIMI|MOONSHOT)[A-Z0-9_]*KEY[A-Z0-9_]*)=\S", envf, re.M)
        return ("GREEN" if built else "YELLOW"), "omniroute %s · %s · .env 模型金鑰 %s" % (ver, "已建" if built else "沒看到建置輸出", ("有 " + ",".join(keys) + "(操作員自填)") if keys else "無"), ver
    return "GRAY", "未知", ""


# ───────────────────────── report ─────────────────────────
def lampc(l):
    return '<span class="lp %s" title="%s"></span>' % (l, l)


def render(doc):
    e = html.escape
    css = """:root{--bg:#f8fafc;--card:#fff;--line:#e2e8f0;--tx:#0f172a;--mu:#64748b;--g:%(GREEN)s;--y:%(YELLOW)s;--r:%(RED)s;--n:%(GRAY)s}
*{box-sizing:border-box}body{margin:0;padding:12px;background:var(--bg);color:var(--tx);font:11px/1.4 -apple-system,'Segoe UI','Microsoft JhengHei',Roboto,Arial,sans-serif}
h1{font-size:14px;margin:0 0 6px}h2{font-size:12px;margin:14px 0 6px}.mu{color:var(--mu)}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px;margin-bottom:10px;overflow-x:auto}
table{width:100%%;border-collapse:collapse;table-layout:fixed}th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#f1f5f9}col.l{width:34px}td.c{text-align:center}
.lp{display:inline-block;width:12px;height:12px;border-radius:50%%}.GREEN{background:var(--g)}.YELLOW{background:var(--y)}.GRAY{background:var(--n)}
.RED{background:var(--r);animation:bl 1.8s ease-in-out infinite}@keyframes bl{50%%{opacity:.25}}""" % PAL
    h = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VCGC 外部工具啟用</title><style>%s</style></head><body>" % css,
         "<h1>VCGC 外部工具啟用 · 先查衝突 → 才裝 → 自測 → 搭配</h1><div class='mu'>%s · %s · 工具夾 %s</div>" % (e(doc["at"]), e(TOOL), e(doc["home"]))]
    h.append("<h2>① 每支工具</h2><div class='card'><table><colgroup><col class='l'><col style='width:90px'><col><col><col></colgroup><tr><th>燈</th><th>工具</th><th>預檢</th><th>安裝</th><th>自測</th></tr>")
    for t in doc["tools"]:
        h.append("<tr><td class='c'>%s</td><td><b>%s</b> %s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (lampc(t["lamp"]), e(t["tool"]), e(t.get("version", "")), e(t["plan"]), e(t["install"]), e(t["verify"])))
    h.append("</table></div><h2>② 預檢(環境與既有安裝衝突)</h2><div class='card'><table><colgroup><col class='l'><col style='width:180px'><col></colgroup><tr><th>燈</th><th>項目</th><th>結果</th></tr>")
    for r in doc["preflight"]["rows"]:
        h.append("<tr><td class='c'>%s</td><td>%s</td><td>%s</td></tr>" % (lampc(r["lamp"]), e(r["item"]), e(r["note"])))
    h.append("</table></div><h2>③ 和 VCGC 內部工具怎麼搭</h2><div class='card'><table><colgroup><col style='width:90px'><col><col><col></colgroup><tr><th>外部</th><th>內部對口</th><th>怎麼用</th><th>邊界</th></tr>")
    for p in PAIRING:
        h.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (e(p["tool"]), e(p["internal"]), e(p["how"]), e(p["boundary"])))
    h.append("</table></div><div class='mu'>燈:綠 = 通過 · 黃 = 有但不完整 / 需你手動一步 · 紅 = 衝突或失敗(慢閃)· 灰 = 沒選 / 沒裝。本頁靜態、不連網。</div></body></html>")
    return "".join(h)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="VIA_ExternalToolsGate")
    ap.add_argument("verb", choices=["preflight", "all"])
    ap.add_argument("--via", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--tools", default=",".join(TOOLS)); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    via = Path(a.via).resolve(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rec = via / "VIA_Reports" / "vcgc" / "tools"; rec.mkdir(parents=True, exist_ok=True)
    want = [t for t in a.tools.split(",") if t in TOOLS]
    pf = preflight(via, want)
    (rec / "VIA_ExternalTools_Preflight_latest.json").write_text(json.dumps(pf, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in pf["rows"]:
        say("[%s] [預檢] %s · %s" % ({"GREEN": "OK", "YELLOW": "YEL", "RED": "RED", "GRAY": "注"}[r["lamp"]], r["item"], r["note"]))
    for t in TOOLS:
        say("[計] [計畫] %s → %s" % (t, pf["plan"][t]))
    if a.verb == "preflight":
        return 1 if pf["lamp"] == "RED" else (2 if pf["lamp"] == "YELLOW" else 0)
    home = Path(pf["home"]); rows = []
    for t in TOOLS:
        if pf["plan"][t] != "裝":
            rows.append({"tool": t, "plan": pf["plan"][t], "install": "—", "verify": "—", "lamp": "GRAY" if "這次沒選" in pf["plan"][t] else "RED", "version": ""})
            continue
        t0 = time.time()
        if a.dry:
            il, inote = "GRAY", "乾跑:不裝"
        else:
            say("[計] [安裝] ▶ %s" % t)
            il, inote, _ = install_one(t, via, home, out)
        vl, vnote, ver = verify_one(t, via, home, rec)
        lamp = "RED" if "RED" in (il, vl) else ("YELLOW" if "YELLOW" in (il, vl) else ("GRAY" if il == "GRAY" else "GREEN"))
        rows.append({"tool": t, "plan": "裝", "install": inote, "verify": vnote, "lamp": lamp, "version": ver, "secs": round(time.time() - t0)})
        say("[%s] [%s] 安裝 %s · 自測 %s · %ds" % ({"GREEN": "OK", "YELLOW": "YEL", "RED": "RED", "GRAY": "注"}[lamp], t, inote, vnote, time.time() - t0))
    doc = {"tool": TOOL, "at": now(), "home": str(home), "preflight": pf, "tools": rows, "pairing": PAIRING,
           "lamp": "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] in ("YELLOW",) for r in rows) else "GREEN")}
    (rec / "VIA_ExternalTools_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# VCGC 外部工具啟用 · %s" % doc["at"], "", "| 燈 | 工具 | 安裝 | 自測 |", "|---|---|---|---|"] + \
         ["| %s | %s %s | %s | %s |" % (r["lamp"], r["tool"], r.get("version", ""), r["install"].replace("|", "/"), r["verify"].replace("|", "/")) for r in rows] + \
         ["", "## 搭配", ""] + ["- **%s** ↔ %s:%s(邊界:%s)" % (p["tool"], p["internal"], p["how"], p["boundary"]) for p in PAIRING]
    (rec / "VIA_ExternalTools_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    hp = out / "VIA_ExternalTools_latest.html"; hp.write_text(render(doc), encoding="utf-8")
    (rec / "VIA_ExternalTools_latest.html").write_text(render(doc), encoding="utf-8")
    say("[計] [收據] %s · 頁 %s" % (rec / "VIA_ExternalTools_latest.json", hp))
    return 1 if doc["lamp"] == "RED" else (2 if doc["lamp"] == "YELLOW" else 0)


if __name__ == "__main__":
    sys.exit(main())
'@ | Set-Content -LiteralPath $GatePy -Encoding UTF8

# ---------- C0 預檢(主執行緒,先於兩道;只讀)----------
$e0 = $script:Errors.Count; $pf = @(Invoke-VCPython -Id 'C0_preflight' -Argv @($GatePy, 'preflight', '--via', $VIA, '--out', $LogDir, '--tools', $Want) -Sec 600)
for ($j = $script:Errors.Count - 1; $j -ge $e0; $j--) { if ($script:Errors[$j] -like '[[]C0_preflight] rc *') { $script:Errors.RemoveAt($j) } }
foreach ($ln in $pf) { $t = "$ln".Trim(); if (-not $t) { continue }
  if ($t -match '^\[RED\]') { $script:Errors.Add($t) } elseif ($t -match '^\[(YEL|計|注)\]') { $script:Verdicts.Add($t) } }
$Plan = @($pf | Where-Object { "$_" -match '^\[計\] \[計畫\] (\w+) → 裝$' } | ForEach-Object { if ("$_" -match '\[計畫\] (\w+) →') { $Matches[1] } })
$script:Verdicts.Add("[預檢] 沒衝突、可以裝的:" + $(if ($Plan.Count) { $Plan -join ' · ' } else { '(沒有)' }))

# ---------- 道 A / 道 B ----------
$LaneRun = { param($Root, $LogDir, $Id, $Plan)
  Set-Location -LiteralPath $Root; $prog = Join-Path $LogDir ($Id + '.progress'); $i = 0
  foreach ($s in $Plan) { $i++
    $sa = @($s.a); $what = "" + $s.label
    Set-Content -LiteralPath $prog ("" + [int](($i - 1) * 100 / $Plan.Count) + " · " + $what) -Encoding UTF8
    if (-not (Test-Path -LiteralPath $s.file)) { "[GRAY] $what · 檔不在 → 未跑"; continue }
    $json = ConvertTo-Json -InputObject @(@($s.file) + $sa) -Compress; $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
    $wrap = "import base64,json,os,sys,threading,runpy; a=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); t=threading.Timer($([int]$s.sec), lambda: (sys.stdout.flush(), os._exit(124))); t.daemon=True; t.start(); sys.argv=a; runpy.run_path(a[0], run_name='__main__')"
    $global:LASTEXITCODE = $null; $t0 = Get-Date
    $o = @(& python -c $wrap $b64 2>&1 | ForEach-Object { "" + $_ }); $rc = $global:LASTEXITCODE
    $dt = [int]((Get-Date) - $t0).TotalSeconds; $o | Set-Content -LiteralPath (Join-Path $LogDir ($s.n + '.out')) -Encoding UTF8
    $lamp = if ($null -eq $rc) { 'NOTE' } elseif ($rc -eq 0) { 'GREEN' } elseif ($rc -in 2, 3, 4) { 'YELLOW' } else { 'RED' }
    $why = if ($null -ne $rc) { @{ 1 = '有紅項(見收據頁)'; 2 = '黃 / 要你手動一步'; 3 = '缺件'; 4 = '等同意閘'; 124 = '逾時' }[[int]$rc] } else { $null }
    $tag = @{ GREEN = '[OK]'; YELLOW = '[YEL]'; RED = '[RED]'; NOTE = '[注]' }[$lamp]
    ($tag + ' ' + $what + ' · rc ' + $(if ($null -eq $rc) { '未回' } else { "$rc" }) + $(if ($why) { "($why)" } else { '' }) + ' · ' + $dt + 's · ' + $o.Count + ' 行') }
  Set-Content -LiteralPath $prog '100 · 完' -Encoding UTF8 }

$Reg = Join-Path $VIA 'supportive modules\registry'
$Con = Get-ChildItem -LiteralPath $Reg -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py' -File -ErrorAction SilentlyContinue | Select-Object -First 1
$Mcp = Get-ChildItem -LiteralPath $Reg -Filter 'CGC_MDL279_MCPServer_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$aArgs = @('all', '--via', $VIA, '--out', $LogDir, '--tools', $(if ($Plan.Count) { $Plan -join ',' } else { 'none' })); if ($Dry) { $aArgs += '--dry' }
$PlanA = @(@{ n = 'A_ext'; file = $GatePy; sec = 13800; label = '外部工具 安裝 → 自測 → 收據(只裝預檢沒紅的)'; a = $aArgs })
$PlanB = @(
  @{ n = 'B1_token'; file = $(if ($Con) { $Con.FullName } else { Join-Path $Reg 'CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py' }); a = @('token'); sec = 900; label = 'VCGC token 卡(省 Token 第一步)' },
  @{ n = 'B2_mcp'; file = $(if ($Mcp) { $Mcp.FullName } else { Join-Path $Reg 'CGC_MDL279_MCPServer_v0000.py' }); a = @('--selftest'); sec = 600; label = 'VCGC MCP 唯讀門面自測(' + $(if ($Mcp) { $Mcp.BaseName -replace '^.*_', '' } else { '不在' }) + ')' })
$env:VIA_FROM_VCGC = 'YES'
$Lanes = @(
  @{ id = 'A'; zh = '外部工具'; args = @($VIA, $LogDir, 'A', $PlanA); run = $LaneRun },
  @{ id = 'B'; zh = 'VCGC 唯讀'; args = @($VIA, $LogDir, 'B', $PlanB); run = $LaneRun })
Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir

foreach ($k in @('A', 'B')) { $lg = Join-Path $LogDir ($k + '.log')
  if ((Test-Path -LiteralPath $lg) -and $script:LaneState.Contains($k)) { $yl = @(Get-Content -LiteralPath $lg -Encoding UTF8 | Where-Object { $_ -match '^\s*\[(YEL|注|GRAY)\]' })
    foreach ($y in $yl) { $script:Verdicts.Add("[$k] " + $y.Trim()) }; if (@($yl | Where-Object { $_ -match '^\s*\[(YEL|GRAY)\]' }).Count -and $script:LaneState[$k].lamp -eq 'GREEN') { $script:LaneState[$k].lamp = 'YELLOW' } } }
$of = Join-Path $LogDir 'A_ext.out'
if (Test-Path -LiteralPath $of) { foreach ($ln in @(Get-Content -LiteralPath $of -Encoding UTF8)) { $t = "$ln".Trim()
    if ($t -match '^\[RED\]|Traceback') { if ($t -notmatch '\[預檢\]' -and $script:Errors.Count -lt 60) { $script:Errors.Add("[A] $t") } }
    elseif ($t -match '^\[(OK|YEL|注|計)\]' -and $t -notmatch '\[預檢\]|\[計畫\]|▶') { $script:Verdicts.Add("[A] $t") } } }
foreach ($n in @('B1_token', 'B2_mcp')) { $f = Join-Path $LogDir ($n + '.out'); if (Test-Path -LiteralPath $f) {
    $last = @(Get-Content -LiteralPath $f -Encoding UTF8 | Where-Object { "$_" -match '\[(PASS|FAIL)\]|已啟用|啟用 \d|token' } | Select-Object -Last 2)
    foreach ($t in $last) { $t = "$t".Trim(); if ($t.Length -gt 220) { $t = $t.Substring(0, 220) }; $script:Verdicts.Add("[$n] $t") } } }

# ---------- 輸出檢視(只認本輪寫的檔) ----------
$OpenLater = [System.Collections.Generic.List[string]]::new()
$Review = { param($label, $path)
  if (-not (Test-Path -LiteralPath $path)) { $script:Verdicts.Add("[輸出] $label 不在:$path(黃)"); return }
  $it = Get-Item -LiteralPath $path; $fresh = ($it.LastWriteTime -ge $StartAt)
  $script:Verdicts.Add("[輸出] $label · " + $(if ($fresh) { '本輪寫的' } else { '不是本輪寫的(舊檔)' }) + " · " + $it.LastWriteTime.ToString('MM-dd HH:mm') + " · $([int]($it.Length / 1KB)) KB")
  if ($fresh -and $it.Extension -eq '.html') { $OpenLater.Add($path) } }
$rd = Join-Path $VIA 'VIA_Reports\vcgc\tools'
& $Review '外部工具啟用頁' (Join-Path $rd 'VIA_ExternalTools_latest.html')
& $Review '外部工具收據 JSON' (Join-Path $rd 'VIA_ExternalTools_latest.json')
& $Review '預檢收據' (Join-Path $rd 'VIA_ExternalTools_Preflight_latest.json')
& $Review 'Prettier 只檢收據' (Join-Path $rd 'VIA_PrettierCheck_latest.json')
& $Review 'Graphify 圖收據' (Join-Path $VIA 'VIA_Reports\graphify\VIA_Graphify_latest.json')

Show-VCSummary -Title $Title -LogDir $LogDir
if (-not $NoOpen) { $noOpenWas = $env:VIA_NO_OPEN; $env:VIA_NO_OPEN = $null
  try { foreach ($h in $OpenLater) { if (Test-Path -LiteralPath $h) { try { Start-Process -FilePath "$h" } catch { } } } }
  finally { if ($null -eq $noOpenWas -or $noOpenWas -eq '') { Remove-Item 'Env:VIA_NO_OPEN' -ErrorAction SilentlyContinue } else { $env:VIA_NO_OPEN = $noOpenWas } } }
