#requires -Version 7.0
param(
    [string]$ProjectRoot = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [string]$DataDir = '',
    [string]$PkgParent = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\PMIS-Lite',
    [string]$Python = 'python',
    [string]$OutDir = 'C:\VIA_RUNS\VIS_Launch'
)

$script:Header1 = 'VeritasIntelligenceAnalytics Environment Governance Nexus (VEGN)'
$script:Header2 = 'VERITAS INTELLIGENCE SYSTEM'
$script:Header3 = 'VIS Launch-All v1.0 . 模組盤點 -> 引擎擷取 -> 測試 -> HTML 報告 . 100% 唯讀'

Write-Host ''
Write-Host $script:Header1 -ForegroundColor Cyan
Write-Host $script:Header2 -ForegroundColor Cyan
Write-Host $script:Header3 -ForegroundColor DarkCyan
Write-Host ''

if (-not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}
$script:DriverPath = Join-Path $PkgParent 'SUP_MDL112_LaunchDriver.py'
if (-not (Test-Path -LiteralPath $script:DriverPath)) {
    Write-Host "找不到驅動器: ${script:DriverPath}" -ForegroundColor Red
    Write-Host '請確認 PkgParent 指向含 SUP_MDL112_LaunchDriver.py 與 pmis_lite 的資料夾。' -ForegroundColor Yellow
    return
}

Write-Progress -Id 1 -Activity 'VIS Launch-All' -Status '啟動 Python 驅動器...' -PercentComplete 20

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $Python
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.ArgumentList.Add($script:DriverPath)
$psi.ArgumentList.Add('--root'); $psi.ArgumentList.Add($ProjectRoot)
if ($DataDir -ne '') { $psi.ArgumentList.Add('--data'); $psi.ArgumentList.Add($DataDir) }
$psi.ArgumentList.Add('--out'); $psi.ArgumentList.Add($OutDir)
$psi.ArgumentList.Add('--pkg'); $psi.ArgumentList.Add($PkgParent)

$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi
$null = $proc.Start()
$outTask = $proc.StandardOutput.ReadToEndAsync()
$errTask = $proc.StandardError.ReadToEndAsync()
$proc.WaitForExit()
$stdout = $outTask.Result
$stderr = $errTask.Result

Write-Progress -Id 1 -Activity 'VIS Launch-All' -Status '讀取結果...' -PercentComplete 60

$script:ReportJson = Join-Path $OutDir 'via_launch_report.json'
if (-not (Test-Path -LiteralPath $script:ReportJson)) {
    Write-Host '驅動器未產出報告 JSON。stderr:' -ForegroundColor Red
    Write-Host $stderr -ForegroundColor DarkGray
    return
}
$rep = Get-Content -LiteralPath $script:ReportJson -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Progress -Id 1 -Activity 'VIS Launch-All' -Status '產生 HTML 報告...' -PercentComplete 85

$mods = $rep.modules
$ing = $rep.ingest
$tst = $rep.tests

$rowsHtml = ''
foreach ($it in $mods.inventory) {
    $rowsHtml += "<tr><td>$($it.module)</td><td>$($it.role)</td><td>$($it.fan_in)</td><td>$($it.lines)</td><td>$($it.type)</td></tr>`n"
}
$byRole = ''
foreach ($k in $mods.by_role.PSObject.Properties) {
    $byRole += "<span class='pill'>$($k.Name): $($k.Value)</span> "
}
$termHtml = ''
if ($ing.summary) { foreach ($t in $ing.summary.key_terms) { $termHtml += "<span class='pill'>$t</span> " } }
$pointHtml = ''
if ($ing.summary) { foreach ($p in $ing.summary.key_points) { $pointHtml += "<li>$p</li>" } }

$guarantee = if ($ing.completeness) { $ing.completeness.guarantee_pass } else { 'N/A' }
$coverage = if ($ing.completeness) { $ing.completeness.coverage_pct } else { 'N/A' }
$gap = if ($ing.completeness) { $ing.completeness.unexplained_gap } else { 'N/A' }
$testLine = "$($tst.passed) / $($tst.total) PASS . 失敗 $($tst.failed)"
$conclusion = if ($tst.failed -eq 0 -and $guarantee -eq $true) { '全部通過 . 引擎健康 . 完整性已保證' } else { '有項目需檢視 . 見上方紅字' }

$css = 'body{background:#f5f4f0;color:#1e1d1a;font-family:"DM Sans",system-ui,sans-serif;margin:0;padding:32px}h1{font-family:Syne,sans-serif;font-size:22px;letter-spacing:1px}h2{font-size:15px;border-bottom:1px solid #dbd9d3;padding-bottom:6px;margin-top:28px}table{border-collapse:collapse;width:100%;font-size:12px;background:#fff}th,td{border:1px solid #dbd9d3;padding:5px 8px;text-align:left}th{background:#efeee9}.pill{display:inline-block;background:#fff;border:1px solid #dbd9d3;border-radius:3px;padding:2px 8px;margin:2px;font-size:12px}.ok{color:#5a9e6f;font-weight:600}.bad{color:#c96b5a;font-weight:600}.mono{font-family:"DM Mono",monospace}.card{background:#fff;border:1px solid #dbd9d3;border-radius:3px;padding:14px 18px;margin:10px 0}'

$okClass = if ($tst.failed -eq 0) { 'ok' } else { 'bad' }
$gClass = if ($guarantee -eq $true) { 'ok' } else { 'bad' }

$html = @"
<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>
<title>VIS Launch-All Report</title><style>$css</style></head><body>
<h1>VIS LAUNCH-ALL . 啟動測試報告</h1>
<div class='mono' style='color:#6b6a66'>$script:Header3</div>
<div class='card'>專案根目錄: <span class='mono'>$ProjectRoot</span></div>

<h2>1. 模組盤點 (SUPPORTIVE / FUNCTIONAL)</h2>
<div class='card'>共 <b>$($mods.count)</b> 個模組 &nbsp; $byRole</div>
<table><thead><tr><th>模組</th><th>角色</th><th>fan-in</th><th>行數</th><th>型別</th></tr></thead>
<tbody>
$rowsHtml
</tbody></table>

<h2>2. 引擎擷取 . 完整性保證</h2>
<div class='card'>
檔案數: $($ing.files) &nbsp;|&nbsp; 覆蓋率: <b>$coverage%</b> &nbsp;|&nbsp;
未解釋遺漏: <b>$gap</b> &nbsp;|&nbsp; 保證全抓: <span class='$gClass'>$guarantee</span><br>
去重模式: $($ing.dedup.mode) &nbsp;|&nbsp; 資料筆數: $($ing.data_count) &nbsp;|&nbsp; CSV: <span class='mono'>$($ing.csv)</span>
</div>

<h2>3. 重點摘要</h2>
<div class='card'>關鍵詞: $termHtml<ul>$pointHtml</ul></div>

<h2>4. 測試 / Debug</h2>
<div class='card'>結果: <span class='$okClass'>$testLine</span></div>

<h2>結論</h2>
<div class='card'><b>$conclusion</b></div>
</body></html>
"@

$script:HtmlPath = Join-Path $OutDir 'VIS_Launch_Report.html'
[System.IO.File]::WriteAllText($script:HtmlPath, $html, [System.Text.UTF8Encoding]::new($false))

Write-Progress -Id 1 -Activity 'VIS Launch-All' -Completed
Write-Host ("模組 {0} 個 . 測試 {1}/{2} PASS . 完整性保證 {3}" -f $mods.count, $tst.passed, $tst.total, $guarantee) -ForegroundColor Green
Write-Host ("報告: {0}" -f $script:HtmlPath) -ForegroundColor Green
Start-Process $script:HtmlPath

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
