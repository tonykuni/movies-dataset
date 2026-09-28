# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-RunAll-v0100.ps1 — R17 一鍵:VCGC 流程閘 → 政策同步 → (同意閘)補資料四件 → 全景實測 → 一包貼回
#   操作員 2026-09-28:「把它們在一個 PS 指令中」(R17 的 sync-db · finstat --mops · cnnfg · fwdval · lists 兩句 · 全景實測)。
#   ① VCGC 流程閘(PSGATE-1):讀不到「[流程] 政策過」就停(exit 3),後面一步都不跑。
#   ② 政策同步 VRN_ENG082 sync-db(每本庫補 L14 四表;aaii 那本就是在這一步補上)。會寫你的庫 → 這支就是你的手。
#   ③ 網路同意閘:AI 永不代設(L07/L08)。只有兩種方式打開,而且**只在這一次執行、跑完就關回原樣**:
#        · 你在指令上自己加 -Consent;或
#        · 跑到這一步時問你一次,你親手打 YES。
#      沒開 = ④–⑦ 全部略過(照實標 GATED),其餘照跑。
#   ④ VDF_ENG082 財報 run --mops(tw_financial_mops)⑤ VDF_ENG229 CNN 恐懼貪婪全歷史 ⑥ VDF_ENG230 Forward PER
#   ⑦ VDF_ENG231 美日台總清單 run + lists
#   ⑧ 全景實測(Invoke-VIA-Sweep 最新一版,報告 rich 矩陣照出)
#   最後:一張總表 + 一包貼回(本支各步 + 全景貼回包)放剪貼簿 → 回 Claude 對話框 Ctrl+V。
#   每步包 Invoke-VIACeleritasScoped(有就套;只動本行程、跑完還原);python 只經 Invoke-VIAPython。
# 用法(站在倉根):.\VIA-RunAll.ps1   參數:-Consent · -SkipSweep · -NoClipboard · -Days N(forward PER 天數,預設 400)
# 結束碼(exit 都在 try 裡,finally 照樣關閘、回夾):0 = 每步都跑完 · 2 = 有步沒跑完(尾版不在 / 崩潰)· 3 = 流程閘沒過
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Consent,
    [switch]$SkipSweep,
    [switch]$NoClipboard,
    [ValidateRange(30, 3000)][int]$Days = 400
)

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$StartDir = (Get-Location).Path
$prevNet = $env:VIA_NET_CONSENT
$prevScrape = $env:VIA_SCRAPE_CONSENT
$exitCode = 0
try {
Set-Location -LiteralPath $VIA
$script:AccelNote = "正主缺,略過"
try {
    $tpl = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $tpl) { . $tpl; $script:AccelNote = "套對 $($script:CeleritasPS7.Version) · 已套" }
} catch { $script:AccelNote = "正主載入失敗,略過" }
Set-StrictMode -Off
Write-Host ("  [加速器] " + $script:AccelNote)
$env:VIA_FROM_VCGC = "YES"
$env:VIA_VCGC_PUSH = "NO"
$env:VIA_NO_OPEN = "1"
$script:HasScoped = [bool](Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue)

if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
    if (Test-Path -LiteralPath $pyMod) { . $pyMod }
}
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Host "  [一鍵] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
    exit 3
}

function Get-RaNewest {
    param([string]$Dir, [string]$Pattern)
    $hit = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $hit) { return $null }
    return $hit.FullName
}

$outDir = Join-Path $VIA "VIA_Reports\runall"
$logDir = Join-Path $outDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir ("RunAll_" + $stamp + ".log")
$steps = [System.Collections.Generic.List[object]]::new()
$rxAnsi = [regex]::new("`e\[[0-9;]*m")
$rxProg = [regex]::new('^@@PROGRESS\|')
$reg = Join-Path $VIA "supportive modules\registry"
$eng = Join-Path $VIA "functional modules\VDF\engine"

function Invoke-RaStep {
    param([string]$Id, [string]$Title, [string]$Family, [string]$Script, [string[]]$ArgList)
    $rec = [ordered]@{ id = $Id; title = $Title; rc = $null; sec = $null; state = ""; tail = @() }
    if (-not $Script) {
        $rec.state = "ABSENT"
        $steps.Add($rec)
        Write-Host ("  " + $Title + " · ABSENT(尾版不在;先 git pull)") -ForegroundColor Red
        return $rec
    }
    Write-Host ("  ▶ " + $Title + " 跑中…(長的步要幾分鐘,別按 Ctrl+C;全文進 log)") -ForegroundColor DarkGray
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $global:LASTEXITCODE = 0
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
    }
    $rec.rc = $rc
    $rec.sec = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
    $crash = [bool](@($lines | Where-Object { $_ -match 'Traceback \(most recent call last\)' }).Count)
    $rec.state = if ($crash) { "CRASH" } elseif ($rc -eq 0) { "OK" } elseif ($rc -eq 4) { "GATED/DENY" } else { "rc=" + $rc }
    $rec.tail = @($lines | Where-Object { ("" + $_).Trim() } | Select-Object -Last 3 | ForEach-Object { ("" + $_).Trim() })
    Add-Content -LiteralPath $logPath -Value (@("===== " + $Title + " · rc=" + $rc + " =====") + @($lines)) -Encoding utf8
    $steps.Add($rec)
    Write-Host ("  " + $Title + " · " + $rec.state + " · " + $rec.sec + "s") -ForegroundColor $(if ($rec.state -eq "OK") { "Green" } elseif ($rec.state -eq "CRASH") { "Red" } else { "Yellow" })
    foreach ($t in $rec.tail) { Write-Host ("      │ " + $t) -ForegroundColor DarkGray }
    return $rec
}

function Add-RaSkipped {
    param([string]$Id, [string]$Title, [string]$Why)
    $steps.Add([ordered]@{ id = $Id; title = $Title; rc = $null; sec = $null; state = "SKIP"; tail = @($Why) })
    Write-Host ("  " + $Title + " · 略過(" + $Why + ")") -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  VIA 一鍵 v0100 · 流程閘 → 政策同步 → 補資料 → 全景實測     ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ("  [log] " + $logPath) -ForegroundColor DarkGray

# ① VCGC 流程閘(PSGATE-1)
$s1 = Invoke-RaStep "vcgc" "① VCGC 流程閘" "vrn" (Get-RaNewest $reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py") @("status")
$logText = Get-Content -LiteralPath $logPath -Raw -Encoding utf8
if ($logText -notmatch '\[流程\]\s*政策過') {
    Write-Host "  [流程閘] 沒讀到「[流程] 政策過」→ 依 PSGATE-1 停在這裡,後面一步都不跑" -ForegroundColor Red
    exit 3
}
Write-Host "  [流程閘] 過:[流程] 政策過 · 子系統已對齊 · 才執行" -ForegroundColor Green

# ② 政策同步(每本庫補 L14 四表)
$null = Invoke-RaStep "policy_sync" "② 政策同步 sync-db(每本庫補 L14 四表)" "vrn" (Get-RaNewest (Join-Path $VIA "functional modules\VRN") "VRN_ENG082_ExtractionLogic_v*.py") @("sync-db")

# ③ 網路同意閘:只由你打開;只在這一次執行
$open = ($env:VIA_NET_CONSENT -eq "YES" -and $env:VIA_SCRAPE_CONSENT -eq "YES")
$how = if ($open) { "你的視窗本來就開著" } else { "" }
if (-not $open -and $Consent) { $open = $true; $how = "你在指令上加了 -Consent" }
if (-not $open -and [Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
    Write-Host ""
    Write-Host "  ③ 網路同意閘:④–⑦ 要上網抓資料(MOPS 財報 · CNN 恐懼貪婪 · FactSet/MSCI/S&P/日經 · NASDAQ/JPX 清單)。" -ForegroundColor Cyan
    Write-Host "     AI 不代開。要開就親手打 YES(只這一次、跑完關回);直接 Enter = 不開,④–⑦ 略過。" -ForegroundColor Cyan
    $ans = Read-Host "     開網路同意閘?"
    if (("" + $ans).Trim() -ceq "YES") { $open = $true; $how = "你親手打了 YES" }
}
if ($open) {
    $env:VIA_NET_CONSENT = "YES"
    $env:VIA_SCRAPE_CONSENT = "YES"
    Write-Host ("  [同意閘] 開(" + $how + ";只這一次執行,結束關回原樣)") -ForegroundColor Green
    $null = Invoke-RaStep "finstat_mops" "④ 交易所財報 run --mops(tw_financial_mops)" "vdf" (Get-RaNewest $eng "VDF_ENG082_FinStatements_v*.py") @("run", "--mops")
    $null = Invoke-RaStep "cnnfg" "⑤ CNN 恐懼貪婪全歷史(ENG229)" "vdf" (Get-RaNewest $eng "VDF_ENG229_CNNFearGreedHistory_v*.py") @("run")
    $null = Invoke-RaStep "fwdval" "⑥ Forward PER / EPS(ENG230)" "vdf" (Get-RaNewest $eng "VDF_ENG230_ForwardValuation_v*.py") @("run", "--days", ("" + $Days))
    $null = Invoke-RaStep "lists_run" "⑦a 美日清單抓取(ENG231 run)" "vdf" (Get-RaNewest $eng "VDF_ENG231_GlobalListings_v*.py") @("run")
} else {
    foreach ($x in @(@("finstat_mops", "④ 交易所財報 --mops"), @("cnnfg", "⑤ CNN 恐懼貪婪"), @("fwdval", "⑥ Forward PER"), @("lists_run", "⑦a 美日清單抓取"))) {
        Add-RaSkipped $x[0] $x[1] "同意閘沒開 = GATED;要跑就加 -Consent 或提示時打 YES"
    }
}
# ⑦b 總清單(讀庫 + ENG087,不上網;閘沒開也照出現有的)
$null = Invoke-RaStep "lists" "⑦b 美日台總清單 + 主動式 ETF(ENG231 lists)" "vdf" (Get-RaNewest $eng "VDF_ENG231_GlobalListings_v*.py") @("lists")

# ⑧ 全景實測(最新一版 Sweep;它自己再過一次流程閘,報告照出)
$sweepRc = $null
if (-not $SkipSweep) {
    $sweep = Get-RaNewest $VIA "Invoke-VIA-Sweep-v*.ps1"
    if ($sweep) {
        Write-Host ""
        Write-Host ("  ▶ ⑧ 全景實測 " + (Split-Path $sweep -Leaf) + " 跑中…(幾分鐘;報告會印在下面)") -ForegroundColor DarkGray
        $sw8 = [Diagnostics.Stopwatch]::StartNew()
        & $sweep -NoClipboard
        $sweepRc = $LASTEXITCODE
        $steps.Add([ordered]@{ id = "sweep"; title = "⑧ 全景實測"; rc = $sweepRc; sec = [Math]::Round($sw8.Elapsed.TotalSeconds, 1)
                               state = $(if ($sweepRc -eq 0) { "OK" } elseif ($sweepRc -eq 2) { "有步沒跑完" } else { "rc=" + $sweepRc }); tail = @() })
    } else {
        $steps.Add([ordered]@{ id = "sweep"; title = "⑧ 全景實測"; rc = $null; sec = $null; state = "ABSENT"; tail = @("Invoke-VIA-Sweep-v*.ps1 不在") })
    }
} else {
    Add-RaSkipped "sweep" "⑧ 全景實測" "-SkipSweep"
}

# 總表 + 一包貼回
Write-Host ""
Write-Host "  ━━ 一鍵總表 ━━" -ForegroundColor Cyan
$tbl = @($steps | ForEach-Object { [pscustomobject]@{ 步驟 = $_.title; 狀態 = $_.state; rc = $_.rc; 秒 = $_.sec } })
$tbl | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
$paste = [System.Collections.Generic.List[string]]::new()
$paste.Add("### VIA 一鍵貼回包 · Invoke-VIA-RunAll-v0100 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " · HEAD " + ("" + (git -C $Repo log --oneline -1 2>$null)))
foreach ($s in $steps) {
    $paste.Add(("  {0,-44} {1,-12} rc {2,-4} {3}s" -f $s.title, $s.state, $s.rc, $s.sec))
    foreach ($t in @($s.tail)) { if ($t) { $paste.Add("      │ " + $t) } }
}
$sweepPaste = Join-Path $VIA "VIA_Reports\sweep\SWEEP_PASTE_latest.txt"
if (-not $SkipSweep -and (Test-Path -LiteralPath $sweepPaste)) {
    $paste.Add("")
    $paste.AddRange([string[]]@(Get-Content -LiteralPath $sweepPaste -Encoding utf8))
}
$pastePath = Join-Path $outDir "RUNALL_PASTE_latest.txt"
[IO.File]::WriteAllText($pastePath, ($paste -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
$clipOk = $false
if (-not $NoClipboard -and (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
    try { Set-Clipboard -Value ([IO.File]::ReadAllText($pastePath)); $clipOk = $true } catch { $clipOk = $false }
}
Write-Host ("  [貼回] " + $pastePath) -ForegroundColor DarkCyan
Write-Host ("  [log]  " + $logPath) -ForegroundColor DarkCyan
if ($clipOk) { Write-Host "  ✅ 一鍵貼回包已放進剪貼簿 → 回到 Claude 對話框按 Ctrl+V 送出。不要貼回 PowerShell。" -ForegroundColor Green }
if (@($steps | Where-Object { $_.state -in @("ABSENT", "CRASH") }).Count -gt 0 -or ($null -ne $sweepRc -and $sweepRc -notin @(0))) { $exitCode = 2 }
exit $exitCode
} finally {
    # 同意閘關回原樣(本次執行才開的,結束就關)
    # PS7:指定 $null 即自本行程環境拿掉
    $env:VIA_NET_CONSENT = $prevNet
    $env:VIA_SCRAPE_CONSENT = $prevScrape
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
    Set-Location -LiteralPath $StartDir
}
