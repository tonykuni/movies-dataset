# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-Round3-Close.ps1 — 全景黃燈收口(2026-10-03 f):
#   註冊@VCGC 新 16 變 5 → registry-sync --apply
#   同義字@VCGC hub.additive 10 多義 → 聯集冊新版加 10 條 rating 裁定(R-SYN-04:粗桶;accumulate/add=ADD)+ E3 FPSTALE(SynonymUnion v0100 指紋)一起消
#   自動編號 缺號 3(CGC_MDL255 v0101 · TW02 v0102 · FirstPageEngine v0130)→ 先提交 → MDL237 --apply → audit
#   env RED(步 7)→ 印 CGC_MDL230 探針紅列 + EnvManager 總判(給根因,不猜)
#   universe 冊 v0103(每欄 display:Title Case)+ VDF_DataArchitecture_Rule v0100 入倉登冊
&{
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent; $dl = "$env:USERPROFILE\Downloads"; $reg = "$VIA\supportive modules\registry"
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:VIA_NO_OPEN = '1'; $stamp = Get-Date -Format yyyyMMdd_HHmmss
$Out = "$VIA\VIA_Reports\review\r3_$stamp"; New-Item -ItemType Directory -Force -Path $Out | Out-Null; git -C $Repo tag -f "pre-r3/$stamp" HEAD | Out-Null
function Invoke-VIAR3([string]$id, [string]$cmd) { Write-Host "=== [$id] $cmd ===" -ForegroundColor Cyan; $o = @(Invoke-Expression $cmd 2>&1 | ForEach-Object { "" + $_ }); $o | Set-Content "$Out\$id.log" -Encoding UTF8
  $o | Where-Object { $_ -match '\[(計|FAIL|RED|GREEN|YELLOW|多義|結|OK)\]|總判|落差|遺失|改身分|重號|FPSTALE|UNCOMMITTED|缺號|撞號|APPLIED|ABSENT|啟動層|rc ' } | Select-Object -Last 8 | ForEach-Object { "  " + $_.Trim().Substring(0, [Math]::Min(150, $_.Trim().Length)) } }

# ① 入倉兩本冊(VDF 基層)
foreach ($f in 'VDF_InputUniverse_SSOT_v0103.json', 'VDF_DataArchitecture_Rule_SSOT_v0100.json') { if (Test-Path "$dl\$f") { Copy-Item "$dl\$f" "$VIA\functional modules\VDF\" -Force; Write-Host "  [入] $f" -ForegroundColor Cyan } else { Write-Host "  [缺] $f" -ForegroundColor Yellow } }

# ② 聯集冊新版 + 10 條 rating 裁定(只增;正本生成器仍是 CGC_MDL176,本步只加 rulings)
$latest = Get-ChildItem $reg -Filter 'VIA_SSOT_SynonymUnion_v*.json' | Sort-Object Name | Select-Object -Last 1
$py = @"
import json,re,datetime,sys
src=r'$($latest.FullName)'; d=json.load(open(src,encoding='utf-8'))
v=int(re.search(r'_v(\d{4})',src).group(1)); dst=src.replace('_v%04d'%v,'_v%04d'%(v+1))
have={(r.get('scope'),str(r.get('key')).lower()) for r in d.get('rulings',[])}
R=[('strong buy','BUY'),('conviction buy','BUY'),('top pick','BUY'),('強力買進','BUY'),('積極買進','BUY'),('strong sell','SELL'),('強力賣出','SELL'),('強烈賣出','SELL'),('accumulate','ADD'),('add','ADD')]
n=0
for k,c in R:
    if ('rating',k) in have: continue
    d.setdefault('rulings',[]).append({'scope':'rating','key':k,'state':'POLYSEMY','verdict':c,'kind':'COARSE_BUCKET','ruled_by':'AI 依操作員「黃燈請修正」(R-SYN-04;LL90 留痕)','why':'同義字只映粗桶;strong/conviction/top pick 是強度 → rating_strength 欄位,不是第二正典;accumulate/add 維持樞紐 ADD 桶'}); n+=1
d['version']='v%04d'%(v+1); d['prior']=src.split(chr(92))[-1]; d['batch']=(d.get('batch','')+' ‖ 側線 2026-10-03 f:+%d rating rulings(R-SYN-04)'%n); d['ts']=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
json.dump(d,open(dst,'w',encoding='utf-8'),ensure_ascii=False,indent=1); print('union', dst.split(chr(92))[-1], '+%d rulings'%n)
"@
python -c $py

# ③ 登冊(新 16 變 5)· 自測兩支薄尾 · 樞紐重量
Invoke-VIAR3 '3a' 'via-vcgc registry-sync --apply'
Invoke-VIAR3 '3b' 'via-vcgc run --family vrn SUP_MDL749_VRNFieldRuleHub additive'
Invoke-VIAR3 '3c' 'via-vcgc run --family core CGC_MDL185_SsotBookSync check'

# ④ 編號:先提交(UNCOMMITTED 律)→ 發號 → 稽核
& git -C $Repo add -A -- 'VeritasIntelligenceAnalytics/supportive modules/registry' 'VeritasIntelligenceAnalytics/functional modules/VRN' 'VeritasIntelligenceAnalytics/functional modules/VDF' 2>&1 | Out-Null
& git -C $Repo commit -q -m "Round3 ($stamp): universe SSOT v0103 (display names), DataArchitecture rule v0100, SynonymUnion +10 rating rulings, registry-sync; append-only" 2>&1 | Out-Null
$branch = (& git -C $Repo rev-parse --abbrev-ref HEAD); $pu = & git -C $Repo push origin $branch 2>&1; if ($LASTEXITCODE -ne 0) { $null = via-medic sync --apply 2>&1; $pu = & git -C $Repo push origin $branch 2>&1 }
Write-Host ("  [推] " + $(if ($LASTEXITCODE -eq 0) { $branch + ' · ' + (& git -C $Repo rev-parse --short=12 HEAD) } else { '被拒(看 git status)' })) -ForegroundColor Green
Invoke-VIAR3 '4a' 'via-vcgc run --family core CGC_MDL237_NumberingSystem --apply'
Invoke-VIAR3 '4b' 'via-vcgc run --family core CGC_MDL237_NumberingSystem audit'
& git -C $Repo add -A -- 'VeritasIntelligenceAnalytics/supportive modules/registry' 2>&1 | Out-Null; & git -C $Repo commit -q -m "Numbering ($stamp): MDL237 apply; append-only" 2>&1 | Out-Null; & git -C $Repo push -q origin $branch 2>&1 | Out-Null

# ⑤ env 紅的根因(只印,不猜):MDL230 探針紅列 + EnvManager 總判
Invoke-VIAR3 '5a' 'via-vcgc run --family core CGC_MDL230_ToolCoverageProbe probe --plain'
Invoke-VIAR3 '5b' 'via-vcgc run --family core CGC_MDL240_EnvManager check'
Get-Content "$Out\5a.log" -Encoding UTF8 | Where-Object { $_ -match '^\s*RED|缺 [1-9]|ABSENT|啟動層' } | Select-Object -First 8 | ForEach-Object { Write-Host ("  [230 紅列] " + $_.Trim().Substring(0, [Math]::Min(170, $_.Trim().Length))) -ForegroundColor Red }

# ⑥ 後測
Invoke-VIAR3 '6' 'via-vcgc ssot panorama --full'
$pack = Get-ChildItem $Out -Filter '*.log' | ForEach-Object { "## " + $_.BaseName; Get-Content $_.FullName -Encoding UTF8 | Where-Object { $_ -match '\[(計|FAIL|RED|YELLOW|多義|結)\]|總判|遺失|改身分|重號|FPSTALE|UNCOMMITTED|缺號|撞號|APPLIED|^\s*RED|啟動層|族總判|^\s*(正則|同義字|自動編號|命名|註冊|上下連結)\s' } | Select-Object -First 14 }
$pack | Set-Content "$Out\paste.md" -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
Write-Host "畢 · 貼回包已進剪貼簿 · 還原 tag pre-r3/$stamp · $Out" -ForegroundColor Green
}
