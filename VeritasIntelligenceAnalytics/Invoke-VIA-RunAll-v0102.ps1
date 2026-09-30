# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-RunAll-v0102.ps1 — R17 一鍵:VCGC 流程閘 → 政策同步 → (同意閘)補資料三件 → 每日台股清單 → 全景實測 → 一包貼回
#   v0102(操作員 2026-09-28「成功的部份鎖住 後面的部分就邊測邊修 … VCGC VDF VRN 自動跳出多頁式矩陣式報告 BY RICH 字體小版面自動優化」):
#        ⑨ RED 節點診斷:讀 VRN 鏈 JSON,RED 的節點(最多 3 支)開 VIA_OCR_TRACE=1 各重跑一次自測,全文進 runall\diag\<節點>.log,
#           [FAIL] 行與尾行進貼回包(工作站才重現得了的紅,證據自動帶回來;-NoDiag 略過)
#        ⑩ 多頁矩陣:CGC_MDL231 MatrixPages 尾版產頁(總覽 · 鎖 · VCGC · VDF · VRN · DB · 橋與全景 · 工具 · 一鍵;rich · 小字 · 自動縮放),
#           鎖檢(對鎖冊 VIA_LampLock 尾版:回歸 / 守住 / 未量 / 可加鎖)進貼回包,跑完自動開頁(-NoOpen 不開)
#   v0101(操作員 2026-09-28「不對 每日台股清單 其他刪除」):拿掉 ⑦a 美日清單抓取;⑦ 只出每日台股清單(ENG231 v0102,讀庫不上網)。
#   操作員 2026-09-28:「把它們在一個 PS 指令中」(R17 的 sync-db · finstat --mops · cnnfg · fwdval · lists 兩句 · 全景實測)。
#   ① VCGC 流程閘(PSGATE-1):讀不到「[流程] 政策過」就停(exit 3),後面一步都不跑。
#   ② 政策同步 VRN_ENG082 sync-db(每本庫補 L14 四表;aaii 那本就是在這一步補上)。會寫你的庫 → 這支就是你的手。
#   ③ 網路同意閘:AI 永不代設(L07/L08)。只有兩種方式打開,而且**只在這一次執行、跑完就關回原樣**:
#        · 你在指令上自己加 -Consent;或
#        · 跑到這一步時問你一次,你親手打 YES。
#      沒開 = ④–⑥ 全部略過(照實標 GATED),其餘照跑。
#   ④ VDF_ENG082 財報 run --mops(tw_financial_mops)⑤ VDF_ENG229 CNN 恐懼貪婪全歷史 ⑥ VDF_ENG230 Forward PER
#   ⑦ VDF_ENG231 每日台股清單 lists(台股個股 + 主動式台股 ETF;不上網,閘沒開也跑)
#   ⑧ 全景實測(Invoke-VIA-Sweep 最新一版,報告 rich 矩陣照出)
#   最後:一張總表 + 一包貼回(本支各步 + 全景貼回包)放剪貼簿 → 回 Claude 對話框 Ctrl+V。
#   每步包 Invoke-VIACeleritasScoped(有就套;只動本行程、跑完還原);python 只經 Invoke-VIAPython。
# 用法(站在倉根):.\VIA-RunAll.ps1   參數:-Consent · -SkipSweep · -NoClipboard · -NoOpen · -NoDiag · -Days N(forward PER 天數,預設 400)
# 結束碼(exit 都在 try 裡,finally 照樣關閘、回夾):0 = 每步都跑完 · 2 = 有步沒跑完(尾版不在 / 崩潰)· 3 = 流程閘沒過
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Consent,
    [switch]$SkipSweep,
    [switch]$NoClipboard,
    [switch]$NoOpen,
    [switch]$NoDiag,
    [ValidateRange(30, 3000)][int]$Days = 400
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
    $cmd = "Invoke-VIAPython -Family " + (& $q $Family) + " " + (& $q $Script) + " " + ((@($ArgList) | ForEach-Object { & $q $_ }) -join " ") + " *>&1"   # 全串流:Invoke-VIAPython 把 stderr 用 Write-Host(資訊串流)重印,2>&1 收不到 Traceback(Codex #345)
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
Write-Host "  ║  VIA 一鍵 v0102 · 流程閘 → 補資料 → 全景 → 診斷 → 多頁矩陣 ║" -ForegroundColor Cyan
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
    Write-Host "  ③ 網路同意閘:④–⑥ 要上網抓資料(MOPS 財報 · CNN 恐懼貪婪 · FactSet/MSCI/S&P/日經)。" -ForegroundColor Cyan
    Write-Host "     AI 不代開。要開就親手打 YES(只這一次、跑完關回);直接 Enter = 不開,④–⑥ 略過。" -ForegroundColor Cyan
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
} else {
    foreach ($x in @(@("finstat_mops", "④ 交易所財報 --mops"), @("cnnfg", "⑤ CNN 恐懼貪婪"), @("fwdval", "⑥ Forward PER"))) {
        Add-RaSkipped $x[0] $x[1] "同意閘沒開 = GATED;要跑就加 -Consent 或提示時打 YES"
    }
}
# ⑦ 每日台股清單(讀 ENG087,不上網;閘沒開也照出)
$null = Invoke-RaStep "lists" "⑦ 每日台股清單 + 主動式 ETF(ENG231 lists)" "vdf" (Get-RaNewest $eng "VDF_ENG231_GlobalListings_v*.py") @("lists")

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

# ⑨ RED 節點診斷(工作站才重現得了的紅:開 trace 重跑一次,證據帶回來)
$diag = [System.Collections.Generic.List[object]]::new()
$chainJson = Join-Path $VIA "VIA_Reports\vrn_chain\VRNCHAIN_latest.json"
if (-not $SkipSweep -and -not $NoDiag -and (Test-Path -LiteralPath $chainJson)) {
    $reds = @()
    try { $reds = @((Get-Content -LiteralPath $chainJson -Raw -Encoding utf8 | ConvertFrom-Json).stages | Where-Object { $_.state -eq "RED" -and $_.evidence }) } catch { $reds = @() }
    $diagDir = Join-Path $outDir "diag"
    New-Item -ItemType Directory -Force -Path $diagDir | Out-Null
    $prevTrace = $env:VIA_OCR_TRACE
    try {
        $env:VIA_OCR_TRACE = "1"
        foreach ($n in @($reds | Select-Object -First 3)) {
            $p = Join-Path $VIA ("" + $n.evidence)
            if (-not (Test-Path -LiteralPath $p)) { continue }
            Write-Host ("  ▶ ⑨ 診斷 " + $n.name + "(VIA_OCR_TRACE=1 重跑自測;全文進 diag)") -ForegroundColor DarkGray
            $swd = [Diagnostics.Stopwatch]::StartNew()
            $global:LASTEXITCODE = 0
            $q = { param($v) "'" + (("" + $v) -replace "'", "''") + "'" }
            $body = [scriptblock]::Create("Push-Location -LiteralPath " + (& $q (Split-Path $p -Parent)) + "; try { Invoke-VIAPython -Family 'vrn' -TimeoutSec 900 " + (& $q $p) + " '--selftest' *>&1 } finally { Pop-Location }")   # 全串流(同上):診斷全文要含 stderr 的 Traceback
            $raw = if ($script:HasScoped) { Invoke-VIACeleritasScoped -Body $body } else { & $body }
            $drc = $global:LASTEXITCODE
            $dl = [System.Collections.Generic.List[string]]::new()
            foreach ($o in @($raw)) { $ln = $rxAnsi.Replace(("" + $o), ""); if (-not $rxProg.IsMatch($ln)) { $dl.Add($ln) } }
            $dlog = Join-Path $diagDir (("" + $n.name) + ".log")
            [IO.File]::WriteAllText($dlog, ($dl -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
            $fails = @($dl | Where-Object { $_ -match '\[FAIL\]|Traceback|Error:' } | Select-Object -First 8 | ForEach-Object { ("" + $_).Trim() })
            $tailL = @($dl | Where-Object { ("" + $_).Trim() } | Select-Object -Last 12 | ForEach-Object { ("" + $_).Trim() })
            $diag.Add([ordered]@{ name = "" + $n.name; state = "rc=" + $drc; rc = $drc; sec = [Math]::Round($swd.Elapsed.TotalSeconds, 1); log = $dlog; fail = $fails; tail = $tailL })
            Write-Host ("  ⑨ 診斷 " + $n.name + " · rc=" + $drc + " · " + $diag[$diag.Count - 1].sec + "s · " + $fails.Count + " 行 FAIL/錯誤") -ForegroundColor Yellow
            foreach ($t in $fails) { Write-Host ("      │ " + $t) -ForegroundColor DarkGray }
        }
    } finally {
        $env:VIA_OCR_TRACE = $prevTrace
    }
    $steps.Add([ordered]@{ id = "diag"; title = "⑨ RED 節點診斷"; rc = $null; sec = $null
                           state = $(if ($reds.Count -eq 0) { "無 RED" } else { "" + $diag.Count + " 支" }); tail = @($diag | ForEach-Object { $_.name + " rc=" + $_.rc }) })
} else {
    Add-RaSkipped "diag" "⑨ RED 節點診斷" $(if ($NoDiag) { "-NoDiag" } elseif ($SkipSweep) { "-SkipSweep" } else { "VRN 鏈 JSON 不在" })
}

# ⑩ 多頁矩陣(先把一鍵各步寫成 JSON,矩陣頁讀它)
$headLine = "" + (git -C $Repo log --oneline -1 2>$null)
$stepsJson = [ordered]@{ ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss"); head = $headLine; steps = @($steps); diag = @($diag) }
[IO.File]::WriteAllText((Join-Path $outDir "RUNALL_STEPS_latest.json"), ($stepsJson | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
$pagesHtml = $null
$lockLine = ""
$mx = Get-RaNewest $reg "CGC_MDL231_MatrixPages_v*.py"
$r10 = Invoke-RaStep "pages" "⑩ 多頁矩陣(鎖檢 · rich · 自動縮放)" "vrn" $mx @("pages")
foreach ($t in @($r10.tail)) {
    if ($t -match 'HTML\s+(.+\.html)\s*$') { $pagesHtml = $Matches[1].Trim() }
}
$lockLine = "" + (@(Get-Content -LiteralPath $logPath -Encoding utf8 | Where-Object { $_ -match '^\s*\[鎖\]' }) | Select-Object -Last 1)
# ⑩ 自己也要進「一鍵」頁(Codex #345):含 ⑩ 重寫步驟 JSON,再重畫一次(0.4s 級;不另記一步)
$stepsJson.steps = @($steps)
[IO.File]::WriteAllText((Join-Path $outDir "RUNALL_STEPS_latest.json"), ($stepsJson | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
if ($mx) {
    $q = { param($v) "'" + (("" + $v) -replace "'", "''") + "'" }
    $rb = [scriptblock]::Create("Invoke-VIAPython -Family 'vrn' " + (& $q $mx) + " 'pages' *>&1")
    $null = if ($script:HasScoped) { Invoke-VIACeleritasScoped -Body $rb } else { & $rb }
}
if ($pagesHtml -and -not $NoOpen -and [Environment]::UserInteractive -and (Test-Path -LiteralPath $pagesHtml)) {
    try { Invoke-Item -LiteralPath $pagesHtml; Write-Host ("  [多頁矩陣] 已開:" + $pagesHtml) -ForegroundColor Green } catch { Write-Host ("  [多頁矩陣] 開不起來(自己開):" + $pagesHtml) -ForegroundColor Yellow }
} elseif ($pagesHtml) {
    Write-Host ("  [多頁矩陣] " + $pagesHtml + "(-NoOpen 或非互動,不自動開)") -ForegroundColor DarkCyan
}

# 總表 + 一包貼回
Write-Host ""
Write-Host "  ━━ 一鍵總表 ━━" -ForegroundColor Cyan
$tbl = @($steps | ForEach-Object { [pscustomobject]@{ 步驟 = $_.title; 狀態 = $_.state; rc = $_.rc; 秒 = $_.sec } })
$tbl | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
$paste = [System.Collections.Generic.List[string]]::new()
$paste.Add("### VIA 一鍵貼回包 · Invoke-VIA-RunAll-v0102 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " · HEAD " + ("" + (git -C $Repo log --oneline -1 2>$null)))
foreach ($s in $steps) {
    $paste.Add(("  {0,-44} {1,-12} rc {2,-4} {3}s" -f $s.title, $s.state, $s.rc, $s.sec))
    foreach ($t in @($s.tail)) { if ($t) { $paste.Add("      │ " + $t) } }
}
if ($lockLine) { $paste.Add(""); $paste.Add("鎖檢 " + $lockLine.Trim()) }
foreach ($d in $diag) {
    $paste.Add("")
    $paste.Add("診斷 " + $d.name + " · rc=" + $d.rc + " · 全文 " + $d.log)
    foreach ($t in @($d.fail) + @("──") + @($d.tail)) { if ($t) { $paste.Add("      │ " + $t) } }
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
