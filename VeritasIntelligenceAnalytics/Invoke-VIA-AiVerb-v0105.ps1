# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Log = '', [int]$Round = 0, [int]$StepSec = 90, [switch]$NoClip)
# AI 產出必須接入模板。只動 $PID,關閉即還原。新規定:前段 安全清理 · TEMP · 加速器;收尾 黃字貼 AI · 紅字錯誤。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-AiVerb-v0105.ps1 — 任何執行輸出 → classify(紅三類)→ 教訓帳 → paste(濾噪 · NEXT 來自分類)→ round(JSON)→ 剪貼簿。
#   v0102:接骨架(清理 · TEMP · 加速器 Celeritas PS7)· 每個 python 步驟都有看門狗(超過 -StepSec 秒 = 殺掉記紅,不卡斷)· 進度列
$ErrorActionPreference = 'Continue'; $VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $dl = "$env:USERPROFILE\Downloads"; Set-Location -LiteralPath $VIA
$env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_FROM_VCGC = 'YES'; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()
function Mark([string]$s) { Write-Host ("  " + (Get-Date -Format HH:mm:ss) + "  ▶ " + $s) }
Mark '骨架'; $skel = Get-ChildItem $VIA -Filter 'VeritasCeleritas.PS7.Skeleton-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if ($skel) { $t = Get-Content $skel.FullName -Raw -Encoding UTF8; Invoke-Expression $t.Substring(0, $t.IndexOf('# ======================= 骨架主體')); Invoke-VCSafeCleanup; $null = Initialize-VCTemp; Initialize-VCAccel } else { $script:Verdicts.Add("[骨架] 不在 → 無清理/TEMP/加速器,功能照跑") }
Mark '骨架完'; $LogDir = Join-Path $VIA ("VIA_Reports\review\aiverb_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
function Invoke-PyStep([string]$Id, [string[]]$Args, [int]$Sec) {   # v0105:直接 & python(你機器上 T-F 驗過 1 秒回);看門狗放在 python 自己裡面(Timer → os._exit 124),PS 側不包 Job、不重導向
  $out = Join-Path $LogDir "$Id.out"; Write-Host ("  " + (Get-Date -Format HH:mm:ss) + "  ▶ $Id … ") -NoNewline
  $argv = @($Args | ForEach-Object { $_ -replace '^"(.*)"$', '$1' }); $argvJson = ($argv | ConvertTo-Json -Compress); if ($argv.Count -eq 1) { $argvJson = "[$argvJson]" }
  $wrap = "import json,os,sys,threading,runpy; a=json.loads(sys.argv[1]); threading.Timer($Sec, lambda: (sys.stdout.flush(), os._exit(124))).start(); sys.argv=a; runpy.run_path(a[0], run_name='__main__')"
  $t0 = Get-Date; $o = @(& python -c $wrap $argvJson 2>&1 | ForEach-Object { "" + $_ }); $rc = $LASTEXITCODE; $o | Set-Content $out -Encoding UTF8
  Write-Host ("rc $rc · " + [int]((Get-Date) - $t0).TotalSeconds + "s")
  if ($rc -eq 124) { $script:Errors.Add("[看門狗] $Id 超過 $Sec 秒(python 自殺 124)· 最後:" + (($o | Select-Object -Last 1) -join '')) }
  elseif ($rc -notin 0, 2) { $script:Errors.Add("[$Id] rc $rc · " + (($o | Select-Object -Last 2) -join ' | ')) }
  return $o }
$eng = "$VIA\supportive modules\registry\CGC_MDL256_AiVerbBridge_v0100.py"
if (Test-Path "$dl\CGC_MDL256_AiVerbBridge_v0100.py") { if (-not (Test-Path $eng) -or ((Get-FileHash $eng).Hash -ne (Get-FileHash "$dl\CGC_MDL256_AiVerbBridge_v0100.py").Hash)) { Copy-Item "$dl\CGC_MDL256_AiVerbBridge_v0100.py" (Split-Path $eng) -Force; $script:Verdicts.Add("[入倉] CGC_MDL256_AiVerbBridge_v0100.py") } }
if (Test-Path "$dl\aiverb_kit\skills\via-verb-interaction") { New-Item -ItemType Directory -Force -Path "$VIA\skills" | Out-Null; Copy-Item "$dl\aiverb_kit\skills\via-verb-interaction" "$VIA\skills\" -Recurse -Force; $script:Verdicts.Add("[技能] skills\via-verb-interaction 已入") }
if (-not (Test-Path $eng)) { $script:Errors.Add("[缺] $eng"); Show-VCSummary -Title 'AI 動詞橋' -LogDir $LogDir; return }
$q = '"' + $eng + '"'
Mark '自測'; $st = Invoke-PyStep 'selftest' @($q, '--selftest') $StepSec | Select-String '\[計\]' | ForEach-Object { $_.Line.Trim() }; foreach ($l in $st) { if ($l -match 'FAIL') { $script:Errors.Add("[自測] $l") } else { $script:Verdicts.Add("[自測] $l · 加速器橋 " + $(if (Test-Path "$VIA\supportive modules\VIA_SuperAccel_Module.py") { '在(SuperAccel → SUP_MDL737 → 鎖冊 Celeritas)' } else { '缺' })) } }
if (-not $Log) { $Log = (Get-ChildItem "$VIA\VIA_Reports\review\*\paste.md" -ErrorAction SilentlyContinue | Where-Object { $_.DirectoryName -notlike '*aiverb_*' } | Sort-Object LastWriteTime | Select-Object -Last 1).FullName }   # v0103:不遞迴(review 下千檔在 OneDrive 會慢到像卡住)
if (-not $Log -or -not (Test-Path $Log)) { $script:Errors.Add("[log] 沒有可壓的 log(-Log 指一個)"); Show-VCSummary -Title 'AI 動詞橋' -LogDir $LogDir; return }
$script:Verdicts.Add("[log] " + $Log.Replace("$VIA\", ''))
Mark "log = $Log"
# ① classify 先
$csv = "$VIA\VIA_Reports\review\ENGINE_READINESS_latest.csv"; $clsRaw = Invoke-PyStep 'classify' @($q, 'classify', ('"' + $(if (Test-Path $csv) { $csv } else { $Log }) + '"')) $StepSec
$next = ($clsRaw | Where-Object { $_ -like 'NEXT:*' } | Select-Object -Last 1) -replace '^NEXT:\s*', ''; if (-not $next) { $next = '看紅字' }
foreach ($l in $clsRaw) { if ($l -and $l -notlike 'NEXT:*') { $script:Verdicts.Add("[分類] " + $l.Trim()) } }
# ② 教訓帳(真紅各查)
$clsJson = Get-ChildItem "$VIA\VIA_Reports\aiverb" -Filter 'classify_*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
if ($clsJson) { try { $c = Get-Content $clsJson.FullName -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($tr in $c.TRUE) { $key = ($tr.engine -replace '_v\d{4}$', ''); $hist = Invoke-PyStep "lesson_$key" @($q, 'lesson', 'get', $key) 30; $n = @($hist | Where-Object { $_ -match '"key"' }).Count; if ($n -ge 2) { $script:Verdicts.Add("[教訓] $key 已 $n 次 → AI 先讀 lesson get $key 再出薄尾") }; $script:Verdicts.Add("[真紅] $($tr.engine) · 錨 $($tr.anchor)") } } catch { } }
Mark 'paste'
# ③ paste(NEXT 來自分類)
$pack = Invoke-PyStep 'paste' @($q, 'paste', ('"' + $Log + '"'), '--max', '300', '--next', ('"' + $next + '"')) $StepSec
# ④ round
if ($Round -gt 0) { $null = Invoke-PyStep 'round' @($q, 'round', 'write', "$Round", '--paste', ('"' + $Log + '"'), $(if ($clsJson) { '--classify' } else { $null }), $(if ($clsJson) { ('"' + $clsJson.FullName + '"') } else { $null })) $StepSec; $script:Verdicts.Add("[round] VIA_Reports\aiverb\ROUND_$('{0:D2}' -f $Round).json") }
Mark '收尾'; Write-Host ''; foreach ($l in $pack) { Write-Host ($(if ($l -match '^- \[(FAIL|RED|真紅|紅|缺|起)\]|Traceback|^## 錯誤') { "`e[91m" } elseif ($l -like 'NEXT:*') { "`e[1m`e[93m" } else { "`e[93m" }) + $l + "`e[0m") }
$script:Verdicts.Add("[NEXT] $next")
Show-VCSummary -Title 'AI 動詞橋(MDL256)· 貼回包' -LogDir $LogDir
if (-not $NoClip) { try { (@($pack) + @('## 判決') + @($script:Verdicts) + @('## 錯誤') + @($script:Errors)) -join "`n" | Set-Clipboard } catch { } }
