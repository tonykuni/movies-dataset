# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0276.ps1 — 2026-10-12:+activate_vdf(別名 activate-vdf · 啟動VDF全部)= VDF 前後端一鍵,從 HTML U/I 操作
#   操作員令(2026-10-12)「設立一個指令啟動VDF 短指令activate_vdf 啟動前後端系統介面 從html u/i操作」= L70 這一次的許可:只加這一件;
#   v0275 以前一字不動(本檔點源 v0275 往回接)。L113 裁定:被點源的函式庫豁免骨架,仍帶兩章(L106)。同名 .cmd 梭 activate_vdf.cmd(cmd 殼直打)。
#   activate_vdf [-SkipCheck] [-Repair] [-Apply] [-NoAsk] [-NoOpen] [-Dry]
#                [--groups ALL|A,B] [--jobs auto|1-5] [--mode live|fixture|block] [--skip a,b]
#                [--home <資料庫夾>] [--start 大類=YYYY-MM-DD] [--add 族群=值] [--remove 族群=值] [--import 頁上匯出.json]
#     ① 母系統監控(VCGC CGC_MDL265:環境 · 加速器 / 網路工具覆蓋 · 衝突提醒;只提醒不擋;-SkipCheck 略過 · -Repair 修)
#     ② 啟動前改:下載夾的 VIA_UI_Input.json(操作頁「匯出輸入」)→ CGC_MDL261 import(-Apply 直接寫,否則問 Y);
#        文字改動 --start / --add / --remove / --import → VDF_SystemManager activate(沒 -Apply = 乾跑只列計畫;帳本只增)
#     ③ 前後端一鍵:VDF_SystemManager all = 健康 → 啟動就緒 → 問參數頁(前端:ENG093 頁跳出 → 頁上按啟動 → 11 步擷取 → 狀況頁)
#        → 族群並行擷取(後端;雙閘沒開回 GATED 黃)→ 輸入清單 → USER-TEST → 族群頁 → 主頁 → 跳出族群頁(-NoOpen 不跳)
#     ④ 操作頁:CGC_MDL261 build → 跳出 VIA_Reports\ui_engine\VIA_UI_Engine_latest.html;收尾印四步 rc 與 ONE_LAUNCH_latest.json
#     網路雙閘永不代設:$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'(操作員的手)。VDF 歸 VDF System Manager 控管,本令只串門。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0275.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:activate_vdf {
    # 不加引號的逗號串在 PS 是陣列:攤平回逗號字串(L112 三檢)
    $a = @($args | ForEach-Object { if ($_ -is [array]) { ($_ | ForEach-Object { "$_" }) -join ',' } else { "$_" } })
    $repair = $a -contains '-Repair'; $skip = $a -contains '-SkipCheck'; $applyAll = $a -contains '-Apply'
    $noAsk = $a -contains '-NoAsk'; $dry = $a -contains '-Dry'
    $noOpen = ($a -contains '-NoOpen') -or [bool]$env:VIA_NO_OPEN
    $rest = @($a | Where-Object { $_ -notin @('-Repair', '-SkipCheck', '-Apply', '-NoAsk', '-NoOpen', '-Dry') })
    $interactive = [Environment]::UserInteractive -and -not [Console]::IsInputRedirected
    $run = { param([object[]]$R) if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped { via-vcgc run @R } } else { via-vcgc run @R } }
    $rcs = [ordered]@{}

    # 旗標分三路:改動旗標 → activate · all 旗標 → all · --home → activate / 操作頁(all 不吃 --home,資料庫位置照 VDF 自己的預設)
    $editKeys = @('--start', '--add', '--remove', '--import'); $allKeys = @('--groups', '--jobs', '--mode', '--skip')
    $edits = @(); $allArgs = @(); $home2 = $null
    for ($i = 0; $i -lt $rest.Count; $i++) {
        $k = $rest[$i]
        if (($k -in $editKeys) -and ($i + 1 -lt $rest.Count)) { $edits += @($k, $rest[$i + 1]); $i++ }
        elseif (($k -in $allKeys) -and ($i + 1 -lt $rest.Count)) { $allArgs += @($k, $rest[$i + 1]); $i++ }
        elseif (($k -eq '--home') -and ($i + 1 -lt $rest.Count)) { $home2 = $rest[$i + 1]; $i++ }
        else { $allArgs += @($k) }   # 其餘原樣交給 all(不認識的由它照實拒)
    }
    if (-not $home2 -and (Get-Command Get-VIAUiDbRoot -ErrorAction SilentlyContinue)) { try { $home2 = Get-VIAUiDbRoot } catch { $home2 = $null } }

    if (-not $skip) {
        Write-Host "  ===== [activate_vdf] ① 母系統監控(VCGC:環境 · 加速器 / 網路工具覆蓋 · 衝突提醒;只提醒不擋)=====" -ForegroundColor Cyan
        & $run (@('CGC_MDL265_VdfVrnReadiness') + $(if ($repair) { @('--repair') } else { @() }))
        $rcs['monitor'] = $global:LASTEXITCODE
    }

    $pending = $null
    if (-not $edits -and (Get-Command Get-VIAUiInputPending -ErrorAction SilentlyContinue)) { $pending = Get-VIAUiInputPending }
    if ($pending) {
        Write-Host ("  ===== [activate_vdf] ② 頁上的改動:" + $pending.Name + "(" + $pending.LastWriteTime.ToString('yyyy-MM-dd HH:mm') + ")=====") -ForegroundColor Cyan
        $ok = $applyAll
        if (-not $ok -and $interactive) { $ans = Read-Host "  套用頁上的改動(位置 · 範本 · 起始日 · 成員)?[Y/n]"; $ok = ("" + $ans).Trim() -in @('', 'y', 'Y', 'yes') }
        # 頁(CGC_MDL261)匯出的是 {locations · 範本 · vdf:{categories · members}};它自己的 import 拆開:位置 / 範本寫操作台參數,vdf 段交 VDF 自己的 ui-import 寫帳本
        $imp = @('CGC_MDL261_UIEngine', 'import', $pending.FullName) + $(if ($ok) { @('--apply') } else { @() })
        & $run $imp
        $rcs['page_edit'] = $global:LASTEXITCODE
        if ($ok -and ($global:LASTEXITCODE -in @(0, 2)) -and (Get-Command Set-VIAUiInputApplied -ErrorAction SilentlyContinue)) { Set-VIAUiInputApplied $pending }
        if (-not $ok) { Write-Host "  [頁上改動] 只列計畫(要寫:加 -Apply 再跑一次)" -ForegroundColor Yellow }
    } elseif ($edits) {
        Write-Host ("  ===== [activate_vdf] ② 文字改動 → VDF_SystemManager activate(" + $(if ($applyAll) { '寫入帳本,只增' } else { '乾跑只列計畫;加 -Apply 才寫' }) + ")=====") -ForegroundColor Cyan
        $va = @('--family', 'vdf', 'VDF_SystemManager', 'activate') + $edits + @('--no-open') + $(if ($applyAll) { @('--apply') } else { @() }) + $(if ($home2) { @('--home', $home2) } else { @() })
        & $run $va
        $rcs['edit'] = $global:LASTEXITCODE
    }

    Write-Host "  ===== [activate_vdf] ③ VDF 前後端一鍵(VDF System Manager all:健康 → 啟動就緒 → 問參數頁 → 族群並行 → 清單 → USER-TEST → 族群頁 → 主頁)=====" -ForegroundColor Cyan
    if (-not $dry -and -not ($env:VIA_NET_CONSENT -eq 'YES' -and $env:VIA_SCRAPE_CONSENT -and $env:VIA_SCRAPE_CONSENT -ne 'OFF')) {
        Write-Host "  [雙閘] 本視窗雙閘沒開 → 擷取步回 GATED(黃)、零出網。要抓:`$env:VIA_NET_CONSENT='YES'; `$env:VIA_SCRAPE_CONSENT='YES'(本令永不代設)" -ForegroundColor Yellow
    }
    $va = @('--family', 'vdf', 'VDF_SystemManager', 'all') + $allArgs
    if ($noAsk) { $va += @('--no-ask') }
    if ($dry) { $va += @('--dry') }
    if ($noOpen) { $va += @('--no-open') }
    & $run $va
    $rcs['all'] = $global:LASTEXITCODE
    $global:VIAActivateVdfAllRc = $global:LASTEXITCODE

    Write-Host "  ===== [activate_vdf] ④ 操作頁(CGC_MDL261 build)+ 跳出 =====" -ForegroundColor Cyan
    $op = @('CGC_MDL261_UIEngine', 'build') + $(if ($home2) { @('--home', $home2) } else { @() })
    & $run $op
    $rcs['operator_page'] = $global:LASTEXITCODE

    $vroot = if ($global:VIARegisterPath) { Split-Path -Parent $global:VIARegisterPath } else { $PSScriptRoot }
    $page = Join-Path $vroot "VIA_Reports\ui_engine\VIA_UI_Engine_latest.html"
    $groups = Join-Path $vroot "supportive modules\ui_support\VIA_UI_VDFFetchGroups_v0100.html"
    $hub = Join-Path $vroot "VIA_Reports\vdf\VDF_UI_latest.html"
    $one = Join-Path $vroot "VIA_Reports\vdf\ONE_LAUNCH_latest.json"
    $worst = 0; foreach ($v in $rcs.Values) { if ($null -ne $v -and [int]$v -gt $worst) { $worst = [int]$v } }
    $lamp = if ($worst -eq 0) { 'GREEN' } elseif ($worst -in @(2, 4)) { 'YELLOW' } else { 'RED' }
    $line = ($rcs.GetEnumerator() | ForEach-Object { $_.Key + ' rc ' + $_.Value }) -join ' · '
    Write-Host ("  [activate_vdf] " + $lamp + " · " + $line + " · 報告 " + $one) -ForegroundColor $(if ($lamp -eq 'GREEN') { 'Green' } elseif ($lamp -eq 'YELLOW') { 'Yellow' } else { 'Red' })
    Write-Host ("  [頁] 族群頁 " + $groups + $(if (Test-Path -LiteralPath $groups) { '' } else { '(沒產出)' })) -ForegroundColor Gray
    Write-Host ("  [頁] 主頁   " + $hub + $(if (Test-Path -LiteralPath $hub) { '' } else { '(沒產出 / 位置另設)' })) -ForegroundColor Gray
    if (-not (Test-Path -LiteralPath $page)) { Write-Host "  [操作頁] 沒產出(看上面 ④ 的訊息)" -ForegroundColor Red; return }
    if ($noOpen) { Write-Host ("  [操作頁] " + $page + "(-NoOpen / VIA_NO_OPEN 不跳;族群頁同)") -ForegroundColor Gray; return }
    try { Start-Process -FilePath $page; Write-Host ("  [操作頁] 已跳出 " + $page + " · 頁上改完按「匯出輸入」→ 再打 activate_vdf -Apply 套用後重啟") -ForegroundColor Green }
    catch { Write-Host ("  [操作頁] 開不了:" + $_.Exception.Message + " · 手動開 " + $page) -ForegroundColor Yellow }
    Write-Host "  [無資料族群] 頁上「總覽 · 無資料 · 補擷取路線」有清單 → via-vdf-refill 看計畫;本視窗開雙閘後 via-vdf-refill -Apply 補抓" -ForegroundColor Gray
}
Set-Alias -Name activate-vdf -Value activate_vdf -Scope Global -Force
Set-Alias -Name 啟動VDF全部 -Value activate_vdf -Scope Global -Force
