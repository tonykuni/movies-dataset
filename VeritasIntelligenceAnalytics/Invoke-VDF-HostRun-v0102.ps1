# Invoke-VDF-HostRun-v0102.ps1 — VDF 主機一鍵檢查(薄殼):只進環境、叫 VDF_SystemManager 尾版的 hostrun
#   取代 v0100 / v0101(那兩版把更新倉 · 判斷 · 摘要處理寫在 PS,違反 CLAUDE.md L117;PR #777 Codex P1)。
#   更新倉(fetch · 有未提交改動就不切 · 切分支)、更新後換新尾版重跑、摘要進剪貼簿,全在 Python(VDF_SystemManager v0209 起)。
#   本檔不搬檔、不擷取、不設同意閘、不裝套件、不改其他 .ps1。
#   用法(任何目錄都可;建議 PowerShell 7):
#     & "$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\Invoke-VDF-HostRun-v0102.ps1"
#     ... -Full          # vv 跑全部引擎(約 30 分鐘)
#     ... -NoUpdate      # 不更新倉
#     ... -Branch main   # PR 合併之後改從 main 更新
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

$mgr = (Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot "functional modules\VDF") -Filter "VDF_SystemManager_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$pyArgs = @("hostrun", "--branch", $Branch)
if ($Full) { $pyArgs += "--full" }
if ($NoUpdate) { $pyArgs += "--no-update" }
$env:PYTHONUTF8 = "1"; $env:VIA_FROM_VDFSM = "YES"
$rc = 1
Push-Location $env:TEMP
try { & $Python $mgr @pyArgs; $rc = $LASTEXITCODE } finally { Pop-Location; Remove-Item env:VIA_FROM_VDFSM -ErrorAction SilentlyContinue }
exit $rc
