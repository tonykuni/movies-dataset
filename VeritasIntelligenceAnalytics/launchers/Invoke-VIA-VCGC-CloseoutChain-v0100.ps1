# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-VCGC-CloseoutChain-v0100.ps1 — 從 VCGC 進入 · 省 Token 全開 · E 站 + 後續全部 · 一步一鎖一推 · 收尾判定(側線 2026-09-30)
#   操作員令:「從 VCGC 進入後啟用所有節省 TOKEN 工具進行工作所有 E 後續工作並自動更新 完成一步驟鎖定一次成果自動更新 GITHUB:確認 VCGC 收尾成功」
#   新檔(L70:不動任何舊 .ps1)。本檔加入 VeritasCeleritas PS7 標準配備模塊(Skeleton 殼 · AutoImport · Final),
#   自己不重寫任何功能:每一步都呼既有正主 —— VCGC 主控台動詞(經 Invoke-VIAPython 中央入口)、唯一入口 OperatorConsole 尾版、整合全景實測 FullCheck 尾版。
#   步驟(紅了照跑下一步;只有 ① 省 Token 與 ④ 入口卡是門,紅就停):
#     ⓪ 位置與只快轉更新  ① token(省 Token 第一步)  ② tools(鎖版工具卡)  ③ 省 Token 工具實作 pack 索引(鎖版那一支)
#     ④ enter --card --no-pull(閘 · 加速器 · 工具版本 · test --quick)  ⑤ functions(必用卡)  ⑥ handoff check
#     ⑦ E 站 ×7(operator-console · envmanager · talib-scan · pathverify · lessons · bridge-sweeper · number-audit)
#     ⑧ test(全功能串測)  ⑨ 唯一入口整輪 OperatorConsole 尾版(-ApproveRegistrySync -NoBuild -NoUpload -NoOpen)
#     ⑩ 整合全景實測 FullCheck 尾版(-NoOpen)  ⑪ handoff checkpoint  ⑫ check  ⑬ ledger · page · onepage  ⑭ 收尾判定 + HTML
#   每一步跑完:只增寫 registry\VIA_VCGC_StepLock_Ledger_v0100.jsonl(UTC 時間 · rc · 燈 · 秒 · HEAD · 變更檔 · sha16)
#   → git add 只收「supportive modules/registry · docs/handoff · VIA_Reports/vcgc_closeout · launchers/本檔」→ commit → push(被拒 → ff-only 拉一次再推;不強推)。
#   收尾判定照實:handoff 燈 ≠ 驗收燈(closeout_lamp);待辦只能帶理由轉態,不會消失。全綠才算「收尾成功」。
#   不抓網路、不寫資料家、不裝件、不開同意閘、不 Read-Host、不 Stop-Process 他 PID。
# 用法:pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VIA-VCGC-CloseoutChain-v0100.ps1
#   環境:VIA_REPO_ROOT(倉根,預設 C:\Users\tonyk\OneDrive\Documents\movies-dataset)· VIA_CELERITAS_ROOT(模塊夾)· VIA_CLOSEOUT_NOPUSH=1(只 commit 不 push)
# =====================================================================================
$__root = if ($PSScriptRoot) { $PSScriptRoot } else { $env:VIA_CELERITAS_ROOT }
$__self = $PSCommandPath
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
    $RunId = "closeout-" + (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
    $Repo = if ($env:VIA_REPO_ROOT) { $env:VIA_REPO_ROOT } else { Join-Path $env:USERPROFILE "OneDrive\Documents\movies-dataset" }
    $VIA = Join-Path $Repo "VeritasIntelligenceAnalytics"
    $Reg = Join-Path $VIA "supportive modules\registry"
    $RptDir = Join-Path $VIA "VIA_Reports\vcgc_closeout"
    $Ledger = Join-Path $Reg "VIA_VCGC_StepLock_Ledger_v0100.jsonl"
    $Rows = [System.Collections.Generic.List[object]]::new()
    $St = @{ Stop = $false }
    $StartDir = (Get-Location).Path
    $PrevEnv = @{ FROM = $env:VIA_FROM_VCGC; PUSH = $env:VIA_VCGC_PUSH; OPEN = $env:VIA_NO_OPEN; TO = $env:VIA_PY_TIMEOUT_SEC }
    $NoPush = ($env:VIA_CLOSEOUT_NOPUSH -eq "1")

    function Write-Lamp([string]$Text, [string]$Lamp) {
        $c = switch ($Lamp) { "GREEN" { "Green" } "YELLOW" { "Yellow" } "RED" { "Red" } default { "DarkGray" } }
        Write-Host $Text -ForegroundColor $c
    }
    function Get-Sha16([string]$Text) {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $h = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Text))
        return (($h | ForEach-Object { $_.ToString("x2") }) -join "").Substring(0, 16)
    }
    function Invoke-Git([string[]]$GitArgs) {
        $out = & git -C $Repo @GitArgs 2>&1
        return @{ rc = $LASTEXITCODE; lines = @($out | ForEach-Object { "$_" }) }
    }
    function Get-Head() { $r = Invoke-Git @("rev-parse", "--short=12", "HEAD"); if ($r.rc -eq 0 -and $r.lines.Count -gt 0) { return $r.lines[0].Trim() } else { return "" } }
    function Get-Branch() { $r = Invoke-Git @("rev-parse", "--abbrev-ref", "HEAD"); if ($r.rc -eq 0 -and $r.lines.Count -gt 0) { return $r.lines[0].Trim() } else { return "HEAD" } }

    # ---- 一步一鎖一推 ---------------------------------------------------------------------
    $CommitScope = @("VeritasIntelligenceAnalytics/supportive modules/registry", "VeritasIntelligenceAnalytics/docs/handoff",
        "VeritasIntelligenceAnalytics/VIA_Reports/vcgc_closeout", "VeritasIntelligenceAnalytics/launchers/Invoke-VIA-VCGC-CloseoutChain-v0100.ps1")
    function Lock-Step($Row) {
        # 1) 只增寫鎖帳
        $Row.head_before_lock = Get-Head
        $scope = @($CommitScope | Where-Object { Test-Path -LiteralPath (Join-Path $Repo $_) })
        if ($scope.Count -eq 0) { $scope = @("VeritasIntelligenceAnalytics/supportive modules/registry") }
        $st = Invoke-Git (@("status", "--porcelain", "--") + $scope)
        $changed = @($st.lines | Where-Object { $_.Trim() -ne "" } | ForEach-Object { $_.Substring(3).Trim() })
        $Row.changed = $changed.Count
        $core = (ConvertTo-Json -InputObject $Row -Compress -Depth 4)
        $Row.sha16 = Get-Sha16 $core
        $line = (ConvertTo-Json -InputObject $Row -Compress -Depth 4)
        [System.IO.File]::AppendAllText($Ledger, $line + "`n", [System.Text.UTF8Encoding]::new($false))
        # 2) commit(只收範圍內的路徑;沒變就不 commit)
        $st2 = Invoke-Git (@("status", "--porcelain", "--") + $scope)
        $changed2 = @($st2.lines | Where-Object { $_.Trim() -ne "" })
        $Row.commit = ""; $Row.push = "skip"
        if ($changed2.Count -gt 0) {
            $null = Invoke-Git (@("add", "--") + $scope)
            $msg = ("vcgc closeout " + $RunId + " step " + $Row.n + " " + $Row.id + " " + $Row.lamp + " (" + $Row.sha16 + ")")
            $c = Invoke-Git @("commit", "-q", "-m", $msg)
            if ($c.rc -eq 0) { $Row.commit = Get-Head } else { $Row.commit = "commit-fail"; $Row.push = "RED" ; Write-Host ("     [鎖] commit 失敗:" + ($c.lines -join " | ")) -ForegroundColor Red }
        }
        # 3) push(被拒就 ff-only 拉一次再推;不強推)
        if ($Row.commit -and $Row.commit -ne "commit-fail" -and -not $NoPush) {
            $p = Invoke-Git @("push", "-q", "origin", "HEAD")
            if ($p.rc -ne 0) {
                $null = Invoke-Git @("pull", "-q", "--ff-only")
                $p = Invoke-Git @("push", "-q", "origin", "HEAD")
            }
            $Row.push = if ($p.rc -eq 0) { "GREEN" } else { "RED" }
            if ($p.rc -ne 0) { Write-Host ("     [推] push 未成功(不強推):" + (($p.lines | Select-Object -Last 2) -join " | ")) -ForegroundColor Yellow }
        } elseif ($Row.commit -and $NoPush) { $Row.push = "nopush" }
        $tag = if ($Row.commit) { "commit " + $Row.commit + " · push " + $Row.push } else { "無變更,不 commit" }
        Write-Host ("     [鎖] " + $Row.sha16 + " · " + $tag) -ForegroundColor DarkCyan
    }

    # ---- 步驟執行器 -----------------------------------------------------------------------
    $VcgcTail = $null
    function Invoke-Vcgc([string[]]$Argv) {
        Invoke-VIAPython -Family "vrn" $VcgcTail @Argv | Out-Host
        return $LASTEXITCODE
    }
    function Invoke-Step([int]$N, [string]$Id, [string]$Name, [scriptblock]$Do, [int[]]$YellowRc = @(), [switch]$Gate) {
        if ($St.Stop) { $Rows.Add([ordered]@{ n = $N; id = $Id; name = $Name; rc = -1; lamp = "SKIP"; sec = 0; note = "門紅,未跑" }); return }
        Write-Host ""
        Write-Host ("  ── 步 " + $N + " · " + $Name + " (" + $Id + ")") -ForegroundColor Cyan
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $rc = 1; $note = ""
        try { $outp = @(& $Do); $rc = if ($outp.Count -gt 0) { [int]$outp[-1] } else { 1 } } catch { $rc = 1; $note = ("" + $_.Exception.Message) }
        $sw.Stop()
        $lamp = if ($rc -eq 0) { "GREEN" } elseif ($YellowRc -contains $rc) { "YELLOW" } else { "RED" }
        $row = [ordered]@{ run = $RunId; ts_utc = (Get-Date).ToUniversalTime().ToString("o"); n = $N; id = $Id; name = $Name; rc = $rc; lamp = $lamp; sec = [math]::Round($sw.Elapsed.TotalSeconds, 1); note = $note; head = (Get-Head) }
        Write-Lamp ("     → rc " + $rc + " · " + $lamp + " · " + $row.sec + " s") $lamp
        Lock-Step $row
        $Rows.Add($row)
        if ($Gate -and $lamp -eq "RED") { $St.Stop = $true; Write-Host "     門紅:後面的步不跑(照 VCGC 規則:第一步 / 入口紅就停)" -ForegroundColor Red }
    }

    # ---- 前置:倉在不在 · 命令冊 · 中央入口 -------------------------------------------------
    if (-not (Test-Path -LiteralPath (Join-Path $Repo ".git")) -or -not (Test-Path -LiteralPath $Reg)) {
        Write-Host ("  [收尾鏈] 倉根不對:" + $Repo + "(設 VIA_REPO_ROOT 指到 movies-dataset 倉根)") -ForegroundColor Red
        $global:LASTEXITCODE = 3; return
    }
    $LogDir = Join-Path $VIA "VIA_Reports\vcgc_closeout_logs"
    New-Item -ItemType Directory -Force -Path $RptDir, $LogDir | Out-Null
    $LogPath = Join-Path $LogDir ($RunId + ".log")
    try { Start-Transcript -Path $LogPath -Append | Out-Null } catch { }
    Set-Location -LiteralPath $VIA
    $env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"; $env:VIA_NO_OPEN = "1"
    $cap = 0
    if ((-not [int]::TryParse(("" + $env:VIA_PY_TIMEOUT_SEC), [ref]$cap)) -or ($cap -gt 0 -and $cap -lt 7200)) { $env:VIA_PY_TIMEOUT_SEC = "7200" }
    $exitCode = 0
    try {
        $regFile = Get-ChildItem -LiteralPath $VIA -Filter "Register-VIA-Commands-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
        if ($regFile) { try { . $regFile.FullName; Write-Host ("  [命令冊] " + $regFile.Name) -ForegroundColor DarkGray } catch { Write-Host ("  [命令冊] 載入失敗:" + $_.Exception.Message) -ForegroundColor Yellow } }
        if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
            $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
            if (Test-Path -LiteralPath $pyMod) { . $pyMod }
        }
        if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
            Write-Host "  [收尾鏈] 中央 Invoke-VIAPython 不在;不繞過直呼 python,停。" -ForegroundColor Red
            $exitCode = 3; return
        }
        $VcgcTail = (Get-ChildItem -LiteralPath $Reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1).FullName
        if (-not $VcgcTail) { Write-Host "  [收尾鏈] VCGC 尾版不在(先 git pull)" -ForegroundColor Red; $exitCode = 3; return }
        $OpConsole = (Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-OperatorConsole-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1).FullName
        $FullCheck = (Get-ChildItem -LiteralPath (Join-Path $VIA "launchers") -Filter "Invoke-VIA-FullCheck-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1).FullName
        $Pwsh = (Get-Process -Id $PID).Path
        # 本檔登進 launchers(新檔;已在就不動)
        try {
            $self = $__self
            $dest = Join-Path $VIA "launchers\Invoke-VIA-VCGC-CloseoutChain-v0100.ps1"
            if ($self -and (Test-Path -LiteralPath $self) -and -not (Test-Path -LiteralPath $dest)) { Copy-Item -LiteralPath $self -Destination $dest }
        } catch { }

        Write-Host ""
        Write-Host "  ╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "  ║  VIA VCGC 收尾鏈 v0100 · 進入 → 省Token → E 站 → 整輪 → 全景 → 判定  ║" -ForegroundColor Cyan
        Write-Host "  ╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ("  [正主] " + (Split-Path $VcgcTail -Leaf) + " · " + $(if ($OpConsole) { Split-Path $OpConsole -Leaf } else { "OperatorConsole 缺" }) + " · " + $(if ($FullCheck) { Split-Path $FullCheck -Leaf } else { "FullCheck 缺" })) -ForegroundColor DarkGray
        Write-Host ("  [倉] " + $Repo + " · 分支 " + (Get-Branch) + " · HEAD " + (Get-Head) + $(if ($NoPush) { " · 只 commit 不 push" } else { "" })) -ForegroundColor DarkGray

        # ⓪ 位置與只快轉更新
        Invoke-Step 0 "git-ff" "位置與只快轉更新(fetch → merge --ff-only;分岔不合併)" {
            $f = Invoke-Git @("fetch", "-q", "origin")
            if ($f.rc -ne 0) { Write-Host ("     fetch 失敗:" + ($f.lines -join " | ")) -ForegroundColor Yellow; return 2 }
            $m = Invoke-Git @("merge", "-q", "--ff-only", "@{u}")
            if ($m.rc -ne 0) { Write-Host ("     不能快轉(分岔或本機改動):" + (($m.lines | Select-Object -Last 2) -join " | ") + " —— 交給操作員 git pull --no-rebase") -ForegroundColor Yellow; return 2 }
            return 0
        } -YellowRc @(2)

        # ① 省 Token 第一步(門)
        Invoke-Step 1 "token" "省 Token 第一步(via-vcgc token;六件 read·slice·digest·etag·pack·brief 全啟用)" { Invoke-Vcgc @("token") } -Gate

        # ② 鎖版工具卡
        Invoke-Step 2 "tools" "鎖版工具卡(加速器 · 網路 · layout · nlp · token · frame)" { Invoke-Vcgc @("tools") } -YellowRc @(2)

        # ③ 省 Token 工具實作:鎖版那一支 pack 索引(H2)
        Invoke-Step 3 "token-pack" "省 Token 工具實作:鎖版 token 引擎 pack 索引(registry · docs/handoff)" {
            $lock = Join-Path $Reg "VIA_ToolVersion_Lock_v0100.json"
            if (-not (Test-Path -LiteralPath $lock)) { return 2 }
            $j = Get-Content -LiteralPath $lock -Raw -Encoding utf8 | ConvertFrom-Json
            $tp = Join-Path $Repo ("" + $j.token.path)
            if (-not (Test-Path -LiteralPath $tp)) { Write-Host ("     鎖冊 token.path 不在:" + $tp) -ForegroundColor Yellow; return 2 }
            $worst = 0
            foreach ($t in @("supportive modules\registry", "docs\handoff")) {
                Invoke-VIAPython -Family "vrn" $tp "pack" (Join-Path $VIA $t) | Out-Host
                if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -gt $worst) { $worst = $LASTEXITCODE }
            }
            return $worst
        } -YellowRc @(1, 2)

        # ④ 唯一入口卡(門):閘 · 加速器真載 · 工具版本 · test --quick
        Invoke-Step 4 "enter-card" "唯一入口卡 enter --card --no-pull(閘 → 加速器 → 工具版本 → test --quick)" { Invoke-Vcgc @("enter", "--card", "--no-pull") } -Gate

        # ⑤ 必用功能卡
        Invoke-Step 5 "functions" "AI 必用功能卡 functions" { Invoke-Vcgc @("functions") } -YellowRc @(2)

        # ⑥ 交接防遺漏
        Invoke-Step 6 "handoff-check" "交接防遺漏 handoff check" { Invoke-Vcgc @("handoff", "check") } -YellowRc @(1, 2)

        # ⑦ E 站 ×7(盤點冊 E-*;唯讀 / 自測形式)
        $EStations = @(
            @{ id = "E-operator-console"; name = "操作台引擎自測"; argv = @("run", "--family", "core", "CGC_MDL238_OperatorConsole", "--selftest"); y = @() },
            @{ id = "E-envmanager"; name = "ENV MANAGER 自測"; argv = @("run", "--family", "core", "CGC_MDL240_EnvManager", "--selftest"); y = @() },
            @{ id = "E-talib-scan"; name = "TA-Lib 活指令掃自測"; argv = @("run", "--family", "core", "CGC_MDL243_TalibCommandScan", "--selftest"); y = @() },
            @{ id = "E-pathverify"; name = "單一路徑驗證自測"; argv = @("run", "--family", "core", "CGC_MDL242_PathVerify", "--selftest"); y = @() },
            @{ id = "E-lessons"; name = "教訓帳自測"; argv = @("run", "--family", "core", "CGC_MDL058_Lessons", "--selftest"); y = @() },
            @{ id = "E-bridge-sweeper"; name = "橋掃自測"; argv = @("run", "--family", "core", "CGC_MDL124_BridgeSweeper", "--selftest"); y = @() },
            @{ id = "E-number-audit"; name = "編號只增稽核(唯讀)"; argv = @("run", "--family", "core", "CGC_MDL237_NumberingSystem", "audit"); y = @(2) }
        )
        $k = 0
        foreach ($e in $EStations) {
            $k++
            $argvE = [string[]]$e.argv
            Invoke-Step 7 $e.id ("E 站 " + $k + "/7 · " + $e.name) { Invoke-Vcgc $argvE } -YellowRc ([int[]]$e.y)
        }

        # ⑧ 全功能串測(整條)
        Invoke-Step 8 "test-full" "VCGC 全功能串測 test(CGC_MDL224 尾版;新指令沒登 = 黃)" { Invoke-Vcgc @("test") } -YellowRc @(2)

        # ⑨ 唯一入口整輪(OperatorConsole 尾版;子行程;不問對話框:註冊同步視為已批 · 不建庫 · 不上傳 · 不開頁)
        Invoke-Step 9 "operator-console" "唯一入口整輪 OperatorConsole 尾版(VCGC → ENV → SYNC(apply) → VDF → VRN → 路徑驗證 → 教訓帳 → workflow)" {
            if (-not $OpConsole) { return 3 }
            & $Pwsh -NoProfile -ExecutionPolicy Bypass -File $OpConsole -NoOpen -NoUpload -NoBuild -ApproveRegistrySync | Out-Host
            return $LASTEXITCODE
        } -YellowRc @(2)

        # ⑩ 整合全景實測(FullCheck 尾版;子行程)
        Invoke-Step 10 "fullcheck" "整合全景實測 FullCheck 尾版(① 串測 ② SSOT 全景 ③ 路徑驗證 ④ 格子讀存證 ⑤ 交接)" {
            if (-not $FullCheck) { return 3 }
            & $Pwsh -NoProfile -ExecutionPolicy Bypass -File $FullCheck -NoOpen | Out-Host
            return $LASTEXITCODE
        } -YellowRc @(2)

        # ⑪ 交接 checkpoint(本輪成果落冊)
        Invoke-Step 11 "handoff-checkpoint" "交接 checkpoint(HANDOFF_latest 重存;待辦只帶理由轉態)" { Invoke-Vcgc @("handoff", "checkpoint") } -YellowRc @(1, 2)

        # ⑫ 安裝核可檢
        Invoke-Step 12 "check" "安裝核可檢 check" { Invoke-Vcgc @("check") } -YellowRc @(2)

        # ⑬ 成功帳 · 中央頁 · 一頁交接(落 VIA_Reports,不 publish)
        Invoke-Step 13 "ledger-page" "成功帳 ledger · 中央頁 page · 一頁交接 onepage" {
            $w = 0
            foreach ($v in @(@("ledger"), @("page"), @("onepage"))) { $r = Invoke-Vcgc ([string[]]$v); if ($r -gt $w) { $w = $r } }
            return $w
        } -YellowRc @(1, 2)
    } finally {
        # ⑭ 收尾判定 + HTML + 最後一鎖
        $handoff = Join-Path $VIA "docs\handoff\HANDOFF_latest.json"
        $hLamp = "?"; $cLamp = "?"; $pend = @(); $pendAI = @(); $pendOp = @(); $pendWs = @(); $hAt = ""
        if (Test-Path -LiteralPath $handoff) {
            try {
                $h = Get-Content -LiteralPath $handoff -Raw -Encoding utf8 | ConvertFrom-Json
                $hLamp = "" + $h.lamp; $cLamp = "" + $h.closeout_lamp; $hAt = "" + $h.at
                $pend = @($h.pending)
                foreach ($p in $pend) {
                    $o = "" + $p.owner
                    if ($o.StartsWith("AI")) { $pendAI += $p } elseif ($o.StartsWith("工作站")) { $pendWs += $p } else { $pendOp += $p }
                }
            } catch { $hLamp = "parse-fail" }
        }
        $preFail = ($exitCode -eq 3)
        $red = @($Rows | Where-Object { $_.lamp -eq "RED" }).Count
        $yel = @($Rows | Where-Object { $_.lamp -eq "YELLOW" }).Count
        $skp = @($Rows | Where-Object { $_.lamp -eq "SKIP" }).Count
        $pushRed = @($Rows | Where-Object { $_.push -eq "RED" }).Count
        $verdict = if ($preFail) { "RED" } elseif ($red -eq 0 -and $skp -eq 0 -and $cLamp -eq "GREEN" -and $pushRed -eq 0) { "GREEN" } elseif ($red -gt 0 -or $skp -gt 0) { "RED" } else { "YELLOW" }
        $verdictText = switch ($verdict) {
            "GREEN" { "VCGC 收尾成功:全步綠 · 交接 GREEN · 驗收 GREEN · 待辦 0 · 已全推 GitHub" }
            "RED" { if ($preFail) { "VCGC 收尾未起跑:環境缺件(倉根 / 命令冊 / 中央入口 / 尾版)" } else { "VCGC 收尾未完成:紅 " + $red + " · 未跑 " + $skp + "(見矩陣)" } }
            default { "VCGC 收尾未達綠:步紅 0 · 黃 " + $yel + " · 交接 " + $hLamp + " · 驗收 " + $cLamp + " · 待辦 " + $pend.Count + "(操作員裁定 " + $pendOp.Count + " · 工作站 " + $pendWs.Count + " · AI 下一輪 " + $pendAI.Count + ")" + $(if ($pushRed -gt 0) { " · push 未成功 " + $pushRed } else { "" }) }
        }
        Write-Host ""
        Write-Lamp ("  ══ 收尾判定 " + $verdict + " ══ " + $verdictText) $verdict
        if ($pendAI.Count -gt 0) {
            Write-Host "  AI 下一輪可接的待辦(只貼這一段給 AI):" -ForegroundColor Yellow
            foreach ($p in $pendAI) { Write-Host ("    " + $p.id + " [" + $p.state + "] " + $p.topic + " → " + $p.next) -ForegroundColor Yellow }
        }
        if ($pendOp.Count -gt 0) { Write-Host ("  操作員裁定 " + $pendOp.Count + " 件:" + (($pendOp | ForEach-Object { $_.id }) -join " · ")) -ForegroundColor DarkYellow }
        # HTML 矩陣
        $esc = { param($s) [System.Net.WebUtility]::HtmlEncode("" + $s) }
        $tr = foreach ($r in $Rows) {
            $lc = @{ GREEN = "#1f9d55"; YELLOW = "#d9a300"; RED = "#c0392b"; SKIP = "#666" }["" + $r.lamp]
            $pc = if ($r.push -eq "GREEN") { "#1f9d55" } elseif ($r.push -eq "RED") { "#c0392b" } else { "#888" }
            "<tr><td>" + $r.n + "</td><td>" + (& $esc $r.id) + "</td><td>" + (& $esc $r.name) + "</td><td style='color:" + $lc + ";font-weight:700'>" + $r.lamp + " (rc " + $r.rc + ")</td><td>" + $r.sec + "</td><td><code>" + (& $esc $r.sha16) + "</code></td><td><code>" + (& $esc $r.commit) + "</code></td><td style='color:" + $pc + "'>" + (& $esc $r.push) + "</td><td>" + (& $esc $r.note) + "</td></tr>"
        }
        $pendRows = foreach ($p in $pend) { "<tr><td>" + (& $esc $p.id) + "</td><td>" + (& $esc $p.state) + "</td><td>" + (& $esc $p.owner) + "</td><td>" + (& $esc $p.topic) + "</td><td>" + (& $esc $p.next) + "</td></tr>" }
        $vc = @{ GREEN = "#1f9d55"; YELLOW = "#d9a300"; RED = "#c0392b" }[$verdict]
        $fcPage = Join-Path $VIA "VIA_Reports\fullcheck\FULLCHECK_latest.html"
        $html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA VCGC 收尾鏈 $RunId</title>
<style>:root{--bg:#0f1115;--fg:#e6e6e6;--mut:#9aa;--card:#171a21;--line:#2a2f3a}@media(prefers-color-scheme:light){:root{--bg:#f7f7f8;--fg:#111;--mut:#555;--card:#fff;--line:#ddd}}
body{margin:0;padding:24px;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,Segoe UI,Noto Sans TC,sans-serif}h1{font-size:20px;margin:0 0 6px}.mut{color:var(--mut)}
.ban{margin:16px 0;padding:14px 16px;border-left:6px solid $vc;background:var(--card);font-weight:700}table{border-collapse:collapse;width:100%;background:var(--card);margin:12px 0}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{background:rgba(127,127,127,.12)}code{font-size:12px}.wrap{overflow-x:auto}a{color:#4ea1ff}</style></head><body>
<h1>VIA VCGC 收尾鏈 v0100 · $RunId</h1>
<div class="mut">倉 $(& $esc $Repo) · 分支 $(& $esc (Get-Branch)) · HEAD $(& $esc (Get-Head)) · 總秒數 $([math]::Round($T0.Elapsed.TotalSeconds,0)) · 交接冊時間 $(& $esc $hAt)</div>
<div class="ban">收尾判定 $verdict — $(& $esc $verdictText)</div>
<div class="wrap"><table><thead><tr><th>#</th><th>站</th><th>做什麼</th><th>燈</th><th>秒</th><th>鎖 sha16</th><th>commit</th><th>push</th><th>備註</th></tr></thead><tbody>
$($tr -join "`n")
</tbody></table></div>
<h2 style="font-size:16px">交接待辦 $($pend.Count)(交接 $hLamp · 驗收 $cLamp;待辦只能帶理由轉態)</h2>
<div class="wrap"><table><thead><tr><th>id</th><th>state</th><th>owner</th><th>topic</th><th>next</th></tr></thead><tbody>
$($pendRows -join "`n")
</tbody></table></div>
<p class="mut">鎖帳:supportive modules\registry\VIA_VCGC_StepLock_Ledger_v0100.jsonl(只增) · 全景實測頁:<a href="file:///$($fcPage -replace '\\','/')">FULLCHECK_latest.html</a> · 交接冊:docs\handoff\HANDOFF_latest.json · 本輪 log:VIA_Reports\vcgc_closeout_logs\$(& $esc (Split-Path $LogPath -Leaf))(不入 git)</p>
</body></html>
"@
        $page = Join-Path $RptDir "VCGC_CLOSEOUT_latest.html"
        [System.IO.File]::WriteAllText($page, $html, [System.Text.UTF8Encoding]::new($false))
        Copy-Item -LiteralPath $page -Destination (Join-Path $RptDir ("VCGC_CLOSEOUT_" + $RunId + ".html")) -Force
        # 最後一鎖(判定也入帳 · 一併推)
        $final = [ordered]@{ run = $RunId; ts_utc = (Get-Date).ToUniversalTime().ToString("o"); n = 14; id = "verdict"; name = "收尾判定"; rc = $(if ($verdict -eq "GREEN") { 0 } elseif ($verdict -eq "YELLOW") { 2 } else { 1 }); lamp = $verdict; sec = [math]::Round($T0.Elapsed.TotalSeconds, 0); note = $verdictText; head = (Get-Head) }
        Lock-Step $final
        $Rows.Add($final)
        $exitCode = [int]$final.rc
        try { Stop-Transcript | Out-Null } catch { }
        Write-Host ("  [頁] " + $page) -ForegroundColor DarkCyan
        if ($env:OS -eq "Windows_NT" -and $env:VIA_CLOSEOUT_NOOPEN -ne "1") { try { Start-Process -FilePath $page } catch { } }
        $env:VIA_FROM_VCGC = $PrevEnv.FROM; $env:VIA_VCGC_PUSH = $PrevEnv.PUSH; $env:VIA_NO_OPEN = $PrevEnv.OPEN; $env:VIA_PY_TIMEOUT_SEC = $PrevEnv.TO
        Set-Location -LiteralPath $StartDir
        $global:LASTEXITCODE = $exitCode
        $global:VIACloseoutVerdict = $verdict
    }
}

$__cmd = Get-Command Invoke-CeleritasGenerated
if ($__cmd.Parameters.ContainsKey("Final")) {
    Invoke-CeleritasGenerated -Name "VIA-VCGC-CloseoutChain-v0100" -Body $__body -Final -FinalAction Shutdown -FinalDelay 60
} else {
    Invoke-CeleritasGenerated -Name "VIA-VCGC-CloseoutChain-v0100" -Body $__body
}
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
if ($PSCommandPath) { exit $global:LASTEXITCODE }
