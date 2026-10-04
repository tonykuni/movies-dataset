# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Samples = 'C:\測試樣本報告', [int]$MaxMin = 60, [int]$PerMin = 10, [switch]$NoPush)
# AI 產出必須接入模板。只動 $PID,關閉即還原。新規定:前段 安全清理 · TEMP · 加速器 · 雙軌;收尾 黃字貼 AI · 紅字錯誤。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-FinalRound-v0100.ps1 — 最後一輪(操作員 2026-10-03):
#   軌 A 備份:git tag + bundle → 三系統產出(VIA_Reports 全景/矩陣/實測/ETF/清單)+ 資料庫(duckdb/parquet)zip 到 VIA_Backups\final_<時戳>\;MANIFEST sha256
#   軌 B 補測:上一輪 TIMEOUT(28 支)與被 Ctrl+C 打斷(rc -1073741510 的 5 支)用更大預算重跑(EngineLanes -PerMin 10 · -Only);真紅 7 支留給薄尾
#   收口:檔案位置清單(三系統此刻實掛:總管理器 · 鎖冊工具 · SSOT 冊 · 引擎尾版 · 資料庫;有版號=綠、無版號=黃、缺=紅)→ VIA_FILE_MAP_latest.html/.csv/.json
#         綠的鎖 LKGC tag;紅的錨點進紅字區
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent; Set-Location -LiteralPath $VIA
$env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()
$skel = Get-ChildItem $VIA -Filter 'VeritasCeleritas.PS7.Skeleton-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if (-not $skel) { Write-Host "骨架不在" -ForegroundColor Red; return }
$skelText = Get-Content $skel.FullName -Raw -Encoding UTF8; Invoke-Expression $skelText.Substring(0, $skelText.IndexOf('# ======================= 骨架主體'))
Invoke-VCSafeCleanup; $Run = Initialize-VCTemp; Initialize-VCAccel
$LogDir = Join-Path $VIA ("VIA_Reports\review\final_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Reg = if ($global:VIARegisterPath) { $global:VIARegisterPath } else { (Get-ChildItem $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName }
$lanesPs = (Get-ChildItem $VIA -Filter 'Invoke-VIA-EngineLanes-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName
$Bak = "C:\Users\tonyk\VIA_Backups\final_$($script:Stamp)"; New-Item -ItemType Directory -Force -Path $Bak | Out-Null
$DataHome = if ($env:VIA_DATA_HOME) { $env:VIA_DATA_HOME } else { 'C:\Users\tonyk\VIA System\via_database' }

# 上一輪矩陣:哪些是 TIMEOUT / 被打斷(-1073741510 = STATUS_CONTROL_C_EXIT,不是引擎壞)/ 真紅
$prev = "$VIA\VIA_Reports\review\ENGINE_READINESS_latest.csv"; $retry = @(); $trueRed = @()
if (Test-Path $prev) { $rows = Import-Csv $prev -Encoding UTF8
  $retry = @($rows | Where-Object { $_.燈 -eq 'TIMEOUT' -or $_.rc -eq '-1073741510' } | ForEach-Object { $_.引擎 -replace '_v\d{4}$', '' })
  $trueRed = @($rows | Where-Object { $_.燈 -eq 'RED' -and $_.rc -ne '-1073741510' }) }
$script:Verdicts.Add("[上輪] 補測 $($retry.Count) 支(逾時 / 被 Ctrl+C 打斷)· 真紅 $($trueRed.Count) 支留薄尾")

$LanesDef = @(
  @{ id = 'A-backup'; zh = '備份:tag · bundle · 產出 · 資料庫 · manifest'; args = @($VIA, $Repo, $Bak, $DataHome, $LogDir); run = { param($VIA, $Repo, $Bak, $DataHome, $LogDir) $pf = Join-Path $LogDir 'A-backup.progress'
      Set-Content $pf '5 · git tag' -Encoding UTF8; $tag = "final/" + (Split-Path $Bak -Leaf); git -C $Repo tag -f $tag HEAD 2>&1 | Out-Null; "tag $tag @ " + (git -C $Repo rev-parse --short=12 HEAD)
      Set-Content $pf '15 · git bundle' -Encoding UTF8; git -C $Repo bundle create (Join-Path $Bak 'repo.bundle') --all 2>&1 | Out-Null; "bundle " + [Math]::Round((Get-Item (Join-Path $Bak 'repo.bundle')).Length / 1MB, 1) + " MB"
      Set-Content $pf '35 · 產出 zip' -Encoding UTF8; $outs = @('ssot_panorama', 'vcgc', 'review', 'vrn', 'vdf', 'panorama', 'lkgc', 'toolprobe', 'rungate') | ForEach-Object { Join-Path "$VIA\VIA_Reports" $_ } | Where-Object { Test-Path $_ }
      Compress-Archive -Path $outs -DestinationPath (Join-Path $Bak 'VIA_Reports_outputs.zip') -CompressionLevel Optimal -Force; "產出 zip " + [Math]::Round((Get-Item (Join-Path $Bak 'VIA_Reports_outputs.zip')).Length / 1MB, 1) + " MB · 夾 " + $outs.Count
      Set-Content $pf '60 · 資料庫 zip' -Encoding UTF8; $dbs = @(Get-ChildItem "$VIA\functional modules\VDF\output_hub", $DataHome -Recurse -Include *.duckdb, *.parquet -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 0 })
      if ($dbs.Count) { Compress-Archive -Path $dbs.FullName -DestinationPath (Join-Path $Bak 'databases.zip') -CompressionLevel Fastest -Force; "資料庫 zip " + [Math]::Round((Get-Item (Join-Path $Bak 'databases.zip')).Length / 1MB, 1) + " MB · 檔 " + $dbs.Count } else { "[FAIL] 資料庫 0 檔(output_hub / VIA_DATA_HOME 都空)" }
      Set-Content $pf '85 · manifest' -Encoding UTF8; Get-ChildItem $Bak -File | ForEach-Object { [pscustomobject]@{ file = $_.Name; mb = [Math]::Round($_.Length / 1MB, 2); sha256 = (Get-FileHash $_.FullName).Hash } } | ConvertTo-Json | Set-Content (Join-Path $Bak 'MANIFEST.json') -Encoding UTF8
      Set-Content $pf '100 · 備份完' -Encoding UTF8; "[OK] 備份 → $Bak" } },
  @{ id = 'B-retest'; zh = "補測 $($retry.Count) 支(更大預算)"; args = @($VIA, $Reg, $lanesPs, $retry, $PerMin, $MaxMin, $LogDir); run = { param($VIA, $Reg, $lanesPs, $retry, $PerMin, $MaxMin, $LogDir) Set-Location $VIA; . $Reg | Out-Null; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'; $pf = Join-Path $LogDir 'B-retest.progress'
      if (-not $retry.Count -or -not $lanesPs) { Set-Content $pf '100 · 無需補測' -Encoding UTF8; "[OK] 無需補測"; return }
      & $lanesPs -Family @('vdf', 'vrn') -Only ($retry -join ',') -PerMin $PerMin -MaxMin ([Math]::Max(10, $MaxMin - 5)) -ProgressFile $pf 2>&1 | Select-String '\[(計|RED|GREEN|NODATA|TIMEOUT)\]|GREEN \d|RED \d|TIMEOUT \d' | ForEach-Object { $_.Line.Trim() } | Select-Object -Last 6 } })
Invoke-VCDualLane -Lanes $LanesDef -LogDir $LogDir

# ===== 檔案位置清單(三系統此刻實掛;有版號綠 · 無版號黃 · 缺紅)=====
$map = [System.Collections.Generic.List[object]]::new()
function Add-Map([string]$fam, [string]$kind, [string]$name, [string]$path) { $exists = $path -and (Test-Path $path); $ver = if ($name -match '_v(\d{4})') { 'v' + $Matches[1] } elseif ($name -match '_v(\d+\.\d+\.\d+)') { 'v' + $Matches[1] } else { '' }
  $lamp = if (-not $exists) { 'RED' } elseif (-not $ver) { 'YELLOW' } else { 'GREEN' }; $map.Add([pscustomobject]@{ 系統 = $fam; 類 = $kind; 名 = $name; 版 = $(if ($ver) { $ver } else { '無版號' }); 燈 = $lamp; 位置 = $(if ($path) { $path.Replace("$VIA\", '') } else { '-' }) }) }
foreach ($p in @(@('VCGC', '總管理器', "$VIA\supportive modules\registry", 'CGC_SystemManager_v*.py'), @('VCGC', '主控台', "$VIA\supportive modules\registry", 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py'), @('VDF', '總管理器', "$VIA\functional modules\VDF", 'VDF_SystemManager_v*.py'), @('VRN', '總管理器', "$VIA\functional modules\VRN", 'VRN_SystemManager_v*.py'), @('SUP', '總管理器', "$VIA\supportive modules", 'VIA_SYSTEM_MANAGER_v*.py'))) {
  $f = Get-ChildItem $p[2] -Filter $p[3] -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; Add-Map $p[0] $p[1] $(if ($f) { $f.Name } else { $p[3] }) $(if ($f) { $f.FullName } else { '' }) }
$lock = Get-ChildItem "$VIA\supportive modules\registry" -Filter 'VIA_ToolVersion_Lock_v*.json' | Sort-Object Name | Select-Object -Last 1
if ($lock) { Add-Map 'SUP' '鎖冊' $lock.Name $lock.FullName; try { $lk = Get-Content $lock.FullName -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($prop in $lk.PSObject.Properties) { if ($prop.Value -is [pscustomobject] -and $prop.Value.path) { Add-Map 'SUP' ('鎖冊工具·' + $prop.Name) (Split-Path $prop.Value.path -Leaf) (Join-Path $VIA $prop.Value.path) } elseif ($prop.Name -eq 'tools' -and $prop.Value) { foreach ($t in $prop.Value.PSObject.Properties) { $tp = $t.Value.path; if ($tp) { Add-Map 'SUP' ('鎖冊工具·' + $t.Name) (Split-Path $tp -Leaf) (Join-Path $VIA $tp) } } } } } catch { } }
foreach ($b in @(@('VCGC', "$VIA\supportive modules\registry", 'VIA_Policy_Laws_SSOT_v*.json'), @('VCGC', "$VIA\supportive modules\registry", 'VIA_Central_Synonym_Regex_v*.json'), @('VCGC', "$VIA\supportive modules\registry", 'VIA_SSOT_SynonymUnion_v*.json'), @('VCGC', "$VIA\supportive modules\registry", 'VIA_VCGC_FunctionInventory_SSOT_v*.json'), @('VCGC', "$VIA\supportive modules\registry", 'VIA_UI_FormatLock_v*.json'), @('VCGC', "$VIA\supportive modules\registry", 'VIA_SSOT_ItemNumbers_v*.json'), @('VCGC', "$VIA\supportive modules\registry", 'VIA_IndustryUnifiedMap_v*.json'), @('VDF', "$VIA\functional modules\VDF", 'VDF_InputUniverse_SSOT_v*.json'), @('VDF', "$VIA\functional modules\VDF", 'VDF_DataArchitecture_Rule_SSOT_v*.json'), @('VDF', "$VIA\functional modules\VDF", 'VDF_AdjPrice_Rule_SSOT_v*.json'), @('VDF', "$VIA\functional modules\VDF", 'VDF_Param_Registry_v*.json'), @('VRN', "$VIA\functional modules\VRN", 'VRN_FrameFlow_SSOT_v*.json'), @('VRN', "$VIA\functional modules\VRN", 'VIA_VRN_ExtractRules_SSOT_v*.json'), @('VRN', "$VIA\functional modules\VRN", 'VRN_FieldRules_SSOT_v*.json'), @('VRN', "$VIA\functional modules\VRN", 'VRN_Param_Registry_v*.json'), @('VRN', "$VIA\functional modules\VRN\knowledge", 'SYNONYM_LIBRARY_v*.json'))) {
  $f = Get-ChildItem $b[1] -Filter $b[2] -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; Add-Map $b[0] 'SSOT冊' $(if ($f) { $f.Name } else { $b[2] }) $(if ($f) { $f.FullName } else { '' }) }
foreach ($d in @(@('VDF', "$VIA\functional modules\VDF\output_hub\universe\VDF_Universe.duckdb"), @('VDF', "$VIA\functional modules\VDF\output_hub\tw_index\VDF_TWIndex_Daily.duckdb"), @('VDF', (Join-Path $DataHome 'VDF_TWEquity_Daily.duckdb')), @('VDF', (Join-Path $DataHome 'ActiveTWETF.duckdb')), @('VDF', (Join-Path $DataHome 'vdf_tw_market.duckdb')), @('VRN', "$VIA\functional modules\VRN\output_hub"))) { Add-Map $d[0] '資料庫' (Split-Path $d[1] -Leaf) $d[1] }
$engTails = @(); foreach ($p in @(@('VCGC', "$VIA\supportive modules\registry", 'CGC_MDL*_v????.py'), @('VDF', "$VIA\functional modules\VDF\engine", 'VDF_ENG*_v????.py'), @('VRN', "$VIA\functional modules\VRN", 'VRN_ENG*_v????.py'), @('SUP', "$VIA\supportive modules", 'SUP_MDL*_v????.py'))) {
  $g = Get-ChildItem $p[1] -Filter $p[2] -File -Recurse -ErrorAction SilentlyContinue | Group-Object { $_.BaseName -replace '_v\d{4}$', '' }; foreach ($grp in $g) { $f = $grp.Group | Sort-Object Name | Select-Object -Last 1; Add-Map $p[0] '引擎尾版' $f.Name $f.FullName }; $engTails += "$($p[0]) $($g.Count)" }
$csv = "$VIA\VIA_Reports\review\VIA_FILE_MAP_latest.csv"; $map | Export-Csv $csv -NoTypeInformation -Encoding UTF8
$map | ConvertTo-Json -Depth 3 | Set-Content ($csv -replace '\.csv$', '.json') -Encoding UTF8
$pal = @{ GREEN = '#16a34a'; YELLOW = '#f59e0b'; RED = '#dc2626'; GRAY = '#9ca3af' }
$h = [Text.StringBuilder]::new(); [void]$h.Append("<!doctype html><html><head><meta charset='utf-8'><title>VIA 檔案位置清單</title><style>body{font:11px Arial,sans-serif;background:#fff;color:#111827;padding:12px}table{border-collapse:collapse}td,th{border:1px solid #e0e0e0;padding:3px 6px}th{background:#f7f7f7;position:sticky;top:0}@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}.lamp{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.15)}.lamp.GREEN{background:$($pal.GREEN)}.lamp.YELLOW{background:$($pal.YELLOW)}.lamp.RED{background:$($pal.RED);animation:via-blink 1.8s ease-in-out infinite}.lamp.GRAY{background:$($pal.GRAY)}</style></head><body><h2>VIA 檔案位置清單 · 三系統此刻實掛 · $($script:Stamp)</h2><p><i class='lamp GREEN'></i>有版號 $(@($map | Where-Object 燈 -eq 'GREEN').Count) <i class='lamp YELLOW'></i>無版號 $(@($map | Where-Object 燈 -eq 'YELLOW').Count) <i class='lamp RED'></i>缺 $(@($map | Where-Object 燈 -eq 'RED').Count) · 引擎尾版 $($engTails -join ' · ') · 色 = VIA_UI_FormatLock v0101</p><table><tr><th>燈</th><th>系統</th><th>類</th><th>名</th><th>版</th><th>位置</th></tr>")
foreach ($r in ($map | Sort-Object { @{RED = 0; YELLOW = 1; GREEN = 2 }[$_.燈] }, 系統, 類, 名)) { [void]$h.Append("<tr><td><i class='lamp $($r.燈)'></i>$($r.燈)</td><td>$($r.系統)</td><td>$($r.類)</td><td>$([Net.WebUtility]::HtmlEncode($r.名))</td><td>$($r.版)</td><td>$([Net.WebUtility]::HtmlEncode($r.位置))</td></tr>") }
[void]$h.Append("</table></body></html>"); $html = $csv -replace '\.csv$', '.html'; [IO.File]::WriteAllText($html, $h.ToString(), [Text.UTF8Encoding]::new($false)); Copy-Item $csv, $html, ($csv -replace '\.csv$', '.json') $Bak -Force
$script:Verdicts.Add("[清單] $($map.Count) 項 · 綠 $(@($map | Where-Object 燈 -eq 'GREEN').Count) · 無版號 $(@($map | Where-Object 燈 -eq 'YELLOW').Count) · 缺 $(@($map | Where-Object 燈 -eq 'RED').Count) → VIA_Reports\review\VIA_FILE_MAP_latest.html(已入備份)")
foreach ($r in ($map | Where-Object { $_.燈 -eq 'RED' })) { $script:Errors.Add("[缺] $($r.系統) $($r.類) $($r.名) · $($r.位置)") }
foreach ($r in ($map | Where-Object { $_.燈 -eq 'YELLOW' -and $_.類 -in '總管理器', '鎖冊工具', 'SSOT冊' })) { $script:Verdicts.Add("[無版號] $($r.系統) $($r.類) $($r.名)(L04 要補版號)") }

# ===== 綠的鎖 · 紅的錨 =====
if (Test-Path $prev) { $rows2 = Import-Csv $prev -Encoding UTF8; $green = @($rows2 | Where-Object { $_.燈 -eq 'GREEN' }); $red2 = @($rows2 | Where-Object { $_.燈 -eq 'RED' -and $_.rc -ne '-1073741510' })
  $ledger = "$VIA\VIA_Reports\lkgc\ENGINE_LOCK_LEDGER.jsonl"; New-Item -ItemType Directory -Force -Path (Split-Path $ledger) | Out-Null; $sha = git -C $Repo rev-parse --short=12 HEAD; $n = 0
  foreach ($g in $green) { $stem = $g.引擎 -replace '_v\d{4}$', ''; $ver = if ($g.引擎 -match '_v(\d{4})$') { $Matches[1] } else { '0000' }; git -C $Repo tag -f "lkgc/$stem/v$ver" HEAD 2>&1 | Out-Null; $n++
    Add-Content $ledger ('{"at":"' + (Get-Date -Format o) + '","engine":"' + $g.引擎 + '","tag":"lkgc/' + $stem + '/v' + $ver + '","sha":"' + $sha + '","verdict":"GREEN","by":"FinalRound-v0100"}') -Encoding UTF8 }
  if (-not $NoPush) { git -C $Repo push -q origin --tags 2>&1 | Out-Null }; $script:Verdicts.Add("[鎖] $n 支綠引擎 LKGC tag @ $sha · 帳 VIA_Reports\lkgc\ENGINE_LOCK_LEDGER.jsonl")
  foreach ($r in $red2) { $script:Errors.Add("[真紅] $($r.家族) $($r.引擎) · $($r.判決) · 錨 $($r.錨點)") } }
$lay = Get-Content "$VIA\VIA_Reports\vrn\layout\*latest*.json" -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
foreach ($l in (Get-Content (Join-Path $LogDir 'A-backup.log') -Encoding UTF8 -ErrorAction SilentlyContinue)) { if ($l -match 'FAIL') { $script:Errors.Add("[備份] $l") } elseif ($l) { $script:Verdicts.Add("[備份] $l") } }
Show-VCSummary -Title '最後一輪:備份 · 清單 · 補測 · 鎖(FinalRound v0100)' -LogDir $LogDir
try { $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $html; $psi.UseShellExecute = $true; $null = [System.Diagnostics.Process]::Start($psi) } catch { }
