# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# Invoke-VIA-SyncFolders-v0100.ps1 — 把最新版 VCGC / VDF 傳入本機資料夾 + VDF 資料庫搬到 VDF 自己的資料家 + 檢查缺什麼(操作員令 2026-10-10;VRN 不在本支範圍)
#   ① 還原點   CGC_MDL274_HealthMatrix restorepoint                         有紅燈要 -ForceRestore 才建(你的決定)
#   ② 打包     CGC_MDL256_SubsystemBundle build via_01_vdf --target → verify   → C:\…\VeritasIntelligenceAnalytics\via_01_vdf
#   ③ 打包     CGC_MDL256_SubsystemBundle build via_00_vcgc --target → verify  → C:\…\VeritasIntelligenceAnalytics\via_00_vcgc
#   ④ 資料家   VDF_SystemManager db move --to <DbHome> [--apply]             複製 → 兩邊逐表列數一致 + 還原點 → 才切 output_hub 接點;舊家不刪
#   ⑤ 缺什麼   VDF_SystemManager db check --home <DbHome>                     缺庫 / 缺表 / 列數不足 / 過舊 → VIA_Reports\vdf\DB_CHECK_latest.html(自動開)
# 包的內容 = 打包冊尾版 VIA_SubsystemBundle_SSOT_v*.json(執行期閉包,只增);本支只啟動與串接,直接呼叫尾版(不經 VCGC 主控台)。
# 不帶 -Apply:②③ 照建(只複製到目標夾),④ 只乾跑列計畫;⑤ 查現在的家。
[CmdletBinding()]
param([switch]$Apply, [switch]$ForceRestore, [switch]$NoBundle, [string]$DbHome = 'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_database', [string]$Root = '')
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = 'Continue'
$VIA = if ($Root) { $Root } elseif ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'supportive modules'))) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:VIA_FROM_VCGC = 'YES'; $env:VIA_NO_OPEN = '1'
$core = Join-Path $VIA 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
$script:Accel = $false
if (Test-Path $core) { try { . $core; Set-StrictMode -Off; $script:Accel = $true } catch { Set-StrictMode -Off } }
function Get-Tail([string]$dir, [string]$stem) {
  Get-ChildItem -LiteralPath (Join-Path $VIA $dir) -Filter "$stem`_v*.py" -ErrorAction SilentlyContinue | Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1 }
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { Write-Host '[停] 找不到 python' -ForegroundColor Red; return }
$rows = [System.Collections.Generic.List[object]]::new()
function Step([string]$id, [string]$name, [string]$dir, [string]$stem, [string[]]$a) {
  $t = Get-Tail $dir $stem
  if (-not $t) { $rows.Add([pscustomobject]@{ Step = $id; Name = $name; Rc = 'ABSENT'; Line = "$stem 不在" }); return 3 }
  Write-Host "── $id $name · $($t.Name) $($a -join ' ')" -ForegroundColor Cyan
  $out = & $py $t.FullName @a 2>&1 | ForEach-Object { "$_" }
  $rc = $LASTEXITCODE
  $out | Select-Object -Last 12 | ForEach-Object { Write-Host "   $_" }
  $rows.Add([pscustomobject]@{ Step = $id; Name = $name; Rc = $rc; Line = (($out | Where-Object { $_ -match '\[計\]|\[擋\]|FAIL|RED' } | Select-Object -Last 1) -as [string]) })
  return $rc }
$reg = 'supportive modules\registry'; $vdf = 'functional modules\VDF'
$rpArgs = @('restorepoint', '--note', 'sync folders + vdf_database') + $(if ($ForceRestore) { @('--force') } else { @() })
$sha = (git -C (Split-Path $VIA -Parent) rev-parse --short HEAD 2>$null); if ($sha) { $rpArgs += @('--git', $sha) }
if ((Step '①' '還原點' $reg 'CGC_MDL274_HealthMatrix' $rpArgs) -ne 0) { Write-Host '[停] 還原點沒建成(有紅燈?確定要建就加 -ForceRestore)' -ForegroundColor Yellow; $rows | Format-Table -AutoSize; return }
if (-not $NoBundle) {
  foreach ($b in @('via_01_vdf', 'via_00_vcgc')) {
    if ((Step "②$b" "打包 $b" $reg 'CGC_MDL256_SubsystemBundle' @('build', $b, '--target', '--no-zip')) -eq 0) {
      [void](Step "②$b" "驗包 $b" $reg 'CGC_MDL256_SubsystemBundle' @('verify', ('C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\' + $b))) }
  }
}
$mv = @('db', 'move', '--to', $DbHome) + $(if ($Apply) { @('--apply') } else { @() })
[void](Step '④' $(if ($Apply) { '資料家搬移' } else { '資料家搬移(乾跑)' }) $vdf 'VDF_SystemManager' $mv)
$home_ = if ($Apply -and (Test-Path (Join-Path $DbHome 'output_hub'))) { Join-Path $DbHome 'output_hub' } else { '' }
[void](Step '⑤' '資料庫缺什麼' $vdf 'VDF_SystemManager' $(if ($home_) { @('db', 'check', '--home', $home_) } else { @('db', 'check') }))
$rows | Format-Table -AutoSize
$page = Join-Path $VIA 'VIA_Reports\vdf\DB_CHECK_latest.html'
if (Test-Path $page) { Start-Process $page }
if ($script:Accel -and (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue)) { try { Restore-CeleritasPS7 | Out-Null } catch { } }   # 關閉即還原
