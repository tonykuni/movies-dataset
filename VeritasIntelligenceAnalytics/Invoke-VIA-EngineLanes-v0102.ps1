# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string[]]$Family = @('vdf', 'vrn'), [int]$Lanes = 0, [int]$PerMin = 4, [int]$MaxMin = 30, [string]$Verb = '--selftest', [string]$Only = '')
# param 必須是第一個語句(PS 規則);加速器橋接在它後面,章的文字判準不受影響
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# v0101(2026-10-03):燈號改用 VIA_UI_FormatLock 鎖定四燈(綠 #15803d · 黃 #b45309 · 紅 #b91c1c · 灰 #6b7280 未跑/暫存/未來)+ 青 NODATA;白底 Arial 11px;其餘一字不動
# Invoke-VIA-EngineLanes-v0102.ps1 — 個別單引擎 · 多軌同時實測輸出(操作員 2026-10-03)
#   每支 VDF / VRN 引擎尾版各自一支 VCGC run(--selftest 或 -Verb 指定),N 條車道並行(預設 核心數-1,上限 6;VCGC 教訓帳有跨行程鎖),
#   每道一個 log,看門狗(每支 -PerMin 分 · 整體 -MaxMin 分;逾時只停本檔自己起的子行程),就緒矩陣 CSV + HTML;
#   紅的引擎從 log 抓 Traceback 最後一個 File "…", line N → AST 錨點(檔:行),配 via-ai-fix <檔>:<行> 逐支修。
#   先印上一輪 ROUND2 三個紅步(3a VDF_SystemManager · 3c DataFrameLock · 3d C-github_panorama)的判決行(digest),不用翻 log。
# 用法:& .\Invoke-VIA-EngineLanes-v0102.ps1 [-Family vdf,vrn] [-Lanes 4] [-PerMin 4] [-MaxMin 30] [-Verb --selftest] [-Only ENG08]
$ErrorActionPreference = 'Continue'
$VIA = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'; $env:VIA_FROM_VCGC = 'YES'
$stamp = Get-Date -Format yyyyMMdd_HHmmss; $Out = "$VIA\VIA_Reports\review\engine_lanes\$stamp"; New-Item -ItemType Directory -Force -Path $Out | Out-Null
if ($Lanes -le 0) { $Lanes = [Math]::Min(6, [Math]::Max(1, [Environment]::ProcessorCount - 1)) }
$py = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source
$V = (Get-ChildItem "$VIA\supportive modules\registry" -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' | Sort-Object { [int]([regex]::Match($_.BaseName,'_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1).FullName

# ⓪ 上一輪三個紅步的判決行(digest,不翻全文)
$r2 = Get-ChildItem "$VIA\VIA_Reports\review\round" -Filter 'ROUND2_*.log' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($r2) {
  Write-Host ("=== 上一輪 " + $r2.Name + " 紅步判決行 ===") -ForegroundColor Cyan
  $txt = Get-Content $r2.FullName -Encoding UTF8; $sec = ''
  foreach ($l in $txt) { if ($l -match '^=== \[(\S+)\] ') { $sec = $Matches[1]; continue }
    if ($sec -in @('3a','3c','3d') -and $l -match 'Traceback|Error|錯|FAIL|RED|RuntimeError|File "|rc[= ]\s*[1-9]|\[計\]|選項|用法|usage|unknown|不認得') { Write-Host ("  [" + $sec + "] " + $l.Trim().Substring(0, [Math]::Min(160, $l.Trim().Length))) -ForegroundColor Yellow } }
}

# ① 引擎清單:同 stem 取尾版;-Only 前綴篩
$targets = @()
if ('vdf' -in $Family) { $targets += Get-ChildItem "$VIA\functional modules\VDF\engine" -Filter 'VDF_ENG*_v*.py' -File | Group-Object { $_.BaseName -replace '_v\d{4}$','' } | ForEach-Object { [pscustomobject]@{ fam='vdf'; stem=$_.Name; file=($_.Group | Sort-Object Name)[-1] } } }
if ('vrn' -in $Family) { $targets += Get-ChildItem "$VIA\functional modules\VRN" -Filter 'VRN_ENG*_v*.py' -File | Group-Object { $_.BaseName -replace '_v\d{4}$','' } | ForEach-Object { [pscustomobject]@{ fam='vrn'; stem=$_.Name; file=($_.Group | Sort-Object Name)[-1] } } }
if ($Only) { $targets = @($targets | Where-Object { $_.stem -like "*$Only*" }) }
Write-Host ("=== 多軌單引擎實測:" + $targets.Count + " 支 · " + $Lanes + " 道 · 每支 " + $PerMin + " 分 · 整體 " + $MaxMin + " 分 · 動詞 " + $Verb + " ===") -ForegroundColor Cyan

# ② 多軌派送(每支一個子行程;看門狗)
$queue = [System.Collections.Generic.Queue[object]]::new(); $targets | ForEach-Object { $queue.Enqueue($_) }
$running = @{}; $done = [System.Collections.Generic.List[object]]::new(); $deadline = (Get-Date).AddMinutes($MaxMin); $n = $targets.Count
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
  while ($queue.Count -gt 0 -and $running.Count -lt $Lanes -and (Get-Date) -lt $deadline) {
    $t = $queue.Dequeue(); $lg = Join-Path $Out ($t.stem + '.log'); $er = Join-Path $Out ($t.stem + '.err.log')
    $argLine = '"' + $V + '" run --family ' + $t.fam + ' ' + $t.stem + ' ' + $Verb
    try { $p = Start-Process -FilePath $py -ArgumentList $argLine -WorkingDirectory $VIA -NoNewWindow -PassThru -RedirectStandardOutput $lg -RedirectStandardError $er
          $running[$t.stem] = [pscustomobject]@{ t=$t; proc=$p; log=$lg; err=$er; t0=(Get-Date) } }
    catch { $done.Add([pscustomobject]@{ 家族=$t.fam; 引擎=$t.file.BaseName; 燈='RED'; rc=-1; 秒=0; 判決=('起不來:' + $_.Exception.Message); 錨點='' }) }
  }
  foreach ($k in @($running.Keys)) { $r = $running[$k]
    $timedOut = -not $r.proc.HasExited -and ((Get-Date) - $r.t0).TotalMinutes -gt $PerMin
    if ($timedOut) { try { $r.proc.Kill() } catch { } }
    if ($r.proc.HasExited -or $timedOut) {
      $rc = if ($timedOut) { 124 } else { $r.proc.ExitCode }
      $o = @(if (Test-Path $r.log) { Get-Content $r.log -Encoding UTF8 }) + @(if (Test-Path $r.err) { Get-Content $r.err -Encoding UTF8 })
      $last = (@($o | Where-Object { $_ -match 'selftest|自測|PASS|FAIL|\[計\]|rc=|RuntimeError|Error:|Traceback' } | Select-Object -Last 1) -join '')
      $anchor = ''; $tb = @($o | Where-Object { $_ -match '^\s*File "(.+?)", line (\d+)' })
      if ($tb.Count) { $m = [regex]::Match($tb[-1], 'File "(.+?)", line (\d+)'); $anchor = (($m.Groups[1].Value -replace [regex]::Escape($VIA + '\'), '') + ':' + $m.Groups[2].Value) }
      $lamp = if ($rc -eq 0) { 'GREEN' } elseif ($rc -eq 2) { 'NODATA' } elseif ($rc -eq 4) { 'GATE' } elseif ($rc -eq 124) { 'TIMEOUT' } else { 'RED' }
      $done.Add([pscustomobject]@{ 家族=$r.t.fam; 引擎=$r.t.file.BaseName; 燈=$lamp; rc=$rc; 秒=[int]((Get-Date)-$r.t0).TotalSeconds; 判決=$last.Substring(0,[Math]::Min(120,$last.Length)); 錨點=$anchor })
      $running.Remove($k)
      Write-Host ("  [" + $lamp + "] " + $r.t.file.BaseName + " · rc " + $rc + " · " + [int]((Get-Date)-$r.t0).TotalSeconds + "s" + $(if ($anchor) { " · " + $anchor } else { "" })) -ForegroundColor $(if ($lamp -eq 'GREEN') {'Green'} elseif ($lamp -eq 'RED' -or $lamp -eq 'TIMEOUT') {'Red'} else {'Yellow'})
    }
  }
  if ((Get-Date) -ge $deadline -and $queue.Count -gt 0) { while ($queue.Count -gt 0) { $t = $queue.Dequeue(); $done.Add([pscustomobject]@{ 家族=$t.fam; 引擎=$t.file.BaseName; 燈='SKIP'; rc='-'; 秒=0; 判決=("整體上限 $MaxMin 分到頂"); 錨點='' }) } }
  Write-Progress -Activity '多軌單引擎實測' -Status ("完成 " + $done.Count + "/" + $n + " · 進行中 " + ($running.Keys -join ' ') + " · 剩 " + [int]($deadline - (Get-Date)).TotalSeconds + "s") -PercentComplete ([int](100 * $done.Count / [Math]::Max(1, $n)))
  Start-Sleep -Milliseconds 800
}
Write-Progress -Activity '多軌單引擎實測' -Completed

# ③ 矩陣:CSV + HTML(紅的帶錨點與 via-ai-fix 指令)· 錨點檔
$csv = Join-Path $Out 'ENGINE_READINESS.csv'; $done | Sort-Object 家族, 燈, 引擎 | Export-Csv $csv -NoTypeInformation -Encoding UTF8
$cnt = @{}; foreach ($l in 'GREEN','NODATA','GATE','RED','TIMEOUT','SKIP') { $cnt[$l] = @($done | Where-Object 燈 -eq $l).Count }
$enc = [System.Net.WebUtility]
$h = [System.Text.StringBuilder]::new()
$null = $h.Append("<!doctype html><html><head><meta charset='utf-8'><title>Engine Lanes $stamp</title><style>body{font:11px Arial,sans-serif;background:#ffffff;color:#111827;margin:0;padding:16px}h1{color:#111827;font-size:16px;margin:0 0 6px}table{border-collapse:collapse;font-size:11px;background:#fff}td,th{border:1px solid #e0e0e0;padding:4px 8px;vertical-align:top;max-width:620px}th{background:#f7f7f7;position:sticky;top:0}.lamp{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}.GREEN{color:#15803d}.GREEN .lamp,.lamp.GREEN{background:#15803d}.YELLOW,.AMBER,.GATE{color:#b45309}.YELLOW .lamp,.lamp.YELLOW,.lamp.AMBER,.lamp.GATE{background:#b45309}.RED,.TIMEOUT{color:#b91c1c}.RED .lamp,.lamp.RED,.lamp.TIMEOUT{background:#b91c1c}.GRAY,.ABSENT,.SKIP,.HOLD,.DORMANT,.UNTESTED{color:#6b7280}.lamp.GRAY,.lamp.ABSENT,.lamp.SKIP,.lamp.HOLD,.lamp.DORMANT,.lamp.UNTESTED{background:#6b7280}.NODATA{color:#0e7490}.lamp.NODATA{background:#0e7490}.legend span{margin-right:14px}</style></head><body>")
$null = $h.Append("<h1>個別單引擎 · 多軌同時實測 · $stamp</h1><p class='legend'><span class='GREEN'><i class='lamp GREEN'></i>綠 過</span><span class='YELLOW'><i class='lamp YELLOW'></i>黃 要人裁 / 待鎖</span><span class='RED'><i class='lamp RED'></i>紅 壞</span><span class='GRAY'><i class='lamp GRAY'></i>灰 未跑 / 暫存 / 未來可能用到(SKIP · HOLD · ABSENT · DORMANT)</span><span class='NODATA'><i class='lamp NODATA'></i>青 沒料(誠實,不冒充綠)</span> · 色 = VIA_UI_FormatLock_v0100 鎖定值</p><p>" + $targets.Count + " 支 · " + $Lanes + " 道 · 動詞 " + $enc::HtmlEncode($Verb) + " · 綠 " + $cnt['GREEN'] + " · 沒料 " + $cnt['NODATA'] + " · 閘 " + $cnt['GATE'] + " · 紅 " + $cnt['RED'] + " · 逾時 " + $cnt['TIMEOUT'] + " · 未跑 " + $cnt['SKIP'] + "</p><table><tr><th>家族</th><th>引擎</th><th>燈</th><th>rc</th><th>秒</th><th>判決</th><th>錨點(檔:行)</th><th>修</th></tr>")
foreach ($d in ($done | Sort-Object @{e='燈';desc=$false}, 家族, 引擎)) { $null = $h.Append("<tr><td>" + $d.家族 + "</td><td>" + $enc::HtmlEncode($d.引擎) + "</td><td class='" + $d.燈 + "'><i class='lamp " + $d.燈 + "'></i>" + $d.燈 + "</td><td>" + $d.rc + "</td><td>" + $d.秒 + "</td><td>" + $enc::HtmlEncode($d.判決) + "</td><td>" + $enc::HtmlEncode($d.錨點) + "</td><td>" + $(if ($d.錨點) { "<code>via-ai-fix " + $enc::HtmlEncode($d.錨點) + "</code>" } else { "" }) + "</td></tr>") }
$null = $h.Append("</table><p>每支 log:" + $enc::HtmlEncode($Out) + "</p></body></html>")
$html = Join-Path $Out 'ENGINE_READINESS.html'; [IO.File]::WriteAllText($html, $h.ToString(), [Text.UTF8Encoding]::new($false))
Copy-Item $html "$VIA\VIA_Reports\review\ENGINE_READINESS_latest.html" -Force; Copy-Item $csv "$VIA\VIA_Reports\review\ENGINE_READINESS_latest.csv" -Force
@("# 引擎錨點 $stamp · 定位=AST精準(Traceback 檔:行)") + ($done | Where-Object { $_.錨點 } | ForEach-Object { $_.錨點 + "  " + $_.燈 + "  " + $_.引擎 + "  " + $_.判決 }) | Set-Content (Join-Path $Out 'ANCHORS.txt') -Encoding UTF8
try { $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $html; $psi.UseShellExecute = $true; $null = [System.Diagnostics.Process]::Start($psi) } catch { }

# ④ 貼回包:只收非綠 + 錨點
$pack = @("# ENGINE LANES $stamp · " + $targets.Count + " 支 · 綠 " + $cnt['GREEN'] + " 沒料 " + $cnt['NODATA'] + " 閘 " + $cnt['GATE'] + " 紅 " + $cnt['RED'] + " 逾時 " + $cnt['TIMEOUT'] + " 未跑 " + $cnt['SKIP']) + ($done | Where-Object 燈 -ne 'GREEN' | Sort-Object 燈 | ForEach-Object { "- [" + $_.燈 + "] " + $_.家族 + " " + $_.引擎 + " · rc " + $_.rc + $(if ($_.錨點) { " · " + $_.錨點 } else { "" }) + " · " + $_.判決 })
$pack | Set-Content (Join-Path $Out 'paste.md') -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
Write-Host ("=== 畢 · 綠 " + $cnt['GREEN'] + " · 沒料 " + $cnt['NODATA'] + " · 紅 " + $cnt['RED'] + " · 逾時 " + $cnt['TIMEOUT'] + " · 未跑 " + $cnt['SKIP'] + " · 矩陣 " + $html + " · 貼回包已進剪貼簿 ===") -ForegroundColor Cyan
