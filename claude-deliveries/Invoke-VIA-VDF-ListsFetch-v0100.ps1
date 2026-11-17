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
# Invoke-VIA-VDF-ListsFetch-v0100.ps1 — 2026-11-15。以上是 VeritasCeleritas.PS7.Skeleton-v0112 原文一字不動;只有這一段是本支的。
#   操作員 2026-11-15:「VDF 為多引擎資料庫擷取維護系統 · 整合好輸入項目 · 時間 2022-01-02 · 以 VCGC 省 Token 工具協助啟用 ·
#   先找出台股個股清單生成引擎 · 主動式台股 ETF 清單生成驗證引擎 · 每步都要 AST 導入加速器 · SYSTEM MANAGER 總控 · 一路跑一路修 ·
#   輸出全面齊到今天 · 中間三個個股個別項目 3017 3334 NVDA · 自動完成」
#   本支只啟動 VDF 自己的入口(L119 / L117):VDF_SystemManager 尾版 + ActivateVDF.py(本體 VDF_MDL013 尾版),PS 不含擷取邏輯。
#   兩張清單引擎 = 擷取冊第一步:009 VDF_MDL009_TWStockList(全台股)· 010 VDF_MDL010_ActiveETFList(主動式台股 ETF),之後 014 三代號宇宙。
#   道 A(VDF 主鏈,依序):
#     A0 找 VDF 工作樹(VDF 自己的 MAIN,固定在 origin/main;MDL014 WorkstationSync 的設計,不在 OneDrive)
#     A1 同步(兩道開跑前,主執行緒):工作樹落後 origin/main 才跑 ActivateVDF --sync --sync-only。成員帳本若有沒提交的新增行,先暫存、還原、同步後原樣補回(只增)
#     A2 輸入:大類起始日 TW_MARKET · FIN · OTHER = 2022-01-02(MACRO 不動,要動設 VIA_VDF_START_MACRO=1)· as-of = latest · TW_FIN 加 3017(已在就略過)
#     A3 ActivateVDF run --refill-apply:CPU / DRAM → 兩張清單(009 · 010)→ 分道擷取 · 引擎載入自測 · 資料庫補不足 → 總覽頁;每個子行程由它的鉤掛鎖定加速器 + 網路工具
#     A4 補缺 fetch fill --apply(只抓不足的部分;最多兩輪,補後不足 0 就停)
#     A5 三代號宇宙 fetch run 014 --apply + 兩張清單驗收 fetch verify 009 010
#     A6 個別項目:三代號 info 3017 3324 3334 · 族群 monitor(財報 / 每日量價 / 主動 ETF / 指數 / 國際每日)· 成員 TW_FIN · INTL_FIN
#   道 B(唯讀,與道 A 並行):VDF_SystemManager version · bridges(AST 橋覆蓋:加速器 + 網路工具)· health · conform
#   不做的事:不代設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 由操作員在啟動行自己設;沒設 = 擷取 GATED、零出網)· 不裝套件 ·
#             不改 VDF 以外的檔 · 不推 main。注意:A1 的同步是 VDF 自己的 WorkstationSync,它會把主 checkout 沒推的提交備份到新分支、把 VDF 收據推到新分支(從不推 main、從不 force)。
#   開關:VIA_VDF_ACT_ARGS='<ActivateVDF 額外參數>'(例 --mode fixture --flows fetch,db)· VIA_VDF_NOSYNC=1 不同步 · VIA_VDF_START=YYYY-MM-DD 改起始日 · VIA_VDF_START_MACRO=1 連 MACRO 一起改 · VIA_VDF_FILL_ROUNDS=0..3 · VIA_VDF_WT=<工作樹> 指定
if (-not (Test-Path -LiteralPath ("$VIA" + '\supportive modules\registry'))) {
  $cands = @(@($env:VIA_ROOT, (Join-Path $env:USERPROFILE 'OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'), (Join-Path $env:USERPROFILE 'Downloads\movies-dataset\VeritasIntelligenceAnalytics'), (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics')) | Where-Object { $_ -and (Test-Path -LiteralPath ("$_" + '\supportive modules\registry')) })
  if ($cands.Count) { $VIA = $cands[0]; Set-Location -LiteralPath $VIA }
  else { Write-Host "`e[91m[根] 找不到 VIA 主 checkout(要有 supportive modules\registry)。什麼都沒跑、沒寫。`e[0m"; Write-Host "`e[93mNEXT: 把 `$env:VIA_ROOT 設成主 checkout 的 VeritasIntelligenceAnalytics 夾後重跑`e[0m"; return } }
if (-not $PSBoundParameters.ContainsKey('Title')) { $Title = 'VDF 清單引擎 → 全擷取到最新 → 3017 · 3324 · NVDA' }
if (-not $PSBoundParameters.ContainsKey('MaxMin')) { $MaxMin = 330 }   # ActivateVDF 一輪最長 14400 秒;骨架預設 60 分會中途停
if (-not $NoCleanup) { Invoke-VCSafeCleanup }
$Run = Initialize-VCTemp; Initialize-VCAccel
$script:LogDir = Join-Path $VIA ("VIA_Reports\review\ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null; $LogDir = $script:LogDir
$StartAt = Get-Date
$StartDay = if ("$env:VIA_VDF_START" -match '^\d{4}-\d{2}-\d{2}$') { "$env:VIA_VDF_START" } else { '2022-01-02' }
$Cats = @('TW_MARKET', 'FIN', 'OTHER'); if ($env:VIA_VDF_START_MACRO -eq '1') { $Cats += 'MACRO' }
$FillRounds = if ("$env:VIA_VDF_FILL_ROUNDS" -match '^[0-3]$') { [int]$env:VIA_VDF_FILL_ROUNDS } else { 2 }
$net = ($env:VIA_NET_CONSENT -eq 'YES'); $scr = ($env:VIA_SCRAPE_CONSENT -eq 'YES')
$script:Verdicts.Add("[雙閘] VIA_NET_CONSENT=" + $(if ($net) { 'YES' } else { '未設' }) + " · VIA_SCRAPE_CONSENT=" + $(if ($scr) { 'YES' } else { '未設' }) + $(if ($net -and $scr) { ' → 真的出網擷取' } else { ' → 擷取步 GATED、零出網(本支不代設;要抓,在啟動行自己設)' }))
$script:Verdicts.Add("[輸入] 起始日 $StartDay → 大類 " + ($Cats -join ' · ') + " · as-of latest(台北最近已收盤交易日)· TW_FIN 加 3017 · 個別項目 3017 · 3324 · NVDA(另查 3334)")

# ---------- A0 VDF 工作樹(VDF 自己的 MAIN) ----------
$repo = "" + (& git -C "$VIA" rev-parse --show-toplevel 2>$null)
$wt = $null
if ($env:VIA_VDF_WT -and (Test-Path -LiteralPath ("$env:VIA_VDF_WT" + '\VeritasIntelligenceAnalytics\functional modules\VDF'))) { $wt = "$env:VIA_VDF_WT" }
if (-not $wt -and $repo) {
  foreach ($ln in @(& git -C "$repo" worktree list --porcelain 2>$null)) { if ("$ln" -match '^worktree (.+)$') { $p = $Matches[1].Trim() -replace '/', '\'; if ($p -match 'vdf-main' -and (Test-Path -LiteralPath ("$p" + '\VeritasIntelligenceAnalytics\functional modules\VDF'))) { $wt = $p; break } } } }
if (-not $wt -and $repo) {
  $def = Join-Path $env:LOCALAPPDATA ('VIA\' + (Split-Path -Leaf $repo) + '-vdf-main')
  if (Test-Path -LiteralPath ("$def" + '\VeritasIntelligenceAnalytics\functional modules\VDF')) { $wt = $def }
  else { $null = @(& git -C "$repo" fetch origin main --quiet 2>&1); $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $def)
    $o = @(& git -C "$repo" worktree add --detach "$def" origin/main 2>&1 | ForEach-Object { "" + $_ }); if ($LASTEXITCODE -eq 0) { $wt = $def; $script:Verdicts.Add("[工作樹] 新建 VDF 工作樹 $def(固定在 origin/main · 不在 OneDrive · 主 checkout 不動)") } else { $script:Errors.Add("[工作樹] 建不起來:" + (($o | Select-Object -Last 2) -join ' | ')) } } }
if (-not $wt) { $script:Errors.Add('[工作樹] 找不到也建不出 VDF 工作樹 → 什麼都沒跑。先跑一次 VDF 工作站同步,或設 $env:VIA_VDF_WT'); Show-VCSummary -Title $Title -LogDir $LogDir; return }
$WtVia = Join-Path $wt 'VeritasIntelligenceAnalytics'; $VdfDir = Join-Path $WtVia 'functional modules\VDF'
$Sm = Get-ChildItem -LiteralPath $VdfDir -Filter 'VDF_SystemManager_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$Act = Join-Path $VdfDir 'ActivateVDF.py'
$wtHead = "" + (& git -C "$wt" log -1 --format='%h %cI' 2>$null)
$script:Verdicts.Add("[工作樹] $wt · HEAD $wtHead · 管理器 " + $(if ($Sm) { $Sm.Name } else { '不在' }) + " · 主 checkout $repo 不動")

# ---------- A1 前置:要不要同步 · 成員帳本暫存 ----------
$Ledger = Join-Path $VdfDir 'VDF_FetchGroups_MemberLedger_v0100.jsonl'; $LedgerRel = 'VeritasIntelligenceAnalytics/functional modules/VDF/VDF_FetchGroups_MemberLedger_v0100.jsonl'
$null = @(& git -C "$wt" fetch origin main --quiet 2>&1)
$hHead = "" + (& git -C "$wt" rev-parse HEAD 2>$null); $hOrg = "" + (& git -C "$wt" rev-parse origin/main 2>$null)
$behind = 0; if ($hHead -and $hOrg -and $hHead -ne $hOrg) { $behind = [int]("" + (& git -C "$wt" rev-list --count "HEAD..origin/main" 2>$null)) }
$SyncPlan = if ($env:VIA_VDF_NOSYNC -eq '1') { 'off' } elseif ($behind -gt 0) { 'sync' } else { 'none' }
$Saved = @()
if ($SyncPlan -eq 'sync') {
  $dirty = @(& git -C "$wt" -c core.quotepath=false status --porcelain 2>$null | Where-Object { $_ -and $_ -notmatch 'output_hub|VIA_Reports' })
  $other = @($dirty | Where-Object { $_ -notmatch 'VDF_FetchGroups_MemberLedger_v0100\.jsonl' })
  if ($other.Count) { $SyncPlan = 'blocked'; $script:Verdicts.Add("[同步] 工作樹有帳本以外的未提交改動 $($other.Count) 筆(例:" + (($other | Select-Object -First 2) -join ' · ') + ")→ 不同步,照現況跑(WorkstationSync 會停下不覆蓋)") }
  elseif ($dirty.Count) {
    $Saved = @(& git -C "$wt" -c core.quotepath=false diff -U0 -- "$LedgerRel" 2>$null | Where-Object { $_ -match '^\+[^+]' } | ForEach-Object { $_.Substring(1) })
    $Saved | Set-Content -LiteralPath (Join-Path $LogDir 'ledger_saved_lines.jsonl') -Encoding UTF8
    $null = @(& git -C "$wt" checkout -- "$LedgerRel" 2>&1)
    $script:Verdicts.Add("[同步] 成員帳本有 $($Saved.Count) 行沒提交 → 先存到本輪 log 夾、還原檔案、同步後原樣補回(只增,不丟)") } }
$script:Verdicts.Add("[同步] 工作樹落後 origin/main $behind 個提交 · 計畫 " + @{ off = '關(VIA_VDF_NOSYNC=1)'; sync = '先同步再跑'; none = '已是最新,不同步'; blocked = '擋下,照現況跑' }[$SyncPlan])

# ---------- A1 同步在兩道開跑前做(同步會換工作樹的檔,唯讀道不能同時讀) ----------
if ($SyncPlan -eq 'sync') {
  Push-Location -LiteralPath $WtVia
  try { $null = Invoke-VCPython -Id 'A1_sync' -Argv @($Act, 'run', '--sync', '--sync-only', '--no-open') -Sec 3600 } finally { Pop-Location }
  $script:Verdicts.Add("[同步] ActivateVDF --sync --sync-only · rc $($script:LastRc) · 之後 HEAD " + ("" + (& git -C "$wt" log -1 --format='%h %cI' 2>$null))) }
if ($Saved.Count) {
  $cur = @(Get-Content -LiteralPath $Ledger -Encoding UTF8 -ErrorAction SilentlyContinue); $add = @($Saved | Where-Object { "$_".Trim() -and $cur -notcontains $_ })
  if ($add.Count) { Add-Content -LiteralPath $Ledger -Value $add -Encoding UTF8 }
  $script:Verdicts.Add("[同步] 成員帳本補回 $($add.Count) 行(原有的不重複)") }
$Sm = Get-ChildItem -LiteralPath $VdfDir -Filter 'VDF_SystemManager_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1

# ---------- 道 A / 道 B ----------
$LaneRun = { param($WtVia, $LogDir, $Id, $Plan)
  Set-Location -LiteralPath $WtVia; $prog = Join-Path $LogDir ($Id + '.progress'); $i = 0
  $skipGroup = ''
  foreach ($s in $Plan) { $i++
    $sa = @($s.a); $what = "" + $s.label
    if ($s.group -and $s.group -eq $skipGroup) { "[注] $what · 前一輪已達停止條件 → 略過"; continue }
    Set-Content -LiteralPath $prog ("" + [int](($i - 1) * 100 / $Plan.Count) + " · " + $what) -Encoding UTF8
    if (-not (Test-Path -LiteralPath $s.file)) { "[GRAY] $what · 檔不在 → 未跑"; continue }
    $json = ConvertTo-Json -InputObject @(@($s.file) + $sa) -Compress; $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
    $wrap = "import base64,json,os,sys,threading,runpy; a=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); t=threading.Timer($([int]$s.sec), lambda: (sys.stdout.flush(), os._exit(124))); t.daemon=True; t.start(); sys.argv=a; runpy.run_path(a[0], run_name='__main__')"
    $global:LASTEXITCODE = $null; $t0 = Get-Date
    $o = @(& python -c $wrap $b64 2>&1 | ForEach-Object { "" + $_ }); $rc = $global:LASTEXITCODE
    $dt = [int]((Get-Date) - $t0).TotalSeconds; $o | Set-Content -LiteralPath (Join-Path $LogDir ($s.n + '.out')) -Encoding UTF8
    $lamp = if ($null -eq $rc) { 'NOTE' } elseif ($rc -eq 0) { 'GREEN' } elseif ($rc -in 2, 3, 4) { 'YELLOW' } else { 'RED' }
    $why = if ($null -ne $rc) { @{ 2 = '黃 / 沒資料'; 3 = '缺件'; 4 = '等同意閘'; 124 = '逾時' }[[int]$rc] } else { $null }
    $tag = @{ GREEN = '[OK]'; YELLOW = '[YEL]'; RED = '[RED]'; NOTE = '[注]' }[$lamp]
    ($tag + ' ' + $what + ' · rc ' + $(if ($null -eq $rc) { '未回' } else { "$rc" }) + $(if ($why) { "($why)" } else { '' }) + ' · ' + $dt + 's · ' + $o.Count + ' 行')
    if ($s.skipif -and (($o -join "`n") -match $s.skipif)) { "[注] $what · 輸出符合「$($s.skipif)」→ 同組後續略過"; $skipGroup = "" + $s.group }
    if ($s.gate -and $lamp -eq 'RED') { "[RED] $what 紅 → 本道後續不跑(留灰)"; break } }
  Set-Content -LiteralPath $prog '100 · 完' -Encoding UTF8 }

$SmF = if ($Sm) { $Sm.FullName } else { Join-Path $VdfDir 'VDF_SystemManager_v0000.py' }
$PlanA = @()
foreach ($c in $Cats) { $PlanA += @{ n = "A2_start_$c"; file = $SmF; a = @('engine', 'run', 'MDL012', 'start', '--category', $c, '--set', $StartDay, '--apply'); sec = 300; label = "起始日 $c = $StartDay" } }
$PlanA += @(
  @{ n = 'A2_asof'; file = $SmF; a = @('engine', 'run', 'MDL012', 'asof', '--set', 'latest', '--apply'); sec = 300; label = 'as-of = latest' },
  @{ n = 'A2_add3017'; file = $SmF; a = @('engine', 'run', 'MDL012', 'add', 'TW_FIN', '3017', '--apply'); sec = 300; label = 'TW_FIN 加 3017' },
  @{ n = 'A2_starts'; file = $SmF; a = @('engine', 'run', 'MDL012', 'start'); sec = 300; label = '各大類起始日現況' },
  @{ n = 'A3_activate'; file = $Act; a = @(@('run', '--refill-apply', '--no-open') + @("$env:VIA_VDF_ACT_ARGS" -split '\s+' | Where-Object { $_ })); sec = 14400; label = 'ActivateVDF run --refill-apply(清單 → 分道擷取 → 引擎 → 資料庫 → 總覽)' })
for ($r = 1; $r -le $FillRounds; $r++) { $PlanA += @{ n = "A4_fill$r"; file = $SmF; a = @('fetch', 'fill', '--apply'); sec = 7200; label = "補缺第 $r 輪 fetch fill --apply"; group = 'fill'; skipif = '要抓 0 ·|GATED|雙閘' } }
$PlanA += @(
  @{ n = 'A5_014'; file = $SmF; a = @('fetch', 'run', '014', '--apply'); sec = 1800; label = '三代號宇宙 fetch run 014 --apply' },
  @{ n = 'A5_verify'; file = $SmF; a = @('fetch', 'verify', '009', '010'); sec = 600; label = '兩張清單驗收 fetch verify 009 010' },
  @{ n = 'A6_info'; file = $SmF; a = @('engine', 'run', 'VDF_MDL014_ThreeCodeUniverse', 'info', '3017', '3324', '3334'); sec = 600; label = '三代號 info 3017 3324 3334' },
  @{ n = 'A6_fin'; file = $SmF; a = @('engine', 'run', 'MDL012', 'members', 'TW_FIN'); sec = 300; label = '成員 TW_FIN' },
  @{ n = 'A6_intl'; file = $SmF; a = @('engine', 'run', 'MDL012', 'members', 'INTL_FIN'); sec = 300; label = '成員 INTL_FIN' },
  @{ n = 'A6_monitor'; file = $SmF; a = @('engine', 'run', 'MDL012', 'monitor', '--groups', 'TW_FIN,INTL_FIN,TW_PRICE_VOL,TW_ACTIVE_ETF,TW_INDEX,INTL_DAILY'); sec = 1800; label = '族群監控(到齊 / 落後天數)' })
$PlanB = @(
  @{ n = 'B1_version'; file = $SmF; a = @('version'); sec = 300; label = 'VDF_SystemManager version' },
  @{ n = 'B2_bridges'; file = $SmF; a = @('bridges'); sec = 900; label = 'AST 橋覆蓋 bridges(加速器 · 網路工具)' },
  @{ n = 'B3_health'; file = $SmF; a = @('health'); sec = 900; label = 'VDF health' },
  @{ n = 'B4_conform'; file = $SmF; a = @('conform'); sec = 900; label = 'VDF conform(標準管理器規格)' })
$Lanes = @(
  @{ id = 'A'; zh = 'VDF 主鏈'; args = @($WtVia, $LogDir, 'A', $PlanA); run = $LaneRun },
  @{ id = 'B'; zh = '唯讀檢查'; args = @($WtVia, $LogDir, 'B', $PlanB); run = $LaneRun })
Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir

# 道上的黃 / 灰 / 注補進黃字;有黃或灰的道從綠改成黃
foreach ($k in @('A', 'B')) { $lg = Join-Path $LogDir ($k + '.log')
  if ((Test-Path -LiteralPath $lg) -and $script:LaneState.Contains($k)) { $yl = @(Get-Content -LiteralPath $lg -Encoding UTF8 | Where-Object { $_ -match '^\s*\[(YEL|注|GRAY)\]' })
    foreach ($y in $yl) { $script:Verdicts.Add("[$k] " + $y.Trim()) }; if (@($yl | Where-Object { $_ -match '^\s*\[(YEL|GRAY)\]' }).Count -and $script:LaneState[$k].lamp -eq 'GREEN') { $script:LaneState[$k].lamp = 'YELLOW' } } }

# ---------- 判決行(每步只留判決;長輸出先試 VCGC 省 Token digest,回 NODATA 就用樣式) ----------
$tok = $null
try { $lk = Get-Content -LiteralPath (Join-Path $VIA 'supportive modules\registry\VIA_ToolVersion_Lock_v0100.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($lk.token.path) { $c = Join-Path (Split-Path -Parent $VIA) "$($lk.token.path)"; if (Test-Path -LiteralPath $c) { $tok = (Resolve-Path -LiteralPath $c).Path } } } catch { }
$pat = '^\s*\[(計|完成|OK|起始日|as-of|SKIP|資料家|鎖驗證|加速|資料庫清點|分道擷取|獨立核對|記憶體|VDF 編號同步|VDF engine run|驗收|同步|VDF MAIN|收據|倉|ABSENT|拒跑|RED|YEL|FAIL)|^\s*[①②③④⑤⑥⑦⑧⑨⑩]|^\s*[✓✗]|^\s*(TW_|INTL_|FIN|OTHER|MACRO)|摘要:|總判|GATED|bridges|"code_in"|"type"|"present"|"name"|落後|到齊|^\s*\d{4}\s*$|^\s*NVDA'
$redRx = '^\s*\[(RED|FAIL)\]|Traceback|Error:|\bRED\b'
$order = @('A1_sync', 'A2_start_TW_MARKET', 'A2_start_FIN', 'A2_start_OTHER', 'A2_start_MACRO', 'A2_asof', 'A2_add3017', 'A2_starts', 'A3_activate', 'A4_fill1', 'A4_fill2', 'A4_fill3', 'A5_014', 'A5_verify', 'A6_info', 'A6_fin', 'A6_intl', 'A6_monitor', 'B1_version', 'B2_bridges', 'B3_health', 'B4_conform')
foreach ($n in $order) {
  $of = Join-Path $LogDir ($n + '.out'); if (-not (Test-Path -LiteralPath $of)) { continue }
  $raw = @(Get-Content -LiteralPath $of -Encoding UTF8 | Where-Object { "$_".Trim() }); $keep = @(); $cap = $(if ($n -in 'A3_activate', 'A6_monitor', 'A6_info') { 45 } else { 14 })
  if ($raw.Count -gt 60 -and $tok) { $e0 = $script:Errors.Count; $keep = @(Invoke-VCPython -Id ('dg_' + $n) -Argv @($tok, 'digest', $of) -Sec 90 | Where-Object { "$_".Trim() })
    for ($j = $script:Errors.Count - 1; $j -ge $e0; $j--) { if ($script:Errors[$j] -like '[[]dg_*] rc 1 *') { $script:Errors.RemoveAt($j) } }
    if ($keep.Count -and (($keep -join ' ') -match 'NODATA')) { $keep = @() } }
  if (-not $keep.Count) { $hit = @($raw | Where-Object { $_ -match $pat }); $keep = @(@($hit | Where-Object { $_ -match $redRx } | Select-Object -First 12) + @($hit | Where-Object { $_ -notmatch $redRx } | Select-Object -Last ($cap - 4)) + @($raw | Select-Object -Last 2) | Select-Object -Unique) }
  foreach ($ln in ($keep | Select-Object -First $cap)) { $t = "$ln".Trim(); if ($t.Length -gt 220) { $t = $t.Substring(0, 220) }
    if ($t -match '^\[(RED|FAIL)\]|Traceback') { if ($script:Errors.Count -lt 60) { $script:Errors.Add("[$n] $t") } } elseif ($script:Verdicts.Count -lt 280) { $script:Verdicts.Add("[$n] $t") } } }

# ---------- 輸出檢視(只認本輪寫的檔) ----------
$OpenLater = [System.Collections.Generic.List[string]]::new()
$Review = { param($label, $path)
  if (-not (Test-Path -LiteralPath $path)) { $script:Verdicts.Add("[輸出] $label 不在:$path(黃)"); return }
  $it = Get-Item -LiteralPath $path; $fresh = ($it.LastWriteTime -ge $StartAt); $extra = ''
  if ($it.Extension -eq '.json' -and $it.Length -lt 20MB) { try { $j = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
      $extra = (@($j.PSObject.Properties | Where-Object { $_.Name -match '^(lamp|verdict|state|status|line|count|date|built_at|version)$' -and $_.Value -isnot [array] -and $_.Value -isnot [pscustomobject] } | ForEach-Object { $v = "$($_.Value)"; if ($v.Length -gt 80) { $v = $v.Substring(0, 80) }; $_.Name + '=' + $v }) -join ' · ') } catch { $extra = 'JSON 讀不進來' } }
  $script:Verdicts.Add("[輸出] $label · " + $(if ($fresh) { '本輪寫的' } else { '不是本輪寫的(舊檔)' }) + " · " + $it.LastWriteTime.ToString('MM-dd HH:mm') + " · $([int]($it.Length / 1KB)) KB" + $(if ($extra) { " · $extra" } else { '' }))
  if ($fresh -and $it.Extension -eq '.html') { $OpenLater.Add($path) } }
& $Review 'ActivateVDF 總覽 JSON' (Join-Path $WtVia 'VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.json')
& $Review 'ActivateVDF 總覽頁' (Join-Path $WtVia 'VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.html')
& $Review 'VDF 操作台主頁' (Join-Path $WtVia 'VIA_Reports\vdf\VDF_UI_latest.html')
$fh = Join-Path $WtVia 'VIA_Reports\vdf_fetch\dict'
& $Review '台股清單 009 驗收報告' (Join-Path $fh '0-1-TWStockList\verify_report.json')
& $Review '主動式 ETF 清單 010 驗收報告' (Join-Path $fh '0-2-ActiveETFList\verify_report.json')
$ld = @(& git -C "$wt" -c core.quotepath=false diff --stat -- "$LedgerRel" 2>$null)
if ($ld.Count) { $script:Verdicts.Add("[帳本] 成員帳本在 VDF 工作樹裡有未提交的新增行(本輪輸入)。下次同步前本支會先暫存再補回;要長期保存請由 VDF 線提交到分支開 PR") }

Show-VCSummary -Title $Title -LogDir $LogDir
if (-not $NoOpen) { $noOpenWas = $env:VIA_NO_OPEN; $env:VIA_NO_OPEN = $null
  try { foreach ($h in $OpenLater) { if (Test-Path -LiteralPath $h) { try { Start-Process -FilePath "$h" } catch { } } } }
  finally { if ($null -eq $noOpenWas -or $noOpenWas -eq '') { Remove-Item 'Env:VIA_NO_OPEN' -ErrorAction SilentlyContinue } else { $env:VIA_NO_OPEN = $noOpenWas } } }
