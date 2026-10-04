# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-InstallBooks-20261003c.ps1 — 冊入倉:政策 v0102 · VRN 擷取規則 v0100 · VDF 調整價規則 v0100 · 中央同義字/正則 v0101 · FunctionInventory v0135(已在就略過)
#   + 容器端 VDF 單引擎矩陣(vdf_lanes zip)解到 VIA_Reports\review\vdf_lanes_main 當對照(本機只備查) → books 驗律數 · 衝突行 → registry-sync --apply → 提交 · 推
&{
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent
$dl = "$env:USERPROFILE\Downloads"; $reg = "$VIA\supportive modules\registry"; $stamp = Get-Date -Format yyyyMMdd_HHmmss
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'
$bk = "$env:USERPROFILE\VIA_Backups\books_$stamp"; New-Item -ItemType Directory -Force -Path $bk | Out-Null; git -C $Repo tag -f "pre-books/$stamp" HEAD | Out-Null

# ① 驗:JSON 可解析 · 政策 v0102 前 106 條 = v0101 一字不差 · 中央冊 v0101 前 7 同義字 / 12 regex = v0100 一字不差
$chk = python -c @"
import json,sys
r=r'$reg'; dl=r'$dl'
a=json.load(open(r+r'\VIA_Policy_Laws_SSOT_v0101.json',encoding='utf-8')); b=json.load(open(dl+r'\VIA_Policy_Laws_SSOT_v0102.json',encoding='utf-8'))
ok1=len(b['laws'])==108 and [l['id'] for l in b['laws'][-2:]]==['L109','L110'] and all(x==y for x,y in zip(a['laws'],b['laws']) if x['id']!='L107') and b['laws'][[l['id'] for l in b['laws']].index('L107')]['zh'].endswith(a['laws'][[l['id'] for l in a['laws']].index('L107')]['zh'])
c=json.load(open(r+r'\VIA_Central_Synonym_Regex_v0100.json',encoding='utf-8')); d=json.load(open(dl+r'\VIA_Central_Synonym_Regex_v0101.json',encoding='utf-8'))
ok2=all(d['synonyms'][k]==v for k,v in c['synonyms'].items()) and all(d['regex'][k]==v for k,v in c['regex'].items())
for f in ('VIA_VRN_ExtractRules_SSOT_v0100.json','VDF_AdjPrice_Rule_SSOT_v0100.json'): json.load(open(dl+'\\'+f,encoding='utf-8'))
print('OK' if ok1 and ok2 else 'BAD', len(b['laws']), len(d['synonyms']), len(d['regex']))
"@
Write-Host "  [驗] $chk" -ForegroundColor $(if ($chk -like 'OK*') {'Green'} else {'Red'}); if ($chk -notlike 'OK*') { return }

# ② 入倉(全部新檔,不覆蓋任何既有版)+ 備份下載件
$plan = @(
  @{ src = "$dl\VIA_Policy_Laws_SSOT_v0102.json";        dst = "$reg\" },
  @{ src = "$dl\VIA_Central_Synonym_Regex_v0101.json";   dst = "$reg\" },
  @{ src = "$dl\VIA_VCGC_FunctionInventory_SSOT_v0135.json"; dst = "$reg\" },
  @{ src = "$dl\VIA_VRN_ExtractRules_SSOT_v0100.json";   dst = "$VIA\functional modules\VRN\" },
  @{ src = "$dl\VDF_AdjPrice_Rule_SSOT_v0100.json";      dst = "$VIA\functional modules\VDF\" })
$files = @()
foreach ($p in $plan) { if (-not (Test-Path $p.src)) { Write-Host ("  [缺] " + (Split-Path $p.src -Leaf)) -ForegroundColor Yellow; continue }
  Copy-Item $p.src $bk -Force; $dst = Join-Path $p.dst (Split-Path $p.src -Leaf)
  if ((Test-Path $dst) -and ((Get-FileHash $dst).Hash -eq (Get-FileHash $p.src).Hash)) { Write-Host ("  [同] " + (Split-Path $dst -Leaf) + " 已在") -ForegroundColor DarkGray }
  else { Copy-Item $p.src $dst -Force; Write-Host ("  [入] " + $dst.Replace($VIA + '\', '')) -ForegroundColor Cyan }
  $files += ('VeritasIntelligenceAnalytics/' + $dst.Replace($VIA + '\', '').Replace('\', '/')) }
if (Test-Path "$dl\vdf_lanes_main12e21cb.zip") { Expand-Archive "$dl\vdf_lanes_main12e21cb.zip" "$VIA\VIA_Reports\review\vdf_lanes_main" -Force; Write-Host "  [對照] 容器端 VDF 單引擎矩陣 → VIA_Reports\review\vdf_lanes_main\vdf_lanes\(本機備查,不進 git)" -ForegroundColor DarkGray }

# ③ VCGC 讀到了嗎:律 108 · [衝突] 行不該再有 L107
via-vcgc books 2>&1 | Select-String '^\[政策\] 第二步|^\s*\[衝突\]' | ForEach-Object { Write-Host ("  " + $_.Line.Trim()) }
# ④ 登冊 + 哨兵
via-vcgc registry-sync --apply 2>&1 | Select-String '元件自動編號冊|撞號|APPLIED' | ForEach-Object { Write-Host ("  " + $_.Line.Trim()) }
via-vcgc guard 2>&1 | Select-String '^\s*\[計\]|FAIL' | ForEach-Object { Write-Host ("  " + $_.Line.Trim()) }

# ⑤ 提交 · 推(只帶這幾本冊)
$files += 'VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0135.json'
$files = $files | Sort-Object -Unique | Where-Object { Test-Path (Join-Path $Repo $_) }
& git -C $Repo add -- @files 2>&1 | Out-Null
& git -C $Repo commit -q -m "Books ($stamp): Policy Laws v0102 (+L109 VRN extract six rules, +L110 adj-price factor, L107 clarified verbatim-kept), Central Synonym/Regex v0101 (+70 namespaced synonyms, +80 shared regex, 3 rulings), VRN ExtractRules v0100, VDF AdjPrice Rule v0100, FunctionInventory v0135; append-only" -- @files 2>&1 | Out-Null
$branch = (& git -C $Repo rev-parse --abbrev-ref HEAD); $pu = & git -C $Repo push origin $branch 2>&1
if ($LASTEXITCODE -ne 0) { $null = via-medic sync --apply 2>&1; $pu = & git -C $Repo push origin $branch 2>&1 }
if ($LASTEXITCODE -eq 0) { Write-Host ("  [推] " + $branch + " · " + (& git -C $Repo rev-parse --short=12 HEAD)) -ForegroundColor Green }
else { $side = "books-$stamp"; & git -C $Repo push origin "HEAD:refs/heads/$side" 2>&1 | Out-Null; Write-Host ("  [推] 改推側線 " + $side) -ForegroundColor Yellow }
Write-Host "  畢 · 還原依據 tag pre-books/$stamp · 備份 $bk" -ForegroundColor DarkGray
}
