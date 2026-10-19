# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VDF-Activate-v0105.ps1 — VDF 獨立一鍵:加速器 + 網路模組 + 覆蓋檢查 + ActivateVDF(自測 → 真跑 → 總覽頁 + 資料庫清點)
#   v0105(操作員 2026-10-19「這裡專注 修正獨立系統VDF 自動跳出HTML U/I清點資料庫沒問題就是收尾」= L70 許可 P024;v0100–v0104 一字不動):
#     ① 一開跑就印同意閘狀態(開 / 沒開 + 要開的兩行),不用等到 ④ 才知道這輪抓不了網
#     ② Ctrl+C / 中途停:總表標 INTERRUPTED、結束碼 130(v0104 在 ② 中途按 Ctrl+C 會印「結束碼 0」= 假綠);
#        ActivateVDF 回報 interrupted 也照 130;主體丟錯 = 一列紅「主體出錯」+ 結束碼 1(錯誤照實印)
#     ③ 總表多一列 6⑤ 資料庫清點(ActivateVDF v0106 寫進總覽 JSON 的 db 節:VDF 表 紅 / 黃 / 綠 · 他系統表 · 收尾判定),
#        跑完印一行收尾判定;自動跳出的總覽頁最上方就是清點表(哪張表缺 / 空 / 舊 · 寫入者 · 怎麼補)
#     ④ -DbHome 沒給時:操作員已設 VIA_VDF_DB_HOME 就照它(v0104 會用 <FetchHome>\output_hub 蓋掉它)
#   v0104(PR #532 Codex P2 = L70 許可 P023;v0100–v0103 一字不動):PYTHONPATH 去重時**空段照留**(Python 把空段當目前目錄),
#   只拿掉第一份之後的 supportive modules\bootstrap;不再 Select-Object -Unique(那會把重複的一般路徑 / 空段也合併掉)。其餘同 v0103。
#   v0103(操作員 2026-10-18 工作站實跑 v0102 貼回:② ③ 各 300 秒逾時、3b 357 秒、ActivateVDF 自測裡 `python -c "import numexpr"` 120 秒逾時
#   = L70 許可 P022;v0100–v0102 一字不動):根因是 v0102 的 Set-VIABoot 替身 —— 操作員 $PROFILE 已把**另一棵樹**(OneDrive)的
#   supportive modules\bootstrap 放進 PYTHONPATH,替身又把本樹(via-main)的 bootstrap 疊到最前面 → 兩份 sitecustomize.py,
#   它的 _chain_shadowed() 會跑「sys.path 上下一份同名檔」→ 兩份互相接力到遞迴上限,每支 Python(含子行程)起跑都重做一大段
#   (容器量:一份 1.5 秒 · 兩份 10 秒;工作站全裝 88 件冊 → 逾時)。本版:
#     ① 替身只在**還沒有任何** bootstrap 時才補本樹那一份;VIA_ROOT 已設就不動(= v0100 在工作站的環境)
#     ② 起跑先查 PYTHONPATH:有兩份以上 supportive modules\bootstrap 就只留第一份(本支範圍;跑完還原)——操作員視窗原本就壞也擋得住
#   v0102(操作員 2026-10-18 工作站實跑貼回 v0100 結果 = L70 許可 P021;v0100 / v0101 一字不動)修三件「操作員視窗殘件」:
#     ① 視窗裡已有別人留下的 Celeritas 殘件(Register 的 Invoke-VIACeleritasScoped 只匯出 Restore-CeleritasPS7;
#        總表函式的狀態是空的)→ 模板塊以為已接就略過 → ① 黃、總表頭「Celeritas  applied=False workers=」。
#        改:模板塊沒由本支接上時,把正主點源進本支範圍重接(只動本行程,跑完還原);接不上照實黃。
#     ② 操作員的短令覆蓋檔把 Set-VIABoot 換成 DEPRECATED 殘樁(印一行 + 吐 2),Invoke-VIAPython 每次都叫它 →
#        每步多兩行雜訊。改:只在偵測到殘樁時,本支範圍給一個做原本那件事的安靜同名函式(VIA_ROOT + bootstrap 進 PYTHONPATH),
#        跑完把這兩個環境變數還原;操作員視窗裡那一個不動。
#     ③ 中央 Invoke-VIAPython 的進度條和本支逐行直播搶同一列 → 每行尾巴殘字(…_NET_CONSENT… ])。
#        本支每行都已直播,子步驟期間關進度條(只在本支範圍)。
#   v0101(操作員 2026-10-18「INTEGRATE INTO ONE PS CODE WITH 加速器模板並確保所有VDF模組都有導入網路工具 善用VCGC節省TOKEN工具注入AST上加速覆蓋到7全部」
#   = L70 這一次的許可 P020;v0100 一字不動):多一步 ③b 覆蓋檢查,每次跑都確認全部 VDF 模組接了加速器與網路工具 ——
#     Py 端:VDF 自己的管理員 `bridges`(尾版逐支;尺 = CGC_MDL124 橋掃器的排除清單 / 真擷取判定,只讀)
#     PS 端:VDF 夾內每族尾版 .ps1 要有模板章 CELERITAS-TEMPLATE-JOIN 與 [VIA:PS-ACCEL] 橋(排除 history / intake / 虛擬環境 / 已取代)
#     缺 = 結束碼紅 + 印補橋指令(經 VCGC 的 AST 注入工具 CGC_MDL124 --apply;本支不代改任何檔)
#   操作員 2026-10-18:「FIX ALL AND INTEGRATE ALL INTI A PS CODE WITH ACCELERATORS AND NETWORK MODULES.」
#   = L70 v0100 那一次的許可 P019(v0100 本體);v0101 = P020。
#   VDF 自己的入口(L120 三系統獨立):只跑 VDF 的 ActivateVDF.py;不經 VCGC / VRN、不載入他系統程式。
#   步驟(每步一列,最後印 MATRIX SUMMARY):
#     ① 加速器 · PS 端  [VIA:PS-TEMPLATE] Celeritas PS7 模板(只動本行程 · 關閉即還原)+ [VIA:PS-ACCEL] 25 格加速器橋
#     ② 加速器 · Py 端  SUP_MDL737_SuperAccelModule 尾版 --selftest(鎖版導向 VeritasCeleritas)
#     ③ 網路模組        via_net_unified 尾版 --selftest(→ SUP_MDL740_NetUnified → VeritasAegisNexus 鎖版;離線,不觸網)
#     ③b 覆蓋檢查      VDF 全部模組:Py 加速器橋 + 網路橋(VDF_SystemManager bridges)· PS 模板章 + PS-ACCEL(每族尾版)
#     ④ 同意閘          只讀不寫:VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手;沒開 = 照跑,擷取段照實 GATED
#     ⑤ ActivateVDF 自測(紅 = 停,不真跑)
#     ⑥ ActivateVDF 真跑(CPU/DRAM → 兩張清單 → 三條流程並行 → U/I;心跳照印;Ctrl+C 子行程樹收乾淨照寫總覽)
#     ⑦ 跳出總覽頁 VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.html(Open-VIAOwnPage;子行程照吃 VIA_NO_OPEN=1)
# 用法(熱 PS 直接貼;站在倉內任何資料夾):
#   & (Get-ChildItem (Join-Path (git rev-parse --show-toplevel) 'VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VDF-Activate-v*.ps1') | Sort-Object Name | Select-Object -Last 1).FullName -FetchHome <VDF 夾> -RefillApply
#   參數 [-Action run|selftest|preflight] [-FetchHome <夾>] [-DbHome <夾>(預設 VIA_VDF_DB_HOME;沒設 = <FetchHome>\output_hub)] [-RefillApply]
#        [-Flows fetch,engines,db] [-Mode live|fixture|block] [-DryFetch] [-SkipSelftest] [-NoOpen]
#        [-TimeoutHours 12] [-Python <VDF python.exe>] [-SystemDir <VeritasIntelligenceAnalytics 夾>]
#   結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件 · 124 逾時 · 130 中斷
# 不 push、不裝套件、不代開同意閘、不碰 TA-Lib;python 只經 Invoke-VIAPython 叫。
# =====================================================================================
[CmdletBinding()]
param(
    [ValidateSet('run', 'selftest', 'preflight')][string]$Action = 'run',
    [string]$FetchHome = "",
    [string]$DbHome = "",
    [switch]$RefillApply,
    [string]$Flows = "",
    [ValidateSet('live', 'fixture', 'block')][string]$Mode = 'live',
    [switch]$DryFetch,
    [switch]$SkipSelftest,
    [switch]$NoOpen,
    [int]$TimeoutHours = 12,
    [string]$Python = "",
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
$VIAActCelOwn = $VIACelTplOwn   # 先記下:加速器模組點源的冊自帶模板塊,會把 $VIACelTplOwn 蓋成 $false(同 FullCheck v0101)
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
# ===== [VDF:CEL-REJOIN:v0102] 模板塊沒由本支接上(視窗裡有別人的 Celeritas 殘件就會略過)→ 正主點源進本支範圍重接 =====
$VIACelRejoin = ""
if ((-not $VIAActCelOwn) -and ($PSVersionTable.PSVersion.Major -ge 7)) {
    $VIACelRejoinFile = $null
    $VIACelRejoinProbe = $PSScriptRoot
    while ($VIACelRejoinProbe) {
        $VIACelRejoinTry = Join-Path $VIACelRejoinProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
        if (Test-Path -LiteralPath $VIACelRejoinTry) { $VIACelRejoinFile = $VIACelRejoinTry; break }
        $VIACelRejoinUp = Split-Path $VIACelRejoinProbe -Parent
        if ((-not $VIACelRejoinUp) -or ($VIACelRejoinUp -eq $VIACelRejoinProbe)) { break }
        $VIACelRejoinProbe = $VIACelRejoinUp
    }
    if ($VIACelRejoinFile) {
        try {
            $script:CeleritasPS7 = $null       # 正主見空就在本支範圍重新起一份狀態(不沿用別人那份)
            $null = . $VIACelRejoinFile -RestoreOnly
            Set-StrictMode -Off
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') { Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                [void](Start-CeleritasPS7)
                $VIAActCelOwn = [bool]$script:CeleritasPS7.Applied
            }
            $VIACelRejoin = if ($VIAActCelOwn) { "視窗裡的 Celeritas 殘件不能用 → 正主已在本支範圍重接" } else { "重接後仍沒套上" }
        } catch {
            Set-StrictMode -Off
            $VIACelRejoin = "重接失敗:" + $_.Exception.Message
        }
    }
}
# ===== [VDF:CEL-REJOIN:END] =====
# ===== [VDF:BOOT-SHIM:v0103] Invoke-VIAPython 每次叫 Set-VIABoot;操作員的短令覆蓋檔把它換成 DEPRECATED 殘樁(印一行 + 吐 2)=====
#   v0103:PYTHONPATH 上只准一份 supportive modules\bootstrap(兩份 = sitecustomize 互相接力到遞迴上限,每支 Python 起跑都慢到逾時)
$VIABootPrev = @{ ROOT = $env:VIA_ROOT; PYTHONPATH = $env:PYTHONPATH }
$VIABootShim = $false
$VIABootNote = ""
$VIABootRx = '[\\/]supportive modules[\\/]bootstrap[\\/]?$'
$VIABootParts = @(("" + $env:PYTHONPATH) -split [regex]::Escape([string][IO.Path]::PathSeparator))   # 空段照留(= 目前目錄;PR #532 Codex P2)
$VIABootHits = @($VIABootParts | Where-Object { $_ -and ($_ -match $VIABootRx) })
if ($VIABootHits.Count -gt 1) {
    $VIABootKeep = $VIABootHits[0]
    $VIABootSeen = $false
    $VIABootOut = foreach ($VIABootP in $VIABootParts) {
        if ($VIABootP -and ($VIABootP -match $VIABootRx)) { if ($VIABootSeen) { continue }; $VIABootSeen = $true }
        $VIABootP
    }
    $env:PYTHONPATH = @($VIABootOut) -join [IO.Path]::PathSeparator
    $VIABootNote = "PYTHONPATH 有 " + $VIABootHits.Count + " 份 bootstrap → 本支只留第一份 " + $VIABootKeep + "(跑完還原)"
}
$VIABootCmd = Get-Command Set-VIABoot -CommandType Function -ErrorAction Ignore
if ($VIABootCmd -and (("" + $VIABootCmd.Definition) -match 'DEPRECATED')) {
    function script:Set-VIABoot {
        # 安靜替身(只在本支範圍):已有任何一份 bootstrap / 已設 VIA_ROOT 就**一個字都不動**;都沒有才補本樹那一份(= Register v0243 原義)
        $have = @(("" + $env:PYTHONPATH) -split [regex]::Escape([string][IO.Path]::PathSeparator) | Where-Object { $_ -match $VIABootRx })
        if ($have.Count -gt 0) { return }
        $b = Join-Path $VIA "supportive modules\bootstrap"
        if (-not (Test-Path -LiteralPath $b)) { return }
        if (-not $env:VIA_ROOT) { $env:VIA_ROOT = $VIA }
        $cur = "" + $env:PYTHONPATH
        $env:PYTHONPATH = if ($cur) { $b + [IO.Path]::PathSeparator + $cur } else { $b }
    }
    $VIABootShim = $true
}
# ===== [VDF:BOOT-SHIM:END] =====

function Open-VIAOwnPage {
    # [VIA:OWN-PAGE:v0100] 開本支自己的總頁:子行程照吃 VIA_NO_OPEN=1(零跳出閘);本支只看呼叫端原值
    param([Parameter(Mandatory)][string]$Page, [string]$CallerNoOpen = "")
    if (-not (Test-Path -LiteralPath $Page)) {
        Write-Host ("  [頁] 這輪沒產出總覽頁(看上面紅字):" + $Page) -ForegroundColor Red
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

function Get-VDFNewest {
    # 夾內同族四碼版號尾版(只認 _vNNNN;不認無版號 / 異形)
    param([Parameter(Mandatory)][string]$Dir, [Parameter(Mandatory)][string]$Stem)
    if (-not (Test-Path -LiteralPath $Dir)) { return $null }
    $hits = @(Get-ChildItem -LiteralPath $Dir -Filter ($Stem + "_v*.py") -File -ErrorAction SilentlyContinue |
              Where-Object { $_.BaseName -match '_v(\d{4})$' } |
              Sort-Object { [int]($_.BaseName -replace '^.*_v(\d{4})$', '$1') })
    if ($hits.Count -eq 0) { return $null }
    return $hits[-1]
}

function Resolve-VDFPython {
    # VDF 家族 python:-Python > Get-VIAEnvPython vdf > VIA_PY_VDF > %USERPROFILE%\envs\via_vdf_312 / via_vdf / via_vdf_313;都沒有才用 PATH 上的 python(黃字照說)
    param([string]$Given = "")
    if ($Given) { return @{ exe = $Given; how = "-Python" } }
    if (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) {
        try { $p = Get-VIAEnvPython vdf; if ($p -and $p -ne "python" -and (Test-Path -LiteralPath $p)) { return @{ exe = $p; how = "Get-VIAEnvPython vdf" } } } catch { }
    }
    if ($env:VIA_PY_VDF -and (Test-Path -LiteralPath $env:VIA_PY_VDF)) { return @{ exe = $env:VIA_PY_VDF; how = "VIA_PY_VDF" } }
    $roots = @()
    if ($env:VIA_ENV_ROOT) { $roots += $env:VIA_ENV_ROOT }
    if ($env:USERPROFILE) { $roots += (Join-Path $env:USERPROFILE "envs") }
    foreach ($root in $roots) {
        foreach ($name in 'via_vdf_312', 'via_vdf', 'via_vdf_313') {
            foreach ($rel in 'Scripts\python.exe', 'bin/python') {
                $cand = Join-Path (Join-Path $root $name) $rel
                if (Test-Path -LiteralPath $cand) { return @{ exe = $cand; how = ($root + " · " + $name) } }
            }
        }
    }
    return @{ exe = "python"; how = "PATH 上的 python(沒找到 VDF 家族環境;缺套件會照實黃燈)" }
}

function Get-VDFPsCoverage {
    # VDF 夾內每族尾版 .ps1(族 = 同夾 + 檔名去掉 -vNNNN):模板章 + PS-ACCEL 橋;排除版史 / 收件 / 虛擬環境 / 已取代 / 隔離
    param([Parameter(Mandatory)][string]$Dir)
    $skip = '[\\/](history|intake|_inbox_to_classify|_vdf_envs|envs|Scripts|_rebuilds_superseded|VIA_RetiredEngines|_quarantine|VIA_Reports|SCOPE_COPY)[\\/]'
    $fam = @{}
    foreach ($f in @(Get-ChildItem -LiteralPath $Dir -Filter *.ps1 -File -Recurse -ErrorAction SilentlyContinue)) {
        if ($f.FullName -match $skip) { continue }
        $name = $f.BaseName -replace '-v\d{4}$', ''
        $ver = if ($f.BaseName -match '-v(\d{4})$') { [int]$Matches[1] } else { -1 }
        $key = $f.DirectoryName + '|' + $name
        if (-not $fam.ContainsKey($key) -or $ver -gt $fam[$key].ver) { $fam[$key] = @{ ver = $ver; file = $f } }
    }
    $miss = [System.Collections.Generic.List[string]]::new()
    $tpl = 0; $acc = 0
    foreach ($v in $fam.Values) {
        $t = Get-Content -LiteralPath $v.file.FullName -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        $hasT = ("" + $t).Contains('CELERITAS-TEMPLATE-JOIN')
        $hasA = ("" + $t).Contains('[VIA:PS-ACCEL:') -or ("" + $t).Contains('VIA_PS_Accel_Module.ps1')
        if ($hasT) { $tpl++ }
        if ($hasA) { $acc++ }
        if (-not ($hasT -and $hasA)) { $miss.Add($v.file.Name + $(if (-not $hasT) { ' 缺模板章' } else { '' }) + $(if (-not $hasA) { ' 缺PS-ACCEL' } else { '' })) }
    }
    return [pscustomobject]@{ tails = $fam.Count; tpl = $tpl; acc = $acc; missing = $miss }
}

$VIA = if ($SystemDir) { $SystemDir } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$StartDir = (Get-Location).Path
$prev = @{ OPEN = $env:VIA_NO_OPEN; FAMILY = $env:VIA_FAMILY }
$script:exitCode = 0
$script:preExit = 0     # ①–③ 先決步驟的較壞結束碼(加速器 / 網路模組自測紅了要帶進最後的結束碼)
$rows = [System.Collections.Generic.List[object]]::new()
function Add-VDFRow { param($Id, $Title, $State, $Sec, $Note) $rows.Add([pscustomobject]@{ id = "" + $Id; title = $Title; state = $State; sec = "" + $Sec; note = $Note }) }
function Get-VDFLamp { param([int]$Rc) switch ($Rc) { 0 { "GREEN" } 2 { "YELLOW" } 3 { "YELLOW" } 4 { "GATED" } 124 { "TIMEOUT" } 130 { "INTERRUPTED" } default { "RED" } } }
function Merge-VDFExit {
    # 兩個結束碼取較壞的一個(0 綠 < 2 黃 < 1 紅 < 124 逾時 < 130 中斷);先決步驟紅了不得被後面的綠蓋掉(PR #529 Codex P1)
    param([int]$A, [int]$B)
    $rank = @{ 0 = 0; 2 = 1; 3 = 1; 4 = 1; 1 = 2; 124 = 3; 130 = 4 }
    $ra = if ($rank.ContainsKey($A)) { $rank[$A] } else { 2 }
    $rb = if ($rank.ContainsKey($B)) { $rank[$B] } else { 2 }
    $hi = if ($ra -ge $rb) { $A } else { $B }
    if ($hi -in 3, 4) { return 2 }
    if (-not $rank.ContainsKey($hi)) { return 1 }
    return $hi
}
function ConvertTo-VDFExit { param([int]$Rc) switch ($Rc) { 0 { 0 } 2 { 2 } 3 { 2 } 4 { 2 } 124 { 124 } 130 { 130 } default { 1 } } }
$clock = [Diagnostics.Stopwatch]::StartNew()
function Invoke-VDFActivateMain {
    # 主體寫成函式:return 只離開函式,腳本尾的 exit $script:exitCode 一定跑得到
    $vdfDir = Join-Path $VIA "functional modules\VDF"
    $supDir = Join-Path $VIA "supportive modules"
    $netDir = Join-Path $supDir "network"
    $entry = Join-Path $vdfDir "ActivateVDF.py"
    if (-not (Test-Path -LiteralPath $entry)) {
        Write-Host ("  [VDF 一鍵] 找不到 " + $entry + "(用 -SystemDir 指到 VeritasIntelligenceAnalytics;或先 git pull)") -ForegroundColor Red
        $script:exitCode = 3
        return
    }
    Set-Location -LiteralPath $VIA
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        $pyMod = Join-Path $supDir "VIA_PS_PyProgress_Module.ps1"
        if (Test-Path -LiteralPath $pyMod) { . $pyMod }
    }
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        Write-Host "  [VDF 一鍵] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
        $script:exitCode = 3
        return
    }
    $py = Resolve-VDFPython -Given $Python
    $env:VIA_NO_OPEN = "1"   # 只給子行程(各自不跳頁);本支自己的總覽頁走 Open-VIAOwnPage
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  VDF 獨立一鍵 v0105 · 加速器 + 網路模組 + 覆蓋 + 資料庫清點         ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ("  [python] " + $py.exe + " · " + $py.how) -ForegroundColor DarkGray
    if ($VIABootNote) { Write-Host ("  [開機] " + $VIABootNote) -ForegroundColor Yellow }
    # v0105 ①:一開跑就說同意閘開沒開(只讀;操作員的手)
    $kNet0 = 'VIA_NET' + '_CONSENT'
    $kScr0 = 'VIA_SCRAPE' + '_CONSENT'
    $vNet0 = [Environment]::GetEnvironmentVariable($kNet0)
    $vScr0 = [Environment]::GetEnvironmentVariable($kScr0)
    if (($vNet0 -eq 'YES') -and ($vScr0 -in @('YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING'))) {
        Write-Host "  [同意閘] 開(本視窗操作員親手開)→ 本輪擷取會觸網" -ForegroundColor Green
    } else {
        Write-Host ("  [同意閘] 沒開(" + $kNet0 + "=" + $(if ($vNet0) { $vNet0 } else { "(空)" }) + " · " + $kScr0 + "=" + $(if ($vScr0) { $vScr0 } else { "(空)" }) + ")→ 本輪擷取 / 補資料照實 GATED;要抓網請先 Ctrl+C,在本視窗打:") -ForegroundColor Yellow
        Write-Host ("      `$env:" + $kNet0 + " = " + "'YES'" + "; `$env:" + $kScr0 + " = " + "'YES'") -ForegroundColor Yellow
    }

    # ① 加速器 · PS 端
    $cel = $null
    if (Get-Command Get-CeleritasStatus -ErrorAction SilentlyContinue) { try { $cel = Get-CeleritasStatus } catch { $cel = $null } }
    $accelPs = [bool](Get-Command Show-VIAAccel20 -ErrorAction SilentlyContinue) -or [bool]$env:VIA_ACCEL_LIT
    if ($cel) {
        $note = $(if ($VIACelRejoin) { $VIACelRejoin + " · " } else { "" }) + "Celeritas PS7 " + $cel.Version + " · 執行緒 " + $cel.Workers + " / " + $cel.Cores + " 核 · 優先權 " + $cel.Priority + $(if ($VIAActCelOwn) { " · 本支套上,跑完還原" } else { " · 沿用本視窗已套的模板" }) + $(if ($accelPs) { " · PS 加速器橋在" } else { " · PS 加速器橋缺" })
        Write-Host ("  [①加速器·PS] " + $note) -ForegroundColor DarkCyan
        Add-VDFRow 1 "加速器 · PS 端" $(if ($accelPs) { "GREEN" } else { "YELLOW" }) "0" $note
    } else {
        Write-Host ("  [①加速器·PS] Celeritas PS7 模板沒接上(supportive modules\ps7\VeritasCeleritas.PS7.ps1 不在,或不是 PowerShell 7)· 照跑,不加速" + $(if ($VIACelRejoin) { " · " + $VIACelRejoin } else { "" })) -ForegroundColor Yellow
        Add-VDFRow 1 "加速器 · PS 端" "YELLOW" "0" ("Celeritas PS7 模板沒接上 · 照跑不加速" + $(if ($VIACelRejoin) { " · " + $VIACelRejoin } else { "" }))
    }

    $runPy = {
        param([string]$Title, [int]$TimeoutSec, [object[]]$PyArgs)
        $lines = [System.Collections.Generic.List[string]]::new()
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $body = {
            $ProgressPreference = 'SilentlyContinue'   # v0102 ③:本支逐行直播,中央進度條會跟它搶同一列留殘字;只在本範圍關
            Invoke-VIAPython -Family 'vdf' -Python $py.exe -TimeoutSec $TimeoutSec @PyArgs 2>&1 | ForEach-Object {
                $s = "" + $_
                $lines.Add($s)
                $color = if ($s -match '\[FAIL\]|\bRED\b|紅') { "Red" } elseif ($s -match '\bYELLOW\b|\bGATED\b|黃|\[取代\]') { "Yellow" } elseif ($s -match '\[OK\]|\bGREEN\b|PASS') { "Green" } elseif ($s -match '進行中|\[完成\]') { "Cyan" } else { "Gray" }
                Write-Host $s -ForegroundColor $color
            }
        }
        $global:LASTEXITCODE = 0
        if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { $null = Invoke-VIACeleritasScoped -Body $body } else { $null = & $body }
        $rc = $global:LASTEXITCODE
        $last = ($lines | Where-Object { $_ -match '\[計\]' } | Select-Object -Last 1)
        if (-not $last) { $last = ($lines | Select-Object -Last 1) }
        return [pscustomobject]@{ rc = $rc; sec = [Math]::Round($sw.Elapsed.TotalSeconds, 1); last = ("" + $last).Trim(); lines = $lines }
    }

    # ② 加速器 · Py 端
    $acc = Get-VDFNewest -Dir $supDir -Stem "SUP_MDL737_SuperAccelModule"
    if ($acc) {
        Write-Host ("  [②加速器·Py] " + $acc.Name + " --selftest") -ForegroundColor DarkCyan
        $r = & $runPy "加速器 · Py 端" 300 @($acc.FullName, "--selftest")
        $script:preExit = Merge-VDFExit $script:preExit (ConvertTo-VDFExit $r.rc)
        Add-VDFRow 2 ("加速器 · Py 端 " + $acc.BaseName) (Get-VDFLamp $r.rc) $r.sec $r.last
    } else {
        $script:preExit = Merge-VDFExit $script:preExit 2
        Add-VDFRow 2 "加速器 · Py 端" "YELLOW" "0" "SUP_MDL737_SuperAccelModule 尾版不在(ActivateVDF 的 ACCEL 橋缺席零影響)"
    }

    # ③ 網路模組
    $net = Get-VDFNewest -Dir $netDir -Stem "via_net_unified"
    if ($net) {
        Write-Host ("  [③網路模組] " + $net.Name + " --selftest(→ SUP_MDL740_NetUnified → VeritasAegisNexus;離線)") -ForegroundColor DarkCyan
        $r = & $runPy "網路模組" 300 @($net.FullName, "--selftest")
        $script:preExit = Merge-VDFExit $script:preExit (ConvertTo-VDFExit $r.rc)
        $aeg = ($r.lines | Where-Object { $_ -match 'VeritasAegisNexus_v\d+' } | Select-Object -Last 1)
        Add-VDFRow 3 ("網路模組 " + $net.BaseName) (Get-VDFLamp $r.rc) $r.sec $(if ($aeg) { ("" + $aeg).Trim() } else { $r.last })
    } else {
        $script:preExit = Merge-VDFExit $script:preExit 1
        Add-VDFRow 3 "網路模組" "RED" "0" "supportive modules\network\via_net_unified_v*.py 不在(ActivateVDF 的擷取要它)"
    }

    # ③b 覆蓋檢查:全部 VDF 模組接了加速器與網路工具(Py 走 VDF 自己的管理員 bridges;PS 掃每族尾版)
    $mgr = Get-VDFNewest -Dir $vdfDir -Stem "VDF_SystemManager"
    if ($mgr) {
        Write-Host ("  [③b覆蓋·Py] " + $mgr.Name + " bridges(尾版逐支:加速器橋 · 網路橋;尺 = CGC_MDL124 排除清單,只讀)") -ForegroundColor DarkCyan
        $r = & $runPy "覆蓋 · Py" 600 @($mgr.FullName, "bridges")
        $cov = ($r.lines | Where-Object { $_ -match '\[計\]' } | Select-Object -Last 1)
        $script:preExit = Merge-VDFExit $script:preExit (ConvertTo-VDFExit $r.rc)
        Add-VDFRow "3b" "覆蓋 · Py 加速器 + 網路橋" (Get-VDFLamp $r.rc) $r.sec $(if ($cov) { (("" + $cov) -replace '^\s*\[計\]\s*', '' -replace '\s*·\s*版史.*$', '').Trim() } else { $r.last })
        if ($r.rc -eq 1) {
            Write-Host "      補橋(經 VCGC 的 AST 注入工具;先看計畫再 --apply):" -ForegroundColor Yellow
            Write-Host ("      python `"" + (Join-Path $supDir "registry") + "\CGC_MDL124_BridgeSweeper_v<尾版>.py`" --subsystems [--apply]") -ForegroundColor Yellow
        }
    } else {
        $script:preExit = Merge-VDFExit $script:preExit 1
        Add-VDFRow "3b" "覆蓋 · Py 加速器 + 網路橋" "RED" "0" "VDF_SystemManager 尾版不在"
    }
    $psCov = Get-VDFPsCoverage -Dir $vdfDir
    $psLamp = if ($psCov.missing.Count -eq 0) { "GREEN" } else { "RED" }
    if ($psCov.missing.Count -gt 0) { $script:preExit = Merge-VDFExit $script:preExit 1 }
    $psNote = ("每族尾版 " + $psCov.tails + " 支 · 模板章 " + $psCov.tpl + " · PS-ACCEL " + $psCov.acc + $(if ($psCov.missing.Count) { " · 缺 " + (($psCov.missing | Select-Object -First 3) -join ' / ') } else { " · 缺 0" }))
    Write-Host ("  [③b覆蓋·PS] " + $psNote) -ForegroundColor $(if ($psLamp -eq "GREEN") { "DarkCyan" } else { "Red" })
    if ($psCov.missing.Count -gt 0) {
        Write-Host ("      PS-ACCEL 補橋:python `"" + (Join-Path $supDir "registry") + "\CGC_MDL124_BridgeSweeper_v<尾版>.py`" --ps --ps-tail --root `"functional modules/VDF`" [--apply];模板章是 .ps1 改動(L70 要操作員逐次許可)") -ForegroundColor Yellow
    }
    Add-VDFRow "3c" "覆蓋 · PS 模板章 + PS-ACCEL" $psLamp "0" $psNote

    # ④ 同意閘(只讀不寫;操作員的手)
    $kNet = 'VIA_NET' + '_CONSENT'
    $kScr = 'VIA_SCRAPE' + '_CONSENT'
    $vNet = [Environment]::GetEnvironmentVariable($kNet)
    $vScr = [Environment]::GetEnvironmentVariable($kScr)
    $gateOpen = ($vNet -eq 'YES') -and ($vScr -in @('YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING'))
    if ($gateOpen) {
        Write-Host "  [④同意閘] 雙閘開(操作員本視窗親手開)→ 擷取段會觸網" -ForegroundColor Green
        Add-VDFRow 4 "同意閘" "GREEN" "0" "雙閘開(操作員親手)"
    } else {
        Write-Host "  [④同意閘] 沒開 → 照跑:清單與擷取段照實 GATED(零出網),引擎 / 資料庫流程照跑。要抓網請您在本視窗自己打這兩行再重跑:" -ForegroundColor Yellow
        Write-Host ("      `$env:" + $kNet + " = " + "'YES'") -ForegroundColor Yellow
        Write-Host ("      `$env:" + $kScr + " = " + "'YES'") -ForegroundColor Yellow
        Add-VDFRow 4 "同意閘" "GATED" "0" "沒開(操作員的手;AI 不代開)· 擷取段照實 GATED"
    }
    $script:exitCode = $script:preExit             # 先決步驟的燈帶進結束碼(GATED 是操作員的手,不算錯)
    if ($script:preExit -ne 0) { Write-Host ("  [先決] 加速器 / 網路模組有紅或黃 → 結束碼 " + $script:preExit + "(看上表)") -ForegroundColor $(if ($script:preExit -eq 2) { 'Yellow' } else { 'Red' }) }
    if ($Action -eq 'preflight') { return }

    # ⑤ ActivateVDF 自測
    if (-not $SkipSelftest -or $Action -eq 'selftest') {
        Write-Host "  [⑤ActivateVDF 自測] ActivateVDF.py --selftest(本體尾版 + 前版鏈)" -ForegroundColor DarkCyan
        $r = & $runPy "ActivateVDF 自測" 1800 @($entry, "--selftest")
        $marks = @($r.lines | Where-Object { $_ -match '\[計\]' } | ForEach-Object { ($_ -replace '^\s*\[計\]\s*', '').Trim() })
        Add-VDFRow 5 "ActivateVDF 自測" (Get-VDFLamp $r.rc) $r.sec $(if ($marks.Count) { $marks -join ' ‖ ' } else { $r.last })
        if ($r.rc -ne 0) {
            Write-Host ("  [⑤ActivateVDF 自測] rc " + $r.rc + " → 不真跑(先修自測紅)") -ForegroundColor Red
            $script:exitCode = Merge-VDFExit $script:preExit (ConvertTo-VDFExit $r.rc)
            return
        }
    }
    if ($Action -eq 'selftest') { return }

    # ⑥ ActivateVDF 真跑
    $argList = @($entry, "run", "--no-open", "--mode", $Mode)
    if ($FetchHome) {
        $argList += @("--fetch-home", $FetchHome)
        if (-not $DbHome -and -not $env:VIA_VDF_DB_HOME) { $DbHome = Join-Path $FetchHome "output_hub" }   # v0105 ④:操作員設的資料家優先
    }
    if ($DbHome) { $argList += @("--db-home", $DbHome) }
    if ($Flows) { $argList += @("--flows", $Flows) }
    if ($RefillApply) { $argList += "--refill-apply" }
    if ($DryFetch) { $argList += "--dry" }
    Write-Host ("  [⑥ActivateVDF 真跑] " + (($argList | Select-Object -Skip 1) -join ' ') + " · 上限 " + $TimeoutHours + " 小時(Ctrl+C = 子行程樹收乾淨並照寫總覽)") -ForegroundColor DarkCyan
    $t0 = [DateTime]::UtcNow
    $r = & $runPy "ActivateVDF 真跑" ([Math]::Max(1, $TimeoutHours) * 3600) $argList
    $script:exitCode = Merge-VDFExit $script:preExit (ConvertTo-VDFExit $r.rc)
    $json = Join-Path $VIA "VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.json"
    $fresh = (Test-Path -LiteralPath $json) -and ((Get-Item -LiteralPath $json).LastWriteTimeUtc -ge $t0.AddSeconds(-2))
    if ($fresh) {
        try {
            $card = Get-Content -LiteralPath $json -Raw -Encoding utf8 | ConvertFrom-Json
            $res = $card.resources
            Add-VDFRow "6①" "CPU/DRAM" "GREEN" "0" ("核 " + $res.cpu.usable + " · 可用 " + $res.mem.avail_mb + "/" + $res.mem.total_mb + " MB · 並行 " + $res.plan.slots + " 條 · 每條 " + $res.plan.threads_per_flow + " 執行緒")
            $lsec = 0.0; foreach ($s in @($card.lists.runs) + @($card.lists.verify)) { if ($s -and $s.secs) { $lsec += [double]$s.secs } }
            Add-VDFRow "6②" "兩張清單" ("" + $card.lists.lamp) ([Math]::Round($lsec, 1)) ("" + $card.lists.note)
            foreach ($f in @($card.flows)) {
                $fsec = 0.0; foreach ($s in @($f.steps)) { if ($s -and $s.secs) { $fsec += [double]$s.secs } }
                $fnote = if ($f.flow -eq 'engines' -and $f.launchable) { ("" + $f.launchable + "/" + $f.n + " 可啟動 · 自測 GREEN " + $f.selftest.GREEN + " · NODATA " + $f.selftest.NODATA + " · RED " + $f.selftest.RED) } else { ("" + $f.note) }
                if (-not $fnote) { $fnote = (@($f.steps) | ForEach-Object { "" + $_.step + " " + $_.lamp } ) -join ' · ' }
                Add-VDFRow ("6③" + $f.flow) ("流程 · " + $f.flow) ("" + $f.lamp) ([Math]::Round($fsec, 1)) $fnote
            }
            if ($card.ui) { Add-VDFRow "6④" "U/I" ("" + $card.ui.lamp) ("" + $card.ui.secs) ("" + $card.ui.summary) }
            $db = $card.db
            if ($db) {
                $dbNote = if ($db.counts) { ("VDF 表 " + $db.tables + " · 紅 " + $db.counts.RED + " · 黃 " + $db.counts.YELLOW + " · 綠 " + $db.counts.GREEN + " · 他系統 " + $db.other + " · " + $(if ($db.closeout) { "可收尾" } else { "還不能收尾" })) } else { ("" + $db.why) }
                Add-VDFRow "6⑤" "資料庫清點" ("" + $db.lamp) "0" $dbNote
                $script:dbVerdict = $db
            }
            Add-VDFRow 6 ("ActivateVDF 總燈 · " + $card.tag) ("" + $card.lamp) $r.sec $(if ($card.interrupted) { "已中斷(Ctrl+C)· 總覽照寫" } else { "總覽 " + $json })
            if ($card.interrupted) { $script:exitCode = Merge-VDFExit $script:exitCode 130 }   # v0105 ②:中斷不報綠
        } catch {
            Add-VDFRow 6 "ActivateVDF 真跑" (Get-VDFLamp $r.rc) $r.sec ("總覽 JSON 讀不了:" + $_.Exception.Message)
        }
    } else {
        Add-VDFRow 6 "ActivateVDF 真跑" (Get-VDFLamp $r.rc) $r.sec ("本輪沒寫出 ACTIVATE_VDF_latest.json · " + $r.last)
    }
    $env:VIA_NO_OPEN = $prev.OPEN
    $page = Join-Path $VIA "VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.html"
    if (-not $fresh) {
        Write-Host ("  [頁] 本輪沒寫出新的總覽(看上面紅字)→ 不開舊頁,免得把上一輪當成這一輪(PR #529 Codex P2):" + $page) -ForegroundColor Yellow
    } elseif (-not $NoOpen) { [void](Open-VIAOwnPage -Page $page -CallerNoOpen $prev.OPEN) } else { Write-Host ("  [頁] " + $page) -ForegroundColor Cyan }
}
$script:mainDone = $false
$script:dbVerdict = $null
$script:mainError = $null
try {
    Invoke-VDFActivateMain
    $script:mainDone = $true
} catch {
    # 主體丟錯 = 紅(結束碼 1),不是中斷;Ctrl+C 不進 catch(PowerShell 停管線只跑 finally)
    $script:mainDone = $true
    $script:mainError = $_
    $script:exitCode = Merge-VDFExit $script:exitCode 1
    Add-VDFRow "!" "主體出錯" "RED" ([Math]::Round($clock.Elapsed.TotalSeconds, 1)) ("" + $_.Exception.Message)
} finally {
    if (-not $script:mainDone) {
        # v0105 ②:主體沒走完(Ctrl+C / 中途丟錯)= 中斷,不是綠
        $script:exitCode = 130
        Add-VDFRow "!" "中斷" "INTERRUPTED" ([Math]::Round($clock.Elapsed.TotalSeconds, 1)) "主體沒走完(Ctrl+C 或中途停止)· 上表之後的步驟沒跑"
    }
    if ($rows.Count -gt 0) {
        $shown = $false
        if (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue) {
            try { Write-CeleritasMatrixSummary -Rows $rows.ToArray() -Title ("VDF 獨立一鍵 · 結束碼 " + $script:exitCode); $shown = $true } catch { $shown = $false }
        }
        if (-not $shown) {
            Write-Host ("  ━━ VDF 獨立一鍵 · 結束碼 " + $script:exitCode + " ━━") -ForegroundColor Cyan
            foreach ($row in $rows) { Write-Host ("  " + $row.id.PadRight(10) + " " + $row.state.PadRight(11) + " " + ("" + $row.sec).PadLeft(8) + "s  " + $row.title + " · " + $row.note) }
        }
    }
    if ($script:dbVerdict -and $script:dbVerdict.counts) {
        if ($script:dbVerdict.closeout) { Write-Host ("  [收尾] 資料庫清點沒問題(VDF 自己的表 0 紅)→ 可收尾:把本段輸出貼回即可") -ForegroundColor Green }
        else { Write-Host ("  [收尾] 還不能:VDF 自己的表 紅 " + $script:dbVerdict.counts.RED + " 列 → 看自動跳出的總覽頁最上方「資料庫清點」(哪張表 · 寫入者 · 怎麼補)") -ForegroundColor Red }
    } elseif ($script:dbVerdict) { Write-Host ("  [收尾] 本輪沒清點到資料庫:" + $script:dbVerdict.why) -ForegroundColor Yellow }
    Write-Host ("  [計時] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $script:exitCode + "(0 綠 · 2 黃 · 1 紅 · 3 環境缺件 · 124 逾時 · 130 中斷)") -ForegroundColor Cyan
    $env:VIA_NO_OPEN = $prev.OPEN
    $env:VIA_FAMILY = $prev.FAMILY
    if ($VIABootShim -or $VIABootNote) { $env:VIA_ROOT = $VIABootPrev.ROOT; $env:PYTHONPATH = $VIABootPrev.PYTHONPATH }   # v0102 ② / v0103:本支動過的兩個環境變數還原
    if ($VIAActCelOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原(只還原本支自己套上的)
    Set-Location -LiteralPath $StartDir
}
if ($script:mainError) { Write-Host ("  [主體出錯] " + $script:mainError.Exception.Message + " · " + $script:mainError.InvocationInfo.PositionMessage) -ForegroundColor Red }
exit $script:exitCode
