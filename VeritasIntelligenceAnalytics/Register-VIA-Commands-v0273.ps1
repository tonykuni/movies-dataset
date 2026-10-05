# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0273.ps1 — 2026-10-05:+via-activate-vdf(別名 via_activate_vdf · 啟動VDF)(VCGC-REQ170 · VDF-REQ018)
#   操作員令「via_activate_vdf … 原始指令用 py 寫並加入加速器 · 啟動 vcgc 對 vrn vdf 所有工具及環境檢查及修復 · 確認所有 py ps 都加速器 ·
#   vdf 都有加網路工具 · 啟動 vdf 讀取資料庫現況然後跳出 html u/i」;同日裁定「vcgc vdf vrn 為獨立系統 · vdf 啟動指令由 vdf manager 控管 ·
#   使用者啟動前有改各類型起始時間或要增減項目的權利」「權力下放子系統 · 母系統監控及衝突提醒全力 · 更改由我跟你定案」
#   = L70 這一次的許可:只加這一件;v0272 以前一字不動。L113 裁定:被點源的函式庫豁免骨架,仍帶兩章(L106)。
#   兩段,各歸各的系統(Python 本體 · 都在加速器 scope 內跑):
#     ① 母系統監控(VCGC):CGC_MDL265_VdfVrnReadiness —— VRN / VDF 家族境 · LKGC · PY / PS 加速器 · VDF 網路工具覆蓋 · 衝突提醒;
#        只提醒不擋(結果照實印);-Repair 才修(安裝要本視窗雙閘,本令永不代設);-SkipCheck 跳過
#     ② VDF 啟動(VDF System Manager 控管):VDF_SystemManager activate —— 現況 → 啟動前改 → 讀庫 → 跳出 U/I
#        啟動前改(你的權利):旗標 --start 大類=YYYY-MM-DD · --add 族群=值[,值] · --remove 族群=值 · --import 檔 [--apply];
#        沒給任何改動旗標、又是互動視窗 → 先問一次:每行一筆(TW_MARKET=2022-01-01 改起始日 · +TW_FIN=2330 加 · -TW_FIN=2330 減),
#        Enter 空行 = 照現況啟動;打了就當你確認 = 帶 --apply。-NoPrompt 不問。
#   via-activate-vdf [-Repair] [-SkipCheck] [-NoPrompt] [-NoOpen] [--home <資料庫夾>] [--start …] [--add …] [--remove …] [--import 檔] [--apply]
#   沒給 --home = 操作台選的資料庫位置(Get-VIAUiDbRoot)。也可 via activate-vdf(總門)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0272.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

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
    $vdf = @($a | Where-Object { $_ -notin @('-Repair', '-SkipCheck', '-NoPrompt', '-NoOpen') })
    if ($a -contains '-NoOpen') { $vdf += @('--no-open') }
    $run = { param([object[]]$Rest) if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped { via-vcgc run @Rest } } else { via-vcgc run @Rest } }

    if (-not $skip) {
        Write-Host "  ===== [via-activate-vdf] ① 母系統監控(VCGC:環境 · 加速器 / 網路工具覆蓋 · 衝突提醒;只提醒不擋)=====" -ForegroundColor Cyan
        & $run (@('CGC_MDL265_VdfVrnReadiness') + $(if ($repair) { @('--repair') } else { @() }))
        $global:VIAActivateVcgcRc = $global:LASTEXITCODE
    }

    $edits = @('--start', '--add', '--remove', '--import') | Where-Object { $vdf -contains $_ }
    if (-not $edits -and -not $noPrompt -and [Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
        Write-Host "  [啟動前改] 你的權利:每行一筆 · TW_MARKET=2022-01-01 改大類起始日 · +TW_FIN=2330 加項目 · -TW_FIN=2330 減項目 · Enter 空行 = 照現況啟動" -ForegroundColor Yellow
        $picked = @()
        while ($true) {
            $line = Read-Host "  改動"
            if (-not "$line".Trim()) { break }
            $f = ConvertTo-VIAVdfEdit $line
            if ($f) { $picked += $f } else { Write-Host ("    [拒絕] 看不懂「" + $line + "」(格式:大類=YYYY-MM-DD · +族群=值 · -族群=值)") -ForegroundColor Red }
        }
        if ($picked) { $vdf += $picked + @('--apply') }
    }
    if ((Get-Command Add-VIAUiHome -ErrorAction SilentlyContinue)) { $vdf = Add-VIAUiHome $vdf }
    Write-Host ("  ===== [via-activate-vdf] ② VDF 啟動(VDF System Manager 控管)activate " + ($vdf -join ' ') + " =====") -ForegroundColor Cyan
    & $run (@('--family', 'vdf', 'VDF_SystemManager', 'activate') + $vdf)
}
Set-Alias -Name via_activate_vdf -Value via-activate-vdf -Scope Global -Force
Set-Alias -Name 啟動VDF -Value via-activate-vdf -Scope Global -Force
