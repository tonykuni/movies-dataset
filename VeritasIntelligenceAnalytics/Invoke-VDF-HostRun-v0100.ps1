# Invoke-VDF-HostRun-v0100.ps1 — VDF 主機一鍵檢查:更新倉 → VDF_SystemManager 尾版 hostrun → 摘要進剪貼簿
#   操作員 2026-11-28:「one ps to handle all」。本檔只做三件事(CLAUDE.md L117:PS 只進環境、叫一個 python 動詞):
#     ① 更新倉:fetch 指定分支;本機有未提交的改動(可能是另一個工作階段在用)→ 不切、照現在的版本跑,照實印出
#     ② 叫 VDF_SystemManager 尾版的 hostrun(唯讀:tidy 只乾跑 · vv 引擎自測(隔離環境)· outputs · ENG232 check-db)
#     ③ 摘要(VIA_Reports\vdf\manager\HOSTRUN_latest.txt)複製到剪貼簿
#   要跑什麼、怎麼判,全在 Python;本檔不搬檔、不擷取、不設同意閘、不裝套件、不改其他 .ps1。
#   用法(任何目錄都可;建議 PowerShell 7):
#     & "$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\Invoke-VDF-HostRun-v0100.ps1"
#     ... -Full                          # vv 跑全部引擎(約 30 分鐘;預設只跑上一輪沒過的那幾支)
#     ... -NoUpdate                      # 不更新倉,照現在的版本跑
#     ... -Branch main                   # PR 合併之後改從 main 更新
param(
    [switch]$Full,
    [switch]$NoUpdate,
    [string]$Branch = "claude/sweet-hamilton-gei01h",
    [string]$Python = "python"
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$via = $PSScriptRoot
$repo = Split-Path $via -Parent

# ① 更新倉(有未提交的改動就不切)
if (-not $NoUpdate) {
    git -C $repo fetch -q origin $Branch
    if ($LASTEXITCODE) {
        Write-Host "[HostRun] 抓不到 origin/$Branch,照現在的版本跑" -ForegroundColor Yellow
    } else {
        $dirty = git -C $repo -c core.quotepath=off status --porcelain --untracked-files=no
        if ($dirty) {
            Write-Host "[HostRun] 本機有未提交的改動(可能是另一個工作階段在用),先不切分支、照現在的版本跑:" -ForegroundColor Yellow
            $dirty | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        } else {
            git -C $repo switch -q -C via-hostrun "origin/$Branch"
            if ($LASTEXITCODE) { Write-Host "[HostRun] 切不到 origin/$Branch,照現在的版本跑" -ForegroundColor Yellow }
        }
    }
}

# ② 叫 VDF_SystemManager 尾版 hostrun
$mgr = Get-ChildItem -LiteralPath (Join-Path $via "functional modules\VDF") -Filter "VDF_SystemManager_v*.py" |
    Sort-Object Name | Select-Object -Last 1
if (-not $mgr) { Write-Host "[HostRun] 找不到 VDF_SystemManager_v*.py" -ForegroundColor Red; exit 3 }
Write-Host "[HostRun] 用 $($mgr.Name) · $(git -C $repo rev-parse --abbrev-ref HEAD) @ $(git -C $repo rev-parse --short HEAD)" -ForegroundColor Cyan
$keep = @{ PYTHONUTF8 = $env:PYTHONUTF8; VIA_FROM_VDFSM = $env:VIA_FROM_VDFSM }
$env:PYTHONUTF8 = "1"; $env:VIA_FROM_VDFSM = "YES"
$pyArgs = @("hostrun"); if ($Full) { $pyArgs += "--full" }
$rc = 1
Push-Location $env:TEMP
try {
    & $Python $mgr.FullName @pyArgs
    $rc = $LASTEXITCODE
} finally {
    Pop-Location
    foreach ($k in $keep.Keys) { Set-Item -Path "env:$k" -Value $keep[$k] -ErrorAction SilentlyContinue; if ($null -eq $keep[$k]) { Remove-Item "env:$k" -ErrorAction SilentlyContinue } }
}

# ③ 摘要進剪貼簿
$sum = Join-Path $via "VIA_Reports\vdf\manager\HOSTRUN_latest.txt"
if (Test-Path -LiteralPath $sum) {
    Get-Content -Raw -LiteralPath $sum | Set-Clipboard
    Write-Host "[HostRun] 摘要已複製到剪貼簿(rc $rc),直接貼給我" -ForegroundColor Cyan
} else {
    Write-Host "[HostRun] 沒有摘要檔(hostrun 沒跑完,rc $rc);把上面畫面最後幾行貼給我" -ForegroundColor Red
}
exit $rc
