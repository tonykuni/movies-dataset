#Requires -Version 7.0
<#
    Invoke-VIA-AcceleratedTest v0103 — ALL-IN-ONE 全系統加速實測(批600)

    操作員令:「一個 ALL-IN-ONE PS CODE,加 25 的加速器,不卡斷,
               啟動實測全部系統生成輸出並驗證,指令前都要先進入環境」。

    v0102 → v0103 四個改法,每一個都對著上面那句話的一段:

      ① 25 的加速器  v0102 卡在 `if ($Roster.Count -ne 20) { throw }` ——**冊是 20 的那本**。
                     v0103 改點源 `VIA_PS_Accelerators_25_Roster_v0100.ps1`(25 項),
                     並把數量不符從 **throw 降成 WARN**:名冊不對是治理問題,
                     不是「今天不准跑實測」的理由。
      ② 不卡斷      v0102 是 `$ErrorActionPreference='Stop'` + 每一步 rc≠0 就 `throw`,
                     **第一盞紅就整條停**;而且 `while (-not $Process.HasExited)` 沒有死線,
                     引擎一掛就掛到天亮。v0103:每一步 try/catch + **逐步逾時**
                     (只殺自己生的那個子行程)+ 失敗照樣往下跑,最後一次把紅的全部列出來。
      ③ 全部系統    v0102 只跑 VDF/VRN 那幾支。v0103 補上全格自測、矩陣控制台、
                     全景稽核、U/I 統一閘、制度健全度——**跑完才叫實測全部系統**。
      ④ 生成輸出並驗證
                     v0102 的「通過」只看 rc。v0103 多一段 **VERIFY**:逐個產出檔比
                     **存在 + 是不是這一跑產的**(mtime ≥ 開跑時間)→ FRESH / STALE / MISSING。
                     **舊檔還在,不等於這一跑產出了東西**——那是假綠最常見的入口。

    指令前都要先進入環境:所有 python 一律走中央唯一入口 `Invoke-VIAPython -Family <fam>`
    (它自己帶 25 加速器控制面、動態進度條、逾時不卡斷);家族解譯器由 `Get-VIAEnvPython`
    解析。解析不到會退到 base `python`——v0103 **不 throw**,但把那一步標成 `ENV_FALLBACK`
    並在總表裡紅字提醒:**能跑 ≠ 在本位跑**。

    用法:
      pwsh -NoProfile -ExecutionPolicy Bypass -File .\launchers\Invoke-VIA-AcceleratedTest-v0103.ps1
      ... -ViaRoot <母資料夾>  -StationTimeout 900  -Only grid,matrix  -SkipHeavy
      ... -Families vdf,vrn
#>
param(
    [string]$ViaRoot = '',
    [ValidateRange(30, 86400)][int]$StationTimeout = 900,
    [string]$Only = '',
    [string]$Families = 'vdf,vrn',
    [switch]$SkipHeavy,
    [switch]$OpenPage
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

# 不卡斷律:全域不用 Stop。單步的錯自己接,接完往下走。
$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false
$RunStart = Get-Date

function Write-Line([string]$Text, [string]$Colour = 'Gray') { Write-Host $Text -ForegroundColor $Colour }

# ── 0 進母根 ───────────────────────────────────────────────────────────────
if (-not $ViaRoot) {
    $here = Split-Path -Parent $PSCommandPath
    $ViaRoot = Split-Path -Parent $here          # launchers\ 的上一層 = 母資料夾
}
if (-not (Test-Path -LiteralPath $ViaRoot -PathType Container)) {
    Write-Line "  [FAIL] 母資料夾不存在:$ViaRoot" 'Red'; exit 2
}
Set-Location -LiteralPath $ViaRoot
Write-Line "`n=== VIA ALL-IN-ONE 加速實測 v0103 ===" 'Cyan'
Write-Line "  母資料夾 : $ViaRoot"

# ── 1 指令冊(短令 + 中央 python 入口)─────────────────────────────────────
$Register = Get-ChildItem -LiteralPath $ViaRoot -Filter 'Register-VIA-Commands-v*.ps1' -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $Register) { Write-Line '  [FAIL] 指令註冊冊缺(Register-VIA-Commands-v*.ps1)' 'Red'; exit 2 }
. $Register.FullName
Set-Location -LiteralPath $ViaRoot
Write-Line "  指令冊   : $($Register.Name)"

if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Line '  [FAIL] 中央 python 入口 Invoke-VIAPython 不在;禁止繞過 VIA 直呼 python(fail-closed)' 'Red'
    exit 2
}

# ── 2 加速器 25 名冊 ───────────────────────────────────────────────────────
$Roster25 = Join-Path $ViaRoot 'supportive modules\registry\VIA_PS_Accelerators_25_Roster_v0100.ps1'
$AccelCount = 0
if (Test-Path -LiteralPath $Roster25) {
    . $Roster25
    if (Get-Variable -Name VIA_PS_ACCELERATORS_25 -Scope Global -ErrorAction SilentlyContinue) {
        $global:VIA_ACCEL25 = $global:VIA_PS_ACCELERATORS_25
    } elseif (Test-Path variable:VIA_PS_ACCELERATORS_25) {
        $global:VIA_ACCEL25 = $VIA_PS_ACCELERATORS_25
    }
    if ($global:VIA_ACCEL25) { $AccelCount = @($global:VIA_ACCEL25.Keys).Count }
}
if ($AccelCount -eq 25) {
    Write-Line "  加速器   : 25/25 已點亮(名冊 VIA_PS_Accelerators_25_Roster_v0100.ps1)" 'Green'
} else {
    # 名冊不對是治理問題,不是「今天不准跑實測」的理由 → WARN 不 throw
    Write-Line "  加速器   : **$AccelCount/25**(名冊對不上;實測照跑,這一條另案處理)" 'Yellow'
}

# ── 3 進環境(每一家族先解析本位解譯器)─────────────────────────────────
$FamList = @($Families.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
$PyOf = @{}
$EnvFallback = @()
foreach ($f in (@('core') + $FamList | Select-Object -Unique)) {
    $p = Get-VIAEnvPython $f
    $PyOf[$f] = $p
    if ($p -eq 'python' -or -not (Test-Path -LiteralPath $p -PathType Leaf)) {
        $EnvFallback += $f
        Write-Line "  環境 $f   : **base 退路**(家族境未見;能跑 ≠ 在本位跑)" 'Yellow'
    } else {
        Write-Line "  環境 $f   : $p" 'Green'
    }
}
if ($EnvFallback.Count) {
    Write-Line "  [提醒] 這些家族沒有本位環境:$($EnvFallback -join ',') → 建境:via-envgov apply --approve" 'Yellow'
}

# ── 4 這一跑的資料夾 ───────────────────────────────────────────────────────
$RunDir = Join-Path $ViaRoot ('VIA_Reports\accelerated_test\' + $RunStart.ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
Write-Line "  本跑存證 : $RunDir"

$Rows = [System.Collections.Generic.List[object]]::new()

function Get-Newest([string]$Folder, [string]$Pattern) {
    $d = Join-Path $ViaRoot $Folder
    if (-not (Test-Path -LiteralPath $d -PathType Container)) { return $null }
    $f = Get-ChildItem -LiteralPath $d -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($f) { return $f.FullName } else { return $null }
}

# ── 5 一步 = 一個子行程;逾時只殺自己生的那個;失敗照樣往下 ───────────────
function Invoke-Step {
    param(
        [string]$Name,
        [string]$Family,
        [string]$Folder,
        [string]$Pattern,
        [string[]]$Arguments = @(),
        [int]$TimeoutSec = 0
    )
    if ($Only) {
        $keys = @($Only.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
        if (-not ($keys | Where-Object { $Name.ToLower().Contains($_) })) { return }
    }
    $target = Get-Newest $Folder $Pattern
    if (-not $target) {
        Write-Line "`n=== $Name / $Family === ABSENT(找不到 $Pattern)" 'DarkYellow'
        $Rows.Add([pscustomobject]@{ Step = $Name; Family = $Family; State = 'ABSENT'; ExitCode = $null
                Seconds = 0; Why = "引擎缺:$Pattern"; Log = '' })
        return
    }
    $timeout = if ($TimeoutSec -gt 0) { $TimeoutSec } else { $StationTimeout }
    $py = $PyOf[$Family]; if (-not $py) { $py = Get-VIAEnvPython $Family; $PyOf[$Family] = $py }
    $log = Join-Path $RunDir ($Name + '.log')
    $timer = [Diagnostics.Stopwatch]::StartNew()
    Write-Line "`n=== $Name / $Family === (逾時 ${timeout}s)" 'Cyan'
    Write-Line "    引擎 $(Split-Path $target -Leaf) $($Arguments -join ' ')" 'DarkGray'

    $state = 'RED'; $code = $null; $why = ''
    try {
        $info = [System.Diagnostics.ProcessStartInfo]::new()
        $info.FileName = $py
        $info.WorkingDirectory = $ViaRoot
        $info.UseShellExecute = $false
        $info.RedirectStandardOutput = $true
        $info.RedirectStandardError = $true
        $info.Environment['PYTHONUTF8'] = '1'
        $info.Environment['PYTHONUNBUFFERED'] = '1'
        if (Test-Path -LiteralPath $py -PathType Leaf) {
            $info.Environment['PATH'] = (Split-Path $py -Parent) + ';' + $env:PATH
            $info.Environment['VIRTUAL_ENV'] = Split-Path (Split-Path $py -Parent) -Parent
        }
        foreach ($a in (@('-u', $target) + $Arguments)) { $info.ArgumentList.Add([string]$a) }
        $proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $info
        if (-not $proc.Start()) { throw '子行程啟動失敗' }
        $streams = @($proc.StandardOutput, $proc.StandardError)
        $tasks = @($streams[0].ReadLineAsync(), $streams[1].ReadLineAsync())
        $killed = $false
        while (-not $proc.HasExited -or $null -ne $tasks[0] -or $null -ne $tasks[1]) {
            for ($i = 0; $i -lt 2; $i++) {
                if ($null -ne $tasks[$i] -and $tasks[$i].IsCompleted) {
                    $line = $tasks[$i].GetAwaiter().GetResult()
                    if ($null -eq $line) { $tasks[$i] = $null }
                    else {
                        Write-Host $line
                        Add-Content -LiteralPath $log -Value $line -Encoding utf8
                        $tasks[$i] = $streams[$i].ReadLineAsync()
                    }
                }
            }
            # 不卡斷:過了死線就只殺自己生的那個子行程,別的步驟照跑
            if (-not $killed -and $timer.Elapsed.TotalSeconds -gt $timeout) {
                $killed = $true
                try { $proc.Kill($true) } catch { }
                Write-Line "    [TIMEOUT] 超過 ${timeout}s,殺掉本步子行程,繼續下一步" 'Red'
            }
            Write-Progress -Activity 'VIA ALL-IN-ONE 加速實測' `
                -Status ("$Name 已跑 {0:N0}s / 完成 {1} 步" -f $timer.Elapsed.TotalSeconds, $Rows.Count)
            Start-Sleep -Milliseconds 100
        }
        $code = $proc.ExitCode
        $proc.Dispose()
        if ($killed) { $state = 'TIMEOUT'; $why = "逾時 ${timeout}s" }
        else {
            # 誠實多態:0 綠 · 2 缺料 · 3 缺件 · 4 閘未開 · 其餘紅
            switch ($code) {
                0 { $state = 'GREEN' }
                2 { $state = 'NODATA'; $why = '引擎自述缺料(不是壞掉)' }
                3 { $state = 'ABSENT'; $why = '引擎自述缺件' }
                4 { $state = 'GATED'; $why = '同意閘未開(要跑=你開閘)' }
                default { $state = 'RED'; $why = "rc=$code" }
            }
        }
    } catch {
        $state = 'RED'; $why = $_.Exception.Message
        Write-Line "    [EXC] $why" 'Red'
    }
    if ($EnvFallback -contains $Family) { $why = ($why + ' · ENV_FALLBACK(非本位環境)').Trim(' ·') }
    $colour = switch ($state) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'TIMEOUT' { 'Red' } default { 'Yellow' } }
    Write-Line ("    → {0}  {1:N1}s  {2}" -f $state, $timer.Elapsed.TotalSeconds, $why) $colour
    $Rows.Add([pscustomobject]@{ Step = $Name; Family = $Family; State = $state; ExitCode = $code
            Seconds = [math]::Round($timer.Elapsed.TotalSeconds, 1); Why = $why; Log = $log })
    $Rows | Export-Csv (Join-Path $RunDir 'summary.csv') -NoTypeInformation -Encoding utf8BOM
}

# ── 6 實測全部系統 ─────────────────────────────────────────────────────────
$REG = 'supportive modules\registry'
Invoke-Step '01_Accel_Core'    'core' 'supportive modules'        'SUP_MDL737_SuperAccelModule_v*.py'        @('--selftest') 300
Invoke-Step '02_Net_Canon'     'vdf'  'supportive modules\network' 'SUP_MDL740_NetUnified_v*.py'             @('--selftest') 300
Invoke-Step '03_AccelControl'  'core' $REG 'CGC_MDL156_VIAAcceleratorControl_v*.py'                          @('--selftest') 600
Invoke-Step '04_EnvRunGate'    'vrn'  $REG 'CGC_MDL137_RunGate_v*.py'                @('run', '--fast', '--family', $Families) 900
Invoke-Step '05_RegistrySync'  'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('registry-sync', '--apply') 600
Invoke-Step '06_GovAudit'      'core' $REG 'CGC_MDL164_GovernanceCompletenessAudit_v*.py'                    @('--selftest') 900
Invoke-Step '07_UIUnifyGate'   'core' $REG 'CGC_MDL160_UIUnifyGate_v*.py'                                    @('--selftest') 900
Invoke-Step '08_PanoramaScan'  'core' $REG 'CGC_MDL158_VIAPanoramaAuditRepair_v*.py'          @('scan', '--json') 900
Invoke-Step '09_MatrixConsole' 'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('matrix', '--family', $Families) 3600
if (-not $SkipHeavy) {
    Invoke-Step '10_SelftestGrid' 'core' $REG 'CGC_MDL064_SelftestGrid_v*.py'                  @() 3600
}
Invoke-Step '11_Handover'      'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('page') 600
Invoke-Step '12_ApprovalCheck' 'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('check') 600
Write-Progress -Activity 'VIA ALL-IN-ONE 加速實測' -Completed

# ── 7 驗證:產出**存在**而且**是這一跑產的** ───────────────────────────────
# 舊檔還在不等於這一跑產出了東西——那是假綠最常見的入口。
$Expect = @(
    @{ Name = '矩陣控制台一頁'; Path = 'VIA_Reports\vcgc\VIA_UI_MatrixControl_v0100.html' },
    @{ Name = '一頁交接';       Path = 'VIA_Reports\vcgc\VIA_UI_CentralGovernanceConsole_v0100.html' },
    @{ Name = '加速器控制面';   Path = 'VIA_Reports\accelerator\VIA_ACCELERATOR_CONTROL_latest.json' },
    @{ Name = '全景稽核存證';   Path = 'VIA_Reports\panorama_audit'; Glob = '*.json' },
    @{ Name = '自測格存證';     Path = 'VIA_Reports\selftest_runs'; Glob = 'GRID_*.json' },
    @{ Name = '能跑閘存證';     Path = 'VIA_Reports\rungate'; Glob = '*.json' }
)
$Verify = [System.Collections.Generic.List[object]]::new()
foreach ($e in $Expect) {
    $full = Join-Path $ViaRoot $e.Path
    $item = $null
    if ($e.ContainsKey('Glob')) {
        if (Test-Path -LiteralPath $full -PathType Container) {
            $item = Get-ChildItem -LiteralPath $full -Filter $e.Glob -File -Recurse -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime | Select-Object -Last 1
        }
    } elseif (Test-Path -LiteralPath $full -PathType Leaf) {
        $item = Get-Item -LiteralPath $full
    }
    if (-not $item) {
        $st = 'MISSING'; $when = ''
    } elseif ($item.LastWriteTime -ge $RunStart) {
        $st = 'FRESH'; $when = $item.LastWriteTime.ToString('HH:mm:ss')
    } else {
        $st = 'STALE'; $when = $item.LastWriteTime.ToString('yyyy-MM-dd HH:mm')
    }
    $Verify.Add([pscustomobject]@{ 產出 = $e.Name; 狀態 = $st; 時間 = $when
            路徑 = $(if ($item) { $item.FullName } else { $full }) })
}
$Verify | Export-Csv (Join-Path $RunDir 'verify.csv') -NoTypeInformation -Encoding utf8BOM

# ── 8 總表 ─────────────────────────────────────────────────────────────────
$tally = @{}
foreach ($r in $Rows) { $tally[$r.State] = 1 + [int]$tally[$r.State] }
$bad = @($Rows | Where-Object { $_.State -in @('RED', 'TIMEOUT') })
Write-Line "`n=== 實測總表 ===" 'Cyan'
$Rows | Format-Table Step, Family, State, ExitCode, Seconds, Why -AutoSize | Out-Host
Write-Line "=== 產出驗證(FRESH=這一跑產的 · STALE=舊檔還在但這跑沒產 · MISSING=根本沒有)===" 'Cyan'
$Verify | Format-Table 產出, 狀態, 時間 -AutoSize | Out-Host

$verdict = if ($bad.Count) { 'RED' }
elseif (@($Verify | Where-Object { $_.狀態 -ne 'FRESH' }).Count) { 'YELLOW' }
elseif ($EnvFallback.Count -or $AccelCount -ne 25) { 'YELLOW' }
else { 'GREEN' }

[pscustomobject]@{
    verdict = $verdict; ts = $RunStart.ToString('s'); via_root = $ViaRoot
    accelerators = "$AccelCount/25"; env_fallback = $EnvFallback
    tally = $tally; steps = $Rows; verify = $Verify
} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $RunDir 'run.json') -Encoding utf8

$vc = switch ($verdict) { 'GREEN' { 'Green' } 'RED' { 'Red' } default { 'Yellow' } }
Write-Line ("[VIA ALL-IN-ONE] {0} · 步 {1} · {2} · 加速器 {3}/25 · 存證 {4}" -f `
        $verdict, $Rows.Count, (($tally.GetEnumerator() | ForEach-Object { "$($_.Key) $($_.Value)" }) -join ' · '), $AccelCount, $RunDir) $vc
if ($bad.Count) {
    Write-Line '  紅的逐個點名(不卡斷=跑完才講,不是跑一半就停):' 'Red'
    foreach ($b in $bad) { Write-Line ("   · {0} / {1} · {2} · 紀錄 {3}" -f $b.Step, $b.State, $b.Why, $b.Log) 'Red' }
}
if ($EnvFallback.Count) { Write-Line "  [黃] 家族境未見:$($EnvFallback -join ',')(能跑 ≠ 在本位跑)" 'Yellow' }
if ($OpenPage -and (Get-Command via-open -ErrorAction SilentlyContinue)) {
    via-open (Join-Path $ViaRoot 'VIA_Reports\vcgc\VIA_UI_MatrixControl_v0100.html')
}
# 誠實三態 rc:0 綠 · 1 紅 · 2 黃(黃不是綠)
exit $(switch ($verdict) { 'GREEN' { 0 } 'RED' { 1 } default { 2 } })
