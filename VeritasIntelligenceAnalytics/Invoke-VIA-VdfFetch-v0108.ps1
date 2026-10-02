# CELERITAS-TEMPLATE-JOIN v1(啟動器接法沿 v0107:模板章由 v0107 在動態模組裡套,本檔只多一段「先補清單」)
#Requires -Version 7.0
# Invoke-VIA-VdfFetch v0108 — 薄尾:一個指令 = ① 先自動補齊台股清單 + 主動式台股 ETF 清單 → ② 全部步驟同步(並行)啟用
#
# 操作員 2026-10-02:「一個ps指令加入加速器先啟動自動補齊台股清單及主動式台股etf清單在全部同步啟用」
# v0107 一字不動(L04);本檔做完 ① 就把同一組參數原樣交給 v0107(② = v0107 的 plan → Hydra 哨兵 → CGC_MDL134 並行跑全部步)。
#
# ① 清單補齊(依序;順序取自正主 VDF_ENG087 `refresh --plan`,本檔不另寫一份清單邏輯):
#   1 台股上市櫃公司清單        via-vcgc run CGC_MDL139_InputConsole run --item macro_lanes lanes=L1
#   2 主動式台股 ETF 總清單      via-vcgc run CGC_MDL139_InputConsole run --item etf_universe
#   3 主動 ETF 每日持股(=驗證)   via-vcgc run CGC_MDL139_InputConsole run --item etf_holdings_daily
#   4 主動 ETF 名碼官方定奪      via-vcgc run FLOW_ENG023_FlowTwActiveEtf --refresh
#   5 股票日快照(價∪籌碼∩清單) via-vcgc run CGC_MDL139_InputConsole run --item tw_universe_update
#   6 台股清單 新上市 / 下市     via-vcgc run --family vdf VDF_ENG087_MarketListGovernance diff
#   7 每日兩張清單檔             via-vcgc run --family vdf VDF_ENG231_GlobalListings lists
#   每步都經 VCGC(VIA_FROM_VCGC=YES 只設在本行程、跑完還原);網路只經各引擎自己的統包網路工具,同意閘在工具裡:
#   閘沒開 = 該步誠實回 GATE / SKIP,不代開、不中斷,① 跑完照樣進 ②。rc:0 綠 · 2 沒料 / 有發現 · 4 閘關 · 其他 紅。
#
# 用法(PowerShell 7;同 v0107 的參數全部照收):
#   pwsh -NoProfile -File "<本檔>" -Since 2023-06-01            ① 補兩張清單 → ② 2023-06-01 到今天全部步並行
#   pwsh -NoProfile -File "<本檔>" -Since 2023-06-01 -Dry       ① 主控台各步 --dry、名碼定奪 / 清單檔略過 → ② 只看計畫
#   pwsh -NoProfile -File "<本檔>" -SkipLists                   只跑 ②(= v0107)
#   via-vdffetch 取尾版 = 本檔(短令照舊)
param(
    [string]$Year = "2023",
    [int]$Limit = 0,
    [switch]$Dry,
    [switch]$NoEnter,
    [switch]$NoHeal,
    [string]$Root = "",
    [string]$Since = "",
    [string]$Steps = "",
    [switch]$SkipLists
)
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

$ErrorActionPreference = "Continue"
$script:Dotted = ($MyInvocation.InvocationName -eq ".")
$here = if ($Root) { $Root } else { $PSScriptRoot }
$prior = Get-ChildItem -LiteralPath $here -Filter "Invoke-VIA-VdfFetch-v*.ps1" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne (Split-Path -Leaf $PSCommandPath) } | Sort-Object Name | Select-Object -Last 1
if (-not $prior) {
    Write-Host "  [FAIL] 前版 Invoke-VIA-VdfFetch-v*.ps1 不在(本檔只是薄尾)" -ForegroundColor Red
    if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 }
}
$fwd = @{}
foreach ($k in @("Year", "Limit", "Dry", "NoEnter", "NoHeal", "Root", "Since", "Steps")) {
    if ($PSBoundParameters.ContainsKey($k)) { $fwd[$k] = $PSBoundParameters[$k] }
}

# ---------------------------------------------------------------- ① 清單補齊
$listRows = @()
if (-not $SkipLists) {
    $reg = Join-Path $here "supportive modules\registry"
    $vcgc = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -ErrorAction SilentlyContinue |
        Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1
    if (-not $vcgc) {
        Write-Host "  [FAIL] VCGC 尾版不在(CGC_MDL149_VeritasCentralGovernanceConsole_v*.py);① 略過,直接進 ②" -ForegroundColor Red
    } else {
        $pyProg = Join-Path $here "supportive modules\VIA_PS_PyProgress_Module.ps1"
        if (Test-Path -LiteralPath $pyProg) { . $pyProg }
        $fromBefore = $env:VIA_FROM_VCGC
        $env:VIA_FROM_VCGC = "YES"
        $dryArg = @(if ($Dry) { "--dry" })
        $plan = @(
            @{ n = "台股上市櫃公司清單";       a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "macro_lanes", "lanes=L1") + $dryArg; dryOk = $true },
            @{ n = "主動式台股 ETF 總清單";     a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "etf_universe") + $dryArg; dryOk = $true },
            @{ n = "主動 ETF 每日持股(驗證)";  a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "etf_holdings_daily") + $dryArg; dryOk = $true },
            @{ n = "主動 ETF 名碼官方定奪";     a = @("run", "FLOW_ENG023_FlowTwActiveEtf", "--refresh"); dryOk = $false },
            @{ n = "股票日快照";               a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "tw_universe_update") + $dryArg; dryOk = $true },
            @{ n = "台股清單 新上市 / 下市";    a = @("run", "--family", "vdf", "VDF_ENG087_MarketListGovernance", "diff") + $dryArg; dryOk = $true },
            @{ n = "每日兩張清單檔";            a = @("run", "--family", "vdf", "VDF_ENG231_GlobalListings", "lists"); dryOk = $false }
        )
        Write-Host ("=== [via-vdffetch v0108] ① 先補台股清單 + 主動式台股 ETF 清單(" + $plan.Count + " 步,經 " + $vcgc.Name + ")===") -ForegroundColor Cyan
        $i = 0
        foreach ($s in $plan) {
            $i++
            if ($Dry -and -not $s.dryOk) {
                $listRows += [pscustomobject]@{ No = $i; Step = $s.n; Lamp = "SKIP"; Rc = "-"; Secs = 0 }
                Write-Host ("  [" + $i + "/" + $plan.Count + "] " + $s.n + " · SKIP(-Dry:本步沒有乾跑)") -ForegroundColor DarkGray
                continue
            }
            Write-Host ("  [" + $i + "/" + $plan.Count + "] " + $s.n + " …") -ForegroundColor Cyan
            $t0 = Get-Date
            $argv = @($vcgc.FullName) + @($s.a)
            if (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue) { Invoke-VIAPython -Python "python" @argv }
            else { & python @argv }
            $rc = $LASTEXITCODE
            $lamp = switch ($rc) { 0 { "GREEN" } 2 { "NODATA" } 3 { "ABSENT" } 4 { "GATE" } default { "RED" } }
            $secs = [int]((Get-Date) - $t0).TotalSeconds
            $listRows += [pscustomobject]@{ No = $i; Step = $s.n; Lamp = $lamp; Rc = $rc; Secs = $secs }
            Write-Host ("  [" + $i + "/" + $plan.Count + "] " + $s.n + " · " + $lamp + " · rc " + $rc + " · " + $secs + "s") -ForegroundColor $(if ($lamp -eq "GREEN") { "Green" } elseif ($lamp -eq "RED") { "Red" } else { "Yellow" })
        }
        $env:VIA_FROM_VCGC = $fromBefore
        Write-Host "=== ① 清單補齊總表 ===" -ForegroundColor Cyan
        $listRows | Format-Table -AutoSize | Out-String | Write-Host
        if ($listRows | Where-Object { $_.Lamp -eq "GATE" }) {
            Write-Host "  [閘] 有步回 GATE = 同意閘沒開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手;本檔不代開)" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------- ② 全部步同步(並行)啟用 = v0107
Write-Host ("=== [via-vdffetch v0108] ② 全部步同步啟用 → " + $prior.Name + " ===") -ForegroundColor Cyan
& $prior.FullName @fwd
$rc2 = $LASTEXITCODE
$redLists = @($listRows | Where-Object { $_.Lamp -eq "RED" }).Count
Write-Host ("=== [via-vdffetch v0108] 畢 · ① 清單 " + $listRows.Count + " 步(紅 " + $redLists + ")· ② rc " + $rc2 + " ===") -ForegroundColor Cyan
$final = if ($rc2 -ne 0) { $rc2 } elseif ($redLists -gt 0) { 1 } else { 0 }
if ($script:Dotted) { $global:LASTEXITCODE = $final; return } else { exit $final }
