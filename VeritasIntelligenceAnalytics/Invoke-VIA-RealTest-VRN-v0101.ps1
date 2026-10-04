# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Samples = 'C:\測試樣本報告', [int]$MaxMin = 45, [int]$Limit = 0)
# param 必須是第一個語句(PS 規則);加速器橋接在它後面,章的文字判準不受影響
# AI 產出必須接入模板。只動 $PID,關閉即還原。新規定(2026-10-03):前段 安全清理 · TEMP · 加速器 · 雙軌;收尾 黃字貼 AI · 紅字錯誤。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-RealTest-VRN-v0101.ps1 — C:\測試樣本報告 實測:25 風險前置(ENG399)‖ VRN 流程輸出(SystemManager outputs)雙軌 → 輸出清點 → CGC_MDL249 check → 清點無誤 = 成功
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $dl = "$env:USERPROFILE\Downloads"
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'; $env:VIA_VRN_SINCE = '2022-06-01'
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()
$skel = Join-Path $VIA 'VeritasCeleritas.PS7.Skeleton-v0102.ps1'
if (Test-Path "$dl\VeritasCeleritas.PS7.Skeleton-v0102.ps1") { Copy-Item "$dl\VeritasCeleritas.PS7.Skeleton-v0102.ps1" $VIA -Force }
if (Test-Path "$dl\VRN_ENG399_RealTestHarness_v0100.py") { Copy-Item "$dl\VRN_ENG399_RealTestHarness_v0100.py" "$VIA\functional modules\VRN\" -Force }
# 骨架的四個函數:只借函數,不跑它的示範主體(dot-source 到一半 → 取函數定義)
$skelText = Get-Content $skel -Raw -Encoding UTF8; $cut = $skelText.IndexOf('# ======================= 骨架主體'); Invoke-Expression $skelText.Substring(0, $cut)

Invoke-VCSafeCleanup; $Run = Initialize-VCTemp; Initialize-VCAccel
$LogDir = Join-Path $VIA ("VIA_Reports\review\realtest_" + $script:Stamp); New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Reg = if ($global:VIARegisterPath) { $global:VIARegisterPath } else { (Get-ChildItem $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName }
if (-not (Test-Path $Samples)) { $script:Errors.Add("[樣本] $Samples 不在"); Show-VCSummary -Title 'VRN 實測' -LogDir $LogDir; return }
$n = @(Get-ChildItem $Samples -File -Include *.pdf,*.docx,*.pptx -Recurse).Count; $script:Verdicts.Add("[樣本] $Samples · $n 件")
$lim = if ($Limit -gt 0) { "--limit $Limit" } else { "" }

# 雙軌:A = 25 風險前置(只讀) ‖ B = VRN 流程輸出(SystemManager → 分類 → 版面 → 實體 → outputs)
$Lanes = @(
  @{ id = 'A-risk25'; zh = 'ENG399 25 風險 × 每件(偵測·修法·驗證·修復)'; args = @($VIA, $Reg, $Samples, $lim); run = { param($VIA, $Reg, $S, $lim) Set-Location $VIA; . $Reg; Invoke-Expression "via-vcgc run --family vrn VRN_ENG399_RealTestHarness run --in `"$S`" $lim --no-open" 2>&1 } },
  @{ id = 'B-outputs'; zh = 'VRN 流程:分類 → 版面 → 實體 → outputs(表頭·DF·驗證·三方對照·Parquet)'; args = @($VIA, $Reg, $Samples); run = { param($VIA, $Reg, $S) Set-Location $VIA; . $Reg
      via-vcgc run --family vrn VRN_ENG393_DocClassVerify classify --samples "$S" 2>&1
      via-vcgc run --family vrn VRN_ENG394_LayoutRestore restore --in "$S" --pages 1 2>&1
      via-vcgc run --family vrn VRN_ENG396_ReportEntities run --in "$S" --pages 1-2 2>&1
      via-vcgc run --family vrn VRN_SystemManager outputs 2>&1 } })
Invoke-VCDualLane -Lanes $Lanes -LogDir $LogDir

# 輸出清點:parquet / duckdb / json 多了哪些 · 列數 · 主鍵 · 表頭 = 冊(CGC_MDL249 check)
$outs = Get-ChildItem "$VIA\VIA_Reports\vrn" -Recurse -File -Include *.parquet,*.duckdb,*.json -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-$MaxMin) }
$script:Verdicts.Add("[清點] 本輪 VRN 輸出 " + $outs.Count + " 件:" + (($outs | Sort-Object Length -Descending | Select-Object -First 6 | ForEach-Object { $_.Name + '(' + [Math]::Round($_.Length/1KB) + 'KB)' }) -join ' · '))
$chk = @(via-vcgc run --family core CGC_MDL249_DataFrameLock check 2>&1 | ForEach-Object { "" + $_ }); $chk | Set-Content (Join-Path $LogDir '249.log') -Encoding UTF8
$c249 = @($chk | Where-Object { $_ -match '\[(計|GREEN|RED|YELLOW|FAIL)\]|總判' } | Select-Object -Last 3); foreach ($l in $c249) { if ($l -match 'RED|FAIL') { $script:Errors.Add("[249] " + $l.Trim()) } else { $script:Verdicts.Add("[249] " + $l.Trim()) } }
$rt = Get-Content "$VIA\VIA_Reports\vrn\realtest\paste.md" -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 12; foreach ($l in $rt) { if ($l -match '\[RED\]') { $script:Errors.Add("[風險] " + $l) } else { $script:Verdicts.Add("[風險] " + $l) } }
$ok = ($script:Errors.Count -eq 0) -and ($outs.Count -gt 0)
$script:Verdicts.Add("[判] " + $(if ($ok) { "成功:輸出清點 " + $outs.Count + " 件 · 249 無紅 · 25 風險無紅" } else { "未成功:看紅字" }))
Show-VCSummary -Title 'VRN 實測(C:\測試樣本報告)' -LogDir $LogDir
try { $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = "$VIA\VIA_Reports\vrn\realtest\REALTEST_latest.html"; $psi.UseShellExecute = $true; $null = [System.Diagnostics.Process]::Start($psi) } catch { }
