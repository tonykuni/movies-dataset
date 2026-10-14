# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-OneShot-v0100.ps1 — 收尾一鍵:把這輪該跑的全部串成一個指令(紅了照跑),最後一頁總報告自動跳出
#   操作員 2026-10-14:「丟失的文件可到隔離區尋找 修正完善收尾功能不要發散 VDF VRN 輸出 HEADER 還要檢查全面 自動更新台股清單及
#   主動式台股 ETF 全清單 ETF 資料要抓到 NAV AUM CASH INFLOW AND OUT FLOW AND BREAKDOWN 輸出 HEADER 完整確認然後 DATAFRAME 固定
#   … 回顧對話紀錄 AI 常做的動作做引擎 … 上面有很多指令未執行 整合起來進一個 ps 指令一起執行 … with the latest accelerator modules
#   and network modules 100% coverage. ps code are also equipped with accelerator function」(本令即 L70 逐次許可;新檔,不動任何舊 .ps1)
#   本支不另寫任何邏輯,只把既有正主依序叫一遍(L120:VCGC · VDF · VRN 各走自己的入口 / 管理器,平等並列):
#     ①  VCGC 省 Token(token)                   ②  VCGC 交接 check(handoff check)
#     ③  隔離區找回(CGC_MDL276 lost)            ④  AI 庫卡(CGC_MDL277 dbcard:每表列數 · 日期區間 → 先看卡再決定抓不抓)
#     ⑤  VDF 台股清單 + 主動式台股 ETF 全清單 → 全部步並行擷取(Invoke-VIA-VdfFetch 尾版;沒 -Consent = -Dry 只看計畫)
#     ⑥  主動 ETF NAV · AUM · 單位數 · 淨流入 / 流出(VDF_ENG094 fetch;毛申購 / 毛贖回查無官方來源 → 照實 NULL)
#     ⑦  主動 ETF 持股 / 產業 breakdown(VDF_ENG094 breakdown;零網路)
#     ⑧  VDF 管理器 status(VDF_SystemManager 尾版)   ⑨  VRN 管理器 status(VRN_SystemManager 尾版)
#     ⑩  輸出表頭全面檢查 + DataFrame 固定(CGC_MDL249 all:check → coverage 全部輸出庫 → lock)
#     ⑪  PS 檢查(CGC_MDL277 pslint:加速器橋 · 自壓頁)   ⑫  撞號(CGC_MDL277 collide --base origin/main)
#     ⑬  整合全景實測(CGC_MDL248 FullCheck)        ⑭  VCGC 收尾(closeout:交接閘 → 重測 → 註冊 → 編號 → SDD → checkpoint)
#     ⑮  AI 狀態索引(CGC_MDL277 status:93 份報告的判決 + 交接頭 → 一個小檔)
#   頁:VIA_Reports\aiops\AIOPS_RUN_latest.html(CGC_MDL277 report;同 JSON),跑完走 Open-VIAOwnPage 自動跳出(-NoOpen 不開)。
# 用法(熱 PS 直接貼,站在倉內任何資料夾;或 pwsh -NoProfile -File 這支):
#   & (Get-ChildItem (Join-Path (git rev-parse --show-toplevel) 'VeritasIntelligenceAnalytics\launchers\Invoke-VIA-OneShot-v*.ps1') | Sort-Object Name | Select-Object -Last 1).FullName
#   參數 [-Consent] [-Apply] [-Since YYYY-MM-DD] [-Grid] [-Only 1,5,10] [-NoOpen] [-SystemDir <VIA 夾>];結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件
#   -Consent  = 操作員親手開同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 只在本行程設 YES,跑完還原);AI 不代打這個旗標
#   -Apply    = 寫入:ENG094 結果進庫 · DataFrame 鎖帳 · VCGC closeout --apply(仍不 push:VIA_VCGC_PUSH=NO)
# 只經 Invoke-VIAPython 叫 python;不 push、不刪檔、不代開同意閘、不碰 TA-Lib。
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Consent,
    [switch]$Apply,
    [string]$Since = "",
    [switch]$Grid,
    [string]$Only = "",
    [switch]$NoOpen,
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
$VIAOsCelOwn = $VIACelTplOwn   # 先記下:加速模組點源的 25 冊(Roster v0100)自帶模板塊,會把 $VIACelTplOwn 蓋成 $false(Z290 附帶)
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
$prev = @{ FROM = $env:VIA_FROM_VCGC; PUSH = $env:VIA_VCGC_PUSH; OPEN = $env:VIA_NO_OPEN; NET = $env:VIA_NET_CONSENT; SCRAPE = $env:VIA_SCRAPE_CONSENT }
$exitCode = 0
$stages = [System.Collections.Generic.List[object]]::new()
$onlySet = @($Only -split "[,\s]+" | Where-Object { $_ } | ForEach-Object { [int]$_ })

function Get-VIAOsTail([string]$Dir, [string]$Filter) {
    # 尾版 = 版號最大(不照檔名字典序;-v / _v 兩種都認)
    Get-ChildItem -LiteralPath $Dir -Filter $Filter -File -ErrorAction SilentlyContinue |
        Sort-Object { if ($_.BaseName -match '[-_]v(\d+)$') { [int]$Matches[1] } else { -1 } } | Select-Object -Last 1
}

function Invoke-VIAOsStage {
    # 跑一段:即時印 · 收 rc / 秒 / 判決行 · 抓網段(-Net)遇同意閘關 = SKIP(不是紅;其他段照 rc 判)· 紅了照跑下一段
    param([int]$N, [string]$Name, [string]$By, [scriptblock]$Run, [switch]$Net)
    if ($onlySet.Count -gt 0 -and $onlySet -notcontains $N) {
        $stages.Add([ordered]@{ n = $N; name = $Name; by = $By; lamp = "SKIP"; rc = $null; sec = 0; note = "-Only 沒選" })
        return
    }
    Write-Host ""
    Write-Host ("  ── " + $N + " · " + $Name + " · " + $By) -ForegroundColor Cyan
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $buf = [System.Collections.Generic.List[string]]::new()
    $global:LASTEXITCODE = 0
    $wrap = {
        & $Run 2>&1 | ForEach-Object {
            $s = "" + $_
            $buf.Add($s)
            $color = if ($s -match '\bRED\b|FAIL|紅') { "Red" } elseif ($s -match '\bYELLOW\b|NODATA|黃') { "Yellow" } elseif ($s -match '\bGREEN\b|PASS') { "Green" } else { "Gray" }
            Write-Host ("     " + $s) -ForegroundColor $color
        }
    }
    try {
        if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { $null = Invoke-VIACeleritasScoped -Body $wrap } else { $null = & $wrap }
        $rc = $global:LASTEXITCODE
    } catch {
        $buf.Add("例外:" + $_.Exception.Message)
        $rc = 1
    }
    $text = $buf -join "`n"
    $gated = $Net -and ($text -match 'NO_CONSENT|同意閘未開') -and ($rc -ne 0)
    $lamp = if ($gated) { "SKIP" } elseif ($rc -eq 0) { "GREEN" } elseif ($rc -in 2, 3, 4) { "YELLOW" } else { "RED" }
    $judge = @($buf | Where-Object { $_ -match 'GREEN|YELLOW|RED|PASS|FAIL|NODATA|判|\[計\]|state' } | Select-Object -Last 4) -join " ‖ "
    if (-not $judge) { $judge = @($buf | Select-Object -Last 2) -join " ‖ " }
    if ($lamp -eq "SKIP") { $judge = "同意閘未開(操作員親打 -Consent 才抓網)‖ " + $judge }
    $sec = [Math]::Round($clock.Elapsed.TotalSeconds, 1)
    $stages.Add([ordered]@{ n = $N; name = $Name; by = $By; lamp = $lamp; rc = $rc; sec = $sec; note = $judge })
    Write-Host ("  ── " + $N + " · " + $lamp + " · rc " + $rc + " · " + $sec + "s") -ForegroundColor $(if ($lamp -eq "GREEN") { "Green" } elseif ($lamp -eq "RED") { "Red" } else { "Yellow" })
}

try {
    if (-not (Test-Path -LiteralPath (Join-Path $VIA "supportive modules\registry"))) {
        Write-Host ("  [收尾一鍵] 找不到系統夾 " + $VIA + "(用 -SystemDir 指到 VeritasIntelligenceAnalytics)") -ForegroundColor Red
        $exitCode = 3
        return
    }
    Set-Location -LiteralPath $VIA
    $reg = Join-Path $VIA "supportive modules\registry"
    $cel = $null
    if (Get-Command Get-CeleritasStatus -ErrorAction SilentlyContinue) { try { $cel = Get-CeleritasStatus } catch { $cel = $null } }
    if ($cel) {
        Write-Host ("  [加速模板] Celeritas PS7 " + $cel.Version + " · 已套用 " + $cel.Applied + " · 執行緒 " + $cel.Workers + " / " + $cel.Cores + " 核 · 只動本行程 PID " + $PID + $(if ($VIAOsCelOwn) { "(本支套上 · 跑完還原)" } else { "(沿用本視窗已套的模板)" })) -ForegroundColor DarkCyan
    } else {
        Write-Host "  [加速模板] 沒接上(supportive modules\ps7\VeritasCeleritas.PS7.ps1 不在,或不是 PowerShell 7)· 照跑,不加速" -ForegroundColor Yellow
    }
    try {
        $lock = Get-Content -LiteralPath (Join-Path $reg "VIA_ToolVersion_Lock_v0100.json") -Raw -Encoding utf8 | ConvertFrom-Json
        $lk = foreach ($k in 'accelerator', 'network', 'token', 'nlp', 'frame') { if ($lock.$k) { $k + " " + ((Split-Path ("" + $lock.$k.path) -Leaf) -replace '^.*?_(v\d+)\.py$', '$1') } }
        Write-Host ("  [鎖版工具] " + ($lk -join " · ") + "(Python 引擎各自經 ACCEL-BRIDGE / 統包網路工具取鎖版)") -ForegroundColor DarkCyan
    } catch { Write-Host "  [鎖版工具] 鎖冊讀不到(VIA_ToolVersion_Lock_v0100.json)" -ForegroundColor Yellow }
    $env:VIA_FROM_VCGC = "YES"
    $env:VIA_VCGC_PUSH = "NO"
    $env:VIA_NO_OPEN = "1"   # 只給引擎與子行程(不各自跳頁);本支自己的總頁走 Open-VIAOwnPage
    if ($Consent) { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES" }   # 操作員親打 -Consent = 親手開閘;只本行程,finally 還原
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
        if (Test-Path -LiteralPath $pyMod) { . $pyMod }
    }
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        Write-Host "  [收尾一鍵] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $console = Get-VIAOsTail $reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    $vdfMgr = Get-VIAOsTail (Join-Path $VIA "functional modules\VDF") "VDF_SystemManager_v*.py"
    $vrnMgr = Get-VIAOsTail (Join-Path $VIA "functional modules\VRN") "VRN_SystemManager_v*.py"
    $vdfFetch = Get-VIAOsTail $VIA "Invoke-VIA-VdfFetch-v*.ps1"
    if ($null -eq $console) {
        Write-Host "  [收尾一鍵] VCGC 主控台尾版不在(先 git pull)" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $C = $console.FullName
    $ap = if ($Apply) { @("--apply") } else { @() }
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  VIA 收尾一鍵 v0100 · VCGC ‖ VDF ‖ VRN · 15 段 · 紅了照跑     ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ("  [模式] " + $(if ($Consent) { "同意閘開(操作員 -Consent)" } else { "同意閘關(抓網的段 = 計畫 / SKIP)" }) + " · " + $(if ($Apply) { "寫入(-Apply)" } else { "乾跑(-Apply 才寫)" }) + $(if ($Since) { " · 起始 " + $Since } else { "" }) + " · 不 push") -ForegroundColor DarkGray
    $total = [Diagnostics.Stopwatch]::StartNew()

    Invoke-VIAOsStage 1 "VCGC 省 Token" $console.Name { Invoke-VIAPython -Family 'core' -TimeoutSec 600 $C token }
    Invoke-VIAOsStage 2 "VCGC 交接 check" $console.Name { Invoke-VIAPython -Family 'core' -TimeoutSec 900 $C handoff check }
    Invoke-VIAOsStage 3 "隔離區找回(丟失檔)" "CGC_MDL276_QuarantineRecover" { Invoke-VIAPython -Family 'core' -TimeoutSec 900 $C run --family core CGC_MDL276_QuarantineRecover lost }
    Invoke-VIAOsStage 4 "AI 庫卡(先看卡再決定抓不抓)" "CGC_MDL277_AiOps dbcard" { Invoke-VIAPython -Family 'core' -TimeoutSec 900 $C run --family core CGC_MDL277_AiOps dbcard }
    if ($vdfFetch) {
        $pwshExe = (Get-Process -Id $PID).Path   # 子行程用同一支 pwsh(繼承本行程的 VIA_* 與同意閘)
        $fa = @("-NoProfile", "-File", $vdfFetch.FullName)
        if ($Since) { $fa += @("-Since", $Since) }
        if (-not $Consent) { $fa += "-Dry" }
        Invoke-VIAOsStage 5 "VDF 台股清單 + 主動式台股 ETF 全清單 → 全部步擷取" $vdfFetch.Name { & $pwshExe @fa }
    } else {
        $stages.Add([ordered]@{ n = 5; name = "VDF 清單 + 擷取"; by = "Invoke-VIA-VdfFetch"; lamp = "YELLOW"; rc = 3; sec = 0; note = "Invoke-VIA-VdfFetch 尾版不在" })
    }
    Invoke-VIAOsStage 6 "主動 ETF NAV · AUM · 單位數 · 淨流入 / 流出" "VDF_ENG094_ActiveETFActivity fetch" { Invoke-VIAPython -Family 'vdf' -TimeoutSec 1800 $C run --family vdf VDF_ENG094_ActiveETFActivity fetch @ap } -Net
    Invoke-VIAOsStage 7 "主動 ETF 持股 / 產業 breakdown" "VDF_ENG094_ActiveETFActivity breakdown" { Invoke-VIAPython -Family 'vdf' -TimeoutSec 1800 $C run --family vdf VDF_ENG094_ActiveETFActivity breakdown @ap }
    if ($vdfMgr) { Invoke-VIAOsStage 8 "VDF 管理器 status" $vdfMgr.Name { Invoke-VIAPython -Family 'vdf' -TimeoutSec 900 $vdfMgr.FullName status } }
    else { $stages.Add([ordered]@{ n = 8; name = "VDF 管理器 status"; by = "VDF_SystemManager"; lamp = "YELLOW"; rc = 3; sec = 0; note = "尾版不在" }) }
    if ($vrnMgr) { Invoke-VIAOsStage 9 "VRN 管理器 status" $vrnMgr.Name { Invoke-VIAPython -Family 'vrn' -TimeoutSec 900 $vrnMgr.FullName status } }
    else { $stages.Add([ordered]@{ n = 9; name = "VRN 管理器 status"; by = "VRN_SystemManager"; lamp = "YELLOW"; rc = 3; sec = 0; note = "尾版不在" }) }
    Invoke-VIAOsStage 10 "輸出表頭全面檢查 + DataFrame 固定" "CGC_MDL249_DataFrameLock all" { Invoke-VIAPython -Family 'core' -TimeoutSec 1800 $C run --family core CGC_MDL249_DataFrameLock all @ap }
    Invoke-VIAOsStage 11 "PS 檢查(加速器橋 · 自壓頁)" "CGC_MDL277_AiOps pslint" { Invoke-VIAPython -Family 'core' -TimeoutSec 900 $C run --family core CGC_MDL277_AiOps pslint }
    Invoke-VIAOsStage 12 "撞號(對 origin/main 新增)" "CGC_MDL277_AiOps collide" { Invoke-VIAPython -Family 'core' -TimeoutSec 900 $C run --family core CGC_MDL277_AiOps collide --base origin/main }
    $fcArgs = @("run", "--family", "core", "CGC_MDL248_FullCheck", "run")
    if ($Grid) { $fcArgs += "--grid" }
    Invoke-VIAOsStage 13 "整合全景實測" "CGC_MDL248_FullCheck" { Invoke-VIAPython -Family 'core' -TimeoutSec $(if ($Grid) { 7200 } else { 3600 }) $C @fcArgs }
    Invoke-VIAOsStage 14 "VCGC 收尾 closeout" $console.Name { Invoke-VIAPython -Family 'core' -TimeoutSec 3600 $C closeout @ap }
    Invoke-VIAOsStage 15 "AI 狀態索引(後)" "CGC_MDL277_AiOps status" { Invoke-VIAPython -Family 'core' -TimeoutSec 900 $C run --family core CGC_MDL277_AiOps status }

    $env:VIA_NO_OPEN = $prev.OPEN   # 引擎跑完就換回呼叫端原值
    $lamps = @($stages | ForEach-Object { $_.lamp })
    $exitCode = if ($lamps -contains "RED") { 1 } elseif ($lamps -contains "YELLOW") { 2 } else { 0 }
    $outDir = Join-Path $VIA "VIA_Reports\aiops"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $stJson = Join-Path $outDir "ONESHOT_STAGES_latest.json"
    [IO.File]::WriteAllText($stJson, ($stages | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    $rows = @($stages | ForEach-Object { [pscustomobject]@{ id = "" + $_.n; title = $_.name; state = $_.lamp; sec = "" + $_.sec; note = ("" + $_.note) } })
    $shown = $false
    if (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue) {
        try { Write-CeleritasMatrixSummary -Rows $rows -Title ("VIA 收尾一鍵 · 15 段總覽 · 結束碼 " + $exitCode); $shown = $true } catch { $shown = $false }
    }
    if (-not $shown) {
        Write-Host ("  ━━ 15 段總覽 · 結束碼 " + $exitCode + " ━━") -ForegroundColor Cyan
        foreach ($r in $rows) { Write-Host ("  " + $r.id.PadLeft(2) + " " + $r.state.PadRight(7) + " " + $r.sec.PadLeft(7) + "s  " + $r.title) }
    }
    $null = Invoke-VIAPython -Family 'core' -TimeoutSec 300 $C run --family core CGC_MDL277_AiOps report $stJson --title "VIA 收尾一鍵 v0100" 2>&1
    $page = Join-Path $outDir "AIOPS_RUN_latest.html"
    Write-Host ("  [計時] 全程 " + [Math]::Round($total.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $exitCode + "(0 綠 · 2 黃 · 1 紅)") -ForegroundColor Cyan
    Write-Host ("  [總報告] " + $page) -ForegroundColor Cyan
    if (-not $NoOpen) { [void](Open-VIAOwnPage -Page $page -CallerNoOpen $prev.OPEN) }
} finally {
    $env:VIA_FROM_VCGC = $prev.FROM
    $env:VIA_VCGC_PUSH = $prev.PUSH
    $env:VIA_NO_OPEN = $prev.OPEN
    $env:VIA_NET_CONSENT = $prev.NET
    $env:VIA_SCRAPE_CONSENT = $prev.SCRAPE
    if ($VIAOsCelOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原(只還原本支自己套上的)
    Set-Location -LiteralPath $StartDir
}
exit $exitCode
