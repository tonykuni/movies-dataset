# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([switch]$NetConsent, [int]$MaxMin = 90, [string]$Samples = 'C:\測試樣本報告', [string]$Since = '2022-06-01', [switch]$SkipVcgc)
# param 必須是第一個語句(PS 規則);加速器橋接在它後面,章的文字判準不受影響
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章 · PY 帶 ACCEL-BRIDGE(鎖冊尾版)。L107:TEMP 核外 · sha/輪分夾 · 滾動 5 輪。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# v0101(2026-10-03):燈號改用 VIA_UI_FormatLock 鎖定四燈 + 青 NODATA;SKIP/HOLD/ABSENT 歸灰;其餘一字不動
# Invoke-VIA-RunAll-VcgcVdfVrn-v0102.ps1 — VCGC 全流程跑一回 → VDF(官方 TWSE/TPEX 塊 ‖ yfinance 塊)‖ VRN(按序 · C:\測試樣本報告 · 增量自 2022-06-01)同時啟動
#   操作員 2026-10-03:「所有 py 用最新版號加速器 · ps 用加速模組 · VDF 檢查分兩塊 · VRN 按序輸出 · 增量擷取庫自 2022-06-01 · 同步啟動 · 用 temp 取代記憶體」
#   車道 = 子 pwsh(各自載 Register 尾版 → 全部 via-* 正主);每道自己的 TEMP 夾與 log;整體看門狗;就緒矩陣 HTML;Final 模組不關機(FinalAction None)。
$ErrorActionPreference = 'Continue'
$VIA = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'
$auto = Join-Path $VIA 'supportive modules\VeritasCeleritas.PS7.AutoImport.ps1'; if (Test-Path $auto) { . $auto }      # 母模組 + Addon 全部進來(有就用,沒有就 fallback)
function Narrate([string]$s, [string]$c = 'Gray') { if (Get-Command Write-VCNarrate -ErrorAction SilentlyContinue) { Write-VCNarrate $s } else { Write-Host $s -ForegroundColor $c } }
if (Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Start-CeleritasPS7 -Profile aggressive | Out-Null } catch { } }   # P1–P5 行程治理(只動 $PID,退出還原)

# ⓪ TEMP 核外(L107):本輪一夾;DuckDB / Polars / Python 暫存全指過去;滾動只留最近 5 輪,刪了記帳
$stamp = Get-Date -Format yyyyMMdd_HHmmss
$TempRoot = if ($env:VIA_TEMP_ROOT) { $env:VIA_TEMP_ROOT } else { Join-Path $env:LOCALAPPDATA 'Temp\VIA_progress' }
$Run = Join-Path $TempRoot "runall_$stamp"; New-Item -ItemType Directory -Force -Path $Run | Out-Null
$env:VIA_TEMP_ROOT = $TempRoot; $env:TMP = $Run; $env:TEMP = $Run; $env:TMPDIR = $Run; $env:POLARS_TEMP_DIR = $Run; $env:VIA_DUCKDB_TEMP_DIR = $Run; $env:VIA_SPILL_TO_DISK = '1'
$env:VIA_VRN_SINCE = $Since; $env:VIA_VDF_SINCE = $Since
if ($NetConsent) { $env:VIA_NET_CONSENT = 'YES' }                                                                        # 同意閘是你的手;預設不開
$old = Get-ChildItem $TempRoot -Directory -Filter 'runall_*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -Skip 5
foreach ($o in $old) { $mb = [Math]::Round(((Get-ChildItem $o.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB), 1); Remove-Item $o.FullName -Recurse -Force -ErrorAction SilentlyContinue
  Add-Content (Join-Path $TempRoot 'purge_ledger.jsonl') ('{"at":"' + (Get-Date -Format o) + '","purged":"' + $o.Name + '","mb":' + $mb + ',"rule":"L107 keep_last=5","by":"Invoke-VIA-RunAll-VcgcVdfVrn-v0102"}') }
Narrate "=== TEMP $Run · 滾動留 5 輪(清 $($old.Count) 輪) · 同意閘 $(if ($NetConsent) {'YES'} else {'未開(--NetConsent)'}) · 增量自 $Since ===" Cyan
$Out = Join-Path $VIA "VIA_Reports\review\runall\$stamp"; New-Item -ItemType Directory -Force -Path $Out | Out-Null
$rows = [System.Collections.Generic.List[object]]::new()
function Step([string]$id, [string]$name, [scriptblock]$b) { $t = Get-Date; $o = @(& $b 2>&1 | ForEach-Object { "" + $_ }); $rc = $LASTEXITCODE
  "=== [$id] $name ===" | Add-Content "$Out\vcgc.log"; $o | Add-Content "$Out\vcgc.log"
  $last = (@($o | Where-Object { $_ -match '\[(GREEN|RED|YELLOW|OK|FAIL|WARN|NODATA|計)|總判|交接閘|全功能串測' } | Select-Object -Last 1) -join '')
  $lamp = if ($rc -eq 0) { 'GREEN' } elseif ($rc -eq 2) { 'YELLOW' } elseif ($rc -eq 3) { 'ABSENT' } elseif ($rc -eq 4) { 'GATE' } else { 'RED' }
  $rows.Add([pscustomobject]@{ 段='VCGC'; 步=$id; 名=$name; 燈=$lamp; rc=$rc; 秒=[int]((Get-Date)-$t).TotalSeconds; 判決=$last.Substring(0,[Math]::Min(140,$last.Length)) })
  Narrate ("  [$id] $name · $lamp · rc $rc · " + [int]((Get-Date)-$t).TotalSeconds + "s") $(if ($lamp -eq 'GREEN') {'Green'} elseif ($lamp -eq 'RED') {'Red'} else {'Yellow'}) }

# ① VCGC 全流程跑一回(照步驟矩陣次序:token → enter → 狀態 → 串測 → SSOT 全景 → 哨兵 → 交接閘)
if (-not $SkipVcgc) {
  Step '1' 'token'          { via-vcgc token }
  Step '2' 'enter --card'   { via-vcgc enter --card --no-pull }
  Step '3' 'status'         { via-vcgc status }
  Step '4' 'test --quick'   { via-vcgc test --quick }
  Step '5' 'ssot panorama'  { via-vcgc ssot panorama }
  Step '6' 'guard'          { via-vcgc guard }
  Step '7' 'handoff check'  { via-vcgc handoff check }
}

# ② 三條車道同時啟動(子 pwsh 各自載 Register 尾版;每道自己的 TEMP 夾與 log)
$reg = if ($global:VIARegisterPath) { $global:VIARegisterPath } else { (Get-ChildItem $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName }
$lanes = @(
  @{ id='VDF-A'; zh='VDF 官方塊(TWSE / TPEX + 其他)'; cmds=@(
      'via-vcgc run --family vdf VDF_ENG232_TWIndexOfficial --selftest',
      'via-vcgc run --family vdf VDF_ENG087_MarketListGovernance diff',
      'via-vcgc run --family vdf VDF_ENG051_ActiveTWETF_Holdings --selftest',
      'via-vcgc run --family vdf VDF_ENG094_ActiveETFActivity --selftest',
      'via-vcgc run --family vdf VDF_SystemManager universe',
      'via-vdfchain run --resume') },
  @{ id='VDF-B'; zh='VDF yfinance 塊(+ 其他)'; cmds=@(
      'via-vcgc run --family vdf VDF_ENG049_FiveDayFetch --selftest',
      'via-vcgc run --family vdf VDF_ENG082_FinStatements --selftest',
      'via-vcgc run --family vdf VDF_ENG060_AdjPriceLayer --selftest',
      'via-vcgc run --family vdf VDF_ENG054_TWDailyBackfill --selftest',
      'via-vcgc run --family vdf VDF_ENG064_HistoryBackfill --selftest',
      'via-market-lists') },
  @{ id='VRN'; zh='VRN 按序(樣本 · 分類 → 版面 → 實體 → 鏈 → 結構庫)'; cmds=@(
      'via-vcgc run --family vrn VRN_SystemManager --selftest',
      ('via-vcgc run --family vrn VRN_ENG393_DocClassVerify classify --samples "' + $Samples + '"'),
      ('via-vcgc run --family vrn VRN_ENG394_LayoutRestore restore --in "' + $Samples + '" --pages 1'),
      ('via-vcgc run --family vrn VRN_ENG396_ReportEntities run --in "' + $Samples + '" --pages 1-2'),
      'via-vcgc run --family vrn VRN_SystemManager outputs',
      'via-vrnchain run --resume',
      'via-vcgc run --family vrn VRN_ENG073_ReportStructuredDB --selftest') })
$procs = @{}
foreach ($L in $lanes) {
  $ld = Join-Path $Run $L.id; New-Item -ItemType Directory -Force -Path $ld | Out-Null; $log = Join-Path $Out ($L.id + '.log')
  $body = @("# CELERITAS-TEMPLATE-JOIN v1", "#Requires -Version 7.0", "# [VIA:PS-ACCEL] 車道腳本(本輪暫存,由母腳本產生;L106)", '$ErrorActionPreference = "Continue"',
            ('Set-Location -LiteralPath "' + $VIA + '"'), ('$env:TMP = "' + $ld + '"; $env:TEMP = "' + $ld + '"; $env:TMPDIR = "' + $ld + '"; $env:POLARS_TEMP_DIR = "' + $ld + '"; $env:VIA_DUCKDB_TEMP_DIR = "' + $ld + '"'),
            ('. "' + $reg + '"'), ('$rcs = @()'))
  foreach ($c in $L.cmds) { $body += ('Write-Host "=== ' + $c.Replace('"', '`"') + ' ==="; $t = Get-Date; ' + $c + ' 2>&1 | ForEach-Object { "" + $_ }; $rcs += ("' + $c.Replace('"', '`"').Replace("'", "''") + '|" + $LASTEXITCODE + "|" + [int]((Get-Date) - $t).TotalSeconds)') }
  $body += ('$rcs | Set-Content "' + (Join-Path $Out ($L.id + '.rc')) + '" -Encoding UTF8')
  $ps1 = Join-Path $ld ('lane_' + $L.id + '.ps1'); $body | Set-Content $ps1 -Encoding UTF8
  $p = Start-Process pwsh -ArgumentList @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ps1) -WorkingDirectory $VIA -NoNewWindow -PassThru -RedirectStandardOutput $log -RedirectStandardError ($log + '.err')
  $procs[$L.id] = @{ proc=$p; t0=(Get-Date); zh=$L.zh }
  Narrate ("  [啟動] " + $L.id + " · " + $L.zh + " · pid " + $p.Id + " · log " + $log) Cyan
}
# ③ 看門狗 + 進度
$deadline = (Get-Date).AddMinutes($MaxMin)
while (($procs.Values | Where-Object { -not $_.proc.HasExited }).Count -gt 0) {
  if ((Get-Date) -gt $deadline) { foreach ($k in $procs.Keys) { if (-not $procs[$k].proc.HasExited) { try { $procs[$k].proc.Kill() } catch { }; Narrate ("  [逾時] " + $k + " 整體上限 $MaxMin 分,停本道") Red } }; break }
  $live = ($procs.Keys | Where-Object { -not $procs[$_].proc.HasExited }) -join ' '
  if (Get-Command Show-VCProgress -ErrorAction SilentlyContinue) { try { Show-VCProgress -Activity '三道同啟' -Status $live -Percent ([int](100 * ($procs.Count - ($live -split ' ').Count) / $procs.Count)) } catch { } }
  else { Write-Progress -Activity '三道同啟(VDF-A ‖ VDF-B ‖ VRN)' -Status ("進行中 " + $live + " · 剩 " + [int]($deadline - (Get-Date)).TotalSeconds + "s") -PercentComplete ([int](100 * ($procs.Count - ($live -split ' ').Count) / $procs.Count)) }
  Start-Sleep -Seconds 3
}
Write-Progress -Activity '三道同啟' -Completed
foreach ($k in $procs.Keys) { $rcf = Join-Path $Out ($k + '.rc')
  if (Test-Path $rcf) { foreach ($l in (Get-Content $rcf -Encoding UTF8)) { $parts = $l -split '\|'; if ($parts.Count -ge 3) { $rc = [int]$parts[1]
      $rows.Add([pscustomobject]@{ 段=$k; 步=''; 名=$parts[0]; 燈=$(if ($rc -eq 0) {'GREEN'} elseif ($rc -eq 2) {'NODATA'} elseif ($rc -eq 4) {'GATE'} elseif ($rc -eq 3) {'ABSENT'} else {'RED'}); rc=$rc; 秒=[int]$parts[2]; 判決='' }) } } }
  else { $rows.Add([pscustomobject]@{ 段=$k; 步=''; 名=$procs[$k].zh; 燈='RED'; rc=-1; 秒=[int]((Get-Date)-$procs[$k].t0).TotalSeconds; 判決='車道沒留 rc 檔(看 ' + $k + '.log.err)' }) } }

# ④ 矩陣 HTML + 貼回包
$enc = [System.Net.WebUtility]; $h = [System.Text.StringBuilder]::new()
$null = $h.Append("<!doctype html><html><head><meta charset='utf-8'><title>RunAll $stamp</title><style>body{font:11px Arial,sans-serif;background:#ffffff;color:#111827;margin:0;padding:16px}h1{color:#111827;font-size:16px;margin:0 0 6px}table{border-collapse:collapse;font-size:11px;background:#fff}td,th{border:1px solid #e0e0e0;padding:4px 8px;vertical-align:top;max-width:620px}th{background:#f7f7f7;position:sticky;top:0}.lamp{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}.GREEN{color:#15803d}.GREEN .lamp,.lamp.GREEN{background:#15803d}.YELLOW,.AMBER,.GATE{color:#b45309}.YELLOW .lamp,.lamp.YELLOW,.lamp.AMBER,.lamp.GATE{background:#b45309}.RED,.TIMEOUT{color:#b91c1c}.RED .lamp,.lamp.RED,.lamp.TIMEOUT{background:#b91c1c}.GRAY,.ABSENT,.SKIP,.HOLD,.DORMANT,.UNTESTED{color:#6b7280}.lamp.GRAY,.lamp.ABSENT,.lamp.SKIP,.lamp.HOLD,.lamp.DORMANT,.lamp.UNTESTED{background:#6b7280}.NODATA{color:#0e7490}.lamp.NODATA{background:#0e7490}.legend span{margin-right:14px}</style></head><body>")
$g = @($rows | Where-Object 燈 -eq 'GREEN').Count; $r = @($rows | Where-Object 燈 -eq 'RED').Count
$null = $h.Append("<h1>VCGC 一回 + VDF-A ‖ VDF-B ‖ VRN 同啟 · $stamp</h1><p class='legend'><span class='GREEN'><i class='lamp GREEN'></i>綠 過</span><span class='YELLOW'><i class='lamp YELLOW'></i>黃 要人裁 / 待鎖</span><span class='RED'><i class='lamp RED'></i>紅 壞</span><span class='GRAY'><i class='lamp GRAY'></i>灰 未跑 / 暫存 / 未來可能用到(SKIP · HOLD · ABSENT · DORMANT)</span><span class='NODATA'><i class='lamp NODATA'></i>青 沒料(誠實,不冒充綠)</span> · 色 = VIA_UI_FormatLock_v0100 鎖定值</p><p>綠 $g · 紅 $r · 其他 $($rows.Count - $g - $r) · TEMP $($enc::HtmlEncode($Run)) · 增量自 $Since · 同意閘 $(if ($NetConsent) {'YES'} else {'未開'})</p><table><tr><th>段</th><th>步</th><th>指令</th><th>燈</th><th>rc</th><th>秒</th><th>判決</th></tr>")
foreach ($x in $rows) { $null = $h.Append("<tr><td>$($x.段)</td><td>$($x.步)</td><td>$($enc::HtmlEncode($x.名))</td><td class='$($x.燈)'><i class='lamp $($x.燈)'></i>$($x.燈)</td><td>$($x.rc)</td><td>$($x.秒)</td><td>$($enc::HtmlEncode($x.判決))</td></tr>") }
$null = $h.Append("</table><p>log:$($enc::HtmlEncode($Out))</p></body></html>")
$html = Join-Path $Out 'RUNALL.html'; [IO.File]::WriteAllText($html, $h.ToString(), [Text.UTF8Encoding]::new($false)); Copy-Item $html "$VIA\VIA_Reports\review\RUNALL_latest.html" -Force
$rows | Export-Csv (Join-Path $Out 'RUNALL.csv') -NoTypeInformation -Encoding UTF8
$pack = @("# RUNALL $stamp · 綠 $g 紅 $r") + ($rows | Where-Object 燈 -ne 'GREEN' | ForEach-Object { "- [" + $_.燈 + "] " + $_.段 + " " + $_.名 + " · rc " + $_.rc + " · " + $_.秒 + "s · " + $_.判決 })
$pack | Set-Content (Join-Path $Out 'paste.md') -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
try { $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $html; $psi.UseShellExecute = $true; $null = [System.Diagnostics.Process]::Start($psi) } catch { }
$rows | Format-Table 段,名,燈,rc,秒 -AutoSize | Out-String -Width 170 | Write-Host
Narrate "=== 畢 · 矩陣 $html · 貼回包已進剪貼簿 · 本輪 TEMP 留著給中斷接續,第 6 輪起自動清 ===" Cyan
if (Get-Command Invoke-CeleritasFinal -ErrorAction SilentlyContinue) { try { Invoke-CeleritasFinal -Action None } catch { } }   # Final 模組:鏈尾,不關機
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 | Out-Null } catch { } }
