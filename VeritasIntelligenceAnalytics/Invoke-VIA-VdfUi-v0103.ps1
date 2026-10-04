# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
[CmdletBinding()]
param([string]$Template = '', [switch]$Serve, [int]$Port = 8765, [switch]$NoOpen, [switch]$Foreground, [string]$Apply = '', [string]$ApplyInputs = '')
# AI 產出必須接入模板。只動 $PID,關閉即還原。新規定:前段 安全清理 · TEMP · 加速器;收尾 黃字貼 AI · 紅字錯誤。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-VdfUi-v0103.ps1 — 一鍵啟動 VDF HTML U/I(VDF_ENG234_UiLauncher):入倉 → 自測 → 背景起伺服器 → 開瀏覽器;不裝任何東西、不動系統(只用標準庫;環境走 via_core 既有境)
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $dl = "$env:USERPROFILE\Downloads"; Set-Location -LiteralPath $VIA
$env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_PANORAMA_AUTO = '0'; $env:VIA_UI_DIRECT = 'YES'; if ($NoOpen) { $env:VIA_NO_OPEN = '1' } else { Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue }
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss; $script:Errors = [System.Collections.Generic.List[string]]::new(); $script:Verdicts = [System.Collections.Generic.List[string]]::new()
$skel = Get-ChildItem $VIA -Filter 'VeritasCeleritas.PS7.Skeleton-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if ($skel) { $t = Get-Content $skel.FullName -Raw -Encoding UTF8; Invoke-Expression $t.Substring(0, $t.IndexOf('# ======================= 骨架主體')); Invoke-VCSafeCleanup; $null = Initialize-VCTemp; Initialize-VCAccel }
$eng = "$VIA\functional modules\VDF\engine\VDF_ENG234_UiLauncher_v0102.py"
if (Test-Path "$dl\VDF_ENG234_UiLauncher_v0102.py") { if (-not (Test-Path $eng) -or ((Get-FileHash $eng).Hash -ne (Get-FileHash "$dl\VDF_ENG234_UiLauncher_v0102.py").Hash)) { Copy-Item "$dl\VDF_ENG234_UiLauncher_v0102.py" (Split-Path $eng) -Force; $script:Verdicts.Add("[入倉] VDF_ENG234_UiLauncher_v0102.py") } }
if (-not (Test-Path $eng)) { $script:Errors.Add("[缺] $eng 不在倉也不在 Downloads"); if (Get-Command Show-VCSummary -ErrorAction SilentlyContinue) { Show-VCSummary -Title 'VDF U/I' -LogDir $VIA } else { Write-Host $script:Errors -ForegroundColor Red }; return }
$py = if (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { try { Get-VIAEnvPython 'via_core' } catch { 'python' } } else { 'python' }; if (-not $py) { $py = 'python' }
$st = @(& $py $eng --selftest 2>&1 | Select-String '\[計\]|FAIL' | ForEach-Object { $_.Line.Trim() }); foreach ($l in $st) { if ($l -match 'FAIL') { $script:Errors.Add("[自測] $l") } else { $script:Verdicts.Add("[自測] $l") } }
if ($script:Errors.Count) { Show-VCSummary -Title 'VDF U/I' -LogDir $VIA; return }
if ($ApplyInputs) { $ip = "$VIA\functional modules\VDF\ui\vdf_inputs.json"; $src = if (Test-Path $ApplyInputs) { $ApplyInputs } elseif (Test-Path "$dl\$ApplyInputs") { "$dl\$ApplyInputs" } else { '' }
  if ($src) { try { $null = Get-Content $src -Raw -Encoding UTF8 | ConvertFrom-Json; New-Item -ItemType Directory -Force -Path (Split-Path $ip) | Out-Null; Copy-Item $src $ip -Force; $script:Verdicts.Add("[輸入項目] 已寫回 vdf_inputs.json(來源 $src)") } catch { $script:Errors.Add("[輸入項目] 不是合法 JSON:$src") } } else { $script:Errors.Add("[輸入項目] 找不到 $ApplyInputs") } }
if ($Apply) { $cfgp = "$VIA\functional modules\VDF\ui\ui_config.json"; New-Item -ItemType Directory -Force -Path (Split-Path $cfgp) | Out-Null
  try { $cur = if (Test-Path $cfgp) { Get-Content $cfgp -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable } else { @{} }; $patch = $Apply | ConvertFrom-Json -AsHashtable; foreach ($k in $patch.Keys) { if ($patch[$k] -is [hashtable] -and $cur[$k] -is [hashtable]) { foreach ($kk in $patch[$k].Keys) { $cur[$k][$kk] = $patch[$k][$kk] } } else { $cur[$k] = $patch[$k] } }
    ($cur | ConvertTo-Json -Depth 6) | Set-Content $cfgp -Encoding UTF8; $script:Verdicts.Add("[參數] 已寫回 ui_config.json:$Apply") } catch { $script:Errors.Add("[參數] -Apply 不是合法 JSON:$($_.Exception.Message)") } }
if (-not $Serve) {
  $args2 = @(('"' + $eng + '"'), 'build'); if ($Template) { $args2 += @('--template', ('"' + $Template + '"')) }
  $o = @(& $py $eng build @($(if ($Template) { @('--template', $Template) } else { @() })) 2>&1 | ForEach-Object { "" + $_ }); $j = $null; try { $j = ($o | Where-Object { $_ -like '{*' } | Select-Object -Last 1) | ConvertFrom-Json } catch { }
  if ($j -and $j.out -and (Test-Path $j.out)) { $script:Verdicts.Add("[建] 靜態單檔 $([Math]::Round($j.bytes/1KB)) KB → $($j.out)(對接:$($j.adapt.injected -join ','))"); if (-not $NoOpen) { Start-Process $j.out; $script:Verdicts.Add("[開] 預設瀏覽器直接開檔(不經伺服器)") } }
  else { $script:Errors.Add("[建] 失敗:" + (($o | Select-Object -Last 3) -join ' | ')) } }
else {
  $args2 = @(('"' + $eng + '"'), 'serve', '--port', "$Port"); if ($Template) { $args2 += @('--template', ('"' + $Template + '"')) }; if ($NoOpen) { $args2 += '--no-open' }
  $old = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($old) { $script:Verdicts.Add("[埠] $Port 已有 pid $($old.OwningProcess) → 直接開頁"); if (-not $NoOpen) { Start-Process "http://127.0.0.1:$Port/" } }
  elseif ($Foreground) { & $py @args2 }
  else { $errLog = Join-Path $env:TEMP "vdfui_$($script:Stamp).err"; $p = Start-Process -FilePath $py -ArgumentList $args2 -WorkingDirectory $VIA -WindowStyle Minimized -PassThru -RedirectStandardError $errLog; Start-Sleep 3
    if ($p.HasExited) { $tail = (Get-Content $errLog -Tail 3 -ErrorAction SilentlyContinue) -join ' | '; $script:Errors.Add("[起] 伺服器退出(rc $($p.ExitCode)) · $tail") } else { $script:Verdicts.Add("[起] pid $($p.Id) · http://127.0.0.1:$Port/ · 停:Stop-Process $($p.Id)") } } }
$script:Verdicts.Add("[自適應] templates\ 夾丟任何 .html → /templates 可見 → 參數面板 active_template 選它(或 -Template X.html);Jinja 變數自動對映,純 HTML 注入 window.VIA + 鎖定色 + 四燈")
Show-VCSummary -Title 'VDF HTML U/I(ENG234)' -LogDir $VIA
