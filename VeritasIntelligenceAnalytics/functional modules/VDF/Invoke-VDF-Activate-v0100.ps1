# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VDF-Activate-v0100.ps1 — VDF 獨立一鍵:加速器 + 網路模組 + ActivateVDF(自測 → 真跑 → 總覽頁)
#   操作員 2026-10-18:「FIX ALL AND INTEGRATE ALL INTI A PS CODE WITH ACCELERATORS AND NETWORK MODULES.」
#   = L70 這一次的許可:只新增這一支(新檔;不動任何舊 .ps1)。許可冊 VIA_ModuleChange_Permits_v0100.json P019。
#   VDF 自己的入口(L120 三系統獨立):只跑 VDF 的 ActivateVDF.py;不經 VCGC / VRN、不載入他系統程式。
#   步驟(每步一列,最後印 MATRIX SUMMARY):
#     ① 加速器 · PS 端  [VIA:PS-TEMPLATE] Celeritas PS7 模板(只動本行程 · 關閉即還原)+ [VIA:PS-ACCEL] 25 格加速器橋
#     ② 加速器 · Py 端  SUP_MDL737_SuperAccelModule 尾版 --selftest(鎖版導向 VeritasCeleritas)
#     ③ 網路模組        via_net_unified 尾版 --selftest(→ SUP_MDL740_NetUnified → VeritasAegisNexus 鎖版;離線,不觸網)
#     ④ 同意閘          只讀不寫:VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手;沒開 = 照跑,擷取段照實 GATED
#     ⑤ ActivateVDF 自測(紅 = 停,不真跑)
#     ⑥ ActivateVDF 真跑(CPU/DRAM → 兩張清單 → 三條流程並行 → U/I;心跳照印;Ctrl+C 子行程樹收乾淨照寫總覽)
#     ⑦ 跳出總覽頁 VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.html(Open-VIAOwnPage;子行程照吃 VIA_NO_OPEN=1)
# 用法(熱 PS 直接貼;站在倉內任何資料夾):
#   & (Get-ChildItem (Join-Path (git rev-parse --show-toplevel) 'VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VDF-Activate-v*.ps1') | Sort-Object Name | Select-Object -Last 1).FullName -FetchHome <VDF 夾> -RefillApply
#   參數 [-Action run|selftest|preflight] [-FetchHome <夾>] [-DbHome <夾>(預設 <FetchHome>\output_hub)] [-RefillApply]
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

$VIA = if ($SystemDir) { $SystemDir } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$StartDir = (Get-Location).Path
$prev = @{ OPEN = $env:VIA_NO_OPEN; FAMILY = $env:VIA_FAMILY }
$script:exitCode = 0
$rows = [System.Collections.Generic.List[object]]::new()
function Add-VDFRow { param($Id, $Title, $State, $Sec, $Note) $rows.Add([pscustomobject]@{ id = "" + $Id; title = $Title; state = $State; sec = "" + $Sec; note = $Note }) }
function Get-VDFLamp { param([int]$Rc) switch ($Rc) { 0 { "GREEN" } 2 { "YELLOW" } 3 { "YELLOW" } 4 { "GATED" } 124 { "TIMEOUT" } 130 { "INTERRUPTED" } default { "RED" } } }
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
    Write-Host "  ║  VDF 獨立一鍵 v0100 · 加速器 + 網路模組 + ActivateVDF(自測 → 真跑) ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ("  [python] " + $py.exe + " · " + $py.how) -ForegroundColor DarkGray

    # ① 加速器 · PS 端
    $cel = $null
    if (Get-Command Get-CeleritasStatus -ErrorAction SilentlyContinue) { try { $cel = Get-CeleritasStatus } catch { $cel = $null } }
    $accelPs = [bool](Get-Command Show-VIAAccel20 -ErrorAction SilentlyContinue) -or [bool]$env:VIA_ACCEL_LIT
    if ($cel) {
        $note = "Celeritas PS7 " + $cel.Version + " · 執行緒 " + $cel.Workers + " / " + $cel.Cores + " 核 · 優先權 " + $cel.Priority + $(if ($VIAActCelOwn) { " · 本支套上,跑完還原" } else { " · 沿用本視窗已套的模板" }) + $(if ($accelPs) { " · PS 加速器橋在" } else { " · PS 加速器橋缺" })
        Write-Host ("  [①加速器·PS] " + $note) -ForegroundColor DarkCyan
        Add-VDFRow 1 "加速器 · PS 端" $(if ($accelPs) { "GREEN" } else { "YELLOW" }) "0" $note
    } else {
        Write-Host "  [①加速器·PS] Celeritas PS7 模板沒接上(supportive modules\ps7\VeritasCeleritas.PS7.ps1 不在,或不是 PowerShell 7)· 照跑,不加速" -ForegroundColor Yellow
        Add-VDFRow 1 "加速器 · PS 端" "YELLOW" "0" "Celeritas PS7 模板沒接上 · 照跑不加速"
    }

    $runPy = {
        param([string]$Title, [int]$TimeoutSec, [object[]]$PyArgs)
        $lines = [System.Collections.Generic.List[string]]::new()
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $body = {
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
        Add-VDFRow 2 ("加速器 · Py 端 " + $acc.BaseName) (Get-VDFLamp $r.rc) $r.sec $r.last
    } else {
        Add-VDFRow 2 "加速器 · Py 端" "YELLOW" "0" "SUP_MDL737_SuperAccelModule 尾版不在(ActivateVDF 的 ACCEL 橋缺席零影響)"
    }

    # ③ 網路模組
    $net = Get-VDFNewest -Dir $netDir -Stem "via_net_unified"
    if ($net) {
        Write-Host ("  [③網路模組] " + $net.Name + " --selftest(→ SUP_MDL740_NetUnified → VeritasAegisNexus;離線)") -ForegroundColor DarkCyan
        $r = & $runPy "網路模組" 300 @($net.FullName, "--selftest")
        $aeg = ($r.lines | Where-Object { $_ -match 'VeritasAegisNexus_v\d+' } | Select-Object -Last 1)
        Add-VDFRow 3 ("網路模組 " + $net.BaseName) (Get-VDFLamp $r.rc) $r.sec $(if ($aeg) { ("" + $aeg).Trim() } else { $r.last })
    } else {
        Add-VDFRow 3 "網路模組" "RED" "0" "supportive modules\network\via_net_unified_v*.py 不在(ActivateVDF 的擷取要它)"
    }

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
    if ($Action -eq 'preflight') { return }

    # ⑤ ActivateVDF 自測
    if (-not $SkipSelftest -or $Action -eq 'selftest') {
        Write-Host "  [⑤ActivateVDF 自測] ActivateVDF.py --selftest(本體尾版 + 前版鏈)" -ForegroundColor DarkCyan
        $r = & $runPy "ActivateVDF 自測" 1800 @($entry, "--selftest")
        $marks = @($r.lines | Where-Object { $_ -match '\[計\]' } | ForEach-Object { ($_ -replace '^\s*\[計\]\s*', '').Trim() })
        Add-VDFRow 5 "ActivateVDF 自測" (Get-VDFLamp $r.rc) $r.sec $(if ($marks.Count) { $marks -join ' ‖ ' } else { $r.last })
        if ($r.rc -ne 0) {
            Write-Host ("  [⑤ActivateVDF 自測] rc " + $r.rc + " → 不真跑(先修自測紅)") -ForegroundColor Red
            $script:exitCode = if ($r.rc -in 2, 3) { 2 } else { 1 }
            return
        }
    }
    if ($Action -eq 'selftest') { return }

    # ⑥ ActivateVDF 真跑
    $argList = @($entry, "run", "--no-open", "--mode", $Mode)
    if ($FetchHome) {
        $argList += @("--fetch-home", $FetchHome)
        if (-not $DbHome) { $DbHome = Join-Path $FetchHome "output_hub" }
    }
    if ($DbHome) { $argList += @("--db-home", $DbHome) }
    if ($Flows) { $argList += @("--flows", $Flows) }
    if ($RefillApply) { $argList += "--refill-apply" }
    if ($DryFetch) { $argList += "--dry" }
    Write-Host ("  [⑥ActivateVDF 真跑] " + (($argList | Select-Object -Skip 1) -join ' ') + " · 上限 " + $TimeoutHours + " 小時(Ctrl+C = 子行程樹收乾淨並照寫總覽)") -ForegroundColor DarkCyan
    $t0 = [DateTime]::UtcNow
    $r = & $runPy "ActivateVDF 真跑" ([Math]::Max(1, $TimeoutHours) * 3600) $argList
    $script:exitCode = if ($r.rc -in 0, 1, 2, 124, 130) { $r.rc } else { 1 }
    $json = Join-Path $VIA "VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.json"
    if ((Test-Path -LiteralPath $json) -and ((Get-Item -LiteralPath $json).LastWriteTimeUtc -ge $t0.AddSeconds(-2))) {
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
            Add-VDFRow 6 ("ActivateVDF 總燈 · " + $card.tag) ("" + $card.lamp) $r.sec $(if ($card.interrupted) { "已中斷(Ctrl+C)· 總覽照寫" } else { "總覽 " + $json })
        } catch {
            Add-VDFRow 6 "ActivateVDF 真跑" (Get-VDFLamp $r.rc) $r.sec ("總覽 JSON 讀不了:" + $_.Exception.Message)
        }
    } else {
        Add-VDFRow 6 "ActivateVDF 真跑" (Get-VDFLamp $r.rc) $r.sec ("本輪沒寫出 ACTIVATE_VDF_latest.json · " + $r.last)
    }
    $env:VIA_NO_OPEN = $prev.OPEN
    $page = Join-Path $VIA "VIA_Reports\vdf\activate\ACTIVATE_VDF_latest.html"
    if (-not $NoOpen) { [void](Open-VIAOwnPage -Page $page -CallerNoOpen $prev.OPEN) } else { Write-Host ("  [頁] " + $page) -ForegroundColor Cyan }
}
try {
    Invoke-VDFActivateMain
} finally {
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
    Write-Host ("  [計時] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $script:exitCode + "(0 綠 · 2 黃 · 1 紅 · 3 環境缺件 · 124 逾時 · 130 中斷)") -ForegroundColor Cyan
    $env:VIA_NO_OPEN = $prev.OPEN
    $env:VIA_FAMILY = $prev.FAMILY
    if ($VIAActCelOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原(只還原本支自己套上的)
    Set-Location -LiteralPath $StartDir
}
exit $script:exitCode
