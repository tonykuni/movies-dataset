# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Log = '', [int]$Round = 0, [int]$StepSec = 90, [switch]$NoClip,
      [string]$Ladder = '', [string]$UserOk = '', [switch]$Approve, [switch]$LadderStatus, [switch]$LadderReset)
# AI 產出必須接入模板。只動 $PID,關閉即還原。新規定:前段 安全清理 · TEMP · 加速器;收尾 黃字貼 AI · 紅字錯誤。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-AiVerb-v0108.ps1 — v0107 + 改號: 橋 CGC_MDL256 與既有 SubsystemBundle 撞號, 依重號 0 律裁定改 CGC_MDL259 (功能不變)。
#   (v0107 內容照舊) v0106 + 兩件事:
#   [修蟲2] 看門狗 Timer 原是非 daemon 執行緒: 引擎 1 秒跑完, 行程仍等 90 秒計時器 → 反被看門狗記 124。
#          v0107: t.daemon=True — 正常結束立即 rc0; 真卡死照樣 124。
#   [修蟲] Invoke-PyStep 參數原名 $Args 是 PowerShell 自動變數, 簡單函式開跑時被自動變數蓋成空陣列
#          → 空陣列用「管線」餵 ConvertTo-Json 吐 $null → GetBytes($null) 炸 → python 拿不到 argv → IndexError。
#          v0107: 參數改名 $Argv + ConvertTo-Json 改 -InputObject 引數式 (空/單元素一律正確) + null 早炸早報。
#   [梯次] -Ladder <引擎.py> : AI 梯次指令 (MDL257) — TEST→DEBUG→OPTIMIZE→…→ACTIVATE 十三段,
#          一步通過才能下一步; 每呼叫推一段並印結果貼回 AI; -UserOk "備註" 過人工閘; -Approve 過啟用閘。
$ErrorActionPreference = 'Continue'
$VIA = if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'supportive modules'))) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }   # 可攜: 以指令檔所在為根, 作者機路徑僅後備
$dl = "$env:USERPROFILE\Downloads"; Set-Location -LiteralPath $VIA
$env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_FROM_VCGC = 'YES'; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'; $env:VIA_ROOT = $VIA; $env:VIA_LADDER_SEC = "$StepSec"
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()
function Mark([string]$s) { Write-Host ("  " + (Get-Date -Format HH:mm:ss) + "  ▶ " + $s) }
Mark '骨架'; $skel = Get-ChildItem $VIA -Filter 'VeritasCeleritas.PS7.Skeleton-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if ($skel) { $t = Get-Content $skel.FullName -Raw -Encoding UTF8; Invoke-Expression $t.Substring(0, $t.IndexOf('# ======================= 骨架主體')); Invoke-VCSafeCleanup; $null = Initialize-VCTemp; Initialize-VCAccel } else { $script:Verdicts.Add("[骨架] 不在 → 無清理/TEMP/加速器,功能照跑") }
Mark '骨架完'; $LogDir = Join-Path $VIA ("VIA_Reports\review\aiverb_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
function Invoke-PyStep([string]$Id, [string[]]$Argv, [int]$Sec) {   # v0107: $Args→$Argv(自動變數迴避);其餘同 v0105 直呼+python 內看門狗
  $out = Join-Path $LogDir "$Id.out"; Write-Host ("  " + (Get-Date -Format HH:mm:ss) + "  ▶ $Id … ") -NoNewline
  $clean = @($Argv | Where-Object { $null -ne $_ } | ForEach-Object { $_ -replace '^"(.*)"$', '$1' })
  $argvJson = ConvertTo-Json -InputObject $clean -Compress                            # 引數式: 空=[] · 單元素=["x"] · 不經管線無 null
  if (-not $argvJson) { Write-Host 'rc 99 · 0s'; $script:Errors.Add("[$Id] argv 序列化為 null — 通道蟲, 不往下丟"); return @() }
  $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($argvJson))         # base64 argv: PS 原生參數引號不會拆
  $wrap = "import base64,json,os,sys,threading,runpy; a=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); t=threading.Timer($Sec, lambda: (sys.stdout.flush(), os._exit(124))); t.daemon=True; t.start(); sys.argv=a; runpy.run_path(a[0], run_name='__main__')"
  $t0 = Get-Date; $o = @(& python -c $wrap $b64 2>&1 | ForEach-Object { "" + $_ }); $rc = $LASTEXITCODE; $script:PyRc = $rc; $o | Set-Content $out -Encoding UTF8
  Write-Host ("rc $rc · " + [int]((Get-Date) - $t0).TotalSeconds + "s")
  if ($rc -eq 124) { $script:Errors.Add("[看門狗] $Id 超過 $Sec 秒(python 自殺 124)· 最後:" + (($o | Select-Object -Last 1) -join '')) }
  elseif ($rc -notin 0, 2, 3) { $script:Errors.Add("[$Id] rc $rc · " + (($o | Select-Object -Last 2) -join ' | ')) }   # rc3=梯次 WAIT, 不是錯
  return $o }
$eng = "$VIA\supportive modules\registry\CGC_MDL259_AiVerbBridge_v0100.py"
$lad = "$VIA\supportive modules\registry\CGC_MDL257_AiVerbLadder_v0100.py"
foreach ($pair in @(@('CGC_MDL259_AiVerbBridge_v0100.py', $eng), @('CGC_MDL257_AiVerbLadder_v0100.py', $lad))) {
  $src = Join-Path $dl $pair[0]; if (-not (Test-Path $src)) { $src = Join-Path "$dl\aiverb_kit" $pair[0] }
  if (Test-Path $src) { if (-not (Test-Path $pair[1]) -or ((Get-FileHash $pair[1]).Hash -ne (Get-FileHash $src).Hash)) { Copy-Item $src (Split-Path $pair[1]) -Force; $script:Verdicts.Add("[入倉] " + $pair[0]) } } }
if (Test-Path "$dl\aiverb_kit\skills\via-verb-interaction") { New-Item -ItemType Directory -Force -Path "$VIA\skills" | Out-Null; Copy-Item "$dl\aiverb_kit\skills\via-verb-interaction" "$VIA\skills\" -Recurse -Force; $script:Verdicts.Add("[技能] skills\via-verb-interaction 已入") }
# ───────── 梯次模式: 一呼叫推一段, 印結果就收工 (跟 AI 一來一回) ─────────
if ($Ladder) {
  if (-not (Test-Path $lad)) { Write-Host "[缺] $lad" -ForegroundColor Red; exit 2 }
  $target = (Resolve-Path -LiteralPath $Ladder -ErrorAction SilentlyContinue).Path
  if (-not $target) { Write-Host "[錯] 梯次標的不存在: $Ladder" -ForegroundColor Red; exit 2 }
  $cmd = if ($LadderStatus) { 'status' } elseif ($LadderReset) { 'reset' } else { 'step' }
  $argv = @(('"' + $lad + '"'), ('"' + $target + '"'), $cmd)
  if ($cmd -eq 'step' -and $UserOk) { $argv += @('--userok', ('"' + $UserOk + '"')) }
  if ($cmd -eq 'step' -and $Approve) { $argv += '--approve' }
  Mark "梯次 $cmd"
  $o = Invoke-PyStep 'ladder' $argv ([Math]::Max($StepSec, 120))
  Write-Host ''
  foreach ($l in $o) { Write-Host ($(if ($l -match 'FAIL|\[錯\]') { "`e[91m" } elseif ($l -match 'WAIT') { "`e[95m" } elseif ($l -match 'PASS|DONE') { "`e[92m" } else { "`e[93m" }) + $l + "`e[0m") }
  if (-not $NoClip) { try { ($o -join "`n") | Set-Clipboard } catch { } }
  Write-Host "`n[梯次] 貼回包已入剪貼簿 — 貼給 AI, 照 NEXT 行動; 同指令重跑 = 重驗同段 / 過了自動進下一段" -ForegroundColor Cyan
  exit $script:PyRc }   # 傳遞梯次判決: 0=PASS/DONE · 1=FAIL · 3=WAIT · 124=看門狗 (不吞紅)
if (-not (Test-Path $eng)) { $script:Errors.Add("[缺] $eng"); Show-VCSummary -Title 'AI 動詞橋' -LogDir $LogDir; return }
$q = '"' + $eng + '"'
Mark '自測'; $st = Invoke-PyStep 'selftest' @($q, '--selftest') $StepSec | Select-String '\[計\]' | ForEach-Object { $_.Line.Trim() }; foreach ($l in $st) { if ($l -match '[1-9]\d* FAIL') { $script:Errors.Add("[自測] $l") } else { $script:Verdicts.Add("[自測] $l · 加速器橋 " + $(if (Test-Path "$VIA\supportive modules\VIA_SuperAccel_Module.py") { '在(SuperAccel → SUP_MDL737 → 鎖冊 Celeritas)' } else { '缺' })) } }
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
Show-VCSummary -Title 'AI 動詞橋(MDL259)· 貼回包' -LogDir $LogDir
if (-not $NoClip) { try { (@($pack) + @('## 判決') + @($script:Verdicts) + @('## 錯誤') + @($script:Errors)) -join "`n" | Set-Clipboard } catch { } }
