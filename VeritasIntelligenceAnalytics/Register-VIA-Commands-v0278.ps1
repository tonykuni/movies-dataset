# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0278.ps1 — 2026-10-13:activate_vdf 一鍵的 python 天花板放寬(蓋過 v0277 的同名函式;v0277 以前一字不動)
#   操作員准(2026-10-13)「准 Register v0278 出版」(L70 逐件准;VDF-REQ021)。工作站 2026-10-13 一鍵實錄:
#   清單先行 OK(tw_list 121.5s · etf_list 46.3s)之後,整程被 Invoke-VIAPython 預設天花板 1800 秒停掉 → all rc 124 · RED;步 7–13 沒跑完。
#   根因:activate_vdf → via-vcgc run … VDF_SystemManager all 沒帶 -TimeoutSec;問參數頁等待(≤ 15 分)+ ① 清單補齊 ~700s + ② 道並行都在同一支 python 子樹。
#   本版只動一處:② all 呼叫前比照 via-in(v0263)—— $env:VIA_PY_TIMEOUT_SEC 沒設 / 不是數字 / 小於 14400 就放寬到 14400 秒,跑完還原;
#   你自己設 0(不設限)或更大就照你的。env 由 pwsh 子行程(問參數頁 → Invoke-VIA-VdfFetch)繼承,內層那次 Invoke-VIAPython 同樣受惠。
#   其餘(① 啟動前改 · 尾版門 · 雙閘提醒 · ③ 跳出 · -Check / -NoAsk / -Dry / -NoOpen)與 v0277 一字不差。載入時印一行旗標。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0277.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:activate_vdf {
    # 不加引號的逗號串在 PS 是陣列:攤平回逗號字串(L112 三檢)
    $a = @($args | ForEach-Object { if ($_ -is [array]) { ($_ | ForEach-Object { "$_" }) -join ',' } else { "$_" } })
    $check = $a -contains '-Check'; $applyAll = $a -contains '-Apply'
    $noAsk = $a -contains '-NoAsk'; $dry = $a -contains '-Dry'; $noOpen = $a -contains '-NoOpen'
    $rest = @($a | Where-Object { $_ -notin @('-Check', '-Apply', '-NoAsk', '-NoOpen', '-Dry', '-SkipCheck', '-Repair') })
    $interactive = [Environment]::UserInteractive -and -not [Console]::IsInputRedirected
    $run = { param([object[]]$R) if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped { via-vcgc run @R } } else { via-vcgc run @R } }
    $rcs = [ordered]@{}
    $vroot = if ($global:VIARegisterPath) { Split-Path -Parent $global:VIARegisterPath } else { $PSScriptRoot }
    $groups = Join-Path $vroot "supportive modules\ui_support\VIA_UI_VDFFetchGroups_v0100.html"
    $hub = Join-Path $vroot "VIA_Reports\vdf\VDF_UI_latest.html"
    $one = Join-Path $vroot "VIA_Reports\vdf\ONE_LAUNCH_latest.json"

    # 旗標分路:改動旗標 → activate · all 旗標 → all · --home → activate(all 不吃 --home,資料庫位置照 VDF 自己的預設)
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
    $homeArgs = @(); if ($home2) { $homeArgs = @('--home', $home2) }

    Write-Host "  ===== [activate_vdf] VDF 獨立操作台一鍵(VDF System Manager 控管;VRN / VDF / VCGC 三台獨立,只共用顏色與版面)=====" -ForegroundColor Cyan
    if ($check) {
        Write-Host "  ===== [activate_vdf] -Check:VCGC 只讀監控(CGC_MDL265;只攤開不代修)=====" -ForegroundColor Cyan
        & $run @('CGC_MDL265_VdfVrnReadiness')
        $rcs['vcgc_check'] = $global:LASTEXITCODE
    }

    $pending = $null
    if (-not $edits -and (Get-Command Get-VIAUiInputPending -ErrorAction SilentlyContinue)) { $pending = Get-VIAUiInputPending }
    if ($pending) {
        Write-Host ("  ===== [activate_vdf] ① 頁上的改動 → VDF_SystemManager activate --import:" + $pending.Name + "(" + $pending.LastWriteTime.ToString('yyyy-MM-dd HH:mm') + ")=====") -ForegroundColor Cyan
        $ok = $applyAll
        if (-not $ok -and $interactive) { $ans = Read-Host "  寫進 VDF 成員帳本(只增)?[Y/n]"; $ok = ("" + $ans).Trim() -in @('', 'y', 'Y', 'yes') }
        $va = @('--family', 'vdf', 'VDF_SystemManager', 'activate', '--import', $pending.FullName, '--no-open') + $(if ($ok) { @('--apply') } else { @() }) + $homeArgs
        & $run $va
        $rcs['edit'] = $global:LASTEXITCODE
        if ($ok -and ($global:LASTEXITCODE -in @(0, 2)) -and (Get-Command Set-VIAUiInputApplied -ErrorAction SilentlyContinue)) { Set-VIAUiInputApplied $pending }
        if (-not $ok) { Write-Host "  [頁上改動] 只列計畫(要寫:加 -Apply 再跑一次);不是 VDF 頁的匯出會被 VDF 自己的 ui-import 照實拒" -ForegroundColor Yellow }
    } elseif ($edits) {
        Write-Host ("  ===== [activate_vdf] ① 文字改動 → VDF_SystemManager activate(" + $(if ($applyAll) { '寫入帳本,只增' } else { '乾跑只列計畫;加 -Apply 才寫' }) + ")=====") -ForegroundColor Cyan
        $va = @('--family', 'vdf', 'VDF_SystemManager', 'activate') + $edits + @('--no-open') + $(if ($applyAll) { @('--apply') } else { @() }) + $homeArgs
        & $run $va
        $rcs['edit'] = $global:LASTEXITCODE
    }

    Write-Host "  ===== [activate_vdf] ② VDF_SystemManager all(健康 → 啟動就緒 → 問參數頁 → 族群並行 → 清單 → USER-TEST → 族群頁 → 主頁)=====" -ForegroundColor Cyan
    $mgrDir = Join-Path $vroot "functional modules\VDF"
    $mgr = Get-ChildItem -LiteralPath $mgrDir -Filter "VDF_SystemManager_v*.py" -File -ErrorAction Ignore | Sort-Object Name | Select-Object -Last 1
    $mgrVer = 0; if ($mgr -and $mgr.BaseName -match '_v(\d{4})$') { $mgrVer = [int]$Matches[1] }
    if ($mgrVer -lt 155) {
        Write-Host ("  [尾版門] VDF_SystemManager 尾版 = " + $(if ($mgr) { $mgr.Name } else { '(沒有)' }) + " · all 動詞自 v0155 起 → 不起(分支 claude/kind-cannon-pti15g 沒併全:git merge --no-edit origin/claude/kind-cannon-pti15g;衝突走 via-medic)") -ForegroundColor Red
        $rcs['all'] = 3
    } else {
        if (-not $dry -and -not ($env:VIA_NET_CONSENT -eq 'YES' -and $env:VIA_SCRAPE_CONSENT -and $env:VIA_SCRAPE_CONSENT -ne 'OFF')) {
            Write-Host "  [雙閘] 本視窗雙閘沒開 → 擷取步回 GATED(黃)、零出網。要抓:`$env:VIA_NET_CONSENT='YES'; `$env:VIA_SCRAPE_CONSENT='YES'(本令永不代設)" -ForegroundColor Yellow
        }
        $va = @('--family', 'vdf', 'VDF_SystemManager', 'all') + $allArgs
        if ($noAsk) { $va += @('--no-ask') }
        if ($dry) { $va += @('--dry') }
        $va += @('--no-open')     # 跳出歸 ③ 一處(主頁 + 族群頁),不開兩次
        # v0278:一鍵全程(問參數頁等待 + ① 清單補齊 + ② 道並行)同在一支 python 子樹,Invoke-VIAPython 預設 1800 秒會整棵殺掉(工作站 2026-10-13 rc 124)
        #        → 比照 via-in(v0263):沒設 / 不是數字 / 小於 14400 就放寬到 14400 秒,跑完還原;設 0 = 不設限照你的;env 由 pwsh 子行程繼承
        $prevTimeout = $env:VIA_PY_TIMEOUT_SEC; $cap = 0
        $raise = (-not [int]::TryParse(("" + $prevTimeout), [ref]$cap)) -or ($cap -gt 0 -and $cap -lt 14400)
        if ($raise) {
            $env:VIA_PY_TIMEOUT_SEC = "14400"
            Write-Host "  [activate_vdf] 本次 python 天花板放寬到 14400 秒(一鍵全程常超過 1800 秒;跑完還原;`$env:VIA_PY_TIMEOUT_SEC=0 = 不設限)" -ForegroundColor DarkGray
        }
        try { & $run $va; $rcs['all'] = $global:LASTEXITCODE }
        finally { if ($raise) { $env:VIA_PY_TIMEOUT_SEC = $prevTimeout } }
    }
    $global:VIAActivateVdfAllRc = $rcs['all']

    $worst = 0; foreach ($v in $rcs.Values) { if ($null -ne $v -and [int]$v -gt $worst) { $worst = [int]$v } }
    $lamp = if ($worst -eq 0) { 'GREEN' } elseif ($worst -in @(2, 4)) { 'YELLOW' } else { 'RED' }
    $line = ($rcs.GetEnumerator() | ForEach-Object { $_.Key + ' rc ' + $_.Value }) -join ' · '
    Write-Host ("  [activate_vdf] " + $lamp + " · " + $line + " · 報告 " + $one) -ForegroundColor $(if ($lamp -eq 'GREEN') { 'Green' } elseif ($lamp -eq 'YELLOW') { 'Yellow' } else { 'Red' })
    Write-Host ("  [VDF 操作台] 主頁   " + $hub + $(if (Test-Path -LiteralPath $hub) { '' } else { '(沒產出 / 位置另設)' })) -ForegroundColor Gray
    Write-Host ("  [VDF 操作台] 族群頁 " + $groups + $(if (Test-Path -LiteralPath $groups) { '' } else { '(沒產出)' })) -ForegroundColor Gray
    if ($noOpen) { Write-Host "  [跳出] -NoOpen:不跳,路徑在上面" -ForegroundColor Gray; return }
    $opened = 0
    foreach ($p in @($hub, $groups)) {
        if (-not (Test-Path -LiteralPath $p)) { continue }
        try {
            if (Get-Command via-open -ErrorAction SilentlyContinue) { via-open $p } else { Start-Process -FilePath $p }
            $opened++
        } catch { Write-Host ("  [跳出] 開不了:" + $p + " · " + $_.Exception.Message) -ForegroundColor Yellow }
    }
    Write-Host ("  [跳出] VDF 操作台 " + $opened + " 頁(主頁 · 族群頁);頁上「匯出輸入」→ 再打 activate_vdf -Apply 套用後重啟") -ForegroundColor $(if ($opened) { 'Green' } else { 'Yellow' })
}
Set-Alias -Name activate-vdf -Value activate_vdf -Scope Global -Force
Set-Alias -Name 啟動VDF全部 -Value activate_vdf -Scope Global -Force
Write-Host "  [VIA] Register 尾版 v0278 · activate_vdf = VDF 獨立操作台一鍵(別名 activate-vdf · 啟動VDF全部)· 一鍵全程 python 天花板 14400 秒(跑完還原)· VRN / VDF / VCGC 三台獨立,只共用 typekit 顏色與版面" -ForegroundColor DarkCyan
