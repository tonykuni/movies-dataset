# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0269.ps1 — 側線 2026-10-04:+via-ui(別名 操作台)· +via-ui-run(別名 照選擷取)· +via-ui-pick(別名 選位置)·
#   +via-uieng(別名 UI引擎)· +via-duck(別名 資料庫)· +via-groups(別名 族群)· +via-groups-ui(別名 族群頁)·
#   +via-startdate(別名 起始日)· +via-monitor(別名 族群監控)· +via-uihelp(別名 操作台短令)。
#   操作員令「以都用短指令組合在一起 · 所有 PS PY 依規定安裝加速器及模組 · VDF 加網路工具」(VCGC-REQ155)= L70 這一次的許可:只加這十件;v0268 以前一字不動。
#   via-ui [-Pick] [-NoImport] [-Template X] [-Set a.b=v] [-Install] [-NoOpen]
#     = Start-VIA-UIEngine 尾版:RunGate / LKGC 環境檢查 → 自動匯入下載夾 VIA_UI_Input.json → 產頁(CGC_MDL261 尾版)→ 自動開(file://,不走 server)
#   via-ui-run [-Mode live|block|fixture]   = via-ui -Run:照頁上勾的族群 → VDF_MDL012_FetchGroups run(網路工具橋 + 加速器)→ monitor → 重產頁
#   via-ui-pick                              = via-ui -Pick:Windows 資料夾對話框選系統 / 資料庫兩個位置
#   via-uieng [build|duck|templates|config|import FILE --apply|--selftest]   = via-vcgc run CGC_MDL261_UIEngine(沒給子令 = build)
#   via-duck                                 = via-uieng duck(DuckDB 顯式:庫 · 表 · 視圖 · LOCKED;沒給 --home = 操作台選的資料庫位置)
#   via-groups [groups|members|add|remove|asof|run|monitor|query|optimize|start|ui-import …]   = via-vcgc run --family vdf VDF_MDL012_FetchGroups(沒給子令 = groups)
#   via-groups-ui [-Template X] [-Watch 15]   = Invoke-VDF-FetchGroupsUI 尾版(族群頁 · 任何範本)
#   via-startdate [--category X --set D|default --apply]   = via-groups start(起始日只按大類改;單群拒絕)
#   via-monitor                              = via-groups monitor(DuckDB 目錄燈 · 截到 as-of;沒給 --home 同上)
#   via-uihelp                               = 本冊十件一張表
#   每件都包 Invoke-VIACeleritasScoped(PS 25 加速器;只動本行程);PY 端尾版自帶 SuperAccel 橋,VDF 端自帶網路工具橋(via_net_unified → AegisNexus)。
#   觸網(-Mode live)要你在自己的視窗開 VIA_NET_CONSENT=YES(AI 永不代設;沒開 = 引擎照實 DENY)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0268.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:Invoke-VIAScopedLauncher {
    param([string]$Pattern, [string]$Tag, [object[]]$Rest)
    $vroot = Split-Path -Parent $global:VIARegisterPath
    $ps = Get-ChildItem -LiteralPath $vroot -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if (-not $ps) { Write-Host ("  [" + $Tag + "] 找不到 " + $Pattern + "(先 git pull)") -ForegroundColor Red; $global:LASTEXITCODE = 3; return }
    $a = @($Rest)
    Write-Host ("  [" + $Tag + "] " + $ps.Name + " " + ($a -join ' ')) -ForegroundColor Cyan
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) {
        Invoke-VIACeleritasScoped { & $ps.FullName @a }
    } else {
        & $ps.FullName @a
    }
}
function global:Invoke-VIAScopedVcgc {
    param([string]$Tag, [object[]]$Rest)
    $a = @($Rest)
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) {
        Invoke-VIACeleritasScoped { via-vcgc run @a }
    } else {
        via-vcgc run @a
    }
}

function global:Get-VIAUiDbRoot {
    # 資料庫位置:操作台存的 ui_config.json locations.db_root → $env:VIA_VDF_FETCH_HOME → <VIA>\via_database\vdf_fetch(Start-VIA-UIEngine 同一個預設);都不在 = 不給 --home(引擎照實報 0 庫)
    $vroot = Split-Path -Parent $global:VIARegisterPath
    $cfg = Join-Path $vroot "VIA_Reports\ui_engine\ui_config.json"
    $c = @()
    if (Test-Path -LiteralPath $cfg) { try { $j = Get-Content -LiteralPath $cfg -Raw -Encoding utf8 | ConvertFrom-Json; if ($j.locations.db_root) { $c += "" + $j.locations.db_root } } catch { } }
    if ($env:VIA_VDF_FETCH_HOME) { $c += $env:VIA_VDF_FETCH_HOME }
    $c += (Join-Path $vroot "via_database\vdf_fetch")
    foreach ($p in $c) { if ($p -and (Test-Path -LiteralPath $p)) { return $p } }
    return $null
}
function global:Add-VIAUiHome([object[]]$Rest) {
    $a = @($Rest)
    if ($a -notcontains '--home') { $h = Get-VIAUiDbRoot; if ($h) { $a += @('--home', $h) } }
    return ,$a
}

# ---- U/I 引擎(VCGC):Start-VIA-UIEngine-v*.ps1 · CGC_MDL261_UIEngine ----
function global:via-ui { Invoke-VIAScopedLauncher "Start-VIA-UIEngine-v*.ps1" "via-ui" $args }
function global:via-ui-run { Invoke-VIAScopedLauncher "Start-VIA-UIEngine-v*.ps1" "via-ui-run" (@('-Run') + @($args)) }
function global:via-ui-pick { Invoke-VIAScopedLauncher "Start-VIA-UIEngine-v*.ps1" "via-ui-pick" (@('-Pick') + @($args)) }
function global:via-uieng {
    $a = @($args); if ($a.Count -eq 0) { $a = @('build') }
    Invoke-VIAScopedVcgc "via-uieng" (@('CGC_MDL261_UIEngine') + $a)
}
function global:via-duck { Invoke-VIAScopedVcgc "via-duck" (@('CGC_MDL261_UIEngine', 'duck') + (Add-VIAUiHome $args)) }

# ---- VDF 擷取大族群:VDF_MDL012_FetchGroups · Invoke-VDF-FetchGroupsUI-v*.ps1 ----
function global:via-groups {
    $a = @($args); if ($a.Count -eq 0) { $a = @('groups') }
    Invoke-VIAScopedVcgc "via-groups" (@('--family', 'vdf', 'VDF_MDL012_FetchGroups') + $a)
}
function global:via-groups-ui { Invoke-VIAScopedLauncher "Invoke-VDF-FetchGroupsUI-v*.ps1" "via-groups-ui" $args }
function global:via-startdate { Invoke-VIAScopedVcgc "via-startdate" (@('--family', 'vdf', 'VDF_MDL012_FetchGroups', 'start') + @($args)) }
function global:via-monitor { Invoke-VIAScopedVcgc "via-monitor" (@('--family', 'vdf', 'VDF_MDL012_FetchGroups', 'monitor') + (Add-VIAUiHome $args)) }

function global:via-uihelp {
    $rows = @(
        @('via-ui', '操作台', '環境檢查 → 匯入下載夾輸入 → 產頁 → 自動開(不走 server)'),
        @('via-ui-run', '照選擷取', '照頁上勾的族群擷取 → 監控 → 重產頁(-Mode live 要 VIA_NET_CONSENT)'),
        @('via-ui-pick', '選位置', '資料夾對話框選系統 / 資料庫位置'),
        @('via-uieng', 'UI引擎', 'CGC_MDL261 build / duck / templates / config / import'),
        @('via-duck', '資料庫', 'DuckDB 顯式:庫 · 表 · 視圖 · LOCKED'),
        @('via-groups', '族群', 'VDF 大族群:groups / members / add / remove / asof / run / optimize'),
        @('via-groups-ui', '族群頁', '族群頁 · -Template 任何範本'),
        @('via-startdate', '起始日', '起始日只按大類改:--category X --set D --apply'),
        @('via-monitor', '族群監控', 'DuckDB 目錄燈(截到 as-of)'),
        @('via-uihelp', '操作台短令', '這張表')
    )
    Write-Host "  [操作台短令] Register-VIA-Commands-v0269(PS 加速器包住 · PY 加速器 · VDF 網路工具)" -ForegroundColor Cyan
    foreach ($r in $rows) { Write-Host ("    {0,-14} {1,-8} {2}" -f $r[0], $r[1], $r[2]) }
}
Set-Alias -Name 操作台 -Value via-ui -Scope Global -Force
Set-Alias -Name 照選擷取 -Value via-ui-run -Scope Global -Force
Set-Alias -Name 選位置 -Value via-ui-pick -Scope Global -Force
Set-Alias -Name UI引擎 -Value via-uieng -Scope Global -Force
Set-Alias -Name 資料庫 -Value via-duck -Scope Global -Force
Set-Alias -Name 族群 -Value via-groups -Scope Global -Force
Set-Alias -Name 族群頁 -Value via-groups-ui -Scope Global -Force
Set-Alias -Name 起始日 -Value via-startdate -Scope Global -Force
Set-Alias -Name 族群監控 -Value via-monitor -Scope Global -Force
Set-Alias -Name 操作台短令 -Value via-uihelp -Scope Global -Force
