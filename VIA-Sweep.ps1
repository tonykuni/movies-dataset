# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# VIA-Sweep.ps1 — 倉根啟動器:VCGC 全景實測一鍵(操作員令 2026-09-28「照流程 · 全自動 · 最後要通過實測」)
# 站在倉根(movies-dataset)打:  .\VIA-Sweep.ps1
# 做的事:git pull --ff-only → 找 VeritasIntelligenceAnalytics\Invoke-VIA-Sweep-v*.ps1 最新一支 → 跑它
#        (VCGC 入口 → VDF/VRN 兩條鏈 → 橋掃乾跑 → 全景 → DB 面板 → 工具註冊/覆蓋/舊副本)→ 實測貼回包自動放進剪貼簿,回 Claude 對話框 Ctrl+V。
# 參數原樣轉:-SkipChains · -SkipPanel · -SkipTools · -Zip <上傳的 zip> · -RetireOld · -NoClipboard · -PlainReport · -Rows N · -NoPull(啟動器也不拉)。
# 只量不修(-RetireOld 例外:只 git rm 探針判「沒有任何引用」的舊副本);不代開網路同意閘。
# 政策附冊 PSGATE-1:實測腳本第一步一定先從 VCGC 跑過流程(沒過就停);PS 加速模板 + rich 詳細摘要矩陣。
$here = $PSScriptRoot
try {
    $join = Join-Path $here "VeritasIntelligenceAnalytics\supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $join) { . $join; Write-Host ("  [加速器] 套對 " + $script:CeleritasPS7.Version) -ForegroundColor DarkGray }
} catch {
    Write-Host "  [加速器] 正主載入失敗,略過" -ForegroundColor DarkGray
}
$env:GIT_EDITOR = "true"
$env:GIT_TERMINAL_PROMPT = "0"
if ($args -notcontains "-NoPull") {
    Write-Host "  [啟動器] git pull --ff-only" -ForegroundColor Cyan
    $g = @(git -C $here pull --ff-only 2>&1 | ForEach-Object { "" + $_ })
    if ($g.Count -gt 0) { Write-Host ("            " + $g[$g.Count - 1]) -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ne 0) { Write-Host "            git pull 沒成功(本機有改動或分叉);照現有碼繼續" -ForegroundColor Yellow }
}
$sweep = Get-ChildItem -LiteralPath (Join-Path $here "VeritasIntelligenceAnalytics") -Filter "Invoke-VIA-Sweep-v*.ps1" -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if ($null -eq $sweep) {
    Write-Host "  [啟動器] 找不到 VeritasIntelligenceAnalytics\Invoke-VIA-Sweep-v*.ps1(先 git pull)" -ForegroundColor Red
    exit 3
}
# 參數轉成雜湊表再展開(字串陣列展開時 "-SkipChains" 不一定被當成參數名)
$pass = @{}
for ($i = 0; $i -lt $args.Count; $i++) {
    $tok = ("" + $args[$i]).TrimStart("-")
    if ($tok -eq "NoPull") { continue }
    $hit = @("SkipChains", "SkipPanel", "SkipTools", "RetireOld", "NoClipboard", "PlainReport") | Where-Object { $_ -ieq $tok } | Select-Object -First 1
    if ($hit) { $pass[$hit] = $true; continue }
    if ($tok -ieq "Rows" -and ($i + 1) -lt $args.Count) { $pass["Rows"] = [int]$args[$i + 1]; $i++; continue }
    if ($tok -ieq "Zip" -and ($i + 1) -lt $args.Count) { $pass["Zip"] = "" + $args[$i + 1]; $i++; continue }
    Write-Host ("  [啟動器] 不認得的參數:" + $args[$i] + "(可用 -SkipChains -SkipPanel -SkipTools -Zip <zip> -RetireOld -NoClipboard -PlainReport -Rows N -NoPull)") -ForegroundColor Yellow
}
Write-Host ("  [啟動器] " + $sweep.Name) -ForegroundColor Cyan
& $sweep.FullName @pass
$rc = $LASTEXITCODE
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
exit $rc
