# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0268.ps1 — 側線 2026-10-02:+via-vdfeng(別名 VDF單引擎)· +via-vrneng(別名 VRN單引擎)· +via-engines(別名 引擎冊)。
#   操作員令「提供 VCGC-VDF 所有引擎獨立啟動短指令 · VCGC-VRN 獨立啟動引擎短指令 … 下放到 SYSTEM MANAGER 掌握各引擎啟動器 …
#   確定好可以進行單引擎啟動」= L70 這一次的許可:只加這三件;v0267 以前一字不動。
#   via-vdfeng list                    VDF 引擎冊(VDF_SystemManager v0123 engine list;頁 VIA_Reports\tooling\ENGINES_VDF_latest.html)
#   via-vdfeng check <引擎>             啟動前閘(紅 = 讀不過 / 沒有入口 / 缺 L103 加速器或網路工具橋)
#   via-vdfeng <引擎> [子令 / 旗標 …]   ① 管理員啟動前閘 → 紅就停 → ② via-vcgc run --family vdf <引擎家族> [子令 / 旗標](每步包 Invoke-VIACeleritasScoped)
#   via-vrneng …                       同上,VRN(VRN_SystemManager v0114;--family vrn)
#   <引擎> = 229 · ENG229 · MDL002 · 全名 · 名稱片段;同號異名照實列候選,不猜。例:via-vdfeng 229 status · via-vdfeng ENG229 --selftest
#   via-engines                        兩冊一起列(VDF + VRN)
#   觸網的引擎要你在自己的視窗開 VIA_NET_CONSENT(AI 永不代設;沒開 = 引擎照實 DENY)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0267.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:Invoke-VIAEngineGate {
    param([string]$Sub, [object[]]$Rest)
    $fam = $Sub.ToLower()
    $mgr = if ($fam -eq 'vdf') { 'VDF_SystemManager' } else { 'VRN_SystemManager' }
    $tag = "via-" + $fam + "eng"
    $a = @(ConvertTo-VIACleanArgs $Rest)
    if ($a.Count -eq 0 -or ("" + $a[0]) -in @('list', 'ls', 'check', 'card')) {
        if ($a.Count -eq 0) { $a = @('list') }
        via-vcgc run --family $fam $mgr engine @a
        return
    }
    $key = "" + $a[0]
    $tail = @($a | Select-Object -Skip 1)
    $vc = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    $py = Get-VIAEnvPython $fam
    if (-not $py) { $py = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source }
    if (-not $vc -or -not $py) { Write-Host ("  [" + $tag + "] 缺 " + $(if (-not $vc) { 'VCGC 主控台' } else { 'python' })) -ForegroundColor Red; $global:LASTEXITCODE = 3; return }

    # ① 管理員啟動前閘(經 VCGC;只讀)
    $keep = $env:VIA_FROM_VCGC; $env:VIA_FROM_VCGC = 'YES'
    try { $out = @(& $py -X utf8 $vc run --family $fam $mgr engine check $key --json 2>&1 | ForEach-Object { '' + $_ }) }
    finally { $env:VIA_FROM_VCGC = $keep }
    $line = $out | Where-Object { $_ -like '{"engine_gate"*' } | Select-Object -Last 1
    if (-not $line) {
        Write-Host ("  [" + $tag + "] 啟動前閘沒有回判決行(看下面最後幾行)") -ForegroundColor Red
        $out | Select-Object -Last 8 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        $global:LASTEXITCODE = 3; return
    }
    $g = ($line | ConvertFrom-Json).engine_gate
    if ($g.lamp -in @('NODATA', 'AMBIGUOUS')) {
        Write-Host ("  [" + $tag + "] " + $(if ($g.lamp -eq 'NODATA') { '找不到引擎:' } else { '同號異名 / 片段命中多支,請給全名:' }) + $key) -ForegroundColor Yellow
        foreach ($c in @($g.candidates)) { Write-Host ("     · " + $c.eid + " " + $c.family + "  (" + $c.path + ")") -ForegroundColor DarkYellow }
        $global:LASTEXITCODE = 3; return
    }
    $color = switch ($g.lamp) { 'GREEN' { 'Green' } 'YELLOW' { 'Yellow' } 'NA' { 'DarkYellow' } default { 'Red' } }
    Write-Host ("  [" + $tag + " 啟動前閘] " + $g.lamp + " · " + $g.eid + " " + $g.family + " " + $g.version + " · 編號 " + $g.code) -ForegroundColor $color
    foreach ($b in @($g.block)) { Write-Host ("     [擋] " + $b) -ForegroundColor Red }
    foreach ($w in @($g.warn)) { Write-Host ("     [黃] " + $w) -ForegroundColor DarkYellow }
    if ($g.lamp -eq 'RED') { Write-Host ("  [" + $tag + "] 啟動前閘紅:不啟動(先照上面 [擋] 修)") -ForegroundColor Red; $global:LASTEXITCODE = 1; return }
    if ($g.lamp -eq 'NA') { Write-Host ("  [" + $tag + "] 這支是程式庫,不單獨啟動") -ForegroundColor DarkYellow; $global:LASTEXITCODE = 2; return }

    # ② 經 VCGC 啟動這一支引擎(Celeritas 範圍包住;只動本行程)
    Write-Host ("  [" + $tag + "] 啟動 → via-vcgc run --family " + $fam + " " + $g.family + " " + ($tail -join ' ')) -ForegroundColor Cyan
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) {
        Invoke-VIACeleritasScoped { via-vcgc run --family $fam $g.family @tail }
    } else {
        via-vcgc run --family $fam $g.family @tail
    }
}
function global:via-vdfeng { Invoke-VIAEngineGate 'vdf' $args }
function global:via-vrneng { Invoke-VIAEngineGate 'vrn' $args }
function global:via-engines {
    Invoke-VIAEngineGate 'vdf' @('list')
    Invoke-VIAEngineGate 'vrn' @('list')
}
Set-Alias -Name VDF單引擎 -Value via-vdfeng -Scope Global -Force
Set-Alias -Name VRN單引擎 -Value via-vrneng -Scope Global -Force
Set-Alias -Name 引擎冊 -Value via-engines -Scope Global -Force
