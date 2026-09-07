<#
Invoke-VIA-EnvGovernance v0100 — 環境治理一貼即用單一 PowerShell(批381;CGC_MDL135 統一治理引擎)
操作員令:「依照已成功地建構布局向上新增;最壞還原成原本規劃;base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」
+《VIA_EnvManager.py 環境與函式庫防衝突管理規範》:全景式分析先行 → uv 極速快篩 → 衝突立拔與動態隔離 → LKGC 授權閉環 → 一貼即用 → HTML UI Matrix。
流程(不關閉、不阻塞、不卡斷):
  ① 20 加速器點亮(SUP_MDL737 --activate;缺席=誠實 SKIP 零影響)
  ② MDL135 全景式分析 + 計畫(預設離線唯讀;-Online 開同意閘=鏡像健康+uv pip compile 多輪模擬)
  ③ -Approve 才執行 GREEN 非破壞段(建境/裝件/驗證/base 補齊);-ApproveRemove 才跑 base 端移除(目標境 VERIFY 綠後;逐件印令)
  ④ LKGC 快照/晉升 + 四分區 UI Matrix 落檔(VIA_Reports\env_governance;零跳出;-Open 只走瀏覽器 exe)
  -Background:全鏈丟背景 Job,終端立即返還(-Watch 直播 LAUNCH log;Ctrl-C 只離開觀看)
慣例:無 Read-Host;失敗誠實續行;PS 5.1/7 相容;回退=改指 MDL135 直呼 python。
用法:via-envgov-auto                      # 唯讀全景+計畫+矩陣
      via-envgov-auto -Online              # 上網模擬(清華→阿里→PyPI)
      via-envgov-auto -Online -Approve     # 執行 GREEN 段
      via-envgov-auto -Online -Approve -ApproveRemove   # 連 base 端移除(候裁段)
      via-envgov-auto -Background;  via-envgov-auto -Watch
#>
param(
    [switch]$Approve,
    [switch]$ApproveRemove,
    [switch]$Online,
    [switch]$Background,
    [switch]$Watch,
    [switch]$Open,
    [string]$EnvRoot = "",
    [string]$BasePython = "",
    [string]$Only = "",
    [int]$Workers = 20,
    [int]$TaskTimeout = 120
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$VIA = $PSScriptRoot
$env:VIA_NO_OPEN = "1"; $env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"; $env:GIT_EDITOR = "true"
if ($Online) { $env:VIA_NET_CONSENT = "YES" }
$RunDir = Join-Path $VIA "VIA_Reports\env_governance"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Get-Tail([string]$Dir, [string]$Pat) {
    $hit = Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($hit) { return $hit.FullName }
    return $null
}
function Get-Py {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    return "python3"
}

if ($Watch) {
    $lg = Get-ChildItem $RunDir -Filter "LAUNCH_*.log" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($lg) { Write-Host ("  [watch] " + $lg.FullName + "(Ctrl-C 只離開觀看)") -ForegroundColor Cyan; Get-Content -Path $lg.FullName -Wait -Tail 30 -Encoding UTF8 }
    else { Write-Host "  [watch] 無 LAUNCH log(先 via-envgov-auto -Background)" -ForegroundColor Yellow }
    return
}

$Engine = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL135_EnvGovernance_v*.py"
$Accel = Get-Tail (Join-Path $VIA "supportive modules") "SUP_MDL737_SuperAccelModule_v*.py"
if (-not $Engine) { Write-Host "  [FAIL] CGC_MDL135_EnvGovernance 尾版缺(誠實停)" -ForegroundColor Red; exit 2 }
$Py = Get-Py
$mode = "run"
if ($Approve) { $mode = "apply" }
$argsList = @($mode)
if (-not $Online) { $argsList += "--offline" }
if ($Approve) { $argsList += "--approve" }
if ($ApproveRemove) { $argsList += "--approve-remove" }
if ($EnvRoot) { $argsList += @("--env-root", $EnvRoot) }
if ($BasePython) { $argsList += @("--base-python", $BasePython) }
if ($Only) { $argsList += @("--only", $Only) }
$argsList += @("--workers", "$Workers", "--task-timeout", "$TaskTimeout")
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$Log = Join-Path $RunDir ("LAUNCH_" + $ts + ".log")

$Body = {
    param($Py, $Engine, $Accel, $ArgList, $Log, $Online)
    $env:VIA_NO_OPEN = "1"; $env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
    if ($Online) { $env:VIA_NET_CONSENT = "YES" }
    # 所有輸出 Tee 落 log 後導 Out-Host:Body 唯一回傳值=rc(避免管線輸出混入 $rc)
    "=== [envgov-auto] 環境治理一貼即用 v0100 · $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') · $($ArgList -join ' ') ===" | Tee-Object -FilePath $Log -Append | Out-Host
    "--- ① 20 加速器點亮(SUP_MDL737 --activate;缺席=誠實 SKIP)" | Tee-Object -FilePath $Log -Append | Out-Host
    if ($Accel) { try { & $Py $Accel --activate 2>&1 | Tee-Object -FilePath $Log -Append | Out-Host } catch { "  [加速器] $($_.Exception.Message)" | Tee-Object -FilePath $Log -Append | Out-Host } }
    else { "  [加速器] SUP_MDL737 缺席=SKIP(零影響)" | Tee-Object -FilePath $Log -Append | Out-Host }
    "--- ② 全景式分析 → uv 快篩 → base 該有冊 → 衝突立拔家族路由 → Zero-Hydra 拓撲三輪 → 模擬 → (授權)執行 → LKGC → 矩陣" | Tee-Object -FilePath $Log -Append | Out-Host
    & $Py $Engine @ArgList 2>&1 | Tee-Object -FilePath $Log -Append | Out-Host
    $rc = $LASTEXITCODE
    "--- ③ 存證:VIA_Reports\env_governance\RUN_latest.json · VIA_EnvGovernance_Matrix_latest.html · logs\env_governance.log(rc=$rc;RED=有待拉出/衝突,非失敗)" | Tee-Object -FilePath $Log -Append | Out-Host
    "=== [envgov-auto] 畢 $(Get-Date -Format 'HH:mm:ss') ===" | Tee-Object -FilePath $Log -Append | Out-Host
    return $rc
}

Write-Host ("=" * 70) -ForegroundColor DarkCyan
Write-Host "  VIA ENV GOVERNANCE v0100(批381)| MDL135 | $mode | $(if ($Online) { '上網(同意閘開)' } else { '離線唯讀' }) | 加速器 $Workers" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor DarkCyan
if ($Background) {
    $job = Start-Job -Name "VIA_EnvGov" -ScriptBlock $Body -ArgumentList @($Py, $Engine, $Accel, $argsList, $Log, [bool]$Online)
    Write-Host ("  [背景] Job Id={0} · log={1}(看:via-envgov-auto -Watch;或 Receive-Job {0} -Keep)" -f $job.Id, $Log) -ForegroundColor Green
    Write-Host "  [非阻塞] 終端已返還;矩陣落檔於 VIA_Reports\env_governance(零跳出)" -ForegroundColor Green
    return
}
$rc = [int](& $Body $Py $Engine $Accel $argsList $Log ([bool]$Online) | Select-Object -Last 1)
$Matrix = Join-Path $RunDir "VIA_EnvGovernance_Matrix_latest.html"
if (Test-Path $Matrix) {
    Write-Host ("  [矩陣] " + $Matrix + "(小字體/自適應/自動換行/四分區 MODULE·ENGINE·FUNCTION-LIB·OTHERS)") -ForegroundColor Cyan
    if ($Open) {
        # 批378 律:只走瀏覽器 exe(Edge/Chrome/Firefox),永不經 .html 預設程式(VS Code)
        $browsers = @("$env:ProgramFiles (x86)\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe")
        $exe = $browsers | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($exe) { Start-Process -FilePath $exe -ArgumentList ('"' + $Matrix + '"') } else { Write-Host "  [看頁] 無瀏覽器 exe;請自開上列路徑" -ForegroundColor Yellow }
    }
}
Write-Host ("  [總結] rc={0}(0=GREEN/YELLOW 計畫可行;1=RED 有待拉出或衝突;皆已存證)· log {1}" -f $rc, $Log) -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Yellow" })
exit $rc
