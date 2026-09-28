# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-Sweep-v0100.ps1 — VCGC 全景實測一鍵(操作員令 2026-09-28「照流程 · 全自動 · 最後要通過實測 · 邊測邊修 · 成功即鎖定」)
#   容器能修的已在 R16-1…5 修好並鎖定;真資料只在這台機器上,所以「實測」在這裡跑。本腳本只量不修:
#     ① VCGC 入口讀流程(status;推座關)——政策過 · 子系統已對齊 · 才往下
#     ② VDF 鏈跑器 run --resume(沒過的站重跑;要網路的站照實 GATED,AI 不代開同意閘)
#     ③ VRN 鏈跑器 run --resume(同上)
#     ④ 橋掃 --subsystems(乾跑;BridgeSweeper v0108 起不碰閘唯讀冊與版史檔)
#     ⑤ 全景掃描(治理七類;只報)
#     ⑥ DB 面板(Invoke-VIA-DBPanel 最新版;-NoPull -NoClipboard)
#   → 全部組成一份「實測貼回包」:寫 VIA_Reports\sweep\SWEEP_PASTE_latest.txt 並放進剪貼簿;回 Claude 對話框 Ctrl+V 一次即可。
# 紀律:python 只走 Invoke-VIAPython(缺 = 停);不裝套件、不寫庫(鏈跑器本身的寫入照它們各自的律)、不代開網路同意閘;
#   長輸出進 VIA_Reports\sweep\logs\;畫面只留每步一行。
# 用法(站在倉根):.\VIA-Sweep.ps1          或直接:& "<VIA 夾>\Invoke-VIA-Sweep-v0100.ps1"
#   -SkipChains     不跑兩條鏈(快)
#   -SkipPanel      不跑 DB 面板
#   -NoClipboard    不放剪貼簿(貼回檔照寫)
# 結束碼:0 = 跑完(各步燈號在貼回包裡)· 3 = 沒跑起來(看 log)
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$SkipChains,
    [switch]$SkipPanel,
    [switch]$NoClipboard
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

function Get-SwpNewest {
    param([string]$Dir, [string]$Pattern)
    $hit = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $hit) { return $null }
    return $hit.FullName
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
$bundle = [System.Collections.Generic.List[string]]::new()

function Invoke-SwpStep {
    # 跑一步:全文進 log;回 (行, rc, 秒)
    param([string]$Title, [string]$Family, [string]$Script, [string[]]$ArgList)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $lines = [System.Collections.Generic.List[string]]::new()
    $global:LASTEXITCODE = 0
    if (-not $Script) {
        Add-Content -LiteralPath $logPath -Value ("===== " + $Title + " · 尾版不在 =====") -Encoding utf8
        return [pscustomobject]@{ Lines = $lines; Rc = 3; Sec = 0.0; Missing = $true }
    }
    Invoke-VIAPython -Family $Family $Script @ArgList 2>&1 | ForEach-Object {
        $ln = ("" + $_) -replace "`e\[[0-9;]*m", ""
        if ($ln -notmatch '^@@PROGRESS\|') { $lines.Add($ln) }
    }
    $rc = $global:LASTEXITCODE
    Add-Content -LiteralPath $logPath -Value (@("===== " + $Title + " · rc=" + $rc + " =====") + @($lines)) -Encoding utf8
    return [pscustomobject]@{ Lines = $lines; Rc = $rc; Sec = [Math]::Round($sw.Elapsed.TotalSeconds, 1); Missing = $false }
}

function Add-SwpSection {
    # 把一步的重點行收進貼回包:標題 + 符合 $Keep 的行(最多 $Max 行)
    param([string]$Title, $Step, [string]$Keep, [int]$Max = 12)
    $bundle.Add("")
    $state = if ($Step.Missing) { "ABSENT" } else { "rc=" + $Step.Rc + " · " + $Step.Sec + "s" }
    $bundle.Add("## " + $Title + " · " + $state)
    $n = 0
    foreach ($ln in $Step.Lines) {
        if ($ln -match $Keep) {
            $bundle.Add(($ln.TrimEnd()).Substring(0, [Math]::Min(220, $ln.TrimEnd().Length)))
            $n++
            if ($n -ge $Max) { $bundle.Add("  …(全文在 log)"); break }
        }
    }
    $color = if ($Step.Missing) { "Red" } elseif ($Step.Rc -eq 0) { "Green" } else { "Yellow" }
    Write-Host ("  " + $Title + " · " + $state) -ForegroundColor $color
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  VIA 全景實測 v0100 · VCGC → 兩條鏈 → 橋 → 全景 → DB 面板     ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ("  [log] " + $logPath) -ForegroundColor DarkGray
$head = ("" + (git -C $Repo log --oneline -1 2>$null))
$bundle.Add("### VIA 全景實測貼回包 · Invoke-VIA-Sweep-v0100 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " · HEAD " + $head)

try {
    # ① VCGC 入口
    $console = Get-SwpNewest $reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    $s1 = Invoke-SwpStep "VCGC status" "vrn" $console @("status")
    Add-SwpSection "① VCGC 入口(政策 · 子系統)" $s1 '\[流程\]|\[衝突\] L|系統管理|SSOT 連動|資料庫:|多矩陣|\[政策\] 第二步' 14

    # ② ③ 兩條鏈
    if (-not $SkipChains) {
        $vdf = Get-SwpNewest $reg "CGC_MDL170_VDFChainRunner_v*.py"
        $s2 = Invoke-SwpStep "VDF 鏈" "vdf" $vdf @("run", "--resume")
        Add-SwpSection "② VDF 鏈跑器 run --resume" $s2 '^\s*\[(RED|GATED|NODATA|ABSENT)\s*\]|\[計\]' 14
        $vrn = Get-SwpNewest $reg "CGC_MDL172_VRNChainRunner_v*.py"
        $s3 = Invoke-SwpStep "VRN 鏈" "vrn" $vrn @("run", "--resume")
        Add-SwpSection "③ VRN 鏈跑器 run --resume" $s3 '\b(RED|ABSENT|GATED)\b|\[計\]' 16
    } else {
        $bundle.Add(""); $bundle.Add("## ②③ 兩條鏈 · 略過(-SkipChains)")
        Write-Host "  ②③ 兩條鏈 · 略過(-SkipChains)" -ForegroundColor DarkGray
    }

    # ④ 橋掃(乾跑)
    $bs = Get-SwpNewest $reg "CGC_MDL124_BridgeSweeper_v*.py"
    $s4 = Invoke-SwpStep "橋掃" "vrn" $bs @("--subsystems")
    Add-SwpSection "④ 橋掃 --subsystems(乾跑)" $s4 'PLAN|四系總表' 10

    # ⑤ 全景
    $pano = Get-SwpNewest $reg "CGC_MDL158_VIAPanoramaAuditRepair_v*.py"
    $s5 = Invoke-SwpStep "全景" "core" $pano @("scan")
    Add-SwpSection "⑤ 全景掃描(治理七類;只報)" $s5 '全景掃描|\[(報|修|免)\]' 10

    # ⑥ DB 面板
    if (-not $SkipPanel) {
        $panel = Get-SwpNewest $VIA "Invoke-VIA-DBPanel-v*.ps1"
        if ($panel) {
            $sw6 = [Diagnostics.Stopwatch]::StartNew()
            $out6 = @(& $panel -NoPull -NoClipboard 2>&1 | ForEach-Object { ("" + $_) -replace "`e\[[0-9;]*m", "" })
            $rc6 = $LASTEXITCODE
            Add-Content -LiteralPath $logPath -Value (@("===== DB 面板 · rc=" + $rc6 + " =====") + $out6) -Encoding utf8
            $bundle.Add(""); $bundle.Add("## ⑥ DB 面板 · rc=" + $rc6 + " · " + [Math]::Round($sw6.Elapsed.TotalSeconds, 1) + "s")
            $pp = Join-Path $VIA "VIA_Reports\dbmanager\DBM_PASTE_latest.txt"
            if (Test-Path -LiteralPath $pp) {
                $pl = @((Get-Content -LiteralPath $pp -Encoding utf8) | Select-Object -First 30)
                foreach ($ln in $pl) { $bundle.Add($ln) }
            }
            Write-Host ("  ⑥ DB 面板 · rc=" + $rc6) -ForegroundColor $(if ($rc6 -le 1) { "Green" } else { "Yellow" })
        }
    }
} finally {
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
}

$pastePath = Join-Path $outDir "SWEEP_PASTE_latest.txt"
[IO.File]::WriteAllText($pastePath, (($bundle -join "`n") + "`n"), [Text.UTF8Encoding]::new($false))
$clipOk = $false
if (-not $NoClipboard -and (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
    try { Set-Clipboard -Value ($bundle -join "`n"); $clipOk = $true } catch { $clipOk = $false }
}
Write-Host ""
Write-Host ("  [貼回包] " + $pastePath) -ForegroundColor DarkCyan
Write-Host ("  [log]    " + $logPath) -ForegroundColor DarkCyan
if ($clipOk) {
    Write-Host ("  ✅ 實測貼回包已放進剪貼簿(共 " + $bundle.Count + " 行)→ 回到 Claude 對話框按 Ctrl+V 送出。不要貼回 PowerShell。") -ForegroundColor Green
}
Set-Location -LiteralPath $StartDir
exit 0
