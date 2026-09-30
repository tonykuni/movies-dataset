# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-FullCheck-v0101.ps1 — 整合全景實測一鍵跑 · 跳出 HTML 總報告(Z290;v0100 一字不動)
#   操作員 2026-09-30:「這個ＰＳ指令一定沒有加加速模板自動跳出ＨＴＭＬ」→ pwsh 實測屬實:
#     ① 沒跳頁:v0100 為了不讓引擎各自跳頁先設 VIA_NO_OPEN=1,到 finally 才還原;同一行程的 PS 加速器模組
#        (PS-ACCEL 橋 · VIA_PS_PyProgress_Module · 命令冊都會載)裝了零跳出閘(批366),看到 VIA_NO_OPEN=1 就把
#        Invoke-Item 的 .html 靜默略過 → 總報告從沒跳出(實跑印「[VIA_NO_OPEN] 抑制跳出 …FULLCHECK_latest.html」)。
#        本版:引擎照樣帶 VIA_NO_OPEN=1(子行程不各自跳頁);本支自己的總頁走 Open-VIAOwnPage —— 呼叫端原值不是 1
#        就用 cmdlet 全名直開(零跳出閘只攔不帶模組名的呼叫);呼叫端自己設 1 = 零跳出閘照守,改印黃字教怎麼開。
#     ② 加速模板:改走全樹標準 [VIA:PS-TEMPLATE:v0101] 模板塊(646 支同一段:只動本行程 · 關閉即還原 · 缺席略過);
#        開跑印 Celeritas 狀態(版號 · 已套用 · 執行緒 · 優先權),結尾印模板的 MATRIX SUMMARY(六段燈 · 秒數 · 摘要)。
#     ③ 邊跑邊印:引擎每行即時上色印出(v0100 要等整輪跑完才一次印)。
#     ④ 熱 PS 直接貼也行:VIA_NO_OPEN / VIA_FROM_VCGC / VIA_VCGC_PUSH 與目前資料夾跑完原樣還原;模板只還原本支自己套上的。
#   其餘照 v0100:經 VCGC 主控台跑正主 CGC_MDL248_FullCheck 尾版,六段紅了照跑;每段尾版 · 版號 · sha16 · UTC · 秒數只增寫
#   registry\VIA_VCGC_FullCheck_Ledger_v0100.jsonl;頁 VIA_Reports\fullcheck\FULLCHECK_latest.html。
# 用法(熱 PS 直接貼,站在倉內任何資料夾;或 pwsh -NoProfile -File 這支):
#   & (Get-ChildItem (Join-Path (git rev-parse --show-toplevel) 'VeritasIntelligenceAnalytics\launchers\Invoke-VIA-FullCheck-v*.ps1') | Sort-Object Name | Select-Object -Last 1).FullName
#   參數 [-Full] [-Grid] [-NoOpen] [-Only 0,5] [-SystemDir <VIA 夾>];結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件
# 不抓網路、不寫庫、不 push、不代開同意閘;只經 Invoke-VIAPython 叫 python。
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Full,
    [switch]$Grid,
    [switch]$NoOpen,
    [string]$Only = "",
    [string]$SystemDir = ""
)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
$VIAFcCelOwn = $VIACelTplOwn   # 先記下:加速模組點源的 25 冊(Roster v0100)自帶模板塊,會把 $VIACelTplOwn 蓋成 $false(Z290 附帶)
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

function Open-VIAOwnPage {
    # [VIA:OWN-PAGE:v0100] 開本支自己的總頁(Z290):子行程照吃 VIA_NO_OPEN=1(零跳出閘);本支只看呼叫端原值
    param([Parameter(Mandatory)][string]$Page, [string]$CallerNoOpen = "")
    if (-not (Test-Path -LiteralPath $Page)) {
        Write-Host ("  [頁] 這輪沒產出總報告頁(看上面紅字):" + $Page) -ForegroundColor Red
        return $false
    }
    if ($CallerNoOpen -eq "1") {
        Write-Host ("  [頁] 這個視窗本來就設了 VIA_NO_OPEN=1(零跳出閘照守)→ 不開。要開:Remove-Item Env:VIA_NO_OPEN 再跑,或手動開 " + $Page) -ForegroundColor Yellow
        return $false
    }
    try {
        Microsoft.PowerShell.Management\Invoke-Item -LiteralPath $Page -ErrorAction Stop   # 帶模組名 = 不經零跳出閘代理
        Write-Host ("  [頁] 已跳出 " + $Page) -ForegroundColor Green
        return $true
    } catch {
        Write-Host ("  [頁] 開不了瀏覽器(手動開 " + $Page + "):" + $_.Exception.Message) -ForegroundColor Yellow
        return $false
    }
}

$VIA = if ($SystemDir) { $SystemDir } else { Split-Path -Parent $PSScriptRoot }
$StartDir = (Get-Location).Path
$prev = @{ FROM = $env:VIA_FROM_VCGC; PUSH = $env:VIA_VCGC_PUSH; OPEN = $env:VIA_NO_OPEN }
$exitCode = 0
try {
    if (-not (Test-Path -LiteralPath (Join-Path $VIA "supportive modules\registry"))) {
        Write-Host ("  [整合全景實測] 找不到系統夾 " + $VIA + "(用 -SystemDir 指到 VeritasIntelligenceAnalytics)") -ForegroundColor Red
        $exitCode = 3
        return
    }
    Set-Location -LiteralPath $VIA
    $cel = $null
    if (Get-Command Get-CeleritasStatus -ErrorAction SilentlyContinue) { try { $cel = Get-CeleritasStatus } catch { $cel = $null } }
    if ($cel) {
        Write-Host ("  [加速模板] Celeritas PS7 " + $cel.Version + " · 已套用 " + $cel.Applied + " · 執行緒 " + $cel.Workers + " / " + $cel.Cores + " 核 · 優先權 " + $cel.Priority + " · 只動本行程 PID " + $PID + $(if ($VIAFcCelOwn) { "(本支套上 · 跑完還原)" } else { "(沿用本視窗已套的模板)" })) -ForegroundColor DarkCyan
    } else {
        Write-Host "  [加速模板] 沒接上(supportive modules\ps7\VeritasCeleritas.PS7.ps1 不在,或不是 PowerShell 7)· 照跑,不加速" -ForegroundColor Yellow
    }
    $env:VIA_FROM_VCGC = "YES"
    $env:VIA_VCGC_PUSH = "NO"
    $env:VIA_NO_OPEN = "1"   # 只給引擎與子行程(不各自跳頁);本支自己的總頁走 Open-VIAOwnPage
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
        if (Test-Path -LiteralPath $pyMod) { . $pyMod }
    }
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        Write-Host "  [整合全景實測] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $reg = Join-Path $VIA "supportive modules\registry"
    $console = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $engine = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL248_FullCheck_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $console -or $null -eq $engine) {
        Write-Host "  [整合全景實測] VCGC 主控台或 CGC_MDL248_FullCheck 尾版不在(先 git pull)" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $argList = @("run", "--family", "core", "CGC_MDL248_FullCheck", "run")
    if ($Full) { $argList += "--full" }
    if ($Grid) { $argList += "--grid" }
    if ($Only) { $argList += @("--only", $Only) }
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  VIA 整合全景實測 v0101 · VCGC → VDF → VRN → SUP · 紅了照跑   ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ("  [正主] " + $engine.Name + " · 經 " + $console.Name + $(if ($Full) { " · 全部重量" } else { " · 沒變的沿用" }) + $(if ($Grid) { " · 格子整張重跑" } else { " · 格子讀存證" })) -ForegroundColor DarkGray
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $t0 = [DateTime]::UtcNow
    $timeout = if ($Grid) { 7200 } else { 3600 }
    $lines = [System.Collections.Generic.List[string]]::new()
    $body = {
        Invoke-VIAPython -Family 'core' -TimeoutSec $timeout $console.FullName @argList 2>&1 | ForEach-Object {
            $s = "" + $_
            $lines.Add($s)
            $color = if ($s -match '\bRED\b|紅') { "Red" } elseif ($s -match '\bYELLOW\b|黃') { "Yellow" } elseif ($s -match '\bGREEN\b') { "Green" } else { "Gray" }
            Write-Host $s -ForegroundColor $color
        }
    }
    $global:LASTEXITCODE = 0
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { $null = Invoke-VIACeleritasScoped -Body $body } else { $null = & $body }
    $rc = $global:LASTEXITCODE
    $exitCode = if ($rc -in 0, 1, 2) { $rc } else { 1 }
    $env:VIA_NO_OPEN = $prev.OPEN   # 引擎跑完就換回呼叫端原值(v0100 到 finally 才還原)
    $rows = @()
    $verdict = ""
    $json = Join-Path $VIA "VIA_Reports\fullcheck\FULLCHECK_latest.json"
    if ((Test-Path -LiteralPath $json) -and ((Get-Item -LiteralPath $json).LastWriteTimeUtc -ge $t0.AddSeconds(-2))) {
        try {
            $rep = Get-Content -LiteralPath $json -Raw -Encoding utf8 | ConvertFrom-Json
            $verdict = "" + $rep.verdict
            $rows = @($rep.steps | ForEach-Object { [pscustomobject]@{ id = "" + $_.n; title = (("" + $_.name) -replace '\s*[\(（].*$', ''); state = "" + $_.lamp; sec = "" + $_.secs; note = "" + $_.summary } })
        } catch { $rows = @() }
    }
    if ($rows.Count -gt 0) {
        $shown = $false
        if (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue) {
            try { Write-CeleritasMatrixSummary -Rows $rows -Title ("VIA 整合全景實測 · 六段總覽 · 總判 " + $verdict); $shown = $true } catch { $shown = $false }
        }
        if (-not $shown) {
            Write-Host ("  ━━ 六段總覽 · 總判 " + $verdict + " ━━") -ForegroundColor Cyan
            foreach ($r in $rows) { Write-Host ("  " + $r.id + " " + $r.state.PadRight(7) + " " + ("" + $r.sec).PadLeft(7) + "s  " + $r.title + " · " + $r.note) }
        }
    } else {
        Write-Host "  [總覽] 本輪沒寫出 FULLCHECK_latest.json(看上面紅字)" -ForegroundColor Yellow
    }
    $page = Join-Path $VIA "VIA_Reports\fullcheck\FULLCHECK_latest.html"
    Write-Host ("  [計時] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $exitCode + "(0 綠 · 2 黃 · 1 紅)") -ForegroundColor Cyan
    Write-Host ("  [總報告] " + $page) -ForegroundColor Cyan
    if (-not $NoOpen) { [void](Open-VIAOwnPage -Page $page -CallerNoOpen $prev.OPEN) }
} finally {
    $env:VIA_FROM_VCGC = $prev.FROM
    $env:VIA_VCGC_PUSH = $prev.PUSH
    $env:VIA_NO_OPEN = $prev.OPEN
    if ($VIAFcCelOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原(只還原本支自己套上的)
    Set-Location -LiteralPath $StartDir
}
exit $exitCode
