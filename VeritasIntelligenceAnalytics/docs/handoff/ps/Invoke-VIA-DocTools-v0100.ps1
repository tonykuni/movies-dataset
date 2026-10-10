# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# Invoke-VIA-DocTools-v0100.ps1 — 文件工具安裝一條龍(操作員令 2026-10-10:VCGC 環境及工具管理協助安裝 pdfplumber fitz pypdfium2 PIL docx reportlab
#   pikepdf win32com docx2pdf soffice pdftoppm ps_word_com;紀錄造冊編碼一定要安裝;所有環境無衝突,以還原點進行新增)。
# 本檔只做啟動與串接(L117:邏輯全在 python 尾版);直接呼叫尾版,不經 VCGC 主控台(MDL149 鏈壞也能跑)。
#   ① 還原點   CGC_MDL274_HealthMatrix restorepoint(檔案層 zip + 帳)              有紅燈要 -ForceRestore 才建(你的決定)
#   ② LKGC     CGC_MDL135_EnvGovernance plan(各境鎖檔 = 環境層還原點)
#   ③ 衝突     CGC_MDL135_EnvGovernance resume(uv 乾跑:每列 CLEAN / CONFLICT)        有 CONFLICT 就停,不裝
#   ④ 安裝     CGC_MDL135_EnvGovernance resume --approve(只增不減;docs 家族 → via_vrn_312;冊 VIA_ToolRoster_SSOT_v0107)   要 -Apply
#   ⑤ 外部程式 CGC_MDL273_EnvToolAudit ext [--apply](soffice / pdftoppm 走 winget;Word 授權不代裝)                 要 -Apply
#   ⑥ 驗證     CGC_MDL135 tools --tool-env via_vrn_312 · CGC_MDL273 audit
#   ⑦ 編號     CGC_MDL237_NumberingSystem audit(LIB 號依 live import 發;docx2pdf 待有 import 才發)
# 不帶 -Apply = 全程乾跑(①② 仍會寫還原點 / 鎖檔)。同意閘 VIA_NET_CONSENT 由你在本視窗自己開,本檔不代設。
[CmdletBinding()]
param([switch]$Apply, [switch]$ForceRestore, [string]$ToolEnv = 'via_vrn_312', [string]$Root = '')
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = 'Continue'
$VIA = if ($Root) { $Root } elseif ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'supportive modules'))) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:VIA_FROM_VCGC = 'YES'; $env:VIA_NO_OPEN = '1'
# ---------- 加速器模板(VeritasCeleritas.PS7.ps1;缺席 = 照跑無加速)----------
$core = Join-Path $VIA 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
$script:Accel = $false
if (Test-Path $core) { try { . $core; Set-StrictMode -Off; $script:Accel = $true } catch { Set-StrictMode -Off } }
$reg = Join-Path $VIA 'supportive modules\registry'
function Get-Tail([string]$stem) {
  Get-ChildItem -LiteralPath $reg -Filter "$stem`_v*.py" -ErrorAction SilentlyContinue | Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1 }
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { Write-Host '[停] 找不到 python' -ForegroundColor Red; return }
$rows = [System.Collections.Generic.List[object]]::new()
function Step([string]$id, [string]$name, [string]$stem, [string[]]$a) {
  $t = Get-Tail $stem
  if (-not $t) { $rows.Add([pscustomobject]@{ Step = $id; Name = $name; Rc = 'ABSENT'; Tail = "$stem 不在" }); return 3 }
  Write-Host "── $id $name · $($t.Name) $($a -join ' ')" -ForegroundColor Cyan
  $out = & $py $t.FullName @a 2>&1 | ForEach-Object { "$_" }
  $rc = $LASTEXITCODE
  $out | Select-Object -Last 15 | ForEach-Object { Write-Host "   $_" }
  $script:LastOut = ($out -join "`n")
  $rows.Add([pscustomobject]@{ Step = $id; Name = $name; Rc = $rc; Tail = (($out | Where-Object { $_ -match '\[計\]|\[擋\]|CONFLICT|BLOCK' } | Select-Object -Last 1) -as [string]) })
  return $rc }

$rpArgs = @('restorepoint', '--note', 'doc tools install') + $(if ($ForceRestore) { @('--force') } else { @() })
$sha = (git -C (Split-Path $VIA -Parent) rev-parse --short HEAD 2>$null); if ($sha) { $rpArgs += @('--git', $sha) }
if ((Step '①' '還原點' 'CGC_MDL274_HealthMatrix' $rpArgs) -ne 0) { Write-Host '[停] 還原點沒建成(有紅燈?看上面;確定要建就加 -ForceRestore)' -ForegroundColor Yellow; $rows | Format-Table -AutoSize; return }
[void](Step '②' 'LKGC 鎖檔' 'CGC_MDL135_EnvGovernance' @('plan'))
[void](Step '③' '衝突乾跑' 'CGC_MDL135_EnvGovernance' @('resume'))
if ($script:LastOut -match 'CONFLICT') { Write-Host '[停] 乾跑有 CONFLICT → 不裝;看 VIA_Reports\env_governance\RESUME_latest.ps1' -ForegroundColor Red; $rows | Format-Table -AutoSize; return }
if ($Apply) {
  if ($env:VIA_NET_CONSENT -ne 'YES') { Write-Host "[停] -Apply 要先在本視窗自己開:`$env:VIA_NET_CONSENT='YES'(本檔不代設)" -ForegroundColor Yellow; $rows | Format-Table -AutoSize; return }
  [void](Step '④' '安裝(只增不減)' 'CGC_MDL135_EnvGovernance' @('resume', '--approve'))
  [void](Step '⑤' '外部程式' 'CGC_MDL273_EnvToolAudit' @('ext', '--apply'))
} else {
  Write-Host '[乾跑] 沒帶 -Apply:④ ⑤ 只列計畫' -ForegroundColor Yellow
  [void](Step '⑤' '外部程式(計畫)' 'CGC_MDL273_EnvToolAudit' @('ext'))
}
[void](Step '⑥a' '驗證 · 工具冊' 'CGC_MDL135_EnvGovernance' @('tools', '--tool-env', $ToolEnv))
[void](Step '⑥b' '驗證 · 全景' 'CGC_MDL273_EnvToolAudit' @('audit'))
[void](Step '⑦' '編號稽核' 'CGC_MDL237_NumberingSystem' @('audit'))
$rows | Format-Table -AutoSize
if ($script:Accel -and (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue)) { try { Restore-CeleritasPS7 | Out-Null } catch { } }   # 關閉即還原
