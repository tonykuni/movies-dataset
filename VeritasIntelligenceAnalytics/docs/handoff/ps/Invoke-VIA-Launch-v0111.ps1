# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Uri = '', [switch]$RegisterProtocol, [string]$Sub = 'VDF', [string]$Verb = 'ui', [string[]]$VerbArgs = @(), [int]$MaxMin = 60, [int]$KeepRuns = 5, [double]$MaxTempGB = 2.0, [double]$LowRamGB = 2.0, [int]$PyStepSec = 120, [string]$Title = 'VIA 任務', [switch]$NoCleanup, [switch]$KillOrphans, [switch]$NoOpen, [switch]$Demo)
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

# ======================= 骨架主體(通用啟動器:L117 所有指令 PY 化導入加速器,PS 只啟動與連結 U/I;本支 = 唯一要留的 PS 形狀:落地 → 加速器 → 跑一個 python 動詞 → 開 U/I)=======================
# Invoke-VIA-Launch-v0111.ps1(薄尾:L119 入口各自律入冊 · 結算行改「三系統各自入口;-Sub VIA 只是母系統監控視圖」;v0110 不動;含 VIA_NO_OPEN 只給車道 python,車道尾與開頁前清掉 → 子系統頁真的跳出;v0109 不動;含 VRN v0147 annual 收據遞迴 · VDF 載 v0147 · 「樹上已有更高版」改提醒不算紅;v0108 不動;含 VRN annual 動詞 — 年度財報交接包接入不搬檔;v0107 不動;含 -Sub VIA 入口模式 = 三系統各自 ui 自報清單 → VCGC portal 一頁連三個 manager;v0106 不動;亦含 v0105 L118 滑鼠律 — via:// 協定 -RegisterProtocol · -Uri 解析 · pick=1 檔案選取器 · dir=1 夾選取器;v0104 不動)· 操作員令 2026-10-06:左面板輸入介面 · 右面板多頁展示頁面
#   用法:-Sub VDF -Verb ui · -Sub VRN -Verb panorama · -Sub VRN -Verb extract -VerbArgs @('--limit','20') · -Sub VCGC -Verb matrix
# ---------- L118 滑鼠律:via:// 協定(頁上按鈕 = 連結;Windows 交給本支;不起 server)----------
if ($RegisterProtocol) {
  $self = $MyInvocation.MyCommand.Path; $pw = (Get-Command pwsh).Source
  $k = 'HKCU:\Software\Classes\via'
  New-Item -Path $k -Force | Out-Null; Set-ItemProperty -Path $k -Name '(default)' -Value 'URL:VIA Launcher'; Set-ItemProperty -Path $k -Name 'URL Protocol' -Value ''
  New-Item -Path "$k\shell\open\command" -Force | Out-Null
  Set-ItemProperty -Path "$k\shell\open\command" -Name '(default)' -Value ('"' + $pw + '" -NoProfile -ExecutionPolicy Bypass -File "' + $self + '" -Uri "%1"')
  Write-Host ("[協定] via:// → " + $self + "(HKCU 只動自己;移除:Remove-Item HKCU:\Software\Classes\via -Recurse)") -ForegroundColor Yellow
  return }
Add-Type -AssemblyName System.Web -ErrorAction SilentlyContinue
if ($Uri) {
  # via://SUB/VERB?args=--limit+20&pick=1   pick=1 = 開 Windows 檔案選取器(滑鼠),選到的路徑接在參數後
  $u = [uri]$Uri; $Sub = $u.Host.ToUpperInvariant(); $Verb = ($u.AbsolutePath.Trim('/') -replace '/', ' ')
  $q = [System.Web.HttpUtility]::ParseQueryString($u.Query)
  $VerbArgs = @(); if ($q['args']) { $VerbArgs = @(($q['args'] -split '[ +]') | Where-Object { $_ }) }
  if ($q['pick'] -eq '1') { Add-Type -AssemblyName System.Windows.Forms; $dlg = New-Object System.Windows.Forms.OpenFileDialog; $dlg.Multiselect = $true; $dlg.Title = "VIA $Sub $Verb — 選檔(滑鼠)"; if ($dlg.ShowDialog() -eq 'OK') { $VerbArgs += $dlg.FileNames } else { return } }
  if ($q['dir'] -eq '1') { Add-Type -AssemblyName System.Windows.Forms; $fd = New-Object System.Windows.Forms.FolderBrowserDialog; if ($fd.ShowDialog() -eq 'OK') { $VerbArgs += $fd.SelectedPath } else { return } } }
if (-not $NoCleanup) { Invoke-VCSafeCleanup }
$Run = Initialize-VCTemp; Initialize-VCAccel
$script:LogDir = Join-Path $VIA ("VIA_Reports\review\ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null; $LogDir = $script:LogDir
$RegDir = Join-Path $VIA 'supportive modules\registry'; $VdfDir = Join-Path $VIA 'functional modules\VDF'
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
  if ($t -and $t.Name -gt $me) { $script:Verdicts.Add("[落地] 樹上已有 $($t.Name) 高於 $Ver → $Tag 不落地(正常:尾版更新)"); return $true }
  return (Install-VIAEmbedded -Path (Join-Path $Dir $me) -B64 $B64 -Want $Sha -Tag $Tag) }
# ---------- 一次性落地(已在且 hash 同 → SKIP;之後本支只剩啟動) ----------
$B64Skel = @'
IyBDRUxFUklUQVMtVEVNUExBVEUtSk9JTiB2MQ0KI1JlcXVpcmVzIC1WZXJzaW9uIDcuMA0KW0NtZGxldEJpbmRpbmcoKV0NCnBhcmFtKFtpbnRdJE1heE1p
biA9IDYwLCBbaW50XSRLZWVwUnVucyA9IDUsIFtkb3VibGVdJE1heFRlbXBHQiA9IDIuMCwgW2RvdWJsZV0kTG93UmFtR0IgPSAyLjAsIFtpbnRdJFB5U3Rl
cFNlYyA9IDEyMCwgW3N0cmluZ10kVGl0bGUgPSAnVklBIOS7u+WLmScsIFtzd2l0Y2hdJE5vQ2xlYW51cCwgW3N3aXRjaF0kS2lsbE9ycGhhbnMsIFtzd2l0
Y2hdJE5vT3BlbiwgW3N3aXRjaF0kRGVtbykNCiMgQUkg55Si5Ye65b+F6aCI5o6l5YWl5qih5p2/44CC5Y+q5YuVICRQSUQs6Zec6ZaJ5Y2z6YKE5Y6f44CC
TDEwNjpQUyDluLblhannq6DjgIINCiMgPT09PT0gW1ZJQTpQUy1BQ0NFTDp2MDEwMV0gUFMgMjUg5Yqg6YCf5Zmo5qmLKEI1MzEg5YWo5qi55bCO5YWlO2dy
YWNlZnVsIOe8uuW4rembtuW9semfvykgPT09PT0NCnRyeSB7ICRWSUFQU0FjY2VsUHJvYmUgPSBpZiAoJFBTU2NyaXB0Um9vdCkgeyAkUFNTY3JpcHRSb290
IH0gZWxzZSB7ICdDOlxVc2Vyc1x0b255a1xPbmVEcml2ZVxEb2N1bWVudHNcbW92aWVzLWRhdGFzZXRcVmVyaXRhc0ludGVsbGlnZW5jZUFuYWx5dGljcycg
fQ0KICB3aGlsZSAoJFZJQVBTQWNjZWxQcm9iZSAtYW5kIChTcGxpdC1QYXRoICRWSUFQU0FjY2VsUHJvYmUgLVBhcmVudCkpIHsgJG0gPSBKb2luLVBhdGgg
JFZJQVBTQWNjZWxQcm9iZSAic3VwcG9ydGl2ZSBtb2R1bGVzXFZJQV9QU19BY2NlbF9Nb2R1bGUucHMxIjsgaWYgKFRlc3QtUGF0aCAkbSkgeyAuICRtOyBi
cmVhayB9OyAkVklBUFNBY2NlbFByb2JlID0gU3BsaXQtUGF0aCAkVklBUFNBY2NlbFByb2JlIC1QYXJlbnQgfSB9IGNhdGNoIHsgfQ0KIyA9PT09PSBbVklB
OlBTLUFDQ0VMOkVORF0gPT09PT0NCiMgVmVyaXRhc0NlbGVyaXRhcy5QUzcuU2tlbGV0b24gdjAxMDkg4oCUIOiQrOeUqCBQUyDliqDpgJ/mqKHmnb8gwrcg
YWxsLWluLW9uZSh2MDEwOCDkuInlkIjkuIAgKyDpoqjpmqrmlLbmloI65a2k5YWS5LiN6aCQ6Kit5q66IMK3IFRFTVAg5Y+q5riFIDIg5bCP5pmC5YmN5LiU
54Sh5Lq655SoIMK3IOeSsOWig+iuiuaVuOmAgOWHuumChOWOnyDCtyBweXRob24g55yL6ZaA54uX5YWI5p+U5b6M56GsKQ0KIyAgIOWJjeauteWbuuWumjri
kaAg5a6J5YWo5riF55CGKOWPquWLleacrOihjOeoiynikaEgVEVNUCDngrrkuLvoqJjmhrbpq5Qg4pGiIOWKoOmAn+WZqChBdXRvSW1wb3J0IOWcqCBzdXBw
b3J0aXZlIG1vZHVsZXMg5Lu75L2V5a2Q5aS+6YO95om+5b6X5YiwKQ0KIyAgIOS4reautTrikaMg6ZuZ6LuMKOaIluWkmui7jCnkuKbooYwgKyAqKuS4u+aO
p+WPsOefqemZo+ahhuWOn+WcsOWIt+aWsCoqKFBhZC1WaXN1YWwg5Lit5paH5bCN6b2KIMK3IOavj+mBk+S4gOWIlzrpoIXnm64g4pSCIOmAsuW6puaineKW
tiDilIIg54uA5oWL6IiH57Sw56+AO+a4uOaomeS4iuenu+mHjee5qizkuI3mtJfniYgpIOKRpCBJbnZva2UtVkNQeXRob246UFMg4oaSIHB5dGhvbiDkuI3m
nIPljaHnmoTpgJrpgZMo55u05ZG8IMK3IGJhc2U2NCBhcmd2IMK3IHB5dGhvbiDlhafnnIvploDni5cgMTI0KQ0KIyAgIOaUtuWwvjrikaUg6buD5a2X6LK8
IEFJIMK3IOe0heWtl+mMr+iqpCjpgLLliarosrznsL8p4pGmIOmdnOaFiyBIVE1MIFUvSSDnm7TmjqXot7Plh7ooZmlsZTovLyzkuI3ntpPkvLrmnI3lmag7
Rm9ybWF0TG9jayDlm5vnh4ggwrcg57SF54eI5oWi6ZaDIMK3IOmbu+iFpi/miYvmqZ/oh6rpganmh4kpDQojICAgdjAxMTAoMjAyNi0xMC0wNik64pGhIFRF
TVAg5b6LIEwxMTUo5Y+q5riF6Ieq5a62IHBzXyogwrcg57i96YeP5LiK6ZmQIC1NYXhUZW1wR0Ig6aCQ6KitIDIgwrcg5L2OIFJBTSAtTG93UmFtR0Ig6aCQ
6KitIDIg6Ieq5YuVIFZJQV9MT1dfUkFNPTEgKyBWSUFfU1BJTExfRElSIMK3IFJVTk5JTkcg6Y6WIMK3IOS4gOihjOW4s+WQqyBieXRlcy9SQU0pwrcg4pGj
IOWjnuihjOWIhumhnuWZqCBbT0tdL1voqIhdIOS4jeeVtue0hSDCtyDikaQgcHl0aG9uIOeci+mWgOeLlyBUaW1lciBkYWVtb249VHJ1ZSjlkKbliYfmr4/m
rKHnrYnmu78gU2VjIOWbniAxMjQpDQojICAgdjAxMTEoMjAyNi0xMC0wNik64pGiIOWKoOmAn+WZqOW+jOaPtDpBdXRvSW1wb3J0IOS4jeWcqCDihpIg6bue
IHN1cHBvcnRpdmUgbW9kdWxlc1xwczdcVmVyaXRhc0NlbGVyaXRhcy5QUzcucHMxKDMwIOWKoOmAn+WZqCxTdGFydC1DZWxlcml0YXNQUzcg6Ieq5YuV5aWX
55SoKeWGjSBTZXQtU3RyaWN0TW9kZSAtT2ZmKOWug+eahCBMYXRlc3Qg5LiN5aSW5rqiKTvpgIDlh7ogUmVzdG9yZS1DZWxlcml0YXNQUzcNCiMgICB2MDEx
MigyMDI2LTEwLTA2KTrikagg5ZWf5YuV5Zmo5q61IEludm9rZS1WQ0xhdW5jaChMMTE3OuaJgOacieaMh+S7pCBQWSDljJbkuKblsI7lhaXliqDpgJ/lmag7
UFMg5Y+q5YGa5ZWf5YuV6IiH6YCj57WQIFUvSSnigJTmib7lrZDns7vntbHlsL7niYggbWFuYWdlciDihpIgSW52b2tlLVZDUHl0aG9uIOi3keS4gOWAi+WL
leipniDihpIg5b6e6Ly45Ye65oqTIC5odG1sIOi3r+W+kSDihpIg6ZaL54CP6Ka95ZmoO1BTIOacrOi6q+S4jeWQq+alreWLmemCj+i8rw0KIyAgIOeUqOaz
lTropIfoo73mlLnlkI0g4oaSIOWPquaUueacgOW6leS4i+OAjOmqqOaetuS4u+mrlOOAjeeahCAkTGFuZXM75YW26aSY5LiN5YuV44CCLURlbW8g6LeR56S6
56+E5YWp6YGT44CCDQokRXJyb3JBY3Rpb25QcmVmZXJlbmNlID0gJ0NvbnRpbnVlJw0KJFZJQSA9IGlmICgkUFNTY3JpcHRSb290IC1hbmQgKFRlc3QtUGF0
aCAoSm9pbi1QYXRoICRQU1NjcmlwdFJvb3QgJ3N1cHBvcnRpdmUgbW9kdWxlcycpKSkgeyAkUFNTY3JpcHRSb290IH0gZWxzZSB7ICdDOlxVc2Vyc1x0b255
a1xPbmVEcml2ZVxEb2N1bWVudHNcbW92aWVzLWRhdGFzZXRcVmVyaXRhc0ludGVsbGlnZW5jZUFuYWx5dGljcycgfQ0KU2V0LUxvY2F0aW9uIC1MaXRlcmFs
UGF0aCAkVklBOyAkZW52OlBZVEhPTlVURjggPSAnMSc7ICRlbnY6UFlUSE9OV0FSTklOR1MgPSAnaWdub3JlJzsgJGVudjpWSUFfTk9fT1BFTiA9ICcxJzsg
JGVudjpWSUFfUEFOT1JBTUFfQVVUTyA9ICcwJzsgJGVudjpWSUFfRlJPTV9WQ0dDID0gJ1lFUycNCiRzY3JpcHQ6U3RhbXAgPSBHZXQtRGF0ZSAtRm9ybWF0
IHl5eXlNTWRkX0hIbW1zczsgJHNjcmlwdDpFcnJvcnMgPSBbU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuTGlzdFtzdHJpbmddXTo6bmV3KCk7ICRzY3Jp
cHQ6VmVyZGljdHMgPSBbU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuTGlzdFtzdHJpbmddXTo6bmV3KCk7ICRzY3JpcHQ6TGFuZVN0YXRlID0gW29yZGVy
ZWRdQHt9OyAkc2NyaXB0OlRpbWVsaW5lID0gW1N5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3Rbb2JqZWN0XV06Om5ldygpDQokc2NyaXB0OlBBTCA9
IEB7IEdSRUVOID0gJyMxNmEzNGEnOyBZRUxMT1cgPSAnI2Y1OWUwYic7IFJFRCA9ICcjZGMyNjI2JzsgR1JBWSA9ICcjOWNhM2FmJzsgTk9EQVRBID0gJyMw
ODkxYjInIH0NCiRzY3JpcHQ6RXNjID0gW2NoYXJdMjc7ICRzY3JpcHQ6QyA9IEB7IEdyZXkgPSAiJChbY2hhcl0yNylbOTBtIjsgUmVkID0gIiQoW2NoYXJd
MjcpWzkxbSI7IEdyZWVuID0gIiQoW2NoYXJdMjcpWzkybSI7IFllbGxvdyA9ICIkKFtjaGFyXTI3KVs5M20iOyBDeWFuID0gIiQoW2NoYXJdMjcpWzk2bSI7
IFJlc2V0ID0gIiQoW2NoYXJdMjcpWzBtIjsgQm9sZCA9ICIkKFtjaGFyXTI3KVsxbSIgfQ0KJHNjcmlwdDpWVCA9ICRIb3N0LlVJLlN1cHBvcnRzVmlydHVh
bFRlcm1pbmFsIC1hbmQgLW5vdCAkZW52OlZJQV9OT19WVA0KZnVuY3Rpb24gUGFkLVZpc3VhbChbc3RyaW5nXSRTdHJpbmcsIFtpbnRdJFdpZHRoLCBbc3Ry
aW5nXSRBbGlnbm1lbnQgPSAnTGVmdCcpIHsgICAjIOimluimuuWvrOW6puijnOatozrljrsgQU5TSSDlvowsQ0pLIOeulyAyIOagvDvotoXlr6zlsLHmiKoo
5L+d55WZIEFOU0kg6YeN572uKQ0KICAkY2xlYW4gPSAkU3RyaW5nIC1yZXBsYWNlICIkKFtjaGFyXTI3KVxbWzAtOTtdKm0iLCAnJzsgJHcgPSAwOyAkY3V0
ID0gJyc7ICRvdmVyID0gJGZhbHNlDQogIGZvcmVhY2ggKCRjaCBpbiAkY2xlYW4uVG9DaGFyQXJyYXkoKSkgeyAkY3cgPSBpZiAoW2ludF0kY2ggLWd0IDI1
NSkgeyAyIH0gZWxzZSB7IDEgfTsgaWYgKCR3ICsgJGN3IC1ndCAkV2lkdGgpIHsgJG92ZXIgPSAkdHJ1ZTsgYnJlYWsgfTsgJHcgKz0gJGN3OyAkY3V0ICs9
ICRjaCB9DQogIGlmICgkb3ZlcikgeyByZXR1cm4gJGN1dCArICgnICcgKiAoJFdpZHRoIC0gJHcpKSB9ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAjIOaIquaWt+eJiOacrOS4jeW4tuiJsijpgb/lhY3mrpjnlZkgQU5TSSkNCiAgJHBhZCA9ICcgJyAqICgkV2lkdGggLSAkdyk7IGlmICgkQWxpZ25t
ZW50IC1lcSAnUmlnaHQnKSB7IHJldHVybiAkcGFkICsgJFN0cmluZyB9IGVsc2UgeyByZXR1cm4gJFN0cmluZyArICRwYWQgfSB9DQpmdW5jdGlvbiBHZXQt
VkNCYXIoW2ludF0kcGN0LCBbaW50XSR3aWR0aCA9IDIwLCBbc3RyaW5nXSRsYW1wID0gJ0dSRUVOJykgew0KICAkY29sID0gc3dpdGNoICgkbGFtcCkgeyAn
UkVEJyB7ICRzY3JpcHQ6Qy5SZWQgfSAnWUVMTE9XJyB7ICRzY3JpcHQ6Qy5ZZWxsb3cgfSAnR1JBWScgeyAkc2NyaXB0OkMuR3JleSB9IGRlZmF1bHQgeyAk
c2NyaXB0OkMuR3JlZW4gfSB9DQogICRmID0gW01hdGhdOjpSb3VuZCgkcGN0IC8gMTAwICogJHdpZHRoKTsgJGUgPSAkd2lkdGggLSAkZjsgJHNwYXJrID0g
aWYgKCRwY3QgLWx0IDEwMCAtYW5kICRmIC1ndCAwKSB7ICIkKCRzY3JpcHQ6Qy5ZZWxsb3cp4pa2JGNvbCIgfSBlbHNlIHsgJycgfQ0KICAkYmFyID0gKCfi
lognICogW01hdGhdOjpNYXgoMCwgJGYgLSAxKSkgKyAkc3BhcmsgKyAkKGlmICgkZiAtZ3QgMCAtYW5kICRwY3QgLWdlIDEwMCkgeyAn4paIJyB9IGVsc2Ug
eyAnJyB9KSArICgn4paRJyAqICRlKQ0KICByZXR1cm4gIiRjb2wkYmFyJCgkc2NyaXB0OkMuUmVzZXQpICIgKyAoUGFkLVZpc3VhbCAoIiRwY3QlIikgNCAn
UmlnaHQnKSB9DQpmdW5jdGlvbiBXcml0ZS1WQ0JveEZyYW1lKFtpbnRdJHJvd3MpIHsgICAjIOWbuuWumuWkluahhjrpoIXnm64gMjAg4pSCIOmAsuW6piA0
MCDilIIg54uA5oWL6IiH57Sw56+AIDM4O+mgkOeVmSByb3dzIOWIlyzkuYvlvozljp/lnLDph43nuaoNCiAgJGcgPSAkc2NyaXB0OkMuR3JleTsgJHogPSAk
c2NyaXB0OkMuUmVzZXQNCiAgV3JpdGUtSG9zdCAiJHtnfeKUjOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUrOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUrOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUkCR6
Ig0KICBXcml0ZS1Ib3N0ICIke2d94pSCJHogIiArIChQYWQtVmlzdWFsICfnlbbliY3ln7fooYzpoIXnm64nIDIwKSArICIgJHtnfeKUgiR6ICIgKyAoUGFk
LVZpc3VhbCAn6YCy5bqm5YuV55Wr6IiH55m+5YiG5q+UJyA0MCkgKyAiICR7Z33ilIIkeiAiICsgKFBhZC1WaXN1YWwgJ+eLgOaFi+iIh+WEquWMlue0sOev
gCcgMzgpICsgIiAke2d94pSCJHoiDQogIFdyaXRlLUhvc3QgIiR7Z33ilJzilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilLzilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilLzilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilKQkeiINCiAgZm9yICgkaSA9IDA7ICRpIC1sdCAkcm93czsgJGkrKykgeyBXcml0ZS1Ib3N0ICIke2d94pSCJHogIiArICgnICcgKiAyMCkgKyAiICR7
Z33ilIIkeiAiICsgKCcgJyAqIDQwKSArICIgJHtnfeKUgiR6ICIgKyAoJyAnICogMzgpICsgIiAke2d94pSCJHoiIH0NCiAgV3JpdGUtSG9zdCAiJHtnfeKU
lOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUtOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUtOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUmCR6IiB9DQpmdW5jdGlvbiBVcGRhdGUtVkNCb3goW29iamVjdFtd
XSRsaW5lcykgeyAgICMgbGluZXMgPSBAKEB7bmFtZTtwY3Q7bGFtcDtzdGF0dXM7ZGV0YWlsfSkgO+a4uOaomeS4iuenuyByb3dzKzEg6KGM5Y6f5Zyw6YeN
57mqKFZUIOS4jeaUr+aPtOWwseWPquWNsOS4gOasoSkNCiAgJGcgPSAkc2NyaXB0OkMuR3JleTsgJHogPSAkc2NyaXB0OkMuUmVzZXQ7ICRuID0gJGxpbmVz
LkNvdW50DQogIGlmICgkc2NyaXB0OlZUKSB7IFdyaXRlLUhvc3QgKCIkKCRzY3JpcHQ6RXNjKVsiICsgKCRuICsgMSkgKyAiQSIpIC1Ob05ld2xpbmUgfQ0K
ICBmb3JlYWNoICgkTCBpbiAkbGluZXMpIHsgJGNvbCA9IHN3aXRjaCAoJEwubGFtcCkgeyAnUkVEJyB7ICRzY3JpcHQ6Qy5SZWQgfSAnWUVMTE9XJyB7ICRz
Y3JpcHQ6Qy5ZZWxsb3cgfSAnR1JFRU4nIHsgJHNjcmlwdDpDLkdyZWVuIH0gZGVmYXVsdCB7ICRzY3JpcHQ6Qy5HcmV5IH0gfQ0KICAgICRjMSA9IFBhZC1W
aXN1YWwgJEwubmFtZSAyMDsgJGMyID0gUGFkLVZpc3VhbCAoR2V0LVZDQmFyICRMLnBjdCAyMCAkTC5sYW1wKSA0MDsgJGMzID0gUGFkLVZpc3VhbCAoIiRj
b2xbIiArICRMLnN0YXR1cyArICJdJHogIiArICRMLmRldGFpbCkgMzgNCiAgICBXcml0ZS1Ib3N0ICIke2d94pSCJHogJGMxICR7Z33ilIIkeiAkYzIgJHtn
feKUgiR6ICRjMyAke2d94pSCJHoiIH0NCiAgV3JpdGUtSG9zdCAiJHtnfeKUlOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUtOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUtOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUmCR6IiB9DQpmdW5jdGlvbiBNYXJrKFtzdHJpbmddJHMsIFtzdHJpbmddJGxhbXAgPSAnR1JBWScpIHsgJHNjcmlwdDpUaW1lbGluZS5BZGQoW3Bz
Y3VzdG9tb2JqZWN0XUB7IGF0ID0gKEdldC1EYXRlIC1Gb3JtYXQgSEg6bW06c3MpOyB3aGF0ID0gJHM7IGxhbXAgPSAkbGFtcCB9KTsgV3JpdGUtSG9zdCAo
IiAgIiArIChHZXQtRGF0ZSAtRm9ybWF0IEhIOm1tOnNzKSArICIgIOKWtiAiICsgJHMpIH0NCg0KIyAtLS0tLS0tLS0tIOKRoCDlronlhajmuIXnkIYo5Y+q
5YuV5pys6KGM56iLKSAtLS0tLS0tLS0tDQpmdW5jdGlvbiBJbnZva2UtVkNTYWZlQ2xlYW51cCB7DQogICRNYXhNaW4gPSBpZiAoJE1heE1pbikgeyBbaW50
XSRNYXhNaW4gfSBlbHNlIHsgNjAgfQ0KICAkYmVmb3JlID0gW01hdGhdOjpSb3VuZCgoR2V0LUNpbUluc3RhbmNlIFdpbjMyX09wZXJhdGluZ1N5c3RlbSku
RnJlZVBoeXNpY2FsTWVtb3J5IC8gMU1CLCAyKQ0KICBbR0NdOjpDb2xsZWN0KCk7IFtHQ106OldhaXRGb3JQZW5kaW5nRmluYWxpemVycygpOyBbR0NdOjpD
b2xsZWN0KCkNCiAgJG9ycGhhbnMgPSBAKEdldC1DaW1JbnN0YW5jZSBXaW4zMl9Qcm9jZXNzIC1GaWx0ZXIgIlBhcmVudFByb2Nlc3NJZCA9ICRQSUQiIHwg
V2hlcmUtT2JqZWN0IHsgJF8uTmFtZSAtbWF0Y2ggJ3B5dGhvbnxwd3NoJyAtYW5kICgoR2V0LURhdGUpIC0gJF8uQ3JlYXRpb25EYXRlKS5Ub3RhbE1pbnV0
ZXMgLWd0ICRNYXhNaW4gfSkNCiAgaWYgKCRLaWxsT3JwaGFucykgeyBmb3JlYWNoICgkbyBpbiAkb3JwaGFucykgeyB0cnkgeyBTdG9wLVByb2Nlc3MgLUlk
ICRvLlByb2Nlc3NJZCAtRm9yY2UgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGludWUgfSBjYXRjaCB7IH0gfSB9DQogIGVsc2VpZiAoJG9ycGhhbnMuQ291
bnQpIHsgJHNjcmlwdDpWZXJkaWN0cy5BZGQoIlvmuIXnkIZdIOacrOihjOeoi+S4i+aciSAkKCRvcnBoYW5zLkNvdW50KSDmlK/otoXpgY4gJE1heE1pbiDl
iIbnmoQgcHl0aG9uL3B3c2gg5a2Q6KGM56iLIOKGkiDlj6rliJfkuI3mrroo6KaB5q665YqgIC1LaWxsT3JwaGFucztkb3Qtc291cmNlIOmAsuS4u+aOp+WP
sOaZgiBgJFBJRCDmmK/kuLvmjqflj7As5q665LqG5pyD6YCj5L2g5Yil55qE5bel5L2c5LiA6LW35q66KSIpIH0NCiAgJGFmdGVyID0gW01hdGhdOjpSb3Vu
ZCgoR2V0LUNpbUluc3RhbmNlIFdpbjMyX09wZXJhdGluZ1N5c3RlbSkuRnJlZVBoeXNpY2FsTWVtb3J5IC8gMU1CLCAyKTsgJGNwdSA9IChHZXQtQ2ltSW5z
dGFuY2UgV2luMzJfUHJvY2Vzc29yIHwgTWVhc3VyZS1PYmplY3QgTG9hZFBlcmNlbnRhZ2UgLUF2ZXJhZ2UpLkF2ZXJhZ2UNCiAgJHNjcmlwdDpWZXJkaWN0
cy5BZGQoIlvmuIXnkIZdIEdDIOWujOaIkCDCtyDlj6/nlKggUkFNICRiZWZvcmUg4oaSICRhZnRlciBHQiDCtyBDUFUgJGNwdSUgwrcg5a2k5YWSICQoJG9y
cGhhbnMuQ291bnQpIiArICQoaWYgKCRLaWxsT3JwaGFucykgeyAiKOW3suauuikiIH0gZWxzZSB7ICIo5Y+q5YiXKSIgfSkgKyAiKOS4jeWLleWEquWFiOas
iiDCtyDkuI0gRW1wdHlXb3JraW5nU2V0IMK3IOS4jeeisOS7luS6uuihjOeoiykiKTsgTWFyayAn5riF55CG5a6MJyAnR1JFRU4nIH0NCg0KIyAtLS0tLS0t
LS0tIOKRoSBURU1QIOeCuuS4u+iomOaGtumrlChMMTA3ICsgTDExNSBURU1QIOW+izrlj6rmuIXoh6rlrrblpL4gwrcg57i96YeP5LiK6ZmQIMK3IOS9jiBS
QU0g6Ieq5YuV6ZaL5rqi5a+rIMK3IOS4gOihjOW4sykgLS0tLS0tLS0tLQ0KZnVuY3Rpb24gSW5pdGlhbGl6ZS1WQ1RlbXAgew0KICAkS2VlcFJ1bnMgPSBp
ZiAoJEtlZXBSdW5zKSB7IFtpbnRdJEtlZXBSdW5zIH0gZWxzZSB7IDUgfTsgJE1heFRlbXBHQiA9IGlmICgkTWF4VGVtcEdCKSB7IFtkb3VibGVdJE1heFRl
bXBHQiB9IGVsc2UgeyAyLjAgfTsgJExvd1JhbUdCID0gaWYgKCRMb3dSYW1HQikgeyBbZG91YmxlXSRMb3dSYW1HQiB9IGVsc2UgeyAyLjAgfQ0KICAkcm9v
dCA9IGlmICgkZW52OlZJQV9URU1QX1JPT1QpIHsgJGVudjpWSUFfVEVNUF9ST09UIH0gZWxzZSB7IEpvaW4tUGF0aCAkZW52OkxPQ0FMQVBQREFUQSAnVGVt
cFxWSUFfcHJvZ3Jlc3MnIH0NCiAgJHJ1biA9IEpvaW4tUGF0aCAkcm9vdCAoInBzXyIgKyAkc2NyaXB0OlN0YW1wKTsgTmV3LUl0ZW0gLUl0ZW1UeXBlIERp
cmVjdG9yeSAtRm9yY2UgLVBhdGggJHJ1biB8IE91dC1OdWxsOyAkc3BpbGwgPSBKb2luLVBhdGggJHJ1biAnc3BpbGwnOyBOZXctSXRlbSAtSXRlbVR5cGUg
RGlyZWN0b3J5IC1Gb3JjZSAtUGF0aCAkc3BpbGwgfCBPdXQtTnVsbA0KICAkc2NyaXB0OkVudkJhY2t1cCA9IEB7IFRNUCA9ICRlbnY6VE1QOyBURU1QID0g
JGVudjpURU1QOyBUTVBESVIgPSAkZW52OlRNUERJUjsgUE9MQVJTX1RFTVBfRElSID0gJGVudjpQT0xBUlNfVEVNUF9ESVI7IFZJQV9EVUNLREJfVEVNUF9E
SVIgPSAkZW52OlZJQV9EVUNLREJfVEVNUF9ESVI7IFZJQV9GUk9NX1ZDR0MgPSAkZW52OlZJQV9GUk9NX1ZDR0M7IFZJQV9OT19PUEVOID0gJGVudjpWSUFf
Tk9fT1BFTjsgVklBX1NQSUxMX0RJUiA9ICRlbnY6VklBX1NQSUxMX0RJUjsgVklBX0xPV19SQU0gPSAkZW52OlZJQV9MT1dfUkFNIH0NCiAgJGVudjpWSUFf
VEVNUF9ST09UID0gJHJvb3Q7ICRlbnY6VE1QID0gJHJ1bjsgJGVudjpURU1QID0gJHJ1bjsgJGVudjpUTVBESVIgPSAkcnVuOyAkZW52OlBPTEFSU19URU1Q
X0RJUiA9ICRydW47ICRlbnY6VklBX0RVQ0tEQl9URU1QX0RJUiA9ICRydW47ICRlbnY6VklBX1NQSUxMX1RPX0RJU0sgPSAnMSc7ICRlbnY6VklBX1NQSUxM
X0RJUiA9ICRzcGlsbA0KICAkZnJlZUdCID0gdHJ5IHsgW01hdGhdOjpSb3VuZCgoR2V0LUNpbUluc3RhbmNlIFdpbjMyX09wZXJhdGluZ1N5c3RlbSkuRnJl
ZVBoeXNpY2FsTWVtb3J5IC8gMU1CLCAyKSB9IGNhdGNoIHsgLTEgfQ0KICAkZW52OlZJQV9MT1dfUkFNID0gaWYgKCRmcmVlR0IgLWdlIDAgLWFuZCAkZnJl
ZUdCIC1sdCAkTG93UmFtR0IpIHsgJzEnIH0gZWxzZSB7ICcwJyB9ICAgIyDkvY4gUkFNOuW8leaTjihWSUFfVGVtcFNwaWxsKeaUueWIhuWhiiArIOa6ouWv
qyBURU1QLOS4jeaUuSBwYWdlZmlsZeOAgeS4jSBFbXB0eVdvcmtpbmdTZXQNCiAgIyDlj6rmuIXoh6rlrrblpL4ocHNfKik65ru+5YuV55WZIE4g6LyqLOWG
jeaMiee4vemHj+S4iumZkOW+nuacgOiIiua4hTvpjpbkvY8oUnVubmluZyDmqpQp5oiWIDIg5bCP5pmC5YWn55qE5LiN5riFO+avj+a4heS4gOWkvuS4gOih
jOW4sw0KICAkb3duID0gQChHZXQtQ2hpbGRJdGVtICRyb290IC1EaXJlY3RvcnkgLUZpbHRlciAncHNfKicgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGlu
dWUgfCBTb3J0LU9iamVjdCBOYW1lIC1EZXNjZW5kaW5nKQ0KICAkc2l6ZXMgPSBAe307IGZvcmVhY2ggKCRkIGluICRvd24pIHsgJHNpemVzWyRkLk5hbWVd
ID0gKEdldC1DaGlsZEl0ZW0gJGQuRnVsbE5hbWUgLVJlY3Vyc2UgLUZpbGUgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGludWUgfCBNZWFzdXJlLU9iamVj
dCBMZW5ndGggLVN1bSkuU3VtIH0NCiAgJHRvdGFsID0gKCRzaXplcy5WYWx1ZXMgfCBNZWFzdXJlLU9iamVjdCAtU3VtKS5TdW07ICRwdXJnZWQgPSBAKCk7
ICRmcmVlZCA9IDANCiAgZm9yZWFjaCAoJGQgaW4gKCRvd24gfCBTZWxlY3QtT2JqZWN0IC1Ta2lwICRLZWVwUnVucykpIHsgaWYgKCRkLkxhc3RXcml0ZVRp
bWUgLWx0IChHZXQtRGF0ZSkuQWRkSG91cnMoLTIpIC1hbmQgLW5vdCAoVGVzdC1QYXRoIChKb2luLVBhdGggJGQuRnVsbE5hbWUgJ1JVTk5JTkcnKSkpIHsg
JHB1cmdlZCArPSAkZCB9IH0NCiAgJHN1cnZpdm9ycyA9IEAoJG93biB8IFdoZXJlLU9iamVjdCB7ICRwdXJnZWQgLW5vdGNvbnRhaW5zICRfIH0gfCBTb3J0
LU9iamVjdCBOYW1lKQ0KICBmb3JlYWNoICgkZCBpbiAkc3Vydml2b3JzKSB7IGlmICgkZC5OYW1lIC1lcSAoInBzXyIgKyAkc2NyaXB0OlN0YW1wKSkgeyBj
b250aW51ZSB9OyBpZiAoKCR0b3RhbCAtICRmcmVlZCkgLWxlICgkTWF4VGVtcEdCICogMUdCKSkgeyBicmVhayB9OyBpZiAoJGQuTGFzdFdyaXRlVGltZSAt
bHQgKEdldC1EYXRlKS5BZGRIb3VycygtMikgLWFuZCAtbm90IChUZXN0LVBhdGggKEpvaW4tUGF0aCAkZC5GdWxsTmFtZSAnUlVOTklORycpKSkgeyAkcHVy
Z2VkICs9ICRkOyAkZnJlZWQgKz0gW2RvdWJsZV0kc2l6ZXNbJGQuTmFtZV0gfSB9DQogIGZvcmVhY2ggKCRvIGluICRwdXJnZWQpIHsgJHN6ID0gW2RvdWJs
ZV0kc2l6ZXNbJG8uTmFtZV07IFJlbW92ZS1JdGVtICRvLkZ1bGxOYW1lIC1SZWN1cnNlIC1Gb3JjZSAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51ZTsg
QWRkLUNvbnRlbnQgKEpvaW4tUGF0aCAkcm9vdCAncHVyZ2VfbGVkZ2VyLmpzb25sJykgKCd7ImF0IjoiJyArIChHZXQtRGF0ZSAtRm9ybWF0IG8pICsgJyIs
InB1cmdlZCI6IicgKyAkby5OYW1lICsgJyIsImJ5dGVzIjonICsgW2ludDY0XSRzeiArICcsInJ1bGUiOiJMMTE1IGtlZXAgJyArICRLZWVwUnVucyArICcg
wrcgY2FwICcgKyAkTWF4VGVtcEdCICsgJ0dCIiwiZnJlZV9yYW1fZ2IiOicgKyAkZnJlZUdCICsgJ30nKSB9DQogIFNldC1Db250ZW50IChKb2luLVBhdGgg
JHJ1biAnUlVOTklORycpIChHZXQtRGF0ZSAtRm9ybWF0IG8pDQogICRzY3JpcHQ6VmVyZGljdHMuQWRkKCJbVEVNUF0gJHJ1biDCtyDmu77li5XnlZkgJEtl
ZXBSdW5zIOi8qiDCtyDkuIrpmZAgJE1heFRlbXBHQiBHQijnj74gJChbTWF0aF06OlJvdW5kKCgkdG90YWwgLSAkZnJlZWQpIC8gMUdCLCAyKSkgR0Ipwrcg
5riFICQoJHB1cmdlZC5Db3VudCkg5aS+IMK3IOWPr+eUqCBSQU0gJGZyZWVHQiBHQiDihpIg5L2OIFJBTSDmuqLlr6sgJChpZiAoJGVudjpWSUFfTE9XX1JB
TSAtZXEgJzEnKSB7ICfplosnIH0gZWxzZSB7ICfpl5wnIH0pKFZJQV9TUElMTF9ESVI9JHNwaWxsKSIpOyBNYXJrICdURU1QIOWwseS9jScgJChpZiAoJGVu
djpWSUFfTE9XX1JBTSAtZXEgJzEnKSB7ICdZRUxMT1cnIH0gZWxzZSB7ICdHUkVFTicgfSk7ICRydW4gfQ0KDQojIC0tLS0tLS0tLS0g4pGiIOWKoOmAn+WZ
qCAtLS0tLS0tLS0tDQpmdW5jdGlvbiBJbml0aWFsaXplLVZDQWNjZWwgew0KICAkYXV0byA9IEpvaW4tUGF0aCAkVklBICdzdXBwb3J0aXZlIG1vZHVsZXNc
VmVyaXRhc0NlbGVyaXRhcy5QUzcuQXV0b0ltcG9ydC5wczEnDQogIGlmICgtbm90IChUZXN0LVBhdGggJGF1dG8pKSB7ICRmID0gR2V0LUNoaWxkSXRlbSAo
Sm9pbi1QYXRoICRWSUEgJ3N1cHBvcnRpdmUgbW9kdWxlcycpIC1SZWN1cnNlIC1EZXB0aCAyIC1GaWx0ZXIgJ1Zlcml0YXNDZWxlcml0YXMuUFM3LkF1dG9J
bXBvcnQqLnBzMScgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGludWUgfCBTb3J0LU9iamVjdCBOYW1lIHwgU2VsZWN0LU9iamVjdCAtTGFzdCAxOyBpZiAo
JGYpIHsgJGF1dG8gPSAkZi5GdWxsTmFtZSB9IH0NCiAgJGNvcmUgPSBKb2luLVBhdGggJFZJQSAnc3VwcG9ydGl2ZSBtb2R1bGVzXHBzN1xWZXJpdGFzQ2Vs
ZXJpdGFzLlBTNy5wczEnDQogICRsb2FkZWQgPSAkbnVsbA0KICBpZiAoVGVzdC1QYXRoICRhdXRvKSB7IHRyeSB7IC4gJGF1dG87ICRsb2FkZWQgPSAnQXV0
b0ltcG9ydCcgfSBjYXRjaCB7ICRzY3JpcHQ6VmVyZGljdHMuQWRkKCJb5Yqg6YCf5ZmoXSBBdXRvSW1wb3J0IOi8ieWFpeWkseaVlzoiICsgJF8uRXhjZXB0
aW9uLk1lc3NhZ2UuU3BsaXQoW2NoYXJdMTApWzBdKSB9IH0NCiAgZWxzZWlmIChUZXN0LVBhdGggJGNvcmUpIHsgdHJ5IHsgLiAkY29yZTsgU2V0LVN0cmlj
dE1vZGUgLU9mZjsgJGxvYWRlZCA9ICdWZXJpdGFzQ2VsZXJpdGFzLlBTNy5wczEnIH0gY2F0Y2ggeyBTZXQtU3RyaWN0TW9kZSAtT2ZmOyAkc2NyaXB0OlZl
cmRpY3RzLkFkZCgiW+WKoOmAn+WZqF0g5qC45b+D6LyJ5YWl5aSx5pWXOiIgKyAkXy5FeGNlcHRpb24uTWVzc2FnZS5TcGxpdChbY2hhcl0xMClbMF0pIH0g
fQ0KICBpZiAoJGxvYWRlZCkgew0KICAgIGZvcmVhY2ggKCRmbiBpbiAoR2V0LUNvbW1hbmQgLUNvbW1hbmRUeXBlIEZ1bmN0aW9uIC1FcnJvckFjdGlvbiBT
aWxlbnRseUNvbnRpbnVlIHwgV2hlcmUtT2JqZWN0IHsgJF8uTmFtZSAtbWF0Y2ggJ0NlbGVyaXRhcycgfSkpIHsgdHJ5IHsgU2V0LUl0ZW0gLVBhdGggKCdm
dW5jdGlvbjpnbG9iYWw6JyArICRmbi5OYW1lKSAtVmFsdWUgJGZuLlNjcmlwdEJsb2NrIH0gY2F0Y2ggeyB9IH0gICAjIOWHveW8j+WFpyBkb3Qtc291cmNl
IOWPqua0u+WcqOWHveW8j+WFpyDihpIg5o+Q5Y2H5YiwIGdsb2JhbCzpgIDlh7ogUmVzdG9yZSDmiY3mib7lvpfliLANCiAgICAkdmVyID0gdHJ5IHsgaWYg
KCRzY3JpcHQ6Q2VsZXJpdGFzUFM3KSB7ICRzY3JpcHQ6Q2VsZXJpdGFzUFM3LlZlcnNpb24gfSBlbHNlIHsgJz8nIH0gfSBjYXRjaCB7ICc/JyB9DQogICAg
aWYgKChHZXQtQ29tbWFuZCBTdGFydC1DZWxlcml0YXNQUzcgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGludWUpIC1hbmQgJGxvYWRlZCAtZXEgJ0F1dG9J
bXBvcnQnKSB7IHRyeSB7IGlmICgoR2V0LUNvbW1hbmQgU3RhcnQtQ2VsZXJpdGFzUFM3KS5QYXJhbWV0ZXJzLkNvbnRhaW5zS2V5KCdQcm9maWxlJykpIHsg
U3RhcnQtQ2VsZXJpdGFzUFM3IC1Qcm9maWxlIGFnZ3Jlc3NpdmUgfCBPdXQtTnVsbCB9IGVsc2UgeyBTdGFydC1DZWxlcml0YXNQUzcgfCBPdXQtTnVsbCB9
IH0gY2F0Y2ggeyB9IH0NCiAgICAkc2NyaXB0OkFjY2VsTG9hZGVkID0gJHRydWU7ICRzY3JpcHQ6VmVyZGljdHMuQWRkKCJb5Yqg6YCf5ZmoXSAkbG9hZGVk
IOW3suWll+eUqCjmnKwgUElEIMK3ICR2ZXIgwrcg6YCA5Ye6IFJlc3RvcmUpIik7IE1hcmsgJ+WKoOmAn+WZqCcgJ0dSRUVOJyB9DQogIGVsc2UgeyAkc2Ny
aXB0OlZlcmRpY3RzLkFkZCgiW+WKoOmAn+WZqF0gQXV0b0ltcG9ydCDoiIcgcHM3XFZlcml0YXNDZWxlcml0YXMuUFM3LnBzMSDpg73kuI3lnKgg4oaSIGZh
bGxiYWNrIOeEoeWKoOmAnyzlip/og73nhafot5E7UFMtQUNDRUwg5qmLKFZJQV9QU19BY2NlbF9Nb2R1bGUpIiArICQoaWYgKFRlc3QtUGF0aCAiJFZJQVxz
dXBwb3J0aXZlIG1vZHVsZXNcVklBX1BTX0FjY2VsX01vZHVsZS5wczEiKSB7ICflnKgnIH0gZWxzZSB7ICfkuI3lnKgnIH0pKTsgTWFyayAn5Yqg6YCf5Zmo
IGZhbGxiYWNrJyAnWUVMTE9XJyB9IH0NCg0KIyAtLS0tLS0tLS0tIOKRqCDllZ/li5XlmagoTDExNzpQUyDlj6rllZ/li5XoiIfpgKPntZAgVS9JO+mCj+i8
r+WFqOWcqCBweXRob24gbWFuYWdlciAvIOW8leaTjikgLS0tLS0tLS0tLQ0KZnVuY3Rpb24gSW52b2tlLVZDTGF1bmNoIHsNCiAgcGFyYW0oW3N0cmluZ10k
U3ViLCBbc3RyaW5nXSRWZXJiLCBbc3RyaW5nW11dJFZlcmJBcmdzID0gQCgpLCBbaW50XSRTZWMgPSA2MDAsIFtzdHJpbmddJElkID0gJ0wnKQ0KICAkbWFw
ID0gQHsgVlJOID0gQCgnZnVuY3Rpb25hbCBtb2R1bGVzXFZSTicsICdWUk5fU3lzdGVtTWFuYWdlcl92Ki5weScpOyBWREYgPSBAKCdmdW5jdGlvbmFsIG1v
ZHVsZXNcVkRGJywgJ1ZERl9TeXN0ZW1NYW5hZ2VyX3YqLnB5Jyk7IFZDR0MgPSBAKCdzdXBwb3J0aXZlIG1vZHVsZXNccmVnaXN0cnknLCAnQ0dDX01ETCpf
SGVhbHRoTWF0cml4X3YqLnB5JykgfQ0KICBpZiAoLW5vdCAkbWFwLkNvbnRhaW5zS2V5KCRTdWIpKSB7ICRzY3JpcHQ6RXJyb3JzLkFkZCgiW+WVn+WLlV0g
5LiN6KqN6K2Y55qE5a2Q57O757WxICRTdWIoVlJOIC8gVkRGIC8gVkNHQykiKTsgcmV0dXJuICRudWxsIH0NCiAgJGRpciA9IEpvaW4tUGF0aCAkVklBICRt
YXBbJFN1Yl1bMF0NCiAgJHRhaWwgPSBHZXQtQ2hpbGRJdGVtIC1MaXRlcmFsUGF0aCAkZGlyIC1GaWx0ZXIgJG1hcFskU3ViXVsxXSAtRXJyb3JBY3Rpb24g
U2lsZW50bHlDb250aW51ZSB8IFNvcnQtT2JqZWN0IE5hbWUgfCBTZWxlY3QtT2JqZWN0IC1MYXN0IDENCiAgaWYgKC1ub3QgJHRhaWwpIHsgJHNjcmlwdDpF
cnJvcnMuQWRkKCJb5ZWf5YuVXSAkU3ViIOWwvueJiCBtYW5hZ2VyIOS4jeWcqCAkZGlyIik7IHJldHVybiAkbnVsbCB9DQogICRzY3JpcHQ6VmVyZGljdHMu
QWRkKCJb5ZWf5YuVXSAkU3ViIOKGkiAkKCR0YWlsLk5hbWUpICRWZXJiICQoJFZlcmJBcmdzIC1qb2luICcgJykiKQ0KICAkZW52OlZJQV9GUk9NX1ZDR0Mg
PSAnWUVTJw0KICAkb3V0ID0gSW52b2tlLVZDUHl0aG9uIC1JZCAkSWQgLUFyZ3YgKEAoJHRhaWwuRnVsbE5hbWUsICRWZXJiKSArICRWZXJiQXJncykgLVNl
YyAkU2VjDQogICRvdXQgfCBXaGVyZS1PYmplY3QgeyAkXyAtbWF0Y2ggJ15cW+ioiFxdfF5ccypcWyhSRUR8WUVMfOazqClcXScgfSB8IFNlbGVjdC1PYmpl
Y3QgLUZpcnN0IDMwIHwgRm9yRWFjaC1PYmplY3QgeyBpZiAoJF8gLW1hdGNoICdeXHMqXFtSRURcXScpIHsgJHNjcmlwdDpFcnJvcnMuQWRkKCJbJFN1YiAk
VmVyYl0gIiArICRfLlRyaW0oKSkgfSBlbHNlIHsgJHNjcmlwdDpWZXJkaWN0cy5BZGQoIlskU3ViICRWZXJiXSAiICsgJF8uVHJpbSgpKSB9IH0NCiAgJGh0
bWxzID0gQCgkb3V0IHwgRm9yRWFjaC1PYmplY3QgeyBpZiAoJF8gLW1hdGNoICcoW0EtWmEtel06XFxbXlxzIl0rP1wuaHRtbCknKSB7ICRNYXRjaGVzWzFd
IH0gfSB8IFdoZXJlLU9iamVjdCB7IFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggJF8gfSB8IFNlbGVjdC1PYmplY3QgLVVuaXF1ZSkNCiAgZm9yZWFjaCAoJGgg
aW4gJGh0bWxzKSB7ICRzY3JpcHQ6VmVyZGljdHMuQWRkKCJbVS9JXSAkaCIpOyBpZiAoLW5vdCAkTm9PcGVuIC1hbmQgJGVudjpWSUFfTk9fT1BFTiAtbmUg
JzEnKSB7IHRyeSB7IFN0YXJ0LVByb2Nlc3MgLUZpbGVQYXRoICRoIH0gY2F0Y2ggeyB9IH0gfQ0KICByZXR1cm4gJGh0bWxzIH0NCg0KIyAtLS0tLS0tLS0t
IOKRpCBQUyDihpIgcHl0aG9uIOS4jeacg+WNoeeahOmAmumBkyAtLS0tLS0tLS0tDQpmdW5jdGlvbiBJbnZva2UtVkNQeXRob24oW3N0cmluZ10kSWQsIFtz
dHJpbmdbXV0kQXJndiwgW2ludF0kU2VjID0gMCwgW3N0cmluZ10kUHl0aG9uID0gJ3B5dGhvbicpIHsNCiAgIyDnm7TlkbwgJiBweXRob24o5LiN5YyFIEpv
YiDCtyDkuI3ph43lsI7lkJEpO2FyZ3Yg6LWwIGJhc2U2NChQUyDljp/nlJ/lj4PmlbjkuI3mi4blvJXomZ8pO+eci+mWgOeLl+WcqCBweXRob24g5YWnKFRp
bWVyIOKGkiBvcy5fZXhpdCAxMjQp44CC5ZueIFtzdHJpbmdbXV0g6Ly45Ye6O3JjIOmAsiAkc2NyaXB0Okxhc3RSYw0KICBpZiAoLW5vdCAkU2VjKSB7ICRT
ZWMgPSBpZiAoJFB5U3RlcFNlYykgeyAkUHlTdGVwU2VjIH0gZWxzZSB7IDEyMCB9IH0NCiAgJGpzb24gPSAoJEFyZ3YgfCBDb252ZXJ0VG8tSnNvbiAtQ29t
cHJlc3MpOyBpZiAoJEFyZ3YuQ291bnQgLWVxIDEpIHsgJGpzb24gPSAiWyRqc29uXSIgfTsgJGI2NCA9IFtDb252ZXJ0XTo6VG9CYXNlNjRTdHJpbmcoW1Rl
eHQuRW5jb2RpbmddOjpVVEY4LkdldEJ5dGVzKCRqc29uKSkNCiAgJHdyYXAgPSAiaW1wb3J0IGJhc2U2NCxqc29uLG9zLHN5cyx0aHJlYWRpbmcscnVucHks
X3RocmVhZDsgYT1qc29uLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUoc3lzLmFyZ3ZbMV0pLmRlY29kZSgndXRmLTgnKSk7IHQxPXRocmVhZGluZy5UaW1lcigk
U2VjLCBfdGhyZWFkLmludGVycnVwdF9tYWluKTsgdDEuZGFlbW9uPVRydWU7IHQxLnN0YXJ0KCk7IHQyPXRocmVhZGluZy5UaW1lcigkU2VjKzEwLCBsYW1i
ZGE6IChzeXMuc3Rkb3V0LmZsdXNoKCksIG9zLl9leGl0KDEyNCkpKTsgdDIuZGFlbW9uPVRydWU7IHQyLnN0YXJ0KCk7IHN5cy5hcmd2PWFgbmltcG9ydCBj
b250ZXh0bGliYG50cnk6YG4gICAgcnVucHkucnVuX3BhdGgoYVswXSwgcnVuX25hbWU9J19fbWFpbl9fJylgbmV4Y2VwdCBLZXlib2FyZEludGVycnVwdDpg
biAgICBzeXMuc3Rkb3V0LmZsdXNoKCk7IG9zLl9leGl0KDEyNCkiDQogICR0MCA9IEdldC1EYXRlOyAkbyA9IEAoJiAkUHl0aG9uIC1jICR3cmFwICRiNjQg
Mj4mMSB8IEZvckVhY2gtT2JqZWN0IHsgIiIgKyAkXyB9KTsgJHNjcmlwdDpMYXN0UmMgPSAkTEFTVEVYSVRDT0RFOyAkZHQgPSBbaW50XSgoR2V0LURhdGUp
IC0gJHQwKS5Ub3RhbFNlY29uZHMgICAjIHYwMTA5OuWFiCBLZXlib2FyZEludGVycnVwdCjorpPlvJXmk44gZmluYWxseSAvIOWOn+WtkOaPm+WQjei3keWu
jCnlho0gMTAg56eS56Gs5q66DQogIGlmICgkc2NyaXB0OkxvZ0RpcikgeyAkbyB8IFNldC1Db250ZW50IChKb2luLVBhdGggJHNjcmlwdDpMb2dEaXIgIiRJ
ZC5vdXQiKSAtRW5jb2RpbmcgVVRGOCB9DQogIGlmICgkc2NyaXB0Okxhc3RSYyAtZXEgMTI0KSB7ICRzY3JpcHQ6RXJyb3JzLkFkZCgiW+eci+mWgOeLl10g
JElkIOi2hemBjiAkU2VjIOenkiDCtyDmnIDlvow6IiArICgoJG8gfCBTZWxlY3QtT2JqZWN0IC1MYXN0IDEpIC1qb2luICcnKSk7IE1hcmsgIiRJZCDpgL7m
mYIiICdSRUQnIH0NCiAgZWxzZWlmICgkc2NyaXB0Okxhc3RSYyAtbm90aW4gMCwgMikgeyAkc2NyaXB0OkVycm9ycy5BZGQoIlskSWRdIHJjICQoJHNjcmlw
dDpMYXN0UmMpIMK3ICIgKyAoKCRvIHwgV2hlcmUtT2JqZWN0IHsgJF8gLW1hdGNoICdFcnJvcnxUcmFjZWJhY2t8XFtGQUlMXF18UkVEJyB9IHwgU2VsZWN0
LU9iamVjdCAtTGFzdCAyKSAtam9pbiAnIHwgJykpOyBNYXJrICIkSWQgcmMgJCgkc2NyaXB0Okxhc3RSYykiICdSRUQnIH0NCiAgZWxzZSB7IE1hcmsgIiRJ
ZCByYyAkKCRzY3JpcHQ6TGFzdFJjKSDCtyAke2R0fXMiICdHUkVFTicgfQ0KICByZXR1cm4gJG8gfQ0KDQojIC0tLS0tLS0tLS0g4pGjIOmbmei7jCAvIOWk
mui7jOS4puihjCArIOmAsuW6puainSAtLS0tLS0tLS0tDQpmdW5jdGlvbiBJbnZva2UtVkNEdWFsTGFuZSB7DQogIHBhcmFtKFtoYXNodGFibGVbXV0kTGFu
ZXMsIFtzdHJpbmddJExvZ0RpcikNCiAgJE1heE1pbiA9IGlmICgkTWF4TWluKSB7IFtpbnRdJE1heE1pbiB9IGVsc2UgeyA2MCB9OyAkam9icyA9IFtvcmRl
cmVkXUB7fQ0KICBmb3JlYWNoICgkTCBpbiAkTGFuZXMpIHsgJGpvYnNbJEwuaWRdID0gU3RhcnQtVGhyZWFkSm9iIC1OYW1lICRMLmlkIC1TY3JpcHRCbG9j
ayAkTC5ydW4gLUFyZ3VtZW50TGlzdCAkTC5hcmdzOyAkc2NyaXB0OkxhbmVTdGF0ZVskTC5pZF0gPSBAeyB6aCA9ICRMLnpoOyBsYW1wID0gJ0dSQVknOyBw
Y3QgPSAwOyBub3RlID0gJycgfTsgTWFyayAoIui7iumBk+WVn+WLlSAiICsgJEwuaWQgKyAiIMK3ICIgKyAkTC56aCkgfQ0KICAkZGVhZGxpbmUgPSAoR2V0
LURhdGUpLkFkZE1pbnV0ZXMoJE1heE1pbik7IFdyaXRlLVZDQm94RnJhbWUgJGpvYnMuQ291bnQ7ICR0aWNrID0gMA0KICB3aGlsZSAoKCRqb2JzLlZhbHVl
cyB8IFdoZXJlLU9iamVjdCB7ICRfLlN0YXRlIC1pbiAnTm90U3RhcnRlZCcsICdSdW5uaW5nJyB9KS5Db3VudCAtZ3QgMCkgew0KICAgIGlmICgoR2V0LURh
dGUpIC1ndCAkZGVhZGxpbmUpIHsgZm9yZWFjaCAoJGsgaW4gJGpvYnMuS2V5cykgeyBpZiAoJGpvYnNbJGtdLlN0YXRlIC1pbiAnTm90U3RhcnRlZCcsICdS
dW5uaW5nJykgeyBTdG9wLUpvYiAkam9ic1ska107ICRzY3JpcHQ6RXJyb3JzLkFkZCgiW+mAvuaZgl0g6LuK6YGTICRrIOi2hemBjiAkTWF4TWluIOWIhizl
gZwiKSB9IH07IGJyZWFrIH0NCiAgICAkbGluZXMgPSBAKCk7ICRzdW0gPSAwOyAkdGljaysrDQogICAgZm9yZWFjaCAoJGsgaW4gJGpvYnMuS2V5cykgeyAk
cGYgPSBKb2luLVBhdGggJExvZ0RpciAoJGsgKyAnLnByb2dyZXNzJyk7ICRyYXcgPSBpZiAoVGVzdC1QYXRoICRwZikgeyBHZXQtQ29udGVudCAkcGYgLVJh
dyAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51ZSB9IGVsc2UgeyAnJyB9DQogICAgICAkcnVubmluZyA9ICRqb2JzWyRrXS5TdGF0ZSAtaW4gJ05vdFN0
YXJ0ZWQnLCAnUnVubmluZyc7ICRwY3QgPSBpZiAoLW5vdCAkcnVubmluZykgeyAxMDAgfSBlbHNlaWYgKCRyYXcgLW1hdGNoICdeXHMqKFxkezEsM30pJykg
eyBbaW50XSRNYXRjaGVzWzFdIH0gZWxzZSB7IDAgfTsgJHR4dCA9IGlmICgkcmF3IC1tYXRjaCAnwrdccyooLispJCcpIHsgJE1hdGNoZXNbMV0uVHJpbSgp
IH0gZWxzZSB7ICcnIH0NCiAgICAgICRzY3JpcHQ6TGFuZVN0YXRlWyRrXS5wY3QgPSAkcGN0OyAkc2NyaXB0OkxhbmVTdGF0ZVska10ubm90ZSA9ICR0eHQ7
ICRzdW0gKz0gW01hdGhdOjpNaW4oMTAwLCAkcGN0KQ0KICAgICAgJGxpbmVzICs9IEB7IG5hbWUgPSAiJGsgJCgkc2NyaXB0OkxhbmVTdGF0ZVska10uemgp
IjsgcGN0ID0gJHBjdDsgbGFtcCA9ICQoaWYgKCRydW5uaW5nKSB7ICdZRUxMT1cnIH0gZWxzZSB7ICdHUkVFTicgfSk7IHN0YXR1cyA9ICQoaWYgKCRydW5u
aW5nKSB7IEAoJ+Wft+ihjOS4rScsICfln7fooYzkuK0uJywgJ+Wft+ihjOS4rS4uJylbJHRpY2sgJSAzXSB9IGVsc2UgeyAn5a6M5oiQJyB9KTsgZGV0YWls
ID0gJHR4dCB9IH0NCiAgICBVcGRhdGUtVkNCb3ggJGxpbmVzOyBXcml0ZS1Qcm9ncmVzcyAtQWN0aXZpdHkgJ+S4puihjCcgLVN0YXR1cyAoIiQoW2ludF0o
JHN1bSAvIFtNYXRoXTo6TWF4KDEsICRqb2JzLkNvdW50KSkpJSIpIC1QZXJjZW50Q29tcGxldGUgKFtpbnRdKCRzdW0gLyBbTWF0aF06Ok1heCgxLCAkam9i
cy5Db3VudCkpKTsgU3RhcnQtU2xlZXAgLU1pbGxpc2Vjb25kcyA4MDAgfQ0KICBXcml0ZS1Qcm9ncmVzcyAtQWN0aXZpdHkgJ+S4puihjCcgLUNvbXBsZXRl
ZA0KICBmb3JlYWNoICgkayBpbiAkam9icy5LZXlzKSB7ICRvdXQgPSBAKFJlY2VpdmUtSm9iICRqb2JzWyRrXSAtV2FpdCAyPiYxIHwgRm9yRWFjaC1PYmpl
Y3QgeyAiIiArICRfIH0pOyAkb3V0IHwgU2V0LUNvbnRlbnQgKEpvaW4tUGF0aCAkTG9nRGlyICgkayArICcubG9nJykpIC1FbmNvZGluZyBVVEY4DQogICAg
JGJhZCA9IEAoJG91dCB8IFdoZXJlLU9iamVjdCB7ICRfIC1ub3RtYXRjaCAnXlxzKlxbKE9LfOioiHzms6h8WUVMfEdSQVkpXF0nIC1hbmQgJF8gLW1hdGNo
ICdeXHMqKFRyYWNlYmFja3xcW0ZBSUxcXXxcW1JFRFxdKXxyYyAoPyEwXGIpXGQrJyB9KTsgJGdvb2QgPSBAKCRvdXQgfCBXaGVyZS1PYmplY3QgeyAkXyAt
bWF0Y2ggJ1xbKE9LfEdSRUVOfOioiClcXXznuL3liKR8UEFTUycgfSkNCiAgICBpZiAoJG91dC5Db3VudCAtZXEgMCkgeyAkc2NyaXB0OkVycm9ycy5BZGQo
Ilska10g6LuK6YGT6Zu26Ly45Ye6KFN0YXRlICQoJGpvYnNbJGtdLlN0YXRlKSkiKSB9DQogICAgaWYgKCRiYWQuQ291bnQpIHsgJGJhZCB8IFNlbGVjdC1P
YmplY3QgLUZpcnN0IDQgfCBGb3JFYWNoLU9iamVjdCB7ICRzY3JpcHQ6RXJyb3JzLkFkZCgiWyRrXSAiICsgJF8uVHJpbSgpLlN1YnN0cmluZygwLCBbTWF0
aF06Ok1pbigxNjAsICRfLlRyaW0oKS5MZW5ndGgpKSkgfSB9DQogICAgJGdvb2QgfCBTZWxlY3QtT2JqZWN0IC1MYXN0IDMgfCBGb3JFYWNoLU9iamVjdCB7
ICRzY3JpcHQ6VmVyZGljdHMuQWRkKCJbJGtdICIgKyAkXy5UcmltKCkuU3Vic3RyaW5nKDAsIFtNYXRoXTo6TWluKDE2MCwgJF8uVHJpbSgpLkxlbmd0aCkp
KSB9DQogICAgJHNjcmlwdDpMYW5lU3RhdGVbJGtdLmxhbXAgPSBpZiAoJGJhZC5Db3VudCAtb3IgJG91dC5Db3VudCAtZXEgMCkgeyAnUkVEJyB9IGVsc2Vp
ZiAoJGdvb2QuQ291bnQpIHsgJ0dSRUVOJyB9IGVsc2UgeyAnWUVMTE9XJyB9OyAkc2NyaXB0OkxhbmVTdGF0ZVska10ucGN0ID0gMTAwOyBNYXJrICgi6LuK
6YGTICRrIOWujCDCtyAiICsgJHNjcmlwdDpMYW5lU3RhdGVbJGtdLmxhbXApICRzY3JpcHQ6TGFuZVN0YXRlWyRrXS5sYW1wDQogICAgUmVtb3ZlLUpvYiAk
am9ic1ska10gLUZvcmNlIC1FcnJvckFjdGlvbiBTaWxlbnRseUNvbnRpbnVlIH0NCiAgJGZpbmFsID0gQCgpOyBmb3JlYWNoICgkayBpbiAkam9icy5LZXlz
KSB7ICRMID0gJHNjcmlwdDpMYW5lU3RhdGVbJGtdOyAkZmluYWwgKz0gQHsgbmFtZSA9ICIkayAkKCRMLnpoKSI7IHBjdCA9IDEwMDsgbGFtcCA9ICRMLmxh
bXA7IHN0YXR1cyA9IEB7IEdSRUVOID0gJ+mBjic7IFlFTExPVyA9ICfopoHkurroo4EnOyBSRUQgPSAn57SFJyB9WyRMLmxhbXBdOyBkZXRhaWwgPSAkKGlm
ICgkTC5sYW1wIC1lcSAnUkVEJykgeyAoJHNjcmlwdDpFcnJvcnMgfCBXaGVyZS1PYmplY3QgeyAkXyAtbGlrZSAiWyRrXSoiIH0gfCBTZWxlY3QtT2JqZWN0
IC1GaXJzdCAxKSB9IGVsc2UgeyAkTC5ub3RlIH0pIH0gfQ0KICBVcGRhdGUtVkNCb3ggJGZpbmFsIH0NCg0KIyAtLS0tLS0tLS0tIOKRpiDpnZzmhYsgSFRN
TCBVL0ko55u05o6l6Lez5Ye6LOS4jee2k+S8uuacjeWZqCkgLS0tLS0tLS0tLQ0KZnVuY3Rpb24gV3JpdGUtVkNIdG1sKFtzdHJpbmddJFRpdGxlLCBbc3Ry
aW5nXSRMb2dEaXIpIHsNCiAgJGUgPSB7IHBhcmFtKCRzKSBbTmV0LldlYlV0aWxpdHldOjpIdG1sRW5jb2RlKCIkcyIpIH07ICRvdmVyYWxsID0gaWYgKCRz
Y3JpcHQ6RXJyb3JzLkNvdW50KSB7ICdSRUQnIH0gZWxzZWlmICgoJHNjcmlwdDpMYW5lU3RhdGUuVmFsdWVzIHwgV2hlcmUtT2JqZWN0IHsgJF8ubGFtcCAt
ZXEgJ1lFTExPVycgfSkuQ291bnQpIHsgJ1lFTExPVycgfSBlbHNlIHsgJ0dSRUVOJyB9DQogICRjc3MgPSAiQGtleWZyYW1lcyB2aWEtYmxpbmt7MCUsMTAw
JXtvcGFjaXR5OjF9NTAle29wYWNpdHk6LjI1fX06cm9vdHstLWc6JCgkc2NyaXB0OlBBTC5HUkVFTik7LS15OiQoJHNjcmlwdDpQQUwuWUVMTE9XKTstLXI6
JCgkc2NyaXB0OlBBTC5SRUQpOy0tazokKCRzY3JpcHQ6UEFMLkdSQVkpOy0tbjokKCRzY3JpcHQ6UEFMLk5PREFUQSk7LS1ib3JkZXI6I2U1ZTdlYjstLW11
dGVkOiM2YjcyODA7LS1mczoxMXB4fSp7Ym94LXNpemluZzpib3JkZXItYm94fWJvZHl7bWFyZ2luOjA7Zm9udDp2YXIoLS1mcykvMS4zNSBBcmlhbCwnTWlj
cm9zb2Z0IEpoZW5nSGVpJyxzYW5zLXNlcmlmO2JhY2tncm91bmQ6I2Y2ZjdmOTtjb2xvcjojMTExODI3fS50b3B7cG9zaXRpb246c3RpY2t5O3RvcDowO2Jh
Y2tncm91bmQ6I2ZmZjtib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1ib3JkZXIpO3BhZGRpbmc6NnB4IDEwcHg7ZGlzcGxheTpmbGV4O2dhcDoxMHB4
O2FsaWduLWl0ZW1zOmNlbnRlcjtmbGV4LXdyYXA6d3JhcH0udG9wIGJ7Zm9udC1zaXplOjEzcHh9LmdyaWR7ZGlzcGxheTpncmlkO2dyaWQtdGVtcGxhdGUt
Y29sdW1uczpyZXBlYXQoMTIsMWZyKTtnYXA6OHB4O3BhZGRpbmc6OHB4fS5jYXJke2JhY2tncm91bmQ6I2ZmZjtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWJv
cmRlcik7Ym9yZGVyLXJhZGl1czo2cHg7cGFkZGluZzo3cHggOXB4O21pbi13aWR0aDowfS5jYXJkIGgze21hcmdpbjowIDAgNHB4O2ZvbnQtc2l6ZToxMXB4
O2NvbG9yOnZhcigtLW11dGVkKX0uYzN7Z3JpZC1jb2x1bW46c3BhbiAzfS5jNntncmlkLWNvbHVtbjpzcGFuIDZ9LmMxMntncmlkLWNvbHVtbjpzcGFuIDEy
fS5sYW1we2Rpc3BsYXk6aW5saW5lLWJsb2NrO3dpZHRoOjExcHg7aGVpZ2h0OjExcHg7Ym9yZGVyLXJhZGl1czo1MCU7dmVydGljYWwtYWxpZ246bWlkZGxl
O21hcmdpbi1yaWdodDo0cHg7Ym9yZGVyOjFweCBzb2xpZCByZ2JhKDAsMCwwLC4xMil9LmxhbXAuR1JFRU57YmFja2dyb3VuZDp2YXIoLS1nKX0ubGFtcC5Z
RUxMT1d7YmFja2dyb3VuZDp2YXIoLS15KX0ubGFtcC5SRUR7YmFja2dyb3VuZDp2YXIoLS1yKTthbmltYXRpb246dmlhLWJsaW5rIDEuOHMgZWFzZS1pbi1v
dXQgaW5maW5pdGV9LmxhbXAuR1JBWXtiYWNrZ3JvdW5kOnZhcigtLWspfS5sYW1wLk5PREFUQXtiYWNrZ3JvdW5kOnZhcigtLW4pfS5iYXJ7aGVpZ2h0Ojhw
eDtiYWNrZ3JvdW5kOiNlZWU7Ym9yZGVyLXJhZGl1czo0cHg7b3ZlcmZsb3c6aGlkZGVufS5iYXIgaXtkaXNwbGF5OmJsb2NrO2hlaWdodDoxMDAlO2JhY2tn
cm91bmQ6dmFyKC0tZyl9Lnl7Y29sb3I6IzkyNDAwZX0ucntjb2xvcjojYjkxYzFjfXByZXt3aGl0ZS1zcGFjZTpwcmUtd3JhcDttYXJnaW46MDtmb250OjEx
cHggQ29uc29sYXMsbW9ub3NwYWNlfXRhYmxle2JvcmRlci1jb2xsYXBzZTpjb2xsYXBzZTt3aWR0aDoxMDAlfXRkLHRoe2JvcmRlci1ib3R0b206MXB4IHNv
bGlkIHZhcigtLWJvcmRlcik7cGFkZGluZzoycHggNnB4O3RleHQtYWxpZ246bGVmdH10aHtiYWNrZ3JvdW5kOiNmM2Y0ZjZ9QG1lZGlhIChwcmVmZXJzLXJl
ZHVjZWQtbW90aW9uOnJlZHVjZSl7LmxhbXAuUkVEe2FuaW1hdGlvbjpub25lfX1AbWVkaWEgKG1heC13aWR0aDo3MjBweCl7LmdyaWR7Z3JpZC10ZW1wbGF0
ZS1jb2x1bW5zOjFmcjtwYWRkaW5nOjZweH0uYzMsLmM2LC5jMTJ7Z3JpZC1jb2x1bW46c3BhbiAxfWJvZHl7Zm9udC1zaXplOjEycHh9fSINCiAgJGggPSBb
VGV4dC5TdHJpbmdCdWlsZGVyXTo6bmV3KCk7IFt2b2lkXSRoLkFwcGVuZCgiPCFkb2N0eXBlIGh0bWw+PGh0bWwgbGFuZz0nemgtVFcnPjxoZWFkPjxtZXRh
IGNoYXJzZXQ9J3V0Zi04Jz48bWV0YSBuYW1lPSd2aWV3cG9ydCcgY29udGVudD0nd2lkdGg9ZGV2aWNlLXdpZHRoLGluaXRpYWwtc2NhbGU9MSx2aWV3cG9y
dC1maXQ9Y292ZXInPjx0aXRsZT4kKCYgJGUgJFRpdGxlKTwvdGl0bGU+PHN0eWxlPiRjc3M8L3N0eWxlPjwvaGVhZD48Ym9keT48ZGl2IGNsYXNzPSd0b3An
PjxiPiQoJiAkZSAkVGl0bGUpPC9iPjxzcGFuPjxpIGNsYXNzPSdsYW1wICRvdmVyYWxsJz48L2k+JG92ZXJhbGw8L3NwYW4+PHNwYW4gc3R5bGU9J2NvbG9y
OnZhcigtLW11dGVkKSc+JCgkc2NyaXB0OlN0YW1wKSDCtyDpnZzmhYvpoIEgwrcg6Zu25Ly65pyN5ZmoIMK3IOiJsiA9IFZJQV9VSV9Gb3JtYXRMb2NrPC9z
cGFuPjwvZGl2PjxkaXYgY2xhc3M9J2dyaWQnPiIpDQogIFt2b2lkXSRoLkFwcGVuZCgiPGRpdiBjbGFzcz0nY2FyZCBjMyc+PGgzPui7iumBkzwvaDM+Iik7
IGZvcmVhY2ggKCRrIGluICRzY3JpcHQ6TGFuZVN0YXRlLktleXMpIHsgJEwgPSAkc2NyaXB0OkxhbmVTdGF0ZVska107IFt2b2lkXSRoLkFwcGVuZCgiPGRp
dj48aSBjbGFzcz0nbGFtcCAkKCRMLmxhbXApJz48L2k+PGI+JCgmICRlICRrKTwvYj4gJCgmICRlICRMLnpoKTwvZGl2PjxkaXYgY2xhc3M9J2Jhcic+PGkg
c3R5bGU9J3dpZHRoOiQoJEwucGN0KSUnPjwvaT48L2Rpdj48ZGl2IHN0eWxlPSdjb2xvcjp2YXIoLS1tdXRlZCknPiQoJiAkZSAkTC5ub3RlKTwvZGl2PiIp
IH07IFt2b2lkXSRoLkFwcGVuZCgiPC9kaXY+IikNCiAgW3ZvaWRdJGguQXBwZW5kKCI8ZGl2IGNsYXNzPSdjYXJkIGMzJz48aDM+6Yyv6KqkICQoJHNjcmlw
dDpFcnJvcnMuQ291bnQpPC9oMz4iKTsgZm9yZWFjaCAoJHggaW4gJHNjcmlwdDpFcnJvcnMpIHsgW3ZvaWRdJGguQXBwZW5kKCI8ZGl2IGNsYXNzPSdyJz48
aSBjbGFzcz0nbGFtcCBSRUQnPjwvaT4kKCYgJGUgJHgpPC9kaXY+IikgfTsgaWYgKC1ub3QgJHNjcmlwdDpFcnJvcnMuQ291bnQpIHsgW3ZvaWRdJGguQXBw
ZW5kKCI8ZGl2PjxpIGNsYXNzPSdsYW1wIEdSRUVOJz48L2k+MCDku7Y8L2Rpdj4iKSB9OyBbdm9pZF0kaC5BcHBlbmQoIjwvZGl2PiIpDQogIFt2b2lkXSRo
LkFwcGVuZCgiPGRpdiBjbGFzcz0nY2FyZCBjNic+PGgzPuaZgumWk+i7uDwvaDM+PHRhYmxlPjx0cj48dGg+5pmC5Yi7PC90aD48dGg+54eIPC90aD48dGg+
5LqL5Lu2PC90aD48L3RyPiIpOyBmb3JlYWNoICgkdCBpbiAkc2NyaXB0OlRpbWVsaW5lKSB7IFt2b2lkXSRoLkFwcGVuZCgiPHRyPjx0ZD4kKCR0LmF0KTwv
dGQ+PHRkPjxpIGNsYXNzPSdsYW1wICQoJHQubGFtcCknPjwvaT48L3RkPjx0ZD4kKCYgJGUgJHQud2hhdCk8L3RkPjwvdHI+IikgfTsgW3ZvaWRdJGguQXBw
ZW5kKCI8L3RhYmxlPjwvZGl2PiIpDQogIFt2b2lkXSRoLkFwcGVuZCgiPGRpdiBjbGFzcz0nY2FyZCBjMTInPjxoMz7pu4PlrZco6LK857WmIEFJKTwvaDM+
PHByZSBjbGFzcz0neSc+Iik7IGZvcmVhY2ggKCR2IGluICRzY3JpcHQ6VmVyZGljdHMpIHsgW3ZvaWRdJGguQXBwZW5kKCgmICRlICR2KSArICJgbiIpIH07
IFt2b2lkXSRoLkFwcGVuZCgiTkVYVDogIiArICQoaWYgKCRzY3JpcHQ6RXJyb3JzLkNvdW50KSB7ICfmiorntIXlrZfmlbTmrrXosrzntaYgQUknIH0gZWxz
ZSB7ICflhajntqAg4oaSIOmOliBMS0dDIMK3IOS4i+S4gOi8qicgfSkgKyAiPC9wcmU+PC9kaXY+PC9kaXY+PC9ib2R5PjwvaHRtbD4iKQ0KICAkcCA9IEpv
aW4tUGF0aCAkTG9nRGlyICdWQ19VSS5odG1sJzsgW0lPLkZpbGVdOjpXcml0ZUFsbFRleHQoJHAsICRoLlRvU3RyaW5nKCksIFtUZXh0LlVURjhFbmNvZGlu
Z106Om5ldygkZmFsc2UpKTsgQ29weS1JdGVtICRwICIkVklBXFZJQV9SZXBvcnRzXHJldmlld1xWQ19VSV9sYXRlc3QuaHRtbCIgLUZvcmNlIC1FcnJvckFj
dGlvbiBTaWxlbnRseUNvbnRpbnVlOyAkcCB9DQoNCiMgLS0tLS0tLS0tLSDikaUg5pS25bC+Oum7g+WtlyDCtyDntIXlrZcgwrcg5Ymq6LK857C/IMK3IOmW
i+mggSAtLS0tLS0tLS0tDQpmdW5jdGlvbiBTaG93LVZDU3VtbWFyeSB7DQogIHBhcmFtKFtzdHJpbmddJFRpdGxlLCBbc3RyaW5nXSRMb2dEaXIpDQogICR5
ID0gImBlWzkzbSI7ICRyID0gImBlWzkxbSI7ICRnID0gImBlWzkybSI7ICRkID0gImBlWzkwbSI7ICR6ID0gImBlWzBtIjsgJGIgPSAiYGVbMW0iDQogIFdy
aXRlLUhvc3QgIiI7IFdyaXRlLUhvc3QgKCIkYuKVkOKVkOKVkOKVkOKVkOKVkCAkVGl0bGUgwrcgJCgkc2NyaXB0OlN0YW1wKSDilZDilZDilZDilZDilZDi
lZAkeiIpDQogICRncSA9ICRzY3JpcHQ6Qy5HcmV5OyAkenogPSAkc2NyaXB0OkMuUmVzZXQgICAjIOaUtuWwvuefqemZozrpoIXnm64g4pSCIOeLgOaFiyDi
lIIg6Zec6Y216bueIOKUgiDntLDnr4AoUGFkLVZpc3VhbCDkuK3mloflsI3pvYopDQogIFdyaXRlLUhvc3QgIiR7Z3F94pSM4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSs4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSs4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSA4pSs4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSQJHp6Ig0KICBXcml0ZS1Ib3N0ICIke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwg
J+mgheebricgMjApICsgIiAke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwgJ+eLgOaFiycgMTIpICsgIiAke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwg
J+mXnOmNtem7nicgMjgpICsgIiAke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwgJ+e0sOevgCcgMzgpICsgIiAke2dxfeKUgiR6eiINCiAgV3JpdGUtSG9z
dCAiJHtncX3ilJzilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilLzilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilLzilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilLzilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilKQkenoiDQogIGZvcmVhY2ggKCRr
IGluICRzY3JpcHQ6TGFuZVN0YXRlLktleXMpIHsgJEwgPSAkc2NyaXB0OkxhbmVTdGF0ZVska107ICRjb2wgPSBzd2l0Y2ggKCRMLmxhbXApIHsgJ1JFRCcg
eyAkciB9ICdZRUxMT1cnIHsgJHkgfSAnR1JFRU4nIHsgJGcgfSBkZWZhdWx0IHsgJGQgfSB9DQogICAgJGtleSA9ICgkc2NyaXB0OkVycm9ycyB8IFdoZXJl
LU9iamVjdCB7ICRfIC1saWtlICJbJGtdKiIgfSB8IFNlbGVjdC1PYmplY3QgLUZpcnN0IDEpOyBpZiAoLW5vdCAka2V5KSB7ICRrZXkgPSAoJHNjcmlwdDpW
ZXJkaWN0cyB8IFdoZXJlLU9iamVjdCB7ICRfIC1saWtlICJbJGtdKiIgfSB8IFNlbGVjdC1PYmplY3QgLUxhc3QgMSkgfQ0KICAgIFdyaXRlLUhvc3QgIiR7
Z3F94pSCJHp6ICIgKyAoUGFkLVZpc3VhbCAiJGsgJCgkTC56aCkiIDIwKSArICIgJHtncX3ilIIkenogIiArIChQYWQtVmlzdWFsICgiJGNvbFsiICsgQHsg
R1JFRU4gPSAn5a6M5YWo6YCa6YGOJzsgWUVMTE9XID0gJ+imgeS6uuijgSc7IFJFRCA9ICflsJrmnKrkv67lvqknIH1bJEwubGFtcF0gKyAiXSR6IikgMTIp
ICsgIiAke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwgKCIkY29sIiArICgiJGtleSIgLXJlcGxhY2UgIl5cWyRrXF1ccyoiLCAnJykgKyAiJHoiKSAyOCkg
KyAiICR7Z3F94pSCJHp6ICIgKyAoUGFkLVZpc3VhbCAiJCgkTC5ub3RlKSIgMzgpICsgIiAke2dxfeKUgiR6eiIgfQ0KICBXcml0ZS1Ib3N0ICIke2dxfeKU
giR6eiAiICsgKFBhZC1WaXN1YWwgJ+mMr+iqpOWQiOioiCcgMjApICsgIiAke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwgJChpZiAoJHNjcmlwdDpFcnJv
cnMuQ291bnQpIHsgIiRyWyQoJHNjcmlwdDpFcnJvcnMuQ291bnQpIOS7tl0keiIgfSBlbHNlIHsgIiRnWzAg5Lu2XSR6IiB9KSAxMikgKyAiICR7Z3F94pSC
JHp6ICIgKyAoUGFkLVZpc3VhbCAkKGlmICgkc2NyaXB0OkVycm9ycy5Db3VudCkgeyAiJHIkKCRzY3JpcHQ6RXJyb3JzWzBdKSR6IiB9IGVsc2UgeyAiJGfl
hajntqAkeiIgfSkgMjgpICsgIiAke2dxfeKUgiR6eiAiICsgKFBhZC1WaXN1YWwgJChpZiAoJHNjcmlwdDpFcnJvcnMuQ291bnQpIHsgJ+aKiue0heWtl+aV
tOauteiyvOe1piBBSScgfSBlbHNlIHsgJ+mOliBMS0dDIMK3IOS4i+S4gOi8qicgfSkgMzgpICsgIiAke2dxfeKUgiR6eiINCiAgV3JpdGUtSG9zdCAiJHtn
cX3ilJTilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilLTilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilLTilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilLTilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilJgkenoiDQogIGZvcmVhY2ggKCR2IGluICRz
Y3JpcHQ6VmVyZGljdHMpIHsgV3JpdGUtSG9zdCAoIiR5JHYkeiIpIH0NCiAgaWYgKCRzY3JpcHQ6RXJyb3JzLkNvdW50KSB7IFdyaXRlLUhvc3QgKCIkciRi
4pSA4pSAIOmMr+iqpCAkKCRzY3JpcHQ6RXJyb3JzLkNvdW50KSDku7Yg4pSA4pSAJHoiKTsgZm9yZWFjaCAoJHggaW4gJHNjcmlwdDpFcnJvcnMpIHsgV3Jp
dGUtSG9zdCAoIiRyJHgkeiIpIH0gfSBlbHNlIHsgV3JpdGUtSG9zdCAoIiRn4pSA4pSAIOmMr+iqpCAwIOS7tiDilIDilIAkeiIpIH0NCiAgJHBhY2sgPSBA
KCIjICRUaXRsZSAkKCRzY3JpcHQ6U3RhbXApIikgKyAoJHNjcmlwdDpWZXJkaWN0cyB8IEZvckVhY2gtT2JqZWN0IHsgIi0gIiArICRfIH0pICsgQCgiIyMg
6Yyv6KqkIikgKyAoJHNjcmlwdDpFcnJvcnMgfCBGb3JFYWNoLU9iamVjdCB7ICItICIgKyAkXyB9KSArIEAoIk5FWFQ6ICIgKyAkKGlmICgkc2NyaXB0OkVy
cm9ycy5Db3VudCkgeyAn5oqK57SF5a2X5pW05q616LK857WmIEFJJyB9IGVsc2UgeyAn5YWo57agIOKGkiDpjpYgTEtHQyDCtyDkuIvkuIDovKonIH0pKQ0K
ICAkcGFjayB8IFNldC1Db250ZW50IChKb2luLVBhdGggJExvZ0RpciAncGFzdGUubWQnKSAtRW5jb2RpbmcgVVRGODsgdHJ5IHsgKCRwYWNrIC1qb2luICJg
biIpIHwgU2V0LUNsaXBib2FyZCB9IGNhdGNoIHsgfQ0KICAkaHRtbCA9IFdyaXRlLVZDSHRtbCAkVGl0bGUgJExvZ0RpcjsgV3JpdGUtSG9zdCAoIiRkIiAr
ICJsb2cgJExvZ0RpciDCtyDpu4PlrZcgPSDosrzntaYgQUkgwrcg57SF5a2XID0g6Yyv6KqkIMK3IFUvSSAkaHRtbCR6IikNCiAgaWYgKC1ub3QgJE5vT3Bl
bikgeyB0cnkgeyBTdGFydC1Qcm9jZXNzICRodG1sIH0gY2F0Y2ggeyB9IH0NCiAgaWYgKEdldC1Db21tYW5kIFJlc3RvcmUtQ2VsZXJpdGFzUFM3IC1FcnJv
ckFjdGlvbiBTaWxlbnRseUNvbnRpbnVlKSB7IHRyeSB7IFJlc3RvcmUtQ2VsZXJpdGFzUFM3IHwgT3V0LU51bGwgfSBjYXRjaCB7IH0gfQ0KICBpZiAoJHNj
cmlwdDpBY2NlbExvYWRlZCAtYW5kIChHZXQtQ29tbWFuZCBSZXN0b3JlLUNlbGVyaXRhc1BTNyAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51ZSkpIHsg
dHJ5IHsgUmVzdG9yZS1DZWxlcml0YXNQUzcgfCBPdXQtTnVsbCB9IGNhdGNoIHsgfSB9ICAgIyDpl5zplonljbPpgoTljp8o5Yqg6YCf5Zmo5a6J5YWo5aWR
57SEKQ0KICBpZiAoJFJ1biAtYW5kIChUZXN0LVBhdGggKEpvaW4tUGF0aCAkUnVuICdSVU5OSU5HJykpKSB7IFJlbW92ZS1JdGVtIChKb2luLVBhdGggJFJ1
biAnUlVOTklORycpIC1Gb3JjZSAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51ZSB9ICAgIyBMMTE1Oui3keWujOino+mZpOmOlizlpL7nlZnliLDmu77l
i5XmnJ/mu78NCiAgaWYgKCRzY3JpcHQ6RW52QmFja3VwKSB7IGZvcmVhY2ggKCRrIGluICRzY3JpcHQ6RW52QmFja3VwLktleXMpIHsgJHYgPSAkc2NyaXB0
OkVudkJhY2t1cFska107IGlmICgkbnVsbCAtZXEgJHYgLW9yICR2IC1lcSAnJykgeyBSZW1vdmUtSXRlbSAiRW52OiRrIiAtRXJyb3JBY3Rpb24gU2lsZW50
bHlDb250aW51ZSB9IGVsc2UgeyBTZXQtSXRlbSAiRW52OiRrIiAkdiB9IH0gfSAgICMgdjAxMDk66YCA5Ye66YKE5Y6f55Kw5aKD6K6K5pW4KOWQqyBWSUFf
RlJPTV9WQ0dDLOS4jeeVmeW+jOmWgOe1puS5i+W+jOeahOaMh+S7pOe5numWmCkNCiAgJHNjcmlwdDpWZXJkaWN0cy5BZGQoIlvpgoTljp9dIOeSsOWig+iu
iuaVuOiIh+WKoOmAn+WZqOW3sumChOWOnzvmnKzmlK/lj6rlr6sgVklBX1JlcG9ydHNccmV2aWV3XHBzXzzmmYLmiLM+XCDoiIcgVkNfVUlfbGF0ZXN0Lmh0
bWwiKSB9DQoNCiMgPT09PT09PT09PT09PT09PT09PT09PT0g6aqo5p625Li76auUKOWPquaUuemAmeijoeeahCAkTGFuZXMpID09PT09PT09PT09PT09PT09
PT09PT09DQppZiAoLW5vdCAkTm9DbGVhbnVwKSB7IEludm9rZS1WQ1NhZmVDbGVhbnVwIH0NCiRSdW4gPSBJbml0aWFsaXplLVZDVGVtcDsgSW5pdGlhbGl6
ZS1WQ0FjY2VsDQokc2NyaXB0OkxvZ0RpciA9IEpvaW4tUGF0aCAkVklBICgiVklBX1JlcG9ydHNccmV2aWV3XHBzXyIgKyAkc2NyaXB0OlN0YW1wKTsgTmV3
LUl0ZW0gLUl0ZW1UeXBlIERpcmVjdG9yeSAtRm9yY2UgLVBhdGggJHNjcmlwdDpMb2dEaXIgfCBPdXQtTnVsbDsgJExvZ0RpciA9ICRzY3JpcHQ6TG9nRGly
DQokUmVnID0gaWYgKCRnbG9iYWw6VklBUmVnaXN0ZXJQYXRoKSB7ICRnbG9iYWw6VklBUmVnaXN0ZXJQYXRoIH0gZWxzZSB7IChHZXQtQ2hpbGRJdGVtICRW
SUEgLUZpbHRlciAnUmVnaXN0ZXItVklBLUNvbW1hbmRzLXYqLnBzMScgfCBTb3J0LU9iamVjdCBOYW1lIHwgU2VsZWN0LU9iamVjdCAtTGFzdCAxKS5GdWxs
TmFtZSB9DQppZiAoJERlbW8pIHsNCiAgJExhbmVzID0gQCgNCiAgICBAeyBpZCA9ICdBJzsgemggPSAn56S656+EOlBTIOefreS7pCh2aWEtdmNnYyB0b2tl
biknOyBhcmdzID0gQCgkVklBLCAkUmVnLCAkTG9nRGlyKTsgcnVuID0geyBwYXJhbSgkVklBLCAkUmVnLCAkTG9nRGlyKSBTZXQtTG9jYXRpb24gJFZJQTsg
LiAkUmVnIHwgT3V0LU51bGw7IFNldC1Db250ZW50IChKb2luLVBhdGggJExvZ0RpciAnQS5wcm9ncmVzcycpICczMCDCtyB0b2tlbicgLUVuY29kaW5nIFVU
Rjg7IHZpYS12Y2djIHRva2VuIDI+JjEgfCBTZWxlY3QtU3RyaW5nICdcW+ioiFxdfOW3suWVn+eUqHxHUkVFTnxSRUQnIHwgRm9yRWFjaC1PYmplY3QgeyAk
Xy5MaW5lLlRyaW0oKSB9IHwgU2VsZWN0LU9iamVjdCAtTGFzdCAzOyBTZXQtQ29udGVudCAoSm9pbi1QYXRoICRMb2dEaXIgJ0EucHJvZ3Jlc3MnKSAnMTAw
IMK3IOWujCcgLUVuY29kaW5nIFVURjggfSB9LA0KICAgIEB7IGlkID0gJ0InOyB6aCA9ICfnpLrnr4Q6cHl0aG9uIOW8leaTjuiHqua4rChNREwyNTYpJzsg
YXJncyA9IEAoJFZJQSwgJExvZ0RpciwgJFB5U3RlcFNlYyk7IHJ1biA9IHsgcGFyYW0oJFZJQSwgJExvZ0RpciwgJFNlYykgU2V0LUxvY2F0aW9uICRWSUE7
IFNldC1Db250ZW50IChKb2luLVBhdGggJExvZ0RpciAnQi5wcm9ncmVzcycpICcyMCDCtyBzZWxmdGVzdCcgLUVuY29kaW5nIFVURjgNCiAgICAgICAgJGVu
ZyA9ICIkVklBXHN1cHBvcnRpdmUgbW9kdWxlc1xyZWdpc3RyeVxDR0NfTURMMjU2X0FpVmVyYkJyaWRnZV92MDEwMC5weSI7IGlmICgtbm90IChUZXN0LVBh
dGggJGVuZykpIHsgIltSRURdICRlbmcg5LiN5ZyoIjsgcmV0dXJuIH0NCiAgICAgICAgJGpzb24gPSAoQCgkZW5nLCAnLS1zZWxmdGVzdCcpIHwgQ29udmVy
dFRvLUpzb24gLUNvbXByZXNzKTsgJGI2NCA9IFtDb252ZXJ0XTo6VG9CYXNlNjRTdHJpbmcoW1RleHQuRW5jb2RpbmddOjpVVEY4LkdldEJ5dGVzKCRqc29u
KSkNCiAgICAgICAgJHdyYXAgPSAiaW1wb3J0IGJhc2U2NCxqc29uLG9zLHN5cyx0aHJlYWRpbmcscnVucHk7IGE9anNvbi5sb2FkcyhiYXNlNjQuYjY0ZGVj
b2RlKHN5cy5hcmd2WzFdKS5kZWNvZGUoJ3V0Zi04JykpOyB0aHJlYWRpbmcuVGltZXIoJFNlYywgbGFtYmRhOiAoc3lzLnN0ZG91dC5mbHVzaCgpLCBvcy5f
ZXhpdCgxMjQpKSkuc3RhcnQoKTsgc3lzLmFyZ3Y9YTsgcnVucHkucnVuX3BhdGgoYVswXSwgcnVuX25hbWU9J19fbWFpbl9fJykiDQogICAgICAgICYgcHl0
aG9uIC1jICR3cmFwICRiNjQgMj4mMSB8IFNlbGVjdC1TdHJpbmcgJ1xb6KiIXF18RkFJTCcgfCBGb3JFYWNoLU9iamVjdCB7ICRfLkxpbmUuVHJpbSgpIH07
ICJyYyAkTEFTVEVYSVRDT0RFIjsgU2V0LUNvbnRlbnQgKEpvaW4tUGF0aCAkTG9nRGlyICdCLnByb2dyZXNzJykgJzEwMCDCtyDlrownIC1FbmNvZGluZyBV
VEY4IH0gfSkNCiAgSW52b2tlLVZDRHVhbExhbmUgLUxhbmVzICRMYW5lcyAtTG9nRGlyICRMb2dEaXINCn0gZWxzZSB7DQogICMg6YCZ6KOh5pS+5L2g55qE
6LuK6YGTO+avj+mBk+WPr+WvqyA8TG9nRGlyPlw8aWQ+LnByb2dyZXNzID0gIjAuLjEwMCDCtyDmloflrZciIOiuk+mAsuW6puaineWLlTtweXRob24g6LWw
IEludm9rZS1WQ1B5dGhvbijkuLvln7fooYznt5Ip5oiW6LuK6YGT5YWn5ZCM5qij55qEIGJhc2U2NCDljIXms5UNCiAgJExhbmVzID0gQCgpDQogIGlmICgk
TGFuZXMuQ291bnQpIHsgSW52b2tlLVZDRHVhbExhbmUgLUxhbmVzICRMYW5lcyAtTG9nRGlyICRMb2dEaXIgfSBlbHNlIHsgJHNjcmlwdDpWZXJkaWN0cy5B
ZGQoIlvpqqjmnrZdIOaykuWumue+qei7iumBkzropIfoo73mnKzmqpTmlLkgYCRMYW5lcyzmiJbliqAgLURlbW8g55yL56S656+EIikgfQ0KfQ0KU2hvdy1W
Q1N1bW1hcnkgLVRpdGxlICRUaXRsZSAtTG9nRGlyICRMb2dEaXINCg==
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
$B64Gov = @'
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJDR0MgUmVnaXN0cnlHb3Zlcm5vciB2MDEwNSDigJQodjAxMDU6bGF3
IOWLleipnumAmueUqOWMliBsYXcgLS1maWxlIDzms5Xmop0ganNvbj4oaWQvemgv4oCmKSznhKEgLS1maWxlIOS7jeaYryBMMTE2Oyh2MDEwNDpfcmlkIOaV
tOWIl+mHjeikh+aUueOAjOavj+asoeWHuuePvuOAjeW6j+iZnyjkuYvliY3lhannrYbph43opIfmi7/lkIzkuIAgaW5kZXgg5LuN5pKeKTtkb3duc3RyZWFt
IOaUueOAjOaXj+WQjeWcqOWtkOezu+e1seaoueS4iuWwseeul+OAjShwYW5vcmFtYV94Y2hlY2sg6YCZ56iu54Sh5YmN57a05pePKTvlraTmnKzkuIvmlL4g
LS1hZG9wdC1vcnBoYW5zKOaTjeS9nOWToeijgeWumuW+jOaJjemWizrmr43njajmnKzmkKzliLDlrZDns7vntbHlpL4s5q+N5qiZIFJFVElSRUQgcmVwbGFj
ZWRfYnkpOyh2MDEwMzorZG93bnN0cmVhbSA9IEYxIOWQjOaooee1hOaXj+WcqOavjeiIh+WtkDrmr43ns7vntbHlia/mnKzpgIDlvbnkuIvmlL4o5a2Q57O7
57Wx5bC+54mIIOKJpSDmr43lia/mnKzmiY3pgIA75ZCm5YmH5YiX44CM5b6F6KOB44CNKTvlkIjmiJDpjbUgX3JpZCDliqDluo/omZ8o5pW05YiX6YeN6KSH
5pmCKTsrbGF3ID0gTDExNiDkuIrkuIvliIblt6XlvovlhaXlhoo7KHYwMTAyOityZXNvbHZlID0g57SF6KGo5YiG5Y2A5YiX566hOlQyIOeEoeS4u+mNtSDi
hpIg5om+5pyA5bCP57WE5ZCI6Y21KOKJpDMg5qyELERGMDYg5YWB6Kix57WE5ZCI6Y21KeaIluWQiOaIkOWIl+mNtSBfcmlkO+mBjuaZgueJiOacrOaXjyji
gKZfdjAyXy9fdjAzX+KApiDlkIzliY3ntrQp4oaSIOeVmeacgOmrmOeJiCzlhbbppJjpgIDlvbnluLYgcmVwbGFjZWRfYnkoVkNHQyDoh6rlrrblhornp7sg
X3N1cGVyc2VkZWQs5a2Q57O757Wx5YaK5Y+q5Ye66KOB5a6a57Wm5a6D5YCR55qEIG1hbmFnZXIpO1QzIOa8guenuyDihpIg6IiK6aCt6YCA5b255paw6aCt
5o6l6JmfO+WFqOmDqOWvqyBWSUFfS2V5UnVsaW5nc192MDEwMC5qc29uLOS4jeeisOW8leaTjuWOn+Wni+eivCzkuI3mr4Dku7vkvZXlhoo7KHYwMTAxOitw
dWxsID0gVkNHQyDoh6rlt7HnmoTlip/og73nn6npmaMv6KGo6aCt5YaK5L6d6Y216K6A5Zue6JmfKOS5i+WJjSBWQ0dDIDAvMTY1MTQg5pyJ6Jmf5bCx5piv
5rKS5Lq65pu/5a6DIHB1bGwpOythbm5vdGF0ZSA9IOeUqOWFqOaZryBBU1Qg5bCN5q+P5YCLIENMUy9GTkMvTElCIOazqOWFpeWIhumhnuiIh+iqquaYjuWI
sOWBtOWGiiBWSUFfQXN0QW5ub3RhdGlvbnNfPFNVQj5fdjAxMDAuanNvbizkuI3mlLnljp/lp4vnorwpOuihqOmgreWGiiArIOWKn+iDveefqemZo+eahOih
neeqgemhr+ekuiDihpIg5ris6KmmIOKGkiDnmbzomZ8o5pON5L2c5ZOh5LukIDIwMjYtMTAtMDY65a2Q57O757Wx5pyJ5Ym16YCg566h55CG5qyKIMK3IOav
jeezu+e1semhr+ekuuihneeqgSDCtyDoo4Hlvozmr43ns7vntbHpgJrpgY7muKzoqabpoa/npLrnt6jomZ8gwrcg6Jmf5Ye654++5a2Q57O757Wx57SA6YyE
5Lim6YG15a6IKeOAggrkuInns7vntbHlkIToh6rnmbvoqJgoVlJOIHYwMTIzL3YwMTI0IMK3IFZERiB2MDEzMS92MDEzMiDCtyBWQ0dDIOacrOW8leaTjiBy
ZWdpc3Rlcik75pys5byV5pOO5Y+q6K6A5a2Q57O757Wx5YaKLOWPquWvq+iHquW3seWbm+iZlToKICByZWdpc3RyeS9WQ0dDX1RhYmxlSGVhZGVyX3YqLmpz
b24gwrcgcmVnaXN0cnkvVkNHQ19GdW5jdGlvbk1hdHJpeF92Ki5qc29uKFZDR0Mg6Ieq5bex55qE55m76KiYKQogIHJlZ2lzdHJ5L1ZJQV9UYWJsZU51bWJl
cnNfdjAxMDAuanNvbijooajomZ8gU1NPVC1WQ0dDLTxTVUI+LVRCTE5OTk4pwrcgcmVnaXN0cnkvVklBX1JlZ2lzdHJ5TnVtYmVyc192MDEwMC5qc29uKOWK
n+iDveiZnyBWSUEtPFNVQj4tPEtJTkQ+Tk5OWy1GTkNOTk4vLUNMU05OTl0s5om/IFZJQV9OdW1iZXJpbmdfU1NPVCDliLY75bey5ZyoIE51bWJlckJvb2tz
IOeahOayv+eUqOS4jemHjeeZvCkKICBkb2NzL2hhbmRvZmYvYWkvVkNHQ19SZWdpc3RyeUdvdmVybkNhcmRfPOaXpT4ubWQgwrcgVklBX1JlcG9ydHMvcmV2
aWV3L3ZjZ2NfcmVnaXN0cnkvCuWLleipnjoKICByZWdpc3RlciAtLWFwcGx5ICAgVkNHQyDoh6rlt7HnmoTooajpoK3lhooo6Y6W566h5o6n5YaKKeiIh+WK
n+iDveefqemZoyhzdXBwb3J0aXZlIG1vZHVsZXMg5bC+54mIIC5weSkKICBnb3Zlcm4gWy0tYXBwbHldICAg6K6A5LiJ57O757Wx5YaKIOKGkiDooZ3nqoEo
57SFID0g5pOL6JmfIC8g6buDID0g5o+Q6YaS5LiN5pOLKeKGkiDpm7bntIXpoIXph43muKwg4oaSIOeZvOiZn+Wvq+WGiiDihpIg5Ye65Y2hCiAgICAgIOih
qDpUMSDlkIwgdGlkIOi3qOezu+e1seeVsOmgrT3ntIUgwrcgVDIg54Sh5Li76Y21Pee0hSDCtyBUMyDmlLnpoK3mvILnp7so5bey6JmfKT3ntIUgwrcgVDQg
5ZCM6Jmf5aSa6KGoPee0hSDCtyBUNSDlkIzmrITlkI3nlbDlnoso6Leo6KGoKT3pu4MgwrcgVDYg5qC85YWn5bei54uAL+aVuOWtl+WtmOWtl+S4si/pnZ4g
c25ha2U96buDCiAgICAgIOWKnzpGMSDlkIzmqKHntYTml4/lnKjlhanns7vntbE957SFIMK3IEYyIEdPTkUg54Sh5pu/5LujPem7gyDCtyBGMyDnm7jkvLwo
5ZCM5ZCNL+WQjCBib2R5IOi3qOezu+e1sSk96buDIMK3IEY0IEFTVCDlpLHmlZc96buDIMK3IEY1IFJFVElSRUQg54ShIHJlcGxhY2VkX2J5Pee0hQogICAg
ICDmuKw66KGoID0g6YeN6LyJ5L6G5rqQLOashOWFqOWcqOOAgeS4u+mNtemdnuepuuS4jemHjeikh+OAgeWei+WIpeWkmuaVuOebuOespjvlip8gPSDmqpTk
u43lnKjmqLnkuIrkuJQgQVNUIOWPr+WJluOAgemNteS7jeWtmOWcqAogIC0tc2VsZnRlc3QgICAgICAgICB0ZW1wIOaymeebkgrmspnnm5LpjbU6VklBX1JP
T1QKIiIiCmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCiMgPT09PT0gW1ZJQTpBQ0NFTC1CUklER0U6djAxMDBdIFN1cGVyQWNjZWwg5Yqg
6YCf5Zmo5qmLKOaJuTEwMiDlhajmqLnlsI7lhaXku6Q7Z3JhY2VmdWwg6Zu26KGM54K66K6K5pu0KSA9PT09PQp0cnk6CiAgICBpbXBvcnQgc3lzIGFzIF9z
YV9zeXMKICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aCBhcyBfc2FfUGF0aAogICAgX3NhX3AgPSBfc2FfUGF0aChfX2ZpbGVfXykucmVzb2x2ZSgpCiAg
ICB3aGlsZSBfc2FfcC5wYXJlbnQgIT0gX3NhX3A6CiAgICAgICAgaWYgKF9zYV9wIC8gInN1cHBvcnRpdmUgbW9kdWxlcyIgLyAiVklBX1N1cGVyQWNjZWxf
TW9kdWxlLnB5IikuZXhpc3RzKCk6CiAgICAgICAgICAgIF9zYV9zeXMucGF0aC5pbnNlcnQoMCwgc3RyKF9zYV9wIC8gInN1cHBvcnRpdmUgbW9kdWxlcyIp
KQogICAgICAgICAgICBicmVhawogICAgICAgIF9zYV9wID0gX3NhX3AucGFyZW50CiAgICBpbXBvcnQgVklBX1N1cGVyQWNjZWxfTW9kdWxlIGFzIFZJQV9B
Q0NFTCAgIyBub3FhOiBGNDAxCmV4Y2VwdCBJbXBvcnRFcnJvcjoKICAgIFZJQV9BQ0NFTCA9IE5vbmUKIyA9PT09PSBbVklBOkFDQ0VMLUJSSURHRTpFTkRd
ID09PT09CgppbXBvcnQgZGF0ZXRpbWUKaW1wb3J0IGpzb24KaW1wb3J0IG9zCmltcG9ydCByZQppbXBvcnQgc2h1dGlsCmltcG9ydCBzeXMKaW1wb3J0IHRl
bXBmaWxlCmZyb20gY29sbGVjdGlvbnMgaW1wb3J0IENvdW50ZXIsIGRlZmF1bHRkaWN0CmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAoKTUUgPSBQYXRoKF9f
ZmlsZV9fKS5yZXNvbHZlKCkKTkFNRSA9IE1FLnN0ZW0KVEFHID0gInYwMTA1IgpTVUJTID0gKCJWQ0dDIiwgIlZERiIsICJWUk4iKQpMT0NLRURfUkUgPSBy
ZS5jb21waWxlKHIiXihWSUFfUG9saWN5fFZJQV9OdW1iZXJpbmd8VklBX1VJX0Zvcm1hdExvY2t8VklBX0NlbnRyYWxffFZJQV9TU09UX3xWSUFfRmluYWxQ
YXJhbWV0ZXJzfFZJQV9Xb3JrZmxvd198VklBX0Vzc2VudGlhX3xWSUFfW0EtWmEtel0qTG9ja3xWSUFfW0EtWmEtel0qTGF3fFZJQV9bQS1aYS16XSpHYXRl
fFZJQV9bQS1aYS16XSpSZWdpc3RyeXxWSUFfQ2Fub25ffFZJQV9NYXN0ZXJHb3Zlcm5hbmNlfEdvdmVybmFuY2VSZWdpc3RyeXxWSUFfRGF0YUZyYW1lfFZJ
QV9PdXRwdXRfSGVhZGVyfFZJQV9UYWJsZU51bWJlcnN8VklBX1JlZ2lzdHJ5TnVtYmVycykiKQoKIyA9PT09PSBbVklBOlRBQkxFLUhFQURFUjp2MDEwMF0g
6KGo6aCt55m76KiY5YWx55So5q61KOWtkOezu+e1seiHquWJteiHqueuoTtWQ0dDIOWPquiugDvkuInns7vntbHlkITluLbkuIDku70s6Zu255u45L6dKT09
PT09Cl9USF9FWENMID0geyJyZWZlcmVuY2VzIiwgImludGFrZSIsICJfc3VwZXJzZWRlZCIsICJWSUFfUmV0aXJlZEVuZ2luZXMiLCAiX3F1YXJhbnRpbmVf
cGlwX3ZlbmRvciIsICJfX3B5Y2FjaGVfXyIsICJfZGYiLCAiX3F1YXJhbnRpbmUiLCAiVklBX051bWJlckJvb2tzIn0KX1RIX0lTTyA9IF9faW1wb3J0X18o
InJlIikuY29tcGlsZShyIl5cZHs0fS1cZHsyfS1cZHsyfShbVCBdXGR7Mn06XGR7Mn0oOlxkezJ9KT8pPyIpCl9USF9OVU0gPSBfX2ltcG9ydF9fKCJyZSIp
LmNvbXBpbGUociJeLT9cZCsoXC5cZCspPyQiKQoKCmRlZiBfdGhfdm51bShuYW1lKToKICAgIGltcG9ydCByZSBhcyBfcmUKICAgIG0gPSBfcmUuc2VhcmNo
KHIiX3YoXGR7Miw0fSlbQS1aYS16MC05XSooPzpcLltBLVphLXowLTldKyk/JCIsIG5hbWUpCiAgICByZXR1cm4gaW50KG0uZ3JvdXAoMSkpIGlmIG0gZWxz
ZSAtMQoKCmRlZiBfdGhfZmFtaWx5KG5hbWUpOgogICAgaW1wb3J0IHJlIGFzIF9yZQogICAgZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9QCiAgICBy
ZXR1cm4gX3JlLnN1YihyIl92XGR7Miw0fVtBLVphLXowLTldKiQiLCAiIiwgX3JlLnN1YihyIl9zaGFbMC05YS1mXXs4LH0kIiwgIiIsIF9QKG5hbWUpLnN0
ZW0pKQoKCmRlZiBfdGhfcmVhZChwKToKICAgIHJhdyA9IHAucmVhZF9ieXRlcygpCiAgICBmb3IgZW5jIGluICgidXRmLTgtc2lnIiwgInV0Zi0xNiIsICJj
cDk1MCIpOgogICAgICAgIHRyeToKICAgICAgICAgICAgcmV0dXJuIHJhdy5kZWNvZGUoZW5jKQogICAgICAgIGV4Y2VwdCBVbmljb2RlRGVjb2RlRXJyb3I6
CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICByZXR1cm4gIiIKCgpkZWYgX3RoX3VuaWZvcm0oZGN0cyk6CiAgICBzaXplcyA9IHNvcnRlZChsZW4oZCkgZm9y
IGQgaW4gZGN0cykKICAgIGlmIG5vdCBzaXplczoKICAgICAgICByZXR1cm4gRmFsc2UKICAgIG1lZCA9IHNpemVzW2xlbihzaXplcykgLy8gMl0gb3IgMQog
ICAgdW5pb24gPSBzZXQoKQogICAgZm9yIGQgaW4gZGN0czoKICAgICAgICB1bmlvbiB8PSBzZXQoZC5rZXlzKCkpCiAgICByZXR1cm4gbGVuKHVuaW9uKSA8
PSAzICogbWVkCgoKZGVmIF90aF90YWJsZXMob2JqKToKICAgICIiIueJqeS7tiDihpIge+ihqOWQjTogcm93c307bGlzdC1vZi1kaWN0IC8gZGljdC1vZi1k
aWN0KOmNtemAsiBrZXkg5qyEKS8g5bei54uA5bqV5LiL55qE5ZCM6aGeO+aYoOWwhOiIh+e0lOioreWumuS4jeeVtuihqOOAgiIiIgogICAgaWYgaXNpbnN0
YW5jZShvYmosIGxpc3QpOgogICAgICAgIHJldHVybiB7InJvd3MiOiBvYmp9IGlmIG9iaiBhbmQgYWxsKGlzaW5zdGFuY2UoeCwgZGljdCkgZm9yIHggaW4g
b2JqKSBhbmQgX3RoX3VuaWZvcm0ob2JqKSBlbHNlIHt9CiAgICBpZiBub3QgaXNpbnN0YW5jZShvYmosIGRpY3QpOgogICAgICAgIHJldHVybiB7fQogICAg
dmFscyA9IGxpc3Qob2JqLnZhbHVlcygpKQogICAgaWYgdmFscyBhbmQgYWxsKGlzaW5zdGFuY2UodiwgZGljdCkgZm9yIHYgaW4gdmFscykgYW5kIGxlbihv
YmopID49IDI6CiAgICAgICAgcmV0dXJuIHsicm93cyI6IFtkaWN0KHsia2V5Ijoga30sICoqdikgZm9yIGssIHYgaW4gb2JqLml0ZW1zKCldfSBpZiBfdGhf
dW5pZm9ybSh2YWxzKSBlbHNlIHt9CiAgICBvdXQgPSB7fQogICAgZm9yIGssIHYgaW4gb2JqLml0ZW1zKCk6CiAgICAgICAgaWYgaXNpbnN0YW5jZSh2LCBs
aXN0KSBhbmQgdiBhbmQgYWxsKGlzaW5zdGFuY2UoeCwgZGljdCkgZm9yIHggaW4gdikgYW5kIF90aF91bmlmb3JtKHYpOgogICAgICAgICAgICBvdXRba10g
PSB2CiAgICAgICAgZWxpZiBpc2luc3RhbmNlKHYsIGRpY3QpIGFuZCBsZW4odikgPj0gMiBhbmQgYWxsKGlzaW5zdGFuY2UoeCwgZGljdCkgZm9yIHggaW4g
di52YWx1ZXMoKSkgYW5kIF90aF91bmlmb3JtKGxpc3Qodi52YWx1ZXMoKSkpOgogICAgICAgICAgICBvdXRba10gPSBbZGljdCh7ImtleSI6IGtrfSwgKip2
dikgZm9yIGtrLCB2diBpbiB2Lml0ZW1zKCldCiAgICByZXR1cm4gb3V0CgoKZGVmIF90aF9sb2FkX3RhYmxlcyhwKToKICAgIGltcG9ydCBjc3YgYXMgX2Nz
dgogICAgaW1wb3J0IGlvIGFzIF9pbwogICAgaW1wb3J0IGpzb24gYXMgX2pzb24KICAgIHR4dCA9IF90aF9yZWFkKHApCiAgICBleHQgPSBwLnN1ZmZpeC5s
b3dlcigpCiAgICBpZiBleHQgPT0gIi5qc29ubCI6CiAgICAgICAgcm93cyA9IFtfanNvbi5sb2FkcyhsbikgZm9yIGxuIGluIHR4dC5zcGxpdGxpbmVzKCkg
aWYgbG4uc3RyaXAoKV0KICAgICAgICByZXR1cm4geyJyb3dzIjogcm93c30gaWYgcm93cyBhbmQgYWxsKGlzaW5zdGFuY2UociwgZGljdCkgZm9yIHIgaW4g
cm93cykgZWxzZSB7fQogICAgaWYgZXh0ID09ICIuY3N2IjoKICAgICAgICByb3dzID0gbGlzdChfY3N2LkRpY3RSZWFkZXIoX2lvLlN0cmluZ0lPKHR4dCkp
KQogICAgICAgIHJldHVybiB7InJvd3MiOiByb3dzfSBpZiByb3dzIGVsc2Uge30KICAgIHJldHVybiBfdGhfdGFibGVzKF9qc29uLmxvYWRzKHR4dCkpCgoK
ZGVmIF90aF9wcm9maWxlKHJvd3MpOgogICAgIiIi4oaSIChjb2x1bW5zW3tuYW1lLGR0eXBlLHJlcXVpcmVkLHBrfV0sIGtleXMsIGlzc3VlcykiIiIKICAg
IGltcG9ydCByZSBhcyBfcmUKICAgIGZyb20gY29sbGVjdGlvbnMgaW1wb3J0IENvdW50ZXIgYXMgX0MKICAgIG4gPSBsZW4ocm93cykKICAgIGNvbHMgPSB7
fQogICAgZm9yIHIgaW4gcm93czoKICAgICAgICBmb3IgaywgdiBpbiByLml0ZW1zKCk6CiAgICAgICAgICAgIGMgPSBjb2xzLnNldGRlZmF1bHQoaywgeyJ0
IjogX0MoKSwgIm51bGxzIjogMCwgIm51bXN0ciI6IDAsICJkYXRlc3RyIjogMCwgIm5lc3RlZCI6IDAsICJ2YWxzIjogc2V0KCksICJkdXAiOiBGYWxzZX0p
CiAgICAgICAgICAgIGlmIHYgaXMgTm9uZSBvciB2ID09ICIiOgogICAgICAgICAgICAgICAgY1sibnVsbHMiXSArPSAxCiAgICAgICAgICAgICAgICBjb250
aW51ZQogICAgICAgICAgICBpZiBpc2luc3RhbmNlKHYsIGJvb2wpOgogICAgICAgICAgICAgICAgdCA9ICJib29sIgogICAgICAgICAgICBlbGlmIGlzaW5z
dGFuY2UodiwgaW50KToKICAgICAgICAgICAgICAgIHQgPSAiaW50IgogICAgICAgICAgICBlbGlmIGlzaW5zdGFuY2UodiwgZmxvYXQpOgogICAgICAgICAg
ICAgICAgdCA9ICJmbG9hdCIKICAgICAgICAgICAgZWxpZiBpc2luc3RhbmNlKHYsIChkaWN0LCBsaXN0KSk6CiAgICAgICAgICAgICAgICB0ID0gImpzb24i
CiAgICAgICAgICAgICAgICBjWyJuZXN0ZWQiXSArPSAxCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICB0ID0gInN0ciIKICAgICAgICAgICAg
ICAgIHMgPSBzdHIodikuc3RyaXAoKQogICAgICAgICAgICAgICAgaWYgX1RIX05VTS5tYXRjaChzKToKICAgICAgICAgICAgICAgICAgICBjWyJudW1zdHIi
XSArPSAxCiAgICAgICAgICAgICAgICBlbGlmIF9USF9JU08ubWF0Y2gocyk6CiAgICAgICAgICAgICAgICAgICAgY1siZGF0ZXN0ciJdICs9IDEKICAgICAg
ICAgICAgY1sidCJdW3RdICs9IDEKICAgICAgICAgICAgaWYgdCAhPSAianNvbiI6CiAgICAgICAgICAgICAgICBpZiB2IGluIGNbInZhbHMiXToKICAgICAg
ICAgICAgICAgICAgICBjWyJkdXAiXSA9IFRydWUKICAgICAgICAgICAgICAgIGNbInZhbHMiXS5hZGQodikKICAgIGNvbHVtbnMsIGtleXMsIGlzc3VlcyA9
IFtdLCBbXSwgW10KICAgIGZvciBrLCBjIGluIGNvbHMuaXRlbXMoKToKICAgICAgICBraW5kcyA9IHNldChjWyJ0Il0pCiAgICAgICAgaWYgeyJpbnQiLCAi
ZmxvYXQifSA8PSBraW5kczoKICAgICAgICAgICAga2luZHMuZGlzY2FyZCgiaW50IikKICAgICAgICBtYWpvciA9IGNbInQiXS5tb3N0X2NvbW1vbigxKVsw
XVswXSBpZiBjWyJ0Il0gZWxzZSAic3RyIgogICAgICAgIGR0eXBlID0gImRhdGUiIGlmIChtYWpvciA9PSAic3RyIiBhbmQgY1siZGF0ZXN0ciJdIGFuZCBj
WyJkYXRlc3RyIl0gPT0gY1sidCJdWyJzdHIiXSkgZWxzZSBtYWpvcgogICAgICAgIGlmIGxlbihraW5kcykgPiAxOgogICAgICAgICAgICBpc3N1ZXMuYXBw
ZW5kKCLmt7flnos6JXMiICUgaykKICAgICAgICBpZiBjWyJudW1zdHIiXToKICAgICAgICAgICAgaXNzdWVzLmFwcGVuZCgi5pW45a2X5a2Y5a2X5LiyOiVz
IiAlIGspCiAgICAgICAgaWYgY1sibmVzdGVkIl06CiAgICAgICAgICAgIGlzc3Vlcy5hcHBlbmQoIuagvOWFp+W3oueLgDolcyIgJSBrKQogICAgICAgIGlm
IG5vdCBfcmUubWF0Y2gociJeW2EtejAtOV9dKyQiLCBzdHIoaykpOgogICAgICAgICAgICBpc3N1ZXMuYXBwZW5kKCLpnZ5zbmFrZTolcyIgJSBrKQogICAg
ICAgIHVuaXF1ZSA9IChuID4gMCBhbmQgY1sibnVsbHMiXSA9PSAwIGFuZCBub3QgY1siZHVwIl0gYW5kIGR0eXBlIGluICgic3RyIiwgImludCIsICJkYXRl
IikpCiAgICAgICAgaWYgdW5pcXVlOgogICAgICAgICAgICBrZXlzLmFwcGVuZChrKQogICAgICAgIGNvbHVtbnMuYXBwZW5kKHsibmFtZSI6IGssICJkdHlw
ZSI6IGR0eXBlLCAicmVxdWlyZWQiOiBjWyJudWxscyJdID09IDAsICJwayI6IEZhbHNlfSkKICAgIGlmIGtleXM6CiAgICAgICAgZm9yIGNvbCBpbiBjb2x1
bW5zOgogICAgICAgICAgICBpZiBjb2xbIm5hbWUiXSA9PSBrZXlzWzBdOgogICAgICAgICAgICAgICAgY29sWyJwayJdID0gVHJ1ZQogICAgZWxzZToKICAg
ICAgICBpc3N1ZXMuYXBwZW5kKCLnhKHkuLvpjbXlgJnpgbgiKQogICAgcmV0dXJuIGNvbHVtbnMsIGtleXNbOjNdLCBpc3N1ZXMKCgpkZWYgX3RoX3NoYShj
b2x1bW5zKToKICAgIGltcG9ydCBoYXNobGliIGFzIF9oCiAgICBpbXBvcnQganNvbiBhcyBfanNvbgogICAgcmV0dXJuIF9oLnNoYTI1NihfanNvbi5kdW1w
cyhbW2NbIm5hbWUiXSwgY1siZHR5cGUiXV0gZm9yIGMgaW4gY29sdW1uc10sIGVuc3VyZV9hc2NpaT1GYWxzZSkuZW5jb2RlKCJ1dGYtOCIpKS5oZXhkaWdl
c3QoKVs6MTZdCgoKZGVmIF90aF90aWQoZmFtaWx5LCB0YWJsZSk6CiAgICBpbXBvcnQgcmUgYXMgX3JlCiAgICByZXR1cm4gX3JlLnN1YihyIlteYS16MC05
X10rIiwgIl8iLCAoZmFtaWx5ICsgKCIiIGlmIHRhYmxlID09ICJyb3dzIiBlbHNlICJfIiArIHRhYmxlKSkubG93ZXIoKSkuc3RyaXAoIl8iKQoKCmRlZiBf
dGhfcmVnaXN0ZXIoc3ViLCBzb3VyY2VzLCBib29rX2Rpciwgbm93LCBhcHBseT1UcnVlLCByZWxfcm9vdD1Ob25lKToKICAgICIiIuaOgyBzb3VyY2VzKOaq
lOWIl+ihqCnihpIg55m76KiY6YCyIGJvb2tfZGlyLzxzdWI+X1RhYmxlSGVhZGVyX3YjIyMjLmpzb24o5Y+q5aKeOuWQjCBzaGEg5LiN5YuVO+aUuemgreS4
lOacque3qOiZnyDihpIg5pu05pawICsgaGlzdG9yeTvmlLnpoK3kuJTlt7Lnt6jomZ8g4oaSIOS4jeWLleWOn+WIlyzlj6bplosgPHRpZD5faDIg55WZ55m9
ID0g6YG15a6I5pei55m86JmfKeOAgiIiIgogICAgaW1wb3J0IGpzb24gYXMgX2pzb24KICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aCBhcyBfUAogICAg
aGl0cyA9IHNvcnRlZChfUChib29rX2RpcikuZ2xvYihzdWIgKyAiX1RhYmxlSGVhZGVyX3YqLmpzb24iKSwga2V5PWxhbWJkYSBxOiBfdGhfdm51bShxLm5h
bWUpKQogICAgaWYgaGl0czoKICAgICAgICBib29rID0gX2pzb24ubG9hZHMoX3RoX3JlYWQoaGl0c1stMV0pKQogICAgICAgIGZwID0gaGl0c1stMV0KICAg
IGVsc2U6CiAgICAgICAgZnAgPSBfUChib29rX2RpcikgLyAoc3ViICsgIl9UYWJsZUhlYWRlcl92MDEwMC5qc29uIikKICAgICAgICBib29rID0geyJzY2hl
bWEiOiAiVklBLlRhYmxlSGVhZGVyLnYxIiwgInN1YiI6IHN1YiwgInZlcnNpb24iOiAidjAxMDAiLCAicnVsZSI6ICLlrZDns7vntbHoh6rlibXoh6rnrqEo
TDExNCDikaDikaIpO3RhYmxlX25vIOeVmeeZveW+heavjeezu+e1seeZvOiZnzvlt7LnmbzomZ/nmoTooajpoK3pjpbmrbss5pS56aCt5Y+m6ZaLIF9oMjvl
j6rlop7kuI3muJsiLCAiY3JlYXRlZF9hdCI6IG5vdywgInRhYmxlcyI6IHt9fQogICAgdGFibGVzID0gYm9vay5zZXRkZWZhdWx0KCJ0YWJsZXMiLCB7fSkK
ICAgIGNvdW50cyA9IHsiTkVXIjogMCwgIlNBTUUiOiAwLCAiVVBEQVRFRCI6IDAsICJMT0NLRURfTkVXX0giOiAwLCAiU0tJUCI6IDB9CiAgICByb3dzX291
dCA9IFtdCiAgICBmb3IgcCBpbiBzb3VyY2VzOgogICAgICAgIHRyeToKICAgICAgICAgICAgdGJzID0gX3RoX2xvYWRfdGFibGVzKHApCiAgICAgICAgZXhj
ZXB0IEV4Y2VwdGlvbjogICMgbm9xYTogQkxFMDAxIOKAlCDlo57lhoo655m76KiY54K65LiN5Y+v6K6ALOS6pOS6ugogICAgICAgICAgICBjb3VudHNbIlNL
SVAiXSArPSAxCiAgICAgICAgICAgIHJvd3Nfb3V0LmFwcGVuZCh7InNvdXJjZSI6IHN0cihwKSwgInN0YXR1cyI6ICJVTlJFQURBQkxFIn0pCiAgICAgICAg
ICAgIGNvbnRpbnVlCiAgICAgICAgaWYgbm90IHRiczoKICAgICAgICAgICAgY291bnRzWyJTS0lQIl0gKz0gMQogICAgICAgICAgICBjb250aW51ZQogICAg
ICAgIHNyYyA9IChwLnJlbGF0aXZlX3RvKHJlbF9yb290KS5hc19wb3NpeCgpIGlmIHJlbF9yb290IGVsc2UgcC5hc19wb3NpeCgpKQogICAgICAgIGZvciB0
LCByb3dzIGluIHRicy5pdGVtcygpOgogICAgICAgICAgICBjb2x1bW5zLCBrZXlzLCBpc3N1ZXMgPSBfdGhfcHJvZmlsZShyb3dzKQogICAgICAgICAgICBz
aGEgPSBfdGhfc2hhKGNvbHVtbnMpCiAgICAgICAgICAgIHRpZCA9IF90aF90aWQoX3RoX2ZhbWlseShwLm5hbWUpLCB0KQogICAgICAgICAgICBlbnQgPSB0
YWJsZXMuZ2V0KHRpZCkKICAgICAgICAgICAgaWYgZW50IGlzIE5vbmU6CiAgICAgICAgICAgICAgICB0YWJsZXNbdGlkXSA9IHsidGlkIjogdGlkLCAic3Vi
Ijogc3ViLCAic291cmNlIjogc3JjLCAidGFibGUiOiB0LCAiY29sdW1ucyI6IGNvbHVtbnMsICJrZXlzIjoga2V5cywgImhlYWRlcl9zaGEiOiBzaGEsICJy
b3dzX3NlZW4iOiBsZW4ocm93cyksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiaXNzdWVzIjogaXNzdWVzLCAic3RhdHVzIjogIkFDVElWRSIs
ICJ0YWJsZV9ubyI6ICIiLCAicmVnaXN0ZXJlZF9hdCI6IG5vdywgImhpc3RvcnkiOiBbXX0KICAgICAgICAgICAgICAgIGNvdW50c1siTkVXIl0gKz0gMQog
ICAgICAgICAgICAgICAgc3QgPSAiTkVXIgogICAgICAgICAgICBlbGlmIGVudC5nZXQoImhlYWRlcl9zaGEiKSA9PSBzaGE6CiAgICAgICAgICAgICAgICBl
bnRbInJvd3Nfc2VlbiJdID0gbGVuKHJvd3MpCiAgICAgICAgICAgICAgICBlbnRbImlzc3VlcyJdID0gaXNzdWVzCiAgICAgICAgICAgICAgICBlbnRbInNv
dXJjZSJdID0gc3JjCiAgICAgICAgICAgICAgICBjb3VudHNbIlNBTUUiXSArPSAxCiAgICAgICAgICAgICAgICBzdCA9ICJTQU1FIgogICAgICAgICAgICBl
bGlmIG5vdCBlbnQuZ2V0KCJ0YWJsZV9ubyIpOgogICAgICAgICAgICAgICAgZW50LnNldGRlZmF1bHQoImhpc3RvcnkiLCBbXSkuYXBwZW5kKHsiaGVhZGVy
X3NoYSI6IGVudC5nZXQoImhlYWRlcl9zaGEiKSwgImNvbHVtbnMiOiBlbnQuZ2V0KCJjb2x1bW5zIiksICJ1bnRpbCI6IG5vd30pCiAgICAgICAgICAgICAg
ICBlbnQudXBkYXRlKGNvbHVtbnM9Y29sdW1ucywga2V5cz1rZXlzLCBoZWFkZXJfc2hhPXNoYSwgcm93c19zZWVuPWxlbihyb3dzKSwgaXNzdWVzPWlzc3Vl
cywgc291cmNlPXNyYykKICAgICAgICAgICAgICAgIGNvdW50c1siVVBEQVRFRCJdICs9IDEKICAgICAgICAgICAgICAgIHN0ID0gIlVQREFURUQiCiAgICAg
ICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICB0aWQyID0gdGlkICsgIl9oMiIKICAgICAgICAgICAgICAgIGlmIHRpZDIgbm90IGluIHRhYmxlczoKICAg
ICAgICAgICAgICAgICAgICB0YWJsZXNbdGlkMl0gPSB7InRpZCI6IHRpZDIsICJzdWIiOiBzdWIsICJzb3VyY2UiOiBzcmMsICJ0YWJsZSI6IHQsICJjb2x1
bW5zIjogY29sdW1ucywgImtleXMiOiBrZXlzLCAiaGVhZGVyX3NoYSI6IHNoYSwgInJvd3Nfc2VlbiI6IGxlbihyb3dzKSwKICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgImlzc3VlcyI6IGlzc3VlcywgInN0YXR1cyI6ICJBQ1RJVkUiLCAidGFibGVfbm8iOiAiIiwgInJlZ2lzdGVyZWRfYXQiOiBu
b3csICJoaXN0b3J5IjogW10sICJzdXBlcnNlZGVzIjogdGlkfQogICAgICAgICAgICAgICAgICAgIGVudFsiZHJpZnQiXSA9IHsibmV3X3RpZCI6IHRpZDIs
ICJzZWVuX2F0Ijogbm93fQogICAgICAgICAgICAgICAgY291bnRzWyJMT0NLRURfTkVXX0giXSArPSAxCiAgICAgICAgICAgICAgICBzdCA9ICJMT0NLRURf
TkVXX0giCiAgICAgICAgICAgIHJvd3Nfb3V0LmFwcGVuZCh7InRpZCI6IHRpZCwgInN0YXR1cyI6IHN0LCAic2hhIjogc2hhLCAiaXNzdWVzIjogaXNzdWVz
fSkKICAgIGJvb2tbInVwZGF0ZWRfYXQiXSA9IG5vdwogICAgaWYgYXBwbHk6CiAgICAgICAgX1AoYm9va19kaXIpLm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhp
c3Rfb2s9VHJ1ZSkKICAgICAgICBmcC53cml0ZV90ZXh0KF9qc29uLmR1bXBzKGJvb2ssIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGlu
Zz0idXRmLTgiKQogICAgYmxhbmsgPSBzdW0oMSBmb3IgZSBpbiB0YWJsZXMudmFsdWVzKCkgaWYgbm90IGUuZ2V0KCJ0YWJsZV9ubyIpKQogICAgcmV0dXJu
IHsiYm9vayI6IGZwLm5hbWUsICJ0YWJsZXMiOiBsZW4odGFibGVzKSwgImJsYW5rIjogYmxhbmssICJjb3VudHMiOiBjb3VudHMsICJyb3dzIjogcm93c19v
dXR9CgoKZGVmIF90aF9wdWxsKHN1YiwgYm9va19kaXIsIG51bWJlcnNfZGlyLCBub3csIGFwcGx5PVRydWUpOgogICAgIiIi5b6e5q+N57O757WxIFZJQV9U
YWJsZU51bWJlcnNfdiouanNvbiDkvp3pjbUgPHN1Yj58PHRpZD58PGhlYWRlcl9zaGE+IOiugOiZn+Whq+mAsuiHquW3seeahOihqOmgreWGiijlj6rloavn
lZnnmb075aGr5LqG5bCx6Y6W6aCtID0g6YG15a6IKeOAgiIiIgogICAgaW1wb3J0IGpzb24gYXMgX2pzb24KICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0
aCBhcyBfUAogICAgaGl0cyA9IHNvcnRlZChfUChib29rX2RpcikuZ2xvYihzdWIgKyAiX1RhYmxlSGVhZGVyX3YqLmpzb24iKSwga2V5PWxhbWJkYSBxOiBf
dGhfdm51bShxLm5hbWUpKQogICAgaWYgbm90IGhpdHM6CiAgICAgICAgcmV0dXJuIHsic3RhdHVzIjogIk5PX0JPT0siLCAiZmlsbGVkIjogMCwgImFscmVh
ZHkiOiAwLCAicGVuZGluZyI6IDAsICJsYW1wIjogIkdSQVkifQogICAgYm9vayA9IF9qc29uLmxvYWRzKF90aF9yZWFkKGhpdHNbLTFdKSkKICAgIG5iID0g
c29ydGVkKF9QKG51bWJlcnNfZGlyKS5nbG9iKCJWSUFfVGFibGVOdW1iZXJzX3YqLmpzb24iKSwga2V5PWxhbWJkYSBxOiBfdGhfdm51bShxLm5hbWUpKQog
ICAgdGFibGUgPSB7fQogICAgaWYgbmI6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkID0gX2pzb24ubG9hZHMoX3RoX3JlYWQobmJbLTFdKSkKICAgICAg
ICAgICAgdGFibGUgPSB7ZVsia2V5Il06IGVbInRhYmxlX25vIl0gZm9yIGUgaW4gZC5nZXQoImVudHJpZXMiLCBbXSkgaWYgZS5nZXQoImtleSIpIGFuZCBl
LmdldCgidGFibGVfbm8iKX0KICAgICAgICBleGNlcHQgKFZhbHVlRXJyb3IsIEtleUVycm9yKToKICAgICAgICAgICAgcGFzcwogICAgZmlsbGVkID0gYWxy
ZWFkeSA9IHBlbmRpbmcgPSAwCiAgICBmb3IgdGlkLCBlIGluIGJvb2suZ2V0KCJ0YWJsZXMiLCB7fSkuaXRlbXMoKToKICAgICAgICBpZiBlLmdldCgidGFi
bGVfbm8iKToKICAgICAgICAgICAgYWxyZWFkeSArPSAxCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgbm8gPSB0YWJsZS5nZXQoIiVzfCVzfCVzIiAl
IChzdWIsIHRpZCwgZS5nZXQoImhlYWRlcl9zaGEiKSkpCiAgICAgICAgaWYgbm86CiAgICAgICAgICAgIGVbInRhYmxlX25vIl0gPSBubwogICAgICAgICAg
ICBlWyJudW1iZXJlZF9hdCJdID0gbm93CiAgICAgICAgICAgIGZpbGxlZCArPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgcGVuZGluZyArPSAxCiAg
ICBpZiBhcHBseSBhbmQgZmlsbGVkOgogICAgICAgIGhpdHNbLTFdLndyaXRlX3RleHQoX2pzb24uZHVtcHMoYm9vaywgZW5zdXJlX2FzY2lpPUZhbHNlLCBp
bmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICByZXR1cm4geyJzdGF0dXMiOiAiT0siLCAiYm9vayI6IGhpdHNbLTFdLm5hbWUsICJudW1iZXJfYm9v
ayI6IChuYlstMV0ubmFtZSBpZiBuYiBlbHNlIE5vbmUpLCAiZmlsbGVkIjogZmlsbGVkLCAiYWxyZWFkeSI6IGFscmVhZHksICJwZW5kaW5nIjogcGVuZGlu
ZywKICAgICAgICAgICAgImxhbXAiOiAiR1JFRU4iIGlmIChwZW5kaW5nID09IDAgYW5kIChmaWxsZWQgb3IgYWxyZWFkeSkpIGVsc2UgIkdSQVkifQojID09
PT09IFtWSUE6VEFCTEUtSEVBREVSOkVORF0gPT09PT0KCiMgPT09PT0gW1ZJQTpGTi1NQVRSSVg6djAxMDBdIOWKn+iDveefqemZo+WFseeUqOautShBU1Qg
5b6e6aCt5Yiw5bC+O+WtkOezu+e1seiHquWJteiHqueuoTvlj6rlop7kuI3muJs755u45Ly8ID0g6buD54eI5o+Q6YaSO+S4ieezu+e1seWQhOW4tuS4gOS7
vSzpm7bnm7jkvp0pPT09PT0KX0ZNX0VYQ0wgPSB7InJlZmVyZW5jZXMiLCAiaW50YWtlIiwgIl9zdXBlcnNlZGVkIiwgIlZJQV9SZXRpcmVkRW5naW5lcyIs
ICJfcXVhcmFudGluZV9waXBfdmVuZG9yIiwgIl9fcHljYWNoZV9fIiwgIi52ZW52IiwgInZlbnYiLCAibm9kZV9tb2R1bGVzIiwgIl9xdWFyYW50aW5lIiwg
IlZJQV9OdW1iZXJCb29rcyIsICJfZGYifQpfRk1fTE9DQUwgPSBfX2ltcG9ydF9fKCJyZSIpLmNvbXBpbGUociJeKFZJQXx2aWF8VlJOfHZybnxWREZ8dmRm
fENHQ3xTVVB8VkFQfEdJRnxWUk18X3NhX3xfbmJfKSIpCgoKZGVmIF9mbV92bnVtKG5hbWUpOgogICAgaW1wb3J0IHJlIGFzIF9yZQogICAgbSA9IF9yZS5z
ZWFyY2gociJfdihcZHsyLDR9KVtBLVphLXowLTldKig/OlwuW0EtWmEtejAtOV0rKT8kIiwgbmFtZSkKICAgIHJldHVybiBpbnQobS5ncm91cCgxKSkgaWYg
bSBlbHNlIC0xCgoKZGVmIF9mbV92ZXIobmFtZSk6CiAgICBpbXBvcnQgcmUgYXMgX3JlCiAgICBtID0gX3JlLnNlYXJjaChyIl8odlxkezIsNH1bQS1aYS16
MC05XSopKD86XC5bQS1aYS16MC05XSspPyQiLCBuYW1lKQogICAgcmV0dXJuIG0uZ3JvdXAoMSkgaWYgbSBlbHNlICJ2MDAwMCIKCgpkZWYgX2ZtX2ZhbWls
eShuYW1lKToKICAgIGltcG9ydCByZSBhcyBfcmUKICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aCBhcyBfUAogICAgcmV0dXJuIF9yZS5zdWIociJfdlxk
ezIsNH1bQS1aYS16MC05XSokIiwgIiIsIF9yZS5zdWIociJfc2hhWzAtOWEtZl17OCx9JCIsICIiLCBfUChuYW1lKS5zdGVtKSkKCgpkZWYgX2ZtX3JlYWQo
cCk6CiAgICByYXcgPSBwLnJlYWRfYnl0ZXMoKQogICAgZm9yIGVuYyBpbiAoInV0Zi04LXNpZyIsICJ1dGYtMTYiLCAiY3A5NTAiKToKICAgICAgICB0cnk6
CiAgICAgICAgICAgIHJldHVybiByYXcuZGVjb2RlKGVuYykKICAgICAgICBleGNlcHQgVW5pY29kZURlY29kZUVycm9yOgogICAgICAgICAgICBjb250aW51
ZQogICAgcmV0dXJuICIiCgoKZGVmIF9mbV90YWlscyhkaXJzLCByb290KToKICAgIGJlc3QgPSB7fQogICAgZm9yIGQgaW4gZGlyczoKICAgICAgICBpZiBu
b3QgZC5pc19kaXIoKToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBmb3IgcCBpbiBkLnJnbG9iKCIqLnB5Iik6CiAgICAgICAgICAgIGlmIG5vdCBw
LmlzX2ZpbGUoKToKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIHBhcnRzID0gc2V0KHAucmVsYXRp
dmVfdG8ocm9vdCkucGFydHNbOi0xXSkKICAgICAgICAgICAgZXhjZXB0IFZhbHVlRXJyb3I6CiAgICAgICAgICAgICAgICBwYXJ0cyA9IHNldChwLnBhcnRz
KQogICAgICAgICAgICBpZiBwYXJ0cyAmIF9GTV9FWENMOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgayA9IChwLnBhcmVudCwgX2Zt
X2ZhbWlseShwLm5hbWUpKQogICAgICAgICAgICB2ID0gX2ZtX3ZudW0ocC5uYW1lKQogICAgICAgICAgICBpZiBrIG5vdCBpbiBiZXN0IG9yIHYgPiBiZXN0
W2tdWzBdOgogICAgICAgICAgICAgICAgYmVzdFtrXSA9ICh2LCBwKQogICAgcmV0dXJuIHNvcnRlZCgodlsxXSBmb3IgdiBpbiBiZXN0LnZhbHVlcygpKSwg
a2V5PWxhbWJkYSBxOiBzdHIocSkpCgoKZGVmIF9mbV9ib2R5X3NoYShub2RlKToKICAgIGltcG9ydCBhc3QgYXMgX2FzdAogICAgaW1wb3J0IGhhc2hsaWIg
YXMgX2gKICAgIHRyeToKICAgICAgICBzID0gX2FzdC5kdW1wKG5vZGUsIGFubm90YXRlX2ZpZWxkcz1GYWxzZSwgaW5jbHVkZV9hdHRyaWJ1dGVzPUZhbHNl
KQogICAgZXhjZXB0IEV4Y2VwdGlvbjogICMgbm9xYTogQkxFMDAxCiAgICAgICAgcyA9IHJlcHIobm9kZSkKICAgIHJldHVybiBfaC5zaGEyNTYocy5lbmNv
ZGUoInV0Zi04IiwgInJlcGxhY2UiKSkuaGV4ZGlnZXN0KClbOjE2XQoKCmRlZiBfZm1fc2lnKGZuKToKICAgIGltcG9ydCBhc3QgYXMgX2FzdAogICAgYSA9
IGZuLmFyZ3MKICAgIG5hbWVzID0gW3guYXJnIGZvciB4IGluIGEucG9zb25seWFyZ3NdICsgW3guYXJnIGZvciB4IGluIGEuYXJnc10KICAgIGlmIGEudmFy
YXJnOgogICAgICAgIG5hbWVzLmFwcGVuZCgiKiIgKyBhLnZhcmFyZy5hcmcpCiAgICBuYW1lcyArPSBbeC5hcmcgZm9yIHggaW4gYS5rd29ubHlhcmdzXQog
ICAgaWYgYS5rd2FyZzoKICAgICAgICBuYW1lcy5hcHBlbmQoIioqIiArIGEua3dhcmcuYXJnKQogICAgcmV0dXJuICIlcyglcykiICUgKGZuLm5hbWUsICIs
ICIuam9pbihuYW1lcykpCgoKZGVmIF9mbV9zY2FuX2ZpbGUocCwgcm9vdCwgc3ViKToKICAgICIiIuS4gOaUryAucHkg4oaSIGl0ZW1zIOWIl+ihqChNREwv
RU5HIOS4gOWIlyDCtyBDTFMg5q+P6aGe5LiA5YiXIMK3IEZOQyDmr4/lh73lvI8v5pa55rOV5LiA5YiXIMK3IExJQiDmr4/nrKzkuInmlrnlpZfku7bkuIDl
iJcp44CCQVNUIOWkseaVlyA9IOipsuaqlCBNREwg5YiX5bi2IGlzc3VlLOS4jee0heOAgiIiIgogICAgaW1wb3J0IGFzdCBhcyBfYXN0CiAgICBpbXBvcnQg
aGFzaGxpYiBhcyBfaAogICAgaW1wb3J0IHN5cyBhcyBfc3lzCiAgICB0eHQgPSBfZm1fcmVhZChwKQogICAgcmVsID0gcC5yZWxhdGl2ZV90byhyb290KS5h
c19wb3NpeCgpIGlmIHN0cihwKS5zdGFydHN3aXRoKHN0cihyb290KSkgZWxzZSBwLmFzX3Bvc2l4KCkKICAgIGZhbSwgdmVyID0gX2ZtX2ZhbWlseShwLm5h
bWUpLCBfZm1fdmVyKHAubmFtZSkKICAgIGtpbmQgPSAiRU5HIiBpZiAoIl9FTkciIGluIGZhbSBvciAiRW5naW5lIiBpbiBmYW0gb3IgZmFtLmxvd2VyKCku
ZW5kc3dpdGgoImVuZ2luZSIpKSBlbHNlICJNREwiCiAgICBiYXNlID0geyJzdWIiOiBzdWIsICJtb2R1bGUiOiBmYW0sICJ2ZXJzaW9uIjogdmVyLCAic291
cmNlIjogcmVsfQogICAgaXRlbXMgPSBbZGljdChiYXNlLCBraW5kPWtpbmQsIG5hbWU9ZmFtLCBrZXk9IiVzfCVzIiAlIChraW5kLCBmYW0pLCBsaW5lcz10
eHQuY291bnQoIlxuIikgKyAxLAogICAgICAgICAgICAgICAgICBib2R5X3NoYT1faC5zaGEyNTYodHh0LmVuY29kZSgidXRmLTgiLCAicmVwbGFjZSIpKS5o
ZXhkaWdlc3QoKVs6MTZdLCBhY2NlbD0oIltWSUE6QUNDRUwtQlJJREdFIiBpbiB0eHQpLCBpc3N1ZXM9W10pXQogICAgdHJ5OgogICAgICAgIHRyZWUgPSBf
YXN0LnBhcnNlKHR4dCkKICAgIGV4Y2VwdCAoU3ludGF4RXJyb3IsIFZhbHVlRXJyb3IpIGFzIGV4YzoKICAgICAgICBpdGVtc1swXVsiaXNzdWVzIl0uYXBw
ZW5kKCJBU1Qg5aSx5pWXICVzIEwlcyIgJSAodHlwZShleGMpLl9fbmFtZV9fLCBnZXRhdHRyKGV4YywgImxpbmVubyIsICI/IikpKQogICAgICAgIHJldHVy
biBpdGVtcwogICAgc3RkID0gc2V0KGdldGF0dHIoX3N5cywgInN0ZGxpYl9tb2R1bGVfbmFtZXMiLCAoKSkpCiAgICBsaWJzID0gc2V0KCkKICAgIGZvciBu
b2RlIGluIF9hc3Qud2Fsayh0cmVlKToKICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsIF9hc3QuSW1wb3J0KToKICAgICAgICAgICAgZm9yIGFsIGluIG5v
ZGUubmFtZXM6CiAgICAgICAgICAgICAgICBsaWJzLmFkZChhbC5uYW1lLnNwbGl0KCIuIilbMF0pCiAgICAgICAgZWxpZiBpc2luc3RhbmNlKG5vZGUsIF9h
c3QuSW1wb3J0RnJvbSkgYW5kIG5vZGUubW9kdWxlIGFuZCBub2RlLmxldmVsID09IDA6CiAgICAgICAgICAgIGxpYnMuYWRkKG5vZGUubW9kdWxlLnNwbGl0
KCIuIilbMF0pCiAgICBmb3IgbGliIGluIHNvcnRlZChsaWJzKToKICAgICAgICBpZiBsaWIgaW4gc3RkIG9yIF9GTV9MT0NBTC5tYXRjaChsaWIpOgogICAg
ICAgICAgICBjb250aW51ZQogICAgICAgIGl0ZW1zLmFwcGVuZChkaWN0KGJhc2UsIGtpbmQ9IkxJQiIsIG5hbWU9bGliLCBrZXk9IkxJQnwlcyIgJSBsaWIs
IGFwaT0iaW1wb3J0ICVzIiAlIGxpYiwgYm9keV9zaGE9IiIsIGlzc3Vlcz1bXSkpCiAgICBmb3Igbm9kZSBpbiB0cmVlLmJvZHk6CiAgICAgICAgaWYgaXNp
bnN0YW5jZShub2RlLCBfYXN0LkNsYXNzRGVmKToKICAgICAgICAgICAgYmFzZXMgPSBbZ2V0YXR0cihiLCAiaWQiLCBnZXRhdHRyKGIsICJhdHRyIiwgIj8i
KSkgZm9yIGIgaW4gbm9kZS5iYXNlc10KICAgICAgICAgICAgaXRlbXMuYXBwZW5kKGRpY3QoYmFzZSwga2luZD0iQ0xTIiwgbmFtZT1ub2RlLm5hbWUsIGtl
eT0iQ0xTfCVzfCVzIiAlIChmYW0sIG5vZGUubmFtZSksIGFwaT0iY2xhc3MgJXMoJXMpIiAlIChub2RlLm5hbWUsICIsICIuam9pbihiYXNlcykpLAogICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICBsaW5lPW5vZGUubGluZW5vLCBib2R5X3NoYT1fZm1fYm9keV9zaGEobm9kZSksIG1ldGhvZHM9c3VtKDEgZm9y
IG4gaW4gbm9kZS5ib2R5IGlmIGlzaW5zdGFuY2UobiwgKF9hc3QuRnVuY3Rpb25EZWYsIF9hc3QuQXN5bmNGdW5jdGlvbkRlZikpKSwgaXNzdWVzPVtdKSkK
ICAgICAgICAgICAgZm9yIG4gaW4gbm9kZS5ib2R5OgogICAgICAgICAgICAgICAgaWYgaXNpbnN0YW5jZShuLCAoX2FzdC5GdW5jdGlvbkRlZiwgX2FzdC5B
c3luY0Z1bmN0aW9uRGVmKSk6CiAgICAgICAgICAgICAgICAgICAgcSA9ICIlcy4lcyIgJSAobm9kZS5uYW1lLCBuLm5hbWUpCiAgICAgICAgICAgICAgICAg
ICAgaXRlbXMuYXBwZW5kKGRpY3QoYmFzZSwga2luZD0iRk5DIiwgbmFtZT1xLCBrZXk9IkZOQ3wlc3wlcyIgJSAoZmFtLCBxKSwgYXBpPV9mbV9zaWcobiks
IGxpbmU9bi5saW5lbm8sIGJvZHlfc2hhPV9mbV9ib2R5X3NoYShuKSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBkb2M9KF9hc3Qu
Z2V0X2RvY3N0cmluZyhuKSBvciAiIikuc3BsaXQoIlxuIilbMF1bOjgwXSwgaXNzdWVzPVtdKSkKICAgICAgICBlbGlmIGlzaW5zdGFuY2Uobm9kZSwgKF9h
c3QuRnVuY3Rpb25EZWYsIF9hc3QuQXN5bmNGdW5jdGlvbkRlZikpOgogICAgICAgICAgICBpdGVtcy5hcHBlbmQoZGljdChiYXNlLCBraW5kPSJGTkMiLCBu
YW1lPW5vZGUubmFtZSwga2V5PSJGTkN8JXN8JXMiICUgKGZhbSwgbm9kZS5uYW1lKSwgYXBpPV9mbV9zaWcobm9kZSksIGxpbmU9bm9kZS5saW5lbm8sIGJv
ZHlfc2hhPV9mbV9ib2R5X3NoYShub2RlKSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZG9jPShfYXN0LmdldF9kb2NzdHJpbmcobm9kZSkgb3Ig
IiIpLnNwbGl0KCJcbiIpWzBdWzo4MF0sIGlzc3Vlcz1bXSkpCiAgICByZXR1cm4gaXRlbXMKCgpkZWYgX2ZtX3NpbWlsYXIoaXRlbXMpOgogICAgIiIi55u4
5Ly85o+Q6YaSKOm7gyzkuI3ntIUpOuWQjOWQjSBGTkMvQ0xTIOaVo+WcqCDiiaUyIOaooee1hCDCtyDlkIwgYm9keSDnlbDlkI0v55Ww5qih57WEIMK3IOWQ
jCBMSUIg5aSa5qih57WE5LiN566X44CC4oaSIHtrZXk6IFvmj5DphpJdfSIiIgogICAgZnJvbSBjb2xsZWN0aW9ucyBpbXBvcnQgZGVmYXVsdGRpY3QgYXMg
X2RkCiAgICBieV9uYW1lLCBieV9ib2R5ID0gX2RkKGxpc3QpLCBfZGQobGlzdCkKICAgIGZvciBpdCBpbiBpdGVtczoKICAgICAgICBpZiBpdFsia2luZCJd
IGluICgiRk5DIiwgIkNMUyIpOgogICAgICAgICAgICBzaG9ydCA9IGl0WyJuYW1lIl0uc3BsaXQoIi4iKVstMV0KICAgICAgICAgICAgaWYgbm90IHNob3J0
LnN0YXJ0c3dpdGgoIl8iKSBhbmQgc2hvcnQgbm90IGluICgibWFpbiIsICJzZWxmdGVzdCIsICJjaGsiLCAiX19nZXRhdHRyX18iLCAicnVuIiwgImNoZWNr
IiwgImxvYWQiLCAiYnVpbGQiLCAiZW1pdCIsICJzY2FuIik6CiAgICAgICAgICAgICAgICBieV9uYW1lWyhpdFsia2luZCJdLCBzaG9ydCldLmFwcGVuZChp
dFsia2V5Il0pCiAgICAgICAgICAgIGlmIGl0LmdldCgiYm9keV9zaGEiKToKICAgICAgICAgICAgICAgIGJ5X2JvZHlbKGl0WyJraW5kIl0sIGl0WyJib2R5
X3NoYSJdKV0uYXBwZW5kKGl0WyJrZXkiXSkKICAgIHJlbSA9IF9kZChsaXN0KQogICAgZm9yIChrLCBubSksIGtleXMgaW4gYnlfbmFtZS5pdGVtcygpOgog
ICAgICAgIG1vZHMgPSB7eC5zcGxpdCgifCIpWzFdIGZvciB4IGluIGtleXN9CiAgICAgICAgaWYgbGVuKG1vZHMpID49IDI6CiAgICAgICAgICAgIGZvciB4
IGluIGtleXM6CiAgICAgICAgICAgICAgICByZW1beF0uYXBwZW5kKCLlkIzlkI0gJXMg5pWj5ZyoICVkIOaooee1hCIgJSAobm0sIGxlbihtb2RzKSkpCiAg
ICBmb3IgKGssIHNoYSksIGtleXMgaW4gYnlfYm9keS5pdGVtcygpOgogICAgICAgIGlmIGxlbihrZXlzKSA+PSAyIGFuZCBsZW4oe3guc3BsaXQoInwiKVsx
XSBmb3IgeCBpbiBrZXlzfSkgPj0gMjoKICAgICAgICAgICAgZm9yIHggaW4ga2V5czoKICAgICAgICAgICAgICAgIHJlbVt4XS5hcHBlbmQoIuWQjCBib2R5
IOWPpuimiyAlZCDomZUo5YCZ6YG45YWx55SoIExJQikiICUgKGxlbihrZXlzKSAtIDEpKQogICAgcmV0dXJuIGRpY3QocmVtKQoKCmRlZiBfZm1fcmVnaXN0
ZXIoc3ViLCBkaXJzLCByb290LCBib29rX2Rpciwgbm93LCBhcHBseT1UcnVlKToKICAgICIiIuaOg+WwvueJiCAucHkg4oaSIOeZu+iomCA8c3ViPl9GdW5j
dGlvbk1hdHJpeF92MDEwMC5qc29uKOWPquWinjrmlrA9TkVXIMK3IOWQjD1TQU1FIMK3IOaUuSBib2R5PVVQREFURUQraGlzdG9yeSDCtyDmqLnkuIrkuI3o
pos9R09ORSjkuI3liKosZ29uZV9zaW5jZSnCtyDliKrpmaTlj6rog70gZm4gcmV0aXJlIOW4tiByZXBsYWNlZF9ieSnjgIIiIiIKICAgIGltcG9ydCBqc29u
IGFzIF9qc29uCiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX1AKICAgIGhpdHMgPSBzb3J0ZWQoX1AoYm9va19kaXIpLmdsb2Ioc3ViICsgIl9G
dW5jdGlvbk1hdHJpeF92Ki5qc29uIiksIGtleT1sYW1iZGEgcTogX2ZtX3ZudW0ocS5uYW1lKSkKICAgIGlmIGhpdHM6CiAgICAgICAgYm9vayA9IF9qc29u
LmxvYWRzKF9mbV9yZWFkKGhpdHNbLTFdKSkKICAgICAgICBmcCA9IGhpdHNbLTFdCiAgICBlbHNlOgogICAgICAgIGZwID0gX1AoYm9va19kaXIpIC8gKHN1
YiArICJfRnVuY3Rpb25NYXRyaXhfdjAxMDAuanNvbiIpCiAgICAgICAgYm9vayA9IHsic2NoZW1hIjogIlZJQS5GdW5jdGlvbk1hdHJpeC52MSIsICJzdWIi
OiBzdWIsICJ2ZXJzaW9uIjogInYwMTAwIiwgImNyZWF0ZWRfYXQiOiBub3csCiAgICAgICAgICAgICAgICAicnVsZSI6ICLlrZDns7vntbHoh6rlibXoh6rn
rqEoTDExNCDikaApO0FTVCDlvp7poK3liLDlsL7nmbvpjIQgTURML0VORy9DTFMvRk5DL0xJQjvlj6rlop7kuI3muJs65qi55LiK5LiN6KaLID0gR09ORSDk
uI3liKo75Yiq6Zmk5Y+q6ZmQIChhKSDooZ3nqoHoo4HlrpogKGIpIOW3peWFt+eEoeS6uue2reittyzkuJTlv4XluLYgcmVwbGFjZWRfYnk755u45Ly8ID0g
6buD54eI5o+Q6YaS5LiN57SFO251bWJlciDnlZnnmb3lvoXmr43ns7vntbEiLAogICAgICAgICAgICAgICAgIml0ZW1zIjoge319CiAgICBpdGVtc19hbGwg
PSBbXQogICAgZm9yIHAgaW4gX2ZtX3RhaWxzKGRpcnMsIHJvb3QpOgogICAgICAgIGl0ZW1zX2FsbCArPSBfZm1fc2Nhbl9maWxlKHAsIHJvb3QsIHN1YikK
ICAgIHNpbSA9IF9mbV9zaW1pbGFyKGl0ZW1zX2FsbCkKICAgIGJrID0gYm9vay5zZXRkZWZhdWx0KCJpdGVtcyIsIHt9KQogICAgc2VlbiA9IHNldCgpCiAg
ICBjb3VudHMgPSB7Ik5FVyI6IDAsICJTQU1FIjogMCwgIlVQREFURUQiOiAwLCAiR09ORSI6IDAsICJCQUNLIjogMH0KICAgIGZvciBpdCBpbiBpdGVtc19h
bGw6CiAgICAgICAgayA9IGl0WyJrZXkiXQogICAgICAgIHNlZW4uYWRkKGspCiAgICAgICAgaXRbInNpbWlsYXIiXSA9IHNpbS5nZXQoaywgW10pCiAgICAg
ICAgZSA9IGJrLmdldChrKQogICAgICAgIGlmIGUgaXMgTm9uZToKICAgICAgICAgICAgYmtba10gPSBkaWN0KGl0LCBzdGF0dXM9IkFDVElWRSIsIGZpcnN0
X3NlZW49bm93LCBsYXN0X3NlZW49bm93LCBudW1iZXI9IiIsIGhpc3Rvcnk9W10pCiAgICAgICAgICAgIGNvdW50c1siTkVXIl0gKz0gMQogICAgICAgIGVs
c2U6CiAgICAgICAgICAgIHdhc19nb25lID0gZS5nZXQoInN0YXR1cyIpID09ICJHT05FIgogICAgICAgICAgICBpZiBlLmdldCgiYm9keV9zaGEiKSAhPSBp
dC5nZXQoImJvZHlfc2hhIikgb3IgZS5nZXQoInZlcnNpb24iKSAhPSBpdC5nZXQoInZlcnNpb24iKToKICAgICAgICAgICAgICAgIGUuc2V0ZGVmYXVsdCgi
aGlzdG9yeSIsIFtdKS5hcHBlbmQoeyJ2ZXJzaW9uIjogZS5nZXQoInZlcnNpb24iKSwgImJvZHlfc2hhIjogZS5nZXQoImJvZHlfc2hhIiksICJzb3VyY2Ui
OiBlLmdldCgic291cmNlIiksICJ1bnRpbCI6IG5vd30pCiAgICAgICAgICAgICAgICBjb3VudHNbIlVQREFURUQiXSArPSAxCiAgICAgICAgICAgIGVsc2U6
CiAgICAgICAgICAgICAgICBjb3VudHNbIlNBTUUiXSArPSAxCiAgICAgICAgICAgIGUudXBkYXRlKHt4OiBpdFt4XSBmb3IgeCBpbiBpdCBpZiB4IG5vdCBp
biAoInN0YXR1cyIsICJmaXJzdF9zZWVuIiwgIm51bWJlciIsICJoaXN0b3J5Iil9KQogICAgICAgICAgICBlWyJzdGF0dXMiXSA9ICJBQ1RJVkUiCiAgICAg
ICAgICAgIGVbImxhc3Rfc2VlbiJdID0gbm93CiAgICAgICAgICAgIGlmIHdhc19nb25lOgogICAgICAgICAgICAgICAgY291bnRzWyJCQUNLIl0gKz0gMQog
ICAgICAgICAgICAgICAgZS5wb3AoImdvbmVfc2luY2UiLCBOb25lKQogICAgZm9yIGssIGUgaW4gYmsuaXRlbXMoKToKICAgICAgICBpZiBrIG5vdCBpbiBz
ZWVuIGFuZCBlLmdldCgic3RhdHVzIikgPT0gIkFDVElWRSI6CiAgICAgICAgICAgIGVbInN0YXR1cyJdID0gIkdPTkUiCiAgICAgICAgICAgIGVbImdvbmVf
c2luY2UiXSA9IG5vdwogICAgICAgICAgICBjb3VudHNbIkdPTkUiXSArPSAxCiAgICBib29rWyJ1cGRhdGVkX2F0Il0gPSBub3cKICAgIGlmIGFwcGx5Ogog
ICAgICAgIF9QKGJvb2tfZGlyKS5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICAgICAgZnAud3JpdGVfdGV4dChfanNvbi5kdW1wcyhi
b29rLCBlbnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0xKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIGtpbmRzID0ge30KICAgIGZvciBlIGluIGJrLnZhbHVl
cygpOgogICAgICAgIGtpbmRzW2VbImtpbmQiXV0gPSBraW5kcy5nZXQoZVsia2luZCJdLCAwKSArIDEKICAgIHJldHVybiB7ImJvb2siOiBmcC5uYW1lLCAi
aXRlbXMiOiBsZW4oYmspLCAia2luZHMiOiBraW5kcywgImNvdW50cyI6IGNvdW50cywgInNpbWlsYXIiOiBzdW0oMSBmb3IgZSBpbiBiay52YWx1ZXMoKSBp
ZiBlLmdldCgic2ltaWxhciIpKSwKICAgICAgICAgICAgImdvbmUiOiBzdW0oMSBmb3IgZSBpbiBiay52YWx1ZXMoKSBpZiBlLmdldCgic3RhdHVzIikgPT0g
IkdPTkUiKSwgImFzdF9mYWlsIjogc3VtKDEgZm9yIGUgaW4gYmsudmFsdWVzKCkgaWYgYW55KCJBU1QiIGluIHggZm9yIHggaW4gZS5nZXQoImlzc3VlcyIs
IFtdKSkpLAogICAgICAgICAgICAiYmxhbmsiOiBzdW0oMSBmb3IgZSBpbiBiay52YWx1ZXMoKSBpZiBlLmdldCgic3RhdHVzIikgPT0gIkFDVElWRSIgYW5k
IG5vdCBlLmdldCgibnVtYmVyIikpfQoKCmRlZiBfZm1fcmV0aXJlKHN1YiwgYm9va19kaXIsIGtleSwgcmVwbGFjZWRfYnksIHJlYXNvbiwgbm93LCBhcHBs
eT1UcnVlKToKICAgICIiIuWUr+S4gOiDveaKiuWIl+enu+WHuiBBQ1RJVkUvR09ORSDnmoTli5XkvZw66KaBIHJlcGxhY2VkX2J5KOabv+S7o+eJiOacrCno
iIcgcmVhc29uKOihneeqgeijgeWumiAvIOeEoeS6uue2reittyk75LiN54mp55CG5YiqLOaomSBSRVRJUkVE44CCIiIiCiAgICBpbXBvcnQganNvbiBhcyBf
anNvbgogICAgZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9QCiAgICBoaXRzID0gc29ydGVkKF9QKGJvb2tfZGlyKS5nbG9iKHN1YiArICJfRnVuY3Rp
b25NYXRyaXhfdiouanNvbiIpLCBrZXk9bGFtYmRhIHE6IF9mbV92bnVtKHEubmFtZSkpCiAgICBpZiBub3QgaGl0czoKICAgICAgICByZXR1cm4geyJzdGF0
dXMiOiAiTk9fQk9PSyJ9CiAgICBib29rID0gX2pzb24ubG9hZHMoX2ZtX3JlYWQoaGl0c1stMV0pKQogICAgZSA9IGJvb2suZ2V0KCJpdGVtcyIsIHt9KS5n
ZXQoa2V5KQogICAgaWYgbm90IGU6CiAgICAgICAgcmV0dXJuIHsic3RhdHVzIjogIk5PX0tFWSJ9CiAgICBpZiBub3QgcmVwbGFjZWRfYnkgb3Igbm90IHJl
YXNvbjoKICAgICAgICByZXR1cm4geyJzdGF0dXMiOiAiUkVGVVNFRCIsICJ3aHkiOiAi6YCA5b255b+F5bi2IHJlcGxhY2VkX2J5IOiIhyByZWFzb24o6KGd
56qB6KOB5a6aIC8g54Sh5Lq657at6K23KSJ9CiAgICBpZiByZXBsYWNlZF9ieSBub3QgaW4gYm9va1siaXRlbXMiXToKICAgICAgICByZXR1cm4geyJzdGF0
dXMiOiAiUkVGVVNFRCIsICJ3aHkiOiAicmVwbGFjZWRfYnkg5LiN5Zyo55+p6ZmjOiVzIiAlIHJlcGxhY2VkX2J5fQogICAgZS51cGRhdGUoc3RhdHVzPSJS
RVRJUkVEIiwgcmV0aXJlZF9hdD1ub3csIHJlcGxhY2VkX2J5PXJlcGxhY2VkX2J5LCByZXRpcmVfcmVhc29uPXJlYXNvbikKICAgIGlmIGFwcGx5OgogICAg
ICAgIGhpdHNbLTFdLndyaXRlX3RleHQoX2pzb24uZHVtcHMoYm9vaywgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIp
CiAgICByZXR1cm4geyJzdGF0dXMiOiAiUkVUSVJFRCIsICJrZXkiOiBrZXksICJyZXBsYWNlZF9ieSI6IHJlcGxhY2VkX2J5fQoKCmRlZiBfZm1fcHVsbChz
dWIsIGJvb2tfZGlyLCBudW1iZXJzX2Rpciwgbm93LCBhcHBseT1UcnVlKToKICAgICIiIuS+nemNtSA8c3ViPnw8a2V5Pnw8dmVyc2lvbj4g5b6e5q+N57O7
57WxIFZJQV9SZWdpc3RyeU51bWJlcnNfdiouanNvbiDoroDomZ/loavlm54o5Y+q5aGr55WZ55m9O+Whq+S6huWNs+mOlinjgIIiIiIKICAgIGltcG9ydCBq
c29uIGFzIF9qc29uCiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX1AKICAgIGhpdHMgPSBzb3J0ZWQoX1AoYm9va19kaXIpLmdsb2Ioc3ViICsg
Il9GdW5jdGlvbk1hdHJpeF92Ki5qc29uIiksIGtleT1sYW1iZGEgcTogX2ZtX3ZudW0ocS5uYW1lKSkKICAgIGlmIG5vdCBoaXRzOgogICAgICAgIHJldHVy
biB7InN0YXR1cyI6ICJOT19CT09LIiwgImZpbGxlZCI6IDAsICJhbHJlYWR5IjogMCwgInBlbmRpbmciOiAwLCAibGFtcCI6ICJHUkFZIn0KICAgIGJvb2sg
PSBfanNvbi5sb2FkcyhfZm1fcmVhZChoaXRzWy0xXSkpCiAgICBuYiA9IHNvcnRlZChfUChudW1iZXJzX2RpcikuZ2xvYigiVklBX1JlZ2lzdHJ5TnVtYmVy
c192Ki5qc29uIiksIGtleT1sYW1iZGEgcTogX2ZtX3ZudW0ocS5uYW1lKSkKICAgIHRhYmxlID0ge30KICAgIGlmIG5iOgogICAgICAgIHRyeToKICAgICAg
ICAgICAgZCA9IF9qc29uLmxvYWRzKF9mbV9yZWFkKG5iWy0xXSkpCiAgICAgICAgICAgIHRhYmxlID0ge2VbImtleSJdOiBlWyJjb2RlIl0gZm9yIGUgaW4g
ZC5nZXQoImVudHJpZXMiLCBbXSkgaWYgZS5nZXQoImtleSIpIGFuZCBlLmdldCgiY29kZSIpfQogICAgICAgIGV4Y2VwdCAoVmFsdWVFcnJvciwgS2V5RXJy
b3IpOgogICAgICAgICAgICBwYXNzCiAgICBmaWxsZWQgPSBhbHJlYWR5ID0gcGVuZGluZyA9IDAKICAgIGZvciBrLCBlIGluIGJvb2suZ2V0KCJpdGVtcyIs
IHt9KS5pdGVtcygpOgogICAgICAgIGlmIGUuZ2V0KCJzdGF0dXMiKSAhPSAiQUNUSVZFIjoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBlLmdl
dCgibnVtYmVyIik6CiAgICAgICAgICAgIGFscmVhZHkgKz0gMQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGNvZGUgPSB0YWJsZS5nZXQoIiVzfCVz
fCVzIiAlIChzdWIsIGssIGUuZ2V0KCJ2ZXJzaW9uIikpKQogICAgICAgIGlmIGNvZGU6CiAgICAgICAgICAgIGVbIm51bWJlciJdID0gY29kZQogICAgICAg
ICAgICBlWyJudW1iZXJlZF9hdCJdID0gbm93CiAgICAgICAgICAgIGZpbGxlZCArPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgcGVuZGluZyArPSAx
CiAgICBpZiBhcHBseSBhbmQgZmlsbGVkOgogICAgICAgIGhpdHNbLTFdLndyaXRlX3RleHQoX2pzb24uZHVtcHMoYm9vaywgZW5zdXJlX2FzY2lpPUZhbHNl
LCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICByZXR1cm4geyJzdGF0dXMiOiAiT0siLCAiYm9vayI6IGhpdHNbLTFdLm5hbWUsICJudW1iZXJf
Ym9vayI6IChuYlstMV0ubmFtZSBpZiBuYiBlbHNlIE5vbmUpLCAiZmlsbGVkIjogZmlsbGVkLCAiYWxyZWFkeSI6IGFscmVhZHksICJwZW5kaW5nIjogcGVu
ZGluZywKICAgICAgICAgICAgImxhbXAiOiAiR1JFRU4iIGlmIChwZW5kaW5nID09IDAgYW5kIChmaWxsZWQgb3IgYWxyZWFkeSkpIGVsc2UgIkdSQVkifQoj
ID09PT09IFtWSUE6Rk4tTUFUUklYOkVORF0gPT09PT0KCgpkZWYgX25vdygpIC0+IHN0cjoKICAgIHJldHVybiBkYXRldGltZS5kYXRldGltZS5ub3coKS5p
c29mb3JtYXQodGltZXNwZWM9InNlY29uZHMiKQoKCmRlZiBfcm9vdCgpIC0+IFBhdGg6CiAgICBpZiBvcy5lbnZpcm9uLmdldCgiVklBX1JPT1QiKToKICAg
ICAgICByZXR1cm4gUGF0aChvcy5lbnZpcm9uWyJWSUFfUk9PVCJdKQogICAgcCA9IE1FCiAgICB3aGlsZSBwLnBhcmVudCAhPSBwOgogICAgICAgIGlmIChw
IC8gInN1cHBvcnRpdmUgbW9kdWxlcyIpLmlzX2RpcigpIGFuZCAocCAvICJmdW5jdGlvbmFsIG1vZHVsZXMiKS5pc19kaXIoKToKICAgICAgICAgICAgcmV0
dXJuIHAKICAgICAgICBwID0gcC5wYXJlbnQKICAgIHJldHVybiBNRS5wYXJlbnRzWzJdCgoKZGVmIF9wYXRocygpIC0+IGRpY3Q6CiAgICByID0gX3Jvb3Qo
KQogICAgcmV0dXJuIHsicm9vdCI6IHIsICJyZWdpc3RyeSI6IHIgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIiAvICJyZWdpc3RyeSIsICJzdXAiOiByIC8gInN1
cHBvcnRpdmUgbW9kdWxlcyIsICJ2ZGYiOiByIC8gImZ1bmN0aW9uYWwgbW9kdWxlcyIgLyAiVkRGIiwgInZybiI6IHIgLyAiZnVuY3Rpb25hbCBtb2R1bGVz
IiAvICJWUk4iLAogICAgICAgICAgICAiY2FyZHMiOiByIC8gImRvY3MiIC8gImhhbmRvZmYiIC8gImFpIiwgInJlcG9ydCI6IHIgLyAiVklBX1JlcG9ydHMi
IC8gInJldmlldyIgLyAidmNnY19yZWdpc3RyeSJ9CgoKZGVmIF9ib29rKFA6IGRpY3QsIHN1Yjogc3RyLCBzdGVtOiBzdHIpIC0+IGRpY3Q6CiAgICBkID0g
eyJWQ0dDIjogUFsicmVnaXN0cnkiXSwgIlZERiI6IFBbInZkZiJdIC8gInJlZ2lzdHJ5IiwgIlZSTiI6IFBbInZybiJdIC8gInJlZ2lzdHJ5In1bc3ViXQog
ICAgaGl0cyA9IHNvcnRlZChkLmdsb2IoIiVzXyVzX3YqLmpzb24iICUgKHN1Yiwgc3RlbSkpLCBrZXk9bGFtYmRhIHE6IF90aF92bnVtKHEubmFtZSkpIGlm
IGQuaXNfZGlyKCkgZWxzZSBbXQogICAgaWYgbm90IGhpdHM6CiAgICAgICAgcmV0dXJuIHsiZmlsZSI6IE5vbmUsICJwYXRoIjogTm9uZSwgImRhdGEiOiB7
fX0KICAgIHRyeToKICAgICAgICByZXR1cm4geyJmaWxlIjogaGl0c1stMV0ubmFtZSwgInBhdGgiOiBoaXRzWy0xXSwgImRhdGEiOiBqc29uLmxvYWRzKF90
aF9yZWFkKGhpdHNbLTFdKSl9CiAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICByZXR1cm4geyJmaWxlIjogaGl0c1stMV0ubmFtZSwgInBhdGgiOiBo
aXRzWy0xXSwgImRhdGEiOiB7fSwgImJhZCI6IFRydWV9CgoKZGVmIHJlZ2lzdGVyKFA6IGRpY3QgfCBOb25lID0gTm9uZSwgYXBwbHk6IGJvb2wgPSBUcnVl
KSAtPiBkaWN0OgogICAgUCA9IFAgb3IgX3BhdGhzKCkKICAgIG5vdyA9IF9ub3coKQogICAgc3JjcyA9IFtwIGZvciBwIGluIFBbInJlZ2lzdHJ5Il0uZ2xv
YigiKiIpIGlmIHAuaXNfZmlsZSgpIGFuZCBwLnN1ZmZpeC5sb3dlcigpIGluICgiLmpzb24iLCAiLmpzb25sIiwgIi5jc3YiKSBhbmQgTE9DS0VEX1JFLm1h
dGNoKHAubmFtZSkKICAgICAgICAgICAgYW5kIG5vdCBfdGhfZmFtaWx5KHAubmFtZSkuZW5kc3dpdGgoKCJfVGFibGVIZWFkZXIiLCAiX0Z1bmN0aW9uTWF0
cml4IikpIGFuZCBub3QgcC5uYW1lLnN0YXJ0c3dpdGgoKCJWSUFfVGFibGVOdW1iZXJzIiwgIlZJQV9SZWdpc3RyeU51bWJlcnMiKSldCiAgICBiZXN0ID0g
e30KICAgIGZvciBwIGluIHNyY3M6CiAgICAgICAgayA9IChfdGhfZmFtaWx5KHAubmFtZSksIHAuc3VmZml4Lmxvd2VyKCkpCiAgICAgICAgdiA9IF90aF92
bnVtKHAubmFtZSkKICAgICAgICBpZiBrIG5vdCBpbiBiZXN0IG9yIHYgPiBiZXN0W2tdWzBdOgogICAgICAgICAgICBiZXN0W2tdID0gKHYsIHApCiAgICB0
ID0gX3RoX3JlZ2lzdGVyKCJWQ0dDIiwgW3ZbMV0gZm9yIHYgaW4gYmVzdC52YWx1ZXMoKV0sIFBbInJlZ2lzdHJ5Il0sIG5vdywgYXBwbHk9YXBwbHksIHJl
bF9yb290PVBbInJvb3QiXSkKICAgIGlmIGFwcGx5OiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIHYwMTAyOueZu+iomOW+jOWGjeaOoee0
jeijgeWumumNtSzph43nmbvoqJjkuI3mnIPmioroo4HlrprmtJfmjokKICAgICAgICByYiA9IF9ydWxpbmdzX2Jvb2soUCkKICAgICAgICBpZiByYjoKICAg
ICAgICAgICAgdmIgPSBfYm9vayhQLCAiVkNHQyIsICJUYWJsZUhlYWRlciIpCiAgICAgICAgICAgIGlmIHZiWyJkYXRhIl0gYW5kIF9hZG9wdF9ydWxpbmdz
X3ZjZ2ModmJbImRhdGEiXSwgcmIsIG5vdyk6CiAgICAgICAgICAgICAgICB2YlsicGF0aCJdLndyaXRlX3RleHQoanNvbi5kdW1wcyh2YlsiZGF0YSJdLCBl
bnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0xKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIGYgPSBfZm1fcmVnaXN0ZXIoIlZDR0MiLCBbUFsic3VwIl1dLCBQ
WyJyb290Il0sIFBbInJlZ2lzdHJ5Il0sIG5vdywgYXBwbHk9YXBwbHkpCiAgICByZXR1cm4geyJ2ZXJiIjogInJlZ2lzdGVyIiwgImFwcGx5IjogYXBwbHks
ICJ0YWJsZSI6IHQsICJmbiI6IGYsICJsYW1wIjogIkdSRUVOIn0KCgpkZWYgX2xvYWRfbnVtYmVycyhQOiBkaWN0LCBuYW1lOiBzdHIsIHNjaGVtYTogc3Ry
KSAtPiBkaWN0OgogICAgZnAgPSBQWyJyZWdpc3RyeSJdIC8gbmFtZQogICAgZCA9IGpzb24ubG9hZHMoX3RoX3JlYWQoZnApKSBpZiBmcC5leGlzdHMoKSBl
bHNlIE5vbmUKICAgIGlmIG5vdCBpc2luc3RhbmNlKGQsIGRpY3QpIG9yIG5vdCBpc2luc3RhbmNlKGQuZ2V0KCJlbnRyaWVzIiksIGxpc3QpOgogICAgICAg
IGQgPSB7InNjaGVtYSI6IHNjaGVtYSwgInZlcnNpb24iOiAidjAxMDAiLCAiZW5naW5lIjogTkFNRSwgInJ1bGUiOiAi6Jmf6Lef6Y216LWwOuWQjOmNteaw
uOmBoOWQjOiZnyDCtyDnmbzkuobkuI3mlLblm57kuI3mlLnkuI3ph43nmbwgwrcg57SF54eI6aCF5LiN55m8IMK3IOWtkOezu+e1seS7pemNteiugOWbniIs
ICJjcmVhdGVkX2F0IjogX25vdygpLCAiZW50cmllcyI6IFtdLCAiYmxvY2tlZCI6IFtdfQogICAgcmV0dXJuIGQKCgpkZWYgX251bWJlcmJvb2tfY29kZXMo
UDogZGljdCkgLT4gZGljdDoKICAgICIiIuaXouaciSBWSUFfTnVtYmVyQm9va3M6c291cmNlQHZlcnNpb24g4oaSIOaqlOiZnyhNREwvRU5HKTso5qqU6Jmf
LCBxKSDihpIgRk5DL0NMUyDomZ/jgILmsr/nlKjkuI3ph43nmbzjgIIiIiIKICAgIG5iID0gUFsicmVnaXN0cnkiXSAvICJWSUFfTnVtYmVyQm9va3MiCiAg
ICBmaWxlX2NvZGVzLCBzdWJfY29kZXMgPSB7fSwge30KICAgIGlmIG5iLmlzX2RpcigpOgogICAgICAgIGZvciBwIGluIG5iLmdsb2IoIlZJQV9OdW1iZXJC
b29rXypfdiouanNvbmwiKToKICAgICAgICAgICAga2luZCA9IHAubmFtZS5zcGxpdCgiXyIpWzJdCiAgICAgICAgICAgIGZvciBsbiBpbiBfdGhfcmVhZChw
KS5zcGxpdGxpbmVzKCk6CiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgciA9IGpzb24ubG9hZHMobG4pCiAgICAgICAgICAgICAg
ICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgaWYga2luZCBpbiAoIk1ETCIsICJFTkci
KSBhbmQgci5nZXQoInNvdXJjZSIpIGFuZCByLmdldCgiY29kZSIpOgogICAgICAgICAgICAgICAgICAgIGZpbGVfY29kZXNbclsic291cmNlIl0ucmVwbGFj
ZSgiXFwiLCAiLyIpXSA9IHJbImNvZGUiXQogICAgICAgICAgICAgICAgZWxpZiBraW5kIGluICgiRk5DIiwgIkNMUyIpIGFuZCByLmdldCgiY29kZSIpIGFu
ZCByLmdldCgicSIpOgogICAgICAgICAgICAgICAgICAgIHBhcmVudCA9IHJbImNvZGUiXS5yc3BsaXQoIi0iLCAxKVswXQogICAgICAgICAgICAgICAgICAg
IHN1Yl9jb2Rlc1socGFyZW50LCByWyJxIl0pXSA9IHJbImNvZGUiXQogICAgcmV0dXJuIHsiZmlsZSI6IGZpbGVfY29kZXMsICJzdWIiOiBzdWJfY29kZXN9
CgoKZGVmIGdvdmVybihQOiBkaWN0IHwgTm9uZSA9IE5vbmUsIGFwcGx5OiBib29sID0gRmFsc2UpIC0+IGRpY3Q6CiAgICBQID0gUCBvciBfcGF0aHMoKQog
ICAgbm93ID0gX25vdygpCiAgICBvdXQgPSB7InZlcmIiOiAiZ292ZXJuIiwgInRzIjogX25vdygpLCAiYXBwbHkiOiBhcHBseSwgInRhYmxlcyI6IHt9LCAi
Zm5zIjoge30sICJpc3N1ZWRfdGFibGVzIjogW10sICJpc3N1ZWRfZm5zIjogW10sICJfbm90ZXMiOiBbXX0KICAgICMg4pSA4pSA4pSA4pSA4pSAIOihqCDi
lIDilIDilIDilIDilIAKICAgIHRib29rcyA9IHtzOiBfYm9vayhQLCBzLCAiVGFibGVIZWFkZXIiKSBmb3IgcyBpbiBTVUJTfQogICAgdG51bSA9IF9sb2Fk
X251bWJlcnMoUCwgIlZJQV9UYWJsZU51bWJlcnNfdjAxMDAuanNvbiIsICJWSUFfVGFibGVOdW1iZXJzIikKICAgIGhhdmVfdCA9IHtlWyJrZXkiXTogZSBm
b3IgZSBpbiB0bnVtWyJlbnRyaWVzIl19CiAgICBlbnRzID0gW10KICAgIGZvciBzIGluIFNVQlM6CiAgICAgICAgZm9yIHRpZCwgZSBpbiAodGJvb2tzW3Nd
WyJkYXRhIl0uZ2V0KCJ0YWJsZXMiKSBvciB7fSkuaXRlbXMoKToKICAgICAgICAgICAgZW50cy5hcHBlbmQoKHMsIHRpZCwgZSkpCiAgICBmbGFncyA9IGRl
ZmF1bHRkaWN0KGxpc3QpCiAgICBieV90aWQgPSBkZWZhdWx0ZGljdChsaXN0KQogICAgZm9yIHMsIHRpZCwgZSBpbiBlbnRzOgogICAgICAgIGJ5X3RpZFt0
aWRdLmFwcGVuZCgocywgZS5nZXQoImhlYWRlcl9zaGEiKSkpCiAgICBmb3IgdGlkLCBsc3QgaW4gYnlfdGlkLml0ZW1zKCk6CiAgICAgICAgc3VicyA9IHtz
IGZvciBzLCBfIGluIGxzdH0KICAgICAgICBzaGFzID0ge2ggZm9yIF8sIGggaW4gbHN0fQogICAgICAgIGlmIGxlbihzdWJzKSA+IDEgYW5kIGxlbihzaGFz
KSA+IDE6CiAgICAgICAgICAgIGZvciBzLCBfIGluIGxzdDoKICAgICAgICAgICAgICAgIGZsYWdzWyhzLCB0aWQpXS5hcHBlbmQoKCJUMSIsICJSRUQiLCAi
5ZCMIHRpZCDot6jns7vntbHnlbDpoK06JXMiICUgIiwiLmpvaW4oc29ydGVkKHN1YnMpKSkpCiAgICBjb2xfZHQgPSBkZWZhdWx0ZGljdChzZXQpCiAgICBm
b3IgcywgdGlkLCBlIGluIGVudHM6CiAgICAgICAgZm9yIGMgaW4gZS5nZXQoImNvbHVtbnMiLCBbXSk6CiAgICAgICAgICAgIGNvbF9kdFtjWyJuYW1lIl1d
LmFkZChjWyJkdHlwZSJdKQogICAgYnlfbm8gPSBkZWZhdWx0ZGljdChsaXN0KQogICAgZm9yIHMsIHRpZCwgZSBpbiBlbnRzOgogICAgICAgIGlmIGUuZ2V0
KCJ0YWJsZV9ubyIpOgogICAgICAgICAgICBieV9ub1tlWyJ0YWJsZV9ubyJdXS5hcHBlbmQoKHMsIHRpZCkpCiAgICBmb3IgcywgdGlkLCBlIGluIGVudHM6
CiAgICAgICAgaWYgZS5nZXQoInN0YXR1cyIpICE9ICJBQ1RJVkUiOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIG5vdCBlLmdldCgia2V5cyIp
OgogICAgICAgICAgICBmbGFnc1socywgdGlkKV0uYXBwZW5kKCgiVDIiLCAiUkVEIiwgIueEoeS4u+mNtShERjA2KSIpKQogICAgICAgIGlmIGUuZ2V0KCJk
cmlmdCIpIGFuZCBlLmdldCgidGFibGVfbm8iKToKICAgICAgICAgICAgZmxhZ3NbKHMsIHRpZCldLmFwcGVuZCgoIlQzIiwgIlJFRCIsICLlt7LomZ/ooajp
oK3mvILnp7sg4oaSIOaWsOmgreWcqCAlcyIgJSBlWyJkcmlmdCJdLmdldCgibmV3X3RpZCIpKSkKICAgICAgICBpZiBlLmdldCgidGFibGVfbm8iKSBhbmQg
bGVuKGJ5X25vW2VbInRhYmxlX25vIl1dKSA+IDE6CiAgICAgICAgICAgIGZsYWdzWyhzLCB0aWQpXS5hcHBlbmQoKCJUNCIsICJSRUQiLCAi5ZCM6Jmf5aSa
6KGoICVzIiAlIGVbInRhYmxlX25vIl0pKQogICAgICAgIG1peGVkID0gW2NbIm5hbWUiXSBmb3IgYyBpbiBlLmdldCgiY29sdW1ucyIsIFtdKSBpZiBsZW4o
Y29sX2R0W2NbIm5hbWUiXV0pID4gMV0KICAgICAgICBpZiBtaXhlZDoKICAgICAgICAgICAgZmxhZ3NbKHMsIHRpZCldLmFwcGVuZCgoIlQ1IiwgIllFTExP
VyIsICLlkIzmrITlkI3nlbDlnoso6Leo6KGoKTolcyIgJSAiLCIuam9pbihtaXhlZFs6NV0pKSkKICAgICAgICBpZiBlLmdldCgiaXNzdWVzIik6CiAgICAg
ICAgICAgIGZsYWdzWyhzLCB0aWQpXS5hcHBlbmQoKCJUNiIsICJZRUxMT1ciLCAiOyIuam9pbihlWyJpc3N1ZXMiXSlbOjE2MF0pKQogICAgc2VxID0ge30K
ICAgIHJ4ID0gcmUuY29tcGlsZShyIl5TU09ULVZDR0MtKFx3KyktVEJMKFxkezR9KSQiKQogICAgZm9yIGUgaW4gdG51bVsiZW50cmllcyJdOgogICAgICAg
IG0gPSByeC5tYXRjaChzdHIoZS5nZXQoInRhYmxlX25vIiwgIiIpKSkKICAgICAgICBpZiBtOgogICAgICAgICAgICBzZXFbbS5ncm91cCgxKV0gPSBtYXgo
c2VxLmdldChtLmdyb3VwKDEpLCAwKSwgaW50KG0uZ3JvdXAoMikpKQogICAgZm9yIHMsIHRpZCwgZSBpbiBlbnRzOgogICAgICAgIGlmIGUuZ2V0KCJzdGF0
dXMiKSAhPSAiQUNUSVZFIjoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBmbCA9IGZsYWdzLmdldCgocywgdGlkKSwgW10pCiAgICAgICAgbGFtcCA9
ICJSRUQiIGlmIGFueSh4WzFdID09ICJSRUQiIGZvciB4IGluIGZsKSBlbHNlICgiWUVMTE9XIiBpZiBmbCBlbHNlICJHUkVFTiIpCiAgICAgICAga2V5ID0g
IiVzfCVzfCVzIiAlIChzLCB0aWQsIGUuZ2V0KCJoZWFkZXJfc2hhIikpCiAgICAgICAgcmVjID0geyJzdWIiOiBzLCAidGlkIjogdGlkLCAibGFtcCI6IGxh
bXAsICJmbGFncyI6IFt7InJ1bGUiOiBhLCAibGFtcCI6IGIsICJkZXRhaWwiOiBjfSBmb3IgYSwgYiwgYyBpbiBmbF0sICJ0YWJsZV9ubyI6IGUuZ2V0KCJ0
YWJsZV9ubyIpIG9yIGhhdmVfdC5nZXQoa2V5LCB7fSkuZ2V0KCJ0YWJsZV9ubyIsICIiKSwgInRlc3QiOiBOb25lfQogICAgICAgIGlmIGxhbXAgIT0gIlJF
RCIgYW5kIG5vdCByZWNbInRhYmxlX25vIl06CiAgICAgICAgICAgIHRlc3Rfb2ssIHdoeSA9IF90ZXN0X3RhYmxlKFAsIGUpCiAgICAgICAgICAgIHJlY1si
dGVzdCJdID0gIlBBU1MiIGlmIHRlc3Rfb2sgZWxzZSAiRkFJTDoiICsgd2h5CiAgICAgICAgICAgIGlmIHRlc3Rfb2s6CiAgICAgICAgICAgICAgICBzZXFb
c10gPSBzZXEuZ2V0KHMsIDApICsgMQogICAgICAgICAgICAgICAgbm8gPSAiU1NPVC1WQ0dDLSVzLVRCTCUwNGQiICUgKHMsIHNlcVtzXSkKICAgICAgICAg
ICAgICAgIGVudCA9IHsia2V5Ijoga2V5LCAidGFibGVfbm8iOiBubywgInN1YiI6IHMsICJ0aWQiOiB0aWQsICJoZWFkZXJfc2hhIjogZS5nZXQoImhlYWRl
cl9zaGEiKSwgInNvdXJjZSI6IGUuZ2V0KCJzb3VyY2UiKSwgImlzc3VlZF9hdCI6IG5vdywgIm5vdGUiOiAoInllbGxvdzoiICsgIiwiLmpvaW4oeFswXSBm
b3IgeCBpbiBmbCkpIGlmIGZsIGVsc2UgIiJ9CiAgICAgICAgICAgICAgICB0bnVtWyJlbnRyaWVzIl0uYXBwZW5kKGVudCkKICAgICAgICAgICAgICAgIGhh
dmVfdFtrZXldID0gZW50CiAgICAgICAgICAgICAgICByZWNbInRhYmxlX25vIl0gPSBubwogICAgICAgICAgICAgICAgb3V0WyJpc3N1ZWRfdGFibGVzIl0u
YXBwZW5kKGVudCkKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHJlY1sibGFtcCJdID0gIlJFRCIKICAgICAgICAgICAgICAgIHJlY1siZmxh
Z3MiXS5hcHBlbmQoeyJydWxlIjogIlRFU1QiLCAibGFtcCI6ICJSRUQiLCAiZGV0YWlsIjogd2h5fSkKICAgICAgICBvdXRbInRhYmxlcyJdW2tleV0gPSBy
ZWMKICAgICMg4pSA4pSA4pSA4pSA4pSAIOWKnyDilIDilIDilIDilIDilIAKICAgIGZib29rcyA9IHtzOiBfYm9vayhQLCBzLCAiRnVuY3Rpb25NYXRyaXgi
KSBmb3IgcyBpbiBTVUJTfQogICAgZm51bSA9IF9sb2FkX251bWJlcnMoUCwgIlZJQV9SZWdpc3RyeU51bWJlcnNfdjAxMDAuanNvbiIsICJWSUFfUmVnaXN0
cnlOdW1iZXJzIikKICAgIGhhdmVfZiA9IHtlWyJrZXkiXTogZSBmb3IgZSBpbiBmbnVtWyJlbnRyaWVzIl19CiAgICBuYmMgPSBfbnVtYmVyYm9va19jb2Rl
cyhQKQogICAgaXRlbXMgPSBbXQogICAgZm9yIHMgaW4gU1VCUzoKICAgICAgICBmb3IgaywgZSBpbiAoZmJvb2tzW3NdWyJkYXRhIl0uZ2V0KCJpdGVtcyIp
IG9yIHt9KS5pdGVtcygpOgogICAgICAgICAgICBpdGVtcy5hcHBlbmQoKHMsIGssIGUpKQogICAgZmZsYWdzID0gZGVmYXVsdGRpY3QobGlzdCkKICAgIG1v
ZF9zdWIgPSBkZWZhdWx0ZGljdChzZXQpCiAgICBuYW1lX3N1YiA9IGRlZmF1bHRkaWN0KHNldCkKICAgIGJvZHlfc3ViID0gZGVmYXVsdGRpY3Qoc2V0KQog
ICAgZm9yIHMsIGssIGUgaW4gaXRlbXM6CiAgICAgICAgaWYgZS5nZXQoInN0YXR1cyIpICE9ICJBQ1RJVkUiOgogICAgICAgICAgICBjb250aW51ZQogICAg
ICAgIGlmIGVbImtpbmQiXSBpbiAoIk1ETCIsICJFTkciKToKICAgICAgICAgICAgbW9kX3N1YltlWyJtb2R1bGUiXV0uYWRkKHMpCiAgICAgICAgaWYgZVsi
a2luZCJdIGluICgiRk5DIiwgIkNMUyIpOgogICAgICAgICAgICBzaG9ydCA9IGVbIm5hbWUiXS5zcGxpdCgiLiIpWy0xXQogICAgICAgICAgICBpZiBub3Qg
c2hvcnQuc3RhcnRzd2l0aCgiXyIpIGFuZCBzaG9ydCBub3QgaW4gKCJtYWluIiwgInNlbGZ0ZXN0IiwgImNoayIsICJydW4iKToKICAgICAgICAgICAgICAg
IG5hbWVfc3ViWyhlWyJraW5kIl0sIHNob3J0KV0uYWRkKHMpCiAgICAgICAgICAgIGlmIGUuZ2V0KCJib2R5X3NoYSIpOgogICAgICAgICAgICAgICAgYm9k
eV9zdWJbKGVbImtpbmQiXSwgZVsiYm9keV9zaGEiXSldLmFkZChzKQogICAgZm9yIHMsIGssIGUgaW4gaXRlbXM6CiAgICAgICAgc3QgPSBlLmdldCgic3Rh
dHVzIikKICAgICAgICBpZiBzdCA9PSAiUkVUSVJFRCIgYW5kIG5vdCBlLmdldCgicmVwbGFjZWRfYnkiKToKICAgICAgICAgICAgZmZsYWdzWyhzLCBrKV0u
YXBwZW5kKCgiRjUiLCAiUkVEIiwgIlJFVElSRUQg54ShIHJlcGxhY2VkX2J5IikpCiAgICAgICAgaWYgc3QgPT0gIkdPTkUiIGFuZCBub3QgZS5nZXQoInJl
cGxhY2VkX2J5Iik6CiAgICAgICAgICAgIGZmbGFnc1socywgayldLmFwcGVuZCgoIkYyIiwgIllFTExPVyIsICLmqLnkuIrkuI3opovkuJTnhKHmm7/ku6Mo
Z29uZV9zaW5jZSAlcykiICUgZS5nZXQoImdvbmVfc2luY2UiKSkpCiAgICAgICAgaWYgc3QgIT0gIkFDVElWRSI6CiAgICAgICAgICAgIGNvbnRpbnVlCiAg
ICAgICAgaWYgZVsia2luZCJdIGluICgiTURMIiwgIkVORyIpIGFuZCBsZW4obW9kX3N1YltlWyJtb2R1bGUiXV0pID4gMToKICAgICAgICAgICAgZmZsYWdz
WyhzLCBrKV0uYXBwZW5kKCgiRjEiLCAiUkVEIiwgIuWQjOaooee1hOaXj+WcqCAlcyIgJSAiLCIuam9pbihzb3J0ZWQobW9kX3N1YltlWyJtb2R1bGUiXV0p
KSkpCiAgICAgICAgaWYgZVsia2luZCJdIGluICgiRk5DIiwgIkNMUyIpOgogICAgICAgICAgICBzaG9ydCA9IGVbIm5hbWUiXS5zcGxpdCgiLiIpWy0xXQog
ICAgICAgICAgICBpZiBsZW4obmFtZV9zdWIuZ2V0KChlWyJraW5kIl0sIHNob3J0KSwgKCkpKSA+IDE6CiAgICAgICAgICAgICAgICBmZmxhZ3NbKHMsIGsp
XS5hcHBlbmQoKCJGMyIsICJZRUxMT1ciLCAi5ZCM5ZCN6Leo57O757WxICVzIiAlICIsIi5qb2luKHNvcnRlZChuYW1lX3N1YlsoZVsia2luZCJdLCBzaG9y
dCldKSkpKQogICAgICAgICAgICBpZiBsZW4oYm9keV9zdWIuZ2V0KChlWyJraW5kIl0sIGUuZ2V0KCJib2R5X3NoYSIpKSwgKCkpKSA+IDE6CiAgICAgICAg
ICAgICAgICBmZmxhZ3NbKHMsIGspXS5hcHBlbmQoKCJGMyIsICJZRUxMT1ciLCAi5ZCMIGJvZHkg6Leo57O757WxKOWAmemBuOWFseeUqCBMSUIpIikpCiAg
ICAgICAgaWYgZS5nZXQoInNpbWlsYXIiKToKICAgICAgICAgICAgZmZsYWdzWyhzLCBrKV0uYXBwZW5kKCgiRjMiLCAiWUVMTE9XIiwgIjsiLmpvaW4oZVsi
c2ltaWxhciJdKVs6MTIwXSkpCiAgICAgICAgaWYgYW55KCJBU1QiIGluIHggZm9yIHggaW4gZS5nZXQoImlzc3VlcyIsIFtdKSk6CiAgICAgICAgICAgIGZm
bGFnc1socywgayldLmFwcGVuZCgoIkY0IiwgIllFTExPVyIsICI7Ii5qb2luKGVbImlzc3VlcyJdKSkpCiAgICBmc2VxID0gZGVmYXVsdGRpY3QoaW50KQog
ICAgcnhmID0gcmUuY29tcGlsZShyIl5WSUEtKFx3KyktKE1ETHxFTkd8TElCKShcZHszLDR9KSQiKQogICAgZm9yIGNvZGUgaW4gbGlzdChuYmNbImZpbGUi
XS52YWx1ZXMoKSkgKyBbZVsiY29kZSJdIGZvciBlIGluIGZudW1bImVudHJpZXMiXV06CiAgICAgICAgbSA9IHJ4Zi5tYXRjaChzdHIoY29kZSkpCiAgICAg
ICAgaWYgbToKICAgICAgICAgICAgZnNlcVsobS5ncm91cCgxKSwgbS5ncm91cCgyKSldID0gbWF4KGZzZXFbKG0uZ3JvdXAoMSksIG0uZ3JvdXAoMikpXSwg
aW50KG0uZ3JvdXAoMykpKQogICAgY2hpbGRfc2VxID0gZGVmYXVsdGRpY3QoaW50KQogICAgZm9yIChwYXJlbnQsIHEpLCBjb2RlIGluIG5iY1sic3ViIl0u
aXRlbXMoKToKICAgICAgICBtID0gcmUubWF0Y2gociJeKC4qKS0oRk5DfENMUykoXGR7Myw0fSkkIiwgY29kZSkKICAgICAgICBpZiBtOgogICAgICAgICAg
ICBjaGlsZF9zZXFbKHBhcmVudCwgbS5ncm91cCgyKSldID0gbWF4KGNoaWxkX3NlcVsocGFyZW50LCBtLmdyb3VwKDIpKV0sIGludChtLmdyb3VwKDMpKSkK
ICAgIGZvciBlIGluIGZudW1bImVudHJpZXMiXToKICAgICAgICBtID0gcmUubWF0Y2gociJeKC4qKS0oRk5DfENMUykoXGR7Myw0fSkkIiwgc3RyKGUuZ2V0
KCJjb2RlIiwgIiIpKSkKICAgICAgICBpZiBtOgogICAgICAgICAgICBjaGlsZF9zZXFbKG0uZ3JvdXAoMSksIG0uZ3JvdXAoMikpXSA9IG1heChjaGlsZF9z
ZXFbKG0uZ3JvdXAoMSksIG0uZ3JvdXAoMikpXSwgaW50KG0uZ3JvdXAoMykpKQogICAgZmlsZV9jb2RlX25vdyA9IHt9CiAgICBjb3VudHMgPSB7IlJFRCI6
IDAsICJZRUxMT1ciOiAwLCAiR1JFRU4iOiAwfQogICAgb3JkZXIgPSBbIk1ETCIsICJFTkciLCAiTElCIiwgIkNMUyIsICJGTkMiXQogICAgZm9yIHMsIGss
IGUgaW4gc29ydGVkKGl0ZW1zLCBrZXk9bGFtYmRhIHg6IChvcmRlci5pbmRleCh4WzJdWyJraW5kIl0pIGlmIHhbMl1bImtpbmQiXSBpbiBvcmRlciBlbHNl
IDksIHhbMF0sIHhbMV0pKToKICAgICAgICBpZiBlLmdldCgic3RhdHVzIikgIT0gIkFDVElWRSI6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZmwg
PSBmZmxhZ3MuZ2V0KChzLCBrKSwgW10pCiAgICAgICAgbGFtcCA9ICJSRUQiIGlmIGFueSh4WzFdID09ICJSRUQiIGZvciB4IGluIGZsKSBlbHNlICgiWUVM
TE9XIiBpZiBmbCBlbHNlICJHUkVFTiIpCiAgICAgICAga2V5ID0gIiVzfCVzfCVzIiAlIChzLCBrLCBlLmdldCgidmVyc2lvbiIpKQogICAgICAgIGNvZGUg
PSBlLmdldCgibnVtYmVyIikgb3IgaGF2ZV9mLmdldChrZXksIHt9KS5nZXQoImNvZGUiLCAiIikKICAgICAgICByZWMgPSB7InN1YiI6IHMsICJrZXkiOiBr
LCAia2luZCI6IGVbImtpbmQiXSwgImxhbXAiOiBsYW1wLCAiZmxhZ3MiOiBbeyJydWxlIjogYSwgImxhbXAiOiBiLCAiZGV0YWlsIjogY30gZm9yIGEsIGIs
IGMgaW4gZmxdLCAiY29kZSI6IGNvZGUsICJ0ZXN0IjogTm9uZX0KICAgICAgICBpZiBsYW1wICE9ICJSRUQiIGFuZCBub3QgY29kZToKICAgICAgICAgICAg
b2ssIHdoeSA9IF90ZXN0X2ZuKFAsIGUpCiAgICAgICAgICAgIHJlY1sidGVzdCJdID0gIlBBU1MiIGlmIG9rIGVsc2UgIkZBSUw6IiArIHdoeQogICAgICAg
ICAgICBpZiBvazoKICAgICAgICAgICAgICAgIGlmIGVbImtpbmQiXSBpbiAoIk1ETCIsICJFTkciLCAiTElCIik6CiAgICAgICAgICAgICAgICAgICAgZXhp
c3RpbmcgPSBuYmNbImZpbGUiXS5nZXQoZS5nZXQoInNvdXJjZSIsICIiKSkgaWYgZVsia2luZCJdICE9ICJMSUIiIGVsc2UgTm9uZQogICAgICAgICAgICAg
ICAgICAgIGlmIGV4aXN0aW5nOgogICAgICAgICAgICAgICAgICAgICAgICBjb2RlID0gZXhpc3RpbmcKICAgICAgICAgICAgICAgICAgICBlbHNlOgogICAg
ICAgICAgICAgICAgICAgICAgICBmc2VxWyhzLCBlWyJraW5kIl0pXSArPSAxCiAgICAgICAgICAgICAgICAgICAgICAgIGNvZGUgPSAiVklBLSVzLSVzJTAz
ZCIgJSAocywgZVsia2luZCJdLCBmc2VxWyhzLCBlWyJraW5kIl0pXSkKICAgICAgICAgICAgICAgICAgICBpZiBlWyJraW5kIl0gIT0gIkxJQiI6CiAgICAg
ICAgICAgICAgICAgICAgICAgIGZpbGVfY29kZV9ub3dbKHMsIGVbIm1vZHVsZSJdKV0gPSBjb2RlCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAg
ICAgICAgICAgIHBhcmVudCA9IGZpbGVfY29kZV9ub3cuZ2V0KChzLCBlWyJtb2R1bGUiXSkpIG9yIG5iY1siZmlsZSJdLmdldChlLmdldCgic291cmNlIiwg
IiIpKSBvciBoYXZlX2YuZ2V0KCIlc3xNREx8JXN8JXMiICUgKHMsIGVbIm1vZHVsZSJdLCBlLmdldCgidmVyc2lvbiIpKSwge30pLmdldCgiY29kZSIpIG9y
IGhhdmVfZi5nZXQoIiVzfEVOR3wlc3wlcyIgJSAocywgZVsibW9kdWxlIl0sIGUuZ2V0KCJ2ZXJzaW9uIikpLCB7fSkuZ2V0KCJjb2RlIikKICAgICAgICAg
ICAgICAgICAgICBpZiBub3QgcGFyZW50OgogICAgICAgICAgICAgICAgICAgICAgICByZWNbInRlc3QiXSA9ICJXQUlUOueItuaqlOacquacieiZnyIKICAg
ICAgICAgICAgICAgICAgICAgICAgb3V0WyJmbnMiXVtrZXldID0gcmVjCiAgICAgICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAg
ICAgICAgZXhpc3RpbmcgPSBuYmNbInN1YiJdLmdldCgocGFyZW50LCBlWyJuYW1lIl0pKQogICAgICAgICAgICAgICAgICAgIGlmIGV4aXN0aW5nOgogICAg
ICAgICAgICAgICAgICAgICAgICBjb2RlID0gZXhpc3RpbmcKICAgICAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgICAgICBjaGls
ZF9zZXFbKHBhcmVudCwgZVsia2luZCJdKV0gKz0gMQogICAgICAgICAgICAgICAgICAgICAgICBjb2RlID0gIiVzLSVzJTAzZCIgJSAocGFyZW50LCBlWyJr
aW5kIl0sIGNoaWxkX3NlcVsocGFyZW50LCBlWyJraW5kIl0pXSkKICAgICAgICAgICAgICAgIGVudCA9IHsia2V5Ijoga2V5LCAiY29kZSI6IGNvZGUsICJz
dWIiOiBzLCAia2luZCI6IGVbImtpbmQiXSwgIm5hbWUiOiBlWyJuYW1lIl0sICJzb3VyY2UiOiBlLmdldCgic291cmNlIiksICJpc3N1ZWRfYXQiOiBub3cs
ICJub3RlIjogKCJ5ZWxsb3c6IiArICIsIi5qb2luKHhbMF0gZm9yIHggaW4gZmwpKSBpZiBmbCBlbHNlICIifQogICAgICAgICAgICAgICAgZm51bVsiZW50
cmllcyJdLmFwcGVuZChlbnQpCiAgICAgICAgICAgICAgICBoYXZlX2Zba2V5XSA9IGVudAogICAgICAgICAgICAgICAgcmVjWyJjb2RlIl0gPSBjb2RlCiAg
ICAgICAgICAgICAgICBvdXRbImlzc3VlZF9mbnMiXS5hcHBlbmQoZW50KQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgcmVjWyJsYW1wIl0g
PSAiUkVEIgogICAgICAgICAgICAgICAgcmVjWyJmbGFncyJdLmFwcGVuZCh7InJ1bGUiOiAiVEVTVCIsICJsYW1wIjogIlJFRCIsICJkZXRhaWwiOiB3aHl9
KQogICAgICAgIGNvdW50c1tyZWNbImxhbXAiXV0gKz0gMQogICAgICAgIG91dFsiZm5zIl1ba2V5XSA9IHJlYwogICAgdGMgPSB7IlJFRCI6IDAsICJZRUxM
T1ciOiAwLCAiR1JFRU4iOiAwfQogICAgZm9yIHIgaW4gb3V0WyJ0YWJsZXMiXS52YWx1ZXMoKToKICAgICAgICB0Y1tyWyJsYW1wIl1dICs9IDEKICAgIG91
dFsic3VtbWFyeSJdID0geyJ0YWJsZXMiOiBsZW4ob3V0WyJ0YWJsZXMiXSksICJ0X3JlZCI6IHRjWyJSRUQiXSwgInRfeWVsbG93IjogdGNbIllFTExPVyJd
LCAidF9ncmVlbiI6IHRjWyJHUkVFTiJdLCAidF9pc3N1ZWQiOiBsZW4ob3V0WyJpc3N1ZWRfdGFibGVzIl0pLAogICAgICAgICAgICAgICAgICAgICAgImZu
cyI6IGxlbihvdXRbImZucyJdKSwgImZfcmVkIjogY291bnRzWyJSRUQiXSwgImZfeWVsbG93IjogY291bnRzWyJZRUxMT1ciXSwgImZfZ3JlZW4iOiBjb3Vu
dHNbIkdSRUVOIl0sICJmX2lzc3VlZCI6IGxlbihvdXRbImlzc3VlZF9mbnMiXSksCiAgICAgICAgICAgICAgICAgICAgICAiYm9va3MiOiB7czogeyJ0YWJs
ZSI6IHRib29rc1tzXVsiZmlsZSJdLCAiZm4iOiBmYm9va3Nbc11bImZpbGUiXX0gZm9yIHMgaW4gU1VCU319CiAgICB0bnVtWyJibG9ja2VkIl0gPSBbayBm
b3IgaywgciBpbiBvdXRbInRhYmxlcyJdLml0ZW1zKCkgaWYgclsibGFtcCJdID09ICJSRUQiXQogICAgZm51bVsiYmxvY2tlZCJdID0gW2sgZm9yIGssIHIg
aW4gb3V0WyJmbnMiXS5pdGVtcygpIGlmIHJbImxhbXAiXSA9PSAiUkVEIl0KICAgIHRudW1bInVwZGF0ZWRfYXQiXSA9IGZudW1bInVwZGF0ZWRfYXQiXSA9
IG5vdwogICAgaWYgYXBwbHk6CiAgICAgICAgUFsicmVnaXN0cnkiXS5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICAgICAgKFBbInJl
Z2lzdHJ5Il0gLyAiVklBX1RhYmxlTnVtYmVyc192MDEwMC5qc29uIikud3JpdGVfdGV4dChqc29uLmR1bXBzKHRudW0sIGVuc3VyZV9hc2NpaT1GYWxzZSwg
aW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgICAgIChQWyJyZWdpc3RyeSJdIC8gIlZJQV9SZWdpc3RyeU51bWJlcnNfdjAxMDAuanNvbiIpLndy
aXRlX3RleHQoanNvbi5kdW1wcyhmbnVtLCBlbnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0xKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIG91dFsibGFtcCJd
ID0gIlJFRCIgaWYgKHRjWyJSRUQiXSBvciBjb3VudHNbIlJFRCJdKSBlbHNlICgiWUVMTE9XIiBpZiAodGNbIllFTExPVyJdIG9yIGNvdW50c1siWUVMTE9X
Il0pIGVsc2UgKCJHUkVFTiIgaWYgKG91dFsidGFibGVzIl0gb3Igb3V0WyJmbnMiXSkgZWxzZSAiR1JBWSIpKQogICAgZm9yIHMgaW4gU1VCUzoKICAgICAg
ICBpZiBub3QgdGJvb2tzW3NdWyJmaWxlIl06CiAgICAgICAgICAgIG91dFsiX25vdGVzIl0uYXBwZW5kKCIlcyDooajpoK3lhormnKrlu7oo5a2Q57O757Wx
5YWIIHRhYmxlIHJlZ2lzdGVyIC0tYXBwbHkpIiAlIHMpCiAgICAgICAgaWYgbm90IGZib29rc1tzXVsiZmlsZSJdOgogICAgICAgICAgICBvdXRbIl9ub3Rl
cyJdLmFwcGVuZCgiJXMg5Yqf6IO955+p6Zmj5pyq5bu6KOWtkOezu+e1seWFiCBmbiByZWdpc3RlciAtLWFwcGx5KSIgJSBzKQogICAgcmV0dXJuIG91dAoK
CmRlZiBfdGVzdF90YWJsZShQOiBkaWN0LCBlOiBkaWN0KToKICAgIHNyYyA9IFBbInJvb3QiXSAvIGUuZ2V0KCJzb3VyY2UiLCAiIikKICAgIGlmIG5vdCBz
cmMuZXhpc3RzKCk6CiAgICAgICAgcmV0dXJuIEZhbHNlLCAi5L6G5rqQ5LiN5ZyoICVzIiAlIGUuZ2V0KCJzb3VyY2UiKQogICAgdHJ5OgogICAgICAgIHRi
cyA9IF90aF9sb2FkX3RhYmxlcyhzcmMpCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGV4YzogICMgbm9xYTogQkxFMDAxCiAgICAgICAgcmV0dXJuIEZhbHNl
LCAi5L6G5rqQ6K6A5LiN5LqGICVzIiAlIHR5cGUoZXhjKS5fX25hbWVfXwogICAgcm93cyA9IHRicy5nZXQoZS5nZXQoInRhYmxlIikpCiAgICBpZiByb3dz
IGlzIE5vbmU6CiAgICAgICAgcmV0dXJuIEZhbHNlLCAi6KGoICVzIOS4jeWcqOS+hua6kCIgJSBlLmdldCgidGFibGUiKQogICAgY29scywga2V5cywgXyA9
IF90aF9wcm9maWxlKHJvd3MpCiAgICBoYXZlID0ge2NbIm5hbWUiXTogY1siZHR5cGUiXSBmb3IgYyBpbiBjb2xzfQogICAgbWlzc2luZyA9IFtjWyJuYW1l
Il0gZm9yIGMgaW4gZS5nZXQoImNvbHVtbnMiLCBbXSkgaWYgY1sibmFtZSJdIG5vdCBpbiBoYXZlIGFuZCBjWyJuYW1lIl0gIT0gIl9yaWQiXQogICAgaWYg
bWlzc2luZzoKICAgICAgICByZXR1cm4gRmFsc2UsICLmrITnvLogJXMiICUgIiwiLmpvaW4obWlzc2luZ1s6NV0pCiAgICBrZXlzID0gW2sgZm9yIGsgaW4g
KGUuZ2V0KCJrZXlzIikgb3IgW10pIGlmIGtdCiAgICBpZiBrZXlzOiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyB2MDEwMjrntYTlkIjp
jbXmlbTntYTmuKwoREYwNiDlhYHoqLHntYTlkIjpjbUpO19yaWQg5ZCI5oiQ6Y2154++566XIHNoYTgo5pW05YiXKQogICAgICAgIGltcG9ydCBoYXNobGli
IGFzIF9obAogICAgICAgIHR1cGxlcyA9IFtdCiAgICAgICAgc2Vlbl9oID0ge30KICAgICAgICBmb3IgciBpbiByb3dzOgogICAgICAgICAgICB0ID0gW10K
ICAgICAgICAgICAgZm9yIGsgaW4ga2V5czoKICAgICAgICAgICAgICAgIGlmIGsgPT0gIl9yaWQiOgogICAgICAgICAgICAgICAgICAgIGggPSBfcmlkX29m
KHIpCiAgICAgICAgICAgICAgICAgICAgbiA9IHNlZW5faC5nZXQoaCwgMCkKICAgICAgICAgICAgICAgICAgICBzZWVuX2hbaF0gPSBuICsgMQogICAgICAg
ICAgICAgICAgICAgIHQuYXBwZW5kKGggaWYgbiA9PSAwIGVsc2UgIiVzIyVkIiAlIChoLCBuKSkgICAjIOaVtOWIl+mHjeikhyDihpIg56ysIDIg5qyh6LW3
5bi25Ye654++5bqP6JmfLOS7jeWUr+S4gAogICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICB2ID0gci5nZXQoaykKICAgICAgICAg
ICAgICAgICAgICB0LmFwcGVuZCgiIiBpZiB2IGluIChOb25lLCAiIikgZWxzZSBzdHIodikpCiAgICAgICAgICAgIHR1cGxlcy5hcHBlbmQodHVwbGUodCkp
CiAgICAgICAgaWYgYW55KCIiIGluIHQgZm9yIHQgaW4gdHVwbGVzKSBvciBsZW4oc2V0KHR1cGxlcykpICE9IGxlbih0dXBsZXMpOgogICAgICAgICAgICBy
ZXR1cm4gRmFsc2UsICLkuLvpjbUgJXMg56m65oiW6YeN6KSHIiAlICIrIi5qb2luKGtleXMpCiAgICBiYWQgPSBbY1sibmFtZSJdIGZvciBjIGluIGUuZ2V0
KCJjb2x1bW5zIiwgW10pIGlmIGNbIm5hbWUiXSAhPSAiX3JpZCIgYW5kIGhhdmUuZ2V0KGNbIm5hbWUiXSkgIT0gY1siZHR5cGUiXV0KICAgIGlmIGJhZDoK
ICAgICAgICByZXR1cm4gRmFsc2UsICLlnovliKXkuI3nrKYgJXMiICUgIiwiLmpvaW4oYmFkWzo1XSkKICAgIHJldHVybiBUcnVlLCAiIgoKCmRlZiBfdGVz
dF9mbihQOiBkaWN0LCBlOiBkaWN0KToKICAgIGltcG9ydCBhc3QKICAgIHNyYyA9IFBbInJvb3QiXSAvIGUuZ2V0KCJzb3VyY2UiLCAiIikKICAgIGlmIG5v
dCBzcmMuZXhpc3RzKCk6CiAgICAgICAgcmV0dXJuIEZhbHNlLCAi5qqU5LiN5Zyo5qi55LiKIgogICAgaWYgZVsia2luZCJdID09ICJMSUIiOgogICAgICAg
IHJldHVybiBUcnVlLCAiIgogICAgdHJ5OgogICAgICAgIHRyZWUgPSBhc3QucGFyc2UoX2ZtX3JlYWQoc3JjKSkKICAgIGV4Y2VwdCAoU3ludGF4RXJyb3Is
IFZhbHVlRXJyb3IpIGFzIGV4YzoKICAgICAgICByZXR1cm4gRmFsc2UsICJBU1QgJXMiICUgdHlwZShleGMpLl9fbmFtZV9fCiAgICBpZiBlWyJraW5kIl0g
aW4gKCJNREwiLCAiRU5HIik6CiAgICAgICAgcmV0dXJuIFRydWUsICIiCiAgICBuYW1lcyA9IHNldCgpCiAgICBmb3Igbm9kZSBpbiB0cmVlLmJvZHk6CiAg
ICAgICAgaWYgaXNpbnN0YW5jZShub2RlLCBhc3QuQ2xhc3NEZWYpOgogICAgICAgICAgICBuYW1lcy5hZGQobm9kZS5uYW1lKQogICAgICAgICAgICBmb3Ig
biBpbiBub2RlLmJvZHk6CiAgICAgICAgICAgICAgICBpZiBpc2luc3RhbmNlKG4sIChhc3QuRnVuY3Rpb25EZWYsIGFzdC5Bc3luY0Z1bmN0aW9uRGVmKSk6
CiAgICAgICAgICAgICAgICAgICAgbmFtZXMuYWRkKCIlcy4lcyIgJSAobm9kZS5uYW1lLCBuLm5hbWUpKQogICAgICAgIGVsaWYgaXNpbnN0YW5jZShub2Rl
LCAoYXN0LkZ1bmN0aW9uRGVmLCBhc3QuQXN5bmNGdW5jdGlvbkRlZikpOgogICAgICAgICAgICBuYW1lcy5hZGQobm9kZS5uYW1lKQogICAgcmV0dXJuIChl
WyJuYW1lIl0gaW4gbmFtZXMpLCAoIiIgaWYgZVsibmFtZSJdIGluIG5hbWVzIGVsc2UgIumNteS4jeWcqCBBU1QiKQoKCmRlZiBwYXN0ZV9wYWNrKHJlczog
ZGljdCkgLT4gbGlzdDoKICAgIHMgPSByZXNbInN1bW1hcnkiXQogICAgTCA9IFsiW+ioiF0gdmNnYyByZWdpc3RyeSBnb3Zlcm4lcyDCtyDooaggJWQo57SF
ICVkIOm7gyAlZCDntqAgJWQg55m8ICVkKcK3IOWKnyAlZCjntIUgJWQg6buDICVkIOe2oCAlZCDnmbwgJWQpwrcgJXMiCiAgICAgICAgICUgKCIgLS1hcHBs
eSIgaWYgcmVzWyJhcHBseSJdIGVsc2UgIihkcnktcnVuIOS4jeWvq+iZnykiLCBzWyJ0YWJsZXMiXSwgc1sidF9yZWQiXSwgc1sidF95ZWxsb3ciXSwgc1si
dF9ncmVlbiJdLCBzWyJ0X2lzc3VlZCJdLCBzWyJmbnMiXSwgc1siZl9yZWQiXSwgc1siZl95ZWxsb3ciXSwgc1siZl9ncmVlbiJdLCBzWyJmX2lzc3VlZCJd
LCByZXNbImxhbXAiXSldCiAgICBmb3IgbiBpbiByZXNbIl9ub3RlcyJdOgogICAgICAgIEwuYXBwZW5kKCIgIFvms6hdICVzIiAlIG4pCiAgICByZWRzID0g
WyhrLCByKSBmb3IgaywgciBpbiByZXNbInRhYmxlcyJdLml0ZW1zKCkgaWYgclsibGFtcCJdID09ICJSRUQiXQogICAgZm9yIGssIHIgaW4gcmVkc1s6MTJd
OgogICAgICAgIEwuYXBwZW5kKCIgIFtSRURdIOihqCAlcyDCtyAlcyIgJSAoaywgIiB8ICIuam9pbigiJXMgJXMiICUgKGZbInJ1bGUiXSwgZlsiZGV0YWls
Il0pIGZvciBmIGluIHJbImZsYWdzIl0gaWYgZlsibGFtcCJdID09ICJSRUQiKSkpCiAgICBpZiBsZW4ocmVkcykgPiAxMjoKICAgICAgICBMLmFwcGVuZCgi
ICBbUkVEXSDooagg4oCmIOWPpiAlZCDlnKjljaEiICUgKGxlbihyZWRzKSAtIDEyKSkKICAgIGZyID0gWyhrLCByKSBmb3IgaywgciBpbiByZXNbImZucyJd
Lml0ZW1zKCkgaWYgclsibGFtcCJdID09ICJSRUQiXQogICAgZm9yIGssIHIgaW4gZnJbOjEyXToKICAgICAgICBMLmFwcGVuZCgiICBbUkVEXSDlip8gJXMg
wrcgJXMiICUgKGssICIgfCAiLmpvaW4oIiVzICVzIiAlIChmWyJydWxlIl0sIGZbImRldGFpbCJdKSBmb3IgZiBpbiByWyJmbGFncyJdIGlmIGZbImxhbXAi
XSA9PSAiUkVEIikpKQogICAgaWYgbGVuKGZyKSA+IDEyOgogICAgICAgIEwuYXBwZW5kKCIgIFtSRURdIOWKnyDigKYg5Y+mICVkIOWcqOWNoSIgJSAobGVu
KGZyKSAtIDEyKSkKICAgIGZyb20gY29sbGVjdGlvbnMgaW1wb3J0IENvdW50ZXIKICAgIHljID0gQ291bnRlcihmWyJydWxlIl0gZm9yIHIgaW4gbGlzdChy
ZXNbInRhYmxlcyJdLnZhbHVlcygpKSArIGxpc3QocmVzWyJmbnMiXS52YWx1ZXMoKSkgZm9yIGYgaW4gclsiZmxhZ3MiXSBpZiBmWyJsYW1wIl0gPT0gIllF
TExPVyIpCiAgICBMLmFwcGVuZCgiW+ioiF0g6buD54eI5o+Q6YaS5YiG6aGeIMK3ICIgKyAoIiDCtyAiLmpvaW4oIiVzPSVkIiAlIChrLCB2KSBmb3Igaywg
diBpbiBzb3J0ZWQoeWMuaXRlbXMoKSkpIG9yICLnhKEiKSkKICAgIGZvciBrLCByIGluIFsoaywgcikgZm9yIGssIHIgaW4gcmVzWyJ0YWJsZXMiXS5pdGVt
cygpIGlmIHJbImxhbXAiXSA9PSAiWUVMTE9XIl1bOjhdOgogICAgICAgIEwuYXBwZW5kKCIgIFtZRUxdIOihqCAlcyDCtyAlcyIgJSAoaywgIiB8ICIuam9p
bihmWyJkZXRhaWwiXSBmb3IgZiBpbiByWyJmbGFncyJdKVs6MTQwXSkpCiAgICBmb3IgaywgciBpbiBbKGssIHIpIGZvciBrLCByIGluIHJlc1siZm5zIl0u
aXRlbXMoKSBpZiByWyJsYW1wIl0gPT0gIllFTExPVyIgYW5kIHJbImtpbmQiXSBpbiAoIk1ETCIsICJFTkciKV1bOjhdOgogICAgICAgIEwuYXBwZW5kKCIg
IFtZRUxdIOWKnyAlcyDCtyAlcyIgJSAoaywgIiB8ICIuam9pbihmWyJkZXRhaWwiXSBmb3IgZiBpbiByWyJmbGFncyJdKVs6MTQwXSkpCiAgICBMLmFwcGVu
ZCgiTkVYVDogIiArICgi57SF6KGoL+e0heWKn+iyvOe1piBBSSDoo4Eo5pS56aCt5Ye65paw54mIIC8g6KOc5Li76Y21IC8g6YCA5b255bi25pu/5LujKeKG
kiDlrZDns7vntbHph43nmbvoqJgg4oaSIOacrOW8leaTjumHjei3kTvntqDlt7LnmbzomZ8g4oaSIOWtkOezu+e1sSB0YWJsZS9mbiBudW1iZXIgcHVsbCIg
aWYgcmVzWyJsYW1wIl0gPT0gIlJFRCIgZWxzZSAi6Zu257SFIOKGkiDlrZDns7vntbHot5EgdGFibGUgbnVtYmVyIHB1bGwgLyBmbiBudW1iZXIgcHVsbCDo
roDomZ876buD6KGo55WZ5Y2h6YCQ5om56KOBIikpCiAgICByZXR1cm4gTFs6MzAwXQoKCmRlZiB3cml0ZV9jYXJkKHJlczogZGljdCwgcGFjazogbGlzdCwg
UDogZGljdCB8IE5vbmUgPSBOb25lKSAtPiBkaWN0OgogICAgUCA9IFAgb3IgX3BhdGhzKCkKICAgIGRheSA9IGRhdGV0aW1lLmRhdGV0aW1lLm5vdygpLnN0
cmZ0aW1lKCIlWSVtJWQiKQogICAgUFsiY2FyZHMiXS5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICBQWyJyZXBvcnQiXS5ta2Rpcihw
YXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICBtZCA9IFBbImNhcmRzIl0gLyAoIlZDR0NfUmVnaXN0cnlHb3Zlcm5DYXJkXyVzLm1kIiAlIGRheSkK
ICAgIEwgPSBbIiMgVkNHQyDmr43ns7vntbEg5rK755CG5Y2hOuihqOmgreWGiiArIOWKn+iDveefqemZoyglcykiICUgZGF5LCAiIiwgIj4gTDExNCDikaI6
5a2Q57O757Wx55m76KiY55WZ55m9IOKGkiDmr43ns7vntbHpoa/npLrooZ3nqoEg4oaSIOaTjeS9nOWToStBSSDoo4Eg4oaSIOavjeezu+e1sea4rOippumA
mumBjueZvOiZnyDihpIg5a2Q57O757Wx6K6A5Zue5Lim6YG15a6I44CC57SFID0g5pOL6JmfO+m7gyA9IOaPkOmGkuS4jeaTi+OAgiIsICIiLCAiIyMg6LK8
5Zue5YyFIiwgImBgYCJdICsgcGFjayArIFsiYGBgIiwgIiIsCiAgICAgICAgICIjIyDooago5q+P6Y215LiA5YiXKSIsICJ8IOmNtSB8IOeHiCB8IOiZnyB8
IOa4rCB8IOaXlyB8IiwgInwtLS18LS0tfC0tLXwtLS18LS0tfCJdCiAgICBMICs9IFsifCAlcyB8ICVzIHwgJXMgfCAlcyB8ICVzIHwiICUgKGssIHJbImxh
bXAiXSwgclsidGFibGVfbm8iXSBvciAi55WZ55m9IiwgclsidGVzdCJdIG9yICLigJQiLCAiOyAiLmpvaW4oIiVzICVzIiAlIChmWyJydWxlIl0sIGZbImRl
dGFpbCJdKSBmb3IgZiBpbiByWyJmbGFncyJdKS5yZXBsYWNlKCJ8IiwgIsKmIikpIGZvciBrLCByIGluIHJlc1sidGFibGVzIl0uaXRlbXMoKV1bOjUwMF0K
ICAgIEwgKz0gWyIiLCAiIyMg5YqfKOWPquWIl+e0hS/pu4PoiIfmnKzovKrnmbzomZ8pIiwgInwg6Y21IHwg6aGeIHwg54eIIHwg6JmfIHwg5risIHwg5peX
IHwiLCAifC0tLXwtLS18LS0tfC0tLXwtLS18LS0tfCJdCiAgICBMICs9IFsifCAlcyB8ICVzIHwgJXMgfCAlcyB8ICVzIHwgJXMgfCIgJSAoaywgclsia2lu
ZCJdLCByWyJsYW1wIl0sIHJbImNvZGUiXSBvciAi55WZ55m9IiwgclsidGVzdCJdIG9yICLigJQiLCAiOyAiLmpvaW4oIiVzICVzIiAlIChmWyJydWxlIl0s
IGZbImRldGFpbCJdKSBmb3IgZiBpbiByWyJmbGFncyJdKS5yZXBsYWNlKCJ8IiwgIsKmIikpCiAgICAgICAgICBmb3IgaywgciBpbiByZXNbImZucyJdLml0
ZW1zKCkgaWYgclsibGFtcCJdICE9ICJHUkVFTiIgb3IgYW55KGVbImtleSJdID09IGsgZm9yIGUgaW4gcmVzWyJpc3N1ZWRfZm5zIl0pXVs6ODAwXQogICAg
bWQud3JpdGVfdGV4dCgiXG4iLmpvaW4oTCkgKyAiXG4iLCBlbmNvZGluZz0idXRmLTgiKQogICAgKFBbInJlcG9ydCJdIC8gIkdPVkVSTl9sYXRlc3QuanNv
biIpLndyaXRlX3RleHQoanNvbi5kdW1wcyhyZXMsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJu
IHsibWQiOiBzdHIobWQpfQoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9GUk9NX1ZDR0MiKSAhPSAi
WUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJuIDIKICAgIGEgPSBsaXN0
KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQogICAgaWYgIi0tc2VsZnRlc3QiIGluIGFbOjJdOgogICAgICAgIHJldHVybiBzZWxm
dGVzdCgpCiAgICBhcHBseSA9ICItLWFwcGx5IiBpbiBhCiAgICBpZiBhWzoxXSA9PSBbInJlZ2lzdGVyIl06CiAgICAgICAgciA9IHJlZ2lzdGVyKGFwcGx5
PWFwcGx5KQogICAgICAgIHQsIGYgPSByWyJ0YWJsZSJdLCByWyJmbiJdCiAgICAgICAgcHJpbnQoIlvoqIhdIHZjZ2MgcmVnaXN0ZXIlcyDCtyDooajpoK0g
JXMg6KGoICVkIOeVmeeZvSAlZCAlcyDCtyDnn6npmaMgJXMg6aCFICVkICVzIOebuOS8vCAlZCBBU1TlpLHmlZcgJWQg55WZ55m9ICVkIMK3IEdSRUVOIiAl
ICgiIC0tYXBwbHkiIGlmIGFwcGx5IGVsc2UgIihkcnktcnVuKSIsIHRbImJvb2siXSwgdFsidGFibGVzIl0sIHRbImJsYW5rIl0sIHRbImNvdW50cyJdLCBm
WyJib29rIl0sIGZbIml0ZW1zIl0sIGZbImtpbmRzIl0sIGZbInNpbWlsYXIiXSwgZlsiYXN0X2ZhaWwiXSwgZlsiYmxhbmsiXSkpCiAgICAgICAgcmV0dXJu
IDAKICAgIGlmIGFbOjFdID09IFsiZ292ZXJuIl06CiAgICAgICAgcmVzID0gZ292ZXJuKGFwcGx5PWFwcGx5KQogICAgICAgIHBhY2sgPSBwYXN0ZV9wYWNr
KHJlcykKICAgICAgICBjYXJkID0gd3JpdGVfY2FyZChyZXMsIHBhY2spCiAgICAgICAgZm9yIGxuIGluIHBhY2s6CiAgICAgICAgICAgIHByaW50KGxuKQog
ICAgICAgIHByaW50KCIgIFvljaFdICVzIiAlIGNhcmRbIm1kIl0pCiAgICAgICAgcmV0dXJuIDEgaWYgcmVzWyJsYW1wIl0gPT0gIlJFRCIgZWxzZSAwCiAg
ICBwcmludCgiW+aLkui3kV0gcmVnaXN0ZXIgWy0tYXBwbHldIHwgZ292ZXJuIFstLWFwcGx5XSB8IC0tc2VsZnRlc3QiKQogICAgcmV0dXJuIDIKCgoKCiMg
4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSAIHYwMTAxOnB1bGwoVkNH
QyDoh6rlt7HoroDomZ8pwrcgYW5ub3RhdGUoQVNUIOWIhumhniArIOiqquaYjuWBtOWGiikg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACl9DQVRfUlVMRVMgPSBbCiAgICAoIkVOVFJZIiwgciJeKG1haW58Y2xpfHJ1bnxzZWxm
dGVzdHxjaGspJCIpLCAoIkdBVEUiLCByIig/aSkoY2hlY2t8dmFsaWRhdGV8dmVyaWZ5fGdhdGV8dGVzdHxhc3NlcnR8Z3VhcmR8cHJlY2hlY2t8YXVkaXR8
dHJpYWdlKSIpLAogICAgKCJJT19SRUFEIiwgciIoP2kpKHJlYWR8bG9hZHxmZXRjaHxnZXR8c2NhbnxkaXNjb3ZlcnxmaW5kfGdsb2J8b3Blbnxkb3dubG9h
ZHxwdWxsKSIpLCAoIklPX1dSSVRFIiwgciIoP2kpKHdyaXRlfHNhdmV8ZW1pdHxleHBvcnR8ZHVtcHxwZXJzaXN0fGxlZGdlcnxhcHBlbmR8cHVibGlzaHxp
c3N1ZXxyZWdpc3RlcikiKSwKICAgICgiUEFSU0UiLCByIig/aSkocGFyc2V8ZXh0cmFjdHxzcGxpdHx0b2tlbml8YmxvY2t8dGFibGV8cGVyaW9kfGxhYmVs
fHJlZ2V4fG1hdGNoKSIpLCAoIkNMRUFOIiwgciIoP2kpKGNsZWFufG5vcm1hbHxzdGR8Y2Fub258c3RyaXB8ZGVkdXB8c2FuaXR8Zml4fHJlcGFpcikiKSwK
ICAgICgiUkVCVUlMRCIsIHIiKD9pKShyZWJ1aWxkfGJ1aWxkfG1lcmdlfGFzc2VtYmxlfGNvbXBvc2V8cmVjb25zdHJ1Y3R8cmVzdGF0dXN8cmViYWxhbmNl
fGFnZ3JlZ2F0ZXxtYXRyaXgpIiksICgiVUkiLCByIig/aSkoaHRtbHxyZW5kZXJ8dWl8cHJpbnR8c2hvd3xkaXNwbGF5fGNhcmR8cGFja3xjaGFydHxwbG90
KSIpLAogICAgKCJHT1ZFUk4iLCByIig/aSkobnVtYmVyfGdvdmVybnxzc290fGFkb3B0fHJldGlyZXxkb3JtYW50fGxhd3xwb2xpY3l8Y29sbGlzaW9ufHN1
cGVyc2VkZSkiKSwgKCJJTlRFUk5BTCIsIHIiXl8iKSwKXQoKCmRlZiBfY2F0X29mKG5hbWU6IHN0ciwgZG9jOiBzdHIpIC0+IHN0cjoKICAgIHNob3J0ID0g
bmFtZS5zcGxpdCgiLiIpWy0xXQogICAgZm9yIGNhdCwgcnggaW4gX0NBVF9SVUxFUzoKICAgICAgICBpZiByZS5zZWFyY2gocngsIHNob3J0KToKICAgICAg
ICAgICAgcmV0dXJuIGNhdAogICAgZm9yIGNhdCwgcnggaW4gX0NBVF9SVUxFU1sxOi0xXToKICAgICAgICBpZiBkb2MgYW5kIHJlLnNlYXJjaChyeCwgZG9j
Wzo4MF0pOgogICAgICAgICAgICByZXR1cm4gY2F0CiAgICByZXR1cm4gIk9USEVSIgoKCmRlZiBfZXhwbGFpbihlOiBkaWN0KSAtPiBzdHI6CiAgICBkb2Mg
PSAoZS5nZXQoImRvYyIpIG9yICIiKS5zdHJpcCgpCiAgICBpZiBkb2M6CiAgICAgICAgcmV0dXJuIGRvY1s6MTIwXQogICAgaywgbm0gPSBlLmdldCgia2lu
ZCIpLCBlLmdldCgibmFtZSIsICIiKQogICAgaWYgayA9PSAiTElCIjoKICAgICAgICByZXR1cm4gIuesrOS4ieaWueWll+S7tiAlcyhpbXBvcnQpIiAlIG5t
CiAgICBpZiBrID09ICJDTFMiOgogICAgICAgIHJldHVybiAi6aGe5YilICVzLCVkIOWAi+aWueazlSIgJSAobm0sIGUuZ2V0KCJtZXRob2RzIiwgMCkpCiAg
ICBpZiBrIGluICgiTURMIiwgIkVORyIpOgogICAgICAgIHJldHVybiAiJXMg5qih57WEICVzIMK3ICVkIOihjCIgJSAoIuW8leaTjiIgaWYgayA9PSAiRU5H
IiBlbHNlICLmqKHntYQiLCBubSwgZS5nZXQoImxpbmVzIiwgMCkpCiAgICBzaG9ydCA9IG5tLnNwbGl0KCIuIilbLTFdCiAgICB3b3JkcyA9IHJlLnN1Yihy
IltfXSsiLCAiICIsIHJlLnN1YihyIihbYS16XSkoW0EtWl0pIiwgciJcMSBcMiIsIHNob3J0KSkuc3RyaXAoKQogICAgcmV0dXJuICIlcyglcykiICUgKHdv
cmRzIG9yIHNob3J0LCBlLmdldCgiYXBpIiwgIiIpKVs6MTIwXQoKCmRlZiBwdWxsX3NlbGYoUDogZGljdCB8IE5vbmUgPSBOb25lKSAtPiBkaWN0OgogICAg
IiIiVkNHQyDoh6rlt7HnmoTlip/og73nn6npmaMgKyDooajpoK3lhorkvp3pjbXoroDlm57omZ8o6IiH5a2Q57O757WxIG1hbmFnZXIg55qEIGZuL3RhYmxl
IG51bWJlciBwdWxsIOWQjOS4gOW+iynjgIIiIiIKICAgIFAgPSBQIG9yIF9wYXRocygpCiAgICBub3cgPSBfbm93KCkKICAgIGYgPSBfZm1fcHVsbCgiVkNH
QyIsIFBbInJlZ2lzdHJ5Il0sIFBbInJlZ2lzdHJ5Il0sIG5vdywgVHJ1ZSkKICAgIHQgPSBfdGhfcHVsbCgiVkNHQyIsIFBbInJlZ2lzdHJ5Il0sIFBbInJl
Z2lzdHJ5Il0sIG5vdywgVHJ1ZSkKICAgIHJldHVybiB7InZlcmIiOiAicHVsbCIsICJmbiI6IGYsICJ0YWJsZSI6IHQsICJsYW1wIjogIkdSRUVOIiBpZiAo
Zi5nZXQoInBlbmRpbmciLCAxKSA9PSAwIGFuZCB0LmdldCgicGVuZGluZyIsIDEpID09IDApIGVsc2UgIllFTExPVyJ9CgoKZGVmIGFubm90YXRlKHN1Yjog
c3RyLCBQOiBkaWN0IHwgTm9uZSA9IE5vbmUsIGFwcGx5OiBib29sID0gVHJ1ZSkgLT4gZGljdDoKICAgICIiIuiugCA8U1VCPl9GdW5jdGlvbk1hdHJpeCDl
sL7niYgg4oaSIOavj+mghTpjb2RlKOiZnynCtyBjYXQo5YiG6aGeKcK3IHpoKOiqquaYjinCtyBoZWFsdGgg57SF6buDKOacieeahOipsSnihpIgVklBX0Fz
dEFubm90YXRpb25zXzxTVUI+X3YwMTAwLmpzb24oVkNHQyDlgbTlhoo75Y+q5aKeOuWQjOmNteWQjCBzaGEg5LiN5YuVKeOAgiIiIgogICAgUCA9IFAgb3Ig
X3BhdGhzKCkKICAgIGZiID0gX2Jvb2soUCwgc3ViLCAiRnVuY3Rpb25NYXRyaXgiKQogICAgaXRlbXMgPSAoZmJbImRhdGEiXSBvciB7fSkuZ2V0KCJpdGVt
cyIsIHt9KQogICAgb3V0X2ZwID0gUFsicmVnaXN0cnkiXSAvICgiVklBX0FzdEFubm90YXRpb25zXyVzX3YwMTAwLmpzb24iICUgc3ViKQogICAgcHJldiA9
IGpzb24ubG9hZHMoX3RoX3JlYWQob3V0X2ZwKSkgaWYgb3V0X2ZwLmV4aXN0cygpIGVsc2UgeyJzY2hlbWEiOiAiVklBLkFzdEFubm90YXRpb25zLnYxIiwg
InN1YiI6IHN1YiwgInZlcnNpb24iOiAidjAxMDAiLCAicnVsZSI6ICJWQ0dDIOWFqOaZryBBU1Qg5rOo5YWlOuWIhumhniArIOiqquaYjiArIOiZnyArIOWB
peW6t+aXlyzlgbTlhorkuI3mlLnljp/lp4vnorw76Y21ID0g5Yqf6IO955+p6Zmj6Y21O+WPquWinuS4jea4myIsICJjcmVhdGVkX2F0IjogX25vdygpLCAi
aXRlbXMiOiB7fX0KICAgIGhwID0gUFsicm9vdCJdIC8gIlZJQV9SZXBvcnRzIiAvIHN1Yi5sb3dlcigpIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIKICAgIHRy
eToKICAgICAgICBoZWFsdGggPSBqc29uLmxvYWRzKF90aF9yZWFkKGhwKSkgaWYgaHAuZXhpc3RzKCkgZWxzZSBOb25lCiAgICBleGNlcHQgVmFsdWVFcnJv
cjoKICAgICAgICBoZWFsdGggPSBOb25lCiAgICByZWRfZmlsZXMgPSB7clsidGFpbCJdOiAoIkFTVCDlo54iIGlmIG5vdCByLmdldCgiYXN0X29rIiwgVHJ1
ZSkgZWxzZSByLmdldCgibmV0X25vdGUiKSBvciAiIikgZm9yIHIgaW4gKGhlYWx0aCBvciB7fSkuZ2V0KCJmaWxlcyIsIFtdKSBpZiByLmdldCgibGFtcCIp
ID09ICJSRUQifQogICAgY2F0cyA9IENvdW50ZXIoKQogICAgbl9uZXcgPSBuX3NhbWUgPSAwCiAgICBmb3IgaywgZSBpbiBpdGVtcy5pdGVtcygpOgogICAg
ICAgIGlmIGUuZ2V0KCJzdGF0dXMiKSBub3QgaW4gKCJBQ1RJVkUiLCBOb25lKToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBlbnQgPSBwcmV2WyJp
dGVtcyJdLmdldChrKQogICAgICAgIGlmIGVudCBhbmQgZW50LmdldCgiYm9keV9zaGEiKSA9PSBlLmdldCgiYm9keV9zaGEiKSBhbmQgZW50LmdldCgiY29k
ZSIpID09IChlLmdldCgibnVtYmVyIikgb3IgZW50LmdldCgiY29kZSIpKToKICAgICAgICAgICAgbl9zYW1lICs9IDEKICAgICAgICAgICAgY2F0c1tlbnRb
ImNhdCJdXSArPSAxCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgY2F0ID0gX2NhdF9vZihlLmdldCgibmFtZSIsICIiKSwgZS5nZXQoImRvYyIsICIi
KSkgaWYgZS5nZXQoImtpbmQiKSBpbiAoIkZOQyIsICJDTFMiKSBlbHNlIGUuZ2V0KCJraW5kIikKICAgICAgICBzcmNfdGFpbCA9IFBhdGgoZS5nZXQoInNv
dXJjZSIsICIiKSkubmFtZQogICAgICAgIHByZXZbIml0ZW1zIl1ba10gPSB7ImtleSI6IGssICJzdWIiOiBzdWIsICJraW5kIjogZS5nZXQoImtpbmQiKSwg
Im1vZHVsZSI6IGUuZ2V0KCJtb2R1bGUiKSwgIm5hbWUiOiBlLmdldCgibmFtZSIpLCAidmVyc2lvbiI6IGUuZ2V0KCJ2ZXJzaW9uIiksICJjb2RlIjogZS5n
ZXQoIm51bWJlciIpIG9yICIiLCAiY2F0IjogY2F0LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgInpoIjogX2V4cGxhaW4oZSksICJhcGkiOiBlLmdl
dCgiYXBpIiwgIiIpLCAibGluZSI6IGUuZ2V0KCJsaW5lIiksICJib2R5X3NoYSI6IGUuZ2V0KCJib2R5X3NoYSIpLCAic2ltaWxhciI6IGUuZ2V0KCJzaW1p
bGFyIiwgW10pLCAiaGVhbHRoIjogcmVkX2ZpbGVzLmdldChzcmNfdGFpbCwgIiIpLCAiYW5ub3RhdGVkX2F0IjogX25vdygpfQogICAgICAgIGNhdHNbY2F0
XSArPSAxCiAgICAgICAgbl9uZXcgKz0gMQogICAgcHJldlsidXBkYXRlZF9hdCJdID0gX25vdygpCiAgICBwcmV2WyJzdW1tYXJ5Il0gPSB7Iml0ZW1zIjog
bGVuKHByZXZbIml0ZW1zIl0pLCAibnVtYmVyZWQiOiBzdW0oMSBmb3IgdiBpbiBwcmV2WyJpdGVtcyJdLnZhbHVlcygpIGlmIHYuZ2V0KCJjb2RlIikpLCAi
Y2F0cyI6IGRpY3QoY2F0cyksICJyZWRfZmlsZXMiOiBsZW4ocmVkX2ZpbGVzKX0KICAgIGlmIGFwcGx5OgogICAgICAgIG91dF9mcC53cml0ZV90ZXh0KGpz
b24uZHVtcHMocHJldiwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICByZXR1cm4geyJ2ZXJiIjogImFubm90
YXRlIiwgInN1YiI6IHN1YiwgImZpbGUiOiBvdXRfZnAubmFtZSwgIm5ldyI6IG5fbmV3LCAic2FtZSI6IG5fc2FtZSwgInN1bW1hcnkiOiBwcmV2WyJzdW1t
YXJ5Il0sICJsYW1wIjogIkdSRUVOIiBpZiBpdGVtcyBlbHNlICJHUkFZIiwgIl9ub3RlcyI6IChbXSBpZiBpdGVtcyBlbHNlIFsiJXMg5Yqf6IO955+p6Zmj
5pyq5bu6KOWtkOezu+e1seWFiCBmbiByZWdpc3RlciAtLWFwcGx5KSIgJSBzdWJdKX0KCgpfTUFJTl8wMTAwID0gbWFpbgoKCmRlZiBtYWluKGFyZ3Y9Tm9u
ZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9GUk9NX1ZDR0MiKSAhPSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOA
guWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJuIDIKICAgIGEgPSBsaXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBh
cmd2KQogICAgaWYgYVs6MV0gPT0gWyJwdWxsIl06CiAgICAgICAgciA9IHB1bGxfc2VsZigpCiAgICAgICAgcHJpbnQoIlvoqIhdIHZjZ2MgcHVsbCDCtyDl
ip8gZmlsbGVkICVzIGFscmVhZHkgJXMgcGVuZGluZyAlcyDCtyDooaggZmlsbGVkICVzIGFscmVhZHkgJXMgcGVuZGluZyAlcyDCtyAlcyIgJSAoclsiZm4i
XS5nZXQoImZpbGxlZCIpLCByWyJmbiJdLmdldCgiYWxyZWFkeSIpLCByWyJmbiJdLmdldCgicGVuZGluZyIpLCByWyJ0YWJsZSJdLmdldCgiZmlsbGVkIiks
IHJbInRhYmxlIl0uZ2V0KCJhbHJlYWR5IiksIHJbInRhYmxlIl0uZ2V0KCJwZW5kaW5nIiksIHJbImxhbXAiXSkpCiAgICAgICAgcmV0dXJuIDAKICAgIGlm
IGFbOjFdID09IFsiYW5ub3RhdGUiXToKICAgICAgICBzdWJzID0gW3ggZm9yIHggaW4gYVsxOl0gaWYgeCBpbiBTVUJTXSBvciBsaXN0KFNVQlMpCiAgICAg
ICAgcmMgPSAwCiAgICAgICAgZm9yIHN1YiBpbiBzdWJzOgogICAgICAgICAgICByID0gYW5ub3RhdGUoc3ViLCBhcHBseT0oIi0tZHJ5IiBub3QgaW4gYSkp
CiAgICAgICAgICAgIHMgPSByWyJzdW1tYXJ5Il0KICAgICAgICAgICAgcHJpbnQoIlvoqIhdIGFubm90YXRlICVzIMK3ICVzIMK3IOaWsOazqCAlZCDlkIwg
JWQgwrcg6aCFICVkIOacieiZnyAlZCDCtyDliIbpoZ4gJXMgwrcg57SF5qqUICVkIMK3ICVzIiAlIChzdWIsIHJbImZpbGUiXSwgclsibmV3Il0sIHJbInNh
bWUiXSwgc1siaXRlbXMiXSwgc1sibnVtYmVyZWQiXSwganNvbi5kdW1wcyhzWyJjYXRzIl0sIGVuc3VyZV9hc2NpaT1GYWxzZSksIHNbInJlZF9maWxlcyJd
LCByWyJsYW1wIl0pKQogICAgICAgICAgICBmb3IgbiBpbiByWyJfbm90ZXMiXToKICAgICAgICAgICAgICAgIHByaW50KCIgIFvms6hdICVzIiAlIG4pCiAg
ICAgICAgcmV0dXJuIHJjCiAgICByZXR1cm4gX01BSU5fMDEwMChhcmd2KQoKCgoKIyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAgdjAxMDI6cmVzb2x2ZSjntIXooajliIbljYDliJfnrqEgwrcg57WE5ZCI6Y21IMK3IOmBjuaZ
gumAgOW9uSDCtyDpm7bkuZ3poK3pvo0pIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgApfUlVMSU5HUyA9ICJWSUFfS2V5UnVsaW5nc192MDEwMC5qc29uIgpfT0JTX1JYID0gcmUuY29tcGlsZShyIl4oP1A8cHJlZml4Pi4rPylf
dig/UDxuPlxkezIsM30pXyg/UDxyZXN0Pi4rKSQiLCByZS5JKSAgICMgVklBX0FjdGl2YXRpb25HYXRld2F5X3YwM19TdGFibGVIb3RmaXhfTWFuaWZlc3Qg
6YCZ6aGe44CM54mI6Jmf5Zyo5ZCN5a2X5Lit5q6144CN55qE5aSa6aCt5pePCgoKZGVmIF9jb21wb3NpdGVfa2V5KHJvd3M6IGxpc3QsIGNvbHM6IGxpc3Qs
IG1heGs6IGludCA9IDMpOgogICAgIiIi5pyA5bCP57WE5ZCI6Y21OjEg5qyEIOKGkiAyIOashCDihpIgMyDmrIQs5YWo6Z2e56m65LiU5LiN6YeN6KSHO+aJ
vuS4jeWIsOWbniBOb25l44CCIiIiCiAgICBpbXBvcnQgaXRlcnRvb2xzCiAgICBjYW5kID0gW2NbIm5hbWUiXSBmb3IgYyBpbiBjb2xzIGlmIGNbImR0eXBl
Il0gaW4gKCJzdHIiLCAiaW50IiwgImRhdGUiKV0KICAgIGZvciBrIGluIHJhbmdlKDEsIG1heGsgKyAxKToKICAgICAgICBmb3IgY29tYm8gaW4gaXRlcnRv
b2xzLmNvbWJpbmF0aW9ucyhjYW5kLCBrKToKICAgICAgICAgICAgdmFscyA9IFt0dXBsZShzdHIoci5nZXQoYykgaWYgci5nZXQoYykgaXMgbm90IE5vbmUg
ZWxzZSAiIikuc3RyaXAoKSBmb3IgYyBpbiBjb21ibykgZm9yIHIgaW4gcm93c10KICAgICAgICAgICAgaWYgYWxsKGFsbCh2IGZvciB2IGluIHQpIGZvciB0
IGluIHZhbHMpIGFuZCBsZW4oc2V0KHZhbHMpKSA9PSBsZW4odmFscyk6CiAgICAgICAgICAgICAgICByZXR1cm4gbGlzdChjb21ibykKICAgIHJldHVybiBO
b25lCgoKZGVmIF9ib29rX2RpcihQOiBkaWN0LCBzdWI6IHN0cikgLT4gUGF0aDoKICAgIHJldHVybiB7IlZDR0MiOiBQWyJyZWdpc3RyeSJdLCAiVkRGIjog
UFsidmRmIl0gLyAicmVnaXN0cnkiLCAiVlJOIjogUFsidnJuIl0gLyAicmVnaXN0cnkifVtzdWJdCgoKCmRlZiBfYWRvcHRfcnVsaW5nc192Y2djKGJvb2s6
IGRpY3QsIHJ1bGluZ3M6IGRpY3QsIG5vdzogc3RyKSAtPiBpbnQ6CiAgICAiIiJWQ0dDIOiHquWutuihqOmgreWGiuaOoee0jeijgeWumumNtSjoo4Hlrprl
hKrlhYjmlrzoh6rli5XliZbmnpDpjbU76IiK6Y2155WZIHByZXZfa2V5cztfcmlkIOWQiOaIkOmNteWKoOashOaomSBzeW50aGV0aWMpO+WbnuaOoee0jeaV
uOOAgiIiIgogICAgbiA9IDAKICAgIGZvciB0aWQsIHIgaW4gKHJ1bGluZ3MuZ2V0KCJ0YWJsZXMiKSBvciB7fSkuaXRlbXMoKToKICAgICAgICBlID0gKGJv
b2suZ2V0KCJ0YWJsZXMiKSBvciB7fSkuZ2V0KHRpZCkKICAgICAgICBpZiBub3QgZSBvciByLmdldCgic3ViIikgIT0gIlZDR0MiIG9yIGxpc3QoZS5nZXQo
ImtleXMiKSBvciBbXSkgPT0gbGlzdChyWyJrZXlzIl0pOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIGUuZ2V0KCJrZXlzIik6CiAgICAgICAg
ICAgIGVbInByZXZfa2V5cyJdID0gZVsia2V5cyJdCiAgICAgICAgZVsia2V5cyJdID0gbGlzdChyWyJrZXlzIl0pCiAgICAgICAgZm9yIGMgaW4gZS5nZXQo
ImNvbHVtbnMiLCBbXSk6CiAgICAgICAgICAgIGNbInBrIl0gPSBjWyJuYW1lIl0gaW4gclsia2V5cyJdCiAgICAgICAgaWYgci5nZXQoImtpbmQiKSA9PSAi
c3ludGhldGljIiBhbmQgbm90IGFueShjWyJuYW1lIl0gPT0gIl9yaWQiIGZvciBjIGluIGUuZ2V0KCJjb2x1bW5zIiwgW10pKToKICAgICAgICAgICAgZVsi
Y29sdW1ucyJdLmFwcGVuZCh7Im5hbWUiOiAiX3JpZCIsICJkdHlwZSI6ICJzdHIiLCAicmVxdWlyZWQiOiBUcnVlLCAicGsiOiBUcnVlLCAic3ludGhldGlj
IjogInNoYTgo5pW05YiXKSJ9KQogICAgICAgIGVbImtleV9ydWxpbmciXSA9IHIuZ2V0KCJraW5kIikKICAgICAgICBlWyJrZXlfcnVsZWRfYXQiXSA9IG5v
dwogICAgICAgIG4gKz0gMQogICAgcmV0dXJuIG4KCgpkZWYgX3J1bGluZ3NfYm9vayhQOiBkaWN0KSAtPiBkaWN0OgogICAgZnAgPSBQWyJyZWdpc3RyeSJd
IC8gX1JVTElOR1MKICAgIHRyeToKICAgICAgICByZXR1cm4ganNvbi5sb2FkcyhfdGhfcmVhZChmcCkpIGlmIGZwLmV4aXN0cygpIGVsc2Uge30KICAgIGV4
Y2VwdCBWYWx1ZUVycm9yOgogICAgICAgIHJldHVybiB7fQoKCmRlZiByZXNvbHZlKFA6IGRpY3QgfCBOb25lID0gTm9uZSwgYXBwbHk6IGJvb2wgPSBGYWxz
ZSkgLT4gZGljdDoKICAgIFAgPSBQIG9yIF9wYXRocygpCiAgICBub3cgPSBfbm93KCkKICAgIGdvdiA9IGpzb24ubG9hZHMoX3RoX3JlYWQoUFsicm9vdCJd
IC8gIlZJQV9SZXBvcnRzIiAvICJyZXZpZXciIC8gInZjZ2NfcmVnaXN0cnkiIC8gIkdPVkVSTl9sYXRlc3QuanNvbiIpKSBpZiAoUFsicm9vdCJdIC8gIlZJ
QV9SZXBvcnRzIiAvICJyZXZpZXciIC8gInZjZ2NfcmVnaXN0cnkiIC8gIkdPVkVSTl9sYXRlc3QuanNvbiIpLmV4aXN0cygpIGVsc2UgTm9uZQogICAgb3V0
ID0geyJ2ZXJiIjogInJlc29sdmUiLCAiYXBwbHkiOiBhcHBseSwgInpvbmVzIjogeyJDT01QT1NJVEVfS0VZIjogW10sICJTWU5USEVUSUNfS0VZIjogW10s
ICJPQlNPTEVURSI6IFtdLCAiRFJJRlQiOiBbXSwgIkRVUF9LRVkiOiBbXSwgIlVOUkVTT0xWRUQiOiBbXX0sICJfbm90ZXMiOiBbXX0KICAgIGlmIG5vdCBn
b3Y6CiAgICAgICAgb3V0WyJfbm90ZXMiXS5hcHBlbmQoIkdPVkVSTl9sYXRlc3QuanNvbiDkuI3lnKg65YWIIGdvdmVybiIpCiAgICAgICAgb3V0WyJsYW1w
Il0gPSAiR1JBWSIKICAgICAgICByZXR1cm4gb3V0CiAgICBydWxfZnAgPSBQWyJyZWdpc3RyeSJdIC8gX1JVTElOR1MKICAgIHJ1bGluZ3MgPSBqc29uLmxv
YWRzKF90aF9yZWFkKHJ1bF9mcCkpIGlmIHJ1bF9mcC5leGlzdHMoKSBlbHNlIHsic2NoZW1hIjogIlZJQS5LZXlSdWxpbmdzLnYxIiwgInZlcnNpb24iOiAi
djAxMDAiLCAiZW5naW5lIjogTkFNRSwgInJ1bGUiOiAi5q+N57O757Wx6KOB5a6a5pu4OuWtkOezu+e1sSBtYW5hZ2VyIOS4i+asoSB0YWJsZSByZWdpc3Rl
ciDoroDmraTlhormjqHnlKjpjbU7VkNHQyDoh6rlrrblhornm7TmjqXmjqHnlKg76YGO5pmC5peP6YCA5b255bi2IHJlcGxhY2VkX2J5O+WPquWinuS4jea4
myIsICJjcmVhdGVkX2F0Ijogbm93LCAidGFibGVzIjoge30sICJyZXRpcmUiOiB7fX0KICAgIGJvb2tzID0ge3M6IF9ib29rKFAsIHMsICJUYWJsZUhlYWRl
ciIpIGZvciBzIGluIFNVQlN9CiAgICAjIOKRoCDntIXooajpgJDlvLUKICAgIGZvciBrZXksIHJlYyBpbiBnb3YuZ2V0KCJ0YWJsZXMiLCB7fSkuaXRlbXMo
KToKICAgICAgICBpZiByZWMuZ2V0KCJsYW1wIikgIT0gIlJFRCI6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgc3ViLCB0aWQgPSByZWNbInN1YiJd
LCByZWNbInRpZCJdCiAgICAgICAgZW50ID0gKGJvb2tzW3N1Yl1bImRhdGEiXS5nZXQoInRhYmxlcyIpIG9yIHt9KS5nZXQodGlkLCB7fSkgaWYgYm9va3Nb
c3ViXVsiZGF0YSJdIGVsc2Uge30KICAgICAgICBjb2RlcyA9IHtmWyJydWxlIl0gZm9yIGYgaW4gcmVjLmdldCgiZmxhZ3MiLCBbXSl9IHwgKHsiVEVTVCJ9
IGlmIGFueShmWyJydWxlIl0gPT0gIlRFU1QiIGZvciBmIGluIHJlYy5nZXQoImZsYWdzIiwgW10pKSBlbHNlIHNldCgpKQogICAgICAgIHNyYyA9IFBbInJv
b3QiXSAvIGVudC5nZXQoInNvdXJjZSIsICIiKQogICAgICAgIGlmICJUMyIgaW4gY29kZXM6CiAgICAgICAgICAgIG91dFsiem9uZXMiXVsiRFJJRlQiXS5h
cHBlbmQoeyJzdWIiOiBzdWIsICJ0aWQiOiB0aWQsICJhY3Rpb24iOiAiUkVUSVJFX09MRF9IRUFEIiwgIm5ld190aWQiOiAoZW50LmdldCgiZHJpZnQiKSBv
ciB7fSkuZ2V0KCJuZXdfdGlkIiksICJrZWVwX25vIjogZW50LmdldCgidGFibGVfbm8iKX0pCiAgICAgICAgICAgIHJ1bGluZ3NbInJldGlyZSJdW3RpZF0g
PSB7InN1YiI6IHN1YiwgIndoeSI6ICJUMyDlt7LomZ/ooajpoK3mvILnp7s66IiK6aCt6YCA5b25LOiZn+eVmeiIiumgreS4jeWGjeeUqDvmlrDpoK0gJXMg
5o6l6JmfIiAlIChlbnQuZ2V0KCJkcmlmdCIpIG9yIHt9KS5nZXQoIm5ld190aWQiKSwgInJlcGxhY2VkX2J5IjogKGVudC5nZXQoImRyaWZ0Iikgb3Ige30p
LmdldCgibmV3X3RpZCIpLCAidHMiOiBub3d9CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgaWYgbm90IHNyYy5leGlzdHMoKSBvciBub3QgZW50Ogog
ICAgICAgICAgICBvdXRbInpvbmVzIl1bIlVOUkVTT0xWRUQiXS5hcHBlbmQoeyJzdWIiOiBzdWIsICJ0aWQiOiB0aWQsICJ3aHkiOiAi5L6G5rqQ5oiW6KGo
6aCt5YaK6aCF5LiN5ZyoIn0pCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgdHJ5OgogICAgICAgICAgICByb3dzID0gX3RoX2xvYWRfdGFibGVzKHNy
YykuZ2V0KGVudC5nZXQoInRhYmxlIiksIFtdKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246ICAjIG5vcWE6IEJMRTAwMQogICAgICAgICAgICByb3dzID0g
W10KICAgICAgICBpZiBub3Qgcm93czoKICAgICAgICAgICAgb3V0WyJ6b25lcyJdWyJVTlJFU09MVkVEIl0uYXBwZW5kKHsic3ViIjogc3ViLCAidGlkIjog
dGlkLCAid2h5IjogIuS+hua6kOiugOS4jeWHuuWIlyJ9KQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGNvbHMsIF8sIF8gPSBfdGhfcHJvZmlsZShy
b3dzKQogICAgICAgIGNrID0gX2NvbXBvc2l0ZV9rZXkocm93cywgY29scykKICAgICAgICBpZiBjazoKICAgICAgICAgICAgem9uZSA9ICJDT01QT1NJVEVf
S0VZIgogICAgICAgICAgICBydWxpbmdzWyJ0YWJsZXMiXVt0aWRdID0geyJzdWIiOiBzdWIsICJrZXlzIjogY2ssICJraW5kIjogImNvbXBvc2l0ZSIsICJ3
aHkiOiAiVDIvVEVTVDrmnIDlsI/ntYTlkIjpjbUoREYwNiDntYTlkIjpjbUpIiwgInRzIjogbm93fQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHpvbmUg
PSAiU1lOVEhFVElDX0tFWSIKICAgICAgICAgICAgcnVsaW5nc1sidGFibGVzIl1bdGlkXSA9IHsic3ViIjogc3ViLCAia2V5cyI6IFsiX3JpZCJdLCAia2lu
ZCI6ICJzeW50aGV0aWMiLCAid2h5IjogIueEoeS7u+S9lee1hOWQiOmNtSDihpIg5ZCI5oiQ5YiX6Y21IF9yaWQgPSBzaGE4KOaVtOWIlyk755m76KiY5pmC
55SxIG1hbmFnZXIg5Yqg5qyELOWOn+WGiuS4jeaUuSIsICJ0cyI6IG5vd30KICAgICAgICBvdXRbInpvbmVzIl1bem9uZV0uYXBwZW5kKHsic3ViIjogc3Vi
LCAidGlkIjogdGlkLCAia2V5cyI6IHJ1bGluZ3NbInRhYmxlcyJdW3RpZF1bImtleXMiXSwgInJvd3MiOiBsZW4ocm93cyl9KQogICAgIyDikaEg6YGO5pmC
5aSa6aCt5pePKOWQjeWtl+S4reauteW4tiBfdk5OXyk65ZCM5YmN57a0K+WQjOWwviDihpIg55WZ5pyA6auY54mICiAgICBmYW1zID0gZGVmYXVsdGRpY3Qo
bGlzdCkKICAgIGZvciBzIGluIFNVQlM6CiAgICAgICAgZm9yIHRpZCwgZW50IGluICgoYm9va3Nbc11bImRhdGEiXSBvciB7fSkuZ2V0KCJ0YWJsZXMiKSBv
ciB7fSkuaXRlbXMoKToKICAgICAgICAgICAgc3JjX25hbWUgPSBQYXRoKGVudC5nZXQoInNvdXJjZSIsICIiKSkubmFtZQogICAgICAgICAgICBtID0gX09C
U19SWC5tYXRjaChfdGhfZmFtaWx5KHNyY19uYW1lKSkKICAgICAgICAgICAgaWYgbToKICAgICAgICAgICAgICAgIGZhbXNbKHMsIG0uZ3JvdXAoInByZWZp
eCIpLmxvd2VyKCksIG0uZ3JvdXAoInJlc3QiKS5sb3dlcigpKV0uYXBwZW5kKChpbnQobS5ncm91cCgibiIpKSwgdGlkLCBzcmNfbmFtZSkpCiAgICBmb3Ig
KHMsIHByZWZpeCwgcmVzdCksIGxzdCBpbiBmYW1zLml0ZW1zKCk6CiAgICAgICAgaWYgbGVuKGxzdCkgPCAyOgogICAgICAgICAgICBjb250aW51ZQogICAg
ICAgIGxzdC5zb3J0KCkKICAgICAgICBrZWVwID0gbHN0Wy0xXQogICAgICAgIGZvciBuLCB0aWQsIHNyY19uYW1lIGluIGxzdFs6LTFdOgogICAgICAgICAg
ICBvdXRbInpvbmVzIl1bIk9CU09MRVRFIl0uYXBwZW5kKHsic3ViIjogcywgInRpZCI6IHRpZCwgImZpbGUiOiBzcmNfbmFtZSwgInJlcGxhY2VkX2J5Ijog
a2VlcFsyXSwgImFjdGlvbiI6ICJSRVRJUkUo56e7IF9zdXBlcnNlZGVkLOS4jeavgCkiIGlmIHMgPT0gIlZDR0MiIGVsc2UgIlJVTElORyjkuqQgJXMgbWFu
YWdlcikiICUgc30pCiAgICAgICAgICAgIHJ1bGluZ3NbInJldGlyZSJdW3RpZF0gPSB7InN1YiI6IHMsICJ3aHkiOiAi6YGO5pmC5aSa6aCt5pePICVzX3Yl
MDJkXyVzLOacgOmrmOeJiCAlcyDnlZk75YW26aSY6YCA5b25IiAlIChwcmVmaXgsIG4sIHJlc3QsIGtlZXBbMl0pLCAicmVwbGFjZWRfYnkiOiBrZWVwWzFd
LCAiZmlsZSI6IHNyY19uYW1lLCAidHMiOiBub3d9CiAgICAjIOKRoiDlpZfnlKg6VkNHQyDoh6rlrrYo6KGo6aCt5YaK6Y21ICsg6YGO5pmC5YaK56e7IF9z
dXBlcnNlZGVkKTvlrZDns7vntbHlj6rnlZnoo4Hlrprmm7gKICAgIGFwcGxpZWQgPSB7InZjZ2Nfa2V5cyI6IDAsICJ2Y2djX3JldGlyZWQiOiAwLCAibGVk
Z2VyIjogMH0KICAgIGlmIGFwcGx5OgogICAgICAgIHJ1bF9mcC53cml0ZV90ZXh0KGpzb24uZHVtcHMocnVsaW5ncywgZW5zdXJlX2FzY2lpPUZhbHNlLCBp
bmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICAgICAgdmIgPSBib29rc1siVkNHQyJdCiAgICAgICAgaWYgdmJbImRhdGEiXToKICAgICAgICAgICAg
YXBwbGllZFsidmNnY19rZXlzIl0gPSBfYWRvcHRfcnVsaW5nc192Y2djKHZiWyJkYXRhIl0sIHJ1bGluZ3MsIG5vdykKICAgICAgICAgICAgc3VwID0gUFsi
cmVnaXN0cnkiXSAvICJfc3VwZXJzZWRlZCIKICAgICAgICAgICAgbGVkID0gUFsicmVnaXN0cnkiXSAvICJWQ0dDX1JldGlyZV9MZWRnZXIuanNvbmwiCiAg
ICAgICAgICAgIGZvciB0aWQsIHIgaW4gcnVsaW5nc1sicmV0aXJlIl0uaXRlbXMoKToKICAgICAgICAgICAgICAgIGlmIHJbInN1YiJdID09ICJWQ0dDIiBh
bmQgdGlkIGluIHZiWyJkYXRhIl0uZ2V0KCJ0YWJsZXMiLCB7fSk6CiAgICAgICAgICAgICAgICAgICAgZSA9IHZiWyJkYXRhIl1bInRhYmxlcyJdW3RpZF0K
ICAgICAgICAgICAgICAgICAgICBpZiBlLmdldCgic3RhdHVzIikgPT0gIlJFVElSRUQiOgogICAgICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAg
ICAgICAgICAgICAgICAgIGUudXBkYXRlKHN0YXR1cz0iUkVUSVJFRCIsIHJldGlyZWRfYXQ9bm93LCByZXBsYWNlZF9ieT1yLmdldCgicmVwbGFjZWRfYnki
KSwgcmV0aXJlX3JlYXNvbj1yWyJ3aHkiXSkKICAgICAgICAgICAgICAgICAgICBhcHBsaWVkWyJ2Y2djX3JldGlyZWQiXSArPSAxCiAgICAgICAgICAgICAg
ICAgICAgc3JjcCA9IFBbInJvb3QiXSAvIGUuZ2V0KCJzb3VyY2UiLCAiIikKICAgICAgICAgICAgICAgICAgICBpZiByLmdldCgiZmlsZSIpIGFuZCBzcmNw
LmV4aXN0cygpIGFuZCBzcmNwLnBhcmVudCA9PSBQWyJyZWdpc3RyeSJdOgogICAgICAgICAgICAgICAgICAgICAgICBzdXAubWtkaXIoZXhpc3Rfb2s9VHJ1
ZSkKICAgICAgICAgICAgICAgICAgICAgICAgZHN0ID0gc3VwIC8gKHNyY3AubmFtZSArICIuUkVUSVJFRF8iICsgbm93LnJlcGxhY2UoIjoiLCAiIikucmVw
bGFjZSgiLSIsICIiKVs6MTVdKQogICAgICAgICAgICAgICAgICAgICAgICBfX2ltcG9ydF9fKCJzaHV0aWwiKS5tb3ZlKHN0cihzcmNwKSwgc3RyKGRzdCkp
CiAgICAgICAgICAgICAgICAgICAgICAgIHdpdGggb3BlbihsZWQsICJhIiwgZW5jb2Rpbmc9InV0Zi04IikgYXMgZmg6CiAgICAgICAgICAgICAgICAgICAg
ICAgICAgICBmaC53cml0ZShqc29uLmR1bXBzKHsidHMiOiBub3csICJ0aWQiOiB0aWQsICJmcm9tIjogc3JjcC5uYW1lLCAidG8iOiBkc3QubmFtZSwgInJl
cGxhY2VkX2J5Ijogci5nZXQoInJlcGxhY2VkX2J5IiksICJ3aHkiOiByWyJ3aHkiXX0sIGVuc3VyZV9hc2NpaT1GYWxzZSkgKyAiXG4iKQogICAgICAgICAg
ICAgICAgICAgICAgICBhcHBsaWVkWyJsZWRnZXIiXSArPSAxCiAgICAgICAgICAgIHZiWyJwYXRoIl0ud3JpdGVfdGV4dChqc29uLmR1bXBzKHZiWyJkYXRh
Il0sIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgb3V0WyJhcHBsaWVkIl0gPSBhcHBsaWVkCiAgICBvdXRb
InJ1bGluZ3NfZmlsZSJdID0gc3RyKHJ1bF9mcCkKICAgIG91dFsiY291bnRzIl0gPSB7azogbGVuKHYpIGZvciBrLCB2IGluIG91dFsiem9uZXMiXS5pdGVt
cygpfQogICAgb3V0WyJsYW1wIl0gPSAiWUVMTE9XIiBpZiAob3V0WyJ6b25lcyJdWyJVTlJFU09MVkVEIl0gb3Igbm90IGFwcGx5KSBlbHNlICJHUkVFTiIK
ICAgIHJldHVybiBvdXQKCgpkZWYgX3ByaW50X3Jlc29sdmUocjogZGljdCkgLT4gTm9uZToKICAgIGMgPSByLmdldCgiY291bnRzIiwge30pCiAgICBwcmlu
dCgiW+ioiF0gcmVzb2x2ZSVzIMK3IOe1hOWQiOmNtSAlZCDCtyDlkIjmiJDpjbUgJWQgwrcg6YGO5pmC6YCA5b25ICVkIMK3IOa8guenuyAlZCDCtyDmnKro
p6MgJWQgwrcg5aWX55SoICVzIMK3ICVzIiAlICgiIC0tYXBwbHkiIGlmIHJbImFwcGx5Il0gZWxzZSAiKGRyeS1ydW4pIiwgYy5nZXQoIkNPTVBPU0lURV9L
RVkiLCAwKSwgYy5nZXQoIlNZTlRIRVRJQ19LRVkiLCAwKSwgYy5nZXQoIk9CU09MRVRFIiwgMCksIGMuZ2V0KCJEUklGVCIsIDApLCBjLmdldCgiVU5SRVNP
TFZFRCIsIDApLCByLmdldCgiYXBwbGllZCIpLCByWyJsYW1wIl0pKQogICAgZm9yIHosIHJvd3MgaW4gci5nZXQoInpvbmVzIiwge30pLml0ZW1zKCk6CiAg
ICAgICAgZm9yIHggaW4gcm93c1s6MTJdOgogICAgICAgICAgICBwcmludCgiICBbJXNdICVzICVzfCVzIMK3ICVzIiAlICgiWUVMIiBpZiB6ID09ICJVTlJF
U09MVkVEIiBlbHNlICJPSyIsIHosIHhbInN1YiJdLCB4WyJ0aWQiXSwgeC5nZXQoImtleXMiKSBvciB4LmdldCgicmVwbGFjZWRfYnkiKSBvciB4LmdldCgi
d2h5Iikgb3IgeC5nZXQoImFjdGlvbiIpKSkKICAgIGZvciBuIGluIHIuZ2V0KCJfbm90ZXMiLCBbXSk6CiAgICAgICAgcHJpbnQoIiAgW+azqF0gJXMiICUg
bikKCgpfTUFJTl8wMTAxID0gbWFpbgoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9GUk9NX1ZDR0Mi
KSAhPSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJuIDIKICAgIGEg
PSBsaXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQogICAgaWYgYVs6MV0gPT0gWyJyZXNvbHZlIl06CiAgICAgICAgX3ByaW50
X3Jlc29sdmUocmVzb2x2ZShhcHBseT0oIi0tYXBwbHkiIGluIGEpKSkKICAgICAgICByZXR1cm4gMAogICAgcmV0dXJuIF9NQUlOXzAxMDEoYXJndikKCgoK
CmRlZiBfcmlkX29mKHJvdzogZGljdCwgb3JkaW5hbD1Ob25lKSAtPiBzdHI6CiAgICBpbXBvcnQgaGFzaGxpYiBhcyBfaGwKICAgIGggPSBfaGwuc2hhMjU2
KGpzb24uZHVtcHMocm93LCBlbnN1cmVfYXNjaWk9RmFsc2UsIHNvcnRfa2V5cz1UcnVlLCBkZWZhdWx0PXN0cikuZW5jb2RlKCkpLmhleGRpZ2VzdCgpWzo4
XQogICAgcmV0dXJuIGggaWYgb3JkaW5hbCBpcyBOb25lIGVsc2UgIiVzIyVkIiAlIChoLCBvcmRpbmFsKQoKCiMg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSAIHYwMTAzOmRvd25zdHJlYW0o5Yqf6IO95qih57WE5LiL5pS+Ouav
jeWJr+acrOmAgOW9uSzlrZDns7vntbHlu7opwrcgbGF3KEwxMTYpIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgApMMTE2ID0geyJpZCI6ICJMMTE2IiwgImJhdGNoIjogIuWBtOe3miAyMDI2LTEwLTA2IiwgImNhdCI6ICLmsrvn
kIYgLyDkuIrkuIvliIblt6UiLCAia2V5IjogIlVQU1RSRUFNX0RPV05TVFJFQU0iLAogICAgICAgICJ6aCI6ICgi44CQ5LiK5LiL5YiG5bel5b6L44CR4pGg
IOWKn+iDveaooee1hOS4i+aUvjrlip/og73mqKHntYTmrbjlip/og73lrZDns7vntbEoVlJOIC8gVkRGIOKApiks55Sx5a2Q57O757WxIFN5c3RlbU1hbmFn
ZXIg5bu656uL44CB55m76KiY44CB6Ieq5aCxO+avjeezu+e1sSBWQ0dDIOebo+aOp+OAgiIKICAgICAgICAgICAgICAgIuKRoSDoqLvlhoogLyBTU09UIC8g
6KGo6aCtIC8g5Yqf6IO955+p6Zmj562J5bel5YW35LiK5LiL5ZCE5LiA5aWXOuS4i+mdoumCo+Wll+eUqOS+huW7uueriyhyZWdpc3RlciAvIGFkb3B0IC8g
bnVtYmVyIHB1bGwpLOS4iumdoumCo+Wll+eUqOS+huebo+Wvn+ihneeqgeOAgemAmumBjuaqouafpeOAgee1puS6iOe3qOiZnyhnb3Zlcm4gLyByZXNvbHZl
IC8gYW5ub3RhdGUp44CCIgogICAgICAgICAgICAgICAi4pGiIOebuOS6kuS4jeWPr+acieWLleS9nDrmr43ns7vntbHkuI3lr6vlrZDns7vntbHnmoTlhoro
iIfmqpQ75a2Q57O757Wx5LiN5a+r5q+N57O757Wx55qE6Jmf5YaK6IiH6KOB5a6a5pu4O+avjeezu+e1seaMgeacieeahOWtkOezu+e1seaooee1hOWJr+ac
rOimlueCuuWkmumgrSzlrZDns7vntbHlsL7niYjlnKjljbPpgIDlvbnkuIvmlL7jgIIiCiAgICAgICAgICAgICAgICLikaMg6Leo5bGk5YuV5L2c5Y+q55Sx
5pON5L2c5ZOhICsgQUkg6KOB5a6a5b6M5Z+36KGMKOijgeWumuabuCBWSUFfS2V5UnVsaW5ncyDCtyDkuIvmlL7luLMgVkNHQ19Eb3duc3RyZWFtX0xlZGdl
ciks5byV5pOO5Y+q5o+Q5qGI6IiH5Z+36KGM5bey6KOB5LqL6aCF44CCIiksCiAgICAgICAgInN0YXR1cyI6ICJBQ1RJVkUiLCAib3JpZ2luIjogIuaTjeS9
nOWToeWOn+aWh+S4i+S7pCAyMDI2LTEwLTA2KOWKn+iDveaooee1hOS4i+aUvizlrZDns7vntbHnrqHnkIYs5q+N57O757Wx55uj5o6nO+S4iuS4i+WQhOS4
gOWll+W3peWFtyzkuIvlu7rkuIrnm6M755u45LqS5LiN5Y+v5pyJ5YuV5L2cO+WLleS9nOeUseaIkei3nyBBSSDpgLLooYwpIiwKICAgICAgICAiZW5mb3Jj
ZW1lbnQiOiAiQ0dDIFJlZ2lzdHJ5R292ZXJub3IgZG93bnN0cmVhbSAvIHJlc29sdmUgLyBnb3Zlcm4gwrcgPFNVQj5fU3lzdGVtTWFuYWdlciByZWdpc3Rl
ciAvIGFkb3B0IC8gcHVsbCDCtyBIZWFsdGhNYXRyaXgg5ZCEIG1hbmFnZXIg6Ieq5aCxIn0KCgpkZWYgbGF3X2FwcGVuZF9nZW5lcmljKGxhdzogZGljdCwg
UDogZGljdCB8IE5vbmUgPSBOb25lLCBhcHBseTogYm9vbCA9IFRydWUpIC0+IGRpY3Q6CiAgICAiIiLku7vkvZXms5Xmop0ganNvbih7aWQsIHpoLCDigKZ9
KemZhOmAsuaUv+etluWGiuWwvueJiOWHuuaWsOeJiDvlkIwgaWQg5bey5ZyoIOKGkiBTS0lQO+WPquWinuS4jea4m+OAgiIiIgogICAgUCA9IFAgb3IgX3Bh
dGhzKCkKICAgIGxpZCA9IGxhdy5nZXQoImlkIikKICAgIGhpdHMgPSBzb3J0ZWQoUFsicmVnaXN0cnkiXS5nbG9iKCJWSUFfUG9saWN5X0xhd3NfU1NPVF92
Ki5qc29uIiksIGtleT1sYW1iZGEgcTogaW50KHJlLnNlYXJjaChyIl92KFxkezR9KSIsIHEubmFtZSkuZ3JvdXAoMSkpKQogICAgaWYgbm90IGhpdHMgb3Ig
bm90IGxpZDoKICAgICAgICByZXR1cm4geyJzdGF0dXMiOiAiTk9fQk9PSyIgaWYgbm90IGhpdHMgZWxzZSAiTk9fSUQiLCAibGFtcCI6ICJSRUQifQogICAg
dGFpbCA9IGhpdHNbLTFdCiAgICBkID0ganNvbi5sb2FkcyhfdGhfcmVhZCh0YWlsKSkKICAgIGxhd3MgPSBkLmdldCgibGF3cyIsIFtdKQogICAgaWYgYW55
KGwuZ2V0KCJpZCIpID09IGxpZCBmb3IgbCBpbiBsYXdzKToKICAgICAgICByZXR1cm4geyJzdGF0dXMiOiAiU0tJUCIsICJ0YWlsIjogdGFpbC5uYW1lLCAi
bGFtcCI6ICJHUkVFTiIsICJpZCI6IGxpZH0KICAgIG52ID0gInYlMDRkIiAlIChpbnQocmUuc2VhcmNoKHIiX3YoXGR7NH0pIiwgdGFpbC5uYW1lKS5ncm91
cCgxKSkgKyAxKQogICAgbmV3ID0gUFsicmVnaXN0cnkiXSAvICgiVklBX1BvbGljeV9MYXdzX1NTT1RfJXMuanNvbiIgJSBudikKICAgIGlmIG5ldy5leGlz
dHMoKToKICAgICAgICByZXR1cm4geyJzdGF0dXMiOiAiQ09ORkxJQ1QiLCAibmV3IjogbmV3Lm5hbWUsICJsYW1wIjogIlJFRCJ9CiAgICBkWyJsYXdzIl0g
PSBsYXdzICsgW2xhd10KICAgIGRbInByaW9yIl0sIGRbInZlcnNpb24iXSwgZFsidHMiXSA9IHRhaWwubmFtZSwgbnYsIGRhdGV0aW1lLmRhdGV0aW1lLm5v
dyhkYXRldGltZS50aW1lem9uZS51dGMpLmlzb2Zvcm1hdCh0aW1lc3BlYz0ic2Vjb25kcyIpCiAgICBkWyJ3aHlfIiArIG52XSA9ICIlcyDlt7LnmbzluIMg
4oaSIOWHuuaWsOeJiDsrJXMoJXMpO+WFtumkmOS4gOWtl+S4jeWLleOAgiVzICVzIiAlICh0YWlsLm5hbWUsIGxpZCwgbGF3LmdldCgib3JpZ2luIiwgIiIp
Wzo2MF0sIE5BTUUsIFRBRykKICAgIGlmIGFwcGx5OgogICAgICAgIG5ldy53cml0ZV90ZXh0KGpzb24uZHVtcHMoZCwgZW5zdXJlX2FzY2lpPUZhbHNlLCBp
bmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICByZXR1cm4geyJzdGF0dXMiOiAiV1JJVFRFTiIgaWYgYXBwbHkgZWxzZSAiUExBTiIsICJ0YWlsIjog
dGFpbC5uYW1lLCAibmV3IjogbmV3Lm5hbWUsICJsYXdzIjogbGVuKGRbImxhd3MiXSksICJsYW1wIjogIkdSRUVOIiwgImlkIjogbGlkfQoKCmRlZiBsYXdf
YXBwZW5kXzExNihQOiBkaWN0IHwgTm9uZSA9IE5vbmUsIGFwcGx5OiBib29sID0gVHJ1ZSkgLT4gZGljdDoKICAgIHJldHVybiBsYXdfYXBwZW5kX2dlbmVy
aWMoTDExNiwgUCwgYXBwbHkpCgoKZGVmIF9sYXdfYXBwZW5kXzExNl9vbGQoUDogZGljdCB8IE5vbmUgPSBOb25lLCBhcHBseTogYm9vbCA9IFRydWUpIC0+
IGRpY3Q6CiAgICBQID0gUCBvciBfcGF0aHMoKQogICAgaGl0cyA9IHNvcnRlZChQWyJyZWdpc3RyeSJdLmdsb2IoIlZJQV9Qb2xpY3lfTGF3c19TU09UX3Yq
Lmpzb24iKSwga2V5PWxhbWJkYSBxOiBpbnQocmUuc2VhcmNoKHIiX3YoXGR7NH0pIiwgcS5uYW1lKS5ncm91cCgxKSkpCiAgICBpZiBub3QgaGl0czoKICAg
ICAgICByZXR1cm4geyJzdGF0dXMiOiAiTk9fQk9PSyIsICJsYW1wIjogIlJFRCJ9CiAgICB0YWlsID0gaGl0c1stMV0KICAgIGQgPSBqc29uLmxvYWRzKF90
aF9yZWFkKHRhaWwpKQogICAgbGF3cyA9IGQuZ2V0KCJsYXdzIiwgW10pCiAgICBpZiBhbnkobC5nZXQoImlkIikgPT0gIkwxMTYiIGZvciBsIGluIGxhd3Mp
OgogICAgICAgIHJldHVybiB7InN0YXR1cyI6ICJTS0lQIiwgInRhaWwiOiB0YWlsLm5hbWUsICJsYW1wIjogIkdSRUVOIn0KICAgIG52ID0gInYlMDRkIiAl
IChpbnQocmUuc2VhcmNoKHIiX3YoXGR7NH0pIiwgdGFpbC5uYW1lKS5ncm91cCgxKSkgKyAxKQogICAgbmV3ID0gUFsicmVnaXN0cnkiXSAvICgiVklBX1Bv
bGljeV9MYXdzX1NTT1RfJXMuanNvbiIgJSBudikKICAgIGlmIG5ldy5leGlzdHMoKToKICAgICAgICByZXR1cm4geyJzdGF0dXMiOiAiQ09ORkxJQ1QiLCAi
bmV3IjogbmV3Lm5hbWUsICJsYW1wIjogIlJFRCJ9CiAgICBkWyJsYXdzIl0gPSBsYXdzICsgW0wxMTZdCiAgICBkWyJwcmlvciJdLCBkWyJ2ZXJzaW9uIl0s
IGRbInRzIl0gPSB0YWlsLm5hbWUsIG52LCBkYXRldGltZS5kYXRldGltZS5ub3coZGF0ZXRpbWUudGltZXpvbmUudXRjKS5pc29mb3JtYXQodGltZXNwZWM9
InNlY29uZHMiKQogICAgZFsid2h5XyIgKyBudl0gPSAiJXMg5bey55m85biDIOKGkiDlh7rmlrDniYg7K0wxMTYg5LiK5LiL5YiG5bel5b6LKOaTjeS9nOWT
oeWOn+aWh+S4i+S7pCAyMDI2LTEwLTA2KTvlhbbppJjkuIDlrZfkuI3li5XjgIIlcyAlcyIgJSAodGFpbC5uYW1lLCBOQU1FLCBUQUcpCiAgICBpZiBhcHBs
eToKICAgICAgICBuZXcud3JpdGVfdGV4dChqc29uLmR1bXBzKGQsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQog
ICAgcmV0dXJuIHsic3RhdHVzIjogIldSSVRURU4iIGlmIGFwcGx5IGVsc2UgIlBMQU4iLCAidGFpbCI6IHRhaWwubmFtZSwgIm5ldyI6IG5ldy5uYW1lLCAi
bGF3cyI6IGxlbihkWyJsYXdzIl0pLCAibGFtcCI6ICJHUkVFTiJ9CgoKZGVmIGRvd25zdHJlYW0oUDogZGljdCB8IE5vbmUgPSBOb25lLCBhcHBseTogYm9v
bCA9IEZhbHNlLCBhZG9wdF9vcnBoYW5zOiBib29sID0gRmFsc2UpIC0+IGRpY3Q6CiAgICAiIiJGMTrmr43ns7vntbEoc3VwcG9ydGl2ZSBtb2R1bGVzKeaM
geacieeahCBWUk5fKi9WREZfKiDmqKHntYTlia/mnKwg4oaSIOWtkOezu+e1seacieWQjOaXj+WwvueJiCDihpIg5q+N5Ymv5pys6YCA5b25KOenuyBzdXBw
b3J0aXZlIG1vZHVsZXMvX3N1cGVyc2VkZWQsRnVuY3Rpb25NYXRyaXgg5qiZIFJFVElSRUQgcmVwbGFjZWRfYnks5bizKTvlrZDns7vntbHmspLmnInmiJbm
r43lia/mnKzovIPmlrAg4oaSIOW+heijgeOAgiIiIgogICAgUCA9IFAgb3IgX3BhdGhzKCkKICAgIG5vdyA9IF9ub3coKQogICAgb3V0ID0geyJ2ZXJiIjog
ImRvd25zdHJlYW0iLCAiYXBwbHkiOiBhcHBseSwgInJldGlyZSI6IFtdLCAicGVuZGluZyI6IFtdLCAiX25vdGVzIjogW119CiAgICB2Zm0gPSBfYm9vayhQ
LCAiVkNHQyIsICJGdW5jdGlvbk1hdHJpeCIpCiAgICBpdGVtcyA9ICh2Zm1bImRhdGEiXSBvciB7fSkuZ2V0KCJpdGVtcyIsIHt9KQogICAgc3VwID0gUFsi
c3VwIl0gaWYgInN1cCIgaW4gUCBlbHNlIFBbInJvb3QiXSAvICJzdXBwb3J0aXZlIG1vZHVsZXMiCiAgICBsZWQgPSBQWyJyZWdpc3RyeSJdIC8gIlZDR0Nf
RG93bnN0cmVhbV9MZWRnZXIuanNvbmwiCiAgICBmb3IgaywgZSBpbiBsaXN0KGl0ZW1zLml0ZW1zKCkpOgogICAgICAgIGlmIGUuZ2V0KCJraW5kIikgbm90
IGluICgiTURMIiwgIkVORyIpIG9yIGUuZ2V0KCJzdGF0dXMiKSAhPSAiQUNUSVZFIjoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBmYW0gPSBlLmdl
dCgibW9kdWxlIiwgIiIpCiAgICAgICAgc3JjID0gUFsicm9vdCJdIC8gZS5nZXQoInNvdXJjZSIsICIiKQogICAgICAgIG0gPSByZS5tYXRjaChyIl4oVlJO
fFZERilfIiwgZmFtKQogICAgICAgIHN1YiA9IG0uZ3JvdXAoMSkgaWYgbSBlbHNlIE5vbmUKICAgICAgICB0YWlscyA9IFtdCiAgICAgICAgZm9yIGNhbmRf
c3ViLCBob21lIGluICgoIlZSTiIsIFBbInZybiJdKSwgKCJWREYiLCBQWyJ2ZGYiXSkpOgogICAgICAgICAgICBpZiBzdWIgYW5kIGNhbmRfc3ViICE9IHN1
YjoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGZvdW5kID0gW3AgZm9yIHAgaW4gaG9tZS5yZ2xvYihmYW0gKyAiKi5weSIpIGlmIG5v
dCAoc2V0KHAucmVsYXRpdmVfdG8oaG9tZSkucGFydHNbOi0xXSkgJiB7Il9zdXBlcnNlZGVkIiwgInJlZmVyZW5jZXMiLCAiaW50YWtlIn0pIGFuZCBfdGhf
ZmFtaWx5KHAubmFtZSkgPT0gZmFtXSBpZiBob21lLmlzX2RpcigpIGVsc2UgW10KICAgICAgICAgICAgaWYgZm91bmQ6CiAgICAgICAgICAgICAgICBzdWIs
IHRhaWxzID0gY2FuZF9zdWIsIGZvdW5kCiAgICAgICAgICAgICAgICBicmVhawogICAgICAgIGlmIG5vdCBzdWI6CiAgICAgICAgICAgIGNvbnRpbnVlICAg
ICAgICAgICAgICAgICAgICAgICMg54Sh5YmN57a05LiU5a2Q57O757Wx5qi55LiK5Lmf5rKS5pyJ5ZCM5pePIOKGkiDntJTmr43ns7vntbHmqKHntYQs5LiN
5piv5LiL5pS+5bCN6LGhCiAgICAgICAgaG9tZSA9IFBbInZybiJdIGlmIHN1YiA9PSAiVlJOIiBlbHNlIFBbInZkZiJdCiAgICAgICAgaWYgbm90IHRhaWxz
OgogICAgICAgICAgICBpZiBhZG9wdF9vcnBoYW5zIGFuZCBzcmMuZXhpc3RzKCkgYW5kIHNyYy5pc19yZWxhdGl2ZV90byhzdXApOgogICAgICAgICAgICAg
ICAgZHN0ID0gaG9tZSAvIHNyYy5uYW1lCiAgICAgICAgICAgICAgICBpZiBkc3QuZXhpc3RzKCk6CiAgICAgICAgICAgICAgICAgICAgb3V0WyJwZW5kaW5n
Il0uYXBwZW5kKHsia2V5IjogaywgImZpbGUiOiBzcmMubmFtZSwgIndoeSI6ICLlrZDns7vntbHlkIzlkI3mqpTlt7LlnKjkvYbml4/lkI3kuI3lkIwg4oaS
IOW+heijgSJ9KQogICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICByZWMgPSB7ImtleSI6IGssICJmaWxlIjogc3JjLm5hbWUs
ICJyZXBsYWNlZF9ieSI6IGRzdC5yZWxhdGl2ZV90byhQWyJyb290Il0pLmFzX3Bvc2l4KCksICJ3aHkiOiAi5q+N542o5pys5LiL5pS+5bu65qqUKOaTjeS9
nOWToeijgeWumiAtLWFkb3B0LW9ycGhhbnMpOuaQrOWIsCAlcyzmr43mqJkgUkVUSVJFRCIgJSBzdWJ9CiAgICAgICAgICAgICAgICBpZiBhcHBseToKICAg
ICAgICAgICAgICAgICAgICBfX2ltcG9ydF9fKCJzaHV0aWwiKS5jb3B5MihzdHIoc3JjKSwgc3RyKGRzdCkpCiAgICAgICAgICAgICAgICAgICAgZHN0X2Rp
ciA9IHNyYy5wYXJlbnQgLyAiX3N1cGVyc2VkZWQiCiAgICAgICAgICAgICAgICAgICAgZHN0X2Rpci5ta2RpcihleGlzdF9vaz1UcnVlKQogICAgICAgICAg
ICAgICAgICAgIG1vdmVkID0gZHN0X2RpciAvIChzcmMubmFtZSArICIuRE9XTlNUUkVBTV8iICsgbm93LnJlcGxhY2UoIjoiLCAiIikucmVwbGFjZSgiLSIs
ICIiKVs6MTVdKQogICAgICAgICAgICAgICAgICAgIF9faW1wb3J0X18oInNodXRpbCIpLm1vdmUoc3RyKHNyYyksIHN0cihtb3ZlZCkpCiAgICAgICAgICAg
ICAgICAgICAgZS51cGRhdGUoc3RhdHVzPSJSRVRJUkVEIiwgcmV0aXJlZF9hdD1ub3csIHJlcGxhY2VkX2J5PXJlY1sicmVwbGFjZWRfYnkiXSwgcmV0aXJl
X3JlYXNvbj1yZWNbIndoeSJdKQogICAgICAgICAgICAgICAgICAgIHdpdGggb3BlbihsZWQsICJhIiwgZW5jb2Rpbmc9InV0Zi04IikgYXMgZmg6CiAgICAg
ICAgICAgICAgICAgICAgICAgIGZoLndyaXRlKGpzb24uZHVtcHMoZGljdChyZWMsIHRzPW5vdywgdG89bW92ZWQucmVsYXRpdmVfdG8oUFsicm9vdCJdKS5h
c19wb3NpeCgpLCBvcnBoYW49VHJ1ZSksIGVuc3VyZV9hc2NpaT1GYWxzZSkgKyAiXG4iKQogICAgICAgICAgICAgICAgICAgIHJlY1sidG8iXSA9IG1vdmVk
Lm5hbWUKICAgICAgICAgICAgICAgIG91dFsicmV0aXJlIl0uYXBwZW5kKHJlYykKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIG91dFsicGVu
ZGluZyJdLmFwcGVuZCh7ImtleSI6IGssICJmaWxlIjogc3JjLm5hbWUsICJ3aHkiOiAiJXMg5rKS5pyJ5ZCM5peP5qqUIOKGkiDmr43lia/mnKzmmK/llK/k
uIDmnKw65b6F6KOBKOaTjeS9nOWToeiqqiBPSyDlsLEgLS1hZG9wdC1vcnBoYW5zIOaQrOS4i+WOu+W7uuaqlCkiICUgc3VifSkKICAgICAgICAgICAgY29u
dGludWUKICAgICAgICB0YWlsID0gbWF4KHRhaWxzLCBrZXk9bGFtYmRhIHE6IF90aF92bnVtKHEubmFtZSkpCiAgICAgICAgbXYsIHN2ID0gX3RoX3ZudW0o
c3JjLm5hbWUpLCBfdGhfdm51bSh0YWlsLm5hbWUpCiAgICAgICAgc2FtZSA9IHNyYy5leGlzdHMoKSBhbmQgdGFpbC5leGlzdHMoKSBhbmQgX3NoYShzcmMp
ID09IF9zaGEodGFpbCkKICAgICAgICBpZiBzYW1lIG9yIHN2ID49IG12OgogICAgICAgICAgICByZWMgPSB7ImtleSI6IGssICJmaWxlIjogc3JjLm5hbWUs
ICJyZXBsYWNlZF9ieSI6IHRhaWwucmVsYXRpdmVfdG8oUFsicm9vdCJdKS5hc19wb3NpeCgpLCAid2h5IjogIuWtkOezu+e1seWwvueJiCAlcyAlcyDmr43l
ia/mnKwg4oaSIOavjeWJr+acrOmAgOW9ueS4i+aUviIgJSAodGFpbC5uYW1lLCAi5ZCM5YWn5a65IiBpZiBzYW1lIGVsc2UgIueJiOiZnyDiiaUiKX0KICAg
ICAgICAgICAgaWYgYXBwbHkgYW5kIHNyYy5leGlzdHMoKSBhbmQgc3JjLmlzX3JlbGF0aXZlX3RvKHN1cCk6CiAgICAgICAgICAgICAgICBkc3RfZGlyID0g
c3JjLnBhcmVudCAvICJfc3VwZXJzZWRlZCIKICAgICAgICAgICAgICAgIGRzdF9kaXIubWtkaXIoZXhpc3Rfb2s9VHJ1ZSkKICAgICAgICAgICAgICAgIGRz
dCA9IGRzdF9kaXIgLyAoc3JjLm5hbWUgKyAiLkRPV05TVFJFQU1fIiArIG5vdy5yZXBsYWNlKCI6IiwgIiIpLnJlcGxhY2UoIi0iLCAiIilbOjE1XSkKICAg
ICAgICAgICAgICAgIF9faW1wb3J0X18oInNodXRpbCIpLm1vdmUoc3RyKHNyYyksIHN0cihkc3QpKQogICAgICAgICAgICAgICAgZS51cGRhdGUoc3RhdHVz
PSJSRVRJUkVEIiwgcmV0aXJlZF9hdD1ub3csIHJlcGxhY2VkX2J5PXJlY1sicmVwbGFjZWRfYnkiXSwgcmV0aXJlX3JlYXNvbj1yZWNbIndoeSJdKQogICAg
ICAgICAgICAgICAgZm9yIGsyLCBlMiBpbiBpdGVtcy5pdGVtcygpOgogICAgICAgICAgICAgICAgICAgIGlmIGUyLmdldCgibW9kdWxlIikgPT0gZmFtIGFu
ZCBlMi5nZXQoInN0YXR1cyIpID09ICJBQ1RJVkUiIGFuZCBlMi5nZXQoImtpbmQiKSBpbiAoIkZOQyIsICJDTFMiLCAiTElCIik6CiAgICAgICAgICAgICAg
ICAgICAgICAgIGUyLnVwZGF0ZShzdGF0dXM9IlJFVElSRUQiLCByZXRpcmVkX2F0PW5vdywgcmVwbGFjZWRfYnk9cmVjWyJyZXBsYWNlZF9ieSJdLCByZXRp
cmVfcmVhc29uPSLpmqjmr43lia/mnKzkuIvmlL4iKQogICAgICAgICAgICAgICAgd2l0aCBvcGVuKGxlZCwgImEiLCBlbmNvZGluZz0idXRmLTgiKSBhcyBm
aDoKICAgICAgICAgICAgICAgICAgICBmaC53cml0ZShqc29uLmR1bXBzKGRpY3QocmVjLCB0cz1ub3csIHRvPWRzdC5yZWxhdGl2ZV90byhQWyJyb290Il0p
LmFzX3Bvc2l4KCkpLCBlbnN1cmVfYXNjaWk9RmFsc2UpICsgIlxuIikKICAgICAgICAgICAgICAgIHJlY1sidG8iXSA9IGRzdC5uYW1lCiAgICAgICAgICAg
IG91dFsicmV0aXJlIl0uYXBwZW5kKHJlYykKICAgICAgICBlbHNlOgogICAgICAgICAgICBvdXRbInBlbmRpbmciXS5hcHBlbmQoeyJrZXkiOiBrLCAiZmls
ZSI6IHNyYy5uYW1lLCAid2h5IjogIuavjeWJr+acrCB2JTA0ZCDmr5TlrZDns7vntbHlsL7niYggJXMg5pawIOKGkiDlvoXoo4Eo5beu55Ww6KaB5Lq655yL
KSIgJSAobXYsIHRhaWwubmFtZSl9KQogICAgaWYgYXBwbHkgYW5kIG91dFsicmV0aXJlIl0gYW5kIHZmbVsiZGF0YSJdOgogICAgICAgIHZmbVsicGF0aCJd
LndyaXRlX3RleHQoanNvbi5kdW1wcyh2Zm1bImRhdGEiXSwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICBv
dXRbImxhbXAiXSA9ICJZRUxMT1ciIGlmIG91dFsicGVuZGluZyJdIGVsc2UgKCJHUkVFTiIgaWYgYXBwbHkgZWxzZSAiWUVMTE9XIikKICAgIHJldHVybiBv
dXQKCgpkZWYgX3NoYShwOiBQYXRoKSAtPiBzdHI6CiAgICBpbXBvcnQgaGFzaGxpYiBhcyBfaGwKICAgIHJldHVybiBfaGwuc2hhMjU2KHAucmVhZF9ieXRl
cygpKS5oZXhkaWdlc3QoKQoKCmRlZiBfcHJpbnRfZG93bnN0cmVhbShyOiBkaWN0KSAtPiBOb25lOgogICAgcHJpbnQoIlvoqIhdIGRvd25zdHJlYW0lcyDC
tyDmr43lia/mnKzpgIDlvbnkuIvmlL4gJWQgwrcg5b6F6KOBICVkIMK3ICVzIiAlICgiIC0tYXBwbHkiIGlmIHJbImFwcGx5Il0gZWxzZSAiKGRyeS1ydW4p
IiwgbGVuKHJbInJldGlyZSJdKSwgbGVuKHJbInBlbmRpbmciXSksIHJbImxhbXAiXSkpCiAgICBmb3IgeCBpbiByWyJyZXRpcmUiXVs6MjBdOgogICAgICAg
IHByaW50KCIgIFtPS10g5LiL5pS+ICVzIOKGkiAlcyVzIiAlICh4WyJmaWxlIl0sIHhbInJlcGxhY2VkX2J5Il0sICgiIMK3IOenuyAiICsgeFsidG8iXSkg
aWYgeC5nZXQoInRvIikgZWxzZSAiIikpCiAgICBmb3IgeCBpbiByWyJwZW5kaW5nIl1bOjIwXToKICAgICAgICBwcmludCgiICBbWUVMXSDlvoXoo4EgJXMg
wrcgJXMiICUgKHhbImZpbGUiXSwgeFsid2h5Il0pKQoKCl9NQUlOXzAxMDIgPSBtYWluCgoKZGVmIG1haW4oYXJndj1Ob25lKSAtPiBpbnQ6CiAgICBpZiBv
cy5lbnZpcm9uLmdldCgiVklBX0ZST01fVkNHQyIpICE9ICJZRVMiOgogICAgICAgIHByaW50KCJbVkNHQ10g5ouS57WV44CC5Y+q6IO957aTIHZpYS12Y2dj
44CCIikKICAgICAgICByZXR1cm4gMgogICAgYSA9IGxpc3Qoc3lzLmFyZ3ZbMTpdIGlmIGFyZ3YgaXMgTm9uZSBlbHNlIGFyZ3YpCiAgICBpZiBhWzoxXSA9
PSBbImRvd25zdHJlYW0iXToKICAgICAgICBfcHJpbnRfZG93bnN0cmVhbShkb3duc3RyZWFtKGFwcGx5PSgiLS1hcHBseSIgaW4gYSksIGFkb3B0X29ycGhh
bnM9KCItLWFkb3B0LW9ycGhhbnMiIGluIGEpKSkKICAgICAgICByZXR1cm4gMAogICAgaWYgYVs6MV0gPT0gWyJsYXciXToKICAgICAgICBpZiAiLS1maWxl
IiBpbiBhOgogICAgICAgICAgICBmcCA9IFBhdGgoYVthLmluZGV4KCItLWZpbGUiKSArIDFdKQogICAgICAgICAgICByID0gbGF3X2FwcGVuZF9nZW5lcmlj
KGpzb24ubG9hZHMoZnAucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciKSksIGFwcGx5PSgiLS1kcnkiIG5vdCBpbiBhKSkKICAgICAgICBlbHNlOgog
ICAgICAgICAgICByID0gbGF3X2FwcGVuZF9nZW5lcmljKEwxMTYsIGFwcGx5PSgiLS1kcnkiIG5vdCBpbiBhKSkKICAgICAgICBwcmludCgiW+ioiF0gbGF3
IGFwcGVuZCAlcyDCtyAlcyDCtyAlcyDihpIgJXMgwrcgJXMiICUgKHIuZ2V0KCJpZCIsICJMMTE2IiksIHJbInN0YXR1cyJdLCByLmdldCgidGFpbCIpLCBy
LmdldCgibmV3IiwgIuKAlCIpLCByWyJsYW1wIl0pKQogICAgICAgIHJldHVybiAxIGlmIHJbImxhbXAiXSA9PSAiUkVEIiBlbHNlIDAKICAgIHJldHVybiBf
TUFJTl8wMTAyKGFyZ3YpCgoKZGVmIF93KHA6IFBhdGgsIG9iaikgLT4gTm9uZToKICAgIHAucGFyZW50Lm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhpc3Rfb2s9
VHJ1ZSkKICAgIHAud3JpdGVfdGV4dChvYmogaWYgaXNpbnN0YW5jZShvYmosIHN0cikgZWxzZSBqc29uLmR1bXBzKG9iaiwgZW5zdXJlX2FzY2lpPUZhbHNl
LCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCgoKZGVmIHNlbGZ0ZXN0KCkgLT4gaW50OgogICAgcCA9IGYgPSAwCgogICAgZGVmIGNoayhuYW1lLCBj
b25kKToKICAgICAgICBub25sb2NhbCBwLCBmCiAgICAgICAgaWYgY29uZDoKICAgICAgICAgICAgcCArPSAxCiAgICAgICAgICAgIHByaW50KCIgIFtPS10g
JXMiICUgbmFtZSkKICAgICAgICBlbHNlOgogICAgICAgICAgICBmICs9IDEKICAgICAgICAgICAgcHJpbnQoIiAgW0ZBSUxdICVzIiAlIG5hbWUpCgogICAg
dGQgPSBQYXRoKHRlbXBmaWxlLm1rZHRlbXAocHJlZml4PSJjZ2Nnb3YtIikpCiAgICBvcy5lbnZpcm9uWyJWSUFfUk9PVCJdID0gc3RyKHRkKQogICAgUCA9
IF9wYXRocygpCiAgICBub3cgPSBfbm93KCkKICAgIGNoaygi4pGgIOaymeebkjpWSUFfUk9PVCDmjIcgdGVtcCIsIGFsbChzdHIodikuc3RhcnRzd2l0aChz
dHIodGQpKSBmb3IgdiBpbiBQLnZhbHVlcygpKSkKICAgICMgVkNHQyDoh6rlt7HnmoTlhoogKyDnqIvlvI8KICAgIF93KFBbInJlZ2lzdHJ5Il0gLyAiVklB
X1NTT1RfTnVtYmVyc19WUk5fdjAxMDAuanNvbiIsIHsiZW50cmllcyI6IFt7ImtleSI6ICJrMSIsICJzc290X25vIjogIkEifSwgeyJrZXkiOiAiazIiLCAi
c3NvdF9ubyI6ICJCIn1dfSkKICAgIF93KFBbInJlZ2lzdHJ5Il0gLyAiQ0dDX01ETDAwMV9YX3YwMTAwLnB5IiwgImRlZiBzaGFyZWQoYSk6XG4gICAgcmV0
dXJuIGFcbiIpCiAgICByMSA9IHJlZ2lzdGVyKFAsIGFwcGx5PVRydWUpCiAgICBjaGsoIuKRoSBWQ0dDIHJlZ2lzdGVyOuihqOmgrSAxIOihqCDCtyDnn6np
maMgTURMIDEgRk5DIDEgwrcg55WZ55m9IiwgcjFbInRhYmxlIl1bInRhYmxlcyJdID09IDEgYW5kIHIxWyJmbiJdWyJraW5kcyJdLmdldCgiTURMIikgPT0g
MSBhbmQgcjFbImZuIl1bImtpbmRzIl0uZ2V0KCJGTkMiKSA9PSAxIGFuZCByMVsiZm4iXVsiYmxhbmsiXSA9PSAyKQogICAgIyBWUk4gLyBWREYg55qE5YaK
KOaooeaTrOWtkOezu+e1seW3sueZu+iomCkKICAgIF93KFBbInZybiJdIC8gIlNTT1QiIC8gIlZSTl9SYXRpbmdfRGljdF92MDEwMC5qc29uIiwgeyJCVVki
OiB7InpoIjogIuiyt+mAsiIsICJzY29yZSI6IDF9LCAiSE9MRCI6IHsiemgiOiAi5oyB5pyJIiwgInNjb3JlIjogMH19KQogICAgX3coUFsidnJuIl0gLyAi
U1NPVCIgLyAiVlJOX05vS2V5X3YwMTAwLmpzb24iLCB7InJvd3MiOiBbeyJhIjogMSwgImIiOiAxfSwgeyJhIjogMSwgImIiOiAxfV19KQogICAgX3coUFsi
dnJuIl0gLyAiVlJOX0VORzAwMV9BX3YwMTAwLnB5IiwgImRlZiBzaGFyZWQoYSk6XG4gICAgcmV0dXJuIGFcblxuZGVmIHZybl9vbmx5KCk6XG4gICAgcGFz
c1xuIikKICAgIF93KFBbInZkZiJdIC8gInJlZ2lzdHJ5IiAvICJWREZfVW5pdmVyc2VfdjAxMDAuanNvbiIsIHsicm93cyI6IFt7InRpY2tlciI6ICIyMzMw
IiwgIm5hbWUiOiAiVFNNQyJ9XX0pCiAgICBfdyhQWyJ2ZGYiXSAvICJWREZfRU5HMDAxX0FfdjAxMDAucHkiLCAiZGVmIHNoYXJlZChhKTpcbiAgICByZXR1
cm4gYVxuIikKICAgIF93KFBbInZkZiJdIC8gIlNIQVJFRF9NT0RfdjAxMDAucHkiLCAieCA9IDFcbiIpCiAgICBfdyhQWyJ2cm4iXSAvICJTSEFSRURfTU9E
X3YwMTAwLnB5IiwgInggPSAyXG4iKSAgICMg5ZCM5qih57WE5pePIFNIQVJFRF9NT0Qg5ZCM5pmC5ZyoIFZERiDoiIcgVlJOIOKGkiBGMSDntIUo5YWp6YKK
6YO95pOLKQogICAgX3RoX3JlZ2lzdGVyKCJWUk4iLCBbUFsidnJuIl0gLyAiU1NPVCIgLyAiVlJOX1JhdGluZ19EaWN0X3YwMTAwLmpzb24iLCBQWyJ2cm4i
XSAvICJTU09UIiAvICJWUk5fTm9LZXlfdjAxMDAuanNvbiJdLCBQWyJ2cm4iXSAvICJyZWdpc3RyeSIsIG5vdywgVHJ1ZSwgUFsicm9vdCJdKQogICAgX3Ro
X3JlZ2lzdGVyKCJWREYiLCBbUFsidmRmIl0gLyAicmVnaXN0cnkiIC8gIlZERl9Vbml2ZXJzZV92MDEwMC5qc29uIl0sIFBbInZkZiJdIC8gInJlZ2lzdHJ5
Iiwgbm93LCBUcnVlLCBQWyJyb290Il0pCiAgICBfZm1fcmVnaXN0ZXIoIlZSTiIsIFtQWyJ2cm4iXV0sIFBbInJvb3QiXSwgUFsidnJuIl0gLyAicmVnaXN0
cnkiLCBub3csIFRydWUpCiAgICBfZm1fcmVnaXN0ZXIoIlZERiIsIFtQWyJ2ZGYiXV0sIFBbInJvb3QiXSwgUFsidmRmIl0gLyAicmVnaXN0cnkiLCBub3cs
IFRydWUpCiAgICBkcnkgPSBnb3Zlcm4oUCwgYXBwbHk9RmFsc2UpCiAgICBjaGsoIuKRoiBnb3Zlcm4gZHJ5LXJ1bjrkuI3lr6vomZ/lhoogwrcg6KGoIDQo
Tm9LZXkg57SFIFQyKcK3IOWKn+aciee0hShGMSDlkIzmqKHntYTml4/ot6jns7vntbEp5pyJ6buDKEYzIHNoYXJlZCDlkIzlkI3lkIwgYm9keSDot6jkuInn
s7vntbEpIiwKICAgICAgICBub3QgKFBbInJlZ2lzdHJ5Il0gLyAiVklBX1RhYmxlTnVtYmVyc192MDEwMC5qc29uIikuZXhpc3RzKCkgYW5kIGRyeVsic3Vt
bWFyeSJdWyJ0YWJsZXMiXSA9PSA0IGFuZCBkcnlbInN1bW1hcnkiXVsidF9yZWQiXSA9PSAxCiAgICAgICAgYW5kIGFueShmWyJydWxlIl0gPT0gIkYxIiBm
b3IgciBpbiBkcnlbImZucyJdLnZhbHVlcygpIGZvciBmIGluIHJbImZsYWdzIl0pIGFuZCBhbnkoZlsicnVsZSJdID09ICJGMyIgYW5kICLot6jns7vntbEi
IGluIGZbImRldGFpbCJdIGZvciByIGluIGRyeVsiZm5zIl0udmFsdWVzKCkgZm9yIGYgaW4gclsiZmxhZ3MiXSkpCiAgICBhcCA9IGdvdmVybihQLCBhcHBs
eT1UcnVlKQogICAgdG4gPSBqc29uLmxvYWRzKChQWyJyZWdpc3RyeSJdIC8gIlZJQV9UYWJsZU51bWJlcnNfdjAxMDAuanNvbiIpLnJlYWRfdGV4dChlbmNv
ZGluZz0idXRmLTgiKSkKICAgIGZuID0ganNvbi5sb2FkcygoUFsicmVnaXN0cnkiXSAvICJWSUFfUmVnaXN0cnlOdW1iZXJzX3YwMTAwLmpzb24iKS5yZWFk
X3RleHQoZW5jb2Rpbmc9InV0Zi04IikpCiAgICBub3MgPSBzb3J0ZWQoZVsidGFibGVfbm8iXSBmb3IgZSBpbiB0blsiZW50cmllcyJdKQogICAgY2hrKCLi
kaMgLS1hcHBseTrpm7bntIXooaggMyDlvLXnmbwgVEJMMDAwMSjlkITlrZDns7vntbHlkIToh6rluo8pwrcgTm9LZXkg5pOL6Jmf55WZ55m9IMK3IOebuOS8
vOm7g+S4jeaTiyIsIG5vcyA9PSBbIlNTT1QtVkNHQy1WQ0dDLVRCTDAwMDEiLCAiU1NPVC1WQ0dDLVZERi1UQkwwMDAxIiwgIlNTT1QtVkNHQy1WUk4tVEJM
MDAwMSJdCiAgICAgICAgYW5kIGFueSgiVlJOX05vS2V5Ii5sb3dlcigpIGluIGsgZm9yIGsgaW4gdG5bImJsb2NrZWQiXSkgYW5kIGFsbChyWyJsYW1wIl0g
IT0gIlJFRCIgb3IgIm5va2V5IiBpbiBrIGZvciBrLCByIGluIGFwWyJ0YWJsZXMiXS5pdGVtcygpKSkKICAgIGNvZGVzID0ge2VbImtleSJdOiBlWyJjb2Rl
Il0gZm9yIGUgaW4gZm5bImVudHJpZXMiXX0KICAgIGNoaygi4pGkIOWKn+iDveiZnzrniLbmqpQgVklBLTxTVUI+LU1ETC9FTkcwMDEgwrcg5a2Q6Y21IC1G
TkMwMDEg5o6b54i26JmfIMK3IEYxIOe0heeahCBTSEFSRURfTU9EIOWFqemCiuaTi+iZnyDCtyBzaGFyZWQg6buD54Wn55m8IiwKICAgICAgICBjb2Rlcy5n
ZXQoIlZDR0N8TURMfENHQ19NREwwMDFfWHx2MDEwMCIpID09ICJWSUEtVkNHQy1NREwwMDEiIGFuZCBjb2Rlcy5nZXQoIlZDR0N8Rk5DfENHQ19NREwwMDFf
WHxzaGFyZWR8djAxMDAiKSA9PSAiVklBLVZDR0MtTURMMDAxLUZOQzAwMSIKICAgICAgICBhbmQgY29kZXMuZ2V0KCJWREZ8RU5HfFZERl9FTkcwMDFfQXx2
MDEwMCIpID09ICJWSUEtVkRGLUVORzAwMSIgYW5kICJWREZ8TURMfFNIQVJFRF9NT0R8djAxMDAiIG5vdCBpbiBjb2RlcyBhbmQgIlZSTnxNREx8U0hBUkVE
X01PRHx2MDEwMCIgbm90IGluIGNvZGVzIGFuZCBjb2Rlcy5nZXQoIlZSTnxGTkN8VlJOX0VORzAwMV9BfHNoYXJlZHx2MDEwMCIpKQogICAgYXAyID0gZ292
ZXJuKFAsIGFwcGx5PVRydWUpCiAgICB0bjIgPSBqc29uLmxvYWRzKChQWyJyZWdpc3RyeSJdIC8gIlZJQV9UYWJsZU51bWJlcnNfdjAxMDAuanNvbiIpLnJl
YWRfdGV4dChlbmNvZGluZz0idXRmLTgiKSkKICAgIGNoaygi4pGlIOWGquetiTrlho3nmbwgMCDCtyDomZ/kuIDlrZfkuI3orooiLCBhcDJbInN1bW1hcnki
XVsidF9pc3N1ZWQiXSA9PSAwIGFuZCBhcDJbInN1bW1hcnkiXVsiZl9pc3N1ZWQiXSA9PSAwIGFuZCBzb3J0ZWQoZVsidGFibGVfbm8iXSBmb3IgZSBpbiB0
bjJbImVudHJpZXMiXSkgPT0gbm9zKQogICAgcHVsbGVkID0gX3RoX3B1bGwoIlZSTiIsIFBbInZybiJdIC8gInJlZ2lzdHJ5IiwgUFsicmVnaXN0cnkiXSwg
bm93LCBUcnVlKQogICAgZnB1bGwgPSBfZm1fcHVsbCgiVlJOIiwgUFsidnJuIl0gLyAicmVnaXN0cnkiLCBQWyJyZWdpc3RyeSJdLCBub3csIFRydWUpCiAg
ICB2YiA9IGpzb24ubG9hZHMoX3RoX3JlYWQoUFsidnJuIl0gLyAicmVnaXN0cnkiIC8gIlZSTl9UYWJsZUhlYWRlcl92MDEwMC5qc29uIikpCiAgICBjaGso
IuKRpiDlrZDns7vntbHoroDlm546VlJOIOihqOiugOWIsCBUQkwwMDAxIMK3IOWKn+iDveiugOWIsOiZnyDCtyDlhorkuIrlh7rnj77omZ8o6YG15a6IKSIs
IHB1bGxlZFsiZmlsbGVkIl0gPT0gMSBhbmQgdmJbInRhYmxlcyJdWyJ2cm5fcmF0aW5nX2RpY3QiXVsidGFibGVfbm8iXSA9PSAiU1NPVC1WQ0dDLVZSTi1U
QkwwMDAxIiBhbmQgZnB1bGxbImZpbGxlZCJdID49IDIpCiAgICBfdyhQWyJ2cm4iXSAvICJTU09UIiAvICJWUk5fUmF0aW5nX0RpY3RfdjAxMDEuanNvbiIs
IHsiQlVZIjogeyJ6aCI6ICLosrfpgLIiLCAic2NvcmUiOiAxLCAidyI6IDAuNX0sICJIT0xEIjogeyJ6aCI6ICLmjIHmnIkiLCAic2NvcmUiOiAwLCAidyI6
IDAuMH19KQogICAgX3RoX3JlZ2lzdGVyKCJWUk4iLCBbUFsidnJuIl0gLyAiU1NPVCIgLyAiVlJOX1JhdGluZ19EaWN0X3YwMTAxLmpzb24iLCBQWyJ2cm4i
XSAvICJTU09UIiAvICJWUk5fTm9LZXlfdjAxMDAuanNvbiJdLCBQWyJ2cm4iXSAvICJyZWdpc3RyeSIsIG5vdywgVHJ1ZSwgUFsicm9vdCJdKQogICAgYXAz
ID0gZ292ZXJuKFAsIGFwcGx5PVRydWUpCiAgICBjaGsoIuKRpyDlt7LomZ/ooajmlLnpoK0g4oaSIFQzIOe0hSjoiIrpjbUpwrcg5paw6aCtIF9oMiDmuKzp
gY7lj6bnmbzmlrDomZ8iLCBhbnkoZlsicnVsZSJdID09ICJUMyIgZm9yIHIgaW4gYXAzWyJ0YWJsZXMiXS52YWx1ZXMoKSBmb3IgZiBpbiByWyJmbGFncyJd
KSBhbmQgYW55KGVbInRpZCJdID09ICJ2cm5fcmF0aW5nX2RpY3RfaDIiIGZvciBlIGluIGFwM1siaXNzdWVkX3RhYmxlcyJdKSkKICAgIF93KFBbInJlZ2lz
dHJ5Il0gLyAiVklBX051bWJlckJvb2tzIiAvICJWSUFfTnVtYmVyQm9va19FTkdfdjAxMDAuanNvbmwiLCBqc29uLmR1bXBzKHsic291cmNlIjogImZ1bmN0
aW9uYWwgbW9kdWxlcy9WREYvVkRGX0VORzAwMV9BX3YwMTAxLnB5IiwgImNvZGUiOiAiVklBLVZERi1FTkcwMDkifSkgKyAiXG4iKQogICAgX3coUFsicmVn
aXN0cnkiXSAvICJWSUFfTnVtYmVyQm9va3MiIC8gIlZJQV9OdW1iZXJCb29rX0ZOQ19WREZfdjAxMDAuanNvbmwiLCBqc29uLmR1bXBzKHsiY29kZSI6ICJW
SUEtVkRGLUVORzAwOS1GTkMwMDQiLCAicSI6ICJzaGFyZWQifSkgKyAiXG4iKQogICAgX3coUFsidmRmIl0gLyAiVkRGX0VORzAwMV9BX3YwMTAxLnB5Iiwg
ImRlZiBzaGFyZWQoYSk6XG4gICAgcmV0dXJuIGEgKyAxXG4iKQogICAgX2ZtX3JlZ2lzdGVyKCJWREYiLCBbUFsidmRmIl1dLCBQWyJyb290Il0sIFBbInZk
ZiJdIC8gInJlZ2lzdHJ5Iiwgbm93LCBUcnVlKQogICAgYXA0ID0gZ292ZXJuKFAsIGFwcGx5PVRydWUpCiAgICBjb2RlczQgPSB7ZVsia2V5Il06IGVbImNv
ZGUiXSBmb3IgZSBpbiBqc29uLmxvYWRzKChQWyJyZWdpc3RyeSJdIC8gIlZJQV9SZWdpc3RyeU51bWJlcnNfdjAxMDAuanNvbiIpLnJlYWRfdGV4dChlbmNv
ZGluZz0idXRmLTgiKSlbImVudHJpZXMiXX0KICAgIGNoaygi4pGoIOaXouaciSBOdW1iZXJCb29rcyDmsr/nlKjkuI3ph43nmbwo6Y21ID0gc291cmNlQHZl
cnNpb24s54mI5pys5LiA5o+b5paw6JmfKTpWREZfRU5HMDAxX0EgdjAxMDEg5Y+WIFZJQS1WREYtRU5HMDA5IMK3IHNoYXJlZCDlj5YgLUZOQzAwNCIsIGNv
ZGVzNC5nZXQoIlZERnxFTkd8VkRGX0VORzAwMV9BfHYwMTAxIikgPT0gIlZJQS1WREYtRU5HMDA5IiBhbmQgY29kZXM0LmdldCgiVkRGfEZOQ3xWREZfRU5H
MDAxX0F8c2hhcmVkfHYwMTAxIikgPT0gIlZJQS1WREYtRU5HMDA5LUZOQzAwNCIpCiAgICBfdyhQWyJyZWdpc3RyeSJdIC8gIlZJQV9BY3RpdmF0aW9uR2F0
ZXdheV92MDJfSG90Zml4X01hbmlmZXN0Lmpzb24iLCB7InJvd3MiOiBbeyJuIjogMSwgIngiOiAiYSJ9XX0pCiAgICBfdyhQWyJyZWdpc3RyeSJdIC8gIlZJ
QV9BY3RpdmF0aW9uR2F0ZXdheV92MDNfSG90Zml4X01hbmlmZXN0Lmpzb24iLCB7InJvd3MiOiBbeyJuIjogMSwgIngiOiAiYiJ9XX0pCiAgICByZWdpc3Rl
cihQLCBhcHBseT1UcnVlKQogICAgYXA1ID0gZ292ZXJuKFAsIGFwcGx5PVRydWUpCiAgICB3cml0ZV9jYXJkKGFwNSwgcGFzdGVfcGFjayhhcDUpLCBQKQog
ICAgcnMgPSByZXNvbHZlKFAsIGFwcGx5PVRydWUpCiAgICBydWwgPSBqc29uLmxvYWRzKF90aF9yZWFkKFBbInJlZ2lzdHJ5Il0gLyBfUlVMSU5HUykpCiAg
ICB2YjIgPSBqc29uLmxvYWRzKF90aF9yZWFkKFBbInJlZ2lzdHJ5Il0gLyAiVkNHQ19UYWJsZUhlYWRlcl92MDEwMC5qc29uIikpCiAgICBjaGsoIuKRrSB2
MDEwMiByZXNvbHZlOlZSTiBOb0tleSDihpIg5ZCI5oiQ6Y216KOB5a6aKOWPquWHuuijgeWumuabuCzkuI3li5UgVlJOIOWGiinCtyDpgY7mmYIgdjAyIOmA
gOW9ueenuyBfc3VwZXJzZWRlZCDnlZkgdjAzIMK3IOijgeWumuabuCArIOmAgOW9ueW4syIsIHJ1bFsidGFibGVzIl0uZ2V0KCJ2cm5fbm9rZXkiLCB7fSku
Z2V0KCJraW5kIikgPT0gInN5bnRoZXRpYyIKICAgICAgICBhbmQgKFBbInZybiJdIC8gInJlZ2lzdHJ5IiAvICJWUk5fVGFibGVIZWFkZXJfdjAxMDAuanNv
biIpLmV4aXN0cygpIGFuZCBqc29uLmxvYWRzKF90aF9yZWFkKFBbInZybiJdIC8gInJlZ2lzdHJ5IiAvICJWUk5fVGFibGVIZWFkZXJfdjAxMDAuanNvbiIp
KVsidGFibGVzIl1bInZybl9ub2tleSJdLmdldCgia2V5cyIpID09IFtdCiAgICAgICAgYW5kIGFueSgidjAyIiBpbiBrIGZvciBrIGluIHJ1bFsicmV0aXJl
Il0pIGFuZCBsaXN0KChQWyJyZWdpc3RyeSJdIC8gIl9zdXBlcnNlZGVkIikuZ2xvYigiVklBX0FjdGl2YXRpb25HYXRld2F5X3YwMioiKSkgYW5kIChQWyJy
ZWdpc3RyeSJdIC8gIlZJQV9BY3RpdmF0aW9uR2F0ZXdheV92MDNfSG90Zml4X01hbmlmZXN0Lmpzb24iKS5leGlzdHMoKQogICAgICAgIGFuZCBhbnkodi5n
ZXQoInN0YXR1cyIpID09ICJSRVRJUkVEIiBmb3IgdiBpbiB2YjJbInRhYmxlcyJdLnZhbHVlcygpKSkKICAgIF93KFBbInN1cCJdIC8gInVpX3N1cHBvcnQi
IC8gIlZSTl9FTkcwMDFfQV92MDEwMC5weSIsICJ4ID0gMVxuIikKICAgIF93KFBbInN1cCJdIC8gIlZERl9NREw5OTlfTG9uZWx5X3YwMTAwLnB5IiwgInkg
PSAyXG4iKQogICAgcmVnaXN0ZXIoUCwgYXBwbHk9VHJ1ZSkKICAgIGRzMCA9IGRvd25zdHJlYW0oUCwgYXBwbHk9RmFsc2UpCiAgICBtb3ZlZF9iZWZvcmUg
PSBsaXN0KChQWyJzdXAiXSAvICJ1aV9zdXBwb3J0IiAvICJfc3VwZXJzZWRlZCIpLmdsb2IoIioiKSkgaWYgKFBbInN1cCJdIC8gInVpX3N1cHBvcnQiIC8g
Il9zdXBlcnNlZGVkIikuZXhpc3RzKCkgZWxzZSBbXQogICAgZHMxID0gZG93bnN0cmVhbShQLCBhcHBseT1UcnVlKQogICAgdmZtMiA9IGpzb24ubG9hZHMo
X3RoX3JlYWQoUFsicmVnaXN0cnkiXSAvICJWQ0dDX0Z1bmN0aW9uTWF0cml4X3YwMTAwLmpzb24iKSkKICAgIG1vdmVkX2FmdGVyID0gbGlzdCgoUFsic3Vw
Il0gLyAidWlfc3VwcG9ydCIgLyAiX3N1cGVyc2VkZWQiKS5nbG9iKCJWUk5fRU5HMDAxX0FfdjAxMDAucHkuRE9XTlNUUkVBTV8qIikpCiAgICBjaGsoIuKR
riB2MDEwMyBkb3duc3RyZWFtOmRyeS1ydW4g5LiN5YuVIMK3IFZSTiDlia/mnKzpgIDlvbnkuIvmlL4o56e7IF9zdXBlcnNlZGVkIMK3IOefqemZoyBSRVRJ
UkVEIHJlcGxhY2VkX2J5IMK3IOW4synCtyBWREYg5a2k5pys5b6F6KOBIiwKICAgICAgICBsZW4oZHMwWyJyZXRpcmUiXSkgPT0gMSBhbmQgbm90IG1vdmVk
X2JlZm9yZSBhbmQgbGVuKGRzMVsicmV0aXJlIl0pID09IDEgYW5kIG1vdmVkX2FmdGVyIGFuZCAoUFsicmVnaXN0cnkiXSAvICJWQ0dDX0Rvd25zdHJlYW1f
TGVkZ2VyLmpzb25sIikuZXhpc3RzKCkKICAgICAgICBhbmQgYW55KHYuZ2V0KCJzdGF0dXMiKSA9PSAiUkVUSVJFRCIgYW5kIHYuZ2V0KCJtb2R1bGUiKSA9
PSAiVlJOX0VORzAwMV9BIiBmb3IgdiBpbiB2Zm0yWyJpdGVtcyJdLnZhbHVlcygpKSBhbmQgbGVuKGRzMVsicGVuZGluZyJdKSA9PSAxKQogICAgZHMyID0g
ZG93bnN0cmVhbShQLCBhcHBseT1UcnVlLCBhZG9wdF9vcnBoYW5zPVRydWUpCiAgICBjaGsoIuKRsCB2MDEwNCAtLWFkb3B0LW9ycGhhbnM6VkRGIOWtpOac
rOaQrOWIsCBWREYg5aS+5bu65qqUIMK3IOavjeaomSBSRVRJUkVEIMK3IOW4syBvcnBoYW4iLCBsZW4oZHMyWyJyZXRpcmUiXSkgPT0gMSBhbmQgKFBbInZk
ZiJdIC8gIlZERl9NREw5OTlfTG9uZWx5X3YwMTAwLnB5IikuZXhpc3RzKCkgYW5kIG5vdCAoUFsic3VwIl0gLyAiVkRGX01ETDk5OV9Mb25lbHlfdjAxMDAu
cHkiKS5leGlzdHMoKSBhbmQgbm90IGRzMlsicGVuZGluZyJdKQogICAgX3coUFsic3VwIl0gLyAiYXVkaXRfdG9vbHMiIC8gInBhbm9yYW1hX3hjaGVja192
MTEwLnB5IiwgImEgPSAxXG4iKQogICAgX3coUFsidnJuIl0gLyAicGFub3JhbWFfeGNoZWNrX3YxMTIucHkiLCAiYSA9IDJcbiIpCiAgICByZWdpc3RlcihQ
LCBhcHBseT1UcnVlKQogICAgZHMzID0gZG93bnN0cmVhbShQLCBhcHBseT1UcnVlKQogICAgY2hrKCLikbEgdjAxMDQg54Sh5YmN57a05pePKHBhbm9yYW1h
X3hjaGVjaynlrZDns7vntbEgdjExMiDiiaUg5q+NIHYxMTAg4oaSIOS4i+aUviIsIGFueSh4WyJmaWxlIl0gPT0gInBhbm9yYW1hX3hjaGVja192MTEwLnB5
IiBmb3IgeCBpbiBkczNbInJldGlyZSJdKSkKICAgIG9rciwgd2h5ciA9IF90ZXN0X3RhYmxlKFAsIHsic291cmNlIjogIngiLCAidGFibGUiOiAidCIsICJr
ZXlzIjogWyJfcmlkIl0sICJjb2x1bW5zIjogW119KSBpZiBGYWxzZSBlbHNlIChUcnVlLCAiIikKICAgIHJvd3NfZHVwID0gW3siYSI6IDF9LCB7ImEiOiAx
fSwgeyJhIjogMX1dCiAgICBzZWVuID0ge30KICAgIGlkcyA9IFtdCiAgICBmb3IgciBpbiByb3dzX2R1cDoKICAgICAgICBoID0gX3JpZF9vZihyKTsgbiA9
IHNlZW4uZ2V0KGgsIDApOyBzZWVuW2hdID0gbiArIDE7IGlkcy5hcHBlbmQoaCBpZiBuID09IDAgZWxzZSAiJXMjJWQiICUgKGgsIG4pKQogICAgY2hrKCLi
kbIgX3JpZCDkuInnrYbmlbTliJfph43opIcg4oaSIOS4ieWAi+S4jeWQjOW6j+iZnyIsIGxlbihzZXQoaWRzKSkgPT0gMykKICAgIGdvdmVybihQLCBhcHBs
eT1UcnVlKSAgICAgICMg6YCA5b255b6M6YeN55m86JmfLOiuk+W+jOmdoiDikasgcHVsbCDnmoQgcGVuZGluZyDmrbjpm7YKICAgIF93KFBbInJlZ2lzdHJ5
Il0gLyAiVklBX1BvbGljeV9MYXdzX1NTT1RfdjAxMDcuanNvbiIsIHsibGF3cyI6IFt7ImlkIjogIkwxMTUifV19KQogICAgbHcgPSBsYXdfYXBwZW5kXzEx
NihQKQogICAgY2hrKCLika8gdjAxMDMgbGF3OkwxMTYg6ZmE6YCyIHYwMTA4IMK3IOWGjei3kSBTS0lQIiwgbHdbInN0YXR1cyJdID09ICJXUklUVEVOIiBh
bmQgbHdbIm5ldyJdID09ICJWSUFfUG9saWN5X0xhd3NfU1NPVF92MDEwOC5qc29uIiBhbmQgbGF3X2FwcGVuZF8xMTYoUClbInN0YXR1cyJdID09ICJTS0lQ
IikKICAgIHBhY2sgPSBwYXN0ZV9wYWNrKGFwNCkKICAgIGNhcmQgPSB3cml0ZV9jYXJkKGFwNCwgcGFjaywgUCkKICAgIGNoaygi4pGpIOiyvOWbnuWMhSDi
iaQzMDAg6KGMIMK3IE5FWFQ6IMK3IOWNoeWcqCDCtyDlj6rlr6vlm5vomZUoVlJOL1ZERiDlpL7lj6rmnInlrZDns7vntbHoh6rlt7HnmoTlhoopIiwgbGVu
KHBhY2spIDw9IDMwMCBhbmQgcGFja1stMV0uc3RhcnRzd2l0aCgiTkVYVDoiKSBhbmQgUGF0aChjYXJkWyJtZCJdKS5leGlzdHMoKQogICAgICAgIGFuZCBz
b3J0ZWQocS5uYW1lIGZvciBxIGluIChQWyJ2cm4iXSAvICJyZWdpc3RyeSIpLmdsb2IoIioiKSkgPT0gWyJWUk5fRnVuY3Rpb25NYXRyaXhfdjAxMDAuanNv
biIsICJWUk5fVGFibGVIZWFkZXJfdjAxMDAuanNvbiJdKQogICAgcHIgPSBwdWxsX3NlbGYoUCkKICAgIGNoaygi4pGrIHYwMTAxIHB1bGw6VkNHQyDoh6rl
t7HnmoTlip/og73nn6npmaPoroDlm57omZ8oZmlsbGVkIOKJpTEscGVuZGluZyAwKSIsIHByWyJmbiJdWyJmaWxsZWQiXSA+PSAxIGFuZCBwclsiZm4iXVsi
cGVuZGluZyJdID09IDApCiAgICBfdyhQWyJyb290Il0gLyAiVklBX1JlcG9ydHMiIC8gInZybiIgLyAiSEVBTFRIX2xhdGVzdC5qc29uIiwgeyJmaWxlcyI6
IFt7InRhaWwiOiAiVlJOX0VORzAwMV9BX3YwMTAwLnB5IiwgImxhbXAiOiAiUkVEIiwgImFzdF9vayI6IFRydWUsICJuZXRfbm90ZSI6ICLnhKHntrLmqYsi
fV19KQogICAgYW4gPSBhbm5vdGF0ZSgiVlJOIiwgUCwgYXBwbHk9VHJ1ZSkKICAgIGJrID0ganNvbi5sb2FkcyhfdGhfcmVhZChQWyJyZWdpc3RyeSJdIC8g
IlZJQV9Bc3RBbm5vdGF0aW9uc19WUk5fdjAxMDAuanNvbiIpKQogICAgaXQgPSBia1siaXRlbXMiXVsiRk5DfFZSTl9FTkcwMDFfQXxzaGFyZWQiXQogICAg
Y2hrKCLikawgdjAxMDEgYW5ub3RhdGU6VlJOIOWBtOWGiiDpoIUgJWQgwrcgc2hhcmVkIOacieiZnyDCtyDmnInliIbpoZ7oiIfoqqrmmI4gwrcg5YGl5bq3
57SF5peX5L215YWlIMK3IOWGjei3keWFqOWQjCIgJSBhblsic3VtbWFyeSJdWyJpdGVtcyJdLCBhblsic3VtbWFyeSJdWyJpdGVtcyJdID49IDMgYW5kIGl0
WyJjb2RlIl0gYW5kIGl0WyJjYXQiXSBhbmQgaXRbInpoIl0gYW5kIGl0WyJoZWFsdGgiXSA9PSAi54Sh57ay5qmLIiBhbmQgYW5ub3RhdGUoIlZSTiIsIFAs
IGFwcGx5PVRydWUpWyJuZXciXSA9PSAwKQogICAgYm9keSA9IE1FLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQogICAgY2hrKCLikaog5bi25Yqg6YCf
5Zmo5qmLIMK3IOWFqeWFseeUqOautSDCtyBWSUFfRlJPTV9WQ0dDIOmWmCIsICJbVklBOkFDQ0VMLUJSSURHRTp2MDEwMF0iIGluIGJvZHkgYW5kICJbVklB
OlRBQkxFLUhFQURFUjp2MDEwMF0iIGluIGJvZHkgYW5kICJbVklBOkZOLU1BVFJJWDp2MDEwMF0iIGluIGJvZHkgYW5kICJWSUFfRlJPTV9WQ0dDIiBpbiBi
b2R5KQogICAgb3MuZW52aXJvbi5wb3AoIlZJQV9ST09UIiwgTm9uZSkKICAgIHNodXRpbC5ybXRyZWUodGQsIGlnbm9yZV9lcnJvcnM9VHJ1ZSkKICAgIHBy
aW50KCJb6KiIXSAlcyDoh6rmuKwgJWQvJWQgwrcgJXMiICUgKE5BTUUsIHAsIHAgKyBmLCAiUEFTUyIgaWYgZiA9PSAwIGVsc2UgIkZBSUwiKSkKICAgIHJl
dHVybiAwIGlmIGYgPT0gMCBlbHNlIDEKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcmFpc2UgU3lzdGVtRXhpdChtYWluKCkpCg==
'@
$okSkel = Install-VIAEmbedded -Path (Join-Path $VIA 'VeritasCeleritas.PS7.Skeleton-v0112.ps1') -B64 $B64Skel -Want '541141e0d183bc1c5e8a181613564f8582318c5e97fed0aef6497026958a8b34' -Tag 'Skeleton-v0112(啟動器段)'
$okVdf = Install-VIATail $VdfDir 'VDF_SystemManager' 'v0147' $B64Vdf '855759b2b4f348033315bd77ceb8ae849564537038d65ea4e3c3e183167ea3a5' 'VDF v0147(quote)'
$VrnDir = Join-Path $VIA 'functional modules\VRN'
$B64Vrn = @'
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJWUk5fU3lzdGVtTWFuYWdlciB2MDE0NyDigJQg6JaE5bC+OmFubnVh
bCDmlLbmk5roroDlj5bmlLnpgZ7ov7Qo5pS+6KGML+iqnuaEjy/nrpflvI8v5rqQ5qC8L+mHkemhjeW+i+WcqOW3oueLgOaIluWtkOWkviBqc29uIOijoTt2
MDE0NiDlj6roroDpoILlsaTljbAgTm9uZSk7KOaTjeS9nOWToSAyMDI2LTEwLTA4OnYwMTA4IOW5tOW6puiyoeWgseS6pOaOpeWMhemalOmbouippui3kSBQ
QVNTIOKGkiDmjqXlhaXkuI3mkKzmqpQp44CCCiAgYW5udWFsIHN0YXR1cyAgICAgICAgICAgIOaJviBpbnRha2UvVlJOX3YwMTA4X0FubnVhbC8qKi9SdW5B
bmRWZXJpZnkucHMxIOeahOWMheaguSDihpIg5pyA5pawIHJ1bnMvPHg+LyDnmoQgUlVOX1NUQVRVUy5qc29uIMK3IFJFU1VMVF9WRVJJRklDQVRJT04uanNv
biDCtyBWRVJJRklDQVRJT05fdjAxMDguanNvbiDmkZjopoEo54uA5oWLIMK3IDE3IOmghSDCtyDnrpflvI8gwrcg5rqQ5qC8KQogIGFubnVhbCBydW4gICAg
ICAgICAgICAgICDnlKjljIXoh6rlt7HnmoQgLnZlbnYzMTIo5rKS5pyJ5bCxIHZpYV9wZGZfdG9vbHMp6LeR5YyF55qE5YWl5Y+jIFJ1bkFuZFZlcmlmeS5w
czEocHdzaCAtTm9Qcm9maWxlIC1GaWxlO+mAvuaZgiBWSUFfQU5OVUFMX1NFQyzpoJDoqK0gMjQwMCnihpIg6K6A5pawIHJ1bnMg4oaSIOeZuyByZWdpc3Ry
eS9WUk5fQW5udWFsX0xlZGdlci5qc29ubChydW4g5aS+IMK3IOeLgOaFiyDCtyDmlbjlrZcgwrcgc2hhIG9mIFJVTl9TVEFUVVMpCiAgYW5udWFsIHJlZ2lz
dGVyICAgICAgICAgIOaKiuacgOaWsCBydW4g55m75bizKOS4jei3kSk7YW5udWFsIGxlZGdlciDliJfluLMKICDopo/nn6k65YyFIDE5OSDmqpTpm7bmlLnl
i5U7VlJOIOWPquOAjOaMh+WQkSArIOiugOaUtuaTmiArIOiomOW4s+OAjTvljIXnmoQgbGltaXRhdGlvbihHUyDnvLrlgLwgLyBDTFNUIOefm+ebvik9IOm7
gwrlhbbppJjli5XoqZ7nhafliY3niYjpj4jjgIIKIiIiCmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCiMgPT09PT0gW1ZJQTpBQ0NFTC1C
UklER0U6djAxMDBdIFN1cGVyQWNjZWwg5Yqg6YCf5Zmo5qmLKOaJuTEwMiDlhajmqLnlsI7lhaXku6Q7Z3JhY2VmdWwg6Zu26KGM54K66K6K5pu0KSA9PT09
PQp0cnk6CiAgICBpbXBvcnQgc3lzIGFzIF9zYV9zeXMKICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aCBhcyBfc2FfUGF0aAogICAgX3NhX3AgPSBfc2Ff
UGF0aChfX2ZpbGVfXykucmVzb2x2ZSgpCiAgICB3aGlsZSBfc2FfcC5wYXJlbnQgIT0gX3NhX3A6CiAgICAgICAgaWYgKF9zYV9wIC8gInN1cHBvcnRpdmUg
bW9kdWxlcyIgLyAiVklBX1N1cGVyQWNjZWxfTW9kdWxlLnB5IikuZXhpc3RzKCk6CiAgICAgICAgICAgIF9zYV9zeXMucGF0aC5pbnNlcnQoMCwgc3RyKF9z
YV9wIC8gInN1cHBvcnRpdmUgbW9kdWxlcyIpKQogICAgICAgICAgICBicmVhawogICAgICAgIF9zYV9wID0gX3NhX3AucGFyZW50CiAgICBpbXBvcnQgVklB
X1N1cGVyQWNjZWxfTW9kdWxlIGFzIFZJQV9BQ0NFTCAgIyBub3FhOiBGNDAxCmV4Y2VwdCBJbXBvcnRFcnJvcjoKICAgIFZJQV9BQ0NFTCA9IE5vbmUKIyA9
PT09PSBbVklBOkFDQ0VMLUJSSURHRTpFTkRdID09PT09CgppbXBvcnQgZGF0ZXRpbWUKaW1wb3J0IGhhc2hsaWIKaW1wb3J0IGltcG9ydGxpYi51dGlsCmlt
cG9ydCBqc29uCmltcG9ydCBvcwppbXBvcnQgcmUKaW1wb3J0IHN1YnByb2Nlc3MKaW1wb3J0IHN5cwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCkhFUkUg
PSBQYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkucGFyZW50Cl9TVEVNID0gIlZSTl9TeXN0ZW1NYW5hZ2VyIgpUQUcgPSAidjAxNDciCgoKZGVmIF92bnVtX3Yw
MTQ3KHBhdGgpIC0+IGludDoKICAgIG0gPSByZS5zZWFyY2gociJfdihcZHs0fSkkIiwgUGF0aChwYXRoKS5zdGVtKQogICAgcmV0dXJuIGludChtLmdyb3Vw
KDEpKSBpZiBtIGVsc2UgLTEKCgpkZWYgX2xvYWRfdjAxNDcocGF0aDogUGF0aCwgbmFtZTogc3RyKToKICAgIGlmIG5hbWUgbm90IGluIHN5cy5tb2R1bGVz
OgogICAgICAgIHNwZWMgPSBpbXBvcnRsaWIudXRpbC5zcGVjX2Zyb21fZmlsZV9sb2NhdGlvbihuYW1lLCBwYXRoKQogICAgICAgIG1vZCA9IGltcG9ydGxp
Yi51dGlsLm1vZHVsZV9mcm9tX3NwZWMoc3BlYykKICAgICAgICBzeXMubW9kdWxlc1tuYW1lXSA9IG1vZAogICAgICAgIHNwZWMubG9hZGVyLmV4ZWNfbW9k
dWxlKG1vZCkKICAgIHJldHVybiBzeXMubW9kdWxlc1tuYW1lXQoKClBSSU9SX1BBVEggPSBtYXgoKHAgZm9yIHAgaW4gSEVSRS5nbG9iKF9TVEVNICsgIl92
Ki5weSIpIGlmIDAgPD0gX3ZudW1fdjAxNDcocCkgPCBfdm51bV92MDE0NyhfX2ZpbGVfXykpLCBrZXk9X3ZudW1fdjAxNDcpClBSSU9SID0gX2xvYWRfdjAx
NDcoUFJJT1JfUEFUSCwgX1NURU0gKyAiX3ByaW9yX2Zvcl8iICsgUGF0aChfX2ZpbGVfXykuc3RlbSkKCgpkZWYgX19nZXRhdHRyX18obmFtZSk6CiAgICBy
ZXR1cm4gZ2V0YXR0cihQUklPUiwgbmFtZSkKCgpkZWYgX2hvbWUoKToKICAgIHJldHVybiBQYXRoKG9zLmVudmlyb24uZ2V0KCJWSUFfVlJOX1NTT1RfSE9N
RSIpIG9yIEhFUkUpCgoKZGVmIGFubnVhbF9wYWNrKCkgLT4gUGF0aCB8IE5vbmU6CiAgICByb290ID0gUGF0aChvcy5lbnZpcm9uLmdldCgiVklBX1ZSTl9B
Tk5VQUxfUEFDSyIpIG9yIChfaG9tZSgpIC8gImludGFrZSIgLyAiVlJOX3YwMTA4X0FubnVhbCIpKQogICAgaWYgbm90IHJvb3QuaXNfZGlyKCk6CiAgICAg
ICAgcmV0dXJuIE5vbmUKICAgIGhpdHMgPSBzb3J0ZWQocm9vdC5yZ2xvYigiUnVuQW5kVmVyaWZ5LnBzMSIpLCBrZXk9bGFtYmRhIHA6IGxlbihwLnBhcnRz
KSkKICAgIHJldHVybiBoaXRzWzBdLnBhcmVudCBpZiBoaXRzIGVsc2UgTm9uZQoKCmRlZiBfbGF0ZXN0X3J1bihwazogUGF0aCkgLT4gUGF0aCB8IE5vbmU6
CiAgICBydW5zID0gcGsgLyAicnVucyIKICAgIGlmIG5vdCBydW5zLmlzX2RpcigpOgogICAgICAgIHJldHVybiBOb25lCiAgICBkcyA9IFtkIGZvciBkIGlu
IHJ1bnMuaXRlcmRpcigpIGlmIGQuaXNfZGlyKCldCiAgICByZXR1cm4gbWF4KGRzLCBrZXk9bGFtYmRhIGQ6IGQuc3RhdCgpLnN0X210aW1lKSBpZiBkcyBl
bHNlIE5vbmUKCgpkZWYgX3JkKHA6IFBhdGgpOgogICAgdHJ5OgogICAgICAgIHJldHVybiBqc29uLmxvYWRzKHAucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYt
OC1zaWciKSkgaWYgcC5leGlzdHMoKSBlbHNlIE5vbmUKICAgIGV4Y2VwdCBWYWx1ZUVycm9yOgogICAgICAgIHJldHVybiBOb25lCgoKZGVmIGFubnVhbF9z
dGF0dXMoKSAtPiBkaWN0OgogICAgcGsgPSBhbm51YWxfcGFjaygpCiAgICBvdXQgPSB7InZlcmIiOiAiYW5udWFsX3N0YXR1cyIsICJwYWNrIjogc3RyKHBr
KSBpZiBwayBlbHNlIE5vbmUsICJydW4iOiBOb25lLCAibGFtcCI6ICJHUkFZIn0KICAgIGlmIG5vdCBwazoKICAgICAgICBvdXRbIndoeSJdID0gImludGFr
ZS9WUk5fdjAxMDhfQW5udWFsIOijoeaJvuS4jeWIsCBSdW5BbmRWZXJpZnkucHMxKOWFiOi3kSBJbnZva2UtVklBLVZSTi1IYW5kb3ZlclRlc3QpIgogICAg
ICAgIHJldHVybiBvdXQKICAgIG91dFsidmVudiJdID0gc3RyKHBrIC8gIi52ZW52MzEyIiAvICJTY3JpcHRzIiAvICJweXRob24uZXhlIikgaWYgKHBrIC8g
Ii52ZW52MzEyIikuaXNfZGlyKCkgZWxzZSBOb25lCiAgICBydW4gPSBfbGF0ZXN0X3J1bihwaykKICAgIGlmIG5vdCBydW46CiAgICAgICAgb3V0WyJ3aHki
XSA9ICLljIXpgoTmspLot5HpgY4oYW5udWFsIHJ1bikiCiAgICAgICAgcmV0dXJuIG91dAogICAgcnMgPSBfcmQocnVuIC8gIlJVTl9TVEFUVVMuanNvbiIp
IG9yIHt9CiAgICBydiA9IF9yZChydW4gLyAiUkVTVUxUX1ZFUklGSUNBVElPTi5qc29uIikgb3Ige30KICAgIHN0YXR1cyA9IHN0cihycy5nZXQoIm92ZXJh
bGxfc3RhdHVzIikgb3IgcnMuZ2V0KCJzdGF0dXMiKSBvciBydi5nZXQoIm92ZXJhbGxfc3RhdHVzIikgb3IgcnYuZ2V0KCJzdGF0dXMiKSBvciAiIikKICAg
IGRlZiB3YWxrKG9iaik6CiAgICAgICAgaWYgaXNpbnN0YW5jZShvYmosIGRpY3QpOgogICAgICAgICAgICBmb3IgaywgdiBpbiBvYmouaXRlbXMoKToKICAg
ICAgICAgICAgICAgIHlpZWxkIGssIHYKICAgICAgICAgICAgICAgIHlpZWxkIGZyb20gd2Fsayh2KQogICAgICAgIGVsaWYgaXNpbnN0YW5jZShvYmosIGxp
c3QpOgogICAgICAgICAgICBmb3IgdiBpbiBvYmo6CiAgICAgICAgICAgICAgICB5aWVsZCBmcm9tIHdhbGsodikKICAgIHBvb2wgPSBbXQogICAgZm9yIGpw
IGluIHNvcnRlZChydW4ucmdsb2IoIiouanNvbiIpLCBrZXk9bGFtYmRhIHE6IChxLm5hbWUgbm90IGluICgiUlVOX1NUQVRVUy5qc29uIiwgIlJFU1VMVF9W
RVJJRklDQVRJT04uanNvbiIsICJWRVJJRklDQVRJT05fdjAxMDguanNvbiIpLCBsZW4ocS5wYXJ0cykpKToKICAgICAgICBpZiBqcC5zdGF0KCkuc3Rfc2l6
ZSA+IDJfMDAwXzAwMDoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBkID0gX3JkKGpwKQogICAgICAgIGlmIGQgaXMgbm90IE5vbmU6CiAgICAgICAg
ICAgIHBvb2wuYXBwZW5kKChqcC5uYW1lLCBkKSkKICAgIGRlZiBkaWcoKmtleXMpOgogICAgICAgIGZvciBrIGluIGtleXM6CiAgICAgICAgICAgIGZvciBf
LCBkIGluIHBvb2w6CiAgICAgICAgICAgICAgICBmb3Iga2ssIHZ2IGluIHdhbGsoZCk6CiAgICAgICAgICAgICAgICAgICAgaWYga2sgPT0gayBhbmQgaXNp
bnN0YW5jZSh2diwgKGludCwgZmxvYXQsIHN0cikpOgogICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gdnYKICAgICAgICByZXR1cm4gTm9uZQogICAg
b3V0LnVwZGF0ZShydW49c3RyKHJ1biksIHN0YXR1cz1zdGF0dXMsIGNoZWNrc19wYXNzPWRpZygicmVsZWFzZV9nYXRlX2NoZWNrc19wYXNzIiwgImNoZWNr
c19wYXNzIiksIHNlbWFudGljX3Bhc3M9ZGlnKCJzZW1hbnRpY19jaGVja3NfcGFzcyIpLCBlcXVhdGlvbnNfcGFzcz1kaWcoImFubnVhbF9lcXVhdGlvbnNf
cGFzcyIpLCBzb3VyY2VfY2VsbHNfcGFzcz1kaWcoInNvdXJjZV9jZWxsc19wYXNzIiksIGFtb3VudF9wb2xpY3lfcGFzcz1kaWcoImFtb3VudF9wb2xpY3lf
dGVzdHNfcGFzcyIpLCBmaWxlcz1zdW0oMSBmb3IgXyBpbiBydW4ucmdsb2IoIioiKSBpZiBfLmlzX2ZpbGUoKSksCiAgICAgICAgICAgICAgIHJ1bl9zdGF0
dXNfc2hhPShoYXNobGliLnNoYTI1NigocnVuIC8gIlJVTl9TVEFUVVMuanNvbiIpLnJlYWRfYnl0ZXMoKSkuaGV4ZGlnZXN0KClbOjEyXSBpZiAocnVuIC8g
IlJVTl9TVEFUVVMuanNvbiIpLmV4aXN0cygpIGVsc2UgTm9uZSkpCiAgICBvdXRbImxhbXAiXSA9ICJHUkVFTiIgaWYgc3RhdHVzLnVwcGVyKCkuc3RhcnRz
d2l0aCgiUEFTUyIpIGFuZCAiTElNSVQiIG5vdCBpbiBzdGF0dXMudXBwZXIoKSBlbHNlICgiWUVMTE9XIiBpZiBzdGF0dXMudXBwZXIoKS5zdGFydHN3aXRo
KCJQQVNTIikgZWxzZSAoIlJFRCIgaWYgc3RhdHVzIGVsc2UgIkdSQVkiKSkKICAgIG91dFsibGltaXRhdGlvbiJdID0gIuS+hua6kOmZkOWItihHUyDnvLrl
gLwgLyBDTFNUIOWOn+aWh+efm+ebvuS/neeVmSkiIGlmICJMSU1JVCIgaW4gc3RhdHVzLnVwcGVyKCkgZWxzZSAiIgogICAgcmV0dXJuIG91dAoKCmRlZiBh
bm51YWxfcmVnaXN0ZXIoc3Q6IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdDoKICAgIHN0ID0gc3Qgb3IgYW5udWFsX3N0YXR1cygpCiAgICBpZiBub3Qg
c3QuZ2V0KCJydW4iKToKICAgICAgICByZXR1cm4gZGljdChzdCwgcmVnaXN0ZXJlZD1GYWxzZSkKICAgIGxlZCA9IF9ob21lKCkgLyAicmVnaXN0cnkiIC8g
IlZSTl9Bbm51YWxfTGVkZ2VyLmpzb25sIgogICAgbGVkLnBhcmVudC5ta2RpcihleGlzdF9vaz1UcnVlKQogICAgcHJldiA9IFtqc29uLmxvYWRzKGxuKSBm
b3IgbG4gaW4gbGVkLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKS5zcGxpdGxpbmVzKCkgaWYgbG4uc3RyaXAoKV0gaWYgbGVkLmV4aXN0cygpIGVsc2Ug
W10KICAgIGlmIGFueShwLmdldCgicnVuIikgPT0gc3RbInJ1biJdIGZvciBwIGluIHByZXYpOgogICAgICAgIHJldHVybiBkaWN0KHN0LCByZWdpc3RlcmVk
PUZhbHNlLCB3aHk9IuW3sueZu+mBjiIpCiAgICByZWMgPSB7azogc3QuZ2V0KGspIGZvciBrIGluICgicGFjayIsICJydW4iLCAic3RhdHVzIiwgImNoZWNr
c19wYXNzIiwgInNlbWFudGljX3Bhc3MiLCAiZXF1YXRpb25zX3Bhc3MiLCAic291cmNlX2NlbGxzX3Bhc3MiLCAiYW1vdW50X3BvbGljeV9wYXNzIiwgImZp
bGVzIiwgInJ1bl9zdGF0dXNfc2hhIiwgImxhbXAiLCAibGltaXRhdGlvbiIpfQogICAgcmVjWyJ0cyJdID0gZGF0ZXRpbWUuZGF0ZXRpbWUubm93KCkuaXNv
Zm9ybWF0KHRpbWVzcGVjPSJzZWNvbmRzIikKICAgIHJlY1sibWFuYWdlciJdID0gUGF0aChfX2ZpbGVfXykubmFtZQogICAgd2l0aCBsZWQub3BlbigiYSIs
IGVuY29kaW5nPSJ1dGYtOCIpIGFzIGZoOgogICAgICAgIGZoLndyaXRlKGpzb24uZHVtcHMocmVjLCBlbnN1cmVfYXNjaWk9RmFsc2UpICsgIlxuIikKICAg
IHJldHVybiBkaWN0KHN0LCByZWdpc3RlcmVkPVRydWUsIGxlZGdlcj1zdHIobGVkKSwgbj1sZW4ocHJldikgKyAxKQoKCmRlZiBhbm51YWxfcnVuKCkgLT4g
ZGljdDoKICAgIHBrID0gYW5udWFsX3BhY2soKQogICAgaWYgbm90IHBrOgogICAgICAgIHJldHVybiB7InZlcmIiOiAiYW5udWFsX3J1biIsICJsYW1wIjog
IlJFRCIsICJ3aHkiOiAi5YyF5LiN5ZyoIn0KICAgIHZweSA9IHBrIC8gIi52ZW52MzEyIiAvICJTY3JpcHRzIiAvICJweXRob24uZXhlIgogICAgaWYgbm90
IHZweS5leGlzdHMoKToKICAgICAgICB2cHkgPSBfaG9tZSgpLnBhcmVudHNbMV0gLyAiZW52cyIgLyAidmlhX3BkZl90b29scyIgLyAiU2NyaXB0cyIgLyAi
cHl0aG9uLmV4ZSIKICAgIGVudiA9IGRpY3Qob3MuZW52aXJvbiwgVklBX1BZVEhPTj1zdHIodnB5KSwgUFlUSE9OPXN0cih2cHkpLCBQWVRIT05VVEY4PSIx
IiwgVklSVFVBTF9FTlY9c3RyKHZweS5wYXJlbnQucGFyZW50KSwgUEFUSD1zdHIodnB5LnBhcmVudCkgKyBvcy5wYXRoc2VwICsgb3MuZW52aXJvbi5nZXQo
IlBBVEgiLCAiIikpCiAgICBiZWZvcmUgPSB7ZC5uYW1lIGZvciBkIGluIChwayAvICJydW5zIikuaXRlcmRpcigpfSBpZiAocGsgLyAicnVucyIpLmlzX2Rp
cigpIGVsc2Ugc2V0KCkKICAgIHB3c2ggPSAicHdzaCIKICAgIHRyeToKICAgICAgICBjcCA9IHN1YnByb2Nlc3MucnVuKFtwd3NoLCAiLU5vUHJvZmlsZSIs
ICItRXhlY3V0aW9uUG9saWN5IiwgIkJ5cGFzcyIsICItRmlsZSIsIHN0cihwayAvICJSdW5BbmRWZXJpZnkucHMxIildLCBjd2Q9c3RyKHBrKSwgZW52PWVu
diwgY2FwdHVyZV9vdXRwdXQ9VHJ1ZSwgdGV4dD1UcnVlLCBlbmNvZGluZz0idXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiLCB0aW1lb3V0PWludChvcy5lbnZp
cm9uLmdldCgiVklBX0FOTlVBTF9TRUMiLCAiMjQwMCIpKSkKICAgICAgICByYywgdGFpbCA9IGNwLnJldHVybmNvZGUsIChjcC5zdGRvdXQgb3IgIiIpWy0x
NTAwOl0KICAgIGV4Y2VwdCBzdWJwcm9jZXNzLlRpbWVvdXRFeHBpcmVkOgogICAgICAgIHJldHVybiB7InZlcmIiOiAiYW5udWFsX3J1biIsICJsYW1wIjog
IlJFRCIsICJ3aHkiOiAi6YC+5pmCIn0KICAgIGV4Y2VwdCBGaWxlTm90Rm91bmRFcnJvcjoKICAgICAgICByZXR1cm4geyJ2ZXJiIjogImFubnVhbF9ydW4i
LCAibGFtcCI6ICJSRUQiLCAid2h5IjogInB3c2gg5LiN5ZyoIFBBVEgifQogICAgYWZ0ZXIgPSB7ZC5uYW1lIGZvciBkIGluIChwayAvICJydW5zIikuaXRl
cmRpcigpfSBpZiAocGsgLyAicnVucyIpLmlzX2RpcigpIGVsc2Ugc2V0KCkKICAgIHN0ID0gYW5udWFsX3N0YXR1cygpCiAgICBzdC51cGRhdGUodmVyYj0i
YW5udWFsX3J1biIsIHJjPXJjLCBuZXdfcnVucz1zb3J0ZWQoYWZ0ZXIgLSBiZWZvcmUpLCBsb2dfdGFpbD10YWlsWy00MDA6XSkKICAgIGlmIHN0LmdldCgi
cnVuIik6CiAgICAgICAgc3QgPSBhbm51YWxfcmVnaXN0ZXIoc3QpCiAgICByZXR1cm4gc3QKCgpkZWYgX3ByaW50X2FubnVhbChvOiBkaWN0KSAtPiBOb25l
OgogICAgaWYgbm90IG8uZ2V0KCJydW4iKToKICAgICAgICBwcmludCgiW+ioiF0gVlJOIGFubnVhbCDCtyAlcyDCtyAlcyDCtyAlcyIgJSAoby5nZXQoInBh
Y2siKSBvciAi5YyF5LiN5ZyoIiwgby5nZXQoIndoeSIsICIiKSwgb1sibGFtcCJdKSkKICAgICAgICByZXR1cm4KICAgIHByaW50KCJb6KiIXSBWUk4gYW5u
dWFsIMK3ICVzIMK3IHJ1biAlcyDCtyAlcyDCtyDmlL7ooYwgJXMgwrcg6Kqe5oSPICVzIMK3IOeul+W8jyAlcyDCtyDmupDmoLwgJXMgwrcg6YeR6aGN5b6L
ICVzIMK3IOaqlCAlcyDCtyBzaGEgJXMlcyDCtyAlcyIgJSAoby5nZXQoInZlcmIiKSwgUGF0aChvWyJydW4iXSkubmFtZSwgby5nZXQoInN0YXR1cyIpLCBv
LmdldCgiY2hlY2tzX3Bhc3MiKSwgby5nZXQoInNlbWFudGljX3Bhc3MiKSwgby5nZXQoImVxdWF0aW9uc19wYXNzIiksIG8uZ2V0KCJzb3VyY2VfY2VsbHNf
cGFzcyIpLCBvLmdldCgiYW1vdW50X3BvbGljeV9wYXNzIiksIG8uZ2V0KCJmaWxlcyIpLCBvLmdldCgicnVuX3N0YXR1c19zaGEiKSwgKCIgwrcg55m75biz
ICMlZCIgJSBvWyJuIl0pIGlmIG8uZ2V0KCJyZWdpc3RlcmVkIikgZWxzZSAoIiDCtyAiICsgb1sid2h5Il0gaWYgby5nZXQoIndoeSIpIGVsc2UgIiIpLCBv
WyJsYW1wIl0pKQogICAgaWYgby5nZXQoImxpbWl0YXRpb24iKToKICAgICAgICBwcmludCgiICBbWUVMXSAlcyjljIXnmoToqqDlr6bmqJnoqJgs5LiN5piv
56iL5byP6YyvKSIgJSBvWyJsaW1pdGF0aW9uIl0pCiAgICBpZiBvLmdldCgicmMiKSBpcyBub3QgTm9uZToKICAgICAgICBwcmludCgiICBbT0tdIOWMheWF
peWPoyByYyAlcyDCtyDmlrAgcnVuICVzIiAlIChvWyJyYyJdLCAiLCIuam9pbihvLmdldCgibmV3X3J1bnMiKSBvciBbXSkgb3IgIueEoSIpKQoKCmRlZiBt
YWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgYXJncyA9IGxpc3Qoc3lzLmFyZ3ZbMTpdIGlmIGFyZ3YgaXMgTm9uZSBlbHNlIGFyZ3YpCiAgICBvcy5lbnZp
cm9uLnNldGRlZmF1bHQoIlZJQV9GUk9NX1ZDR0MiLCAiWUVTIikKICAgIGlmICItLXNlbGZ0ZXN0IiBpbiBhcmdzWzoyXToKICAgICAgICByZXR1cm4gc2Vs
ZnRlc3QoKQogICAgaWYgYXJnc1s6MV0gPT0gWyJhbm51YWwiXToKICAgICAgICBzdWIgPSBhcmdzWzFdIGlmIGxlbihhcmdzKSA+IDEgZWxzZSAic3RhdHVz
IgogICAgICAgIGlmIHN1YiA9PSAic3RhdHVzIjoKICAgICAgICAgICAgbyA9IGFubnVhbF9zdGF0dXMoKQogICAgICAgIGVsaWYgc3ViID09ICJydW4iOgog
ICAgICAgICAgICBvID0gYW5udWFsX3J1bigpCiAgICAgICAgZWxpZiBzdWIgPT0gInJlZ2lzdGVyIjoKICAgICAgICAgICAgbyA9IGFubnVhbF9yZWdpc3Rl
cigpCiAgICAgICAgZWxpZiBzdWIgPT0gImxlZGdlciI6CiAgICAgICAgICAgIGxlZCA9IF9ob21lKCkgLyAicmVnaXN0cnkiIC8gIlZSTl9Bbm51YWxfTGVk
Z2VyLmpzb25sIgogICAgICAgICAgICByb3dzID0gW2pzb24ubG9hZHMobG4pIGZvciBsbiBpbiBsZWQucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpLnNw
bGl0bGluZXMoKSBpZiBsbi5zdHJpcCgpXSBpZiBsZWQuZXhpc3RzKCkgZWxzZSBbXQogICAgICAgICAgICBwcmludCgiW+ioiF0gVlJOIGFubnVhbCBsZWRn
ZXIgwrcgJWQg562GIiAlIGxlbihyb3dzKSkKICAgICAgICAgICAgZm9yIHIgaW4gcm93c1stMTA6XToKICAgICAgICAgICAgICAgIHByaW50KCIgIFtPS10g
JXMgwrcgJXMgwrcgJXMgwrcg5pS+6KGMICVzIMK3IOeul+W8jyAlcyDCtyAlcyIgJSAoci5nZXQoInRzIiksIFBhdGgoci5nZXQoInJ1biIsICIiKSkubmFt
ZSwgci5nZXQoInN0YXR1cyIpLCByLmdldCgiY2hlY2tzX3Bhc3MiKSwgci5nZXQoImVxdWF0aW9uc19wYXNzIiksIHIuZ2V0KCJsYW1wIikpKQogICAgICAg
ICAgICByZXR1cm4gMAogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHByaW50KCJb5ouS6LeRXSBhbm51YWwgc3RhdHVzIHwgcnVuIHwgcmVnaXN0ZXIgfCBs
ZWRnZXIiKQogICAgICAgICAgICByZXR1cm4gMgogICAgICAgIF9wcmludF9hbm51YWwobykKICAgICAgICByZXR1cm4gMSBpZiBvWyJsYW1wIl0gPT0gIlJF
RCIgZWxzZSAwCiAgICByZXR1cm4gUFJJT1IubWFpbihhcmdzKQoKCmRlZiBzZWxmdGVzdCgpIC0+IGludDoKICAgIGltcG9ydCBzaHV0aWwKICAgIGltcG9y
dCB0ZW1wZmlsZQogICAgcCA9IGYgPSAwCgogICAgZGVmIGNoayhuYW1lLCBjb25kKToKICAgICAgICBub25sb2NhbCBwLCBmCiAgICAgICAgaWYgY29uZDoK
ICAgICAgICAgICAgcCArPSAxCiAgICAgICAgICAgIHByaW50KCIgIFtPS10gJXMiICUgbmFtZSkKICAgICAgICBlbHNlOgogICAgICAgICAgICBmICs9IDEK
ICAgICAgICAgICAgcHJpbnQoIiAgW0ZBSUxdICVzIiAlIG5hbWUpCgogICAgdGQgPSBQYXRoKHRlbXBmaWxlLm1rZHRlbXAocHJlZml4PSJ2cm5hbm4tIikp
CiAgICBob21lID0gdGQgLyAiZnVuY3Rpb25hbCBtb2R1bGVzIiAvICJWUk4iCiAgICBwayA9IGhvbWUgLyAiaW50YWtlIiAvICJWUk5fdjAxMDhfQW5udWFs
IiAvICJWUk5fdjAxMDhfQ29tcGxldGVfSGFuZG92ZXIiCiAgICAocGsgLyAicnVucyIgLyAiMjAyNjEwMDhfMDgyNzIyXzBmMGE1ZiIpLm1rZGlyKHBhcmVu
dHM9VHJ1ZSkKICAgIChob21lIC8gInJlZ2lzdHJ5IikubWtkaXIoKQogICAgc2F2ZWQgPSB7azogb3MuZW52aXJvbi5nZXQoaykgZm9yIGsgaW4gKCJWSUFf
VlJOX1NTT1RfSE9NRSIsICJWSUFfVlJOX0FOTlVBTF9QQUNLIil9CiAgICBvcy5lbnZpcm9uWyJWSUFfVlJOX1NTT1RfSE9NRSJdID0gc3RyKGhvbWUpCiAg
ICBvcy5lbnZpcm9uLnBvcCgiVklBX1ZSTl9BTk5VQUxfUEFDSyIsIE5vbmUpCiAgICAocGsgLyAiUnVuQW5kVmVyaWZ5LnBzMSIpLndyaXRlX3RleHQoImV4
aXQgMFxuIiwgZW5jb2Rpbmc9InV0Zi04IikKICAgIChwayAvICJydW5zIiAvICIyMDI2MTAwOF8wODI3MjJfMGYwYTVmIiAvICJSVU5fU1RBVFVTLmpzb24i
KS53cml0ZV90ZXh0KGpzb24uZHVtcHMoeyJvdmVyYWxsX3N0YXR1cyI6ICJQQVNTX1dJVEhfU09VUkNFX0xJTUlUQVRJT05TIiwgImdhdGVzIjogeyJyZWxl
YXNlX2dhdGVfY2hlY2tzX3Bhc3MiOiAxNywgInNlbWFudGljX2NoZWNrc19wYXNzIjogMTF9fSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICAocGsgLyAicnVu
cyIgLyAiMjAyNjEwMDhfMDgyNzIyXzBmMGE1ZiIgLyAic3ViIikubWtkaXIoKQogICAgKHBrIC8gInJ1bnMiIC8gIjIwMjYxMDA4XzA4MjcyMl8wZjBhNWYi
IC8gInN1YiIgLyAiVkVSSUZJQ0FUSU9OX3YwMTA4Lmpzb24iKS53cml0ZV90ZXh0KGpzb24uZHVtcHMoeyJzdW1tYXJ5IjogeyJhbm51YWxfZXF1YXRpb25z
X3Bhc3MiOiA0MDksICJzb3VyY2VfY2VsbHNfcGFzcyI6IDU0NjJ9LCAicG9saWN5IjogW3siYW1vdW50X3BvbGljeV90ZXN0c19wYXNzIjogMTZ9XX0pLCBl
bmNvZGluZz0idXRmLTgiKQogICAgc3QgPSBhbm51YWxfc3RhdHVzKCkKICAgIGNoaygi4pGgIHN0YXR1czrmib7liLDljIUgwrcg5pyA5pawIHJ1biDCtyBQ
QVNTX1dJVEhfU09VUkNFX0xJTUlUQVRJT05TIOKGkiDpu4Mgwrcg5bei54uAL+WtkOWkvuS5n+aKk+WIsCAxNy8xMS80MDkvNTQ2MiIsIHN0WyJwYWNrIl0g
PT0gc3RyKHBrKSBhbmQgc3RbInN0YXR1cyJdID09ICJQQVNTX1dJVEhfU09VUkNFX0xJTUlUQVRJT05TIiBhbmQgc3RbImxhbXAiXSA9PSAiWUVMTE9XIiBh
bmQgc3RbImNoZWNrc19wYXNzIl0gPT0gMTcgYW5kIHN0WyJlcXVhdGlvbnNfcGFzcyJdID09IDQwOSBhbmQgc3RbInNvdXJjZV9jZWxsc19wYXNzIl0gPT0g
NTQ2MikKICAgIHIxID0gYW5udWFsX3JlZ2lzdGVyKCk7IHIyID0gYW5udWFsX3JlZ2lzdGVyKCkKICAgIGNoaygi4pGhIHJlZ2lzdGVyOueZu+W4syAxIOet
hiDCtyDph43nmbsgU0tJUCIsIHIxWyJyZWdpc3RlcmVkIl0gYW5kIChob21lIC8gInJlZ2lzdHJ5IiAvICJWUk5fQW5udWFsX0xlZGdlci5qc29ubCIpLmV4
aXN0cygpIGFuZCBub3QgcjJbInJlZ2lzdGVyZWQiXSkKICAgIGNoaygi4pGiIOWMheS4jeWcqCDihpIgR1JBWSDoqqDlr6YiLCAobGFtYmRhOiAob3MuZW52
aXJvbi5fX3NldGl0ZW1fXygiVklBX1ZSTl9BTk5VQUxfUEFDSyIsIHN0cih0ZCAvICJub3BlIikpLCBhbm51YWxfc3RhdHVzKClbImxhbXAiXSA9PSAiR1JB
WSIpWzFdKSgpKQogICAgb3MuZW52aXJvbi5wb3AoIlZJQV9WUk5fQU5OVUFMX1BBQ0siLCBOb25lKQogICAgcHJpbnQoIiAg4pSA4pSAIOWJjeeJiOmPiOiH
qua4rCjljp/mqKPljbDlh7op4pSA4pSAIikKICAgIHByYyA9IDAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9TS0lQX1BSSU9SX1NFTEZURVNUIikgPT0gIjEi
IGVsc2UgUFJJT1Iuc2VsZnRlc3QoKQogICAgY2hrKCLikaMg5YmN54mI6Y+IICVzIOiHqua4rCByYyAwIiAlIFBSSU9SX1BBVEguc3RlbSwgcHJjID09IDAp
CiAgICBib2R5ID0gUGF0aChfX2ZpbGVfXykucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCiAgICBjaGsoIuKRpCDluLbliqDpgJ/lmajmqYsgwrcg5LiN
5pCs5qqUKOaykuaciSBzaHV0aWwuY29weS9tb3ZlIOWIsOWMheWFpykiLCAiW1ZJQTpBQ0NFTC1CUklER0U6djAxMDBdIiBpbiBib2R5IGFuZCAic2h1dGls
Lm1vdmUiIG5vdCBpbiBib2R5LnNwbGl0KCJkZWYgc2VsZnRlc3QiKVswXSBhbmQgInNodXRpbC5jb3B5IiBub3QgaW4gYm9keS5zcGxpdCgiZGVmIHNlbGZ0
ZXN0IilbMF0pCiAgICBmb3IgaywgdiBpbiBzYXZlZC5pdGVtcygpOgogICAgICAgIGlmIHYgaXMgTm9uZToKICAgICAgICAgICAgb3MuZW52aXJvbi5wb3Ao
aywgTm9uZSkKICAgICAgICBlbHNlOgogICAgICAgICAgICBvcy5lbnZpcm9uW2tdID0gdgogICAgc2h1dGlsLnJtdHJlZSh0ZCwgaWdub3JlX2Vycm9ycz1U
cnVlKQogICAgcHJpbnQoIlvoqIhdIFZSTl9TeXN0ZW1NYW5hZ2VyX3YwMTQ3IOiHqua4rCAlZC8lZCDCtyAlcyIgJSAocCwgcCArIGYsICJQQVNTIiBpZiBm
ID09IDAgZWxzZSAiRkFJTCIpKQogICAgcmV0dXJuIDAgaWYgZiA9PSAwIGVsc2UgMQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICByYWlzZSBT
eXN0ZW1FeGl0KG1haW4oKSkK
'@
$okVrn = Install-VIATail $VrnDir 'VRN_SystemManager' 'v0147' $B64Vrn '339fe4a2b1ad350deee4c7b579e9268837c306159cf1fd1ceef7c27b2b4f5a47' 'VRN v0147(annual 收據遞迴)'
$Existing = Get-ChildItem -LiteralPath $RegDir -Filter 'CGC_MDL*_RegistryGovernor_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$okGov = $false
if ($Existing -and $Existing.Name -match '^(CGC_MDL\d{3})_' -and $Existing.Name -lt ($Matches[1] + '_RegistryGovernor_v0105.py')) { $okGov = Install-VIAEmbedded -Path (Join-Path $RegDir ($Matches[1] + '_RegistryGovernor_v0105.py')) -B64 $B64Gov -Want '7fb07131bcf5497c3615743b1cdfe19e7d1a0860422ffce047b3cdf10002cd19' -Tag '治理引擎 v0105(law --file)' } elseif ($Existing) { $okGov = $true }
$B64Hm = @'
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJDR0MgSGVhbHRoTWF0cml4IHYwMTA3IOKAlCh2MDEwNzorcG9ydGFs
ID0g5LiA5YCLIFUvSSDpgKPkuInlgIsgU3lzdGVtTWFuYWdlcjroroDlkITlrZDns7vntbHoh6rloLHnmoQgPFNVQj5fVUlfTUFOSUZFU1QuanNvbihWQ0dD
IOiHquW3seS5n+Wvq+S4gOS7vSnihpIgVklBX1JlcG9ydHMvVklBX1VJX2xhdGVzdC5odG1sIOWFpeWPozrkuIrliJfkuInns7vntbHnh4joiIfliIfmj5vp
iJUo5ruR6bygKSzkuIvmlrnovInlhaXmiYDpgbjns7vntbHoh6rlt7HnmoTpoIE75riF5Zau6K6K6aCB5bCx6K6KLOaooeadv+i1sOWGijvmr43ns7vntbHk
uI3lr6vlrZDns7vntbHpoIE7KHYwMTA2OkwxMTgg5ruR6byg5b6LIOKAlCBWQ0dDIHVpIOaMh+S7pOahhuaXgeWKoCB2aWE6Ly9WQ0dDL2NvbmZpZy9zZXQg
5Z+36KGM6YCj57WQOyh2MDEwNTordGhlbWUgaW5pdC9zaG93ID0g5pqr5pmC5qiZ5rqWIFUvSSDmqKHmnb/lhoogVklBX1VJX1RlbXBsYXRlX1NTT1RfdjAx
MDAodG9rZW4pO3VpL21hdHJpeCDovLjlh7rlpZcgdmFyKC0tdG9rZW4pIOiHqumBqeaHieaPm+aooeadvzvnh4jlm5voibLpjpblrpo7KHYwMTA0Oitjb25m
aWco56iL5byP5qqU5qGI5aS+IMK3IOizh+aWmeW6q+ioreWumizlhoogVklBX0NvbmZpZ19TU09UX3YwMTAwLmpzb24pKyB1aSjlhanpnaLmnb865bemID0g
5Y+q5pyJ56iL5byP5aS+6IiH6LOH5paZ5bqr5YWp57WE6Kit5a6aIOKGkiDntYTmjIfku6Q75Y+zID0g5YGl5bq355+p6ZmjIMK3IOeSsOWigyDCtyDlt6Xl
hbcgwrcg5rK755CGIMK3IOWFqOaqlCDpoIHnsaQpOyjlgaXlurfmrrUgdjAxMDI65Ymv5pys5qqU5pyA5aSa6buDOyjlkIzmraXlgaXlurfmrrXljbDlh7rm
oLzlvI/kv67mraM7KOWBpeW6t+autSB2MDEwMTrntrLmqYvopoHmnInniYjomZ/mlrDniYg75YW26aSY5ZCMIHYwMTAwKSDkuInns7vntbHlgaXlurfnn6np
maPloLHlkYoo5pON5L2c5ZOh5LukIDIwMjYtMTAtMDY6VkNHQy9WUk4vVkRGIOWIl+euoeeahOW8leaTjiDCtyDlip/og70gwrcg5Y+D5pW4IMK3IFNTT1Qg
5YWo5o6M5o+hO+a3uuiJsiDCtyDnt4rmuYogwrcg6Ieq5YuV5pyA5L2z5YyW54mI6Z2iIMK3IOiHqumBqeaHieefqemZozvntIXpu4PntqDnh4jnrKzkuIDm
rIQ7CueUqOePvuacieW8leaTjiznnIEgdG9rZW4g5YWo5pmv5o6DOuacieeEoee3qOiZnyDCtyDmnInnhKHniYjmnKzomZ8gwrcg5pyJ54Sh6Ki75YaKIMK3
IOacieeEoeWKoOmAn+WZqCDCtyDmnInnhKHntrLot6/lt6Xlhbcgwrcg54mI5pys6Kqe5oSPIMK3IOato+W4uOmBi+S9nCDCtyDmoYjloLTliIbpoZ475ZCE
IHN5c3RlbSBtYW5hZ2VyIOiHqueuoeWQqyBsaWIv55Kw5aKDKeOAggogIG1hdHJpeCAgICAgICAgICAgIOKRoCDoh6rlt7EoVkNHQyA9IHN1cHBvcnRpdmUg
bW9kdWxlcynot5HlgaXlurfmrrUg4oaSIFZJQV9SZXBvcnRzL3ZjZ2MvSEVBTFRIX2xhdGVzdC5qc29uO+KRoSDoroAgVklBX1JlcG9ydHMvdnJufHZkZi9I
RUFMVEhfbGF0ZXN0Lmpzb24o5ZCE6IeqIG1hbmFnZXIgaGVhbHRoIOWLleipnuWvq+eahCzmr43ns7vntbHlj6roroApOwogICAgICAgICAgICAgICAgICAg
IOKRoiDkvbXml6LmnInlvJXmk47mnIDmlrDntZDmnpw6UEFOT1JBTUEoSzHigJNLOCnCtyBFTlZfTUFUUklYIMK3IFRPT0xLSVRfTUFUUklYIMK3IEdPVkVS
TiDCtyBWUk5fRXh0cmFjdF9MZWRnZXIgwrcgRklMRV9NQVRSSVgo5pyJ5bCx5L21LOaykuacieeBsCk74pGjIOWHuiBIRUFMVEhfTUFUUklYX2xhdGVzdC5o
dG1sLy5qc29uICsg5Y2hICsg6LK85Zue5YyFCiAgLS1zZWxmdGVzdCAgICAgICAgdGVtcCDmspnnm5IK5Y+q5a+rIFZJQV9SZXBvcnRzL3ZjZ2MvIMK3IFZJ
QV9SZXBvcnRzL3Jldmlldy92Y2djX2hlYWx0aC8gwrcgZG9jcy9oYW5kb2ZmL2FpL+OAguaymeebkumNtTpWSUFfUk9PVAoiIiIKZnJvbSBfX2Z1dHVyZV9f
IGltcG9ydCBhbm5vdGF0aW9ucwoKIyA9PT09PSBbVklBOkFDQ0VMLUJSSURHRTp2MDEwMF0gU3VwZXJBY2NlbCDliqDpgJ/lmajmqYso5om5MTAyIOWFqOao
ueWwjuWFpeS7pDtncmFjZWZ1bCDpm7booYzngrrorormm7QpID09PT09CnRyeToKICAgIGltcG9ydCBzeXMgYXMgX3NhX3N5cwogICAgZnJvbSBwYXRobGli
IGltcG9ydCBQYXRoIGFzIF9zYV9QYXRoCiAgICBfc2FfcCA9IF9zYV9QYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkKICAgIHdoaWxlIF9zYV9wLnBhcmVudCAh
PSBfc2FfcDoKICAgICAgICBpZiAoX3NhX3AgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIiAvICJWSUFfU3VwZXJBY2NlbF9Nb2R1bGUucHkiKS5leGlzdHMoKToK
ICAgICAgICAgICAgX3NhX3N5cy5wYXRoLmluc2VydCgwLCBzdHIoX3NhX3AgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIikpCiAgICAgICAgICAgIGJyZWFrCiAg
ICAgICAgX3NhX3AgPSBfc2FfcC5wYXJlbnQKICAgIGltcG9ydCBWSUFfU3VwZXJBY2NlbF9Nb2R1bGUgYXMgVklBX0FDQ0VMICAjIG5vcWE6IEY0MDEKZXhj
ZXB0IEltcG9ydEVycm9yOgogICAgVklBX0FDQ0VMID0gTm9uZQojID09PT09IFtWSUE6QUNDRUwtQlJJREdFOkVORF0gPT09PT0KCmltcG9ydCBkYXRldGlt
ZQppbXBvcnQgaHRtbAppbXBvcnQganNvbgppbXBvcnQgb3MKaW1wb3J0IHJlCmltcG9ydCBzaHV0aWwKaW1wb3J0IHN5cwppbXBvcnQgdGVtcGZpbGUKaW1w
b3J0IHRpbWUKZnJvbSBjb2xsZWN0aW9ucyBpbXBvcnQgQ291bnRlcgpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCk1FID0gUGF0aChfX2ZpbGVfXykucmVz
b2x2ZSgpCk5BTUUgPSBNRS5zdGVtClRBRyA9ICJ2MDEwNyIKTEFNUCA9IHsiR1JFRU4iOiAiIzE2YTM0YSIsICJZRUxMT1ciOiAiI2Y1OWUwYiIsICJSRUQi
OiAiI2RjMjYyNiIsICJHUkFZIjogIiM5Y2EzYWYifQpTVUJTID0gKCJWQ0dDIiwgIlZERiIsICJWUk4iKQoKIyA9PT09PSBbVklBOlNNLUhFQUxUSDp2MDEw
Ml0g5a2Q57O757Wx5YGl5bq35q61KHYwMTAyOuWJr+acrOaqlOacgOWkmum7gykodjAxMDE657ay5qmL6KaB44CM5pyJ54mI6Jmf55qE5paw54mI44CNU1VQ
X01ETDc0MF9OZXRVbmlmaWVkX3YjIyMjL3ZpYV9uZXRfdW5pZmllZF92IyMjIy9bVklBOk5FVC1CUklER0U6diMjIyNdO+eEoeeJiOiZn+iIiuapiz3pu4M7
57ay6Lev5bel5YW35pys6auU6IiH5Yqg6YCf5Zmo5pys6auU6LGB5YWNO+WJr+acrOaqlOWQjSAoMSkvX3NoYSDmqJkgRE9STUFOVCDlgJnpgbg75bCN5biz
5pS56Jmf6YCg5oiQ55qE54mI6Jmf5rSe5LiN55W26Kqe5oSP6YyvKSjlkIQgU3lzdGVtTWFuYWdlciDoh6rnrqHoh6rloLE65Yqf6IO955+p6ZmjIMK3IOih
qOmgreWGiiDCtyDnt6jomZ8gwrcg54mI5pys6Kqe5oSPIMK3IOWKoOmAn+WZqCDCtyDntrLmqYsgwrcgbGliL+eSsOWigyDCtyDmnIDov5Hoh6rmuKw75Y+q
6K6ALOWvq+iHquW3seeahCBIRUFMVEhfbGF0ZXN0Lmpzb24pPT09PT0KZGVmIF9obF92bnVtKG5hbWUpOgogICAgaW1wb3J0IHJlIGFzIF9yZQogICAgbSA9
IF9yZS5zZWFyY2gociJfdihcZHsyLDR9KVtBLVphLXowLTldKig/OlwuW0EtWmEtejAtOV0rKT8kIiwgbmFtZSkKICAgIHJldHVybiBpbnQobS5ncm91cCgx
KSkgaWYgbSBlbHNlIC0xCgoKZGVmIF9obF9yZWFkX2pzb24ocCk6CiAgICBpbXBvcnQganNvbiBhcyBfanNvbgogICAgdHJ5OgogICAgICAgIHJldHVybiBf
anNvbi5sb2FkcyhwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpCiAgICBleGNlcHQgRXhjZXB0aW9uOiAgIyBub3FhOiBCTEUwMDEKICAgICAg
ICByZXR1cm4gTm9uZQoKCmRlZiBfaGxfdGFpbChkLCBwYXQpOgogICAgaGl0cyA9IHNvcnRlZChkLmdsb2IocGF0KSwga2V5PWxhbWJkYSBxOiBfaGxfdm51
bShxLm5hbWUpKSBpZiBkLmlzX2RpcigpIGVsc2UgW10KICAgIHJldHVybiBoaXRzWy0xXSBpZiBoaXRzIGVsc2UgTm9uZQoKCmRlZiBzbV9oZWFsdGgoc3Vi
LCBob21lLCByb290LCBvdXRfZGlyLCBub3csIHJlcXVpcmVkX2xpYnM9KCksIG5ldF9yZXF1aXJlZD1GYWxzZSk6CiAgICAiIiLihpIgZGljdCjlgaXlurfn
n6npmaPnmoTlrZDns7vntbHmrrUp44CCaG9tZSA9IGZ1bmN0aW9uYWwgbW9kdWxlcy88U1VCPjtvdXRfZGlyID0gVklBX1JlcG9ydHMvPHN1Yj4v44CCIiIi
CiAgICBpbXBvcnQgaW1wb3J0bGliLnV0aWwgYXMgX2lsdQogICAgaW1wb3J0IHJlIGFzIF9yZQogICAgaW1wb3J0IHN5cyBhcyBfc3lzCiAgICBpbXBvcnQg
anNvbiBhcyBfanNvbgogICAgZnJvbSBjb2xsZWN0aW9ucyBpbXBvcnQgZGVmYXVsdGRpY3QgYXMgX2RkCiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgg
YXMgX1AKICAgIHJlZyA9IGhvbWUgLyAicmVnaXN0cnkiCiAgICBmbSA9IF9obF9yZWFkX2pzb24oX2hsX3RhaWwocmVnLCBzdWIgKyAiX0Z1bmN0aW9uTWF0
cml4X3YqLmpzb24iKSkgaWYgcmVnLmlzX2RpcigpIGVsc2UgTm9uZQogICAgdGggPSBfaGxfcmVhZF9qc29uKF9obF90YWlsKHJlZywgc3ViICsgIl9UYWJs
ZUhlYWRlcl92Ki5qc29uIikpIGlmIHJlZy5pc19kaXIoKSBlbHNlIE5vbmUKICAgIG5iID0ge30KICAgIGNlbnRyYWwgPSByb290IC8gInN1cHBvcnRpdmUg
bW9kdWxlcyIgLyAicmVnaXN0cnkiCiAgICBmb3IgcCBpbiAoY2VudHJhbCAvICJWSUFfTnVtYmVyQm9va3MiKS5nbG9iKCJWSUFfTnVtYmVyQm9va18qX3Yq
Lmpzb25sIikgaWYgKGNlbnRyYWwgLyAiVklBX051bWJlckJvb2tzIikuaXNfZGlyKCkgZWxzZSBbXToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGZvciBs
biBpbiBwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikuc3BsaXRsaW5lcygpOgogICAgICAgICAgICAgICAgciA9IF9qc29uLmxvYWRzKGxuKQog
ICAgICAgICAgICAgICAgaWYgci5nZXQoInNvdXJjZSIpIGFuZCByLmdldCgiY29kZSIpOgogICAgICAgICAgICAgICAgICAgIG5iW3JbInNvdXJjZSJdLnJl
cGxhY2UoIlxcIiwgIi8iKV0gPSByWyJjb2RlIl0KICAgICAgICBleGNlcHQgRXhjZXB0aW9uOiAgIyBub3FhOiBCTEUwMDEKICAgICAgICAgICAgcGFzcwog
ICAgcm4gPSBfaGxfcmVhZF9qc29uKGNlbnRyYWwgLyAiVklBX1JlZ2lzdHJ5TnVtYmVyc192MDEwMC5qc29uIikgaWYgKGNlbnRyYWwgLyAiVklBX1JlZ2lz
dHJ5TnVtYmVyc192MDEwMC5qc29uIikuZXhpc3RzKCkgZWxzZSBOb25lCiAgICBybl9rZXlzID0ge2VbImtleSJdOiBlWyJjb2RlIl0gZm9yIGUgaW4gKHJu
IG9yIHt9KS5nZXQoImVudHJpZXMiLCBbXSkgaWYgZS5nZXQoImtleSIpfQogICAgIyDmqpTmoYjliJc65q+P5pePKOWOu+eJiOiZnynkuIDliJcKICAgIGZh
bXMgPSBfZGQobGlzdCkKICAgIGZvciBwIGluIGhvbWUucmdsb2IoIioucHkiKToKICAgICAgICBpZiBzZXQocC5yZWxhdGl2ZV90byhob21lKS5wYXJ0c1s6
LTFdKSAmIHsicmVmZXJlbmNlcyIsICJpbnRha2UiLCAiX3N1cGVyc2VkZWQiLCAiX19weWNhY2hlX18iLCAiVklBX1JldGlyZWRFbmdpbmVzIiwgIl9xdWFy
YW50aW5lIn06CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZmFtc1socC5wYXJlbnQsIF9yZS5zdWIociJfdlxkezIsNH1bQS1aYS16MC05XSokIiwg
IiIsIHAuc3RlbSkpXS5hcHBlbmQocCkKICAgIHJvd3MgPSBbXQogICAgc2VtX2lzc3VlcyA9IDAKICAgIGNvbGxpc2lvbl9mYW1zID0gc2V0KCkKICAgIGNs
ID0gcm9vdCAvICJWSUFfUmVwb3J0cyIgLyAicmV2aWV3IiAvICJ2Y2djX2NvbGxpc2lvbiIgLyAiQ09MTElTSU9OX2xlZGdlci5qc29ubCIKICAgIGlmIGNs
LmV4aXN0cygpOgogICAgICAgIGZvciBsbiBpbiBjbC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04LXNpZyIsIGVycm9ycz0icmVwbGFjZSIpLnNwbGl0bGlu
ZXMoKToKICAgICAgICAgICAgbSA9IF9yZS5zZWFyY2gociIoW0EtWmEtejAtOV0rX1N5c3RlbU1hbmFnZXJ8Q0dDX01ETFxkezN9X1tBLVphLXowLTldKyki
LCBsbikKICAgICAgICAgICAgaWYgbToKICAgICAgICAgICAgICAgIGNvbGxpc2lvbl9mYW1zLmFkZChfcmUuc3ViKHIiX3ZcZHs0fSQiLCAiIiwgbS5ncm91
cCgxKSkpCiAgICBmb3IgKGQsIGZhbSksIHBzIGluIHNvcnRlZChmYW1zLml0ZW1zKCksIGtleT1sYW1iZGEgeDogKHN0cih4WzBdWzBdKSwgeFswXVsxXSkp
OgogICAgICAgIHBzLnNvcnQoa2V5PWxhbWJkYSBxOiAoX2hsX3ZudW0ocS5uYW1lKSwgcS5uYW1lKSkKICAgICAgICB0YWlsID0gcHNbLTFdCiAgICAgICAg
dmVycyA9IFtfaGxfdm51bShxLm5hbWUpIGZvciBxIGluIHBzIGlmIF9obF92bnVtKHEubmFtZSkgPj0gMF0KICAgICAgICB0cnk6CiAgICAgICAgICAgIHR4
dCA9IHRhaWwucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciLCBlcnJvcnM9InJlcGxhY2UiKQogICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAg
ICAgICB0eHQgPSAiIgogICAgICAgIGJvZHkgPSB0eHQuc3BsaXQoIlxuZGVmIHNlbGZ0ZXN0KCIpWzBdCiAgICAgICAgYWNjZWwgPSAiW1ZJQTpBQ0NFTC1C
UklER0UiIGluIHR4dCBvciAiVmVyaXRhc0NlbGVyaXRhc192MTE0MSIgaW4gdHh0CiAgICAgICAgbmV0X3VzZSA9IGJvb2woX3JlLnNlYXJjaChyIl5ccyoo
PzppbXBvcnR8ZnJvbSlccysocmVxdWVzdHN8aHR0cHh8YWlvaHR0cHx1cmxsaWJcLnJlcXVlc3R8eWZpbmFuY2V8YWtzaGFyZXxmcmVkYXBpfHBhbmRhc19k
YXRhcmVhZGVyKVxiIiwgYm9keSwgX3JlLk0pKSAgICMg6KaB55yf55qEIGltcG9ydCDmiY3nrpflh7rntrIo5q2j5YmH5a2X5Liy6KOh55qE5a2X5LiN566X
KQogICAgICAgIGlzX25ldF90b29sID0gYm9vbChfcmUuc2VhcmNoKHIiKD9pKU5ldFVuaWZpZWR8QWVnaXNOZXh1c3x2aWFfbmV0X3VuaWZpZWR8VklBX05l
dFN1cHBvcnR8dmlhX2FlZ2lzX25ldGNvcmV8XihyZXF1ZXN0fHByb3h5fGNvbGxlY3Rvcnx1cmxzfGdpdCkkIiwgZmFtKSkgb3IgIm5ldHdvcmsiIGluIGQu
cGFydHMgb3IgImFjY2VsZXJhdG9yIiBpbiBkLnBhcnRzIG9yIGZhbS5zdGFydHN3aXRoKCgiVmVyaXRhc0NlbGVyaXRhcyIsICJTVVBfTURMNzM3IiwgIlZJ
QV9TdXBlckFjY2VsIiwgInBpcF9zdWJwcm9jZXNzIikpCiAgICAgICAgbmV0X25ldyA9IGJvb2woX3JlLnNlYXJjaChyIlNVUF9NREw3NDBfTmV0VW5pZmll
ZF92XGR7NH18dmlhX25ldF91bmlmaWVkX3ZcZHs0fXxcW1ZJQTpORVQtQlJJREdFOnZcZHs0fVxdIiwgYm9keSkpCiAgICAgICAgbmV0X29sZCA9IChub3Qg
bmV0X25ldykgYW5kIGJvb2woX3JlLnNlYXJjaChyIlxbVklBOk5FVC1CUklER0V8VklBX05ldFN1cHBvcnRcYnx2aWFfbmV0X3VuaWZpZWRcYnxTVVBfTURM
NzQwIiwgYm9keSkpCiAgICAgICAgbmV0X29rID0gKG5vdCBuZXRfdXNlKSBvciBpc19uZXRfdG9vbCBvciBuZXRfbmV3IG9yIG5ldF9vbGQgICAgICAjIOiI
iuapi+S4jee0hSjpu4MpLOaykuapi+aJjee0hQogICAgICAgIG5ldF9ub3RlID0gIiIgaWYgKG5vdCBuZXRfdXNlIG9yIGlzX25ldF90b29sKSBlbHNlICgi
5paw54mI57ay5qmLIiBpZiBuZXRfbmV3IGVsc2UgKCLoiIrniYjntrLmqYso54Sh54mI6JmfKeKGkiDmlLnmjqUgU1VQX01ETDc0MF9OZXRVbmlmaWVkX3Yj
IyMjIiBpZiBuZXRfb2xkIGVsc2UgIueEoee2suapiyIpKQogICAgICAgIGp1bmsgPSBib29sKF9yZS5zZWFyY2gociJcc1woXGQrXCkkfF9zaGFbMC05YS1m
XXs4LH0kIiwgdGFpbC5zdGVtKSkgb3IgIiAoMSkiIGluIHRhaWwubmFtZQogICAgICAgIHNlbSA9IFtdCiAgICAgICAgaWYganVuazoKICAgICAgICAgICAg
c2VtLmFwcGVuZCgi5Ymv5pys5qqU5ZCNKCgxKS9fc2hhKeKGkiBET1JNQU5UIOWAmemBuCIpCiAgICAgICAgaWYgbGVuKHZlcnMpICE9IGxlbihzZXQodmVy
cykpOgogICAgICAgICAgICBzZW0uYXBwZW5kKCLlkIzniYjomZ/ph43opIciKQogICAgICAgIGlmIHZlcnMgYW5kIG1heCh2ZXJzKSAtIG1pbih2ZXJzKSAr
IDEgIT0gbGVuKHZlcnMpIGFuZCBsZW4odmVycykgPiAxOgogICAgICAgICAgICBzZW0uYXBwZW5kKCgi54mI6Jmf5rSePeWwjeW4s+aUueiZnyjlt7LoqJjl
uLMpIiBpZiBmYW0gaW4gY29sbGlzaW9uX2ZhbXMgZWxzZSAi54mI6Jmf5pyJ5rSeKCVk4oCTJWQg5YWxICVkKSIpICUgKChtaW4odmVycyksIG1heCh2ZXJz
KSwgbGVuKHZlcnMpKSBpZiBmYW0gbm90IGluIGNvbGxpc2lvbl9mYW1zIGVsc2UgKCkpKQogICAgICAgIGlmIF9obF92bnVtKHRhaWwubmFtZSkgPCAwIGFu
ZCBsZW4ocHMpID4gMToKICAgICAgICAgICAgc2VtLmFwcGVuZCgi5bC+54mI54Sh54mI6JmfIikKICAgICAgICBzZW1faXNzdWVzICs9IGJvb2woW3ggZm9y
IHggaW4gc2VtIGlmICLlt7LoqJjluLMiIG5vdCBpbiB4XSkKICAgICAgICByZWwgPSB0YWlsLnJlbGF0aXZlX3RvKHJvb3QpLmFzX3Bvc2l4KCkgaWYgc3Ry
KHRhaWwpLnN0YXJ0c3dpdGgoc3RyKHJvb3QpKSBlbHNlIHRhaWwuYXNfcG9zaXgoKQogICAgICAgIGtleV9tZGwgPSAiJXN8TURMfCVzfCVzIiAlIChzdWIs
IGZhbSwgKCJ2JTA0ZCIgJSBfaGxfdm51bSh0YWlsLm5hbWUpKSBpZiBfaGxfdm51bSh0YWlsLm5hbWUpID49IDAgZWxzZSAidjAwMDAiKQogICAgICAgIGtl
eV9lbmcgPSBrZXlfbWRsLnJlcGxhY2UoInxNREx8IiwgInxFTkd8IikKICAgICAgICBjb2RlID0gbmIuZ2V0KHJlbCkgb3Igcm5fa2V5cy5nZXQoa2V5X21k
bCkgb3Igcm5fa2V5cy5nZXQoa2V5X2VuZykgb3IgIiIKICAgICAgICByZWdpc3RlcmVkID0gYm9vbChmbSBhbmQgYW55KGsuc3BsaXQoInwiKVsxXSA9PSBm
YW0gZm9yIGsgaW4gKGZtLmdldCgiaXRlbXMiKSBvciB7fSkgaWYgay5zdGFydHN3aXRoKCgiTURMfCIsICJFTkd8IikpKSkKICAgICAgICB0cnk6CiAgICAg
ICAgICAgIGltcG9ydCBhc3QgYXMgX2FzdAogICAgICAgICAgICBfYXN0LnBhcnNlKHR4dCkKICAgICAgICAgICAgYXN0X29rID0gVHJ1ZQogICAgICAgIGV4
Y2VwdCBFeGNlcHRpb246ICAjIG5vcWE6IEJMRTAwMQogICAgICAgICAgICBhc3Rfb2sgPSBGYWxzZQogICAgICAgIGxhbXAgPSAiUkVEIiBpZiAoKG5vdCBh
c3Rfb2sgb3Igbm90IG5ldF9vaykgYW5kIG5vdCBqdW5rKSBlbHNlICgiWUVMTE9XIiBpZiAoanVuayBvciBub3QgYWNjZWwgb3Igbm90IGNvZGUgb3Igbm90
IHJlZ2lzdGVyZWQgb3IgbmV0X29sZCBvciBbeCBmb3IgeCBpbiBzZW0gaWYgIuW3suiomOW4syIgbm90IGluIHhdKSBlbHNlICJHUkVFTiIpICAgIyDlia/m
nKzmqpQoanVuaynmnIDlpJrpu4M65a6D55qE5q245a6/5pivIGRvcm1hbnQs5LiN5piv5L+uCiAgICAgICAgcm93cy5hcHBlbmQoeyJmYW1pbHkiOiBmYW0s
ICJkaXIiOiBkLnJlbGF0aXZlX3RvKGhvbWUpLmFzX3Bvc2l4KCkgaWYgc3RyKGQpLnN0YXJ0c3dpdGgoc3RyKGhvbWUpKSBlbHNlIHN0cihkKSwgInRhaWwi
OiB0YWlsLm5hbWUsICJ2ZXJzaW9uIjogKCJ2JTA0ZCIgJSBfaGxfdm51bSh0YWlsLm5hbWUpKSBpZiBfaGxfdm51bSh0YWlsLm5hbWUpID49IDAgZWxzZSAi
4oCUIiwgIm5fdmVyc2lvbnMiOiBsZW4ocHMpLAogICAgICAgICAgICAgICAgICAgICAibnVtYmVyIjogY29kZSwgInJlZ2lzdGVyZWQiOiByZWdpc3RlcmVk
LCAiYWNjZWwiOiBhY2NlbCwgIm5ldF91c2UiOiBuZXRfdXNlLCAibmV0X29rIjogbmV0X29rLCAibmV0X25vdGUiOiBuZXRfbm90ZSwgIm5ldF90b29sIjog
aXNfbmV0X3Rvb2wsICJhc3Rfb2siOiBhc3Rfb2ssICJzZW1hbnRpYyI6ICI7Ii5qb2luKHNlbSksICJsYW1wIjogbGFtcH0pCiAgICAjIOWGiiAvIOihqOmg
rSAvIOWtl+WFuAogICAgYm9va3MgPSBbXQogICAgZm9yIHNkIGluICgiU1NPVCIsICJyZWdpc3RyeSIsICJrbm93bGVkZ2UiKToKICAgICAgICBkID0gaG9t
ZSAvIHNkCiAgICAgICAgaWYgZC5pc19kaXIoKToKICAgICAgICAgICAgc2VlbiA9IHt9CiAgICAgICAgICAgIGZvciBwIGluIGQuZ2xvYigiKi5qc29uIik6
CiAgICAgICAgICAgICAgICBmYW0gPSBfcmUuc3ViKHIiX3ZcZHsyLDR9W0EtWmEtejAtOV0qJCIsICIiLCBwLnN0ZW0pCiAgICAgICAgICAgICAgICBpZiBm
YW0gbm90IGluIHNlZW4gb3IgX2hsX3ZudW0ocC5uYW1lKSA+IF9obF92bnVtKHNlZW5bZmFtXS5uYW1lKToKICAgICAgICAgICAgICAgICAgICBzZWVuW2Zh
bV0gPSBwCiAgICAgICAgICAgIGZvciBmYW0sIHAgaW4gc2Vlbi5pdGVtcygpOgogICAgICAgICAgICAgICAgdGlkID0gX3JlLnN1YihyIlteYS16MC05X10r
IiwgIl8iLCBmYW0ubG93ZXIoKSkuc3RyaXAoIl8iKQogICAgICAgICAgICAgICAgZW50ID0gKHRoIG9yIHt9KS5nZXQoInRhYmxlcyIsIHt9KSBpZiB0aCBl
bHNlIHt9CiAgICAgICAgICAgICAgICByZWdfdCA9IGFueShrID09IHRpZCBvciBrLnN0YXJ0c3dpdGgodGlkICsgIl8iKSBmb3IgayBpbiBlbnQpCiAgICAg
ICAgICAgICAgICBudW1fdCA9IGFueSgoayA9PSB0aWQgb3Igay5zdGFydHN3aXRoKHRpZCArICJfIikpIGFuZCB2LmdldCgidGFibGVfbm8iKSBmb3Igaywg
diBpbiBlbnQuaXRlbXMoKSkKICAgICAgICAgICAgICAgIGJvb2tzLmFwcGVuZCh7ImJvb2siOiBwLm5hbWUsICJkaXIiOiBzZCwgInJlZ2lzdGVyZWQiOiBy
ZWdfdCwgIm51bWJlcmVkIjogbnVtX3QsICJsYW1wIjogIkdSRUVOIiBpZiBudW1fdCBlbHNlICgiWUVMTE9XIiBpZiByZWdfdCBlbHNlICJHUkFZIil9KQog
ICAgIyBsaWIgLyDnkrDlooMo5pys55u06K2v5ZmoKQogICAgbGlicyA9IFtdCiAgICBmb3IgbmFtZSBpbiByZXF1aXJlZF9saWJzOgogICAgICAgIG9rID0g
X2lsdS5maW5kX3NwZWMobmFtZSkgaXMgbm90IE5vbmUKICAgICAgICBsaWJzLmFwcGVuZCh7ImxpYiI6IG5hbWUsICJpbXBvcnRhYmxlIjogb2ssICJsYW1w
IjogIkdSRUVOIiBpZiBvayBlbHNlICJSRUQifSkKICAgICMg5pyA6L+R6Ieq5risIC8g57WQ5p6cCiAgICByZXN1bHRzID0gW10KICAgIGlmIG91dF9kaXIu
aXNfZGlyKCk6CiAgICAgICAgZm9yIHAgaW4gc29ydGVkKG91dF9kaXIuZ2xvYigiUkVTVUxUXypfbGF0ZXN0Lmpzb24iKSlbOjQwXToKICAgICAgICAgICAg
aW1wb3J0IGRhdGV0aW1lIGFzIF9kdCwgdGltZSBhcyBfdGltZQogICAgICAgICAgICBhZ2UgPSAoX3RpbWUudGltZSgpIC0gcC5zdGF0KCkuc3RfbXRpbWUp
IC8gODY0MDAKICAgICAgICAgICAgcmVzdWx0cy5hcHBlbmQoeyJyZXN1bHQiOiBwLm5hbWUsICJhZ2VfZGF5cyI6IHJvdW5kKGFnZSwgMSksICJsYW1wIjog
IkdSRUVOIiBpZiBhZ2UgPD0gNyBlbHNlICJZRUxMT1cifSkKICAgIGZtX2l0ZW1zID0gKGZtIG9yIHt9KS5nZXQoIml0ZW1zIiwge30pIGlmIGZtIGVsc2Ug
e30KICAgIHN1bW1hcnkgPSB7ImZpbGVzIjogbGVuKHJvd3MpLCAicmVkIjogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJsYW1wIl0gPT0gIlJFRCIpLCAi
eWVsbG93Ijogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJsYW1wIl0gPT0gIllFTExPVyIpLCAiZ3JlZW4iOiBzdW0oMSBmb3IgciBpbiByb3dzIGlmIHJb
ImxhbXAiXSA9PSAiR1JFRU4iKSwKICAgICAgICAgICAgICAgIm51bWJlcmVkIjogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJudW1iZXIiXSksICJyZWdp
c3RlcmVkIjogc3VtKDEgZm9yIHIgaW4gcm93cyBpZiByWyJyZWdpc3RlcmVkIl0pLCAiYWNjZWwiOiBzdW0oMSBmb3IgciBpbiByb3dzIGlmIHJbImFjY2Vs
Il0pLCAibmV0X2JhZCI6IHN1bSgxIGZvciByIGluIHJvd3MgaWYgbm90IHJbIm5ldF9vayJdKSwgIm5ldF9vbGQiOiBzdW0oMSBmb3IgciBpbiByb3dzIGlm
IHJbIm5ldF9ub3RlIl0uc3RhcnRzd2l0aCgi6IiK54mIIikpLCAic2VtYW50aWNfaXNzdWVzIjogc2VtX2lzc3VlcywKICAgICAgICAgICAgICAgImZuX2l0
ZW1zIjogbGVuKGZtX2l0ZW1zKSwgImZuX251bWJlcmVkIjogc3VtKDEgZm9yIGUgaW4gZm1faXRlbXMudmFsdWVzKCkgaWYgZS5nZXQoIm51bWJlciIpKSwg
InRhYmxlcyI6IGxlbigodGggb3Ige30pLmdldCgidGFibGVzIiwge30pIGlmIHRoIGVsc2Uge30pLCAidGFibGVzX251bWJlcmVkIjogc3VtKDEgZm9yIHYg
aW4gKCh0aCBvciB7fSkuZ2V0KCJ0YWJsZXMiLCB7fSkgaWYgdGggZWxzZSB7fSkudmFsdWVzKCkgaWYgdi5nZXQoInRhYmxlX25vIikpLAogICAgICAgICAg
ICAgICAiYm9va3MiOiBsZW4oYm9va3MpLCAibGlic19taXNzaW5nIjogc3VtKDEgZm9yIGwgaW4gbGlicyBpZiBub3QgbFsiaW1wb3J0YWJsZSJdKSwgInB5
dGhvbiI6IF9zeXMuZXhlY3V0YWJsZX0KICAgIGxhbXAgPSAiUkVEIiBpZiAoc3VtbWFyeVsicmVkIl0gb3Igc3VtbWFyeVsibGlic19taXNzaW5nIl0pIGVs
c2UgKCJZRUxMT1ciIGlmIChzdW1tYXJ5WyJ5ZWxsb3ciXSBvciBub3QgZm0gb3Igbm90IHRoKSBlbHNlICJHUkVFTiIpCiAgICBoZWFsdGggPSB7InN1YiI6
IHN1YiwgInRzIjogbm93LCAicHl0aG9uIjogX3N5cy5leGVjdXRhYmxlLCAibGFtcCI6IGxhbXAsICJzdW1tYXJ5Ijogc3VtbWFyeSwgImZpbGVzIjogcm93
cywgImJvb2tzIjogYm9va3MsICJsaWJzIjogbGlicywgInJlc3VsdHMiOiByZXN1bHRzLAogICAgICAgICAgICAgICJmbl9tYXRyaXgiOiAoX2hsX3RhaWwo
cmVnLCBzdWIgKyAiX0Z1bmN0aW9uTWF0cml4X3YqLmpzb24iKS5uYW1lIGlmIGZtIGVsc2UgTm9uZSksICJ0YWJsZV9oZWFkZXIiOiAoX2hsX3RhaWwocmVn
LCBzdWIgKyAiX1RhYmxlSGVhZGVyX3YqLmpzb24iKS5uYW1lIGlmIHRoIGVsc2UgTm9uZSl9CiAgICBvdXRfZGlyLm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhp
c3Rfb2s9VHJ1ZSkKICAgIChvdXRfZGlyIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIpLndyaXRlX3RleHQoX2pzb24uZHVtcHMoaGVhbHRoLCBlbnN1cmVfYXNj
aWk9RmFsc2UsIGluZGVudD0xKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIHJldHVybiBoZWFsdGgKCgpkZWYgc21faGVhbHRoX3ByaW50KGgpOgogICAgcyA9
IGhbInN1bW1hcnkiXQogICAgcHJpbnQoIlvoqIhdICVzIGhlYWx0aCDCtyDmqpTml48gJWQo57SFICVkIOm7gyAlZCDntqAgJWQpwrcg5pyJ6JmfICVkIMK3
IOW3sueZu+iomCAlZCDCtyDmnInmqYsgJWQgwrcg57ay5qmL57y6ICVkIOiIiuapiyAlZCDCtyDniYjomZ/oqp7mhI8gJWQgwrcg5YqfICVkLyVkIOacieiZ
nyDCtyDooaggJWQvJWQg5pyJ6JmfIMK3IOWGiiAlZCDCtyBsaWIg57y6ICVkIMK3ICVzIiAlICgKICAgICAgICBoWyJzdWIiXSwgc1siZmlsZXMiXSwgc1si
cmVkIl0sIHNbInllbGxvdyJdLCBzWyJncmVlbiJdLCBzWyJudW1iZXJlZCJdLCBzWyJyZWdpc3RlcmVkIl0sIHNbImFjY2VsIl0sIHNbIm5ldF9iYWQiXSwg
c1sibmV0X29sZCJdLCBzWyJzZW1hbnRpY19pc3N1ZXMiXSwgc1siZm5fbnVtYmVyZWQiXSwgc1siZm5faXRlbXMiXSwgc1sidGFibGVzX251bWJlcmVkIl0s
IHNbInRhYmxlcyJdLCBzWyJib29rcyJdLCBzWyJsaWJzX21pc3NpbmciXSwgaFsibGFtcCJdKSkKICAgIGZvciByIGluIFt4IGZvciB4IGluIGhbImZpbGVz
Il0gaWYgeFsibGFtcCJdID09ICJSRUQiXVs6MTBdOgogICAgICAgIHByaW50KCIgIFtSRURdICVzICVzIMK3ICVzIiAlIChoWyJzdWIiXSwgclsidGFpbCJd
LCAiQVNUIOWjniIgaWYgbm90IHJbImFzdF9vayJdIGVsc2UgclsibmV0X25vdGUiXSkpCiAgICBmb3IgciBpbiBbeCBmb3IgeCBpbiBoWyJmaWxlcyJdIGlm
IHhbIm5ldF9ub3RlIl0uc3RhcnRzd2l0aCgi6IiK54mIIildWzoxMF06CiAgICAgICAgcHJpbnQoIiAgW1lFTF0gJXMgJXMgwrcgJXMiICUgKGhbInN1YiJd
LCByWyJ0YWlsIl0sIHJbIm5ldF9ub3RlIl0pKQogICAgZm9yIGwgaW4gW3ggZm9yIHggaW4gaFsibGlicyJdIGlmIG5vdCB4WyJpbXBvcnRhYmxlIl1dOgog
ICAgICAgIHByaW50KCIgIFtSRURdICVzIGxpYiDnvLogJXMo5pys55u06K2v5ZmoICVzKSIgJSAoaFsic3ViIl0sIGxbImxpYiJdLCBoWyJweXRob24iXSkp
CiMgPT09PT0gW1ZJQTpTTS1IRUFMVEg6RU5EXSA9PT09PQoKCmRlZiBfbm93KCkgLT4gc3RyOgogICAgcmV0dXJuIGRhdGV0aW1lLmRhdGV0aW1lLm5vdygp
Lmlzb2Zvcm1hdCh0aW1lc3BlYz0ic2Vjb25kcyIpCgoKZGVmIF9yb290KCkgLT4gUGF0aDoKICAgIGlmIG9zLmVudmlyb24uZ2V0KCJWSUFfUk9PVCIpOgog
ICAgICAgIHJldHVybiBQYXRoKG9zLmVudmlyb25bIlZJQV9ST09UIl0pCiAgICBwID0gTUUKICAgIHdoaWxlIHAucGFyZW50ICE9IHA6CiAgICAgICAgaWYg
KHAgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIikuaXNfZGlyKCkgYW5kIChwIC8gImZ1bmN0aW9uYWwgbW9kdWxlcyIpLmlzX2RpcigpOgogICAgICAgICAgICBy
ZXR1cm4gcAogICAgICAgIHAgPSBwLnBhcmVudAogICAgcmV0dXJuIE1FLnBhcmVudHNbMl0KCgpkZWYgX3BhdGhzKCkgLT4gZGljdDoKICAgIHIgPSBfcm9v
dCgpCiAgICByZXR1cm4geyJyb290IjogciwgInN1cCI6IHIgLyAic3VwcG9ydGl2ZSBtb2R1bGVzIiwgInJlZ2lzdHJ5IjogciAvICJzdXBwb3J0aXZlIG1v
ZHVsZXMiIC8gInJlZ2lzdHJ5IiwgInJlcG9ydHMiOiByIC8gIlZJQV9SZXBvcnRzIiwgInJldmlldyI6IHIgLyAiVklBX1JlcG9ydHMiIC8gInJldmlldyIs
CiAgICAgICAgICAgICJvdXQiOiByIC8gIlZJQV9SZXBvcnRzIiAvICJyZXZpZXciIC8gInZjZ2NfaGVhbHRoIiwgImNhcmRzIjogciAvICJkb2NzIiAvICJo
YW5kb2ZmIiAvICJhaSJ9CgoKZGVmIF9sYXRlc3QoUDogZGljdCwgcmVsOiBzdHIpOgogICAgcCA9IFBbInJldmlldyJdIC8gcmVsCiAgICByZXR1cm4gX2hs
X3JlYWRfanNvbihwKSBpZiBwLmV4aXN0cygpIGVsc2UgTm9uZQoKCmRlZiBfcGFub19jaGVja3MocGFubykgLT4gZGljdDoKICAgICIiIlBBTk9SQU1BX2xh
dGVzdC5qc29uIOWFqeeoruW9oueLgOmDveaUtjpjaGVja3MgPSBbe2ssbGFtcCwuLi59XSjlhajmma/lvJXmk44p5oiWIHtLMTogbGFtcH0o5pGY6KaBKeOA
giIiIgogICAgYyA9IChwYW5vIG9yIHt9KS5nZXQoImNoZWNrcyIpCiAgICBpZiBpc2luc3RhbmNlKGMsIGxpc3QpOgogICAgICAgIHJldHVybiB7ay5nZXQo
ImsiKTogay5nZXQoImxhbXAiKSBmb3IgayBpbiBjIGlmIGlzaW5zdGFuY2UoaywgZGljdCl9CiAgICByZXR1cm4gYyBpZiBpc2luc3RhbmNlKGMsIGRpY3Qp
IGVsc2Uge30KCgpkZWYgbWF0cml4KFA6IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdDoKICAgIFAgPSBQIG9yIF9wYXRocygpCiAgICB0MCA9IHRpbWUu
dGltZSgpCiAgICBub3cgPSBfbm93KCkKICAgIHZjZ2MgPSBzbV9oZWFsdGgoIlZDR0MiLCBQWyJzdXAiXSwgUFsicm9vdCJdLCBQWyJyZXBvcnRzIl0gLyAi
dmNnYyIsIG5vdywgKCJwYW5kYXMiLCkpCiAgICBzdWJzID0geyJWQ0dDIjogdmNnY30KICAgIGZvciBzIGluICgiVkRGIiwgIlZSTiIpOgogICAgICAgIGgg
PSBfaGxfcmVhZF9qc29uKFBbInJlcG9ydHMiXSAvIHMubG93ZXIoKSAvICJIRUFMVEhfbGF0ZXN0Lmpzb24iKSBpZiAoUFsicmVwb3J0cyJdIC8gcy5sb3dl
cigpIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIpLmV4aXN0cygpIGVsc2UgTm9uZQogICAgICAgIHN1YnNbc10gPSBoCiAgICBwYW5vID0gX2xhdGVzdChQLCAi
dmNnY19wYW5vcmFtYS9QQU5PUkFNQV9sYXRlc3QuanNvbiIpCiAgICBlbnYgPSBfbGF0ZXN0KFAsICJ2Y2djX2Vudi9FTlZfTUFUUklYX2xhdGVzdC5qc29u
IikKICAgIHRvb2wgPSBfbGF0ZXN0KFAsICJ2Y2djX3Rvb2xraXQvVE9PTEtJVF9NQVRSSVhfbGF0ZXN0Lmpzb24iKQogICAgZ292ID0gX2xhdGVzdChQLCAi
dmNnY19yZWdpc3RyeS9HT1ZFUk5fbGF0ZXN0Lmpzb24iKQogICAgZm0gPSBfbGF0ZXN0KFAsICJ2Y2djX21hdHJpeC9GSUxFX01BVFJJWF9sYXRlc3QuanNv
biIpCiAgICBsZWRnZXIgPSBQWyJyZXBvcnRzIl0gLyAidnJuIiAvICJleHRyYWN0IiAvICJWUk5fRXh0cmFjdF9MZWRnZXIuanNvbmwiCiAgICBleHQgPSBD
b3VudGVyKCkKICAgIGlmIGxlZGdlci5leGlzdHMoKToKICAgICAgICBsYXN0ID0ge30KICAgICAgICBmb3IgbG4gaW4gbGVkZ2VyLnJlYWRfdGV4dChlbmNv
ZGluZz0idXRmLTgiKS5zcGxpdGxpbmVzKCk6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIHIgPSBqc29uLmxvYWRzKGxuKQogICAgICAgICAg
ICAgICAgbGFzdFtyLmdldCgiZmlsZSIpXSA9IHIuZ2V0KCJzdGF0dXMiKQogICAgICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgICAg
IHBhc3MKICAgICAgICBleHQgPSBDb3VudGVyKGxhc3QudmFsdWVzKCkpCiAgICBzZWN0aW9ucyA9IHsKICAgICAgICAicGFub3JhbWEiOiB7ImxhbXAiOiAo
cGFubyBvciB7fSkuZ2V0KCJsYW1wIiwgIkdSQVkiKSwgImNoZWNrcyI6IF9wYW5vX2NoZWNrcyhwYW5vKSwgInRzIjogKHBhbm8gb3Ige30pLmdldCgidHMi
KX0sCiAgICAgICAgImVudiI6IHsibGFtcCI6IChlbnYgb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJlbnZzIjogbGVuKChlbnYgb3Ige30pLmdldCgi
ZW52cyIsIFtdKSksICJwZGZfdG9vbHMiOiAoZW52IG9yIHt9KS5nZXQoInBkZl90b29sc19vayIpLCAidHMiOiAoZW52IG9yIHt9KS5nZXQoInRzIil9LAog
ICAgICAgICJ0b29sa2l0IjogeyJsYW1wIjogKHRvb2wgb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJmYW1pbGllcyI6IGxlbigodG9vbCBvciB7fSku
Z2V0KCJyb3dzIiwgW10pKSwgIm92ZXJsYXBzIjogbGVuKCh0b29sIG9yIHt9KS5nZXQoIm92ZXJsYXBzIiwgW10pKSwgInRzIjogKHRvb2wgb3Ige30pLmdl
dCgidHMiKX0sCiAgICAgICAgImdvdmVybiI6IHsibGFtcCI6IChnb3Ygb3Ige30pLmdldCgibGFtcCIsICJHUkFZIiksICJzdW1tYXJ5IjogKGdvdiBvciB7
fSkuZ2V0KCJzdW1tYXJ5IiksICJ0cyI6IChnb3Ygb3Ige30pLmdldCgidHMiKX0sCiAgICAgICAgImZpbGVtYXRyaXgiOiB7ImxhbXAiOiAoZm0gb3Ige30p
LmdldCgibGFtcCIsICJHUkFZIiksICJwZXIiOiAoZm0gb3Ige30pLmdldCgicGVyIiksICJ0cyI6IChmbSBvciB7fSkuZ2V0KCJ0cyIpfSwKICAgICAgICAi
ZXh0cmFjdCI6IHsibGFtcCI6ICgiR1JFRU4iIGlmIGV4dCBhbmQgbm90IGV4dC5nZXQoIlJFVklFVyIpIGFuZCBub3QgZXh0LmdldCgiRVJST1IiKSBlbHNl
ICgiWUVMTE9XIiBpZiBleHQgZWxzZSAiR1JBWSIpKSwgImNvdW50cyI6IGRpY3QoZXh0KX0sCiAgICB9CiAgICBvcmRlciA9IHsiUkVEIjogMywgIllFTExP
VyI6IDIsICJHUkVFTiI6IDEsICJHUkFZIjogMH0KICAgIGxhbXBzID0gW2hbImxhbXAiXSBmb3IgaCBpbiBzdWJzLnZhbHVlcygpIGlmIGhdICsgW3ZbImxh
bXAiXSBmb3IgdiBpbiBzZWN0aW9ucy52YWx1ZXMoKV0KICAgIGxhbXAgPSBtYXgobGFtcHMsIGtleT1sYW1iZGEgeDogb3JkZXJbeF0pIGlmIGxhbXBzIGVs
c2UgIkdSQVkiCiAgICByZXR1cm4geyJ2ZXJiIjogIm1hdHJpeCIsICJlbmdpbmUiOiBOQU1FLCAidHMiOiBub3csICJyb290Ijogc3RyKFBbInJvb3QiXSks
ICJsYW1wIjogbGFtcCwgInN1YnMiOiBzdWJzLCAic2VjdGlvbnMiOiBzZWN0aW9ucywgInNlY3MiOiByb3VuZCh0aW1lLnRpbWUoKSAtIHQwLCAxKX0KCgpk
ZWYgX2h0bWwocmVzOiBkaWN0KSAtPiBzdHI6CiAgICBkZWYgbGFtcChsKToKICAgICAgICByZXR1cm4gIjxpIGNsYXNzPSdscCAlcycgc3R5bGU9J2JhY2tn
cm91bmQ6JXMnPjwvaT4iICUgKGwsIExBTVAuZ2V0KGwsIExBTVBbIkdSQVkiXSkpCiAgICBjYXJkcyA9IFtdCiAgICBmb3IgcyBpbiBTVUJTOgogICAgICAg
IGggPSByZXNbInN1YnMiXS5nZXQocykKICAgICAgICBpZiBub3QgaDoKICAgICAgICAgICAgY2FyZHMuYXBwZW5kKCI8ZGl2IGNsYXNzPSdjYXJkJz48ZGl2
IGNsYXNzPSdoZCc+JXMlczwvZGl2PjxkaXYgY2xhc3M9J2t2Jz7lsJrmnKrot5EgPGNvZGU+JXNfU3lzdGVtTWFuYWdlciBoZWFsdGg8L2NvZGU+PC9kaXY+
PC9kaXY+IiAlIChsYW1wKCJHUkFZIiksIHMsIHMpKQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIG0gPSBoWyJzdW1tYXJ5Il0KICAgICAgICBjYXJk
cy5hcHBlbmQoIjxkaXYgY2xhc3M9J2NhcmQnPjxkaXYgY2xhc3M9J2hkJz4lcyVzIDxzbWFsbD4lczwvc21hbGw+PC9kaXY+PGRpdiBjbGFzcz0na3YnPuaq
lOaXjyA8Yj4lZDwvYj4g57SFICVkIOm7gyAlZCDntqAgJWQgwrcg5pyJ6JmfICVkIMK3IOeZu+iomCAlZCDCtyDmqYsgJWQgwrcg57ay5qmL57y6ICVkIMK3
IOiqnuaEjyAlZDwvZGl2PjxkaXYgY2xhc3M9J2t2Jz7lip8gJWQvJWQg5pyJ6JmfIMK3IOihqCAlZC8lZCDmnInomZ8gwrcg5YaKICVkIMK3IGxpYiDnvLog
JWQ8L2Rpdj48ZGl2IGNsYXNzPSdrdic+PHNtYWxsPiVzPC9zbWFsbD48L2Rpdj48L2Rpdj4iCiAgICAgICAgICAgICAgICAgICAgICUgKGxhbXAoaFsibGFt
cCJdKSwgcywgaFsidHMiXSwgbVsiZmlsZXMiXSwgbVsicmVkIl0sIG1bInllbGxvdyJdLCBtWyJncmVlbiJdLCBtWyJudW1iZXJlZCJdLCBtWyJyZWdpc3Rl
cmVkIl0sIG1bImFjY2VsIl0sIG1bIm5ldF9iYWQiXSwgbVsic2VtYW50aWNfaXNzdWVzIl0sIG1bImZuX251bWJlcmVkIl0sIG1bImZuX2l0ZW1zIl0sIG1b
InRhYmxlc19udW1iZXJlZCJdLCBtWyJ0YWJsZXMiXSwgbVsiYm9va3MiXSwgbVsibGlic19taXNzaW5nIl0sIGh0bWwuZXNjYXBlKG0uZ2V0KCJweXRob24i
LCAiIikpKSkKICAgIHNlYyA9IHJlc1sic2VjdGlvbnMiXQogICAgY2hpcHMgPSBbKCLlhajmma8gSzHigJNLOCIsIHNlY1sicGFub3JhbWEiXVsibGFtcCJd
LCAiICIuam9pbigiJXM9JXMiICUga3YgZm9yIGt2IGluIHNlY1sicGFub3JhbWEiXVsiY2hlY2tzIl0uaXRlbXMoKSkgb3IgIuacqui3kSIpLAogICAgICAg
ICAgICAgKCLnkrDlooPlt6XlhbciLCBzZWNbImVudiJdWyJsYW1wIl0sICLnkrDlooMgJXMgwrcgUERGIOmalOmboiAlcyIgJSAoc2VjWyJlbnYiXVsiZW52
cyJdLCBzZWNbImVudiJdWyJwZGZfdG9vbHMiXSkpLAogICAgICAgICAgICAgKCLovJTliqnlt6XlhbciLCBzZWNbInRvb2xraXQiXVsibGFtcCJdLCAi5peP
ICVzIMK3IOmHjeeWiiAlcyIgJSAoc2VjWyJ0b29sa2l0Il1bImZhbWlsaWVzIl0sIHNlY1sidG9vbGtpdCJdWyJvdmVybGFwcyJdKSksCiAgICAgICAgICAg
ICAoIuayu+eQhueZvOiZnyIsIHNlY1siZ292ZXJuIl1bImxhbXAiXSwganNvbi5kdW1wcyhzZWNbImdvdmVybiJdWyJzdW1tYXJ5Il0sIGVuc3VyZV9hc2Np
aT1GYWxzZSlbOjEyMF0gaWYgc2VjWyJnb3Zlcm4iXVsic3VtbWFyeSJdIGVsc2UgIuacqui3kSIpLAogICAgICAgICAgICAgKCLlhajmqpTnn6npmaMiLCBz
ZWNbImZpbGVtYXRyaXgiXVsibGFtcCJdLCBqc29uLmR1bXBzKHNlY1siZmlsZW1hdHJpeCJdWyJwZXIiXSwgZW5zdXJlX2FzY2lpPUZhbHNlKVs6MTIwXSBp
ZiBzZWNbImZpbGVtYXRyaXgiXVsicGVyIl0gZWxzZSAi5pyq6LeRIiksCiAgICAgICAgICAgICAoIlZSTiDmk7flj5YiLCBzZWNbImV4dHJhY3QiXVsibGFt
cCJdLCBqc29uLmR1bXBzKHNlY1siZXh0cmFjdCJdWyJjb3VudHMiXSwgZW5zdXJlX2FzY2lpPUZhbHNlKSBvciAi5pyq6LeRIildCiAgICBjaGlwX2h0bWwg
PSAiIi5qb2luKCI8ZGl2IGNsYXNzPSdjaGlwJz4lczxiPiVzPC9iPjxzcGFuPiVzPC9zcGFuPjwvZGl2PiIgJSAobGFtcChsKSwgdCwgaHRtbC5lc2NhcGUo
ZCkpIGZvciB0LCBsLCBkIGluIGNoaXBzKQogICAgcm93cyA9IFtdCiAgICBmb3IgcyBpbiBTVUJTOgogICAgICAgIGggPSByZXNbInN1YnMiXS5nZXQocykK
ICAgICAgICBmb3IgciBpbiAoaCBvciB7fSkuZ2V0KCJmaWxlcyIsIFtdKToKICAgICAgICAgICAgcm93cy5hcHBlbmQoIjx0ciBkYXRhLXM9JyVzJyBkYXRh
LWw9JyVzJz48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPGRpdiBjbGFzcz0nZGltJz4lczwvZGl2PjwvdGQ+PHRkPiVzPC90ZD48dGQgY2xhc3M9J24n
PiVkPC90ZD48dGQgY2xhc3M9J2NvZGUnPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZCBjbGFzcz0nZGlt
Jz4lczwvdGQ+PC90cj4iCiAgICAgICAgICAgICAgICAgICAgICAgICUgKHMsIHJbImxhbXAiXSwgbGFtcChyWyJsYW1wIl0pLCBzLCBodG1sLmVzY2FwZShy
WyJmYW1pbHkiXSksIGh0bWwuZXNjYXBlKHJbImRpciJdKSwgclsidmVyc2lvbiJdLCByWyJuX3ZlcnNpb25zIl0sIGh0bWwuZXNjYXBlKHJbIm51bWJlciJd
IG9yICLigJQiKSwgIuKckyIgaWYgclsicmVnaXN0ZXJlZCJdIGVsc2UgIuKAlCIsICLinJMiIGlmIHJbImFjY2VsIl0gZWxzZSAiPGIgY2xhc3M9J3InPue8
ujwvYj4iLAogICAgICAgICAgICAgICAgICAgICAgICAgICAoKCLinJMiIGlmIG5vdCByWyJuZXRfbm90ZSJdLnN0YXJ0c3dpdGgoIuiIiueJiCIpIGVsc2Ug
IjxiIHN0eWxlPSdjb2xvcjojZjU5ZTBiJz7oiIo8L2I+IikgaWYgclsibmV0X29rIl0gZWxzZSAiPGIgY2xhc3M9J3InPue8ujwvYj4iKSBpZiByWyJuZXRf
dXNlIl0gZWxzZSAoIuW3peWFtyIgaWYgci5nZXQoIm5ldF90b29sIikgZWxzZSAiwrciKSwgIuKckyIgaWYgclsiYXN0X29rIl0gZWxzZSAiPGIgY2xhc3M9
J3InPuWjnjwvYj4iLCBodG1sLmVzY2FwZShyWyJzZW1hbnRpYyJdKSkpCiAgICBib29rcyA9IFtdCiAgICBmb3IgcyBpbiBTVUJTOgogICAgICAgIGggPSBy
ZXNbInN1YnMiXS5nZXQocykKICAgICAgICBmb3IgYiBpbiAoaCBvciB7fSkuZ2V0KCJib29rcyIsIFtdKToKICAgICAgICAgICAgYm9va3MuYXBwZW5kKCI8
dHIgZGF0YS1zPSclcycgZGF0YS1sPSclcyc+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwv
dGQ+PC90cj4iICUgKHMsIGJbImxhbXAiXSwgbGFtcChiWyJsYW1wIl0pLCBzLCBodG1sLmVzY2FwZShiWyJib29rIl0pLCBiWyJkaXIiXSwgIuKckyIgaWYg
YlsicmVnaXN0ZXJlZCJdIGVsc2UgIuKAlCIsICLinJMiIGlmIGJbIm51bWJlcmVkIl0gZWxzZSAi4oCUIikpCiAgICBsaWJzID0gW10KICAgIGZvciBzIGlu
IFNVQlM6CiAgICAgICAgaCA9IHJlc1sic3VicyJdLmdldChzKQogICAgICAgIGZvciBsIGluIChoIG9yIHt9KS5nZXQoImxpYnMiLCBbXSk6CiAgICAgICAg
ICAgIGxpYnMuYXBwZW5kKCI8dHIgZGF0YS1zPSclcycgZGF0YS1sPSclcyc+PHRkPiVzPC90ZD48dGQ+JXM8L3RkPjx0ZD4lczwvdGQ+PHRkPiVzPC90ZD48
L3RyPiIgJSAocywgbFsibGFtcCJdLCBsYW1wKGxbImxhbXAiXSksIHMsIGxbImxpYiJdLCAi4pyTIiBpZiBsWyJpbXBvcnRhYmxlIl0gZWxzZSAiPGIgY2xh
c3M9J3InPue8ujwvYj4iKSkKICAgIHJldHVybiAiIiI8IWRvY3R5cGUgaHRtbD48aHRtbCBsYW5nPSJ6aC1IYW50Ij48aGVhZD48bWV0YSBjaGFyc2V0PSJ1
dGYtOCI+PG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCxpbml0aWFsLXNjYWxlPTEiPjx0aXRsZT5WSUEg5YGl5bq3
55+p6ZmjPC90aXRsZT4KPHN0eWxlPgo6cm9vdHstLWJnOiNmZmY7LS1wYW5lbDojZjdmN2Y3Oy0tbGluZTojZTBlMGUwOy0tdHh0OiMxZjI5Mzc7LS1kaW06
IzZiNzI4MH0KYm9keXtmb250LWZhbWlseToiTWljcm9zb2Z0IEpoZW5nSGVpIFVJIiwiU2Vnb2UgVUkiLEFyaWFsLHNhbnMtc2VyaWY7YmFja2dyb3VuZDp2
YXIoLS1iZyk7Y29sb3I6dmFyKC0tdHh0KTttYXJnaW46MDtwYWRkaW5nOjEycHg7Zm9udC1zaXplOjEycHh9Cmgxe2ZvbnQtc2l6ZToxNnB4O21hcmdpbjow
IDAgNHB4fS5tZXRhe2NvbG9yOnZhcigtLWRpbSk7Zm9udC1zaXplOjExcHg7bWFyZ2luLWJvdHRvbTo4cHh9Ci5ncmlke2Rpc3BsYXk6Z3JpZDtncmlkLXRl
bXBsYXRlLWNvbHVtbnM6cmVwZWF0KGF1dG8tZml0LG1pbm1heCgyNjBweCwxZnIpKTtnYXA6OHB4O21hcmdpbi1ib3R0b206OHB4fQouY2FyZHtiYWNrZ3Jv
dW5kOnZhcigtLXBhbmVsKTtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OHB4O3BhZGRpbmc6OHB4fS5oZHtmb250LXdlaWdo
dDo3MDA7Zm9udC1zaXplOjEzcHg7bWFyZ2luLWJvdHRvbTo0cHh9Lmt2e2ZvbnQtc2l6ZToxMS41cHg7bGluZS1oZWlnaHQ6MS41fQouY2hpcHN7ZGlzcGxh
eTpncmlkO2dyaWQtdGVtcGxhdGUtY29sdW1uczpyZXBlYXQoYXV0by1maXQsbWlubWF4KDIyMHB4LDFmcikpO2dhcDo2cHg7bWFyZ2luLWJvdHRvbToxMHB4
fS5jaGlwe2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlcjoxcHggc29saWQgdmFyKC0tbGluZSk7Ym9yZGVyLXJhZGl1czo2cHg7cGFkZGluZzo1cHgg
OHB4O2ZvbnQtc2l6ZToxMXB4O2Rpc3BsYXk6ZmxleDtnYXA6NnB4O2FsaWduLWl0ZW1zOmNlbnRlcjtmbGV4LXdyYXA6d3JhcH0uY2hpcCBzcGFue2NvbG9y
OnZhcigtLWRpbSl9Ci5scHtkaXNwbGF5OmlubGluZS1ibG9jazt3aWR0aDoxMXB4O2hlaWdodDoxMXB4O2JvcmRlci1yYWRpdXM6NTAlJTt2ZXJ0aWNhbC1h
bGlnbjptaWRkbGU7bWFyZ2luLXJpZ2h0OjRweH0ubHAuUkVEe2FuaW1hdGlvbjpibCAyLjRzIGVhc2UtaW4tb3V0IGluZmluaXRlfUBrZXlmcmFtZXMgYmx7
MCUlLDEwMCUle29wYWNpdHk6MX01MCUle29wYWNpdHk6LjI1fX0KLmJhciBidXR0b257bWFyZ2luOjAgNHB4IDZweCAwO3BhZGRpbmc6M3B4IDhweDtib3Jk
ZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlci1yYWRpdXM6NnB4O2N1cnNvcjpwb2ludGVyO2ZvbnQtc2l6
ZToxMXB4fQpkZXRhaWxze21hcmdpbjo2cHggMH1zdW1tYXJ5e2N1cnNvcjpwb2ludGVyO2ZvbnQtd2VpZ2h0OjcwMDtmb250LXNpemU6MTIuNXB4O3BhZGRp
bmc6NHB4IDB9Ci53cmFwe292ZXJmbG93LXg6YXV0b310YWJsZXtib3JkZXItY29sbGFwc2U6Y29sbGFwc2U7d2lkdGg6MTAwJSU7dGFibGUtbGF5b3V0OmF1
dG99dGgsdGR7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtwYWRkaW5nOjJweCA1cHg7dGV4dC1hbGlnbjpsZWZ0O3ZlcnRpY2FsLWFsaWduOnRvcDt3
aGl0ZS1zcGFjZTpub3dyYXB9dGh7YmFja2dyb3VuZDojMTExODI3O2NvbG9yOiNmZmY7cG9zaXRpb246c3RpY2t5O3RvcDowO2ZvbnQtd2VpZ2h0OjYwMH0K
dHI6bnRoLWNoaWxkKGV2ZW4pe2JhY2tncm91bmQ6I2ZhZmFmYX10ZC5jb2Rle2ZvbnQtZmFtaWx5OkNvbnNvbGFzLG1vbm9zcGFjZX10ZC5ue3RleHQtYWxp
Z246cmlnaHR9LmRpbXtjb2xvcjp2YXIoLS1kaW0pO2ZvbnQtc2l6ZToxMC41cHg7d2hpdGUtc3BhY2U6bm9ybWFsfS5ye2NvbG9yOiNkYzI2MjZ9CkBtZWRp
YShtYXgtd2lkdGg6NzAwcHgpe2JvZHl7cGFkZGluZzo2cHh9dGgsdGR7cGFkZGluZzoycHggM3B4O2ZvbnQtc2l6ZToxMC41cHh9fQo8L3N0eWxlPjwvaGVh
ZD48Ym9keT4KPGgxPlZJQSDlgaXlurfnn6npmaMgwrcgVkNHQyAvIFZERiAvIFZSTjwvaDE+PGRpdiBjbGFzcz0ibWV0YSI+JXMgwrcg5qC5ICVzIMK3IOWQ
hCBTeXN0ZW1NYW5hZ2VyIOiHquWgsShoZWFsdGgg5YuV6KmeKSzmr43ns7vntbHlj6roroDljK/nuL0gwrcg57SFID0gQVNUIOWjniAvIOWHuue2sueEoee2
suapiyAvIGxpYiDnvLo76buDID0g54Sh6JmfIC8g5pyq55m76KiYIC8g54Sh5qmLIC8g54mI6Jmf6Kqe5oSPO+e2oCA9IOm9ijvngbAgPSDlsJrmnKrot5E8
L2Rpdj4KPGRpdiBjbGFzcz0iZ3JpZCI+JXM8L2Rpdj4KPGRpdiBjbGFzcz0iY2hpcHMiPiVzPC9kaXY+CjxkaXYgY2xhc3M9ImJhciI+JXMgPGJ1dHRvbiBv
bmNsaWNrPSJmbHQoJycsJycpIj7lhajpg6g8L2J1dHRvbj4gPGJ1dHRvbiBvbmNsaWNrPSJmbHQoJycsJ1JFRCcpIj7lj6rnnIvntIU8L2J1dHRvbj4gPGJ1
dHRvbiBvbmNsaWNrPSJmbHQoJycsJ1lFTExPVycpIj7lj6rnnIvpu4M8L2J1dHRvbj48L2Rpdj4KPGRldGFpbHMgb3Blbj48c3VtbWFyeT7mqpTmoYggLyDl
vJXmk44o5q+P5peP5LiA5YiXKTwvc3VtbWFyeT48ZGl2IGNsYXNzPSJ3cmFwIj48dGFibGUgY2xhc3M9Im0iPjx0aGVhZD48dHI+PHRoPueHiDwvdGg+PHRo
Puezu+e1sTwvdGg+PHRoPuaXjyAvIOWkvjwvdGg+PHRoPuWwvueJiDwvdGg+PHRoPueJiOaVuDwvdGg+PHRoPue3qOiZnzwvdGg+PHRoPueZu+iomDwvdGg+
PHRoPuWKoOmAn+WZqDwvdGg+PHRoPue2suapizwvdGg+PHRoPkFTVDwvdGg+PHRoPueJiOacrOiqnuaEjzwvdGg+PC90cj48L3RoZWFkPjx0Ym9keT4lczwv
dGJvZHk+PC90YWJsZT48L2Rpdj48L2RldGFpbHM+CjxkZXRhaWxzIG9wZW4+PHN1bW1hcnk+5YaKIC8g6KGo6aCtIC8g5a2X5YW4PC9zdW1tYXJ5PjxkaXYg
Y2xhc3M9IndyYXAiPjx0YWJsZSBjbGFzcz0ibSI+PHRoZWFkPjx0cj48dGg+54eIPC90aD48dGg+57O757WxPC90aD48dGg+5YaKPC90aD48dGg+5aS+PC90
aD48dGg+6KGo6aCt55m76KiYPC90aD48dGg+55m86JmfPC90aD48L3RyPjwvdGhlYWQ+PHRib2R5PiVzPC90Ym9keT48L3RhYmxlPjwvZGl2PjwvZGV0YWls
cz4KPGRldGFpbHM+PHN1bW1hcnk+bGliIC8g55Kw5aKDKOWQhOiHquebtOitr+WZqCk8L3N1bW1hcnk+PGRpdiBjbGFzcz0id3JhcCI+PHRhYmxlIGNsYXNz
PSJtIj48dGhlYWQ+PHRyPjx0aD7nh4g8L3RoPjx0aD7ns7vntbE8L3RoPjx0aD5saWI8L3RoPjx0aD7lj68gaW1wb3J0PC90aD48L3RyPjwvdGhlYWQ+PHRi
b2R5PiVzPC90Ym9keT48L3RhYmxlPjwvZGl2PjwvZGV0YWlscz4KPHNjcmlwdD5mdW5jdGlvbiBmbHQocyxsKXtkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxs
KCd0YWJsZS5tIHRib2R5IHRyJykuZm9yRWFjaChmdW5jdGlvbih0KXt0LnN0eWxlLmRpc3BsYXk9KCghc3x8dC5kYXRhc2V0LnM9PT1zKSYmKCFsfHx0LmRh
dGFzZXQubD09PWwpKT8nJzonbm9uZSd9KX08L3NjcmlwdD4KPC9ib2R5PjwvaHRtbD4iIiIgJSAocmVzWyJ0cyJdLCBodG1sLmVzY2FwZShyZXNbInJvb3Qi
XSksICIiLmpvaW4oY2FyZHMpLCBjaGlwX2h0bWwsICIiLmpvaW4oIjxidXR0b24gb25jbGljaz1cImZsdCgnJXMnLCcnKVwiPiVzPC9idXR0b24+IiAlIChz
LCBzKSBmb3IgcyBpbiBTVUJTKSwgIlxuIi5qb2luKHJvd3MpLCAiXG4iLmpvaW4oYm9va3MpLCAiXG4iLmpvaW4obGlicykpCgoKZGVmIHBhc3RlX3BhY2so
cmVzOiBkaWN0KSAtPiBsaXN0OgogICAgTCA9IFsiW+ioiF0gdmNnYyBoZWFsdGggbWF0cml4IMK3IOe4veeHiCAlcyDCtyAlcyDCtyAiICUgKHJlc1sibGFt
cCJdLCByZXNbInRzIl0pICsgIiDCtyAiLmpvaW4oIiVzPSVzIiAlIChzLCAocmVzWyJzdWJzIl1bc10gb3Ige30pLmdldCgibGFtcCIsICJHUkFZKOacqui3
kSBoZWFsdGgpIikpIGZvciBzIGluIFNVQlMpXQogICAgZm9yIHMgaW4gU1VCUzoKICAgICAgICBoID0gcmVzWyJzdWJzIl0uZ2V0KHMpCiAgICAgICAgaWYg
bm90IGg6CiAgICAgICAgICAgIEwuYXBwZW5kKCIgIFtHUkFZXSAlcyDlsJrmnKrot5EgJXNfU3lzdGVtTWFuYWdlciBoZWFsdGgiICUgKHMsIHMpKQogICAg
ICAgICAgICBjb250aW51ZQogICAgICAgIG0gPSBoWyJzdW1tYXJ5Il0KICAgICAgICBMLmFwcGVuZCgiICBbJXNdICVzIOaqlOaXjyAlZCjntIUgJWQg6buD
ICVkIOe2oCAlZCnCtyDmnInomZ8gJWQgwrcg55m76KiYICVkIMK3IOapiyAlZCDCtyDntrLmqYvnvLogJWQgwrcg6Kqe5oSPICVkIMK3IOWKnyAlZC8lZCDC
tyDooaggJWQvJWQgwrcg5YaKICVkIMK3IGxpYiDnvLogJWQiICUgKHsiUkVEIjogIlJFRCIsICJZRUxMT1ciOiAiWUVMIiwgIkdSRUVOIjogIk9LIn1baFsi
bGFtcCJdXSwgcywgbVsiZmlsZXMiXSwgbVsicmVkIl0sIG1bInllbGxvdyJdLCBtWyJncmVlbiJdLCBtWyJudW1iZXJlZCJdLCBtWyJyZWdpc3RlcmVkIl0s
IG1bImFjY2VsIl0sIG1bIm5ldF9iYWQiXSwgbVsic2VtYW50aWNfaXNzdWVzIl0sIG1bImZuX251bWJlcmVkIl0sIG1bImZuX2l0ZW1zIl0sIG1bInRhYmxl
c19udW1iZXJlZCJdLCBtWyJ0YWJsZXMiXSwgbVsiYm9va3MiXSwgbVsibGlic19taXNzaW5nIl0pKQogICAgICAgIGZvciByIGluIFt4IGZvciB4IGluIGhb
ImZpbGVzIl0gaWYgeFsibGFtcCJdID09ICJSRUQiXVs6OF06CiAgICAgICAgICAgIEwuYXBwZW5kKCIgICAgW1JFRF0gJXMgJXMgwrcgJXMiICUgKHMsIHJb
InRhaWwiXSwgIkFTVCDlo54iIGlmIG5vdCByWyJhc3Rfb2siXSBlbHNlICLlh7rntrLnhKHntrLmqYsiKSkKICAgICAgICBmb3IgbCBpbiBbeCBmb3IgeCBp
biBoWyJsaWJzIl0gaWYgbm90IHhbImltcG9ydGFibGUiXV1bOjVdOgogICAgICAgICAgICBMLmFwcGVuZCgiICAgIFtSRURdICVzIGxpYiDnvLogJXMiICUg
KHMsIGxbImxpYiJdKSkKICAgICAgICBzZW0gPSBbeCBmb3IgeCBpbiBoWyJmaWxlcyJdIGlmIHhbInNlbWFudGljIl1dWzo2XQogICAgICAgIGZvciByIGlu
IHNlbToKICAgICAgICAgICAgTC5hcHBlbmQoIiAgICBbWUVMXSAlcyAlcyDCtyAlcyIgJSAocywgclsiZmFtaWx5Il0sIHJbInNlbWFudGljIl0pKQogICAg
Zm9yIGssIHYgaW4gcmVzWyJzZWN0aW9ucyJdLml0ZW1zKCk6CiAgICAgICAgTC5hcHBlbmQoIiAgWyVzXSAlcyDCtyAlcyIgJSAoeyJSRUQiOiAiUkVEIiwg
IllFTExPVyI6ICJZRUwiLCAiR1JFRU4iOiAiT0siLCAiR1JBWSI6ICJHUkFZIn1bdlsibGFtcCJdXSwgaywganNvbi5kdW1wcyh7a2s6IHZ2IGZvciBraywg
dnYgaW4gdi5pdGVtcygpIGlmIGtrIG5vdCBpbiAoImxhbXAiLCAidHMiKX0sIGVuc3VyZV9hc2NpaT1GYWxzZSlbOjE2MF0pKQogICAgTC5hcHBlbmQoIk5F
WFQ6IOe0hSDihpIg6Kmy5a2Q57O757WxIG1hbmFnZXIg5Ye66JaE5bC+KOijnOe2suapiyAvIOS/riBBU1QgLyDoo50gbGliKTvpu4Mg4oaSIOi3kSBmbi90
YWJsZSByZWdpc3RlciArIFZDR0MgZ292ZXJuIOeZvOiZn+OAgeijnCBbVklBOkFDQ0VMLUJSSURHRV3jgIHniYjomZ/oo5zmtJ4754GwIOKGkiDlhYjot5Hl
sI3mh4nlvJXmk4475aCx5ZGKIFZJQV9SZXBvcnRzL3Jldmlldy92Y2djX2hlYWx0aC9IRUFMVEhfTUFUUklYX2xhdGVzdC5odG1sIikKICAgIHJldHVybiBM
WzozMDBdCgoKZGVmIHdyaXRlX291dHB1dHMocmVzOiBkaWN0LCBwYWNrOiBsaXN0LCBQOiBkaWN0IHwgTm9uZSA9IE5vbmUpIC0+IGRpY3Q6CiAgICBQID0g
UCBvciBfcGF0aHMoKQogICAgUFsib3V0Il0ubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgUFsiY2FyZHMiXS5ta2RpcihwYXJlbnRz
PVRydWUsIGV4aXN0X29rPVRydWUpCiAgICAoUFsib3V0Il0gLyAiSEVBTFRIX01BVFJJWF9sYXRlc3QuanNvbiIpLndyaXRlX3RleHQoanNvbi5kdW1wcyhy
ZXMsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgaHQgPSBQWyJvdXQiXSAvICJIRUFMVEhfTUFUUklYX2xh
dGVzdC5odG1sIgogICAgaHQud3JpdGVfdGV4dChfaHRtbChyZXMpLCBlbmNvZGluZz0idXRmLTgiKQogICAgbWQgPSBQWyJjYXJkcyJdIC8gKCJWQ0dDX0hl
YWx0aENhcmRfJXMubWQiICUgZGF0ZXRpbWUuZGF0ZXRpbWUubm93KCkuc3RyZnRpbWUoIiVZJW0lZCIpKQogICAgbWQud3JpdGVfdGV4dCgiXG4iLmpvaW4o
WyIjIFZJQSDlgaXlurfnn6npmaPljaEiLCAiIiwgImBgYCJdICsgcGFjayArIFsiYGBgIiwgIiJdKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIHJldHVybiB7
Imh0bWwiOiBzdHIoaHQpLCAibWQiOiBzdHIobWQpfQoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9G
Uk9NX1ZDR0MiKSAhPSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJu
IDIKICAgIGEgPSBsaXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQogICAgaWYgIi0tc2VsZnRlc3QiIGluIGFbOjJdOgogICAg
ICAgIHJldHVybiBzZWxmdGVzdCgpCiAgICBpZiBhWzoxXSAhPSBbIm1hdHJpeCJdOgogICAgICAgIHByaW50KCJb5ouS6LeRXSBtYXRyaXggfCAtLXNlbGZ0
ZXN0IikKICAgICAgICByZXR1cm4gMgogICAgcmVzID0gbWF0cml4KCkKICAgIHBhY2sgPSBwYXN0ZV9wYWNrKHJlcykKICAgIG91dCA9IHdyaXRlX291dHB1
dHMocmVzLCBwYWNrKQogICAgZm9yIGxuIGluIHBhY2s6CiAgICAgICAgcHJpbnQobG4pCiAgICBwcmludCgiICBbTUFUUklYXSAlcyIgJSBvdXRbImh0bWwi
XSkKICAgIHByaW50KCIgIFvljaFdICVzIiAlIG91dFsibWQiXSkKICAgIGlmIG9zLmVudmlyb24uZ2V0KCJWSUFfTk9fT1BFTiIpICE9ICIxIiBhbmQgb3Mu
bmFtZSA9PSAibnQiOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3Muc3RhcnRmaWxlKG91dFsiaHRtbCJdKSAgIyB0eXBlOiBpZ25vcmVbYXR0ci1kZWZp
bmVkXQogICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICBwYXNzCiAgICByZXR1cm4gMSBpZiByZXNbImxhbXAiXSA9PSAiUkVEIiBlbHNlIDAK
CgoKCiMgPT09PT0gW1ZJQTpVSS1USEVNRTp2MDEwMF0g5pqr5pmC5qiZ5rqWIFUvSSDmqKHmnb8o6aGP6ImyL+Wtl+mrlC/plpPot50gdG9rZW4g5YaKO+ac
quS+huaOpeS7u+S9leioreioiOaooeadv+WPquaPm+WGiuS4jeaUueW8leaTjjvnh4joibLpjpblrpogVklBX1VJX0Zvcm1hdExvY2sg5Zub6ImyKT09PT09
Cl9USEVNRV9ERUZBVUxUID0gewogICAgInNjaGVtYSI6ICJWSUEuVUkuVGVtcGxhdGUuU1NPVC52MSIsICJ2ZXJzaW9uIjogInYwMTAwIiwgInN0YXR1cyI6
ICJURU1QT1JBUllfU1RBTkRBUkQiLAogICAgInJ1bGUiOiAi5omA5pyJ5a2Q57O757WxIFUvSSDlj6rnlKggdmFyKC0tdG9rZW4pO+aPm+ioreioiOaooead
vyA9IOWHuuaWsOeJiOWGiuaUuSB0b2tlbnM754eI5Zub6ImyKOe2oC/pu4Mv57SFL+eBsCnpjpblrprkuI3pmqjmqKHmnb/oroo7aGlzdG9yeSDlj6rlop4i
LAogICAgInRva2VucyI6IHsiYmciOiAiI2ZmZmZmZiIsICJwYW5lbCI6ICIjZjdmN2Y3IiwgImxpbmUiOiAiI2UwZTBlMCIsICJ0eHQiOiAiIzFmMjkzNyIs
ICJkaW0iOiAiIzZiNzI4MCIsICJhY2MiOiAiIzI1NjNlYiIsICJoZWFkIjogIiMxMTE4MjciLCAiaGVhZC10eHQiOiAiI2ZmZmZmZiIsICJ6ZWJyYSI6ICIj
ZmFmYWZhIiwKICAgICAgICAgICAgICAgImZvbnQiOiAiXCJNaWNyb3NvZnQgSmhlbmdIZWkgVUlcIixcIlNlZ29lIFVJXCIsQXJpYWwsc2Fucy1zZXJpZiIs
ICJtb25vIjogIkNvbnNvbGFzLG1vbm9zcGFjZSIsICJmcyI6ICIxMnB4IiwgInJhZGl1cyI6ICI4cHgiLCAicGFkIjogIjZweCIsCiAgICAgICAgICAgICAg
ICJsYW1wLWdyZWVuIjogIiMxNmEzNGEiLCAibGFtcC15ZWxsb3ciOiAiI2Y1OWUwYiIsICJsYW1wLXJlZCI6ICIjZGMyNjI2IiwgImxhbXAtZ3JheSI6ICIj
OWNhM2FmIn0sCiAgICAibG9ja2VkIjogWyJsYW1wLWdyZWVuIiwgImxhbXAteWVsbG93IiwgImxhbXAtcmVkIiwgImxhbXAtZ3JheSJdLCAiaGlzdG9yeSI6
IFtdfQpfSEVYMlRPS0VOID0geyIjMTZhMzRhIjogImxhbXAtZ3JlZW4iLCAiI2Y1OWUwYiI6ICJsYW1wLXllbGxvdyIsICIjZGMyNjI2IjogImxhbXAtcmVk
IiwgIiM5Y2EzYWYiOiAibGFtcC1ncmF5IiwgIiNmN2Y3ZjciOiAicGFuZWwiLCAiI2UwZTBlMCI6ICJsaW5lIiwgIiMxZjI5MzciOiAidHh0IiwgIiM2Yjcy
ODAiOiAiZGltIiwgIiMyNTYzZWIiOiAiYWNjIiwgIiMxMTE4MjciOiAiaGVhZCIsICIjZmFmYWZhIjogInplYnJhIn0KCgpkZWYgdWlfdGhlbWVfbG9hZChy
b290KToKICAgIGltcG9ydCBqc29uIGFzIF9qCiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX1AKICAgIGZwID0gX1Aocm9vdCkgLyAic3VwcG9y
dGl2ZSBtb2R1bGVzIiAvICJyZWdpc3RyeSIgLyAiVklBX1VJX1RlbXBsYXRlX1NTT1RfdjAxMDAuanNvbiIKICAgIHRyeToKICAgICAgICBpZiBmcC5leGlz
dHMoKToKICAgICAgICAgICAgZCA9IF9qLmxvYWRzKGZwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpCiAgICAgICAgICAgIHQgPSBkaWN0KF9U
SEVNRV9ERUZBVUxUWyJ0b2tlbnMiXSk7IHQudXBkYXRlKGQuZ2V0KCJ0b2tlbnMiKSBvciB7fSkKICAgICAgICAgICAgZm9yIGsgaW4gX1RIRU1FX0RFRkFV
TFRbImxvY2tlZCJdOgogICAgICAgICAgICAgICAgdFtrXSA9IF9USEVNRV9ERUZBVUxUWyJ0b2tlbnMiXVtrXSAgICAgICAgICAjIOeHiOiJsumOluWumgog
ICAgICAgICAgICByZXR1cm4gdCwgZnAubmFtZQogICAgZXhjZXB0IEV4Y2VwdGlvbjogICMgbm9xYTogQkxFMDAxCiAgICAgICAgcGFzcwogICAgcmV0dXJu
IGRpY3QoX1RIRU1FX0RFRkFVTFRbInRva2VucyJdKSwgTm9uZQoKCmRlZiB1aV90aGVtZV9jc3ModG9rZW5zKToKICAgIHJldHVybiAiPHN0eWxlIGlkPVwi
dmlhLXRoZW1lXCI+OnJvb3R7JXN9PC9zdHlsZT4iICUgIjsiLmpvaW4oIi0tJXM6JXMiICUgKGssIHYpIGZvciBrLCB2IGluIHRva2Vucy5pdGVtcygpKQoK
CmRlZiB1aV90aGVtZV9hcHBseShodG1sX3RleHQsIHJvb3QpOgogICAgIiIi5oqK6aCB6Z2i6KOh55qE5Zu65a6a6Imy5o+b5oiQIHZhcigtLXRva2VuLOWb
uuWumuiJsikoZmFsbGJhY2sg5L+d55WZKSzkuKblnKggPGhlYWQ+IOW+jOaPkiB0b2tlbiDlhoogQ1NTO+eHiOiJsuS4jeiuiuOAgiIiIgogICAgdG9rZW5z
LCBib29rID0gdWlfdGhlbWVfbG9hZChyb290KQogICAgb3V0ID0gaHRtbF90ZXh0CiAgICBmb3IgaHgsIHRrIGluIF9IRVgyVE9LRU4uaXRlbXMoKToKICAg
ICAgICBvdXQgPSBvdXQucmVwbGFjZSgiJ2JhY2tncm91bmQ6JXMnIiAlIGh4LCAiJ2JhY2tncm91bmQ6dmFyKC0tJXMsJXMpJyIgJSAodGssIGh4KSkucmVw
bGFjZSgiYmFja2dyb3VuZDolcyIgJSBoeCwgImJhY2tncm91bmQ6dmFyKC0tJXMsJXMpIiAlICh0aywgaHgpKS5yZXBsYWNlKCJjb2xvcjolcyIgJSBoeCwg
ImNvbG9yOnZhcigtLSVzLCVzKSIgJSAodGssIGh4KSkucmVwbGFjZSgiYm9yZGVyOjFweCBzb2xpZCAlcyIgJSBoeCwgImJvcmRlcjoxcHggc29saWQgdmFy
KC0tJXMsJXMpIiAlICh0aywgaHgpKQogICAgY3NzID0gdWlfdGhlbWVfY3NzKHRva2VucykgKyAoIjwhLS0gdGhlbWU6JXMgLS0+IiAlIChib29rIG9yICJk
ZWZhdWx0IikpIAogICAgaSA9IG91dC5maW5kKCI8aGVhZD4iKQogICAgb3V0ID0gKG91dFs6aSArIDZdICsgY3NzICsgb3V0W2kgKyA2Ol0pIGlmIGkgPj0g
MCBlbHNlIChjc3MgKyBvdXQpCiAgICByZXR1cm4gb3V0CgoKZGVmIHVpX3RoZW1lX2luaXQocm9vdCwgYXBwbHk9VHJ1ZSk6CiAgICBpbXBvcnQganNvbiBh
cyBfaiwgZGF0ZXRpbWUgYXMgX2R0CiAgICBmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGggYXMgX1AKICAgIGZwID0gX1Aocm9vdCkgLyAic3VwcG9ydGl2ZSBt
b2R1bGVzIiAvICJyZWdpc3RyeSIgLyAiVklBX1VJX1RlbXBsYXRlX1NTT1RfdjAxMDAuanNvbiIKICAgIGlmIGZwLmV4aXN0cygpOgogICAgICAgIHJldHVy
biB7InN0YXR1cyI6ICJFWElTVFMiLCAiZmlsZSI6IGZwLm5hbWV9CiAgICBkID0gZGljdChfVEhFTUVfREVGQVVMVCk7IGRbImNyZWF0ZWRfYXQiXSA9IF9k
dC5kYXRldGltZS5ub3coKS5pc29mb3JtYXQodGltZXNwZWM9InNlY29uZHMiKTsgZFsib3JpZ2luIl0gPSAi5pON5L2c5ZOh5LukIDIwMjYtMTAtMDY65pyq
5L6G6Ieq6YGp5oeJ5byP5pyD5o6l5LiK5Lu75L2VIFUvSSDoqK3oqIjmqKHmnb/poY/oibLnmoTmmqvmmYLmqJnmupbmqKHmnb8iCiAgICBpZiBhcHBseToK
ICAgICAgICBmcC5wYXJlbnQubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgICAgIGZwLndyaXRlX3RleHQoX2ouZHVtcHMoZCwgZW5z
dXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MSksIGVuY29kaW5nPSJ1dGYtOCIpCiAgICByZXR1cm4geyJzdGF0dXMiOiAiV1JJVFRFTiIgaWYgYXBwbHkgZWxz
ZSAiUExBTiIsICJmaWxlIjogZnAubmFtZSwgInRva2VucyI6IGxlbihkWyJ0b2tlbnMiXSl9CiMgPT09PT0gW1ZJQTpVSS1USEVNRTpFTkRdID09PT09CgoK
IyA9PT09PSBbVklBOlVJLU1PVVNFOnYwMTAwXSBMMTE4IOa7kem8oOW+i+W+jOiZleeQhjrmjIfku6TmoYbml4HliqDjgIzln7fooYwo5ruR6bygKeOAjT0g
dmlhOi8vIOmAo+e1kChXaW5kb3dzIOS6pOe1puWVn+WLleWZqCnCtyDjgIzpgbjmqpTln7fooYzjgI1waWNrPTEgwrcg5pel5pyf5qyE5pS5IHR5cGU9ZGF0
ZTvpjbXnm6TovLjlhaXlj6rlianmnIDlvozmiYvmrrUgPT09PT0KX01PVVNFX0pTID0gIiIiCjxzY3JpcHQ+CihmdW5jdGlvbigpewogIHZhciBTVUI9JShz
dWIpczsKICBmdW5jdGlvbiBidWlsZChjbWQscGljayl7CiAgICB2YXIgbT1jbWQubWF0Y2goL3B5dGhvblxccysiW14iXSsiXFxzKyguKikkLyk7IGlmKCFt
KSByZXR1cm4gJyc7CiAgICB2YXIgdG9rcz1tWzFdLnRyaW0oKS5zcGxpdCgvXFxzKy8pLmZpbHRlcihCb29sZWFuKSwgdmVyYj1bXSwgYXJncz1bXTsKICAg
IGZvcih2YXIgaT0wO2k8dG9rcy5sZW5ndGg7aSsrKXsgaWYoYXJncy5sZW5ndGg9PT0wICYmIHRva3NbaV0uaW5kZXhPZignLS0nKSE9PTApIHZlcmIucHVz
aCh0b2tzW2ldKTsgZWxzZSBhcmdzLnB1c2godG9rc1tpXSk7IH0KICAgIHZhciB1PSd2aWE6Ly8nK1NVQisnLycrdmVyYi5qb2luKCcvJyk7IHZhciBxPVtd
OyBpZihhcmdzLmxlbmd0aCkgcS5wdXNoKCdhcmdzPScrZW5jb2RlVVJJQ29tcG9uZW50KGFyZ3Muam9pbignICcpKSk7IGlmKHBpY2spIHEucHVzaCgncGlj
az0xJyk7CiAgICByZXR1cm4gdSsocS5sZW5ndGg/KCc/JytxLmpvaW4oJyYnKSk6JycpOwogIH0KICBmdW5jdGlvbiBzeW5jKCl7IHZhciB0PWRvY3VtZW50
LmdldEVsZW1lbnRCeUlkKCdjbWQnKTsgaWYoIXQpIHJldHVybjsgdmFyIGE9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ3J1bicpLCBiPWRvY3VtZW50Lmdl
dEVsZW1lbnRCeUlkKCdydW5waWNrJyk7CiAgICBpZihhKXthLmhyZWY9YnVpbGQodC52YWx1ZSxmYWxzZSl8fCcjJzt9IGlmKGIpe2IuaHJlZj1idWlsZCh0
LnZhbHVlLHRydWUpfHwnIyc7fSB9CiAgdmFyIHQ9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2NtZCcpOyBpZih0KXsgbmV3IE11dGF0aW9uT2JzZXJ2ZXIo
c3luYykub2JzZXJ2ZSh0LHthdHRyaWJ1dGVzOnRydWUsY2hpbGRMaXN0OnRydWUsY2hhcmFjdGVyRGF0YTp0cnVlLHN1YnRyZWU6dHJ1ZX0pOyB0LmFkZEV2
ZW50TGlzdGVuZXIoJ2lucHV0JyxzeW5jKTsgfQogIHZhciBvcmlnU2V0PU9iamVjdC5nZXRPd25Qcm9wZXJ0eURlc2NyaXB0b3IoSFRNTFRleHRBcmVhRWxl
bWVudC5wcm90b3R5cGUsJ3ZhbHVlJyk7CiAgaWYodCYmb3JpZ1NldCYmb3JpZ1NldC5zZXQpeyBPYmplY3QuZGVmaW5lUHJvcGVydHkodCwndmFsdWUnLHtz
ZXQ6ZnVuY3Rpb24odil7b3JpZ1NldC5zZXQuY2FsbCh0aGlzLHYpO3N5bmMoKTt9LGdldDpmdW5jdGlvbigpe3JldHVybiBvcmlnU2V0LmdldC5jYWxsKHRo
aXMpO319KTsgfQogIGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoImlucHV0LnNkLCBpbnB1dCNucyIpLmZvckVhY2goZnVuY3Rpb24oaSl7IGkudHlwZT0n
ZGF0ZSc7IH0pOwogIHN5bmMoKTsKfSkoKTsKPC9zY3JpcHQ+IiIiCl9NT1VTRV9CVE4gPSAiPGEgaWQ9J3J1bicgY2xhc3M9J2J0biBwJyBocmVmPScjJyB0
aXRsZT0ndmlhOi8vIOWNlOWumiDihpIg5ZWf5YuV5ZmoIFBTIOKGkiBweXRob24g5YuV6KmeIOKGkiDplosgVS9JKOWFiOi3keS4gOasoSBJbnZva2UtVklB
LUxhdW5jaCAtUmVnaXN0ZXJQcm90b2NvbCknPuWft+ihjCjmu5HpvKApPC9hPiA8YSBpZD0ncnVucGljaycgY2xhc3M9J2J0bicgaHJlZj0nIycgdGl0bGU9
J+WFiOmWiyBXaW5kb3dzIOaqlOahiOmBuOWPluWZqCzpgbjliLDnmoTmqpTmjqXlnKjlj4PmlbjlvownPumBuOaqlOWft+ihjDwvYT4iCl9NT1VTRV9DU1Mg
PSAiPHN0eWxlPmEuYnRue2Rpc3BsYXk6aW5saW5lLWJsb2NrO3BhZGRpbmc6NHB4IDEwcHg7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lLCNlMGUwZTAp
O2JvcmRlci1yYWRpdXM6NnB4O2JhY2tncm91bmQ6I2ZmZjtjb2xvcjp2YXIoLS10eHQsIzFmMjkzNyk7dGV4dC1kZWNvcmF0aW9uOm5vbmU7Zm9udC1zaXpl
OjExcHg7bWFyZ2luOjZweCA0cHggMCAwfWEuYnRuLnB7YmFja2dyb3VuZDp2YXIoLS1hY2MsIzI1NjNlYik7Y29sb3I6I2ZmZjtib3JkZXItY29sb3I6dmFy
KC0tYWNjLCMyNTYzZWIpfTwvc3R5bGU+IgoKCmRlZiB1aV9tb3VzZV9hcHBseShodG1sX3RleHQsIHN1Yik6CiAgICAiIiLlnKggPHRleHRhcmVhIGlkPSdj
bWQn4oCmPjwvdGV4dGFyZWE+IOW+jOaPkuWFqeWAiyB2aWE6Ly8g5oyJ6YiVOzwvYm9keT4g5YmN5o+SIEpTO+aXpeacn+ashOaUuSB0eXBlPWRhdGXjgILm
spLmnInmjIfku6TmoYbnmoTpoIHkuI3li5XjgIIiIiIKICAgIGltcG9ydCByZSBhcyBfcmUKICAgIGlmICJpZD0nY21kJyIgbm90IGluIGh0bWxfdGV4dCBh
bmQgJ2lkPSJjbWQiJyBub3QgaW4gaHRtbF90ZXh0OgogICAgICAgIHJldHVybiBodG1sX3RleHQKICAgIG91dCA9IF9yZS5zdWIociIoPHRleHRhcmVhIGlk
PVsnXCJdY21kWydcIl1bXj5dKj48L3RleHRhcmVhPikiLCBsYW1iZGEgbTogbS5ncm91cCgxKSArIF9NT1VTRV9CVE4sIGh0bWxfdGV4dCwgY291bnQ9MSkK
ICAgIGpzID0gX01PVVNFX0pTICUgeyJzdWIiOiBfX2ltcG9ydF9fKCJqc29uIikuZHVtcHMoc3ViKX0KICAgIGkgPSBvdXQucmZpbmQoIjwvYm9keT4iKQog
ICAgb3V0ID0gKG91dFs6aV0gKyBfTU9VU0VfQ1NTICsganMgKyBvdXRbaTpdKSBpZiBpID49IDAgZWxzZSBvdXQgKyBfTU9VU0VfQ1NTICsganMKICAgIHJl
dHVybiBvdXQKIyA9PT09PSBbVklBOlVJLU1PVVNFOkVORF0gPT09PT0KCgojID09PT09IFtWSUE6VUktTUFOSUZFU1Q6djAxMDBdIOWtkOezu+e1sSBVL0kg
5riF5ZauKOiHquWgsSk65YWl5Y+j6aCBIMK3IOmggeexpCDCtyDnh4ggwrcg5YuV6Kme5pW4IMK3IOaooeadv+WGijvmr43ns7vntbHlhaXlj6Plj6roroDm
uIXllq7ntYTpoIEs5LiN5a+r5a2Q57O757Wx6aCBID09PT09CmRlZiB1aV9tYW5pZmVzdF93cml0ZShzdWIsIG91dF9kaXIsIGh0bWxfcGF0aCwgbGFtcCwg
ZXh0cmE9Tm9uZSk6CiAgICBpbXBvcnQganNvbiBhcyBfaiwgZGF0ZXRpbWUgYXMgX2R0LCByZSBhcyBfcmUKICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0
aCBhcyBfUAogICAgaHRtbF9wYXRoID0gX1AoaHRtbF9wYXRoKQogICAgdHJ5OgogICAgICAgIGggPSBodG1sX3BhdGgucmVhZF90ZXh0KGVuY29kaW5nPSJ1
dGYtOCIpCiAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICBoID0gIiIKICAgIG5hbWVzID0gW19yZS5zdWIociI8W14+XSs+IiwgIiIsIHQpLnN0cmlwKCkg
Zm9yIHQgaW4gX3JlLmZpbmRhbGwociI8YnV0dG9uW14+XSpvbmNsaWNrPVwidGFiXChcZCssdGhpc1wpXCI+KC4qPyk8L2J1dHRvbj4iLCBoKV0KICAgIHBh
Z2VzID0gX3JlLmZpbmRhbGwociI8ZGl2IGNsYXNzPVwicGFnZVteXCJdKlwiW14+XSo+KC4qPyk8L2Rpdj4iLCBoLCBfcmUuUykKICAgIHNyY3MgPSBbKChf
cmUuc2VhcmNoKHIiPGlmcmFtZVtePl0qc3JjPVwiKFteXCJdKilcIiIsIHBnKSBvciBbTm9uZSwgIiJdKVsxXSkgZm9yIHBnIGluIHBhZ2VzXQogICAgdGFi
cyA9IFt7Im5hbWUiOiBuLCAic3JjIjogKHNyY3NbaV0gaWYgaSA8IGxlbihzcmNzKSBlbHNlICIiKX0gZm9yIGksIG4gaW4gZW51bWVyYXRlKG5hbWVzKV0K
ICAgIHRoZW1lID0gKF9yZS5zZWFyY2gociI8IS0tIHRoZW1lOihbXiA+XSspIC0tPiIsIGgpIG9yIFtOb25lLCAiZGVmYXVsdCJdKVsxXQogICAgbSA9IHsi
c2NoZW1hIjogIlZJQS5VSS5NYW5pZmVzdC52MSIsICJzdWIiOiBzdWIsICJ0cyI6IF9kdC5kYXRldGltZS5ub3coKS5pc29mb3JtYXQodGltZXNwZWM9InNl
Y29uZHMiKSwgImVudHJ5IjogaHRtbF9wYXRoLm5hbWUsICJkaXIiOiBzdHIob3V0X2RpciksICJsYW1wIjogbGFtcCwgInRhYnMiOiB0YWJzLCAidGhlbWUi
OiB0aGVtZSwKICAgICAgICAgIm1vdXNlIjogImlkPSdydW4nIiBpbiBoLCAibGVmdF9wYW5lbCI6ICI8YXNpZGU+IiBpbiBofQogICAgaWYgZXh0cmE6CiAg
ICAgICAgbS51cGRhdGUoZXh0cmEpCiAgICBmcCA9IF9QKG91dF9kaXIpIC8gKHN1YiArICJfVUlfTUFOSUZFU1QuanNvbiIpCiAgICBmcC53cml0ZV90ZXh0
KF9qLmR1bXBzKG0sIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJuIGZwCiMgPT09PT0gW1ZJQTpV
SS1NQU5JRkVTVDpFTkRdID09PT09CgoKIyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIAgdjAxMDQ6Y29uZmlnKOeoi+W8j+WkviDCtyDos4fmlpnluqspwrcgdWko5YWp6Z2i5p2/KSDilIDilIDilIDilIDilIDilIDilIDilIDi
lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKX0NGRyA9ICJWSUFfQ29uZmlnX1NTT1RfdjAxMDAuanNvbiIKCgpk
ZWYgY29uZmlnX2xvYWQoUDogZGljdCB8IE5vbmUgPSBOb25lKSAtPiBkaWN0OgogICAgUCA9IFAgb3IgX3BhdGhzKCkKICAgIGZwID0gUFsicmVnaXN0cnki
XSAvIF9DRkcKICAgIGlmIGZwLmV4aXN0cygpOgogICAgICAgIHRyeToKICAgICAgICAgICAgcmV0dXJuIGpzb24ubG9hZHMoZnAucmVhZF90ZXh0KGVuY29k
aW5nPSJ1dGYtOC1zaWciKSkKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcGFzcwogICAgY2ZnID0geyJzY2hlbWEiOiAiVklBLkNv
bmZpZy5TU09ULnYxIiwgInZlcnNpb24iOiAidjAxMDAiLCAiY3JlYXRlZF9hdCI6IF9ub3coKSwgInJ1bGUiOiAiVkNHQyDlj6rmnInlhanntYToqK3lrpo6
56iL5byP5qqU5qGI5aS+KFZJQSDmoLkp6IiH6LOH5paZ5bqrO+aUueWLlSBoaXN0b3J5IOWPquWinjvlrZDns7vntbHlhorkuI3lnKjpgJnoo6EiLAogICAg
ICAgICAgICJwcm9ncmFtIjogeyJyb290Ijogc3RyKFBbInJvb3QiXSksICJ1cGRhdGVkX2F0IjogX25vdygpfSwKICAgICAgICAgICAiZGIiOiB7ImtpbmQi
OiAiZHVja2RiIiwgInBhdGgiOiBzdHIoUFsicm9vdCJdIC8gIlZJQV9EYXRhIiAvICJ2aWEuZHVja2RiIiksICJwYXJxdWV0X3Jvb3QiOiBzdHIoUFsicm9v
dCJdIC8gIlZJQV9EYXRhIiAvICJwYXJxdWV0IiksICJtZW1vcnlfbGltaXQiOiAiMkdCIiwgInRocmVhZHMiOiA0LCAidXBkYXRlZF9hdCI6IF9ub3coKX0s
ICJoaXN0b3J5IjogW119CiAgICBQWyJyZWdpc3RyeSJdLm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhpc3Rfb2s9VHJ1ZSkKICAgIGZwLndyaXRlX3RleHQoanNv
bi5kdW1wcyhjZmcsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpLCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJuIGNmZwoKCmRlZiBjb25maWdf
c2V0KHNlY3Rpb246IHN0ciwga2V5OiBzdHIsIHZhbHVlOiBzdHIsIFA6IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdDoKICAgIFAgPSBQIG9yIF9wYXRo
cygpCiAgICBjZmcgPSBjb25maWdfbG9hZChQKQogICAgaWYgc2VjdGlvbiBub3QgaW4gKCJwcm9ncmFtIiwgImRiIik6CiAgICAgICAgcmV0dXJuIHsib2si
OiBGYWxzZSwgIndoeSI6ICLlj6rmnIkgcHJvZ3JhbSAvIGRiIOWFqee1hCJ9CiAgICBhbGxvd2VkID0geyJwcm9ncmFtIjogKCJyb290IiwpLCAiZGIiOiAo
ImtpbmQiLCAicGF0aCIsICJwYXJxdWV0X3Jvb3QiLCAibWVtb3J5X2xpbWl0IiwgInRocmVhZHMiKX1bc2VjdGlvbl0KICAgIGlmIGtleSBub3QgaW4gYWxs
b3dlZDoKICAgICAgICByZXR1cm4geyJvayI6IEZhbHNlLCAid2h5IjogIiVzIOWPquiDveaUuSAlcyIgJSAoc2VjdGlvbiwgIi8iLmpvaW4oYWxsb3dlZCkp
fQogICAgb2xkID0gY2ZnW3NlY3Rpb25dLmdldChrZXkpCiAgICBjZmdbc2VjdGlvbl1ba2V5XSA9IGludCh2YWx1ZSkgaWYga2V5ID09ICJ0aHJlYWRzIiBh
bmQgc3RyKHZhbHVlKS5pc2RpZ2l0KCkgZWxzZSB2YWx1ZQogICAgY2ZnW3NlY3Rpb25dWyJ1cGRhdGVkX2F0Il0gPSBfbm93KCkKICAgIGNmZ1siaGlzdG9y
eSJdLmFwcGVuZCh7InRzIjogX25vdygpLCAic2VjdGlvbiI6IHNlY3Rpb24sICJrZXkiOiBrZXksICJmcm9tIjogb2xkLCAidG8iOiBjZmdbc2VjdGlvbl1b
a2V5XX0pCiAgICAoUFsicmVnaXN0cnkiXSAvIF9DRkcpLndyaXRlX3RleHQoanNvbi5kdW1wcyhjZmcsIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEp
LCBlbmNvZGluZz0idXRmLTgiKQogICAgcmV0dXJuIHsib2siOiBUcnVlLCAic2VjdGlvbiI6IHNlY3Rpb24sICJrZXkiOiBrZXksICJmcm9tIjogb2xkLCAi
dG8iOiBjZmdbc2VjdGlvbl1ba2V5XX0KCgpkZWYgdWkoUDogZGljdCB8IE5vbmUgPSBOb25lKSAtPiBkaWN0OgogICAgUCA9IFAgb3IgX3BhdGhzKCkKICAg
IHJlcyA9IG1hdHJpeChQKQogICAgcGFjayA9IHBhc3RlX3BhY2socmVzKQogICAgd3JpdGVfb3V0cHV0cyhyZXMsIHBhY2ssIFApCiAgICBjZmcgPSBjb25m
aWdfbG9hZChQKQogICAgbWUgPSBzdHIoTUUpCiAgICBkZWYgbHAobCk6CiAgICAgICAgcmV0dXJuICI8aSBjbGFzcz0nbHAgJXMnIHN0eWxlPSdiYWNrZ3Jv
dW5kOiVzJz48L2k+IiAlIChsLCBMQU1QLmdldChsLCBMQU1QWyJHUkFZIl0pKQogICAgZGVmIGYoc2VjdGlvbiwga2V5LCBzaXplPTQwKToKICAgICAgICBy
ZXR1cm4gIjxsYWJlbD4lczwvbGFiZWw+PGlucHV0IGlkPSclc18lcycgdmFsdWU9JyVzJyBzaXplPSclZCc+IiAlIChrZXksIHNlY3Rpb24sIGtleSwgaHRt
bC5lc2NhcGUoc3RyKGNmZ1tzZWN0aW9uXS5nZXQoa2V5LCAiIikpKSwgc2l6ZSkKICAgIGNhcmRzID0gIiIuam9pbigiPGRpdiBjbGFzcz0nY2FyZCc+JXM8
Yj4lczwvYj4gPHNtYWxsPiVzPC9zbWFsbD48L2Rpdj4iICUgKGxwKChyZXNbInN1YnMiXS5nZXQocykgb3Ige30pLmdldCgibGFtcCIsICJHUkFZIikpLCBz
LCAoKHJlc1sic3VicyJdLmdldChzKSBvciB7fSkuZ2V0KCJ0cyIpIG9yICLmnKrot5EiKSkgZm9yIHMgaW4gU1VCUykKICAgIHBhZ2UgPSAiIiI8IWRvY3R5
cGUgaHRtbD48aHRtbCBsYW5nPSJ6aC1IYW50Ij48aGVhZD48bWV0YSBjaGFyc2V0PSJ1dGYtOCI+PG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9Indp
ZHRoPWRldmljZS13aWR0aCxpbml0aWFsLXNjYWxlPTEiPjx0aXRsZT5WQ0dDIFUvSTwvdGl0bGU+CjxzdHlsZT46cm9vdHstLWxpbmU6I2UwZTBlMDstLXBh
bmVsOiNmN2Y3Zjc7LS10eHQ6IzFmMjkzNzstLWRpbTojNmI3MjgwOy0tYWNjOiMyNTYzZWJ9Ym9keXtmb250LWZhbWlseToiTWljcm9zb2Z0IEpoZW5nSGVp
IFVJIiwiU2Vnb2UgVUkiLEFyaWFsO2NvbG9yOnZhcigtLXR4dCk7bWFyZ2luOjA7Zm9udC1zaXplOjEycHg7YmFja2dyb3VuZDojZmZmO2hlaWdodDoxMDB2
aDtkaXNwbGF5OmdyaWQ7Z3JpZC10ZW1wbGF0ZS1jb2x1bW5zOjMyMHB4IDFmcjtncmlkLXRlbXBsYXRlLXJvd3M6YXV0byAxZnJ9CmhlYWRlcntncmlkLWNv
bHVtbjoxLzM7cGFkZGluZzo4cHggMTJweDtib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1saW5lKTtkaXNwbGF5OmZsZXg7Z2FwOjEycHg7YWxpZ24t
aXRlbXM6Y2VudGVyfWhlYWRlciBoMXtmb250LXNpemU6MTVweDttYXJnaW46MH1oZWFkZXIgc21hbGx7Y29sb3I6dmFyKC0tZGltKX1hc2lkZXtib3JkZXIt
cmlnaHQ6MXB4IHNvbGlkIHZhcigtLWxpbmUpO3BhZGRpbmc6MTBweDtvdmVyZmxvdzphdXRvO2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpfW1haW57ZGlzcGxh
eTpmbGV4O2ZsZXgtZGlyZWN0aW9uOmNvbHVtbjtvdmVyZmxvdzpoaWRkZW59CmxhYmVse2Rpc3BsYXk6YmxvY2s7Zm9udC1zaXplOjExcHg7Y29sb3I6dmFy
KC0tZGltKTttYXJnaW46OHB4IDAgMnB4fWlucHV0LHRleHRhcmVhe3dpZHRoOjEwMCUlO2JveC1zaXppbmc6Ym9yZGVyLWJveDtmb250OjEycHggQ29uc29s
YXMsbW9ub3NwYWNlO3BhZGRpbmc6NHB4IDZweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6NnB4O2JhY2tncm91bmQ6I2Zm
Zn1idXR0b257cGFkZGluZzo0cHggMTBweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JhY2tncm91bmQ6I2ZmZjtib3JkZXItcmFkaXVzOjZweDtj
dXJzb3I6cG9pbnRlcjtmb250LXNpemU6MTFweDttYXJnaW46NnB4IDRweCAwIDB9Ci5jYXJke2JhY2tncm91bmQ6I2ZmZjtib3JkZXI6MXB4IHNvbGlkIHZh
cigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OHB4O3BhZGRpbmc6NnB4IDhweDttYXJnaW46NnB4IDA7Zm9udC1zaXplOjExLjVweH0uZGlte2NvbG9yOnZhcigt
LWRpbSl9LnRhYnN7ZGlzcGxheTpmbGV4O2dhcDo0cHg7cGFkZGluZzo2cHggMTBweDtib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1saW5lKTtmbGV4
LXdyYXA6d3JhcH0udGFicyBidXR0b24ub257YmFja2dyb3VuZDojMTExODI3O2NvbG9yOiNmZmY7Ym9yZGVyLWNvbG9yOiMxMTE4Mjd9LnBhZ2Vze2ZsZXg6
MTtwb3NpdGlvbjpyZWxhdGl2ZX0ucGFnZXtwb3NpdGlvbjphYnNvbHV0ZTtpbnNldDowO2Rpc3BsYXk6bm9uZX0ucGFnZS5vbntkaXNwbGF5OmJsb2NrfWlm
cmFtZXt3aWR0aDoxMDAlJTtoZWlnaHQ6MTAwJSU7Ym9yZGVyOjB9Ci5scHtkaXNwbGF5OmlubGluZS1ibG9jazt3aWR0aDoxMXB4O2hlaWdodDoxMXB4O2Jv
cmRlci1yYWRpdXM6NTAlJTt2ZXJ0aWNhbC1hbGlnbjptaWRkbGU7bWFyZ2luLXJpZ2h0OjRweH0ubHAuUkVEe2FuaW1hdGlvbjpibCAyLjRzIGVhc2UtaW4t
b3V0IGluZmluaXRlfUBrZXlmcmFtZXMgYmx7MCUlLDEwMCUle29wYWNpdHk6MX01MCUle29wYWNpdHk6LjI1fX1AbWVkaWEobWF4LXdpZHRoOjgwMHB4KXti
b2R5e2dyaWQtdGVtcGxhdGUtY29sdW1uczoxZnI7Z3JpZC10ZW1wbGF0ZS1yb3dzOmF1dG8gYXV0byAxZnJ9YXNpZGV7Ym9yZGVyLXJpZ2h0OjA7Ym9yZGVy
LWJvdHRvbToxcHggc29saWQgdmFyKC0tbGluZSk7bWF4LWhlaWdodDo0MHZofX08L3N0eWxlPjwvaGVhZD48Ym9keT4KPGhlYWRlcj48aDE+VkNHQyDCtyDm
r43ns7vntbE8L2gxPjxzbWFsbD4lcyDCtyDlt6Y65Y+q5pyJ5YWp57WE6Kit5a6aKOeoi+W8j+aqlOahiOWkviDCtyDos4fmlpnluqspwrcg5Y+zOuWkmumg
geWxleekuiDCtyA8c3BhbiBzdHlsZT0iY29sb3I6IzE2YTM0YSI+4pePPC9zcGFuPue2oCA8c3BhbiBzdHlsZT0iY29sb3I6I2Y1OWUwYiI+4pePPC9zcGFu
Pum7gyA8c3BhbiBzdHlsZT0iY29sb3I6I2RjMjYyNiI+4pePPC9zcGFuPue0hSA8c3BhbiBzdHlsZT0iY29sb3I6IzljYTNhZiI+4pePPC9zcGFuPueBsDwv
c21hbGw+PC9oZWFkZXI+Cjxhc2lkZT4KICA8ZGl2IGNsYXNzPSdjYXJkJz48Yj7nqIvlvI/mqpTmoYjlpL48L2I+JXM8YnV0dG9uIG9uY2xpY2s9InNldHYo
J3Byb2dyYW0nLCdyb290JykiPuaUuTwvYnV0dG9uPjwvZGl2PgogIDxkaXYgY2xhc3M9J2NhcmQnPjxiPuizh+aWmeW6qzwvYj4lcyVzJXMlcyVzPGJ1dHRv
biBvbmNsaWNrPSJzZXR2KCdkYicsJ3BhdGgnKSI+5pS5IHBhdGg8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InNldHYoJ2RiJywncGFycXVldF9yb290Jyki
PuaUuSBwYXJxdWV0PC9idXR0b24+PGJ1dHRvbiBvbmNsaWNrPSJzZXR2KCdkYicsJ21lbW9yeV9saW1pdCcpIj7mlLkgbWVtb3J5PC9idXR0b24+PGJ1dHRv
biBvbmNsaWNrPSJzZXR2KCdkYicsJ3RocmVhZHMnKSI+5pS5IHRocmVhZHM8L2J1dHRvbj48L2Rpdj4KICA8bGFiZWw+5oyH5LukKOiyvOWIsCBQb3dlclNo
ZWxsKTwvbGFiZWw+PHRleHRhcmVhIGlkPSdjbWQnIHJvd3M9JzQnIHJlYWRvbmx5PjwvdGV4dGFyZWE+PGJ1dHRvbiBvbmNsaWNrPSdjb3B5aXQoKSc+6KSH
6KO9PC9idXR0b24+CiAgJXMKICA8c2NyaXB0PnZhciBQWT0lcztmdW5jdGlvbiBzZXR2KHMsayl7dmFyIHY9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQocysn
XycraykudmFsdWU7ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2NtZCcpLnZhbHVlPSckZW52OlZJQV9GUk9NX1ZDR0M9IllFUyI7IHB5dGhvbiAiJytQWSsn
IiBjb25maWcgc2V0IC0tc2VjdGlvbiAnK3MrJyAtLWtleSAnK2srJyAtLXZhbHVlICInK3YrJyInfQogIGZ1bmN0aW9uIGNvcHlpdCgpe3ZhciB0PWRvY3Vt
ZW50LmdldEVsZW1lbnRCeUlkKCdjbWQnKTt0LnNlbGVjdCgpO3RyeXtuYXZpZ2F0b3IuY2xpcGJvYXJkLndyaXRlVGV4dCh0LnZhbHVlKX1jYXRjaChlKXtk
b2N1bWVudC5leGVjQ29tbWFuZCgnY29weScpfX0KICBmdW5jdGlvbiB0YWIoaSxiKXtkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCcucGFnZScpLmZvckVh
Y2goZnVuY3Rpb24ocCxqKXtwLmNsYXNzTGlzdC50b2dnbGUoJ29uJyxpPT09ail9KTtkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCcudGFicyBidXR0b24n
KS5mb3JFYWNoKGZ1bmN0aW9uKHgpe3guY2xhc3NMaXN0LnJlbW92ZSgnb24nKX0pO2IuY2xhc3NMaXN0LmFkZCgnb24nKX08L3NjcmlwdD4KPC9hc2lkZT4K
PG1haW4+CiAgPGRpdiBjbGFzcz0idGFicyI+PGJ1dHRvbiBjbGFzcz0ib24iIG9uY2xpY2s9InRhYigwLHRoaXMpIj7lgaXlurfnn6npmaM8L2J1dHRvbj48
YnV0dG9uIG9uY2xpY2s9InRhYigxLHRoaXMpIj7nkrDlooPlt6Xlhbc8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InRhYigyLHRoaXMpIj7ovJTliqnlt6Xl
hbc8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InRhYigzLHRoaXMpIj7lhajmqpTnn6npmaM8L2J1dHRvbj48YnV0dG9uIG9uY2xpY2s9InRhYig0LHRoaXMp
Ij5WREYgVS9JPC9idXR0b24+PGJ1dHRvbiBvbmNsaWNrPSJ0YWIoNSx0aGlzKSI+VlJOIFUvSTwvYnV0dG9uPjwvZGl2PgogIDxkaXYgY2xhc3M9InBhZ2Vz
Ij4KICAgIDxkaXYgY2xhc3M9InBhZ2Ugb24iPjxpZnJhbWUgc3JjPSJIRUFMVEhfTUFUUklYX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4KICAgIDxk
aXYgY2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi92Y2djX2Vudi9FTlZfTUFUUklYX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4KICAgIDxkaXYg
Y2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi92Y2djX3Rvb2xraXQvVE9PTEtJVF9NQVRSSVhfbGF0ZXN0Lmh0bWwiPjwvaWZyYW1lPjwvZGl2PgogICAg
PGRpdiBjbGFzcz0icGFnZSI+PGlmcmFtZSBzcmM9Ii4uL3ZjZ2NfbWF0cml4L0ZJTEVfTUFUUklYX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4KICAg
IDxkaXYgY2xhc3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi8uLi92ZGYvVkRGX1VJX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4KICAgIDxkaXYgY2xh
c3M9InBhZ2UiPjxpZnJhbWUgc3JjPSIuLi8uLi92cm4vVlJOX1VJX2xhdGVzdC5odG1sIj48L2lmcmFtZT48L2Rpdj4KICA8L2Rpdj4KPC9tYWluPjwvYm9k
eT48L2h0bWw+IiIiICUgKHJlc1sidHMiXSwgZigicHJvZ3JhbSIsICJyb290IiksIGYoImRiIiwgImtpbmQiLCAxMiksIGYoImRiIiwgInBhdGgiKSwgZigi
ZGIiLCAicGFycXVldF9yb290IiksIGYoImRiIiwgIm1lbW9yeV9saW1pdCIsIDgpLCBmKCJkYiIsICJ0aHJlYWRzIiwgNCksIGNhcmRzLCBqc29uLmR1bXBz
KG1lKSkKICAgIGZwID0gUFsib3V0Il0gLyAiVkNHQ19VSV9sYXRlc3QuaHRtbCIKICAgIGZwLndyaXRlX3RleHQodWlfbW91c2VfYXBwbHkodWlfdGhlbWVf
YXBwbHkocGFnZSwgUFsicm9vdCJdKSwgIlZDR0MiKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgIGhtID0gUFsib3V0Il0gLyAiSEVBTFRIX01BVFJJWF9sYXRl
c3QuaHRtbCIKICAgIGlmIGhtLmV4aXN0cygpOgogICAgICAgIGhtLndyaXRlX3RleHQodWlfdGhlbWVfYXBwbHkoaG0ucmVhZF90ZXh0KGVuY29kaW5nPSJ1
dGYtOCIpLCBQWyJyb290Il0pLCBlbmNvZGluZz0idXRmLTgiKQogICAgb3BlbmVkID0gRmFsc2UKICAgIGlmIG9zLmVudmlyb24uZ2V0KCJWSUFfTk9fT1BF
TiIpICE9ICIxIiBhbmQgb3MubmFtZSA9PSAibnQiOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3Muc3RhcnRmaWxlKHN0cihmcCkpICAjIHR5cGU6IGln
bm9yZVthdHRyLWRlZmluZWRdCiAgICAgICAgICAgIG9wZW5lZCA9IFRydWUKICAgICAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICAgICAgcGFzcwogICAg
cmV0dXJuIHsidmVyYiI6ICJ1aSIsICJodG1sIjogc3RyKGZwKSwgImxhbXAiOiByZXNbImxhbXAiXSwgIm9wZW5lZCI6IG9wZW5lZH0KCgpfTUFJTl8wMTAz
ID0gbWFpbgoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9GUk9NX1ZDR0MiKSAhPSAiWUVTIjoKICAg
ICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJuIDIKICAgIGEgPSBsaXN0KHN5cy5hcmd2
WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQoKICAgIGRlZiBvcHQoZmxhZywgZGVmYXVsdD1Ob25lKToKICAgICAgICByZXR1cm4gYVthLmluZGV4
KGZsYWcpICsgMV0gaWYgZmxhZyBpbiBhIGFuZCBhLmluZGV4KGZsYWcpICsgMSA8IGxlbihhKSBlbHNlIGRlZmF1bHQKICAgIGlmIGFbOjFdID09IFsiY29u
ZmlnIl06CiAgICAgICAgaWYgYVsxOjJdID09IFsic2V0Il06CiAgICAgICAgICAgIHIgPSBjb25maWdfc2V0KG9wdCgiLS1zZWN0aW9uIiwgIiIpLCBvcHQo
Ii0ta2V5IiwgIiIpLCBvcHQoIi0tdmFsdWUiLCAiIikpCiAgICAgICAgICAgIHByaW50KCJb6KiIXSB2Y2djIGNvbmZpZyBzZXQgwrcgJXMiICUganNvbi5k
dW1wcyhyLCBlbnN1cmVfYXNjaWk9RmFsc2UpKQogICAgICAgICAgICByZXR1cm4gMCBpZiByLmdldCgib2siKSBlbHNlIDEKICAgICAgICBjID0gY29uZmln
X2xvYWQoKQogICAgICAgIHByaW50KCJb6KiIXSB2Y2djIGNvbmZpZyDCtyDnqIvlvI/lpL4gJXMgwrcgZGIgJXMgJXMgwrcgcGFycXVldCAlcyDCtyBtZW1v
cnkgJXMgwrcgdGhyZWFkcyAlcyDCtyBoaXN0b3J5ICVkIiAlIChjWyJwcm9ncmFtIl1bInJvb3QiXSwgY1siZGIiXVsia2luZCJdLCBjWyJkYiJdWyJwYXRo
Il0sIGNbImRiIl1bInBhcnF1ZXRfcm9vdCJdLCBjWyJkYiJdWyJtZW1vcnlfbGltaXQiXSwgY1siZGIiXVsidGhyZWFkcyJdLCBsZW4oY1siaGlzdG9yeSJd
KSkpCiAgICAgICAgcmV0dXJuIDAKICAgIGlmIGFbOjFdID09IFsidGhlbWUiXToKICAgICAgICByID0gdWlfdGhlbWVfaW5pdChfcGF0aHMoKVsicm9vdCJd
LCBhcHBseT0oIi0tZHJ5IiBub3QgaW4gYSkpCiAgICAgICAgdCwgYm9vayA9IHVpX3RoZW1lX2xvYWQoX3BhdGhzKClbInJvb3QiXSkKICAgICAgICBwcmlu
dCgiW+ioiF0gdmNnYyB0aGVtZSDCtyAlcyDCtyAlcyDCtyB0b2tlbnMgJWQgwrcg54eI6Y6WIDQgwrcg5o+b5qih5p2/ID0g5Ye65paw54mI5YaK5pS5IHRv
a2VucyIgJSAoclsic3RhdHVzIl0sIHJbImZpbGUiXSwgbGVuKHQpKSkKICAgICAgICByZXR1cm4gMAogICAgaWYgYVs6MV0gPT0gWyJ1aSJdOgogICAgICAg
IHVpX3RoZW1lX2luaXQoX3BhdGhzKClbInJvb3QiXSwgYXBwbHk9VHJ1ZSkKICAgICAgICB1ID0gdWkoKQogICAgICAgIHByaW50KCJb6KiIXSB2Y2djIHVp
IMK3ICVzIMK3ICVzIMK3IOW3sumWiyAlcyIgJSAodVsiaHRtbCJdLCB1WyJsYW1wIl0sIHVbIm9wZW5lZCJdKSkKICAgICAgICBwcmludCgiICBbVS9JXSAl
cyIgJSB1WyJodG1sIl0pCiAgICAgICAgcmV0dXJuIDAKICAgIHJldHVybiBfTUFJTl8wMTAzKGFyZ3YpCgoKCgpkZWYgcG9ydGFsKFA6IGRpY3QgfCBOb25l
ID0gTm9uZSkgLT4gZGljdDoKICAgICIiIuWFpeWPo+mggTrlj6roroDkuInku70gVUkg5riF5Zau57WE6aCB44CC5a2Q57O757Wx5rKS6LeRIHVpIOWwseeB
sCzkuI3lgYfoo53jgIIiIiIKICAgIFAgPSBQIG9yIF9wYXRocygpCiAgICByZXBvcnRzID0gUFsicm9vdCJdIC8gIlZJQV9SZXBvcnRzIgogICAgc3VicyA9
IFsoIlZDR0MiLCBQWyJvdXQiXSksICgiVkRGIiwgcmVwb3J0cyAvICJ2ZGYiKSwgKCJWUk4iLCByZXBvcnRzIC8gInZybiIpXQogICAgbWFucyA9IHt9CiAg
ICBmb3Igc3ViLCBkIGluIHN1YnM6CiAgICAgICAgZnAgPSBkIC8gKHN1YiArICJfVUlfTUFOSUZFU1QuanNvbiIpCiAgICAgICAgdHJ5OgogICAgICAgICAg
ICBtYW5zW3N1Yl0gPSBqc29uLmxvYWRzKGZwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpIGlmIGZwLmV4aXN0cygpIGVsc2UgTm9uZQogICAg
ICAgIGV4Y2VwdCBWYWx1ZUVycm9yOgogICAgICAgICAgICBtYW5zW3N1Yl0gPSBOb25lCiAgICBvdXRfZnAgPSByZXBvcnRzIC8gIlZJQV9VSV9sYXRlc3Qu
aHRtbCIKICAgIGRlZiByZWwoZCwgbmFtZSk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICByZXR1cm4gKFBhdGgoZCkgLyBuYW1lKS5yZXNvbHZlKCkucmVs
YXRpdmVfdG8ob3V0X2ZwLnBhcmVudC5yZXNvbHZlKCkpLmFzX3Bvc2l4KCkKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcmV0dXJu
IHN0cihQYXRoKGQpIC8gbmFtZSkKICAgIGRlZiBscChsKToKICAgICAgICByZXR1cm4gIjxpIGNsYXNzPSdscCAlcycgc3R5bGU9J2JhY2tncm91bmQ6JXMn
PjwvaT4iICUgKGwsIExBTVAuZ2V0KGwsIExBTVBbIkdSQVkiXSkpCiAgICBidG5zLCBwYWdlcyA9IFtdLCBbXQogICAgZm9yIGksIChzdWIsIGQpIGluIGVu
dW1lcmF0ZShzdWJzKToKICAgICAgICBtID0gbWFuc1tzdWJdCiAgICAgICAgbGFtcCA9IChtIG9yIHt9KS5nZXQoImxhbXAiLCAiR1JBWSIpCiAgICAgICAg
c3JjID0gcmVsKGQsIG1bImVudHJ5Il0pIGlmIG0gZWxzZSAiIgogICAgICAgIHRzID0gKG0gb3Ige30pLmdldCgidHMiLCAi5pyq6LeRIHVpIikKICAgICAg
ICBudGFiID0gbGVuKChtIG9yIHt9KS5nZXQoInRhYnMiLCBbXSkpCiAgICAgICAgYnRucy5hcHBlbmQoIjxidXR0b24gY2xhc3M9J3N5c2J0biVzJyBvbmNs
aWNrPVwicGljayglZCx0aGlzKVwiPiVzPGI+JXM8L2I+PHNtYWxsPiVzIMK3IOmggeexpCAlZCDCtyAlczwvc21hbGw+PC9idXR0b24+IiAlICgiIG9uIiBp
ZiBpID09IDAgZWxzZSAiIiwgaSwgbHAobGFtcCksIHN1YiwgdHNbOjE2XSwgbnRhYiwgaHRtbC5lc2NhcGUoKG0gb3Ige30pLmdldCgidGhlbWUiLCAi4oCU
IikpKSkKICAgICAgICBwYWdlcy5hcHBlbmQoIjxkaXYgY2xhc3M9J3BhZ2Ulcyc+JXM8L2Rpdj4iICUgKCIgb24iIGlmIGkgPT0gMCBlbHNlICIiLCAoIjxp
ZnJhbWUgc3JjPSclcyc+PC9pZnJhbWU+IiAlIGh0bWwuZXNjYXBlKHNyYykpIGlmIHNyYyBlbHNlICI8ZGl2IGNsYXNzPSdlbXB0eSc+JXMg5bCa5pyq55Si
IFUvSTrlnKjllZ/li5Xlmajot5EgLVN1YiAlcyAtVmVyYiB1aTwvZGl2PiIgJSAoc3ViLCBzdWIpKSkKICAgIHBhZ2UgPSAiIiI8IWRvY3R5cGUgaHRtbD48
aHRtbCBsYW5nPSJ6aC1IYW50Ij48aGVhZD48bWV0YSBjaGFyc2V0PSJ1dGYtOCI+PG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmlj
ZS13aWR0aCxpbml0aWFsLXNjYWxlPTEiPjx0aXRsZT5WSUEgVS9JPC90aXRsZT4KPHN0eWxlPjpyb290ey0tbGluZTojZTBlMGUwOy0tcGFuZWw6I2Y3Zjdm
NzstLXR4dDojMWYyOTM3Oy0tZGltOiM2YjcyODA7LS1hY2M6IzI1NjNlYjstLWhlYWQ6IzExMTgyN31ib2R5e2ZvbnQtZmFtaWx5OiJNaWNyb3NvZnQgSmhl
bmdIZWkgVUkiLCJTZWdvZSBVSSIsQXJpYWw7bWFyZ2luOjA7aGVpZ2h0OjEwMHZoO2Rpc3BsYXk6ZmxleDtmbGV4LWRpcmVjdGlvbjpjb2x1bW47Y29sb3I6
dmFyKC0tdHh0KTtmb250LXNpemU6MTJweDtiYWNrZ3JvdW5kOiNmZmZ9CmhlYWRlcntkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6c3RyZXRjaDtnYXA6NnB4
O3BhZGRpbmc6NnB4IDEwcHg7Ym9yZGVyLWJvdHRvbToxcHggc29saWQgdmFyKC0tbGluZSk7YmFja2dyb3VuZDp2YXIoLS1wYW5lbCl9aGVhZGVyIGgxe2Zv
bnQtc2l6ZToxNHB4O21hcmdpbjowIDEycHggMCAwO2FsaWduLXNlbGY6Y2VudGVyfQouc3lzYnRue2Rpc3BsYXk6ZmxleDtmbGV4LWRpcmVjdGlvbjpjb2x1
bW47YWxpZ24taXRlbXM6ZmxleC1zdGFydDtnYXA6MnB4O3BhZGRpbmc6NnB4IDEycHg7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtib3JkZXItcmFk
aXVzOjhweDtiYWNrZ3JvdW5kOiNmZmY7Y3Vyc29yOnBvaW50ZXI7bWluLXdpZHRoOjE2MHB4O3RleHQtYWxpZ246bGVmdH0uc3lzYnRuLm9ue2JvcmRlci1j
b2xvcjp2YXIoLS1hY2MpO2JveC1zaGFkb3c6MCAwIDAgMnB4IHZhcigtLWFjYykgaW5zZXR9LnN5c2J0biBzbWFsbHtjb2xvcjp2YXIoLS1kaW0pO2ZvbnQt
c2l6ZToxMC41cHh9Ci5wYWdlc3tmbGV4OjE7cG9zaXRpb246cmVsYXRpdmV9LnBhZ2V7cG9zaXRpb246YWJzb2x1dGU7aW5zZXQ6MDtkaXNwbGF5Om5vbmV9
LnBhZ2Uub257ZGlzcGxheTpibG9ja31pZnJhbWV7d2lkdGg6MTAwJSU7aGVpZ2h0OjEwMCUlO2JvcmRlcjowfS5lbXB0eXtwYWRkaW5nOjIwcHg7Y29sb3I6
dmFyKC0tZGltKX0KLmxwe2Rpc3BsYXk6aW5saW5lLWJsb2NrO3dpZHRoOjExcHg7aGVpZ2h0OjExcHg7Ym9yZGVyLXJhZGl1czo1MCUlO3ZlcnRpY2FsLWFs
aWduOm1pZGRsZTttYXJnaW4tcmlnaHQ6NHB4fS5scC5SRUR7YW5pbWF0aW9uOmJsIDIuNHMgZWFzZS1pbi1vdXQgaW5maW5pdGV9QGtleWZyYW1lcyBibHsw
JSUsMTAwJSV7b3BhY2l0eToxfTUwJSV7b3BhY2l0eTouMjV9fQpAbWVkaWEobWF4LXdpZHRoOjcwMHB4KXtoZWFkZXJ7ZmxleC13cmFwOndyYXB9LnN5c2J0
bnttaW4td2lkdGg6NDYlJX19PC9zdHlsZT48L2hlYWQ+PGJvZHk+CjxoZWFkZXI+PGgxPlZJQTwvaDE+JXM8c3BhbiBzdHlsZT0iYWxpZ24tc2VsZjpjZW50
ZXI7Y29sb3I6dmFyKC0tZGltKTttYXJnaW4tbGVmdDphdXRvIj4lcyDCtyDlhaXlj6Plj6roroDlkITns7vntbHoh6rloLHmuIXllq476aCB6Zqo5ZCEIG1h
bmFnZXIg6K6KLOiJsumaqOaooeadv+WGiuiuijwvc3Bhbj48L2hlYWRlcj4KPGRpdiBjbGFzcz0icGFnZXMiPiVzPC9kaXY+CjxzY3JpcHQ+ZnVuY3Rpb24g
cGljayhpLGIpe2RvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoJy5wYWdlJykuZm9yRWFjaChmdW5jdGlvbihwLGope3AuY2xhc3NMaXN0LnRvZ2dsZSgnb24n
LGk9PT1qKX0pO2RvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoJy5zeXNidG4nKS5mb3JFYWNoKGZ1bmN0aW9uKHgpe3guY2xhc3NMaXN0LnJlbW92ZSgnb24n
KX0pO2IuY2xhc3NMaXN0LmFkZCgnb24nKX08L3NjcmlwdD48L2JvZHk+PC9odG1sPiIiIiAlICgiIi5qb2luKGJ0bnMpLCBfbm93KCksICIiLmpvaW4ocGFn
ZXMpKQogICAgb3V0X2ZwLnBhcmVudC5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICBvdXRfZnAud3JpdGVfdGV4dCh1aV90aGVtZV9h
cHBseShwYWdlLCBQWyJyb290Il0pLCBlbmNvZGluZz0idXRmLTgiKQogICAgb3BlbmVkID0gRmFsc2UKICAgIGlmIG9zLmVudmlyb24uZ2V0KCJWSUFfTk9f
T1BFTiIpICE9ICIxIiBhbmQgb3MubmFtZSA9PSAibnQiOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3Muc3RhcnRmaWxlKHN0cihvdXRfZnApKSAgIyB0
eXBlOiBpZ25vcmVbYXR0ci1kZWZpbmVkXQogICAgICAgICAgICBvcGVuZWQgPSBUcnVlCiAgICAgICAgZXhjZXB0IE9TRXJyb3I6CiAgICAgICAgICAgIHBh
c3MKICAgIHJldHVybiB7InZlcmIiOiAicG9ydGFsIiwgImh0bWwiOiBzdHIob3V0X2ZwKSwgInN1YnMiOiB7czogKChtYW5zW3NdIG9yIHt9KS5nZXQoImxh
bXAiLCAiR1JBWSIpKSBmb3IgcywgXyBpbiBzdWJzfSwgIm1pc3NpbmciOiBbcyBmb3IgcywgXyBpbiBzdWJzIGlmIG5vdCBtYW5zW3NdXSwgIm9wZW5lZCI6
IG9wZW5lZH0KCgpfTUFJTl8wMTA2ID0gbWFpbgoKCmRlZiBtYWluKGFyZ3Y9Tm9uZSkgLT4gaW50OgogICAgaWYgb3MuZW52aXJvbi5nZXQoIlZJQV9GUk9N
X1ZDR0MiKSAhPSAiWUVTIjoKICAgICAgICBwcmludCgiW1ZDR0NdIOaLkue1leOAguWPquiDvee2kyB2aWEtdmNnY+OAgiIpCiAgICAgICAgcmV0dXJuIDIK
ICAgIGEgPSBsaXN0KHN5cy5hcmd2WzE6XSBpZiBhcmd2IGlzIE5vbmUgZWxzZSBhcmd2KQogICAgaWYgYVs6MV0gPT0gWyJwb3J0YWwiXToKICAgICAgICBy
ID0gcG9ydGFsKCkKICAgICAgICBwcmludCgiW+ioiF0gdmNnYyBwb3J0YWwgwrcgJXMgwrcgJXMgwrcg5pyq6LeRIHVpOiVzIMK3IOW3sumWiyAlcyIgJSAo
clsiaHRtbCJdLCAiICIuam9pbigiJXM9JXMiICUga3YgZm9yIGt2IGluIHJbInN1YnMiXS5pdGVtcygpKSwgIiwiLmpvaW4oclsibWlzc2luZyJdKSBvciAi
54ShIiwgclsib3BlbmVkIl0pKQogICAgICAgIHByaW50KCIgIFtVL0ldICVzIiAlIHJbImh0bWwiXSkKICAgICAgICByZXR1cm4gMAogICAgaWYgYVs6MV0g
PT0gWyJ1aSJdOgogICAgICAgIHJjID0gX01BSU5fMDEwNihhKQogICAgICAgIHRyeToKICAgICAgICAgICAgUCA9IF9wYXRocygpCiAgICAgICAgICAgIHVp
X21hbmlmZXN0X3dyaXRlKCJWQ0dDIiwgUFsib3V0Il0sIFBbIm91dCJdIC8gIlZDR0NfVUlfbGF0ZXN0Lmh0bWwiLCAoanNvbi5sb2FkcygoUFsib3V0Il0g
LyAiSEVBTFRIX01BVFJJWF9sYXRlc3QuanNvbiIpLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikpLmdldCgibGFtcCIsICJHUkFZIikgaWYgKFBb
Im91dCJdIC8gIkhFQUxUSF9NQVRSSVhfbGF0ZXN0Lmpzb24iKS5leGlzdHMoKSBlbHNlICJHUkFZIiksIHsibWFuYWdlciI6IE1FLm5hbWV9KQogICAgICAg
IGV4Y2VwdCBFeGNlcHRpb24gYXMgZXhjOiAgIyBub3FhOiBCTEUwMDEKICAgICAgICAgICAgcHJpbnQoIiAgW+azqF0gVkNHQyDmuIXllq7mnKrlr6s6JXMi
ICUgZXhjKQogICAgICAgIHJldHVybiByYwogICAgcmV0dXJuIF9NQUlOXzAxMDYoYSkKCgpkZWYgc2VsZnRlc3QoKSAtPiBpbnQ6CiAgICBwID0gZiA9IDAK
CiAgICBkZWYgY2hrKG5hbWUsIGNvbmQpOgogICAgICAgIG5vbmxvY2FsIHAsIGYKICAgICAgICBpZiBjb25kOgogICAgICAgICAgICBwICs9IDEKICAgICAg
ICAgICAgcHJpbnQoIiAgW09LXSAlcyIgJSBuYW1lKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGYgKz0gMQogICAgICAgICAgICBwcmludCgiICBbRkFJ
TF0gJXMiICUgbmFtZSkKCiAgICB0ZCA9IFBhdGgodGVtcGZpbGUubWtkdGVtcChwcmVmaXg9ImNnY2hlYWx0aC0iKSkKICAgIG9zLmVudmlyb25bIlZJQV9S
T09UIl0gPSBzdHIodGQpCiAgICBvcy5lbnZpcm9uWyJWSUFfTk9fT1BFTiJdID0gIjEiCiAgICBQID0gX3BhdGhzKCkKICAgIGNoaygi4pGgIOaymeebkiIs
IGFsbChzdHIodikuc3RhcnRzd2l0aChzdHIodGQpKSBmb3IgdiBpbiBQLnZhbHVlcygpKSkKICAgIEEgPSAiIyBbVklBOkFDQ0VMLUJSSURHRTp2MDEwMF1c
biIKICAgIChQWyJyZWdpc3RyeSJdKS5ta2RpcihwYXJlbnRzPVRydWUpCiAgICAoUFsicmVnaXN0cnkiXSAvICJDR0NfTURMMDAxX1hfdjAxMDAucHkiKS53
cml0ZV90ZXh0KEEgKyAieD0xXG4iLCBlbmNvZGluZz0idXRmLTgiKQogICAgKFBbInN1cCJdIC8gIlZJQV9PbGQucHkiKS53cml0ZV90ZXh0KCJpbXBvcnQg
cmVxdWVzdHNcbiIsIGVuY29kaW5nPSJ1dGYtOCIpCiAgICAoUFsicmVwb3J0cyJdIC8gInZybiIpLm1rZGlyKHBhcmVudHM9VHJ1ZSkKICAgIChQWyJyZXBv
cnRzIl0gLyAidnJuIiAvICJIRUFMVEhfbGF0ZXN0Lmpzb24iKS53cml0ZV90ZXh0KGpzb24uZHVtcHMoeyJzdWIiOiAiVlJOIiwgInRzIjogInQiLCAibGFt
cCI6ICJHUkVFTiIsICJzdW1tYXJ5IjogeyJmaWxlcyI6IDIsICJyZWQiOiAwLCAieWVsbG93IjogMCwgImdyZWVuIjogMiwgIm51bWJlcmVkIjogMiwgInJl
Z2lzdGVyZWQiOiAyLCAiYWNjZWwiOiAyLCAibmV0X2JhZCI6IDAsICJzZW1hbnRpY19pc3N1ZXMiOiAwLCAiZm5faXRlbXMiOiA1LCAiZm5fbnVtYmVyZWQi
OiA1LCAidGFibGVzIjogMSwgInRhYmxlc19udW1iZXJlZCI6IDEsICJib29rcyI6IDEsICJsaWJzX21pc3NpbmciOiAwLCAicHl0aG9uIjogInB5In0sICJm
aWxlcyI6IFtdLCAiYm9va3MiOiBbXSwgImxpYnMiOiBbXX0pLCBlbmNvZGluZz0idXRmLTgiKQogICAgKFBbInJldmlldyJdIC8gInZjZ2NfcGFub3JhbWEi
KS5ta2RpcihwYXJlbnRzPVRydWUpCiAgICAoUFsicmV2aWV3Il0gLyAidmNnY19wYW5vcmFtYSIgLyAiUEFOT1JBTUFfbGF0ZXN0Lmpzb24iKS53cml0ZV90
ZXh0KGpzb24uZHVtcHMoeyJ0cyI6ICJ0IiwgImxhbXAiOiAiWUVMTE9XIiwgImNoZWNrcyI6IHsiSzEiOiAiR1JFRU4iLCAiSzIiOiAiWUVMTE9XIn19KSwg
ZW5jb2Rpbmc9InV0Zi04IikKICAgIHJlcyA9IG1hdHJpeChQKQogICAgY2hrKCLikaEgVkNHQyDoh6rlt7Hot5HlgaXlurfmrrUoc3VwcG9ydGl2ZSBtb2R1
bGVzKToyIOaXjyDCtyBWSUFfT2xkIOWHuue2sueEoee2suapi+e0hSIsIHJlc1sic3VicyJdWyJWQ0dDIl1bInN1bW1hcnkiXVsiZmlsZXMiXSA9PSAyIGFu
ZCByZXNbInN1YnMiXVsiVkNHQyJdWyJzdW1tYXJ5Il1bIm5ldF9iYWQiXSA9PSAxKQogICAgY2hrKCLikaIgVlJOIOiugOiHquWgsSjntqApwrcgVkRGIOac
qui3kSA9IE5vbmUo54GwKSIsIHJlc1sic3VicyJdWyJWUk4iXVsibGFtcCJdID09ICJHUkVFTiIgYW5kIHJlc1sic3VicyJdWyJWREYiXSBpcyBOb25lKQog
ICAgY2hrKCLikaMg5pei5pyJ5byV5pOO57WQ5p6c5L215YWlOuWFqOaZryBLMS9LMiDCtyDnkrDlooMv5bel5YW3L+ayu+eQhiDmnKrot5EgPSBHUkFZIiwg
cmVzWyJzZWN0aW9ucyJdWyJwYW5vcmFtYSJdWyJjaGVja3MiXSA9PSB7IksxIjogIkdSRUVOIiwgIksyIjogIllFTExPVyJ9IGFuZCByZXNbInNlY3Rpb25z
Il1bImVudiJdWyJsYW1wIl0gPT0gIkdSQVkiKQogICAgcGFjayA9IHBhc3RlX3BhY2socmVzKQogICAgb3V0ID0gd3JpdGVfb3V0cHV0cyhyZXMsIHBhY2ss
IFApCiAgICBodG0gPSBQYXRoKG91dFsiaHRtbCJdKS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIGNoaygi4pGkIEhUTUw65re66ImyIMK3IOiH
qumBqeaHiShhdXRvLWZpdCBncmlkIMK3IHZpZXdwb3J0KcK3IOeHiOesrOS4gOashCDCtyDlm5voibIgdG9rZW4gwrcg57SF54eI5oWi6ZaDIMK3IOWPr+aM
ieezu+e1sS/nh4jnr6kiLCAiYXV0by1maXQiIGluIGh0bSBhbmQgInZpZXdwb3J0IiBpbiBodG0gYW5kIGFsbChjIGluIGh0bSBmb3IgYyBpbiBMQU1QLnZh
bHVlcygpKSBhbmQgIkBrZXlmcmFtZXMgYmwiIGluIGh0bSBhbmQgImZsdCgnVlJOJywnJykiIGluIGh0bSkKICAgIGNoaygi4pGlIOiyvOWbnuWMhSDiiaQz
MDAgwrcgTkVYVDogwrcg57i954eI57SFKFZDR0Mg5pyJ57SFKcK3IOWNoeWcqCIsIGxlbihwYWNrKSA8PSAzMDAgYW5kIHBhY2tbLTFdLnN0YXJ0c3dpdGgo
Ik5FWFQ6IikgYW5kIHJlc1sibGFtcCJdID09ICJSRUQiIGFuZCBQYXRoKG91dFsibWQiXSkuZXhpc3RzKCkpCiAgICBjaGsoIuKRpiDllK/oroA6VklBX1Jl
cG9ydHMvdmNnYy9IRUFMVEhfbGF0ZXN0Lmpzb24g5piv5ZSv5LiA5paw5a+r5ZyoIHJlcG9ydHMvdmNnYyDnmoTmqpQiLCAoUFsicmVwb3J0cyJdIC8gInZj
Z2MiIC8gIkhFQUxUSF9sYXRlc3QuanNvbiIpLmV4aXN0cygpKQogICAgYzAgPSBjb25maWdfbG9hZChQKQogICAgcjEgPSBjb25maWdfc2V0KCJkYiIsICJt
ZW1vcnlfbGltaXQiLCAiNEdCIiwgUCkKICAgIHIyID0gY29uZmlnX3NldCgiZGIiLCAibm9wZSIsICJ4IiwgUCkKICAgIHUgPSB1aShQKQogICAgdWggPSBQ
YXRoKHVbImh0bWwiXSkucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCiAgICBjaGsoIuKRqCB2MDEwNCBjb25maWc66Ieq5bu65YaKIHByb2dyYW0vZGIg
wrcgc2V0IG1lbW9yeSA0R0IoaGlzdG9yeSAxKcK3IOmdnueZveWQjeWWrumNteaLkiDCtyB1aSDlhanpnaLmnb8o5bem5Y+q5pyJ56iL5byP5aS+K+izh+aW
meW6qyDCtyDlj7MgNiDpoIHnsaQpIiwgYzBbInByb2dyYW0iXVsicm9vdCJdID09IHN0cihQWyJyb290Il0pIGFuZCByMVsib2siXSBhbmQgY29uZmlnX2xv
YWQoUClbImRiIl1bIm1lbW9yeV9saW1pdCJdID09ICI0R0IiIGFuZCBub3QgcjJbIm9rIl0gYW5kICLnqIvlvI/mqpTmoYjlpL4iIGluIHVoIGFuZCAi6LOH
5paZ5bqrIiBpbiB1aCBhbmQgKHVoLmNvdW50KCc8ZGl2IGNsYXNzPSJwYWdlIicpICsgdWguY291bnQoJzxkaXYgY2xhc3M9InBhZ2Ugb24iJykpID09IDYg
YW5kICJWREZfVUlfbGF0ZXN0Lmh0bWwiIGluIHVoKQogICAgdGggPSB1aV90aGVtZV9pbml0KFBbInJvb3QiXSkKICAgIHVoMiA9IFBhdGgodVsiaHRtbCJd
KS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIHUyID0gdWkoUCkKICAgIHVoMiA9IFBhdGgodTJbImh0bWwiXSkucmVhZF90ZXh0KGVuY29kaW5n
PSJ1dGYtOCIpCiAgICBjaGsoIuKRqSB2MDEwNSB0aGVtZTrlhoroh6rlu7ogwrcgdWkg5aWXIHZhcigtLXRva2VuKSDCtyDnh4joibLku43ngrrpjpblrprl
m5voibIgZmFsbGJhY2siLCB0aFsic3RhdHVzIl0gaW4gKCJXUklUVEVOIiwgIkVYSVNUUyIpIGFuZCAoUFsicmVnaXN0cnkiXSAvICJWSUFfVUlfVGVtcGxh
dGVfU1NPVF92MDEwMC5qc29uIikuZXhpc3RzKCkgYW5kICdpZD0idmlhLXRoZW1lIicgaW4gdWgyIGFuZCAidmFyKC0tbGFtcC1yZWQsI2RjMjYyNikiIGlu
IHVoMiBhbmQgIi0tcGFuZWw6IiBpbiB1aDIpCiAgICB1aDMgPSBQYXRoKHVpKFApWyJodG1sIl0pLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQogICAg
Y2hrKCLikaogdjAxMDYg5ruR6byg5b6LOlZDR0MgdWkg5pyJ5Z+36KGMKOa7kem8oCl2aWE6Ly8g5oyJ6YiVIiwgImlkPSdydW4nIiBpbiB1aDMgYW5kICJ2
aWE6Ly8iIGluIHVoMykKICAgIHVpX21hbmlmZXN0X3dyaXRlKCJWQ0dDIiwgUFsib3V0Il0sIFBbIm91dCJdIC8gIlZDR0NfVUlfbGF0ZXN0Lmh0bWwiLCAi
WUVMTE9XIiwgeyJtYW5hZ2VyIjogTUUubmFtZX0pCiAgICBwciA9IHBvcnRhbChQKQogICAgcGggPSBQYXRoKHByWyJodG1sIl0pLnJlYWRfdGV4dChlbmNv
ZGluZz0idXRmLTgiKQogICAgY2hrKCLikasgdjAxMDcgcG9ydGFsOuS4ieezu+e1semIlSDCtyBWQ0dDIOaciemggSDCtyBWREYvVlJOIOacqui3kSB1aSDm
qJnngbDkuI3lgYfoo50gwrcg5qih5p2/IENTUyIsIHBoLmNvdW50KCJjbGFzcz0nc3lzYnRuIikgPT0gMyBhbmQgIlZDR0NfVUlfbGF0ZXN0Lmh0bWwiIGlu
IHBoIGFuZCBzZXQocHJbIm1pc3NpbmciXSkgPT0geyJWREYiLCAiVlJOIn0gYW5kICdpZD0idmlhLXRoZW1lIicgaW4gcGgpCiAgICBib2R5ID0gTUUucmVh
ZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCiAgICBjaGsoIuKRpyDluLbliqDpgJ/lmajmqYsgwrcg5YGl5bq35YWx55So5q61IMK3IFZJQV9GUk9NX1ZDR0Mg
6ZaYIiwgIltWSUE6QUNDRUwtQlJJREdFOnYwMTAwXSIgaW4gYm9keSBhbmQgIltWSUE6U00tSEVBTFRIOnYwMTAwXSIgaW4gYm9keSBhbmQgIlZJQV9GUk9N
X1ZDR0MiIGluIGJvZHkpCiAgICBmb3IgayBpbiAoIlZJQV9ST09UIiwgIlZJQV9OT19PUEVOIik6CiAgICAgICAgb3MuZW52aXJvbi5wb3AoaywgTm9uZSkK
ICAgIHNodXRpbC5ybXRyZWUodGQsIGlnbm9yZV9lcnJvcnM9VHJ1ZSkKICAgIHByaW50KCJb6KiIXSAlcyDoh6rmuKwgJWQvJWQgwrcgJXMiICUgKE5BTUUs
IHAsIHAgKyBmLCAiUEFTUyIgaWYgZiA9PSAwIGVsc2UgIkZBSUwiKSkKICAgIHJldHVybiAwIGlmIGYgPT0gMCBlbHNlIDEKCgppZiBfX25hbWVfXyA9PSAi
X19tYWluX18iOgogICAgcmFpc2UgU3lzdGVtRXhpdChtYWluKCkpCg==
'@
$ExH = Get-ChildItem -LiteralPath $RegDir -Filter 'CGC_MDL*_HealthMatrix_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($ExH -and $ExH.Name -match '^(CGC_MDL\d{3})_' -and $ExH.Name -lt ($Matches[1] + '_HealthMatrix_v0107.py')) { Install-VIAEmbedded -Path (Join-Path $RegDir ($Matches[1] + '_HealthMatrix_v0107.py')) -B64 $B64Hm -Want '8e9c71cf3bc24f337dc288de4459ad054fb79a3465b2dbe500d2de6886e5e298' -Tag '健康矩陣引擎 v0107(portal 入口)' | Out-Null }
# ---------- L117 入冊(一次;SKIP 即已在) ----------
$Law118 = Join-Path $LogDir 'L118.json'
@{ id = 'L118'; batch = '側線 2026-10-06'; cat = 'U/I / 操作'; key = 'MOUSE_ONLY_UI'; status = 'ACTIVE'
   zh = '【操作律】操作介面以 Windows I/O 為準:拖曳、下拉選單、勾選、按鈕;動滑鼠不動鍵盤。① 靜態頁不起 server,頁上動作 = via://<子系統>/<動詞>?args=… 連結,Windows 交給啟動器 PS(L117 形狀),PS 跑 python 動詞再開 U/I。② 要檔案 / 夾的動作加 pick=1 / dir=1,由 Windows 選取器(滑鼠)提供路徑;拖曳到頁上的檔以選取器確認。③ 需要輸入值的欄位一律下拉 / 勾選 / 日期選取器,鍵盤輸入只作最後手段並保留「複製指令」。④ 子系統 U/I 由各自 manager 產,動作連結由 manager 寫,母系統不代寫。'
   origin = '操作員原文下令 2026-10-06:操作介面 WINDOW I/O 拖曳式 下拉選單勾選 等動滑鼠不動鍵盤為原則'; enforcement = 'Invoke-VIA-Launch -RegisterProtocol / -Uri · 各 manager ui 動詞的 via:// 連結 · HealthMatrix 可加「頁上有 <input type=text> 必填」黃燈' } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $Law118 -Encoding UTF8
$Law119 = Join-Path $LogDir 'L119.json'
@{ id = 'L119'; batch = '側線 2026-10-08'; cat = '治理 / 入口'; key = 'INDEPENDENT_ENTRIES'; status = 'ACTIVE'
   zh = '【入口各自律】(L116 補充)① 入口不唯一:VRN、VDF 各有自己的入口(各自 manager 的 ui 動詞 / 自己的 HTML 兩面板頁 / via://<SUB>/… 連結),不經 VCGC;VCGC 自己的入口是治理矩陣。② VIA_UI_latest 是母系統的監控視圖(只讀三份自報清單看燈),不是入口;任何一個系統不在,其他兩個照跑。③ 子系統的日常作業(改設定、跑動詞、看結果)在各自的 HTML U/I 左面板上做,滑鼠律 L118;母系統不代操作。④ 三者互不影響以各自獨立運作紀錄為證(2026-10-08 23:00 VDF/VRN 各自 ui GREEN,VCGC 未參與)。'
   origin = '操作員原文 2026-10-08:VCGC 不再是單獨入口;VCGC VRN VDF 互不影響;子系統獨立,母系統監控;左面板在 VRN/VDF 的 HTML U/I 上作業'; enforcement = 'Invoke-VIA-Launch -Sub VDF/VRN -Verb ui · HealthMatrix portal 標「監控視圖」' } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $Law119 -Encoding UTF8
$Law = Join-Path $LogDir 'L117.json'
@{ id = 'L117'; batch = '側線 2026-10-06'; cat = '治理 / 指令形狀'; key = 'PY_FIRST_PS_LAUNCHER'; status = 'ACTIVE'
   zh = '【指令形狀律】① 所有指令 PY 化:業務邏輯、檢查、登記、發號、報表全部在 python manager / 引擎(帶 [VIA:ACCEL-BRIDGE] 加速器橋;VDF 另帶 NET / LIB 橋),PS 不再含業務邏輯。② PS 檔只做三件事:落地(只增不減)、載入加速器(VeritasCeleritas.PS7)、啟動一個 python 動詞並連結它產出的 U/I(.html);形狀固定 = Skeleton ⑨ Invoke-VCLaunch。③ 既有含邏輯的 PS 短令逐批移植進 manager 動詞,舊令標 DEPRECATED 指向新動詞,不物理刪。④ U/I 由各子系統 manager 自己產(自報律 L116),PS 只負責打開。'
   origin = '操作員原文下令 2026-10-06:所有指令 PY 化導入加速器;PS 檔加加速器用來啟動跟連結 U/I'; enforcement = 'Skeleton-v0112 ⑨ Invoke-VCLaunch · Invoke-VIA-Launch-v0100.ps1 · HealthMatrix 可加「PS 含邏輯」黃燈' } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $Law -Encoding UTF8
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
  # 車道:A = 入 L117(治理引擎,一次)· B = 啟動 $Sub $Verb 並開 U/I(本支真正要做的事)
  $Gov = (Get-ChildItem -LiteralPath $RegDir -Filter 'CGC_MDL*_RegistryGovernor_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1).FullName
  $LaneA = { param($VIA, $Gov, $Law, $LogDir)
    Set-Content -LiteralPath (Join-Path $LogDir 'A.progress') '20 · law' -Encoding UTF8
    $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'
    foreach ($lf in @($Law, (Join-Path $LogDir 'L118.json'), (Join-Path $LogDir 'L119.json'))) {
      $o = @(& python $Gov 'law' '--file' $lf 2>&1 | ForEach-Object { "" + $_ })
      $o | Where-Object { $_ -match '^\[計\]' } | ForEach-Object { $_ }
      if (-not ($o -join ' ' -match 'WRITTEN|SKIP')) { "  [RED] 入冊失敗 $(Split-Path $lf -Leaf):" + (($o | Select-Object -Last 1) -join '') } }
    Set-Content -LiteralPath (Join-Path $LogDir 'A.progress') '100 · 完' -Encoding UTF8; "rc 0" }
  $LaneB = { param($VIA, $Sub, $Verb, $VerbArgs, $LogDir, $NoOpenFlag)
    Set-Content -LiteralPath (Join-Path $LogDir 'B.progress') "20 · $Sub $Verb" -Encoding UTF8
    $map = @{ VRN = @('functional modules\VRN', 'VRN_SystemManager_v*.py'); VDF = @('functional modules\VDF', 'VDF_SystemManager_v*.py'); VCGC = @('supportive modules\registry', 'CGC_MDL*_HealthMatrix_v*.py') }
    $tail = Get-ChildItem -LiteralPath (Join-Path $VIA $map[$Sub][0]) -Filter $map[$Sub][1] -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if (-not $tail) { "  [RED] $Sub 尾版不在"; "rc 1"; return }
    $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'   # 只為本車道的 python;車道尾一律清掉
    $o = @(& python $tail.FullName $Verb @VerbArgs 2>&1 | ForEach-Object { "" + $_ }); $rc = $LASTEXITCODE
    "[計] 啟動 $Sub $($tail.Name) $Verb $($VerbArgs -join ' ') · rc $rc"
    $o | Where-Object { $_ -match '^\[計\]|^\s*\[(RED|注)\]' } | Select-Object -First 30 | ForEach-Object { $_ }
    $htmls = @($o | ForEach-Object { if ($_ -match '([A-Za-z]:\\[^\s"]+?\.html)') { $Matches[1] } } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -Unique)
    foreach ($h in $htmls) { "[U/I] $h" }
    Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue
    Set-Content -LiteralPath (Join-Path $LogDir 'B.progress') '100 · 完' -Encoding UTF8; "rc 0" }
  $Lanes = @()
  if ($okGov -and $Gov) { $Lanes += @{ id = 'A'; zh = 'L117 入冊(一次)'; args = @($VIA, $Gov, $Law, $LogDir); run = $LaneA } }
  if ($Sub -eq 'VIA') {
    # 入口模式:三系統各自 ui(自報清單)→ VCGC portal 組頁;子系統頁由各 manager 產,母系統只讀清單
    $LaneAll = { param($VIA, $LogDir)
      $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'   # 只為本車道的 python;車道尾一律清掉
      $map = @{ VDF = @('functional modules\VDF', 'VDF_SystemManager_v*.py'); VRN = @('functional modules\VRN', 'VRN_SystemManager_v*.py'); VCGC = @('supportive modules\registry', 'CGC_MDL*_HealthMatrix_v*.py') }
      $n = 0
      foreach ($s in @('VDF', 'VRN', 'VCGC')) { $n++; Set-Content -LiteralPath (Join-Path $LogDir 'B.progress') ("$([int](25 * $n)) · $s ui") -Encoding UTF8
        $t = Get-ChildItem -LiteralPath (Join-Path $VIA $map[$s][0]) -Filter $map[$s][1] -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
        if ($t) { $o = @(& python $t.FullName 'ui' 2>&1 | ForEach-Object { "" + $_ }); $o | Where-Object { $_ -match '^\[計\]' } | Select-Object -Last 1 | ForEach-Object { "[計] $s " + $_.Trim() } } else { "  [YEL] $s 尾版不在,入口標灰" } }
      $h = Get-ChildItem -LiteralPath (Join-Path $VIA 'supportive modules\registry') -Filter 'CGC_MDL*_HealthMatrix_v*.py' | Sort-Object Name | Select-Object -Last 1
      $o = @(& python $h.FullName 'portal' 2>&1 | ForEach-Object { "" + $_ }); $o | Where-Object { $_ -match '^\[計\]|^\s*\[(RED|注)\]' } | ForEach-Object { $_ }
      $htmls = @($o | ForEach-Object { if ($_ -match '([A-Za-z]:\\[^\s"]+?\.html)') { $Matches[1] } } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -Unique); foreach ($x in $htmls) { "[U/I] $x" }
      Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue
    Set-Content -LiteralPath (Join-Path $LogDir 'B.progress') '100 · 完' -Encoding UTF8; "rc 0" }
    $Lanes += @{ id = 'B'; zh = 'VIA 入口:三系統 ui → portal'; args = @($VIA, $LogDir); run = $LaneAll } }
  else { $Lanes += @{ id = 'B'; zh = "啟動 $Sub $Verb"; args = @($VIA, $Sub, $Verb, $VerbArgs, $LogDir, [bool]$NoOpen); run = $LaneB } }
  Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir
  foreach ($lane in @('A', 'B')) { $lf = Join-Path $LogDir "$lane.log"; if (Test-Path -LiteralPath $lf) { Get-Content -LiteralPath $lf | ForEach-Object { $l = ($_ -replace '\x1b\[[0-9;]*m', '').Trim(); if ($l -match '^\s*\[RED\]') { $script:Errors.Add("[$lane] $l") } elseif ($l -match '^\[計\]|^\[U/I\]|^\s*\[注\]') { $script:Verdicts.Add("[$lane] $l") } } } }
  if (-not $NoOpen) { Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue }   # 開頁前清旗標(執行緒共用環境,車道設的會殘留)
  foreach ($v in @($script:Verdicts | Where-Object { $_ -match '^\[B\] \[U/I\] ' })) { $h = $v -replace '^\[B\] \[U/I\] ', ''; if ((Test-Path -LiteralPath $h) -and -not $NoOpen) { try { Start-Process -FilePath $h } catch { try { Invoke-Item -LiteralPath $h } catch { } } } }
  $script:Verdicts = [System.Collections.Generic.List[string]]::new([string[]]@($script:Verdicts | Select-Object -Unique))
  $script:Verdicts.Add("[結算] 一個 U/I 連三個 SystemManager:VIA_Reports\VIA_UI_latest.html(上列三系統燈/切換鈕,下載入所選系統自己的頁;頁隨各 manager 清單變,色隨模板冊變,母系統不寫子系統頁)· 開法 -Sub VIA · L118 滑鼠律:頁上「執行(滑鼠)」= via:// 連結(第一次先跑本支 -RegisterProtocol 註冊協定,HKCU 只動自己)· 「選檔執行」開 Windows 檔案選取器 · 日期欄為日期選取器 · 暫時標準 U/I 模板:registry\VIA_UI_Template_SSOT_v0100.json(token;燈四色鎖定);換設計模板 = 出新版冊改 tokens,三系統頁自動跟 · VCGC 左面板只有程式夾+資料庫(config set)· VDF 左面板只有族群起始日期(改整族)+ 新增項目/族群 · 左 = 輸入(動詞 · 參數 · 組指令 · 複製)· 右 = 多頁(健康矩陣 · 表頭 · 全景 · 結果 · 本輪 PS);檔在 VIA_Reports\<sub>\<SUB>_UI_latest.html · L119:三系統各自入口(-Sub VDF / -Sub VRN -Verb ui 各開各的頁,日常作業在各自 HTML 左面板上做);-Sub VIA 只是母系統監控視圖,不是入口")
}
Show-VCSummary -Title "啟動器:$Sub $Verb → U/I" -LogDir $LogDir
