# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# VIA-OperatorConsole.ps1 — 倉根啟動器:VCGC 操作台一鍵(R24;操作員令「唯一要輸入的地方是系統檔案夾位置及資料庫檔案夾位置 WINDOW I/O」)
# 站在倉根(movies-dataset)打:  .\VIA-OperatorConsole.ps1          第一次會跳兩個 Windows 選夾視窗;之後記住(-Pick 重選)
# 做的事:git pull --ff-only → 找 VeritasIntelligenceAnalytics\Invoke-VIA-OperatorConsole-v*.ps1 最新一支 → 跑它
#        (VCGC 流程閘 → 輸入包入冊 → 全景實測 → 輸出統一 Parquet → 操作台頁,第一頁總覽三色燈)。
# 參數原樣轉:-Pick · -ApplyInput <json> · -SkipSweep · -NoOpen · -SystemDir <夾> · -DataDir <夾> · -NoPull(啟動器不拉)。
$here = $PSScriptRoot
$env:GIT_EDITOR = "true"
$env:GIT_TERMINAL_PROMPT = "0"
if ($args -notcontains "-NoPull") {
    Write-Host "  [啟動器] git pull --ff-only" -ForegroundColor Cyan
    $g = @(git -C $here pull --ff-only 2>&1 | ForEach-Object { "" + $_ })
    if ($g.Count -gt 0) { Write-Host ("            " + $g[$g.Count - 1]) -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ne 0) { Write-Host "            git pull 沒成功(本機有改動或分叉);照現有碼繼續" -ForegroundColor Yellow }
}
$oc = Get-ChildItem -LiteralPath (Join-Path $here "VeritasIntelligenceAnalytics") -Filter "Invoke-VIA-OperatorConsole-v*.ps1" -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if ($null -eq $oc) {
    Write-Host "  [啟動器] 找不到 VeritasIntelligenceAnalytics\Invoke-VIA-OperatorConsole-v*.ps1(先 git pull)" -ForegroundColor Red
    exit 3
}
$pass = @{}
for ($i = 0; $i -lt $args.Count; $i++) {
    $tok = ("" + $args[$i]).TrimStart("-")
    if ($tok -eq "NoPull") { continue }
    $hit = @("Pick", "SkipSweep", "NoOpen") | Where-Object { $_ -ieq $tok } | Select-Object -First 1
    if ($hit) { $pass[$hit] = $true; continue }
    $val = @("ApplyInput", "SystemDir", "DataDir") | Where-Object { $_ -ieq $tok } | Select-Object -First 1
    if ($val -and ($i + 1) -lt $args.Count) { $pass[$val] = "" + $args[$i + 1]; $i++; continue }
    Write-Host ("  [啟動器] 不認得的參數:" + $args[$i] + "(可用 -Pick -ApplyInput <json> -SkipSweep -NoOpen -SystemDir <夾> -DataDir <夾> -NoPull)") -ForegroundColor Yellow
}
Write-Host ("  [啟動器] " + $oc.Name) -ForegroundColor Cyan
& $oc.FullName @pass
exit $LASTEXITCODE
