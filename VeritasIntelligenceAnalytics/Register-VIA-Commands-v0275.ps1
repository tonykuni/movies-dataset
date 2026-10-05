# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0275.ps1 — 2026-10-05:+via-vdf-refill(別名 via_vdf_refill · 補資料)· via-activate-vdf 改動提示防貼指令
#   操作員令「FOR THOSE NO DATA USE FRED KEY AND OTHER GOVERNMENT UNIT AND AKSHARE TO FETCH」= L70 這一次的許可:只加這兩件;v0274 以前一字不動。
#   L113 裁定:被點源的函式庫豁免骨架,仍帶兩章(L106)。分工照 L111 ruling_20261005b:補擷取歸 VDF(VDF System Manager refill → MDL012 refill)。
#   via-vdf-refill [-Apply] [--home <資料庫夾>] [--groups X,Y] [--as-of D] [--timeout S]
#     沒給 -Apply = 只列計畫:哪些族群無資料 · 每族群的分層(FRED 要 FRED_API_KEY · 政府單位 TWSE / TPEx / MOPS / 財政部 · AkShare)
#     -Apply = 真跑;網路要本視窗先開雙閘(本令永不代設):$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'
#     FRED 鑰:本視窗 $env:FRED_API_KEY 或輸出根 .fred_api_key(引擎只查有沒有,不印)
#   via-activate-vdf:改動提示若收到 PowerShell 指令(git · . .\ · via- · Remove-Item …)就停止收改動、照目前的改動啟動;
#     結尾提示無資料族群怎麼補。其餘一圈(① 監控 · ② 頁上改動 · ③ VDF 啟動 · ④ 操作頁)照 v0274。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0274.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
# 改動提示收到這些開頭 = 使用者貼的是指令,不是改動
$global:VIACommandLike = '^(git\s|\.\s|\.\\|&\s|via[-_]|Remove-Item|Set-|Get-|cd\s|python|pwsh|\$env:)'

# ConvertTo-VIAVdfEdit:照 v0273 原樣帶到尾版(互動文字改動用;CGC_MDL265 自測從尾版取函式)
function global:ConvertTo-VIAVdfEdit {
    # 互動輸入一行 → VDF activate 旗標:大類=日期 → --start · +族群=值 → --add · -族群=值 → --remove;其他 = $null(照實拒)
    param([string]$Line)
    $t = "$Line".Trim()
    if ($t -match '^\+\s*([A-Za-z0-9_]+)\s*=\s*(.+)$') { return @('--add', ($Matches[1] + '=' + $Matches[2].Trim())) }
    if ($t -match '^-\s*([A-Za-z0-9_]+)\s*=\s*(.+)$') { return @('--remove', ($Matches[1] + '=' + $Matches[2].Trim())) }
    if ($t -match '^([A-Za-z0-9_]+)\s*=\s*(\d{4}-\d{2}-\d{2}|default)$') { return @('--start', ($Matches[1] + '=' + $Matches[2])) }
    return $null
}

function global:via-activate-vdf {
    # 不加引號的逗號串在 PS 是陣列:攤平回逗號字串(L112 三檢)
    $a = @($args | ForEach-Object { if ($_ -is [array]) { ($_ | ForEach-Object { "$_" }) -join ',' } else { "$_" } })
    $repair = $a -contains '-Repair'; $skip = $a -contains '-SkipCheck'; $noPrompt = $a -contains '-NoPrompt'
    $applyAll = $a -contains '-Apply'; $noOpen = $a -contains '-NoOpen'
    $vdf = @($a | Where-Object { $_ -notin @('-Repair', '-SkipCheck', '-NoPrompt', '-NoOpen', '-Apply') })
    if ($noOpen) { $vdf += @('--no-open') }
    $interactive = (-not $noPrompt) -and [Environment]::UserInteractive -and -not [Console]::IsInputRedirected
    $run = { param([object[]]$Rest) if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped { via-vcgc run @Rest } } else { via-vcgc run @Rest } }

    if (-not $skip) {
        Write-Host "  ===== [via-activate-vdf] ① 母系統監控(VCGC:環境 · 加速器 / 網路工具覆蓋 · 衝突提醒;只提醒不擋)=====" -ForegroundColor Cyan
        & $run (@('CGC_MDL265_VdfVrnReadiness') + $(if ($repair) { @('--repair') } else { @() }))
    }

    $edits = @('--start', '--add', '--remove', '--import') | Where-Object { $vdf -contains $_ }
    $pending = if (-not $edits) { Get-VIAUiInputPending } else { $null }
    $pageApplied = $false
    if ($pending) {
        Write-Host ("  ===== [via-activate-vdf] ② 頁上的改動:" + $pending.Name + "(" + $pending.LastWriteTime.ToString('yyyy-MM-dd HH:mm') + ")=====") -ForegroundColor Cyan
        $ok = $applyAll
        if (-not $ok -and $interactive) { $ans = Read-Host "  套用頁上的改動(位置 · 範本 · 起始日 · 成員)?[Y/n]"; $ok = ("" + $ans).Trim() -in @('', 'y', 'Y', 'yes') }
        # 頁(CGC_MDL261)匯出的是 {locations · 範本 · vdf:{categories · members}};它自己的 import 拆開:位置 / 範本寫操作台參數,vdf 段轉 VDF 原生格式交 VDF 自己的 ui-import 寫帳本
        $imp = @('CGC_MDL261_UIEngine', 'import', $pending.FullName) + $(if ($ok) { @('--apply') } else { @() })
        & $run $imp
        if ($ok -and $global:LASTEXITCODE -in @(0, 2)) { $pageApplied = $true }
        if (-not $ok) { Write-Host "  [頁上改動] 只列計畫(要寫:再跑一次並回 Y,或加 -Apply)" -ForegroundColor Yellow }
    } elseif (-not $edits -and $interactive) {
        Write-Host "  [啟動前改] 沒有新的頁上輸入。文字改動:每行一筆 · TW_MARKET=2022-01-01 · +TW_FIN=2330 · -TW_FIN=2330 · Enter 空行 = 照現況啟動" -ForegroundColor Yellow
        $picked = @()
        while ($true) {
            $line = Read-Host "  改動"
            if (-not "$line".Trim()) { break }
            if ("$line".Trim() -match $global:VIACommandLike) {
                Write-Host "    [停] 這行是 PowerShell 指令,不是改動 → 結束改動輸入、照目前的改動啟動(指令等啟動完再打)" -ForegroundColor Yellow
                break
            }
            $f = ConvertTo-VIAVdfEdit $line
            if ($f) { $picked += $f } else { Write-Host ("    [拒絕] 看不懂「" + $line + "」(格式:大類=YYYY-MM-DD · +族群=值 · -族群=值)") -ForegroundColor Red }
        }
        if ($picked) { $vdf += $picked + @('--apply') }
    }
    if ((Get-Command Add-VIAUiHome -ErrorAction SilentlyContinue)) { $vdf = Add-VIAUiHome $vdf }
    if ($vdf -notcontains '--no-open') { $vdf += @('--no-open') }            # VDF 頁照產;跳出的是操作頁(④),不開兩個分頁
    $home2 = $null; $i = [array]::IndexOf($vdf, '--home'); if ($i -ge 0 -and $i + 1 -lt $vdf.Count) { $home2 = $vdf[$i + 1] }
    Write-Host ("  ===== [via-activate-vdf] ③ VDF 啟動(VDF System Manager 控管)+ ④ 操作頁 =====") -ForegroundColor Cyan
    $op = @('CGC_MDL261_UIEngine', 'build') + $(if ($home2) { @('--home', $home2) } else { @() })
    $both = { param([object[]]$V, [object[]]$O) $va = @('--family', 'vdf', 'VDF_SystemManager', 'activate') + $V; via-vcgc run @va; $global:VIAActivateVdfRc = $global:LASTEXITCODE; via-vcgc run @O }   # 先組變數再 splat:@(@(...)) 會整串當一個參數
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped { & $both $vdf $op } } else { & $both $vdf $op }
    if ($pending -and $pageApplied) { Set-VIAUiInputApplied $pending }

    if (-not $global:VIARegisterPath) { return }
    $vroot = Split-Path -Parent $global:VIARegisterPath
    $page = Join-Path $vroot "VIA_Reports\ui_engine\VIA_UI_Engine_latest.html"
    if (-not (Test-Path -LiteralPath $page)) { Write-Host "  [操作頁] 沒產出(看上面 ④ 的訊息)" -ForegroundColor Red; return }
    if ($noOpen) { Write-Host ("  [操作頁] " + $page + "(-NoOpen 不跳)") -ForegroundColor Gray; return }
    if ($env:VIA_NO_OPEN) { Write-Host ("  [操作頁] 本視窗有 VIA_NO_OPEN 抑制跳出 → Remove-Item Env:VIA_NO_OPEN 後再跑,或直接開:" + $page) -ForegroundColor Yellow; return }
    try { Start-Process -FilePath $page; Write-Host ("  [操作頁] 已跳出 " + $page + " · 頁上改完按「匯出輸入」→ 再打 via_activate_vdf 套用") -ForegroundColor Green }
    catch { Write-Host ("  [操作頁] 開不了:" + $_.Exception.Message + " · 手動開 " + $page) -ForegroundColor Yellow }
    Write-Host "  [無資料族群] 頁上「總覽 · 無資料 · 補擷取路線」有清單 → via-vdf-refill 看計畫;本視窗開雙閘後 via-vdf-refill -Apply 補抓(FRED → 政府單位 → AkShare)" -ForegroundColor Gray
}
Set-Alias -Name via_activate_vdf -Value via-activate-vdf -Scope Global -Force
Set-Alias -Name 啟動VDF -Value via-activate-vdf -Scope Global -Force

function global:via-vdf-refill {
    # 不加引號的逗號串在 PS 是陣列:攤平回逗號字串(L112 三檢)
    $a = @($args | ForEach-Object { if ($_ -is [array]) { ($_ | ForEach-Object { "$_" }) -join ',' } else { "$_" } })
    $rest = @($a | Where-Object { $_ -ne '-Apply' })
    if ($a -contains '-Apply') { $rest += @('--apply') }
    if ((Get-Command Add-VIAUiHome -ErrorAction SilentlyContinue)) { $rest = Add-VIAUiHome $rest }
    if (($rest -contains '--apply') -and -not ($env:VIA_NET_CONSENT -eq 'YES' -and $env:VIA_SCRAPE_CONSENT -and $env:VIA_SCRAPE_CONSENT -ne 'OFF')) {
        Write-Host "  [via-vdf-refill] 本視窗雙閘沒開 → VDF 會回 GATED、零出網。要抓:`$env:VIA_NET_CONSENT='YES'; `$env:VIA_SCRAPE_CONSENT='YES'(本令永不代設)" -ForegroundColor Yellow
    }
    $va = @('--family', 'vdf', 'VDF_SystemManager', 'refill') + $rest
    Write-Host ("  ===== [via-vdf-refill] VDF 無資料族群補擷取(VDF System Manager 控管)" + ($rest -join ' ') + " =====") -ForegroundColor Cyan
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped { via-vcgc run @va } } else { via-vcgc run @va }
}
Set-Alias -Name via_vdf_refill -Value via-vdf-refill -Scope Global -Force
Set-Alias -Name 補資料 -Value via-vdf-refill -Scope Global -Force
