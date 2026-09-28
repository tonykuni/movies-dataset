# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-Sweep-v0101.ps1 — VCGC 全景實測一鍵 · 加速器模板 + rich 詳細摘要矩陣(政策附冊 PSGATE-1)
#   v0100 留作版史(L04)。操作員 2026-09-28:「ps 加速指令模板及 detailed summary matrix summary by rich 把它加上」
#   「一定要從 vcgc 跑過流程才可生成 ps 指令」。v0101:
#     ⓐ 流程閘:第一步 VCGC 入口 status;沒讀到「[流程] 政策過」就停在這裡,後面各步一律不跑(exit 3),報告照樣畫(總判 RED)。
#     ⓑ PS 加速模板:點源 Celeritas;每一步包在 Invoke-VIACeleritasScoped(VCGC 流程指定的 PS 加速;只動本行程、跑完就還原);
#        沒有這個助手(沒載短令冊)就照實說並直接跑。Celeritas 函式:Get-CeleritasRegex(流程閘與進度協定)、
#        Read/Write-CeleritasText(側車)、Get-CeleritasStatus(報告 ②)、Write-CeleritasReport(加速器頁)、finally Restore。
#     ⓒ rich 詳細摘要矩陣:CGC_MDL229 SweepReport 十張矩陣(總判 KPI · 加速器 · VCGC 燈 · 流程 · DB · VDF 鏈 · VRN 鏈 · 橋 · 全景 · 待辦),
#        rich 缺 = 純文字同十張;存 HTML / TXT;貼回包放剪貼簿。
#   其餘照 v0100:② VDF 鏈 run --resume · ③ VRN 鏈 run --resume · ④ 橋掃乾跑 · ⑤ 全景 · ⑥ DB 面板。只量不修;不代開網路同意閘。
# 用法(站在倉根):.\VIA-Sweep.ps1        參數:-SkipChains · -SkipPanel · -NoClipboard · -PlainReport · -Rows N
# 結束碼:0 = 跑完 · 3 = 流程閘沒過或沒跑起來(看 log 與報告)
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$SkipChains,
    [switch]$SkipPanel,
    [switch]$NoClipboard,
    [switch]$PlainReport,
    [ValidateRange(5, 500)][int]$Rows = 25
)

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$StartDir = (Get-Location).Path
Set-Location -LiteralPath $VIA
$script:VIAAccelPairNote = "正主缺,略過"
try {
    $join = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $join) {
        . $join
        $script:VIAAccelPairNote = "套對 $($script:CeleritasPS7.Version) · 已套"
    }
} catch {
    $script:VIAAccelPairNote = "正主載入失敗,略過"
}
Write-Host ("  [加速器] " + $script:VIAAccelPairNote)
$env:VIA_FROM_VCGC = "YES"
$env:VIA_VCGC_PUSH = "NO"
$env:VIA_NO_OPEN = "1"
$env:GIT_EDITOR = "true"
$env:GIT_TERMINAL_PROMPT = "0"
$script:HasCel = [bool](Get-Command Get-CeleritasRegex -ErrorAction SilentlyContinue)
$script:HasScoped = [bool](Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue)

function Get-SwpNewest {
    param([string]$Dir, [string]$Pattern)
    $hit = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $hit) { return $null }
    return $hit.FullName
}

function Get-SwpRegex {
    param([string]$Pattern)
    if ($script:HasCel) { return (Get-CeleritasRegex -Pattern $Pattern) }
    return [regex]::new($Pattern)
}

function Write-SwpText {
    param([string]$Path, [string]$Text)
    if ($script:HasCel) { Write-CeleritasText -Path $Path -Text $Text; return }
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
    if (Test-Path -LiteralPath $pyMod) { . $pyMod }
}
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Host "  [實測] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
    Set-Location -LiteralPath $StartDir
    exit 3
}

$reg = Join-Path $VIA "supportive modules\registry"
$outDir = Join-Path $VIA "VIA_Reports\sweep"
$logDir = Join-Path $outDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir ("Sweep_" + $stamp + ".log")
$steps = [System.Collections.Generic.List[object]]::new()
$rxAnsi = Get-SwpRegex "`e\[[0-9;]*m"
$rxProg = Get-SwpRegex '^@@PROGRESS\|'
$rxFlow = Get-SwpRegex '\[流程\]\s*政策過'

function Invoke-SwpStep {
    # 一步:包在 Invoke-VIACeleritasScoped(有就套)裡跑 Invoke-VIAPython;全文進 log;記進側車
    param([string]$Id, [string]$Title, [string]$Family, [string]$Script, [string[]]$ArgList, [switch]$Show)
    $rec = [ordered]@{ id = $Id; title = $Title; rc = $null; sec = $null; started_utc = [DateTime]::UtcNow.ToString("yyyy-MM-dd HH:mm:ss"); missing = $false; lines = @() }
    if (-not $Script) {
        $rec.missing = $true
        $steps.Add($rec)
        Write-Host ("  " + $Title + " · ABSENT(尾版不在)") -ForegroundColor Red
        return $rec
    }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $global:LASTEXITCODE = 0
    # 參數寫成字面值嵌進指令塊(不用 GetNewClosure:閉包是另一個模組範圍,看不到本腳本點源的 Invoke-VIAPython)
    $q = { param($v) "'" + (("" + $v) -replace "'", "''") + "'" }
    $cmd = "Invoke-VIAPython -Family " + (& $q $Family) + " " + (& $q $Script) + " " + ((@($ArgList) | ForEach-Object { & $q $_ }) -join " ") + " 2>&1"
    $body = [scriptblock]::Create($cmd)
    $raw = if ($script:HasScoped) { Invoke-VIACeleritasScoped -Body $body } else { & $body }
    $rc = $global:LASTEXITCODE
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($o in @($raw)) {
        $ln = $rxAnsi.Replace(("" + $o), "")
        if ($rxProg.IsMatch($ln)) { continue }
        $lines.Add($ln)
        if ($Show) { Write-Host ("" + $o) }
    }
    $rec.rc = $rc
    $rec.sec = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
    $rec.lines = @($lines)
    Add-Content -LiteralPath $logPath -Value (@("===== " + $Title + " · rc=" + $rc + " =====") + @($lines)) -Encoding utf8
    $steps.Add($rec)
    if (-not $Show) { Write-Host ("  " + $Title + " · rc=" + $rc + " · " + $rec.sec + "s") -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Yellow" }) }
    return $rec
}

function Add-SwpSkipped {
    param([string]$Id, [string]$Title)
    $steps.Add([ordered]@{ id = $Id; title = $Title; skipped = $true; lines = @() })
    Write-Host ("  " + $Title + " · 略過") -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  VIA 全景實測 v0101 · VCGC 流程閘 · PS 加速模板 · rich 矩陣   ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ("  [模板] Invoke-VIACeleritasScoped " + $(if ($script:HasScoped) { "已套(每步只動本行程、跑完還原)" } else { "不在(沒載短令冊;照實直接跑)" })) -ForegroundColor DarkGray
Write-Host ("  [log]  " + $logPath) -ForegroundColor DarkGray
$head = ("" + (git -C $Repo log --oneline -1 2>$null))
$flow = [ordered]@{ ok = $false; line = "" }
$gateStop = $false

try {
    # ① VCGC 入口 = 流程閘(PSGATE-1)
    $console = Get-SwpNewest $reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    $s1 = Invoke-SwpStep "vcgc" "① VCGC 入口(流程閘)" "vrn" $console @("status")
    $hit = @($s1.lines | Where-Object { $rxFlow.IsMatch($_) } | Select-Object -First 1)
    if ($hit.Count -gt 0) {
        $flow.ok = $true
        $flow.line = ("" + $hit[0]).Trim()
        Write-Host ("  [流程閘] 過:" + $flow.line) -ForegroundColor Green
    } else {
        $gateStop = $true
        Write-Host "  [流程閘] 沒讀到「[流程] 政策過」→ 依 PSGATE-1 停在這裡,後面各步不跑(報告照畫,總判 RED)" -ForegroundColor Red
    }

    if (-not $gateStop) {
        if (-not $SkipChains) {
            $null = Invoke-SwpStep "vdf_chain" "② VDF 鏈 run --resume" "vdf" (Get-SwpNewest $reg "CGC_MDL170_VDFChainRunner_v*.py") @("run", "--resume")
            $null = Invoke-SwpStep "vrn_chain" "③ VRN 鏈 run --resume" "vrn" (Get-SwpNewest $reg "CGC_MDL172_VRNChainRunner_v*.py") @("run", "--resume")
        } else {
            Add-SwpSkipped "vdf_chain" "② VDF 鏈"
            Add-SwpSkipped "vrn_chain" "③ VRN 鏈"
        }
        $null = Invoke-SwpStep "bridge" "④ 橋掃(乾跑)" "vrn" (Get-SwpNewest $reg "CGC_MDL124_BridgeSweeper_v*.py") @("--subsystems")
        $null = Invoke-SwpStep "panorama" "⑤ 全景" "core" (Get-SwpNewest $reg "CGC_MDL158_VIAPanoramaAuditRepair_v*.py") @("scan")
        if (-not $SkipPanel) {
            $panel = Get-SwpNewest $VIA "Invoke-VIA-DBPanel-v*.ps1"
            $rec6 = [ordered]@{ id = "db_panel"; title = "⑥ DB 面板"; rc = $null; sec = $null; started_utc = [DateTime]::UtcNow.ToString("yyyy-MM-dd HH:mm:ss"); missing = (-not $panel); lines = @() }
            if ($panel) {
                $sw6 = [Diagnostics.Stopwatch]::StartNew()
                $out6 = @(& $panel -NoPull -NoClipboard -Rows $Rows 2>&1 | ForEach-Object { $rxAnsi.Replace(("" + $_), "") })
                $rec6.rc = $LASTEXITCODE
                $rec6.sec = [Math]::Round($sw6.Elapsed.TotalSeconds, 1)
                Add-Content -LiteralPath $logPath -Value (@("===== ⑥ DB 面板 · rc=" + $rec6.rc + " =====") + $out6) -Encoding utf8
            }
            $steps.Add($rec6)
        } else {
            Add-SwpSkipped "db_panel" "⑥ DB 面板"
        }
    }

    # 側車 → rich 詳細摘要矩陣(CGC_MDL229)
    $accel = [ordered]@{ "加速器" = $script:VIAAccelPairNote; "模板助手" = $(if ($script:HasScoped) { "Invoke-VIACeleritasScoped 已套(每步)" } else { "Invoke-VIACeleritasScoped 不在(沒載短令冊)" }) }
    if (Get-Command Get-CeleritasStatus -ErrorAction SilentlyContinue) {
        try { $st = Get-CeleritasStatus; foreach ($k in $st.Keys) { $accel[$k] = "" + $st[$k] } } catch { $accel["狀態"] = "讀不到:" + $_.Exception.Message }
    }
    $accel["PowerShell"] = "" + $PSVersionTable.PSVersion
    $sidePath = Join-Path $outDir "SWEEP_SIDE_latest.json"
    $side = [ordered]@{ schema = "VIA.Sweep.Side.v1"; script = (Split-Path $PSCommandPath -Leaf); ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                        head = $head; flow = $flow; accel = $accel; steps = @($steps) }
    Write-SwpText $sidePath ($side | ConvertTo-Json -Depth 6)
    $width = 160
    try { $width = [Math]::Max(100, [Math]::Min(220, $Host.UI.RawUI.WindowSize.Width - 2)) } catch { $width = 160 }
    $rargs = @("render", "--side", $sidePath, "--width", ("" + $width), "--rows", ("" + $Rows))
    if ($PlainReport) { $rargs += "--plain" }
    Write-Host ""
    $null = Invoke-SwpStep "report" "⑦ rich 詳細摘要矩陣" "vrn" (Get-SwpNewest $reg "CGC_MDL229_SweepReport_v*.py") $rargs -Show

    if (Get-Command Write-CeleritasReport -ErrorAction SilentlyContinue) {
        try { [void](Write-CeleritasReport -Path (Join-Path $outDir "SWEEP_ACCEL_latest.html")) } catch { }
    }
} finally {
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
}

$pastePath = Join-Path $outDir "SWEEP_PASTE_latest.txt"
$clipOk = $false
if ((Test-Path -LiteralPath $pastePath) -and -not $NoClipboard -and (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
    try { Set-Clipboard -Value ([IO.File]::ReadAllText($pastePath)); $clipOk = $true } catch { $clipOk = $false }
}
Write-Host ""
Write-Host ("  [報告] " + (Join-Path $outDir "SWEEP_REPORT_latest.html")) -ForegroundColor DarkCyan
Write-Host ("  [貼回] " + $pastePath) -ForegroundColor DarkCyan
Write-Host ("  [log]  " + $logPath) -ForegroundColor DarkCyan
if ($clipOk) {
    Write-Host "  ✅ 實測貼回包已放進剪貼簿 → 回到 Claude 對話框按 Ctrl+V 送出。不要貼回 PowerShell。" -ForegroundColor Green
}
Set-Location -LiteralPath $StartDir
if ($gateStop) { exit 3 }
exit 0
