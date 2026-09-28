# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# VIA-DBPanel.ps1 — 倉根啟動器(操作員令 2026-09-28「one powershell code to handle all」)
# 站在倉根(movies-dataset)打:  .\VIA-DBPanel.ps1
# 做的事:git pull --ff-only → 找 VeritasIntelligenceAnalytics\Invoke-VIA-DBPanel-v*.ps1 最新一支 → 帶著你給的參數跑它(加 -NoPull,已拉過)。
# 面板唯讀;跑完貼回包自動放進剪貼簿,回 Claude 對話框按 Ctrl+V 即可。
# 其餘參數原樣轉給面板:-SkipCatalog · -NoEolFix · -Rows N · -PlainReport · -BuildUi · -NoClipboard · -NoPull(啟動器也不拉)。
$here = $PSScriptRoot
$env:GIT_EDITOR = "true"
$env:GIT_TERMINAL_PROMPT = "0"
if ($args -notcontains "-NoPull") {
    Write-Host "  [啟動器] git pull --ff-only" -ForegroundColor Cyan
    $g = @(git -C $here pull --ff-only 2>&1 | ForEach-Object { "" + $_ })
    if ($g.Count -gt 0) { Write-Host ("            " + $g[$g.Count - 1]) -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ne 0) { Write-Host "            git pull 沒成功(本機有改動或分叉);照現有碼繼續" -ForegroundColor Yellow }
}
$panel = Get-ChildItem -LiteralPath (Join-Path $here "VeritasIntelligenceAnalytics") -Filter "Invoke-VIA-DBPanel-v*.ps1" -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if ($null -eq $panel) {
    Write-Host "  [啟動器] 找不到 VeritasIntelligenceAnalytics\Invoke-VIA-DBPanel-v*.ps1(先 git pull)" -ForegroundColor Red
    exit 3
}
# 參數轉成雜湊表再展開(字串陣列展開時 "-SkipCatalog" 不一定被當成參數名)
$pass = @{ NoPull = $true }
$switches = @("SkipCatalog", "NoEolFix", "BuildUi", "PlainReport", "NoClipboard")
for ($i = 0; $i -lt $args.Count; $i++) {
    $tok = ("" + $args[$i]).TrimStart("-")
    if ($tok -eq "NoPull") { continue }
    $hit = $switches | Where-Object { $_ -ieq $tok } | Select-Object -First 1
    if ($hit) { $pass[$hit] = $true; continue }
    if ($tok -ieq "Rows" -and ($i + 1) -lt $args.Count) { $pass["Rows"] = [int]$args[$i + 1]; $i++; continue }
    Write-Host ("  [啟動器] 不認得的參數:" + $args[$i] + "(可用 -SkipCatalog -NoEolFix -Rows N -PlainReport -BuildUi -NoClipboard -NoPull)") -ForegroundColor Yellow
}
Write-Host ("  [啟動器] " + $panel.Name) -ForegroundColor Cyan
& $panel.FullName @pass
exit $LASTEXITCODE
