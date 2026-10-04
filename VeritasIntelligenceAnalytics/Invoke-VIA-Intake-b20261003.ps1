# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([switch]$NoNlpMount)
# AI 產出必須接入模板。只動 $PID,關閉即還原。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-Intake-b20261003.ps1 — 收容五個上傳包(只讀收容;NLP 1.9.0 掛成 ENG078 認得的夾名;Layout 四包只備查不打 patch)
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $dl = "$env:USERPROFILE\Downloads"; Set-Location $VIA; $env:VIA_NO_OPEN = '1'; $env:VIA_PANORAMA_AUTO = '0'
$zips = @{
  'VIA_NLP_OneEngine_v1.9.0'              = @{ zip = 'VIA_NLP_OneEngine_v1_9_0_bundle.zip';   dest = "$VIA\functional modules\VRN\references\intake"; inner = 'VIA_NLP_OneEngine_v1_9_0' }
  'VCGC_LAYOUT_ENGINE_v0104_b20261003'    = @{ zip = 'VCGC_LAYOUT_ENGINE_v0104 (1).zip';      dest = "$VIA\supportive modules\references\intake"; inner = '' }
  'VCGC_LAYOUT_UNIFIED_v0102_b20261003'   = @{ zip = 'VCGC_LAYOUT_UNIFIED_v0102 (1).zip';     dest = "$VIA\supportive modules\references\intake"; inner = '' }
  'VCGC_LAYOUT_UNIFIED_v0103_b20261003'   = @{ zip = 'VCGC_LAYOUT_UNIFIED_v0103.zip';         dest = "$VIA\supportive modules\references\intake"; inner = '' }
  'VCGC_LAYOUT_upgrade_b20261003'         = @{ zip = 'VCGC_LAYOUT_upgrade.zip';               dest = "$VIA\supportive modules\references\intake"; inner = '' } }
foreach ($name in $zips.Keys) { $z = $zips[$name]; $src = Get-ChildItem $dl -Filter ($z.zip -replace '\s*\(1\)', '*') | Where-Object { $_.Name -like ($z.zip.Split(' ')[0] + '*') } | Select-Object -First 1
  if (-not $src) { Write-Host "  [缺] $($z.zip) 不在 Downloads" -ForegroundColor Yellow; continue }
  $tgt = Join-Path $z.dest $name; if (Test-Path $tgt) { Write-Host "  [跳過·已在] $name" -ForegroundColor DarkGray; continue }
  $tmp = Join-Path $env:TEMP ("intake_" + [guid]::NewGuid().ToString('N')); Expand-Archive $src.FullName $tmp -Force
  $root = if ($z.inner -and (Test-Path (Join-Path $tmp $z.inner))) { Join-Path $tmp $z.inner } else { $tmp }
  New-Item -ItemType Directory -Force -Path $tgt | Out-Null; Copy-Item "$root\*" $tgt -Recurse -Force; Remove-Item $tmp -Recurse -Force
  Copy-Item $src.FullName (Join-Path $tgt ('_SOURCE_' + $src.Name)) -Force
  $man = Join-Path $dl "INTAKE_MANIFEST_$name.json"; if (Test-Path $man) { Copy-Item $man $tgt -Force }
  Write-Host ("  [收容] " + $name + " → " + $tgt.Replace("$VIA\", '') + " · " + @(Get-ChildItem $tgt -Recurse -File).Count + " 檔") -ForegroundColor Cyan }
# NLP 1.9.0:ENG078 要 <夾>\src\via_nlp_engine;1.9.0 包把 v1.8 來源放在 embedded_sources\legacy\src → 只「複製」一份到 src(收容件本體不動)
$nlp = "$VIA\functional modules\VRN\references\intake\VIA_NLP_OneEngine_v1.9.0"
if (-not $NoNlpMount -and (Test-Path "$nlp\embedded_sources\legacy\src\via_nlp_engine") -and -not (Test-Path "$nlp\src\via_nlp_engine")) { New-Item -ItemType Directory -Force -Path "$nlp\src" | Out-Null; Copy-Item "$nlp\embedded_sources\legacy\src\via_nlp_engine" "$nlp\src\" -Recurse -Force; Write-Host "  [掛] src\via_nlp_engine 已就位(ENG078 掛載點;來源本體原封)" -ForegroundColor Cyan }
Copy-Item "$dl\INTAKE_ROSTER_PROPOSAL_b20261003.json" "$VIA\VIA_Reports\review\" -Force -ErrorAction SilentlyContinue
# 驗:橋掛得到 NLP 了嗎 · layout 鎖冊沒被動
"## ENG078 掛載"; via-vcgc run --family vrn VRN_ENG078_NLPOneBridge --selftest 2>&1 | Select-String '\[計\]|掛載|ABSENT|STDLIB|FAIL' | ForEach-Object { "  " + $_.Line.Trim() } | Select-Object -Last 4
"## 鎖冊(layout 應仍 v0110 sha_ok)"; via-vcgc tools status 2>&1 | Select-String 'layout|sha_ok' | Select-Object -First 3
"## 收容名冊"; via-intake-roster 2>&1 | Select-String 'NLP_OneEngine|LAYOUT|\[計\]|未登' | Select-Object -First 6
