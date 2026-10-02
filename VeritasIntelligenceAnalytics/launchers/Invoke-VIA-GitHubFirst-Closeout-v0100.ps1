# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-GitHubFirst-Closeout-v0100.ps1 — 以 GitHub 為主 · VCGC→VDF→VRN 既有架構 · 啟動 → 實測 → 收尾 → 輸出 → 輸出驗證 = 完工(側線 2026-09-30)
#   操作員令:「以 github 為主 在現有的 vcgc-vdf-vrn 架構下完成啟動實測收尾 output 輸出;輸出驗證檢查無誤算完工;若有缺乏才去本機找,避免混亂且無限擴張;integrate all into one powershell」
#   實錄根因(兩輪):① 工作站 main 與 origin 分岔(領先 19 · 落後 146)→ 尾版落後 → 動詞不認得;已由全景解掉。
#                 ② 同步後 enter --card 的 test --quick 仍紅:V-status rc 2 · run 動詞回 GATE missing ["policy_step"]—— 流程閘 CGC_MDL223 → 政策門 CGC_MDL207 → policy_step rc≠0;
#                    加上「註冊冊待同步 new 1」。本檔把「閘診斷 → 有界修復(registry-sync --apply)→ 重閘」做成一步,量到什麼寫什麼。
#   本檔 = 全景(GitHub 為主同步)+ 收尾鏈 合一,新檔(L70 不動舊 .ps1),接 Celeritas 殼;每段只呼既有正主 / git 原生:
#     ⓪ via-entry  ① GitHub 為主同步(fetch · 備份分支 · stash · merge origin:衝突一律 origin 勝,*.jsonl 聯集,本機版存旁證 · push)+ 尾版對照
#     ② 缺件補位(origin 沒有、本機才找:Downloads / VIA_CELERITAS_ROOT / 倉外副本 → 複製進 launchers,只增)
#     ③ 啟動 VCGC:token(門)· tools  ④ 閘診斷與有界修復:status → 門卡(CGC_MDL223 流程閘 · CGC_MDL207 政策門,唯讀印 missing)→ 待同步就 registry-sync --apply → 重閘(最多 2 輪)
#     ⑤ enter --card --no-pull(閘 · 加速器 · 工具版本 · test --quick)  ⑥ 實測整輪:唯一入口 OperatorConsole 尾版(-ApproveRegistrySync -NoBuild -NoUpload -NoOpen)
#     ⑦ 整合全景實測 FullCheck 尾版(-NoOpen)  ⑧ 收尾:handoff checkpoint · check · test · ledger · page · onepage
#     ⑨ 輸出驗證(這一輪產出的 TEST / PATH_VERIFY / FULLCHECK / HANDOFF_CHECK / HANDOFF / ENVMGR / SYNC / 鏈 各 latest:在不在 · 新不新 · 燈)→ 完工判定
#   每步只增寫 registry\VIA_VCGC_StepLock_Ledger_v0100.jsonl → git add 只收 registry · docs/handoff · launchers/新檔 → commit → push(被拒 ff-only 一次;不強推)。
#   VIA_Reports 整夾 .gitignore(倉規:不入 git、不弄髒工作樹),本檔的頁與 log 落 VIA_Reports\github_first\,只在本機。
#   界線:閘診斷只讀兩扇門的卡;修復只做 registry-sync --apply 與門自己會做的座位同步;其他缺件(政策節 · 家族尾版 · 法冊註記)= 亮紅列出原因位置,不擴張、不新造引擎。
#   不抓網路(只 git 對 origin)、不寫資料家、不裝件、不代設同意閘、不 Read-Host、不 rebase、不 force push、不刪分支或檔。
# 用法:pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VIA-GitHubFirst-Closeout-v0100.ps1 [-DryRun] [-Full] [-SkipSync]
#   環境:VIA_REPO_ROOT · VIA_CELERITAS_ROOT · VIA_GHF_NOOPEN=1 · VIA_GHF_NOPUSH=1(只 commit 不 push)
# =====================================================================================
param([switch]$DryRun, [switch]$Full, [switch]$SkipSync)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$__root = if ($PSScriptRoot) { $PSScriptRoot } else { $env:VIA_CELERITAS_ROOT }
$__self = $PSCommandPath
if ($DryRun) { $env:VIA_GHF_DRYRUN = "1" }
if ($Full) { $env:VIA_GHF_FULL = "1" }
if ($SkipSync) { $env:VIA_GHF_SKIPSYNC = "1" }
$env:VIA_CELERITAS_FINAL = "1"
$__joined = "shim"
foreach ($__cand in @(
        $env:VIA_CELERITAS_ROOT,
        (Join-Path (Join-Path $env:USERPROFILE "OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics") "supportive modules"),
        (Join-Path (Split-Path -Parent $__root) "supportive modules"),
        $__root)) {
    if (-not $__cand) { continue }
    $__ai = Join-Path $__cand "VeritasCeleritas.PS7.AutoImport.ps1"
    $__tp = Join-Path $__cand "VeritasCeleritas.PS7.Template.ps1"
    if (Test-Path -LiteralPath $__ai) { try { . $__ai; $__joined = "AutoImport " + $__cand; break } catch { } }
    if (Test-Path -LiteralPath $__tp) { try { . $__tp; $__joined = "Template " + $__cand; break } catch { } }
}
if (-not (Get-Command Invoke-CeleritasGenerated -ErrorAction SilentlyContinue)) {
    function Invoke-CeleritasGenerated { param([string]$Name, [scriptblock]$Body, [switch]$Final, [string]$FinalAction = "None", [int]$FinalDelay = 60); & $Body }
    $__joined = "shim(模塊不在;本輪照跑,Final 不接)"
}
Write-Host ("  [Celeritas] 接法:" + $__joined) -ForegroundColor DarkGray

$__body = {
    Set-StrictMode -Off
    $ErrorActionPreference = "Continue"
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
    $T0 = [Diagnostics.Stopwatch]::StartNew()
    $RunStart = Get-Date
    $RunId = "ghf-" + $RunStart.ToUniversalTime().ToString("yyyyMMdd-HHmmss")
    $Repo = if ($env:VIA_REPO_ROOT) { $env:VIA_REPO_ROOT } else { Join-Path $env:USERPROFILE "OneDrive\Documents\movies-dataset" }
    $VIA = Join-Path $Repo "VeritasIntelligenceAnalytics"
    $Reg = Join-Path $VIA "supportive modules\registry"
    $RptDir = Join-Path $VIA "VIA_Reports\github_first"
    $Ledger = Join-Path $Reg "VIA_VCGC_StepLock_Ledger_v0100.jsonl"
    $Dry = ($env:VIA_GHF_DRYRUN -eq "1"); $FullRun = ($env:VIA_GHF_FULL -eq "1"); $SkipSyncRun = ($env:VIA_GHF_SKIPSYNC -eq "1"); $NoPush = ($env:VIA_GHF_NOPUSH -eq "1")
    $StartDir = (Get-Location).Path
    $PrevEnv = @{ FROM = $env:VIA_FROM_VCGC; PUSH = $env:VIA_VCGC_PUSH; OPEN = $env:VIA_NO_OPEN; TO = $env:VIA_PY_TIMEOUT_SEC }
    $Mx = [ordered]@{ run = $RunId; ts_utc = $RunStart.ToUniversalTime().ToString("o"); repo = $Repo; dry = $Dry; sections = [ordered]@{} }
    $Rows = [System.Collections.Generic.List[object]]::new()
    $St = @{ Stop = $false; GateOk = $false }
    $VcgcTail = $null

    function Write-Lamp([string]$Text, [string]$Lamp) { $c = switch ($Lamp) { "GREEN" { "Green" } "YELLOW" { "Yellow" } "RED" { "Red" } default { "DarkGray" } }; Write-Host $Text -ForegroundColor $c }
    function Invoke-Git([string[]]$GitArgs) { $out = & git -C $Repo @GitArgs 2>&1; return @{ rc = $LASTEXITCODE; lines = @($out | ForEach-Object { "$_" }) } }
    function Get-GitLine([string[]]$GitArgs) { $r = Invoke-Git $GitArgs; if ($r.rc -eq 0 -and $r.lines.Count -gt 0) { return $r.lines[0].Trim() } else { return "" } }
    function Get-Head() { return (Get-GitLine @("rev-parse", "--short=12", "HEAD")) }
    function Write-NoBom([string]$Path, [string]$Text) { [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false)) }
    function Get-Sha16([string]$Text) { $sha = [System.Security.Cryptography.SHA256]::Create(); $h = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Text)); return (($h | ForEach-Object { $_.ToString("x2") }) -join "").Substring(0, 16) }
    function Get-NewestName([string[]]$Names) { if (-not $Names -or $Names.Count -eq 0) { return "" }; return (($Names | ForEach-Object { Split-Path $_ -Leaf }) | Sort-Object | Select-Object -Last 1) }
    function Get-Tail([string]$Dir, [string]$Filter) { $f = Get-ChildItem -LiteralPath $Dir -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; if ($f) { return $f.FullName } else { return "" } }
    # VCGC 動詞:經中央 Invoke-VIAPython;回 @{ rc; lines }(行同時印到畫面)
    function Invoke-Vcgc([string[]]$Argv) {
        $global:LASTEXITCODE = 0
        $ls = @(Invoke-VIAPython -Family "vrn" $VcgcTail @Argv | ForEach-Object { Write-Host $_; "$_" })
        return @{ rc = [int]$LASTEXITCODE; lines = $ls }
    }
    function Invoke-Door([string]$Filter) {
        # 唯讀門卡:門檔自己的 main() 印卡(VIA_FROM_VCGC=YES;不經 run,因為 run 正被這扇門擋著);只讀不寫
        $door = Get-Tail $Reg $Filter
        if (-not $door) { return @{ rc = 3; lines = @("門不在:" + $Filter); card = $null } }
        $global:LASTEXITCODE = 0
        $ls = @(Invoke-VIAPython -Family "vrn" $door | ForEach-Object { "$_" })
        $card = $null
        try { $j0 = [array]::IndexOf($ls, ($ls | Where-Object { $_.Trim() -eq "{" } | Select-Object -First 1)); if ($j0 -ge 0) { $card = (($ls | Select-Object -Skip $j0) -join "`n") | ConvertFrom-Json } } catch { }
        return @{ rc = [int]$LASTEXITCODE; lines = $ls; card = $card; door = (Split-Path $door -Leaf) }
    }

    # ---- 一步一鎖一推 ---------------------------------------------------------------------
    $CommitScope = @("VeritasIntelligenceAnalytics/supportive modules/registry", "VeritasIntelligenceAnalytics/docs/handoff", "VeritasIntelligenceAnalytics/launchers")
    function Lock-Step($Row) {
        $scope = @($CommitScope | Where-Object { Test-Path -LiteralPath (Join-Path $Repo $_) })
        $Row.head_before_lock = Get-Head
        $Row.changed = @((Invoke-Git (@("status", "--porcelain", "--") + $scope)).lines | Where-Object { $_.Trim() -ne "" }).Count
        $Row.sha16 = Get-Sha16 (ConvertTo-Json -InputObject $Row -Compress -Depth 4)
        [System.IO.File]::AppendAllText($Ledger, (ConvertTo-Json -InputObject $Row -Compress -Depth 4) + "`n", [System.Text.UTF8Encoding]::new($false))
        $Row.commit = ""; $Row.push = "skip"
        if ($Dry) { $Row.push = "dry"; Write-Host ("     [鎖] " + $Row.sha16 + " · DryRun 不 commit") -ForegroundColor DarkCyan; return }
        $changed2 = @((Invoke-Git (@("status", "--porcelain", "--") + $scope)).lines | Where-Object { $_.Trim() -ne "" })
        if ($changed2.Count -gt 0) {
            $null = Invoke-Git (@("add", "--") + $scope)
            $c = Invoke-Git @("commit", "-q", "-m", ("ghf " + $RunId + " step " + $Row.n + " " + $Row.id + " " + $Row.lamp + " (" + $Row.sha16 + ")"))
            if ($c.rc -eq 0) { $Row.commit = Get-Head } else { $Row.commit = "commit-fail"; $Row.push = "RED"; Write-Host ("     [鎖] commit 失敗:" + ($c.lines -join " | ")) -ForegroundColor Red }
        }
        if ($Row.commit -and $Row.commit -ne "commit-fail" -and -not $NoPush) {
            $p = Invoke-Git @("push", "-q", "origin", "HEAD")
            if ($p.rc -ne 0) { $null = Invoke-Git @("pull", "-q", "--ff-only"); $p = Invoke-Git @("push", "-q", "origin", "HEAD") }
            $Row.push = if ($p.rc -eq 0) { "GREEN" } else { "RED" }
            if ($p.rc -ne 0) { Write-Host ("     [推] push 未成功(不強推):" + (($p.lines | Select-Object -Last 2) -join " | ")) -ForegroundColor Yellow }
        } elseif ($Row.commit -and $NoPush) { $Row.push = "nopush" }
        Write-Host ("     [鎖] " + $Row.sha16 + " · " + $(if ($Row.commit) { "commit " + $Row.commit + " · push " + $Row.push } else { "無變更,不 commit" })) -ForegroundColor DarkCyan
    }
    function Invoke-Step([int]$N, [string]$Id, [string]$Name, [scriptblock]$Do, [int[]]$YellowRc = @(), [switch]$Gate, [switch]$NoLock) {
        if ($St.Stop) { $Rows.Add([ordered]@{ run = $RunId; n = $N; id = $Id; name = $Name; rc = -1; lamp = "SKIP"; sec = 0; note = "門紅,未跑" }); return }
        Write-Host ""; Write-Host ("  ── 步 " + $N + " · " + $Name + " (" + $Id + ")") -ForegroundColor Cyan
        $sw = [Diagnostics.Stopwatch]::StartNew(); $rc = 1; $note = ""
        try { $outp = @(& $Do); if ($outp.Count -eq 0) { $rc = 1; $note = "步沒回傳 rc" } else { $last = $outp[-1]; if ($last -is [hashtable]) { $rc = [int]$last.rc; $note = "" + $last.note } else { $rc = [int]$last } } } catch { $rc = 1; $note = ("" + $_.Exception.Message + " @" + $_.InvocationInfo.ScriptLineNumber) }
        $sw.Stop()
        $lamp = if ($rc -eq 0) { "GREEN" } elseif ($YellowRc -contains $rc) { "YELLOW" } else { "RED" }
        $row = [ordered]@{ run = $RunId; ts_utc = (Get-Date).ToUniversalTime().ToString("o"); n = $N; id = $Id; name = $Name; rc = $rc; lamp = $lamp; sec = [math]::Round($sw.Elapsed.TotalSeconds, 1); note = $note; head = (Get-Head) }
        Write-Lamp ("     → rc " + $rc + " · " + $lamp + " · " + $row.sec + " s" + $(if ($note) { " · " + $note } else { "" })) $lamp
        if ($NoLock) { $row.commit = ""; $row.push = "nolock" } else { Lock-Step $row }
        $Rows.Add($row)
        if ($Gate -and $lamp -eq "RED") { $St.Stop = $true; Write-Host "     門紅:實測 / 收尾不跑,直接到輸出驗證(照實)" -ForegroundColor Red }
    }

    # ---- 前置 ---------------------------------------------------------------------------
    if (-not (Test-Path -LiteralPath (Join-Path $Repo ".git")) -or -not (Test-Path -LiteralPath $Reg)) { Write-Host ("  [GitHub 為主] 倉根不對:" + $Repo + "(設 VIA_REPO_ROOT)") -ForegroundColor Red; $global:LASTEXITCODE = 3; return }
    New-Item -ItemType Directory -Force -Path $RptDir, (Join-Path $RptDir "conflicts"), (Join-Path $RptDir "logs") | Out-Null
    try { Start-Transcript -Path (Join-Path $RptDir ("logs\" + $RunId + ".log")) -Append | Out-Null } catch { }
    Set-Location -LiteralPath $VIA
    $env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"; $env:VIA_NO_OPEN = "1"
    $cap = 0; if ((-not [int]::TryParse(("" + $env:VIA_PY_TIMEOUT_SEC), [ref]$cap)) -or ($cap -gt 0 -and $cap -lt 7200)) { $env:VIA_PY_TIMEOUT_SEC = "7200" }
    $verdict = "RED"; $verdictText = "未起跑"; $exitCode = 0
    try {
        $regFile = Get-ChildItem -LiteralPath $VIA -Filter "Register-VIA-Commands-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
        if ($regFile) { try { . $regFile.FullName } catch { Write-Host ("  [命令冊] 載入失敗:" + $_.Exception.Message) -ForegroundColor Yellow } }
        if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) { $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"; if (Test-Path -LiteralPath $pyMod) { . $pyMod } }
        if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) { Write-Host "  中央 Invoke-VIAPython 不在;不繞過直呼 python,停。" -ForegroundColor Red; $exitCode = 3; return }
        $Pwsh = (Get-Process -Id $PID).Path
        Write-Host ""; Write-Host "  ╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "  ║  VIA GitHub 為主 · VCGC→VDF→VRN 啟動 → 實測 → 收尾 → 輸出 → 輸出驗證 v0100  ║" -ForegroundColor Cyan
        Write-Host "  ╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        if ($Dry) { Write-Host "  [模式] DryRun:只檢不動(不 merge · 不 commit · 不跑實測)" -ForegroundColor Yellow }

        # ⓪ 進入環境
        Invoke-Step 0 "via-entry" "進入環境 via-entry" {
            if (-not (Get-Command via-entry -ErrorAction SilentlyContinue)) { return @{ rc = 2; note = "命令冊沒有 via-entry" } }
            $global:LASTEXITCODE = 0; via-entry | Out-Host; $r0 = [int]$LASTEXITCODE
            Set-Location -LiteralPath $VIA; $env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"; $env:VIA_NO_OPEN = "1"
            return @{ rc = $r0; note = "" }
        } -YellowRc @(1, 2) -NoLock

        # ① GitHub 為主同步
        $g = [ordered]@{}
        Invoke-Step 1 "github-sync" "GitHub 為主同步(fetch → 備份 → stash → merge origin[衝突 origin 勝 · jsonl 聯集] → push)+ 尾版對照" {
            $f = Invoke-Git @("fetch", "-q", "--prune", "origin"); if ($f.rc -ne 0) { return @{ rc = 1; note = "fetch 失敗:" + ($f.lines -join " | ") } }
            $branch = Get-GitLine @("rev-parse", "--abbrev-ref", "HEAD"); $rb = "origin/" + $branch
            if ((Invoke-Git @("rev-parse", "--verify", "-q", $rb)).rc -ne 0) { $rb = "origin/main" }
            $lr = Get-GitLine @("rev-list", "--left-right", "--count", ("HEAD..." + $rb)); $ahead = 0; $behind = 0
            if ($lr -match "^(\d+)\s+(\d+)$") { $ahead = [int]$Matches[1]; $behind = [int]$Matches[2] }
            $dirty = @((Invoke-Git @("status", "--porcelain")).lines | Where-Object { $_.Trim() -ne "" })
            $stashN = @((Invoke-Git @("stash", "list")).lines | Where-Object { $_.Trim() -ne "" }).Count
            $g.branch = $branch; $g.remote = $rb; $g.head_before = Get-Head; $g.head_origin = Get-GitLine @("rev-parse", "--short=12", $rb); $g.ahead = $ahead; $g.behind = $behind; $g.dirty = $dirty.Count; $g.stash = $stashN
            $lo = @((Invoke-Git @("log", "--format=%h|%ci|%s", ($rb + "..HEAD"))).lines | Where-Object { $_ -match "\|" } | Select-Object -First 30)
            $g.local_only = $lo
            Write-Host ("     分支 " + $branch + " ↔ " + $rb + " · 領先 " + $ahead + " · 落後 " + $behind + " · 未提交 " + $dirty.Count + " · stash " + $stashN) -ForegroundColor DarkGray
            $notes = @(); $rcS = 0
            if ($Dry -or $SkipSyncRun) { $notes += $(if ($Dry) { "DryRun:不動" } else { "-SkipSync:不同步" }) }
            elseif ($ahead -eq 0 -and $behind -eq 0) { $notes += "已一致" }
            else {
                $backup = "backup/" + $branch.Replace("/", "-") + "-" + (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
                $b = Invoke-Git @("branch", $backup, "HEAD"); if ($b.rc -ne 0) { return @{ rc = 1; note = "備份分支建不起來:" + ($b.lines -join " | ") } }
                $notes += "備份 " + $backup
                $stashed = $false
                if ($dirty.Count -gt 0) { $s = Invoke-Git @("stash", "push", "-u", "-q", "-m", ("ghf " + $RunId), "--", ".", ":(exclude)VeritasIntelligenceAnalytics/VIA_Reports"); if ($s.rc -eq 0) { $stashed = $true; $notes += "stash " + $dirty.Count + " 檔" } else { return @{ rc = 1; note = "stash 失敗:" + ($s.lines -join " | ") } } }
                New-Item -ItemType Directory -Force -Path (Join-Path $RptDir "conflicts") | Out-Null
                if ($behind -gt 0) {
                    $mg = Invoke-Git @("merge", "--no-edit", "--no-ff", "-m", ("ghf " + $RunId + ": merge " + $rb + " (GitHub first; ahead " + $ahead + " behind " + $behind + ")"), $rb)
                    if ($mg.rc -eq 0) { $notes += "merge 乾淨" }
                    else {
                        $conf = @((Invoke-Git @("diff", "--name-only", "--diff-filter=U")).lines | Where-Object { $_.Trim() -ne "" })
                        foreach ($p in $conf) {
                            $full = Join-Path $Repo ($p.Replace("/", "\"))
                            $side = Join-Path $RptDir ("conflicts\" + $RunId + "_LOCAL_" + (Split-Path $p -Leaf))
                            $ours = @((Invoke-Git @("show", (":2:" + $p))).lines); Write-NoBom $side (($ours -join "`n") + "`n")
                            if ($p -like "*.jsonl") {
                                $theirs = @((Invoke-Git @("show", (":3:" + $p))).lines)
                                $seen = [System.Collections.Generic.HashSet[string]]::new(); $u = [System.Collections.Generic.List[string]]::new()
                                foreach ($x in ($ours + $theirs)) { if ($x.Trim() -ne "" -and $seen.Add($x)) { $u.Add($x) } }
                                Write-NoBom $full (($u -join "`n") + "`n"); $notes += "聯集 " + (Split-Path $p -Leaf) + "(" + $u.Count + " 行)"
                            } else { $null = Invoke-Git @("checkout", "--theirs", "--", $p); $notes += "origin 勝 " + (Split-Path $p -Leaf) + "(本機版旁證)" }
                            $null = Invoke-Git @("add", "--", $p)
                        }
                        $c2 = Invoke-Git @("commit", "-q", "--no-edit")
                        if ($c2.rc -ne 0) { $null = Invoke-Git @("merge", "--abort"); if ($stashed) { $null = Invoke-Git @("stash", "pop", "-q") }; return @{ rc = 1; note = "merge commit 失敗,已中止:" + ($c2.lines -join " | ") } }
                        $notes += "衝突 " + $conf.Count + " 檔照規則解完"
                    }
                }
                if ($stashed) { $pop = Invoke-Git @("stash", "pop", "-q"); if ($pop.rc -eq 0) { $notes += "stash 還原" } else { $rcS = 2; $notes += "stash pop 衝突,stash 留著" } }
                if (-not $NoPush) { $p1 = Invoke-Git @("push", "-q", "origin", "HEAD"); if ($p1.rc -eq 0) { $notes += "push 成功" } else { $rcS = 1; $notes += "push 被拒(不強推):" + (($p1.lines | Select-Object -Last 1) -join "") } }
            }
            $g.head_after = Get-Head; $g.ahead_behind_after = Get-GitLine @("rev-list", "--left-right", "--count", ("HEAD..." + $rb)); $g.notes = $notes
            # 尾版對照(本機 ↔ origin)
            $Families = @(
                @{ name = "命令冊"; glob = "VeritasIntelligenceAnalytics/Register-VIA-Commands-v*.ps1" }, @{ name = "唯一入口 OperatorConsole"; glob = "VeritasIntelligenceAnalytics/Invoke-VIA-OperatorConsole-v*.ps1" },
                @{ name = "FullCheck 啟動器"; glob = "VeritasIntelligenceAnalytics/launchers/Invoke-VIA-FullCheck-v*.ps1" }, @{ name = "VCGC 主控台"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" },
                @{ name = "串測 CGC_MDL224"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL224_TestAuto_v*.py" }, @{ name = "流程閘 CGC_MDL223"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL223_FlowConsistency_v*.py" },
                @{ name = "政策門 CGC_MDL207"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL207_PolicyRun_v*.py" }, @{ name = "省Token CGC_MDL158"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_VIAPanoramaAuditRepair_v*.py" },
                @{ name = "交接台 CGC_MDL140"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL140_HandoverConsole_v*.py" }, @{ name = "全景實測 CGC_MDL248"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL248_FullCheck_v*.py" },
                @{ name = "路徑驗證 CGC_MDL242"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL242_PathVerify_v*.py" }, @{ name = "編號 CGC_MDL237"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL237_NumberingSystem_v*.py" },
                @{ name = "需求冊"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Requirements_SSOT_v*.json" }, @{ name = "功能盤點冊"; glob = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v*.json" },
                @{ name = "VDF 管理器"; glob = "VeritasIntelligenceAnalytics/functional modules/VDF/VDF_SystemManager_v*.py" }, @{ name = "VRN 管理器"; glob = "VeritasIntelligenceAnalytics/functional modules/VRN/VRN_SystemManager_v*.py" }
            )
            $remoteTree = @((Invoke-Git @("ls-tree", "-r", "--name-only", $rb)).lines); $localTree = @((Invoke-Git @("ls-files", "-co", "--exclude-standard")).lines)
            $tails = @(); $behindN = 0
            foreach ($fam in $Families) {
                $rx = "^" + [regex]::Escape($fam.glob).Replace("\*", "[^/]*") + "$"
                $rn = Get-NewestName @($remoteTree | Where-Object { $_ -match $rx }); $ln = Get-NewestName @($localTree | Where-Object { $_ -match $rx })
                $lamp = if (-not $rn -and -not $ln) { "SKIP" } elseif ($rn -eq $ln) { "GREEN" } elseif (-not $ln) { "RED" } else { "YELLOW" }
                if ($lamp -in @("RED", "YELLOW")) { $behindN++ ; Write-Lamp ("     尾版 " + $fam.name + ":本機 " + $(if ($ln) { $ln } else { "—" }) + " ↔ origin " + $(if ($rn) { $rn } else { "—" })) $lamp }
                $tails += [ordered]@{ family = $fam.name; local = $ln; origin = $rn; lamp = $lamp }
            }
            $Mx.sections.tails = $tails
            foreach ($n in $notes) { Write-Host ("     " + $n) -ForegroundColor DarkGray }
            if ($rcS -eq 0 -and $behindN -gt 0 -and -not ($Dry -or $SkipSyncRun)) { $rcS = 2 }
            return @{ rc = $rcS; note = ("HEAD " + $g.head_after + " · 領先/落後 " + $g.ahead_behind_after + " · 尾版不同 " + $behindN) }
        } -YellowRc @(2)
        $Mx.sections.git = $g

        # ② 缺件補位(origin 沒有的才去本機找)
        Invoke-Step 2 "fill-missing" "缺件補位(只補 origin 沒有的:FullCheck · OperatorConsole;本機 Downloads / VIA_CELERITAS_ROOT 找)" {
            $need = @(
                @{ name = "Invoke-VIA-FullCheck-v*.ps1"; dir = (Join-Path $VIA "launchers") },
                @{ name = "Invoke-VIA-OperatorConsole-v*.ps1"; dir = $VIA }
            )
            $filled = @(); $missing = @()
            $searchDirs = @((Join-Path $env:USERPROFILE "Downloads"), $env:VIA_CELERITAS_ROOT, (Join-Path $VIA "supportive modules")) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
            foreach ($nd in $need) {
                if (Get-Tail $nd.dir $nd.name) { continue }
                $found = ""
                foreach ($sd in $searchDirs) { $c = Get-ChildItem -LiteralPath $sd -Filter $nd.name -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; if ($c) { $found = $c.FullName; break } }
                if ($found -and -not $Dry) { New-Item -ItemType Directory -Force -Path $nd.dir | Out-Null; Copy-Item -LiteralPath $found -Destination (Join-Path $nd.dir (Split-Path $found -Leaf)); $filled += (Split-Path $found -Leaf) + " ← " + (Split-Path $found -Parent) }
                elseif (-not $found) { $missing += $nd.name }
            }
            if ($__self -and (Test-Path -LiteralPath $__self) -and -not (Test-Path -LiteralPath (Join-Path $VIA "launchers\Invoke-VIA-GitHubFirst-Closeout-v0100.ps1")) -and -not $Dry) { New-Item -ItemType Directory -Force -Path (Join-Path $VIA "launchers") | Out-Null; Copy-Item -LiteralPath $__self -Destination (Join-Path $VIA "launchers\Invoke-VIA-GitHubFirst-Closeout-v0100.ps1"); $filled += "Invoke-VIA-GitHubFirst-Closeout-v0100.ps1(本檔)" }
            $Mx.sections.fill = [ordered]@{ filled = $filled; missing = $missing }
            return @{ rc = $(if ($missing.Count -gt 0) { 2 } else { 0 }); note = ("補 " + $filled.Count + " · 仍缺 " + $missing.Count + $(if ($missing.Count -gt 0) { ":" + ($missing -join " · ") } else { "" })) }
        } -YellowRc @(2)

        $VcgcTail = Get-Tail $Reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
        $OpConsole = Get-Tail $VIA "Invoke-VIA-OperatorConsole-v*.ps1"
        $FullCheck = Get-Tail (Join-Path $VIA "launchers") "Invoke-VIA-FullCheck-v*.ps1"
        if (-not $VcgcTail) { $exitCode = 3; Write-Host "  VCGC 尾版不在" -ForegroundColor Red; return }
        $regFile2 = Get-ChildItem -LiteralPath $VIA -Filter "Register-VIA-Commands-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
        if ($regFile2 -and $regFile -and $regFile2.Name -ne $regFile.Name) { try { . $regFile2.FullName; Write-Host ("  [命令冊] 換新:" + $regFile2.Name) -ForegroundColor DarkGray } catch { } }
        Write-Host ("  [正主] " + (Split-Path $VcgcTail -Leaf) + " · " + $(if ($OpConsole) { Split-Path $OpConsole -Leaf } else { "OperatorConsole 缺" }) + " · " + $(if ($FullCheck) { Split-Path $FullCheck -Leaf } else { "FullCheck 缺" })) -ForegroundColor DarkGray
        if ($Dry) { Write-Host "  DryRun:到此為止(不啟動實測)" -ForegroundColor Yellow; return }

        # ③ 啟動 VCGC
        Invoke-Step 3 "token" "啟動 VCGC:省 Token 第一步 token(門)" { $r = Invoke-Vcgc @("token"); return @{ rc = $r.rc; note = "" } } -Gate
        Invoke-Step 3 "tools" "鎖版工具卡 tools" { $r = Invoke-Vcgc @("tools"); return @{ rc = $r.rc; note = "" } } -YellowRc @(2)

        # ④ 閘診斷與有界修復
        Invoke-Step 4 "gate-fix" "閘診斷與有界修復:status → 門卡(流程閘 CGC_MDL223 · 政策門 CGC_MDL207)→ 待同步就 registry-sync --apply → 重閘(最多 2 輪)" {
            $rounds = @(); $ok = $false; $why = ""
            for ($k = 1; $k -le 2; $k++) {
                $stt = Invoke-Vcgc @("status")
                $flow = Invoke-Door "CGC_MDL223_FlowConsistency_v*.py"
                $missing = @(); if ($flow.card) { $missing = @($flow.card.missing) }
                $pendingSync = @($stt.lines | Where-Object { $_ -match "註冊冊待同步" -or $_ -match "registry-sync --apply" }).Count -gt 0
                $pol = $null; $polRed = @()
                if ($missing -contains "policy_step") { $pol = Invoke-Door "CGC_MDL207_PolicyRun_v*.py"; $polRed = @($pol.lines | Where-Object { $_ -match "^\s*\[(政策|環境|加速|衝突|還原|分群|不衝突|靜態|位階|環境計畫|回覆)\].*(ABSENT|RED|不在|失敗|讀不了|停)" } | Select-Object -First 8) }
                $rounds += [ordered]@{ round = $k; status_rc = $stt.rc; flow_door = $flow.door; flow_rc = $flow.rc; missing = $missing; weak = $(if ($flow.card) { @($flow.card.weak) } else { @() }); drift = $(if ($flow.card) { "" + $flow.card.drift } else { "?" }); pending_sync = $pendingSync; policy_red_lines = $polRed }
                Write-Lamp ("     第 " + $k + " 輪:status rc " + $stt.rc + " · 流程閘 " + $(if ($flow.rc -eq 0) { "過" } else { "缺 " + ($missing -join ",") }) + " · 待同步 " + $pendingSync) $(if ($flow.rc -eq 0) { "GREEN" } else { "YELLOW" })
                foreach ($l in $polRed) { Write-Host ("       政策門:" + $l.Trim()) -ForegroundColor Yellow }
                if ($flow.rc -eq 0 -and $stt.rc -eq 0) { $ok = $true; break }
                if ($flow.rc -eq 0 -and $stt.rc -ne 0 -and -not $pendingSync) { $ok = $true; $why = "流程閘過,status rc " + $stt.rc + "(黃:全景 / 家族燈,不擋 run)"; break }
                if ($k -eq 2) { break }
                if ($pendingSync) {
                    Write-Host "     有界修復:registry-sync(乾跑)→ registry-sync --apply(操作員令「一口氣」= 批准)" -ForegroundColor Cyan
                    $null = Invoke-Vcgc @("registry-sync"); $ap = Invoke-Vcgc @("registry-sync", "--apply"); $rounds[-1].fix = "registry-sync --apply rc " + $ap.rc
                } else { $rounds[-1].fix = "無可自動修的項(policy_step / 家族尾版 / 法冊註記 = 操作員或程式之手)"; break }
            }
            $Mx.sections.gate = [ordered]@{ ok = $ok; rounds = $rounds }
            $St.GateOk = $ok
            $lastR = $rounds[-1]
            $note = if ($ok) { $(if ($why) { $why } else { "閘過" }) } else { "閘未過:缺 " + ($lastR.missing -join ",") + $(if ($lastR.policy_red_lines.Count -gt 0) { " · 政策門紅行 " + $lastR.policy_red_lines.Count } else { "" }) + $(if ($lastR.weak.Count -gt 0) { " · 家族弱 " + ($lastR.weak -join ",") } else { "" }) }
            return @{ rc = $(if ($ok) { $(if ($why) { 2 } else { 0 }) } else { 1 }); note = $note }
        } -YellowRc @(2) -Gate

        # ⑤ 唯一入口卡(閘 · 加速器 · 工具版本 · test --quick)
        Invoke-Step 5 "enter-card" "唯一入口卡 enter --card --no-pull(閘 → 加速器 → 工具版本 → test --quick)" { $r = Invoke-Vcgc @("enter", "--card", "--no-pull"); return @{ rc = $r.rc; note = "" } } -YellowRc @(2)

        # ⑥ 實測整輪(唯一入口 OperatorConsole)
        Invoke-Step 6 "operator-console" "實測整輪:唯一入口 OperatorConsole 尾版(VCGC → ENV → SYNC(apply) → VDF → VRN → 路徑驗證 → 教訓帳 → workflow)" {
            if (-not $OpConsole) { return @{ rc = 3; note = "OperatorConsole 缺" } }
            $a = @("-NoOpen", "-NoUpload", "-NoBuild", "-ApproveRegistrySync"); if ($FullRun) { $a += "-Full" }
            $global:LASTEXITCODE = 0; & $Pwsh -NoProfile -ExecutionPolicy Bypass -File $OpConsole @a | Out-Host
            return @{ rc = [int]$LASTEXITCODE; note = "" }
        } -YellowRc @(2)

        # ⑦ 整合全景實測
        Invoke-Step 7 "fullcheck" "整合全景實測 FullCheck 尾版(① 串測 ② SSOT 全景 ③ 路徑驗證 ④ 格子讀存證 ⑤ 交接)" {
            if (-not $FullCheck) { return @{ rc = 3; note = "FullCheck 缺(origin 沒有、本機也沒找到)" } }
            $a = @("-NoOpen"); if ($FullRun) { $a += "-Full" }
            $global:LASTEXITCODE = 0; & $Pwsh -NoProfile -ExecutionPolicy Bypass -File $FullCheck @a | Out-Host
            return @{ rc = [int]$LASTEXITCODE; note = "" }
        } -YellowRc @(2)

        # ⑧ 收尾
        Invoke-Step 8 "handoff-checkpoint" "收尾:handoff checkpoint(交接快照;待辦只帶理由轉態)" { $r = Invoke-Vcgc @("handoff", "checkpoint"); return @{ rc = $r.rc; note = "" } } -YellowRc @(1, 2)
        Invoke-Step 8 "check" "收尾:安裝核可檢 check" { $r = Invoke-Vcgc @("check"); return @{ rc = $r.rc; note = "" } } -YellowRc @(2)
        Invoke-Step 8 "test" "收尾:VCGC 全功能串測 test" { $r = Invoke-Vcgc @("test"); return @{ rc = $r.rc; note = "" } } -YellowRc @(2)
        Invoke-Step 8 "ledger-page" "收尾:ledger · page · onepage(落 VIA_Reports,不 publish)" { $w = 0; foreach ($v in @(@("ledger"), @("page"), @("onepage"))) { $r = Invoke-Vcgc ([string[]]$v); if ($r.rc -gt $w) { $w = $r.rc } }; return @{ rc = $w; note = "" } } -YellowRc @(1, 2)
    } catch {
        Write-Host ("  [GitHub 為主] 例外:" + $_.Exception.Message + " @ " + $_.InvocationInfo.ScriptLineNumber) -ForegroundColor Red
        $Rows.Add([ordered]@{ run = $RunId; n = 99; id = "exception"; name = "例外中斷"; rc = 1; lamp = "RED"; sec = 0; note = ("" + $_.Exception.Message) })
    } finally {
        # ⑨ 輸出驗證 → 完工判定
        Write-Host ""; Write-Host "  ── 步 9 · 輸出驗證(這一輪的產出:在不在 · 新不新 · 燈)" -ForegroundColor Cyan
        $Outs = @(
            @{ name = "VCGC 串測"; path = "VIA_Reports\vcgc\TEST_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "單一路徑驗證"; path = "VIA_Reports\path_verify\PATH_VERIFY_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "整合全景實測"; path = "VIA_Reports\fullcheck\FULLCHECK_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "交接檢查"; path = "VIA_Reports\fullcheck\HANDOFF_CHECK_latest.json"; lampKeys = @("lamp") },
            @{ name = "交接冊"; path = "docs\handoff\HANDOFF_latest.json"; lampKeys = @("closeout_lamp", "lamp") },
            @{ name = "ENV MANAGER"; path = "VIA_Reports\env_manager\ENVMGR_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "註冊同步"; path = "VIA_Reports\operator_console\SYNC_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "VDF 鏈"; path = "VIA_Reports\vdf_chain\VDFCHAIN_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "VRN 鏈"; path = "VIA_Reports\vrn_chain\VRNCHAIN_latest.json"; lampKeys = @("lamp", "verdict") },
            @{ name = "步驟鎖帳"; path = "supportive modules\registry\VIA_VCGC_StepLock_Ledger_v0100.jsonl"; lampKeys = @() }
        )
        $outRows = @(); $outBad = 0; $outStale = 0; $outRed = 0
        foreach ($o in $Outs) {
            $p = Join-Path $VIA $o.path; $exists = Test-Path -LiteralPath $p
            $fresh = $false; $lamp = "—"; $at = ""
            if ($exists) {
                $fi = Get-Item -LiteralPath $p; $fresh = ($fi.LastWriteTime -ge $RunStart.AddMinutes(-1)); $at = $fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
                if ($o.lampKeys.Count -gt 0) { try { $j = Get-Content -LiteralPath $p -Raw -Encoding utf8 | ConvertFrom-Json; foreach ($k in $o.lampKeys) { $v = $j.$k; if ($v) { $lamp = "" + $v; break } } } catch { $lamp = "讀不了" } }
            }
            $state = if (-not $exists) { "RED" } elseif (-not $fresh) { "YELLOW" } elseif ($lamp -match "^(RED|FAIL|BLOCK)") { "RED" } elseif ($lamp -match "^(YELLOW|PARTIAL|GATE)") { "YELLOW" } else { "GREEN" }
            if (-not $exists) { $outBad++ } elseif (-not $fresh) { $outStale++ }
            if ($state -eq "RED" -and $exists) { $outRed++ }
            $outRows += [ordered]@{ name = $o.name; path = $o.path; exists = $exists; fresh = $fresh; at = $at; lamp = $lamp; state = $state }
            Write-Lamp ("     " + $o.name + ":" + $(if (-not $exists) { "不在" } elseif (-not $fresh) { "舊的(" + $at + ")" } else { "本輪 " + $at }) + " · 燈 " + $lamp) $state
        }
        $Mx.sections.outputs = $outRows
        $redSteps = @($Rows | Where-Object { $_.lamp -eq "RED" }).Count; $skip = @($Rows | Where-Object { $_.lamp -eq "SKIP" }).Count; $yel = @($Rows | Where-Object { $_.lamp -eq "YELLOW" }).Count
        $pushRed = @($Rows | Where-Object { $_.push -eq "RED" }).Count
        $verdict = if ($exitCode -eq 3) { "RED" } elseif ($Dry) { "YELLOW" } elseif ($redSteps -gt 0 -or $skip -gt 0 -or $outBad -gt 0 -or $outRed -gt 0) { "RED" } elseif ($yel -gt 0 -or $outStale -gt 0 -or $pushRed -gt 0) { "YELLOW" } else { "GREEN" }
        $verdictText = switch ($verdict) {
            "GREEN" { "完工:全步綠 · 輸出 " + $outRows.Count + " 件全在全新全綠 · 已推 GitHub" }
            "RED" { $(if ($exitCode -eq 3) { "未起跑:環境缺件" } elseif ($Dry) { "" } else { "未完工:步紅 " + $redSteps + " · 未跑 " + $skip + " · 輸出缺 " + $outBad + " · 輸出紅 " + $outRed + "(原因位置見矩陣 §閘診斷 / §輸出)" }) }
            default { $(if ($Dry) { "DryRun:只檢不動" } else { "未達完工:步黃 " + $yel + " · 輸出舊 " + $outStale + " · push 未成功 " + $pushRed + "(黃不是綠,照實)" }) }
        }
        $Mx.verdict = $verdict; $Mx.verdict_text = $verdictText; $Mx.steps = $Rows; $Mx.sec = [math]::Round($T0.Elapsed.TotalSeconds, 0)
        Write-Host ""; Write-Lamp ("  ══ 完工判定 " + $verdict + " ══ " + $verdictText) $verdict
        # 交接冊待辦摘要(AI 可接的一段)
        $handoff = Join-Path $VIA "docs\handoff\HANDOFF_latest.json"; $pendAI = @(); $pendOp = @()
        if (Test-Path -LiteralPath $handoff) { try { $h = Get-Content -LiteralPath $handoff -Raw -Encoding utf8 | ConvertFrom-Json; foreach ($pp in @($h.pending)) { if (("" + $pp.owner).StartsWith("AI")) { $pendAI += $pp } elseif (("" + $pp.owner).StartsWith("操作員")) { $pendOp += $pp } } } catch { } }
        if ($pendAI.Count -gt 0) { Write-Host ("  AI 下一輪可接 " + $pendAI.Count + " 件(只貼這一段給 AI):") -ForegroundColor Yellow; foreach ($pp in $pendAI) { Write-Host ("    " + $pp.id + " [" + $pp.state + "] " + $pp.topic + " → " + $pp.next) -ForegroundColor Yellow } }
        if ($pendOp.Count -gt 0) { Write-Host ("  操作員裁定 " + $pendOp.Count + " 件:" + (($pendOp | ForEach-Object { $_.id }) -join " · ")) -ForegroundColor DarkYellow }
        # 最後一鎖
        $final = [ordered]@{ run = $RunId; ts_utc = (Get-Date).ToUniversalTime().ToString("o"); n = 9; id = "verdict"; name = "完工判定"; rc = $(if ($verdict -eq "GREEN") { 0 } elseif ($verdict -eq "YELLOW") { 2 } else { 1 }); lamp = $verdict; sec = $Mx.sec; note = $verdictText; head = (Get-Head) }
        if ($exitCode -ne 3) { Lock-Step $final }
        $Rows.Add($final)
        # HTML 矩陣
        $esc = { param($s) [System.Net.WebUtility]::HtmlEncode("" + $s) }
        $lc = @{ GREEN = "#1f9d55"; YELLOW = "#d9a300"; RED = "#c0392b"; SKIP = "#666" }
        $rowsSteps = ($Rows | ForEach-Object { "<tr><td>" + $_.n + "</td><td>" + (& $esc $_.id) + "</td><td>" + (& $esc $_.name) + "</td><td style='color:" + $lc["" + $_.lamp] + ";font-weight:700'>" + $_.lamp + " (rc " + $_.rc + ")</td><td>" + $_.sec + "</td><td><code>" + (& $esc $_.commit) + "</code></td><td>" + (& $esc $_.push) + "</td><td>" + (& $esc $_.note) + "</td></tr>" }) -join "`n"
        $rowsOut = ($outRows | ForEach-Object { "<tr><td>" + (& $esc $_.name) + "</td><td><code>" + (& $esc $_.path) + "</code></td><td>" + $(if ($_.exists) { "在" } else { "不在" }) + "</td><td>" + $(if ($_.fresh) { "本輪" } else { "舊" }) + " " + (& $esc $_.at) + "</td><td>" + (& $esc $_.lamp) + "</td><td style='color:" + $lc["" + $_.state] + ";font-weight:700'>" + $_.state + "</td></tr>" }) -join "`n"
        $rowsTails = (@($Mx.sections.tails) | Where-Object { $_ } | ForEach-Object { "<tr><td>" + (& $esc $_.family) + "</td><td><code>" + (& $esc $_.local) + "</code></td><td><code>" + (& $esc $_.origin) + "</code></td><td style='color:" + $lc["" + $_.lamp] + ";font-weight:700'>" + $_.lamp + "</td></tr>" }) -join "`n"
        $gateHtml = (@($Mx.sections.gate.rounds) | Where-Object { $_ } | ForEach-Object { "<li>第 " + $_.round + " 輪:status rc " + $_.status_rc + " · " + (& $esc $_.flow_door) + " rc " + $_.flow_rc + " · 缺 [" + (& $esc ($_.missing -join ", ")) + "] · 家族弱 [" + (& $esc ($_.weak -join ", ")) + "] · 座位漂移 " + (& $esc $_.drift) + " · 待同步 " + $_.pending_sync + $(if ($_.fix) { " · 修復:" + (& $esc $_.fix) } else { "" }) + $(if (@($_.policy_red_lines).Count -gt 0) { "<ul>" + ((@($_.policy_red_lines) | ForEach-Object { "<li><code>" + (& $esc $_.Trim()) + "</code></li>" }) -join "") + "</ul>" } else { "" }) + "</li>" }) -join "`n"
        $gg = $Mx.sections.git
        $gitHtml = if ($gg) { "分支 " + (& $esc $gg.branch) + " ↔ " + (& $esc $gg.remote) + " · HEAD 前 <code>" + (& $esc $gg.head_before) + "</code> → 後 <code>" + (& $esc $gg.head_after) + "</code>(origin <code>" + (& $esc $gg.head_origin) + "</code>)· 領先/落後 " + $gg.ahead + "/" + $gg.behind + " → " + (& $esc $gg.ahead_behind_after) + " · 未提交 " + $gg.dirty + " · stash " + $gg.stash + "<ul>" + ((@($gg.notes) | ForEach-Object { "<li>" + (& $esc $_) + "</li>" }) -join "") + "</ul>" + $(if (@($gg.local_only).Count -gt 0) { "<details><summary>本機獨有 commit(前 30)</summary><ul>" + ((@($gg.local_only) | ForEach-Object { "<li><code>" + (& $esc $_) + "</code></li>" }) -join "") + "</ul></details>" } else { "" }) } else { "—" }
        $fillHtml = if ($Mx.sections.fill) { "補 " + (& $esc (@($Mx.sections.fill.filled) -join " · ")) + " · 仍缺 " + (& $esc (@($Mx.sections.fill.missing) -join " · ")) } else { "—" }
        $pendHtml = (@($pendAI) | ForEach-Object { "<li><code>" + (& $esc $_.id) + "</code> [" + (& $esc $_.state) + "] " + (& $esc $_.topic) + " → " + (& $esc $_.next) + "</li>" }) -join "`n"
        $vc = $lc[$verdict]
        $html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA GitHub 為主 · 完工矩陣 $RunId</title>
<style>:root{--bg:#0f1115;--fg:#e6e6e6;--mut:#9aa;--card:#171a21;--line:#2a2f3a}@media(prefers-color-scheme:light){:root{--bg:#f7f7f8;--fg:#111;--mut:#555;--card:#fff;--line:#ddd}}
body{margin:0;padding:24px;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,Segoe UI,Noto Sans TC,sans-serif}h1{font-size:20px;margin:0 0 6px}h2{font-size:15px;margin:22px 0 6px}.mut{color:var(--mut)}
.ban{margin:16px 0;padding:14px 16px;border-left:6px solid $vc;background:var(--card);font-weight:700}table{border-collapse:collapse;width:100%;background:var(--card);margin:8px 0}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{background:rgba(127,127,127,.12)}code{font-size:12px}.wrap{overflow-x:auto}ul{margin:4px 0 4px 18px}details{margin:6px 0}</style></head><body>
<h1>VIA GitHub 為主 · VCGC→VDF→VRN 啟動 → 實測 → 收尾 → 輸出 · $RunId</h1>
<div class="mut">倉 $(& $esc $Repo) · 總秒數 $($Mx.sec) · $(if ($Dry) { "DryRun" } else { "實動" })$(if ($FullRun) { " · -Full" })</div>
<div class="ban">完工判定 $verdict — $(& $esc $verdictText)</div>
<h2>A. 步驟(一步一鎖一推)</h2><div class="wrap"><table><thead><tr><th>#</th><th>站</th><th>做什麼</th><th>燈</th><th>秒</th><th>commit</th><th>push</th><th>備註</th></tr></thead><tbody>$rowsSteps</tbody></table></div>
<h2>B. 輸出驗證(完工的依據)</h2><div class="wrap"><table><thead><tr><th>產出</th><th>路徑</th><th>在</th><th>新</th><th>燈</th><th>判</th></tr></thead><tbody>$rowsOut</tbody></table></div>
<h2>C. GitHub 為主同步</h2><div>$gitHtml</div>
<h2>D. 尾版對照(本機 ↔ origin)</h2><div class="wrap"><table><thead><tr><th>家族</th><th>本機</th><th>origin</th><th>燈</th></tr></thead><tbody>$rowsTails</tbody></table></div>
<h2>E. 缺件補位</h2><div>$fillHtml</div>
<h2>F. 閘診斷與有界修復(原因位置)</h2><ul>$gateHtml</ul>
<h2>G. AI 下一輪可接的待辦 $($pendAI.Count)(操作員裁定 $($pendOp.Count) 件另列)</h2><ul>$pendHtml</ul>
<p class="mut">鎖帳:supportive modules\registry\VIA_VCGC_StepLock_Ledger_v0100.jsonl(只增,入 git)· 本頁與 log:VIA_Reports\github_first\(倉規 .gitignore,只在本機)· 衝突旁證:conflicts\</p>
</body></html>
"@
        $page = Join-Path $RptDir "GITHUB_FIRST_latest.html"
        Write-NoBom $page $html; Copy-Item -LiteralPath $page -Destination (Join-Path $RptDir ("GITHUB_FIRST_" + $RunId + ".html")) -Force
        Write-NoBom (Join-Path $RptDir "GITHUB_FIRST_latest.json") (ConvertTo-Json -InputObject $Mx -Depth 8)
        try { Stop-Transcript | Out-Null } catch { }
        Write-Host ("  [頁] " + $page) -ForegroundColor DarkCyan
        if ($env:OS -eq "Windows_NT" -and $env:VIA_GHF_NOOPEN -ne "1") { try { Start-Process -FilePath $page } catch { } }
        $env:VIA_FROM_VCGC = $PrevEnv.FROM; $env:VIA_VCGC_PUSH = $PrevEnv.PUSH; $env:VIA_NO_OPEN = $PrevEnv.OPEN; $env:VIA_PY_TIMEOUT_SEC = $PrevEnv.TO
        Set-Location -LiteralPath $StartDir
        $global:LASTEXITCODE = $(if ($exitCode -eq 3) { 3 } elseif ($verdict -eq "GREEN") { 0 } elseif ($verdict -eq "YELLOW") { 2 } else { 1 })
        $global:VIAGitHubFirstVerdict = $verdict
    }
}

$__cmd = Get-Command Invoke-CeleritasGenerated
if ($__cmd.Parameters.ContainsKey("Final")) { Invoke-CeleritasGenerated -Name "VIA-GitHubFirst-Closeout-v0100" -Body $__body -Final -FinalAction Shutdown -FinalDelay 60 }
else { Invoke-CeleritasGenerated -Name "VIA-GitHubFirst-Closeout-v0100" -Body $__body }
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
if ($PSCommandPath) { exit $global:LASTEXITCODE }
