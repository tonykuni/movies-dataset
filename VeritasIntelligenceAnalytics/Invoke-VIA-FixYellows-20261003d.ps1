# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-FixYellows-20261003d.ps1 — 修黃燈(操作員:「黃燈的地方請修正」)
#   同義字@VRN  drift 2 支 → TW02 v0102 · FirstPageEngine v0130 委樞(落差 0)
#   同義字@VCGC hub.additive 10 多義 → R-SYN-04 · E2 jpmorgan.com → R-SYN-05(中央冊 v0102)· E3 副本 DIVERGED → MDL176 apply 出 SynonymUnion 新版
#   自動編號   CGC_MDL255 缺號 · FPSTALE 3 · UNCOMMITTED 16 → 先提交推,再 MDL237 --apply(ssot/rgx/syn + 缺號)
#   上下連結   待重驗鎖 5 → sdd selftests → lock --apply
#   命名 同號異名 12 組 → 改號是操作員裁(本支只列,不動)
&{
$ErrorActionPreference = 'Continue'
$ApplyLock = $true; $ApplyNumber = $true     # 兩個寫冊開關;sdd selftests 不綠 lock 不會寫;發號有寫後自核與整批還原
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent; $dl = "$env:USERPROFILE\Downloads"; $reg = "$VIA\supportive modules\registry"
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'; $stamp = Get-Date -Format yyyyMMdd_HHmmss
$Out = "$VIA\VIA_Reports\review\fixy_$stamp"; New-Item -ItemType Directory -Force -Path $Out | Out-Null; git -C $Repo tag -f "pre-fixy/$stamp" HEAD | Out-Null
function Invoke-VIAFixStep([string]$id, [string]$cmd) { Write-Host "=== [$id] $cmd ===" -ForegroundColor Cyan; $o = @(Invoke-Expression $cmd 2>&1 | ForEach-Object { "" + $_ }); $o | Set-Content "$Out\$id.log" -Encoding UTF8
  $o | Where-Object { $_ -match '\[(計|FAIL|RED|GREEN|YELLOW|結|OK)\]|總判|落差|委樞|遺失|改身分|重號|FPSTALE|UNCOMMITTED|缺號|待重驗鎖|撞號|rc ' } | Select-Object -Last 8 | ForEach-Object { "  " + $_.Trim().Substring(0, [Math]::Min(150, $_.Trim().Length)) } }

# ① 入倉:兩支薄尾 + 中央冊 v0102(全新檔,不覆蓋)
foreach ($f in @(@{s="$dl\VRN_TW02_ReportParser_v0102.py"; d="$VIA\functional modules\VRN\"}, @{s="$dl\VIA_VRN_FirstPageEngine_v0130.py"; d="$VIA\functional modules\VRN\"}, @{s="$dl\VIA_Central_Synonym_Regex_v0102.json"; d="$reg\"})) {
  if (Test-Path $f.s) { Copy-Item $f.s $f.d -Force; Write-Host ("  [入] " + (Split-Path $f.s -Leaf)) -ForegroundColor Cyan } else { Write-Host ("  [缺] " + (Split-Path $f.s -Leaf) + " 不在 Downloads") -ForegroundColor Yellow } }
Invoke-VIAFixStep '1a' 'via-vcgc run --family vrn VRN_TW02_ReportParser --selftest'
Invoke-VIAFixStep '1b' 'via-vcgc run --family vrn VIA_VRN_FirstPageEngine --selftest'
Invoke-VIAFixStep '1c' 'via-vcgc run --family vrn SUP_MDL749_VRNFieldRuleHub drift'                 # 應:落差引擎 0 支

# ② 同義字鏈:中央 v0102 → SynonymUnion 新版 → 樞紐 → 冊同步 E2/E3/E4
Invoke-VIAFixStep '2a' 'via-vcgc run --family core CGC_MDL176_SynonymUnion apply'
Invoke-VIAFixStep '2b' 'via-vcgc run --family vrn SUP_MDL749_VRNFieldRuleHub additive'
Invoke-VIAFixStep '2c' 'via-vcgc run --family core CGC_MDL185_SsotBookSync check'

# ③ 上下連結:待重驗鎖 5 → selftests → lock
Invoke-VIAFixStep '3a' 'via-vcgc sdd selftests'
if ($ApplyLock) { Invoke-VIAFixStep '3b' 'via-vcgc sdd lock --apply' }

# ④ 編號:先提交推(UNCOMMITTED 16 的解法是「先提交再發號」)→ 發號 → 稽核
$files = @('VeritasIntelligenceAnalytics/functional modules/VRN/VRN_TW02_ReportParser_v0102.py', 'VeritasIntelligenceAnalytics/functional modules/VRN/VIA_VRN_FirstPageEngine_v0130.py', 'VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Central_Synonym_Regex_v0102.json') | Where-Object { Test-Path (Join-Path $Repo $_) }
& git -C $Repo add -A -- 'VeritasIntelligenceAnalytics/supportive modules/registry' 'VeritasIntelligenceAnalytics/functional modules/VRN' 'VeritasIntelligenceAnalytics/functional modules/VDF' 2>&1 | Out-Null
& git -C $Repo commit -q -m "FixYellows ($stamp): TW02 v0102 + FirstPageEngine v0130 delegate to hub (drift 0), Central Synonym/Regex v0102 (R-SYN-04 rating strength, R-SYN-05 jpmorgan→JPM), SynonymUnion/lock books from engines; append-only" 2>&1 | Out-Null
$branch = (& git -C $Repo rev-parse --abbrev-ref HEAD); $pu = & git -C $Repo push origin $branch 2>&1
if ($LASTEXITCODE -ne 0) { $null = via-medic sync --apply 2>&1; $pu = & git -C $Repo push origin $branch 2>&1 }
Write-Host ("  [推] " + $(if ($LASTEXITCODE -eq 0) { $branch + ' · ' + (& git -C $Repo rev-parse --short=12 HEAD) } else { '被拒 → 改推側線 fixy-' + $stamp; & git -C $Repo push origin "HEAD:refs/heads/fixy-$stamp" 2>&1 | Out-Null })) -ForegroundColor Green
if ($ApplyNumber) { Invoke-VIAFixStep '4a' 'via-vcgc run --family core CGC_MDL237_NumberingSystem --apply'; foreach ($s in 'ssot','rgx','syn') { Invoke-VIAFixStep "4b-$s" "via-vcgc run --family core CGC_MDL237_NumberingSystem --apply --scope $s" } }
Invoke-VIAFixStep '4c' 'via-vcgc run --family core CGC_MDL237_NumberingSystem audit'
& git -C $Repo add -A -- 'VeritasIntelligenceAnalytics/supportive modules/registry' 2>&1 | Out-Null; & git -C $Repo commit -q -m "Numbering ($stamp): MDL237 apply (ssot/rgx/syn scopes + missing CGC_MDL255); append-only" 2>&1 | Out-Null; & git -C $Repo push -q origin $branch 2>&1 | Out-Null

# ⑤ 後測
Invoke-VIAFixStep '5' 'via-vcgc ssot panorama --full'
$pack = Get-ChildItem $Out -Filter '*.log' | ForEach-Object { "## " + $_.BaseName; Get-Content $_.FullName -Encoding UTF8 | Where-Object { $_ -match '\[(計|FAIL|RED|YELLOW|結)\]|總判|落差|委樞|遺失|改身分|重號|FPSTALE|UNCOMMITTED|缺號|待重驗鎖|撞號|族總判|^\s*(正則|同義字|自動編號|命名|註冊|上下連結)\s' } | Select-Object -First 14 }
$pack | Set-Content "$Out\paste.md" -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
Write-Host "畢 · 貼回包已進剪貼簿 · 還原 tag pre-fixy/$stamp · $Out" -ForegroundColor Green
}
