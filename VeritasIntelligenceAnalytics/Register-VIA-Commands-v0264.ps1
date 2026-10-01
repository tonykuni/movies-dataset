# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0264.ps1 — R35c(2026-10-01):+via-ui-all(別名 全部UI)· 跑完自動跳出 U/I。
#   操作員令「自動跳出所有U/I」= L70 這一次的許可:只加這兩件;v0263 以前一字不動。
#   為什麼不直接把 VIA_NO_OPEN 關掉:批378 零跳出律的根因是 .html 預設程式 = VS Code,python 端 os.startfile 一開就是 VS Code。
#   本版照舊不碰 VIA_NO_OPEN,改走 via-open 同一條「只叫瀏覽器 exe」的道:一次把頁全開成同一個瀏覽器視窗的分頁。
#   via-ui-all [-Hours N] [-All] [-List]
#     預設:主要 U/I(全景監控 · 首頁擷取總覽 · 四點文摘 · 收尾 · VCGC 流程矩陣 / 中控台 · 模板同步索引 · 家族 U/I · 入口 ·
#           總控 · 輸入主控台 · 接棒)在位的全開,再加 VIA_Reports 底下最近 N 小時(預設 24)改過的 *.html;最多 25 頁。
#     -All:VIA_Reports 底下所有 *_latest.html 都開(仍最多 40 頁);-List:只列不開。
#   跑完自動跳出:via-closeout · via-vcgc 包一層 —— 原指令跑完後,把**這一輪新寫出 / 改過**的 VIA_Reports *.html 用瀏覽器開出來
#     (沒有新頁就不開)。關掉:$env:VIA_UI_AUTOPOP = "0";VIA_NO_OPEN 照舊管 python 端(不會再跳 VS Code)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0263.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:Get-VIABrowserExe {
    @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
      "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
      "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe") |
        Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
}

function global:Open-VIAPagesInBrowser {
    param([string[]]$Paths, [string]$Tag = "via-ui-all")
    $p = @($Paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
    if ($p.Count -eq 0) { Write-Host ("  [" + $Tag + "] 沒有可開的頁") -ForegroundColor DarkGray; return }
    $bx = Get-VIABrowserExe
    if (-not $bx) {
        Write-Host ("  [" + $Tag + "] 未找到瀏覽器 exe(Edge / Chrome / Firefox);請手動以瀏覽器開:") -ForegroundColor Yellow
        $p | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        return
    }
    Start-Process -FilePath $bx -ArgumentList @($p | ForEach-Object { "`"" + $_ + "`"" })
    Write-Host ("  [" + $Tag + "] " + (Split-Path $bx -Leaf) + " 開 " + $p.Count + " 頁(同一視窗分頁;不經 VS Code)") -ForegroundColor Green
    $p | ForEach-Object { Write-Host ("     " + $_.Replace($VIA, "<VIA>")) -ForegroundColor DarkGray }
}

function global:Get-VIAUiPages {
    param([double]$Hours = 24, [switch]$All, [datetime]$Since = [datetime]::MinValue, [int]$Max = 25)
    $rep = Join-Path $VIA "VIA_Reports"
    $ui = Join-Path $VIA "supportive modules\ui_support"
    $out = New-Object System.Collections.Generic.List[string]
    if ($Since -eq [datetime]::MinValue) {
        $core = @(
            "VIA_Reports\panorama\monitor_latest.html", "VIA_Reports\panorama\dashboard_latest.html",
            "VIA_Reports\first_page_text\FIRSTPAGE_SUMMARY.html", "VIA_Reports\vrn\four_point\DIGEST_latest.html",
            "VIA_Reports\closeout\CLOSEOUT_latest.html", "VIA_Reports\vcgc\VIA_Flow_Matrix_v0100.html",
            "VIA_Reports\vcgc\VIA_UI_CentralGovernanceConsole_v0100.html", "VIA_Reports\template_adapter\SYNC_INDEX_latest.html",
            "VIA_Reports\ui\FAMILY_UI_latest.html", "VIA_Reports\entry\ENTRY_latest.html")
        foreach ($c in $core) { $f = Join-Path $VIA $c; if (Test-Path -LiteralPath $f) { $out.Add($f) } }
        foreach ($k in @("VIA_UI_MasterControl", "VIA_UI_InputConsole", "VIA_UI_Handover")) {
            $f = Get-ChildItem -LiteralPath $ui -Filter ($k + "*.html") -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
            if ($f) { $out.Add($f.FullName) }
        }
    }
    if (Test-Path -LiteralPath $rep) {
        $cut = if ($Since -ne [datetime]::MinValue) { $Since } else { (Get-Date).AddHours(-$Hours) }
        $more = Get-ChildItem -LiteralPath $rep -Recurse -File -Filter "*.html" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '[\\/]converted[\\/]' } |
            Where-Object { ($All -and $_.Name -like "*_latest.html") -or ($_.LastWriteTime -ge $cut) } |
            Sort-Object LastWriteTime -Descending
        foreach ($m in $more) { if (-not $out.Contains($m.FullName)) { $out.Add($m.FullName) } }
    }
    @($out | Select-Object -First $Max)
}

function global:via-ui-all {
    if (-not $VIA -or -not (Test-Path -LiteralPath $VIA)) { Write-Host "  [via-ui-all] FAIL:`$VIA 不在(先點源命令冊)" -ForegroundColor Red; return }
    $h = 24; $all = $false; $list = $false
    for ($i = 0; $i -lt $args.Count; $i++) {
        $t = ("" + $args[$i]).TrimStart("-")
        if ($t -ieq "Hours" -and ($i + 1) -lt $args.Count) { [double]::TryParse(("" + $args[$i + 1]), [ref]$h) | Out-Null; $i++ }
        elseif ($t -ieq "All") { $all = $true }
        elseif ($t -ieq "List") { $list = $true }
    }
    $pages = Get-VIAUiPages -Hours $h -All:$all -Max $(if ($all) { 40 } else { 25 })
    if ($list) { Write-Host ("  [via-ui-all] " + $pages.Count + " 頁(只列不開)") -ForegroundColor Cyan; $pages | ForEach-Object { Write-Host ("     " + $_.Replace($VIA, "<VIA>")) }; return }
    Open-VIAPagesInBrowser -Paths $pages -Tag "via-ui-all"
}
Set-Alias -Name 全部UI -Value via-ui-all -Scope Global -Force

# 跑完自動跳出:包 via-closeout / via-vcgc(原定義照叫;只多「本輪新頁 → 瀏覽器」一步)
foreach ($cmdName in @("via-closeout", "via-vcgc")) {
    $orig = Get-Command -Name $cmdName -CommandType Function -ErrorAction SilentlyContinue
    if (-not $orig) { continue }
    Set-Variable -Name ("VIAOrig_" + $cmdName.Replace("-", "_")) -Scope Global -Value $orig.ScriptBlock -Force
    $body = @"
`$t0 = Get-Date
try { & `$global:VIAOrig_$($cmdName.Replace("-", "_")) @args }
finally {
    if (`$env:VIA_UI_AUTOPOP -ne "0" -and (`$args -notcontains "--card") -and (`$args -notcontains "--selftest")) {
        `$new = Get-VIAUiPages -Since `$t0.AddSeconds(-2) -Max 25
        if (`$new.Count -gt 0) { Open-VIAPagesInBrowser -Paths `$new -Tag "$cmdName 自動跳出" }
    }
}
"@
    Set-Item -Path ("Function:\global:" + $cmdName) -Value ([scriptblock]::Create($body)) -Force
}
