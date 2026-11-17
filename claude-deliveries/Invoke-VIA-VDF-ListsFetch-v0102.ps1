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
# Invoke-VIA-VDF-ListsFetch-v0102.ps1 — 2026-11-15 夜。以上是 VeritasCeleritas.PS7.Skeleton-v0112 原文一字不動;只有這一段是本支的。前版 v0100 · v0101 一字不動。
#   v0101 → v0102(桌機 v0100 實跑回饋 2026-11-15 16:17–21:48):
#     ① VDF 工作樹停在 10-21(落後 origin/main 821 提交 · 管理器 v0161)只因有 9 筆非帳本的未提交改動(例 docs/handoff/evidence/qg_onebridge.json)→ 同步被擋、跑的是舊碼。
#        本版:未提交改動先「收起」到本輪 log 夾(整份複本 + git diff --binary patch + 清單,可 git apply 還原)→ 還原 → 直接 git checkout --detach origin/main
#        (舊工作樹的 ActivateVDF 不一定會 --sync);工作樹若有不在 origin 的本機提交 → 先留本機分支 via/vdf-main-keep-<時戳>(不推)。超過 200 筆不自動收。
#     ② 舊 ActivateVDF 一步就用滿 14400 秒(引擎啟動 2958 秒 + e232 台股指數 1800 秒逾時)→ 整道 330 分被砍、補缺沒跑到。
#        本版:殼 420 分 · ActivateVDF 單步 10800 秒 · 補缺每輪 3600 秒(VIA_VDF_ACT_SEC / VIA_VDF_FILL_SEC 可改)→ 補缺一定輪得到。
# (以下為 v0101 原說明)
# Invoke-VIA-VDF-ListsFetch-v0101.ps1 — 2026-11-15。
#   操作員 2026-11-15 17:48:「輸入準備好 · 啟動兩個清單引擎也會生出輸入 · 先檢查全部都導入加速器及網路工具 AST 覆蓋率 100% · 給予版本號及編號 ·
#   先優化 CPU/DRAM · 取得清單後這些流程幾乎獨立 → 啟動分量最佳化規劃 · 獨立步驟同時啟動 · 最快完成所有流程並輸出 · 這個概念也傳給 VRN VCGC VDF VQG VAP」
#   v0100 → v0101 只換「道」:
#     C0(主執行緒,兩道開跑前)五系統 AST 覆蓋:VDF · VRN · VCGC · VQG · VAP 各自的夾 + 前綴 + 尾版,ast.parse 認加速器橋 / 網路工具橋(網路呼叫者才要)·
#        薄尾沿前版鏈 · 版本號 = _vNNNN · 編號 = VCGC 編號冊(只讀,冊上沒有 = 待號)· 全表 cov_latest.csv。只報不改(他系統的檔歸他系統)
#     道 A 一個 python 動詞:VIA_ListsFirstDAG dag(本輪 log 夾裡落地的輔助檔,不進任何系統的夾)——
#        CPU/DRAM 規劃 → 並行讀現況(起始日 / as-of / 成員)→ 只寫缺的(同一本帳 → 串;已是目標值 = 零寫入)→
#        ActivateVDF(它自己:CPU/DRAM → 009 · 010 → 依資料庫分道並行擷取 → 引擎 → 資料庫)與「等兩張清單落地」同時起;
#        清單一落地就同時起 三代號 info · 清單驗收(不等擷取跑完)→ ActivateVDF 完 → 補缺(最多 N 輪,0 就停)→ 014 → 族群監控 → HTML 時間軸
#     道 B(唯讀,與道 A 並行):VDF_SystemManager version · bridges · number · health
#   不做的事:不代設同意閘 · 不裝套件 · 不改任何系統的檔 · 不推 main(A1 同步照 v0100:VDF 自己的 WorkstationSync,可能把備份 / 收據推到新分支)
#   開關同 v0100:VIA_VDF_ACT_ARGS · VIA_VDF_NOSYNC · VIA_VDF_START · VIA_VDF_START_MACRO · VIA_VDF_FILL_ROUNDS · VIA_VDF_WT;另 VIA_COV_SYSTEMS=VDF,VRN… 只查部分系統
if (-not (Test-Path -LiteralPath ("$VIA" + '\supportive modules\registry'))) {
  $cands = @(@($env:VIA_ROOT, (Join-Path $env:USERPROFILE 'OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'), (Join-Path $env:USERPROFILE 'Downloads\movies-dataset\VeritasIntelligenceAnalytics'), (Join-Path $env:USERPROFILE 'movies-dataset\VeritasIntelligenceAnalytics')) | Where-Object { $_ -and (Test-Path -LiteralPath ("$_" + '\supportive modules\registry')) })
  if ($cands.Count) { $VIA = $cands[0]; Set-Location -LiteralPath $VIA }
  else { Write-Host "`e[91m[根] 找不到 VIA 主 checkout(要有 supportive modules\registry)。什麼都沒跑、沒寫。`e[0m"; Write-Host "`e[93mNEXT: 把 `$env:VIA_ROOT 設成主 checkout 的 VeritasIntelligenceAnalytics 夾後重跑`e[0m"; return } }
if (-not $PSBoundParameters.ContainsKey('Title')) { $Title = 'VDF 清單先行 → 相依圖並行 → 3017 · 3324 · NVDA(v0102)' }
if (-not $PSBoundParameters.ContainsKey('MaxMin')) { $MaxMin = 420 }   # ActivateVDF 一輪最長 14400 秒;骨架預設 60 分會中途停
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
$Saved = @(); $Shelved = 0
if ($SyncPlan -eq 'sync') {
  $st = @(& git -C "$wt" -c core.quotepath=false status --porcelain --untracked-files=no 2>$null | Where-Object { "$_".Trim() })
  $dirtyPaths = @($st | ForEach-Object { $p = "$_".Substring(3).Trim().Trim('"'); if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1].Trim('"') }; $p } | Where-Object { $_ -and $_ -notmatch 'output_hub|VIA_Reports' })
  $other = @($dirtyPaths | Where-Object { $_ -notmatch 'VDF_FetchGroups_MemberLedger_v0100\.jsonl$' })
  if (@($dirtyPaths | Where-Object { $_ -match 'VDF_FetchGroups_MemberLedger_v0100\.jsonl$' }).Count) {
    $Saved = @(& git -C "$wt" -c core.quotepath=false diff -U0 -- "$LedgerRel" 2>$null | Where-Object { $_ -match '^\+[^+]' } | ForEach-Object { $_.Substring(1) })
    $Saved | Set-Content -LiteralPath (Join-Path $LogDir 'ledger_saved_lines.jsonl') -Encoding UTF8
    $null = @(& git -C "$wt" checkout -- "$LedgerRel" 2>&1)
    $script:Verdicts.Add("[同步] 成員帳本有 $($Saved.Count) 行沒提交 → 先存到本輪 log 夾、還原檔案、同步後原樣補回(只增,不丟)") }
  if ($other.Count -gt 200) { $SyncPlan = 'blocked'; $script:Errors.Add("[同步] 工作樹有 $($other.Count) 筆未提交改動(超過 200,不自動收起)→ 不同步 · 例:" + (($other | Select-Object -First 3) -join ' · ')) }
  elseif ($other.Count) {
    # v0102:未提交改動先「收起」(整份複本 + 二進位安全 patch + 清單,全在本輪 log 夾,可 git apply 還原)→ 還原那幾個檔 → 才能同步
    $Shelf = Join-Path $LogDir 'presync_shelf'; $null = New-Item -ItemType Directory -Force -Path $Shelf
    $patch = Join-Path $LogDir 'presync_shelf.patch'; $null = @(& git -C "$wt" -c core.quotepath=false diff --binary HEAD "--output=$patch" -- @other 2>&1)
    $man = foreach ($p in $other) { $src = Join-Path $wt ($p -replace '/', '\'); $dst = Join-Path $Shelf ($p -replace '/', '\')
      if (Test-Path -LiteralPath $src) { $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst); Copy-Item -LiteralPath $src -Destination $dst -Force
        [pscustomobject]@{ path = $p; state = 'copied'; sha256 = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower() } } else { [pscustomobject]@{ path = $p; state = 'deleted_in_worktree'; sha256 = '' } } }
    ConvertTo-Json -InputObject @{ at = (Get-Date).ToString('s'); worktree = $wt; head = $hHead; patch = $patch; files = @($man) } -Depth 4 | Set-Content -LiteralPath (Join-Path $LogDir 'presync_shelf.json') -Encoding UTF8
    $null = @(& git -C "$wt" reset -q -- @other 2>&1); $null = @(& git -C "$wt" checkout -- @other 2>&1)
    $left = @(& git -C "$wt" -c core.quotepath=false status --porcelain --untracked-files=no -- @other 2>$null | Where-Object { "$_".Trim() })
    if ($left.Count) { $SyncPlan = 'blocked'; $script:Errors.Add("[同步] 收起後仍有 $($left.Count) 筆改動還原不了 → 不同步 · 例:" + (($left | Select-Object -First 2) -join ' · ')) }
    else { $Shelved = $other.Count; $script:Verdicts.Add("[同步] 工作樹 $Shelved 筆未提交改動已收起(複本 + patch 在 $Shelf · 還原:git -C `"$wt`" apply `"$patch`")→ 可以同步(例:" + (($other | Select-Object -First 2) -join ' · ') + ")") } } }
$script:Verdicts.Add("[同步] 工作樹落後 origin/main $behind 個提交 · 計畫 " + @{ off = '關(VIA_VDF_NOSYNC=1)'; sync = '先同步再跑'; none = '已是最新,不同步'; blocked = '擋下,照現況跑' }[$SyncPlan])

# ---------- A1 同步在兩道開跑前做(v0102:直接 git 換到 origin/main;舊工作樹裡的 ActivateVDF 可能還不會 --sync)----------
if ($SyncPlan -eq 'sync') {
  $ahead = 0; try { $ahead = [int]("" + (& git -C "$wt" rev-list --count "origin/main..HEAD" 2>$null)) } catch { $ahead = 0 }
  if ($ahead -gt 0) { $bk = 'via/vdf-main-keep-' + (Get-Date -Format 'yyyyMMdd_HHmmss'); $null = @(& git -C "$wt" branch "$bk" HEAD 2>&1)
    $script:Verdicts.Add("[同步] 工作樹有 $ahead 個本機提交不在 origin → 先留本機分支 $bk(不推)") }
  $go = @(& git -C "$wt" checkout --detach origin/main 2>&1 | ForEach-Object { "" + $_ }); $rcg = $LASTEXITCODE
  $now = "" + (& git -C "$wt" rev-parse HEAD 2>$null)
  if ($rcg -eq 0 -and $now -eq $hOrg) { $script:Verdicts.Add("[同步] git checkout --detach origin/main · rc 0 · 之後 HEAD " + ("" + (& git -C "$wt" log -1 --format='%h %cI' 2>$null))) }
  else { $script:Errors.Add("[同步] 換到 origin/main 失敗 rc $rcg · " + (($go | Select-Object -Last 2) -join ' · ') + " → 照現況跑") } }
if ($Saved.Count) {
  $cur = @(Get-Content -LiteralPath $Ledger -Encoding UTF8 -ErrorAction SilentlyContinue); $add = @($Saved | Where-Object { "$_".Trim() -and $cur -notcontains $_ })
  if ($add.Count) { Add-Content -LiteralPath $Ledger -Value $add -Encoding UTF8 }
  $script:Verdicts.Add("[同步] 成員帳本補回 $($add.Count) 行(原有的不重複)") }
$Sm = Get-ChildItem -LiteralPath $VdfDir -Filter 'VDF_SystemManager_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1

# ---------- 落地輔助檔(本輪 log 夾,不進任何系統的夾) ----------
$DagPy = Join-Path $LogDir 'VIA_ListsFirstDAG_v0101.py'
@'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ListsFirstDAG v0101 — 清單先行 → 相依圖並行扇出(2026-11-15 操作員令)
「輸入準備好 · 啟動兩個清單引擎也會生出輸入 · 先檢查全部都導入加速器及網路工具 AST 覆蓋率 100% · 給予版本號及編號 ·
  先優化 CPU/DRAM · 取得清單後這些流程幾乎獨立 → 啟動分量最佳化規劃 · 獨立步驟同時啟動 · 最快完成所有流程並輸出」

三個動詞(全部只讀他系統;只經 VDF 自己的入口跑 VDF):
  res  CPU / DRAM 規劃:核數、可用記憶體、保底 1024 MB → 本輪並行槽數(只動本行程:gc · 不改他行程優先序)
  cov  五系統 AST 覆蓋(VDF · VRN · VCGC · VQG · VAP):各系統自己的夾 + 自己的前綴 + 尾版(_vNNNN 最大)·
       ast.parse 認「加速器橋」(import VIA_SuperAccel_Module / VeritasCeleritas*)與「網路工具橋」
       (模組層 VIA_NET_TOOL_PATH 指派 + def _via_net*);網路呼叫者 = 匯入 requests / yfinance / urllib.request … 的尾版 ·
       版本號 = 檔名 _vNNNN · 編號 = VCGC 編號冊 VIA_NumberBooks(MDL / ENG)只讀,冊上沒有 = 待號
  dag  VDF 相依圖:輸入(起始日 / as-of / 成員,同帳本 → 串)→ ActivateVDF(它自己:CPU/DRAM → 009 · 010 → 依資料庫分道並行擷取 → 引擎 → 資料庫)
       兩張清單一落地(本輪寫的 verify_report)就同時起:三代號 info · 清單驗收;成員查詢不等任何東西;
       ActivateVDF 完 → 補缺(最多 N 輪,補後 0 就停)→ 014 → 族群監控。輸出 JSON + HTML(四燈 · 時間軸 · 串行估計 vs 牆鐘)
v0101(2026-11-15 桌機實跑回饋):ActivateVDF 單步上限 14400 → 10800 秒、補缺每輪 7200 → 3600 秒(可用 --act-sec / --fill-sec 改),
  讓「ActivateVDF + 補缺 2 輪 + 014 + 監控」整條 ≤ 360 分,落在殼的 420 分內 → 補缺不再因整道逾時被砍掉。
不做:不代設同意閘 · 不裝套件 · 不寫任何系統的程式檔 · 不推 git · 不碰 TA-Lib。
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures as cf
import gc
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

TOOL = "VIA_ListsFirstDAG v0101"
PAL = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
VER_RX = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{4})\.py$")
SKIP = {"__pycache__", "_superseded", "_superseded_redundant", "VIA_RetiredEngines", "references", "intake", "retired", "evidence",
        "node_modules", ".git", "VIA_Reports", "ASSETS", "SCOPE_COPY", "tests", "_rebuilds_superseded"}
SYSTEMS = [  # 系統 · 自己的夾 · 自己的前綴(同各 SystemManager 的 SM_CONFIG)· 遞迴
    ("VDF", "functional modules/VDF", ("VDF_",), True),
    ("VRN", "functional modules/VRN", ("VRN2_", "VRN_"), True),
    ("VCGC", "supportive modules/registry", ("CGC_",), False),
    ("VQG", "functional modules/VQG", ("VQG_",), True),
    ("VAP", "functional modules/VAP", ("VAP_",), True),
]
ACCEL_MODS = ("VIA_SuperAccel_Module", "VeritasCeleritas")
NET_LIBS = ("requests", "httpx", "aiohttp", "urllib.request", "urllib3", "http.client", "yfinance", "curl_cffi", "akshare",
            "FinMind", "twstock", "fredapi", "websocket", "websockets", "pandas_datareader", "selenium", "playwright", "ftplib")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def say(*a):
    print(*a, flush=True)


# ───────────────────────── res ─────────────────────────
def res_plan(floor_mb=1024, per_mb=300):
    gc.collect()
    logical = os.cpu_count() or 1
    total = avail = None
    how = "none"
    try:
        import psutil  # noqa: PLC0415
        vm = psutil.virtual_memory()
        total, avail, how = vm.total // 2**20, vm.available // 2**20, "psutil"
    except Exception:
        if os.name == "nt":
            try:
                import ctypes  # noqa: PLC0415

                class MS(ctypes.Structure):
                    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong),
                                ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong),
                                ("av", ctypes.c_ulonglong), ("ae", ctypes.c_ulonglong)]
                ms = MS(); ms.l = ctypes.sizeof(MS)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
                total, avail, how = ms.t // 2**20, ms.a // 2**20, "GlobalMemoryStatusEx"
            except Exception:
                pass
        elif Path("/proc/meminfo").exists():
            kv = dict(ln.split(":", 1) for ln in Path("/proc/meminfo").read_text().splitlines() if ":" in ln)
            total = int(kv["MemTotal"].split()[0]) // 1024
            avail = int(kv.get("MemAvailable", kv["MemFree"]).split()[0]) // 1024
            how = "/proc/meminfo"
    cpu_slots = max(2, logical - 1)
    mem_slots = max(2, int(((avail or 4096) - floor_mb) // per_mb)) if avail else cpu_slots
    slots = max(2, min(6, cpu_slots, mem_slots))
    return {"logical": logical, "total_mb": total, "avail_mb": avail, "how": how, "floor_mb": floor_mb, "per_step_mb": per_mb,
            "slots": slots, "why": f"核 {logical}(留 1)→ {cpu_slots} · 記憶體 ({avail}−{floor_mb})÷{per_mb} → {mem_slots} · 上限 6 → {slots}"}


# ───────────────────────── cov ─────────────────────────
def own_tails(via: Path, d: str, prefixes, rec: bool):
    base = via / d
    if not base.is_dir():
        return None
    fams = {}
    it = base.rglob("*.py") if rec else base.glob("*.py")
    for p in it:
        rel = p.relative_to(base)
        if any(part in SKIP for part in rel.parts[:-1]):
            continue
        m = VER_RX.match(p.name)
        if not (m and p.name.startswith(prefixes)):
            continue
        fam, ver = m.group("fam"), int(m.group("ver"))
        if fam not in fams or ver > fams[fam][0]:
            fams[fam] = (ver, p)
    return fams


def numbers(via: Path) -> dict:
    out = {}
    nb = via / "supportive modules" / "registry" / "VIA_NumberBooks"
    for g in ("VIA_NumberBook_MDL_v*.jsonl", "VIA_NumberBook_ENG_v*.jsonl"):
        for bp in sorted(nb.glob(g)):
            try:
                lines = bp.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for ln in lines:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if isinstance(r, dict) and r.get("name") and r.get("code"):
                    out[str(r["name"]).removesuffix(".py")] = r["code"]
    return out


def _mod_names(node):
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module]
    return []


def ast_check(p: Path) -> dict:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
    except SyntaxError as exc:
        return {"parse": False, "why": f"SyntaxError 行 {exc.lineno}"}
    accel = net_assign = net_def = False
    net_caller = []
    # 模組層(含模組層 try / if 內)找橋
    stack = list(tree.body)
    while stack:
        n = stack.pop()
        for name in _mod_names(n):
            if name.startswith(ACCEL_MODS):
                accel = True
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Name) and t.id == "VIA_NET_TOOL_PATH" for t in tg):
                net_assign = True
            if any(isinstance(t, ast.Name) and t.id == "VIA_ACCEL" for t in tg) and isinstance(n.value, ast.Call):
                accel = True
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_via_net"):
            net_def = True
        if isinstance(n, (ast.Try, ast.If)):
            stack.extend(n.body); stack.extend(getattr(n, "orelse", []))
            for h in getattr(n, "handlers", []):
                stack.extend(h.body)
            stack.extend(getattr(n, "finalbody", []))
    for n in ast.walk(tree):
        for name in _mod_names(n):
            if name in NET_LIBS or any(name.startswith(x + ".") for x in NET_LIBS):
                net_caller.append(name)
    prior = dyn = None
    for n in tree.body:   # 薄尾:模組層 PRIOR_NAME = "<同族前版>.py" → 前版鏈
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("PRIOR_NAME", "PRIOR_FILE") for t in n.targets) \
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str) and VER_RX.match(n.value.value):
            prior = n.value.value
    if not accel:
        strs = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        if "import_module" in names or any("import_module" in x for x in strs):
            if any(("VeritasCeleritas" in x or "VIA_SuperAccel" in x or "accelerator" in x) for x in strs):
                dyn = True
    return {"parse": True, "accel": accel, "net_bridge": net_assign and net_def, "net_caller": sorted(set(net_caller)), "prior": prior, "dyn": bool(dyn)}


def ast_chain(p: Path, depth=0) -> dict:
    """尾版本身沒有加速器橋,但它是薄尾(PRIOR_NAME 指同夾前版)→ 沿前版鏈找;最多 40 層。"""
    a = ast_check(p)
    if a.get("parse") and not a.get("accel") and a.get("prior") and depth < 40:
        q = p.with_name(a["prior"])
        if q.exists() and q != p:
            b = ast_chain(q, depth + 1)
            if b.get("accel"):
                a["accel"] = True; a["via"] = b.get("via") or q.name
            if not a.get("net_bridge") and b.get("net_bridge"):
                a["net_bridge"] = True
            a["dyn"] = a.get("dyn") or b.get("dyn")
    return a


def cov(via: Path, out: Path, systems=None):
    t0 = time.time()
    book = numbers(via)
    rows, summ = [], []
    jobs = []
    for sysname, d, pref, rec in SYSTEMS:
        if systems and sysname not in systems:
            continue
        fams = own_tails(via, d, pref, rec)
        if fams is None:
            summ.append({"system": sysname, "dir": d, "lamp": "GRAY", "tails": 0, "note": "夾不在(這台 / 這份 checkout 沒有)"})
            continue
        for fam, (ver, p) in sorted(fams.items()):
            jobs.append((sysname, fam, ver, p))
    with cf.ThreadPoolExecutor(max_workers=min(16, (os.cpu_count() or 2) * 2)) as ex:
        res = list(ex.map(lambda j: (j, ast_chain(j[3])), jobs))
    for (sysname, fam, ver, p), a in res:
        stem = p.stem
        code = book.get(stem) or book.get(fam)
        need_net = bool(a.get("net_caller"))
        ok = a["parse"] and a.get("accel") and (a.get("net_bridge") or not need_net)
        soft = a["parse"] and not a.get("accel") and a.get("dyn") and (a.get("net_bridge") or not need_net)
        why = []
        if not a["parse"]:
            why.append(a["why"])
        else:
            if a.get("via"):
                why.append("經前版鏈 " + a["via"])
            if not a["accel"]:
                why.append("加速器動態載入(import_module),不是標準橋" if a.get("dyn") else "缺加速器橋")
            if need_net and not a["net_bridge"]:
                why.append("網路呼叫者缺網路工具橋(" + ",".join(a["net_caller"][:3]) + ")")
        if not code:
            why.append("待號")
        rows.append({"system": sysname, "family": fam, "version": "v%04d" % ver, "code": code or "", "file": str(p.relative_to(via)),
                     "parse": a["parse"], "accel": bool(a.get("accel")), "net_caller": ",".join(a.get("net_caller", [])),
                     "net_bridge": bool(a.get("net_bridge")),
                     "lamp": "GREEN" if (ok and code) else ("YELLOW" if (ok or soft) else "RED"), "why": " · ".join(why)})
    for sysname, d, pref, rec in SYSTEMS:
        if systems and sysname not in systems:
            continue
        r = [x for x in rows if x["system"] == sysname]
        if not r:
            continue
        n = len(r); acc = sum(x["accel"] for x in r); par = sum(x["parse"] for x in r)
        nc = [x for x in r if x["net_caller"]]; nb = sum(x["net_bridge"] for x in nc); num = sum(bool(x["code"]) for x in r)
        lamp = "RED" if any(x["lamp"] == "RED" for x in r) else ("YELLOW" if any(x["lamp"] == "YELLOW" for x in r) else "GREEN")
        summ.append({"system": sysname, "dir": d, "lamp": lamp, "tails": n, "parse": par, "accel": acc, "net_callers": len(nc), "net_bridged": nb,
                     "numbered": num, "accel_pct": round(100 * acc / n, 1), "net_pct": round(100 * nb / len(nc), 1) if nc else 100.0,
                     "num_pct": round(100 * num / n, 1)})
    order = {"VDF": 0, "VRN": 1, "VCGC": 2, "VQG": 3, "VAP": 4}
    summ.sort(key=lambda s: order.get(s["system"], 9))
    doc = {"tool": TOOL, "at": now(), "via": str(via), "secs": round(time.time() - t0, 1), "book_codes": len(book), "systems": summ, "rows": rows}
    out.mkdir(parents=True, exist_ok=True)
    (out / "cov_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "cov_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        cols = ["lamp", "system", "family", "version", "code", "parse", "accel", "net_caller", "net_bridge", "why", "file"]
        fh.write(",".join(cols) + "\n")
        for x in rows:
            fh.write(",".join('"%s"' % str(x[c]).replace('"', "'") for c in cols) + "\n")
    for s in summ:
        if s.get("tails"):
            tag = {"GREEN": "[OK]", "YELLOW": "[YEL]", "RED": "[RED]"}[s["lamp"]]
            say(f"{tag} [覆蓋] {s['system']:<4} 尾版 {s['tails']} · AST 可解析 {s['parse']}/{s['tails']} · 加速器橋 {s['accel']}/{s['tails']}"
                f"({s['accel_pct']}%)· 網路呼叫者 {s['net_callers']} 支有網路工具橋 {s['net_bridged']}/{s['net_callers']}({s['net_pct']}%)"
                f" · VCGC 編號 {s['numbered']}/{s['tails']}({s['num_pct']}%)")
        else:
            say(f"[注] [覆蓋] {s['system']} {s['note']}")
    bad = [x for x in rows if x["lamp"] != "GREEN"]
    for x in sorted(bad, key=lambda r: r["lamp"] != "RED")[:25]:
        say(f"[{'RED' if x['lamp'] == 'RED' else 'YEL'}] [覆蓋] {x['system']} {x['family']} {x['version']} {x['code'] or '待號'} · {x['why']}")
    if len(bad) > 25:
        say(f"[YEL] [覆蓋] 另有 {len(bad) - 25} 支不合 / 待號(全表 cov_latest.csv)")
    say(f"[計] [覆蓋] {len(rows)} 支尾版 · {doc['secs']}s · 編號冊 {len(book)} 個號 · 表 {out / 'cov_latest.csv'}")
    return doc


# ───────────────────────── dag ─────────────────────────
class Step:
    def __init__(self, sid, label, deps, argv=None, sec=600, kind="run", group=None, skipif=None, wait=None, after=None):
        self.sid, self.label, self.deps, self.argv, self.sec, self.kind = sid, label, list(deps), argv, sec, kind
        self.group, self.skipif, self.wait, self.after = group, skipif, wait or [], after
        self.cfg = {}; self.rc = None; self.lamp = "GRAY"; self.t0 = self.t1 = None; self.lines = 0; self.note = ""


def kill_tree(pid):
    try:
        import psutil  # noqa: PLC0415
        p = psutil.Process(pid)
        for c in p.children(recursive=True):
            try:
                c.kill()
            except Exception:
                pass
        p.kill()
    except Exception:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30)
            else:
                os.kill(pid, 9)
        except Exception:
            pass


def run_step(st: Step, cwd: Path, logs: Path, t_start: float, steps: dict, prog):
    st.t0 = time.time()
    if st.kind == "wait":
        st.lamp, st.note = "YELLOW", "清單沒在本輪落地 → 照 ActivateVDF 結束放行"
        while time.time() - st.t0 < st.sec:
            fresh = [Path(w).exists() and Path(w).stat().st_mtime >= t_start for w in st.wait]
            if all(fresh):
                st.lamp, st.note = "GREEN", "兩張清單本輪已落地 → 放行同時起跑"
                break
            if st.after and steps[st.after].t1:
                break
            time.sleep(2)
        st.rc = 0 if st.lamp == "GREEN" else 2
        st.t1 = time.time()
        return st
    out = logs / (st.sid + ".out")
    if st.kind == "inputs":
        return run_inputs(st, cwd, logs)
    if not Path(st.argv[0]).exists():
        st.rc, st.lamp, st.note, st.t1 = None, "GRAY", "檔不在 → 未跑", time.time()
        return st
    prog(f"▶ {st.label}")
    with out.open("w", encoding="utf-8") as fh:
        p = subprocess.Popen([sys.executable, *st.argv], cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        try:
            st.rc = p.wait(timeout=st.sec)
        except subprocess.TimeoutExpired:
            kill_tree(p.pid); st.rc = 124
    st.t1 = time.time()
    txt = out.read_text(encoding="utf-8", errors="replace")
    st.lines = txt.count("\n")
    st.lamp = "GREEN" if st.rc == 0 else ("YELLOW" if st.rc in (2, 3, 4) else "RED")
    st.note = {2: "黃 / 沒資料", 3: "缺件", 4: "等同意閘", 124: "逾時"}.get(st.rc, "")
    if st.skipif and re.search(st.skipif, txt):
        st.note = (st.note + " · " if st.note else "") + "符合停止條件 → 同組後續略過"
        st.after = "STOPGROUP"
    return st


def _read(logs, sid):
    f = logs / (sid + ".out")
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


def run_inputs(st: Step, cwd: Path, logs: Path):
    """讀現況 → 只寫缺的(冪等):起始日 / as-of / 成員都寫同一本成員帳本 → 依序;全部已是目標值 = 零寫入、零秒。"""
    sm, cfg = st.argv[0], st.cfg
    cur = {m.group(1): m.group(2) for m in re.finditer(r"^\s*(TW_MARKET|FIN|MACRO|OTHER)\s.*?起始日 (\d{4}-\d{2}-\d{2})", _read(logs, "q_starts"), re.M)}
    asof = re.search(r"設定 (\S+) →", _read(logs, "q_asof"))
    mem = re.findall(r"^\s*(\d{4,6})\s*$", _read(logs, "q_members_fin"), re.M)
    todo = []
    for c in cfg["cats"]:
        if cur.get(c) != cfg["start"]:
            todo.append(("起始日 %s %s → %s" % (c, cur.get(c, "?"), cfg["start"]), ["engine", "run", "MDL012", "start", "--category", c, "--set", cfg["start"], "--apply"]))
    if not (asof and asof.group(1) == "latest"):
        todo.append(("as-of → latest", ["engine", "run", "MDL012", "asof", "--set", "latest", "--apply"]))
    if "3017" not in mem:
        todo.append(("TW_FIN 加 3017", ["engine", "run", "MDL012", "add", "TW_FIN", "3017", "--apply"]))
        todo.append(("讀 成員 TW_FIN(加後)", ["engine", "run", "MDL012", "members", "TW_FIN"]))
    lines = ["[現況] 起始日 " + " · ".join("%s=%s" % kv for kv in sorted(cur.items())) + " · as-of " + (asof.group(1) if asof else "?") +
             " · TW_FIN 成員 " + " ".join(mem)]
    rc_all = 0
    for label, args in todo:
        r = subprocess.run([sys.executable, sm, *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=300)
        lines.append("[寫] %s · rc %s" % (label, r.returncode)); lines.extend("    " + x for x in r.stdout.splitlines()[-4:])
        if label.startswith("讀 成員"):
            (logs / "q_members_fin.out").write_text(r.stdout, encoding="utf-8")
        rc_all = rc_all or r.returncode
    if not todo:
        lines.append("[略過] 全部已是目標值 → 零寫入(帳本不多加行)")
    (logs / (st.sid + ".out")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    st.rc, st.t1, st.lines = rc_all, time.time(), len(lines)
    st.lamp = "GREEN" if rc_all == 0 else "RED"
    st.note = ("寫了 %d 項" % len([t for t in todo if not t[0].startswith("讀")])) if todo else "全部已是目標值 → 零寫入"
    return st


def build_dag(a, via: Path):
    sm, act = a.sm, a.act
    fh = via / "VIA_Reports" / "vdf_fetch" / "dict"
    S = []
    S.append(Step("q_starts", "讀 各大類起始日現況", [], [sm, "engine", "run", "MDL012", "start"], 300))
    S.append(Step("q_asof", "讀 as-of 現況", [], [sm, "engine", "run", "MDL012", "asof"], 300))
    S.append(Step("q_members_fin", "讀 成員 TW_FIN", [], [sm, "engine", "run", "MDL012", "members", "TW_FIN"], 300))
    S.append(Step("q_members_intl", "讀 成員 INTL_FIN", [], [sm, "engine", "run", "MDL012", "members", "INTL_FIN"], 300))
    S.append(Step("in_apply", f"輸入 只寫缺的:起始日 {'·'.join(a.cats)} = {a.start} · as-of latest · TW_FIN 加 3017(同一本帳 → 串)",
                  ["q_starts", "q_asof", "q_members_fin"], [sm], 1200, kind="inputs"))
    S[-1].cfg = {"cats": a.cats, "start": a.start}
    S.append(Step("activate", "ActivateVDF(CPU/DRAM → 009 · 010 → 分道並行擷取 → 引擎 → 資料庫 → 總覽)", ["in_apply"],
                  [act, "run", "--refill-apply", "--no-open", *a.act_args], a.act_sec))
    S.append(Step("lists_landed", "等兩張清單本輪落地(009 · 010 驗收報告)", ["in_apply"], kind="wait", sec=7200,
                  wait=[str(fh / "0-1-TWStockList" / "verify_report.json"), str(fh / "0-2-ActiveETFList" / "verify_report.json")], after="activate"))
    S.append(Step("q_info", "三代號 info 3017 3324 3334", ["lists_landed"], [sm, "engine", "run", "VDF_MDL014_ThreeCodeUniverse", "info", "3017", "3324", "3334"], 600))
    S.append(Step("q_verify", "兩張清單驗收 fetch verify 009 010", ["lists_landed"], [sm, "fetch", "verify", "009", "010"], 600))
    prev = ["activate"]
    for r in range(1, a.fill + 1):
        sid = f"fill{r}"
        S.append(Step(sid, f"補缺第 {r} 輪 fetch fill --apply", prev, [sm, "fetch", "fill", "--apply"], a.fill_sec, group="fill", skipif=r"要抓 0 ·|GATED|雙閘"))
        prev = [sid]
    S.append(Step("u014", "三代號宇宙 fetch run 014 --apply", prev, [sm, "fetch", "run", "014", "--apply"], 1800))
    S.append(Step("q_monitor", "族群監控(到齊 / 落後天數)", ["u014"],
                  [sm, "engine", "run", "MDL012", "monitor", "--groups", "TW_FIN,INTL_FIN,TW_PRICE_VOL,TW_ACTIVE_ETF,TW_INDEX,INTL_DAILY"], 1800))
    return S


def dag(a):
    via = Path(a.via).resolve(); out = Path(a.out); logs = out / "dag"; logs.mkdir(parents=True, exist_ok=True)
    plan = res_plan()
    say(f"[計] [CPU/DRAM] 核 {plan['logical']} · 可用 {plan['avail_mb']} / {plan['total_mb']} MB({plan['how']})· 並行槽 {plan['slots']} · {plan['why']}")
    S = build_dag(a, via); steps = {s.sid: s for s in S}
    t_start = time.time(); done = set(); running = {}; stopped_groups = set()
    lock = threading.Lock()
    progf = out / "A.progress"

    def prog(msg):
        try:
            pct = int(100 * len(done) / len(S))
            progf.write_text(f"{pct} · {msg}"[:160], encoding="utf-8")
        except OSError:
            pass

    with cf.ThreadPoolExecutor(max_workers=max(8, plan["slots"])) as ex:   # 相依圖最寬 6;重活的資源分配交給 ActivateVDF 自己的記憶體准入閘
        while len(done) < len(S):
            for s in S:
                if s.sid in done or s.sid in running:
                    continue
                if all(d in done for d in s.deps):
                    if s.group and s.group in stopped_groups:
                        s.lamp, s.note, s.t0 = "GRAY", "前一輪已達停止條件 → 略過", time.time(); s.t1 = s.t0
                        done.add(s.sid); say(f"[注] [DAG] {s.label} · {s.note}"); continue
                    say(f"[計] [DAG] ▶ {s.label}(+{int(time.time() - t_start)}s · 同時在跑 {len(running) + 1})")
                    running[s.sid] = ex.submit(run_step, s, via, logs, t_start, steps, prog)
            fin = [k for k, f in running.items() if f.done()]
            for k in fin:
                st = running.pop(k).result(); done.add(k)
                if st.after == "STOPGROUP" and st.group:
                    stopped_groups.add(st.group)
                tag = {"GREEN": "[OK]", "YELLOW": "[YEL]", "RED": "[RED]", "GRAY": "[注]"}[st.lamp]
                say(f"{tag} [DAG] {st.label} · rc {st.rc} · {st.t1 - st.t0:.0f}s · {st.lines} 行" + (f" · {st.note}" if st.note else ""))
                prog(f"✓ {st.label}")
            if not fin:
                time.sleep(0.5)
    wall = time.time() - t_start
    serial = sum((s.t1 or 0) - (s.t0 or 0) for s in S if s.kind == "run")
    say(f"[計] [DAG] 牆鐘 {wall:.0f}s · 各步加總(串行估計){serial:.0f}s · 省 {max(0, serial - wall):.0f}s"
        f"({(100 * (serial - wall) / serial) if serial else 0:.0f}%)")
    rows = [{"id": s.sid, "label": s.label, "deps": s.deps, "kind": s.kind, "rc": s.rc, "lamp": s.lamp, "note": s.note,
             "start": round((s.t0 or t_start) - t_start, 1), "end": round((s.t1 or t_start) - t_start, 1), "lines": s.lines} for s in S]
    pick = {}
    for sid, rx in (("q_info", r'"code_in"|"type"|"name"|"present"|"market"|"industry"'), ("q_members_fin", r"^\s*\w{2,6}\s*$"),
                    ("q_members_intl", r"^\s*\w{2,6}\s*$"), ("q_monitor", r"\|"), ("q_verify", r"[✓✗]"), ("q_starts", r"TW_|FIN|OTHER|MACRO")):
        f = logs / (sid + ".out")
        if f.exists():
            pick[sid] = [ln.rstrip() for ln in f.read_text(encoding="utf-8", errors="replace").splitlines() if re.search(rx, ln)][:60]
    doc = {"tool": TOOL, "at": now(), "via": str(via), "plan": plan, "wall": round(wall, 1), "serial": round(serial, 1), "steps": rows, "picks": pick}
    (out / "dag_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    covf = out / "cov_latest.json"
    covd = json.loads(covf.read_text(encoding="utf-8")) if covf.exists() else None
    html_out = out / "VIA_ListsFirstDAG_latest.html"
    html_out.write_text(render(doc, covd), encoding="utf-8")
    say(f"[計] [DAG] 報告 {html_out}")
    progf.write_text("100 · 完", encoding="utf-8")
    return 1 if any(s.lamp == "RED" for s in S) else (2 if any(s.lamp == "YELLOW" for s in S) else 0)


# ───────────────────────── html ─────────────────────────
def lamp(l):
    return f'<span class="lp {l}" title="{l}"></span>'


def render(doc, covd):
    e = html.escape
    css = """
:root{--bg:#f8fafc;--card:#fff;--line:#e2e8f0;--tx:#0f172a;--mu:#64748b;--g:%(GREEN)s;--y:%(YELLOW)s;--r:%(RED)s;--n:%(GRAY)s}
*{box-sizing:border-box}body{margin:0;padding:12px;background:var(--bg);color:var(--tx);font:11px/1.4 -apple-system,'Segoe UI','Microsoft JhengHei',Roboto,Arial,sans-serif}
h1{font-size:14px;margin:0 0 6px}h2{font-size:12px;margin:14px 0 6px}.mu{color:var(--mu)}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px;margin-bottom:10px;overflow-x:auto}
table{width:100%%;border-collapse:collapse;table-layout:fixed}th,td{border-bottom:1px solid var(--line);padding:3px 6px;text-align:left;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f1f5f9;font-weight:600}td.c,th.c{text-align:center}col.l{width:34px}
.lp{display:inline-block;width:12px;height:12px;border-radius:50%%;vertical-align:middle}.GREEN{background:var(--g)}.YELLOW{background:var(--y)}.GRAY{background:var(--n)}
.RED{background:var(--r);animation:bl 1.8s ease-in-out infinite}@keyframes bl{50%%{opacity:.25}}
.bar{position:relative;height:12px;background:#f1f5f9;border-radius:3px}.bar i{position:absolute;top:0;height:12px;border-radius:3px}
pre{white-space:pre-wrap;word-break:break-word;margin:0;font:10.5px/1.35 Consolas,'Cascadia Mono',monospace}
@media(max-width:700px){body{padding:6px}.hide-s{display:none}}
""" % PAL
    h = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>VDF 清單先行並行</title><style>{css}</style></head><body>"]
    p = doc["plan"]
    sp = doc["serial"] - doc["wall"]
    h.append(f"<h1>VDF 清單先行 → 相依圖並行扇出</h1><div class='mu'>{e(doc['at'])} · {e(TOOL)} · {e(doc['via'])}</div>")
    h.append(f"<div class='card'>CPU/DRAM:核 {p['logical']} · 可用 {p['avail_mb']} / {p['total_mb']} MB · 並行槽 <b>{p['slots']}</b> · {e(p['why'])}<br>"
             f"牆鐘 <b>{doc['wall']:.0f}s</b> · 各步加總(全串行估計){doc['serial']:.0f}s · 省 <b>{max(0, sp):.0f}s</b></div>")
    if covd:
        h.append("<h2>① 加速器 / 網路工具 AST 覆蓋 · 版本號 · VCGC 編號(五系統,各自的夾 · 尾版)</h2><div class='card'><table><colgroup><col class='l'><col style='width:60px'>"
                 "<col><col><col><col><col></colgroup><tr><th class='c'>燈</th><th>系統</th><th>尾版</th><th>AST 可解析</th><th>加速器橋</th><th>網路呼叫者有網路工具橋</th><th>VCGC 編號</th></tr>")
        for s in covd["systems"]:
            if not s.get("tails"):
                h.append(f"<tr><td class='c'>{lamp('GRAY')}</td><td>{e(s['system'])}</td><td colspan=5 class='mu'>{e(s.get('note', ''))}</td></tr>"); continue
            h.append(f"<tr><td class='c'>{lamp(s['lamp'])}</td><td><b>{e(s['system'])}</b></td><td>{s['tails']}</td><td>{s['parse']}/{s['tails']}</td>"
                     f"<td>{s['accel']}/{s['tails']}({s['accel_pct']}%)</td><td>{s['net_bridged']}/{s['net_callers']}({s['net_pct']}%)</td>"
                     f"<td>{s['numbered']}/{s['tails']}({s['num_pct']}%)</td></tr>")
        h.append("</table></div>")
        bad = [x for x in covd["rows"] if x["lamp"] != "GREEN"]
        h.append(f"<h2>② 不合 / 待號的尾版({len(bad)} 支;全表 cov_latest.csv)</h2><div class='card'><table><colgroup><col class='l'><col style='width:50px'><col><col style='width:60px'>"
                 "<col style='width:130px'><col></colgroup><tr><th class='c'>燈</th><th>系統</th><th>家族</th><th>版本</th><th>編號</th><th>原因</th></tr>")
        for x in sorted(bad, key=lambda r: (r["lamp"] != "RED", r["system"], r["family"]))[:400]:
            h.append(f"<tr><td class='c'>{lamp(x['lamp'])}</td><td>{e(x['system'])}</td><td>{e(x['family'])}</td><td>{e(x['version'])}</td>"
                     f"<td>{e(x['code'] or '待號')}</td><td>{e(x['why'])}</td></tr>")
        h.append("</table></div>")
    h.append("<h2>③ 相依圖時間軸(同一時間起跑的步驟 = 並行)</h2><div class='card'><table><colgroup><col class='l'><col style='width:34%'><col class='hide-s' style='width:16%'>"
             "<col style='width:60px'><col></colgroup><tr><th class='c'>燈</th><th>步驟</th><th class='hide-s'>等誰</th><th>秒</th><th>時間軸</th></tr>")
    W = max(1.0, doc["wall"])
    for s in doc["steps"]:
        l = 100 * s["start"] / W; w = max(0.8, 100 * (s["end"] - s["start"]) / W)
        h.append(f"<tr><td class='c'>{lamp(s['lamp'])}</td><td>{e(s['label'])}<div class='mu'>{e(' · '.join(x for x in (s['note'] or '', ('rc ' + str(s['rc'])) if s['rc'] is not None else '') if x))}</div></td>"
                 f"<td class='hide-s mu'>{e(', '.join(s['deps']) or '—')}</td><td>{s['end'] - s['start']:.0f}</td>"
                 f"<td><div class='bar'><i class='{s['lamp']}' style='left:{l:.1f}%;width:{w:.1f}%'></i></div></td></tr>")
    h.append("</table></div><h2>④ 個別項目 3017 · 3324 · NVDA(另查 3334)與族群到齊</h2>")
    names = {"q_info": "三代號 info", "q_members_fin": "成員 TW_FIN", "q_members_intl": "成員 INTL_FIN", "q_monitor": "族群監控", "q_verify": "清單驗收", "q_starts": "起始日現況"}
    for k, v in doc["picks"].items():
        h.append(f"<div class='card'><b>{e(names.get(k, k))}</b><pre>{e(chr(10).join(v) or '(無輸出)')}</pre></div>")
    h.append("<div class='mu'>燈:綠 = 通過 · 黃 = 沒資料 / 等同意閘 / 待號 · 紅 = 失敗(慢閃)· 灰 = 未跑 / 略過。本頁只讀、不連網、不需伺服器。</div></body></html>")
    return "".join(h)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="VIA_ListsFirstDAG")
    sub = ap.add_subparsers(dest="verb", required=True)
    r = sub.add_parser("res")
    c = sub.add_parser("cov"); c.add_argument("--via", required=True); c.add_argument("--out", required=True); c.add_argument("--systems", default="")
    d = sub.add_parser("dag"); d.add_argument("--via", required=True); d.add_argument("--out", required=True)
    d.add_argument("--sm", required=True); d.add_argument("--act", required=True); d.add_argument("--start", default="2022-01-02")
    d.add_argument("--cats", default="TW_MARKET,FIN,OTHER"); d.add_argument("--fill", type=int, default=2); d.add_argument("--act-args", default=""); d.add_argument("--act-sec", type=int, default=10800); d.add_argument("--fill-sec", type=int, default=3600)
    a = ap.parse_args(argv)
    if a.verb == "res":
        say(json.dumps(res_plan(), ensure_ascii=False)); return 0
    if a.verb == "cov":
        doc = cov(Path(a.via).resolve(), Path(a.out), [x for x in a.systems.split(",") if x] or None)
        lamps = [s["lamp"] for s in doc["systems"]]
        return 1 if "RED" in lamps else (2 if "YELLOW" in lamps else 0)
    a.cats = [x for x in a.cats.split(",") if x]
    a.act_args = [x for x in a.act_args.split() if x]
    return dag(a)


if __name__ == "__main__":
    sys.exit(main())
'@ | Set-Content -LiteralPath $DagPy -Encoding UTF8
$script:Verdicts.Add("[相依圖] 輔助檔 $DagPy(只讀他系統 · 只經 VDF 自己的入口跑 VDF)")

# ---------- C0 五系統 AST 覆蓋(主執行緒,先於兩道)----------
$covArgs = @($DagPy, 'cov', '--via', $WtVia, '--out', $LogDir); if ("$env:VIA_COV_SYSTEMS") { $covArgs += @('--systems', "$env:VIA_COV_SYSTEMS") }
$e0 = $script:Errors.Count; $cov = @(Invoke-VCPython -Id 'C0_cov' -Argv $covArgs -Sec 900)
for ($j = $script:Errors.Count - 1; $j -ge $e0; $j--) { if ($script:Errors[$j] -like '[[]C0_cov] rc 1 *') { $script:Errors.RemoveAt($j) } }
foreach ($ln in $cov) { $t = "$ln".Trim(); if (-not $t) { continue }
  if ($t -match '^\[RED\]') { $script:Errors.Add($t) } elseif ($t -match '^\[(OK|YEL|計|注)\]') { $script:Verdicts.Add($t) } }

# ---------- 道 A / 道 B ----------
$LaneRun = { param($WtVia, $LogDir, $Id, $Plan)
  Set-Location -LiteralPath $WtVia; $prog = Join-Path $LogDir ($Id + '.progress'); $i = 0
  foreach ($s in $Plan) { $i++
    $sa = @($s.a); $what = "" + $s.label
    if (-not $s.inner) { Set-Content -LiteralPath $prog ("" + [int](($i - 1) * 100 / $Plan.Count) + " · " + $what) -Encoding UTF8 }
    if (-not (Test-Path -LiteralPath $s.file)) { "[GRAY] $what · 檔不在 → 未跑"; continue }
    $json = ConvertTo-Json -InputObject @(@($s.file) + $sa) -Compress; $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
    $wrap = "import base64,json,os,sys,threading,runpy; a=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); t=threading.Timer($([int]$s.sec), lambda: (sys.stdout.flush(), os._exit(124))); t.daemon=True; t.start(); sys.argv=a; runpy.run_path(a[0], run_name='__main__')"
    $global:LASTEXITCODE = $null; $t0 = Get-Date
    $o = @(& python -c $wrap $b64 2>&1 | ForEach-Object { "" + $_ }); $rc = $global:LASTEXITCODE
    $dt = [int]((Get-Date) - $t0).TotalSeconds; $o | Set-Content -LiteralPath (Join-Path $LogDir ($s.n + '.out')) -Encoding UTF8
    $lamp = if ($null -eq $rc) { 'NOTE' } elseif ($rc -eq 0) { 'GREEN' } elseif ($rc -in 2, 3, 4) { 'YELLOW' } else { 'RED' }
    $why = if ($null -ne $rc) { @{ 1 = '有紅步(見相依圖時間軸)'; 2 = '黃 / 沒資料'; 3 = '缺件'; 4 = '等同意閘'; 124 = '逾時' }[[int]$rc] } else { $null }
    $tag = @{ GREEN = '[OK]'; YELLOW = '[YEL]'; RED = '[RED]'; NOTE = '[注]' }[$lamp]
    ($tag + ' ' + $what + ' · rc ' + $(if ($null -eq $rc) { '未回' } else { "$rc" }) + $(if ($why) { "($why)" } else { '' }) + ' · ' + $dt + 's · ' + $o.Count + ' 行') }
  Set-Content -LiteralPath $prog '100 · 完' -Encoding UTF8 }

$SmF = if ($Sm) { $Sm.FullName } else { Join-Path $VdfDir 'VDF_SystemManager_v0000.py' }
$PlanA = @(@{ n = 'A_dag'; file = $DagPy; inner = $true; sec = 25200; label = 'VDF 相依圖並行(輸入 → ActivateVDF ∥ 清單落地即起 info · 驗收 → 補缺 → 014 → 監控)'
    a = @('dag', '--via', $WtVia, '--out', $LogDir, '--sm', $SmF, '--act', $Act, '--start', $StartDay, '--cats', ($Cats -join ','), '--fill', "$FillRounds", '--act-sec', $(if ("$env:VIA_VDF_ACT_SEC") { "$env:VIA_VDF_ACT_SEC" } else { '10800' }), '--fill-sec', $(if ("$env:VIA_VDF_FILL_SEC") { "$env:VIA_VDF_FILL_SEC" } else { '3600' }), '--act-args', ("$env:VIA_VDF_ACT_ARGS").Trim()) })
$PlanB = @(
  @{ n = 'B1_version'; file = $SmF; a = @('version'); sec = 300; label = 'VDF_SystemManager version' },
  @{ n = 'B2_bridges'; file = $SmF; a = @('bridges'); sec = 900; label = 'VDF bridges(管理器自報:加速器 · 網路工具)' },
  @{ n = 'B3_number'; file = $SmF; a = @('number'); sec = 900; label = 'VDF number(VCGC 編號同步)' },
  @{ n = 'B4_health'; file = $SmF; a = @('health'); sec = 900; label = 'VDF health' })
$Lanes = @(
  @{ id = 'A'; zh = 'VDF 相依圖'; args = @($WtVia, $LogDir, 'A', $PlanA); run = $LaneRun },
  @{ id = 'B'; zh = '唯讀檢查'; args = @($WtVia, $LogDir, 'B', $PlanB); run = $LaneRun })
Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir

foreach ($k in @('A', 'B')) { $lg = Join-Path $LogDir ($k + '.log')
  if ((Test-Path -LiteralPath $lg) -and $script:LaneState.Contains($k)) { $yl = @(Get-Content -LiteralPath $lg -Encoding UTF8 | Where-Object { $_ -match '^\s*\[(YEL|注|GRAY)\]' })
    foreach ($y in $yl) { $script:Verdicts.Add("[$k] " + $y.Trim()) }; if (@($yl | Where-Object { $_ -match '^\s*\[(YEL|GRAY)\]' }).Count -and $script:LaneState[$k].lamp -eq 'GREEN') { $script:LaneState[$k].lamp = 'YELLOW' } } }

# ---------- 判決行:相依圖每步一行 · 個別項目 · 道 B ----------
$of = Join-Path $LogDir 'A_dag.out'
if (Test-Path -LiteralPath $of) { foreach ($ln in @(Get-Content -LiteralPath $of -Encoding UTF8)) { $t = "$ln".Trim()
    if ($t -match '^\[RED\]|Traceback') { if ($script:Errors.Count -lt 60) { $script:Errors.Add("[A] $t") } }
    elseif ($t -match '^\[(OK|YEL|注|計)\]' -and $t -notmatch '\] ▶ ') { $script:Verdicts.Add("[A] $t") } } }
$dd = Join-Path $LogDir 'dag'
foreach ($p in @(@('in_apply', '^\[(現況|寫|略過)\]'), @('q_info', '"code_in"|"type"|"name"|"present"'), @('q_members_fin', '^\s*\d{4}\s*$|^\[TW_FIN\]'), @('q_members_intl', '^\s*[A-Z]{1,5}\s*$|^\[INTL_FIN\]'), @('q_monitor', '^\s*(TW_FIN|INTL_FIN|TW_PRICE_VOL|TW_ACTIVE_ETF|TW_INDEX|INTL_DAILY) \|'), @('q_verify', '[✓✗]'))) {
  $f = Join-Path $dd ($p[0] + '.out'); if (-not (Test-Path -LiteralPath $f)) { continue }
  foreach ($ln in @(Get-Content -LiteralPath $f -Encoding UTF8 | Where-Object { $_ -match $p[1] } | Select-Object -First 24)) { $t = "$ln".Trim(); if ($t.Length -gt 220) { $t = $t.Substring(0, 220) }; if ($script:Verdicts.Count -lt 280) { $script:Verdicts.Add("[$($p[0])] $t") } } }
foreach ($n in @('B1_version', 'B2_bridges', 'B3_number', 'B4_health')) { $f = Join-Path $LogDir ($n + '.out'); if (Test-Path -LiteralPath $f) { $t = "" + (@(Get-Content -LiteralPath $f -Encoding UTF8 | Where-Object { "$_".Trim() }) | Select-Object -Last 1); if ($t.Length -gt 220) { $t = $t.Substring(0, 220) }; $script:Verdicts.Add("[$n] " + $t.Trim()) } }


# ---------- 輸出檢視(只認本輪寫的檔) ----------
$OpenLater = [System.Collections.Generic.List[string]]::new()
$Review = { param($label, $path)
  if (-not (Test-Path -LiteralPath $path)) { $script:Verdicts.Add("[輸出] $label 不在:$path(黃)"); return }
  $it = Get-Item -LiteralPath $path; $fresh = ($it.LastWriteTime -ge $StartAt); $extra = ''
  if ($it.Extension -eq '.json' -and $it.Length -lt 20MB) { try { $j = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
      $extra = (@($j.PSObject.Properties | Where-Object { $_.Name -match '^(lamp|verdict|state|status|line|count|date|built_at|version)$' -and $_.Value -isnot [array] -and $_.Value -isnot [pscustomobject] } | ForEach-Object { $v = "$($_.Value)"; if ($v.Length -gt 80) { $v = $v.Substring(0, 80) }; $_.Name + '=' + $v }) -join ' · ') } catch { $extra = 'JSON 讀不進來' } }
  $script:Verdicts.Add("[輸出] $label · " + $(if ($fresh) { '本輪寫的' } else { '不是本輪寫的(舊檔)' }) + " · " + $it.LastWriteTime.ToString('MM-dd HH:mm') + " · $([int]($it.Length / 1KB)) KB" + $(if ($extra) { " · $extra" } else { '' }))
  if ($fresh -and $it.Extension -eq '.html') { $OpenLater.Add($path) } }
& $Review '相依圖時間軸 + 五系統覆蓋頁' (Join-Path $LogDir 'VIA_ListsFirstDAG_latest.html')
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
