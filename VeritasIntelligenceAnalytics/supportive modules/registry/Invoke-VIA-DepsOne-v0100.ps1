#requires -Version 7.0
<#
Invoke-VIA-DepsOne-v0100 — 依賴治理一鍵統包(TOOL-033;操作員令 2026-08-12)
==========================================================================
令:ONE POWERSHELL TO HANDLE ALL——十械三防線+三鏡像+多環境隔離重建,一支到底。
五段:① via-deps 全景(TOOL-031:十械矩陣/衝突掃描/pip check 印證/鏡像現況)
     ② 三鏡像測速(official/tsinghua/aliyun;-Consent 才發包,否則 NOT_RUN 誠實)
     ③ via-rebuild 七段(TOOL-032:盤點→風險因子→旁建計畫→測選→反覆實測→出令)
     ④ GREEN 執行檔處置:預設候裁只列路徑;-Execute 明示才受令代跑
     ⑤ 回驗(僅代跑後):重掃全境;末段五步總結裁決
鐵則:無 Read-Host 不卡斷,單段失敗誠實記錄續行(via-one 家規);
     預設零安裝零改動;網路一律 -Consent 明示開閘;破壞性(切換/移除)永遠候裁。
用法:via-depsone                       # 全程唯讀(測速/實測 NOT_RUN)
     via-depsone -Consent              # 開同意閘:三鏡像測速+dry-run 反覆實測
     via-depsone -Consent -Execute     # 實測綠後受令代跑 GREEN 執行檔+回驗
     via-depsone -Offline              # 零網路快巡(①③)
     參:-EnvName via_core · -Roots "D:\envs" · -Rounds 3
#>
param(
  [switch]$Offline,
  [switch]$Consent,
  [switch]$Execute,
  [string]$EnvName = "",
  [string]$Roots = "",
  [int]$Rounds = 0
)
$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$env:PYTHONIOENCODING = "utf-8"
$T0 = Get-Date
$Reg = $PSScriptRoot
$VIA = Split-Path -Parent (Split-Path -Parent $Reg)
$RunsDir = Join-Path $VIA "VIA_Reports\rebuild_runs"

function Get-NewestEngine([string]$Pattern) {
  $hits = @(Get-ChildItem -Path (Join-Path $Reg $Pattern) -ErrorAction SilentlyContinue | Sort-Object Name)
  if ($hits.Count -gt 0) { return $hits[-1].FullName }
  return $null
}
function Show-Banner([string]$Text) {
  Write-Host ""
  Write-Host ("══ " + $Text + " ══") -ForegroundColor Cyan
}
$Steps = [System.Collections.Generic.List[object]]::new()
function Add-Step([string]$Name, [int]$Rc, [string]$Note) {
  $Steps.Add([pscustomobject]@{ Name = $Name; Rc = $Rc; Note = $Note })
}

$Py = $null
foreach ($Cand in @("py", "python", "python3")) {
  if (Get-Command $Cand -ErrorAction SilentlyContinue) { $Py = $Cand; break }
}
if ($null -eq $Py) {
  Write-Host "  ✗ Python 解譯器缺(py/python/python3 皆未尋獲)——誠實停" -ForegroundColor Red
  exit 2
}
$DepEng = Get-NewestEngine "CGC_MDL046_DepSuper_v0*.py"
$RebEng = Get-NewestEngine "CGC_MDL050_EnvRebuild_v0*.py"
if ((-not $DepEng) -or (-not $RebEng)) {
  Write-Host "  ✗ 引擎缺(via_dep_super/via_env_rebuild 未尋獲)——誠實停" -ForegroundColor Red
  exit 2
}
if ($Consent -and (-not $Offline)) { $env:VIA_NET_CONSENT = "YES" }
$GateTxt = "關(測速/實測 NOT_RUN 誠實)"
if ($env:VIA_NET_CONSENT) { $GateTxt = "開" }
$ExecTxt = "否(候裁)"
if ($Execute) { $ExecTxt = "是(-Execute 明示)" }

Show-Banner ("依賴治理一鍵統包 v0100 · " + (Get-Date -Format "yyyyMMdd_HHmmss") + " · ONE POWERSHELL TO HANDLE ALL")
Write-Host ("  引擎:" + (Split-Path -Leaf $DepEng) + " + " + (Split-Path -Leaf $RebEng))
Write-Host ("  同意閘:" + $GateTxt + " · 受令執行:" + $ExecTxt + " · 破壞性永遠候裁(紅線)")

# ── ① via-deps 全景 ──
Show-Banner "① via-deps 全景(十械/衝突/pip check 印證/鏡像現況)"
& $Py $DepEng
$Rc1 = $LASTEXITCODE
$Note1 = "GREEN/YELLOW(無互撞缺件)"
if ($Rc1 -ne 0) { $Note1 = "RED:本境有互撞/缺件(③ 會出計畫)" }
Add-Step "① via-deps 全景" $Rc1 $Note1

# ── ② 三鏡像測速 ──
if ($Offline) {
  Show-Banner "② 三鏡像測速:SKIP(-Offline 零網路)"
  Add-Step "② 鏡像測速" 0 "SKIP(-Offline)"
} else {
  Show-Banner "② 三鏡像測速(official/tsinghua/aliyun)"
  & $Py $DepEng --mirror-test
  $Note2 = "NOT_RUN(-Consent 未開,誠實)"
  if ($env:VIA_NET_CONSENT) { $Note2 = "三源全測畢(最快源已裁)" }
  Add-Step "② 鏡像測速" $LASTEXITCODE $Note2
}

# ── ③ via-rebuild 七段 ──
Show-Banner "③ via-rebuild 七段(盤點→風險→旁建計畫→測選→反覆實測→出令)"
$RebArgs = @($RebEng)
if ($Offline) { $RebArgs += "--offline" }
if ($EnvName -ne "") { $RebArgs += @("--env", $EnvName) }
if ($Roots -ne "") { $RebArgs += @("--roots", $Roots) }
if ($Rounds -gt 0) { $RebArgs += @("--rounds", "$Rounds") }
& $Py @RebArgs
$Rc3 = $LASTEXITCODE
$Note3 = "全境健康或無 RED 段"
if ($Rc3 -ne 0) { $Note3 = "有重建/壞損境——計畫+實測已出(見上)" }
Add-Step "③ 重建計畫" $Rc3 $Note3

# ── ④ GREEN 執行檔處置 ──
$ExecFile = $null
if (Test-Path $RunsDir) {
  $ExecFile = @(Get-ChildItem -Path (Join-Path $RunsDir "REBUILD_EXEC_*.ps1") -ErrorAction SilentlyContinue |
      Where-Object { $_.LastWriteTime -gt $T0 } | Sort-Object LastWriteTime) | Select-Object -Last 1
}
if ($null -eq $ExecFile) {
  Show-Banner "④ 執行檔:本輪無 GREEN 段出檔(全境已淨或段未轉綠——誠實)"
  Add-Step "④ 執行檔" 0 "無出檔(候/RED 段見 ③;或零段)"
} elseif (-not $Execute) {
  Show-Banner "④ 執行檔:已出,候裁不代跑(紅線)"
  Write-Host ("  [候裁] GREEN 執行檔:" + $ExecFile.FullName)
  Write-Host "         檢閱後自跑:pwsh -NoProfile -File <上列路徑>;或本統包加 -Execute 受令代跑"
  Add-Step "④ 執行檔" 0 "候裁(已出檔未跑)"
} else {
  Show-Banner "④ 執行檔:受令代跑(-Execute 明示;只含 GREEN 段)"
  $RunTarget = $ExecFile.FullName
  $UseSh = $false
  if (-not $IsWindows) {  # 非 Windows 改跑 .sh 孿生檔(.ps1 內含 py/Scripts 慣例)
    $ShTwin = [System.IO.Path]::ChangeExtension($RunTarget, ".sh")
    if (Test-Path $ShTwin) { $RunTarget = $ShTwin; $UseSh = $true }
  }
  Write-Host ("  跑:" + $RunTarget)
  $RcExec = 1
  try {
    if ($UseSh) { & sh $RunTarget } else { & $RunTarget }
    $RcExec = $LASTEXITCODE
    if ($null -eq $RcExec) { $RcExec = 0 }
  } catch {
    Write-Host ("  ✗ 執行中斷:" + $_.Exception.Message) -ForegroundColor Red
    $RcExec = 1
  }
  $Note4 = "GREEN 段裝畢+逐段 pip check 淨"
  if ($RcExec -ne 0) { $Note4 = "中斷(誠實;旁建零破壞,原境未動可重跑)" }
  Add-Step "④ 執行檔(受令)" $RcExec $Note4

  # ── ⑤ 回驗(僅代跑後) ──
  Show-Banner "⑤ 回驗(重掃全境;旁建境應轉綠,原境紅=待切換候裁)"
  $VerArgs = @($RebEng, "--offline")
  if ($EnvName -ne "") { $VerArgs += @("--env", $EnvName) }
  if ($Roots -ne "") { $VerArgs += @("--roots", $Roots) }
  & $Py @VerArgs
  $Rc5 = $LASTEXITCODE
  $Note5 = "全境綠"
  if ($Rc5 -ne 0) { $Note5 = "原境仍紅屬預期(旁建綠後,切換走候裁令)" }
  Add-Step "⑤ 回驗" $Rc5 $Note5
}

# ── 總結裁決 ──
Show-Banner "總結裁決(五段)"
$Final = 0
foreach ($s in $Steps) {
  $Mark = "GREEN"
  if ($s.Rc -ne 0) { $Mark = "RED "; $Final = 1 }
  Write-Host ("  [" + $Mark + "] " + $s.Name + " · rc" + $s.Rc + " · " + $s.Note)
}
Write-Host "  存證:VIA_Reports\depsuper_runs + VIA_Reports\rebuild_runs(JSON+執行檔)"
Write-Host "  候裁事項(切換/移除/YELLOW·RED 段)見 ③ 輸出——操作員裁後另跑;安裝亦可走 via-plan→via-install"
Write-Host ("  出口碼:" + $Final)
exit $Final

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
