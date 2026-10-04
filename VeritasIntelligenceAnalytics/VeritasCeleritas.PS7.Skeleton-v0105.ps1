# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([int]$MaxMin = 60, [int]$KeepRuns = 5, [switch]$NoCleanup)
# param 必須是第一個語句(PS 規則);加速器橋接在它後面,章的文字判準不受影響
# AI 產出必須接入模板。只動 $PID,關閉即還原。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# VeritasCeleritas.PS7.Skeleton v0105 — AI 寫 PS 的新規定(操作員 2026-10-03):
#   前段固定四件:① 安全清理(只動本行程:GC · 關本輪孤兒子行程 · TEMP 滾動;不碰別人、不 EmptyWorkingSet、不改優先權)
#               ② TEMP 為主記憶體支援(VIA_TEMP_ROOT/<run>/;TMP/TEMP/TMPDIR/POLARS_TEMP_DIR/duckdb 全指過去;L107)
#               ③ 加速器模組(dot-source AutoImport → Start-CeleritasPS7;缺席 fallback)
#               ④ 雙軌並行:Invoke-VCDualLane 兩條(或多條)車道同時跑,各自 log,看門狗
#   收尾固定:Show-VCSummary — 黃字 = 貼給 AI 的判決行;紅字 = 錯誤;綠 = 過;灰 = 沒跑;字體只用主控台既有(不改終端機字型 = 安全),HTML 用 VIA_UI_FormatLock 鎖定字體與四燈。
#   用法:複製本檔改名,把工作放進 $Lanes;其餘不動。
$ErrorActionPreference = 'Continue'
$VIA = if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'supportive modules'))) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()

# ---------- ① 安全清理(只動本行程) ----------
function Invoke-VCSafeCleanup {
  $MaxMin = if ($MaxMin) { [int]$MaxMin } else { 60 }   # 被別支借用時 param 不在 → 用預設(v0103)
  $before = [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
  [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
  # 只關「本行程」上一輪留下的孤兒子行程(父 PID = 本 PID 且已超過 MaxMin);別人的 python 一律不碰
  $orphans = Get-CimInstance Win32_Process -Filter "ParentProcessId = $PID" | Where-Object { $_.Name -match 'python|pwsh' -and ((Get-Date) - $_.CreationDate).TotalMinutes -gt $MaxMin }
  foreach ($o in $orphans) { try { Stop-Process -Id $o.ProcessId -Force -ErrorAction SilentlyContinue; $script:Verdicts.Add("[清理] 關本行程孤兒子行程 pid $($o.ProcessId) ($($o.Name))") } catch { } }
  $after = [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
  $cpu = (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average
  $script:Verdicts.Add("[清理] GC 完成 · 可用 RAM $before → $after GB · CPU 負載 $cpu% · 孤兒 $($orphans.Count)(不動優先權 · 不 EmptyWorkingSet · 不碰他人行程)")
}

# ---------- ② TEMP 為主記憶體支援(L107) ----------
function Initialize-VCTemp {
  $KeepRuns = if ($KeepRuns) { [int]$KeepRuns } else { 5 }   # 被別支借用時 param 不在 → 用預設(v0103)
  $root = if ($env:VIA_TEMP_ROOT) { $env:VIA_TEMP_ROOT } else { Join-Path $env:LOCALAPPDATA 'Temp\VIA_progress' }
  $run = Join-Path $root ("ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $run | Out-Null
  $env:VIA_TEMP_ROOT = $root; $env:TMP = $run; $env:TEMP = $run; $env:TMPDIR = $run; $env:POLARS_TEMP_DIR = $run; $env:VIA_DUCKDB_TEMP_DIR = $run; $env:VIA_SPILL_TO_DISK = '1'
  $old = Get-ChildItem $root -Directory -Filter 'ps_*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -Skip $KeepRuns
  foreach ($o in $old) { $mb = [Math]::Round(((Get-ChildItem $o.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB), 1); Remove-Item $o.FullName -Recurse -Force -ErrorAction SilentlyContinue
    Add-Content (Join-Path $root 'purge_ledger.jsonl') ('{"at":"' + (Get-Date -Format o) + '","purged":"' + $o.Name + '","mb":' + $mb + ',"rule":"L107 keep_last=' + $KeepRuns + '","by":"PS7.Skeleton-v0101"}') }
  $script:Verdicts.Add("[TEMP] $run · 滾動留 $KeepRuns 輪(清 $($old.Count))")
  $run
}

# ---------- ③ 加速器模組 ----------
function Initialize-VCAccel {
  $auto = Join-Path $VIA 'supportive modules\VeritasCeleritas.PS7.AutoImport.ps1'
  if (Test-Path $auto) { . $auto }
  if (Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) { try { if ((Get-Command Start-CeleritasPS7).Parameters.ContainsKey('Profile')) { Start-CeleritasPS7 -Profile aggressive | Out-Null } else { Start-CeleritasPS7 | Out-Null }; $script:Verdicts.Add("[加速器] Celeritas PS7 已掛(P1–P5;退出還原)") } catch { $script:Verdicts.Add("[加速器] Start-CeleritasPS7 掛不上(" + $_.Exception.Message.Split([char]10)[0] + ")→ fallback 無加速,功能照跑") } }
  else { $script:Verdicts.Add("[加速器] AutoImport 缺席 → fallback(功能照跑,無加速)") }
}

# ---------- ④ 雙軌並行 ----------
function Invoke-VCDualLane {
  param([hashtable[]]$Lanes, [string]$LogDir)
  $MaxMin = if ($MaxMin) { [int]$MaxMin } else { 60 }
  $jobs = @{}
  foreach ($L in $Lanes) { $jobs[$L.id] = Start-ThreadJob -Name $L.id -ScriptBlock $L.run -ArgumentList $L.args; $script:Verdicts.Add("[車道] 啟動 " + $L.id + " · " + $L.zh) }
  $deadline = (Get-Date).AddMinutes($MaxMin)
  while (($jobs.Values | Where-Object { $_.State -in 'NotStarted','Running' }).Count -gt 0) {   # v0104:NotStarted 也算在跑(前版漏了 → 兩道瞬間被收掉、log 空)
    if ((Get-Date) -gt $deadline) { foreach ($k in $jobs.Keys) { if ($jobs[$k].State -in 'NotStarted','Running') { Stop-Job $jobs[$k]; $script:Errors.Add("[逾時] 車道 $k 超過 $MaxMin 分,停") } }; break }
    # v0105:每道車道可寫 <LogDir>\<id>.progress(0..100 [· 文字]);讀出來算百分比 + 動態條
    $parts = @(); $sum = 0
    foreach ($k in ($jobs.Keys | Sort-Object)) { $pf = Join-Path $LogDir ($k + '.progress'); $raw = if (Test-Path $pf) { (Get-Content $pf -Raw -ErrorAction SilentlyContinue) } else { '' }
      $pct = if ($jobs[$k].State -notin 'NotStarted','Running') { 100 } elseif ($raw -match '^\s*(\d{1,3})') { [int]$Matches[1] } else { 0 }
      $txt = if ($raw -match '·\s*(.+)$') { $Matches[1].Trim() } else { '' }; $sum += [Math]::Min(100, $pct)
      $bar = ('█' * [Math]::Floor($pct / 10)) + ('░' * (10 - [Math]::Floor($pct / 10))); $parts += ("$k $bar $pct%" + $(if ($txt) { ' ' + $txt.Substring(0, [Math]::Min(40, $txt.Length)) } else { '' })) }
    $total = [int]($sum / [Math]::Max(1, $jobs.Count)); $live = $parts -join '  ‖  '
    if (Get-Command Show-VCProgress -ErrorAction SilentlyContinue) { try { Show-VCProgress -Activity '雙軌並行' -Status $live -Percent $total } catch { Write-Progress -Activity '雙軌並行' -Status $live -PercentComplete $total } } else { Write-Progress -Activity '雙軌並行' -Status $live -PercentComplete $total }
    Write-Host ("`r  " + (Get-Date -Format HH:mm:ss) + "  " + $live + "   ") -NoNewline
    Start-Sleep -Seconds 2
  }
  Write-Progress -Activity '雙軌並行' -Completed; Write-Host ''
  foreach ($k in $jobs.Keys) { $out = @(Receive-Job $jobs[$k] -Wait 2>&1 | ForEach-Object { "" + $_ }); $out | Set-Content (Join-Path $LogDir ($k + '.log')) -Encoding UTF8
    if ($out.Count -eq 0) { $script:Errors.Add("[$k] 車道零輸出(State $($jobs[$k].State);看 $k.log)") }
    $bad = @($out | Where-Object { $_ -match 'Traceback|\[FAIL\]|\[RED\]|Error|rc [1-9]' }); $good = @($out | Where-Object { $_ -match '\[(OK|GREEN|計)\]|總判|PASS' })
    if ($bad.Count) { $bad | Select-Object -First 4 | ForEach-Object { $script:Errors.Add("[$k] " + $_.Trim().Substring(0, [Math]::Min(160, $_.Trim().Length))) } }
    $good | Select-Object -Last 3 | ForEach-Object { $script:Verdicts.Add("[$k] " + $_.Trim().Substring(0, [Math]::Min(160, $_.Trim().Length))) }
    Remove-Job $jobs[$k] -Force -ErrorAction SilentlyContinue }
}

# ---------- 收尾:黃字貼給 AI · 紅字錯誤(主控台用既有字型 = 安全;HTML 走 FormatLock) ----------
function Show-VCSummary {
  param([string]$Title, [string]$LogDir)
  $y = "`e[93m"; $r = "`e[91m"; $g = "`e[92m"; $d = "`e[90m"; $z = "`e[0m"; $b = "`e[1m"
  Write-Host ""; Write-Host ("$b══════ $Title · $($script:Stamp) ══════$z")
  foreach ($v in $script:Verdicts) { Write-Host ("$y$v$z") }
  if ($script:Errors.Count) { Write-Host ("$r$b── 錯誤 $($script:Errors.Count) 件 ──$z"); foreach ($e in $script:Errors) { Write-Host ("$r$e$z") } } else { Write-Host ("$g── 錯誤 0 件 ──$z") }
  Write-Host ("$d" + "log $LogDir · 黃字 = 貼給 AI · 紅字 = 錯誤 · 綠 = 過 · 灰 = 沒跑$z")
  $pack = @("# $Title $($script:Stamp)") + ($script:Verdicts | ForEach-Object { "- " + $_ }) + @("## 錯誤") + ($script:Errors | ForEach-Object { "- " + $_ })
  $pack | Set-Content (Join-Path $LogDir 'paste.md') -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
  if (Get-Command Invoke-CeleritasFinal -ErrorAction SilentlyContinue) { try { Invoke-CeleritasFinal -Action None } catch { } }
  if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 | Out-Null } catch { } }
}

# ======================= 骨架主體(範例:兩條車道;改這裡) =======================
if (-not $NoCleanup) { Invoke-VCSafeCleanup }
$Run = Initialize-VCTemp; Initialize-VCAccel
$LogDir = Join-Path $VIA ("VIA_Reports\review\ps_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Reg = if ($global:VIARegisterPath) { $global:VIARegisterPath } else { (Get-ChildItem $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName }
$Lanes = @(
  @{ id = 'A'; zh = '範例車道 A(換成你的工作)'; args = @($VIA, $Reg); run = { param($VIA, $Reg) Set-Location $VIA; . $Reg; via-vcgc token 2>&1 } },
  @{ id = 'B'; zh = '範例車道 B(換成你的工作)'; args = @($VIA, $Reg); run = { param($VIA, $Reg) Set-Location $VIA; . $Reg; via-vcgc status 2>&1 } })
Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir
Show-VCSummary -Title 'PS7 Skeleton v0105 示範' -LogDir $LogDir
